import hashlib
import hmac
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.database import get_db
from app.models.entities import User, Plan, Subscription, Payment, Invoice, Coupon, AnalyticsEvent
from app.services.auth import get_current_user, hash_value, get_client_ip
from app.services.entitlements import get_user_effective_plan, get_user_usage, get_setting
from app.services.payments import get_payment_provider, process_webhook_event

router = APIRouter(prefix="/api/billing", tags=["Billing & Subscriptions"])


class CheckoutRequest(BaseModel):
    plan_id: str
    billing_cycle: str = "monthly"  # monthly | yearly
    coupon_code: Optional[str] = None
    provider: Optional[str] = None  # simulated | razorpay


class SimulatePaymentRequest(BaseModel):
    plan_id: str
    billing_cycle: str = "monthly"
    coupon_code: Optional[str] = None
    outcome: str = "success"  # success | failed


@router.get("/plans")
async def get_public_plans(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Plan).where(Plan.is_active == True).order_by(Plan.sort_order))
    plans = res.scalars().all()
    refund_note = await get_setting(db, "refund_guarantee_text", "7-day money-back guarantee.")
    return {
        "refund_guarantee_text": refund_note,
        "plans": [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "price_monthly_inr": p.price_monthly_inr,
                "price_yearly_inr": p.price_yearly_inr,
                "max_states": p.max_states,
                "max_runs_per_day": p.max_runs_per_day,
                "max_leads_per_run": p.max_leads_per_run,
                "max_leads_per_month": p.max_leads_per_month,
                "retention_days": p.retention_days,
                "allow_advanced_filters": p.allow_advanced_filters,
                "allow_all_filters": p.allow_all_filters,
                "allow_presets": p.allow_presets,
                "allow_csv_export": p.allow_csv_export,
                "allow_webhook_export": p.allow_webhook_export,
                "team_seats": p.team_seats,
                "is_popular": p.is_popular,
            }
            for p in plans
        ],
    }


def _apply_coupon(base_price: int, coupon: Optional[Coupon]) -> tuple[int, int]:
    if not coupon or not coupon.is_active:
        return base_price, 0
    if coupon.expires_at and coupon.expires_at < datetime.utcnow():
        return base_price, 0
    if coupon.uses_count >= coupon.max_uses:
        return base_price, 0

    if coupon.discount_type == "percent":
        discount = int(round(base_price * (coupon.discount_value / 100.0)))
    else:
        discount = min(base_price, coupon.discount_value)
    return max(0, base_price - discount), discount


@router.post("/checkout")
async def create_checkout(
    req: CheckoutRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    p_res = await db.execute(select(Plan).where(Plan.id == req.plan_id, Plan.is_active == True))
    plan = p_res.scalar_one_or_none()
    if not plan or plan.price_monthly_inr == 0:
        raise HTTPException(status_code=400, detail="Please choose a valid paid plan.")

    base_price = plan.price_yearly_inr if req.billing_cycle == "yearly" else plan.price_monthly_inr
    coupon = None
    if req.coupon_code:
        c_res = await db.execute(select(Coupon).where(Coupon.code == req.coupon_code.strip().upper()))
        coupon = c_res.scalar_one_or_none()
        if not coupon:
            raise HTTPException(status_code=404, detail="Coupon code not found.")

    final_amount, discount = _apply_coupon(base_price, coupon)
    provider = get_payment_provider(req.provider)
    order = await provider.create_order(
        amount_inr=final_amount,
        receipt=f"rcpt_{user.id}_{plan.id}",
        notes={"user_id": user.id, "plan_id": plan.id, "billing_cycle": req.billing_cycle},
    )

    db.add(AnalyticsEvent(
        user_id=user.id,
        event_name="checkout_started",
        properties_json=json.dumps({"plan_id": plan.id, "amount_inr": final_amount}),
        ip_hash=hash_value(get_client_ip(request)),
    ))
    await db.commit()

    return {
        "order": order,
        "plan_id": plan.id,
        "plan_name": plan.name,
        "billing_cycle": req.billing_cycle,
        "base_amount_inr": base_price,
        "discount_inr": discount,
        "final_amount_inr": final_amount,
        "coupon_code": coupon.code if coupon else None,
    }


@router.post("/simulate-complete")
async def simulate_payment_complete(
    req: SimulatePaymentRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Completes a simulated payment through the exact same idempotent webhook pipeline."""
    p_res = await db.execute(select(Plan).where(Plan.id == req.plan_id))
    plan = p_res.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found.")

    base_price = plan.price_yearly_inr if req.billing_cycle == "yearly" else plan.price_monthly_inr
    coupon = None
    if req.coupon_code:
        c_res = await db.execute(select(Coupon).where(Coupon.code == req.coupon_code.strip().upper()))
        coupon = c_res.scalar_one_or_none()
    final_amount, discount = _apply_coupon(base_price, coupon)

    event_id = f"sim_evt_{uuid.uuid4().hex[:14]}"
    event_type = "payment.captured" if req.outcome == "success" else "payment.failed"

    result = await process_webhook_event(
        db=db,
        provider_name="simulated",
        event_id=event_id,
        event_type=event_type,
        payload={
            "user_id": user.id,
            "plan_id": plan.id,
            "billing_cycle": req.billing_cycle,
            "amount_inr": final_amount,
            "discount_inr": discount,
            "coupon_code": coupon.code if coupon else None,
        },
    )

    if req.outcome == "success":
        db.add(AnalyticsEvent(
            user_id=user.id,
            event_name="payment_success",
            properties_json=json.dumps({"plan_id": plan.id, "amount_inr": final_amount}),
            ip_hash=hash_value(get_client_ip(request)),
        ))
        await db.commit()

    return result


@router.post("/webhook/{provider_name}")
async def payment_webhook(
    provider_name: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Signed, idempotent webhook endpoint for Razorpay and Simulated providers."""
    body_bytes = await request.body()
    sig = request.headers.get("X-Razorpay-Signature") or request.headers.get("X-Webhook-Signature") or ""

    provider = get_payment_provider(provider_name)
    if not provider.verify_webhook_signature(body_bytes, sig):
        raise HTTPException(status_code=401, detail="Invalid webhook signature.")

    payload = json.loads(body_bytes.decode("utf-8"))
    event_id = payload.get("event_id") or payload.get("id") or hashlib.sha256(body_bytes).hexdigest()[:24]
    event_type = payload.get("event") or payload.get("event_type") or "payment.captured"
    data = payload.get("payload", payload)

    return await process_webhook_event(db, provider_name, event_id, event_type, data)


@router.get("/status")
async def get_billing_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    plan, sub = await get_user_effective_plan(db, user)
    usage = await get_user_usage(db, user)

    inv_res = await db.execute(
        select(Invoice).where(Invoice.user_id == user.id).order_by(Invoice.created_at.desc())
    )
    invoices = inv_res.scalars().all()

    return {
        "plan": {
            "id": plan.id,
            "name": plan.name,
            "price_monthly_inr": plan.price_monthly_inr,
            "max_states": plan.max_states,
            "max_runs_per_day": plan.max_runs_per_day,
            "max_leads_per_month": plan.max_leads_per_month,
        },
        "subscription": {
            "status": sub.status if sub else "active",
            "billing_cycle": sub.billing_cycle if sub else "monthly",
            "current_period_end": sub.current_period_end if sub else None,
            "grace_until": sub.grace_until if sub else None,
            "cancel_at_period_end": sub.cancel_at_period_end if sub else False,
        },
        "usage": usage,
        "invoices": [
            {
                "id": inv.id,
                "invoice_number": inv.invoice_number,
                "plan_name": inv.plan_name,
                "total_inr": inv.total_inr,
                "created_at": inv.created_at,
            }
            for inv in invoices
        ],
    }


@router.get("/invoices/{invoice_id}/pdf")
async def download_invoice_pdf(
    invoice_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    inv = res.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if inv.user_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    if not inv.pdf_path or not Path(inv.pdf_path).exists():
        raise HTTPException(status_code=404, detail="Invoice PDF missing")
    return FileResponse(path=inv.pdf_path, filename=f"{inv.invoice_number}.pdf", media_type="application/pdf")


@router.post("/cancel")
async def cancel_subscription(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(Subscription).where(Subscription.user_id == user.id).order_by(Subscription.updated_at.desc())
    )
    sub = res.scalars().first()
    if not sub or sub.plan_id == "free":
        raise HTTPException(status_code=400, detail="No active paid subscription to cancel.")

    sub.status = "cancelled"
    sub.plan_id = "free"
    sub.cancel_at_period_end = True
    await db.commit()
    return {"status": "cancelled", "message": "Subscription cancelled and reverted to Free plan."}

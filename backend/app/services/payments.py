import hashlib
import hmac
import json
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from fpdf import FPDF
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.core.config import settings
from app.models.entities import (
    User, Plan, Subscription, Payment, Invoice, Coupon, WebhookEvent
)
from app.services.email_service import email_service


class PaymentProvider(ABC):
    """Abstraction layer for payment gateways (Razorpay, Simulated, future Stripe)."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def verify_webhook_signature(self, body_bytes: bytes, signature: str) -> bool:
        pass

    @abstractmethod
    async def create_order(self, amount_inr: int, receipt: str, notes: Dict[str, str]) -> Dict[str, Any]:
        pass


class RazorpayProvider(PaymentProvider):
    def __init__(self):
        super().__init__("razorpay")

    def verify_webhook_signature(self, body_bytes: bytes, signature: str) -> bool:
        if not settings.RAZORPAY_WEBHOOK_SECRET or not signature:
            return False
        expected = hmac.new(
            settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
            body_bytes,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    async def create_order(self, amount_inr: int, receipt: str, notes: Dict[str, str]) -> Dict[str, Any]:
        if settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET:
            import razorpay
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            order = client.order.create({
                "amount": amount_inr * 100,
                "currency": "INR",
                "receipt": receipt,
                "notes": notes,
            })
            return {
                "provider": "razorpay",
                "key_id": settings.RAZORPAY_KEY_ID,
                "order_id": order["id"],
                "amount_paise": order["amount"],
                "currency": "INR",
            }
        # Fallback if keys not configured
        return {
            "provider": "razorpay_test_stub",
            "key_id": "rzp_test_placeholder",
            "order_id": f"order_{uuid.uuid4().hex[:14]}",
            "amount_paise": amount_inr * 100,
            "currency": "INR",
        }


class SimulatedPaymentProvider(PaymentProvider):
    """In-app simulated payment provider for zero-cost local & admin testing."""

    def __init__(self):
        super().__init__("simulated")

    def verify_webhook_signature(self, body_bytes: bytes, signature: str) -> bool:
        expected = hmac.new(
            settings.SECRET_KEY.encode("utf-8"),
            body_bytes,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    async def create_order(self, amount_inr: int, receipt: str, notes: Dict[str, str]) -> Dict[str, Any]:
        return {
            "provider": "simulated",
            "order_id": f"sim_order_{uuid.uuid4().hex[:12]}",
            "amount_paise": amount_inr * 100,
            "currency": "INR",
        }


def get_payment_provider(mode: Optional[str] = None) -> PaymentProvider:
    chosen = (mode or settings.PAYMENT_MODE).lower()
    if chosen == "razorpay":
        return RazorpayProvider()
    return SimulatedPaymentProvider()


def generate_gst_invoice_pdf(invoice: Invoice) -> Path:
    """Generates a clean GST-ready PDF invoice using fpdf2."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Brand Header
    pdf.set_fill_color(15, 118, 110)
    pdf.rect(0, 0, 210, 32, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_xy(14, 9)
    pdf.cell(0, 8, "LeadHarvest India", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_x(14)
    pdf.cell(0, 6, "Tax Invoice / Payment Receipt", ln=True)

    pdf.set_text_color(30, 41, 59)
    pdf.set_y(42)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(100, 7, f"Invoice No: {invoice.invoice_number}")
    pdf.cell(0, 7, f"Date: {invoice.created_at.strftime('%d %b %Y')}", ln=True, align="R")

    pdf.set_font("Helvetica", "", 10)
    pdf.ln(4)
    pdf.cell(0, 6, f"Billed To: {invoice.customer_name} ({invoice.customer_email})", ln=True)
    if invoice.customer_gstin:
        pdf.cell(0, 6, f"Customer GSTIN: {invoice.customer_gstin}", ln=True)

    pdf.ln(8)
    pdf.set_fill_color(241, 245, 249)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(110, 9, "Description", border=1, fill=True)
    pdf.cell(40, 9, "Amount (INR)", border=1, fill=True, align="R")
    pdf.cell(35, 9, "GST (18%)", border=1, fill=True, align="R", ln=True)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(110, 9, f"{invoice.plan_name} Subscription", border=1)
    pdf.cell(40, 9, f"{invoice.subtotal_inr:,}", border=1, align="R")
    pdf.cell(35, 9, f"{invoice.gst_amount_inr:,}", border=1, align="R", ln=True)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(150, 10, "Total Paid (INR)", border=1, align="R")
    pdf.cell(35, 10, f"INR {invoice.total_inr:,}", border=1, align="R", ln=True)

    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 6, "This is a computer-generated invoice for LeadHarvest India SaaS.", ln=True)

    out_path = settings.INVOICES_DIR / f"{invoice.invoice_number}.pdf"
    pdf.output(str(out_path))
    return out_path


async def process_webhook_event(
    db: AsyncSession,
    provider_name: str,
    event_id: str,
    event_type: str,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Idempotent webhook processor.
    Stores event_id in WebhookEvent so duplicate deliveries are safely ignored.
    Handles: payment.captured / subscription.activated, payment.failed (3-day dunning),
    subscription.cancelled, payment.refunded.
    """
    existing = await db.execute(select(WebhookEvent).where(WebhookEvent.event_id == event_id))
    if existing.scalar_one_or_none():
        return {"status": "already_processed", "event_id": event_id}

    wh = WebhookEvent(
        id=f"wh_{uuid.uuid4().hex[:12]}",
        provider=provider_name,
        event_id=event_id,
        event_type=event_type,
        payload_json=json.dumps(payload),
        status="processed",
    )
    db.add(wh)

    user_id = payload.get("user_id")
    plan_id = payload.get("plan_id", "starter")
    billing_cycle = payload.get("billing_cycle", "monthly")
    amount_inr = int(payload.get("amount_inr", 0))
    discount_inr = int(payload.get("discount_inr", 0))
    coupon_code = payload.get("coupon_code")

    u_res = await db.execute(select(User).where(User.id == user_id))
    user = u_res.scalar_one_or_none()
    if not user:
        wh.status = "failed"
        wh.error_message = f"User {user_id} not found"
        await db.commit()
        return {"status": "failed", "reason": "user_not_found"}

    p_res = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = p_res.scalar_one_or_none()
    plan_name = plan.name if plan else plan_id.title()

    sub_res = await db.execute(
        select(Subscription).where(Subscription.user_id == user.id).order_by(Subscription.updated_at.desc())
    )
    sub = sub_res.scalars().first()
    now = datetime.utcnow()

    if event_type in ("payment.captured", "subscription.activated", "subscription.renewed"):
        period_days = 365 if billing_cycle == "yearly" else 30
        if not sub:
            sub = Subscription(
                id=f"sub_{uuid.uuid4().hex[:12]}",
                user_id=user.id,
                plan_id=plan_id,
                billing_cycle=billing_cycle,
                status="active",
                provider=provider_name,
                provider_subscription_id=payload.get("provider_subscription_id"),
                current_period_start=now,
                current_period_end=now + timedelta(days=period_days),
                grace_until=None,
                cancel_at_period_end=False,
            )
            db.add(sub)
        else:
            sub.plan_id = plan_id
            sub.billing_cycle = billing_cycle
            sub.status = "active"
            sub.provider = provider_name
            sub.current_period_start = now
            sub.current_period_end = now + timedelta(days=period_days)
            sub.grace_until = None
            sub.cancel_at_period_end = False

        # GST calculation (inclusive 18%)
        subtotal = round(amount_inr / 1.18) if amount_inr > 0 else 0
        gst = max(0, amount_inr - subtotal)

        pay = Payment(
            id=f"pay_{uuid.uuid4().hex[:12]}",
            user_id=user.id,
            subscription_id=sub.id,
            plan_id=plan_id,
            amount_inr=amount_inr,
            gst_amount_inr=gst,
            discount_inr=discount_inr,
            coupon_code=coupon_code,
            status="captured",
            provider=provider_name,
            provider_payment_id=payload.get("provider_payment_id", event_id),
        )
        db.add(pay)

        inv_count = (await db.scalar(select(func.count(Invoice.id))) or 0) + 1
        inv_number = f"LH-{now.year}-{inv_count:04d}"
        inv = Invoice(
            id=f"inv_{uuid.uuid4().hex[:12]}",
            invoice_number=inv_number,
            user_id=user.id,
            payment_id=pay.id,
            plan_name=plan_name,
            subtotal_inr=subtotal,
            gst_amount_inr=gst,
            total_inr=amount_inr,
            customer_name=user.name,
            customer_email=user.email,
            customer_gstin=user.gstin,
            created_at=now,
        )
        pdf_path = generate_gst_invoice_pdf(inv)
        inv.pdf_path = str(pdf_path)
        db.add(inv)
        pay.invoice_id = inv.id

        if coupon_code:
            c_res = await db.execute(select(Coupon).where(Coupon.code == coupon_code.upper()))
            coupon = c_res.scalar_one_or_none()
            if coupon:
                coupon.uses_count += 1

        await db.commit()
        await email_service.send_payment_receipt(user.email, user.name, plan_name, amount_inr, inv_number)

    elif event_type == "payment.failed":
        if sub:
            sub.status = "past_due"
            sub.grace_until = now + timedelta(days=3)
        pay = Payment(
            id=f"pay_{uuid.uuid4().hex[:12]}",
            user_id=user.id,
            subscription_id=sub.id if sub else None,
            plan_id=plan_id,
            amount_inr=amount_inr,
            status="failed",
            provider=provider_name,
            provider_payment_id=payload.get("provider_payment_id", event_id),
            failure_reason=payload.get("reason", "Payment declined by bank/UPI"),
        )
        db.add(pay)
        await db.commit()
        await email_service.send_payment_failed(user.email, user.name, plan_name)

    elif event_type == "subscription.cancelled":
        if sub:
            sub.status = "cancelled"
            sub.plan_id = "free"
            sub.cancel_at_period_end = True
        await db.commit()

    elif event_type == "payment.refunded":
        pay_id = payload.get("provider_payment_id")
        if pay_id:
            pr = await db.execute(select(Payment).where(Payment.provider_payment_id == pay_id))
            p_row = pr.scalar_one_or_none()
            if p_row:
                p_row.status = "refunded"
        if sub:
            sub.status = "cancelled"
            sub.plan_id = "free"
        await db.commit()

    return {"status": "processed", "event_id": event_id, "event_type": event_type}

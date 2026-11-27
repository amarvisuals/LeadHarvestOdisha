import csv
import io
import json
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, delete

from app.core.config import settings
from app.core.database import get_db
from app.models.entities import (
    User, Guest, Plan, Subscription, Payment, Coupon, WebhookEvent,
    Job, KnownRecord, Preset, AnalyticsEvent, PageView, AuditLog,
    FeatureFlag, AppSetting
)
from app.services.auth import (
    get_admin_user, hash_password, hash_value, get_client_ip,
    sign_token, COOKIE_IMPERSONATE, get_guest_hashes
)
from app.services.job_runner import job_runner_service
from app.services.payments import process_webhook_event

router = APIRouter(prefix="/api/admin", tags=["Admin"])


async def _log_admin_action(
    db: AsyncSession,
    admin: User,
    request: Request,
    action: str,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
):
    db.add(AuditLog(
        actor_user_id=admin.id,
        actor_email=admin.email,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details_json=json.dumps(details or {}),
        ip_hash=hash_value(get_client_ip(request)),
    ))
    await db.commit()


# ---------------------------------------------------------------------------
# 6.1 Dashboard KPIs, Funnel & Charts
# ---------------------------------------------------------------------------
@router.get("/dashboard")
async def get_admin_dashboard(
    days: int = 30,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.utcnow()
    since = now - timedelta(days=days)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Visitors & Page Views
    page_views = await db.scalar(select(func.count(PageView.id)).where(PageView.created_at >= since)) or 0
    unique_visitors = await db.scalar(
        select(func.count(func.distinct(PageView.session_id))).where(PageView.created_at >= since)
    ) or 0

    # Guest trials
    guest_runs = await db.scalar(
        select(func.count(Job.id)).where(Job.guest_id.isnot(None), Job.user_id.is_(None), Job.created_at >= since)
    ) or 0
    guests_hit_limit = await db.scalar(
        select(func.count(Guest.id)).where(Guest.runs_used >= 4)
    ) or 0

    # Signups & Conversion
    signups = await db.scalar(select(func.count(User.id)).where(User.created_at >= since)) or 0
    verified_signups = await db.scalar(
        select(func.count(User.id)).where(User.created_at >= since, User.is_verified == True)
    ) or 0
    signup_conv_rate = round((signups / max(unique_visitors, 1)) * 100, 1)

    # Subscriptions & Revenue
    active_subs_res = await db.execute(
        select(Subscription, Plan)
        .join(Plan, Subscription.plan_id == Plan.id)
        .where(Subscription.status == "active", Plan.price_monthly_inr > 0)
    )
    active_paid = active_subs_res.all()
    active_paying_count = len(active_paid)

    mrr_inr = 0
    rev_by_plan = defaultdict(int)
    for sub, plan in active_paid:
        monthly_val = int(plan.price_yearly_inr / 12) if sub.billing_cycle == "yearly" else plan.price_monthly_inr
        mrr_inr += monthly_val
        rev_by_plan[plan.name] += monthly_val

    total_revenue = await db.scalar(
        select(func.coalesce(func.sum(Payment.amount_inr), 0)).where(Payment.status == "captured", Payment.created_at >= since)
    ) or 0
    cancelled_count = await db.scalar(
        select(func.count(Subscription.id)).where(Subscription.status == "cancelled", Subscription.updated_at >= since)
    ) or 0
    churn_rate = round((cancelled_count / max(active_paying_count + cancelled_count, 1)) * 100, 1)
    arpu = round(mrr_inr / max(active_paying_count, 1), 0)

    # Runs & Insights
    jobs_res = await db.execute(select(Job).where(Job.created_at >= since))
    jobs = jobs_res.scalars().all()

    state_counter = Counter()
    city_counter = Counter()
    cat_counter = Counter()
    filter_counter = Counter()
    runs_by_day = defaultdict(int)

    for j in jobs:
        day_key = j.created_at.strftime("%Y-%m-%d") if j.created_at else now.strftime("%Y-%m-%d")
        runs_by_day[day_key] += 1
        for s in (json.loads(j.states_json) if j.states_json else ["Odisha"]):
            state_counter[s] += 1
        for c in json.loads(j.cities_json):
            city_counter[c] += 1
        for cat in json.loads(j.categories_json):
            cat_counter[cat] += 1
        if j.filters_json:
            for fk, fv in json.loads(j.filters_json).items():
                if fv not in (None, False, "", 0):
                    filter_counter[fk] += 1

    # Revenue by day
    pay_res = await db.execute(
        select(Payment).where(Payment.status == "captured", Payment.created_at >= since)
    )
    rev_by_day = defaultdict(int)
    for p in pay_res.scalars().all():
        rev_by_day[p.created_at.strftime("%Y-%m-%d")] += p.amount_inr

    # Signups by day
    usr_res = await db.execute(select(User).where(User.created_at >= since))
    signups_by_day = defaultdict(int)
    for u in usr_res.scalars().all():
        signups_by_day[u.created_at.strftime("%Y-%m-%d")] += 1

    # System Health
    running_jobs = sum(1 for s in job_runner_service.active_jobs.values() if s.status in ("running", "pending", "paused"))
    failed_today = await db.scalar(
        select(func.count(Job.id)).where(Job.status == "failed", Job.created_at >= today_start)
    ) or 0
    avg_duration = round(
        sum(j.duration_seconds or 0 for j in jobs) / max(len(jobs), 1), 1
    )

    return {
        "kpis": {
            "unique_visitors": unique_visitors,
            "page_views": page_views,
            "guest_runs": guest_runs,
            "guests_hit_limit": guests_hit_limit,
            "signups": signups,
            "verified_signups": verified_signups,
            "signup_conversion_pct": signup_conv_rate,
            "active_paying_subscribers": active_paying_count,
            "cancelled_subscriptions": cancelled_count,
            "churn_rate_pct": churn_rate,
            "mrr_inr": mrr_inr,
            "total_revenue_inr": int(total_revenue),
            "arpu_inr": int(arpu),
        },
        "revenue_by_plan": [{"name": k, "value": v} for k, v in rev_by_plan.items()],
        "funnel": [
            {"stage": "Visitors", "count": max(unique_visitors, guest_runs)},
            {"stage": "Free Trial", "count": guest_runs},
            {"stage": "Hit Limit", "count": guests_hit_limit},
            {"stage": "Signed Up", "count": signups},
            {"stage": "Paid", "count": active_paying_count},
        ],
        "daily_series": [
            {
                "date": d,
                "runs": runs_by_day.get(d, 0),
                "signups": signups_by_day.get(d, 0),
                "revenue": rev_by_day.get(d, 0),
            }
            for d in sorted(set(list(runs_by_day.keys()) + list(signups_by_day.keys()) + list(rev_by_day.keys())))
        ],
        "top_states": [{"name": k, "count": v} for k, v in state_counter.most_common(8)],
        "top_cities": [{"name": k, "count": v} for k, v in city_counter.most_common(8)],
        "top_categories": [{"name": k, "count": v} for k, v in cat_counter.most_common(8)],
        "top_filters": [{"name": k, "count": v} for k, v in filter_counter.most_common(8)],
        "system_health": {
            "running_jobs": running_jobs,
            "failed_jobs_today": failed_today,
            "avg_job_seconds": avg_duration,
            "total_runs_period": len(jobs),
        },
    }


# ---------------------------------------------------------------------------
# 6.3 Users Management & Contact Export
# ---------------------------------------------------------------------------
@router.get("/users")
async def list_users(
    q: Optional[str] = None,
    plan_filter: Optional[str] = None,
    page: int = 1,
    page_size: int = 25,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(User).order_by(User.created_at.desc())
    if q:
        like_q = f"%{q.strip()}%"
        query = query.where((User.name.ilike(like_q)) | (User.email.ilike(like_q)) | (User.phone.ilike(like_q)))

    res = await db.execute(query)
    all_users = res.scalars().all()

    enriched = []
    for u in all_users:
        sub_res = await db.execute(select(Subscription).where(Subscription.user_id == u.id).order_by(Subscription.updated_at.desc()))
        sub = sub_res.scalars().first()
        plan_id = sub.plan_id if sub else "free"
        if plan_filter and plan_id != plan_filter:
            continue

        runs_count = await db.scalar(select(func.count(Job.id)).where(Job.user_id == u.id)) or 0
        leads_count = await db.scalar(select(func.coalesce(func.sum(Job.new_leads), 0)).where(Job.user_id == u.id)) or 0
        ltv = await db.scalar(select(func.coalesce(func.sum(Payment.amount_inr), 0)).where(Payment.user_id == u.id, Payment.status == "captured")) or 0

        enriched.append({
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "phone": u.phone,
            "business_type": u.business_type,
            "role": u.role,
            "plan_id": plan_id,
            "status": "suspended" if u.is_suspended else ("verified" if u.is_verified else "unverified"),
            "is_suspended": u.is_suspended,
            "created_at": u.created_at,
            "last_active_at": u.last_active_at,
            "total_runs": runs_count,
            "leads_generated": int(leads_count),
            "lifetime_revenue_inr": int(ltv),
        })

    total = len(enriched)
    start = (page - 1) * page_size
    return {"total": total, "page": page, "items": enriched[start:start + page_size]}


@router.get("/users/export/contacts.csv")
async def export_user_contacts(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Exports contact details of users who accepted Terms and have not unsubscribed."""
    res = await db.execute(
        select(User).where(User.terms_accepted_at.isnot(None), User.marketing_unsubscribed == False)
    )
    users = res.scalars().all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Name", "Email", "Phone", "Business Type", "Plan", "Joined"])
    for u in users:
        sub_res = await db.execute(select(Subscription).where(Subscription.user_id == u.id).order_by(Subscription.updated_at.desc()))
        sub = sub_res.scalars().first()
        writer.writerow([u.name, u.email, u.phone or "", u.business_type or "", sub.plan_id if sub else "free", u.created_at.strftime("%Y-%m-%d")])

    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leadharvest_user_contacts.csv"},
    )


@router.get("/users/{user_id}")
async def get_user_detail(
    user_id: str,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(User).where(User.id == user_id))
    u = res.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    sub_res = await db.execute(select(Subscription).where(Subscription.user_id == u.id).order_by(Subscription.updated_at.desc()))
    sub = sub_res.scalars().first()
    pay_res = await db.execute(select(Payment).where(Payment.user_id == u.id).order_by(Payment.created_at.desc()))
    jobs_res = await db.execute(select(Job).where(Job.user_id == u.id).order_by(Job.created_at.desc()).limit(25))
    known_count = await db.scalar(select(func.count(KnownRecord.id)).where(KnownRecord.user_id == u.id)) or 0

    return {
        "user": {
            "id": u.id, "name": u.name, "email": u.email, "phone": u.phone,
            "business_type": u.business_type, "role": u.role,
            "is_verified": u.is_verified, "is_suspended": u.is_suspended,
            "created_at": u.created_at,
        },
        "subscription": {
            "plan_id": sub.plan_id if sub else "free",
            "status": sub.status if sub else "active",
            "comp_expires_at": sub.comp_expires_at if sub else None,
        },
        "known_records_count": known_count,
        "payments": [
            {"id": p.id, "amount_inr": p.amount_inr, "status": p.status, "provider": p.provider, "created_at": p.created_at}
            for p in pay_res.scalars().all()
        ],
        "runs": [
            {"id": j.id, "status": j.status, "new_leads": j.new_leads, "excel_file": j.excel_file, "created_at": j.created_at}
            for j in jobs_res.scalars().all()
        ],
    }


class ChangePlanRequest(BaseModel):
    plan_id: str
    comp_days: Optional[int] = None


@router.post("/users/{user_id}/plan")
async def admin_change_user_plan(
    user_id: str,
    req: ChangePlanRequest,
    request: Request,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    sub_res = await db.execute(select(Subscription).where(Subscription.user_id == user_id).order_by(Subscription.updated_at.desc()))
    sub = sub_res.scalars().first()
    exp = datetime.utcnow() + timedelta(days=req.comp_days) if req.comp_days else None
    if not sub:
        sub = Subscription(
            id=f"sub_{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            plan_id=req.plan_id,
            status="active",
            provider="manual",
            comp_expires_at=exp,
        )
        db.add(sub)
    else:
        sub.plan_id = req.plan_id
        sub.status = "active"
        sub.provider = "manual"
        sub.comp_expires_at = exp
    await db.commit()
    await _log_admin_action(db, admin, request, "change_user_plan", "user", user_id, {"plan_id": req.plan_id})
    return {"status": "updated", "plan_id": req.plan_id}


@router.post("/users/{user_id}/suspend")
async def admin_toggle_suspend(
    user_id: str,
    request: Request,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(User).where(User.id == user_id))
    u = res.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    u.is_suspended = not u.is_suspended
    await db.commit()
    await _log_admin_action(db, admin, request, "toggle_suspend", "user", user_id, {"suspended": u.is_suspended})
    return {"status": "ok", "is_suspended": u.is_suspended}


@router.delete("/users/{user_id}")
async def admin_delete_user(
    user_id: str,
    request: Request,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(User).where(User.id == user_id))
    u = res.scalar_one_or_none()
    if not u or u.role == "admin":
        raise HTTPException(status_code=400, detail="Cannot delete user")
    await db.execute(delete(KnownRecord).where(KnownRecord.user_id == user_id))
    await db.execute(delete(Job).where(Job.user_id == user_id))
    await db.delete(u)
    await db.commit()
    await _log_admin_action(db, admin, request, "delete_user", "user", user_id)
    return {"status": "deleted"}


# ---------------------------------------------------------------------------
# 6.4 Runs & Search-Intent Insights
# ---------------------------------------------------------------------------
@router.get("/runs")
async def admin_list_runs(
    status_filter: Optional[str] = None,
    page: int = 1,
    page_size: int = 30,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Job).order_by(Job.created_at.desc())
    if status_filter:
        query = query.where(Job.status == status_filter)
    res = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    jobs = res.scalars().all()
    return [
        {
            "id": j.id,
            "user_id": j.user_id,
            "guest_id": j.guest_id,
            "status": j.status,
            "adapter_name": j.adapter_name,
            "states": json.loads(j.states_json) if j.states_json else ["Odisha"],
            "cities": json.loads(j.cities_json),
            "categories": json.loads(j.categories_json),
            "filters": json.loads(j.filters_json) if j.filters_json else {},
            "total_found": j.total_found,
            "duplicates_skipped": j.duplicates_skipped,
            "new_leads": j.new_leads,
            "duration_seconds": j.duration_seconds,
            "excel_file": j.excel_file,
            "created_at": j.created_at,
        }
        for j in jobs
    ]


@router.get("/insights")
async def admin_search_insights(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(Job).order_by(Job.created_at.desc()).limit(500))
    combo_counter = Counter()
    filter_counter = Counter()
    for j in res.scalars().all():
        cities = json.loads(j.cities_json)[:2]
        cats = json.loads(j.categories_json)[:2]
        filters = json.loads(j.filters_json) if j.filters_json else {}
        tag = "No Website" if filters.get("no_website") else "Standard"
        for ct in cities:
            for ca in cats:
                combo_counter[f"{ca} + {ct} ({tag})"] += 1
        for fk, fv in filters.items():
            if fv not in (None, False, "", 0):
                filter_counter[fk] += 1

    return {
        "top_combos": [{"combo": k, "searches": v} for k, v in combo_counter.most_common(12)],
        "filter_popularity": [{"filter": k, "uses": v} for k, v in filter_counter.most_common(12)],
    }


# ---------------------------------------------------------------------------
# 6.4b Plans Editor, Coupons, Payments & Webhooks
# ---------------------------------------------------------------------------
class PlanUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price_monthly_inr: Optional[int] = None
    price_yearly_inr: Optional[int] = None
    max_states: Optional[int] = None
    max_runs_per_day: Optional[int] = None
    max_leads_per_run: Optional[int] = None
    max_leads_per_month: Optional[int] = None
    allow_advanced_filters: Optional[bool] = None
    allow_all_filters: Optional[bool] = None
    is_popular: Optional[bool] = None


@router.put("/plans/{plan_id}")
async def admin_update_plan(
    plan_id: str,
    req: PlanUpdateRequest,
    request: Request,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = res.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    for field, val in req.model_dump(exclude_none=True).items():
        setattr(plan, field, val)
    await db.commit()
    await _log_admin_action(db, admin, request, "update_plan", "plan", plan_id, req.model_dump(exclude_none=True))
    return {"status": "updated", "plan_id": plan_id}


@router.get("/payments")
async def admin_list_payments(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(Payment).order_by(Payment.created_at.desc()).limit(100))
    return [
        {
            "id": p.id, "user_id": p.user_id, "plan_id": p.plan_id,
            "amount_inr": p.amount_inr, "status": p.status,
            "provider": p.provider, "created_at": p.created_at,
        }
        for p in res.scalars().all()
    ]


@router.get("/webhooks")
async def admin_list_webhooks(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(WebhookEvent).order_by(WebhookEvent.created_at.desc()).limit(50))
    return [
        {
            "id": w.id, "provider": w.provider, "event_id": w.event_id,
            "event_type": w.event_type, "status": w.status, "created_at": w.created_at,
        }
        for w in res.scalars().all()
    ]


class CouponCreateRequest(BaseModel):
    code: str
    discount_type: str = "percent"
    discount_value: int
    max_uses: int = 100


@router.get("/coupons")
async def admin_list_coupons(admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Coupon).order_by(Coupon.created_at.desc()))
    return res.scalars().all()


@router.post("/coupons")
async def admin_create_coupon(
    req: CouponCreateRequest,
    request: Request,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    c = Coupon(
        id=f"cpn_{uuid.uuid4().hex[:8]}",
        code=req.code.strip().upper(),
        discount_type=req.discount_type,
        discount_value=req.discount_value,
        max_uses=req.max_uses,
    )
    db.add(c)
    await db.commit()
    await _log_admin_action(db, admin, request, "create_coupon", "coupon", c.code)
    return c


# ---------------------------------------------------------------------------
# 6.5 & 6.6 Admin Testing Tools, Flags, Settings, System Checks
# ---------------------------------------------------------------------------
@router.post("/impersonate/{user_id}")
async def admin_impersonate_user(
    user_id: str,
    request: Request,
    response: Response,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(User).where(User.id == user_id))
    target = res.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Target user not found")

    token = sign_token({"target_uid": user_id, "admin_id": admin.id}, salt="impersonate")
    response.set_cookie(
        key=COOKIE_IMPERSONATE,
        value=token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=4 * 3600,
        path="/",
    )
    await _log_admin_action(db, admin, request, "impersonate_start", "user", user_id)
    return {"status": "impersonating", "target_email": target.email}


@router.post("/test/reset-my-guest")
async def admin_reset_guest_counter(
    request: Request,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    ip_h, _, fp_h = get_guest_hashes(request)
    res = await db.execute(select(Guest).where((Guest.fingerprint_hash == fp_h) | (Guest.ip_hash == ip_h)))
    count = 0
    for g in res.scalars().all():
        g.runs_used = 0
        count += 1
    await db.commit()
    await _log_admin_action(db, admin, request, "reset_guest_counter")
    return {"status": "reset", "guests_reset": count}


class CreateTestUserRequest(BaseModel):
    name: str = "Test Customer"
    email: str
    password: str = "TestPass123!"
    plan_id: str = "pro"


@router.post("/test/create-user")
async def admin_create_test_user(
    req: CreateTestUserRequest,
    request: Request,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    u = User(
        id=f"usr_{uuid.uuid4().hex[:10]}",
        name=req.name,
        email=req.email.lower().strip(),
        password_hash=hash_password(req.password),
        business_type="Web Design Agency",
        role="user",
        is_verified=True,
        terms_accepted_at=datetime.utcnow(),
    )
    db.add(u)
    db.add(Subscription(
        id=f"sub_{uuid.uuid4().hex[:10]}",
        user_id=u.id,
        plan_id=req.plan_id,
        status="active",
        provider="simulated",
    ))
    await db.commit()
    await _log_admin_action(db, admin, request, "create_test_user", "user", u.id, {"plan_id": req.plan_id})
    return {"id": u.id, "email": u.email, "plan_id": req.plan_id}


@router.post("/test/simulate-captcha/{job_id}")
async def admin_simulate_captcha(job_id: str, admin: User = Depends(get_admin_user)):
    ok = await job_runner_service.trigger_verification_pause(job_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Job is not currently running.")
    return {"status": "verification_pause_triggered"}


@router.get("/system-checks")
async def admin_system_checks(admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    db_ok = True
    try:
        await db.execute(select(func.count(Plan.id)))
    except Exception:
        db_ok = False

    storage_ok = settings.EXPORTS_DIR.exists() and settings.UPLOADS_DIR.exists()
    return {
        "database": {"status": "green" if db_ok else "red", "detail": "Connected"},
        "storage": {"status": "green" if storage_ok else "red", "detail": str(settings.EXPORTS_DIR)},
        "email": {"status": "green", "detail": f"Provider: {settings.EMAIL_PROVIDER}"},
        "payments": {"status": "green", "detail": f"Mode: {settings.PAYMENT_MODE}"},
        "worker": {"status": "green", "detail": f"Active jobs: {len(job_runner_service.active_jobs)}"},
        "scraper": {"status": "green", "detail": "Playwright Firefox & Demo Engine ready"},
    }


@router.get("/audit-logs")
async def admin_audit_logs(admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(100))
    return res.scalars().all()


@router.get("/flags")
async def admin_get_flags(admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(FeatureFlag))
    return res.scalars().all()


@router.put("/flags/{key}")
async def admin_toggle_flag(
    key: str,
    enabled: bool,
    request: Request,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(FeatureFlag).where(FeatureFlag.key == key))
    flag = res.scalar_one_or_none()
    if not flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    flag.enabled = enabled
    await db.commit()
    await _log_admin_action(db, admin, request, "toggle_flag", "flag", key, {"enabled": enabled})
    return flag


@router.get("/settings")
async def admin_get_settings(admin: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(AppSetting))
    return res.scalars().all()


@router.put("/settings")
async def admin_update_settings(
    updates: Dict[str, str],
    request: Request,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    for k, v in updates.items():
        res = await db.execute(select(AppSetting).where(AppSetting.key == k))
        row = res.scalar_one_or_none()
        if row:
            row.value = str(v)
        else:
            db.add(AppSetting(key=k, value=str(v)))
    await db.commit()
    await _log_admin_action(db, admin, request, "update_settings", "settings", "cms", updates)
    return {"status": "updated"}

import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.models.entities import (
    User, Guest, Plan, Subscription, Job, FeatureFlag, AppSetting
)
from app.core.config import settings

DEFAULT_PLANS = [
    {
        "id": "free",
        "name": "Free",
        "description": "Odisha-only starter access with saved history and automatic deduplication.",
        "price_monthly_inr": 0,
        "price_yearly_inr": 0,
        "max_states": 1,
        "max_runs_per_day": 2,
        "max_leads_per_run": 100,
        "max_leads_per_month": 300,
        "retention_days": 30,
        "allow_advanced_filters": False,
        "allow_all_filters": False,
        "allow_presets": False,
        "allow_csv_export": False,
        "allow_webhook_export": False,
        "team_seats": 1,
        "priority_queue": 1,
        "is_popular": False,
        "sort_order": 0,
    },
    {
        "id": "starter",
        "name": "Starter",
        "description": "Ideal for freelancers and local web designers pitching across 3 states.",
        "price_monthly_inr": 499,
        "price_yearly_inr": 4990,  # 2 months free
        "max_states": 3,
        "max_runs_per_day": 10,
        "max_leads_per_run": 500,
        "max_leads_per_month": 2000,
        "retention_days": 365,
        "allow_advanced_filters": True,
        "allow_all_filters": False,
        "allow_presets": True,
        "allow_csv_export": False,
        "allow_webhook_export": False,
        "team_seats": 1,
        "priority_queue": 2,
        "is_popular": False,
        "sort_order": 1,
    },
    {
        "id": "pro",
        "name": "Pro",
        "description": "All-India coverage with every Smart Filter, Opportunity Score, and Pitch Presets.",
        "price_monthly_inr": 1499,
        "price_yearly_inr": 14990,  # 2 months free
        "max_states": 36,
        "max_runs_per_day": 30,
        "max_leads_per_run": 2000,
        "max_leads_per_month": 10000,
        "retention_days": 365,
        "allow_advanced_filters": True,
        "allow_all_filters": True,
        "allow_presets": True,
        "allow_csv_export": True,
        "allow_webhook_export": False,
        "team_seats": 1,
        "priority_queue": 3,
        "is_popular": True,
        "sort_order": 2,
    },
    {
        "id": "agency",
        "name": "Agency",
        "description": "High-volume lead harvesting for agencies with team seats, CSV & webhook export.",
        "price_monthly_inr": 3999,
        "price_yearly_inr": 39990,  # 2 months free
        "max_states": 36,
        "max_runs_per_day": 100,
        "max_leads_per_run": 5000,
        "max_leads_per_month": 40000,
        "retention_days": 365,
        "allow_advanced_filters": True,
        "allow_all_filters": True,
        "allow_presets": True,
        "allow_csv_export": True,
        "allow_webhook_export": True,
        "team_seats": 3,
        "priority_queue": 4,
        "is_popular": False,
        "sort_order": 3,
    },
]

DEFAULT_FLAGS = [
    ("guest_trial_enabled", True, "Allow unauthenticated visitors to run free guest trials"),
    ("google_oauth_enabled", True, "Show Continue with Google button on login/signup"),
    ("maintenance_mode", False, "Show maintenance banner and pause new runs"),
    ("test_mode_enabled", True, "Allow Demo source adapter and Simulated payment provider"),
]

DEFAULT_SETTINGS = [
    ("guest_free_tries", "4", "Number of free runs allowed per guest visitor before signup gate"),
    ("refund_guarantee_text", "7-day no-questions-asked money-back guarantee on all paid plans.", "Pricing page refund note"),
    ("announcement_banner", "", "Optional site-wide announcement banner text"),
    ("support_email", "support@leadharvest.in", "Public support email address"),
]


async def seed_defaults(db: AsyncSession):
    """Seeds plans, feature flags, and settings if absent."""
    for p_data in DEFAULT_PLANS:
        res = await db.execute(select(Plan).where(Plan.id == p_data["id"]))
        if not res.scalar_one_or_none():
            db.add(Plan(**p_data))

    for key, enabled, desc in DEFAULT_FLAGS:
        res = await db.execute(select(FeatureFlag).where(FeatureFlag.key == key))
        if not res.scalar_one_or_none():
            db.add(FeatureFlag(key=key, enabled=enabled, description=desc))

    for key, val, desc in DEFAULT_SETTINGS:
        res = await db.execute(select(AppSetting).where(AppSetting.key == key))
        if not res.scalar_one_or_none():
            db.add(AppSetting(key=key, value=val, description=desc))

    await db.commit()


async def get_setting(db: AsyncSession, key: str, default: str = "") -> str:
    res = await db.execute(select(AppSetting).where(AppSetting.key == key))
    row = res.scalar_one_or_none()
    return row.value if row else default


async def get_flag(db: AsyncSession, key: str, default: bool = True) -> bool:
    res = await db.execute(select(FeatureFlag).where(FeatureFlag.key == key))
    row = res.scalar_one_or_none()
    return row.enabled if row else default


async def get_user_effective_plan(db: AsyncSession, user: User) -> Tuple[Plan, Optional[Subscription]]:
    """Resolves user's active or grace-period plan; falls back to Free plan."""
    res = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == user.id)
        .order_by(Subscription.updated_at.desc())
    )
    sub = res.scalars().first()
    now = datetime.utcnow()

    plan_id = "free"
    if sub:
        if sub.status == "active":
            if sub.comp_expires_at and sub.comp_expires_at < now:
                sub.status = "cancelled"
                await db.commit()
            else:
                plan_id = sub.plan_id
        elif sub.status == "past_due" and sub.grace_until and sub.grace_until >= now:
            plan_id = sub.plan_id

    p_res = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = p_res.scalar_one_or_none()
    if not plan:
        p_res = await db.execute(select(Plan).where(Plan.id == "free"))
        plan = p_res.scalar_one()
    return plan, sub


async def get_user_usage(db: AsyncSession, user: User) -> Dict[str, int]:
    now = datetime.utcnow()
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    runs_today = await db.scalar(
        select(func.count(Job.id)).where(Job.user_id == user.id, Job.created_at >= day_start)
    ) or 0

    leads_month = await db.scalar(
        select(func.coalesce(func.sum(Job.new_leads), 0)).where(
            Job.user_id == user.id, Job.created_at >= month_start
        )
    ) or 0

    total_runs = await db.scalar(
        select(func.count(Job.id)).where(Job.user_id == user.id)
    ) or 0

    return {
        "runs_today": int(runs_today),
        "leads_this_month": int(leads_month),
        "total_runs": int(total_runs),
    }


def _has_advanced_filters(filters: Optional[Dict[str, Any]]) -> Tuple[bool, bool]:
    """Returns (uses_any_advanced, uses_pro_only_filters)."""
    if not filters:
        return False, False
    basic_adv = any([
        filters.get("no_website"),
        filters.get("has_website"),
        filters.get("mobile_only"),
        filters.get("min_rating") is not None,
    ])
    pro_only = any([
        filters.get("has_email"),
        filters.get("has_social_only"),
        filters.get("verified_only"),
        filters.get("exclude_chains"),
        filters.get("min_opportunity_score") and int(filters.get("min_opportunity_score", 0)) > 0,
        filters.get("max_reviews") is not None,
        filters.get("min_reviews") is not None,
    ])
    return (basic_adv or pro_only), pro_only


async def can_user_do(
    db: AsyncSession,
    actor: Union[User, Guest, None] = None,
    action: str = "start_run",
    params: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Central entitlements service.
    Single source of truth for all tier, state, filter, export, and quota checks.
    Returns (allowed, friendly_message, upgrade_hint).
    """
    params = params or {}

    if await get_flag(db, "maintenance_mode", False):
        if not isinstance(actor, User) or actor.role != "admin":
            return False, "LeadHarvest India is undergoing brief maintenance. Please try again in a few minutes.", None

    # ---------------------------------------------------------
    # Guest Entitlements
    # ---------------------------------------------------------
    if isinstance(actor, Guest):
        if not await get_flag(db, "guest_trial_enabled", True):
            return False, "Please create a free account to run lead collections.", {"action": "signup"}

        max_tries = int(await get_setting(db, "guest_free_tries", str(settings.GUEST_FREE_TRIES_DEFAULT)))
        if action == "start_run":
            if actor.runs_used >= max_tries:
                return (
                    False,
                    f"You have used all {max_tries} free guest tries. Create a free account to keep collecting and unlock saved history!",
                    {"action": "guest_limit", "runs_used": actor.runs_used, "max_tries": max_tries},
                )

            states = params.get("states") or ["Odisha"]
            if any(s.lower() != "odisha" for s in states):
                return (
                    False,
                    "Guest trials are limited to Odisha. Create a free or paid account to search other Indian states.",
                    {"action": "upgrade", "required_plan": "starter"},
                )

            _, pro_only = _has_advanced_filters(params.get("filters"))
            uses_adv, _ = _has_advanced_filters(params.get("filters"))
            if uses_adv or pro_only:
                return (
                    False,
                    "Smart Lead Filters (like 'No Website' and Opportunity Score) require a paid plan.",
                    {"action": "upgrade", "required_plan": "starter"},
                )
        elif action in ("save_preset", "csv_export", "webhook_export"):
            return False, "Create a free or paid account to use this feature.", {"action": "signup"}

        return True, "OK", None

    # ---------------------------------------------------------
    # Authenticated User Entitlements
    # ---------------------------------------------------------
    if not isinstance(actor, User):
        return False, "Authentication required.", {"action": "signup"}

    # Admin bypasses usage quotas unless testing
    if actor.role == "admin":
        return True, "OK", None

    plan, _ = await get_user_effective_plan(db, actor)
    usage = await get_user_usage(db, actor)

    if action == "start_run":
        if usage["runs_today"] >= plan.max_runs_per_day:
            return (
                False,
                f"You've reached your daily limit of {plan.max_runs_per_day} runs on the {plan.name} plan.",
                {"action": "upgrade", "current_plan": plan.id, "limit_type": "runs_per_day"},
            )

        if usage["leads_this_month"] >= plan.max_leads_per_month:
            return (
                False,
                f"You've used {usage['leads_this_month']:,} of {plan.max_leads_per_month:,} monthly leads on the {plan.name} plan. Upgrade for higher limits.",
                {"action": "upgrade", "current_plan": plan.id, "limit_type": "leads_per_month"},
            )

        states = params.get("states") or ["Odisha"]
        if plan.max_states == 1 and any(s.lower() != "odisha" for s in states):
            return (
                False,
                "The Free plan is limited to Odisha. Upgrade to Starter (3 states) or Pro (All India) to unlock more states.",
                {"action": "upgrade", "required_plan": "starter"},
            )
        if len(states) > plan.max_states:
            return (
                False,
                f"Your {plan.name} plan allows up to {plan.max_states} states per run (you selected {len(states)}).",
                {"action": "upgrade", "required_plan": "pro"},
            )

        uses_adv, pro_only = _has_advanced_filters(params.get("filters"))
        if uses_adv and not plan.allow_advanced_filters:
            return (
                False,
                "Smart Lead Filters (like 'No Website') are available on Starter, Pro, and Agency plans.",
                {"action": "upgrade", "required_plan": "starter"},
            )
        if pro_only and not plan.allow_all_filters:
            return (
                False,
                "This advanced Smart Filter (Opportunity Score, Chain Exclusion, Email, Social-only) requires the Pro or Agency plan.",
                {"action": "upgrade", "required_plan": "pro"},
            )

    elif action == "save_preset":
        if not plan.allow_presets:
            return (
                False,
                "Saved Pitch Presets are unlocked on Starter, Pro, and Agency plans.",
                {"action": "upgrade", "required_plan": "starter"},
            )
    elif action == "csv_export":
        if not plan.allow_csv_export:
            return (
                False,
                "CSV export is available on Pro and Agency plans.",
                {"action": "upgrade", "required_plan": "pro"},
            )
    elif action == "webhook_export":
        if not plan.allow_webhook_export:
            return (
                False,
                "Webhook export is available on the Agency plan.",
                {"action": "upgrade", "required_plan": "agency"},
            )

    return True, "OK", None

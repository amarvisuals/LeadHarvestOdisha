import json
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional

import pyotp
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete

from app.core.config import settings
from app.core.database import get_db
from app.models.entities import (
    User, Session as UserSession, Subscription, Job, KnownRecord, Preset, AnalyticsEvent
)
from app.services.auth import (
    hash_password, verify_password, hash_value, check_rate_limit,
    create_user_session, clear_auth_cookies, get_or_create_guest,
    migrate_guest_to_user, get_current_user, get_current_user_optional,
    get_admin_user, verify_totp_code, get_client_ip, COOKIE_REFRESH, COOKIE_IMPERSONATE
)
from app.services.entitlements import get_user_effective_plan, get_user_usage, get_setting
from app.services.email_service import email_service

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class SignupRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    phone: Optional[str] = Field(default=None, max_length=32)
    business_type: Optional[str] = Field(default="Web Design / Digital Agency", max_length=100)
    terms_accepted: bool = Field(...)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    totp_code: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    phone: Optional[str] = Field(default=None, max_length=32)
    business_type: Optional[str] = Field(default=None, max_length=100)
    gstin: Optional[str] = Field(default=None, max_length=32)
    marketing_unsubscribed: Optional[bool] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


@router.post("/signup")
async def signup(
    req: SignupRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    ip_h = hash_value(get_client_ip(request))
    check_rate_limit(f"signup:{ip_h}", max_requests=10, window_seconds=300)

    if not req.terms_accepted:
        raise HTTPException(status_code=400, detail="You must accept the Terms of Use and Privacy Policy.")

    email_lower = req.email.lower().strip()
    existing = await db.execute(select(User).where(User.email == email_lower))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    verify_token = secrets.token_urlsafe(24)
    user = User(
        id=f"usr_{uuid.uuid4().hex[:12]}",
        name=req.name.strip(),
        email=email_lower,
        password_hash=hash_password(req.password),
        phone=req.phone.strip() if req.phone else None,
        business_type=req.business_type,
        role="user",
        is_verified=False,
        verification_token=verify_token,
        terms_accepted_at=datetime.utcnow(),
    )
    db.add(user)

    # Create default Free subscription
    sub = Subscription(
        id=f"sub_{uuid.uuid4().hex[:12]}",
        user_id=user.id,
        plan_id="free",
        status="active",
        provider="manual",
    )
    db.add(sub)
    await db.commit()

    # Attach previous guest runs and Known Records immediately
    migrated_count = await migrate_guest_to_user(db, request, user)

    # Log signup analytics event
    db.add(AnalyticsEvent(
        user_id=user.id,
        event_name="signup",
        properties_json=json.dumps({"migrated_guest_sessions": migrated_count}),
        ip_hash=ip_h,
    ))
    await db.commit()

    await email_service.send_verification(user.email, user.name, verify_token)
    csrf = await create_user_session(db, user, request, response)

    return {
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "is_verified": user.is_verified,
            "plan_id": "free",
        },
        "migrated_guest_sessions": migrated_count,
        "csrf_token": csrf,
        "verification_token_dev": verify_token if settings.EMAIL_PROVIDER == "console" else None,
    }


@router.post("/login")
async def login(
    req: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    ip_h = hash_value(get_client_ip(request))
    email_lower = req.email.lower().strip()
    check_rate_limit(f"login:{ip_h}:{email_lower}", max_requests=10, window_seconds=300)

    res = await db.execute(select(User).where(User.email == email_lower))
    user = res.scalar_one_or_none()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    if user.is_suspended:
        raise HTTPException(status_code=403, detail="Your account has been suspended. Please contact support.")

    if user.totp_enabled and user.totp_secret:
        if not req.totp_code or not verify_totp_code(user.totp_secret, req.totp_code):
            raise HTTPException(status_code=401, detail="Valid 2FA TOTP code required.")

    await migrate_guest_to_user(db, request, user)
    csrf = await create_user_session(db, user, request, response)
    plan, _ = await get_user_effective_plan(db, user)

    return {
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "is_verified": user.is_verified,
            "plan_id": plan.id,
            "plan_name": plan.name,
        },
        "csrf_token": csrf,
    }


@router.post("/logout")
async def logout(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    raw_refresh = request.cookies.get(COOKIE_REFRESH)
    if raw_refresh and "." in raw_refresh:
        sid = raw_refresh.split(".", 1)[0]
        res = await db.execute(select(UserSession).where(UserSession.id == sid))
        sess = res.scalar_one_or_none()
        if sess:
            sess.revoked = True
            await db.commit()
    clear_auth_cookies(response)
    return {"status": "logged_out"}


@router.post("/verify-email")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(User).where(User.verification_token == token))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token.")
    user.is_verified = True
    user.verification_token = None
    await db.commit()
    return {"status": "verified", "email": user.email}


@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest, request: Request, db: AsyncSession = Depends(get_db)):
    ip_h = hash_value(get_client_ip(request))
    check_rate_limit(f"reset:{ip_h}", max_requests=5, window_seconds=300)

    res = await db.execute(select(User).where(User.email == req.email.lower().strip()))
    user = res.scalar_one_or_none()
    if user:
        token = secrets.token_urlsafe(24)
        user.reset_token = token
        user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        await db.commit()
        await email_service.send_password_reset(user.email, user.name, token)
    return {"status": "ok", "message": "If an account exists, a password reset link has been sent."}


@router.post("/reset-password")
async def reset_password(req: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(User).where(User.reset_token == req.token))
    user = res.scalar_one_or_none()
    if not user or not user.reset_token_expires or user.reset_token_expires < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired reset token.")
    user.password_hash = hash_password(req.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    await db.commit()
    return {"status": "password_updated"}


@router.get("/me")
async def get_me(
    request: Request,
    response: Response,
    user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """Returns either the authenticated user's profile + plan + usage, or guest trial status."""
    if not user:
        guest = await get_or_create_guest(request, response, db)
        max_tries = int(await get_setting(db, "guest_free_tries", "4"))
        return {
            "authenticated": False,
            "guest": {
                "id": guest.id,
                "runs_used": guest.runs_used,
                "max_tries": max_tries,
                "remaining_tries": max(0, max_tries - guest.runs_used),
            },
        }

    plan, sub = await get_user_effective_plan(db, user)
    usage = await get_user_usage(db, user)
    impersonated_by = getattr(user, "_impersonated_by", None)

    return {
        "authenticated": True,
        "impersonated_by": impersonated_by,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "business_type": user.business_type,
            "gstin": user.gstin,
            "role": user.role,
            "is_verified": user.is_verified,
            "totp_enabled": user.totp_enabled,
            "marketing_unsubscribed": user.marketing_unsubscribed,
            "created_at": user.created_at,
        },
        "plan": {
            "id": plan.id,
            "name": plan.name,
            "max_states": plan.max_states,
            "max_runs_per_day": plan.max_runs_per_day,
            "max_leads_per_run": plan.max_leads_per_run,
            "max_leads_per_month": plan.max_leads_per_month,
            "allow_advanced_filters": plan.allow_advanced_filters,
            "allow_all_filters": plan.allow_all_filters,
            "allow_presets": plan.allow_presets,
            "allow_csv_export": plan.allow_csv_export,
            "allow_webhook_export": plan.allow_webhook_export,
            "subscription_status": sub.status if sub else "active",
            "billing_cycle": sub.billing_cycle if sub else "monthly",
            "grace_until": sub.grace_until if sub else None,
        },
        "usage": usage,
    }


@router.patch("/profile")
async def update_profile(
    req: ProfileUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if req.name is not None:
        user.name = req.name.strip()
    if req.phone is not None:
        user.phone = req.phone.strip()
    if req.business_type is not None:
        user.business_type = req.business_type.strip()
    if req.gstin is not None:
        user.gstin = req.gstin.strip().upper()
    if req.marketing_unsubscribed is not None:
        user.marketing_unsubscribed = req.marketing_unsubscribed
    await db.commit()
    return {"status": "updated"}


@router.post("/change-password")
async def change_password(
    req: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(req.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
    user.password_hash = hash_password(req.new_password)
    await db.commit()
    return {"status": "password_changed"}


@router.get("/export-my-data")
async def export_my_data(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """DPDP Act 2023 data portability export."""
    jobs_res = await db.execute(select(Job).where(Job.user_id == user.id))
    presets_res = await db.execute(select(Preset).where(Preset.user_id == user.id))
    known_res = await db.execute(select(KnownRecord).where(KnownRecord.user_id == user.id))

    return {
        "profile": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "business_type": user.business_type,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
        "jobs": [
            {
                "id": j.id,
                "status": j.status,
                "cities": json.loads(j.cities_json),
                "categories": json.loads(j.categories_json),
                "new_leads": j.new_leads,
                "created_at": j.created_at.isoformat() if j.created_at else None,
            }
            for j in jobs_res.scalars().all()
        ],
        "presets": [
            {"id": p.id, "name": p.name, "categories": json.loads(p.categories_json)}
            for p in presets_res.scalars().all()
        ],
        "known_records_count": len(known_res.scalars().all()),
    }


@router.delete("/delete-account")
async def delete_account(
    response: Response,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """DPDP Act 2023 right to erasure."""
    if user.role == "admin":
        raise HTTPException(status_code=400, detail="Admin accounts cannot be self-deleted.")
    await db.execute(delete(KnownRecord).where(KnownRecord.user_id == user.id))
    await db.execute(delete(Job).where(Job.user_id == user.id))
    await db.execute(delete(Preset).where(Preset.user_id == user.id))
    await db.delete(user)
    await db.commit()
    clear_auth_cookies(response)
    return {"status": "account_deleted"}


@router.post("/admin-totp/setup")
async def setup_admin_totp(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    secret = pyotp.random_base32()
    admin.totp_secret = secret
    await db.commit()
    uri = pyotp.totp.TOTP(secret).provisioning_uri(name=admin.email, issuer_name="LeadHarvest India")
    return {"secret": secret, "provisioning_uri": uri}


@router.post("/admin-totp/enable")
async def enable_admin_totp(
    code: str,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    if not admin.totp_secret or not verify_totp_code(admin.totp_secret, code):
        raise HTTPException(status_code=400, detail="Invalid TOTP code.")
    admin.totp_enabled = True
    await db.commit()
    return {"status": "totp_enabled"}


@router.post("/stop-impersonation")
async def stop_impersonation(response: Response):
    response.delete_cookie(key=COOKIE_IMPERSONATE, path="/")
    return {"status": "impersonation_ended"}

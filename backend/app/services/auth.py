import hashlib
import hmac
import secrets
import time
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple

import pyotp
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Request, Response, HTTPException, Depends, status
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update

from app.core.config import settings
from app.core.database import get_db
from app.models.entities import User, Session as UserSession, Guest, Job, KnownRecord, UploadedFileAudit

ph = PasswordHasher()
serializer = URLSafeTimedSerializer(settings.SECRET_KEY)

COOKIE_ACCESS = "lh_access"
COOKIE_REFRESH = "lh_refresh"
COOKIE_GUEST = "lh_guest"
COOKIE_CSRF = "lh_csrf"
COOKIE_IMPERSONATE = "lh_impersonate"

# In-memory sliding-window rate limiter (used when Redis is not configured)
_RATE_BUCKETS: Dict[str, list] = defaultdict(list)


def hash_password(password: str) -> str:
    return ph.hash(password)


def verify_password(password: str, password_hash: Optional[str]) -> bool:
    if not password_hash:
        return False
    try:
        return ph.verify(password_hash, password)
    except VerifyMismatchError:
        return False
    except Exception:
        return False


def hash_value(raw: str) -> str:
    """One-way HMAC-SHA256 hash so raw IPs/UAs/tokens are never stored in plaintext."""
    return hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        raw.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def sign_token(payload: Dict[str, Any], salt: str = "auth") -> str:
    return serializer.dumps(payload, salt=salt)


def unsign_token(token: str, max_age_seconds: int, salt: str = "auth") -> Optional[Dict[str, Any]]:
    try:
        return serializer.loads(token, salt=salt, max_age=max_age_seconds)
    except (BadSignature, SignatureExpired):
        return None


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


def get_guest_hashes(request: Request) -> Tuple[str, str, str]:
    """Returns (ip_hash, ua_hash, fingerprint_hash) without storing raw IP."""
    ip = get_client_ip(request)
    ua = request.headers.get("user-agent", "unknown")
    ip_h = hash_value(f"ip:{ip}")
    ua_h = hash_value(f"ua:{ua}")
    fp_h = hash_value(f"fp:{ip}:{ua}")
    return ip_h, ua_h, fp_h


def check_rate_limit(bucket_key: str, max_requests: int, window_seconds: int) -> None:
    """Sliding-window rate limiter; raises HTTP 429 on abuse."""
    now = time.time()
    cutoff = now - window_seconds
    entries = [t for t in _RATE_BUCKETS[bucket_key] if t > cutoff]
    if len(entries) >= max_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Please wait a moment before trying again.",
        )
    entries.append(now)
    _RATE_BUCKETS[bucket_key] = entries


def set_auth_cookies(
    response: Response,
    user_id: str,
    session_id: str,
    refresh_token: str,
    role: str = "user",
) -> str:
    access_token = sign_token(
        {"uid": user_id, "sid": session_id, "role": role},
        salt="access",
    )
    csrf_token = secrets.token_urlsafe(24)

    response.set_cookie(
        key=COOKIE_ACCESS,
        value=access_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    response.set_cookie(
        key=COOKIE_REFRESH,
        value=f"{session_id}.{refresh_token}",
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/",
    )
    response.set_cookie(
        key=COOKIE_CSRF,
        value=csrf_token,
        httponly=False,  # Readable by frontend JS for X-CSRF-Token header
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/",
    )
    return csrf_token


def clear_auth_cookies(response: Response):
    for name in [COOKIE_ACCESS, COOKIE_REFRESH, COOKIE_CSRF, COOKIE_IMPERSONATE]:
        response.delete_cookie(key=name, path="/")


async def create_user_session(
    db: AsyncSession,
    user: User,
    request: Request,
    response: Response,
) -> str:
    session_id = str(uuid.uuid4())
    raw_refresh = secrets.token_urlsafe(32)
    ip_h, ua_h, _ = get_guest_hashes(request)

    db_session = UserSession(
        id=session_id,
        user_id=user.id,
        refresh_token_hash=hash_value(raw_refresh),
        user_agent_hash=ua_h,
        ip_hash=ip_h,
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(db_session)
    user.last_active_at = datetime.utcnow()
    await db.commit()

    return set_auth_cookies(response, user.id, session_id, raw_refresh, user.role)


async def get_or_create_guest(
    request: Request,
    response: Optional[Response],
    db: AsyncSession,
) -> Guest:
    """
    Resolves guest identity by combining:
    1) Signed httpOnly guest cookie
    2) Hashed IP + User-Agent fingerprint (so clearing cookies does not reset trial count!)
    """
    ip_h, ua_h, fp_h = get_guest_hashes(request)
    guest: Optional[Guest] = None

    raw_cookie = request.cookies.get(COOKIE_GUEST)
    if raw_cookie:
        data = unsign_token(raw_cookie, max_age_seconds=90 * 86400, salt="guest")
        if data and data.get("gid"):
            res = await db.execute(select(Guest).where(Guest.id == data["gid"]))
            guest = res.scalar_one_or_none()

    # Fallback lookup by fingerprint or IP hash so clearing cookies cannot reset guest limit
    if not guest:
        res = await db.execute(
            select(Guest)
            .where(Guest.fingerprint_hash == fp_h)
            .order_by(Guest.runs_used.desc())
        )
        guest = res.scalars().first()

    if not guest:
        res = await db.execute(
            select(Guest)
            .where(Guest.ip_hash == ip_h)
            .order_by(Guest.runs_used.desc())
        )
        guest = res.scalars().first()

    if not guest:
        guest = Guest(
            id=f"guest_{uuid.uuid4().hex[:16]}",
            fingerprint_hash=fp_h,
            ip_hash=ip_h,
            ua_hash=ua_h,
            runs_used=0,
        )
        db.add(guest)
        await db.commit()
        await db.refresh(guest)

    if response is not None:
        signed_gid = sign_token({"gid": guest.id}, salt="guest")
        response.set_cookie(
            key=COOKIE_GUEST,
            value=signed_gid,
            httponly=True,
            secure=settings.COOKIE_SECURE,
            samesite=settings.COOKIE_SAMESITE,
            max_age=90 * 86400,
            path="/",
        )

    return guest


async def migrate_guest_to_user(
    db: AsyncSession,
    request: Request,
    user: User,
) -> int:
    """Attaches all previous guest runs, known records, and uploads to the new user."""
    ip_h, _, fp_h = get_guest_hashes(request)
    guest_ids = set()

    raw_cookie = request.cookies.get(COOKIE_GUEST)
    if raw_cookie:
        data = unsign_token(raw_cookie, max_age_seconds=90 * 86400, salt="guest")
        if data and data.get("gid"):
            guest_ids.add(data["gid"])

    res = await db.execute(
        select(Guest).where((Guest.fingerprint_hash == fp_h) | (Guest.ip_hash == ip_h))
    )
    matching_guests = res.scalars().all()
    for g in matching_guests:
        if not g.migrated_to_user_id:
            guest_ids.add(g.id)
            g.migrated_to_user_id = user.id

    if not guest_ids:
        return 0

    gid_list = list(guest_ids)
    await db.execute(
        update(Job).where(Job.guest_id.in_(gid_list), Job.user_id.is_(None)).values(user_id=user.id)
    )
    await db.execute(
        update(KnownRecord).where(KnownRecord.guest_id.in_(gid_list), KnownRecord.user_id.is_(None)).values(user_id=user.id)
    )
    await db.execute(
        update(UploadedFileAudit).where(UploadedFileAudit.guest_id.in_(gid_list), UploadedFileAudit.user_id.is_(None)).values(user_id=user.id)
    )
    await db.commit()
    return len(gid_list)


async def get_current_user_optional(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Returns authenticated User (supporting admin impersonation) or None for guests."""
    token = request.cookies.get(COOKIE_ACCESS)
    if not token:
        return None
    payload = unsign_token(token, max_age_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, salt="access")
    if not payload or not payload.get("uid"):
        return None

    res = await db.execute(select(User).where(User.id == payload["uid"]))
    user = res.scalar_one_or_none()
    if not user or user.is_suspended:
        return None

    # Check admin impersonation cookie
    imp_token = request.cookies.get(COOKIE_IMPERSONATE)
    if imp_token and user.role == "admin":
        imp_data = unsign_token(imp_token, max_age_seconds=4 * 3600, salt="impersonate")
        if imp_data and imp_data.get("target_uid"):
            t_res = await db.execute(select(User).where(User.id == imp_data["target_uid"]))
            target_user = t_res.scalar_one_or_none()
            if target_user:
                setattr(target_user, "_impersonated_by", user.email)
                return target_user

    return user


async def get_current_user(
    user: Optional[User] = Depends(get_current_user_optional),
) -> User:
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please sign in to continue.",
        )
    return user


async def get_admin_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Strictly resolves the real admin user (ignores impersonation)."""
    token = request.cookies.get(COOKIE_ACCESS)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin authentication required")
    payload = unsign_token(token, max_age_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, salt="access")
    if not payload or not payload.get("uid"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")

    res = await db.execute(select(User).where(User.id == payload["uid"]))
    user = res.scalar_one_or_none()
    if not user or user.role not in ("admin", "support") or user.is_suspended:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return user


def verify_totp_code(secret: str, code: str) -> bool:
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)

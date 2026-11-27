import json
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.entities import AnalyticsEvent, PageView, User
from app.services.auth import get_current_user_optional, hash_value, get_client_ip
from app.services.entitlements import get_flag, get_setting

router = APIRouter(prefix="/api", tags=["Analytics & Public Config"])


class TrackRequest(BaseModel):
    type: str = "pageview"  # pageview | event
    path: Optional[str] = "/"
    event_name: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    referrer: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    consent_given: bool = True


def _detect_device(ua: str) -> str:
    ua_l = ua.lower()
    if "mobile" in ua_l or "android" in ua_l or "iphone" in ua_l:
        return "mobile"
    if "ipad" in ua_l or "tablet" in ua_l:
        return "tablet"
    return "desktop"


@router.post("/analytics/track")
async def track_analytics(
    req: TrackRequest,
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    ua = request.headers.get("user-agent", "")
    device = _detect_device(ua)
    ip_h = hash_value(get_client_ip(request)) if req.consent_given else None
    sess_id = req.session_id if req.consent_given else None
    uid = user.id if (user and req.consent_given) else None

    if req.type == "pageview":
        db.add(PageView(
            session_id=sess_id,
            user_id=uid,
            path=req.path or "/",
            referrer=req.referrer,
            utm_source=req.utm_source,
            device_type=device,
            ip_hash=ip_h,
            consent_given=req.consent_given,
        ))
    elif req.event_name:
        db.add(AnalyticsEvent(
            session_id=sess_id,
            user_id=uid,
            event_name=req.event_name,
            properties_json=json.dumps(req.properties or {}),
            ip_hash=ip_h,
            device_type=device,
            referrer=req.referrer,
            utm_source=req.utm_source,
            utm_medium=req.utm_medium,
            utm_campaign=req.utm_campaign,
            consent_given=req.consent_given,
        ))

    await db.commit()
    return {"status": "ok"}


@router.get("/config/public-settings")
async def get_public_settings(db: AsyncSession = Depends(get_db)):
    return {
        "guest_free_tries": int(await get_setting(db, "guest_free_tries", "4")),
        "refund_guarantee_text": await get_setting(db, "refund_guarantee_text", "7-day money-back guarantee."),
        "announcement_banner": await get_setting(db, "announcement_banner", ""),
        "support_email": await get_setting(db, "support_email", "support@leadharvest.in"),
        "flags": {
            "guest_trial_enabled": await get_flag(db, "guest_trial_enabled", True),
            "google_oauth_enabled": await get_flag(db, "google_oauth_enabled", True),
            "maintenance_mode": await get_flag(db, "maintenance_mode", False),
            "test_mode_enabled": await get_flag(db, "test_mode_enabled", True),
        },
    }

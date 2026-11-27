"""
Home State Location Detection, One-Time Chooser, 90-Day Change Requests,
and Starter Plan Extra States APIs.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.models.entities import (
    AnalyticsEvent,
    AppSetting,
    AuditLog,
    FeatureFlag,
    GeoDetectionLog,
    Guest,
    StateChangeRequest,
    User,
    UserExtraState,
)
from app.services.auth import (
    check_rate_limit,
    get_client_ip,
    get_current_user,
    get_current_user_optional,
    get_or_create_guest,
    hash_value,
)
from app.services.entitlements import (
    get_allowed_states_for_actor,
    get_flag,
    get_setting,
    get_user_effective_plan,
)
from app.services.geoip import (
    detect_geo_for_request,
    resolve_canonical_state,
    set_guest_state_cookie,
)

router = APIRouter(prefix="/api/location", tags=["Location"])


@router.get("/status")
async def get_location_status(
    request: Request,
    response: Response,
    user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    ip_h = hash_value(get_client_ip(request))
    check_rate_limit(f"loc_status:{ip_h}", max_requests=60, window_seconds=60)

    provider_name = await get_setting(db, "geoip_provider", "local")
    db_path = await get_setting(db, "geoip_db_path", "")
    test_mode = await get_flag(db, "test_mode_enabled", True)
    geo = detect_geo_for_request(
        request,
        get_client_ip(request),
        provider_name=provider_name,
        db_path=db_path,
        test_mode_enabled=test_mode,
    )

    if not user:
        guest = await get_or_create_guest(request, response, db)
        allowed_info = await get_allowed_states_for_actor(db, guest)
        return {
            "actor_type": "guest",
            "home_state": guest.home_state,
            "home_state_source": guest.home_state_source,
            "locked": bool(guest.home_state),
            "requires_manual_choice": guest.home_state is None,
            "outside_india": (geo.country_code not in (None, "IN")),
            "is_vpn": bool(guest.location_unverified or geo.is_vpn_or_proxy),
            "detected_state": geo.state,
            "mismatch_detected": bool(guest.home_state and geo.state and guest.home_state.lower() != geo.state.lower()),
            "allowed_states": allowed_info["allowed_states"],
            "extra_states": [],
            "max_extra_slots": 0,
            "all_india": False,
        }

    # Authenticated user
    # If user has no home_state yet and geo detected one, auto-assign once
    if not user.home_state and geo.state and not geo.is_vpn_or_proxy:
        user.home_state = geo.state
        user.home_state_source = "auto_detected"
        user.home_state_locked_at = datetime.utcnow()
        user.detection_confidence = geo.confidence
        db.add(GeoDetectionLog(
            id=f"geo_{uuid.uuid4().hex[:12]}",
            actor_type="user",
            actor_id=user.id,
            ip_hash=ip_h,
            detected_state=geo.state,
            country_code=geo.country_code,
            is_vpn_or_proxy=False,
            provider=geo.provider,
            confidence=geo.confidence,
        ))
        await db.commit()

    allowed_info = await get_allowed_states_for_actor(db, user)
    pending_req = (await db.execute(
        select(StateChangeRequest)
        .where(StateChangeRequest.user_id == user.id, StateChangeRequest.status == "pending")
        .order_by(StateChangeRequest.created_at.desc())
    )).scalars().first()

    cooldown_days = int(await get_setting(db, "state_change_cooldown_days", "90"))
    cooldown_remaining = 0
    if user.last_change_request_at and user.home_state_source != "migrated":
        elapsed = (datetime.utcnow() - user.last_change_request_at).days
        cooldown_remaining = max(0, cooldown_days - elapsed)

    mismatch = bool(
        (not allowed_info["all_india"])
        and user.home_state
        and geo.state
        and user.home_state.lower() != geo.state.lower()
    )

    return {
        "actor_type": "user",
        "home_state": user.home_state,
        "home_state_source": user.home_state_source,
        "locked": bool(user.home_state_locked_at),
        "requires_manual_choice": user.home_state is None,
        "outside_india": (geo.country_code not in (None, "IN")),
        "is_vpn": bool(user.location_unverified or geo.is_vpn_or_proxy),
        "detected_state": geo.state,
        "mismatch_detected": mismatch,
        "allowed_states": allowed_info["allowed_states"],
        "extra_states": allowed_info["extra_states"],
        "max_extra_slots": allowed_info["max_extra_slots"],
        "all_india": allowed_info["all_india"],
        "cooldown_days_remaining": cooldown_remaining,
        "pending_change_request": {
            "id": pending_req.id,
            "to_state": pending_req.to_state,
            "created_at": pending_req.created_at.isoformat(),
        } if pending_req else None,
    }


class ChooseStateRequest(BaseModel):
    state: str = Field(..., min_length=2, max_length=100)


@router.post("/choose")
async def choose_home_state(
    payload: ChooseStateRequest,
    request: Request,
    response: Response,
    user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    ip_h = hash_value(get_client_ip(request))
    check_rate_limit(f"loc_choose:{ip_h}", max_requests=10, window_seconds=300)

    canonical = resolve_canonical_state(payload.state)
    if not canonical:
        raise HTTPException(status_code=400, detail="Please select a valid Indian state or union territory.")

    if not user:
        guest = await get_or_create_guest(request, response, db)
        if guest.home_state:
            raise HTTPException(
                status_code=403,
                detail=f"Your free guest state is already locked to {guest.home_state}.",
            )
        guest.home_state = canonical
        guest.home_state_source = "chosen"
        guest.home_state_locked_at = datetime.utcnow()
        set_guest_state_cookie(response, canonical)
        db.add(AuditLog(
            actor_user_id=None,
            action="guest_home_state_chosen",
            target_type="guest",
            target_id=guest.id,
            details_json=json.dumps({"state": canonical}),
            ip_hash=ip_h,
        ))
        await db.commit()
        return {"home_state": canonical, "locked": True}

    if user.home_state and user.home_state_locked_at:
        raise HTTPException(
            status_code=403,
            detail=f"Your Home State is locked to {user.home_state}. Use 'Request change' in Settings.",
        )

    user.home_state = canonical
    user.home_state_source = "chosen"
    user.home_state_locked_at = datetime.utcnow()
    db.add(AuditLog(
        actor_user_id=user.id,
        actor_email=user.email,
        action="user_home_state_chosen",
        target_type="user",
        target_id=user.id,
        details_json=json.dumps({"state": canonical}),
        ip_hash=ip_h,
    ))
    await db.commit()
    return {"home_state": canonical, "locked": True}


class ChangeStateRequestPayload(BaseModel):
    to_state: str = Field(..., min_length=2, max_length=100)
    reason: str = Field(..., min_length=5, max_length=500)


@router.post("/change-request")
async def request_home_state_change(
    payload: ChangeStateRequestPayload,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ip_h = hash_value(get_client_ip(request))
    check_rate_limit(f"loc_change:{user.id}", max_requests=5, window_seconds=3600)

    canonical = resolve_canonical_state(payload.to_state)
    if not canonical:
        raise HTTPException(status_code=400, detail="Invalid Indian state or union territory.")
    if user.home_state and canonical.lower() == user.home_state.lower():
        raise HTTPException(status_code=400, detail=f"Your Home State is already {user.home_state}.")

    # Pending request check
    pending = (await db.execute(
        select(StateChangeRequest).where(StateChangeRequest.user_id == user.id, StateChangeRequest.status == "pending")
    )).scalars().first()
    if pending:
        raise HTTPException(status_code=409, detail="You already have a pending Home State change request.")

    # Cooldown check (skipped for unlocked migrated users' first change)
    cooldown_days = int(await get_setting(db, "state_change_cooldown_days", "90"))
    is_unlocked_migrated = (user.home_state_source == "migrated" and user.home_state_locked_at is None)
    if user.last_change_request_at and not is_unlocked_migrated:
        elapsed = (datetime.utcnow() - user.last_change_request_at).days
        if elapsed < cooldown_days:
            remaining = cooldown_days - elapsed
            raise HTTPException(
                status_code=429,
                detail=f"You can request a Home State change once every {cooldown_days} days ({remaining} days remaining).",
            )

    # First change ever (or unlocked migrated user) is auto-approved; subsequent changes require admin approval
    prior_approved = (await db.execute(
        select(StateChangeRequest).where(
            StateChangeRequest.user_id == user.id,
            StateChangeRequest.status == "approved",
        )
    )).scalars().first()

    auto_approve = (prior_approved is None) or is_unlocked_migrated
    now = datetime.utcnow()

    req_row = StateChangeRequest(
        id=f"scr_{uuid.uuid4().hex[:12]}",
        user_id=user.id,
        from_state=user.home_state,
        to_state=canonical,
        reason=payload.reason.strip(),
        status="approved" if auto_approve else "pending",
        auto_approved=auto_approve,
        reviewed_by="system_auto" if auto_approve else None,
        reviewed_at=now if auto_approve else None,
    )
    db.add(req_row)

    if auto_approve:
        user.home_state = canonical
        user.home_state_source = "chosen"
        user.home_state_locked_at = now
        user.last_change_request_at = now

    db.add(AuditLog(
        actor_user_id=user.id,
        actor_email=user.email,
        action="home_state_change_requested",
        target_type="state_change_request",
        target_id=req_row.id,
        details_json=json.dumps({
            "from_state": req_row.from_state,
            "to_state": canonical,
            "auto_approved": auto_approve,
        }),
        ip_hash=ip_h,
    ))
    await db.commit()

    return {
        "id": req_row.id,
        "status": req_row.status,
        "auto_approved": auto_approve,
        "home_state": user.home_state,
        "message": (
            f"Home State updated to {canonical}."
            if auto_approve
            else "Change request submitted for admin review."
        ),
    }


class ExtraStatesUpdateRequest(BaseModel):
    states: List[str]


@router.put("/extra-states")
async def update_starter_extra_states(
    payload: ExtraStatesUpdateRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ip_h = hash_value(get_client_ip(request))
    check_rate_limit(f"extra_states:{user.id}", max_requests=10, window_seconds=3600)

    plan, _ = await get_user_effective_plan(db, user)
    if plan.max_states <= 1:
        raise HTTPException(status_code=403, detail="Extra states require the Starter plan or higher.")
    if plan.max_states >= 36:
        return {"message": "Your plan already includes all 36 Indian states & UTs.", "extra_states": []}

    slots = int(await get_setting(db, "starter_extra_states_count", "2"))
    canonical_list: List[str] = []
    for s in payload.states:
        c = resolve_canonical_state(s)
        if not c:
            raise HTTPException(status_code=400, detail=f"Invalid state: {s}")
        if user.home_state and c.lower() == user.home_state.lower():
            continue
        if c not in canonical_list:
            canonical_list.append(c)

    if len(canonical_list) > slots:
        raise HTTPException(
            status_code=400,
            detail=f"Your {plan.name} plan allows up to {slots} extra states beyond your Home State.",
        )

    # 30-day change limit if extra states were already set
    existing = (await db.execute(
        select(UserExtraState).where(
            UserExtraState.user_id == user.id,
            UserExtraState.granted_by == "starter_choice",
        )
    )).scalars().all()
    if existing:
        latest_update = max(e.updated_at or e.created_at for e in existing)
        if (datetime.utcnow() - latest_update).days < 30:
            days_left = 30 - (datetime.utcnow() - latest_update).days
            raise HTTPException(
                status_code=429,
                detail=f"Extra states can be changed once every 30 days ({days_left} days remaining).",
            )

    await db.execute(
        delete(UserExtraState).where(
            UserExtraState.user_id == user.id,
            UserExtraState.granted_by == "starter_choice",
        )
    )
    for st in canonical_list:
        db.add(UserExtraState(
            id=f"ues_{uuid.uuid4().hex[:12]}",
            user_id=user.id,
            state_name=st,
            granted_by="starter_choice",
        ))
    db.add(AuditLog(
        actor_user_id=user.id,
        actor_email=user.email,
        action="starter_extra_states_updated",
        target_type="user",
        target_id=user.id,
        details_json=json.dumps({"extra_states": canonical_list}),
        ip_hash=ip_h,
    ))
    await db.commit()
    return {"extra_states": canonical_list, "remaining_slots": max(0, slots - len(canonical_list))}


class LockedStateClickRequest(BaseModel):
    state: str


@router.post("/locked-click")
async def track_locked_state_click(
    payload: LockedStateClickRequest,
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    ip_h = hash_value(get_client_ip(request))
    canonical = resolve_canonical_state(payload.state) or payload.state
    db.add(AnalyticsEvent(
        user_id=user.id if user else None,
        event_name="locked_state_clicked",
        properties_json=json.dumps({"state": canonical}),
        ip_hash=ip_h,
    ))
    await db.commit()
    return {"tracked": True}

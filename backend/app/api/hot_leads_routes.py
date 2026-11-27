"""
Hot Leads API Routes:
  - Public inbound quote form, WhatsApp click tracking, and Google Ads webhook
  - Admin-only Hot Leads CRM, Kanban pipeline, filters, bulk actions, CSV/Excel export
  - Website health checker, Score weights config, Message templates, Proposal PDF
  - Intent Sources (RSS / Official API / Email Alert / CSV import)
  - Do Not Contact (DNC) list, DPDP export/deletion, Follow-up reminders & Audit Log
"""
from __future__ import annotations

import csv
import io
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import APIRouter, Depends, File, Header, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.database import get_db
from app.models.entities import (
    AuditLog,
    DoNotContactEntry,
    HotLead,
    HotLeadActivity,
    HotLeadAttachment,
    IntentSourceConfig,
    User,
)
from app.services.auth import check_rate_limit, get_client_ip, hash_value, get_admin_user as require_admin
from app.services.email_service import EmailService
from app.services.hot_leads import (
    INTENT_SOURCE_REGISTRY,
    PIPELINE_STAGES,
    SCORE_WEIGHT_LABELS,
    check_website_health,
    compute_hot_lead_score,
    extract_phone_digits as clean_phone_number,
    generate_proposal_pdf,
    get_score_weights,
    is_do_not_contact,
    parse_public_requests_csv,
    render_message_templates,
    save_score_weights,
)

logger = logging.getLogger("leadharvest.hot_leads_api")
router = APIRouter(tags=["Hot Leads"])


# ---------------------------------------------------------------------------
# Helpers & Audit
# ---------------------------------------------------------------------------
async def _audit(
    db: AsyncSession,
    admin: User,
    action: str,
    target_type: str,
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
    ))
    await db.commit()


def _serialize_lead(lead: HotLead) -> Dict[str, Any]:
    return {
        "id": lead.id,
        "source_type": lead.source_type,
        "source_name": lead.source_name,
        "source_url": lead.source_url,
        "terms_note": lead.terms_note,
        "name": lead.name,
        "business_name": lead.business_name,
        "phone": lead.phone,
        "phone_clean": lead.phone_clean,
        "email": lead.email,
        "business_type": lead.business_type,
        "city": lead.city,
        "state": lead.state,
        "website": lead.website,
        "budget_range": lead.budget_range,
        "timeline": lead.timeline,
        "notes_summary": lead.notes_summary,
        "utm_source": lead.utm_source,
        "utm_medium": lead.utm_medium,
        "utm_campaign": lead.utm_campaign,
        "utm_term": lead.utm_term,
        "utm_content": lead.utm_content,
        "landing_page": lead.landing_page,
        "score": lead.score,
        "temperature": lead.temperature,
        "score_breakdown": json.loads(lead.score_breakdown_json) if lead.score_breakdown_json else [],
        "signals": json.loads(lead.signals_json) if lead.signals_json else [],
        "website_health": json.loads(lead.website_health_json) if lead.website_health_json else None,
        "rating": lead.rating,
        "review_count": lead.review_count,
        "stage": lead.stage,
        "deal_value_inr": lead.deal_value_inr,
        "expected_close_date": lead.expected_close_date.isoformat() if lead.expected_close_date else None,
        "lost_reason": lead.lost_reason,
        "owner_name": lead.owner_name,
        "next_followup_at": lead.next_followup_at.isoformat() if lead.next_followup_at else None,
        "first_contacted_at": lead.first_contacted_at.isoformat() if lead.first_contacted_at else None,
        "consent_given": lead.consent_given,
        "consent_record": lead.consent_record,
        "do_not_contact": lead.do_not_contact,
        "dnc_reason": lead.dnc_reason,
        "created_at": lead.created_at.isoformat() if lead.created_at else None,
        "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
    }


# ---------------------------------------------------------------------------
# Public Inbound Endpoints (Quote Form, WhatsApp CTA, Google Ads Webhook)
# ---------------------------------------------------------------------------
class QuoteInboundRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    phone: str = Field(..., min_length=6, max_length=32)
    email: Optional[str] = Field(None, max_length=255)
    business_name: Optional[str] = Field(None, max_length=255)
    business_type: str = Field(..., min_length=2, max_length=150)
    city: str = Field(..., min_length=2, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    website: Optional[str] = Field(None, max_length=500)
    budget_range: Optional[str] = Field(None, max_length=100)
    timeline: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=1000)
    consent: bool = Field(...)
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_term: Optional[str] = None
    utm_content: Optional[str] = None
    landing_page: Optional[str] = None


@router.post("/api/inbound/quote")
async def submit_website_quote(
    payload: QuoteInboundRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    ip_h = hash_value(f"ip:{get_client_ip(request)}")
    check_rate_limit(f"quote:{ip_h}", max_requests=10, window_seconds=300)

    if not payload.consent:
        raise HTTPException(status_code=400, detail="Please check the consent box so we can contact you regarding your quote.")

    phone_clean = clean_phone_number(payload.phone)
    email_clean = payload.email.strip().lower() if payload.email else None
    dnc, dnc_reason = await is_do_not_contact(db, phone_clean=phone_clean, email=email_clean)

    weights = await get_score_weights(db)
    bname = (payload.business_name or f"{payload.name} ({payload.business_type})").strip()
    score_input = {
        "source_type": "inbound",
        "source_name": "website_quote_form",
        "website": payload.website,
        "phone_clean": phone_clean,
        "budget_range": payload.budget_range,
        "timeline": payload.timeline,
        "contacted_directly": True,
        "requested_quote": True,
    }
    score, temp, breakdown = compute_hot_lead_score(score_input, weights)

    lead = HotLead(
        id=f"hl_{uuid.uuid4().hex[:12]}",
        source_type="inbound",
        source_name="website_quote_form",
        source_url=payload.landing_page or "/contact",
        terms_note="Direct inbound quote submission with explicit user consent",
        name=payload.name.strip(),
        business_name=bname,
        phone=payload.phone.strip(),
        phone_clean=phone_clean,
        email=email_clean,
        business_type=payload.business_type.strip(),
        city=payload.city.strip(),
        state=(payload.state or "").strip() or None,
        website=(payload.website or "").strip() or None,
        budget_range=payload.budget_range,
        timeline=payload.timeline,
        notes_summary=payload.notes,
        utm_source=payload.utm_source,
        utm_medium=payload.utm_medium,
        utm_campaign=payload.utm_campaign,
        utm_term=payload.utm_term,
        utm_content=payload.utm_content,
        landing_page=payload.landing_page,
        score=score,
        temperature=temp,
        score_breakdown_json=json.dumps(breakdown),
        signals_json=json.dumps(["requested_quote"] + ([] if payload.website else ["no_website"])),
        stage="New",
        next_followup_at=datetime.utcnow() + timedelta(hours=2),
        consent_given=True,
        consent_record=f"Explicit quote form checkbox consent on {datetime.utcnow().isoformat()}Z from {payload.landing_page or '/contact'}",
        do_not_contact=dnc,
        dnc_reason=dnc_reason,
    )
    db.add(lead)
    db.add(HotLeadActivity(
        id=f"act_{uuid.uuid4().hex[:12]}",
        lead_id=lead.id,
        activity_type="system",
        title="Inbound quote form submitted",
        body=f"Budget: {payload.budget_range or 'N/A'} | Timeline: {payload.timeline or 'N/A'} | UTM: {payload.utm_source or 'direct'}",
    ))
    await db.commit()

    return {
        "status": "received",
        "lead_id": lead.id,
        "message": "Thank you! Our web design team will reach out within 2 business hours.",
    }


class WhatsAppClickRequest(BaseModel):
    page: Optional[str] = "/contact"
    business_type: Optional[str] = None
    city: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None


@router.post("/api/inbound/whatsapp-click")
async def track_whatsapp_cta_click(
    payload: WhatsAppClickRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    ip_h = hash_value(f"ip:{get_client_ip(request)}")
    check_rate_limit(f"waclick:{ip_h}", max_requests=20, window_seconds=300)

    weights = await get_score_weights(db)
    score, temp, breakdown = compute_hot_lead_score(
        {"source_type": "inbound", "source_name": "whatsapp_cta", "contacted_directly": True},
        weights,
    )
    lead = HotLead(
        id=f"hl_{uuid.uuid4().hex[:12]}",
        source_type="inbound",
        source_name="whatsapp_cta",
        source_url=payload.page,
        terms_note="Inbound WhatsApp click-to-chat initiated by visitor",
        name="WhatsApp Visitor",
        business_name=f"WhatsApp Inquiry ({payload.city or 'India'})",
        business_type=payload.business_type or "Website Inquiry",
        city=payload.city or "Unknown",
        utm_source=payload.utm_source,
        utm_medium=payload.utm_medium,
        utm_campaign=payload.utm_campaign,
        landing_page=payload.page,
        score=score,
        temperature=temp,
        score_breakdown_json=json.dumps(breakdown),
        signals_json=json.dumps(["whatsapp_cta"]),
        stage="New",
        consent_given=True,
        consent_record=f"Visitor clicked WhatsApp click-to-chat CTA on {payload.page} at {datetime.utcnow().isoformat()}Z",
    )
    db.add(lead)
    await db.commit()
    return {
        "lead_id": lead.id,
        "whatsapp_url": f"https://wa.me/{settings.OWNER_WHATSAPP_NUMBER}?text=Hi%20Amar%2C%20I%20would%20like%20a%20website%20quote.",
    }


@router.post("/api/webhooks/google-ads")
async def google_ads_lead_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Receives Google Ads Lead Form Extension webhook payloads.
    Verifies `google_key` in JSON body or `X-Google-Key` header.
    """
    body = await request.json()
    provided_key = body.get("google_key") or request.headers.get("X-Google-Key") or ""
    if provided_key != settings.GOOGLE_ADS_WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Invalid Google Ads webhook key.")

    # Parse Google Ads user_column_data array or flat fields
    cols: Dict[str, str] = {}
    for col in body.get("user_column_data", []):
        cid = (col.get("column_id") or col.get("column_name") or "").lower()
        cols[cid] = col.get("string_value") or ""

    name = cols.get("full_name") or body.get("name") or "Google Ads Lead"
    phone = cols.get("phone_number") or body.get("phone") or ""
    email = (cols.get("email") or body.get("email") or "").strip().lower() or None
    city = cols.get("city") or body.get("city") or ""
    bname = cols.get("company_name") or body.get("business_name") or name

    phone_clean = clean_phone_number(phone)
    dnc, dnc_reason = await is_do_not_contact(db, phone_clean=phone_clean, email=email)

    weights = await get_score_weights(db)
    score, temp, breakdown = compute_hot_lead_score(
        {
            "source_type": "inbound",
            "source_name": "google_ads_webhook",
            "phone_clean": phone_clean,
            "contacted_directly": True,
            "requested_quote": True,
        },
        weights,
    )

    lead = HotLead(
        id=f"hl_{uuid.uuid4().hex[:12]}",
        source_type="inbound",
        source_name="google_ads_webhook",
        source_url="google_ads_lead_form",
        terms_note="Google Ads Lead Form Extension submission with user consent",
        name=name,
        business_name=bname,
        phone=phone,
        phone_clean=phone_clean,
        email=email,
        city=city,
        utm_source="google",
        utm_medium="cpc",
        utm_campaign=str(body.get("campaign_id") or "google_ads"),
        score=score,
        temperature=temp,
        score_breakdown_json=json.dumps(breakdown),
        signals_json=json.dumps(["requested_quote"]),
        stage="New",
        next_followup_at=datetime.utcnow() + timedelta(hours=1),
        consent_given=True,
        consent_record=f"Google Ads Lead Form webhook (lead_id={body.get('lead_id', 'n/a')}) at {datetime.utcnow().isoformat()}Z",
        do_not_contact=dnc,
        dnc_reason=dnc_reason,
    )
    db.add(lead)
    await db.commit()
    return {"status": "accepted", "lead_id": lead.id}


# ---------------------------------------------------------------------------
# Admin Hot Leads Dashboard & Stats
# ---------------------------------------------------------------------------
@router.get("/api/admin/hot-leads/stats")
async def get_hot_leads_stats(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    res = await db.execute(select(HotLead))
    all_leads = res.scalars().all()

    new_this_week = sum(1 for l in all_leads if l.created_at and l.created_at >= week_ago and l.temperature == "Hot")
    won_leads = [l for l in all_leads if l.stage == "Won"]
    active_pipeline = [l for l in all_leads if l.stage not in ("Won", "Lost")]
    revenue_won = sum(l.deal_value_inr or 0 for l in won_leads)
    pipeline_value = sum(l.deal_value_inr or 0 for l in active_pipeline)

    response_hours = [
        max(0.1, (l.first_contacted_at - l.created_at).total_seconds() / 3600.0)
        for l in all_leads
        if l.first_contacted_at and l.created_at and l.first_contacted_at >= l.created_at
    ]
    avg_response_hours = round(sum(response_hours) / len(response_hours), 1) if response_hours else 0.0

    # Conversion rate by source_type
    by_source: Dict[str, Dict[str, Any]] = {}
    for stype in ("inbound", "public_request", "signal"):
        subset = [l for l in all_leads if l.source_type == stype]
        won_cnt = sum(1 for l in subset if l.stage == "Won")
        by_source[stype] = {
            "total": len(subset),
            "won": won_cnt,
            "conversion_rate": round((won_cnt / len(subset) * 100), 1) if subset else 0.0,
        }

    # Today's focus: due today or overdue follow-ups
    due_today = [
        _serialize_lead(l)
        for l in all_leads
        if l.next_followup_at and l.stage not in ("Won", "Lost") and l.next_followup_at <= today_end
    ]
    overdue_count = sum(1 for l in all_leads if l.next_followup_at and l.stage not in ("Won", "Lost") and l.next_followup_at < now)

    return {
        "total_leads": len(all_leads),
        "new_hot_this_week": new_this_week,
        "avg_response_hours": avg_response_hours,
        "revenue_won_inr": revenue_won,
        "pipeline_value_inr": pipeline_value,
        "won_count": len(won_leads),
        "lost_count": sum(1 for l in all_leads if l.stage == "Lost"),
        "conversion_by_source": by_source,
        "overdue_followups": overdue_count,
        "todays_focus": sorted(due_today, key=lambda x: x["score"], reverse=True)[:10],
    }


# ---------------------------------------------------------------------------
# List, Search, Filter, Sort, Export & Bulk Actions
# ---------------------------------------------------------------------------
@router.get("/api/admin/hot-leads")
async def list_hot_leads(
    source_type: Optional[str] = None,
    stage: Optional[str] = None,
    city: Optional[str] = None,
    category: Optional[str] = None,
    min_score: Optional[int] = None,
    owner: Optional[str] = None,
    q: Optional[str] = None,
    date_from: Optional[str] = None,
    sort_by: str = "score",
    sort_dir: str = "desc",
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    query = select(HotLead)
    if source_type:
        query = query.where(HotLead.source_type == source_type)
    if stage:
        query = query.where(HotLead.stage == stage)
    if city:
        query = query.where(HotLead.city.ilike(f"%{city}%"))
    if category:
        query = query.where(HotLead.business_type.ilike(f"%{category}%"))
    if min_score is not None:
        query = query.where(HotLead.score >= min_score)
    if owner:
        query = query.where(HotLead.owner_name.ilike(f"%{owner}%"))
    if date_from:
        try:
            dt = datetime.fromisoformat(date_from)
            query = query.where(HotLead.created_at >= dt)
        except ValueError:
            pass
    if q:
        like = f"%{q}%"
        query = query.where(
            (HotLead.business_name.ilike(like))
            | (HotLead.name.ilike(like))
            | (HotLead.phone.ilike(like))
            | (HotLead.email.ilike(like))
            | (HotLead.city.ilike(like))
        )

    sort_col = getattr(HotLead, sort_by, HotLead.score)
    query = query.order_by(sort_col.desc() if sort_dir == "desc" else sort_col.asc())

    res = await db.execute(query)
    items = [_serialize_lead(l) for l in res.scalars().all()]
    return {"items": items, "total": len(items)}


@router.get("/api/admin/hot-leads/export")
async def export_hot_leads(
    format: str = Query("csv", pattern="^(csv|xlsx)$"),
    source_type: Optional[str] = None,
    stage: Optional[str] = None,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    query = select(HotLead).order_by(HotLead.score.desc())
    if source_type:
        query = query.where(HotLead.source_type == source_type)
    if stage:
        query = query.where(HotLead.stage == stage)
    leads = (await db.execute(query)).scalars().all()

    rows = [
        {
            "ID": l.id,
            "Business Name": l.business_name,
            "Contact Name": l.name or "",
            "Phone": l.phone_clean or l.phone or "",
            "Email": l.email or "",
            "Category": l.business_type or "",
            "City": l.city or "",
            "State": l.state or "",
            "Website": l.website or "",
            "Source Type": l.source_type,
            "Source Name": l.source_name,
            "Score": l.score,
            "Temperature": l.temperature,
            "Stage": l.stage,
            "Deal Value (INR)": l.deal_value_inr,
            "Do Not Contact": "YES" if l.do_not_contact else "NO",
            "Consent": "YES" if l.consent_given else "NO",
            "Created At": l.created_at.strftime("%Y-%m-%d %H:%M") if l.created_at else "",
        }
        for l in leads
    ]
    await _audit(db, admin, "hot_leads_export", "hot_lead", details={"format": format, "count": len(rows)})

    df = pd.DataFrame(rows)
    if format == "xlsx":
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Hot Leads")
        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=hot_leads_export.xlsx"},
        )

    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    csv_buf.seek(0)
    return StreamingResponse(
        iter([csv_buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=hot_leads_export.csv"},
    )


class BulkActionRequest(BaseModel):
    lead_ids: List[str]
    action: str  # change_stage | mark_dnc | delete
    stage: Optional[str] = None
    lost_reason: Optional[str] = None


@router.post("/api/admin/hot-leads/bulk")
async def bulk_update_hot_leads(
    payload: BulkActionRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if not payload.lead_ids:
        return {"updated": 0}
    res = await db.execute(select(HotLead).where(HotLead.id.in_(payload.lead_ids)))
    leads = res.scalars().all()
    count = 0
    for l in leads:
        if payload.action == "change_stage" and payload.stage in PIPELINE_STAGES:
            l.stage = payload.stage
            if payload.stage == "Contacted" and not l.first_contacted_at:
                l.first_contacted_at = datetime.utcnow()
            if payload.stage == "Lost" and payload.lost_reason:
                l.lost_reason = payload.lost_reason
            count += 1
        elif payload.action == "mark_dnc":
            l.do_not_contact = True
            l.dnc_reason = "Bulk marked Do Not Contact by admin"
            count += 1
        elif payload.action == "delete":
            await db.delete(l)
            count += 1
    await db.commit()
    await _audit(db, admin, f"hot_leads_bulk_{payload.action}", "hot_lead", details={"count": count})
    return {"updated": count}


# ---------------------------------------------------------------------------
# Score Weights Config (must come before /{lead_id} wildcard)
# ---------------------------------------------------------------------------
@router.get("/api/admin/hot-leads/config/weights")
async def get_hot_lead_weights(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    weights = await get_score_weights(db)
    return {"weights": weights, "labels": SCORE_WEIGHT_LABELS}


@router.put("/api/admin/hot-leads/config/weights")
async def update_hot_lead_weights(
    weights: Dict[str, int],
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    saved = await save_score_weights(db, weights)
    # Recompute scores for existing leads
    leads = (await db.execute(select(HotLead))).scalars().all()
    for l in leads:
        signals = json.loads(l.signals_json) if l.signals_json else []
        health = json.loads(l.website_health_json) if l.website_health_json else {}
        score, temp, breakdown = compute_hot_lead_score(
            {
                "source_type": l.source_type,
                "source_name": l.source_name,
                "website": l.website,
                "phone_clean": l.phone_clean,
                "rating": l.rating,
                "budget_range": l.budget_range,
                "timeline": l.timeline,
                "signals": signals,
                "website_health": health,
            },
            saved,
        )
        l.score = score
        l.temperature = temp
        l.score_breakdown_json = json.dumps(breakdown)
    await db.commit()
    await _audit(db, admin, "hot_leads_weights_updated", "app_setting", "hot_lead_score_weights", saved)
    return {"weights": saved, "recomputed_leads": len(leads)}


# ---------------------------------------------------------------------------
# Intent Sources & CSV Import
# ---------------------------------------------------------------------------
@router.get("/api/admin/hot-leads/sources")
async def list_intent_sources(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(select(IntentSourceConfig).order_by(IntentSourceConfig.created_at.desc()))).scalars().all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "source_kind": r.source_kind,
            "endpoint_or_query": r.endpoint_or_query,
            "terms_note": r.terms_note,
            "is_active": r.is_active,
            "last_synced_at": r.last_synced_at.isoformat() if r.last_synced_at else None,
            "leads_imported": r.leads_imported,
        }
        for r in rows
    ]


class CreateIntentSourceRequest(BaseModel):
    name: str
    source_kind: str = Field(..., pattern="^(rss|official_api|email_alert|manual)$")
    endpoint_or_query: Optional[str] = None
    terms_note: str = Field(..., min_length=5)


@router.post("/api/admin/hot-leads/sources")
async def create_intent_source(
    payload: CreateIntentSourceRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    src = IntentSourceConfig(
        id=f"src_{uuid.uuid4().hex[:10]}",
        name=payload.name,
        source_kind=payload.source_kind,
        endpoint_or_query=payload.endpoint_or_query,
        terms_note=payload.terms_note,
        is_active=True,
    )
    db.add(src)
    await db.commit()
    await _audit(db, admin, "intent_source_created", "intent_source", src.id, {"name": src.name})
    return {"id": src.id, "name": src.name}


@router.post("/api/admin/hot-leads/sources/{source_id}/sync")
async def sync_intent_source(
    source_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    src = (await db.execute(select(IntentSourceConfig).where(IntentSourceConfig.id == source_id))).scalar_one_or_none()
    if not src:
        raise HTTPException(status_code=404, detail="Intent source not found")
    adapter = INTENT_SOURCE_REGISTRY.get(src.source_kind)
    if not adapter or not src.endpoint_or_query:
        raise HTTPException(status_code=400, detail="Source kind cannot be auto-synced without an endpoint.")
    try:
        raw_items = await adapter.fetch_leads(src.endpoint_or_query)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Sync failed: {str(exc)}")

    weights = await get_score_weights(db)
    added = 0
    for item in raw_items:
        bname = (item.get("business_name") or "Public Request").strip()
        phone = item.get("phone") or ""
        phone_clean = clean_phone_number(phone)
        dnc, dnc_reason = await is_do_not_contact(db, phone_clean=phone_clean, email=item.get("email"))
        score, temp, breakdown = compute_hot_lead_score(
            {"source_type": "public_request", "source_name": src.source_kind, "phone_clean": phone_clean, "signals": item.get("signals") or ["recently_listed"]},
            weights,
        )
        db.add(HotLead(
            id=f"hl_{uuid.uuid4().hex[:12]}",
            source_type="public_request",
            source_name=src.source_kind,
            source_url=item.get("source_url"),
            terms_note=src.terms_note,
            name=item.get("name") or bname,
            business_name=bname,
            phone=phone,
            phone_clean=phone_clean,
            email=item.get("email"),
            city=item.get("city") or "",
            notes_summary=item.get("notes_summary"),
            score=score,
            temperature=temp,
            score_breakdown_json=json.dumps(breakdown),
            signals_json=json.dumps(item.get("signals") or ["recently_listed"]),
            stage="New",
            consent_given=False,
            consent_record=f"Public request from {src.name} ({src.terms_note})",
            do_not_contact=dnc,
            dnc_reason=dnc_reason,
        ))
        added += 1

    src.last_synced_at = datetime.utcnow()
    src.leads_imported += added
    await db.commit()
    return {"imported": added}


@router.post("/api/admin/hot-leads/import-csv")
async def import_public_requests_csv(
    file: UploadFile = File(...),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    content = await file.read()
    rows, errors = parse_public_requests_csv(content)
    if not rows and errors:
        raise HTTPException(status_code=400, detail={"message": "CSV validation failed", "errors": errors})

    weights = await get_score_weights(db)
    imported = 0
    for r in rows:
        dnc, dnc_reason = await is_do_not_contact(db, phone_clean=r.get("phone_clean"), email=r.get("email"))
        score, temp, breakdown = compute_hot_lead_score(
            {
                "source_type": "public_request",
                "source_name": "csv_import",
                "website": r.get("website"),
                "phone_clean": r.get("phone_clean"),
                "budget_range": r.get("budget_range"),
                "timeline": r.get("timeline"),
                "signals": ["recently_listed"],
            },
            weights,
        )
        db.add(HotLead(
            id=f"hl_{uuid.uuid4().hex[:12]}",
            source_type="public_request",
            source_name="csv_import",
            source_url=r.get("source_url"),
            terms_note=r.get("terms_note"),
            name=r.get("name"),
            business_name=r["business_name"],
            phone=r.get("phone"),
            phone_clean=r.get("phone_clean"),
            email=r.get("email"),
            business_type=r.get("business_type"),
            city=r.get("city"),
            state=r.get("state"),
            website=r.get("website"),
            budget_range=r.get("budget_range"),
            timeline=r.get("timeline"),
            notes_summary=r.get("notes_summary"),
            score=score,
            temperature=temp,
            score_breakdown_json=json.dumps(breakdown),
            signals_json=json.dumps(["recently_listed"]),
            stage="New",
            consent_given=False,
            consent_record=f"CSV import by {admin.email}: {r.get('terms_note')}",
            do_not_contact=dnc,
            dnc_reason=dnc_reason,
        ))
        imported += 1

    await db.commit()
    await _audit(db, admin, "hot_leads_csv_import", "hot_lead", details={"imported": imported, "errors": len(errors)})
    return {"imported": imported, "errors": errors}


# ---------------------------------------------------------------------------
# Do Not Contact (DNC) Management & Reminder Digest
# ---------------------------------------------------------------------------
@router.get("/api/admin/hot-leads/dnc")
async def list_dnc_entries(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(select(DoNotContactEntry).order_by(DoNotContactEntry.created_at.desc()))).scalars().all()
    return [
        {
            "id": r.id,
            "phone_clean": r.phone_clean,
            "email": r.email,
            "reason": r.reason,
            "source": r.source,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


class DncCreateRequest(BaseModel):
    phone: Optional[str] = None
    email: Optional[str] = None
    reason: str = Field(..., min_length=2)
    source: str = "admin"


@router.post("/api/admin/hot-leads/dnc")
async def add_dnc_entry(
    payload: DncCreateRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    phone_clean = clean_phone_number(payload.phone) if payload.phone else None
    email_clean = payload.email.strip().lower() if payload.email else None
    if not phone_clean and not email_clean:
        raise HTTPException(status_code=400, detail="Provide a valid phone number or email.")

    entry = DoNotContactEntry(
        id=f"dnc_{uuid.uuid4().hex[:10]}",
        phone_clean=phone_clean,
        email=email_clean,
        reason=payload.reason,
        source=payload.source,
    )
    db.add(entry)

    # Sync existing HotLeads matching this phone/email
    q = select(HotLead)
    if phone_clean and email_clean:
        q = q.where((HotLead.phone_clean == phone_clean) | (HotLead.email == email_clean))
    elif phone_clean:
        q = q.where(HotLead.phone_clean == phone_clean)
    else:
        q = q.where(HotLead.email == email_clean)

    for hl in (await db.execute(q)).scalars().all():
        hl.do_not_contact = True
        hl.dnc_reason = payload.reason

    await db.commit()
    await _audit(db, admin, "dnc_added", "do_not_contact", entry.id, {"reason": payload.reason})
    return {"id": entry.id, "phone_clean": phone_clean, "email": email_clean}


@router.delete("/api/admin/hot-leads/dnc/{entry_id}")
async def remove_dnc_entry(
    entry_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    entry = (await db.execute(select(DoNotContactEntry).where(DoNotContactEntry.id == entry_id))).scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="DNC entry not found")
    await db.delete(entry)
    await db.commit()
    return {"deleted": True}


@router.post("/api/admin/hot-leads/reminders/send-digest")
async def send_followup_reminder_digest(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.utcnow()
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    due = (await db.execute(
        select(HotLead).where(
            HotLead.next_followup_at <= today_end,
            HotLead.stage.notin_(["Won", "Lost"]),
        )
    )).scalars().all()

    if not due:
        return {"sent": False, "count": 0, "message": "No follow-ups due today."}

    lines = [f"- {l.business_name} ({l.city or 'India'}) | Score {l.score} | Stage: {l.stage}" for l in due[:20]]
    body = "<ul>" + "".join(f"<li>{x}</li>" for x in lines) + "</ul>"
    await EmailService().send(admin.email, f"Hot Leads Reminder: {len(due)} follow-ups due", "Hot Leads Follow-Up Digest", body)
    await _audit(db, admin, "hot_leads_reminder_digest_sent", "hot_lead", details={"count": len(due)})
    return {"sent": True, "count": len(due), "recipient": admin.email}


# ---------------------------------------------------------------------------
# Single Lead CRUD, Health Check, Templates, Proposal PDF, DPDP Export/Delete
# ---------------------------------------------------------------------------
class ManualLeadCreateRequest(BaseModel):
    business_name: str = Field(..., min_length=2)
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    business_type: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    website: Optional[str] = None
    budget_range: Optional[str] = None
    timeline: Optional[str] = None
    source_type: str = "public_request"
    source_name: str = "manual_entry"
    terms_note: str = "Manually entered public request"
    notes_summary: Optional[str] = None
    deal_value_inr: int = 12000


@router.post("/api/admin/hot-leads")
async def create_hot_lead_manual(
    payload: ManualLeadCreateRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    phone_clean = clean_phone_number(payload.phone) if payload.phone else None
    email_clean = payload.email.strip().lower() if payload.email else None
    dnc, dnc_reason = await is_do_not_contact(db, phone_clean=phone_clean, email=email_clean)

    weights = await get_score_weights(db)
    score, temp, breakdown = compute_hot_lead_score(
        {
            "source_type": payload.source_type,
            "source_name": payload.source_name,
            "website": payload.website,
            "phone_clean": phone_clean,
            "budget_range": payload.budget_range,
            "timeline": payload.timeline,
            "signals": ["recently_listed"] + ([] if payload.website else ["no_website"]),
        },
        weights,
    )
    lead = HotLead(
        id=f"hl_{uuid.uuid4().hex[:12]}",
        source_type=payload.source_type,
        source_name=payload.source_name,
        terms_note=payload.terms_note,
        name=payload.name or payload.business_name,
        business_name=payload.business_name,
        phone=payload.phone,
        phone_clean=phone_clean,
        email=email_clean,
        business_type=payload.business_type,
        city=payload.city,
        state=payload.state,
        website=payload.website,
        budget_range=payload.budget_range,
        timeline=payload.timeline,
        notes_summary=payload.notes_summary,
        deal_value_inr=payload.deal_value_inr,
        score=score,
        temperature=temp,
        score_breakdown_json=json.dumps(breakdown),
        signals_json=json.dumps(["recently_listed"] + ([] if payload.website else ["no_website"])),
        stage="New",
        consent_given=payload.source_type == "inbound",
        consent_record=f"Created by admin {admin.email}: {payload.terms_note}",
        do_not_contact=dnc,
        dnc_reason=dnc_reason,
    )
    db.add(lead)
    await db.commit()
    await _audit(db, admin, "hot_lead_created", "hot_lead", lead.id)
    return _serialize_lead(lead)


@router.post("/api/admin/hot-leads/seed-demo")
async def seed_demo_hot_leads_endpoint(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    from app.services.hot_leads_seed import seed_30_hot_leads
    count = await seed_30_hot_leads(db)
    await _audit(db, admin, "hot_leads_seed_demo", "hot_lead", details={"seeded": count})
    return {"seeded": count}


@router.get("/api/admin/hot-leads/{lead_id}")
async def get_hot_lead_detail(
    lead_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    lead = (await db.execute(select(HotLead).where(HotLead.id == lead_id))).scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Hot Lead not found")

    acts = (await db.execute(
        select(HotLeadActivity).where(HotLeadActivity.lead_id == lead_id).order_by(HotLeadActivity.created_at.desc())
    )).scalars().all()
    atts = (await db.execute(
        select(HotLeadAttachment).where(HotLeadAttachment.lead_id == lead_id).order_by(HotLeadAttachment.created_at.desc())
    )).scalars().all()

    await _audit(db, admin, "hot_lead_viewed", "hot_lead", lead_id)

    return {
        "lead": _serialize_lead(lead),
        "activities": [
            {
                "id": a.id,
                "activity_type": a.activity_type,
                "title": a.title,
                "body": a.body,
                "due_at": a.due_at.isoformat() if a.due_at else None,
                "completed": a.completed,
                "actor_email": a.actor_email,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in acts
        ],
        "attachments": [
            {
                "id": att.id,
                "filename": att.filename,
                "mime_type": att.mime_type,
                "size_bytes": att.size_bytes,
                "created_at": att.created_at.isoformat() if att.created_at else None,
            }
            for att in atts
        ],
        "outreach": render_message_templates(lead),
    }


class HotLeadUpdateRequest(BaseModel):
    stage: Optional[str] = None
    deal_value_inr: Optional[int] = None
    expected_close_date: Optional[str] = None
    lost_reason: Optional[str] = None
    owner_name: Optional[str] = None
    next_followup_at: Optional[str] = None
    do_not_contact: Optional[bool] = None
    dnc_reason: Optional[str] = None
    website: Optional[str] = None
    budget_range: Optional[str] = None
    timeline: Optional[str] = None
    notes_summary: Optional[str] = None


@router.patch("/api/admin/hot-leads/{lead_id}")
async def update_hot_lead(
    lead_id: str,
    payload: HotLeadUpdateRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    lead = (await db.execute(select(HotLead).where(HotLead.id == lead_id))).scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Hot Lead not found")

    if payload.stage is not None:
        if payload.stage not in PIPELINE_STAGES:
            raise HTTPException(status_code=400, detail=f"Invalid stage. Must be one of: {PIPELINE_STAGES}")
        old_stage = lead.stage
        lead.stage = payload.stage
        if payload.stage == "Contacted" and not lead.first_contacted_at:
            lead.first_contacted_at = datetime.utcnow()
        if old_stage != payload.stage:
            db.add(HotLeadActivity(
                id=f"act_{uuid.uuid4().hex[:12]}",
                lead_id=lead.id,
                activity_type="stage_change",
                title=f"Stage moved: {old_stage} -> {payload.stage}",
                body=payload.lost_reason if payload.stage == "Lost" else None,
                actor_email=admin.email,
            ))

    if payload.deal_value_inr is not None:
        lead.deal_value_inr = max(0, payload.deal_value_inr)
    if payload.expected_close_date is not None:
        lead.expected_close_date = datetime.fromisoformat(payload.expected_close_date) if payload.expected_close_date else None
    if payload.lost_reason is not None:
        lead.lost_reason = payload.lost_reason
    if payload.owner_name is not None:
        lead.owner_name = payload.owner_name
    if payload.next_followup_at is not None:
        lead.next_followup_at = datetime.fromisoformat(payload.next_followup_at) if payload.next_followup_at else None
    if payload.website is not None:
        lead.website = payload.website
    if payload.budget_range is not None:
        lead.budget_range = payload.budget_range
    if payload.timeline is not None:
        lead.timeline = payload.timeline
    if payload.notes_summary is not None:
        lead.notes_summary = payload.notes_summary

    if payload.do_not_contact is not None:
        lead.do_not_contact = payload.do_not_contact
        lead.dnc_reason = payload.dnc_reason or ("Marked DNC by admin" if payload.do_not_contact else None)
        if payload.do_not_contact and (lead.phone_clean or lead.email):
            db.add(DoNotContactEntry(
                id=f"dnc_{uuid.uuid4().hex[:10]}",
                phone_clean=lead.phone_clean,
                email=lead.email,
                reason=lead.dnc_reason or "Opt-out / DNC",
                source="admin",
            ))

    await db.commit()
    await _audit(db, admin, "hot_lead_updated", "hot_lead", lead_id, payload.model_dump(exclude_none=True))
    return _serialize_lead(lead)


@router.post("/api/admin/hot-leads/{lead_id}/health-check")
async def run_lead_website_health_check(
    lead_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    lead = (await db.execute(select(HotLead).where(HotLead.id == lead_id))).scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Hot Lead not found")

    health = await check_website_health(lead.website or "")
    lead.website_health_json = json.dumps(health)

    weights = await get_score_weights(db)
    signals = json.loads(lead.signals_json) if lead.signals_json else []
    score, temp, breakdown = compute_hot_lead_score(
        {
            "source_type": lead.source_type,
            "source_name": lead.source_name,
            "website": lead.website,
            "phone_clean": lead.phone_clean,
            "rating": lead.rating,
            "budget_range": lead.budget_range,
            "timeline": lead.timeline,
            "signals": signals,
            "website_health": health,
        },
        weights,
    )
    lead.score = score
    lead.temperature = temp
    lead.score_breakdown_json = json.dumps(breakdown)

    db.add(HotLeadActivity(
        id=f"act_{uuid.uuid4().hex[:12]}",
        lead_id=lead.id,
        activity_type="health_check",
        title="Website health check completed",
        body=f"Issues: {', '.join(health.get('issues') or ['None'])} | Response: {health.get('response_ms')} ms",
        actor_email=admin.email,
    ))
    await db.commit()
    return {"health": health, "score": score, "temperature": temp, "score_breakdown": breakdown}


class ActivityCreateRequest(BaseModel):
    activity_type: str = Field("note", pattern="^(note|task|email|whatsapp)$")
    title: str = Field(..., min_length=2, max_length=255)
    body: Optional[str] = None
    due_at: Optional[str] = None


@router.post("/api/admin/hot-leads/{lead_id}/activities")
async def add_lead_activity(
    lead_id: str,
    payload: ActivityCreateRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    lead = (await db.execute(select(HotLead).where(HotLead.id == lead_id))).scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Hot Lead not found")

    if payload.activity_type in ("email", "whatsapp") and lead.do_not_contact:
        raise HTTPException(status_code=403, detail="Outreach blocked: this lead is on the Do Not Contact list.")

    due_dt = datetime.fromisoformat(payload.due_at) if payload.due_at else None
    act = HotLeadActivity(
        id=f"act_{uuid.uuid4().hex[:12]}",
        lead_id=lead_id,
        activity_type=payload.activity_type,
        title=payload.title,
        body=payload.body,
        due_at=due_dt,
        actor_email=admin.email,
    )
    db.add(act)
    if due_dt and (not lead.next_followup_at or due_dt < lead.next_followup_at):
        lead.next_followup_at = due_dt
    await db.commit()
    return {"id": act.id, "title": act.title}


@router.patch("/api/admin/hot-leads/{lead_id}/activities/{act_id}")
async def toggle_lead_activity(
    lead_id: str,
    act_id: str,
    completed: bool = True,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    act = (await db.execute(
        select(HotLeadActivity).where(HotLeadActivity.id == act_id, HotLeadActivity.lead_id == lead_id)
    )).scalar_one_or_none()
    if not act:
        raise HTTPException(status_code=404, detail="Activity not found")
    act.completed = completed
    await db.commit()
    return {"id": act.id, "completed": act.completed}


@router.post("/api/admin/hot-leads/{lead_id}/attachments")
async def upload_lead_attachment(
    lead_id: str,
    file: UploadFile = File(...),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    lead = (await db.execute(select(HotLead).where(HotLead.id == lead_id))).scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Hot Lead not found")

    settings.ATTACHMENTS_DIR.mkdir(parents=True, exist_ok=True)
    att_id = f"att_{uuid.uuid4().hex[:10]}"
    safe_name = (file.filename or "attachment.bin").replace("/", "_").replace("\\", "_")
    dest = settings.ATTACHMENTS_DIR / f"{att_id}_{safe_name}"
    data = await file.read()
    dest.write_bytes(data)

    att = HotLeadAttachment(
        id=att_id,
        lead_id=lead_id,
        filename=safe_name,
        file_path=str(dest),
        mime_type=file.content_type,
        size_bytes=len(data),
    )
    db.add(att)
    await db.commit()
    return {"id": att.id, "filename": att.filename, "size_bytes": att.size_bytes}


class ProposalRequest(BaseModel):
    package_name: str = "Growth Business Website"
    price_range: str = "Rs 9,999 - Rs 14,999"
    timeline: str = "7 Business Days"


@router.post("/api/admin/hot-leads/{lead_id}/proposal-pdf")
async def create_lead_proposal_pdf(
    lead_id: str,
    payload: ProposalRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    lead = (await db.execute(select(HotLead).where(HotLead.id == lead_id))).scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Hot Lead not found")

    pdf_path = generate_proposal_pdf(
        lead,
        package_name=payload.package_name,
        price_range=payload.price_range,
        timeline=payload.timeline,
    )
    db.add(HotLeadActivity(
        id=f"act_{uuid.uuid4().hex[:12]}",
        lead_id=lead.id,
        activity_type="proposal",
        title=f"Generated 1-page proposal PDF ({payload.package_name})",
        body=f"Price: {payload.price_range} | Timeline: {payload.timeline}",
        actor_email=admin.email,
    ))
    await db.commit()
    await _audit(db, admin, "hot_lead_proposal_generated", "hot_lead", lead_id)
    return FileResponse(path=str(pdf_path), filename=pdf_path.name, media_type="application/pdf")


@router.get("/api/admin/hot-leads/{lead_id}/gdpr-export")
async def export_single_lead_dpdp(
    lead_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    lead = (await db.execute(select(HotLead).where(HotLead.id == lead_id))).scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Hot Lead not found")
    acts = (await db.execute(select(HotLeadActivity).where(HotLeadActivity.lead_id == lead_id))).scalars().all()
    await _audit(db, admin, "hot_lead_dpdp_export", "hot_lead", lead_id)
    return {
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "lead": _serialize_lead(lead),
        "activities": [{"type": a.activity_type, "title": a.title, "body": a.body, "created_at": a.created_at.isoformat()} for a in acts],
    }


@router.delete("/api/admin/hot-leads/{lead_id}")
async def delete_hot_lead(
    lead_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    lead = (await db.execute(select(HotLead).where(HotLead.id == lead_id))).scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Hot Lead not found")
    await db.delete(lead)
    await db.commit()
    await _audit(db, admin, "hot_lead_deleted", "hot_lead", lead_id)
    return {"deleted": True}

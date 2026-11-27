"""
Hot Leads CRM, Transparent Scoring, Website Health Checker,
Pluggable Intent Sources, Message Templates, and 1-Page Proposal PDF Generator.
"""
from __future__ import annotations

import asyncio
import csv
import io
import ipaddress
import json
import logging
import re
import socket
import time
import uuid
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote, urlparse

import httpx
from fpdf import FPDF
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.models.entities import (
    AppSetting,
    DoNotContactEntry,
    HotLead,
    HotLeadActivity,
)
from app.services.normalizer import clean_phone_number


def extract_phone_digits(phone: Optional[str]) -> Optional[str]:
    if not phone:
        return None
    digits, _ = clean_phone_number(str(phone))
    return digits or None

logger = logging.getLogger("leadharvest.hot_leads")

PIPELINE_STAGES = [
    "New",
    "Contacted",
    "Meeting booked",
    "Proposal sent",
    "Negotiation",
    "Won",
    "Lost",
]

DEFAULT_SCORE_WEIGHTS: Dict[str, int] = {
    "contacted_directly": 40,
    "requested_quote": 20,
    "no_website": 15,
    "broken_or_outdated_website": 15,
    "mobile_available": 5,
    "good_rating_or_active": 5,
    "recently_listed": 10,
    "budget_stated": 10,
}

SCORE_WEIGHT_LABELS: Dict[str, str] = {
    "contacted_directly": "Contacted us directly (inbound form / WhatsApp / ads)",
    "requested_quote": "Explicitly requested a website quote",
    "no_website": "Business has no website listed",
    "broken_or_outdated_website": "Broken, non-HTTPS, slow, or non-mobile website",
    "mobile_available": "Valid 10-digit Indian mobile number available",
    "good_rating_or_active": "Good rating (>= 3.5) or active public request",
    "recently_listed": "Recently listed or fresh buying intent",
    "budget_stated": "Budget range or timeline stated",
}

DISALLOWED_SCRAPE_DOMAINS = {
    "google.com",
    "www.google.com",
    "linkedin.com",
    "www.linkedin.com",
    "facebook.com",
    "www.facebook.com",
    "instagram.com",
    "www.instagram.com",
}

_last_health_check_ts: float = 0.0


# ---------------------------------------------------------------------------
# Editable Score Formula & Breakdown
# ---------------------------------------------------------------------------
async def get_score_weights(db: AsyncSession) -> Dict[str, int]:
    res = await db.execute(select(AppSetting).where(AppSetting.key == "hot_lead_score_weights"))
    row = res.scalar_one_or_none()
    if not row:
        return dict(DEFAULT_SCORE_WEIGHTS)
    try:
        parsed = json.loads(row.value)
        merged = dict(DEFAULT_SCORE_WEIGHTS)
        for k, v in parsed.items():
            if k in merged:
                merged[k] = max(0, min(100, int(v)))
        return merged
    except Exception:
        return dict(DEFAULT_SCORE_WEIGHTS)


async def save_score_weights(db: AsyncSession, weights: Dict[str, int]) -> Dict[str, int]:
    merged = dict(DEFAULT_SCORE_WEIGHTS)
    for k, v in weights.items():
        if k in merged:
            merged[k] = max(0, min(100, int(v)))
    res = await db.execute(select(AppSetting).where(AppSetting.key == "hot_lead_score_weights"))
    row = res.scalar_one_or_none()
    if row:
        row.value = json.dumps(merged)
    else:
        db.add(AppSetting(
            key="hot_lead_score_weights",
            value=json.dumps(merged),
            description="Editable Hot Lead scoring weights (0-100)",
        ))
    await db.commit()
    return merged


def compute_hot_lead_score(
    lead_data: Dict[str, Any],
    weights: Optional[Dict[str, int]] = None,
) -> Tuple[int, str, List[Dict[str, Any]]]:
    """
    Transparent 0-100 Hot Lead Score with "Why this score" breakdown.
    Labels: Hot (75+), Warm (50-74), Cold (<50).
    """
    w = weights or DEFAULT_SCORE_WEIGHTS
    breakdown: List[Dict[str, Any]] = []
    total = 0

    source_type = (lead_data.get("source_type") or "").lower()
    source_name = (lead_data.get("source_name") or "").lower()
    signals = set(lead_data.get("signals") or [])
    health = lead_data.get("website_health") or {}
    website = (lead_data.get("website") or "").strip()
    phone_clean = lead_data.get("phone_clean") or extract_phone_digits(lead_data.get("phone"))
    rating = lead_data.get("rating")
    budget = (lead_data.get("budget_range") or "").strip()

    if source_type == "inbound" or lead_data.get("contacted_directly"):
        pts = w["contacted_directly"]
        total += pts
        breakdown.append({"factor": "contacted_directly", "points": pts, "reason": "Contacted us directly via inbound channel"})

    if "quote" in source_name or lead_data.get("requested_quote") or bool(lead_data.get("timeline")):
        pts = w["requested_quote"]
        total += pts
        breakdown.append({"factor": "requested_quote", "points": pts, "reason": "Requested a website quote / timeline"})

    has_site = bool(website and website.startswith("http"))
    if not has_site or "no_website" in signals or "advertising_without_website" in signals:
        pts = w["no_website"]
        total += pts
        breakdown.append({"factor": "no_website", "points": pts, "reason": "No business website listed"})

    broken_signals = {"broken_website", "no_https", "slow_site", "not_mobile_friendly"}
    health_issues = health.get("issues") or []
    if bool(signals & broken_signals) or (has_site and len(health_issues) > 0):
        pts = w["broken_or_outdated_website"]
        total += pts
        reason_detail = ", ".join(health_issues[:3]) if health_issues else ", ".join(sorted(signals & broken_signals))
        breakdown.append({"factor": "broken_or_outdated_website", "points": pts, "reason": f"Website issues: {reason_detail}"})

    if phone_clean and len(str(phone_clean)) == 10:
        pts = w["mobile_available"]
        total += pts
        breakdown.append({"factor": "mobile_available", "points": pts, "reason": "Valid 10-digit mobile number available"})

    try:
        rating_val = float(rating) if rating is not None else 0.0
    except (ValueError, TypeError):
        rating_val = 0.0
    if rating_val >= 3.5 or source_type in ("inbound", "public_request"):
        pts = w["good_rating_or_active"]
        total += pts
        breakdown.append({"factor": "good_rating_or_active", "points": pts, "reason": "Active business / strong customer rating"})

    if "recently_listed" in signals or source_type == "public_request":
        pts = w["recently_listed"]
        total += pts
        breakdown.append({"factor": "recently_listed", "points": pts, "reason": "Fresh listing or recent public request"})

    if budget:
        pts = w["budget_stated"]
        total += pts
        breakdown.append({"factor": "budget_stated", "points": pts, "reason": f"Budget stated ({budget})"})

    score = min(100, max(0, total))
    if score >= 75:
        temp = "Hot"
    elif score >= 50:
        temp = "Warm"
    else:
        temp = "Cold"
    return score, temp, breakdown


# ---------------------------------------------------------------------------
# Safe, Rate-Limited Website Health Checker
# ---------------------------------------------------------------------------
def _is_public_hostname(hostname: str) -> Tuple[bool, Optional[str]]:
    """Blocks private/loopback/link-local IPs to prevent SSRF."""
    if not hostname or hostname.lower() in ("localhost", "127.0.0.1", "::1"):
        return False, "Localhost URLs are not allowed."
    try:
        infos = socket.getaddrinfo(hostname, None)
        for info in infos:
            ip_str = info[4][0]
            ip_obj = ipaddress.ip_address(ip_str)
            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_reserved:
                return False, "Private or internal IP addresses are not allowed."
        return True, None
    except socket.gaierror:
        return False, "DNS resolution failed"


async def check_website_health(url: str) -> Dict[str, Any]:
    """
    Rate-limited website health checker:
    Checks DNS, HTTP status, HTTPS, mobile viewport meta tag, and response time.
    """
    global _last_health_check_ts
    checked_at = datetime.utcnow().isoformat() + "Z"
    clean_url = (url or "").strip()
    if not clean_url:
        return {
            "url": "",
            "dns_ok": False,
            "http_status": None,
            "https_ok": False,
            "mobile_viewport": False,
            "response_ms": None,
            "issues": ["No website listed"],
            "checked_at": checked_at,
        }
    if not clean_url.startswith(("http://", "https://")):
        clean_url = "https://" + clean_url

    parsed = urlparse(clean_url)
    hostname = parsed.hostname or ""

    # Rate limit: at least 0.5s between live outbound checks
    elapsed = time.monotonic() - _last_health_check_ts
    if elapsed < 0.5:
        await asyncio.sleep(0.5 - elapsed)
    _last_health_check_ts = time.monotonic()

    loop = asyncio.get_running_loop()
    dns_ok, dns_err = await loop.run_in_executor(None, _is_public_hostname, hostname)
    if not dns_ok:
        return {
            "url": clean_url,
            "dns_ok": False,
            "http_status": None,
            "https_ok": False,
            "mobile_viewport": False,
            "response_ms": None,
            "issues": [dns_err or "DNS lookup failed"],
            "checked_at": checked_at,
        }

    issues: List[str] = []
    https_ok = parsed.scheme == "https"
    if not https_ok:
        issues.append("No HTTPS")

    start = time.monotonic()
    http_status: Optional[int] = None
    mobile_viewport = False
    try:
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            resp = await client.get(clean_url, headers={"User-Agent": "LeadHarvestHealthCheck/2.0"})
            http_status = resp.status_code
            final_scheme = urlparse(str(resp.url)).scheme
            https_ok = final_scheme == "https"
            if not https_ok and "No HTTPS" not in issues:
                issues.append("No HTTPS")
            if http_status >= 400:
                issues.append(f"HTTP {http_status} error")
            html_lower = (resp.text or "")[:30000].lower()
            mobile_viewport = bool(re.search(r'<meta[^>]+name=["\']viewport["\']', html_lower))
            if not mobile_viewport:
                issues.append("Not mobile-friendly (missing viewport tag)")
    except Exception as exc:
        issues.append(f"Unreachable ({type(exc).__name__})")

    response_ms = int((time.monotonic() - start) * 1000)
    if response_ms > 2500:
        issues.append(f"Slow response ({response_ms} ms)")

    return {
        "url": clean_url,
        "dns_ok": True,
        "http_status": http_status,
        "https_ok": https_ok,
        "mobile_viewport": mobile_viewport,
        "response_ms": response_ms,
        "issues": issues,
        "checked_at": checked_at,
    }


# ---------------------------------------------------------------------------
# Compliance: Do Not Contact Check
# ---------------------------------------------------------------------------
async def is_do_not_contact(
    db: AsyncSession,
    phone_clean: Optional[str] = None,
    email: Optional[str] = None,
) -> Tuple[bool, Optional[str]]:
    if phone_clean:
        res = await db.execute(
            select(DoNotContactEntry).where(DoNotContactEntry.phone_clean == phone_clean)
        )
        entry = res.scalars().first()
        if entry:
            return True, entry.reason
    if email:
        res = await db.execute(
            select(DoNotContactEntry).where(DoNotContactEntry.email == email.strip().lower())
        )
        entry = res.scalars().first()
        if entry:
            return True, entry.reason
    return False, None


# ---------------------------------------------------------------------------
# Pluggable Intent Source Interface & CSV Importer
# ---------------------------------------------------------------------------
class BaseIntentSource(ABC):
    source_kind: str = "manual"
    terms_note: str = "User-supplied or official feed within platform terms."

    @abstractmethod
    async def fetch_leads(self, endpoint_or_query: str) -> List[Dict[str, Any]]:
        ...


class RssIntentSource(BaseIntentSource):
    source_kind = "rss"
    terms_note = "Public RSS/Atom feed; respects feed publishing terms and no-auth public access."

    async def fetch_leads(self, endpoint_or_query: str) -> List[Dict[str, Any]]:
        parsed = urlparse(endpoint_or_query)
        if (parsed.hostname or "").lower() in DISALLOWED_SCRAPE_DOMAINS:
            raise ValueError(f"Source domain '{parsed.hostname}' is disallowed by compliance policy.")
        dns_ok, err = _is_public_hostname(parsed.hostname or "")
        if not dns_ok:
            raise ValueError(err or "Invalid RSS host")

        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(endpoint_or_query, headers={"User-Agent": "LeadHarvestRSS/2.0"})
            resp.raise_for_status()
            root = ET.fromstring(resp.text)

        items: List[Dict[str, Any]] = []
        for item in root.findall(".//item")[:25]:
            title = (item.findtext("title") or "Public Request").strip()
            link = (item.findtext("link") or endpoint_or_query).strip()
            desc = re.sub(r"<[^>]+>", " ", (item.findtext("description") or "")).strip()
            items.append({
                "business_name": title[:180],
                "source_url": link,
                "notes_summary": desc[:500],
                "signals": ["recently_listed"],
            })
        return items


class OfficialApiIntentSource(BaseIntentSource):
    source_kind = "official_api"
    terms_note = "Official partner/webhook API payload ingested with explicit authorization."

    async def fetch_leads(self, endpoint_or_query: str) -> List[Dict[str, Any]]:
        # Official JSON endpoint returning {"items": [...]}
        parsed = urlparse(endpoint_or_query)
        if (parsed.hostname or "").lower() in DISALLOWED_SCRAPE_DOMAINS:
            raise ValueError(f"Domain '{parsed.hostname}' is disallowed.")
        dns_ok, err = _is_public_hostname(parsed.hostname or "")
        if not dns_ok:
            raise ValueError(err or "Invalid API host")
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(endpoint_or_query)
            resp.raise_for_status()
            data = resp.json()
        return data.get("items", []) if isinstance(data, dict) else []


class EmailAlertIntentSource(BaseIntentSource):
    source_kind = "email_alert"
    terms_note = "Owner-connected inbox saved-search alert parser (forwarded alerts only)."

    async def fetch_leads(self, endpoint_or_query: str) -> List[Dict[str, Any]]:
        # Parses JSON or newline-delimited alert summaries supplied by the owner
        try:
            data = json.loads(endpoint_or_query)
            if isinstance(data, list):
                return data
        except Exception:
            pass
        return []


INTENT_SOURCE_REGISTRY: Dict[str, BaseIntentSource] = {
    "rss": RssIntentSource(),
    "official_api": OfficialApiIntentSource(),
    "email_alert": EmailAlertIntentSource(),
}


def parse_public_requests_csv(csv_bytes: bytes) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Validates and parses a CSV of publicly posted website requests.
    Required column: business_name (or name).
    Returns (valid_rows, errors).
    """
    text = csv_bytes.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        return [], ["CSV file has no header row."]

    normalized_headers = {h.strip().lower(): h for h in reader.fieldnames if h}
    if "business_name" not in normalized_headers and "name" not in normalized_headers:
        return [], ["CSV must contain a 'business_name' or 'name' column."]

    rows: List[Dict[str, Any]] = []
    errors: List[str] = []
    for idx, raw in enumerate(reader, start=2):
        clean = {(k or "").strip().lower(): (v or "").strip() for k, v in raw.items()}
        bname = clean.get("business_name") or clean.get("name")
        if not bname:
            errors.append(f"Row {idx}: missing business_name/name")
            continue
        phone = clean.get("phone") or clean.get("mobile") or ""
        email = clean.get("email") or ""
        if not phone and not email and not clean.get("source_url"):
            errors.append(f"Row {idx}: needs at least one contact method (phone, email, or source_url)")
            continue
        rows.append({
            "name": clean.get("contact_name") or clean.get("name") or bname,
            "business_name": bname,
            "phone": phone,
            "phone_clean": extract_phone_digits(phone),
            "email": email.lower() if email else None,
            "business_type": clean.get("business_type") or clean.get("category") or "",
            "city": clean.get("city") or "",
            "state": clean.get("state") or "",
            "website": clean.get("website") or "",
            "budget_range": clean.get("budget_range") or clean.get("budget") or "",
            "timeline": clean.get("timeline") or "",
            "source_url": clean.get("source_url") or "",
            "notes_summary": clean.get("notes") or clean.get("requirement") or "",
            "terms_note": clean.get("terms_note") or "CSV import of publicly posted request",
        })
    return rows, errors


# ---------------------------------------------------------------------------
# Signal Ingestion from LeadHarvest Collector Jobs
# ---------------------------------------------------------------------------
async def ingest_signal_leads_from_job(
    db: AsyncSession,
    leads: List[Dict[str, Any]],
    filters: Optional[Dict[str, Any]],
) -> int:
    """
    Sends matching buying-signal leads from collector runs into Hot Leads automatically.
    Signals: no_website, broken_website, no_https, slow_site, not_mobile_friendly,
             recently_listed, advertising_without_website.
    """
    if not leads:
        return 0
    weights = await get_score_weights(db)
    added = 0

    for item in leads[:25]:  # cap per run to keep Hot Leads curated
        signals: List[str] = []
        website = (item.get("website") or "").strip()
        has_site = bool(website and website.startswith("http"))
        if not has_site:
            signals.append("no_website")
        elif website.startswith("http://"):
            signals.append("no_https")

        if filters:
            for sig in ("broken_website", "no_https", "slow_site", "not_mobile_friendly", "recently_listed", "advertising_without_website"):
                if filters.get(sig):
                    signals.append(sig)
        if item.get("is_verified_listing") and not has_site:
            signals.append("advertising_without_website")

        if not signals:
            continue

        phone_clean = item.get("phone_clean") or extract_phone_digits(item.get("phone"))
        bname = (item.get("business_name") or "").strip()
        city = (item.get("city") or "").strip()
        if not bname:
            continue

        # Check DNC
        dnc, dnc_reason = await is_do_not_contact(db, phone_clean=phone_clean, email=item.get("email"))

        # Dedupe against existing HotLeads
        existing_q = select(HotLead).where(HotLead.business_name == bname, HotLead.city == city)
        if phone_clean:
            existing_q = select(HotLead).where(
                (HotLead.phone_clean == phone_clean) | ((HotLead.business_name == bname) & (HotLead.city == city))
            )
        if (await db.execute(existing_q)).scalars().first():
            continue

        rating_val = None
        try:
            if item.get("rating"):
                rating_val = float(item.get("rating"))
        except (ValueError, TypeError):
            rating_val = None

        lead_payload = {
            "source_type": "signal",
            "source_name": "leadharvest_signal",
            "website": website,
            "phone_clean": phone_clean,
            "rating": rating_val,
            "signals": signals,
        }
        score, temp, breakdown = compute_hot_lead_score(lead_payload, weights)

        hl = HotLead(
            id=f"hl_{uuid.uuid4().hex[:12]}",
            source_type="signal",
            source_name="leadharvest_signal",
            source_url=item.get("listing_url") or "",
            terms_note="Internal buying-signal derived from LeadHarvest Smart Filters on public directory data",
            name=bname,
            business_name=bname,
            phone=item.get("phone"),
            phone_clean=phone_clean,
            email=item.get("email"),
            business_type=item.get("category"),
            city=city,
            state=item.get("state"),
            website=website,
            score=score,
            temperature=temp,
            score_breakdown_json=json.dumps(breakdown),
            signals_json=json.dumps(sorted(set(signals))),
            rating=rating_val,
            stage="New",
            consent_given=False,
            consent_record="Public B2B directory signal (no direct inbound opt-in; verify DND before outreach)",
            do_not_contact=dnc,
            dnc_reason=dnc_reason,
        )
        db.add(hl)
        added += 1

    if added:
        await db.commit()
    return added


# ---------------------------------------------------------------------------
# Message Templates (English, Hindi, Odia) — Never Auto-Sent
# ---------------------------------------------------------------------------
def render_message_templates(lead: HotLead) -> Dict[str, Any]:
    """
    Generates WhatsApp, Email, and Call script templates in English, Hindi, and Odia.
    Returns disabled links if lead.do_not_contact is True.
    """
    bname = lead.business_name or lead.name or "your business"
    city = lead.city or "your city"
    issues: List[str] = []
    if not lead.website:
        issues.append("no official website found online")
    elif lead.website_health_json:
        try:
            health = json.loads(lead.website_health_json)
            issues.extend(health.get("issues") or [])
        except Exception:
            pass
    issue_found = issues[0] if issues else "missing online website presence"

    templates = {
        "english": {
            "whatsapp": (
                f"Hi {bname} team, I noticed your business in {city} currently has {issue_found}. "
                f"We build fast, mobile-ready websites for local businesses in {city} starting at Rs 7,999 "
                f"with Google Maps & WhatsApp integration. Would you like a free 2-minute sample mockup?"
            ),
            "email_subject": f"Quick website idea for {bname} ({city})",
            "email_body": (
                f"Hello {bname} team,\n\n"
                f"I came across {bname} in {city} and noticed: {issue_found}.\n"
                f"We help local businesses in {city} launch clean, mobile-friendly websites in 5-7 days "
                f"so customers searching on Google can call or WhatsApp you directly.\n\n"
                f"Reply to this email if you'd like a free homepage preview.\n\nBest regards,\nAmar\nLeadHarvest Web Studio"
            ),
            "call_script": (
                f"\"Namaste, am I speaking with the owner of {bname} in {city}? "
                f"I'm Amar, a local web designer. I noticed you have great visibility in {city} but {issue_found}. "
                f"We're helping {lead.business_type or 'local businesses'} get direct Google & WhatsApp leads. "
                f"Can I send you a 1-page sample design on WhatsApp with zero obligation?\""
            ),
        },
        "hindi": {
            "whatsapp": (
                f"Namaste {bname} ji, maine {city} me aapka business dekha. Abhi aapka {issue_found} hai. "
                f"Hum {city} ke businesses ke liye mobile-friendly website (Google Maps + WhatsApp button ke saath) "
                f"banate hain. Kya main aapko ek free sample design bheju?"
            ),
            "email_subject": f"{bname} ({city}) ke liye website proposal",
            "email_body": (
                f"Namaste {bname} team,\n\n"
                f"{city} me aapke business ke liye hum ek fast, mobile-ready website bana sakte hain "
                f"jisse naye customers seedha Google se aapko call ya WhatsApp kar sakein.\n\n"
                f"Free demo dekhne ke liye reply karein.\nDhanyawad,\nAmar"
            ),
            "call_script": (
                f"\"Namaste ji, main Amar bol raha hoon. Maine {city} me {bname} dekha, "
                f"abhi aapki website nahi hai / update ki zaroorat hai. Kya main WhatsApp par aapko ek free sample bheju?\""
            ),
        },
        "odia": {
            "whatsapp": (
                f"Namaskar {bname}, mu {city} re aapanka business dekhili. Bartaman aapanka {issue_found} achhi. "
                f"Aame {city} ra local business pain mobile-friendly website (Google Maps o WhatsApp sahita) tiari karuchhu. "
                f"Aapanka pain eka free sample design pathaibi ki?"
            ),
            "email_subject": f"{bname} ({city}) pain website prastab",
            "email_body": (
                f"Namaskar {bname} team,\n\n"
                f"{city} re aapanka business pain eka sundar o mobile-friendly website tiari kari paribu "
                f"jaha dwara nua grahak Google ru sidha call o WhatsApp kari paribe.\n\n"
                f"Free sample pain reply karantu.\nDhanyabad,\nAmar"
            ),
            "call_script": (
                f"\"Namaskar, mu Amar kahuchhi. {city} re aapanka {bname} dekhili. "
                f"Website tiari pain eka free sample WhatsApp re pathaibi ki?\""
            ),
        },
    }

    blocked = bool(lead.do_not_contact)
    phone_digits = lead.phone_clean or extract_phone_digits(lead.phone)
    links: Dict[str, Any] = {}
    for lang, tpl in templates.items():
        wa_url = (
            f"https://wa.me/91{phone_digits}?text={quote(tpl['whatsapp'])}"
            if (not blocked and phone_digits)
            else None
        )
        mailto_url = (
            f"mailto:{lead.email}?subject={quote(tpl['email_subject'])}&body={quote(tpl['email_body'])}"
            if (not blocked and lead.email)
            else None
        )
        links[lang] = {
            **tpl,
            "wa_url": wa_url,
            "mailto_url": mailto_url,
        }

    return {
        "blocked_by_dnc": blocked,
        "dnc_reason": lead.dnc_reason,
        "compliance_reminder": "Respect TRAI DND rules, WhatsApp Business opt-in policy, and DPDP Act 2023. Never auto-send bulk unsolicited messages.",
        "templates": links,
    }


# ---------------------------------------------------------------------------
# One-Page Proposal PDF Generator
# ---------------------------------------------------------------------------
def generate_proposal_pdf(
    lead: HotLead,
    package_name: str = "Growth Business Website",
    price_range: str = "Rs 9,999 - Rs 14,999",
    timeline: str = "7 Business Days",
) -> Path:
    """Generates a clean one-page PDF proposal for a Hot Lead."""
    settings.PROPOSALS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"proposal_{lead.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.pdf"
    out_path = settings.PROPOSALS_DIR / filename

    problems: List[str] = []
    if not lead.website:
        problems.append("No dedicated business website found for Google searchers.")
    if lead.website_health_json:
        try:
            health = json.loads(lead.website_health_json)
            for iss in health.get("issues") or []:
                problems.append(iss)
        except Exception:
            pass
    if not problems:
        problems = [
            "Missing mobile-first landing page optimized for local Google searches.",
            "No instant WhatsApp click-to-chat conversion funnel for visitors.",
        ]

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Header
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 10, "Website Growth Proposal", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(90, 90, 90)
    pdf.cell(0, 6, f"Prepared for: {lead.business_name} ({lead.city or 'India'})  |  Date: {datetime.utcnow().strftime('%d %b %Y')}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Problems Found
    pdf.set_text_color(20, 20, 20)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "1. Opportunities & Gaps Identified", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    for prob in problems[:5]:
        safe_prob = prob.encode("latin-1", "replace").decode("latin-1")
        pdf.cell(0, 6, f"- {safe_prob}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Package Options
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "2. Recommended Package Options", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    packages = [
        ("Starter One-Page", "Rs 7,999", "5 Days", "Mobile-ready landing page, WhatsApp CTA, Google Map embed, SSL"),
        (package_name, price_range, timeline, "5-page SEO website, Lead Quote form, Speed optimization, Analytics"),
        ("Pro Growth + SEO", "Rs 24,999", "12 Days", "Custom design, Local SEO pages, Blog setup, Google Business sync"),
    ]
    for pkg, price, tl, desc in packages:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, f"{pkg}  |  {price}  |  Delivery: {tl}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 5, f"   Includes: {desc}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # Next Steps
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "3. Next Steps", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "Reply on WhatsApp or email to approve the layout. 50% advance to start, 50% on launch.", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, "Prepared by Amar | LeadHarvest Web Studio | support@leadharvest.in", new_x="LMARGIN", new_y="NEXT")

    pdf.output(str(out_path))
    return out_path

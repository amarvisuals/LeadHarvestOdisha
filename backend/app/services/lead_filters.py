import logging
from typing import List, Dict, Any, Optional, Tuple
import httpx

logger = logging.getLogger("leadharvest.filters")

PITCH_PRESETS = [
    {
        "id": "website_design_pitch",
        "name": "Website Design Pitch",
        "description": "Businesses with NO website, valid mobile number, and rating >= 3.5 — ideal for selling custom websites.",
        "badge": "Flagship",
        "filters": {
            "no_website": True,
            "mobile_only": True,
            "min_rating": 3.5,
            "min_opportunity_score": 60,
        },
    },
    {
        "id": "seo_ads_pitch",
        "name": "SEO / Ads Pitch",
        "description": "Businesses that already have a website but low review count (< 30) — great for SEO & Google Ads.",
        "badge": "Marketing",
        "filters": {
            "has_website": True,
            "max_reviews": 30,
        },
    },
    {
        "id": "reputation_pitch",
        "name": "Reputation Pitch",
        "description": "Businesses with rating < 3.5 and 20+ reviews — ideal for reputation management & redesigns.",
        "badge": "Turnaround",
        "filters": {
            "max_rating": 3.5,
            "min_reviews": 20,
        },
    },
]


def compute_opportunity_score(lead: Dict[str, Any]) -> Tuple[int, str]:
    """
    Computes a transparent 0-100 Opportunity Score for B2B outreach:
      - No website listed:      +40
      - Mobile number available: +20
      - Low reviews (< 50):     +15
      - Good rating (3.5-4.7):  +15
      - Complete address + pin: +10
    Returns (score, lead_tag).
    """
    score = 0
    has_site = bool(lead.get("website") and str(lead.get("website")).strip().startswith("http"))
    mobile_avail = bool(lead.get("phone_clean") and len(str(lead.get("phone_clean"))) == 10)

    if not has_site:
        score += 40
    if mobile_avail:
        score += 20

    try:
        reviews = int(float(lead.get("review_count") or 0))
    except (ValueError, TypeError):
        reviews = 0
    if reviews < 50:
        score += 15

    try:
        rating = float(lead.get("rating") or 0.0)
    except (ValueError, TypeError):
        rating = 0.0
    if 3.5 <= rating <= 4.7:
        score += 15

    if lead.get("address") and lead.get("pincode"):
        score += 10

    score = min(100, max(0, score))

    # Determine Lead Tag
    if not has_site and mobile_avail and rating >= 3.5:
        tag = "Hot Website Pitch"
    elif has_site and reviews < 30:
        tag = "SEO / Ads Pitch"
    elif rating > 0 and rating < 3.5 and reviews >= 20:
        tag = "Reputation Pitch"
    elif score >= 70:
        tag = "High Opportunity"
    else:
        tag = "Standard Lead"

    return score, tag


def enrich_lead_metadata(lead: Dict[str, Any]) -> Dict[str, Any]:
    """Populates derived SaaS fields (has_website, mobile_available, whatsapp_link, score, tag)."""
    website = lead.get("website")
    has_website = bool(website and str(website).strip().startswith("http"))
    phone_clean = lead.get("phone_clean")
    mobile_available = bool(phone_clean and len(str(phone_clean)) == 10 and str(phone_clean)[0] in "6789")
    social_url = lead.get("social_url")
    has_social_only = bool((not has_website) and social_url)

    score, tag = compute_opportunity_score(lead)

    lead["has_website"] = has_website
    lead["mobile_available"] = mobile_available
    lead["has_social_only"] = has_social_only
    lead["opportunity_score"] = score
    lead["lead_tag"] = tag
    lead["whatsapp_link"] = f"https://wa.me/91{phone_clean}" if mobile_available else ""
    return lead


def matches_smart_filters(lead: Dict[str, Any], filters: Optional[Dict[str, Any]]) -> Tuple[bool, Optional[str]]:
    """
    Evaluates whether an enriched lead passes the user's Smart Filters.
    Returns (passed: bool, reason_if_excluded: Optional[str]).
    """
    if not filters:
        return True, None

    if filters.get("no_website") and lead.get("has_website"):
        return False, "Has website"
    if filters.get("has_website") and not lead.get("has_website"):
        return False, "No website"
    if filters.get("mobile_only") and not lead.get("mobile_available"):
        return False, "No mobile number"
    if filters.get("has_email") and not lead.get("email"):
        return False, "No email"
    if filters.get("verified_only") and not lead.get("is_verified_listing"):
        return False, "Not verified"
    if filters.get("has_social_only") and not lead.get("has_social_only"):
        return False, "Not social-only"
    if filters.get("exclude_chains") and lead.get("is_chain"):
        return False, "Chain/franchise excluded"

    try:
        rating = float(lead.get("rating") or 0.0)
    except (ValueError, TypeError):
        rating = 0.0

    if filters.get("min_rating") is not None and rating < float(filters["min_rating"]):
        return False, "Rating below minimum"
    if filters.get("max_rating") is not None and rating > float(filters["max_rating"]):
        return False, "Rating above maximum"

    try:
        reviews = int(float(lead.get("review_count") or 0))
    except (ValueError, TypeError):
        reviews = 0

    if filters.get("min_reviews") is not None and reviews < int(filters["min_reviews"]):
        return False, "Reviews below minimum"
    if filters.get("max_reviews") is not None and reviews > int(filters["max_reviews"]):
        return False, "Reviews above maximum"

    min_score = filters.get("min_opportunity_score")
    if min_score is not None and int(lead.get("opportunity_score", 0)) < int(min_score):
        return False, "Opportunity score below minimum"

    return True, None


def detect_chains_across_leads(leads: List[Dict[str, Any]], min_cities: int = 4) -> List[Dict[str, Any]]:
    """Heuristic: marks businesses whose normalized name appears across 4+ distinct cities as chains."""
    name_cities: Dict[str, set] = {}
    for l in leads:
        nm = str(l.get("business_name", "")).strip().lower()
        ct = str(l.get("city", "")).strip().lower()
        if nm and ct:
            name_cities.setdefault(nm, set()).add(ct)

    for l in leads:
        nm = str(l.get("business_name", "")).strip().lower()
        if len(name_cities.get(nm, set())) >= min_cities:
            l["is_chain"] = True
    return leads


async def verify_website_enrichment_hook(website_url: Optional[str], enabled: bool = False) -> bool:
    """
    Optional Enrichment Adapter hook: performs a lightweight HEAD check
    to confirm whether a listed website actually resolves. Disabled by default.
    """
    if not enabled or not website_url:
        return bool(website_url)
    try:
        async with httpx.AsyncClient(timeout=3.0, follow_redirects=True) as client:
            res = await client.head(website_url)
            return res.status_code < 500
    except Exception:
        return False

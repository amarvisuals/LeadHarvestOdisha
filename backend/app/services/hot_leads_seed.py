"""Seeds 30 realistic demo Hot Leads across Inbound, Public Requests, and Signal Leads."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.entities import (
    DoNotContactEntry,
    HotLead,
    HotLeadActivity,
    IntentSourceConfig,
)
from app.services.hot_leads import compute_hot_lead_score, get_score_weights


async def seed_30_hot_leads(db: AsyncSession) -> int:
    existing = (await db.execute(select(HotLead))).scalars().first()
    if existing:
        return 0

    weights = await get_score_weights(db)
    now = datetime.utcnow()

    # Seed 2 compliant Intent Sources
    db.add(IntentSourceConfig(
        id="src_demo_rss",
        name="India Freelance Web RFPs (RSS)",
        source_kind="rss",
        endpoint_or_query="https://example.org/web-rfp-feed.xml",
        terms_note="Public RSS feed of posted web design project requests.",
        is_active=True,
        leads_imported=10,
        last_synced_at=now - timedelta(hours=4),
    ))
    db.add(IntentSourceConfig(
        id="src_demo_email_alert",
        name="Forwarded Saved-Search Email Alerts",
        source_kind="email_alert",
        endpoint_or_query="owner-alerts@leadharvest.in",
        terms_note="Owner-forwarded saved-search email alerts from authorized job boards.",
        is_active=True,
        leads_imported=5,
        last_synced_at=now - timedelta(days=1),
    ))

    # Seed 1 DNC entry
    db.add(DoNotContactEntry(
        id="dnc_demo_01",
        phone_clean="9861099999",
        email="optout@kalingaclinic.in",
        reason="Requested opt-out / DND registered",
        source="opt_out",
    ))

    # 30 Demo Leads across Inbound (10), Public Requests (10), Signal Leads (10)
    demo_specs = [
        # 10 Inbound
        ("inbound", "website_quote_form", "Dr. Ananya Mishra", "SmileCare Dental Clinic", "9861011101", "smilecare@odisha.in", "Dental Clinic", "Bhubaneswar", "Odisha", "", "Rs 10,000 - Rs 20,000", "Within 2 weeks", "New", 15000, -1, 4.7, []),
        ("inbound", "google_ads_webhook", "Rajesh Agrawal", "Agrawal Ortho & Spine", "9437022202", "rajesh@agrawalortho.in", "Healthcare Clinic", "Cuttack", "Odisha", "http://agrawalortho-old.in", "Rs 15,000 - Rs 30,000", "Immediate", "Contacted", 22000, -3, 4.5, ["broken_website", "no_https"]),
        ("inbound", "whatsapp_cta", "Sneha Patnaik", "GlowAura Salon & Spa", "7008033303", "sneha@glowaura.in", "Beauty Salon", "Puri", "Odisha", "", "Rs 8,000 - Rs 15,000", "This month", "Meeting booked", 12000, 0, 4.6, []),
        ("inbound", "website_quote_form", "Vikram Malhotra", "Apex Modular Kitchens", "9811044404", "vikram@apexkitchens.in", "Interior Designer", "Pune", "Maharashtra", "http://apexkitchens.in", "Rs 25,000+", "Within 1 week", "Proposal sent", 28000, 0, 4.4, ["no_https", "not_mobile_friendly"]),
        ("inbound", "google_ads_webhook", "Neha Sharma", "BrightFuture Coaching", "9820055505", "neha@brightfuture.in", "Coaching Institute", "Indore", "Madhya Pradesh", "", "Rs 12,000 - Rs 20,000", "Within 2 weeks", "Negotiation", 18000, -1, 4.8, []),
        ("inbound", "website_quote_form", "Suresh Panda", "Kalinga Builders & Infra", "9438066606", "suresh@kalingabuild.in", "Real Estate", "Bhubaneswar", "Odisha", "", "Rs 20,000 - Rs 35,000", "This month", "Won", 30000, None, 4.6, []),
        ("inbound", "whatsapp_cta", "Pooja Nair", "SpiceRoute Kitchen", "9845077707", "pooja@spiceroute.in", "Restaurant", "Kochi", "Kerala", "", "Rs 10,000 - Rs 15,000", "Immediate", "Won", 14000, None, 4.5, []),
        ("inbound", "website_quote_form", "Amit Verma", "Verma Tax & CA Associates", "9818088808", "amit@vermatax.in", "Chartered Accountant", "Noida", "Uttar Pradesh", "", "Rs 8,000 - Rs 12,000", "Flexible", "Lost", 10000, None, 4.2, []),
        ("inbound", "google_ads_webhook", "Deepak Sahoo", "Odisha Solar Solutions", "8249099909", "deepak@odishasolar.in", "Solar Energy", "Rourkela", "Odisha", "", "Rs 15,000 - Rs 25,000", "Within 2 weeks", "Contacted", 20000, 0, 4.7, []),
        ("inbound", "website_quote_form", "Kavita Joshi", "Joshi Bridal Boutique", "9765010101", "kavita@joshiboutique.in", "Boutique", "Jaipur", "Rajasthan", "", "Rs 12,000 - Rs 18,000", "Immediate", "New", 15000, 0, 4.6, []),

        # 10 Public Requests
        ("public_request", "csv_import", "Manish Tiwari", "Tiwari Dental Care", "9937012121", "manish@tiwaridental.in", "Dental Clinic", "Sambalpur", "Odisha", "", "Rs 10,000", "Within 10 days", "New", 10000, -2, 4.3, ["recently_listed"]),
        ("public_request", "rss_feed", "Ritu Agarwal", "FitZone Unisex Gym", "9830023232", "ritu@fitzonegym.in", "Gym & Fitness", "Kolkata", "West Bengal", "", "Rs 12,000 - Rs 18,000", "This month", "Contacted", 15000, 0, 4.4, ["recently_listed"]),
        ("public_request", "email_alert", "Prakash Reddy", "Deccan Diagnostics", "9848034343", "prakash@deccandiag.in", "Diagnostic Center", "Hyderabad", "Telangana", "http://deccandiag.in", "Rs 20,000", "Immediate", "Meeting booked", 20000, 0, 4.5, ["no_https", "slow_site"]),
        ("public_request", "csv_import", "Subham Behera", "Behera Packers & Movers", "7978045454", "subham@beheramovers.in", "Packers & Movers", "Cuttack", "Odisha", "", "Rs 9,000", "Within 2 weeks", "Proposal sent", 9000, -1, 4.1, ["recently_listed"]),
        ("public_request", "rss_feed", "Meera Kulkarni", "Kulkarni Law Chambers", "9822056565", "meera@kulkarnilaw.in", "Law Firm", "Nagpur", "Maharashtra", "", "Rs 15,000", "This month", "Won", 15000, None, 4.6, ["recently_listed"]),
        ("public_request", "csv_import", "Harish Patel", "Patel Jewellers", "9825067676", "harish@pateljewels.in", "Jewellery Store", "Surat", "Gujarat", "", "Rs 25,000", "Next month", "Lost", 25000, None, 4.4, ["recently_listed"]),
        ("public_request", "email_alert", "Anjali Menon", "Veda Ayurveda Wellness", "9895078787", "anjali@vedaayur.in", "Wellness Spa", "Thrissur", "Kerala", "", "Rs 14,000", "Immediate", "New", 14000, 0, 4.7, ["recently_listed"]),
        ("public_request", "csv_import", "Gaurav Bansal", "Bansal Hardware & Paints", "9814089898", "gaurav@bansalhw.in", "Hardware Store", "Ludhiana", "Punjab", "", "", "Flexible", "New", 8000, 2, 3.9, ["recently_listed"]),
        ("public_request", "rss_feed", "Swati Deshmukh", "Petals Wedding Planners", "9823090909", "swati@petalswed.in", "Wedding Planner", "Nashik", "Maharashtra", "", "Rs 18,000", "Within 2 weeks", "Contacted", 18000, 0, 4.5, ["recently_listed"]),
        ("public_request", "csv_import", "Rakesh Mohapatra", "Kalinga OptOut Clinic", "9861099999", "optout@kalingaclinic.in", "Clinic", "Bhubaneswar", "Odisha", "", "", "", "Lost", 0, None, 4.0, ["recently_listed"]),

        # 10 Signal Leads (from Smart Filters)
        ("signal", "leadharvest_signal", "Odisha Heart & Care", "Odisha Heart & Care Clinic", "9437111222", None, "Healthcare Clinic", "Bhubaneswar", "Odisha", "", "", "", "New", 12000, 0, 4.6, ["no_website", "advertising_without_website"]),
        ("signal", "leadharvest_signal", "Cuttack Royal Biryani", "Cuttack Royal Biryani", "9861222333", None, "Restaurant", "Cuttack", "Odisha", "", "", "", "New", 9000, -1, 4.4, ["no_website", "recently_listed"]),
        ("signal", "leadharvest_signal", "Surya Dental Studio", "Surya Dental Studio", "7008333444", None, "Dental Clinic", "Berhampur", "Odisha", "http://suryadental-odisha.in", "", "", "Contacted", 15000, 0, 4.5, ["no_https", "not_mobile_friendly"]),
        ("signal", "leadharvest_signal", "Puri SeaBreeze Resort", "Puri SeaBreeze Resort", "9437444555", None, "Hotel & Resort", "Puri", "Odisha", "http://puriseabreeze.com", "", "", "Meeting booked", 25000, 0, 4.3, ["broken_website", "slow_site"]),
        ("signal", "leadharvest_signal", "Rourkela Steel Gym", "Rourkela Steel Gym", "8249555666", None, "Gym & Fitness", "Rourkela", "Odisha", "", "", "", "New", 10000, 1, 4.1, ["no_website"]),
        ("signal", "leadharvest_signal", "Indore MedPlus Dental", "Indore MedPlus Dental", "9826666777", None, "Dental Clinic", "Indore", "Madhya Pradesh", "", "", "", "Proposal sent", 16000, 0, 4.7, ["no_website", "advertising_without_website"]),
        ("signal", "leadharvest_signal", "Jaipur Heritage Sweets", "Jaipur Heritage Sweets", "9829777888", None, "Bakery & Sweets", "Jaipur", "Rajasthan", "http://jaipursweets.in", "", "", "New", 12000, 2, 4.2, ["not_mobile_friendly"]),
        ("signal", "leadharvest_signal", "Surat Diamond Realty", "Surat Diamond Realty", "9825888999", None, "Real Estate", "Surat", "Gujarat", "", "", "", "Won", 22000, None, 4.6, ["no_website", "recently_listed"]),
        ("signal", "leadharvest_signal", "Bhubaneswar Pet Care", "Bhubaneswar Pet Care", "9438999000", None, "Veterinary Clinic", "Bhubaneswar", "Odisha", "", "", "", "New", 10000, 0, 4.5, ["no_website"]),
        ("signal", "leadharvest_signal", "Sambalpur Handloom House", "Sambalpur Handloom House", "7978000111", None, "Clothing Store", "Sambalpur", "Odisha", "", "", "", "Lost", 8000, None, 3.8, ["no_website"]),
    ]

    created = 0
    for idx, spec in enumerate(demo_specs):
        (
            stype, sname, name, bname, phone, email, btype, city, state,
            website, budget, timeline, stage, deal_val, followup_offset_days, rating, signals
        ) = spec

        health = None
        if website and ("broken_website" in signals or "no_https" in signals):
            health = {
                "url": website,
                "dns_ok": True,
                "http_status": 500 if "broken_website" in signals else 200,
                "https_ok": False,
                "mobile_viewport": "not_mobile_friendly" not in signals,
                "response_ms": 3100 if "slow_site" in signals else 680,
                "issues": [s.replace("_", " ").title() for s in signals if s != "recently_listed"],
                "checked_at": (now - timedelta(hours=6)).isoformat() + "Z",
            }

        score, temp, breakdown = compute_hot_lead_score(
            {
                "source_type": stype,
                "source_name": sname,
                "website": website,
                "phone_clean": phone,
                "rating": rating,
                "budget_range": budget,
                "timeline": timeline,
                "signals": signals,
                "website_health": health or {},
                "contacted_directly": stype == "inbound",
                "requested_quote": stype == "inbound",
            },
            weights,
        )

        is_dnc = phone == "9861099999"
        created_dt = now - timedelta(days=(idx % 6), hours=(idx % 12))
        first_contact = (created_dt + timedelta(hours=2)) if stage != "New" else None
        followup_dt = (now + timedelta(days=followup_offset_days)) if followup_offset_days is not None else None

        hl = HotLead(
            id=f"hl_demo_{idx + 1:02d}",
            source_type=stype,
            source_name=sname,
            source_url="/contact" if stype == "inbound" else "https://example.org/request",
            terms_note="Direct inbound consent" if stype == "inbound" else "Public B2B request / directory signal",
            name=name,
            business_name=bname,
            phone=f"+91 {phone}",
            phone_clean=phone,
            email=email,
            business_type=btype,
            city=city,
            state=state,
            website=website or None,
            budget_range=budget or None,
            timeline=timeline or None,
            utm_source="google" if stype == "inbound" else None,
            utm_medium="cpc" if sname == "google_ads_webhook" else ("organic" if stype == "inbound" else None),
            utm_campaign="website_design_india" if stype == "inbound" else None,
            score=score,
            temperature=temp,
            score_breakdown_json=json.dumps(breakdown),
            signals_json=json.dumps(signals),
            website_health_json=json.dumps(health) if health else None,
            rating=rating,
            stage=stage,
            deal_value_inr=deal_val,
            lost_reason="Opted out / DND" if is_dnc else ("Chose local freelancer" if stage == "Lost" else None),
            owner_name="Amar (Owner)",
            next_followup_at=followup_dt,
            first_contacted_at=first_contact,
            consent_given=(stype == "inbound"),
            consent_record="Explicit quote consent" if stype == "inbound" else "Public listing / request (verify DND before outreach)",
            do_not_contact=is_dnc,
            dnc_reason="Requested opt-out / DND" if is_dnc else None,
            created_at=created_dt,
        )
        db.add(hl)
        db.add(HotLeadActivity(
            id=f"act_demo_{idx + 1:02d}",
            lead_id=hl.id,
            activity_type="system",
            title=f"Lead captured via {sname}",
            body=f"Initial Hot Lead Score: {score}/100 ({temp})",
            created_at=created_dt,
        ))
        created += 1

    await db.commit()
    return created

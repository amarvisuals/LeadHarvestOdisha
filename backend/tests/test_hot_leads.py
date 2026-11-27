import uuid
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.config import settings
from app.core.database import AsyncSessionLocal, init_db
from app.models.entities import User, AuditLog
from app.services.auth import hash_password
from app.services.hot_leads import (
    compute_hot_lead_score,
    parse_public_requests_csv,
    DEFAULT_SCORE_WEIGHTS,
)
from sqlalchemy.future import select


@pytest.mark.asyncio
async def test_hot_lead_scoring_and_breakdown():
    lead_data = {
        "source_type": "inbound",
        "source_name": "website_quote_form",
        "website": "",
        "phone_clean": "9861011101",
        "rating": 4.6,
        "budget_range": "Rs 15,000",
        "timeline": "Immediate",
        "contacted_directly": True,
        "requested_quote": True,
    }
    score, temp, breakdown = compute_hot_lead_score(lead_data, DEFAULT_SCORE_WEIGHTS)
    assert score >= 75
    assert temp == "Hot"
    factors = {b["factor"] for b in breakdown}
    assert "contacted_directly" in factors
    assert "no_website" in factors
    assert "budget_stated" in factors

    # Editable weights test
    custom_weights = dict(DEFAULT_SCORE_WEIGHTS)
    custom_weights["contacted_directly"] = 10
    custom_weights["requested_quote"] = 10
    custom_weights["no_website"] = 5
    custom_weights["budget_stated"] = 5
    score2, temp2, _ = compute_hot_lead_score(lead_data, custom_weights)
    assert score2 < 50
    assert temp2 == "Cold"


def test_csv_import_validation():
    bad_csv = b"wrong_col,phone\nTest,9861011111\n"
    rows, errs = parse_public_requests_csv(bad_csv)
    assert rows == []
    assert len(errs) == 1

    mixed_csv = (
        b"business_name,phone,email,city,budget_range\n"
        b"Kalinga Dental,9861012345,kalinga@test.in,Bhubaneswar,Rs 12000\n"
        b"Missing Contact,,,,\n"
    )
    rows, errs = parse_public_requests_csv(mixed_csv)
    assert len(rows) == 1
    assert rows[0]["business_name"] == "Kalinga Dental"
    assert rows[0]["phone_clean"] == "9861012345"
    assert len(errs) == 1


@pytest.mark.asyncio
async def test_hot_leads_end_to_end_admin_and_compliance():
    await init_db()

    # Ensure an admin user and a normal user exist
    async with AsyncSessionLocal() as db:
        admin_email = f"hl_admin_{uuid.uuid4().hex[:6]}@test.in"
        user_email = f"hl_user_{uuid.uuid4().hex[:6]}@test.in"
        db.add(User(
            id=f"usr_{uuid.uuid4().hex[:10]}",
            name="Admin",
            email=admin_email,
            password_hash=hash_password("AdminPass@123"),
            role="admin",
            is_verified=True,
        ))
        db.add(User(
            id=f"usr_{uuid.uuid4().hex[:10]}",
            name="Regular",
            email=user_email,
            password_hash=hash_password("UserPass@123"),
            role="user",
            is_verified=True,
        ))
        await db.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Consent required on quote form
        bad_q = await client.post("/api/inbound/quote", json={
            "name": "Test",
            "phone": "9861011122",
            "business_type": "Dental Clinic",
            "city": "Cuttack",
            "consent": False,
        })
        assert bad_q.status_code == 400

        # 2. Valid inbound quote with UTM capture
        good_q = await client.post("/api/inbound/quote", json={
            "name": "Dr. Priya",
            "phone": "9861055566",
            "email": "priya@dental.in",
            "business_name": "Priya Dental Studio",
            "business_type": "Dental Clinic",
            "city": "Bhubaneswar",
            "budget_range": "Rs 15,000",
            "timeline": "Immediate",
            "consent": True,
            "utm_source": "google",
            "utm_medium": "cpc",
            "utm_campaign": "web_design_odisha",
        })
        assert good_q.status_code == 200
        lead_id = good_q.json()["lead_id"]

        # 3. Google Ads webhook & WhatsApp click
        wa_res = await client.post("/api/inbound/whatsapp-click", json={"page": "/contact", "city": "Puri"})
        assert wa_res.status_code == 200
        assert "wa.me/" in wa_res.json()["whatsapp_url"]

        ads_res = await client.post("/api/webhooks/google-ads", json={
            "google_key": settings.GOOGLE_ADS_WEBHOOK_SECRET,
            "lead_id": "gads_123",
            "user_column_data": [
                {"column_id": "FULL_NAME", "string_value": "Ravi Verma"},
                {"column_id": "PHONE_NUMBER", "string_value": "+919820012345"},
                {"column_id": "CITY", "string_value": "Pune"},
            ],
        })
        assert ads_res.status_code == 200

        # 4. Admin-only access enforcement (anonymous -> 401, regular user -> 403)
        unauth = await client.get("/api/admin/hot-leads")
        assert unauth.status_code in (401, 403)

        await client.post("/api/auth/login", json={"email": user_email, "password": "UserPass@123"})
        non_admin = await client.get("/api/admin/hot-leads")
        assert non_admin.status_code == 403

        # 5. Login as admin
        login_admin = await client.post("/api/auth/login", json={"email": admin_email, "password": "AdminPass@123"})
        assert login_admin.status_code == 200

        # 6. Pipeline transition & proposal PDF
        patch_res = await client.patch(f"/api/admin/hot-leads/{lead_id}", json={
            "stage": "Proposal sent",
            "deal_value_inr": 18000,
        })
        assert patch_res.status_code == 200
        assert patch_res.json()["stage"] == "Proposal sent"

        pdf_res = await client.post(f"/api/admin/hot-leads/{lead_id}/proposal-pdf", json={
            "package_name": "Growth Website",
            "price_range": "Rs 15,000",
            "timeline": "7 Days",
        })
        assert pdf_res.status_code == 200
        assert pdf_res.headers["content-type"] == "application/pdf"

        # 7. Do-Not-Contact enforcement blocks outreach
        dnc_patch = await client.patch(f"/api/admin/hot-leads/{lead_id}", json={
            "do_not_contact": True,
            "dnc_reason": "User opted out",
        })
        assert dnc_patch.status_code == 200

        detail = await client.get(f"/api/admin/hot-leads/{lead_id}")
        assert detail.status_code == 200
        assert detail.json()["outreach"]["blocked_by_dnc"] is True
        assert detail.json()["outreach"]["templates"]["english"]["wa_url"] is None

        blocked_act = await client.post(f"/api/admin/hot-leads/{lead_id}/activities", json={
            "activity_type": "whatsapp",
            "title": "Send WhatsApp",
        })
        assert blocked_act.status_code == 403

        # 8. Dashboard stats & audit log check
        stats_res = await client.get("/api/admin/hot-leads/stats")
        assert stats_res.status_code == 200
        assert stats_res.json()["total_leads"] >= 3

        async with AsyncSessionLocal() as db:
            logs = (await db.execute(select(AuditLog).where(AuditLog.target_id == lead_id))).scalars().all()
            assert len(logs) >= 2

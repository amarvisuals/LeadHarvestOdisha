import asyncio
import tempfile
import uuid
from pathlib import Path
import openpyxl
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.database import init_db


@pytest.mark.asyncio
async def test_e2e_saas_funnel_and_tenant_isolation():
    await init_db()
    from app.core.database import AsyncSessionLocal
    from app.models.entities import AppSetting
    from sqlalchemy.future import select

    async with AsyncSessionLocal() as db:
        s_row = (await db.execute(select(AppSetting).where(AppSetting.key == "guest_free_tries"))).scalar_one_or_none()
        orig_tries = s_row.value if s_row else "0"
        if s_row:
            s_row.value = "4"
            await db.commit()

    transport = ASGITransport(app=app)

    # Unique IP header per test so guest counters are isolated
    r_int = uuid.uuid4().int
    guest_headers = {"X-Forwarded-For": f"10.{(r_int >> 16) % 250}.{(r_int >> 8) % 250}.{r_int % 200 + 10}", "User-Agent": f"TestBrowser/{uuid.uuid4().hex[:6]}"}

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Guest runs 4 times -> succeeds; 5th attempt hits gate
        last_job_id = None
        for i in range(4):
            res = await client.post(
                "/api/jobs",
                headers=guest_headers,
                json={"states": ["Odisha"], "cities": ["Bhubaneswar"], "categories": ["Dentists & Dental Clinics"], "adapter": "mock"},
            )
            assert res.status_code == 200, f"Guest run {i+1} failed: {res.text}"
            last_job_id = res.json()["id"]

        # Simulate clearing cookies by creating a fresh AsyncClient with same IP+UA fingerprint
        async with AsyncClient(transport=transport, base_url="http://test") as fresh_client:
            blocked_res = await fresh_client.post(
                "/api/jobs",
                headers=guest_headers,
                json={"states": ["Odisha"], "cities": ["Bhubaneswar"], "categories": ["Dentists & Dental Clinics"], "adapter": "mock"},
            )
            assert blocked_res.status_code == 403
            assert blocked_res.json()["detail"]["upgrade_hint"]["action"] == "guest_limit"

        # 2. Signup -> attaches guest history
        email_a = f"usera_{uuid.uuid4().hex[:6]}@test.in"
        signup_a = await client.post(
            "/api/auth/signup",
            headers=guest_headers,
            json={
                "name": "User A",
                "email": email_a,
                "password": "StrongPassword!1",
                "phone": "9861012345",
                "business_type": "Web Design Agency",
                "terms_accepted": True,
            },
        )
        assert signup_a.status_code == 200
        assert signup_a.json()["migrated_guest_sessions"] >= 1

        # Verify guest history is now visible to User A
        hist_a = await client.get("/api/history")
        assert hist_a.status_code == 200
        assert any(h["id"] == last_job_id for h in hist_a.json())

        # 3. Upgrade User A to Pro via Simulated Payment
        sim_res = await client.post(
            "/api/billing/simulate-complete",
            json={"plan_id": "pro", "billing_cycle": "monthly", "outcome": "success"},
        )
        assert sim_res.status_code == 200
        assert sim_res.json()["status"] == "processed"

        # 4. Run Pro job across multiple states with "No Website" Smart Filter
        pro_job_res = await client.post(
            "/api/jobs",
            json={
                "states": ["Odisha", "Maharashtra"],
                "cities": ["Cuttack", "Pune"],
                "categories": ["Dentists & Dental Clinics"],
                "adapter": "mock",
                "filters": {"no_website": True, "mobile_only": True},
            },
        )
        assert pro_job_res.status_code == 200
        pro_job_id = pro_job_res.json()["id"]

        for _ in range(25):
            await asyncio.sleep(0.5)
            st = (await client.get(f"/api/jobs/{pro_job_id}")).json()
            if st["status"] == "completed":
                break
        assert st["status"] == "completed"

        # Verify Excel contains new SaaS columns
        dl = await client.get(f"/api/jobs/{pro_job_id}/download")
        assert dl.status_code == 200
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp.write(dl.content)
            tmp_path = Path(tmp.name)
        wb = openpyxl.load_workbook(tmp_path)
        headers_row = [wb["Leads"].cell(row=1, column=c).value for c in range(1, 15)]
        assert "Has Website" in headers_row
        assert "Opportunity Score" in headers_row
        assert "WhatsApp Link" in headers_row
        wb.close()
        tmp_path.unlink(missing_ok=True)

        # 5. Security Isolation: User B cannot access User A's job, Excel, or Admin routes
        async with AsyncClient(transport=transport, base_url="http://test") as client_b:
            email_b = f"userb_{uuid.uuid4().hex[:6]}@test.in"
            sb = await client_b.post(
                "/api/auth/signup",
                json={
                    "name": "User B",
                    "email": email_b,
                    "password": "StrongPassword!2",
                    "terms_accepted": True,
                },
            )
            assert sb.status_code == 200

            # Attempt cross-tenant access to User A's job & download -> MUST FAIL (403)
            forged_status = await client_b.get(f"/api/jobs/{pro_job_id}")
            assert forged_status.status_code == 403

            forged_dl = await client_b.get(f"/api/jobs/{pro_job_id}/download")
            assert forged_dl.status_code == 403

            # Attempt admin route access as normal user -> MUST FAIL (403)
            admin_try = await client_b.get("/api/admin/dashboard")
            assert admin_try.status_code == 403

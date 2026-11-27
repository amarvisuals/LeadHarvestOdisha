import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.future import select

from app.main import app
from app.core.database import AsyncSessionLocal, init_db
from app.models.entities import GeoDetectionLog, Guest, User
from app.services.auth import hash_password
from app.services.geoip import LocalPrefixGeoIPProvider, resolve_canonical_state
from app.services.payments import process_webhook_event


def test_state_resolution_and_geoip_vpn_outside_india():
    assert resolve_canonical_state("Orissa") == "Odisha"
    assert resolve_canonical_state("NCT of Delhi") == "Delhi (NCT)"
    assert resolve_canonical_state("maharashtra") == "Maharashtra"

    provider = LocalPrefixGeoIPProvider()
    mh = provider.lookup("49.36.10.20")
    assert mh.state == "Maharashtra"
    assert mh.country_code == "IN"
    assert mh.is_vpn_or_proxy is False

    vpn = provider.lookup("198.51.100.42")
    assert vpn.is_vpn_or_proxy is True
    assert vpn.requires_manual_choice is True

    outside = provider.lookup("203.0.113.77")
    assert outside.country_code == "US"
    assert outside.requires_manual_choice is True


@pytest.mark.asyncio
async def test_home_state_e2e_abuse_and_security():
    await init_db()
    transport = ASGITransport(app=app)

    mh_ip = f"49.36.{uuid.uuid4().int % 200 + 10}.{uuid.uuid4().int % 200 + 10}"
    ka_ip = f"106.51.{uuid.uuid4().int % 200 + 10}.{uuid.uuid4().int % 200 + 10}"
    ua = f"HomeStateTest/{uuid.uuid4().hex[:6]}"
    mh_headers = {"X-Forwarded-For": mh_ip, "User-Agent": ua}

    # 1. Guest from Maharashtra runs free for Maharashtra, blocked for Karnataka
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        st_res = await client.get("/api/location/status", headers=mh_headers)
        assert st_res.status_code == 200
        assert st_res.json()["home_state"] == "Maharashtra"

        ok_job = await client.post(
            "/api/jobs",
            headers=mh_headers,
            json={"states": ["Maharashtra"], "cities": ["Pune"], "categories": ["Dentists & Dental Clinics"], "adapter": "mock"},
        )
        assert ok_job.status_code == 200

        blocked_job = await client.post(
            "/api/jobs",
            headers=mh_headers,
            json={"states": ["Karnataka"], "cities": ["Bengaluru"], "categories": ["Dentists & Dental Clinics"], "adapter": "mock"},
        )
        assert blocked_job.status_code == 403
        hint = blocked_job.json()["detail"]["upgrade_hint"]
        assert hint["error_code"] == "upgrade_required"
        assert "Karnataka" in hint["locked_states"]

    # 2. Abuse test: clearing cookies AND switching IP to Karnataka still cannot unlock Karnataka
    async with AsyncClient(transport=transport, base_url="http://test") as fresh_client:
        ka_headers_same_ua = {"X-Forwarded-For": ka_ip, "User-Agent": ua}
        # Even if they pass a fresh cookie jar with same UA or IP, Maharashtra stays locked on original guest
        tamper = await fresh_client.post(
            "/api/jobs",
            headers=mh_headers,
            json={"states": ["Karnataka"], "cities": ["Bengaluru"], "categories": ["Dentists & Dental Clinics"], "adapter": "mock"},
        )
        assert tamper.status_code == 403

    # 3. Signup carries over guest state + allows 1-time correction (Maharashtra -> Gujarat) -> locks
    email = f"hs_{uuid.uuid4().hex[:8]}@test.in"
    async with AsyncClient(transport=transport, base_url="http://test") as user_client:
        su = await user_client.post(
            "/api/auth/signup",
            headers=mh_headers,
            json={
                "name": "Home State Tester",
                "email": email,
                "password": "StrongPass@123",
                "home_state": "Gujarat",
                "terms_accepted": True,
            },
        )
        assert su.status_code == 200

        me = await user_client.get("/api/auth/me")
        assert me.status_code == 200
        assert me.json()["user"]["home_state"] == "Gujarat"
        assert me.json()["user"]["home_state_locked"] is True

        # 4. 90-day change rule: first change auto-approved, second blocked
        c1 = await user_client.post("/api/location/change-request", json={"to_state": "Rajasthan", "reason": "Relocated office to Jaipur"})
        assert c1.status_code == 200
        assert c1.json()["auto_approved"] is True
        assert c1.json()["home_state"] == "Rajasthan"

        c2 = await user_client.post("/api/location/change-request", json={"to_state": "Kerala", "reason": "Trying to bypass cooldown"})
        assert c2.status_code == 429

        # 5. Upgrade to Starter -> pick 2 extra states -> Pro unlocks all
        sim = await user_client.post("/api/billing/simulate-complete", json={"plan_id": "starter", "billing_cycle": "monthly", "outcome": "success"})
        assert sim.status_code == 200

        ex = await user_client.put("/api/location/extra-states", json={"states": ["Maharashtra", "Karnataka"]})
        assert ex.status_code == 200
        assert set(ex.json()["extra_states"]) == {"Maharashtra", "Karnataka"}

        starter_ok = await user_client.post(
            "/api/jobs",
            json={"states": ["Rajasthan", "Maharashtra"], "cities": ["Jaipur", "Pune"], "categories": ["Dentists & Dental Clinics"], "adapter": "mock"},
        )
        assert starter_ok.status_code == 200

        starter_blocked = await user_client.post(
            "/api/jobs",
            json={"states": ["Delhi (NCT)"], "cities": ["New Delhi"], "categories": ["Dentists & Dental Clinics"], "adapter": "mock"},
        )
        assert starter_blocked.status_code == 403
        assert "Delhi (NCT)" in starter_blocked.json()["detail"]["upgrade_hint"]["locked_states"]

        # Upgrade to Pro -> unlocks all India
        sim_pro = await user_client.post("/api/billing/simulate-complete", json={"plan_id": "pro", "billing_cycle": "monthly", "outcome": "success"})
        assert sim_pro.status_code == 200
        pro_ok = await user_client.post(
            "/api/jobs",
            json={"states": ["Delhi (NCT)"], "cities": ["New Delhi"], "categories": ["Dentists & Dental Clinics"], "adapter": "mock"},
        )
        assert pro_ok.status_code == 200

    # 6. Security: confirm NO raw IPs stored in GeoDetectionLog
    async with AsyncSessionLocal() as db:
        logs = (await db.execute(select(GeoDetectionLog))).scalars().all()
        assert len(logs) > 0
        for lg in logs:
            assert lg.ip_hash != mh_ip
            assert mh_ip not in lg.ip_hash

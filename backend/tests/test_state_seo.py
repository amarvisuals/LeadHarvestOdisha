import uuid
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.database import AsyncSessionLocal, init_db
from app.models.entities import User
from app.services.auth import hash_password


@pytest.mark.asyncio
async def test_state_seo_admin_and_events():
    await init_db()

    async with AsyncSessionLocal() as db:
        admin_email = f"seo_admin_{uuid.uuid4().hex[:6]}@test.in"
        db.add(User(
            id=f"usr_{uuid.uuid4().hex[:10]}",
            name="SEO Admin",
            email=admin_email,
            password_hash=hash_password("AdminPass@123"),
            role="admin",
            is_verified=True,
        ))
        await db.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Public event tracking
        ev = await client.post("/api/state-seo/event", json={
            "state_slug": "maharashtra",
            "event_name": "state_hub_view",
            "variant": "A",
        })
        assert ev.status_code == 200

        # 2. Admin-only enforcement
        unauth = await client.get("/api/admin/state-seo/overview")
        assert unauth.status_code in (401, 403)

        # 3. Login as admin & check 36 states overview + config update
        await client.post("/api/auth/login", json={"email": admin_email, "password": "AdminPass@123"})
        ov = await client.get("/api/admin/state-seo/overview?days=30")
        assert ov.status_code == 200
        data = ov.json()
        assert len(data["states"]) >= 36
        assert data["cannibalisation"] == []

        upd = await client.put("/api/admin/state-seo/maharashtra", json={"daily_publish_cap": 40, "is_published": True})
        assert upd.status_code == 200

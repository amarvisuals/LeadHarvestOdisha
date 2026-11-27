import uuid
import pytest
from app.services.auth import hash_password, verify_password, hash_value
from app.services.entitlements import can_user_do, seed_defaults
from app.core.database import AsyncSessionLocal, init_db
from app.models.entities import Guest, User, Subscription


@pytest.mark.asyncio
async def test_argon2id_password_hashing():
    pw = "SuperStrongPassword!2026"
    hashed = hash_password(pw)
    assert hashed.startswith("$argon2id$")
    assert verify_password(pw, hashed) is True
    assert verify_password("wrong-password", hashed) is False


@pytest.mark.asyncio
async def test_guest_entitlements_and_4_run_limit():
    await init_db()
    async with AsyncSessionLocal() as db:
        await seed_defaults(db)
        guest = Guest(
            id=f"guest_{uuid.uuid4().hex[:8]}",
            fingerprint_hash=hash_value("fp:test"),
            ip_hash=hash_value("ip:test"),
            runs_used=0,
        )
        db.add(guest)
        await db.commit()

        # When guest_free_tries is 0 (testing mode), unlimited runs are allowed
        from sqlalchemy.future import select
        from app.models.entities import AppSetting
        setting_res = await db.execute(select(AppSetting).where(AppSetting.key == "guest_free_tries"))
        setting = setting_res.scalar_one_or_none()
        orig_val = setting.value if setting else "0"
        if setting:
            setting.value = "0"
            await db.commit()

        guest.runs_used = 10
        allowed, _, _ = await can_user_do(db, guest, "start_run", {"states": ["Odisha"]})
        assert allowed is True

        # Enable 4-run limit and verify enforcement
        if setting:
            setting.value = "4"
            await db.commit()

        # Run 1-4 allowed for Odisha without advanced filters
        for i in range(4):
            guest.runs_used = i
            allowed, _, _ = await can_user_do(db, guest, "start_run", {"states": ["Odisha"]})
            assert allowed is True

        # Non-Odisha blocked for guest
        guest.runs_used = 0
        allowed, msg, hint = await can_user_do(db, guest, "start_run", {"states": ["Maharashtra"]})
        assert allowed is False
        assert "Odisha" in msg
        assert hint["action"] == "upgrade"

        # Advanced filters blocked for guest
        allowed, _, hint = await can_user_do(db, guest, "start_run", {"states": ["Odisha"], "filters": {"no_website": True}})
        assert allowed is False
        assert hint["action"] == "upgrade"

        # 5th run blocked when limit is 4
        guest.runs_used = 4
        allowed, msg, hint = await can_user_do(db, guest, "start_run", {"states": ["Odisha"]})
        assert allowed is False
        assert hint["action"] == "guest_limit"

        if setting:
            setting.value = orig_val
            await db.commit()


@pytest.mark.asyncio
async def test_paid_tier_entitlements():
    await init_db()
    async with AsyncSessionLocal() as db:
        await seed_defaults(db)
        uid = f"usr_{uuid.uuid4().hex[:8]}"
        user = User(id=uid, name="Tester", email=f"{uid}@test.in", role="user", is_verified=True)
        db.add(user)
        sub = Subscription(id=f"sub_{uid}", user_id=uid, plan_id="starter", status="active")
        db.add(sub)
        await db.commit()

        # Starter allows 3 states and basic advanced filters (no_website)
        allowed, _, _ = await can_user_do(
            db, user, "start_run",
            {"states": ["Odisha", "West Bengal", "Andhra Pradesh"], "filters": {"no_website": True}}
        )
        assert allowed is True

        # Starter blocks 4 states
        allowed, _, hint = await can_user_do(
            db, user, "start_run",
            {"states": ["Odisha", "West Bengal", "Andhra Pradesh", "Bihar"]}
        )
        assert allowed is False
        assert hint["required_plan"] == "pro"

        # Starter blocks Pro-only min_opportunity_score
        allowed, _, hint = await can_user_do(
            db, user, "start_run",
            {"states": ["Odisha"], "filters": {"min_opportunity_score": 60}}
        )
        assert allowed is False
        assert hint["required_plan"] == "pro"

        # Upgrade to Pro -> unlocks All India & All Smart Filters
        sub.plan_id = "pro"
        await db.commit()
        allowed, _, _ = await can_user_do(
            db, user, "start_run",
            {"states": ["Odisha", "Maharashtra", "Karnataka", "Delhi"], "filters": {"min_opportunity_score": 60, "exclude_chains": True}}
        )
        assert allowed is True

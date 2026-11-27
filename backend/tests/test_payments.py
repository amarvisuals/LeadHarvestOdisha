import hashlib
import hmac
import json
import uuid
from pathlib import Path
import pytest
from sqlalchemy.future import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal, init_db
from app.models.entities import User, Subscription, Invoice
from app.services.payments import RazorpayProvider, process_webhook_event


@pytest.mark.asyncio
async def test_razorpay_webhook_signature_verification():
    provider = RazorpayProvider()
    payload = b'{"event":"payment.captured","id":"evt_123"}'
    valid_sig = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    assert provider.verify_webhook_signature(payload, valid_sig) is True
    assert provider.verify_webhook_signature(payload, "tampered_sig") is False


@pytest.mark.asyncio
async def test_idempotent_webhook_and_dunning_flow():
    await init_db()
    async with AsyncSessionLocal() as db:
        uid = f"usr_pay_{uuid.uuid4().hex[:8]}"
        user = User(id=uid, name="Pay Tester", email=f"{uid}@test.in", role="user", is_verified=True)
        db.add(user)
        db.add(Subscription(id=f"sub_{uid}", user_id=uid, plan_id="free", status="active"))
        await db.commit()

        evt_id = f"evt_{uuid.uuid4().hex[:10]}"
        # 1. Activate Pro plan via webhook
        res1 = await process_webhook_event(
            db, "simulated", evt_id, "payment.captured",
            {"user_id": uid, "plan_id": "pro", "billing_cycle": "monthly", "amount_inr": 1499},
        )
        assert res1["status"] == "processed"

        # 2. Replay same event_id -> idempotent skip
        res2 = await process_webhook_event(
            db, "simulated", evt_id, "payment.captured",
            {"user_id": uid, "plan_id": "pro", "billing_cycle": "monthly", "amount_inr": 1499},
        )
        assert res2["status"] == "already_processed"

        # Verify PDF invoice generated
        inv_res = await db.execute(select(Invoice).where(Invoice.user_id == uid))
        inv = inv_res.scalar_one_or_none()
        assert inv is not None
        assert inv.total_inr == 1499
        assert Path(inv.pdf_path).exists()

        # 3. Payment failed -> triggers 3-day dunning grace period
        fail_evt = f"evt_fail_{uuid.uuid4().hex[:8]}"
        await process_webhook_event(
            db, "simulated", fail_evt, "payment.failed",
            {"user_id": uid, "plan_id": "pro", "amount_inr": 1499, "reason": "Insufficient funds"},
        )
        sub_res = await db.execute(select(Subscription).where(Subscription.user_id == uid))
        sub = sub_res.scalar_one()
        assert sub.status == "past_due"
        assert sub.grace_until is not None

        # 4. Cancellation reverts to free
        cancel_evt = f"evt_can_{uuid.uuid4().hex[:8]}"
        await process_webhook_event(
            db, "simulated", cancel_evt, "subscription.cancelled",
            {"user_id": uid, "plan_id": "pro"},
        )
        await db.refresh(sub)
        assert sub.status == "cancelled"
        assert sub.plan_id == "free"

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from sqlalchemy.future import select

from app.core.database import AsyncSessionLocal, init_db
from app.models.entities import (
    User, Subscription, Payment, Invoice, Coupon, Job,
    AnalyticsEvent, PageView, AuditLog
)
from app.services.auth import hash_password
from app.services.payments import generate_gst_invoice_pdf


async def seed_demo_data():
    await init_db()
    async with AsyncSessionLocal() as db:
        # 1. Admin User
        admin_email = "admin@leadharvest.in"
        res = await db.execute(select(User).where(User.email == admin_email))
        admin = res.scalar_one_or_none()
        if not admin:
            admin = User(
                id="usr_admin_01",
                name="Amar (Owner)",
                email=admin_email,
                password_hash=hash_password("Admin@LeadHarvest2026!"),
                phone="+91 98610 00001",
                business_type="Custom Website Agency",
                role="admin",
                is_verified=True,
                terms_accepted_at=datetime.utcnow(),
            )
            db.add(admin)
            db.add(Subscription(
                id="sub_admin_01",
                user_id=admin.id,
                plan_id="agency",
                status="active",
                provider="manual",
            ))

        # 2. Three Test Users (Free, Starter, Pro)
        demo_users = [
            ("usr_free_01", "Rohan Das", "rohan@odishatech.in", "free", "Freelance Web Designer", "+91 94370 11111"),
            ("usr_starter_01", "Priya Mohanty", "priya@kalingamedia.in", "starter", "Digital Marketing Agency", "+91 70080 22222"),
            ("usr_pro_01", "Siddharth Patra", "siddharth@apexweb.in", "pro", "Web Design & SEO Studio", "+91 82490 33333"),
        ]
        now = datetime.utcnow()

        for uid, name, email, plan_id, btype, phone in demo_users:
            u_res = await db.execute(select(User).where(User.email == email))
            if not u_res.scalar_one_or_none():
                u = User(
                    id=uid,
                    name=name,
                    email=email,
                    password_hash=hash_password("DemoUser@123"),
                    phone=phone,
                    business_type=btype,
                    role="user",
                    is_verified=True,
                    terms_accepted_at=now - timedelta(days=5),
                    created_at=now - timedelta(days=5),
                )
                db.add(u)
                db.add(Subscription(
                    id=f"sub_{uid}",
                    user_id=uid,
                    plan_id=plan_id,
                    status="active",
                    provider="simulated",
                    current_period_start=now - timedelta(days=4),
                    current_period_end=now + timedelta(days=26),
                ))

                # Seed a sample payment + invoice for paid users
                if plan_id in ("starter", "pro"):
                    amt = 499 if plan_id == "starter" else 1499
                    sub_amt = round(amt / 1.18)
                    gst = amt - sub_amt
                    pay = Payment(
                        id=f"pay_{uid}",
                        user_id=uid,
                        subscription_id=f"sub_{uid}",
                        plan_id=plan_id,
                        amount_inr=amt,
                        gst_amount_inr=gst,
                        status="captured",
                        provider="simulated",
                        provider_payment_id=f"sim_{uid}",
                        created_at=now - timedelta(days=4),
                    )
                    db.add(pay)
                    inv = Invoice(
                        id=f"inv_{uid}",
                        invoice_number=f"LH-2026-DEMO-{plan_id.upper()}",
                        user_id=uid,
                        payment_id=pay.id,
                        plan_name=plan_id.title(),
                        subtotal_inr=sub_amt,
                        gst_amount_inr=gst,
                        total_inr=amt,
                        customer_name=name,
                        customer_email=email,
                        created_at=now - timedelta(days=4),
                    )
                    inv.pdf_path = str(generate_gst_invoice_pdf(inv))
                    db.add(inv)

                # Seed demo completed runs
                db.add(Job(
                    id=f"job_demo_{plan_id}",
                    user_id=uid,
                    status="completed",
                    adapter_name="mock",
                    states_json=json.dumps(["Odisha"]),
                    cities_json=json.dumps(["Bhubaneswar", "Cuttack"]),
                    categories_json=json.dumps(["Dentists & Dental Clinics"]),
                    filters_json=json.dumps({"no_website": True, "mobile_only": True} if plan_id != "free" else {}),
                    total_found=42,
                    duplicates_skipped=4,
                    new_leads=28,
                    progress_pct=100.0,
                    current_stage="success",
                    current_detail="All done! 28 new leads are ready.",
                    duration_seconds=18,
                    created_at=now - timedelta(days=2),
                    completed_at=now - timedelta(days=2),
                ))

        # 3. Sample Coupon
        c_res = await db.execute(select(Coupon).where(Coupon.code == "WELCOME20"))
        if not c_res.scalar_one_or_none():
            db.add(Coupon(
                id="cpn_welcome20",
                code="WELCOME20",
                discount_type="percent",
                discount_value=20,
                max_uses=500,
                is_active=True,
            ))

        # 4. Sample Analytics
        pv_count = len((await db.execute(select(PageView))).scalars().all())
        if pv_count == 0:
            for d in range(7):
                day_dt = now - timedelta(days=d)
                for i in range(6 - (d % 3)):
                    db.add(PageView(
                        session_id=f"sess_{d}_{i}",
                        path="/",
                        device_type="desktop" if i % 2 == 0 else "mobile",
                        created_at=day_dt,
                    ))
                db.add(AnalyticsEvent(
                    session_id=f"sess_{d}_0",
                    event_name="run_started",
                    created_at=day_dt,
                ))

        db.add(AuditLog(
            actor_user_id="usr_admin_01",
            actor_email=admin_email,
            action="seed_demo_data",
            target_type="system",
            target_id="initial",
        ))
        await db.commit()
        print("Seeded admin (admin@leadharvest.in / Admin@LeadHarvest2026!), 3 test users, demo runs, and WELCOME20 coupon.")


if __name__ == "__main__":
    asyncio.run(seed_demo_data())

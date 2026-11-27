from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def _ensure_sqlite_columns(conn):
    """Safely adds new v2 SaaS columns to existing v1 SQLite tables without data loss."""
    migrations = {
        "known_records": [
            ("user_id", "VARCHAR(64)"),
            ("guest_id", "VARCHAR(64)"),
            ("state", "VARCHAR(100)"),
        ],
        "jobs": [
            ("user_id", "VARCHAR(64)"),
            ("guest_id", "VARCHAR(64)"),
            ("states_json", "TEXT"),
            ("filters_json", "TEXT"),
            ("priority", "INTEGER DEFAULT 1"),
            ("max_leads_cap", "INTEGER DEFAULT 100"),
            ("filtered_out_count", "INTEGER DEFAULT 0"),
            ("csv_file", "VARCHAR(255)"),
            ("expires_at", "DATETIME"),
            ("duration_seconds", "INTEGER DEFAULT 0"),
        ],
        "job_leads": [
            ("email", "VARCHAR(255)"),
            ("state", "VARCHAR(100)"),
            ("has_website", "BOOLEAN DEFAULT 0"),
            ("mobile_available", "BOOLEAN DEFAULT 0"),
            ("has_social_only", "BOOLEAN DEFAULT 0"),
            ("social_url", "VARCHAR(500)"),
            ("is_verified_listing", "BOOLEAN DEFAULT 0"),
            ("is_chain", "BOOLEAN DEFAULT 0"),
            ("opportunity_score", "INTEGER DEFAULT 0"),
            ("lead_tag", "VARCHAR(100)"),
            ("whatsapp_link", "VARCHAR(500)"),
        ],
        "presets": [
            ("user_id", "VARCHAR(64)"),
            ("states_json", "TEXT"),
            ("filters_json", "TEXT"),
        ],
        "uploaded_file_audits": [
            ("user_id", "VARCHAR(64)"),
            ("guest_id", "VARCHAR(64)"),
        ],
        "users": [
            ("home_state", "VARCHAR(100)"),
            ("home_state_source", "VARCHAR(32)"),
            ("home_state_locked_at", "DATETIME"),
            ("home_state_corrected", "BOOLEAN DEFAULT 0"),
            ("location_unverified", "BOOLEAN DEFAULT 0"),
            ("detection_confidence", "VARCHAR(32)"),
            ("last_change_request_at", "DATETIME"),
        ],
        "guests": [
            ("home_state", "VARCHAR(100)"),
            ("home_state_source", "VARCHAR(32)"),
            ("home_state_locked_at", "DATETIME"),
            ("location_unverified", "BOOLEAN DEFAULT 0"),
            ("detection_confidence", "VARCHAR(32)"),
            ("country_code", "VARCHAR(10)"),
        ],
    }

    for table, cols in migrations.items():
        res = await conn.execute(text(f"PRAGMA table_info({table})"))
        existing = {row[1] for row in res.fetchall()}
        if not existing:
            continue
        for col_name, col_type in cols:
            if col_name not in existing:
                await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}"))

    # Migrate existing users who were previously limited to Odisha
    await conn.execute(
        text(
            "UPDATE users SET home_state = 'Odisha', home_state_source = 'migrated' "
            "WHERE home_state IS NULL AND role != 'admin'"
        )
    )


async def init_db():
    async with engine.begin() as conn:
        from app.models import entities  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)
        if settings.DATABASE_URL.startswith("sqlite"):
            await _ensure_sqlite_columns(conn)

    from app.services.entitlements import seed_defaults
    async with AsyncSessionLocal() as session:
        await seed_defaults(session)

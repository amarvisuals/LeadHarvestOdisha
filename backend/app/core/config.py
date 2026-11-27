from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "LeadHarvest India"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development | production | test

    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    PROJECT_ROOT: Path = BASE_DIR.parent
    CONFIG_DIR: Path = (PROJECT_ROOT / "config") if (PROJECT_ROOT / "config").exists() else (BASE_DIR / "config")
    DATA_DIR: Path = BASE_DIR / "data"
    UPLOADS_DIR: Path = DATA_DIR / "uploads"
    EXPORTS_DIR: Path = DATA_DIR / "exports"
    INVOICES_DIR: Path = DATA_DIR / "invoices"

    # Database (PostgreSQL in production/Docker, SQLite for local dev/testing)
    DATABASE_URL: str = f"sqlite+aiosqlite:///{DATA_DIR / 'leadharvest.db'}"
    SYNC_DATABASE_URL: str = f"sqlite:///{DATA_DIR / 'leadharvest.db'}"

    # Redis (optional for local dev; required for multi-worker production)
    REDIS_URL: str = ""

    # Security & Auth
    SECRET_KEY: str = "dev-secret-change-me-in-production-leadharvest-india-2026"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"
    FRONTEND_URL: str = "http://localhost:3000"
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://leadharvestodisha.vercel.app",
    ]

    # OAuth (optional)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # Payments (Razorpay + Simulated fallback)
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = "dev-webhook-secret"
    PAYMENT_MODE: str = "simulated"  # simulated | razorpay

    # Email (SMTP / Resend / console fallback)
    EMAIL_PROVIDER: str = "console"  # console | smtp | resend
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "noreply@leadharvest.in"

    # Admin bootstrap (creates initial admin on startup if none exists; override in Render env vars)
    ADMIN_EMAIL: str = "admin@leadharvest.in"
    ADMIN_PASSWORD: str = "Admin@LeadHarvest2026!"
    ADMIN_NAME: str = "Amar (Owner)"

    # Scraper pacing and limits
    MIN_PAGE_DELAY_SEC: float = 2.0
    MAX_PAGE_DELAY_SEC: float = 5.0
    MAX_CONCURRENCY: int = 2
    MAX_PAGE_RETRIES: int = 3
    DEFAULT_MAX_SCROLLS: int = 5

    # Matching thresholds
    FUZZY_MATCH_THRESHOLD: int = 90

    # Guest & SaaS defaults (0 = unlimited guest runs during testing phase)
    GUEST_FREE_TRIES_DEFAULT: int = 0

    model_config = {"env_prefix": "LEADHARVEST_", "extra": "ignore"}


settings = Settings()

# Ensure local storage directories exist
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
settings.EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
settings.INVOICES_DIR.mkdir(parents=True, exist_ok=True)

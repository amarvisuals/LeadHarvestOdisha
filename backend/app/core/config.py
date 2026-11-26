from pathlib import Path
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "LeadHarvest Odisha"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    PROJECT_ROOT: Path = BASE_DIR.parent
    CONFIG_DIR: Path = (PROJECT_ROOT / "config") if (PROJECT_ROOT / "config").exists() else (BASE_DIR / "config")
    DATA_DIR: Path = BASE_DIR / "data"
    UPLOADS_DIR: Path = DATA_DIR / "uploads"
    EXPORTS_DIR: Path = DATA_DIR / "exports"
    
    DATABASE_URL: str = f"sqlite+aiosqlite:///{DATA_DIR / 'leadharvest.db'}"
    SYNC_DATABASE_URL: str = f"sqlite:///{DATA_DIR / 'leadharvest.db'}"
    
    # Scraper pacing and limits
    MIN_PAGE_DELAY_SEC: float = 2.0
    MAX_PAGE_DELAY_SEC: float = 5.0
    MAX_CONCURRENCY: int = 2
    MAX_PAGE_RETRIES: int = 3
    DEFAULT_MAX_SCROLLS: int = 5
    
    # Matching thresholds
    FUZZY_MATCH_THRESHOLD: int = 90
    
    model_config = {"env_prefix": "LEADHARVEST_"}

settings = Settings()

# Ensure directories exist
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
settings.EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

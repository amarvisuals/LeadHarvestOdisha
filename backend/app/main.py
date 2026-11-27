from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.database import init_db
from app.api.endpoints import router as core_router
from app.api.auth_routes import router as auth_router
from app.api.billing_routes import router as billing_router
from app.api.analytics_routes import router as analytics_router
from app.api.admin_routes import router as admin_router
from app.api.seo_blog_routes import router as seo_blog_router

logger = setup_logging(debug=settings.DEBUG)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing LeadHarvest India SaaS database schema...")
    await init_db()
    logger.info("Database initialized successfully.")
    yield
    logger.info("Shutting down LeadHarvest India backend.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="LeadHarvest India – All-India B2B Lead Data Collection SaaS.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if settings.ENVIRONMENT == "production" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


app.include_router(core_router)
app.include_router(auth_router)
app.include_router(billing_router)
app.include_router(analytics_router)
app.include_router(admin_router)
app.include_router(seo_blog_router)


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }

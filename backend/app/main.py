"""
FinSage Backend — Main Application Entry Point.
"""

import asyncio
from contextlib import asynccontextmanager, suppress
from sqlalchemy import select
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import init_db, async_session
from app.models.user import User
from app.routers import health, dashboard, auth, chat, forecasting, simulator, alerts, tax, ingestion
from app.services.anomaly_detection import run_proactive_anomaly_scan

# Import models so SQLModel discovers them for table creation
import app.models  # noqa: F401

settings = get_settings()
ANOMALY_SCAN_INTERVAL_SECONDS = 15 * 60


def _build_allowed_origins() -> list[str]:
    frontend_origin = (settings.frontend_url or "").rstrip("/")
    origins = [
        frontend_origin,
        "http://localhost:5173",
        "http://localhost:8080",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
    ]
    # Preserve order while removing empty entries and duplicates.
    return list(dict.fromkeys(origin for origin in origins if origin))


async def _run_background_anomaly_scans() -> None:
    """Continuously generate proactive anomaly alerts for active users."""
    while True:
        try:
            async with async_session() as session:
                result = await session.execute(select(User.id).where(User.is_active == True))
                user_ids = [row[0] for row in result.all()]

                for user_id in user_ids:
                    await run_proactive_anomaly_scan(session, user_id)

                await session.commit()
        except Exception:
            # Background scans should never crash the app startup lifecycle.
            pass

        await asyncio.sleep(ANOMALY_SCAN_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create DB tables. Shutdown: cleanup."""
    await init_db()

    anomaly_scan_task: asyncio.Task | None = None
    if settings.environment != "test":
        anomaly_scan_task = asyncio.create_task(_run_background_anomaly_scans())

    try:
        yield
    finally:
        if anomaly_scan_task:
            anomaly_scan_task.cancel()
            with suppress(asyncio.CancelledError):
                await anomaly_scan_task


app = FastAPI(
    title="FinSage API",
    description="AI-Powered Personal Finance Intelligence System",
    version="0.1.0",
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Consistent payload for request-validation failures."""
    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "detail": exc.errors(),
            "path": request.url.path,
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Catch-all error response to avoid leaking stack traces in production."""
    detail = str(exc) if settings.environment == "development" else "Internal server error"
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "detail": detail,
            "path": request.url.path,
        },
    )

# CORS — allow frontend to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=_build_allowed_origins(),
    # Also allow localhost/127.0.0.1 on arbitrary ports for local dev preview URLs.
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(forecasting.router, prefix="/api/v1")
app.include_router(simulator.router, prefix="/api/v1")
app.include_router(alerts.router, prefix="/api/v1")
app.include_router(tax.router, prefix="/api/v1")
app.include_router(ingestion.router, prefix="/api/v1")


@app.post("/api/v1/seed", tags=["dev"])
async def seed_database():
    """DEV ONLY: Seed the database with demo data."""
    from app.services.seed_data import seed_demo_data
    from app.database import async_session

    async with async_session() as session:
        result = await seed_demo_data(session)
        return result


@app.get("/")
async def root():
    return {
        "app": "FinSage API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }

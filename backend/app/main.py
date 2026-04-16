"""
FinSage Backend — Main Application Entry Point.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db, get_session
from app.routers import health, dashboard, auth

# Import models so SQLModel discovers them for table creation
import app.models  # noqa: F401

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create DB tables. Shutdown: cleanup."""
    await init_db()
    yield


app = FastAPI(
    title="FinSage API",
    description="AI-Powered Personal Finance Intelligence System",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow frontend to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")


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

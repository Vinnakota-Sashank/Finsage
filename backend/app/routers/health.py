"""
Health check router — verify the API and database are alive.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_session

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Basic API health check."""
    return {"status": "healthy", "service": "finsage-api", "version": "0.1.0"}


@router.get("/health/db")
async def db_health_check(session: AsyncSession = Depends(get_session)):
    """Database connectivity check."""
    try:
        result = await session.execute(text("SELECT 1"))
        result.scalar()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

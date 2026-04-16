"""
Alerts router — proactive intelligence feed, filters, and trend analytics.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

from app.database import get_session
from app.models.alert import Alert
from app.models.user import User
from app.routers.dashboard import get_dashboard_user

router = APIRouter(prefix="/alerts", tags=["alerts"])

Severity = Literal["all", "critical", "warning", "info", "insight"]

ACTION_BY_TYPE = {
    "spending_spike": "Review Transactions",
    "credit_health": "Set Payment Reminder",
    "budget_breach": "Adjust Budget",
    "goal_risk": "Adjust Savings Plan",
    "recurring_anomaly": "Check Subscription",
}


class AlertFeedItem(SQLModel):
    id: int
    severity: str
    title: str
    desc: str
    action: str
    time: str
    is_read: bool
    created_at: str


class WeeklyAlertPoint(SQLModel):
    week: str
    count: int


class AlertSummaryResponse(SQLModel):
    filter: str
    unread_count: int
    weekly_alerts: list[WeeklyAlertPoint]
    alerts: list[AlertFeedItem]


def _relative_time(ts: datetime, now: datetime) -> str:
    delta = now - ts
    minutes = int(delta.total_seconds() // 60)

    if minutes < 1:
        return "just now"
    if minutes < 60:
        return f"{minutes} min ago"

    hours = minutes // 60
    if hours < 24:
        return f"{hours} hour{'s' if hours != 1 else ''} ago"

    days = hours // 24
    if days == 1:
        return "Yesterday"
    if days < 7:
        return f"{days} days ago"

    weeks = max(1, days // 7)
    return f"{weeks} week{'s' if weeks != 1 else ''} ago"


async def _weekly_trend(
    session: AsyncSession,
    user_id: int,
    weeks: int,
) -> list[WeeklyAlertPoint]:
    now = datetime.utcnow()
    start_date = now - timedelta(days=weeks * 7)

    result = await session.execute(
        select(Alert.created_at)
        .where(Alert.user_id == user_id, Alert.created_at >= start_date)
        .order_by(Alert.created_at.asc())
    )
    rows = result.all()

    counters = [0 for _ in range(weeks)]
    for row in rows:
        created_at = row[0]
        day_index = (now - created_at).days
        week_index_from_now = min(weeks - 1, max(0, day_index // 7))
        bucket = weeks - 1 - week_index_from_now
        counters[bucket] += 1

    return [WeeklyAlertPoint(week=f"W{i + 1}", count=counters[i]) for i in range(weeks)]


@router.get("/feed", response_model=list[AlertFeedItem])
async def get_alert_feed(
    severity: Severity = Query(default="all"),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(get_dashboard_user),
    session: AsyncSession = Depends(get_session),
):
    """Return filtered alert feed with action recommendations and relative timestamps."""
    query = select(Alert).where(Alert.user_id == current_user.id)
    if severity != "all":
        query = query.where(Alert.severity == severity)

    result = await session.execute(query.order_by(Alert.created_at.desc()).limit(limit))
    alerts = result.scalars().all()
    now = datetime.utcnow()

    return [
        AlertFeedItem(
            id=alert.id,
            severity=alert.severity,
            title=alert.title,
            desc=alert.description,
            action=ACTION_BY_TYPE.get(alert.alert_type, "Review Insight"),
            time=_relative_time(alert.created_at, now),
            is_read=alert.is_read,
            created_at=alert.created_at.isoformat(),
        )
        for alert in alerts
    ]


@router.get("/weekly-trend", response_model=list[WeeklyAlertPoint])
async def get_alert_weekly_trend(
    weeks: int = Query(default=4, ge=2, le=12),
    current_user: User = Depends(get_dashboard_user),
    session: AsyncSession = Depends(get_session),
):
    """Return alert volume grouped into week buckets for trend mini-chart."""
    return await _weekly_trend(session, current_user.id, weeks)


@router.get("/summary", response_model=AlertSummaryResponse)
async def get_alert_summary(
    severity: Severity = Query(default="all"),
    weeks: int = Query(default=4, ge=2, le=12),
    current_user: User = Depends(get_dashboard_user),
    session: AsyncSession = Depends(get_session),
):
    """Return complete Alerts page payload: filtered feed + weekly trend + unread count."""
    unread_result = await session.execute(
        select(func.count(Alert.id)).where(Alert.user_id == current_user.id, Alert.is_read == False)
    )
    unread_count = int(unread_result.scalar() or 0)

    feed = await get_alert_feed(
        severity=severity,
        limit=50,
        current_user=current_user,
        session=session,
    )
    weekly = await _weekly_trend(session, current_user.id, weeks)

    return AlertSummaryResponse(
        filter=severity,
        unread_count=unread_count,
        weekly_alerts=weekly,
        alerts=feed,
    )


@router.patch("/{alert_id}/read", response_model=dict)
async def mark_alert_read(
    alert_id: int,
    current_user: User = Depends(get_dashboard_user),
    session: AsyncSession = Depends(get_session),
):
    """Mark a specific alert as read."""
    result = await session.execute(
        select(Alert).where(Alert.id == alert_id, Alert.user_id == current_user.id)
    )
    alert = result.scalar_one_or_none()
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.is_read = True
    await session.commit()
    return {"ok": True, "alert_id": alert_id}

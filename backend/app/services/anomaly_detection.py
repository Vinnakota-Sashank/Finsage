"""
Proactive anomaly detection service for alerts.
Generates Z-score spending spike alerts and budget threshold breaches.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from statistics import mean, pstdev
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.budget import Budget
from app.models.transaction import Transaction


def _currency(amount: float) -> str:
    return f"₹{amount:,.0f}"


async def _has_recent_alert(
    session: AsyncSession,
    user_id: int,
    alert_type: str,
    title: str,
    since: datetime,
) -> bool:
    result = await session.execute(
        select(Alert.id).where(
            Alert.user_id == user_id,
            Alert.alert_type == alert_type,
            Alert.title == title,
            Alert.created_at >= since,
        )
    )
    return result.scalars().first() is not None


async def _detect_daily_spike(
    session: AsyncSession,
    user_id: int,
    now: datetime,
) -> tuple[list[Alert], float | None]:
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_start = today_start + timedelta(days=1)
    history_start = today_start - timedelta(days=28)

    result = await session.execute(
        select(
            func.date(Transaction.timestamp).label("day"),
            func.coalesce(func.sum(Transaction.amount), 0).label("total"),
        )
        .where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "debit",
            Transaction.timestamp >= history_start,
            Transaction.timestamp < tomorrow_start,
        )
        .group_by("day")
    )
    rows = result.all()

    daily_map = {str(row.day): float(row.total) for row in rows}

    baseline_values: list[float] = []
    for offset in range(28, 0, -1):
        day_key = (today_start - timedelta(days=offset)).strftime("%Y-%m-%d")
        baseline_values.append(daily_map.get(day_key, 0.0))

    if len(baseline_values) < 14:
        return [], None

    baseline_mean = mean(baseline_values)
    baseline_std = pstdev(baseline_values)
    today_key = today_start.strftime("%Y-%m-%d")
    today_total = daily_map.get(today_key, 0.0)

    if baseline_std <= 0:
        return [], None

    z_score = (today_total - baseline_mean) / baseline_std

    if z_score < 2.2:
        return [], z_score

    title = "Unusual Daily Spending Spike"
    already_exists = await _has_recent_alert(
        session=session,
        user_id=user_id,
        alert_type="spending_spike",
        title=title,
        since=today_start - timedelta(days=2),
    )
    if already_exists:
        return [], z_score

    top_result = await session.execute(
        select(
            Transaction.category,
            func.coalesce(func.sum(Transaction.amount), 0).label("total"),
        )
        .where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "debit",
            Transaction.timestamp >= today_start,
            Transaction.timestamp < tomorrow_start,
        )
        .group_by(Transaction.category)
        .order_by(func.sum(Transaction.amount).desc())
        .limit(2)
    )
    top_categories = top_result.all()
    top_summary = ", ".join(
        f"{str(item.category).replace('_', ' ').title()} {_currency(float(item.total))}"
        for item in top_categories
    )

    severity = "critical" if z_score >= 3.0 else "warning"
    description = (
        f"Today's spend is {_currency(today_total)}, {z_score:.1f}σ above your 28-day baseline "
        f"of {_currency(baseline_mean)}."
    )
    if top_summary:
        description += f" Top categories: {top_summary}."

    alert = Alert(
        user_id=user_id,
        severity=severity,
        alert_type="spending_spike",
        title=title,
        description=description,
        recommendation="Review large debits today and postpone non-essential expenses for the next 48 hours.",
    )
    return [alert], z_score


async def _detect_budget_breaches(
    session: AsyncSession,
    user_id: int,
    now: datetime,
) -> list[Alert]:
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    next_month = (month_start + timedelta(days=35)).replace(day=1)

    budget_result = await session.execute(select(Budget).where(Budget.user_id == user_id))
    budgets = budget_result.scalars().all()

    alerts: list[Alert] = []
    for budget in budgets:
        if budget.monthly_limit <= 0:
            continue

        spend_result = await session.execute(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                Transaction.user_id == user_id,
                Transaction.transaction_type == "debit",
                Transaction.category == budget.category,
                Transaction.timestamp >= month_start,
                Transaction.timestamp < next_month,
            )
        )
        spend = float(spend_result.scalar() or 0.0)
        utilization = spend / budget.monthly_limit

        if utilization < budget.alert_threshold:
            continue

        category_label = budget.category.replace("_", " ").title()
        title = f"{category_label} Budget Threshold Breached"
        exists = await _has_recent_alert(
            session=session,
            user_id=user_id,
            alert_type="budget_breach",
            title=title,
            since=month_start,
        )
        if exists:
            continue

        severity = "critical" if utilization >= 1.0 else "warning"
        recommendation = (
            f"You have used {utilization * 100:.0f}% of this budget. "
            "Slow this category for the rest of the month or increase budget limits."
        )

        alerts.append(
            Alert(
                user_id=user_id,
                severity=severity,
                alert_type="budget_breach",
                title=title,
                description=(
                    f"{category_label} spend is {_currency(spend)} against a monthly limit of "
                    f"{_currency(budget.monthly_limit)} ({utilization * 100:.0f}% used)."
                ),
                recommendation=recommendation,
            )
        )

    return alerts


async def run_proactive_anomaly_scan(
    session: AsyncSession,
    user_id: int,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Run proactive anomaly scans and stage newly generated alerts in the session."""
    current_time = now or datetime.utcnow()

    spike_alerts, z_score = await _detect_daily_spike(session, user_id, current_time)
    budget_alerts = await _detect_budget_breaches(session, user_id, current_time)

    new_alerts = spike_alerts + budget_alerts
    if new_alerts:
        session.add_all(new_alerts)
        await session.flush()

    return {
        "generated": len(new_alerts),
        "daily_spend_zscore": round(z_score, 2) if z_score is not None else None,
        "types": [alert.alert_type for alert in new_alerts],
    }

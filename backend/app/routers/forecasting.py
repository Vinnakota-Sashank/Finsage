"""
Forecasting router — trend projections, goal probabilities, and net-worth outlook.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

from app.database import get_session
from app.models.account import Account
from app.models.goal import Goal
from app.models.transaction import Transaction
from app.models.user import User
from app.routers.dashboard import get_dashboard_user

router = APIRouter(prefix="/forecasting", tags=["forecasting"])


class SpendingPoint(SQLModel):
    month: str
    spend: float | None = None
    forecast: float | None = None
    upper: float | None = None
    lower: float | None = None


class GoalProbabilityPoint(SQLModel):
    name: str
    prob: int


class NetWorthPoint(SQLModel):
    month: str
    assets: float
    liabilities: float
    net_worth: float


class ForecastOverviewResponse(SQLModel):
    spending: dict[str, Any]
    goal_probabilities: list[GoalProbabilityPoint]
    net_worth_projection: list[NetWorthPoint]
    insights: list[str]


def _month_start(dt: datetime) -> datetime:
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _shift_month(month_start: datetime, offset: int) -> datetime:
    month_index = month_start.month - 1 + offset
    year = month_start.year + (month_index // 12)
    month = (month_index % 12) + 1
    return month_start.replace(year=year, month=month, day=1)


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _months_between(start: datetime, end: datetime) -> int:
    return max(1, (end.year - start.year) * 12 + (end.month - start.month))


async def _monthly_spending_series(
    session: AsyncSession,
    user_id: int,
    months: int,
) -> list[dict[str, float | str]]:
    now = datetime.utcnow()
    current_month_start = _month_start(now)
    month_starts = [_shift_month(current_month_start, -i) for i in range(months - 1, -1, -1)]
    start_date = month_starts[0]

    result = await session.execute(
        select(
            extract("year", Transaction.timestamp).label("year"),
            extract("month", Transaction.timestamp).label("month"),
            func.sum(Transaction.amount).label("total"),
        )
        .where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "debit",
            Transaction.timestamp >= start_date,
        )
        .group_by("year", "month")
        .order_by("year", "month")
    )
    rows = result.all()
    totals = {(int(r.year), int(r.month)): float(r.total) for r in rows}

    return [
        {"month": m.strftime("%b"), "spend": round(totals.get((m.year, m.month), 0.0), 2)}
        for m in month_starts
    ]


async def _average_monthly_savings(session: AsyncSession, user: User) -> float:
    now = datetime.utcnow()
    lookback_start = _shift_month(_month_start(now), -3)
    lookback_end = _month_start(now)

    income_result = await session.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user.id,
            Transaction.transaction_type == "credit",
            Transaction.timestamp >= lookback_start,
            Transaction.timestamp < lookback_end,
        )
    )
    spend_result = await session.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user.id,
            Transaction.transaction_type == "debit",
            Transaction.timestamp >= lookback_start,
            Transaction.timestamp < lookback_end,
        )
    )

    income = float(income_result.scalar() or 0)
    spend = float(spend_result.scalar() or 0)
    savings = (income - spend) / 3

    if savings <= 0:
        if user.monthly_income and user.monthly_income > 0:
            return round(user.monthly_income * 0.15, 2)
        return 5000.0

    return round(savings, 2)


async def _build_spending_projection(
    session: AsyncSession,
    user_id: int,
    history_months: int,
    forecast_months: int,
) -> dict[str, Any]:
    historical = await _monthly_spending_series(session, user_id, history_months)
    values = [float(point["spend"]) for point in historical]

    growth_rates: list[float] = []
    for prev, curr in zip(values[:-1], values[1:]):
        if prev > 0:
            growth_rates.append((curr - prev) / prev)

    avg_growth = sum(growth_rates) / len(growth_rates) if growth_rates else 0.03
    avg_growth = _clamp(avg_growth, -0.15, 0.15)

    volatility = _clamp(0.08 + (abs(avg_growth) * 0.5), 0.08, 0.25)
    last_value = values[-1] if values else 90000.0

    now = datetime.utcnow()
    current_month_start = _month_start(now)
    forecast: list[dict[str, float | str]] = []

    projected = float(last_value)
    for step in range(1, forecast_months + 1):
        projected = max(0.0, projected * (1 + avg_growth))
        month_label = _shift_month(current_month_start, step).strftime("%b")
        upper = projected * (1 + volatility)
        lower = projected * (1 - volatility)
        forecast.append(
            {
                "month": month_label,
                "forecast": round(projected, 2),
                "upper": round(upper, 2),
                "lower": round(lower, 2),
            }
        )

    combined = [
        {"month": row["month"], "spend": row["spend"]}
        for row in historical
    ] + [
        {
            "month": row["month"],
            "forecast": row["forecast"],
            "upper": row["upper"],
            "lower": row["lower"],
        }
        for row in forecast
    ]

    next_month = forecast[0] if forecast else {"forecast": 0, "upper": 0, "lower": 0}

    return {
        "historical": historical,
        "forecast": forecast,
        "combined": combined,
        "next_month_forecast": next_month,
        "avg_growth_pct": round(avg_growth * 100, 1),
        "confidence_band_pct": round(volatility * 100, 1),
    }


async def _build_goal_probabilities(
    session: AsyncSession,
    user: User,
) -> list[GoalProbabilityPoint]:
    result = await session.execute(
        select(Goal)
        .where(Goal.user_id == user.id, Goal.status == "active")
        .order_by(Goal.deadline)
    )
    goals = result.scalars().all()
    avg_savings = await _average_monthly_savings(session, user)

    goal_probs: list[GoalProbabilityPoint] = []
    now = datetime.utcnow()

    for goal in goals:
        remaining = max(0.0, goal.target_amount - goal.current_amount)
        months_left = _months_between(now, datetime(goal.deadline.year, goal.deadline.month, 1))
        needed_per_month = remaining / months_left if months_left > 0 else remaining

        if remaining <= 0:
            prob = 99
        elif needed_per_month <= 0:
            prob = 95
        else:
            ratio = avg_savings / needed_per_month
            prob = int(round(_clamp(15 + (ratio * 70), 5, 95)))

        goal_probs.append(GoalProbabilityPoint(name=goal.name, prob=prob))

    return goal_probs


async def _build_net_worth_projection(
    session: AsyncSession,
    user: User,
    months: int,
) -> list[NetWorthPoint]:
    account_result = await session.execute(
        select(func.coalesce(func.sum(Account.balance), 0)).where(Account.user_id == user.id)
    )
    base_assets = float(account_result.scalar() or 0)
    if base_assets <= 0:
        base_assets = 1240000.0

    avg_savings = await _average_monthly_savings(session, user)
    base_liabilities = 160000.0

    now = datetime.utcnow()
    current_month_start = _month_start(now)

    points: list[NetWorthPoint] = []
    for offset in range(months):
        month = _shift_month(current_month_start, offset)
        assets = base_assets + (avg_savings * offset) + (base_assets * 0.004 * offset)
        liabilities = max(0.0, base_liabilities - (2000.0 * offset))
        points.append(
            NetWorthPoint(
                month=month.strftime("%b"),
                assets=round(assets, 2),
                liabilities=round(liabilities, 2),
                net_worth=round(assets - liabilities, 2),
            )
        )

    return points


@router.get("/spending")
async def get_spending_projection(
    history_months: int = Query(default=6, ge=3, le=24),
    forecast_months: int = Query(default=3, ge=1, le=12),
    current_user: User = Depends(get_dashboard_user),
    session: AsyncSession = Depends(get_session),
):
    """Return historical spending and near-term projection with confidence band."""
    return await _build_spending_projection(session, current_user.id, history_months, forecast_months)


@router.get("/goal-probabilities", response_model=list[GoalProbabilityPoint])
async def get_goal_probabilities(
    current_user: User = Depends(get_dashboard_user),
    session: AsyncSession = Depends(get_session),
):
    """Return projected completion probabilities for active goals."""
    return await _build_goal_probabilities(session, current_user)


@router.get("/net-worth", response_model=list[NetWorthPoint])
async def get_net_worth_projection(
    months: int = Query(default=12, ge=3, le=24),
    current_user: User = Depends(get_dashboard_user),
    session: AsyncSession = Depends(get_session),
):
    """Return projected net-worth curve (assets, liabilities, net)."""
    return await _build_net_worth_projection(session, current_user, months)


@router.get("/overview", response_model=ForecastOverviewResponse)
async def get_forecasting_overview(
    current_user: User = Depends(get_dashboard_user),
    session: AsyncSession = Depends(get_session),
):
    """Return all forecasting data required by the Forecasting page."""
    spending = await _build_spending_projection(session, current_user.id, history_months=6, forecast_months=3)
    goals = await _build_goal_probabilities(session, current_user)
    net_worth = await _build_net_worth_projection(session, current_user, months=12)

    next_month = spending.get("next_month_forecast", {})
    top_goal = max(goals, key=lambda g: g.prob) if goals else None
    weakest_goal = min(goals, key=lambda g: g.prob) if goals else None

    insights: list[str] = []
    if next_month:
        insights.append(
            f"Predicted next-month spend is ₹{next_month.get('forecast', 0):,.0f} with an {spending.get('confidence_band_pct', 0):.1f}% confidence band."
        )
    if top_goal:
        insights.append(f"Strongest goal momentum: {top_goal.name} at {top_goal.prob}% completion probability.")
    if weakest_goal:
        insights.append(f"Most at-risk goal currently: {weakest_goal.name} at {weakest_goal.prob}% probability.")

    return ForecastOverviewResponse(
        spending=spending,
        goal_probabilities=goals,
        net_worth_projection=net_worth,
        insights=insights,
    )

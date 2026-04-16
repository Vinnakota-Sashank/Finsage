"""
Dashboard router — summary metrics, spending trends, and dashboard widgets.
These power the main Dashboard page.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, extract

from app.database import get_session
from app.config import get_settings
from app.models.user import User
from app.models.transaction import Transaction
from app.models.goal import Goal
from app.models.alert import Alert

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
settings = get_settings()

# Step 2 (full auth) is postponed, so dashboard routes support a dev fallback.
optional_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login", auto_error=False)


def _shift_month(month_start: datetime, offset: int) -> datetime:
    """Return a month start shifted by offset months."""
    month_index = month_start.month - 1 + offset
    year = month_start.year + (month_index // 12)
    month = (month_index % 12) + 1
    return month_start.replace(year=year, month=month, day=1)


async def get_dashboard_user(
    token: str | None = Depends(optional_oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    """
    Return authenticated user when token exists.
    In non-production, fallback to the first available user for demo mode.
    """
    if token:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            email: str | None = payload.get("sub")
            if email is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception

        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is None:
            raise credentials_exception
        return user

    if settings.environment != "production":
        result = await session.execute(select(User).order_by(User.id))
        demo_user = result.scalars().first()
        if demo_user is not None:
            return demo_user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.get("/summary")
async def get_dashboard_summary(
    current_user: User = Depends(get_dashboard_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Returns the 5 key metric cards:
    Monthly Income, Total Spending, Savings Rate, Credit Score, Net Worth.
    """
    user_id = current_user.id
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Monthly income (credits this month)
    income_result = await session.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "credit",
            Transaction.timestamp >= month_start,
        )
    )
    monthly_income = income_result.scalar()

    # Monthly spending (debits this month)
    spending_result = await session.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "debit",
            Transaction.timestamp >= month_start,
        )
    )
    total_spending = spending_result.scalar()

    # Savings rate
    savings_rate = 0.0
    if monthly_income > 0:
        savings_rate = round(((monthly_income - total_spending) / monthly_income) * 100, 1)

    # Unread alerts count
    alerts_result = await session.execute(
        select(func.count(Alert.id)).where(
            Alert.user_id == user_id,
            Alert.is_read == False,
        )
    )
    unread_alerts = alerts_result.scalar()

    return {
        "monthly_income": float(monthly_income),
        "total_spending": float(total_spending),
        "savings_rate": savings_rate,
        "credit_score": 742,  # TODO: Real credit score integration
        "net_worth": 1240000,  # TODO: Compute from accounts + investments
        "unread_alerts": unread_alerts,
    }


@router.get("/spending-trend")
async def get_spending_trend(
    months: int = Query(default=6, ge=3, le=24),
    rolling_window: int = Query(default=3, ge=2, le=12),
    current_user: User = Depends(get_dashboard_user),
    session: AsyncSession = Depends(get_session),
):
    """Returns month-wise spending totals plus rolling averages for trend charts."""
    user_id = current_user.id
    now = datetime.utcnow()
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    month_starts = [_shift_month(current_month_start, -i) for i in range(months - 1, -1, -1)]
    start_date = month_starts[0]
    rolling_window = min(rolling_window, months)

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

    totals_by_month = {
        (int(r.year), int(r.month)): float(r.total)
        for r in rows
    }

    trend = []
    amount_values: list[float] = []

    for month_start in month_starts:
        amount = totals_by_month.get((month_start.year, month_start.month), 0.0)
        amount_values.append(amount)

        avg_window = amount_values[max(0, len(amount_values) - rolling_window):]
        rolling_average = sum(avg_window) / len(avg_window) if avg_window else 0.0
        vs_rolling_pct = ((amount - rolling_average) / rolling_average * 100) if rolling_average else 0.0

        trend.append(
            {
                "month": month_start.strftime("%b"),
                "month_key": month_start.strftime("%Y-%m"),
                "amount": round(amount, 2),
                "rolling_average": round(rolling_average, 2),
                "vs_rolling_pct": round(vs_rolling_pct, 1),
            }
        )

    latest = trend[-1] if trend else {"month": "", "amount": 0.0, "rolling_average": 0.0, "vs_rolling_pct": 0.0}

    return {
        "months": months,
        "rolling_window": rolling_window,
        "period_total": round(sum(amount_values), 2),
        "latest": latest,
        "trend": trend,
    }


@router.get("/category-breakdown")
async def get_category_breakdown(
    current_user: User = Depends(get_dashboard_user),
    session: AsyncSession = Depends(get_session),
):
    """Returns spending grouped by category for pie/donut chart."""
    user_id = current_user.id
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    result = await session.execute(
        select(
            Transaction.category,
            func.sum(Transaction.amount).label("total"),
        )
        .where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "debit",
            Transaction.timestamp >= month_start,
        )
        .group_by(Transaction.category)
        .order_by(func.sum(Transaction.amount).desc())
    )
    rows = result.all()

    categories = [{"name": r.category.replace("_", " ").title(), "value": float(r.total)} for r in rows]
    return {"categories": categories}


@router.get("/goals")
async def get_goals(
    current_user: User = Depends(get_dashboard_user),
    session: AsyncSession = Depends(get_session),
):
    """Returns active goals with progress."""
    user_id = current_user.id
    result = await session.execute(
        select(Goal).where(Goal.user_id == user_id, Goal.status == "active").order_by(Goal.deadline)
    )
    goals = result.scalars().all()

    return {
        "goals": [
            {
                "id": g.id,
                "name": g.name,
                "current": g.current_amount,
                "target": g.target_amount,
                "deadline": g.deadline.isoformat(),
                "pct": round((g.current_amount / g.target_amount) * 100, 1) if g.target_amount > 0 else 0,
                "probability": g.probability,
            }
            for g in goals
        ]
    }


@router.get("/recent-alerts")
async def get_recent_alerts(
    limit: int = Query(default=4, ge=1, le=10),
    current_user: User = Depends(get_dashboard_user),
    session: AsyncSession = Depends(get_session),
):
    """Returns recent alerts for dashboard right-rail widget."""
    user_id = current_user.id
    result = await session.execute(
        select(Alert)
        .where(Alert.user_id == user_id)
        .order_by(Alert.created_at.desc())
        .limit(limit)
    )
    alerts = result.scalars().all()

    return {
        "alerts": [
            {
                "id": a.id,
                "severity": a.severity,
                "title": a.title,
                "description": a.description,
                "is_read": a.is_read,
                "created_at": a.created_at.isoformat(),
            }
            for a in alerts
        ]
    }

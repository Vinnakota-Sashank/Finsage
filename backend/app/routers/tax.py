"""
Tax router — India-specific tax intelligence, EPF projection, and UPI analytics.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

from app.database import get_session
from app.models.transaction import Transaction
from app.models.user import User
from app.routers.dashboard import get_dashboard_user

router = APIRouter(prefix="/tax", tags=["tax"])


class TaxOverviewResponse(SQLModel):
    section80c: dict
    section80d: dict
    epf_projection: list[dict]
    festival_predictor: dict
    upi_merchants: list[dict]
    highlights: list[str]


def _month_start(dt: datetime) -> datetime:
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _financial_year_start(now: datetime) -> datetime:
    fy_start_year = now.year if now.month >= 4 else now.year - 1
    return datetime(fy_start_year, 4, 1)


@router.get("/overview", response_model=TaxOverviewResponse)
async def get_tax_overview(
    current_user: User = Depends(get_dashboard_user),
    session: AsyncSession = Depends(get_session),
):
    """Return India-focused tax intelligence payload for the Tax page."""
    now = datetime.utcnow()
    fy_start = _financial_year_start(now)

    # 80C estimation components
    salary_count_result = await session.execute(
        select(func.count(Transaction.id)).where(
            Transaction.user_id == current_user.id,
            Transaction.transaction_type == "credit",
            Transaction.category == "salary",
            Transaction.timestamp >= fy_start,
            Transaction.timestamp <= now,
        )
    )
    sip_sum_result = await session.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == current_user.id,
            Transaction.transaction_type == "debit",
            Transaction.category == "sip_mutual_funds",
            Transaction.timestamp >= fy_start,
            Transaction.timestamp <= now,
        )
    )

    salary_credits = int(salary_count_result.scalar() or 0)
    sip_total = float(sip_sum_result.scalar() or 0)

    epf_value = min(86400.0, salary_credits * 7200.0)
    elss_value = min(50000.0, sip_total * 0.2)
    ppf_value = 24000.0

    section80c_total = 150000.0
    section80c_used = min(section80c_total, epf_value + elss_value + ppf_value)
    section80c_remaining = max(0.0, section80c_total - section80c_used)

    # 80D from health-category spends in FY
    health_sum_result = await session.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == current_user.id,
            Transaction.transaction_type == "debit",
            Transaction.category == "health",
            Transaction.timestamp >= fy_start,
            Transaction.timestamp <= now,
        )
    )
    section80d_total = 25000.0
    section80d_used = min(section80d_total, float(health_sum_result.scalar() or 0))
    section80d_remaining = max(0.0, section80d_total - section80d_used)

    # EPF projection model
    starting_corpus = 560000.0
    annual_contribution = 7200.0 * 12
    annual_rate = 0.0815

    epf_projection = []
    corpus = starting_corpus
    for year in range(0, 30):
        age = 30 + year
        epf_projection.append({"age": age, "corpus": round(corpus, 2)})
        corpus = (corpus * (1 + annual_rate)) + annual_contribution

    # Festival prediction from shopping trends
    shopping_result = await session.execute(
        select(
            func.coalesce(func.sum(Transaction.amount), 0),
            func.strftime("%Y", Transaction.timestamp),
        )
        .where(
            Transaction.user_id == current_user.id,
            Transaction.transaction_type == "debit",
            Transaction.category == "shopping",
            func.strftime("%m", Transaction.timestamp).in_(["10", "11"]),
        )
        .group_by(func.strftime("%Y", Transaction.timestamp))
        .order_by(func.strftime("%Y", Transaction.timestamp).asc())
    )
    shopping_rows = shopping_result.all()

    festival_data = [
        {"year": str(row[1]), "spend": round(float(row[0]), 2)}
        for row in shopping_rows[-3:]
    ]

    if festival_data:
        predicted_budget = sum(item["spend"] for item in festival_data) / len(festival_data)
    else:
        predicted_budget = 28000.0

    recommended_monthly = max(1000.0, predicted_budget / 4)

    # UPI merchant analytics for current month
    current_month_start = _month_start(now)
    upi_result = await session.execute(
        select(
            Transaction.merchant,
            func.sum(Transaction.amount).label("total"),
        )
        .where(
            Transaction.user_id == current_user.id,
            Transaction.transaction_type == "debit",
            Transaction.payment_mode == "upi",
            Transaction.timestamp >= current_month_start,
            Transaction.timestamp <= now,
            Transaction.merchant.is_not(None),
        )
        .group_by(Transaction.merchant)
        .order_by(func.sum(Transaction.amount).desc())
        .limit(5)
    )
    upi_rows = upi_result.all()
    upi_merchants = [
        {"name": str(row.merchant), "amount": round(float(row.total), 2)}
        for row in upi_rows
    ]

    highlights = [
        f"Section 80C used: ₹{section80c_used:,.0f} / ₹{section80c_total:,.0f}.",
        f"Section 80D remaining capacity: ₹{section80d_remaining:,.0f}.",
        f"Estimated Diwali budget: ₹{predicted_budget:,.0f}.",
    ]

    return TaxOverviewResponse(
        section80c={
            "used": round(section80c_used, 2),
            "total": section80c_total,
            "remaining": round(section80c_remaining, 2),
            "pct": round((section80c_used / section80c_total) * 100, 1),
            "breakdown": [
                {"name": "EPF", "value": round(epf_value, 2), "fill": "#B8860B"},
                {"name": "ELSS SIP", "value": round(elss_value, 2), "fill": "#D4AF37"},
                {"name": "PPF", "value": round(ppf_value, 2), "fill": "#FFD700"},
                {"name": "Remaining", "value": round(section80c_remaining, 2), "fill": "#222"},
            ],
            "tax_saving_opportunity": round(section80c_remaining * 0.30, 2),
        },
        section80d={
            "used": round(section80d_used, 2),
            "total": section80d_total,
            "remaining": round(section80d_remaining, 2),
            "tax_saving_opportunity": round(section80d_remaining * 0.30, 2),
            "recommendation": "Consider health insurance to utilize remaining 80D deduction.",
        },
        epf_projection=epf_projection,
        festival_predictor={
            "predicted_budget": round(predicted_budget, 2),
            "recommended_monthly_saving": round(recommended_monthly, 2),
            "start_month": "Aug",
            "data": festival_data,
        },
        upi_merchants=upi_merchants,
        highlights=highlights,
    )

"""
Simulator router — Monte Carlo what-if scenario engine.
"""

from __future__ import annotations

import random
import re
from statistics import mean

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

from app.database import get_session
from app.models.transaction import Transaction
from app.models.user import User
from app.routers.dashboard import get_dashboard_user

router = APIRouter(prefix="/simulator", tags=["simulator"])


class SimulatorRunRequest(SQLModel):
    scenario: str
    years: int = 5
    runs: int = 1000
    current_sip: float | None = None
    proposed_sip: float | None = None


class SimulatorRunResponse(SQLModel):
    scenario: str
    metrics: dict
    histogram: list[dict]
    comparison: dict
    tradeoffs: list[str]


def _extract_sip_from_text(text: str) -> float | None:
    matches = re.findall(r"(?:₹|inr)?\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(k|l|lakh|lakhs)?", text.lower())
    if not matches:
        return None

    raw, suffix = matches[-1]
    value = float(raw.replace(",", ""))
    if suffix == "k":
        value *= 1000
    elif suffix in {"l", "lakh", "lakhs"}:
        value *= 100000
    return value


def _percentile(sorted_values: list[float], p: float) -> float:
    if not sorted_values:
        return 0.0
    index = int(round((p / 100) * (len(sorted_values) - 1)))
    index = max(0, min(index, len(sorted_values) - 1))
    return sorted_values[index]


def _simulate_outcomes(monthly_sip: float, months: int, runs: int, seed: int) -> list[float]:
    rng = random.Random(seed)
    outcomes: list[float] = []

    for _ in range(runs):
        corpus = 0.0
        for _ in range(months):
            monthly_return = rng.gauss(0.010, 0.025)
            monthly_return = max(-0.12, min(0.12, monthly_return))
            corpus = max(0.0, corpus * (1 + monthly_return) + monthly_sip)
        outcomes.append(corpus)

    return outcomes


def _build_histogram(values: list[float], buckets: int = 13) -> list[dict]:
    if not values:
        return []

    low = min(values)
    high = max(values)
    if high <= low:
        return [{"bucket": f"₹{low / 100000:.1f}L", "freq": len(values)}]

    step = (high - low) / buckets
    counts = [0 for _ in range(buckets)]

    for value in values:
        idx = int((value - low) / step)
        idx = min(max(idx, 0), buckets - 1)
        counts[idx] += 1

    histogram = []
    for i, count in enumerate(counts):
        bucket_mid = low + ((i + 0.5) * step)
        histogram.append({"bucket": f"₹{bucket_mid / 100000:.1f}L", "freq": count})

    return histogram


async def _estimate_base_sip(session: AsyncSession, user_id: int) -> float:
    result = await session.execute(
        select(func.coalesce(func.avg(Transaction.amount), 0)).where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "debit",
            Transaction.category == "sip_mutual_funds",
        )
    )
    avg_sip = float(result.scalar() or 0)
    return round(avg_sip, 2) if avg_sip > 0 else 15000.0


async def _estimate_monthly_income(session: AsyncSession, user: User) -> float:
    if user.monthly_income and user.monthly_income > 0:
        return float(user.monthly_income)

    result = await session.execute(
        select(func.coalesce(func.avg(Transaction.amount), 0)).where(
            Transaction.user_id == user.id,
            Transaction.transaction_type == "credit",
            Transaction.category == "salary",
        )
    )
    avg_income = float(result.scalar() or 0)
    return avg_income if avg_income > 0 else 120000.0


@router.post("/run", response_model=SimulatorRunResponse)
async def run_simulation(
    payload: SimulatorRunRequest,
    current_user: User = Depends(get_dashboard_user),
    session: AsyncSession = Depends(get_session),
) -> SimulatorRunResponse:
    """Run Monte Carlo what-if simulation for SIP adjustment scenarios."""
    years = max(1, min(payload.years, 20))
    runs = max(200, min(payload.runs, 5000))
    months = years * 12

    inferred_proposed = _extract_sip_from_text(payload.scenario)
    base_sip = payload.current_sip or await _estimate_base_sip(session, current_user.id)
    proposed_sip = payload.proposed_sip or inferred_proposed or base_sip

    if proposed_sip <= 0:
        proposed_sip = base_sip

    base_seed = abs(hash((payload.scenario.lower().strip(), years, runs))) % 100000
    current_outcomes = _simulate_outcomes(base_sip, months, runs, seed=base_seed)
    proposed_outcomes = _simulate_outcomes(proposed_sip, months, runs, seed=base_seed + 11)

    current_sorted = sorted(current_outcomes)
    proposed_sorted = sorted(proposed_outcomes)

    current_median = _percentile(current_sorted, 50)
    proposed_median = _percentile(proposed_sorted, 50)
    best_case = _percentile(proposed_sorted, 90)
    worst_case = _percentile(proposed_sorted, 10)

    improvement_value = proposed_median - current_median
    improvement_pct = (improvement_value / current_median * 100) if current_median > 0 else 0.0

    monthly_income = await _estimate_monthly_income(session, current_user)
    current_savings_rate = (base_sip / monthly_income * 100) if monthly_income > 0 else 0.0
    proposed_savings_rate = (proposed_sip / monthly_income * 100) if monthly_income > 0 else 0.0

    current_discretionary = max(0.0, monthly_income - (base_sip + 77000.0))
    proposed_discretionary = max(0.0, monthly_income - (proposed_sip + 77000.0))

    tradeoffs = [
        f"Monthly discretionary budget shifts from ₹{current_discretionary:,.0f} to ₹{proposed_discretionary:,.0f}.",
        f"Savings rate changes from {current_savings_rate:.1f}% to {proposed_savings_rate:.1f}%.",
    ]

    if proposed_sip > base_sip:
        tradeoffs.append("Higher SIP improves long-term upside but tightens short-term lifestyle flexibility.")
    elif proposed_sip < base_sip:
        tradeoffs.append("Lower SIP improves cashflow today but reduces projected wealth accumulation.")
    else:
        tradeoffs.append("Scenario keeps SIP unchanged; outcomes mostly reflect market variability.")

    histogram = _build_histogram(proposed_outcomes)

    return SimulatorRunResponse(
        scenario=payload.scenario,
        metrics={
            "expected_corpus": round(mean(proposed_outcomes), 2),
            "best_case_p90": round(best_case, 2),
            "worst_case_p10": round(worst_case, 2),
            "improvement_value": round(improvement_value, 2),
            "improvement_pct": round(improvement_pct, 1),
            "median": round(proposed_median, 2),
        },
        histogram=histogram,
        comparison={
            "current": {
                "sip": round(base_sip, 2),
                "savings_rate": round(current_savings_rate, 1),
                "corpus": round(current_median, 2),
            },
            "proposed": {
                "sip": round(proposed_sip, 2),
                "savings_rate": round(proposed_savings_rate, 1),
                "corpus": round(proposed_median, 2),
            },
        },
        tradeoffs=tradeoffs,
    )

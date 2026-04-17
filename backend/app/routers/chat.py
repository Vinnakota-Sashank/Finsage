"""
Chat router — conversational finance API with real transaction querying.
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

from app.config import get_settings
from app.database import get_session
from app.models.alert import Alert
from app.models.conversation import Conversation, Message
from app.models.goal import Goal
from app.models.transaction import Transaction
from app.models.user import User
from app.services.gemini_tools import FUNCTION_TO_INTENT, get_chat_plan_with_gemini

router = APIRouter(prefix="/chat", tags=["chat"])
settings = get_settings()
optional_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login", auto_error=False)

FOOD_CATEGORIES = ["food_delivery", "dining_out", "groceries"]
CATEGORY_ALIASES = {
    "rent": "rent",
    "food": "food",
    "groceries": "groceries",
    "dining": "dining_out",
    "shopping": "shopping",
    "transport": "transport",
    "utilities": "utilities",
    "emi": "emi_student_loan",
    "sip": "sip_mutual_funds",
    "entertainment": "entertainment",
}
CATEGORY_LABELS = {
    "food_delivery": "Food Delivery",
    "dining_out": "Dining Out",
    "groceries": "Groceries",
    "rent": "Rent",
    "shopping": "Shopping",
    "transport": "Transport",
    "utilities": "Utilities",
    "emi_student_loan": "EMI",
    "sip_mutual_funds": "SIP",
    "entertainment": "Entertainment",
}


class ChatMessageRequest(SQLModel):
    message: str
    conversation_id: Optional[int] = None


class ChatMessagePayload(SQLModel):
    role: str
    content: str
    chart_type: Optional[str] = None
    chart_data: Any = None
    suggestions: list[str] = []


class ChatMessageResponse(SQLModel):
    conversation_id: int
    assistant: ChatMessagePayload


class ConversationMessagesResponse(SQLModel):
    conversation_id: int
    messages: list[ChatMessagePayload]


class ChatHealthResponse(SQLModel):
    ready: bool
    gemini_configured: bool
    mode: str
    function_calling_enabled: bool
    tool_chain_size: int


def _month_start(dt: datetime) -> datetime:
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _shift_month(month_start: datetime, offset: int) -> datetime:
    month_index = month_start.month - 1 + offset
    year = month_start.year + (month_index // 12)
    month = (month_index % 12) + 1
    return month_start.replace(year=year, month=month, day=1)


def _format_currency(amount: float) -> str:
    return f"₹{amount:,.0f}"


def _to_json(value: Any) -> Optional[str]:
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False)


def _from_json(value: Optional[str]) -> Any:
    if not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def _extract_category(message: str) -> Optional[str]:
    lowered = message.lower()
    for keyword, category in CATEGORY_ALIASES.items():
        if keyword in lowered:
            return category
    return None


def _title_from_message(message: str) -> str:
    normalized = " ".join(message.strip().split())
    return normalized[:80] if normalized else "New Conversation"


def _months_between(from_date: date, to_date: date) -> int:
    delta = (to_date.year - from_date.year) * 12 + (to_date.month - from_date.month)
    return max(1, delta)


def _extract_rupee_amount(message: str) -> Optional[float]:
    matches = re.findall(r"(?:₹|inr)?\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(k|l|lakhs?|m)?", message.lower())
    if not matches:
        return None

    raw_number, suffix = matches[-1]
    value = float(raw_number.replace(",", ""))
    if suffix in {"k"}:
        value *= 1000
    elif suffix in {"l", "lakh", "lakhs"}:
        value *= 100000
    elif suffix in {"m"}:
        value *= 1000000
    return value


async def get_chat_user(
    token: str | None = Depends(optional_oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    """
    Return authenticated user if token exists.
    In non-production, fallback to first user for demo velocity.
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


async def _get_or_create_conversation(
    session: AsyncSession,
    user_id: int,
    message: str,
    conversation_id: Optional[int],
) -> Conversation:
    if conversation_id:
        result = await session.execute(
            select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user_id)
        )
        conversation = result.scalar_one_or_none()
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        conversation.updated_at = datetime.utcnow()
        return conversation

    conversation = Conversation(
        user_id=user_id,
        title=_title_from_message(message),
    )
    session.add(conversation)
    await session.flush()
    return conversation


async def _get_last_user_message(
    session: AsyncSession,
    conversation_id: int,
) -> Optional[str]:
    result = await session.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id, Message.role == "user")
        .order_by(Message.created_at.desc())
        .limit(1)
    )
    msg = result.scalars().first()
    return msg.content if msg else None


async def _query_category_total(
    session: AsyncSession,
    user_id: int,
    start_date: datetime,
    end_date: datetime,
    category: str,
) -> float:
    result = await session.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "debit",
            Transaction.timestamp >= start_date,
            Transaction.timestamp < end_date,
            Transaction.category == category,
        )
    )
    return float(result.scalar() or 0)


async def _query_food_breakdown(
    session: AsyncSession,
    user_id: int,
    start_date: datetime,
    end_date: datetime,
) -> list[dict[str, float | str]]:
    result = await session.execute(
        select(
            Transaction.category,
            func.sum(Transaction.amount).label("total"),
        )
        .where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "debit",
            Transaction.timestamp >= start_date,
            Transaction.timestamp < end_date,
            Transaction.category.in_(FOOD_CATEGORIES),
        )
        .group_by(Transaction.category)
        .order_by(func.sum(Transaction.amount).desc())
    )
    rows = result.all()

    return [
        {
            "name": CATEGORY_LABELS.get(r.category, r.category.replace("_", " ").title()),
            "value": round(float(r.total), 2),
        }
        for r in rows
    ]


async def _query_top_categories(
    session: AsyncSession,
    user_id: int,
    start_date: datetime,
    end_date: datetime,
    limit: int = 6,
) -> list[dict[str, float | str]]:
    result = await session.execute(
        select(
            Transaction.category,
            func.sum(Transaction.amount).label("total"),
        )
        .where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "debit",
            Transaction.timestamp >= start_date,
            Transaction.timestamp < end_date,
        )
        .group_by(Transaction.category)
        .order_by(func.sum(Transaction.amount).desc())
        .limit(limit)
    )
    rows = result.all()

    return [
        {
            "name": CATEGORY_LABELS.get(r.category, r.category.replace("_", " ").title()),
            "value": round(float(r.total), 2),
        }
        for r in rows
    ]


async def _query_spending_trend(
    session: AsyncSession,
    user_id: int,
    now: datetime,
    months: int = 6,
) -> list[dict[str, float | str]]:
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
        {
            "month": month_start.strftime("%b"),
            "amount": round(totals.get((month_start.year, month_start.month), 0.0), 2),
        }
        for month_start in month_starts
    ]


async def _query_recent_alerts(
    session: AsyncSession,
    user_id: int,
    limit: int = 3,
) -> list[Alert]:
    result = await session.execute(
        select(Alert)
        .where(Alert.user_id == user_id)
        .order_by(Alert.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


async def _estimate_tax_remaining(
    session: AsyncSession,
    user: User,
    now: datetime,
) -> dict[str, float]:
    fy_start_year = now.year if now.month >= 4 else now.year - 1
    fy_start = datetime(fy_start_year, 4, 1)

    sip_result = await session.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user.id,
            Transaction.transaction_type == "debit",
            Transaction.category == "sip_mutual_funds",
            Transaction.timestamp >= fy_start,
            Transaction.timestamp <= now,
        )
    )
    health_result = await session.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user.id,
            Transaction.transaction_type == "debit",
            Transaction.category == "health",
            Transaction.timestamp >= fy_start,
            Transaction.timestamp <= now,
        )
    )

    months_elapsed = _months_between(fy_start.date(), now.date())
    epf_component = min(86400.0, months_elapsed * 7200.0)
    sip_total = float(sip_result.scalar() or 0)
    elss_component = min(50000.0, sip_total * 0.2)
    ppf_component = 24000.0

    section80c_limit = 150000.0
    section80c_used = min(section80c_limit, epf_component + elss_component + ppf_component)
    section80c_remaining = max(0.0, section80c_limit - section80c_used)

    section80d_limit = 25000.0
    section80d_used = min(section80d_limit, float(health_result.scalar() or 0))
    section80d_remaining = max(0.0, section80d_limit - section80d_used)

    return {
        "section80c_used": round(section80c_used, 2),
        "section80c_remaining": round(section80c_remaining, 2),
        "section80d_used": round(section80d_used, 2),
        "section80d_remaining": round(section80d_remaining, 2),
    }


async def _avg_monthly_savings(
    session: AsyncSession,
    user: User,
    now: datetime,
) -> float:
    lookback_start = _shift_month(_month_start(now), -3)

    income_result = await session.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user.id,
            Transaction.transaction_type == "credit",
            Transaction.timestamp >= lookback_start,
            Transaction.timestamp < _month_start(now),
        )
    )
    spending_result = await session.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user.id,
            Transaction.transaction_type == "debit",
            Transaction.timestamp >= lookback_start,
            Transaction.timestamp < _month_start(now),
        )
    )

    income = float(income_result.scalar() or 0)
    spending = float(spending_result.scalar() or 0)
    savings = (income - spending) / 3

    if savings <= 0:
        if user.monthly_income and user.monthly_income > 0:
            return round(user.monthly_income * 0.15, 2)
        return 5000.0

    return round(savings, 2)


def _build_trajectory_data(
    current_amount: float,
    target_amount: float,
    projected_final: float,
    months_remaining: int,
) -> list[dict[str, float | str]]:
    now_month = _month_start(datetime.utcnow())
    points = [0]
    if months_remaining >= 2:
        midpoint = max(1, months_remaining // 2)
        points.append(midpoint)
    points.append(months_remaining)
    points = sorted(set(points))

    chart_data: list[dict[str, float | str]] = []
    for month_offset in points:
        pct = month_offset / months_remaining if months_remaining > 0 else 1
        expected = current_amount + ((projected_final - current_amount) * pct)
        point_month = _shift_month(now_month, month_offset)
        chart_data.append(
            {
                "month": point_month.strftime("%b"),
                "actual": round(expected, 2),
                "target": round(target_amount, 2),
            }
        )

    return chart_data


def _detect_intent(message: str, previous_user_message: Optional[str]) -> str:
    lowered = message.lower()

    if any(token in lowered for token in ["where does my money go", "top categories", "top spending"]):
        return "top_categories"

    if "trend" in lowered and any(token in lowered for token in ["spend", "spending", "food"]):
        return "spending_trend"

    if any(token in lowered for token in ["alert", "anomaly", "unusual"]):
        return "alert_summary"

    if any(token in lowered for token in ["tax", "80c", "80d", "deduction"]):
        return "tax_summary"

    if ("what if" in lowered or "increase" in lowered) and any(token in lowered for token in ["save", "savings"]):
        return "goal_what_if"

    if "compare" in lowered or "last month" in lowered:
        if "food" in lowered:
            return "food_compare"
        if previous_user_message and "food" in previous_user_message.lower():
            return "food_compare"

    if any(token in lowered for token in ["goa", "on track", "goal track", "goal", "trip savings"]):
        return "goal_track"

    if "food" in lowered and any(token in lowered for token in ["how much", "spend", "this month"]):
        return "food_spend"

    if "spend" in lowered and "month" in lowered:
        return "category_spend"

    return "summary"


def _select_chart_type(
    intent: str,
    default_chart: Optional[str],
    preferred_chart: Optional[str],
) -> Optional[str]:
    allowed_by_intent = {
        "food_spend": {"donut"},
        "top_categories": {"donut"},
        "food_compare": {"bar"},
        "spending_trend": {"line"},
        "goal_track": {"trajectory"},
        "goal_what_if": {"trajectory"},
    }

    allowed = allowed_by_intent.get(intent)
    if not allowed:
        return None

    preferred = (preferred_chart or "").lower().strip()
    if preferred in allowed:
        return preferred

    if default_chart in allowed:
        return default_chart

    return next(iter(allowed))


def _resolve_intent_and_chart(
    message: str,
    previous_user_message: Optional[str],
) -> tuple[str, Optional[str]]:
    fallback_intent = _detect_intent(message, previous_user_message)
    preferred_chart: Optional[str] = None

    plan = get_chat_plan_with_gemini(message, previous_user_message)
    if not plan:
        return fallback_intent, preferred_chart

    confidence = float(plan.get("confidence", 0.0))
    if confidence < 0.35:
        return fallback_intent, preferred_chart

    resolved_intent = str(plan.get("intent", fallback_intent)) or fallback_intent
    chart_type = str(plan.get("chart_type", "")).strip().lower()
    preferred_chart = None if chart_type in {"", "none"} else chart_type

    return resolved_intent, preferred_chart


def _polish_with_gemini(base_text: str, user_message: str, facts: dict[str, Any]) -> str:
    if not settings.gemini_api_key:
        return base_text

    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = (
            "You are FinSage, a concise personal finance assistant. "
            "Rewrite the answer in <= 70 words, keep numeric facts exact, use INR format, "
            "and avoid markdown lists.\n"
            f"User question: {user_message}\n"
            f"Facts JSON: {json.dumps(facts, ensure_ascii=False)}\n"
            f"Draft answer: {base_text}"
        )
        result = model.generate_content(prompt)
        polished = (result.text or "").strip()
        return polished if polished else base_text
    except Exception:
        return base_text


async def _build_assistant_payload(
    session: AsyncSession,
    user: User,
    message: str,
    previous_user_message: Optional[str],
) -> ChatMessagePayload:
    now = datetime.utcnow()
    current_month_start = _month_start(now)
    next_month_start = _shift_month(current_month_start, 1)
    last_month_start = _shift_month(current_month_start, -1)

    intent, preferred_chart = _resolve_intent_and_chart(message, previous_user_message)

    if intent == "top_categories":
        categories = await _query_top_categories(session, user.id, current_month_start, next_month_start)
        total = round(sum(float(item["value"]) for item in categories), 2)
        top_name = str(categories[0]["name"]) if categories else "N/A"

        content = (
            f"This month, your top spending categories total {_format_currency(total)}. "
            f"Highest category is {top_name}."
        )
        content = _polish_with_gemini(content, message, {"total": total, "categories": categories})

        return ChatMessagePayload(
            role="assistant",
            content=content,
            chart_type=_select_chart_type(intent, "donut", preferred_chart),
            chart_data=categories,
            suggestions=["Show spending trend", "Compare with last month", "Set category budgets"],
        )

    if intent == "spending_trend":
        trend = await _query_spending_trend(session, user.id, now, months=6)
        if not trend:
            return ChatMessagePayload(
                role="assistant",
                content="I do not have enough transactions yet to build a spending trend.",
                suggestions=["Show monthly summary", "How much food spend this month?"],
            )

        latest = trend[-1]["amount"]
        previous = trend[-2]["amount"] if len(trend) > 1 else latest
        delta_pct = ((latest - previous) / previous * 100) if previous else 0.0
        direction = "up" if delta_pct >= 0 else "down"

        content = (
            f"Here is your 6-month spending trend. Latest month is {_format_currency(float(latest))}, "
            f"{abs(delta_pct):.1f}% {direction} versus previous month."
        )
        content = _polish_with_gemini(
            content,
            message,
            {"latest": latest, "previous": previous, "delta_pct": round(delta_pct, 1), "trend": trend},
        )

        return ChatMessagePayload(
            role="assistant",
            content=content,
            chart_type=_select_chart_type(intent, "line", preferred_chart),
            chart_data=trend,
            suggestions=["Show top categories", "How much did I save this month?", "Forecast next month"],
        )

    if intent == "alert_summary":
        alerts = await _query_recent_alerts(session, user.id, limit=3)
        unread_result = await session.execute(
            select(func.count(Alert.id)).where(Alert.user_id == user.id, Alert.is_read == False)
        )
        unread = int(unread_result.scalar() or 0)
        titles = [a.title for a in alerts]

        if not titles:
            content = "No recent alerts are active right now."
        else:
            content = f"You have {unread} unread alerts. Most recent: " + "; ".join(titles)

        content = _polish_with_gemini(content, message, {"unread": unread, "alerts": titles})

        return ChatMessagePayload(
            role="assistant",
            content=content,
            suggestions=["Show critical alerts", "How to reduce spending spikes?", "Open alerts page"],
        )

    if intent == "tax_summary":
        tax = await _estimate_tax_remaining(session, user, now)
        content = (
            f"Section 80C used {_format_currency(tax['section80c_used'])}, remaining {_format_currency(tax['section80c_remaining'])}. "
            f"Section 80D used {_format_currency(tax['section80d_used'])}, remaining {_format_currency(tax['section80d_remaining'])}."
        )
        content = _polish_with_gemini(content, message, tax)

        return ChatMessagePayload(
            role="assistant",
            content=content,
            suggestions=["Show full tax breakdown", "How much can I invest in ELSS?", "Check health insurance gap"],
        )

    if intent == "food_spend":
        breakdown = await _query_food_breakdown(session, user.id, current_month_start, next_month_start)
        total = round(sum(float(item["value"]) for item in breakdown), 2)

        if total == 0:
            content = "I couldn't find food transactions for this month yet."
            return ChatMessagePayload(role="assistant", content=content, suggestions=["Show my total monthly spend", "How much did I save this month?"])

        content = f"You spent {_format_currency(total)} on food this month. Here is the category breakdown from your real transactions."
        content = _polish_with_gemini(content, message, {"total": total, "breakdown": breakdown})

        return ChatMessagePayload(
            role="assistant",
            content=content,
            chart_type=_select_chart_type(intent, "donut", preferred_chart),
            chart_data=breakdown,
            suggestions=["Compare with last month", "Show 3-month trend", "Set food budget"],
        )

    if intent == "food_compare":
        current_breakdown = await _query_food_breakdown(session, user.id, current_month_start, next_month_start)
        last_breakdown = await _query_food_breakdown(session, user.id, last_month_start, current_month_start)

        current_map = {str(i["name"]): float(i["value"]) for i in current_breakdown}
        last_map = {str(i["name"]): float(i["value"]) for i in last_breakdown}
        labels = sorted(set(current_map.keys()) | set(last_map.keys()))

        chart_data = [
            {
                "cat": label,
                "this": round(current_map.get(label, 0.0), 2),
                "last": round(last_map.get(label, 0.0), 2),
            }
            for label in labels
        ]

        this_total = sum(item["this"] for item in chart_data)
        last_total = sum(item["last"] for item in chart_data)
        change_pct = ((this_total - last_total) / last_total * 100) if last_total > 0 else 0.0

        direction = "increased" if change_pct >= 0 else "decreased"
        content = (
            f"Food spending {direction} by {abs(change_pct):.1f}% month-over-month. "
            f"This month: {_format_currency(this_total)} vs last month: {_format_currency(last_total)}."
        )
        content = _polish_with_gemini(
            content,
            message,
            {"this_month_total": this_total, "last_month_total": last_total, "change_pct": round(change_pct, 1)},
        )

        return ChatMessagePayload(
            role="assistant",
            content=content,
            chart_type=_select_chart_type(intent, "bar", preferred_chart),
            chart_data=chart_data,
            suggestions=["Why did food increase?", "Forecast next month", "Show all categories"],
        )

    if intent in {"goal_track", "goal_what_if"}:
        goals_result = await session.execute(
            select(Goal)
            .where(Goal.user_id == user.id, Goal.status == "active")
            .order_by(Goal.deadline)
        )
        goals = goals_result.scalars().all()

        if not goals:
            return ChatMessagePayload(
                role="assistant",
                content="I couldn't find active goals yet. Add a goal first and I can track progress in chat.",
                suggestions=["Show spending summary", "How much did I save this month?"],
            )

        goal = next((g for g in goals if "goa" in g.name.lower()), goals[0])
        months_remaining = _months_between(now.date(), goal.deadline)
        avg_savings = await _avg_monthly_savings(session, user, now)

        extra_save = 0.0
        if intent == "goal_what_if":
            parsed = _extract_rupee_amount(message)
            if parsed and parsed <= 100000:
                extra_save = parsed

        adjusted_savings = avg_savings + extra_save
        projected = round(goal.current_amount + (adjusted_savings * months_remaining), 2)
        pct = round((goal.current_amount / goal.target_amount) * 100, 1) if goal.target_amount > 0 else 0.0
        shortfall = max(0.0, round(goal.target_amount - projected, 2))

        trajectory = _build_trajectory_data(
            current_amount=goal.current_amount,
            target_amount=goal.target_amount,
            projected_final=projected,
            months_remaining=months_remaining,
        )

        if shortfall > 0:
            content = (
                f"{goal.name}: {_format_currency(goal.current_amount)} saved of {_format_currency(goal.target_amount)} ({pct}%). "
                f"At your recent savings pace, you are projected at {_format_currency(projected)} by the deadline, "
                f"which is {_format_currency(shortfall)} short."
            )
        else:
            buffer = projected - goal.target_amount
            content = (
                f"{goal.name}: {_format_currency(goal.current_amount)} saved of {_format_currency(goal.target_amount)} ({pct}%). "
                f"You are on track to reach about {_format_currency(projected)} by the deadline, "
                f"roughly {_format_currency(buffer)} above target."
            )

        content = _polish_with_gemini(
            content,
            message,
            {
                "goal": goal.name,
                "current": goal.current_amount,
                "target": goal.target_amount,
                "projected": projected,
                "shortfall": shortfall,
                "months_remaining": months_remaining,
                "extra_monthly_saving": extra_save,
            },
        )

        return ChatMessagePayload(
            role="assistant",
            content=content,
            chart_type=_select_chart_type(intent, "trajectory", preferred_chart),
            chart_data=trajectory,
            suggestions=["What if I save 5k more?", "Show all goals", "How much can I cut from spending?"],
        )

    if intent == "category_spend":
        category = _extract_category(message)

        if category == "food":
            return await _build_assistant_payload(session, user, "how much food spend this month", previous_user_message)

        if category:
            total = await _query_category_total(
                session=session,
                user_id=user.id,
                start_date=current_month_start,
                end_date=next_month_start,
                category=category,
            )
            label = CATEGORY_LABELS.get(category, category.replace("_", " ").title())
            content = f"You spent {_format_currency(total)} on {label} this month based on your transaction ledger."
            content = _polish_with_gemini(content, message, {"category": label, "total": total})
            return ChatMessagePayload(
                role="assistant",
                content=content,
                suggestions=["Compare with last month", "Show top spending categories", "How much did I save this month?"],
            )

    income_result = await session.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user.id,
            Transaction.transaction_type == "credit",
            Transaction.timestamp >= current_month_start,
            Transaction.timestamp < next_month_start,
        )
    )
    spending_result = await session.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user.id,
            Transaction.transaction_type == "debit",
            Transaction.timestamp >= current_month_start,
            Transaction.timestamp < next_month_start,
        )
    )

    income = float(income_result.scalar() or 0)
    spending = float(spending_result.scalar() or 0)
    savings = income - spending
    savings_rate = (savings / income * 100) if income > 0 else 0.0

    content = (
        f"This month so far: income {_format_currency(income)}, spending {_format_currency(spending)}, "
        f"estimated savings {_format_currency(savings)} ({savings_rate:.1f}% savings rate)."
    )
    content = _polish_with_gemini(
        content,
        message,
        {"income": income, "spending": spending, "savings": savings, "savings_rate": round(savings_rate, 1)},
    )

    return ChatMessagePayload(
        role="assistant",
        content=content,
        suggestions=["How much did I spend on food this month?", "Compare food with last month", "Am I on track for Goa trip?"],
    )


@router.get("/health", response_model=ChatHealthResponse)
async def chat_health() -> ChatHealthResponse:
    """Quick check for chat subsystem readiness and Gemini mode."""
    return ChatHealthResponse(
        ready=True,
        gemini_configured=bool(settings.gemini_api_key),
        mode="gemini" if settings.gemini_api_key else "rule-based",
        function_calling_enabled=bool(settings.gemini_api_key),
        tool_chain_size=len(FUNCTION_TO_INTENT),
    )


@router.post("/message", response_model=ChatMessageResponse)
async def send_chat_message(
    payload: ChatMessageRequest,
    current_user: User = Depends(get_chat_user),
    session: AsyncSession = Depends(get_session),
) -> ChatMessageResponse:
    """Process a user message and return a transaction-aware assistant response."""
    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    conversation = await _get_or_create_conversation(
        session=session,
        user_id=current_user.id,
        message=message,
        conversation_id=payload.conversation_id,
    )

    previous_user_message = await _get_last_user_message(session, conversation.id)

    user_msg = Message(
        conversation_id=conversation.id,
        role="user",
        content=message,
    )
    session.add(user_msg)

    assistant_payload = await _build_assistant_payload(
        session=session,
        user=current_user,
        message=message,
        previous_user_message=previous_user_message,
    )

    assistant_msg = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=assistant_payload.content,
        chart_type=assistant_payload.chart_type,
        chart_data_json=_to_json(assistant_payload.chart_data),
        suggestions_json=_to_json(assistant_payload.suggestions),
    )
    session.add(assistant_msg)

    conversation.updated_at = datetime.utcnow()
    await session.commit()

    return ChatMessageResponse(conversation_id=conversation.id, assistant=assistant_payload)


@router.get("/conversations/{conversation_id}/messages", response_model=ConversationMessagesResponse)
async def get_conversation_messages(
    conversation_id: int,
    limit: int = Query(default=100, ge=1, le=300),
    current_user: User = Depends(get_chat_user),
    session: AsyncSession = Depends(get_session),
) -> ConversationMessagesResponse:
    """Fetch persisted messages for a conversation."""
    conv_result = await session.execute(
        select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
    )
    conversation = conv_result.scalar_one_or_none()
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    result = await session.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .limit(limit)
    )
    rows = result.scalars().all()

    messages = [
        ChatMessagePayload(
            role=row.role,
            content=row.content,
            chart_type=row.chart_type,
            chart_data=_from_json(row.chart_data_json),
            suggestions=_from_json(row.suggestions_json) or [],
        )
        for row in rows
    ]

    return ConversationMessagesResponse(conversation_id=conversation_id, messages=messages)

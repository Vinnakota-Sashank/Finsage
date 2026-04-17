"""
Gemini tools service — lightweight planner for chat intent and chart selection.
"""

from __future__ import annotations

import json
import re
from typing import Optional, TypedDict

from app.config import get_settings

settings = get_settings()


class ChatPlan(TypedDict, total=False):
    intent: str
    chart_type: str
    confidence: float


ALLOWED_INTENTS = {
    "top_categories",
    "spending_trend",
    "alert_summary",
    "tax_summary",
    "goal_what_if",
    "food_spend",
    "food_compare",
    "goal_track",
    "category_spend",
    "summary",
}

ALLOWED_CHART_TYPES = {"none", "donut", "bar", "line", "trajectory"}

# Core tool-chain: first 5 data queries for agentic chat routing.
QUERY_FUNCTION_DECLARATIONS = [
    {
        "name": "get_top_categories",
        "description": "Return the highest spending categories for the current month.",
        "parameters": {
            "type": "object",
            "properties": {
                "confidence": {
                    "type": "number",
                    "description": "Confidence score between 0 and 1",
                }
            },
        },
    },
    {
        "name": "get_spending_trend",
        "description": "Return month-over-month spending trend for recent months.",
        "parameters": {
            "type": "object",
            "properties": {
                "confidence": {
                    "type": "number",
                    "description": "Confidence score between 0 and 1",
                }
            },
        },
    },
    {
        "name": "get_alert_summary",
        "description": "Return current unread alerts and recent anomaly summaries.",
        "parameters": {
            "type": "object",
            "properties": {
                "confidence": {
                    "type": "number",
                    "description": "Confidence score between 0 and 1",
                }
            },
        },
    },
    {
        "name": "get_tax_summary",
        "description": "Return Indian tax optimization summary including 80C and 80D.",
        "parameters": {
            "type": "object",
            "properties": {
                "confidence": {
                    "type": "number",
                    "description": "Confidence score between 0 and 1",
                }
            },
        },
    },
    {
        "name": "get_goal_projection",
        "description": "Return goal progress and what-if savings projection.",
        "parameters": {
            "type": "object",
            "properties": {
                "confidence": {
                    "type": "number",
                    "description": "Confidence score between 0 and 1",
                }
            },
        },
    },
]

FUNCTION_TO_INTENT = {
    "get_top_categories": {"intent": "top_categories", "chart_type": "donut", "confidence": 0.88},
    "get_spending_trend": {"intent": "spending_trend", "chart_type": "line", "confidence": 0.88},
    "get_alert_summary": {"intent": "alert_summary", "chart_type": "none", "confidence": 0.85},
    "get_tax_summary": {"intent": "tax_summary", "chart_type": "none", "confidence": 0.84},
    "get_goal_projection": {"intent": "goal_what_if", "chart_type": "trajectory", "confidence": 0.82},
}


def _extract_json_block(text: str) -> Optional[str]:
    text = text.strip()
    if not text:
        return None

    if text.startswith("{") and text.endswith("}"):
        return text

    match = re.search(r"\{.*\}", text, re.DOTALL)
    return match.group(0) if match else None


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)  # type: ignore[arg-type]
    except Exception:
        return default


def _extract_tool_plan(result: object) -> Optional[ChatPlan]:
    """Extract function-call selection from Gemini tool response."""
    try:
        candidates = getattr(result, "candidates", None) or []
        for candidate in candidates:
            content = getattr(candidate, "content", None)
            parts = getattr(content, "parts", None) or []

            for part in parts:
                function_call = getattr(part, "function_call", None)
                if not function_call:
                    continue

                name = str(getattr(function_call, "name", "")).strip()
                mapped = FUNCTION_TO_INTENT.get(name)
                if not mapped:
                    continue

                confidence = float(mapped["confidence"])
                args = getattr(function_call, "args", None)
                if isinstance(args, dict):
                    confidence = _safe_float(args.get("confidence", confidence), confidence)
                elif hasattr(args, "items"):
                    try:
                        as_dict = dict(args.items())
                        confidence = _safe_float(as_dict.get("confidence", confidence), confidence)
                    except Exception:
                        pass

                confidence = max(0.0, min(1.0, confidence))
                return {
                    "intent": str(mapped["intent"]),
                    "chart_type": str(mapped["chart_type"]),
                    "confidence": confidence,
                }
    except Exception:
        return None

    return None


def _normalize_plan(parsed: dict) -> Optional[ChatPlan]:
    intent = str(parsed.get("intent", "")).strip().lower()
    chart_type = str(parsed.get("chart_type", "none")).strip().lower()

    if intent not in ALLOWED_INTENTS:
        return None
    if chart_type not in ALLOWED_CHART_TYPES:
        chart_type = "none"

    confidence = _safe_float(parsed.get("confidence", 0.0), 0.0)
    confidence = max(0.0, min(1.0, confidence))

    return {
        "intent": intent,
        "chart_type": chart_type,
        "confidence": confidence,
    }


def get_chat_plan_with_gemini(
    user_message: str,
    previous_user_message: str | None = None,
) -> Optional[ChatPlan]:
    """
    Ask Gemini to classify user intent and preferred chart type.
    Returns None on any failure so caller can fallback safely.
    """
    if not settings.gemini_api_key:
        return None

    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.gemini_api_key)

        # Try structured function calling first.
        try:
            tool_model = genai.GenerativeModel(
                "gemini-1.5-flash",
                tools=[{"function_declarations": QUERY_FUNCTION_DECLARATIONS}],
            )
            tool_result = tool_model.generate_content(
                (
                    "Select exactly one function that best matches the user's finance question. "
                    "Use higher confidence for clear matches and lower confidence for ambiguous requests.\n"
                    f"Previous user message: {previous_user_message or ''}\n"
                    f"Current user message: {user_message}"
                ),
                generation_config={
                    "temperature": 0.0,
                    "top_p": 0.9,
                    "max_output_tokens": 80,
                },
                tool_config={
                    "function_calling_config": {
                        "mode": "ANY",
                        "allowed_function_names": [decl["name"] for decl in QUERY_FUNCTION_DECLARATIONS],
                    }
                },
            )

            tool_plan = _extract_tool_plan(tool_result)
            if tool_plan:
                return tool_plan
        except Exception:
            # Keep fallback path active if function calling is unavailable.
            pass

        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = f"""
You are a financial assistant planner.
Classify the user query into one intent and one chart type.

Return ONLY strict JSON with keys:
- intent
- chart_type
- confidence

Allowed intents:
{sorted(ALLOWED_INTENTS)}

Allowed chart_type:
{sorted(ALLOWED_CHART_TYPES)}

Guidance:
- food breakdown -> food_spend + donut
- compare month-over-month -> food_compare + bar
- trend query -> spending_trend + line
- goal progress or what-if savings -> goal_track or goal_what_if + trajectory
- tax query -> tax_summary + none
- alerts/anomaly query -> alert_summary + none
- top categories / where money goes -> top_categories + donut
- generic category spend -> category_spend + none
- fallback -> summary + none

Previous user message:
{previous_user_message or ""}

Current user message:
{user_message}
""".strip()

        result = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.0,
                "top_p": 0.9,
                "max_output_tokens": 120,
            },
        )
        raw_text = (result.text or "").strip()
        json_text = _extract_json_block(raw_text)
        if not json_text:
            return None

        parsed = json.loads(json_text)
        if not isinstance(parsed, dict):
            return None

        return _normalize_plan(parsed)
    except Exception:
        return None

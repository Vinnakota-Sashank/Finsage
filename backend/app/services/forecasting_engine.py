"""
Forecasting engine service.
Uses Prophet when available, otherwise falls back to deterministic trend projection.
"""

from __future__ import annotations

import importlib
import math
from datetime import datetime
from typing import Any


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _heuristic_forecast(
    historical: list[dict[str, Any]],
    forecast_months: int,
) -> dict[str, Any]:
    values = [float(point.get("spend", 0.0) or 0.0) for point in historical]

    growth_rates: list[float] = []
    for prev, curr in zip(values[:-1], values[1:]):
        if prev > 0:
            growth_rates.append((curr - prev) / prev)

    avg_growth = sum(growth_rates) / len(growth_rates) if growth_rates else 0.03
    avg_growth = _clamp(avg_growth, -0.15, 0.15)

    volatility = _clamp(0.08 + (abs(avg_growth) * 0.5), 0.08, 0.25)
    last_value = values[-1] if values else 90000.0

    if historical and historical[-1].get("month_key"):
        current_month_start = datetime.strptime(str(historical[-1]["month_key"]), "%Y-%m-01")
    else:
        now = datetime.utcnow()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    forecast: list[dict[str, float | str]] = []
    projected = float(last_value)

    for step in range(1, forecast_months + 1):
        month_index = current_month_start.month - 1 + step
        year = current_month_start.year + (month_index // 12)
        month = (month_index % 12) + 1
        month_start = current_month_start.replace(year=year, month=month, day=1)

        projected = max(0.0, projected * (1 + avg_growth))
        upper = projected * (1 + volatility)
        lower = projected * (1 - volatility)

        forecast.append(
            {
                "month": month_start.strftime("%b"),
                "month_key": month_start.strftime("%Y-%m-01"),
                "forecast": round(projected, 2),
                "upper": round(upper, 2),
                "lower": round(lower, 2),
            }
        )

    return {
        "engine": "heuristic",
        "forecast": forecast,
        "avg_growth_pct": round(avg_growth * 100, 1),
        "confidence_band_pct": round(volatility * 100, 1),
    }


def _prophet_forecast(
    historical: list[dict[str, Any]],
    forecast_months: int,
) -> dict[str, Any] | None:
    if len(historical) < 4:
        return None

    try:
        pd = importlib.import_module("pandas")
        prophet_module = importlib.import_module("prophet")
        Prophet = getattr(prophet_module, "Prophet")
    except Exception:
        return None

    records = []
    for point in historical:
        month_key = point.get("month_key")
        spend = point.get("spend")
        if not month_key or spend is None:
            continue

        records.append({"ds": str(month_key), "y": float(spend)})

    if len(records) < 4:
        return None

    try:
        df = pd.DataFrame(records)
        df["ds"] = pd.to_datetime(df["ds"])

        history_len = len(records)
        use_yearly = history_len >= 18

        model = Prophet(
            interval_width=0.8,
            yearly_seasonality=use_yearly,
            weekly_seasonality=False,
            daily_seasonality=False,
            seasonality_mode="additive",
            changepoint_prior_scale=0.08,
        )
        model.fit(df)

        future = model.make_future_dataframe(periods=forecast_months, freq="MS", include_history=True)
        pred = model.predict(future)

        tail = pred.tail(forecast_months)
        forecast: list[dict[str, float | str]] = []

        for _, row in tail.iterrows():
            ds = row["ds"]
            yhat = max(0.0, float(row["yhat"]))
            upper = max(yhat, float(row["yhat_upper"]))
            lower = max(0.0, min(yhat, float(row["yhat_lower"])))
            forecast.append(
                {
                    "month": ds.strftime("%b"),
                    "month_key": ds.strftime("%Y-%m-01"),
                    "forecast": round(yhat, 2),
                    "upper": round(upper, 2),
                    "lower": round(lower, 2),
                }
            )

        # Guard against unstable Prophet fits on short/noisy histories.
        historical_values = [float(point.get("spend", 0.0) or 0.0) for point in historical]
        forecast_values = [float(item["forecast"]) for item in forecast]
        if not forecast_values:
            return None

        if any((not math.isfinite(v)) for v in forecast_values):
            return None

        hist_non_zero = [v for v in historical_values if v > 0]
        if hist_non_zero:
            hist_avg = sum(hist_non_zero) / len(hist_non_zero)
            first_forecast = forecast_values[0]

            # Reject explosive or collapsed projections and let heuristic fallback handle it.
            if first_forecast > hist_avg * 3.0 or first_forecast < hist_avg * 0.2:
                return None

        growth_rates: list[float] = []
        forecast_values = [float(item["forecast"]) for item in forecast]
        for prev, curr in zip(forecast_values[:-1], forecast_values[1:]):
            if prev > 0:
                growth_rates.append((curr - prev) / prev)

        avg_growth = sum(growth_rates) / len(growth_rates) if growth_rates else 0.0

        rel_band_values = []
        for item in forecast:
            center = float(item["forecast"])
            if center > 0:
                rel_band_values.append((float(item["upper"]) - float(item["lower"])) / (2 * center))
        rel_band = sum(rel_band_values) / len(rel_band_values) if rel_band_values else 0.1

        return {
            "engine": "prophet",
            "forecast": forecast,
            "avg_growth_pct": round(avg_growth * 100, 1),
            "confidence_band_pct": round(_clamp(rel_band * 100, 3.0, 30.0), 1),
        }
    except Exception:
        return None


def forecast_spending_with_engine(
    historical: list[dict[str, Any]],
    forecast_months: int,
) -> dict[str, Any]:
    """Return spending forecast using Prophet when available, else deterministic fallback."""
    prophet_result = _prophet_forecast(historical, forecast_months)
    if prophet_result:
        return prophet_result

    return _heuristic_forecast(historical, forecast_months)

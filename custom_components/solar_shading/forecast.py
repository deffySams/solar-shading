"""Forecast helpers for pre-emptive shading policy."""

from __future__ import annotations

from datetime import datetime, time
from typing import Any

import numpy as np

from .weather import normalized_cloud_coverage


def extract_daily_forecast_summary(
    forecast_list: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    """Extract a compact summary from a daily forecast list."""
    if not forecast_list:
        return {}

    today = forecast_list[0] if len(forecast_list) > 0 else {}
    tomorrow = forecast_list[1] if len(forecast_list) > 1 else {}

    return {
        "today_condition": today.get("condition"),
        "today_max_temp": today.get("temperature"),
        "today_cloud_coverage": normalized_cloud_coverage(
            today.get("cloud_coverage"), today.get("condition")
        ),
        "today_precipitation_probability": today.get("precipitation_probability"),
        "today_precipitation_amount": today.get("precipitation"),
        "today_uv_index": today.get("uv_index"),
        "tomorrow_max_temp": tomorrow.get("temperature"),
    }


def temperature_risk(
    temperature: float | None, hot_threshold: float | None, very_hot_threshold: float | None
) -> float:
    """Map forecast temperature into a 0..1 risk scale."""
    if temperature is None or hot_threshold is None:
        return 0.0
    if very_hot_threshold is None or very_hot_threshold <= hot_threshold:
        return float(temperature >= hot_threshold)
    return float(
        np.clip(
            (float(temperature) - float(hot_threshold))
            / (float(very_hot_threshold) - float(hot_threshold)),
            0.0,
            1.0,
        )
    )


def uv_risk(uv_index: float | None) -> float:
    """Return a 0..1 UV risk proxy."""
    if uv_index is None:
        return 0.0
    return float(np.clip(float(uv_index) / 8.0, 0.0, 1.0))


def precipitation_probability_damping(probability: float | None) -> float:
    """Return a 0..1 damping factor from precipitation probability."""
    if probability is None:
        return 1.0
    return float(np.clip(1.0 - (float(probability) / 100.0), 0.0, 1.0))


def precipitation_amount_damping(amount: float | None) -> float:
    """Return a 0..1 damping factor from expected precipitation amount."""
    if amount is None:
        return 1.0
    return float(np.clip(1.0 - (float(amount) / 10.0), 0.0, 1.0))


def parse_time_or_none(value: str | None) -> time | None:
    """Parse an optional HH:MM:SS string."""
    if not value:
        return None
    return time.fromisoformat(value)


def after_preemptive_start(now: datetime, start_time: str | None) -> bool:
    """Return whether the current local time is after the configured start."""
    parsed = parse_time_or_none(start_time)
    if parsed is None:
        return True
    return now.time() >= parsed

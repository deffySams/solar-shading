"""Open-data solar radiation helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import numpy as np
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
DNI_REFERENCE_W_M2 = 900.0
GHI_REFERENCE_W_M2 = 800.0


def radiation_factor(
    value: float | None,
    *,
    direct_normal: bool = True,
    reference: float | None = None,
) -> float:
    """Normalize irradiance in W/m2 into a 0..1 heat-gain factor."""
    if value is None:
        return 0.0
    default_reference = DNI_REFERENCE_W_M2 if direct_normal else GHI_REFERENCE_W_M2
    reference_value = float(reference or default_reference)
    if reference_value <= 0:
        reference_value = default_reference
    return float(np.clip(float(value) / reference_value, 0.0, 1.0))


def _float_or_none(value: Any) -> float | None:
    """Return a float or None for absent API values."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _max_or_none(values: list[Any]) -> float | None:
    """Return the maximum numeric value from a list."""
    numbers = [_float_or_none(value) for value in values]
    numbers = [value for value in numbers if value is not None]
    if not numbers:
        return None
    return max(numbers)


async def async_fetch_open_meteo_solar_summary(
    hass: HomeAssistant,
    latitude: float,
    longitude: float,
) -> dict[str, Any]:
    """Fetch a compact Open-Meteo solar radiation summary."""
    session = async_get_clientsession(hass)
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": ",".join(
            [
                "shortwave_radiation",
                "direct_radiation",
                "direct_normal_irradiance",
                "diffuse_radiation",
            ]
        ),
        "hourly": ",".join(
            [
                "shortwave_radiation",
                "direct_radiation",
                "direct_normal_irradiance",
                "diffuse_radiation",
            ]
        ),
        "daily": "shortwave_radiation_sum",
        "timezone": hass.config.time_zone or "auto",
        "forecast_days": 2,
    }

    async with session.get(OPEN_METEO_FORECAST_URL, params=params, timeout=10) as resp:
        resp.raise_for_status()
        data = await resp.json()

    current = data.get("current") or {}
    hourly = data.get("hourly") or {}
    daily = data.get("daily") or {}
    hourly_times = hourly.get("time") or []
    now = datetime.now().date()
    today_indexes = [
        index
        for index, value in enumerate(hourly_times)
        if isinstance(value, str) and datetime.fromisoformat(value).date() == now
    ]

    def hourly_values(key: str) -> list[Any]:
        values = hourly.get(key) or []
        return [values[index] for index in today_indexes if index < len(values)]

    return {
        "source": "open_meteo",
        "current_shortwave_radiation": _float_or_none(
            current.get("shortwave_radiation")
        ),
        "current_direct_radiation": _float_or_none(current.get("direct_radiation")),
        "current_direct_normal_irradiance": _float_or_none(
            current.get("direct_normal_irradiance")
        ),
        "current_diffuse_radiation": _float_or_none(current.get("diffuse_radiation")),
        "today_max_shortwave_radiation": _max_or_none(
            hourly_values("shortwave_radiation")
        ),
        "today_max_direct_normal_irradiance": _max_or_none(
            hourly_values("direct_normal_irradiance")
        ),
        "today_shortwave_radiation_sum": (
            _float_or_none((daily.get("shortwave_radiation_sum") or [None])[0])
        ),
        "tomorrow_shortwave_radiation_sum": (
            _float_or_none((daily.get("shortwave_radiation_sum") or [None, None])[1])
            if len(daily.get("shortwave_radiation_sum") or []) > 1
            else None
        ),
    }

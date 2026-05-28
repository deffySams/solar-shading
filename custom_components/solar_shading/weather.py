"""Weather attenuation helpers for solar gain estimation."""

from __future__ import annotations


CONDITION_TO_CLOUD_COVERAGE = {
    "sunny": 0.0,
    "clear": 0.0,
    "clear-night": 0.0,
    "windy": 20.0,
    "partlycloudy": 50.0,
    "windy-variant": 60.0,
    "cloudy": 90.0,
    "fog": 100.0,
    "rainy": 100.0,
    "pouring": 100.0,
    "lightning": 100.0,
    "lightning-rainy": 100.0,
    "hail": 100.0,
    "snowy": 100.0,
    "snowy-rainy": 100.0,
    "exceptional": 100.0,
}

PRECIPITATION_CONDITIONS = {
    "rainy",
    "pouring",
    "lightning-rainy",
    "hail",
    "snowy",
    "snowy-rainy",
}


def _clamp_percent(value: float | None) -> float | None:
    """Clamp an optional percentage to the supported range."""
    if value is None:
        return None
    return max(0.0, min(float(value), 100.0))


def normalized_cloud_coverage(
    cloud_coverage: float | None, condition: str | None
) -> float:
    """Return cloud coverage in percent, inferring it from condition if needed."""
    reported = _clamp_percent(cloud_coverage)
    if reported is not None:
        return reported
    return CONDITION_TO_CLOUD_COVERAGE.get(condition or "", 0.0)


def cloud_attenuation_factor(cloud_coverage: float | None, condition: str | None) -> float:
    """Return a linear attenuation factor based on cloud coverage."""
    coverage = normalized_cloud_coverage(cloud_coverage, condition)
    return max(0.0, min(1.0, 1.0 - (coverage / 100.0)))


def rain_attenuation_factor(
    condition: str | None, precipitation: float | None
) -> float:
    """Return a strong attenuation factor when precipitation is active."""
    if (condition or "") in PRECIPITATION_CONDITIONS:
        return 0.1
    if precipitation is not None and float(precipitation) > 0.0:
        return 0.1
    return 1.0


def weather_attenuation_factor(
    cloud_coverage: float | None,
    condition: str | None,
    precipitation: float | None,
) -> float:
    """Combine cloud and rain attenuation into a single factor."""
    return max(
        0.0,
        min(
            1.0,
            cloud_attenuation_factor(cloud_coverage, condition)
            * rain_attenuation_factor(condition, precipitation),
        ),
    )

"""Simple, explicit solar attenuation models for shading covers."""

from __future__ import annotations

from .const import (
    COVER_CLOSED_RESIDUAL_FACTORS,
    COVER_LOCATION_EXTERIOR,
)


def closed_cover_residual_factor(cover_location: str | None = None) -> float:
    """Return the solar-gain fraction remaining behind a fully closed cover."""
    return COVER_CLOSED_RESIDUAL_FACTORS.get(
        cover_location or COVER_LOCATION_EXTERIOR,
        COVER_CLOSED_RESIDUAL_FACTORS[COVER_LOCATION_EXTERIOR],
    )


def cover_transmission_factor(
    open_position: float | None,
    cover_location: str | None = None,
) -> float | None:
    """Interpolate from the closed residual factor to fully open."""
    if open_position is None:
        return None
    open_fraction = max(0.0, min(100.0, float(open_position))) / 100.0
    residual = closed_cover_residual_factor(cover_location)
    return residual + (1.0 - residual) * open_fraction


def estimate_power_with_cover(
    power_without_cover: float | None,
    open_position: float | None,
    cover_location: str | None = None,
) -> float | None:
    """Estimate room-side solar power after the selected cover model."""
    factor = cover_transmission_factor(open_position, cover_location)
    if power_without_cover is None or factor is None:
        return None
    return float(power_without_cover) * factor


def maximum_open_position_for_limit(
    power_without_cover: float | None,
    power_limit: float | None,
    cover_location: str | None = None,
) -> int | None:
    """Return the largest open percentage that can satisfy a power limit."""
    if power_without_cover is None or power_limit is None:
        return None
    power = float(power_without_cover)
    limit = float(power_limit)
    if power <= 0 or power <= limit:
        return None
    residual = closed_cover_residual_factor(cover_location)
    required_factor = limit / power
    if required_factor <= residual:
        return 0
    open_fraction = (required_factor - residual) / (1.0 - residual)
    return int(round(max(0.0, min(1.0, open_fraction)) * 100))

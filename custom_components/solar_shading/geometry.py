"""Geometry helpers for adaptive horizon and reveal shading."""

from __future__ import annotations

import json
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class HorizonPoint:
    """One support point in the local window horizon profile."""

    angle: float
    lower_elevation: float
    upper_elevation: float


def local_window_angle(gamma: float) -> float:
    """Convert surface-relative gamma to a local 0..180 window angle."""
    return float(np.clip(90 - gamma, 0, 180))


def parse_horizon_profile(value) -> list[HorizonPoint]:
    """Parse a horizon profile from stored config data."""
    if value in (None, "", []):
        return []

    profile = value
    if isinstance(value, str):
        profile = json.loads(value)

    points: list[HorizonPoint] = []
    for item in profile:
        angle = float(item["angle"])
        lower = float(item.get("lower_elevation", 0))
        upper = float(item.get("upper_elevation", 90))
        points.append(
            HorizonPoint(
                angle=max(0.0, min(359.0, angle)),
                lower_elevation=max(0.0, min(90.0, lower)),
                upper_elevation=max(0.0, min(90.0, upper)),
            )
        )

    return sorted(points, key=lambda point: point.angle)


def interpolate_horizon_elevations(
    local_angle: float, profile: list[HorizonPoint]
) -> tuple[float, float]:
    """Interpolate lower and upper horizon elevations for a local angle."""
    if not profile:
        return 0.0, 90.0

    if len(profile) == 1:
        point = profile[0]
        return point.lower_elevation, point.upper_elevation

    clamped_angle = max(0.0, min(180.0, local_angle))

    if clamped_angle <= profile[0].angle:
        point = profile[0]
        return point.lower_elevation, point.upper_elevation

    if clamped_angle >= profile[-1].angle:
        point = profile[-1]
        return point.lower_elevation, point.upper_elevation

    for left, right in zip(profile, profile[1:]):
        if left.angle <= clamped_angle <= right.angle:
            if np.isclose(left.angle, right.angle):
                return left.lower_elevation, left.upper_elevation

            ratio = (clamped_angle - left.angle) / (right.angle - left.angle)
            lower = left.lower_elevation + (
                right.lower_elevation - left.lower_elevation
            ) * ratio
            upper = left.upper_elevation + (
                right.upper_elevation - left.upper_elevation
            ) * ratio
            return lower, upper

    point = profile[-1]
    return point.lower_elevation, point.upper_elevation


def interpolate_compass_horizon_elevations(
    compass_azimuth: float, profile: list[HorizonPoint]
) -> tuple[float, float]:
    """Interpolate a cyclic 0..359 degree compass horizon profile."""
    if not profile:
        return 0.0, 90.0
    if len(profile) == 1:
        point = profile[0]
        return point.lower_elevation, point.upper_elevation

    angle = float(compass_azimuth) % 360.0
    cyclic = [*profile, HorizonPoint(
        angle=profile[0].angle + 360.0,
        lower_elevation=profile[0].lower_elevation,
        upper_elevation=profile[0].upper_elevation,
    )]
    if angle < profile[0].angle:
        angle += 360.0

    for left, right in zip(cyclic, cyclic[1:]):
        if left.angle <= angle <= right.angle:
            if np.isclose(left.angle, right.angle):
                return left.lower_elevation, left.upper_elevation
            ratio = (angle - left.angle) / (right.angle - left.angle)
            lower = left.lower_elevation + (
                right.lower_elevation - left.lower_elevation
            ) * ratio
            upper = left.upper_elevation + (
                right.upper_elevation - left.upper_elevation
            ) * ratio
            return lower, upper

    point = profile[-1]
    return point.lower_elevation, point.upper_elevation


def _safe_dimension(value: float | None) -> float | None:
    """Normalize optional dimensions used in geometry calculations."""
    if value is None:
        return None
    if value <= 0:
        return None
    return float(value)


def left_reveal_shadow_fraction(
    gamma: float, window_width: float | None, reveal_left_depth: float | None
) -> float:
    """Return the left reveal shading fraction."""
    width = _safe_dimension(window_width)
    depth = _safe_dimension(reveal_left_depth)
    if width is None or depth is None or gamma <= 0:
        return 0.0
    shadow = depth * np.tan(np.radians(min(abs(gamma), 89.9))) / width
    return float(np.clip(shadow, 0.0, 1.0))


def right_reveal_shadow_fraction(
    gamma: float, window_width: float | None, reveal_right_depth: float | None
) -> float:
    """Return the right reveal shading fraction."""
    width = _safe_dimension(window_width)
    depth = _safe_dimension(reveal_right_depth)
    if width is None or depth is None or gamma >= 0:
        return 0.0
    shadow = depth * np.tan(np.radians(min(abs(gamma), 89.9))) / width
    return float(np.clip(shadow, 0.0, 1.0))


def top_reveal_shadow_fraction(
    sun_elevation: float, window_height: float | None, reveal_top_depth: float | None
) -> float:
    """Return the top reveal shading fraction."""
    height = _safe_dimension(window_height)
    depth = _safe_dimension(reveal_top_depth)
    if height is None or depth is None or sun_elevation <= 0:
        return 0.0
    shadow = depth * np.tan(np.radians(min(sun_elevation, 89.9))) / height
    return float(np.clip(shadow, 0.0, 1.0))


def combined_reveal_shadow_fraction(side_shadow: float, top_shadow: float) -> float:
    """Combine independent reveal shadow fractions with simple overlap handling."""
    return float(np.clip(1 - (1 - side_shadow) * (1 - top_shadow), 0.0, 1.0))

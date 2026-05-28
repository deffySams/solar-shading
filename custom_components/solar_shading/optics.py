"""Optical helper functions for glazing-aware solar estimates."""

from __future__ import annotations

from dataclasses import dataclass
from math import acos, cos, degrees

import numpy as np
from numpy import radians as rad


@dataclass(frozen=True)
class GlassProfile:
    """Approximate optical coefficients for a glazing preset."""

    visible_transmittance: float
    solar_transmittance: float
    near_ir_transmittance: float
    visible_reflectance_normal: float
    solar_reflectance_normal: float
    near_ir_reflectance_normal: float


GLASS_PROFILES: dict[str, GlassProfile] = {
    "single_clear": GlassProfile(0.90, 0.86, 0.82, 0.08, 0.08, 0.07),
    "double_clear": GlassProfile(0.80, 0.70, 0.62, 0.14, 0.14, 0.16),
    "double_low_e": GlassProfile(0.72, 0.52, 0.38, 0.13, 0.28, 0.38),
    "triple_clear": GlassProfile(0.70, 0.60, 0.52, 0.19, 0.20, 0.22),
    "triple_low_e": GlassProfile(0.62, 0.42, 0.28, 0.18, 0.32, 0.48),
    "solar_control": GlassProfile(0.50, 0.30, 0.18, 0.22, 0.36, 0.50),
}

DEFAULT_GLASS_TYPE = "double_clear"


def glass_profile_for_type(glass_type: str | None) -> GlassProfile:
    """Return the configured glazing profile or the default preset."""
    return GLASS_PROFILES.get(
        glass_type or DEFAULT_GLASS_TYPE, GLASS_PROFILES[DEFAULT_GLASS_TYPE]
    )


def incidence_angle_from_gamma_elevation(gamma: float, sol_elev: float) -> float:
    """Return the solar incidence angle against the window normal."""
    cos_incidence = float(np.clip(cos(rad(sol_elev)) * cos(rad(gamma)), -1.0, 1.0))
    return degrees(acos(cos_incidence))


def incidence_cosine_from_angle(incidence_angle: float) -> float:
    """Return the front-facing cosine term of the incidence angle."""
    return float(np.clip(cos(rad(incidence_angle)), 0.0, 1.0))


def schlick_reflectance(normal_reflectance: float, incidence_angle: float) -> float:
    """Approximate angle-dependent reflectance from normal-incidence reflectance."""
    r0 = float(np.clip(normal_reflectance, 0.0, 1.0))
    cos_theta = incidence_cosine_from_angle(incidence_angle)
    reflectance = r0 + (1.0 - r0) * ((1.0 - cos_theta) ** 5)
    return float(np.clip(reflectance, 0.0, 1.0))


def angular_transmittance(
    normal_transmittance: float,
    normal_reflectance: float,
    incidence_angle: float,
) -> float:
    """Scale transmittance down as angle-driven reflectance rises."""
    t0 = float(np.clip(normal_transmittance, 0.0, 1.0))
    r0 = float(np.clip(normal_reflectance, 0.0, 1.0))
    r_theta = schlick_reflectance(r0, incidence_angle)
    remaining_normal = max(1.0 - r0, 1e-6)
    transmitted = t0 * ((1.0 - r_theta) / remaining_normal)
    return float(np.clip(transmitted, 0.0, 1.0))

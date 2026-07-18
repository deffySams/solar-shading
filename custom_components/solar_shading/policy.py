"""Heat-gain policy helpers for daylight-aware shading."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass(frozen=True)
class PolicyPreset:
    """Bias profile for the heat-gain policy."""

    score_multiplier: float
    threshold_shift: float
    position_offset: int
    weights: dict[str, float] = field(default_factory=dict)


POLICY_PRESETS: dict[str, PolicyPreset] = {
    "custom": PolicyPreset(1.0, 0.0, 0),
    "daylight_first_single_aspect": PolicyPreset(
        0.92,
        0.06,
        5,
        {
            "direct_exposure": 1.25,
            "incidence": 1.0,
            "glazing": 0.75,
            "solar_radiation": 1.1,
            "forecast_temperature": 0.7,
        },
    ),
    "daylight_first_multi_aspect": PolicyPreset(
        1.0,
        0.0,
        0,
        {
            "direct_exposure": 1.3,
            "incidence": 1.05,
            "glazing": 0.8,
            "solar_radiation": 1.1,
            "forecast_temperature": 0.85,
        },
    ),
    "balanced": PolicyPreset(
        1.08,
        -0.02,
        0,
        {
            "direct_exposure": 1.2,
            "incidence": 0.95,
            "glazing": 0.8,
            "solar_radiation": 1.15,
            "forecast_temperature": 1.0,
        },
    ),
    "cooling_first": PolicyPreset(
        1.16,
        -0.06,
        -5,
        {
            "direct_exposure": 1.35,
            "incidence": 1.1,
            "glazing": 0.75,
            "solar_radiation": 1.25,
            "forecast_temperature": 1.35,
        },
    ),
}


def clamp01(value: float) -> float:
    """Clamp a numeric value into 0..1."""
    return float(np.clip(value, 0.0, 1.0))


def clamp_component(value: float) -> float:
    """Clamp a policy component while allowing explicit boost signals."""
    return float(np.clip(value, 0.0, 2.0))


def preset_for_name(name: str | None) -> PolicyPreset:
    """Return a policy preset or the custom fallback."""
    if not name:
        return POLICY_PRESETS["custom"]
    return POLICY_PRESETS.get(name, POLICY_PRESETS["custom"])


def preset_weights_for_name(name: str | None) -> dict[str, float]:
    """Return configured default weights for a policy preset."""
    return dict(preset_for_name(name).weights)


def temperature_boost_signal(risk: float | None) -> float:
    """Return a neutral-to-hot forecast temperature signal.

    Below the hot-day threshold the value is neutral (1.0) instead of zero.
    This keeps forecast temperature from disabling otherwise valid physical
    heat gain. Above the threshold it can gently emphasize hotter days.
    """
    return 1.0 + clamp01(float(risk or 0.0))


def very_hot_policy_pressure(
    temperature_risk_value: float | None,
    forecast_strength: float | None,
) -> float:
    """Return how strongly very-hot forecast should tighten the policy.

    The hot-day threshold only enables heat protection. Very-hot pressure is
    the stricter layer above it and is scaled by forecast influence.
    """
    strength = clamp01(float(forecast_strength or 0.0) * 2.0)
    return clamp01(float(temperature_risk_value or 0.0)) * strength


def temperature_adjusted_thresholds(
    partial_threshold: float,
    full_threshold: float,
    pressure: float,
) -> tuple[float, float]:
    """Lower close thresholds on very-hot days."""
    reduction = 0.20 * clamp01(pressure)
    partial = clamp01(partial_threshold - reduction)
    full = clamp01(max(full_threshold - reduction, partial))
    return partial, full


def temperature_adjusted_positions(
    partial_position: int,
    full_position: int,
    pressure: float,
) -> tuple[int, int]:
    """Move the partial target toward the configured strict target on very-hot days."""
    offset = int(round(10 * clamp01(pressure)))
    full = int(np.clip(full_position, 0, 100))
    partial = int(np.clip(max(partial_position - offset, full), full, 100))
    return partial, full


def weighted_risk_score(components: dict[str, float | None], weights: dict[str, float]) -> float:
    """Return a weighted multiplicative score for all active components.

    A heat-gain model should collapse when a physically required factor is 0:
    no sun, blocked horizon, missing irradiance, grazing incidence, or opaque glazing
    must not be averaged away by unrelated forecast factors.
    """
    active_values: list[tuple[float, float]] = []
    weight_sum = 0.0

    for key, value in components.items():
        if value is None:
            continue
        weight = max(float(weights.get(key, 0.0) or 0.0), 0.0)
        if weight <= 0.0:
            continue
        active_values.append((clamp_component(float(value)), weight))
        weight_sum += weight

    if weight_sum <= 0.0:
        return 0.0

    score = 1.0
    for value, weight in active_values:
        score *= value ** (weight / weight_sum)

    return clamp01(score)


def gain_limited_policy_score(weighted_score: float, heat_gain_response: float) -> float:
    """Limit policy aggressiveness by the physical heat-gain response.

    Forecast and comfort weights may raise or lower the relative risk, but they
    must not invent heat when the window geometry, reflection, irradiance, or
    shading already reduce the physical solar gain to near zero.
    """
    return min(clamp01(weighted_score), clamp01(heat_gain_response))


def adjusted_policy_score(
    raw_score: float,
    preset_name: str | None,
    has_additional_daylight_windows: bool,
) -> float:
    """Return the preset-adjusted policy score."""
    preset = preset_for_name(preset_name)
    multiplier = preset.score_multiplier
    if has_additional_daylight_windows:
        multiplier *= 1.08
    return clamp01(raw_score * multiplier)


def adjusted_thresholds(
    partial_threshold: float,
    full_threshold: float,
    preset_name: str | None,
    has_additional_daylight_windows: bool,
) -> tuple[float, float]:
    """Return preset-adjusted partial and full thresholds."""
    preset = preset_for_name(preset_name)
    shift = preset.threshold_shift
    if has_additional_daylight_windows:
        shift -= 0.04

    partial = clamp01(float(partial_threshold) + shift)
    full = clamp01(float(full_threshold) + shift)
    if full < partial:
        full = partial
    return partial, full


def legacy_position_input_detected(
    partial_position: int,
    full_position: int,
) -> bool:
    """Return whether positions look like older closing-percentage inputs."""
    return int(full_position) > int(partial_position)


def normalize_policy_positions(
    partial_position: int,
    full_position: int,
) -> tuple[int, int]:
    """Return policy targets in the current % open notation.

    Older beta builds stored these as closing percentages where larger meant
    stricter shading. If full is larger than partial, interpret the pair as
    legacy values and convert them to Home Assistant open positions.
    """
    partial_base = int(partial_position)
    full_base = int(full_position)
    if legacy_position_input_detected(partial_base, full_base):
        partial_base = 100 - partial_base
        full_base = 100 - full_base
    return partial_base, full_base


def adjusted_positions(
    partial_position: int,
    full_position: int,
    preset_name: str | None,
    has_additional_daylight_windows: bool,
) -> tuple[int, int]:
    """Return preset-adjusted target open positions."""
    preset = preset_for_name(preset_name)
    offset = preset.position_offset
    if has_additional_daylight_windows:
        offset -= 5

    partial_base, full_base = normalize_policy_positions(
        partial_position,
        full_position,
    )

    full = int(np.clip(full_base, 0, 100))
    partial = int(np.clip(max(partial_base + offset, full), full, 100))
    return partial, full


def away_adjusted_score(
    score: float,
    away_active: bool,
    score_multiplier: float | None,
) -> float:
    """Return the score adjusted for away-from-home mode."""
    adjusted = clamp01(score)
    if away_active:
        adjusted *= float(score_multiplier or 1.0)
    return clamp01(adjusted)


def away_adjusted_thresholds(
    partial_threshold: float,
    full_threshold: float,
    away_active: bool,
    threshold_reduction: float | None,
) -> tuple[float, float]:
    """Return thresholds adjusted for away-from-home mode."""
    partial = clamp01(partial_threshold)
    full = clamp01(max(full_threshold, partial))
    if away_active:
        reduction = max(float(threshold_reduction or 0.0), 0.0)
        partial = clamp01(partial - reduction)
        full = clamp01(max(full - reduction, partial))
    return partial, full


def away_adjusted_positions(
    partial_position: int,
    full_position: int,
    away_active: bool,
    position_offset: int | None,
) -> tuple[int, int]:
    """Return positions adjusted for away-from-home mode."""
    full = int(np.clip(full_position, 0, 100))
    partial = int(np.clip(max(partial_position, full), full, 100))
    if away_active:
        offset = max(int(position_offset or 0), 0)
        partial = int(np.clip(max(partial - offset, full), full, 100))
    return partial, full


def policy_target_position(
    score: float,
    partial_threshold: float,
    full_threshold: float,
    partial_position: int,
    full_position: int,
) -> tuple[str, int | None]:
    """Return policy action level and target position."""
    score = clamp01(score)
    partial_threshold = clamp01(partial_threshold)
    full_threshold = clamp01(full_threshold)

    if score < partial_threshold:
        return "none", None

    if full_threshold <= partial_threshold:
        if score >= full_threshold:
            return "full", int(np.clip(full_position, 0, 100))
        return "partial", int(np.clip(partial_position, 0, 100))

    if score >= full_threshold:
        return "full", int(np.clip(full_position, 0, 100))

    progress = (score - partial_threshold) / (full_threshold - partial_threshold)
    target = int(
        round(
            np.interp(
                clamp01(progress),
                [0.0, 1.0],
                [int(partial_position), int(full_position)],
            )
        )
    )
    return "partial", int(np.clip(target, 0, 100))

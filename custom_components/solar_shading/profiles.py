"""Resolve house-profile inheritance for Solar Shading windows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .const import (
    CONF_AWAY_ENTITY,
    CONF_AWAY_POSITION_OFFSET,
    CONF_AWAY_SCORE_MULTIPLIER,
    CONF_AWAY_THRESHOLD_REDUCTION,
    CONF_AWNING_ANGLE,
    CONF_AZIMUTH,
    CONF_BINARY_CLOSE_POSITION,
    CONF_BINARY_CLOSE_THRESHOLD,
    CONF_BLIND_SPOT_ELEVATION,
    CONF_BLIND_SPOT_LEFT,
    CONF_BLIND_SPOT_RIGHT,
    CONF_DEFAULT_HEIGHT,
    CONF_DELTA_POSITION,
    CONF_DELTA_TIME,
    CONF_DISTANCE,
    CONF_ENABLE_AWAY_MODE,
    CONF_ENABLE_BLIND_SPOT,
    CONF_ENABLE_HEAT_GAIN_POLICY,
    CONF_ENABLE_MAX_POSITION,
    CONF_ENABLE_MIN_POSITION,
    CONF_END_ENTITY,
    CONF_END_TIME,
    CONF_ENTITIES,
    CONF_ENTRY_TYPE,
    CONF_FACADE_NAME,
    CONF_FACADE_OFFSET,
    CONF_FACADE_PROFILES,
    CONF_FACADE_REFERENCE_AZIMUTH,
    CONF_FLOOR_NAME,
    CONF_FLOOR_PROFILES,
    CONF_FORECAST_HOT_DAY_THRESHOLD,
    CONF_FORECAST_INFLUENCE_STRENGTH,
    CONF_FORECAST_PREEMPTIVE_START_TIME,
    CONF_FORECAST_VERY_HOT_DAY_THRESHOLD,
    CONF_FOV_LEFT,
    CONF_FOV_RIGHT,
    CONF_FULL_CLOSE_POSITION,
    CONF_FULL_CLOSE_THRESHOLD,
    CONF_GLASS_TYPE,
    CONF_HEAT_POWER_LIMIT_ENABLED,
    CONF_HEAT_PROTECTION_CONTROL_MODE,
    CONF_HEAT_PROTECTION_MIN_OUTSIDE_TEMP,
    CONF_HEIGHT_WIN,
    CONF_HORIZON_MODE,
    CONF_HORIZON_PROFILE,
    CONF_HOUSE_DEFAULTS,
    CONF_HOUSE_PROFILE_ENTRY_ID,
    CONF_HOUSE_REFERENCE_AZIMUTH,
    CONF_INTERP,
    CONF_INTERP_END,
    CONF_INTERP_LIST,
    CONF_INTERP_LIST_NEW,
    CONF_INTERP_START,
    CONF_INVERSE_STATE,
    CONF_LENGTH_AWNING,
    CONF_MANUAL_IGNORE_INTERMEDIATE,
    CONF_MANUAL_OVERRIDE_DURATION,
    CONF_MANUAL_OVERRIDE_RESET,
    CONF_MANUAL_THRESHOLD,
    CONF_MAX_ELEVATION,
    CONF_MAX_POSITION,
    CONF_MAX_TRANSMITTED_SOLAR_POWER,
    CONF_MIN_ELEVATION,
    CONF_MIN_POSITION,
    CONF_NIGHT_END_TIME,
    CONF_NIGHT_MODE,
    CONF_NIGHT_START_TIME,
    CONF_PARTIAL_CLOSE_POSITION,
    CONF_PARTIAL_CLOSE_THRESHOLD,
    CONF_POLICY_PRESET,
    CONF_PROFILE_OVERRIDES,
    CONF_RETURN_SUNSET,
    CONF_REVEAL_LEFT,
    CONF_REVEAL_RIGHT,
    CONF_REVEAL_TOP,
    CONF_ROOM_FACADE_PROFILES,
    CONF_ROOM_HEAT_PROTECTION_THRESHOLD,
    CONF_ROOM_NAME,
    CONF_ROOM_PROFILES,
    CONF_ROOM_TEMPERATURE_ENTITY,
    CONF_SHOW_EXPERT_WEIGHTS,
    CONF_SOLAR_RADIATION_ENTITY,
    CONF_SOLAR_RADIATION_REFERENCE,
    CONF_START_ENTITY,
    CONF_START_TIME,
    CONF_SUNRISE_OFFSET,
    CONF_SUNSET_OFFSET,
    CONF_SUNSET_POS,
    CONF_TEMP_ENTITY,
    CONF_TEMP_HIGH,
    CONF_TILT_DEPTH,
    CONF_TILT_DISTANCE,
    CONF_TILT_MODE,
    CONF_USE_FACADE_AZIMUTH,
    CONF_USE_FORECAST_MAX_TEMP_TODAY,
    CONF_USE_FORECAST_MAX_TEMP_TOMORROW,
    CONF_USE_LOCAL_GEOMETRY,
    CONF_USE_LOCAL_HORIZON,
    CONF_USE_LOCAL_POLICY,
    CONF_USE_OPEN_DATA_SOLAR_RADIATION,
    CONF_WEATHER_ENTITY,
    CONF_WEIGHT_DIRECT_EXPOSURE,
    CONF_WEIGHT_FORECAST_TEMPERATURE,
    CONF_WEIGHT_GLAZING,
    CONF_WEIGHT_INCIDENCE,
    CONF_WEIGHT_SOLAR_RADIATION,
    CONF_WINDOW_OVERRIDES,
    CONF_WINDOW_WIDTH,
    ENTRY_TYPE_HOUSE,
    HEAT_PROTECTION_MODE_SCALING,
    HORIZON_MODE_WINDOW,
    NIGHT_MODE_TIME,
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant


HOUSE_RULE_KEYS = {
    CONF_DEFAULT_HEIGHT,
    CONF_SUNSET_POS,
    CONF_SUNSET_OFFSET,
    CONF_SUNRISE_OFFSET,
    CONF_NIGHT_MODE,
    CONF_NIGHT_START_TIME,
    CONF_NIGHT_END_TIME,
    CONF_GLASS_TYPE,
    CONF_WEATHER_ENTITY,
    CONF_USE_FORECAST_MAX_TEMP_TODAY,
    CONF_USE_FORECAST_MAX_TEMP_TOMORROW,
    CONF_USE_OPEN_DATA_SOLAR_RADIATION,
    CONF_SOLAR_RADIATION_ENTITY,
    CONF_SOLAR_RADIATION_REFERENCE,
    CONF_FORECAST_HOT_DAY_THRESHOLD,
    CONF_FORECAST_VERY_HOT_DAY_THRESHOLD,
    CONF_FORECAST_PREEMPTIVE_START_TIME,
    CONF_FORECAST_INFLUENCE_STRENGTH,
    CONF_ENABLE_HEAT_GAIN_POLICY,
    CONF_POLICY_PRESET,
    CONF_ENABLE_AWAY_MODE,
    CONF_AWAY_ENTITY,
    CONF_AWAY_SCORE_MULTIPLIER,
    CONF_AWAY_THRESHOLD_REDUCTION,
    CONF_AWAY_POSITION_OFFSET,
    CONF_HEAT_POWER_LIMIT_ENABLED,
    CONF_HEAT_PROTECTION_MIN_OUTSIDE_TEMP,
    CONF_ROOM_HEAT_PROTECTION_THRESHOLD,
    CONF_MAX_TRANSMITTED_SOLAR_POWER,
    CONF_HEAT_PROTECTION_CONTROL_MODE,
    CONF_BINARY_CLOSE_THRESHOLD,
    CONF_BINARY_CLOSE_POSITION,
    CONF_SHOW_EXPERT_WEIGHTS,
    CONF_WEIGHT_DIRECT_EXPOSURE,
    CONF_WEIGHT_INCIDENCE,
    CONF_WEIGHT_GLAZING,
    CONF_WEIGHT_FORECAST_TEMPERATURE,
    CONF_WEIGHT_SOLAR_RADIATION,
    CONF_PARTIAL_CLOSE_THRESHOLD,
    CONF_FULL_CLOSE_THRESHOLD,
    CONF_PARTIAL_CLOSE_POSITION,
    CONF_FULL_CLOSE_POSITION,
    CONF_DELTA_POSITION,
    CONF_DELTA_TIME,
    CONF_START_TIME,
    CONF_START_ENTITY,
    CONF_END_TIME,
    CONF_END_ENTITY,
    CONF_RETURN_SUNSET,
    CONF_MANUAL_OVERRIDE_DURATION,
    CONF_MANUAL_OVERRIDE_RESET,
    CONF_MANUAL_THRESHOLD,
    CONF_MANUAL_IGNORE_INTERMEDIATE,
}

STANDARD_GEOMETRY_KEYS = {
    CONF_FOV_LEFT,
    CONF_FOV_RIGHT,
    CONF_REVEAL_LEFT,
    CONF_REVEAL_RIGHT,
    CONF_REVEAL_TOP,
    CONF_HORIZON_MODE,
    CONF_HORIZON_PROFILE,
    CONF_MIN_ELEVATION,
    CONF_MAX_ELEVATION,
}

WINDOW_OWNED_KEYS = {
    CONF_HOUSE_PROFILE_ENTRY_ID,
    CONF_FLOOR_NAME,
    CONF_ROOM_NAME,
    CONF_FACADE_NAME,
    CONF_ENTITIES,
    CONF_HEIGHT_WIN,
    CONF_WINDOW_WIDTH,
    CONF_DISTANCE,
    CONF_LENGTH_AWNING,
    CONF_AWNING_ANGLE,
    CONF_TILT_DISTANCE,
    CONF_TILT_DEPTH,
    CONF_TILT_MODE,
    CONF_MAX_POSITION,
    CONF_MIN_POSITION,
    CONF_ENABLE_MAX_POSITION,
    CONF_ENABLE_MIN_POSITION,
    CONF_INVERSE_STATE,
    CONF_INTERP,
    CONF_INTERP_START,
    CONF_INTERP_END,
    CONF_INTERP_LIST,
    CONF_INTERP_LIST_NEW,
    CONF_ENABLE_BLIND_SPOT,
    CONF_BLIND_SPOT_LEFT,
    CONF_BLIND_SPOT_RIGHT,
    CONF_BLIND_SPOT_ELEVATION,
    CONF_TEMP_ENTITY,
    CONF_TEMP_HIGH,
    CONF_USE_LOCAL_GEOMETRY,
    CONF_USE_LOCAL_HORIZON,
    CONF_USE_LOCAL_POLICY,
    CONF_WINDOW_OVERRIDES,
    CONF_FACADE_OFFSET,
    CONF_ROOM_TEMPERATURE_ENTITY,
}


def built_in_house_defaults() -> dict[str, Any]:
    """Return stable defaults used before any profile layer."""
    return {
        CONF_DISTANCE: 0.5,
        CONF_DEFAULT_HEIGHT: 100,
        CONF_SUNSET_POS: 100,
        CONF_SUNSET_OFFSET: 0,
        CONF_SUNRISE_OFFSET: 0,
        CONF_NIGHT_MODE: NIGHT_MODE_TIME,
        CONF_NIGHT_START_TIME: "22:00:00",
        CONF_NIGHT_END_TIME: "06:00:00",
        CONF_GLASS_TYPE: "double_clear",
        CONF_FOV_LEFT: 90,
        CONF_FOV_RIGHT: 90,
        CONF_REVEAL_LEFT: 0.0,
        CONF_REVEAL_RIGHT: 0.0,
        CONF_REVEAL_TOP: 0.0,
        CONF_HORIZON_MODE: HORIZON_MODE_WINDOW,
        CONF_HORIZON_PROFILE: None,
        CONF_USE_FORECAST_MAX_TEMP_TODAY: True,
        CONF_USE_FORECAST_MAX_TEMP_TOMORROW: False,
        CONF_USE_OPEN_DATA_SOLAR_RADIATION: True,
        CONF_SOLAR_RADIATION_REFERENCE: 900,
        CONF_FORECAST_HOT_DAY_THRESHOLD: 26,
        CONF_FORECAST_VERY_HOT_DAY_THRESHOLD: 30,
        CONF_FORECAST_PREEMPTIVE_START_TIME: "09:00:00",
        CONF_FORECAST_INFLUENCE_STRENGTH: 0.5,
        CONF_ROOM_HEAT_PROTECTION_THRESHOLD: 24,
        CONF_ENABLE_HEAT_GAIN_POLICY: True,
        CONF_POLICY_PRESET: "balanced",
        CONF_ENABLE_AWAY_MODE: False,
        CONF_HEAT_POWER_LIMIT_ENABLED: False,
        CONF_HEAT_PROTECTION_MIN_OUTSIDE_TEMP: 14,
        CONF_MAX_TRANSMITTED_SOLAR_POWER: 250,
        CONF_HEAT_PROTECTION_CONTROL_MODE: HEAT_PROTECTION_MODE_SCALING,
        CONF_BINARY_CLOSE_THRESHOLD: 180,
        CONF_BINARY_CLOSE_POSITION: 20,
        CONF_SHOW_EXPERT_WEIGHTS: False,
        CONF_WEIGHT_DIRECT_EXPOSURE: 1.2,
        CONF_WEIGHT_INCIDENCE: 0.9,
        CONF_WEIGHT_GLAZING: 0.8,
        CONF_WEIGHT_FORECAST_TEMPERATURE: 1.0,
        CONF_WEIGHT_SOLAR_RADIATION: 1.0,
        CONF_PARTIAL_CLOSE_THRESHOLD: 0.35,
        CONF_FULL_CLOSE_THRESHOLD: 0.65,
        CONF_PARTIAL_CLOSE_POSITION: 70,
        CONF_FULL_CLOSE_POSITION: 30,
        CONF_DELTA_POSITION: 1,
        CONF_DELTA_TIME: 2,
        CONF_START_TIME: "00:00:00",
        CONF_END_TIME: "00:00:00",
        CONF_RETURN_SUNSET: False,
        CONF_MANUAL_OVERRIDE_DURATION: {"minutes": 15},
        CONF_MANUAL_OVERRIDE_RESET: False,
        CONF_MANUAL_IGNORE_INTERMEDIATE: False,
    }


def default_house_profile_options() -> dict[str, Any]:
    """Return the initial options for a new house profile entry."""
    return {
        CONF_HOUSE_REFERENCE_AZIMUTH: 0,
        CONF_HOUSE_DEFAULTS: built_in_house_defaults(),
        CONF_FLOOR_PROFILES: {},
        CONF_FACADE_PROFILES: {},
        CONF_ROOM_PROFILES: {},
        CONF_ROOM_FACADE_PROFILES: {},
    }


@dataclass(frozen=True)
class ProfileResolution:
    """Resolved options and their inheritance trace."""

    options: dict[str, Any]
    layers: tuple[str, ...]
    source_by_key: dict[str, str]
    house_profile_entry_id: str | None = None
    house_profile_name: str | None = None


def room_facade_key(room_id: str, facade_name: str) -> str:
    """Build a stable key for one wall/facade in a room."""
    return f"{room_id}::{facade_name}"


def apply_bulk_profile_assignment(
    window_options: dict[str, Any],
    *,
    house_profile_entry_id: str,
    floor_id: str,
    room_id: str,
    facade_name: str | None,
    facade_offset: float = 0,
    reset_local_overrides: bool = True,
) -> dict[str, Any]:
    """Apply one shared hierarchy assignment without changing cover entities."""
    updated = dict(window_options)
    updated[CONF_HOUSE_PROFILE_ENTRY_ID] = house_profile_entry_id
    updated[CONF_FLOOR_NAME] = floor_id
    updated[CONF_ROOM_NAME] = room_id
    updated[CONF_FACADE_OFFSET] = facade_offset
    if facade_name:
        updated[CONF_FACADE_NAME] = facade_name
    else:
        updated.pop(CONF_FACADE_NAME, None)

    if reset_local_overrides:
        updated[CONF_USE_LOCAL_GEOMETRY] = False
        updated[CONF_USE_LOCAL_HORIZON] = False
        updated[CONF_USE_LOCAL_POLICY] = False
        updated[CONF_WINDOW_OVERRIDES] = {}
        updated.pop(CONF_ROOM_TEMPERATURE_ENTITY, None)
    return updated


def _overrides(profile: Any) -> dict[str, Any]:
    if not isinstance(profile, dict):
        return {}
    value = profile.get(CONF_PROFILE_OVERRIDES, profile)
    return dict(value) if isinstance(value, dict) else {}


def _merge(
    target: dict[str, Any],
    values: dict[str, Any],
    source: str,
    sources: dict[str, str],
) -> None:
    for key, value in values.items():
        if value is not None:
            target[key] = value
            sources[key] = source


def resolve_profile_options(
    window_options: dict[str, Any],
    house_options: dict[str, Any] | None,
    *,
    house_profile_entry_id: str | None = None,
    house_profile_name: str | None = None,
) -> ProfileResolution:
    """Resolve one window from built-ins through all configured profile layers."""
    raw = dict(window_options)
    if not raw.get(CONF_ROOM_TEMPERATURE_ENTITY) and raw.get(CONF_TEMP_ENTITY):
        raw[CONF_ROOM_TEMPERATURE_ENTITY] = raw[CONF_TEMP_ENTITY]
    if (
        CONF_ROOM_HEAT_PROTECTION_THRESHOLD not in raw
        and raw.get(CONF_TEMP_HIGH) is not None
    ):
        raw[CONF_ROOM_HEAT_PROTECTION_THRESHOLD] = raw[CONF_TEMP_HIGH]
    if not house_options:
        return ProfileResolution(raw, ("window",), {key: "window" for key in raw})

    house = default_house_profile_options()
    house.update(dict(house_options))
    resolved = built_in_house_defaults()
    sources = {key: "built_in" for key in resolved}
    layers = ["built_in"]

    house_defaults = dict(house.get(CONF_HOUSE_DEFAULTS) or {})
    if (
        CONF_ROOM_HEAT_PROTECTION_THRESHOLD not in house_defaults
        and house_defaults.get(CONF_TEMP_HIGH) is not None
    ):
        house_defaults[CONF_ROOM_HEAT_PROTECTION_THRESHOLD] = house_defaults[
            CONF_TEMP_HIGH
        ]
    _merge(resolved, house_defaults, "house", sources)
    layers.append("house")

    room_id = raw.get(CONF_ROOM_NAME)
    room_profiles = dict(house.get(CONF_ROOM_PROFILES) or {})
    room_profile = room_profiles.get(room_id, {}) if room_id else {}
    floor_id = raw.get(CONF_FLOOR_NAME) or room_profile.get(CONF_FLOOR_NAME)
    facade_name = raw.get(CONF_FACADE_NAME) or room_profile.get(CONF_FACADE_NAME)

    floor_profile = (house.get(CONF_FLOOR_PROFILES) or {}).get(floor_id, {})
    if floor_profile:
        _merge(resolved, _overrides(floor_profile), f"floor:{floor_id}", sources)
        layers.append(f"floor:{floor_id}")

    facade_profile = (house.get(CONF_FACADE_PROFILES) or {}).get(facade_name, {})
    if facade_profile:
        _merge(
            resolved,
            _overrides(facade_profile),
            f"facade:{facade_name}",
            sources,
        )
        layers.append(f"facade:{facade_name}")

    if room_profile:
        _merge(resolved, _overrides(room_profile), f"room:{room_id}", sources)
        layers.append(f"room:{room_id}")

    room_wall = {}
    if room_id and facade_name:
        room_wall = (house.get(CONF_ROOM_FACADE_PROFILES) or {}).get(
            room_facade_key(room_id, facade_name), {}
        )
    if room_wall:
        _merge(
            resolved,
            _overrides(room_wall),
            f"room_facade:{room_id}:{facade_name}",
            sources,
        )
        layers.append(f"room_facade:{room_id}:{facade_name}")

    _merge(
        resolved,
        {key: raw.get(key) for key in WINDOW_OWNED_KEYS if key in raw},
        "window",
        sources,
    )
    resolved[CONF_ROOM_NAME] = room_id
    resolved[CONF_FLOOR_NAME] = floor_id
    resolved[CONF_FACADE_NAME] = facade_name

    if raw.get(CONF_USE_LOCAL_GEOMETRY):
        _merge(
            resolved,
            {key: raw.get(key) for key in STANDARD_GEOMETRY_KEYS | {CONF_GLASS_TYPE}},
            "window_geometry",
            sources,
        )
        layers.append("window_geometry")
    elif raw.get(CONF_USE_LOCAL_HORIZON):
        _merge(
            resolved,
            {
                CONF_HORIZON_MODE: raw.get(CONF_HORIZON_MODE),
                CONF_HORIZON_PROFILE: raw.get(CONF_HORIZON_PROFILE),
            },
            "window_horizon",
            sources,
        )
        layers.append("window_horizon")

    if raw.get(CONF_USE_LOCAL_POLICY):
        _merge(
            resolved,
            {key: raw.get(key) for key in HOUSE_RULE_KEYS if key in raw},
            "window_policy",
            sources,
        )
        layers.append("window_policy")

    _merge(
        resolved,
        dict(raw.get(CONF_WINDOW_OVERRIDES) or {}),
        "window_override",
        sources,
    )
    if raw.get(CONF_WINDOW_OVERRIDES):
        layers.append("window_override")

    reference = float(house.get(CONF_HOUSE_REFERENCE_AZIMUTH, 0) or 0)
    facade_offset = float(facade_profile.get(CONF_FACADE_OFFSET, 0) or 0)
    window_offset = float(raw.get(CONF_FACADE_OFFSET, 0) or 0)
    if facade_name and facade_profile:
        resolved[CONF_USE_FACADE_AZIMUTH] = True
        resolved[CONF_FACADE_REFERENCE_AZIMUTH] = reference
        resolved[CONF_FACADE_OFFSET] = facade_offset + window_offset
        resolved[CONF_AZIMUTH] = int(round((reference + facade_offset + window_offset) % 360))
        sources[CONF_AZIMUTH] = f"facade:{facade_name}"
    elif raw.get(CONF_USE_FACADE_AZIMUTH):
        legacy_reference = float(raw.get(CONF_FACADE_REFERENCE_AZIMUTH, reference) or 0)
        resolved[CONF_AZIMUTH] = int(round((legacy_reference + window_offset) % 360))
        sources[CONF_AZIMUTH] = "window_facade"
    elif raw.get(CONF_AZIMUTH) is not None:
        resolved[CONF_AZIMUTH] = raw[CONF_AZIMUTH]
        sources[CONF_AZIMUTH] = "window"

    return ProfileResolution(
        resolved,
        tuple(layers),
        sources,
        house_profile_entry_id,
        house_profile_name,
    )


def resolve_effective_options(
    hass: HomeAssistant, entry: ConfigEntry
) -> ProfileResolution:
    """Resolve a Home Assistant window entry against its linked house profile."""
    profile_id = entry.options.get(CONF_HOUSE_PROFILE_ENTRY_ID)
    if not profile_id:
        return resolve_profile_options(dict(entry.options), None)

    profile_entry = hass.config_entries.async_get_entry(profile_id)
    if (
        profile_entry is None
        or profile_entry.data.get(CONF_ENTRY_TYPE) != ENTRY_TYPE_HOUSE
    ):
        return resolve_profile_options(dict(entry.options), None)

    return resolve_profile_options(
        dict(entry.options),
        dict(profile_entry.options),
        house_profile_entry_id=profile_entry.entry_id,
        house_profile_name=profile_entry.data.get("name") or profile_entry.title,
    )

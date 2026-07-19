"""Migrate retired Solar Shading settings to the unified policy model."""

from __future__ import annotations

from typing import Any

from .const import (
    CONF_BINARY_CLOSE_POSITION,
    CONF_BINARY_CLOSE_THRESHOLD,
    CONF_CLIMATE_MODE,
    CONF_ENABLE_HEAT_GAIN_POLICY,
    CONF_FORECAST_HOT_DAY_THRESHOLD,
    CONF_HEAT_POWER_OUTSIDE_TEMP_THRESHOLD,
    CONF_HEAT_PROTECTION_CONTROL_MODE,
    CONF_HOT_DAY_CLOSE_ENABLED,
    CONF_HOT_DAY_CLOSE_POSITION,
    CONF_HOT_DAY_CLOSE_THRESHOLD,
    CONF_IRRADIANCE_ENTITY,
    CONF_IRRADIANCE_THRESHOLD,
    CONF_MAX_TRANSMITTED_SOLAR_POWER,
    CONF_OUTSIDE_THRESHOLD,
    CONF_OUTSIDETEMP_ENTITY,
    CONF_PRESENCE_ENTITY,
    CONF_ROOM_HEAT_PROTECTION_THRESHOLD,
    CONF_ROOM_TEMPERATURE_ENTITY,
    CONF_TEMP_ENTITY,
    CONF_TEMP_HIGH,
    CONF_TEMP_LOW,
    CONF_TRANSPARENT_BLIND,
    CONF_VERY_HOT_DAY_CLOSE_POSITION,
)

LEGACY_MAX_TRANSMITTED_SOLAR_POWER = "heat_power_max_watts"

RETIRED_OPTION_KEYS = {
    "enable_legacy_basic_shading",
    "lux_entity",
    "lux_threshold",
    "use_forecast_cloud_coverage",
    "use_forecast_precipitation_probability",
    "use_forecast_precipitation_amount",
    "use_forecast_uv_index",
    "weather_state",
    "weight_weather",
    "weight_forecast_uv",
    "weight_forecast_clouds",
    "weight_forecast_precipitation_probability",
    "weight_forecast_precipitation_amount",
    CONF_CLIMATE_MODE,
    CONF_TEMP_LOW,
    CONF_PRESENCE_ENTITY,
    CONF_OUTSIDETEMP_ENTITY,
    CONF_IRRADIANCE_ENTITY,
    CONF_IRRADIANCE_THRESHOLD,
    CONF_OUTSIDE_THRESHOLD,
    CONF_HOT_DAY_CLOSE_ENABLED,
    CONF_HOT_DAY_CLOSE_THRESHOLD,
    CONF_HOT_DAY_CLOSE_POSITION,
    CONF_VERY_HOT_DAY_CLOSE_POSITION,
    CONF_HEAT_POWER_OUTSIDE_TEMP_THRESHOLD,
    CONF_TRANSPARENT_BLIND,
}


def migrate_retired_options(options: dict[str, Any]) -> dict[str, Any]:
    """Recursively migrate useful values and discard retired settings."""
    migrated = {
        key: _migrate_nested(value)
        for key, value in options.items()
    }

    if CONF_ROOM_TEMPERATURE_ENTITY not in migrated:
        legacy_room_sensor = migrated.get(CONF_TEMP_ENTITY)
        if legacy_room_sensor:
            migrated[CONF_ROOM_TEMPERATURE_ENTITY] = legacy_room_sensor
    if (
        CONF_ROOM_HEAT_PROTECTION_THRESHOLD not in migrated
        and CONF_TEMP_HIGH in migrated
    ):
        migrated[CONF_ROOM_HEAT_PROTECTION_THRESHOLD] = migrated[CONF_TEMP_HIGH]
    if CONF_FORECAST_HOT_DAY_THRESHOLD not in migrated:
        legacy_hot_threshold = migrated.get(CONF_HOT_DAY_CLOSE_THRESHOLD)
        if legacy_hot_threshold is not None:
            migrated[CONF_FORECAST_HOT_DAY_THRESHOLD] = legacy_hot_threshold
    if migrated.get(CONF_TRANSPARENT_BLIND):
        migrated.setdefault(CONF_HEAT_PROTECTION_CONTROL_MODE, "binary")
        migrated.setdefault(CONF_BINARY_CLOSE_POSITION, 0)
        migrated.setdefault(
            CONF_BINARY_CLOSE_THRESHOLD,
            migrated.get(CONF_IRRADIANCE_THRESHOLD, 180),
        )
        migrated.setdefault(CONF_ENABLE_HEAT_GAIN_POLICY, True)
    if CONF_MAX_TRANSMITTED_SOLAR_POWER not in migrated:
        legacy_limit = migrated.get(LEGACY_MAX_TRANSMITTED_SOLAR_POWER)
        if legacy_limit is not None:
            migrated[CONF_MAX_TRANSMITTED_SOLAR_POWER] = legacy_limit

    migrated.pop(LEGACY_MAX_TRANSMITTED_SOLAR_POWER, None)
    migrated.pop(CONF_TEMP_ENTITY, None)
    migrated.pop(CONF_TEMP_HIGH, None)
    for key in RETIRED_OPTION_KEYS:
        migrated.pop(key, None)
    return migrated


def _migrate_nested(value: Any) -> Any:
    """Migrate dictionaries at every house-profile inheritance level."""
    if isinstance(value, dict):
        return migrate_retired_options(value)
    if isinstance(value, list):
        return [_migrate_nested(item) for item in value]
    return value

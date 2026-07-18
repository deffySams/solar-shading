"""Config flow for Adaptive Cover integration."""

from __future__ import annotations

import json
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_AWNING_ANGLE,
    CONF_AZIMUTH,
    CONF_AWAY_ENTITY,
    CONF_AWAY_POSITION_OFFSET,
    CONF_AWAY_SCORE_MULTIPLIER,
    CONF_AWAY_THRESHOLD_REDUCTION,
    CONF_BLIND_SPOT_ELEVATION,
    CONF_BLIND_SPOT_LEFT,
    CONF_BLIND_SPOT_RIGHT,
    CONF_CLIMATE_MODE,
    CONF_DEFAULT_HEIGHT,
    CONF_DELTA_POSITION,
    CONF_DELTA_TIME,
    CONF_DISTANCE,
    CONF_ENABLE_BLIND_SPOT,
    CONF_ENABLE_AWAY_MODE,
    CONF_END_ENTITY,
    CONF_END_TIME,
    CONF_ENTITIES,
    CONF_FACADE_NAME,
    CONF_FACADE_OFFSET,
    CONF_FACADE_REFERENCE_AZIMUTH,
    CONF_FOV_LEFT,
    CONF_FOV_RIGHT,
    CONF_FLOOR_NAME,
    CONF_FORECAST_HOT_DAY_THRESHOLD,
    CONF_FORECAST_INFLUENCE_STRENGTH,
    CONF_FORECAST_PREEMPTIVE_START_TIME,
    CONF_FORECAST_VERY_HOT_DAY_THRESHOLD,
    CONF_FULL_CLOSE_POSITION,
    CONF_FULL_CLOSE_THRESHOLD,
    CONF_GLASS_TYPE,
    CONF_HAS_ADDITIONAL_DAYLIGHT_WINDOWS,
    CONF_HEAT_POWER_LIMIT_ENABLED,
    CONF_MAX_TRANSMITTED_SOLAR_POWER,
    CONF_HEAT_POWER_OUTSIDE_TEMP_THRESHOLD,
    CONF_HEAT_PROTECTION_MIN_OUTSIDE_TEMP,
    CONF_HEIGHT_WIN,
    CONF_HOT_DAY_CLOSE_ENABLED,
    CONF_HOT_DAY_CLOSE_POSITION,
    CONF_HOT_DAY_CLOSE_THRESHOLD,
    CONF_VERY_HOT_DAY_CLOSE_POSITION,
    CONF_HORIZON_PROFILE,
    CONF_INTERP,
    CONF_INTERP_END,
    CONF_INTERP_LIST,
    CONF_INTERP_LIST_NEW,
    CONF_INTERP_START,
    CONF_INVERSE_STATE,
    CONF_IRRADIANCE_ENTITY,
    CONF_IRRADIANCE_THRESHOLD,
    CONF_LENGTH_AWNING,
    CONF_MANUAL_IGNORE_INTERMEDIATE,
    CONF_MANUAL_OVERRIDE_DURATION,
    CONF_MANUAL_OVERRIDE_RESET,
    CONF_MANUAL_THRESHOLD,
    CONF_MAX_ELEVATION,
    CONF_MAX_POSITION,
    CONF_MIN_ELEVATION,
    CONF_MODE,
    CONF_ENABLE_HEAT_GAIN_POLICY,
    CONF_OUTSIDETEMP_ENTITY,
    CONF_PRESENCE_ENTITY,
    CONF_POLICY_PRESET,
    CONF_RETURN_SUNSET,
    CONF_REVEAL_LEFT,
    CONF_REVEAL_RIGHT,
    CONF_REVEAL_TOP,
    CONF_ROOM_NAME,
    CONF_PARTIAL_CLOSE_POSITION,
    CONF_PARTIAL_CLOSE_THRESHOLD,
    CONF_SENSOR_TYPE,
    CONF_SHOW_EXPERT_WEIGHTS,
    CONF_START_ENTITY,
    CONF_START_TIME,
    CONF_SUNRISE_OFFSET,
    CONF_SUNSET_OFFSET,
    CONF_SUNSET_POS,
    CONF_TEMP_ENTITY,
    CONF_TEMP_HIGH,
    CONF_TEMP_LOW,
    CONF_TILT_DEPTH,
    CONF_TILT_DISTANCE,
    CONF_TILT_MODE,
    CONF_TRANSPARENT_BLIND,
    CONF_TEMPLATE_ENTRY,
    CONF_USE_FACADE_AZIMUTH,
    CONF_USE_FORECAST_MAX_TEMP_TODAY,
    CONF_USE_FORECAST_MAX_TEMP_TOMORROW,
    CONF_USE_OPEN_DATA_SOLAR_RADIATION,
    CONF_WEIGHT_DIRECT_EXPOSURE,
    CONF_WEIGHT_FORECAST_TEMPERATURE,
    CONF_WEIGHT_GLAZING,
    CONF_WEIGHT_INCIDENCE,
    CONF_WEIGHT_SOLAR_RADIATION,
    CONF_WEATHER_ENTITY,
    CONF_OUTSIDE_THRESHOLD,
    CONF_SOLAR_RADIATION_ENTITY,
    CONF_SOLAR_RADIATION_REFERENCE,
    CONF_WINDOW_WIDTH,
    DOMAIN,
    GLASS_TYPE_OPTIONS,
    POLICY_PRESET_OPTIONS,
    SensorType,
    CONF_MIN_POSITION,
    CONF_ENABLE_MAX_POSITION,
    CONF_ENABLE_MIN_POSITION,
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
}


def _migrate_retired_options(options: dict[str, Any]) -> dict[str, Any]:
    """Move the one renamed value and discard options no longer used."""
    migrated = dict(options)
    if CONF_MAX_TRANSMITTED_SOLAR_POWER not in migrated:
        legacy_limit = migrated.get(LEGACY_MAX_TRANSMITTED_SOLAR_POWER)
        if legacy_limit is not None:
            migrated[CONF_MAX_TRANSMITTED_SOLAR_POWER] = legacy_limit
    migrated.pop(LEGACY_MAX_TRANSMITTED_SOLAR_POWER, None)
    for key in RETIRED_OPTION_KEYS:
        migrated.pop(key, None)
    return migrated

# DEFAULT_NAME = "Adaptive Cover"

SENSOR_TYPE_MENU = [SensorType.BLIND, SensorType.AWNING, SensorType.TILT]

HORIZON_PROFILE_EXAMPLE = """[
  {"angle": 0, "lower_elevation": 18, "upper_elevation": 90},
  {"angle": 45, "lower_elevation": 12, "upper_elevation": 90},
  {"angle": 90, "lower_elevation": 8, "upper_elevation": 55},
  {"angle": 135, "lower_elevation": 14, "upper_elevation": 90},
  {"angle": 180, "lower_elevation": 20, "upper_elevation": 90}
]"""


CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required("name"): selector.TextSelector(),
        vol.Optional(CONF_MODE, default=SensorType.BLIND): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=SENSOR_TYPE_MENU, translation_key="mode"
            )
        ),
    }
)

TEMPLATE_NONE = "__none__"


def _template_entry_options(hass) -> list[dict[str, str]]:
    """Return selectable existing Solar Shading entries for default reuse."""
    entries = getattr(hass.config_entries, "async_entries", lambda _domain: [])(DOMAIN)
    result: list[dict[str, str]] = []
    for entry in entries:
        name = entry.data.get("name") or entry.title or entry.entry_id
        sensor_type = entry.data.get(CONF_SENSOR_TYPE)
        result.append(
            {
                "value": entry.entry_id,
                "label": f"{name} ({sensor_type or 'Solar Shading'})",
            }
        )
    return result


def _config_schema(hass) -> vol.Schema:
    """Return the initial schema, including existing-window templates."""
    schema: dict[Any, Any] = dict(CONFIG_SCHEMA.schema)
    options = _template_entry_options(hass)
    if options:
        schema[
            vol.Optional(CONF_TEMPLATE_ENTRY, default=TEMPLATE_NONE)
        ] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[
                    {"value": TEMPLATE_NONE, "label": "Keine Vorlage"},
                    *options,
                ]
            )
        )
    return vol.Schema(schema)


def _template_options(hass, entry_id: str | None) -> dict[str, Any]:
    """Return options from an existing entry selected as setup template."""
    if not entry_id or entry_id == TEMPLATE_NONE:
        return {}
    entries = getattr(hass.config_entries, "async_entries", lambda _domain: [])(DOMAIN)
    for entry in entries:
        if entry.entry_id == entry_id:
            options = dict(entry.options)
            options.pop(CONF_ENTITIES, None)
            options.pop(CONF_TEMPLATE_ENTRY, None)
            return options
    return {}


def _ha_selector_or_text(name: str):
    """Use HA-native selectors when available, otherwise keep the flow usable."""
    selector_class = getattr(selector, name, None)
    if selector_class is None:
        return selector.TextSelector()
    return selector_class()


CLIMATE_MODE = vol.Schema(
    {
        vol.Optional(CONF_CLIMATE_MODE, default=False): selector.BooleanSelector(),
    }
)

OPTIONS = vol.Schema(
    {
        vol.Optional(CONF_FACADE_NAME): selector.TextSelector(),
        vol.Optional(CONF_FLOOR_NAME): _ha_selector_or_text("FloorSelector"),
        vol.Optional(CONF_ROOM_NAME): _ha_selector_or_text("AreaSelector"),
        vol.Optional(CONF_USE_FACADE_AZIMUTH, default=False): selector.BooleanSelector(),
        vol.Optional(CONF_FACADE_REFERENCE_AZIMUTH, default=0): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0, max=359, step=1, mode="slider", unit_of_measurement="Â°"
            )
        ),
        vol.Optional(CONF_FACADE_OFFSET, default=0): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=-360, max=360, step=1, mode="box", unit_of_measurement="Â°"
            )
        ),
        vol.Required(CONF_AZIMUTH, default=180): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0, max=359, mode="slider", unit_of_measurement="°"
            )
        ),
        vol.Required(CONF_DEFAULT_HEIGHT, default=60): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0, max=100, step=1, mode="slider", unit_of_measurement="%"
            )
        ),
        vol.Optional(CONF_MAX_POSITION): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=100)
        ),
        vol.Optional(CONF_ENABLE_MAX_POSITION, default=False): bool,
        vol.Optional(CONF_MIN_POSITION): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=99)
        ),
        vol.Optional(CONF_ENABLE_MIN_POSITION, default=False): bool,
        vol.Optional(CONF_MIN_ELEVATION): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=90)
        ),
        vol.Optional(CONF_MAX_ELEVATION): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=90)
        ),
        vol.Required(CONF_FOV_LEFT, default=90): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=1, max=90, step=1, mode="slider", unit_of_measurement="°"
            )
        ),
        vol.Required(CONF_FOV_RIGHT, default=90): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=1, max=90, step=1, mode="slider", unit_of_measurement="°"
            )
        ),
        vol.Required(CONF_SUNSET_POS, default=0): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0, max=100, step=1, mode="slider", unit_of_measurement="%"
            )
        ),
        vol.Required(CONF_SUNSET_OFFSET, default=0): selector.NumberSelector(
            selector.NumberSelectorConfig(mode="box", unit_of_measurement="minutes")
        ),
        vol.Required(CONF_SUNRISE_OFFSET, default=0): selector.NumberSelector(
            selector.NumberSelectorConfig(mode="box", unit_of_measurement="minutes")
        ),
        vol.Required(CONF_INVERSE_STATE, default=False): bool,
        vol.Required(CONF_ENABLE_BLIND_SPOT, default=False): bool,
        vol.Required(CONF_INTERP, default=False): bool,
        vol.Optional(CONF_WINDOW_WIDTH): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0.1, max=20, step=0.01, mode="box", unit_of_measurement="m"
            )
        ),
        vol.Optional(CONF_REVEAL_LEFT): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0, max=5, step=0.01, mode="box", unit_of_measurement="m"
            )
        ),
        vol.Optional(CONF_REVEAL_RIGHT): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0, max=5, step=0.01, mode="box", unit_of_measurement="m"
            )
        ),
        vol.Optional(CONF_REVEAL_TOP): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0, max=5, step=0.01, mode="box", unit_of_measurement="m"
            )
        ),
        vol.Optional(
            CONF_HORIZON_PROFILE, default=HORIZON_PROFILE_EXAMPLE
        ): selector.TextSelector(
            selector.TextSelectorConfig(multiline=True)
        ),
        vol.Optional(CONF_GLASS_TYPE, default="double_clear"): selector.SelectSelector(
            selector.SelectSelectorConfig(options=GLASS_TYPE_OPTIONS)
        ),
        vol.Optional(CONF_WEATHER_ENTITY, default=vol.UNDEFINED): selector.EntitySelector(
            selector.EntityFilterSelectorConfig(domain="weather")
        ),
    }
)

VERTICAL_OPTIONS = vol.Schema(
    {
        vol.Optional(CONF_ENTITIES, default=[]): selector.EntitySelector(
            selector.EntitySelectorConfig(
                multiple=True,
                filter=selector.EntityFilterSelectorConfig(domain="cover"),
            )
        ),
        vol.Required(CONF_HEIGHT_WIN, default=2.1): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0.1, max=6, step=0.01, mode="slider", unit_of_measurement="m"
            )
        ),
        vol.Required(CONF_DISTANCE, default=0.5): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0.1, max=2, step=0.1, mode="slider", unit_of_measurement="m"
            )
        ),
    }
).extend(OPTIONS.schema)


HORIZONTAL_OPTIONS = vol.Schema(
    {
        vol.Required(CONF_LENGTH_AWNING, default=2.1): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0.3, max=6, step=0.01, mode="slider", unit_of_measurement="m"
            )
        ),
        vol.Required(CONF_AWNING_ANGLE, default=0): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0, max=45, mode="slider", unit_of_measurement="°"
            )
        ),
    }
).extend(VERTICAL_OPTIONS.schema)

TILT_OPTIONS = vol.Schema(
    {
        vol.Optional(CONF_ENTITIES, default=[]): selector.EntitySelector(
            selector.EntitySelectorConfig(
                multiple=True,
                filter=selector.EntityFilterSelectorConfig(domain="cover"),
            )
        ),
        vol.Required(CONF_TILT_DEPTH, default=3): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0.1, max=15, step=0.1, mode="slider", unit_of_measurement="cm"
            )
        ),
        vol.Required(CONF_TILT_DISTANCE, default=2): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0.1, max=15, step=0.1, mode="slider", unit_of_measurement="cm"
            )
        ),
        vol.Required(CONF_TILT_MODE, default="mode2"): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=["mode1", "mode2"], translation_key="tilt_mode"
            )
        ),
    }
).extend(OPTIONS.schema)

CLIMATE_OPTIONS = vol.Schema(
    {
        vol.Required(CONF_TEMP_ENTITY): selector.EntitySelector(
            selector.EntityFilterSelectorConfig(domain=["climate", "sensor"])
        ),
        vol.Required(CONF_TEMP_LOW, default=21): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0, max=86, step=1, mode="slider", unit_of_measurement="°"
            )
        ),
        vol.Required(CONF_TEMP_HIGH, default=25): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0, max=90, step=1, mode="slider", unit_of_measurement="°"
            )
        ),
        vol.Optional(
            CONF_OUTSIDETEMP_ENTITY, default=vol.UNDEFINED
        ): selector.EntitySelector(
            selector.EntityFilterSelectorConfig(domain=["sensor"])
        ),
        vol.Optional(CONF_OUTSIDE_THRESHOLD, default=0): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=100)
        ),
        vol.Optional(
            CONF_PRESENCE_ENTITY, default=vol.UNDEFINED
        ): selector.EntitySelector(
            selector.EntityFilterSelectorConfig(
                domain=["device_tracker", "zone", "binary_sensor", "input_boolean"]
            )
        ),
        vol.Optional(
            CONF_IRRADIANCE_ENTITY, default=vol.UNDEFINED
        ): selector.EntitySelector(
            selector.EntityFilterSelectorConfig(
                domain=["sensor"], device_class="irradiance"
            )
        ),
        vol.Optional(CONF_IRRADIANCE_THRESHOLD, default=300): selector.NumberSelector(
            selector.NumberSelectorConfig(mode="box", unit_of_measurement="W/m²")
        ),
        vol.Optional(CONF_TRANSPARENT_BLIND, default=False): selector.BooleanSelector(),
    }
)

WEATHER_OPTIONS = vol.Schema(
    {
        vol.Optional(CONF_USE_FORECAST_MAX_TEMP_TODAY, default=False): selector.BooleanSelector(),
        vol.Optional(CONF_USE_FORECAST_MAX_TEMP_TOMORROW, default=False): selector.BooleanSelector(),
        vol.Optional(CONF_USE_OPEN_DATA_SOLAR_RADIATION, default=False): selector.BooleanSelector(),
        vol.Optional(
            CONF_SOLAR_RADIATION_ENTITY, default=vol.UNDEFINED
        ): selector.EntitySelector(
            selector.EntityFilterSelectorConfig(
                domain=["sensor"], device_class="irradiance"
            )
        ),
        vol.Optional(CONF_SOLAR_RADIATION_REFERENCE, default=900): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=300, max=1600, step=50, mode="slider", unit_of_measurement="W/m²"
            )
        ),
        vol.Optional(CONF_FORECAST_HOT_DAY_THRESHOLD, default=26): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0, max=50, step=0.5, mode="box", unit_of_measurement="°C"
            )
        ),
        vol.Optional(
            CONF_FORECAST_VERY_HOT_DAY_THRESHOLD, default=30
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0, max=50, step=0.5, mode="box", unit_of_measurement="°C"
            )
        ),
        vol.Optional(
            CONF_FORECAST_PREEMPTIVE_START_TIME, default="09:00:00"
        ): selector.TimeSelector(),
        vol.Optional(CONF_FORECAST_INFLUENCE_STRENGTH, default=0.5): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0, max=1, step=0.05, mode="slider"
            )
        ),
    }
)

POLICY_OPTIONS = vol.Schema(
    {
        vol.Optional(CONF_ENABLE_HEAT_GAIN_POLICY, default=False): selector.BooleanSelector(),
        vol.Optional(
            CONF_POLICY_PRESET, default="daylight_first_single_aspect"
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=POLICY_PRESET_OPTIONS,
                translation_key="policy_preset",
            )
        ),
        vol.Optional(CONF_HAS_ADDITIONAL_DAYLIGHT_WINDOWS, default=False): selector.BooleanSelector(),
        vol.Optional(CONF_ENABLE_AWAY_MODE, default=False): selector.BooleanSelector(),
        vol.Optional(CONF_AWAY_ENTITY, default=vol.UNDEFINED): selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain=["person", "device_tracker", "zone", "binary_sensor", "input_boolean"]
            )
        ),
        vol.Optional(CONF_AWAY_SCORE_MULTIPLIER, default=1.25): selector.NumberSelector(
            selector.NumberSelectorConfig(min=1, max=2.5, step=0.05, mode="slider")
        ),
        vol.Optional(CONF_AWAY_THRESHOLD_REDUCTION, default=0.1): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=0.5, step=0.01, mode="slider")
        ),
        vol.Optional(CONF_AWAY_POSITION_OFFSET, default=10): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0, max=30, step=1, mode="slider", unit_of_measurement="%"
            )
        ),
        vol.Optional(CONF_HOT_DAY_CLOSE_ENABLED, default=False): selector.BooleanSelector(),
        vol.Optional(CONF_HOT_DAY_CLOSE_THRESHOLD, default=28): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=20, max=40, step=0.5, mode="slider", unit_of_measurement="°C"
            )
        ),
        vol.Optional(CONF_HOT_DAY_CLOSE_POSITION, default=20): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0, max=100, step=1, mode="slider", unit_of_measurement="%"
            )
        ),
        vol.Optional(CONF_VERY_HOT_DAY_CLOSE_POSITION, default=10): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0, max=100, step=1, mode="slider", unit_of_measurement="%"
            )
        ),
        vol.Optional(CONF_HEAT_POWER_LIMIT_ENABLED, default=False): selector.BooleanSelector(),
        vol.Optional(CONF_HEAT_POWER_OUTSIDE_TEMP_THRESHOLD, default=24): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=-10, max=45, step=0.5, mode="slider", unit_of_measurement="Â°C"
            )
        ),
        vol.Optional(CONF_HEAT_PROTECTION_MIN_OUTSIDE_TEMP, default=14): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=-20, max=30, step=0.5, mode="slider", unit_of_measurement="Ã‚Â°C"
            )
        ),
        vol.Optional(
            CONF_MAX_TRANSMITTED_SOLAR_POWER, default=250
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=50, max=800, step=25, mode="slider", unit_of_measurement="W/m2"
            )
        ),
        vol.Optional(CONF_SHOW_EXPERT_WEIGHTS, default=False): selector.BooleanSelector(),
        vol.Optional(CONF_WEIGHT_DIRECT_EXPOSURE, default=1.2): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=3, step=0.05, mode="slider")
        ),
        vol.Optional(CONF_WEIGHT_INCIDENCE, default=0.9): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=3, step=0.05, mode="slider")
        ),
        vol.Optional(CONF_WEIGHT_GLAZING, default=0.8): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=3, step=0.05, mode="slider")
        ),
        vol.Optional(
            CONF_WEIGHT_FORECAST_TEMPERATURE, default=1.0
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=3, step=0.05, mode="slider")
        ),
        vol.Optional(CONF_WEIGHT_SOLAR_RADIATION, default=1.0): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=3, step=0.05, mode="slider")
        ),
        vol.Optional(CONF_PARTIAL_CLOSE_THRESHOLD, default=0.35): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=1, step=0.01, mode="slider")
        ),
        vol.Optional(CONF_FULL_CLOSE_THRESHOLD, default=0.65): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=1, step=0.01, mode="slider")
        ),
        vol.Optional(CONF_PARTIAL_CLOSE_POSITION, default=70): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0, max=100, step=1, mode="slider", unit_of_measurement="%"
            )
        ),
        vol.Optional(CONF_FULL_CLOSE_POSITION, default=30): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0, max=100, step=1, mode="slider", unit_of_measurement="%"
            )
        ),
    }
)


AUTOMATION_CONFIG = vol.Schema(
    {
        vol.Required(CONF_DELTA_POSITION, default=1): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=1, max=90, step=1, mode="slider", unit_of_measurement="%"
            )
        ),
        vol.Optional(CONF_DELTA_TIME, default=2): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=2, mode="box", unit_of_measurement="minutes"
            )
        ),
        vol.Optional(CONF_START_TIME, default="00:00:00"): selector.TimeSelector(),
        vol.Optional(CONF_START_ENTITY): selector.EntitySelector(
            selector.EntitySelectorConfig(domain=["sensor", "input_datetime"])
        ),
        vol.Required(
            CONF_MANUAL_OVERRIDE_DURATION, default={"minutes": 15}
        ): selector.DurationSelector(),
        vol.Required(CONF_MANUAL_OVERRIDE_RESET, default=False): bool,
        vol.Optional(CONF_MANUAL_THRESHOLD): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=99)
        ),
        vol.Optional(CONF_MANUAL_IGNORE_INTERMEDIATE, default=False): bool,
        vol.Optional(CONF_END_TIME, default="00:00:00"): selector.TimeSelector(),
        vol.Optional(CONF_END_ENTITY): selector.EntitySelector(
            selector.EntitySelectorConfig(domain=["sensor", "input_datetime"])
        ),
        vol.Optional(CONF_RETURN_SUNSET, default=False): bool,
    }
)

INTERPOLATION_OPTIONS = vol.Schema(
    {
        vol.Optional(CONF_INTERP_START): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=100)
        ),
        vol.Optional(CONF_INTERP_END): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=100)
        ),
        vol.Optional(CONF_INTERP_LIST, default=[]): selector.SelectSelector(
            selector.SelectSelectorConfig(
                multiple=True, custom_value=True, options=["0", "50", "100"]
            )
        ),
        vol.Optional(CONF_INTERP_LIST_NEW, default=[]): selector.SelectSelector(
            selector.SelectSelectorConfig(
                multiple=True, custom_value=True, options=["0", "50", "100"]
            )
        ),
    }
)


def _get_azimuth_edges(data) -> tuple[int, int]:
    """Calculate azimuth edges."""
    return data[CONF_FOV_LEFT] + data[CONF_FOV_RIGHT]


def _normalize_horizon_profile(value: str | None) -> str | None:
    """Normalize optional horizon profile input."""
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    return value


def _validate_horizon_profile(value: str | None) -> str | None:
    """Validate the optional horizon profile JSON."""
    normalized = _normalize_horizon_profile(value)
    if normalized is None:
        return None

    try:
        profile = json.loads(normalized)
    except json.JSONDecodeError as err:
        raise vol.Invalid("Invalid JSON") from err

    if not isinstance(profile, list) or not profile:
        raise vol.Invalid("Must be a non-empty JSON list")

    last_angle = None
    for item in profile:
        if not isinstance(item, dict):
            raise vol.Invalid("Each horizon point must be an object")
        if "angle" not in item:
            raise vol.Invalid("Each horizon point needs an angle")

        angle = float(item["angle"])
        lower = float(item.get("lower_elevation", 0))
        upper = float(item.get("upper_elevation", 90))

        if not 0 <= angle <= 180:
            raise vol.Invalid("Angles must be within 0..180")
        if not 0 <= lower <= 90:
            raise vol.Invalid("Lower elevation must be within 0..90")
        if not 0 <= upper <= 90:
            raise vol.Invalid("Upper elevation must be within 0..90")
        if upper < lower:
            raise vol.Invalid("Upper elevation must be >= lower elevation")
        if last_angle is not None and angle < last_angle:
            raise vol.Invalid("Angles must be sorted ascending")
        last_angle = angle

    return normalized


def _validate_geometry_input(user_input: dict[str, Any]) -> dict[str, str]:
    """Validate geometry-related config values."""
    errors: dict[str, str] = {}
    _apply_facade_azimuth(user_input)
    try:
        user_input[CONF_HORIZON_PROFILE] = _validate_horizon_profile(
            user_input.get(CONF_HORIZON_PROFILE)
        )
    except vol.Invalid:
        errors[CONF_HORIZON_PROFILE] = "invalid_horizon_profile"

    if (
        any(
            user_input.get(key) not in (None, 0)
            for key in (CONF_REVEAL_LEFT, CONF_REVEAL_RIGHT, CONF_REVEAL_TOP)
        )
        and user_input.get(CONF_WINDOW_WIDTH) in (None, 0)
    ):
        errors[CONF_WINDOW_WIDTH] = "window_width_required_for_reveals"

    return errors


def _apply_facade_azimuth(user_input: dict[str, Any]) -> None:
    """Derive the window azimuth from house/facade reference settings."""
    if not user_input.get(CONF_USE_FACADE_AZIMUTH):
        return
    reference = user_input.get(CONF_FACADE_REFERENCE_AZIMUTH)
    offset = user_input.get(CONF_FACADE_OFFSET)
    if reference is None or offset is None:
        return
    user_input[CONF_AZIMUTH] = int(round((float(reference) + float(offset)) % 360))


def _validate_policy_input(user_input: dict[str, Any]) -> dict[str, str]:
    """Validate heat-gain policy settings."""
    errors: dict[str, str] = {}
    partial_threshold = float(user_input.get(CONF_PARTIAL_CLOSE_THRESHOLD, 0.35) or 0.0)
    full_threshold = float(user_input.get(CONF_FULL_CLOSE_THRESHOLD, 0.65) or 0.0)
    partial_position = int(user_input.get(CONF_PARTIAL_CLOSE_POSITION, 70) or 0)
    full_position = int(user_input.get(CONF_FULL_CLOSE_POSITION, 30) or 0)

    if full_threshold < partial_threshold:
        errors[CONF_FULL_CLOSE_THRESHOLD] = "full_threshold_must_exceed_partial"
    if user_input.get(CONF_ENABLE_AWAY_MODE) and not user_input.get(CONF_AWAY_ENTITY):
        errors[CONF_AWAY_ENTITY] = "away_entity_required"

    return errors


class ConfigFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle ConfigFlow."""

    def __init__(self) -> None:  # noqa: D107
        super().__init__()
        self.type_blind: str | None = None
        self.config: dict[str, Any] = {}
        self.mode: str = "basic"

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)

    def optional_entities(self, keys: list, user_input: dict[str, Any] | None = None):
        """Set optional entity fields to None when the form omits them."""
        if user_input is None:
            return
        for key in keys:
            if key not in user_input:
                user_input[key] = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        # errors = {}
        if user_input:
            selected_mode = user_input.get(CONF_MODE, SensorType.BLIND)
            name = user_input["name"]
            template_entry = user_input.get(CONF_TEMPLATE_ENTRY)
            self.config = _template_options(self.hass, template_entry)
            self.config.update(user_input)
            self.config["name"] = name
            self.config[CONF_MODE] = selected_mode
            if selected_mode == SensorType.BLIND:
                return await self.async_step_vertical()
            if selected_mode == SensorType.AWNING:
                return await self.async_step_horizontal()
            if selected_mode == SensorType.TILT:
                return await self.async_step_tilt()
        return self.async_show_form(
            step_id="user", data_schema=_config_schema(self.hass)
        )

    async def async_step_vertical(self, user_input: dict[str, Any] | None = None):
        """Show basic config for vertical blinds."""
        self.type_blind = SensorType.BLIND
        if user_input is not None:
            geometry_errors = _validate_geometry_input(user_input)
            if geometry_errors:
                return self.async_show_form(
                    step_id="vertical",
                    data_schema=CLIMATE_MODE.extend(VERTICAL_OPTIONS.schema),
                    errors=geometry_errors,
                )
            if (
                user_input.get(CONF_MAX_ELEVATION) is not None
                and user_input.get(CONF_MIN_ELEVATION) is not None
            ):
                if user_input[CONF_MAX_ELEVATION] <= user_input[CONF_MIN_ELEVATION]:
                    return self.async_show_form(
                        step_id="vertical",
                        data_schema=CLIMATE_MODE.extend(VERTICAL_OPTIONS.schema),
                        errors={
                            CONF_MAX_ELEVATION: "Must be greater than 'Minimal Elevation'"
                        },
                    )
            self.config.update(user_input)
            if self.config.get(CONF_INTERP, False):
                return await self.async_step_interp()
            if self.config.get(CONF_ENABLE_BLIND_SPOT, False):
                return await self.async_step_blind_spot()
            return await self.async_step_automation()
        return self.async_show_form(
            step_id="vertical",
            data_schema=self.add_suggested_values_to_schema(
                CLIMATE_MODE.extend(VERTICAL_OPTIONS.schema), self.config
            ),
        )

    async def async_step_horizontal(self, user_input: dict[str, Any] | None = None):
        """Show basic config for horizontal blinds."""
        self.type_blind = SensorType.AWNING
        if user_input is not None:
            geometry_errors = _validate_geometry_input(user_input)
            if geometry_errors:
                return self.async_show_form(
                    step_id="horizontal",
                    data_schema=CLIMATE_MODE.extend(HORIZONTAL_OPTIONS.schema),
                    errors=geometry_errors,
                )
            if (
                user_input.get(CONF_MAX_ELEVATION) is not None
                and user_input.get(CONF_MIN_ELEVATION) is not None
            ):
                if user_input[CONF_MAX_ELEVATION] <= user_input[CONF_MIN_ELEVATION]:
                    return self.async_show_form(
                        step_id="horizontal",
                        data_schema=CLIMATE_MODE.extend(HORIZONTAL_OPTIONS.schema),
                        errors={
                            CONF_MAX_ELEVATION: "Must be greater than 'Minimal Elevation'"
                        },
                    )
            self.config.update(user_input)
            if self.config.get(CONF_INTERP, False):
                return await self.async_step_interp()
            if self.config.get(CONF_ENABLE_BLIND_SPOT, False):
                return await self.async_step_blind_spot()
            return await self.async_step_automation()
        return self.async_show_form(
            step_id="horizontal",
            data_schema=self.add_suggested_values_to_schema(
                CLIMATE_MODE.extend(HORIZONTAL_OPTIONS.schema), self.config
            ),
        )

    async def async_step_tilt(self, user_input: dict[str, Any] | None = None):
        """Show basic config for tilted blinds."""
        self.type_blind = SensorType.TILT
        if user_input is not None:
            geometry_errors = _validate_geometry_input(user_input)
            if geometry_errors:
                return self.async_show_form(
                    step_id="tilt",
                    data_schema=CLIMATE_MODE.extend(TILT_OPTIONS.schema),
                    errors=geometry_errors,
                )
            if (
                user_input.get(CONF_MAX_ELEVATION) is not None
                and user_input.get(CONF_MIN_ELEVATION) is not None
            ):
                if user_input[CONF_MAX_ELEVATION] <= user_input[CONF_MIN_ELEVATION]:
                    return self.async_show_form(
                        step_id="tilt",
                        data_schema=CLIMATE_MODE.extend(TILT_OPTIONS.schema),
                        errors={
                            CONF_MAX_ELEVATION: "Must be greater than 'Minimal Elevation'"
                        },
                    )
            self.config.update(user_input)
            if self.config.get(CONF_INTERP, False):
                return await self.async_step_interp()
            if self.config.get(CONF_ENABLE_BLIND_SPOT, False):
                return await self.async_step_blind_spot()
            return await self.async_step_automation()
        return self.async_show_form(
            step_id="tilt",
            data_schema=self.add_suggested_values_to_schema(
                CLIMATE_MODE.extend(TILT_OPTIONS.schema), self.config
            ),
        )

    async def async_step_interp(self, user_input: dict[str, Any] | None = None):
        """Show interpolation options."""
        if user_input is not None:
            if len(user_input[CONF_INTERP_LIST]) != len(
                user_input[CONF_INTERP_LIST_NEW]
            ):
                return self.async_show_form(
                    step_id="interp",
                    data_schema=INTERPOLATION_OPTIONS,
                    errors={
                        CONF_INTERP_LIST_NEW: "Must have same length as 'Interpolation' list"
                    },
                )
            self.config.update(user_input)
            if self.config.get(CONF_ENABLE_BLIND_SPOT, False):
                return await self.async_step_blind_spot()
            return await self.async_step_automation()
        return self.async_show_form(
            step_id="interp",
            data_schema=self.add_suggested_values_to_schema(
                INTERPOLATION_OPTIONS, self.config
            ),
        )

    async def async_step_blind_spot(self, user_input: dict[str, Any] | None = None):
        """Add blindspot to data."""
        edges = _get_azimuth_edges(self.config)
        schema = vol.Schema(
            {
                vol.Required(CONF_BLIND_SPOT_LEFT, default=0): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        mode="slider", unit_of_measurement="°", min=0, max=edges - 1
                    )
                ),
                vol.Required(CONF_BLIND_SPOT_RIGHT, default=1): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        mode="slider", unit_of_measurement="°", min=1, max=edges
                    )
                ),
                vol.Optional(CONF_BLIND_SPOT_ELEVATION): vol.All(
                    vol.Coerce(int), vol.Range(min=0, max=90)
                ),
            }
        )
        if user_input is not None:
            if user_input[CONF_BLIND_SPOT_RIGHT] <= user_input[CONF_BLIND_SPOT_LEFT]:
                return self.async_show_form(
                    step_id="blind_spot",
                    data_schema=schema,
                    errors={
                        CONF_BLIND_SPOT_RIGHT: "Must be greater than 'Blind Spot Left Edge'"
                    },
                )
            self.config.update(user_input)
            return await self.async_step_automation()

        return self.async_show_form(step_id="blind_spot", data_schema=schema)

    async def async_step_automation(self, user_input: dict[str, Any] | None = None):
        """Manage automation options."""
        if user_input is not None:
            self.config.update(user_input)
            if self.config.get(CONF_CLIMATE_MODE, False) is True:
                return await self.async_step_climate()
            return await self.async_step_weather()
        return self.async_show_form(
            step_id="automation",
            data_schema=self.add_suggested_values_to_schema(
                AUTOMATION_CONFIG, self.config
            ),
        )

    async def async_step_climate(self, user_input: dict[str, Any] | None = None):
        """Manage climate options."""
        if user_input is not None:
            self.config.update(user_input)
            return await self.async_step_weather()
        return self.async_show_form(
            step_id="climate",
            data_schema=self.add_suggested_values_to_schema(CLIMATE_OPTIONS, self.config),
        )

    async def async_step_weather(self, user_input: dict[str, Any] | None = None):
        """Manage weather conditions."""
        if user_input is not None:
            self.optional_entities([CONF_SOLAR_RADIATION_ENTITY], user_input)
            self.config.update(user_input)
            return await self.async_step_policy()
        return self.async_show_form(
            step_id="weather",
            data_schema=self.add_suggested_values_to_schema(WEATHER_OPTIONS, self.config),
        )

    async def async_step_policy(self, user_input: dict[str, Any] | None = None):
        """Manage heat-gain policy options."""
        if user_input is not None:
            if CONF_AWAY_ENTITY not in user_input:
                user_input[CONF_AWAY_ENTITY] = None
            errors = _validate_policy_input(user_input)
            if errors:
                return self.async_show_form(
                    step_id="policy",
                    data_schema=POLICY_OPTIONS,
                    errors=errors,
                )
            self.config.update(user_input)
            return await self.async_step_update()
        return self.async_show_form(
            step_id="policy",
            data_schema=self.add_suggested_values_to_schema(POLICY_OPTIONS, self.config),
        )

    async def async_step_update(self, user_input: dict[str, Any] | None = None):
        """Create entry."""
        type = {
            "cover_blind": "Vertical",
            "cover_awning": "Horizontal",
            "cover_tilt": "Tilt",
        }
        return self.async_create_entry(
            title=f"{type[self.type_blind]} {self.config['name']}",
            data={
                "name": self.config["name"],
                CONF_SENSOR_TYPE: self.type_blind,
            },
            options={
                CONF_MODE: self.mode,
                CONF_FACADE_NAME: self.config.get(CONF_FACADE_NAME),
                CONF_FLOOR_NAME: self.config.get(CONF_FLOOR_NAME),
                CONF_ROOM_NAME: self.config.get(CONF_ROOM_NAME),
                CONF_USE_FACADE_AZIMUTH: self.config.get(
                    CONF_USE_FACADE_AZIMUTH, False
                ),
                CONF_FACADE_REFERENCE_AZIMUTH: self.config.get(
                    CONF_FACADE_REFERENCE_AZIMUTH
                ),
                CONF_FACADE_OFFSET: self.config.get(CONF_FACADE_OFFSET),
                CONF_AZIMUTH: self.config.get(CONF_AZIMUTH),
                CONF_HEIGHT_WIN: self.config.get(CONF_HEIGHT_WIN),
                CONF_DISTANCE: self.config.get(CONF_DISTANCE),
                CONF_DEFAULT_HEIGHT: self.config.get(CONF_DEFAULT_HEIGHT),
                CONF_MAX_POSITION: self.config.get(CONF_MAX_POSITION),
                CONF_MIN_POSITION: self.config.get(CONF_MIN_POSITION),
                CONF_FOV_LEFT: self.config.get(CONF_FOV_LEFT),
                CONF_FOV_RIGHT: self.config.get(CONF_FOV_RIGHT),
                CONF_ENTITIES: self.config.get(CONF_ENTITIES),
                CONF_INVERSE_STATE: self.config.get(CONF_INVERSE_STATE),
                CONF_SUNSET_POS: self.config.get(CONF_SUNSET_POS),
                CONF_SUNSET_OFFSET: self.config.get(CONF_SUNSET_OFFSET),
                CONF_SUNRISE_OFFSET: self.config.get(CONF_SUNRISE_OFFSET),
                CONF_LENGTH_AWNING: self.config.get(CONF_LENGTH_AWNING),
                CONF_AWNING_ANGLE: self.config.get(CONF_AWNING_ANGLE),
                CONF_TILT_DISTANCE: self.config.get(CONF_TILT_DISTANCE),
                CONF_TILT_DEPTH: self.config.get(CONF_TILT_DEPTH),
                CONF_TILT_MODE: self.config.get(CONF_TILT_MODE),
                CONF_TEMP_ENTITY: self.config.get(CONF_TEMP_ENTITY),
                CONF_PRESENCE_ENTITY: self.config.get(CONF_PRESENCE_ENTITY),
                CONF_WEATHER_ENTITY: self.config.get(CONF_WEATHER_ENTITY),
                CONF_TEMP_LOW: self.config.get(CONF_TEMP_LOW),
                CONF_TEMP_HIGH: self.config.get(CONF_TEMP_HIGH),
                CONF_OUTSIDETEMP_ENTITY: self.config.get(CONF_OUTSIDETEMP_ENTITY),
                CONF_CLIMATE_MODE: self.config.get(CONF_CLIMATE_MODE),
                CONF_DELTA_POSITION: self.config.get(CONF_DELTA_POSITION),
                CONF_DELTA_TIME: self.config.get(CONF_DELTA_TIME),
                CONF_START_TIME: self.config.get(CONF_START_TIME),
                CONF_START_ENTITY: self.config.get(CONF_START_ENTITY),
                CONF_MANUAL_OVERRIDE_DURATION: self.config.get(
                    CONF_MANUAL_OVERRIDE_DURATION
                ),
                CONF_MANUAL_OVERRIDE_RESET: self.config.get(CONF_MANUAL_OVERRIDE_RESET),
                CONF_MANUAL_THRESHOLD: self.config.get(CONF_MANUAL_THRESHOLD),
                CONF_MANUAL_IGNORE_INTERMEDIATE: self.config.get(
                    CONF_MANUAL_IGNORE_INTERMEDIATE
                ),
                CONF_BLIND_SPOT_RIGHT: self.config.get(CONF_BLIND_SPOT_RIGHT, None),
                CONF_BLIND_SPOT_LEFT: self.config.get(CONF_BLIND_SPOT_LEFT, None),
                CONF_BLIND_SPOT_ELEVATION: self.config.get(
                    CONF_BLIND_SPOT_ELEVATION, None
                ),
                CONF_ENABLE_BLIND_SPOT: self.config.get(CONF_ENABLE_BLIND_SPOT),
                CONF_MIN_ELEVATION: self.config.get(CONF_MIN_ELEVATION, None),
                CONF_MAX_ELEVATION: self.config.get(CONF_MAX_ELEVATION, None),
                CONF_TRANSPARENT_BLIND: self.config.get(CONF_TRANSPARENT_BLIND, False),
                CONF_INTERP: self.config.get(CONF_INTERP),
                CONF_INTERP_START: self.config.get(CONF_INTERP_START, None),
                CONF_INTERP_END: self.config.get(CONF_INTERP_END, None),
                CONF_INTERP_LIST: self.config.get(CONF_INTERP_LIST, []),
                CONF_INTERP_LIST_NEW: self.config.get(CONF_INTERP_LIST_NEW, []),
                CONF_HORIZON_PROFILE: self.config.get(CONF_HORIZON_PROFILE),
                CONF_WINDOW_WIDTH: self.config.get(CONF_WINDOW_WIDTH),
                CONF_REVEAL_LEFT: self.config.get(CONF_REVEAL_LEFT),
                CONF_REVEAL_RIGHT: self.config.get(CONF_REVEAL_RIGHT),
                CONF_REVEAL_TOP: self.config.get(CONF_REVEAL_TOP),
                CONF_IRRADIANCE_ENTITY: self.config.get(CONF_IRRADIANCE_ENTITY),
                CONF_IRRADIANCE_THRESHOLD: self.config.get(CONF_IRRADIANCE_THRESHOLD),
                CONF_OUTSIDE_THRESHOLD: self.config.get(CONF_OUTSIDE_THRESHOLD),
                CONF_USE_FORECAST_MAX_TEMP_TODAY: self.config.get(
                    CONF_USE_FORECAST_MAX_TEMP_TODAY, False
                ),
                CONF_USE_FORECAST_MAX_TEMP_TOMORROW: self.config.get(
                    CONF_USE_FORECAST_MAX_TEMP_TOMORROW, False
                ),
                CONF_USE_OPEN_DATA_SOLAR_RADIATION: self.config.get(
                    CONF_USE_OPEN_DATA_SOLAR_RADIATION, False
                ),
                CONF_SOLAR_RADIATION_ENTITY: self.config.get(
                    CONF_SOLAR_RADIATION_ENTITY
                ),
                CONF_SOLAR_RADIATION_REFERENCE: self.config.get(
                    CONF_SOLAR_RADIATION_REFERENCE, 900
                ),
                CONF_FORECAST_HOT_DAY_THRESHOLD: self.config.get(
                    CONF_FORECAST_HOT_DAY_THRESHOLD
                ),
                CONF_FORECAST_VERY_HOT_DAY_THRESHOLD: self.config.get(
                    CONF_FORECAST_VERY_HOT_DAY_THRESHOLD
                ),
                CONF_FORECAST_PREEMPTIVE_START_TIME: self.config.get(
                    CONF_FORECAST_PREEMPTIVE_START_TIME
                ),
                CONF_FORECAST_INFLUENCE_STRENGTH: self.config.get(
                    CONF_FORECAST_INFLUENCE_STRENGTH, 0.5
                ),
                CONF_ENABLE_HEAT_GAIN_POLICY: self.config.get(
                    CONF_ENABLE_HEAT_GAIN_POLICY, False
                ),
                CONF_POLICY_PRESET: self.config.get(
                    CONF_POLICY_PRESET, "daylight_first_single_aspect"
                ),
                CONF_HAS_ADDITIONAL_DAYLIGHT_WINDOWS: self.config.get(
                    CONF_HAS_ADDITIONAL_DAYLIGHT_WINDOWS, False
                ),
                CONF_ENABLE_AWAY_MODE: self.config.get(CONF_ENABLE_AWAY_MODE, False),
                CONF_AWAY_ENTITY: self.config.get(CONF_AWAY_ENTITY),
                CONF_AWAY_SCORE_MULTIPLIER: self.config.get(
                    CONF_AWAY_SCORE_MULTIPLIER, 1.25
                ),
                CONF_AWAY_THRESHOLD_REDUCTION: self.config.get(
                    CONF_AWAY_THRESHOLD_REDUCTION, 0.1
                ),
                CONF_AWAY_POSITION_OFFSET: self.config.get(
                    CONF_AWAY_POSITION_OFFSET, 10
                ),
                CONF_HOT_DAY_CLOSE_ENABLED: self.config.get(
                    CONF_HOT_DAY_CLOSE_ENABLED, False
                ),
                CONF_HOT_DAY_CLOSE_THRESHOLD: self.config.get(
                    CONF_HOT_DAY_CLOSE_THRESHOLD, 28
                ),
                CONF_HOT_DAY_CLOSE_POSITION: self.config.get(
                    CONF_HOT_DAY_CLOSE_POSITION, 20
                ),
                CONF_VERY_HOT_DAY_CLOSE_POSITION: self.config.get(
                    CONF_VERY_HOT_DAY_CLOSE_POSITION, 10
                ),
                CONF_HEAT_POWER_LIMIT_ENABLED: self.config.get(
                    CONF_HEAT_POWER_LIMIT_ENABLED, False
                ),
                CONF_HEAT_POWER_OUTSIDE_TEMP_THRESHOLD: self.config.get(
                    CONF_HEAT_POWER_OUTSIDE_TEMP_THRESHOLD, 24
                ),
                CONF_HEAT_PROTECTION_MIN_OUTSIDE_TEMP: self.config.get(
                    CONF_HEAT_PROTECTION_MIN_OUTSIDE_TEMP, 14
                ),
                CONF_MAX_TRANSMITTED_SOLAR_POWER: self.config.get(
                    CONF_MAX_TRANSMITTED_SOLAR_POWER,
                    self.config.get(LEGACY_MAX_TRANSMITTED_SOLAR_POWER, 250),
                ),
                CONF_SHOW_EXPERT_WEIGHTS: self.config.get(
                    CONF_SHOW_EXPERT_WEIGHTS, False
                ),
                CONF_WEIGHT_DIRECT_EXPOSURE: self.config.get(
                    CONF_WEIGHT_DIRECT_EXPOSURE, 1.2
                ),
                CONF_WEIGHT_INCIDENCE: self.config.get(CONF_WEIGHT_INCIDENCE, 0.9),
                CONF_WEIGHT_GLAZING: self.config.get(CONF_WEIGHT_GLAZING, 0.8),
                CONF_WEIGHT_FORECAST_TEMPERATURE: self.config.get(
                    CONF_WEIGHT_FORECAST_TEMPERATURE, 1.0
                ),
                CONF_WEIGHT_SOLAR_RADIATION: self.config.get(
                    CONF_WEIGHT_SOLAR_RADIATION, 1.0
                ),
                CONF_PARTIAL_CLOSE_THRESHOLD: self.config.get(
                    CONF_PARTIAL_CLOSE_THRESHOLD, 0.35
                ),
                CONF_FULL_CLOSE_THRESHOLD: self.config.get(
                    CONF_FULL_CLOSE_THRESHOLD, 0.65
                ),
                CONF_PARTIAL_CLOSE_POSITION: self.config.get(
                    CONF_PARTIAL_CLOSE_POSITION, 70
                ),
                CONF_FULL_CLOSE_POSITION: self.config.get(
                    CONF_FULL_CLOSE_POSITION, 30
                ),
            },
        )


class OptionsFlowHandler(OptionsFlow):
    """Options to adjust parameters."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.current_config: dict = dict(config_entry.data)
        self.options = _migrate_retired_options(dict(config_entry.options))
        self.sensor_type: SensorType = (
            self.current_config.get(CONF_SENSOR_TYPE) or SensorType.BLIND
        )

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        options = ["automation", "blind"]
        if self.options.get(CONF_CLIMATE_MODE, False):
            options.append("climate")
        options.append("weather")
        options.append("policy")
        if self.options.get(CONF_ENABLE_BLIND_SPOT, False):
            options.append("blind_spot")
        if self.options.get(CONF_INTERP, False):
            options.append("interp")
        return self.async_show_menu(step_id="init", menu_options=options)

    async def async_step_automation(self, user_input: dict[str, Any] | None = None):
        """Manage automation options."""
        if user_input is not None:
            entities = [CONF_START_ENTITY, CONF_END_ENTITY, CONF_MANUAL_THRESHOLD]
            self.optional_entities(entities, user_input)
            self.options.update(user_input)
            return await self._update_options()
        return self.async_show_form(
            step_id="automation",
            data_schema=self.add_suggested_values_to_schema(
                AUTOMATION_CONFIG, user_input or self.options
            ),
        )

    async def async_step_blind(self, user_input: dict[str, Any] | None = None):
        """Adjust blind parameters."""
        if self.sensor_type == SensorType.BLIND:
            return await self.async_step_vertical()
        if self.sensor_type == SensorType.AWNING:
            return await self.async_step_horizontal()
        if self.sensor_type == SensorType.TILT:
            return await self.async_step_tilt()

    async def async_step_vertical(self, user_input: dict[str, Any] | None = None):
        """Show basic config for vertical blinds."""
        self.type_blind = SensorType.BLIND
        schema = CLIMATE_MODE.extend(VERTICAL_OPTIONS.schema)
        if self.options.get(CONF_CLIMATE_MODE, False):
            schema = VERTICAL_OPTIONS
        if user_input is not None:
            keys = [
                CONF_MIN_ELEVATION,
                CONF_MAX_ELEVATION,
                CONF_WEATHER_ENTITY,
            ]
            self.optional_entities(keys, user_input)
            geometry_errors = _validate_geometry_input(user_input)
            if geometry_errors:
                return self.async_show_form(
                    step_id="vertical",
                    data_schema=CLIMATE_MODE.extend(VERTICAL_OPTIONS.schema),
                    errors=geometry_errors,
                )
            if (
                user_input.get(CONF_MAX_ELEVATION) is not None
                and user_input.get(CONF_MIN_ELEVATION) is not None
            ):
                if user_input[CONF_MAX_ELEVATION] <= user_input[CONF_MIN_ELEVATION]:
                    return self.async_show_form(
                        step_id="vertical",
                        data_schema=CLIMATE_MODE.extend(VERTICAL_OPTIONS.schema),
                        errors={
                            CONF_MAX_ELEVATION: "Must be greater than 'Minimal Elevation'"
                        },
                    )
            self.options.update(user_input)
            if self.options.get(CONF_INTERP, False):
                return await self.async_step_interp()
            if self.options.get(CONF_ENABLE_BLIND_SPOT, False):
                return await self.async_step_blind_spot()
            if self.options.get(CONF_CLIMATE_MODE, False):
                return await self.async_step_climate()
            return await self.async_step_weather()
        return self.async_show_form(
            step_id="vertical",
            data_schema=self.add_suggested_values_to_schema(
                schema, user_input or self.options
            ),
        )

    async def async_step_horizontal(self, user_input: dict[str, Any] | None = None):
        """Show basic config for horizontal blinds."""
        self.type_blind = SensorType.AWNING
        schema = CLIMATE_MODE.extend(HORIZONTAL_OPTIONS.schema)
        if self.options.get(CONF_CLIMATE_MODE, False):
            schema = HORIZONTAL_OPTIONS
        if user_input is not None:
            keys = [
                CONF_MIN_ELEVATION,
                CONF_MAX_ELEVATION,
                CONF_WEATHER_ENTITY,
            ]
            self.optional_entities(keys, user_input)
            geometry_errors = _validate_geometry_input(user_input)
            if geometry_errors:
                return self.async_show_form(
                    step_id="horizontal",
                    data_schema=CLIMATE_MODE.extend(HORIZONTAL_OPTIONS.schema),
                    errors=geometry_errors,
                )
            if (
                user_input.get(CONF_MAX_ELEVATION) is not None
                and user_input.get(CONF_MIN_ELEVATION) is not None
            ):
                if user_input[CONF_MAX_ELEVATION] <= user_input[CONF_MIN_ELEVATION]:
                    return self.async_show_form(
                        step_id="horizontal",
                        data_schema=CLIMATE_MODE.extend(HORIZONTAL_OPTIONS.schema),
                        errors={
                            CONF_MAX_ELEVATION: "Must be greater than 'Minimal Elevation'"
                        },
                    )
            self.options.update(user_input)
            if self.options.get(CONF_CLIMATE_MODE, False):
                return await self.async_step_climate()
            return await self.async_step_weather()
        return self.async_show_form(
            step_id="horizontal",
            data_schema=self.add_suggested_values_to_schema(
                schema, user_input or self.options
            ),
        )

    async def async_step_tilt(self, user_input: dict[str, Any] | None = None):
        """Show basic config for tilted blinds."""
        self.type_blind = SensorType.TILT
        schema = CLIMATE_MODE.extend(TILT_OPTIONS.schema)
        if self.options.get(CONF_CLIMATE_MODE, False):
            schema = TILT_OPTIONS
        if user_input is not None:
            keys = [
                CONF_MIN_ELEVATION,
                CONF_MAX_ELEVATION,
                CONF_WEATHER_ENTITY,
            ]
            self.optional_entities(keys, user_input)
            geometry_errors = _validate_geometry_input(user_input)
            if geometry_errors:
                return self.async_show_form(
                    step_id="tilt",
                    data_schema=CLIMATE_MODE.extend(TILT_OPTIONS.schema),
                    errors=geometry_errors,
                )
            if (
                user_input.get(CONF_MAX_ELEVATION) is not None
                and user_input.get(CONF_MIN_ELEVATION) is not None
            ):
                if user_input[CONF_MAX_ELEVATION] <= user_input[CONF_MIN_ELEVATION]:
                    return self.async_show_form(
                        step_id="tilt",
                        data_schema=CLIMATE_MODE.extend(TILT_OPTIONS.schema),
                        errors={
                            CONF_MAX_ELEVATION: "Must be greater than 'Minimal Elevation'"
                        },
                    )
            self.options.update(user_input)
            if self.options.get(CONF_CLIMATE_MODE, False):
                return await self.async_step_climate()
            return await self.async_step_weather()
        return self.async_show_form(
            step_id="tilt",
            data_schema=self.add_suggested_values_to_schema(
                schema, user_input or self.options
            ),
        )

    async def async_step_interp(self, user_input: dict[str, Any] | None = None):
        """Show interpolation options."""
        if user_input is not None:
            if len(user_input[CONF_INTERP_LIST]) != len(
                user_input[CONF_INTERP_LIST_NEW]
            ):
                return self.async_show_form(
                    step_id="interp",
                    data_schema=INTERPOLATION_OPTIONS,
                    errors={
                        CONF_INTERP_LIST_NEW: "Must have same length as 'Interpolation' list"
                    },
                )
            self.options.update(user_input)
            return await self._update_options()
        return self.async_show_form(
            step_id="interp",
            data_schema=self.add_suggested_values_to_schema(
                INTERPOLATION_OPTIONS, user_input or self.options
            ),
        )

    async def async_step_blind_spot(self, user_input: dict[str, Any] | None = None):
        """Add blindspot to data."""
        edges = _get_azimuth_edges(self.options)
        schema = vol.Schema(
            {
                vol.Required(CONF_BLIND_SPOT_LEFT, default=0): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        mode="slider", unit_of_measurement="°", min=0, max=edges - 1
                    )
                ),
                vol.Required(CONF_BLIND_SPOT_RIGHT, default=1): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        mode="slider", unit_of_measurement="°", min=1, max=edges
                    )
                ),
                vol.Optional(CONF_BLIND_SPOT_ELEVATION): vol.All(
                    vol.Coerce(int), vol.Range(min=0, max=90)
                ),
            }
        )
        if user_input is not None:
            if user_input[CONF_BLIND_SPOT_RIGHT] <= user_input[CONF_BLIND_SPOT_LEFT]:
                return self.async_show_form(
                    step_id="blind_spot",
                    data_schema=schema,
                    errors={
                        CONF_BLIND_SPOT_RIGHT: "Must be greater than 'Blind Spot Left Edge'"
                    },
                )
            self.options.update(user_input)
            return await self._update_options()
        return self.async_show_form(
            step_id="blind_spot",
            data_schema=self.add_suggested_values_to_schema(
                schema, user_input or self.options
            ),
        )

    async def async_step_climate(self, user_input: dict[str, Any] | None = None):
        """Manage climate options."""
        if user_input is not None:
            entities = [
                CONF_OUTSIDETEMP_ENTITY,
                CONF_PRESENCE_ENTITY,
                CONF_IRRADIANCE_ENTITY,
            ]
            self.optional_entities(entities, user_input)
            self.options.update(user_input)
            return await self.async_step_weather()
        return self.async_show_form(
            step_id="climate",
            data_schema=self.add_suggested_values_to_schema(
                CLIMATE_OPTIONS, user_input or self.options
            ),
        )

    async def async_step_weather(self, user_input: dict[str, Any] | None = None):
        """Manage weather conditions."""
        if user_input is not None:
            self.optional_entities([CONF_SOLAR_RADIATION_ENTITY], user_input)
            self.options.update(user_input)
            return await self._update_options()
        return self.async_show_form(
            step_id="weather",
            data_schema=self.add_suggested_values_to_schema(
                WEATHER_OPTIONS, user_input or self.options
            ),
        )

    async def async_step_policy(self, user_input: dict[str, Any] | None = None):
        """Manage heat-gain policy settings."""
        if user_input is not None:
            if CONF_AWAY_ENTITY not in user_input:
                user_input[CONF_AWAY_ENTITY] = None
            errors = _validate_policy_input(user_input)
            if errors:
                return self.async_show_form(
                    step_id="policy",
                    data_schema=self.add_suggested_values_to_schema(
                        POLICY_OPTIONS, user_input
                    ),
                    errors=errors,
                )
            self.options.update(user_input)
            return await self._update_options()
        return self.async_show_form(
            step_id="policy",
            data_schema=self.add_suggested_values_to_schema(
                POLICY_OPTIONS, user_input or self.options
            ),
        )

    async def _update_options(self) -> FlowResult:
        """Update config entry options."""
        return self.async_create_entry(title="", data=self.options)

    def optional_entities(self, keys: list, user_input: dict[str, Any] | None = None):
        """Set value to None if key does not exist."""
        for key in keys:
            if key not in user_input:
                user_input[key] = None

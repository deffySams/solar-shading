"""Constants for integration_blueprint."""

import logging

DOMAIN = "solar_shading"
LOGGER = logging.getLogger(__package__)
_LOGGER = logging.getLogger(__name__)

ATTR_POSITION = "position"
ATTR_TILT_POSITION = "tilt_position"

CONF_AZIMUTH = "set_azimuth"
CONF_BLUEPRINT = "blueprint"
CONF_HEIGHT_WIN = "window_height"
CONF_DISTANCE = "distance_shaded_area"
CONF_DEFAULT_HEIGHT = "default_percentage"
CONF_FOV_LEFT = "fov_left"
CONF_FOV_RIGHT = "fov_right"
CONF_ENTITIES = "group"
CONF_HEIGHT_AWNING = "height_awning"
CONF_LENGTH_AWNING = "length_awning"
CONF_AWNING_ANGLE = "angle"
CONF_SENSOR_TYPE = "sensor_type"
CONF_INVERSE_STATE = "inverse_state"
CONF_SUNSET_POS = "sunset_position"
CONF_SUNSET_OFFSET = "sunset_offset"
CONF_TILT_DEPTH = "slat_depth"
CONF_TILT_DISTANCE = "slat_distance"
CONF_TILT_MODE = "tilt_mode"
CONF_SUNSET_POS = "sunset_position"
CONF_SUNSET_OFFSET = "sunset_offset"
CONF_SUNRISE_OFFSET = "sunrise_offset"
CONF_TEMP_ENTITY = "temp_entity"
CONF_PRESENCE_ENTITY = "presence_entity"
CONF_WEATHER_ENTITY = "weather_entity"
CONF_TEMP_LOW = "temp_low"
CONF_TEMP_HIGH = "temp_high"
CONF_MODE = "mode"
CONF_CLIMATE_MODE = "climate_mode"
CONF_WEATHER_STATE = "weather_state"
CONF_MAX_POSITION = "max_position"
CONF_MIN_POSITION = "min_position"
CONF_ENABLE_MAX_POSITION = "enable_max_position"
CONF_ENABLE_MIN_POSITION = "enable_min_position"
CONF_OUTSIDETEMP_ENTITY = "outside_temp"
CONF_ENABLE_BLIND_SPOT = "blind_spot"
CONF_BLIND_SPOT_RIGHT = "blind_spot_right"
CONF_BLIND_SPOT_LEFT = "blind_spot_left"
CONF_BLIND_SPOT_ELEVATION = "blind_spot_elevation"
CONF_MIN_ELEVATION = "min_elevation"
CONF_MAX_ELEVATION = "max_elevation"
CONF_TRANSPARENT_BLIND = "transparent_blind"
CONF_INTERP_START = "interp_start"
CONF_INTERP_END = "interp_end"
CONF_INTERP_LIST = "interp_list"
CONF_INTERP_LIST_NEW = "interp_list_new"
CONF_INTERP = "interp"
CONF_LUX_ENTITY = "lux_entity"
CONF_LUX_THRESHOLD = "lux_threshold"
CONF_IRRADIANCE_ENTITY = "irradiance_entity"
CONF_IRRADIANCE_THRESHOLD = "irradiance_threshold"
CONF_OUTSIDE_THRESHOLD = "outside_threshold"
CONF_HORIZON_PROFILE = "horizon_profile"
CONF_WINDOW_WIDTH = "window_width"
CONF_REVEAL_LEFT = "reveal_left_depth"
CONF_REVEAL_RIGHT = "reveal_right_depth"
CONF_REVEAL_TOP = "reveal_top_depth"
CONF_GLASS_TYPE = "glass_type"
CONF_USE_FORECAST_MAX_TEMP_TODAY = "use_forecast_max_temp_today"
CONF_USE_FORECAST_MAX_TEMP_TOMORROW = "use_forecast_max_temp_tomorrow"
CONF_USE_FORECAST_CLOUD_COVERAGE = "use_forecast_cloud_coverage"
CONF_USE_FORECAST_PRECIPITATION_PROBABILITY = (
    "use_forecast_precipitation_probability"
)
CONF_USE_FORECAST_PRECIPITATION_AMOUNT = "use_forecast_precipitation_amount"
CONF_USE_FORECAST_UV_INDEX = "use_forecast_uv_index"
CONF_USE_OPEN_DATA_SOLAR_RADIATION = "use_open_data_solar_radiation"
CONF_SOLAR_RADIATION_ENTITY = "solar_radiation_entity"
CONF_SOLAR_RADIATION_REFERENCE = "solar_radiation_reference_w_m2"
CONF_HEAT_POWER_LIMIT_ENABLED = "heat_power_limit_enabled"
CONF_HEAT_POWER_OUTSIDE_TEMP_THRESHOLD = "heat_power_outside_temp_threshold"
CONF_HEAT_PROTECTION_MIN_OUTSIDE_TEMP = "heat_protection_min_outside_temp"
CONF_HEAT_POWER_MAX_WATTS = "heat_power_max_watts"
CONF_FORECAST_HOT_DAY_THRESHOLD = "forecast_hot_day_threshold"
CONF_FORECAST_VERY_HOT_DAY_THRESHOLD = "forecast_very_hot_day_threshold"
CONF_FORECAST_PREEMPTIVE_START_TIME = "forecast_preemptive_start_time"
CONF_FORECAST_INFLUENCE_STRENGTH = "forecast_influence_strength"
CONF_ENABLE_HEAT_GAIN_POLICY = "enable_heat_gain_policy"
CONF_POLICY_PRESET = "policy_preset"
CONF_HAS_ADDITIONAL_DAYLIGHT_WINDOWS = "has_additional_daylight_windows"
CONF_ENABLE_AWAY_MODE = "enable_away_mode"
CONF_AWAY_ENTITY = "away_entity"
CONF_AWAY_SCORE_MULTIPLIER = "away_score_multiplier"
CONF_AWAY_THRESHOLD_REDUCTION = "away_threshold_reduction"
CONF_AWAY_POSITION_OFFSET = "away_position_offset"
CONF_HOT_DAY_CLOSE_ENABLED = "hot_day_close_enabled"
CONF_HOT_DAY_CLOSE_THRESHOLD = "hot_day_close_threshold"
CONF_HOT_DAY_CLOSE_POSITION = "hot_day_close_position"
CONF_VERY_HOT_DAY_CLOSE_POSITION = "very_hot_day_close_position"
CONF_ENABLE_LEGACY_BASIC_SHADING = "enable_legacy_basic_shading"
CONF_SHOW_EXPERT_WEIGHTS = "show_expert_weights"
CONF_WEIGHT_DIRECT_EXPOSURE = "weight_direct_exposure"
CONF_WEIGHT_INCIDENCE = "weight_incidence"
CONF_WEIGHT_GLAZING = "weight_glazing"
CONF_WEIGHT_WEATHER = "weight_weather"
CONF_WEIGHT_FORECAST_TEMPERATURE = "weight_forecast_temperature"
CONF_WEIGHT_FORECAST_UV = "weight_forecast_uv"
CONF_WEIGHT_FORECAST_CLOUDS = "weight_forecast_clouds"
CONF_WEIGHT_FORECAST_PRECIPITATION_PROBABILITY = (
    "weight_forecast_precipitation_probability"
)
CONF_WEIGHT_FORECAST_PRECIPITATION_AMOUNT = (
    "weight_forecast_precipitation_amount"
)
CONF_WEIGHT_SOLAR_RADIATION = "weight_solar_radiation"
CONF_PARTIAL_CLOSE_THRESHOLD = "partial_close_threshold"
CONF_FULL_CLOSE_THRESHOLD = "full_close_threshold"
CONF_PARTIAL_CLOSE_POSITION = "partial_close_position"
CONF_FULL_CLOSE_POSITION = "full_close_position"

GLASS_TYPE_OPTIONS = [
    "single_clear",
    "double_clear",
    "double_low_e",
    "triple_clear",
    "triple_low_e",
    "solar_control",
]

POLICY_PRESET_OPTIONS = [
    "custom",
    "daylight_first_single_aspect",
    "daylight_first_multi_aspect",
    "balanced",
    "cooling_first",
]


CONF_DELTA_POSITION = "delta_position"
CONF_DELTA_TIME = "delta_time"
CONF_START_TIME = "start_time"
CONF_START_ENTITY = "start_entity"
CONF_END_TIME = "end_time"
CONF_END_ENTITY = "end_entity"
CONF_RETURN_SUNSET = "return_sunset"
CONF_MANUAL_OVERRIDE_DURATION = "manual_override_duration"
CONF_MANUAL_OVERRIDE_RESET = "manual_override_reset"
CONF_MANUAL_THRESHOLD = "manual_threshold"
CONF_MANUAL_IGNORE_INTERMEDIATE = "manual_ignore_intermediate"

STRATEGY_MODE_BASIC = "basic"
STRATEGY_MODE_CLIMATE = "climate"
STRATEGY_MODES = [
    STRATEGY_MODE_BASIC,
    STRATEGY_MODE_CLIMATE,
]


class SensorType:
    """Possible modes for a number selector."""

    BLIND = "cover_blind"
    AWNING = "cover_awning"
    TILT = "cover_tilt"

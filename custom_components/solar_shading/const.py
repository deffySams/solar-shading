"""Constants for integration_blueprint."""

import logging

DOMAIN = "solar_shading"
LOGGER = logging.getLogger(__package__)
_LOGGER = logging.getLogger(__name__)

ATTR_POSITION = "position"
ATTR_TILT_POSITION = "tilt_position"

CONF_AZIMUTH = "set_azimuth"
CONF_HEIGHT_WIN = "window_height"
CONF_DISTANCE = "distance_shaded_area"
CONF_DEFAULT_HEIGHT = "default_percentage"
CONF_FOV_LEFT = "fov_left"
CONF_FOV_RIGHT = "fov_right"
CONF_ENTITIES = "group"
CONF_LENGTH_AWNING = "length_awning"
CONF_AWNING_ANGLE = "angle"
CONF_SENSOR_TYPE = "sensor_type"
CONF_INVERSE_STATE = "inverse_state"
CONF_SUNSET_POS = "sunset_position"
CONF_SUNSET_OFFSET = "sunset_offset"
CONF_TILT_DEPTH = "slat_depth"
CONF_TILT_DISTANCE = "slat_distance"
CONF_TILT_MODE = "tilt_mode"
CONF_SUNRISE_OFFSET = "sunrise_offset"
CONF_TEMP_ENTITY = "temp_entity"
CONF_PRESENCE_ENTITY = "presence_entity"
CONF_WEATHER_ENTITY = "weather_entity"
CONF_TEMP_LOW = "temp_low"
CONF_TEMP_HIGH = "temp_high"
CONF_MODE = "mode"
CONF_CLIMATE_MODE = "climate_mode"
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
CONF_IRRADIANCE_ENTITY = "irradiance_entity"
CONF_IRRADIANCE_THRESHOLD = "irradiance_threshold"
CONF_OUTSIDE_THRESHOLD = "outside_threshold"
CONF_HORIZON_PROFILE = "horizon_profile"
CONF_WINDOW_WIDTH = "window_width"
CONF_REVEAL_LEFT = "reveal_left_depth"
CONF_REVEAL_RIGHT = "reveal_right_depth"
CONF_REVEAL_TOP = "reveal_top_depth"
CONF_GLASS_TYPE = "glass_type"
CONF_TEMPLATE_ENTRY = "template_entry"
CONF_ENTRY_TYPE = "entry_type"
CONF_HOUSE_PROFILE_ENTRY_ID = "house_profile_entry_id"
CONF_HOUSE_REFERENCE_AZIMUTH = "house_reference_azimuth"
CONF_HOUSE_DEFAULTS = "house_defaults"
CONF_FLOOR_PROFILES = "floor_profiles"
CONF_FACADE_PROFILES = "facade_profiles"
CONF_ROOM_PROFILES = "room_profiles"
CONF_ROOM_FACADE_PROFILES = "room_facade_profiles"
CONF_PROFILE_OVERRIDES = "overrides"
CONF_PROFILE_ACTION = "profile_action"
CONF_PROFILE_NAME = "profile_name"
CONF_PROFILE_DELETE = "delete_profile"
CONF_USE_LOCAL_GEOMETRY = "use_local_geometry"
CONF_USE_LOCAL_HORIZON = "use_local_horizon"
CONF_USE_LOCAL_POLICY = "use_local_policy"
CONF_WINDOW_OVERRIDES = "window_overrides"
CONF_BULK_WINDOW_ENTRIES = "bulk_window_entries"
CONF_BULK_RESET_LOCAL_OVERRIDES = "bulk_reset_local_overrides"
CONF_BULK_FACADE_ROTATION = "bulk_facade_rotation"
CONF_HORIZON_MODE = "horizon_mode"
CONF_NIGHT_MODE = "night_mode"
CONF_NIGHT_START_TIME = "night_start_time"
CONF_NIGHT_END_TIME = "night_end_time"
CONF_NIGHT_EVENING_MODE = "night_evening_mode"
CONF_NIGHT_MORNING_MODE = "night_morning_mode"
CONF_NIGHT_EVENING_EARLIEST_TIME = "night_evening_earliest_time"
CONF_NIGHT_EVENING_LATEST_TIME = "night_evening_latest_time"
CONF_NIGHT_MORNING_EARLIEST_TIME = "night_morning_earliest_time"
CONF_NIGHT_MORNING_LATEST_TIME = "night_morning_latest_time"
CONF_COVER_LOCATION = "cover_location"
CONF_HEAT_PROTECTION_CONTROL_MODE = "heat_protection_control_mode"
CONF_BINARY_CLOSE_THRESHOLD = "binary_close_threshold_w_m2"
CONF_BINARY_CLOSE_POSITION = "binary_close_position"
CONF_FACADE_NAME = "facade_name"
CONF_FLOOR_NAME = "floor_name"
CONF_ROOM_NAME = "room_name"
CONF_USE_FACADE_AZIMUTH = "use_facade_azimuth"
CONF_FACADE_REFERENCE_AZIMUTH = "facade_reference_azimuth"
CONF_FACADE_OFFSET = "facade_offset"
CONF_USE_FORECAST_MAX_TEMP_TODAY = "use_forecast_max_temp_today"
CONF_USE_FORECAST_MAX_TEMP_TOMORROW = "use_forecast_max_temp_tomorrow"
CONF_USE_OPEN_DATA_SOLAR_RADIATION = "use_open_data_solar_radiation"
CONF_SOLAR_RADIATION_ENTITY = "solar_radiation_entity"
CONF_SOLAR_RADIATION_REFERENCE = "solar_radiation_reference_w_m2"
CONF_HEAT_POWER_LIMIT_ENABLED = "heat_power_limit_enabled"
CONF_HEAT_POWER_OUTSIDE_TEMP_THRESHOLD = "heat_power_outside_temp_threshold"
CONF_HEAT_PROTECTION_MIN_OUTSIDE_TEMP = "heat_protection_min_outside_temp"
CONF_ROOM_TEMPERATURE_ENTITY = "room_temperature_entity"
CONF_ROOM_HEAT_PROTECTION_THRESHOLD = "room_heat_protection_threshold"
CONF_MAX_TRANSMITTED_SOLAR_POWER = "max_transmitted_solar_power_w_m2"
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
CONF_SHOW_EXPERT_WEIGHTS = "show_expert_weights"
CONF_WEIGHT_DIRECT_EXPOSURE = "weight_direct_exposure"
CONF_WEIGHT_INCIDENCE = "weight_incidence"
CONF_WEIGHT_GLAZING = "weight_glazing"
CONF_WEIGHT_FORECAST_TEMPERATURE = "weight_forecast_temperature"
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

ENTRY_TYPE_WINDOW = "window"
ENTRY_TYPE_HOUSE = "house"
ENTRY_TYPE_OPTIONS = [ENTRY_TYPE_WINDOW, ENTRY_TYPE_HOUSE]

HORIZON_MODE_WINDOW = "window"
HORIZON_MODE_COMPASS = "compass"
HORIZON_MODE_OPTIONS = [HORIZON_MODE_WINDOW, HORIZON_MODE_COMPASS]

NIGHT_MODE_TIME = "time"
NIGHT_MODE_SOLAR = "solar"
NIGHT_MODE_OPTIONS = [NIGHT_MODE_TIME, NIGHT_MODE_SOLAR]
NIGHT_EVENING_FIXED = "fixed"
NIGHT_EVENING_SUNSET = "sunset"
NIGHT_EVENING_MODE_OPTIONS = [NIGHT_EVENING_FIXED, NIGHT_EVENING_SUNSET]
NIGHT_MORNING_FIXED = "fixed"
NIGHT_MORNING_SUNRISE = "sunrise"
NIGHT_MORNING_MODE_OPTIONS = [NIGHT_MORNING_FIXED, NIGHT_MORNING_SUNRISE]
COVER_LOCATION_EXTERIOR = "exterior"
COVER_LOCATION_INTERIOR = "interior"
COVER_LOCATION_OPTIONS = [COVER_LOCATION_EXTERIOR, COVER_LOCATION_INTERIOR]
COVER_CLOSED_RESIDUAL_FACTORS = {
    COVER_LOCATION_EXTERIOR: 0.10,
    COVER_LOCATION_INTERIOR: 0.55,
}

HEAT_PROTECTION_MODE_SCALING = "scaling"
HEAT_PROTECTION_MODE_BINARY = "binary"
HEAT_PROTECTION_MODE_OPTIONS = [
    HEAT_PROTECTION_MODE_SCALING,
    HEAT_PROTECTION_MODE_BINARY,
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


class SensorType:
    """Possible modes for a number selector."""

    BLIND = "cover_blind"
    AWNING = "cover_awning"
    TILT = "cover_tilt"

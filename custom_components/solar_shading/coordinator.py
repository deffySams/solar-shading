"""The Coordinator for Adaptive Cover."""

from __future__ import annotations

import asyncio
import datetime as dt
from dataclasses import dataclass

import numpy as np
import pytz
from homeassistant.components.cover import DOMAIN as COVER_DOMAIN
from homeassistant.components.weather import DOMAIN as WEATHER_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_SET_COVER_POSITION,
    SERVICE_SET_COVER_TILT_POSITION,
)
from homeassistant.core import (
    Event,
    EventStateChangedData,
    HomeAssistant,
    State,
    callback,
)
from homeassistant.helpers.event import async_track_point_in_time
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .calculation import (
    AdaptiveHorizontalCover,
    AdaptiveTiltCover,
    AdaptiveVerticalCover,
    NormalCoverState,
)
from .compat import state_attr
from .config_context_adapter import ConfigContextAdapter
from .const import (
    _LOGGER,
    ATTR_POSITION,
    ATTR_TILT_POSITION,
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
    CONF_FACADE_NAME,
    CONF_FACADE_OFFSET,
    CONF_FACADE_REFERENCE_AZIMUTH,
    CONF_FLOOR_NAME,
    CONF_FORECAST_HOT_DAY_THRESHOLD,
    CONF_FORECAST_INFLUENCE_STRENGTH,
    CONF_FORECAST_PREEMPTIVE_START_TIME,
    CONF_FORECAST_VERY_HOT_DAY_THRESHOLD,
    CONF_FOV_LEFT,
    CONF_FOV_RIGHT,
    CONF_FULL_CLOSE_POSITION,
    CONF_FULL_CLOSE_THRESHOLD,
    CONF_GLASS_TYPE,
    CONF_HAS_ADDITIONAL_DAYLIGHT_WINDOWS,
    CONF_HEAT_POWER_LIMIT_ENABLED,
    CONF_HEAT_PROTECTION_CONTROL_MODE,
    CONF_HEAT_PROTECTION_MIN_OUTSIDE_TEMP,
    CONF_HEIGHT_WIN,
    CONF_HORIZON_MODE,
    CONF_HORIZON_PROFILE,
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
    CONF_RETURN_SUNSET,
    CONF_REVEAL_LEFT,
    CONF_REVEAL_RIGHT,
    CONF_REVEAL_TOP,
    CONF_ROOM_HEAT_PROTECTION_THRESHOLD,
    CONF_ROOM_NAME,
    CONF_ROOM_TEMPERATURE_ENTITY,
    CONF_SHOW_EXPERT_WEIGHTS,
    CONF_SOLAR_RADIATION_ENTITY,
    CONF_SOLAR_RADIATION_REFERENCE,
    CONF_START_ENTITY,
    CONF_START_TIME,
    CONF_SUNRISE_OFFSET,
    CONF_SUNSET_OFFSET,
    CONF_SUNSET_POS,
    CONF_TILT_DEPTH,
    CONF_TILT_DISTANCE,
    CONF_TILT_MODE,
    CONF_USE_FACADE_AZIMUTH,
    CONF_USE_FORECAST_MAX_TEMP_TODAY,
    CONF_USE_FORECAST_MAX_TEMP_TOMORROW,
    CONF_USE_OPEN_DATA_SOLAR_RADIATION,
    CONF_WEATHER_ENTITY,
    CONF_WEIGHT_DIRECT_EXPOSURE,
    CONF_WEIGHT_FORECAST_TEMPERATURE,
    CONF_WEIGHT_GLAZING,
    CONF_WEIGHT_INCIDENCE,
    CONF_WEIGHT_SOLAR_RADIATION,
    CONF_WINDOW_WIDTH,
    DOMAIN,
    LOGGER,
)
from .forecast import extract_daily_forecast_summary
from .helpers import get_datetime_from_str, get_last_updated, get_safe_state
from .overview import (
    configuration_warnings,
    derive_window_status,
    estimate_power_with_cover,
)
from .profiles import resolve_effective_options
from .solar_radiation import async_fetch_open_meteo_solar_summary

LEGACY_MAX_TRANSMITTED_SOLAR_POWER = "heat_power_max_watts"


@dataclass
class StateChangedData:
    """StateChangedData class."""

    entity_id: str
    old_state: State | None
    new_state: State | None


@dataclass
class AdaptiveCoverData:
    """AdaptiveCoverData class."""

    states: dict
    attributes: dict


class AdaptiveDataUpdateCoordinator(DataUpdateCoordinator[AdaptiveCoverData]):
    """Adaptive cover data update coordinator."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant) -> None:  # noqa: D107
        super().__init__(hass, LOGGER, name=DOMAIN)

        self.logger = ConfigContextAdapter(_LOGGER)
        self.logger.set_config_name(self.config_entry.data.get("name"))
        self.profile_resolution = resolve_effective_options(hass, self.config_entry)
        self.options = self.profile_resolution.options
        self._cover_type = self.config_entry.data.get("sensor_type")
        self._inverse_state = self.options.get(CONF_INVERSE_STATE, False)
        self._use_interpolation = self.options.get(CONF_INTERP, False)
        self._track_end_time = self.options.get(CONF_RETURN_SUNSET)
        self._control_toggle = None
        self._manual_toggle = None
        self._start_time = None
        self._sun_end_time = None
        self._sun_start_time = None
        # self._end_time = None
        self.manual_reset = self.options.get(
            CONF_MANUAL_OVERRIDE_RESET, False
        )
        self.manual_duration = self.options.get(
            CONF_MANUAL_OVERRIDE_DURATION, {"minutes": 15}
        )
        self.state_change = False
        self.cover_state_change = False
        self.first_refresh = False
        self.timed_refresh = False
        self.state_change_data: StateChangedData | None = None
        self.manager = AdaptiveCoverManager(self.manual_duration, self.logger)
        self.wait_for_target = {}
        self.target_call = {}
        self.ignore_intermediate_states = self.options.get(
            CONF_MANUAL_IGNORE_INTERMEDIATE, False
        )
        self._update_listener = None
        self._scheduled_time = dt.datetime.now()

        self._cached_options = None
        self._forecast_summary: dict | None = None
        self._forecast_cache_entity: str | None = None
        self._forecast_cache_updated: dt.datetime | None = None
        self._forecast_cache_data: dict | None = None
        self._solar_radiation_summary: dict | None = None
        self._solar_radiation_cache_updated: dt.datetime | None = None
        self._solar_radiation_cache_data: dict | None = None

    async def async_config_entry_first_refresh(self) -> None:
        """Config entry first refresh."""
        self.first_refresh = True
        await super().async_config_entry_first_refresh()
        self.logger.debug("Config entry first refresh")

    async def async_timed_refresh(self, event) -> None:
        """Control state at end time."""

        now = dt.datetime.now()
        if self.end_time is not None:
            time = self.end_time
        if self.end_time_entity is not None:
            time = get_safe_state(self.hass, self.end_time_entity)

        self.logger.debug("Checking timed refresh. End time: %s, now: %s", time, now)

        time_check = now - get_datetime_from_str(time)
        if time is not None and (time_check <= dt.timedelta(seconds=1)):
            self.timed_refresh = True
            self.logger.debug("Timed refresh triggered")
            await self.async_refresh()
        else:
            self.logger.debug("Timed refresh, but: not equal to end time")

    async def async_check_entity_state_change(
        self, event: Event[EventStateChangedData]
    ) -> None:
        """Fetch and process state change event."""
        self.logger.debug("Entity state change")
        self.state_change = True
        await self.async_refresh()

    async def async_check_cover_state_change(
        self, event: Event[EventStateChangedData]
    ) -> None:
        """Fetch and process state change event."""
        self.logger.debug("Cover state change")
        data = event.data
        if data["old_state"] is None:
            self.logger.debug("Old state is None")
            return
        self.state_change_data = StateChangedData(
            data["entity_id"], data["old_state"], data["new_state"]
        )
        if self.state_change_data.old_state.state != "unknown":
            self.cover_state_change = True
            self.process_entity_state_change()
            await self.async_refresh()
        else:
            self.logger.debug("Old state is unknown, not processing")

    def process_entity_state_change(self):
        """Process state change event."""
        event = self.state_change_data
        self.logger.debug("Processing state change event: %s", event)
        entity_id = event.entity_id
        if self.ignore_intermediate_states and event.new_state.state in [
            "opening",
            "closing",
        ]:
            self.logger.debug("Ignoring intermediate state change for %s", entity_id)
            return
        if self.wait_for_target.get(entity_id):
            position = event.new_state.attributes.get(
                "current_position"
                if self._cover_type != "cover_tilt"
                else "current_tilt_position"
            )
            if position == self.target_call.get(entity_id):
                self.wait_for_target[entity_id] = False
                self.logger.debug("Position %s reached for %s", position, entity_id)
            self.logger.debug("Wait for target: %s", self.wait_for_target)
        else:
            self.logger.debug("No wait for target call for %s", entity_id)

    @callback
    def _async_cancel_update_listener(self) -> None:
        """Cancel the scheduled update."""
        if self._update_listener:
            self._update_listener()
            self._update_listener = None

    async def async_timed_end_time(self) -> None:
        """Control state at end time."""
        self.logger.debug("Scheduling end time update at %s", self._end_time)
        self._async_cancel_update_listener()
        self.logger.debug(
            "End time: %s, Track end time: %s, Scheduled time: %s, Condition: %s",
            self._end_time,
            self._track_end_time,
            self._scheduled_time,
            self._end_time > self._scheduled_time,
        )
        self._update_listener = async_track_point_in_time(
            self.hass, self.async_timed_refresh, self._end_time
        )
        self._scheduled_time = self._end_time

    async def _async_update_data(self) -> AdaptiveCoverData:
        self.logger.debug("Updating data")
        self.profile_resolution = resolve_effective_options(
            self.hass, self.config_entry
        )
        self.options = self.profile_resolution.options
        if self.first_refresh:
            self._cached_options = self.options

        options = self.options
        self._update_options(options)
        self._forecast_summary = await self._async_get_forecast_summary(
            options.get(CONF_WEATHER_ENTITY)
        )
        self._solar_radiation_summary = await self._async_get_solar_radiation_summary(
            options.get(CONF_USE_OPEN_DATA_SOLAR_RADIATION, False)
        )

        # Get data for the blind
        cover_data = self.get_blind_data(options=options)

        # Update manager with covers
        self._update_manager_and_covers()

        # calculate the state of the cover
        self.normal_cover_state = NormalCoverState(cover_data)
        self.logger.debug(
            "Determined normal cover state to be %s", self.normal_cover_state
        )

        self.default_state = round(self.normal_cover_state.get_state())
        self.logger.debug("Determined default state to be %s", self.default_state)
        state = self.state

        await self.manager.reset_if_needed()

        if (
            self._end_time
            and self._track_end_time
            and self._end_time > self._scheduled_time
        ):
            await self.async_timed_end_time()

        # Handle types of changes
        if self.state_change:
            await self.async_handle_state_change(state, options)
        if self.cover_state_change:
            await self.async_handle_cover_state_change(state)
        if self.first_refresh:
            await self.async_handle_first_refresh(state, options)
        if self.timed_refresh:
            await self.async_handle_timed_refresh(options)

        normal_cover = self.normal_cover_state.cover
        # Run the solar_times method in a separate thread
        if (
            self.first_refresh
            or self._sun_start_time is None
            or dt.datetime.now(pytz.UTC).date() != self._sun_start_time.date()
        ):
            self.logger.debug("Calculating solar times")
            loop = asyncio.get_event_loop()
            start, end = await loop.run_in_executor(None, normal_cover.solar_times)
            self._sun_start_time = start
            self._sun_end_time = end
            self.logger.debug("Sun start time: %s, Sun end time: %s", start, end)
        else:
            start, end = self._sun_start_time, self._sun_end_time

        current_cover_positions = {
            entity: self._get_current_position(entity) for entity in self.entities
        }
        available_positions = [
            position
            for position in current_cover_positions.values()
            if position is not None
        ]
        current_position_average = (
            round(sum(available_positions) / len(available_positions), 2)
            if available_positions
            else None
        )
        power_without_cover = normal_cover.transmitted_solar_power_w
        power_density_without_cover = normal_cover.transmitted_solar_power_w_m2
        power_with_target_cover = estimate_power_with_cover(
            power_without_cover, state
        )
        power_density_with_target_cover = estimate_power_with_cover(
            power_density_without_cover, state
        )
        cover_count = len(self.entities)
        power_with_actual_cover = (
            sum(
                estimate_power_with_cover(power_without_cover, position) or 0.0
                for position in available_positions
            )
            if available_positions and len(available_positions) == cover_count
            else None
        )
        warnings = configuration_warnings(
            options,
            entities=self.entities,
            current_positions=current_cover_positions,
            solar_radiation_value=normal_cover.solar_radiation_value,
        )
        control_enabled = self.control_toggle is not False
        window_status = derive_window_status(
            target_position=state,
            decision_reason=normal_cover.decision_reason,
            activation_reason=normal_cover.heat_protection_activation_reason,
            direct_sun_valid=normal_cover.direct_sun_valid,
            control_enabled=control_enabled,
            manual_override=self.manager.binary_cover_manual,
            cover_available=bool(available_positions),
            configuration_warnings=warnings,
            full_close_position=normal_cover.effective_full_close_position,
        )
        return AdaptiveCoverData(
            states={
                "state": state,
                "window_status": window_status,
                "start": start,
                "end": end,
                "sun_motion": normal_cover.valid,
                "manual_override": self.manager.binary_cover_manual,
                "manual_list": self.manager.manual_controlled,
            },
            attributes={
                "control_enabled": control_enabled,
                "configuration_warnings": warnings,
                "current_cover_positions": current_cover_positions,
                "current_cover_position_average": current_position_average,
                "cover_attenuation_model": "linear_open_fraction",
                "solar_power_without_cover_w_per_window": (
                    round(power_without_cover, 2)
                    if power_without_cover is not None
                    else None
                ),
                "solar_power_without_cover_w_total": (
                    round(power_without_cover * cover_count, 2)
                    if power_without_cover is not None
                    else None
                ),
                "solar_power_with_target_cover_w_per_window": (
                    round(power_with_target_cover, 2)
                    if power_with_target_cover is not None
                    else None
                ),
                "solar_power_with_target_cover_w_total": (
                    round(power_with_target_cover * cover_count, 2)
                    if power_with_target_cover is not None
                    else None
                ),
                "solar_power_with_actual_cover_w_total": (
                    round(power_with_actual_cover, 2)
                    if power_with_actual_cover is not None
                    else None
                ),
                "solar_power_with_target_cover_w_m2": (
                    round(power_density_with_target_cover, 2)
                    if power_density_with_target_cover is not None
                    else None
                ),
                "house_profile": self.profile_resolution.house_profile_name,
                "house_profile_entry_id": (
                    self.profile_resolution.house_profile_entry_id
                ),
                "configuration_layers": list(self.profile_resolution.layers),
                "configuration_sources": self.profile_resolution.source_by_key,
                "default": options.get(CONF_DEFAULT_HEIGHT),
                "sunset_default": options.get(CONF_SUNSET_POS),
                "sunset_offset": options.get(CONF_SUNSET_OFFSET),
                "facade_name": options.get(CONF_FACADE_NAME),
                "floor_name": options.get(CONF_FLOOR_NAME),
                "room_name": options.get(CONF_ROOM_NAME),
                "use_facade_azimuth": options.get(CONF_USE_FACADE_AZIMUTH, False),
                "facade_reference_azimuth": options.get(
                    CONF_FACADE_REFERENCE_AZIMUTH
                ),
                "facade_offset": options.get(CONF_FACADE_OFFSET),
                "azimuth_window": options.get(CONF_AZIMUTH),
                "field_of_view": [
                    options.get(CONF_FOV_LEFT),
                    options.get(CONF_FOV_RIGHT),
                ],
                "fov_left_deg": options.get(CONF_FOV_LEFT),
                "fov_right_deg": options.get(CONF_FOV_RIGHT),
                "min_elevation_deg": options.get(CONF_MIN_ELEVATION),
                "max_elevation_deg": options.get(CONF_MAX_ELEVATION),
                "window_height_m": options.get(CONF_HEIGHT_WIN),
                "window_width_m": options.get(CONF_WINDOW_WIDTH),
                "window_area_m2": (
                    round(normal_cover.window_area, 3)
                    if normal_cover.window_area is not None
                    else None
                ),
                "legacy_distance_m": options.get(CONF_DISTANCE),
                "reveal_left_depth_m": options.get(CONF_REVEAL_LEFT),
                "reveal_right_depth_m": options.get(CONF_REVEAL_RIGHT),
                "reveal_top_depth_m": options.get(CONF_REVEAL_TOP),
                "horizon_profile": options.get(CONF_HORIZON_PROFILE),
                "horizon_mode": options.get(CONF_HORIZON_MODE, "window"),
                "night_mode": options.get(CONF_NIGHT_MODE, "solar"),
                "night_start_time": options.get(CONF_NIGHT_START_TIME),
                "night_end_time": options.get(CONF_NIGHT_END_TIME),
                "blind_spot": options.get(CONF_BLIND_SPOT_ELEVATION),
                "local_solar_angle": round(normal_cover.local_solar_angle, 2),
                "effective_lower_horizon_elevation": round(
                    normal_cover.effective_lower_horizon_elevation, 2
                ),
                "effective_upper_horizon_elevation": round(
                    normal_cover.effective_upper_horizon_elevation, 2
                ),
                "sun_above_lower_horizon": normal_cover.sun_above_lower_horizon,
                "sun_below_upper_horizon": normal_cover.sun_below_upper_horizon,
                "sun_within_horizon_profile": normal_cover.sun_within_horizon_profile,
                "lower_horizon_clearance": round(
                    normal_cover.lower_horizon_clearance, 2
                ),
                "upper_horizon_clearance": round(
                    normal_cover.upper_horizon_clearance, 2
                ),
                "left_reveal_shadow_pct": round(
                    normal_cover.left_reveal_shadow * 100, 2
                ),
                "right_reveal_shadow_pct": round(
                    normal_cover.right_reveal_shadow * 100, 2
                ),
                "top_reveal_shadow_pct": round(
                    normal_cover.top_reveal_shadow * 100, 2
                ),
                "total_reveal_shadow_pct": round(
                    normal_cover.total_reveal_shadow * 100, 2
                ),
                "direct_solar_exposure_factor": round(
                    normal_cover.direct_solar_exposure_factor, 4
                ),
                "glass_type": normal_cover.glass_type,
                "weather_entity": normal_cover.weather_entity,
                "incidence_angle_deg": round(normal_cover.incidence_angle_deg, 2),
                "incidence_cosine": round(normal_cover.incidence_cosine, 4),
                "visible_reflectance_factor": round(
                    normal_cover.visible_reflectance_factor, 4
                ),
                "solar_reflectance_factor": round(
                    normal_cover.solar_reflectance_factor, 4
                ),
                "near_ir_reflectance_factor": round(
                    normal_cover.near_ir_reflectance_factor, 4
                ),
                "visible_transmittance_factor": round(
                    normal_cover.visible_transmittance_factor, 4
                ),
                "solar_transmittance_factor": round(
                    normal_cover.solar_transmittance_factor, 4
                ),
                "near_ir_transmittance_factor": round(
                    normal_cover.near_ir_transmittance_factor, 4
                ),
                "solar_gain_factor": round(normal_cover.solar_gain_factor, 4),
                "use_open_data_solar_radiation": normal_cover.use_open_data_solar_radiation,
                "solar_radiation_entity": normal_cover.solar_radiation_entity,
                "solar_radiation_source": normal_cover.solar_radiation_source,
                "solar_radiation_reference_w_m2": normal_cover.solar_radiation_reference,
                "solar_radiation_value_w_m2": (
                    round(normal_cover.solar_radiation_value, 2)
                    if normal_cover.solar_radiation_value is not None
                    else None
                ),
                "solar_radiation_factor": (
                    round(normal_cover.solar_radiation_factor, 4)
                    if normal_cover.solar_radiation_factor is not None
                    else None
                ),
                "open_data_current_shortwave_radiation_w_m2": (
                    round(normal_cover.open_data_current_shortwave_radiation, 2)
                    if normal_cover.open_data_current_shortwave_radiation is not None
                    else None
                ),
                "open_data_current_direct_normal_irradiance_w_m2": (
                    round(normal_cover.open_data_current_direct_normal_irradiance, 2)
                    if normal_cover.open_data_current_direct_normal_irradiance is not None
                    else None
                ),
                "open_data_today_max_direct_normal_irradiance_w_m2": (
                    round(normal_cover.open_data_today_max_direct_normal_irradiance, 2)
                    if normal_cover.open_data_today_max_direct_normal_irradiance is not None
                    else None
                ),
                "open_data_today_shortwave_radiation_sum_mj_m2": (
                    round(normal_cover.open_data_today_shortwave_radiation_sum, 2)
                    if normal_cover.open_data_today_shortwave_radiation_sum is not None
                    else None
                ),
                "incoming_solar_radiation_factor": round(
                    normal_cover.incoming_solar_radiation_factor, 4
                ),
                "effective_solar_gain_factor": round(
                    normal_cover.effective_solar_gain_factor, 4
                ),
                "transmitted_solar_power_source": (
                    normal_cover.transmitted_solar_power_source
                ),
                "transmitted_solar_power_w_m2": (
                    round(normal_cover.transmitted_solar_power_w_m2, 2)
                    if normal_cover.transmitted_solar_power_w_m2 is not None
                    else None
                ),
                "transmitted_solar_power_w": (
                    round(normal_cover.transmitted_solar_power_w, 2)
                    if normal_cover.transmitted_solar_power_w is not None
                    else None
                ),
                "heat_power_limit_enabled": normal_cover.heat_power_limit_enabled,
                "heat_power_outside_temperature": (
                    round(normal_cover.heat_power_outside_temperature, 2)
                    if normal_cover.heat_power_outside_temperature is not None
                    else None
                ),
                "heat_protection_min_outside_temp": (
                    normal_cover.heat_protection_min_outside_temp
                ),
                "max_transmitted_solar_power_w_m2": (
                    normal_cover.max_transmitted_solar_power_w_m2
                ),
                "heat_power_limit_active": normal_cover.heat_power_limit_active,
                "heat_power_limit_trigger": normal_cover.heat_power_limit_trigger,
                "heat_protection_current_temperature_allowed": (
                    normal_cover.heat_protection_current_temperature_allowed
                ),
                "heat_power_limited_open_position": (
                    normal_cover.heat_power_limited_open_position
                ),
                "forecast_today_max_temp": normal_cover.forecast_today_max_temp,
                "forecast_tomorrow_max_temp": normal_cover.forecast_tomorrow_max_temp,
                "heat_protection_temperature_signal": (
                    normal_cover.heat_protection_temperature_signal
                ),
                "heat_protection_temperature_allowed": (
                    normal_cover.heat_protection_temperature_allowed
                ),
                "forecast_hot_day_threshold": normal_cover.forecast_hot_day_threshold,
                "forecast_very_hot_day_threshold": (
                    normal_cover.forecast_very_hot_day_threshold
                ),
                "forecast_preemptive_start_time": (
                    normal_cover.forecast_preemptive_start_time
                ),
                "forecast_influence_strength": round(
                    float(normal_cover.forecast_influence_strength or 0.0), 3
                ),
                "use_forecast_max_temp_today": (
                    normal_cover.use_forecast_max_temp_today
                ),
                "use_forecast_max_temp_tomorrow": (
                    normal_cover.use_forecast_max_temp_tomorrow
                ),
                "forecast_solar_radiation_risk": (
                    round(normal_cover.forecast_solar_radiation_risk, 4)
                    if normal_cover.forecast_solar_radiation_risk is not None
                    else None
                ),
                "forecast_temperature_risk": round(
                    normal_cover.forecast_temperature_risk, 4
                ),
                "forecast_preemptive_active": normal_cover.forecast_preemptive_active,
                "forecast_risk_factor": round(normal_cover.forecast_risk_factor, 4),
                "forecast_temperature_gain_boost": round(
                    normal_cover.forecast_temperature_gain_boost, 4
                ),
                "forecast_gain_uplift_factor": round(
                    normal_cover.forecast_gain_uplift_factor, 4
                ),
                "forecast_temperature_policy_pressure": round(
                    normal_cover.forecast_temperature_policy_pressure, 4
                ),
                "forecast_temperature_band": normal_cover.forecast_temperature_band,
                "forecast_temperature_effect_note": (
                    normal_cover.forecast_temperature_effect_note
                ),
                "forecast_temperature_threshold_reduction": round(
                    normal_cover.forecast_temperature_threshold_reduction, 4
                ),
                "forecast_temperature_position_offset": (
                    normal_cover.forecast_temperature_position_offset
                ),
                "forecast_adjusted_gain_factor": round(
                    normal_cover.forecast_adjusted_gain_factor, 4
                ),
                "heat_gain_response_factor": round(
                    normal_cover.heat_gain_response_factor, 4
                ),
                "heat_gain_policy_enabled": normal_cover.heat_gain_policy_active,
                "heat_gain_policy_preset": normal_cover.policy_preset,
                "heat_gain_policy_has_additional_daylight_windows": (
                    normal_cover.has_additional_daylight_windows
                ),
                "heat_gain_policy_away_mode_enabled": normal_cover.enable_away_mode,
                "heat_gain_policy_away_entity": normal_cover.away_entity,
                "heat_gain_policy_away_mode_active": normal_cover.away_mode_active,
                "heat_gain_policy_away_score_multiplier": round(
                    float(normal_cover.away_score_multiplier or 1.0), 3
                ),
                "heat_gain_policy_away_threshold_reduction": round(
                    float(normal_cover.away_threshold_reduction or 0.0), 3
                ),
                "heat_gain_policy_away_position_offset": int(
                    normal_cover.away_position_offset or 0
                ),
                "room_temperature_entity": normal_cover.room_temperature_entity,
                "room_temperature": normal_cover.room_temperature,
                "room_heat_protection_threshold": (
                    normal_cover.room_heat_protection_threshold
                ),
                "room_temperature_heat_active": (
                    normal_cover.room_temperature_heat_active
                ),
                "forecast_hot_day_active": normal_cover.forecast_hot_day_active,
                "heat_protection_activation_active": (
                    normal_cover.heat_protection_activation_active
                ),
                "heat_protection_activation_reason": (
                    normal_cover.heat_protection_activation_reason
                ),
                "heat_gain_policy_show_expert_weights": (
                    normal_cover.show_expert_weights
                ),
                "heat_gain_policy_hot_day_signal": normal_cover.hot_day_signal,
                "heat_gain_policy_weighted_score": round(
                    normal_cover.policy_weighted_score, 4
                ),
                "heat_gain_policy_raw_score": round(
                    normal_cover.policy_raw_score, 4
                ),
                "heat_gain_policy_preset_score": round(
                    normal_cover.policy_preset_score, 4
                ),
                "heat_gain_policy_score": round(normal_cover.policy_score, 4),
                "heat_gain_policy_action_level": normal_cover.policy_action_level,
                "heat_protection_control_mode": getattr(
                    normal_cover, "heat_protection_control_mode", "scaling"
                ),
                "binary_close_threshold_w_m2": getattr(
                    normal_cover, "binary_close_threshold_w_m2", None
                ),
                "binary_close_position": getattr(
                    normal_cover, "binary_close_position", None
                ),
                "binary_heat_protection_active": (
                    normal_cover.binary_heat_protection_active
                ),
                "decision_reason": normal_cover.decision_reason,
                "decision_trace": normal_cover.decision_trace,
                "heat_gain_policy_base_partial_threshold": round(
                    normal_cover.base_policy_thresholds[0], 4
                ),
                "heat_gain_policy_base_full_threshold": round(
                    normal_cover.base_policy_thresholds[1], 4
                ),
                "heat_gain_policy_preset_partial_threshold": round(
                    normal_cover.preset_policy_thresholds[0], 4
                ),
                "heat_gain_policy_preset_full_threshold": round(
                    normal_cover.preset_policy_thresholds[1], 4
                ),
                "heat_gain_policy_away_partial_threshold": round(
                    normal_cover.away_policy_thresholds[0], 4
                ),
                "heat_gain_policy_away_full_threshold": round(
                    normal_cover.away_policy_thresholds[1], 4
                ),
                "heat_gain_policy_partial_threshold": round(
                    normal_cover.effective_partial_close_threshold, 4
                ),
                "heat_gain_policy_full_threshold": round(
                    normal_cover.effective_full_close_threshold, 4
                ),
                "heat_gain_policy_config_partial_position": (
                    normal_cover.configured_policy_positions[0]
                ),
                "heat_gain_policy_config_full_position": (
                    normal_cover.configured_policy_positions[1]
                ),
                "heat_gain_policy_legacy_position_input_detected": (
                    normal_cover.legacy_policy_position_input_detected
                ),
                "heat_gain_policy_base_partial_position": (
                    normal_cover.base_policy_positions[0]
                ),
                "heat_gain_policy_base_full_position": (
                    normal_cover.base_policy_positions[1]
                ),
                "heat_gain_policy_preset_partial_position": (
                    normal_cover.preset_policy_positions[0]
                ),
                "heat_gain_policy_preset_full_position": (
                    normal_cover.preset_policy_positions[1]
                ),
                "heat_gain_policy_away_partial_position": (
                    normal_cover.away_policy_positions[0]
                ),
                "heat_gain_policy_away_full_position": (
                    normal_cover.away_policy_positions[1]
                ),
                "heat_gain_policy_partial_position": (
                    normal_cover.effective_partial_close_position
                ),
                "heat_gain_policy_full_position": (
                    normal_cover.effective_full_close_position
                ),
                "heat_gain_policy_target_position": (
                    normal_cover.heat_gain_target_position
                ),
                "heat_gain_policy_weight_direct_exposure": round(
                    normal_cover.policy_component_weights["direct_exposure"], 3
                ),
                "heat_gain_policy_weight_incidence": round(
                    normal_cover.policy_component_weights["incidence"], 3
                ),
                "heat_gain_policy_weight_glazing": round(
                    normal_cover.policy_component_weights["glazing"], 3
                ),
                "heat_gain_policy_weight_solar_radiation": round(
                    normal_cover.policy_component_weights.get("solar_radiation", 0.0),
                    3,
                ),
                "heat_gain_policy_weight_forecast_temperature": round(
                    normal_cover.policy_component_weights["forecast_temperature"], 3
                ),
            },
        )

    async def _async_get_forecast_summary(self, weather_entity: str | None) -> dict:
        """Fetch and cache the daily weather forecast summary."""
        if not weather_entity:
            return {}

        now = dt.datetime.now(dt.UTC)
        if (
            self._forecast_cache_entity == weather_entity
            and self._forecast_cache_updated is not None
            and now - self._forecast_cache_updated < dt.timedelta(minutes=30)
            and self._forecast_cache_data is not None
        ):
            return self._forecast_cache_data

        try:
            response = await self.hass.services.async_call(
                WEATHER_DOMAIN,
                "get_forecasts",
                {"entity_id": weather_entity, "type": "daily"},
                blocking=True,
                return_response=True,
            )
        except Exception as err:  # noqa: BLE001
            self.logger.debug("Unable to fetch forecast for %s: %s", weather_entity, err)
            return {}

        entity_response = response.get(weather_entity)
        if entity_response is None and "service_response" in response:
            entity_response = response["service_response"].get(weather_entity)
        forecast = entity_response.get("forecast") if entity_response else None
        summary = extract_daily_forecast_summary(forecast)
        self._forecast_cache_entity = weather_entity
        self._forecast_cache_updated = now
        self._forecast_cache_data = summary
        return summary

    async def _async_get_solar_radiation_summary(self, enabled: bool) -> dict:
        """Fetch and cache open-data solar radiation."""
        if not enabled:
            return {}

        now = dt.datetime.now(dt.UTC)
        if (
            self._solar_radiation_cache_updated is not None
            and now - self._solar_radiation_cache_updated < dt.timedelta(minutes=30)
            and self._solar_radiation_cache_data is not None
        ):
            return self._solar_radiation_cache_data

        try:
            summary = await async_fetch_open_meteo_solar_summary(
                self.hass,
                self.hass.config.latitude,
                self.hass.config.longitude,
            )
        except Exception as err:  # noqa: BLE001
            self.logger.debug("Unable to fetch Open-Meteo solar radiation: %s", err)
            return {}

        self._solar_radiation_cache_updated = now
        self._solar_radiation_cache_data = summary
        return summary

    async def async_handle_state_change(self, state: int, options):
        """Handle state change from tracked entities."""
        if self.control_toggle:
            for cover in self.entities:
                await self.async_handle_call_service(cover, state, options)
        else:
            self.logger.debug("State change but control toggle is off")
        self.state_change = False
        self.logger.debug("State change handled")

    async def async_handle_cover_state_change(self, state: int):
        """Handle state change from assigned covers."""
        if self.manual_toggle and self.control_toggle:
            self.manager.handle_state_change(
                self.state_change_data,
                state,
                self._cover_type,
                self.manual_reset,
                self.wait_for_target,
                self.manual_threshold,
            )
        self.cover_state_change = False
        self.logger.debug("Cover state change handled")

    async def async_handle_first_refresh(self, state: int, options):
        """Handle first refresh."""
        if self.control_toggle:
            for cover in self.entities:
                if (
                    self.check_adaptive_time
                    and not self.manager.is_cover_manual(cover)
                    and self.check_position_delta(cover, state, options)
                ):
                    await self.async_set_position(cover, state)
        else:
            self.logger.debug("First refresh but control toggle is off")
        self.first_refresh = False
        self.logger.debug("First refresh handled")

    async def async_handle_timed_refresh(self, options):
        """Handle timed refresh."""
        self.logger.debug(
            "This is a timed refresh, using sunset position: %s",
            options.get(CONF_SUNSET_POS),
        )
        if self.control_toggle:
            for cover in self.entities:
                await self.async_set_manual_position(
                    cover,
                    (
                        inverse_state(options.get(CONF_SUNSET_POS))
                        if self._inverse_state
                        else options.get(CONF_SUNSET_POS)
                    ),
                )
        else:
            self.logger.debug("Timed refresh but control toggle is off")
        self.timed_refresh = False
        self.logger.debug("Timed refresh handled")

    async def async_handle_call_service(self, entity, state: int, options):
        """Handle call service."""
        if (
            self.check_adaptive_time
            and self.check_position_delta(entity, state, options)
            and self.check_time_delta(entity)
            and not self.manager.is_cover_manual(entity)
        ):
            await self.async_set_position(entity, state)

    async def async_set_position(self, entity, state: int):
        """Call service to set cover position."""
        await self.async_set_manual_position(entity, state)

    async def async_set_manual_position(self, entity, state):
        """Call service to set cover position."""
        if self.check_position(entity, state):
            service = SERVICE_SET_COVER_POSITION
            service_data = {}
            service_data[ATTR_ENTITY_ID] = entity

            if self._cover_type == "cover_tilt":
                service = SERVICE_SET_COVER_TILT_POSITION
                service_data[ATTR_TILT_POSITION] = state
            else:
                service_data[ATTR_POSITION] = state

            self.wait_for_target[entity] = True
            self.target_call[entity] = state
            self.logger.debug(
                "Set wait for target %s and target call %s",
                self.wait_for_target,
                self.target_call,
            )
            self.logger.debug("Run %s with data %s", service, service_data)
            await self.hass.services.async_call(COVER_DOMAIN, service, service_data)

    def _update_options(self, options):
        """Update options."""
        self.entities = options.get(CONF_ENTITIES, [])
        self.min_change = options.get(CONF_DELTA_POSITION, 1)
        self.time_threshold = options.get(CONF_DELTA_TIME, 2)
        self.start_time = options.get(CONF_START_TIME)
        self.start_time_entity = options.get(CONF_START_ENTITY)
        self.end_time = options.get(CONF_END_TIME)
        self.end_time_entity = options.get(CONF_END_ENTITY)
        self.manual_reset = options.get(CONF_MANUAL_OVERRIDE_RESET, False)
        self.manual_duration = options.get(
            CONF_MANUAL_OVERRIDE_DURATION, {"minutes": 15}
        )
        self.manual_threshold = options.get(CONF_MANUAL_THRESHOLD)
        self.start_value = options.get(CONF_INTERP_START)
        self.end_value = options.get(CONF_INTERP_END)
        self.normal_list = options.get(CONF_INTERP_LIST)
        self.new_list = options.get(CONF_INTERP_LIST_NEW)

    def _update_manager_and_covers(self):
        self.manager.add_covers(self.entities)
        if not self._manual_toggle:
            for entity in self.manager.manual_controlled:
                self.manager.reset(entity)

    def get_blind_data(self, options):
        """Assign correct class for type of blind."""
        if self._cover_type == "cover_blind":
            cover_data = AdaptiveVerticalCover(
                self.hass,
                self.logger,
                *self.pos_sun,
                *self.common_data(options),
                *self.vertical_data(options),
            )
        if self._cover_type == "cover_awning":
            cover_data = AdaptiveHorizontalCover(
                self.hass,
                self.logger,
                *self.pos_sun,
                *self.common_data(options),
                *self.vertical_data(options),
                *self.horizontal_data(options),
            )
        if self._cover_type == "cover_tilt":
            cover_data = AdaptiveTiltCover(
                self.hass,
                self.logger,
                *self.pos_sun,
                *self.common_data(options),
                *self.tilt_data(options),
            )
        cover_data.horizon_mode = options.get(CONF_HORIZON_MODE, "window")
        cover_data.night_mode = options.get(CONF_NIGHT_MODE, "solar")
        cover_data.night_start_time = options.get(
            CONF_NIGHT_START_TIME, "22:00:00"
        )
        cover_data.night_end_time = options.get(CONF_NIGHT_END_TIME, "06:00:00")
        cover_data.heat_protection_control_mode = options.get(
            CONF_HEAT_PROTECTION_CONTROL_MODE, "scaling"
        )
        cover_data.binary_close_threshold_w_m2 = options.get(
            CONF_BINARY_CLOSE_THRESHOLD, 180
        )
        cover_data.binary_close_position = options.get(CONF_BINARY_CLOSE_POSITION, 20)
        return cover_data

    @property
    def check_adaptive_time(self):
        """Check if time is within start and end times."""
        if self._start_time and self._end_time and self._start_time > self._end_time:
            self.logger.error("Start time is after end time")
        return self.before_end_time and self.after_start_time

    @property
    def after_start_time(self):
        """Check if time is after start time."""
        now = dt.datetime.now()
        if self.start_time_entity is not None:
            time = get_datetime_from_str(
                get_safe_state(self.hass, self.start_time_entity)
            )
            self.logger.debug(
                "Start time: %s, now: %s, now >= time: %s ", time, now, now >= time
            )
            self._start_time = time
            return now >= time
        if self.start_time is not None:
            time = get_datetime_from_str(self.start_time)

            self.logger.debug(
                "Start time: %s, now: %s, now >= time: %s", time, now, now >= time
            )
            self._start_time
            return now >= time
        return True

    @property
    def _end_time(self) -> dt.datetime | None:
        """Get end time."""
        time = None
        if self.end_time_entity is not None:
            time = get_datetime_from_str(
                get_safe_state(self.hass, self.end_time_entity)
            )
        elif self.end_time is not None:
            time = get_datetime_from_str(self.end_time)
            if time.time() == dt.time(0, 0):
                time = time + dt.timedelta(days=1)
        return time

    @property
    def before_end_time(self):
        """Check if time is before end time."""
        if self._end_time is not None:
            now = dt.datetime.now()
            self.logger.debug(
                "End time: %s, now: %s, now < time: %s",
                self._end_time,
                now,
                now < self._end_time,
            )
            return now < self._end_time
        return True

    def _get_current_position(self, entity) -> int | None:
        """Get current position of cover."""
        if self._cover_type == "cover_tilt":
            return state_attr(self.hass, entity, "current_tilt_position")
        return state_attr(self.hass, entity, "current_position")

    def check_position(self, entity, state):
        """Check if position is different as state."""
        position = self._get_current_position(entity)
        if position is not None:
            return position != state
        self.logger.debug("Cover is already at position %s", state)
        return False

    def check_position_delta(self, entity, state: int, options):
        """Check cover positions to reduce calls."""
        position = self._get_current_position(entity)
        if position is not None:
            condition = abs(position - state) >= self.min_change
            self.logger.debug(
                "Entity: %s,  position: %s, state: %s, delta position: %s, min_change: %s, condition: %s",
                entity,
                position,
                state,
                abs(position - state),
                self.min_change,
                condition,
            )
            if state in [
                options.get(CONF_SUNSET_POS),
                options.get(CONF_DEFAULT_HEIGHT),
                0,
                100,
            ]:
                condition = True
            return condition
        return True

    def check_time_delta(self, entity):
        """Check if time delta is passed."""
        now = dt.datetime.now(dt.UTC)
        last_updated = get_last_updated(entity, self.hass)
        if last_updated is not None:
            condition = now - last_updated >= dt.timedelta(minutes=self.time_threshold)
            self.logger.debug(
                "Entity: %s, time delta: %s, threshold: %s, condition: %s",
                entity,
                now - last_updated,
                self.time_threshold,
                condition,
            )
            return condition
        return True

    @property
    def pos_sun(self):
        """Fetch information for sun position."""
        return [
            state_attr(self.hass, "sun.sun", "azimuth"),
            state_attr(self.hass, "sun.sun", "elevation"),
        ]

    def common_data(self, options):
        """Update shared parameters."""
        return [
            options.get(CONF_SUNSET_POS),
            options.get(CONF_SUNSET_OFFSET),
            options.get(CONF_SUNRISE_OFFSET, options.get(CONF_SUNSET_OFFSET)),
            self.hass.config.time_zone,
            options.get(CONF_FOV_LEFT),
            options.get(CONF_FOV_RIGHT),
            options.get(CONF_AZIMUTH),
            options.get(CONF_DEFAULT_HEIGHT),
            options.get(CONF_MAX_POSITION),
            options.get(CONF_MIN_POSITION),
            options.get(CONF_ENABLE_MAX_POSITION, False),
            options.get(CONF_ENABLE_MIN_POSITION, False),
            options.get(CONF_BLIND_SPOT_LEFT),
            options.get(CONF_BLIND_SPOT_RIGHT),
            options.get(CONF_BLIND_SPOT_ELEVATION),
            options.get(CONF_ENABLE_BLIND_SPOT, False),
            options.get(CONF_MIN_ELEVATION, None),
            options.get(CONF_MAX_ELEVATION, None),
            options.get(CONF_HORIZON_PROFILE),
            options.get(CONF_WINDOW_WIDTH),
            options.get(CONF_REVEAL_LEFT),
            options.get(CONF_REVEAL_RIGHT),
            options.get(CONF_REVEAL_TOP),
            options.get(CONF_GLASS_TYPE),
            options.get(CONF_WEATHER_ENTITY),
            self._forecast_summary,
            self._solar_radiation_summary,
            options.get(CONF_USE_OPEN_DATA_SOLAR_RADIATION, False),
            options.get(CONF_SOLAR_RADIATION_ENTITY),
            options.get(CONF_SOLAR_RADIATION_REFERENCE, 900),
            options.get(CONF_HEAT_POWER_LIMIT_ENABLED, False),
            options.get(CONF_HEAT_PROTECTION_MIN_OUTSIDE_TEMP, 14),
            options.get(CONF_ROOM_TEMPERATURE_ENTITY),
            options.get(CONF_ROOM_HEAT_PROTECTION_THRESHOLD, 24),
            options.get(
                CONF_MAX_TRANSMITTED_SOLAR_POWER,
                options.get(LEGACY_MAX_TRANSMITTED_SOLAR_POWER, 250),
            ),
            options.get(CONF_USE_FORECAST_MAX_TEMP_TODAY, False),
            options.get(CONF_USE_FORECAST_MAX_TEMP_TOMORROW, False),
            options.get(CONF_FORECAST_HOT_DAY_THRESHOLD),
            options.get(CONF_FORECAST_VERY_HOT_DAY_THRESHOLD),
            options.get(CONF_FORECAST_PREEMPTIVE_START_TIME),
            options.get(CONF_FORECAST_INFLUENCE_STRENGTH, 0.0),
            options.get(CONF_ENABLE_HEAT_GAIN_POLICY, False),
            options.get(CONF_POLICY_PRESET, "daylight_first_single_aspect"),
            options.get(CONF_HAS_ADDITIONAL_DAYLIGHT_WINDOWS, False),
            options.get(CONF_ENABLE_AWAY_MODE, False),
            options.get(CONF_AWAY_ENTITY),
            options.get(CONF_AWAY_SCORE_MULTIPLIER, 1.25),
            options.get(CONF_AWAY_THRESHOLD_REDUCTION, 0.1),
            options.get(CONF_AWAY_POSITION_OFFSET, 10),
            options.get(CONF_SHOW_EXPERT_WEIGHTS, False),
            options.get(CONF_WEIGHT_DIRECT_EXPOSURE, 1.0),
            options.get(CONF_WEIGHT_INCIDENCE, 1.0),
            options.get(CONF_WEIGHT_GLAZING, 1.0),
            options.get(CONF_WEIGHT_FORECAST_TEMPERATURE, 1.0),
            options.get(CONF_WEIGHT_SOLAR_RADIATION, 1.0),
            options.get(CONF_PARTIAL_CLOSE_THRESHOLD, 0.35),
            options.get(CONF_FULL_CLOSE_THRESHOLD, 0.65),
            options.get(CONF_PARTIAL_CLOSE_POSITION, 70),
            options.get(CONF_FULL_CLOSE_POSITION, 30),
        ]

    def vertical_data(self, options):
        """Update data for vertical blinds."""
        return [
            options.get(CONF_DISTANCE),
            options.get(CONF_HEIGHT_WIN),
        ]

    def horizontal_data(self, options):
        """Update data for horizontal blinds."""
        return [
            options.get(CONF_LENGTH_AWNING),
            options.get(CONF_AWNING_ANGLE),
        ]

    def tilt_data(self, options):
        """Update data for tilted blinds."""
        return [
            options.get(CONF_TILT_DISTANCE),
            options.get(CONF_TILT_DEPTH),
            options.get(CONF_TILT_MODE),
        ]

    @property
    def state(self) -> int:
        """Handle the output of the state based on mode."""
        state = self.default_state

        if self._use_interpolation:
            self.logger.debug("Interpolating position: %s", state)
            state = self.interpolate_states(state)

        if self._inverse_state and self._use_interpolation:
            self.logger.info(
                "Inverse state is not supported with interpolation, you can inverse the state by arranging the list from high to low"
            )

        if self._inverse_state and not self._use_interpolation:
            state = inverse_state(state)
            self.logger.debug("Inversed position: %s", state)

        self.logger.debug("Final position to use: %s", state)
        return state

    def interpolate_states(self, state):
        """Interpolate states."""
        normal_range = [0, 100]
        new_range = []
        if self.start_value and self.end_value:
            new_range = [self.start_value, self.end_value]
        if self.normal_list and self.new_list:
            normal_range = list(map(int, self.normal_list))
            new_range = list(map(int, self.new_list))
        if new_range:
            state = np.interp(state, normal_range, new_range)
            if state == new_range[0]:
                state = 0
            if state == new_range[-1]:
                state = 100
        return state

    @property
    def control_toggle(self):
        """Toggle automation."""
        return self._control_toggle

    @control_toggle.setter
    def control_toggle(self, value):
        self._control_toggle = value

    @property
    def manual_toggle(self):
        """Toggle automation."""
        return self._manual_toggle

    @manual_toggle.setter
    def manual_toggle(self, value):
        self._manual_toggle = value


class AdaptiveCoverManager:
    """Track position changes."""

    def __init__(self, reset_duration: dict[str:int], logger) -> None:
        """Initialize the AdaptiveCoverManager."""
        self.covers: set[str] = set()

        self.manual_control: dict[str, bool] = {}
        self.manual_control_time: dict[str, dt.datetime] = {}
        self.reset_duration = dt.timedelta(**reset_duration)
        self.logger = logger

    def add_covers(self, entity):
        """Update set with entities."""
        self.covers.update(entity)

    def handle_state_change(
        self,
        states_data,
        our_state,
        blind_type,
        allow_reset,
        wait_target_call,
        manual_threshold,
    ):
        """Process state change event."""
        event = states_data
        if event is None:
            return
        entity_id = event.entity_id
        if entity_id not in self.covers:
            return
        if wait_target_call.get(entity_id):
            return

        new_state = event.new_state

        if blind_type == "cover_tilt":
            new_position = new_state.attributes.get("current_tilt_position")
        else:
            new_position = new_state.attributes.get("current_position")

        if new_position != our_state:
            if (
                manual_threshold is not None
                and abs(our_state - new_position) < manual_threshold
            ):
                self.logger.debug(
                    "Position change is less than threshold %s for %s",
                    manual_threshold,
                    entity_id,
                )
                return
            self.logger.debug(
                "Manual change detected for %s. Our state: %s, new state: %s",
                entity_id,
                our_state,
                new_position,
            )
            self.logger.debug(
                "Set manual control for %s, for at least %s seconds, reset_allowed: %s",
                entity_id,
                self.reset_duration.total_seconds(),
                allow_reset,
            )
            self.mark_manual_control(entity_id)
            self.set_last_updated(entity_id, new_state, allow_reset)

    def set_last_updated(self, entity_id, new_state, allow_reset):
        """Set last updated time for manual control."""
        if entity_id not in self.manual_control_time or allow_reset:
            last_updated = new_state.last_updated
            self.manual_control_time[entity_id] = last_updated
            self.logger.debug(
                "Updating last updated for manual control to %s for %s. Allow reset:%s",
                last_updated,
                entity_id,
                allow_reset,
            )
        elif not allow_reset:
            self.logger.debug(
                "Already manual control time specified for %s, reset is not allowed by user setting:%s",
                entity_id,
                allow_reset,
            )

    def mark_manual_control(self, cover: str) -> None:
        """Mark cover as under manual control."""
        self.manual_control[cover] = True

    async def reset_if_needed(self):
        """Reset manual control state of the covers."""
        current_time = dt.datetime.now(dt.UTC)
        manual_control_time_copy = dict(self.manual_control_time)
        for entity_id, last_updated in manual_control_time_copy.items():
            if current_time - last_updated > self.reset_duration:
                self.logger.debug(
                    "Resetting manual override for %s, because duration has elapsed",
                    entity_id,
                )
                self.reset(entity_id)

    def reset(self, entity_id):
        """Reset manual control for a cover."""
        self.manual_control[entity_id] = False
        self.manual_control_time.pop(entity_id, None)
        self.logger.debug("Reset manual override for %s", entity_id)

    def is_cover_manual(self, entity_id):
        """Check if a cover is under manual control."""
        return self.manual_control.get(entity_id, False)

    @property
    def binary_cover_manual(self):
        """Check if any cover is under manual control."""
        return any(value for value in self.manual_control.values())

    @property
    def manual_controlled(self):
        """Get the list of covers under manual control."""
        return [k for k, v in self.manual_control.items() if v]


def inverse_state(state: int) -> int:
    """Inverse state."""
    return 100 - state

"""Generate values for all types of covers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

import numpy as np
import pandas as pd
from homeassistant.core import HomeAssistant
from numpy import cos, sin, tan
from numpy import radians as rad

from .compat import state_attr
from .forecast import (
    after_preemptive_start,
    temperature_risk,
)
from .helpers import get_domain, get_safe_state
from .sun import SunData
from .config_context_adapter import ConfigContextAdapter
from .geometry import (
    combined_reveal_shadow_fraction,
    interpolate_horizon_elevations,
    left_reveal_shadow_fraction,
    local_window_angle,
    parse_horizon_profile,
    right_reveal_shadow_fraction,
    top_reveal_shadow_fraction,
)
from .optics import (
    angular_transmittance,
    glass_profile_for_type,
    incidence_angle_from_gamma_elevation,
    incidence_cosine_from_angle,
    schlick_reflectance,
)
from .policy import (
    adjusted_policy_score,
    adjusted_positions,
    adjusted_thresholds,
    away_adjusted_positions,
    away_adjusted_score,
    away_adjusted_thresholds,
    gain_limited_policy_score,
    legacy_position_input_detected,
    normalize_policy_positions,
    policy_target_position,
    preset_weights_for_name,
    temperature_adjusted_positions,
    temperature_adjusted_thresholds,
    temperature_boost_signal,
    very_hot_policy_pressure,
    weighted_risk_score,
)
from .solar_radiation import radiation_factor

HEAT_GAIN_RESPONSE_START = 0.06
HEAT_GAIN_RESPONSE_FULL = 0.32


def heat_gain_response_factor(gain: float | None) -> float:
    """Map physical solar gain to a practical shading response factor."""
    if gain is None:
        return 0.0
    progress = (float(gain) - HEAT_GAIN_RESPONSE_START) / (
        HEAT_GAIN_RESPONSE_FULL - HEAT_GAIN_RESPONSE_START
    )
    progress = float(np.clip(progress, 0.0, 1.0))
    return float(progress * progress * (3.0 - 2.0 * progress))


@dataclass
class AdaptiveGeneralCover(ABC):
    """Collect common data."""

    hass: HomeAssistant
    logger: ConfigContextAdapter
    sol_azi: float
    sol_elev: float
    sunset_pos: int
    sunset_off: int
    sunrise_off: int
    timezone: str
    fov_left: int
    fov_right: int
    win_azi: int
    h_def: int
    max_pos: int
    min_pos: int
    max_pos_bool: bool
    min_pos_bool: bool
    blind_spot_left: int
    blind_spot_right: int
    blind_spot_elevation: int
    blind_spot_on: bool
    min_elevation: int
    max_elevation: int
    horizon_profile: str | list | None
    window_width: float | None
    reveal_left_depth: float | None
    reveal_right_depth: float | None
    reveal_top_depth: float | None
    glass_type: str | None
    weather_entity: str | None
    forecast_summary: dict | None
    solar_radiation_summary: dict | None
    use_open_data_solar_radiation: bool
    solar_radiation_entity: str | None
    solar_radiation_reference: float | None
    heat_power_limit_enabled: bool
    heat_power_outside_temp_threshold: float | None
    heat_protection_min_outside_temp: float | None
    max_transmitted_solar_power_w_m2: float | None
    use_forecast_max_temp_today: bool
    use_forecast_max_temp_tomorrow: bool
    forecast_hot_day_threshold: float | None
    forecast_very_hot_day_threshold: float | None
    forecast_preemptive_start_time: str | None
    forecast_influence_strength: float | None
    enable_heat_gain_policy: bool
    policy_preset: str | None
    has_additional_daylight_windows: bool
    enable_away_mode: bool
    away_entity: str | None
    away_score_multiplier: float | None
    away_threshold_reduction: float | None
    away_position_offset: int | None
    hot_day_close_enabled: bool
    hot_day_close_threshold: float | None
    hot_day_close_position: int | None
    very_hot_day_close_position: int | None
    show_expert_weights: bool
    weight_direct_exposure: float | None
    weight_incidence: float | None
    weight_glazing: float | None
    weight_forecast_temperature: float | None
    weight_solar_radiation: float | None
    partial_close_threshold: float | None
    full_close_threshold: float | None
    partial_close_position: int | None
    full_close_position: int | None
    evaluation_datetime: datetime | None = field(default=None, kw_only=True)
    sun_data: SunData = field(init=False)
    _parsed_horizon_profile: list = field(init=False, repr=False)

    def __post_init__(self):
        """Add solar data to dataset."""
        self.sun_data = SunData(self.timezone, self.hass)
        self._parsed_horizon_profile = parse_horizon_profile(self.horizon_profile)

    def solar_times(self):
        """Determine start/end times."""
        df_today = pd.DataFrame(
            {
                "azimuth": self.sun_data.solar_azimuth,
                "elevation": self.sun_data.solar_elevation,
            }
        )
        solpos = df_today.set_index(self.sun_data.times)

        alpha = solpos["azimuth"]
        frame = (
            (alpha - self.azi_min_abs) % 360
            <= (self.azi_max_abs - self.azi_min_abs) % 360
        ) & (solpos["elevation"] > 0)

        if solpos[frame].empty:
            return None, None
        else:
            return (
                solpos[frame].index[0].to_pydatetime(),
                solpos[frame].index[-1].to_pydatetime(),
            )

    @property
    def _get_azimuth_edges(self) -> tuple[int, int]:
        """Calculate azimuth edges."""
        return self.fov_left + self.fov_right

    @property
    def is_sun_in_blind_spot(self) -> bool:
        """Check if sun is in blind spot."""
        if (
            self.blind_spot_left is not None
            and self.blind_spot_right is not None
            and self.blind_spot_on
        ):
            left_edge = self.fov_left - self.blind_spot_left
            right_edge = self.fov_left - self.blind_spot_right
            blindspot = (self.gamma <= left_edge) & (self.gamma >= right_edge)
            if self.blind_spot_elevation is not None:
                blindspot = blindspot & (self.sol_elev <= self.blind_spot_elevation)
            self.logger.debug("Is sun in blind spot? %s", blindspot)
            return blindspot
        return False

    @property
    def azi_min_abs(self) -> int:
        """Calculate min azimuth."""
        azi_min_abs = (self.win_azi - self.fov_left + 360) % 360
        return azi_min_abs

    @property
    def azi_max_abs(self) -> int:
        """Calculate max azimuth."""
        azi_max_abs = (self.win_azi + self.fov_right + 360) % 360
        return azi_max_abs

    @property
    def gamma(self) -> float:
        """Calculate Gamma."""
        # surface solar azimuth
        gamma = (self.win_azi - self.sol_azi + 180) % 360 - 180
        return gamma

    @property
    def local_solar_angle(self) -> float:
        """Return the local window angle from left (0) to right (180)."""
        return local_window_angle(self.gamma)

    @property
    def effective_horizon_elevations(self) -> tuple[float, float]:
        """Return interpolated lower and upper horizon elevations."""
        return interpolate_horizon_elevations(
            self.local_solar_angle, self._parsed_horizon_profile
        )

    @property
    def effective_lower_horizon_elevation(self) -> float:
        """Return the interpolated lower horizon elevation."""
        return self.effective_horizon_elevations[0]

    @property
    def effective_upper_horizon_elevation(self) -> float:
        """Return the interpolated upper horizon elevation."""
        return self.effective_horizon_elevations[1]

    @property
    def sun_above_lower_horizon(self) -> bool:
        """Return whether the sun is above the lower horizon profile."""
        return self.sol_elev >= self.effective_lower_horizon_elevation

    @property
    def sun_below_upper_horizon(self) -> bool:
        """Return whether the sun is below the upper horizon profile."""
        return self.sol_elev <= self.effective_upper_horizon_elevation

    @property
    def sun_within_horizon_profile(self) -> bool:
        """Return whether the sun is within the visible sky band."""
        if not self._parsed_horizon_profile:
            return True
        return self.sun_above_lower_horizon and self.sun_below_upper_horizon

    @property
    def lower_horizon_clearance(self) -> float:
        """Return clearance above the lower horizon."""
        return self.sol_elev - self.effective_lower_horizon_elevation

    @property
    def upper_horizon_clearance(self) -> float:
        """Return clearance below the upper horizon."""
        return self.effective_upper_horizon_elevation - self.sol_elev

    @property
    def valid_elevation(self) -> bool:
        """Check if elevation is within range."""
        if self.min_elevation is None and self.max_elevation is None:
            return self.sol_elev >= 0
        if self.min_elevation is None:
            return self.sol_elev <= self.max_elevation
        if self.max_elevation is None:
            return self.sol_elev >= self.min_elevation
        within_range = self.min_elevation <= self.sol_elev <= self.max_elevation
        self.logger.debug("elevation within range? %s", within_range)
        return within_range

    @property
    def valid(self) -> bool:
        """Determine if sun is in front of window."""
        # clip azi_min and azi_max to 90
        azi_min = min(self.fov_left, 90)
        azi_max = min(self.fov_right, 90)

        # valid sun positions are those within the blind's azimuth range and above the horizon (FOV)
        valid = (
            (self.gamma < azi_min) & (self.gamma > -azi_max) & (self.valid_elevation)
        )
        self.logger.debug("Sun in front of window (ignoring blindspot)? %s", valid)
        return valid

    @property
    def left_reveal_shadow(self) -> float:
        """Return left reveal shading fraction."""
        return left_reveal_shadow_fraction(
            self.gamma, self.window_width, self.reveal_left_depth
        )

    @property
    def right_reveal_shadow(self) -> float:
        """Return right reveal shading fraction."""
        return right_reveal_shadow_fraction(
            self.gamma, self.window_width, self.reveal_right_depth
        )

    @property
    def side_reveal_shadow(self) -> float:
        """Return side reveal shading fraction on the glass area."""
        return max(self.left_reveal_shadow, self.right_reveal_shadow)

    @property
    def top_reveal_shadow(self) -> float:
        """Return top reveal shading fraction."""
        return top_reveal_shadow_fraction(
            self.sol_elev,
            self.h_win if hasattr(self, "h_win") else None,
            self.reveal_top_depth,
        )

    @property
    def total_reveal_shadow(self) -> float:
        """Return total reveal shading fraction with simple overlap handling."""
        return combined_reveal_shadow_fraction(
            self.side_reveal_shadow, self.top_reveal_shadow
        )

    @property
    def direct_solar_exposure_factor(self) -> float:
        """Return a first-order direct solar exposure factor."""
        if not self.sun_within_horizon_profile:
            return 0.0
        return float(np.clip(1.0 - self.total_reveal_shadow, 0.0, 1.0))

    @property
    def glazing_profile(self):
        """Return the optical preset for the configured glazing."""
        return glass_profile_for_type(self.glass_type)

    @property
    def incidence_angle_deg(self) -> float:
        """Return the incidence angle between window normal and sun."""
        return incidence_angle_from_gamma_elevation(self.gamma, self.sol_elev)

    @property
    def incidence_cosine(self) -> float:
        """Return the front-facing incidence cosine."""
        return incidence_cosine_from_angle(self.incidence_angle_deg)

    @property
    def visible_reflectance_factor(self) -> float:
        """Return the angle-adjusted visible reflectance."""
        return schlick_reflectance(
            self.glazing_profile.visible_reflectance_normal,
            self.incidence_angle_deg,
        )

    @property
    def solar_reflectance_factor(self) -> float:
        """Return the angle-adjusted solar reflectance."""
        return schlick_reflectance(
            self.glazing_profile.solar_reflectance_normal,
            self.incidence_angle_deg,
        )

    @property
    def near_ir_reflectance_factor(self) -> float:
        """Return the angle-adjusted near-IR reflectance."""
        return schlick_reflectance(
            self.glazing_profile.near_ir_reflectance_normal,
            self.incidence_angle_deg,
        )

    @property
    def visible_transmittance_factor(self) -> float:
        """Return the angle-adjusted visible transmittance."""
        return angular_transmittance(
            self.glazing_profile.visible_transmittance,
            self.glazing_profile.visible_reflectance_normal,
            self.incidence_angle_deg,
        )

    @property
    def solar_transmittance_factor(self) -> float:
        """Return the angle-adjusted total solar transmittance."""
        return angular_transmittance(
            self.glazing_profile.solar_transmittance,
            self.glazing_profile.solar_reflectance_normal,
            self.incidence_angle_deg,
        )

    @property
    def near_ir_transmittance_factor(self) -> float:
        """Return the angle-adjusted near-IR transmittance."""
        return angular_transmittance(
            self.glazing_profile.near_ir_transmittance,
            self.glazing_profile.near_ir_reflectance_normal,
            self.incidence_angle_deg,
        )

    @property
    def solar_gain_factor(self) -> float:
        """Return the geometry and glazing adjusted solar gain factor."""
        return float(
            np.clip(
                self.direct_solar_exposure_factor
                * self.incidence_cosine
                * self.solar_transmittance_factor,
                0.0,
                1.0,
            )
        )

    @property
    def open_data_current_direct_normal_irradiance(self) -> float | None:
        """Return current Open-Meteo DNI in W/m2."""
        value = (self.solar_radiation_summary or {}).get(
            "current_direct_normal_irradiance"
        )
        return None if value is None else float(value)

    @property
    def open_data_current_shortwave_radiation(self) -> float | None:
        """Return current Open-Meteo shortwave/GHI in W/m2."""
        value = (self.solar_radiation_summary or {}).get("current_shortwave_radiation")
        return None if value is None else float(value)

    @property
    def open_data_today_max_direct_normal_irradiance(self) -> float | None:
        """Return today's maximum Open-Meteo DNI in W/m2."""
        value = (self.solar_radiation_summary or {}).get(
            "today_max_direct_normal_irradiance"
        )
        return None if value is None else float(value)

    @property
    def open_data_today_shortwave_radiation_sum(self) -> float | None:
        """Return today's Open-Meteo shortwave radiation sum in MJ/m2."""
        value = (self.solar_radiation_summary or {}).get(
            "today_shortwave_radiation_sum"
        )
        return None if value is None else float(value)

    @property
    def solar_radiation_sensor_value(self) -> float | None:
        """Return optional local solar radiation sensor value in W/m2."""
        if not self.solar_radiation_entity:
            return None
        value = get_safe_state(self.hass, self.solar_radiation_entity)
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @property
    def solar_radiation_value(self) -> float | None:
        """Return the active solar radiation value in W/m2."""
        if self.solar_radiation_sensor_value is not None:
            return self.solar_radiation_sensor_value
        if self.use_open_data_solar_radiation:
            return (
                self.open_data_current_direct_normal_irradiance
                if self.open_data_current_direct_normal_irradiance is not None
                else self.open_data_current_shortwave_radiation
            )
        return None

    @property
    def solar_radiation_source(self) -> str | None:
        """Return where the active solar radiation value came from."""
        if self.solar_radiation_sensor_value is not None:
            return "sensor"
        if self.use_open_data_solar_radiation and self.solar_radiation_value is not None:
            return "open_meteo"
        return None

    @property
    def solar_radiation_factor(self) -> float | None:
        """Return the active solar radiation factor."""
        if self.solar_radiation_value is None:
            return None
        return radiation_factor(
            self.solar_radiation_value,
            direct_normal=self.solar_radiation_source != "sensor",
            reference=self.solar_radiation_reference,
        )

    @property
    def forecast_solar_radiation_risk(self) -> float | None:
        """Return today's open-data solar radiation risk."""
        if not self.use_open_data_solar_radiation:
            return None
        value = self.open_data_today_max_direct_normal_irradiance
        if value is None:
            value = (self.solar_radiation_summary or {}).get(
                "today_max_shortwave_radiation"
            )
            if value is None:
                return None
            return radiation_factor(
                value,
                direct_normal=False,
                reference=self.solar_radiation_reference,
            )
        return radiation_factor(
            value,
            direct_normal=True,
            reference=self.solar_radiation_reference,
        )

    @property
    def incoming_solar_radiation_factor(self) -> float:
        """Return normalized incoming irradiance, or zero when it is unavailable."""
        return float(self.solar_radiation_factor or 0.0)

    @property
    def effective_solar_gain_factor(self) -> float:
        """Return the irradiance, geometry, and glazing adjusted solar gain factor."""
        return float(
            np.clip(
                self.solar_gain_factor * self.incoming_solar_radiation_factor,
                0.0,
                1.0,
            )
        )

    @property
    def window_area(self) -> float | None:
        """Return configured window glass area in m2."""
        width = self.window_width
        height = self.h_win if hasattr(self, "h_win") else None
        if width is None or height is None:
            return None
        try:
            area = float(width) * float(height)
        except (TypeError, ValueError):
            return None
        return area if area > 0 else None

    @property
    def transmitted_solar_power_source(self) -> str | None:
        """Return the source used for transmitted solar power."""
        return self.solar_radiation_source

    @property
    def transmitted_solar_power_w_m2(self) -> float | None:
        """Return transmitted solar power per square meter of window glass."""
        if self.solar_radiation_value is None:
            return None
        power = self.solar_radiation_value * self.solar_gain_factor
        return float(np.clip(power, 0.0, 2000.0))

    @property
    def transmitted_solar_power_w(self) -> float | None:
        """Return transmitted solar power for the configured window area."""
        if self.window_area is None or self.transmitted_solar_power_w_m2 is None:
            return None
        return self.transmitted_solar_power_w_m2 * self.window_area

    @property
    def heat_power_outside_temperature(self) -> float | None:
        """Return current outside temperature from weather, falling back to forecast."""
        if self.weather_entity is not None:
            value = state_attr(self.hass, self.weather_entity, "temperature")
            if value is not None:
                try:
                    return float(value)
                except (TypeError, ValueError):
                    pass
        return self.forecast_today_max_temp

    @property
    def heat_power_limit_active(self) -> bool:
        """Return whether the heat-power cap may constrain the open position."""
        if not self.heat_power_limit_enabled:
            return False
        if not self.direct_sun_valid:
            return False
        if (
            self.max_transmitted_solar_power_w_m2 is None
            or self.max_transmitted_solar_power_w_m2 <= 0
        ):
            return False
        return self.heat_power_temperature_gate_active

    @property
    def heat_power_temperature_gate_active(self) -> bool:
        """Return whether temperature or forecast allows the watt cap.

        The watt cap is a binary safety rail: when measured heat power is above
        the configured W limit, it may close on either a currently hot outside
        temperature or a forecast hot/very-hot day. This keeps cool mornings on
        hot days from missing preemptive shading, while a measured cold outside
        temperature still blocks heat protection.
        """
        threshold = self.heat_power_outside_temp_threshold
        if threshold is None:
            return True

        outside_temp = self.heat_power_outside_temperature
        if outside_temp is not None and float(outside_temp) >= float(threshold):
            return True

        hot_threshold = self.forecast_hot_day_threshold
        if self.hot_day_signal is None or hot_threshold is None:
            return False
        if not self.forecast_preemptive_active:
            return False
        if not self.heat_protection_current_temperature_allowed:
            return False
        return float(self.hot_day_signal) >= float(hot_threshold)

    @property
    def heat_power_limit_trigger(self) -> str:
        """Return the active temperature trigger for diagnostics."""
        if not self.heat_power_limit_enabled:
            return "disabled"
        if not self.direct_sun_valid:
            return "no_direct_sun"
        if (
            self.max_transmitted_solar_power_w_m2 is None
            or self.max_transmitted_solar_power_w_m2 <= 0
        ):
            return "no_watt_limit"
        threshold = self.heat_power_outside_temp_threshold
        if threshold is None:
            return "always"
        outside_temp = self.heat_power_outside_temperature
        if outside_temp is not None and float(outside_temp) >= float(threshold):
            return "outside_temperature"
        if not self.heat_protection_current_temperature_allowed:
            return "cold_lockout"
        hot_threshold = self.forecast_hot_day_threshold
        if (
            self.hot_day_signal is not None
            and hot_threshold is not None
            and self.forecast_preemptive_active
            and self.heat_protection_current_temperature_allowed
            and float(self.hot_day_signal) >= float(hot_threshold)
        ):
            if (
                self.forecast_very_hot_day_threshold is not None
                and float(self.hot_day_signal)
                >= float(self.forecast_very_hot_day_threshold)
            ):
                return "very_hot_forecast"
            return "hot_forecast"
        return "below_temperature_gate"

    @property
    def heat_protection_current_temperature_allowed(self) -> bool:
        """Return whether current outside temperature is not too cold for heat protection."""
        threshold = self.heat_power_outside_temp_threshold
        outside_temp = self.heat_power_outside_temperature
        if self.heat_protection_min_outside_temp is None or outside_temp is None:
            return True
        return float(outside_temp) >= float(self.heat_protection_min_outside_temp)

    @property
    def heat_power_limited_open_position(self) -> int | None:
        """Return max open position needed to stay below configured W/m2 cap."""
        if not self.heat_power_limit_active:
            return None
        power = self.transmitted_solar_power_w_m2
        if power is None or power <= 0:
            return None
        limit = float(self.max_transmitted_solar_power_w_m2)
        if power <= limit:
            return None
        return int(np.clip(round((limit / power) * 100), 0, 100))

    @property
    def forecast_today_max_temp(self) -> float | None:
        """Return today's forecast maximum temperature."""
        value = (self.forecast_summary or {}).get("today_max_temp")
        return None if value is None else float(value)

    @property
    def forecast_tomorrow_max_temp(self) -> float | None:
        """Return tomorrow's forecast maximum temperature."""
        value = (self.forecast_summary or {}).get("tomorrow_max_temp")
        return None if value is None else float(value)

    @property
    def forecast_temperature_risk(self) -> float:
        """Return the maximum selected forecast temperature risk."""
        risks = [0.0]
        if self.use_forecast_max_temp_today:
            risks.append(
                temperature_risk(
                    self.forecast_today_max_temp,
                    self.forecast_hot_day_threshold,
                    self.forecast_very_hot_day_threshold,
                )
            )
        if self.use_forecast_max_temp_tomorrow:
            risks.append(
                temperature_risk(
                    self.forecast_tomorrow_max_temp,
                    self.forecast_hot_day_threshold,
                    self.forecast_very_hot_day_threshold,
                )
            )
        return max(risks)

    @property
    def forecast_preemptive_active(self) -> bool:
        """Return whether forecast-based pre-emptive mode is currently active."""
        return after_preemptive_start(
            self.evaluation_datetime or datetime.now(),
            self.forecast_preemptive_start_time,
        )

    @property
    def forecast_risk_factor(self) -> float:
        """Return the composite forecast risk factor."""
        risk = (
            self.forecast_temperature_risk
            * (
                self.forecast_solar_radiation_risk
                if self.forecast_solar_radiation_risk is not None
                else 1.0
            )
        )
        if not self.forecast_preemptive_active:
            return 0.0
        return float(np.clip(risk, 0.0, 1.0))

    @property
    def heat_protection_temperature_signal(self) -> float | None:
        """Return the forecast temperature used as hard heat-protection gate."""
        values: list[float] = []
        if self.forecast_today_max_temp is not None:
            values.append(float(self.forecast_today_max_temp))
        if (
            self.use_forecast_max_temp_tomorrow
            and self.forecast_tomorrow_max_temp is not None
        ):
            values.append(float(self.forecast_tomorrow_max_temp))
        if not values:
            return None
        return max(values)

    @property
    def heat_protection_temperature_allowed(self) -> bool:
        """Return whether forecast temperature allows heat-protection shading."""
        if not self.heat_protection_current_temperature_allowed:
            return False
        if (
            self.heat_protection_temperature_signal is None
            or self.forecast_hot_day_threshold is None
        ):
            return True
        return (
            float(self.heat_protection_temperature_signal)
            >= float(self.forecast_hot_day_threshold)
        )

    @property
    def forecast_adjusted_gain_factor(self) -> float:
        """Return the gain factor with forecast-based policy uplift."""
        if not self.heat_protection_temperature_allowed:
            return 0.0
        return float(
            np.clip(
                self.effective_solar_gain_factor * self.forecast_gain_uplift_factor,
                0.0,
                1.0,
            )
        )

    @property
    def forecast_temperature_gain_boost(self) -> float:
        """Return the direct very-hot temperature boost signal for gain uplift."""
        if (
            not self.heat_protection_temperature_allowed
            or not self.forecast_preemptive_active
        ):
            return 0.0
        return float(np.clip(self.forecast_temperature_risk, 0.0, 1.0))

    @property
    def forecast_gain_uplift_factor(self) -> float:
        """Return the forecast multiplier applied to the physical solar gain.

        Hot opens the heat-protection gate. Very hot then increases the gain
        response directly; absolute forecast solar radiation is the only
        weather forecast proxy that still participates in heat-gain pressure.
        """
        if not self.heat_protection_temperature_allowed:
            return 0.0
        strength = float(self.forecast_influence_strength or 0.0)
        return float(
            np.clip(
                1.0
                + strength * self.forecast_risk_factor
                + strength * self.forecast_temperature_gain_boost,
                1.0,
                1.0 + (2.0 * strength),
            )
        )

    @property
    def forecast_temperature_policy_pressure(self) -> float:
        """Return the policy strictness caused by very-hot forecast."""
        if not self.heat_protection_temperature_allowed or not self.forecast_preemptive_active:
            return 0.0
        return very_hot_policy_pressure(
            self.forecast_temperature_risk,
            self.forecast_influence_strength,
        )

    @property
    def forecast_temperature_band(self) -> str:
        """Return the current forecast temperature control band."""
        signal = self.heat_protection_temperature_signal
        if signal is None or self.forecast_hot_day_threshold is None:
            return "no_temperature_signal"
        if not self.heat_protection_temperature_allowed:
            return "below_hot"
        if (
            self.forecast_very_hot_day_threshold is not None
            and float(signal) >= float(self.forecast_very_hot_day_threshold)
        ):
            return "very_hot_saturated"
        if self.forecast_temperature_risk > 0:
            return "between_hot_and_very_hot"
        return "hot_gate_only"

    @property
    def forecast_temperature_effect_note(self) -> str:
        """Explain why hot and very-hot may or may not visibly differ."""
        if not self.heat_protection_temperature_allowed:
            return "below hot-day threshold; heat protection is disabled"
        if not self.forecast_preemptive_active:
            return "before preemptive start; very-hot pressure is inactive"
        if self.forecast_temperature_band == "very_hot_saturated":
            return "at or above very-hot threshold; additional temperature no longer increases pressure"
        if self.policy_action_level == "full":
            return "full policy target already reached; temperature can only reach it earlier"
        if self.forecast_temperature_policy_pressure > 0:
            return "very-hot pressure lowers thresholds and moves the partial target toward the strict target"
        return "hot-day gate is open, but very-hot pressure is still zero"

    @property
    def forecast_temperature_threshold_reduction(self) -> float:
        """Return how much very-hot pressure lowers score thresholds."""
        return 0.20 * self.forecast_temperature_policy_pressure

    @property
    def forecast_temperature_position_offset(self) -> int:
        """Return how much very-hot pressure closes target positions."""
        return int(round(10 * self.forecast_temperature_policy_pressure))

    @property
    def heat_gain_response_factor(self) -> float:
        """Return the practical shading response for the physical gain."""
        return heat_gain_response_factor(self.forecast_adjusted_gain_factor)

    @property
    def hot_day_signal(self) -> float | None:
        """Return the hottest selected forecast temperature signal."""
        values: list[float] = []
        if self.use_forecast_max_temp_today and self.forecast_today_max_temp is not None:
            values.append(float(self.forecast_today_max_temp))
        if (
            self.use_forecast_max_temp_tomorrow
            and self.forecast_tomorrow_max_temp is not None
        ):
            values.append(float(self.forecast_tomorrow_max_temp))
        if not values:
            return None
        return max(values)

    @property
    def hot_day_override_active(self) -> bool:
        """Return whether the strict hot-day override is active."""
        if not self.hot_day_close_enabled:
            return False
        if self.sunset_valid or not self.forecast_preemptive_active:
            return False
        if (
            not self.direct_sun_valid
            or self.direct_solar_exposure_factor <= 0.001
            or self.incoming_solar_radiation_factor <= 0.001
        ):
            return False
        if not self.heat_protection_current_temperature_allowed:
            return False
        if self.hot_day_signal is None or self.hot_day_close_threshold is None:
            return False
        return float(self.hot_day_signal) >= float(self.hot_day_close_threshold)

    @property
    def very_hot_day_override_active(self) -> bool:
        """Return whether the stricter very-hot open limit is active."""
        if not self.hot_day_override_active:
            return False
        if self.hot_day_signal is None or self.forecast_very_hot_day_threshold is None:
            return False
        return float(self.hot_day_signal) >= float(self.forecast_very_hot_day_threshold)

    @property
    def active_hot_day_close_position(self) -> int | None:
        """Return the active hot/very-hot open-position cap."""
        if not self.hot_day_override_active:
            return None
        if self.very_hot_day_override_active and self.very_hot_day_close_position is not None:
            return int(np.clip(self.very_hot_day_close_position, 0, 100))
        if self.hot_day_close_position is None:
            return None
        return int(np.clip(self.hot_day_close_position, 0, 100))

    @property
    def policy_component_values(self) -> dict[str, float | None]:
        """Return the active heat-gain policy components."""
        return {
            "direct_exposure": self.direct_solar_exposure_factor,
            "incidence": self.incidence_cosine,
            "glazing": self.solar_transmittance_factor,
            "solar_radiation": (
                self.solar_radiation_factor
                if (
                    self.use_open_data_solar_radiation
                    or self.solar_radiation_entity is not None
                )
                else None
            ),
            "forecast_temperature": (
                temperature_boost_signal(self.forecast_temperature_risk)
                if (
                    self.use_forecast_max_temp_today
                    or self.use_forecast_max_temp_tomorrow
                )
                else None
            ),
        }

    @property
    def policy_component_weights(self) -> dict[str, float]:
        """Return the configured weights for the heat-gain policy."""
        if not self.show_expert_weights:
            preset_weights = preset_weights_for_name(self.policy_preset)
            if preset_weights:
                return preset_weights
        return {
            "direct_exposure": float(self.weight_direct_exposure or 0.0),
            "incidence": float(self.weight_incidence or 0.0),
            "glazing": float(self.weight_glazing or 0.0),
            "solar_radiation": float(self.weight_solar_radiation or 0.0),
            "forecast_temperature": float(self.weight_forecast_temperature or 0.0),
        }

    @property
    def heat_gain_policy_active(self) -> bool:
        """Return whether the heat-gain overlay policy is enabled."""
        weight_policy_active = self.enable_heat_gain_policy and any(
            weight > 0.0 for weight in self.policy_component_weights.values()
        )
        return weight_policy_active or self.hot_day_override_active

    @property
    def policy_weighted_score(self) -> float:
        """Return the raw weighted heat-gain score before physical gating."""
        return weighted_risk_score(
            self.policy_component_values,
            self.policy_component_weights,
        )

    @property
    def policy_raw_score(self) -> float:
        """Return the weighted heat-gain score limited by physical gain."""
        return gain_limited_policy_score(
            self.policy_weighted_score,
            self.heat_gain_response_factor,
        )

    @property
    def policy_preset_score(self) -> float:
        """Return the score after preset and daylight-window adjustment."""
        return adjusted_policy_score(
            self.policy_raw_score,
            self.policy_preset,
            self.has_additional_daylight_windows,
        )

    @property
    def policy_score(self) -> float:
        """Return the final heat-gain policy score."""
        return away_adjusted_score(
            self.policy_preset_score,
            self.away_mode_active,
            self.away_score_multiplier,
        )

    @property
    def away_mode_active(self) -> bool:
        """Return whether stricter away-from-home mode is active."""
        if not self.enable_away_mode or not self.away_entity:
            return False

        state = get_safe_state(self.hass, self.away_entity)
        if state is None:
            return False

        domain = get_domain(self.away_entity)
        if domain in ["person", "device_tracker"]:
            return state != "home"
        if domain == "zone":
            try:
                return int(state) <= 0
            except (TypeError, ValueError):
                return False
        if domain in ["binary_sensor", "input_boolean"]:
            return state == "off"
        return str(state).lower() not in ["home", "on", "true", "1"]

    @property
    def base_policy_thresholds(self) -> tuple[float, float]:
        """Return configured partial and full thresholds before adjustments."""
        return (
            float(self.partial_close_threshold or 0.35),
            float(self.full_close_threshold or 0.65),
        )

    @property
    def preset_policy_thresholds(self) -> tuple[float, float]:
        """Return thresholds after preset and daylight-window adjustment."""
        partial, full = self.base_policy_thresholds
        return adjusted_thresholds(
            partial,
            full,
            self.policy_preset,
            self.has_additional_daylight_windows,
        )

    @property
    def away_policy_thresholds(self) -> tuple[float, float]:
        """Return thresholds after away-from-home adjustment."""
        partial, full = self.preset_policy_thresholds
        return away_adjusted_thresholds(
            partial,
            full,
            self.away_mode_active,
            self.away_threshold_reduction,
        )

    @property
    def effective_partial_close_threshold(self) -> float:
        """Return the final partial close threshold."""
        partial, full = self.away_policy_thresholds
        return temperature_adjusted_thresholds(
            partial,
            full,
            self.forecast_temperature_policy_pressure,
        )[0]

    @property
    def effective_full_close_threshold(self) -> float:
        """Return the final full close threshold."""
        partial, full = self.away_policy_thresholds
        return temperature_adjusted_thresholds(
            partial,
            full,
            self.forecast_temperature_policy_pressure,
        )[1]

    @property
    def base_policy_positions(self) -> tuple[int, int]:
        """Return configured partial and full open-position targets, normalized."""
        partial, full = self.configured_policy_positions
        return normalize_policy_positions(partial, full)

    @property
    def configured_policy_positions(self) -> tuple[int, int]:
        """Return stored partial and full policy position values."""
        return (
            int(self.partial_close_position or 55),
            int(self.full_close_position or 85),
        )

    @property
    def legacy_policy_position_input_detected(self) -> bool:
        """Return whether stored policy positions use legacy closed notation."""
        partial, full = self.configured_policy_positions
        return legacy_position_input_detected(partial, full)

    @property
    def preset_policy_positions(self) -> tuple[int, int]:
        """Return open-position targets after preset adjustment."""
        partial, full = self.base_policy_positions
        return adjusted_positions(
            partial,
            full,
            self.policy_preset,
            self.has_additional_daylight_windows,
        )

    @property
    def away_policy_positions(self) -> tuple[int, int]:
        """Return open-position targets after away-from-home adjustment."""
        partial, full = self.preset_policy_positions
        return away_adjusted_positions(
            partial,
            full,
            self.away_mode_active,
            self.away_position_offset,
        )

    @property
    def effective_partial_close_position(self) -> int:
        """Return the final partial close target position."""
        partial, _full = self.away_policy_positions
        return temperature_adjusted_positions(
            partial,
            _full,
            self.forecast_temperature_policy_pressure,
        )[0]

    @property
    def effective_full_close_position(self) -> int:
        """Return the final full close target position."""
        partial, full = self.away_policy_positions
        return temperature_adjusted_positions(
            partial,
            full,
            self.forecast_temperature_policy_pressure,
        )[1]

    @property
    def policy_action_level(self) -> str:
        """Return the active policy action level."""
        if not self.heat_gain_policy_active:
            return "disabled"
        base_level, base_target = policy_target_position(
            self.policy_score,
            self.effective_partial_close_threshold,
            self.effective_full_close_threshold,
            self.effective_partial_close_position,
            self.effective_full_close_position,
        )
        if self.very_hot_day_override_active:
            return "veryhotday"
        active_hot_day_position = self.active_hot_day_close_position
        if (
            self.hot_day_override_active
            and (
                base_level in {"none", "partial"}
                or (
                    active_hot_day_position is not None
                    and active_hot_day_position < int(base_target or 100)
                )
            )
        ):
            return "hotday"
        return base_level

    @property
    def heat_gain_target_position(self) -> int | None:
        """Return the overlay target position from the heat-gain policy."""
        if not self.heat_gain_policy_active:
            return None
        policy_target = policy_target_position(
            self.policy_score,
            self.effective_partial_close_threshold,
            self.effective_full_close_threshold,
            self.effective_partial_close_position,
            self.effective_full_close_position,
        )[1]
        active_hot_day_position = self.active_hot_day_close_position
        if active_hot_day_position is not None:
            return min(active_hot_day_position, int(policy_target or 100))
        return policy_target

    @property
    def sunset_valid(self) -> bool:
        """Determine if it is after sunset plus offset."""
        sunset = self.sun_data.sunset().replace(tzinfo=None)
        sunrise = self.sun_data.sunrise().replace(tzinfo=None)
        now_utc = (self.evaluation_datetime or datetime.now(UTC)).replace(tzinfo=None)
        after_sunset = now_utc > (sunset + timedelta(minutes=self.sunset_off))
        before_sunrise = now_utc < (sunrise + timedelta(minutes=self.sunrise_off))
        self.logger.debug(
            "After sunset plus offset? %s", (after_sunset or before_sunrise)
        )
        return after_sunset or before_sunrise

    @property
    def default(self) -> float:
        """Change default position at sunset."""
        default = self.h_def
        if self.sunset_valid:
            default = self.sunset_pos
        return default

    def fov(self) -> list:
        """Return field of view."""
        return [self.azi_min_abs, self.azi_max_abs]

    @property
    def apply_min_position(self) -> bool:
        """Check if min position is applied."""
        if self.min_pos is not None and self.min_pos != 0:
            if self.min_pos_bool:
                return self.direct_sun_valid
            return True
        return False

    @property
    def apply_max_position(self) -> bool:
        """Check if max position is applied."""
        if self.max_pos is not None and self.max_pos != 100:
            if self.max_pos_bool:
                return self.direct_sun_valid
            return True
        return False

    @property
    def direct_sun_valid(self) -> bool:
        """Check if sun is directly in front of window."""
        return (
            self.valid
            & self.sun_within_horizon_profile
            & (not self.sunset_valid)
            & (not self.is_sun_in_blind_spot)
        )

    @abstractmethod
    def calculate_position(self) -> float:
        """Calculate the position of the blind."""

    @abstractmethod
    def calculate_percentage(self) -> int:
        """Calculate percentage from position."""


@dataclass
class NormalCoverState:
    """Compute state for normal operation."""

    cover: AdaptiveGeneralCover

    def get_state(self) -> int:
        """Return state."""
        self.cover.logger.debug("Determining normal position")
        dsv = self.cover.direct_sun_valid and (
            self.cover.direct_solar_exposure_factor > 0.001
        )
        self.cover.logger.debug(
            "Sun directly in front of window & before sunset + offset? %s", dsv
        )
        if dsv:
            state = self.cover.default
            self.cover.logger.debug(
                "Using default value before heat-gain overlays (%s)",
                state,
            )
            policy_target = self.cover.heat_gain_target_position
            if policy_target is not None:
                state = min(state, policy_target)
                self.cover.logger.debug(
                    "Heat-gain policy reduced open position to %s (policy score %.3f, level %s)",
                    state,
                    self.cover.policy_score,
                    self.cover.policy_action_level,
                )
            heat_power_target = self.cover.heat_power_limited_open_position
            if heat_power_target is not None:
                state = min(state, heat_power_target)
                self.cover.logger.debug(
                    "Heat-power cap reduced open position to %s (%.1f W/m2 estimated, %.1f W/m2 limit)",
                    state,
                    self.cover.transmitted_solar_power_w_m2,
                    self.cover.max_transmitted_solar_power_w_m2,
                )
        else:
            state = self.cover.default
            self.cover.logger.debug("No sun in window: using default value (%s)", state)

        result = np.clip(state, 0, 100)
        if self.cover.apply_max_position and result > self.cover.max_pos:
            return self.cover.max_pos
        if self.cover.apply_min_position and result < self.cover.min_pos:
            return self.cover.min_pos
        return result


@dataclass
class ClimateCoverData:
    """Fetch additional data."""

    hass: HomeAssistant
    logger: ConfigContextAdapter
    temp_entity: str
    temp_low: float
    temp_high: float
    presence_entity: str
    weather_entity: str
    outside_entity: str
    temp_switch: bool
    blind_type: str
    transparent_blind: bool
    irradiance_entity: str
    irradiance_threshold: int
    temp_summer_outside: float
    _use_irradiance: bool

    @property
    def outside_temperature(self):
        """Get outside temperature."""
        temp = None
        if self.outside_entity:
            temp = get_safe_state(
                self.hass,
                self.outside_entity,
            )
        elif self.weather_entity:
            temp = state_attr(self.hass, self.weather_entity, "temperature")
        return temp

    @property
    def inside_temperature(self):
        """Get inside temp from entity."""
        if self.temp_entity is not None:
            if get_domain(self.temp_entity) != "climate":
                temp = get_safe_state(
                    self.hass,
                    self.temp_entity,
                )
            else:
                temp = state_attr(self.hass, self.temp_entity, "current_temperature")
            return temp

    @property
    def get_current_temperature(self) -> float:
        """Get temperature."""
        if self.temp_switch:
            if self.outside_temperature:
                return float(self.outside_temperature)
        if self.inside_temperature:
            return float(self.inside_temperature)

    @property
    def is_presence(self):
        """Checks if people are present."""
        presence = None
        if self.presence_entity is not None:
            presence = get_safe_state(self.hass, self.presence_entity)
        # set to true if no sensor is defined
        if presence is not None:
            domain = get_domain(self.presence_entity)
            if domain == "device_tracker":
                return presence == "home"
            if domain == "zone":
                return int(presence) > 0
            if domain in ["binary_sensor", "input_boolean"]:
                return presence == "on"
        return True

    @property
    def is_winter(self) -> bool:
        """Check if temperature is below threshold."""
        if self.temp_low is not None and self.get_current_temperature is not None:
            is_it = self.get_current_temperature < self.temp_low
        else:
            is_it = False

        self.logger.debug(
            "is_winter(): current_temperature < temp_low: %s < %s = %s",
            self.get_current_temperature,
            self.temp_low,
            is_it,
        )
        return is_it

    @property
    def outside_high(self) -> bool:
        """Check if outdoor temperature is above threshold."""
        if (
            self.temp_summer_outside is not None
            and self.outside_temperature is not None
        ):
            return float(self.outside_temperature) > self.temp_summer_outside
        return True

    @property
    def is_summer(self) -> bool:
        """Check if temperature is over threshold."""
        if self.temp_high is not None and self.get_current_temperature is not None:
            is_it = self.get_current_temperature > self.temp_high and self.outside_high
        else:
            is_it = False

        self.logger.debug(
            "is_summer(): current_temp > temp_high and outside_high?: %s > %s and %s = %s",
            self.get_current_temperature,
            self.temp_high,
            self.outside_high,
            is_it,
        )
        return is_it

    @property
    def irradiance(self) -> bool:
        """Get irradiance value and compare to threshold."""
        if not self._use_irradiance:
            return False
        if self.irradiance_entity is not None and self.irradiance_threshold is not None:
            value = get_safe_state(self.hass, self.irradiance_entity)
            return float(value) <= self.irradiance_threshold
        return False


@dataclass
class ClimateCoverState(NormalCoverState):
    """Compute state for climate control operation."""

    climate_data: ClimateCoverData

    def normal_type_cover(self) -> int:
        """Determine state for horizontal and vertical covers."""

        self.cover.logger.debug("Is presence? %s", self.climate_data.is_presence)

        if self.climate_data.is_presence:
            return self.normal_with_presence()

        return self.normal_without_presence()

    def normal_with_presence(self) -> int:
        """Determine state for horizontal and vertical covers with occupants."""

        is_summer = self.climate_data.is_summer

        # A local irradiance sensor may still open the cover on low-radiation days.
        if not is_summer and self.climate_data.irradiance:
            # If it's winter and the cover is valid, return 100
            if self.climate_data.is_winter and self.cover.valid:
                self.cover.logger.debug(
                    "n_w_p(): Winter and sun is in front of window = use 100"
                )
                return 100
            # Otherwise, return the default cover state
            self.cover.logger.debug(
                "n_w_p(): low irradiance outside summer = use default"
            )
            return self.cover.default

        # If it's summer and there's a transparent blind, return 0
        if is_summer and self.climate_data.transparent_blind:
            return 0

        # If none of the above conditions are met, get the state from the parent class
        self.cover.logger.debug("n_w_p(): None of the climate conditions are met")
        return super().get_state()

    def normal_without_presence(self) -> int:
        """Determine state for horizontal and vertical covers without occupants."""
        if self.cover.valid:
            if self.climate_data.is_summer:
                return 0
            if self.climate_data.is_winter:
                return 100
        return self.cover.default

    def tilt_with_presence(self, degrees: int) -> int:
        """Determine state for tilted blinds with occupants."""
        if self.cover.valid and (
            self.climate_data.irradiance
        ):
            if self.climate_data.is_summer:
                # If it's summer, return 45 degrees
                return 45 / degrees * 100
            return super().get_state()
        return 80 / degrees * 100

    def tilt_without_presence(self, degrees: int) -> int:
        """Determine state for tilted blinds without occupants."""
        beta = np.rad2deg(self.cover.beta)
        if self.cover.valid:
            if self.climate_data.is_summer:
                # block out all light in summer
                return 0
            if self.climate_data.is_winter and self.cover.mode == "mode2":
                # parallel to sun beams, not possible with single direction
                return (beta + 90) / degrees * 100
            return 80 / degrees * 100
        return super().get_state()

    def tilt_state(self):
        """Add tilt specific controls."""
        degrees = 90
        if self.cover.mode == "mode2":
            degrees = 180
        if self.climate_data.is_presence:
            return self.tilt_with_presence(degrees)
        return self.tilt_without_presence(degrees)

    def get_state(self) -> int:
        """Return state."""
        result = self.normal_type_cover()
        if self.climate_data.blind_type == "cover_tilt":
            result = self.tilt_state()
        if self.cover.apply_max_position and result > self.cover.max_pos:
            self.cover.logger.debug(
                "Climate state: Max position applied (%s > %s)",
                result,
                self.cover.max_pos,
            )
            return self.cover.max_pos
        if self.cover.apply_min_position and result < self.cover.min_pos:
            self.cover.logger.debug(
                "Climate state: Min position applied (%s < %s)",
                result,
                self.cover.min_pos,
            )
            return self.cover.min_pos
        return result


@dataclass
class AdaptiveVerticalCover(AdaptiveGeneralCover):
    """Calculate state for Vertical blinds."""

    distance: float
    h_win: float

    def calculate_position(self) -> float:
        """Calculate blind height."""
        # calculate blind height
        blind_height = np.clip(
            (self.distance / cos(rad(self.gamma))) * tan(rad(self.sol_elev)),
            0,
            self.h_win,
        )
        return blind_height

    def calculate_percentage(self) -> float:
        """Convert blind height to Home Assistant open percentage."""
        position = self.calculate_position()
        self.logger.debug(
            "Converting height to percentage: %s / %s * 100", position, self.h_win
        )
        result = 100 - (position / self.h_win * 100)
        return round(result)


@dataclass
class AdaptiveHorizontalCover(AdaptiveVerticalCover):
    """Calculate state for Horizontal blinds."""

    awn_length: float
    awn_angle: float

    def calculate_position(self) -> float:
        """Calculate awn length from blind height."""
        awn_angle = 90 - self.awn_angle
        a_angle = 90 - self.sol_elev
        c_angle = 180 - awn_angle - a_angle

        vertical_position = super().calculate_position()
        length = ((self.h_win - vertical_position) * sin(rad(a_angle))) / sin(
            rad(c_angle)
        )
        # return np.clip(length, 0, self.awn_length)
        return length

    def calculate_percentage(self) -> float:
        """Convert awn length to percentage or default value."""
        result = self.calculate_position() / self.awn_length * 100
        return round(result)


@dataclass
class AdaptiveTiltCover(AdaptiveGeneralCover):
    """Calculate state for tilted blinds."""

    slat_distance: float
    depth: float
    mode: str

    @property
    def beta(self):
        """Calculate beta."""
        beta = np.arctan(tan(rad(self.sol_elev)) / cos(rad(self.gamma)))
        return beta

    def calculate_position(self) -> float:
        """Calculate position of venetian blinds.

        https://www.mdpi.com/1996-1073/13/7/1731
        """
        beta = self.beta

        slat = 2 * np.arctan(
            (
                tan(beta)
                + np.sqrt(
                    (tan(beta) ** 2) - ((self.slat_distance / self.depth) ** 2) + 1
                )
            )
            / (1 + self.slat_distance / self.depth)
        )
        result = np.rad2deg(slat)

        return result

    def calculate_percentage(self):
        """Convert tilt angle to percentages or default value."""
        # 0 degrees is closed, 90 degrees is open, 180 degrees is closed
        percentage_single = self.calculate_position() / 90 * 100  # single directional
        percentage_bi = self.calculate_position() / 180 * 100  # bi-directional

        if self.mode == "mode1":
            percentage = percentage_single
        else:
            percentage = percentage_bi

        return round(percentage)

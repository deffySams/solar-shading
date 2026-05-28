"""HTTP simulator endpoint backed by the real Solar Shading calculation code."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .calculation import AdaptiveVerticalCover, NormalCoverState
from .config_context_adapter import ConfigContextAdapter
from .const import _LOGGER

SIMULATOR_API_URL = "/api/solar_shading/simulate"


@dataclass
class _SimulationState:
    """Minimal state object for simulator-only entities."""

    state: str
    attributes: dict[str, Any]


class _SimulationStates:
    """State registry proxy with simulator overrides."""

    def __init__(self, hass: HomeAssistant, states: dict[str, _SimulationState]) -> None:
        self._hass = hass
        self._states = states

    def get(self, entity_id: str):
        """Return simulator state first, then real Home Assistant state."""
        return self._states.get(entity_id) or self._hass.states.get(entity_id)


class _SimulationHass:
    """Small proxy exposing the Home Assistant pieces used by calculation.py."""

    def __init__(self, hass: HomeAssistant, states: dict[str, _SimulationState]) -> None:
        self.config = hass.config
        self.data = hass.data
        self.states = _SimulationStates(hass, states)


class _SimulationSunData:
    """Sunrise/sunset stub matching the simulator's selected daylight state."""

    def __init__(self, daytime: bool, now: datetime) -> None:
        self._daytime = daytime
        self._now = now.astimezone(UTC).replace(tzinfo=None)

    def sunset(self) -> datetime:
        """Return a synthetic sunset relative to the selected simulator time."""
        if self._daytime:
            return self._now + timedelta(hours=6)
        return self._now - timedelta(hours=1)

    def sunrise(self) -> datetime:
        """Return a synthetic sunrise relative to the selected simulator time."""
        if self._daytime:
            return self._now - timedelta(hours=6)
        return self._now + timedelta(hours=6)


class SolarShadingSimulationView(HomeAssistantView):
    """Run a simulator calculation through the real Python policy code."""

    url = SIMULATOR_API_URL
    name = "api:solar_shading:simulate"
    requires_auth = True

    async def post(self, request):
        """Handle a simulator request."""
        hass: HomeAssistant = request.app["hass"]
        payload = await request.json()
        return self.json(simulate_from_payload(hass, payload))


def _float(values: dict[str, Any], key: str, default: float | None = None) -> float | None:
    value = values.get(key, default)
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _int(values: dict[str, Any], key: str, default: int = 0) -> int:
    value = _float(values, key, default)
    return int(round(value if value is not None else default))


def _bool(values: dict[str, Any], key: str, default: bool = False) -> bool:
    value = values.get(key, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _time_to_datetime(values: dict[str, Any]) -> datetime:
    year = _int(values, "year", datetime.now().year)
    month = _int(values, "month", datetime.now().month)
    day = _int(values, "day", datetime.now().day)
    time_text = str(values.get("time") or "12:00")
    hour_text, minute_text = (time_text.split(":") + ["0"])[:2]
    return datetime(
        year,
        month,
        day,
        int(hour_text),
        int(minute_text),
    )


def _round(value: Any, digits: int = 4):
    if value is None:
        return None
    try:
        return round(float(value), digits)
    except (TypeError, ValueError):
        return value


def simulate_from_payload(hass: HomeAssistant, payload: dict[str, Any]) -> dict[str, Any]:
    """Run one simulator calculation with the production Python code."""
    values = payload.get("values") or payload
    sun = payload.get("sun") or {}
    now = _time_to_datetime(values)
    weather_entity = "weather.solar_shading_simulator"
    radiation_entity = (
        "sensor.solar_shading_simulator_radiation"
        if _bool(values, "useOpenDataSolarRadiation")
        else None
    )
    away_entity = "input_boolean.solar_shading_simulator_away"
    precipitation = _float(values, "precipitation", 0.0) or 0.0
    cloud_coverage = _float(values, "cloudCoverage", 0.0) or 0.0
    fake_states = {
        weather_entity: _SimulationState(
            "rainy" if precipitation > 0 else "partlycloudy",
            {
                "temperature": _float(values, "outsideTemp"),
                "cloud_coverage": cloud_coverage,
                "precipitation": precipitation,
            },
        ),
        away_entity: _SimulationState(
            "off" if _bool(values, "awayActive") else "on",
            {},
        ),
    }
    if radiation_entity:
        fake_states[radiation_entity] = _SimulationState(
            str(_float(values, "solarRadiation", 0.0) or 0.0),
            {},
        )

    logger = ConfigContextAdapter(_LOGGER)
    logger.set_config_name("simulator")
    cover = AdaptiveVerticalCover(
        hass=hass,
        logger=logger,
        sol_azi=_float(sun, "azimuth", 0.0) or 0.0,
        sol_elev=_float(sun, "elevation", 0.0) or 0.0,
        sunset_pos=_int(values, "sunsetPosition", 100),
        sunset_off=0,
        sunrise_off=0,
        timezone=str(hass.config.time_zone),
        fov_left=_int(values, "fovLeft", 90),
        fov_right=_int(values, "fovRight", 90),
        win_azi=_int(values, "windowAzimuth", 90),
        h_def=_int(values, "defaultPosition", 100),
        max_pos=100,
        min_pos=0,
        max_pos_bool=False,
        min_pos_bool=False,
        blind_spot_left=None,
        blind_spot_right=None,
        blind_spot_elevation=None,
        blind_spot_on=False,
        min_elevation=_int(values, "minElevation", 0),
        max_elevation=_int(values, "maxElevation", 90),
        horizon_profile=values.get("horizonProfile"),
        window_width=_float(values, "windowWidth"),
        reveal_left_depth=_float(values, "revealLeft"),
        reveal_right_depth=_float(values, "revealRight"),
        reveal_top_depth=_float(values, "revealTop"),
        glass_type=values.get("glassType") or "double_clear",
        weather_entity=weather_entity,
        forecast_summary={
            "today_max_temp": _float(values, "forecastTodayMax"),
            "today_cloud_coverage": _float(values, "forecastCloudCoverage"),
            "today_precipitation_probability": _float(values, "forecastRainProb"),
            "today_precipitation_amount": _float(values, "forecastRainAmount"),
            "today_uv_index": _float(values, "forecastUv"),
            "tomorrow_max_temp": _float(values, "forecastTomorrowMax"),
        },
        solar_radiation_summary={
            "current_direct_normal_irradiance": _float(values, "solarRadiation"),
            "current_shortwave_radiation": _float(values, "solarRadiation"),
            "today_max_direct_normal_irradiance": _float(values, "forecastSolarMax"),
            "today_max_shortwave_radiation": _float(values, "forecastSolarMax"),
        },
        use_open_data_solar_radiation=_bool(values, "useOpenDataSolarRadiation"),
        solar_radiation_entity=radiation_entity,
        solar_radiation_reference=_float(values, "solarReference", 900.0),
        heat_power_limit_enabled=_bool(values, "heatPowerLimitEnabled"),
        heat_power_outside_temp_threshold=_float(values, "heatPowerTempThreshold"),
        heat_protection_min_outside_temp=_float(values, "heatProtectionMinOutsideTemp"),
        heat_power_max_watts=_float(values, "heatPowerMaxWatts"),
        use_forecast_max_temp_today=_bool(values, "useTodayMax", True),
        use_forecast_max_temp_tomorrow=_bool(values, "useTomorrowMax"),
        use_forecast_cloud_coverage=_bool(values, "useForecastClouds"),
        use_forecast_precipitation_probability=_bool(values, "useForecastRainProb"),
        use_forecast_precipitation_amount=_bool(values, "useForecastRainAmount"),
        use_forecast_uv_index=_bool(values, "useForecastUv"),
        forecast_hot_day_threshold=_float(values, "hotDayThreshold"),
        forecast_very_hot_day_threshold=_float(values, "veryHotThreshold"),
        forecast_preemptive_start_time=str(values.get("preemptiveStart") or "00:00"),
        forecast_influence_strength=_float(values, "forecastInfluence", 0.5),
        enable_heat_gain_policy=_bool(values, "enableHeatGainPolicy", True),
        policy_preset=values.get("policyPreset") or "balanced",
        has_additional_daylight_windows=_bool(values, "additionalWindows"),
        enable_away_mode=_bool(values, "awayActive"),
        away_entity=away_entity,
        away_score_multiplier=_float(values, "awayScoreMultiplier", 1.25),
        away_threshold_reduction=_float(values, "awayThresholdReduction", 0.1),
        away_position_offset=_int(values, "awayPositionOffset", 10),
        hot_day_close_enabled=_bool(values, "hotDayCloseEnabled"),
        hot_day_close_threshold=_float(values, "hotDayCloseThreshold"),
        hot_day_close_position=_int(values, "hotDayClosePosition", 30),
        very_hot_day_close_position=_int(values, "veryHotDayClosePosition", 15),
        enable_legacy_basic_shading=_bool(values, "enableLegacyBasicShading"),
        show_expert_weights=_bool(values, "showExpertWeights"),
        weight_direct_exposure=_float(values, "weightDirect"),
        weight_incidence=_float(values, "weightIncidence"),
        weight_glazing=_float(values, "weightGlazing"),
        weight_weather=_float(values, "weightWeather"),
        weight_forecast_temperature=_float(values, "weightForecastTemp"),
        weight_forecast_uv=_float(values, "weightForecastUv"),
        weight_forecast_clouds=_float(values, "weightForecastClouds"),
        weight_forecast_precipitation_probability=_float(values, "weightForecastRainProb"),
        weight_forecast_precipitation_amount=_float(values, "weightForecastRainAmount"),
        weight_solar_radiation=_float(values, "weightSolarRadiation"),
        partial_close_threshold=_float(values, "partialThreshold"),
        full_close_threshold=_float(values, "fullThreshold"),
        partial_close_position=_int(values, "partialPosition", 55),
        full_close_position=_int(values, "fullPosition", 85),
        evaluation_datetime=now,
        distance=_float(values, "distance", 0.5) or 0.5,
        h_win=_float(values, "windowHeight", 2.1) or 2.1,
    )
    cover.hass = _SimulationHass(hass, fake_states)
    cover.sun_data = _SimulationSunData(cover.sol_elev > 0, now)
    open_position = int(round(NormalCoverState(cover).get_state()))
    attrs = {
        "local_solar_angle": _round(cover.local_solar_angle, 2),
        "effective_lower_horizon_elevation": _round(cover.effective_lower_horizon_elevation, 2),
        "effective_upper_horizon_elevation": _round(cover.effective_upper_horizon_elevation, 2),
        "sun_within_horizon_profile": cover.sun_within_horizon_profile,
        "left_reveal_shadow_pct": _round(cover.left_reveal_shadow * 100, 2),
        "right_reveal_shadow_pct": _round(cover.right_reveal_shadow * 100, 2),
        "top_reveal_shadow_pct": _round(cover.top_reveal_shadow * 100, 2),
        "total_reveal_shadow_pct": _round(cover.total_reveal_shadow * 100, 2),
        "direct_solar_exposure_factor": _round(cover.direct_solar_exposure_factor),
        "incidence_angle_deg": _round(cover.incidence_angle_deg, 2),
        "incidence_cosine": _round(cover.incidence_cosine),
        "solar_transmittance_factor": _round(cover.solar_transmittance_factor),
        "solar_reflectance_factor": _round(cover.solar_reflectance_factor),
        "weather_factor": _round(cover.weather_factor),
        "solar_radiation_factor": _round(cover.solar_radiation_factor),
        "radiation_or_weather_factor": _round(cover.radiation_or_weather_factor),
        "effective_solar_gain_factor": _round(cover.effective_solar_gain_factor),
        "estimated_solar_heat_power_w_m2": _round(cover.estimated_solar_heat_power_w_m2, 2),
        "estimated_solar_heat_power_w": _round(cover.estimated_solar_heat_power_w, 2),
        "heat_power_limit_active": cover.heat_power_limit_active,
        "heat_power_limit_trigger": cover.heat_power_limit_trigger,
        "heat_power_limited_open_position": cover.heat_power_limited_open_position,
        "forecast_temperature_risk": _round(cover.forecast_temperature_risk),
        "forecast_risk_factor": _round(cover.forecast_risk_factor),
        "forecast_temperature_gain_boost": _round(cover.forecast_temperature_gain_boost),
        "forecast_gain_uplift_factor": _round(cover.forecast_gain_uplift_factor),
        "forecast_temperature_policy_pressure": _round(cover.forecast_temperature_policy_pressure),
        "forecast_adjusted_gain_factor": _round(cover.forecast_adjusted_gain_factor),
        "heat_gain_response_factor": _round(cover.heat_gain_response_factor),
        "heat_gain_policy_weighted_score": _round(cover.policy_weighted_score),
        "heat_gain_policy_raw_score": _round(cover.policy_raw_score),
        "heat_gain_policy_score": _round(cover.policy_score),
        "heat_gain_policy_action_level": cover.policy_action_level,
        "heat_gain_policy_target_position": cover.heat_gain_target_position,
        "heat_gain_policy_hot_day_override_active": cover.hot_day_override_active,
        "heat_gain_policy_very_hot_day_override_active": cover.very_hot_day_override_active,
        "heat_gain_policy_active_hot_day_close_position": cover.active_hot_day_close_position,
        "forecast_preemptive_active": cover.forecast_preemptive_active,
        "sunset_valid": cover.sunset_valid,
        "direct_sun_valid": cover.direct_sun_valid,
    }
    return {
        "source": "ha_python",
        "open_position": open_position,
        "closed_position": 100 - open_position,
        "attributes": attrs,
        "annotations": [
            "Ergebnis aus custom_components/solar_shading/calculation.py",
            "JS zeichnet weiter die GUI, Python liefert Policy und Zielposition.",
        ],
    }

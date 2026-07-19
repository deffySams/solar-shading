"""Scenario tests for the combined solar-shading decision path."""

from __future__ import annotations

import datetime as dt
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from custom_components.solar_shading.calculation import (
    AdaptiveVerticalCover,
    NormalCoverState,
)


class FakeLogger:
    """Small logger stub for calculation tests."""

    def debug(self, *_args, **_kwargs):
        """Ignore debug output."""

    def info(self, *_args, **_kwargs):
        """Ignore info output."""

    def error(self, *_args, **_kwargs):
        """Ignore error output."""


class FakeState:
    """Small Home Assistant state stub."""

    def __init__(self, state="sunny", attributes=None):
        self.state = state
        self.attributes = attributes or {}
        self.last_updated = dt.datetime.now(dt.UTC)


class FakeStates:
    """State registry stub."""

    def __init__(self, values=None):
        self.values = values or {}

    def get(self, entity_id):
        return self.values.get(entity_id)


class FakeHass:
    """Home Assistant stub with config and state registry."""

    def __init__(self, states=None):
        self.config = SimpleNamespace(time_zone="Europe/Berlin")
        self.states = FakeStates(states)


class FakeSunData:
    """Sun data stub that keeps tests in daytime."""

    def __init__(self, *_args, **_kwargs):
        pass

    def sunset(self):
        return dt.datetime.now(dt.UTC).replace(tzinfo=None) + dt.timedelta(hours=6)

    def sunrise(self):
        return dt.datetime.now(dt.UTC).replace(tzinfo=None) - dt.timedelta(hours=6)


class FakeNightSunData:
    """Sun data stub that keeps tests in nighttime."""

    def sunset(self):
        return dt.datetime.now(dt.UTC).replace(tzinfo=None) - dt.timedelta(hours=1)

    def sunrise(self):
        return dt.datetime.now(dt.UTC).replace(tzinfo=None) + dt.timedelta(hours=6)


def make_cover(**overrides):
    """Create a vertical cover with defaults aimed at direct east-window sun."""
    values = {
        "hass": FakeHass(),
        "logger": FakeLogger(),
        "sol_azi": 15,
        "sol_elev": 30,
        "sunset_pos": 100,
        "sunset_off": 0,
        "sunrise_off": 0,
        "timezone": "Europe/Berlin",
        "fov_left": 90,
        "fov_right": 90,
        "win_azi": 90,
        "h_def": 100,
        "max_pos": 100,
        "min_pos": 0,
        "max_pos_bool": False,
        "min_pos_bool": False,
        "blind_spot_left": None,
        "blind_spot_right": None,
        "blind_spot_elevation": None,
        "blind_spot_on": False,
        "min_elevation": 0,
        "max_elevation": 90,
        "horizon_profile": None,
        "window_width": 1.6,
        "reveal_left_depth": 0.0,
        "reveal_right_depth": 0.0,
        "reveal_top_depth": 0.0,
        "glass_type": "double_clear",
        "weather_entity": None,
        "forecast_summary": {
            "today_max_temp": 30.0,
            "tomorrow_max_temp": None,
        },
        "solar_radiation_summary": {
            "current_direct_normal_irradiance": 810.0,
            "today_max_direct_normal_irradiance": 850.0,
        },
        "use_open_data_solar_radiation": True,
        "solar_radiation_entity": None,
        "solar_radiation_reference": 900.0,
        "heat_power_limit_enabled": False,
        "heat_protection_min_outside_temp": 14.0,
        "room_temperature_entity": None,
        "room_heat_protection_threshold": 24.0,
        "max_transmitted_solar_power_w_m2": 250.0,
        "use_forecast_max_temp_today": True,
        "use_forecast_max_temp_tomorrow": False,
        "forecast_hot_day_threshold": 26.0,
        "forecast_very_hot_day_threshold": 30.0,
        "forecast_preemptive_start_time": "00:00:00",
        "forecast_influence_strength": 0.5,
        "enable_heat_gain_policy": True,
        "policy_preset": "balanced",
        "has_additional_daylight_windows": False,
        "enable_away_mode": False,
        "away_entity": None,
        "away_score_multiplier": 1.25,
        "away_threshold_reduction": 0.1,
        "away_position_offset": 10,
        "show_expert_weights": False,
        "weight_direct_exposure": 1.0,
        "weight_incidence": 1.0,
        "weight_glazing": 1.0,
        "weight_forecast_temperature": 1.0,
        "weight_solar_radiation": 1.0,
        "partial_close_threshold": 0.35,
        "full_close_threshold": 0.65,
        "partial_close_position": 70,
        "full_close_position": 30,
        "distance": 0.5,
        "h_win": 2.1,
    }
    values.update(overrides)
    return AdaptiveVerticalCover(**values)


class CalculationMatrixTests(unittest.TestCase):
    """Validate important combined behaviours across features."""

    def setUp(self):
        self.sun_patch = patch(
            "custom_components.solar_shading.calculation.SunData", FakeSunData
        )
        self.sun_patch.start()
        self.addCleanup(self.sun_patch.stop)

    def test_cold_forecast_blocks_heat_protection_even_with_direct_sun(self):
        """Below hot threshold, heat protection must not shade direct sun."""
        cover = make_cover(
            forecast_summary={
                "today_max_temp": 20.0,
            }
        )

        self.assertFalse(cover.heat_protection_temperature_allowed)
        self.assertEqual(cover.forecast_adjusted_gain_factor, 0.0)
        self.assertEqual(cover.policy_score, 0.0)
        self.assertEqual(NormalCoverState(cover).get_state(), 100)

    def test_very_hot_is_stricter_than_hot_for_same_sun(self):
        """Very-hot threshold should create a visibly stricter target."""
        hot = make_cover(
            forecast_summary={
                "today_max_temp": 26.0,
            }
        )
        very_hot = make_cover(
            forecast_summary={
                "today_max_temp": 30.0,
            }
        )

        self.assertGreater(very_hot.forecast_gain_uplift_factor, hot.forecast_gain_uplift_factor)
        self.assertGreater(very_hot.policy_score, hot.policy_score)
        self.assertLess(
            very_hot.effective_partial_close_threshold,
            hot.effective_partial_close_threshold,
        )
        self.assertLess(
            very_hot.effective_partial_close_position,
            hot.effective_partial_close_position,
        )
        self.assertLess(
            NormalCoverState(very_hot).get_state(),
            NormalCoverState(hot).get_state(),
        )

    def test_forecast_start_time_stops_very_hot_boosts(self):
        """Before forecast start, very-hot should not add extra pressure."""
        cover = make_cover(forecast_preemptive_start_time="23:59:59")

        self.assertFalse(cover.forecast_preemptive_active)
        self.assertEqual(cover.forecast_risk_factor, 0.0)
        self.assertEqual(cover.forecast_temperature_gain_boost, 0.0)
        self.assertEqual(cover.forecast_temperature_policy_pressure, 0.0)
        self.assertEqual(cover.forecast_gain_uplift_factor, 0.0)

    def test_missing_solar_radiation_does_not_invent_heat_from_weather(self):
        """Missing irradiance must not fall back to cloud or rain proxies."""
        cover = make_cover(
            use_open_data_solar_radiation=False,
            solar_radiation_summary=None,
            weather_entity="weather.test",
            hass=FakeHass({"weather.test": FakeState("sunny")}),
        )

        self.assertEqual(cover.incoming_solar_radiation_factor, 0.0)
        self.assertEqual(cover.effective_solar_gain_factor, 0.0)
        self.assertIsNone(cover.transmitted_solar_power_w_m2)
        self.assertEqual(NormalCoverState(cover).get_state(), 100)

    def test_open_data_solar_radiation_scales_physical_gain(self):
        """Open-data radiation should directly scale the physical solar gain."""
        low_radiation = make_cover(
            use_open_data_solar_radiation=True,
            solar_radiation_summary={
                "current_direct_normal_irradiance": 90.0,
                "today_max_direct_normal_irradiance": 180.0,
            },
        )
        high_radiation = make_cover(
            use_open_data_solar_radiation=True,
            solar_radiation_summary={
                "current_direct_normal_irradiance": 810.0,
                "today_max_direct_normal_irradiance": 850.0,
            },
        )

        self.assertAlmostEqual(low_radiation.solar_radiation_factor, 0.1)
        self.assertAlmostEqual(high_radiation.solar_radiation_factor, 0.9)
        self.assertGreater(
            high_radiation.effective_solar_gain_factor,
            low_radiation.effective_solar_gain_factor,
        )
        self.assertGreater(
            high_radiation.forecast_solar_radiation_risk,
            low_radiation.forecast_solar_radiation_risk,
        )

    def test_solar_radiation_reference_can_soften_moderate_values(self):
        """Higher full-scale reference should reduce the radiation factor."""
        normal_reference = make_cover(
            use_open_data_solar_radiation=True,
            solar_radiation_summary={"current_direct_normal_irradiance": 300.0},
            solar_radiation_reference=900.0,
        )
        high_reference = make_cover(
            use_open_data_solar_radiation=True,
            solar_radiation_summary={"current_direct_normal_irradiance": 300.0},
            solar_radiation_reference=1500.0,
        )

        self.assertGreater(
            normal_reference.solar_radiation_factor,
            high_reference.solar_radiation_factor,
        )
        self.assertAlmostEqual(high_reference.solar_radiation_factor, 0.2)

    def test_transmitted_solar_power_limit_can_cap_position(self):
        """Transmitted solar power should translate into a max open position."""
        cover = make_cover(
            enable_heat_gain_policy=False,
            use_open_data_solar_radiation=True,
            solar_radiation_summary={"current_direct_normal_irradiance": 900.0},
            heat_power_limit_enabled=True,
            max_transmitted_solar_power_w_m2=50.0,
        )

        self.assertIsNotNone(cover.transmitted_solar_power_w)
        self.assertGreater(cover.transmitted_solar_power_w_m2, 50.0)
        self.assertTrue(cover.heat_power_limit_active)
        self.assertIsNotNone(cover.heat_power_limited_open_position)
        self.assertEqual(
            NormalCoverState(cover).get_state(),
            cover.heat_power_limited_open_position,
        )

    def test_heat_power_limit_uses_hot_forecast_even_on_cool_morning(self):
        """Hot-day forecast should allow watt-limit closing before outside heats up."""
        cover = make_cover(
            enable_heat_gain_policy=False,
            use_open_data_solar_radiation=True,
            solar_radiation_summary={"current_direct_normal_irradiance": 900.0},
            forecast_summary={
                "today_max_temp": 30.0,
            },
            heat_power_limit_enabled=True,
            max_transmitted_solar_power_w_m2=50.0,
        )

        self.assertTrue(cover.heat_power_limit_active)
        self.assertEqual(cover.heat_power_limit_trigger, "very_hot_forecast")
        self.assertIsNotNone(cover.heat_power_limited_open_position)
        self.assertEqual(
            NormalCoverState(cover).get_state(),
            cover.heat_power_limited_open_position,
        )

    def test_heat_power_limit_stays_inactive_below_temperature_and_hot_thresholds(self):
        """Cold day and cool forecast should prevent watt-limit closing."""
        cover = make_cover(
            enable_heat_gain_policy=False,
            use_open_data_solar_radiation=True,
            solar_radiation_summary={"current_direct_normal_irradiance": 900.0},
            forecast_summary={
                "today_max_temp": 15.0,
            },
            heat_power_limit_enabled=True,
            max_transmitted_solar_power_w_m2=50.0,
        )

        self.assertFalse(cover.heat_power_limit_active)
        self.assertEqual(cover.heat_power_limit_trigger, "inactive")
        self.assertIsNone(cover.heat_power_limited_open_position)
        self.assertEqual(NormalCoverState(cover).get_state(), 100)

    def test_very_cold_current_temperature_blocks_forecast_heat_protection(self):
        """A hot forecast must not force heat protection while it is very cold now."""
        hass = FakeHass({"weather.test": FakeState("sunny", {"temperature": -5.0})})
        cover = make_cover(
            hass=hass,
            weather_entity="weather.test",
            use_open_data_solar_radiation=True,
            solar_radiation_summary={"current_direct_normal_irradiance": 900.0},
            forecast_summary={
                "today_max_temp": 35.0,
            },
            heat_power_limit_enabled=True,
            heat_protection_min_outside_temp=10.0,
            max_transmitted_solar_power_w_m2=50.0,
        )

        self.assertFalse(cover.heat_protection_current_temperature_allowed)
        self.assertFalse(cover.heat_protection_temperature_allowed)
        self.assertFalse(cover.heat_power_limit_active)
        self.assertEqual(cover.heat_power_limit_trigger, "cold_lockout")
        self.assertEqual(cover.policy_score, 0.0)
        self.assertEqual(NormalCoverState(cover).get_state(), 100)

    def test_cold_lockout_threshold_is_configurable(self):
        """Lowering the cold lockout threshold should allow preemptive heat protection."""
        hass = FakeHass({"weather.test": FakeState("sunny", {"temperature": -5.0})})
        cover = make_cover(
            hass=hass,
            weather_entity="weather.test",
            heat_protection_min_outside_temp=-10.0,
        )

        self.assertTrue(cover.heat_protection_current_temperature_allowed)
        self.assertTrue(cover.heat_protection_temperature_allowed)

    def test_horizon_and_extreme_reveals_can_remove_direct_sun(self):
        """Blocked horizon or full reveal shadow should collapse solar gain."""
        blocked_horizon = make_cover(
            horizon_profile='[{"angle": 0, "lower_elevation": 45, "upper_elevation": 90}, {"angle": 180, "lower_elevation": 45, "upper_elevation": 90}]'
        )
        full_reveal = make_cover(reveal_left_depth=100.0)

        self.assertFalse(blocked_horizon.sun_within_horizon_profile)
        self.assertEqual(blocked_horizon.direct_solar_exposure_factor, 0.0)
        self.assertEqual(blocked_horizon.policy_score, 0.0)

        self.assertEqual(full_reveal.left_reveal_shadow, 1.0)
        self.assertEqual(full_reveal.direct_solar_exposure_factor, 0.0)
        self.assertEqual(full_reveal.policy_score, 0.0)

    def test_temperature_activation_does_not_shade_without_direct_sun(self):
        """An active heat gate must not shade once sun leaves the window."""
        no_direct_sun = make_cover(
            sol_azi=270,
            forecast_very_hot_day_threshold=35.0,
        )

        self.assertFalse(no_direct_sun.direct_sun_valid)
        self.assertTrue(no_direct_sun.forecast_hot_day_active)
        self.assertEqual(NormalCoverState(no_direct_sun).get_state(), 100)

        night = make_cover(
            sol_azi=270,
            sunset_pos=75,
            forecast_very_hot_day_threshold=35.0,
        )
        night.sun_data = FakeNightSunData()
        self.assertTrue(night.sunset_valid)
        self.assertEqual(NormalCoverState(night).get_state(), 75)

    def test_hot_room_activates_heat_protection_on_cool_forecast(self):
        """A hot room should react even when the daily forecast misses the heat."""
        hass = FakeHass({"sensor.room": FakeState("25.0")})
        cover = make_cover(
            hass=hass,
            room_temperature_entity="sensor.room",
            room_heat_protection_threshold=24.0,
            forecast_summary={"today_max_temp": 20.0},
            heat_power_limit_enabled=True,
            max_transmitted_solar_power_w_m2=50.0,
        )

        self.assertTrue(cover.room_temperature_heat_active)
        self.assertTrue(cover.heat_protection_activation_active)
        self.assertEqual(cover.heat_protection_activation_reason, "room_temperature")
        self.assertEqual(cover.heat_power_limit_trigger, "room_temperature")
        self.assertLess(NormalCoverState(cover).get_state(), 100)

    def test_room_below_threshold_keeps_cool_day_inactive(self):
        """Below both activation thresholds, direct sun alone does not close."""
        hass = FakeHass({"sensor.room": FakeState("23.5")})
        cover = make_cover(
            hass=hass,
            room_temperature_entity="sensor.room",
            room_heat_protection_threshold=24.0,
            forecast_summary={"today_max_temp": 20.0},
        )

        self.assertFalse(cover.room_temperature_heat_active)
        self.assertFalse(cover.heat_protection_activation_active)
        self.assertEqual(cover.heat_protection_activation_reason, "inactive")
        self.assertEqual(NormalCoverState(cover).get_state(), 100)

    def test_tomorrow_hot_does_not_activate_today_by_itself(self):
        """Tomorrow's maximum must not be treated as today's activation gate."""
        cover = make_cover(
            use_forecast_max_temp_tomorrow=True,
            forecast_summary={
                "today_max_temp": 20.0,
                "tomorrow_max_temp": 35.0,
            },
        )

        self.assertFalse(cover.forecast_hot_day_active)
        self.assertFalse(cover.heat_protection_activation_active)
        self.assertEqual(NormalCoverState(cover).get_state(), 100)

    def test_away_mode_is_stricter_than_home_for_same_conditions(self):
        """Away mode should close more for the same solar and forecast inputs."""
        home = make_cover()
        away = make_cover(
            hass=FakeHass({"person.test": FakeState("not_home")}),
            enable_away_mode=True,
            away_entity="person.test",
            away_score_multiplier=1.5,
            away_threshold_reduction=0.1,
            away_position_offset=10,
        )

        self.assertFalse(home.away_mode_active)
        self.assertTrue(away.away_mode_active)
        self.assertGreater(away.policy_score, home.policy_score)
        self.assertLess(
            away.effective_partial_close_threshold,
            home.effective_partial_close_threshold,
        )
        self.assertLessEqual(
            NormalCoverState(away).get_state(),
            NormalCoverState(home).get_state(),
        )
        self.assertEqual(
            NormalCoverState(away).get_state(),
            away.effective_full_close_position,
        )


if __name__ == "__main__":
    unittest.main()

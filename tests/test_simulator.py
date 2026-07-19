"""Tests for the browser simulator backend bridge."""

import unittest
from types import SimpleNamespace

from custom_components.solar_shading.simulator import (
    SolarShadingSimulationView,
    simulate_from_payload,
)


class _States:
    def get(self, _entity_id):
        return None


class _Hass:
    def __init__(self):
        self.config = SimpleNamespace(
            time_zone="Europe/Berlin",
            latitude=48.1372,
            longitude=11.5756,
            elevation=520,
        )
        self.data = {}
        self.states = _States()


def _payload(**overrides):
    values = {
        "year": 2026,
        "month": 6,
        "day": 21,
        "time": "13:00",
        "windowAzimuth": 90,
        "defaultPosition": 100,
        "sunsetPosition": 100,
        "nightMode": "time",
        "nightStartTime": "22:00",
        "nightEndTime": "06:00",
        "fovLeft": 90,
        "fovRight": 90,
        "minElevation": 0,
        "maxElevation": 90,
        "windowHeight": 2.1,
        "windowWidth": 1.2,
        "distance": 0.5,
        "glassType": "double_clear",
        "horizonProfile": "[]",
        "horizonMode": "window",
        "solarRadiation": 800,
        "solarReference": 900,
        "outsideTemp": 28,
        "roomTemperature": 22,
        "roomHeatProtectionThreshold": 24,
        "forecastTodayMax": 30,
        "forecastTomorrowMax": 30,
        "forecastSolarMax": 900,
        "hotDayThreshold": 24,
        "veryHotThreshold": 29,
        "forecastInfluence": 0.5,
        "preemptiveStart": "00:00",
        "useTodayMax": True,
        "useTomorrowMax": False,
        "useOpenDataSolarRadiation": True,
        "enableHeatGainPolicy": True,
        "heatProtectionControlMode": "scaling",
        "binaryCloseThreshold": 180,
        "binaryClosePosition": 20,
        "policyPreset": "balanced",
        "additionalWindows": False,
        "awayActive": False,
        "heatPowerLimitEnabled": False,
        "heatProtectionMinOutsideTemp": 14,
        "maxTransmittedSolarPower": 250,
        "showExpertWeights": False,
        "weightDirect": 1,
        "weightIncidence": 1,
        "weightGlazing": 1,
        "weightSolarRadiation": 1,
        "weightForecastTemp": 1,
        "partialThreshold": 0.35,
        "fullThreshold": 0.65,
        "partialPosition": 55,
        "fullPosition": 15,
    }
    values.update(overrides)
    return {"values": values, "sun": {"azimuth": 90, "elevation": 40}}


class SimulatorBackendTest(unittest.TestCase):
    def test_simulator_endpoint_is_public_for_local_page(self):
        self.assertFalse(SolarShadingSimulationView.requires_auth)

    def test_simulator_uses_python_policy(self):
        result = simulate_from_payload(_Hass(), _payload())

        self.assertEqual(result["source"], "ha_python")
        self.assertLess(result["open_position"], 100)
        self.assertTrue(
            result["attributes"]["heat_protection_activation_active"]
        )
        self.assertEqual(
            result["attributes"]["heat_protection_activation_reason"],
            "forecast_hot",
        )
        attributes = result["attributes"]
        self.assertAlmostEqual(
            attributes["solar_power_with_target_cover_w_per_window"],
            attributes["solar_power_without_cover_w_per_window"]
            * result["open_position"]
            / 100,
            places=2,
        )

    def test_simulator_opens_without_direct_sun(self):
        result = simulate_from_payload(
            _Hass(),
            _payload(solarRadiation=800) | {"sun": {"azimuth": 270, "elevation": 40}},
        )

        self.assertEqual(result["open_position"], 100)
        self.assertFalse(result["attributes"]["direct_sun_valid"])

    def test_binary_control_uses_transmitted_solar_power_threshold(self):
        result = simulate_from_payload(
            _Hass(),
            _payload(
                heatProtectionControlMode="binary",
                binaryCloseThreshold=100,
                binaryClosePosition=22,
            ),
        )

        self.assertEqual(result["open_position"], 22)
        self.assertTrue(result["attributes"]["binary_heat_protection_active"])
        self.assertEqual(result["attributes"]["decision_reason"], "binary_solar_threshold")

    def test_binary_control_stays_open_below_threshold(self):
        result = simulate_from_payload(
            _Hass(),
            _payload(
                heatProtectionControlMode="binary",
                binaryCloseThreshold=1000,
                binaryClosePosition=22,
            ),
        )

        self.assertEqual(result["open_position"], 100)
        self.assertFalse(result["attributes"]["binary_heat_protection_active"])

    def test_fixed_night_time_overrides_daylight_calculation(self):
        result = simulate_from_payload(
            _Hass(),
            _payload(
                time="23:00",
                nightMode="time",
                nightStartTime="22:00",
                nightEndTime="06:00",
                sunsetPosition=35,
            ),
        )

        self.assertEqual(result["open_position"], 35)
        self.assertTrue(result["attributes"]["sunset_valid"])
        self.assertEqual(result["attributes"]["decision_reason"], "night_position")

    def test_compass_horizon_uses_true_solar_azimuth(self):
        result = simulate_from_payload(
            _Hass(),
            _payload(
                horizonMode="compass",
                horizonProfile=(
                    '[{"angle":0,"lower_elevation":50},'
                    '{"angle":180,"lower_elevation":50},'
                    '{"angle":359,"lower_elevation":50}]'
                ),
            ),
        )

        self.assertFalse(result["attributes"]["sun_within_horizon_profile"])
        self.assertEqual(result["attributes"]["horizon_mode"], "compass")
        self.assertTrue(result["attributes"]["decision_trace"])

    def test_room_temperature_can_activate_cool_forecast(self):
        result = simulate_from_payload(
            _Hass(),
            _payload(
                forecastTodayMax=20,
                roomTemperature=25,
                roomHeatProtectionThreshold=24,
                heatPowerLimitEnabled=True,
                maxTransmittedSolarPower=200,
            ),
        )

        self.assertTrue(result["attributes"]["room_temperature_heat_active"])
        self.assertEqual(
            result["attributes"]["heat_protection_activation_reason"],
            "room_temperature",
        )
        self.assertLess(result["open_position"], 100)


if __name__ == "__main__":
    unittest.main()

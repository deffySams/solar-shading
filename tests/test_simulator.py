"""Tests for the browser simulator backend bridge."""

from types import SimpleNamespace
import unittest

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
        "fovLeft": 90,
        "fovRight": 90,
        "minElevation": 0,
        "maxElevation": 90,
        "windowHeight": 2.1,
        "windowWidth": 1.2,
        "distance": 0.5,
        "glassType": "double_clear",
        "horizonProfile": "[]",
        "solarRadiation": 800,
        "solarReference": 900,
        "outsideTemp": 28,
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
        "policyPreset": "balanced",
        "additionalWindows": False,
        "awayActive": False,
        "hotDayCloseEnabled": True,
        "hotDayCloseThreshold": 24,
        "hotDayClosePosition": 30,
        "veryHotDayClosePosition": 15,
        "heatPowerLimitEnabled": False,
        "heatPowerTempThreshold": 24,
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
        self.assertEqual(result["open_position"], 15)
        self.assertEqual(
            result["attributes"]["heat_gain_policy_action_level"],
            "veryhotday",
        )

    def test_simulator_opens_without_direct_sun(self):
        result = simulate_from_payload(
            _Hass(),
            _payload(solarRadiation=800) | {"sun": {"azimuth": 270, "elevation": 40}},
        )

        self.assertEqual(result["open_position"], 100)
        self.assertFalse(result["attributes"]["direct_sun_valid"])


if __name__ == "__main__":
    unittest.main()

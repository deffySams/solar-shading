"""Broad plausibility matrix for the production simulator backend."""

from __future__ import annotations

import unittest

from custom_components.solar_shading.simulator import simulate_from_payload

from test_simulator import _Hass, _payload


def _simulate(*, azimuth: int = 180, **values):
    payload = _payload(windowAzimuth=azimuth, **values)
    payload["sun"] = {"azimuth": azimuth, "elevation": 40}
    return simulate_from_payload(_Hass(), payload)


class SimulatorPlausibilityMatrixTests(unittest.TestCase):
    def test_outputs_stay_bounded_across_main_operating_matrix(self):
        for azimuth in (0, 90, 180, 270):
            for forecast in (20, 26, 30, 35):
                for room_temperature in (20, 24, 27):
                    for radiation in (0, 150, 450, 900):
                        with self.subTest(
                            azimuth=azimuth,
                            forecast=forecast,
                            room_temperature=room_temperature,
                            radiation=radiation,
                        ):
                            result = _simulate(
                                azimuth=azimuth,
                                forecastTodayMax=forecast,
                                roomTemperature=room_temperature,
                                solarRadiation=radiation,
                            )
                            self.assertGreaterEqual(result["open_position"], 0)
                            self.assertLessEqual(result["open_position"], 100)
                            self.assertEqual(
                                result["open_position"] + result["closed_position"],
                                100,
                            )

    def test_more_radiation_never_opens_the_cover_further(self):
        for azimuth in (0, 90, 180, 270):
            positions = [
                _simulate(
                    azimuth=azimuth,
                    forecastTodayMax=30,
                    roomTemperature=25,
                    solarRadiation=radiation,
                    heatPowerLimitEnabled=True,
                    maxTransmittedSolarPower=80,
                )["open_position"]
                for radiation in (0, 150, 450, 900)
            ]
            self.assertEqual(positions, sorted(positions, reverse=True))

    def test_very_hot_forecast_is_never_weaker_than_hot_forecast(self):
        for azimuth in (0, 90, 180, 270):
            hot = _simulate(
                azimuth=azimuth,
                forecastTodayMax=26,
                roomTemperature=20,
                solarRadiation=800,
            )
            very_hot = _simulate(
                azimuth=azimuth,
                forecastTodayMax=32,
                roomTemperature=20,
                solarRadiation=800,
            )
            self.assertLessEqual(very_hot["open_position"], hot["open_position"])

    def test_cold_lockout_wins_over_forecast_and_room_temperature(self):
        result = _simulate(
            outsideTemp=5,
            heatProtectionMinOutsideTemp=14,
            forecastTodayMax=35,
            roomTemperature=28,
            solarRadiation=900,
            heatPowerLimitEnabled=True,
            maxTransmittedSolarPower=50,
        )

        self.assertEqual(result["open_position"], 100)
        self.assertFalse(
            result["attributes"]["heat_protection_activation_active"]
        )
        self.assertEqual(
            result["attributes"]["heat_protection_activation_reason"],
            "cold_lockout",
        )

    def test_binary_mode_changes_only_at_physical_watt_threshold(self):
        below = _simulate(
            heatProtectionControlMode="binary",
            binaryCloseThreshold=1000,
            binaryClosePosition=18,
            forecastTodayMax=30,
            solarRadiation=800,
        )
        above = _simulate(
            heatProtectionControlMode="binary",
            binaryCloseThreshold=20,
            binaryClosePosition=18,
            forecastTodayMax=30,
            solarRadiation=800,
        )

        self.assertEqual(below["open_position"], 100)
        self.assertEqual(above["open_position"], 18)


if __name__ == "__main__":
    unittest.main()

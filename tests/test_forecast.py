"""Unit tests for forecast helper logic."""

from __future__ import annotations

import importlib
import unittest


FORECAST = importlib.import_module("custom_components.solar_shading.forecast")


class ForecastTests(unittest.TestCase):
    """Test forecast extraction and policy helpers."""

    def test_extract_daily_forecast_summary_reads_today_and_tomorrow(self) -> None:
        summary = FORECAST.extract_daily_forecast_summary(
            [
                {
                    "condition": "partlycloudy",
                    "temperature": 25,
                    "precipitation_probability": 40,
                    "precipitation": 1.2,
                    "uv_index": 6.0,
                },
                {"condition": "sunny", "temperature": 28},
            ]
        )

        self.assertEqual(summary["today_max_temp"], 25)
        self.assertEqual(summary["tomorrow_max_temp"], 28)
        self.assertEqual(summary["today_cloud_coverage"], 50.0)

    def test_temperature_risk_interpolates_between_thresholds(self) -> None:
        risk = FORECAST.temperature_risk(28, 26, 30)
        self.assertAlmostEqual(risk, 0.5)

    def test_precipitation_probability_damping_uses_percent(self) -> None:
        damping = FORECAST.precipitation_probability_damping(70)
        self.assertAlmostEqual(damping, 0.3)

    def test_precipitation_amount_damping_uses_amount(self) -> None:
        damping = FORECAST.precipitation_amount_damping(5)
        self.assertAlmostEqual(damping, 0.5)

    def test_uv_risk_caps_at_one(self) -> None:
        self.assertEqual(FORECAST.uv_risk(12), 1.0)


if __name__ == "__main__":
    unittest.main()

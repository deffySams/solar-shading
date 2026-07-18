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
                    "temperature": 25,
                },
                {"temperature": 28},
            ]
        )

        self.assertEqual(summary["today_max_temp"], 25)
        self.assertEqual(summary["tomorrow_max_temp"], 28)

    def test_temperature_risk_interpolates_between_thresholds(self) -> None:
        risk = FORECAST.temperature_risk(28, 26, 30)
        self.assertAlmostEqual(risk, 0.5)

if __name__ == "__main__":
    unittest.main()

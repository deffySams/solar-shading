"""Unit tests for weather attenuation helpers."""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import unittest


MODULE_PATH = (
    pathlib.Path(__file__).resolve().parents[1]
    / "custom_components"
    / "solar_shading"
    / "weather.py"
)

SPEC = importlib.util.spec_from_file_location("solar_shading_weather", MODULE_PATH)
WEATHER = importlib.util.module_from_spec(SPEC)
assert SPEC is not None and SPEC.loader is not None
sys.modules[SPEC.name] = WEATHER
SPEC.loader.exec_module(WEATHER)


class WeatherTests(unittest.TestCase):
    """Test cloud and rain attenuation helpers."""

    def test_reported_cloud_coverage_is_used_directly(self) -> None:
        self.assertEqual(WEATHER.normalized_cloud_coverage(80, "sunny"), 80.0)

    def test_cloud_coverage_falls_back_to_condition_mapping(self) -> None:
        self.assertEqual(WEATHER.normalized_cloud_coverage(None, "cloudy"), 90.0)

    def test_cloud_factor_uses_percentage(self) -> None:
        self.assertAlmostEqual(
            WEATHER.cloud_attenuation_factor(75, "partlycloudy"), 0.25
        )

    def test_rain_factor_damps_precipitating_conditions(self) -> None:
        self.assertAlmostEqual(
            WEATHER.rain_attenuation_factor("rainy", None), 0.1
        )

    def test_weather_factor_combines_clouds_and_rain(self) -> None:
        self.assertAlmostEqual(
            WEATHER.weather_attenuation_factor(80, "rainy", 0.5), 0.02
        )


if __name__ == "__main__":
    unittest.main()

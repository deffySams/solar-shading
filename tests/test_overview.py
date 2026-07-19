"""Tests for window status and read-only overview calculations."""

import unittest
from types import SimpleNamespace

from custom_components.solar_shading.const import CONF_HEIGHT_WIN, CONF_WINDOW_WIDTH
from custom_components.solar_shading.overview import (
    build_window_snapshot,
    configuration_warnings,
    derive_window_status,
    estimate_power_with_cover,
)


class OverviewTests(unittest.TestCase):
    def test_linear_cover_power_is_explicit_and_clamped(self):
        self.assertEqual(estimate_power_with_cover(800, 0), 0)
        self.assertEqual(estimate_power_with_cover(800, 25), 200)
        self.assertEqual(estimate_power_with_cover(800, 100), 800)
        self.assertEqual(estimate_power_with_cover(800, 120), 800)
        self.assertIsNone(estimate_power_with_cover(None, 50))

    def test_configuration_status_has_priority(self):
        status = derive_window_status(
            target_position=20,
            decision_reason="transmitted_solar_power_limit",
            activation_reason="room_temperature",
            direct_sun_valid=True,
            control_enabled=True,
            manual_override=False,
            cover_available=True,
            configuration_warnings=["missing_house_profile"],
            full_close_position=30,
        )
        self.assertEqual(status, "configuration_incomplete")

    def test_power_limit_status_is_distinct(self):
        status = derive_window_status(
            target_position=42,
            decision_reason="transmitted_solar_power_limit",
            activation_reason="forecast_hot",
            direct_sun_valid=True,
            control_enabled=True,
            manual_override=False,
            cover_available=True,
            configuration_warnings=[],
            full_close_position=30,
        )
        self.assertEqual(status, "power_limited")

    def test_warnings_report_partial_cover_availability(self):
        warnings = configuration_warnings(
            {
                "house_profile_entry_id": "house-1",
                "floor_name": "floor-1",
                "room_name": "living",
                "facade_name": "east",
                "room_temperature_entity": "sensor.room",
                "horizon_profile": [[0, 0]],
                CONF_HEIGHT_WIN: 1.5,
                CONF_WINDOW_WIDTH: 1.2,
            },
            entities=["cover.a", "cover.b"],
            current_positions={"cover.a": 40, "cover.b": None},
            solar_radiation_value=500,
        )
        self.assertEqual(warnings, ["some_covers_unavailable"])

    def test_snapshot_exposes_cover_and_power_details(self):
        entry = SimpleNamespace(
            entry_id="entry-1",
            title="Fallback",
            data={"name": "Living East", "sensor_type": "cover_blind"},
        )
        coordinator = SimpleNamespace(
            data=SimpleNamespace(
                states={"state": 30, "window_status": "partial_shading"},
                attributes={
                    "current_cover_positions": {"cover.a": 20, "cover.b": 40},
                    "current_cover_position_average": 30,
                    "solar_power_without_cover_w_total": 1000,
                    "solar_power_with_target_cover_w_total": 300,
                    "solar_power_with_actual_cover_w_total": 300,
                    "configuration_warnings": [],
                },
            )
        )

        snapshot = build_window_snapshot(entry, coordinator)

        self.assertEqual(snapshot["name"], "Living East")
        self.assertEqual(snapshot["actual_open_position"], 30)
        self.assertEqual(len(snapshot["covers"]), 2)
        self.assertEqual(snapshot["solar_power_with_actual_cover_w_total"], 300)


if __name__ == "__main__":
    unittest.main()

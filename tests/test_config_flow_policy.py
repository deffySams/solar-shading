import unittest
from types import SimpleNamespace
from unittest.mock import patch

from custom_components.solar_shading.config_flow import (
    _area_options_for_floor,
    _migrate_retired_options,
    _validate_policy_input,
)
from custom_components.solar_shading.migration import RETIRED_OPTION_KEYS
from custom_components.solar_shading.const import (
    CONF_BINARY_CLOSE_POSITION,
    CONF_BINARY_CLOSE_THRESHOLD,
    CONF_PARTIAL_CLOSE_THRESHOLD,
    CONF_FULL_CLOSE_THRESHOLD,
    CONF_PARTIAL_CLOSE_POSITION,
    CONF_FULL_CLOSE_POSITION,
    CONF_MAX_TRANSMITTED_SOLAR_POWER,
    CONF_HEAT_PROTECTION_CONTROL_MODE,
    CONF_FORECAST_HOT_DAY_THRESHOLD,
    CONF_ROOM_HEAT_PROTECTION_THRESHOLD,
    CONF_ROOM_TEMPERATURE_ENTITY,
)

class ConfigFlowPolicyValidationTests(unittest.TestCase):
    def test_retired_options_are_removed_and_power_limit_is_renamed(self):
        migrated = _migrate_retired_options(
            {
                "weather_state": ["sunny"],
                "lux_entity": "sensor.lux",
                "weight_weather": 1.0,
                "heat_power_max_watts": 225,
            }
        )

        self.assertEqual(migrated[CONF_MAX_TRANSMITTED_SOLAR_POWER], 225)
        self.assertNotIn("weather_state", migrated)
        self.assertNotIn("lux_entity", migrated)
        self.assertNotIn("weight_weather", migrated)
        self.assertNotIn("heat_power_max_watts", migrated)

    def test_transparent_cover_migrates_to_binary_control(self):
        migrated = _migrate_retired_options(
            {
                "transparent_blind": True,
                "irradiance_threshold": 240,
            }
        )

        self.assertEqual(migrated[CONF_HEAT_PROTECTION_CONTROL_MODE], "binary")
        self.assertEqual(migrated[CONF_BINARY_CLOSE_THRESHOLD], 240)
        self.assertEqual(migrated[CONF_BINARY_CLOSE_POSITION], 0)
        self.assertNotIn("transparent_blind", migrated)

    def test_climate_mode_values_migrate_to_common_temperature_gate(self):
        migrated = _migrate_retired_options(
            {
                "climate_mode": True,
                "temp_entity": "sensor.living_room_temperature",
                "temp_low": 20,
                "temp_high": 24.5,
                "hot_day_close_enabled": True,
                "hot_day_close_threshold": 27.0,
                "hot_day_close_position": 30,
                "very_hot_day_close_position": 15,
                "heat_power_outside_temp_threshold": 23,
            }
        )

        self.assertEqual(
            migrated[CONF_ROOM_TEMPERATURE_ENTITY],
            "sensor.living_room_temperature",
        )
        self.assertEqual(migrated[CONF_ROOM_HEAT_PROTECTION_THRESHOLD], 24.5)
        self.assertEqual(migrated[CONF_FORECAST_HOT_DAY_THRESHOLD], 27.0)
        for retired in (
            "climate_mode",
            "temp_entity",
            "temp_low",
            "temp_high",
            "hot_day_close_enabled",
            "hot_day_close_threshold",
            "hot_day_close_position",
            "very_hot_day_close_position",
            "heat_power_outside_temp_threshold",
        ):
            self.assertNotIn(retired, migrated)

    def test_nested_house_profile_overrides_are_migrated(self):
        migrated = _migrate_retired_options(
            {
                "house_defaults": {"temp_high": 23.5},
                "room_profiles": {
                    "bedroom": {
                        "profile_overrides": {
                            "temp_entity": "sensor.bedroom_temperature",
                            "hot_day_close_enabled": True,
                        }
                    }
                },
            }
        )

        self.assertEqual(
            migrated["house_defaults"][CONF_ROOM_HEAT_PROTECTION_THRESHOLD],
            23.5,
        )
        room_overrides = migrated["room_profiles"]["bedroom"]["profile_overrides"]
        self.assertEqual(
            room_overrides[CONF_ROOM_TEMPERATURE_ENTITY],
            "sensor.bedroom_temperature",
        )
        self.assertTrue(RETIRED_OPTION_KEYS.isdisjoint(room_overrides))

    def test_legacy_closed_notation_is_accepted(self):
        errors = _validate_policy_input({
            CONF_PARTIAL_CLOSE_THRESHOLD: 0.35,
            CONF_FULL_CLOSE_THRESHOLD: 0.83,
            CONF_PARTIAL_CLOSE_POSITION: 65,
            CONF_FULL_CLOSE_POSITION: 100,
        })
        self.assertNotIn(CONF_FULL_CLOSE_POSITION, errors)

    def test_position_order_is_normalized_by_policy_layer(self):
        errors = _validate_policy_input({
            CONF_PARTIAL_CLOSE_THRESHOLD: 0.35,
            CONF_FULL_CLOSE_THRESHOLD: 0.83,
            CONF_PARTIAL_CLOSE_POSITION: 30,
            CONF_FULL_CLOSE_POSITION: 60,
        })
        self.assertNotIn(CONF_FULL_CLOSE_POSITION, errors)

class FloorRoomSelectionTests(unittest.TestCase):
    @patch("custom_components.solar_shading.config_flow.area_registry.async_get")
    def test_only_rooms_from_selected_floor_are_offered(self, async_get):
        registry = async_get.return_value
        registry.async_list_areas.return_value = [
            SimpleNamespace(id="office", name="Office", floor_id="ground"),
            SimpleNamespace(id="bedroom", name="Bedroom", floor_id="upper"),
            SimpleNamespace(id="living", name="Living room", floor_id="ground"),
            SimpleNamespace(id="outside", name="Outside", floor_id=None),
        ]

        options = _area_options_for_floor(SimpleNamespace(), "ground")

        self.assertEqual(
            options,
            [
                {"value": "living", "label": "Living room"},
                {"value": "office", "label": "Office"},
            ],
        )

    @patch("custom_components.solar_shading.config_flow.area_registry.async_get")
    def test_no_floor_returns_no_room_options(self, async_get):
        self.assertEqual(_area_options_for_floor(SimpleNamespace(), None), [])
        async_get.assert_not_called()


if __name__ == "__main__":
    unittest.main()

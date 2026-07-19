"""Tests for recursive legacy-setting migration."""

import unittest

from custom_components.solar_shading.const import (
    CONF_BINARY_CLOSE_POSITION,
    CONF_BINARY_CLOSE_THRESHOLD,
    CONF_FORECAST_HOT_DAY_THRESHOLD,
    CONF_HEAT_PROTECTION_CONTROL_MODE,
    CONF_MAX_TRANSMITTED_SOLAR_POWER,
    CONF_ROOM_HEAT_PROTECTION_THRESHOLD,
    CONF_ROOM_TEMPERATURE_ENTITY,
)
from custom_components.solar_shading.migration import (
    RETIRED_OPTION_KEYS,
    migrate_retired_options,
)


class MigrationTests(unittest.TestCase):
    """Verify useful values survive while retired controls disappear."""

    def test_climate_and_hot_day_values_move_to_common_gate(self):
        migrated = migrate_retired_options(
            {
                "climate_mode": True,
                "temp_entity": "sensor.living_room_temperature",
                "temp_high": 24.5,
                "hot_day_close_threshold": 27.0,
                "heat_power_outside_temp_threshold": 23,
            }
        )

        self.assertEqual(
            migrated[CONF_ROOM_TEMPERATURE_ENTITY],
            "sensor.living_room_temperature",
        )
        self.assertEqual(migrated[CONF_ROOM_HEAT_PROTECTION_THRESHOLD], 24.5)
        self.assertEqual(migrated[CONF_FORECAST_HOT_DAY_THRESHOLD], 27.0)
        self.assertTrue(RETIRED_OPTION_KEYS.isdisjoint(migrated))

    def test_transparent_cover_moves_to_binary_control(self):
        migrated = migrate_retired_options(
            {"transparent_blind": True, "irradiance_threshold": 240}
        )

        self.assertEqual(migrated[CONF_HEAT_PROTECTION_CONTROL_MODE], "binary")
        self.assertEqual(migrated[CONF_BINARY_CLOSE_THRESHOLD], 240)
        self.assertEqual(migrated[CONF_BINARY_CLOSE_POSITION], 0)

    def test_nested_profiles_and_power_limit_are_migrated(self):
        migrated = migrate_retired_options(
            {
                "house_defaults": {
                    "temp_high": 23.5,
                    "heat_power_max_watts": 225,
                },
                "room_profiles": {
                    "bedroom": {
                        "profile_overrides": {
                            "temp_entity": "sensor.bedroom_temperature"
                        }
                    }
                },
            }
        )

        defaults = migrated["house_defaults"]
        self.assertEqual(defaults[CONF_ROOM_HEAT_PROTECTION_THRESHOLD], 23.5)
        self.assertEqual(defaults[CONF_MAX_TRANSMITTED_SOLAR_POWER], 225)
        overrides = migrated["room_profiles"]["bedroom"]["profile_overrides"]
        self.assertEqual(
            overrides[CONF_ROOM_TEMPERATURE_ENTITY],
            "sensor.bedroom_temperature",
        )


if __name__ == "__main__":
    unittest.main()

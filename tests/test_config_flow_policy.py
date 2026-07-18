import unittest
from custom_components.solar_shading.config_flow import (
    _migrate_retired_options,
    _validate_policy_input,
)
from custom_components.solar_shading.const import (
    CONF_BINARY_CLOSE_POSITION,
    CONF_BINARY_CLOSE_THRESHOLD,
    CONF_PARTIAL_CLOSE_THRESHOLD,
    CONF_FULL_CLOSE_THRESHOLD,
    CONF_PARTIAL_CLOSE_POSITION,
    CONF_FULL_CLOSE_POSITION,
    CONF_MAX_TRANSMITTED_SOLAR_POWER,
    CONF_HEAT_PROTECTION_CONTROL_MODE,
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

if __name__ == "__main__":
    unittest.main()

import unittest
from custom_components.solar_shading.config_flow import _validate_policy_input
from custom_components.solar_shading.const import (
    CONF_PARTIAL_CLOSE_THRESHOLD,
    CONF_FULL_CLOSE_THRESHOLD,
    CONF_PARTIAL_CLOSE_POSITION,
    CONF_FULL_CLOSE_POSITION,
)

class ConfigFlowPolicyValidationTests(unittest.TestCase):
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

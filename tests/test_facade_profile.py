import unittest

from custom_components.solar_shading.config_flow import _apply_facade_azimuth
from custom_components.solar_shading.const import (
    CONF_AZIMUTH,
    CONF_FACADE_OFFSET,
    CONF_FACADE_REFERENCE_AZIMUTH,
    CONF_USE_FACADE_AZIMUTH,
)


class FacadeProfileTests(unittest.TestCase):
    def test_facade_azimuth_derives_window_azimuth(self):
        data = {
            CONF_USE_FACADE_AZIMUTH: True,
            CONF_FACADE_REFERENCE_AZIMUTH: 12,
            CONF_FACADE_OFFSET: 90,
            CONF_AZIMUTH: 180,
        }

        _apply_facade_azimuth(data)

        self.assertEqual(data[CONF_AZIMUTH], 102)

    def test_facade_azimuth_wraps_around_compass(self):
        data = {
            CONF_USE_FACADE_AZIMUTH: True,
            CONF_FACADE_REFERENCE_AZIMUTH: 282,
            CONF_FACADE_OFFSET: 180,
            CONF_AZIMUTH: 180,
        }

        _apply_facade_azimuth(data)

        self.assertEqual(data[CONF_AZIMUTH], 102)

    def test_manual_azimuth_is_kept_when_facade_mode_is_disabled(self):
        data = {
            CONF_USE_FACADE_AZIMUTH: False,
            CONF_FACADE_REFERENCE_AZIMUTH: 12,
            CONF_FACADE_OFFSET: 90,
            CONF_AZIMUTH: 180,
        }

        _apply_facade_azimuth(data)

        self.assertEqual(data[CONF_AZIMUTH], 180)


if __name__ == "__main__":
    unittest.main()

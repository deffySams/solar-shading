"""Tests for house-profile inheritance."""

import unittest

from custom_components.solar_shading.const import (
    CONF_AZIMUTH,
    CONF_ENTITIES,
    CONF_FACADE_NAME,
    CONF_FACADE_OFFSET,
    CONF_FACADE_PROFILES,
    CONF_FLOOR_NAME,
    CONF_FLOOR_PROFILES,
    CONF_GLASS_TYPE,
    CONF_HORIZON_PROFILE,
    CONF_HOUSE_DEFAULTS,
    CONF_HOUSE_PROFILE_ENTRY_ID,
    CONF_HOUSE_REFERENCE_AZIMUTH,
    CONF_POLICY_PRESET,
    CONF_PROFILE_OVERRIDES,
    CONF_REVEAL_LEFT,
    CONF_ROOM_FACADE_PROFILES,
    CONF_ROOM_HEAT_PROTECTION_THRESHOLD,
    CONF_ROOM_NAME,
    CONF_ROOM_PROFILES,
    CONF_ROOM_TEMPERATURE_ENTITY,
    CONF_USE_LOCAL_GEOMETRY,
    CONF_USE_LOCAL_HORIZON,
    CONF_USE_LOCAL_POLICY,
    CONF_WINDOW_OVERRIDES,
    CONF_WINDOW_WIDTH,
)
from custom_components.solar_shading.profiles import (
    apply_bulk_profile_assignment,
    resolve_profile_options,
    room_facade_key,
)


class ProfileResolutionTests(unittest.TestCase):
    def test_bulk_assignment_keeps_physical_window_details(self):
        original = {
            CONF_ENTITIES: ["cover.a", "cover.b"],
            CONF_WINDOW_WIDTH: 1.4,
            CONF_ROOM_TEMPERATURE_ENTITY: "sensor.local_temperature",
            CONF_USE_LOCAL_GEOMETRY: True,
            CONF_USE_LOCAL_HORIZON: True,
            CONF_USE_LOCAL_POLICY: True,
            CONF_WINDOW_OVERRIDES: {CONF_GLASS_TYPE: "single_clear"},
        }

        result = apply_bulk_profile_assignment(
            original,
            house_profile_entry_id="house-1",
            floor_id="floor-1",
            room_id="living",
            facade_name="east",
            facade_offset=2,
        )

        self.assertEqual(result[CONF_ENTITIES], ["cover.a", "cover.b"])
        self.assertEqual(result[CONF_WINDOW_WIDTH], 1.4)
        self.assertEqual(result[CONF_HOUSE_PROFILE_ENTRY_ID], "house-1")
        self.assertEqual(result[CONF_FLOOR_NAME], "floor-1")
        self.assertEqual(result[CONF_ROOM_NAME], "living")
        self.assertEqual(result[CONF_FACADE_NAME], "east")
        self.assertEqual(result[CONF_FACADE_OFFSET], 2)
        self.assertFalse(result[CONF_USE_LOCAL_GEOMETRY])
        self.assertFalse(result[CONF_USE_LOCAL_HORIZON])
        self.assertFalse(result[CONF_USE_LOCAL_POLICY])
        self.assertEqual(result[CONF_WINDOW_OVERRIDES], {})
        self.assertNotIn(CONF_ROOM_TEMPERATURE_ENTITY, result)

    def test_resolves_all_layers_in_order(self):
        house = {
            CONF_HOUSE_REFERENCE_AZIMUTH: 12,
            CONF_HOUSE_DEFAULTS: {
                CONF_GLASS_TYPE: "double_clear",
                CONF_POLICY_PRESET: "balanced",
                CONF_REVEAL_LEFT: 0.1,
            },
            CONF_FLOOR_PROFILES: {
                "floor-1": {CONF_PROFILE_OVERRIDES: {CONF_REVEAL_LEFT: 0.12}}
            },
            CONF_FACADE_PROFILES: {
                "east": {
                    CONF_FACADE_OFFSET: 90,
                    CONF_PROFILE_OVERRIDES: {CONF_REVEAL_LEFT: 0.15},
                }
            },
            CONF_ROOM_PROFILES: {
                "bedroom": {
                    CONF_FLOOR_NAME: "floor-1",
                    CONF_FACADE_NAME: "east",
                    CONF_PROFILE_OVERRIDES: {CONF_POLICY_PRESET: "cooling_first"},
                }
            },
            CONF_ROOM_FACADE_PROFILES: {
                room_facade_key("bedroom", "east"): {
                    CONF_PROFILE_OVERRIDES: {CONF_REVEAL_LEFT: 0.2}
                }
            },
        }
        window = {
            CONF_HOUSE_PROFILE_ENTRY_ID: "house-1",
            CONF_ROOM_NAME: "bedroom",
            CONF_WINDOW_OVERRIDES: {CONF_GLASS_TYPE: "triple_low_e"},
        }

        result = resolve_profile_options(window, house)

        self.assertEqual(result.options[CONF_FLOOR_NAME], "floor-1")
        self.assertEqual(result.options[CONF_FACADE_NAME], "east")
        self.assertEqual(result.options[CONF_AZIMUTH], 102)
        self.assertEqual(result.options[CONF_REVEAL_LEFT], 0.2)
        self.assertEqual(result.options[CONF_POLICY_PRESET], "cooling_first")
        self.assertEqual(result.options[CONF_GLASS_TYPE], "triple_low_e")

    def test_window_horizon_only_overrides_when_enabled(self):
        house = {CONF_HOUSE_DEFAULTS: {CONF_HORIZON_PROFILE: "house"}}
        inherited = resolve_profile_options(
            {CONF_HORIZON_PROFILE: "window"}, house
        )
        local = resolve_profile_options(
            {
                CONF_HORIZON_PROFILE: "window",
                CONF_USE_LOCAL_HORIZON: True,
            },
            house,
        )

        self.assertEqual(inherited.options[CONF_HORIZON_PROFILE], "house")
        self.assertEqual(local.options[CONF_HORIZON_PROFILE], "window")

    def test_unlinked_window_keeps_legacy_flat_options(self):
        window = {CONF_AZIMUTH: 181, CONF_GLASS_TYPE: "single_clear"}

        result = resolve_profile_options(window, None)

        self.assertEqual(result.options, window)
        self.assertEqual(result.layers, ("window",))

    def test_room_temperature_sensor_is_inherited_by_every_room_window(self):
        house = {
            CONF_HOUSE_DEFAULTS: {CONF_ROOM_HEAT_PROTECTION_THRESHOLD: 24.0},
            CONF_ROOM_PROFILES: {
                "living": {
                    CONF_PROFILE_OVERRIDES: {
                        CONF_ROOM_TEMPERATURE_ENTITY: "sensor.living_temperature"
                    }
                }
            },
        }

        result = resolve_profile_options(
            {CONF_ROOM_NAME: "living"},
            house,
        )

        self.assertEqual(
            result.options[CONF_ROOM_TEMPERATURE_ENTITY],
            "sensor.living_temperature",
        )
        self.assertEqual(result.options[CONF_ROOM_HEAT_PROTECTION_THRESHOLD], 24.0)

    def test_legacy_climate_threshold_is_available_before_options_are_saved(self):
        result = resolve_profile_options(
            {
                "temp_entity": "sensor.legacy_room",
                "temp_high": 25,
            },
            None,
        )

        self.assertEqual(
            result.options[CONF_ROOM_TEMPERATURE_ENTITY], "sensor.legacy_room"
        )
        self.assertEqual(result.options[CONF_ROOM_HEAT_PROTECTION_THRESHOLD], 25)


if __name__ == "__main__":
    unittest.main()

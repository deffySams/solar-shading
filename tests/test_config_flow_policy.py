import unittest
from types import SimpleNamespace
from unittest.mock import patch

from custom_components.solar_shading.config_flow import (
    HOUSE_DEFAULT_OPTIONS,
    HOUSE_EXPERT_OPTIONS,
    HOUSE_FORM_SECTIONS,
    HOUSE_HEAT_KEYS,
    HOUSE_NIGHT_KEYS,
    HOUSE_SETUP_KEYS,
    LINKED_WINDOW_OPTIONS,
    OptionsFlowHandler,
    _area_options_for_floor,
    _facade_options,
    _floor_options,
    _flatten_section_values,
    _linked_detail_schema,
    _linked_initial_schema,
    _migrate_retired_options,
    _nest_section_values,
    _schema_subset,
    _sectioned_schema,
    _validate_policy_input,
)
from custom_components.solar_shading.migration import RETIRED_OPTION_KEYS
from custom_components.solar_shading.const import (
    CONF_BULK_FACADE_ROTATION,
    CONF_BULK_OVERRIDE_ROOM_FACADE_GEOMETRY,
    CONF_BULK_RESET_LOCAL_OVERRIDES,
    CONF_BULK_ROOM_FACADE_POLICY_PRESET,
    CONF_BULK_ROOM_POLICY_PRESET,
    CONF_COVER_LOCATION,
    CONF_ENTRY_TYPE,
    CONF_FACADE_NAME,
    CONF_FACADE_OFFSET,
    CONF_FACADE_PROFILES,
    CONF_FOV_LEFT,
    CONF_FOV_RIGHT,
    CONF_HAS_ADDITIONAL_DAYLIGHT_WINDOWS,
    CONF_HORIZON_MODE,
    CONF_HORIZON_PROFILE,
    CONF_HOUSE_DEFAULTS,
    CONF_HOUSE_PROFILE_ENTRY_ID,
    CONF_HOUSE_REFERENCE_AZIMUTH,
    CONF_HEAT_POWER_LIMIT_ENABLED,
    CONF_NIGHT_MORNING_ACTION_ENABLED,
    CONF_DEFAULT_HEIGHT,
    CONF_SHOW_EXPERT_WEIGHTS,
    CONF_WEIGHT_DIRECT_EXPOSURE,
    CONF_USE_LOCAL_HORIZON,
    CONF_POLICY_PRESET,
    CONF_PROFILE_OVERRIDES,
    CONF_REVEAL_LEFT,
    CONF_REVEAL_RIGHT,
    CONF_REVEAL_TOP,
    CONF_ROOM_FACADE_PROFILES,
    CONF_ROOM_NAME,
    CONF_ROOM_PROFILES,
    ENTRY_TYPE_WINDOW,
    ENTRY_TYPE_HOUSE,
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
    SensorType,
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
        errors = _validate_policy_input(
            {
                CONF_PARTIAL_CLOSE_THRESHOLD: 0.35,
                CONF_FULL_CLOSE_THRESHOLD: 0.83,
                CONF_PARTIAL_CLOSE_POSITION: 65,
                CONF_FULL_CLOSE_POSITION: 100,
            }
        )
        self.assertNotIn(CONF_FULL_CLOSE_POSITION, errors)

    def test_position_order_is_normalized_by_policy_layer(self):
        errors = _validate_policy_input(
            {
                CONF_PARTIAL_CLOSE_THRESHOLD: 0.35,
                CONF_FULL_CLOSE_THRESHOLD: 0.83,
                CONF_PARTIAL_CLOSE_POSITION: 30,
                CONF_FULL_CLOSE_POSITION: 60,
            }
        )
        self.assertNotIn(CONF_FULL_CLOSE_POSITION, errors)


class FloorRoomSelectionTests(unittest.TestCase):
    def test_facade_dropdown_shows_effective_compass_azimuth(self):
        options = _facade_options(
            {
                CONF_HOUSE_REFERENCE_AZIMUTH: 234,
                CONF_FACADE_PROFILES: {
                    "South": {CONF_FACADE_OFFSET: 0},
                    "West": {CONF_FACADE_OFFSET: 90},
                },
            }
        )

        self.assertEqual(
            options,
            [
                {"value": "South", "label": "South (234 deg)"},
                {"value": "West", "label": "West (324 deg)"},
            ],
        )

    @patch("custom_components.solar_shading.config_flow.floor_registry.async_get")
    def test_home_assistant_floors_are_explicit_dropdown_options(self, async_get):
        registry = async_get.return_value
        registry.async_list_floors.return_value = [
            SimpleNamespace(floor_id="og", name="Obergeschoss"),
            SimpleNamespace(floor_id="eg", name="Erdgeschoss"),
        ]

        options = _floor_options(SimpleNamespace())

        self.assertEqual(
            options,
            [
                {"value": "eg", "label": "Erdgeschoss"},
                {"value": "og", "label": "Obergeschoss"},
            ],
        )

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


class HouseJourneySchemaTests(unittest.IsolatedAsyncioTestCase):
    def test_house_default_pages_are_complete_and_non_overlapping(self):
        all_keys = {
            getattr(marker, "schema", marker) for marker in HOUSE_DEFAULT_OPTIONS.schema
        }

        self.assertEqual(
            HOUSE_SETUP_KEYS | HOUSE_NIGHT_KEYS | HOUSE_HEAT_KEYS,
            all_keys,
        )
        self.assertFalse(HOUSE_SETUP_KEYS & HOUSE_NIGHT_KEYS)
        self.assertFalse(HOUSE_SETUP_KEYS & HOUSE_HEAT_KEYS)
        self.assertFalse(HOUSE_NIGHT_KEYS & HOUSE_HEAT_KEYS)
        self.assertLess(len(HOUSE_SETUP_KEYS), len(all_keys))
        self.assertLess(len(HOUSE_NIGHT_KEYS), len(all_keys))
        self.assertLess(len(HOUSE_HEAT_KEYS), len(all_keys))

        ordered_keys = [
            getattr(marker, "schema", marker)
            for marker in HOUSE_DEFAULT_OPTIONS.schema
            if getattr(marker, "schema", marker) in HOUSE_SETUP_KEYS
        ]
        self.assertLess(
            ordered_keys.index(CONF_HORIZON_MODE),
            ordered_keys.index(CONF_HORIZON_PROFILE),
        )

    def test_checkbox_dependencies_are_native_second_tier_sections(self):
        fake_section = lambda schema, _options: schema
        with patch(
            "custom_components.solar_shading.config_flow.flow_section", fake_section
        ):
            night_schema = _sectioned_schema(
                _schema_subset(HOUSE_DEFAULT_OPTIONS, HOUSE_NIGHT_KEYS),
                HOUSE_FORM_SECTIONS["house_night"],
            )
            expert_schema = _sectioned_schema(
                HOUSE_EXPERT_OPTIONS, HOUSE_FORM_SECTIONS["house_expert"]
            )

        night_keys = [
            getattr(marker, "schema", marker) for marker in night_schema.schema
        ]
        expert_keys = [
            getattr(marker, "schema", marker) for marker in expert_schema.schema
        ]
        self.assertEqual(
            night_keys[night_keys.index(CONF_NIGHT_MORNING_ACTION_ENABLED) + 1],
            "morning_action_settings",
        )
        self.assertNotIn(CONF_DEFAULT_HEIGHT, night_keys)
        self.assertEqual(
            expert_keys[expert_keys.index(CONF_SHOW_EXPERT_WEIGHTS) + 1],
            "expert_weight_settings",
        )
        self.assertNotIn(CONF_WEIGHT_DIRECT_EXPOSURE, expert_keys)

    def test_section_values_round_trip_without_changing_stored_keys(self):
        groups = HOUSE_FORM_SECTIONS["house_heat"]
        flat = {
            CONF_HEAT_POWER_LIMIT_ENABLED: True,
            CONF_MAX_TRANSMITTED_SOLAR_POWER: 225,
        }
        with patch(
            "custom_components.solar_shading.config_flow.flow_section", object()
        ):
            nested = _nest_section_values(flat, groups)

        self.assertEqual(
            nested["power_limit_settings"][CONF_MAX_TRANSMITTED_SOLAR_POWER], 225
        )
        self.assertEqual(_flatten_section_values(nested, groups), flat)

    def test_linked_window_editor_always_exposes_local_horizon(self):
        fake_section = lambda schema, _options: schema
        with patch(
            "custom_components.solar_shading.config_flow.flow_section", fake_section
        ):
            schema = _linked_detail_schema(LINKED_WINDOW_OPTIONS, {})

        keys = [getattr(marker, "schema", marker) for marker in schema.schema]
        self.assertEqual(
            keys[keys.index(CONF_USE_LOCAL_HORIZON) + 1],
            "local_horizon_settings",
        )
        horizon_schema = next(
            validator
            for marker, validator in schema.schema.items()
            if getattr(marker, "schema", marker) == "local_horizon_settings"
        )
        horizon_keys = [
            getattr(marker, "schema", marker) for marker in horizon_schema.schema
        ]
        self.assertEqual(horizon_keys, [CONF_HORIZON_MODE, CONF_HORIZON_PROFILE])

    def test_linked_window_creation_also_exposes_local_horizon(self):
        fake_section = lambda schema, _options: schema
        with patch(
            "custom_components.solar_shading.config_flow.flow_section", fake_section
        ):
            schema = _linked_initial_schema(LINKED_WINDOW_OPTIONS)

        keys = [getattr(marker, "schema", marker) for marker in schema.schema]
        self.assertEqual(
            keys[keys.index(CONF_USE_LOCAL_HORIZON) + 1],
            "local_horizon_settings",
        )

    async def test_linked_window_horizon_submission_is_saved_flat(self):
        flow = OptionsFlowHandler.__new__(OptionsFlowHandler)
        flow.options = {
            CONF_HOUSE_PROFILE_ENTRY_ID: "house",
            CONF_USE_LOCAL_HORIZON: False,
        }
        flow.sensor_type = SensorType.BLIND
        flow.optional_entities = OptionsFlowHandler.optional_entities.__get__(flow)
        flow.async_create_entry = lambda **kwargs: kwargs

        horizon = '[{"angle": 90, "lower_elevation": 12}]'
        result = await flow.async_step_vertical(
            {
                CONF_USE_LOCAL_HORIZON: True,
                "local_horizon_settings": {
                    CONF_HORIZON_MODE: "compass",
                    CONF_HORIZON_PROFILE: horizon,
                },
            }
        )

        self.assertTrue(result["data"][CONF_USE_LOCAL_HORIZON])
        self.assertEqual(result["data"][CONF_HORIZON_MODE], "compass")
        self.assertEqual(result["data"][CONF_HORIZON_PROFILE], horizon)
        self.assertNotIn("local_horizon_settings", result["data"])

    async def test_empty_bulk_assignment_does_not_block_house_menu(self):
        flow = OptionsFlowHandler.__new__(OptionsFlowHandler)
        flow.entry_type = ENTRY_TYPE_HOUSE
        flow.hass = SimpleNamespace(
            config_entries=SimpleNamespace(async_entries=lambda _domain: [])
        )
        flow.async_show_menu = lambda **kwargs: kwargs

        result = await flow.async_step_init()

        self.assertNotIn("house_bulk_assignment", result["menu_options"])
        self.assertIn("house_floors", result["menu_options"])
        self.assertIn("house_rooms", result["menu_options"])
        self.assertIn("house_room_facades", result["menu_options"])


class BulkAssignmentJourneyTests(unittest.IsolatedAsyncioTestCase):
    def _flow(self):
        flow = OptionsFlowHandler.__new__(OptionsFlowHandler)
        flow._house_entry_id = "house"
        flow._selected_floor_id = "upper"
        flow._bulk_window_entry_ids = ["window"]
        flow._bulk_assignment_values = {
            CONF_ROOM_NAME: "bedroom",
            CONF_FACADE_NAME: "east",
        }
        flow.options = {
            CONF_HOUSE_DEFAULTS: {
                CONF_COVER_LOCATION: "exterior",
                CONF_HORIZON_MODE: "compass",
                CONF_FOV_LEFT: 90,
                CONF_FOV_RIGHT: 90,
                CONF_REVEAL_LEFT: 0,
                CONF_REVEAL_RIGHT: 0,
                CONF_REVEAL_TOP: 0,
            },
            CONF_FACADE_PROFILES: {
                "east": {
                    CONF_FACADE_OFFSET: 92,
                    CONF_PROFILE_OVERRIDES: {CONF_FOV_LEFT: 80},
                }
            },
            CONF_ROOM_PROFILES: {
                "bedroom": {CONF_PROFILE_OVERRIDES: {CONF_POLICY_PRESET: "balanced"}}
            },
            CONF_ROOM_FACADE_PROFILES: {
                "bedroom::east": {
                    CONF_PROFILE_OVERRIDES: {
                        CONF_POLICY_PRESET: "cooling_first",
                        CONF_HORIZON_MODE: "compass",
                        CONF_HORIZON_PROFILE: '[{"angle": 90}]',
                    }
                }
            },
        }
        window = SimpleNamespace(
            data={CONF_ENTRY_TYPE: ENTRY_TYPE_WINDOW},
            options={CONF_FACADE_OFFSET: 4},
        )
        config_entries = SimpleNamespace(
            async_get_entry=lambda entry_id: window if entry_id == "window" else None,
            async_update_entry=lambda entry, **kwargs: setattr(
                entry, "options", kwargs["options"]
            ),
        )
        flow.hass = SimpleNamespace(config_entries=config_entries)
        flow.add_suggested_values_to_schema = lambda schema, values: (schema, values)
        flow.async_show_form = lambda **kwargs: kwargs
        return flow

    async def test_existing_values_are_prefilled(self):
        result = await self._flow().async_step_house_bulk_assignment_settings()
        suggested = result["data_schema"][1]

        self.assertEqual(suggested[CONF_BULK_FACADE_ROTATION], 92)
        self.assertEqual(suggested[CONF_FACADE_OFFSET], 4)
        self.assertEqual(suggested[CONF_BULK_ROOM_POLICY_PRESET], "balanced")
        self.assertEqual(
            suggested[CONF_BULK_ROOM_FACADE_POLICY_PRESET], "cooling_first"
        )
        self.assertTrue(suggested[CONF_BULK_OVERRIDE_ROOM_FACADE_GEOMETRY])

    async def test_inherit_removes_wall_override_without_resetting_facade(self):
        flow = self._flow()

        async def finish():
            return {"type": "done"}

        flow._update_options = finish
        result = await flow.async_step_house_bulk_assignment_settings(
            {
                CONF_BULK_FACADE_ROTATION: 92,
                CONF_FACADE_OFFSET: 4,
                CONF_HAS_ADDITIONAL_DAYLIGHT_WINDOWS: False,
                CONF_BULK_ROOM_POLICY_PRESET: "__inherit__",
                CONF_BULK_ROOM_FACADE_POLICY_PRESET: "__inherit__",
                CONF_BULK_OVERRIDE_ROOM_FACADE_GEOMETRY: False,
                CONF_HORIZON_MODE: "compass",
                CONF_REVEAL_LEFT: 0,
                CONF_REVEAL_RIGHT: 0,
                CONF_REVEAL_TOP: 0,
                CONF_FOV_LEFT: 80,
                CONF_FOV_RIGHT: 90,
                CONF_BULK_RESET_LOCAL_OVERRIDES: True,
            }
        )

        self.assertEqual(result, {"type": "done"})
        self.assertEqual(
            flow.options[CONF_FACADE_PROFILES]["east"][CONF_FACADE_OFFSET], 92
        )
        self.assertNotIn(
            CONF_POLICY_PRESET,
            flow.options[CONF_ROOM_PROFILES]["bedroom"][CONF_PROFILE_OVERRIDES],
        )
        self.assertNotIn("bedroom::east", flow.options[CONF_ROOM_FACADE_PROFILES])


if __name__ == "__main__":
    unittest.main()

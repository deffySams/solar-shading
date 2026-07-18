"""Unit tests for the standalone geometry helpers."""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import unittest


MODULE_PATH = (
    pathlib.Path(__file__).resolve().parents[1]
    / "custom_components"
    / "solar_shading"
    / "geometry.py"
)

SPEC = importlib.util.spec_from_file_location("solar_shading_geometry", MODULE_PATH)
GEOMETRY = importlib.util.module_from_spec(SPEC)
assert SPEC is not None and SPEC.loader is not None
sys.modules[SPEC.name] = GEOMETRY
SPEC.loader.exec_module(GEOMETRY)


class HorizonProfileTests(unittest.TestCase):
    """Test horizon profile parsing and interpolation."""

    def test_parse_horizon_profile_sorts_points(self) -> None:
        profile = GEOMETRY.parse_horizon_profile(
            [
                {"angle": 180, "lower_elevation": 20, "upper_elevation": 90},
                {"angle": 0, "lower_elevation": 10, "upper_elevation": 80},
            ]
        )

        self.assertEqual(profile[0].angle, 0)
        self.assertEqual(profile[1].angle, 180)

    def test_interpolate_horizon_elevations_between_points(self) -> None:
        profile = GEOMETRY.parse_horizon_profile(
            [
                {"angle": 0, "lower_elevation": 10, "upper_elevation": 90},
                {"angle": 180, "lower_elevation": 30, "upper_elevation": 50},
            ]
        )

        lower, upper = GEOMETRY.interpolate_horizon_elevations(90, profile)

        self.assertAlmostEqual(lower, 20.0)
        self.assertAlmostEqual(upper, 70.0)

    def test_interpolate_horizon_defaults_without_profile(self) -> None:
        lower, upper = GEOMETRY.interpolate_horizon_elevations(42, [])

        self.assertEqual(lower, 0.0)
        self.assertEqual(upper, 90.0)

    def test_local_window_angle_maps_gamma_to_zero_to_one_eighty(self) -> None:
        self.assertEqual(GEOMETRY.local_window_angle(90), 0.0)
        self.assertEqual(GEOMETRY.local_window_angle(0), 90.0)
        self.assertEqual(GEOMETRY.local_window_angle(-90), 180.0)

    def test_compass_horizon_interpolates_across_north(self) -> None:
        profile = GEOMETRY.parse_horizon_profile(
            [
                {"angle": 350, "lower_elevation": 20},
                {"angle": 10, "lower_elevation": 40},
            ]
        )

        lower, upper = GEOMETRY.interpolate_compass_horizon_elevations(
            0, profile
        )

        self.assertAlmostEqual(lower, 30.0)
        self.assertEqual(upper, 90.0)


class RevealShadowTests(unittest.TestCase):
    """Test reveal shading helpers."""

    def test_left_reveal_shadow_only_when_sun_comes_from_left(self) -> None:
        left = GEOMETRY.left_reveal_shadow_fraction(30, 2.0, 0.2)
        right = GEOMETRY.left_reveal_shadow_fraction(-30, 2.0, 0.2)

        self.assertGreater(left, 0.0)
        self.assertEqual(right, 0.0)

    def test_right_reveal_shadow_only_when_sun_comes_from_right(self) -> None:
        right = GEOMETRY.right_reveal_shadow_fraction(-30, 2.0, 0.2)
        left = GEOMETRY.right_reveal_shadow_fraction(30, 2.0, 0.2)

        self.assertGreater(right, 0.0)
        self.assertEqual(left, 0.0)

    def test_top_reveal_shadow_grows_with_elevation(self) -> None:
        low = GEOMETRY.top_reveal_shadow_fraction(10, 2.0, 0.1)
        high = GEOMETRY.top_reveal_shadow_fraction(40, 2.0, 0.1)

        self.assertGreater(high, low)

    def test_combined_reveal_shadow_fraction_handles_overlap(self) -> None:
        combined = GEOMETRY.combined_reveal_shadow_fraction(0.5, 0.5)

        self.assertAlmostEqual(combined, 0.75)

    def test_reveal_shadow_is_clamped(self) -> None:
        side = GEOMETRY.left_reveal_shadow_fraction(89, 0.5, 5.0)
        top = GEOMETRY.top_reveal_shadow_fraction(89, 0.5, 5.0)

        self.assertLessEqual(side, 1.0)
        self.assertLessEqual(top, 1.0)


if __name__ == "__main__":
    unittest.main()

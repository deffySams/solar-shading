"""Unit tests for glazing-aware optical helpers."""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import unittest


MODULE_PATH = (
    pathlib.Path(__file__).resolve().parents[1]
    / "custom_components"
    / "solar_shading"
    / "optics.py"
)

SPEC = importlib.util.spec_from_file_location("solar_shading_optics", MODULE_PATH)
OPTICS = importlib.util.module_from_spec(SPEC)
assert SPEC is not None and SPEC.loader is not None
sys.modules[SPEC.name] = OPTICS
SPEC.loader.exec_module(OPTICS)


class OpticsTests(unittest.TestCase):
    """Test glazing presets and angle-dependent optics."""

    def test_triple_clear_profile_exists(self) -> None:
        profile = OPTICS.glass_profile_for_type("triple_clear")

        self.assertAlmostEqual(profile.solar_transmittance, 0.60)
        self.assertAlmostEqual(profile.solar_reflectance_normal, 0.20)

    def test_incidence_angle_is_zero_for_head_on_sun(self) -> None:
        angle = OPTICS.incidence_angle_from_gamma_elevation(0, 0)

        self.assertAlmostEqual(angle, 0.0)

    def test_incidence_angle_grows_for_oblique_sun(self) -> None:
        head_on = OPTICS.incidence_angle_from_gamma_elevation(0, 10)
        oblique = OPTICS.incidence_angle_from_gamma_elevation(45, 10)

        self.assertGreater(oblique, head_on)

    def test_reflectance_rises_towards_grazing_angles(self) -> None:
        profile = OPTICS.glass_profile_for_type("double_low_e")
        low = OPTICS.schlick_reflectance(profile.solar_reflectance_normal, 10)
        high = OPTICS.schlick_reflectance(profile.solar_reflectance_normal, 80)

        self.assertGreater(high, low)

    def test_transmittance_drops_towards_grazing_angles(self) -> None:
        profile = OPTICS.glass_profile_for_type("triple_low_e")
        low = OPTICS.angular_transmittance(
            profile.solar_transmittance,
            profile.solar_reflectance_normal,
            10,
        )
        high = OPTICS.angular_transmittance(
            profile.solar_transmittance,
            profile.solar_reflectance_normal,
            80,
        )

        self.assertLess(high, low)


if __name__ == "__main__":
    unittest.main()

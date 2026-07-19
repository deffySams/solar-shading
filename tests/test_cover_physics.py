"""Tests for location-aware solar cover attenuation."""

import unittest

from custom_components.solar_shading.cover_physics import (
    closed_cover_residual_factor,
    cover_transmission_factor,
    estimate_power_with_cover,
    maximum_open_position_for_limit,
)


class CoverPhysicsTests(unittest.TestCase):
    def test_closed_residual_depends_on_mounting_location(self):
        self.assertEqual(closed_cover_residual_factor("exterior"), 0.10)
        self.assertEqual(closed_cover_residual_factor("interior"), 0.55)

    def test_transmission_interpolates_from_closed_residual_to_open(self):
        self.assertAlmostEqual(cover_transmission_factor(50, "exterior"), 0.55)
        self.assertAlmostEqual(cover_transmission_factor(50, "interior"), 0.775)
        self.assertEqual(cover_transmission_factor(100, "interior"), 1.0)

    def test_power_and_limit_use_same_inverse_model(self):
        target = maximum_open_position_for_limit(800, 440, "exterior")
        self.assertEqual(target, 50)
        self.assertAlmostEqual(estimate_power_with_cover(800, target, "exterior"), 440)

    def test_unattainable_interior_limit_closes_fully(self):
        self.assertEqual(maximum_open_position_for_limit(800, 200, "interior"), 0)
        self.assertAlmostEqual(estimate_power_with_cover(800, 0, "interior"), 440)


if __name__ == "__main__":
    unittest.main()

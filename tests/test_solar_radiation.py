"""Unit tests for open-data solar radiation helpers."""

import unittest

from custom_components.solar_shading.solar_radiation import radiation_factor


class SolarRadiationTests(unittest.TestCase):
    """Test solar radiation normalization."""

    def test_radiation_factor_normalizes_dni(self) -> None:
        """DNI around 900 W/m2 should map to full clear-sky strength."""
        self.assertAlmostEqual(radiation_factor(90), 0.1)
        self.assertEqual(radiation_factor(900), 1.0)
        self.assertEqual(radiation_factor(1200), 1.0)

    def test_missing_radiation_has_no_synthetic_heat(self) -> None:
        self.assertEqual(radiation_factor(None), 0.0)

    def test_radiation_factor_normalizes_shortwave(self) -> None:
        """GHI/shortwave uses a slightly lower reference value."""
        self.assertAlmostEqual(radiation_factor(80, direct_normal=False), 0.1)
        self.assertEqual(radiation_factor(800, direct_normal=False), 1.0)

    def test_radiation_factor_allows_custom_reference(self) -> None:
        """User-selected full-scale reference softens moderate irradiance."""
        self.assertAlmostEqual(radiation_factor(300, reference=1500), 0.2)


if __name__ == "__main__":
    unittest.main()

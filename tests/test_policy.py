"""Tests for daylight-aware heat-gain policy helpers."""

import unittest

from custom_components.solar_shading.policy import (
    adjusted_policy_score,
    adjusted_positions,
    adjusted_thresholds,
    away_adjusted_positions,
    away_adjusted_score,
    away_adjusted_thresholds,
    gain_limited_policy_score,
    legacy_position_input_detected,
    normalize_policy_positions,
    policy_target_position,
    temperature_adjusted_positions,
    temperature_adjusted_thresholds,
    temperature_boost_signal,
    very_hot_policy_pressure,
    weighted_risk_score,
)


class TestPolicyHelpers(unittest.TestCase):
    """Validate weighted risk scoring and preset adjustments."""

    def test_weighted_risk_score_ignores_zero_weight_and_inactive_values(self):
        """Only active weighted factors should contribute to the score."""
        score = weighted_risk_score(
            {
                "direct_exposure": 0.8,
                "weather": 0.6,
                "forecast_uv": None,
            },
            {
                "direct_exposure": 2.0,
                "weather": 1.0,
                "forecast_uv": 3.0,
            },
        )
        self.assertAlmostEqual(score, (0.8 ** (2.0 / 3.0)) * (0.6 ** (1.0 / 3.0)), places=6)

    def test_weighted_risk_score_collapses_when_required_factor_is_zero(self):
        """Multiplicative scoring must not invent heat gain at night or in clouds."""
        score = weighted_risk_score(
            {
                "direct_exposure": 0.0,
                "weather": 1.0,
                "forecast_temperature": 1.0,
            },
            {
                "direct_exposure": 1.0,
                "weather": 1.0,
                "forecast_temperature": 1.0,
            },
        )
        self.assertEqual(score, 0.0)

    def test_gain_limited_policy_score_cannot_exceed_physics(self):
        """Forecast weights must not shade harder than the physical gain allows."""
        self.assertEqual(gain_limited_policy_score(0.38, 0.0), 0.0)
        self.assertAlmostEqual(gain_limited_policy_score(0.8, 0.56), 0.56)
        self.assertAlmostEqual(gain_limited_policy_score(0.3, 0.9), 0.3)

    def test_forecast_temperature_signal_is_neutral_below_hot_day(self):
        """Temperature forecast should boost hot days, not disable normal physics."""
        self.assertEqual(temperature_boost_signal(0.0), 1.0)
        self.assertEqual(temperature_boost_signal(None), 1.0)
        self.assertAlmostEqual(temperature_boost_signal(0.5), 1.5)

    def test_very_hot_pressure_tightens_thresholds_and_positions(self):
        """Very-hot forecast should visibly tighten policy outputs."""
        pressure = very_hot_policy_pressure(1.0, 0.5)
        self.assertEqual(pressure, 1.0)

        partial, full = temperature_adjusted_thresholds(0.35, 0.65, pressure)
        self.assertAlmostEqual(partial, 0.15, places=6)
        self.assertAlmostEqual(full, 0.45, places=6)

        partial_pos, full_pos = temperature_adjusted_positions(70, 30, pressure)
        self.assertEqual(partial_pos, 60)
        self.assertEqual(full_pos, 30)

    def test_additional_daylight_windows_make_policy_more_aggressive(self):
        """Extra daylight sources should lower thresholds and raise the score."""
        base_score = adjusted_policy_score(0.5, "daylight_first_single_aspect", False)
        multi_score = adjusted_policy_score(0.5, "daylight_first_single_aspect", True)
        self.assertGreater(multi_score, base_score)

        base_partial, base_full = adjusted_thresholds(0.35, 0.65, "balanced", False)
        multi_partial, multi_full = adjusted_thresholds(0.35, 0.65, "balanced", True)
        self.assertLess(multi_partial, base_partial)
        self.assertLess(multi_full, base_full)

    def test_adjusted_positions_keep_full_below_partial(self):
        """Preset position offsets must preserve open-position ordering."""
        partial, full = adjusted_positions(
            55, 20, "cooling_first", has_additional_daylight_windows=True
        )
        self.assertLessEqual(full, partial)
        self.assertEqual(partial, 45)
        self.assertEqual(full, 20)

    def test_legacy_position_inputs_are_detected_and_normalized(self):
        """Old closing-percent style positions must be explicit and reversible."""
        self.assertTrue(legacy_position_input_detected(65, 100))
        self.assertEqual(normalize_policy_positions(65, 100), (35, 0))
        self.assertFalse(legacy_position_input_detected(70, 30))
        self.assertEqual(normalize_policy_positions(70, 30), (70, 30))

    def test_strict_open_target_is_hard_floor_for_position_adjustments(self):
        """Preset, away, and very-hot adjustments must not exceed max closing."""
        partial, full = adjusted_positions(70, 30, "cooling_first", False)
        self.assertEqual((partial, full), (65, 30))

        partial, full = away_adjusted_positions(partial, full, True, 50)
        self.assertEqual((partial, full), (30, 30))

        partial, full = temperature_adjusted_positions(35, 30, 1.0)
        self.assertEqual((partial, full), (30, 30))

    def test_policy_target_position_interpolates_between_thresholds(self):
        """The partial band should interpolate smoothly between both targets."""
        level, target = policy_target_position(
            score=0.5,
            partial_threshold=0.4,
            full_threshold=0.8,
            partial_position=70,
            full_position=30,
        )
        self.assertEqual(level, "partial")
        self.assertEqual(target, 60)

    def test_policy_target_position_disables_below_threshold(self):
        """Below the partial threshold the overlay should stay inactive."""
        level, target = policy_target_position(
            score=0.2,
            partial_threshold=0.35,
            full_threshold=0.65,
            partial_position=70,
            full_position=30,
        )
        self.assertEqual(level, "none")
        self.assertIsNone(target)

    def test_away_adjusted_score_and_thresholds_become_stricter(self):
        """Away mode should raise score and lower thresholds."""
        self.assertGreater(
            away_adjusted_score(0.5, True, 1.3),
            away_adjusted_score(0.5, False, 1.3),
        )
        partial, full = away_adjusted_thresholds(0.35, 0.65, True, 0.1)
        self.assertAlmostEqual(partial, 0.25, places=6)
        self.assertAlmostEqual(full, 0.55, places=6)

    def test_away_adjusted_positions_reduce_open_targets(self):
        """Away mode should enforce stricter open-position targets."""
        partial, full = away_adjusted_positions(55, 25, True, 10)
        self.assertEqual(partial, 45)
        self.assertEqual(full, 25)


if __name__ == "__main__":
    unittest.main()

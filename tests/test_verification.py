"""Tests for post-maintenance strainer verification."""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import verification as vf  # noqa: E402

Q = 21.2
TWO_ABS = vf.Instruments()                                  # 0–400 kPa, ±0.1 % span, flow ±0.5 %
DP_CELL = vf.Instruments(vf.DIFFERENTIAL, 25.0, 0.1, 0.5)   # 0–25 kPa DP transmitter


def check(dp, flow=Q, instruments=TWO_ABS, **kw):
    return vf.verify_cleaning(dp, flow, Q, 5.0, 20.0, instruments, **kw)


class UncertaintyTests(unittest.TestCase):
    def test_two_transmitters_combine_root_two(self):
        u_single = 400 * 0.001 / math.sqrt(3)
        self.assertAlmostEqual(vf.dp_uncertainty_kpa(TWO_ABS), math.sqrt(2) * u_single)

    def test_dp_cell_is_much_tighter(self):
        self.assertLess(vf.dp_uncertainty_kpa(DP_CELL), 0.1 * vf.dp_uncertainty_kpa(TWO_ABS))

    def test_low_flow_rejected(self):
        with self.assertRaises(ValueError):
            check(1.0, flow=0.2 * Q)

    def test_non_positive_dp_rejected(self):
        with self.assertRaises(ValueError):
            check(0.0)


class VerdictTests(unittest.TestCase):
    def test_restored_within_band(self):
        result = check(5.1, flow=21.0, dp_star_before_kpa=10.7)
        self.assertEqual(result.verdict, "RESTORED")
        self.assertGreater(result.reduction_pct, 45)

    def test_flow_normalisation_catches_low_flow_reading(self):
        # 4.9 kPa at 70 % flow is 10 kPa at design flow: not clean.
        result = check(4.9, flow=0.7 * Q)
        self.assertAlmostEqual(result.dp_star_kpa, 10.0, places=2)
        self.assertEqual(result.verdict, "IMPROVED, NOT CLEAN")

    def test_suspiciously_low(self):
        self.assertEqual(check(3.5).verdict, "SUSPICIOUSLY LOW")

    def test_not_effective(self):
        self.assertEqual(check(21.0).verdict, "NOT EFFECTIVE")

    def test_precise_instrument_narrows_band(self):
        self.assertEqual(check(5.6, instruments=TWO_ABS).verdict, "RESTORED")
        self.assertEqual(check(5.6, instruments=DP_CELL).verdict, "IMPROVED, NOT CLEAN")

    def test_repeatability_widens_band(self):
        self.assertEqual(check(5.6, instruments=DP_CELL, baseline_repeatability_kpa=0.4).verdict, "RESTORED")


class ReadingValidationTests(unittest.TestCase):
    def problem(self, dp, flow, **kw):
        return vf.reading_problem(dp, flow, Q, **kw)

    def test_valid_reading(self):
        self.assertIsNone(self.problem(5.1, 21.0, pressure_before_kpa_abs=33.0, max_flow_lps=38.9))

    def test_missing_values(self):
        self.assertIn("post-cleaning Δp and the flow", self.problem(None, None))
        self.assertIn("the flow", self.problem(5.0, None))
        self.assertIn("post-cleaning Δp", self.problem(None, 21.0))

    def test_not_a_number(self):
        self.assertIn("numbers", self.problem("abc", 21.0))
        self.assertIn("finite", self.problem(float("nan"), 21.0))

    def test_zero_and_negative(self):
        self.assertIn("greater than 0 kPa", self.problem(0.0, 21.0))
        self.assertIn("greater than 0 kPa", self.problem(-1.0, 21.0))
        self.assertIn("greater than 0 L/s", self.problem(5.0, 0.0))

    def test_low_flow(self):
        self.assertIn("below 30%", self.problem(5.0, 5.0))

    def test_flow_above_pump_range(self):
        self.assertIn("units", self.problem(5.0, 76.3, max_flow_lps=38.9))

    def test_dp_larger_than_upstream_pressure(self):
        self.assertIn("cannot be equal to or larger", self.problem(40.0, 21.0, pressure_before_kpa_abs=33.0))


if __name__ == "__main__":
    unittest.main()

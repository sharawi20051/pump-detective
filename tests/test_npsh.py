"""Tests for the suction physics in npsh.py (independent hand calculations)."""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import npsh  # noqa: E402

Q_M3H = 21.2 * 3.6  # design flow, 76.32 m³/h
RHO_G = npsh.WATER_DENSITY_KG_M3 * npsh.GRAVITY_M_S2


class VelocityTests(unittest.TestCase):
    def test_dn100_design_flow(self):
        # 0.0212 m³/s through a 0.1 m bore: 0.0212 / 0.007854 = 2.70 m/s
        self.assertAlmostEqual(npsh.suction_velocity(Q_M3H, 100), 2.699, places=3)


class NpshaTests(unittest.TestCase):
    def test_atmospheric_suction(self):
        v = npsh.suction_velocity(Q_M3H, 100)
        expected = (101.325 - npsh.WATER_VAPOR_PRESSURE_KPA) * 1000 / RHO_G + v**2 / (2 * npsh.GRAVITY_M_S2)
        self.assertAlmostEqual(npsh.available_npsh(101.325, Q_M3H, 100), expected, places=9)
        self.assertAlmostEqual(expected, 10.48, places=2)

    def test_readme_demo_values(self):
        # README demo: 8 kPa abs at the flange gives 0.95 m; after cleaning (+20 kPa) 2.99 m.
        self.assertAlmostEqual(npsh.available_npsh(8.0, Q_M3H, 100), 0.95, places=2)
        self.assertAlmostEqual(npsh.available_npsh(28.0, Q_M3H, 100), 2.99, places=2)

    def test_pressure_for_npsha_is_inverse(self):
        for target in (0.5, 1.07, 3.0, 8.0):
            p = npsh.pressure_for_npsha(target, Q_M3H, 100)
            self.assertAlmostEqual(npsh.available_npsh(p, Q_M3H, 100), target, places=9)

    def test_boiling_input_rejected(self):
        self.assertIn("vapour pressure", npsh.npsha_input_problem(2.0, Q_M3H, 100))

    def test_small_pipe_is_not_safer(self):
        # A tiny diameter must be rejected, not rewarded with a large velocity head.
        self.assertIn("plausibility", npsh.npsha_input_problem(50.0, Q_M3H, 50))
        self.assertIsNone(npsh.npsha_input_problem(50.0, Q_M3H, 100))


class CurveTests(unittest.TestCase):
    def test_catalogue_points(self):
        for flow, head in npsh.LOWARA_CURVE:
            self.assertAlmostEqual(npsh.lowara_npshr(flow), head)

    def test_interpolation(self):
        self.assertAlmostEqual(npsh.lowara_npshr(130), (1.51 + 2.21) / 2)

    def test_outside_range(self):
        with self.assertRaises(ValueError):
            npsh.lowara_npshr(150)


class AssessmentTests(unittest.TestCase):
    def test_statuses(self):
        self.assertEqual(npsh.npsh_assessment(3.0, 1.0, 0.5)[2], "SAFE")
        self.assertEqual(npsh.npsh_assessment(1.3, 1.0, 0.5)[2], "WARNING")
        self.assertEqual(npsh.npsh_assessment(0.9, 1.0, 0.5)[2], "CRITICAL")

    def test_exact_boundary_is_not_a_deficit(self):
        self.assertEqual(npsh.npsh_assessment(1.5, 1.0, 0.5)[2], "SAFE")

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            npsh.npsh_assessment(math.nan, 1.0, 0.5)
        with self.assertRaises(ValueError):
            npsh.npsh_assessment(2.0, 1.0, -0.1)


class PipeLossTests(unittest.TestCase):
    def test_darcy_weisbach_readme_case(self):
        # 80 mm, 12 m, f = 0.025 at design flow: v = 4.217 m/s, Δp = f·L/D·ρv²/2
        v = (Q_M3H / 3600) / (math.pi * 0.08**2 / 4)
        expected = 0.025 * (12 / 0.08) * npsh.WATER_DENSITY_KG_M3 * v**2 / 2000
        self.assertAlmostEqual(npsh.straight_pipe_loss_kpa(Q_M3H, 80, 12, 0.025), expected, places=9)
        self.assertAlmostEqual(expected, 33.3, delta=0.1)


if __name__ == "__main__":
    unittest.main()

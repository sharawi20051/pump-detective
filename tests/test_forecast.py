"""Tests for the fouling forecast and the core suction physics.

Run from the project folder:  py -m unittest discover tests
"""
import math
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import forecast as fc  # noqa: E402
from pump_detective import diagnose_filter  # noqa: E402

Q_REF = 21.2


def analyse(scenario, upstream=33.0):
    log = fc.generate_sensor_log(scenario, upstream_kpa_abs=upstream, q_ref_lps=Q_REF)
    norm = fc.normalise_dp(log["dp_kpa"], log["flow_lps"], Q_REF)
    spikes = fc.find_spikes(norm)
    daily = fc.daily_medians(log, norm, spikes)
    steps = fc.find_steps(daily)
    return log, norm, spikes, daily, steps, fc.fit_trend(daily, steps=steps)


class NormalisationTests(unittest.TestCase):
    def test_reference_flow_is_unchanged(self):
        self.assertAlmostEqual(fc.normalise_dp([10.0], [Q_REF], Q_REF)[0], 10.0)

    def test_half_flow_quadruples(self):
        self.assertAlmostEqual(fc.normalise_dp([2.5], [Q_REF / 2], Q_REF)[0], 10.0)

    def test_very_low_flow_is_dropped(self):
        self.assertTrue(math.isnan(fc.normalise_dp([1.0], [0.1 * Q_REF], Q_REF)[0]))

    def test_normalisation_reduces_scatter(self):
        log, norm, *_ = analyse("Stable strainer")
        # Sensor noise remains, but the flow-driven swing is removed.
        self.assertLess(np.nanstd(norm), 0.8 * np.std(log["dp_kpa"].to_numpy()))


class ScenarioTests(unittest.TestCase):
    def test_gradual_fouling_rate_recovered(self):
        *_, steps, fit = analyse("Gradual fouling")
        self.assertEqual(steps, [])
        self.assertAlmostEqual(fit.rate_per_day, fc.SCENARIOS["Gradual fouling"]["rate"], delta=0.004)

    def test_injected_spikes_found(self):
        _, _, spikes, *_ = analyse("Gradual fouling")
        self.assertEqual(set(spikes.tolist()), set(fc.SCENARIOS["Gradual fouling"]["spike_hours"]))

    def test_debris_step_found_and_refit(self):
        *_, steps, fit = analyse("Debris slug")
        self.assertIn(45, steps)
        self.assertGreaterEqual(fit.start_day, 45)

    def test_stable_strainer_not_forecast(self):
        *_, fit = analyse("Stable strainer")
        self.assertIsNone(fc.days_to_limit(fit.current_kpa, fit.rate_per_day, 20.0))


class BacktestTests(unittest.TestCase):
    """Hide the last days of the log, forecast them with the same pipeline, and score."""

    def test_gradual_fouling_forecast_is_accurate(self):
        *_, daily, _, _ = analyse("Gradual fouling")
        bt = fc.backtest(daily, horizon_days=14)
        self.assertLess(bt.mape_pct, 10.0)
        self.assertGreaterEqual(bt.coverage_pct, 80.0)
        self.assertEqual(bt.train_days, daily.size - 14)

    def test_model_mismatch_still_close(self):
        # Linear fouling, exponential fit: over two weeks the error stays small.
        *_, daily, _, _ = analyse("Linear fouling (model mismatch)")
        self.assertLess(fc.backtest(daily, horizon_days=14).mape_pct, 10.0)

    def test_sudden_event_is_not_predicted(self):
        # A forecast made before the day-45 debris slug cannot see it coming.
        *_, daily, _, _ = analyse("Debris slug")
        bt = fc.backtest(daily, horizon_days=21)
        self.assertLess(bt.end_error_pct, -20.0)
        self.assertFalse(bt.recent_step)

    def test_step_at_end_of_training_is_flagged(self):
        *_, daily, _, _ = analyse("Debris slug")
        self.assertTrue(fc.backtest(daily, horizon_days=14).recent_step)

    def test_fit_reports_day_to_day_scatter(self):
        *_, fit = analyse("Gradual fouling")
        self.assertGreater(fit.resid_sd, 0.0)

    def test_horizon_too_long(self):
        with self.assertRaises(ValueError):
            fc.backtest(np.full(10, 5.0), horizon_days=8)


class DaysToLimitTests(unittest.TestCase):
    def test_already_reached(self):
        self.assertEqual(fc.days_to_limit(15.0, 0.01, 10.0), 0.0)

    def test_exponential_doubling(self):
        self.assertAlmostEqual(fc.days_to_limit(5.0, math.log(2) / 10, 10.0), 10.0)

    def test_flat_trend(self):
        self.assertIsNone(fc.days_to_limit(5.0, 0.0, 10.0))


class FilterRuleTests(unittest.TestCase):
    def test_restriction(self):
        self.assertIn("restriction", diagnose_filter(33.0, 8.0)[1])

    def test_upstream_problem(self):
        self.assertIn("upstream", diagnose_filter(13.0, 8.0)[1])

    def test_clean_reference(self):
        self.assertIn("matches", diagnose_filter(110.0, 105.0)[1])

    def test_missing_reading(self):
        self.assertIsNone(diagnose_filter(None, 85.0)[0])


if __name__ == "__main__":
    unittest.main()

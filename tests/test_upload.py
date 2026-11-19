"""Tests for reading a user's sensor log (forecast.load_sensor_csv)."""
import io
import os
import sys
import unittest

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import forecast as fc  # noqa: E402

Q_REF = 21.2
EXAMPLE = os.path.join(ROOT, "examples", "example_sensor_log.csv")


def csv_text(days=21, freq="30min", dp_only=False, **overrides):
    t = pd.date_range("2026-10-01", periods=int(days * 24 * 60 / int(freq[:-3])), freq=freq)
    flow = np.full(t.size, Q_REF)
    df = pd.DataFrame({"timestamp": t.strftime("%Y-%m-%d %H:%M"), "flow_lps": flow})
    if dp_only:
        df["dp_kpa"] = 6.0
    else:
        df["pressure_before_kpa_abs"] = 105.0
        df["suction_kpa_abs"] = 99.0
    for key, value in overrides.items():
        df[key] = value
    return io.StringIO(df.to_csv(index=False))


def analyse(log):
    norm = fc.normalise_dp(log["dp_kpa"], log["flow_lps"], Q_REF)
    daily = fc.daily_medians(log, norm, fc.find_spikes(norm))
    return daily, fc.regime_changes(daily)


class ExampleFileTests(unittest.TestCase):
    def setUp(self):
        self.log, self.info = fc.load_sensor_csv(EXAMPLE, Q_REF)

    def test_shape_matches_synthetic_log(self):
        self.assertEqual(list(self.log.columns), list(fc.generate_sensor_log("Stable strainer").columns))
        self.assertEqual(self.info["days"], 40)
        self.assertEqual(self.info["interval_minutes"], 15.0)
        self.assertEqual(self.info["warnings"], [])

    def test_cleaning_detected_and_trend_restarts(self):
        daily, changes = analyse(self.log)
        self.assertEqual(fc.find_drops(daily), [12])
        fit = fc.fit_trend(daily, steps=changes)
        self.assertGreater(fit.start_day, 12)
        self.assertAlmostEqual(fit.rate_per_day, 0.02, delta=0.005)

    def test_backtest_runs(self):
        daily, _ = analyse(self.log)
        self.assertLess(fc.backtest(daily, horizon_days=14).mape_pct, 10.0)


class FormatTests(unittest.TestCase):
    def test_dp_transmitter_only(self):
        log, info = fc.load_sensor_csv(csv_text(dp_only=True), Q_REF)
        self.assertAlmostEqual(float(np.nanmedian(log["dp_kpa"])), 6.0)
        self.assertFalse(info["has_absolute_pressures"])

    def test_column_names_are_case_insensitive(self):
        text = csv_text().getvalue().replace("timestamp", "Timestamp").replace("flow_lps", " FLOW_LPS")
        log, _ = fc.load_sensor_csv(io.StringIO(text), Q_REF)
        self.assertAlmostEqual(float(np.nanmedian(log["dp_kpa"])), 6.0)

    def test_resampled_to_hourly_from_midnight(self):
        log, _ = fc.load_sensor_csv(csv_text(freq="10min"), Q_REF)
        self.assertEqual(int(log["hour"].iloc[0]), 0)
        self.assertEqual(len(log), 21 * 24)

    def test_stopped_pump_becomes_a_gap(self):
        df = pd.read_csv(csv_text())
        df.loc[:47, "flow_lps"] = 0.0
        log, _ = fc.load_sensor_csv(io.StringIO(df.to_csv(index=False)), Q_REF)
        self.assertTrue(log["flow_lps"].iloc[:24].isna().all())


class RejectionTests(unittest.TestCase):
    def assertRejected(self, source, fragment):
        with self.assertRaises(fc.SensorLogError) as ctx:
            fc.load_sensor_csv(source, Q_REF)
        self.assertIn(fragment, str(ctx.exception))

    def test_missing_columns(self):
        self.assertRejected(io.StringIO("timestamp,flow_lps\n2026-10-01 00:00,20\n"), "suction_kpa_abs")

    def test_too_short(self):
        self.assertRejected(csv_text(days=12), "at least 15 days")

    def test_gauge_pressure(self):
        self.assertRejected(csv_text(pressure_before_kpa_abs=-20.0, suction_kpa_abs=-26.0), "absolute")

    def test_swapped_taps(self):
        self.assertRejected(csv_text(pressure_before_kpa_abs=99.0, suction_kpa_abs=105.0), "swapped")

    def test_not_a_csv(self):
        self.assertRejected(io.BytesIO(b"\x89PNG\r\n\x1a\n\x00\x00binary"), "could not be read")

    def test_unreadable_times(self):
        self.assertRejected(io.StringIO("timestamp,flow_lps,dp_kpa\nyesterday,20,5\nsoon,20,5\n"), "timestamps")


class WarningTests(unittest.TestCase):
    def test_flow_in_m3h_rejected(self):
        with self.assertRaises(fc.SensorLogError) as ctx:
            fc.load_sensor_csv(csv_text(flow_lps=Q_REF * 3.6), Q_REF)
        self.assertIn("m³/h", str(ctx.exception))

    def test_low_flow_warns(self):
        _, info = fc.load_sensor_csv(csv_text(flow_lps=0.2 * Q_REF), Q_REF)
        self.assertTrue(any("30 %" in w for w in info["warnings"]))

    def test_downloaded_synthetic_log_round_trips(self):
        # The app's download adds a timestamp column and keeps upstream_kpa_abs: it must load again.
        log = fc.generate_sensor_log("Debris slug")
        export = log.assign(timestamp=pd.Timestamp("2026-09-20") + pd.to_timedelta(log["hour"], unit="h"))
        back, info = fc.load_sensor_csv(io.StringIO(export.to_csv(index=False)), Q_REF)
        self.assertEqual(info["days"], 60)
        np.testing.assert_allclose(back["dp_kpa"].to_numpy(), log["dp_kpa"].to_numpy(), atol=1e-9)
        daily, changes = analyse(back)
        self.assertIn(45, changes)


if __name__ == "__main__":
    unittest.main()

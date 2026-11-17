"""Strainer fouling trend and forecast from a (synthetic) sensor log.

Everything here is pure numpy / pandas so it can be tested without Streamlit.
Pressures are kPa (Δp) or kPa abs (line pressures); flow is L/s; time is hours.

Engineering basis
-----------------
A strainer behaves like a fixed-geometry restriction in turbulent flow, so its
pressure drop scales with flow squared: Δp = K · Q². Comparing raw Δp readings
taken at different flows is therefore misleading. Normalising every reading to a
reference flow, Δp* = Δp · (Q_ref / Q)², removes the flow effect and leaves the
change in K, which is the fouling signal we trend.
"""

from dataclasses import dataclass
from math import log

import numpy as np
import pandas as pd

HOURS_PER_DAY = 24

# Synthetic scenarios. dp0 is the clean normalised Δp on day 0, rate is the
# exponential fouling rate per day, step adds a sudden debris-slug event.
SCENARIOS = {
    "Gradual fouling": {
        "dp0": 5.0, "rate": 0.0131, "step_day": None, "step_kpa": 0.0, "rate_after_step": None,
        "spike_hours": (310, 777, 1105), "spike_kpa": 9.0, "seed": 7,
        "story": "Debris slowly builds up on the strainer screen over two months.",
    },
    "Debris slug": {
        "dp0": 5.0, "rate": 0.0131, "step_day": 45, "step_kpa": 4.0, "rate_after_step": 0.021,
        "spike_hours": (402,), "spike_kpa": 9.0, "seed": 11,
        "story": "Slow fouling, then a sudden load of debris (for example after pipe work) on day 45.",
    },
    "Stable strainer": {
        "dp0": 5.0, "rate": 0.0005, "step_day": None, "step_kpa": 0.0, "rate_after_step": None,
        "spike_hours": (950,), "spike_kpa": 9.0, "seed": 3,
        "story": "Clean water and a recently serviced strainer: almost no fouling.",
    },
}


def generate_sensor_log(scenario, days=60, upstream_kpa_abs=33.0, q_ref_lps=21.2):
    """Return an hourly synthetic sensor log as a DataFrame.

    Columns: hour, day, flow_lps, upstream_kpa_abs, suction_kpa_abs, dp_kpa.
    Flow varies with a daily cycle and day-to-day staging so that the raw Δp is
    noisy; pressure sensors have small Gaussian noise; a few isolated hours carry
    sensor spikes. The data are deterministic for a given scenario.
    """
    p = SCENARIOS[scenario]
    rng = np.random.default_rng(p["seed"])
    hours = np.arange(days * HOURS_PER_DAY)
    day = hours / HOURS_PER_DAY

    # Flow ratio: daily load cycle plus a per-day staging offset.
    staging = rng.uniform(-0.06, 0.04, size=days)[hours // HOURS_PER_DAY]
    ratio = 0.90 + 0.07 * np.sin(2 * np.pi * (hours % HOURS_PER_DAY - 9) / HOURS_PER_DAY) + staging
    ratio = np.clip(ratio + rng.normal(0, 0.01, hours.size), 0.70, 1.05)
    flow = q_ref_lps * ratio

    # True normalised strainer Δp (the quantity the analysis should recover).
    dp_star = p["dp0"] * np.exp(p["rate"] * day)
    if p["step_day"] is not None:
        after = day >= p["step_day"]
        at_step = p["dp0"] * np.exp(p["rate"] * p["step_day"]) + p["step_kpa"]
        dp_star[after] = at_step * np.exp(p["rate_after_step"] * (day[after] - p["step_day"]))
    # Real fouling is not perfectly smooth: add day-to-day variation of a few percent.
    dp_star *= np.exp(rng.normal(0, 0.03, days))[hours // HOURS_PER_DAY]

    dp_true = dp_star * ratio**2
    upstream = upstream_kpa_abs + rng.normal(0, 0.25, hours.size)
    suction = upstream - dp_true + rng.normal(0, 0.25, hours.size)
    spikes = np.array(p["spike_hours"], dtype=int)
    spikes = spikes[spikes < hours.size]
    suction[spikes] -= p["spike_kpa"]  # a suction transmitter glitch

    return pd.DataFrame({
        "hour": hours, "day": day, "flow_lps": flow,
        "upstream_kpa_abs": upstream, "suction_kpa_abs": suction,
        "dp_kpa": upstream - suction,
    })


def normalise_dp(dp_kpa, flow_lps, q_ref_lps):
    """Δp* = Δp · (Q_ref/Q)²; readings at very low flow are unreliable and dropped (NaN)."""
    dp = np.asarray(dp_kpa, dtype=float)
    q = np.asarray(flow_lps, dtype=float)
    out = np.full(dp.shape, np.nan)
    ok = q >= 0.3 * q_ref_lps
    out[ok] = dp[ok] * (q_ref_lps / q[ok]) ** 2
    return out


def find_spikes(dp_norm, window=25, z_limit=6.0):
    """Indices of isolated outliers: robust z-score against a centred rolling median."""
    s = pd.Series(dp_norm)
    median = s.rolling(window, center=True, min_periods=5).median()
    resid = s - median
    mad = np.nanmedian(np.abs(resid - np.nanmedian(resid)))
    scale = 1.4826 * mad if mad > 0 else 1e-9
    z = resid / scale
    return np.flatnonzero(np.abs(z.to_numpy()) > z_limit)


def find_steps(daily_median, min_jump_kpa=1.5):
    """Day indices where the daily median jumps versus the previous three days."""
    m = np.asarray(daily_median, dtype=float)
    steps = []
    for d in range(3, m.size):
        if m[d] - np.median(m[d - 3:d]) > min_jump_kpa and m[d] - m[d - 1] > 0.6 * min_jump_kpa:
            steps.append(d)
    # Keep only the first day of each jump.
    return [d for i, d in enumerate(steps) if i == 0 or d - steps[i - 1] > 1]


@dataclass
class TrendFit:
    start_day: int        # first day used in the fit
    current_kpa: float    # fitted normalised Δp at the end of the log
    rate_per_day: float   # exponential growth rate
    rate_se: float        # standard error of the rate
    days_used: int


def fit_trend(daily_median, max_window_days=21, min_days=5, steps=()):
    """Fit ln(Δp*) = a + b·day on recent daily medians.

    The window starts after the most recent step change (the old regime no longer
    describes the strainer) and is at most ``max_window_days`` long.
    """
    m = np.asarray(daily_median, dtype=float)
    n = m.size
    start = max(0, n - max_window_days)
    if steps:
        start = max(start, min(max(steps), n - min_days))
    x = np.arange(start, n, dtype=float)
    y = np.log(m[start:])
    keep = np.isfinite(y)
    x, y = x[keep], y[keep]
    if x.size < 3:
        raise ValueError("Not enough valid days to fit a trend.")
    b, a = np.polyfit(x, y, 1)
    resid = y - (a + b * x)
    dof = max(x.size - 2, 1)
    se = float(np.sqrt(np.sum(resid**2) / dof / np.sum((x - x.mean()) ** 2)))
    current = float(np.exp(a + b * (n - 1)))
    return TrendFit(start, current, float(b), se, int(x.size))


def days_to_limit(current_kpa, rate_per_day, limit_kpa, horizon_days=180):
    """Days from now until the exponential trend reaches ``limit_kpa``.

    Returns 0.0 if already at or above the limit and None if it is not reached
    within the horizon (including flat or improving trends).
    """
    if limit_kpa <= current_kpa:
        return 0.0
    if rate_per_day <= 1e-6:
        return None
    days = log(limit_kpa / current_kpa) / rate_per_day
    return days if days <= horizon_days else None


def daily_medians(log_df, dp_norm, spike_idx=()):
    """Daily median of Δp* with spike hours removed."""
    values = np.array(dp_norm, dtype=float)
    values[list(spike_idx)] = np.nan
    days = (log_df["hour"].to_numpy() // HOURS_PER_DAY).astype(int)
    return pd.Series(values).groupby(days).median().to_numpy()

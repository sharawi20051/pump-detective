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

import warnings
from dataclasses import dataclass
from math import log

import numpy as np
import pandas as pd

HOURS_PER_DAY = 24

# Synthetic scenarios. dp0 is the clean normalised Δp on day 0, rate is the
# exponential fouling rate per day, step adds a sudden debris-slug event.
# "Linear fouling" deliberately does NOT follow the exponential model the
# forecast fits, so the backtest can show how the method behaves when its
# assumption is wrong.
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
    "Linear fouling (model mismatch)": {
        "dp0": 5.0, "rate": 0.0, "slope_kpa_per_day": 0.09, "step_day": None, "step_kpa": 0.0,
        "rate_after_step": None, "spike_hours": (520, 1290), "spike_kpa": 9.0, "seed": 19,
        "story": "Debris builds up at a constant rate, not exponentially. The forecast still fits an exponential "
                 "trend; the backtest shows what that assumption costs.",
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
    if p.get("slope_kpa_per_day"):
        dp_star = p["dp0"] + p["slope_kpa_per_day"] * day
    else:
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


def find_drops(daily_median, min_drop_kpa=1.5):
    """Day indices where the daily median falls sharply: usually a strainer cleaning.

    The mirror image of ``find_steps``. Real logs contain cleanings; the trend
    must restart after the most recent one, exactly as it does after a debris slug.
    """
    return find_steps(-np.asarray(daily_median, dtype=float), min_jump_kpa=min_drop_kpa)


def regime_changes(daily_median):
    """All step increases and sudden drops, sorted: the trend restarts after the last one."""
    return sorted(set(find_steps(daily_median)) | set(find_drops(daily_median)))


@dataclass
class TrendFit:
    start_day: int        # first day used in the fit
    current_kpa: float    # fitted normalised Δp at the end of the log
    rate_per_day: float   # exponential growth rate
    rate_se: float        # standard error of the rate
    days_used: int
    resid_sd: float = 0.0  # scatter of daily ln(Δp*) around the fit (day-to-day variation)


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
    resid_sd = float(np.sqrt(np.sum(resid**2) / dof))
    return TrendFit(start, current, float(b), se, int(x.size), resid_sd)


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


@dataclass
class Backtest:
    train_days: int          # daily medians available to the past forecast
    horizon_days: int        # days held out and compared
    fit: TrendFit            # the fit made on the training days only
    predicted: np.ndarray    # forecast Δp* for each held-out day
    low: np.ndarray          # 95 % prediction range (trend uncertainty + day-to-day scatter)
    high: np.ndarray
    actual: np.ndarray       # observed daily median Δp* on the held-out days
    mape_pct: float          # mean absolute percentage error over the held-out days
    end_error_pct: float     # (forecast − actual) / actual on the last held-out day
    coverage_pct: float      # share of held-out days inside the 95 % range
    recent_step: bool = False  # a step change sits too close to the end of the training days


def backtest(daily_median, horizon_days=14, max_window_days=21, min_days=5):
    """Hide the last ``horizon_days`` of the log, forecast them, and score the forecast.

    The past forecast uses exactly the same pipeline as the live one (step detection
    on the training days only, then ``fit_trend``), so the score describes the method,
    not a model tuned to the answer. The 95 % range combines the uncertainty of the
    fitted rate with the day-to-day scatter of the daily medians, because the
    comparison is against individual days.
    """
    m = np.asarray(daily_median, dtype=float)
    n_train = m.size - horizon_days
    if horizon_days < 1 or n_train < min_days + 3:
        raise ValueError("Not enough history for a backtest of this length.")
    train = m[:n_train]
    steps = regime_changes(train)
    fit = fit_trend(train, max_window_days=max_window_days, min_days=min_days, steps=steps)
    h = np.arange(1, horizon_days + 1, dtype=float)
    predicted = fit.current_kpa * np.exp(fit.rate_per_day * h)
    half_width = 1.96 * np.sqrt((h * fit.rate_se) ** 2 + fit.resid_sd ** 2)
    low, high = predicted * np.exp(-half_width), predicted * np.exp(half_width)
    actual = m[n_train:]
    ok = np.isfinite(actual)
    if not ok.any():
        raise ValueError("No valid readings in the hidden days.")
    last = np.flatnonzero(ok)[-1]
    err = (predicted[ok] - actual[ok]) / actual[ok]
    inside = (actual[ok] >= low[ok]) & (actual[ok] <= high[ok])
    return Backtest(
        n_train, horizon_days, fit, predicted, low, high, actual,
        mape_pct=float(100 * np.mean(np.abs(err))),
        end_error_pct=float(100 * (predicted[last] - actual[last]) / actual[last]),
        coverage_pct=float(100 * np.mean(inside)),
        recent_step=bool(steps) and max(steps) > n_train - min_days,
    )


# --- Uploaded sensor logs ------------------------------------------------------

class SensorLogError(ValueError):
    """A sensor log that cannot be analysed; the message is safe to show to the user."""


# Accepted column names (case-insensitive). The first name is the documented one.
CSV_COLUMNS = {
    "timestamp": ("timestamp", "time", "datetime", "date_time"),
    "flow_lps": ("flow_lps",),
    "pressure_before_kpa_abs": ("pressure_before_kpa_abs", "upstream_kpa_abs"),
    "suction_kpa_abs": ("suction_kpa_abs",),
    "dp_kpa": ("dp_kpa", "strainer_dp_kpa"),
}
MIN_UPLOAD_DAYS = 15  # 8 days to fit + 7 hidden for the shortest backtest
# Below this, a pressure labelled absolute is more likely a gauge reading (a closed chilled-water loop at
# 20 kPa abs would be in deep vacuum). The demo plant runs at 33 kPa abs, so it does not trigger.
LOW_ABSOLUTE_KPA = 20.0
WATER_VAPOUR_KPA_20C = 2.339


def load_sensor_csv(source, q_ref_lps, min_days=MIN_UPLOAD_DAYS):
    """Read a user's strainer sensor log and return (log, info).

    Required columns: ``timestamp`` and ``flow_lps`` (L/s), plus either both
    ``pressure_before_kpa_abs`` and ``suction_kpa_abs`` (kPa abs) or ``dp_kpa``
    from a differential transmitter. Any logging interval works: readings are
    averaged to hourly values, so the result has the same shape as
    ``generate_sensor_log`` and goes through the same analysis. Days are counted
    from midnight of the first day. Rows with an unreadable time are dropped;
    non-numeric or non-positive flows (pump stopped) become gaps.
    """
    try:
        raw = pd.read_csv(source)
    except Exception:  # noqa: BLE001 - any parser failure gets the same friendly message
        raise SensorLogError("The file could not be read as CSV. Save it as comma-separated text with a header row.")
    names = {str(c).strip().lower(): c for c in raw.columns}

    def column(key):
        for alias in CSV_COLUMNS[key]:
            if alias in names:
                return raw[names[alias]]
        return None

    ts, flow = column("timestamp"), column("flow_lps")
    before, suction, dp = column("pressure_before_kpa_abs"), column("suction_kpa_abs"), column("dp_kpa")
    missing = [k for k, v in (("timestamp", ts), ("flow_lps", flow)) if v is None]
    if dp is None and (before is None or suction is None):
        missing.append("pressure_before_kpa_abs + suction_kpa_abs (or dp_kpa)")
    if missing:
        raise SensorLogError("Missing column(s): " + ", ".join(missing) + ". See the expected format below.")

    with warnings.catch_warnings():  # mixed or unusual date formats are parsed row by row; that is fine
        warnings.simplefilter("ignore", UserWarning)
        times = pd.to_datetime(ts, errors="coerce")
    if getattr(times.dt, "tz", None) is not None:
        times = times.dt.tz_localize(None)  # keep the local clock time the logger wrote

    def numeric(series):
        return pd.to_numeric(series, errors="coerce") if series is not None else pd.Series(np.nan, index=raw.index)

    df = pd.DataFrame({"t": times, "flow_lps": numeric(flow), "before": numeric(before),
                       "suction": numeric(suction), "dp": numeric(dp)})
    if dp is None:
        df["dp"] = df["before"] - df["suction"]
    bad_times = int(df["t"].isna().sum())
    df = df.dropna(subset=["t"]).sort_values("t").drop_duplicates("t")
    if df.empty:
        raise SensorLogError("No readable timestamps. Use a format such as 2026-11-01 14:00.")
    df.loc[~(df["flow_lps"] > 0), "flow_lps"] = np.nan

    hourly = df.set_index("t")[["flow_lps", "before", "suction", "dp"]].resample("1h").mean()
    start = hourly.index[0].normalize()
    hours = ((hourly.index - start) / pd.Timedelta(hours=1)).to_numpy().astype(int)
    span_days = int(hours[-1] // HOURS_PER_DAY) + 1
    if span_days < min_days:
        raise SensorLogError(f"The log covers {span_days} day(s); at least {min_days} days are needed for a trend "
                             "and a backtest.")
    usable = hourly["dp"].notna() & hourly["flow_lps"].notna()
    if usable.sum() < min_days * HOURS_PER_DAY * 0.5:
        raise SensorLogError("Too few hours have both a pressure drop and a flow reading to fit a trend.")

    med_dp, med_flow = float(hourly["dp"].median()), float(hourly["flow_lps"].median())
    if med_dp <= 0:
        raise SensorLogError("The strainer pressure drop is zero or negative on most readings. Check that the "
                             "pressure columns are not swapped.")
    notes = []
    med_before = float(hourly["before"].median()) if hourly["before"].notna().any() else None
    if med_before is not None and med_before <= 0:
        raise SensorLogError("Pressure before the strainer must be absolute (kPa abs, always positive). If the "
                             "logger records gauge pressure, add the local atmospheric pressure (about 101.3 kPa).")
    if med_before is not None and med_before > 2000:
        notes.append(f"Pressure before the strainer is about {med_before:,.0f}: is it in Pa rather than kPa?")
    # A positive gauge reading cannot be told apart from an absolute one, but very low values are a strong hint:
    # the NPSH checks need absolute pressure, while the strainer Δp (a difference) is unaffected.
    if med_before is not None and 0 < med_before < LOW_ABSOLUTE_KPA:
        notes.append(f"Pressure before the strainer is about {med_before:.1f} kPa, unusually low for an absolute "
                     "pressure. If the logger records gauge pressure, add the local atmospheric pressure (about "
                     "101.3 kPa) to both pressure columns; otherwise the NPSH results will be wrong.")
    med_suction = float(hourly["suction"].median()) if hourly["suction"].notna().any() else None
    if med_suction is not None and med_suction <= WATER_VAPOUR_KPA_20C:
        notes.append(f"Suction pressure is about {med_suction:.1f} kPa, at or below the vapour pressure of water: "
                     "it cannot be an absolute pressure. Check for gauge readings or swapped units.")
    if med_dp > 100:
        notes.append(f"Strainer Δp is about {med_dp:.0f} kPa, very high for a strainer: check the units.")
    if med_flow > 2 * q_ref_lps:
        raise SensorLogError(f"Typical flow is {med_flow:.1f}, more than twice the {q_ref_lps:g} L/s design flow, "
                             "so the flow correction would be meaningless. Is the column in m³/h? Convert to L/s "
                             "(divide by 3.6).")
    if med_flow < 0.3 * q_ref_lps:
        notes.append(f"Typical flow is {med_flow:.1f} L/s, below 30 % of design flow; most readings will be "
                        "excluded from the flow normalisation.")
    gap_hours = int((~usable).sum())
    if gap_hours > 0.2 * len(hourly):
        notes.append(f"{gap_hours} of {len(hourly)} hours have no usable reading.")

    last_week = hourly["before"][hourly.index >= hourly.index[-1] - pd.Timedelta(days=7)]
    log = pd.DataFrame({
        "hour": hours, "day": hours / HOURS_PER_DAY, "flow_lps": hourly["flow_lps"].to_numpy(),
        "upstream_kpa_abs": hourly["before"].to_numpy(), "suction_kpa_abs": hourly["suction"].to_numpy(),
        "dp_kpa": hourly["dp"].to_numpy(),
    })
    steps = df["t"].diff().dropna()
    info = {
        "first_reading": df["t"].iloc[0], "last_reading": df["t"].iloc[-1], "start_midnight": start,
        "days": span_days, "rows_read": int(len(raw)), "rows_bad_time": bad_times,
        "interval_minutes": float(steps.median() / pd.Timedelta(minutes=1)) if len(steps) else None,
        "hours_without_data": gap_hours,
        "pressure_before_last_7d_kpa_abs": float(last_week.median()) if last_week.notna().any() else None,
        "has_absolute_pressures": med_before is not None,
        "warnings": notes,
    }
    return log, info

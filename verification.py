"""Post-maintenance verification of a suction strainer.

Pure Python (no Streamlit) so it can be unit tested.

Method
------
1. Flow-normalise the post-cleaning reading to the reference flow, because a
   strainer's loss follows Δp = K·Q²:  Δp* = Δp · (Q_ref / Q)².
2. Estimate the measurement uncertainty from instrument accuracy specs, following
   the GUM approach: a manufacturer accuracy of ±a is treated as a rectangular
   limit, so its standard uncertainty is a/√3.
     - Two absolute transmitters:  u(Δp) = √2 · u(p)
     - One differential transmitter: u(Δp) = u(DP cell)
     - Δp* relative uncertainty:  √[(u(Δp)/Δp)² + (2·u(Q)/Q)²]
3. Compare with the clean baseline. The baseline is assumed to have been measured
   with the same instruments, so it carries the same type of uncertainty, plus an
   optional repeatability term from past post-cleaning readings.
   Expanded uncertainty of the difference: U = k · √[u(Δp*)² + u(baseline)²], k = 2 (≈95 %).
4. Grade the result:
     - Δp* below baseline − U        → SUSPICIOUSLY LOW (torn/missing screen, bypass or sensor)
     - |Δp* − baseline| ≤ U           → RESTORED
     - above baseline + U, below limit → IMPROVED, NOT CLEAN
     - at or above the maintenance limit → NOT EFFECTIVE
"""

from dataclasses import dataclass
from math import isfinite, sqrt

COVERAGE_K = 2.0
TWO_ABSOLUTE = "Two absolute pressure transmitters"
DIFFERENTIAL = "One differential pressure transmitter"
MIN_FLOW_FRACTION = 0.3  # same validity floor as the forecast's flow normalisation


@dataclass
class Instruments:
    method: str = TWO_ABSOLUTE
    pressure_span_kpa: float = 400.0       # span of each absolute transmitter, or of the DP cell
    pressure_accuracy_pct_span: float = 0.1
    flow_accuracy_pct_reading: float = 0.5


@dataclass
class Verification:
    verdict: str
    dp_star_kpa: float
    baseline_kpa: float
    expanded_uncertainty_kpa: float
    u_dp_star_kpa: float
    reduction_pct: float | None
    message: str
    next_check: str


def reading_problem(dp_kpa, flow_lps, q_ref_lps, pressure_before_kpa_abs=None, max_flow_lps=None):
    """Return a friendly message if a post-maintenance reading cannot be used, else None.

    Checks: missing values, non-numbers, zero or negative values, flow too low for the
    Q² normalisation, flow above the pump's published range (often a unit mix-up), and a
    Δp equal to or larger than the absolute pressure before the strainer (impossible).
    """
    if dp_kpa is None or flow_lps is None:
        missing = [name for name, value in (("the post-cleaning Δp", dp_kpa), ("the flow", flow_lps)) if value is None]
        return "Enter " + " and ".join(missing) + " before verifying."
    try:
        dp, flow = float(dp_kpa), float(flow_lps)
    except (TypeError, ValueError):
        return "Δp and flow must be numbers."
    if not (isfinite(dp) and isfinite(flow)):
        return "Δp and flow must be finite numbers."
    if dp <= 0:
        return ("Δp must be greater than 0 kPa. A zero or negative drop across a strainer usually means swapped "
                "or mis-located pressure taps; check the readings.")
    if flow <= 0:
        return "Flow must be greater than 0 L/s. Verify the strainer while the pump is running."
    if flow < MIN_FLOW_FRACTION * q_ref_lps:
        return (f"Flow {flow:g} L/s is below {MIN_FLOW_FRACTION:.0%} of design flow ({MIN_FLOW_FRACTION * q_ref_lps:.1f} L/s). "
                "The Q² correction is not reliable there; re-measure closer to design flow.")
    if max_flow_lps is not None and flow > max_flow_lps:
        return (f"Flow {flow:g} L/s is above the pump's published range (max {max_flow_lps:.1f} L/s). "
                "Check the units (L/s, not m³/h) and the flow meter.")
    if pressure_before_kpa_abs is not None and dp >= pressure_before_kpa_abs:
        return (f"Δp {dp:g} kPa cannot be equal to or larger than the absolute pressure before the strainer "
                f"({pressure_before_kpa_abs:g} kPa abs). Check units (kPa vs bar or psi) and the readings.")
    return None


def dp_uncertainty_kpa(instruments):
    """Standard uncertainty of the measured Δp (kPa) from the transmitter spec."""
    if instruments.pressure_span_kpa <= 0 or instruments.pressure_accuracy_pct_span < 0:
        raise ValueError("Pressure span must be positive and accuracy non-negative.")
    u_single = instruments.pressure_span_kpa * instruments.pressure_accuracy_pct_span / 100 / sqrt(3)
    return sqrt(2) * u_single if instruments.method == TWO_ABSOLUTE else u_single


def normalised_with_uncertainty(dp_kpa, flow_lps, q_ref_lps, instruments):
    """Return (Δp*, u(Δp*)) in kPa."""
    if flow_lps < MIN_FLOW_FRACTION * q_ref_lps:
        raise ValueError(f"Flow below {MIN_FLOW_FRACTION:.0%} of the reference flow: the Q² normalisation "
                         "is not reliable. Re-measure closer to design flow.")
    if dp_kpa <= 0:
        raise ValueError("Measured Δp must be positive. Check pressure readings and tap locations.")
    if instruments.flow_accuracy_pct_reading < 0:
        raise ValueError("Flow accuracy must be non-negative.")
    factor = (q_ref_lps / flow_lps) ** 2
    dp_star = dp_kpa * factor
    u_rel_dp = dp_uncertainty_kpa(instruments) / dp_kpa
    u_rel_q = instruments.flow_accuracy_pct_reading / 100 / sqrt(3)
    return dp_star, dp_star * sqrt(u_rel_dp**2 + (2 * u_rel_q) ** 2)


def verify_cleaning(dp_after_kpa, flow_after_lps, q_ref_lps, baseline_kpa, maintenance_limit_kpa,
                    instruments=None, dp_star_before_kpa=None, baseline_repeatability_kpa=0.0):
    """Grade a post-maintenance strainer reading against the clean baseline.

    ``baseline_repeatability_kpa`` is the standard deviation of past post-cleaning
    Δp* readings (how repeatable "clean" is for this strainer). 0 means only the
    instrument uncertainty is considered.
    """
    instruments = instruments or Instruments()
    if baseline_kpa <= 0 or maintenance_limit_kpa <= baseline_kpa:
        raise ValueError("Baseline must be positive and below the maintenance limit.")
    if baseline_repeatability_kpa < 0:
        raise ValueError("Baseline repeatability must be non-negative.")
    dp_star, u_star = normalised_with_uncertainty(dp_after_kpa, flow_after_lps, q_ref_lps, instruments)
    # Baseline measured at reference flow with the same instruments, plus its repeatability.
    _, u_base_instr = normalised_with_uncertainty(baseline_kpa, q_ref_lps, q_ref_lps, instruments)
    u_base = sqrt(u_base_instr**2 + baseline_repeatability_kpa**2)
    big_u = COVERAGE_K * sqrt(u_star**2 + u_base**2)
    diff = dp_star - baseline_kpa
    reduction = None
    if dp_star_before_kpa:
        reduction = 100 * (dp_star_before_kpa - dp_star) / dp_star_before_kpa

    band = f"{baseline_kpa:.2f} ± {big_u:.2f} kPa"
    if dp_star >= maintenance_limit_kpa:
        return Verification("NOT EFFECTIVE", dp_star, baseline_kpa, big_u, u_star, reduction,
                            f"Δp* {dp_star:.2f} kPa is still at or above the {maintenance_limit_kpa:g} kPa cleaning limit.",
                            "Re-inspect the strainer: basket seating, remaining debris, correct strainer cleaned.")
    if diff < -big_u:
        return Verification("SUSPICIOUSLY LOW", dp_star, baseline_kpa, big_u, u_star, reduction,
                            f"Δp* {dp_star:.2f} kPa is below the clean band {band}.",
                            "Check for a torn or missing screen, an open bypass, wrong tap locations or a sensor fault "
                            "before accepting the job.")
    if diff <= big_u:
        return Verification("RESTORED", dp_star, baseline_kpa, big_u, u_star, reduction,
                            f"Δp* {dp_star:.2f} kPa is within the clean band {band}.",
                            "Close the work order and use this reading as the new trend starting point.")
    return Verification("IMPROVED, NOT CLEAN", dp_star, baseline_kpa, big_u, u_star, reduction,
                        f"Δp* {dp_star:.2f} kPa is above the clean band {band} but below the cleaning limit.",
                        "Check basket seating and residual debris, and confirm the clean baseline is current.")

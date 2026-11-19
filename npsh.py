"""Suction physics for Pump Detective: NPSHa, the Lowara demo NPSHr curve and pipe loss.

Pure Python (no Streamlit) so it can be unit tested. Pressures are kPa abs,
flows m³/h, diameters mm, heads m. Water properties are taken at 20 °C, which is
conservative for chilled water (colder water has a lower vapour pressure).
"""

from math import isclose, isfinite, pi


# Approximate readings from the Lowara NSC 80-200/55 curve, p. 100, 1450 rpm.
# Each pair is (flow in m³/h, laboratory NPSH in m).
LOWARA_CURVE = ((40, 1.07), (60, 1.04), (80, 1.06), (100, 1.19), (120, 1.51), (140, 2.21))
CATALOG_ALLOWANCE_M = 0.5
WATER_VAPOR_PRESSURE_KPA = 2.339  # Water at 20 °C
WATER_DENSITY_KG_M3 = 998.2
GRAVITY_M_S2 = 9.80665
# Lowara NSC 80-200 suction flange is DN100; the NPSH datum reading is taken there.
LOWARA_SUCTION_NOZZLE_MM = 100
# Above this velocity a suction reading is treated as implausible (typical suction
# nozzle velocities are roughly 1-4 m/s). Illustrative plausibility check only.
MAX_PLAUSIBLE_SUCTION_VELOCITY_M_S = 5.0


def suction_velocity(flow_m3_h, diameter_mm):
    area_m2 = pi * (diameter_mm / 1000) ** 2 / 4
    return (flow_m3_h / 3600) / area_m2


def npsha_input_problem(pressure_abs_kpa, flow_m3_h, diameter_mm):
    """Return a message when the inputs cannot give a meaningful NPSHa, else None."""
    if pressure_abs_kpa <= WATER_VAPOR_PRESSURE_KPA:
        return (f"Suction pressure {pressure_abs_kpa:.2f} kPa abs is at or below the vapour pressure "
                f"of water at 20 °C ({WATER_VAPOR_PRESSURE_KPA} kPa). The water would already be boiling; "
                "check the reading, units (absolute vs gauge) and sensor before assessing NPSH.")
    velocity = suction_velocity(flow_m3_h, diameter_mm)
    if velocity > MAX_PLAUSIBLE_SUCTION_VELOCITY_M_S:
        return (f"Velocity at the measurement point would be {velocity:.1f} m/s, above the "
                f"{MAX_PLAUSIBLE_SUCTION_VELOCITY_M_S:g} m/s plausibility limit. Check the internal diameter "
                "and flow. A smaller pipe does not add NPSH: for the same upstream conditions it lowers "
                "static pressure.")
    return None


def lowara_npshr(flow_m3_h):
    """Interpolate between catalog points within the demo's flow range."""
    for (flow_a, head_a), (flow_b, head_b) in zip(LOWARA_CURVE, LOWARA_CURVE[1:]):
        if flow_a <= flow_m3_h <= flow_b:
            fraction = (flow_m3_h - flow_a) / (flow_b - flow_a)
            return head_a + fraction * (head_b - head_a)
    raise ValueError("Flow is outside the digitized curve range.")


def available_npsh(pressure_abs_kpa, flow_m3_h, diameter_mm):
    """Estimate NPSHa from static pressure at the suction nozzle at the datum."""
    velocity_m_s = suction_velocity(flow_m3_h, diameter_mm)
    pressure_head = (pressure_abs_kpa - WATER_VAPOR_PRESSURE_KPA) * 1000
    return pressure_head / (WATER_DENSITY_KG_M3 * GRAVITY_M_S2) + velocity_m_s**2 / (
        2 * GRAVITY_M_S2
    )


def pressure_for_npsha(target_npsha_m, flow_m3_h, diameter_mm):
    """Absolute static pressure (kPa abs) at the datum that gives the target NPSHa."""
    velocity_head = suction_velocity(flow_m3_h, diameter_mm) ** 2 / (2 * GRAVITY_M_S2)
    return (target_npsha_m - velocity_head) * WATER_DENSITY_KG_M3 * GRAVITY_M_S2 / 1000 + WATER_VAPOR_PRESSURE_KPA


def straight_pipe_loss_kpa(flow_m3_h, diameter_mm, length_m, friction_factor):
    """Return the Darcy–Weisbach pressure loss for a straight pipe segment."""
    diameter_m = diameter_mm / 1000
    area_m2 = pi * diameter_m**2 / 4
    velocity_m_s = flow_m3_h / (3600 * area_m2)
    return friction_factor * (length_m / diameter_m) * WATER_DENSITY_KG_M3 * velocity_m_s**2 / 2000


def npsh_assessment(available, required, required_margin):
    """Compare raw NPSHr with an independently selected additive margin."""
    if not all(isfinite(v) for v in (available, required, required_margin)):
        raise ValueError("NPSH inputs must be finite.")
    if required < 0 or required_margin < 0:
        raise ValueError("NPSHr and required margin must be nonnegative.")
    actual_margin = available - required
    surplus = actual_margin - required_margin
    # Avoid a false deficit at a floating-point equality boundary.
    if isclose(actual_margin, 0.0, abs_tol=1e-9):
        actual_margin = 0.0
    if isclose(surplus, 0.0, abs_tol=1e-9):
        surplus = 0.0
    status = "CRITICAL" if actual_margin < 0 else "WARNING" if surplus < 0 else "SAFE"
    return actual_margin, surplus, status

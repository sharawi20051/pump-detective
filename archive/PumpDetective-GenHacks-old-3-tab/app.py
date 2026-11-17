"""Interactive pump diagnostics and suction-head demonstration."""

from math import pi

import streamlit as st

from pump_detective import CLEAN_FILTER_DROP_KPA, DESIGN_FLOW_LPS, diagnose_filter


SCENARIOS = {
    "Case A · Low downstream pressure": (110.0, 85.0),
    "Case B · Low downstream pressure": (90.0, 85.0),
    "Clean filter · Reference case": (110.0, 105.0),
}


# Approximate readings from the Lowara NSC 80-200/55 curve, p. 100, 1450 rpm.
# Each pair is (flow in m³/h, laboratory NPSH in m).
LOWARA_CURVE = ((40, 1.07), (60, 1.04), (80, 1.06), (100, 1.19), (120, 1.51), (140, 2.21))
CATALOG_ALLOWANCE_M = 0.5
WATER_VAPOR_PRESSURE_KPA = 2.339  # Water at 20 °C
WATER_DENSITY_KG_M3 = 998.2
GRAVITY_M_S2 = 9.80665


def lowara_npshr(flow_m3_h):
    """Interpolate between catalog points within the demo's flow range."""
    for (flow_a, head_a), (flow_b, head_b) in zip(LOWARA_CURVE, LOWARA_CURVE[1:]):
        if flow_a <= flow_m3_h <= flow_b:
            fraction = (flow_m3_h - flow_a) / (flow_b - flow_a)
            return head_a + fraction * (head_b - head_a)
    raise ValueError("Flow is outside the digitized curve range.")


def available_npsh(pressure_abs_kpa, flow_m3_h, diameter_mm):
    """Estimate NPSHa from static pressure at the suction nozzle at the datum."""
    area_m2 = pi * (diameter_mm / 1000) ** 2 / 4
    velocity_m_s = (flow_m3_h / 3600) / area_m2
    pressure_head = (pressure_abs_kpa - WATER_VAPOR_PRESSURE_KPA) * 1000
    return pressure_head / (WATER_DENSITY_KG_M3 * GRAVITY_M_S2) + velocity_m_s**2 / (
        2 * GRAVITY_M_S2
    )


def straight_pipe_loss_kpa(flow_m3_h, diameter_mm, length_m, friction_factor):
    """Return the Darcy–Weisbach pressure loss for a straight pipe segment."""
    diameter_m = diameter_mm / 1000
    area_m2 = pi * diameter_m**2 / 4
    velocity_m_s = flow_m3_h / (3600 * area_m2)
    return friction_factor * (length_m / diameter_m) * WATER_DENSITY_KG_M3 * velocity_m_s**2 / 2000


def hide_upstream_reading():
    st.session_state.show_upstream = False


def reset_repair_demo():
    st.session_state.repair_reading_visible = False
    st.session_state.simulate_cleaning = False


st.set_page_config(page_title="Pump Detective", layout="centered")
st.title("Pump Detective")
diagnostics, cavitation, repair = st.tabs(
    ["Filter diagnostics", "Cavitation Shield", "Repair simulation"]
)

with diagnostics:
    st.caption(f"CHWPP-01 · Simulated pressures · Fixed flow of {DESIGN_FLOW_LPS:g} L/s")

    scenario = st.selectbox("Choose a test case", SCENARIOS, on_change=hide_upstream_reading)
    upstream, downstream = SCENARIOS[scenario]
    show_upstream = st.toggle("Reveal upstream pressure", key="show_upstream")
    measured_upstream = upstream if show_upstream else None
    pressure_drop, suggestion = diagnose_filter(measured_upstream, downstream)

    before, after, difference = st.columns(3)
    before.metric(
        "Before the filter",
        f"{measured_upstream:g} kPa" if measured_upstream is not None else "Hidden",
    )
    after.metric("After the filter", f"{downstream:g} kPa")
    difference.metric("Pressure drop", f"{pressure_drop:g} kPa" if pressure_drop is not None else "—")

    st.subheader("Suggested check")
    st.info(suggestion)
    if pressure_drop is not None:
        st.write(
            f"Pressure drop: {measured_upstream:g} − {downstream:g} = {pressure_drop:g} kPa. "
            f"Clean-filter reference at this flow: {CLEAN_FILTER_DROP_KPA:g} kPa."
        )


with cavitation:
    st.subheader("Suction-head comparison")
    st.caption("Reference pump: Lowara NSC 80-200/55 at approximately 1450 rpm. Water at 20 °C.")
    st.write(
        "Set the simulated absolute static pressure at the pump suction nozzle. "
        "This demo assumes the pressure reading is at the pump's NPSH datum."
    )
    flow = st.slider("Flow (m³/h)", 40.0, 140.0, round(DESIGN_FLOW_LPS * 3.6, 1), 0.1)
    pressure_abs = st.slider("Absolute suction pressure (kPa)", 5.0, 200.0, 30.0, 0.1)
    diameter = st.number_input("Internal diameter at the measurement point (mm)", 40, 300, 100)
    st.caption("The default pressure and diameter are demonstration inputs.")

    available = available_npsh(pressure_abs, flow, diameter)
    required = lowara_npshr(flow)
    benchmark = required + CATALOG_ALLOWANCE_M
    margin = available - required

    col_a, col_r, col_margin = st.columns(3)
    col_a.metric("Available NPSH", f"{available:.2f} m")
    col_r.metric("Catalog NPSH (approx.)", f"{required:.2f} m")
    col_margin.metric("Margin over catalog", f"{margin:+.2f} m")

    st.write(f"Catalog NPSH + Xylem's 0.50 m allowance = {benchmark:.2f} m.")
    if available < required:
        st.warning("Available NPSH is below the approximate laboratory curve.")
    elif available < benchmark:
        st.warning("Available NPSH is below the catalog curve plus Xylem's allowance.")
    else:
        st.info("Available NPSH meets the catalog comparison for these simulated inputs.")

    st.caption(
        "Educational simulation. The curve points were read approximately from the graph. "
        "An installed pump requires its own curve, operating conditions, and margin review."
    )
    st.markdown(
        "[Xylem Lowara e-NSC catalog, page 100]"
        "(https://www.xylem.com/siteassets/brand/lowara/resources/technical-brochure/"
        "191002951_nsc-50hz_en.pdf#page=100)"
    )


with repair:
    st.subheader("Would cleaning the filter improve suction?")
    st.caption(
        "Simulated absolute pressures · Lowara reference curve · Water at 20 °C · "
        f"Fixed flow of {DESIGN_FLOW_LPS:g} L/s"
    )
    repair_case = st.selectbox(
        "Choose a low-pressure case",
        ("Scenario A", "Scenario B"),
        on_change=reset_repair_demo,
    )
    suction_kpa = 8.0
    upstream_kpa = 33.0 if repair_case == "Scenario A" else 13.0
    reveal = st.toggle("Reveal pressure before the filter", key="repair_reading_visible")
    measured = upstream_kpa if reveal else None
    drop, suggestion = diagnose_filter(measured, suction_kpa)

    inlet, outlet, loss = st.columns(3)
    inlet.metric("Before the filter", f"{measured:g} kPa abs" if reveal else "Hidden")
    outlet.metric("At pump suction", f"{suction_kpa:g} kPa abs")
    loss.metric("Filter pressure drop", f"{drop:g} kPa" if drop is not None else "—")
    st.info(suggestion)

    if reveal:
        flow = DESIGN_FLOW_LPS * 3.6
        nozzle_mm = 100
        before = available_npsh(suction_kpa, flow, nozzle_mm)
        benchmark = lowara_npshr(flow) + CATALOG_ALLOWANCE_M
        restored_suction = upstream_kpa - CLEAN_FILTER_DROP_KPA
        after_cleaning = available_npsh(restored_suction, flow, nozzle_mm)
        simulate_cleaning = st.checkbox("Simulate a clean filter", key="simulate_cleaning")
        if simulate_cleaning:
            initial, cleaned = st.columns(2)
            initial.metric("NPSH available before cleaning", f"{before:.2f} m")
            cleaned.metric("NPSH available with clean filter", f"{after_cleaning:.2f} m", f"{after_cleaning - before:+.2f} m")
            st.write(f"Catalog comparison with allowance: **{benchmark:.2f} m**.")
            if after_cleaning >= benchmark:
                st.success("The simulated cleaning raises suction head above the catalog comparison.")
            else:
                st.warning("The clean filter still leaves low suction head. Check conditions upstream.")
            st.caption(
                "The model holds flow and upstream pressure fixed. It assumes a 100 mm internal "
                "diameter and negligible pressure loss between the filter outlet and pump suction. "
                "Cleaning sets the filter loss to the demo's 5 kPa reference."
            )

        st.subheader("Compare suction-side changes")
        st.caption(
            "The pipe segment is before the filter. Assumed baseline: 80 mm internal diameter, "
            "12 m straight length, and Darcy friction factor 0.025. The 100 mm pump inlet stays fixed."
        )
        new_diameter = st.slider("Proposed pipe internal diameter (mm)", 80, 160, 100, 5)
        old_loss = straight_pipe_loss_kpa(flow, 80, 12, 0.025)
        new_loss = straight_pipe_loss_kpa(flow, new_diameter, 12, 0.025)
        after_resize = available_npsh(suction_kpa + old_loss - new_loss, flow, nozzle_mm)
        pressure_needed = max(0.0, benchmark - before) * WATER_DENSITY_KG_M3 * GRAVITY_M_S2 / 1000

        st.write(f"Straight-pipe pressure loss: **{old_loss:.2f} → {new_loss:.2f} kPa**.")
        st.table(
            [
                {
                    "Change": label,
                    "Available NPSH": f"{head:.2f} m",
                    "Margin vs. catalog + allowance": f"{head - benchmark:+.2f} m",
                }
                for label, head in (
                    ("Current condition", before),
                    ("Clean the filter", after_cleaning),
                    (f"Resize pipe to {new_diameter} mm", after_resize),
                    (f"Add {pressure_needed:.2f} kPa before the pipe", max(before, benchmark)),
                )
            ]
        )
        st.caption(
            "Each change starts from the same baseline. The comparison holds flow and pipe-inlet "
            "velocity head constant (the changed segment is between fixed stations). It models "
            "straight-pipe friction only and excludes fitting and transition losses. The pressure "
            "increase is the modeled amount needed to reach the catalog comparison."
        )

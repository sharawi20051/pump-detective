"""Run a fixed-flow pump suction diagnostic demo with simulated pressures.

All pressures in this module are absolute pressures in kPa (kPa abs).
"""

DESIGN_FLOW_LPS = 21.2
CLEAN_FILTER_DROP_KPA = 5.0
# Expected suction pressure (after the filter) in normal operation for the demo plant, kPa abs.
NORMAL_SUCTION_KPA_ABS = 105.0
# Illustrative tolerance for this demo, not a field alarm threshold.
TOLERANCE_KPA = 2.0
ATMOSPHERIC_KPA_ABS = 101.325


def diagnose_filter(pressure_before_kpa, pressure_after_kpa,
                    clean_drop_kpa=CLEAN_FILTER_DROP_KPA,
                    tolerance_kpa=TOLERANCE_KPA,
                    normal_after_kpa=NORMAL_SUCTION_KPA_ABS):
    """Return the pressure drop and a suggested check at the design flow.

    Both readings are absolute pressures (kPa abs) taken at the same flow.
    ``normal_after_kpa`` is the expected pressure after the strainer in normal
    operation; it is only used once the strainer drop matches the clean reference.
    """
    if pressure_before_kpa is None:
        return None, "Measure the pressure upstream of the strainer."

    pressure_drop_kpa = pressure_before_kpa - pressure_after_kpa

    if pressure_drop_kpa < 0:
        return pressure_drop_kpa, "Verify the pressure readings and flow direction."
    if pressure_drop_kpa > clean_drop_kpa + tolerance_kpa:
        return pressure_drop_kpa, "Check the strainer for restriction first."
    if pressure_drop_kpa < clean_drop_kpa - tolerance_kpa:
        return pressure_drop_kpa, "Verify the flow and the clean-strainer reference."
    if pressure_after_kpa < normal_after_kpa - tolerance_kpa:
        return pressure_drop_kpa, "Check pressure conditions upstream of the strainer."
    return pressure_drop_kpa, "Strainer pressure drop matches the clean reference."


def run_demo():
    """Show what the diagnosis does before and after the extra measurement."""
    cases = [
        ("Clean strainer", 110.0, 105.0),
        ("Partially clogged strainer", 110.0, 85.0),
        ("Low upstream pressure", 90.0, 85.0),
        ("Missing upstream reading", None, 85.0),
    ]

    print(f"Pump Detective | Simulated absolute pressures at {DESIGN_FLOW_LPS} L/s")
    for label, pressure_before, pressure_after in cases:
        pressure_drop, suggestion = diagnose_filter(pressure_before, pressure_after)
        upstream = "missing" if pressure_before is None else f"{pressure_before:g} kPa abs"
        print(f"\n{label}: upstream {upstream}, downstream {pressure_after:g} kPa abs")
        if pressure_drop is not None:
            print(f"Pressure drop: {pressure_drop:g} kPa")
        print(suggestion)


if __name__ == "__main__":
    run_demo()

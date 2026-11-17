"""Run a fixed-flow pump suction diagnostic demo with simulated pressures."""

DESIGN_FLOW_LPS = 21.2
CLEAN_FILTER_DROP_KPA = 5.0
REFERENCE_DOWNSTREAM_KPA = 105.0
# Illustrative tolerance for this demo, not a field alarm threshold.
TOLERANCE_KPA = 2.0


def diagnose_filter(pressure_before_kpa, pressure_after_kpa):
    """Return the pressure drop and a suggested check at the design flow."""
    if pressure_before_kpa is None:
        return None, "Measure the pressure upstream of the filter."

    pressure_drop_kpa = pressure_before_kpa - pressure_after_kpa

    if pressure_drop_kpa < 0:
        return pressure_drop_kpa, "Verify the pressure readings and flow direction."
    if pressure_drop_kpa > CLEAN_FILTER_DROP_KPA + TOLERANCE_KPA:
        return pressure_drop_kpa, "Check the filter for restriction first."
    if pressure_drop_kpa < CLEAN_FILTER_DROP_KPA - TOLERANCE_KPA:
        return pressure_drop_kpa, "Verify the flow and the clean-filter reference."
    if pressure_after_kpa < REFERENCE_DOWNSTREAM_KPA - TOLERANCE_KPA:
        return pressure_drop_kpa, "Check pressure conditions upstream of the filter."
    return pressure_drop_kpa, "Filter pressure drop matches the clean reference."


def run_demo():
    """Show what the diagnosis does before and after the extra measurement."""
    cases = [
        ("Clean filter", 110.0, 105.0),
        ("Partially clogged filter", 110.0, 85.0),
        ("Low upstream pressure", 90.0, 85.0),
        ("Missing upstream reading", None, 85.0),
    ]

    print(f"Pump Detective | Simulated pressures at {DESIGN_FLOW_LPS} L/s")
    for label, pressure_before, pressure_after in cases:
        pressure_drop, suggestion = diagnose_filter(pressure_before, pressure_after)
        upstream = "missing" if pressure_before is None else f"{pressure_before:g} kPa"
        print(f"\n{label}: upstream {upstream}, downstream {pressure_after:g} kPa")
        if pressure_drop is not None:
            print(f"Pressure drop: {pressure_drop:g} kPa")
        print(suggestion)


if __name__ == "__main__":
    run_demo()

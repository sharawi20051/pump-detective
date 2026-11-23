"""Diagrams and charts for the Engineering tools page.

``suction_line_svg`` draws the suction line (upstream → gauge → strainer → gauge →
pump) with each part coloured by what the readings say. The Altair helpers draw
the NPSH curve, the repair comparison and the affinity laws. No engineering is
done here: every number is passed in, already calculated.
"""

from html import escape

import altair as alt
import pandas as pd

GREEN, AMBER, RED, GREY, BLUE, NAVY = "#12805C", "#B54708", "#B42318", "#98A2B3", "#0B5CAD", "#0A2540"
STATUS_COLOUR = {"SAFE": GREEN, "WARNING": AMBER, "CRITICAL": RED, "NOT ASSESSED": GREY}

# verdict → (strainer colour, upstream colour, strainer label)
VERDICTS = {
    "unknown": (GREY, GREY, "Δp unknown"),
    "restricted": (RED, GREEN, "Restricted"),
    "low_drop": (AMBER, GREY, "Below clean reference"),
    "upstream": (GREEN, AMBER, "Clean"),
    "ok": (GREEN, GREEN, "Clean"),
    "invalid": (GREY, GREY, "Check readings"),
}


def _gauge(x, y, value, label, colour):
    return (f'<circle cx="{x}" cy="{y}" r="27" fill="#fff" stroke="{colour}" stroke-width="3"/>'
            f'<line x1="{x}" y1="{y + 27}" x2="{x}" y2="{y + 47}" stroke="#667085" stroke-width="3"/>'
            f'<text x="{x}" y="{y - 3}" text-anchor="middle" font-size="13" font-weight="800" fill="{NAVY}">{escape(value)}</text>'
            f'<text x="{x}" y="{y + 12}" text-anchor="middle" font-size="9" fill="#667085">kPa abs</text>'
            f'<text x="{x}" y="{y - 36}" text-anchor="middle" font-size="11" font-weight="700" fill="#475467">{escape(label)}</text>')


def suction_line_svg(before, after, drop, verdict, atmospheric=101.325, note=""):
    """Schematic of the suction line. ``before`` may be None (reading hidden or missing)."""
    strainer_c, upstream_c, strainer_label = VERDICTS.get(verdict, VERDICTS["unknown"])
    after_c = AMBER if after < atmospheric else GREEN
    pipe_y = 126
    mesh = "".join(f'<line x1="{352 + i * 8}" y1="{pipe_y - 22}" x2="{352 + i * 8}" y2="{pipe_y + 22}" '
                   f'stroke="{strainer_c}" stroke-width="1.5" opacity="0.55"/>' for i in range(7))
    drop_txt = "?" if drop is None else f"{drop:g} kPa"
    svg = f'''<svg viewBox="0 0 780 224" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:780px;
font-family:'Source Sans Pro','Segoe UI',Arial,sans-serif">
<rect x="0" y="0" width="780" height="224" rx="14" fill="#fff" stroke="#E3E8EF"/>
<text x="24" y="28" font-size="12" font-weight="800" fill="#0E9384" letter-spacing="1">SUCTION LINE · FLOW →</text>
<rect x="24" y="{pipe_y - 34}" width="70" height="68" rx="8" fill="{upstream_c}" opacity="0.14" stroke="{upstream_c}"/>
<text x="59" y="{pipe_y - 4}" text-anchor="middle" font-size="11" font-weight="700" fill="{NAVY}">System</text>
<text x="59" y="{pipe_y + 11}" text-anchor="middle" font-size="9" fill="#475467">fill / tank</text>
<rect x="94" y="{pipe_y - 10}" width="250" height="20" fill="#DCEBFA" stroke="{upstream_c}" stroke-width="2"/>
<rect x="416" y="{pipe_y - 10}" width="220" height="20" fill="#DCEBFA" stroke="#9DB7D3" stroke-width="2"/>
<path d="M150 {pipe_y} l14 0 m-5 -5 l5 5 l-5 5" stroke="{BLUE}" stroke-width="2" fill="none"/>
<path d="M470 {pipe_y} l14 0 m-5 -5 l5 5 l-5 5" stroke="{BLUE}" stroke-width="2" fill="none"/>
{_gauge(230, pipe_y - 66, "?" if before is None else f"{before:g}", "Before strainer", upstream_c if before is not None else GREY)}
<rect x="344" y="{pipe_y - 28}" width="72" height="56" rx="10" fill="{strainer_c}" opacity="0.16" stroke="{strainer_c}" stroke-width="3"/>
{mesh}
<text x="380" y="{pipe_y + 50}" text-anchor="middle" font-size="12" font-weight="800" fill="{strainer_c}">Strainer · {escape(strainer_label)}</text>
<text x="380" y="{pipe_y + 66}" text-anchor="middle" font-size="12" fill="{NAVY}">Δp = {escape(drop_txt)}</text>
{_gauge(540, pipe_y - 66, f"{after:g}", "Pump suction", after_c)}
<circle cx="690" cy="{pipe_y}" r="42" fill="#EAF4FF" stroke="{NAVY}" stroke-width="3"/>
<path d="M690 {pipe_y} l0 -30 a30 30 0 0 1 26 15 z M690 {pipe_y} l26 15 a30 30 0 0 1 -26 15 z M690 {pipe_y} l-26 15 a30 30 0 0 1 0 -30 z" fill="{BLUE}" opacity="0.55"/>
<text x="690" y="{pipe_y + 60}" text-anchor="middle" font-size="11" font-weight="700" fill="{NAVY}">Pump</text>
{f'<text x="24" y="212" font-size="11" fill="#475467">{escape(note)}</text>' if note else ""}
</svg>'''
    return " ".join(svg.split())  # one line, so markdown does not treat it as text


def npsh_curve_chart(curve, margin, allowance, flow_m3h, npsha, status, height=300):
    """Lowara NPSHr curve, NPSHr + margin, the catalogue reference, and the operating point."""
    rows = []
    for q, h in curve:
        rows += [{"Flow (m³/h)": q, "Head (m)": h, "Line": "NPSHr (pump needs)"},
                 {"Flow (m³/h)": q, "Head (m)": h + margin, "Line": f"NPSHr + {margin:.2f} m margin (target)"},
                 {"Flow (m³/h)": q, "Head (m)": h + allowance, "Line": f"NPSHr + {allowance:.2f} m catalogue ref."}]
    lines = pd.DataFrame(rows)
    top = max(float(lines["Head (m)"].max()), npsha if npsha is not None else 0) * 1.15
    scale = alt.Scale(domain=[0, top])
    domain = list(dict.fromkeys(lines["Line"]))
    chart = alt.Chart(lines).mark_line(strokeWidth=2.5).encode(
        x=alt.X("Flow (m³/h):Q", scale=alt.Scale(domain=[curve[0][0], curve[-1][0]])),
        y=alt.Y("Head (m):Q", scale=scale, title="NPSH (m)"),
        color=alt.Color("Line:N", scale=alt.Scale(domain=domain, range=[RED, AMBER, GREY]),
                        legend=alt.Legend(orient="bottom", title=None, columns=1, labelLimit=0, labelFontSize=12)),
        strokeDash=alt.StrokeDash("Line:N", scale=alt.Scale(domain=domain, range=[[1, 0], [6, 4], [2, 3]]), legend=None),
    )
    layers = [chart, alt.Chart(pd.DataFrame({"q": [flow_m3h]})).mark_rule(color="#98A2B3", strokeDash=[2, 2]).encode(x="q:Q")]
    if npsha is not None:
        point = pd.DataFrame({"Flow (m³/h)": [flow_m3h], "Head (m)": [min(npsha, top * 0.98)],
                              "label": [f"Your pump: NPSHa {npsha:.2f} m · {status}"]})
        colour = STATUS_COLOUR.get(status, BLUE)
        layers += [
            alt.Chart(point).mark_point(size=420, filled=True, color=colour, opacity=0.9).encode(
                x="Flow (m³/h):Q", y=alt.Y("Head (m):Q", scale=scale), tooltip=["label"]),
            alt.Chart(point).mark_text(align="left", dx=14, dy=-12, fontSize=13, fontWeight="bold", color=colour).encode(
                x="Flow (m³/h):Q", y=alt.Y("Head (m):Q", scale=scale), text="label"),
        ]
    return alt.layer(*layers).properties(height=height)


def options_chart(options, npshr, target, height=220):
    """Horizontal bars: NPSHa for each repair option, with NPSHr and the target as lines."""
    df = pd.DataFrame(options, columns=["Option", "NPSHa (m)", "Status"])
    scale = alt.Scale(domain=[0, max(df["NPSHa (m)"].max(), target) * 1.6])  # room for the value labels
    bars = alt.Chart(df).mark_bar(cornerRadiusEnd=6, height=26).encode(
        y=alt.Y("Option:N", sort=None, title=None, axis=alt.Axis(labelLimit=260, labelFontSize=12)),
        x=alt.X("NPSHa (m):Q", scale=scale, title="NPSH available (m)"),
        color=alt.Color("Status:N", scale=alt.Scale(domain=list(STATUS_COLOUR), range=list(STATUS_COLOUR.values())),
                        legend=None),
        tooltip=["Option", alt.Tooltip("NPSHa (m):Q", format=".2f"), "Status"],
    )
    labels = alt.Chart(df).mark_text(align="left", dx=6, fontSize=12, fontWeight="bold").encode(
        y=alt.Y("Option:N", sort=None), x=alt.X("NPSHa (m):Q", scale=scale),
        text=alt.Text("label:N"), color=alt.value(NAVY),
    ).transform_calculate(label="format(datum['NPSHa (m)'], '.2f') + ' m · ' + datum.Status")
    rules = pd.DataFrame({"x": [npshr, target], "Line": ["NPSHr (cavitation)", "Target (NPSHr + margin)"]})
    rule = alt.Chart(rules).mark_rule(strokeWidth=2, strokeDash=[5, 3]).encode(
        x=alt.X("x:Q", scale=scale),
        color=alt.Color("Line:N", scale=alt.Scale(domain=list(rules["Line"]), range=[RED, AMBER]),
                        legend=alt.Legend(orient="bottom", title=None)),
    )
    return alt.layer(bars, labels, rule).resolve_scale(color="independent").properties(height=height)


def affinity_chart(speed_pct, height=260):
    """Affinity laws: flow ∝ n, head ∝ n², ideal shaft power ∝ n³, with the current speed marked."""
    rows = []
    for n in range(10, 101, 2):
        r = n / 100
        rows += [{"Speed (%)": n, "% of full speed value": 100 * r, "Quantity": "Flow ∝ n"},
                 {"Speed (%)": n, "% of full speed value": 100 * r ** 2, "Quantity": "Head ∝ n²"},
                 {"Speed (%)": n, "% of full speed value": 100 * r ** 3, "Quantity": "Shaft power ∝ n³"}]
    df = pd.DataFrame(rows)
    domain = ["Flow ∝ n", "Head ∝ n²", "Shaft power ∝ n³"]
    lines = alt.Chart(df).mark_line(strokeWidth=2.5).encode(
        x=alt.X("Speed (%):Q", title="Pump speed (% of reference)"),
        y=alt.Y("% of full speed value:Q", title="% of the value at reference speed"),
        color=alt.Color("Quantity:N", scale=alt.Scale(domain=domain, range=[BLUE, "#0E9384", AMBER]),
                        legend=alt.Legend(orient="bottom", title=None)),
    )
    r = speed_pct / 100
    here = pd.DataFrame({"Speed (%)": [speed_pct] * 3, "% of full speed value": [100 * r, 100 * r ** 2, 100 * r ** 3],
                         "Quantity": domain})
    points = alt.Chart(here).mark_point(size=120, filled=True).encode(
        x="Speed (%):Q", y="% of full speed value:Q",
        color=alt.Color("Quantity:N", scale=alt.Scale(domain=domain, range=[BLUE, "#0E9384", AMBER]), legend=None),
        tooltip=["Quantity", alt.Tooltip("% of full speed value:Q", format=".1f")],
    )
    rule = alt.Chart(pd.DataFrame({"x": [speed_pct]})).mark_rule(color="#667085", strokeDash=[3, 3]).encode(x="x:Q")
    return alt.layer(lines, rule, points).properties(height=height)

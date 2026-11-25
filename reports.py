"""PDF exports for Pump Detective (reportlab).

All downloads a person reads (forecast report, work order, answers, tool reports)
are PDF. Text uses the bundled DejaVu Sans font so Δ, ±, ³, → and similar symbols
print correctly. Every function returns the PDF as bytes for st.download_button.
"""

import os
from datetime import datetime
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.shapes import Drawing, Line, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle)


FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
NAVY, BLUE, TEAL = colors.HexColor("#0A2540"), colors.HexColor("#0B5CAD"), colors.HexColor("#0E9384")
GREY, LINE = colors.HexColor("#475467"), colors.HexColor("#E3E8EF")
STATUS = {
    "SAFE": "#12805C", "NONE": "#12805C", "RESTORED": "#12805C",
    "WARNING": "#B54708", "HIGH": "#B54708", "IMPROVED, NOT CLEAN": "#B54708",
    "CRITICAL": "#B42318", "URGENT": "#B42318", "NOT EFFECTIVE": "#B42318", "SUSPICIOUSLY LOW": "#B42318",
    "PLANNED": "#0B5CAD", "NOT ASSESSED": "#667085",
}

_fonts_ready = False


def _fonts():
    global _fonts_ready
    if not _fonts_ready:
        pdfmetrics.registerFont(TTFont("DejaVu", os.path.join(FONT_DIR, "DejaVuSans.ttf")))
        pdfmetrics.registerFont(TTFont("DejaVu-Bold", os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")))
        pdfmetrics.registerFontFamily("DejaVu", normal="DejaVu", bold="DejaVu-Bold",
                                      italic="DejaVu", boldItalic="DejaVu-Bold")
        _fonts_ready = True


def _styles():
    _fonts()
    base = dict(fontName="DejaVu", fontSize=9.5, leading=13, textColor=colors.HexColor("#1F2A37"), alignment=TA_LEFT)
    return {
        "title": ParagraphStyle("title", **{**base, "fontName": "DejaVu-Bold", "fontSize": 18, "leading": 22,
                                            "textColor": NAVY}),
        "sub": ParagraphStyle("sub", **{**base, "fontSize": 9, "textColor": GREY}),
        "h": ParagraphStyle("h", **{**base, "fontName": "DejaVu-Bold", "fontSize": 12, "leading": 16,
                                    "textColor": NAVY, "spaceBefore": 10, "spaceAfter": 4}),
        "body": ParagraphStyle("body", **base),
        "small": ParagraphStyle("small", **{**base, "fontSize": 8, "leading": 10.5, "textColor": GREY}),
        "mono": ParagraphStyle("mono", **{**base, "fontSize": 9, "leading": 12.5}),
        "cell": ParagraphStyle("cell", **{**base, "fontSize": 8.5, "leading": 11}),
        "cellb": ParagraphStyle("cellb", **{**base, "fontName": "DejaVu-Bold", "fontSize": 8.5, "leading": 11}),
        "cardvalue": ParagraphStyle("cardvalue", **{**base, "fontSize": 12, "leading": 16}),
    }


def _p(text, style):
    return Paragraph(escape(str(text)).replace("\n", "<br/>"), style)


TEXT_WIDTH = A4[0] - 30 * mm


def _text(text, style):
    """Multi-line text as flowables: one paragraph per line, blank lines as small gaps."""
    flowables = []
    for line in str(text).split("\n"):
        if not line.strip():
            flowables.append(Spacer(1, style.leading * 0.6))
        else:
            flowables.append(Paragraph(escape(line), style))
    return flowables


def _header_footer(title):
    def draw(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(NAVY)
        canvas.rect(0, A4[1] - 9 * mm, A4[0], 9 * mm, stroke=0, fill=1)
        canvas.setFillColor(colors.white)
        canvas.setFont("DejaVu-Bold", 9)
        canvas.drawString(15 * mm, A4[1] - 6 * mm, "Pump Detective · predictive strainer care")
        canvas.setFont("DejaVu", 8)
        canvas.drawRightString(A4[0] - 15 * mm, A4[1] - 6 * mm, title)
        canvas.setFillColor(GREY)
        canvas.drawString(15 * mm, 9 * mm, "Educational prototype · data and results must be checked by a qualified engineer")
        canvas.drawRightString(A4[0] - 15 * mm, 9 * mm, f"Page {doc.page}")
        canvas.restoreState()
    return draw


def _build(title, story):
    _fonts()
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm,
                            topMargin=16 * mm, bottomMargin=16 * mm, title=title, author="Pump Detective")
    doc.build(story, onFirstPage=_header_footer(title), onLaterPages=_header_footer(title))
    return buffer.getvalue()


def _status_row(cards, s):
    """Coloured status boxes: list of (label, value, sub, key)."""
    cells = []
    for label, value, sub, key in cards:
        colour = STATUS.get(key, "#0B5CAD")
        cells.append([
            Paragraph(f'<font size="7" color="#667085">{escape(label.upper())}</font>', s["cell"]),
            Paragraph(f'<font name="DejaVu-Bold" size="12" color="{colour}">{escape(value)}</font>', s["cardvalue"]),
            Paragraph(f'<font size="7.5" color="#475467">{escape(sub)}</font>', s["cell"]),
        ])
    width = (A4[0] - 30 * mm) / max(len(cells), 1)
    table = Table([cells], colWidths=[width] * len(cells))
    style = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOX", (0, 0), (-1, -1), 0.5, LINE),
             ("INNERGRID", (0, 0), (-1, -1), 0.5, LINE), ("BACKGROUND", (0, 0), (-1, -1), colors.white),
             ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]
    for i, (*_, key) in enumerate(cards):
        style.append(("LINEBEFORE", (i, 0), (i, 0), 3, colors.HexColor(STATUS.get(key, "#0B5CAD"))))
    table.setStyle(TableStyle(style))
    return table


def _grid(rows, s, header=True, widths=None):
    data = [[_p(c, s["cellb"] if header and r == 0 else s["cell"]) for c in row] for r, row in enumerate(rows)]
    table = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style = [("GRID", (0, 0), (-1, -1), 0.4, LINE), ("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    if header:
        style.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EEF5")))
    table.setStyle(TableStyle(style))
    return table


def _trend_chart(daily, forecast, limits):
    """Daily Δp* history and forecast, with horizontal limit lines. ``daily``/``forecast`` are (day, kPa) lists."""
    width, height = A4[0] - 30 * mm, 62 * mm
    drawing = Drawing(width, height)
    plot = LinePlot()
    plot.x, plot.y, plot.width, plot.height = 32, 22, width - 44, height - 34
    series = [s for s in (daily, forecast) if s]
    data_top = max(y for s in series for _, y in s)
    # Scale to the data; show a limit only if it is within reach (as the app's chart does).
    shown = [(name, v) for name, v in limits if 0 < v <= 3 * data_top]
    top = max([data_top] + [v for _, v in shown]) * 1.1
    xs = [x for s in series for x, _ in s]
    plot.data = series
    plot.lines[0].strokeColor, plot.lines[0].strokeWidth = BLUE, 1.4
    if len(series) > 1:
        plot.lines[1].strokeColor, plot.lines[1].strokeWidth = colors.HexColor("#E07B00"), 1.4
        plot.lines[1].strokeDashArray = [4, 3]
    plot.xValueAxis.valueMin, plot.xValueAxis.valueMax = min(xs), max(xs)
    plot.yValueAxis.valueMin, plot.yValueAxis.valueMax = 0, top
    for axis in (plot.xValueAxis, plot.yValueAxis):
        axis.labels.fontName, axis.labels.fontSize = "DejaVu", 7
        axis.strokeColor = GREY
    plot.yValueAxis.gridStrokeColor, plot.yValueAxis.visibleGrid = LINE, True
    drawing.add(plot)
    palette = ["#6B7280", "#D4A017", "#C62828"]
    for (name, value), colour in zip(limits, palette):
        if (name, value) not in shown:
            continue
        y = plot.y + plot.height * value / plot.yValueAxis.valueMax
        drawing.add(Line(plot.x, y, plot.x + plot.width, y, strokeColor=colors.HexColor(colour), strokeWidth=0.8,
                         strokeDashArray=[2, 2]))
        drawing.add(String(plot.x + plot.width - 2, y + 2, name, fontName="DejaVu", fontSize=6.5,
                           fillColor=colors.HexColor(colour), textAnchor="end"))
    hidden = [name for name, v in limits if v > 3 * data_top]
    caption = "Strainer Δp* (kPa) · blue: daily history" + (" · orange: forecast" if forecast else "")
    if hidden:
        caption += f" · {', '.join(hidden)} far above this range (not drawn)"
    drawing.add(String(plot.x, height - 8, caption, fontName="DejaVu", fontSize=7.5, fillColor=GREY))
    drawing.add(String(plot.x + plot.width, 4, "day of log", fontName="DejaVu", fontSize=7, fillColor=GREY,
                       textAnchor="end"))
    return drawing


def forecast_report_pdf(summary, findings, cards, chart, work_order=None):
    """Full forecast report. ``cards`` = status cards (label, value, sub, key); ``chart`` = (daily, forecast, limits)."""
    s = _styles()
    reco = summary["recommendation"]
    story = [
        _p("Strainer forecast report", s["title"]),
        _p(f"{summary['asset']}\n{summary['data_origin']} · case: {summary['scenario']} · as of {summary['today']} · "
           f"generated {datetime.now():%Y-%m-%d %H:%M}", s["sub"]),
        Spacer(1, 8), _status_row([c[:4] for c in cards], s), Spacer(1, 8),
        _p("Recommendation", s["h"]),
        _p(f"{reco['action']} — priority {reco['priority']}"
           + (f", complete by {reco['complete_by']}" if reco["complete_by"] else "") + ".", s["body"]),
    ]
    if reco.get("driver"):
        story.append(_p(f"Driver: {reco['driver']}.", s["small"]))
    story += [_p("History and forecast", s["h"]), _trend_chart(*chart)]
    story += [_p("Forecast to each limit", s["h"]), _grid(
        [["Threshold", "Δp* limit (kPa)", "Days (central)", "Earliest date"]]
        + [[r["threshold"], f"{r['dp_limit_kpa']:.1f}",
            "already reached" if r["days_central"] == 0 else "> 180" if r["days_central"] is None else f"{r['days_central']:.0f}",
            r["earliest_date"] or "—"] for r in summary["thresholds"]], s, widths=[78 * mm, 30 * mm, 30 * mm, 42 * mm])]
    bt = summary["backtest"]
    story += [_p("Key figures", s["h"]), _grid([
        ["Quantity", "Value"],
        ["Strainer Δp* now (flow-normalised)", f"{summary['normalised_dp_now_kpa']} kPa (clean {summary['clean_strainer_dp_kpa']} kPa)"],
        ["Fouling rate (95 % range)", f"{summary['fouling_rate_percent_per_day']} %/day "
                                      f"({summary['fouling_rate_95pct_range_percent_per_day'][0]} to "
                                      f"{summary['fouling_rate_95pct_range_percent_per_day'][1]})"],
        ["NPSH now at design flow", f"{summary['npsh_status_now']} · NPSHa {summary['npsha_now_m']} m · NPSHr "
                                    f"{summary['npshr_m']} m · margin {summary['engineer_required_margin_m']:.2f} m"],
        ["Pressure before the strainer", f"{summary['pressure_before_strainer_kpa_abs']} kPa abs"],
        ["Backtest", "step change too recent to judge" if bt["step_change_too_recent_for_past_forecast"] else
         f"{bt['days_hidden']} days hidden: {bt['error_on_last_hidden_day_pct']:+.1f} % on the last day, "
         f"mean absolute error {bt['mean_absolute_error_pct']} %"],
        ["Trend fit", f"{summary['trend_fit_days']} daily medians from {summary['trend_fit_start']}"],
    ], s, widths=[62 * mm, 118 * mm])]
    if summary["events"]:
        story += [_p("Events detected in the sensor log", s["h"]),
                  _grid([["When", "Type", "Evidence"]] + [[e["date"], e["type"], e["evidence"]] for e in summary["events"]],
                        s, widths=[26 * mm, 58 * mm, 96 * mm])]
    ver = summary.get("post_maintenance_verification")
    if ver:
        story += [_p("Post-maintenance check", s["h"]), _status_row([(
            "Strainer verdict", ver["strainer_verdict"], f"Δp* {ver['normalised_dp_after_kpa']} kPa after cleaning",
            ver["strainer_verdict"]), ("NPSH after cleaning", ver["npsh_status_after"],
            f"NPSHa {ver['npsha_after_m']} m", ver["npsh_status_after"])], s),
            Spacer(1, 4), _p(f"{ver['message']} Next: {ver['next_check']}", s["body"])]
    story += [_p("Evidence and next checks", s["h"])]
    for item in findings:
        story.append(KeepTogether([_p(item["Finding"], s["cellb"]), _p(item["Evidence"], s["body"]),
                                   _p("Next check: " + item["Next check"], s["small"]), Spacer(1, 5)]))
    if work_order:
        story += [_p("Work order", s["h"])] + _text(work_order, s["mono"])
    story += [Spacer(1, 8), _p("Assumptions: " + summary["uncertainty_note"] + " Water at 20 °C; absolute suction "
                               "pressure at the NPSH datum; Lowara reference curve; no overall pump-health verdict.",
                               s["small"])]
    return _build("Strainer forecast report", story)


def text_pdf(title, subtitle, body, note=None, extra_rows=None):
    """A simple document: title, subtitle, optional key/value table, then the body text (line breaks kept)."""
    s = _styles()
    story = [_p(title, s["title"])] + _text(f"{subtitle} · generated {datetime.now():%Y-%m-%d %H:%M}", s["sub"])
    story.append(Spacer(1, 8))
    if extra_rows:
        story += [_grid([["Item", "Value"]] + [list(r) for r in extra_rows], s, widths=[62 * mm, 118 * mm]), Spacer(1, 8)]
    story += _text(body, s["mono"])
    if note:
        story += [Spacer(1, 10), _p(note, s["small"])]
    return _build(title, story)


def sensor_data_pdf(summary, info_rows, daily_rows, chart):
    """Readable sensor-data report: what the log contains, the chart, and one row per day."""
    s = _styles()
    story = [
        _p("Sensor data report", s["title"]),
        _p(f"{summary['asset']}\n{summary['data_origin']} · case: {summary['scenario']} · generated "
           f"{datetime.now():%Y-%m-%d %H:%M}", s["sub"]),
        _p("About this log", s["h"]),
        _grid([["Item", "Value"]] + [list(r) for r in info_rows], s, widths=[62 * mm, 118 * mm]),
        _p("Strainer pressure drop, day by day", s["h"]),
        _trend_chart(*chart),
        _p("Daily values", s["h"]),
        _p("Δp is the measured drop across the strainer; Δp* is the same drop corrected to design flow, which is "
           "what the forecast trends. Flagged readings are excluded as sensor glitches.", s["small"]),
        Spacer(1, 4),
        _grid([["Date", "Mean flow (L/s)", "Median Δp (kPa)", "Daily Δp* (kPa)", "Hours used", "Flagged", "Event"]]
              + daily_rows, s, widths=[26 * mm, 24 * mm, 25 * mm, 25 * mm, 20 * mm, 18 * mm, 42 * mm]),
        Spacer(1, 8),
        _p("The raw hourly numbers are available as a CSV file (for Excel or re-upload) under 'Raw data for "
           "engineers' in the app.", s["small"]),
    ]
    return _build("Sensor data report", story)


def tool_pdf(title, question, intro, cards, sections, note=None):
    """Report for one engineering tool.

    ``cards``: status boxes (label, value, sub, key). ``sections``: list of (heading, content) where content is
    text or a table given as a list of rows whose first row is the header.
    """
    s = _styles()
    story = [_p(title, s["title"]), _p(question, s["h"]),
             _p(f"{intro} · generated {datetime.now():%Y-%m-%d %H:%M}", s["sub"]), Spacer(1, 8)]
    if cards:
        story += [_status_row([c[:4] for c in cards], s), Spacer(1, 6)]
    for heading, content in sections:
        story.append(_p(heading, s["h"]))
        if isinstance(content, list):
            columns = len(content[0])
            story.append(_grid(content, s, widths=[TEXT_WIDTH / columns] * columns))
        else:
            story += _text(content, s["body"])
    if note:
        story += [Spacer(1, 10), _p(note, s["small"])]
    return _build(title, story)

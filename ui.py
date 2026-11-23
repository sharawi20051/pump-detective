"""Presentation helpers for Pump Detective: page style, header, status cards, section titles.

Kept apart from app.py so the engineering code stays readable. Everything here is
HTML/CSS rendered with st.markdown; any text that can come from a user (an uploaded
file name, for example) is escaped before it is placed in HTML.
"""

from html import escape

import streamlit as st

NAVY, BLUE, TEAL = "#0A2540", "#0B5CAD", "#0E9384"
STATUS_COLOURS = {
    "SAFE": "#12805C", "WARNING": "#B54708", "CRITICAL": "#B42318", "NOT ASSESSED": "#667085",
    "URGENT": "#B42318", "HIGH": "#B54708", "PLANNED": BLUE, "NONE": "#12805C",
    "RESTORED": "#12805C", "IMPROVED, NOT CLEAN": "#B54708", "NOT EFFECTIVE": "#B42318",
    "SUSPICIOUSLY LOW": "#B42318",
}

CSS = f"""
<style>
.block-container {{max-width: 1180px; padding-top: 1.6rem; padding-bottom: 4rem;}}
h1, h2, h3 {{color: {NAVY}; letter-spacing: -0.01em;}}
h3 {{font-size: 1.15rem !important; margin-top: 0.6rem;}}

/* Header */
.pd-hero {{background: linear-gradient(120deg, {NAVY} 0%, {BLUE} 70%, {TEAL} 130%); color: #fff;
  border-radius: 16px; padding: 22px 26px 20px; margin-bottom: 14px;
  box-shadow: 0 6px 20px rgba(10, 37, 64, 0.18);}}
.pd-hero-top {{display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; flex-wrap: wrap;}}
.pd-brand {{font-size: 1.75rem; font-weight: 800; letter-spacing: -0.02em; line-height: 1.1;}}
.pd-brand span {{opacity: 0.75; font-weight: 600;}}
.pd-tagline {{margin-top: 6px; font-size: 0.98rem; opacity: 0.92; max-width: 640px;}}
.pd-asset {{margin-top: 10px; font-size: 0.82rem; opacity: 0.8;}}
.pd-badge {{display: inline-block; padding: 4px 10px; border-radius: 999px; font-size: 0.74rem; font-weight: 700;
  letter-spacing: 0.04em; text-transform: uppercase; background: rgba(255,255,255,0.16);
  border: 1px solid rgba(255,255,255,0.35); color: #fff; white-space: nowrap;}}
.pd-badge.upload {{background: rgba(14,147,132,0.35); border-color: rgba(255,255,255,0.5);}}

/* Status cards */
.pd-status {{display: grid; grid-template-columns: repeat(auto-fit, minmax(min(140px, 100%), 1fr)); gap: 12px; margin: 4px 0 18px;}}
.pd-card {{background: #fff; border: 1px solid #E3E8EF; border-left: 6px solid var(--c); border-radius: 12px;
  padding: 12px 14px; box-shadow: 0 1px 3px rgba(16, 24, 40, 0.06);}}
.pd-card-label {{font-size: 0.72rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: #667085;}}
.pd-card-value {{font-size: 1.35rem; font-weight: 800; color: var(--c); margin-top: 2px; line-height: 1.2;}}
.pd-card-sub {{font-size: 0.8rem; color: #475467; margin-top: 3px;}}

/* Story sections */
.pd-section {{margin: 26px 0 6px; padding-top: 14px; border-top: 1px solid #E3E8EF;}}
.pd-section.first {{border-top: none; margin-top: 4px; padding-top: 0;}}
.pd-step {{display: inline-flex; align-items: center; gap: 8px; font-size: 0.74rem; font-weight: 800;
  letter-spacing: 0.08em; text-transform: uppercase; color: {TEAL};}}
.pd-step b {{display: inline-grid; place-items: center; width: 22px; height: 22px; border-radius: 50%;
  background: {TEAL}; color: #fff; font-size: 0.75rem; letter-spacing: 0;}}
.pd-section-title {{font-size: 1.35rem; font-weight: 800; color: {NAVY}; margin: 4px 0 2px; letter-spacing: -0.01em;}}
.pd-section-sub {{color: #475467; font-size: 0.92rem; margin-bottom: 4px;}}

/* Streamlit widgets */
div[data-testid="stMetric"] {{background: #fff; border: 1px solid #E3E8EF; border-radius: 12px; padding: 10px 14px;
  box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);}}
div[data-testid="stMetricLabel"] p {{font-weight: 600; color: #475467;}}
.stTabs [data-baseweb="tab-list"] {{gap: 4px; border-bottom: 2px solid #E3E8EF;}}
.stTabs [data-baseweb="tab"] {{padding: 10px 16px; font-weight: 700;}}
.stTabs [data-baseweb="tab"] p {{font-size: 1rem;}}
div[data-testid="stExpander"] details {{background: #fff; border-radius: 10px;}}
div[data-testid="stTable"] table {{background: #fff;}}
div[data-testid="stVegaLiteChart"], div[data-testid="stArrowVegaLiteChart"] {{background: #fff; border: 1px solid #E3E8EF;
  border-radius: 12px; padding: 8px;}}
.pd-tools-intro {{background: #fff; border: 1px dashed #C9D3DF; border-radius: 12px; padding: 10px 14px;
  color: #475467; font-size: 0.92rem; margin-bottom: 8px;}}
.pd-guide {{color: #475467; font-size: 0.88rem; margin: -6px 0 12px;}}
.pd-card[title] {{cursor: help;}}
section[data-testid="stSidebar"] .stButton button {{width: 100%;}}
.pd-tools {{display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin: 2px 0 10px;}}
.pd-tool {{background: #fff; border: 1px solid #E3E8EF; border-radius: 12px; padding: 12px 14px;
  box-shadow: 0 1px 3px rgba(16, 24, 40, 0.06);}}
.pd-tool-icon {{font-size: 1.5rem; line-height: 1;}}
.pd-tool-name {{font-weight: 800; color: {NAVY}; margin-top: 6px; font-size: 0.95rem;}}
.pd-tool-q {{color: #475467; font-size: 0.82rem; margin-top: 2px;}}
.pd-pointer {{background: #EAF4FF; border: 1px solid #C5DDF5; border-radius: 12px; padding: 10px 14px;
  color: {NAVY}; font-size: 0.93rem; margin: 18px 0 4px;}}
</style>
"""


def apply_style():
    st.markdown(CSS, unsafe_allow_html=True)


def header(data_label, data_detail):
    """Brand header. ``data_label`` is 'SYNTHETIC' or 'uploaded'; ``data_detail`` is the scenario or file name."""
    upload = data_label == "uploaded"
    badge = "Uploaded log" if upload else "Synthetic demo data"
    st.markdown(
        f"""<div class="pd-hero"><div class="pd-hero-top"><div>
<div class="pd-brand">🔍 Pump Detective <span>· predictive strainer care</span></div>
<div class="pd-tagline">Predicts when a clogging suction strainer will cost a chilled-water pump its NPSH margin,
schedules the cleaning, writes the work order and verifies the result.</div>
<div class="pd-asset">CHWPP-01 primary chilled-water pump · Lowara NSC 80-200 reference curve · {escape(str(data_detail))}</div>
</div><div class="pd-badge{' upload' if upload else ''}">{badge}</div></div></div>""",
        unsafe_allow_html=True,
    )


def status_cards(cards):
    """Render a row of cards: (label, value, sub, status_key[, tooltip]); status_key picks the colour."""
    html = ""
    for label, value, sub, key, *tip in cards:
        title = f' title="{escape(tip[0])}"' if tip and tip[0] else ""
        html += (f'<div class="pd-card" style="--c:{STATUS_COLOURS.get(key, BLUE)}"{title}>'
                 f'<div class="pd-card-label">{escape(label)}</div><div class="pd-card-value">{escape(value)}</div>'
                 f'<div class="pd-card-sub">{escape(sub)}</div></div>')
    st.markdown(f'<div class="pd-status">{html}</div>', unsafe_allow_html=True)


def section(step, kicker, title, sub=None, first=False):
    """Numbered story heading, e.g. section(1, 'Monitor', 'Sensor data')."""
    number = f"<b>{step}</b>" if step else ""
    st.markdown(
        f'<div class="pd-section{" first" if first else ""}"><div class="pd-step">{number}{escape(kicker)}</div>'
        f'<div class="pd-section-title">{escape(title)}</div>'
        + (f'<div class="pd-section-sub">{escape(sub)}</div>' if sub else "") + "</div>",
        unsafe_allow_html=True,
    )


def note(text, kind="pointer"):
    st.markdown(f'<div class="pd-{kind}">{text}</div>', unsafe_allow_html=True)


def tool_cards(tools):
    """A row of tool cards: (icon, name, the question it answers). Opened with the tabs underneath."""
    html = "".join(
        f'<div class="pd-tool"><div class="pd-tool-icon">{escape(icon)}</div>'
        f'<div class="pd-tool-name">{escape(name)}</div><div class="pd-tool-q">{escape(question)}</div></div>'
        for icon, name, question in tools
    )
    st.markdown(f'<div class="pd-tools">{html}</div>', unsafe_allow_html=True)

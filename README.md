# Pump Detective

**Predictive maintenance for chilled-water pump strainers, a prototype built for GenHacks 2026.**

A clogging suction strainer slowly eats a pump's NPSH safety margin until the pump cavitates. Pump Detective trends strainer pressure drop, corrects it for flow, **predicts when the NPSH margin will be lost**, schedules cleaning before that happens, writes the work order, and **verifies after maintenance whether the cleaning actually worked**.

**Live app:** _link to be added_ · All data are **synthetic**. Nothing has been validated with field measurements.

## The story

```
MONITOR → DIAGNOSE → PREDICT → RECOMMEND → MAINTAIN → VERIFY
```

| Step | What happens | Where |
|---|---|---|
| Monitor | 60-day hourly sensor log (synthetic): flow, pressure before the strainer, suction pressure | Fouling forecast |
| Diagnose | Flow-normalised strainer Δp; sensor glitches and debris events detected | Fouling forecast, Strainer diagnostics |
| Predict | Fouling trend projected to the maintenance limit and to the NPSH WARNING / CRITICAL limits | Fouling forecast |
| Recommend | Clean-by date and priority from deterministic rules; work order written by AI or offline | Fouling forecast, Detective Intelligence |
| Maintain | Technician cleans the strainer and records one Δp reading and the flow | Verify the maintenance form |
| Verify | RESTORED / IMPROVED, NOT CLEAN / NOT EFFECTIVE / SUSPICIOUSLY LOW, plus NPSH after cleaning | Fouling forecast |

## Architecture: Python decides, AI explains

```
Engineering calculations (NPSHa, NPSHr, margin, Q² normalisation)   app.py, pump_detective.py
        ↓
Statistical forecast (trend, anomalies, time to limit)               forecast.py
        ↓
Maintenance decision (priority, clean-by date, verification verdict) app.py, verification.py
        ↓
AI explanation / work order (optional; offline fallback)             app.py (OpenAI Responses API)
```

Every number, status, priority and date is computed in Python before the AI sees it. The AI is instructed not to change or invent any of them. Offline mode produces the same work order with no API key.

## What is in the app

| Tab | What it does |
|---|---|
| **Fouling forecast** | The predictive core: synthetic sensor log, flow-normalised trend, anomaly detection, forecast to each limit, clean-by recommendation, and the post-maintenance verification form. |
| **Detective Intelligence** | Ranked findings with evidence and next checks; maintenance work order (AI or offline); downloadable report. |
| Repair simulation | Fault diagnosis: one extra reading shows whether low suction comes from the strainer or from upstream; compares cleaning, pipe resizing and adding pressure. |
| Strainer diagnostics | The basic "reveal the missing reading" rule on three cases. |
| Cavitation Shield | NPSHa at the suction flange vs the Lowara demo curve; SAFE / WARNING / CRITICAL. |
| Secondary pump · Part-load / VFD | Part-load snapshot; NPSH assessed only with user-supplied pump-specific NPSHr. |

## Engineering method

- **Pressures:** all absolute (kPa abs).
- **NPSHa:** static absolute pressure at the DN100 suction flange + velocity head − vapour pressure of water at 20 °C (conservative; chilled water is colder). Inputs at or below vapour pressure, or with velocity above 5 m/s, are reported as NOT ASSESSED.
- **NPSHr:** points read approximately from the [Xylem Lowara e-NSC catalog, page 100](https://www.xylem.com/siteassets/brand/lowara/resources/technical-brochure/191002951_nsc-50hz_en.pdf#page=100), NSC 80-200/55 at about 1450 rpm. This is a reference pump; the installed CHWPP-01 model is not confirmed.
- **NPSH status:**
  - CRITICAL: NPSHa below NPSHr.
  - WARNING: the engineer-selected margin (sidebar, default 1.0 m) is not met.
  - SAFE: otherwise.

  The catalogue's 0.5 m allowance is shown separately and is not added to the margin.
- **Flow normalisation:** strainer loss follows Δp = K·Q² (turbulent flow), so readings are converted to design flow (21.2 L/s): Δp* = Δp·(Q_ref/Q)². Readings below 30 % of design flow are rejected.
- **Physics-based limits:** allowable strainer Δp = pressure before the strainer − suction pressure needed for NPSHr (+ margin), at design flow.

## Predictive method (`forecast.py`)

1. **Synthetic log:** daily load cycle and chiller staging, sensor noise, injected sensor glitches. Three scenarios: gradual fouling, a debris slug on day 45, and a stable strainer.
2. **Anomalies:** isolated outliers (robust z-score above 6 against a 25-hour rolling median) are excluded. A jump of more than 1.5 kPa in the daily median is a step change, and the trend is refitted from that day.
3. **Trend:** ln(Δp*) is fitted linearly against time on recent daily medians (exponential fouling), with a 95 % range on the rate.
4. **Forecast:** days until each limit; the recommendation uses the earliest estimate, plus whether cleaning alone can restore the margin.

## Maintenance verification (`verification.py`)

- One post-cleaning Δp reading **and the flow at that moment**, flow-normalised. A low-flow reading cannot pass as clean.
- **Clean band:** the expanded uncertainty (k = 2) of the difference from the clean baseline. It comes from instrument datasheet accuracies treated as rectangular limits (GUM), for either two absolute transmitters or one DP transmitter, plus optional baseline repeatability.
- **Verdicts:**
  - RESTORED: within the band.
  - IMPROVED, NOT CLEAN: above the band, below the maintenance limit.
  - NOT EFFECTIVE: at or above the limit.
  - SUSPICIOUSLY LOW: below the band; possible torn screen, bypass or sensor fault.
- **NPSH after cleaning:** reported separately.
- **Input checks:** missing, zero, out-of-range and physically impossible readings are rejected with a clear message.

## AI maintenance recommendation

Detective Intelligence opens on the Fouling forecast snapshot. Ask **"What maintenance should we schedule?"** to get a work order: Action, Priority, Complete by, Why, Also check, Confidence.

- **Priority rule:** URGENT = due now, HIGH = within 14 days, PLANNED = later, NONE = nothing within 180 days. It is set by the rules, not the AI.
- **OpenAI mode** (optional, `OPENAI_API_KEY`): the model may use only the forecast's own dates, priority and ranges, must state that the data are synthetic, and must report verification verdicts exactly.
- **Offline mode** (the default without a key): the same work order, built deterministically.

## Limitations

- All sensor data are synthetic. The pump curve is a published reference read by eye, not the installed pump's.
- The demo plant is a **low-pressure rooftop plant** (33 kPa abs before the strainer), so suction is below atmospheric. With this pump's low NPSHr, strainer fouling only threatens the NPSH margin at such low pressures; the app flags the low suction separately.
- The forecast range reflects uncertainty in the fouling **rate** only. Real fouling can accelerate or stop; re-run the forecast as data arrive.
- Anomaly thresholds, the 5 kPa clean baseline, the 20 kPa maintenance limit and the instrument accuracies are example values.
- The diagnosis tabs use an illustrative ±2 kPa tolerance. Verification uses the instrument-based band instead.
- NPSH after cleaning assumes the pressure before the strainer is unchanged. Water properties are taken at 20 °C.
- The AI's wording is not automatically cross-checked against the calculated numbers; the findings are shown alongside it.

## Run locally

Use Python 3.12 or 3.13, in the folder that contains `app.py`:

```bash
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

(macOS/Linux: use `python3` instead of `py`.)

## Tests

32 unit tests cover the forecast, flow normalisation, anomaly detection, verification and its input validation, and the strainer diagnosis rule:

```bash
py -m unittest discover tests
```

## Future work

Real sensor ingestion, alerts, multiple pumps, a forecast range that includes level uncertainty, and an automated check of AI wording against the calculated numbers. A technician work-order app (Momen) was prototyped but **not integrated**; see `docs/MOMEN_PLAN.md`.

## Tools

Python (calculations and rules), numpy and pandas (trend analysis), Streamlit and Altair (interface and charts), OpenAI Responses API (optional explanations). ChatGPT and Claude Code assisted with code, review and documentation. `archive/` holds an earlier version for reference only.

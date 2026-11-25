# Pump Detective

**Predictive maintenance for chilled-water pump strainers, a prototype built for GenHacks 2026.**

A clogging suction strainer slowly eats a pump's NPSH safety margin until the pump cavitates. Pump Detective trends strainer pressure drop, corrects it for flow, **predicts when the NPSH margin will be lost**, schedules cleaning before that happens, writes the work order, and **verifies after maintenance whether the cleaning actually worked**.

**Live app:** [pump-detective.streamlit.app](https://pump-detective.streamlit.app/) (free hosting: if you see a sleep screen, click "Yes, get this app back up!" and wait about a minute) · All data are **synthetic**. Nothing has been validated with field measurements.

## The story

```
MONITOR → DIAGNOSE → PREDICT → RECOMMEND → MAINTAIN → VERIFY
```

| Step | What happens | Where |
|---|---|---|
| Monitor | 60-day hourly sensor log (synthetic), or **your own CSV log**: flow, pressure before the strainer, suction pressure | Strainer forecast |
| Diagnose | Flow-normalised strainer Δp; sensor glitches and debris events detected | Strainer forecast, Engineering tools |
| Predict | Fouling trend projected to the maintenance limit and to the NPSH WARNING / CRITICAL limits, then checked with a backtest | Strainer forecast |
| Recommend | Clean-by date and priority from deterministic rules; work order written by AI or offline | Strainer forecast (Create work order) |
| Maintain | Technician cleans the strainer and records one Δp reading and the flow | Record cleaning result (pop-up) |
| Verify | RESTORED / IMPROVED, NOT CLEAN / NOT EFFECTIVE / SUSPICIOUSLY LOW, plus NPSH after cleaning | Strainer forecast |

## Architecture: Python decides, AI explains

```
Engineering calculations (NPSHa, NPSHr, margin, Q² normalisation)   npsh.py, pump_detective.py
        ↓
Statistical forecast (trend, anomalies, time to limit)               forecast.py
        ↓
Maintenance decision (priority, clean-by date, verification verdict) app.py, verification.py
        ↓
AI explanation / work order (optional; offline fallback)             app.py (OpenAI Responses API)
```

Every number, status, priority and date is computed in Python before the AI sees it. The AI is instructed not to change or invent any of them. Offline mode produces the same work order with no API key.

## What is in the app

The main page answers three questions on one screen: is the pump OK, what should be done, and by when.

- **Sidebar:** page switch, sensor data (synthetic demo, your CSV, or a one-click example log), pressure before the strainer, cleaning limit, and ⚙️ Settings (NPSH margin; AI or Offline writer when the server has an AI key).
- **📈 Strainer forecast:**
  - **Status row:** NPSH status now, next action and priority, complete-by date, backtest error, and the last maintenance check once one is recorded. Hover a card for a plain-language explanation.
  - **Recommendation box:** the recommendation with three buttons. **Create work order** writes it right there. **Record cleaning result** opens a pop-up that verifies a post-cleaning reading. **Download report** saves a PDF with the status, recommendation, chart, forecast table, evidence and, once created, the work order. Under the buttons, **Why?** lists the evidence and **Ask about this forecast** answers questions.
  - **Chart:** history and forecast, followed by detail tabs: Forecast table · Forecast check (backtest) · Events · How it works & data.
- **🧰 Engineering tools** (separate page, run only when opened). Each tool is titled with the question it answers, with inputs on the left and results on the right: coloured status cards, plus a diagram or chart.
  - **🔧 Repair simulation:** the "reveal the missing reading" rule on a suction-line diagram coloured by the readings shows whether the strainer or the system is to blame. A bar chart then compares NPSH available for cleaning, pipe resizing and adding system pressure against NPSHr and the target.
  - **🛡️ Cavitation Shield:** the operating point plotted on the Lowara NPSHr curve, with the target margin and the catalogue reference.
  - **⚙️ Part-load / VFD:** operating-point cards, an affinity-law chart at the current speed, and NPSH checked only with user-supplied NPSHr.
  - **🧠 Findings & explanation:** evidence and next checks for these cases, with a PDF report.
- **Downloads:** every readable document is a PDF: the forecast report, the work order, answers, the sensor data report, a PDF for each engineering tool, and the tools' diagnostic report and explanation. PDFs use the DejaVu Sans font in `fonts/` (license included), so Δ, ± and similar symbols print correctly. Data files stay CSV, because they are for Excel or for uploading again: the raw hourly data (in "Raw data for engineers") and the example log.

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

1. **Synthetic log:** daily load cycle and chiller staging, sensor noise, injected sensor glitches. Four scenarios: gradual fouling, a debris slug on day 45, a stable strainer, and linear fouling, which deliberately does not follow the exponential model the forecast fits.
2. **Anomalies:** isolated outliers (robust z-score above 6 against a 25-hour rolling median) are excluded. A jump of more than 1.5 kPa in the daily median is a step change, and the trend is refitted from that day.
3. **Trend:** ln(Δp*) is fitted linearly against time on recent daily medians (exponential fouling), with a 95 % range on the rate.
4. **Forecast:** days until each limit; the recommendation uses the earliest estimate, plus whether cleaning alone can restore the margin.
5. **Backtest:** the last 7, 14 or 21 days are hidden, the same pipeline (step detection included) is run on the earlier days, and its forecast is compared with what the sensors then showed. The app reports the error on the last hidden day, the mean absolute error and how many hidden days fall inside the 95 % range (rate uncertainty plus day-to-day scatter). With 14 days hidden:

   | Scenario | Error after 14 days | Mean absolute error |
   |---|---|---|
   | Gradual fouling | +1.2 % | 2.8 % |
   | Linear fouling (model mismatch) | −0.6 % | 2.7 % |
   | Stable strainer | +1.2 % | 2.9 % |
   | Debris slug | not meaningful: the step change falls on the last training day, and the app says so |

   With 21 days hidden, the debris-slug forecast is made before the event and misses it (−42 %). A trend cannot predict a sudden event; that is why the method watches for step changes and refits.

## Use your own sensor data

In the sidebar, choose **My own sensor log (CSV)** and drop in a file, or click **▶ Try it with the example log**. The uploaded log goes through the same pipeline as the demo: flow normalisation, anomaly and step detection, trend, forecast, backtest, recommendation, work order and verification.

| Column | Unit | |
|---|---|---|
| `timestamp` | e.g. `2026-11-01 14:15` | required |
| `flow_lps` | L/s | required |
| `pressure_before_kpa_abs` | kPa absolute, before the strainer | with `suction_kpa_abs` |
| `suction_kpa_abs` | kPa absolute, at the pump suction | with `pressure_before_kpa_abs` |
| `dp_kpa` | kPa, DP transmitter across the strainer | instead of the two pressures |

- **What is accepted:** any logging interval (readings are averaged to hourly values), gaps, and pump stops (flow 0). At least 15 days of data are needed.
- **Cleanings:** a cleaning in the log is detected as a sudden drop, and the trend restarts after the last one.
- **Pressure for the NPSH limits:** the pressure before the strainer is taken as the median of the last 7 days. If the file has only `dp_kpa`, you enter it.
- **Rejected files:** missing columns, unreadable files, logs that are too short, gauge (negative) pressures, swapped pressure taps and flows that look like m³/h are rejected with a message saying what to fix.
- **Dates:** forecast dates count from the last reading in the file.
- **Privacy:** the file is analysed in memory and not saved.

`examples/example_sensor_log.csv` is a **synthetic** 40-day log in this format, with 15-minute readings, a strainer cleaning on 22 Oct, a 10-hour logger outage and two transmitter glitches. `examples/make_example_log.py` recreates it. The app's **Download** button also produces a log in this format, so a downloaded demo log can be uploaded again.

The app cannot confirm that an uploaded log comes from this plant, or that its pressures are absolute. The data origin is shown on screen, in the report and to the AI.

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

Click **📋 Create work order** in the recommendation box to get a work order: Action, Priority, Complete by, Why, Also check, Confidence.

- **Priority rule:** URGENT = due now, HIGH = within 14 days, PLANNED = later, NONE = nothing within 180 days. It is set by the rules, not the AI.
- **AI mode** (optional, set up by the developer, never by users): put **one** key in `.streamlit/secrets.toml` (see `secrets.toml.example`; the real file is git-ignored) or in the host's secrets settings. Use `OPENAI_API_KEY` (paid API, optional `OPENAI_MODEL`) or `GEMINI_API_KEY` (Google Gemini, which has a free tier; optional `GEMINI_MODEL`, default `gemini-flash-latest`). If both are set, OpenAI is used. The key stays on the server. With a key, Settings offers AI or Offline, and "Ask about this forecast" appears; without one, the app uses Offline only. On Gemini's free tier Google may use the requests to improve its products, which is acceptable here because the data are synthetic. In AI mode, the model may use only the forecast's own dates, priority and ranges, must state that the data are synthetic, and must report verification verdicts exactly.
- **Offline mode** (the default without a key): the same work order, built deterministically.

## Limitations

- All sensor data are synthetic. The pump curve is a published reference read by eye, not the installed pump's.
- The demo plant is a **low-pressure rooftop plant** (33 kPa abs before the strainer), so suction is below atmospheric. With this pump's low NPSHr, strainer fouling only threatens the NPSH margin at such low pressures; the app flags the low suction separately.
- The forecast range reflects uncertainty in the fouling **rate** only. Real fouling can accelerate or stop; re-run the forecast as data arrive.
- The backtest scores the method on the same synthetic log. It shows the method behaves sensibly, not how accurate it would be in the field.
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

67 unit tests cover the NPSH physics (checked against hand calculations and the demo values), the forecast and its backtest, CSV upload (format, cleanings, rejected files, round trip), flow normalisation, anomaly detection, verification and its input validation, and the strainer diagnosis rule:

```bash
py -m unittest discover tests
```

## Future work

Live sensor ingestion (BMS / historian connection instead of CSV files), alerts, multiple pumps, a forecast range that includes level uncertainty, a phone app for technicians to receive work orders and submit the post-cleaning reading, and an automated check of AI wording against the calculated numbers.

## Tools

Python (calculations and rules), numpy and pandas (trend analysis), Streamlit and Altair (interface and charts; custom theme in `.streamlit/config.toml`, `ui.py` and `visuals.py`), reportlab (PDF reports), OpenAI Responses API (optional explanations). ChatGPT and Claude Code assisted with code, review and documentation. `archive/` holds an earlier version for reference only.

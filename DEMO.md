# GenHacks demo recording (≤ 3:00)

Story: the pump is safe today → fouling rises once flow is corrected for → a future NPSH-margin violation is predicted → maintenance is scheduled first → the work order is written → the strainer is cleaned → the post-maintenance reading is entered → Pump Detective verifies the result.

Suggested track: **AI, Agentic Systems, Cybersecurity & Dev Tools** (AI integrated with engineering guardrails). Open is the safe alternative. All data are synthetic; say so on screen.

## Before recording

- Sidebar: **📈 Strainer forecast**, **Synthetic demo**, history **Gradual fouling**, 33 kPa abs before the strainer, cleaning limit 20 kPa. Under ⚙️ Settings: margin 1.00 m (and AI if the server has a key in `.streamlit/secrets.toml`).
- Don't show `.streamlit/secrets.toml`, the terminal, downloads or the `archive/` folder.
- Record at 1280 px wide or more; zoom the browser to about 110 %.

## Script

Everything up to 2:50 happens on one screen: the status row, the recommendation box and the chart. Only the detail tabs need a short scroll.

| Time | Show | Say |
|---|---|---|
| 0:00–0:15 | Title card: "Losing cooling isn't an option", then the app's yellow "Schedule strainer cleaning before…" box | "In a hospital or a data centre, losing cooling isn't an option. After power, cooling is the most common cause of serious data-centre outages, and more than half of major outages cost over $100,000. One quiet cause: a clogged pump strainer that makes the pump cavitate and destroy itself, with no warning. Pump Detective sees it coming." |
| 0:15–0:30 | The status row (**SAFE**, **PLANNED**, complete-by date, backtest +1.2 %) | "This chilled-water pump is safe today. But its suction strainer is clogging, and a clogged strainer silently eats the margin that keeps the pump from cavitating. The top row gives the whole answer: safe now, cleaning planned, and a forecast we have checked." |
| 0:30–1:05 | The chart: grey dots → blue line → orange forecast → coloured limit lines | "Raw pressure drop swings with flow, the grey dots. Strainer loss scales with flow squared, so we correct every reading to design flow: the blue line, the real fouling trend. Physics turns our NPSH safety margin into a strainer limit, the yellow line, and the trend is projected to it." |
| 1:05–1:20 | The yellow recommendation, then the **📊 Forecast table** tab (the dates move with the recording day) | "The margin is lost in about [read the number of days from the screen]. So Pump Detective schedules cleaning before the earliest estimate." |
| 1:20–1:35 | **✅ Forecast check** tab (14 days hidden) | "Can we trust it? We hide the last two weeks, run the same method on the rest, and compare. The forecast made 14 days ago was within about one percent of today's reading. Even when fouling doesn't follow our model, it stays within a few percent." |
| 1:35–2:05 | **📋 Create work order**: the work order appears in the box | "Python makes every decision: dates, priority, limits. The work order is written from those facts, including the backtest, and the AI can't change them. Without an API key, the same work order is built offline." |
| 2:05–2:30 | **🧹 Record cleaning result** → 5.1 kPa at 21.0 L/s → **RESTORED**, and a fifth card appears in the status row | "After cleaning, the technician records one reading and the flow. Corrected to design flow, it's inside the clean band, ±0.94 kPa from the instrument accuracy. Strainer restored, NPSH safe." |
| 2:30–2:50 | Record again: 4.9 kPa at 14.8 L/s → **IMPROVED, NOT CLEAN** | "Here's why flow matters: 4.9 kPa looks clean, but it was measured at low flow. At design flow it's 10 kPa, so this cleaning did not work." |
| 2:50–3:00 | Close on the status row | "Monitor, diagnose, predict, recommend, maintain, verify. Synthetic data and a published pump curve today; ready for real sensors." |

Cuts if you run long: shorten the 0:30–1:05 chart explanation first. If you have spare time, show the example log (sidebar: **My own sensor log** → **▶ Try it with the example log**: "The same method runs on a real logger export. It even finds the cleaning on 22 October and restarts the trend."). If you have spare time, show the **⚠️ Events** tab ("sensor glitches are detected and excluded, so they can't trigger false alarms").

## Devpost checklist

Public GitHub link, deployed app link, embeddable YouTube or Vimeo video, track, every team member, tools used including AI tools (ChatGPT, Claude Code, Google Gemini API), and 3 screenshots (forecast chart, work order, RESTORED verdict).

[GenHacks submission requirements](https://genhacks-open.devpost.com/#requirements)

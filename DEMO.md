# GenHacks demo recording (≤ 3:00)

Story: the pump is safe today → fouling rises once flow is corrected for → a future NPSH-margin violation is predicted → maintenance is scheduled first → the work order is written → the strainer is cleaned → the post-maintenance reading is entered → Pump Detective verifies the result.

Suggested track: **AI, Agentic Systems, Cybersecurity & Dev Tools** (AI integrated with engineering guardrails). Open is the safe alternative. All data are synthetic; say so on screen.

## Before recording

- Open **https://pump-detective.streamlit.app/?embed=true** (hides Streamlit Cloud's own badges). Wait until the app has fully loaded, then reload once so nothing is left from a previous visit.
- Sidebar: **📈 Strainer forecast**, **Synthetic demo**, history **Gradual fouling**, 33 kPa abs before the strainer, cleaning limit 20 kPa. Under ⚙️ Settings: margin 1.00 m.
- Then collapse the sidebar (« at its top) so the status row and the chart fill the screen.
- Record at 1280 px wide or more; zoom the browser to about 110 %. Turn off notifications.
- Don't show `.streamlit/secrets.toml`, the terminal, downloads or the `archive/` folder.
- Dates move with the recording day: read the complete-by date from the screen ("[date]" below).
- Speak at a relaxed pace: the narration is about 330 words, which fits 3:00 with pauses. Do one full practice run with a timer.

## Script

| Time | Show | Say |
|---|---|---|
| 0:00–0:20 | Title card: "Losing cooling isn't an option", then the app header | "In a hospital or a data centre, losing cooling isn't an option. After power, cooling is the most common cause of serious data-centre outages. One silent cause is a clogging pump strainer: it starves the pump until it cavitates and destroys itself. Pump Detective sees it coming, weeks ahead." |
| 0:20–0:35 | The status row: **SAFE**, **PLANNED**, complete-by date, forecast check +1.2 % | "This chilled-water pump is safe today, but its strainer is clogging. The top row gives the whole answer: safe now, cleaning planned, a complete-by date, and a forecast we have actually checked." |
| 0:35–1:05 | Scroll to the chart. Point in turn at the grey dots, the blue line, the red crosses, the yellow line, then the orange **"Clean by [date]"** marker | "Raw pressure drop, the grey dots, swings with flow. Strainer loss scales with flow squared, so every reading is corrected to design flow: the blue line is the true fouling trend. The red crosses are sensor glitches, detected and excluded. Physics turns the pump's NPSH safety margin into a pressure-drop limit, the yellow line, and the forecast shows when we reach it: clean by [date]." |
| 1:05–1:25 | **✅ Forecast check** tab under the chart | "Can we trust it? We hide the last two weeks, run exactly the same method on the rest, and compare. The forecast was within about one percent of the real reading." |
| 1:25–1:55 | Scroll up, click **📋 Create work order**; the work order appears | "One click writes the work order. Python makes every decision: the date, the priority, the limits. Gemini only turns those facts into clear instructions for the technician, and it can't change a single number. If the AI is unavailable, the same work order is built offline." |
| 1:55–2:20 | **🧹 Record cleaning result** → 5.1 kPa at 21.0 L/s → **Verify maintenance** → **RESTORED**, a fifth card appears and the work order folds away as closed | "After cleaning, the technician enters one reading and the flow. Corrected to design flow, it is inside the clean band, plus or minus 0.94 kPa from instrument accuracy. Strainer restored, pump safe, work order closed." |
| 2:20–2:45 | **🧹 Record cleaning result** again: 4.9 kPa at 14.8 L/s → **IMPROVED, NOT CLEAN** | "Here's why flow matters. 4.9 kPa looks clean, but it was measured at low flow. At design flow it is 10 kPa, so this cleaning did not work, and the work order stays open." |
| 2:45–3:00 | Scroll to the top; close on the status row | "Monitor, diagnose, predict, recommend, maintain, verify. Synthetic data and a published pump curve today; ready for real sensor logs tomorrow. This is Pump Detective." |

Cuts if you run long: shorten the chart explanation first (drop the red-crosses sentence). If you have spare time, open the sidebar and show **My own sensor log** → **▶ Try it with the example log**: "The same method runs on a real logger export. It even finds the cleaning in the middle of the log and restarts the trend."

If something goes wrong during the take (a slow AI answer, a typo), keep going: the work order also appears offline, and you can cut the pause in editing.

## Devpost checklist

Public GitHub link, deployed app link, embeddable YouTube or Vimeo video, track, every team member, tools used including AI tools (ChatGPT, Claude Code, Google Gemini API), and 3 screenshots (forecast chart with the "Clean by" marker, work order, RESTORED verdict).

[GenHacks submission requirements](https://genhacks-open.devpost.com/#requirements)

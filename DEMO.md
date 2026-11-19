# GenHacks demo recording (≤ 3:00)

Story: the pump is safe today → fouling rises once flow is corrected for → a future NPSH-margin violation is predicted → maintenance is scheduled first → the work order is written → the strainer is cleaned → the post-maintenance reading is entered → Pump Detective verifies the result.

Suggested track: **AI, Agentic Systems, Cybersecurity & Dev Tools** (AI integrated with engineering guardrails). Open is the safe alternative. All data are synthetic; say so on screen.

## Before recording

- Open the app on **Fouling forecast**, scenario **Gradual fouling**, 33 kPa abs before the strainer, sidebar margin 1.00 m.
- In **Detective Intelligence**, select **Offline** (or OpenAI if a key is configured) and the question **What maintenance should we schedule?**. Don't generate yet.
- Don't show API-key settings, the terminal, downloads or the `archive/` folder.
- Record at 1280 px wide or more; zoom the browser to about 110 %.

## Script

| Time | Show | Say |
|---|---|---|
| 0:00–0:15 | **Fouling forecast**: the three figures (Δp* 10.7 kPa, fouling rate, NPSHa 2.41 m **SAFE**) | "This chilled-water pump is safe today. But its suction strainer is clogging, and a clogged strainer silently eats the margin that keeps the pump from cavitating." |
| 0:15–0:50 | Chart: grey dots → blue line → orange forecast → coloured limit lines | "Raw pressure drop swings with flow, the grey dots. Strainer loss scales with flow squared, so we correct every reading to design flow: the blue line, the real fouling trend. Physics turns our NPSH safety margin into a strainer limit, the yellow line, and the trend is projected to it." |
| 0:50–1:05 | Forecast table and the yellow banner (clean-by date about 20 days from the recording day; the dates move with today's date) | "The margin is lost in about 24 days, 20 to 30. So Pump Detective schedules cleaning before the earliest estimate." |
| 1:05–1:20 | Scroll to **Would this forecast have worked?** (14 days hidden) | "Can we trust it? We hide the last two weeks, run the same method on the rest, and compare. The forecast made 14 days ago was within about one percent of today's reading. Even when fouling doesn't follow our model, it stays within a few percent." |
| 1:20–1:50 | **Detective Intelligence** → Generate | "Python makes every decision: dates, priority, limits. The AI only writes the work order from those facts, including the backtest, and can't change them. Without an API key, the same work order is built offline." |
| 1:50–2:15 | Back to **Fouling forecast** → Verify: 5.1 kPa at 21.0 L/s → **RESTORED** | "After cleaning, the technician records one reading and the flow. Corrected to design flow, it's inside the clean band, ±0.94 kPa from the instrument accuracy. Strainer restored, NPSH safe." |
| 2:15–2:35 | Enter 4.9 kPa at 14.8 L/s → **IMPROVED, NOT CLEAN** | "Here's why flow matters: 4.9 kPa looks clean, but it was measured at low flow. At design flow it's 10 kPa, so this cleaning did not work." |
| 2:35–2:50 | *(Optional)* Note on the blue info box | "It also notes that suction is still below atmospheric in this low-pressure plant, a problem cleaning alone can't fix." |
| 2:50–3:00 | Close on the chart | "Monitor, diagnose, predict, recommend, maintain, verify. Synthetic data and a published pump curve today; ready for real sensors." |

Cuts if you run long: drop the optional 2:35 note first. If you have spare time, add the events table after the forecast table ("sensor glitches are detected and excluded, so they can't trigger false alarms").

## Devpost checklist

Public GitHub link, deployed app link, embeddable YouTube or Vimeo video, track, every team member, tools used including AI tools (ChatGPT, Claude Code, OpenAI API), and 3 screenshots (forecast chart, work order, RESTORED verdict).

[GenHacks submission requirements](https://genhacks-open.devpost.com/#requirements)

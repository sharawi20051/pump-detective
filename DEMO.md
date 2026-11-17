# GenHacks demo recording

Track: to be decided. Open is the safe default; the AI track becomes a better fit once the AI layer recommends maintenance. The prototype uses simulated data and engineering rules.

| Time | Show | Say |
|---|---|---|
| 0:00–0:15 | Open **Repair simulation** and point to the fault-scenario text. | “A rooftop chiller plant has lost system pressure, and pump suction is far below atmospheric. Is the strainer to blame, or something upstream?” |
| 0:15–0:45 | Scenario A: reveal the upstream pressure, then **Simulate a clean filter**. | “One extra reading shows a 25 kPa drop across the strainer. Cleaning raises available suction head from 0.95 to 2.99 metres, from CRITICAL to SAFE.” |
| 0:45–1:05 | Switch to Scenario B and reveal the reading. | “Same suction pressure, but the strainer drop is normal, so the problem is upstream. Cleaning would not help.” |
| 1:05–1:55 | Open **Fouling forecast** (Gradual fouling). Point at the grey dots, then the blue line, then the orange forecast and the threshold lines. | “That is diagnosis. To predict, we trend 60 days of sensor data, synthetic for this prototype. Raw Δp swings with flow, so we normalise it to design flow. Physics converts our NPSH margin into an allowable strainer Δp, and the trend tells us we lose the margin in about three weeks. Clean before this date.” |
| 1:55–2:20 | Switch to **Debris slug**. Point at the events table. | “Here a debris event on day 45 is detected automatically, the trend is refitted, and the alert becomes clean now. Sensor glitches are flagged and ignored.” |
| 2:20–2:45 | Open **Detective Intelligence** (Fouling forecast snapshot). Ask **What maintenance should we schedule?** and generate. | “The AI turns the forecast into a work order: action, priority, complete-by date and evidence. It may only use the forecast's own dates, and it flags that suction is still below atmospheric, which cleaning won't fix. With no API key, the same work order is built offline.” |
| 2:45–2:55 | Close on the forecast chart. | “The pressures are simulated and the pump curve is a published reference. The method is ready for real sensor data.” |

Before submitting: push the source to a public repository; record the demo on YouTube or Vimeo with embedding enabled and keep it under three minutes; on Devpost add the code and video links, the chosen track, every team member, and the tools used, including AI tools.

[GenHacks submission requirements](https://genhacks-open.devpost.com/#requirements)

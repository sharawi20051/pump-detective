# GenHacks demo recording

Suggested track: **Open**. The current prototype uses software simulation and engineering rules.

| Time | Show | Say |
|---|---|---|
| 0:00–0:20 | Open **Repair simulation**. | “Low suction pressure can come from a blocked filter or from a problem before the filter. Pump Detective helps decide where to check first.” |
| 0:20–0:55 | In Scenario A, point out 8 kPa absolute at suction. Reveal the upstream pressure. | “With only this suction reading, the tool requests one more measurement. The drop across the filter is 25 kPa, so the first check is for a restriction.” |
| 0:55–1:25 | Select **Simulate a clean filter**. | “Holding flow and upstream pressure fixed, the model estimates that cleaning raises available suction head from 0.95 to 2.99 metres. That crosses the catalog comparison value in this scenario.” |
| 1:25–2:00 | Switch to Scenario B, reveal the reading and simulate cleaning. | “Same starting suction pressure. This time the drop is 5 kPa, our clean-filter reference. Simulated cleaning makes no difference, so the next check is upstream.” |
| 2:00–2:20 | Open **Cavitation Shield** and point to the catalog reference. | “Python calculates the suction head. We compare it with a published Lowara curve. The pressures are simulated and the curve is for a reference pump.” |

Before submitting, upload the source to a public repository and record the demo on YouTube or Vimeo with embedding enabled. Add the code and video links, the chosen track, team members, and the tools used to the Devpost draft. Keep the recording under three minutes.

[GenHacks submission requirements](https://genhacks-open.devpost.com/#requirements)

# Devpost submission text: Pump Detective

Copy each section into the matching Devpost field. Devpost accepts Markdown in the main story.

---

## Project name
Pump Detective

## Elevator pitch / tagline (max 200 characters)
Predicts when a clogging strainer will make a chilled-water pump cavitate, schedules the cleaning, writes the work order and checks that the fix worked.

## Track
AI, Agentic Systems, Cybersecurity, and Dev Tools

## Built with (tags)
python, streamlit, altair, numpy, pandas, reportlab, openai-api, github-actions, streamlit-community-cloud

## Try it out (links)
- Live app: https://pump-detective.streamlit.app/
- Code: https://github.com/sharawi20051/pump-detective
- Video: <paste your YouTube link>

> Note for judges: the free hosting sleeps when unused. If you see a sleep screen, click "Yes, get this app back up!" and wait about a minute.

---

## About the project (main story)

### Inspiration
Every large building is cooled by chilled-water pumps, and in front of each pump sits a strainer that catches debris. As the strainer slowly clogs, the pressure at the pump inlet drops. Below a certain point the water starts to boil inside the pump. That is **cavitation**: it eats the impeller, causes noise and vibration, and ends in an expensive repair and downtime.

Today, strainers are usually cleaned on a fixed calendar or after something goes wrong. The data to do better already exists, because most plants log flow and pressure, but nobody turns it into the question a technician actually needs answered: **"When do I have to clean this, and did my cleaning work?"**

### What it does
Pump Detective follows the whole maintenance loop:

**Monitor → Diagnose → Predict → Recommend → Maintain → Verify**

- **One screen answers the main question.** A status row shows whether the pump is safe now, the next action and its priority, the clean-by date, and how accurate the forecast has been.
- **Predicts the failure date.** It trends the strainer's pressure drop, corrects it for flow, and projects when the pump's NPSH safety margin (its protection against cavitation) will be lost, with a 95 % range.
- **Proves the forecast can be trusted.** A built-in backtest hides the last two weeks of data, forecasts them with the same method, and compares. On the demo data, the forecast made 14 days earlier was within about 1 % of the real value. Even when the data deliberately does not follow the model, it stays within a few percent.
- **Writes the work order.** One click produces a work order with action, priority, deadline, evidence and checks. It is written by AI, or by a built-in offline writer when no AI is available.
- **Verifies the repair.** After cleaning, the technician enters one reading and the flow. The app tells them whether the strainer is really clean, within the accuracy of their own instruments. It also catches misleading cases, such as a reading taken at low flow that only looks clean.
- **Works with real data.** You can upload your own logger export (CSV). The app finds strainer cleanings and sensor glitches in it by itself, and restarts the trend after the last cleaning.
- **Engineering tools.** A suction-line diagram shows whether the strainer or the system is to blame. A repair comparison shows whether cleaning, a bigger pipe or more system pressure fixes the problem. There is also a cavitation chart on the pump's real curve, and a part-load check for variable-speed pumps.
- **Reports anyone can use.** Every result downloads as a PDF: the forecast report, the work order, the sensor-data report and each tool's result.

### How we built it
- **Python decides, AI explains.** Every number, status, priority and date is calculated in Python before the AI sees anything. The AI is told to use only those facts and may not change them. The same work order can be written offline with no API key.
- **Engineering core.**
  - NPSH available is calculated from absolute suction pressure, velocity head and the vapour pressure of water.
  - NPSH required comes from a published Lowara pump curve.
  - Strainer pressure drop is corrected to design flow with Δp* = Δp·(Q_ref/Q)², because strainer loss scales with flow squared.
  - Physics turns the NPSH safety margin into a strainer pressure-drop limit, so the forecast has a meaningful target.
- **Forecasting.**
  - A robust rolling filter removes sensor glitches.
  - Sudden jumps (a debris slug) and sudden drops (a cleaning) are detected, and the trend restarts after them.
  - An exponential fouling trend is fitted with its statistical range.
- **Verification.** The clean band comes from the instruments' datasheet accuracy, following the GUM method for measurement uncertainty, so "clean" means clean within what the sensors can actually tell.
- **Interface and delivery.**
  - Streamlit and Altair for the app, with a custom design, SVG diagrams and PDF reports built with reportlab.
  - Deployed on Streamlit Community Cloud, with a GitHub Action that keeps the demo awake for judges.
  - 74 automated tests cover the physics (checked against hand calculations), the forecast and backtest, CSV upload, verification and the PDFs.

### Challenges we ran into
- **Making the forecast trustworthy, not just good-looking.** The first version fitted a trend to data generated with that same trend shape. We added a backtest and a deliberately mismatched scenario to show how the method behaves when its own assumption is wrong.
- **Raw pressure drop is misleading.** It swings with flow all day. Without flow correction, a dirty strainer measured at low flow looks clean. Getting this right changed both the forecast and the verification.
- **Being honest about the physics.** With this pump, cavitation only becomes possible when the system loses fill pressure. Instead of hiding that, the app says so, and it tells the user when cleaning alone cannot fix the problem.
- **Keeping AI in its place.** We designed the app so the AI cannot invent a date or change a priority, and so it still works fully without AI.

### Accomplishments that we're proud of
- A complete loop, from raw sensor data to a verified repair, that a technician could follow without an engineering degree.
- A forecast that checks itself and openly reports when it cannot be trusted (for example, right after a sudden event).
- It runs on real logger exports, detects cleanings automatically, and produces professional PDF reports.

### What we learned
- Engineering credibility comes from showing your assumptions and testing them, not from more features.
- The best place for AI in safety-related work is explaining decisions, not making them.
- Good user experience matters as much as good calculations: one clear screen beats six tabs of numbers.

### What's next for Pump Detective
- Connect directly to building-management systems instead of CSV files.
- Validate the forecast on real plant data, and support each installed pump's own curve.
- Add alerts and a phone view for technicians, and support many pumps at once.

### Honest limitations
All demo data are synthetic. The pump curve is a published reference curve read from the catalogue, not a specific installed pump. Nothing has been validated with field measurements yet. The app is a maintenance-planning aid, not a safety certification.

---

## Team
<add every team member's name and Devpost profile>

## Tools used (including AI tools)
Python, Streamlit, Altair, numpy, pandas, reportlab, GitHub Actions, Streamlit Community Cloud, OpenAI API (optional AI work orders). ChatGPT and Claude assisted with code, review and documentation.

## Screenshots (suggested captions)
1. **One screen, the whole answer:** pump status, the next action, the clean-by date and the forecast's own accuracy.
2. **Is it the strainer or the system?** The suction-line diagram changes colour with the readings, then the repair options are compared.
3. **Reports anyone can use:** the forecast report as a PDF, with chart, evidence and work order.
4. **Real data:** an uploaded logger export, with the strainer cleaning on 22 Oct detected automatically.

# Pump Detective

Pump Detective is an educational web app for investigating low suction pressure in a chilled-water pump system. It shows how a pressure reading before a filter helps distinguish a restricted filter from low pressure upstream, then simulates how cleaning the filter changes available net positive suction head (NPSHa).

## Run locally

Use Python 3.12 or 3.13. Unzip the project and open a terminal in the folder containing `app.py`.

Windows PowerShell:

```powershell
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

macOS or Linux:

```bash
python3 -m pip install -r requirements.txt
python3 -m streamlit run app.py
```

Open the Local URL shown in the terminal. You can also run the original text demo with `py pump_detective.py` on Windows or `python3 pump_detective.py` on macOS or Linux.

## Try the demo

1. Open **Repair simulation**. Both scenarios begin at **8 kPa absolute** at the pump suction.
2. In **Scenario A**, turn on **Reveal pressure before the filter**. The filter pressure drop is **25 kPa**. Select **Simulate a clean filter** to see NPSHa rise from **0.95 m to 2.99 m**.
3. Switch to **Scenario B** and reveal the reading again. The filter pressure drop is already **5 kPa**, the simulated clean-filter baseline. The cleaning simulation leaves NPSHa at **0.95 m** and the app suggests checking upstream conditions.

## Model and data

- **Design reference:** Equipment schedule MH010001, primary chilled-water pump CHWPP-01, at 21.2 L/s and 15 m design head. The design head is distinct from NPSH.
- **Pump curve:** [Xylem Lowara e-NSC catalog, page 100](https://www.xylem.com/siteassets/brand/lowara/resources/technical-brochure/191002951_nsc-50hz_en.pdf#page=100), NSC 80-200/55 at approximately 1450 rpm. The app interpolates approximate readings from the catalog graph and shows the manufacturer's additional 0.50 m allowance. The installed CHWPP-01 pump model has not been confirmed.
- **Simulation:** The repair comparison holds flow and pressure upstream of the filter fixed. It assumes water at 20 °C, a 100 mm internal diameter, and negligible loss between the filter outlet and pump suction. The clean-filter pressure drop of 5 kPa and diagnostic tolerance of ±2 kPa are demonstration assumptions. The app has not been validated with field measurements.

## Tools

Python implements the calculations and diagnostic rules. Streamlit provides the interface. ChatGPT assisted with code, tests, and documentation.

## Compare suction-side changes

In Repair simulation, reveal the upstream reading and move the pipe diameter slider. The app compares filter cleaning, pipe resizing, and an upstream pressure increase from the same baseline. The 80 mm baseline pipe is an assumed straight segment, 12 m long with Darcy friction factor 0.025. The nozzle stays fixed at 100 mm. Fitting and transition losses are excluded.

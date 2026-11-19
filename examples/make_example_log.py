"""Create examples/example_sensor_log.csv: a SYNTHETIC log in the upload format.

It imitates what a building management system export looks like: 15-minute
readings, real timestamps, a strainer cleaning on day 12, a 10-hour logger
outage and two suction-transmitter glitches. Run:  py examples/make_example_log.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

Q_REF = 21.2
rng = np.random.default_rng(42)
t = pd.date_range("2026-10-10 00:00", "2026-11-18 23:45", freq="15min")
day = ((t - t[0]) / pd.Timedelta(days=1)).to_numpy()
hour_of_day = (t.hour + t.minute / 60).to_numpy()

ratio = 0.9 + 0.07 * np.sin(2 * np.pi * (hour_of_day - 9) / 24) + rng.normal(0, 0.015, t.size)
flow = Q_REF * np.clip(np.asarray(ratio), 0.7, 1.05)
flow[np.asarray((t.dayofweek == 6) & (t.hour < 6))] = 0.0  # pump stopped early on Sunday mornings

clean_day = 12.4
dp_star = np.where(day < clean_day, 6.0 * np.exp(0.035 * day), 5.2 * np.exp(0.02 * (day - clean_day)))
dp = dp_star * (flow / Q_REF) ** 2
before = 105.0 + rng.normal(0, 0.3, t.size)
suction = before - dp + rng.normal(0, 0.3, t.size)
for when in ("2026-10-27 03:15", "2026-11-09 16:30"):
    suction[t.get_loc(pd.Timestamp(when))] -= 9.0  # transmitter glitch

df = pd.DataFrame({"timestamp": t.strftime("%Y-%m-%d %H:%M"), "flow_lps": flow.round(2),
                   "pressure_before_kpa_abs": before.round(2), "suction_kpa_abs": suction.round(2)})
outage = (t >= "2026-11-02 08:00") & (t < "2026-11-02 18:00")
df = df[~outage]
out = Path(__file__).with_name("example_sensor_log.csv")
df.to_csv(out, index=False)
print(f"Wrote {out} ({len(df)} rows)")

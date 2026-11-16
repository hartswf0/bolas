"""Measured checks for the test shot: cord lag after the shove (I7), energy decay, wheel lock, drawings on twos."""
import sys, json
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/mauro-martino-exercises-in-style/test-shot-build")
import build as b
import numpy as np
b.setup(); sim = b.simulate()
rows = []
for d in range(10, 42):
    f = 2 * d; s = sim[f]
    tip = s["cord"][-1] - s["anchor"]
    ang = float(np.degrees(np.arctan2(tip[0], tip[1])))     # swing angle from vertical (deg)
    # head tilt: neck angle in the pose
    rows.append(dict(drawing=d, t=round(d / 12, 3), cord_deg=round(ang, 1), energy=round(float(s["energy"]), 1)))
base = np.mean([r["cord_deg"] for r in rows if 10 <= r["drawing"] < 14])
win = [r for r in rows if 14 <= r["drawing"] <= 20]
first = max(win, key=lambda r: abs(r["cord_deg"] - base))   # drawing of the largest swing-out after contact
peakE = max(r["energy"] for r in rows if 14 <= r["drawing"] <= 22)
E = [float(s["energy"]) for s in sim]
e32 = E[int(3.2 * 24)]
tips = {d: b.man_state(d / 12)[2] for d in range(12, 26)}
out = dict(shove_drawing=14, shove_t=[14 / 12, 15 / 12], stanchion_drawing=16, cord_swing_out_drawing=first["drawing"],
           cord_lag_drawings=first["drawing"] - 14, cord_energy_peak_after_shove=peakE, cord_energy_at_3_2s=e32,
           cord_energy_ratio_3_2s=e32 / peakE, tip_deg_by_drawing=tips, wheel_angle_0_80=b.wheel_angle(0.80),
           wheel_angle_0_85=b.wheel_angle(0.85), wheel_angle_0_95=b.wheel_angle(0.95), bus_x_0_85=b.bus_x(0.85), bus_x_0_90=b.bus_x(0.90),
           runners=len(b.RUNNERS), rows=rows)
p = b.WS / "test-shot-build" / "metrics.json"
p.write_text(json.dumps(out, indent=1))
print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=1))
for r in rows[:16]: print(r)

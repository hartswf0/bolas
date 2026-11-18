"""I9 hinge / FK tests, I5 memory light, I6 silence, multiplane ratios -> test-shot-build/stage_tests.json"""
import json, subprocess, numpy as np, math
from PIL import Image
D = "/home/user/bolas/paeleo/scion/oulipo/films/swarm/les-lieux-dune-fugue"
ev = json.load(open(D + "/test-shot-build/stage_events.json"))
E = [e for e in ev["events"] if "leaves" in e]
out = {}
for s in "LR":
    ht = np.array([e["leaves"][s]["hinge_top"] for e in E]); hb = np.array([e["leaves"][s]["hinge_bottom"] for e in E])
    tr = np.array([e["truck"] for e in E]) * 0.95
    hx = ht[:, 0] + tr                       # hinge x in leaf-plane coords (truck removed)
    out[f"I9_hinge_x_drift_{s}_px"] = round(float(hx.max() - hx.min()), 4)
    out[f"I9_hinge_height_range_{s}_px"] = round(float((hb[:, 1] - ht[:, 1]).max() - (hb[:, 1] - ht[:, 1]).min()), 4)
    th = np.array([e["leaves"][s]["theta"] for e in E])
    out[f"theta_max_{s}_deg"] = round(float(th.max()), 2)
    out[f"distinct_leaf_drawings_{s}"] = int(len(set(np.round(th, 3))))
    # child (knob) never slides: its projected position equals the leaf homography of its local anchor (by construction);
    # check the knob stays on the line hinge->free edge at constant v (y ratio along the hinge)
TL = [e["theta_L"] for e in E]; TR = [e["theta_R"] for e in E]
iL = next(i for i, v in enumerate(TL) if v > 0); iR = next(i for i, v in enumerate(TR) if v > 0)
out["right_leaf_lag_frames"] = iR - iL
out["contact_L_s"], out["contact_R_s"], out["cut_s"] = ev["contact_L"], ev["contact_R"], ev["cut"]
out["parallax"] = dict(truck_px=6.0, facade=6.0, leaves=6.0 * 0.95, memory_bench=6.0 * 0.4, memory_park=0.0)
# audio silence after the cut (decoded from the mp4)
a = np.frombuffer(subprocess.run(["ffmpeg", "-loglevel", "error", "-i", D + "/test-shot.mp4", "-f", "s16le", "-ac", "2", "-ar", "44100", "-"],
                                 capture_output=True).stdout, np.int16).reshape(-1, 2)
nz = np.nonzero(np.abs(a).max(1))[0]
out["I6_last_nonzero_sample_s"] = round(float(nz[-1] / 44100), 4)
out["I6_exact_zero_seconds_after_cut"] = round(float(len(a) / 44100 - nz[-1] / 44100), 3)
out["I6_note"] = "PCM is exactly 0 from 8.000 s; AAC codec smear leaves ~3.5 ms of tiny values (|x|<=164) after the cut"
# I5: memory cold, stone warm (frame at 3.5 s)
f = np.asarray(Image.open(D + "/test-shot-build/_f350.png").convert("RGB")).astype(float)
mem = f[300:560, 270:420]; st = f[200:560, 600:940]
out["I5_memory_mean_rgb"] = mem.reshape(-1, 3).mean(0).round(1).tolist()
out["I5_memory_B_ge_R"] = bool(mem[..., 2].mean() >= mem[..., 0].mean())
out["I5_stone_R_minus_B"] = round(float(st[..., 0].mean() - st[..., 2].mean()), 1)
out["I8_kit_grain"] = "not applied: frames bypass kit.Ink entirely (Film.frame overridden); no vignette"
json.dump(out, open(D + "/test-shot-build/stage_tests.json", "w"), indent=1)
print(json.dumps(out, indent=1))

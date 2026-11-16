"""Assemble the animator outputs: master clip, test-shot sheet, stills, exposure sheet, animation.json."""
import json
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import motion as M          # noqa: E402
import anim as A            # noqa: E402

OUT = A.OUT
SW = "/home/user/bolas/paeleo/scion/oulipo/films/swarm/teuf-teuf/"
FPS = 24

# ---- master clip (concat of the shot clips, same codec -> stream copy)
lst = OUT + "shots.txt"
with open(lst, "w") as f:
    for name, a, b in A.SHOT_LIST:
        f.write(f"file 'shot_{name}.mp4'\n")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
                OUT + "animator_master_0-44s.mp4"], check=True)

# ---- stills for the editor + test-shot sheet 16.2-21.0
os.makedirs(OUT + "stills", exist_ok=True)


def grab(t):
    p = OUT + f"stills/frame_{t:05.2f}.png"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t + 0.5 / FPS:.4f}", "-i",
                    OUT + "animator_master_0-44s.mp4", "-frames:v", "1", p], check=True)
    return p


for t in (2.0, 7.0, 11.8, 13.4, 15.0, 17.5, 19.5, 22.0, 24.0, 28.8, 30.0, 33.2, 34.5, 36.4, 40.0, 42.0):
    grab(t)

times = [16.2, 16.45, 16.7, 16.9, 17.1, 17.5, 18.2, 18.8, 19.2, 19.6, 19.75, 20.0, 20.4, 20.7, 21.0 - 1 / FPS]
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 15)
cw, ch = 426, 240
sheet = Image.new("RGB", (cw * 3 + 40, (ch + 26) * 5 + 50), (22, 22, 18))
d = ImageDraw.Draw(sheet)
d.text((10, 10), "teuf-teuf ANIMATOR - TEST SHOT rollers beat 16.2-21.0 s (3b close-up x2.2, 3c wide). Frames from animator_master_0-44s.mp4",
       fill=(230, 225, 200), font=font)
ev = {round(e["t"], 2): e["event"] for e in M.EVENTS}
for i, t in enumerate(times):
    p = grab(t)
    im = Image.open(p).resize((cw, ch), Image.LANCZOS)
    x, y = 10 + (i % 3) * (cw + 10), 40 + (i // 3) * (ch + 26)
    sheet.paste(im, (x, y))
    near = [e for e in M.EVENTS if abs(e["t"] - t) < 0.13]
    lab = f"{t:5.2f}s cam {'B' if 16.2 <= t < 18.8 else 'A'}" + (f"  {near[0]['kind']}" if near else "")
    d.text((x, y + ch + 3), lab, fill=(230, 225, 200), font=font)
sheet.save(SW + "test-shot-sheet.jpg", quality=88)

# ---- metrics
FM = json.load(open(OUT + "frames_metrics.json"))
frames = FM["frames"]
frames.sort(key=lambda r: r["k"])


def shot_of(t):
    for name, a, b in A.SHOT_LIST:
        if a <= t < b:
            return name


per_shot = {}
CUTS = {int(round(x * FPS)) for x in (13.0, 16.2, 18.8, 25.0, 34.0)}
for name, a, b in A.SHOT_LIST:
    fr = [r for r in frames if r["shot"] == name]
    out = {"film_time_s": [a, b], "frames": [fr[0]["k"], fr[-1]["k"]], "n_frames": len(fr),
           "camera": sorted({r["cam"] for r in fr}), "clip": f"sources/teuf-teuf/animator/shot_{name}.mp4"}
    for who in ("pusher", "carrier"):
        slide = 0.0
        for r0, r1 in zip(fr, fr[1:]):
            if r1["k"] in CUTS or who not in r0 or who not in r1:
                continue
            for j in range(2):
                if r0[who]["planted"][j] and r1[who]["planted"][j]:
                    a0, a1 = r0[who]["feet_xy"][j], r1[who]["feet_xy"][j]
                    slide = max(slide, math.hypot(a1[0] - a0[0], a1[1] - a0[1]))
        hres = [max(r[who]["hand_res"]) for r in fr if who in r and r[who]["pinned"]]
        fres = [max(r[who]["foot_res"]) for r in fr if who in r]
        knee = [max(r[who]["knee_flex"]) for r in fr if who in r]
        out[who] = {"max_planted_foot_slide_px": round(slide, 3),
                    "max_hand_residual_px_while_pinned": round(max(hres), 3) if hres else None,
                    "pinned_frames": len(hres),
                    "max_foot_ik_residual_px": round(max(fres), 3) if fres else None,
                    "max_knee_flex_deg": round(max(knee), 1) if knee else None}
    # roller slip: d(theta)*R - d(x) for carried logs
    if any("logs" in r for r in fr):
        slip = 0.0
        for r0, r1 in zip(fr, fr[1:]):
            if r1["k"] in CUTS or "logs" not in r0 or "logs" not in r1:
                continue
            for n in "ABCD":
                s0, s1 = r0["logs"][n], r1["logs"][n]
                if s0[2] == s1[2] == "carried" or (s0[2] == s1[2] == "free"):
                    R = M.LOGS[n].R
                    slip = max(slip, abs((s1[1] - s0[1]) * R - (s1[0] - s0[0])))
        out["roller_slip_px_per_frame"] = round(slip, 4)
    if any("wheels" in r for r in fr):
        slip = 0.0
        for r0, r1 in zip(fr, fr[1:]):
            for j in range(2):
                if r0["wheels"][j][2] == r1["wheels"][j][2] and r0["wheels"][j][2] in ("free", "out"):
                    slip = max(slip, abs((r1["wheels"][j][1] - r0["wheels"][j][1]) * M.R_WHEEL - (r1["wheels"][j][0] - r0["wheels"][j][0])))
        out["loose_wheel_slip_px_per_frame"] = round(slip, 4)
    # stone continuity: max jump vs sim velocity
    jumps = []
    for r0, r1 in zip(fr, fr[1:]):
        if r1["k"] in CUTS:
            continue
        jumps.append(abs(r1["stone"]["F"] - r0["stone"]["F"]))
    out["max_stone_step_px_per_frame"] = round(max(jumps), 3) if jumps else 0.0
    out["stone_front_m_at_end"] = round((fr[-1]["stone"]["F"] - M.X0) / M.PXM, 3)
    per_shot[name] = out

# wide vs close-up agreement at the cuts (same tau -> same sim state)
agree = {}
for tc in (16.2, 18.8):
    k = int(round(tc * FPS))
    r0 = [r for r in frames if r["k"] == k - 1][0]
    r1 = [r for r in frames if r["k"] == k][0]
    agree[f"{tc}"] = {"cams": [r0["cam"], r1["cam"]], "stone_F_step_px": round(abs(r1["stone"]["F"] - r0["stone"]["F"]), 3),
                      "note": "both cameras sample the same per-frame sim state (motion.ROLL); the step is one frame of motion"}

decay = {k: [x for x in v.decay_times()] for k, v in M.SP.items()}
first_imp = {k: (round(v.imp[0][0], 3) if v.imp else None) for k, v in M.SP.items()}
pre = {}
for k, v in M.SP.items():
    if v.imp:
        i0 = int(v.imp[0][0] / M.DT)
        pre[k] = float(np.abs(v.x[:max(i0 - 1, 1)]).max())
sec = {"integrator": "semi-implicit Euler, dt 1/240 s (motion.Spring)",
       "channels": {k: {"f_hz": round(v.w / (2 * math.pi), 2), "zeta": v.z, "impulse_times": [round(t, 3) for t, _ in v.imp],
                         "decay_to_1pct_energy_s": decay[k], "max_abs_before_first_impulse": pre.get(k)}
                    for k, v in M.SP.items()},
       "test": "no secondary motion before the first impulse (max_abs_before_first_impulse == 0); every decay <= 0.6 s"}
worst_decay = max([x for v in decay.values() for x in v if x is not None])

# exposure sheet (Reiniger): per frame the replacement profiles and contact states
expo = []
for r in frames:
    row = {"k": r["k"], "t": r["t"], "cam": r["cam"], "shot": r["shot"], "stone": r["stone"]}
    for who in ("pusher", "carrier"):
        if who in r:
            row[who] = {"head": r[who]["head"], "hands": r[who]["hands"], "planted": r[who]["planted"],
                        "pinned": r[who]["pinned"], "feet_x": [r[who]["feet_xy"][0][0], r[who]["feet_xy"][1][0]]}
    for key in ("logs", "wheels", "wheel_theta", "plat_tilt_deg"):
        if key in r:
            row[key] = r[key]
    expo.append(row)
json.dump({"note": "exposure sheet of the rendered frames (motion fixture motion.py); the film's single motion ledger (editor repair 1)",
           "fps": FPS, "events": M.EVENTS, "frames": expo}, open(OUT + "exposure_animator.json", "w"))

# composited-frame tone vs reference (plan s10.6)
import layout_wall as LW     # noqa: E402
tone = {}
for t in (7.0, 17.5, 30.0):
    rgb = np.asarray(Image.open(OUT + f"stills/frame_{t:05.2f}.png").convert("RGB"))
    tone[f"{t}"] = LW.measure(rgb)

animation = {
    "unit": "animator", "film": "teuf-teuf", "direction": "1 La paroi", "date": "2026-11-16",
    "code": {"motion": "films/swarm/teuf-teuf/animator-build/motion.py", "render": "films/swarm/teuf-teuf/animator-build/anim.py",
             "wheel_cutout": "films/swarm/teuf-teuf/animator-build/wheel_cut.py", "report": "films/swarm/teuf-teuf/animator-build/report.py"},
    "inputs": {"plates": "sources/teuf-teuf/layout/frameA_lum.npy, frameB_lum.npy (layout-wall unit)",
               "title": "sources/teuf-teuf/layout/title_rub_A.png + title_reveal/ (layout-wall unit)",
               "exposure_json": "RECONCILED (editor repair 1): motion.py is the film's single motion fixture; this render's per-frame records (exposure_animator.json, frames_metrics.json) are the ledger, and films/swarm/teuf-teuf/verify_sheet.py regenerates swarm/teuf-teuf/exposure.json and the mechanism.json asserts from them. sim.py's earlier sheet is kept in swarm/teuf-teuf/superseded/."},
    "outputs": {
        "master_clip": "sources/teuf-teuf/animator/animator_master_0-44s.mp4 (1280x720, 24 fps, 1056 frames, H.264 crf 12, picture only, no captions, no sound)",
        "shot_clips": {n: f"sources/teuf-teuf/animator/shot_{n}.mp4" for n, a, b in A.SHOT_LIST},
        "stills": "sources/teuf-teuf/animator/stills/frame_*.png",
        "test_shot_sheet": "films/swarm/teuf-teuf/test-shot-sheet.jpg",
        "exposure_sheet": "sources/teuf-teuf/animator/exposure_animator.json",
        "per_frame_metrics": "sources/teuf-teuf/animator/frames_metrics.json",
        "wheel": "sources/teuf-teuf/animator/wheel_lum.npy, wheel_alpha.npy, wheel_grabcut_mask_src.png, wheel_charcoal_preview.png, wheel_ellipse.json"},
    "for_the_editor": {
        "events": M.EVENTS,
        "caption_cues": {"drag 4th stick begins": [e["t"] for e in M.EVENTS if e["kind"] == "stick"][3],
                         "log A stops (Et moi ?)": M.A_STOP[0], "cart passes 3 m": [e["t"] for e in M.EVENTS if e["kind"] == "pass-3m"][0],
                         "pin pulled": [e["t"] for e in M.EVENTS if e["kind"] == "pin-pull"][0],
                         "rear wheel drops": [e["t"] for e in M.EVENTS if e["kind"] == "wheel-drop"][0]},
        "declared_cuts_s": [13.0, 16.2, 18.8, 25.0, 34.0],
        "not_in_picture": "captions, end source line, scratch-wipe at 34.0, sound: editor / commentary-sound units",
        "footsteps_s": {k: [p for p, _ in v] for k, v in A.PLANTS.items()}},
    "per_shot": per_shot,
    "wide_closeup_agreement": agree,
    "secondary_dynamics": sec,
    "silhouette_read_test": {"method": "frame luminance < 0.30 thresholded, 4-connected components; a figure must be one component of its own mask (limbs never detach) and must not share a dark component with stone/logs/wheels/other figure",
                             "results": FM["silhouette"]},
    "tone_composited_frames": tone,
    "summary": {
        "max_planted_foot_slide_px": max(v[w]["max_planted_foot_slide_px"] for v in per_shot.values() for w in ("pusher", "carrier")),
        "max_pusher_hand_residual_px_while_pinned": max((v["pusher"]["max_hand_residual_px_while_pinned"] or 0) for v in per_shot.values()),
        "max_carrier_hand_residual_px_while_pinned": max((v["carrier"]["max_hand_residual_px_while_pinned"] or 0) for v in per_shot.values()),
        "max_roller_slip_px_per_frame": max(v.get("roller_slip_px_per_frame", 0) for v in per_shot.values()),
        "worst_secondary_decay_s": worst_decay,
        "final_positions_m": {"drag": per_shot["1_drag"]["stone_front_m_at_end"], "rollers": per_shot["3e_hold_3m"]["stone_front_m_at_end"],
                              "wheel": per_shot["4_wheel_axle"]["stone_front_m_at_end"], "counter": per_shot["5_counter_no_axle"]["stone_front_m_at_end"]}},
}
json.dump(animation, open(SW + "animation_metrics_tmp.json", "w"), indent=1)
print(json.dumps(animation["summary"], indent=1))
print(json.dumps({k: {w: v[w] for w in ("pusher", "carrier")} for k, v in per_shot.items()}, indent=0)[:3000])
print(json.dumps(tone, indent=0))
print(json.dumps(FM["silhouette"], indent=0)[:3000])

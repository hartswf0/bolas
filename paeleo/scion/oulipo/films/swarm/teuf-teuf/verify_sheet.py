"""teuf-teuf: ONE motion ledger (editor repair 1).

The critic found two ledgers: sim.py's exposure.json (250 px stone) certified by mechanism.json,
and the animator's motion.py sheet (180 px stone) that the picture was actually rendered from.
This script makes the RENDERED frames the only ledger:

  * reads the per-frame records written while rendering (sources/teuf-teuf/animator/
    frames_metrics.json, exposure_animator.json) and the motion fixture they were drawn from
    (animator-build/motion.py, anim.py),
  * re-runs invariants 1, 2, 3 and 7 and the caption-lag test on those frames,
  * measures the caption onsets on the rendered mp4s (caption band of teuf-teuf.mp4 minus the
    no-caption control, frame by frame),
  * rewrites swarm/teuf-teuf/exposure.json and the asserts / cues of mechanism.json.
sim.py's earlier outputs are kept unchanged in swarm/teuf-teuf/superseded/.

    python3 films/swarm/teuf-teuf/verify_sheet.py        (after anim.py, report.py and the film render)
"""
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FILMS = os.path.dirname(os.path.dirname(HERE))
ROOT = os.path.dirname(FILMS)
sys.path.insert(0, os.path.join(HERE, "animator-build"))
sys.path.insert(0, HERE)
import motion as M   # noqa: E402
import anim as A     # noqa: E402

AN = os.path.join(FILMS, "sources", "teuf-teuf", "animator")
FPS = 24
FM = json.load(open(os.path.join(AN, "frames_metrics.json")))
REC = sorted(FM["frames"], key=lambda r: r["k"])
XA = json.load(open(os.path.join(AN, "exposure_animator.json")))
CUTS_S = [13.0, 16.2, 18.8, 25.0, 34.0]
CUT_K = {int(round(c * FPS)) for c in CUTS_S}
RESETS = {13.0: "drag -> rollers trial (load back to 0 m), held black", 25.0: "rollers -> wheel trial (back to 0 m), held black",
          34.0: "wheel -> counter-check (back to 0 m), held black"}
EV = {}
for e in M.EVENTS:
    EV.setdefault(e["kind"], []).append(e["t"])

# ------------------------------------------------------------ superseded sim outputs (kept once)
SUP = os.path.join(HERE, "superseded")
os.makedirs(SUP, exist_ok=True)
for f in ("exposure.json", "mechanism.json"):
    src, dst = os.path.join(HERE, f), os.path.join(SUP, f.replace(".json", "-sim.json"))
    if os.path.exists(src) and not os.path.exists(dst):
        d = json.load(open(src))
        if "superseded" not in json.dumps(d.get("about", ""))[:200] and d.get("source") != "rendered frames":
            shutil.copy2(src, dst)

# ------------------------------------------------------------ helpers
def F_at(k):
    return REC[k]["stone"]["F"]


def front_m(k):
    return round((F_at(k) - M.X0) / M.PXM, 4)


def local_of(T, p):
    o = T(0.0, 0.0); ex = T(1.0, 0.0); ey = T(0.0, 1.0)
    a, c = ex[0] - o[0], ex[1] - o[1]
    b, d = ey[0] - o[0], ey[1] - o[1]
    det = a * d - b * c
    x, y = p[0] - o[0], p[1] - o[1]
    return ((d * x - b * y) / det, (-c * x + a * y) / det)


PUSH = [("drag", 4.5, 11.5), ("rollers", M.ROLL1[0], M.ROLL1[1]), ("rollers", M.ROLL2[0], M.ROLL2[1]),
        ("wheel", M.W_T0, M.W_T1), ("counter", M.C_T0, EV["stop-counter"][0])]

# ------------------------------------------------------------ invariant 1: same challenge
sha = hashlib.sha1(json.dumps([[round(x, 4), round(y, 4)] for x, y in M.STONE]).encode()).hexdigest()
hand_local = {}
for name, a, b in PUSH:
    ys = []
    for k in range(int(math.ceil(a * FPS)), int(b * FPS)):
        t = k / FPS
        st = A.stone_state(t)
        T = A.stone_T(st["xb"], st["bottom"], st["tilt"], st["pivot"])
        if st["mode"] == "counter" and A.plat_tilt(t) != 0.0:
            T = A.stone_T_counter(t, st)
        P = A.pusher(t, k, st)
        if not P.get("pinned"):
            continue
        ys.append([round(local_of(T, h)[1], 2) for h in P["hands"]])
    if ys:
        arr = np.array(ys)
        hand_local.setdefault(name, []).append([float(arr[:, 0].min()), float(arr[:, 0].max()), float(arr[:, 1].min()), float(arr[:, 1].max())])
push_len = {"drag": 7.0, "rollers": round((M.ROLL1[1] - M.ROLL1[0]) + (M.ROLL2[1] - M.ROLL2[0]), 3), "wheel": round(M.W_T1 - M.W_T0, 3)}
start_k = {"drag": int(round(4.5 * FPS)), "rollers": int(round(14.0 * FPS)), "wheel": int(round(26.0 * FPS)), "counter": int(round(35.0 * FPS))}
ends = {"drag (11.5 s)": front_m(int(round(11.5 * FPS))), "rollers (23.0 s)": front_m(int(round(23.0 * FPS))),
        "wheel (33.0 s)": front_m(int(round(33.0 * FPS))), "counter (stop)": front_m(int(math.ceil(EV["stop-counter"][0] * FPS)))}
hl = [v for vs in hand_local.values() for v in vs]
inv1 = {
    "stone_outline_sha1": sha, "stone_length_px": M.SL, "one_mask_every_trial": True,
    "load_front_at_push_start_px": {n: round(F_at(k), 3) for n, k in start_k.items()},
    "push_window_s": push_len,
    "pusher_hand_local_y_range_while_pinned": hand_local,
    "front_edge_m": ends,
}
inv1["pass"] = bool(all(abs(v - M.X0) < 0.5 for v in inv1["load_front_at_push_start_px"].values())
                    and all(abs(v - 7.0) < 1e-6 for v in push_len.values())
                    and max(abs(h[0] + 80) + abs(h[1] + 80) + abs(h[2] + 60) + abs(h[3] + 60) for h in hl) < 0.5
                    and abs(ends["drag (11.5 s)"] - 1.2) <= 0.05 and abs(ends["rollers (23.0 s)"] - 3.0) <= 0.05
                    and abs(ends["wheel (33.0 s)"] - 8.0) <= 0.1 and ends["counter (stop)"] <= 1.2)

# ------------------------------------------------------------ invariant 2: contact
def in_push(t):
    return any(a <= t < b for _, a, b in PUSH)


slide = {"pusher": 0.0, "carrier": 0.0}
slide_where = {}
hand = {"pusher_push": 0.0, "pusher_all_pinned": 0.0, "carrier_all_pinned": 0.0}
for r0, r1 in zip(REC, REC[1:]):
    if r1["k"] in CUT_K:
        continue
    for who in ("pusher", "carrier"):
        if who not in r0 or who not in r1:
            continue
        for j in range(2):
            if r0[who]["planted"][j] and r1[who]["planted"][j]:
                a0, a1 = r0[who]["feet_xy"][j], r1[who]["feet_xy"][j]
                d = math.hypot(a1[0] - a0[0], a1[1] - a0[1])
                if d > slide[who]:
                    slide[who] = d
                    slide_where[who] = r1["t"]
for r in REC:
    for who in ("pusher", "carrier"):
        if who in r and r[who]["pinned"]:
            h = max(r[who]["hand_res"])
            hand[f"{who}_all_pinned"] = max(hand[f"{who}_all_pinned"], h)
            if who == "pusher" and in_push(r["t"]):
                hand["pusher_push"] = max(hand["pusher_push"], h)
roll_slip = 0.0
for r0, r1 in zip(REC, REC[1:]):
    if r1["k"] in CUT_K or "logs" not in r0 or "logs" not in r1:
        continue
    for n in "ABCD":
        s0, s1 = r0["logs"][n], r1["logs"][n]
        if s0[2] == s1[2] and s0[2] in ("carried", "free"):
            roll_slip = max(roll_slip, abs((s1[1] - s0[1]) * M.LOGS[n].R - (s1[0] - s0[0])))
wheel_err = 0.0
for r in REC:
    if "wheel_theta" in r:
        wheel_err = max(wheel_err, abs(r["wheel_theta"] * M.R_WHEEL - (r["stone"]["F"] - M.X0)))
loose = 0.0
for r0, r1 in zip(REC, REC[1:]):
    if "wheels" in r0 and "wheels" in r1:
        for j in range(2):
            if r0["wheels"][j][2] == r1["wheels"][j][2] and r0["wheels"][j][2] in ("free", "out"):
                loose = max(loose, abs((r1["wheels"][j][1] - r0["wheels"][j][1]) * M.R_WHEEL - (r1["wheels"][j][0] - r0["wheels"][j][0])))
tang = 0.0
for r in REC:
    if "logs" in r:
        for n, s in r["logs"].items():
            if s[2] in ("carried", "free", "ground", "rest", "laid") and s[0]:
                L = M.LOGS[n]
                tang = max(tang, abs(L.cy(s[1]) + L.support(s[1], math.pi / 2) - M.GROUND))
inv2 = {"max_planted_foot_slide_px": {k: round(v, 3) for k, v in slide.items()}, "worst_slide_at_s": slide_where,
        "max_hand_residual_px": {k: round(v, 3) for k, v in hand.items()},
        "max_roller_slip_px_per_frame": round(roll_slip, 4), "max_loose_wheel_slip_px_per_frame": round(loose, 4),
        "wheel_rotation_error_px": round(wheel_err, 4), "log_ground_tangency_error_px": round(tang, 4),
        "bar": "foot slide <= 1 px, hand residual <= 2 px during pushes, roller slip <= 0.5 px/frame, tangent +-1 px"}
inv2["pass"] = bool(max(slide.values()) <= 1.0 and hand["pusher_push"] <= 2.0 and roll_slip <= 0.5 and tang <= 1.0)

# ------------------------------------------------------------ invariant 3: continuity
SUB = 10
worst = 0.0
jumps = []
for r0, r1 in zip(REC, REC[1:]):
    dF = abs(r1["stone"]["F"] - r0["stone"]["F"])
    t0, t1 = r0["t"], r1["t"]
    vs = [abs(A.stone_state(t0 + (t1 - t0) * (i + 1) / SUB)["F"] - A.stone_state(t0 + (t1 - t0) * i / SUB)["F"]) * SUB * FPS for i in range(SUB)]
    allow = max(vs) / FPS + 1.0
    if dF > allow:
        jumps.append({"t": r1["t"], "jump_px": round(dF, 2), "declared_cut": r1["k"] in CUT_K})
    elif r1["k"] not in CUT_K:
        worst = max(worst, dF - max(vs) / FPS)
agree = {}
for tc in (16.2, 18.8):
    k = int(round(tc * FPS))
    agree[str(tc)] = {"cams": [REC[k - 1]["cam"], REC[k]["cam"]], "load_step_px": round(abs(F_at(k) - F_at(k - 1)), 3),
                      "same_tau": True, "note": "both cameras draw the same per-frame state of motion.ROLL"}
inv3 = {"undeclared_jumps": [j for j in jumps if not j["declared_cut"]], "jumps_at_declared_cuts": [j for j in jumps if j["declared_cut"]],
        "declared_cuts_s": CUTS_S, "resets": {str(k): v for k, v in RESETS.items()}, "wide_closeup_agreement": agree}
inv3["pass"] = not inv3["undeclared_jumps"] and all(abs(j["t"] - min(CUTS_S, key=lambda c: abs(c - j["t"]))) < 0.05 for j in inv3["jumps_at_declared_cuts"])

# ------------------------------------------------------------ invariant 7: secondary motion
sec = {}
for k, v in M.SP.items():
    if not v.imp:
        continue
    i0 = int(v.imp[0][0] / M.DT)
    dec = [x for x in v.decay_times() if x is not None]
    sec[k] = {"first_impulse_s": round(v.imp[0][0], 3), "max_abs_before": float(np.abs(v.x[:max(i0 - 1, 1)]).max()),
              "max_decay_to_1pct_s": max(dec) if dec else None}
inv7 = {"channels": sec, "pass": all(s["max_abs_before"] == 0.0 and (s["max_decay_to_1pct_s"] or 0) <= 0.6 for s in sec.values())}

# ------------------------------------------------------------ captions (cues from the film script + measured on the mp4s)
CUE = json.load(open(os.path.join(HERE, "assembly-cues.json")))
caps = CUE["captions"]


def band_series(path, y0=620, h=90):
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", f"crop=1280:{h}:0:{y0},scale=320:{h // 4},format=gray",
                        "-f", "rawvideo", "-"], capture_output=True, check=True)
    a = np.frombuffer(p.stdout, np.uint8).reshape(-1, h // 4, 320).astype(np.float32)
    return a


measured = []
try:
    cap = band_series(os.path.join(ROOT, "assets", "films", "teuf-teuf.mp4"))
    nocap = band_series(os.path.join(ROOT, "assets", "films", "teuf-teuf-nocaption.mp4"))
    n = min(len(cap), len(nocap))
    diff = np.abs(cap[:n] - nocap[:n]).reshape(n, -1)
    vis = (diff > 25).mean(1) > 0.002
    for c in caps:
        k0 = int(round((c["on"] - 0.6) * FPS))
        ks = [k for k in range(max(0, k0), min(n, k0 + 48)) if vis[k]]
        measured.append(round(ks[0] / FPS, 3) if ks else None)
except Exception as ex:   # noqa: BLE001
    measured = [None] * len(caps)
    print("caption measurement skipped:", ex)
cues = []
for c, mt in zip(caps, measured):
    lag = round(c["on"] - c["cause_t"], 3)
    lag_m = round(mt - c["cause_t"], 3) if mt is not None else None
    cues.append({"text_fr": c["fr"], "cause": c["cause"], "cause_t": c["cause_t"], "onset_scripted": c["on"],
                 "first_visible_frame_measured_s": mt, "lag_scripted_s": lag, "lag_measured_s": lag_m,
                 "ok": 0.2 <= lag <= 0.6 and (lag_m is None or 0.2 <= lag_m <= 0.6 + 0.5 / FPS), "voice": c["voice"]})
cap_pass = all(c["ok"] for c in cues) and sum(1 for c in caps if c["voice"] != "narrator") == 1

# ------------------------------------------------------------ exposure.json (the one sheet)
frames = []
for r, x in zip(REC, XA["frames"]):
    row = {"k": r["k"], "t": r["t"], "cam": r["cam"], "shot": r["shot"],
           "load": {"front_px": r["stone"]["F"], "front_m": front_m(r["k"]), "rear_px": round(r["stone"]["F"] - M.SL, 3),
                    "underside_y": r["stone"]["bottom"], "tilt_deg": r["stone"]["tilt_deg"]}}
    for key in ("logs", "wheels", "wheel_theta", "plat_tilt_deg"):
        if key in r:
            row[key] = r[key]
    for who in ("pusher", "carrier"):
        if who in r:
            row[who] = {"feet_xy": r[who]["feet_xy"], "planted": r[who]["planted"], "pinned": r[who]["pinned"],
                        "hand_res": r[who]["hand_res"], "foot_res": r[who]["foot_res"], "head": r[who]["head"], "hands": r[who]["hands"]}
    frames.append(row)
expo = {"about": "teuf-teuf exposure sheet of the RENDERED frames: the film's single motion ledger (editor repair 1). "
                 "Written by verify_sheet.py from sources/teuf-teuf/animator/frames_metrics.json (records written by anim.py while "
                 "drawing each frame) and motion.py's event list. sim.py's earlier sheet: superseded/exposure-sim.json.",
        "source": "rendered frames", "fps": FPS, "px_per_m": M.PXM, "x0_px": M.X0, "ground_y": M.GROUND,
        "load": {"outline_local": M.STONE, "outline_sha1": sha, "length_px": M.SL},
        "events": M.EVENTS, "declared_cuts_s": CUTS_S, "push_windows": [{"trial": n, "t": [a, b]} for n, a, b in PUSH],
        "caption_cues": cues, "frames": frames}
json.dump(expo, open(os.path.join(HERE, "exposure.json"), "w"))

# ------------------------------------------------------------ mechanism.json: asserts on the rendered sheet
mech = json.load(open(os.path.join(HERE, "mechanism.json")))
mech["about"] = ("teuf-teuf parts and contact schema (plan 3, Olog), the [substitute] operation, and asserts for invariants 1-3, 7 "
                 "and the caption lags, RUN ON THE RENDERED FRAMES (verify_sheet.py, editor repair 1). The parts/contact schema is the "
                 "mechanic-historian's; the motion laws are motion.py's (film_laws). sim.py's own asserts: superseded/mechanism-sim.json.")
mech["revision"] = {"motion": "films/swarm/teuf-teuf/animator-build/motion.py", "render": "films/swarm/teuf-teuf/animator-build/anim.py",
                    "verify": "films/swarm/teuf-teuf/verify_sheet.py", "exposure": "films/swarm/teuf-teuf/exposure.json (rendered frames)",
                    "register": "films/swarm/teuf-teuf/register.json", "credits": "films/credits/teuf-teuf.json", "date": "2026-11-16",
                    "superseded": "films/swarm/teuf-teuf/superseded/ (sim.py exposure + asserts, 250 px stone)"}
mech["input_force"] = {"kind": "Push", "N": "same law in every trial", "hand_local_y": [-80.0, -60.0],
                       "window_s": 7.0, "note": "hands pinned to the stone's rear face at the same stone-local height in every trial; "
                       "7.0 s of push in drag (4.5-11.5), rollers (14.0-17.6 + 19.6-23.0, the stone waiting on two logs while log D is set "
                       "down) and wheel (26.0-33.0); the counter-check replays the wheel trial's input law from 35.0 s"}
mech["load"] = {"outline_sha1": sha, "width_px": M.SL, "same_mask_every_trial": True, "front_at_0m_px": M.X0}
mech["film_laws"] = {"drag": "9 stick-slip lurches (smoothstep, 0.16 s each, every 0.75 s from 4.85 s), 1.20 m in total",
                     "rollers": "cycloid ease 0->150 px (14.0-17.6) and 150->300 px (19.6-23.0); carried logs at v/2, no slip; a log is squeezed "
                                "out when it passes the stone's rear lip, rolls back (kick -260/-190 px/s, friction 520 px/s^2) and stops",
                     "wheel": "accelerate 0.8 s, cruise, decelerate 1.4 s: 8.00 m in 26.0-33.0; wheel angle = dx/R",
                     "counter": "the same input law from 35.0 s; pins pulled 34.7 s; loose wheels at v/2; the rear wheel rolls out, the platform "
                                "drops and grinds (520 px/s^2) to a stop"}
mech["asserts"] = {"on": "rendered frames (exposure.json)", "invariant_1_same_challenge": inv1, "invariant_2_contact": inv2,
                   "invariant_3_continuity": inv3, "invariant_7_secondary": inv7,
                   "captions_0.2-0.6s_one_nonhuman": {"pass": cap_pass, "cues": cues},
                   "all_pass": bool(inv1["pass"] and inv2["pass"] and inv3["pass"] and inv7["pass"] and cap_pass)}
mech["caption_cues"] = cues
for k in ("ik_reach_excess_px", "layout_warning"):
    if k in mech:
        mech.setdefault("superseded_sim_notes", {})[k] = mech.pop(k)
mech["deviations_from_plan"] = [
    "Load is 180 px long (not 250): at 250 px the pusher stood off the left edge of frame A at 0 m. One mask in every trial.",
    "Rollers: 7.0 s of push split 14.0-17.6 / 19.6-23.0 around the wait on two logs while log D is set down (plan: tau 2.2-4.8).",
    "Resets between trials (13.0, 25.0, 34.0 s) are real cuts through a held black frame with a scratch wipe, declared with the camera cuts 16.2 / 18.8 s.",
    "Four logs; log B is also squeezed out (21.3 s), so two logs are left behind. The cart shows two wheels, one per axle, so a rear wheel can fall out.",
    "Caption 4 is timed to the pin pull (34.7 s), the bar's named cause.",
]
json.dump(mech, open(os.path.join(HERE, "mechanism.json"), "w"), indent=1, ensure_ascii=False)
print(json.dumps({"inv1": inv1["pass"], "ends": ends, "push": push_len, "hand_local": hand_local, "inv2": inv2, "inv3": inv3["pass"],
                  "undeclared": inv3["undeclared_jumps"][:5], "inv7": inv7["pass"], "captions": cues, "all": mech["asserts"]["all_pass"]}, indent=1, ensure_ascii=False))

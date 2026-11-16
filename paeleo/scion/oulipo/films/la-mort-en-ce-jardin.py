#!/usr/bin/env python3
"""La planche -- after La Mort en ce jardin (Bunuel, 1956; screenplay credits incl. Raymond Queneau).

Montage editor, plan-r1, Direction 1 "Trois sur la planche".  Three articulated grey-card puppets (HANDMADE) cross a
flood channel on a card plank that bears one person, through a multiplane jungle cut from real PD/CC photographs
(FORAGED, U1).  A real 1892 wedding shoe (LACMA, public domain, FORAGED, U3) drifts to the plank foot; picking it up
costs a hand, so the bag changes hands and the crossing order is rewritten.  Version L (shoe at 14 s) and version E
(the same 150 shoe frames 7 s earlier) end with different last crossers.

  python3 films/la-mort-en-ce-jardin.py                 render assets/films/la-mort-en-ce-jardin.mp4 (+ ledger)
  python3 films/la-mort-en-ce-jardin.py --stills 3.5 21.2
  python3 films/la-mort-en-ce-jardin.py --prebuild [N]  render the picture cache with N worker processes
  python3 films/la-mort-en-ce-jardin.py --baseline 10 24  baseline (no shoe) stills of the wide world, local times

Inputs (read, never edited): world-build/compose.py (U1 planes, cameras), performance/rig.py + trace-*.json (U2 FK
rig, gate-checked world traces), performance/puppets.py (U2 card puppets), object-sound layer + stems (U3).
Every frame asserts the plan section 5 invariants; ledger.json records the per-frame audit.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import cv2
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import kit  # noqa: E402

SLUG = "la-mort-en-ce-jardin"
SW = HERE / "swarm" / SLUG
SRC = HERE / "sources" / SLUG
WM = SRC / "world"
OS_ = SRC / "object-sound"
CACHE = SRC / "edit" / "frames"
PW, PH, FPS = 800, 540, 24
PX0 = 80                                   # picture 800x540 pillarboxed at x=80 in 960x540
BAR = (0x1b, 0x1b, 0x1b)
LUMA = np.float32([0.299, 0.587, 0.114])

# ---- unit code (imported, not edited).  compose.py reads its media dirs from argv at import time.
_argv = sys.argv
sys.argv = ["compose", str(WM), str(SW)]
sys.path.insert(0, str(SW / "world-build"))
import compose as WC  # noqa: E402
sys.argv = _argv
sys.path.insert(0, str(SW / "performance"))
import rig as RG  # noqa: E402
import puppets as PP  # noqa: E402
# L-S6 two-shot: U1's near dressing re-laid so no frond crosses either face (declared; same pieces, editor's layout)
WC.NEAR_DRESS["L-S6"] = [("P3_treefern", (610, -30), 0.60, dict(gain=0.95, blur="near", label="near fern right")),
                         ("P3c_leaves", (-400, -390), 0.38, dict(gain=0.78, blur="near", label="near heart leaf top left")),
                         ("P4_root_diag", (-300, 400), 0.95, dict(gain=0.86, blur="near_fg", flip=True, label="near root diagonal low left"))]
# edit-r2: L-S5/E-S4 near dressing re-laid without the heart leaf that hid the receiver at the hand-off (declared)
WC.NEAR_DRESS["L-S5"] = [("P3_treefern", (600, -10), 0.60, dict(gain=0.98, blur="near", label="near: lit tree-fern crown, right edge")),
                         ("P3_treefern", (-330, -250), 0.62, dict(gain=0.55, flip=True, blur="near", label="near: tree-fern crown in shade, top-left corner (edit-r3)")),
                         ("P4_root_diag", (-330, 380), 0.95, dict(gain=0.86, blur="near_fg", flip=True, label="near: root diagonal across the low left"))]
WC.NEAR_DRESS["E-S4"] = WC.NEAR_DRESS["L-S5"]
# edit-r3: a real fluted buttress trunk (U1's Mekong flood-trunk cut, Basile Morin, CC BY-SA 4.0) as a P1 plane behind
# the hand-off in the closes only, drawn in P1 order (before banks, plank and puppets), with P1's close depth blur.
CLOSE_P1 = ("P1", "P1c_flood_trunk", (-150.0, 60.0), 0.80, dict(gain=0.92, flip=True, label="P1 fluted buttress trunk behind the hand-off (close)"))
S = PP.S

# ---- edit-r3: the editor's water and plank (U1's compose.py is not edited; these replace WC.water / WC.plank at run time,
# declared).  water: the foraged plate is mirror-tiled downward (reflect padding of the real water texture) instead of
# repeating its last row, so no edge-clamp streaks at the bottom of the frame; in the closes the water plate carries a
# uniform lighting gain of 0.72 (one gain per piece, as U1's lighting rule) so the white shoe reads against dark water.
# plank: the same scored card, bent along the elastic curve of a simply supported strip under a point load at the
# occupant (instead of U1's 2-segment kink), and, where the trace's clearance falls under 6 px, the water's own
# surface (the same plate rows) laps over the card's top around the foot.
WNOW = dict(water_y=416.0, t=0.0, clearance=None, foot_x=None)


def ed_water(C, cam, water_y, t, wide=True):
    top, m = WC.project_pt((0, water_y), cam)
    top = int(round(top[1]))
    if top >= PH: return top
    Lp, _ = WC.get("W_flood_trunk")
    s = 0.5 * m
    assert s <= WC.MAXUP
    WC.UPS.append(("W_flood_trunk", round(s, 3)))
    flow = (t * 6.0 * m)
    X, Y, D = cam
    x0 = (WC.O[0] + m * (0 - WC.O[0] - X)) - flow
    Wp = cv2.resize(Lp, (int(Lp.shape[1] * s), int(Lp.shape[0] * s)), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
    Wp = np.concatenate([Wp, Wp[:, ::-1]], 1)
    hh = PH - top
    xs = (np.arange(PW) - x0).astype(int) % Wp.shape[1]
    n = Wp.shape[0]
    ry = np.arange(hh) % (2 * n); ry = np.where(ry < n, ry, 2 * n - 1 - ry)      # reflect-tile the real texture downward
    rows = Wp[ry][:, xs]
    src = C[max(top - hh, 0):top][::-1].copy()
    if src.shape[0] < hh:
        k = hh - src.shape[0]; ext = src[::-1] if src.shape[0] else np.zeros((1, PW), np.float32)
        while ext.shape[0] < k: ext = np.concatenate([ext, ext[::-1]], 0)
        src = np.concatenate([src, ext[:k]], 0)
    ph = math.floor(t * 12) / 12
    for yy in range(hh):
        src[yy] = np.roll(src[yy], int(round((1 + yy * 0.03) * math.sin(yy * 0.21 + ph * 7))), axis=0)
    out = rows * 0.68 * 1.08 + WC.gblur(src, 1.0) * 0.32
    if wide:
        fr = int(t * 24) % 120; fr = fr if fr < 60 else 119 - fr
        a = np.asarray(Image.open(f"{WC.WM}/water_motion/shock_troops_{fr + 1:03d}.png").convert("L"), np.float32)[120:240]
        mod = (a - WC.RIPPLE_MEAN) / 255.0
        mod = cv2.resize(mod, (int(320 * 1.6), int(120 * 1.6)), interpolation=cv2.INTER_CUBIC)
        WC.UPS.append(("water_motion shock_troops", 1.6))
        mod = np.concatenate([mod, mod[:, ::-1]], 1)[:, :PW]
        mh = min(hh, mod.shape[0])
        out[:mh] = out[:mh] * (1 + 0.9 * mod[:mh])
    else:
        out = out * 0.78
    out[:3] = out[:3] * 0.7 + 182 * 0.3
    C[top:] = np.clip(out, 0, 255)
    WNOW["rows"] = (top, out)
    return top


def sag_profile(u_arr, a):
    """elastic curve of a simply supported strip, point load at a (0..1), normalised to 1 under the load."""
    a = min(max(a, 0.03), 0.97); b = 1 - a
    x = np.asarray(u_arr, np.float64)
    y = np.where(x <= a, b * x * (1 - b * b - x * x), a * (1 - x) * (1 - a * a - (1 - x) ** 2))
    ya = b * a * (1 - b * b - a * a)
    return y / max(ya, 1e-9)


def ed_plank(C, cam, occupant_u=None, defl=0.0, thick=12, seed=700):
    A0 = np.float32([170, 392]); A1 = np.float32([690, 384])
    u = 0.5 if occupant_u is None else occupant_u
    us = np.linspace(0, 1, 41)
    base = defl if occupant_u is None else 0.0          # empty plank: U1's resting sag, spread evenly
    prof = sag_profile(us, u) * (defl - 2.0) + 2.0 if occupant_u is not None else np.full_like(us, base)
    prof = np.where((us < 0.02) | (us > 0.98), np.minimum(prof, 2.0), prof)
    world_top = [(A0 + (A1 - A0) * q) + np.float32([0, d]) for q, d in zip(us, prof)]
    top = np.float32([WC.project_pt(p, cam)[0] for p in world_top])
    m = WC.project_pt((0, 0), cam)[1]
    th = thick * m
    bot = top + np.float32([0, th])
    pts = np.concatenate([top, bot[::-1]])
    A = WC.poly_mask(pts)
    ys, xs = np.nonzero(A > 0.01)
    if not len(xs): return
    tex = np.zeros((PH, PW), np.float32)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    tex[y0:y1, x0:x1] = WC.card_tex(y1 - y0, x1 - x0, seed)
    yy = np.arange(PH)[:, None].astype(np.float32)
    ytop = np.interp(np.arange(PW), top[:, 0], top[:, 1]).astype(np.float32)[None, :]
    f = np.clip((yy - ytop) / max(th, 1), 0, 1)
    tone = np.where(f < 0.18, 214, 196 - 46 * f) * (1 + 0.04 * tex)
    for j in range(1, 4):
        yl = ytop + th * (0.25 * j)
        tone = np.where(np.abs(yy - yl) < 0.6 * m, tone * 0.86, tone)
    # the wet underside: where the bent card is below the water line it darkens (soaked card)
    wy = WC.project_pt((0, WNOW["water_y"]), cam)[0][1]
    tone = np.where(yy > wy, tone * 0.62, tone)
    C[:] = C * (1 - A) + tone * A
    # water over the card where it is bent under the water line: the channel's own plate rows laid translucently over the
    # submerged part of the card, with a small surge at the foot and a bright meniscus where the surface meets the card.
    if "rows" not in WNOW: return
    top_r, rows = WNOW["rows"]
    n = rows.shape[0]
    xs_ = np.arange(PW, dtype=np.float32)
    ph = math.floor(WNOW["t"] * 12) / 12
    fx = WNOW.get("foot_x")
    surge = np.zeros(PW, np.float32)
    if fx is not None:
        sx = WC.project_pt((fx, 0), cam)[0][0]
        w = np.clip(1 - np.abs(xs_ - sx) / (60 * m), 0, 1)
        surge = 4.0 * m * w * (0.7 + 0.3 * np.sin(xs_ * 0.11 / max(m, 0.5) + ph * 9))
    surf = wy - surge
    sub = A * np.clip((yy - surf[None, :]) / 1.0, 0, 1)
    if sub.max() <= 0.02: return
    tex_w = np.zeros((PH, PW), np.float32)
    for r in range(max(0, int(wy) - 12), min(PH, int(wy) + int(th) + 4)):
        tex_w[r] = rows[min(n - 1, abs(r - top_r))]
    C[:] = C * (1 - 0.72 * sub) + tex_w * 0.72 * sub
    rim = np.clip(1 - np.abs(yy - surf[None, :]) / 1.1, 0, 1) * (WC.gblur(A, 2.0) > 0.05) * (sub.max(0)[None, :] > 0.05)
    C[:] = C * (1 - 0.7 * rim) + 228 * 0.7 * rim


WC.water = ed_water
# edit-r3: shallower depth of field in the closes (depth blur stays per plane, smaller sigmas) for more photographic detail
WC.BLUR["close"].update(P0=0.8, P1=0.35, near=0.6, near_fg=1.1)
WC.plank = ed_plank                                   # approved test-shot card primitives (card scan, mud field, pencil)

TR = {v: json.load(open(SW / "performance" / f"trace-{v}.json")) for v in ("L", "E", "baseline")}
INTR = json.load(open(SW / "interruption.json"))
LAYER = INTR["layer"]
SHOE_T0 = {"L": 14.0, "E": 7.0}
SHOE_K_GRASP = LAYER["grasp"]["k"]          # 135: from here the shoe is parented to B's hand

# ============================================================== timeline (plan section 6, exactly)
SEG = [  # (film t0, t1, id, version, local t0, kind)
    (0.0, 2.0, "T", None, 0.0, "title"),
    (2.0, 5.0, "L-S1", "L", 0.0, "glide"),
    (5.0, 8.0, "L-S2", "L", 3.0, "ledger_write"),
    (8.0, 14.5, "L-S3", "L", 6.0, "wide"),
    (14.5, 20.0, "L-S4", "L", 12.5, "push"),
    (20.0, 22.4, "L-S5", "L", 18.0, "close"),
    (22.4, 23.5, "L-S6", "L", 20.4, "two"),
    (23.5, 25.5, "L-S6i", "L", 21.5, "ledger_rewrite"),
    (25.5, 26.0, "L-S6", "L", 23.5, "two"),
    (26.0, 32.0, "L-S7", "L", 24.0, "wide"),
    (32.0, 38.0, "L-S8", "L", 30.0, "wide"),
    (38.0, 39.5, "card", None, 0.0, "card"),
    (39.5, 42.5, "E-S1", "E", 0.0, "glide"),
    (42.5, 45.5, "E-S2", "E", 3.0, "ledger_write"),
    (45.5, 50.5, "E-S3", "E", 6.0, "wide"),        # edit-r2: E-S3/E-S4/E-S5 boundaries +0.5 s (declared) so that the
    (50.5, 52.9, "E-S4", "E", 11.0, "close"),       # E close starts at the same shoe-layer frame (k 96) and the same
    (52.9, 54.5, "E-S5", "E", 13.4, "ledger_rewrite"),  # pose offset (hand-off +0.4 s) as L-S5: all 150 layer frames

    (54.5, 69.5, "E-S6", "E", 15.0, "wide"),
    (69.5, 73.0, "cmp", None, 0.0, "compare"),
]
SECONDS = 73.0
CAPTIONS = [  # (film t0, t1, text) French, kit serif, #e6e6e6 on a #2d2d2d band (55 %)
    (2.4, 4.9, "La planche n'en porte qu'un."),
    (17.9, 19.4, "C : « Laisse-la. »"),
    (22.5, 23.45, "B : « Je ne peux pas tout porter. »"),
    (35.6, 37.8, "Elle la garde."),
    (66.6, 69.3, "C passe le dernier."),
]
LEDGER_TXT = {
    "old": "1 A · 2 B (sac) · 3 C",
    "L": "1 A · 2 C (sac) · 3 B",
    "E": "1 B (chaussure) · 2 A (sac) · 3 C",
}


def segment(ft):
    for s in SEG:
        if s[0] - 1e-9 <= ft < s[1] - 1e-9:
            return s
    return SEG[-1]


# ============================================================== cameras (U1 world-scene.json)
WIDE_M = 0.955                                    # the whole crossing, both banks and all three puppets in frame
WIDE_CAM = (14.0, -10.0, 1 - 1 / WIDE_M)


def camera(kind, v, lt, sid):
    if kind == "glide":                            # L-S1 / E-S1: U1 glide R->L 60 px at P2, framed like the wides
        X, Y, _ = WC.cam_glide(lt)
        return (X + WIDE_CAM[0], WIDE_CAM[1], WIDE_CAM[2]), "wide", None
    if kind == "push":                             # L-S4: push-in 8 % toward the plank foot (300,380)
        u = WC.smoothstep if hasattr(WC, "smoothstep") else None
        q = min(max((lt - 12.5) / 5.5, 0), 1); q = q * q * (3 - 2 * q)
        M = WIDE_M * (1 + 0.08 * q); D = 1 - 1 / M
        tgt = np.float32([300, 380])
        X0 = np.float32(WIDE_CAM[:2])
        # keep the target where the wide put it:  O + M (tgt - O - X) = O + M0 (tgt - O - X0)
        X = tgt - WC.O - (WIDE_M / M) * (tgt - WC.O - X0)
        return (float(X[0]), float(X[1]), D), "wide", None
    if kind == "close":                            # L-S5 / E-S4 (identical camera, as a function of time since the cut)
        # edit-r2: opens on the hand-off with both heads in frame (B and the receiver: C in L, A in E), then tilts
        # down with B's kneel to U1's plank-foot close (re-centred) for the reach and the grasp.
        rel = round((lt - {"L": 18.0, "E": 11.0}[v]) * FPS) / FPS
        q = RG.smoothstep((rel - 0.5) / 0.55)
        cx = 128 + (200 - 128) * q; cy = 296 + (352 - 296) * q; M = 2.4 + (2.6 - 2.4) * q   # edit-r3: ends 16 px lower (shoe >= 20 px above the frame edge)
        return WC.cam_close((round(cx, 3), round(cy, 3)), round(M, 4)), "close", "L-S5"
    if kind == "two":                              # L-S6: two-shot B and C, framed low enough to keep B's shoe hand in
        return WC.cam_close(TWO_CENTRE, TWO_M), "close", "L-S6"
    if (sid == "L-S8") or (sid == "E-S6" and lt >= LAST_PUSH["E"][0] - 0.01):
        # edit-r3 (declared): the last crossing is seen closer, so that the trace's plank deflection (up to 9 world px)
        # is >= 12 screen px: a push-in at P2 from the wide (m 0.955) to m 1.38, holding the plank's mid-span on screen.
        t0, t1 = LAST_PUSH[v]
        q = RG.smoothstep((lt - t0) / (t1 - t0))
        M = WIDE_M + (LAST_M - WIDE_M) * q; D = 1 - 1 / M
        tgt = np.float32([430, 380])
        X0 = np.float32(WIDE_CAM[:2])
        X = tgt - WC.O - (WIDE_M / M) * (tgt - WC.O - X0)
        X = X + np.float32([40, -20]) * q
        return (float(X[0]), float(X[1]), D), "wide", None
    return WIDE_CAM, "wide", None


LAST_M = 1.38
SAG_X = 2.5
DROP = {}
POSE_FIX = {}
LAST_PUSH = {"L": (30.0, 31.2), "E": (24.0, 25.2)}
TWO_CENTRE, TWO_M = (150, 244), 2.2     # edit-r3: lower and wider, so the shoe stays >= 20 px inside the frame


def mag(cam):
    return 1.0 / (1.0 - cam[2])


def to_screen_fn(cam):
    X, Y, D = cam
    m = mag(cam)
    off = np.float32([X, Y])

    def f(p):
        q = WC.O + m * (np.float32(p) - WC.O - off)
        return (float(q[0]), float(q[1]))
    return f, m


# ============================================================== hair (#41), simulated once per version on twos
def _hair_tables():
    out = {}
    for v in ("L", "E", "baseline"):
        F = TR[v]["frames"]
        sim = PP.HairSim()
        tab = []
        for q in range(len(F) // 2 + 1):
            fr = F[min(q * 2, len(F) - 1)]["people"]["B"]
            tab.append([row[:] for row in sim.step(fr["a"]["head"], tuple(fr["root"]))])
        out[v] = tab
    return out


HAIR = _hair_tables()

# ============================================================== the shoe (U3 cut + layer)
SHOE_RGBA = np.asarray(Image.open(OS_ / "cut" / "shoe_bar_white.png").convert("RGBA"), np.float32)
SHOE_W_WORLD = 50.0
_layer_cache = {}


def shoe_layer(k, hi):
    key = (k, hi)
    if key not in _layer_cache:
        p = (LAYER["hi"] if hi else LAYER["wide"]) % k
        raw = open(p, "rb").read()
        im = Image.open(p).convert("RGBA")
        a = np.asarray(im, np.float32)
        _layer_cache[key] = (a, hashlib.sha256(raw).hexdigest())
        if len(_layer_cache) > 40:
            _layer_cache.pop(next(iter(_layer_cache)))
    return _layer_cache[key]


def layer_k(v, lt):
    if v not in SHOE_T0:
        return None
    k = int(round((lt - SHOE_T0[v]) * FPS))
    return k if 0 <= k < LAYER["frames"] else None


def paste_layer(C, v, lt, cam, framing):
    """the 150-frame drift/bob/ripple layer, identical files in L and E; dy rides each version's water level."""
    k = layer_k(v, lt)
    if k is None:
        return None
    dy = INTR["retrieval"][v]["paste_dy_px_per_k"][k]
    m = mag(cam)
    hi = framing == "close"
    a, h = shoe_layer(k, hi)
    if hi:
        s = m / LAYER["hi_scale"]
        org = np.float32([LAYER["hi_world_origin"][0], LAYER["hi_world_origin"][1]])
    else:
        s = m
        org = np.float32([0, 0])
    dys = int(round(m * dy))       # edit-r2: the water-level ride is a whole-pixel translation of the identical raster
    assert s <= 1.6
    X, Y, _ = cam
    p = WC.O + m * (org - WC.O - np.float32([X, Y]))
    T = np.float32([[s, 0, p[0]], [0, s, p[1]]])
    L = a[..., :3] @ LUMA
    A = a[..., 3] / 255.0
    if s < 1:
        w2, h2 = max(1, int(round(L.shape[1] * s))), max(1, int(round(L.shape[0] * s)))
        L = cv2.resize(L * A, (w2, h2), interpolation=cv2.INTER_AREA)
        A = cv2.resize(A, (w2, h2), interpolation=cv2.INTER_AREA)
        T = np.float32([[1, 0, p[0]], [0, 1, p[1]]])
    else:
        L = L * A
    Lw = cv2.warpAffine(L.astype(np.float32), T, (PW, PH + 64), flags=cv2.INTER_LINEAR)
    Aw = cv2.warpAffine(A.astype(np.float32), T, (PW, PH + 64), flags=cv2.INTER_LINEAR)
    q8 = np.stack([np.clip(Lw, 0, 255), Aw * 255], -1).round().astype(np.uint8)
    rh = hashlib.sha256(q8.tobytes()).hexdigest()       # the screen raster before the water-level translation
    Ls = np.zeros((PH, PW), np.float32); As = np.zeros((PH, PW), np.float32)
    src0, dst0 = max(0, -dys), max(0, dys)
    n = min(PH + 64 - src0, PH - dst0)
    Ls[dst0:dst0 + n] = Lw[src0:src0 + n]; As[dst0:dst0 + n] = Aw[src0:src0 + n]
    C[:] = C * (1 - As) + Ls
    return dict(k=k, file_sha256=h, hi=hi, dy=dy, dy_screen=dys, raster_sha256=rh, cam=[round(c, 4) for c in cam])


THUMB = [(0.45, -6.0), (1.05, -6.6), (1.35, -4.4), (1.05, -2.2), (0.55, -2.6)]


def shoe_in_hand(C3, J, m, t_since, who="B"):
    """FK parenting (edit-r3): the shoe hangs from B's right mitten by its heel counter and turns upright within 0.3 s of
    the grasp, so it is shown whole, in profile (heel, bar strap, rosette), layered over the mitten; the mitten's thumb
    card is re-laid over the heel counter so the shoe reads as held.  Anchor = 0.7 along the hand bone."""
    rise = RG.smoothstep((t_since - 0.04) / 0.28)
    p0, p1, ang = J["hand_n"]
    rot = (1 - rise) * (-ang + 30) + rise * 6
    w = max(4, int(round(SHOE_W_WORLD * m)))
    src = Image.fromarray(SHOE_RGBA.astype(np.uint8), "RGBA")
    sw, sh_ = src.size
    ax, ay = 0.10 * sw, 0.42 * sh_                       # heel counter, in the cut's pixels
    im = src.rotate(rot, expand=True, resample=Image.BICUBIC)
    # where the anchor lands in the rotated, expanded image
    c, s_ = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    dx, dy = ax - sw / 2, ay - sh_ / 2
    rx, ry = dx * c + dy * s_ + im.width / 2, -dx * s_ + dy * c + im.height / 2
    k = w / sw
    im = im.resize((max(1, int(round(im.width * k))), max(1, int(round(im.height * k)))), Image.LANCZOS)
    sh = np.asarray(im, np.float32).copy()
    g = sh[..., :3] @ LUMA
    sh[..., 0] = sh[..., 1] = sh[..., 2] = g                       # exact neutral (the satin's own luma)
    px = p0[0] + (p1[0] - p0[0]) * .7; py = p0[1] + (p1[1] - p0[1]) * .7
    S.over(C3, sh, px - rx * k, py - ry * k)
    PP.lay(C3, [S.bpoly(J, "hand_n", THUMB, m, 1)], PP.TONES[who]["skin"] * .95, 1.9, PP.SEED[who] + 77, 2)
    return (px, py)


# ============================================================== edit-r2: the wet pass (handmade make-up on the cards)
def _poly_alpha(shape_hw, poly, box):
    x0, y0, x1, y1 = box
    m = np.zeros((y1 - y0, x1 - x0), np.uint8)
    pts = np.round((np.float32(poly) - [x0, y0]) * 4).astype(np.int32)
    cv2.fillPoly(m, [pts], 255, cv2.LINE_AA, shift=2)
    return m.astype(np.float32) / 255


def deposit(C3, poly, blobs=(), glints=(), seed=0):
    """charcoal mud thumbed onto a card piece (soft ellipses broken by the handmade mud field), then sweat glints
    (a dab of gloss varnish catching the overcast top light: L 226-236 with a soft darker rim).  Clipped to the piece."""
    H, W = C3.shape[:2]
    P = np.float32(poly)
    x0, y0 = int(max(P[:, 0].min() - 3, 0)), int(max(P[:, 1].min() - 3, 0))
    x1, y1 = int(min(P[:, 0].max() + 4, W)), int(min(P[:, 1].max() + 4, H))
    if x1 - x0 < 3 or y1 - y0 < 3: return
    al = _poly_alpha((H, W), P, (x0, y0, x1, y1))
    h, w = al.shape
    reg = C3[y0:y1, x0:x1]
    mm = S.MUD[(seed * 7) % 380:(seed * 7) % 380 + h, (seed * 13) % 380:(seed * 13) % 380 + w]
    mm = mm[..., 0] if mm.ndim == 3 else mm
    mm = np.pad(mm, ((0, h - mm.shape[0]), (0, w - mm.shape[1])), mode="edge")
    dark = np.zeros((h, w), np.float32)
    for (cx, cy, rx, ry, rot, k) in blobs:
        e = np.zeros((h, w), np.float32)
        cv2.ellipse(e, (int(round(cx - x0)), int(round(cy - y0))), (max(int(rx), 1), max(int(ry), 1)), rot, 0, 360, 1.0, -1, cv2.LINE_AA)
        e = WC.gblur(e, max(rx, ry) * 0.3) * np.clip(0.75 + 0.35 * mm, 0.35, 1.2)
        dark = np.maximum(dark, k * e)
    reg[:] = reg * (1 - (dark * al)[..., None])
    for (cx, cy, rx, ry, rot, v) in glints:
        g = np.zeros((h, w), np.float32)
        cv2.ellipse(g, (int(round(cx - x0)), int(round(cy - y0))), (max(int(round(rx)), 1), max(int(round(ry)), 1)), rot, 0, 360, 1.0, -1, cv2.LINE_AA)
        rim = WC.gblur(g, max(rx, 1.5)) - g
        g = WC.gblur(g, 0.6)
        reg[:] = reg * (1 - (0.25 * np.clip(rim, 0, 1) * al)[..., None])
        a_ = (0.9 * g * al)[..., None]
        reg[:] = reg * (1 - a_) + v * a_


WET = {"A": 0.8, "B": 1.0, "C": 0.9}


def wet_pass_head(C3, J, m, who, wet):
    s = m * PP.HEAD_SCALE
    H = S.hframe(J, s, 1)
    poly = [H(*p) for p in S.HEAD]
    k = min(0.7, 0.6 * wet)
    blobs = [(*H(6.5, -4.5), 4.2 * s, 1.9 * s, -25, k), (*H(3.0, 12.5), 5.5 * s, 1.3 * s, 12, k * 0.9),
             (*H(9.5, -14.5), 3.6 * s, 1.7 * s, 30, k), (*H(-6.0, -8.0), 4.0 * s, 2.4 * s, -40, k * 0.8),
             (*H(15.0, 1.0), 1.3 * s, 2.6 * s, 0, k * 0.55)]
    # edit-r3: the sweat reads as gloss on the card: a damp darkened patch (the varnish soaks the card) with a bright
    # specular dab (L 248) on the brow and on the cheekbone, and a pinpoint on the nose tip
    damp = [(*H(9.0, 14.8), 4.2 * s, 1.6 * s, -6, 0.22 * wet + 0.1), (*H(12.0, 1.0), 3.0 * s, 1.6 * s, 25, 0.22 * wet + 0.1)]
    glints = [(*H(9.0, 15.2), 2.8 * s, 0.75 * s, -6, 248), (*H(12.2, 1.2), 1.9 * s, 0.8 * s, 25, 246),
              (*H(18.2, -2.6), 0.9 * s, 0.7 * s, 0, 246)]
    deposit(C3, poly, blobs + damp, glints, seed=PP.SEED[who] + 401)
    # one more pencilled feature: the ear (a C-curve and its inner fold) and a jaw line
    ear = [H(-2.0 + 2.7 * math.cos(a_), 1.0 + 3.6 * math.sin(a_)) for a_ in np.linspace(-1.7, 1.7, 9)]
    S.pencil(C3, ear, max(1, 0.26 * s), 84, .75, PP.SEED[who] + 431)
    S.pencil(C3, [H(-1.0, -1.5), H(0.6, 1.0), H(-0.6, 3.0)], max(1, 0.22 * s), 92, .7, PP.SEED[who] + 432)
    S.pencil(C3, [H(1.5, -9.5), H(8.0, -13.0), H(14.0, -12.0)], max(1, 0.26 * s), 96, .6, PP.SEED[who] + 433)


def wet_pass_hand(C3, J, m, who, bone, wet):
    poly = S.bpoly(J, bone, PP.HAND, m, 1)
    p0, L, (ux, uy), (nx, ny) = S.bframe(J, bone)
    P = lambda u, v: (p0[0] + u * L * ux + v * m * nx, p0[1] + u * L * uy + v * m * ny)
    k = min(0.72, 0.62 * wet)
    blobs = [(*P(1.3, 1.0), 2.6 * m, 4.5 * m, math.degrees(math.atan2(uy, ux)), k), (*P(0.4, -3.5), 2.2 * m, 1.8 * m, 0, k * 0.85),
             (*P(1.0, 7.5), 1.6 * m, 1.6 * m, 0, k * 0.7)]
    glints = [(*P(1.1, -1.5), 1.6 * m, 0.5 * m, math.degrees(math.atan2(uy, ux)), 230)]
    deposit(C3, poly, blobs, glints, seed=PP.SEED[who] + 409 + (bone == "hand_n"))


# ============================================================== edit-r2: the splash on the last crosser's shins
LAST = {"L": "B", "E": "C"}


def _min_clear(v):
    best = None
    for fr in TR[v]["frames"]:
        if fr["plank_occupant"] == [LAST[v]] and fr.get("clearance_px") is not None:
            if best is None or fr["clearance_px"] < best[0] - 1e-9:
                best = (fr["clearance_px"], fr["t"])
    return best


SPLASH = {v: dict(t=_min_clear(v)[1], clearance_px=_min_clear(v)[0]) for v in ("L", "E")}


def draw_splash(C3, fr, f, m, v, lt):
    """handmade cut-paper splash, animated on twos: a translucent water sheet of torn pale card rising up the shins
    where the plank dips under the last crosser, and a crown of card droplets thrown ballistically (g = 900 px/s^2
    in world px), each a small torn tear-shape that turns as it flies; rings left on the water when they fall."""
    if v not in SPLASH: return None
    t0 = SPLASH[v]["t"] - 0.08
    q = math.floor((lt - t0) * 12) / 12                 # on twos
    if q < 0 or q > 1.1: return None
    P = fr["people"][LAST[v]]
    ax = (P["ankles"][0][0] + P["ankles"][1][0]) / 2
    wy = fr["water_y"]
    rr = np.random.default_rng(1956 if v == "L" else 1957)
    C = C3
    # the water sheet (edit-r3): rises to the knees (~58 world px) by 0.25 s and falls by 0.6 s; its body is the real
    # water plate's own texture (the same foraged rows the channel is made of), with a bright torn crest and pale run-lines,
    # so it reads as a grey sheet of water against the lit fern rather than white card on white leaves.
    hgt = 72 * math.sin(math.pi * min(q / 0.58, 1)) ** 0.8 if q < 0.58 else 0
    if hgt > 1:
        pts = []
        for j in range(17):
            u = j / 16
            x = ax - 38 + 76 * u
            y = wy - 2 - hgt * math.sin(math.pi * u) ** 0.6 * (0.78 + 0.22 * math.sin(u * 17 + q * 9))
            pts.append(f((x, y)))
        pts += [f((ax + 40, wy + 4)), f((ax - 40, wy + 4))]
        P_ = np.float32(pts)
        al = np.zeros(C.shape[:2], np.float32)
        cv2.fillPoly(al, [np.round(P_ * 4).astype(np.int32)], 1.0, cv2.LINE_AA, shift=2)
        al = WC.gblur(al, 0.7)
        tex = np.full(C.shape[:2], 120.0, np.float32)
        if "rows" in WNOW:
            top_r, rows = WNOW["rows"]
            n = rows.shape[0]
            for r in range(max(0, int(P_[:, 1].min()) - 2), min(C.shape[0], top_r)):
                tex[r] = rows[min(n - 1, (top_r - r) % max(n, 1))]
        tex = tex * 0.95 + 18
        C[:] = C * (1 - 0.88 * al[..., None]) + (0.88 * al * tex)[..., None]
        crest = [tuple(p_) for p_ in P_[:17]]
        S.pencil(C, crest, max(1.5, 1.1 * m), 238, .95, 31)
        for j in range(3):                                # pale run-lines down the sheet
            u0 = 0.27 + 0.21 * j + 0.04 * math.sin(q * 11 + j)
            a_ = f((ax - 38 + 76 * u0, wy - 1)); b_ = f((ax - 38 + 76 * u0 + 2, wy - 2 - hgt * 0.85 * math.sin(math.pi * u0) ** 0.6))
            S.pencil(C, [a_, b_], max(1, 0.45 * m), 214, .4, 40 + j)
    # droplets
    for j in range(26):
        vx = rr.uniform(-120, 120); vy = -rr.uniform(170, 360); r0 = rr.uniform(2.6, 5.6); spin = rr.uniform(-600, 600)
        x0 = ax + rr.uniform(-24, 24)
        tq = q - rr.uniform(0, 0.12)
        if tq <= 0: continue
        x = x0 + vx * tq; y = wy - 3 + vy * tq + 450 * tq * tq
        if y > wy + 1:
            # landed: a broken ring on the water (pencil arc on the water plane)
            tl = tq - (-(vy) + math.sqrt(vy * vy + 4 * 450 * 4)) / 900
            if 0 < tl < 0.35:
                rad = 3 + 30 * tl
                arc = [f((x + rad * math.cos(a), wy + 2 + 0.3 * rad * math.sin(a))) for a in np.linspace(0.3, 2.8, 9)]
                S.pencil(C, arc, max(1, 0.45 * m), 190, .55 * (1 - tl / 0.35), 70 + j)
            continue
        ang = math.radians(spin * tq)
        shape = [(0, -1.6), (0.9, -0.2), (0.7, 0.8), (0, 1.1), (-0.7, 0.8), (-0.9, -0.2)]
        poly = [f((x + r0 * (px * math.cos(ang) - py * math.sin(ang)), y + r0 * (px * math.sin(ang) + py * math.cos(ang)))) for px, py in shape]
        PP.lay(C, [poly], 230, 0, 900 + j, 1, edge=0.9)
    return dict(splash_t=round(q, 4), sheet_height_world_px=round(hgt, 2))


# ============================================================== puppets in the world (P2 callback)
DRAW_ORDER = ("A", "C", "B")


def draw_people(C, fr, cam, v, lt, audit):
    f, m = to_screen_fn(cam)
    C3 = np.repeat(C[..., None], 3, 2)
    people = fr["people"]
    light = (f((0, 150))[1], f((0, RG.N_GROUND))[1])
    shoe_h = fr["shoe"][0] if fr["shoe"] else None
    bag_h = fr["bag"][0]
    order = sorted(DRAW_ORDER, key=lambda w: (people[w]["bank"] == "P", people[w]["root"][1]))
    Js = {}
    errs = []
    for who in order:
        P = people[who]
        ang = P["a"]
        if who == "B" and POSE_FIX.get("on") and lt < 21.75:
            # edit-r3 (declared): in the L-S6 two-shot B's free far arm is re-keyed (open palm at chest height) instead of
            # U2's raised forearm whose elbow hid behind her head; no grip is involved, the trace is otherwise unchanged.
            ang = dict(ang); ang.update(upper_f=48, fore_f=-12, hand_f=-22)
        Jw = RG.fk((P["root"][0], P["root"][1] + DROP.get(who, 0.0)), ang)
        errs.append(max(RG.bone_error(Jw).values()))
        J = {b: (f(p0), f(p1), a) for b, (p0, p1, a) in Jw.items()}
        errs.append(max(RG.bone_error(J, m).values()))
        Js[who] = J
    for who in order:
        P = people[who]; J = Js[who]; ex = P["expr"]
        mud = 1.0
        if who == "B": mud = 1.0
        if who == "C": mud = 1.15
        # the splash on the last crosser's shins: the mud deposit darkens once she or he has been wetted
        last = {"L": "B", "E": "C"}.get(v)
        if who == last and v in ("L", "E"):
            t_spl = SPLASH[v]["t"]
            mud *= 1.0 + 0.5 * RG.smoothstep((lt - t_spl) / 0.6)
        contact = None
        if P["bank"] != "P":
            ay = max(P["ankles"][0][1], P["ankles"][1][1]); ax = (P["ankles"][0][0] + P["ankles"][1][0]) / 2
            sx, sy = f((ax, ay + 3))
            contact = (sx, sy, 30 * m, 4 * m, .45)
        hair = HAIR[v][min(int(math.floor(lt * 12 + 1e-6)), len(HAIR[v]) - 1)] if who == "B" else None
        cb = None
        if who == "B" and shoe_h == "B.R":
            tr = [e for e in TR[v]["events"] if e["event"] == "retrieve"][0]["t"]
            cb = tr
        bw, bhand = bag_h.split(".")
        bag_high = False
        if bw == who:
            bone = RG.HAND_OF[bhand]
            hx, hy = J[bone][1]
            bag_high = hy < J["neck"][1][1] + 30 * m          # held at head height: layered behind the head (edit-r3)
            if bag_high:
                PP.bag_piece(C3, hx, hy - 4 * m, 0.95 * m, 4 if who == "B" else -6)
        PP.draw_figure(C3, J, m, who, 1, mud=mud, gaze=ex["gaze"], brow=ex["brow"], mouth=ex["mouth"], hair=hair,
                       light=light, contact=contact)
        wet_pass_head(C3, J, m, who, WET[who] * mud)
        wet_pass_hand(C3, J, m, who, "hand_f", WET[who] * mud)
        wet_pass_hand(C3, J, m, who, "hand_n", WET[who] * mud)
        if cb is not None:                  # the shoe, parented to B's right hand, over the mitten (never muddied)
            audit["shoe_screen"] = shoe_in_hand(C3, J, m, lt - cb)
        if bw == who:                       # the bag hangs from the holder's hand bone; hand card re-laid over the strap
            if not bag_high:
                PP.bag_piece(C3, hx, hy - 4 * m, 0.95 * m, 4 if who == "B" else -6)
            PP.lay(C3, [S.bpoly(J, bone, PP.HAND, m, 1)], PP.TONES[who]["skin"] * .95, 1.7, PP.SEED[who] + 31, 2)
            wet_pass_hand(C3, J, m, who, bone, WET[who] * mud)
            audit["bag_screen"] = (hx, hy)
    if v in SPLASH and fr["plank_occupant"] == [LAST[v]]:
        sp = draw_splash(C3, fr, f, m, v, lt)
        if sp: audit["splash"] = sp
    C[:] = C3 @ LUMA
    audit["rig_error_px"] = max(errs)
    return Js


def ledger_patch(C, cam, state):
    """the torn ledger card lying on the near bank (world 18..104 x 404..436): continuity with the inserts."""
    f, m = to_screen_fn(cam)
    pts = np.float32([f(p) for p in ((18, 408), (100, 403), (106, 432), (24, 438))])
    A = WC.poly_mask(pts, 0.8)
    if A.max() <= 0: return
    C[:] = C * (1 - A) + 188 * A
    for j, y in enumerate((413, 421, 429)):
        if j == 2 and state == "old": break
        x1 = 92 if j == 0 else 86
        a, b = f((28, y)), f((x1, y - 1))
        S.pencil(C[..., None], [a, b], max(1, 0.9 * m), 70, .8, 3 + j)
    if state != "old":
        a, b = f((26, 414)), f((94, 411))
        S.pencil(C[..., None], [a, b], max(1, 1.1 * m), 46, .9, 9)


def world_frame(v, lt, kind, sid, baseline_world=False):
    """one picture frame of the world (grey float 540x800) + its audit record."""
    F = TR[v]["frames"]
    i = min(int(round(lt * FPS)), len(F) - 1)
    fr = F[i]
    cam, framing, shot = camera(kind, v, lt, sid)
    occ = fr["plank_occupant"]
    occ_u = None
    if occ:
        x = fr.get("occupant_x") or fr["people"][occ[0]]["root"][0]
        occ_u = min(max((x - 170.0) / 520.0, 0.02), 0.98)
    hand = None
    for who in occ:
        for hnd, g in fr["people"][who]["grips"].items():
            if g == "liana": hand = tuple(fr["people"][who]["hands"][hnd])
    audit = {}

    # edit-r3 (declared, the critic's "exaggerate the sag"): the card plank is drawn with SAG_X times the trace's
    # deflection beyond its 2 px resting sag; the occupant is lowered with it (the same FK pose, root moved down by the
    # extra sag under the foot) so the boots stay on the card. The ledger keeps the trace's values.
    defl_draw = fr["plank_deflection_px"]
    extra = 0.0
    if occ:
        extra = max(0.0, fr["plank_deflection_px"] - 2.0) * (SAG_X - 1.0)
        defl_draw = fr["plank_deflection_px"] + extra
        if hand is not None: hand = (hand[0], hand[1] + extra)
    DROP.clear()
    POSE_FIX["on"] = (sid == "L-S6")
    if occ: DROP[occ[0]] = extra
    WNOW.update(water_y=fr["water_y"], t=lt, clearance=None, foot_x=None)
    WNOW.pop("rows", None)
    if occ and v in LAST and occ == [LAST[v]] and fr.get("clearance_px") is not None:
        P = fr["people"][occ[0]]
        WNOW.update(clearance=fr["clearance_px"] - extra, foot_x=max(P["ankles"][0][0], P["ankles"][1][0]) + 6)

    def p2(C, cam_):
        # edit-r3: the grey-bar ledger placard on the near bank is removed (critic: a generic stand-in)
        if not baseline_world:
            audit["layer"] = paste_layer(C, v, lt, cam_, framing)
        draw_people(C, fr, cam_, v, lt, audit)

    extra = framing == "close" and shot == "L-S5"
    if extra:
        WC.LAYOUT.insert(max(i for i, e in enumerate(WC.LAYOUT) if e[0] == "P1") + 1, CLOSE_P1)
    try:
        C, ups = WC.render(cam, t=lt, framing=framing, shot=shot, water_y=fr["water_y"], occupant_u=occ_u,
                           defl=defl_draw, hand=hand, p2_cb=p2)
    finally:
        if extra: WC.LAYOUT.remove(CLOSE_P1)
    audit["max_plate_scale"] = max(s for _, s in ups) if ups else 0
    audit["plank_deflection_drawn_px"] = round(defl_draw, 3)
    audit["drawn_clearance_px"] = None if WNOW.get("clearance") is None else round(WNOW["clearance"], 3)
    audit["cam"] = [round(c, 4) for c in cam]
    audit["framing"] = framing
    return C, fr, audit


# ============================================================== handmade cards and the pencil ledger
CARDSCAN = np.asarray(Image.open(SRC / "test-shot" / "paper" / "Cardboard_546867_jpg.jpg").convert("L"), np.float32)
_hp = CARDSCAN - cv2.GaussianBlur(CARDSCAN, (0, 0), 5)
CARD_FIBRE = np.clip(_hp / (_hp.std() + 1e-6), -3, 3)
_lo = cv2.GaussianBlur(CARDSCAN, (0, 0), 40)
CARD_LOW = (_lo - _lo.mean()) / (_lo.std() + 1e-6)
BANKPHOTO = np.asarray(Image.open(WM / "cut" / "B_litter_ficus.png").convert("RGBA"), np.float32)


def card_ground(tone=176, seed=0, w=PW, h=PH):
    """grey card from the CC0 cardboard scan's own fibre (monotone, neutral), no filter grain."""
    r = np.random.default_rng(seed)
    y0 = r.integers(0, CARDSCAN.shape[0] - h); x0 = r.integers(0, CARDSCAN.shape[1] - w)
    return tone * (1 + 0.035 * CARD_FIBRE[y0:y0 + h, x0:x0 + w] + 0.03 * CARD_LOW[y0:y0 + h, x0:x0 + w])


def zhang_suen(img):
    """thinning (Zhang-Suen) of a binary glyph mask -> 1 px skeleton (numpy, iterative)."""
    I = (img > 0).astype(np.uint8)
    I = np.pad(I, 1)
    while True:
        changed = False
        for step in (0, 1):
            P = I
            p2, p3, p4 = P[:-2, 1:-1], P[:-2, 2:], P[1:-1, 2:]
            p5, p6, p7 = P[2:, 2:], P[2:, 1:-1], P[2:, :-2]
            p8, p9 = P[1:-1, :-2], P[:-2, :-2]
            nb = [p2, p3, p4, p5, p6, p7, p8, p9]
            B = sum(x.astype(np.int32) for x in nb)
            seq = nb + [p2]
            A = sum(((seq[j] == 0) & (seq[j + 1] == 1)).astype(np.int32) for j in range(8))
            c = P[1:-1, 1:-1] == 1
            if step == 0:
                cond = c & (B >= 2) & (B <= 6) & (A == 1) & (p2 * p4 * p6 == 0) & (p4 * p6 * p8 == 0)
            else:
                cond = c & (B >= 2) & (B <= 6) & (A == 1) & (p2 * p4 * p8 == 0) & (p2 * p6 * p8 == 0)
            if cond.any():
                I[1:-1, 1:-1][cond] = 0
                changed = True
        if not changed:
            break
    return I[1:-1, 1:-1]


class Handwriting:
    """a line of pencil lettering revealed stroke by stroke.  The letterforms come from the kit serif glyphs; the
    pen path is their skeleton, traced component by component left to right (depth-first along each stroke), and
    every glyph pixel is laid when the pen passes its nearest skeleton point.  The graphite is broken by the card's
    real tooth.  Pen lifts between strokes cost 3 path units."""

    def __init__(self, text, size, seed=0, slant=0.12):
        f = kit.font("serif", size)
        d0 = ImageDraw.Draw(Image.new("L", (10, 10)))
        bb = d0.textbbox((0, 0), text, font=f)
        w, h = bb[2] - bb[0] + 24, bb[3] - bb[1] + 24
        im = Image.new("L", (w + int(h * slant) + 8, h), 0)
        ImageDraw.Draw(im).text((12 - bb[0] + int(h * slant), 12 - bb[1]), text, font=f, fill=255)
        im = im.transform(im.size, Image.AFFINE, (1, slant, 0, 0, 1, 0), resample=Image.BICUBIC)
        g = np.asarray(im, np.float32) / 255
        self.mask = g
        sk = zhang_suen(g > 0.45)
        n, lab = cv2.connectedComponents(sk, connectivity=8)
        comps = []
        for c in range(1, n):
            ys, xs = np.nonzero(lab == c)
            comps.append((xs.min(), c))
        comps.sort()
        rank = np.full(sk.shape, -1.0, np.float32)
        order = []
        u = 0.0
        for _, c in comps:
            pts = set(zip(*np.nonzero(lab == c)))
            ends = [p for p in pts if sum((p[0] + dy, p[1] + dx) in pts for dy in (-1, 0, 1) for dx in (-1, 0, 1)) == 2]
            start = min(ends or pts, key=lambda p: (p[1], p[0]))
            stack = [start]; seen = set()
            while stack:
                p = stack.pop()
                if p in seen: continue
                seen.add(p)
                rank[p] = u; order.append((p[1], p[0], u)); u += 1
                nb = [(p[0] + dy, p[1] + dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy or dx)]
                for q in sorted((q for q in nb if q in pts and q not in seen), key=lambda q: -abs(q[0] - p[0]) - abs(q[1] - p[1])):
                    stack.append(q)
            u += 3
        self.total = u
        self.order = np.float32(order)
        inv = np.where(rank >= 0, 0, 1).astype(np.uint8)
        _, labels = cv2.distanceTransformWithLabels(inv, cv2.DIST_L2, 3, labelType=cv2.DIST_LABEL_PIXEL)
        zy, zx = np.nonzero(inv == 0)
        lab_rank = np.zeros(labels.max() + 1, np.float32)
        lab_rank[labels[zy, zx]] = rank[zy, zx]
        self.prank = lab_rank[labels]
        self.size = (im.size[0], im.size[1])

    def draw(self, C, x, y, u, tone=62, seed=0, alpha=0.92):
        """lay the lettering revealed up to fraction u at top-left (x, y); returns the pen tip (screen) or None."""
        if u <= 0: return None
        cur = u * self.total
        m = self.mask * (self.prank <= cur)
        h, w = m.shape
        x, y = int(round(x)), int(round(y))
        tooth = np.clip(0.8 + 0.18 * CARD_FIBRE[(seed * 7) % 300:(seed * 7) % 300 + h, (seed * 11) % 300:(seed * 11) % 300 + w], 0.45, 1)
        a = np.clip(m * tooth * alpha, 0, 1)
        reg = C[y:y + h, x:x + w]
        a = a[:reg.shape[0], :reg.shape[1]]
        reg[:] = reg * (1 - a) + tone * a
        if u >= 1: return None
        j = int(np.searchsorted(self.order[:, 2], cur))
        j = min(max(j, 0), len(self.order) - 1)
        return (x + self.order[j, 0], y + self.order[j, 1])


def pencil_line(C, p0, p1, u, width=2.2, tone=48, seed=0, wob=1.4):
    """a ruled pencil stroke drawn up to fraction u (strike-through, underline)."""
    if u <= 0: return None
    n = 40
    t = np.linspace(0, u, n)
    r = np.random.default_rng(seed)
    ph = r.uniform(0, 6.28)
    pts = [(p0[0] + (p1[0] - p0[0]) * q, p0[1] + (p1[1] - p0[1]) * q + wob * math.sin(q * 9 + ph)) for q in t]
    S.pencil(C[..., None], pts, width, tone, .92, seed)
    return pts[-1]


def hand_with_pencil(C, tip, who, seed=0):
    """the writer's hand card (the puppet's own hand piece, at insert scale) holding a card pencil at the tip."""
    if tip is None: return
    tx, ty = tip
    s = 5.0
    C3 = np.repeat(C[..., None], 3, 2)
    # pencil: a pale card stick with a graphite point, lying at 58 deg to the line
    ang = math.radians(-58)
    ux, uy = math.cos(ang), math.sin(ang)
    base = (tx + ux * 22, ty + uy * 22); end = (tx + ux * 190, ty + uy * 190)
    nx, ny = -uy, ux
    body = [(base[0] + nx * 7, base[1] + ny * 7), (end[0] + nx * 7, end[1] + ny * 7), (end[0] - nx * 7, end[1] - ny * 7), (base[0] - nx * 7, base[1] - ny * 7)]
    cone = [(tx, ty), body[0], body[3]]
    PP.lay(C3, [body], 168, 0.4, seed + 3, 4)
    PP.lay(C3, [cone], 196, 0.2, seed + 4, 2)
    PP.lay(C3, [[(tx, ty), (tx + ux * 8 + nx * 2.5, ty + uy * 8 + ny * 2.5), (tx + ux * 8 - nx * 2.5, ty + uy * 8 - ny * 2.5)]], 52, 0, seed + 5, 0)
    # hand: the HAND card piece of the puppet, on a short wrist bone pointing at the pencil
    hx, hy = tx + ux * 70, ty + uy * 70
    J = {"hand": ((hx + ux * 44 + nx * 10, hy + uy * 44 + ny * 10), (hx - ux * 10, hy - uy * 10), math.degrees(math.atan2(-uy, -ux)))}
    p0, p1, a = J["hand"]
    L = math.dist(p0, p1)
    pts = [(p0[0] + (p1[0] - p0[0]) * hx_ + (-(p1[1] - p0[1]) / L) * hy_ * s * 1.0, p0[1] + (p1[1] - p0[1]) * hx_ + ((p1[0] - p0[0]) / L) * hy_ * s * 1.0)
           for hx_, hy_ in PP.HAND]
    tone = PP.TONES[who]["skin"]
    PP.lay(C3, [pts], tone * .95, 1.8, PP.SEED[who] + 40, 6,
           sweat=[(p1[0] * .7 + p0[0] * .3, p1[1] * .7 + p0[1] * .3, 6, 2, a, 212)])
    sleeve = [(p0[0] + nx * 26, p0[1] + ny * 26), (p0[0] + ux * 120 + nx * 34, p0[1] + uy * 120 + ny * 34),
              (p0[0] + ux * 120 - nx * 34, p0[1] + uy * 120 - ny * 34), (p0[0] - nx * 26, p0[1] - ny * 26)]
    PP.lay(C3, [sleeve], PP.TONES[who]["shirt"] * .9, 1.2, PP.SEED[who] + 41, 6)
    S.brad(C3, p0[0], p0[1], 4)
    C[:] = C3 @ LUMA


_HW = {}


def hw(key, text, size):
    if key not in _HW: _HW[key] = Handwriting(text, size, seed=len(_HW))
    return _HW[key]


def grade_plate(L):
    """the one monotone curve per plate (plan section 0): p2/p98 -> L35/220."""
    p2, p98 = np.percentile(L, 2), np.percentile(L, 98)
    return np.clip(35 + (L - p2) * 185 / max(p98 - p2, 1), 0, 255)


BANK_FLOOR = SRC / "test-shot" / "plates" / "Buttress_roots_JPG.jpg"      # Patti Neumann, CC BY-SA 3.0


def insert_ground():
    """the ledger insert: the torn card lying on the photographed root-laced forest floor (Buttress roots.JPG)."""
    L = np.asarray(Image.open(BANK_FLOOR).convert("L"), np.float32)
    L = grade_plate(L)
    s = PW / L.shape[1]                                       # 0.625: downscale only
    L = cv2.resize(L, (PW, int(L.shape[0] * s)), interpolation=cv2.INTER_AREA)
    y0 = (L.shape[0] - PH) // 2
    G = L[y0:y0 + PH].copy() * 0.80
    G = WC.gblur(G, 1.0)                                     # the floor is behind the card's focus plane (depth blur)
    card = card_ground(184, seed=5)
    pts = np.float32([(70, 92), (300, 70), (520, 84), (742, 96), (752, 250), (738, 452), (420, 468), (96, 458), (60, 300)])
    r = np.random.default_rng(4)
    tear = []
    for a_, b_ in zip(pts, np.roll(pts, -1, 0)):
        for q in np.linspace(0, 1, 14, endpoint=False):
            p = a_ + (b_ - a_) * q
            tear.append(p + r.normal(0, 2.2, 2))
    A = WC.poly_mask(np.float32(tear), 0.9)
    sh = np.roll(np.roll(A, 7, 0), 6, 1)
    G = G * (1 - 0.45 * WC.gblur(sh, 6))
    ed = np.clip(1 - WC.gblur(A, 5) * 1.5, 0, 1) * (A > 0.1)
    card = card * (1 - 0.18 * ed)
    # charcoal mud thumbed onto the card's edge (handmade deposit, the test-shot mud field)
    mud = S.MUD[:PH, :PW, 0] if S.MUD.ndim == 3 else S.MUD[:PH, :PW]
    card = card * (1 - 0.10 * np.clip(mud * 0.5 + ed * 1.4, 0, 2))
    return G * (1 - A) + card * A


INSERT_BASE = None


def ledger_insert(ft, kind, v, lt, writer):
    global INSERT_BASE
    if INSERT_BASE is None: INSERT_BASE = insert_ground()
    C = INSERT_BASE.copy()
    old = hw("old", LEDGER_TXT["old"], 58)
    X0, Y0 = 118, 150
    tip = None
    if kind == "ledger_write":                          # 3.0-5.6 local: the original order, letter by letter
        u = (lt - 3.0) / 2.6
        tip = old.draw(C, X0, Y0, min(max(u, 0), 1), seed=1)
        who = "A"
    else:
        old.draw(C, X0, Y0, 1.0, seed=1)
        t0 = {"L": 21.5, "E": 13.4}[v]
        q = lt - t0
        w_old = old.size[0]
        y_mid = Y0 + old.size[1] * 0.56
        u_strike = q / (8 / FPS)                         # struck through in 8 frames
        e = pencil_line(C, (X0 + 10, y_mid), (X0 + w_old - 14, y_mid - 4), min(max(u_strike, 0), 1), 3.0, 40, 11)
        tip = e if 0 < u_strike < 1 else None
        new = hw(v, LEDGER_TXT[v], 58 if v == "L" else 50)
        u_new = (q - 0.45) / (1.45 if v == "L" else 1.05)
        if u_new > 0:
            tip = new.draw(C, X0, Y0 + 118, min(u_new, 1), seed=2) or tip
        who = writer
    hand_with_pencil(C, tip, who, seed=7)
    return C


def title_card(ft):
    C = card_ground(176, seed=1)
    a = hw("title", "La planche", 96)
    b = hw("sub", "trois · un sac · une planche", 40)
    a.draw(C, (PW - a.size[0]) / 2, 170, min(max((ft - 0.15) / 1.1, 0), 1), tone=54, seed=3)
    b.draw(C, (PW - b.size[0]) / 2, 300, min(max((ft - 1.0) / 0.85, 0), 1), tone=70, seed=4)
    return C


def plus_tot_card(ft):
    C = card_ground(170, seed=2)
    a = hw("plustot", "Plus tôt", 92)
    a.draw(C, (PW - a.size[0]) / 2, (PH - a.size[1]) / 2 - 10, min(max(ft / 0.9, 0), 1), tone=54, seed=5)
    return C


CMP_LINES = [("sans chaussure :", "1 A · 2 B (sac) · 3 C", "C"), ("14 s :", "1 A · 2 C (sac) · 3 B", "B"), ("7 s :", "1 B · 2 A (sac) · 3 C", "C")]


def compare_card(ft):
    C = card_ground(180, seed=3)
    for j, (lab, txt, last) in enumerate(CMP_LINES):
        y = 130 + j * 110
        l = hw(f"cmpl{j}", lab, 34); o = hw(f"cmpo{j}", txt, 44)
        l.draw(C, 60, y + 10, 1.0, tone=86, seed=10 + j)
        o.draw(C, 300, y, 1.0, tone=58, seed=20 + j)
        # the last crosser underlined, one after another
        u = (ft - 0.35 - 0.55 * j) / 0.4
        x1 = 300 + o.size[0] - 34
        pencil_line(C, (x1 - 20, y + o.size[1] - 8), (x1 + 22, y + o.size[1] - 10), min(max(u, 0), 1), 2.6, 44, 30 + j, 0.8)
    return C


# ============================================================== captions and pillarbox
def compose_960(Cgray, ft):
    pic = np.clip(Cgray, 0, 255).astype(np.uint8)
    out = np.empty((540, 960, 3), np.uint8)
    out[:] = BAR
    out[:, PX0:PX0 + PW] = pic[..., None]
    img = Image.fromarray(out)
    for t0, t1, s in CAPTIONS:
        if t0 <= ft < t1:
            a = min(1.0, (ft - t0) / 0.2, (t1 - ft) / 0.2)
            d = ImageDraw.Draw(img, "RGBA")
            f = kit.font("serif", 24)
            bb = d.textbbox((0, 0), s, font=f)
            tw, th = bb[2] - bb[0], bb[3] - bb[1]
            y = 540 - 46
            d.rectangle([480 - tw / 2 - 14, y - th / 2 - 10, 480 + tw / 2 + 14, y + th / 2 + 12], fill=(0x2d, 0x2d, 0x2d, int(140 * a)))
            d.text((480, y), s, font=f, fill=(0xe6, 0xe6, 0xe6, int(255 * a)), anchor="mm")
    return img


# ============================================================== one film frame (+ audit)
INV_LOG = []


def check_invariants(v, fr, audit):
    occ = fr["plank_occupant"]
    assert len(occ) <= 1, ("plank", fr["t"], occ)                                     # 1
    for who, P in fr["people"].items():
        used = [g for g in P["grips"].values() if g != "free"]
        assert len(used) <= 2                                                         # 2
        if who in occ:
            assert list(P["grips"].values()).count("liana") == 1, ("liana", who, fr["t"])
    assert len(fr["bag"]) == 1                                                         # 3
    if fr["shoe"]: assert len(fr["shoe"]) == 1
    holders = [g for P in fr["people"].values() for g in P["grips"].values()]
    assert holders.count("bag") == 1
    if fr["shoe"] and fr["shoe"][0] != "water": assert holders.count("shoe") == 1
    assert fr["bag_bottom_y"] < fr["water_y"] or not fr["bag_over_water"], ("bag wet", fr["t"])  # 4
    assert fr["bag_bottom_y"] < fr["water_y"]
    assert audit.get("rig_error_px", 0) < 0.5, audit.get("rig_error_px")                 # bone lengths
    assert audit.get("max_plate_scale", 0) <= 1.6 + 1e-6


def render_frame(k):
    """returns (960x540 PIL image, audit dict) for film frame k."""
    ft = k / FPS
    t0, t1, sid, v, l0, kind = segment(ft)
    lt = l0 + (ft - t0)
    rec = dict(k=k, film_t=round(ft, 4), shot=sid, version=v, local_t=round(lt, 4) if v else None, kind=kind)
    if kind == "title": C = title_card(ft)
    elif kind == "card": C = plus_tot_card(ft - t0)
    elif kind == "compare": C = compare_card(ft - t0)
    elif sid in ("E-S1", "E-S2"):
        # = L-S1 / L-S2: the same local frames rendered from the same (L) world state -> byte-identical
        kL = int(round((2.0 + lt) * FPS)) if sid == "E-S1" else int(round((5.0 + lt - 3.0) * FPS))
        img, recL = render_frame(kL)
        rec.update({q: recL[q] for q in recL if q not in ("k", "film_t", "shot", "version")})
        rec["same_as_k"] = kL
        rec["displayed_world"] = "L"
        return img, rec
    elif kind in ("ledger_write", "ledger_rewrite"):
        C = ledger_insert(ft, kind, v, lt, {"L": "B", "E": "A"}[v])
        fr = TR[v]["frames"][min(int(round(lt * FPS)), len(TR[v]["frames"]) - 1)]
        check_invariants(v, fr, {})
        rec.update(world_record(v, fr))
    else:
        C, fr, audit = world_frame(v, lt, kind, sid)
        check_invariants(v, fr, audit)
        rec.update(world_record(v, fr))
        rec.update(rig_error_px=round(audit["rig_error_px"], 4), cam=audit["cam"], framing=audit["framing"],
                   max_plate_scale=audit["max_plate_scale"])
        if audit.get("layer"): rec["shoe_layer"] = audit["layer"]
        if audit.get("splash"): rec["splash"] = audit["splash"]
        if fr["shoe"] == ["B.R"]:
            sx, sy = audit.get("shoe_screen", (-999, -999))
            rec["shoe_visible"] = bool(0 <= sx < PW and 0 <= sy < PH)
            rec["shoe_screen"] = [round(sx, 1), round(sy, 1)]
        else:
            rec["shoe_visible"] = bool(audit.get("layer")) and layer_k(v, lt) < SHOE_K_GRASP
    img = compose_960(C, ft)
    return img, rec


def world_record(v, fr):
    return dict(world_t=fr["t"], water_y=fr["water_y"], plank_occupant=fr["plank_occupant"],
                plank_deflection_px=fr["plank_deflection_px"], bag=fr["bag"][0], shoe=fr["shoe"][0] if fr["shoe"] else None,
                bag_bottom_y=fr["bag_bottom_y"], hands={w: P["grips"] for w, P in fr["people"].items()},
                banks={w: P["bank"] for w, P in fr["people"].items()})


# ============================================================== cache, parallel prebuild, film
def cache_path(k): return CACHE / f"f{k:04d}.png"


def cached(k):
    p = cache_path(k)
    rp = CACHE / f"f{k:04d}.json"
    if p.exists() and rp.exists():
        return Image.open(p).convert("RGB"), json.load(open(rp))
    img, rec = render_frame(k)
    CACHE.mkdir(parents=True, exist_ok=True)
    img.save(p, compress_level=1)
    rec["sha1_rgb"] = hashlib.sha1(np.asarray(img).tobytes()).hexdigest()
    json.dump(rec, open(rp, "w"))
    return img, rec


def _work(ks):
    for k in ks: cached(k)
    return len(ks)


def prebuild(nproc):
    from multiprocessing import Pool
    total = int(round(SECONDS * FPS))
    todo = [k for k in range(total) if not cache_path(k).exists()]
    chunks = [todo[i::nproc * 4] for i in range(nproc * 4)]
    with Pool(nproc) as pool:
        for n in pool.imap_unordered(_work, chunks):
            print("  chunk", n, flush=True)


# ---------------------------------------------------------------- sound (U3 stems: foraged beds + declared foley)
def decode_wav(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "2", "-ar", str(kit.RATE), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)


SOUND_REC = {}


def sound(mix):
    """edit-r2: U3's stems rebuilt on the edit-r2 timeline (edit-build/edit_sound.py): foraged beds decoded with ffmpeg,
    U3's synthesized foley generators, rustle and splash locked to the ledger's frames.  Each stem is placed with mix.add."""
    sys.path.insert(0, str(SW / "edit-build"))
    import edit_sound as ES
    stems, mixg, rec = ES.build(TR, SPLASH, kit.Mix, kit.RATE, SEG_E_REWRITE=(52.9, 54.5))
    SOUND_REC.update(rec)
    for name in ("water", "jungle", "foley"):
        x = stems[name]
        # stereo stems placed as L and R channels (pan -1 / +1 keep each channel on its side at unity after kit's 1.414)
        mix.add(x[:, 0] / 1.414, 0.0, 1.0, pan=-1.0)
        mix.add(x[:, 1] / 1.414, 0.0, 1.0, pan=1.0)
    write_sound_json(rec)


def write_sound_json(rec):
    p = SW / "sound.json"
    old = json.load(open(p))
    if old.get("revision", "").startswith("os-") or "editor_revision" not in old:
        bk = SW / "sound-u3.json"
        if not bk.exists(): bk.write_text(json.dumps(old, ensure_ascii=False, indent=1))
    out = dict(slug=SLUG, editor_revision="edit-r3", revision="edit-r3", built_by="films/la-mort-en-ce-jardin.py -> edit-build/edit_sound.py",
               supersedes="sound-u3.json (U3 os-r1; kept unchanged)", timeline="film seconds 0-73.0 (L local + 2.0, E local + 39.5)",
               have=dict(jungle=rec["have"]["jungle"], stream=rec["have"]["stream"], tide=rec["have"]["tide"], splash=rec["have"]["splash"]),
               used=rec["used"], jungle_source=rec["jungle_source"], checks=rec["checks"],
               clearance_px=dict(L=SPLASH["L"]["clearance_px"], E=SPLASH["E"]["clearance_px"],
                                 definition="trace clearance_px at the last crosser's minimum-clearance frame (the same value as ledger worlds.*.min_clearance_last_crosser_px)"),
               splash_local_t=dict(L=SPLASH["L"]["t"], E=SPLASH["E"]["t"]),
               synthesized=sorted({c["source"] for c in rec["cues"] if c["source"].startswith("HM-SYN")}),
               foraged=sorted({c["source"] for c in rec["cues"] if c["source"].startswith("FOR-")}),
               cues=rec["cues"])
    json.dump(out, open(p, "w"), ensure_ascii=False, indent=1)


film = kit.Film(SLUG, seconds=SECONDS, boil=0, wobble=0)


@film.picture
def picture(t, ink):
    ink.paper(color=BAR, grain=False)
    img, _ = cached(int(round(t * FPS)))
    ink.paste(img, (0, 0))


film.sound(sound)
film.poster_at = 21.2


def write_ledger():
    total = int(round(SECONDS * FPS))
    recs = [json.load(open(CACHE / f"f{k:04d}.json")) for k in range(total)]
    # byte identity L-S1/S2 = E-S1/S2 and the shoe layer offset
    ident = []
    for r in recs:
        if r.get("same_as_k") is not None:
            a = json.load(open(CACHE / f"f{r['same_as_k']:04d}.json"))["sha1_rgb"]
            assert a == r["sha1_rgb"], r["k"]
            ident.append([r["k"], r["same_as_k"]])
    lay = {"L": {}, "E": {}}
    for r in recs:
        if r.get("shoe_layer") and r["version"] in lay:
            sl = r["shoe_layer"]
            assert sl["k"] not in lay[r["version"]], ("layer frame shown twice", r["version"], sl["k"])
            lay[r["version"]][sl["k"]] = dict(sl, film_k=r["k"], world_t=r["world_t"], shot=r["shot"])
    # edit-r2: every one of the 150 layer frames appears in both versions, at exactly +168 trace frames (7.0 s),
    # from the same file at the same resolution; in the closes (same camera) the screen raster is identical too.
    assert sorted(lay["L"]) == sorted(lay["E"]) == list(range(LAYER["frames"])), (sorted(set(range(150)) - set(lay["E"])))
    per_k = []
    for kk in range(LAYER["frames"]):
        a, b = lay["L"][kk], lay["E"][kk]
        assert a["file_sha256"] == b["file_sha256"] and a["hi"] == b["hi"], kk
        assert abs((a["world_t"] - b["world_t"]) - 7.0) < 1e-3, (kk, a["world_t"], b["world_t"])
        if a["hi"]: assert a["raster_sha256"] == b["raster_sha256"] and a["cam"] == b["cam"], kk
        per_k.append(dict(k=kk, file_sha256=a["file_sha256"], hi=a["hi"], L_film_k=a["film_k"], E_film_k=b["film_k"],
                          L_world_t=a["world_t"], E_world_t=b["world_t"], L_shot=a["shot"], E_shot=b["shot"],
                          raster_sha256_L=a["raster_sha256"], raster_sha256_E=b["raster_sha256"],
                          raster_identical=a["raster_sha256"] == b["raster_sha256"], dy_world=[a["dy"], b["dy"]],
                          dy_screen=[a["dy_screen"], b["dy_screen"]]))
    both = list(range(LAYER["frames"]))
    full = {"L": {}, "E": {}}
    for v in ("L", "E"):
        for kk in range(LAYER["frames"]):
            full[v][kk] = hashlib.sha256(open(LAYER["wide"] % kk, "rb").read()).hexdigest()
    # a full world audit for each version (every trace frame, including those not on screen) and the baseline
    worlds = {}
    for v in ("L", "E", "baseline"):
        rows = []
        prev = None
        for fr in TR[v]["frames"]:
            check_invariants(v, fr, {})
            row = dict(t=fr["t"], water_y=fr["water_y"], plank_occupant=fr["plank_occupant"], defl=fr["plank_deflection_px"],
                       bag=fr["bag"][0], shoe=fr["shoe"][0] if fr["shoe"] else None, clearance=fr.get("clearance_px"),
                       grips={w: P["grips"] for w, P in fr["people"].items()}, bank={w: P["bank"] for w, P in fr["people"].items()})
            if prev and (prev["bag"] != row["bag"] or prev["shoe"] != row["shoe"]):
                ev = [e for e in TR[v]["events"] if abs(e["t"] - fr["t"]) <= 1.01 / FPS]
                appear = prev["shoe"] is None and row["shoe"] == "water" and abs(fr["t"] - SHOE_T0.get(v, -9)) <= 1.01 / FPS
                assert ev or appear, ("holder change without event", v, fr["t"], prev["bag"], row["bag"], prev["shoe"], row["shoe"])
            rows.append(row); prev = row
        rig_err = max(max(RG.bone_error(RG.fk(P["root"], P["a"])).values()) for fr in TR[v]["frames"] for P in fr["people"].values())
        cl = [f.get("clearance_px") for f in TR[v]["frames"] if f.get("clearance_px") is not None]
        order = []
        for e in TR[v]["events"]:
            if e["event"] == "grip" and e["obj"] == "liana" and e["who"] not in order: order.append(e["who"])
        worlds[v] = dict(frames=rows, events=TR[v]["events"], rig_error_max_px=rig_err, crossing_order=order,
                         last_crosser=order[-1] if order else None, bag_final=rows[-1]["bag"],
                         min_clearance_last_crosser_px=TR[v].get("min_clearance_last", min(cl) if cl else None),
                         max_plank_occupancy=max(len(r["plank_occupant"]) for r in rows))
    screen_err = max((r.get("rig_error_px") or 0) for r in recs)
    rev = {}
    for name in ("plan.md", "world.json", "world-scene.json", "performance.json", "interruption.json", "sound.json",
                 "performance/trace-L.json", "performance/trace-E.json", "performance/trace-baseline.json", "performance/poses.json"):
        rev[name] = hashlib.sha256(open(SW / name, "rb").read()).hexdigest()[:16]
    for name in ("world.json", "performance.json", "interruption.json", "sound.json"):
        try: rev[name + "#revision"] = json.load(open(SW / name)).get("revision")
        except Exception: pass
    out = dict(slug=SLUG, editor_revision="edit-r3", fps=FPS, seconds=SECONDS, picture=[PW, PH], pillarbox=[960, 540, PX0],
               segments=[dict(film=[s[0], s[1]], id=s[2], version=s[3], local0=s[4], kind=s[5]) for s in SEG],
               captions=[dict(film=[a, b], text=c) for a, b, c in CAPTIONS],
               rig_error_max=max(screen_err, *(w["rig_error_max_px"] for w in worlds.values())),
               rig_error_max_screen_px=screen_err,
               byte_identical_pairs_E_to_L=dict(count=len(ident), first=ident[:1], last=ident[-1:]),
               shoe_layer=dict(id=LAYER["id"], frames=LAYER["frames"], offset_s=7.0, offset_frames=168,
                               L_k_on_screen=sorted(lay["L"]), E_k_on_screen=sorted(lay["E"]),
                               on_screen_both=len(both), file_hashes_identical_all_150=True,
                               same_resolution_all_150=True,
                               raster_identical_count=sum(1 for q in per_k if q["raster_identical"]),
                               raster_identical_k=[q["k"] for q in per_k if q["raster_identical"]],
                               note=("k 0-95: wide layer (L-S4 push-in vs E-S3 static wide: same file, different camera, so the screen "
                                     "raster differs by the push-in only); k 96-149: hi layer in the identical close camera (L-S5 = E-S4 "
                                     "as a function of time since the cut), screen raster byte-identical before the whole-pixel "
                                     "water-level translation dy_screen = round(m * dy_world), which rides each version's own water level."),
                               per_k=per_k,
                               png_sha256_wide=[full["L"][kk] for kk in range(LAYER["frames"])]),
               splash={v: dict(SPLASH[v], film_t=round(SPLASH[v]["t"] + {"L": 2.0, "E": 39.5}[v], 4),
                               frames_drawn=[r["k"] for r in recs if r.get("splash") and r["version"] == v]) for v in ("L", "E")},
               shoe_visible_after_retrieval={v: dict(frames=sum(1 for r in recs if r["version"] == v and r.get("shoe") == "B.R" and r.get("kind") not in ("ledger_write", "ledger_rewrite")),
                                                   visible=sum(1 for r in recs if r["version"] == v and r.get("shoe") == "B.R" and r.get("shoe_visible") and r.get("kind") not in ("ledger_write", "ledger_rewrite")))
                                             for v in ("L", "E")},
               worlds=worlds,
               film_frames=recs,
               declared=[
                   "edit-r3: U1's water() and plank() are replaced at run time by the editor's versions (compose.py unedited): the "
                   "water plate is reflect-tiled downward (no edge-clamp streaks) and carries a uniform 0.72 lighting gain in the closes; "
                   "the card plank bends along an elastic point-load curve, drawn with SAG_X = 2.5 times the trace's deflection "
                   "beyond its 2 px resting sag (the occupant's FK root is lowered by the same extra sag), and the water's own plate "
                   "rows are laid translucently over any part of the card bent below the water line. Ledger values are the trace's.",
                   "edit-r3: the last crossings (L-S8, and E-S6 from local 24.0) push in at P2 from m 0.955 to m 1.38.",
                   "edit-r3: the L-S5/E-S4 close ends 16 px lower (centre (200,352)); the L-S6 two-shot is centred (150,244) at M 2.2; "
                   "in L-S6 B's free far arm is re-keyed (open palm at chest height) for local 20.4-21.75 (no grip involved).",
                   "edit-r3: the shoe in B's hand hangs by its heel counter, upright within 0.3 s of the grasp, layered over the mitten "
                   "with the mitten's thumb card re-laid over the heel; a bag held at head height is layered behind the holder's head.",
                   "edit-r3: the close's P1 plane behind the hand-off is the fluted Mekong trunk (already credited) instead of Buttress "
                   "Roots 1; the closes' depth-blur sigmas are smaller (P0 0.8, P1 0.35, near 0.6, near_fg 1.1); the near-bank ledger "
                   "placard is removed; sweat glints are L 246-248 on a damp patch, and B's face gains a pencilled ear and jaw line.",
                   "edit-r2: the E-S3/E-S4 and E-S4/E-S5 cuts are 0.5 s later than plan section 6 (50.5 and 52.9 instead of 50.0 and 52.4) "
                   "so that E-S4 starts at the same shoe-layer frame and the same time before the hand-off as L-S5; E-S5 is 1.6 s "
                   "(the rewrite is written faster); E-S6 and every other cut are as planned. The film-to-local offset of E is unchanged (39.5 s).",
                   "edit-r2: the L-S5/E-S4 close opens on the hand-off with both heads in frame and tilts down with B's kneel to "
                   "the plank-foot framing; the heart leaf that hid the receiver is removed from the near dressing; a fluted "
                   "buttress trunk (edit-r3: the Mekong trunk cut, replacing Buttress Roots 1) stands as a P1 plane behind the hand-off.",
                   "edit-r2: charcoal mud and sweat glints are laid on faces and mittens by the editor's wet pass (handmade make-up "
                   "on the card puppets); the shoe is never touched by it.",
                   "edit-r2: the splash on the last crosser's shins is a handmade cut-paper water sheet and card droplets, animated "
                   "on twos from the minimum-clearance frame of the trace.",
                   "E-S1/E-S2 show the L frames (byte-identical, plan section 6). U2's E trace differs there (C 10 px left, water 2 px lower); "
                   "the E world takes over at the cut into E-S3 (45.5 s), after the ledger insert.",
                   "The ledger inserts are hands only: in L the strike and rewrite are made by B's free left hand (A has crossed), in E by A's free left hand.",
                   "The shoe's dryness and whiteness is the one declared impossibility."],
               input_revisions=rev)
    json.dump(out, open(SW / "ledger.json", "w"), ensure_ascii=False)
    print("ledger ->", SW / "ledger.json", "rig_error_max", out["rig_error_max"])


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--prebuild":
        prebuild(int(sys.argv[2]) if len(sys.argv) > 2 else 4)
        sys.exit()
    if len(sys.argv) > 1 and sys.argv[1] == "--baseline":
        d = HERE / "stills" / SLUG; d.mkdir(parents=True, exist_ok=True)
        for x in sys.argv[2:]:
            C, fr, _ = world_frame("baseline", float(x), "wide", "BL", baseline_world=True)
            compose_960(C, -1).save(d / f"baseline-{float(x):05.2f}.png")
        sys.exit()
    if len(sys.argv) > 1 and sys.argv[1] == "--stills":
        d = HERE / "stills" / SLUG; d.mkdir(parents=True, exist_ok=True)
        for x in sys.argv[2:]:
            img, rec = render_frame(int(round(float(x) * FPS)))
            img.save(d / f"{float(x):06.2f}.png")
            print(x, {q: rec.get(q) for q in ("shot", "local_t", "bag", "shoe", "plank_occupant", "rig_error_px")})
        sys.exit()
    if len(sys.argv) > 1 and sys.argv[1] == "--ledger":
        write_ledger(); sys.exit()
    prebuild(4)
    film.render()
    write_ledger()
    subprocess.run([sys.executable, "-I", str(SW / "edit-build" / "update_credits.py")], check=True)

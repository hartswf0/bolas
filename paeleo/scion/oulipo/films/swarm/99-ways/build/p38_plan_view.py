"""99 ways, page 38 "Plan view" (point of view; medium: cut-paper).
The office and the platform seen straight down as a floor plan: walls are cut dark strips (the plan's section),
people are the tops of heads and hats on their shoulders, the agent's walk is a track of punched paper dots that grows
from panel to panel (her walk a finer track of smaller dots). Six panels, the same plan in each, E0-E5.
Detail circles (the draughtsman's callout) enlarge the memo, the clock at 4:10 and the key on its hook, so nothing
is seen standing up. All HANDMADE cut paper (films/swarm/99-ways/kit/cutpaper99.py) on the LoC 1934 sheet;
lettering and balloons in the shared pen hand.
Run: python3 -I p38_plan_view.py"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/kit")
import pen99  # noqa: E402
from pen99 import penlib, ROOT  # noqa: E402
from cutpaper99 import Cut, ellipse, rect, hexc  # noqa: E402

CANON = json.load(open(ROOT / "films/swarm/99-ways/canon.json"))
C = [c for c in CANON["constraints"] if c["id"] == "plan-view"][0]
LN = {k: v["text"] for k, v in CANON["incident"]["lines"].items()}
SRC = ROOT / "films/sources/99-ways"
OUT_JPG = ROOT / "assets/pages/99-ways/38-plan-view.jpg"
OUT_PNG = SRC / "masters/38-plan-view.png"
BEATS = SRC / "beats/38"
W, H = pen99.PAGE_W, pen99.PAGE_H

COL = dict(ballast="#8f8a80", tie="#5b4330", rail="#6f7378", boards="#b29f80", edge="#ece6d4",
           wall="#2e2722", floor="#cfae80", seam="#b8956a", desk="#5e3f26", chair="#7a5434", memo="#fbf8ee",
           glass="#bfd0cd", counter="#6b4a2e", sign="#f4ecd6", cupboard="#4a3426", cuptop="#7d5a36",
           leaf="#a07b52", sdoor="#8a6640", card="#fbf8ee",
           hair="#3b2a1e", skin="#e4b896", shirt="#f3efe4", vest="#2a2420", shoe="#1e1a17", pencil="#e2b23a",
           brim="#6a2e27", crown="#55231d", band="#2b2420", coat="#4a5d72",
           dot="#3b2a1e", herdot="#6a2e27", clockface="#f4ecd6", hand="#1b1715", key="#c9a040", hook="#2c2017",
           tag="#f4ecd6", callout="#f7f3e8", inkwell="#1e1a17")

PW, PH = 975, 806
COLX = (110, 110 + PW + 30)
ROWY = (262, 262 + PH + 30, 262 + 2 * (PH + 30))

# ------------------------------------------------------------------ the plan (panel-local px)
OFF = (300, 14, 965, 795)            # office outer wall rectangle
WT = 24                              # wall thickness
WIN = (300, 300, 470)                # ticket window in the left wall: x, y0, y1
CUP = (612, 38, 812, 168)            # cupboard against the top wall (x0, y0, x1, y1: front at y1)
SDOOR = (852, 932)                   # SERVICE door gap in the top wall
CLOCK = (324, 150)                   # clock on the left wall (inner face)
DESK = (690, 545, 900, 645)
CHAIR = (770, 664, 836, 722)

# the agent's walk: from the chair, round the desk, past the window, to the cupboard
AG_PATH = [(803, 700), (740, 740), (655, 712), (610, 610), (540, 500), (455, 420), (448, 392),
           (520, 360), (610, 350), (690, 320), (718, 262)]
HER_PATH_IN = [(205, 806), (212, 640), (218, 500), (222, 392)]
HER_PATH_OUT = [(222, 392), (226, 300), (214, 160), (205, -40)]


def resample(path, step):
    p = np.array(path, np.float32)
    seg = np.linalg.norm(np.diff(p, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    t = np.arange(0, s[-1] + 1e-3, step)
    x = np.interp(t, s, p[:, 0])
    y = np.interp(t, s, p[:, 1])
    return np.stack([x, y], 1), s[-1]


def smooth(path, n=400):
    """Catmull-Rom through the points, then even resampling."""
    P = np.array(path, np.float32)
    P = np.vstack([P[:1], P, P[-1:]])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for t in np.linspace(0, 1, 24, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(P[-2])
    return np.array(out, np.float32)


AG_CURVE = smooth(AG_PATH)
AG_DOTS, AG_LEN = resample(AG_CURVE, 25.0)


def at_frac(curve, f):
    pts, L = resample(curve, 1.0)
    i = int(round(f * (len(pts) - 1)))
    i = max(1, min(len(pts) - 1, i))
    d = pts[i] - pts[max(0, i - 12)]
    return pts[i], math.degrees(math.atan2(d[1], d[0]))


FIG_S = 1.45


def xf(poly, at, ang):
    """local (facing -y) -> panel: rotate so -y points along heading ang (deg, image coords), scale, translate"""
    p = np.asarray(poly, np.float32) * FIG_S
    a = math.radians(ang + 90)
    c, s = math.cos(a), math.sin(a)
    return np.stack([p[:, 0] * c - p[:, 1] * s, p[:, 0] * s + p[:, 1] * c], 1) + np.float32(at)


def limbp(a, b, w0, w1):
    a, b = np.float32(a), np.float32(b)
    d = b - a
    ang = math.degrees(math.atan2(d[1], d[0]))
    ea = ellipse(a[0], a[1], w0 / 2, w0 / 2, ang + 90, ang + 270, 10)
    eb = ellipse(b[0], b[1], w1 / 2, w1 / 2, ang - 90, ang + 90, 10)
    return np.vstack([eb, ea])


def agent_top(c, at, ang, pose="walk", stride=0.0):
    """The agent from straight above: shoes, sleeves, hands, shirt shoulders, waistcoat back, head top (hair), nose tip,
    pencil. Local frame: facing -y, his right hand at +x. Returns head centre (panel px)."""
    P = lambda poly: xf(poly, at, ang)
    sw = 12 * stride
    if pose in ("walk", "stand"):
        c.piece(P(ellipse(-15, -22 - sw, 10, 17)), COL["shoe"], opacity=0.3)
        c.piece(P(ellipse(15, -22 + sw, 10, 17)), COL["shoe"], opacity=0.3)
    # sleeves (white shirt) and hands
    if pose == "chin":
        rarm = [(38, -2), (34, -26), (12, -30)]
    elif pose == "reach":
        rarm = [(38, -2), (36, -40), (30, -74)]
    else:
        rarm = [(38, -2), (42, -24 + sw), (40, -40 + sw)]
    larm = [(-38, -2), (-42, -24 - sw), (-40, -40 - sw)]
    for arm in (larm, rarm):
        c.piece(limbp(P([arm[0]])[0], P([arm[1]])[0], 22, 20), COL["shirt"], opacity=0.3)
        c.piece(limbp(P([arm[1]])[0], P([arm[2]])[0], 20, 17), COL["shirt"], opacity=0.3)
    hx, hy = rarm[2]
    # pencil in the right hand, pointing forward (or up to the chin)
    if pose == "chin":
        c.piece(limbp(P([(hx - 2, hy + 2)])[0], P([(hx - 10, hy - 18)])[0], 6, 3), COL["pencil"], opacity=0.3)
    else:
        c.piece(limbp(P([(hx, hy)])[0], P([(hx + 4, hy - 22)])[0], 6, 3), COL["pencil"], opacity=0.3)
    for (x, y) in (larm[2], rarm[2]):
        c.piece(P(ellipse(x, y, 9, 9)), COL["skin"], opacity=0.3)
    # shoulders: shirt, then the waistcoat across the back
    c.piece(P(ellipse(0, 2, 46, 23)), COL["shirt"])
    c.piece(P([(-32, -10), (-12, -6), (0, -16), (12, -6), (32, -10), (36, 10), (0, 22), (-36, 10)]), COL["vest"], opacity=0.25)
    # head: the nose tip shows past the hair in front
    c.piece(P(ellipse(0, -18, 6, 6)), COL["skin"], opacity=0.25)
    c.piece(P(ellipse(0, -2, 18, 20)), COL["hair"], opacity=0.35)
    if pose == "chin":
        c.piece(P(ellipse(hx, hy, 9, 9)), COL["skin"], opacity=0.3)
    return P([(0, -2)])[0]


def stranger_top(c, at, ang):
    """The stranger from straight above: coat shoulders, a hat (brim, band, crown)."""
    P = lambda poly: xf(poly, at, ang)
    c.piece(P(ellipse(-28, -6, 10, 15)), COL["coat"], opacity=0.3)
    c.piece(P(ellipse(28, -6, 10, 15)), COL["coat"], opacity=0.3)
    c.piece(P(ellipse(0, 4, 38, 21)), COL["coat"])
    c.piece(P(ellipse(0, -4, 27, 26)), COL["brim"], opacity=0.42)
    c.piece(P(ellipse(0, -2, 17, 16)), COL["band"], shadow=False)
    c.piece(P(ellipse(0, -2, 15, 14)), COL["crown"], shadow=False)
    return P([(0, -4)])[0]


def pen_line(c, pts, w=3.2, seed=0, dash=None, colour=None):
    m = np.zeros((c.h, c.w), np.uint8)
    pts = np.asarray(pts, np.float32)
    if dash:
        q, L = resample(pts, 1.0)
        on, off = dash
        k = 0
        while k < len(q) - 2:
            seg = q[k:min(len(q), k + on)]
            if len(seg) > 2:
                penlib.brush_line(m, seg, w, seed + k, tremor=0.4)
            k += on + off
    else:
        penlib.brush_line(m, pts, w, seed, tremor=0.5)
    penlib.ink_onto(c.img, m, penlib.INK if colour is None else hexc(colour))


def text_mask(lines, cap, seed, weight=0.13):
    return pen99.letter(lines, cap, seed, weight=weight)


def paste_mask(c, m, cx, cy, colour=None):
    h, w = m.shape
    x0, y0 = int(cx - w / 2), int(cy - h / 2)
    full = np.zeros((c.h, c.w), np.uint8)
    ys, xs, ye, xe = max(0, y0), max(0, x0), min(c.h, y0 + h), min(c.w, x0 + w)
    full[ys:ye, xs:xe] = m[ys - y0:ye - y0, xs - x0:xe - x0]
    penlib.ink_onto(c.img, full, penlib.INK if colour is None else hexc(colour))


def clock_face(c, cx, cy, r):
    c.piece(ellipse(cx, cy, r, r), COL["clockface"])
    ring = np.zeros((c.h, c.w), np.uint8)
    cv2.circle(ring, (int(cx * 4), int(cy * 4)), int(r * 4 - 10), 255, 4, cv2.LINE_AA, shift=2)
    penlib.ink_onto(c.img, ring)
    for k in range(12):
        a = math.radians(k * 30 - 90)
        r0 = r * (0.74 if k % 3 == 0 else 0.8)
        c.strip((cx + r0 * math.cos(a), cy + r0 * math.sin(a)), (cx + r * 0.88 * math.cos(a), cy + r * 0.88 * math.sin(a)),
                 4 if k % 3 == 0 else 2.5, COL["hand"], shadow=False)
    # 4:10 -- hour hand a third of the way from 4 to 5, minute hand on 2
    ah = math.radians((4 + 10 / 60) * 30 - 90)
    am = math.radians(10 * 6 - 90)
    c.limb((cx, cy), (cx + r * 0.48 * math.cos(ah), cy + r * 0.48 * math.sin(ah)), 7, 4, COL["hand"], opacity=0.3)
    c.limb((cx, cy), (cx + r * 0.74 * math.cos(am), cy + r * 0.74 * math.sin(am)), 5, 3, COL["hand"], opacity=0.3)
    c.piece(ellipse(cx, cy, 4, 4), COL["hand"], shadow=False)


def callout(c, cx, cy, r, to, seed):
    """the draughtsman's detail circle: a paper disc with an inked rim and a leader to the thing it enlarges"""
    ang = math.atan2(to[1] - cy, to[0] - cx)
    pen_line(c, [(cx + r * math.cos(ang), cy + r * math.sin(ang)), to], 3.0, seed, dash=(9, 7))
    c.piece(ellipse(cx, cy, r, r), COL["callout"], opacity=0.45)
    ring = np.zeros((c.h, c.w), np.uint8)
    cv2.circle(ring, (int(cx * 4), int(cy * 4)), int((r - 4) * 4), 255, 14, cv2.LINE_AA, shift=2)
    penlib.ink_onto(c.img, ring)
    c.piece(ellipse(to[0], to[1], 6, 6), COL["hand"], shadow=False)


def key_detail(c, cx, cy, s=1.0):
    """frontal detail inside a callout: the hook, the brass key hanging from it, its SERVICE tag"""
    c.piece(rect(cx - 6 * s, cy - 58 * s, cx + 6 * s, cy - 44 * s), COL["hook"], opacity=0.3)
    c.strip((cx, cy - 46 * s), (cx, cy - 34 * s), 4 * s, COL["hook"], opacity=0.3)
    bow = ellipse(cx, cy - 18 * s, 15 * s, 15 * s)
    k = np.vstack([bow])
    c.piece(k, COL["key"], holes=[ellipse(cx, cy - 18 * s, 7 * s, 7 * s)], opacity=0.35)
    c.piece(rect(cx - 4 * s, cy - 5 * s, cx + 4 * s, cy + 46 * s), COL["key"], opacity=0.35)
    c.piece(np.array([[cx + 3 * s, cy + 30 * s], [cx + 16 * s, cy + 30 * s], [cx + 16 * s, cy + 38 * s], [cx + 10 * s, cy + 38 * s],
                      [cx + 10 * s, cy + 44 * s], [cx + 3 * s, cy + 44 * s]]), COL["key"], opacity=0.35)
    # tag on a string from the bow
    pen_line(c, [(cx - 12 * s, cy - 14 * s), (cx - 30 * s, cy + 2 * s)], 2.0, 77)
    tg = np.array([[cx - 74 * s, cy + 0 * s], [cx - 20 * s, cy - 4 * s], [cx - 16 * s, cy + 20 * s], [cx - 72 * s, cy + 24 * s]])
    c.piece(tg, COL["tag"], opacity=0.35)
    m = text_mask(["SERVICE"], int(13 * s), 381)
    paste_mask(c, m, cx - 45 * s, cy + 11 * s)


def ground(c):
    # track bed: ballast, ties, rails
    c.piece(rect(-10, -10, 122, PH + 10), COL["ballast"], shadow=False, jitter=0.3)
    for y in range(-6, PH + 20, 44):
        c.piece(rect(4, y, 114, y + 17), COL["tie"], opacity=0.3, jitter=0.5)
    for x in (26, 92):
        c.strip((x, -10), (x, PH + 10), 9, COL["rail"], opacity=0.4)
    # platform boards with seams and a white edge
    c.piece(rect(122, -10, OFF[0] + 2, PH + 10), COL["boards"], jitter=0.4)
    for x in range(156, OFF[0], 34):
        c.strip((x, -10), (x, PH + 10), 2.0, "#8f7d61", shadow=False)
    c.strip((130, -10), (130, PH + 10), 9, COL["edge"], opacity=0.25)
    # office floor
    c.piece(rect(OFF[0], OFF[1], OFF[2], OFF[3]), COL["floor"], shadow=False, jitter=0.3)
    for y in range(OFF[1] + WT + 40, OFF[3] - WT, 42):
        c.strip((OFF[0] + WT, y), (OFF[2] - WT, y), 1.8, COL["seam"], shadow=False)


def walls(c):
    x0, y0, x1, y1 = OFF
    wy0, wy1 = WIN[1], WIN[2]
    # left wall in two pieces either side of the ticket window
    c.piece(rect(x0, y0, x0 + WT, wy0), COL["wall"], opacity=0.45)
    c.piece(rect(x0, wy1, x0 + WT, y1), COL["wall"], opacity=0.45)
    c.piece(rect(x1 - WT, y0, x1, y1), COL["wall"], opacity=0.45)
    c.piece(rect(x0, y1 - WT, x1, y1), COL["wall"], opacity=0.45)
    # top wall, broken by the SERVICE door
    c.piece(rect(x0, y0, SDOOR[0], y0 + WT), COL["wall"], opacity=0.45)
    c.piece(rect(SDOOR[1], y0, x1, y0 + WT), COL["wall"], opacity=0.45)
    # ticket window: glass in the wall line, counter inside, sill outside
    c.piece(rect(x0 + 6, wy0, x0 + 16, wy1), COL["glass"], opacity=0.3)
    c.piece(rect(x0 + WT, wy0 - 12, x0 + WT + 62, wy1 + 12), COL["counter"], opacity=0.4)
    c.piece(rect(x0 - 16, wy0 + 6, x0, wy1 - 6), COL["counter"], opacity=0.35)
    # TICKET OFFICE sign card along the outside wall, below the window, lettered along the wall
    sx0, sx1 = x0 - 34, x0 - 4
    c.piece(rect(sx0, wy1 + 20, sx1, wy1 + 262), COL["sign"], opacity=0.35)
    m = np.rot90(text_mask(["TICKET OFFICE"], 22, 3801))
    paste_mask(c, m, (sx0 + sx1) / 2 + 1, wy1 + 141)
    # SERVICE door: shut, its leaf flush in the wall line; the card on it
    c.piece(rect(SDOOR[0], y0 + 3, SDOOR[1], y0 + WT - 3), COL["sdoor"], opacity=0.4)
    c.piece(rect(SDOOR[0] - 6, y0 + WT + 4, SDOOR[1] + 6, y0 + WT + 44), COL["card"], opacity=0.4)
    paste_mask(c, text_mask(["SERVICE"], 22, 3802), (SDOOR[0] + SDOOR[1]) / 2, y0 + WT + 24)
    # the clock's bracket on the left wall
    c.piece(rect(CLOCK[0], CLOCK[1] - 20, CLOCK[0] + 12, CLOCK[1] + 20), COL["hand"], opacity=0.35)
    c.piece(rect(CLOCK[0] + 12, CLOCK[1] - 16, CLOCK[0] + 18, CLOCK[1] + 16), COL["clockface"], opacity=0.3)


def furniture(c, cup_open):
    x0, y0, x1, y1 = DESK
    c.piece(rect(*CHAIR), COL["chair"], opacity=0.4)
    c.piece(rect(CHAIR[0] - 4, CHAIR[3] - 12, CHAIR[2] + 4, CHAIR[3] + 4), "#5a3d26", opacity=0.3)
    c.piece(rect(x0, y0, x1, y1), COL["desk"], opacity=0.45)
    memo = np.array([[x0 + 24, y0 + 22], [x0 + 128, y0 + 16], [x0 + 132, y0 + 74], [x0 + 28, y0 + 80]], np.float32)
    c.piece(memo, COL["memo"], opacity=0.35)
    paste_mask(c, text_mask(["4:15", "SERVICE", "Key"], 13, 3803), x0 + 78, y0 + 48)
    c.piece(ellipse(x1 - 36, y0 + 30, 13, 13), COL["inkwell"], opacity=0.35)
    c.piece(rect(x1 - 80, y0 + 56, x1 - 20, y0 + 64), COL["pencil"], opacity=0.3)
    # cupboard: its top (closed) or, opened, its interior; the door hinged on the left jamb
    cx0, cy0, cx1, cy1 = CUP
    if not cup_open:
        c.piece(rect(cx0, cy0, cx1, cy1), COL["cuptop"], opacity=0.45)
        for k in range(1, 4):
            c.strip((cx0 + 6, cy0 + k * 32), (cx1 - 6, cy0 + k * 32), 1.6, "#6a4a2c", shadow=False)
        c.piece(rect(cx0, cy1 - 14, cx1, cy1), COL["leaf"], opacity=0.3)
    else:
        c.piece(rect(cx0, cy0, cx1, cy1), COL["cupboard"], opacity=0.45,
                holes=[rect(cx0 + 12, cy0 + 4, cx1 - 12, cy1 - 4)])
        c.piece(rect(cx0 + 12, cy0 + 4, cx1 - 12, cy1 - 4), "#241c17", shadow=False)
        c.piece(rect(cx0 + 12, cy0 + 4, cx1 - 12, cy0 + 40), "#3b2c22", shadow=False)
        # the leaf swung open 90 degrees on the left jamb, toward the room; the key hangs on its inside face
        c.piece(rect(cx0 - 14, cy1, cx0, cy1 + (cx1 - cx0)), COL["leaf"], opacity=0.42)
        r = cx1 - cx0
        arc = [(cx0 + r * math.cos(math.radians(a)), cy1 + r * math.sin(math.radians(a))) for a in np.linspace(0, 90, 60)]
        pen_line(c, arc, 2.6, 3804, dash=(8, 8))
        # the key on the leaf's inside face (seen from above: brass bow and tag edge)
        ky = cy1 + 70
        c.piece(rect(cx0, ky - 4, cx0 + 8, ky + 4), COL["hook"], shadow=False)
        c.piece(ellipse(cx0 + 15, ky, 8, 5), COL["key"], opacity=0.3)
        c.piece(rect(cx0 + 4, ky + 10, cx0 + 10, ky + 40), COL["tag"], opacity=0.3)
        return (cx0 + 15, ky)
    return None


def track(c, upto, r=6.5):
    """punched paper dots along his walk, from the chair up to arc-length `upto` (px)"""
    n = int(upto / 25.0)
    for i, (x, y) in enumerate(AG_DOTS[1:n]):
        c.piece(ellipse(x, y, r, r, n=14), COL["dot"], opacity=0.35, jitter=0.25, eps=0.8)


def her_track(c, curve, upto_frac, start=0.0):
    pts, L = resample(smooth(curve), 18.0)
    a, b = int(start * len(pts)), int(upto_frac * len(pts))
    for (x, y) in pts[a:b]:
        c.piece(ellipse(x, y, 3.8, 3.8, n=10), COL["herdot"], opacity=0.3, jitter=0.2, eps=0.6)


def ag_pos(f):
    """position/heading at fraction f of his walk"""
    p, ang = at_frac(AG_CURVE, f)
    return (float(p[0]), float(p[1])), ang


def balloon(c, lines, cap, centre, tip, seed):
    return c.balloon(lines, cap, centre, tip, seed)


def panel(n, stage=9):
    c = Cut(PH, PW, seed=3800 + n, fibre_off=(n * 211, n * 97))
    ground(c)
    walls(c)
    keyat = furniture(c, cup_open=(n >= 5 and stage >= 1))
    # her walk
    if n == 1:
        her_track(c, HER_PATH_IN, 0.55)
        stranger_top(c, (213, 590), -88)
    elif n in (2, 3):
        her_track(c, HER_PATH_IN, 0.97)
        stranger_top(c, (226, 388), 0)
    elif n == 4:
        her_track(c, HER_PATH_IN, 1.0)
        her_track(c, HER_PATH_OUT, 0.42)
        stranger_top(c, (222, 250), -95)
    else:
        her_track(c, HER_PATH_IN, 1.0)
        her_track(c, HER_PATH_OUT, 1.0)
    # his walk: where he is in each beat (fraction of the whole walk)
    F = {1: 0.03, 2: 0.63, 3: 0.655, 4: 0.86, 5: 1.0, 6: 1.0}
    f = F[n]
    track(c, f * AG_LEN)
    (x, y), ang = ag_pos(f)
    if n == 1:
        head = agent_top(c, (x, y), -170, "stand", 0.0)
    elif n == 2:
        head = agent_top(c, (x, y), 200, "walk", 1.0)     # turned toward the window
    elif n == 3:
        head = agent_top(c, (x, y), 228, "stand", 0.0)    # head up toward the clock on the left wall
    elif n == 4:
        head = agent_top(c, (x, y), ang, "walk", -1.0)
    elif n == 5:
        head = agent_top(c, (x, y), -90, "reach" if stage < 1 else "stand", 0.0)
    else:
        head = agent_top(c, (x, y), -90, "chin", 0.0)
    hx, hy = head
    # details and lines
    if n == 1:
        callout(c, 500, 610, 128, (DESK[0] + 78, DESK[1] + 48), 3811)
        m = text_mask(["4:15 - open", "SERVICE door.", "Key in cupboard."], 26, 3812)
        c.piece(np.array([[398, 548], [602, 542], [606, 676], [394, 680]], np.float32), COL["memo"], opacity=0.3)
        paste_mask(c, m, 500, 611)
    if n == 2 and stage >= 1:
        balloon(c, ["Pardon me —", "have you the", "right time?"], 38, (205, 615), (224, 412), 3821)
    if n == 3:
        pen_line(c, [(hx - 10, hy - 12), (CLOCK[0] + 22, CLOCK[1] + 4)], 2.6, 3831, dash=(10, 9))
        callout(c, 470, 125, 88, (CLOCK[0] + 18, CLOCK[1]), 3832)
        clock_face(c, 470, 125, 66)
        if stage >= 1:
            balloon(c, ["Ten past four,", "by the clock."], 38, (735, 300), (hx + 16, hy - 4), 3833)
    if n == 4 and stage >= 1:
        balloon(c, ["Much", "obliged!"], 40, (150, 560), (215, 285), 3841)
    if n in (5, 6) and keyat is not None:
        callout(c, 855, 330, 82, keyat, 3851 + n)
        key_detail(c, 855, 336, 1.15)
    if n == 6 and stage >= 1:
        balloon(c, ["Well, here I am...", "and what for?"], 38, (560, 520), (hx - 6, hy + 22), 3861)
    return c.img


def header(pg):
    """the plan's title block: what is drawn, a north arrow, a scale bar, the legend of the two tracks"""
    c = Cut(130, 1980, seed=3890, ground=pg[110:240, 110:2090])
    m = text_mask(["PLAN: ticket office and platform, Randolph station, 4:09 to 4:11"], 40, 3891)
    paste_mask(c, m, m.shape[1] / 2 + 6, 40)
    # legend: his dots, her dots
    for i in range(5):
        c.piece(ellipse(30 + i * 25, 100, 6.5, 6.5, n=14), COL["dot"], opacity=0.35, jitter=0.25, eps=0.8)
    m = text_mask(["his walk"], 28, 3892)
    paste_mask(c, m, 160 + m.shape[1] / 2, 100)
    for i in range(7):
        c.piece(ellipse(370 + i * 18, 100, 3.8, 3.8, n=10), COL["herdot"], opacity=0.3, jitter=0.2, eps=0.6)
    m = text_mask(["her walk"], 28, 3893)
    paste_mask(c, m, 490 + m.shape[1] / 2, 100)
    # scale bar: alternate cut strips
    x = 1460
    for k in range(4):
        c.piece(rect(x + k * 80, 88, x + (k + 1) * 80, 104), COL["wall"] if k % 2 == 0 else COL["callout"], opacity=0.3)
    for k, lab in ((0, "0"), (2, "5"), (4, "10 ft")):
        m = text_mask([lab], 22, 3894 + k)
        paste_mask(c, m, x + k * 80 + (m.shape[1] / 2 - 14 if k == 4 else 0), 70)
    # north arrow
    c.piece(np.array([[1890, 112], [1912, 30], [1934, 112], [1912, 96]], np.float32), COL["wall"], opacity=0.4)
    m = text_mask(["N"], 26, 3899)
    paste_mask(c, m, 1955, 52)
    pg[110:240, 110:2090] = c.img


def build(stages=None):
    pg = pen99.sheet99()
    header(pg)
    boxes = []
    for n in range(1, 7):
        col, row = (n - 1) % 2, (n - 1) // 2
        x0, y0 = COLX[col], ROWY[row]
        boxes.append((x0, y0, x0 + PW, y0 + PH))
        st = 9 if stages is None else stages.get(n)
        if st is None:
            continue
        pg[y0:y0 + PH, x0:x0 + PW] = panel(n, st)
    penlib.ink_onto(pg, penlib.border_mask(pg.shape[:2], boxes, 8, 3880))
    pen99.folio(pg, 38, C["title"])
    return np.clip(np.round(pg), 0, 255).astype(np.uint8)


def main():
    for p in (OUT_JPG.parent, OUT_PNG.parent, BEATS):
        p.mkdir(parents=True, exist_ok=True)
    page = build()
    Image.fromarray(page).save(OUT_PNG, compress_level=6)
    Image.fromarray(page).save(OUT_JPG, quality=90, dpi=(300, 300))
    size = OUT_JPG.stat().st_size
    print("jpeg", size)
    if "--page-only" in sys.argv:
        return
    for f in BEATS.glob("b*.png"):
        f.unlink()
    seq = [({1: 9}, "b01: E0 panel: he rises from the chair; the first dots of his track; she walks up the platform"),
           ({1: 9, 2: 0}, "b02: E1 panel: the dotted track has curved round the desk to the window; she stands at the glass"),
           ({1: 9, 2: 9}, "b03: + her question balloon"),
           ({1: 9, 2: 9, 3: 9}, "b04: E2 panel: he stops, a dotted sight line up to the clock bracket; detail circle at 4:10; the answer"),
           ({1: 9, 2: 9, 3: 9, 4: 9}, "b05: E3 panel: her small dots turn away up the platform; his track bends toward the cupboard; thanks"),
           ({1: 9, 2: 9, 3: 9, 4: 9, 5: 0}, "b06: E4 panel: his track reaches the cupboard, still shut (its top seen)"),
           ({1: 9, 2: 9, 3: 9, 4: 9, 5: 9}, "b07: the cupboard leaf swings open on its left jamb (dotted swing arc); key detail circle"),
           (None, "b08: E5 panel: pencil to his chin, the forgetting line; the whole track ends at the open cupboard (= the page)")]
    bd = []
    for j, (st, d) in enumerate(seq, 1):
        im = build(st) if st is not None else page
        Image.fromarray(im).resize((960, 1242), Image.LANCZOS).save(BEATS / f"b{j:02d}.png")
        bd.append(d)
    record = {
        "n": 38, "id": C["id"], "title": C["title"], "rule": C["rule"], "medium": C["medium"], "family": C["family"],
        "canon_revision": CANON["revision"], "declares": C["declares"],
        "file": str(OUT_JPG.relative_to(ROOT)), "master": str(OUT_PNG.relative_to(ROOT)), "beats_dir": str(BEATS.relative_to(ROOT)),
        "build": "films/swarm/99-ways/build/p38_plan_view.py",
        "sources": ["99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"],
        "made": [
            "every figure and object HANDMADE cut paper in code (films/swarm/99-ways/kit/cutpaper99.py: scissor-faceted flat papers with the LoC 1934 sheet's fibre as relative tone, one down-right paper shadow per piece)",
            "one floor plan repeated in six panels: walls as dark cut strips (the plan's section line) with the ticket-window glass, counter and sill in the left wall and the SERVICE door shut flush in the top wall; office floorboards; the platform's boards and white edge; the track bed with ties and two rails",
            "furniture from above: desk with the memo slip, inkwell and pencil, the chair, the cupboard (its top while shut; opened, its dark interior and the leaf swung 90 degrees on the left jamb with a dotted swing arc and the key on its inside face)",
            "people from above: the agent as hair-top, nose tip, shirt shoulders with the waistcoat across the back, white sleeves, hands, shoes, yellow pencil; the stranger as a hat (brim, band, crown) on coat shoulders",
            "his walk a growing track of punched paper dots from the chair round the desk, past the window, to the cupboard; her walk a finer track of small dots in and back out along the platform",
            "draughtsman's detail circles with dashed leaders enlarge things lying flat or too small from above: the memo (P1), the clock face at 4:10 (P3), the key on its hook with its SERVICE tag (P5-P6); a dashed sight line from his head to the clock bracket (P3)",
            "title block: 'PLAN: ticket office and platform, Randolph station, 4:09 to 4:11', the two-track legend, a cut scale bar and north arrow",
            "lettering in the shared pen hand; the four canon lines in the shared cut-paper balloons (penlib.balloon_piece); hand-ruled borders (penlib.border_mask); folio '38 / Plan view' (pen99.folio)"],
        "events": {"E0": "P1: he stands up from the chair at the desk, the memo enlarged in a detail circle; the first dots of his track",
                   "E1": "P2: his track has rounded the desk to the counter; she stands at the glass outside; question balloon to her hat",
                   "E2": "P3: a dashed sight line from his head to the clock bracket; the clock detail at 4:10; answer balloon",
                   "E3": "P4: her small dots turn back up the platform; thanks balloon to her hat; his track bends toward the cupboard",
                   "E4": "P5: the track ends at the cupboard; its leaf is swung open on the left jamb; key detail circle",
                   "E5": "P6: pencil to his chin, forgetting balloon; the key still on its hook; SERVICE door shut flush in the wall"},
        "lines": LN,
        "substitutions": "none: the four lines verbatim",
        "beat": "the dotted track grows panel by panel as the agent's hat-less head-top moves from the chair to the cupboard; the cupboard leaf swings open on its left jamb; the forgetting line ends the track",
        "beat_frames": bd,
        "self_check": {"size_px": [page.shape[1], page.shape[0]], "jpeg_bytes": size, "jpeg_quality": 90,
                       "in_target_0.4_1.2MB": 400000 <= size <= 1200000,
                       "no_wall_standing": "every wall is a cut strip seen from above in section; the clock, memo and key faces appear only inside detail circles (plan callouts), never as standing walls",
                       "path_as_line": "his walk is one continuous dotted track, chair to cupboard, complete in P6",
                       "lines_verbatim": True,
                       "pending": "independent blind reading not run by the maker"},
    }
    json.dump(record, open(ROOT / "films/swarm/99-ways/pages/38.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps(record["self_check"], indent=1))


if __name__ == "__main__":
    main()

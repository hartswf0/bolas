"""99 ways, page 02 "The key waits" (point of view; medium: cut-paper, HANDMADE).
The view is the brass key's, from its hook inside the closed cupboard, facing the door. Every panel is framed by the
inside of the cupboard door (cut kraft planks, battens, lock box); the office is seen only through its openings: the
jamb crack, the gap under the door, the keyhole (which looks straight at the wall clock) and a knot hole. Sounds are
pen letters cut out of pale paper; voices are the shared cut-paper balloons with tails into the crack. On E4 the door
swings open and the light comes in; the key's own SERVICE tag hangs in the foreground of every panel.
Writes assets/pages/99-ways/02-the-key-waits.jpg, films/sources/99-ways/masters/02-the-key-waits.png,
films/sources/99-ways/beats/02/b01..b07.png, films/swarm/99-ways/pages/02.json.  Run: python3 -I build_page02.py"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pen99  # noqa: E402
from pen99 import penlib, ROOT  # noqa: E402
from cutpaper99 import Cut, ellipse, rect, hexc  # noqa: E402

CANON = json.load(open(ROOT / "films/swarm/99-ways/canon.json"))
C = CANON["constraints"][1]
assert C["id"] == "the-key-waits"
LN = {k: v["text"] for k, v in CANON["incident"]["lines"].items()}
SRC = ROOT / "films/sources/99-ways"
OUT_JPG = ROOT / "assets/pages/99-ways/02-the-key-waits.jpg"
OUT_PNG = SRC / "masters/02-the-key-waits.png"
BEATS = SRC / "beats/02"

# papers
WALL, WAINS, RAIL, FLOOR = "#f1e0a8", "#b48957", "#8a6238", "#a07b52"
GLASS, WFRAME = "#cdd6cf", "#5b3d25"
DOOR, DOOR2, DOOR3, BATTEN, SEAM = "#2b1f16", "#261b13", "#302318", "#382819", "#150f0a"
IRON, SILL = "#262422", "#231a12"
SHIRT, WAIST, TROUS, TIE, SKIN, SKIN2, HAIR, BOOT = "#f3efe4", "#37332f", "#45423e", "#1d1b1a", "#e0b08a", "#c99372", "#4b3324", "#1f1a16"
PENCIL, HAT, HATBAND, COAT, FACE2 = "#e2b23a", "#6d2e2b", "#2a1716", "#4d5b63", "#e4b896"
LAMP, BULB = "#4f6a46", "#f6e7a6"
TAG_LIT, TAG_DIM = "#dcc48e", "#6a5a40"
SOUND = "#f2d878"

# the door's openings, normalised (u = x / w, v = y / h); the view never moves, so these never move
CRACK = [(0.835, 0.0), (0.955, 0.0), (0.925, 0.905), (0.870, 0.905)]
GAP = [(0.0, 0.885), (0.93, 0.885), (0.93, 0.95), (0.0, 0.955)]
KEYHOLE_C, KEYHOLE_R = (0.655, 0.25), 0.055
KNOT_C, KNOT_R = (0.26, 0.19), 0.040
LOCKBOX = (0.565, 0.15, 0.745, 0.43)


# ------------------------------------------------------------------------------------------------ the office (behind)
def clock(c, w, h, cx, cy, r, hh, mm):
    s = min(w, h)
    c.piece(rect(cx - r * 1.25, cy - r * 1.3, cx + r * 1.25, cy + r * 3.6), "#4a2f1d")          # case
    c.piece(ellipse(cx, cy, r * 1.12, r * 1.12), "#6a4528")
    c.piece(ellipse(cx, cy, r, r), "#f4ecd6", shadow=False)
    for k in range(12):
        a = math.radians(k * 30)
        L = 0.16 if k % 3 == 0 else 0.09
        c.strip((cx + math.sin(a) * r * 0.80, cy - math.cos(a) * r * 0.80),
                (cx + math.sin(a) * r * (0.80 - L), cy - math.cos(a) * r * (0.80 - L)), max(2, r * 0.05), "#1b1715", shadow=False, jitter=0.3)
    am = math.radians(mm * 6)
    ah = math.radians((hh % 12) * 30 + mm * 0.5)
    c.strip((cx, cy), (cx + math.sin(ah) * r * 0.50, cy - math.cos(ah) * r * 0.50), max(3, r * 0.11), "#1b1715", jitter=0.3, off=(2, 3))
    c.strip((cx, cy), (cx + math.sin(am) * r * 0.78, cy - math.cos(am) * r * 0.78), max(2, r * 0.07), "#1b1715", jitter=0.3, off=(2, 3))
    c.piece(ellipse(cx, cy, r * 0.07, r * 0.07), "#a8862f", shadow=False)
    c.strip((cx, cy + r * 1.15), (cx, cy + r * 2.9), max(2, r * 0.05), "#2a2018", shadow=False)    # pendulum rod
    c.piece(ellipse(cx, cy + r * 3.0, r * 0.22, r * 0.22), "#9c7a2c", shadow=False)


def office(c, w, h, clock_t=(4, 10), lamp=True, stranger=None):
    U = lambda u: u * w
    V = lambda v: v * h
    c.piece(rect(-20, V(0.60), w + 20, V(0.905)), WAINS, shadow=False)
    c.strip((-20, V(0.60)), (w + 20, V(0.60)), V(0.022), RAIL)
    c.piece(rect(-20, V(0.885), w + 20, h + 20), FLOOR)
    # ticket window (right): frame, glass, lettered sill
    c.piece(rect(U(0.775), V(0.06), U(1.04), V(0.585)), WFRAME)
    c.piece(rect(U(0.80), V(0.09), U(1.04), V(0.545)), GLASS, shadow=False)
    if stranger:
        su = stranger.get("u", 0.895)
        c.piece(rect(U(su - 0.075), V(0.335), U(su + 0.075), V(0.56)), COAT)                     # shoulders
        c.piece(ellipse(U(su), V(0.27), U(0.042), V(0.058)), FACE2)
        c.piece(ellipse(U(su - (0.02 if stranger.get("turn") else 0.0)), V(0.215), U(0.075), V(0.022)), HAT)   # brim
        c.piece(ellipse(U(su - (0.025 if stranger.get("turn") else 0.0)), V(0.185), U(0.045), V(0.045), 180, 360), HAT)
        c.strip((U(su - 0.045), V(0.2)), (U(su + 0.04), V(0.2)), V(0.012), HATBAND, shadow=False)
    c.strip((U(0.79), V(0.33)), (U(1.04), V(0.33)), max(4, V(0.012)), WFRAME)                  # glazing bar
    c.piece(rect(U(0.765), V(0.55), U(1.04), V(0.6)), "#4a3220")                               # counter
    # clock, straight across from the keyhole
    clock(c, w, h, U(KEYHOLE_C[0]), V(KEYHOLE_C[1]), min(w, h) * 0.078, *clock_t)
    # pendant lamp, seen through the knot hole
    if lamp:
        c.strip((U(KNOT_C[0]), -10), (U(KNOT_C[0]), V(0.15)), 3, "#2a2420", shadow=False)
        c.piece(np.array([[U(0.20), V(0.23)], [U(0.32), V(0.23)], [U(0.285), V(0.15)], [U(0.235), V(0.15)]]), LAMP)
        c.piece(ellipse(U(0.26), V(0.235), U(0.03), V(0.02), 0, 180), BULB, shadow=False)
    # desk (left)
    c.piece(rect(U(0.20), V(0.58), U(0.60), V(0.63)), "#5a3b24")
    c.piece(rect(U(0.22), V(0.63), U(0.58), V(0.86)), "#4a311f")
    for x in (0.23, 0.55):
        c.piece(rect(U(x), V(0.84), U(x + 0.025), V(0.935)), "#3a2618")


def agent(c, x0, yb, H, pose="stand", look=(0, 0), hand_to=None, face=True, legs=True):
    """The agent in cut paper; origin at his feet, H = head height in px. pose: stand | walk | door | chin."""
    P = lambda dx, dy: (x0 + dx * H, yb + dy * H)
    A = lambda pts: np.array([P(*p) for p in pts], np.float32)
    if legs:
        sp = 0.55 if pose == "walk" else 0.0
        c.piece(A([(-0.45 - sp, -3.55), (-0.02, -3.55), (-0.08 - sp * .6, -0.2), (-0.48 - sp, -0.2)]), TROUS)
        c.piece(A([(0.02, -3.55), (0.45 + sp * .3, -3.55), (0.5 + sp, -0.2), (0.1 + sp * .7, -0.2)]), TROUS)
        c.piece(A([(-0.55 - sp, -0.28), (-0.05 - sp * .6, -0.28), (0.05 - sp * .6, 0.0), (-0.72 - sp, 0.0)]), BOOT)
        c.piece(A([(0.08 + sp * .7, -0.28), (0.55 + sp, -0.28), (0.82 + sp, 0.0), (0.06 + sp * .7, 0.0)]), BOOT)
    arms = []
    if pose == "door" and hand_to is not None:
        arms.append(("L", P(-0.98, -5.9), P(-1.45, -4.55), hand_to))
    else:
        arms.append(("L", P(-0.98, -5.9), P(-1.2, -4.6), P(-1.22, -3.5)))
    if pose == "chin":
        arms.append(("R", P(0.98, -5.9), P(1.35, -4.6), P(0.20, -6.12)))
    else:
        arms.append(("R", P(0.98, -5.9), P(1.2, -4.6), P(1.22, -3.5)))
    # shirt (sloped shoulders), waistcoat with armholes, tie
    c.piece(A([(-1.12, -5.75), (-0.75, -6.2), (-0.3, -6.38), (0.3, -6.38), (0.75, -6.2), (1.12, -5.75), (0.98, -3.3), (-0.98, -3.3)]), SHIRT)
    c.piece(A([(-0.80, -6.05), (-0.62, -6.26), (-0.2, -6.3), (0.0, -5.0), (0.2, -6.3), (0.62, -6.26), (0.80, -6.05),
               (0.74, -5.25), (0.92, -4.8), (0.9, -3.25), (0.0, -3.1), (-0.9, -3.25), (-0.92, -4.8), (-0.74, -5.25)]), WAIST)
    c.piece(A([(-0.075, -6.33), (0.075, -6.33), (0.1, -5.15), (0.0, -4.98), (-0.1, -5.15)]), TIE, shadow=False)
    c.strip(P(-0.55, -4.25), P(-0.25, -4.25), H * 0.06, "#24211e", shadow=False)          # pocket welts
    c.strip(P(0.25, -4.25), P(0.55, -4.25), H * 0.06, "#24211e", shadow=False)
    for k in range(4):
        c.piece(ellipse(*P(0.0, -4.75 + k * 0.38), H * 0.048, H * 0.048), "#c8b98f", shadow=False)
    c.piece(A([(-0.30, -6.66), (0.30, -6.66), (0.28, -6.28), (-0.28, -6.28)]), SKIN2, shadow=False)       # neck
    c.piece(A([(-0.37, -6.47), (0.0, -6.20), (0.37, -6.47), (0.34, -6.27), (0.0, -6.04), (-0.34, -6.27)]), SHIRT)  # collar
    for side, s0, e0, hand in arms:
        c.limb(s0, e0, H * 0.62, H * 0.50, SHIRT)
        c.limb(e0, hand, H * 0.50, H * 0.40, SHIRT)
        # a fold or two cut in a greyer paper
        m = (np.float32(s0) + np.float32(e0)) / 2
        c.strip((m[0] - H * 0.12, m[1] - H * 0.02), (m[0] + H * 0.10, m[1] + H * 0.08), H * 0.035, "#d6d0c2", shadow=False)
        d = np.subtract(hand, e0)
        d = d / (np.linalg.norm(d) + 1e-6)
        c.limb((hand[0] - d[0] * H * 0.42, hand[1] - d[1] * H * 0.42), (hand[0] - d[0] * H * 0.2, hand[1] - d[1] * H * 0.2), H * 0.52, H * 0.52, "#e6e0d0")
        c.piece(ellipse(hand[0], hand[1], H * (0.17 if pose == "chin" and side == "R" else 0.22), H * (0.15 if pose == "chin" and side == "R" else 0.20)), SKIN)
        c.strip((hand[0] - H * 0.12, hand[1] - H * 0.04), (hand[0] + H * 0.12, hand[1] - H * 0.04), H * 0.02, SKIN2, shadow=False)
        if side == "R" and pose == "chin":
            c.strip((hand[0] + H * 0.02, hand[1] + H * 0.10), (hand[0] - H * 0.12, hand[1] - H * 0.36), H * 0.07, PENCIL, off=(3, 4))
            c.strip((hand[0] - H * 0.105, hand[1] - H * 0.32), (hand[0] - H * 0.14, hand[1] - H * 0.42), H * 0.035, "#2a2420", shadow=False)
        elif side == "R":
            c.strip((hand[0] - H * 0.2, hand[1] + H * 0.05), (hand[0] + H * 0.25, hand[1] - H * 0.22), H * 0.07, PENCIL, off=(3, 4))
    # head
    hx, hy = P(0, -7.05)
    c.piece(ellipse(hx - H * 0.43, hy + H * 0.02, H * 0.08, H * 0.14), SKIN2)
    c.piece(ellipse(hx + H * 0.43, hy + H * 0.02, H * 0.08, H * 0.14), SKIN2)
    c.piece(np.vstack([ellipse(hx, hy - H * 0.05, H * 0.43, H * 0.45, 180, 360),
                       [[hx + H * 0.40, hy + H * 0.22], [hx + H * 0.16, hy + H * 0.50], [hx - H * 0.16, hy + H * 0.50], [hx - H * 0.40, hy + H * 0.22]]]), SKIN)
    c.piece(np.vstack([ellipse(hx, hy - H * 0.16, H * 0.46, H * 0.40, 180, 360),
                       [[hx + H * 0.45, hy - H * 0.06], [hx + H * 0.36, hy - H * 0.20], [hx - H * 0.08, hy - H * 0.30],
                        [hx - H * 0.18, hy - H * 0.22], [hx - H * 0.38, hy - H * 0.20], [hx - H * 0.45, hy - H * 0.06]]]), HAIR)
    if face:
        lx, ly = look
        for sx in (-1, 1):
            ex, ey = hx + sx * H * 0.165, hy - H * 0.01
            c.piece(ellipse(ex, ey, H * 0.095, H * 0.065), "#fbf8ee", shadow=False)
            c.piece(ellipse(ex + lx * H * 0.04, ey + ly * H * 0.025, H * 0.042, H * 0.042), "#1c1714", shadow=False)
            ring = ellipse(ex, ey, H * 0.15, H * 0.12)
            c.piece(ring, "#2a2420", holes=[ellipse(ex, ey, H * 0.123, H * 0.095)], off=(2, 3), opacity=0.25)
            up = 0.08 if pose == "chin" else 0.0
            tilt = -0.035 * sx if pose == "chin" else 0.0
            by = ey - H * (0.17 + up)
            c.strip((ex - H * 0.11, by + H * tilt), (ex + H * 0.11, by - H * tilt), H * 0.045, HAIR, shadow=False)
        c.strip((hx - H * 0.03, hy - H * 0.01), (hx + H * 0.03, hy - H * 0.01), H * 0.03, "#2a2420", shadow=False)
        c.piece(np.array([[hx + H * 0.01, hy + H * 0.02], [hx + H * 0.08, hy + H * 0.21], [hx - H * 0.05, hy + H * 0.22]]), SKIN2, off=(2, 3), opacity=0.3)
        if pose == "chin":
            c.piece(ellipse(hx + H * 0.04, hy + H * 0.33, H * 0.055, H * 0.03), "#6a2e27", shadow=False)
        else:
            c.strip((hx - H * 0.11, hy + H * 0.33), (hx + H * 0.11, hy + H * 0.33), H * 0.04, "#6a2e27", shadow=False)


NEAR_SHOULDER_V = 0.73      # his shoulder line in the near pose (below the counter, so the crack shows her above, him below)
NEAR_X, NEAR_H = 0.728, 0.20


def agent_near(c, w, h):
    """P3-P5: he has stopped just beside the cupboard door on its left; his head and most of him are hidden by the door,
    the jamb crack shows only his right shirt sleeve and the edge of his waistcoat, below the window counter; the gap
    under the door shows his boots."""
    H = h * NEAR_H
    agent(c, w * NEAR_X, h * NEAR_SHOULDER_V + 5.9 * H, H, pose="stand", face=False, legs=False)
    c.piece(rect(-20, h * 0.875, w + 20, h + 20), FLOOR, shadow=False)          # floor seen through the gap
    for x0, x1 in ((0.60, 0.70), (0.72, 0.83)):
        c.piece(np.array([(w * x0, h * 0.875), (w * x1, h * 0.875), (w * (x1 + 0.02), h * 0.95), (w * (x0 - 0.01), h * 0.95)]), BOOT)


# ------------------------------------------------------------------------------------------------ the door (in front)
def door_closed(c, w, h, lit=0.0):
    U = lambda u: u * w
    V = lambda v: v * h
    N = lambda pts: np.array([(U(a), V(b)) for a, b in pts], np.float32)
    holes = [N(CRACK), N(GAP), ellipse(U(KEYHOLE_C[0]), V(KEYHOLE_C[1]), min(w, h) * KEYHOLE_R, min(w, h) * KEYHOLE_R),
             N([(KEYHOLE_C[0] - 0.022, KEYHOLE_C[1]), (KEYHOLE_C[0] + 0.022, KEYHOLE_C[1]), (KEYHOLE_C[0] + 0.035, KEYHOLE_C[1] + 0.13), (KEYHOLE_C[0] - 0.035, KEYHOLE_C[1] + 0.13)]),
             ellipse(U(KNOT_C[0]), V(KNOT_C[1]), min(w, h) * KNOT_R * 1.15, min(w, h) * KNOT_R * 0.8)]
    planks = [(-0.05, 0.22, DOOR), (0.22, 0.47, DOOR2), (0.47, 0.70, DOOR3), (0.70, 0.86, DOOR2)]
    for i, (a, b, col) in enumerate(planks):
        poly = N([(a, -0.02), (b, -0.02), (b if i < 3 else 0.87, 0.897), (a, 0.897)])
        if i == 3:
            poly = N([(a, -0.02), (0.84, -0.02), (0.872, 0.897), (a, 0.897)])
        c.piece(poly, col, holes=holes, off=(7, 9), opacity=0.55)
        # grain: thin darker cut slivers
        for k in range(3):
            x = a + (b - a) * (0.25 + 0.25 * k)
            if x > 0.83:
                continue
            c.strip((U(x), V(0.03 + 0.1 * k)), (U(x + 0.008), V(0.35 + 0.15 * k)), 3, SEAM, shadow=False, jitter=0.6)
    # jamb and lintel of the cupboard on the right of the crack
    c.piece(N([(0.95, -0.02), (1.02, -0.02), (1.02, 0.95), (0.925, 0.95), (0.925, 0.905)]), "#2c2017", off=(6, 8))
    c.piece(N([(-0.02, 0.948), (1.02, 0.948), (1.02, 1.02), (-0.02, 1.02)]), SILL, off=(0, -4))
    # battens and brace
    for v0 in (0.08, 0.72):
        c.piece(N([(-0.02, v0), (0.80, v0), (0.80, v0 + 0.065), (-0.02, v0 + 0.065)]), BATTEN, off=(6, 8), opacity=0.5)
    c.strip((U(0.08), V(0.70)), (U(0.55), V(0.16)), U(0.06), BATTEN, off=(6, 8), opacity=0.5)
    # lock box with its keyhole, and the knot hole re-cut through the brace
    lb = LOCKBOX
    kh = [ellipse(U(KEYHOLE_C[0]), V(KEYHOLE_C[1]), min(w, h) * KEYHOLE_R, min(w, h) * KEYHOLE_R),
          N([(KEYHOLE_C[0] - 0.022, KEYHOLE_C[1]), (KEYHOLE_C[0] + 0.022, KEYHOLE_C[1]), (KEYHOLE_C[0] + 0.035, KEYHOLE_C[1] + 0.13), (KEYHOLE_C[0] - 0.035, KEYHOLE_C[1] + 0.13)])]
    c.piece(N([(lb[0], lb[1]), (lb[2], lb[1]), (lb[2], lb[3]), (lb[0], lb[3])]), IRON, holes=kh, off=(6, 8), opacity=0.55)
    for (a, b) in ((lb[0] + 0.02, lb[1] + 0.03), (lb[2] - 0.02, lb[1] + 0.03), (lb[0] + 0.02, lb[3] - 0.03), (lb[2] - 0.02, lb[3] - 0.03)):
        c.piece(ellipse(U(a), V(b), min(w, h) * 0.011, min(w, h) * 0.011), "#6b6457", shadow=False)
    c.piece(N([(lb[0] - 0.015, 0.36), (lb[0], 0.36), (lb[0], 0.40), (lb[0] - 0.015, 0.40)]), "#575049")   # latch tongue


def tag(c, w, h, lit):
    """The key's own paper tag, hanging just below the viewpoint, foreground, bottom left."""
    s = min(w, h)
    cx, cy = 0.15 * w, h - 0.085 * s
    ang = math.radians(-14)
    pts = np.array([(-0.17, -0.07), (0.13, -0.07), (0.17, -0.035), (0.17, 0.035), (0.13, 0.07), (-0.17, 0.07)]) * s
    R = np.array([[math.cos(ang), -math.sin(ang)], [math.sin(ang), math.cos(ang)]])
    poly = pts @ R.T + (cx, cy)
    hole_c = np.array([0.125 * s, 0]) @ R.T + (cx, cy)
    c.strip(hole_c, (hole_c[0] + 0.12 * s, h + 10), 4, "#d8cfba" if lit else "#7d735f", off=(4, 6))
    m = c.piece(poly, TAG_LIT if lit else TAG_DIM, holes=[ellipse(hole_c[0], hole_c[1], s * 0.012, s * 0.012)], off=(8, 10), opacity=0.5)
    c.piece(ellipse(hole_c[0], hole_c[1], s * 0.024, s * 0.024), "#c9b27a" if lit else "#5e5039", holes=[ellipse(hole_c[0], hole_c[1], s * 0.012, s * 0.012)], shadow=False)
    let = pen99.letter(["SERVICE"], s * 0.05, 4402, weight=0.15)
    lh, lw = let.shape
    M = cv2.getRotationMatrix2D((lw / 2, lh / 2), 14, 1.0)
    M[0, 2] += cx - 0.02 * s - lw / 2
    M[1, 2] += cy - lh / 2
    lm = cv2.warpAffine(let, M, (w, h))
    penlib.ink_onto(c.img, lm, hexc("#1b1612") if lit else hexc("#2c2419"), alpha=0.95)


def door_open(c, w, h, k):
    """The door swung outward on its left jamb by fraction k (0 closed .. 1 open): its inner face foreshortens to the left."""
    U = lambda u: u * w
    V = lambda v: v * h
    xr = 0.93 - (0.93 - 0.16) * k            # free edge moves left
    dv = 0.05 * k                            # and shrinks in perspective
    poly = np.array([(U(-0.02), V(-0.02)), (U(xr), V(-0.02 + dv)), (U(xr), V(0.95 - dv)), (U(-0.02), V(0.98))], np.float32)
    c.piece(poly, DOOR, off=(10, 12), opacity=0.55)
    # its planks seams and the lock box, foreshortened
    for f in (0.25, 0.5, 0.75):
        x = -0.02 + (xr + 0.02) * f
        c.strip((U(x), V(0.0 + dv * f)), (U(x), V(0.94 - dv * f)), 3, SEAM, shadow=False, jitter=0.5)
    for v0 in (0.08, 0.72):
        c.piece(np.array([(U(-0.02), V(v0)), (U(xr * 0.93), V(v0 + dv * 0.6)), (U(xr * 0.93), V(v0 + 0.065 + dv * 0.3)), (U(-0.02), V(v0 + 0.065))]), BATTEN, off=(6, 8), opacity=0.5)
    lb0, lb1 = -0.02 + (xr + 0.02) * 0.70, -0.02 + (xr + 0.02) * 0.90
    c.piece(np.array([(U(lb0), V(0.33 + dv * 0.2)), (U(lb1), V(0.33 + dv * 0.3)), (U(lb1), V(0.60 - dv * 0.3)), (U(lb0), V(0.60 - dv * 0.2))]), IRON, off=(5, 7))
    # the cupboard's own jamb (right) and sill stay where they were
    c.piece(np.array([(U(0.95), V(-0.02)), (U(1.02), V(-0.02)), (U(1.02), V(0.95)), (U(0.925), V(0.95))]), "#2c2017", off=(6, 8))
    c.piece(np.array([(U(-0.02), V(0.948)), (U(1.02), V(0.948)), (U(1.02), V(1.02)), (U(-0.02), V(1.02))]), SILL, off=(0, -4))
    c.piece(np.array([(U(-0.02), V(-0.02)), (U(1.02), V(-0.02)), (U(1.02), V(0.025)), (U(-0.02), V(0.025))]), "#2c2017", off=(0, 5))


# ------------------------------------------------------------------------------------------------ panels
def panel_closed(w, h, seed, st):
    c = Cut(h, w, seed, ground=WALL, fibre_off=(seed * 37, seed * 53))
    office(c, w, h, clock_t=st["clock"], stranger=st.get("stranger"))
    if st.get("seated"):
        # chair legs and his boots under the desk, all that the gap shows of E0
        dx = 0.17
        c.piece(rect(w * (0.17 + dx), h * 0.80, w * (0.19 + dx), h * 0.94), "#2e2016")
        c.piece(rect(w * (0.29 + dx), h * 0.80, w * (0.31 + dx), h * 0.94), "#2e2016")
        c.piece(rect(w * (0.205 + dx), h * 0.78, w * (0.24 + dx), h * 0.915), TROUS)
        c.piece(rect(w * (0.245 + dx), h * 0.78, w * (0.28 + dx), h * 0.915), TROUS)
        c.piece(np.array([(w * (0.20 + dx), h * 0.905), (w * (0.245 + dx), h * 0.905), (w * (0.25 + dx), h * 0.94), (w * (0.185 + dx), h * 0.94)]), BOOT)
        c.piece(np.array([(w * (0.245 + dx), h * 0.905), (w * (0.285 + dx), h * 0.905), (w * (0.30 + dx), h * 0.94), (w * (0.24 + dx), h * 0.94)]), BOOT)
    if st.get("agent"):
        ax, look = st["agent"]
        agent(c, w * ax, h * 0.942, h * 0.098, pose=st.get("pose", "stand"), look=look, face=True)
    if st.get("near"):
        agent_near(c, w, h)
    door_closed(c, w, h)
    tag(c, w, h, lit=False)
    for (words, cap, u, v, sd) in st.get("sounds", []):
        c.cut_letters(words, cap, (w * u, h * v), SOUND, sd, margin=1.2)
    for (lines, cap, ctr, tip, sd) in st.get("balloons", []):
        c.balloon(lines, cap, (w * ctr[0], h * ctr[1]), (w * tip[0], h * tip[1]), sd)
    return c.u8()


def panel_open(w, h, seed, k, pose, look, clock_t=(4, 11), balloon=None, sounds=()):
    c = Cut(h, w, seed, ground=WALL, fibre_off=(seed * 37, seed * 53))
    office(c, w, h, clock_t=clock_t)
    if k > 0:
        H = h * 0.19 * (0.6 + 0.4 * min(1, k * 1.6))
        hand = (w * (0.035 + 0.93 - (0.93 - 0.16) * k), h * 0.56) if pose == "door" else None
        # while the door is still swinging his door hand is hidden behind it: only his fingers on its edge show
        agent(c, w * 0.57, h * 0.32 + 7.05 * H, H, pose=pose if (pose != "door" or k > 0.7) else "stand", look=look, hand_to=hand, face=True, legs=False)
    if k <= 0.001:
        door_closed(c, w, h)
    else:
        door_open(c, w, h, k)
        if pose == "door":   # his fingers curl round the door's free edge, in front of it
            xr = 0.93 - (0.93 - 0.16) * k
            c.piece(ellipse(w * (xr + 0.012), h * 0.56, h * 0.02, h * 0.045), SKIN, off=(4, 6))
    tag(c, w, h, lit=k > 0.2)
    for (words, cap, u, v, sd) in sounds:
        c.cut_letters(words, cap, (w * u, h * v), SOUND, sd, margin=1.2)
    if balloon:
        lines, cap, ctr, tip, sd = balloon
        c.balloon(lines, cap, (w * ctr[0], h * ctr[1]), (w * tip[0], h * tip[1]), sd)
    return c.u8()


Q = ["Pardon me —", "have you the", "right time?"]
A = ["Ten past four,", "by the clock."]
T = ["Much", "obliged!"]
F = ["Well, here I am...", "and what for?"]
assert " ".join(Q) == LN["question"] and " ".join(A) == LN["answer"] and " ".join(T) == LN["thanks"] and " ".join(F) == LN["forgetting"]

SMALL = [
    # E0: he sits at the desk (chair scrape), then gets up
    dict(clock=(4, 9), seated=True, sounds=[(["scrape"], 50, 0.42, 0.66, 11)]),
    # E0: his boots cross the gap, he passes the crack
    dict(clock=(4, 9), agent=(0.52, (0, 0)), pose="walk", sounds=[(["step"], 46, 0.24, 0.83, 21), (["step"], 46, 0.52, 0.80, 22)]),
    # E1: her hat and face in the ticket-window pane at the top of the crack; he has stopped right by the cupboard,
    # so the lower crack shows only his shirt sleeve and waistcoat (head hidden by the door), boots in the gap
    dict(clock=(4, 10), near=True, stranger=dict(u=0.905), balloons=[(Q, 44, (0.36, 0.20), (0.885, 0.255), 31)]),
    # E2: the keyhole shows the clock at 4:10; his answer, tailed low onto his waistcoat in the crack
    dict(clock=(4, 10), near=True, stranger=dict(u=0.905), balloons=[(A, 46, (0.36, 0.62), (0.893, 0.80), 41)]),
    # E3: her thanks as the hat turns away
    dict(clock=(4, 10), near=True, stranger=dict(u=0.93, turn=True), balloons=[(T, 50, (0.34, 0.50), (0.905, 0.245), 51)]),
    # E4 approach: his boots right at the gap, his body darkens the crack; the latch clicks
    dict(clock=(4, 11), agent=(0.62, (0, 0)), sounds=[(["step"], 46, 0.47, 0.80, 61), (["click"], 52, 0.655, 0.52, 62)]),
]
for st in SMALL[5:6]:
    pass

TIERS = {"P1": (110, 110, 737, 800), "P2": (787, 110, 1413, 800), "P3": (1463, 110, 2090, 800),
         "P4": (110, 850, 737, 1540), "P5": (787, 850, 1413, 1540), "P6": (1463, 850, 2090, 1540),
         "P7": (110, 1590, 1075, 2730), "P8": (1125, 1590, 2090, 2730)}


def p6_state():
    st = dict(SMALL[5])
    return st


def big_agent_close(w, h, seed, pose, look, balloon=None):
    return panel_open(w, h, seed, 1.0, pose, look, balloon=balloon)


def build(reveal=8):
    pg = pen99.sheet99()
    for i, (k, (x0, y0, x1, y1)) in enumerate(TIERS.items()):
        if i >= reveal:
            continue
        w, h = x1 - x0, y1 - y0
        if i < 6:
            st = SMALL[i]
            if i == 5:
                # his body right in front of the crack: a near, larger figure (only the waistcoat shows in the slit)
                st = dict(st)
            im = panel_closed(w, h, 200 + i, st)
            if i == 5:
                # re-render with a near agent standing against the door
                c = Cut(h, w, 205, ground=WALL, fibre_off=(205 * 37, 205 * 53))
                office(c, w, h, clock_t=(4, 11))
                agent(c, w * 0.80, h * 1.25, h * 0.19, pose="stand", face=False)
                door_closed(c, w, h)
                tag(c, w, h, lit=False)
                for (words, cap, u, v, sd) in st["sounds"]:
                    c.cut_letters(words, cap, (w * u, h * v), SOUND, sd, margin=1.2)
                im = c.u8()
        elif i == 6:
            im = panel_open(w, h, 206, 1.0, "door", (0, 0))
        else:
            im = panel_open(w, h, 207, 1.0, "chin", (1, -1),
                            balloon=(F, 54, (0.42, 0.105), (0.555, 0.375), 81))
        pg[y0:y1, x0:x1] = im
    bm = penlib.border_mask(pg.shape[:2], list(TIERS.values())[:reveal], 9, 1200)
    penlib.ink_onto(pg, bm)
    pen99.folio(pg, 2, C["title"])
    return np.clip(np.round(pg), 0, 255).astype(np.uint8)


def beats():
    """Key-beat frames: the key's view as the door is reached and swung open (960x1242)."""
    w, h = 960, 1242
    frames = []
    # b01 closed, his steps arriving under the door
    c = Cut(h, w, 300, ground=WALL, fibre_off=(300, 900))
    office(c, w, h, clock_t=(4, 11)); agent(c, w * 0.66, h * 0.942, h * 0.098, pose="walk", face=True)
    door_closed(c, w, h); tag(c, w, h, False)
    c.cut_letters(["step"], 60, (w * 0.30, h * 0.83), SOUND, 301, margin=1.2)
    frames.append(("closed; his boots cross the gap under the door (step)", c.u8()))
    # b02 he is at the door: the crack goes dark, the latch clicks
    c = Cut(h, w, 302, ground=WALL, fibre_off=(300, 900))
    office(c, w, h, clock_t=(4, 11)); agent(c, w * 0.80, h * 1.25, h * 0.19, pose="stand", face=False)
    door_closed(c, w, h); tag(c, w, h, False)
    c.cut_letters(["click"], 70, (w * 0.655, h * 0.50), SOUND, 303, margin=1.2)
    frames.append(("his body blocks the crack; the latch clicks", c.u8()))
    for j, k in enumerate((0.12, 0.35, 0.65), 3):
        frames.append((f"the door swings open on its left jamb ({int(k * 100)}%), light comes in",
                       panel_open(w, h, 300 + j, k, "door", (0, 0), sounds=[(["creak"], 60, 0.62, 0.86, 310 + j)] if j == 3 else ())))
    frames.append(("open: he looks straight at the key (E4)", panel_open(w, h, 307, 1.0, "door", (0, 0))))
    frames.append(("pencil to his chin, his line (E5); the key stays where it hangs",
                   panel_open(w, h, 308, 1.0, "chin", (1, -1), balloon=(F, 62, (0.42, 0.10), (0.555, 0.375), 82))))
    return frames


def crack_check():
    """Measure the P3-P5 crack: render with agent pieces in magenta and stranger pieces in green and find the rows each
    occupies above the door gap; the strip between them is window counter, rail and wainscot (wall)."""
    keep = {k: globals()[k] for k in ("SHIRT", "WAIST", "TIE", "SKIN", "SKIN2", "HAIR", "TROUS", "COAT", "FACE2", "HAT", "HATBAND")}
    try:
        for k in ("SHIRT", "WAIST", "TIE", "SKIN", "SKIN2", "HAIR", "TROUS"):
            globals()[k] = "#ff00ff"
        for k in ("COAT", "FACE2", "HAT", "HATBAND"):
            globals()[k] = "#00ff00"
        out = {}
        for i in (2, 3, 4):
            x0, y0, x1, y1 = list(TIERS.values())[i]
            w, h = x1 - x0, y1 - y0
            st = dict(SMALL[i]); st.pop("balloons", None)
            im = panel_closed(w, h, 200 + i, st).astype(int)
            r, g, b = im[..., 0], im[..., 1], im[..., 2]
            A = (r - g > 90) & (b - g > 90)
            S = (g - r > 90) & (g - b > 90)
            A[int(h * 0.87):] = False
            ys, ya = np.where(S)[0], np.where(A)[0]
            out[f"P{i + 1}"] = {"stranger_rows": [int(ys.min()), int(ys.max())], "agent_rows": [int(ya.min()), int(ya.max())],
                                "wall_strip_px": int(ya.min() - ys.max() - 1), "pixels_touching": bool((S & A).any())}
        bal = SMALL[3]["balloons"][0]
        out["P4_answer_tail_below_her_face_px"] = int(round((bal[3][1] - 0.27) * (list(TIERS.values())[3][3] - list(TIERS.values())[3][1])))
        return out
    finally:
        globals().update(keep)


CRACK_CHECK = {}


def main():
    CRACK_CHECK.update(crack_check())
    for p in (OUT_JPG.parent, OUT_PNG.parent, BEATS, ROOT / "films/swarm/99-ways/pages"):
        p.mkdir(parents=True, exist_ok=True)
    page = build(8)
    Image.fromarray(page).save(OUT_PNG, compress_level=6)
    Image.fromarray(page).save(OUT_JPG, quality=90, dpi=(300, 300))
    size = OUT_JPG.stat().st_size
    if "--page-only" in sys.argv:
        print(size)
        return
    bd = []
    for f in BEATS.glob("b*.png"):
        f.unlink()
    for j, (desc, im) in enumerate(beats(), 1):
        Image.fromarray(im).save(BEATS / f"b{j:02d}.png")
        bd.append(f"b{j:02d}: {desc}")
    L = np.asarray(Image.fromarray(page).convert("L")).astype(np.float32)
    record = {
        "n": 2, "id": C["id"], "title": C["title"], "rule": C["rule"], "medium": C["medium"], "family": C["family"],
        "canon_revision": CANON["revision"], "declares": C["declares"],
        "file": str(OUT_JPG.relative_to(ROOT)), "master": str(OUT_PNG.relative_to(ROOT)), "beats_dir": str(BEATS.relative_to(ROOT)),
        "sources": ["99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"],
        "made": ["every shape HANDMADE cut paper in code (films/swarm/99-ways/kit/cutpaper99.py): polygons with hand jitter reduced to straight scissor facets, flat papers whose fibre is the LoC 1934 sheet's relative tone, one down-right paper shadow per piece",
                 "the cupboard door's inside (kraft planks, battens, brace, iron lock box) with four openings cut through: jamb crack, gap under the door, keyhole, knot hole; the view never moves, so the openings sit in the same place in panels P1-P6",
                 "the office behind (wall, wainscot, ticket window, wall clock straight across from the keyhole, pendant lamp, desk) and the agent (shirt sleeves, waistcoat, glasses, pencil) and the stranger (hat, coat) in cut paper",
                 "sound words ('scrape', 'step', 'click', 'creak') cut out of pale paper from the shared pen hand; the four lines in the shared cut-paper balloons (penlib.balloon_piece)",
                 "the key's own SERVICE tag on its string in the foreground of every panel (dim in the dark, lit after the door opens)",
                 "hand-ruled borders (penlib.border_mask); folio '02 / The key waits' (pen99.folio)"],
        "events": {"E0": "P1 chair legs and his boots under the desk through the gap, 'scrape'; P2 his boots cross the gap, 'step', a sleeve passes the crack",
                   "E1": "P3 the upper crack: her hat and face behind the ticket-window glass; the lower crack, below the counter: his shirt sleeve and waistcoat edge (he has stopped by the cupboard, head hidden by the door), his boots in the gap; question balloon tailed to her face",
                   "E2": "P4 the keyhole frames the wall clock at 4:10; his answer tailed low onto his sleeve and waistcoat in the lower crack, 366 px below her face",
                   "E3": "P5 her hat turning away in the window pane; thanks balloon tailed to her; his sleeve still below the counter",
                   "E4": "P6 his body darkens the crack, 'step', the latch 'click'; P7 the door swung open on its left jamb, light, he looks straight at the key",
                   "E5": "P8 pencil to his chin, eyes up, 'Well, here I am... and what for?'; the view (the key) has not moved"},
        "lines": LN,
        "beat": "the key's view as the door is reached and swung open: boots in the gap, the crack goes dark, the latch clicks, the door swings out on its left jamb in three steps, light floods, he looks at the key, then the pencil goes to his chin with his line",
        "beat_frames": bd,
        "self_check": {
            "size_px": [page.shape[1], page.shape[0]], "jpeg_bytes": size, "jpeg_quality": 90,
            "in_target_0.4_1.2MB": 400000 <= size <= 1200000,
            "pct_L_lt_60": round(float((L < 60).mean() * 100), 1),
            "viewer_inside_cupboard": "structurally verified: P1-P6 are the door's inner face with the same four openings at the same coordinates; P7-P8 keep the opened door's inner face at left, the cupboard jamb at right and the sill at the bottom",
            "lines_verbatim": True,
            "crack_P3_P5": CRACK_CHECK,
            "known_deviation": "the key's view faces the door, which places its hook on the cupboard's back; page 01 P7 shows the key hanging on the open door's inner face. Not a canon field (the canon says only 'a hook inside the cupboard door'), noted for continuity readers.",
            "pending": "independent blind reading not run by the maker",
        },
    }
    json.dump(record, open(ROOT / "films/swarm/99-ways/pages/02.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps(record["self_check"], indent=1))


if __name__ == "__main__":
    main()

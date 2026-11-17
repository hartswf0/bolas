"""99 ways, page 18 "Fill the balloons" (reader and object; medium: pen-hand).
Six panels E0-E5 drawn in the shared HANDMADE pen line on the LoC 1934 sheet. Every balloon is drawn EMPTY, its outline
the exact size and shape its line needs; the four canon lines wait in the outer margin as cut-out slips, each slip the
same outline as its balloon, with a scissor line round it and a paste tab, in shuffled order. The reader matches slip to
balloon (by shape and by sense); the film's beat cuts each slip out and pastes it home.
Pen set (clock, cupboard, key, SERVICE door) from build_page03 (the shared pen hand); figures drawn here in the same pen.
Run: python3 -I p18_fill_the_balloons.py"""
import json
import math
import random
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/kit")
import pen99  # noqa: E402
from pen99 import penlib, ROOT  # noqa: E402
from cutpaper99 import hexc  # noqa: E402
import build_page03 as b3  # noqa: E402  (pen set: pen, clock, cupboard, key, service_door, letters)

CANON = json.load(open(ROOT / "films/swarm/99-ways/canon.json"))
C = [c for c in CANON["constraints"] if c["id"] == "fill-the-balloons"][0]
LN = {k: v["text"] for k, v in CANON["incident"]["lines"].items()}
SRC = ROOT / "films/sources/99-ways"
OUT_JPG = ROOT / "assets/pages/99-ways/18-fill-the-balloons.jpg"
OUT_PNG = SRC / "masters/18-fill-the-balloons.png"
BEATS = SRC / "beats/18"
W, H = pen99.PAGE_W, pen99.PAGE_H
INK = penlib.INK
pen, letters = b3.pen, b3.letters
SLIP_PAPER = np.float32([250, 248, 241])

BAL = {  # line key: (lines, cap)
    "question": (["Pardon me —", "have you the", "right time?"], 40),
    "answer": (["Ten past four,", "by the clock."], 40),
    "thanks": (["Much", "obliged!"], 46),
    "forgetting": (["Well, here I am...", "and what for?"], 36),
}
for k, (ls, _) in BAL.items():
    assert " ".join(ls) == LN[k], k
SLIP_ORDER = ["thanks", "forgetting", "question", "answer"]          # shuffled in the margin


# ------------------------------------------------------------------ balloon geometry (shared by balloon and slip)
def bshape(key):
    lines, cap = BAL[key]
    let = pen99.letter(lines, cap, 1800 + list(BAL).index(key))
    th, tw = let.shape
    rx = tw * 0.5 * 1.16 + cap * 0.45
    ry = th * 0.5 * 1.08 + cap * 0.40
    rnd = random.Random(1810 + list(BAL).index(key))
    ph = [rnd.uniform(0, 6.28) for _ in range(3)]
    return let, rx, ry, ph


def ell_pts(cx, cy, rx, ry, ph, n=120):
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    rr = 1 + .022 * np.sin(a * 3 + ph[0]) + .012 * np.sin(a * 5 + ph[1])
    return np.stack([cx + rx * rr * np.cos(a), cy + ry * rr * np.sin(a)], 1)


def empty_balloon(cv, key, cx, cy, tip, seed):
    """the balloon outline with its tail, drawn in pen, empty"""
    _, rx, ry, ph = bshape(key)
    pts = ell_pts(cx, cy, rx, ry, ph)
    a0 = math.atan2((tip[1] - cy) / ry, (tip[0] - cx) / rx)
    tw = 0.20
    ang = np.arctan2((pts[:, 1] - cy) / ry, (pts[:, 0] - cx) / rx)
    d = np.angle(np.exp(1j * (ang - a0)))
    keep = np.abs(d) > tw
    # outline as one pen stroke from one side of the tail round to the other
    idx = np.nonzero(keep)[0]
    start = np.argmax(np.abs(d) < tw)
    order = [(start + k) % len(pts) for k in range(len(pts))]
    ring = [pts[i] for i in order if keep[i]]
    b1 = np.array([cx + rx * math.cos(a0 + tw), cy + ry * math.sin(a0 + tw)])
    b2 = np.array([cx + rx * math.cos(a0 - tw), cy + ry * math.sin(a0 - tw)])
    tipv = np.float32(tip)
    mid = (b1 + b2) / 2
    perp = np.array([-(tipv - mid)[1], (tipv - mid)[0]]) * 0.10
    q = lambda p0, p1, c, n=16: [(1 - t) ** 2 * p0 + 2 * (1 - t) * t * c + t ** 2 * p1 for t in np.linspace(0, 1, n)]
    path = [b1] + ring + [b2] + q(b2, tipv, mid + perp) + q(tipv, b1, mid + perp * .6)
    pen(cv, path, 5, seed)
    return rx, ry


def slip(cv, key, cx, cy, seed, state="margin"):
    """state 'margin': drawn on the page with scissor line and tab; 'hole': the cut-out hole left in the margin;
    'paper': the cut slip as a paper piece (for the beats)"""
    let, rx, ry, ph = bshape(key)
    cut = ell_pts(cx, cy, rx + 20, ry + 20, ph)
    # the paste tab on the slip's top, joined along a dotted fold
    tx = cx - rx * 0.28
    tab = [(tx - 54, cy - ry - 16), (tx - 40, cy - ry - 62), (tx + 40, cy - ry - 62), (tx + 54, cy - ry - 16)]
    if state == "paper":
        m = np.zeros(cv.shape[:2], np.uint8)
        cv2.fillPoly(m, [np.int32(ell_pts(cx, cy, rx + 6, ry + 6, ph) * 4)], 255, cv2.LINE_AA, shift=2)
        penlib.shadow_onto(cv, m, off=7, blur=5, opacity=0.38)
        cv[:] = cv * (1 - m[..., None] / 255) + SLIP_PAPER * (m[..., None] / 255)
    if state in ("margin", "paper"):
        pen(cv, list(ell_pts(cx, cy, rx, ry, ph)), 5, seed, closed=True)
        sub = np.zeros(cv.shape[:2], np.uint8)
        th, tw = let.shape
        y0, x0 = int(cy - th / 2), int(cx - tw / 2)
        sub[y0:y0 + th, x0:x0 + tw] = let
        penlib.ink_onto(cv, sub)
    if state in ("margin", "hole"):
        # scissor line: dashes round the slip and its tab
        ring = list(cut)
        for k in range(0, len(ring), 3):
            a, bb = ring[k], ring[(k + 1) % len(ring)]
            pen(cv, [a, bb], 2.6, seed + 100 + k)
        for a, bb in zip(tab[:-1], tab[1:]):
            n = int(np.hypot(*(np.float32(bb) - a)) / 14)
            for k in range(0, n, 2):
                p0 = np.float32(a) + (np.float32(bb) - a) * k / n
                p1 = np.float32(a) + (np.float32(bb) - a) * (k + 1) / n
                pen(cv, [p0, p1], 2.6, seed + 300 + k)
        if state == "margin":
            # the fold: dotted, and the tab's diagonal hatching
            for k in range(9):
                x = tx - 50 + k * 12.5
                m = np.zeros(cv.shape[:2], np.uint8)
                cv2.circle(m, (int(x), int(cy - ry - 16)), 2, 255, -1, cv2.LINE_AA)
                penlib.ink_onto(cv, m)
            for k in range(5):
                x = tx - 34 + k * 17
                pen(cv, [(x, cy - ry - 24), (x + 14, cy - ry - 54)], 2, seed + 400 + k)
            scissors(cv, cx + rx + 10, cy + ry * 0.55, seed + 500)
    return rx, ry


def scissors(cv, x, y, seed):
    """a small pen pictogram of scissors on the cut line"""
    pen(cv, b3.circle_pts(x - 10, y + 12, 8, 14), 2.6, seed, closed=True)
    pen(cv, b3.circle_pts(x + 10, y + 12, 8, 14), 2.6, seed + 1, closed=True)
    pen(cv, [(x - 5, y + 5), (x + 12, y - 26)], 2.6, seed + 2)
    pen(cv, [(x + 5, y + 5), (x - 12, y - 26)], 2.6, seed + 3)


# ------------------------------------------------------------------ figures in pen line (HANDMADE)
def T(pts, s, at, f=1, rot=0.0, pivot=(0, -490)):
    p = np.asarray(pts, np.float32) - np.float32(pivot)
    a = math.radians(rot)
    p = np.stack([p[:, 0] * math.cos(a) - p[:, 1] * math.sin(a), p[:, 0] * math.sin(a) + p[:, 1] * math.cos(a)], 1) + np.float32(pivot)
    p[:, 0] *= f
    return [tuple(v) for v in p * s + np.float32(at)]


def oval(cx, cy, rx, ry, n=36):
    return [(cx + rx * math.cos(t), cy + ry * math.sin(t)) for t in np.linspace(0, 2 * math.pi, n, endpoint=False)]


ARMS = {
    "stand": ([(-82, -460), (-96, -370), (-98, -282)], [(82, -460), (96, -370), (98, -282)]),
    "walk": ([(-82, -460), (-112, -378), (-136, -300)], [(82, -460), (110, -378), (136, -304)]),
    "desk": ([(-82, -460), (-104, -370), (-80, -300)], [(82, -460), (104, -370), (80, -300)]),
    "reach": ([(-82, -460), (-98, -370), (-100, -282)], [(82, -460), (170, -440), (262, -430)]),
    "chin": ([(-82, -460), (-98, -370), (-100, -282)], [(82, -460), (120, -372), (44, -488)]),
}


def arm_pen(cv, pts, s, at, f, seed, w=34):
    P = np.float32(T(pts, s, at, f))
    sides = [[], []]
    for i in range(len(P)):
        d = P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]
        n = np.float32([-d[1], d[0]]) / (np.linalg.norm(d) + 1e-6) * w * s / 2
        sides[0].append(P[i] + n)
        sides[1].append(P[i] - n)
    pen(cv, sides[0], 4, seed)
    pen(cv, sides[1], 4, seed + 1)
    pen(cv, [sides[0][-1], sides[1][-1]], 3.5, seed + 2)                # cuff
    e = P[-1] + (P[-1] - P[-2]) / (np.linalg.norm(P[-1] - P[-2]) + 1e-6) * 14 * s
    pen(cv, oval(e[0], e[1], 13 * s, 13 * s, 18), 3.5, seed + 3, closed=True)   # hand
    return e


def agent(cv, at, s=1.0, f=1, arms="stand", walk=False, head_rot=0.0, seed=0, legs=True):
    """the agent in pen: hair, glasses, collar and tie, waistcoat with buttons, shirt sleeves, pencil. f=+1 faces right.
    Returns (mouth point, front hand point)."""
    hp = lambda pts: T(pts, s, at, f, head_rot)
    bp = lambda pts: T(pts, s, at, f)
    # legs
    if legs:
        if walk:
            pen(cv, bp([(-72, -282), (-104, 0)]), 4, seed + 1)
            pen(cv, bp([(-40, 0), (0, -186), (44, 0)]), 4, seed + 2)
            pen(cv, bp([(72, -282), (106, 0)]), 4, seed + 3)
            pen(cv, bp([(-112, 0), (-36, 0)]), 5, seed + 4)
            pen(cv, bp([(40, 0), (124, 0)]), 5, seed + 5)
        else:
            pen(cv, bp([(-72, -282), (-66, 0)]), 4, seed + 1)
            pen(cv, bp([(-10, 0), (0, -176), (10, 0)]), 4, seed + 2)
            pen(cv, bp([(72, -282), (66, 0)]), 4, seed + 3)
            pen(cv, bp([(-70, 0), (-6, 0)]), 5, seed + 4)
            pen(cv, bp([(6, 0), (84, 0)]), 5, seed + 5)
    # waistcoat and shirt
    pen(cv, bp([(-30, -480), (-82, -464), (-74, -282), (0, -266), (74, -282), (82, -464), (30, -480)]), 4, seed + 6)
    pen(cv, bp([(-36, -472), (0, -400), (36, -472)]), 4, seed + 7)
    for k, yy in enumerate((-384, -344, -304)):
        pen(cv, b3.circle_pts(*bp([(0, yy)])[0], 4 * s, 8), 3, seed + 8 + k, closed=True)
    pen(cv, bp([(-26, -482), (0, -456), (26, -482)]), 3.5, seed + 11)                 # collar
    pen(cv, bp([(0, -456), (-9, -440), (0, -404)]), 3, seed + 12)                     # tie (into the V)
    pen(cv, bp([(0, -456), (9, -440), (0, -404)]), 3, seed + 13)
    back, front = ARMS[arms]
    arm_pen(cv, back, s, at, f, seed + 20)
    hand = arm_pen(cv, front, s, at, f, seed + 30)
    # pencil in the front hand
    if arms == "chin":
        q = [hand + np.float32([0, 8 * s]), hand + np.float32([-6 * f * s, -46 * s])]
    else:
        q = [hand + np.float32([2 * f * s, 10 * s]), hand + np.float32([14 * f * s, -44 * s])]
    pen(cv, [tuple(q[0] + np.float32([-3, 0])), tuple(q[1] + np.float32([-3, 0]))], 3, seed + 40)
    pen(cv, [tuple(q[0] + np.float32([3, 0])), tuple(q[1] + np.float32([3, 0]))], 3, seed + 41)
    # neck and head
    pen(cv, bp([(-14, -500), (-14, -480)]), 3.5, seed + 50)
    pen(cv, bp([(14, -500), (14, -480)]), 3.5, seed + 51)
    pen(cv, hp(oval(0, -548, 44, 54)), 4.5, seed + 52, closed=True)
    pen(cv, hp([(-44, -556), (-38, -592), (-8, -606), (26, -600), (44, -572)]), 4, seed + 53)     # hair
    pen(cv, hp([(-30, -594), (-4, -576), (30, -588)]), 3, seed + 54)
    for gx in (-10, 22):
        pen(cv, hp(oval(gx, -552, 13, 11, 16)), 3, seed + 60 + gx, closed=True)                    # glasses
    pen(cv, hp([(3, -553), (9, -553)]), 2.5, seed + 70)
    pen(cv, hp([(12, -544), (18, -526), (10, -523)]), 3, seed + 71)                                  # nose (faces f)
    pen(cv, hp([(-2, -510), (18, -511)]), 3, seed + 72)                                              # mouth
    pen(cv, hp([(-44, -556), (-52, -548), (-48, -534), (-42, -532)]), 3, seed + 73)                  # ear
    mouth = hp([(14, -510)])[0]
    return mouth, hand


def stranger(cv, at, s=1.0, f=-1, seed=0):
    """the stranger in pen, a woman traveller seen to the waist behind the glass: a close bell cloche with a ribbon
    band, a bow at the back and a flower at the front; bobbed hair curling out below it and a kiss curl at the cheek;
    a slender neck; a travelling coat with sloping shoulders, a deep scalloped fur collar and a brooch, a nipped
    waist and a single row of buttons set to one side. Nothing in it echoes the agent's waistcoat V. f=-1 faces left."""
    p = lambda pts: T(pts, s, at, f, 0, (0, 0))
    # coat: sloping shoulders, nipped waist, flaring below
    pen(cv, p([(-30, -350), (-66, -322), (-80, -270), (-70, -160), (-86, -40), (-94, 0)]), 4, seed)
    pen(cv, p([(30, -350), (66, -322), (80, -270), (70, -160), (86, -40), (94, 0)]), 4, seed + 1)
    pen(cv, p([(-70, -160), (-20, -152), (20, -152), (70, -160)]), 3, seed + 2)                  # belt
    pen(cv, p([(14, -340), (26, -250), (22, -160), (30, 0)]), 3, seed + 3)                       # wrap front edge
    for k, yy in enumerate((-226, -186, -110, -60)):
        pen(cv, b3.circle_pts(*p([(38, yy)])[0], 3.6 * s, 8), 2.8, seed + 4 + k, closed=True)
    # deep fur collar: a scalloped ring round the neck
    col = []
    for t in np.linspace(math.pi * 1.02, math.pi * 1.98, 9):
        col.append((math.cos(t) * 58, -318 - math.sin(t) * 40))
    sc_ = []
    for (x_a, y_a), (x_b, y_b) in zip(col, col[1:]):
        mx_, my_ = (x_a + x_b) / 2, (y_a + y_b) / 2 + 9
        sc_ += [(x_a, y_a), (mx_, my_)]
    sc_.append(col[-1])
    pen(cv, p(sc_), 3.5, seed + 9)
    pen(cv, p([(-56, -322), (-34, -352), (-14, -356)]), 3.5, seed + 10)
    pen(cv, p([(56, -322), (34, -352), (14, -356)]), 3.5, seed + 11)
    pen(cv, b3.circle_pts(*p([(30, -300)])[0], 7 * s, 10), 3, seed + 12, closed=True)            # brooch
    # slender neck
    pen(cv, p([(-11, -372), (-12, -352)]), 3, seed + 13)
    pen(cv, p([(11, -372), (12, -352)]), 3, seed + 14)
    # face: a smaller oval, lashes, a cupid's-bow mouth
    pen(cv, p(oval(0, -412, 34, 42)), 4.2, seed + 15, closed=True)
    pen(cv, p(oval(14, -414, 4.5, 3, 8)), 2.5, seed + 16, closed=True)                           # eye
    pen(cv, p([(10, -419), (6, -426)]), 2.2, seed + 17)                                           # lashes
    pen(cv, p([(16, -420), (15, -428)]), 2.2, seed + 18)
    pen(cv, p([(20, -419), (24, -425)]), 2.2, seed + 19)
    pen(cv, p([(31, -418), (39, -402), (31, -398)]), 3, seed + 20)                                # nose
    pen(cv, p([(16, -386), (21, -390), (24, -387), (27, -390), (31, -386), (24, -381), (16, -386)]), 2.6, seed + 21)  # lips
    pen(cv, b3.circle_pts(*p([(-26, -394)])[0], 3.6 * s, 8), 2.6, seed + 22, closed=True)          # earring
    # bobbed hair below the hat: curls at the nape and a kiss curl on the cheek
    pen(cv, p([(-34, -430), (-46, -412), (-42, -392), (-52, -380), (-42, -366), (-30, -372)]), 3.5, seed + 23)
    pen(cv, p([(-30, -404), (-36, -388), (-28, -380)]), 3, seed + 24)
    pen(cv, p([(30, -436), (36, -426), (28, -420), (24, -428), (30, -432)]), 2.8, seed + 25)    # kiss curl
    # cloche: a close bell crown pulled down to the brow, its brim turned down round the head
    pen(cv, p([(-48, -404), (-50, -440), (-44, -474), (-22, -496), (6, -500), (30, -490), (44, -468), (48, -444),
               (54, -436), (40, -434), (26, -440)]), 4.6, seed + 26)
    pen(cv, p([(-48, -404), (-36, -414), (-30, -430)]), 4, seed + 27)
    pen(cv, p([(-48, -456), (-20, -450), (20, -450), (47, -456)]), 3, seed + 28)                    # ribbon band
    pen(cv, p([(-48, -466), (-20, -460), (20, -460), (46, -466)]), 3, seed + 29)
    # bow at the back of the band
    pen(cv, p([(-46, -460), (-66, -476), (-70, -456), (-46, -460), (-64, -444), (-56, -430)]), 3, seed + 30)
    # a flower at the front of the band: five petals round a centre
    fx, fy = 32, -472
    for k in range(5):
        t = k * 2 * math.pi / 5
        pen(cv, p(oval(fx + 8 * math.cos(t), fy + 8 * math.sin(t), 5.5, 5.5, 10)), 2.4, seed + 31 + k, closed=True)
    return p([(32, -386)])[0]


def window(cv, x0, y0, x1, y1, seed):
    """the ticket window: frame, glazing bars, counter ledge, TICKET OFFICE on the glass"""
    pen(cv, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 5, seed, closed=True)
    pen(cv, [(x0 + 22, y0 + 22), (x1 - 22, y0 + 22), (x1 - 22, y1 - 22), (x0 + 22, y1 - 22)], 3, seed + 1, closed=True)
    pen(cv, [(x0 + 22, y0 + (y1 - y0) * 0.27), (x1 - 22, y0 + (y1 - y0) * 0.27)], 3, seed + 3)
    letters(cv, ["TICKET OFFICE"], 28, (x0 + x1) / 2, y0 + (y1 - y0) * 0.14, seed + 4)
    pen(cv, [(x0 - 30, y1), (x1 + 30, y1), (x1 + 30, y1 + 24), (x0 - 30, y1 + 24)], 4, seed + 5, closed=True)


def mask_rect(cv, x0, y0, x1, y1, ground):
    """the panel paper in front: hide lines behind an object (the window frame hides her lower coat etc.)"""
    cv[y0:y1, x0:x1] = ground[y0:y1, x0:x1]


def memo_pen(cv, cx, cy, w, seed, deg=-4):
    h = w * 0.58
    a = math.radians(deg)
    R = lambda p: (cx + p[0] * math.cos(a) - p[1] * math.sin(a), cy + p[0] * math.sin(a) + p[1] * math.cos(a))
    pen(cv, [R(p) for p in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))], 3.5, seed, closed=True)
    m = pen99.letter(["4:15 - open", "SERVICE door.", "Key in cupboard."], w * 0.085, seed + 1)
    M = cv2.getRotationMatrix2D((m.shape[1] / 2, m.shape[0] / 2), -deg, 1.0)
    M[0, 2] += cx - m.shape[1] / 2
    M[1, 2] += cy - m.shape[0] / 2
    penlib.ink_onto(cv, cv2.warpAffine(m, M, (cv.shape[1], cv.shape[0])))


# ------------------------------------------------------------------ panels
PX = [110, 885]
PY = [110, 990, 1870]
PW, PH = 735, 840
FL = PH - 60
S = 0.84
TIPS = {}


def panel(n, ground):
    cv = ground.copy()
    pen(cv, [(0, FL), (PW, FL)], 3, 1830 + n)                                # floor line
    if n == 1:      # E0
        agent(cv, (250, FL - 10), S, 1, arms="desk", seed=1840, legs=False)
        g = cv.copy()
        pen(cv, [(40, 560), (640, 560), (640, 590), (40, 590)], 4.5, 1850, closed=True)       # desk top
        cv[562:588, 42:638] = ground[562:588, 42:638]
        cv[592:FL - 2, 60:620] = ground[592:FL - 2, 60:620]
        pen(cv, [(40, 560), (640, 560), (640, 590), (40, 590)], 4.5, 1850, closed=True)
        pen(cv, [(70, 590), (70, FL)], 4.5, 1851)
        pen(cv, [(610, 590), (610, FL)], 4.5, 1852)
        pen(cv, [(90, 590), (90, 720), (590, 720), (590, 590)], 3.5, 1853)
        memo_pen(cv, 470, 470, 260, 1854)
        b3.clock(cv, 610, 120, 50, 4, 9, 1855)
    elif n in (2, 3, 4):
        wx0, wx1 = 400, 715
        if n != 3:      # panel 3 turns to the clock; the window is out of shot to the right
            sx = (wx0 + wx1) / 2 + (40 if n == 4 else 0)
            st_mouth = stranger(cv, (sx, 712), 0.92, f=(1 if n == 4 else -1), seed=1860 + n)   # seen to the waist; the counter hides the rest
            cv[590 - 22:FL - 2, wx0:wx1] = ground[590 - 22:FL - 2, wx0:wx1]          # the counter hides her below the glass
            window(cv, wx0, 110, wx1, 590, 1870 + n)
            pen(cv, [(wx0 - 30, 614), (wx0 - 30, FL)], 4, 1875 + n)
        if n == 3:
            b3.clock(cv, 130, 140, 62, 4, 10, 1880)
            m, _ = agent(cv, (250, FL), S, -1, arms="stand", head_rot=24, seed=1885)
            TIPS[n] = m
        else:
            m, _ = agent(cv, (180 if n == 2 else 150, FL), S, 1, arms="walk", walk=True, seed=1890 + n)
            TIPS[n] = st_mouth
    else:
        b3.service_door(cv, 560, 150, 700, FL, 1900 + n)
        b3.cupboard(cv, 300, 210, 500, FL - 4, 1.0 if n == 6 else 0.82, 1910 + n)
        if n == 5:
            agent(cv, (150, FL), S, 1, arms="reach", seed=1920)
        else:
            m, _ = agent(cv, (150, FL), S, 1, arms="chin", head_rot=-4, seed=1925)
            TIPS[n] = m
    return cv


BALLOON_AT = {2: ("question", (205, 138)), 3: ("answer", (510, 330)), 4: ("thanks", (215, 128)), 6: ("forgetting", (450, 96))}
SLIP_Y = {"thanks": 300, "forgetting": 760, "question": 1330, "answer": 1960}
SLIP_X = 1880


def build(placed=(), lifting=None):
    """placed: line keys whose slips have been cut out and pasted into their balloons (beats);
    lifting: (key, t) a slip on its way, t in 0..1"""
    pg = pen99.sheet99()
    boxes = []
    centres = {}
    for n in range(1, 7):
        x0, y0 = PX[(n - 1) % 2], PY[(n - 1) // 2]
        ground = pg[y0:y0 + PH, x0:x0 + PW].copy()
        cv = panel(n, ground)
        if n in BALLOON_AT:
            key, (cx, cy) = BALLOON_AT[n]
            tip = TIPS[n]
            empty_balloon(cv, key, cx, cy, tip, 1940 + n)
            centres[key] = (x0 + cx, y0 + cy)
        pg[y0:y0 + PH, x0:x0 + PW] = cv
        boxes.append((x0, y0, x0 + PW, y0 + PH))
    bm = penlib.border_mask(pg.shape[:2], boxes, 8, 1960)
    penlib.ink_onto(pg, bm)
    for k in SLIP_ORDER:
        if k in placed or (lifting and lifting[0] == k):
            slip(pg, k, SLIP_X, SLIP_Y[k], 1970 + SLIP_ORDER.index(k) * 7, state="hole")
        else:
            slip(pg, k, SLIP_X, SLIP_Y[k], 1970 + SLIP_ORDER.index(k) * 7, state="margin")
    for k in placed:
        slip(pg, k, *centres[k], 1990 + SLIP_ORDER.index(k), state="paper")
    if lifting:
        k, t = lifting
        a, b = np.float32([SLIP_X, SLIP_Y[k]]), np.float32(centres[k])
        p = a + (b - a) * t + np.float32([0, -120 * math.sin(math.pi * t)])
        slip(pg, k, float(p[0]), float(p[1]), 1990 + SLIP_ORDER.index(k), state="paper")
    pen99.folio(pg, 18, C["title"])
    return np.clip(np.round(pg), 0, 255).astype(np.uint8), centres


def main():
    for p in (OUT_JPG.parent, OUT_PNG.parent, BEATS):
        p.mkdir(parents=True, exist_ok=True)
    page, centres = build()
    Image.fromarray(page).save(OUT_PNG, compress_level=6)
    Image.fromarray(page).save(OUT_JPG, quality=90, dpi=(300, 300))
    size = OUT_JPG.stat().st_size
    print("jpeg", size)
    if "--page-only" in sys.argv:
        return
    for f in BEATS.glob("b*.png"):
        f.unlink()
    seq = [((), None, "b01: the page: four empty balloons, the four slips waiting in the margin"),
           ((), ("question", 0.5), "b02: the question slip cut out along its scissor line and carried toward panel 2"),
           (("question",), None, "b03: the question pasted into its balloon (panel 2, tail to the stranger)"),
           (("question", "answer"), None, "b04: + the answer pasted (panel 3, tail to the agent under the clock)"),
           (("question", "answer", "thanks"), None, "b05: + the thanks pasted (panel 4, tail to the stranger turning away)"),
           (("question", "answer", "thanks", "forgetting"), None, "b06: + the forgetting pasted (panel 6, tail to the agent at the cupboard); the margin holds only the cut-out holes")]
    bd = []
    for j, (pl, lf, d) in enumerate(seq, 1):
        im = page if j == 1 else build(pl, lf)[0]
        Image.fromarray(im).resize((960, 1242), Image.LANCZOS).save(BEATS / f"b{j:02d}.png")
        bd.append(d)
    record = {
        "n": 18, "id": C["id"], "title": C["title"], "rule": C["rule"], "medium": C["medium"], "family": C["family"],
        "canon_revision": CANON["revision"], "declares": C["declares"],
        "file": str(OUT_JPG.relative_to(ROOT)), "master": str(OUT_PNG.relative_to(ROOT)), "beats_dir": str(BEATS.relative_to(ROOT)),
        "build": "films/swarm/99-ways/build/p18_fill_the_balloons.py",
        "sources": ["99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"],
        "made": [
            "six panels drawn entirely in the shared HANDMADE pen line (penlib.brush_line via build_page03.pen) on the LoC 1934 sheet: the agent (hair, glasses, collar and tie, waistcoat with three buttons, shirt sleeves, pencil), the stranger (hat with band, coat with collar and buttons) behind the glazed ticket window lettered TICKET OFFICE, desk, memo slip with the canon text, wall clock (4:09 at the desk, 4:10 at the answer), cupboard hinged on the left jamb with the key on its hook and its SERVICE tag, SERVICE door",
            "four balloons drawn EMPTY in pen with their tails to the speakers; each balloon outline is computed from its own line in the pen hand (same size and wobble as its slip)",
            "the four canon lines lettered in the shared pen hand on four cut-out slips in the outer margin, shuffled (thanks, forgetting, question, answer): the same outline as the balloon, a dashed scissor line, a hatched paste tab on a dotted fold, a small pen scissors",
            "hand-ruled borders (penlib.border_mask); folio '18 / Fill the balloons' (pen99.folio)",
            "beats: each slip cut out (its hole left in the margin) and pasted into its balloon as a paper piece with one shadow"],
        "events": {"E0": "panel 1: the agent behind his desk, the memo '4:15 - open SERVICE door. Key in cupboard.' on it, clock at 4:09",
                   "E1": "panel 2: walking past the ticket window; the stranger behind the glass; empty balloon tailed to her",
                   "E2": "panel 3: he turns to the wall clock (4:10); empty balloon tailed to him",
                   "E3": "panel 4: she turns away; empty balloon tailed to her; he walks on",
                   "E4": "panel 5: he swings the cupboard door open on its left jamb; key on its hook with the SERVICE tag",
                   "E5": "panel 6: pencil to his chin before the open cupboard; empty balloon tailed to him; SERVICE door shut"},
        "lines": LN,
        "slips": {k: {"lines": BAL[k][0], "margin_order": SLIP_ORDER.index(k) + 1, "balloon_panel": [n for n, v in BALLOON_AT.items() if v[0] == k][0]} for k in BAL},
        "beat": "the slips are cut out of the margin one by one and pasted into their balloons: question, answer, thanks, forgetting",
        "beat_frames": bd,
        "self_check": {"size_px": [page.shape[1], page.shape[0]], "jpeg_bytes": size, "jpeg_quality": 90,
                       "in_target_0.4_1.2MB": 400000 <= size <= 1200000,
                       "balloons_on_page_all_empty": True, "slips": 4, "slips_shuffled": SLIP_ORDER,
                       "slip_outline_equals_balloon_outline": True, "lines_verbatim": True,
                       "pending": "independent blind reading not run by the maker"},
    }
    json.dump(record, open(ROOT / "films/swarm/99-ways/pages/18.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps(record["self_check"], indent=1))


if __name__ == "__main__":
    main()

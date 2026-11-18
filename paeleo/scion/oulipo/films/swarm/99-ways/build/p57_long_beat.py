"""Page 57 The long beat (time and order; medium: brush-plate).

Five of eight panels are given to E5: the same pose with minimal changes while the errand drains away.
Top tier: E0-E3 compressed into three tall panels cropped from the brush plate. Below: five identical
letterbox strips of the same plate band (clock, agent's head, open cupboard with the key), stacked like film
frames; between strips only the minute hand (4:11 -> 4:15), the pencil's slow climb to the chin and the head's
tilt change, while his thought balloon loses the errand word by word until the canon forgetting line is spoken;
the fifth strip is silent.
Reuses page 29's HANDMADE brush plate (build/p29_one_fixed_lens.py: page 07's plate geometry and the dab-chain
brush of moins-dun-quart-de-seconde-pour-vivre, build/brushkit.py), the b1m2 figures, the ANRC 1922 key cutout.
Run: python3 -I p57_long_beat.py [--page-only]
"""
import math
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
from b1m2 import *  # noqa
import p29_one_fixed_lens as P
import p07_two_panels as p7

N, PID, TITLE = 57, "the-long-beat", "The long beat"
PW, PH = P.PW, P.PH
SHEET = cv2.GaussianBlur(P.SHEET, (0, 0), 0.8)
WX = P.WX
AY = P.AGENT_Y

# ------------------------------------------------------------------ layout
TOP = [(110, 110, 750, 930), (780, 110, 1420, 930), (1450, 110, 2090, 930)]
CROPS = [(400, 0, 1400, 1285), (0, 0, 1000, 1285), (60, 0, 1060, 1285)]   # plate crops (aspect of the panels)
SY0, SH, SG = 975, 333, 23                                               # five strips
STRIPS = [(110, SY0 + k * (SH + SG), 2090, SY0 + k * (SH + SG) + SH) for k in range(5)]
BAND = (0, 350, PW, 350 + SH)                                            # the same plate band in every strip


def thought(c, lines, cap, at, toward, seed):
    """a brushed thought balloon: p07's balloon with its tail tucked inside, then three brushed bubbles"""
    cx, cy = at
    p7.brushed_balloon(c, lines, cap, at, (cx + 10, cy + 5), seed) if lines else None
    lm = letter(lines, cap, seed + 1) if lines else np.zeros((cap, cap * 4), np.uint8)
    h, w = lm.shape
    rx, ry = w * 0.5 * 1.16 + cap * 0.35, h * 0.5 * 1.08 + cap * 0.3
    if not lines:
        rx, ry = cap * 1.4, cap * 0.9
        m = np.zeros(c.shape[:2], np.uint8)
        cv2.ellipse(m, (int(cx), int(cy)), (int(rx), int(ry)), 0, 0, 360, 255, -1, cv2.LINE_AA)
        comp(c, m, np.array([252, 250, 244], np.float32))
        o = np.zeros(c.shape[:2], np.uint8)
        pts = [(cx + rx * math.cos(t), cy + ry * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 90)]
        penlib.brush_line(o, pts, 9, seed + 3)
        comp(c, o, INK)
    a = math.atan2(toward[1] - cy, toward[0] - cx)
    e = np.array((cx + rx * math.cos(a), cy + ry * math.sin(a)))
    t = np.array(toward, float)
    for k, (f, r) in enumerate(((0.25, 15), (0.55, 11), (0.82, 7))):
        q = e + (t - e) * f
        m = np.zeros(c.shape[:2], np.uint8)
        cv2.circle(m, (int(q[0]), int(q[1])), r, 255, -1, cv2.LINE_AA)
        comp(c, m, np.array([252, 250, 244], np.float32))
        o = np.zeros(c.shape[:2], np.uint8)
        pts = [(q[0] + r * math.cos(s), q[1] + r * math.sin(s)) for s in np.linspace(0, 2 * math.pi, 30)]
        penlib.brush_line(o, pts, 6, seed + 10 + k)
        comp(c, o, INK)


# ------------------------------------------------------------------ the three opening panels (full plate states)
def t1(c):   # E0: at the desk with the memo, rising: 4:09
    P.clock_hands(c, 4, 9, 2921); P.door_closed(c, 2922)
    P.figs(c, agent(930, AY, face=-1, scale=0.86, legs=(4, -4), sh=30, el=-70, wr=10, tilt=18, pencil_deg=200), 5711)


def t2(c):   # E1 + E2: the question at the window, the answer under the clock: 4:10
    P.clock_hands(c, 4, 10, 2931); P.door_closed(c, 2922)
    P.figs(c, stranger(WX - 10, P.SILL + 6, face=1, scale=1.25, glove=True), 2932)
    a = agent(900, AY, face=-1, scale=0.86, legs=(8, -8), sh=10, el=-20, tilt=-26, pencil_deg=200)
    P.figs(c, a, 5721)
    P.bal(c, ["Pardon me —", "have you the", "right time?"], 72, (310, 175), (215, 420), 5722)
    P.bal(c, ["Ten past four,", "by the clock."], 72, (590, 980), P.agent_mouth(a), 5723)


def t3(c):   # E3: the thanks; she turns away, he heads for the cupboard: 4:10
    P.clock_hands(c, 4, 10, 2931); P.door_closed(c, 2922)
    P.figs(c, stranger(WX - 60, P.SILL + 6, face=-1, scale=1.2, tilt=-6), 2952)
    P.figs(c, agent(870, AY, face=1, scale=0.86, legs=(18, -16), sh=-12, el=18, lean=3, pencil_deg=200), 5731)
    P.bal(c, ["Much", "obliged!"], 86, (640, 215), (330, 440), 5732)


# ------------------------------------------------------------------ the long beat: five states of one pose
# minute, elbow, wrist, pencil angle, head tilt: the pencil climbs to the chin, the head sinks a little
POSE = [(11, 12, 0, 200, 0), (12, 60, 14, 190, 2), (13, 100, 28, 182, 4), (14, 140, 40, 175, 6), (15, 140, 40, 175, 9)]
THINK = [["the key...", "the SERVICE door...", "at 4:15..."], ["the key...", "the SERVICE..."], ["the... the...?"], None, []]


def long_state(c, k, speak=True):
    mm, el, wr, pd, tilt = POSE[k]
    P.clock_hands(c, 4, mm, 5740 + k)
    P.door_open(c, 2962)
    a = agent(1262, AY, face=1, scale=0.86, legs=(4, -4), sh=5, el=el, wr=wr, pencil_deg=pd, tilt=tilt)
    P.figs(c, a, 2973)
    fp = p7.face_points(a)
    head = (fp["nose"][0] - 60, fp["nose"][1] - 50)
    if k == 3:
        if speak:
            P.bal(c, ["Well, here I am...", "and what for?"], 50, (960, 520), (fp["nose"][0] + 2, fp["lip_lo"][1] + 8), 5750,
                  ctrl=(1190, 500))
    elif THINK[k] is not None:
        if THINK[k]:
            thought(c, THINK[k], 46, (960, 510), head, 5760 + 20 * k)
        else:
            thought(c, [], 46, (1020, 470), head, 5760 + 20 * k)    # an empty thought: nothing left in it
    return a


def render(fn, k=None, speak=True):
    c = P.background()
    if k is None:
        fn(c)
    else:
        long_state(c, k, speak)
    return c


def build(n_strips=5, speak=True):
    page = SHEET.copy()
    for (x0, y0, x1, y1), fn, (cx0, cy0, cx1, cy1) in zip(TOP, (t1, t2, t3), CROPS):
        c = render(fn)[cy0:cy1, cx0:cx1]
        p = cv2.resize(c, (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA)
        page[y0:y1, x0:x1] = page[y0:y1, x0:x1] * (p / 255.0)
    for k in range(n_strips):
        x0, y0, x1, y1 = STRIPS[k]
        c = render(None, k, speak)
        bx0, by0, bx1, by1 = BAND
        p = c[by0:by1, bx0:bx1]
        page[y0:y1, x0:x1] = page[y0:y1, x0:x1] * (p / 255.0)
        # a small pen time-stamp in each strip's corner, so the held minutes read
        slip(page, x0 + 14, y0 + 14, [f"{k + 1} of 5"], 30, 5780 + k, paper=np.array([246, 242, 230], np.float32),
             pad=(12, 6), shadow=0.3)
    if n_strips == 5:
        slip(page, 1580, STRIPS[4][1] + 18, ["4:15. The key stays", "on its hook. The", "SERVICE door stays shut."], 32,
             5790, paper=np.array([246, 242, 230], np.float32), shadow=0.35)
    frame_border(page, TOP + STRIPS[:n_strips], w=10, seed=5791)
    return page


def finish(p):
    p = np.clip(np.round(p), 0, 255).astype(np.uint8)
    pen99.folio(p, N, TITLE)
    return p


if __name__ == "__main__":
    page = build()
    img, size = save_page(page, N, PID, TITLE)
    print("jpeg bytes", size)
    if "--page-only" not in sys.argv:
        frames = [build(0)] + [build(k) for k in (1, 2, 3)] + [build(4, speak=False), build(4), build(5)]
        save_beats(N, [np.asarray(Image.fromarray(finish(f)).resize((960, 1242), Image.LANCZOS)) for f in frames])
        print("beats", len(frames))

"""99 ways, page 39 "Meanwhile" (time and order; medium: busch-fold).
A printed picture sheet in two tiers, folded once along the line between them and opened again on the table (the
les-caids tabletop: vintage paper CC BY 2.0, wood CC0). Six columns: the office tier above, the platform tier below;
each column is one moment, its clock time printed across the fold so the upper and lower pictures pair off.
Above: the agent = the les-caids porter cutout (Busch 1865, Max und Moritz plate 31, PD), cut round his figure.
Below: the stranger = Helene (Busch 1872, Die fromme Helene, Werke v2 p 246, PD; the 99-ways forage), cut round her
figure, with a HANDMADE ink cloche hat drawn onto the piece (the canon gives the stranger a hat). The set (desk, memo,
window, clock at 4:10, cupboard, key, SERVICE door, platform, rails, train) is HANDMADE ink line in code; captions,
balloons, times in the shared pen hand. Declared: adds her platform actions (arrival, waiting, the train).
Run: python3 -I p39_meanwhile.py"""
import json
import math
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/kit")
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import pen99  # noqa: E402
from pen99 import penlib  # noqa: E402
import p11_station_cat as k11  # noqa: E402  (busch-fold kit: wood, paper, ink helpers, paste, affine)
from p11_station_cat import line, hatch, text, ellipse_pts, paste, affine  # noqa: E402

ROOT = pen99.ROOT
W, H = pen99.PAGE_W, pen99.PAGE_H
CANON = json.load(open(ROOT / "films/swarm/99-ways/canon.json"))
C = [c for c in CANON["constraints"] if c["id"] == "meanwhile"][0]
LN = {k: v["text"] for k, v in CANON["incident"]["lines"].items()}
LCG = ROOT / "films/sources/les-caids-de-la-gaudriole"
HEL_SRC = ROOT / "films/sources/99-ways/forage/busch_werke_v2_p246.jpg"
INK = np.array([20, 19, 18], np.float32)
OUT_JPG = ROOT / "assets/pages/99-ways/39-meanwhile.jpg"
OUT_PNG = ROOT / "films/sources/99-ways/masters/39-meanwhile.png"
BEATS = ROOT / "films/sources/99-ways/beats/39"

PW, PH = 313, 1150
GAP = 20
COLS = [110 + i * (PW + GAP) for i in range(6)]
TOP_Y, BOT_Y = 230, 1480
CREASE_Y = 1405
TIMES = ["4:09:30", "4:09:50", "4:10:00", "4:10:10", "4:10:40", "4:11:00"]

CAP_UP = [["He reads", "the memo", "and gets up."],
          ["On his way,", "a voice at", "the window."],
          ["He looks", "at the clock."],
          ["She thanks", "him. He", "walks on."],
          ["He opens", "the cupboard."],
          ["And stands", "there. The", "door stays shut."]]
CAP_LO = [["Meanwhile,", "she comes up", "the platform."],
          ["Meanwhile,", "she leans in", "and asks."],
          ["Meanwhile,", "she sets her", "watch by it."],
          ["Meanwhile,", "she thanks", "him and turns."],
          ["Meanwhile,", "her train", "pulls in."],
          ["Meanwhile,", "she is aboard;", "the train goes."]]

# ------------------------------------------------------------------ cut pieces
# the porter (les-caids part, 430x580): hand-cut polygon round his figure (the door slab, wall and stick left behind)
PORTER_POLY = [(205, 30), (240, 22), (275, 30), (295, 60), (300, 95), (330, 100), (345, 120), (330, 135), (300, 150),
               (295, 175), (275, 182), (252, 188), (258, 215), (278, 248), (302, 256), (302, 282), (262, 300),
               (230, 312), (238, 340), (262, 390), (296, 440), (316, 480), (336, 488), (402, 486), (412, 505),
               (382, 526), (352, 556), (324, 546), (308, 520), (298, 505), (240, 478), (200, 440), (165, 400),
               (130, 340), (100, 285), (98, 250), (110, 205), (150, 148), (203, 112), (198, 60)]
PORTER_HAND = (300, 268)
PORTER_CHIN = (288, 178)
PORTER_MOUTH = (300, 160)
PORTER_FEET = (330, 545)
# Helene (p246 rendition, 1400x2184): hand-cut polygon round her (ribbons, arm to the door); door and shadow left behind
HX, HY = 180, 1080
HEL_POLY = [(150, 128), (232, 118), (288, 92), (300, 38), (352, 22), (408, 50), (412, 104), (398, 150), (396, 166),
            (440, 180), (490, 172), (520, 166), (530, 192), (512, 240), (470, 252), (420, 262), (382, 292), (352, 334),
            (338, 400), (332, 480), (322, 560), (312, 612), (232, 642), (132, 672), (90, 690), (58, 650), (58, 560),
            (78, 420), (68, 322), (98, 270), (148, 228), (196, 192), (160, 186), (148, 168)]
HEL_HAT = [(292, 100), (300, 60), (322, 34), (356, 26), (392, 40), (410, 70), (414, 100), (432, 106), (420, 116),
           (350, 112), (290, 118), (276, 110)]
HEL_HAND = (522, 180)
HEL_HEAD = (352, 90)
HEL_FEET = (110, 680)


def porter_piece():
    im = np.asarray(Image.open(LCG / "panel-artist/parts/porter.body.png").convert("LA"))
    g = im[..., 0].astype(np.float32)
    a = np.zeros(g.shape, np.uint8)
    cv2.fillPoly(a, [np.int32(PORTER_POLY)], 255, cv2.LINE_AA)
    a = np.minimum(a, np.where(im[..., 1] > 20, 255, 0).astype(np.uint8) | 0) if False else a
    g = np.where(im[..., 1] > 20, g, 255.0)          # outside the part's own alpha: the plate's white
    return g, a


def helene_piece():
    """Helene cut round her outline, with the HANDMADE cloche drawn onto the piece (white crown, ink brim, band, hatching)"""
    src = np.asarray(Image.open(HEL_SRC).convert("L")).astype(np.float32)
    g = src[HY:HY + 720, HX:HX + 600].copy()
    hat = np.zeros(g.shape, np.uint8)
    cv2.fillPoly(hat, [np.int32(HEL_HAT)], 255, cv2.LINE_AA)
    brim = np.zeros(g.shape, np.uint8)
    cv2.ellipse(brim, (352, 106), (84, 13), -3, 0, 360, 255, -1, cv2.LINE_AA)
    hat = np.maximum(hat, brim)
    g = np.where(hat > 127, 26.0, g)                                              # a black hat, wide brim
    m = np.zeros(g.shape, np.uint8)
    line(m, [(300, 86), (352, 78), (408, 84)], 6, 3903, tremor=0.3)               # pale band
    line(m, [(380, 70), (402, 52), (420, 40)], 3, 3904, tremor=0.3)               # a feather's quill
    g = g * (1 - m / 255.0) + 236 * (m / 255.0)
    for k in range(6):                                                             # sheen hatching on the crown
        line(m, [(322 + k * 8, 40 + k), (318 + k * 8, 66)], 1.4, 3910 + k, tremor=0.2)
    a = np.zeros(g.shape, np.uint8)
    cv2.fillPoly(a, [np.int32(HEL_POLY)], 255, cv2.LINE_AA)
    a = np.maximum(a, cv2.dilate(hat, np.ones((7, 7), np.uint8)))
    return g, a


PORTER = None
HELENE = None


def lay(c, piece, M, clip=None):
    g, a = piece
    return paste(c, g, a, M, clip=clip, margin=6)


def pt(M, p):
    return (M[0, 0] * p[0] + M[0, 1] * p[1] + M[0, 2], M[1, 0] * p[0] + M[1, 1] * p[1] + M[1, 2])


def balloon(c, lines, cap, centre, tip, seed):
    """a cut-paper balloon fitted inside the narrow picture: the cap shrinks and the centre shifts until the
    ellipse clears both picture edges (no letter is cut by a frame line)"""
    lines = [pen99.clean(l) for l in lines]
    while True:
        tw = penlib.letter_lines(lines, cap, seed + 1).shape[1]
        rx = tw * 0.5 * 1.18 + cap * 0.35
        if 2 * rx <= PW - 30 or cap <= 22:
            break
        cap -= 1
    cx = min(max(centre[0], rx + 14), PW - rx - 14)
    centre = (cx, centre[1])
    b = penlib.balloon_piece(lines, cap, (tip[0] - centre[0], tip[1] - centre[1]), seed, tail_w=0.26, bend=0.08)
    penlib.lay_balloon(c, b, centre)


def caption(c, ground, lines, seed, cap=32):
    m = np.zeros(c.shape[:2], np.uint8)
    for k, ln in enumerate(lines):
        text(m, [ln], 22, 54 + k * 44, cap, seed + k)
    box = np.zeros(c.shape[:2], np.uint8)
    cv2.rectangle(box, (8, 8), (PW - 8, 26 + 44 * len(lines)), 255, -1)
    pa = box.astype(np.float32)[..., None] / 255 * 0.9
    c[:] = c * (1 - pa) + ground * pa
    penlib.ink_onto(c, m, INK)


# ------------------------------------------------------------------ the office set (HANDMADE ink)
FLOOR = 1010


def office(m, seed):
    line(m, [(0, FLOOR), (PW, FLOOR)], 6, seed)
    line(m, [(0, 760), (PW, 760)], 3, seed + 1)
    hatch(m, 0, FLOOR + 6, PW, PH, 40, 2, seed + 2, ang=-20)


def desk(m, seed):
    x0, x1, y = 170, PW + 10, 800
    line(m, [(x0, y), (x1, y)], 7, seed)
    line(m, [(x0 + 6, y + 18), (x1, y + 18)], 3, seed + 1)
    line(m, [(x0 + 14, y + 18), (x0 + 14, FLOOR)], 6, seed + 2)
    hatch(m, x0 + 20, y + 24, x1, FLOOR - 4, 16, 2, seed + 3, ang=-80)


def window(m, seed, x0=0, x1=150, y0=330, y1=740, label=True):
    line(m, [(x0 - 10, y0), (x1, y0), (x1, y1), (x0 - 10, y1)], 7, seed)
    line(m, [(x0 - 10, y0 + 20), (x1 - 20, y0 + 20), (x1 - 20, y1 - 20)], 3, seed + 1)
    line(m, [(x0 - 10, (y0 + y1) / 2), (x1 - 20, (y0 + y1) / 2)], 3, seed + 2)
    line(m, [(x0 - 10, y1 + 14), (x1 + 16, y1 + 14)], 6, seed + 3)


def clock(m, cx, cy, r, seed):
    line(m, ellipse_pts(cx, cy, r + 10, r + 10), 6, seed)
    line(m, ellipse_pts(cx, cy, r, r), 2.5, seed + 1)
    for k in range(12):
        a = math.radians(k * 30 - 90)
        line(m, [(cx + (r - 11) * math.cos(a), cy + (r - 11) * math.sin(a)), (cx + (r - 3) * math.cos(a), cy + (r - 3) * math.sin(a))],
             4 if k % 3 == 0 else 2.5, seed + 2 + k, tremor=0.15)
    for ang, L, w in [((4 + 10 / 60) * 30, r * 0.5, 6), (10 * 6, r * 0.8, 4)]:      # 4:10
        a = math.radians(ang - 90)
        line(m, [(cx, cy), (cx + L * math.cos(a), cy + L * math.sin(a))], w, seed + 20 + w, tremor=0.15)
    cv2.circle(m, (int(cx), int(cy)), 5, 255, -1, cv2.LINE_AA)
    line(m, [(cx, cy + r + 10), (cx, cy + r + 90)], 4, seed + 30)
    cv2.circle(m, (int(cx), int(cy + r + 98)), 14, 255, -1, cv2.LINE_AA)


def cupboard(m, seed, x0=120, x1=236, y0=470, y1=FLOOR, open_=True):
    line(m, [(x0, y0), (x1, y0), (x1, y1)], 6, seed)
    line(m, [(x0, y0), (x0, y1)], 6, seed + 1)
    if open_:
        hatch(m, x0 + 4, y0 + 4, x1 - 4, y1 - 4, 9, 2, seed + 2, ang=-70)
        for yy in (600, 760):
            line(m, [(x0 + 4, yy), (x1 - 4, yy)], 4, seed + 3 + yy)
        line(m, [(x0, y0), (x0 - 62, y0 + 34), (x0 - 62, y1 - 20), (x0, y1)], 6, seed + 4)   # leaf on the left jamb
    else:
        line(m, [(x0 + 14, y0 + 14), (x1 - 14, y0 + 14), (x1 - 14, y1 - 14), (x0 + 14, y1 - 14), (x0 + 14, y0 + 14)], 3, seed + 5)


def key_on_hook(c, hook, seed):
    """the brass key on its hook with the SERVICE tag, on a white paper ground over the cupboard's dark inside:
    the key drawn large (bow, shaft, two-tooth bit) with a thin brass wash, its tag hung beside it on a string"""
    hx, hy = hook
    bg = np.zeros(c.shape[:2], np.uint8)
    cv2.rectangle(bg, (int(hx - 26), int(hy - 30)), (int(min(PW - 6, hx + 96)), int(hy + 170)), 255, -1)
    pa = bg.astype(np.float32)[..., None] / 255
    c[:] = c * (1 - pa) + np.array([240, 238, 232], np.float32) * pa
    # brass wash under the ink (hand-colouring on the printed sheet)
    wash = np.zeros(c.shape[:2], np.uint8)
    cv2.circle(wash, (int(hx), int(hy + 30)), 19, 255, -1, cv2.LINE_AA)
    cv2.rectangle(wash, (int(hx - 5), int(hy + 46)), (int(hx + 5), int(hy + 150)), 255, -1)
    cv2.rectangle(wash, (int(hx + 2), int(hy + 122)), (int(hx + 24), int(hy + 150)), 255, -1)
    wa = (cv2.GaussianBlur(wash, (0, 0), 1.2).astype(np.float32) / 255 * 0.8)[..., None]
    c[:] = c * (1 - wa) + np.array([214, 168, 62], np.float32) * wa
    m = np.zeros(c.shape[:2], np.uint8)
    line(m, [(hx - 8, hy - 18), (hx, hy - 6), (hx, hy + 8), (hx + 6, hy + 12)], 5, seed)        # the hook
    line(m, ellipse_pts(hx, hy + 30, 19, 19), 5, seed + 1)                                       # bow
    line(m, ellipse_pts(hx, hy + 30, 7, 7), 3, seed + 7)
    line(m, [(hx - 5, hy + 48), (hx - 5, hy + 150)], 4, seed + 2)                                # shaft
    line(m, [(hx + 5, hy + 48), (hx + 5, hy + 150)], 4, seed + 8)
    line(m, [(hx + 5, hy + 122), (hx + 24, hy + 122), (hx + 24, hy + 132), (hx + 14, hy + 132),
             (hx + 14, hy + 140), (hx + 24, hy + 140), (hx + 24, hy + 150), (hx - 5, hy + 150)], 4, seed + 3)  # bit
    tx, ty = hx + 30, hy + 52
    line(m, [(hx + 14, hy + 38), (tx + 4, ty + 2)], 2, seed + 4)                                 # the tag's string
    line(m, [(tx, ty), (tx + 62, ty + 3), (tx + 60, ty + 30), (tx - 2, ty + 27), (tx, ty)], 3, seed + 5)
    text(m, ["SERVICE"], tx + 30, ty + 23, 13, seed + 6, align="centre", weight=0.16)
    penlib.ink_onto(c, m, INK)


# ------------------------------------------------------------------ the platform set (HANDMADE ink)
PLAT = 1000


def platform(m, seed, wall=True, window_x=None):
    line(m, [(0, PLAT), (PW, PLAT)], 6, seed)
    for k, y in enumerate((1040, 1090, 1150)):
        line(m, [(0, y), (PW, y)], 2, seed + 1 + k)
    for x in range(20, PW, 70):
        line(m, [(x, PLAT + 4), (x - 30, PH)], 2, seed + 10 + x)
    if wall:   # the station's outside wall: clapboard
        xr = (window_x - 18) if window_x is not None else PW
        for y in range(330, PLAT - 10, 74):
            x_end = xr if 170 <= y <= 790 else PW
            line(m, [(0, y), (x_end, y + 2)], 1.8, seed + 100 + y, tremor=0.5)
    if window_x is not None:   # the ticket window seen from the platform, cut by the right edge
        x0 = window_x
        line(m, [(x0, 310), (PW + 10, 310)], 7, seed + 200)
        line(m, [(x0, 310), (x0, 760)], 7, seed + 201)
        line(m, [(x0, 760), (PW + 10, 760)], 7, seed + 202)
        line(m, [(x0 - 14, 776), (PW + 10, 776)], 5, seed + 203)
        line(m, [(x0 + 18, 330), (x0 + 18, 742), (PW + 10, 742)], 3, seed + 204)
        line(m, [(x0 + 18, 560), (PW + 10, 560)], 3, seed + 205)


def ticket_sign(c, x0, seed):
    """TICKET / OFFICE board over the window"""
    m = np.zeros(c.shape[:2], np.uint8)
    bg = np.zeros(c.shape[:2], np.uint8)
    cv2.rectangle(bg, (x0 - 4, 182), (PW + 10, 284), 255, -1)
    pa = bg.astype(np.float32)[..., None] / 255
    c[:] = c * (1 - pa) + np.array([246, 244, 238], np.float32) * pa
    line(m, [(x0 - 4, 182), (PW + 10, 182)], 5, seed)
    line(m, [(x0 - 4, 182), (x0 - 4, 284), (PW + 10, 284)], 5, seed + 1)
    text(m, ["TICKET", "OFFICE"], (x0 + PW) / 2 - 2, 228, 23, seed + 2, align="centre", weight=0.17)
    penlib.ink_onto(c, m, INK)


def coach(m, seed, dx=0):
    x0, x1, y0, y1 = -20 + dx, PW + 20 + dx, 400, 880
    line(m, [(x0, y0), (x1, y0)], 6, seed)
    line(m, ellipse_pts((x0 + x1) / 2, y0, (x1 - x0) / 2, 50, 180, 360), 5, seed + 1)
    line(m, [(x0, y1), (x1, y1)], 6, seed + 2)
    for k, wx in enumerate(range(x0 + 40, x1 - 40, 120)):
        line(m, [(wx, 470), (wx + 80, 470), (wx + 80, 600), (wx, 600), (wx, 470)], 4, seed + 10 + k)
    line(m, [(x0, 640), (x1, 640)], 2.5, seed + 3)
    hatch(m, max(0, x0 + 2), 645, min(PW, x1 - 2), y1 - 4, 34, 1.8, seed + 4, ang=-85)
    for k, wx in enumerate((x0 + 60, x1 - 60)):
        line(m, ellipse_pts(wx, y1 + 40, 38, 38), 5, seed + 30 + k)
    line(m, [(x0, y1 + 30), (x1, y1 + 30)], 3, seed + 5)


def steam(m, seed, x, y, n=4):
    for k in range(n):
        r = 26 + k * 12
        line(m, ellipse_pts(x + k * 30, y - k * 52, r, r * 0.7, 200, 520), 3, seed + k, tremor=0.6)


# ------------------------------------------------------------------ panels
def upper(i, ground):
    c = ground.copy()
    seed = 3900 + i * 53
    m = np.zeros((PH, PW), np.uint8)
    office(m, seed)
    clip = None
    if i == 0:
        desk(m, seed + 10)
    if i in (1, 3):
        window(m, seed + 20)
    if i == 2:
        clock(m, 262, 420, 44, seed + 30)
    if i in (4, 5):
        cupboard(m, seed + 40, x0=196, x1=300, open_=True)
    if i == 5:
        pass
    penlib.ink_onto(c, m, INK)
    if i in (4, 5):
        key_on_hook(c, (204, 500), seed + 45)
    if i == 0:   # memo slip lying on the desk edge
        slip = np.zeros((PH, PW), np.uint8)
        poly = [(178, 798), (196, 728), (322, 734), (322, 802)]
        cv2.fillPoly(slip, [np.int32(poly)], 255, cv2.LINE_AA)
        penlib.shadow_onto(c, slip, off=4, blur=3, opacity=0.3)
        sa = slip.astype(np.float32)[..., None] / 255
        c[:] = c * (1 - sa) + np.array([247, 246, 241], np.float32) * sa
        mm = np.zeros((PH, PW), np.uint8)
        line(mm, poly + [poly[0]], 2.5, seed + 60)
        text(mm, ["4:15 open", "SERVICE door.", "Key in cupb'd."], 262, 754, 16, seed + 61, align="centre", weight=0.17)
        penlib.ink_onto(c, mm, INK)
    if i == 1:   # her hat through the glass
        g, a = HELENE
        glass = np.zeros((PH, PW), np.float32)
        glass[352:718, 0:128] = 1
        M = affine(HEL_HEAD, (54, 520), 0.78, flip=True)
        paste(c, g, a, M, clip=glass)
        gm = (glass * 255).astype(np.uint8)
        penlib.ink_onto(c, gm, np.array([205, 203, 198], np.float32), alpha=0.2)
    # the agent
    if i == 0:
        M = affine(PORTER_FEET, (150, FLOOR + 40), 0.95, deg=6)
    elif i == 1:
        M = affine(PORTER_FEET, (150, FLOOR + 40), 0.95, flip=True)         # turned to the window
    elif i == 2:
        M = affine(PORTER_FEET, (245, FLOOR + 40), 0.95, deg=-12)           # head up to the clock
    elif i == 3:
        M = affine(PORTER_FEET, (230, FLOOR + 40), 0.95)
    else:
        M = affine(PORTER_FEET, (125, FLOOR + 40), 0.95)
    lay(c, PORTER, M)
    if i == 5:   # the pencil to his chin (handmade)
        pm = np.zeros((PH, PW), np.uint8)
        line(pm, [pt(M, (PORTER_HAND[0] + 2, PORTER_HAND[1] - 4)), pt(M, (PORTER_CHIN[0] + 4, PORTER_CHIN[1] + 4))], 9, seed + 90, tremor=0.2)
        penlib.ink_onto(c, pm, INK)
    if i == 5:   # the SERVICE door, shut, at the right edge: its card
        m2 = np.zeros((PH, PW), np.uint8)
        line(m2, [(304, 380), (304, FLOOR)], 6, seed + 70)
        penlib.ink_onto(c, m2, INK)
        bg = np.zeros((PH, PW), np.uint8)
        cv2.rectangle(bg, (198, 400), (PW - 4, 446), 255, -1)
        pa = bg.astype(np.float32)[..., None] / 255
        c[:] = c * (1 - pa) + np.array([248, 246, 240], np.float32) * pa
        m3 = np.zeros((PH, PW), np.uint8)
        line(m3, [(198, 400), (PW - 4, 400), (PW - 4, 446), (198, 446), (198, 400)], 3, seed + 72)
        text(m3, ["SERVICE"], (198 + PW - 4) / 2, 436, 26, seed + 73, align="centre", weight=0.17)
        penlib.ink_onto(c, m3, INK)
    mouth = pt(M, PORTER_MOUTH)
    caption(c, ground, CAP_UP[i], seed + 100)
    if i == 1:
        balloon(c, ["Pardon", "me — have you", "the right", "time?"], 33, (182, 300), (70, 470), seed + 120)
    if i == 2:
        balloon(c, ["Ten past", "four, by the", "clock."], 31, (100, 330), mouth, seed + 120)
    if i == 3:
        balloon(c, ["Much", "obliged!"], 34, (190, 300), (60, 460), seed + 120)
    if i == 5:
        balloon(c, ["Well, here", "I am... and", "what for?"], 33, (150, 270), mouth, seed + 120)
    return c


def lower(i, ground):
    c = ground.copy()
    seed = 3960 + i * 53
    m = np.zeros((PH, PW), np.uint8)
    win = 170 if i in (1, 2, 3) else (196 if i == 0 else None)
    if i in (4, 5):
        platform(m, seed, wall=False)
        coach(m, seed + 40, dx=0 if i == 4 else -150)
        steam(m, seed + 60, 60 if i == 4 else 200, 330, 4)
        if i == 5:
            for k in range(4):
                line(m, [(PW - 10 - k * 6, 480 + k * 90), (PW - 120 - k * 6, 480 + k * 90)], 3, seed + 80 + k)
    else:
        platform(m, seed, wall=True, window_x=win)
    penlib.ink_onto(c, m, INK)
    if win is not None:
        ticket_sign(c, win, seed + 30)
    g, a = HELENE
    if i == 0:
        M = affine(HEL_FEET, (70, PLAT + 60), 0.58, deg=-6)
    elif i in (1, 2):
        M = affine(HEL_HAND, (196, 560), 0.70)                    # leaning in at the window
    elif i == 3:
        M = affine(HEL_FEET, (300, PLAT + 60), 0.62, flip=True)   # turned away to the train
    elif i == 4:
        M = affine(HEL_FEET, (60, PLAT + 70), 0.58, deg=-4)
    else:
        M = None
    if M is not None:
        lay(c, HELENE, M)
    else:   # aboard: her hatted head in a coach window
        clipw = np.zeros((PH, PW), np.float32)
        clipw[474:598, 14:86] = 1
        M = affine(HEL_HEAD, (50, 545), 0.62)
        paste(c, g, a, M, clip=clipw)
    if i == 2:   # her wristwatch set by his answer: a small handmade watch on her raised wrist
        wx, wy = pt(M, (452, 200))
        mm = np.zeros((PH, PW), np.uint8)
        cv2.circle(mm, (int(wx), int(wy)), 13, 255, 4, cv2.LINE_AA)
        line(mm, [(wx, wy), (wx + 6, wy + 3)], 2.5, seed + 70, tremor=0.1)
        line(mm, [(wx, wy), (wx + 7, wy - 6)], 2, seed + 71, tremor=0.1)
        penlib.ink_onto(c, mm, INK)
    head = pt(M, HEL_HEAD)
    caption(c, ground, CAP_LO[i], seed + 100)
    if i == 1:
        balloon(c, ["Pardon", "me — have you", "the right", "time?"], 28, (92, 380), (head[0] + 6, head[1] - 34), seed + 120)
    if i == 2:   # his answer, coming out through the glass
        balloon(c, ["Ten past", "four, by the", "clock."], 28, (92, 380), (250, 420), seed + 120)
    if i == 3:
        balloon(c, ["Much", "obliged!"], 30, (100, 430), (head[0] - 4, head[1] - 30), seed + 120)
    return c


def build(n_cols=6, lower_upto=None):
    global PORTER, HELENE
    if PORTER is None:
        PORTER, HELENE = porter_piece(), helene_piece()
    lower_upto = n_cols if lower_upto is None else lower_upto
    page = cv2.GaussianBlur(k11.wood(), (0, 0), 1.6)
    sheet = k11.paper()
    sheet = 238 + cv2.GaussianBlur(sheet - 238, (0, 0), 2.6) * 0.85     # the sheet's relief kept, its finest grain eased (file size)
    boxes = []
    for i in range(n_cols):
        x0 = COLS[i]
        sheet[TOP_Y:TOP_Y + PH, x0:x0 + PW] = upper(i, sheet[TOP_Y:TOP_Y + PH, x0:x0 + PW])
        boxes.append((x0, TOP_Y, x0 + PW, TOP_Y + PH))
        if i < lower_upto:
            sheet[BOT_Y:BOT_Y + PH, x0:x0 + PW] = lower(i, sheet[BOT_Y:BOT_Y + PH, x0:x0 + PW])
            boxes.append((x0, BOT_Y, x0 + PW, BOT_Y + PH))
    m = np.zeros((H, W), np.uint8)
    # head of the sheet and the tier labels
    text(m, ["Above, the office. Below, the platform. Each column, one moment."], W / 2, 175, 40, 3990, align="centre")
    for i in range(n_cols):
        x0 = COLS[i]
        text(m, [TIMES[i]], x0 + PW / 2, CREASE_Y + 14, 34, 3991 + i, align="centre", weight=0.15)
        # a short tick from each panel down/up to its time on the fold: the pairing
        line(m, [(x0 + PW / 2, TOP_Y + PH + 6), (x0 + PW / 2, CREASE_Y - 34)], 3, 3995 + i)
        if i < lower_upto:
            line(m, [(x0 + PW / 2, CREASE_Y + 26), (x0 + PW / 2, BOT_Y - 6)], 3, 3998 + i)
    penlib.ink_onto(sheet, m, INK)
    penlib.ink_onto(sheet, penlib.border_mask((H, W), boxes, 6, 3920), INK)
    pen99.folio(sheet, 39, C["title"])
    # the fold, along the line between the tiers
    y = np.arange(H, dtype=np.float32)[:, None]
    d = y - CREASE_Y
    shade = 1 - 0.16 * np.exp(-(d / 7) ** 2) - 0.035 * np.exp(-((d - 30) / 40) ** 2) + 0.025 * np.exp(-((d + 26) / 30) ** 2)
    shade = shade * np.where(d > 0, 0.965, 1.0)
    sheet *= shade[..., None]
    Ms = cv2.getRotationMatrix2D((W / 2, H / 2), -0.3, 1.0)
    sh = cv2.warpAffine(sheet, Ms, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
    mk = np.zeros((H, W), np.uint8)
    cv2.rectangle(mk, (58, 46), (W - 58, H + 100), 255, -1)
    mk = cv2.warpAffine(mk, Ms, (W, H), flags=cv2.INTER_LINEAR)
    penlib.shadow_onto(page, mk, off=10, blur=12, opacity=0.5)
    a = mk.astype(np.float32)[..., None] / 255
    page = page * (1 - a) + sh * a
    page = cv2.GaussianBlur(page, (0, 0), 0.55)      # half-pixel ease of the pen tremor: keeps the JPEG inside 1.2 MB
    return np.clip(np.round(page), 0, 255).astype(np.uint8)


def main():
    from b1m2 import credit_pages
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
    seq = [((6, 0), "b01: the office tier alone, six moments of the agent; the platform tier still blank paper"),
           ((6, 1), "b02: + platform 4:09:30: meanwhile she comes up the platform"),
           ((6, 2), "b03: + platform 4:09:50: meanwhile she leans in and asks (the same line in both tiers)"),
           ((6, 3), "b04: + platform 4:10:00: meanwhile she sets her watch by his answer"),
           ((6, 4), "b05: + platform 4:10:10: meanwhile she thanks him and turns"),
           ((6, 5), "b06: + platform 4:10:40: meanwhile her train pulls in"),
           ((6, 6), "b07: + platform 4:11:00: meanwhile she is aboard and the train goes (= the page)")]
    bd = []
    for j, ((nc, lo), d) in enumerate(seq, 1):
        im = page if lo == 6 else build(nc, lo)
        Image.fromarray(im).resize((960, 1242), Image.LANCZOS).save(BEATS / f"b{j:02d}.png")
        bd.append(d)
    src = ["les-caids-de-la-gaudriole:busch-mm-031", "99-ways:busch-helene-munzel",
           "les-caids-de-la-gaudriole:vintage-paper", "les-caids-de-la-gaudriole:wood-table", "99-ways:handmade"]
    credit_pages(src, 39)
    rec = {
        "n": 39, "id": C["id"], "title": C["title"], "rule": C["rule"], "medium": C["medium"], "family": C["family"],
        "canon_revision": CANON["revision"], "declares": C["declares"],
        "file": str(OUT_JPG.relative_to(ROOT)), "master": str(OUT_PNG.relative_to(ROOT)), "beats_dir": str(BEATS.relative_to(ROOT)),
        "build": "films/swarm/99-ways/build/p39_meanwhile.py (busch-fold kit from p11_station_cat.py)",
        "sources": src,
        "made": [
            "a printed picture sheet on the les-caids tabletop (vintage paper scan graded neutral, its relief kept; greyed wood), folded once along the line between the two tiers and opened again (valley crease shading, the halves lit differently), laid a hair off square with its shadow",
            "two tiers of six tall pictures: the office above, the platform below; each column's clock time (4:09:30 ... 4:11:00) printed on the fold between its two pictures, with a ruled tick up and down to each: the pairing",
            "the agent = the les-caids porter cutout (Busch 1865, Max und Moritz plate 31), re-cut by hand round his figure (door slab, wall and stick left behind), laid in all six office pictures (turned, tilted to the clock), a handmade ink pencil at his chin in the last",
            "the stranger = Helene (Busch 1872, Die fromme Helene, Werke v2 p 246) cut by hand round her figure; a HANDMADE ink cloche hat (white crown, band, brim, hatching) drawn onto the piece so she wears the canon's hat; her own leaning pose put to the ticket window; seen through the office glass (picture 2), turned away (4), by the coach (5), her hatted head in a coach window (6)",
            "HANDMADE ink set (penlib.brush_line): desk with the memo slip, the ticket window from both sides (TICKET OFFICE board on the platform side), the clock at 4:10 with its pendulum, the cupboard open on its left jamb, the brass key drawn large on its hook (bow, shaft, bit, a thin brass wash as hand-colouring) with its SERVICE tag on a string, the shut SERVICE door with its card, platform boards, clapboard wall, the coach with its windows, wheels and steam; a small handmade wristwatch",
            "captions (office: what he does; platform: each begins 'Meanwhile,') and the four canon lines in the shared pen hand and cut-paper balloons; the question and the answer appear in both tiers at the same column; folio '39 / Meanwhile' (pen99.folio)"],
        "events": {"E0": "column 1 (4:09:30): above, he reads the memo and gets up; below, she comes up the platform",
                   "E1": "column 2 (4:09:50): above, her hat through the glass, the question; below, she leans in and asks",
                   "E2": "column 3 (4:10:00): above, head up to the clock at 4:10, the answer; below, the answer through the glass, she sets her watch",
                   "E3": "column 4 (4:10:10): above, the empty window, 'Much obliged!', he walks on; below, she thanks him and turns",
                   "E4": "column 5 (4:10:40): above, the cupboard open, key on its hook; below, her train pulls in",
                   "E5": "column 6 (4:11:00): above, pencil to chin, the forgetting line, the SERVICE door shut; below, she is aboard and the train goes"},
        "lines": LN,
        "substitutions": "none: the four lines verbatim (broken into short lines to fit the narrow columns); question and answer are repeated in the platform tier",
        "added": "her platform actions: arrival, leaning in, setting her watch, turning, the train pulling in, boarding (declared)",
        "beat": "the office tier lies complete; the platform tier is filled column by column under it, so each of her actions lands beneath his at the same printed time",
        "beat_frames": bd,
        "self_check": {"size_px": [W, H], "jpeg_bytes": size, "jpeg_quality": 90,
                       "in_target_0.4_1.2MB": 400000 <= size <= 1200000,
                       "tiers": 2, "columns": 6, "times_on_fold": TIMES,
                       "every_lower_caption_begins_meanwhile": all(c[0].startswith("Meanwhile") for c in CAP_LO),
                       "clock_at_answer": "4:10 (column 3, printed time 4:10:00)",
                       "pending": "independent blind reading not run by the maker"},
    }
    json.dump(rec, open(ROOT / "films/swarm/99-ways/pages/39.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps(rec["self_check"], indent=1))


if __name__ == "__main__":
    main()

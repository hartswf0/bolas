"""Page 25 Inventory (reduction and expansion; medium: busch-fold).

Every object of the incident laid out as a labelled specimen chart; numbered threads tell the story in order.
A printed specimen plate, folded in four and opened again, on the les-caids tabletop (vintage paper scan
CC BY 2.0 graded neutral, greyed wood CC0, as page 11). Eight specimens in Busch-manner ink line and
hatching (HANDMADE in code), the stranger's hat cut by hand from Busch's Max und Moritz plate mm_016 (PD).
People appear only as their objects and their lines: the four canon lines are pinned slips attributed to
'the owner of Fig. n'. A red cotton thread runs pin to pin with ten numbered tags; the legend retells.
"""
import math
import random
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/kit")
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import pen99  # noqa: E402
from pen99 import penlib  # noqa: E402
import p11_station_cat as B11  # noqa: E402  (tabletop grounds, ink helpers, cutout paste)
import b1m2  # noqa: E402

N, PID, TITLE = 25, "inventory", "Inventory"
W, H = pen99.PAGE_W, pen99.PAGE_H
INK = np.array([22, 20, 19], np.float32)
THREAD = np.array([168, 34, 30], np.float32)
BRASSW = np.array([214, 172, 82], np.float32)
TAGP = np.array([250, 246, 236], np.float32)
SLIPP = np.array([246, 240, 222], np.float32)
line, hatch, text, ellipse_pts = B11.line, B11.hatch, B11.text, B11.ellipse_pts
LCG = B11.LCG
STATE = {"upto": 10}

# ------------------------------------------------------------------ plate geometry
ROW = [(380, 1000), (1000, 1620), (1620, 2240)]
COL3 = [(140, 790), (790, 1430), (1430, 2060)]
COL2 = [(140, 1100), (1100, 2060)]
POS = {1: (0, 0), 2: (0, 1), 3: (0, 2), 4: (1, 0), 5: (1, 1), 6: (1, 2)}
CELLS = {f: (COL3[c][0], ROW[r][0], COL3[c][1], ROW[r][1]) for f, (r, c) in POS.items()}
CELLS[7] = (COL2[0][0], ROW[2][0], COL2[0][1], ROW[2][1])
CELLS[8] = (COL2[1][0], ROW[2][0], COL2[1][1], ROW[2][1])
OBJ = {"clock": 1, "hat": 2, "memo": 3, "window": 4, "pencil": 5, "cupboard": 6, "door": 7, "key": 8}
LABELS = {
    1: ["Fig. 1.  CLOCK, office wall.", "Stands at 4:10."],
    2: ["Fig. 2.  HAT, a lady's.", "Platform side only."],
    3: ["Fig. 3.  MEMO slip, from the desk.", "In pencil."],
    4: ["Fig. 4.  TICKET WINDOW, glazed.", "Between office and platform."],
    5: ["Fig. 5.  PENCIL, the agent's.", "Well chewed at the end."],
    6: ["Fig. 6.  CUPBOARD, office.", "Door hinged on the left jamb."],
    7: ["Fig. 7.  DOOR, marked SERVICE.", "Never opened."],
    8: ["Fig. 8.  KEY, brass, on its hook.", "Paper tag: SERVICE."],
}
STEPS = [  # (thread number, fig, legend text)
    (1, 3, "He reads the memo and rises."),
    (2, 5, "Pencil in hand, he sets off across the office."),
    (3, 4, "The ticket window: on his way, he is stopped."),
    (4, 2, "The hat asks its question."),
    (5, 1, "The clock says 4:10; he gives the answer."),
    (6, 2, "The hat says thanks, and goes."),
    (7, 6, "He reaches the cupboard and opens it."),
    (8, 8, "There hangs the key, tagged SERVICE."),
    (9, 5, "Pencil to his chin: he has forgotten why he came."),
    (10, 7, "The key stays on its hook. The door stays closed."),
]


BOXES = []      # (name, (x0, y0, x1, y1)) every text box on the plate: labels, memo text, slips, title, legend
MEMO = {}


def text_box(m, lines, x, y, cap, seed, name, align="left", weight=0.13):
    t = pen99.letter(lines, cap, seed, weight=weight)
    h, w = t.shape
    left = int(x - cap * 0.6) if align == "left" else int(x - w / 2)
    top = int(y - cap * 1.15)
    text(m, lines, x, y, cap, seed, align=align, weight=weight)
    ys, xs = np.nonzero(t > 40)
    BOXES.append((name, (left + xs.min(), top + ys.min(), left + xs.max(), top + ys.max())))


def cell_mid(f):
    x0, y0, x1, y1 = CELLS[f]
    return (x0 + x1) / 2, (y0 + y1) / 2 - 40


# ------------------------------------------------------------------ specimens in ink (HANDMADE, Busch manner)
def spec_clock(m, seed):
    cx, cy = cell_mid(OBJ['clock'])
    cx -= 172
    cy -= 90
    r = 112
    line(m, ellipse_pts(cx, cy, r + 22, r + 22), 8, seed)
    line(m, ellipse_pts(cx, cy, r, r), 3, seed + 1)
    for k in range(12):
        a = math.radians(k * 30 - 90)
        L = 26 if k % 3 == 0 else 14
        line(m, [(cx + (r - 6) * math.cos(a), cy + (r - 6) * math.sin(a)), (cx + (r - 6 - L) * math.cos(a), cy + (r - 6 - L) * math.sin(a))], 5 if k % 3 == 0 else 3, seed + 10 + k)
    ah, am = math.radians(4 * 30 + 5 - 90), math.radians(10 * 6 - 90)
    line(m, [(cx, cy), (cx + 70 * math.cos(ah), cy + 70 * math.sin(ah))], 9, seed + 30)
    line(m, [(cx, cy), (cx + 112 * math.cos(am), cy + 112 * math.sin(am))], 5, seed + 31)
    # case and pendulum, hatched on the shadow side
    y0, y1 = cy + r + 22, cy + r + 150
    line(m, [(cx - 80, y0), (cx - 80, y1), (cx, y1 + 30), (cx + 80, y1), (cx + 80, y0)], 5, seed + 40)
    line(m, [(cx, y0), (cx + 14, y1 - 50)], 3, seed + 41)
    line(m, ellipse_pts(cx + 15, y1 - 34, 22, 22), 4, seed + 42)
    hatch(m, int(cx + 48), int(y0 + 6), int(cx + 76), int(y1 - 4), 9, 2, seed + 43, ang=-70)
    for k in range(14):  # Busch-like short strokes round the rim
        a = math.radians(40 + k * 8)
        line(m, [(cx + (r + 26) * math.cos(a), cy + (r + 26) * math.sin(a)), (cx + (r + 38) * math.cos(a), cy + (r + 38) * math.sin(a))], 2, seed + 60 + k, tremor=0.3)
    return {"a": (cx + 112 * math.cos(am) * 0.6, cy + 112 * math.sin(am) * 0.6 - 4)}


def spec_memo(m, canvas, seed):
    cx, cy = cell_mid(OBJ['memo'])
    a = math.radians(-4)
    w, h = 520, 262          # inside Fig. 3's cell with a 50 px margin each side (cell 630 wide)
    P = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
    R = lambda p: (cx + p[0] * math.cos(a) - p[1] * math.sin(a), cy + p[0] * math.sin(a) + p[1] * math.cos(a))
    pm = np.zeros((H, W), np.uint8)
    cv2.fillPoly(pm, [np.int32([[R(p)[0] * 4, R(p)[1] * 4] for p in P])], 255, cv2.LINE_AA, shift=2)
    penlib.shadow_onto(canvas, pm, off=5, blur=4, opacity=0.3)
    canvas[:] = canvas * (1 - pm[..., None] / 255) + SLIPP * (pm[..., None] / 255)
    line(m, [R(p) for p in P] + [R(P[0])], 3, seed)
    t = pen99.letter(["MEMO      Randolph Sta.", "4:15 - open SERVICE door.", "Key in cupboard."], 36, seed + 1)
    ys_, xs_ = np.nonzero(t)
    t = t[ys_.min():ys_.max() + 1, xs_.min():xs_.max() + 1]
    sc = min(0.9, (w - 60) / t.shape[1])
    Mt = cv2.getRotationMatrix2D((t.shape[1] / 2, t.shape[0] / 2), 4, sc)
    Mt[:, 2] += np.array([cx, cy + 6]) - np.array([t.shape[1] / 2, t.shape[0] / 2])
    tw = cv2.warpAffine(t, Mt, (W, H))
    np.maximum(m, tw, out=m)
    ys_, xs_ = np.nonzero(tw > 40)
    BOXES.append(("memo text", (xs_.min(), ys_.min(), xs_.max(), ys_.max())))
    MEMO["slip"] = [tuple(np.round(R(p_), 1)) for p_ in P]
    return {"a": R((-w / 2 + 22, -h / 2 + 18))}


HAT_POLY = [(238, 214), (262, 190), (300, 172), (330, 160), (380, 160), (430, 170), (468, 190), (500, 236), (506, 270),
            (490, 300), (440, 296), (380, 292), (330, 300), (285, 310), (262, 300), (250, 268), (232, 250)]


def spec_hat(canvas, seed):
    g = np.asarray(Image.open(LCG / "busch/mm_016.png").convert("L")).astype(np.float32)
    piece, a = B11.cutout_from(g, HAT_POLY)
    cx, cy = cell_mid(OBJ['hat'])
    M = B11.affine((piece.shape[1] / 2, piece.shape[0] / 2), (cx, cy - 40), 1.7, deg=-6)
    B11.paste(canvas, piece, a, M, margin=6)
    return {"a": (cx - 170, cy - 10), "b": (cx + 160, cy + 30)}


def spec_cupboard(m, seed):
    cx, cy = cell_mid(OBJ['cupboard'])
    x0, x1, y0, y1 = cx - 60, cx + 170, cy - 230, cy + 220
    line(m, [(x0 - 10, y0 - 18), (x1 + 10, y0 - 18)], 7, seed)
    line(m, [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], 5, seed + 1)
    for k, yy in enumerate((y0 + 150, y0 + 300)):
        line(m, [(x0 + 6, yy), (x1 - 6, yy)], 4, seed + 2 + k)
    hatch(m, int(x0 + 8), int(y0 + 8), int(x1 - 8), int(y1 - 8), 13, 2, seed + 5, ang=-55)
    # the door leaf open toward us on the left jamb (perspective), panels and knob
    dx = 170
    leaf = [(x0, y0), (x0 - dx, y0 - 34), (x0 - dx, y1 + 34), (x0, y1)]
    line(m, leaf + [leaf[0]], 5, seed + 8)
    line(m, [(x0 - dx * 0.2, y0 + 30), (x0 - dx * 0.8, y0 + 10), (x0 - dx * 0.8, cy - 10), (x0 - dx * 0.2, cy), (x0 - dx * 0.2, y0 + 30)], 3, seed + 9)
    line(m, [(x0 - dx * 0.2, cy + 30), (x0 - dx * 0.8, cy + 24), (x0 - dx * 0.8, y1 + 4), (x0 - dx * 0.2, y1 - 30), (x0 - dx * 0.2, cy + 30)], 3, seed + 10)
    line(m, ellipse_pts(x0 - dx * 0.9, cy + 8, 7, 9), 4, seed + 11)
    # the empty hook where Fig. 8 hangs, on the inside of the door
    line(m, [(x0 - dx * 0.5, y0 + 50), (x0 - dx * 0.5, y0 + 70), (x0 - dx * 0.42, y0 + 78)], 4, seed + 12)
    return {"a": (x1 - 40, cy - 60)}


def spec_pencil(m, canvas, seed):
    cx, cy = cell_mid(OBJ['pencil'])
    a = math.radians(-28)
    d = np.array([math.cos(a), math.sin(a)])
    n = np.array([-d[1], d[0]])
    p0 = np.array([cx, cy]) - d * 250
    p1 = np.array([cx, cy]) + d * 200
    tip = p1 + d * 70
    hw = 20
    body = [p0 + n * hw, p1 + n * hw, tip, p1 - n * hw, p0 - n * hw]
    line(m, [tuple(p) for p in body] + [tuple(body[0])], 4, seed)
    line(m, [tuple(p1 + n * hw), tuple(p1 - n * hw)], 3, seed + 1)
    line(m, [tuple(p0 + n * hw * 0.3), tuple(p1 + n * hw * 0.3)], 2, seed + 2)
    line(m, [tuple(tip - d * 22 + n * 6), tuple(tip), tuple(tip - d * 22 - n * 6)], 5, seed + 3)
    # chewed end: ragged strokes
    for k in range(6):
        q = p0 + n * hw * (-1 + k * 0.4)
        line(m, [tuple(q), tuple(q - d * random.Random(seed + k).uniform(8, 22))], 3, seed + 10 + k)
    # shading on one side
    for k in range(26):
        q = p0 + d * (k * 17 + 10)
        line(m, [tuple(q - n * hw * 0.9), tuple(q - n * hw * 0.35 + d * 8)], 2, seed + 30 + k, tremor=0.2)
    return {"a": tuple(p0 + d * 60), "b": tuple(p1 - d * 40)}


def spec_window(m, seed):
    cx, cy = cell_mid(OBJ['window'])
    x0, x1, y0, y1 = cx - 200, cx + 200, cy - 230, cy + 210
    line(m, [(x0 - 20, y0), (x1 + 20, y0), (x1 + 20, y0 + 70), (x0 - 20, y0 + 70), (x0 - 20, y0)], 5, seed)
    text(m, ["TICKET OFFICE"], cx, y0 + 50, 34, seed + 1, align="centre", weight=0.18)
    line(m, [(x0, y0 + 70), (x0, y1)], 6, seed + 2)
    line(m, [(x1, y0 + 70), (x1, y1)], 6, seed + 3)
    line(m, [(x0 - 40, y1), (x1 + 40, y1), (x1 + 40, y1 + 28), (x0 - 40, y1 + 28), (x0 - 40, y1)], 5, seed + 4)
    line(m, [(cx, y0 + 70), (cx, y1)], 4, seed + 5)
    line(m, [(x0, cy), (x1, cy)], 4, seed + 6)
    for k in range(5):  # light glints on the glass
        xx = x0 + 30 + k * 18
        line(m, [(xx, y0 + 110 + k * 4), (xx + 40, y0 + 160 + k * 4)], 2, seed + 10 + k, tremor=0.2)
    hatch(m, int(x0 - 38), int(y1 + 4), int(x1 + 38), int(y1 + 26), 8, 2, seed + 20, ang=-80)
    return {"a": (x0 + 60, cy + 40)}


def spec_door(m, seed):
    x0c, y0c, x1c, y1c = CELLS[7]
    cx, cy = (x0c + x1c) / 2, (y0c + y1c) / 2 - 40
    x0, x1, y0, y1 = cx - 150, cx + 150, cy - 240, cy + 220
    line(m, [(x0 - 20, y1), (x0 - 20, y0 - 20), (x1 + 20, y0 - 20), (x1 + 20, y1)], 7, seed)
    line(m, [(x0, y1), (x0, y0), (x1, y0), (x1, y1)], 4, seed + 1)
    for (a, b, c, d) in ((0.15, 0.30, 0.85, 0.55), (0.15, 0.62, 0.85, 0.92)):
        px0, py0, px1, py1 = x0 + (x1 - x0) * a, y0 + (y1 - y0) * b, x0 + (x1 - x0) * c, y0 + (y1 - y0) * d
        line(m, [(px0, py0), (px1, py0), (px1, py1), (px0, py1), (px0, py0)], 3, seed + int(a * 100 + b * 100))
        hatch(m, int(px0 + 4), int(py0 + 4), int(px0 + 24), int(py1 - 4), 7, 2, seed + 7, ang=-80)
    line(m, ellipse_pts(x1 - 30, cy + 10, 9, 9), 4, seed + 20)
    line(m, [(x1 - 30, cy + 26), (x1 - 30, cy + 40)], 4, seed + 21)
    line(m, [(cx - 85, y0 + 34), (cx + 85, y0 + 34), (cx + 85, y0 + 90), (cx - 85, y0 + 90), (cx - 85, y0 + 34)], 3, seed + 22)
    text(m, ["SERVICE"], cx, y0 + 76, 34, seed + 23, align="centre", weight=0.18)
    hatch(m, int(x1 + 4), int(y0 - 16), int(x1 + 18), int(y1), 8, 2, seed + 30, ang=-80)
    return {"a": (x1 - 30, cy + 10)}


def spec_key(m, canvas, seed):
    x0c, y0c, x1c, y1c = CELLS[8]
    cx, cy = (x0c + x1c) / 2 - 60, (y0c + y1c) / 2 - 220
    s = 2.4
    # the hook
    line(m, [(cx - 30 * s, cy - 10), (cx + 30 * s, cy - 10)], 6, seed)
    line(m, [(cx, cy - 10), (cx, cy + 16 * s), (cx + 8 * s, cy + 22 * s)], 5, seed + 1)
    # the key: bow, shank, bit (brass wash under ink)
    bow = ellipse_pts(cx, cy + 40 * s, 22 * s, 22 * s)
    shank = [(cx - 6 * s, cy + 60 * s), (cx + 6 * s, cy + 60 * s), (cx + 6 * s, cy + 160 * s), (cx - 6 * s, cy + 160 * s)]
    bit = [(cx + 6 * s, cy + 130 * s), (cx + 36 * s, cy + 130 * s), (cx + 36 * s, cy + 140 * s), (cx + 24 * s, cy + 140 * s),
           (cx + 24 * s, cy + 150 * s), (cx + 36 * s, cy + 150 * s), (cx + 36 * s, cy + 160 * s), (cx + 6 * s, cy + 160 * s)]
    wash = np.zeros((H, W), np.uint8)
    cv2.fillPoly(wash, [np.int32(np.array(bow) * 4), np.int32(np.array(shank) * 4), np.int32(np.array(bit) * 4)], 255, cv2.LINE_AA, shift=2)
    cv2.circle(wash, (int(cx * 4), int((cy + 40 * s) * 4)), int(11 * s * 4), 0, -1, cv2.LINE_AA, shift=2)
    wash = cv2.GaussianBlur(wash, (0, 0), 1.5)
    a = (wash.astype(np.float32) / 255 * 0.75)[..., None]
    canvas[:] = canvas * (1 - a) + canvas * (BRASSW / 255) * a
    line(m, bow + [bow[0]], 5, seed + 2)
    line(m, ellipse_pts(cx, cy + 40 * s, 11 * s, 11 * s), 3, seed + 3)
    line(m, shank + [shank[0]], 4, seed + 4)
    line(m, bit, 4, seed + 5)
    hatch(m, int(cx + 1 * s), int(cy + 64 * s), int(cx + 5 * s), int(cy + 156 * s), 6, 2, seed + 6, ang=-75)
    # tag on a string
    tx, ty = cx + 70 * s, cy + 80 * s
    line(m, [(cx + 14 * s, cy + 52 * s), (tx, ty)], 2, seed + 7)
    tag = [(tx, ty - 22), (tx + 220, ty - 6), (tx + 214, ty + 70), (tx - 6, ty + 54), (tx, ty - 22)]
    pm = np.zeros((H, W), np.uint8)
    cv2.fillPoly(pm, [np.int32(np.array(tag) * 4)], 255, cv2.LINE_AA, shift=2)
    canvas[:] = canvas * (1 - pm[..., None] / 255 * 0.8) + TAGP * (pm[..., None] / 255 * 0.8)
    line(m, tag, 3, seed + 8)
    t = pen99.letter(["SERVICE"], 36, seed + 9, weight=0.17)
    Mt = cv2.getRotationMatrix2D((t.shape[1] / 2, t.shape[0] / 2), -4, 1.0)
    Mt[:, 2] += np.array([tx + 106, ty + 26]) - np.array([t.shape[1] / 2, t.shape[0] / 2])
    np.maximum(m, cv2.warpAffine(t, Mt, (W, H)), out=m)
    return {"a": (cx, cy + 40 * s - 22 * s), "b": (cx, cy + 150 * s)}


# ------------------------------------------------------------------ the lines, pinned slips
SLIP_CAP = 27
SLIPS = [  # (line key, anchor fig, owner fig, x, y, wrap width): each slip kept inside its own cell, clear of the labels
    ("question", 2, 2, 812, 716, 560),
    ("thanks", 2, 2, 1040, 404, 300),
    ("answer", 1, 5, 448, 650, 215),
    ("forgetting", 5, 5, 812, 1030, 470),
]


def pinned_slip(canvas, m, lines, owner, x, y, seed):
    box = b1m2.slip(canvas, x, y, lines + [f"  - the owner of Fig. {owner}"], SLIP_CAP, seed, paper=SLIPP, tilt=random.Random(seed).uniform(-2, 2), ink=INK)
    pin_at(canvas, x + 20, y + 16)
    BOXES.append((f"slip {lines[0][:14]}", box))
    return box


def slip_box(lines, owner, x, y, seed):
    m = b1m2.letter_left(lines + [f"  - the owner of Fig. {owner}"], SLIP_CAP, seed, 0.13)
    h, w = m.shape
    return (x, y, x + w + 44 - SLIP_CAP, y + h + 32 - int(SLIP_CAP * 0.3))


def pin_at(canvas, x, y, r=8, col=(70, 70, 76)):
    pm = np.zeros((H, W), np.uint8)
    cv2.circle(pm, (int(x * 4), int(y * 4)), int(r * 4), 255, -1, cv2.LINE_AA, shift=2)
    penlib.shadow_onto(canvas, pm, off=3, blur=2, opacity=0.45)
    a = pm.astype(np.float32)[..., None] / 255
    canvas[:] = canvas * (1 - a) + np.array(col, np.float32) * a
    hl = np.zeros((H, W), np.uint8)
    cv2.circle(hl, (int((x - r * .35) * 4), int((y - r * .35) * 4)), int(r * 1.3), 255, -1, cv2.LINE_AA, shift=2)
    canvas[:] = canvas * (1 - hl[..., None] / 255 * .7) + 235 * (hl[..., None] / 255 * .7)


# ------------------------------------------------------------------ the red thread
def thread(canvas, pts, seed):
    """a red cotton thread from pin to pin, sagging slightly, with its shadow; returns nothing"""
    m = np.zeros((H, W), np.uint8)
    for i in range(len(pts) - 1):
        a, b = np.array(pts[i]), np.array(pts[i + 1])
        mid = (a + b) / 2 + np.array([0, 0.06 * np.linalg.norm(b - a)])
        cur = [tuple((1 - t) ** 2 * a + 2 * (1 - t) * t * mid + t ** 2 * b) for t in np.linspace(0, 1, 60)]
        penlib.brush_line(m, cur, 5, seed + i, tremor=0.6)
    sh = np.zeros_like(m)
    sh[6:, 5:] = m[:-6, :-5]
    sh = cv2.GaussianBlur(sh, (0, 0), 3)
    canvas *= (1 - sh[..., None] / 255 * 0.25)
    # twist highlights for cotton
    a_ = m.astype(np.float32)[..., None] / 255
    canvas[:] = canvas * (1 - a_) + THREAD * a_


# ------------------------------------------------------------------ routing the thread round the text
CHECK = {}
GRID = 8
ROUTE_MARGIN, SIGHT_MARGIN, TAG_R = 22, 14, 31


def box_mask(margin, names=None):
    mk = np.zeros((H, W), np.uint8)
    for nm, (x0, y0, x1, y1) in BOXES:
        cv2.rectangle(mk, (int(x0 - margin), int(y0 - margin)), (int(x1 + margin), int(y1 + margin)), 255, -1)
    return mk


def astar(block, a, b):
    """8-connected A* on the coarse grid; cost grows near obstacles so the thread keeps its distance."""
    import heapq
    gh, gw = block.shape
    dist = cv2.distanceTransform((block == 0).astype(np.uint8), cv2.DIST_L2, 5)
    pen = 2.5 / (1.0 + dist)
    sa, sb = (int(a[1] // GRID), int(a[0] // GRID)), (int(b[1] // GRID), int(b[0] // GRID))
    blk = block.copy()
    for (r0, c0) in (sa, sb):     # free a small disc round the pins themselves
        blk[max(0, r0 - 3):r0 + 4, max(0, c0 - 3):c0 + 4] = 0
    g = {sa: 0.0}
    prev = {}
    hq = [(0.0, sa)]
    nb = [(-1, 0, 1), (1, 0, 1), (0, -1, 1), (0, 1, 1), (-1, -1, 1.414), (-1, 1, 1.414), (1, -1, 1.414), (1, 1, 1.414)]
    while hq:
        f, u = heapq.heappop(hq)
        if u == sb:
            break
        for dr, dc, c in nb:
            v = (u[0] + dr, u[1] + dc)
            if not (0 <= v[0] < gh and 0 <= v[1] < gw) or blk[v]:
                continue
            ng = g[u] + c * (1 + pen[v])
            if ng < g.get(v, 1e18):
                g[v] = ng
                prev[v] = u
                hq_h = math.hypot(v[0] - sb[0], v[1] - sb[1])
                heapq.heappush(hq, (ng + hq_h, v))
    path = [sb]
    while path[-1] != sa:
        path.append(prev[path[-1]])
    path.reverse()
    return [((c + 0.5) * GRID, (r + 0.5) * GRID) for r, c in path]


def visible(mask, p, q):
    n = int(math.hypot(q[0] - p[0], q[1] - p[1]) / 3) + 2
    for t in np.linspace(0, 1, n):
        x, y = p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t
        if mask[min(H - 1, max(0, int(y))), min(W - 1, max(0, int(x)))]:
            return False
    return True


def plan_route(pins):
    """One polyline per span pin -> pin: A* round every text box, pulled taut (string-pulling against the box
    mask), so the thread bends only round small guide pins."""
    coarse = cv2.resize(box_mask(ROUTE_MARGIN), (W // GRID, H // GRID), interpolation=cv2.INTER_AREA) > 0
    sight = box_mask(SIGHT_MARGIN)
    route = []
    for a, b in zip(pins[:-1], pins[1:]):
        a, b = tuple(map(float, a)), tuple(map(float, b))
        if visible(sight, a, b):
            route.append([a, b])
            continue
        path = [a] + astar(coarse, a, b)[1:-1] + [b]
        out, i = [a], 0
        while i < len(path) - 1:
            j = len(path) - 1
            while j > i + 1 and not visible(sight, path[i], path[j]):
                j -= 1
            out.append(path[j])
            i = j
        route.append(out)
    return route


def thread_poly(canvas, route, seed):
    """the red cotton thread laid along the routed polylines (taut, a little tremor), with its shadow"""
    m = np.zeros((H, W), np.uint8)
    for i, seg in enumerate(route):
        dense = []
        for a, b in zip(seg[:-1], seg[1:]):
            for t in np.linspace(0, 1, max(4, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 12))):
                dense.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
        penlib.brush_line(m, dense, 5, seed + i, tremor=0.5)
    sh = np.zeros_like(m)
    sh[6:, 5:] = m[:-6, :-5]
    sh = cv2.GaussianBlur(sh, (0, 0), 3)
    canvas *= (1 - sh[..., None] / 255 * 0.25)
    a_ = m.astype(np.float32)[..., None] / 255
    canvas[:] = canvas * (1 - a_) + THREAD * a_
    return m


def place_tags(seq, route):
    """each number tag beside its pin, in the first free direction: clear of every text box, of the thread and
    of the other tags"""
    bm = box_mask(8)
    th = np.zeros((H, W), np.uint8)
    for seg in route:
        for a, b in zip(seg[:-1], seg[1:]):
            cv2.line(th, (int(a[0]), int(a[1])), (int(b[0]), int(b[1])), 255, 9)
    tags = {}
    taken = np.zeros((H, W), np.uint8)
    dirs = [(46, -46), (-46, 46), (-46, -46), (46, 46), (0, -62), (62, 0), (0, 62), (-62, 0)]
    for n, p in seq:
        best = None
        for k, (dx, dy) in enumerate(dirs if n % 2 else dirs[1:] + dirs[:1]):
            for r in (1.0, 1.35, 1.7):
                x, y = p[0] + dx * r, p[1] + dy * r
                cm = np.zeros((H, W), np.uint8)
                cv2.circle(cm, (int(x), int(y)), TAG_R + 4, 255, -1)
                hit = int((cm & bm).any()) * 100 + int((cm & taken).any()) * 100 + int((cm & th).sum() > 0)
                if best is None or hit < best[0]:
                    best = (hit, (x, y))
                if hit == 0:
                    break
            if best[0] == 0:
                break
        tags[n] = best[1]
        cv2.circle(taken, (int(best[1][0]), int(best[1][1])), TAG_R + 4, 255, -1)
    return tags


def check_route(route, tags):
    """the print check: thread polyline (5 px) and every slip / tag against every text box, unexpanded"""
    th = np.zeros((H, W), np.uint8)
    for seg in route:
        for a, b in zip(seg[:-1], seg[1:]):
            cv2.line(th, (int(a[0]), int(a[1])), (int(b[0]), int(b[1])), 255, 7)
    hits = []
    for nm, (x0, y0, x1, y1) in BOXES:
        if th[int(y0):int(y1) + 1, int(x0):int(x1) + 1].any():
            hits.append(("thread", nm))
    slips = [(nm, b) for nm, b in BOXES if nm.startswith("slip")]
    for sn, (a0, b0, a1, b1) in slips:
        for nm, (x0, y0, x1, y1) in BOXES:
            if nm == sn or nm == "legend":
                continue
            if a0 < x1 and x0 < a1 and b0 < y1 and y0 < b1:
                hits.append((sn, nm))
    for n, (x, y) in tags.items():
        for nm, (x0, y0, x1, y1) in BOXES:
            if x0 - TAG_R < x < x1 + TAG_R and y0 - TAG_R < y < y1 + TAG_R:
                hits.append((f"tag {n}", nm))
    return {"intersections": len(hits), "hits": hits, "text_boxes": len(BOXES),
            "guide_pins": sum(len(sg) - 2 for sg in route)}


def num_tag(canvas, m, x, y, n, seed):
    pm = np.zeros((H, W), np.uint8)
    cv2.circle(pm, (int(x * 4), int(y * 4)), 31 * 4, 255, -1, cv2.LINE_AA, shift=2)
    penlib.shadow_onto(canvas, pm, off=4, blur=3, opacity=0.35)
    canvas[:] = canvas * (1 - pm[..., None] / 255) + TAGP * (pm[..., None] / 255)
    ring = np.zeros((H, W), np.uint8)
    line(ring, ellipse_pts(x, y, 27, 27), 4, seed)
    a = ring.astype(np.float32)[..., None] / 255
    canvas[:] = canvas * (1 - a) + THREAD * a
    text(m, [str(n)], x, y + 15, 36, seed + 1, align="centre", weight=0.19)


# ------------------------------------------------------------------ build
def build(upto=None):
    upto = STATE["upto"] if upto is None else upto
    page = B11.wood()
    sheet = B11.paper()
    m = np.zeros((H, W), np.uint8)
    # title
    BOXES.clear()
    text_box(m, ["INVENTORY"], W / 2, 220, 92, 2501, "title", align="centre", weight=0.2)
    text_box(m, ["Objects recovered from the office at Randolph station, September 1937."], W / 2, 290, 34, 2502, "subtitle", align="centre")
    text_box(m, ["Each laid out and labelled. The red thread runs through them in the order of the afternoon."], W / 2, 340, 34, 2503, "subtitle 2", align="centre")
    anchors = {OBJ["clock"]: spec_clock(m, 2510), OBJ["memo"]: spec_memo(m, sheet, 2520), OBJ["hat"]: spec_hat(sheet, 2530),
               OBJ["cupboard"]: spec_cupboard(m, 2540), OBJ["pencil"]: spec_pencil(m, sheet, 2550), OBJ["window"]: spec_window(m, 2560),
               OBJ["door"]: spec_door(m, 2570), OBJ["key"]: spec_key(m, sheet, 2580)}
    for f, (x0, y0, x1, y1) in CELLS.items():
        lab = LABELS[f]
        text_box(m, [lab[0]], x0 + 30, y1 - 70, 32, 2600 + f, f"label Fig. {f}", weight=0.15)
        text_box(m, [lab[1]], x0 + 30, y1 - 28, 28, 2610 + f, f"label Fig. {f} (2)")
    # specimen plate rules
    rules = np.zeros((H, W), np.uint8)
    for (y0, y1) in ROW:
        line(rules, [(140, y0), (2060, y0)], 2, 2620 + y0)
    line(rules, [(140, ROW[2][1]), (2060, ROW[2][1])], 2, 2630)
    for x in (COL3[0][1], COL3[1][1]):
        line(rules, [(x, ROW[0][0] + 10), (x, ROW[1][1] - 10)], 2, 2631 + x)
    line(rules, [(COL2[0][1], ROW[2][0] + 10), (COL2[0][1], ROW[2][1] - 10)], 2, 2640)
    # legend, two columns
    text_box(m, ["THE THREAD"], 150, 2310, 38, 2650, "legend head", weight=0.18)
    BOXES.append(("legend", (140, 2250, 2060, 2760)))
    for i, (n, f, t) in enumerate(STEPS):
        col, row = i // 5, i % 5
        x, y = 150 + col * 980, 2370 + row * 76
        lines_ = b1m2.wrap(f"{n}.  {t}", 31, 900)
        text(m, lines_[:1], x, y, 31, 2660 + i)
        if len(lines_) > 1:
            text(m, [" ".join(lines_[1:])], x + 52, y + 36, 31, 2680 + i)
    sheet = sheet.astype(np.float32)
    a = rules.astype(np.float32)[..., None] / 255 * 0.7
    sheet[:] = sheet * (1 - a) + INK * a
    a = m.astype(np.float32)[..., None] / 255
    sheet[:] = sheet * (1 - a) + INK * a
    # the slips with the lines (spoken by 'the owner of Fig. n')
    canon = {k: v["text"] for k, v in B11.json.load(open(pen99.ROOT / "films/swarm/99-ways/canon.json"))["incident"]["lines"].items()}
    sm = np.zeros((H, W), np.uint8)
    step_of = {"question": 4, "answer": 5, "thanks": 6, "forgetting": 9}
    for k, anc, owner, x, y, ww in SLIPS:
        ln = b1m2.wrap(canon[k], SLIP_CAP, ww)
        if step_of[k] <= upto:
            pinned_slip(sheet, sm, ln, owner, x, y, 2700 + len(k))
        else:   # reserve its box all the same, so the thread's route is the same in every beat
            BOXES.append((f"slip {ln[0][:14]}", slip_box(ln, owner, x, y, 2700 + len(k))))
    # the thread: pins in story order
    seq = []
    used = {}
    for n, f, _ in STEPS:
        an = anchors[f]
        k = "b" if (f in used and "b" in an) else "a"
        used[f] = True
        seq.append((n, an[k]))
    route = plan_route([p for n, p in seq])
    drawn = [pt for seg in route[:max(0, upto - 1)] for pt in seg]
    if upto >= 2:
        thread_poly(sheet, route[:upto - 1], 2750)
        for seg in route[:upto - 1]:
            for q in seg[1:-1]:
                pin_at(sheet, q[0], q[1], 6, col=(120, 116, 110))      # small guide pins at the bends
    tm = np.zeros((H, W), np.uint8)
    tags = place_tags(seq, route)
    for n, p in seq:
        if n <= upto:
            pin_at(sheet, p[0], p[1], 9)
            num_tag(sheet, tm, tags[n][0], tags[n][1], n, 2760 + n)
    CHECK.update(check_route(route, tags))
    a = tm.astype(np.float32)[..., None] / 255
    sheet[:] = sheet * (1 - a) + THREAD * 0.8 * a
    pen99.folio(sheet, N, TITLE)
    # folded in four and opened again: two valley creases
    yy = np.arange(H, dtype=np.float32)[:, None]
    xx = np.arange(W, dtype=np.float32)[None, :]
    dy, dx = yy - H / 2, xx - W / 2
    shade = (1 - 0.15 * np.exp(-(dy / 7) ** 2) - 0.03 * np.exp(-((dy - 30) / 40) ** 2) + 0.02 * np.exp(-((dy + 26) / 30) ** 2))
    shade = shade * (1 - 0.12 * np.exp(-(dx / 6) ** 2) + 0.02 * np.exp(-((dx + 24) / 30) ** 2) - 0.025 * np.exp(-((dx - 28) / 36) ** 2))
    quad = np.where(dy > 0, 0.97, 1.0) * np.where(dx > 0, 0.985, 1.0)
    sheet *= (shade * quad)[..., None]
    Ms = cv2.getRotationMatrix2D((W / 2, H / 2), -0.3, 1.0)
    sh = cv2.warpAffine(sheet, Ms, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0))
    mm = np.zeros((H, W), np.uint8)
    cv2.rectangle(mm, (58, 46), (W - 58, H + 100), 255, -1)
    mm = cv2.warpAffine(mm, Ms, (W, H), flags=cv2.INTER_LINEAR)
    penlib.shadow_onto(page, mm, off=10, blur=12, opacity=0.5)
    a = mm.astype(np.float32)[..., None] / 255
    page = page * (1 - a) + sh * a
    return np.clip(np.round(page), 0, 255).astype(np.uint8)


if __name__ == "__main__":
    page = build(10)
    im = Image.fromarray(page)
    im.save(b1m2.MASTERS / f"{N:02d}-{PID}.png", optimize=True)
    jp = b1m2.PAGES_OUT / f"{N:02d}-{PID}.jpg"
    im.save(jp, quality=90)
    print("jpeg bytes", jp.stat().st_size)
    if len(sys.argv) > 1 and sys.argv[1] == "beats":
        frames = [build(k) for k in (0, 2, 4, 5, 6, 8, 9, 10)]
        b1m2.save_beats(N, frames)

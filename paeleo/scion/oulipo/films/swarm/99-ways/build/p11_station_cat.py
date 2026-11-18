"""99 ways, page 11 "The station cat" (busch-fold).
A printed picture sheet, folded once and opened again, lying on the table (the les-caids-de-la-gaudriole tabletop:
vintage paper scan CC BY 2.0, wood CC0, both graded as that work graded them). Six pictures told by the station cat:
Munzel, the cat of Wilhelm Busch's 'Die fromme Helene' (1872, PD), cut from the Commons scan of the Busch Gesamtausgabe
vol. 2 p. 246, sits on the counter and watches the clock pendulum swing; the people of the incident are Busch 1865
Max und Moritz cutouts (PD, the les-caids parts) cropped by the panel edges, their lines small and grey at the edge.
The set (wall clock with its pendulum, window, cupboard, key, memo, counter) is HANDMADE ink line in code; captions
and balloons in the shared pen hand.  Run: python3 -I p11_station_cat.py"""
import json
import math
import random
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/kit")
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import pen99  # noqa: E402
from pen99 import penlib  # noqa: E402

ROOT = pen99.ROOT
W, H = pen99.PAGE_W, pen99.PAGE_H
LCG = ROOT / "films/sources/les-caids-de-la-gaudriole"
FORAGE = ROOT / "films/sources/99-ways/forage"
CAT_SRC = FORAGE / "busch_werke_v2_p246.jpg"
INK = np.array([20, 19, 18], np.float32)
GREY = np.array([120, 118, 114], np.float32)

PW, PH = 965, 820
COLS = (110, 1125)
ROWS = (150, 1010, 1870)
CREASE_Y = 1440
SWING = [-15, 15, -15, 15, -15, 15]

CAPTIONS = [
    ["Left... right... The bob swings.", "Behind me, the man gets up."],
    ["Right... left... A voice", "at the glass. Not for me."],
    ["He looks up at MY clock.", "Left... right..."],
    ["The voice goes away. Good.", "Left... right..."],
    ["A door creaks. A shiny thing", "on a hook. It does not swing."],
    ["He stands there, mouth open.", "I never forget the bob."],
]


# ------------------------------------------------------------------ grounds (les-caids tabletop materials)
def wood():
    im = Image.open(LCG / "wood.jpg").convert("L")
    im = im.resize((int(im.width * H / im.height * 1.0) + 2, H), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32)[:, :W]
    if a.shape[1] < W:
        a = np.hstack([a, a[:, ::-1]])[:, :W]
    a = cv2.GaussianBlur(a, (0, 0), 2.0)
    a = (a - a.mean()) * 0.7 + 92                    # greyed, darkened (as les-caids graded its table)
    return np.repeat(a[..., None], 3, 2)


def paper():
    im = Image.open(LCG / "paper.jpg").convert("L").resize((W, int(W * 1630 / 1280)), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32)
    a = np.vstack([a, a[::-1]])[:H + 200]
    g = cv2.GaussianBlur(a, (0, 0), 40)
    rel = a - g                                       # keep the scan's own wrinkle and fibre, drop its stain
    out = 238 + cv2.GaussianBlur(rel, (0, 0), 1.8) * 0.38
    return np.repeat(np.clip(out, 0, 255)[..., None], 3, 2)[:H]


# ------------------------------------------------------------------ handmade ink helpers
def line(m, pts, w, seed, tremor=0.8):
    penlib.brush_line(m, pts, w, seed, tremor)


def ellipse_pts(cx, cy, rx, ry, a0=0, a1=360, n=60):
    t = np.radians(np.linspace(a0, a1, n))
    return list(zip(cx + rx * np.cos(t), cy + ry * np.sin(t)))


def hatch(m, x0, y0, x1, y1, step, w, seed, ang=-60):
    rnd = random.Random(seed)
    a = math.radians(ang)
    d = np.array([math.cos(a), math.sin(a)])
    L = (x1 - x0) + (y1 - y0)
    for k, s in enumerate(np.arange(-L, L, step)):
        p0 = np.array([x0 + s, y1])
        p1 = p0 + d * L * 2
        # clip segment to box by sampling
        pts = [p0 + (p1 - p0) * t for t in np.linspace(0, 1, 200)]
        pts = [p for p in pts if x0 <= p[0] <= x1 and y0 <= p[1] <= y1]
        if len(pts) > 2:
            j = rnd.uniform(0, 0.15)
            n = len(pts)
            pts = pts[int(n * j):max(int(n * j) + 2, int(n * (1 - rnd.uniform(0, .15))))]
            line(m, [pts[0], pts[-1]], w, seed + k, tremor=0.3)


def text(m, lines, x, y, cap, seed, align="left", weight=0.13):
    t = pen99.letter(lines, cap, seed, weight=weight)
    h, w = t.shape
    left = int(x - cap * 0.6) if align == "left" else int(x - w / 2)
    top = int(y - cap * 1.15)
    ys, xs = max(0, top), max(0, left)
    ye, xe = min(m.shape[0], top + h), min(m.shape[1], left + w)
    if ye > ys and xe > xs:
        np.maximum(m[ys:ye, xs:xe], t[ys - top:ye - top, xs - left:xe - left], out=m[ys:ye, xs:xe])
    return w, h


# ------------------------------------------------------------------ foraged cutouts
def cutout_from(gray, poly):
    """crop a Busch line plate to a hand-cut polygon: returns (gray, alpha) ; white of the plate kept as paper"""
    m = np.zeros(gray.shape, np.uint8)
    cv2.fillPoly(m, [np.int32(poly)], 255, cv2.LINE_AA)
    x, y, w, h = cv2.boundingRect(np.int32(poly))
    return gray[y:y + h, x:x + w].astype(np.float32), m[y:y + h, x:x + w]


def load_cat():
    g = np.asarray(Image.open(CAT_SRC).convert("L"))
    return g


def rgba_part(p):
    im = np.asarray(Image.open(p).convert("RGBA"))
    return im[..., 0].astype(np.float32), im[..., 3]


def paste(canvas, g, a, M, clip=None, margin=0, paper_col=(244, 242, 236)):
    """lay a cut piece (gray, alpha) with affine M (2x3) onto canvas (float RGB); a white scissor margin optional"""
    h, w = canvas.shape[:2]
    gw = cv2.warpAffine(g, M, (w, h), flags=cv2.INTER_CUBIC, borderValue=255)
    aw = cv2.warpAffine(a, M, (w, h), flags=cv2.INTER_LINEAR, borderValue=0)
    if clip is not None:
        aw = (aw.astype(np.float32) * clip).astype(np.uint8)
    if margin:
        pm = penlib.scissor((aw > 127).astype(np.uint8) * 255, margin)
        if clip is not None:
            pm = (pm.astype(np.float32) * clip).astype(np.uint8)
        penlib.shadow_onto(canvas, pm, off=4, blur=3, opacity=0.25)
        pa = pm.astype(np.float32)[..., None] / 255
        canvas[:] = canvas * (1 - pa) + np.array(paper_col, np.float32) * pa
    af = aw.astype(np.float32)[..., None] / 255
    canvas[:] = canvas * (1 - af) + np.clip(gw, 0, 255)[..., None] * af
    return aw


def affine(src_pt, dst_pt, s, deg=0.0, flip=False):
    a = math.radians(deg)
    R = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]]) * s
    if flip:
        R = R @ np.array([[-1, 0], [0, 1]])
    t = np.array(dst_pt) - R @ np.array(src_pt)
    return np.hstack([R, t[:, None]]).astype(np.float64)


# ------------------------------------------------------------------ pieces
# Munzel, cut by hand round his outline (src px of the Commons rendition, 1400x2184), with his tail up
CAT_POLY = [(755, 1600), (775, 1578), (800, 1573), (830, 1578), (865, 1578), (890, 1578), (935, 1565), (930, 1455),
            (935, 1435), (950, 1432), (963, 1450), (968, 1505), (966, 1560), (973, 1585), (1000, 1600), (1045, 1615),
            (1072, 1630), (1070, 1645), (1050, 1646), (1020, 1632), (990, 1622), (985, 1650), (980, 1673), (962, 1675),
            (948, 1658), (935, 1642), (915, 1642), (890, 1660), (850, 1672), (815, 1682), (775, 1690), (738, 1702),
            (733, 1690), (752, 1675), (765, 1667), (755, 1640), (748, 1620)]
CAT_EYE = (762, 1617)
# the widow's bonnet and shawl (Max und Moritz plate mm_016, 1280 px copy), seen through the glass
BOLTE_POLY = [(240, 180), (310, 160), (380, 160), (460, 190), (505, 240), (512, 330), (450, 350), (370, 370),
              (290, 390), (245, 350), (238, 250)]
PORTER = LCG / "panel-artist/parts/porter.body.png"
PORTER_HEAD = (285, 140)          # part px: his face (cap above, nose right)


def cat_piece():
    g = load_cat().astype(np.float32)
    return cutout_from(g, CAT_POLY)


def bolte_piece():
    g = np.asarray(Image.open(LCG / "busch/mm_016.png").convert("L")).astype(np.float32)
    return cutout_from(g, BOLTE_POLY)


def porter_piece(head_only=True):
    g, a = rgba_part(PORTER)
    a = a.copy()
    if head_only:
        a[330:] = 0             # head, shoulders and the arm; the rest falls below the counter
    return g, a


# ------------------------------------------------------------------ the set, drawn in ink (HANDMADE)
CLOCK = (380, 330, 78)           # face centre and radius (panel px)


def draw_clock(m, swing, seed):
    cx, cy, r = CLOCK
    line(m, ellipse_pts(cx, cy, r + 14, r + 14), 7, seed)
    line(m, ellipse_pts(cx, cy, r, r), 3, seed + 1)
    for k in range(12):
        a = math.radians(k * 30 - 90)
        p0 = (cx + (r - 14) * math.cos(a), cy + (r - 14) * math.sin(a))
        p1 = (cx + (r - 3) * math.cos(a), cy + (r - 3) * math.sin(a))
        line(m, [p0, p1], 5 if k % 3 == 0 else 3, seed + 2 + k, tremor=0.2)
    for ang, L, w in [(4 * 30 + 10 * 0.5, r * 0.5, 7), (10 * 6, r * 0.8, 5)]:   # 4:10
        a = math.radians(ang - 90)
        line(m, [(cx, cy), (cx + L * math.cos(a), cy + L * math.sin(a))], w, seed + 20 + w, tremor=0.2)
    cv2.circle(m, (int(cx), int(cy)), 6, 255, -1, cv2.LINE_AA)
    # the long case with its glass, the pendulum inside
    x0, x1, y0, y1 = cx - 70, cx + 70, cy + r + 12, cy + r + 280
    line(m, [(x0, y0), (x0, y1), (x1, y1), (x1, y0)], 6, seed + 30)
    line(m, [(x0 + 18, y0 + 18), (x0 + 18, y1 - 20), (x1 - 18, y1 - 20), (x1 - 18, y0 + 18), (x0 + 18, y0 + 18)], 3, seed + 31)
    hatch(m, x0 + 2, y0 + 2, x0 + 16, y1 - 2, 9, 2, seed + 32, ang=-75)
    pv = (cx, y0 + 20)
    a = math.radians(90 + swing)
    L = 205
    bob = (pv[0] + L * math.cos(a), pv[1] + L * math.sin(a))
    line(m, [pv, bob], 5, seed + 33, tremor=0.2)
    cv2.circle(m, (int(bob[0]), int(bob[1])), 30, 255, -1, cv2.LINE_AA)
    # motion ticks beside the bob (the cat's interest)
    side = 1 if swing > 0 else -1
    for k in range(3):
        aa = math.radians(90 + swing - side * (7 + 6 * k))
        q0 = (pv[0] + (L - 22) * math.cos(aa), pv[1] + (L - 22) * math.sin(aa))
        q1 = (pv[0] + (L + 22) * math.cos(aa), pv[1] + (L + 22) * math.sin(aa))
        line(m, [q0, q1], 3, seed + 40 + k, tremor=0.2)
    return bob


COUNTER_Y = 700


def draw_room(m, seed, window=True, cupboard=False):
    # the wall's base line, the counter top and its front in hatching
    line(m, [(0, 470), (PW, 470)], 3, seed)
    line(m, [(0, COUNTER_Y), (PW, COUNTER_Y)], 7, seed + 1)
    line(m, [(0, COUNTER_Y + 22), (PW, COUNTER_Y + 22)], 3, seed + 2)
    hatch(m, 0, COUNTER_Y + 26, PW, PH, 19, 2, seed + 3, ang=-80)
    if window:   # the ticket window, cut by the right edge
        x0 = 770
        line(m, [(x0, 130), (x0, 600)], 8, seed + 4)
        line(m, [(x0 + 22, 150), (x0 + 22, 600)], 3, seed + 5)
        line(m, [(x0, 130), (PW + 10, 130)], 8, seed + 6)
        line(m, [(x0, 600), (PW + 10, 600)], 8, seed + 7)
        line(m, [(x0 + 22, 370), (PW + 10, 370)], 4, seed + 8)
        text(m, ["TICKET"], x0 + 40, 200, 30, seed + 9, weight=0.16)
    if cupboard:   # the cupboard at the left, its door open on the left jamb; the SERVICE door at the right, shut
        line(m, [(100, 170), (265, 170), (265, 640), (100, 640), (100, 170)], 6, seed + 12)
        for yy in (280, 400, 520):
            line(m, [(106, yy), (259, yy)], 4, seed + 13 + yy)
        hatch(m, 102, 172, 263, 278, 11, 2, seed + 14, ang=-70)
        line(m, [(100, 170), (18, 205), (18, 610), (100, 640)], 6, seed + 15)      # the leaf, swung toward us
        x0 = 770
        line(m, [(x0, 120), (x0, COUNTER_Y)], 8, seed + 16)
        line(m, [(x0, 120), (PW + 10, 120)], 8, seed + 17)
        line(m, [(x0 + 30, 150), (PW + 10, 150)], 3, seed + 18)
        line(m, [(x0 + 30, 150), (x0 + 30, COUNTER_Y - 10)], 3, seed + 19)
        line(m, [(x0 + 30, 420), (PW + 10, 420)], 3, seed + 20)
        cv2.circle(m, (x0 + 52, 440), 9, 255, -1, cv2.LINE_AA)


def draw_key(m, hook, seed):
    hx, hy = hook
    line(m, [(hx, hy - 16), (hx, hy), (hx + 8, hy + 8)], 4, seed)
    line(m, ellipse_pts(hx, hy + 22, 13, 13), 4, seed + 1)
    line(m, [(hx, hy + 35), (hx, hy + 110)], 5, seed + 2)
    line(m, [(hx, hy + 100), (hx + 14, hy + 100), (hx + 14, hy + 110), (hx, hy + 110)], 4, seed + 3)
    line(m, [(hx + 2, hy + 40), (hx + 34, hy + 66)], 2, seed + 4)
    tx, ty = hx + 30, hy + 60
    line(m, [(tx, ty), (tx + 92, ty + 10), (tx + 88, ty + 46), (tx - 4, ty + 36), (tx, ty)], 3, seed + 5)
    t = pen99.letter(["SERVICE"], 17, seed + 6, weight=0.16)
    Mt = cv2.getRotationMatrix2D((t.shape[1] / 2, t.shape[0] / 2), -6, 1.0)
    Mt[:, 2] += np.array([tx + 44, ty + 24]) - np.array([t.shape[1] / 2, t.shape[0] / 2])
    np.maximum(m, cv2.warpAffine(t, Mt, (m.shape[1], m.shape[0])), out=m)


def service_card(m, seed):
    line(m, [(800, 220), (950, 220), (950, 286), (800, 286), (800, 220)], 3, seed)
    text(m, ["SERVICE"], 875, 268, 30, seed + 1, align="centre", weight=0.17)


def memo(m, seed):
    x0, y0 = 250, COUNTER_Y - 4
    line(m, [(x0, y0), (x0 + 24, y0 - 62), (x0 + 250, y0 - 56), (x0 + 240, y0), (x0, y0)], 3, seed)
    text(m, ["4:15 open SERVICE door."], x0 + 134, y0 - 36, 17, seed + 1, align="centre", weight=0.17)
    text(m, ["Key in cupboard."], x0 + 134, y0 - 12, 17, seed + 2, align="centre", weight=0.17)


# ------------------------------------------------------------------ panels
LINES = {1: ("STRANGER", ["Pardon me —", "have you the", "right time?"]), 2: ("AGENT", ["Ten past four,", "by the clock."]),
         3: ("STRANGER", ["Much obliged!"]), 5: ("AGENT", ["Well, here I am...", "and what for?"])}


def heard(canvas, lines, at, tip, seed):
    """a human line, heard: small cut-paper balloon in grey ink at the edge of the cat's interest"""
    b = penlib.balloon_piece([pen99.clean(l) for l in lines], 40, (tip[0] - at[0], tip[1] - at[1]), seed, tail_w=0.30, bend=0.08)
    h, w = canvas.shape[:2]
    cx, cy = b["center"]
    ox, oy = int(round(at[0] - cx)), int(round(at[1] - cy))

    def put(mm):
        out = np.zeros((h, w), np.uint8)
        Hc, Wc = mm.shape
        ys, xs = max(0, oy), max(0, ox)
        ye, xe = min(h, oy + Hc), min(w, ox + Wc)
        if ye > ys and xe > xs:
            out[ys:ye, xs:xe] = mm[ys - oy:ye - oy, xs - ox:xe - ox]
        return out
    pm, im = put(b["paper"]), put(b["ink"])
    penlib.shadow_onto(canvas, pm, off=3, blur=2, opacity=0.2)
    pa = pm.astype(np.float32)[..., None] / 255
    canvas[:] = canvas * (1 - pa) + np.array([246, 245, 240], np.float32) * pa
    penlib.ink_onto(canvas, im, GREY)


def panel(i, ground):
    """render panel i (0..5) on its own patch of the sheet; returns float RGB patch"""
    c = ground.copy()
    ink = np.zeros((PH, PW), np.uint8)
    seed = 1100 + i * 97
    swing = SWING[i]
    draw_room(ink, seed, window=i in (0, 1, 2, 3), cupboard=i in (4, 5))
    draw_clock(ink, swing, seed + 50)
    if i in (4, 5):
        service_card(ink, seed + 80)
        draw_key(ink, (52, 290), seed + 90)
    penlib.ink_onto(c, ink, INK)
    if i == 0:   # the memo slip, a paper piece lying on the counter in front of the clock case
        x0, y0 = 250, COUNTER_Y - 4
        slip = np.zeros((PH, PW), np.uint8)
        cv2.fillPoly(slip, [np.int32([(x0, y0), (x0 + 24, y0 - 62), (x0 + 250, y0 - 56), (x0 + 240, y0)])], 255, cv2.LINE_AA)
        penlib.shadow_onto(c, slip, off=4, blur=3, opacity=0.3)
        sa = slip.astype(np.float32)[..., None] / 255
        c[:] = c * (1 - sa) + np.array([247, 246, 241], np.float32) * sa
        mm = np.zeros((PH, PW), np.uint8)
        memo(mm, seed + 70)
        penlib.ink_onto(c, mm, INK)
    # the people, cut by the edges
    if i == 1:
        g, a = bolte_piece()
        clip = np.zeros((PH, PW), np.float32)
        clip[152:598, 794:] = 1
        paste(c, g, a, affine((380 - 238, 270 - 160), (880, 480), 0.85), clip=clip)
        glass = np.zeros((PH, PW), np.uint8)
        glass[152:598, 794:] = 255
        penlib.ink_onto(c, glass, np.array([200, 198, 194], np.float32), alpha=0.18)
    mouth = None
    if i in (0, 2, 4, 5):
        g, a = porter_piece()
        tilt = {0: 4, 2: -16, 4: -4, 5: -10}[i]
        at = {0: (120, 480), 2: (130, 470), 4: (110, 560), 5: (120, 540)}[i]
        M = affine(PORTER_HEAD, at, 1.15, deg=tilt)
        paste(c, g, a, M, margin=6)
        mouth = (at[0] + 40, at[1] + 40)
        if i == 5:   # the pencil to his chin (handmade)
            pm = np.zeros((PH, PW), np.uint8)
            line(pm, [(88, 668), (128, 592)], 13, seed + 99, tremor=0.2)
            penlib.ink_onto(c, pm, INK)
    # Munzel on the counter, his eye on the bob
    g, a = cat_piece()
    tilt = 4 if swing > 0 else -4             # his head follows the bob
    M = affine((170, 135), (660, COUNTER_Y - 130), 1.05, deg=tilt)
    paste(c, g, a, M)
    # caption: the cat speaks
    cap = np.zeros((PH, PW), np.uint8)
    for k, ln in enumerate(CAPTIONS[i]):
        text(cap, [ln], 34, 76 + k * 64, 46, seed + 200 + k)
    # a paper ground behind the caption so it reads over the room
    cw = max(sum(penlib.GLYPHS[ch][0] * 46 + 4.6 for ch in pen99.clean(l)) for l in CAPTIONS[i]) + 50
    box = np.zeros((PH, PW), np.uint8)
    cv2.rectangle(box, (14, 14), (int(cw), 14 + 64 * len(CAPTIONS[i]) + 26), 255, -1)
    pa = box.astype(np.float32)[..., None] / 255 * 0.85
    c[:] = c * (1 - pa) + ground * pa
    penlib.ink_onto(c, cap, INK)
    if i in LINES:
        spk, lines = LINES[i]
        if spk == "STRANGER":
            heard(c, lines, (765, 285) if i == 1 else (745, 265), (870, 440), seed + 300)
        else:
            heard(c, lines, (300, 735), mouth, seed + 300)
    return c


def build(n_panels=6):
    page = wood()
    sheet = paper()
    for i in range(n_panels):
        x0, y0 = COLS[i % 2], ROWS[i // 2]
        sheet[y0:y0 + PH, x0:x0 + PW] = panel(i, sheet[y0:y0 + PH, x0:x0 + PW])
    bm = penlib.border_mask((H, W), [(COLS[i % 2], ROWS[i // 2], COLS[i % 2] + PW, ROWS[i // 2] + PH) for i in range(n_panels)], 7, 1150)
    penlib.ink_onto(sheet, bm, INK)
    pen99.folio(sheet, 11, "The station cat")
    # the fold: folded once across the middle and opened again: a valley crease with its light and shade
    y = np.arange(H, dtype=np.float32)[:, None]
    d = y - CREASE_Y
    shade = 1 - 0.16 * np.exp(-(d / 7) ** 2) - 0.035 * np.exp(-((d - 30) / 40) ** 2) + 0.025 * np.exp(-((d + 26) / 30) ** 2)
    shade = shade * np.where(d > 0, 0.965, 1.0)    # the two halves take the lamp a little differently
    sheet *= shade[..., None]
    # lay the sheet on the table, a hair off square, with its shadow
    Ms = cv2.getRotationMatrix2D((W / 2, H / 2), 0.35, 1.0)
    Ms[:, 2] += [0, 0]
    sh = cv2.warpAffine(sheet, Ms, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
    m = np.zeros((H, W), np.uint8)
    cv2.rectangle(m, (58, 46), (W - 58, H + 100), 255, -1)
    m = cv2.warpAffine(m, Ms, (W, H), flags=cv2.INTER_LINEAR)
    penlib.shadow_onto(page, m, off=10, blur=12, opacity=0.5)
    a = m.astype(np.float32)[..., None] / 255
    page = page * (1 - a) + sh * a
    return np.clip(np.round(page), 0, 255).astype(np.uint8)




def main():
    from b1m2 import credit_pages
    out_jpg = ROOT / "assets/pages/99-ways/11-station-cat.jpg"
    out_png = ROOT / "films/sources/99-ways/masters/11-station-cat.png"
    beats = ROOT / "films/sources/99-ways/beats/11"
    beats.mkdir(parents=True, exist_ok=True)
    page = build(6)
    Image.fromarray(page).save(out_png, compress_level=6)
    Image.fromarray(page).save(out_jpg, quality=90, dpi=(300, 300))
    size = out_jpg.stat().st_size
    desc = [f"b{k:02d}: the sheet with pictures 1-{k} (pendulum {'left' if SWING[k-1] < 0 else 'right'} in picture {k}; "
            + ["E0 the man gets up at the edge", "E1 the voice at the glass", "E2 he looks up at the clock",
               "E3 the voice goes away", "E4 the cupboard open, key on its hook", "E5 he stands there; the cat watches the bob"][k - 1] + ")"
            for k in range(1, 7)]
    for k in range(1, 7):
        im = page if k == 6 else build(k)
        Image.fromarray(im).resize((960, 1242), Image.LANCZOS).save(beats / f"b{k:02d}.png")
    lcg = {e["title"]: e for e in json.load(open(ROOT / "films/credits/les-caids-de-la-gaudriole.json"))}
    new = []
    for cid, title, use in [
            ("les-caids-de-la-gaudriole:busch-mm-016", "File:Max und Moritz (Busch) 016.png", "the stranger: the widow's bonnet and shawl seen through the ticket-window glass (picture 2)"),
            ("les-caids-de-la-gaudriole:busch-mm-031", "File:Max und Moritz (Busch) 031.png", "the agent: the les-caids porter cutout (stick cut away), cropped by the left edge (pictures 1, 3, 5, 6)"),
            ("les-caids-de-la-gaudriole:vintage-paper", "File:Vintage Paper Texture (9789792113).jpg", "the printed sheet (relief and fibre kept, stain removed, graded neutral)"),
            ("les-caids-de-la-gaudriole:wood-table", "File:Wood Texture Background.jpg", "the table under the sheet (greyed, darkened)")]:
        if title in lcg:
            e = dict(lcg[title])
        else:   # downloaded by les-caids into busch/ but not used or credited there: credit read here from its file page
            e = dict(lcg["File:Max und Moritz (Busch) 031.png"])
            e.update(title=title, source_url="https://commons.wikimedia.org/wiki/File:Max_und_Moritz_(Busch)_016.png",
                     file_url="https://commons.wikimedia.org/wiki/File:Max_und_Moritz_(Busch)_016.png",
                     license="Public domain", note="local copy films/sources/les-caids-de-la-gaudriole/busch/mm_016.png "
                     "(1280 px wide derivative, sha1 4307436c0f3e68d2370b9a73b3c4d282ef9acae1); licence read from the Commons file page "
                     "(PD-old: author died 1908), saved as films/sources/99-ways/forage/mm_016_filepage.html")
            e.pop("used_as", None)
        e.update(id=cid, carried_from="films/credits/les-caids-de-la-gaudriole.json", used_as_99_ways=use)
        new.append(e)
    new.append({"id": "99-ways:busch-helene-munzel", "title": "File:Busch Werke v2 p 246.jpg",
                "author": "Wilhelm Busch (1832-1908); Die fromme Helene (1872), scan of Busch Gesamtausgabe in vier Baenden, vol. 2, p. 246",
                "license": "Public domain (Commons: PD-old-100 / published before 1931)",
                "license_url": "https://commons.wikimedia.org/wiki/Commons:Public_domain",
                "source_url": "https://commons.wikimedia.org/wiki/File:Busch_Werke_v2_p_246.jpg",
                "file_url": "https://commons.wikimedia.org/w/thumb.php?f=Busch_Werke_v2_p_246.jpg&w=1400",
                "local": "films/sources/99-ways/forage/busch_werke_v2_p246.jpg (1400x2184 rendition; sha1 a1e0845a4df59add5556ecf6dfc6b56555ead602); file page saved as busch_werke_v2_p246_filepage.html",
                "used_as": "Munzel the cat (lower picture), cut by hand round his outline: the station cat on the counter in all six pictures",
                "note": "licence read from the Commons file page (licence template text: public domain, author life+100, published before 1931); the original 1477x2304 file was rate-limited, the 1400 px server rendition was used"})
    for e in new:
        if "license" not in e:
            raise SystemExit(f"credit not found in les-caids: {e['title']}")
    src = [e["id"] for e in new] + ["99-ways:handmade"]
    credit_pages(src, 11, new_entries=new)
    rec = {
        "n": 11, "id": "station-cat", "title": "The station cat", "family": "point of view", "medium": "busch-fold",
        "canon_revision": "c1",
        "rule": "Told by the station cat on the counter, whose attention keeps drifting to the clock pendulum; the human events sit at the edge of its interest.",
        "declares": "adds a cat; human lines heard, not focused on",
        "file": str(out_jpg.relative_to(ROOT)), "master": str(out_png.relative_to(ROOT)),
        "beats_dir": str(beats.relative_to(ROOT)), "build": "films/swarm/99-ways/build/p11_station_cat.py",
        "sources": src,
        "made": [
            "a picture sheet on the les-caids tabletop: the vintage paper scan graded neutral (its own relief kept), folded once across the middle and opened (valley crease shading, the halves lit differently), laid a hair off square on the greyed wood with its shadow",
            "six pictures, 2x3: the set drawn in code in ink line (penlib.brush_line): wall clock at 4:10 with its long case and pendulum (swinging left/right alternately), ticket window lettered TICKET, counter with hatched front, the memo slip on the counter (picture 1), the cupboard with its door open on the left jamb, the key on a hook on the door with its SERVICE tag, the shut SERVICE door with its card (pictures 5-6)",
            "Munzel (Busch 1872) cut by hand from the Commons scan and laid on the counter in every picture, his head turned toward the bob, tilting with its swing",
            "the agent = the les-caids porter cutout (Busch 1865, mm_031) cropped by the left edge; the stranger = the widow's bonnet (mm_016) behind the glass; a handmade pencil at his chin in picture 6",
            "captions in the cat's voice (first person) in the shared pen hand, cap 46; the four canon lines as small grey cut-paper balloons at the edges (cap 40); folio by pen99.folio"],
        "events": {"E0": "picture 1: memo on the counter; the man at the left edge, rising ('Behind me, the man gets up')",
                   "E1": "picture 2: the bonnet behind the glass, the question in a grey balloon",
                   "E2": "picture 3: the man at the edge, head up to the clock (4:10), the answer",
                   "E3": "picture 4: the window empty, 'Much obliged!', 'The voice goes away'",
                   "E4": "picture 5: the cupboard open, the key on its hook with its tag ('A shiny thing on a hook')",
                   "E5": "picture 6: the man at the edge, pencil to chin, the forgetting line; key still on the hook, SERVICE door shut"},
        "lines": {"question": "Pardon me — have you the right time?", "answer": "Ten past four, by the clock.",
                  "thanks": "Much obliged!", "forgetting": "Well, here I am... and what for?"},
        "substitutions": "none: the four lines verbatim, set small and grey (heard, not focused on)",
        "beat": "the sheet fills picture by picture while the pendulum swings left, right, left in turn and the cat's head follows it; the people only pass at the edges",
        "beat_frames": desc,
        "self_check": {"size_px": [W, H], "jpeg_bytes": size, "jpeg_quality": 90,
                       "in_target_0.4_1.2MB": 400000 <= size <= 1200000, "pictures": 6,
                       "caption_cap_px": 46, "heard_line_cap_px": 40,
                       "check": "A reader names the cat as the one watching (maker's judgement from the full-size page: first-person captions about the bob, the cat in every picture; blind reading pending)",
                       "evidence": "measured (size, bytes) and perceptually judged (from frames) by the maker"},
    }
    json.dump(rec, open(ROOT / "films/swarm/99-ways/pages/11.json", "w"), indent=1, ensure_ascii=False)
    print(size)


if __name__ == "__main__":
    if len(sys.argv) > 2:
        Image.fromarray(build(int(sys.argv[1]))).save(sys.argv[2])
    else:
        main()

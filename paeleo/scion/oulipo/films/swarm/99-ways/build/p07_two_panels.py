"""Page 07 Two panels (reduction and expansion; medium: brush-plate).

ONE brush plate of the office, drawn once in ink (dab-chain brush after the moins-dun-quart-de-seconde
plate method), printed identically in both panels. Panel 1, before the question: the memo on the desk,
the agent set off for the cupboard, the stranger at the window putting her question. Panel 2, at the
cupboard: the open cupboard (a pasted paper overlay on the plate), the key on its hook, and the rest of
the exchange carried by balloons in reading order: answer, thanks, forgetting.
Figures: the b1m2 model brushed (white masses, black waistcoat and trousers). Lettering: shared pen hand.
"""
import hashlib
import math
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
from b1m2 import *  # noqa
from brushkit import brush, shape, wobble

N, PID, TITLE = 7, "two-panels", "Two panels"
PW, PH = 1980, 1285
SS = 2
BOX1 = (110, 110, 110 + PW, 110 + PH)
BOX2 = (110, 2730 - PH, 110 + PW, 2730)
SHEET = pen99.sheet99()
LW = 8
PRESS = 0.5          # brush pressure swing: dab width 0.5x..1.5x along a contour (thick/thin >= 2:1)
TAPER = (0.12, 0.12)

BLACK_ROLES = {"waistcoat", "trousers", "hair", "tie", "coat", "hat", "bow", "pencil", "hand"}


def S(pts):
    return [(x * SS, y * SS) for x, y in pts]


def rectp(x0, y0, x1, y1, n=6):
    pts = []
    for (a, b) in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        for i in range(n):
            pts.append((a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n))
    return pts


def box(d, rng, x0, y0, x1, y1, fill=255, w=LW, amp=0.7):
    return shape(d, S(rectp(x0, y0, x1, y1)), w * SS, rng, fill=fill, amp=amp * SS, press=PRESS, taper=TAPER)


def line(d, rng, pts, w=LW, col=0, taper=(0.2, 0.2)):
    brush(d, S(pts), w * SS, rng, col=col, taper=taper, press=PRESS)


# ------------------------------------------------------------------ geometry of the one plate
WIN = (60, 260, 430, 1110)       # window frame
SILL = 690
HEADER = 350
DESK = (480, 770, 840, 1110)
CLOCK = (650, 420, 74)
CUP = (1180, 300, 1470, 1110)
SDOOR = (1585, 240, 1880, 1110)
FLOOR = 1110


def plate_ink(seed=7):
    """The plate: 'L' image at SS (0 ink .. 255 paper). Deterministic."""
    rng = np.random.default_rng(seed)
    im = Image.new("L", (PW * SS, PH * SS), 255)
    d = ImageDraw.Draw(im)
    # floor: solid ink with white board seams
    d.rectangle([0, FLOOR * SS, PW * SS, PH * SS], fill=0)
    for k in range(7):
        y = FLOOR + 22 + k * 26
        line(d, rng, [(-10, y), (PW + 10, y + rng.uniform(-3, 3))], w=3, col=255, taper=(0.05, 0.05))
    # wainscot: a black band with white plank seams
    d.rectangle([0, 860 * SS, PW * SS, FLOOR * SS], fill=0)
    for x in range(30, PW, 64):
        line(d, rng, [(x, 872), (x + rng.uniform(-2, 2), FLOOR - 10)], w=3, col=255, taper=(0.1, 0.1))
    line(d, rng, [(-10, 860), (PW + 10, 858)], w=9)
    # wall hatching high in the corners (brush tone)
    for k in range(26):
        x = rng.uniform(0, PW)
        if WIN[0] - 20 < x < WIN[2] + 20 or CUP[0] - 20 < x < SDOOR[2] + 20:
            continue
        y = rng.uniform(40, 200)
        line(d, rng, [(x, y), (x + 38, y - 30)], w=3)
    # ceiling moulding
    line(d, rng, [(-10, 34), (PW + 10, 30)], w=10)
    # ticket window: header board (ink) lettered white, frame, panes, sill, counter front
    x0, y0, x1, y1 = WIN
    box(d, rng, x0 - 26, y0, x1 + 26, HEADER, fill=0)
    box(d, rng, x0 - 26, HEADER, x0, SILL)
    box(d, rng, x1, HEADER, x1 + 26, SILL)
    box(d, rng, (x0 + x1) / 2 - 9, HEADER, (x0 + x1) / 2 + 9, SILL)
    box(d, rng, x0, (HEADER + SILL) / 2 - 8, x1, (HEADER + SILL) / 2 + 8)
    box(d, rng, x0 - 60, SILL, x1 + 60, SILL + 34)
    box(d, rng, x0 - 40, SILL + 34, x1 + 40, FLOOR, fill=0)
    for (gx, gy) in ((x0 + 40, HEADER + 70), (x0 + 220, HEADER + 230)):
        line(d, rng, [(gx, gy + 40), (gx + 40, gy)], w=4)
        line(d, rng, [(gx + 14, gy + 56), (gx + 54, gy + 16)], w=4)
    # desk (ink mass with white drawers) and its lamp
    dx0, dy0, dx1, dy1 = DESK
    box(d, rng, dx0 - 16, dy0, dx1 + 16, dy0 + 26)
    d.rectangle([dx0 * SS, (dy0 + 26) * SS, (dx0 + 140) * SS, dy1 * SS], fill=0)
    d.rectangle([(dx0 + 140) * SS, (dy0 + 26) * SS, dx1 * SS, (dy0 + 120) * SS], fill=0)
    d.rectangle([(dx1 - 26) * SS, (dy0 + 120) * SS, dx1 * SS, dy1 * SS], fill=0)
    for k in range(3):
        yy = dy0 + 60 + k * 95
        line(d, rng, [(dx0 + 18, yy), (dx0 + 122, yy)], w=4, col=255)
        line(d, rng, [(dx0 + 62, yy + 34), (dx0 + 78, yy + 34)], w=7, col=255)
    line(d, rng, [(dx0 + 170, dy0 + 70), (dx1 - 40, dy0 + 70)], w=4, col=255)
    shape(d, S([(dx1 - 140, dy0 - 150), (dx1 - 100, dy0 - 215), (dx1 - 40, dy0 - 215), (dx1 - 0, dy0 - 150)]), LW * SS, rng, fill=0, amp=0.5, press=PRESS, taper=TAPER)
    line(d, rng, [(dx1 - 70, dy0 - 150), (dx1 - 70, dy0 - 6)], w=9)
    line(d, rng, [(dx1 - 110, dy0 - 4), (dx1 - 30, dy0 - 4)], w=12)
    # clock
    cx, cy, r = CLOCK
    ang = np.linspace(0, 2 * np.pi, 60, endpoint=False)
    d.polygon(S([(cx + (r + 16) * math.cos(a), cy + (r + 16) * math.sin(a)) for a in ang]), fill=0)
    shape(d, S([(cx + r * math.cos(a), cy + r * math.sin(a)) for a in ang]), 5 * SS, rng, fill=255, amp=0.4 * SS, press=PRESS, taper=TAPER)
    for k in range(12):
        a = math.radians(k * 30)
        line(d, rng, [(cx + r * .72 * math.sin(a), cy - r * .72 * math.cos(a)), (cx + r * .9 * math.sin(a), cy - r * .9 * math.cos(a))],
             w=7 if k % 3 == 0 else 4, taper=(0, 0))
    am, ah = math.radians(60), math.radians(125)
    line(d, rng, [(cx, cy), (cx + r * .48 * math.sin(ah), cy - r * .48 * math.cos(ah))], w=10, taper=(0, 0.3))
    line(d, rng, [(cx, cy), (cx + r * .78 * math.sin(am), cy - r * .78 * math.cos(am))], w=6, taper=(0, 0.3))
    shape(d, S([(cx - 46, cy + r + 10), (cx + 46, cy + r + 10), (cx + 46, cy + r + 140), (cx, cy + r + 170), (cx - 46, cy + r + 140)]),
          LW * SS, rng, fill=0, amp=0.4, press=PRESS, taper=TAPER)
    shape(d, S(rectp(cx - 22, cy + r + 34, cx + 22, cy + r + 126, 3)), 4 * SS, rng, fill=255, amp=0.3, press=PRESS, taper=TAPER)
    line(d, rng, [(cx, cy + r + 36), (cx + 6, cy + r + 104)], w=4, taper=(0, 0))
    d.ellipse([(cx + 6 - 12) * SS, (cy + r + 104 - 12) * SS, (cx + 6 + 12) * SS, (cy + r + 104 + 12) * SS], fill=0)
    # cupboard (closed on the plate): white door in an ink case
    c0, c1, c2, c3 = CUP
    box(d, rng, c0 - 18, c1 - 34, c2 + 18, c1, fill=0)
    d.rectangle([c0 * SS, c1 * SS, c2 * SS, c3 * SS], fill=0)
    box(d, rng, c0 + 20, c1 + 20, c2 - 20, c3 - 20)
    for (a, b) in ((0.12, 0.47), (0.53, 0.9)):
        box(d, rng, c0 + 50, c1 + (c3 - c1) * a, c2 - 50, c1 + (c3 - c1) * b, w=5)
    d.ellipse([(c2 - 52) * SS, ((c1 + c3) / 2 - 10) * SS, (c2 - 32) * SS, ((c1 + c3) / 2 + 10) * SS], fill=0)
    # SERVICE door with its card
    s0, s1, s2, s3 = SDOOR
    d.rectangle([(s0 - 20) * SS, (s1 - 20) * SS, (s2 + 20) * SS, s3 * SS], fill=0)
    box(d, rng, s0, s1, s2, s3)
    for (a, b) in ((0.30, 0.56), (0.63, 0.93)):
        box(d, rng, s0 + 46, s1 + (s3 - s1) * a, s2 - 46, s1 + (s3 - s1) * b, w=5)
    d.ellipse([(s2 - 44) * SS, (s1 + (s3 - s1) * 0.58 - 11) * SS, (s2 - 22) * SS, (s1 + (s3 - s1) * 0.58 + 11) * SS], fill=0)
    box(d, rng, s0 + 50, s1 + 300, s2 - 50, s1 + 380, w=6)
    return im


def plate_letters(L):
    """Pen-hand lettering that belongs to the plate: TICKET OFFICE (white on the header), SERVICE card, memo."""
    mw = np.zeros((PH, PW), np.uint8)
    x0, y0, x1, y1 = WIN
    put_mask(mw, letter(["TICKET OFFICE"], 34, 7001, weight=0.16), (x0 + x1) / 2, (y0 + HEADER) / 2 + 2)
    mb = np.zeros((PH, PW), np.uint8)
    s0, s1, s2, s3 = SDOOR
    put_mask(mb, letter(["SERVICE"], 40, 7002, weight=0.16), (s0 + s2) / 2, s1 + 340)
    return mw, mb


_PLATE = None


def plate():
    """The identical plate layer: ink alpha (float 0..1, PH x PW) incl. its lettering; memo slip separate."""
    global _PLATE
    if _PLATE is None:
        im = plate_ink()
        L = np.asarray(im.resize((PW, PH), Image.LANCZOS)).astype(np.float32) / 255.0
        ink = 1 - L
        mw, mb = plate_letters(L)
        ink = np.maximum(ink, mb / 255.0)
        ink = ink * (1 - mw / 255.0)
        _PLATE = ink
    return _PLATE


def memo(canvas):
    dx0, dy0, dx1, dy1 = DESK
    return slip(canvas, dx0 - 30, dy0 - 64, ["4:15 - open SERVICE door.", "Key in cupboard."], 30, 7010,
                paper=np.array([250, 248, 240], np.float32), pad=(18, 10), tilt=-2, shadow=0.0)


def fig_brush(d, shapes, rng):
    for s in sorted(shapes, key=lambda s: s.z):
        pts = S(s.curve())
        role = s.role
        if role in ("pin", "glass_in"):
            continue
        if role == "button":
            c = np.mean(pts, axis=0)
            d.ellipse([c[0] - 5 * SS, c[1] - 5 * SS, c[0] + 5 * SS, c[1] + 5 * SS], fill=255)
            continue
        if role == "glass":
            c = np.mean(pts, axis=0)
            rr = 12 * SS
            d.ellipse([c[0] - rr, c[1] - rr, c[0] + rr, c[1] + rr], outline=0, width=int(4 * SS))
            continue
        if role in ("glass_arm", "garter"):
            d.polygon([tuple(p) for p in pts], fill=0)
            continue
        if role == "eye":
            c = np.mean(pts, axis=0)
            d.ellipse([c[0] - 5 * SS, c[1] - 5 * SS, c[0] + 5 * SS, c[1] + 5 * SS], fill=0)
            continue
        fill = 0 if role in BLACK_ROLES else 255
        shape(d, pts, (6 if role != "pencil" else 2) * SS, rng, fill=fill, amp=0.5 * SS, press=PRESS, taper=TAPER)


def figures_layer(shapes, seed):
    """Brushed figures: returns (ink alpha, paper alpha) at panel size."""
    im = Image.new("L", (PW * SS, PH * SS), 128)
    d = ImageDraw.Draw(im)
    fig_brush(d, shapes, np.random.default_rng(seed))
    a = np.asarray(im.resize((PW, PH), Image.LANCZOS)).astype(np.float32)
    cover = np.abs(a - 128) / 127.0
    # anything not 128 was drawn: black ink or white paper
    m = Image.new("L", (PW * SS, PH * SS), 0)
    dm = ImageDraw.Draw(m)
    for s in shapes:
        if not s.hole:
            dm.polygon([tuple(p) for p in S(s.curve())], fill=255)
    m = cv2.dilate(np.asarray(m), np.ones((15, 15), np.uint8))
    m = np.asarray(Image.fromarray(m).resize((PW, PH), Image.LANCZOS)).astype(np.float32) / 255
    ink = np.clip((128 - a) / 128, 0, 1) * m
    paper = m * (1 - ink)
    return ink, paper


def brushed_balloon(canvas, lines, cap, at, tip, seed, upto=1.0, bendk=0.08, ctrl=None, mask_out=None):
    """White balloon (ellipse + tail, cut as one shape) with a brushed contour; pen-hand lines inside."""
    rng = np.random.default_rng(seed)
    lm = letter(lines, cap, seed + 1)
    h, w = lm.shape
    rx, ry = w * 0.5 * 1.16 + cap * 0.35, h * 0.5 * 1.08 + cap * 0.3
    cx, cy = at
    aim = tip if ctrl is None else ctrl
    a0 = math.atan2((aim[1] - cy) / ry, (aim[0] - cx) / rx)
    b1 = np.array((cx + rx * .85 * math.cos(a0 - 0.2), cy + ry * .85 * math.sin(a0 - 0.2)))
    b2 = np.array((cx + rx * .85 * math.cos(a0 + 0.2), cy + ry * .85 * math.sin(a0 + 0.2)))
    mid = (b1 + b2) / 2
    tp = np.array(tip, float)
    if ctrl is None:
        bend = np.array([-(tp[1] - mid[1]), tp[0] - mid[0]]) * bendk
        c1_, c2_ = mid + bend, mid + bend * .5
    else:   # explicit route: both tail edges bow through the given control point (a narrow, curved tail)
        cp = np.array(ctrl, float)
        nrm = np.array([-(tp[1] - cp[1]), tp[0] - cp[0]])
        nrm = nrm / (np.linalg.norm(nrm) + 1e-9) * cap * 0.22
        c1_, c2_ = cp + nrm, cp - nrm
    tail = [b1 * (1 - t) ** 2 + 2 * (1 - t) * t * c1_ + tp * t * t for t in np.linspace(0, 1, 40)]
    tail += [tp * (1 - t) ** 2 + 2 * (1 - t) * t * c2_ + b2 * t * t for t in np.linspace(0, 1, 40)]
    m = np.zeros((PH * SS, PW * SS), np.uint8)
    cv2.ellipse(m, (int(cx * SS), int(cy * SS)), (int(rx * SS), int(ry * SS)), 0, 0, 360, 255, -1)
    tm = np.zeros_like(m)
    cv2.fillPoly(tm, [np.int32(np.array(tail + [mid]) * SS)], 255)
    if mask_out is not None:      # the tail's own footprint, for the overlap check
        e = np.zeros_like(m)
        cv2.ellipse(e, (int(cx * SS), int(cy * SS)), (int(rx * SS), int(ry * SS)), 0, 0, 360, 255, -1)
        tl = cv2.resize(np.where(e > 0, 0, tm).astype(np.uint8), (PW, PH), interpolation=cv2.INTER_AREA)
        mask_out.append(cv2.dilate(tl, np.ones((9, 9), np.uint8)))     # + the contour's brush width
    m = np.maximum(m, tm)
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    cpts = max(cs, key=len)[:, 0, :].astype(float)[::3]
    im = Image.new("L", (PW * SS, PH * SS), 128)
    d = ImageDraw.Draw(im)
    shape(d, [tuple(p) for p in cpts], 7 * SS, rng, fill=255, amp=0.3 * SS, press=0.45, taper=TAPER)
    a = np.asarray(im.resize((PW, PH), Image.LANCZOS)).astype(np.float32)
    ink = np.clip((128 - a) / 128, 0, 1)
    white = np.clip((a - 128) / 127, 0, 1)
    comp(canvas, (white * 255).astype(np.uint8), np.array([252, 250, 244], np.float32))
    comp(canvas, (ink * 255).astype(np.uint8), INK)
    if upto > 0:
        mm = np.zeros((PH, PW), np.uint8)
        if upto < 1:
            lm = lm.copy()
            lm[:, int(w * upto):] = 0
        put_mask(mm, lm, cx, cy + cap * 0.02)
        comp(canvas, mm, INK)


def ground(box):
    x0, y0, x1, y1 = box
    return SHEET[y0:y1, x0:x1].copy()


PLATE_LAID = []     # sha256 of the plate ink as laid in each panel render


def lay_plate(canvas):
    ink = plate()
    u8 = (ink * 255).astype(np.uint8)
    PLATE_LAID.append(hashlib.sha256(u8.tobytes()).hexdigest())
    comp(canvas, u8, INK)


def brush_check():
    """Thick/thin of the plate's brushed contours: ink run-width across five long straight panel edges
    (10th and 90th percentile per edge), measured on the plate layer at panel size."""
    ink = plate()
    c0, c1, c2, c3 = CUP
    s0, s1, s2, s3 = SDOOR
    edges = {"cupboard upper panel, left": (c0 + 50, c1 + (c3 - c1) * .14, c1 + (c3 - c1) * .45),
             "cupboard upper panel, right": (c2 - 50, c1 + (c3 - c1) * .14, c1 + (c3 - c1) * .45),
             "cupboard lower panel, left": (c0 + 50, c1 + (c3 - c1) * .55, c1 + (c3 - c1) * .88),
             "SERVICE door lower panel, left": (s0 + 46, s1 + (s3 - s1) * .65, s1 + (s3 - s1) * .91),
             "SERVICE door lower panel, right": (s2 - 46, s1 + (s3 - s1) * .65, s1 + (s3 - s1) * .91)}
    out = {}
    for k, (x, ya, yb) in edges.items():
        w = (ink[int(ya):int(yb), int(x) - 14:int(x) + 14] > 0.5).sum(1)
        w = w[w > 0]
        lo, hi = float(np.percentile(w, 10)), float(np.percentile(w, 90))
        out[k] = {"thin_px": lo, "thick_px": hi, "ratio": round(hi / lo, 2)}
    return out


def lay_figs(canvas, shapes, seed):
    ink, paper = figures_layer(shapes, seed)
    comp(canvas, (paper * 255).astype(np.uint8), np.array([250, 248, 242], np.float32))
    comp(canvas, (ink * 255).astype(np.uint8), INK)


def panel1(st=None):
    c = ground(BOX1)
    lay_plate(c)
    memo(c)
    x0, y0, x1, y1 = WIN
    lay_figs(c, stranger((x0 + x1) / 2 - 10, SILL + 6, face=1, scale=1.25, glove=True), 7101)
    lay_figs(c, agent(1000, FLOOR + 12, face=1, scale=0.86, legs=(20, -18), sh=-20, el=22, lean=3, pencil_deg=200,
                      far_arm=(20, 20)), 7102)
    brushed_balloon(c, ["Pardon me —", "have you the", "right time?"], 52, (690, 150), (300, 420), 7103)
    return c


AG2 = dict(x=1262, scale=0.86, legs=(4, -4), sh=5, el=140, wr=40, pencil_deg=175, tilt=6)   # P2: pencil to chin
KEY2 = 600          # P2: the key's hook height in the cupboard (hangs below the forgetting tail's path)
CHECK = {}


def agent2():
    g = dict(AG2)
    return agent(g.pop("x"), FLOOR + 12, face=1, **g)


def face_points(shapes):
    """World points of the P2 head outline: nose tip, lips, chin (HEAD indices 11, 14-16, 17)."""
    head = [q for q in shapes if q.role == "skin" and q.z == 0][0].pts
    return {"nose": head[11], "lip_up": head[14], "mouth": head[15], "lip_lo": head[16], "chin": head[17]}


def leaf_poly():
    c0, c1, c2, c3 = CUP
    return [(c0, c1 - 6), (c0 - 112, c1 - 50), (c0 - 112, c3 + 40), (c0, c3)]


def mask_of(polys, dil=0):
    m = np.zeros((PH, PW), np.uint8)
    for pts in polys:
        cv2.fillPoly(m, [np.int32(np.round(np.asarray(pts)))], 255)
    if dil:
        m = cv2.dilate(m, np.ones((dil, dil), np.uint8))
    return m


def panel2(st=None):
    st = st or {}
    c = ground(BOX2)
    lay_plate(c)
    memo(c)
    c0, c1, c2, c3 = CUP
    shapes = agent2()
    fp = face_points(shapes)
    if st.get("open", True):
        # a pasted paper overlay: the cupboard open (lit inside, shelves, the key on its hook) and the swung leaf
        rng = np.random.default_rng(7201)
        im = Image.new("L", (PW * SS, PH * SS), 128)
        d = ImageDraw.Draw(im)
        d.rectangle([(c0 + 20) * SS, (c1 + 20) * SS, (c2 - 20) * SS, (c3 - 20) * SS], fill=255)
        for fy in (0.50, 0.78):
            y = c1 + (c3 - c1) * fy
            shape(d, S(rectp(c0 + 20, y, c2 - 20, y + 16, 3)), 5 * SS, rng, fill=0, amp=0.3, press=PRESS, taper=TAPER)
        brush(d, S([(c0 + 20, c1 + 24), (c0 + 30, c3 - 24)]), 7 * SS, rng, col=0, press=PRESS)
        leaf = leaf_poly()
        dens = []
        for a, b in zip(leaf, leaf[1:] + leaf[:1]):
            for t in np.linspace(0, 1, 8, endpoint=False):
                dens.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
        shape(d, S(dens), LW * SS, rng, fill=255, amp=0.4, press=PRESS, taper=TAPER)
        for (a, b) in ((0.14, 0.46), (0.54, 0.88)):
            y0_, y1_ = c1 + (c3 - c1) * a, c1 + (c3 - c1) * b
            q = [(c0 - 18, y0_ - 8), (c0 - 92, y0_ - 30), (c0 - 92, y1_ + 22), (c0 - 18, y1_ + 6)]
            dq = []
            for a_, b_ in zip(q, q[1:] + q[:1]):
                for t in np.linspace(0, 1, 6, endpoint=False):
                    dq.append((a_[0] + (b_[0] - a_[0]) * t, a_[1] + (b_[1] - a_[1]) * t))
            shape(d, S(dq), 5 * SS, rng, fill=255, amp=0.3, press=PRESS, taper=TAPER)
        a = np.asarray(im.resize((PW, PH), Image.LANCZOS)).astype(np.float32)
        comp(c, (np.clip((a - 128) / 127, 0, 1) * 255).astype(np.uint8), np.array([250, 248, 242], np.float32))
        comp(c, (np.clip((128 - a) / 128, 0, 1) * 255).astype(np.uint8), INK)
        # the key (ANRC cutout) printed as ink on its hook, with its SERVICE tag, in the right half of the open
        # cupboard, in front of his eyes; he stands between the leaf and the cupboard interior, facing it
        km = np.zeros((PH, PW), np.uint8)
        kx, ky = c2 - 52, KEY2
        paste_mask(km, key_alpha(), kx, ky, 0.27)
        hk = np.zeros((PH, PW), np.uint8)
        penlib.brush_line(hk, [(kx - 24, ky - 104), (kx + 4, ky - 104), (kx + 4, ky - 88)], 8, 7203)
        comp(c, np.maximum(km, hk), INK)
        slip(c, int(kx + 12), int(ky + 30), ["SERVICE"], 26, 7204, paper=np.array([250, 248, 240], np.float32),
             pad=(12, 4), tilt=10, shadow=0.0)
        CHECK["key_box"] = [int(kx - 30), int(ky - 110), int(kx + 30), int(ky + 110)]
    lay_figs(c, shapes, 7202)
    k = st.get("balloons", 3)
    tails = []
    m, n = fp["mouth"], fp["nose"]
    a_tip = (n[0] + 2, m[1] + 3)                    # under the nose, in front of the lips, approached from above
    f_tip = (n[0] + 4, fp["lip_lo"][1] + 11)        # in front of the lower lip, approached from the right
    if k >= 1:
        brushed_balloon(c, ["Ten past four,", "by the clock."], 52, (275, 122), a_tip, 7211,
                        ctrl=(1480, 40), mask_out=tails)
    if k >= 2:
        brushed_balloon(c, ["Much", "obliged!"], 46, (700, 222), (330, 470), 7212, ctrl=(470, 330))
    if k >= 3:
        brushed_balloon(c, ["Well,", "here I am...", "and what for?"], 50, (1735, 330), f_tip, 7213,
                        ctrl=(1440, 448), mask_out=tails)
    if k >= 3:
        arm = [q.pts for q in shapes if q.z >= 5 and q.role in ("sleeve", "skin", "garter")]
        pen = [q.pts for q in shapes if q.role == "pencil"]
        CHECK.update({
            "forgetting_tail_px_on_arm": int(((tails[1] > 0) & (mask_of(arm, 7) > 0)).sum()),
            "forgetting_tail_px_on_pencil": int(((tails[1] > 0) & (mask_of(pen, 5) > 0)).sum()),
            "forgetting_tail_px_on_leaf": int(((tails[1] > 0) & (mask_of([leaf_poly()], 9) > 0)).sum()),
            "answer_tail_px_on_forgetting_tail": int(((tails[0] > 0) & (tails[1] > 0)).sum()),
            "answer_tail_px_on_key": int(((tails[0] > 0) & (mask_of([[(CHECK['key_box'][0], CHECK['key_box'][1]), (CHECK['key_box'][2], CHECK['key_box'][1]), (CHECK['key_box'][2], CHECK['key_box'][3]), (CHECK['key_box'][0], CHECK['key_box'][3])]]) > 0)).sum()),
            "answer_tip_to_mouth_px": round(float(np.hypot(a_tip[0] - m[0], a_tip[1] - m[1])), 1),
            "forgetting_tip_to_mouth_px": round(float(np.hypot(f_tip[0] - m[0], f_tip[1] - m[1])), 1),
            "agent_back_minus_leaf_edge_px": int(min(q.pts[:, 0].min() for q in shapes) - CUP[0]),
            "eye_to_key": "eye at (%d,%d), key ring at (%d,%d): he faces right, head tilted 6 deg down, toward the key" % (
                int(face_points(shapes)["nose"][0] - 40), int(face_points(shapes)["nose"][1] - 20), CUP[2] - 52, KEY2 - 60),
        })
    return c


def build(st2=None):
    page = SHEET.copy()
    for box_, fn in ((BOX1, panel1), (BOX2, panel2)):
        x0, y0, x1, y1 = box_
        page[y0:y1, x0:x1] = fn(st2) if fn is panel2 else fn()
    frame_border(page, [BOX1, BOX2], w=12, seed=7300)
    return page


def plate_hash():
    ink = (plate() * 255).astype(np.uint8)
    return hashlib.sha256(ink.tobytes()).hexdigest()


if __name__ == "__main__":
    page = build()
    img, size = save_page(page, N, PID, TITLE)
    print("jpeg bytes", size, "plate sha256", plate_hash()[:16])
    if len(sys.argv) > 1 and sys.argv[1] == "beats":
        frames = []
        for st in ({"open": False, "balloons": 0}, {"open": True, "balloons": 0}, {"balloons": 1}, {"balloons": 2}, {"balloons": 3}):
            p = np.clip(np.round(build(st)), 0, 255).astype(np.uint8)
            pen99.folio(p, N, TITLE)
            frames.append(np.asarray(Image.fromarray(p).resize((960, 1242), Image.LANCZOS)))
        save_beats(N, frames)

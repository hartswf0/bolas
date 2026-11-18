"""Page 29 One fixed lens (point of view; medium: brush-plate).

One brush plate of the office (page 07's plate geometry and dab-chain brush, after the HANDMADE brush method of
moins-dun-quart-de-seconde-pour-vivre, copied in build/brushkit.py), redrawn with a heavier brush and WITHOUT the
two parts that are allowed to change: the clock's hands and the cupboard door. The identical plate (with the
memo slip lying on the desk) is printed in all eight panels; only the figures (b1m2 model, brushed), the clock
hands and the cupboard door (closed / open, a pasted overlay) change. The plate as laid is hashed per panel.
Run: python3 -I p29_one_fixed_lens.py [beats]
"""
import hashlib
import math
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
from b1m2 import *  # noqa
import brushkit
import p07_two_panels as p7
from p07_two_panels import (PW, PH, SS, FLOOR, WIN, SILL, HEADER, DESK, CLOCK, CUP, SDOOR, LW, S, rectp, PRESS, TAPER,
                            BLACK_ROLES)

N, PID, TITLE = 29, "one-fixed-lens", "One fixed lens"
K = 1.85                 # brush weight factor: panels are printed at 0.49 of the plate's drawing size
SHEET = cv2.GaussianBlur(pen99.sheet99(), (0, 0), 0.8)   # softened fibre keeps the JPEG under 1.2 MB


def shape(d, pts, w, rng, **kw):
    return brushkit.shape(d, pts, w * K, rng, **kw)


def box(d, rng, x0, y0, x1, y1, fill=255, w=LW, amp=0.7):
    return shape(d, S(rectp(x0, y0, x1, y1)), w * SS, rng, fill=fill, amp=amp * SS, press=PRESS, taper=TAPER)


def line(d, rng, pts, w=LW, col=0, taper=(0.2, 0.2)):
    brushkit.brush(d, S(pts), w * SS * K, rng, col=col, taper=taper, press=PRESS)


def brush(d, pts, w, rng, **kw):
    brushkit.brush(d, pts, w * K, rng, **kw)


def plate_ink29(seed=29):
    """The page-29 plate: page 07's office plate redrawn with heavier brush (K) and WITHOUT the clock hands or
    the cupboard door, which are the only set parts that change (laid per panel). 'L' image at SS."""
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
    shape(d, S([(cx - 46, cy + r + 10), (cx + 46, cy + r + 10), (cx + 46, cy + r + 140), (cx, cy + r + 170), (cx - 46, cy + r + 140)]),
          LW * SS, rng, fill=0, amp=0.4, press=PRESS, taper=TAPER)
    shape(d, S(rectp(cx - 22, cy + r + 34, cx + 22, cy + r + 126, 3)), 4 * SS, rng, fill=255, amp=0.3, press=PRESS, taper=TAPER)
    line(d, rng, [(cx, cy + r + 36), (cx + 6, cy + r + 104)], w=4, taper=(0, 0))
    d.ellipse([(cx + 6 - 12) * SS, (cy + r + 104 - 12) * SS, (cx + 6 + 12) * SS, (cy + r + 104 + 12) * SS], fill=0)
    # cupboard case only (its door is laid per panel)
    c0, c1, c2, c3 = CUP
    box(d, rng, c0 - 18, c1 - 34, c2 + 18, c1, fill=0)
    d.rectangle([c0 * SS, c1 * SS, c2 * SS, c3 * SS], fill=0)
    # SERVICE door with its card
    s0, s1, s2, s3 = SDOOR
    d.rectangle([(s0 - 20) * SS, (s1 - 20) * SS, (s2 + 20) * SS, s3 * SS], fill=0)
    box(d, rng, s0, s1, s2, s3)
    for (a, b) in ((0.30, 0.56), (0.63, 0.93)):
        box(d, rng, s0 + 46, s1 + (s3 - s1) * a, s2 - 46, s1 + (s3 - s1) * b, w=5)
    d.ellipse([(s2 - 44) * SS, (s1 + (s3 - s1) * 0.58 - 11) * SS, (s2 - 22) * SS, (s1 + (s3 - s1) * 0.58 + 11) * SS], fill=0)
    box(d, rng, s0 + 50, s1 + 300, s2 - 50, s1 + 380, w=6)
    return im




_PLATE = None


def plate():
    """The background drawing, identical in every panel: plate ink + its lettering (TICKET OFFICE, SERVICE card),
    then the memo slip, as RGB float on a blank (white) sheet-free canvas; returned with its alpha."""
    global _PLATE
    if _PLATE is None:
        im = plate_ink29()
        L = np.asarray(im.resize((PW, PH), Image.LANCZOS)).astype(np.float32) / 255.0
        ink = 1 - L
        mw, mb = p7.plate_letters(L)
        mw = cv2.dilate(mw, np.ones((3, 3), np.uint8))
        ink = np.maximum(ink, cv2.dilate(mb, np.ones((3, 3), np.uint8)) / 255.0)
        ink = ink * (1 - mw / 255.0)
        _PLATE = (ink * 255).astype(np.uint8)
    return _PLATE


def memo(canvas):
    dx0, dy0, dx1, dy1 = DESK
    return slip(canvas, dx0 - 40, dy0 - 108, ["4:15 - open", "SERVICE door.", "Key in cupboard."], 46, 2910,
                paper=np.array([250, 248, 240], np.float32), pad=(18, 10), tilt=-2, shadow=0.0, weight=0.15)


def background():
    """Plate + memo on the sheet ground (the sheet is the page's own; the plate is the drawing)."""
    c = np.full((PH, PW, 3), 255.0, np.float32)
    comp(c, plate(), INK)
    memo(c)
    return c


# ------------------------------------------------------------------ the changing parts
def overlay(drawfn, seed):
    rng = np.random.default_rng(seed)
    im = Image.new("L", (PW * SS, PH * SS), 128)
    d = ImageDraw.Draw(im)
    drawfn(d, rng)
    a = np.asarray(im.resize((PW, PH), Image.LANCZOS)).astype(np.float32)
    return np.clip((a - 128) / 127, 0, 1), np.clip((128 - a) / 128, 0, 1)


def lay_overlay(c, ov):
    white, ink = ov
    comp(c, (white * 255).astype(np.uint8), np.array([252, 250, 244], np.float32))
    comp(c, (ink * 255).astype(np.uint8), INK)


def clock_hands(c, hh, mm, seed):
    cx, cy, r = CLOCK

    def f(d, rng):
        am = math.radians(mm * 6)
        ah = math.radians((hh % 12) * 30 + mm * 0.5)
        line(d, rng, [(cx, cy), (cx + r * .48 * math.sin(ah), cy - r * .48 * math.cos(ah))], w=8, taper=(0, 0.3))
        line(d, rng, [(cx, cy), (cx + r * .80 * math.sin(am), cy - r * .80 * math.cos(am))], w=5, taper=(0, 0.3))
        d.ellipse([(cx - 9) * SS, (cy - 9) * SS, (cx + 9) * SS, (cy + 9) * SS], fill=0)
    lay_overlay(c, overlay(f, seed))


def door_closed(c, seed):
    c0, c1, c2, c3 = CUP

    def f(d, rng):
        box(d, rng, c0 + 20, c1 + 20, c2 - 20, c3 - 20)
        for (a, b) in ((0.12, 0.47), (0.53, 0.9)):
            box(d, rng, c0 + 50, c1 + (c3 - c1) * a, c2 - 50, c1 + (c3 - c1) * b, w=5)
        d.ellipse([(c2 - 56) * SS, ((c1 + c3) / 2 - 13) * SS, (c2 - 30) * SS, ((c1 + c3) / 2 + 13) * SS], fill=0)
    lay_overlay(c, overlay(f, seed))


KEY = (CUP[2] - 60, 600)


def door_open(c, seed):
    c0, c1, c2, c3 = CUP

    def f(d, rng):
        d.rectangle([(c0 + 20) * SS, (c1 + 20) * SS, (c2 - 20) * SS, (c3 - 20) * SS], fill=255)
        for fy in (0.50, 0.78):
            y = c1 + (c3 - c1) * fy
            shape(d, S(rectp(c0 + 20, y, c2 - 20, y + 16, 3)), 5 * SS, rng, fill=0, amp=0.3, press=PRESS, taper=TAPER)
        brush(d, S([(c0 + 20, c1 + 24), (c0 + 30, c3 - 24)]), 7 * SS, rng, col=0, press=PRESS)
        leaf = p7.leaf_poly()
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
    lay_overlay(c, overlay(f, seed))
    km = np.zeros((PH, PW), np.uint8)
    kx, ky = KEY
    paste_mask(km, key_alpha(), kx, ky, 0.30)
    hk = np.zeros((PH, PW), np.uint8)
    penlib.brush_line(hk, [(kx - 26, ky - 116), (kx + 4, ky - 116), (kx + 4, ky - 98)], 12, seed + 3)
    comp(c, np.maximum(km, hk), INK)
    slip(c, int(kx - 30), int(ky + 46), ["SERVICE"], 40, seed + 4, paper=np.array([250, 248, 240], np.float32),
         pad=(12, 4), tilt=8, shadow=0.0, weight=0.16)


def fig_brush(d, shapes, rng):
    """p07's brushed figure, heavier brush (K)."""
    for s in sorted(shapes, key=lambda s: s.z):
        pts = S(s.curve())
        role = s.role
        if role in ("pin", "glass_in"):
            continue
        if role == "button":
            cc = np.mean(pts, axis=0)
            d.ellipse([cc[0] - 6 * SS, cc[1] - 6 * SS, cc[0] + 6 * SS, cc[1] + 6 * SS], fill=255)
            continue
        if role == "glass":
            cc = np.mean(pts, axis=0)
            rr = 13 * SS
            d.ellipse([cc[0] - rr, cc[1] - rr, cc[0] + rr, cc[1] + rr], outline=0, width=int(6 * SS))
            continue
        if role in ("glass_arm", "garter"):
            d.polygon([tuple(p) for p in pts], fill=0)
            continue
        if role == "eye":
            cc = np.mean(pts, axis=0)
            d.ellipse([cc[0] - 7 * SS, cc[1] - 7 * SS, cc[0] + 7 * SS, cc[1] + 7 * SS], fill=0)
            continue
        fill = 0 if role in BLACK_ROLES else 255
        shape(d, pts, (6 if role != "pencil" else 3) * SS, rng, fill=fill, amp=0.5 * SS, press=PRESS, taper=TAPER)


p7.fig_brush = fig_brush      # p7.figures_layer draws with this heavier brush


def figs(c, shapes, seed):
    ink, paper = p7.figures_layer(shapes, seed)
    comp(c, (paper * 255).astype(np.uint8), np.array([250, 248, 242], np.float32))
    comp(c, (ink * 255).astype(np.uint8), INK)


def bal(c, lines, cap, at, tip, seed, ctrl=None):
    """p07's brushed balloon at a heavier contour: drawn by p7.brushed_balloon with brushkit.shape scaled."""
    p7.shape = shape
    try:
        p7.brushed_balloon(c, lines, cap, at, tip, seed, ctrl=ctrl)
    finally:
        p7.shape = brushkit.shape


# ------------------------------------------------------------------ the eight states (same lens)
WX = (WIN[0] + WIN[2]) / 2
AGENT_Y = FLOOR + 12


def agent_mouth(shapes):
    f = p7.face_points(shapes)
    return f["nose"][0] + 4, f["mouth"][1] + 4


def st1(c):   # E0 at the desk, reading the memo: 4:09
    clock_hands(c, 4, 9, 2921); door_closed(c, 2922)
    figs(c, agent(930, AGENT_Y, face=-1, scale=0.86, legs=(4, -4), sh=30, el=-70, wr=10, tilt=18, pencil_deg=200), 2923)


def st2(c):   # E0 he sets off for the cupboard: 4:09
    clock_hands(c, 4, 9, 2921); door_closed(c, 2922)
    figs(c, agent(1010, AGENT_Y, face=1, scale=0.86, legs=(20, -18), sh=-20, el=22, lean=3, pencil_deg=200,
                  far_arm=(20, 20)), 2924)


def st3(c):   # E1 the question at the window: 4:10
    clock_hands(c, 4, 10, 2931); door_closed(c, 2922)
    figs(c, stranger(WX - 10, SILL + 6, face=1, scale=1.25, glove=True), 2932)
    figs(c, agent(1010, AGENT_Y, face=-1, scale=0.86, legs=(8, -8), sh=6, el=10, tilt=-2, pencil_deg=200), 2933)
    bal(c, ["Pardon me — have", "you the right time?"], 86, (930, 200), (300, 420), 2934)


def st4(c):   # E2 he looks up at the clock and answers: 4:10
    clock_hands(c, 4, 10, 2931); door_closed(c, 2922)
    figs(c, stranger(WX - 10, SILL + 6, face=1, scale=1.25, glove=True), 2932)
    a = agent(1010, AGENT_Y, face=-1, scale=0.86, legs=(8, -8), sh=10, el=-20, tilt=-26, pencil_deg=200)
    figs(c, a, 2943)
    bal(c, ["Ten past four,", "by the clock."], 86, (1500, 200), agent_mouth(a), 2944)


def st5(c):   # E3 the thanks; she turns from the window: 4:10
    clock_hands(c, 4, 10, 2931); door_closed(c, 2922)
    figs(c, stranger(WX - 60, SILL + 6, face=-1, scale=1.2, tilt=-6), 2952)
    figs(c, agent(1060, AGENT_Y, face=1, scale=0.86, legs=(14, -12), sh=-8, el=16, pencil_deg=200), 2953)
    bal(c, ["Much obliged!"], 86, (930, 150), (330, 440), 2954)


def st6(c):   # E4 at the cupboard; the door opened, the key on its hook: 4:11
    clock_hands(c, 4, 11, 2961); door_open(c, 2962)
    figs(c, agent(1262, AGENT_Y, face=1, scale=0.86, legs=(4, -4), sh=-4, el=12, pencil_deg=200), 2963)


def st7(c):   # E5 the forgetting: pencil to his chin: 4:11
    clock_hands(c, 4, 11, 2961); door_open(c, 2962)
    a = p7.agent2()
    figs(c, a, 2973)
    fp = p7.face_points(a)
    bal(c, ["Well, here I am...", "and what for?"], 86, (1560, 200), (fp["nose"][0] + 4, fp["lip_lo"][1] + 11), 2974,
        ctrl=(1440, 448))


def st8(c):   # E5 held: still there at 4:15, the key on its hook, the SERVICE door shut
    clock_hands(c, 4, 15, 2981); door_open(c, 2962)
    figs(c, p7.agent2(), 2973)


STATES = [st1, st2, st3, st4, st5, st6, st7, st8]
GX, GY = 30, 28
CWp = (1980 - GX) // 2
CHp = int(round(CWp * PH / PW))
BOXES = []
for r in range(4):
    for col in range(2):
        x0 = 110 + col * (CWp + GX)
        y0 = 110 + r * (CHp + GY)
        BOXES.append((x0, y0, x0 + CWp, y0 + CHp))
LAID = []


def panel(k, show=True):
    c = background()
    LAID.append(hashlib.sha256(plate().tobytes()).hexdigest())
    if show:
        STATES[k](c)
    else:
        clock_hands(c, 4, 9, 2921); door_closed(c, 2922)
    small = cv2.resize(c, (CWp, CHp), interpolation=cv2.INTER_AREA)
    # print onto the sheet: the panel's white is the sheet's paper (multiply)
    return small


def build(upto=8):
    page = SHEET.copy()
    for k, b in enumerate(BOXES):
        x0, y0, x1, y1 = b
        p = panel(k, k < upto)
        page[y0:y1, x0:x1] = page[y0:y1, x0:x1] * (p / 255.0)
    frame_border(page, BOXES, w=10, seed=2990)
    return page


if __name__ == "__main__":
    page = build()
    img, size = save_page(page, N, PID, TITLE)
    print("jpeg bytes", size, "panel", CWp, CHp, "bottom", BOXES[-1][3], "plate hashes", len(set(LAID)))
    if len(sys.argv) > 1 and sys.argv[1] == "beats":
        frames = []
        for u in (0, 2, 4, 6, 7, 8):
            p = np.clip(np.round(build(u)), 0, 255).astype(np.uint8)
            pen99.folio(p, N, TITLE)
            frames.append(np.asarray(Image.fromarray(p).resize((960, 1242), Image.LANCZOS)))
        save_beats(N, frames)

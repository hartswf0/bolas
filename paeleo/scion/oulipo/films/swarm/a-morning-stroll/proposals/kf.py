"""Keyframes for a-morning-stroll, round of proposals (deterministic).

kf-1  Rizzuto Stoop   foraged 1959 photograph + articulated cutout rooster (1870s stereo card)
                      + foraged OWI figure turned into the watcher's cast shadow.
kf-2  Pen Number      handmade pen-line drawing (procedural wobbling strokes, boiling line),
                      drawn onomatopoeia as kinetic type.
kf-3  Lace Door       handmade Reiniger-style articulated silhouette theatre on backlit paper,
                      lace railing cut from a vine motif; the 2059 door opens as a slot of light.

Run: python3 kf.py   (reads ../../../../films/sources/a-morning-stroll/, writes kf-*.png, board.jpg)
"""
import math
import os
import random

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUL = os.path.abspath(os.path.join(HERE, "../../../.."))
SRC = os.path.join(OUL, "films/sources/a-morning-stroll")
REF = os.path.join(OUL, "assets/references/orchard3.webp")
W, H = 1280, 720
TREAD_Y, ROO_X = 496, 940
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(p, s):
    return ImageFont.truetype(p, s)


# ---------------------------------------------------------------- shared finish
def grain_vignette(img, amount=14, vig=0.55, seed=1):
    a = np.asarray(img.convert("L"), dtype=np.float32)
    rng = np.random.default_rng(seed)
    g = rng.normal(0, amount, a.shape).astype(np.float32)
    g = cv2.GaussianBlur(g, (0, 0), 0.8)
    yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    r = np.sqrt(((xx - a.shape[1] / 2) / (a.shape[1] / 2)) ** 2 + ((yy - a.shape[0] / 2) / (a.shape[0] / 2)) ** 2)
    v = 1 - vig * np.clip(r - 0.45, 0, 1) ** 1.6
    out = np.clip((a + g) * v, 0, 255).astype(np.uint8)
    return Image.fromarray(out).convert("RGB")


def grabcut(img_rgb, rect, fg_rects=(), bg_rects=(), iters=6):
    a = np.asarray(img_rgb)[:, :, ::-1].copy()
    mask = np.zeros(a.shape[:2], np.uint8)
    x0, y0, x1, y1 = rect
    mask[:] = cv2.GC_BGD
    mask[y0:y1, x0:x1] = cv2.GC_PR_FGD
    for (a0, b0, a1, b1) in fg_rects:
        mask[b0:b1, a0:a1] = cv2.GC_FGD
    for (a0, b0, a1, b1) in bg_rects:
        mask[b0:b1, a0:a1] = cv2.GC_BGD
    bgd = np.zeros((1, 65), np.float64)
    fgd = np.zeros((1, 65), np.float64)
    cv2.grabCut(a, mask, None, bgd, fgd, iters, cv2.GC_INIT_WITH_MASK)
    m = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    # keep largest component
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    if n > 1:
        k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
        m = np.where(lab == k, 255, 0).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    return m


# ================================================================ KF-1
def kf1():
    plate = Image.open(os.path.join(SRC, "r2/70651v.jpg")).convert("L")
    # interior of the print; the top of the stoop with the door, 16:9 band
    x0, x1 = 62, 785
    bw = x1 - x0
    bh = int(bw * 9 / 16)
    y0 = 120
    band = plate.crop((x0, y0, x1, y0 + bh)).resize((W, H), Image.LANCZOS)
    s = W / bw  # 1.77
    # tonal match to reference: lift whites, deepen blacks (b/w print, high key)
    a = np.asarray(band, np.float32)
    a = np.clip((a - 40) * 1.25, 0, 255)
    base = Image.fromarray(a.astype(np.uint8)).convert("RGBA")

    # ---- rooster: scissor-cut outline (hand-placed points on the 1870s stereo card, left half),
    # refined by GrabCut in a narrow band around the cut (#29), then split into pinned pieces.
    card = Image.open(os.path.join(SRC, "r2/1s08734v.jpg")).convert("RGB")
    cut2x = [(40,120),(70,100),(105,110),(125,150),(200,175),(250,160),(290,110),(310,75),(335,55),
             (355,48),(370,70),(378,92),(355,100),(345,120),(348,160),(340,220),(320,260),(290,280),
             (270,300),(260,340),(245,380),(235,420),(245,445),(275,465),(285,475),(230,474),(210,445),
             (200,405),(185,385),(172,405),(175,440),(185,462),(210,476),(150,478),(145,465),(160,440),
             (150,400),(140,372),(110,330),(95,290),(75,250),(60,210),(45,180),(40,150)]
    poly = np.array([(190 + x / 2, 150 + y / 2) for x, y in cut2x], np.int32)
    cw_, ch_ = card.size
    m0 = np.zeros((ch_, cw_), np.uint8)
    cv2.fillPoly(m0, [poly], 255)
    gm = np.full(m0.shape, cv2.GC_BGD, np.uint8)
    gm[cv2.dilate(m0, np.ones((7, 7), np.uint8)) > 0] = cv2.GC_PR_BGD
    gm[m0 > 0] = cv2.GC_PR_FGD
    gm[cv2.erode(m0, np.ones((7, 7), np.uint8)) > 0] = cv2.GC_FGD
    bgd = np.zeros((1, 65), np.float64); fgd = np.zeros((1, 65), np.float64)
    cv2.grabCut(np.asarray(card)[:, :, ::-1].copy(), gm, None, bgd, fgd, 4, cv2.GC_INIT_WITH_MASK)
    m = np.where((gm == cv2.GC_FGD) | (gm == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    m = cv2.GaussianBlur(m, (0, 0), 0.6)
    rgba = np.dstack([np.asarray(card), m])
    ys, xs = np.where(m > 20)
    bx0, by0, bx1, by1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    roo = Image.fromarray(rgba[by0:by1, bx0:bx1]).convert("RGBA")
    roo = roo.resize((roo.size[0] * 2, roo.size[1] * 2), Image.LANCZOS)
    # albumen sepia -> neutral grey, body pushed toward the reference's white
    r, g, b, al = roo.split()
    la = np.asarray(Image.merge("RGB", (r, g, b)).convert("L"), np.float32)
    la = np.clip((la - 60) * 1.9 + 25, 0, 255).astype(np.uint8)
    roo = Image.merge("RGBA", (*[Image.fromarray(la)] * 3, al))
    rw, rh = roo.size
    yy, xx = np.mgrid[0:rh, 0:rw]
    A = np.asarray(roo).copy()
    head_mask = (xx > rw * 0.66) & (yy < rh * 0.30)
    legs_mask = (yy > rh * 0.74)
    body = A.copy(); body[head_mask | legs_mask, 3] = 0
    head = A.copy(); head[~head_mask, 3] = 0
    legs = A.copy(); legs[~legs_mask, 3] = 0
    body, head, legs = (Image.fromarray(p) for p in (body, head, legs))
    # knock pose: the head piece swings forward-down about the neck pin (beak strike on the door)
    pin_neck = (int(rw * 0.70), int(rh * 0.29))
    head_r = head.rotate(-22, center=pin_neck, resample=Image.BICUBIC, translate=(6, 2))
    puppet = Image.new("RGBA", roo.size, (0, 0, 0, 0))
    puppet.alpha_composite(legs)
    puppet.alpha_composite(body)
    puppet.alpha_composite(head_r)
    pd = ImageDraw.Draw(puppet)
    for (px, py) in [pin_neck, (int(rw * 0.52), int(rh * 0.74))]:
        pd.ellipse((px - 4, py - 4, px + 4, py + 4), fill=(150, 150, 150, 255), outline=(30, 30, 30, 255))
    sc = 0.48
    puppet = puppet.resize((int(rw * sc), int(rh * sc)), Image.LANCZOS)

    # ---- watcher: OWI woman, GrabCut, flattened to a cast shadow sheared across the treads
    owi = Image.open(os.path.join(SRC, "2017861981.jpg")).convert("RGB")
    wm = grabcut(owi, (405, 378, 530, 725), fg_rects=[(440, 420, 500, 600), (458, 640, 468, 700), (474, 640, 484, 700)])
    ys, xs = np.where(wm > 0)
    wm = wm[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    sh = Image.fromarray(wm).resize((int(wm.shape[1] * 2.5), int(wm.shape[0] * 2.5)), Image.LANCZOS)
    sw, shh = sh.size
    # shear: the low morning sun from behind-left lays the figure up the stairs
    M = np.float32([[1, 0.55, 0], [0, 0.72, 0]])
    shn = cv2.warpAffine(np.asarray(sh), M, (int(sw + shh * 0.55) + 4, int(shh * 0.72) + 4))
    # the shadow breaks over each riser: rows shift by a sawtooth with the tread period
    per = 64
    for yy_ in range(shn.shape[0]):
        sh_off = int(10 * ((yy_ % per) / per))
        shn[yy_] = np.roll(shn[yy_], -sh_off)
    shn = cv2.flip(shn, 1)  # mirrored: feet bottom-left (off frame), head thrown up the stoop
    shn = cv2.GaussianBlur(shn, (0, 0), 2.2)
    shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    alpha = Image.fromarray((shn * 0.72).astype(np.uint8))
    blk = Image.new("RGBA", alpha.size, (8, 8, 8, 255))
    blk.putalpha(alpha)
    ox, oy = 150, H - alpha.size[1] + 190
    blk = blk.crop((0, 0, min(blk.size[0], W - ox), min(blk.size[1], H - oy)))
    shadow.alpha_composite(blk, (ox, oy))

    frame = base.copy()
    frame.alpha_composite(shadow)
    # rooster on the top tread, under the door (door panels in plate ~ x 575..700 src)
    tread_y = TREAD_Y
    px = ROO_X
    py = tread_y - puppet.size[1] + 18
    # contact shadow
    cs = Image.new("L", (puppet.size[0], 24), 0)
    ImageDraw.Draw(cs).ellipse((10, 4, puppet.size[0] - 30, 20), fill=150)
    cs = cs.filter(ImageFilter.GaussianBlur(4))
    csl = Image.new("RGBA", cs.size, (0, 0, 0, 255)); csl.putalpha(cs)
    frame.alpha_composite(csl, (px, py + puppet.size[1] - 14))
    frame.alpha_composite(puppet, (px, py))
    # occlusion: the near railing balusters in the plate pass in front of the rooster
    # (#45): re-matte bright baluster strokes from the plate over the puppet.
    plate_np = np.asarray(base.convert("L"), np.float32)
    region = np.zeros_like(plate_np)
    rx0, ry0 = px, py
    rx1, ry1 = px + puppet.size[0], py + puppet.size[1]
    sub = plate_np[ry0:ry1, rx0:rx1]
    # thin vertical bright structures = baluster iron
    vk = cv2.morphologyEx(sub.astype(np.uint8), cv2.MORPH_TOPHAT, cv2.getStructuringElement(cv2.MORPH_RECT, (11, 1)))
    occ = np.where(vk > 55, 255, 0).astype(np.uint8)
    occ = cv2.morphologyEx(occ, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25)))
    region[ry0:ry1, rx0:rx1] = occ
    occl = Image.fromarray(region.astype(np.uint8))
    front = base.copy(); front.putalpha(occl)
    frame.alpha_composite(front)

    out = grain_vignette(frame.convert("RGB"), amount=10, vig=0.65, seed=11)
    d = ImageDraw.Draw(out)
    d.text((34, H - 52), "1959", font=font(MONO, 26), fill=(235, 235, 235))
    out.save(os.path.join(HERE, "kf-1.png"))


# ================================================================ KF-2
class Pen:
    """Wobbling ink line, drawn at 2x and reduced (handmade pen texture, seeded = boil)."""

    def __init__(self, draw, seed, scale=2):
        self.d = draw
        self.r = random.Random(seed)
        self.k = scale

    def line(self, pts, w=3.0, wob=1.4, ink=(14, 14, 14)):
        k = self.k
        dense = []
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            L = math.hypot(x1 - x0, y1 - y0)
            n = max(2, int(L / 6))
            for i in range(n):
                t = i / n
                dense.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
        dense.append(pts[-1])
        ph = self.r.random() * 6.28
        fr = 0.02 + self.r.random() * 0.02
        out = []
        for i, (x, y) in enumerate(dense):
            o = wob * (math.sin(i * fr * 6 + ph) * 0.7 + (self.r.random() - 0.5) * 0.6)
            out.append(((x + o) * k, (y + o * 0.8) * k))
        for i in range(len(out) - 1):
            ww = w * (0.85 + 0.3 * math.sin(i * 0.15 + ph)) * k
            self.d.line([out[i], out[i + 1]], fill=ink, width=max(1, int(ww)))
            self.d.ellipse((out[i][0] - ww / 2, out[i][1] - ww / 2, out[i][0] + ww / 2, out[i][1] + ww / 2), fill=ink)

    def rect(self, x0, y0, x1, y1, **kw):
        self.line([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], **kw)

    def poly_fill(self, pts, fill):
        self.d.polygon([(x * self.k, y * self.k) for x, y in pts], fill=fill)

    def circle_arc(self, cx, cy, r, a0, a1, **kw):
        n = max(6, int(abs(a1 - a0) * r / 8))
        self.line([(cx + r * math.cos(a0 + (a1 - a0) * i / n), cy + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)], **kw)


def scallop_tree(p, cx, cy, R, seed):
    rr = random.Random(seed)
    n = 9
    pts = []
    for i in range(n):
        a = i / n * 2 * math.pi
        r = R * (0.85 + rr.random() * 0.25)
        pts.append((cx + r * math.cos(a), cy + r * 0.8 * math.sin(a), r))
    for i in range(n):
        x, y, r = pts[i]
        a = math.atan2(y - cy, x - cx)
        p.circle_arc(x - (r * 0.25) * math.cos(a), y - (r * 0.25) * math.sin(a), R * 0.42, a - 1.5, a + 1.5, w=2.6)


def kf2():
    k = 2
    PAPER = (240, 238, 232)
    INK = (14, 14, 14)
    img = Image.new("RGB", (W * k, H * k), PAPER)
    d = ImageDraw.Draw(img)
    p = Pen(d, seed=7, scale=k)
    rr = random.Random(9)
    HOR = 520  # sidewalk line at the building base
    # --- road and kerb washes
    p.poly_fill([(0, 585), (W, 572), (W, H), (0, H)], (178, 177, 173))
    p.line([(0, 585), (W, 572)], w=3)
    p.poly_fill([(0, 596), (W, 583), (W, 590), (0, 604)], (60, 60, 58))
    # --- facade (brownstone), x 430..1280, brick coursing as broken pen dashes
    FX = 430
    p.poly_fill([(FX, 0), (W, 0), (W, HOR), (FX, HOR + 4)], (226, 224, 217))
    for y in range(18, HOR - 8, 16):
        x = FX + rr.randint(0, 30)
        while x < W - 10:
            L = rr.randint(26, 70)
            if rr.random() < 0.55:
                p.line([(x, y), (min(W - 4, x + L), y + rr.uniform(-0.6, 0.6))], w=1.1, wob=0.5, ink=(90, 88, 84))
            x += L + rr.randint(16, 50)
    p.line([(FX, 0), (FX, HOR + 4)], w=3.4)
    # cornice band
    p.poly_fill([(FX, 0), (W, 0), (W, 26), (FX, 26)], (40, 40, 40))
    for x in range(FX + 8, W, 26):
        p.line([(x, 26), (x, 40)], w=3)
    # windows: lintels, black glass with two pale glints, sills
    for (wx, wy) in [(1000, 80), (1150, 80), (1000, 300), (1150, 300)]:
        p.poly_fill([(wx, wy), (wx + 96, wy), (wx + 96, wy + 150), (wx, wy + 150)], (22, 22, 22))
        p.rect(wx, wy, wx + 96, wy + 150, w=3)
        p.line([(wx + 48, wy), (wx + 48, wy + 150)], w=3, ink=(236, 236, 230))
        p.line([(wx, wy + 72), (wx + 96, wy + 72)], w=3, ink=(236, 236, 230))
        p.line([(wx + 10, wy + 12), (wx + 22, wy + 40)], w=2, ink=(210, 210, 205))
        p.poly_fill([(wx - 12, wy - 22), (wx + 108, wy - 22), (wx + 104, wy - 8), (wx - 8, wy - 8)], INK)
        p.line([(wx - 8, wy + 156), (wx + 104, wy + 156)], w=5)
    # fire escape: platforms, balusters, the diagonal ladder
    for yy in (230, 452):
        p.line([(960, yy), (1280, yy)], w=4)
        p.line([(960, yy - 44), (1280, yy - 44)], w=2.4)
        for xx in range(964, 1280, 14):
            p.line([(xx, yy - 44), (xx, yy)], w=1.4)
    p.line([(1240, 230), (1100, 452)], w=3)
    p.line([(1262, 230), (1122, 452)], w=3)
    for i in range(1, 9):
        t = i / 9
        p.line([(1240 - 140 * t, 230 + 222 * t), (1262 - 140 * t, 230 + 222 * t)], w=1.8)
    # door at the top of the stoop: deep black, panel highlights, transom fan
    dx0, dy0, dx1, dy1 = 760, 168, 872, 352
    p.poly_fill([(dx0 - 20, dy0 - 30), (dx1 + 20, dy0 - 30), (dx1 + 20, dy1), (dx0 - 20, dy1)], (205, 203, 196))
    p.poly_fill([(dx0, dy0), (dx1, dy0), (dx1, dy1), (dx0, dy1)], (18, 18, 18))
    p.rect(dx0, dy0, dx1, dy1, w=3.6)
    p.rect(dx0 - 20, dy0 - 30, dx1 + 20, dy1, w=3)
    for (a0, b0, a1, b1) in [(772, 184, 808, 262), (824, 184, 860, 262), (772, 278, 808, 340), (824, 278, 860, 340)]:
        p.rect(a0, b0, a1, b1, w=1.8, ink=(215, 215, 210))
    p.d.ellipse((849 * k, 262 * k, 857 * k, 270 * k), fill=(230, 230, 225))  # knob
    for i in range(7):
        a = math.pi + i * math.pi / 6
        p.line([(816, dy0 - 32), (816 + 54 * math.cos(a), dy0 - 32 + 40 * math.sin(a))], w=1.6)
    p.circle_arc(816, dy0 - 32, 56, math.pi, 2 * math.pi, w=3)
    # house number on the door frame
    d.text(((dx1 + 2) * k, (dy0 + 60) * k), "17", font=font(SERIF_B, 14 * k), fill=INK)
    # stoop in side elevation, rising left to right: seven steps
    steps = 7
    sx0, sy0 = 470, HOR + 2
    tx, ty = dx0 - 20, dy1
    run = (tx - sx0) / steps
    rise = (sy0 - ty) / steps
    prof = [(sx0, sy0)]
    for i in range(steps):
        x = sx0 + i * run
        y = sy0 - (i + 1) * rise
        prof += [(x, y), (x + run, y)]
    prof += [(tx + 132, ty), (tx + 132, sy0)]
    p.poly_fill(prof + [(sx0, sy0)], (250, 249, 245))
    p.line(prof, w=3.2)
    # stone texture: stipple on each riser
    for i in range(steps):
        x = sx0 + i * run
        y = sy0 - (i + 1) * rise
        for _ in range(14):
            px_, py_ = x + rr.uniform(2, run - 2), y + rr.uniform(3, rise - 2)
            p.d.ellipse((px_ * k, py_ * k, px_ * k + 2, py_ * k + 2), fill=(120, 120, 116))
    # the black mass under the stoop (areaway) and its iron gate
    p.poly_fill([(tx + 132, ty + 6), (tx + 200, ty + 18), (tx + 200, sy0), (tx + 132, sy0)], INK)
    for xx in range(tx + 140, tx + 200, 10):
        p.line([(xx, ty + 40), (xx, sy0)], w=1.6, ink=(200, 200, 195))
    # railing: handrail, a baluster on every step, newel ball
    p.line([(sx0 - 4, sy0 - 110), (tx + 2, ty - 104), (tx + 2, ty - 6)], w=3.6)
    for i in range(steps + 1):
        bx = sx0 - 4 + i * run
        p.line([(bx, sy0 - 110 - i * rise * 0.995), (bx, sy0 - i * rise)], w=2.2)
        if i < steps:
            for j in (1, 2):
                xb = bx + run * j / 3
                p.line([(xb, sy0 - 110 - (i + j / 3) * rise), (xb, sy0 - (i + 1) * rise)], w=1.3)
    p.d.ellipse(((sx0 - 14) * k, (sy0 - 132) * k, (sx0 + 6) * k, (sy0 - 112) * k), fill=INK)
    # far side of the street, seen past the tree: a thin-line tenement row
    for (bx0, bx1, top) in [(0, 150, 120), (150, 300, 70), (300, 425, 140)]:
        p.line([(bx0, top), (bx1, top)], w=2.2)
        p.line([(bx1, top), (bx1, 470)], w=1.8)
        for wy in range(top + 24, 440, 56):
            for wx in range(bx0 + 14, bx1 - 24, 38):
                p.rect(wx, wy, wx + 18, wy + 30, w=1.2, wob=0.5, ink=(80, 80, 78))
    p.line([(0, 470), (425, 470)], w=2)
    # street tree (scalloped crown) and a lamp post on the sidewalk, left
    p.line([(230, 560), (236, 270)], w=4)
    p.line([(246, 560), (244, 270)], w=3)
    p.line([(238, 330), (200, 280)], w=2.4)
    crown = [(236 + 140 * math.cos(i / 40 * 6.283), 190 + 116 * math.sin(i / 40 * 6.283)) for i in range(41)]
    p.poly_fill(crown, PAPER)
    scallop_tree(p, 236, 190, 130, seed=3)
    p.line([(384, 560), (384, 120)], w=4.2)
    p.poly_fill([(370, 120), (398, 120), (392, 96), (376, 96)], INK)
    # parked car, outline only, cut by the frame at left, on the road
    car = [(230, 650), (230, 600), (280, 596), (310, 566), (410, 562), (450, 594), (540, 600), (546, 650)]
    p.poly_fill(car, (236, 235, 230))
    p.line(car, w=3)
    p.line([(320, 572), (330, 594), (430, 594), (408, 570)], w=2)
    for cx_ in (290, 480):
        p.d.ellipse(((cx_ - 26) * k, 628 * k, (cx_ + 26) * k, 680 * k), fill=INK)
    # --- the chicken on the landing, beak to the door: pose 5 of the 8-drawing knock cycle
    cx, cy = 708, 318
    body = []
    for i in range(41):
        a = i / 40 * 2 * math.pi
        rx = 40 if math.cos(a) > 0 else 46
        body.append((cx + rx * math.cos(a), cy + 30 * math.sin(a) - (8 if math.sin(a) < 0 and math.cos(a) < 0 else 0)))
    p.poly_fill(body, (253, 253, 251))
    p.line(body, w=3.2)
    # tail fan
    for a in (-2.2, -2.5, -2.8):
        p.line([(cx - 34, cy - 10), (cx - 34 + 30 * math.cos(a), cy - 10 + 30 * math.sin(a))], w=2.6)
    # neck stretched toward the door
    p.poly_fill([(cx + 22, cy - 22), (cx + 44, cy - 58), (cx + 58, cy - 56), (cx + 40, cy - 10)], (253, 253, 251))
    p.line([(cx + 22, cy - 22), (cx + 44, cy - 58)], w=3)
    p.line([(cx + 40, cy - 10), (cx + 58, cy - 54)], w=3)
    p.d.ellipse(((cx + 38) * k, (cy - 76) * k, (cx + 62) * k, (cy - 52) * k), fill=(253, 253, 251))
    p.circle_arc(cx + 50, cy - 64, 12, -2.6, 2.2, w=2.8)
    p.poly_fill([(cx + 60, cy - 70), (cx + 76, cy - 64), (cx + 60, cy - 60)], INK)  # beak on the door
    p.poly_fill([(cx + 40, cy - 74), (cx + 44, cy - 86), (cx + 49, cy - 76), (cx + 53, cy - 88), (cx + 57, cy - 74)], INK)  # comb
    p.d.ellipse(((cx + 52) * k, (cy - 68) * k, (cx + 56) * k, (cy - 64) * k), fill=INK)
    p.line([(cx - 2, cy + 28), (cx - 4, cy + 34)], w=2.8)
    p.line([(cx + 14, cy + 28), (cx + 16, cy + 34)], w=2.8)
    d.text(((cx - 12) * k, (cy - 16) * k), "1", font=font(SANS_B, 28 * k), fill=INK)
    # strike ticks at the door, white on black
    for (a, L) in [(-1.0, 24), (-0.45, 30), (0.15, 24), (0.7, 18)]:
        x0, y0 = dx0 + 6, cy - 65
        p.line([(x0 + 8 * math.cos(a), y0 + 8 * math.sin(a)), (x0 + L * math.cos(a), y0 + L * math.sin(a))], w=2.4, wob=0.4, ink=(240, 240, 236))
    # --- the watcher: man in the foreground, three-quarter back view, cut at the hip, head turned to the stoop
    hx, hy = 110, 420
    coat = [(hx - 92, H + 10), (hx - 84, hy + 120), (hx - 58, hy + 64), (hx - 18, hy + 52), (hx + 26, hy + 52), (hx + 62, hy + 68), (hx + 88, hy + 130), (hx + 96, H + 10)]
    p.poly_fill(coat, (24, 24, 24))
    p.line(coat, w=3)
    p.line([(hx + 4, hy + 56), (hx + 14, hy + 160)], w=2, ink=(120, 120, 118))  # coat seam
    p.poly_fill([(hx - 16, hy + 54), (hx + 22, hy + 54), (hx + 18, hy + 32), (hx - 12, hy + 32)], (250, 249, 245))  # neck
    head = [(hx + 2 + 34 * math.cos(i / 30 * 6.283), hy + 4 + 38 * math.sin(i / 30 * 6.283)) for i in range(31)]
    p.poly_fill(head, (250, 249, 245))
    p.line(head, w=3)
    p.poly_fill([(hx - 54, hy - 18), (hx + 60, hy - 24), (hx + 50, hy - 36), (hx + 34, hy - 78), (hx - 30, hy - 74), (hx - 42, hy - 30)], INK)  # hat
    p.line([(hx - 40, hy - 36), (hx + 46, hy - 42)], w=2, ink=(170, 170, 166))  # hat band
    p.line([(hx + 26, hy + 2), (hx + 34, hy)], w=3.2)  # eye, looking right
    p.line([(hx + 36, hy + 6), (hx + 42, hy + 16), (hx + 34, hy + 18)], w=2.4)  # nose
    p.line([(hx - 34, hy + 4), (hx - 30, hy + 18)], w=2)  # ear
    # newspaper under the arm
    p.poly_fill([(hx + 70, hy + 150), (hx + 150, hy + 136), (hx + 156, hy + 176), (hx + 76, hy + 190)], (232, 231, 226))
    p.line([(hx + 70, hy + 150), (hx + 150, hy + 136), (hx + 156, hy + 176), (hx + 76, hy + 190), (hx + 70, hy + 150)], w=2.4)
    for j in range(4):
        p.line([(hx + 84, hy + 156 + j * 7), (hx + 140, hy + 146 + j * 7)], w=1, wob=0.3, ink=(110, 110, 106))
    # sidewalk marks, a puddle ring at the stoop foot
    p.circle_arc(560, 548, 46, 0.2, 2.9, w=2.2)
    p.line([(600, 556), (640, 555)], w=2)
    p.line([(900, 548), (980, 546)], w=2)
    img = img.resize((W, H), Image.LANCZOS)
    # kinetic type: TOK TOK, each glyph cut and rotated by hand (key pose of the second knock)
    t = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rr2 = random.Random(5)
    x = 540
    for i, ch in enumerate("TOK TOK"):
        if ch == " ":
            x += 22
            continue
        sz = 44 + (8 if i >= 4 else 0)
        g = Image.new("RGBA", (80, 90), (0, 0, 0, 0))
        ImageDraw.Draw(g).text((10, 6), ch, font=font(SERIF_B, sz), fill=(14, 14, 14, 255))
        g = g.rotate(rr2.uniform(-16, 16), resample=Image.BICUBIC)
        t.alpha_composite(g, (x, 96 - (i % 3) * 6 - (14 if i >= 4 else 0)))
        x += int(sz * 0.72)
    img = img.convert("RGBA"); img.alpha_composite(t)
    out = grain_vignette(img.convert("RGB"), amount=9, vig=0.5, seed=22)
    ImageDraw.Draw(out).text((W - 110, H - 52), "1959", font=font(MONO, 26), fill=(250, 250, 250))
    out.save(os.path.join(HERE, "kf-2.png"))


# ================================================================ KF-3
def kf3():
    """Silhouette theatre on a light table: black card, grey tissue layers, backlit paper."""
    yy, xx = np.mgrid[0:H, 0:W]
    rng = np.random.default_rng(3)
    fib = cv2.GaussianBlur(rng.normal(0, 7, (H, W)).astype(np.float32), (0, 0), 1.1)
    fib += cv2.resize(rng.normal(0, 5, (H // 10, W // 10)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
    # value map: start with backlit sky, graded from the lamp-bright doorway
    sky = 236 - 70 * np.clip(np.sqrt(((xx - 820) / 1100) ** 2 + ((yy - 330) / 700) ** 2), 0, 1)
    val = sky.copy()

    def layer(mask, v):
        nonlocal val
        val = np.where(mask > 0, v, val)

    def poly_mask(pts_list):
        m = np.zeros((H, W), np.uint8)
        for pts in pts_list:
            cv2.fillPoly(m, [np.array(pts, np.int32)], 255)
        return m

    # far row of houses: one tissue layer (pale grey), roofline with chimneys
    far = poly_mask([[(0, 330), (60, 330), (60, 300), (74, 300), (74, 330), (190, 330), (190, 280), (330, 280), (330, 260), (344, 260), (344, 280), (470, 280), (470, 600), (0, 600)]])
    layer(far, 196)
    farwin = np.zeros((H, W), np.uint8)
    for x0 in range(18, 450, 46):
        for y0 in (350, 420, 490):
            if y0 < 300 and x0 > 190:
                continue
            cv2.rectangle(farwin, (x0, y0), (x0 + 20, y0 + 36), 255, -1)
    layer(farwin & far, 214)
    # the house: two tissue layers deep (mid grey), cornice and pilasters in black card
    house = poly_mask([[(600, 0), (W, 0), (W, 600), (600, 600)]])
    layer(house, 128)
    sil = np.zeros((H, W), np.uint8)  # black card
    cv2.rectangle(sil, (600, 0), (W, 34), 255, -1)
    for x0 in range(610, W, 30):
        cv2.rectangle(sil, (x0, 34), (x0 + 12, 50), 255, -1)
    cv2.rectangle(sil, (600, 0), (618, 600), 255, -1)
    # windows cut through to the light, with black glazing bars and lace lambrequins
    for wx in (1000, 1140):
        for wy in (110, 330):
            cv2.rectangle(val_mask := np.zeros((H, W), np.uint8), (wx, wy), (wx + 90, wy + 150), 255, -1)
            layer(val_mask, 226)
            cv2.rectangle(sil, (wx - 8, wy - 18), (wx + 98, wy - 4), 255, -1)
            cv2.rectangle(sil, (wx + 42, wy), (wx + 48, wy + 150), 255, -1)
            cv2.rectangle(sil, (wx, wy + 72), (wx + 90, wy + 78), 255, -1)
            for i in range(6):
                cv2.ellipse(sil, (wx + 8 + i * 15, wy), (8, 10), 0, 0, 180, 255, 3)
    # fire escape in black lace across the windows
    for fy in (280, 500):
        cv2.rectangle(sil, (960, fy), (W, fy + 6), 255, -1)
        cv2.rectangle(sil, (960, fy - 46), (W, fy - 42), 255, -1)
        for x0 in range(964, W, 16):
            cv2.line(sil, (x0, fy - 44), (x0, fy), 255, 2)
            cv2.circle(sil, (x0 + 8, fy - 22), 5, 255, 1)
    cv2.line(sil, (1250, 280), (1110, 500), 255, 4)
    cv2.line(sil, (1272, 280), (1132, 500), 255, 4)
    # doorway: the 2059 door has slid aside on the second knock; the hall light is the brightest paper
    door = (744, 226, 904, 470)
    dm = np.zeros((H, W), np.uint8)
    cv2.rectangle(dm, door[:2], door[2:], 255, -1)
    layer(dm, 255)
    # sliding leaf, half retracted into the wall (black card with a slot of sensor dots)
    cv2.rectangle(sil, (door[2] - 22, door[1]), (door[2] + 8, door[3]), 255, -1)
    cv2.rectangle(sil, (door[0] - 18, door[1] - 26), (door[2] + 18, door[1] - 8), 255, -1)
    cv2.rectangle(sil, (door[0] - 18, door[1] - 8), (door[0] - 6, door[3]), 255, -1)
    sensor = np.zeros((H, W), np.uint8)
    for i in range(10):
        cv2.circle(sensor, (door[0] + 10 + i * 15, door[1] - 17), 3, 255, -1)
    # stoop: black card stepped profile; the lit wedge from the door falls on its treads (tissue overlay)
    steps = 6
    sx0, sy0, tx, ty = 470, 600, door[0] - 18, door[3]
    run = (tx - sx0) / steps
    rise = (sy0 - ty) / steps
    prof = [(sx0, sy0)]
    for i in range(steps):
        x = sx0 + i * run
        y = sy0 - (i + 1) * rise
        prof += [(x, y), (x + run, y)]
    prof += [(door[2] + 40, ty), (door[2] + 40, sy0)]
    cv2.fillPoly(sil, [np.array(prof, np.int32)], 255)
    # ground
    cv2.rectangle(sil, (0, 600), (W, H), 255, -1)
    # lace railing: handrail, balusters and cut scrolls (positive black curls)
    hr0 = (sx0 - 2, sy0 - 120)
    hr1 = (tx + 6, ty - 116)
    cv2.line(sil, hr0, hr1, 255, 7)
    cv2.circle(sil, (hr0[0], hr0[1] - 6), 13, 255, -1)
    cv2.line(sil, (hr0[0], hr0[1]), (hr0[0], sy0), 255, 6)
    for i in range(steps):
        bx = int(sx0 + i * run + run * 0.5)
        ytop = int(hr0[1] + (hr1[1] - hr0[1]) * (bx - hr0[0]) / (hr1[0] - hr0[0]))
        ybot = int(sy0 - (i + 1) * rise)
        cv2.line(sil, (bx, ytop), (bx, ybot), 255, 3)
        for j, c in enumerate(range(ytop + 22, ybot - 14, 30)):
            sgn = 1 if (i + j) % 2 else -1
            cv2.ellipse(sil, (bx + sgn * 12, c), (11, 13), 0, 90 * (1 - sgn), 90 * (1 - sgn) + 270, 255, 2)
            cv2.circle(sil, (bx + sgn * 12, c), 3, 255, -1)
    # lamp post and a scalloped street tree, black card, left
    cv2.rectangle(sil, (380, 230), (388, 600), 255, -1)
    cv2.fillPoly(sil, [np.array([(366, 230), (402, 230), (394, 196), (374, 196)], np.int32)], 255)
    cv2.rectangle(sil, (110, 230), (124, 600), 255, -1)
    cv2.line(sil, (117, 330), (70, 270), 255, 6)
    cv2.line(sil, (117, 300), (160, 250), 255, 5)
    for (cx_, cy_, r_) in [(117, 170, 70), (55, 200, 58), (180, 196, 60), (80, 120, 56), (156, 116, 56), (117, 80, 50), (30, 150, 40), (205, 145, 42)]:
        cv2.circle(sil, (cx_, cy_), r_, 255, -1)
    for (cx_, cy_, r_) in [(80, 180, 8), (140, 140, 7), (170, 205, 9), (100, 100, 6), (50, 230, 7)]:
        cv2.circle(sil, (cx_, cy_), r_, 0, -1)

    # ---- the watcher: a silhouette paused mid-stride, head turned to the door, cup in hand
    wx, wy = 300, 600
    man = [(wx - 34, wy), (wx - 22, wy - 96), (wx - 10, wy - 120), (wx + 6, wy - 96), (wx + 34, wy), (wx + 24, wy), (wx + 2, wy - 80),
           (wx - 14, wy), ]
    cv2.fillPoly(sil, [np.array(man, np.int32)], 255)
    coat = [(wx - 30, wy - 92), (wx - 34, wy - 190), (wx - 20, wy - 236), (wx + 22, wy - 236), (wx + 34, wy - 190), (wx + 36, wy - 100), (wx + 10, wy - 112), (wx - 12, wy - 110)]
    cv2.fillPoly(sil, [np.array(coat, np.int32)], 255)
    cv2.rectangle(sil, (wx - 8, wy - 252), (wx + 10, wy - 234), 255, -1)
    cv2.ellipse(sil, (wx + 2, wy - 270), (20, 24), 0, 0, 360, 255, -1)
    cv2.fillPoly(sil, [np.array([(wx + 18, wy - 276), (wx + 30, wy - 268), (wx + 18, wy - 262)], np.int32)], 255)  # nose
    cv2.fillPoly(sil, [np.array([(wx - 34, wy - 284), (wx + 40, wy - 288), (wx + 30, wy - 296), (wx + 20, wy - 322), (wx - 18, wy - 320), (wx - 26, wy - 294)], np.int32)], 255)
    cv2.fillPoly(sil, [np.array([(wx + 20, wy - 214), (wx + 70, wy - 186), (wx + 66, wy - 176), (wx + 16, wy - 196)], np.int32)], 255)
    cv2.rectangle(sil, (wx + 62, wy - 204), (wx + 78, wy - 178), 255, -1)
    cv2.circle(sil, (wx - 26, wy + 2), 7, 255, -1); cv2.circle(sil, (wx + 30, wy + 2), 7, 255, -1)
    pins = [(wx + 2, wy - 236), (wx - 10, wy - 112), (wx + 22, wy - 208)]

    # ---- the chicken: articulated card puppet stepping over the sill into the hall light
    cx, cy = 806, 432  # body centre, standing on the sill line ty=470
    ch = np.zeros((H, W), np.uint8)
    body = cv2.ellipse2Poly((cx, cy), (36, 24), -12, 0, 360, 10)
    cv2.fillPoly(ch, [body], 255)
    tail = [(cx - 28, cy - 6), (cx - 56, cy - 44), (cx - 46, cy - 18), (cx - 62, cy - 30), (cx - 44, cy + 2), (cx - 30, cy + 12)]
    cv2.fillPoly(ch, [np.array(tail, np.int32)], 255)
    neck = [(cx + 16, cy - 18), (cx + 28, cy - 50), (cx + 42, cy - 52), (cx + 36, cy - 10)]
    cv2.fillPoly(ch, [np.array(neck, np.int32)], 255)
    cv2.circle(ch, (cx + 38, cy - 56), 11, 255, -1)
    comb = [(cx + 30, cy - 64), (cx + 32, cy - 78), (cx + 37, cy - 68), (cx + 41, cy - 80), (cx + 45, cy - 68), (cx + 50, cy - 74), (cx + 48, cy - 60)]
    cv2.fillPoly(ch, [np.array(comb, np.int32)], 255)
    cv2.fillPoly(ch, [np.array([(cx + 47, cy - 60), (cx + 60, cy - 54), (cx + 47, cy - 50)], np.int32)], 255)  # beak
    cv2.ellipse(ch, (cx + 44, cy - 44), (4, 7), 0, 0, 360, 255, -1)  # wattle
    cv2.circle(ch, (cx + 41, cy - 59), 2, 0, -1)  # eye hole
    # legs: planted leg on the sill, lifted leg mid-step over it (thigh/shank pinned)
    cv2.line(ch, (cx - 4, cy + 20), (cx - 8, ty - 2), 255, 4)
    cv2.line(ch, (cx - 8, ty - 2), (cx + 6, ty - 2), 255, 3); cv2.line(ch, (cx - 8, ty - 2), (cx - 18, ty), 255, 3)
    cv2.line(ch, (cx + 12, cy + 18), (cx + 26, cy + 26), 255, 4)
    cv2.line(ch, (cx + 26, cy + 26), (cx + 28, cy + 36), 255, 3)
    cv2.line(ch, (cx + 28, cy + 36), (cx + 40, cy + 34), 255, 2); cv2.line(ch, (cx + 28, cy + 36), (cx + 34, cy + 42), 255, 2)
    sil = np.maximum(sil, ch)
    pins += [(cx + 18, cy - 16), (cx - 4, cy + 18), (cx + 12, cy + 18), (cx + 26, cy + 26), (cx - 26, cy - 4)]

    # ---- composite: black card absorbs, slight translucency at the edges
    card = cv2.GaussianBlur(sil.astype(np.float32) / 255.0, (0, 0), 0.8)
    img = (val + fib) * (1 - card) + 8 * card
    # light spill from the doorway onto the treads: thin tissue laid over the card
    spill = np.zeros((H, W), np.float32)
    cv2.fillPoly(spill, [np.array([(door[0], door[3]), (door[2] - 28, door[3]), (door[2] + 10, 600), (door[0] - 60, 600)], np.int32)], 1.0)
    spill = cv2.GaussianBlur(spill, (0, 0), 9)
    img = img + spill * (card > 0.5) * (1 - (ch > 0)) * 34
    # sensor dots glow
    img = np.where(sensor > 0, 250, img)
    out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert("RGB")
    od = ImageDraw.Draw(out)
    for (px_, py_) in pins:  # split pins catching the light
        od.ellipse((px_ - 2, py_ - 2, px_ + 2, py_ + 2), fill=(105, 105, 105))
    out = grain_vignette(out, amount=6, vig=0.55, seed=33)
    ImageDraw.Draw(out).text((W - 110, H - 52), "2059", font=font(MONO, 26), fill=(210, 210, 210))
    out.save(os.path.join(HERE, "kf-3.png"))


# ================================================================ board
def board():
    names = ["REFERENCE  Orchard, A Morning Stroll (2011), 1959 section",
             "1  RIZZUTO STOOP  foraged 1959 photo + cutout rooster puppet",
             "2  PEN NUMBER  handmade boiling pen line + kinetic type",
             "3  LACE DOOR  articulated silhouette theatre, 2059"]
    ims = [Image.open(REF).convert("RGB")] + [Image.open(os.path.join(HERE, f"kf-{i}.png")).convert("RGB") for i in (1, 2, 3)]
    cw, chh = 960, 540
    lab = 44
    B = Image.new("RGB", (cw * 2 + 30, (chh + lab) * 2 + 30), (20, 20, 20))
    dd = ImageDraw.Draw(B)
    for i, (im, n) in enumerate(zip(ims, names)):
        im = im.resize((cw, int(im.height * cw / im.width)), Image.LANCZOS)
        im = im.crop((0, 0, cw, min(chh, im.height)))
        x = 10 + (i % 2) * (cw + 10)
        y = 10 + (i // 2) * (chh + lab + 10)
        dd.text((x + 4, y + 8), n, font=font(MONO, 22), fill=(240, 240, 240))
        B.paste(im, (x, y + lab))
    B.save(os.path.join(HERE, "board.jpg"), quality=90)


if __name__ == "__main__":
    kf1()
    kf2()
    kf3()
    board()

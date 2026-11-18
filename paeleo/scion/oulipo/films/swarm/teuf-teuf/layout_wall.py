"""LAYOUT-WALL: frame A (wide) and frame B (x2.2 close-up) for teuf-teuf.

FORAGED: films/sources/teuf-teuf/hands_cueva.jpg = "Cueva de las manos - detalle.jpg",
Suzko, CC BY-SA 3.0 (Wikimedia Commons). Decoded with PIL only.
HANDMADE (procedural, here): charcoal bands, ground line, scratched ticks, ghost-outline
generator, dot cluster, engraved ghost animal, white-scratched title.

World space = layout A: 1280x720, ground y 566, x0 330 px = 0 m, 100 px/m.
Everything is built once on a MASTER raster at 2.2 px per world px (2816x1584), so
frame B (x2.2) is an exact 1:1 crop of it and frame A is an area-downsample of it:
both views show the identical wall at the identical tau.

Compositing contract (for the animator / editor): work in LUMINANCE 0..1 on top of
plate_lum(cam), then print through ramp() (the reference's greenish-sepia ramp).
"""
import json
import math
import os
import sys

import numpy as np
import cv2
from PIL import Image, ImageDraw

ROOT = "/home/user/bolas/paeleo/scion/oulipo"
SRC = ROOT + "/films/sources/teuf-teuf/hands_cueva.jpg"
OUT = ROOT + "/films/sources/teuf-teuf/layout"
REF = ROOT + "/assets/references/teuf.webp"

WW, WH = 1280, 720
GROUND = 566.0
X0, PXM = 330.0, 100.0
M = 2.2                                   # master px per world px
MW, MH = int(WW * M), int(WH * M)         # 2816 x 1584
SRC_W, SRC_H = 960, 720
S0 = WW / SRC_W                           # cover scale source -> world (4/3)
SRC_OY = 150.0                            # world y = src_y * S0 - SRC_OY

HP_GAIN = 0.10                            # rock high-pass gain (kf-1 used 0.85; repair 2: 0.25 -> 0.10, a wash)
BROAD_GAIN = 0.12                         # repair 2: low-frequency rock relief 0.55 -> 0.12
KEEP_GUAN = 3                             # repair 2: only the 3 largest guanacos stay solid
FADE_GUAN = 0.06                          # the rest fade below 10 % contrast
PALE_LEVEL = 0.875                        # median wash level on the ramp (-> ~ (223,217,188))

# reference ramp: sampled tones of teuf.webp (darkest ink .. highlight), plan s7
RAMP_L = np.array([0.00, 0.12, 0.33, 0.68, 0.87, 0.94, 1.00], np.float32)
RAMP_C = np.array([[15, 17, 9], [43, 44, 31], [89, 90, 73], [179, 176, 152],
                   [223, 217, 188], [239, 232, 202], [251, 243, 213]], np.float32)

# bands (world px): mean edges, wave terms (amp, period, phase)
TOP_EDGE = (70.0, [(18, 230, 0.6), (7, 71, 2.0), (3, 23, 0.0)])
BOT_EDGE = (614.0, [(10, 270, 1.3), (5, 47, 0.0), (2, 19, 0.4)])
TICKS_M = (0.0, 1.2, 3.0, 8.0)


class Cam:
    """screen = (world - (ox, oy)) * s, output w x h"""
    def __init__(self, s, ox, oy, w=WW, h=WH):
        self.s, self.ox, self.oy, self.w, self.h = s, ox, oy, w, h

    def p(self, x, y):
        return ((x - self.ox) * self.s, (y - self.oy) * self.s)

    def world(self, sx, sy):
        return (sx / self.s + self.ox, sy / self.s + self.oy)

    def as_dict(self):
        return dict(scale=self.s, ox=self.ox, oy=self.oy, w=self.w, h=self.h,
                    affine_world_to_screen=[[self.s, 0, -self.ox * self.s], [0, self.s, -self.oy * self.s]])


CAM_A = Cam(1.0, 0.0, 0.0)
# frame B: x2.2, aimed at the stone's rear edge at rollers tau 2.2 (xb = 230 world px,
# stone mid-height y 486). Centre x would be 230, but the photograph starts at world x 0,
# so the camera is clamped to ox = 0 (centre x 291); the rear edge lands at screen x 506.
STONE_REAR_TAU22 = (230.0, 486.0)
_ox = max(0.0, STONE_REAR_TAU22[0] - WW / 2 / M)
CAM_B = Cam(M, _ox, STONE_REAR_TAU22[1] - WH / 2 / M)


def ramp(l):
    l = np.clip(l, 0, 1)
    out = np.empty(l.shape + (3,), np.float32)
    for c in range(3):
        out[..., c] = np.interp(l, RAMP_L, RAMP_C[:, c])
    return out


def edge_y(x, top):
    mean, terms = TOP_EDGE if top else BOT_EDGE
    y = mean + 0 * x
    for a, p, ph in terms:
        y = y + a * np.sin(x / p + ph)
    return y


# ------------------------------------------------------------- the real rock ---
def rock_maps():
    """source-resolution maps from the photograph: rock lum (toned), red pigment
    density, guanaco density, yellow ochre density, negative-hand interior."""
    a = np.asarray(Image.open(SRC).convert("RGB")).astype(np.float32) / 255.0
    lab = cv2.cvtColor(a, cv2.COLOR_RGB2LAB)
    L, A, B = lab[..., 0], lab[..., 1], lab[..., 2]

    def hp(x, big, small):
        return cv2.GaussianBlur(x, (0, 0), small) - cv2.GaussianBlur(x, (0, 0), big)

    # red ochre (blown spray round the negative stencils, the positive hand, spiral, zigzag)
    Ab = cv2.GaussianBlur(A, (0, 0), 60)
    red = np.clip((cv2.GaussianBlur(A, (0, 0), 1.5) - Ab - 3) / 18.0, 0, 1)
    red = cv2.GaussianBlur(red, (0, 0), 1.6)
    # grey guanacos: less yellow and darker than the surrounding rock, not red; hysteresis
    f = (np.clip(-hp(B, 20, 1.6) / 8, 0, None) * 0.6 + np.clip(-hp(L, 20, 1.6) / 14, 0, None) * 0.6
         - np.clip(hp(A, 40, 1.5) / 6, 0, None))
    f = np.clip(f, 0, 1.5)
    fL = -hp(L, 20, 1.6)
    n, lb, st, _ = cv2.connectedComponentsWithStats((f > 0.30).astype(np.uint8), connectivity=8)
    keep = np.zeros(n, bool)
    for i in np.unique(lb[f > 0.75]):
        # guanaco bodies: big enough and clearly darker than the rock (drops ochre shadows)
        if i and st[i, cv2.CC_STAT_AREA] > 600 and fL[lb == i].mean() > 5:
            keep[i] = True
    g = keep[lb].astype(np.uint8)
    g = cv2.morphologyEx(g, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    inv = (1 - g).astype(np.uint8)
    n2, lb2, st2, _ = cv2.connectedComponentsWithStats(inv, connectivity=4)
    holes = np.zeros(n2, bool); holes[1:] = st2[1:, cv2.CC_STAT_AREA] < 400
    g = np.maximum(g, holes[lb2].astype(np.uint8)).astype(np.float32)
    # legs, necks, tails: thin painted strokes near the bodies, kept as a graded density
    thin = np.clip((-hp(L, 6, 1.0) - 3.5) / 6.0, 0, 1) * np.clip(1 - np.clip(hp(A, 30, 1.2) / 5, 0, 1), 0, 1)
    # keep only near-vertical strokes (legs) hanging below a body: open with a vertical line
    tb = cv2.morphologyEx((thin > 0.25).astype(np.uint8), cv2.MORPH_OPEN, np.ones((9, 1), np.uint8))
    below = np.zeros_like(g); below[12:] = g[:-12]                     # body shifted down 12 px
    near = cv2.GaussianBlur(cv2.dilate(np.maximum(below, g), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 21))), (0, 0), 2)
    n3, lb3, st3, _ = cv2.connectedComponentsWithStats(tb, connectivity=8)
    ok = np.zeros(n3, bool); ok[1:] = st3[1:, cv2.CC_STAT_HEIGHT] >= 10
    thin = cv2.GaussianBlur(ok[lb3].astype(np.float32), (0, 0), 0.8)
    mottle = np.clip(f / 1.2, 0, 1)
    guan = np.maximum(cv2.GaussianBlur(g, (0, 0), 0.7), 0.8 * thin * near)
    # yellow ochre figures (lighter)
    Bb = cv2.GaussianBlur(B, (0, 0), 60)
    yel = np.clip((cv2.GaussianBlur(B, (0, 0), 1.5) - Bb - 6) / 22.0, 0, 1) * (1 - red)
    # negative-hand interior: unpainted rock enclosed by spray -> lifted pale
    ring = cv2.GaussianBlur(red, (0, 0), 14)
    hand = np.clip((ring - 0.22) * 3.0, 0, 1) * np.clip(1 - red * 2.5, 0, 1)
    hand = cv2.GaussianBlur(hand, (0, 0), 1.2)
    # rock: low frequencies + a 0.30 high-pass, itself low-passed (wash, not grit)
    Ln = L / 100.0
    base = cv2.GaussianBlur(Ln, (0, 0), 45)
    rock_hp = cv2.GaussianBlur(Ln - base, (0, 0), 3.0)
    broad = base - np.median(base)
    rock = HP_GAIN * rock_hp + BROAD_GAIN * broad
    # --- editor repair 1: stencils as PALE hands in DARK blown halos; guanacos thinned ---
    # stencil masks from the photograph's own hands: the negative stencil's unpainted interior
    # (enclosed by spray) and the positive red hand's outline (used as the mask a halo is blown round)
    rr = (cv2.GaussianBlur(red, (0, 0), 1) > 0.35).astype(np.uint8)
    n4, lb4, st4, cen4 = cv2.connectedComponentsWithStats(rr, connectivity=8)
    pos = np.zeros_like(red)
    for i in range(1, n4):
        cx, cy = cen4[i]
        if 480 < cx < 600 and 420 < cy < 560 and st4[i, cv2.CC_STAT_AREA] > 1500:   # the positive red hand
            pos = np.maximum(pos, (lb4 == i).astype(np.float32))
    pos = cv2.GaussianBlur(cv2.morphologyEx(pos, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)), (0, 0), 1.0)
    # repair 2: re-cut the positive red hand's outline at a finer red threshold so all five
    # fingers survive (the coarse mask kept three and left a dark 'heart'); largest part, holes filled
    dA = cv2.GaussianBlur(A, (0, 0), 1.5) - cv2.GaussianBlur(A, (0, 0), 40)
    box = np.zeros(A.shape, np.uint8); box[400:580, 470:620] = 1
    pm = ((dA > 6) & (box > 0)).astype(np.uint8)
    pm = cv2.morphologyEx(pm, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    pm = cv2.morphologyEx(pm, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n8, lb8, st8, _ = cv2.connectedComponentsWithStats(pm, connectivity=8)
    if n8 > 1:
        pm = (lb8 == (np.argmax(st8[1:, cv2.CC_STAT_AREA]) + 1)).astype(np.uint8)
        ff8 = pm.copy(); cv2.floodFill(ff8, np.zeros((pm.shape[0] + 2, pm.shape[1] + 2), np.uint8), (0, 0), 1)
        pm = np.maximum(pm, 1 - ff8)
        pos = cv2.GaussianBlur(pm.astype(np.float32), (0, 0), 1.0)
    # the negative stencil (upper centre): its spray components enclose a hand of bare rock
    hullm = np.zeros(red.shape, np.uint8)
    for i in range(1, n4):
        cx, cy = cen4[i]
        if 640 < cx < 800 and 220 < cy < 450 and st4[i, cv2.CC_STAT_AREA] > 1500:
            ys, xs = np.nonzero(lb4 == i)
            hullm = np.maximum(hullm, ((lb4 == i)).astype(np.uint8))
    if hullm.any():
        ys, xs = np.nonzero(hullm)
        hull = cv2.convexHull(np.c_[xs, ys].astype(np.int32))
        hm = np.zeros_like(hullm); cv2.fillConvexPoly(hm, hull, 1)
        hm = cv2.erode(hm, np.ones((7, 7), np.uint8))
        inner = (hm > 0) & (cv2.GaussianBlur(red, (0, 0), 1.2) < 0.18)
        n6, lb6, st6, _ = cv2.connectedComponentsWithStats(inner.astype(np.uint8), connectivity=4)
        big = np.argmax(st6[1:, cv2.CC_STAT_AREA]) + 1 if n6 > 1 else 0
        negm = (lb6 == big).astype(np.float32) if big else np.zeros_like(red)
        negm = cv2.morphologyEx(negm, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    else:
        negm = np.zeros_like(red)
    neg = np.maximum(cv2.GaussianBlur(negm, (0, 0), 1.0), np.clip((hand - 0.15) * 2.5, 0, 1))
    sten = np.clip(np.maximum(neg, pos), 0, 1)
    # blown halo: pigment density falls off from the stencil edge, broken by spray grain
    sm = (sten > 0.4).astype(np.uint8)
    # repair 2: a stencil is one unbroken pale hand: fill every enclosed hole (the lower hand's
    # dark 'heart' in the palm was an unfilled hole of the positive hand's mask)
    sm = cv2.morphologyEx(sm, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    # only the photograph's two real hands are stencils (drop small lifted specks)
    n7, lb7, st7, _ = cv2.connectedComponentsWithStats(sm, connectivity=8)
    big2 = (np.argsort(-st7[1:, cv2.CC_STAT_AREA]) + 1)[:2]
    sm = np.isin(lb7, big2).astype(np.uint8)
    sten = sten * cv2.GaussianBlur(cv2.dilate(sm, np.ones((9, 9), np.uint8)).astype(np.float32), (0, 0), 2)
    ff = sm.copy(); ffm = np.zeros((sm.shape[0] + 2, sm.shape[1] + 2), np.uint8)
    cv2.floodFill(ff, ffm, (0, 0), 1)
    sm = np.maximum(sm, (1 - ff).astype(np.uint8))
    sten = np.maximum(sten, cv2.GaussianBlur(sm.astype(np.float32), (0, 0), 0.8))
    # the real red spray prints dark only round the stencils (their blown halos); elsewhere
    # (spiral, red figure, stray spray) it fades to a faint stain
    near = cv2.GaussianBlur(cv2.dilate(sm, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (81, 81))).astype(np.float32), (0, 0), 14)
    dist = cv2.distanceTransform(1 - sm, cv2.DIST_L2, 5)
    rng = np.random.default_rng(1956)
    spray = cv2.GaussianBlur(rng.random(sten.shape).astype(np.float32), (0, 0), 0.8)
    spray = (spray - spray.mean()) / (spray.std() + 1e-6)
    blow = cv2.GaussianBlur(cv2.dilate(sm, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))).astype(np.float32), (0, 0), 7)
    halo = (0.55 * np.exp(-dist / 13.0) + 0.55 * blow) * (dist > 0) * np.clip(0.8 + 0.4 * spray, 0, 1.25)
    halo = np.clip(cv2.GaussianBlur(halo, (0, 0), 1.0), 0, 1)
    sten = cv2.GaussianBlur(sten, (0, 0), 0.8)
    # guanacos: keep the six largest bodies solid, fade the small blobs to a faint wash
    gm = (guan > 0.5).astype(np.uint8)
    n5, lb5, st5, _ = cv2.connectedComponentsWithStats(gm, connectivity=8)
    order = np.argsort(-st5[1:, cv2.CC_STAT_AREA]) + 1
    _, _, _, cen5 = cv2.connectedComponentsWithStats(gm, connectivity=8)
    keepg = np.zeros(n5, np.float32)
    kept = 0
    for i in order:
        # repair 2: keep the KEEP_GUAN largest bodies that sit above world y 400 (clear of the
        # action band over the ground line); every other body fades below 10 % contrast
        wy = cen5[i][1] * S0 - SRC_OY
        if kept < KEEP_GUAN and wy < 400:
            keepg[i] = 1.0; kept += 1
        else:
            keepg[i] = FADE_GUAN
    gw = cv2.GaussianBlur(keepg[lb5].astype(np.float32), (0, 0), 2.0)
    guan = guan * np.clip(gw, FADE_GUAN, 1.0)
    # thin strokes (legs) that belong to a faded body fade with it
    guan = np.where(gw > 0.5, guan, np.minimum(guan, FADE_GUAN))
    # and nothing solid low on the wall, behind the action (world y > 405 fades out by 430)
    wy = np.arange(guan.shape[0], dtype=np.float32)[:, None] * S0 - SRC_OY
    vy = np.clip((402.0 - wy) / 22.0, 0, 1)
    # and none in the close-up's window (world x < 600, y > 290): frame B is an open wash
    wx = np.arange(guan.shape[1], dtype=np.float32)[None, :] * S0
    vb = 1 - np.clip((600.0 - wx) / 30.0, 0, 1) * np.clip((wy - 290.0) / 20.0, 0, 1)
    guan = guan * (FADE_GUAN + (1 - FADE_GUAN) * vy * vb)
    return dict(rock=rock, red=red, guan=guan, mottle=mottle, yel=yel, hand=hand, sten=sten, halo=halo, near=np.clip(near, 0, 1))


def wall_lum_master():
    """toned real wall on the master raster."""
    mp = rock_maps()
    A = np.float32([[S0 * M, 0, 0], [0, S0 * M, -SRC_OY * M]])
    w = {k: cv2.warpAffine(v, A, (MW, MH), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
         for k, v in mp.items()}
    l = PALE_LEVEL + w["rock"]
    l = l + 0.05 * np.clip(w["hand"], 0, 1)                         # pale hands
    l = l - 0.04 * np.clip(w["yel"], 0, 1)                         # repair 2: 0.30 -> 0.04 (no grey blotches)
    r = np.clip(w["red"] * 3.0, 0, 1) ** 0.6
    r = r * (0.06 + 0.94 * np.clip(w["near"], 0, 1))                # repair 2: dark spray only round stencils
    l = l * (1 - 0.90 * r) + 0.09 * 0.90 * r                    # blown halos -> dark charcoal
    g = np.clip(w["guan"], 0, 1)
    gl = 0.06 + 0.14 * np.clip(1 - w["mottle"], 0, 1) ** 1.5        # black with real grey dry-brush mottle
    l = l * (1 - g) + gl * g
    # repair 1: the hand stencils print as pale hands (bare rock lifted) in dark blown halos
    sten = np.clip(w["sten"], 0, 1)
    hl = np.clip(w["halo"], 0, 1) * (1 - sten)
    l = l * (1 - 0.88 * hl) + 0.10 * 0.88 * hl
    l = l * (1 - sten) + 0.94 * sten
    # repair 2: the stencil interiors are bare pale rock: no hand-hole lift outside them
    return l, w


# ------------------------------------------------------------- handmade layers ---
def _noise(shape, sx, sy, seed):
    rng = np.random.default_rng(seed)
    n = cv2.GaussianBlur(rng.random(shape).astype(np.float32), (0, 0), sigmaX=sx, sigmaY=sy)
    return (n - n.mean()) / (n.std() + 1e-6)


def band_layer(top, seed):
    """rubbed charcoal band, built from ~70 hand-laid horizontal charcoal strokes:
    each deposits only on the paper's tooth (pressure vs tooth), the deposit is then
    finger-rubbed (partly smeared sideways). Soft wavy edge with a pressed rim.
    Returns (alpha, lum) on the master raster."""
    h, w = MH, MW
    rng = np.random.default_rng(seed)
    xs = np.arange(w, dtype=np.float32) / M
    edge = (edge_y(xs, top) + 1.2 * _noise((1, w), 6 * M, 0.1, seed + 1)[0]) * M
    yy = np.arange(h, dtype=np.float32)[:, None]
    d = (edge[None, :] - yy) if top else (yy - edge[None, :])           # >0 inside the band
    alpha = np.clip(d / (5.0 * M) + 0.5, 0, 1)
    tooth = cv2.GaussianBlur(rng.random((h, w)).astype(np.float32), (0, 0), 1.6 * M)
    tooth = (tooth - tooth.min()) / (tooth.max() - tooth.min() + 1e-6)
    tooth = np.clip((tooth - 0.5) * 1.8 + 0.5, 0, 1)                      # paper peaks ~1, valleys ~0
    keep_free = np.ones((h, w), np.float32)                              # 1 - accumulated deposit
    y_lo = 0 if top else int((BOT_EDGE[0] - 25) * M)
    y_hi = int((TOP_EDGE[0] + 30) * M) if top else h
    for k in range(130):
        x0 = rng.uniform(-300, WW) * M; length = rng.uniform(250, 900) * M
        yc = rng.uniform(y_lo, y_hi); thick = rng.uniform(8, 26) * M
        press = rng.uniform(0.35, 0.75); slope = rng.normal(0, 0.012); wav = rng.uniform(2, 6) * M
        xa, xb = int(max(0, x0)), int(min(w, x0 + length))
        if xb <= xa:
            continue
        ya, yb = int(max(0, yc - 2 * thick - wav - 40 * M)), int(min(h, yc + 2 * thick + wav + 40 * M))
        X = np.arange(xa, xb, dtype=np.float32)[None, :]; Y = np.arange(ya, yb, dtype=np.float32)[:, None]
        u = (X - x0) / length
        cy = yc + slope * (X - x0) + wav * np.sin(u * rng.uniform(2, 6) + rng.uniform(0, 6))
        prof = np.exp(-((Y - cy) / (0.5 * thick)) ** 4)                   # flat stick, soft sides
        taper = np.clip(np.minimum(u, 1 - u) / 0.08, 0, 1)
        p = press * taper * prof
        dep = np.clip((p - (1 - tooth[ya:yb, xa:xb]) * 0.55) / 0.45, 0, 1) * 0.85
        keep_free[ya:yb, xa:xb] *= (1 - dep)
    D = 1 - keep_free
    rub = cv2.GaussianBlur(D, (0, 0), sigmaX=10 * M, sigmaY=2.5 * M)
    D = 0.72 * rub + 0.28 * D + 0.25 * cv2.GaussianBlur(D, (0, 0), 30 * M)
    target = 0.37 if top else 0.45                                        # ref means: lum 99 / 120
    lum = 0.93 - 0.85 * D
    inside = alpha > 0.5
    lum = lum - (lum[inside].mean() - target)
    dw = np.clip(d / M, 0, None)
    lum = lum - 0.10 * np.exp(-dw / 7.0)                                  # pressed along the edge
    return alpha, np.clip(lum, 0.03, 0.95)


def stroke_alpha(strokes, width=1.6, seed=0, gaps=0.2, shape=(MH, MW), scale=M, ox=0.0, oy=0.0):
    """scratched lines: each stroke drawn in short segments with pressure-varied width
    and random skips (the burin catching). strokes are world-coordinate polylines."""
    h, w = shape
    im = Image.new("L", (w, h), 0)
    dr = ImageDraw.Draw(im)
    rng = np.random.default_rng(seed)
    for pts in strokes:
        P = np.array(pts, np.float64)
        if len(P) < 2:
            continue
        seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
        L = seg.sum()
        n = max(2, int(L / 2.0))
        t = np.linspace(0, L, n)
        cum = np.r_[0, np.cumsum(seg)]
        xy = np.c_[np.interp(t, cum, P[:, 0]), np.interp(t, cum, P[:, 1])]
        press = np.clip(0.75 + 0.35 * np.sin(np.linspace(0, math.pi, n)) + rng.normal(0, 0.08, n), 0.3, 1.2)
        skip = False
        for i in range(n - 1):
            if rng.random() < 0.04:
                skip = rng.random() < gaps * 2
            if skip:
                continue
            a = ((xy[i, 0] - ox) * scale, (xy[i, 1] - oy) * scale)
            b = ((xy[i + 1, 0] - ox) * scale, (xy[i + 1, 1] - oy) * scale)
            dr.line([a, b], fill=255, width=max(1, int(round(width * press[i] * scale))))
    a = np.asarray(im).astype(np.float32) / 255
    return cv2.GaussianBlur(a, (0, 0), 0.45 * scale)


def wobble(p0, p1, n, amp, rng):
    return [(p0[0] + (p1[0] - p0[0]) * t + rng.normal(0, amp), p0[1] + (p1[1] - p0[1]) * t + rng.normal(0, amp))
            for t in np.linspace(0, 1, n + 1)]


def apply_scratch(l, a, rub=0.0, lip=0.12, rub_sigma=5.0, rub_tone=0.30):
    """engrave: optional charcoal rub behind (sgraffito), a faint dark lip, then the white line."""
    if rub > 0:
        r = cv2.GaussianBlur(a, (0, 0), rub_sigma * M) * 6
        r = np.clip(r, 0, 1) * rub
        l = l * (1 - r) + rub_tone * r
    sh = np.roll(np.roll(a, int(M), 0), int(M), 1)
    l = l * (1 - lip * sh)
    return l * (1 - a) + 0.99 * a


# default stone outline (local coords, rear at x 0, bottom y 0) = test-shot make_stone()
def stone_outline():
    rng = np.random.default_rng(1956)
    pts = []
    cx, cy, rx, ry = 125.0, -76.0, 127.0, 80.0
    for t in np.linspace(0, 2 * math.pi, 90, endpoint=False):
        c, s_ = math.cos(t), math.sin(t)
        r = (abs(c) ** 2.4 + abs(s_) ** 2.4) ** (-1 / 2.4)
        r *= 1 + 0.035 * math.sin(3 * t + 1) + 0.025 * math.sin(7 * t + 0.4) + rng.normal(0, 0.008)
        pts.append((cx + rx * r * c, min(cy + ry * r * s_, 0.0)))
    return pts


def ghost_strokes(poly, dx=0.0, dy=0.0, seed=0, breaks=3):
    """ghost-outline scratch generator: retrace a polygon (world coords after dx,dy)
    as 2-4 overlapping hand strokes with drift, overshoot and gaps, like the
    reference's engraved ghost animals."""
    rng = np.random.default_rng(seed)
    P = np.array(poly, np.float64) + [dx, dy]
    n = len(P)
    cuts = sorted(rng.choice(np.arange(n), size=breaks, replace=False))
    strokes = []
    for k in range(breaks):
        i0 = cuts[k] - rng.integers(0, 4)
        i1 = cuts[(k + 1) % breaks] + (n if k == breaks - 1 else 0) + rng.integers(1, 5)
        idx = np.arange(i0, i1) % n
        drift = np.cumsum(rng.normal(0, 0.5, (len(idx), 2)), axis=0)
        drift -= np.linspace(0, 1, len(idx))[:, None] * drift[-1] * 0.6
        strokes.append([tuple(p) for p in P[idx] + drift])
    return strokes


def ghost_layer(front_m, seed, bottom=GROUND - 4.0):
    """(wash alpha, scratch alpha) master-raster layers of the stone ghost whose front is
    at front_m metres."""
    poly = stone_outline()
    xb = X0 + front_m * PXM - 250.0
    st = ghost_strokes(poly, xb, bottom, seed)
    a = stroke_alpha(st, width=1.7, seed=seed)
    im = Image.new("L", (MW, MH), 0)
    ImageDraw.Draw(im).polygon([((x + xb) * M, (y + bottom) * M) for x, y in poly], fill=255)
    wash = cv2.GaussianBlur(np.asarray(im).astype(np.float32) / 255, (0, 0), 6 * M) * 0.16
    return wash, a


# ---- hand-cut title glyphs (single scratched strokes; unit = cap height, y up negative)
GLYPHS = {
    "T": (0.70, [[(-0.04, -0.97), (0.20, -1.01), (0.46, -1.0), (0.68, -1.04)],
                 [(0.31, -1.0), (0.30, -0.6), (0.29, -0.2), (0.27, 0.0), (0.20, 0.05)]]),
    "e": (0.50, [[(0.05, -0.24), (0.25, -0.27), (0.42, -0.30), (0.40, -0.45), (0.24, -0.53), (0.08, -0.43),
                  (0.03, -0.24), (0.08, -0.06), (0.22, 0.01), (0.42, -0.06)]]),
    "u": (0.53, [[(0.04, -0.52), (0.03, -0.30), (0.05, -0.10), (0.15, 0.0), (0.30, -0.03), (0.42, -0.20)],
                 [(0.43, -0.53), (0.42, -0.25), (0.44, 0.0)]]),
    "f": (0.40, [[(0.44, -0.92), (0.34, -1.0), (0.22, -0.94), (0.18, -0.70), (0.17, -0.35), (0.16, 0.0)],
                 [(0.02, -0.50), (0.20, -0.52), (0.36, -0.51)]]),
    "-": (0.36, [[(0.04, -0.30), (0.17, -0.32), (0.31, -0.31)]]),
    "t": (0.40, [[(0.17, -0.82), (0.17, -0.45), (0.17, -0.12), (0.25, 0.0), (0.37, -0.05)],
                 [(0.02, -0.52), (0.18, -0.53), (0.34, -0.51)]]),
}


def catmull(pts, k=8):
    P = np.array(pts, np.float64)
    if len(P) < 3:
        return [tuple(p) for p in P]
    P = np.vstack([P[0], P, P[-1]])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for t in np.linspace(0, 1, k, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-2])
    return [tuple(p) for p in out]


TITLE = "Teuf-teuf"
TITLE_BASE = (420.0, 150.0)    # world baseline centre of the title (upper-left wash, above the guanaco heads)
TITLE_CAP = 66.0               # cap height in world px


def title_strokes(seed=56):
    rng = np.random.default_rng(seed)
    x, y = TITLE_BASE
    total = sum(GLYPHS[c][0] for c in TITLE) * TITLE_CAP
    x -= total / 2 - 0  # centre the word on TITLE_BASE x
    out = []
    for c in TITLE:
        adv, sts = GLYPHS[c]
        for s in sts:
            pts = [(x + (u + rng.normal(0, 0.012)) * TITLE_CAP, y + (v + rng.normal(0, 0.012)) * TITLE_CAP) for u, v in s]
            out.append(catmull(pts))
        x += adv * TITLE_CAP
    return out


def title_rub(l, a, seed=57):
    """sgraffito ground for the title: a broad finger-rubbed charcoal patch laid over the
    word's area first, so the white scratches cut through dark (as engraving does)."""
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(22 * M) | 1, int(22 * M) | 1))
    area = cv2.dilate((a > 0.2).astype(np.uint8), k).astype(np.float32)
    patch = np.clip(cv2.GaussianBlur(area, (0, 0), sigmaX=16 * M, sigmaY=9 * M) * 1.5, 0, 1)
    tex = 0.80 + 0.12 * _noise(l.shape, 10 * M, 1.2 * M, seed) + 0.08 * _noise(l.shape, 1.2 * M, 1.2 * M, seed + 1)
    patch = np.clip(patch * tex, 0, 1) * 0.88
    return l * (1 - patch) + 0.26 * patch


def partial(strokes, frac):
    """the first `frac` of the total stroke length, in writing order (title reveal)."""
    lens = [np.linalg.norm(np.diff(np.array(s), axis=0), axis=1).sum() for s in strokes]
    budget = frac * sum(lens)
    out = []
    for s, L in zip(strokes, lens):
        if budget <= 0:
            break
        if L <= budget:
            out.append(s); budget -= L; continue
        P = np.array(s); seg = np.linalg.norm(np.diff(P, axis=0), axis=1); cum = np.r_[0, np.cumsum(seg)]
        k = np.searchsorted(cum, budget)
        t = (budget - cum[k - 1]) / max(seg[k - 1], 1e-9)
        out.append([tuple(p) for p in P[:k]] + [tuple(P[k - 1] + (P[k] - P[k - 1]) * t)])
        budget = 0
    return out


def ghost_animal_strokes(seed=13):
    """an engraved ghost bovid contour in the upper middle wash (handmade)."""
    rng = np.random.default_rng(seed)
    back = [(610 + 300 * t, 128 - 34 * math.sin(math.pi * t ** 0.8) + 4 * math.sin(11 * t)) for t in np.linspace(0, 1, 26)]
    head = [(910, 120), (936, 112), (958, 128), (966, 150), (948, 162), (926, 150), (912, 140)]
    horn = [(934, 112), (950, 88), (972, 80)]
    belly = [(640, 232), (720, 246), (800, 244), (880, 232), (908, 196), (912, 150)]
    rump = [(610, 128), (596, 170), (612, 214), (640, 232)]
    legs = [[(650, 236), (646, 270), (652, 296)], [(690, 242), (700, 284), (694, 300)],
            [(842, 240), (836, 280), (846, 300)], [(882, 232), (896, 270), (888, 296)]]
    out = [back, head, horn, belly, rump] + legs
    return [[(x + rng.normal(0, 0.8), y + rng.normal(0, 0.8)) for x, y in catmull(s, 5)] for s in out]


QUAD = {   # unit profile of a scratched quadruped (facing +x, y down; rump top at 0,0)
    "back": [(0.0, 0.0), (0.2, -0.04), (0.45, -0.02), (0.68, -0.07), (0.8, -0.12)],
    "neck": [(0.8, -0.12), (0.9, -0.3), (0.96, -0.42), (1.02, -0.47)],
    "head": [(0.96, -0.5), (1.02, -0.49), (1.12, -0.42), (1.16, -0.36), (1.1, -0.33), (1.0, -0.33), (0.93, -0.24)],
    "ear": [(0.97, -0.48), (0.95, -0.6), (0.99, -0.51)],
    "chest": [(0.93, -0.24), (0.9, -0.05), (0.84, 0.16), (0.8, 0.26)],
    "belly": [(0.8, 0.26), (0.62, 0.3), (0.42, 0.31), (0.24, 0.27)],
    "rump": [(0.0, 0.0), (-0.05, 0.1), (-0.02, 0.22), (0.06, 0.28), (0.24, 0.27)],
    "tail": [(0.0, 0.02), (-0.08, 0.06), (-0.12, 0.16)],
    "leg1": [(0.78, 0.25), (0.8, 0.45), (0.77, 0.66), (0.8, 0.7)],
    "leg2": [(0.68, 0.29), (0.64, 0.47), (0.68, 0.68)],
    "leg3": [(0.08, 0.27), (0.04, 0.45), (0.1, 0.67), (0.13, 0.7)],
    "leg4": [(0.2, 0.28), (0.24, 0.47), (0.2, 0.68)],
}


def scratched_quadruped(x0, y0, size, face=1, seed=0, skip=()):
    """repair 2: a white scratched line animal like the reference's engraved ghost beasts
    (handmade: drawn here, not traced from anything)."""
    rng = np.random.default_rng(seed)
    out = []
    for k, pts in QUAD.items():
        if k in skip:
            continue
        P = [(x0 + face * (u + rng.normal(0, 0.008)) * size, y0 + (v + rng.normal(0, 0.008)) * size) for u, v in pts]
        out.append(catmull(P, 6))
    return out


def dot_cluster(seed=21, cx=1135.0, cy=150.0, n=110):
    """dabbed charcoal dots (the reference's dot clusters), irregular dab shapes."""
    rng = np.random.default_rng(seed)
    m = np.zeros((MH, MW), np.float32)
    for _ in range(n):
        x = rng.normal(cx, 62); y = rng.normal(cy, 24) + 0.25 * (x - cx)
        r = rng.uniform(1.4, 2.8) * M
        cv2.ellipse(m, (int(x * M), int(y * M)), (int(r * rng.uniform(1.0, 1.8)) + 1, int(r) + 1),
                    rng.uniform(-30, 30), 0, 360, float(rng.uniform(0.7, 1.0)), -1)
    return cv2.GaussianBlur(m, (0, 0), 0.6 * M)


# ------------------------------------------------------------- assembly ---
def build_master():
    l, maps = wall_lum_master()
    # ground line: pressed charcoal stroke, broken by the tooth
    xs = np.arange(MW, dtype=np.float32) / M
    gy = (GROUND + 1.0 * np.sin(xs / 37) + 0.7 * np.sin(xs / 11)) * M
    yy = np.arange(MH, dtype=np.float32)[:, None]
    gl = np.exp(-((yy - gy[None, :]) / (1.5 * M)) ** 2)
    gl *= np.clip(0.8 + 0.3 * _noise((1, MW), 4 * M, 0.1, 31)[0], 0.3, 1.1)[None, :]
    l = l * (1 - 0.85 * gl) + 0.08 * 0.85 * gl
    # bands
    bands = {}
    for top, seed in ((True, 3), (False, 4)):
        a, bl = band_layer(top, seed)
        bl = bl * 0.76        # repair 1: charcoal pressed harder (dark mass lost from the thinned guanacos)
        # repair 2: rub contrast x1.9 about the band's mean (pressed streaks go black, rubbed ones
        # stay grey), as in the reference's bands whose lum spans ~30..220 around the same mean
        mb = float(bl[a > 0.5].mean())
        bl = np.clip(mb + 0.03 + 1.85 * (bl - mb), 0.03, 0.95)
        l = l * (1 - a) + bl * a
        bands["top" if top else "bottom"] = a
    # dot cluster + ghost animal + ticks
    dots = dot_cluster()
    l = l * (1 - 0.85 * dots) + 0.09 * 0.85 * dots
    rng = np.random.default_rng(7)
    ga = stroke_alpha(ghost_animal_strokes(), width=1.9, seed=13, gaps=0.15)
    l = apply_scratch(l, 0.9 * ga, rub=0.10, lip=0.10)
    # repair 2: two more white scratched line animals in the open wash (as in the reference)
    qa = stroke_alpha(scratched_quadruped(290, 215, 200, face=-1, seed=41) +
                      scratched_quadruped(1250, 300, 190, face=-1, seed=42, skip=("tail",)), width=1.9, seed=43, gaps=0.15)
    l = apply_scratch(l, 0.9 * qa, rub=0.10, lip=0.10)
    ticks = [wobble((X0 + PXM * m - 1, GROUND + 6), (X0 + PXM * m + 2, GROUND + 28), 4, 0.5, rng) for m in TICKS_M]
    ta = stroke_alpha(ticks, width=1.5, seed=17, gaps=0.05)
    l = apply_scratch(l, 0.9 * ta, rub=0.45, lip=0.15)
    return l, bands, maps


def to_cam(master, cam):
    """sample the master raster for a camera (exact crop when cam.s == M)."""
    k = cam.s / M
    A = np.float32([[k, 0, -cam.ox * cam.s], [0, k, -cam.oy * cam.s]])
    flag = cv2.INTER_AREA if k < 1 else cv2.INTER_LINEAR
    if k < 1:
        # area-downsample first, then a sub-pixel affine
        small = cv2.resize(master, (int(round(MW * k)), int(round(MH * k))), interpolation=cv2.INTER_AREA)
        A = np.float32([[1, 0, -cam.ox * cam.s], [0, 1, -cam.oy * cam.s]])
        return cv2.warpAffine(small, A, (cam.w, cam.h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    return cv2.warpAffine(master, A, (cam.w, cam.h), flags=flag, borderMode=cv2.BORDER_REPLICATE)


def grain(shape, seed, amt=3.0):
    rng = np.random.default_rng(seed)
    g = rng.normal(0, 1, shape).astype(np.float32)
    return cv2.GaussianBlur(g, (0, 0), 0.6) * amt


def print_rgb(lum, seed=0, amt=3.0):
    rgb = ramp(lum) + grain(lum.shape, seed, amt)[..., None]
    return np.clip(rgb, 0, 255).astype(np.uint8)


def measure(rgb, top_mask=None, bot_mask=None):
    a = rgb.astype(np.float32)
    lum = 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
    bl = cv2.GaussianBlur(lum, (0, 0), 4)
    pale = bl > 150
    q = np.percentile(lum, [1, 5, 10, 25, 50, 75, 90, 95, 99]).round(0).tolist()
    out = dict(pale_fraction=round(float(pale.mean()), 3),
               pale_median_rgb=[int(np.median(a[..., c][pale])) for c in range(3)],
               pale_median_lum=int(np.median(lum[pale])),
               frac_below_60=round(float((lum < 60).mean()), 3),
               lum_percentiles_1_5_10_25_50_75_90_95_99=q)
    if top_mask is not None:
        for nm, mk in (("top", top_mask), ("bottom", bot_mask)):
            out[nm + "_band_mean_rgb"] = [int(a[..., c][mk].mean()) for c in range(3)] if mk.any() else None
        out["top_band_fraction"] = round(float(top_mask.mean()), 3)
        out["bottom_band_fraction"] = round(float(bot_mask.mean()), 3)
    return out


def save_alpha_png(path, a, cam):
    x = to_cam(a, cam)
    Image.fromarray(np.clip(x * 255, 0, 255).astype(np.uint8), "L").save(path)


def main():
    os.makedirs(OUT, exist_ok=True)
    master, bands, maps = build_master()
    np.save(OUT + "/master_lum_x2.2.npy", master.astype(np.float16))
    np.save(OUT + "/bandtop_A.npy", to_cam(bands["top"], CAM_A).astype(np.float16))   # repair 2: for push-in cameras
    res = {}
    for name, cam, seed in (("A", CAM_A, 1), ("B", CAM_B, 2)):
        lum = to_cam(master, cam)
        if name == "B":
            # repair 1: the close-up keeps the wall's top charcoal band at screen scale (frame A's band)
            aA = to_cam(bands["top"], CAM_A)
            lumA = to_cam(master, CAM_A)
            lum = lum * (1 - aA) + lumA * aA
        np.save(f"{OUT}/frame{name}_lum.npy", lum.astype(np.float32))
        rgb = print_rgb(lum, seed)
        Image.fromarray(rgb).save(f"{OUT}/frame{name}.png")
        tm = (to_cam(bands["top"], CAM_A) if name == "B" else to_cam(bands["top"], cam)) > 0.5
        bm = to_cam(bands["bottom"], cam) > 0.5
        res[name] = measure(rgb, tm, bm)
        # ghosts at 1.2 / 3.0 / 8.0 m as separate alpha layers (they appear during the film)
        for i, m in enumerate((1.2, 3.0, 8.0)):
            wash, sc = ghost_layer(m, 100 + i)
            save_alpha_png(f"{OUT}/ghost_{m:.1f}m_{name}_scratch.png", sc, cam)
            save_alpha_png(f"{OUT}/ghost_{m:.1f}m_{name}_wash.png", wash, cam)
        if name == "A":
            # demo with all three ghosts burned in (wash darkens, scratch whitens)
            l2 = master.copy()
            for i, m in enumerate((1.2, 3.0, 8.0)):
                wash, sc = ghost_layer(m, 100 + i)
                l2 = l2 * (1 - wash) + 0.35 * wash
                l2 = apply_scratch(l2, sc, rub=0.0, lip=0.10)
            Image.fromarray(print_rgb(to_cam(l2, cam), 1)).save(f"{OUT}/frameA_with_ghosts.png")
    # title: full alpha (A camera) + 29-frame reveal (1.2 s at 24 fps)
    ts = title_strokes()
    os.makedirs(OUT + "/title_reveal", exist_ok=True)
    for k in range(29):
        f = (k + 1) / 29
        a = stroke_alpha(partial(ts, f), width=3.3, seed=56, gaps=0.02)
        save_alpha_png(f"{OUT}/title_reveal/title_{k:02d}.png", a, CAM_A)
    full = stroke_alpha(ts, width=3.3, seed=56, gaps=0.02)
    save_alpha_png(OUT + "/title_alpha_A.png", full, CAM_A)
    lt = apply_scratch(title_rub(master.copy(), full), full, rub=0.0, lip=0.10)
    save_alpha_png(OUT + "/title_rub_A.png", 1 - np.clip((title_rub(np.ones_like(master), full) - 0.26) / 0.74, 0, 1), CAM_A)
    Image.fromarray(print_rgb(to_cam(lt, CAM_A), 1)).save(OUT + "/frameA_title.png")
    json.dump(dict(strokes_world=[[list(map(lambda v: round(v, 1), p)) for p in s] for s in ts]),
              open(OUT + "/title_strokes.json", "w"))
    return res


if __name__ == "__main__":
    print(json.dumps(main(), indent=1))

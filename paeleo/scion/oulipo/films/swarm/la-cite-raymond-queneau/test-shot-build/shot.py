"""TEST SHOT r2 · La Cité Raymond Queneau · S3 key beat, master f456-f623 (19.0-26.0 s).

A handmade cut-paper model of three staggered blocks (plus a hazed fourth) receding on a diagonal
to the left, built in 3D street coordinates and photographed by a pinhole camera at eye level
(1.5 m) from across the road.  Every face is a sheet cut from a foraged paper scan (LoC blank
sheet, Commons kraft, Commons vintage paper; see test-shot-ledger.json) graded only by
per-channel levels, set into perspective by a homography.

Techniques
  #5 Norstein multiplane: the model is split into glass planes (P0 sky, P1 far hazed block,
     P2 far block, P2b mid block, P3 near block, P4 saplings+hedge, P5 pavement/road, P6 verge,
     P7 fence post).  A fog sheet between successive planes (denser low) softens far planes, and
     the far planes are slightly out of focus.  The camera's last 8 cm of lateral drift settles
     to a lock as window 16 lights; each plane shifts by f*dx/Z (near planes more).
     Exposure schedule: dusk = lower exposure on the paper (0.885 -> 0.78), lamps unchanged.
  #6 Whitney: window i lights at step s(i) = 37 i mod 96, frame = round(24 (6.1 + 0.9 s));
     3-frame attack; each lit window breathes 0.5 % (phase 2 pi i / 96, period 3.1 s);
     saplings sway on two incommensurate oscillators (0.37 Hz, 0.23 Hz).
  #47 Sound-to-action: the silhouette's rise / hold / head turn / curtain settle are the body
     action the two soundtracks read (cue maps in cues.json).

Window numbering (plan §6): i = floor*24 + bay; floor 0 = top floor; bays 0-7 far block,
8-15 middle block, 16-23 near block (the score is unchanged; window 16 = top floor, first bay
of the near block, directly above its entrance).

Usage: python3 -I shot.py build            (cache static planes)
       python3 -I shot.py frames <dir> [k ...]
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SRC = "/home/user/bolas/paeleo/scion/oulipo/films/sources/la-cite-raymond-queneau/test-shot/paper"
CACHE = "/home/user/bolas/paeleo/scion/oulipo/films/sources/la-cite-raymond-queneau/test-shot/cache"
PW, PH = 960, 464
SS = 2
W2, H2 = PW * SS, PH * SS
FPS = 24
K0, K1 = 456, 624

# ------------------------------------------------------------------ score ---
def step_of(i):
    return (37 * i) % 96

def light_frame(i):
    s = step_of(i)
    return int(round(FPS * (6.1 + 0.9 * s))) if s <= 21 else None

LIGHT = {i: light_frame(i) for i in range(96) if light_frame(i) is not None}
assert LIGHT[16] == 492 and LIGHT[47] == 384

def glow(i, k):
    f = LIGHT.get(i)
    if f is None or k < f - 2:
        return 0.0
    a = min(1.0, (k - (f - 3)) / 3.0)
    return a * (1.0 + 0.005 * math.sin(2 * math.pi * (k / FPS) / 3.1 + 2 * math.pi * i / 96))

def exposure(k):
    return 0.93 - 0.15 * (k - 384) / 239.0

# ----------------------------------------------------------------- camera ---
ANG = math.radians(47.0)                     # facades meet the picture plane at 47 deg
D = np.array([-math.cos(ANG), math.sin(ANG)])   # street direction, toward far-left
NV = np.array([math.sin(ANG), math.cos(ANG)])   # perpendicular, from camera toward the blocks
F = 610.0 * SS                               # focal length, px
CX, CY = W2 * 0.5, H2 * 0.865                # level camera, horizon at 0.865 H (closer key shot)
EYE = 1.5
CAM_S = 2.2                                  # camera's street coordinate (frames window 16 right of centre)

def world(s, n):
    p = (s - CAM_S) * D + n * NV
    return p[0], p[1]

def proj(s, n, y):
    X, Z = world(s, n)
    return (CX + F * X / Z, CY - F * (y - EYE) / Z)

def depth(s, n):
    return world(s, n)[1]

# ------------------------------------------------------------------ model ---
BAY, NBK = 3.2, 8
GF, FL = 3.6, 3.0
HE = GF + 4 * FL                     # eave 15.6 m
RR = 4.2                             # quarter-cylinder roof radius
DEPTH = 12.0
WIN_W, WIN_H = 1.45, 2.3
# blocks: (s_left = far-left end, n_front); the score's bays run left to right
BLOCKS = [dict(name="far", s_left=88.0, n=17.0, bay0=0),
          dict(name="mid", s_left=55.0, n=18.0, bay0=8),
          dict(name="near", s_left=22.0, n=19.0, bay0=16)]
LEN = BAY * NBK

def bay_s(bay):
    """street coordinate of the left (far) edge of a global bay index."""
    b = BLOCKS[bay // NBK]
    return b["s_left"] - (bay % NBK) * BAY

def storey_base(fl):
    return GF + (3 - fl) * FL

# ----------------------------------------------------- paper (foraged) ---
def load_paper(name, size, target, contrast, crop=None, rot=0, native=False):
    """A foraged scan cropped (clean area only) and graded by per-channel levels toward a target."""
    im = Image.open(os.path.join(SRC, name)).convert("RGB")
    if crop:
        im = im.crop(crop)
    if rot:
        im = im.rotate(rot, expand=True)
    w, h = im.size
    tw, th = size
    if w >= tw and h >= th and native:
        im = im.crop((0, 0, tw, th))                       # native scan resolution: the fibre survives
    else:
        sc = max(tw / w, th / h)
        im = im.resize((int(w * sc) + 2, int(h * sc) + 2), Image.BICUBIC).crop((0, 0, tw, th))
    a = np.asarray(im).astype(np.float32)
    med = np.median(a.reshape(-1, 3), axis=0)
    return np.clip((a - med) * contrast + np.array(target, np.float32), 0, 255)

LOC_CLEAN = (420, 260, 2900, 2330)          # inside the LoC sheet, away from tape and edges

def tiled_kraft(size, target, contrast, rot=0, ox=0):
    im = Image.open(os.path.join(SRC, "kraft_tileable.png")).convert("RGB")
    if rot:
        im = im.rotate(rot)
    w, h = size
    big = Image.new("RGB", (w + 1024, h + 1024))
    for x in range(0, w + 1024, 1024):
        for y in range(0, h + 1024, 1024):
            big.paste(im, (x, y))
    big = big.crop((ox % 1024, 0, ox % 1024 + w, h))
    a = np.asarray(big).astype(np.float32)
    med = np.median(a.reshape(-1, 3), axis=0)
    return np.clip((a - med) * contrast + np.array(target, np.float32), 0, 255)

# -------------------------------------------------------------- warping ---
def homography(src, dst):
    Am, bm = [], []
    for (x, y), (u, v) in zip(dst, src):
        Am.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); bm.append(u)
        Am.append([0, 0, 0, x, y, 1, -v * x, -v * y]); bm.append(v)
    return np.linalg.solve(np.array(Am, float), np.array(bm, float))

def warp_into(canvas, tex, src_quad, dst_quad, mask=None):
    """Warp an RGBA texture onto the RGBA canvas (premult not needed: paste with alpha). Bbox-limited."""
    xs = [p[0] for p in dst_quad]; ys = [p[1] for p in dst_quad]
    x0, y0 = max(0, int(math.floor(min(xs))) - 1), max(0, int(math.floor(min(ys))) - 1)
    x1, y1 = min(canvas.width, int(math.ceil(max(xs))) + 1), min(canvas.height, int(math.ceil(max(ys))) + 1)
    if x1 <= x0 or y1 <= y0:
        return
    dq = [(x - x0, y - y0) for x, y in dst_quad]
    co = homography(src_quad, dq)
    rgba = tex if tex.mode == "RGBA" else tex.convert("RGBA")
    out = rgba.transform((x1 - x0, y1 - y0), Image.PERSPECTIVE, co.tolist(), Image.BICUBIC)
    m = Image.new("L", out.size, 0)
    ImageDraw.Draw(m).polygon(dq, fill=255)
    a = np.minimum(np.asarray(out.getchannel("A")), np.asarray(m))
    out.putalpha(Image.fromarray(a))
    canvas.alpha_composite(out, (x0, y0))

def to_img(a, alpha=None):
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    if alpha is not None:
        im.putalpha(alpha)
    return im

# ------------------------------------------------------- block textures ---
TPX = 40        # texture px per metre

def hand_poly(pts, jit, seed):
    r = np.random.RandomState(seed)
    out = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        n = max(2, int(math.hypot(x1 - x0, y1 - y0) / 10))
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append((x0 + (x1 - x0) * t + r.normal(0, jit), y0 + (y1 - y0) * t + r.normal(0, jit)))
    return out

BALC = {0: {2, 3, 6}, 1: {10, 11, 14}, 2: {18, 19}}     # bays with balconies, floors 1-3

def win_tex_rect(bay_local, fl):
    """window rectangle in facade texture px (u from the left end, v from the eave down)."""
    u0 = (bay_local * BAY + (BAY - WIN_W) / 2) * TPX
    yb = storey_base(fl) + 0.22
    v1 = (HE - yb) * TPX
    v0 = (HE - yb - WIN_H) * TPX
    return u0, v0, u0 + WIN_W * TPX, v1

def build_facade(bi, seed):
    w, h = int(LEN * TPX), int(HE * TPX)
    off = [(0, 0), (900, 300), (300, 900)][bi]
    crop = (LOC_CLEAN[0] + off[0] // 3, LOC_CLEAN[1] + off[1] // 3, LOC_CLEAN[2] - 300 + off[0] // 3, LOC_CLEAN[3] - 300 + off[1] // 3)
    a = load_paper("loc_blank_0001.jpg", (w, h), (181, 183, 168), 1.5, crop=crop, native=True)
    yy = np.linspace(0, 1, h)[:, None, None]
    a *= 1.0 - 0.05 * yy
    a[:28] *= np.linspace(0.72, 1.0, 28)[:, None, None]              # eave occlusion
    img = to_img(a)
    d = ImageDraw.Draw(img)
    b0 = BLOCKS[bi]["bay0"]
    for fl in range(4):
        # string course at each floor line
        y = (HE - storey_base(fl)) * TPX
        d.line((0, y, w, y), fill=(160, 164, 150, 255), width=3)
        for j in range(NBK):
            bay = b0 + j
            u0, v0, u1, v1 = win_tex_rect(j, fl)
            if bay in BALC[bi] and fl > 0:
                # loggia occlusion band beneath the slab (balcony shadow on the wall)
                d.rectangle((u0 - 22, v1 + 4, u1 + 22, v1 + 22), fill=(118, 120, 104, 255))
            d.polygon(hand_poly([(u0, v0), (u1, v0), (u1, v1), (u0, v1)], 0.6, seed + fl * 31 + j), fill=(74, 85, 86, 255))
            d.rectangle((u0, v0, u1, v0 + 7), fill=(54, 62, 63, 255))       # top reveal in shadow
            d.rectangle((u0, v0, u0 + 4, v1), fill=(62, 71, 72, 255))       # left reveal
            # french window: mullion and transom (cream card strips)
            mx = (u0 + u1) / 2
            d.line((mx, v0 + 7, mx, v1), fill=(150, 154, 142, 255), width=3)
            d.line((u0 + 4, v0 + 24, u1, v0 + 24), fill=(150, 154, 142, 255), width=2)
            # low guard rail (dark olive) across the lower third
            d.rectangle((u0, v1 - 36, u1, v1 - 33), fill=(73, 73, 55, 255))
            for xx in np.arange(u0 + 5, u1, 7):
                d.line((xx, v1 - 33, xx, v1), fill=(80, 80, 62, 255), width=1)
    # ground floor
    gy = (HE - GF) * TPX
    for j in range(NBK):
        u = (j * BAY + 0.9) * TPX
        if bi == 2 and j == 0:
            # entrance under bay 16: canopy, glazed door
            d.rectangle((u - 18, gy + 24, u + 70 + 18, gy + 34), fill=(130, 134, 124, 255))
            d.rectangle((u - 14, gy + 34, u + 70 + 14, gy + 42), fill=(96, 100, 92, 255))
            d.rectangle((u, gy + 42, u + 70, h), fill=(64, 72, 70, 255))
            d.line((u + 35, gy + 46, u + 35, h), fill=(96, 104, 100, 255), width=3)
            continue
        d.rectangle((u, gy + 30, u + 56, gy + 92), fill=(80, 90, 90, 255))
        d.rectangle((u, gy + 30, u + 56, gy + 36), fill=(58, 66, 66, 255))
    for x in (int(LEN * TPX * 0.37), int(LEN * TPX * 0.74)):
        d.line((x, 0, x, h), fill=(146, 150, 140, 255), width=5)          # downpipes
    return img

def build_roof_tex(bi):
    w, h = int(LEN * TPX), 200
    a = tiled_kraft((w, h), (84, 98, 101), 0.55, rot=0, ox=bi * 333)      # laid lines run down the slope = seams
    img = to_img(a)
    d = ImageDraw.Draw(img)
    for x in np.arange(0, w, 0.62 * TPX):
        d.line((x, 0, x, h), fill=(104, 118, 124, 255), width=2)          # standing seams (paper strips)
    return img

def build_end_tex(bi):
    w, h = int(DEPTH * TPX), int((HE + RR) * TPX)
    a = load_paper("loc_blank_0001.jpg", (w, h), (168, 172, 158), 1.5,
                   crop=(LOC_CLEAN[0] + 200 * bi, LOC_CLEAN[1] + 300, LOC_CLEAN[2], LOC_CLEAN[3]), native=True)
    img = to_img(a)
    d = ImageDraw.Draw(img)
    # a narrow stair window column near the front, and floor lines
    for fl in range(4):
        yb = storey_base(fl) + 0.9
        v1 = (HE + RR - yb) * TPX
        d.rectangle((2.2 * TPX, v1 - 1.2 * TPX, 2.9 * TPX, v1), fill=(80, 90, 90, 255))
    return img

def build_dormer_tex():
    w, h = int(1.4 * TPX), int(1.6 * TPX)
    a = load_paper("loc_blank_0001.jpg", (w, h), (190, 207, 212), 0.6, crop=(1200, 900, 1600, 1300))
    img = to_img(a)
    d = ImageDraw.Draw(img)
    d.rectangle((9, 12, w - 9, h - 6), fill=(92, 104, 108, 255))
    d.line((w / 2, 12, w / 2, h - 6), fill=(170, 186, 190, 255), width=2)
    return img

# ------------------------------------------------------- block geometry ---
def facade_quad(b):
    s0, s1, n = b["s_left"], b["s_left"] - LEN, b["n"]
    return [proj(s0, n, HE), proj(s1, n, HE), proj(s1, n, 0), proj(s0, n, 0)]

def roof_strips(b, N=14):
    s0, s1, n = b["s_left"], b["s_left"] - LEN, b["n"]
    out = []
    for j in range(N):
        t0 = (math.pi / 2) * j / N
        t1 = (math.pi / 2) * (j + 1) / N
        def P(s, t):
            return proj(s, n + RR * (1 - math.cos(t)), HE + RR * math.sin(t))
        v0, v1 = 200 * (1 - j / N), 200 * (1 - (j + 1) / N)
        out.append((t0, t1, [(0, v1), (LEN * TPX, v1), (LEN * TPX, v0), (0, v0)],
                    [P(s0, t1 + 0.012), P(s1, t1 + 0.012), P(s1, t0), P(s0, t0)]))
    return out

def end_wall(b):
    """right (near) end wall in the plane s = s_left - LEN: front edge, quarter-circle top, flat roof, back."""
    s, n = b["s_left"] - LEN, b["n"]
    pts = [(n, 0.0)]
    for j in range(25):
        t = (math.pi / 2) * j / 24
        pts.append((n + RR * (1 - math.cos(t)), HE + RR * math.sin(t)))
    pts += [(n + DEPTH, HE + RR), (n + DEPTH, 0.0)]
    return s, pts

def shade_roof(t):
    """overcast from above: steep lower slope darker, upper curve catches the sky, sheen near 55 deg."""
    base = np.array([77, 91, 93], np.float32)
    hi = np.array([119, 133, 147], np.float32)
    m = math.sin(t) ** 1.6
    sheen = math.exp(-((t - 1.05) / 0.22) ** 2) * 0.55
    c = base * (0.86 + 0.14 * m) + (hi - base) * (0.25 * m + sheen)
    return c / base

def render_block(bi, hazed_far=False):
    b = BLOCKS[bi]
    L = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
    fac = build_facade(bi, 100 * bi)
    warp_into(L, fac, [(0, 0), (fac.width, 0), (fac.width, fac.height), (0, fac.height)], facade_quad(b))
    # balconies: slab + rail card standing 1.1 m in front of the wall (real depth, occludes the wall)
    for fl in (1, 2, 3):
        for j in range(NBK):
            bay = b["bay0"] + j
            if bay not in BALC[bi]:
                continue
            sL = b["s_left"] - j * BAY - 0.25
            sR = b["s_left"] - (j + 1) * BAY + 0.25
            yb = storey_base(fl)
            nf = b["n"] - 1.1
            # side cheek (visible right side, in shade)
            cheek = to_img(np.full((20, 40, 3), (150, 153, 138), np.float32))
            warp_into(L, cheek, [(0, 0), (40, 0), (40, 20), (0, 20)],
                      [proj(sR, nf, yb + 1.05), proj(sR, b["n"], yb + 1.05), proj(sR, b["n"], yb - 0.1), proj(sR, nf, yb - 0.1)])
            rail = load_paper("loc_blank_0001.jpg", (128, 40), (172, 175, 160), 0.9, crop=(900 + 37 * j, 700 + 50 * fl, 1700, 1100))
            rail_img = to_img(rail)
            dr = ImageDraw.Draw(rail_img)
            dr.rectangle((0, 30, 128, 40), fill=(176, 178, 163, 255))       # slab edge (cream card)
            dr.rectangle((0, 0, 128, 4), fill=(73, 73, 55, 255))            # handrail
            for xx in range(4, 128, 6):
                dr.line((xx, 4, xx, 30), fill=(73, 73, 55, 255), width=1)  # balusters (olive)
            # the parapet card is perforated: between balusters the wall shows (alpha)
            al = np.full((40, 128), 255, np.uint8)
            for xx in range(4, 128, 6):
                al[5:30, xx + 1:xx + 6] = 70
            rail_img.putalpha(Image.fromarray(al))
            warp_into(L, rail_img, [(0, 0), (128, 0), (128, 40), (0, 40)],
                      [proj(sL, nf, yb + 1.05), proj(sR, nf, yb + 1.05), proj(sR, nf, yb - 0.1), proj(sL, nf, yb - 0.1)])
    # roof strips (zinc card bent over a quarter-cylinder former)
    rt = build_roof_tex(bi)
    rarr = np.asarray(rt).astype(np.float32)
    for t0, t1, src, dst in roof_strips(b):
        sh = shade_roof((t0 + t1) / 2)
        tex = rarr.copy(); tex[..., :3] *= sh
        warp_into(L, to_img(tex[..., :3]), src, dst)
    # dormers on the steep lower slope, every bay (pale card with a dark glazed recess)
    dt = build_dormer_tex()
    def n_roof(y):
        return b["n"] + RR * (1 - math.cos(math.asin(min(1.0, max(0.0, (y - HE) / RR)))))
    for j in range(NBK):
        sc = b["s_left"] - (j + 0.5) * BAY
        nd = b["n"] + 0.12
        y0 = HE + 0.30
        y1 = y0 + 1.55
        sL, sR = sc + 0.58, sc - 0.58
        cheek = to_img(np.full((10, 10, 3), (150, 166, 170), np.float32))
        warp_into(L, cheek, [(0, 0), (10, 0), (10, 10), (0, 10)],
                  [proj(sR, nd, y1), proj(sR, n_roof(y1) + 0.02, y1), proj(sR, n_roof(y0) + 0.02, y0 + 0.02), proj(sR, nd, y0)])
        warp_into(L, dt, [(0, 0), (dt.width, 0), (dt.width, dt.height), (0, dt.height)],
                  [proj(sL, nd, y1), proj(sR, nd, y1), proj(sR, nd, y0), proj(sL, nd, y0)])
        cap = to_img(np.full((10, 10, 3), (70, 84, 88), np.float32))
        yc = y1 + 0.28
        warp_into(L, cap, [(0, 0), (10, 0), (10, 10), (0, 10)],
                  [proj(sL + 0.06, n_roof(yc), yc), proj(sR - 0.06, n_roof(yc), yc), proj(sR - 0.06, nd - 0.06, y1), proj(sL + 0.06, nd - 0.06, y1)])
    # end wall last (it is nearest of this block's faces to a camera on its right)
    s, pts = end_wall(b)
    et = build_end_tex(bi)
    poly = [proj(s, n, y) for n, y in pts]
    src = [(0, 0), (et.width, 0), (et.width, et.height), (0, et.height)]
    top = HE + RR
    quad = [proj(s, b["n"], top), proj(s, b["n"] + DEPTH, top), proj(s, b["n"] + DEPTH, 0), proj(s, b["n"], 0)]
    tmp = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
    warp_into(tmp, et, src, quad)
    m = Image.new("L", (W2, H2), 0)
    ImageDraw.Draw(m).polygon(poly, fill=255)
    ta = np.asarray(tmp).copy()
    ta[..., 3] = np.minimum(ta[..., 3], np.asarray(m))
    L.alpha_composite(Image.fromarray(ta))
    # the zinc card's cut edge, seen in section along the curve (a thin slate rim) + paper cut-edge light
    rim = [proj(s, n, y) for n, y in pts[1:26]]
    ImageDraw.Draw(L).line(rim, fill=(88, 102, 108, 255), width=max(2, int(0.18 * F / depth(s, b["n"]))))
    ImageDraw.Draw(L).line([proj(s, b["n"], 0.4), proj(s, b["n"], HE)], fill=(206, 206, 192, 200), width=2)
    return L

def window_quad(bay, fl):
    b = BLOCKS[bay // NBK]
    j = bay % NBK
    u0 = b["s_left"] - (j * BAY + (BAY - WIN_W) / 2)
    u1 = u0 - WIN_W
    yb = storey_base(fl) + 0.22
    n = b["n"] + 0.02
    return [proj(u0, n, yb + WIN_H), proj(u1, n, yb + WIN_H), proj(u1, n, yb), proj(u0, n, yb)]

def build_far_block():
    """P1: a white block much further on, hazed (the reference's far left)."""
    L = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
    b = dict(s_left=150.0, n=15.0, bay0=0)
    s0, s1, n = 150.0, 112.0, 15.0
    a = load_paper("loc_blank_0001.jpg", (800, 400), (196, 200, 196), 0.6, crop=(500, 500, 2500, 1500))
    img = to_img(a)
    d = ImageDraw.Draw(img)
    for fl in range(6):
        for j in range(14):
            d.rectangle((j * 57 + 14, fl * 62 + 30, j * 57 + 40, fl * 62 + 62), fill=(132, 142, 144, 255))
    warp_into(L, img, [(0, 0), (800, 0), (800, 400), (0, 400)], [proj(s0, n, 19), proj(s1, n, 19), proj(s1, n, 0), proj(s0, n, 0)])
    endq = [proj(s1, n, 19), proj(s1, n + 12, 19), proj(s1, n + 12, 0), proj(s1, n, 0)]
    e = to_img(np.full((20, 20, 3), (178, 184, 182), np.float32))
    warp_into(L, e, [(0, 0), (20, 0), (20, 20), (0, 20)], endq)
    return L

# ---------------------------------------------------------- ground & co ---
def ground_quad(n0, n1, s0=-40.0, s1=260.0):
    return [proj(s1, n1, 0), proj(s0, n1, 0), proj(s0, n0, 0), proj(s1, n0, 0)]

def clip_near(n0, n1, s0, s1):
    """keep the ground quad in front of the camera (Z > 1.5 m)."""
    def zok(s, n):
        return depth(s, n) > 1.5
    while not (zok(s0, n0) and zok(s0, n1)):
        s0 += 1.0
    return s0, s1

def build_ground():
    L = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
    # far grass strip behind the hedge (seen in the block gaps)
    g = load_paper("p3.jpg", (400, 200), (88, 108, 70), 0.35)
    s0, s1 = clip_near(14.0, 30.0, -10.0, 260.0)
    warp_into(L, to_img(g), [(0, 0), (400, 0), (400, 200), (0, 200)], ground_quad(14.0, 30.0, s0, s1))
    return L

def build_road():
    """P5: far pavement (11-13.6 m), road (4.2-11 m) with dashed centre line, near kerb."""
    L = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
    s0, s1 = clip_near(3.0, 13.6, -12.0, 260.0)
    ln = s1 - s0
    PX = 12
    w, h = int(ln * PX), int((13.6 - 3.0) * 40)
    road = tiled_kraft((w, h), (97, 115, 113), 0.45, rot=90, ox=77)
    img = to_img(road)
    d = ImageDraw.Draw(img)
    def vy(n):
        return (13.6 - n) * 40
    pav = load_paper("loc_blank_0001.jpg", (w, int(2.6 * 40)), (128, 136, 132), 0.7, crop=(500, 400, 2800, 900))
    img.paste(to_img(pav), (0, 0))
    d.rectangle((0, vy(11.15), w, vy(11.0)), fill=(150, 156, 150, 255))        # far kerb (lit top)
    d.rectangle((0, vy(11.0), w, vy(10.9)), fill=(84, 98, 98, 255))
    d.rectangle((0, vy(5.45), w, vy(5.3)), fill=(144, 152, 146, 255))          # edge line
    # dashed centre line: 3 m dashes, 9 m period (white card strips laid on the road)
    for sx in np.arange(0, ln, 9.0):
        x0 = sx * PX
        d.polygon(hand_poly([(x0, vy(8.18)), (x0 + 3.0 * PX, vy(8.18)), (x0 + 3.0 * PX, vy(8.02)), (x0, vy(8.02))], 0.4, int(sx)),
                  fill=(168, 176, 172, 255))
    d.rectangle((0, vy(3.0) - 12, w, h), fill=(110, 120, 112, 255))           # near kerb / gutter strip
    src = [(w, 0), (0, 0), (0, h), (w, h)]
    dst = [proj(s0, 13.6, 0), proj(s1, 13.6, 0), proj(s1, 3.0, 0), proj(s0, 3.0, 0)]
    # orientation: texture x runs s1 -> s0 left to right; map s=s1 at x=0
    src = [(0, 0), (w, 0), (w, h), (0, h)]
    dst = [proj(s1, 13.6, 0), proj(s0, 13.6, 0), proj(s0, 3.0, 0), proj(s1, 3.0, 0)]
    warp_into(L, img, src, dst)
    return L

def build_verge():
    """P6: our grass verge, a wedge at lower left (n < 3)."""
    L = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
    s0, s1 = clip_near(-4.0, 5.0, -12.0, 260.0)
    v = load_paper("p3.jpg", (1600, 300), (78, 102, 56), 0.45)
    img = to_img(v)
    m = Image.new("L", (1600, 300), 255)
    r = np.random.RandomState(4)
    pts = [(0, 300), (0, 6)] + [(x, 4 + r.normal(0, 2)) for x in range(0, 1601, 8)] + [(1600, 300)]
    m2 = Image.new("L", (1600, 300), 0); ImageDraw.Draw(m2).polygon(pts, fill=255)
    img.putalpha(m2)
    warp_into(L, img, [(0, 0), (1600, 0), (1600, 300), (0, 300)],
              [proj(s1, 5.0, 0), proj(s0, 5.0, 0), proj(s0, -4.0, 0), proj(s1, -4.0, 0)])
    return L

LEAF_COLS = [(40, 54, 34), (48, 63, 41), (58, 74, 48), (70, 86, 56), (36, 48, 30)]

def build_hedge():
    """P4 hedge: a clipped hedge 1.25 m high at n = 13.9-14.8, built from thousands of cut leaf stamps."""
    L = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    r = np.random.RandomState(77)
    kr = tiled_kraft((256, 256), (48, 63, 41), 0.8)
    # body (dark interior) first: the hedge's front face as a polygon
    s0, s1 = clip_near(13.9, 13.9, -12.0, 230.0)
    def top(s):
        return 1.25 + 0.05 * math.sin(s * 1.3) + 0.04 * math.sin(s * 3.7 + 1)
    body = [proj(s, 13.9, top(s) - 0.12) for s in np.arange(s0, s1, 0.5)] + [proj(s1, 13.9, 0), proj(s0, 13.9, 0)]
    d.polygon(body, fill=(34, 46, 28, 255))
    # leaves: back-to-front, dark to light (inner shade to outer lit tips)
    ss = np.arange(s0, s1, 0.05)
    for layer in range(3):
        for s in ss:
            z = depth(s, 13.9)
            pxm = F / z
            if pxm < 6 and r.rand() < 0.6:
                continue
            for _ in range(2 if pxm > 12 else 1):
                y = r.rand() ** 0.6 * top(s) - 0.02 + layer * 0.03
                n = 13.9 - 0.05 * layer
                x, yy = proj(s + r.normal(0, 0.03), n, y)
                L_ = max(1.6, 0.11 * pxm)
                ang = r.rand() * math.pi
                c = LEAF_COLS[min(4, int(r.rand() * 3) + layer)] if layer < 2 else LEAF_COLS[int(r.rand() * 4) + 0]
                if layer == 2 and r.rand() < 0.5:
                    c = (66, 82, 52)
                dx, dy = math.cos(ang) * L_, math.sin(ang) * L_ * 0.55
                d.polygon([(x - dx, yy - dy), (x + dy * 0.5, yy - dx * 0.35), (x + dx, yy + dy), (x - dy * 0.5, yy + dx * 0.35)], fill=c + (255,))
    # fibre: modulate by the kraft scan so leaves read as cut paper
    a = np.asarray(L).astype(np.float32)
    tile = np.tile(kr, (H2 // 256 + 1, W2 // 256 + 1, 1))[:H2, :W2]
    a[..., :3] *= (tile / np.array([48, 63, 41], np.float32)) ** 0.5
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

def sapling_strokes(s, n, k, seed, height):
    """3D bare sapling in the plane parallel to the facade; sway on two incommensurate oscillators."""
    t = k / FPS
    sway = math.radians(1.5) * (0.6 * math.sin(2 * math.pi * 0.37 * t + seed) + 0.4 * math.sin(2 * math.pi * 0.23 * t + 2 * seed))
    r = np.random.RandomState(seed)
    out = []
    def br(x0, y0, ang, length, width, depth_):
        x1 = x0 + math.sin(ang) * length
        y1 = y0 + math.cos(ang) * length
        out.append((x0, y0, x1, y1, width))
        if depth_ == 0:
            return
        kids = 2 if (depth_ < 3 or r.rand() < 0.5) else 3
        for c in range(kids):
            da = (-0.45 + 0.9 * c / max(1, kids - 1)) * (0.6 + 0.7 * r.rand()) + r.normal(0, 0.22)
            br(x1, y1, ang * 0.6 + da * 0.75 + sway * (6 - depth_) * 0.6, length * (0.6 + 0.15 * r.rand()), width * 0.62, depth_ - 1)
    trunk_h = height * 0.30
    out.append((0, 0, math.sin(sway) * trunk_h, trunk_h, 0.16))
    for c in range(3):
        br(math.sin(sway) * trunk_h * (0.75 + 0.25 * c / 2), trunk_h * (0.75 + 0.25 * c / 2),
           -0.42 + c * 0.42 + r.normal(0, 0.15) + sway, height * (0.26 + 0.08 * r.rand()), 0.085, 4)
    # strokes in screen space: x offset along the street (s), y height
    res = []
    for x0, y0, x1, y1, wdt in out:
        p0 = proj(s - x0, n, y0); p1 = proj(s - x1, n, y1)
        pxm = F / depth(s, n)
        res.append((p0, p1, max(1.0, wdt * pxm)))
    return res

SAPLINGS = []   # (s, n, seed, height), set in setup()

def setup_saplings():
    out = []
    # one between every second bay on the strip between hedge and wall, avoiding window 16's line of sight
    for blk in BLOCKS:
        for j in range(0, NBK + 1, 2):
            s = blk["s_left"] - j * BAY + 0.0
            out.append((s + 0.2, blk["n"] - 2.6, len(out) + 3, 7.5 + (len(out) % 3) * 0.8))
    for s in (blk["s_left"] + 3.5 for blk in BLOCKS):
        out.append((s, 16.0, len(out) + 3, 8.0))
    # remove any whose crown would cross window 16
    q = window_quad(16, 0)
    wx0, wx1 = min(p[0] for p in q) - 6, max(p[0] for p in q) + 6
    keep = []
    for sp in out:
        xs = [p for st in sapling_strokes(sp[0], sp[1], 492, sp[2], sp[3]) for p in (st[0][0], st[1][0])]
        if max(xs) < wx0 or min(xs) > wx1:
            keep.append(sp)
    return keep

def draw_saplings(k):
    L = Image.new("L", (W2, H2), 0)
    d = ImageDraw.Draw(L)
    for s, n, seed, h in SAPLINGS:
        for p0, p1, w in sapling_strokes(s, n, k, seed, h):
            d.line((p0[0], p0[1], p1[0], p1[1]), fill=255, width=int(round(w)))
    return L

def build_fence():
    """P7: a dark post at the right edge with a wire mesh panel (near: real fibre visible)."""
    L = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
    m = Image.new("L", (W2, H2), 0)
    d = ImageDraw.Draw(m)
    # post standing 1.25 m on our verge, about 4.6 m from the camera, near the right frame edge
    X, Z = 2.95, 4.3
    def P(X_, Z_, y):
        return (CX + F * X_ / Z_, CY - F * (y - EYE) / Z_)
    xL, yT = P(X, Z, 1.25); xR, _ = P(X + 0.09, Z, 1.25)
    _, yB = P(X, Z, -0.1)
    d.polygon(hand_poly([(xL, yT), (xR, yT - 2), (xR + 1, yB), (xL - 1, yB)], 0.8, 5), fill=255)
    d.ellipse((xL - 3, yT - 7, xR + 3, yT + 5), fill=255)
    # mesh panel going right toward the camera-side (receding a little)
    for i in range(1, 7):
        yy = 1.2 - i * 0.2
        a = P(X + 0.09, Z, yy); b_ = P(X + 1.6, Z - 0.9, yy + 0.06)
        d.line((a[0], a[1], b_[0], b_[1]), fill=210, width=2)
    for i in range(1, 9):
        xx = X + 0.09 + i * 0.18
        zz = Z - 0.9 * i * 0.18 / 1.51
        a = P(xx, zz, 1.22); b_ = P(xx - 0.08, zz, -0.1)
        d.line((a[0], a[1], b_[0], b_[1]), fill=210, width=2)
    tex = tiled_kraft((W2, H2), (60, 69, 61), 0.7, rot=90)
    img = to_img(tex)
    img.putalpha(m)
    return img

# ---------------------------------------------------------------- cache ---
LAYER_NAMES = ["sky", "p1far", "ground", "blk0", "blk1", "blk2", "hedge", "road", "verge", "fence"]
LAYER_Z = {"p1far": 120.0, "ground": 26.0, "blk0": 70.0, "blk1": 45.0, "blk2": 24.0, "hedge": 19.0,
           "road": 13.0, "verge": 8.0, "fence": 4.3, "trees": 21.0}

def build_sky():
    top = np.array([245, 235, 241], np.float32)
    low = np.array([234, 225, 239], np.float32)
    yy = np.linspace(0, 1, H2)[:, None, None] / 0.865
    sky = top + (low - top) * np.clip(yy, 0, 1)
    fib = load_paper("loc_blank_0001.jpg", (W2, H2), (0, 0, 0), 0.10, crop=(500, 400, 2800, 2200))
    return to_img(sky + fib)

def build_all():
    os.makedirs(CACHE, exist_ok=True)
    layers = {"sky": build_sky(), "p1far": build_far_block(), "ground": build_ground(),
              "blk0": render_block(0), "blk1": render_block(1), "blk2": render_block(2),
              "hedge": build_hedge(), "road": build_road(), "verge": build_verge(), "fence": build_fence()}
    for k, v in layers.items():
        v.save(os.path.join(CACHE, k + ".png"))
    # lit-window masks (screen space) for every scored window
    masks = {}
    for i in LIGHT:
        fl, bay = divmod(i, 24)
        q = window_quad(bay, fl)
        m = Image.new("L", (W2, H2), 0)
        ImageDraw.Draw(m).polygon(q, fill=255)
        masks[i] = q
    np.save(os.path.join(CACHE, "winquads.npy"), {i: masks[i] for i in masks}, allow_pickle=True)

_L = {}
def layers():
    if not _L:
        for n in LAYER_NAMES:
            _L[n] = np.asarray(Image.open(os.path.join(CACHE, n + ".png"))).astype(np.float32)
    return _L

# -------------------------------------------------------------- window 16 ---
def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)

def rise_y(k):
    """f502-518: rises from below the sill with weight (slow start, a 3 % overshoot, settle)."""
    if k < 502:
        return 1.0
    x = (k - 502) / 16.0
    if x < 1:
        return 1.0 - ease(x) * 1.03
    s = k - 518
    return -0.03 * math.exp(-s / 2.5) * math.cos(s * 0.9) + 0.004 * math.sin(k / FPS * 2 * math.pi / 3.4)

def yaw_deg(k):
    """f538-552: 0 -> 25 deg toward the road, peaking at 27 (overshoot), settling over 6 frames."""
    if k < 538:
        return 0.0
    if k <= 552:
        return 27.0 * ease((k - 538) / 14.0)
    s = k - 552
    return 25.0 + (2.0 * (1 - s / 6.0) * math.cos(s / 6.0 * math.pi / 2) if s < 6 else 0.0)

def curtain_dx(k):
    """f552-566: the tissue curtain's edge slides 8 % of the window width and settles with a small rebound."""
    if k < 552:
        return 0.0
    x = (k - 552) / 14.0
    if x >= 1:
        return 1.0
    return ease(min(1, x * 1.25)) + 0.12 * math.sin(math.pi * min(1, x * 1.25)) * (1 - x)

def window16_tex(k, lit):
    """Window 16 at 8 px/cm-ish: back-lit tissue, black-card silhouette articulated at the neck."""
    w, h = 145 * 2, 230 * 2
    amber = np.array([240, 190, 110], np.float32)
    recess = np.array([74, 85, 86], np.float32) * 0.85
    yy, xx = np.mgrid[0:h, 0:w]
    fall = 1 - 0.25 * (((xx - w * 0.55) / w) ** 2 + ((yy - h * 0.30) / h) ** 2)
    col = recess + (amber * fall[..., None] - recess) * lit
    sil = Image.new("L", (w, h), 0)
    sd = ImageDraw.Draw(sil)
    ry = rise_y(k)
    off = ry * h * 0.98
    yaw = math.radians(yaw_deg(k))
    # shoulders / torso card (pivot: neck)
    ncx, ncy = w * 0.42, h * 0.40 + off
    sd.polygon([(w * 0.02, h + 4), (w * 0.06, ncy + h * 0.16), (w * 0.20, ncy + h * 0.08), (ncx - w * 0.08, ncy + h * 0.05),
                (ncx + w * 0.10, ncy + h * 0.05), (w * 0.66, ncy + h * 0.09), (w * 0.78, ncy + h * 0.17), (w * 0.82, h + 4)], fill=255)
    sd.rectangle((ncx - w * 0.075, ncy - h * 0.04, ncx + w * 0.075, ncy + h * 0.08), fill=255)
    # head (second card, pinned at the neck): profile toward the left (along the street, the door);
    # the yaw turns the face toward the road (the viewer): nose shortens, the bun slides behind.
    phi = math.radians(-80.0) + yaw * 1.0
    fx = math.sin(phi)
    hr = w * 0.215
    hc = (ncx - fx * hr * 0.12, ncy - hr * 1.05)
    tilt = math.radians(4) * yaw / math.radians(25)
    sd.ellipse((hc[0] - hr * 0.86, hc[1] - hr, hc[0] + hr * 0.86, hc[1] + hr), fill=255)
    ny = hc[1] + hr * 0.05 + tilt * hr * 1.5
    sd.polygon([(hc[0] + fx * hr * 0.70, ny - hr * 0.40), (hc[0] + fx * hr * 1.14, ny + hr * 0.10), (hc[0] + fx * hr * 0.72, ny + hr * 0.24)], fill=255)
    sd.polygon([(hc[0] + fx * hr * 0.72, hc[1] + hr * 0.45), (hc[0] + fx * hr * 0.88, hc[1] + hr * 0.66), (hc[0] + fx * hr * 0.30, hc[1] + hr * 0.92)], fill=255)
    bx = hc[0] - fx * hr * 0.92
    sd.ellipse((bx - hr * 0.40, hc[1] - hr * 0.80, bx + hr * 0.40, hc[1] - hr * 0.02), fill=255)
    # leaning to the glass while turning: the shadow on the tissue sharpens (focus as the event)
    lean = ease((k - 536) / 16.0)
    sil = sil.filter(ImageFilter.GaussianBlur(16.0 * (1.0 - 0.6 * lean)))
    sa = np.asarray(sil).astype(np.float32)[..., None] / 255.0
    shadow = np.array([44, 36, 32], np.float32)
    col = col * (1 - sa * 0.9 * lit) + shadow * sa * 0.9 * lit
    # curtain: a second tissue over the right third; its edge slides then settles
    cx = w * (0.70 - 0.08 * curtain_dx(k))
    edge = cx + np.sin(np.arange(h) / 14.0) * 3
    curt = (np.arange(w)[None, :] >= edge[:, None]).astype(np.float32)
    curt = np.asarray(Image.fromarray((curt * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(4))).astype(np.float32)[..., None] / 255
    col = col * (1 - curt * 0.38) + np.array([250, 226, 176], np.float32) * curt * 0.38 * lit + col * curt * 0.38 * (1 - lit)
    img = to_img(col)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, w, 18), fill=(54, 62, 63, 255))                       # reveal in shadow
    d.rectangle((0, 0, 9, h), fill=(62, 71, 72, 255))
    d.line((0, 48, w, 48), fill=(150, 150, 138, 255), width=4)               # transom
    d.rectangle((0, h - 72, w, h - 66), fill=(73, 73, 55, 255))              # guard rail
    for xx_ in range(10, w, 14):
        d.line((xx_, h - 66, xx_, h), fill=(80, 80, 62, 255), width=2)
    return img

# ---------------------------------------------------------------- frame ---
def cam_dx(k):
    """lateral drift of the last 8 cm, easing to rest on f492 (window 16 lights on a still frame)."""
    x = min(1.0, max(0.0, (k - K0) / (492 - K0)))
    return -0.08 * (1 - (1 - (1 - x) ** 3)) if x < 1 else 0.0

def shift(a, dx):
    if abs(dx) < 1e-3:
        return a
    P = 48                                           # edge-padded so the sheet never shows its cut end
    ap = np.pad(np.clip(a, 0, 255).astype(np.uint8), ((0, 0), (P, P), (0, 0)), mode="edge")
    im = Image.fromarray(ap, "RGBA" if a.shape[2] == 4 else "RGB")
    im = im.transform(im.size, Image.AFFINE, (1, 0, -dx, 0, 1, 0), Image.BILINEAR)
    return np.asarray(im).astype(np.float32)[:, P:-P]

def over(base, layer, shadow=False):
    a = layer[..., 3:4] / 255.0
    if shadow:
        sh = Image.fromarray(layer[..., 3].astype(np.uint8)).filter(ImageFilter.GaussianBlur(5))
        sh = np.asarray(sh.transform(sh.size, Image.AFFINE, (1, 0, -3, 0, 1, -4))).astype(np.float32)[..., None] / 255.0 * 0.30
        base[..., :3] = base[..., :3] * (1 - sh) + np.array([30, 36, 32], np.float32) * sh
    base[..., :3] = base[..., :3] * (1 - a) + layer[..., :3] * a
    return base

def haze(base, amount, k_E):
    """fog sheet between planes: denser low (toward the hedge line), thinning with height."""
    ys = np.arange(H2)[:, None, None] / H2
    dens = amount * (0.35 + 0.65 * np.clip((ys - 0.05) / 0.74, 0, 1) ** 1.4)
    col = np.array([232, 226, 234], np.float32) * (0.92 + 0.08 * k_E)
    base[..., :3] = base[..., :3] * (1 - dens) + col * dens
    return base

def blur(a, r):
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
    return np.asarray(im.filter(ImageFilter.GaussianBlur(r))).astype(np.float32)

_QUADS = None
def frame(k):
    global _QUADS
    Ls = layers()
    if _QUADS is None:
        _QUADS = np.load(os.path.join(CACHE, "winquads.npy"), allow_pickle=True).item()
    E = exposure(k)
    dxm = cam_dx(k)
    def sh(name, a):
        return shift(a, -F * dxm / LAYER_Z[name])
    dmix = (0.93 - E) / 0.15 * 0.40
    sky = Ls["sky"].copy()
    sky[..., :3] = sky[..., :3] + (np.array([205, 205, 215], np.float32) - sky[..., :3]) * dmix
    sky[..., :3] *= (0.97 + 0.03 * E)
    can = sky
    def lit_block(name, bays):
        a = Ls[name].copy()
        a[..., :3] *= E
        img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
        d = ImageDraw.Draw(img, "RGBA")
        for i, q in _QUADS.items():
            fl, bay = divmod(i, 24)
            if bay not in bays or i == 16:
                continue
            g = glow(i, k)
            if g <= 0:
                continue
            rec = np.array([74, 85, 86]) * E
            c = rec + (np.array([240, 190, 110]) - rec) * min(1.02, g)
            # lit glass only above the guard rail; the rail and mullion stay dark against the lamp
            d.polygon(q, fill=tuple(int(v) for v in c) + (255,))
            (xa, ya), (xb, yb_), (xc, yc), (xd, yd) = q
            def lerp(p, r_, t):
                return (p[0] + (r_[0] - p[0]) * t, p[1] + (r_[1] - p[1]) * t)
            top_l, top_r = q[0], q[1]
            bot_r, bot_l = q[2], q[3]
            d.line([lerp(top_l, bot_l, 0.08), lerp(top_r, bot_r, 0.08)], fill=(int(60 * E), int(66 * E), int(66 * E), 255), width=2)
            d.line([lerp(top_l, top_r, 0.5), lerp(bot_l, bot_r, 0.5)], fill=(int(150 * E), int(140 * E), int(112 * E), 255), width=2)
            ra, rb = lerp(top_l, bot_l, 0.84), lerp(top_r, bot_r, 0.84)
            d.line([ra, rb], fill=(int(73 * E), int(73 * E), int(55 * E), 255), width=2)
            for t in np.linspace(0.08, 0.92, 7):
                d.line([lerp(ra, rb, t), lerp(lerp(bot_l, bot_r, t), lerp(bot_l, bot_r, t), 0)], fill=(int(80 * E), int(80 * E), int(62 * E), 210), width=1)
        if 16 in bays:
            q = _QUADS[16]
            t16 = window16_tex(k, glow(16, k))
            warp_into(img, t16, [(0, 0), (t16.width, 0), (t16.width, t16.height), (0, t16.height)], q)
        return np.asarray(img).astype(np.float32)
    far = Ls["p1far"].copy(); far[..., :3] *= E
    can = over(can, blur(sh("p1far", far), 1.6))
    can = haze(can, 0.40, E)
    g = Ls["ground"].copy(); g[..., :3] *= E
    can = over(can, sh("ground", g))
    can = over(can, blur(sh("blk0", lit_block("blk0", range(0, 8))), 1.0))
    can = haze(can, 0.16, E)
    can = over(can, blur(sh("blk1", lit_block("blk1", range(8, 16))), 0.5), shadow=True)
    can = haze(can, 0.08, E)
    can = over(can, sh("blk2", lit_block("blk2", range(16, 24))), shadow=True)
    can = haze(can, 0.035, E)
    # saplings (cut card), then hedge, road, verge, fence: each a sheet with a soft overcast shadow
    tm = np.asarray(draw_saplings(k)).astype(np.float32)
    tt = np.zeros((H2, W2, 4), np.float32)
    tt[..., :3] = np.array([114, 124, 105], np.float32) * E * 0.92
    tt[..., 3] = tm
    can = over(can, sh("trees", tt), shadow=True)
    for name in ("hedge", "road", "verge", "fence"):
        a = Ls[name].copy(); a[..., :3] *= E
        can = over(can, sh(name, a), shadow=name in ("hedge", "fence"))
    out = Image.fromarray(np.clip(can[..., :3], 0, 255).astype(np.uint8))
    return out.resize((PW, PH), Image.LANCZOS)

SAPLINGS = setup_saplings()

if __name__ == "__main__":
    if sys.argv[1] == "build":
        build_all()
        print("cached")
    else:
        out = sys.argv[2]
        os.makedirs(out, exist_ok=True)
        ks = [int(a) for a in sys.argv[3:]] or list(range(K0, K1))
        for k in ks:
            frame(k).save(os.path.join(out, f"f{k:04d}.png"))

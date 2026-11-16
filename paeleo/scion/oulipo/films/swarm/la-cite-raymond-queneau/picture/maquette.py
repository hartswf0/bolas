"""La Cité Raymond Queneau · picture master (plan-r3) · the paper maquette.

frame(k) -> 960x464 RGB PIL image, k = 0..719, a pure function of k.

A handmade cut-paper model of three staggered cream blocks (plus a hazed fourth) receding on a
diagonal to the left, with curved zinc roofs, dormers, balconies, a hedge, saplings, a road, a
grass verge, a fence post and a swan-neck lamp post.  Every face is a sheet cut (hand-jittered
polygon) from a FORAGED paper scan (picture/ledger.json) graded only by per-channel levels toward
the palette of plan section 7, given a soft overcast drop shadow (offset <= 3 px, blur >= 6 px)
and a 1 px lighter cut edge.  The sheets are photographed in two set-ups of the model (the wide
eye-level view across the road, and the closer key view of the near block) and then laid out as
eight multiplane planes that the camera tracks / pushes through at their declared ratios.

Techniques (swarms.json):
  #5 Norstein multiplane: P0 sky 0.00, P1 haze far block 0.15, P2 far + mid blocks 0.35,
     P3 near block 0.55, P4 saplings + hedge 0.75, P5 road/pavement 0.90, P6 verge 1.00,
     P7 fence post + lamp post 1.25.  Plane offset = ratio * X(k); S2 push-in scale
     1 + 0.18 * ratio * u(k).  Fog sheets between planes, denser low.  Exposure schedule
     1.00 / 0.93 / 0.78 / 0.70 (dusk = less light on the paper, not a tint).
  #6 Whitney: window i lights at step s(i) = 37 i mod 96 (frame round(24 (6.1 + 0.9 s))),
     3-frame attack, each lit window breathes 0.5 % (period 3.1 s, phase 2 pi i / 96).
     Saplings sway on 0.37 Hz + 0.23 Hz (1.5 deg at the base, more with height).
  #47 Sound-to-action: walker step contacts, door, silhouette rise / hold / head turn /
     curtain, lamp, cuts: the PictureEvents that the sound teams' CueClaims anchor to.
  #32 FK walker (articulated paper cutout, joint angles per frame), #45 occlusion (door jamb,
     hedge gap, fence, lamp post), #41 secondary motion (bag lag, curtain settle, head overshoot).

Window numbering (plan section 6): i = floor*24 + bay; floor 0 = top floor; the near block
(the row of three staggered volumes) has 24 bays: 0-7 far volume, 8-15 middle, 16-23 near;
the entrance door is under bay 16.

Usage: python3 -I maquette.py build          (cache the static sheets for both set-ups)
       python3 -I maquette.py frames <dir> k...
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = "/home/user/bolas/paeleo/scion/oulipo/films/sources/la-cite-raymond-queneau/picture"
CACHE = os.path.join(SRC, "cache")
PW, PH = 960, 464
SS = 2
W2, H2 = PW * SS, PH * SS
FPS = 24
NFR = 720
ML, MR = 300, 700          # cached-canvas margins (SS px) for the lateral tracks
CW = W2 + ML + MR

# ================================================================== score ===
def step_of(i):
    return (37 * i) % 96

def light_frame(i):
    s = step_of(i)
    return int(round(FPS * (6.1 + 0.9 * s))) if s <= 21 else None

LIGHT = {i: light_frame(i) for i in range(96) if light_frame(i) is not None}
assert LIGHT[16] == 492 and LIGHT[47] == 384 and LIGHT[0] == 146 and len(LIGHT) == 22
W16_OFF = 696

def glow(i, k):
    f = LIGHT.get(i)
    if f is None or k < f - 2:
        return 0.0
    if i == 16 and k >= W16_OFF:
        return 0.0
    a = min(1.0, (k - (f - 3)) / 3.0)            # 3-frame attack: f-2, f-1, f (full on the score frame)
    return a * (1.0 + 0.005 * math.sin(2 * math.pi * (k / FPS) / 3.1 + 2 * math.pi * i / 96))

# ================================================================= shots ===
SHOTS = [dict(id="S1", k0=0, k1=191, cam="wide"), dict(id="S2", k0=192, k1=383, cam="tele"),
         dict(id="S3", k0=384, k1=623, cam="key"), dict(id="S4", k0=624, k1=719, cam="wide")]

def shot_of(k):
    for s in SHOTS:
        if s["k0"] <= k <= s["k1"]:
            return s
    raise ValueError(k)

def smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)

def exposure(k):
    if k < 192:
        return 1.00
    if k < 384:
        return 1.00 - 0.07 * (k - 192) / 191.0
    if k < 624:
        return 0.93 - 0.15 * (k - 384) / 239.0
    return 0.78 - 0.08 * (k - 624) / 95.0

def track_X(k):
    """lateral offset of P6 (ratio 1.00) in final px; scene moves right = camera tracks left."""
    if k < 192:
        x = k / 191.0
        return 64.0 * (x * x * (3 - 2 * x) * 0.5 + x * x * 0.5) if x < 1 else 64.0   # ease-in
    if k < 384:
        return 64.0 + 32.0 * (k - 192) / 192.0                                       # half speed
    if k < 624:
        return 0.0
    x = (k - 624) / 95.0
    return -220.0 * (0.25 * x * x + 0.75 * x) / 1.0 if x <= 1 else -220.0            # tracks right

def push_u(k):
    if 192 <= k < 384:
        return smooth((k - 192) / 191.0)
    return 0.0

RATIOS = dict(P0=0.00, P1=0.15, P2=0.35, P3=0.55, P4=0.75, P5=0.90, P6=1.00, P7=1.25)

# ================================================================ cameras ===
ANG = math.radians(47.0)
D = np.array([-math.cos(ANG), math.sin(ANG)])     # street direction, toward far-left
NV = np.array([math.sin(ANG), math.cos(ANG)])     # from the camera toward the blocks
EYE = 1.5
CAMS = {
    # eye level 1.5 m from our side of the road, across verge + road; horizon 0.60 H
    "wide": dict(F=760.0 * SS, CX=ML + W2 * 0.50, CY=H2 * 0.60, CAM_S=-11.0, NOFF=16.0),
    # the key set-up (approved test shot): closer, horizon low, window 16 right of centre
    "key": dict(F=610.0 * SS, CX=ML + W2 * 0.50, CY=H2 * 0.865, CAM_S=2.2, NOFF=0.0),
}
# r3: S2 is the same eye-level position with a 2.4x longer lens (the documentary zoom-in), centred on
# the entrance, so the walker reads at ~65 px; horizon 0.50 H.
TELE = 3.4
def _tele():
    w = CAMS["wide"]
    p = (20.2 - w["CAM_S"]) * np.array([-math.cos(math.radians(47.0)), math.sin(math.radians(47.0))]) + \
        (19.0 + w["NOFF"]) * np.array([math.sin(math.radians(47.0)), math.cos(math.radians(47.0))])
    F = w["F"] * TELE
    return dict(F=F, CX=ML + W2 * 0.50 - F * p[0] / p[1], CY=H2 * 0.50, CAM_S=w["CAM_S"], NOFF=w["NOFF"])
CAMS["tele"] = _tele()
C = dict(CAMS["wide"])

def use_cam(name):
    C.clear(); C.update(CAMS[name]); C["name"] = name

def world(s, n):
    p = (s - C["CAM_S"]) * D + (n + C["NOFF"]) * NV
    return p[0], p[1]

def proj(s, n, y):
    X, Z = world(s, n)
    return (C["CX"] + C["F"] * X / Z, C["CY"] - C["F"] * (y - EYE) / Z)

def depth(s, n):
    return world(s, n)[1]

def push_center(cam):
    """the S2 push-in centres on the entrance (door under bay 16), at the horizon."""
    use_cam(cam)
    x, _ = proj(20.2, 19.0, 1.2)
    return x - ML, C["CY"]

# ================================================================== model ===
BAY, NBK = 3.2, 8
GF, FL = 3.0, 2.6
HE = GF + 4 * FL
RR = 6.6          # r3: a full, tall curved zinc roof (reference): elliptical quarter, rise RR, run RN
RN = 3.6
DEPTH = 12.0
WIN_W, WIN_H = 1.45, 1.85
BLOCKS = [dict(name="far", s_left=88.0, n=17.0, bay0=0),
          dict(name="mid", s_left=55.0, n=18.0, bay0=8),
          dict(name="near", s_left=22.0, n=19.0, bay0=16)]
LEN = BAY * NBK
DOOR_S0, DOOR_S1 = 22.0 - 0.95, 22.0 - 0.95 - 1.6      # door opening under bay 16 (street coords)
DOOR_H = 2.45
PATH_S = 0.5 * (DOOR_S0 + DOOR_S1)

def storey_base(fl):
    return GF + (3 - fl) * FL

# ------------------------------------------------------------ paper -----
_PAPER = {}
def paper_img(name):
    if name not in _PAPER:
        _PAPER[name] = Image.open(os.path.join(SRC, name)).convert("RGB")
    return _PAPER[name]

def load_paper(name, size, target, contrast, crop=None, native=False, gamma_lo=None):
    """a foraged scan, cropped (clean area) and graded ONLY by per-channel levels toward target."""
    im = paper_img(name)
    if crop:
        im = im.crop(crop)
    w, h = im.size
    tw, th = size
    if w >= tw and h >= th and native:
        im = im.crop((0, 0, tw, th))
    else:
        sc = max(tw / w, th / h)
        im = im.resize((int(w * sc) + 2, int(h * sc) + 2), Image.BICUBIC).crop((0, 0, tw, th))
    a = np.asarray(im).astype(np.float32)
    med = np.median(a.reshape(-1, 3), axis=0)
    return np.clip((a - med) * contrast + np.array(target, np.float32), 0, 255)

LOC_CLEAN = (420, 260, 2900, 2330)

def tiled(name, size, target, contrast, rot=0, ox=0, tile=1024):
    im = paper_img(name)
    if rot:
        im = im.rotate(rot)
    w, h = size
    big = Image.new("RGB", (w + tile, h + tile))
    for x in range(0, w + tile, tile):
        for y in range(0, h + tile, tile):
            big.paste(im, (x, y))
    big = big.crop((ox % tile, 0, ox % tile + w, h))
    a = np.asarray(big).astype(np.float32)
    med = np.median(a.reshape(-1, 3), axis=0)
    return np.clip((a - med) * contrast + np.array(target, np.float32), 0, 255)

def kraft(size, target, contrast, rot=0, ox=0):
    return tiled("kraft_tileable.png", size, target, contrast, rot, ox)

def sheet_warp(a, seed, amp=0.035):
    """a slight buckle of the sheet: low-frequency light fall-off across a not-quite-flat card."""
    h, w = a.shape[:2]
    r = np.random.RandomState(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    f = (np.sin(2 * math.pi * (xx / w * (0.8 + r.rand()) + yy / h * (0.4 * r.rand())) + r.rand() * 6)
         * 0.6 + np.sin(2 * math.pi * (yy / h * (1.0 + r.rand())) + r.rand() * 6) * 0.4)
    return a * (1.0 + amp * f[..., None])

# ---------------------------------------------------------- warping -----
def homography(src, dst):
    Am, bm = [], []
    for (x, y), (u, v) in zip(dst, src):
        Am.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); bm.append(u)
        Am.append([0, 0, 0, x, y, 1, -v * x, -v * y]); bm.append(v)
    return np.linalg.solve(np.array(Am, float), np.array(bm, float))

def hand_poly(pts, jit, seed, step=10):
    r = np.random.RandomState(seed)
    out = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        n = max(2, int(math.hypot(x1 - x0, y1 - y0) / step))
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append((x0 + (x1 - x0) * t + r.normal(0, jit), y0 + (y1 - y0) * t + r.normal(0, jit)))
    return out

def warp_into(canvas, tex, src_quad, dst_quad, mask_poly=None, edge=None, seed=0, jit=0.0, shadow=0.0):
    """warp an RGBA sheet onto the canvas inside a (hand-jittered) cut outline; optional 1 px cut edge."""
    xs = [p[0] for p in dst_quad]; ys = [p[1] for p in dst_quad]
    x0, y0 = max(0, int(math.floor(min(xs))) - 3), max(0, int(math.floor(min(ys))) - 3)
    x1, y1 = min(canvas.width, int(math.ceil(max(xs))) + 3), min(canvas.height, int(math.ceil(max(ys))) + 3)
    if x1 <= x0 or y1 <= y0:
        return
    dq = [(x - x0, y - y0) for x, y in dst_quad]
    co = homography(src_quad, dq)
    rgba = tex if tex.mode == "RGBA" else tex.convert("RGBA")
    out = rgba.transform((x1 - x0, y1 - y0), Image.PERSPECTIVE, co.tolist(), Image.BICUBIC)
    poly = [(x - x0, y - y0) for x, y in (mask_poly or dst_quad)]
    if jit > 0:
        poly = hand_poly(poly, jit, seed, step=14)
    m = Image.new("L", out.size, 0)
    ImageDraw.Draw(m).polygon(poly, fill=255)
    a = np.minimum(np.asarray(out.getchannel("A")), np.asarray(m))
    out.putalpha(Image.fromarray(a))
    if edge is not None:
        ImageDraw.Draw(out).line(poly + poly[:1], fill=edge, width=2)
        ea = np.asarray(out.getchannel("A")).copy()
        ea = np.minimum(ea, np.asarray(m.filter(ImageFilter.MaxFilter(3))))
        out.putalpha(Image.fromarray(ea))
    if shadow > 0:      # r3: 2-3 px soft contact shadow of the cut piece, cast down (overcast top light)
        pad = 10
        sa = Image.new("L", (out.width + 2 * pad, out.height + 2 * pad), 0)
        sa.paste(out.getchannel("A"), (pad + 1, pad + 4))
        sa = sa.filter(ImageFilter.GaussianBlur(3.0))
        sh = Image.new("RGBA", sa.size, (28, 34, 30, 0))
        sh.putalpha(sa.point(lambda v: int(v * shadow)))
        sx, sy = x0 - pad, y0 - pad
        cx0, cy0 = max(0, -sx), max(0, -sy)
        sh = sh.crop((cx0, cy0, min(sh.width, canvas.width - sx), min(sh.height, canvas.height - sy)))
        if sh.width > 0 and sh.height > 0:
            canvas.alpha_composite(sh, (sx + cx0, sy + cy0))
    canvas.alpha_composite(out, (x0, y0))

def to_img(a, alpha=None):
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    if alpha is not None:
        im.putalpha(alpha)
    return im

def lighter(c, d=16):
    return tuple(min(255, int(v + d)) for v in c[:3]) + (255,)

# ---------------------------------------------------- block textures ----
TPX = 40
BALC = {0: {2, 3, 6}, 1: {10, 11, 14}, 2: {18, 19, 22}}
FACADE = (183, 186, 171)

def win_tex_rect(bay_local, fl):
    u0 = (bay_local * BAY + (BAY - WIN_W) / 2) * TPX
    yb = storey_base(fl) + 0.22
    v1 = (HE - yb) * TPX
    v0 = (HE - yb - WIN_H) * TPX
    return u0, v0, u0 + WIN_W * TPX, v1

def build_facade(bi, seed):
    w, h = int(LEN * TPX), int(HE * TPX)
    off = [(0, 0), (900, 300), (300, 900)][bi]
    crop = (LOC_CLEAN[0] + off[0] // 3, LOC_CLEAN[1] + off[1] // 3, LOC_CLEAN[2] - 300 + off[0] // 3, LOC_CLEAN[3] - 300 + off[1] // 3)
    a = load_paper("loc_blank_0001.jpg", (w, h), FACADE, 2.7, crop=crop, native=True)
    a = sheet_warp(a, seed + 5, 0.03)
    yy = np.linspace(0, 1, h)[:, None, None]
    a *= 1.0 - 0.04 * yy
    a[:30] *= np.linspace(0.70, 1.0, 30)[:, None, None]
    img = to_img(a)
    d = ImageDraw.Draw(img)
    b0 = BLOCKS[bi]["bay0"]
    for fl in range(4):
        y = (HE - storey_base(fl)) * TPX
        d.line((0, y, w, y), fill=(158, 162, 148, 255), width=3)
        for j in range(NBK):
            bay = b0 + j
            u0, v0, u1, v1 = win_tex_rect(j, fl)
            if bay in BALC[bi] and fl > 0:
                d.rectangle((u0 - 26, v1 + 2, u1 + 26, v1 + 24), fill=(112, 114, 98, 255))   # occlusion under slab
            d.polygon(hand_poly([(u0, v0), (u1, v0), (u1, v1), (u0, v1)], 0.6, seed + fl * 31 + j), fill=(74, 85, 86, 255))
            d.rectangle((u0, v0, u1, v0 + 7), fill=(56, 64, 65, 255))
            d.rectangle((u0, v0, u0 + 4, v1), fill=(62, 71, 72, 255))
            d.line((u0 - 2, v1 + 1, u1 + 2, v1 + 1), fill=(198, 199, 186, 255), width=2)          # sill cut edge
            mx = (u0 + u1) / 2
            d.line((mx, v0 + 7, mx, v1), fill=(150, 154, 142, 255), width=3)
            d.line((u0 + 4, v0 + 24, u1, v0 + 24), fill=(150, 154, 142, 255), width=2)
            d.rectangle((u0, v1 - 36, u1, v1 - 33), fill=(62, 63, 48, 255))
            for xx in np.arange(u0 + 5, u1, 7):
                d.line((xx, v1 - 33, xx, v1), fill=(70, 70, 54, 255), width=1)
    gy = (HE - GF) * TPX
    for j in range(NBK):
        u = (j * BAY + 0.9) * TPX
        if bi == 2 and j == 0:
            uL = (22.0 - DOOR_S0) * TPX; uR = (22.0 - DOOR_S1) * TPX
            d.rectangle((uL - 20, h - (DOOR_H + 0.45) * TPX, uR + 20, h - (DOOR_H + 0.25) * TPX), fill=(196, 198, 184, 255))
            d.rectangle((uL - 16, h - (DOOR_H + 0.25) * TPX, uR + 16, h - (DOOR_H + 0.12) * TPX), fill=(96, 100, 92, 255))
            d.rectangle((uL - 6, h - DOOR_H * TPX - 6, uR + 6, h), fill=(132, 136, 124, 255))     # jamb frame
            continue
        d.rectangle((u, gy + 30, u + 56, gy + 92), fill=(80, 90, 90, 255))
        d.rectangle((u, gy + 30, u + 56, gy + 36), fill=(58, 66, 66, 255))
    for x in (int(LEN * TPX * 0.37), int(LEN * TPX * 0.74)):
        d.line((x, 0, x, h), fill=(146, 150, 140, 255), width=5)
    return img

def build_roof_tex(bi):
    w, h = int(LEN * TPX), 200
    a = kraft((w, h), (84, 98, 101), 0.65, ox=bi * 333)
    a = sheet_warp(a, 40 + bi, 0.05)
    img = to_img(a)
    d = ImageDraw.Draw(img)
    for x in np.arange(0, w, 0.62 * TPX):
        d.line((x, 0, x, h), fill=(106, 120, 128, 255), width=2)
    return img

def build_end_tex(bi):
    w, h = int(DEPTH * TPX), int((HE + RR) * TPX)
    a = load_paper("loc_blank_0001.jpg", (w, h), (166, 170, 156), 1.9,
                   crop=(LOC_CLEAN[0] + 200 * bi, LOC_CLEAN[1] + 300, LOC_CLEAN[2], LOC_CLEAN[3]), native=True)
    a = sheet_warp(a, 60 + bi, 0.035)
    img = to_img(a)
    d = ImageDraw.Draw(img)
    for fl in range(4):
        yb = storey_base(fl) + 0.9
        v1 = (HE + RR - yb) * TPX
        d.rectangle((2.2 * TPX, v1 - 1.2 * TPX, 2.9 * TPX, v1), fill=(80, 90, 90, 255))
    return img

def build_dormer_tex():
    w, h = int(1.4 * TPX), int(1.6 * TPX)
    a = load_paper("loc_blank_0001.jpg", (w, h), (190, 207, 212), 0.8, crop=(1200, 900, 1600, 1300))
    img = to_img(a)
    d = ImageDraw.Draw(img)
    d.rectangle((9, 12, w - 9, h - 6), fill=(92, 104, 108, 255))
    d.line((w / 2, 12, w / 2, h - 6), fill=(170, 186, 190, 255), width=2)
    return img

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
            return proj(s, n + RN * (1 - math.cos(t)), HE + RR * math.sin(t))
        v0, v1 = 200 * (1 - j / N), 200 * (1 - (j + 1) / N)
        out.append((t0, t1, [(0, v1), (LEN * TPX, v1), (LEN * TPX, v0), (0, v0)],
                    [P(s0, t1 + 0.012), P(s1, t1 + 0.012), P(s1, t0), P(s0, t0)]))
    return out

def end_wall(b):
    s, n = b["s_left"] - LEN, b["n"]
    pts = [(n, 0.0)]
    for j in range(25):
        t = (math.pi / 2) * j / 24
        pts.append((n + RN * (1 - math.cos(t)), HE + RR * math.sin(t)))
    pts += [(n + DEPTH, HE + RR), (n + DEPTH, 0.0)]
    return s, pts

def shade_roof(t):
    base = np.array([77, 91, 93], np.float32)
    hi = np.array([119, 133, 147], np.float32)
    m = math.sin(t) ** 1.6
    sheen = math.exp(-((t - 0.75) / 0.25) ** 2) * 0.40
    c = base * (0.88 + 0.14 * m) + (hi - base) * (0.25 * m + sheen)
    return c / base

def render_block(bi):
    b = BLOCKS[bi]
    L = Image.new("RGBA", (CW, H2), (0, 0, 0, 0))
    fac = build_facade(bi, 100 * bi)
    warp_into(L, fac, [(0, 0), (fac.width, 0), (fac.width, fac.height), (0, fac.height)], facade_quad(b),
              edge=lighter(FACADE, 30), seed=bi, jit=0.9)
    # balconies: cream card slab + dark rail standing 1.1 m proud of the wall (real depth)
    for fl in (1, 2, 3):
        for j in range(NBK):
            bay = b["bay0"] + j
            if bay not in BALC[bi]:
                continue
            sL = b["s_left"] - j * BAY - 0.25
            sR = b["s_left"] - (j + 1) * BAY + 0.25
            yb = storey_base(fl)
            nf = b["n"] - 1.1
            cheek = to_img(np.full((20, 40, 3), (150, 153, 138), np.float32))
            warp_into(L, cheek, [(0, 0), (40, 0), (40, 20), (0, 20)],
                      [proj(sR, nf, yb + 1.05), proj(sR, b["n"], yb + 1.05), proj(sR, b["n"], yb - 0.2), proj(sR, nf, yb - 0.2)])
            rail = load_paper("loc_blank_0001.jpg", (128, 44), (182, 184, 168), 1.4, crop=(900 + 37 * j, 700 + 50 * fl, 1700, 1100))
            ri = to_img(rail)
            dr = ImageDraw.Draw(ri)
            dr.rectangle((0, 0, 128, 3), fill=(52, 54, 42, 255))           # dark handrail
            for xx in range(4, 128, 6):
                dr.line((xx, 3, xx, 28), fill=(56, 58, 44, 255), width=1)  # dark balusters
            dr.rectangle((0, 28, 128, 44), fill=(186, 188, 172, 255))      # cream slab edge (thick card)
            dr.line((0, 29, 128, 29), fill=(206, 206, 192, 255), width=1)  # its cut edge, lighter
            al = np.full((44, 128), 255, np.uint8)
            for xx in range(4, 128, 6):
                al[4:28, xx + 1:xx + 6] = 60
            ri.putalpha(Image.fromarray(al))
            warp_into(L, ri, [(0, 0), (128, 0), (128, 44), (0, 44)],
                      [proj(sL, nf, yb + 1.05), proj(sR, nf, yb + 1.05), proj(sR, nf, yb - 0.2), proj(sL, nf, yb - 0.2)], shadow=0.55)
    rt = build_roof_tex(bi)
    rarr = np.asarray(rt).astype(np.float32)
    for t0, t1, src, dst in roof_strips(b):
        sh = shade_roof((t0 + t1) / 2)
        tex = rarr.copy(); tex[..., :3] *= sh
        warp_into(L, to_img(tex[..., :3]), src, dst)
    # the zinc card's lower (eave) cut edge: a lighter 1 px line
    ImageDraw.Draw(L).line([proj(b["s_left"], b["n"], HE + 0.02), proj(b["s_left"] - LEN, b["n"], HE + 0.02)], fill=(132, 146, 156, 255), width=2)
    dt = build_dormer_tex()
    def n_roof(y):
        return b["n"] + RN * (1 - math.cos(math.asin(min(1.0, max(0.0, (y - HE) / RR)))))
    for j in range(NBK):
        sc = b["s_left"] - (j + 0.5) * BAY
        nd = b["n"] + 0.12
        y0 = HE + 0.45
        y1 = y0 + 1.75
        sL, sR = sc + 0.70, sc - 0.70
        cheek = to_img(np.full((10, 10, 3), (150, 166, 170), np.float32))
        warp_into(L, cheek, [(0, 0), (10, 0), (10, 10), (0, 10)],
                  [proj(sR, nd, y1), proj(sR, n_roof(y1) + 0.02, y1), proj(sR, n_roof(y0) + 0.02, y0 + 0.02), proj(sR, nd, y0)])
        warp_into(L, dt, [(0, 0), (dt.width, 0), (dt.width, dt.height), (0, dt.height)],
                  [proj(sL, nd, y1), proj(sR, nd, y1), proj(sR, nd, y0), proj(sL, nd, y0)], edge=(212, 226, 230, 255), shadow=0.6)
        cap = to_img(np.full((10, 10, 3), (70, 84, 88), np.float32))
        yc = y1 + 0.28
        warp_into(L, cap, [(0, 0), (10, 0), (10, 10), (0, 10)],
                  [proj(sL + 0.06, n_roof(yc), yc), proj(sR - 0.06, n_roof(yc), yc), proj(sR - 0.06, nd - 0.06, y1), proj(sL + 0.06, nd - 0.06, y1)], shadow=0.4)
        # upper row: a small skylight card lying on the curve (t ~ 0.95 rad)
        if j % 2 == 0:
            ta, tb = 0.92, 1.12
            def Pq(s_, t_):
                return proj(s_, b["n"] + RN * (1 - math.cos(t_)), HE + RR * math.sin(t_))
            sk = to_img(np.full((10, 10, 3), (96, 110, 116), np.float32))
            warp_into(L, sk, [(0, 0), (10, 0), (10, 10), (0, 10)],
                      [Pq(sc + 0.42, tb), Pq(sc - 0.42, tb), Pq(sc - 0.42, ta), Pq(sc + 0.42, ta)], edge=(150, 166, 172, 255), shadow=0.35)
    s, pts = end_wall(b)
    et = build_end_tex(bi)
    poly = [proj(s, n, y) for n, y in pts]
    src = [(0, 0), (et.width, 0), (et.width, et.height), (0, et.height)]
    top = HE + RR
    quad = [proj(s, b["n"], top), proj(s, b["n"] + DEPTH, top), proj(s, b["n"] + DEPTH, 0), proj(s, b["n"], 0)]
    warp_into(L, et, src, quad, mask_poly=poly, edge=(196, 198, 184, 255), seed=7 + bi, jit=0.6)
    rim = [proj(s, n, y) for n, y in pts[1:26]]
    ImageDraw.Draw(L).line(rim, fill=(92, 106, 112, 255), width=max(2, int(0.18 * C["F"] / depth(s, b["n"]))))
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
    L = Image.new("RGBA", (CW, H2), (0, 0, 0, 0))
    s0, s1, n = 150.0, 112.0, 15.0
    a = load_paper("loc_blank_0001.jpg", (800, 400), (200, 204, 200), 0.8, crop=(500, 500, 2500, 1500))
    img = to_img(a)
    d = ImageDraw.Draw(img)
    for fl in range(6):
        for j in range(14):
            d.rectangle((j * 57 + 14, fl * 62 + 30, j * 57 + 40, fl * 62 + 62), fill=(132, 142, 144, 255))
        d.rectangle((0, fl * 62 + 64, 800, fl * 62 + 70), fill=(214, 216, 212, 255))
    warp_into(L, img, [(0, 0), (800, 0), (800, 400), (0, 400)], [proj(s0, n, 19), proj(s1, n, 19), proj(s1, n, 0), proj(s0, n, 0)], jit=0.6)
    endq = [proj(s1, n, 19), proj(s1, n + 12, 19), proj(s1, n + 12, 0), proj(s1, n, 0)]
    e = to_img(load_paper("loc_blank_0001.jpg", (40, 40), (182, 188, 186), 0.6, crop=(900, 900, 1300, 1300)))
    warp_into(L, e, [(0, 0), (40, 0), (40, 40), (0, 40)], endq, jit=0.6)
    return L

# ------------------------------------------------------- ground & co ----
def clip_near(n0, n1, s0, s1):
    while not (depth(s0, n0) > 1.5 and depth(s0, n1) > 1.5):
        s0 += 1.0
    return s0, s1

def ground_quad(n0, n1, s0, s1):
    return [proj(s1, n1, 0), proj(s0, n1, 0), proj(s0, n0, 0), proj(s1, n0, 0)]

def build_ground():
    L = Image.new("RGBA", (CW, H2), (0, 0, 0, 0))
    g = load_paper("p3.jpg", (400, 200), (88, 106, 70), 0.35)
    s0, s1 = clip_near(14.0, 30.0, -60.0, 260.0)
    warp_into(L, to_img(g), [(0, 0), (400, 0), (400, 200), (0, 200)], ground_quad(14.0, 30.0, s0, s1))
    return L

def build_road():
    L = Image.new("RGBA", (CW, H2), (0, 0, 0, 0))
    s0, s1 = clip_near(-7.0, 13.6, -80.0, 260.0)
    ln = s1 - s0
    PX = 12
    w, h = int(ln * PX), int((13.6 + 7.0) * 40)
    road = kraft((w, h), (101, 119, 117), 0.55, rot=90, ox=77)
    img = to_img(road)
    d = ImageDraw.Draw(img)
    def vy(n):
        return (13.6 - n) * 40
    pav = load_paper("loc_blank_0001.jpg", (w, int(2.6 * 40)), (130, 138, 134), 0.9, crop=(500, 400, 2800, 900))
    img.paste(to_img(pav), (0, 0))
    # entrance path across the far pavement toward the door (paler card)
    xp = (s1 - PATH_S) * PX
    d.rectangle((xp - 1.0 * PX, 0, xp + 1.0 * PX, vy(11.15)), fill=(146, 152, 146, 255))
    d.rectangle((0, vy(11.15), w, vy(11.0)), fill=(156, 162, 156, 255))
    d.rectangle((0, vy(11.0), w, vy(10.9)), fill=(84, 98, 98, 255))
    d.rectangle((0, vy(5.45), w, vy(5.3)), fill=(140, 150, 146, 255))
    for sx in np.arange(0, ln, 9.0):
        x0 = sx * PX
        d.polygon(hand_poly([(x0, vy(8.18)), (x0 + 3.0 * PX, vy(8.18)), (x0 + 3.0 * PX, vy(8.02)), (x0, vy(8.02))], 0.4, int(sx)),
                  fill=(158, 168, 166, 255))
    d.rectangle((0, vy(2.45), w, vy(2.3)), fill=(132, 142, 140, 255))         # far edge line of our carriageway
    for sx in np.arange(4.0, ln, 9.0):
        x0 = sx * PX
        d.polygon(hand_poly([(x0, vy(-0.18)), (x0 + 3.0 * PX, vy(-0.18)), (x0 + 3.0 * PX, vy(-0.34)), (x0, vy(-0.34))], 0.4, int(sx) + 7),
                  fill=(150, 160, 158, 255))
    for sx in np.arange(1.0, ln, 9.0):   # r3: a second carriageway (wide boulevard, as in the reference)
        x0 = sx * PX
        d.polygon(hand_poly([(x0, vy(-3.6)), (x0 + 3.0 * PX, vy(-3.6)), (x0 + 3.0 * PX, vy(-3.76)), (x0, vy(-3.76))], 0.4, int(sx) + 13),
                  fill=(150, 160, 158, 255))
    d.rectangle((0, vy(-7.0) - 12, w, h), fill=(112, 122, 114, 255))
    d.line((0, vy(-7.0) - 12, w, vy(-7.0) - 12), fill=(150, 156, 148, 255), width=2)    # kerb cut edge
    src = [(0, 0), (w, 0), (w, h), (0, h)]
    dst = [proj(s1, 13.6, 0), proj(s0, 13.6, 0), proj(s0, -7.0, 0), proj(s1, -7.0, 0)]
    warp_into(L, img, src, dst)
    return L

def build_verge():
    """P6: our grass verge, cut from the green paper sheet: everything in front of the road's near
    kerb, out to the frame's lower edge (the camera stands on it), with a torn top edge."""
    L = Image.new("RGBA", (CW, H2), (0, 0, 0, 0))
    s0, s1 = clip_near(-6.9, -6.9, -80.0, 400.0)
    edge = [proj(s, -6.9, 0) for s in np.linspace(s0, s1, 400)]
    edge = [(x, y) for x, y in edge if -400 < x < CW + 4000]
    r = np.random.RandomState(4)
    top = [(x, y - 1 + r.normal(0, 0.9)) for x, y in edge]
    poly = top + [(-400, top[-1][1]), (-400, H2 + 50), (CW + 4000, H2 + 50)]
    m = Image.new("L", (CW, H2), 0)
    ImageDraw.Draw(m).polygon(poly, fill=255)
    v = load_paper("p3.jpg", (CW, H2), (78, 102, 56), 0.55)
    # receding grass: the sheet's fibre is finer far up the wedge (a second, reduced copy) than near
    vf = load_paper("p3.jpg", (CW // 3 + 1, H2 // 3 + 1), (78, 102, 56), 0.55)
    vf = np.tile(vf, (3, 3, 1))[:H2, :CW]
    yy = np.clip((np.arange(H2)[:, None, None] - C["CY"]) / (H2 - C["CY"]), 0, 1)
    v = v * yy + vf * (1 - yy)
    v = sheet_warp(v, 91, 0.05)
    v *= (0.97 + 0.06 * yy)
    img = to_img(v)
    img.putalpha(m)
    ImageDraw.Draw(img).line(top, fill=(108, 128, 84, 255), width=2)
    return img

LEAF_COLS = [(44, 58, 37), (50, 65, 42), (60, 76, 50), (72, 88, 58), (40, 53, 34)]

def build_hedge():
    L = Image.new("RGBA", (CW, H2), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    r = np.random.RandomState(77)
    kr = kraft((256, 256), (48, 63, 41), 0.8)
    s0, s1 = clip_near(13.9, 13.9, -60.0, 230.0)
    def top(s):
        return 1.25 + 0.05 * math.sin(s * 1.3) + 0.04 * math.sin(s * 3.7 + 1)
    gap = (PATH_S - 1.1, PATH_S + 1.1)
    segs = [(s0, gap[0]), (gap[1], s1)]
    for a0, a1 in segs:
        body = [proj(s, 13.9, top(s) - 0.12) for s in np.arange(a0, a1, 0.5)] + [proj(a1, 13.9, top(a1) - 0.12), proj(a1, 13.9, 0), proj(a0, 13.9, 0)]
        d.polygon(body, fill=(38, 50, 31, 255))
    ss = np.arange(s0, s1, 0.05)
    for layer in range(3):
        for s in ss:
            if gap[0] + 0.05 < s < gap[1] - 0.05:
                continue
            z = depth(s, 13.9)
            pxm = C["F"] / z
            if pxm < 6 and r.rand() < 0.6:
                continue
            for _ in range(2 if pxm > 12 else 1):
                y = r.rand() ** 0.6 * top(s) - 0.02 + layer * 0.03
                n = 13.9 - 0.05 * layer
                x, yy = proj(s + r.normal(0, 0.03), n, y)
                L_ = max(1.6, 0.11 * pxm)
                ang = r.rand() * math.pi
                c = LEAF_COLS[min(4, int(r.rand() * 3) + layer)] if layer < 2 else LEAF_COLS[int(r.rand() * 4)]
                if layer == 2 and r.rand() < 0.5:
                    c = (68, 84, 54)
                dx, dy = math.cos(ang) * L_, math.sin(ang) * L_ * 0.55
                d.polygon([(x - dx, yy - dy), (x + dy * 0.5, yy - dx * 0.35), (x + dx, yy + dy), (x - dy * 0.5, yy + dx * 0.35)], fill=c + (255,))
    a = np.asarray(L).astype(np.float32)
    tile = np.tile(kr, (H2 // 256 + 1, CW // 256 + 1, 1))[:H2, :CW]
    a[..., :3] *= (tile / np.array([48, 63, 41], np.float32)) ** 0.5
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

def sapling_strokes(s, n, k, seed, height):
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
    res = []
    pxm = C["F"] / depth(s, n)
    for x0, y0, x1, y1, wdt in out:
        res.append((proj(s - x0, n, y0), proj(s - x1, n, y1), max(1.0, wdt * pxm)))
    return res

def sapling_list():
    out = []
    for blk in BLOCKS:
        for j in range(0, NBK + 1, 2):
            s = blk["s_left"] - j * BAY
            out.append((s + 0.2, blk["n"] - 2.6, len(out) + 3, 7.5 + (len(out) % 3) * 0.8))
    for s in (blk["s_left"] + 3.5 for blk in BLOCKS):
        out.append((s, 16.0, len(out) + 3, 8.0))
    use_cam("key")
    q = window_quad(16, 0)
    wx0, wx1 = min(p[0] for p in q) - 6, max(p[0] for p in q) + 6
    keep = []
    for sp in out:
        if abs(sp[0] - PATH_S) < 1.5:
            continue
        xs = [p for st in sapling_strokes(sp[0], sp[1], 492, sp[2], sp[3]) for p in (st[0][0], st[1][0])]
        if max(xs) < wx0 or min(xs) > wx1:
            keep.append(sp)
    return keep

SAPLINGS = sapling_list()

def draw_saplings(k, cam):
    use_cam(cam)
    L = Image.new("L", (CW, H2), 0)
    d = ImageDraw.Draw(L)
    for s, n, seed, h in SAPLINGS:
        for p0, p1, w in sapling_strokes(s, n, k, seed, h):
            d.line((p0[0], p0[1], p1[0], p1[1]), fill=255, width=int(round(w)))
    return L

# fence post: on our verge near the right edge (P7)
def fence_pos(cam):
    return (3.3, 5.2) if cam == "key" else (3.6, 7.5)

def build_fence(cam):
    L = Image.new("RGBA", (CW, H2), (0, 0, 0, 0))
    m = Image.new("L", (CW, H2), 0)
    e = Image.new("L", (CW, H2), 0)
    d = ImageDraw.Draw(m); de = ImageDraw.Draw(e)
    X, Z = fence_pos(cam)
    def P(X_, Z_, y):
        return (C["CX"] + C["F"] * X_ / Z_, C["CY"] - C["F"] * (y - EYE) / Z_)
    xL, yT = P(X, Z, 1.25); xR, _ = P(X + 0.09, Z, 1.25)
    _, yB = P(X, Z, -0.4)
    post = hand_poly([(xL, yT), (xR, yT - 2), (xR + 1, yB), (xL - 1, yB)], 0.8, 5)
    d.polygon(post, fill=255)
    d.ellipse((xL - 3, yT - 7, xR + 3, yT + 5), fill=255)
    de.line([(xL, yT + 4), (xL - 1, yB)], fill=255, width=2)
    for i in range(1, 7):
        yy = 1.2 - i * 0.2
        a = P(X + 0.09, Z, yy); b_ = P(X + 1.8, Z - 0.9, yy + 0.06)
        d.line((a[0], a[1], b_[0], b_[1]), fill=230, width=3)
    for i in range(1, 10):
        xx = X + 0.09 + i * 0.18
        zz = Z - 0.9 * i * 0.18 / 1.71
        a = P(xx, zz, 1.22); b_ = P(xx - 0.08, zz, -0.4)
        d.line((a[0], a[1], b_[0], b_[1]), fill=230, width=3)
    tex = kraft((CW, H2), (60, 69, 61), 0.8, rot=90)
    ea = np.asarray(e).astype(np.float32)[..., None] / 255.0
    tex = tex * (1 - ea) + np.array([86, 96, 88], np.float32) * ea           # cut edge 1 px lighter
    img = to_img(tex)
    img.putalpha(m)
    return img

def build_sky(cam):
    top = np.array([246, 237, 243], np.float32)
    low = np.array([236, 228, 240], np.float32)
    hz = CAMS[cam]["CY"]
    yy = np.linspace(0, H2, H2)[:, None, None] / hz
    sky = top + (low - top) * np.clip(yy, 0, 1)
    fib = load_paper("loc_blank_0001.jpg", (CW, H2), (0, 0, 0), 0.10, crop=(500, 400, 2800, 2200))
    return to_img(sky + fib)

# ------------------------------------------- shadow + bake + cache -----
def bake_shadow(img, strength=0.32, off=(4, 5), radius=12):
    """soft overcast drop shadow under a sheet: offset (2, 2.5) final px, blur 6 final px."""
    a = img.getchannel("A")
    sh = a.filter(ImageFilter.GaussianBlur(radius)).transform(a.size, Image.AFFINE, (1, 0, -off[0], 0, 1, -off[1]))
    sa = (np.asarray(sh).astype(np.float32) / 255.0 * strength)
    base = np.zeros((img.height, img.width, 4), np.float32)
    base[..., :3] = np.array([30, 36, 32], np.float32)
    base[..., 3] = sa * 255
    # r3: plus a tight 1-2 px contact shadow where the cut edge stands off the sheet behind
    tight = a.filter(ImageFilter.GaussianBlur(3)).transform(a.size, Image.AFFINE, (1, 0, -1, 0, 1, -4))
    ta = np.asarray(tight).astype(np.float32) / 255.0 * 0.38
    base[..., 3] = np.clip(1 - (1 - sa) * (1 - ta), 0, 1) * 255
    out = Image.fromarray(base.astype(np.uint8), "RGBA")
    out.alpha_composite(img)
    return out

LAYERS = {   # name: (plane, shadow?, pre-blur SS px)
    "sky": ("P0", False, 0), "p1far": ("P1", False, 1.6), "ground": ("P2", False, 0),
    "blk0": ("P2", False, 1.0), "blk1": ("P2", True, 0.5), "blk2": ("P3", True, 0),
    "hedge": ("P4", True, 0), "road": ("P5", False, 0), "verge": ("P6", True, 0), "fence": ("P7", True, 0)}

def build_cam(cam):
    use_cam(cam)
    out = {"sky": build_sky(cam), "p1far": build_far_block(), "ground": build_ground(),
           "blk0": render_block(0), "blk1": render_block(1), "blk2": render_block(2),
           "hedge": build_hedge(), "road": build_road(), "verge": build_verge(), "fence": build_fence(cam)}
    for name, img in out.items():
        plane, shd, bl = LAYERS[name]
        if shd:
            img = bake_shadow(img)
        if bl:
            img = img.filter(ImageFilter.GaussianBlur(bl))
        img.save(os.path.join(CACHE, f"{cam}-{name}.png"))
    quads = {i: window_quad(i % 24, i // 24) for i in LIGHT}
    np.save(os.path.join(CACHE, f"{cam}-winquads.npy"), quads, allow_pickle=True)

def build_all():
    os.makedirs(CACHE, exist_ok=True)
    for cam in ("wide", "tele", "key"):
        build_cam(cam)

_L = {}
def layer(cam, name):
    key = (cam, name)
    if key not in _L:
        _L[key] = Image.open(os.path.join(CACHE, f"{cam}-{name}.png")).convert("RGBA")
    return _L[key]

_Q = {}
def quads(cam):
    if cam not in _Q:
        _Q[cam] = np.load(os.path.join(CACHE, f"{cam}-winquads.npy"), allow_pickle=True).item()
    return _Q[cam]

# ============================================================== multiplane ===
def plane_params(k, plane):
    """(dx SS px, scale, centre) of a plane at frame k."""
    sh = shot_of(k)
    r = RATIOS[plane] if isinstance(plane, str) else plane
    dx = r * track_X(k) * SS
    sc = 1.0 + 0.18 * r * push_u(k)
    return dx, sc, push_center(sh["cam"])

def place(img, k, plane):
    """the camera's view of one glass plane: canvas -> frame (SS) by offset + scale."""
    dx, sc, (pcx, pcy) = plane_params(k, plane)
    a = 1.0 / sc
    c = pcx + ML - (pcx + dx) * a
    f = pcy - pcy * a
    return img.transform((W2, H2), Image.AFFINE, (a, 0, c, 0, a, f), Image.BILINEAR)

def canvas_to_frame(k, plane, x, y):
    dx, sc, (pcx, pcy) = plane_params(k, plane)
    return ((x - ML - pcx) * sc + pcx + dx, (y - pcy) * sc + pcy)

# ================================================================ walker ===
WALK_K0 = 200
STEP = 13.2                       # frames per step; stride (two steps) = 26.4 frames = 1.10 s
HOLD = 6                          # double-support contact hold, frames
STEP_LEN = 0.70                   # m
N_STEPS = 12
P_START = (PATH_S + 1.25, 11.9)   # on the far pavement, just left of the entrance path
P_TURN = (PATH_S, 11.9)            # she turns up the path through the hedge gap
P_DOOR = (PATH_S, 19.0)

def path_point(u):
    """(s, n) at arc length u along pavement -> path -> door (a rounded corner)."""
    a = P_START[0] - P_TURN[0]
    R = 0.45
    if u < a - R:
        return P_START[0] - u, P_START[1]
    if u < a - R + R * math.pi / 2:
        th = (u - (a - R)) / R
        cs, cn = P_TURN[0] + R, P_TURN[1] + R
        return cs - R * math.sin(th), cn - R * math.cos(th)
    v = u - (a - R + R * math.pi / 2)
    return P_TURN[0], P_TURN[1] + R + v

def contact_frames():
    return [int(round(WALK_K0 + j * STEP)) for j in range(N_STEPS + 1)]

def foot_plants():
    """plant u (metres along the path) for each contact; foot 0 = left starts behind."""
    return [j * STEP_LEN for j in range(N_STEPS + 3)]

def gait(k):
    """hip u, hip height, foot positions (u, lift) for both feet, and phase; contact holds of 6 frames."""
    t = k - WALK_K0
    j = int(math.floor(t / STEP))
    tt = t - j * STEP
    plants = foot_plants()
    # hip advances smoothly: half a step per step-period, bobbing low in double support
    hip_u = (t / STEP) * STEP_LEN + 0.35 * STEP_LEN
    bob = -0.035 * math.cos(2 * math.pi * (tt - HOLD / 2) / STEP)      # lowest at mid double-support
    lead = j % 2                     # foot that made the contact at step j
    trail = 1 - lead
    feet = [None, None]
    feet[lead] = (plants[j + 1], 0.0)
    if tt < HOLD:
        feet[trail] = (plants[j], 0.0)
    else:
        x = (tt - HOLD) / (STEP - HOLD)
        e = 0.5 - 0.5 * math.cos(math.pi * x)
        feet[trail] = (plants[j] + (plants[j + 2] - plants[j]) * e, 0.09 * math.sin(math.pi * x))
    return hip_u, 0.88 + bob, feet, j, tt

def ik2(hx, hy, fx, fy, l1, l2):
    """2-link leg: thigh and shin angles from vertical (positive = forward), knee bends forward."""
    dx, dy = fx - hx, fy - hy
    d = min(l1 + l2 - 1e-4, math.hypot(dx, dy))
    a = math.atan2(dx, -dy)
    c = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)
    b = math.acos(max(-1, min(1, c)))
    th = a + b
    knee = (hx + l1 * math.sin(th), hy - l1 * math.cos(th))
    sh = math.atan2(fx - knee[0], -(fy - knee[1]))
    return th, sh

TH, SHN, FOOT = 0.44, 0.44, 0.22

_BAG = {}
def bag_angle(k):
    """bag swings as a pendulum driven by the hand, 4 frames behind (secondary motion)."""
    def hand_ang(kk):
        hip_u, hy, feet, j, tt = gait(kk)
        return -0.32 * math.sin(math.pi * (kk - WALK_K0) / STEP)
    return 0.8 * hand_ang(k - 4)

def walker_pose(k):
    """joint angles (radians, from vertical, + = forward along the path) for frame k, or None."""
    if k < WALK_K0 or k > 362:
        return None
    hip_u, hy, feet, j, tt = gait(k)
    pose = dict(k=k, hip_u=hip_u, hip_y=hy)
    for side, (fu, fl) in zip(("L", "R"), feet):
        th, sh = ik2(0.0, hy, fu - hip_u, fl + 0.07, TH, SHN)
        pose["thigh_" + side] = th
        pose["shin_" + side] = sh
        pose["foot_" + side] = (fu, fl)
    ph = math.pi * (k - WALK_K0) / STEP
    pose["torso"] = 0.07 + 0.02 * math.sin(2 * ph)
    pose["uarm_L"] = 0.30 * math.sin(ph); pose["farm_L"] = pose["uarm_L"] + 0.25 + 0.15 * math.sin(ph)
    pose["uarm_R"] = -0.10 * math.sin(ph); pose["farm_R"] = pose["uarm_R"] - 0.05    # bag arm: shorter swing
    pose["bag"] = bag_angle(k)
    pose["head"] = -0.05 + 0.03 * math.sin(2 * ph + 0.5)
    return pose

COAT = (70, 74, 70)
COAT_FAR = (52, 56, 54)
SKIN = (172, 150, 132)
BAGC = (150, 140, 112)

def capsule(d, p0, p1, w, fill):
    d.line([p0, p1], fill=fill, width=max(1, int(round(w))))
    r = w / 2
    for p in (p0, p1):
        d.ellipse((p[0] - r, p[1] - r, p[0] + r, p[1] + r), fill=fill)

def draw_walker(k, cam="wide"):
    """the articulated paper cutout, joint by joint (FK), in the wide set-up's canvas coords."""
    pose = walker_pose(k)
    if pose is None:
        return None, None, None
    use_cam(cam)
    def W(u, y):
        s, n = path_point(u)
        return proj(s, n, y)
    L = Image.new("RGBA", (CW, H2), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    hu, hy = pose["hip_u"], pose["hip_y"]
    pxm = C["F"] / depth(*path_point(hu))
    def fk_leg(side, col):
        th, sh = pose["thigh_" + side], pose["shin_" + side]
        hip = (hu, hy)
        knee = (hu + TH * math.sin(th), hy - TH * math.cos(th))
        ank = (knee[0] + SHN * math.sin(sh), knee[1] - SHN * math.cos(sh))
        toe = (ank[0] + FOOT * 0.85, max(0.0, ank[1] - 0.06))
        capsule(d, W(*hip), W(*knee), 0.15 * pxm, col)
        capsule(d, W(*knee), W(*ank), 0.11 * pxm, col)
        capsule(d, W(*ank), W(*toe), 0.07 * pxm, (40, 42, 40))
    def fk_arm(side, col, bag=False):
        sho = (hu + 0.52 * math.sin(pose["torso"]), hy + 0.52)
        ua, fa = pose["uarm_" + side], pose["farm_" + side]
        elb = (sho[0] + 0.29 * math.sin(ua), sho[1] - 0.29 * math.cos(ua))
        hand = (elb[0] + 0.27 * math.sin(fa), elb[1] - 0.27 * math.cos(fa))
        capsule(d, W(*sho), W(*elb), 0.10 * pxm, col)
        capsule(d, W(*elb), W(*hand), 0.08 * pxm, col)
        if bag:
            b = pose["bag"]
            bt = (hand[0] + 0.30 * math.sin(b), hand[1] - 0.30 * math.cos(b))
            d.line([W(*hand), W(hand[0] + 0.08 * math.sin(b), hand[1] - 0.08 * math.cos(b))], fill=(60, 58, 50, 255), width=max(1, int(0.02 * pxm)))
            cx, cy = W(*bt)
            bw, bh = 0.30 * pxm, 0.34 * pxm
            ang = b
            pts = [(-bw / 2, -bh * 0.75), (bw / 2, -bh * 0.75), (bw / 2 * 1.05, bh * 0.35), (-bw / 2 * 1.05, bh * 0.35)]
            ca, sa = math.cos(ang), math.sin(ang)
            d.polygon([(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in pts], fill=BAGC + (255,))
    # far limbs first (darker card), body, near limbs
    fk_arm("R", COAT_FAR + (255,), bag=False) if False else None
    fk_leg("R", COAT_FAR + (255,))
    fk_arm("R", COAT_FAR + (255,), bag=True)
    # torso (coat card, a trapezoid pinned at the hip), head pinned at the neck
    tor = pose["torso"]
    hip = W(hu, hy + 0.02)
    sh_ = W(hu + 0.55 * math.sin(tor), hy + 0.55)
    tw = 0.36 * pxm
    hx_, hy_ = hip; sx_, sy_ = sh_
    d.polygon([(hx_ - tw * 0.62, hy_ + 0.12 * pxm), (hx_ + tw * 0.62, hy_ + 0.12 * pxm), (sx_ + tw * 0.42, sy_), (sx_ - tw * 0.48, sy_)], fill=COAT + (255,))
    nk = (hu + 0.62 * math.sin(tor), hy + 0.62)
    hd = pose["head"]
    hc = W(nk[0] + 0.12 * math.sin(tor + hd), nk[1] + 0.12)
    r = 0.115 * pxm
    capsule(d, W(*nk), W(nk[0], nk[1] + 0.05), 0.07 * pxm, SKIN + (255,))
    d.ellipse((hc[0] - r, hc[1] - r * 1.15, hc[0] + r, hc[1] + r * 1.1), fill=SKIN + (255,))
    d.chord((hc[0] - r * 1.05, hc[1] - r * 1.25, hc[0] + r * 0.9, hc[1] + r * 0.6), 150, 360, fill=(84, 78, 72, 255))   # hair card
    fk_leg("L", COAT + (255,))
    fk_arm("L", COAT + (255,))
    n_now = path_point(hu)[1]
    ratio = RATIOS["P4"] + (RATIOS["P3"] - RATIOS["P4"]) * min(1.0, max(0.0, (n_now - 13.9) / (19.0 - 13.9)))
    return L, ratio, n_now

# ================================================================== door ===
def door_angle(k):
    """inward-opening door leaf, hinged on its right jamb: 0 = shut, 1 = open (80 deg)."""
    if k < 334:
        return 0.0
    if k <= 346:
        return smooth((k - 334) / 12.0)
    if k < 365:
        return 1.0
    if k <= 374:
        x = (k - 365) / 9.0
        return 1.0 - x * x                      # it swings shut and stops hard (latched at 374)
    return 0.0

def draw_door(img, k):
    """onto the near-block layer (canvas coords of the current set-up)."""
    d = ImageDraw.Draw(img)
    n = BLOCKS[2]["n"] + 0.01
    quad = [proj(DOOR_S0, n, DOOR_H), proj(DOOR_S1, n, DOOR_H), proj(DOOR_S1, n, 0), proj(DOOR_S0, n, 0)]
    d.polygon(quad, fill=(30, 34, 33, 255))                     # the dark hall behind
    a = door_angle(k) * math.radians(80)
    # leaf hinged at DOOR_S1 (right), swings inward (+n)
    wl = DOOR_S0 - DOOR_S1
    fs = DOOR_S1 + wl * math.cos(a)
    fn = n + wl * math.sin(a)
    leaf = [proj(fs, fn, DOOR_H - 0.02), proj(DOOR_S1, n, DOOR_H - 0.02), proj(DOOR_S1, n, 0.0), proj(fs, fn, 0.0)]
    lc = (96, 106, 102)
    d.polygon(leaf, fill=lc + (255,))
    # glazed panel in the leaf (darker) and its 1 px lighter cut edge
    def lp(u, y):
        return proj(DOOR_S1 + (fs - DOOR_S1) * u, n + (fn - n) * u, y)
    d.polygon([lp(0.82, 2.1), lp(0.18, 2.1), lp(0.18, 0.9), lp(0.82, 0.9)], fill=(58, 66, 66, 255))
    d.line([leaf[0], leaf[3]], fill=lighter(lc, 22), width=2)
    return quad

# ================================================================== lamp ===
LAMP_X, LAMP_Z = 3.0, 8.6        # in camera space of the wide set-up (m), on our verge
def lamp_geom():
    use_cam("wide")
    def P(X_, Z_, y):
        return (C["CX"] + C["F"] * X_ / Z_, C["CY"] - C["F"] * (y - EYE) / Z_)
    base = P(LAMP_X, LAMP_Z, -0.3)
    top = P(LAMP_X, LAMP_Z, 3.5)
    neck = [P(LAMP_X - 0.75 * (1 - math.cos(t)), LAMP_Z, 3.5 + 0.55 * math.sin(t)) for t in np.linspace(0, math.pi * 0.95, 14)]
    head = P(LAMP_X - 1.45, LAMP_Z, 3.75)
    pool = P(LAMP_X - 1.45, LAMP_Z, 0.0)           # the ground straight under the head
    return base, top, neck, head, pool

def lamp_on(k):
    return 0.0 if k < 660 else min(1.0, (k - 658) / 3.0)

def draw_lamp(k):
    base, top, neck, head, pool = lamp_geom()
    L = Image.new("RGBA", (CW, H2), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    col = (60, 69, 61, 255)
    wpx = C["F"] * 0.11 / LAMP_Z
    d.polygon(hand_poly([(base[0] - wpx / 2, base[1]), (top[0] - wpx * 0.35, top[1]), (top[0] + wpx * 0.35, top[1]), (base[0] + wpx / 2, base[1])], 0.7, 21), fill=col)
    d.line(neck, fill=col, width=int(wpx * 0.6))
    hx, hy = head
    hw = C["F"] * 0.55 / LAMP_Z
    hood = [(hx - hw / 2, hy), (hx + hw / 2, hy - hw * 0.05), (hx + hw * 0.32, hy + hw * 0.22), (hx - hw * 0.38, hy + hw * 0.24)]
    d.polygon(hood, fill=col)
    d.line([(base[0] - wpx / 2 + 1, base[1]), (top[0] - wpx * 0.35 + 1, top[1])], fill=(86, 96, 88, 255), width=2)   # cut edge
    on = lamp_on(k)
    lampc = tuple(int(v) for v in np.array([92, 98, 90]) + (np.array([255, 214, 150]) - np.array([92, 98, 90])) * on)
    d.ellipse((hx - hw * 0.30, hy + hw * 0.12, hx + hw * 0.26, hy + hw * 0.34), fill=lampc + (255,))
    return L, head, pool, hw

# ===================================================================== frame ===
def over(base, layer):
    a = layer[..., 3:4] * (1.0 / 255.0)
    base *= (1 - a)
    base += layer[..., :3] * a
    return base

def haze(base, amount, E, cy):
    ys = np.arange(H2, dtype=np.float32)[:, None, None] / cy
    dens = amount * (0.30 + 0.70 * np.clip((ys - 0.05) / 0.95, 0, 1) ** 1.4)
    col = np.array([234, 228, 236], np.float32) * (0.90 + 0.10 * E)
    base *= (1 - dens)
    base += col * dens
    return base

def arr(img):
    return np.asarray(img).astype(np.float32)

def lit_block(cam, name, bays, k, E):
    src = layer(cam, name)
    a = arr(src)
    a[..., :3] *= E
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
    d = ImageDraw.Draw(img, "RGBA")
    for i, q in quads(cam).items():
        fl, bay = divmod(i, 24)
        if bay not in bays:
            continue
        if i == 16 and cam == "key":
            continue
        g = glow(i, k)
        if g <= 0:
            continue
        rec = np.array([74, 85, 86]) * E
        c = rec + (np.array([240, 190, 110]) - rec) * min(1.02, g)
        d.polygon(q, fill=tuple(int(v) for v in c) + (255,))
        def lerp(p, r_, t):
            return (p[0] + (r_[0] - p[0]) * t, p[1] + (r_[1] - p[1]) * t)
        tl, tr, br_, bl = q
        wq = abs(tr[0] - tl[0])
        lw = 2 if wq > 14 else 1
        d.line([lerp(tl, bl, 0.08), lerp(tr, br_, 0.08)], fill=(int(60 * E), int(66 * E), int(66 * E), 255), width=lw)
        d.line([lerp(tl, tr, 0.5), lerp(bl, br_, 0.5)], fill=(int(150 * E), int(140 * E), int(112 * E), 255), width=lw)
        ra, rb = lerp(tl, bl, 0.84), lerp(tr, br_, 0.84)
        d.line([ra, rb], fill=(int(62 * E), int(63 * E), int(48 * E), 255), width=lw)
        if wq > 10:
            for t in np.linspace(0.08, 0.92, 7):
                d.line([lerp(ra, rb, t), lerp(bl, br_, t)], fill=(int(70 * E), int(70 * E), int(54 * E), 210), width=1)
    if name == "blk2":
        use_cam(cam)
        draw_door(img, k)
        if cam == "key" and 16 in bays:
            q = quads(cam)[16]
            t16 = window16_tex(k, glow(16, k))
            warp_into(img, t16, [(0, 0), (t16.width, 0), (t16.width, t16.height), (0, t16.height)], q)
    return img

def frame(k):
    """the paper maquette at frame k (0..719): a pure function of k."""
    k = int(k)
    sh = shot_of(k)
    cam = sh["cam"]
    E = exposure(k)
    cy = CAMS[cam]["CY"]
    # P0 sky: cools toward (205,205,215) in S3/S4 and loses a little light
    sky = arr(place(layer(cam, "sky"), k, "P0"))[..., :3]
    dmix = max(0.0, (0.93 - E) / 0.15) * 0.40 if k >= 384 else (1.0 - E) / 0.07 * 0.06
    sky += (np.array([205, 205, 215], np.float32) - sky) * dmix
    sky *= (0.97 + 0.03 * E)
    can = sky
    def plane(name, img=None):
        p = LAYERS[name][0]
        im = img if img is not None else layer(cam, name)
        a = arr(place(im, k, p))
        if img is None:
            a[..., :3] *= E
        return a
    can = over(can, plane("p1far"))
    can = haze(can, 0.42, E, cy)
    can = over(can, plane("ground"))
    can = over(can, plane("blk0", lit_block(cam, "blk0", range(0, 8), k, E)))
    can = haze(can, 0.15, E, cy)
    can = over(can, plane("blk1", lit_block(cam, "blk1", range(8, 16), k, E)))
    can = haze(can, 0.08, E, cy)
    blk2 = lit_block(cam, "blk2", range(16, 24), k, E)
    # the walker: behind the hedge's gap edges, in front of the block; inside the door she is
    # clipped by the opening (the jamb occludes her) and the hall's dark takes her
    wk = None
    if cam in ("wide", "tele"):
        wl, wr, wn = draw_walker(k, cam) if walker_pose(k) is not None else (None, None, None)
        if wl is not None:
            if k >= 346:
                use_cam(cam)
                n = BLOCKS[2]["n"] + 0.01
                quad = [proj(DOOR_S0, n, DOOR_H), proj(DOOR_S1, n, DOOR_H), proj(DOOR_S1, n, 0), proj(DOOR_S0, n, 0)]
                m = Image.new("L", (CW, H2), 0)
                ImageDraw.Draw(m).polygon(quad, fill=255)
                wa = arr(wl)
                dark = 1.0 - 0.75 * min(1.0, (k - 346) / 16.0)
                wa[..., :3] *= dark
                wa[..., 3] = np.minimum(wa[..., 3], arr(m)[..., 0] if arr(m).ndim == 3 else arr(m))
                wl = Image.fromarray(np.clip(wa, 0, 255).astype(np.uint8), "RGBA")
            wa = arr(wl)
            wa[..., :3] *= E
            wk = (Image.fromarray(np.clip(wa, 0, 255).astype(np.uint8), "RGBA"), wr, wn)
    can = over(can, plane("blk2", blk2))
    can = haze(can, 0.035, E, cy)
    if wk is not None and wk[2] > 14.3:          # behind the hedge line: the gap's edges occlude her
        can = over(can, arr(place(wk[0], k, wk[1])))
    # P4 saplings (cut card) + hedge
    tm = draw_saplings(k, cam)
    tt = np.zeros((H2, CW, 4), np.float32)
    tt[..., :3] = np.array([114, 124, 105], np.float32) * 0.92
    tt[..., 3] = np.asarray(tm)
    timg = bake_shadow(Image.fromarray(tt.astype(np.uint8), "RGBA"), strength=0.22)
    can = over(can, plane("hedge", None) if False else arr(place(Image.fromarray(np.clip(arr(timg) * np.array([E, E, E, 1.0], np.float32), 0, 255).astype(np.uint8), "RGBA"), k, "P4")))
    can = over(can, plane("hedge"))
    if wk is not None and wk[2] <= 14.3:         # on the pavement, in front of the hedge
        can = over(can, arr(place(wk[0], k, wk[1])))
    can = over(can, plane("road"))
    can = over(can, plane("verge"))
    # S4: lamp post (P7, swan neck) and its light pool computed from its pose
    if cam == "wide" and k >= 624:
        ll, head, pool, hw = draw_lamp(k)
        on = lamp_on(k)
        if on > 0:
            px, py = canvas_to_frame(k, "P7", *pool)
            hx, hy = canvas_to_frame(k, "P7", *head)
            yy, xx = np.mgrid[0:H2, 0:W2].astype(np.float32)
            rx, ry = hw * 2.6, hw * 0.55
            g = np.exp(-(((xx - px) / rx) ** 2 + ((yy - py) / ry) ** 2)) * (yy > cy + 10)
            g2 = np.exp(-(((xx - hx) / (hw * 0.9)) ** 2 + ((yy - hy - hw * 0.25) / (hw * 0.6)) ** 2))
            warm = np.array([255, 205, 140], np.float32)
            can += (warm * 0.42 * on) * g[..., None] * (can / 160.0)
            can += (warm * 0.30 * on) * g2[..., None]
        la = arr(ll); la[..., :3] *= E
        lamp_layer = Image.fromarray(np.clip(la, 0, 255).astype(np.uint8), "RGBA")
        hd = arr(ll)
        can = over(can, arr(place(bake_shadow(lamp_layer), k, "P7")))
        if on > 0:   # the lit lamp is not dimmed by the exposure
            hx0, hy0 = head
            m = Image.new("L", (CW, H2), 0)
            ImageDraw.Draw(m).ellipse((hx0 - hw * 0.30, hy0 + hw * 0.12, hx0 + hw * 0.26, hy0 + hw * 0.34), fill=255)
            bulb = Image.new("RGBA", (CW, H2), (255, 214, 150, 0)); bulb.putalpha(m.point(lambda v: int(v * on)))
            can = over(can, arr(place(bulb, k, "P7")))
    can = over(can, plane("fence"))
    out = Image.fromarray(np.clip(can, 0, 255).astype(np.uint8))
    return out.resize((PW, PH), Image.LANCZOS).point(GRADE_LUT * 3)

# r2 grade (editor, master revision 2): one global mid-tone levels curve, gamma 0.93 per channel, end points fixed.
# r1 (e467efc...) measured luma p50 114.7 on the DECODED master at 4.0 s, under plan 9.6's floor of 115; this lifts
# the mid-tones toward the reference (p50 131) without touching geometry, timing or any event frame.
GRADE_GAMMA = 0.93
GRADE_LUT = [int(round(255 * (v / 255.0) ** GRADE_GAMMA)) for v in range(256)]

# ============================================================ window 16 ===
def rise_y(k):
    if k < 502:
        return 1.0
    x = (k - 502) / 16.0
    if x < 1:
        return 1.0 - smooth(x) * 1.03
    s = k - 518
    return -0.03 * math.exp(-s / 2.5) * math.cos(s * 0.9) + 0.004 * math.sin(k / FPS * 2 * math.pi / 3.4)

def yaw_deg(k):
    """f538-552: 0 -> 27 deg (2 deg overshoot), settling to 25 over 6 frames."""
    if k < 538:
        return 0.0
    if k <= 552:
        return 27.0 * smooth((k - 538) / 14.0)
    s = k - 552
    return 25.0 + (2.0 * (1 - s / 6.0) * math.cos(s / 6.0 * math.pi / 2) if s < 6 else 0.0)

def curtain_dx(k):
    if k < 552:
        return 0.0
    x = (k - 552) / 14.0
    if x >= 1:
        return 1.0
    return smooth(min(1, x * 1.25)) + 0.12 * math.sin(math.pi * min(1, x * 1.25)) * (1 - x)

def window16_tex(k, lit):
    w, h = 145 * 2, 185 * 2
    amber = np.array([240, 190, 110], np.float32)
    recess = np.array([74, 85, 86], np.float32) * 0.85
    yy, xx = np.mgrid[0:h, 0:w]
    fall = 1 - 0.25 * (((xx - w * 0.55) / w) ** 2 + ((yy - h * 0.30) / h) ** 2)
    # the tissue's own fibre (foraged scan) shows in the back-lit glass
    tis = load_paper(TISSUE, (w, h), (0, 0, 0), 0.20, crop=TISSUE_CROP)
    col = recess + (amber * fall[..., None] + tis - recess) * lit
    sil = Image.new("L", (w, h), 0)
    sd = ImageDraw.Draw(sil)
    off = rise_y(k) * h * 0.98
    yaw = math.radians(yaw_deg(k))
    ncx, ncy = w * 0.42, h * 0.40 + off
    sd.polygon([(w * 0.02, h + 4), (w * 0.06, ncy + h * 0.16), (w * 0.20, ncy + h * 0.08), (ncx - w * 0.08, ncy + h * 0.05),
                (ncx + w * 0.10, ncy + h * 0.05), (w * 0.66, ncy + h * 0.09), (w * 0.78, ncy + h * 0.17), (w * 0.82, h + 4)], fill=255)
    sd.rectangle((ncx - w * 0.075, ncy - h * 0.04, ncx + w * 0.075, ncy + h * 0.08), fill=255)
    phi = math.radians(-80.0) + yaw
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
    lean = smooth((k - 536) / 16.0)
    sil = sil.filter(ImageFilter.GaussianBlur(16.0 * (1.0 - 0.6 * lean)))
    sa = np.asarray(sil).astype(np.float32)[..., None] / 255.0
    shadow = np.array([44, 36, 32], np.float32)
    col = col * (1 - sa * 0.9 * lit) + shadow * sa * 0.9 * lit
    cx = w * (0.70 - 0.08 * curtain_dx(k))
    edge = cx + np.sin(np.arange(h) / 14.0) * 3
    curt = (np.arange(w)[None, :] >= edge[:, None]).astype(np.float32)
    curt = np.asarray(Image.fromarray((curt * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(4))).astype(np.float32)[..., None] / 255
    col = col * (1 - curt * 0.38) + np.array([250, 226, 176], np.float32) * curt * 0.38 * lit + col * curt * 0.38 * (1 - lit)
    img = to_img(col)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, w, 18), fill=(54, 62, 63, 255))
    d.rectangle((0, 0, 9, h), fill=(62, 71, 72, 255))
    d.line((0, 48, w, 48), fill=(150, 150, 138, 255), width=4)
    d.rectangle((0, h - 72, w, h - 66), fill=(62, 63, 48, 255))
    for xx_ in range(10, w, 14):
        d.line((xx_, h - 66, xx_, h), fill=(70, 70, 54, 255), width=2)
    return img

TISSUE = "loc_blank_0001.jpg"          # replaced by the foraged tissue scan if one is found
TISSUE_CROP = (900, 700, 1600, 1800)
if os.path.exists(os.path.join(SRC, "tissue.jpg")):
    TISSUE, TISSUE_CROP = "tissue.jpg", None

if __name__ == "__main__":
    if sys.argv[1] == "build":
        build_all()
        print("cached")
    else:
        out = sys.argv[2]
        os.makedirs(out, exist_ok=True)
        for kk in [int(a) for a in sys.argv[3:]]:
            frame(kk).save(os.path.join(out, f"f{kk:04d}.png"))

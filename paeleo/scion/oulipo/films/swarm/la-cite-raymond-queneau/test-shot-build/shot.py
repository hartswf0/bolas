"""TEST SHOT · La Cité Raymond Queneau · S3 key shot, f456-f623 (19.0-26.0 s of the master).

Handmade cut-paper model built from foraged paper scans (see test-shot-ledger.json).
frame(k) is a pure function of the master frame number k.

Techniques
  #5 Norstein multiplane: planes P0 sky, P1 haze/far block, P3 near block (facade + curved
     roof + end wall), P4 saplings + hedge, P5 pavement/road, P6 verge, P7 fence post; a haze
     field denser low; exposure schedule (dusk = lower exposure on paper, lamps lit).
  #6 Whitney: window i lights at step s(i) = 37 i mod 96, frame = round(24 (6.1 + 0.9 s));
     3-frame attack; each lit window breathes 0.5 % with phase 2 pi i / 96, period 3.1 s;
     saplings sway on two incommensurate oscillators (0.37 Hz, 0.23 Hz).
  #47 Sound-to-action: the silhouette's rise/hold/turn and the curtain settle are the body
     action the two soundtracks read (cue maps in cues.json).

Usage: python3 -I shot.py <out_dir_for_png_frames> [k ...]
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SRC = "/home/user/bolas/paeleo/scion/oulipo/films/sources/la-cite-raymond-queneau/test-shot/paper"
PW, PH = 960, 464          # picture master size (caption band is added by the reel)
SS = 2                      # supersample for the composite
FPS = 24
K0, K1 = 456, 624           # shot span (master frames)

rng = np.random.RandomState(1998)

# ------------------------------------------------------------------ score ---
def step_of(i):
    return (37 * i) % 96

def light_frame(i):
    s = step_of(i)
    return int(round(FPS * (6.1 + 0.9 * s))) if s <= 21 else None

LIGHT = {i: light_frame(i) for i in range(96) if light_frame(i) is not None}
assert LIGHT[16] == 492 and LIGHT[47] == 384 and LIGHT[39] == 211

def glow(i, k):
    f = LIGHT.get(i)
    if f is None or k < f - 2:
        return 0.0
    a = min(1.0, (k - (f - 3)) / 3.0)                       # 3-frame attack from frame below
    breathe = 1.0 + 0.005 * math.sin(2 * math.pi * (k / FPS) / 3.1 + 2 * math.pi * i / 96)
    return a * breathe

def exposure(k):
    return 0.93 - 0.15 * (k - 384) / 239.0                 # S3 drift 0.93 -> 0.78

# ------------------------------------------------------- paper (foraged) ---
def load_paper(name, size, levels):
    """Crop a foraged scan, grade it only by per-channel levels toward a target median."""
    im = Image.open(os.path.join(SRC, name)).convert("RGB")
    w, h = im.size
    tw, th = size
    sc = max(tw / w, th / h)
    im = im.resize((int(w * sc) + 1, int(h * sc) + 1), Image.LANCZOS).crop((0, 0, tw, th))
    a = np.asarray(im).astype(np.float32)
    med = np.median(a.reshape(-1, 3), axis=0)
    target, contrast = levels
    out = (a - med) * contrast + np.array(target, np.float32)
    return np.clip(out, 0, 255)

# --------------------------------------------------------------- facade ---
# Facade sheet in its own flat texture space (the real cut sheet, before it is set at an angle).
BAYW, FLH = 100, 92
NB, NF = 24, 4
FW = BAYW * NB                     # 2400
GF = 110                           # ground floor height
FH = NF * FLH + GF                 # 478
WIN_W, WIN_H = 54, 62

def win_rect(i):
    fl, bay = divmod(i, NB)
    x0 = bay * BAYW + (BAYW - WIN_W) // 2
    y0 = fl * FLH + 16
    return x0, y0, x0 + WIN_W, y0 + WIN_H

LOGGIA_BAYS = {2, 3, 7, 8, 12, 13, 18, 19, 22, 23}

def hand_poly(pts, jit=1.2, seed=0):
    r = np.random.RandomState(seed)
    out = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        n = max(2, int(math.hypot(x1 - x0, y1 - y0) / 14))
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append((x0 + (x1 - x0) * t + r.normal(0, jit), y0 + (y1 - y0) * t + r.normal(0, jit)))
    return out

def build_facade():
    cream = load_paper("p4.jpg", (FW, FH), ((176, 179, 164), 0.55))
    img = Image.fromarray(cream.astype(np.uint8))
    d = ImageDraw.Draw(img)
    # vertical shade toward bottom (ambient occlusion from hedge/ground)
    a = np.asarray(img).astype(np.float32)
    yy = np.linspace(0, 1, FH)[:, None, None]
    a *= 1.0 - 0.06 * yy
    # eave occlusion under the roof
    a[:22] *= np.linspace(0.78, 1.0, 22)[:, None, None]
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    # window recesses (cut-through holes): recess colour with a dark top lip (occlusion)
    for i in range(NB * NF):
        x0, y0, x1, y1 = win_rect(i)
        d.polygon(hand_poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 0.7, i), fill=(74, 85, 86))
        d.rectangle((x0, y0, x1, y0 + 5), fill=(58, 66, 67))
        d.line((x0 + WIN_W // 2, y0 + 4, x0 + WIN_W // 2, y1), fill=(150, 155, 145), width=2)   # mullion
    # balconies / loggia bands (olive card strips with a shadow under)
    for fl in range(NF):
        for b in LOGGIA_BAYS:
            x0 = b * BAYW + 6
            y = fl * FLH + 16 + WIN_H - 18
            d.rectangle((x0, y + 18, x0 + BAYW - 12, y + 26), fill=(52, 54, 42))          # shadow below
            d.polygon(hand_poly([(x0, y), (x0 + BAYW - 12, y), (x0 + BAYW - 12, y + 18), (x0, y + 18)], 0.8, 500 + fl * 30 + b),
                      fill=(73, 73, 55))
            for xx in range(x0 + 6, x0 + BAYW - 12, 9):
                d.line((xx, y + 2, xx, y + 16), fill=(92, 92, 72), width=1)
    # string course between floors
    for fl in range(1, NF + 1):
        y = fl * FLH + (0 if fl < NF else 2)
        d.line((0, y, FW, y), fill=(160, 163, 150), width=2)
    # ground floor: small windows, the entrance door under bay 16
    gy = NF * FLH
    for b in range(NB):
        if b == 16:
            continue
        x0 = b * BAYW + 30
        d.rectangle((x0, gy + 28, x0 + 40, gy + 70), fill=(80, 90, 90))
        d.rectangle((x0, gy + 28, x0 + 40, gy + 32), fill=(60, 68, 68))
    x0 = 16 * BAYW + 18
    d.rectangle((x0 - 6, gy + 10, x0 + BAYW - 30, gy + 16), fill=(120, 126, 118))     # canopy
    d.rectangle((x0, gy + 18, x0 + BAYW - 36, FH), fill=(64, 72, 70))                   # door (closed)
    d.line((x0 + (BAYW - 36) // 2, gy + 20, x0 + (BAYW - 36) // 2, FH), fill=(90, 98, 95), width=2)
    # downpipes
    for b in (6, 11, 17):
        d.line((b * BAYW, 0, b * BAYW, FH), fill=(140, 146, 138), width=4)
    return img

ROOF_H = 150
def build_roof():
    """Curved zinc roof seen from below: the quarter-cylinder's apparent band, shaded across the curve."""
    slate = load_paper("p7.jpg", (FW, ROOF_H), ((92, 106, 110), 0.7))
    v = np.linspace(0, 1, ROOF_H)[:, None, None]            # 0 = ridge (top), 1 = eave
    # sheen band where the curve faces the sky; darker at ridge and near the eave
    sheen = np.exp(-((v - 0.42) / 0.20) ** 2)
    base = np.array([77, 91, 93], np.float32)
    hi = np.array([119, 133, 147], np.float32)
    tint = base + (hi - base) * sheen
    a = slate - np.array([92, 106, 110]) + tint
    # standing seams
    xs = np.arange(FW)
    seam = ((xs % 40) < 2)[None, :, None]
    a = np.where(seam, a * 0.9, a)
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    # dormers (pale cut card with a recess)
    for j in range(12):
        cx = j * 200 + 100
        x0, y0 = cx - 26, 62
        d.rectangle((x0 - 3, y0 + 46, x0 + 55, y0 + 52), fill=(60, 72, 74))           # shadow below
        d.polygon(hand_poly([(x0, y0), (x0 + 52, y0), (x0 + 52, y0 + 46), (x0, y0 + 46)], 0.6, 900 + j), fill=(190, 207, 212))
        d.rectangle((x0 + 10, y0 + 10, x0 + 42, y0 + 40), fill=(96, 108, 112))
    # gutter
    d.rectangle((0, ROOF_H - 6, FW, ROOF_H), fill=(150, 160, 160))
    return img

# ------------------------------------------------------------- camera ---
# Pinhole camera at eye level 1.5 m. Facade is a vertical plane; texture px -> metres.
M = 3.2 / BAYW                       # one bay = 3.2 m
F_PX = 940 * SS                      # focal length (supersampled px)
CX, CY = PW * SS * 0.5, PH * SS * 0.60   # horizon at 0.60 H
EYE = 1.5
# facade start (left/far) and end (right/near) points on the ground, metres (X right, Z forward)
LEN = FW * M                         # 76.8 m
_ang = math.radians(25.0)            # facade recedes to the left at 25 deg to the picture plane
DIR = np.array([math.cos(_ang), -math.sin(_ang)])
B = np.array([24.68, 58.0])          # near (right) end, solved so the block spans the frame
A = B - DIR * LEN

def proj(X, Y, Z):
    return (CX + F_PX * X / Z, CY - F_PX * (Y - EYE) / Z)

def facade_pt(u_px, v_px, back=0.0):
    """u along the facade (tex px), v height from roof base down (tex px from top of facade); back = set-back in m."""
    p = A + DIR * (u_px * M)
    nrm = np.array([DIR[1], -DIR[0]])   # points away from camera (into the building)
    p = p + nrm * back
    Y = (FH - v_px) * M
    return proj(p[0], Y, p[1])

def homography(src, dst):
    """Coefficients for PIL PERSPECTIVE (maps output px -> input px)."""
    Am, bm = [], []
    for (x, y), (u, v) in zip(dst, src):
        Am.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); bm.append(u)
        Am.append([0, 0, 0, x, y, 1, -v * x, -v * y]); bm.append(v)
    return np.linalg.solve(np.array(Am, float), np.array(bm, float)).tolist()

OUT_SIZE = (PW * SS, PH * SS)

def warp(tex, src_quad, dst_quad):
    co = homography(src_quad, dst_quad)
    rgba = tex if tex.mode == "RGBA" else tex.convert("RGBA")
    return rgba.transform(OUT_SIZE, Image.PERSPECTIVE, co, Image.BICUBIC)

# --------------------------------------------------------- the planes ---
FACADE = build_facade()
ROOF = build_roof()

def facade_quad():
    return [facade_pt(0, 0), facade_pt(FW, 0), facade_pt(FW, FH), facade_pt(0, FH)]

RROOF = 3.0   # roof radius, metres (quarter cylinder)
N_STRIP = 10

def roof_strips():
    """Quarter-cylinder: strip j spans angles th0..th1; height Y = top + R sin th, set-back R(1-cos th)."""
    strips = []
    top = FH * M
    for j in range(N_STRIP):
        th0 = (math.pi / 2) * j / N_STRIP
        th1 = min(math.pi / 2, (math.pi / 2) * (j + 1.35) / N_STRIP)   # overlap: no seams between strips
        def pt(u, th):
            p = A + DIR * (u * M) + np.array([DIR[1], -DIR[0]]) * (RROOF * (1 - math.cos(th)))
            return proj(p[0], top + RROOF * math.sin(th), p[1])
        # texture rows: eave at bottom (v=ROOF_H) -> ridge at top (v=0); map by angle
        v0 = ROOF_H * (1 - j / N_STRIP)
        v1 = ROOF_H * (1 - th1 / (math.pi / 2))
        src = [(0, v1), (FW, v1), (FW, v0), (0, v0)]
        dst = [pt(0, th1), pt(FW, th1), pt(FW, th0), pt(0, th0)]
        strips.append((src, dst))
    return strips

def build_roof_map():
    top = FH * M
    nrm = np.array([DIR[1], -DIR[0]])
    us = np.arange(0, FW, 0.5)
    ths = np.linspace(0, math.pi / 2, 900)
    U, TH = np.meshgrid(us, ths)
    P = A[None, None, :] + DIR[None, None, :] * (U[..., None] * M) + nrm[None, None, :] * (RROOF * (1 - np.cos(TH)))[..., None]
    Y = top + RROOF * np.sin(TH)
    X = CX + F_PX * P[..., 0] / P[..., 1]
    Yp = CY - F_PX * (Y - EYE) / P[..., 1]
    xi = np.clip(np.round(X).astype(int), 0, OUT_SIZE[0] - 1).ravel()
    yi = np.clip(np.round(Yp).astype(int), 0, OUT_SIZE[1] - 1).ravel()
    v = np.clip(((1 - TH / (math.pi / 2)) * (ROOF_H - 1)).astype(int), 0, ROOF_H - 1).ravel()
    u = np.clip(U.astype(int), 0, FW - 1).ravel()
    return xi, yi, (v, u)

ROOF_MAP = None

def end_wall_poly():
    """Right end wall: cream, curved top (quarter circle profile), receding into the block."""
    top = FH * M
    pB = A + DIR * LEN
    nrm = np.array([DIR[1], -DIR[0]])
    depth = 11.0
    pts = [proj(pB[0], 0, pB[1])]
    for j in range(N_STRIP + 1):
        th = (math.pi / 2) * j / N_STRIP
        p = pB + nrm * (RROOF * (1 - math.cos(th)))
        pts.append(proj(p[0], top + RROOF * math.sin(th), p[1]))
    pr = pB + nrm * depth
    pts.append(proj(pr[0], top + RROOF, pr[1]))
    pts.append(proj(pr[0], 0, pr[1]))
    return pts

# -------------------------------------------------------- silhouette ---
def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)

def spring(x, overshoot):
    """0..1 with an overshoot that settles (damped)."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    return 1 - math.exp(-6 * x) * math.cos(1.6 * math.pi * x) * (1 - x) - (1 - x) ** 3 * math.exp(-6 * x) * 0 \
        + overshoot * math.sin(math.pi * x) * x * 0

def rise_y(k):
    """Silhouette rise, f502-518: comes up from below the sill, slight overshoot, settles (weight)."""
    if k < 502:
        return 1.0
    x = (k - 502) / 16.0
    if x >= 1:
        # settle over ~4 frames after 518 then breathe very slightly
        s = (k - 518)
        return -0.03 * math.exp(-s / 2.5) * math.cos(s * 0.9) + 0.004 * math.sin(k / FPS * 2 * math.pi / 3.4)
    return 1.0 - (ease(x) * 1.03)

def yaw_deg(k):
    """Head turn toward the road f538-552: 0 -> 25 deg with a 2 deg overshoot settling over 6 frames."""
    if k < 538:
        return 0.0
    if k <= 552:
        x = (k - 538) / 14.0
        return 27.0 * ease(x)
    s = k - 552
    if s >= 6:
        return 25.0
    return 25.0 + 2.0 * math.cos(s / 6.0 * math.pi / 2) ** 2 * (1 if s < 3 else 1) * (1 - s / 6.0) + 0.0

def curtain_dx(k):
    """Curtain edge slides 8 px (tex) f552-566 and settles with a small rebound."""
    if k < 552:
        return 0.0
    x = (k - 552) / 14.0
    if x >= 1:
        return 8.0
    return 8.0 * (ease(min(1, x * 1.25)) + 0.12 * math.sin(math.pi * min(1, x * 1.25)) * (1 - x))

def draw_window16(k, base, lit):
    """Window 16 contents in tex px at 4x for a soft, back-lit shadow edge."""
    x0, y0, x1, y1 = win_rect(16)
    S4 = 4
    w, h = (x1 - x0) * S4, (y1 - y0) * S4
    amber = np.array([240, 190, 110], np.float32)
    recess = np.array([74, 85, 86], np.float32)
    # lamp inside: warmer centre, falloff
    yy, xx = np.mgrid[0:h, 0:w]
    fall = 1 - 0.22 * (((xx - w * 0.55) / w) ** 2 + ((yy - h * 0.35) / h) ** 2)
    col = recess + (amber * fall[..., None] - recess) * lit
    tissue = Image.fromarray(np.clip(col, 0, 255).astype(np.uint8))
    # black card silhouette: shoulders, neck, head (articulated at the neck pivot)
    sil = Image.new("L", (w, h), 0)
    sd = ImageDraw.Draw(sil)
    ry = rise_y(k)
    off = ry * h * 0.95
    neck = (w * 0.44, h * 0.62 + off)
    # shoulders + torso (card)
    sd.polygon([(w * 0.10, h + 4), (w * 0.14, h * 0.80 + off), (w * 0.28, h * 0.70 + off), (w * 0.60, h * 0.70 + off),
                (w * 0.76, h * 0.80 + off), (w * 0.80, h + 4)], fill=255)
    sd.rectangle((neck[0] - w * 0.07, neck[1] - h * 0.06, neck[0] + w * 0.07, neck[1] + h * 0.10), fill=255)
    # head: ellipsoid in 3D, yaw rotates the profile (nose) toward the road (toward camera / right-down)
    yaw = math.radians(yaw_deg(k))
    pitch = math.radians(6.0) * min(1.0, yaw / math.radians(25))
    hr = h * 0.19
    hc = (neck[0], neck[1] - hr * 1.15)
    # initial pose: profile facing left (looking along the street toward the door's approach).
    # yaw turns the face toward the viewer (the road).
    phi = math.radians(-50.0) + yaw                 # starts 3/4 to the left (along the street); turns 25 deg toward the road
    pts = []
    for a in np.linspace(0, 2 * math.pi, 64, endpoint=False):
        pts.append((hc[0] + hr * 0.86 * math.cos(a), hc[1] + hr * math.sin(a)))
    sd.polygon(pts, fill=255)
    # nose and brow: features on the face's front; projected x offset = sin(phi) * depth
    fx = math.sin(phi)            # -1 = full profile left, 0 = frontal
    nose_x = hc[0] + fx * hr * 1.05
    nose_y = hc[1] + hr * 0.10 + pitch * hr * 0.9
    sd.polygon([(hc[0] + fx * hr * 0.70, nose_y - hr * 0.35), (nose_x, nose_y + hr * 0.05), (hc[0] + fx * hr * 0.72, nose_y + hr * 0.20)], fill=255)
    sd.polygon([(hc[0] + fx * hr * 0.75, hc[1] + hr * 0.45), (hc[0] + fx * hr * 0.86, hc[1] + hr * 0.62), (hc[0] + fx * hr * 0.40, hc[1] + hr * 0.85)], fill=255)  # chin
    # hair bun at the back of the head (makes the turn legible: it slides behind the head)
    bx = hc[0] - fx * hr * 0.85
    sd.ellipse((bx - hr * 0.42, hc[1] - hr * 0.75, bx + hr * 0.42, hc[1] - hr * 0.0), fill=255)
    # tissue diffuses the card's edge (the card is behind the tissue, back-lit)
    # lean toward the glass while turning: the shadow on the tissue grows and sharpens (focus as event)
    lean = ease((k - 536) / 16.0)
    if lean > 0:
        sc = 1.0 + 0.10 * lean
        big = sil.resize((int(w * sc), int(h * sc)), Image.BICUBIC)
        ox, oy = int((big.width - w) * 0.45), int((big.height - h) * 0.85)
        sil = big.crop((ox, oy, ox + w, oy + h))
    sil = sil.filter(ImageFilter.GaussianBlur(S4 * (1.0 - 0.45 * lean)))
    sa = np.asarray(sil).astype(np.float32)[..., None] / 255.0
    shadow = np.array([46, 38, 34], np.float32)
    tarr = np.asarray(tissue).astype(np.float32)
    tarr = tarr * (1 - sa * 0.88 * lit) + shadow * sa * 0.88 * lit
    # curtain: second tissue layer covering the right third, its edge slides then settles
    cx = int(w * 0.70 - curtain_dx(k) * S4)
    curt = np.zeros((h, w), np.float32)
    edge = cx + (np.sin(np.arange(h) / 9.0) * 2).astype(int)
    for yrow in range(h):
        curt[yrow, max(0, edge[yrow]):] = 1.0
    curt = np.asarray(Image.fromarray((curt * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3))).astype(np.float32)[..., None] / 255
    tarr = tarr * (1 - curt * 0.35) + np.array([250, 228, 180]) * curt * 0.35 * lit + tarr * 0
    # window frame & mullion are hidden behind the tissue in this window: draw the cross-bar only
    out = Image.fromarray(np.clip(tarr, 0, 255).astype(np.uint8)).resize((x1 - x0, y1 - y0), Image.LANCZOS)
    base.paste(out, (x0, y0))
    dd = ImageDraw.Draw(base)
    dd.rectangle((x0, y0, x1, y0 + 4), fill=(58, 66, 67))
    dd.line((x0, y0 + WIN_H * 0.55, x1, y0 + WIN_H * 0.55), fill=(120, 110, 90), width=1)

def facade_for(k, E):
    tex = FACADE.copy()
    a = np.asarray(tex).astype(np.float32) * E
    tex = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(tex)
    amber = np.array([240, 190, 110], np.float32)
    recess = np.array([74, 85, 86], np.float32) * E
    for i in range(NB * NF):
        g = glow(i, k)
        if i == 16:
            continue
        if g > 0:
            x0, y0, x1, y1 = win_rect(i)
            c = tuple(int(v) for v in recess + (amber - recess) * min(g, 1.02))
            d.polygon(hand_poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 0.7, i), fill=c)
            d.rectangle((x0, y0, x1, y0 + 4), fill=tuple(int(v * 0.75) for v in c))
            d.line((x0 + WIN_W // 2, y0 + 4, x0 + WIN_W // 2, y1), fill=(int(150 * E), int(140 * E), int(110 * E)), width=2)
    draw_window16(k, tex, glow(16, k))
    return tex

# ---------------------------------------------------- foreground sheets ---
def tex_layer(name, size, levels, seed):
    return load_paper(name, size, levels)

HEDGE = tex_layer("p3.jpg", (PW * SS, 140 * SS), ((48, 63, 41), 0.55), 3)
ROAD = tex_layer("p7.jpg", (PW * SS, 200 * SS), ((97, 115, 113), 0.45), 4)
VERGE = tex_layer("p3.jpg", (PW * SS, 220 * SS), ((78, 102, 56), 0.5), 5)
SKY = tex_layer("p4.jpg", (PW * SS, PH * SS), ((240, 231, 239), 0.08), 6)
FENCE = tex_layer("p7.jpg", (60 * SS, PH * SS), ((60, 69, 61), 0.6), 7)
TREE_TEX = tex_layer("p7.jpg", (400, 600), ((96, 104, 88), 0.5), 8)

def sheet(canvas, arr, mask, dx=0, dy=0, shadow=True, E=1.0, edge=True):
    """Composite a cut sheet (RGB float array + L mask) with a soft overcast drop shadow (offset <= 3 px)."""
    m = mask.filter(ImageFilter.GaussianBlur(0.6))
    if shadow:
        sh = mask.filter(ImageFilter.GaussianBlur(5 * SS))
        sh = Image.fromarray((np.asarray(sh) * 0.35).astype(np.uint8))
        canvas.paste((30, 34, 30), (dx + 2 * SS // 2, dy + 3 * SS // 2), sh)
    rgb = Image.fromarray(np.clip(arr * E, 0, 255).astype(np.uint8))
    canvas.paste(rgb, (dx, dy), m)
    if not edge:
        return
    # 1 px lighter cut edge
    edge = mask.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(0.5))
    edge = Image.fromarray((np.asarray(edge) * 0.25).astype(np.uint8))
    canvas.paste((235, 232, 220), (dx, dy - 1), edge)

def jag_mask(size, top_fn, seed):
    w, h = size
    m = Image.new("L", size, 0)
    r = np.random.RandomState(seed)
    pts = [(0, h)]
    for x in range(0, w + 8, 8):
        pts.append((x, top_fn(x) + r.normal(0, 0.8 * SS)))
    pts.append((w, h))
    ImageDraw.Draw(m).polygon(pts, fill=255)
    return m

def sapling(d_mask, x, base_y, height, k, seed):
    """Bare sapling: trunk + forked branches, swaying on two incommensurate oscillators (rad grows with height)."""
    t = k / FPS
    sway = math.radians(1.5) * (0.6 * math.sin(2 * math.pi * 0.37 * t + seed) + 0.4 * math.sin(2 * math.pi * 0.23 * t + 2 * seed))
    r = np.random.RandomState(seed)
    def branch(x0, y0, ang, length, width, depth):
        x1 = x0 + math.sin(ang) * length
        y1 = y0 - math.cos(ang) * length
        d_mask.line((x0, y0, x1, y1), fill=255, width=max(1, int(width)))
        if depth > 0:
            for da in (-0.38 - r.rand() * 0.25, 0.05 + r.rand() * 0.15, 0.32 + r.rand() * 0.3)[: 2 + (depth < 3)]:
                branch(x1, y1, ang + da + sway * (4 - depth), length * (0.62 + r.rand() * 0.12), width * 0.62, depth - 1)
    branch(x, base_y, sway, height * 0.36, 4.0 * SS, 4)

# --------------------------------------------------------------- frame ---
def frame(k):
    E = exposure(k)
    W2, H2 = OUT_SIZE
    sky_top = np.array([245, 235, 241], np.float32)
    sky_low = np.array([234, 225, 239], np.float32)
    dusk = np.array([205, 205, 215], np.float32)
    dmix = (0.93 - E) / 0.15 * 0.45                        # sky sheet cools toward dusk
    yy = np.linspace(0, 1, H2)[:, None, None]
    sky = (sky_top + (sky_low - sky_top) * yy)
    sky = sky + (dusk - sky) * dmix
    sky = sky + (SKY - np.array([240, 231, 239])) * 1.0
    can = Image.fromarray(np.clip(sky * (0.97 + 0.03 * E), 0, 255).astype(np.uint8)).convert("RGB")

    # P1/P2 far block (left, behind), hazed: cut silhouette warped in perspective
    far = Image.new("L", OUT_SIZE, 0)
    fd = ImageDraw.Draw(far)
    hz = int(CY)
    fd.polygon([(0, hz - 150 * SS), (90 * SS, hz - 156 * SS), (150 * SS, hz - 128 * SS), (150 * SS, hz + 14 * SS), (0, hz + 14 * SS)], fill=255)
    farcol = np.full((H2, W2, 3), (150, 158, 156), np.float32)
    for fy in range(0, 5):
        y = hz - 128 * SS + fy * 26 * SS
        for fx in range(0, 7):
            x = 8 * SS + fx * 20 * SS
            farcol[y:y + 10 * SS, x:x + 9 * SS] = (118, 128, 128)
    sheet(can, farcol, far, shadow=False, E=E)

    # P3 near block: facade (homography), curved roof strips, end wall
    tex = facade_for(k, E)
    fq = facade_quad()
    wf = warp(tex, [(0, 0), (FW, 0), (FW, FH), (0, FH)], fq)
    rtex = Image.fromarray(np.clip(np.asarray(ROOF).astype(np.float32) * E, 0, 255).astype(np.uint8))
    # end wall first (it sits behind the facade's right edge visually)
    ew = Image.new("L", OUT_SIZE, 0)
    ImageDraw.Draw(ew).polygon(end_wall_poly(), fill=255)
    endcol = load_end_wall() * E
    sheet(can, endcol, ew, shadow=False, E=1.0)
    # curved roof: forward-project a dense (u, theta) grid of the zinc sheet onto the canvas
    carr = np.asarray(can).copy()
    rt = np.asarray(rtex)
    xs_, ys_, cols = ROOF_MAP
    carr[ys_, xs_] = rt[cols[0], cols[1]]
    can = Image.fromarray(carr)
    # facade shadow/occlusion onto ground (soft, below)
    can.paste(wf, (0, 0), wf)
    # roof-end quarter-circle rim (zinc edge seen in section)
    rim = [facade_pt(FW, 0)]
    top = FH * M
    pB = A + DIR * LEN
    nrm = np.array([DIR[1], -DIR[0]])
    for j in range(N_STRIP + 1):
        th = (math.pi / 2) * j / N_STRIP
        p = pB + nrm * (RROOF * (1 - math.cos(th)))
        rim.append(proj(p[0] + 0.15, top + RROOF * math.sin(th) + 0.15, p[1]))
    ImageDraw.Draw(can).line(rim, fill=tuple(int(c * E) for c in (96, 110, 116)), width=3 * SS)

    # haze field between the block and the hedge: denser low, thins with height (not uniform)
    hzarr = np.asarray(can).astype(np.float32)
    ys = np.arange(H2)[:, None, None] / H2
    dens = np.clip((ys - 0.25) / 0.45, 0, 1) ** 1.6 * 0.16
    xs = np.arange(W2)[None, :, None] / W2
    dens = dens * (1.15 - 0.5 * xs)                        # far (left) end hazier
    hazecol = np.array([226, 222, 228], np.float32) * (0.9 + 0.1 * E)
    hzarr = hzarr * (1 - dens) + hazecol * dens
    can = Image.fromarray(np.clip(hzarr, 0, 255).astype(np.uint8))

    # P4 saplings (cut card) + hedge
    tm = Image.new("L", OUT_SIZE, 0)
    td = ImageDraw.Draw(tm)
    for j, u in enumerate([1.5, 4.6, 7.4, 10.6, 13.5, 15.3, 18.6, 21.3, 23.4]):
        bx, by = facade_pt(u * BAYW, FH)
        bx = bx + (j % 3 - 1) * 6 * SS
        base_y = by + 30 * SS
        scale = (by - facade_pt(u * BAYW, 0)[1])
        sapling(td, bx, base_y, scale * 0.9, k, j + 1)
    tarr = np.asarray(Image.fromarray(TREE_TEX.astype(np.uint8)).resize(OUT_SIZE)).astype(np.float32)
    sheet(can, tarr, tm, shadow=True, E=E, edge=False)

    gl = facade_pt(0, FH)[1]
    gr = facade_pt(FW, FH)[1]
    def hedge_top(x):
        base = gl + (gr - gl) * x / W2
        return base - 12 * SS + 2 * SS * math.sin(x / 23.0) + 1.5 * SS * math.sin(x / 7.3)
    hm = jag_mask((W2, H2), hedge_top, 11)
    harr = np.zeros((H2, W2, 3), np.float32)
    harr[:] = np.asarray(Image.fromarray(HEDGE.astype(np.uint8)).resize((W2, H2))).astype(np.float32)
    sheet(can, harr, hm, shadow=True, E=E)

    # P5 pavement + road: band rising gently left -> right
    def road_top(x):
        return gl + (gr - gl) * x / W2 + 16 * SS
    rm = jag_mask((W2, H2), road_top, 12)
    rarr = np.zeros((H2, W2, 3), np.float32)
    rarr[:] = np.asarray(Image.fromarray(ROAD.astype(np.uint8)).resize((W2, H2))).astype(np.float32)
    # kerb line + faint dashes (cut paper strips)
    rimg = Image.fromarray(np.clip(rarr, 0, 255).astype(np.uint8))
    rd = ImageDraw.Draw(rimg)
    pav = [(0, road_top(0)), (W2, road_top(W2)), (W2, road_top(W2) + 16 * SS), (0, road_top(0) + 12 * SS)]
    rd.polygon(pav, fill=(124, 133, 129))
    for x in range(0, W2, 8):
        y = road_top(x) + 12 * SS + 4 * SS * x / W2
        rd.line((x, y, x + 8, y), fill=(146, 152, 146), width=2 * SS)
    for j in range(7):
        x = j * 160 * SS + 30 * SS
        y = road_top(x) + 70 * SS + (x / W2) * -14 * SS
        rd.polygon([(x, y), (x + 90 * SS, y - 4 * SS), (x + 90 * SS, y - 1 * SS), (x, y + 3 * SS)], fill=(112, 124, 124))
    sheet(can, np.asarray(rimg).astype(np.float32), rm, shadow=True, E=E)

    # P6 verge: grass wedge at lower left
    def verge_top(x):
        return H2 - 2 * SS - (W2 * 0.72 - x) * 0.17 if x < W2 * 0.72 else H2 + 10
    vm = jag_mask((W2, H2), verge_top, 13)
    varr = np.asarray(Image.fromarray(VERGE.astype(np.uint8)).resize((W2, H2))).astype(np.float32)
    sheet(can, varr, vm, shadow=True, E=E)

    # P7 fence post at the right edge, with a wire panel
    fm = Image.new("L", OUT_SIZE, 0)
    fdraw = ImageDraw.Draw(fm)
    px = W2 - 34 * SS
    fdraw.polygon(hand_poly([(px, 292 * SS), (px + 12 * SS, 290 * SS), (px + 13 * SS, H2), (px - 1 * SS, H2)], 0.8, 77), fill=255)
    fdraw.ellipse((px - 2 * SS, 286 * SS, px + 14 * SS, 296 * SS), fill=255)
    for yy_ in range(318, 464, 26):
        fdraw.line((px + 12 * SS, yy_ * SS, W2, (yy_ - 6) * SS), fill=255, width=2 * SS)
    for xx_ in range(int(px / SS) + 16, PW, 14):
        fdraw.line((xx_ * SS, 312 * SS, (xx_ + 4) * SS, H2), fill=255, width=2 * SS)
    farr = np.asarray(Image.fromarray(FENCE.astype(np.uint8)).resize((W2, H2))).astype(np.float32)
    sheet(can, farr, fm, shadow=True, E=E)

    return can.resize((PW, PH), Image.LANCZOS)

ROOF_MAP = build_roof_map()
_END = None
def load_end_wall():
    global _END
    if _END is None:
        _END = load_paper("p4.jpg", (OUT_SIZE[0], OUT_SIZE[1]), ((150, 156, 146), 0.5))  # end wall in soft shade
    return _END

if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    ks = [int(a) for a in sys.argv[2:]] or list(range(K0, K1))
    for k in ks:
        frame(k).save(os.path.join(out, f"f{k:04d}.png"))
        if k % 24 == 0:
            print("frame", k, flush=True)

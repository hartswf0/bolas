"""Anemic cinema, TEST SHOT: T1 -> (W1) -> O_A -> (W2) -> T2 -> (W3) -> O_B, one plate, one clock.

Local frame n = 0..227 is film frame k = n + 96. The whole shot turns at a constant
omega = 1/80 rev/frame (0.30 rev/s), counter-clockwise on screen.

Techniques (SCION prompts read in full):
  #6  Whitney harmonic motion: a single integer clock theta_k = 2*pi*k/80 drives every mark;
      ring eccentricities are an envelope (gain 0.7 -> 1.0 in O_A, 1.0 -> 0.7 in O_B).
  #7  Foldes drawn metamorphosis: per-ring drawing substitution with a 2-frame stagger,
      outside-in: glyph -> squashed glyph -> dash of its arc -> radial slide (circle
      parameters interpolated) -> dashes on the eccentric ring -> closed grooved ring.
      W3 carries a discontinuity marker: dashes regroup, then are substituted by real keys.
  #29 GrabCut: keys are the foraged key photograph cut out by keycut.py.

Optics: 2x supersampled area rendering (1920x1080 -> INTER_AREA 960x540) and a 180 deg
shutter integrating 8 sub-frames of the actual rotation. No grain, vignette, flicker.
Light is fixed to the camera (upper left), the marks rotate under it.

Run: python3 -I shot.py [--frames n1,n2,...]   (writes stills only)  |  no args: full render
"""
import json
import math
import sys
import wave
import subprocess

import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

ROOT = "/home/user/bolas/paeleo/scion/oulipo"
FILMS = ROOT + "/films"
sys.path.insert(0, FILMS)
import kit  # noqa: E402

WS = FILMS + "/swarm/anemic-cinema"
MED = FILMS + "/sources/anemic-cinema/test-shot"
FONT = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

FPS = 24
K0 = 96                       # film frame of local frame 0
NFR = 228
PERIOD = 80                   # frames per revolution (omega_fast)
SS = 2                        # supersampling
W2X, H2X = 960 * SS, 540 * SS
R = 232 * SS                  # plate radius at 2x
N = 2 * R + 32                # plate texture size
C = N / 2.0                   # plate texture centre
NSUB = 8                      # shutter sub-frames
SHUTTER = 0.5                 # 180 deg

# ---------------------------------------------------------------- score
SEG = [  # (name, n0, n1 exclusive)
    ("T1", 0, 30), ("W1", 30, 48), ("OA", 48, 108), ("W2", 108, 126),
    ("T2", 126, 150), ("W3", 150, 168), ("OB", 168, 228)]
BELLS = [30, 108, 150]


def seg_of(n):
    for name, a, b in SEG:
        if a <= n < b:
            return name, n - a, b - a
    raise ValueError(n)


def theta(n):
    """Exact plate angle (radians, ccw on screen) of local frame n; integer clock."""
    k = n + K0
    return 2 * math.pi * (k % PERIOD) / PERIOD


def smooth(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def gain_OA(n):
    name, j, L = seg_of(n)
    if name in ("T1", "W1"):
        return 0.7
    if name == "OA":
        return 0.7 + 0.3 * smooth(j / (L - 1))
    return 1.0


def gain_OB(n):
    name, j, L = seg_of(n)
    if name == "OB":
        return 1.0 - 0.3 * smooth(j / (L - 1))
    return 1.0


# ---------------------------------------------------------------- rings
KR = 5
STAG = 3                      # frames of stagger between rings (5 rings x 3 + 6 stages = 18)
PITCH = 38 * SS
RW = 19 * SS                  # ring width (= gap at mean), 19 px at 1x
RADII = [(205 - 38 * k) * SS for k in range(KR)]
GROOVE = 2.5 * SS             # groove pitch, 2.5 px at 1x


def ring_set(gain, sign=1.0):
    """Ring centres in plate coords (eccentric along the plate x axis)."""
    out = []
    for k in range(KR):
        off = sign * gain * 11.0 * SS * k
        out.append((C + off, C, RADII[k]))
    return out


yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
DPLATE = np.hypot(xx - C, yy - C)
LETTER_GROOVE = (1.0 + 0.015 * np.cos(2 * np.pi * DPLATE / GROOVE)).astype(np.float32)


def ring_fields(rs):
    """Per ring: distance map, value map of the engraved cream stock."""
    out = []
    for k, (cx, cy, r) in enumerate(rs):
        d = np.hypot(xx - cx, yy - cy)
        edge = np.clip(np.abs(d - r) / RW, 0, 1)
        val = 136.0 * (1 + 0.12 * np.cos(2 * np.pi * d / GROOVE)) * (0.9 + 0.1 * (1 - edge ** 2))
        out.append((d, val.astype(np.float32)))
    return out


def full_ring_alpha(d, r):
    return np.clip(RW / 2 - np.abs(d - r) + 0.5, 0, 1).astype(np.float32)


def core_alpha(d):
    return np.clip(26 * SS - d + 0.5, 0, 1).astype(np.float32)


def region_masks(rs):
    """Region k of the plate: inside ring k's outer boundary, outside ring k+1's."""
    bounds = []
    for k, (cx, cy, r) in enumerate(rs):
        d = np.hypot(xx - cx, yy - cy)
        bounds.append(np.clip(r + PITCH / 2 - d + 0.5, 0, 1))
    regs = []
    for k in range(KR):
        outer = np.ones_like(DPLATE) if k == 0 else bounds[k]
        inner = bounds[k + 1] if k + 1 < KR else np.zeros_like(DPLATE)
        regs.append(np.clip(outer - inner, 0, 1).astype(np.float32))
    return regs


def circle_hit(cx, cy, r, phi):
    """Distance t along direction phi from the plate centre to ring circle (cx, cy, r)."""
    ux, uy = math.cos(phi), math.sin(phi)
    ox, oy = cx - C, cy - C
    b = ux * ox + uy * oy
    return b + math.sqrt(max(b * b - (ox * ox + oy * oy) + r * r, 0.0))


# ---------------------------------------------------------------- glyphs
T1 = ("LA PORTE DE SERVICE NE REND PAS SERVICE · LE SERVICE DE LA PORTE NE REND PAS LA PORTE · "
      "LA CLEF DE LA PORTE NE FERME PAS LA CLEF · LA PORTE DE LA CLEF NE FERME PAS LA PORTE · ")
T2 = ("LA CLOCHE DU QUAI SONNE L'HEURE DE LA CLEF · L'HEURE DU QUAI SONNE LA CLEF DE LA CLOCHE · "
      "LA CLEF DU BANC FERME LE QUAI DE L'HEURE · LE QUAI DU BANC FERME L'HEURE DE LA CLEF · ")
CAP = 23 * SS                 # cap height (pitch 38 / cap 23 = 1.65)
FPX = int(round(CAP / 0.729))
FNT = ImageFont.truetype(FONT, FPX)
R_START = RADII[0] + 13 * SS
R_END = RADII[-1] - 16 * SS


def sprite(ch):
    """Glyph alpha at 2x, local frame: x right, y down, glyph centre at the middle."""
    wch = max(int(math.ceil(FNT.getlength(ch))), 1)
    sw, sh = wch + 12, int(CAP * 2.2)
    im = Image.new("L", (sw, sh), 0)
    ImageDraw.Draw(im).text((sw / 2, sh / 2 + CAP / 2), ch, font=FNT, fill=255, anchor="ms")
    return np.asarray(im, np.float32) / 255.0, wch


def glyph_path(text):
    """GlyphPath: per token, (char, r, phi, adv, ring). Inward clockwise spiral, tops out.
    Tracking is solved so the sentence fills the seven turns exactly."""
    widths = [FNT.getlength(c) if c != " " else FNT.getlength(" ") * 1.2 for c in text]
    phi0 = math.radians(-118)
    dr_dphi = PITCH / (2 * math.pi)
    lo, hi = 0.0, 200.0
    for _ in range(50):
        track = (lo + hi) / 2
        r, phi = R_START, phi0
        for wv in widths:
            step = (wv + track) / r
            phi += step
            r -= dr_dphi * step
            if r < R_END:
                break
        if r < R_END:
            hi = track
        else:
            lo = track
    track = lo
    path = []
    r, phi = R_START, phi0
    for c, wv in zip(text, widths):
        adv = wv + track
        mid_phi = phi + (adv / 2) / r
        mid_r = r - dr_dphi * (adv / 2) / r
        ring = int(min(KR - 1, max(0, round((RADII[0] - mid_r) / PITCH))))
        path.append(dict(ch=c, r=mid_r, phi=mid_phi, adv=adv, w=wv, ring=ring))
        step = adv / r
        phi += step
        r -= dr_dphi * step
    for i in range(1, len(path)):
        assert path[i]["phi"] > path[i - 1]["phi"] and path[i]["ring"] >= path[i - 1]["ring"]
    return path, track


SPR = {}


def get_sprite(ch):
    if ch not in SPR:
        SPR[ch] = sprite(ch)
    return SPR[ch]


def paste_affine(canvas, src, ux, uy, vx, vy, cx, cy):
    """Add src (h, w) into canvas with src centre at (cx, cy) and src x/y axes mapped to
    plate vectors (ux, uy) and (vx, vy). Max-combine for alpha."""
    h, w = src.shape
    ext = int(math.ceil(abs(ux) * w / 2 + abs(vx) * h / 2)) + 3
    eyt = int(math.ceil(abs(uy) * w / 2 + abs(vy) * h / 2)) + 3
    bx, by = int(cx) - ext, int(cy) - eyt
    bw, bh = 2 * ext + 1, 2 * eyt + 1
    M = np.array([[ux, vx, cx - bx - ux * w / 2 - vx * h / 2],
                  [uy, vy, cy - by - uy * w / 2 - vy * h / 2]], np.float32)
    out = cv2.warpAffine(src, M, (bw, bh), flags=cv2.INTER_LINEAR)
    x0, y0 = max(bx, 0), max(by, 0)
    x1, y1 = min(bx + bw, canvas.shape[1]), min(by + bh, canvas.shape[0])
    sub = canvas[y0:y1, x0:x1]
    np.maximum(sub, out[y0 - by:y1 - by, x0 - bx:x1 - bx], out=sub)


def draw_glyph(At, g, squash=0.0):
    """squash 0 = the letter; 1 = in-between drawing (half height, stretched to its arc)."""
    if g["ch"] == " ":
        return
    spr, wch = get_sprite(g["ch"])
    phi, r = g["phi"], g["r"]
    tx, ty = -math.sin(phi), math.cos(phi)
    nx, ny = math.cos(phi), math.sin(phi)
    sx = 1.0 + squash * 0.5 * (g["adv"] * 0.9 / max(wch, 1) - 1.0)
    sy = 1.0 - 0.5 * squash
    paste_affine(At, spr, tx * sx, ty * sx, -nx * sy, -ny * sy, C + r * nx, C + r * ny)


def draw_arc(canvas, cx, cy, rad, a_mid, half, thick):
    """Thick antialiased arc (a dash) about (cx, cy). Angles in radians, image convention."""
    sh = 4
    cv2.ellipse(canvas, (int(round(cx * 16)), int(round(cy * 16))),
                (int(round(rad * 16)), int(round(rad * 16))), 0,
                math.degrees(a_mid - half), math.degrees(a_mid + half), 255,
                int(round(thick)), cv2.LINE_AA, sh)


# ---------------------------------------------------------------- keys
KEY = cv2.imread(MED + "/key_rgba.png", cv2.IMREAD_UNCHANGED)
KEY_G = cv2.cvtColor(KEY[:, :, :3], cv2.COLOR_BGR2GRAY).astype(np.float32)
KEY_A = KEY[:, :, 3].astype(np.float32) / 255.0
_lo, _hi = np.percentile(KEY_G[KEY_A > 0.5], [3, 98])
KEY_V = np.clip((KEY_G - _lo) / (_hi - _lo), 0, 1) ** 0.85   # iron tone, 0..1
KEY_ASPECT = KEY.shape[1] / KEY.shape[0]
KEYSPR = {}


def key_scale(k):
    return 0.62 + 0.38 * RADII[k] / RADII[0]


def key_sprite(k):
    if k not in KEYSPR:
        L = 72 * SS * key_scale(k)
        w, h = int(round(L)), int(round(L / KEY_ASPECT))
        a = cv2.resize(KEY_A, (w, h), interpolation=cv2.INTER_AREA)
        v = cv2.resize(KEY_V * KEY_A, (w, h), interpolation=cv2.INTER_AREA)
        KEYSPR[k] = (a, v, L)
    return KEYSPR[k]


def key_slots(rs):
    """Ordered tangential slots: per ring, n_k keys, bow leading clockwise."""
    slots = []
    for k, (cx, cy, r) in enumerate(rs):
        a, v, L = key_sprite(k)
        n = int(2 * math.pi * r // (L * 1.1))
        for i in range(n):
            ang = 2 * math.pi * (i + 0.5 * (k % 2)) / n - math.pi / 2
            slots.append(dict(ring=k, ang=ang, cx=cx, cy=cy, r=r, L=L))
    return slots


def draw_key(Ak, Vk, s, rad_frac=1.0, r_from=None, scale=1.0):
    a, v, L = key_sprite(s["ring"])
    ang = s["ang"]
    r = s["r"] if r_from is None else r_from + (s["r"] - r_from) * rad_frac
    cx = C + (s["cx"] - C) * rad_frac
    cy = C + (s["cy"] - C) * rad_frac
    px, py = cx + r * math.cos(ang), cy + r * math.sin(ang)
    tx, ty = -math.sin(ang), math.cos(ang)
    nx, ny = math.cos(ang), math.sin(ang)
    for src, dst in ((a, Ak), (v, Vk)):
        paste_affine(dst, src, tx * scale, ty * scale, -nx * scale, -ny * scale, px, py)


# ---------------------------------------------------------------- per-frame marks
P1, TRACK1 = glyph_path(T1)
P2, TRACK2 = glyph_path(T2)


def ring_glyphs(path, k):
    return [g for g in path if g["ring"] == k and g["ch"] != " "]


def dash_angles_on_ring(glyphs, ring):
    cx, cy, r = ring
    out = []
    for g in glyphs:
        t = circle_hit(cx, cy, r, g["phi"])
        px, py = C + t * math.cos(g["phi"]), C + t * math.sin(g["phi"])
        out.append(math.atan2(py - cy, px - cx))
    return out


def close_halfwidths(angs, frac):
    """Half-width of each dash so that it covers `frac` of the arc to its neighbours."""
    n = len(angs)
    o = np.argsort(angs)
    a = np.array(angs)[o]
    nxt = np.roll(a, -1) + np.r_[np.zeros(n - 1), 2 * np.pi]
    prv = np.roll(a, 1) - np.r_[2 * np.pi, np.zeros(n - 1)]
    hw = (nxt - prv) / 4 * frac
    out = np.empty(n)
    out[o] = hw
    return out


def text_to_ring_stage(At, Ao, Vo, S, path, k, s, rs, rf, regs, reverse=False):
    """Ring k of a switch at stage s (0..5 forward). Draws into the layers."""
    glyphs = ring_glyphs(path, k)
    ring = rs[k]
    cx, cy, r = ring
    d, val = rf[k]
    if s <= -1:
        for g in glyphs:
            draw_glyph(At, g)
        return
    if s == 0:
        for g in glyphs:
            draw_glyph(At, g, squash=1.0)
        return
    if s >= 5:
        a = full_ring_alpha(d, r)
        if k == KR - 1:
            a = np.maximum(a, core_alpha(d))
        np.maximum(Ao, a, out=Ao)
        Vo += a * val
        S += regs[k]
        return
    angs = dash_angles_on_ring(glyphs, ring)
    if s in (1, 2):
        f = 0.0 if s == 1 else 0.5
        thick = 10 * SS if s == 1 else 14 * SS
        canvas = np.zeros((N, N), np.uint8)
        for g, al in zip(glyphs, angs):
            t = circle_hit(cx, cy, r, g["phi"])
            # interpolate circle parameters: centre, radius, angle, arc length
            ccx, ccy = C + (cx - C) * f, C + (cy - C) * f
            px0, py0 = C + g["r"] * math.cos(g["phi"]), C + g["r"] * math.sin(g["phi"])
            px1, py1 = C + t * math.cos(g["phi"]), C + t * math.sin(g["phi"])
            px, py = px0 + (px1 - px0) * f, py0 + (py1 - py0) * f
            rad = math.hypot(px - ccx, py - ccy)
            am = math.atan2(py - ccy, px - ccx)
            half = (g["adv"] * 0.42) / rad
            draw_arc(canvas, ccx, ccy, rad, am, half, thick)
        np.maximum(At, canvas.astype(np.float32) / 255.0, out=At)
        return
    # s 3, 4: dashes on the eccentric ring, cream stock, optical state
    frac = None if s == 3 else 0.82
    canvas = np.zeros((N, N), np.uint8)
    hws = close_halfwidths(angs, frac) if frac else None
    for i, (g, al) in enumerate(zip(glyphs, angs)):
        half = (g["adv"] * 0.42) / r if hws is None else hws[i]
        draw_arc(canvas, cx, cy, r, al, half, RW)
    a = canvas.astype(np.float32) / 255.0
    if k == KR - 1 and s == 4:
        a = np.maximum(a, core_alpha(d) * 0.6)
    np.maximum(Ao, a, out=Ao)
    Vo += a * val
    S += regs[k]


def text_to_key_stage(At, Ao, Vo, S, path, k, s, slots, regs, rs):
    glyphs = ring_glyphs(path, k)
    if s <= -1:
        for g in glyphs:
            draw_glyph(At, g)
        return
    if s == 0:
        for g in glyphs:
            draw_glyph(At, g, squash=1.0)
        return
    mine = [q for q in slots if q["ring"] == k]
    if s == 1:
        canvas = np.zeros((N, N), np.uint8)
        for g in glyphs:
            draw_arc(canvas, C, C, g["r"], g["phi"], g["adv"] * 0.42 / g["r"], 10 * SS)
        np.maximum(At, canvas.astype(np.float32) / 255.0, out=At)
        return
    r_text = float(np.mean([g["r"] for g in glyphs]))
    if s == 2:  # regroup: n_k dashes of key length at the key slots, on the text radius
        canvas = np.zeros((N, N), np.uint8)
        for q in mine:
            draw_arc(canvas, C, C, r_text, q["ang"], q["L"] * 0.45 / r_text, 13 * SS)
        np.maximum(At, canvas.astype(np.float32) / 255.0, out=At)
        return
    # s >= 3: the real keys (discontinuity marker at s == 3), sliding onto their ring
    frac = 0.5 if s == 3 else 1.0
    Ak = np.zeros((N, N), np.float32)
    Vk = np.zeros((N, N), np.float32)
    for q in mine:
        draw_key(Ak, Vk, q, rad_frac=frac, r_from=r_text, scale=0.85 if s == 3 else 1.0)
    darker = 0.78 + 0.22 * RADII[k] / RADII[0]
    np.maximum(Ao, Ak, out=Ao)
    Vo += (100 + 85 * np.clip(Vk / np.maximum(Ak, 1e-3), 0, 1)) * Ak * darker
    S += regs[k]


def guide_grooves(rs):
    """Faint engraved guide grooves under the key chains (two fine lines per ring)."""
    g = np.zeros((N, N), np.float32)
    for (cx, cy, r) in rs:
        d = np.hypot(xx - cx, yy - cy)
        for rr in (r - 13 * SS, r + 13 * SS):
            g = np.maximum(g, np.clip(1.6 - np.abs(d - rr), 0, 1))
    return g


def layers(n):
    """Plate-coordinate layers for local frame n.
    S: optical-state map. At: text-stock alpha. Ao, Vo: optical-stock alpha and premult value.
    G: guide grooves. flavour: 'A' or 'B' for the optical plate."""
    name, j, L = seg_of(n)
    At = np.zeros((N, N), np.float32)
    Ao = np.zeros((N, N), np.float32)
    Vo = np.zeros((N, N), np.float32)
    S = np.zeros((N, N), np.float32)
    G = None
    flavour = "A"
    if name in ("T1", "T2"):
        for g in (P1 if name == "T1" else P2):
            draw_glyph(At, g)
        flavour = "A" if name == "T1" else "B"
    elif name in ("W1", "OA", "W2"):
        rs = ring_set(gain_OA(n))
        rf = ring_fields(rs)
        regs = region_masks(rs)
        for k in range(KR):
            if name == "OA":
                s = 5
            elif name == "W1":
                s = j - STAG * k
            else:  # reverse: ring -> T2 glyph
                s = min(5, max(-1, 4 - (j - STAG * k)))
            text_to_ring_stage(At, Ao, Vo, S, P1 if name == "W1" else P2, k, min(s, 5), rs, rf, regs)
    else:  # W3, OB
        flavour = "B"
        rs = ring_set(gain_OB(n), sign=-1.0)
        regs = region_masks(rs)
        slots = key_slots(rs)
        G = guide_grooves(rs)
        for k in range(KR):
            s = 5 if name == "OB" else j - STAG * k
            text_to_key_stage(At, Ao, Vo, S, P2, k, s, slots, regs, rs)
    S = np.clip(S, 0, 1)
    if G is None:
        G = np.zeros((N, N), np.float32)
    return S, np.clip(At, 0, 1), np.clip(Ao, 0, 1), Vo, G * S, flavour


# ---------------------------------------------------------------- light (camera-fixed)
sy, sx = np.mgrid[0:N, 0:N].astype(np.float32)
ux, uy = (sx - C) / R, (sy - C) / R
rr = np.hypot(ux, uy)
uz = np.sqrt(np.clip(1 - rr * rr, 0, 1))
DISC = np.clip((1 - rr) * R + 0.5, 0, 1).astype(np.float32)


def lam(L):
    L = np.array(L, np.float32) / np.linalg.norm(L)
    return np.clip(ux * L[0] + uy * L[1] + uz * L[2], 0, 1)


LF_TEXT = lam((-0.38, -0.78, 0.55))            # sphere, key light top / upper left
LF_A = lam((-0.45, -0.55, 0.70))               # convex, soft
LF_B = lam((0.50, 0.55, 0.67))                 # concave: light from the lower right
PLATE_TEXT = 58 + 158 * LF_TEXT
PLATE_A = 22 + 22 * LF_A
PLATE_B = 10 + 22 * LF_B
LIGHT_LET = 0.95 + 0.07 * LF_TEXT
LIGHT_A = 0.86 + 0.22 * LF_A
LIGHT_B = 0.88 + 0.30 * LF_B
WARM = np.array([1.045, 0.99, 0.875], np.float32)
FIELD = 2.0


def rot(img, ang):
    M = cv2.getRotationMatrix2D((C, C), math.degrees(ang), 1.0)
    return cv2.warpAffine(img, M, (N, N), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)


def render(n):
    S, At, Ao, Vo, G, flav = layers(n)
    Mt = At * 238.0 * LETTER_GROOVE
    st1 = np.dstack([S, At, Mt, G])
    st2 = np.dstack([Ao, Vo])
    th = theta(n)
    dth = 2 * math.pi / PERIOD
    accL = np.zeros((N, N), np.float32)
    accS = np.zeros((N, N), np.float32)
    plate_o = PLATE_A if flav == "A" else PLATE_B
    light_o = LIGHT_A if flav == "A" else LIGHT_B
    for q in range(NSUB):
        a = th + dth * SHUTTER * ((q + 0.5) / NSUB - 0.5)
        r1 = rot(st1, a)
        r2 = rot(st2, a)
        s, at, mt, g = r1[..., 0], r1[..., 1], r1[..., 2], r1[..., 3]
        ao, vo = r2[..., 0], r2[..., 1]
        # embossed letters: shadow cast down-right by the camera-fixed light, 1.5 px at 1x
        sh = cv2.GaussianBlur(np.roll(at, (3, 3), (0, 1)), (0, 0), 1.2)
        plate = (1 - s) * PLATE_TEXT * (1 - 0.6 * sh * (1 - at)) + s * (plate_o + 9 * g)
        out = plate * (1 - np.clip(at + ao, 0, 1)) + mt * LIGHT_LET + vo * light_o
        accL += out
        accS += s
    L = accL / NSUB
    Sm = accS / NSUB
    L = FIELD + (L - FIELD) * DISC
    rgb = L[..., None] * (1 + (WARM[None, None] - 1) * (Sm * DISC)[..., None])
    full = np.full((H2X, W2X, 3), FIELD, np.float32)
    x0, y0 = int(W2X / 2 - C), int(H2X / 2 - C)
    full[y0:y0 + N, x0:x0 + N] = rgb
    small = cv2.resize(full, (960, 540), interpolation=cv2.INTER_AREA)
    return np.clip(small + 0.5, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------- sound
def bell_wav():
    """Decode the foraged Fridingen station bell, take one clean strike, level it."""
    p = MED + "/bell_strike.wav"
    data = np.frombuffer(open(p, "rb").read()[44:], np.int16).astype(np.float64) / 32768
    return data


def ledger_dump():
    out = dict(
        T1=T1, T2=T2, track_px_1x=[TRACK1 / SS, TRACK2 / SS], cap_px_1x=CAP / SS,
        pitch_px_1x=PITCH / SS, pitch_over_cap=PITCH / CAP, rings_1x=[r / SS for r in RADII],
        glyphs_per_ring_T1=[len(ring_glyphs(P1, k)) for k in range(KR)],
        glyphs_per_ring_T2=[len(ring_glyphs(P2, k)) for k in range(KR)],
        keys_per_ring=[sum(1 for q in key_slots(ring_set(1.0, -1)) if q["ring"] == k) for k in range(KR)],
        segments=SEG, bells_local_frames=BELLS, period_frames=PERIOD, k0=K0)
    json.dump(out, open(WS + "/test-shot-build/geometry.json", "w"), indent=1, ensure_ascii=False)
    return out


# fixtures on the score
assert all(abs(theta(n + 1) - theta(n) - 2 * math.pi / PERIOD) < 1e-12 or theta(n + 1) < theta(n)
           for n in range(NFR - 1))
assert all((n + K0 + PERIOD) % PERIOD == (n + K0) % PERIOD for n in range(NFR))
kinds = [s[0][0] for s in SEG if not s[0].startswith("W")]
assert all(kinds[i] != kinds[i + 1] for i in range(len(kinds) - 1)), "alternation"
assert "".join(g["ch"] for g in P1) == T1 and "".join(g["ch"] for g in P2) == T2


if __name__ == "__main__":
    info = ledger_dump()
    print({k: v for k, v in info.items() if k not in ("T1", "T2")})
    if len(sys.argv) > 2 and sys.argv[1] == "--frames":
        for n in [int(x) for x in sys.argv[2].split(",")]:
            Image.fromarray(render(n)).save(MED + f"/frame_{n:03d}.png")
            print("frame", n)
        sys.exit(0)
    # full render through kit.Film (grain off)
    film = kit.Film("test-shot", seconds=NFR / FPS)
    cache = {}

    def picture(t, ink):
        n = int(round(t * FPS))
        ink._grain = False
        img = Image.fromarray(render(min(n, NFR - 1)))
        ink.img.paste(img, (0, 0))
        if n % 24 == 0:
            print("  frame", n, flush=True)

    def sound(mix):
        sig = bell_wav()
        for n in BELLS:
            mix.add(sig, n / FPS, gain=1.0)

    film.picture(picture)
    film.sound(sound)
    from pathlib import Path
    film.poster_at = 38 / FPS
    film.render(out_dir=Path(WS))

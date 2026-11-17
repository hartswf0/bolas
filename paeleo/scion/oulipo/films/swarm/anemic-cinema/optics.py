"""Anemic cinema -- U1 optics: the engraved ring disc O_A and the key-ring disc O_B.

Field contract (plan.md section 10): canvas 960x540, plate centre (480, 270), plate radius
R = 232 px; every renderer works at 2x (1920x1080) and the editor downsamples with
cv2.INTER_AREA. theta is in radians, counter-clockwise positive on screen, taken from
score.json. Deterministic (no randomness; SEED = 1926 kept for the contract). Run with
python3 -I.

Angles. Marks live in the PLATE frame, which turns rigidly with the plate. A plate-frame
angle phi is measured in image coordinates (atan2(y, x) with y down): 0 = 3 o'clock,
increasing = clockwise on screen. On screen a mark at plate angle phi sits at phi - theta.
Plate offsets are given in 1x px relative to the plate centre.

Renderers return dict(L=float32 (1080, 1920) 0..255 straight luminance, A=float32 alpha
0..1, tint="warm" | "neutral"). L is meaningful where A > 0. The 180 deg shutter is real:
pass omega (rev/frame) and the renderer integrates `nsub` sub-frames of the actual rotation
across half a frame interval. Softness otherwise comes only from 2x area sampling.

Public API
  ring_set(gain)                         O_A geometry: 7 eccentric rings + grooved core
  render_rings(theta, gain, ring_mask=None, omega=0, nsub=8, detune=0)
  ring_segment_mask(k, a0, a1)           arc of ring k (k = 7 is the core), for ring_mask
  key_ring_set(gain)                     O_B geometry: 6 eccentric rings of keys
  key_slots(gain=1.0)                    ordered tangential key slots (token order)
  key_sprite(i)                          the cut-out key printed into slot i (2x px)
  render_keys(theta, gain, placed=None, omega=0, nsub=8, grooves=True, detune=0)
  plate(kind)                            camera-fixed lit plates: "text", "A", "B"
  compose(plate_L, layers, warm)         preview / reference composite -> 960x540 RGB uint8
  WARM                                   the warm grade (RGB gains) for optical discs

SCIONs: #6 Whitney (one clock, gain envelope, locked vs detuned orbit), #29 GrabCut (keys
from optics_keycut.py; RGBA + masks + failure overlays in sources/anemic-cinema/optics/).
"""
import json
import math
import os

import cv2
import numpy as np

SEED = 1926
ROOT = "/home/user/bolas/paeleo/scion/oulipo"
WS = ROOT + "/films/swarm/anemic-cinema"
MED = ROOT + "/films/sources/anemic-cinema/optics"

W1X, H1X = 960, 540
CX, CY = 480.0, 270.0
R = 232.0
SS = 2
W2X, H2X = W1X * SS, H1X * SS
FIELD = 2.0
WARM = np.array([1.045, 0.99, 0.875], np.float32)

# bbox of the plate at 1x (integer pixel bounds) and at 2x
BX0, BY0 = int(CX - R - 2), int(CY - R - 2)
BX1, BY1 = int(CX + R + 2), int(CY + R + 2)

# ---------------------------------------------------------------- O_A geometry
NR = 7
RING_R = [216.0 - 30.0 * k for k in range(NR)]   # 216 .. 36
RING_W = 15.0                                     # ring width = gap width = 15 px
CORE_R = 14.0
ECC = 11.0                                        # centre drift per ring at gain 1 (px)
GROOVE_1X = 2.5                                   # groove pitch at 1x (5 px at 2x); see ledger
GROOVE_DEPTH = 0.14
STOCK_A = 142.0


def ring_set(gain):
    """O_A rings. Returns list of dict(k, r, w, ox, oy, b) in 1x px, plate frame; k = 7 is the
    grooved core (r = its radius). Centres drift along the plate x axis by ECC*k*gain, so the
    near-side gap closes to 15 - 11*gain px. b = stock brightness: the innermost is brightest
    (it is the near tip of the cone)."""
    out = []
    for k in range(NR):
        out.append(dict(k=k, r=RING_R[k], w=RING_W, ox=ECC * k * gain, oy=0.0,
                        b=0.90 + 0.10 * k / (NR - 1)))
    out.append(dict(k=NR, r=CORE_R, w=2 * CORE_R, ox=ECC * NR * gain, oy=0.0, b=1.02, core=True))
    return out


class RingSeg:
    """An arc of ring k between plate-frame angles a0 and a1 (radians, about the ring's own
    centre, clockwise on screen from a0 to a1). Used inside ring_mask."""

    def __init__(self, k, a0, a1):
        self.k, self.a0, self.a1 = int(k), float(a0), float(a1)

    def coverage(self, alpha, d, sp):
        h = (self.a1 - self.a0) / 2.0
        if h >= math.pi:
            return np.ones_like(alpha)
        c = (self.a0 + self.a1) / 2.0
        dl = np.angle(np.exp(1j * (alpha - c))).astype(np.float32)
        inside = (h - np.abs(dl)) * np.maximum(d, 1.0)
        return np.clip(inside / sp + 0.5, 0, 1)

    def __repr__(self):
        return f"RingSeg(k={self.k}, a0={self.a0:.3f}, a1={self.a1:.3f})"


def ring_segment_mask(k, a0, a1):
    """Arc mask of ring k from a0 to a1 (plate frame, about ring k's centre). Put one RingSeg,
    or a list of them (union), at index k of ring_mask. Evaluated analytically per sample and
    per shutter sub-frame, so the arc ends antialias and motion-blur like the ring itself."""
    return RingSeg(k, a0, a1)


# ---------------------------------------------------------------- lights (camera-fixed)
def _sphere(X, Y):
    ux, uy = (X - CX) / R, (Y - CY) / R
    rr = np.hypot(ux, uy)
    uz = np.sqrt(np.clip(1 - rr * rr, 0, 1))
    return ux, uy, uz, rr


def _lam(ux, uy, uz, L):
    L = np.array(L, np.float32) / np.linalg.norm(L)
    return np.clip(ux * L[0] + uy * L[1] + uz * L[2], 0, 1).astype(np.float32)


L_TEXT = (-0.38, -0.78, 0.55)   # text plates: sphere lit from the top / upper left
L_A = (-0.45, -0.55, 0.70)      # O_A: convex, soft key light upper left
L_B = (0.50, 0.55, 0.67)        # O_B: concave dish under the same upper-left light: its
                                # lit side is the lower right (= convex normals lit from LR)


def _grid(x0, y0, w, h, ss):
    xs = x0 + (np.arange(w * ss, dtype=np.float32) + 0.5) / ss
    ys = y0 + (np.arange(h * ss, dtype=np.float32) + 0.5) / ss
    return np.meshgrid(xs, ys)


def plate(kind):
    """Camera-fixed lit plate at 2x: returns (L, disc_alpha) float32 (1080, 1920).
    kind "text": neutral sphere-lit grey card (L ~ 58 -> 216).
    kind "A"   : dark convex plate under O_A (L ~ 18 -> 46), warm-graded by the editor.
    kind "B"   : black-card concave plate under O_B (L ~ 10 -> 34).
    The plate is rotation invariant (radial light model), so it needs no theta. For the
    switches, blend two plates globally with a scalar (one continuous tone, no annuli)."""
    X, Y = _grid(0, 0, W1X, H1X, SS)
    ux, uy, uz, rr = _sphere(X, Y)
    disc = np.clip((1 - rr) * R * SS + 0.5, 0, 1).astype(np.float32)
    if kind == "text":
        L = 58 + 158 * _lam(ux, uy, uz, L_TEXT)
    elif kind == "A":
        L = 18 + 28 * _lam(ux, uy, uz, L_A)
    elif kind == "B":
        L = 10 + 24 * _lam(ux, uy, uz, L_B)
    else:
        raise ValueError(kind)
    L = FIELD + (L - FIELD) * disc
    return L.astype(np.float32), disc


def _to_plate(X, Y, th):
    """Screen 1x coords -> plate-frame coords (relative to the centre) at plate angle th."""
    dx, dy = X - CX, Y - CY
    c, s = math.cos(th), math.sin(th)
    return dx * c - dy * s, dx * s + dy * c


def _to_screen(px, py, th):
    c, s = math.cos(th), math.sin(th)
    return CX + px * c + py * s, CY - px * s + py * c


def _sub_angles(theta, omega, nsub):
    """180 deg shutter: nsub sub-frame plate angles spread over half a frame interval."""
    if omega == 0 or nsub <= 1:
        return [theta]
    dth = 2 * math.pi * omega * 0.5
    return [theta + dth * ((q + 0.5) / nsub - 0.5) for q in range(nsub)]


def _rings_region(x0, y0, w, h, ss, theta, gain, ring_mask=None, omega=0.0, nsub=8,
                  detune=0.0, groove=None):
    """Analytic O_A rings sampled at ss samples per 1x px over the 1x region (x0, y0, w, h).
    Returns (L, A) at ss resolution. Used at ss = 2 for the film and ss = 8 as ground truth
    in the aliasing test."""
    groove = GROOVE_1X if groove is None else groove
    X, Y = _grid(x0, y0, w, h, ss)
    ux, uy, uz, _ = _sphere(X, Y)
    light = (0.86 + 0.22 * _lam(ux, uy, uz, L_A)).astype(np.float32)
    sp = 1.0 / ss
    rs = ring_set(gain)
    accA = np.zeros(X.shape, np.float32)
    accLA = np.zeros(X.shape, np.float32)
    angs = _sub_angles(theta, omega, nsub)
    for th in angs:
        px, py = _to_plate(X, Y, th)
        for q in rs:
            k = q["k"]
            m = 1.0 if ring_mask is None else ring_mask[k]
            if m is None or (isinstance(m, (int, float)) and m <= 0):
                continue
            ox, oy = q["ox"], q["oy"]
            if detune:
                # Whitney detuned orbit: ring k's offset precesses against the plate
                psi = -theta * detune * k / NR
                ox, oy = ox * math.cos(psi) - oy * math.sin(psi), ox * math.sin(psi) + oy * math.cos(psi)
            # screen bbox of this ring
            scx, scy = _to_screen(ox, oy, th)
            ext = q["r"] + q["w"] / 2 + 2
            i0 = max(int((scy - ext - y0) * ss), 0)
            i1 = min(int((scy + ext - y0) * ss) + 1, X.shape[0])
            j0 = max(int((scx - ext - x0) * ss), 0)
            j1 = min(int((scx + ext - x0) * ss) + 1, X.shape[1])
            if i0 >= i1 or j0 >= j1:
                continue
            sl = (slice(i0, i1), slice(j0, j1))
            ddx, ddy = px[sl] - ox, py[sl] - oy
            d = np.sqrt(ddx * ddx + ddy * ddy)
            if q.get("core"):
                a = np.clip((q["r"] - d) / sp + 0.5, 0, 1)
                prof = 0.94 + 0.06 * np.clip(1 - (d / q["r"]) ** 2, 0, 1)
            else:
                u = np.abs(d - q["r"])
                a = np.clip((q["w"] / 2 - u) / sp + 0.5, 0, 1)
                prof = 0.90 + 0.10 * np.clip(1 - (u / (q["w"] / 2)) ** 2, 0, 1)
            if not isinstance(m, (int, float)):
                segs = m if isinstance(m, (list, tuple)) else [m]
                alpha = np.arctan2(ddy, ddx)
                cov = np.zeros_like(a)
                for sg in segs:
                    np.maximum(cov, sg.coverage(alpha, d, sp), out=cov)
                a = a * cov
            elif m < 1:
                a = a * float(m)
            gr = 1.0 + GROOVE_DEPTH * np.cos((2 * np.pi / groove) * d)
            val = STOCK_A * q["b"] * prof * gr * light[sl]
            accA[sl] += a
            accLA[sl] += a * val
    n = len(angs)
    A = np.clip(accA / n, 0, 1)
    L = np.where(accA > 1e-6, accLA / np.maximum(accA, 1e-6), 0).astype(np.float32)
    return L, A.astype(np.float32)


def _full(Lr, Ar):
    L = np.zeros((H2X, W2X), np.float32)
    A = np.zeros((H2X, W2X), np.float32)
    L[BY0 * SS:BY1 * SS, BX0 * SS:BX1 * SS] = Lr
    A[BY0 * SS:BY1 * SS, BX0 * SS:BX1 * SS] = Ar
    return L, A


def render_rings(theta, gain, ring_mask=None, omega=0.0, nsub=8, detune=0.0):
    """O_A at plate angle theta (rad, ccw-positive) with eccentric gain `gain` (0.7..1.0).
    ring_mask: None = all 7 rings + core; else a length-8 sequence (index 7 = core) whose
    entries are a coverage float 0..1, a RingSeg, or a list of RingSegs.
    omega: rotation in rev/frame for the 180 deg shutter (0 = a still exposure).
    detune: Whitney orbit detune (0 = locked, the chosen profile; 0.02 = test only; needs
    an unwrapped theta). Returns dict(L, A, tint="warm") at 2x."""
    Lr, Ar = _rings_region(BX0, BY0, BX1 - BX0, BY1 - BY0, SS, theta, gain, ring_mask,
                           omega, nsub, detune)
    L, A = _full(Lr, Ar)
    return dict(L=L, A=A, tint="warm")


# ---------------------------------------------------------------- keys (GrabCut cutouts)
# repair 2: only K0 (Noy-nac, CC BY-SA 4.0) is used, as the acceptance bar requires; the odd
# rings carry the same cutout mirrored (teeth down) where K1 used to be.
KEY_FILES = {"K0": MED + "/key0_rgba.png"}
_KEYSRC = {}


def _key_src(kid):
    if kid not in _KEYSRC:
        im = cv2.imread(KEY_FILES[kid], cv2.IMREAD_UNCHANGED)
        g = cv2.cvtColor(im[:, :, :3], cv2.COLOR_BGR2GRAY).astype(np.float32)
        a = im[:, :, 3].astype(np.float32) / 255.0
        lo, hi = np.percentile(g[a > 0.5], [3, 98])
        v = np.clip((g - lo) / (hi - lo), 0, 1) ** 0.9
        _KEYSRC[kid] = (a, v, im.shape[1] / im.shape[0])
    return _KEYSRC[kid]


NKR = 6
KEY_R = [206.0, 168.0, 134.0, 104.0, 78.0, 56.0]
KEY_PITCH = [38.0, 34.0, 30.0, 26.0, 22.0, 22.0]
KEY_H_FRAC = 0.72          # key height (bow) as a fraction of the local ring pitch
KEY_ECC = 5.0              # centre drift per ring at gain 1 (px), REVERSED sign (-x)
KEY_GAP = 1.04             # chain spacing: key length x 1.04 per slot (bow nearly touching bit)
ASPECT0 = 1221 / 418       # K0 crop aspect (length / height), sets every ring's key length
STOCK_KEY = (114.0, 78.0)  # cream print: L = 114 + 78 * tone


def key_ring_set(gain):
    """O_B rings. Returns list of dict(k, r, ox, oy, key, length, height, n, b), 1x px, plate
    frame. Offsets run the opposite way to O_A (-x) and inner rings are smaller and darker
    (b falls 1.0 -> 0.80): the far end of a funnel."""
    out = []
    for k in range(NKR):
        h = KEY_H_FRAC * KEY_PITCH[k]
        length = h * ASPECT0
        n = int(2 * math.pi * KEY_R[k] // (length * KEY_GAP))
        out.append(dict(k=k, r=KEY_R[k], ox=-KEY_ECC * k * gain, oy=0.0,
                        key="K0", flip=(k % 2 == 1), length=length, height=h, n=n,
                        b=1.0 - 0.20 * k / (NKR - 1)))
    return out


def key_slots(gain=1.0):
    """Ordered tangential slots for O_B, in TOKEN ORDER: ring 0 (outer) first, then inward;
    within a ring, clockwise from 12 o'clock (plate frame), matching the reading order of
    the spiral. Each slot: i, ring, key, ang (rad, about the ring's own centre, plate frame),
    ox, oy (ring centre), r, pos (key centre rel. plate centre, 1x px), phi (angle of pos
    about the plate centre), tangent (unit, clockwise = bit -> bow), length, height, b."""
    slots = []
    i = 0
    for q in key_ring_set(gain):
        for j in range(q["n"]):
            ang = -math.pi / 2 + 2 * math.pi * (j + 0.5 * (q["k"] % 2)) / q["n"]
            px = q["ox"] + q["r"] * math.cos(ang)
            py = q["oy"] + q["r"] * math.sin(ang)
            slots.append(dict(i=i, ring=q["k"], key=q["key"], flip=q["flip"], ang=ang, ox=q["ox"], oy=q["oy"],
                              r=q["r"], pos=[px, py], phi=math.atan2(py, px),
                              tangent=[-math.sin(ang), math.cos(ang)],
                              length=q["length"], height=q["height"], b=q["b"]))
            i += 1
    return slots


_SPR = {}


def key_sprite(i, scale=1.0):
    """The real cut-out key for slot i at 2x: dict(A, V (tone 0..1, premultiplied by A),
    key, length_2x, height_2x). Orientation: bit at the left (sprite -x), bow at the right
    (sprite +x); teeth up on even rings, the same K0 cutout mirrored (teeth down) on odd rings.
    Area-resampled from the GrabCut RGBA."""
    s = key_slots()[i]
    tag = (s["key"], s["flip"], round(s["length"] * scale, 2))
    if tag not in _SPR:
        a, v, asp = _key_src(s["key"])
        Lp = max(int(round(s["length"] * scale * SS)), 4)
        hp = max(int(round(Lp / asp)), 2)
        A = cv2.resize(a, (Lp, hp), interpolation=cv2.INTER_AREA)
        V = cv2.resize(v * a, (Lp, hp), interpolation=cv2.INTER_AREA)
        if s["flip"]:
            A, V = np.ascontiguousarray(A[::-1]), np.ascontiguousarray(V[::-1])
        _SPR[tag] = dict(A=A, V=V, key=s["key"], length_2x=Lp, height_2x=hp)
    return _SPR[tag]


def _paste_over(LA, A, spr, ex, ey, fx, fy, cx2, cy2, val_fn):
    """Composite sprite (premult tone V, alpha) 'over' into LA/A (2x canvas) with sprite
    x axis -> (ex, ey) and y axis -> (fx, fy) (2x px per sprite px), centre at (cx2, cy2)."""
    a, v = spr["A"], spr["V"]
    h, w = a.shape
    hx = abs(ex) * w / 2 + abs(fx) * h / 2 + 3
    hy = abs(ey) * w / 2 + abs(fy) * h / 2 + 3
    bx, by = int(cx2 - hx), int(cy2 - hy)
    bw, bh = int(2 * hx) + 2, int(2 * hy) + 2
    M = np.array([[ex, fx, cx2 - bx - ex * w / 2 - fx * h / 2],
                  [ey, fy, cy2 - by - ey * w / 2 - fy * h / 2]], np.float32)
    aa = cv2.warpAffine(a, M, (bw, bh), flags=cv2.INTER_LINEAR)
    vv = cv2.warpAffine(v, M, (bw, bh), flags=cv2.INTER_LINEAR)
    x0, y0 = max(bx, 0), max(by, 0)
    x1, y1 = min(bx + bw, W2X), min(by + bh, H2X)
    if x0 >= x1 or y0 >= y1:
        return
    aa = aa[y0 - by:y1 - by, x0 - bx:x1 - bx]
    vv = vv[y0 - by:y1 - by, x0 - bx:x1 - bx]
    tone = np.where(aa > 1e-4, vv / np.maximum(aa, 1e-4), 0)
    lv = val_fn(tone, y0, y1, x0, x1)
    sA = A[y0:y1, x0:x1]
    sLA = LA[y0:y1, x0:x1]
    sLA *= (1 - aa)
    sLA += aa * lv
    sA *= (1 - aa)
    sA += aa


_LIGHT_B = None


def _light_b():
    global _LIGHT_B
    if _LIGHT_B is None:
        X, Y = _grid(0, 0, W1X, H1X, SS)
        ux, uy, uz, _ = _sphere(X, Y)
        _LIGHT_B = (0.84 + 0.30 * _lam(ux, uy, uz, L_B)).astype(np.float32)
    return _LIGHT_B


def _guides_region(theta, gain, angs, detune=0.0):
    """Faint engraved guide grooves: two fine circles per key ring, just outside the chain."""
    x0, y0, w, h = BX0, BY0, BX1 - BX0, BY1 - BY0
    X, Y = _grid(x0, y0, w, h, SS)
    sp = 1.0 / SS
    acc = np.zeros(X.shape, np.float32)
    for th in angs:
        px, py = _to_plate(X, Y, th)
        for q in key_ring_set(gain):
            ox, oy = q["ox"], q["oy"]
            if detune:
                psi = -theta * detune * q["k"] / NKR
                ox, oy = ox * math.cos(psi), ox * math.sin(psi)
            scx, scy = _to_screen(ox, oy, th)
            ext = q["r"] + q["height"] / 2 + 6
            i0, i1 = max(int((scy - ext - y0) * SS), 0), min(int((scy + ext - y0) * SS) + 1, X.shape[0])
            j0, j1 = max(int((scx - ext - x0) * SS), 0), min(int((scx + ext - x0) * SS) + 1, X.shape[1])
            sl = (slice(i0, i1), slice(j0, j1))
            d = np.hypot(px[sl] - ox, py[sl] - oy)
            for rr in (q["r"] - q["height"] / 2 - 2.5, q["r"] + q["height"] / 2 + 2.5):
                np.maximum(acc[sl], np.clip((0.6 - np.abs(d - rr)) / sp + 0.5, 0, 1), out=acc[sl])
    return acc / len(angs)


def render_keys(theta, gain, placed=None, omega=0.0, nsub=8, grooves=True, detune=0.0):
    """O_B at plate angle theta with eccentric gain `gain` (1.0 -> 0.7 in the film).
    placed: None = every slot at home; int n = the first n slots (token order); an iterable
    of slot indices; or a dict {i: overrides} drawing only those slots, where overrides may
    set pos=[px, py] (1x, plate frame rel. centre), ang (tangent direction = ang + 90 deg),
    scale, alpha (0..1) -- for the W3 slide. Guide grooves (faint, L 46) are included in the
    same layer when grooves=True. Returns dict(L, A, tint="warm") at 2x."""
    slots = key_slots(gain)
    if placed is None:
        todo = {s["i"]: {} for s in slots}
    elif isinstance(placed, int):
        todo = {s["i"]: {} for s in slots[:placed]}
    elif isinstance(placed, dict):
        todo = placed
    else:
        todo = {int(i): {} for i in placed}
    angs = _sub_angles(theta, omega, nsub)
    LB = _light_b()
    accA = np.zeros((H2X, W2X), np.float32)
    accLA = np.zeros((H2X, W2X), np.float32)
    if grooves:
        g = _guides_region(theta, gain, angs, detune)
        gA = _full(0.55 * g, g)[0]          # guide-groove alpha on the 2x canvas
    for th in angs:
        A = np.zeros((H2X, W2X), np.float32)
        LA = np.zeros((H2X, W2X), np.float32)
        if grooves:
            A[:] = gA
            LA[:] = gA * 46.0
        for i, ov in todo.items():
            s = slots[i]
            sc = ov.get("scale", 1.0)
            spr = key_sprite(i, sc) if sc != 1.0 else key_sprite(i)
            ox, oy = s["ox"], s["oy"]
            if detune:
                psi = -theta * detune * s["ring"] / NKR
                ox, oy = ox * math.cos(psi), ox * math.sin(psi)
            ang = ov.get("ang", s["ang"])
            if "pos" in ov:
                ppx, ppy = ov["pos"]
            else:
                ppx, ppy = ox + s["r"] * math.cos(ang), oy + s["r"] * math.sin(ang)
            sx, sy = _to_screen(ppx, ppy, th)
            tpx, tpy = -math.sin(ang), math.cos(ang)        # plate tangent (cw)
            c, sn = math.cos(th), math.sin(th)
            ex, ey = tpx * c + tpy * sn, -tpx * sn + tpy * c   # screen tangent
            # sprite +y -> inward normal on screen; outward plate normal = (cos ang, sin ang)
            npx, npy = math.cos(ang), math.sin(ang)
            nx, ny = npx * c + npy * sn, -npx * sn + npy * c
            fx, fy = -nx, -ny
            alpha = ov.get("alpha", 1.0)
            b = s["b"]

            def val_fn(tone, y0, y1, x0, x1, b=b):
                return (STOCK_KEY[0] + STOCK_KEY[1] * tone) * b * LB[y0:y1, x0:x1]
            if alpha < 1.0:
                spr = dict(spr, A=spr["A"] * alpha, V=spr["V"] * alpha)
            _paste_over(LA, A, spr, ex, ey, fx, fy, sx * SS, sy * SS, val_fn)
        accA += A
        accLA += LA
    n = len(angs)
    Aout = np.clip(accA / n, 0, 1)
    L = np.where(accA > 1e-6, accLA / np.maximum(accA, 1e-6), 0).astype(np.float32)
    return dict(L=L, A=Aout.astype(np.float32), tint="warm")


# ---------------------------------------------------------------- reference composite
def compose(plate_L, layers, warm=True):
    """Composite marks over a plate at 2x, downsample with INTER_AREA to 960x540, and apply
    the warm grade to the disc when warm=True (optical discs) or none (text discs).
    layers: list of render dicts. Returns uint8 (540, 960, 3) RGB."""
    L = plate_L.copy()
    for ly in layers:
        L = L * (1 - ly["A"]) + ly["L"] * ly["A"]
    small = cv2.resize(L, (W1X, H1X), interpolation=cv2.INTER_AREA)
    if warm:
        X, Y = _grid(0, 0, W1X, H1X, 1)
        disc = np.clip(R - np.hypot(X - CX, Y - CY) + 0.5, 0, 1)[..., None]
        rgb = small[..., None] * (1 + (WARM[None, None] - 1) * disc)
    else:
        rgb = np.repeat(small[..., None], 3, axis=2)
    return np.clip(rgb + 0.5, 0, 255).astype(np.uint8)


def geometry():
    """Everything the other units need, JSON-ready."""
    return dict(
        O_A=dict(rings=[dict(k=q["k"], r_1x=q["r"], width_1x=q["w"],
                             centre_offset_1x_at_gain1=[ECC * q["k"], 0.0], stock_b=q["b"])
                        for q in ring_set(1.0)[:NR]],
                 core=dict(r_1x=CORE_R, centre_offset_1x_at_gain1=[ECC * NR, 0.0]),
                 groove_pitch_1x=GROOVE_1X, groove_pitch_2x=GROOVE_1X * SS, groove_depth=GROOVE_DEPTH,
                 stock_L=STOCK_A),
        O_B=dict(rings=[{k: v for k, v in q.items()} for q in key_ring_set(1.0)],
                 n_slots=len(key_slots(1.0)), key_ecc_1x=KEY_ECC))


if __name__ == "__main__":
    print(json.dumps(geometry(), indent=1)[:2000])

# SHOE-DRIFT-1: the interruption layer (150 RGBA frames, 24 fps), identical for Version L (first appearance local
# 14.0) and Version E (local 7.0).  python3 -I render_layer.py <shoe_white.png> <out_dir>
#
# Coordinates: P2 plane, wide framing, picture px (800x540), y down, with the layer's own waterline at WL = 408.
# The editor pastes frame k at integer offset (0, dy) with dy = round(water_y(v, t) - 408) so the pixels stay
# hash-identical while the shoe rides the version's water level (L dy ~ +1..+3, E dy ~ +5..+6).
# Every frame is rendered once at S = 3x in a world strip (x -20..880, y 340..470) = layer_hi/ (for the close shots,
# zoom 2.6: downscale only, never upscale); the wide layer/ is that strip area-downsampled by 3 and placed in 800x540.
#
# Methods: #41 secondary dynamics (bob spring, a damped recoil impulse at the plank contact, pitch wobble that decays;
#   nothing wiggles without a source), #45 occlusion (layer order: water < reflection < rings < shoe(submerged tint)
#   < shoe(above water); B's hand card is drawn ABOVE this layer by the editor in frames 115-134), #29 the cut shoe.
import sys, os, json, math, hashlib
import numpy as np, cv2
from PIL import Image

SHOE, OUT = sys.argv[1], sys.argv[2]
FPS, N = 24, 150
S = 3                       # supersample of the hi strip
X0W, Y0W, X1W, Y1W = -20, 340, 880, 470
WL = 408.0                  # layer reference = the water edge line under the plank (world y); dy is taken from it
FRONT = 16.0                # the shoe floats 16 px nearer the camera on the water plane: in front of the plank, clear of it
SHOE_W = 50.0               # world px (matches performance render: SHOE_W = 50 * Z)
T_CONTACT = 3.6             # s after first appearance: the shoe taps the plank foot (L 17.6, E 10.6)
T_GRASP = 5.6               # s: B's fingers close on the heel (L 19.6, E 12.6); from k = 135 the shoe is in her hand
K_GRASP = 135
K_OCC = (115, 134)          # B's hand card overlaps the shoe (L 18.8-19.6 local)
PATH = [(880, 403), (850, 404), (640, 398), (430, 406), (237.34, 405), (237.34, 405)]   # Catmull-Rom control pts
REST_X = 237.34             # B's grasp point (performance trace hand R x at the retrieve frame)
rng = np.random.RandomState(1956)

os.makedirs(f"{OUT}/layer", exist_ok=True); os.makedirs(f"{OUT}/layer_hi", exist_ok=True)

def catmull(P, u):
    n = len(P) - 3; s = min(max(u, 0), 1) * n; i = min(int(s), n - 1); f = s - i
    p0, p1, p2, p3 = [np.array(P[i + j], float) for j in range(4)]
    return 0.5 * ((2 * p1) + (-p0 + p2) * f + (2 * p0 - 5 * p1 + 4 * p2 - p3) * f * f + (-p0 + 3 * p1 - 3 * p2 + p3) * f ** 3)

def arclen_table(P, M=2000):
    us = np.linspace(0, 1, M); pts = np.array([catmull(P, u) for u in us])
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(pts, axis=0).T))]
    return us, d / d[-1]

US, DS = arclen_table(PATH)

def drift_u(t):
    """fraction of path length: arrives at t = 3.6 s still moving (0.4 of entry speed), so it really taps the plank."""
    s = min(t / T_CONTACT, 1.0)
    return 1.6 * s - 0.6 * s * s

def state(k):
    t = k / FPS
    d = drift_u(t); u = float(np.interp(d, DS, US)); x, y = catmull(PATH, u)
    bob = 3.0 * math.sin(2 * math.pi * t / 0.9)                 # +-3 px, 0.9 s
    pitch = 2.5 * math.sin(2 * math.pi * t / 0.9 + 0.9)         # rocks with the bob
    dx = 0.0
    if t >= T_CONTACT:                                           # contact impulse: recoil + pitch kick, decays (#41)
        dt = t - T_CONTACT; e = math.exp(-dt / 0.35)
        dx = 4.0 * e * math.sin(2 * math.pi * 1.6 * dt)
        pitch += 6.0 * e * math.sin(2 * math.pi * 2.2 * dt)
        x = REST_X
    if k >= K_OCC[0]:                                            # the hand presses the water: the shoe dips 2 px, stills
        f = min((k - K_OCC[0]) / (K_OCC[1] - K_OCC[0]), 1.0)
        bob = bob * (1 - 0.6 * f) + 2.0 * f
    return dict(t=t, x=x + dx, y_wl=WL + FRONT + (y - 405.0) + bob, pitch=pitch, vx=None)

SH = Image.open(SHOE).convert("RGBA")
def shoe_rgba(width_px, rot):
    im = SH.rotate(rot, expand=True, resample=Image.BICUBIC)
    h = max(1, int(round(width_px * im.height / im.width)))
    return np.asarray(im.resize((int(round(width_px)), h), Image.LANCZOS), np.float32) / 255.0

def over(C, src, x0, y0):
    """straight-alpha 'over' of src (h,w,4) onto premultiplied canvas C (H,W,4) at float pos (rounded)."""
    x0, y0 = int(round(x0)), int(round(y0)); h, w = src.shape[:2]; H, W = C.shape[:2]
    xa, ya, xb, yb = max(x0, 0), max(y0, 0), min(x0 + w, W), min(y0 + h, H)
    if xa >= xb or ya >= yb: return
    s = src[ya - y0:yb - y0, xa - x0:xb - x0]; a = s[..., 3:4]
    C[ya:yb, xa:xb, :3] = s[..., :3] * a + C[ya:yb, xa:xb, :3] * (1 - a)
    C[ya:yb, xa:xb, 3:4] = a + C[ya:yb, xa:xb, 3:4] * (1 - a)

def W2H(x, y): return ((x - X0W) * S, (y - Y0W) * S)

# ripple-ring sources: (birth k, world x, strength, seed). Rings at bob troughs while drifting (small), a strong
# set at the contact, small rings from the hand entering the water, a burst as the shoe leaves, three drips after.
RINGS = []
for k in range(0, N):
    t = k / FPS
    ph = (t / 0.9) % 1.0
    if abs(ph - 0.75) < 0.5 / (0.9 * FPS) and k < K_GRASP: RINGS.append((k, None, 0.55, k))
k_c = int(round(T_CONTACT * FPS))
RINGS += [(k_c, None, 1.0, 901), (k_c + 5, None, 0.75, 902), (k_c + 11, None, 0.5, 903)]
RINGS += [(K_OCC[0] + 6, "hand", 0.6, 911), (K_OCC[0] + 14, "hand", 0.5, 912)]
RINGS += [(K_GRASP, None, 1.1, 921), (K_GRASP + 3, None, 0.8, 922)]
RINGS += [(K_GRASP + 4, 241.0, 0.35, 931), (K_GRASP + 8, 239.5, 0.3, 932), (K_GRASP + 13, 240.5, 0.28, 933)]
DASH = {sd: np.random.RandomState(sd).rand(64) for (_, _, _, sd) in RINGS}

def ring_x(src, kb):
    if src is None: return state(min(kb, K_GRASP - 1))["x"]
    if src == "hand": return REST_X + 3.0
    return src

hashes, recs = [], []
Hh, Wh = (Y1W - Y0W) * S, (X1W - X0W) * S
for k in range(N):
    st = state(k); t = st["t"]
    C = np.zeros((Hh, Wh, 4), np.float32)
    xs_h, wl_h = W2H(st["x"], st["y_wl"])
    shoe_on = k < K_GRASP
    if shoe_on:
        s = shoe_rgba(SHOE_W * S, st["pitch"]); h, w = s.shape[:2]
        sub = 0.22                                     # draught: 22 % of the height below the waterline
        y_top = wl_h - h * (1 - sub); x_left = xs_h - w / 2
        # reflection: the shoe mirrored about the waterline, darker, fading, re-rippled every frame, broken in bands
        r = s[::-1].copy()
        rows = np.arange(h)
        shift = (2.2 * S * np.sin(rows / S * 0.55 + t * 9.0) + 1.2 * S * np.sin(rows / S * 1.7 - t * 13.0)).astype(int)
        for yy in range(h): r[yy] = np.roll(r[yy], shift[yy], axis=0)
        band = np.clip(0.55 + 0.45 * np.sin(rows / S * 0.9 + t * 5.0) + 0.25 * np.sin(rows / S * 2.3 - t * 7.0), 0, 1)  # broken by ripple troughs
        r = cv2.GaussianBlur(r, (0, 0), sigmaX=0.4 * S, sigmaY=0.9 * S)
        r[..., :3] = r[..., :3] * 0.50 + 0.06
        r[..., 3] *= (np.linspace(0.42, 0.0, h) * band)[:, None]
        over(C, r[: int(h * 0.7)], x_left, wl_h + 1 * S)
    # ripple rings: broken elliptical arcs, a bright crest with a dark trough 1.5 px below, expanding and fading
    ring = np.zeros((Hh, Wh), np.float32); trough = np.zeros((Hh, Wh), np.float32)
    for (kb, src, strength, sd) in RINGS:
        age = (k - kb) / FPS
        if age < 0 or age > 1.6: continue
        cx = ring_x(src, kb); cxh, cyh = W2H(cx, WL + FRONT + 1.0)
        R = (10 + 30 * age ** 0.8) * S * (0.7 + 0.5 * strength)
        fade = strength * (1 - age / 1.6) ** 1.5
        rnd = DASH[sd]
        for j in range(12):                           # 12 dashes, each with its own gap (broken rings)
            if rnd[j] < 0.28: continue
            a0 = j * 30 + rnd[j + 12] * 12; a1 = a0 + 14 + rnd[j + 24] * 12
            cv2.ellipse(ring, (int(cxh), int(cyh)), (int(R), int(R * 0.13)), 0, a0, a1, fade, int(1.3 * S), cv2.LINE_AA)
            cv2.ellipse(trough, (int(cxh), int(cyh + 1.5 * S)), (int(R), int(R * 0.13)), 0, a0, a1, fade, int(1.1 * S), cv2.LINE_AA)
    # wake while drifting: two trailing broken lines upstream (frame right) of the moving shoe
    if k < k_c:
        sp = 1.0 - k / k_c
        for side in (-1, 1):
            for j in range(5):
                L0 = (14 + j * 9) * S; x_a = xs_h + 22 * S + L0; y_a = wl_h + side * (1.5 + j * 1.2) * S + 2 * S
                cv2.line(ring, (int(x_a), int(y_a)), (int(x_a + 6 * S), int(y_a + side * 0.6 * S)), 0.45 * sp * (1 - j / 5), int(1.2 * S), cv2.LINE_AA)
    ring = cv2.GaussianBlur(ring, (0, 0), 0.6 * S); trough = cv2.GaussianBlur(trough, (0, 0), 0.6 * S)
    # trough (dark L 40) then crest (light L 205): as light on moving water, under the shoe
    for img, val, amax in ((trough, 40 / 255, 0.30), (ring, 205 / 255, 0.40)):
        a = np.clip(img * amax / max(1e-6, 1.0), 0, amax)[..., None]
        C[..., :3] = val * a + C[..., :3] * (1 - a); C[..., 3:4] = a + C[..., 3:4] * (1 - a)
    if shoe_on:
        # submerged part: tinted toward the dark water and half transparent; above the waterline: immaculate white
        s2 = s.copy(); rows_w = np.arange(h) + y_top
        under = np.clip((rows_w - wl_h) / (2.5 * S), 0, 1)[:, None]
        s2[..., :3] = s2[..., :3] * (1 - 0.55 * under[..., None]) + (70 / 255) * 0.55 * under[..., None]
        s2[..., 3] *= (1 - 0.6 * under)
        # a thin wet meniscus where the shoe meets the water (bright line, 1 px)
        over(C, s2, x_left, y_top)
    # straight alpha out
    A = C[..., 3:4]; RGB = np.where(A > 1e-6, C[..., :3] / np.maximum(A, 1e-6), 0)
    hi = np.dstack([RGB, A]).clip(0, 1)
    hi8 = (hi * 255 + 0.5).astype(np.uint8)
    Image.fromarray(hi8, "RGBA").save(f"{OUT}/layer_hi/shoe_hi_{k:03d}.png", optimize=False, compress_level=6)
    # wide: area-downsample premultiplied, then place in 800x540
    pm = np.dstack([hi[..., :3] * hi[..., 3:4], hi[..., 3:4]])
    lo = cv2.resize(pm, (Wh // S, Hh // S), interpolation=cv2.INTER_AREA)
    a = lo[..., 3:4]; rgb = np.where(a > 1e-6, lo[..., :3] / np.maximum(a, 1e-6), 0)
    wide = np.zeros((540, 800, 4), np.uint8)
    part = (np.dstack([rgb, a]).clip(0, 1) * 255 + 0.5).astype(np.uint8)       # world x -20..880, y 340..470
    wide[Y0W:Y1W, 0:800] = part[:, 20:820]
    Image.fromarray(wide, "RGBA").save(f"{OUT}/layer/shoe_{k:03d}.png", optimize=False, compress_level=6)
    fn = f"{OUT}/layer/shoe_{k:03d}.png"
    hashes.append(dict(k=k, png_sha256=hashlib.sha256(open(fn, "rb").read()).hexdigest(),
                       rgba_sha256=hashlib.sha256(wide.tobytes()).hexdigest(),
                       hi_rgba_sha256=hashlib.sha256(hi8.tobytes()).hexdigest()))
    recs.append(dict(k=k, t=round(t, 4), L_local=round(14.0 + t, 4), E_local=round(7.0 + t, 4),
                     shoe_visible=shoe_on, centre_layer=[round(st["x"], 2), round(st["y_wl"] - 0.28 * SHOE_W * SH.height / SH.width, 2)] if shoe_on else None,
                     waterline_layer=round(st["y_wl"], 2), pitch_deg=round(st["pitch"], 2)))
json.dump(dict(frames=recs, hashes=hashes), open(f"{OUT}/layer_frames.json", "w"), indent=0)
print("done", N)

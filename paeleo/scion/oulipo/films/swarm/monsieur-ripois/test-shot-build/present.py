"""PRESENT-TENSE layers: SCION #29 cut pieces of LoC 2017831564 articulated by FK at the neck pivots,
inpainted+burned plate, the handmade box placed on her lap, one unifying tone curve, the print's own grain."""
import numpy as np, cv2, json, math, sys
sys.path.insert(0, __file__.rsplit('/', 1)[0])
import box
SRC = "/home/user/bolas/paeleo/scion/oulipo/films/sources/monsieur-ripois/test-shot/"
g = cv2.imread(SRC + "plate-1440.png", 0).astype(np.float32) / 255
plate = cv2.imread(SRC + "plate-inpainted.png", 0).astype(np.float32) / 255
PCS = json.load(open(SRC + "pieces.json"))["pieces"]
masks = {n: cv2.imread(SRC + f"piece-{n}-mask.png", 0).astype(np.float32) / 255 for n in PCS}

# plate repair behind her head: wall and wainscot run horizontally, so each row of the vacated region
# is filled by mirroring the row to its left (Telea smears; the room's own rows don't)
hole = cv2.dilate((masks["her_head"] > 0.08).astype(np.uint8), np.ones((9, 9), np.uint8))
for y in range(hole.shape[0]):
    xs = np.nonzero(hole[y])[0]
    if len(xs) == 0: continue
    a, b = xs.min(), xs.max()
    span = b - a + 1
    src = plate[y, max(0, a - span):a][::-1] if a > 0 else plate[y, b + 1:b + 1 + span]
    if len(src) < span: src = np.pad(src, (0, span - len(src)), mode="reflect")
    plate[y, a:b + 1] = src[:span]
plate = plate * 0 + plate
# film grain of the print, sampled from the master itself: high-pass of a flat wall patch at native res
m = cv2.imread(SRC + "v0-master-crop.png", 0).astype(np.float32) / 255
patch = m[126:1000, 4662:5922]            # plain wall right of the painting, above the wainscot, clear of his head and its shadow
res = patch - cv2.GaussianBlur(patch, (0, 0), 6)
res = cv2.resize(res, (res.shape[1] // 2, res.shape[0] // 2), interpolation=cv2.INTER_AREA)
GRAIN_STD_SRC = float(res.std())
def grain_field(h, w, seed):
    r = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    ph, pw = res.shape
    for y in range(0, h, ph):
        for x in range(0, w, pw):
            oy, ox = r.integers(0, ph // 2), r.integers(0, pw // 2)
            t = np.roll(np.roll(res, oy, 0), ox, 1)
            out[y:y + ph, x:x + pw] = t[:min(ph, h - y), :min(pw, w - x)]
    return out
GRAIN = grain_field(540, 720, 3)

couple = cv2.imread(SRC + "matte-couple.png", 0).astype(np.float32) / 255
COUPLE_POLY = [(30,520),(150,470),(230,330),(330,80),(500,100),(600,330),(700,370),(800,250),(820,60),(950,10),(1060,60),(1060,300),(1180,420),(1270,560),(1330,750),(1340,880),(1380,1080),(840,1080),(780,840),(700,770),(400,700),(30,690)]
P = np.zeros_like(couple); cv2.fillPoly(P, [np.array(COUPLE_POLY, np.int32)], 1.0)
P = np.minimum(P, 1 - 0.0 * P)
fig = cv2.GaussianBlur(np.maximum(couple, cv2.erode(P, np.ones((41, 41), np.uint8))) * P, (0, 0), 3)
yy, xx = np.mgrid[0:1080, 0:1440].astype(np.float32)
# darkroom burn: background (wall, wainscot, sofa arm) held back; key pool on the faces (camera-right flash)
key = np.exp(-(((xx - 820) / 700) ** 2 + ((yy - 330) / 560) ** 2))
HEADS = cv2.GaussianBlur(cv2.dilate(((masks["her_head"] + masks["his_head"]) > 0.05).astype(np.float32), np.ones((61, 61), np.uint8)), (0, 0), 10)
KEYF = (0.50 + 0.55 * key)
BURN = (0.62 + 0.38 * fig * (1 - HEADS)) * KEYF
BURN_PIECE = (0.62 + 0.38 * cv2.GaussianBlur(couple, (0, 0), 3)) * KEYF        # burn of the plate only; the pieces carry their own exposure

def rot_piece(img, a, piv, deg):
    M = cv2.getRotationMatrix2D(piv, deg, 1.0)
    return (cv2.warpAffine(img, M, (1440, 1080), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT),
            cv2.warpAffine(a, M, (1440, 1080), flags=cv2.INTER_LINEAR))

BOX_CAM_2S = box.Cam(yaw=-22, pitch=40, dist=2.4, f=275, cx=1015, cy=872)
_box_cache = {}
def lap_box(lid):
    if lid not in _box_cache:
        _box_cache[lid] = box.render(BOX_CAM_2S, (1440, 1080), lid, (g * 255).astype(np.uint8), ss=2)
    return _box_cache[lid]

def twoshot(her_deg, his_deg, lid=100):
    """her_deg: + = head drops toward the box (clockwise); his_deg: + = leans toward her (counter-clockwise)"""
    c = plate.copy()
    C, A, S = lap_box(lid)
    c = c * (1 - 0.55 * S)                           # contact shadow on the skirt
    bgr = (C * 0.92 + grain_field(1080, 1440, 11)[:1080, :1440] * 0.0)
    c = c * (1 - A) + bgr * A
    layers = []
    for n, deg, sign in (("his_head", his_deg, 1), ("her_head", her_deg, -1)):
        piv = tuple(PCS[n]["pivot"])
        pi, pa = rot_piece(g, masks[n], piv, sign * deg)
        # card piece casts a faint contact shadow on the plate (offset away from the camera-right key)
        sh = cv2.GaussianBlur(pa, (0, 0), 5)
        sh = np.roll(np.roll(sh, 4, 0), -5, 1)
        c = c * (1 - 0.18 * sh * (1 - pa))
        _, pb = rot_piece(g, BURN_PIECE, piv, sign * deg)      # the piece carries its own burn-in (incl. any wall it took with it)
        layers.append((pi * pb, pa))
    c = c * BURN
    for pi, pa in layers:
        c = c * (1 - pa) + pi * pa
    return cv2.resize(c, (720, 540), interpolation=cv2.INTER_AREA)

# insert: her lap, the box close (≈60 % of picture width), skirt fabric from the same master as a shallow-focus plane
lap = m[3700 - 456:4900 - 456, 4300 - 391:5900 - 391] if False else m[3244:4444, 3909:5509]
lap = cv2.GaussianBlur(cv2.resize(lap, (720, 540), interpolation=cv2.INTER_AREA), (0, 0), 3.5)
BOX_CAM_IN = box.Cam(yaw=-24, pitch=52, dist=2.1, f=720, cx=372, cy=330)
def insert(lid=100):
    C, A, S = box.render(BOX_CAM_IN, (720, 540), lid, (g * 255).astype(np.uint8), ss=2)
    c = lap * (1 - 0.6 * S)
    yy2, xx2 = np.mgrid[0:540, 0:720].astype(np.float32)
    pool = np.exp(-(((xx2 - 390) / 330) ** 2 + ((yy2 - 300) / 260) ** 2))
    c = c * (0.30 + 0.55 * pool)
    gb = grain_field(540, 720, 5) * 1.0                 # the box carries the print's grain
    c = c * (1 - A) + (C * (0.55 + 0.45 * pool) * 0.95 + gb * 0.6) * A
    return c

def tone(x):
    """one unifying curve for all present shots (fixed constants, not per frame), print blacks, faint green-grey shadows"""
    x = np.clip(x, 0, 1.2)
    y = np.clip((x - 0.05) / 0.74, 0, 1) ** 1.7
    L = 34 + (252 - 34) * y + GRAIN * 255 * 1.0
    L = np.clip(L, 0, 255)
    sh = np.clip(1 - L / 140, 0, 1)
    rgb = np.stack([L - 3 * sh, L + 3 * sh, L + 0.5 * sh], -1)
    return np.clip(rgb, 0, 255).astype(np.uint8)

def slot_screen_insert():
    return box.slot_screen(BOX_CAM_IN)

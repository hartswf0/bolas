"""SCION 40 · shared definitions: paths, the score, stage geometry, paper, fiducials, affine helpers.

Coordinate systems (all typed, all in pixels unless stated):
  stage  : 1280x720, the film's picture plane = the layout sheet on the table, y down.
  plate  : 1280x720, the overhead camera's image of the table (homography H_stage_to_plate).
  card   : each paper piece's own image; origin at its anchor (cx, cy) in the card PNG.
  score  : metres along the porch (threshold 0, sill 0.56, steps 4.9), seconds at 24 fps.
A piece pose is (X, Y, theta) in stage px / radians: card anchor -> (X, Y), card rotated by theta (counter-clockwise on screen).
"""
import json, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
F = os.path.dirname(HERE)                                  # the swarm folder
R = os.path.dirname(os.path.dirname(os.path.dirname(F)))  # repo root
CACHE = os.path.join(HERE, 'cache')
DATA = os.path.join(F, 'data')
SCORE = json.load(open(os.path.join(R, 'paeleo/handmade/score/threshold-score.json')))
FR = SCORE['frames']
N = len(FR)
FPS = 24
W, H = 1280, 720
HAND_SRC = '/home/user/hartswf0/secondhand-motion/shots/hand-sam'
FONTS = os.path.join(R, 'tools/paeleo/fonts')

# ---- stage geometry (the layout sheet) -------------------------------------------------------
GROUND = 600          # porch floor / room floor line, stage px
PX_PER_M = 200.0
SILL_X = 330.0        # the threshold (middle of the wall section) = score x 0.56 (the sill)
WALL = (316, 344)     # wall section in stage px
LINTEL = 196          # top of the door opening
ROOF = 120


def x_stage(x_m):
    """score metres -> stage px. The sill (0.56 m) sits on the wall line; outside is to the right."""
    return SILL_X + (x_m - SCORE['places']['sill']) * PX_PER_M


def x_score_from_stage(X):
    return SCORE['places']['sill'] + (X - SILL_X) / PX_PER_M


def os_makedirs(*ps):
    for p in ps:
        os.makedirs(p, exist_ok=True)


# ---- paper ---------------------------------------------------------------------------------------
def value_noise(h, w, scale, seed):
    rng = np.random.default_rng(seed)
    gh, gw = h // scale + 2, w // scale + 2
    g = rng.random((gh, gw)).astype(np.float32)
    im = Image.fromarray((g * 255).astype(np.uint8)).resize((gw * scale, gh * scale), Image.BICUBIC)
    return np.asarray(im, np.float32)[:h, :w] / 255.0


def grain(h, w, seed=1):
    """paper grain in [-1, 1]: fibres (stretched noise) plus fine speckle"""
    a = value_noise(h, w, 24, seed) * .45 + value_noise(h, w, 6, seed + 1) * .35 + value_noise(h, w, 2, seed + 2) * .2
    rng = np.random.default_rng(seed + 9)
    fib = np.asarray(Image.fromarray((rng.random((h // 2 + 1, w // 12 + 1)) * 255).astype(np.uint8)).resize((w, h), Image.BILINEAR), np.float32)[:h, :w] / 255.
    return (a * .7 + fib * .3 - .5) * 2.0


def jitter_poly(pts, amt, seed, step=6.0):
    """resample a closed polygon and wobble it: a scissor-cut edge"""
    pts = np.asarray(pts, float)
    out = []
    rng = np.random.default_rng(seed)
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        L = np.hypot(*(b - a))
        n = max(1, int(L / step))
        for k in range(n):
            out.append(a + (b - a) * k / n)
    out = np.array(out)
    if len(out) < 3:
        return pts
    nrm = np.roll(out, -1, 0) - np.roll(out, 1, 0)
    nrm = np.stack([nrm[:, 1], -nrm[:, 0]], 1)
    nrm /= np.maximum(np.hypot(nrm[:, 0], nrm[:, 1]), 1e-6)[:, None]
    # low-frequency wobble so the cut looks hand-made, not noisy
    k = len(out)
    ph = rng.random(3) * 6.283
    s = np.arange(k) / k * 6.283
    wob = (np.sin(s * 3 + ph[0]) * .5 + np.sin(s * 7 + ph[1]) * .3 + np.sin(s * 13 + ph[2]) * .2) * amt
    wob += rng.normal(0, amt * .25, k)
    return out + nrm * wob[:, None]


def hull(P):
    """2D convex hull (monotone chain)"""
    P = sorted(set(map(tuple, np.round(np.asarray(P), 2))))
    if len(P) < 3:
        return np.array(P)

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in P:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(P):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return np.array(lo[:-1] + up[:-1])


# ---- fiducials -----------------------------------------------------------------------------------
# a 6x6-cell square: black border ring, 4x4 data. Data = 8-bit id and its complement, laid out so that
# the top-left data cell is always 1 (black) and the bottom-right always 0 (white): that fixes orientation.
CELL = 5
MARK = 6 * CELL


def fid_bits(ident):
    b = [(ident >> k) & 1 for k in range(7)]           # 7 id bits (ids 0..127)
    p = sum(b) & 1
    data = [1] + b + [1 - x for x in b[:6]] + [p, 0]   # 16 cells
    return np.array(data, np.uint8).reshape(4, 4)


def fid_decode(cells):
    """cells: 4x4 array of 0/1 (1 = dark). Returns id or None."""
    c = np.asarray(cells).reshape(-1)
    if c[0] != 1 or c[15] != 0:
        return None
    b = list(c[1:8])
    if list(c[8:14]) != [1 - x for x in b[:6]] or c[14] != (sum(b) & 1):
        return None
    return int(sum(int(x) << k for k, x in enumerate(b)))


def fid_image(ident, cell=CELL):
    g = np.zeros((6, 6), np.uint8)
    g[1:5, 1:5] = fid_bits(ident)
    g[0, :] = g[5, :] = g[:, 0] = g[:, 5] = 1
    a = np.where(g == 1, 22, 246).astype(np.uint8)
    return np.kron(a, np.ones((cell, cell), np.uint8))


def fid_cell_centres(cell=CELL):
    """card-local offsets of the 16 data-cell centres relative to the marker centre"""
    out = []
    for r in range(4):
        for c in range(4):
            out.append(((c + 1.5) * cell - 3 * cell, (r + 1.5) * cell - 3 * cell))
    return np.array(out)


# ---- affine placement ----------------------------------------------------------------------------
def place(card_img, anchor, X, Y, th, scale=1.0):
    """card RGBA (PIL) with anchor (ax, ay) -> a full-frame RGBA layer at pose (X, Y, th)."""
    ax, ay = anchor
    c, s = math.cos(th), math.sin(th)
    # forward: screen = R(-th on y-down) ... use: x' = X + s*( c*(u-ax) + s*(v-ay) ), y' = Y + s*(-s*(u-ax) + c*(v-ay))
    # inverse for PIL: u = ax + ( c*(x-X) - s*(y-Y) )/scale ; v = ay + ( s*(x-X) + c*(y-Y) )/scale
    k = 1.0 / scale
    coeffs = (c * k, -s * k, ax - k * (c * X - s * Y), s * k, c * k, ay - k * (s * X + c * Y))
    return card_img.transform((W, H), Image.AFFINE, coeffs, resample=Image.BICUBIC)


def to_stage(pt_card, anchor, X, Y, th, scale=1.0):
    u, v = pt_card[0] - anchor[0], pt_card[1] - anchor[1]
    c, s = math.cos(th), math.sin(th)
    return (X + scale * (c * u + s * v), Y + scale * (-s * u + c * v))


def homography(src, dst):
    A = []
    for (x, y), (u, v) in zip(src, dst):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y, -u])
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y, -v])
    _, _, Vt = np.linalg.svd(np.array(A, float))
    Hm = Vt[-1].reshape(3, 3)
    return Hm / Hm[2, 2]


def apply_h(Hm, pts):
    p = np.c_[np.asarray(pts, float), np.ones(len(pts))] @ Hm.T
    return p[:, :2] / p[:, 2:3]


def font(name, size):
    from PIL import ImageFont
    files = {'display': 'f8.woff2', 'mono': 'f14.woff2', 'serif': 'f27.woff2'}
    f = ImageFont.truetype(os.path.join(FONTS, files[name]), size)
    try:
        if name == 'display':
            f.set_variation_by_axes([800])
    except Exception:
        pass
    return f


def smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)

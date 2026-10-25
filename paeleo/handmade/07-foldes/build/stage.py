"""SCION 07 · the place, drawn: a house front with a doorway and a sill, a porch along it, a railing and the dusk beyond.
Everything is a contour drawn here (coordinates in screen px at 1x) with a flat wash; nothing is a photograph.
Mapping (fixed camera): screen_x = X0 + S * x_metres, the threshold x=0 at the door's centre, porch steps at x=4.9."""
import math, random
import numpy as np
from PIL import Image, ImageFilter
from draw import Canvas, SS, cr, INK

W, H = 1280, 720
X0, S = 330.0, 190.0
YWALL = 560.0      # where the facade meets the boards
YDOG = 578.0       # the dog's and the person's floor line (a little in front of the wall)
DOOR = (X0 - 0.46 * S, X0 + 0.46 * S, YWALL - 2.05 * S, YWALL)   # x0 x1 y0 y1 of the opening
CORNER = X0 + 1.6 * S
STEPS = X0 + 4.9 * S
SILL = (DOOR[0] - 8, DOOR[1] + 8, YWALL - 4, YWALL + 11)

PAPER = (233, 227, 213)


def sx(x):
    return X0 + S * x


def paper():
    rng = np.random.default_rng(7)
    a = np.ones((H * SS, W * SS, 3), np.float32) * np.array(PAPER, np.float32)
    g = rng.normal(0, 1, (H * SS // 6, W * SS // 6)).astype(np.float32)
    g = np.array(Image.fromarray(((g * 18) + 128).clip(0, 255).astype(np.uint8)).resize((W * SS, H * SS), Image.BILINEAR), np.float32) - 128
    a += g[..., None] * 0.18
    return a


def gradient_fill(a, box, top, bot):
    x0, y0, x1, y1 = [int(v * SS) for v in box]
    t = np.linspace(0, 1, y1 - y0)[:, None, None]
    a[y0:y1, x0:x1] = np.array(top, np.float32) * (1 - t) + np.array(bot, np.float32) * t


def dens(pts, step=6.0):
    """a ruled line with its corners kept (no spline), densified so the pen pressure can vary along it"""
    out = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / step))
        out += [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(1, n + 1)]
    return out


def background(late=0.0, lit=0.0):
    """late: 0 early dusk .. 1 evening. lit: 0 interior dark .. 1 lamp on."""
    a = paper()
    skytop = np.array([128, 136, 160]) * (1 - late) + np.array([70, 78, 104]) * late
    skybot = np.array([222, 190, 160]) * (1 - late) + np.array([150, 126, 128]) * late
    gradient_fill(a, (CORNER, 96, W, 500), skytop, skybot)
    gradient_fill(a, (CORNER, 500, W, YWALL), skybot * 0.92, skybot * 0.8)
    fac = np.array([200, 192, 180]) * (1 - 0.35 * late)
    a[int(96 * SS):int(YWALL * SS), 0:int(CORNER * SS)] = fac
    # interior through the opening
    dx0, dx1, dy0, dy1 = DOOR
    dark, warm = np.array([62, 56, 58]), np.array([250, 222, 160])
    inner = dark * (1 - lit) + warm * lit
    gradient_fill(a, (dx0, dy0, dx1, dy1 - 46), inner * 0.92, inner)
    gradient_fill(a, (dx0, dy1 - 46, dx1, dy1), inner * 0.82, inner * 0.7 + 20 * lit)
    # boards and below
    gradient_fill(a, (0, YWALL, W, 640), np.array([176, 164, 148]) * (1 - .3 * late), np.array([158, 146, 132]) * (1 - .3 * late))
    a[int(640 * SS):int(662 * SS), :] = np.array([112, 100, 92]) * (1 - .3 * late)
    gradient_fill(a, (0, 662, W, H), np.array([84, 86, 80]) * (1 - .3 * late), np.array([60, 62, 60]) * (1 - .3 * late))
    # roof underside / beam
    gradient_fill(a, (0, 0, W, 80), np.array([96, 90, 92]) * (1 - .3 * late), np.array([120, 112, 112]) * (1 - .3 * late))
    a[int(80 * SS):int(96 * SS), :] = np.array([150, 140, 130]) * (1 - .3 * late)
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    cv = Canvas(im)
    ink = INK
    L = lambda pts, w=2.0, al=1.0, seed=0: cv.line(dens(pts), w, ink, al, seed, taper=(0.6, 0.6))
    # dusk: horizon, a far tree line drawn as one wandering pen line, the moon
    L([(CORNER, 470), (W, 466)], 1.4, 0.6)
    rnd = random.Random(3)
    pts, x = [], CORNER
    while x < W:
        pts.append((x, 470 - 14 - 18 * abs(math.sin(x * 0.011)) - rnd.random() * 9)); x += 12
    pts.append((W, pts[-1][1]))
    trees = cr(pts, False, 3)
    cv.fill(trees + [(W, 472), (CORNER, 472)], tuple(int(c) for c in (np.array([92, 92, 108]) * (1 - late) + np.array([52, 54, 70]) * late)), 1.0)
    cv.line(trees, 1.3, ink, 0.6, 2)
    mx, my = 1010, 190
    moon = [(mx + 22 * math.cos(t), my + 22 * math.sin(t)) for t in np.linspace(-1.9, 1.9, 16)]
    moon += [(mx + 9 + 17 * math.cos(t), my + 19 * math.sin(t)) for t in np.linspace(1.75, -1.75, 16)]
    cv.fill(moon, (238, 232, 214), 1.0); cv.line(moon + [moon[0]], 1.6, ink, 0.9)
    # roof beam, posts, railing behind the dog
    L([(0, 80), (W, 80)], 2.2); L([(0, 96), (W, 96)], 2.2)
    for px in (sx(3.05), STEPS - 6):
        cv.fill([(px - 9, 96), (px + 9, 96), (px + 9, YWALL), (px - 9, YWALL)], (176, 166, 152), 1.0)
        L([(px - 9, 96), (px - 9, YWALL)], 2.0); L([(px + 9, 96), (px + 9, YWALL)], 2.0)
    rt, rb = YDOG - 0.92 * S, YWALL - 14
    L([(CORNER, rt), (W, rt)], 2.0); L([(CORNER, rt + 9), (W, rt + 9)], 1.4, 0.8)
    L([(CORNER, rb), (W, rb)], 1.6, 0.8)
    x = CORNER + 22
    while x < W:
        L([(x, rt + 9), (x, rb)], 1.1, 0.45); x += 26
    # facade: corner, siding lines, window
    L([(CORNER, 96), (CORNER, YWALL)], 2.4)
    y = 120
    while y < YWALL - 6:
        L([(0, y), (DOOR[0] - 16, y)], 1.0, 0.28); L([(DOOR[1] + 16, y), (CORNER, y)], 1.0, 0.28); y += 24
    wx0, wx1, wy0, wy1 = sx(0.78), sx(1.38), 236, 392
    glass = (88, 86, 96) if lit < 0.5 else (88 + int(150 * (lit - 0.5) * 2 * 0.9), 86 + int(120 * (lit - .5) * 2 * .9), 96 + int(40 * (lit - .5) * 2))
    cv.fill([(wx0, wy0), (wx1, wy0), (wx1, wy1), (wx0, wy1)], glass, 1.0)
    for pts in ([(wx0, wy0), (wx1, wy0), (wx1, wy1), (wx0, wy1), (wx0, wy0)], [((wx0 + wx1) / 2, wy0), ((wx0 + wx1) / 2, wy1)],
                [(wx0, (wy0 + wy1) / 2), (wx1, (wy0 + wy1) / 2)], [(wx0 - 8, wy1 + 6), (wx1 + 8, wy1 + 6)]):
        L(pts, 2.0)
    # door frame (trim), lintel; interior: back wall line, a lamp on a table, a picture
    dx0, dx1, dy0, dy1 = DOOR
    for pts in ([(dx0 - 14, dy1), (dx0 - 14, dy0 - 14), (dx1 + 14, dy0 - 14), (dx1 + 14, dy1)],
                [(dx0, dy1), (dx0, dy0), (dx1, dy0), (dx1, dy1)], [(dx0 - 20, dy0 - 22), (dx1 + 20, dy0 - 22)]):
        L(pts, 2.3)
    L([(dx0, dy1 - 46), (dx1, dy1 - 46)], 1.3, 0.5)
    tx = dx0 + 40
    L([(tx - 22, dy1 - 46 - 70), (tx + 22, dy1 - 46 - 70)], 1.6, 0.7)
    L([(tx - 18, dy1 - 46 - 70), (tx - 18, dy1 - 46)], 1.4, 0.7); L([(tx + 18, dy1 - 46 - 70), (tx + 18, dy1 - 46)], 1.4, 0.7)
    lamp = [(tx - 16, dy1 - 116 - 4), (tx - 8, dy1 - 116 - 34), (tx + 8, dy1 - 116 - 34), (tx + 16, dy1 - 116 - 4)]
    cv.fill(lamp, (255, 236, 186) if lit > 0.3 else (120, 110, 100), 1.0); L(lamp + [lamp[0]], 1.6, 0.8)
    L([(tx, dy1 - 116 - 4), (tx, dy1 - 116)], 1.6, 0.8)
    pfx = dx1 - 70
    L([(pfx, dy0 + 70), (pfx + 44, dy0 + 70), (pfx + 44, dy0 + 120), (pfx, dy0 + 120), (pfx, dy0 + 70)], 1.4, 0.55)
    # boards: back edge, joints converging toward a point above the door, front edge
    L([(0, YWALL), (W, YWALL)], 2.2)
    vpx = X0
    for bx in range(-200, W + 400, 64):
        x1b = bx + (bx - vpx) * 0.16
        L([(bx, YWALL + 1), (x1b, 640)], 1.0, 0.3)
    L([(0, 640), (STEPS, 640)], 2.2); L([(0, 662), (STEPS, 662)], 1.6, 0.8)
    # steps going down off the porch
    for i, (y0s, y1s) in enumerate([(640, 662), (662, 690), (690, 720)]):
        x = STEPS + 4 + i * 8
        L([(x, y0s), (x, y1s), (W, y1s)], 1.8, 0.9)
    # the sill: a raised board across the bottom of the opening
    s0, s1, sy0, sy1 = SILL
    cv.fill([(s0, sy0), (s1, sy0), (s1, sy1), (s0, sy1)], (186, 170, 150), 1.0)
    L([(s0, sy0), (s1, sy0)], 2.2); L([(s0, sy1), (s1, sy1)], 1.8); L([(s0, sy0), (s0, sy1)], 1.6); L([(s1, sy0), (s1, sy1)], 1.6)
    return im


def door_leaf(theta):
    """the leaf hinged at the left jamb swinging inward: a parallelogram whose free edge narrows and recedes."""
    dx0, dx1, dy0, dy1 = DOOR
    w = (dx1 - dx0) * math.cos(theta)
    sh = math.sin(theta)
    return [(dx0, dy0), (dx0 + w, dy0 + 14 * sh), (dx0 + w, dy1 - 7 * sh), (dx0, dy1)]


POOL = [(DOOR[0], YWALL + 2), (DOOR[1], YWALL + 2), (DOOR[1] + 380, 640), (DOOR[0] - 70, 640)]


def light_field(lit):
    """how much door light falls on a screen point (0..1): the pool on the boards and the opening itself."""
    def f(x, y):
        if lit <= 0:
            return 0.0
        if y < DOOR[2] or y > 640:
            return 0.0
        if y <= YWALL:
            return lit * 0.55 if DOOR[0] <= x <= DOOR[1] + 40 else 0.0
        u = (y - YWALL) / (640 - YWALL)
        xl = DOOR[0] + (POOL[3][0] - DOOR[0]) * u; xr = DOOR[1] + (POOL[2][0] - DOOR[1]) * u
        if xl <= x <= xr:
            return lit * 0.5
        d = min(abs(x - xl), abs(x - xr))
        return lit * 0.5 * max(0.0, 1 - d / 120)
    return f

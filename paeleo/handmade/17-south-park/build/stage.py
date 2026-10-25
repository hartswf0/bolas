"""SCION 17 // stage template v1: THE PORCH (a reusable flat set) and its camera framings.

World frame: metres, y up. x runs along the porch: the threshold is x = 0, the door opening spans x in [-0.46, 0.46]
(drawn frontally, the flat-stage convention: the set faces the camera, the figures play along one line in front of the
wall), the sill is at x = 0.56, the porch steps at x = 4.9. The figures stand on y = 0, the line of the wall's foot.
The door is three drawings (AJAR, WIDE, OPEN); its light is a function of which drawing is up, nothing else.
"""
import json, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from kit import Piece, ellipse, rrect, capsule, handcut, poly, seed_of

VERSION = 'porch-v1'
HERE = os.path.dirname(os.path.abspath(__file__))
SS = 2                                    # supersampling factor for drawing
W, H = 1280, 720

CAMERAS = {                               # px per metre, screen x of world x=0, screen y of world y=0 (at 1x)
    'WIDE': dict(s=188.0, x0=335.0, fy=562.0),
    'CLOSE': dict(s=330.0, x0=620.0, fy=600.0),
}

DOOR_STATES = {'AJAR': dict(theta=56.0, light=0.30), 'WIDE': dict(theta=74.0, light=0.72), 'OPEN': dict(theta=87.0, light=1.0)}


def cam_matrix(name, ss=SS):
    c = CAMERAS[name]
    return np.array([[c['s'] * ss, 0, c['x0'] * ss], [0, -c['s'] * ss, c['fy'] * ss], [0, 0, 1.0]])


def world_to_px(name, x, y=0.0):
    c = CAMERAS[name]
    return c['x0'] + c['s'] * x, c['fy'] - c['s'] * y


def px_to_world_x(name, px):
    c = CAMERAS[name]
    return (px - c['x0']) / c['s']


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def wavy_band(x0, x1, ytop, ybot, name, amp=0.03, step=0.25):
    xs = np.arange(x0, x1 + step, step)
    g = np.random.default_rng(seed_of(name))
    bot = [(x, ybot + g.uniform(-amp, amp)) for x in xs]
    return np.array([(x0, ytop), (x1, ytop)] + bot[::-1])


def qd_drawings():
    rows = [json.loads(l) for l in open(os.path.join(HERE, '..', 'assets', 'quickdraw_used.ndjson'))]
    return rows


def qd_strokes(d, x, y, size, flip_y=True):
    """Quick, Draw! strokes (0..255 box, y down) -> world polylines: bottom-left at (x,y), height `size`"""
    out = []
    for s in d['drawing']:
        pts = np.array([(x + px / 255.0 * size, y + (255 - py) / 255.0 * size) for px, py in zip(s[0], s[1])])
        out.append(pts)
    return out


def static_pieces(cam):
    """Everything that never changes: sky, moon, yard, house wall, window, porch, steps. Returns [(Piece, kind)]"""
    P = []
    sky = [(34, 36, 72), (46, 46, 90), (70, 58, 108), (112, 76, 118), (168, 98, 116), (214, 132, 106)]
    tops = [4.2, 3.0, 2.3, 1.7, 1.2, 0.75]
    for k, (c, t) in enumerate(zip(sky, tops)):
        bot = tops[k + 1] if k + 1 < len(tops) else -0.7
        P.append(Piece(wavy_band(-4, 8, t + 0.05, bot - 0.02, 'sky%d' % k, 0.04), c, 0, 'sky', outline=False))
    qd = {(d['word'], d['key_id']): d for d in qd_drawings()}
    moon = [d for d in qd.values() if d['word'] == 'moon'][0]
    for s in qd_strokes(moon, 3.42, 1.86, 0.5):
        P.append(Piece(handcut(s, 'moon', 0.004), (238, 226, 170), 1, 'moon', outline=False))
    # stars: tiny cut dots
    g = np.random.default_rng(17)
    for k in range(26):
        sx, sy = g.uniform(-2.2, 6), g.uniform(2.2, 3.6)
        P.append(Piece(ellipse(sx, sy, 0.012, 0.012, n=6), (230, 226, 200), 1, 'star', outline=False))
    # far yard behind the house corner
    P.append(Piece(wavy_band(3.0, 8, 0.12, -0.7, 'yard', 0.02), (50, 60, 76), 2, 'yard', outline=False))
    trees = [d for d in qd.values() if d['word'] == 'tree']
    for d, (tx, ty, sz, col) in zip(trees, [(4.02, 0.02, 2.15, (36, 40, 66)), (5.25, 0.02, 1.9, (42, 46, 74))]):
        strokes = qd_strokes(d, tx, ty, sz)
        big = max(strokes, key=len)
        P.append(Piece(handcut(big, 'tree' + d['key_id'], 0.01), col, 3, 'tree', outline=False))
        for s in strokes:
            if s is big: continue
            for a, b in zip(s[:-1], s[1:]):
                P.append(Piece(capsule(a, b, 0.07), col, 3, 'tree', outline=False))
    fences = [d for d in qd.values() if d['word'] == 'fence']
    fx = 3.1
    while fx < 7.0:
        d = fences[int(fx * 7) % len(fences)]
        for s in qd_strokes(d, fx, 0.06, 0.62):
            for a, b in zip(s[:-1], s[1:]):
                P.append(Piece(capsule(a, b, 0.035), (88, 84, 116), 4, 'fence', outline=False))
        fx += 0.6
    # house wall with clapboards
    P.append(Piece([(-4, 0), (3.22, 0), (3.22, 4.5), (-4, 4.5)], (88, 104, 140), 5, 'wall', outline=False))
    y = 0.16
    while y < 4.4:
        P.append(Piece([(-4, y), (3.22, y), (3.22, y + 0.022), (-4, y + 0.022)], (72, 86, 120), 6, 'clap', outline=False))
        y += 0.19
    P.append(Piece(rrect(3.12, 0, 3.27, 4.5, 0.01), (150, 152, 176), 7, 'corner'))
    # window right of the door (dark, unlit room)
    P.append(Piece(rrect(1.22, 0.92, 2.18, 2.04, 0.02), (170, 170, 188), 7, 'wtrim'))
    P.append(Piece([(1.3, 1.0), (2.1, 1.0), (2.1, 1.96), (1.3, 1.96)], (40, 52, 88), 8, 'glass', outline=False))
    P.append(Piece([(1.42, 1.0), (1.62, 1.0), (1.98, 1.96), (1.78, 1.96)], (58, 72, 110), 8.5, 'glint', outline=False))
    P.append(Piece([(1.68, 1.0), (1.72, 1.0), (1.72, 1.96), (1.68, 1.96)], (170, 170, 188), 9, 'mull', outline=False))
    P.append(Piece([(1.3, 1.46), (2.1, 1.46), (2.1, 1.5), (1.3, 1.5)], (170, 170, 188), 9, 'mull', outline=False))
    P.append(Piece(rrect(1.16, 0.86, 2.24, 0.94, 0.01), (170, 170, 188), 9, 'sill'))
    # a second window far left (behind where she sits), dark
    P.append(Piece(rrect(-2.62, 0.92, -1.72, 2.04, 0.02), (170, 170, 188), 7, 'wtrim'))
    P.append(Piece([(-2.54, 1.0), (-1.8, 1.0), (-1.8, 1.96), (-2.54, 1.96)], (40, 52, 88), 8, 'glass', outline=False))
    P.append(Piece([(-2.19, 1.0), (-2.15, 1.0), (-2.15, 1.96), (-2.19, 1.96)], (170, 170, 188), 9, 'mull', outline=False))
    # porch roof fascia and post
    P.append(Piece([(-4, 2.5), (4.95, 2.5), (4.95, 2.76), (-4, 2.76)], (46, 42, 66), 10, 'fascia', outline=False))
    P.append(Piece([(-4, 2.76), (4.95, 2.76), (4.95, 4.6), (-4, 4.6)], (36, 34, 56), 10, 'roof', outline=False))
    P.append(Piece(rrect(4.64, 0, 4.78, 2.52, 0.01), (150, 150, 172), 11, 'post'))
    P.append(Piece(rrect(4.6, 2.4, 4.82, 2.5, 0.01), (150, 150, 172), 11, 'postcap'))
    # porch floor strip (in front of the figures' line), fascia, lattice skirt, steps, grass
    P.append(Piece([(-4, 0), (4.86, 0), (4.86, -0.26), (-4, -0.26)], (112, 94, 96), 30, 'floor', outline=False))
    for yy in (-0.07, -0.15, -0.21):
        P.append(Piece([(-4, yy), (4.86, yy), (4.86, yy - 0.012), (-4, yy - 0.012)], (92, 76, 80), 31, 'plank', outline=False))
    P.append(Piece([(-4, -0.26), (4.9, -0.26), (4.9, -0.34), (-4, -0.34)], (86, 70, 76), 31, 'edge', outline=False))
    P.append(Piece([(-4, -0.34), (4.86, -0.34), (4.86, -0.66), (-4, -0.66)], (38, 32, 46), 31, 'skirt', outline=False))
    lx = -4.0
    while lx < 4.86:
        for a, b in (((lx, -0.34), (lx + 0.3, -0.66)), ((lx + 0.3, -0.34), (lx, -0.66))):
            P.append(Piece(capsule(a, b, 0.025), (66, 56, 74), 32, 'lattice', outline=False))
        lx += 0.3
    for k in range(3):
        x0 = 4.86 + 0.24 * k; y0 = -0.22 * k
        P.append(Piece([(x0, y0 - 0.02), (6.5, y0 - 0.02), (6.5, y0 - 0.24), (x0, y0 - 0.24)], (100, 84, 88), 33 + k, 'step'))
    P.append(Piece(wavy_band(-4, 8, -0.66, -2.0, 'grass', 0.0), (40, 52, 58), 30.5, 'grass', outline=False))
    return P


def door_pieces(state, light):
    """Interior (seen through the opening), the door leaf at its drawn angle, casing and sill."""
    P = []
    th = math.radians(DOOR_STATES[state]['theta'])
    L = lambda dim, lit: mix(dim, lit, light)
    P.append(Piece([(-0.46, 0), (0.46, 0), (0.46, 2.05), (-0.46, 2.05)], L((70, 56, 56), (226, 176, 104)), 12, 'hall', outline=False))
    P.append(Piece([(-0.27, 0.36), (0.27, 0.36), (0.27, 1.72), (-0.27, 1.72)], L((86, 68, 62), (246, 204, 128)), 12.2, 'backwall', outline=False))
    P.append(Piece([(-0.46, 0), (0.46, 0), (0.27, 0.36), (-0.27, 0.36)], L((56, 42, 44), (190, 120, 74)), 12.3, 'hallfloor', outline=False))
    P.append(Piece([(-0.1, 0.0), (0.1, 0.0), (0.06, 0.36), (-0.06, 0.36)], L((70, 30, 36), (178, 64, 60)), 12.4, 'runner', outline=False))
    P.append(Piece(rrect(-0.11, 1.02, 0.11, 1.32, 0.01), L((52, 40, 36), (120, 80, 52)), 12.5, 'frame'))
    P.append(Piece([(-0.08, 1.05), (0.08, 1.05), (0.08, 1.29), (-0.08, 1.29)], L((60, 70, 80), (130, 170, 160)), 12.6, 'picture', outline=False))
    P.append(Piece(ellipse(0.0, 1.62, 0.045, 0.055, n=10), L((110, 100, 80), (255, 246, 206)), 12.7, 'bulb'))
    P.append(Piece(capsule((0, 1.67), (0, 1.74), 0.012), (40, 34, 40), 12.7, 'cord', outline=False))
    # the door leaf, hinged on the left jamb, swung inward (away from us): a quad that narrows as it opens
    xf = -0.46 + 0.92 * math.cos(th); shade = 0.62 + 0.38 * math.cos(th)
    col = tuple(int(c * shade) for c in (150, 62, 64))
    leaf = [(-0.46, 0.0), (xf, 0.04 * math.sin(th)), (xf, 2.05 - 0.07 * math.sin(th)), (-0.46, 2.05)]
    P.append(Piece(leaf, col, 13, 'leaf'))
    def onleaf(u, v):
        x = -0.46 + (xf + 0.46) * u
        yb = 0.04 * math.sin(th) * u; yt = 2.05 - 0.07 * math.sin(th) * u
        return (x, yb + (yt - yb) * v)
    if xf + 0.46 > 0.12:
        for v0, v1 in ((0.08, 0.44), (0.54, 0.92)):
            P.append(Piece([onleaf(0.18, v0), onleaf(0.82, v0), onleaf(0.82, v1), onleaf(0.18, v1)], tuple(int(c * 0.82) for c in col), 13.1, 'inset'))
        kx, ky = onleaf(0.88, 0.47)
        P.append(Piece(ellipse(kx, ky, 0.022 * max(0.3, math.cos(th)) + 0.008, 0.028, n=8), (226, 190, 90), 13.2, 'knob'))
    # casing and sill (in front of the hall, behind the figures)
    cas = (170, 164, 160)
    P.append(Piece(rrect(-0.6, 0, -0.46, 2.2, 0.01), cas, 14, 'jamb'))
    P.append(Piece(rrect(0.46, 0, 0.6, 2.2, 0.01), cas, 14, 'jamb'))
    P.append(Piece(rrect(-0.66, 2.05, 0.66, 2.24, 0.01), cas, 14.1, 'head'))
    P.append(Piece(rrect(-0.58, -0.035, 0.64, 0.035, 0.008), (150, 118, 92), 14.2, 'sill'))
    return P


def light_mask(cam, light):
    """Soft mask (1x, float 0..1) of where the door light falls: the opening and its spill on the porch floor."""
    m = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(m)
    c = CAMERAS[cam]
    f = lambda x, y: (c['x0'] + c['s'] * x, c['fy'] - c['s'] * y)
    d.polygon([f(-0.46, 0), f(0.46, 0), f(1.05, -0.27), f(-1.05, -0.27)], fill=int(255 * light))
    d.polygon([f(-0.46, 0), f(0.46, 0), f(0.46, 2.05), f(-0.46, 2.05)], fill=int(200 * light))
    m = m.filter(ImageFilter.GaussianBlur(6 * c['s'] / 170.0))
    return np.asarray(m, np.float32) / 255.0


def paper_grain(seed=17):
    g = np.random.default_rng(seed)
    lo = Image.fromarray((g.random((H // 8, W // 8)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)
    hi = g.random((H, W)).astype(np.float32)
    a = np.asarray(lo, np.float32) / 255.0
    return (1.0 + 0.035 * (a - 0.5) + 0.03 * (hi - 0.5))[..., None]

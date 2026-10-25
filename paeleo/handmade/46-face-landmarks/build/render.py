"""SCION 46 renderer: draws each scene frame from the registration (plates placed only by their fits) and the world.
Usage: python3 render.py [start end] [--stride k] [--out dir]  -> JPEG frames build/cache/frames/s%04d.jpg"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
from geom import Camera, CACHE, W, H, FPS, mirror_key, fit_affine, apply, smoothstep, HEAD
from plates import TORSO, HEADS, EAR, BONES, BONE_W, EYE, PAL, catmull
import voice

SS = 2
WW, HH = W * SS, H * SS
UP = np.array([0.0, 1.0, 0.0])
LAMP = np.array([-1.7, 2.45, -0.35])
FACE_DIR = os.path.join(CACHE, 'face')
DOOR_TEX = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'sources', 'door', 'f031.jpg')
# door panel in the source frame (annotated by hand: hinge edge at left, knob at right; the top runs out of frame)
DOOR_SRC_QUAD = [(117, 0), (238, 0), (222, 272), (119, 247)]


def fwd_of(th):
    r = math.radians(th); return np.array([math.cos(r), 0.0, math.sin(r)])


def right_of(th):
    r = math.radians(th); return np.array([-math.sin(r), 0.0, math.cos(r)])


def lerp(a, b, s): return a + (b - a) * s


# ------------------------------------------------------------------ light
def door_open_frac(f):
    return smoothstep(9.0, 96.0, f['door'])


def light_at(P, f, inside_bias=0.0):
    """RGB multiplier at world point P: dusk ambient + warm light from the house (through the door when outside)"""
    t = f['t']
    amb = np.array([0.60, 0.64, 0.84]) * (1 - 0.18 * t / 32.0)
    warm = np.array([1.05, 0.78, 0.50])
    X, Y, Z = P
    if X < -0.1:
        d = np.linalg.norm(P - LAMP)
        return amb * 0.55 + warm * (0.95 / (1 + (d / 2.4) ** 2)) + 0.12 * warm
    o = 0.25 + 0.75 * door_open_frac(f)
    # inside the light wedge from the doorway
    half = 0.46 + 0.55 * X
    edge = 1 - smoothstep(half - 0.25, half + 0.35, abs(Z + 0.05))
    dist = math.hypot(X, Z)
    I = o * edge * (1.0 / (1 + (dist / 1.6) ** 2)) * (0.75 + 0.25 * (Y < 1.2))
    return amb + warm * I * 0.95


def lit(col, L):
    c = np.clip(np.array(PAL[col] if isinstance(col, str) else col, float) * L, 0, 255)
    return tuple(int(v) for v in c)


# ------------------------------------------------------------------ drawing helpers (inputs in 1x screen px)
class Painter:
    def __init__(self, img):
        self.img = img; self.d = ImageDraw.Draw(img)

    def poly(self, pts, fill=None, outline=None, w=1.0):
        pts = [(float(x) * SS, float(y) * SS) for x, y in pts]
        if len(pts) < 3: return
        if fill is not None: self.d.polygon(pts, fill=fill)
        if outline is not None:
            self.d.line(pts + [pts[0]], fill=outline, width=max(1, int(round(w * SS))), joint='curve')

    def line(self, pts, color, w=1.0):
        pts = [(float(x) * SS, float(y) * SS) for x, y in pts]
        if len(pts) >= 2: self.d.line(pts, fill=color, width=max(1, int(round(w * SS))), joint='curve')

    def ellipse(self, c, rx, ry, fill):
        x, y = c; self.d.ellipse([(x - rx) * SS, (y - ry) * SS, (x + rx) * SS, (y + ry) * SS], fill=fill)


def draw_shapes(pt, shapes, M, colors, L, ink_w=1.0, flip_y=True, skip=()):
    for sh in shapes:
        if sh['tag'] in skip: continue
        P = catmull(sh['pts'], sh['closed']) if sh['smooth'] else sh['pts']
        if flip_y: P = P * np.array([1, -1])
        Q = apply(M, P)
        fill = colors(sh['fill']) if sh['fill'] else None
        st = lit('ink', np.minimum(L, 1.0)) if sh['stroke'] else None
        if sh['closed']:
            pt.poly(Q, fill=fill, outline=st, w=sh['w'] * ink_w)
        else:
            if st: pt.line(Q, st, w=sh['w'] * ink_w)


def bone_M(a, b, width_px):
    a = np.asarray(a, float); b = np.asarray(b, float)
    v = b - a; n = np.array([-v[1], v[0]]); ln = np.linalg.norm(n)
    n = n / ln if ln > 1e-6 else np.array([1.0, 0.0])
    return np.array([[n[0] * width_px, v[0], a[0]], [n[1] * width_px, v[1], a[1]]])


# ------------------------------------------------------------------ world (all drawn, projected through the camera)
class World:
    def __init__(self, cam, f, pt):
        self.cam, self.f, self.pt = cam, f, pt

    def P(self, X):
        return self.cam.project(np.array(X, float))[0]

    def quad(self, pts3, col, outline=None, w=0.8):
        Q = self.P(pts3)
        self.pt.poly(Q, fill=col, outline=outline, w=w)

    def seg(self, a, b, col, w=0.8):
        Q = self.P([a, b]); self.pt.line(Q, col, w)


def sky_base():
    y = np.linspace(0, 1, HH)[:, None]
    top = np.array([22, 26, 58.0]); mid = np.array([58, 56, 98.0]); low = np.array([150, 108, 112.0])
    c = np.where(y < 0.55, top + (mid - top) * (y / 0.55), mid + (low - mid) * ((y - 0.55) / 0.45))
    img = np.repeat(c[:, None, :], WW, axis=1)
    return img.astype(np.uint8)


SKY = None
_yy, _xx = np.mgrid[0:H, 0:W]
VIG = 1 - 0.32 * (((_xx - W / 2) / (W / 2)) ** 2 + ((_yy - H / 2) / (H / 2)) ** 2) ** 1.3
rng_static = np.random.default_rng(46)
STARS = [(rng_static.uniform(-40, 40), rng_static.uniform(6, 30), rng_static.uniform(0.4, 1.0)) for _ in range(60)]
TREES = []
xs = np.linspace(-30, 40, 120)
xs = np.linspace(-30, 40, 400)
hs = 1.9 + 0.9 * np.abs(np.sin(xs * 0.55)) + 0.55 * np.abs(np.sin(xs * 1.7 + 1.0)) + 0.5 * np.sin(xs * 0.13)
TREES = list(zip(xs, hs))


def draw_world(w, f):
    t = f['t']; pt = w.pt; cam = w.cam
    amb = 1 - 0.18 * t / 32
    # stars and moon (far away, parallax-free directions)
    for sx, sy, b in STARS:
        p = w.P([cam.pos[0] + sx, cam.pos[1] + sy, cam.pos[2] - 60])[0]
        if 0 <= p[0] < W and 0 <= p[1] < H * 0.55:
            c = int(150 + 90 * b * (0.6 + 0.4 * t / 32)); pt.ellipse(p, 0.9 * b, 0.9 * b, (c, c, int(c * 0.95)))
    m = w.P([cam.pos[0] + 14, cam.pos[1] + 13, cam.pos[2] - 60])[0]
    pt.ellipse(m, 13, 13, (236, 226, 196)); pt.ellipse((m[0] + 4, m[1] - 2), 11.5, 11.5, (60, 58, 98))
    # treeline far beyond the yard
    pts = [(x, h, -22.0) for x, h in TREES] + [(40, -0.6, -22.0), (-30, -0.6, -22.0)]
    w.quad(pts, (int(24 * amb), int(30 * amb), int(46 * amb)))
    # yard ground
    w.quad([(-30, -0.5, -22), (40, -0.5, -22), (40, -0.5, 12), (-30, -0.5, 12)], (int(34 * amb), int(40 * amb), int(52 * amb)))
    # a fence along the yard (Quick, Draw!-free: drawn posts)
    for x in np.arange(5.6, 14, 0.55):
        w.quad([(x, -0.5, -6), (x + 0.08, -0.5, -6), (x + 0.08, 0.55, -6), (x, 0.6, -6)], (int(48 * amb), int(50 * amb), int(66 * amb)))
    w.quad([(5.4, 0.28, -6), (14, 0.28, -6), (14, 0.36, -6), (5.4, 0.36, -6)], (int(48 * amb), int(50 * amb), int(66 * amb)))


def porch_color(X, Z, f, base=(96, 98, 112)):
    return lit(base, light_at(np.array([X, 0.0, Z]), f))


def draw_house(w, f):
    t = f['t']; pt = w.pt
    door = f['door']
    # ---------- interior (seen through the cut at Z = 0.9)
    Lin = light_at(np.array([-1.5, 1.0, -1.0]), f)
    w.quad([(-3.4, 0, -3.0), (-0.18, 0, -3.0), (-0.18, 2.75, -3.0), (-3.4, 2.75, -3.0)], lit((150, 120, 86), Lin))   # back wall
    w.quad([(-3.4, 0, -3.0), (-3.4, 0, 0.58), (-3.4, 2.75, 0.58), (-3.4, 2.75, -3.0)], lit((128, 100, 72), Lin * 0.9))  # side wall
    w.quad([(-3.4, 0, -3.0), (-0.18, 0, -3.0), (-0.18, 0, 0.58), (-3.4, 0, 0.58)], lit((112, 76, 50), Lin))             # floor
    for z in np.arange(-2.9, 0.58, 0.16):
        w.seg((-3.4, 0, z), (-0.18, 0, z), lit((86, 58, 40), Lin), 0.5)
    w.quad([(-3.4, 0, -3.0), (-0.18, 0, -3.0), (-0.18, 0.12, -3.0), (-3.4, 0.12, -3.0)], lit((92, 66, 46), Lin))     # skirting
    # rug where the person will sit
    w.quad([(-1.85, 0.005, -0.1), (-0.65, 0.005, -0.1), (-0.65, 0.005, 0.56), (-1.85, 0.005, 0.56)], lit((120, 58, 50), Lin))
    w.quad([(-1.78, 0.006, -0.03), (-0.72, 0.006, -0.03), (-0.72, 0.006, 0.49), (-1.78, 0.006, 0.49)], None, lit((168, 120, 72), Lin), 0.6)
    # picture frame and the lamp on the back wall
    w.quad([(-2.6, 1.35, -2.99), (-1.9, 1.35, -2.99), (-1.9, 1.85, -2.99), (-2.6, 1.85, -2.99)], lit((70, 50, 36), Lin), lit((40, 28, 22), Lin), 0.8)
    w.quad([(-2.53, 1.42, -2.98), (-1.97, 1.42, -2.98), (-1.97, 1.78, -2.98), (-2.53, 1.78, -2.98)], lit((112, 120, 104), Lin))
    w.seg((-1.1, 0.0, -2.6), (-1.1, 1.45, -2.6), lit((50, 36, 28), Lin), 1.2)
    w.quad([(-1.32, 1.45, -2.6), (-0.88, 1.45, -2.6), (-0.98, 1.75, -2.6), (-1.22, 1.75, -2.6)], (255, 214, 150))
    # ---------- door: the archive door, rectified and re-projected (projective fit) on its hinge
    draw_door(w, f)
    # ---------- facade (outer face X = 0), with the opening and a lit window
    wall = lit((86, 94, 116), light_at(np.array([0.05, 1.2, -1.2]), f) * 0.92)
    wall_near = lit((86, 94, 116), light_at(np.array([0.05, 1.2, 0.7]), f) * 0.92)
    w.quad([(0, 0, -3.2), (0, 0, -0.46), (0, 2.75, -0.46), (0, 2.75, -3.2)], wall)
    w.quad([(0, 2.05, -0.46), (0, 2.05, 0.46), (0, 2.75, 0.46), (0, 2.75, -0.46)], wall)
    w.quad([(0, 2.05, 0.46), (0, 2.05, 0.58), (0, 2.75, 0.58), (0, 2.75, 0.46)], wall_near)
    # window (Z -2.5..-1.5)
    w.quad([(0.001, 0.95, -2.5), (0.001, 0.95, -1.5), (0.001, 1.95, -1.5), (0.001, 1.95, -2.5)], (214, 160, 96))
    w.seg((0.002, 1.45, -2.5), (0.002, 1.45, -1.5), (60, 50, 50), 1.0)
    w.seg((0.002, 0.95, -2.0), (0.002, 1.95, -2.0), (60, 50, 50), 1.0)
    w.quad([(0.002, 0.95, -2.5), (0.002, 0.95, -1.5), (0.002, 1.95, -1.5), (0.002, 1.95, -2.5)], None, (52, 52, 62), 1.6)
    # clapboard lines
    for y in np.arange(0.15, 2.75, 0.15):
        c = lit((60, 66, 86), light_at(np.array([0.05, y, -1.0]), f))
        for (z0, z1) in ((-3.2, -2.5), (-1.5, -0.55)):
            if 0.95 < y < 1.95 or z0 != -3.2 and False: pass
            w.seg((0.003, y, z0), (0.003, y, z1), c, 0.55)
        w.seg((0.003, y, -2.5), (0.003, y, -1.5), c, 0.55) if not (0.95 <= y <= 1.95) else None
        if y > 2.15: w.seg((0.003, y, -0.55), (0.003, y, 0.58), c, 0.55)
    # door casing (trim) on the facade
    trim = lit((160, 158, 150), light_at(np.array([0.05, 1.0, 0.0]), f) * 0.85)
    for a, b in (((0.004, 0, -0.56), (0.004, 2.15, -0.56)), ((0.004, 0, 0.56), (0.004, 2.15, 0.56))):
        pass
    w.quad([(0.004, 0, -0.56), (0.004, 0, -0.46), (0.004, 2.05, -0.46), (0.004, 2.15, -0.56)], trim)
    w.quad([(0.004, 2.05, -0.46), (0.004, 2.05, 0.46), (0.004, 2.15, 0.56), (0.004, 2.15, -0.56)], trim)
    # jamb faces and lintel underside (wall thickness), lit from inside
    jam = lit((150, 120, 92), light_at(np.array([-0.1, 1.0, -0.4]), f))
    w.quad([(0, 0, -0.46), (-0.18, 0, -0.46), (-0.18, 2.05, -0.46), (0, 2.05, -0.46)], jam)
    w.quad([(0, 2.05, -0.46), (-0.18, 2.05, -0.46), (-0.18, 2.05, 0.46), (0, 2.05, 0.46)], lit((110, 90, 72), light_at(np.array([-0.1, 2.0, 0]), f)))
    # sill
    sl = lit((128, 104, 80), light_at(np.array([0.0, 0.03, 0.0]), f))
    w.quad([(0.06, 0.035, -0.46), (-0.2, 0.035, -0.46), (-0.2, 0.035, 0.46), (0.06, 0.035, 0.46)], sl, lit((44, 34, 30), np.ones(3)), 0.6)
    w.quad([(0.06, 0.0, -0.46), (0.06, 0.035, -0.46), (0.06, 0.035, 0.46), (0.06, 0.0, 0.46)], lit((70, 56, 46), light_at(np.array([0.1, 0.02, 0]), f)))
    # eave
    w.quad([(0.0, 2.75, -3.2), (0.45, 2.75, -3.2), (0.45, 2.75, 0.9), (0.0, 2.75, 0.9)], (36, 38, 54))
    w.quad([(0.45, 2.75, -3.2), (0.45, 2.92, -3.2), (0.45, 2.92, 0.9), (0.45, 2.75, 0.9)], (46, 48, 66))
    # ---------- the cut (section) at Z = 0.9: wall, floor slab, ceiling, drawn as a cut, hatched
    cut = (30, 26, 34); ZC = 0.58
    w.quad([(0.004, 2.05, ZC), (0.004, 2.92, ZC), (-0.18, 2.92, ZC), (-0.18, 2.05, ZC)], cut)
    w.quad([(-3.5, 0, ZC), (-0.18, 0, ZC), (-0.18, -0.5, ZC), (-3.5, -0.5, ZC)], cut)
    w.quad([(-3.5, 2.75, ZC), (0.45, 2.75, ZC), (0.45, 2.98, ZC), (-3.5, 2.98, ZC)], cut)
    for k in np.arange(-3.5, -0.2, 0.12):
        w.seg((k, -0.02, ZC), (k + 0.12, -0.46, ZC), (56, 48, 58), 0.5)


def draw_near_jamb(w, f):
    """the near side of the door frame (casing and jamb, cut at Z=0.58): in front of whatever crosses the threshold"""
    trim = lit((160, 158, 150), light_at(np.array([0.05, 1.0, 0.3]), f) * 0.85)
    jam = lit((40, 34, 40), np.ones(3))
    w.quad([(0.004, 0, 0.46), (0.004, 0, 0.56), (0.004, 2.15, 0.56), (0.004, 2.05, 0.46)], trim)
    w.quad([(0.004, 2.05, -0.46), (0.004, 2.05, 0.46), (0.004, 2.15, 0.56), (0.004, 2.15, -0.56)], trim)


_DOOR_TEX = None


def door_texture():
    global _DOOR_TEX
    if _DOOR_TEX is None:
        im = Image.open(DOOR_TEX).convert('RGB')
        # rectify the source quad to a 240 x 560 panel (projective fit), mirrored so the hinge matches this house
        tw, th = 240, 560
        coeffs = persp_coeffs([(0, 0), (tw, 0), (tw, th), (0, th)], DOOR_SRC_QUAD)
        rect = im.transform((tw, th), Image.PERSPECTIVE, coeffs, Image.BICUBIC)
        rect = rect.transpose(Image.FLIP_LEFT_RIGHT)
        # the source panel's top runs out of frame: add a plain head rail (drawn) above it
        full = Image.new('RGB', (tw, 600), (200, 198, 190)); full.paste(rect, (0, 40))
        d = ImageDraw.Draw(full); d.rectangle([0, 0, tw - 1, 599], outline=(120, 116, 110), width=3)
        _DOOR_TEX = full
    return _DOOR_TEX


def persp_coeffs(dst, src):
    """coefficients for PIL PERSPECTIVE: maps output (dst) points to input (src) points"""
    A = []; B = []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()


def draw_door(w, f):
    ang = math.radians(f['door'])
    hinge = np.array([-0.09, 0.0, -0.46])
    dirp = np.array([-math.sin(ang), 0.0, math.cos(ang)])
    free = hinge + 0.92 * dirp
    quad3 = [hinge + UP * 2.03, free + UP * 2.03, free, hinge]   # TL(hinge top) TR(free top) BR BL
    Q = w.P(quad3) * SS
    tex = door_texture(); tw, th = tex.size
    # visible face: outer face normal (cos, 0, sin); grade by the light it receives
    L = light_at(np.array([-0.4, 1.0, -0.6]), w.f) * 0.85
    texl = Image.fromarray(np.clip(np.asarray(tex, float) * L, 0, 255).astype(np.uint8))
    x0, y0 = np.floor(Q.min(0)).astype(int); x1, y1 = np.ceil(Q.max(0)).astype(int)
    x0 = max(0, x0); y0 = max(0, y0); x1 = min(WW, x1); y1 = min(HH, y1)
    if x1 - x0 < 2 or y1 - y0 < 2: return
    # texture TL is the hinge-top after the mirror? the mirrored texture has its hinge at right; map hinge -> right edge
    src = [(tw, 0), (0, 0), (0, th), (tw, th)]
    dst = [(q[0] - x0, q[1] - y0) for q in Q]
    co = persp_coeffs(dst, src)
    patch = texl.transform((x1 - x0, y1 - y0), Image.PERSPECTIVE, co, Image.BICUBIC)
    mask = Image.new('L', (x1 - x0, y1 - y0), 0)
    ImageDraw.Draw(mask).polygon([tuple(d) for d in dst], fill=255)
    w.pt.img.paste(patch, (x0, y0), mask)
    # edge of the door (thickness) as a dark line
    w.pt.line(w.P([free, free + UP * 2.03]), (60, 46, 40), 1.2)


def draw_porch(w, f):
    pt = w.pt
    w.quad([(0, 0, -1.7), (4.9, 0, -1.7), (4.9, 0, 1.4), (0, 0, 1.4)], porch_color(2.0, 0.0, f, (78, 82, 98)))
    # boards along X, shaded by the light they get
    for z in np.arange(-1.7, 1.4, 0.13):
        for x0 in np.arange(0, 4.9, 0.7):
            x1 = min(4.9, x0 + 0.7)
            c = lit((92, 94, 110), np.array([0.60, 0.64, 0.84]) * (1 - 0.18 * f['t'] / 32.0) * (0.96 + 0.08 * ((int(x0 / 0.7) * 7 + int((z + 2) / 0.13) * 3) % 5) / 4))
            w.quad([(x0, 0, z + 0.008), (x1, 0, z + 0.008), (x1, 0, z + 0.122), (x0, 0, z + 0.122)], c)
        w.seg((0, 0.0005, z), (4.9, 0.0005, z), porch_color(2.0, z, f, (44, 46, 58)), 0.5)
    # front fascia and steps down at 4.9
    w.quad([(0, 0, 1.4), (4.9, 0, 1.4), (4.9, -0.5, 1.4), (0, -0.5, 1.4)], (40, 44, 58))
    for k in range(3):
        y = -0.17 * (k + 1); x0 = 4.9 + 0.3 * k; x1 = x0 + 0.3
        w.quad([(x0, y, -1.2), (x1, y, -1.2), (x1, y, 1.2), (x0, y, 1.2)], porch_color(x0, 0, f, (70, 72, 88)))
        w.quad([(x0, y + 0.17, 1.2), (x0, y, 1.2), (x1, y, 1.2), (x1, y + 0.17 - 0.0, 1.2)], (36, 40, 52))
    # far railing (behind the dog)
    rc = (52, 54, 72)
    for x in (0.25, 1.6, 3.2, 4.85):
        w.quad([(x - 0.05, 0, -1.65), (x + 0.05, 0, -1.65), (x + 0.05, 1.0, -1.65), (x - 0.05, 1.0, -1.65)], rc)
    w.quad([(0.2, 0.92, -1.65), (4.9, 0.92, -1.65), (4.9, 1.0, -1.65), (0.2, 1.0, -1.65)], rc)
    w.quad([(0.2, 0.08, -1.65), (4.9, 0.08, -1.65), (4.9, 0.13, -1.65), (0.2, 0.13, -1.65)], rc)
    for x in np.arange(0.35, 4.85, 0.16):
        w.seg((x, 0.13, -1.65), (x, 0.92, -1.65), (46, 48, 64), 0.9)


# ------------------------------------------------------------------ the dog
def proj(cam, X):
    p, z = cam.project(np.array(X, float)); return p[0], float(z[0])


def px_per_m(cam, X):
    return cam.focal / float(cam.project(np.array(X, float))[1][0])


def dog_parts(cam, f, p, r):
    """returns list of (depth, callable(painter)) for the dog, plus measured landmarks for the trace"""
    body = {k: np.array(v) for k, v in p['body'].items()}
    head = {k: np.array(v) for k, v in p['head'].items()}
    th = f['heading']; fw = fwd_of(th)
    center = (body['W'] + body['R'] + body['K'] + body['B']) / 4
    cdepth = proj(cam, center)[1]
    parts = []
    Lb = light_at(center, f)
    colors = lambda k: lit(k, Lb)
    # torso
    vt = r['torso']['view']; Mt = np.array(r['torso']['M'])
    parts.append((cdepth, lambda pt: draw_shapes(pt, TORSO[vt]['shapes'], Mt, colors, Lb)))
    # legs
    for name, js in p['legs'].items():
        J = [np.array(j) for j in js]
        rd = proj(cam, J[0])[1]
        near = rd < cdepth
        col = 'coat' if near else 'coat_far'
        fore = name.startswith('F')
        Ll = light_at(J[-1], f) * (1.0 if near else 0.82)
        def leg(pt, J=J, fore=fore, col=col, Ll=Ll, near=near):
            sc = px_per_m(cam, J[0])
            pts = [proj(cam, j)[0] for j in J]
            if fore:
                chain = pts[:3]; widths = [0.12, 0.062, 0.05]; paw = (pts[2], pts[3])
            else:
                chain = pts[:4]; widths = [0.17, 0.075, 0.05, 0.045]; paw = (pts[3] + (pts[3] - pts[4]) * 0.3, pts[4])
            limb_outline(pt, chain, [w_ * sc for w_ in widths], lit(col, Ll), lit('ink', np.minimum(Ll, 1)))
            pc = 'white' if fore else col
            draw_shapes(pt, BONES['paw'], bone_M(paw[0], paw[1], BONE_W['paw'] * sc * 0.8), lambda k: lit(pc, Ll), Ll, flip_y=False)
        parts.append((rd + (0.0 if not near else -0.001), leg))
    # tail
    chain = [np.array(c) for c in p['tail']]
    td = proj(cam, chain[1])[1]
    def tail(pt):
        pts = np.array([proj(cam, c)[0] for c in chain]); sc = px_per_m(cam, chain[0])
        widths = np.linspace(0.055, 0.018, len(pts)) * sc
        left = []; right = []
        for k in range(len(pts)):
            a = pts[max(0, k - 1)]; b = pts[min(len(pts) - 1, k + 1)]
            v = b - a; n = np.array([-v[1], v[0]]); n = n / (np.linalg.norm(n) + 1e-9)
            left.append(pts[k] + n * widths[k] / 2); right.append(pts[k] - n * widths[k] / 2)
        poly = catmull(left + [pts[-1] + (pts[-1] - pts[-2]) * 0.35] + right[::-1], True, 4)
        Lt = light_at(chain[2], f)
        pt.poly(poly, fill=lit('coat', Lt), outline=lit('ink', np.minimum(Lt, 1)), w=1.0)
        tip = catmull([left[-2], pts[-1] + (pts[-1] - pts[-2]) * 0.35, right[-2], pts[-2]], True, 3)
        pt.poly(tip, fill=lit('white', Lt))
    parts.append((td, tail))
    # neck + head + ears + eyes
    S = np.array(p['skull']); N = body['N']
    sd = proj(cam, S)[1]
    vh = r['head']['view']; side_h = r['head']['side']; Mh = np.array(r['head']['M'])
    Lh = light_at(S, f)
    hcol = lambda k: lit(k, Lh)
    ears = {s: (np.array(a), np.array(b)) for s, (a, b) in p['ears'].items()}
    def neck(pt):
        sc = px_per_m(cam, N)
        a = proj(cam, N)[0]; b = proj(cam, S)[0]
        draw_shapes(pt, BONES['neck'], bone_M(a, b, BONE_W['neck'] * sc), lambda k: lit(k, light_at(N, f)), Lh, flip_y=False)
    def ear(pt, s):
        a, b = ears[s]
        sc = px_per_m(cam, a)
        pa, pb = proj(cam, a)[0], proj(cam, b)[0]
        # the ear shows its inner face when the head is seen from the front half
        frontish = vh <= 90
        sh = EAR['inner'] if frontish else EAR['outer']
        v = pb - pa; ln = np.linalg.norm(v)
        minlen = 0.07 * sc
        if ln < minlen:   # an ear seen end-on keeps a readable length along the head's up direction
            upv = apply(Mh, np.array([[0, 0.0], [0, -1.0]])); upv = upv[1] - upv[0]; upv /= (np.linalg.norm(upv) + 1e-9)
            pb = pa + (v / (ln + 1e-9) * ln + upv * (minlen - ln) * 0.8)
        draw_shapes(pt, sh, bone_M(pa, pb, 0.085 * sc), hcol, Lh, flip_y=False)
    def headf(pt):
        draw_shapes(pt, HEADS[vh]['shapes'], Mh, hcol, Lh, skip=('mouthline',) if f['mouth'] > 0.08 else ())
        draw_mouth(pt, vh, Mh, f, Lh)
        draw_eyes(pt, vh, side_h, Mh, f, Lh)
    # ear depth ordering relative to the skull
    ear_d = {s: proj(cam, ears[s][0])[1] for s in ears}
    def head_group(pt):
        for s in ears:
            if ear_d[s] > sd: ear(pt, s)
        neck(pt)
        headf(pt)
        for s in ears:
            if ear_d[s] <= sd: ear(pt, s)
    hd = sd if sd > cdepth + 0.12 else min(sd, cdepth - 0.02)
    parts.append((hd, head_group))
    return parts


def limb_outline(pt, chain, widths, fill, ink):
    """one continuous limb through its pivot landmarks (no seams at the joints)"""
    P = [np.asarray(p, float) for p in chain]
    L, R = [], []
    for k in range(len(P)):
        if k == 0: v = P[1] - P[0]
        elif k == len(P) - 1: v = P[-1] - P[-2]
        else:
            a = P[k] - P[k - 1]; b = P[k + 1] - P[k]
            v = a / (np.linalg.norm(a) + 1e-9) + b / (np.linalg.norm(b) + 1e-9)
        n = np.array([-v[1], v[0]]); n = n / (np.linalg.norm(n) + 1e-9)
        L.append(P[k] + n * widths[k] / 2); R.append(P[k] - n * widths[k] / 2)
    top = P[0] - (P[1] - P[0]) / (np.linalg.norm(P[1] - P[0]) + 1e-9) * widths[0] * 0.45
    poly = catmull([top] + L + [P[-1] + (P[-1] - P[-2]) / (np.linalg.norm(P[-1] - P[-2]) + 1e-9) * widths[-1] * 0.4] + R[::-1], True, 5)
    pt.poly(poly, fill=fill, outline=ink, w=1.0)


def draw_mouth(pt, vh, Mh, f, Lh):
    m = f['mouth']
    if vh not in (45, 90) or m <= 0.08: return
    if vh == 90:
        a, b, c = (0.248, -0.066), (0.20, -0.064), (0.14, -0.052)
        lo = (0.20, -0.066 - 0.05 * m)
    else:
        a, b, c = (0.178, -0.066), (0.15, -0.072), (0.07, -0.058)
        lo = (0.15, -0.072 - 0.045 * m)
    P = np.array([a, b, c, lo]) * np.array([1, -1])
    Q = apply(Mh, catmull(P, True, 4))
    pt.poly(Q, fill=lit('mouth', Lh), outline=lit('ink', np.minimum(Lh, 1)), w=0.7)
    if m > 0.25:
        T = np.array([(a[0] - 0.01, a[1] - 0.006), (lo[0], lo[1] + 0.004), (lo[0] + 0.03, lo[1] - 0.004)]) * np.array([1, -1])
        pt.poly(apply(Mh, T), fill=lit('tongue', Lh))


def draw_eyes(pt, vh, side_h, Mh, f, Lh):
    spec = HEADS[vh]['eyes']; lm = HEADS[vh]['lm']
    lid = max(0.05, min(1.0, f['lid']))
    for role, key in spec.items():
        c = np.array(lm[key])
        sx = EYE['w'] * (0.62 if role == 'far' else (0.45 if role == 'near_sliver' else 1.0))
        sy = EYE['h']
        xs = np.linspace(-1, 1, 15)
        up = sy * (1 - xs ** 2) ** 0.55 * (1 + 0.15 * xs)
        lo = -sy * 0.8 * (1 - xs ** 2) ** 0.7
        top = np.stack([c[0] + xs * sx / 2, c[1] + up / 2], 1)
        bot = np.stack([c[0] + xs[::-1] * sx / 2, c[1] + lo[::-1] / 2], 1)
        almond = np.vstack([top, bot])
        F = lambda Pn: apply(Mh, np.asarray(Pn) * np.array([1, -1]))
        pt.poly(F(almond), fill=lit((40, 26, 18), Lh), outline=lit('ink', np.minimum(Lh, 1)), w=0.7)
        if role != 'near_sliver':
            gaze = 0.28 if f['crouch'] < 0.5 else -0.05
            ic = np.array([c[0] + gaze * sx / 2, c[1] - sy * 0.05])
            ang = np.linspace(0, 2 * np.pi, 14)
            iris = np.stack([ic[0] + 0.36 * sx * np.cos(ang), ic[1] + 0.40 * sy * np.sin(ang)], 1)
            pt.poly(F(iris), fill=lit('iris', np.maximum(Lh, 0.7)))
            pup = np.stack([ic[0] + 0.17 * sx * np.cos(ang), ic[1] + 0.2 * sy * np.sin(ang)], 1)
            pt.poly(F(pup), fill=lit('pupil', Lh))
            sh = np.stack([ic[0] + 0.12 * sx + 0.07 * sx * np.cos(ang), ic[1] + 0.14 * sy + 0.08 * sy * np.sin(ang)], 1)
            pt.poly(F(sh), fill=lit('shine', np.maximum(Lh, 0.85)))
            if f['crouch'] > 0.6:   # the white of a worried eye
                wh = np.stack([c[0] + (0.30 + 0.14 * np.cos(ang)) * sx, c[1] + 0.25 * sy * np.sin(ang) * 0.8], 1)
                pt.poly(F(wh), fill=lit((214, 204, 188), Lh))
        # the lid comes down from the top (eye control)
        cover = 1.0 - lid
        if cover > 0.02:
            lidline = top[:, 1] - cover * (top[:, 1] - np.interp(top[:, 0], bot[::-1, 0], bot[::-1, 1]))
            lidpoly = np.vstack([top + np.array([0, 0.002]), np.stack([top[::-1, 0], lidline[::-1]], 1)])
            pt.poly(F(lidpoly), fill=lit('coat', Lh))
            pt.line(F(np.stack([top[:, 0], lidline], 1)), lit('ink', np.minimum(Lh, 1)), 0.8)


# ------------------------------------------------------------------ the person (drawn body; the face is the source portrait)
_FACES = {}


def face_img(state):
    if state not in _FACES:
        man = json.load(open(os.path.join(FACE_DIR, 'manifest.json')))
        fn = sorted(k for k, v in man['frames'].items() if v['state'] == state)[0]
        _FACES[state] = Image.open(os.path.join(FACE_DIR, fn)).convert('RGBA')
    return _FACES[state]


def person_skeleton(f):
    p = f['person']; t = f['t']
    X, Z = p['X'], p['Z']; sit = p['sit2']; lean = p['lean']; walk = p['walk']
    fwd = np.array([1.0, 0, 0])
    hip = np.array([X, 0.93 * (1 - sit) + 0.13 * sit, Z])
    hip[0] -= 0.12 * sit * (1 - sit) * 4 * 0.5
    lam = math.radians(4 + 22 * lean + 6 * sit)
    tdir = np.array([math.sin(lam), math.cos(lam), 0])
    sh = hip + 0.52 * tdir
    neck = sh + 0.08 * np.array([math.sin(lam * 0.7), math.cos(lam * 0.7), 0])
    skull = neck + np.array([0.025, 0.10, 0])
    # feet: two steps while stepping aside, then out in front when seated
    f_near0 = np.array([-0.18, 0, 0.10]); f_far0 = np.array([-0.40, 0, -0.10])
    f_near1 = np.array([-1.00, 0, 0.84]); f_far1 = np.array([-1.18, 0, 0.62])
    s1 = smoothstep(5.0, 5.45, t); s2 = smoothstep(5.4, 5.9, t)
    fn = f_near0 + (f_near1 - f_near0) * s1; fn[1] = 0.08 * math.sin(math.pi * s1)
    ff = f_far0 + (f_far1 - f_far0) * s2; ff[1] = 0.08 * math.sin(math.pi * s2)
    seat_n = hip + np.array([0.56, -0.12, 0.10]); seat_n[1] = 0.0
    seat_f = hip + np.array([0.48, -0.12, -0.10]); seat_f[1] = 0.0
    fn = fn + (seat_n - fn) * sit; ff = ff + (seat_f - ff) * sit
    # arms
    reach = p['reach2']; low = p['low2']
    hang_n = sh + np.array([0.06, -0.60, 0.12]); hang_f = sh + np.array([-0.04, -0.58, -0.12])
    reach_n = sh + 0.64 * np.array([math.cos(math.radians(-28)), math.sin(math.radians(-28)), 0]) + np.array([0, 0, 0.1])
    knee_rest = hip + np.array([0.34, 0.36, -0.08])
    low_n = hip + np.array([0.80, 0.05, -0.14]); low_n[1] = 0.24
    hand_n = hang_n + (reach_n - hang_n) * reach
    hand_n = hand_n + ((hip + np.array([0.30, 0.30, 0.14])) - hand_n) * sit * (1 - low)
    hand_n = hand_n + (low_n - hand_n) * low
    back = smoothstep(24.3, 25.6, t)   # once it lies down, the hand is drawn back and rests low, giving it room
    rest_n = hip + np.array([0.52, 0.0, -0.12]); rest_n[1] = 0.16
    hand_n = hand_n + (rest_n - hand_n) * back
    hand_f = hang_f + (knee_rest - hang_f) * sit
    return dict(hip=hip, sh=sh, neck=neck, skull=skull, lam=lam, foot_n=fn, foot_f=ff, hand_n=hand_n, hand_f=hand_f, sit=sit)


def ik_knee(a, c, L1, L2, bend):
    from pose import ik2
    m, e = ik2(a, c, L1, L2, bend); return m, e


def person_parts(cam, f):
    sk = person_skeleton(f)
    Lp = light_at(np.array([sk['hip'][0], 1.0, sk['hip'][2]]), f)
    Lp = Lp * 0.85
    coat = lit((58, 66, 92), Lp); coat_far = lit((44, 50, 72), Lp); trous = lit((60, 54, 58), Lp); trous_f = lit((46, 42, 46), Lp)
    skin = lit((196, 150, 122), Lp); shoe = lit((34, 28, 30), Lp); ink = lit('ink', np.minimum(Lp, 1))
    hip, sh = sk['hip'], sk['sh']
    fw = np.array([1.0, 0, 0])
    def limb(pt, a, m, b, wa, wb, col):
        sc = px_per_m(cam, a)
        A, Mm, B = proj(cam, a)[0], proj(cam, m)[0], proj(cam, b)[0]
        limb_outline(pt, [A, Mm, B], [wa * sc, (wa + wb) / 2 * sc * 0.95, wb * sc], col, ink)
    def legs_far(pt):
        hf = hip + np.array([0, 0, -0.09]); ank = sk['foot_f'] + np.array([0, 0.07, 0])
        k, e = ik_knee(hf, ank, 0.46, 0.45, fw)
        limb(pt, hf, k, e, 0.17, 0.11, trous_f)
        foot(pt, e, sk['foot_f'], shoe)
    def legs_near(pt):
        hn = hip + np.array([0, 0, 0.09]); ank = sk['foot_n'] + np.array([0, 0.07, 0])
        k, e = ik_knee(hn, ank, 0.46, 0.45, fw)
        limb(pt, hn, k, e, 0.18, 0.115, trous)
        foot(pt, e, sk['foot_n'], shoe)
    def foot(pt, ank, fpos, col):
        sc = px_per_m(cam, ank)
        a = proj(cam, ank)[0]; b = proj(cam, fpos + np.array([0.20, 0.0, 0]))[0]; c = proj(cam, fpos + np.array([-0.06, 0, 0]))[0]
        pt.poly(catmull([a + (0, -2), b + (0, -0.03 * sc), b, c], True, 4), fill=col, outline=ink, w=0.7)
    def arm(pt, hand, near):
        side = 0.13 if near else -0.13
        s = sh + np.array([0, -0.05, side])
        e, h2 = ik_knee(s, hand, 0.31, 0.30, np.array([-0.2, -1, 0]))
        limb(pt, s, e, h2, 0.11, 0.085, coat if near else coat_far)
        sc = px_per_m(cam, h2)
        hp = proj(cam, h2)[0]; v = hp - proj(cam, e)[0]; v /= (np.linalg.norm(v) + 1e-9)
        n = np.array([-v[1], v[0]])
        L = 0.11 * sc
        hand_poly = [hp + n * 0.035 * sc, hp + v * L * 0.75 + n * 0.03 * sc, hp + v * L, hp + v * L * 0.8 - n * 0.035 * sc, hp - n * 0.04 * sc]
        pt.poly(catmull(hand_poly, True, 3), fill=skin, outline=ink, w=0.7)
        pt.poly(catmull([hp + n * 0.02 * sc, hp + n * 0.07 * sc + v * L * 0.25, hp + n * 0.05 * sc + v * L * 0.45], True, 3), fill=skin, outline=ink, w=0.6)
    def torso(pt):
        sc = px_per_m(cam, hip)
        a = proj(cam, hip)[0]; b = proj(cam, sh)[0]
        M = bone_M(a, b, 0.36 * sc)
        M[:, 1] *= -1; M[:, 2] = a + (b - a) * 0.0   # local y up from hip to shoulder (y=1 at the shoulder)
        M = np.array([[M[0, 0], (b - a)[0], a[0]], [M[1, 0], (b - a)[1], a[1]]])
        coat_pts = [(-0.45, -0.10), (-0.52, 0.35), (-0.46, 0.76), (-0.30, 1.0), (-0.06, 1.08), (0.16, 1.02), (0.40, 0.88),
                    (0.46, 0.56), (0.40, 0.26), (0.46, -0.06), (0.05, -0.14)]
        pt.poly(apply(M, catmull(coat_pts, True, 5)), fill=coat, outline=ink, w=0.9)
        pt.line(apply(M, catmull([(0.30, 0.90), (0.36, 0.55), (0.30, 0.15), (0.34, -0.08)], False, 4)), lit((40, 46, 66), Lp), 0.7)
        pt.poly(apply(M, catmull([(-0.20, 1.0), (-0.05, 1.12), (0.18, 1.05), (0.10, 0.92), (-0.08, 0.95)], True, 3)), fill=lit((120, 108, 96), Lp), outline=ink, w=0.6)
    def headf(pt):
        draw_person_head(pt, cam, f, sk, Lp)
    sd = proj(cam, hip)[1]
    parts = [(sd + 0.2, lambda pt: (legs_far(pt), arm(pt, sk['hand_f'], False))), (sd, lambda pt: (torso(pt), legs_near(pt) if sk['sit'] > 0.5 else None)),
             (sd - 0.01, lambda pt: (legs_near(pt) if sk['sit'] <= 0.5 else None, headf(pt), arm(pt, sk['hand_n'], True)))]
    return parts, sk


# cranium, hat and ear are drawn in the source portrait's own pixel frame (x right, y down), so one similarity fit
# places the whole head; the hat brim covers exactly the forehead the source never showed.
HAT = [(-150, -38), (-105, -130), (-10, -180), (110, -150), (150, -70), (166, -42), (232, -24), (240, -16), (150, -18), (40, -20), (-60, -16), (-160, -20)]
HAT_BAND = [(-150, -38), (160, -44), (166, -26), (-158, -22)]
# forehead and cheek drawn in the portrait's own frame, under the cut, so the cut has no seam; the source never shows them
UNDERLAY = [(-20, -30), (141, -30), (146, -12), (151, 5), (122, 60), (96, 214), (-20, 222)]
FOREHEAD_LINE = [(141, -30), (146, -12), (151, 5)]
SKULL_BACK = [(-150, -30), (-162, 70), (-130, 160), (-60, 215), (4, 226), (22, 196), (0, 120), (8, 40), (4, -30)]
EAR_P = [(-20, 70), (-5, 60), (10, 85), (5, 120), (-15, 130), (-28, 105)]
NECK_P = [(-90, 200), (40, 210), (60, 320), (-110, 320)]
EYE_C, EYE_W, EYE_H = (124.0, 1.0), 27.0, 13.0
MOUTH_CAV = {'half': ((104, 134), 22, 8), 'open': ((100, 136), 26, 24)}
FACE_LM_KEYS = ('bridge', 'nose_tip', 'chin')
PERSON_BLINKS = (2.6, 9.2, 13.1, 17.8, 21.4, 25.1, 28.6, 31.0)


def person_head_fit(cam, sk, f, src_lm):
    """the portrait is registered by its landmarks: target landmarks are the source landmarks carried rigidly on the
    person's skull (metres, tilted with the body), projected; the fit is a similarity (no shear) and its residual is kept"""
    tilt = -sk['lam'] * 0.5 + math.radians(6) * f['person']['low2'] - math.radians(4) * (voice.envelope(f['t'])[1] >= 0.9)
    c, s_ = math.cos(tilt), math.sin(tilt)
    pivot = np.array([40.0, 95.0]); m_per_px = 0.00082
    src = np.array([src_lm[k] for k in FACE_LM_KEYS], float)
    dst = []
    for q in src:
        d = (q - pivot) * m_per_px; d = np.array([d[0], -d[1]])           # source y-down -> world y-up
        d = np.array([c * d[0] + s_ * d[1], -s_ * d[0] + c * d[1]])        # tilt (screen-clockwise positive)
        dst.append(cam.project(np.array(sk['skull']) + np.array([d[0], d[1], 0.0]))[0][0])
    from geom import fit_similarity, residual
    M = fit_similarity(src, np.array(dst))
    return M, residual(M, src, np.array(dst))


_FACE_MAN = None


def draw_person_head(pt, cam, f, sk, Lp):
    global _FACE_MAN
    t = f['t']
    if _FACE_MAN is None: _FACE_MAN = json.load(open(os.path.join(FACE_DIR, 'manifest.json')))
    state = voice.mouth_state(t)
    img = face_img(state)
    lm = next(v['landmarks'] for v in _FACE_MAN['frames'].values() if v['state'] == state)
    M, res = person_head_fit(cam, sk, f, lm)
    g = np.minimum(Lp * 1.05, 1.25)
    skin = tuple(int(v) for v in np.clip(np.array([198, 152, 124]) * g, 0, 255))
    hair = lit((40, 30, 30), Lp); hatc = lit((52, 44, 40), Lp); band = lit((104, 64, 52), Lp); ink = lit('ink', np.minimum(Lp, 1))
    pt.poly(apply(M, catmull(NECK_P, True, 3)), fill=skin, outline=ink, w=0.7)
    pt.poly(apply(M, np.array(UNDERLAY, float)), fill=skin)
    if state in MOUTH_CAV:
        (cx, cy), rx, ry = MOUTH_CAV[state]
        ang = np.linspace(0, 2 * np.pi, 20)
        pt.poly(apply(M, np.stack([cx + rx * np.cos(ang), cy + ry * np.sin(ang)], 1)), fill=lit((70, 30, 34), Lp))
    Ms = np.vstack([M, [0, 0, 1]]); Minv = np.linalg.inv(Ms)
    corners = apply(M, np.array([[0, 0], [384, 0], [384, 288], [0, 288]]))
    x0, y0 = np.floor(corners.min(0) * SS).astype(int); x1, y1 = np.ceil(corners.max(0) * SS).astype(int)
    if x1 > x0 and y1 > y0:
        T = np.array([[1.0 / SS, 0, x0 / SS], [0, 1.0 / SS, y0 / SS], [0, 0, 1]])
        A = Minv @ T
        arr = np.asarray(img, float).copy()
        arr[..., :3] = np.clip(arr[..., :3] * g, 0, 255)
        src = Image.fromarray(arr.astype(np.uint8), 'RGBA')
        patch = src.transform((x1 - x0, y1 - y0), Image.AFFINE, A[:2].flatten().tolist(), Image.BICUBIC)
        pt.img.paste(patch, (x0, y0), patch)
    pt.line(apply(M, catmull(FOREHEAD_LINE, False, 4)), ink, 0.8)
    # eye (control): almond, iris looking forward, lid with blinks; brow
    lid = 1.0
    for tb in PERSON_BLINKS:
        if tb <= t < tb + 0.16: lid = min(lid, 0.1 + 5 * abs(t - tb - 0.08))
    if f['person']['low2'] > 0.5: lid = min(lid, 0.92)
    xs = np.linspace(-1, 1, 13)
    top = np.stack([EYE_C[0] + xs * EYE_W / 2, EYE_C[1] - EYE_H / 2 * (1 - xs ** 2) ** 0.6], 1)
    bot = np.stack([EYE_C[0] + xs[::-1] * EYE_W / 2, EYE_C[1] + EYE_H / 2 * 0.8 * (1 - xs[::-1] ** 2) ** 0.7], 1)
    pt.poly(apply(M, np.vstack([top, bot])), fill=lit((236, 228, 216), np.maximum(Lp, 0.8)), outline=ink, w=0.6)
    ang = np.linspace(0, 2 * np.pi, 14)
    pt.poly(apply(M, np.stack([EYE_C[0] + 6 + 4.6 * np.cos(ang), EYE_C[1] + 0.5 + 5.2 * np.sin(ang)], 1)), fill=lit((48, 32, 26), Lp))
    if lid < 0.98:
        ly = top[:, 1] + (1 - lid) * (np.interp(top[:, 0], bot[::-1, 0], bot[::-1, 1]) - top[:, 1])
        pt.poly(apply(M, np.vstack([top - np.array([0, 1.0]), np.stack([top[::-1, 0], ly[::-1]], 1)])), fill=skin)
        pt.line(apply(M, np.stack([top[:, 0], ly], 1)), ink, 0.7)
    pt.line(apply(M, catmull([(108, -12), (124, -15), (138, -11)], False, 3)), hair, 1.3)
    pt.poly(apply(M, catmull(SKULL_BACK, True, 5)), fill=hair, outline=ink, w=0.8)
    pt.poly(apply(M, catmull(EAR_P, True, 3)), fill=skin, outline=ink, w=0.7)
    pt.poly(apply(M, catmull(HAT, True, 4)), fill=hatc, outline=ink, w=0.9)
    pt.poly(apply(M, np.array(HAT_BAND)), fill=band)
    return M, res


# ------------------------------------------------------------------ light spill and shadows
def spill_and_shadows(img, cam, f, p, sk):
    """warm light thrown through the doorway onto the porch, with the dog's and person's shadows cut out of it
    (landmarks projected from the lamp onto the floor), plus contact shadows"""
    o = 0.28 + 0.72 * door_open_frac(f)
    mask = Image.new('L', (W, H), 0); d = ImageDraw.Draw(mask)
    # the lit part of the opening: limited by the door's free edge while it is not fully open
    ang = math.radians(f['door']); freeZ = -0.46 + 0.92 * math.cos(ang)
    z0 = max(-0.46, min(0.46, freeZ)) if f['door'] < 90 else -0.46
    floor_pts = []
    for (z, y) in ((z0, 0.04), (0.46, 0.04), (0.46, 2.05), (z0, 2.05)):
        Pt = np.array([0.0, y, z]); dv = Pt - LAMP
        if y < 0.1: G = Pt
        else:
            tt = (0.0 - LAMP[1]) / dv[1]; G = LAMP + dv * tt
        floor_pts.append(G)
    floor_pts = [floor_pts[0], floor_pts[1], floor_pts[2], floor_pts[3]]
    # clip the far end to the porch
    FP = []
    for G in floor_pts:
        G = G.copy()
        if G[0] > 5.0:
            k = (5.0 - 0.0) / max(1e-6, G[0]); G = np.array([5.0, 0, floor_pts[0][2] + (G[2] - floor_pts[0][2]) * k])
        FP.append(G)
    Q = cam.project(np.array(FP))[0]
    d.polygon([tuple(q) for q in Q], fill=int(255 * o))
    # shadows: the dog's landmark vector and the person's skeleton, projected from the lamp onto the floor
    sh = Image.new('L', (W, H), 0); ds = ImageDraw.Draw(sh)
    def shadow_pts(pts3):
        out = []
        for X in pts3:
            X = np.array(X, float)
            if X[0] <= LAMP[0] + 0.05: continue
            dv = X - LAMP
            if dv[1] >= -1e-3: continue
            tt = (0.0 - LAMP[1]) / dv[1]; G = LAMP + dv * tt
            if G[0] < 0.0: continue
            out.append(G)
        return out
    def hull(P2):
        P2 = sorted(map(tuple, P2))
        if len(P2) < 3: return P2
        def cross(o, a, b): return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
        lo, up = [], []
        for q in P2:
            while len(lo) >= 2 and cross(lo[-2], lo[-1], q) <= 0: lo.pop()
            lo.append(q)
        for q in reversed(P2):
            while len(up) >= 2 and cross(up[-2], up[-1], q) <= 0: up.pop()
            up.append(q)
        return lo[:-1] + up[:-1]
    groups = [list(p['body'].values()), list(p['head'].values()) + [p['skull']] + [p['body']['N']]]
    for js in p['legs'].values(): groups.append(js)
    groups.append(p['tail'])
    hp = sk['hip']; skl = sk['skull']
    groups.append([hp + np.array([0, 0, 0.15]), hp - np.array([0, 0, 0.15]), sk['sh'] + np.array([0, 0, 0.2]), sk['sh'] - np.array([0, 0, 0.2]), skl + np.array([0, 0.12, 0]), skl + np.array([0.1, 0, 0])])
    groups.append([sk['foot_n'], sk['foot_f'], hp, sk['hand_n'], sk['hand_f']])
    for g in groups:
        G = shadow_pts(g)
        if len(G) >= 3:
            Q = cam.project(np.array(G))[0]
            ds.polygon([tuple(q) for q in hull(Q)], fill=255)
    sh = sh.filter(ImageFilter.GaussianBlur(3))
    mask = mask.filter(ImageFilter.GaussianBlur(9))
    m = np.asarray(mask, float) / 255.0 * (1 - 0.88 * np.asarray(sh, float) / 255.0)
    # contact shadow under the dog
    ct = Image.new('L', (W, H), 0); dc = ImageDraw.Draw(ct)
    body = p['body']; c = (np.array(body['W']) + np.array(body['R'])) / 2
    th = f['heading']; fw = fwd_of(th); rt = right_of(th)
    ell = [np.array([c[0], 0.0, c[2]]) + fw * 0.55 * math.cos(a) + rt * 0.2 * math.sin(a) for a in np.linspace(0, 2 * math.pi, 20)]
    Qe = cam.project(np.array(ell))[0]
    dc.polygon([tuple(q) for q in Qe], fill=150 + int(60 * f['lie']))
    for js in p['legs'].values():
        q = cam.project(np.array(js[-1]))[0][0]; dc.ellipse([q[0] - 7, q[1] - 2.5, q[0] + 7, q[1] + 2.5], fill=200)
    for ft in (sk['foot_n'], sk['foot_f']):
        q = cam.project(np.array(ft))[0][0]; dc.ellipse([q[0] - 10, q[1] - 3, q[0] + 12, q[1] + 3], fill=170)
    ct = ct.filter(ImageFilter.GaussianBlur(5))
    return m, np.asarray(ct, float) / 255.0


# ------------------------------------------------------------------ frame
def render_frame(f, p, r):
    global SKY
    if SKY is None: SKY = sky_base()
    cam = Camera(f['camera']['pos'], f['camera']['target'], f['camera']['fov'])
    img = Image.fromarray(SKY.copy())
    pt = Painter(img)
    w = World(cam, f, pt)
    draw_world(w, f)
    draw_porch(w, f)
    draw_house(w, f)
    sk = person_skeleton(f)
    spill, contact = spill_and_shadows(img, cam, f, p, sk)
    # apply spill (warm, onto the porch floor only: masked by the floor's screen region implicitly via the polygon)
    arr = np.asarray(img, float)
    sp = np.asarray(Image.fromarray((spill * 255).astype(np.uint8)).resize((WW, HH), Image.BILINEAR), float)[..., None] / 255.0
    ct = np.asarray(Image.fromarray((contact * 255).astype(np.uint8)).resize((WW, HH), Image.BILINEAR), float)[..., None] / 255.0
    arr = arr * (1 - 0.55 * ct) + sp * np.array([150, 96, 46.0]) * 0.95
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    pt = Painter(img)
    parts = dog_parts(cam, f, p, r)
    pparts, _ = person_parts(cam, f)
    allp = [(d, fn) for d, fn in parts] + [(d, fn) for d, fn in pparts]
    allp.sort(key=lambda x: -x[0])
    for d, fn in allp: fn(pt)
    small = img.reduce(SS)
    a = np.asarray(small, float)
    # bloom around the brightest light (door light and lamp)
    lum = a.mean(2)
    br = np.clip(lum - 150, 0, 255)[..., None] * (a / (lum[..., None] + 1))
    bl = np.asarray(Image.fromarray(np.clip(br, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(18)), float)
    a = a + 0.55 * bl
    # vignette and grain
    a = a * VIG[..., None]
    rng = np.random.default_rng(1000 + f['i'])
    a = a + rng.normal(0, 3.2, (H, W, 1))
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def main():
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument('s0', nargs='?', type=int, default=0); ap.add_argument('s1', nargs='?', type=int, default=768)
    ap.add_argument('--stride', type=int, default=1); ap.add_argument('--out', default=os.path.join(CACHE, 'frames'))
    ap.add_argument('--frames', default='')
    a = ap.parse_args()
    rig = json.load(open(os.path.join(CACHE, 'rig.json')))
    pose = json.load(open(os.path.join(CACHE, 'pose.json')))
    reg = json.load(open(os.path.join(CACHE, 'registration.json')))
    os.makedirs(a.out, exist_ok=True)
    idx = [int(x) for x in a.frames.split(',')] if a.frames else range(a.s0, min(a.s1, len(rig)), a.stride)
    for i in idx:
        im = render_frame(rig[i], pose[i], reg[i])
        im.save(os.path.join(a.out, f's{i:04d}.jpg'), quality=93)


if __name__ == '__main__':
    main()

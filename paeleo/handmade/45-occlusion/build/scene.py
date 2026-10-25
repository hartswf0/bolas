"""SCION 45 · Occlusion Compositing — who is in front? The threshold scene, one frame at a time.

Coordinates (world, metres): x along the porch (score x; the doorway is x in [-0.46, 0.46]), D = depth in front of the
house wall (toward the camera; inside the house is D < 0), h = height. Time base: score frame i at 24 fps.
Projection: cabinet-oblique stage camera  X = 640 + (x - fx) s ;  Y = 360 + (K D - h + fh) s ,  K = 0.38.
Each element is an RGBA layer (premultiplied) with a depth (scalar, or a per-pixel depth pass). The frame is composited in
the topological order of an occlusion DAG built from overlaps; where one object is both behind and in front of another
(the dog lying across the jamb, the person's arm through the door frame) it is split into semantic sublayers by its own
depth pass, never forced into one global z. A render verifier re-composites by per-pixel depth test and compares.
Version: scene-v9
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dog as DOG
import person as PERSON

W, H = 1280, 720
K = 0.38
FPS = 24
SCORE = DOG.SCORE
FR = SCORE['frames']
PL = os.path.join(HERE, 'cache/plates')
OPEN_X = 0.46            # half-width of the opening
FRAME_W = 0.12           # casing width
FRAME_D = 0.005          # casing face depth (flush trim): the plane the dog and the person are split at
DOOR_H = 2.03
LAMP = (-0.12, 1.02, -1.05)
POST_X, POST_D, POST_W = 2.32, 2.30, 0.13
CORNER_X = 2.05
BENCH = (-1.55, -0.62, 0.22, 0.58, 0.44)   # x0, x1, D0, D1, seat h

_img = {}


def plate(n):
    if n not in _img:
        _img[n] = Image.open(os.path.join(PL, n + '.png')).convert('RGBA')
    return _img[n]


def sm(a, b, t):
    t = min(1, max(0, (t - a) / (b - a)))
    return t * t * (3 - 2 * t)


def lerp(a, b, u):
    return a + (b - a) * u


# ------------------------------------------------------------------ camera
CAM_KEYS = [  # t, px/m, focus x, focus h: the caller and the dog in one frame for the commands; the bench comes in for the
    # changed circumstances; a small push for the turn back (the lit door stays in frame); then the approach and the sill
    (0.0, 250, 1.95, 0.52), (4.7, 250, 1.95, 0.52), (5.9, 220, 1.58, 0.50), (7.0, 220, 1.58, 0.50),
    (7.6, 245, 2.00, 0.50), (9.4, 245, 2.00, 0.50), (11.0, 220, 1.58, 0.50), (15.0, 220, 1.58, 0.50),
    (24.0, 262, 0.40, 0.53), (24.4, 290, 0.32, 0.55), (31.8, 370, 0.14, 0.58), (40.0, 370, 0.14, 0.58)]


def camera(t):
    for (t0, s0, x0, h0), (t1, s1, x1, h1) in zip(CAM_KEYS[:-1], CAM_KEYS[1:]):
        if t0 <= t <= t1:
            u = sm(t0, t1, t)
            return dict(s=lerp(s0, s1, u), fx=lerp(x0, x1, u), fh=lerp(h0, h1, u))
    return dict(s=CAM_KEYS[-1][1], fx=CAM_KEYS[-1][2], fh=CAM_KEYS[-1][3])


class Cam:
    def __init__(self, c):
        self.s, self.fx, self.fh = c['s'], c['fx'], c['fh']

    def X(self, x):
        return 640 + (x - self.fx) * self.s

    def Y(self, h, D):
        return 360 + (K * D - h + self.fh) * self.s

    def P(self, x, h, D):
        return (self.X(x), self.Y(h, D))

    def floor_world(self, Xs, Ys, h=0.0):
        x = self.fx + (Xs - 640) / self.s
        D = ((Ys - 360) / self.s - self.fh + h) / K
        return x, D

    def wall_world(self, Xs, Ys, D=0.0):
        x = self.fx + (Xs - 640) / self.s
        h = K * D + self.fh - (Ys - 360) / self.s
        return x, h


YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)


def hashn(a):
    return (np.sin(a * 12.9898 + 78.233) * 43758.5453) % 1.0


class Layer:
    def __init__(self, name, rgb, a, depth, kind, src=''):
        self.name, self.rgb, self.a, self.depth, self.kind, self.src = name, rgb.astype(np.float32, copy=False), a.astype(np.float32, copy=False), depth, kind, src
        rows = np.nonzero(a.max(1) > 0.002)[0]; cols = np.nonzero(a.max(0) > 0.002)[0]
        self.bb = (int(rows[0]), int(rows[-1]) + 1, int(cols[0]), int(cols[-1]) + 1) if len(rows) else (0, 0, 0, 0)

    def dz(self):
        return self.depth if np.isscalar(self.depth) else None


def from_pil(im):
    a = np.asarray(im).astype(np.float32) / 255
    al = a[:, :, 3]
    return a[:, :, :3] * al[..., None], al


def poly_alpha(polys, ss=2):
    """Antialiased polygon matte, rasterised only inside the polygons' bounding box."""
    xs = [x for p in polys for x, y in p]; ys = [y for p in polys for x, y in p]
    x0, x1 = max(0, int(math.floor(min(xs))) - 2), min(W, int(math.ceil(max(xs))) + 2)
    y0, y1 = max(0, int(math.floor(min(ys))) - 2), min(H, int(math.ceil(max(ys))) + 2)
    out = np.zeros((H, W), np.float32)
    if x1 <= x0 or y1 <= y0:
        return out
    m = Image.new('L', ((x1 - x0) * ss, (y1 - y0) * ss), 0)
    d = ImageDraw.Draw(m)
    for p in polys:
        d.polygon([((x - x0) * ss, (y - y0) * ss) for x, y in p], fill=255)
    if ss > 1:
        m = m.resize((x1 - x0, y1 - y0), Image.BOX)
    out[y0:y1, x0:x1] = np.asarray(m).astype(np.float32) / 255
    return out


def perspective_coeffs(dst, src):
    """PIL PERSPECTIVE coefficients mapping output points dst[i] -> input points src[i]."""
    A, B = [], []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()


def warp_to_quad(img, quad):
    """quad: screen corners for img's TL, TR, BR, BL."""
    w, h = img.size
    c = perspective_coeffs(quad, [(0, 0), (w, 0), (w, h), (0, h)])
    return img.transform((W, H), Image.PERSPECTIVE, c, resample=Image.BICUBIC)


def ambient(t):
    """Dusk deepens across the 32 s: exterior ambient colour."""
    u = t / 32.0
    return np.array([lerp(0.50, 0.36, u), lerp(0.53, 0.39, u), lerp(0.66, 0.52, u)], np.float32)


WARM = np.array([1.0, 0.70, 0.40], np.float32)


# ------------------------------------------------------------------ door state from the score
def door_angle(t):
    """degrees the leaf has swung in (hinge at the right jamb). Ajar 9 deg; the push at 6.1-6.3, swings to 76 by 7.0."""
    return lerp(9, 76, sm(6.15, 7.0, t))


HINGE_D = -0.16          # the leaf hangs at the inner face of the wall and swings into the room


def leaf_edge(th):
    r = math.radians(th)
    return OPEN_X - 2 * OPEN_X * math.cos(r), HINGE_D - 2 * OPEN_X * math.sin(r)


def light_through(th, n=240):
    """Fraction of the opening (sampled across x0 in [-0.46, 0.46] at D=0) that the lamp sees past the leaf (plan view)."""
    xs = np.linspace(-OPEN_X, OPEN_X, n)
    lx, _, lD = LAMP
    hx, hD = OPEN_X, HINGE_D
    fxe, fDe = leaf_edge(th)
    lit = np.ones(n)
    for k, x0 in enumerate(xs):
        # segment lamp->(x0,0) vs leaf (hx,hD)-(fxe,fDe)
        p, r = np.array([lx, lD]), np.array([x0 - lx, 0 - lD])
        q, sv = np.array([hx, hD]), np.array([fxe - hx, fDe - hD])
        den = r[0] * sv[1] - r[1] * sv[0]
        if abs(den) < 1e-9:
            continue
        qp = q - p
        tt = (qp[0] * sv[1] - qp[1] * sv[0]) / den
        uu = (qp[0] * r[1] - qp[1] * r[0]) / den
        if 0 < tt < 0.999 and 0 <= uu <= 1:
            lit[k] = 0
    return xs, lit


# ------------------------------------------------------------------ layers
def L_sky(cam, t):
    sky = plate('sky').convert('RGB')
    par = (cam.fx - 1.5) * 25
    big = sky.resize((1500, int(1500 * sky.size[1] / sky.size[0])), Image.BICUBIC)
    canvas = Image.new('RGB', (W, H), tuple(int(c * 255) for c in (0.13, 0.13, 0.22)))
    canvas.paste(big, (int(-110 - par), -60))
    rgb = np.asarray(canvas).astype(np.float32) / 255
    dim = lerp(1.0, 0.72, t / 32)
    rgb = rgb * dim
    # horizon: a far tree line (drawn), then the dark yard rising to the porch edge
    hz = 330 + (cam.s - 224) * 0.6 + (cam.fh - 0.5) * 300
    xs1 = np.arange(W, dtype=np.float32)
    n = (np.sin(xs1 * 0.021 + 1.3) * 9 + np.sin(xs1 * 0.057) * 6 + np.sin(xs1 * 0.13 + 2) * 3 + (hashn(np.floor(xs1 / 7)) - .5) * 10)
    tree = (YY > (hz - 30 - n)[None, :]).astype(np.float32)
    yard = np.clip((YY - hz) / 200, 0, 1)
    col_tree = np.array([0.07, 0.08, 0.11], np.float32); col_yard = np.array([0.10, 0.11, 0.12], np.float32)
    rgb = rgb * (1 - tree[..., None]) + tree[..., None] * (col_tree * (1 - yard[..., None]) + col_yard * yard[..., None])
    return Layer('sky', rgb.astype(np.float32), np.ones((H, W), np.float32), -100.0, 'sky', 'Top Of The Cloud f030 (graded)')


def L_interior(cam, t):
    """The hallway seen through the doorway: back wall plate at D=-1.5, warm wooden floor from D=-1.5 to 0, the bulb.
    Computed only inside the opening's screen box (the facade holds out everything else)."""
    x0 = int(max(0, cam.X(-OPEN_X - 0.05))); x1 = int(min(W, cam.X(OPEN_X + 0.05)))
    y0 = int(max(0, cam.Y(DOOR_H + 0.1, 0))); y1 = int(min(H, cam.Y(-0.02, 0.0) + 2))
    rgbF = np.zeros((H, W, 3), np.float32); aF = np.zeros((H, W), np.float32); depthF = np.full((H, W), -1.5, np.float32)
    if x1 <= x0 or y1 <= y0:
        return Layer('interior', rgbF, aF, depthF, 'back', '')
    YYc, XXc = YY[y0:y1, x0:x1], XX[y0:y1, x0:x1]
    h_, w_ = YYc.shape
    rgb = np.zeros((h_, w_, 3), np.float32); a = np.zeros((h_, w_), np.float32)
    xw, Dw = cam.floor_world(XXc, YYc)
    flo = (Dw < 0.0) & (Dw > -1.5)
    plank = np.floor(xw / 0.13)
    tone = 0.62 + 0.10 * hashn(plank)
    gap = (np.abs((xw / 0.13) % 1.0 - 0.5) > 0.46)
    fl = np.where(gap, tone * 0.6, tone)
    rgb[flo] = (fl[flo, None] * np.array([0.98, 0.74, 0.48], np.float32))
    a[flo] = 1
    wall = plate('interior').crop((0, 0, 372, 288)).convert('RGBA')
    quad = [cam.P(-1.25, 2.05, -1.5), cam.P(1.25, 2.05, -1.5), cam.P(1.25, -0.15, -1.5), cam.P(-1.25, -0.15, -1.5)]
    wr, wa = from_pil(warp_to_quad(wall, quad))
    wr, wa = wr[y0:y1, x0:x1], wa[y0:y1, x0:x1]
    keep = 1 - a
    rgb = rgb + wr * 0.95 * keep[..., None]; a = a + wa * keep
    bx, bh, bD = LAMP
    shelf = [cam.P(bx - 0.28, bh - 0.12, bD), cam.P(bx + 0.28, bh - 0.12, bD), cam.P(bx + 0.28, bh - 0.16, bD), cam.P(bx - 0.28, bh - 0.16, bD)]
    sa = poly_alpha([shelf])[y0:y1, x0:x1]
    rgb = rgb * (1 - sa[..., None]) + sa[..., None] * np.array([0.30, 0.18, 0.10], np.float32); a = np.maximum(a, sa)
    bulb = plate('bulb')
    bw = 0.10 * cam.s; bhp = bw * bulb.size[1] / bulb.size[0]
    X0, Y0 = cam.P(bx, bh - 0.12, bD)
    bl = bulb.resize((max(2, int(bw)), max(2, int(bhp))), Image.LANCZOS)
    can = Image.new('RGBA', (W, H), (0, 0, 0, 0)); can.paste(bl, (int(X0 - bw / 2), int(Y0 - bhp)), bl)
    br, ba = from_pil(can)
    br, ba = br[y0:y1, x0:x1], ba[y0:y1, x0:x1]
    rgb = rgb * (1 - ba[..., None]) + br * 1.1; a = np.maximum(a, ba)
    gx, gy = cam.P(bx, bh + 0.06, bD)
    r2 = ((XXc - gx) ** 2 + (YYc - gy) ** 2) / (0.9 * cam.s) ** 2
    glow = np.exp(-r2 * 2.2)[..., None] * WARM * 0.55
    rgb = np.clip(rgb * (0.55 + 0.9 * np.exp(-r2 * 0.8))[..., None] + glow * a[..., None], 0, 1.2)
    rgbF[y0:y1, x0:x1] = rgb * a[..., None] if False else rgb
    aF[y0:y1, x0:x1] = a
    depthF[y0:y1, x0:x1] = np.where(flo, Dw, -1.5)
    return Layer('interior', rgbF, aF, depthF, 'back', 'Straight Talk f029 hallway + Light Of Your Life B f012 bulb + drawn floor/shelf')


def L_leaf(cam, t, amb):
    th = door_angle(t)
    xe, De = leaf_edge(th)
    leaf = plate('leaf')
    quad = [cam.P(xe, DOOR_H, De), cam.P(OPEN_X, DOOR_H, HINGE_D), cam.P(OPEN_X, 0, HINGE_D), cam.P(xe, 0, De)]
    im = warp_to_quad(leaf, quad)
    rgb, a = from_pil(im)
    shade = 0.30 + 0.55 * math.cos(math.radians(th)) ** 1.5
    rgb = rgb * shade * (amb / amb.max()) + rgb * (WARM * 0.30 * sm(6.3, 7.0, t))
    # depth pass along the leaf
    xw = cam.fx + (XX - 640) / cam.s
    u = np.clip((OPEN_X - xw) / max(1e-3, OPEN_X - xe), 0, 1)
    depth = (HINGE_D + u * (De - HINGE_D)).astype(np.float32)
    return Layer('door_leaf', rgb.astype(np.float32), a, depth, 'wall', 'Straight Talk f016 door panel (SAM, rectified)'), th


def L_facade(cam, t, amb, light_amt):
    xw, hw = cam.wall_world(XX, YY, 0.0)
    inside = (xw < CORNER_X) & (hw > -0.02) & (hw < 3.4)
    hole = (np.abs(xw) < OPEN_X) & (hw < DOOR_H) & (hw > -0.05)
    a = (inside & ~hole).astype(np.float32)
    # clapboards
    b = hw / 0.165
    fr = b % 1.0
    lap = np.clip(1 - fr / 0.10, 0, 1)
    tone = 0.62 + 0.06 * hashn(np.floor(b)) + 0.03 * np.sin(xw * 3.1 + np.floor(b) * 1.7)
    base = np.array([0.55, 0.60, 0.66], np.float32)
    col = (tone * (1 - 0.45 * lap))[..., None] * base * amb * 1.25
    # corner board
    cb = (xw > CORNER_X - 0.12)
    col[cb] = np.array([0.72, 0.73, 0.75], np.float32) * amb * 1.2
    # door light bloom on the wall face next to the frame (light scattered from the open door)
    gx = np.exp(-((np.abs(xw) - OPEN_X) / 0.5).clip(0) ** 2) * np.exp(-((hw - 0.8) / 1.3) ** 2)
    col = col + (gx * light_amt * 0.10)[..., None] * WARM
    rgb = col.astype(np.float32) * a[..., None]
    return Layer('facade', rgb, a, FRAME_D, 'wall', 'drawn clapboard wall; the opening is its holdout')


def L_frame(cam, t, amb, light_amt):
    x0, x1 = OPEN_X, OPEN_X + FRAME_W
    polys = {
        'jamb_L': [cam.P(-x1, 0, FRAME_D), cam.P(-x0, 0, FRAME_D), cam.P(-x0, DOOR_H + 0.15, FRAME_D), cam.P(-x1, DOOR_H + 0.15, FRAME_D)],
        'jamb_R': [cam.P(x0, 0, FRAME_D), cam.P(x1, 0, FRAME_D), cam.P(x1, DOOR_H + 0.15, FRAME_D), cam.P(x0, DOOR_H + 0.15, FRAME_D)],
        'lintel': [cam.P(-x1 - 0.03, DOOR_H, FRAME_D), cam.P(x1 + 0.03, DOOR_H, FRAME_D), cam.P(x1 + 0.03, DOOR_H + 0.17, FRAME_D), cam.P(-x1 - 0.03, DOOR_H + 0.17, FRAME_D)],
    }
    out = []
    for n, p in polys.items():
        a = poly_alpha([p])
        xw = cam.fx + (XX - 640) / cam.s
        # paint: white trim at dusk; the inner edge catches the doorway light once it is open
        col = np.array([0.80, 0.80, 0.80], np.float32) * amb * 1.15
        rgb = np.broadcast_to(col, (H, W, 3)).astype(np.float32).copy()
        if n != 'lintel':
            edge = np.clip(1 - np.abs(np.abs(xw) - OPEN_X) / 0.035, 0, 1)
            rgb += (edge * light_amt * 0.35)[..., None] * WARM
            rgb *= (0.92 + 0.08 * np.sin((xw - (x0 if n == 'jamb_R' else -x1)) / FRAME_W * math.pi))[..., None]
        out.append(Layer(n, (rgb * a[..., None]).astype(np.float32), a, FRAME_D, 'frame', 'drawn door casing'))
    return out


def L_sill(cam, t, amb, light_amt):
    x0 = OPEN_X + 0.04
    top = [cam.P(-x0, 0.045, -0.16), cam.P(x0, 0.045, -0.16), cam.P(x0, 0.045, 0.10), cam.P(-x0, 0.045, 0.10)]
    face = [cam.P(-x0, 0.045, 0.10), cam.P(x0, 0.045, 0.10), cam.P(x0, 0, 0.10), cam.P(-x0, 0, 0.10)]
    at = poly_alpha([top]); af = poly_alpha([face])
    col_t = np.array([0.56, 0.47, 0.38], np.float32) * amb * 1.1 + WARM * 0.45 * light_amt
    col_f = np.array([0.40, 0.33, 0.27], np.float32) * amb
    rgb = at[..., None] * col_t + af[..., None] * col_f * (1 - at[..., None])
    a = np.maximum(at, af)
    _, Dw = cam.floor_world(XX, YY, 0.045)
    depth = np.clip(Dw, -0.16, 0.10).astype(np.float32)
    return Layer('sill', rgb.astype(np.float32), a, depth, 'support', 'drawn oak sill')


def L_floor(cam, t, amb):
    xw, Dw = cam.floor_world(XX, YY)
    on = (Dw >= 0) & (xw < 4.9) & (xw > -4)
    plank = np.floor(Dw / 0.115)
    fr = (Dw / 0.115) % 1.0
    gap = np.clip(1 - fr / 0.07, 0, 1)
    tone = 0.50 + 0.10 * hashn(plank) + 0.04 * np.sin(xw * (7 + 3 * hashn(plank + 3)) + plank)
    butt = (np.abs(((xw + hashn(plank) * 2.4) / 2.4) % 1.0) < 0.004)
    tone = tone * (1 - 0.55 * gap) * (1 - 0.5 * butt)
    base = np.array([0.62, 0.55, 0.48], np.float32)
    col = tone[..., None] * base * amb * 1.2
    a = on.astype(np.float32)
    # porch edge beyond x=4.9: the steps go down into the dark
    return xw, Dw, col.astype(np.float32), a


def spill_map(cam, xw, Dw, th, occluders):
    """Light pass: doorway light on the porch floor (D>=0), with the leaf as a holdout and actors' cast shadows."""
    lx, lh, lD = LAMP
    xs, lit = light_through(th)
    f = (0 - lD) / np.maximum(Dw - lD, 1e-3)
    x0 = lx + f * (xw - lx)
    L = np.interp(x0, xs, lit, left=0, right=0)
    L = L * ((Dw >= -0.17) & (np.abs(x0) <= OPEN_X)).astype(np.float32)
    dist = np.sqrt((xw - lx) ** 2 + (Dw - lD) ** 2 + lh ** 2)
    L = L * (1.6 / (1 + (dist / 1.6) ** 2))
    for (alpha, Dc) in occluders:
        if alpha is None:
            continue
        ff = (Dc - lD) / np.maximum(Dw - lD, 1e-3)
        qx = lx + ff * (xw - lx); qh = lh * (1 - ff)
        QX = cam.X(qx); QY = cam.Y(qh, Dc)
        ok = (Dw > Dc + 0.02) & (QX >= 0) & (QX < W - 1) & (QY >= 0) & (QY < H - 1)
        sx = np.clip(QX, 0, W - 1).astype(np.int32); sy = np.clip(QY, 0, H - 1).astype(np.int32)
        occ = alpha[sy, sx] * ok
        L = L * (1 - 0.92 * occ)
    return L.astype(np.float32)


def blur(a, r):
    im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(r))).astype(np.float32) / 255


def contact_shadow(alpha, s, band=0.05):
    """Contact-shadow pass: the lowest band of an actor's alpha, flattened onto its support and blurred."""
    if alpha.max() < 0.05:
        return np.zeros_like(alpha)
    col_has = alpha.max(0) > 0.3
    ys = np.where(alpha > 0.3, YY, -1).max(0)
    bot = np.where(col_has, ys, -1)
    m = ((YY > bot[None, :] - band * s) & (YY <= bot[None, :] + 0.02 * s) & col_has[None, :]).astype(np.float32)
    m = m * np.clip(alpha + 0.6, 0, 1)
    sh = blur(m, max(1.5, 0.02 * s))
    return np.clip(sh * 1.4, 0, 1)


# ------------------------------------------------------------------ actors
def L_post(cam, t, amb):
    x0, x1 = POST_X - POST_W / 2, POST_X + POST_W / 2
    p = [cam.P(x0, 0, POST_D), cam.P(x1, 0, POST_D), cam.P(x1, 4.5, POST_D), cam.P(x0, 4.5, POST_D)]
    a = poly_alpha([p])
    xw = cam.fx + (XX - 640) / cam.s
    u = np.clip((xw - x0) / POST_W, 0, 1)
    shade = 0.55 + 0.45 * np.clip(np.sin(u * math.pi), 0, 1) ** 0.7
    col = shade[..., None] * np.array([0.70, 0.71, 0.73], np.float32) * amb * 1.05
    # base block
    return Layer('porch_post', (col * a[..., None]).astype(np.float32), a, POST_D, 'prop', 'drawn porch post')


def L_bench(cam, t, amb):
    x0, x1, D0, D1, hs = BENCH
    seat = [cam.P(x0, hs, D0), cam.P(x1, hs, D0), cam.P(x1, hs, D1), cam.P(x0, hs, D1)]
    apron = [cam.P(x0, hs, D1), cam.P(x1, hs, D1), cam.P(x1, hs - 0.07, D1), cam.P(x0, hs - 0.07, D1)]
    legs = []
    for lx in (x0 + 0.05, x1 - 0.09):
        legs.append([cam.P(lx, hs - 0.07, D1), cam.P(lx + 0.05, hs - 0.07, D1), cam.P(lx + 0.05, 0, D1), cam.P(lx, 0, D1)])
    a1 = poly_alpha([seat]); a2 = poly_alpha([apron]); a3 = poly_alpha(legs)
    c1 = np.array([0.36, 0.28, 0.22], np.float32) * amb * 1.3; c2 = np.array([0.24, 0.19, 0.15], np.float32) * amb * 1.2
    rgb = a1[..., None] * c1
    rgb = rgb * (1 - a2[..., None]) + a2[..., None] * c2
    rgb = rgb * (1 - a3[..., None]) + a3[..., None] * c2 * 0.9
    a = np.clip(a1 + a2 + a3, 0, 1)
    return Layer('bench', rgb.astype(np.float32), a, D1, 'prop', 'drawn bench')


def person_layers(cam, t, f, amb, light_amt, th):
    rx, rD, Jl, flags = PERSON.pose_at(t, f)
    if flags.get('hand') == 'push':
        # the hand finds the leaf's free edge: support, not a gesture in the air
        xe, De = leaf_edge(th)
        Jl = dict(Jl, wn=(xe + 0.06 - rx, 0.95))
    Jw = {k: (rx + v[0], v[1]) for k, v in Jl.items()}
    ss = 2
    Dbody = rD
    jx = [v[0] for v in Jw.values()]; jh = [v[1] for v in Jw.values()]
    bx0 = int(max(0, cam.X(min(jx) - 0.3))); bx1 = int(min(W, cam.X(max(jx) + 0.3)))
    by0 = int(max(0, cam.Y(max(jh) + 0.3, Dbody))); by1 = int(min(H, cam.Y(-0.05, Dbody) + 4))
    al = {k: np.zeros((H, W), np.float32) for k in ('far', 'near', 'arm')}
    if bx1 > bx0 and by1 > by0:
        ims = {k: Image.new('L', ((bx1 - bx0) * ss, (by1 - by0) * ss), 0) for k in ('far', 'near', 'arm')}
        drs = {k: ImageDraw.Draw(v) for k, v in ims.items()}
        to_screen = lambda x, h: ((cam.X(x) - bx0) * ss, (cam.Y(h, Dbody) - by0) * ss)
        PERSON.draw(Jw, to_screen, cam.s * ss, drs['far'], drs['near'], drs['arm'])
        for k, v in ims.items():
            al[k][by0:by1, bx0:bx1] = np.asarray(v.resize((bx1 - bx0, by1 - by0), Image.BOX)).astype(np.float32) / 255
    a = np.clip(al['far'] + al['near'] + al['arm'], 0, 1)
    farness = np.clip(al['far'] - al['near'] - al['arm'], 0, 1)
    base = np.array([0.075, 0.08, 0.11], np.float32) * (0.6 + 0.4 * amb / amb.max())
    rgb = np.broadcast_to(base, (H, W, 3)).astype(np.float32) * (1 - 0.35 * farness[..., None])
    # rim pass: the edge of the matte facing the doorway light (and the dusk sky on the right)
    sh = np.roll(a, -3, axis=1) if rx < -0.5 else np.roll(a, 3, axis=1)
    rim = np.clip(a - sh, 0, 1)
    rgb = rgb + rim[..., None] * (WARM * 0.45 * (0.25 + light_amt) if t > 5 else np.array([0.25, 0.28, 0.38], np.float32))
    # the found hand at the wrist (reach and low): real skin in the light
    hand = flags.get('hand')
    handA = np.zeros((H, W), np.float32)
    if hand in ('reach', 'low'):
        hp = plate('hand').transpose(Image.FLIP_LEFT_RIGHT)   # fingers toward the dog
        wx, wh = Jw['wn']
        L = 0.40 * cam.s / hp.size[0] * 1.0
        hs = hp.resize((max(2, int(hp.size[0] * L)), max(2, int(hp.size[1] * L))), Image.LANCZOS)
        ang = -12 if hand == 'reach' else 8
        hs = hs.rotate(ang, resample=Image.BICUBIC, expand=True)
        can = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        HX, HY = cam.X(wx), cam.Y(wh, Dbody)
        # the wrist sits ~47% along the cut (forearm on the left after the flip)
        can.paste(hs, (int(HX - hs.size[0] * 0.47), int(HY - hs.size[1] * 0.55)), hs)
        hr, ha = from_pil(can)
        lum = hr.mean(-1, keepdims=True)
        warmth = 0.35 + 1.1 * light_amt if hand == 'low' else 0.45
        hr = lum * (WARM * warmth + amb * 0.5)
        rgb = rgb * (1 - ha[..., None]) + hr
        a = np.maximum(a, ha); handA = ha
    # depth pass: the body at its depth; the near arm reaches toward the camera/dog along its length
    xw = cam.fx + (XX - 640) / cam.s
    shx = Jw['sh'][0]
    armmask = np.clip(al['arm'] + handA, 0, 1)
    depth = np.full((H, W), Dbody, np.float32)
    if hand == 'reach':
        depth = np.where(armmask > 0.02, Dbody + np.clip(xw - shx, 0, None) * 0.9, depth)
    if hand == 'push':
        xe, De = leaf_edge(th)
        span = max(0.05, (xe + 0.06) - shx)
        uleaf = np.clip((OPEN_X - xw) / max(1e-3, OPEN_X - xe), 0, 1)
        depth = np.where(armmask > 0.02, np.where(xw < -OPEN_X - 0.02, 0.30, uleaf * De + 0.03), depth)
    rgbp = (rgb * a[..., None]).astype(np.float32)
    return rgbp, a, depth.astype(np.float32), dict(root=(rx, rD), hand=hand, joints=Jw)


_dog_geom = {}


def dog_geom(cam, i):
    key = (i, cam.s, cam.fx, cam.fh)
    if key in _dog_geom:
        return _dog_geom[key]
    r = DOG.dog_frame(i)
    img = r['img']; ua, va = r['anchor']
    k = cam.s / DOG.P_SRC
    Xa, Ya = cam.X(r['Xc']), cam.Y(0, r['D'])
    sh = r['shear']; cx = 1.0 - 0.6 * sh          # foreshorten when angled into depth
    # forward: x = Xa + k cx (u-ua) ; y = Ya + k (v-va) + sh (x - Xa)
    a11, a12, b1 = k * cx, 0.0, Xa - k * cx * ua
    a21, a22 = sh * k * cx, k
    b2 = Ya - k * va
    det = a11 * a22 - a12 * a21
    ia, ib, ic, id_ = a22 / det, -a12 / det, -a21 / det, a11 / det
    coeffs = (ia, ib, -(ia * b1 + ib * b2), ic, id_, -(ic * b1 + id_ * b2))
    scr = img.transform((W, H), Image.AFFINE, coeffs, resample=Image.BICUBIC)
    rgbs, a = from_pil(scr)
    r['head_a'] = None
    if r.get('head_img') is not None:
        r['head_a'] = from_pil(r['head_img'].transform((W, H), Image.AFFINE, coeffs, resample=Image.BICUBIC))[1]
    _dog_geom.clear(); _dog_geom[key] = (r, rgbs, a, Xa, Ya, k, cx, sh, ua, va)
    return _dog_geom[key]


def dog_layer(cam, i, t, amb, spillL):
    r, rgbs, a, Xa, Ya, k, cx, sh, ua, va = dog_geom(cam, i)
    if spillL is None:
        return None, a, None, dict(D=r['D'])
    # head-only layer for the backlit look-in
    lum = (rgbs.sum(-1) / 3) / np.maximum(a, 1e-4)
    lum = np.clip(lum, 0, 1)
    # light pass: dusk ambient + doorway spill at the dog's own position + rim on the door side
    xw = cam.fx + (XX - 640) / cam.s
    by = int(min(H - 1, max(0, Ya))); bx = int(min(W - 1, max(0, Xa)))
    Ld = float(spillL[max(0, by - 2):by + 3, max(0, bx - 30):bx + 30].mean()) if spillL is not None else 0.0
    inside_light = np.clip((OPEN_X + 0.1 - xw) / 0.5, 0, 1) * (r['D'] < 0.4) * 0.8   # forequarters in the doorway get the room light
    lit = lum[..., None] * (amb * 1.25 + WARM * (0.55 * Ld + inside_light[..., None] * 0.9 * DOOR_OPEN[0]))
    rim_src = np.roll(a, 3, axis=1)   # light from the left (the door)
    rim = np.clip(a - rim_src, 0, 1) * (0.25 + 0.6 * DOOR_OPEN[0])
    lit = lit + rim[..., None] * WARM * 0.5
    if r['head_a'] is not None:
        hm = np.clip(r['head_a'], 0, 1)
        # the back of the head: dusk on it (dim, cool), the lit room behind it wrapping its upper edge
        if r['tone'] == 'back':
            fill = amb * (0.30 + 0.30 * lum[..., None])
            edge = np.clip(hm - np.roll(np.roll(hm, 2, axis=0), 0, axis=1) * 0.5 - np.roll(hm, 2, axis=0) * 0.5, 0, 1)
            side = np.clip(hm - 0.5 * (np.roll(hm, 2, axis=1) + np.roll(hm, -2, axis=1)), 0, 1)
            head_col = fill + WARM * (1.1 * edge + 0.6 * side)[..., None]
        else:
            head_col = lit * 0.55 + WARM * 0.15 * lum[..., None]
        lit = lit * (1 - hm[..., None]) + head_col * hm[..., None]
    rgb = (np.clip(lit, 0, 1.3) * a[..., None]).astype(np.float32)
    # depth pass along the body: the end toward the door is deeper by the angle into the doorway
    slope = sh / K
    xw_c = r['Xc']
    depth = (r['D'] + (xw - xw_c) * slope).astype(np.float32)
    meta = {k2: r[k2] for k2 in ('Xc', 'D', 'shear', 'parts', 'kind', 'facing', 'posture', 'tone', 'state', 'mirror')}
    hx, hy = r['head']
    meta['head_screen'] = (Xa + k * cx * (hx - ua), Ya + k * (hy - va) + sh * (k * cx * (hx - ua)))
    return rgb, a, depth, meta


DOOR_OPEN = [0.0]
_set_cache = {}


# ------------------------------------------------------------------ the occlusion DAG
def overlap(A, B):
    y0, y1 = max(A.bb[0], B.bb[0]), min(A.bb[1], B.bb[1]); x0, x1 = max(A.bb[2], B.bb[2]), min(A.bb[3], B.bb[3])
    m = np.zeros((H, W), bool)
    if y1 > y0 and x1 > x0:
        m[y0:y1, x0:x1] = (A.a[y0:y1, x0:x1] > 0.02) & (B.a[y0:y1, x0:x1] > 0.02)
    return m


def build_dag(layers):
    """Edges far->near for every overlapping pair, decided from depth (scalar or per-pixel at the overlap)."""
    edges = []
    n = len(layers)
    for p in range(n):
        for q in range(p + 1, n):
            A, B = layers[p], layers[q]
            if A.kind == 'support' or B.kind == 'support':
                pass
            if min(A.bb[1], B.bb[1]) <= max(A.bb[0], B.bb[0]) or min(A.bb[3], B.bb[3]) <= max(A.bb[2], B.bb[2]):
                continue
            m = overlap(A, B)
            cnt = int(m.sum())
            if cnt == 0:
                continue
            dA = A.depth if np.isscalar(A.depth) else A.depth[m]
            dB = B.depth if np.isscalar(B.depth) else B.depth[m]
            diff = np.asarray(dB - dA)
            front_B = float((diff > 1e-4).mean()) if diff.size > 1 else float(diff > 1e-4)
            front_A = float((diff < -1e-4).mean()) if diff.size > 1 else float(diff < -1e-4)
            if A.kind == 'sky' or B.kind == 'sky':
                edges.append((A.name, B.name, cnt, 'ok') if A.kind == 'sky' else (B.name, A.name, cnt, 'ok')); continue
            STAND = ('actor', 'prop', 'frame', 'wall')
            if A.kind == 'back' and B.kind in ('actor', 'prop', 'frame'):
                edges.append((A.name, B.name, cnt, 'room')); continue
            if B.kind == 'back' and A.kind in ('actor', 'prop', 'frame'):
                edges.append((B.name, A.name, cnt, 'room')); continue
            if A.kind == 'support' and B.kind in STAND:
                edges.append((A.name, B.name, cnt, 'support')); continue
            if B.kind == 'support' and A.kind in STAND:
                edges.append((B.name, A.name, cnt, 'support')); continue
            if min(front_A, front_B) > 0.02 and min(front_A, front_B) * cnt > 20:
                edges.append((A.name, B.name, cnt, 'CONFLICT'))
            elif front_B >= front_A:
                edges.append((A.name, B.name, cnt, 'ok'))
            else:
                edges.append((B.name, A.name, cnt, 'ok'))
    return edges


def topo(layers, edges):
    names = [L.name for L in layers]
    indeg = {n: 0 for n in names}; adj = {n: [] for n in names}
    for a, b, c, st in edges:
        if st == 'CONFLICT':
            continue
        adj[a].append(b); indeg[b] += 1
    dz = {L.name: (L.depth if np.isscalar(L.depth) else float(np.median(L.depth[L.a > 0.02])) if (L.a > 0.02).any() else 0) for L in layers}
    ready = sorted([n for n in names if indeg[n] == 0], key=lambda n: dz[n])
    order = []
    while ready:
        n = ready.pop(0); order.append(n)
        for m in adj[n]:
            indeg[m] -= 1
            if indeg[m] == 0:
                ready.append(m); ready.sort(key=lambda k: dz[k])
    acyclic = len(order) == len(names)
    return order, acyclic


def has_cycle_if_merged(layers, edges, group):
    """Would the DAG have a cycle if the sublayers in `group` were one layer? (the reason they are split)"""
    rename = {g: '+'.join(group) for g in group}
    E = set()
    for a, b, c, st in edges:
        a2, b2 = rename.get(a, a), rename.get(b, b)
        if a2 != b2:
            E.add((a2, b2))
    # cycle of length 2 is enough evidence here
    return any((b, a) in E for (a, b) in E)


def split_by_depth(name, rgb, a, depth, plane, kind, src):
    """Semantic sublayers by the object's own depth pass: the part behind `plane` and the part in front."""
    behind = (depth < plane).astype(np.float32)
    return (Layer(name + '_in', rgb * behind[..., None], a * behind, depth, kind, src),
            Layer(name + '_out', rgb * (1 - behind)[..., None], a * (1 - behind), depth, kind, src))


def composite(layers, order):
    by = {L.name: L for L in layers}
    out = np.zeros((H, W, 3), np.float32); A = np.zeros((H, W), np.float32)
    for n in order:
        L = by[n]
        y0, y1, x0, x1 = L.bb
        if y1 <= y0:
            continue
        a = L.a[y0:y1, x0:x1]
        out[y0:y1, x0:x1] = L.rgb[y0:y1, x0:x1] + out[y0:y1, x0:x1] * (1 - a[..., None])
        A[y0:y1, x0:x1] = a + A[y0:y1, x0:x1] * (1 - a)
    return out, A


def zcomposite(layers, step=2):
    """Verifier: per-pixel depth-sorted compositing on a subsampled grid (independent of the DAG)."""
    def zd(L):
        d = np.full(L.a[::step, ::step].shape, L.depth, np.float32) if np.isscalar(L.depth) else L.depth[::step, ::step]
        # horizontal supports sit under whatever stands on them; the room behind the opening sits behind the porch
        if L.kind == 'support':
            d = -50 + 0.01 * d
        if L.kind == 'back':
            d = -60 + 0.01 * d
        return d
    sub = [(L.rgb[::step, ::step], L.a[::step, ::step], zd(L)) for L in layers]
    Dp = np.stack([s[2] for s in sub]); Ap = np.stack([s[1] for s in sub]); Cp = np.stack([s[0] for s in sub])
    # floors are horizontal supports: anything standing on them is in front where they overlap
    order = np.argsort(Dp, axis=0, kind='stable')
    out = np.zeros(Cp.shape[1:], np.float32)
    for k in range(len(layers)):
        idx = order[k]
        a = np.take_along_axis(Ap, idx[None], 0)[0]
        c = np.take_along_axis(Cp, idx[None, ..., None].repeat(3, -1), 0)[0]
        out = c + out * (1 - a[..., None])
    return out


# ------------------------------------------------------------------ one frame
def render(i, verify=False):
    f = FR[i]; t = f['t']
    cam = Cam(camera(t))
    tq = float(round(t))
    amb = ambient(tq)                 # dusk deepens in 1 s steps (0.9% each), so the set can be cached between steps
    th = door_angle(t)
    DOOR_OPEN[0] = sm(6.12, 7.0, t)
    light_amt = 0.15 + 0.85 * DOOR_OPEN[0]
    key = (round(cam.s, 4), round(cam.fx, 5), round(cam.fh, 5), tq, round(th, 3), round(light_amt, 4))
    if _set_cache.get('key') != key:
        st = {}
        st['sky'] = L_sky(cam, tq)
        st['interior'] = L_interior(cam, tq)
        st['leaf'], _ = L_leaf(cam, t, amb)
        st['facade'] = L_facade(cam, t, amb, light_amt)
        st['frame'] = L_frame(cam, t, amb, light_amt)
        st['sill'] = L_sill(cam, t, amb, light_amt)
        st['floor'] = L_floor(cam, t, amb)
        st['post'] = L_post(cam, t, amb)
        st['bench'] = L_bench(cam, t, amb)
        _set_cache.clear(); _set_cache.update(st); _set_cache['key'] = key
    st = _set_cache
    import copy
    layers = [st['sky'], copy.copy(st['interior']), st['leaf'], st['facade']] + list(st['frame']) + [copy.copy(st['sill'])]
    # actors first (their alphas drive the floor's light and shadow passes)
    prgb, pa, pdepth, pmeta = person_layers(cam, t, f, amb, light_amt, th)
    xw, Dw, fcol, fa = st['floor']
    # first dog pass without spill to get its alpha for the cast shadow; then light it
    drgb0, da0, ddepth0, dmeta0 = dog_layer(cam, i, t, amb, None)
    occl = [(pa, float(np.median(pdepth[pa > 0.1])) if (pa > 0.1).any() else 0.0), (da0, dmeta0['D'])]
    L = spill_map(cam, xw, Dw, th, occl)
    drgb, da, ddepth, dmeta = dog_layer(cam, i, t, amb, L)
    # floor: base + light pass + contact shadows (dog, person on the bench, post, bench legs)
    csd = contact_shadow(da, cam.s)
    csp = contact_shadow(pa, cam.s, 0.04) * 0.6
    post_layer = st['post']
    bench_layer = st['bench']
    csb = contact_shadow(post_layer.a, cam.s, 0.03) * 0.5 + contact_shadow(bench_layer.a, cam.s, 0.03) * 0.5
    shade = 1 - np.clip(0.62 * csd + csp + csb, 0, 0.85)
    fl = (fcol * (1 + 0 * L[..., None]) + (L[..., None] * WARM * 0.62) * (fcol / np.maximum(fcol.max(), 1e-3) * 1.6 + 0.15)) * shade[..., None]
    floor = Layer('porch_floor', (fl * fa[..., None]).astype(np.float32), fa, Dw.astype(np.float32), 'support', 'drawn boards + light pass + contact shadows')
    layers.append(floor)
    # the sill also takes the contact shadow of the lying dog
    sill = next(Lr for Lr in layers if Lr.name == 'sill')
    sill.rgb = sill.rgb * (1 - np.clip(0.55 * csd, 0, 0.8))[..., None]
    for Lr in layers:
        if Lr.name == 'interior':
            Lr.rgb = Lr.rgb * (1 - np.clip(0.6 * csd, 0, 0.8))[..., None]
    layers.append(bench_layer)
    # split the person and the dog by their own depth passes against the door frame plane
    pin, pout = split_by_depth('person', prgb, pa, pdepth, FRAME_D, 'actor', 'drawn matte + Door to Heaven hand')
    din, dout = split_by_depth('dog', drgb, da, ddepth, FRAME_D, 'actor', 'Amateur Film New Jersey C cels/parts')
    layers += [pin, pout, din, dout, post_layer]
    layers = [Lr for Lr in layers if Lr.a.max() > 0.004]
    edges = build_dag(layers)
    order, acyclic = topo(layers, edges)
    conflicts = [e for e in edges if e[3] == 'CONFLICT']
    names = [Lr.name for Lr in layers]
    split_needed = {}
    if 'dog_in' in names and 'dog_out' in names:
        split_needed['dog'] = has_cycle_if_merged(layers, edges, ['dog_in', 'dog_out'])
    if 'person_in' in names and 'person_out' in names:
        split_needed['person'] = has_cycle_if_merged(layers, edges, ['person_in', 'person_out'])
    rgb, A = composite(layers, order)
    # alpha validity per layer
    bad_alpha = []
    for Lr in layers:
        if Lr.a.min() < -1e-5 or Lr.a.max() > 1 + 1e-5 or np.isnan(Lr.a).any():
            bad_alpha.append(Lr.name)
        if (Lr.rgb.max(-1) - Lr.a * 1.31 > 1e-3).any():
            bad_alpha.append(Lr.name + ':premult')
    rec = dict(i=i, t=round(t, 4), cam=dict(s=cam.s, fx=cam.fx, fh=cam.fh), order=order, acyclic=acyclic,
               conflicts=[(a, b, c) for a, b, c, _ in conflicts], edges=[(a, b, c) for a, b, c, _ in edges],
               split_needed=split_needed, bad_alpha=bad_alpha, final_alpha_min=float(A.min()), door_deg=th)
    # dog measurements from the render (full dog alpha = before holdouts; visible = after)
    by = {Lr.name: Lr for Lr in layers}
    vis = np.zeros((H, W), np.float32)
    pos = {n: k for k, n in enumerate(order)}
    for dn in ('dog_in', 'dog_out'):
        if dn not in by:
            continue
        cov = by[dn].a.copy()
        for n in order[pos[dn] + 1:]:
            cov = cov * (1 - by[n].a)
        vis += cov
    ys, xs = np.nonzero(da > 0.5)
    if len(xs):
        cxs, cys = float(xs.mean()), float(ys.mean())
        top, bot, left, right = float(ys.min()), float(ys.max()), float(xs.min()), float(xs.max())
    else:
        cxs = cys = top = bot = left = right = None
    hidden = float(da.sum() - vis.sum())
    head_side = None; dark_head = 0
    if len(xs) > 20:
        band = ys < top + 0.35 * (bot - top)
        head_side = float((cxs - xs[band].mean()) / max(1.0, right - left))
        lumf = rgb.mean(-1)
        dark_head = int(((lumf[ys[band], xs[band]] < 0.10) & (vis[ys[band], xs[band]] > 0.5)).sum())
    in_frac = float(din.a.sum() / max(1e-3, da.sum()))
    # who hides the dog: per occluder coverage
    hiders = {}
    for dn in ('dog_in', 'dog_out'):
        if dn not in pos:
            continue
        for n in order[pos[dn] + 1:]:
            if n in ('dog_in', 'dog_out'):
                continue
            ov = float((by[dn].a * by[n].a).sum())
            if ov > 1:
                hiders[n] = round(hiders.get(n, 0) + ov, 1)
    # contact-shadow registration: share of the dog's bottom-contour columns that have shadow just under them
    contact_cov = None
    if len(xs):
        colmax = np.where(da > 0.5, YY, -1).max(0)
        cols = np.nonzero(colmax >= 0)[0]
        yb = np.clip(colmax[cols] + 2, 0, H - 1).astype(int)
        contact_cov = float((csd[yb, cols] > 0.15).mean())
    csx = base_x = None
    rec['dog'] = dict(head_side=head_side, dark_head=dark_head, cx=cxs, cy=cys, top=top, bot=bot, left=left, right=right, area=float(da.sum()), visible=float(vis.sum()),
                      hidden=hidden, in_frac=in_frac, hiders=hiders, shadow_cx=csx, base_cx=base_x, contact_cov=contact_cov,
                      head_screen=dmeta['head_screen'], **{k: dmeta[k] for k in ('Xc', 'D', 'shear', 'parts', 'kind', 'facing', 'posture', 'tone', 'mirror')})
    rec['person'] = dict(root=pmeta['root'], hand=pmeta['hand'])
    rec['light_at_dog'] = float(L[int(min(H - 1, max(0, cam.Y(0, dmeta['D'])))), int(min(W - 1, max(0, cam.X(dmeta['Xc']))))])
    if verify:
        zc = zcomposite(layers, 2)
        dc = rgb[::2, ::2]
        rec['verify_max_diff'] = float(np.abs(zc - dc).max())
        rec['verify_px_over_2pct'] = int((np.abs(zc - dc).max(-1) > 0.02).sum())
    frame = np.clip(rgb, 0, 1)
    return frame, rec, layers


if __name__ == '__main__':
    import time
    i = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    t0 = time.time()
    fr, rec, layers = render(i, verify=True)
    print('render s', round(time.time() - t0, 2))
    Image.fromarray((fr * 255).astype(np.uint8)).save(sys.argv[2] if len(sys.argv) > 2 else '/tmp/f.png')
    print(json.dumps({k: v for k, v in rec.items() if k not in ('edges',)}, default=str)[:2500])

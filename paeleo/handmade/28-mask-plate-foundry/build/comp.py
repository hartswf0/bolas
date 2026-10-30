"""SCION 28 compositor: a small layer compositor in numpy + PIL.

First-class primitives (each is a typed object, not pixels):
  BezierMask   closed path of vertices with automatic (Catmull-Rom) bezier tangents, keyframed vertex lists,
               feather (gaussian px) and expansion (px, dilate/erode), mode add / subtract.
  Track        a keyframed 2-D point (a motion track): measured from footage or keyed to the score.
  Xform        parented 2-D transform: anchor, position, scale, rotation, flip; world = parent.world @ local.
  CornerPin    4 source corners -> 4 destination points (homography), from a camera projection.
  Holdout      a matte (full-frame float array) that removes a layer where something nearer stands in front.
  DiffKey      difference key of a plate against a stabilised clean plate.
  Grade/Grain  per-plate light and grain matching: lift/gain/gamma/tint, measured noise added to a common target.

Coordinates: source plates in their own pixels (origin top-left, y down); the comp is 1280x720, y down.
Time base: scene frame i at 24 fps, t = i/24 s. Images are float32 RGB in 0..1, alpha float32 0..1, premultiplied
during compositing."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 1280, 720


# ---------------------------------------------------------------- matrices
def mT(x, y):
    return np.array([[1, 0, x], [0, 1, y], [0, 0, 1]], float)


def mS(sx, sy=None):
    return np.diag([sx, sx if sy is None else sy, 1.0])


def mR(deg):
    a = np.radians(deg); c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], float)


def apply(M, pts):
    p = np.asarray(pts, float).reshape(-1, 2)
    q = (M @ np.c_[p, np.ones(len(p))].T).T
    return q[:, :2] / q[:, 2:3]


def homography(src, dst):
    """3x3 H with dst ~ H src for 4 point pairs (DLT)."""
    A = []
    for (x, y), (u, v) in zip(src, dst):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y, -u])
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y, -v])
    _, _, Vt = np.linalg.svd(np.array(A, float))
    Hm = Vt[-1].reshape(3, 3)
    return Hm / Hm[2, 2]


# ---------------------------------------------------------------- primitives
class Track:
    """A keyframed 2-D point. keys: {t: (x, y)}; linear between keys, held outside."""
    def __init__(self, keys, name=''):
        self.name = name
        self.t = np.array(sorted(keys), float)
        self.v = np.array([keys[k] for k in sorted(keys)], float)

    def at(self, t):
        return np.array([np.interp(t, self.t, self.v[:, 0]), np.interp(t, self.t, self.v[:, 1])])


class Xform:
    """Parented transform. anchor in source px; pos in parent space; rot in degrees; flip mirrors about the anchor."""
    def __init__(self, anchor=(0, 0), pos=(0, 0), scale=1.0, rot=0.0, flip=False, parent=None, name=''):
        self.anchor, self.pos, self.scale, self.rot, self.flip, self.parent, self.name = anchor, pos, scale, rot, flip, parent, name

    def local(self):
        s = self.scale if np.ndim(self.scale) else (self.scale, self.scale)
        return mT(*self.pos) @ mR(self.rot) @ mS(-s[0] if self.flip else s[0], s[1]) @ mT(-self.anchor[0], -self.anchor[1])

    def world(self):
        return (self.parent.world() if self.parent is not None else np.eye(3)) @ self.local()


def _catmull_bezier(pts, closed=True, n=10):
    """Smooth closed path through vertices: each segment a cubic bezier with Catmull-Rom tangents."""
    P = np.asarray(pts, float); k = len(P); out = []
    for i in range(k if closed else k - 1):
        p0, p1, p2, p3 = P[(i - 1) % k], P[i], P[(i + 1) % k], P[(i + 2) % k]
        c1 = p1 + (p2 - p0) / 6.0; c2 = p2 - (p3 - p1) / 6.0
        for s in np.linspace(0, 1, n, endpoint=False):
            out.append((1 - s) ** 3 * p1 + 3 * (1 - s) ** 2 * s * c1 + 3 * (1 - s) * s ** 2 * c2 + s ** 3 * p2)
    return np.array(out)


class BezierMask:
    """keys: {t: [(x,y), ...]} (same vertex count), feather px, expansion px, mode 'add'|'sub'."""
    def __init__(self, keys, feather=1.5, expand=0.0, mode='add', name=''):
        if not isinstance(keys, dict):
            keys = {0.0: keys}
        self.keys = {float(k): np.asarray(v, float) for k, v in keys.items()}
        self.feather, self.expand, self.mode, self.name = feather, expand, mode, name

    def verts(self, t):
        ts = sorted(self.keys)
        if t <= ts[0]: return self.keys[ts[0]]
        if t >= ts[-1]: return self.keys[ts[-1]]
        j = np.searchsorted(ts, t); a, b = ts[j - 1], ts[j]; u = (t - a) / (b - a)
        u = u * u * (3 - 2 * u)  # eased keyframes
        return (1 - u) * self.keys[a] + u * self.keys[b]

    def raster(self, size, t=0.0, ss=4):
        w, h = size
        path = _catmull_bezier(self.verts(t)) * ss
        im = Image.new('L', (w * ss, h * ss), 0)
        ImageDraw.Draw(im).polygon([tuple(p) for p in path], fill=255)
        im = im.resize((w, h), Image.BOX)
        e = self.expand
        if abs(e) >= 0.5:
            r = int(round(abs(e))) * 2 + 1
            im = im.filter(ImageFilter.MaxFilter(r) if e > 0 else ImageFilter.MinFilter(r))
        if self.feather > 0:
            im = im.filter(ImageFilter.GaussianBlur(self.feather))
        return np.asarray(im, np.float32) / 255.0


def mask_stack(masks, size, t):
    a = np.zeros((size[1], size[0]), np.float32)
    for m in masks:
        r = m.raster(size, t)
        a = np.maximum(a, r) if m.mode == 'add' else a * (1 - r)
    return a


def poly_matte(polys, size, feather=0.0, ss=2):
    w, h = size
    im = Image.new('L', (w * ss, h * ss), 0); d = ImageDraw.Draw(im)
    for p in polys:
        d.polygon([(x * ss, y * ss) for x, y in p], fill=255)
    im = im.resize((w, h), Image.BOX)
    if feather: im = im.filter(ImageFilter.GaussianBlur(feather))
    return np.asarray(im, np.float32) / 255.0


# ---------------------------------------------------------------- sampling
def warp(rgb, alpha, M, out=(W, H), pad=2):
    """Sample a source (rgb HxWx3, alpha HxW) through src->dst matrix M (affine or projective) into the comp.
    Returns (x0, y0, rgb_premult, a) for the destination bbox, or None if off-screen."""
    h, w = alpha.shape
    corners = apply(M, [(0, 0), (w, 0), (w, h), (0, h)])
    x0 = int(max(0, np.floor(corners[:, 0].min()) - pad)); x1 = int(min(out[0], np.ceil(corners[:, 0].max()) + pad))
    y0 = int(max(0, np.floor(corners[:, 1].min()) - pad)); y1 = int(min(out[1], np.ceil(corners[:, 1].max()) + pad))
    if x1 <= x0 or y1 <= y0: return None
    Mi = np.linalg.inv(M)
    xs, ys = np.meshgrid(np.arange(x0, x1) + .5, np.arange(y0, y1) + .5)
    q = Mi @ np.stack([xs.ravel(), ys.ravel(), np.ones(xs.size)])
    u = q[0] / q[2] - .5; v = q[1] / q[2] - .5
    iu = np.floor(u).astype(int); iv = np.floor(v).astype(int); fu = (u - iu).astype(np.float32); fv = (v - iv).astype(np.float32)
    ok = (iu >= -1) & (iu < w) & (iv >= -1) & (iv < h)
    pm = np.dstack([rgb * alpha[..., None], alpha]).astype(np.float32)
    pm = np.pad(pm, ((1, 1), (1, 1), (0, 0)))
    iu1 = np.clip(iu + 1, 0, w + 1); iv1 = np.clip(iv + 1, 0, h + 1); iu2 = np.clip(iu + 2, 0, w + 1); iv2 = np.clip(iv + 2, 0, h + 1)
    s = (pm[iv1, iu1] * ((1 - fu) * (1 - fv))[:, None] + pm[iv1, iu2] * (fu * (1 - fv))[:, None]
         + pm[iv2, iu1] * ((1 - fu) * fv)[:, None] + pm[iv2, iu2] * (fu * fv)[:, None])
    s[~ok] = 0
    s = s.reshape(y1 - y0, x1 - x0, 4)
    return x0, y0, s[..., :3], s[..., 3]


class Comp:
    """A frame buffer with 'over' compositing, holdouts, and per-layer matte capture (isolated matte passes)."""
    def __init__(self, bg):
        self.rgb = bg.astype(np.float32).copy()
        self.mattes = {}

    def over(self, piece, holdout=None, name=None, light=None):
        if piece is None: return
        x0, y0, c, a = piece
        hh, ww = a.shape
        if holdout is not None:
            k = 1 - holdout[y0:y0 + hh, x0:x0 + ww]
            c = c * k[..., None]; a = a * k
        if light is not None:
            c = c * light[y0:y0 + hh, x0:x0 + ww]
        dst = self.rgb[y0:y0 + hh, x0:x0 + ww]
        dst *= (1 - a)[..., None]; dst += c
        if name:
            m = self.mattes.setdefault(name, np.zeros((H, W), np.float32))
            sub = m[y0:y0 + hh, x0:x0 + ww]; np.maximum(sub, a, out=sub)


# ---------------------------------------------------------------- matching
def grade(rgb, lift=0.0, gain=1.0, gamma=1.0, tint=(1, 1, 1), sat=1.0):
    y = rgb @ np.array([.299, .587, .114], np.float32)
    x = y[..., None] + (rgb - y[..., None]) * sat
    x = np.clip(x * gain + lift, 0, None) ** (1.0 / gamma)
    return np.clip(x * np.asarray(tint, np.float32), 0, 1).astype(np.float32)


def match_stats(rgb, alpha, ref_mean, ref_std):
    """Luma mean/std match of a cut plate (inside its alpha) to a reference - the light match."""
    y = rgb @ np.array([.299, .587, .114], np.float32)
    w = alpha > .5
    m, s = float(y[w].mean()), float(y[w].std() + 1e-4)
    g = ref_std / s
    return np.clip((rgb - m) * g + ref_mean, 0, 1).astype(np.float32), dict(src_mean=m, src_std=s, gain=g)


def noise_level(rgb):
    """Grain estimate: std of the high-pass (pixel minus 3x3 box mean) of luma, robust (MAD)."""
    y = rgb @ np.array([.299, .587, .114], np.float32)
    im = Image.fromarray((y * 255).astype(np.uint8))
    b = np.asarray(im.filter(ImageFilter.BoxBlur(1)), np.float32) / 255
    d = (y - b).ravel()
    return float(1.4826 * np.median(np.abs(d - np.median(d))))


def soften(rgb, sigma):
    if sigma <= 0.05: return rgb
    out = np.empty_like(rgb)
    for c in range(3):
        im = Image.fromarray((rgb[..., c] * 255).astype(np.uint8))
        out[..., c] = np.asarray(im.filter(ImageFilter.GaussianBlur(sigma)), np.float32) / 255
    return out


def load(path):
    return np.asarray(Image.open(path).convert('RGB'), np.float32) / 255.0

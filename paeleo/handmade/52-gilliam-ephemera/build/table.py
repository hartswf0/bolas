"""table: the digital rostrum. Pieces lie on the table; each exposure places every piece by a rigid transform
(pin rotation + slide, optionally flopped = a mirrored print). No piece is ever scaled, bent or warped after it is cut:
place() asserts the linear part of every transform is a rotation (|det| = 1)."""
import json, math, os
import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
FOLDER = os.path.dirname(HERE)
PIECES = json.load(open(os.path.join(HERE, 'cache', 'pieces.json')))
_img = {}
_shadow = {}


def img(name):
    if name not in _img:
        _img[name] = Image.open(os.path.join(FOLDER, PIECES[name]['file'])).convert('RGBA')
    return _img[name]


def pin(name, key):
    return PIECES[name]['pins'][key]


class Aff:
    """2x3 affine, screen = A @ [x, y, 1]."""
    def __init__(self, m=None):
        self.m = np.array(m if m is not None else [[1, 0, 0], [0, 1, 0]], float)

    def __matmul__(self, o):
        a = np.vstack([self.m, [0, 0, 1]]); b = np.vstack([o.m, [0, 0, 1]])
        return Aff((a @ b)[:2])

    def apply(self, p):
        return (self.m[0, 0] * p[0] + self.m[0, 1] * p[1] + self.m[0, 2], self.m[1, 0] * p[0] + self.m[1, 1] * p[1] + self.m[1, 2])


def T(x, y): return Aff([[1, 0, x], [0, 1, y]])
def R(deg, about=(0, 0)):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    cx, cy = about
    return T(cx, cy) @ Aff([[c, -s, 0], [s, c, 0]]) @ T(-cx, -cy)
def FLIP(): return Aff([[-1, 0, 0], [0, 1, 0]])


def place(canvas, name, A, shadow=(2.0, 3.0, .38), tint=None, alpha=1.0, record=None):
    """Lay piece `name` on the canvas (RGBA Image) with transform A (puppet-space -> screen).
    Piece image pixel (u,v) is puppet-space (u+ox, v+oy)."""
    det = A.m[0, 0] * A.m[1, 1] - A.m[0, 1] * A.m[1, 0]
    assert abs(abs(det) - 1) < 1e-6, ('non-rigid placement', name, det)
    P = PIECES[name]; im = img(name)
    ox, oy = P['origin']
    full = A @ T(ox, oy)
    W, H = im.size
    corners = [full.apply(c) for c in [(0, 0), (W, 0), (0, H), (W, H)]]
    pad = 8
    x0 = int(math.floor(min(c[0] for c in corners))) - pad; y0 = int(math.floor(min(c[1] for c in corners))) - pad
    x1 = int(math.ceil(max(c[0] for c in corners))) + pad; y1 = int(math.ceil(max(c[1] for c in corners))) + pad
    CW, CH = canvas.size
    if x1 < 0 or y1 < 0 or x0 > CW or y0 > CH:
        return
    # inverse of (T(-x0,-y0) @ full)
    loc = T(-x0, -y0) @ full
    M = np.vstack([loc.m, [0, 0, 1]]); Mi = np.linalg.inv(M)
    data = tuple(Mi[0]) + tuple(Mi[1])
    src = im
    if tint is not None:
        a = np.asarray(im).astype(np.float32)
        a[..., :3] *= np.array(tint, np.float32)
        src = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')
    tile = src.transform((x1 - x0, y1 - y0), Image.AFFINE, data, Image.BICUBIC)
    if alpha < 1:
        t = np.asarray(tile).copy(); t[..., 3] = (t[..., 3] * alpha).astype(np.uint8); tile = Image.fromarray(t, 'RGBA')
    if shadow:
        dx, dy, op = shadow
        sa = tile.getchannel('A').filter(ImageFilter.GaussianBlur(1.6))
        sh = Image.new('RGBA', tile.size, (10, 8, 14, 0)); sh.putalpha(sa.point(lambda v: int(v * op)))
        _comp(canvas, sh, x0 + int(round(dx)), y0 + int(round(dy)))
    _comp(canvas, tile, x0, y0)
    if record is not None:
        record.append((name, x0, y0, tile.getchannel('A')))


def _comp(canvas, tile, x, y):
    CW, CH = canvas.size
    sx0, sy0 = max(0, -x), max(0, -y)
    sx1, sy1 = min(tile.width, CW - x), min(tile.height, CH - y)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    canvas.alpha_composite(tile.crop((sx0, sy0, sx1, sy1)), (x + sx0, y + sy0))

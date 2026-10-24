"""SCION 53 · civic footage performer. Shared helpers: sources, masks, cut-outs, the lying composite.

Every cut-out is made from a real archive frame and its SAM polygon. Nothing here draws a dog.
Coordinates: source pixels (384x288 or 384x256) -> scene pixels via a fixed scale per source.
"""
import json, os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, 'sources')
FONTS = os.path.join(ROOT, '..', '..', '..', 'tools', 'paeleo', 'fonts')

def font(kind, size):
    f = {'display': 'f5.woff2', 'display9': 'f8.woff2', 'mono': 'f14.woff2', 'mono6': 'f20.woff2',
         'serif': 'f27.woff2', 'serifi': 'f34.woff2', 'serif6': 'f41.woff2'}[kind]
    return ImageFont.truetype(os.path.join(FONTS, f), size)

def load_json(*p):
    with open(os.path.join(*p)) as fh:
        return json.load(fh)

def poly_area(P):
    return abs(sum(P[i][0] * P[i - 1][1] - P[i - 1][0] * P[i][1] for i in range(len(P)))) / 2

class Source:
    """One archive shot: frames, SAM masks, camera drift, and its catalogue record."""
    def __init__(self, slug):
        self.slug = slug
        self.dir = os.path.join(SRC, slug)
        self.masks = load_json(self.dir, 'masks.json')
        self.clip = load_json(self.dir, 'clip.json')
        s = load_json(self.dir, 'source.json')
        self.rec = s.get('source', s)
        self.camera = load_json(self.dir, 'camera.json')
        self.n = self.clip['n']
        self._cache = {}

    def frame(self, i):
        if i not in self._cache:
            self._cache[i] = Image.open(os.path.join(self.dir, 'frames', 'f%03d.jpg' % i)).convert('RGB')
        return self._cache[i]

    def polys(self, i):
        return self.masks.get(str(i), [])

    def mask(self, i, which='largest', feather=1.2, erode=0):
        im = self.frame(i)
        m = Image.new('L', im.size, 0)
        d = ImageDraw.Draw(m)
        P = self.polys(i)
        if which == 'largest' and P:
            P = [max(P, key=poly_area)]
        for p in P:
            if len(p) > 2:
                d.polygon([tuple(q) for q in p], fill=255)
        if erode:
            m = m.filter(ImageFilter.MinFilter(2 * erode + 1))
        if feather:
            m = m.filter(ImageFilter.GaussianBlur(feather))
        return m

    def clip_time(self, i):
        """seconds inside the archive clip file (clip.json interval/t0 + i/fps)."""
        fps = self.clip.get('fps', 12)
        t0 = self.clip.get('t0', (self.clip.get('interval') or [0])[0])
        return t0 + i / fps

    def source_time(self, i):
        """seconds inside the original film, where the catalogue gives the clip's offset; None if unknown."""
        off = None
        r = self.rec
        if self.slug == 'dog':
            off = float(r['start_seconds'])            # clip starts at 225.559 s of the film
        else:
            u = r.get('video_url', '')
            base = u.rsplit('/', 1)[-1].split('.')[0]
            if '-' in base and base.split('-')[0].isdigit() and len(base.split('-')[0]) == 10:
                off = int(base.split('-')[0]) / 1000.0  # clip file named by its ms range in the film
        return None if off is None else off + self.clip_time(i)

def tc(sec, fps=24):
    if sec is None:
        return '--:--:--:--'
    h = int(sec // 3600); m = int(sec % 3600 // 60); s = int(sec % 60); f = int(round((sec - int(sec)) * fps)) % fps
    return '%02d:%02d:%02d:%02d' % (h, m, s, f)

def to_grey(im, tone=(1.0, 1.0, 1.0)):
    a = np.asarray(im.convert('RGB')).astype(np.float32)
    L = a[..., 0] * 0.299 + a[..., 1] * 0.587 + a[..., 2] * 0.114
    out = np.stack([L * tone[0], L * tone[1], L * tone[2]], -1)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))

def cutout(src, i, mirror=False, feather=1.2, grey=True, erode=0):
    """RGBA crop of frame i under its SAM mask. Returns (rgba np float32 HxWx4 in 0..1, origin (x0,y0) in source px)."""
    im = src.frame(i)
    if grey:
        im = to_grey(im)
    m = src.mask(i, feather=feather, erode=erode)
    a = np.dstack([np.asarray(im).astype(np.float32) / 255, np.asarray(m).astype(np.float32) / 255])
    if mirror:
        a = a[:, ::-1]
    ys, xs = np.nonzero(a[..., 3] > 0.02)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    pad = 24
    y0 = max(0, y0 - pad); x0 = max(0, x0 - pad); y1 = min(a.shape[0], y1 + pad); x1 = min(a.shape[1], x1 + pad)
    return a[y0:y1, x0:x1].copy(), (x0, y0)

def mirror_pt(p, W=384):
    return (W - 1 - p[0], p[1])

def resample_rows(arr, y0, y1, new_h):
    """take rows y0..y1 of arr and resample to new_h rows (nearest-linear)."""
    seg = arr[y0:y1]
    if new_h <= 0 or seg.shape[0] == 0:
        return arr[0:0]
    idx = np.linspace(0, seg.shape[0] - 1, new_h)
    lo = np.floor(idx).astype(int); hi = np.minimum(lo + 1, seg.shape[0] - 1); w = (idx - lo)[:, None, None]
    return seg[lo] * (1 - w) + seg[hi] * w

def rotate_rgba(arr, angle_deg, center):
    """rotate premultiplied-safe: rotate each channel with PIL bilinear about center (x,y)."""
    im = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), 'RGBA')
    im = im.rotate(angle_deg, resample=Image.BICUBIC, center=center)
    return np.asarray(im).astype(np.float32) / 255

def fold(arr, origin, neck, belly_y, foot_y, lie, head_deg, facing, fore_x=None, fore_legs=None):  # fore_x: y of the muzzle's underside (source px)
    """The lying composite (COMPOSED, not in the footage): the standing cut-out is split at the neck;
    the legs below the belly line are folded (rows compressed) and the body and head lowered by the same amount;
    the head piece pivots at the neck. lie 0..1. head_deg >0 lifts the nose. facing -1 left, +1 right."""
    H, W = arr.shape[:2]
    ox, oy = origin
    nx, ny = neck[0] - ox, neck[1] - oy
    by = int(round(belly_y - oy)); fy = int(round(foot_y - oy))
    by = max(1, min(H - 1, by)); fy = max(by + 1, min(H, fy))
    # head / body separation with a soft seam along x = neck_x
    xs = np.arange(W)[None, :]
    ys_ = np.arange(H)[:, None]
    if facing < 0:
        hw = np.clip((nx - xs) / 6.0 + 0.5, 0, 1)
    else:
        hw = np.clip((xs - nx) / 6.0 + 0.5, 0, 1)
    # the foreleg is not head: nothing below the muzzle belongs to the head piece
    if fore_x is not None:
        below = np.clip((ys_ - (fore_x - oy)) / 4.0, 0, 1)
        hw = hw * (1 - below)
    head = arr.copy(); head[..., 3] *= hw
    body = arr.copy(); body[..., 3] *= (1 - hw)
    # forelegs (COMPOSED): cut out of the body, they swing forward as the dog lies, paws out in front (sphinx lie)
    fore = None
    if fore_legs is not None:
        f0, f1 = fore_legs[0] - ox, fore_legs[1] - ox
        sel = np.clip((xs - f0) / 3.0, 0, 1) * np.clip((f1 - xs) / 3.0, 0, 1) * np.clip((ys_ - by + 2) / 4.0, 0, 1)
        fore = body.copy(); fore[..., 3] *= sel
        body = body.copy(); body[..., 3] *= (1 - sel)
    leg_h = fy - by
    new_leg = max(1, int(round(leg_h * (1 - 0.90 * lie))))
    drop = leg_h - new_leg
    out = np.zeros_like(body)
    # body above belly line, lowered
    out[drop:by + drop] = body[0:by]
    legs = resample_rows(body, by, fy, new_leg)
    legs[..., :3] *= (1 - 0.35 * lie)   # folded legs sit in the body's shadow
    out[by + drop:by + drop + new_leg] = legs
    if fore is not None:
        fd = np.zeros_like(fore)
        fd[drop:] = fore[:H - drop] if drop > 0 else fore
        piv = ((fore_legs[0] + fore_legs[1]) / 2 - ox, by + drop)
        swing = 78 * lie * (1 if facing < 0 else -1)
        fd = rotate_rgba(fd, -swing, piv)
        a_f = fd[..., 3:4]
        o2 = out.copy()
        o2[..., :3] = fd[..., :3] * a_f + out[..., :3] * out[..., 3:4] * (1 - a_f)
        o2[..., 3:4] = a_f + out[..., 3:4] * (1 - a_f)
        o2[..., :3] = np.where(o2[..., 3:4] > 1e-4, o2[..., :3] / np.maximum(o2[..., 3:4], 1e-4), 0)
        out = o2
    # head lowered with the body, then pivoted at the (lowered) neck
    hd = np.zeros_like(head)
    hd[drop:] = head[:H - drop] if drop > 0 else head
    ang = head_deg if facing > 0 else -head_deg
    hd = rotate_rgba(hd, ang, (nx, ny + drop))
    a_h = hd[..., 3:4]
    comp = out.copy()
    comp[..., :3] = hd[..., :3] * a_h + out[..., :3] * out[..., 3:4] * (1 - a_h)
    comp[..., 3:4] = a_h + out[..., 3:4] * (1 - a_h)
    nz = comp[..., 3:4] > 1e-4
    comp[..., :3] = np.where(nz, comp[..., :3] / np.maximum(comp[..., 3:4], 1e-4), 0)
    return comp, drop

def over(base, layer, x, y, opacity=1.0):
    """alpha-composite float RGBA layer (HxWx4, 0..1, straight alpha) onto base float RGB (0..1) at integer x,y."""
    H, W = base.shape[:2]
    h, w = layer.shape[:2]
    x = int(round(x)); y = int(round(y))
    X0, Y0 = max(0, x), max(0, y)
    X1, Y1 = min(W, x + w), min(H, y + h)
    if X1 <= X0 or Y1 <= Y0:
        return None
    L = layer[Y0 - y:Y1 - y, X0 - x:X1 - x]
    a = L[..., 3:4] * opacity
    base[Y0:Y1, X0:X1] = L[..., :3] * a + base[Y0:Y1, X0:X1] * (1 - a)
    return (X0, Y0, X1, Y1, a[..., 0])

def scale_rgba(arr, s):
    h, w = arr.shape[:2]
    im = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), 'RGBA')
    # premultiply to avoid dark fringes
    p = np.asarray(im).astype(np.float32) / 255
    pm = p.copy(); pm[..., :3] *= pm[..., 3:4]
    imp = Image.fromarray((pm * 255).astype(np.uint8), 'RGBA').resize((max(1, int(round(w * s))), max(1, int(round(h * s)))), Image.LANCZOS)
    q = np.asarray(imp).astype(np.float32) / 255
    q[..., :3] = np.where(q[..., 3:4] > 1e-3, q[..., :3] / np.maximum(q[..., 3:4], 1e-3), 0)
    return np.clip(q, 0, 1)

def fold2(arr, origin, neck, chest_belly, hind_belly, hind_x, foot_y, lie, head_deg, facing, muzzle_y, head_flip=False, no_head=False):
    """The lying composite, rebuilt after critic round 1 (COMPOSED, not in the footage).
    Per column: the belly line runs from the chest (at the neck's x) to the hindquarters (hind_x); everything below it
    (legs, thighs) is folded to 6 % height and darkened, everything above it is lowered so the belly rests on the ground.
    The back line stays nearly level because the hind belly line is set high. The head is a separate piece (above the
    muzzle's underside, beyond the neck) lowered with the body and pivoted at the neck; head_flip mirrors it about the neck
    so it looks back over the shoulder. Returns (rgba, drop_at_neck)."""
    H, W = arr.shape[:2]
    ox, oy = origin
    nx, ny = neck[0] - ox, neck[1] - oy
    fy = int(round(foot_y - oy)); fy = min(H, fy)
    xs = np.arange(W)
    ys_ = np.arange(H)[:, None]
    hw = np.clip(((xs - nx) if facing > 0 else (nx - xs)) / 6.0 + 0.5, 0, 1)[None, :] * np.ones((H, 1))
    hw = hw * (1 - np.clip((ys_ - (muzzle_y - oy)) / 4.0, 0, 1))
    head = arr.copy(); head[..., 3] *= hw * (0 if no_head else 1)
    body = arr.copy(); body[..., 3] *= (1 - hw)
    hx = hind_x - ox
    u = np.clip((xs - nx) / (hx - nx + 1e-6), 0, 1)
    belly = (chest_belly - oy) + u * (hind_belly - chest_belly)
    out = np.zeros_like(body)
    drop_neck = 0
    for x in range(W):
        by = int(round(min(belly[x], fy - 1)))
        leg_h = max(1, fy - by)
        new_leg = max(1, int(round(leg_h * (1 - 0.94 * lie))))
        drop = leg_h - new_leg
        if abs(x - nx) < 1: drop_neck = drop
        col = body[:, x]
        top = col[:by]
        out[drop:by + drop, x] = top
        seg = col[by:fy]
        if len(seg):
            idx = np.linspace(0, len(seg) - 1, new_leg).astype(int)
            legs = seg[idx].copy(); legs[:, :3] *= (1 - 0.45 * lie)
            out[by + drop:by + drop + new_leg, x] = legs
    if drop_neck == 0:
        by = int(round(belly[int(np.clip(nx, 0, W - 1))])); drop_neck = int(round((fy - by) * 0.94 * lie))
    hd = np.zeros_like(head)
    d = drop_neck
    hd[d:] = head[:H - d] if d > 0 else head
    if head_flip:
        hd2 = np.zeros_like(hd)
        c = int(round(nx))
        for x in range(W):
            xm = 2 * c - x
            if 0 <= xm < W: hd2[:, xm] = hd[:, x]
        hd = hd2
        facing = -facing
    ang = head_deg if facing > 0 else -head_deg
    hd = rotate_rgba(hd, ang, (nx, ny + d))
    a_h = hd[..., 3:4]
    comp = out.copy()
    comp[..., :3] = hd[..., :3] * a_h + out[..., :3] * out[..., 3:4] * (1 - a_h)
    comp[..., 3:4] = a_h + out[..., 3:4] * (1 - a_h)
    comp[..., :3] = np.where(comp[..., 3:4] > 1e-4, comp[..., :3] / np.maximum(comp[..., 3:4], 1e-4), 0)
    return comp, d

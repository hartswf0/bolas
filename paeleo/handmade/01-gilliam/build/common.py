"""Shared primitives for SCION-01 (Gilliam): engraving by luminance hatching, masks, card placement."""
import json, os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, 'sources')
CACHE = os.path.join(HERE, 'cache')
SCORE = os.path.abspath(os.path.join(ROOT, '..', 'score', 'threshold-score.json'))
os.makedirs(CACHE, exist_ok=True)

W, H, FPS = 1280, 720, 24
# --- the space: score metres -> screen pixels (elevation of the house front, porch running right) ---
X0, K = 300.0, 185.0          # x = 0 (threshold, centre of the door opening) at screen 300; 185 px per metre
FLOOR = 604                   # porch floor line
def sx(x):
    return X0 + K * x

INK = np.array([28, 20, 24], np.float32)
CARD_BACK = np.array([236, 230, 214], np.float32)


def load(name, f):
    return Image.open(os.path.join(SRC, name, 'f%03d.jpg' % f)).convert('RGB')


def mask_of(name, f, size=None, polys_filter=None):
    m = json.load(open(os.path.join(SRC, name, 'masks.json')))[str(f)]
    im = load(name, f)
    mk = Image.new('L', im.size, 0)
    d = ImageDraw.Draw(mk)
    for i, p in enumerate(m):
        if polys_filter is None or polys_filter(i, p):
            d.polygon([tuple(q) for q in p], fill=255)
    return mk


def poly_mask(size, poly):
    mk = Image.new('L', size, 0)
    ImageDraw.Draw(mk).polygon([tuple(q) for q in poly], fill=255)
    return mk


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def box_blur(a, r):
    im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(r)), np.float32) / 255.0


def engrave(rgb, alpha, scale, angle=35.0, spacing=4.2, wash=(200, 170, 120), wash_mix=0.35,
            contrast=(0.04, 0.96), gamma=1.0, warp=1.6, cross=0.52, outline=2.2, margin=0,
            ink=INK, seed=0, lift=0.0):
    """Turn a photographic cut-out into an engraved, hand-coloured paper card.
    rgb, alpha: PIL images of the source crop. scale: output px per source px.
    Lines: parallel hatching whose width follows darkness, displaced by the blurred tone (so lines bend
    over form like a burin line); a second set crosses only the darkest tones. Returns RGBA PIL image."""
    ss = 2  # supersample
    w, h = rgb.size
    Wd, Hd = max(2, int(round(w * scale * ss))), max(2, int(round(h * scale * ss)))
    pad = int((outline + margin + 2) * ss)
    big = rgb.resize((Wd, Hd), Image.BICUBIC)
    al = np.asarray(alpha.convert('L').resize((Wd, Hd), Image.BILINEAR), np.float32) / 255.0
    al = (box_blur(al, 1.5 * ss) > 0.5).astype(np.float32)
    col = np.asarray(big, np.float32) / 255.0
    col = np.pad(col, ((pad, pad), (pad, pad), (0, 0)), mode='edge')
    al = np.pad(al, pad)
    Hh, Ww = al.shape
    L = col @ np.array([0.299, 0.587, 0.114], np.float32)
    inside = al > 0.5
    if inside.sum() > 10:
        lo, hi = np.quantile(L[inside], [contrast[0], contrast[1]])
    else:
        lo, hi = 0, 1
    Ln = np.clip((L - lo) / max(1e-3, hi - lo), 0, 1) ** gamma
    Ln = np.clip(Ln + lift, 0, 1)
    Ls = box_blur(Ln, 3 * ss)
    yy, xx = np.mgrid[0:Hh, 0:Ww].astype(np.float32)
    s = spacing * ss
    def hatch(theta, dark):
        t = math.radians(theta)
        u = xx * math.cos(t) + yy * math.sin(t) + warp * s * (Ls - 0.5) * 2.0
        dist = np.abs(((u / s) + 0.5) % 1.0 - 0.5) * s
        hw = dark * s * 0.5
        return np.clip(hw - dist + 0.7 * ss, 0, 1)
    dark = 1.0 - Ln
    ink1 = hatch(angle, np.clip(dark * 1.05, 0, 1))
    ink2 = hatch(angle + 62, np.clip((dark - cross) / (1 - cross), 0, 1) * 0.9)
    ink_a = np.maximum(ink1, ink2)
    # cut edge: a firm engraved contour just inside the scissor line
    A = Image.fromarray((al * 255).astype(np.uint8))
    if outline > 0:
        er = np.asarray(A.filter(ImageFilter.MinFilter(int(outline * ss) * 2 + 1)), np.float32) / 255
        edge = np.clip(al - er, 0, 1)
        ink_a = np.maximum(ink_a * al, edge)
    else:
        ink_a = ink_a * al
    # paper margin (a scissor halo of bare card)
    if margin > 0:
        dil = np.asarray(A.filter(ImageFilter.MaxFilter(int(margin * ss) * 2 + 1)), np.float32) / 255
    else:
        dil = al
    # hand colouring: a wash mixed from the source's own colour and a chosen tint
    src_c = np.stack([box_blur(col[..., i], 2.5 * ss) for i in range(3)], -1)
    wash_c = np.array(wash, np.float32) / 255.0
    wcol = (1 - wash_mix) * wash_c + wash_mix * src_c
    wcol = wcol * (0.82 + 0.18 * Ls[..., None])
    rng = np.random.default_rng(seed)
    grain = 1.0 + (box_blur(rng.random((Hh, Ww)).astype(np.float32), 0.8) - 0.5) * 0.10
    paper = np.where(inside_pad(al)[..., None], wcol, np.array([0.93, 0.90, 0.82]))
    out = paper * grain[..., None]
    ink_rgb = ink / 255.0
    out = out * (1 - ink_a[..., None] * 0.92) + ink_rgb * ink_a[..., None] * 0.92
    out = np.clip(out, 0, 1)
    rgba = np.dstack([out, dil])
    im = Image.fromarray((rgba * 255).astype(np.uint8), 'RGBA')
    im = im.resize((max(1, Ww // ss), max(1, Hh // ss)), Image.LANCZOS)
    return im, pad / ss


def inside_pad(al):
    return al > 0.5


def card_back(front, seed=1, ghost=0.13, stamp=None):
    """The reverse of a cut-out: bare white card, with the engraving's ink faintly showing through."""
    a = np.asarray(front, np.float32) / 255.0
    lum = a[..., :3] @ np.array([0.299, 0.587, 0.114], np.float32)
    rng = np.random.default_rng(seed)
    h, w = lum.shape
    fib = box_blur(rng.random((h, w)).astype(np.float32), 0.7)
    base = CARD_BACK / 255.0 * (0.96 + 0.08 * fib[..., None])
    out = base * (1 - ghost * (1 - lum[..., None]))
    # glue smear
    yy, xx = np.mgrid[0:h, 0:w]
    out *= (1 - 0.05 * np.exp(-(((xx - w * 0.55) / (w * 0.18)) ** 2 + ((yy - h * 0.45) / (h * 0.15)) ** 2)))[..., None]
    # firm cut edge
    al = a[..., 3]
    A = Image.fromarray((al * 255).astype(np.uint8))
    er = np.asarray(A.filter(ImageFilter.MinFilter(3)), np.float32) / 255
    edge = np.clip(al - er, 0, 1)[..., None]
    out = out * (1 - edge * 0.55) + np.array([0.45, 0.42, 0.38]) * edge * 0.55
    im = Image.fromarray((np.dstack([np.clip(out, 0, 1), al]) * 255).astype(np.uint8), 'RGBA')
    return im


def place(dst, card, pivot, at, angle=0.0, sx_=1.0, sy_=1.0):
    """Paste a card so that its pivot (card px) lands on `at` (dst px), rotated by angle (deg, clockwise
    on screen) and scaled (sx_ may be negative: the card is turned over). dst: RGBA PIL image (mutated)."""
    if abs(sx_) < 0.02:
        return
    a = math.radians(angle)
    ca, sa = math.cos(a), math.sin(a)
    # forward: p_dst = at + R * S * (p - pivot)
    M = np.array([[ca * sx_, -sa * sy_], [sa * sx_, ca * sy_]])
    Mi = np.linalg.inv(M)
    w, h = card.size
    corners = np.array([[0, 0], [w, 0], [0, h], [w, h]], float) - pivot
    pts = corners @ M.T + np.array(at)
    x0, y0 = np.floor(pts.min(0)).astype(int) - 1
    x1, y1 = np.ceil(pts.max(0)).astype(int) + 1
    x0c, y0c = max(x0, 0), max(y0, 0)
    x1c, y1c = min(x1, dst.size[0]), min(y1, dst.size[1])
    if x1c <= x0c or y1c <= y0c:
        return
    # inverse: p = pivot + Mi (q - at), q = (x0c + i, y0c + j)
    off = np.array([x0c, y0c], float) - np.array(at)
    c = np.array(pivot) + Mi @ off
    coeffs = (Mi[0, 0], Mi[0, 1], c[0], Mi[1, 0], Mi[1, 1], c[1])
    patch = card.transform((x1c - x0c, y1c - y0c), Image.AFFINE, coeffs, resample=Image.BICUBIC)
    dst.alpha_composite(patch, (x0c, y0c))


def shadowed(card, off=(4, 5), alpha=0.38, blur=2.0):
    """A cut-out lifted off the background: return (shadow card, offset)."""
    a = np.asarray(card, np.float32)[..., 3] / 255.0
    sh = Image.fromarray((a * 255 * alpha).astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur))
    z = Image.new('RGBA', card.size, (20, 10, 30, 0))
    z.putalpha(sh)
    return z


def load_score():
    return json.load(open(SCORE))

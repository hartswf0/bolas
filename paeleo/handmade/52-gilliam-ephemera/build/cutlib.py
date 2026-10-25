"""cutlib: the fabricator's bench. Cuts a piece out of a source print with scissors (a polygon), optionally
intersected with the SAM matte of that print, prints it in a hand-tinted tone, and leaves the light paper core showing
at the cut edge. Everything a piece is (source frame, cut polygon, scale, tint, pins) is recorded in pieces.json."""
import json, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
FOLDER = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(FOLDER)))  # /home/user/bolas
CACHE = os.path.join(HERE, 'cache')
SS = 4  # supersampling of the scissor line

PALETTES = {  # three-stop print tones (dark, mid, light): the hand-tinting of a monochrome print
    'dog':   [(34, 22, 16), (120, 84, 54), (222, 190, 140)],
    'dogfar': [(24, 16, 12), (84, 58, 40), (160, 132, 98)],
    'smock': [(48, 28, 40), (150, 100, 112), (236, 206, 204)],
    'skin':  [(44, 26, 20), (158, 108, 82), (242, 214, 182)],
    'jeans': [(18, 22, 36), (58, 66, 100), (146, 156, 186)],
    'door':  [(58, 52, 46), (168, 156, 134), (240, 232, 210)],
    'stone': [(36, 36, 42), (112, 110, 106), (196, 190, 178)],
    'cloud': [(70, 52, 96), (170, 112, 132), (246, 186, 156)],
    'bulb':  [(70, 44, 20), (214, 172, 92), (255, 246, 206)],
    'sleeve': [(30, 14, 20), (110, 40, 52), (200, 140, 140)],
}


def lum(img):
    a = np.asarray(img.convert('RGB')).astype(np.float32) / 255.0
    return 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]


def ramp(L, pal):
    pal = np.array(pal, np.float32) / 255.0
    L = np.clip(L, 0, 1)[..., None]
    lo = pal[0] + (pal[1] - pal[0]) * np.clip(L * 2, 0, 1)
    hi = pal[1] + (pal[2] - pal[1]) * np.clip(L * 2 - 1, 0, 1)
    return np.where(L < .5, lo, hi)


def poly_alpha(polys, size, scale, off, holes=()):
    """Rasterise scissor polygons (source coords) at scale, anti-aliased by supersampling."""
    W, H = size
    m = Image.new('L', (W * SS, H * SS), 0)
    d = ImageDraw.Draw(m)
    tr = lambda p: ((p[0] * scale - off[0]) * SS, (p[1] * scale - off[1]) * SS)
    for p in polys:
        if p[0] == 'disc':
            _, cx, cy, r = p
            x, y = tr((cx, cy)); rr = r * scale * SS
            d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=255)
        else:
            d.polygon([tr(q) for q in p], fill=255)
    for p in holes:
        d.polygon([tr(q) for q in p], fill=0)
    return np.asarray(m.resize((W, H), Image.BOX)).astype(np.float32) / 255.0


def cut(name, src, polys, scale, palette, mask_polys=None, holes=(), stretch=(2, 98), gamma=1.0, sharpen=True,
        rim=1.0, seed=0, pins=None, notes='', provenance=None, keep_color=False, extra_alpha=None):
    """src: path to the print (a frame). polys: list of polygons / ('disc',cx,cy,r) in source pixels.
    Returns a record; writes cache/pieces/<name>.png (RGBA at screen scale)."""
    im = Image.open(src).convert('RGB')
    pts = []
    for p in polys:
        if p[0] == 'disc':
            pts += [(p[1] - p[3], p[2] - p[3]), (p[1] + p[3], p[2] + p[3])]
        else:
            pts += list(p)
    x0 = max(0, min(q[0] for q in pts) - 3); y0 = max(0, min(q[1] for q in pts) - 3)
    x1 = min(im.width, max(q[0] for q in pts) + 3); y1 = min(im.height, max(q[1] for q in pts) + 3)
    off = (math.floor(x0 * scale), math.floor(y0 * scale))
    W = int(math.ceil(x1 * scale)) - off[0]; H = int(math.ceil(y1 * scale)) - off[1]
    # resample the print region to screen scale
    crop = im.transform((W, H), Image.AFFINE, (1 / scale, 0, off[0] / scale, 0, 1 / scale, off[1] / scale), Image.BICUBIC)
    a = poly_alpha(polys, (W, H), scale, off, holes)
    if mask_polys is not None:
        a = a * poly_alpha(mask_polys, (W, H), scale, off)
    if extra_alpha is not None:
        a = a * extra_alpha(crop, W, H)
    L = lum(crop)
    inside = a > .5
    if inside.sum() > 10:
        lo, hi = np.percentile(L[inside], stretch)
        L = np.clip((L - lo) / max(hi - lo, 1e-3), 0, 1)
    L = L ** gamma
    if sharpen:
        Li = Image.fromarray((L * 255).astype(np.uint8)).filter(ImageFilter.UnsharpMask(radius=1.6, percent=90, threshold=1))
        L = np.asarray(Li).astype(np.float32) / 255.0
    if keep_color:
        rgb = np.asarray(crop).astype(np.float32) / 255.0
    else:
        rgb = ramp(L, PALETTES[palette])
    # hand tint: a low-frequency wash, the unevenness of a brush of dye
    rng = np.random.default_rng(seed)
    n = Image.fromarray((rng.random((max(2, H // 14), max(2, W // 14))) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)
    wash = (np.asarray(n).astype(np.float32) / 255.0 - .5) * .10
    rgb = np.clip(rgb * (1 + wash[..., None]), 0, 1)
    # paper core at the cut edge
    A = Image.fromarray((a * 255).astype(np.uint8))
    er = np.asarray(A.filter(ImageFilter.MinFilter(3))).astype(np.float32) / 255.0
    edge = np.clip(a - er, 0, 1) * rim
    paper = np.array([.93, .90, .82], np.float32)
    rgb = rgb * (1 - edge[..., None] * .75) + paper * edge[..., None] * .75
    out = np.dstack([rgb * 255, a * 255]).astype(np.uint8)
    os.makedirs(os.path.join(CACHE, 'pieces'), exist_ok=True)
    fn = os.path.join(CACHE, 'pieces', name + '.png')
    Image.fromarray(out, 'RGBA').save(fn)
    pins = {k: [v[0] * scale, v[1] * scale] for k, v in (pins or {}).items()}
    return {'name': name, 'file': os.path.relpath(fn, FOLDER), 'origin': [off[0], off[1]], 'size': [W, H],
            'scale': scale, 'pins': pins, 'palette': palette, 'cut_polygons_src_px': [list(p) for p in polys],
            'source_print': os.path.relpath(src, ROOT) if src.startswith(ROOT) else src,
            'provenance': provenance or {}, 'notes': notes}

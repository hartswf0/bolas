"""Test-shot rig for La Machine a tuer le temps (direction 1, Le cahier rebattu).

Handmade notebook (paper, coil, mount cards, typed tape, pen and red-pencil
numbers written stroke by stroke) + the frozen pool of LoC Jack Delano 1943
prints, printed once with one print-stage tone map.  Cards move by translation
only (SCION 40), with a damped spring at set-down and a lift shadow (SCION 41).
Everything is a pure function of the frame index (SCION 27).
"""
import math, random, hashlib, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SRC = '/home/user/bolas/paeleo/scion/oulipo/films/sources/la-machine-a-tuer-le-temps/'
HI = SRC + 'test-shot/hires/'
COUR = '/usr/share/fonts/X11/Type1/c0419bt_.pfb'
OW, OH = 1280, 720

# ---------------------------------------------------------------- the pool ---
# crop = picture area inside the negative rebate, in coordinates of the LoC
# 1024-px service JPEG; windows W0/W1 (16:9) in the same coordinates.
POOL = {
 '05': dict(file='loc_2017843923.jpg', hi='05u.tif', crop=(132, 32, 856, 748),
            W0=(134, 150, 854, 555), W1=(253, 189, 807, 501),
            cap="05.- Le porteur regarde hors du\n     champ, vers la consigne."),
 '04': dict(file='loc_2017843935.jpg', hi='04u.tif', crop=(66, 96, 888, 968),
            W0=(70, 168, 870, 618), W1=(146, 192, 813, 567),
            cap="04.- Un soldat monte dans le\n     wagon ; on lui fait signe."),
 '02': dict(file='loc_2017844121.jpg', hi=None, crop=(38, 32, 982, 768),
            W0=(40, 100, 960, 617), W1=(100, 173, 836, 587),
            cap="02.- Une femme emporte le colis\n     et se retourne."),
 '03': dict(file='loc_2017844115.jpg', hi=None, crop=(32, 34, 756, 980),
            W0=None, W1=None,
            cap="03.- Le controleur regarde\n     sa montre."),
}
LO = np.array([24, 20, 18.0]); HIW = np.array([232, 226, 214.0])   # print_op


def print_op(gray):
    """One print stage: print each negative to full scale (black / white points
    at its own 0.5 / 99.5 percentiles, as a printer exposes per negative), then
    map grey to warm silver-gelatin black (24,20,18) .. paper white (232,226,214)."""
    a = np.asarray(gray).astype(np.float64)
    lo, hi = np.percentile(a, [0.5, 99.5])
    a = np.clip((a - lo) / (hi - lo), 0, 1)
    return Image.fromarray((LO + (HIW - LO) * a[..., None]).round().clip(0, 255).astype(np.uint8))


_toned = {}


def toned(k):
    """(image, scale) : the toned print of asset k, cropped to its picture area.
    scale = pixels of this image per pixel of the 1024 service JPEG."""
    if k in _toned:
        return _toned[k]
    p = POOL[k]
    if p['hi']:
        im = Image.open(HI + p['hi']).convert('L')
        v = Image.open(SRC + p['file'])
        s_native = im.width / v.width
        s = 2.0
        im = im.resize((round(v.width * s), round(v.height * s)), Image.LANCZOS)
    else:
        im = Image.open(SRC + p['file']).convert('L'); s = 1.0
    c = p['crop']
    im = im.crop(tuple(round(x * s) for x in c))
    _toned[k] = (print_op(im), s)
    return _toned[k]


def asset_frame(k, src):
    """Frozen rostrum asset: frame src (0..119) of asset k at 1280x720."""
    im, s = toned(k); p = POOL[k]; c = p['crop']
    u = src / 119.0; u = u * u * (3 - 2 * u)
    box = [(p['W0'][i] + (p['W1'][i] - p['W0'][i]) * u - c[i % 2]) * s for i in range(4)]
    return im.transform((OW, OH), Image.EXTENT, tuple(box), Image.BICUBIC)


# ------------------------------------------------------------ paper model ---
def fibre(w, h, base, seed, sigma=4.0):
    rng = np.random.default_rng(seed)
    lf = rng.normal(0, 1, (h // 48 + 2, w // 48 + 2))
    lf = np.array(Image.fromarray(((lf * 40) + 128).clip(0, 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)).astype(float) - 128
    mf = rng.normal(0, 1, (h // 6 + 2, w // 6 + 2))
    mf = np.array(Image.fromarray(((mf * 40) + 128).clip(0, 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)).astype(float) - 128
    hf = rng.normal(0, 1, (h, w))
    n = hf / hf.std() * sigma * 0.85 + (lf * 0.5 + mf * 0.5) / (lf * 0.5 + mf * 0.5).std() * sigma * 0.5
    a = np.empty((h, w, 3))
    for i, cc in enumerate(base):
        a[..., i] = cc + n * (1.0 if i < 2 else 0.9)
    return a


TW, TH = 2560, 1440                     # table coordinates
LP = (70, 40, 1250, 1400); RP = (1310, 40, 2490, 1400)
SLOT_C = {1: (110, 120), 2: (680, 120), 3: (110, 760), 4: (680, 760),      # card top-left
          5: (1340, 120), 6: (1910, 120), 7: (1340, 760), 8: (1910, 760)}
CW, CH = 540, 580                       # mount card


def build_table():
    t = fibre(TW, TH, (214, 208, 197), 3, sigma=4)
    img = t
    for i, (x0, y0, x1, y1) in enumerate([LP, RP]):
        base = (237, 229, 213) if i == 0 else (243, 235, 217)
        pg = fibre(x1 - x0, y1 - y0, base, 10 + i)
        yy, xx = np.mgrid[0:y1 - y0, 0:x1 - x0]
        gut = (x1 - x0 - xx) if i == 0 else xx
        pg *= (0.965 + 0.035 * np.clip(gut / 60, 0, 1))[..., None]      # faint gutter
        # page contact shadow on the table (flat copy light: 2 px)
        sh = np.zeros((TH, TW)); sh[y0 + 2:y1 + 2, x0 + 1:x1 + 1] = 1
        sh = np.array(Image.fromarray((sh * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2))).astype(float) / 255
        img = img * (1 - 0.18 * sh[..., None])
        img[y0:y1, x0:x1] = pg
    im = Image.fromarray(img.clip(0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    # wire coil, 24 loops, fine
    n = 24; ys = np.linspace(70, 1370, n)
    for y in ys:
        y = float(y)
        for x in (1238, 1312):                      # punched holes
            d.ellipse([x - 5, y + 10, x + 5, y + 20], fill=(150, 140, 126))
        d.arc([1228, y - 4, 1322, y + 30], 195, 345, fill=(52, 50, 48), width=4)
        d.arc([1230, y - 2, 1320, y + 28], 205, 300, fill=(196, 194, 190), width=1)
    return im


# ------------------------------------------------------- hand lettering ---
DIG = {'1': [[(.25, .25), (.55, 0), (.5, 1)]],
       '2': [[(.1, .25), (.4, 0), (.8, .1), (.8, .4), (.1, 1), (.95, .98)]],
       '3': [[(.1, .1), (.5, 0), (.85, .2), (.45, .48), (.9, .7), (.6, 1), (.1, .9)]],
       '4': [[(.7, 1), (.65, 0), (.05, .7), (.95, .68)]],
       '5': [[(.85, 0), (.2, 0), (.15, .45), (.6, .4), (.9, .7), (.55, 1), (.1, .9)]],
       'A': [[(0, 1), (.45, 0), (.95, 1)], [(.2, .6), (.75, .6)]],
       'B': [[(.1, 1), (.1, 0), (.7, .05), (.75, .4), (.1, .5), (.85, .62), (.8, 1), (.1, 1)]]}


def catmull(pts, n=10):
    P = [pts[0]] + pts + [pts[-1]]; out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t * t
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t ** 3) for j in range(2)))
    out.append(pts[-1]); return out


def glyph_path(ch, x, y, h, seed, slant=0.14):
    """One instance of a hand glyph: its own jitter (no two instances equal)."""
    rng = random.Random(seed); strokes = []
    for st in DIG[ch]:
        pts = [(x + (px + rng.uniform(-.05, .05)) * h * 0.62 + (1 - py) * h * slant,
                y + (py + rng.uniform(-.035, .035)) * h) for px, py in st]
        strokes.append(catmull(pts))
    return strokes


def draw_path(strokes, frac, width, rng_seed, pencil=False):
    """Draw the first `frac` (0..1) of the strokes' total length onto a mask
    (returned as an L image in a local box) plus its offset."""
    allp = [p for s in strokes for p in s]
    x0 = int(min(p[0] for p in allp)) - 8; y0 = int(min(p[1] for p in allp)) - 8
    x1 = int(max(p[0] for p in allp)) + 8; y1 = int(max(p[1] for p in allp)) + 8
    m = Image.new('L', (x1 - x0, y1 - y0), 0); d = ImageDraw.Draw(m)
    L = [sum(math.dist(s[i], s[i + 1]) for i in range(len(s) - 1)) for s in strokes]
    budget = frac * sum(L); k = 0
    for s in strokes:
        for i in range(len(s) - 1):
            seg = math.dist(s[i], s[i + 1])
            if budget <= 0: break
            a, b = s[i], s[i + 1]
            if seg > budget:
                f = budget / seg; b = (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
            budget -= seg
            # pressure: heavier mid-stroke, lighter at entry/exit
            pr = 0.65 + 0.45 * math.sin(math.pi * min(1, (i + 1) / max(2, len(s) - 1)))
            w = width * pr
            d.line([(a[0] - x0, a[1] - y0), (b[0] - x0, b[1] - y0)], fill=255, width=max(1, round(w)))
            d.ellipse([b[0] - x0 - w / 2, b[1] - y0 - w / 2, b[0] - x0 + w / 2, b[1] - y0 + w / 2], fill=255)
            k += 1
    m = m.filter(ImageFilter.GaussianBlur(0.6))
    if pencil:   # graphite/wax catches only the paper tooth: broken, grainy stroke
        rng = np.random.default_rng(rng_seed)
        tooth = rng.random((m.height, m.width))
        tooth = np.array(Image.fromarray((tooth * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7))).astype(float) / 255
        a = np.asarray(m).astype(float) / 255
        a = a * np.clip((tooth - 0.30) * 2.4, 0.15, 1)
        m = Image.fromarray((a * 255).clip(0, 255).astype(np.uint8))
    return m, (x0, y0)


def ink_on(img, mask, off, color, opacity=1.0):
    col = Image.new('RGB', mask.size, color)
    a = mask.point(lambda v: int(v * opacity))
    img.paste(col, off, a)


INK = (66, 58, 47)          # #423a2f
RED_CORE = (170, 38, 42)    # red pencil


# ------------------------------------------------------------ typed tape ---
def typed_tape(text, seed, sz=19):
    f = ImageFont.truetype(COUR, sz)
    lines = text.split('\n'); adv = f.getlength('M')
    W = int(max(len(l) for l in lines) * adv + 26); H = int(len(lines) * sz * 1.2 + 16)
    a = fibre(W, H, (240, 236, 224), seed + 50, sigma=3)
    band = np.zeros((H, W)); band[int(H * .16):int(H * .86)] = 1
    band = np.array(Image.fromarray((band * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5))).astype(float) / 255
    rng = np.random.default_rng(seed)
    yel = np.array([223, 190, 135.0])            # #dfbe87
    tone = yel[None, None, :] + rng.normal(0, 9, (1, W, 1)).repeat(H, 0) * 0.6
    a = a * (1 - band[..., None] * .8) + tone * band[..., None] * .8
    tape = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    # character-by-character typewriter: baseline + density variation per strike
    r = random.Random(seed)
    for li, l in enumerate(lines):
        for ci, ch in enumerate(l):
            if ch == ' ': continue
            g = Image.new('L', (int(adv) + 6, sz + 8), 0)
            ImageDraw.Draw(g).text((3, 2), ch, font=f, fill=255)
            dens = r.uniform(0.55, 0.92)
            g = g.point(lambda v, dd=dens: int(v * dd))
            x = 13 + ci * adv + r.uniform(-.5, .5); y = 7 + li * sz * 1.2 + r.uniform(-.8, .8)
            tape.paste(Image.new('RGB', g.size, (112, 86, 58)), (int(x), int(y)), g)
    return tape


# ----------------------------------------------------------- mount card ---
def print_rect_local(k):
    im, s = toned(k)
    w, h = im.size
    sc = min(460 / w, 320 / h)
    pw, ph = w * sc, h * sc
    return ((CW - pw) / 2, 40.0, (CW - pw) / 2 + pw, 40.0 + ph)


def build_card(k, number, seed):
    a = fibre(CW, CH, (244, 237, 223), seed, sigma=5)
    card = Image.fromarray(a.clip(0, 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(card)
    d.rectangle([0, 0, CW - 1, CH - 1], outline=(222, 213, 196, 255), width=1)
    x0, y0, x1, y1 = print_rect_local(k)
    tape = typed_tape(POOL[k]['cap'], seed + 7)
    ty = int(y1 + 30)
    card.paste(tape, (int(CW / 2 - tape.width / 2), ty))
    ny = ty + tape.height + 40
    g = glyph_path(number, CW / 2 - 14, ny, 46, seed + 3)
    m, off = draw_path(g, 1.0, 3.0, seed)
    rgb = card.convert('RGB'); ink_on(rgb, m, off, INK, 0.92)
    card = rgb.convert('RGBA')
    return card, (CW / 2 - 14, ny)

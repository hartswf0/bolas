"""notebook_rig.py -- La Machine a tuer le temps, direction 1 'Le cahier rebattu'.

The handmade notebook and its frame-by-frame animation, as an importable rig.

  SCION 40 (paper performance): every paper piece is a rigid piece with a
    per-drawing transform restricted to TRANSLATION, driven by a frame-indexed
    event stream (lift / travel / setdown / settle / strike / write / turn /
    slide / line) that the sound unit consumes.
  SCION 41 (secondary dynamics): damped spring at set-down (overshoot 2-3 px,
    energy gone within 6 drawings), lift shadow whose offset and blur grow
    with lift height, leading-edge shadow on the loose sheet.  Nothing moves
    at rest except the +-0.6 px stop-motion table jitter.
  SCION 27 (declarative compiler): the whole notebook is a pure function of
    (frame index, choreography data, fixed seeds); the S5 moves are data.

Layout (user review of the first test shot): ONE print pasted directly on
each page with broad cream margins, two pages per spread, 4 spreads.  The
page = slot.  Each print travels with its typed tape and its ink number on a
slip of the same notebook stock; at rest on a page the slip is flush and is
not drawn (the page reads as print + tape + number pasted on the page); the
slip's paper edge only shows while it is lifted or lies on the table.

Prints are never drawn at table resolution when at rest or lifted: they are
re-sampled from the registrar's master-TIFF pyramid at the camera scale and
toned with the registrar's print_op (same lo/hi, same gamma) so the push ends
on asset frame 0.  Exception, declared per frame in the ledger: during a leaf
turn the prints on the turning leaf are foreshortened by the physical turn.

Public API
  TL                         timeline (global frames, plan section 7, S5 rebuilt)
  notebook_frame(f) -> (PIL.Image 1280x720, ledger dict) for notebook segments
  asset_frame(k, src)        registrar frozen asset frame (PNG) or exact re-render
  EVENTS                     frame-indexed event stream (global frames)
  segment_of(f)
Run:  python3 notebook_rig.py --prep      (build print pyramids from masters)
"""
import math, random, json, hashlib, os, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

Image.MAX_IMAGE_PIXELS = None
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]                                   # .../oulipo
SRC = ROOT / 'films/sources/la-machine-a-tuer-le-temps'
REG = SRC / 'registrar'
WORK = SRC / 'notebook-animator/work'
COUR = '/usr/share/fonts/X11/Type1/c0419bt_.pfb'
OW, OH, FPS = 1280, 720, 24
sys.path.insert(0, str(HERE))
import registrar_build as RB                             # geometry + print_op of the frozen pool

A_ORDER = ['01', '02', '03', '04', '05', '06', '07', '08']
B_ORDER = ['05', '04', '02', '06', '03', '01', '07', '08']
CAPS = {
 '01': "01.- L'horloge du bureau de\n     régulation ; on pointe.",
 '02': "02.- Une femme emporte le colis\n     et se retourne.",
 '03': "03.- Le contrôleur regarde\n     sa montre.",
 '04': "04.- Un soldat monte dans le\n     wagon ; la porte reste ouverte.",
 '05': "05.- Le porteur regarde hors du\n     champ, vers la consigne.",
 '06': "06.- Les bons de réservation\n     restent sur le comptoir.",
 '07': "07.- Les soldats sortent par\n     la voie 2.",
 '08': "08.- La salle d'attente, vide,\n     à une heure du matin.",
}

# ============================================================ the print pool
_meta = None


def meta():
    """Registrar geometry (master px), levels, and our pyramid reduce factor."""
    global _meta
    if _meta is None:
        mf = WORK / 'pyramid.json'
        _meta = json.load(open(mf)) if mf.exists() else {}
    return _meta


def prep():
    """Build one gray pyramid level per print from the LoC master TIFF:
    integer box reduce so the clean picture is ~2600 px wide (never upscaled)."""
    WORK.mkdir(parents=True, exist_ok=True)
    meas = json.load(open(REG / 'measure.json')) if (REG / 'measure.json').exists() else {}
    out = {}
    for k in A_ORDER:
        im = RB.load(k)
        s, clean, W0, W1 = RB.geometry(k, im.size)
        lo, hi = meas[k]['levels'] if k in meas else RB.levels(im, clean)
        r = max(1, int((clean[2] - clean[0]) // 2600))
        lvl = im.reduce(r) if r > 1 else im
        lvl.save(WORK / f'{k}_pyr.png')
        out[k] = dict(native=list(im.size), clean=list(clean), W0=list(W0), W1=list(W1),
                      levels=[lo, hi], pyr_reduce=r, pyr_size=list(lvl.size),
                      master_sha256=None)
        print(k, im.size, 'r', r, lvl.size, flush=True)
    json.dump(out, open(WORK / 'pyramid.json', 'w'), indent=1)


_pyr = {}


def pyr(k):
    if k not in _pyr:
        _pyr[k] = Image.open(WORK / f'{k}_pyr.png').convert('L')
        _pyr[k].load()
    return _pyr[k]


def tone(gray_img, k):
    lo, hi = meta()[k]['levels']
    return Image.fromarray(RB.print_op(np.asarray(gray_img), lo, hi), 'RGB')


def clean_aspect(k):
    c = meta()[k]['clean']
    return (c[2] - c[0]) / (c[3] - c[1])


def sample_print(k, box_frac, size):
    """Re-sample print k from the master pyramid: box_frac = region of the
    clean picture in 0..1 fractions; size = output pixels.  Tone after resample
    (registrar order)."""
    m = meta()[k]; c = m['clean']; r = m['pyr_reduce']
    cw, ch = c[2] - c[0], c[3] - c[1]
    box = ((c[0] + box_frac[0] * cw) / r, (c[1] + box_frac[1] * ch) / r,
           (c[0] + box_frac[2] * cw) / r, (c[1] + box_frac[3] * ch) / r)
    g = pyr(k).resize(size, Image.LANCZOS, box=box)
    return tone(g, k)


def w_frac(k, which='W0'):
    """Registrar window (master px) as fractions of the clean picture."""
    m = meta()[k]; c = m['clean']; W = m[which]
    cw, ch = c[2] - c[0], c[3] - c[1]
    return ((W[0] - c[0]) / cw, (W[1] - c[1]) / ch, (W[2] - c[0]) / cw, (W[3] - c[1]) / ch)


def asset_frame(k, src):
    """The frozen pool frame (registrar PNG); exact re-render if not frozen yet."""
    p = REG / 'assets' / k / f'{src:04d}.png'
    if p.exists():
        return Image.open(p).convert('RGB')
    m = meta()[k]; red = 2 if max(m['native']) > 8000 else 1
    W = RB.windows(tuple(m['W0']), tuple(m['W1']))[src]
    im = RB.load(k); work = im.reduce(red) if red > 1 else im
    g = work.resize((OW, OH), Image.LANCZOS, box=tuple(v / red for v in W))
    return tone(g, k)


# ============================================================ paper model
def fibre(w, h, base, seed, sigma=4.5):
    """Cream stock: fine fibre noise + faint cloud, low sigma, no ruling."""
    rng = np.random.default_rng(seed)

    def up(n, cell):
        a = rng.normal(0, 1, (h // cell + 2, w // cell + 2))
        return np.array(Image.fromarray((a * 40 + 128).clip(0, 255).astype(np.uint8))
                        .resize((w, h), Image.BICUBIC)).astype(np.float32) - 128
    lf = up(0, 90); mf = up(0, 7)
    hf = rng.normal(0, 1, (h, w)).astype(np.float32)
    n = hf * sigma * 0.75 + mf / (mf.std() + 1e-6) * sigma * 0.45 + lf / (lf.std() + 1e-6) * sigma * 0.35
    a = np.empty((h, w, 3), np.float32)
    for i, cc in enumerate(base):
        a[..., i] = cc + n * (1.0, 0.98, 0.9)[i]
    return a


def to_img(a):
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


# ============================================================ hand lettering
G = {  # single-stroke skeletons in a unit box (x right, y down); my hand
 '0': [[(.5, 0), (.15, .2), (.1, .6), (.35, 1), (.75, .9), (.9, .45), (.7, .05), (.45, 0)]],
 '1': [[(.2, .25), (.55, 0), (.5, 1)]],
 '2': [[(.1, .25), (.4, 0), (.8, .1), (.8, .4), (.1, 1), (.95, .98)]],
 '3': [[(.1, .1), (.5, 0), (.85, .2), (.45, .48), (.9, .7), (.6, 1), (.1, .9)]],
 '4': [[(.7, 1), (.65, 0), (.05, .7), (.95, .68)]],
 '5': [[(.85, 0), (.2, 0), (.15, .45), (.6, .4), (.9, .7), (.55, 1), (.1, .9)]],
 '6': [[(.75, 0), (.25, .35), (.12, .75), (.45, 1), (.85, .75), (.6, .5), (.15, .65)]],
 '7': [[(.05, .02), (.95, 0), (.4, 1)]],
 '8': [[(.5, .48), (.15, .25), (.45, 0), (.85, .2), (.5, .48), (.1, .75), (.45, 1), (.9, .75), (.5, .48)]],
 '9': [[(.85, .3), (.5, .5), (.15, .3), (.45, 0), (.85, .2), (.8, .6), (.6, 1)]],
 'A': [[(0, 1), (.48, 0), (.95, 1)], [(.2, .62), (.78, .6)]],
 'B': [[(.1, 1), (.1, 0), (.65, .03), (.8, .25), (.6, .47), (.1, .5)], [(.6, .47), (.92, .72), (.7, .98), (.1, 1)]],
 'C': [[(.9, .15), (.55, 0), (.15, .15), (0, .5), (.15, .85), (.55, 1), (.9, .85)]],
 'E': [[(.85, 0), (.08, 0), (.08, 1), (.88, 1)], [(.08, .5), (.65, .5)]],
 'G': [[(.9, .15), (.55, 0), (.15, .15), (0, .5), (.15, .85), (.55, 1), (.9, .82), (.9, .55), (.55, .55)]],
 'H': [[(.05, 0), (.05, 1)], [(.9, 0), (.9, 1)], [(.05, .5), (.9, .5)]],
 'I': [[(.5, 0), (.5, 1)]],
 'L': [[(.1, 0), (.1, 1), (.85, 1)]],
 'M': [[(0, 1), (.08, 0), (.5, .65), (.92, 0), (1, 1)]],
 'N': [[(.05, 1), (.05, 0), (.9, 1), (.9, 0)]],
 'O': [[(.5, 0), (.12, .15), (0, .5), (.15, .88), (.5, 1), (.88, .85), (1, .5), (.85, .12), (.5, 0)]],
 'P': [[(.1, 1), (.1, 0), (.7, .02), (.9, .25), (.7, .48), (.1, .5)]],
 'R': [[(.1, 1), (.1, 0), (.7, .02), (.9, .25), (.7, .48), (.1, .5), (.95, 1)]],
 'S': [[(.9, .12), (.5, 0), (.12, .15), (.2, .42), (.8, .58), (.9, .85), (.5, 1), (.08, .88)]],
 'T': [[(0, 0), (1, 0)], [(.5, 0), (.5, 1)]],
 'U': [[(.05, 0), (.08, .75), (.5, 1), (.92, .75), (.95, 0)]],
 'À': [[(0, 1), (.48, 0), (.95, 1)], [(.2, .62), (.78, .6)], [(.3, -.38), (.55, -.16)]],
 '.': [[(.45, .92), (.5, .97)]],
 '-': [[(.1, .55), (.85, .5)]],
}
ADV = {'I': .42, 'M': 1.05, '.': .4, '-': .8, '1': .6}


def catmull(pts, n=9):
    if len(pts) == 2:
        return [pts[0], ((pts[0][0] + pts[1][0]) / 2, (pts[0][1] + pts[1][1]) / 2), pts[1]]
    P = [pts[0]] + pts + [pts[-1]]; out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t * t
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t ** 3) for j in range(2)))
    out.append(pts[-1]); return out


def word_strokes(s, x, y, h, seed, slant=0.13, wob=1.0, aspect=0.62):
    """Strokes of one written instance of string s (own jitter per instance,
    per glyph baseline drift and size wobble: a hand, not a font)."""
    rng = random.Random(seed); cx = x; out = []
    for ch in s:
        if ch == ' ':
            cx += h * 0.45; continue
        gh = h * rng.uniform(0.93, 1.07) ** wob
        by = y + rng.uniform(-0.05, 0.05) * h * wob
        for st in G[ch]:
            pts = [(cx + (px + rng.uniform(-.045, .045) * wob) * gh * aspect + (1 - py) * gh * slant,
                    by + (py + rng.uniform(-.035, .035) * wob) * gh) for px, py in st]
            out.append(catmull(pts))
        cx += gh * aspect * ADV.get(ch, 1.0) + h * 0.16 * rng.uniform(0.8, 1.25)
    return out


def strokes_len(strokes):
    return sum(math.dist(s[i], s[i + 1]) for s in strokes for i in range(len(s) - 1))


def stroke_bbox(strokes, pad):
    xs = [p[0] for s in strokes for p in s]; ys = [p[1] for s in strokes for p in s]
    return int(min(xs) - pad), int(min(ys) - pad), int(max(xs) + pad) + 1, int(max(ys) + pad) + 1


def render_strokes(strokes, frac, width, seed, tool='pen'):
    """Stroke-by-stroke mask of the first `frac` of total path length.
    Pressure: entry/exit taper, per-stroke weight, slow wander.  Pencil: the
    wax only catches the paper tooth, so the stroke is grainy and broken.
    Returns (L mask, (x0, y0)) in the strokes' coordinate frame."""
    x0, y0, x1, y1 = stroke_bbox(strokes, width * 2 + 4)
    S = 2                                                    # supersample
    m = Image.new('L', ((x1 - x0) * S, (y1 - y0) * S), 0); d = ImageDraw.Draw(m)
    rng = random.Random(seed)
    budget = frac * strokes_len(strokes)
    for s in strokes:
        if budget <= 0:
            break
        L = sum(math.dist(s[i], s[i + 1]) for i in range(len(s) - 1)) or 1
        sw = rng.uniform(0.85, 1.15); ph = rng.uniform(0, 6.28); acc = 0
        for i in range(len(s) - 1):
            a, b = s[i], s[i + 1]; seg = math.dist(a, b)
            if budget <= 0:
                break
            if seg > budget:
                f = budget / seg; b = (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f); seg = budget
            n = max(1, int(seg / max(0.6, width * 0.25)))
            for j in range(n + 1):
                t = j / n; px = a[0] + (b[0] - a[0]) * t; py = a[1] + (b[1] - a[1]) * t
                u = min(1, (acc + seg * t) / L)
                pr = (0.45 + 0.55 * min(1, u / 0.12) ** 0.6) * (0.55 + 0.45 * min(1, (1 - u) / 0.18) ** 0.7)
                pr *= sw * (1 + 0.12 * math.sin(ph + u * 7.0))
                r = max(0.5, width * pr / 2) * S
                cx, cy = (px - x0) * S, (py - y0) * S
                d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
            acc += seg; budget -= seg
    m = m.resize((x1 - x0, y1 - y0), Image.LANCZOS)
    if tool == 'pencil':
        g = np.random.default_rng(seed + 991)
        tooth = g.random((m.height, m.width)).astype(np.float32)
        tooth = np.asarray(Image.fromarray((tooth * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.55))).astype(np.float32) / 255
        a = np.asarray(m).astype(np.float32) / 255
        a = a * np.clip((tooth - 0.33) * 3.2, 0.12, 1.0) * 1.05
        m = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
    elif tool == 'felt':
        m = m.filter(ImageFilter.GaussianBlur(0.5))
    return m, (x0, y0)


def ink_on(img, mask, off, color, opacity=1.0):
    col = Image.new('RGB', mask.size, color)
    a = mask if opacity >= 1 else mask.point(lambda v: int(v * opacity))
    if img.mode == 'RGBA':
        lay = Image.new('RGBA', mask.size, color + (0,)); lay.putalpha(a)
        img.alpha_composite(lay, (int(off[0]), int(off[1])))
    else:
        img.paste(col, (int(off[0]), int(off[1])), a)


PEN = (66, 58, 47)            # #423a2f thin dark pen
RED_PENCIL = (196, 26, 34)    # true red pencil core
RED_INK = (168, 52, 47)       # thin red ink for page numbers (#b76158 at AA edge)
FELT = (24, 21, 23)
NUM_H = 58                    # pen and red-pencil numbers share this height


def hand(img, s, x, y, h, seed, color, width, tool='pen', frac=1.0, **kw):
    st = word_strokes(s, x, y, h, seed, **kw)
    m, off = render_strokes(st, frac, width, seed, tool)
    ink_on(img, m, off, color)
    return st


# ============================================================ typed tape
def typed_tape(text, seed, sz=25):
    """A strip of pale tape with the yellowed band; every character struck
    separately: its own density, baseline and a hair of horizontal play."""
    f = ImageFont.truetype(COUR, sz)
    lines = text.split('\n'); adv = f.getlength('M')
    W = int(max(len(l) for l in lines) * adv + 30); H = int(len(lines) * sz * 1.18 + 18)
    a = fibre(W, H, (242, 238, 226), seed + 50, sigma=2.5)
    band = np.zeros((H, W), np.float32); band[int(H * .14):int(H * .88)] = 1
    band = np.asarray(Image.fromarray((band * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.6))).astype(np.float32) / 255
    rng = np.random.default_rng(seed)
    yel = np.array([223, 190, 135.0], np.float32)          # #dfbe87
    streak = rng.normal(0, 1, (1, W, 1)).repeat(H, 0) * 6 + rng.normal(0, 3, (H, W, 1))
    a = a * (1 - band[..., None] * .85) + (yel + streak) * band[..., None] * .85
    tape = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    r = random.Random(seed)
    for li, l in enumerate(lines):
        for ci, ch in enumerate(l):
            if ch == ' ':
                continue
            g = Image.new('L', (int(adv) + 8, sz + 10), 0)
            ImageDraw.Draw(g).text((4, 3), ch, font=f, fill=255)
            dens = r.uniform(0.5, 0.9)
            if r.random() < 0.15:
                dens *= 0.7                                   # a weak strike
            g = g.point(lambda v, dd=dens: int(v * dd))
            x = 15 + ci * adv + r.uniform(-.6, .6); y = 7 + li * sz * 1.18 + r.uniform(-1.0, 1.0)
            tape.paste(Image.new('RGB', g.size, (118, 90, 60)), (int(x), int(y)), g)
    return tape


# ============================================================ geometry
TW, TH = 4000, 2250                  # table, in table px (1 out px = 1.94 table px in the spread view)
XC = 2000                            # coil axis
FW, FH = 1030, 1360                  # page face incl. 30 px punched strip
PY0 = 445
PAGE_BASE = {'L': (240, 230, 207), 'R': (243, 233, 210)}   # warm yellow-cream
TABLE_BASE = (226, 223, 217)
COVER_RED = (97, 14, 24)             # #610e18
V_SPREAD = (XC - 1240.0, 1125 - 697.5, XC + 1240.0, 1125 + 697.5)
V_WORK = (200.0, 112.5, 3800.0, 2137.5)
PRINT_MAX = (740, 540)
PRINT_TOP = 205
SLIP_M = 34


def side(p):
    return 'L' if p % 2 == 1 else 'R'


def face_origin(sd):
    return (XC - FW, PY0) if sd == 'L' else (XC, PY0)


def content_cx(sd):
    return FW / 2 - 15 if sd == 'L' else FW / 2 + 15


def print_size(k):
    a = clean_aspect(k)
    w, h = PRINT_MAX
    return (w, round(w / a)) if w / a <= h else (round(h * a), h)


# ============================================================ slips (print + tape + number)
class Slip:
    def __init__(self, k):
        self.k = k
        self.pw, self.ph = print_size(k)
        self.tape = typed_tape(CAPS[k], seed=300 + int(k))
        self.w = max(self.pw, self.tape.width) + 2 * SLIP_M
        self.tape_xy = ((self.w - self.tape.width) // 2, SLIP_M + self.ph + 72)
        self.num_y = self.tape_xy[1] + self.tape.height + 96
        self.h = self.num_y + NUM_H + 40
        self.print_xy = ((self.w - self.pw) / 2, SLIP_M)
        self.num_x = self.w / 2 - 20
        self.paper = to_img(fibre(self.w, self.h, (241, 231, 208), seed=500 + int(k)))
        a = np.full((self.h, self.w), 255, np.uint8)
        self.alpha = Image.fromarray(a)
        ink = Image.new('RGBA', (self.w, self.h), (0, 0, 0, 0))
        ink.paste(self.tape, self.tape_xy)
        anum = str(A_ORDER.index(k) + 1)
        st = word_strokes(anum, self.num_x, self.num_y, NUM_H, seed=700 + int(k))
        m, off = render_strokes(st, 1.0, 4.2, 700 + int(k), 'pen')
        ink_on(ink, m, off, PEN)
        self.ink = ink
        self.marks = []              # (kind, glyph, f0, frames, seed)

    def rest_xy(self, sd):
        ox, oy = face_origin(sd)
        return (ox + content_cx(sd) - self.w / 2, oy + PRINT_TOP - SLIP_M)

    def ink_at(self, f):
        """The slip's ink layer with the red marks written up to frame f."""
        if not self.marks:
            return self.ink
        im = self.ink.copy(); fq = 2 * (f // 2)
        for kind, gl, f0, nf, seed in self.marks:
            fr = min(1.0, max(0.0, (fq - f0 + 2) / nf))
            if fr <= 0:
                continue
            if kind == 'strike':
                r = random.Random(seed)
                x, y = self.num_x, self.num_y
                pts = [(x - 10 + r.uniform(-2, 2), y + NUM_H + 6), (x + 14, y + NUM_H * .5 + r.uniform(-3, 3)),
                       (x + 46 + r.uniform(-2, 2), y - 6)]
                m, off = render_strokes([catmull(pts)], fr, 6.0, seed, 'pencil')
            else:
                st = word_strokes(gl, self.num_x + 66, self.num_y - 4, NUM_H, seed)
                m, off = render_strokes(st, fr, 7.0, seed, 'pencil')
            ink_on(im, m, off, RED_PENCIL)
        return im


# ============================================================ handmade stock
_cache = {}


def page_face(p):
    """Face image of page p (1..8, 9 = inside back cover): cream stock, faint
    gutter, punched holes, red page number in the outer top corner."""
    if p in _cache:
        return _cache[p]
    sd = side(p)
    a = fibre(FW, FH, PAGE_BASE[sd], seed=20 + p)
    xx = np.arange(FW, dtype=np.float32)
    gut = (FW - xx) if sd == 'L' else xx
    a *= (0.972 + 0.028 * np.clip(gut / 90, 0, 1))[None, :, None]
    im = to_img(a); d = ImageDraw.Draw(im)
    hx = FW - 16 if sd == 'L' else 16
    for y in COIL_Y:
        d.ellipse([hx - 6, y - PY0 - 5, hx + 6, y - PY0 + 5], fill=(78, 72, 66))
    if p <= 8:
        x = FW - 115 if sd == 'R' else 70
        hand(im, str(p), x, 46, 40, seed=900 + p, color=RED_INK, width=3.0, tool='pen')
    _cache[p] = im
    return im


COIL_Y = [PY0 + 32 + i * (FH - 64) / 23 for i in range(24)]


def coil_layer():
    """Fine wire coil, 24 loops across the gutter (RGBA strip)."""
    if 'coil' in _cache:
        return _cache['coil']
    x0 = XC - 40; w = 80
    im = Image.new('RGBA', (w, FH + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for y in COIL_Y:
        yy = y - PY0 + 20
        d.arc([XC - 16 - x0 - 2, yy - 14 + 2, XC + 16 - x0 + 2, yy + 14 + 2], 180, 360, fill=(30, 28, 26, 70), width=5)
        d.arc([XC - 16 - x0, yy - 14, XC + 16 - x0, yy + 14], 180, 360, fill=(58, 58, 60, 255), width=4)
        d.arc([XC - 14 - x0, yy - 12, XC + 14 - x0, yy + 12], 210, 300, fill=(205, 205, 205, 230), width=1)
    _cache['coil'] = (im, (x0, PY0 - 20))
    return _cache['coil']


def cover_face():
    if 'cover' in _cache:
        return _cache['cover']
    rng = np.random.default_rng(7)
    a = fibre(FW, FH, COVER_RED, seed=8, sigma=5.0)
    peb = rng.normal(0, 1, (FH // 3 + 2, FW // 3 + 2))
    peb = np.asarray(Image.fromarray(((peb * 50) + 128).clip(0, 255).astype(np.uint8)).resize((FW, FH), Image.BICUBIC)).astype(np.float32) - 128
    a += (peb / peb.std() * 4.5)[..., None]                  # pebbled board grain
    im = to_img(a); d = ImageDraw.Draw(im)
    for y in COIL_Y:
        d.ellipse([16 - 6, y - PY0 - 5, 16 + 6, y - PY0 + 5], fill=(40, 8, 12))

    def label(box, seed):
        x0, y0, x1, y1 = box; r = random.Random(seed)
        lab = to_img(fibre(x1 - x0, y1 - y0, (246, 244, 238), seed, sigma=2.5))
        msk = Image.new('L', lab.size, 0)
        ImageDraw.Draw(msk).polygon([(r.uniform(0, 4), r.uniform(0, 4)), (lab.width - r.uniform(0, 4), r.uniform(0, 4)),
                                     (lab.width - r.uniform(0, 4), lab.height - r.uniform(0, 4)), (r.uniform(0, 4), lab.height - r.uniform(0, 4))], fill=255)
        im.paste(lab, (x0, y0), msk)
    label((130, 150, 930, 640), 11)
    label((110, 1010, 950, 1280), 12)
    for i, (t, x) in enumerate((('LA MACHINE', 205), ('À TUER', 325), ('LE TEMPS', 245))):
        hand(im, t, x, 215 + i * 140, 98, seed=40 + i, color=FELT, width=10.5, tool='felt', slant=0.02, wob=1.6, aspect=0.6)
    hand(im, '8 PHOTOGRAPHIES', 170, 1060, 46, seed=61, color=FELT, width=5.5, tool='felt', slant=0.08, wob=1.5, aspect=0.6)
    hand(im, '2 MONTAGES . 1 POOL', 170, 1160, 46, seed=62, color=FELT, width=5.5, tool='felt', slant=0.08, wob=1.5, aspect=0.6)
    _cache['cover'] = im
    return im


def table_base():
    if 'table' not in _cache:
        a = fibre(TW, TH, TABLE_BASE, seed=3, sigma=2.5)
        _cache['table'] = to_img(a)
    return _cache['table']


def sheet_img():
    """The loose sheet for the coda (same stock), with the two hand columns."""
    if 'sheet' in _cache:
        return _cache['sheet']
    w, h = 1760, 1240
    im = to_img(fibre(w, h, (242, 232, 209), seed=77))
    hand(im, 'A', 395, 90, 70, seed=81, color=PEN, width=4.5)
    hand(im, 'B', 1290, 90, 70, seed=82, color=PEN, width=4.5)
    for i in range(8):
        hand(im, A_ORDER[i], 360, 220 + i * 112, NUM_H, seed=1100 + i, color=PEN, width=4.0)
        hand(im, B_ORDER[i], 1260, 220 + i * 112, NUM_H, seed=1200 + i, color=PEN, width=4.0)
    _cache['sheet'] = im
    return im


# ============================================================ timeline (global frames)
def _tl(l5):
    s = {}; t = 0
    for name, n in (('S0', 72), ('S1', 72), ('S2', 18), ('S3', 480), ('S4', 18), ('S5', l5),
                    ('S6', 18), ('S7', 564), ('S8', 18), ('S9', 24), ('S10', 108)):
        s[name] = (t, t + n - 1); t += n
    s['total'] = t
    return s


# ---- S5 choreography (local frames, even = on twos).  Pages are slots.
#   R/L parks are on the table beside the notebook (no gutter room once a
#   print fills each page).  Stack-carrying keeps it to 4 page turns.
PARK = {'L1': (110, 470), 'L2': (165, 545), 'R1': (3090, 440), 'R2': (3125, 500), 'R3': (3160, 560), 'R4': (3195, 620)}
S5_TURNS = [  # (leaf, f0, frames, direction)  riffle back from spread 4, then work
    (3, 0, 8, -1), (2, 4, 8, -1), (1, 8, 8, -1),
    (1, 30, 8, +1), (2, 66, 8, +1), (2, 112, 8, -1), (1, 146, 8, -1)]
S5_MOVES = [  # (asset, f0, frames, from, to)
    ('01', 16, 12, ('page', 1), ('park', 'L1')),
    ('02', 20, 12, ('page', 2), ('park', 'R1')),
    ('03', 38, 12, ('page', 3), ('park', 'L2')),
    ('04', 42, 12, ('page', 4), ('park', 'R2')),
    ('02', 46, 12, ('park', 'R1'), ('page', 3)),
    ('05', 74, 12, ('page', 5), ('park', 'R3')),
    ('06', 78, 12, ('page', 6), ('park', 'R4')),
    ('03', 82, 12, ('park', 'L2'), ('page', 5)),
    ('01', 88, 12, ('park', 'L1'), ('page', 6)),
    ('06', 120, 12, ('park', 'R4'), ('page', 4)),
    ('05', 154, 12, ('park', 'R3'), ('page', 1)),
    ('04', 158, 12, ('park', 'R2'), ('page', 2)),
]
S5_MARKS = [  # (asset, strike f0, new number, write f0)
    ('02', 56, '3', 60), ('03', 96, '5', 100), ('01', 104, '6', 108), ('06', 134, '4', 138),
    ('05', 168, '1', 172), ('04', 176, '2', 180)]
S5_AB = (184, 188)            # strike 'A', write 'B' on page 1
S5_LEN = 188 + 8 + 20         # last stroke + 0.8 s hold on the re-numbered spread
TL = _tl(S5_LEN)


def segment_of(f):
    for k, v in TL.items():
        if k != 'total' and v[0] <= f <= v[1]:
            return k
    return None


# ============================================================ state resolution
SLIPS = {}


def slips():
    if not SLIPS:
        for k in A_ORDER:
            SLIPS[k] = Slip(k)
        g5 = TL['S5'][0]
        for k, fs, gl, fw in S5_MARKS:
            SLIPS[k].marks = [('strike', None, g5 + fs, 4, 1300 + int(k)), ('write', gl, g5 + fw, 8, 1400 + int(k))]
    return SLIPS


def leaf_theta(i, f):
    """Angle of leaf i (0 = flat on the right, pi = flat on the left)."""
    fq = 2 * (f // 2)
    th = 0.0
    c0 = TL['S0'][0] + 54                                    # cover flip, 6 drawings
    if i == 0:
        th = math.pi * _ease(min(1, max(0, (fq - c0 + 2) / 12)))
        # leaves open to spread 4 for S4..S5 start, then S5 riffles back
    if i in (1, 2, 3):
        th = 0.0
        if f >= TL['S3'][0]:                                 # during cut A the notebook is turned to s4 (unseen)
            th = math.pi
        g5 = TL['S5'][0]
        state = math.pi if f >= TL['S3'][0] else 0.0
        for leaf, f0, nf, dr in S5_TURNS:
            if leaf != i:
                continue
            u = (fq - (g5 + f0) + 2) / (nf + 2)
            if u <= 0:
                break
            tgt = math.pi if dr > 0 else 0.0
            state = state + (tgt - state) * _ease(min(1, u))
            if u < 1:
                return state
            state = tgt
        th = state
        if f >= TL['S7'][0]:                                 # during cut B the notebook is turned to s4 again (unseen)
            th = math.pi
    return th


def _ease(u):
    u = min(1, max(0, u)); return u * u * (3 - 2 * u)


def spread_of(f):
    """(left page, right page) on top, ignoring turning leaves."""
    ths = [leaf_theta(i, f) for i in range(5)]
    left = [i for i in range(5) if ths[i] >= math.pi - 1e-9]
    right = [i for i in range(5) if ths[i] <= 1e-9]
    lp = (2 * max(left) + 1) if left else None              # back of leaf i = page 2i+1
    rp = (2 * min(right)) if right else None                # front of leaf i = page 2i (0 = cover)
    turning = [(i, ths[i]) for i in range(5) if 1e-9 < ths[i] < math.pi - 1e-9]
    return lp, rp, turning


def slip_state(k, f):
    """('page', p) | ('table', (x, y), h) | ('move', (x, y), h).  Translation only."""
    fq = 2 * (f // 2); g5 = TL['S5'][0]
    page = A_ORDER.index(k) + 1
    if f > TL['S5'][1]:
        return ('page', B_ORDER.index(k) + 1, 0.0)
    loc = ('page', page)
    for kk, f0, nf, a, b in S5_MOVES:
        if kk != k:
            continue
        t0 = g5 + f0; ta = t0 + nf
        if fq < t0:
            break
        P0 = _where(a, k); P1 = _where(b, k)
        if fq < ta + 12:
            return ('move',) + _kin(P0, P1, fq - t0, nf, seed=int(k) * 100 + f0)
        loc = b
    if loc[0] == 'page':
        return ('page', loc[1], 0.0)
    return ('table', PARK[loc[1]], 0.0)


def _where(loc, k):
    if loc[0] == 'park':
        return PARK[loc[1]]
    return slips()[k].rest_xy(side(loc[1]))


def _kin(P0, P1, t, T, seed):
    """Hand trajectory: lift (shadow grows over 4 f), eased travel along a
    slightly irregular arc, spring settle at set-down (SCION 41)."""
    h = _ease(t / 4) if t < T - 2 else _ease(1 - (t - (T - 2)) / 6)
    dx, dy = P1[0] - P0[0], P1[1] - P0[1]; D = math.hypot(dx, dy) or 1
    ux, uy = dx / D, dy / D
    if t <= T:
        u = max(0.0, (t - 1) / (T - 1)); e = _ease(u) if u < 1 else 1.0
        e = e ** 0.9
        r = random.Random(seed + t)
        arc = 0.06 * D * math.sin(math.pi * e)
        nz = 2.5 * math.sin(math.pi * e)
        x = P0[0] + dx * e - uy * arc + r.uniform(-nz, nz)
        y = P0[1] + dy * e + ux * arc + r.uniform(-nz, nz)
    else:
        s = t - T
        amp = 7.0 * math.exp(-0.32 * s) * math.sin(1.05 * s)   # ~2.5 out px overshoot, gone in 12 f
        x, y = P1[0] + ux * amp, P1[1] + uy * amp
    return (x, y), max(0.0, min(1.0, h))


# ============================================================ camera
def lerp_view(Va, Vb, u, push=True):
    wa, wb = Va[2] - Va[0], Vb[2] - Vb[0]
    w = wa * (wb / wa) ** u if push else wa + (wb - wa) * u
    k = (wa - w) / (wa - wb) if abs(wa - wb) > 1e-9 else u
    ca = ((Va[0] + Va[2]) / 2, (Va[1] + Va[3]) / 2); cb = ((Vb[0] + Vb[2]) / 2, (Vb[1] + Vb[3]) / 2)
    cx = ca[0] + (cb[0] - ca[0]) * k; cy = ca[1] + (cb[1] - ca[1]) * k
    h = w * 9 / 16
    return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)


def _cubic(u):
    u = min(1, max(0, u)); return 4 * u ** 3 if u < .5 else 1 - (-2 * u + 2) ** 3 / 2


def w0_table_rect(k, page):
    """Table rect of asset k's W0 window when k rests on `page`."""
    s = slips()[k]; x, y = s.rest_xy(side(page))
    px0, py0 = x + s.print_xy[0], y + s.print_xy[1]
    W = w_frac(k, 'W0')
    return (px0 + W[0] * s.pw, py0 + W[1] * s.ph, px0 + W[2] * s.pw, py0 + W[3] * s.ph)


def view(f):
    """Camera rect in table px + whether jitter applies (jitter scale 0..1)."""
    seg = segment_of(f); a, b = TL[seg]
    if seg in ('S0', 'S1'):
        return V_SPREAD, 1.0
    if seg == 'S2':
        u = (f - a) / (b - a); return lerp_view(V_SPREAD, w0_table_rect('01', 1), _cubic(u)), 1 - _cubic(u)
    if seg == 'S4':
        u = (f - a) / (b - a); return lerp_view(w0_table_rect('08', 8), V_SPREAD, _cubic(u)), _cubic(u)
    if seg == 'S5':
        u = (f - a) / 16
        return lerp_view(V_SPREAD, V_WORK, _cubic(u), push=False), 1.0
    if seg == 'S6':
        u = (f - a) / (b - a); return lerp_view(V_WORK, w0_table_rect('05', 1), _cubic(u)), 1 - _cubic(u)
    if seg == 'S8':
        u = (f - a) / (b - a); return lerp_view(w0_table_rect('08', 8), V_SPREAD, _cubic(u)), _cubic(u)
    return V_SPREAD, 1.0


def jitter(f, V, amt):
    """Stop-motion table jitter: +-0.6 output px per drawing, notebook layer only."""
    d = f // 2
    r = random.Random(5000 + d); sc = (V[2] - V[0]) / OW
    jx, jy = r.uniform(-0.6, 0.6) * amt * sc, r.uniform(-0.6, 0.6) * amt * sc
    return (V[0] + jx, V[1] + jy, V[2] + jx, V[3] + jy)


# ============================================================ compositing
def to_out(V, R):
    S = OW / (V[2] - V[0])
    return ((R[0] - V[0]) * S, (R[1] - V[1]) * S, (R[2] - V[0]) * S, (R[3] - V[1]) * S), S


def put_print(out, k, R, V, led):
    """Paste print k (table rect R) re-sampled from the master pyramid at the
    current camera scale; only its visible part is sampled."""
    o, S = to_out(V, R)
    ox0, oy0 = max(0, math.floor(o[0])), max(0, math.floor(o[1]))
    ox1, oy1 = min(OW, math.ceil(o[2])), min(OH, math.ceil(o[3]))
    if ox1 <= ox0 or oy1 <= oy0:
        return
    fw, fh = o[2] - o[0], o[3] - o[1]
    box = ((ox0 - o[0]) / fw, (oy0 - o[1]) / fh, (ox1 - o[0]) / fw, (oy1 - o[1]) / fh)
    im = sample_print(k, box, (ox1 - ox0, oy1 - oy0))
    if ox0 > 0 or oy0 > 0 or ox1 < OW or oy1 < OH:
        # antialiased fractional edge: blend the 1-px border by coverage
        cov = np.ones((oy1 - oy0, ox1 - ox0), np.float32)
        cov[:, 0] *= min(1, ox0 + 1 - o[0]) if o[0] > 0 else 1
        cov[:, -1] *= min(1, o[2] - (ox1 - 1)) if o[2] < OW else 1
        cov[0, :] *= min(1, oy0 + 1 - o[1]) if o[1] > 0 else 1
        cov[-1, :] *= min(1, o[3] - (oy1 - 1)) if o[3] < OH else 1
        out.paste(im, (ox0, oy0), Image.fromarray((np.clip(cov, 0, 1) * 255).astype(np.uint8)))
    else:
        out.paste(im, (ox0, oy0))
    led.setdefault('prints', []).append(dict(asset=k, rect_out=[round(v, 3) for v in o], scale=round(fw / meta()[k]['pyr_size'][0], 5)))


def patch_to_out(out, patch, xy, V):
    """Composite an RGBA patch placed at table xy into the output (exact
    translation + uniform camera scale, filtered resample)."""
    pad = int(math.ceil((V[2] - V[0]) / OW)) + 2
    pp = Image.new('RGBA', (patch.width + 2 * pad, patch.height + 2 * pad), (0, 0, 0, 0))
    pp.paste(patch, (pad, pad)); patch = pp; xy = (xy[0] - pad, xy[1] - pad)
    o, S = to_out(V, (xy[0], xy[1], xy[0] + patch.width, xy[1] + patch.height))
    ox0, oy0 = max(0, math.ceil(o[0])), max(0, math.ceil(o[1]))
    ox1, oy1 = min(OW, math.floor(o[2])), min(OH, math.floor(o[3]))
    if ox1 <= ox0 or oy1 <= oy0:
        return
    box = ((ox0 - o[0]) / S, (oy0 - o[1]) / S, (ox1 - o[0]) / S, (oy1 - o[1]) / S)
    p = patch.resize((ox1 - ox0, oy1 - oy0), Image.LANCZOS, box=box)
    out.alpha_composite(p, (ox0, oy0))


def page_marks(f):
    """Page-level red pencil on page 1: 'A' (cut A), struck and 'B' at end of S5."""
    g5 = TL['S5'][0]; fq = 2 * (f // 2)
    return [('A', 1.0)], min(1, max(0, (fq - (g5 + S5_AB[0]) + 2) / 4)), min(1, max(0, (fq - (g5 + S5_AB[1]) + 2) / 8))


def draw_page_marks(img, ox, oy, f):
    _, fs, fw = page_marks(f)
    hand(img, 'A', ox + 70, oy + 120, NUM_H, seed=1501, color=RED_PENCIL, width=7.0, tool='pencil')
    if fs > 0:
        pts = catmull([(ox + 60, oy + 120 + NUM_H + 8), (ox + 90, oy + 150), (ox + 125, oy + 112)])
        m, off = render_strokes([pts], fs, 6.0, 1502, 'pencil'); ink_on(img, m, off, RED_PENCIL)
    if fw > 0:
        st = word_strokes('B', ox + 150, oy + 116, NUM_H, 1503)
        m, off = render_strokes(st, fw, 7.0, 1503, 'pencil'); ink_on(img, m, off, RED_PENCIL)


def face_full(p, f, with_prints):
    """Face image of page p with its resting slips (and prints at table res
    when it is a turning leaf)."""
    im = (cover_face() if p == 0 else page_face(p)).copy().convert('RGBA')
    if p == 1:
        draw_page_marks(im, 0, 0, f)
    for k, s in slips().items():
        st = slip_state(k, f)
        if st[0] == 'page' and st[1] == p:
            x, y = s.rest_xy(side(p)); ox, oy = face_origin(side(p))
            lx, ly = int(round(x - ox)), int(round(y - oy))
            im.alpha_composite(s.ink_at(f), (lx, ly))
            if with_prints:
                pr = sample_print(k, (0, 0, 1, 1), (s.pw, s.ph))
                im.paste(pr, (int(round(lx + s.print_xy[0])), int(round(ly + s.print_xy[1]))))
    return im


def homography(src, dst):
    A = []
    for (x, y), (u, v) in zip(src, dst):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); A.append([0, 0, 0, x, y, 1, -v * x, -v * y])
    b = [c for p in dst for c in p]
    return np.linalg.solve(np.array(A, float), np.array(b, float))


def turning_leaf(canvas, i, th, f, led):
    """Leaf i turning about the coil (rigid, foreshortened by the overhead
    camera; perspective from a camera ~9000 table px above)."""
    front = th < math.pi / 2
    p = 2 * i if front else 2 * i + 1
    if abs(math.cos(th)) < 0.03:                             # edge-on: the leaf is a lit sliver
        d = ImageDraw.Draw(canvas)
        d.rectangle([XC - 3, PY0 - 60, XC + 3, PY0 + FH + 60], fill=(214, 205, 186))
        d.line([XC + 4, PY0 - 60, XC + 4, PY0 + FH + 60], fill=(150, 140, 125), width=2)
        led.setdefault('turning', []).append(dict(leaf=i, theta=round(th, 4), face_page=None, note='edge-on'))
        return
    face = face_full(p, f, with_prints=True)
    lift = math.sin(th) * FW
    s = 9000 / (9000 - lift)                                 # nearer = larger
    xo = XC + math.cos(th) * FW * s
    cy = PY0 + FH / 2
    inner = [(XC, PY0), (XC, PY0 + FH)]
    outer = [(xo, cy - FH / 2 * s), (xo, cy + FH / 2 * s)]
    if front:   # face inner edge = x 0
        src = [(0, 0), (0, FH), (FW, FH), (FW, 0)]
        dst = [inner[0], inner[1], outer[1], outer[0]]
    else:       # back face lies on the left: inner edge = x FW
        src = [(FW, 0), (FW, FH), (0, FH), (0, 0)]
        dst = [inner[0], inner[1], outer[1], outer[0]]
    xs = [d[0] for d in dst]; ys = [d[1] for d in dst]
    bx0, by0, bx1, by1 = int(min(xs)) - 2, int(min(ys)) - 2, int(max(xs)) + 3, int(max(ys)) + 3
    # shadow on the page beneath, falling away from the camera-left light
    sh = Image.new('L', (TW, TH), 0)
    off = 30 + 60 * math.sin(th)
    ImageDraw.Draw(sh).polygon([(x + off * (1 if front else -1) * 0.5, y + off * 0.4) for x, y in dst], fill=int(70 * math.sin(th) + 10))
    sh = sh.crop((max(0, bx0 - 200), max(0, by0 - 200), min(TW, bx1 + 200), min(TH, by1 + 200)))
    sh = sh.filter(ImageFilter.GaussianBlur(14 + 20 * math.sin(th)))
    canvas.paste(Image.new('RGB', sh.size, (60, 50, 40)), (max(0, bx0 - 200), max(0, by0 - 200)), sh)
    dst_l = [(x - bx0, y - by0) for x, y in dst]
    H = homography(dst_l, src)                               # output -> input
    w = face.transform((bx1 - bx0, by1 - by0), Image.PERSPECTIVE, tuple(H), Image.BICUBIC)
    shade = 0.80 + 0.20 * abs(math.cos(th))
    rgb = Image.eval(w.convert('RGB'), lambda v: int(v * shade))
    canvas.paste(rgb, (bx0, by0), w.getchannel('A'))
    led.setdefault('turning', []).append(dict(leaf=i, theta=round(th, 4), face_page=p,
                                              note='prints on this leaf foreshortened by the physical turn'))


def lifted_patch(s, f, h, on_table):
    """Slip paper + ink + lift shadow, as an RGBA patch; returns (patch, offset)."""
    M = 110
    P = Image.new('RGBA', (s.w + 2 * M, s.h + 2 * M), (0, 0, 0, 0))
    if h > 0 or on_table:
        sa = Image.new('L', P.size, 0)
        dx, dy = 2 + 20 * h, 3 + 26 * h
        ImageDraw.Draw(sa).rectangle([M + dx, M + dy, M + dx + s.w, M + dy + s.h], fill=int(50 + 70 * h))
        sa = sa.filter(ImageFilter.GaussianBlur(1.5 + 22 * h))
        shadow = Image.new('RGBA', P.size, (45, 36, 28, 0)); shadow.putalpha(sa)
        P.alpha_composite(shadow)
    P.alpha_composite(s.paper.convert('RGBA'), (M, M))
    P.alpha_composite(s.ink_at(f), (M, M))
    return P, M


def notebook_frame(f):
    """One notebook frame (on twos: drawing = f // 2), with its ledger."""
    seg = segment_of(f)
    led = dict(frame=f, segment=seg, drawing=f // 2)
    if seg in ('S9', 'S10'):
        return coda_frame(f, led)
    fd = 2 * (f // 2) if seg not in ('S2', 'S4', 'S6', 'S8') else f   # camera moves on ones
    V, jam = view(f)
    V = jitter(fd, V, jam)
    led['view'] = [round(v, 3) for v in V]
    lp, rp, turning = spread_of(fd)
    led['spread'] = [lp, rp]
    canvas = table_base().copy()
    if rp is not None and rp <= 8:   # back cover edge under the right stack
        pass
    vis = []
    for p, sd in ((lp, 'L'), (rp, 'R')):
        if p is None:
            continue
        ox, oy = face_origin(sd)
        canvas.paste(cover_face() if p == 0 else page_face(p), (ox, oy))
        if p == 1:
            draw_page_marks(canvas, ox, oy, fd)
        vis.append(p)
    tl = bool(turning)
    lifted = []; rest_prints = []
    for k, s in slips().items():
        st = slip_state(k, fd)
        if st[0] == 'page':
            if st[1] not in vis:
                continue
            x, y = s.rest_xy(side(st[1]))
            canvas.paste(s.ink_at(fd), (int(round(x)), int(round(y))), s.ink_at(fd))
            rest_prints.append((k, (x, y)))
        elif st[0] == 'table':
            x, y = st[1]
            P, M = lifted_patch(s, fd, 0.0, True)
            canvas.paste(P, (int(round(x - M)), int(round(y - M))), P)
            rest_prints.append((k, (x, y)))
        else:
            lifted.append((k, st[1], st[2]))
    led['slips'] = {k: list(slip_state(k, fd)[:2]) if slip_state(k, fd)[0] == 'page' else
                    ['xy', [round(v, 3) for v in slip_state(k, fd)[1]], round(slip_state(k, fd)[2], 3)] for k in A_ORDER}
    if tl:
        # prints into the canvas at table res (z-order under the turning leaf)
        for k, (x, y) in rest_prints:
            s = slips()[k]
            canvas.paste(sample_print(k, (0, 0, 1, 1), (s.pw, s.ph)), (int(round(x + s.print_xy[0])), int(round(y + s.print_xy[1]))))
        cim, cxy = coil_layer(); canvas.paste(cim, cxy, cim)
        for i, th in turning:
            turning_leaf(canvas, i, th, fd, led)
    out = canvas.resize((OW, OH), Image.LANCZOS, box=V).convert('RGBA')
    if not tl:
        for k, (x, y) in rest_prints:
            s = slips()[k]
            put_print(out, k, (x + s.print_xy[0], y + s.print_xy[1], x + s.print_xy[0] + s.pw, y + s.print_xy[1] + s.ph), V, led)
        cim, cxy = coil_layer(); patch_to_out(out, cim, cxy, V)
    for k, (x, y), h in lifted:
        s = slips()[k]
        P, M = lifted_patch(s, fd, h, False)
        patch_to_out(out, P, (x - M, y - M), V)
        put_print(out, k, (x + s.print_xy[0], y + s.print_xy[1], x + s.print_xy[0] + s.pw, y + s.print_xy[1] + s.ph), V, led)
    return out.convert('RGB'), led


# ============================================================ coda (S9 sheet, S10 graph)
SHEET_REST = (XC - 880, 1125 - 620)
CODA_TAPE = None


def coda_tape():
    global CODA_TAPE
    if CODA_TAPE is None:
        ph = pool_hash()
        CODA_TAPE = typed_tape('même pool . sha256 %s...%s . 42 -> 8' % (ph[:8], ph[-4:]), seed=909, sz=27)
    return CODA_TAPE


def pool_hash():
    mf = HERE / 'pool-manifest.json'
    if mf.exists():
        try:
            return json.load(open(mf))['pool_hash']
        except Exception:
            pass
    return 'a3d308bd38b67cc3a54277bb50030206b8356b78fac7895b175dfc1b36eb2056'


def coda_frame(f, led):
    a9 = TL['S9'][0]; a10 = TL['S10'][0]; fq = 2 * (f // 2)
    V = jitter(fq, V_SPREAD, 1.0); led['view'] = [round(v, 3) for v in V]
    canvas = table_base().copy()
    for p, sd in ((7, 'L'), (8, 'R')):
        canvas.paste(page_face(p), face_origin(sd))
    for k in ('03', '01'):
        pass
    rest = []
    for k, s in slips().items():
        p = B_ORDER.index(k) + 1
        if p in (7, 8):
            x, y = s.rest_xy(side(p)); canvas.paste(s.ink_at(f), (int(round(x)), int(round(y))), s.ink_at(f)); rest.append((k, (x, y)))
    out = canvas.resize((OW, OH), Image.LANCZOS, box=V).convert('RGBA')
    for k, (x, y) in rest:
        s = slips()[k]
        put_print(out, k, (x + s.print_xy[0], y + s.print_xy[1], x + s.print_xy[0] + s.pw, y + s.print_xy[1] + s.ph), V, led)
    cim, cxy = coil_layer(); patch_to_out(out, cim, cxy, V)
    # the loose sheet slides in from the right, translation only, leading shadow
    u = min(1, max(0, (fq - a9 + 2) / 22))
    e = 1 - (1 - u) ** 2.4
    x = SHEET_REST[0] + (1 - e) * 2600; y = SHEET_REST[1] + (1 - e) * 60
    if u >= 1:
        sp = fq - (a9 + 20)
        x += -6.0 * math.exp(-0.35 * sp) * math.sin(1.0 * sp) if sp > 0 and sp < 12 else 0
    sheet = sheet_img().copy().convert('RGBA')
    if f >= a10:
        t = fq - a10
        for i, k in enumerate(A_ORDER):                       # 8 red lines, 6 f each
            j = B_ORDER.index(k)
            fr = min(1, max(0, (t - 12 - 6 * i + 2) / 6))
            if fr <= 0:
                continue
            r = random.Random(1600 + i)
            p0 = (520, 220 + i * 112 + NUM_H / 2 + r.uniform(-3, 3)); p1 = (1230, 220 + j * 112 + NUM_H / 2 + r.uniform(-3, 3))
            mid = ((p0[0] + p1[0]) / 2 + r.uniform(-8, 8), (p0[1] + p1[1]) / 2 + r.uniform(-6, 6))
            m, off = render_strokes([catmull([p0, mid, p1])], fr, 6.5, 1600 + i, 'pencil')
            ink_on(sheet, m, off, RED_PENCIL)
        tu = min(1, max(0, (t - 66 + 2) / 10))
        if tu > 0:                                            # the typed tape is laid on
            tp = coda_tape(); ty = 1130 - tp.height + (1 - (1 - tu) ** 2) * 0 + (1 - tu) * 260
            ta = Image.new('L', tp.size, 255)
            sheet.paste(tp, (int(880 - tp.width / 2), int(ty)), ta)
            led['tape'] = round(tu, 3)
    M = 120
    P = Image.new('RGBA', (sheet.width + 2 * M, sheet.height + 2 * M), (0, 0, 0, 0))
    sa = Image.new('L', P.size, 0); lead = 30 * (1 - e) + 4
    ImageDraw.Draw(sa).rectangle([M - lead, M + 6, M + sheet.width + 4, M + sheet.height + 8], fill=int(60 + 50 * (1 - e)))
    sa = sa.filter(ImageFilter.GaussianBlur(4 + 16 * (1 - e)))
    shp = Image.new('RGBA', P.size, (45, 36, 28, 0)); shp.putalpha(sa); P.alpha_composite(shp)
    P.alpha_composite(sheet, (M, M))
    patch_to_out(out, P, (x - M, y - M), V)
    led['sheet_xy'] = [round(x, 3), round(y, 3)]
    return out.convert('RGB'), led


# ============================================================ event stream
def events():
    g5 = TL['S5'][0]; ev = []
    ev.append(dict(f=TL['S0'][0] + 54, ev='cover_flip', frames=12, drawings=6))
    for leaf, f0, nf, dr in S5_TURNS:
        ev.append(dict(f=g5 + f0, ev='turn', leaf=leaf, direction='forward' if dr > 0 else 'back', frames=nf))
    for k, f0, nf, a, b in S5_MOVES:
        ev.append(dict(f=g5 + f0, ev='lift', asset=k, frm=list(a), frames=4))
        ev.append(dict(f=g5 + f0 + 1, ev='travel', asset=k, to=list(b), frames=nf - 1))
        ev.append(dict(f=g5 + f0 + nf, ev='setdown', asset=k, at=list(b)))
        ev.append(dict(f=g5 + f0 + nf, ev='settle', asset=k, frames=12, overshoot_px_out=2.5))
    for k, fs, gl, fw in S5_MARKS:
        ev.append(dict(f=g5 + fs, ev='strike', asset=k, mark=str(A_ORDER.index(k) + 1), frames=4, tool='red pencil'))
        ev.append(dict(f=g5 + fw, ev='write', asset=k, mark=gl, frames=8, tool='red pencil'))
    ev.append(dict(f=g5 + S5_AB[0], ev='strike', mark='A', page=1, frames=4, tool='red pencil'))
    ev.append(dict(f=g5 + S5_AB[1], ev='write', mark='B', page=1, frames=8, tool='red pencil'))
    for s, a in (('S2', '01'), ('S6', '05')):
        ev.append(dict(f=TL[s][0], ev='push', asset=a, frames=18, ends_on='asset %s frame 0 (W0)' % a))
    for s in ('S4', 'S8'):
        ev.append(dict(f=TL[s][0], ev='pull', asset='08', frames=18))
    ev.append(dict(f=TL['S9'][0], ev='slide', piece='loose sheet', frames=22))
    for i in range(8):
        ev.append(dict(f=TL['S10'][0] + 12 + 6 * i, ev='line', asset=A_ORDER[i], a_pos=i + 1, b_pos=B_ORDER.index(A_ORDER[i]) + 1, frames=6, tool='red pencil'))
    ev.append(dict(f=TL['S10'][0] + 66, ev='tape', text='même pool . sha256 ... . 42 -> 8', frames=10))
    return sorted(ev, key=lambda e: e['f'])


EVENTS = None


def check_final_slots():
    """SCION 40 'no wrong-ID swaps': after S5 the slip on page k is B[k]."""
    f = TL['S5'][1]
    got = {}
    for k in A_ORDER:
        st = slip_state(k, f)
        assert st[0] == 'page', (k, st)
        got[st[1]] = k
    assert [got[p] for p in range(1, 9)] == B_ORDER, got
    assert all(slip_state(k, f)[1] == A_ORDER.index(k) + 1 for k in ('07', '08'))
    return True


if __name__ == '__main__':
    if '--prep' in sys.argv:
        prep()
    else:
        print(json.dumps(TL)); print(check_final_slots())

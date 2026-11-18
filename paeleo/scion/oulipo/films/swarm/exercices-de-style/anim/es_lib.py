"""es_lib: the handmade page objects and puppets of « Exercices de style » (SCION U3 animator-pagemaker).

Everything here is HANDMADE in code (page, ghost type, mixed-face title setter, band, strip, cut-paper bench,
the ONE fixed service door, deckled vignette frame, GUICHET 3 + frosted pane, notice grid + stamp, envelope
interior, straight-ahead tear) or a loader/articulator for FORAGED pieces (Rol 57642 walker cut by #29/#31,
CC0 Edna C. Rex key).  No synthetic film grain anywhere: tooth/mottle exist only on the paper objects.

Import:  sys.path.insert(0, '<films>/swarm/exercices-de-style/anim'); import es_lib as L
All coordinates are 960x540 frame px, y down.  24 fps; puppets on twos.
"""
import json, math, hashlib
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

W, H, FPS = 960, 540, 24
ROOT = Path('/home/user/bolas/paeleo/scion/oulipo')
FILMS = ROOT / 'films'
SRC = FILMS / 'sources' / 'exercices-de-style'
MEDIA = SRC / 'anim'                      # RGBA objects + renders
PM = SRC / 'animator-pagemaker'           # this unit's foraged cut + editor media
HERE = Path(__file__).resolve().parent

# ------------------------------------------------------------------ palette (sampled from styleBook.webp)
PAGE = (253, 219, 140)      # #fddb8c page median
PAGE_HI = (254, 228, 152)   # #fee498
PAGE_TOP = (255, 239, 178)  # #ffefb2 lightest
GHOST = (253, 239, 177)     # #fdefb1  LIGHTER than the page
RED = (214, 40, 10)         # #d6280a
BLACK = (25, 19, 4)         # #191304
GREEN = (40, 55, 22)        # #283716 bus green
GREEN2 = (47, 74, 32)       # #2f4a20
CREAM = (239, 230, 200)     # #efe6c8 rail cream
BAND = (142, 132, 123)      # #8e847b
SHADOW = (92, 58, 14)       # warm lift-shadow
WHITE = (255, 255, 255)
BAND_Y, BAND_H = 432, 108   # 20 % of 540

# ------------------------------------------------------------------ type
FONTS = ROOT / 'assets' / 'fonts'
TT = '/usr/share/fonts/truetype/'
_fc = {}
def font(path, size):
    k = (str(path), int(size))
    if k not in _fc:
        _fc[k] = ImageFont.truetype(str(path), int(size))
    return _fc[k]
SANS = FONTS / 'instrument-sans.woff2'      # band (white humanist sans)
SERIF = FONTS / 'instrument-serif.woff2'
MONO = FONTS / 'ibm-plex-mono.woff2'
SERIF_I = TT + 'liberation/LiberationSerif-Italic.ttf'
SERIF_R = TT + 'liberation/LiberationSerif-Regular.ttf'
SERIF_B = TT + 'liberation/LiberationSerif-Bold.ttf'
TITLE_FACES = [str(SERIF), TT + 'liberation/LiberationSerif-Bold.ttf', TT + 'freefont/FreeSansBold.ttf',
               TT + 'crosextra/Caladea-Italic.ttf', '/usr/share/fonts/opentype/inter/Inter-Black.otf',
               TT + 'liberation/LiberationSerif-BoldItalic.ttf', TT + 'dejavu/DejaVuSerif-Bold.ttf']


def _noise(h, w, sigma, seed):
    r = np.random.RandomState(seed).normal(0, 1, (h, w)).astype(np.float32)
    im = Image.fromarray(((r * 40) + 128).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(sigma))
    a = np.asarray(im, np.float32) - 128
    return a / (np.abs(a).max() + 1e-6)


# ------------------------------------------------------------------ 1. the butter page
_page_cache = {}
def page(seed=1, size=(W, H)):
    """Butter page #fddb8c, lifting toward #fee498 at top-centre (the cover's light), plus a paper-fibre mottle.
    Measured median stays within ~2 dE of #fddb8c."""
    k = (seed, size)
    if k in _page_cache:
        return _page_cache[k].copy()
    w, h = size
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    g = np.exp(-(((xx - w * 0.5) / (w * 0.42)) ** 2) - ((yy / (h * 0.55)) ** 2))       # top-centre lift
    m = 0.6 * _noise(h, w, 28, seed) + 0.4 * _noise(h, w, 6, seed + 1)                  # cloudy mottle
    fib = 0.7 * _noise(h, w, 0.7, seed + 2) + 0.3 * _noise(h, w, 2.2, seed + 3)          # fibre tooth
    p = np.array(PAGE, np.float32); hi = np.array(PAGE_HI, np.float32); top = np.array(PAGE_TOP, np.float32)
    x = np.clip(0.55 * g + 0.18 * m, -0.2, 1.0)[..., None]
    a = np.where(x < 0.6, p + (hi - p) * (np.clip(x, -0.25, 0.6) / 0.6), hi + (top - hi) * ((x - 0.6) / 0.4) * 0.6)
    a = a - 2.2 + fib[..., None] * np.array([2.0, 2.4, 3.6], np.float32)                  # tooth reads in the blue
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    _page_cache[k] = im
    return im.copy()


def fibre(size, seed, amt=0.06):
    w, h = size
    n = 0.6 * _noise(h, w, 0.8, seed) + 0.4 * _noise(h, w, 3, seed + 1)
    return Image.fromarray((255 * (1 - amt + amt * (n * 0.5 + 0.5))).clip(0, 255).astype(np.uint8))


# ------------------------------------------------------------------ 2. ghost words (LIGHTER than page)
def ghost(word, xy=(40, -160), size=640, face=SERIF_R, sheet=(W + 400, H)):
    """A huge cropped word in #fdefb1 (lighter than the page) on its own plane (parallax 0.25)."""
    g = Image.new('RGBA', sheet, (0, 0, 0, 0))
    ImageDraw.Draw(g).text(xy, word, font=font(face, size), fill=GHOST + (255,))
    return g


# ------------------------------------------------------------------ 3. mixed-face, jumping-baseline title setter
def set_title(img, words, x=30, base=66, size=46, seed=3, letters=None, faces=None):
    """words: [(text, colour)], colour alternates RED/BLACK by word as on the cover.  Each letter gets its own face,
    size (x0.75-1.25) and baseline (+-8 px).  `letters` = how many letters are set so far (type-in), None = all.
    Returns the end x."""
    d = ImageDraw.Draw(img)
    r = np.random.RandomState(seed)
    faces = faces or TITLE_FACES
    n = 0
    for wi, (word, col) in enumerate(words):
        for ch in word:
            f_i = r.randint(len(faces)); sz = size * r.uniform(0.75, 1.25); dy = r.uniform(-8, 8)
            if letters is not None and n >= letters:
                return x
            f = font(faces[f_i], int(sz))
            d.text((x, base + dy), ch, font=f, fill=col, anchor='ls')
            x += d.textlength(ch, font=f) + 1
            n += 1
        x += size * 0.28
    return x


# ------------------------------------------------------------------ 4. the warm grey band
_band_cache = {}
def band(img, name, label='', clock=None):
    """#8e847b band, 108 px, light printed mottle; episode name in white Instrument Sans 40, label small caps 15."""
    if 'b' not in _band_cache:
        m = _noise(BAND_H, W, 6, 9) * 0.55 + _noise(BAND_H, W, 1.0, 10) * 0.45
        a = np.array(BAND, np.float32)[None, None, :] + (m[..., None] * 6.0)
        _band_cache['b'] = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    img.paste(_band_cache['b'], (0, BAND_Y))
    d = ImageDraw.Draw(img)
    d.text((30, BAND_Y + 58), name, font=font(SANS, 40), fill=WHITE, anchor='lm')
    if label:
        d.text((W - 30, BAND_Y + 82), label.upper(), font=font(SANS, 15), fill=WHITE, anchor='rm')
    if clock:
        d.text((W - 30, BAND_Y + 40), clock, font=font(SANS, 26), fill=WHITE, anchor='rm')


# ------------------------------------------------------------------ 5. six-cell vignette strip on the band
CELL = 64        # user review: "as thick and photographic as the cover's" (plan said 44; cover cell = 8 % of width)
def strip(img, cells, ring=None, x0=24, cell=CELL, gutter=3):
    """Six square cells sitting directly on the band (bottom edge = BAND_Y), thin cream gutters, red ring on `ring`
    (0-based).  `cells` are RGB images (frames of this film's own material), cropped square and resized."""
    y0 = BAND_Y - cell
    lay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).rectangle([x0 - gutter, y0 - gutter, x0 + len(cells) * (cell + gutter), BAND_Y], fill=CREAM + (255,))
    for i, c in enumerate(cells):
        c = square(c).resize((cell, cell), Image.LANCZOS).convert('RGB')
        lay.paste(c, (x0 + i * (cell + gutter), y0))
    img.alpha_composite(lift_shadow(lay, (1, -2), 2.5, 0.22)) if img.mode == 'RGBA' else None
    img.alpha_composite(lay) if img.mode == 'RGBA' else img.paste(lay, (0, 0), lay)
    if ring is not None:
        rx = x0 + ring * (cell + gutter)
        ImageDraw.Draw(img).rectangle([rx - 3, y0 - 3, rx + cell + 2, BAND_Y + 1], outline=RED, width=3)


def square(im):
    w, h = im.size; s = min(w, h)
    return im.crop(((w - s) // 2, (h - s) // 2, (w - s) // 2 + s, (h - s) // 2 + s))


# ------------------------------------------------------------------ 6. cut paper
def cut_paper(poly, color, seed, jitter=1.6, size=(W + 400, H), edge=True):
    """A scissor-cut polygon: edges subdivided and nudged once (cut once: it never boils), paper tooth multiplied
    in, and a 1 px darker cut edge (the card's thickness)."""
    r = np.random.RandomState(seed); pts = []
    poly = list(poly) + [poly[0]]
    for (x0, y0), (x1, y1) in zip(poly, poly[1:]):
        n = max(1, int(math.hypot(x1 - x0, y1 - y0) / 7))
        for k in range(n):
            f = k / n
            pts.append((x0 + (x1 - x0) * f + r.uniform(-jitter, jitter), y0 + (y1 - y0) * f + r.uniform(-jitter, jitter)))
    m = Image.new('L', size, 0); ImageDraw.Draw(m).polygon(pts, fill=255)
    m = m.filter(ImageFilter.GaussianBlur(0.6))
    col = Image.new('RGB', size, color)
    col = ImageChops.multiply(col, fibre(size, seed).convert('RGB'))
    if edge:
        e = ImageChops.subtract(m, m.filter(ImageFilter.MinFilter(3)))
        dark = Image.new('RGB', size, tuple(int(c * 0.62) for c in color))
        col = Image.composite(dark, col, e)
    col.putalpha(m)
    return col


def lift_shadow(layer, off=(2, 3), blur=3.5, alpha=0.30):
    """Soft offset shadow: the paper lifted off the page (the only shadow in the print light)."""
    a = layer.getchannel('A').filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * alpha))
    sh = Image.new('RGBA', layer.size, SHADOW + (0,)); sh.putalpha(a)
    out = Image.new('RGBA', layer.size, (0, 0, 0, 0)); out.alpha_composite(sh, off); return out


def with_shadow(layer, **kw):
    return Image.alpha_composite(lift_shadow(layer, **kw), layer)


# ------------------------------------------------------------------ 7. the cut-paper bench (bus green + cream)
def bench_low(top=352, bottom=BAND_Y, width=W + 400, seed=11):
    """S5c bench lip at key height: slats of #283716/#2f4a20 with cream gaps, full width (+400 for parallax)."""
    b = Image.new('RGBA', (width, H), (0, 0, 0, 0))
    hgt = bottom - top
    rows = [(0.00, 0.26, GREEN), (0.26, 0.33, CREAM), (0.33, 0.62, GREEN2), (0.62, 0.68, CREAM), (0.68, 1.02, GREEN)]
    for i, (a, c, col) in enumerate(rows):
        y0, y1 = top + a * hgt, top + c * hgt
        b.alpha_composite(cut_paper([(0, y0), (width, y0 - 2), (width, y1 - 2), (0, y1)], col, seed + i, size=(width, H)))
    return with_shadow(b, off=(0, -2), blur=4, alpha=0.35)


def bench_eye(x=260, y=300, w=300, seed=31):
    """S1/S2 bench seen at eye level: seat + back rail + two legs, cut paper."""
    b = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    parts = [([(x, y - 58), (x + w, y - 60), (x + w, y - 44), (x, y - 42)], GREEN),          # back rail
             ([(x + 4, y - 40), (x + w - 4, y - 42), (x + w - 4, y - 36), (x + 4, y - 34)], CREAM),
             ([(x - 6, y - 12), (x + w + 6, y - 14), (x + w + 4, y + 4), (x - 4, y + 6)], GREEN2),  # seat
             ([(x, y + 4), (x + w, y + 2), (x + w, y + 9), (x, y + 10)], CREAM),
             ([(x + 18, y + 8), (x + 32, y + 8), (x + 30, y + 62), (x + 16, y + 62)], GREEN),       # legs
             ([(x + w - 32, y + 8), (x + w - 18, y + 8), (x + w - 16, y + 62), (x + w - 30, y + 62)], GREEN),
             ([(x + 24, y - 34), (x + 34, y - 34), (x + 34, y - 12), (x + 24, y - 12)], GREEN),
             ([(x + w - 34, y - 34), (x + w - 24, y - 34), (x + w - 24, y - 12), (x + w - 34, y - 12)], GREEN)]
    for i, (p, c) in enumerate(parts):
        b.alpha_composite(cut_paper(p, c, seed + i, size=(W, H)))
    return with_shadow(b)


# ------------------------------------------------------------------ 8. THE service door: one RGBA asset, never transformed
DOOR_FILE = MEDIA / 'door.png'
def _make_door(path):
    dw, dh = 150, 300
    s = (dw, dh)
    d = Image.new('RGBA', s, (0, 0, 0, 0))
    d.alpha_composite(cut_paper([(4, 4), (dw - 4, 4), (dw - 4, dh), (4, dh)], CREAM, 21, size=s))         # frame
    d.alpha_composite(cut_paper([(14, 14), (dw - 14, 14), (dw - 14, dh), (14, dh)], GREEN, 22, size=s))
    d.alpha_composite(cut_paper([(28, 34), (dw - 28, 34), (dw - 28, 140), (28, 140)], GREEN2, 23, 1.2, size=s))
    d.alpha_composite(cut_paper([(28, 160), (dw - 28, 160), (dw - 28, dh - 20), (28, dh - 20)], GREEN2, 24, 1.2, size=s))
    d.alpha_composite(cut_paper([(22, 150), (34, 148), (34, 176), (22, 176)], CREAM, 25, 0.8, size=s))   # handle plate
    d.alpha_composite(cut_paper([(36, 62), (dw - 36, 62), (dw - 36, 90), (36, 90)], CREAM, 26, 0.8, size=s))
    ImageDraw.Draw(d).text((dw / 2 + 1, 76), 'SERVICE', font=font(TT + 'crosextra/Carlito-Bold.ttf', 14), fill=BLACK + (235,), anchor='mm')
    path.parent.mkdir(parents=True, exist_ok=True)
    d.save(path)

def door():
    """The single fixed door.  Created once on first call, then always loaded from disk.  Paste ONLY with
    paste_door(): integer offset, no resampling, so its pixels are identical in every frame (INV-DOOR)."""
    if not DOOR_FILE.exists():
        _make_door(DOOR_FILE)
    return Image.open(DOOR_FILE).convert('RGBA')

_DOOR = None
def paste_door(img, x, y, shadow=True):
    global _DOOR
    if _DOOR is None:
        _DOOR = door()
    x, y = int(round(x)), int(round(y))
    if shadow:
        sh = lift_shadow(_DOOR, (0, 0), 3.5, 0.30)
        img.alpha_composite(sh, (x + 2, y + 3))
    img.alpha_composite(_DOOR, (x, y))
    return (x, y, x + _DOOR.size[0], y + _DOOR.size[1])

def door_hash(frame, box, occluded_below=None):
    """Hash of the fully opaque door interior inside `box` (x0,y0,x1,y1) as pasted: the INV-DOOR frame test.
    `occluded_below` (frame y): rows at/below it are covered by a nearer plane (the bench lip + its lift shadow) and
    are excluded, since occlusion by a nearer layer is not a change of the door."""
    a = np.asarray(door().getchannel('A')) == 255
    if occluded_below is not None:
        a = a.copy(); a[max(0, int(occluded_below) - box[1]):] = False
    crop = np.asarray(frame.convert('RGB').crop(box))
    return hashlib.sha256(crop[a].tobytes()).hexdigest()[:16]


# ------------------------------------------------------------------ 9. deckled station-vignette frame
def deckle(photo, size=(300, 210), seed=41, border=9, tint=0.06):
    """Paste a real B&W photograph in a deckled (torn-cream) border.  Photo is converted to its own luminance
    (it is B&W) with a <=8 % warm tint toward the page; the border edge is torn once, straight-ahead."""
    w, h = size
    ph = tint_bw(photo.convert('RGBA'), tint).convert('RGB')
    ph = square_crop(ph, (w - 2 * border, h - 2 * border))
    r = np.random.RandomState(seed)
    def torn(x0, y0, x1, y1, amp):
        pts = []
        for (ax, ay), (bx, by) in [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]:
            n = int(math.hypot(bx - ax, by - ay) / 3)
            for k in range(n):
                f = k / n
                pts.append((ax + (bx - ax) * f + r.uniform(-amp, amp), ay + (by - ay) * f + r.uniform(-amp, amp)))
        return pts
    m = Image.new('L', size, 0); ImageDraw.Draw(m).polygon(torn(2, 2, w - 3, h - 3, 1.8), fill=255)
    out = Image.new('RGBA', size, CREAM + (255,))
    out = Image.composite(out, Image.new('RGBA', size, (0, 0, 0, 0)), m)
    out = Image.fromarray(np.asarray(out)); out.putalpha(m)
    tex = ImageChops.multiply(Image.new('RGB', size, CREAM), fibre(size, seed, 0.08).convert('RGB'))
    out = Image.merge('RGBA', tex.split() + (m,))
    out.paste(ph, (border, border))
    return with_shadow(out, off=(3, 4), blur=4, alpha=0.32)

def square_crop(im, size):
    tw, th = size; w, h = im.size
    s = max(tw / w, th / h)
    im = im.resize((int(w * s + 1), int(h * s + 1)), Image.LANCZOS)
    x = (im.size[0] - tw) // 2; y = (im.size[1] - th) // 2
    return im.crop((x, y, x + tw, y + th))


# ------------------------------------------------------------------ 10. GUICHET 3 + procedural frosted pane (S3)
def frosted_pane(size=(360, 250), seed=51, light=1.0):
    """Lit frosted glass, procedural: back-light falloff + acid-etch speckle + slight vertical drawn-glass ripple.
    Returns RGB.  The only back-lit object in the film (declared exception)."""
    w, h = size
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    fall = np.exp(-(((xx - w * 0.52) / (w * 0.75)) ** 2 + ((yy - h * 0.45) / (h * 0.9)) ** 2))
    speck = 0.6 * _noise(h, w, 0.6, seed) + 0.4 * _noise(h, w, 1.6, seed + 1)
    ripple = np.sin(xx / 7.0 + 0.9 * _noise(h, w, 12, seed + 2) * 3) * 0.5
    base = np.array([255, 241, 205], np.float32) * (0.80 + 0.20 * fall[..., None]) * light
    a = base + speck[..., None] * 7 + ripple[..., None] * 3
    return Image.fromarray(a.clip(0, 255).astype(np.uint8))

def shadow_through_glass(pane, sil_alpha, blur=6.0, density=0.78):
    """Composite a silhouette (L mask, same size as pane) BEHIND diffusion: blur it (5-9 px as he steps back),
    darken the pane by it.  The silhouette never sharpens beyond `blur` - no key shape can be read."""
    a = sil_alpha.filter(ImageFilter.GaussianBlur(blur))
    p = np.asarray(pane, np.float32)
    k = np.asarray(a, np.float32)[..., None] / 255.0 * density
    out = p * (1 - k) + np.array([62, 52, 40], np.float32) * k
    return Image.fromarray(out.clip(0, 255).astype(np.uint8))

def guichet(size=(440, 330), pane_box=(40, 62, 400, 312), seed=61):
    """Cut-paper ticket window: green surround, cream sill, stencil « GUICHET 3 » read BACKWARDS (we are inside).
    Returns RGBA with the pane area transparent (composite the lit pane under it)."""
    w, h = size
    g = Image.new('RGBA', size, (0, 0, 0, 0))
    g.alpha_composite(cut_paper([(0, 0), (w, 0), (w, h), (0, h)], GREEN, seed, size=size))
    x0, y0, x1, y1 = pane_box
    hole = Image.new('L', size, 255); ImageDraw.Draw(hole).rectangle([x0, y0, x1, y1], fill=0)
    g.putalpha(ImageChops.multiply(g.getchannel('A'), hole))
    g.alpha_composite(cut_paper([(x0 - 14, y1), (x1 + 14, y1), (x1 + 18, y1 + 14), (x0 - 18, y1 + 14)], CREAM, seed + 1, size=size))
    lab = Image.new('RGBA', (300, 40), (0, 0, 0, 0))
    ImageDraw.Draw(lab).text((150, 20), 'GUICHET 3', font=font(SANS, 30), fill=CREAM + (255,), anchor='mm')
    g.alpha_composite(lab.transpose(Image.FLIP_LEFT_RIGHT), ((w - 300) // 2, 12))
    for xx in np.linspace(x0, x1, 5)[1:-1]:                                      # glazing bars
        g.alpha_composite(cut_paper([(xx - 3, y0), (xx + 3, y0), (xx + 3, y1), (xx - 3, y1)], GREEN, seed + int(xx), 0.8, size=size))
    return g


# ------------------------------------------------------------------ 11. notice grid + red stamp (S4)
NOTICE_FIELDS = ['N°', 'HEURE', 'LIEU', 'OBJET', 'ACTION', 'ÉTAT']
NOTICE_COLS = [44, 70, 110, 130, 100, 190]
def notice(rows, chars=None, size=(660, 330), seed=71, footnote='cloche : consignée, non entendue'):
    """Printed notice card « AVIS — OBJET TROUVÉ »: header row + six rows of boxes, always drawn (empty boxes are
    visible before they fill).  rows = list of 6-field lists; chars = number of characters typed so far (None=all)."""
    w, h = size
    card = Image.new('RGBA', size, (0, 0, 0, 0))
    card.alpha_composite(cut_paper([(0, 0), (w, 0), (w, h), (0, h)], (250, 244, 226), seed, 1.0, size=size))
    d = ImageDraw.Draw(card)
    d.text((w / 2, 26), 'AVIS — OBJET TROUVÉ', font=font(SERIF_B, 24), fill=BLACK, anchor='mm')
    x0, y0, rh = 20, 52, 36
    xs = [x0]
    for cw in NOTICE_COLS: xs.append(xs[-1] + cw * (w - 40) / sum(NOTICE_COLS))
    for i, f in enumerate(NOTICE_FIELDS):
        d.text(((xs[i] + xs[i + 1]) / 2, y0 + 13), f, font=font(SANS, 12), fill=BLACK, anchor='mm')
    for r in range(7):
        d.line([(xs[0], y0 + r * rh + (0 if r == 0 else -10)), (xs[-1], y0 + r * rh + (0 if r == 0 else -10))], fill=BLACK, width=1)
    yb = y0 + 6 * rh + 26
    for xx in xs:
        d.line([(xx, y0), (xx, yb)], fill=BLACK, width=1)
    d.line([(xs[0], yb), (xs[-1], yb)], fill=BLACK, width=2)
    left = chars
    for r, row in enumerate(rows):
        for i, val in enumerate(row):
            if left is not None:
                if left <= 0: break
                val = val[:left]; left -= len(val)
            d.text((xs[i] + 5, y0 + 26 + r * rh + 7), val, font=font(MONO, 12), fill=BLACK, anchor='lm')
    d.text((xs[0], yb + 14), footnote, font=font(MONO, 11), fill=BLACK, anchor='lm')
    return with_shadow(card, off=(3, 4), blur=4, alpha=0.3)

def stamp(text='SUITE DONNÉE : NÉANT', squash=0.0, angle=-7, seed=81, size=30):
    """Red rubber stamp, ink unevenly taken (a real pad prints patchy): squash 0..1 flattens it for the 2-frame landing."""
    f = font(SANS, size); hh = int(round(64 * size / 30))
    tw = int(f.getlength(text)) + 40
    s = Image.new('L', (tw, hh), 0); d = ImageDraw.Draw(s)
    d.rectangle([3, 3, tw - 4, hh - 4], outline=255, width=4)
    d.text((tw / 2, hh / 2), text, font=f, fill=255, anchor='mm')
    ink = (_noise(hh, tw, 1.2, seed) * 0.5 + 0.5)
    a = (np.asarray(s, np.float32) * np.clip(0.55 + 0.6 * ink, 0, 1)).astype(np.uint8)
    im = Image.new('RGBA', (tw, hh), RED + (0,)); im.putalpha(Image.fromarray(a))
    if squash:
        im = im.resize((int(tw * (1 + 0.08 * squash)), int(hh * (1 - 0.25 * squash))), Image.LANCZOS)
    return im.rotate(angle, expand=True, resample=Image.BICUBIC)


# ------------------------------------------------------------------ 12. envelope interior + straight-ahead tear (S5a-b)
def envelope_interior(size=(W, BAND_Y), seed=91, lamp=1.0):
    """Inside the sealed envelope: lamp-through-paper brown, laid lines and fibre clouds of the envelope paper."""
    w, h = size
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    glow = np.exp(-(((xx - w * 0.62) / (w * 0.6)) ** 2 + ((yy - h * 0.35) / (h * 0.8)) ** 2))
    cloud = 0.6 * _noise(h, w, 18, seed) + 0.4 * _noise(h, w, 4, seed + 1)
    laid = 0.5 + 0.5 * np.sin(yy * 2 * math.pi / 5.0)
    base = np.array([58, 36, 18], np.float32) + np.array([96, 62, 28], np.float32) * (glow * lamp)[..., None]
    a = base * (1 + 0.10 * cloud[..., None] + 0.025 * laid[..., None])
    return Image.fromarray(a.clip(0, 255).astype(np.uint8))

class Tear:
    """Straight-ahead torn edge.  The rip is drawn frame by frame (re-cut every 2 frames): each new drawing extends
    the previous one's polyline by a new fibre-jagged segment, and the paper lips widen.  State is carried forward,
    so no two drawings are interpolations of each other.  mask(k) -> L image: 255 = opened (light)."""
    def __init__(self, n_frames=40, size=(W, BAND_Y), seed=101, y=200, x0=-20, x1=W + 20):
        self.size = size; self.r = np.random.RandomState(seed); self.drawings = []
        pts = [(x0, y)]
        n_draw = n_frames // 2
        for i in range(n_draw):
            f = (i + 1) / n_draw
            target = x0 + (x1 - x0) * min(1.0, f * 1.25)
            while pts[-1][0] < target:
                px, py = pts[-1]
                pts.append((px + self.r.uniform(4, 11), py + self.r.normal(0, 2.6) + 0.15 * (y - py)))
            open_ = 46 * (f ** 1.4)                                       # lips part
            upper = [(x, yy - open_ * (0.4 + 0.6 * self.r.rand()) * min(1, (x - x0) / 160 + 0.2)) for x, yy in pts]
            lower = [(x, yy + open_ * (0.5 + 0.5 * self.r.rand()) * min(1, (x - x0) / 160 + 0.2)) for x, yy in pts]
            m = Image.new('L', size, 0)
            if len(pts) > 1:
                ImageDraw.Draw(m).polygon(upper + lower[::-1], fill=255)
            fringe = m.filter(ImageFilter.MaxFilter(3))
            self.drawings.append((m, fringe))
    def mask(self, k):
        i = min(len(self.drawings) - 1, max(0, k // 2))
        return self.drawings[i]


# ------------------------------------------------------------------ 13. foraged pieces: tint, place
def tint_bw(img, amt=0.08):
    """The Rol prints are genuinely B&W (measured chroma < 6): take luminance, add a <=8 % warm tint toward the page."""
    a = np.asarray(img.convert('RGBA'), np.float32).copy()
    L = a[..., :3] @ np.array([0.299, 0.587, 0.114], np.float32)
    g = np.repeat(L[..., None], 3, 2)
    a[..., :3] = g * (1 - amt) + (g * np.array(PAGE, np.float32) / 255.0) * amt
    return Image.fromarray(a.clip(0, 255).astype(np.uint8))

def R(angle_deg, v):
    th = math.radians(angle_deg); c, s = math.cos(th), math.sin(th)
    return (c * v[0] - s * v[1], s * v[0] + c * v[1])

def place(canvas, img, origin, pivot, world, angle_deg, scale, alpha=1.0):
    """Paste RGBA piece so its pivot (source coords; piece's top-left at `origin`) lands on `world`, rotated by
    angle (+ turns the piece's 'down' toward -x) and scaled.  Bicubic, one resample per frame."""
    th = math.radians(angle_deg); c, s = math.cos(th), math.sin(th)
    ox, oy = origin; px, py = pivot; wx, wy = world
    a, b, d, e = c / scale, s / scale, -s / scale, c / scale
    A = (a, b, px - ox - a * wx - b * wy, d, e, py - oy - d * wx - e * wy)
    lay = img.transform(canvas.size, Image.AFFINE, A, resample=Image.BICUBIC)
    if alpha < 1.0:
        lay.putalpha(lay.getchannel('A').point(lambda v: int(v * alpha)))
    canvas.alpha_composite(lay)


# ------------------------------------------------------------------ 14. the visitor puppet (Rol 57642 walker, FK + drawing substitution)
class Visitor:
    """Articulated cutout from rig_walker.json (#29 cut, #32 FK).  Joints: hip (root), shoulder (arm), neck (head),
    hem pin (coat skirt), two hip pins for the legs.  Legs use DRAWING SUBSTITUTION from the print's own two legs:
    leg_straight in stance, leg_bent in swing; the far leg is the same paper, printed darker."""
    def __init__(self, rig_path=PM / 'cut' / 'rig_walker.json', tint=0.08):
        self.rig = json.load(open(rig_path)); base = Path(rig_path).parent
        self.P = {}
        for k, v in self.rig['pieces'].items():
            im = tint_bw(Image.open(base / v['file']), tint)
            self.P[k] = dict(img=im, origin=tuple(v['origin']), pivot=tuple(v['pivot']))
        for k in ('leg_straight', 'leg_bent'):
            a = np.asarray(self.P[k]['img'], np.float32).copy(); a[..., :3] *= 0.74
            self.P[k + '_far'] = dict(self.P[k], img=Image.fromarray(a.clip(0, 255).astype(np.uint8)))
        self.hip = tuple(self.rig['hip']); self.leg = self.rig['leg_length']; self.height = self.rig['figure_height']

    def xf(self, hipw, sc, lean, p):
        v = R(lean, (p[0] - self.hip[0], p[1] - self.hip[1]))
        return (hipw[0] + sc * v[0], hipw[1] + sc * v[1])

    def draw(self, canvas, hipw, sc, pose, shadow=True):
        """pose: dict(lean, head, arm, hem, legs={'near': (angle, 'stance'|'swing'), 'far': (...)})."""
        lay = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
        lean = pose.get('lean', 0.0)
        for side in ('far', 'near'):
            ang, ph = pose['legs'][side]
            key = 'leg_straight' if ph == 'stance' else 'leg_bent'
            pc = self.P[key + ('_far' if side == 'far' else '')]
            j = self.xf(hipw, sc, lean, (self.hip[0] + (-8 if side == 'far' else 8) * 1.5, self.hip[1]))
            place(lay, pc['img'], pc['origin'], self.P[key]['pivot'], j, ang, sc)
        P = self.P
        place(lay, P['hem']['img'], P['hem']['origin'], P['hem']['pivot'], self.xf(hipw, sc, lean, P['hem']['pivot']), lean + pose.get('hem', 0.0), sc)
        place(lay, P['torso']['img'], P['torso']['origin'], P['torso']['pivot'], self.xf(hipw, sc, lean, P['torso']['pivot']), lean, sc)
        if pose.get('own_arm', True):                 # False while the close-up arm (same piece) is out in S5c
            place(lay, P['arm']['img'], P['arm']['origin'], P['arm']['pivot'], self.xf(hipw, sc, lean, P['arm']['pivot']), lean + pose.get('arm', 0.0), sc)
        place(lay, P['head']['img'], P['head']['origin'], P['head']['pivot'], self.xf(hipw, sc, lean, P['head']['pivot']), lean + pose.get('head', 0.0), sc)
        if shadow:
            canvas.alpha_composite(lift_shadow(lay, (2, 3), 3, 0.26))
        canvas.alpha_composite(lay)
        return lay

    def silhouette_pieces(self):
        """Reiniger S3 puppet: each piece's matte made a flat black card (rotoscoped contour of the real walker),
        pins at the same joints.  Returns a Visitor-like object drawing pure black shapes."""
        sil = Visitor.__new__(Visitor); sil.rig = self.rig; sil.hip = self.hip; sil.leg = self.leg; sil.height = self.height
        sil.P = {}
        for k, v in self.P.items():
            a = v['img'].getchannel('A').point(lambda x: 255 if x > 110 else 0).filter(ImageFilter.MedianFilter(5))
            im = Image.new('RGBA', a.size, (12, 10, 8, 0)); im.putalpha(a)
            sil.P[k] = dict(v, img=im)
        return sil


class Walk:
    """FK walk with planted (non-sliding) feet, simulated on twos.  Leg = rigid pendulum from the hip pin; stance
    leg sweeps +A -> -A (hip passes over the planted foot), swing leg uses the bent drawing.  Scale falls 3 % per
    step (recession), ground line rises toward the horizon, bob comes from the pendulum (L(1-cos A)) + 'bob' px."""
    def __init__(self, x0, ground0, sc0, t0, step=0.44, amp=22.0, fps=FPS, horizon=226.0, recede=0.97, bob=6.0,
                 direction=-1, dur=12.0, leg=None):
        self.f = {}; self.contacts = []
        x = x0; planted = None; prev = None
        for k in range(0, int(dur * fps) + 2, 2):
            t = k / fps; u = t - t0
            n = max(0.0, u / step)
            sc = sc0 * (recede ** n)
            g = horizon + (ground0 - horizon) * sc / sc0
            L = leg * sc
            if u < 0:
                self.f[k] = dict(hip=(x, g - L), sc=sc, legs={'near': (0.0, 'stance'), 'far': (0.0, 'stance')}, phase=0.0, steps=0.0)
                continue
            ph = (u / (2 * step))
            pn = ph % 1.0; pf = (ph + 0.5) % 1.0
            def ang(p):     # stance first half, swing second half; + angle swings foot toward -x (walking left)
                if p < 0.5:
                    return direction * amp * (1 - 4 * p) * -1, 'stance'
                s = (p - 0.5) / 0.5
                return direction * amp * (-1 + 2 * (0.5 - 0.5 * math.cos(math.pi * s))) * -1, 'swing'
            an, sn = ang(pn); af, sf = ang(pf)
            stance = 'near' if sn == 'stance' else 'far'
            a_st = an if stance == 'near' else af
            foot_rel = R(a_st, (0, L))
            if stance != prev:
                planted = x + foot_rel[0]
                self.contacts.append(t)
                prev = stance
            x = planted - foot_rel[0]
            hy = g - foot_rel[1] - bob * 0.5 * (1 - math.cos(2 * math.pi * 2 * ph)) * sc / sc0
            self.f[k] = dict(hip=(x, hy), sc=sc, legs={'near': (an, sn), 'far': (af, sf)}, phase=ph, steps=n)

    def at(self, k):
        kk = (k // 2) * 2
        return self.f[min(kk, max(self.f))]


# ------------------------------------------------------------------ 15. the key (CC0 watercolour)
KEY_FILE = SRC / 'test-shot' / 'key_cut.png'
def key(length=380.0):
    """Edna C. Rex's painted key, cut with its bow hole open, bow LEFT, bit up-right; returns (img, w, h)."""
    k = Image.open(KEY_FILE).convert('RGBA').rotate(-90, expand=True, resample=Image.BICUBIC)
    s = length / k.size[0]
    k = k.resize((int(k.size[0] * s), int(k.size[1] * s)), Image.LANCZOS)
    return k


# ------------------------------------------------------------------ 16. #41 damped settle
def settle(n=10, a0=6.0, bounce_frame=4, bounce_px=3.0):
    """6 deg -> 0 over n frames: under-damped rotation (one overshoot), one 3 px bounce peaking on frame 4,
    energy exactly zero from frame n on.  Returns [(angle, dy)] per frame."""
    out = []
    for f in range(n + 1):
        x = f / n
        ang = a0 * math.exp(-4.2 * x) * math.cos(math.pi * 1.35 * x) * (1 - x)
        dy = -bounce_px * math.sin(math.pi * (f - 2) / 4) if 2 <= f <= 6 else 0.0
        out.append((round(ang, 3), round(dy, 3)))
    out[-1] = (0.0, 0.0)
    return out


# ------------------------------------------------------------------ 17. measurement helpers
def lab(rgb):
    c = np.asarray(rgb, np.float64) / 255.0
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = c @ M.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)

def dE(a, b):
    return float(np.linalg.norm(lab(a) - lab(b)))

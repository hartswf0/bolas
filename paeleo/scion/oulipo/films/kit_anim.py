"""Small helpers shared by teuf-teuf, bang-bang, a-morning-stroll,
exercices-de-style and la-belle-hortense. Built on kit.py, which stays untouched."""
import math
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from kit import *  # noqa


def contact(slug, cols=3, scale=0.5, times=None):
    """Contact sheet of stills in films/stills/<slug>/ -> films/stills/<slug>_sheet.png"""
    d = HERE / "stills" / slug
    files = [d / f"{t:06.2f}.png" for t in times] if times else sorted(d.glob("*.png"))
    if not files:
        return
    w, h = int(W * scale), int(H * scale)
    rows = (len(files) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * w + (cols + 1) * 6, rows * (h + 22) + 6), (60, 60, 60))
    dd = ImageDraw.Draw(sheet)
    for k, f in enumerate(files):
        im = Image.open(f).resize((w, h), Image.LANCZOS)
        x, y = 6 + (k % cols) * (w + 6), 6 + (k // cols) * (h + 22)
        sheet.paste(im, (x, y))
        dd.text((x + 4, y + h + 3), f.stem, fill=(230, 230, 230), font=font("mono", 13))
    out = HERE / "stills" / f"{slug}_sheet.png"
    sheet.save(out)
    print("sheet ->", out)


def run(film):
    """Render, or write stills + a contact sheet when called with --stills."""
    film.render()
    if len(sys.argv) > 1 and sys.argv[1] == "--stills":
        times = [float(x) for x in sys.argv[2:]]
        contact(film.slug, cols=2 if len(times) <= 4 else 3, scale=0.75 if len(times) <= 4 else 0.5, times=times or None)


def poly_mask(size, pts):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).polygon([tuple(p) for p in pts], fill=255)
    return m


def hatch_poly(ink, pts, gap=6, angle=45, color=INK, width=1, alpha=255, jitter=0.6, cross=False):
    """Engraver's hatching clipped to an arbitrary polygon (works on its bounding box)."""
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    x0, y0 = int(max(0, min(xs) - 2)), int(max(0, min(ys) - 2))
    x1, y1 = int(min(ink.w, max(xs) + 3)), int(min(ink.h, max(ys) + 3))
    if x1 <= x0 or y1 <= y0:
        return
    bw, bh = x1 - x0, y1 - y0
    layer = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    dd = ImageDraw.Draw(layer)
    cx, cy = bw / 2, bh / 2
    span = int(math.hypot(bw, bh) / 2) + gap
    # anchor the hatch phase to the canvas so neighbouring shapes line up
    for ang in ((angle, angle + 90) if cross else (angle,)):
        a = math.radians(ang)
        dx, dy = math.cos(a), math.sin(a)
        off = ((x0 + cx) * -dy + (y0 + cy) * dx) % gap
        for k in range(-span, span + gap, gap):
            kk = k - off
            ox, oy = cx - dy * kk, cy + dx * kk
            p = (ox - dx * span + ink.j(jitter), oy - dy * span + ink.j(jitter))
            q = (ox + dx * span + ink.j(jitter), oy + dy * span + ink.j(jitter))
            dd.line([p, q], fill=tuple(color[:3]) + (alpha,), width=max(1, int(width)))
    m = Image.new("L", (bw, bh), 0)
    ImageDraw.Draw(m).polygon([(px - x0, py - y0) for px, py in pts], fill=255)
    layer.putalpha(ImageChops.multiply(layer.getchannel("A"), m))
    ink.img.paste(layer, (x0, y0), layer)
    ink.d = ImageDraw.Draw(ink.img, "RGBA")


def glow(ink, sheet, radius=6, strength=1.6):
    """Additive glow: blur a drawn RGBA sheet and add it (screen-era light)."""
    base = ink.img.convert("RGB")
    rgb = Image.new("RGB", base.size, (0, 0, 0))
    rgb.paste(sheet.img, (0, 0), sheet.img)
    blur = rgb.filter(ImageFilter.GaussianBlur(radius))
    blur = blur.point(lambda v: min(255, int(v * strength)))
    out = ImageChops.add(base, blur)
    out = ImageChops.add(out, rgb)
    ink.img = out
    ink.d = ImageDraw.Draw(ink.img, "RGBA")


def typed(s, t, a, cps=28):
    """Prefix of s typed from time a at cps characters per second."""
    if t < a:
        return ""
    return s[: int((t - a) * cps)]


def wrap(ink, s, kind, size, width):
    words, lines, cur = s.split(" "), [], ""
    for w_ in words:
        cand = (cur + " " + w_).strip()
        if ink.text_size(cand, kind, size)[0] > width and cur:
            lines.append(cur)
            cur = w_
        else:
            cur = cand
    if cur:
        lines.append(cur)
    return lines


def sub_frame(fn, t, i, size=(W, H), boil=8, wobble=1.2, seed=0, grain=False):
    """Draw fn(t, ink) on a separate canvas and return the PIL image."""
    ink = Ink(t, i, size, boil, wobble, seed)
    ink.paper()
    fn(t, ink)
    ink._grain = grain
    return ink.finish()


# ------------------------------------------------------------ handwriting ---

_hand_cache = {}


def hand_word(word, size, color, seed=0, slant=0.2, weight=0):
    """A word that looks pen-written: drawn with the sans at 2x, warped by a slow wobble,
    slanted, randomly scaled, then thickened a touch like felt-tip bleed."""
    key = (word, size, color, seed, slant, weight)
    if key in _hand_cache:
        return _hand_cache[key]
    rs = np.random.RandomState((hash(word) + seed * 7919) % (2 ** 31))
    S = 2
    f = font("sans", int(size * S * rs.uniform(0.94, 1.06)))
    tmp = ImageDraw.Draw(Image.new("L", (1, 1)))
    bx = tmp.textbbox((0, 0), word, font=f)
    w, h = bx[2] - bx[0] + 40 * S, int(size * S * 1.9)
    m = Image.new("L", (w, h), 0)
    dm = ImageDraw.Draw(m)
    cx = 10 * S - bx[0]
    for ch in word:  # letter by letter: each a little higher or lower, larger or smaller
        fc = font("sans", max(6, int(f.size * rs.uniform(0.9, 1.1))))
        dm.text((cx, int(size * S * 0.35) + rs.uniform(-1.6, 1.6) * S + (f.size - fc.size) * 0.8), ch, font=fc, fill=255)
        cx += fc.getlength(ch) * rs.uniform(0.94, 1.04)
    a = np.asarray(m, np.float32)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    ph1, ph2 = rs.uniform(0, 6.28, 2)
    dx = 0.7 * S * np.sin(yy / (16.0 * S) + ph1) + 0.5 * S * np.sin(xx / (6.0 * S)) + slant * (h * 0.6 - yy)
    dy = 1.2 * S * np.sin(xx / (11.0 * S) + ph2)
    sx = np.clip(xx - dx, 0, w - 1).astype(np.int32)
    sy = np.clip(yy - dy, 0, h - 1).astype(np.int32)
    warped = Image.fromarray(a[sy, sx].astype(np.uint8), "L")
    if weight:
        warped = warped.filter(ImageFilter.MaxFilter(3))
    warped = warped.resize((w // S, h // S), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.35))
    im = Image.new("RGBA", warped.size, tuple(color[:3]) + (0,))
    im.putalpha(warped.point(lambda v: min(255, int(v * 1.15))))
    _hand_cache[key] = im
    return im


def hand_text(ink, xy, s, size=24, color=(30, 30, 40), width=None, seed=0, line_gap=1.35, alpha=1.0, rot=0.0):
    """Lay handwritten words along lines (wrapping at width). Returns the y after the last line."""
    x0, y = xy
    x = x0
    rs = random.Random(seed)
    for k, word in enumerate(s.split(" ")):
        if word == "\n":
            x, y = x0, y + size * line_gap
            continue
        im = hand_word(word, size, color, seed + k)
        ww = im.width - 36
        if width and x + ww - x0 > width and x > x0:
            x, y = x0 + rs.uniform(-3, 3), y + size * line_gap
        jitter = rs.uniform(-2, 2)
        if rot:
            im = im.rotate(rot, expand=True, resample=Image.BICUBIC)
        ink.paste(im, (x, y - size * 0.35 + jitter), alpha=alpha)
        x += ww + size * 0.26 + rs.uniform(-1, 2)
    return y + size * line_gap

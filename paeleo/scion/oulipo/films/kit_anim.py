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

"""Shared comic-page helpers: hand-inked borders, balloons, captions."""
import math, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONTS = '/home/user/bolas/paeleo/scion/oulipo/assets/fonts/'
PAPER = (247, 244, 236)
INK = (18, 17, 16)


def font(size, kind='sans'):
    f = {'sans': 'instrument-sans.woff2', 'serif': 'instrument-serif.woff2', 'mono': 'ibm-plex-mono.woff2'}[kind]
    return ImageFont.truetype(FONTS + f, size)


def wobble_line(d, p, q, w=4, rng=None, col=INK, amp=1.1):
    rng = rng or np.random.default_rng(0)
    n = max(2, int(math.dist(p, q) / 18))
    pts = []
    for i in range(n + 1):
        t = i / n
        pts.append((p[0] + (q[0] - p[0]) * t + rng.normal(0, amp), p[1] + (q[1] - p[1]) * t + rng.normal(0, amp)))
    d.line(pts, fill=col, width=w, joint='curve')


def border(d, box, w=5, rng=None):
    x0, y0, x1, y1 = box
    for p, q in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        wobble_line(d, p, q, w, rng)


def balloon(img, cx, cy, text, tail, size=26, pad=(22, 14), rng=None, clip=None, fill=PAPER, kind='sans'):
    """Draw a speech balloon centred at cx,cy with a tail pointing at `tail` (may lie outside the panel)."""
    rng = rng or np.random.default_rng(1)
    d = ImageDraw.Draw(img)
    f = font(size, kind)
    lines = text.split('\n')
    bbs = [d.textbbox((0, 0), l, font=f) for l in lines]
    tw = max(b[2] - b[0] for b in bbs); lh = size * 1.15; th = lh * len(lines)
    rx, ry = (tw / 2) * 1.2 + pad[0], (th / 2) * 1.25 + pad[1]
    layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    pts = []
    for k in range(72):
        a = 2 * math.pi * k / 72
        r = 1 + rng.normal(0, 0.012)
        pts.append((cx + rx * r * math.cos(a), cy + ry * r * math.sin(a)))
    # tail: a wedge from the balloon edge to the target
    ang = math.atan2(tail[1] - cy, tail[0] - cx)
    bx, by = cx + rx * 0.8 * math.cos(ang), cy + ry * 0.8 * math.sin(ang)
    nx, ny = -math.sin(ang), math.cos(ang)
    wedge = [(bx + nx * 16, by + ny * 16), tail, (bx - nx * 16, by - ny * 16)]
    ld.polygon(wedge, fill=INK)
    ld.polygon(pts, fill=INK)
    # inner fill (inset)
    inner = [(cx + (x - cx) * (1 - 4.5 / rx), cy + (y - cy) * (1 - 4.5 / ry)) for x, y in pts]
    w2 = [(bx + nx * 11, by + ny * 11), (tail[0] - math.cos(ang) * 9, tail[1] - math.sin(ang) * 9), (bx - nx * 11, by - ny * 11)]
    ld.polygon(w2, fill=fill + (255,))
    ld.polygon(inner, fill=fill + (255,))
    y = cy - th / 2
    for l, b in zip(lines, bbs):
        ld.text((cx - (b[2] - b[0]) / 2, y), l, font=f, fill=INK)
        y += lh
    if clip:
        m = Image.new('L', img.size, 0); ImageDraw.Draw(m).rectangle(clip, fill=255)
        a = layer.split()[3]
        layer.putalpha(Image.fromarray(np.minimum(np.asarray(a), np.asarray(m))))
    img.alpha_composite(layer) if img.mode == 'RGBA' else img.paste(layer, (0, 0), layer)


def caption(img, box, text, size=22, kind='sans'):
    d = ImageDraw.Draw(img)
    d.rectangle(box, fill=(250, 246, 226), outline=INK, width=3)
    d.text((box[0] + 10, box[1] + 6), text, font=font(size, kind), fill=INK)


def ink_to_rgb(L, paper=PAPER, ink=INK):
    a = np.asarray(L, np.float32)[..., None] / 255
    p = np.array(paper, np.float32); k = np.array(ink, np.float32)
    return Image.fromarray((k + (p - k) * a).astype(np.uint8), 'RGB')

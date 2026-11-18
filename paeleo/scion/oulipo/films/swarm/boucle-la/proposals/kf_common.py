"""Shared stage for the boucle-la proposals: the seven-occurrence loop page
(A B C / H / C B A), handmade single-stroke lettering, balloons, the note prop.

The lettering is a hand-built single-stroke capital alphabet (glyph polylines
defined below) inked with a round pen; the jitter is seeded per balloon so a
repeated balloon is the *same* drawing, as the palindrome rule demands.
"""
import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 1280, 720
PAPER = (247, 245, 240)
INK = (17, 17, 17)

# ------------------------------------------------------------------ script --
TEXT = {
    "A": ("odette", "ET ÇA ?! C'EST TOI QUI L'AS LAISSÉ, CE MOT ?"),
    "B": ("gustave", "MOI ?! TU CROIS QUE J'AI QUE ÇA À FAIRE ?"),
    "C": ("odette", "ALORS DE QUI IL EST ?!"),
    "H": ("gustave", "« À MA CHÈRE ODETTE... » TIENS. C'EST POUR TOI."),
}
SEQ = ["A", "B", "C", "H", "C", "B", "A"]
NOTE_FACE = ["À MA CHÈRE", "ODETTE"]
# clock of a ~62 s film: title 0-4, then 7 s per occurrence, hinge 10 s, hold to 62
CLOCK = {"title": (0, 4), "A1": (4, 11), "B1": (11, 18), "C1": (18, 25), "H": (25, 35),
         "C2": (35, 42), "B2": (42, 49), "A2": (49, 56), "hold": (56, 62)}
KEY_T = 31.0  # the keyframe instant: hinge, note turned to face the accuser


def assert_fixture(seq=SEQ):
    assert len(seq) == 7 and seq[3] == "H"
    assert seq[:3] == list(reversed(seq[4:])), "mirror broken"
    assert seq.count("H") == 1, "hinge must be the single unpaired occurrence"
    for k in "ABC":
        assert seq.count(k) == 2


assert_fixture()

# ---------------------------------------------------------- stroke alphabet --
# glyph: (advance width, [polylines]); coords on a 6-unit cap height, y down.
def _arc(cx, cy, rx, ry, a0, a1, n=14):
    return [(cx + rx * math.cos(math.radians(a)), cy + ry * math.sin(math.radians(a)))
            for a in np.linspace(a0, a1, n)]


G = {
    "A": (4.2, [[(0, 6), (2.1, 0), (4.2, 6)], [(0.75, 4), (3.45, 4)]]),
    "B": (3.8, [[(0, 0), (0, 6)], [(0, 0), (2.5, 0), (3.3, 0.7), (3.3, 2.2), (2.5, 2.9), (0, 2.9)],
                [(2.5, 2.9), (3.7, 3.7), (3.7, 5.2), (2.8, 6), (0, 6)]]),
    "C": (3.9, [_arc(2.1, 3, 2.0, 3, -38, -322)]),
    "D": (3.9, [[(0, 0), (0, 6)], [(0, 0), (1.7, 0), (3.4, 1.2), (3.9, 3), (3.4, 4.8), (1.7, 6), (0, 6)]]),
    "E": (3.4, [[(3.4, 0), (0, 0), (0, 6), (3.4, 6)], [(0, 2.9), (2.7, 2.9)]]),
    "F": (3.3, [[(3.3, 0), (0, 0), (0, 6)], [(0, 2.9), (2.6, 2.9)]]),
    "G": (4.0, [_arc(2.1, 3, 2.0, 3, -38, -340) + [(4.0, 3.4), (2.3, 3.4)]]),
    "H": (3.9, [[(0, 0), (0, 6)], [(3.9, 0), (3.9, 6)], [(0, 3), (3.9, 3)]]),
    "I": (1.8, [[(0, 0), (1.8, 0)], [(0.9, 0), (0.9, 6)], [(0, 6), (1.8, 6)]]),
    "J": (3.4, [[(3.3, 0), (3.3, 4.5), (2.7, 5.7), (1.6, 6), (0.6, 5.5), (0.2, 4.6)]]),
    "K": (3.8, [[(0, 0), (0, 6)], [(3.6, 0), (0, 3.7)], [(1.2, 2.6), (3.8, 6)]]),
    "L": (3.2, [[(0, 0), (0, 6), (3.2, 6)]]),
    "M": (4.6, [[(0, 6), (0, 0), (2.3, 3.9), (4.6, 0), (4.6, 6)]]),
    "N": (4.0, [[(0, 6), (0, 0), (4.0, 6), (4.0, 0)]]),
    "O": (4.3, [_arc(2.15, 3, 2.15, 3, 0, 360, 24)]),
    "P": (3.6, [[(0, 6), (0, 0), (2.5, 0), (3.5, 0.8), (3.5, 2.4), (2.5, 3.2), (0, 3.2)]]),
    "Q": (4.3, [_arc(2.15, 3, 2.15, 3, 0, 360, 24), [(2.5, 4.4), (4.2, 6.3)]]),
    "R": (3.8, [[(0, 6), (0, 0), (2.5, 0), (3.5, 0.8), (3.5, 2.4), (2.5, 3.2), (0, 3.2)], [(1.8, 3.2), (3.8, 6)]]),
    "S": (3.7, [[(3.5, 0.9), (2.6, 0), (1.2, 0), (0.3, 0.8), (0.3, 2.0), (1.2, 2.7), (2.6, 3.2),
                 (3.6, 4.0), (3.6, 5.2), (2.6, 6), (1.1, 6), (0.1, 5.1)]]),
    "T": (4.0, [[(0, 0), (4.0, 0)], [(2.0, 0), (2.0, 6)]]),
    "U": (3.9, [[(0, 0), (0, 4.4), (0.7, 5.6), (1.95, 6), (3.2, 5.6), (3.9, 4.4), (3.9, 0)]]),
    "V": (4.1, [[(0, 0), (2.05, 6), (4.1, 0)]]),
    "W": (5.0, [[(0, 0), (1.25, 6), (2.5, 1.6), (3.75, 6), (5.0, 0)]]),
    "X": (3.9, [[(0, 0), (3.9, 6)], [(3.9, 0), (0, 6)]]),
    "Y": (4.0, [[(0, 0), (2.0, 3.1), (4.0, 0)], [(2.0, 3.1), (2.0, 6)]]),
    "Z": (3.8, [[(0, 0), (3.8, 0), (0, 6), (3.8, 6)]]),
    "?": (3.4, [[(0.2, 1.2), (0.9, 0.2), (2.0, 0), (3.1, 0.6), (3.2, 1.8), (2.1, 2.8), (1.7, 3.5), (1.7, 4.3)], ["dot", 1.7, 5.75]]),
    "!": (1.2, [[(0.6, 0), (0.6, 4.3)], ["dot", 0.6, 5.75]]),
    ".": (0.9, [["dot", 0.45, 5.75]]),
    ",": (0.9, [[(0.6, 5.5), (0.2, 6.7)]]),
    "'": (0.9, [[(0.55, 0), (0.35, 1.5)]]),
    "«": (3.0, [[(1.4, 2.0), (0.2, 3.2), (1.4, 4.4)], [(2.8, 2.0), (1.6, 3.2), (2.8, 4.4)]]),
    "»": (3.0, [[(0.2, 2.0), (1.4, 3.2), (0.2, 4.4)], [(1.6, 2.0), (2.8, 3.2), (1.6, 4.4)]]),
    "·": (1.4, [["dot", 0.7, 3.2]]),
    "-": (2.2, [[(0.2, 3.3), (2.0, 3.3)]]),
    ":": (0.9, [["dot", 0.45, 2.4], ["dot", 0.45, 5.75]]),
    " ": (2.0, []),
}
ACC = {"É": ("E", [[(1.2, -0.5), (2.5, -1.5)]]), "È": ("E", [[(1.0, -1.5), (2.3, -0.5)]]),
       "À": ("A", [[(1.5, -1.5), (2.6, -0.5)]]), "Ç": ("C", [[(2.1, 6), (2.4, 6.8), (1.5, 7.3)]]),
       "Ê": ("E", [[(0.9, -0.5), (1.7, -1.4), (2.5, -0.5)]])}


def glyph(ch):
    if ch in ACC:
        base, extra = ACC[ch]
        w, s = G[base]
        return w, s + extra
    return G.get(ch, G[" "])


def text_width(s, cap, track=0.55):
    u = cap / 6.0
    return sum((glyph(c)[0] + track) * u for c in s) - track * u


def ink_text(mask, x, y, s, cap=13, seed=0, pen=None, track=0.55, slant=0.06):
    """Ink one line of capitals into an L mask (drawn at the mask's scale)."""
    d = ImageDraw.Draw(mask)
    u = cap / 6.0
    pen = pen or max(2, int(round(cap * 0.19)))
    rs = random.Random(seed)
    cx = x
    for c in s:
        w, strokes = glyph(c)
        dy = rs.uniform(-0.25, 0.25) * u
        sc = rs.uniform(0.95, 1.05)
        for st in strokes:
            if st and st[0] == "dot":
                px, py = cx + st[1] * u * sc, y + st[2] * u * sc + dy
                r = pen * 0.75
                d.ellipse([px - r, py - r, px + r, py + r], fill=255)
                continue
            pts = []
            for (gx, gy) in st:
                jx, jy = rs.uniform(-0.12, 0.12), rs.uniform(-0.12, 0.12)
                pts.append((cx + (gx + jx + slant * (6 - gy)) * u * sc, y + (gy + jy) * u * sc + dy))
            d.line(pts, fill=255, width=pen, joint="curve")
            for p in (pts[0], pts[-1]):
                d.ellipse([p[0] - pen / 2, p[1] - pen / 2, p[0] + pen / 2, p[1] + pen / 2], fill=255)
        cx += (w + track) * u * sc
    return cx


def wrap_words(s, cap, maxw):
    lines, cur = [], ""
    for wd in s.split(" "):
        t = (cur + " " + wd).strip()
        if cur and text_width(t, cap) > maxw:
            lines.append(cur)
            cur = wd
        else:
            cur = t
    if cur:
        lines.append(cur)
    return lines


def draw_mask_on(img, mask, color=INK, ss=3):
    """Downsample a supersampled L mask and ink it onto img."""
    m = mask.resize((mask.width // ss, mask.height // ss), Image.LANCZOS)
    img.paste(Image.new("RGB", img.size, color), (0, 0), m)


def balloon(img, cx, cy, key, cap=12, maxw=200, tail=None, seed=None, ss=3, alpha=255, color=INK):
    """Hand-lettered balloon. Same key -> same seed -> identical drawing."""
    speaker, text = TEXT[key]
    seed = seed if seed is not None else sum(map(ord, key + text))
    lines = wrap_words(text, cap, maxw)
    lh = cap * 1.55
    tw = max(text_width(l, cap) for l in lines)
    th = lh * len(lines) - (lh - cap)
    rx, ry = tw / 2 + cap * 1.3, th / 2 + cap * 1.05
    S = ss
    box = (int(cx - rx - 60), int(cy - ry - 60), int(cx + rx + 60), int(cy + ry + 90))
    bw, bh = box[2] - box[0], box[3] - box[1]
    fill = Image.new("L", (bw * S, bh * S), 0)
    line = Image.new("L", (bw * S, bh * S), 0)
    df, dl = ImageDraw.Draw(fill), ImageDraw.Draw(line)
    rs = random.Random(seed)
    lcx, lcy = (cx - box[0]) * S, (cy - box[1]) * S
    pts = []
    ph = rs.uniform(0, 6.28)
    for a in np.linspace(0, 2 * math.pi, 90, endpoint=False):
        r = 1 + 0.02 * math.sin(3 * a + ph) + 0.012 * math.sin(7 * a)
        ca, sa = math.cos(a), math.sin(a)
        # superellipse for the comic balloon belly
        e = 2.4
        px = abs(ca) ** (2 / e) * (1 if ca >= 0 else -1)
        py = abs(sa) ** (2 / e) * (1 if sa >= 0 else -1)
        pts.append((lcx + px * rx * S * r, lcy + py * ry * S * r))
    if tail:
        tx, ty = (tail[0] - box[0]) * S, (tail[1] - box[1]) * S
        ang = math.atan2(ty - lcy, tx - lcx)
        # insert a tail wedge at the nearest boundary angle
        k = min(range(len(pts)), key=lambda i: abs(math.atan2(pts[i][1] - lcy, pts[i][0] - lcx) - ang))
        n = len(pts)
        a0, a1 = pts[(k - 1) % n], pts[(k + 1) % n]
        pts = [pts[(k + 1 + j) % n] for j in range(n - 2)]
        pts = [a1] + pts[1:-1] + [a0, (tx, ty)]
    df.polygon(pts, fill=255)
    dl.line(pts + [pts[0]], fill=255, width=int(2.2 * S), joint="curve")
    region = img.crop(box)
    white = Image.new("RGB", region.size, (255, 255, 255))
    fm = fill.resize((bw, bh), Image.LANCZOS)
    if alpha < 255:
        fm = fm.point(lambda v: v * alpha // 255)
    region.paste(white, (0, 0), fm)
    txt = Image.new("L", (bw * S, bh * S), 0)
    y = lcy - th / 2 * S
    for i, l in enumerate(lines):
        lw = text_width(l, cap) * S
        ink_text(txt, lcx - lw / 2, y, l, cap=cap * S, seed=seed + i * 13)
        y += lh * S
    both = Image.fromarray(np.maximum(np.asarray(line), np.asarray(txt)))
    m = both.resize((bw, bh), Image.LANCZOS)
    if alpha < 255:
        m = m.point(lambda v: v * alpha // 255)
    region.paste(Image.new("RGB", region.size, color), (0, 0), m)
    img.paste(region, box[:2])


# ------------------------------------------------------------------ the page --
LEFT = 212
GUT = 12
ROW = [(14, 246), (258, 462), (474, 706)]


def layout():
    """Panel rects keyed by occurrence index 0..6 (A B C H C B A)."""
    w = (W - 16 - LEFT - 2 * GUT) / 3
    rects = {}
    for i in range(3):
        x0 = LEFT + i * (w + GUT)
        rects[i] = (int(x0), ROW[0][0], int(x0 + w), ROW[0][1])
        rects[6 - i] = (int(LEFT + (2 - i) * (w + GUT)), ROW[2][0], int(LEFT + (2 - i) * (w + GUT) + w), ROW[2][1])
    rects[3] = (LEFT, ROW[1][0], W - 16, ROW[1][1])
    # row 3 reads C B A left to right: occurrence 4 = C at left
    return rects


def wobbly_rect(d, r, width=3, seed=0, S=1, fill=None):
    rs = random.Random(seed)
    x0, y0, x1, y1 = [v * S for v in r]
    pts = []
    for (ax, ay, bx, by) in ((x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)):
        for t in np.linspace(0, 1, 8, endpoint=False):
            pts.append((ax + (bx - ax) * t + rs.uniform(-0.6, 0.6) * S, ay + (by - ay) * t + rs.uniform(-0.6, 0.6) * S))
    if fill is not None:
        d.polygon(pts, fill=fill)
    d.line(pts + [pts[0]], fill=255 if fill is None else 255, width=width * S, joint="curve")


def page_furniture(img, seed=3, ss=3):
    """Title column (outside the mirrored sequence) and the hinge marks."""
    m = Image.new("L", (W * ss, H * ss), 0)
    ink_text(m, 24 * ss, 34 * ss, "LE MOT", cap=40 * ss, seed=seed, pen=int(7.5 * ss), slant=0.1)
    ink_text(m, 26 * ss, 96 * ss, "OU QUI L'A", cap=15 * ss, seed=seed + 1)
    ink_text(m, 26 * ss, 120 * ss, "LAISSÉ ?", cap=15 * ss, seed=seed + 2)
    d = ImageDraw.Draw(m)
    # a hand-drawn loop: down the margin, round, and back up (the "boucle")
    pts = _arc(100 * ss, 420 * ss, 58 * ss, 170 * ss, -80, 260, 60)
    d.line(pts, fill=255, width=int(3 * ss), joint="curve")
    ex, ey = pts[-1]
    d.polygon([(ex - 10 * ss, ey + 6 * ss), (ex + 9 * ss, ey + 4 * ss), (ex + 2 * ss, ey - 14 * ss)], fill=255)
    for i, k in enumerate(SEQ):
        ink_text(m, (34 + i * 22) * ss, 655 * ss, k, cap=14 * ss, seed=seed + 40 + i, pen=int(2.6 * ss))
    ink_text(m, 24 * ss, 686 * ss, "ÉTUDE · OUBAPO", cap=9 * ss, seed=seed + 60, pen=int(1.8 * ss))
    draw_mask_on(img, m, ss=ss)


def panel_ids(img, rects, ss=3, alpha=150):
    m = Image.new("L", (W * ss, H * ss), 0)
    for i, k in enumerate(SEQ):
        x0, y0, x1, y1 = rects[i]
        ink_text(m, (x1 - 15) * ss, (y1 + 1.5) * ss, k, cap=7 * ss, seed=90 + i, pen=int(1.5 * ss))
    m = m.point(lambda v: v * alpha // 255)
    draw_mask_on(img, m, color=(90, 90, 90), ss=ss)


def frame_panel(img, r, seed=0, width=3, ss=3):
    m = Image.new("L", (W * ss, H * ss), 0)
    wobbly_rect(ImageDraw.Draw(m), r, width=width, seed=seed, S=ss)
    draw_mask_on(img, m, ss=ss)


def note_prop(w=86, h=58, face=True, fold=0.0, seed=5, ss=3, ink=INK, paper=(252, 251, 246)):
    """The handmade note: a folded card lettered on its face. RGBA."""
    im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(2 * ss, 3 * ss), (w * ss - 3 * ss, 1 * ss), (w * ss - 1 * ss, h * ss - 3 * ss), (3 * ss, h * ss - 1 * ss)],
              fill=paper + (255,), outline=ink + (255,), width=int(1.8 * ss))
    d.line([(w * ss * 0.5, 2 * ss), (w * ss * 0.52, h * ss - 2 * ss)], fill=(160, 160, 160, 255), width=ss)
    if face:
        m = Image.new("L", im.size, 0)
        cap = h * 0.17
        y = h * 0.24
        for i, l in enumerate(NOTE_FACE):
            lw = text_width(l, cap)
            ink_text(m, (w - lw) / 2 * ss, y * ss, l, cap=cap * ss, seed=seed + i, pen=int(cap * 0.17 * ss) + 1, slant=0.18)
            y += cap * 1.7
        im.paste(Image.new("RGBA", im.size, ink + (255,)), (0, 0), m)
    return im.resize((w, h), Image.LANCZOS)


def board(ref_path, kfs, names, out, width=2000):
    ref = Image.open(ref_path).convert("RGB")
    cell_w = (width - 30) // 2
    cell_h = int(cell_w * 9 / 16)
    lab = 34
    bd = Image.new("RGB", (width, 2 * (cell_h + lab) + 30), (24, 24, 24))
    tiles = [(ref, "REFERENCE · Lécroart, Boucle-là ! (Cité BD scan)")] + [(Image.open(k).convert("RGB"), n) for k, n in zip(kfs, names)]
    for i, (im, n) in enumerate(tiles):
        x = 10 + (i % 2) * (cell_w + 10)
        y = 10 + (i // 2) * (cell_h + lab + 10)
        t = im.copy()
        t.thumbnail((cell_w, cell_h))
        bd.paste(t, (x + (cell_w - t.width) // 2, y + lab))
        m = Image.new("L", (cell_w * 2, lab * 2), 0)
        ink_text(m, 8, 10, n.upper(), cap=34, seed=i, pen=5)
        lm = m.resize((cell_w, lab), Image.LANCZOS)
        bd.paste(Image.new("RGB", (cell_w, lab), (240, 236, 220)), (x, y), lm)
    bd.save(out, quality=90)

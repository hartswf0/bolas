"""Looser pen hand for the full build (test-shot note: "a looser, less uniform
lettering hand with mixed sizes").

Built on hand.py's single-stroke capitals (same glyph skeletons, same pen
order). Each written letter is a fresh drawing of its skeleton, not a copy:
  * every control point of every glyph is moved by its own hand jitter;
  * each glyph gets its own width, height, slant and small rotation;
  * the baseline drifts as a slow random walk along each line;
  * word sizes vary (a word can be marked for emphasis and is written larger);
  * stroke ends overshoot or fall short a little, as a quick pen does;
  * stroke weight varies per stroke (3.4-4.3 px at 540 px panels).
Seeded, so a balloon is the same every time it is rendered.
"""
import math
import numpy as np
from hand import GLYPHS as BASE, catmull, wobble, arc

GLYPHS = dict(BASE)
# extra marks needed by the page lettering
GLYPHS['&'] = (0.62, [[(0.62, 1.0), (0.2, 0.45), (0.12, 0.22), (0.24, 0.02), (0.42, 0.06),
                       (0.44, 0.26), (0.08, 0.6), (0.06, 0.86), (0.22, 1.0), (0.44, 0.94), (0.62, 0.62)]])
GLYPHS['—'] = (0.7, [[(0.02, 0.55), (0.68, 0.53)]])     # em dash
GLYPHS['·'] = (0.18, [[(0.08, 0.5), (0.1, 0.53)]])     # middle dot


def glyph_strokes(ch):
    return GLYPHS.get(ch, GLYPHS[' '])


def layout(lines, size, seed, emph=(), track=0.2, lead=1.46, loose=1.0):
    """Lay out lines of capitals in the loose hand.

    lines: list of strings. size: nominal cap height (px, in the render space).
    emph: words (upper case, punctuation stripped) written ~18% larger.
    Returns (glyphs, (w, h)) where glyphs is a list of dicts in pen order:
      {ch, line, word, strokes:[[(x,y),...], ...], widths:[w_scale,...]}
    """
    rng = np.random.default_rng(seed)
    out = []
    y = 0.0
    maxw = 0.0
    line_sizes = []
    for li, line in enumerate(lines):
        ls = size * rng.uniform(0.93, 1.07)                 # each line its own size
        words = line.upper().split(' ')
        wsz = []
        for w in words:
            key = ''.join(c for c in w if c.isalnum() or c == "'")
            k = 1.18 if key in emph else rng.uniform(0.95, 1.05)
            wsz.append(ls * k)
        line_h = max(wsz) if wsz else ls
        line_sizes.append(line_h)
        x = 0.0
        drift = 0.0
        x_shift = rng.normal(0, 0.08) * size * loose          # lines do not left-align exactly
        x += x_shift
        for wi, w in enumerate(words):
            sz = wsz[wi]
            slant = rng.normal(0.05, 0.05) * loose          # word slant (forward lean)
            for ch in w:
                gw, gs = glyph_strokes(ch)
                drift += rng.normal(0, 0.022) * size * loose
                drift *= 0.85
                sx = sz * rng.uniform(0.9, 1.14) * (1 + 0.04 * (loose - 1))
                sy = sz * rng.uniform(0.9, 1.1)
                rot = rng.normal(0, 0.05) * loose
                ca, sa = math.cos(rot), math.sin(rot)
                base = y + (line_h - sy) * 0.75 + drift           # bigger words rise, small ones sit
                strokes, widths = [], []
                for s in gs:
                    pts = []
                    for (u, v) in s:
                        u += rng.normal(0, 0.035) * loose
                        v += rng.normal(0, 0.03) * loose
                        u2 = u * sx + (1 - v) * sy * slant
                        v2 = v * sy
                        cx, cy = gw * sx / 2, sy / 2
                        u3 = cx + (u2 - cx) * ca - (v2 - cy) * sa
                        v3 = cy + (u2 - cx) * sa + (v2 - cy) * ca
                        pts.append((x + u3, base + v3))
                    # pen overshoot / short stop at the ends
                    if len(pts) >= 2:
                        a, b = np.array(pts[0]), np.array(pts[1])
                        e, f = np.array(pts[-1]), np.array(pts[-2])
                        if np.linalg.norm(b - a) > 1e-6:
                            pts[0] = tuple(a + (a - b) / np.linalg.norm(b - a) * rng.uniform(-0.03, 0.06) * sz)
                        if np.linalg.norm(e - f) > 1e-6:
                            pts[-1] = tuple(e + (e - f) / np.linalg.norm(e - f) * rng.uniform(-0.03, 0.08) * sz)
                    pts = catmull(pts, 4) if len(pts) > 3 else pts
                    pts = wobble(pts, size * 0.014 * loose, rng, 3) if len(pts) > 4 else pts
                    strokes.append([tuple(map(float, p)) for p in pts])
                    widths.append(float(rng.uniform(0.9, 1.13)))
                out.append(dict(ch=ch, line=li, word=wi, strokes=strokes, widths=widths, size=sz))
                x += gw * sx + track * sz * rng.uniform(0.8, 1.15)
            x += 0.5 * ls * rng.uniform(0.8, 1.25)               # word space
        x -= 0.5 * ls
        maxw = max(maxw, x)
        y += line_h * lead
    h = y - line_sizes[-1] * (lead - 1)
    # centre each line (comic-balloon convention), keeping a little hand jitter
    spans = {}
    for g in out:
        for st in g['strokes']:
            for px, py in st:
                a, b = spans.get(g['line'], (1e9, -1e9))
                spans[g['line']] = (min(a, px), max(b, px))
    W = max(b - a for a, b in spans.values()) if spans else 0
    jit = {li: rng.normal(0, 0.06) * size * loose for li in spans}
    for g in out:
        a, b = spans[g['line']]
        dx = (W - (b - a)) / 2 - a + jit[g['line']]
        g['strokes'] = [[(px + dx, py) for px, py in st] for st in g['strokes']]
    # normalise so the block starts at x=0
    xs = [p[0] for g in out for s in g['strokes'] for p in s]
    x0 = min(xs) if xs else 0
    for g in out:
        g['strokes'] = [[(px - x0, py) for px, py in s] for s in g['strokes']]
    xs = [p[0] for g in out for s in g['strokes'] for p in s]
    ys = [p[1] for g in out for s in g['strokes'] for p in s]
    return out, (max(xs) if xs else 0, max(ys) if ys else h)

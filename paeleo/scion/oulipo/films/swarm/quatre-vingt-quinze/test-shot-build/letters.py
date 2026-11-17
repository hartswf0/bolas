"""Single-stroke hand lettering for quatre-vingt-quinze (HANDMADE, no typeface).

Every glyph is a list of pen strokes in a unit box (cap height 1, y down,
baseline y=1). Strokes are drawn with kit.Ink.stroke (swelling, tapered,
wobbled), and every glyph instance gets its own small tilt, scale and
baseline jitter from a seeded RNG, so repeated letters are never identical
but the same text with the same seed is always the same drawing.
"""
import math
import random


def arc(cx, cy, rx, ry, a0, a1, n=14):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * k / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]


DOT = lambda x, y: [(x, y), (x + 0.02, y + 0.03)]

CAPS = {
    "A": (0.62, [[(0, 1), (0.31, 0), (0.62, 1)], [(0.13, 0.63), (0.5, 0.61)]]),
    "B": (0.56, [[(0, 1), (0, 0)], [(0, 0), (0.34, 0), (0.48, 0.08), (0.5, 0.22), (0.42, 0.4), (0.28, 0.46), (0, 0.47)],
                 [(0.28, 0.46), (0.48, 0.54), (0.56, 0.72), (0.5, 0.9), (0.34, 1), (0, 1)]]),
    "C": (0.62, [arc(0.34, 0.5, 0.34, 0.5, -40, -318)]),
    "D": (0.6, [[(0, 1), (0, 0), (0.2, 0)] + arc(0.2, 0.5, 0.4, 0.5, -90, 90)[1:] + [(0, 1)]]),
    "E": (0.52, [[(0.52, 0), (0, 0), (0, 1), (0.54, 1)], [(0, 0.5), (0.42, 0.49)]]),
    "F": (0.5, [[(0.52, 0), (0, 0), (0, 1)], [(0, 0.48), (0.4, 0.47)]]),
    "G": (0.66, [arc(0.34, 0.5, 0.34, 0.5, -40, -350), [(0.67, 0.58), (0.4, 0.58)], [(0.67, 0.58), (0.66, 0.93)]]),
    "H": (0.58, [[(0, 0), (0, 1)], [(0.58, 0), (0.58, 1)], [(0, 0.5), (0.58, 0.49)]]),
    "I": (0.12, [[(0.06, 0), (0.06, 1)]]),
    "L": (0.48, [[(0, 0), (0, 1), (0.48, 1)]]),
    "M": (0.74, [[(0, 1), (0.04, 0), (0.37, 0.64), (0.7, 0), (0.74, 1)]]),
    "N": (0.58, [[(0, 1), (0, 0), (0.58, 1), (0.58, 0)]]),
    "O": (0.68, [arc(0.34, 0.5, 0.34, 0.5, -100, 262, 22)]),
    "P": (0.52, [[(0, 1), (0, 0), (0.32, 0), (0.48, 0.1), (0.5, 0.26), (0.4, 0.42), (0.26, 0.48), (0, 0.48)]]),
    "R": (0.56, [[(0, 1), (0, 0), (0.32, 0), (0.48, 0.1), (0.5, 0.26), (0.4, 0.42), (0.26, 0.48), (0, 0.48)],
                 [(0.24, 0.48), (0.58, 1)]]),
    "S": (0.54, [[(0.52, 0.12), (0.4, 0.02), (0.22, 0), (0.06, 0.08), (0.02, 0.22), (0.12, 0.38), (0.3, 0.48),
                  (0.46, 0.58), (0.54, 0.74), (0.5, 0.9), (0.34, 1), (0.14, 0.98), (0, 0.86)]]),
    "T": (0.62, [[(0, 0.01), (0.62, 0)], [(0.31, 0), (0.31, 1)]]),
    "U": (0.58, [[(0, 0)] + arc(0.29, 0.68, 0.29, 0.32, 180, 0)[0:] + [(0.58, 0)]]),
    "V": (0.6, [[(0, 0), (0.3, 1), (0.6, 0)]]),
    "6": (0.52, [[(0.46, 0.04), (0.28, 0.04), (0.12, 0.2), (0.04, 0.45), (0.04, 0.72), (0.14, 0.94), (0.3, 1),
                  (0.46, 0.92), (0.52, 0.74), (0.44, 0.56), (0.28, 0.5), (0.12, 0.56), (0.04, 0.68)]]),
    "1": (0.3, [[(0.04, 0.2), (0.22, 0), (0.22, 1)]]),
    "0": (0.52, [arc(0.26, 0.5, 0.26, 0.5, -90, 270, 20)]),
    ".": (0.1, [DOT(0.04, 0.93)]),
    ",": (0.12, [[(0.08, 0.9), (0.03, 1.12)]]),
    "!": (0.14, [[(0.08, 0), (0.06, 0.7)], DOT(0.05, 0.93)]),
    "?": (0.5, [[(0.02, 0.2), (0.12, 0.04), (0.28, 0), (0.44, 0.08), (0.48, 0.24), (0.38, 0.4), (0.25, 0.5), (0.24, 0.7)],
                DOT(0.23, 0.93)]),
    "'": (0.1, [[(0.07, -0.02), (0.03, 0.26)]]),
    "-": (0.34, [[(0.02, 0.55), (0.32, 0.53)]]),
    "(": (0.22, [arc(0.32, 0.5, 0.28, 0.58, 120, 240, 10)]),
    ")": (0.22, [arc(-0.1, 0.5, 0.28, 0.58, -60, 60, 10)]),
    ":": (0.1, [DOT(0.04, 0.35), DOT(0.04, 0.9)]),
    "—": (0.9, [[(0.04, 0.52), (0.86, 0.5)]]),
    "·": (0.12, [DOT(0.05, 0.5)]),
}
CAPS["É"] = (0.52, CAPS["E"][1] + [[(0.18, -0.12), (0.36, -0.28)]])
CAPS["Ê"] = (0.52, CAPS["E"][1] + [[(0.1, -0.12), (0.26, -0.28), (0.42, -0.12)]])

LOWER = {
    "a": (0.52, [arc(0.26, 0.71, 0.25, 0.29, -10, 350, 16), [(0.52, 0.42), (0.52, 1)]]),
    "b": (0.54, [[(0, 0), (0, 1)], arc(0.27, 0.71, 0.27, 0.29, 180, 540, 16)]),
    "e": (0.52, [[(0.03, 0.72), (0.5, 0.72)] + arc(0.26, 0.71, 0.25, 0.29, 0, -318, 14)[1:]]),
    "g": (0.52, [arc(0.26, 0.7, 0.25, 0.28, -10, 350, 16), [(0.52, 0.42), (0.52, 1.14)] + arc(0.3, 1.14, 0.22, 0.2, 0, 160, 8)[1:]]),
    "i": (0.12, [[(0.06, 0.44), (0.06, 1)], DOT(0.05, 0.2)]),
    "n": (0.5, [[(0, 0.42), (0, 1)], [(0, 0.62), (0.1, 0.46), (0.26, 0.42), (0.42, 0.48), (0.49, 0.62), (0.49, 1)]]),
    "q": (0.56, [arc(0.26, 0.71, 0.25, 0.29, -10, 350, 16), [(0.52, 0.42), (0.52, 1.36), (0.62, 1.3)]]),
    "r": (0.38, [[(0, 0.42), (0, 1)], [(0, 0.66), (0.1, 0.48), (0.24, 0.42), (0.38, 0.45)]]),
    "s": (0.44, [[(0.42, 0.5), (0.3, 0.42), (0.14, 0.43), (0.04, 0.52), (0.08, 0.64), (0.24, 0.7), (0.38, 0.77),
                  (0.44, 0.88), (0.36, 0.98), (0.18, 1), (0.02, 0.93)]]),
    "t": (0.38, [[(0.16, 0.12), (0.16, 0.9), (0.22, 0.99), (0.38, 0.97)], [(0, 0.44), (0.36, 0.43)]]),
    "u": (0.5, [[(0, 0.42), (0, 0.82), (0.08, 0.96), (0.24, 1), (0.4, 0.96), (0.49, 0.84)], [(0.49, 0.42), (0.49, 1)]]),
    "v": (0.5, [[(0, 0.42), (0.25, 1), (0.5, 0.42)]]),
    "z": (0.48, [[(0, 0.43), (0.46, 0.42), (0.02, 1), (0.5, 0.99)]]),
    "-": (0.36, [[(0.03, 0.72), (0.33, 0.7)]]),
}


def glyph(ch):
    if ch in CAPS:
        return CAPS[ch]
    if ch in LOWER:
        return LOWER[ch]
    raise KeyError(ch)


def measure(text, size, track=0.2, space=0.42):
    w = 0.0
    for ch in text:
        w += space if ch == " " else glyph(ch)[0] + track
    return (w - track) * size


def letter(ink, text, x, y, size, width, color, seed=0, align="center", track=0.2, space=0.42,
           tilt=0.0, flip_every=0, jitter=1.0, scale=1.0):
    """Hand-letter `text` with cap-height `size` (px), baseline at y.

    align: left | center. tilt rotates the whole line (degrees) about its start.
    flip_every=2 turns every second glyph over (180 degrees), as in the title.
    `scale` multiplies all coordinates (for supersampled drawing).
    """
    rng = random.Random(hash((text, seed)) & 0xffffffff)
    total = measure(text, size, track, space)
    x0 = x - total / 2 if align == "center" else x
    ct, st = math.cos(math.radians(tilt)), math.sin(math.radians(tilt))
    cx = x0
    gi = 0
    for ch in text:
        if ch == " ":
            cx += space * size
            continue
        gw, strokes = glyph(ch)
        rot = math.radians(rng.uniform(-3.5, 3.5) * jitter)
        sc = size * (1 + rng.uniform(-0.07, 0.07) * jitter)
        dy = rng.uniform(-0.05, 0.05) * size * jitter
        flip = flip_every and (gi % flip_every == 1)
        pivot_y = 0.71 if ch in LOWER else 0.5
        for s in strokes:
            pts = []
            for (u, v) in s:
                if flip:
                    u, v = gw - u, 2 * pivot_y - v
                px, py = (u - gw / 2) * sc, (v - 0.5) * sc
                px, py = px * math.cos(rot) - py * math.sin(rot), px * math.sin(rot) + py * math.cos(rot)
                gx = cx + gw * size / 2 + px - x0
                gy = py + 0.5 * size - size + dy
                X = x0 + gx * ct - gy * st
                Y = y + gx * st + gy * ct
                pts.append((X * scale, Y * scale))
            if len(pts) == 2 and math.hypot(pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]) < 0.1 * size * scale:
                # a pen dot
                mx, my = pts[0]
                r = width * scale * 0.62
                ink.d.ellipse([mx - r, my - r, mx + r, my + r], fill=tuple(color) + (255,))
                continue
            w = width * scale * (1 + rng.uniform(-0.12, 0.12) * jitter)
            ink.stroke(pts, color=color, width=w * 1.25, taper=True, amount=0.6 * scale)
            # the pen's body: a second, untapered pass keeps strokes inky to the ends
            ink.stroke(pts, color=color, width=w * 0.8, taper=False, amount=0.35 * scale)
        cx += (gw + track) * size
        gi += 1
    return total

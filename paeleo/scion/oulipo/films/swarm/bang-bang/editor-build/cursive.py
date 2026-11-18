# Bang Bang, editor repair 1: the magpie's hand, built by hand.
#
# A joined French cursive drawn as pen strokes, not set from a font.  Every lowercase letter is a single stroke with
# an entry and an exit, written here as control points (x-height = 1, baseline = 0, ascender 1.9, descender -0.9) and
# chained through one Catmull-Rom spline per word, so the letters of a word are joined the way a pen joins them.
# Each instance of a letter has its control points moved by its own noise, its own width and size; the slant
# wanders along the line and the baseline drifts across the whole line (a slow tilt plus a long wave), not per word.
# The stroke is laid down as a felt nib: heavier on downstrokes, thinner on the upward joins.
# Capitals, digits and punctuation are separate pen lifts.  No glyph outline from any typeface is used.
import math
import numpy as np
import cv2

E = (0.0, 0.1)        # the standard entry: the pen arrives low from the left
G = {
    "a": [E, (0.4, 0.55), (0.75, 0.9), (0.5, 1.0), (0.2, 0.85), (0.08, 0.45), (0.2, 0.05), (0.45, 0.05), (0.7, 0.5), (0.78, 1.0), (0.74, 0.4), (0.78, 0.05), (0.95, 0.0), (1.1, 0.15)],
    "b": [E, (0.3, 0.8), (0.55, 1.6), (0.5, 1.9), (0.35, 1.7), (0.28, 0.8), (0.27, 0.1), (0.45, 0.0), (0.65, 0.3), (0.62, 0.8), (0.45, 0.9), (0.7, 0.88), (0.9, 0.9)],
    "c": [E, (0.3, 0.5), (0.6, 0.88), (0.74, 0.8), (0.68, 0.96), (0.45, 1.0), (0.2, 0.8), (0.1, 0.4), (0.25, 0.03), (0.55, 0.0), (0.8, 0.15)],
    "d": [E, (0.4, 0.55), (0.75, 0.9), (0.5, 1.0), (0.2, 0.85), (0.08, 0.45), (0.2, 0.05), (0.45, 0.05), (0.7, 0.5), (0.82, 1.9), (0.76, 0.6), (0.78, 0.05), (0.95, 0.0), (1.1, 0.15)],
    "e": [E, (0.35, 0.4), (0.6, 0.7), (0.55, 0.95), (0.35, 0.95), (0.15, 0.6), (0.15, 0.2), (0.35, 0.0), (0.6, 0.05), (0.8, 0.2)],
    "f": [E, (0.3, 0.8), (0.5, 1.6), (0.45, 1.9), (0.3, 1.7), (0.28, 0.8), (0.25, -0.3), (0.2, -0.8), (0.1, -0.7), (0.25, -0.2), (0.45, 0.05), (0.65, 0.15)],
    "g": [E, (0.4, 0.55), (0.72, 0.9), (0.5, 1.0), (0.2, 0.85), (0.08, 0.45), (0.2, 0.05), (0.45, 0.05), (0.7, 0.5), (0.78, 1.0), (0.74, 0.2), (0.68, -0.6), (0.45, -0.9), (0.3, -0.7), (0.5, -0.3), (0.85, 0.0), (1.05, 0.15)],
    "h": [E, (0.3, 0.8), (0.55, 1.6), (0.5, 1.9), (0.35, 1.7), (0.28, 0.8), (0.25, 0.0), (0.35, 0.6), (0.55, 0.95), (0.72, 0.8), (0.75, 0.3), (0.78, 0.03), (0.92, 0.0), (1.05, 0.15)],
    "i": [E, (0.25, 0.55), (0.38, 1.0), (0.32, 0.5), (0.32, 0.1), (0.45, 0.0), (0.65, 0.15)],
    "j": [E, (0.25, 0.55), (0.38, 1.0), (0.33, 0.2), (0.28, -0.6), (0.1, -0.88), (0.0, -0.65), (0.25, -0.25), (0.55, 0.0), (0.7, 0.15)],
    "k": [E, (0.3, 0.8), (0.55, 1.6), (0.5, 1.9), (0.35, 1.7), (0.28, 0.8), (0.25, 0.0), (0.35, 0.6), (0.6, 0.95), (0.7, 0.75), (0.4, 0.5), (0.6, 0.35), (0.72, 0.03), (0.9, 0.0), (1.0, 0.15)],
    "l": [E, (0.3, 0.8), (0.55, 1.6), (0.5, 1.9), (0.35, 1.7), (0.3, 0.9), (0.3, 0.2), (0.42, 0.0), (0.65, 0.15)],
    "m": [E, (0.12, 0.55), (0.2, 1.0), (0.18, 0.5), (0.15, 0.0), (0.25, 0.6), (0.4, 0.95), (0.55, 0.8), (0.58, 0.0), (0.65, 0.6), (0.82, 0.95), (0.98, 0.8), (1.0, 0.3), (1.03, 0.03), (1.18, 0.0), (1.3, 0.15)],
    "n": [E, (0.12, 0.55), (0.2, 1.0), (0.18, 0.5), (0.15, 0.0), (0.25, 0.6), (0.45, 0.95), (0.65, 0.85), (0.7, 0.4), (0.72, 0.05), (0.88, 0.0), (1.0, 0.15)],
    "o": [E, (0.35, 0.6), (0.65, 0.95), (0.4, 1.0), (0.12, 0.75), (0.1, 0.3), (0.3, 0.0), (0.6, 0.15), (0.68, 0.6), (0.62, 0.92), (0.8, 0.85), (1.0, 0.9)],
    "p": [E, (0.15, 0.55), (0.22, 1.0), (0.2, 0.0), (0.15, -0.9), (0.18, -0.2), (0.25, 0.6), (0.45, 0.95), (0.68, 0.75), (0.65, 0.2), (0.4, 0.0), (0.3, 0.1), (0.55, 0.05), (0.8, 0.15)],
    "q": [E, (0.4, 0.55), (0.75, 0.9), (0.5, 1.0), (0.2, 0.85), (0.08, 0.45), (0.2, 0.05), (0.45, 0.05), (0.7, 0.5), (0.78, 1.0), (0.74, 0.0), (0.72, -0.9), (0.8, -0.3), (0.9, 0.0), (1.05, 0.15)],
    "r": [E, (0.2, 0.7), (0.25, 1.0), (0.35, 0.85), (0.55, 0.9), (0.5, 0.6), (0.48, 0.2), (0.55, 0.0), (0.75, 0.15)],
    "s": [E, (0.3, 0.6), (0.42, 1.0), (0.58, 0.55), (0.65, 0.25), (0.5, 0.0), (0.25, 0.05), (0.2, 0.15), (0.45, 0.1), (0.75, 0.15)],
    "t": [E, (0.25, 0.8), (0.4, 1.6), (0.32, 0.6), (0.33, 0.1), (0.45, 0.0), (0.65, 0.15)],
    "u": [E, (0.2, 0.55), (0.3, 1.0), (0.25, 0.4), (0.35, 0.0), (0.55, 0.15), (0.72, 0.6), (0.78, 1.0), (0.74, 0.4), (0.78, 0.05), (0.95, 0.0), (1.1, 0.15)],
    "v": [E, (0.15, 0.6), (0.2, 0.95), (0.3, 0.4), (0.45, 0.0), (0.6, 0.5), (0.7, 0.95), (0.65, 0.8), (0.85, 0.85), (1.0, 0.9)],
    "w": [E, (0.15, 0.6), (0.2, 0.95), (0.3, 0.3), (0.4, 0.0), (0.52, 0.5), (0.58, 0.8), (0.65, 0.3), (0.75, 0.0), (0.88, 0.5), (0.95, 0.95), (0.92, 0.8), (1.1, 0.85), (1.25, 0.9)],
    "x": [E, (0.2, 0.7), (0.35, 0.95), (0.5, 0.6), (0.6, 0.15), (0.75, 0.0), (0.9, 0.15)],
    "y": [E, (0.15, 0.6), (0.22, 1.0), (0.25, 0.4), (0.4, 0.05), (0.62, 0.4), (0.72, 1.0), (0.68, 0.0), (0.6, -0.6), (0.42, -0.9), (0.28, -0.7), (0.5, -0.3), (0.85, 0.0), (1.05, 0.15)],
    "z": [E, (0.2, 0.8), (0.35, 0.95), (0.6, 0.9), (0.2, 0.0), (0.45, 0.1), (0.6, -0.3), (0.45, -0.8), (0.35, -0.6), (0.6, -0.1), (0.8, 0.1)],
}
HIGH_EXIT = set("bovw")
EXTRA = {"i": [[(0.42, 1.42), (0.46, 1.46)]], "j": [[(0.44, 1.42), (0.48, 1.46)]], "t": [[(0.1, 1.02), (0.62, 1.07)]],
         "x": [[(0.68, 0.95), (0.3, 0.02)]]}
# separate pen lifts: list of strokes, advance
LIFT = {
    "A": ([[(0.0, 0.0), (0.3, 1.0), (0.55, 1.9), (0.7, 1.0), (0.9, 0.0)], [(0.22, 0.78), (0.75, 0.82)]], 1.0),
    "B": ([[(0.15, 1.9), (0.12, 1.0), (0.1, 0.0)], [(0.0, 1.75), (0.4, 1.95), (0.75, 1.75), (0.65, 1.2), (0.25, 1.0), (0.8, 0.8), (0.85, 0.25), (0.5, 0.0), (0.1, 0.05)]], 1.0),
    "C": ([[(0.95, 1.65), (0.7, 1.9), (0.3, 1.7), (0.05, 1.0), (0.15, 0.25), (0.5, 0.0), (0.9, 0.2)]], 1.0),
    "D": ([[(0.15, 1.85), (0.12, 0.0)], [(0.0, 1.8), (0.5, 1.95), (0.9, 1.4), (0.85, 0.5), (0.45, 0.0), (0.05, 0.05)]], 1.0),
    "E": ([[(0.85, 1.7), (0.55, 1.92), (0.25, 1.75), (0.35, 1.15), (0.6, 1.0), (0.3, 0.95), (0.05, 0.55), (0.2, 0.05), (0.6, 0.0), (0.9, 0.2)]], 1.0),
    "F": ([[(0.15, 1.85), (0.5, 1.9), (1.0, 1.92)], [(0.55, 1.9), (0.45, 1.0), (0.3, 0.1), (0.1, 0.0)], [(0.25, 0.95), (0.75, 1.0)]], 0.95),
    "G": ([[(0.95, 1.65), (0.7, 1.9), (0.3, 1.7), (0.05, 1.0), (0.15, 0.25), (0.5, 0.0), (0.85, 0.3), (0.9, 0.9), (0.55, 0.85)]], 1.0),
    "H": ([[(0.15, 1.9), (0.1, 0.0)], [(0.8, 1.9), (0.75, 0.0)], [(0.12, 0.95), (0.78, 1.0)]], 1.0),
    "I": ([[(0.1, 1.8), (0.45, 1.92), (0.65, 1.9)], [(0.45, 1.9), (0.38, 0.95), (0.3, 0.05), (0.05, 0.0)]], 0.75),
    "K": ([[(0.15, 1.9), (0.1, 0.0)], [(0.85, 1.9), (0.15, 0.85), (0.85, 0.0)]], 1.0),
    "L": ([[(0.55, 1.65), (0.7, 1.9), (0.45, 1.85), (0.3, 1.0), (0.15, 0.15), (0.0, 0.05), (0.2, 0.0), (0.6, 0.05), (0.9, 0.1)]], 1.0),
    "M": ([[(0.0, 0.0), (0.12, 1.0), (0.2, 1.9), (0.45, 0.6), (0.7, 1.9), (0.8, 1.0), (0.9, 0.0)]], 1.1),
    "P": ([[(0.15, 1.9), (0.12, 1.0), (0.08, 0.0)], [(0.0, 1.75), (0.4, 1.95), (0.8, 1.7), (0.7, 1.1), (0.15, 0.95)]], 0.9),
    "S": ([[(0.85, 1.75), (0.6, 1.92), (0.25, 1.7), (0.3, 1.25), (0.75, 0.85), (0.8, 0.3), (0.45, 0.0), (0.05, 0.2)]], 0.95),
    "T": ([[(0.0, 1.85), (0.5, 1.92), (1.0, 1.88)], [(0.5, 1.9), (0.42, 0.95), (0.38, 0.05), (0.2, 0.0)]], 0.95),
    "U": ([[(0.05, 1.9), (0.1, 0.6), (0.35, 0.0), (0.65, 0.2), (0.8, 1.0), (0.83, 1.9), (0.8, 0.6), (0.85, 0.05), (1.0, 0.1)]], 1.05),
    "V": ([[(0.0, 1.9), (0.3, 0.9), (0.45, 0.0), (0.65, 1.0), (0.95, 1.9)]], 1.0),
    "N": ([[(0.05, 0.0), (0.12, 1.9), (0.75, 0.0), (0.82, 1.9)]], 0.95),
    "R": ([[(0.15, 1.9), (0.1, 0.0)], [(0.0, 1.75), (0.4, 1.95), (0.8, 1.7), (0.7, 1.1), (0.15, 0.95), (0.55, 0.6), (0.85, 0.0)]], 0.95),
    "0": ([[(0.5, 1.6), (0.15, 1.3), (0.05, 0.6), (0.3, 0.0), (0.6, 0.1), (0.75, 0.9), (0.65, 1.5), (0.5, 1.6)]], 0.85),
    "1": ([[(0.15, 1.3), (0.45, 1.6), (0.4, 0.8), (0.35, 0.0)]], 0.6),
    "2": ([[(0.1, 1.3), (0.4, 1.6), (0.7, 1.4), (0.6, 0.9), (0.05, 0.0), (0.4, 0.05), (0.8, 0.0)]], 0.9),
    "3": ([[(0.1, 1.45), (0.45, 1.6), (0.7, 1.35), (0.35, 0.9), (0.75, 0.6), (0.6, 0.1), (0.3, 0.0), (0.05, 0.2)]], 0.85),
    "4": ([[(0.55, 1.6), (0.05, 0.5), (0.8, 0.55)], [(0.6, 1.1), (0.55, 0.0)]], 0.9),
    "5": ([[(0.75, 1.6), (0.3, 1.58), (0.2, 0.95), (0.55, 1.0), (0.75, 0.55), (0.55, 0.05), (0.1, 0.15)]], 0.85),
    "6": ([[(0.7, 1.55), (0.35, 1.3), (0.1, 0.6), (0.3, 0.0), (0.65, 0.2), (0.65, 0.75), (0.3, 0.75), (0.15, 0.5)]], 0.85),
    "7": ([[(0.05, 1.55), (0.8, 1.6), (0.4, 0.7), (0.25, 0.0)]], 0.85),
    "8": ([[(0.6, 1.45), (0.4, 1.6), (0.15, 1.35), (0.65, 0.6), (0.55, 0.05), (0.2, 0.05), (0.15, 0.5), (0.7, 1.2), (0.6, 1.45)]], 0.85),
    "9": ([[(0.65, 1.2), (0.35, 0.85), (0.12, 1.15), (0.4, 1.6), (0.68, 1.3), (0.6, 0.6), (0.45, 0.0)]], 0.85),
    ".": ([[(0.12, 0.03), (0.17, 0.06)]], 0.4),
    ",": ([[(0.2, 0.08), (0.1, -0.3)]], 0.4),
    "'": ([[(0.22, 1.85), (0.12, 1.4)]], 0.32),
    "’": ([[(0.22, 1.85), (0.12, 1.4)]], 0.32),
    "!": ([[(0.27, 1.85), (0.18, 0.5)], [(0.13, 0.03), (0.18, 0.06)]], 0.5),
    "?": ([[(0.1, 1.5), (0.4, 1.85), (0.65, 1.5), (0.35, 0.95), (0.3, 0.5)], [(0.27, 0.03), (0.32, 0.06)]], 0.75),
    "-": ([[(0.05, 0.55), (0.55, 0.6)]], 0.65),
    "–": ([[(0.05, 0.55), (0.85, 0.6)]], 0.95),
    "(": ([[(0.45, 1.9), (0.15, 0.9), (0.4, -0.3)]], 0.55),
    ")": ([[(0.1, 1.9), (0.35, 0.9), (0.05, -0.3)]], 0.55),
    ":": ([[(0.15, 0.85), (0.19, 0.88)], [(0.12, 0.03), (0.16, 0.06)]], 0.4),
    ";": ([[(0.15, 0.85), (0.19, 0.88)], [(0.18, 0.08), (0.08, -0.3)]], 0.4),
    "°": ([[(0.25, 1.85), (0.1, 1.7), (0.25, 1.5), (0.4, 1.7), (0.25, 1.85)]], 0.55),
}
ACC = {"é": ("e", "acute"), "è": ("e", "grave"), "ê": ("e", "circ"), "à": ("a", "grave"), "â": ("a", "circ"),
       "ç": ("c", "ced"), "ô": ("o", "circ"), "î": ("i", "circ"), "ù": ("u", "grave"), "û": ("u", "circ"), "ë": ("e", "trema")}


def accent_strokes(kind, cx):
    if kind == "acute": return [[(cx - 0.05, 1.22), (cx + 0.22, 1.52)]]
    if kind == "grave": return [[(cx + 0.15, 1.22), (cx - 0.12, 1.5)]]
    if kind == "circ": return [[(cx - 0.2, 1.18), (cx, 1.42), (cx + 0.2, 1.18)]]
    if kind == "ced": return [[(cx, 0.0), (cx + 0.08, -0.15), (cx - 0.1, -0.32)]]
    if kind == "trema": return [[(cx - 0.15, 1.3), (cx - 0.12, 1.33)], [(cx + 0.15, 1.3), (cx + 0.18, 1.33)]]
    return []


def catmull(pts, n=8):
    p = np.asarray(pts, np.float64)
    if len(p) < 3:
        t = np.linspace(0, 1, max(2, n))[:, None]
        return p[0] + (p[-1] - p[0]) * t if len(p) == 2 else p
    P = np.vstack([2 * p[0] - p[1], p, 2 * p[-1] - p[-2]])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(P[-2])
    return np.asarray(out)


def word_strokes(word, r, jit=0.045):
    """Strokes of one word in unit space: list of (glyph_index, points(N,2)) in pen order, and the word's advance.
    Glyph i owns the strokes tagged i; a joined run of lowercase letters is ONE spline, split per glyph afterwards."""
    strokes = []; x = 0.0; run = []; run_owner = []; prev_high = False
    def flush():
        nonlocal run, run_owner
        if len(run) >= 2:
            dense = catmull(run, 9)
            own = np.repeat(run_owner, 9)[:len(dense)]
            own = np.r_[own, [run_owner[-1]] * (len(dense) - len(own))]
            for gi in sorted(set(own)):
                idx = np.nonzero(own == gi)[0]
                a, b = max(0, idx[0] - 1), min(len(dense), idx[-1] + 2)
                strokes.append((gi, dense[a:b]))
        run, run_owner = [], []
    for gi, ch in enumerate(word):
        base, acc = ACC.get(ch, (ch, None))
        sc = r.uniform(0.93, 1.08); wsc = r.uniform(0.9, 1.1)
        if base in G:
            pts = [(x + px * wsc + r.normal(0, jit), py * sc + r.normal(0, jit)) for px, py in G[base]]
            if run:
                pts = pts[1:] if not prev_high else [(x + 0.05, 0.82)] + pts[2:]
            run += pts; run_owner += [gi] * len(pts)
            for st in EXTRA.get(base, []):
                strokes.append((gi, catmull([(x + px * wsc + r.normal(0, jit), py * sc + r.normal(0, jit)) for px, py in st], 4)))
            if acc:
                for st in accent_strokes(acc, x + 0.42 * wsc):
                    strokes.append((gi, catmull([(px + r.normal(0, jit * 0.6), py + r.normal(0, jit * 0.6)) for px, py in st], 4)))
            adv = G[base][-1][0] * wsc + 0.02
            prev_high = base in HIGH_EXIT
        else:
            flush(); prev_high = False
            sts, adv0 = LIFT.get(base, ([], 0.6))
            for st in sts:
                strokes.append((gi, catmull([(x + px * wsc + r.normal(0, jit), py * sc + r.normal(0, jit)) for px, py in st], 9)))
            adv = adv0 * wsc + 0.08
        x += adv
    flush()
    strokes.sort(key=lambda s: s[0])
    return strokes, x


class Line:
    """Baseline drift and slant for one written line: a slow tilt plus a long wave across the whole line."""
    def __init__(self, r, xh):
        self.tilt = r.normal(0, 0.012); self.amp = r.uniform(0.04, 0.09) * xh; self.ph = r.uniform(0, 6.3)
        self.lam = r.uniform(4, 8) * xh * 4; self.slant0 = r.normal(13, 3); self.sl_amp = r.uniform(2, 5); self.sph = r.uniform(0, 6.3)

    def dy(self, u):
        return self.tilt * u + self.amp * math.sin(2 * math.pi * u / self.lam + self.ph)

    def slant(self, u):
        return math.radians(self.slant0 + self.sl_amp * math.sin(2 * math.pi * u / (self.lam * 1.7) + self.sph))


def layout(text, x, y, xh, maxw, line_h, r):
    """Place words: returns list of (char_index_in_text, page_points) per stroke, plus end pen position."""
    out = []; ci = 0; cx = x; cy = y; ln = Line(r, xh); lx0 = x
    words = text.split(" ")
    for wi, wd in enumerate(words):
        if wd == "":
            cx += 0.5 * xh; ci += 1; continue
        if wd in ("\\n", "\n"):
            cx, cy = x + r.normal(0, 0.15 * xh), cy + line_h * r.uniform(0.97, 1.05); ln = Line(r, xh); lx0 = cx; ci += len(wd) + 1; continue
        strokes, adv = word_strokes(wd, r)
        wpx = adv * xh
        if maxw and cx + wpx > x + maxw and cx > x + 1:
            cx, cy = x + r.normal(0, 0.15 * xh), cy + line_h * r.uniform(0.97, 1.05); ln = Line(r, xh); lx0 = cx
        for gi, pts in strokes:
            u = cx + pts[:, 0] * xh - lx0
            sl = np.array([ln.slant(v) for v in u])
            px = cx + pts[:, 0] * xh + np.tan(sl) * pts[:, 1] * xh
            py = cy + ln.dy(cx - lx0) - pts[:, 1] * xh + np.array([ln.dy(v) - ln.dy(cx - lx0) for v in u])
            out.append((ci + gi, np.stack([px, py], 1)))
        cx += wpx + xh * r.uniform(0.75, 1.0)
        ci += len(wd) + 1
    return out, (cx, cy)


def draw_stroke(canvas, pts, width, SS, r, press=1.0):
    """Felt nib: width follows direction (downstrokes heavier), with a little pressure noise."""
    p = pts * SS
    if len(p) < 2:
        return
    d = np.diff(p, axis=0); L = np.hypot(d[:, 0], d[:, 1]) + 1e-6
    down = np.clip(d[:, 1] / L, -1, 1)                   # +1 = moving down the page
    w = width * press * (0.72 + 0.42 * np.clip(down, 0, 1) - 0.1 * np.clip(-down, 0, 1))
    w *= 1 + 0.08 * np.sin(np.cumsum(L) / (SS * 9) + r.uniform(0, 6))
    for i in range(len(d)):
        t = max(1, int(round(w[i] * SS)))
        cv2.line(canvas, (int(round(p[i, 0] * 4)), int(round(p[i, 1] * 4))), (int(round(p[i + 1, 0] * 4)), int(round(p[i + 1, 1] * 4))),
                 1.0, t, cv2.LINE_AA, shift=2)


def letters(W, H, text, x, y, xh, width, seed, maxw=None, line_h=None, SS=3):
    """Per-character coverage maps (H,W float32) in pen order, for write-on; and the end pen position."""
    r = np.random.default_rng(seed)
    placed, end = layout(text, x, y, xh, maxw, line_h or 2.8 * xh, r)
    by = {}
    for ci, pts in placed:
        by.setdefault(ci, []).append(pts)
    out = []
    for ci in sorted(by):
        cv = np.zeros((H * SS, W * SS), np.float32); press = r.uniform(0.85, 1.15)
        for pts in by[ci]:
            draw_stroke(cv, pts, width, SS, r, press)
        out.append((ci, cv2.resize(np.clip(cv, 0, 1), (W, H), interpolation=cv2.INTER_AREA)))
    return out, end


def write(acc_layer, SS, text, x, y, xh, width, seed, maxw=None, line_h=None):
    """Draw the whole text into a supersampled coverage array (pen.Ink.a, factor SS)."""
    r = np.random.default_rng(seed)
    placed, end = layout(text, x, y, xh, maxw, line_h or 2.8 * xh, r)
    H, W = acc_layer.shape
    cv = np.zeros((H, W), np.float32)
    for ci, pts in placed:
        draw_stroke(cv, pts, width, SS, r, r.uniform(0.85, 1.15))
    np.maximum(acc_layer, np.clip(cv, 0, 1), out=acc_layer)
    return end

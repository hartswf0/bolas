"""PAPER HANDS test shot: the lightbox, scissor-cut pieces, hand lettering, compositor.

Everything here is handmade for this work in code: the translucent paper sheet (fibres + cloud
generated into the sheet), the felt board, scissor-faceted card outlines (6-12 px facets at
page resolution, generated ONCE per piece in its own local frame, so nothing boils), the
single-stroke mixed-case alphabet, and the occlusion compositor (SCION #45).
Coordinates: page px of the 3200 x 1800 page.
"""
import math
import numpy as np
import cv2

PAGE_W, PAGE_H = 3200, 1800
PANELS = {1: (70, 70, 1090, 875), 2: (1125, 70, 2115, 875), 3: (2150, 70, 3130, 875),
          4: (70, 910, 1600, 1730), 5: (1635, 910, 2360, 1730), 6: (2395, 910, 3130, 1730)}

# palette (sampled from kf-2, see plan section 7)
PAPER_C = np.array([233, 225, 210], np.float32)      # #e9e1d2 warm centre
TAN = np.array([217, 202, 176], np.float32)          # #d9cab0 dial inlay / note
VELLUM = np.array([246, 242, 230], np.float32)       # #f6f2e6
BOARD = np.array([58, 55, 50], np.float32)           # #3a3732
SIL_K = 0.066                                        # silhouette = paper * k  -> ~#0f0e0d
BRASS = np.array([120, 98, 52], np.float32)          # #786234
INK = np.array([16, 15, 14], np.float32)


# ------------------------------------------------------------------ the sheet ---
def _cloud(h, w, rng, scale):
    small = rng.normal(0, 1, (max(2, h // scale), max(2, w // scale))).astype(np.float32)
    big = cv2.resize(small, (w, h), interpolation=cv2.INTER_CUBIC)
    return cv2.GaussianBlur(big, (0, 0), scale * 0.35)


def make_page(seed=7):
    """Full 3200x1800 RGB float page: felt board + six lamp-lit fibrous paper windows."""
    rng = np.random.default_rng(seed)
    H, W = PAGE_H, PAGE_W
    felt = rng.normal(0, 1, (H, W)).astype(np.float32)
    felt = cv2.GaussianBlur(felt, (0, 0), 1.2) * 2.2 + _cloud(H, W, rng, 60) * 1.5
    page = BOARD[None, None, :] + felt[..., None]
    for k, (x0, y0, x1, y1) in PANELS.items():
        w, h = x1 - x0, y1 - y0
        # fibres: thousands of short curved strands, in every direction, seen in transmitted light
        fib = np.zeros((h, w), np.float32)
        n = int(w * h / 90)
        for _ in range(n):
            x, y = rng.uniform(0, w), rng.uniform(0, h)
            a = rng.uniform(0, math.pi); L = rng.uniform(12, 70); c = rng.normal(0, 0.03)
            pts = []
            for s in np.linspace(0, L, 6):
                pts.append((x + math.cos(a + c * s) * s, y + math.sin(a + c * s) * s))
            v = rng.choice([-1.0, 1.0]) * rng.uniform(0.4, 1.0)
            cv2.polylines(fib, [np.int32(pts)], False, v, 1, cv2.LINE_AA)
        fib = cv2.GaussianBlur(fib, (0, 0), 0.7)
        cloud = _cloud(h, w, rng, 40) * 0.7 + _cloud(h, w, rng, 12) * 0.35   # flocculation
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        # one lamp behind the panel, upper-left of centre
        r2 = ((xx - w * 0.44) / (w * 0.62)) ** 2 + ((yy - h * 0.40) / (h * 0.62)) ** 2
        lamp = 1.0 - 0.115 * r2
        L = lamp * (1 + cloud * 0.018) + fib * 0.022
        page[y0:y1, x0:x1] = PAPER_C[None, None, :] * L[..., None]
    return page


# ------------------------------------------------------------ cut pieces ---
def facet(pts, seed, lo=6.0, hi=12.0, jit=0.7):
    """Scissor-cut a dense closed outline: straight facets of random length 6-12 px."""
    rng = np.random.default_rng(seed)
    P = np.asarray(pts, np.float64)
    Q = np.vstack([P, P[:1]])
    seg = np.linalg.norm(np.diff(Q, axis=0), axis=1)
    cum = np.concatenate([[0], np.cumsum(seg)])
    Ltot = cum[-1]
    out = []
    s = rng.uniform(0, lo)
    while s < Ltot:
        i = min(np.searchsorted(cum, s, side='right') - 1, len(seg) - 1)
        f = (s - cum[i]) / max(seg[i], 1e-9)
        p = Q[i] + (Q[i + 1] - Q[i]) * f
        tvec = (Q[i + 1] - Q[i]) / max(seg[i], 1e-9)
        p = p + np.array([-tvec[1], tvec[0]]) * rng.normal(0, jit)
        out.append(p)
        s += rng.uniform(lo, hi)
    return np.array(out)


def dense_poly(pts, step=3.0):
    P = np.asarray(pts, np.float64)
    out = []
    for i in range(len(P)):
        p, q = P[i], P[(i + 1) % len(P)]
        n = max(1, int(np.linalg.norm(q - p) / step))
        for j in range(n):
            out.append(p + (q - p) * j / n)
    return np.array(out)


def ellipse_pts(cx, cy, rx, ry, rot=0.0, n=120):
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    x, y = rx * np.cos(a), ry * np.sin(a)
    c, s = math.cos(rot), math.sin(rot)
    return np.stack([cx + x * c - y * s, cy + x * s + y * c], 1)


def capsule_pts(p, q, r0, r1, n=24):
    """Tapered limb outline between pivots p,q (radii r0 at p, r1 at q), round ends."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    d = q - p; L = np.linalg.norm(d)
    if L < 1e-6:
        return ellipse_pts(p[0], p[1], r0, r0)
    a = math.atan2(d[1], d[0])
    out = []
    for t in np.linspace(-np.pi / 2, np.pi / 2, n):     # cap around q
        out.append(q + r1 * np.array([math.cos(a + t), math.sin(a + t)]))
    for t in np.linspace(np.pi / 2, 3 * np.pi / 2, n):  # cap around p
        out.append(p + r0 * np.array([math.cos(a + t), math.sin(a + t)]))
    return np.array(out)


def hull(pts):
    h = cv2.convexHull(np.float32(pts)).reshape(-1, 2)
    return dense_poly(h, 3.0)


def xf(pts, ang, pos):
    """rigid transform of local piece points"""
    c, s = math.cos(ang), math.sin(ang)
    P = np.asarray(pts, float)
    return np.stack([P[:, 0] * c - P[:, 1] * s + pos[0], P[:, 0] * s + P[:, 1] * c + pos[1]], 1)


class Raster:
    """Rasteriser for a page-coordinate rectangle (x0,y0,w,h)."""

    def __init__(self, x0, y0, w, h):
        self.x0, self.y0, self.w, self.h = x0, y0, w, h

    def blank(self):
        return np.zeros((self.h, self.w), np.float32)

    def fill(self, m, pts, v=1.0):
        P = np.round((np.asarray(pts, float) - [self.x0, self.y0]) * 16).astype(np.int32)
        tmp = np.zeros((self.h, self.w), np.uint8)
        cv2.fillPoly(tmp, [P], 255, cv2.LINE_AA, 4)
        a = tmp.astype(np.float32) / 255
        m[:] = m * (1 - a) + v * a
        return a

    def line(self, m, pts, width, v=1.0):
        P = np.round((np.asarray(pts, float) - [self.x0, self.y0]) * 16).astype(np.int32)
        tmp = np.zeros((self.h, self.w), np.uint8)
        cv2.polylines(tmp, [P], False, 255, max(1, int(round(width))), cv2.LINE_AA, 4)
        a = tmp.astype(np.float32) / 255
        m[:] = m * (1 - a) + v * a
        return a

    def disc(self, m, c, r, v=1.0):
        return self.fill(m, ellipse_pts(c[0], c[1], r, r, n=24), v)


# ------------------------------------------------------- hand lettering ---
# single-stroke mixed-case alphabet built for this work (cap height = 1, y up from baseline)
def _arc(cx, cy, rx, ry, a0, a1, n=14):
    return [(cx + rx * math.cos(math.radians(a)), cy + ry * math.sin(math.radians(a))) for a in np.linspace(a0, a1, n)]


GLYPHS = {
    'Q': ([_arc(.42, .5, .40, .5, 0, 360, 30)], [[(.50, .20), (.88, -.10)]], .92),
    'W': ([[(0, 1), (.22, 0), (.46, .74), (.70, 0), (.92, 1)]], [], 1.0),
    'T': ([[(0, 1), (.72, 1.02)], [(.36, 1.0), (.36, 0)]], [], .76),
    'h': ([[(0, 1.05), (0, 0)], [(0, .40), (.09, .54), (.24, .61), (.38, .56), (.45, .42), (.46, 0)]], [], .62),
    'a': ([[(.45, .50), (.32, .60), (.15, .58), (.04, .43), (.02, .20), (.10, .04), (.25, 0), (.39, .08), (.46, .28)],
           [(.47, .61), (.47, .08), (.53, 0)]], [], .64),
    't': ([[(.17, .92), (.17, .09), (.25, 0), (.38, .05)], [(0, .60), (.38, .62)]], [], .46),
    'i': ([[(.05, .59), (.05, 0)], [(.04, .84), (.07, .88)]], [], .24),
    'm': ([[(0, .61), (0, 0)], [(0, .44), (.10, .57), (.21, .61), (.30, .52), (.31, 0)],
           [(.31, .44), (.41, .57), (.52, .61), (.60, .52), (.62, 0)]], [], .80),
    'e': ([[(.04, .31), (.46, .33), (.44, .48), (.32, .60), (.16, .59), (.04, .45), (.02, .22), (.10, .06), (.26, 0), (.43, .07)]], [], .56),
    's': ([[(.40, .52), (.28, .61), (.12, .59), (.04, .48), (.10, .37), (.33, .27), (.42, .14), (.34, .03), (.16, 0), (.02, .08)]], [], .52),
    '?': ([[(.03, .80), (.13, .97), (.31, 1.01), (.44, .88), (.42, .72), (.26, .57), (.24, .33)], [(.23, .07), (.26, .03)]], [], .56),
    'u': ([[(0, .61), (0, .17), (.10, .03), (.24, 0), (.37, .07), (.45, .22)], [(.46, .61), (.46, 0)]], [], .62),
    'r': ([[(0, .61), (0, 0)], [(0, .38), (.10, .54), (.24, .61), (.35, .57)]], [], .44),
    'p': ([[(0, .61), (0, -.38)], [(0, .44), (.10, .57), (.26, .61), (.42, .50), (.47, .30), (.41, .10), (.25, 0), (.09, .03), (0, .13)]], [], .60),
    'o': ([_arc(.25, .30, .25, .305, 0, 360, 24)], [], .60),
    'n': ([[(0, .61), (0, 0)], [(0, .41), (.10, .55), (.24, .61), (.38, .55), (.45, .41), (.46, 0)]], [], .62),
    '!': ([[(.06, 1.02), (.05, .30)], [(.04, .06), (.07, .02)]], [], .26),
    'k': ([[(0, 1.05), (0, 0)], [(.40, .62), (.02, .25)], [(.13, .34), (.44, 0)]], [], .52),
    ' ': ([], [], .30),
}


def text_strokes(text, x, y, cap, seed=0, line_gap=1.45, align='center'):
    """Return list of polylines (page px) for multi-line hand lettering centred at x, first baseline y."""
    rng = np.random.default_rng(seed)
    lines = text.split('\n')
    out = []
    for li, ln in enumerate(lines):
        adv = sum(GLYPHS[c][2] + 0.10 for c in ln) * cap
        cx = x - adv / 2 if align == 'center' else x
        by = y + li * cap * line_gap
        for c in ln:
            strokes, extra, a = GLYPHS[c]
            rot = rng.normal(0, 0.035); dy = rng.normal(0, cap * 0.025); sc = 1 + rng.normal(0, 0.03)
            for st in strokes + extra:
                pts = []
                for (u, v) in st:
                    u2, v2 = u * sc, v * sc
                    xr = u2 * math.cos(rot) - v2 * math.sin(rot)
                    yr = u2 * math.sin(rot) + v2 * math.cos(rot)
                    pts.append((cx + xr * cap, by - yr * cap + dy))
                out.append(pts)
            cx += (a + 0.10) * cap
    return out


def text_box(text, cap, line_gap=1.45):
    lines = text.split('\n')
    w = max(sum(GLYPHS[c][2] + 0.10 for c in ln) for ln in lines) * cap
    h = cap * (1 + line_gap * (len(lines) - 1))
    return w, h


class Card:
    """A vellum balloon card with a cut black rim, a tail running off the panel, and a rod.
    Built once (fixed facets); moved rigidly."""

    def __init__(self, text, cap, tail_vec, seed, rod_vec=(0, -1)):
        self.text, self.cap, self.seed = text, cap, seed
        w, h = text_box(text, cap)
        self.rx, self.ry = w / 2 * 1.18 + cap * 0.6, h / 2 * 1.2 + cap * 0.55
        rim = 7
        self.outer = facet(ellipse_pts(0, 0, self.rx + rim, self.ry + rim), seed, 7, 11, 0.6)
        self.inner = facet(ellipse_pts(0, 0, self.rx, self.ry), seed + 1, 7, 11, 0.5)
        tv = np.asarray(tail_vec, float)
        ang = math.atan2(tv[1], tv[0]); L = np.linalg.norm(tv)
        base = np.array([self.rx * 0.75 * math.cos(ang), self.ry * 0.75 * math.sin(ang)])
        nrm = np.array([-math.sin(ang), math.cos(ang)])
        tip = tv
        self.tail_o = facet(dense_poly([base + nrm * 30, tip + nrm * 7, tip - nrm * 7, base - nrm * 30]), seed + 2, 7, 11, 0.4)
        tip_i = tip - (tv / L) * 2
        self.tail_i = facet(dense_poly([base + nrm * 22, tip_i + nrm * 1.5, tip_i - nrm * 1.5, base - nrm * 22]), seed + 3, 7, 11, 0.3)
        self.rod_vec = np.asarray(rod_vec, float)
        w0, h0 = text_box(text, cap)
        self.strokes = text_strokes(text, 0, -h0 / 2 + cap, cap, seed)

    def draw(self, R, dark, vel, ink, pos, rod_len=1400):
        """dark: black card/rod coverage; vel: vellum coverage; ink: lettering coverage"""
        p = np.asarray(pos, float)
        # rod from the card edge out under the board
        rstart = p + self.rod_vec * (self.ry * 0.9)
        R.line(dark, [rstart, p + self.rod_vec * rod_len], 7)
        R.fill(dark, self.tail_o + p)
        R.fill(dark, self.outer + p)
        a = R.fill(vel, self.tail_i + p)
        b = R.fill(vel, self.inner + p)
        for st in self.strokes:
            R.line(ink, np.asarray(st) + p, max(3, self.cap * 0.11))


def composite(R, paper, hand_groups, set_dark, card_layers, board_mask, inlay=None, pins=()):
    """Occlusion DAG (#45), back to front:
       lamp -> hands behind the screen (soft, penumbra) -> paper screen -> set pieces against the screen (sharp)
       -> vellum cards and rods in front -> felt board mat (opaque) in front of everything.
    hand_groups: list of (D, sigma, offset(dx,dy), shadow_strength)."""
    rgb = paper.copy()
    Dtot = np.zeros(paper.shape[:2], np.float32)
    for D, sig, off, st in hand_groups:
        body = cv2.GaussianBlur(D, (0, 0), sig)
        M = np.float32([[1, 0, off[0]], [0, 1, off[1]]])
        sh = cv2.warpAffine(D, M, (D.shape[1], D.shape[0]))
        pen = cv2.GaussianBlur(sh, (0, 0), sig * 2.2 + 2) * st
        Dtot = np.maximum(Dtot, np.maximum(body, pen))
    rgb = rgb * (1 - (1 - SIL_K) * Dtot[..., None])
    if inlay is not None:
        Mi, level, sig = inlay
        Mi = cv2.GaussianBlur(Mi, (0, 0), sig)
        lamp = paper / PAPER_C[None, None, :]
        col = TAN[None, None, :] * lamp * level
        rgb = rgb * (1 - Mi[..., None]) + col * Mi[..., None]
    for (c, r, vis) in pins:
        m = R.blank(); R.disc(m, c, r)
        m *= vis
        rgb = rgb * (1 - m[..., None]) + BRASS[None, None, :] * m[..., None]
    sd = cv2.GaussianBlur(set_dark, (0, 0), 0.6)
    rgb = rgb * (1 - sd[..., None]) + (paper * SIL_K) * sd[..., None]
    for dark, vel, ink in card_layers:
        under = rgb.copy()
        vcol = VELLUM[None, None, :] * 0.78 + under * 0.24
        rgb = rgb * (1 - dark[..., None]) + (paper * SIL_K) * dark[..., None]
        rgb = rgb * (1 - vel[..., None]) + vcol * vel[..., None]
        rgb = rgb * (1 - ink[..., None]) + INK[None, None, :] * ink[..., None]
    # mat edge: a faint bevel shadow just inside each window
    bm = cv2.GaussianBlur(board_mask, (0, 0), 2.5)
    rgb = rgb * (1 - 0.35 * np.clip(bm - board_mask, 0, 1)[..., None])
    rgb = rgb * (1 - board_mask[..., None]) + paper * board_mask[..., None]   # paper array holds the felt in gutters
    return rgb

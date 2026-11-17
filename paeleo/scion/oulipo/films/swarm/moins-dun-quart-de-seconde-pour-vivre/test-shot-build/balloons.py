"""Balloon plane: hand balloons lettered stroke by stroke, on their own RGBA plane.

Every balloon is a list of real pen strokes (outline first, then glyph strokes in
pen order) with a time schedule, so it can be written on frame by frame.
Rendering at 1080 (2x panel) and reducing once, premultiplied, to 540.

#38 drawing library on the balloon plane: each balloon has three hand
variants (v0 canonical + two boil redraws). While writing, a DP decoder picks
the variant per frame with a minimum hold of 2 frames and a flicker penalty;
after writing it is locked to v0, which is the published balloon PNG.
"""
import math
import numpy as np
from PIL import Image, ImageDraw
from hand import layout, balloon_shape, brush, wobble, length, catmull
from plate2 import INK_V

FPS = 24
K = 2                    # supersample
GLYPH_S = 1 / 9.0        # pen speed: 9 glyphs per second
SPACE_S = 0.05
LINE_S = 0.12
LIFT = 0.22              # share of a glyph's time spent in pen lifts between its strokes
OUTLINE_F = 6

# panel-space (540) specs: lines, centre, cap size, tail tip, seed
SPECS = {
    'A1': (["IF I OPEN IT,", "I'LL KNOW."], (300, 86), 22, (400, 200), 201),
    'A2': (["IF I DON'T,", "I CAN STILL", "HOPE."], (222, 96), 22, (372, 206), 202),
    'A4': (["HOPE IT IS,", "THEN."], (330, 84), 22, (420, 200), 204),
    'B1': (["ME? I'VE BEEN", "ON THIS BENCH", "SINCE NINE."], (212, 96), 22, (372, 206), 211),
    'B2': (["ASK THE LAMP."], (368, 78), 22, (428, 196), 212),
    'B3': (["AND LOOK -", "STILL SEALED."], (330, 90), 22, (418, 202), 213),
    'B4': (["WHY WOULD I", "OPEN SOMEONE", "ELSE'S?"], (222, 98), 22, (372, 206), 214),
}
PEN_HOLD = {'B4': ("OPEN SOMEONE", 10)}  # 10-frame pen hold after this line


class Balloon:
    def __init__(self, key):
        self.key = key
        lines, (cx, cy), size, tail, seed = SPECS[key]
        self.lines = lines
        rng = np.random.default_rng(seed)
        S = size * K
        strokes, (tw, th) = layout(lines, S, rng)
        # glyph bookkeeping: rebuild per-glyph stroke counts in layout order
        from hand import GLYPHS
        self.glyph_of = []
        g = 0
        self.events = []  # (kind, index) in order
        for li, line in enumerate(lines):
            for ch in line.upper():
                n = len(GLYPHS.get(ch, GLYPHS[' '])[1])
                self.events.append(('glyph', ch, n, li))
            self.events.append(('line', None, 0, li))
        rw = (tw / 2 + S * 0.9 * 1.3) * 1.08
        rh = (th / 2 + S * 0.85 * 1.3) * 1.12
        CX, CY = cx * K, cy * K
        self.box = (cx - rw / K, cy - rh / K, cx + rw / K, cy + rh / K)
        self.outline = balloon_shape(CX, CY, rw, rh, rng, (tail[0] * K, tail[1] * K))
        self.centre = (CX, CY)
        self.strokes = [[(x + CX - tw / 2, y + CY - th / 2) for x, y in s] for s in strokes]
        self.stroke_w = 3.8 * K      # ~3.8 px single-stroke capitals at 540
        self.outline_w = 5.0 * K
        self._schedule()
        # boil variants (#38 illustrated candidate states): v0 canonical, v1/v2 redraws
        self.variants = [self._variant(v) for v in range(3)]
        self.path = self._decode()

    # ---------------------------------------------------------- schedule
    def _schedule(self):
        """Per-stroke (t0, t1) in seconds from balloon start; outline first."""
        t = OUTLINE_F / FPS
        sched = []
        si = 0
        hold_line = PEN_HOLD.get(self.key)
        self.pen_hold = None
        for kind, ch, n, li in self.events:
            if kind == 'line':
                if hold_line and self.lines[li] == hold_line[0]:
                    self.pen_hold = (t, t + hold_line[1] / FPS)
                    t += hold_line[1] / FPS
                else:
                    t += LINE_S
                continue
            if n == 0:
                t += SPACE_S
                continue
            ss = self.strokes[si:si + n]
            lens = [max(1.0, length(s)) for s in ss]
            ink_t = GLYPH_S * (1 - LIFT)
            lift_t = GLYPH_S * LIFT / max(1, n)
            for s, L in zip(ss, lens):
                d = ink_t * L / sum(lens)
                sched.append((t, t + d, L, ch))
                t += d + lift_t
            si += n
        assert si == len(self.strokes)
        self.sched = sched
        self.end = t
        self.end_f = int(math.ceil(t * FPS))

    # ---------------------------------------------------------- variants
    def _variant(self, v):
        if v == 0:
            return self.outline, self.strokes
        rng = np.random.default_rng(1000 * v + SPECS[self.key][4])
        o = wobble(self.outline, 1.4 * K, rng, 5)
        st = []
        for s in self.strokes:
            dx, dy = rng.normal(0, 0.45 * K, 2)
            st.append([(x + dx, y + dy) for x, y in s])
        return o, st

    def _decode(self):
        """DP over (variant) per writing frame: min hold 2, flicker/stagnation costs, end on v0."""
        n = self.end_f + 1
        V = 3
        INF = 1e9
        # cost of state at frame: want boil (non-canonical) while writing, canonical at the end
        def unary(f, v):
            if f >= self.end_f:
                return 0 if v == 0 else INF
            return 0.0 if v else 0.4
        # state = (v, hold_len capped at 3)
        best = {}
        back = {}
        for v in range(V):
            best[(0, v, 1)] = unary(0, v)
        for f in range(1, n):
            for (ff, v, h), c in list(best.items()):
                if ff != f - 1:
                    continue
                for w in range(V):
                    if w == v:
                        nh = min(h + 1, 3)
                        tc = 0.6 if h >= 2 else 0.0        # holding longer than 2 = no boil
                    else:
                        if h < 2:
                            continue                        # minimum-duration hold
                        tc = 0.1
                    cost = c + tc + unary(f, w)
                    key = (f, w, nh if w == v else 1)
                    if cost < best.get(key, INF):
                        best[key] = cost
                        back[key] = (f - 1, v, h)
        end = min((k for k in best if k[0] == n - 1), key=lambda k: best[k])
        path = []
        k = end
        while True:
            path.append(k[1])
            if k[0] == 0:
                break
            k = back[k]
        path = path[::-1]
        assert len(path) == n and path[-1] == 0
        runs = [len(list(g)) for _, g in __import__('itertools').groupby(path)]
        assert min(runs[:-1] or [2]) >= 2, runs
        return path

    # ---------------------------------------------------------- render
    def render(self, f=None):
        """RGBA-ish (colour L, alpha L) at 540 for frame f from balloon start; None = final."""
        final = f is None or f >= self.end_f
        tt = self.end + 1 if final else f / FPS
        v = 0 if final else self.path[max(0, f)]
        outline, strokes = self.variants[v]
        W = 540 * K
        C = Image.new('L', (W, W), 255)
        A = Image.new('L', (W, W), 0)
        dc, da = ImageDraw.Draw(C), ImageDraw.Draw(A)
        of = min(1.0, tt / (OUTLINE_F / FPS)) if tt >= 0 else 0.0
        if of > 0:
            n = len(outline)
            m = max(2, int(round(n * of)))
            poly = outline if of >= 1 else [self.centre] + outline[:m]
            dc.polygon(poly, fill=255)
            da.polygon(poly, fill=255)
            rng = np.random.default_rng(7 + SPECS[self.key][4])
            seg = outline + [outline[0]]
            brush(dc, seg, self.outline_w, rng, taper=(0.05, 0.05), press=0.25, upto=of)
            rng = np.random.default_rng(7 + SPECS[self.key][4])
            brush(da, seg, self.outline_w, rng, col=255, taper=(0.05, 0.05), press=0.25, upto=of)
        for i, (s, (t0, t1, L, ch)) in enumerate(zip(strokes, self.sched)):
            if tt <= t0:
                break
            u = min(1.0, (tt - t0) / max(1e-6, t1 - t0))
            u = u * u * (3 - 2 * u)  # ease in/out along each stroke
            rng = np.random.default_rng(31 * i + SPECS[self.key][4])
            brush(dc, s, self.stroke_w, rng, taper=(0.15, 0.2), press=0.18, upto=u)
        C = np.asarray(C, np.float64)
        A = np.asarray(A, np.float64) / 255.0
        Ct = INK_V + C * (255 - INK_V) / 255.0
        pm = Image.fromarray((Ct * A).astype(np.float32), 'F').resize((540, 540), Image.LANCZOS)
        a = Image.fromarray(A.astype(np.float32), 'F').resize((540, 540), Image.LANCZOS)
        return np.asarray(pm, np.float64), np.clip(np.asarray(a, np.float64), 0, 1)

    def onsets(self):
        return [(t0, t1, L, ch) for (t0, t1, L, ch) in self.sched]


def composite(plate, layer):
    """plate: PIL L 540; layer: (premultiplied colour, alpha) -> PIL L."""
    p = np.asarray(plate, np.float64)
    if layer is None:
        return plate.copy()
    pm, a = layer
    out = p * (1 - a) + pm
    return Image.fromarray(np.clip(np.round(out), INK_V, 255).astype(np.uint8), 'L')

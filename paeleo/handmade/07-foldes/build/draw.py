"""SCION 07 · pen and wash primitives. A contour is drawn as an ink ribbon over a flat wash, the way Hunger's lines carry a
wash of colour. Coordinates passed in are screen pixels at 1x; drawing happens at SS x and is reduced (box filter)."""
import math
from PIL import Image, ImageDraw

SS = 3
INK = (26, 24, 30)


def cr(pts, closed=False, n=7):
    """Catmull-Rom through the key points (the contour passes through every correspondence point)."""
    P = [tuple(p) for p in pts]
    if len(P) < 2:
        return P
    if len(P) == 2:
        return [(P[0][0] + (P[1][0] - P[0][0]) * i / n, P[0][1] + (P[1][1] - P[0][1]) * i / n) for i in range(n + 1)]
    out = []
    m = len(P)
    rng = range(m) if closed else range(m - 1)
    for i in rng:
        p0 = P[(i - 1) % m] if closed else P[max(i - 1, 0)]
        p1 = P[i]
        p2 = P[(i + 1) % m] if closed else P[i + 1]
        p3 = P[(i + 2) % m] if closed else P[min(i + 2, m - 1)]
        for j in range(n):
            t = j / n; t2 = t * t; t3 = t2 * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    if closed:
        out.append(out[0])
    else:
        out.append(P[-1])
    return out


def normals(poly):
    N = []
    for i in range(len(poly)):
        a = poly[max(i - 1, 0)]; b = poly[min(i + 1, len(poly) - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.0
        N.append((-dy / L, dx / L))
    return N


def ribbon(poly, w0, seed=0.0, taper=(1.0, 1.0)):
    """ink ribbon polygon around a polyline. Width w0 px, a slow pen-pressure swell, tapered ends."""
    if len(poly) < 2:
        return None
    N = normals(poly)
    n = len(poly)
    L, R = [], []
    for i, (p, nv) in enumerate(zip(poly, N)):
        u = i / (n - 1)
        w = w0 * (0.86 + 0.28 * (0.5 + 0.5 * math.sin(seed + u * 5.3)))
        if u < 0.12: w *= taper[0] + (1 - taper[0]) * (u / 0.12)
        if u > 0.88: w *= taper[1] + (1 - taper[1]) * ((1 - u) / 0.12)
        h = max(w, 0.35) / 2
        L.append((p[0] + nv[0] * h, p[1] + nv[1] * h)); R.append((p[0] - nv[0] * h, p[1] - nv[1] * h))
    return L + R[::-1]


def limb_outline(cl, widths, fwd, sx):
    """centreline (screen px) + widths (px) -> (left side, foot arc, right side) polylines."""
    C = cr(cl, False, 6)
    n = len(C)
    nseg = len(cl) - 1
    W = []
    for i in range(n):
        f = i / (n - 1) * nseg
        k = min(int(f), nseg - 1); r = f - k
        W.append(widths[k] * (1 - r) + widths[k + 1] * r)
    N = normals(C)
    Lft = [(p[0] + nv[0] * w / 2, p[1] + nv[1] * w / 2) for p, nv, w in zip(C, N, W)]
    Rgt = [(p[0] - nv[0] * w / 2, p[1] - nv[1] * w / 2) for p, nv, w in zip(C, N, W)]
    return C, W, Lft, Rgt


class Canvas:
    def __init__(self, base):
        """base: PIL RGB image at SS scale."""
        self.im = base
        self.W, self.H = base.size

    def _paste(self, polys, color, alpha, lines=False):
        if alpha <= 0.01 or not polys:
            return
        xs = [p[0] for poly in polys for p in poly]; ys = [p[1] for poly in polys for p in poly]
        x0, y0 = int(max(min(xs) * SS - 4, 0)), int(max(min(ys) * SS - 4, 0))
        x1, y1 = int(min(max(xs) * SS + 4, self.W)), int(min(max(ys) * SS + 4, self.H))
        if x1 <= x0 or y1 <= y0:
            return
        m = Image.new('L', (x1 - x0, y1 - y0), 0)
        d = ImageDraw.Draw(m)
        for poly in polys:
            if len(poly) >= 3:
                d.polygon([(p[0] * SS - x0, p[1] * SS - y0) for p in poly], fill=255)
        if alpha < 0.999:
            m = m.point(lambda v: int(v * alpha))
        self.im.paste(color, (x0, y0, x1, y1), m)

    def fill(self, poly, color, alpha=1.0):
        self._paste([poly], color, alpha)

    def line(self, poly, w, color=INK, alpha=1.0, seed=0.0, taper=(0.35, 0.35)):
        r = ribbon(poly, w, seed, taper)
        if r:
            self._paste([r], color, alpha)

    def lines(self, polys, w, color=INK, alpha=1.0, seed=0.0, taper=(0.35, 0.35)):
        rs = [ribbon(p, w, seed + i, taper) for i, p in enumerate(polys)]
        self._paste([r for r in rs if r], color, alpha)

    def dot(self, x, y, r, color=INK, alpha=1.0):
        poly = [(x + r * math.cos(a / 10 * 2 * math.pi), y + r * math.sin(a / 10 * 2 * math.pi)) for a in range(10)]
        self._paste([poly], color, alpha)


def reduce(im):
    return im.reduce(SS)

"""A small engraving toolkit: parts are masks with a hatch field and a tone; the result is ink lines on paper.

Coordinates: a drawing has its own metric frame (mm, y up). The image frame is px = (OX + x, OY - y) at 1 px/mm.
Every part keeps a name, a layer (draw order) and its own outline, so mesh triangles can be labelled by part.
"""
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

SPACING_MUL = 1.6      # coarser engraving: lines >= 4 px apart on screen in the wide shot (no moire)
PAPER = np.array([0.94, 0.90, 0.81])
INK = np.array([0.10, 0.085, 0.075])


def catmull(points, n=12, closed=True):
    P = np.asarray(points, float)
    if closed:
        P = np.vstack([P[-1], P, P[0], P[1]])
    else:
        P = np.vstack([P[0], P, P[-1]])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    if not closed:
        out.append(P[-2])
    return np.array(out)


class Drawing:
    def __init__(self, w, h, ox, oy):
        self.w, self.h, self.ox, self.oy = w, h, ox, oy
        self.parts = []
        self.points = {}
        self.features = []        # (name, center(x,y), radius) in drawing coords: protected regions
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        self.X = xx - ox
        self.Y = oy - yy

    def to_img(self, pts):
        P = np.asarray(pts, float).reshape(-1, 2)
        return np.stack([P[:, 0] + self.ox, self.oy - P[:, 1]], 1)

    def poly_mask(self, pts):
        im = Image.new('L', (self.w, self.h), 0)
        ImageDraw.Draw(im).polygon([tuple(p) for p in self.to_img(pts)], fill=255)
        return np.array(im) > 127

    def capsules_mask(self, chain, radii):
        m = np.zeros((self.h, self.w), bool)
        chain = np.asarray(chain, float)
        for i in range(len(chain) - 1):
            a, b = chain[i], chain[i + 1]
            r0, r1 = radii[i], radii[i + 1]
            d = b - a
            L2 = max(d @ d, 1e-6)
            t = np.clip(((self.X - a[0]) * d[0] + (self.Y - a[1]) * d[1]) / L2, 0, 1)
            px, py = a[0] + t * d[0], a[1] + t * d[1]
            r = r0 + (r1 - r0) * t
            m |= (self.X - px) ** 2 + (self.Y - py) ** 2 <= r * r
        return m

    def ellipse_mask(self, c, rx, ry, ang=0.0):
        ca, sa = np.cos(ang), np.sin(ang)
        u = (self.X - c[0]) * ca + (self.Y - c[1]) * sa
        v = -(self.X - c[0]) * sa + (self.Y - c[1]) * ca
        return (u / rx) ** 2 + (v / ry) ** 2 <= 1

    def add(self, name, mask, layer, hatch, tone=0.0, spacing=13.0, cross=0.92, outline=7.0):
        """hatch: ('dir', angle) straight lines; ('axis', chain) lines along a limb, bunched at its edges;
        ('contour',) lines parallel to the part's outline."""
        self.parts.append(dict(name=name, mask=mask, layer=layer, hatch=hatch, tone=tone, spacing=spacing,
                               cross=cross, outline=outline))

    # ---------------------------------------------------------------- render
    def render(self, light=(-0.55, 0.55, 0.63), marks=()):
        """Returns RGBA float image, label map (part index, -1 outside), and per-part layer list."""
        h, w = self.h, self.w
        union = np.zeros((h, w), bool)
        for p in self.parts:
            union |= p['mask']
        # a puffy height field of the whole figure gives the light
        dist = ndimage.distance_transform_edt(union)
        hgt = np.sqrt(np.maximum(ndimage.gaussian_filter(dist, 5), 0) * 2 * 70.0)
        gy, gx = np.gradient(hgt)
        nx, ny, nz = -gx, gy, np.ones_like(gx) * 1.0
        nn = np.sqrt(nx * nx + ny * ny + nz * nz)
        L = np.array(light, float); L /= np.linalg.norm(L)
        lam = np.clip((nx * L[0] + ny * L[1] + nz * L[2]) / nn, 0, 1)
        rgb = np.ones((h, w, 3), np.float32) * PAPER
        alpha = np.zeros((h, w), np.float32)
        label = -np.ones((h, w), np.int16)
        order = sorted(range(len(self.parts)), key=lambda i: self.parts[i]['layer'])
        for i in order:
            p = self.parts[i]
            m = p['mask']
            if not m.any():
                continue
            s = p['spacing'] * SPACING_MUL
            tone = np.clip(0.08 + 0.85 * (1 - lam) ** 1.3 + p['tone'], 0, 1)
            phi, phi2 = self._fields(p)
            # engraved line: width grows with tone
            wid = (0.10 + 0.72 * tone) * s
            d1 = np.abs((phi / s) % 1.0 - 0.5) * s
            ink1 = 1 - np.clip((s / 2 - d1) - wid / 2 + 0.5, 0, 1)
            # cross hatch in the dark
            c = np.clip((tone - p['cross']) / 0.3, 0, 1)
            d2 = np.abs((phi2 / (s * 1.15)) % 1.0 - 0.5) * s * 1.15
            ink2 = (1 - np.clip((s * 0.575 - d2) - c * 0.35 * s + 0.5, 0, 1)) * (c > 0)
            # outline of this part
            pd = ndimage.distance_transform_edt(m)
            ol = (1 - np.clip(pd - p['outline'], 0, 1)) if p['outline'] > 0 else np.zeros_like(pd)
            ink = np.clip(np.maximum(np.maximum(ink1, ink2), ol), 0, 1)
            col = PAPER[None, None, :] * (1 - ink[..., None]) + INK[None, None, :] * ink[..., None]
            rgb[m] = col[m]
            alpha[m] = 1.0
            label[m] = i
        for mk in marks:
            mk(self, rgb, alpha)
        # soft 1px edge
        a_s = ndimage.gaussian_filter(alpha, 0.7)
        alpha = np.minimum(alpha, np.clip(a_s * 1.6, 0, 1))
        return np.dstack([rgb, alpha]), label, [p['layer'] for p in self.parts]

    def _fields(self, p):
        X, Y = self.X, self.Y
        kind = p['hatch'][0]
        m = p['mask']
        if kind == 'dir':
            a = p['hatch'][1]
            n = np.array([-np.sin(a), np.cos(a)])
            phi = X * n[0] + Y * n[1]
            phi2 = X * np.cos(a + 1.1) + Y * np.sin(a + 1.1)
            # a little bend along the outline keeps the barrel
            pd = ndimage.distance_transform_edt(m)
            phi = phi + 0.35 * np.sqrt(np.maximum(pd, 0)) * 6
            return phi, phi2
        if kind == 'axis':
            chain = np.asarray(p['hatch'][1], float)
            radii = p['hatch'][2]
            best = np.full(X.shape, 1e9, np.float32); phi = np.zeros_like(best); tang = np.zeros_like(best)
            for i in range(len(chain) - 1):
                a, b = chain[i], chain[i + 1]
                d = b - a; L = np.sqrt(d @ d); u = d / L
                t = np.clip((X - a[0]) * u[0] + (Y - a[1]) * u[1], 0, L)
                px, py = a[0] + t * u[0], a[1] + t * u[1]
                dd = (X - px) ** 2 + (Y - py) ** 2
                perp = (X - a[0]) * (-u[1]) + (Y - a[1]) * u[0]
                r = radii[i] + (radii[i + 1] - radii[i]) * t / L
                cross = np.clip(perp / r, -1, 1)
                val = np.arcsin(cross) / (np.pi / 2) * r            # bunched toward the edges
                sel = dd < best
                best = np.where(sel, dd, best); phi = np.where(sel, val, phi)
                tang = np.where(sel, (X - a[0]) * u[0] + (Y - a[1]) * u[1], tang)
            return phi, tang
        if kind == 'contour':
            pd = ndimage.distance_transform_edt(m)
            return pd, X * 0.7 + Y * 0.7
        raise ValueError(kind)


def to_pil(rgba):
    return Image.fromarray((np.clip(rgba, 0, 1) * 255).astype(np.uint8), 'RGBA')

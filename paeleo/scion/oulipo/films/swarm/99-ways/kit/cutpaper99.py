"""99 ways: HANDMADE flat cut paper made in code (the 'cut-paper' medium).

Every shape is a polygon cut with scissors: its outline is sampled, given a small hand jitter, then reduced to straight
scissor facets (approxPolyDP). Each paper is a flat colour whose fibre comes from the LoC 1934 sheet (relative tone only),
and each piece throws one paper shadow, always down-right. No filter is laid over anything.
Use: from cutpaper99 import Cut; c = Cut(h, w, seed); c.piece(poly, colour); ...; c.img"""
import math
import random

import cv2
import numpy as np

import pen99
from pen99 import penlib

_FIBRE = None
SHADOW = (5, 7)          # the one light: shadows fall down-right


def fibre():
    global _FIBRE
    if _FIBRE is None:
        g = pen99.sheet99().mean(axis=2)
        _FIBRE = (g - g.mean()).astype(np.float32)        # relative fibre tone of the 1934 sheet, ~ +-8
    return _FIBRE


def hexc(s):
    s = s.lstrip("#")
    return np.array([int(s[i:i + 2], 16) for i in (0, 2, 4)], np.float32)


def ellipse(cx, cy, rx, ry, a0=0, a1=360, n=None):
    n = n or max(16, int((rx + ry) * 0.25))
    a = np.radians(np.linspace(a0, a1, n, endpoint=(a1 - a0) < 360))
    return np.stack([cx + rx * np.cos(a), cy + ry * np.sin(a)], 1)


def rect(x0, y0, x1, y1):
    return np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], np.float32)


def densify(p, step=6.0):
    p = np.asarray(p, np.float32)
    out = []
    q = np.vstack([p, p[:1]])
    for a, b in zip(q[:-1], q[1:]):
        n = max(1, int(np.linalg.norm(b - a) / step))
        for k in range(n):
            out.append(a + (b - a) * k / n)
    return np.array(out, np.float32)


class Cut:
    def __init__(self, h, w, seed=0, ground=None, fibre_off=(0, 0)):
        self.h, self.w = h, w
        self.rnd = random.Random(seed)
        F = fibre()
        oy, ox = fibre_off
        oy, ox = oy % max(1, F.shape[0] - h), ox % max(1, F.shape[1] - w)
        if h <= F.shape[0] and w <= F.shape[1]:
            self.tex = F[oy:oy + h, ox:ox + w].copy()
        else:
            self.tex = cv2.resize(F, (w, h))
        if ground is None:
            self.img = pen99.sheet99(w, h) if (h, w) != (pen99.PAGE_H, pen99.PAGE_W) else pen99.sheet99()
        else:
            self.img = np.zeros((h, w, 3), np.float32) + hexc(ground) if isinstance(ground, str) else ground.astype(np.float32).copy()
            self.img += self.tex[..., None] * 0.9

    # ---------------------------------------------------------- masks
    def mask(self, poly, jitter=0.8, eps=None, holes=()):
        """Scissor-faceted mask (uint8) of a polygon (Nx2 px), with optional holes: a few hand-cut straight facets."""
        m = np.zeros((self.h, self.w), np.uint8)
        def facet(p):
            p = np.asarray(p, np.float32)
            diag = float(np.linalg.norm(p.max(0) - p.min(0)))
            e = eps if eps is not None else min(4.5, max(1.2, diag * 0.006))
            p = densify(p, max(3.0, diag / 90))
            p = p + np.array([[self.rnd.gauss(0, jitter), self.rnd.gauss(0, jitter)] for _ in range(len(p))], np.float32)
            return cv2.approxPolyDP(p.reshape(-1, 1, 2), e, True).reshape(-1, 2)
        cv2.fillPoly(m, [np.int32(np.round(facet(poly) * 4))], 255, cv2.LINE_AA, shift=2)
        for hp in holes:
            cv2.fillPoly(m, [np.int32(np.round(facet(hp) * 4))], 0, cv2.LINE_AA, shift=2)
        return m

    def shadow(self, m, off=SHADOW, blur=3.5, opacity=0.38):
        dx, dy = off
        sh = np.zeros_like(m)
        H, W = m.shape
        sh[max(0, dy):, max(0, dx):] = m[:H - max(0, dy), :W - max(0, dx)]
        s = cv2.GaussianBlur(sh, (0, 0), blur).astype(np.float32) / 255 * opacity
        self.img *= (1 - s[..., None])

    def fill(self, m, colour, grain=1.0):
        c = hexc(colour) if isinstance(colour, str) else np.asarray(colour, np.float32)
        a = (m.astype(np.float32) / 255)[..., None]
        paper = c + self.tex[..., None] * grain * (0.6 + c.mean() / 255 * 0.7)
        self.img[:] = self.img * (1 - a) + paper * a

    def piece(self, poly, colour, shadow=True, holes=(), jitter=0.8, eps=None, off=SHADOW, opacity=0.38, grain=1.0):
        m = self.mask(poly, jitter, eps, holes)
        if shadow:
            self.shadow(m, off, opacity=opacity)
        self.fill(m, colour, grain)
        return m

    def piece_mask(self, m, colour, shadow=True, off=SHADOW, opacity=0.38, grain=1.0):
        if shadow:
            self.shadow(m, off, opacity=opacity)
        self.fill(m, colour, grain)
        return m

    def limb(self, a, b, w0, w1, colour, **kw):
        """A tapered cut piece from a (width w0) to b (width w1), with rounded scissor ends."""
        a, b = np.float32(a), np.float32(b)
        d = b - a
        L = np.linalg.norm(d) + 1e-6
        n = np.float32([-d[1], d[0]]) / L
        ang = math.degrees(math.atan2(d[1], d[0]))
        ea = ellipse(a[0], a[1], w0 / 2, w0 / 2, ang + 90, ang + 270, 10)
        eb = ellipse(b[0], b[1], w1 / 2, w1 / 2, ang - 90, ang + 90, 10)
        return self.piece(np.vstack([eb, ea]), colour, **kw)

    def strip(self, a, b, w, colour, **kw):
        """A cut strip of paper from a to b, width w."""
        a, b = np.float32(a), np.float32(b)
        d = b - a
        n = np.float32([-d[1], d[0]]) / (np.linalg.norm(d) + 1e-6) * w / 2
        return self.piece(np.array([a + n, b + n, b - n, a - n]), colour, **kw)

    # ---------------------------------------------------------- cut letters
    def cut_letters(self, lines, cap, at, colour, seed, margin=0.0, shadow=True, align="center"):
        """Pen letters (shared hand) cut out of paper: the stroke mask, slightly fattened and faceted."""
        let = pen99.letter(lines, cap, seed, weight=0.17)
        if margin:
            k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * int(margin) + 1,) * 2)
            let = cv2.dilate(let, k)
        lh, lw = let.shape
        x0 = int(at[0] - lw / 2) if align == "center" else int(at[0])
        y0 = int(at[1] - lh / 2)
        m = np.zeros((self.h, self.w), np.uint8)
        ys, xs, ye, xe = max(0, y0), max(0, x0), min(self.h, y0 + lh), min(self.w, x0 + lw)
        m[ys:ye, xs:xe] = let[ys - y0:ye - y0, xs - x0:xe - x0]
        m = np.where(m > 110, 255, 0).astype(np.uint8)
        m = cv2.GaussianBlur(m, (3, 3), 0.7)
        return self.piece_mask(m, colour, shadow, off=(3, 4), opacity=0.45)

    def ink_letters(self, lines, cap, at, seed, colour=None):
        let = pen99.letter(lines, cap, seed)
        lh, lw = let.shape
        x0, y0 = int(at[0] - lw / 2), int(at[1] - lh / 2)
        m = np.zeros((self.h, self.w), np.uint8)
        ys, xs, ye, xe = max(0, y0), max(0, x0), min(self.h, y0 + lh), min(self.w, x0 + lw)
        m[ys:ye, xs:xe] = let[ys - y0:ye - y0, xs - x0:xe - x0]
        penlib.ink_onto(self.img, m, penlib.INK if colour is None else hexc(colour))
        return m

    def balloon(self, lines, cap, centre, tip, seed):
        """The shared cut-paper balloon (penlib.balloon_piece), tail tip in canvas px."""
        b = penlib.balloon_piece([pen99.clean(l) for l in lines], cap, (tip[0] - centre[0], tip[1] - centre[1]), seed,
                                 tail_w=0.22, bend=0.10)
        penlib.lay_balloon(self.img, b, centre)
        return b

    def u8(self):
        return np.clip(np.round(self.img), 0, 255).astype(np.uint8)

"""Small helpers shared by six films (renzo-e-luciana, monsieur-ripois,
la-mort-en-ce-jardin, la-cite-raymond-queneau, mauro-martino-exercises-in-style,
le-maki-mococo). Built on kit.py; kit.py itself is untouched."""
from __future__ import annotations

import math

import numpy as np

from kit import *  # noqa: F401,F403
from kit import Film, Ink, Mix, W, H, FPS, RATE, PAPER, PAGE, INK, MUTED, RULE, ACCENT, WASH, BRASS, NIGHT, ramp, ease, clamp, lerp


class Score:
    """An ordered list of (start, end, name) segments with local-time lookup."""

    def __init__(self, segs):
        self.segs = segs

    def at(self, t):
        for a, b, name in self.segs:
            if a <= t < b:
                return name, t - a, a, b
        a, b, name = self.segs[-1]
        return name, t - a, a, b

    def start(self, name):
        for a, b, n in self.segs:
            if n == name:
                return a
        raise KeyError(name)

    @property
    def total(self):
        return self.segs[-1][1]


def edge_fade(ink, t, a, b, dur=0.3, color=NIGHT):
    """Fade in from / out to a colour at the edges of a segment."""
    f = min(1.0, (t - a) / dur if dur else 1, (b - t) / dur if dur else 1)
    if f < 1:
        ink.d.rectangle([0, 0, ink.w, ink.h], fill=tuple(color) + (int(255 * (1 - clamp(f))),))


def section_card(ink, kicker, title, sub=None, dark=True):
    ground = NIGHT if dark else PAPER
    fg = PAGE if dark else INK
    ink.fill(ground)
    ink.label((W / 2, H / 2 - 62), kicker, 15, BRASS if dark else ACCENT, anchor="mm")
    ink.text((W / 2, H / 2 - 4), title, "serif", 50, fg, anchor="mm")
    if sub:
        ink.label((W / 2, H / 2 + 50), sub, 15, RULE if dark else MUTED, anchor="mm")


def speaker_caption(ink, who, line, alpha=1.0, y=None, color=INK, who_color=ACCENT, size=24):
    """Caption with a small speaker tag above it."""
    if alpha <= 0:
        return
    y = H - 46 if y is None else y
    ink.caption(line, alpha, y=y, size=size, color=color)
    tw, th = ink.text_size(line, "serif", size)
    if who:
        lx, ly = W / 2 - tw / 2 - 14, y - th / 2 - 30
        ww, hh = ink.text_size(who, "mono", 13)
        ink.d.rectangle([lx, ly - 2, lx + ww + 12, ly + hh + 8], fill=PAGE + (int(215 * alpha),))
        ink.label((lx + 6, ly), who, 13, who_color, alpha=int(255 * alpha))


def timeline_bar(ink, x0, x1, y, t0, t1, bars, now=None, label_w=70, row=16, gap=5, font_size=12):
    """Schedule strip. bars = [(label, [(a,b),...], color)]; times in the same units as t0..t1."""
    def X(v):
        return lerp(x0 + label_w, x1, (v - t0) / (t1 - t0))
    for k, (label, spans, col) in enumerate(bars):
        yy = y + k * (row + gap)
        ink.label((x0, yy + row / 2), label, font_size, MUTED, anchor="lm")
        ink.d.rectangle([x0 + label_w, yy, x1, yy + row], fill=RULE + (90,))
        for a, b in spans:
            a, b = max(a, t0), min(b, t1)
            if b <= a:
                continue
            ink.d.rectangle([X(a), yy, X(b), yy + row], fill=tuple(col[:3]) + (230,))
    if now is not None and t0 <= now <= t1:
        nx = X(now)
        ink.d.line([(nx, y - 4), (nx, y + len(bars) * (row + gap))], fill=INK + (255,), width=2)
    return X


def sub_mix(seconds, build, seed=0):
    """Render a separate Mix (for a stem or an edition) and return its stereo array (n, 2) floats."""
    m = Mix(seconds, seed=seed)
    build(m)
    return np.stack([m.L, m.R], 1)


def rms_db(st, gate_db=-50.0):
    """Gated RMS in dBFS over 400 ms blocks (a plain stand-in for integrated loudness)."""
    blk = int(0.4 * RATE)
    vals = []
    for i in range(0, len(st) - blk, blk // 2):
        r = math.sqrt(float((st[i:i + blk] ** 2).mean()) + 1e-12)
        if 20 * math.log10(r) > gate_db:
            vals.append(r * r)
    if not vals:
        return -120.0
    return 10 * math.log10(sum(vals) / len(vals))


def place(mix, st, at, gain=1.0):
    i = int(at * mix.rate)
    n = min(len(st), mix.n - i)
    if n <= 0:
        return
    mix.L[i:i + n] += st[:n, 0] * gain
    mix.R[i:i + n] += st[:n, 1] * gain


def bench_key_glint(ink, x, y, t):
    """A small sparkle near the brass key."""
    a = 0.5 + 0.5 * math.sin(t * 6)
    for k in range(4):
        ang = k * math.pi / 2 + math.pi / 4
        ink.d.line([(x + math.cos(ang) * 3, y + math.sin(ang) * 3), (x + math.cos(ang) * (6 + 4 * a), y + math.sin(ang) * (6 + 4 * a))],
                   fill=BRASS + (int(200 * a),), width=2)


def _biquad_mag2(b, a, w):
    z = np.exp(-1j * w)
    num = b[0] + b[1] * z + b[2] * z * z
    den = a[0] + a[1] * z + a[2] * z * z
    return np.abs(num / den) ** 2


def _k_weight_coeffs(rate):
    """BS.1770 K-weighting (shelf + high-pass) via the usual bilinear designs."""
    G, Q, fc = 4.0, 1 / math.sqrt(2), 1500.0
    A = 10 ** (G / 40)
    w0 = 2 * math.pi * fc / rate
    al = math.sin(w0) / (2 * Q)
    cw = math.cos(w0)
    b1 = [A * ((A + 1) + (A - 1) * cw + 2 * math.sqrt(A) * al), -2 * A * ((A - 1) + (A + 1) * cw),
          A * ((A + 1) + (A - 1) * cw - 2 * math.sqrt(A) * al)]
    a1 = [(A + 1) - (A - 1) * cw + 2 * math.sqrt(A) * al, 2 * ((A - 1) - (A + 1) * cw),
          (A + 1) - (A - 1) * cw - 2 * math.sqrt(A) * al]
    Q2, fc2 = 0.5, 38.0
    w0 = 2 * math.pi * fc2 / rate
    al = math.sin(w0) / (2 * Q2)
    cw = math.cos(w0)
    b2 = [(1 + cw) / 2, -(1 + cw), (1 + cw) / 2]
    a2 = [1 + al, -2 * cw, 1 - al]
    return (b1, a1), (b2, a2)


def lufs(st, rate=RATE):
    """Integrated loudness (BS.1770-style gating) with K-weighting applied as a magnitude response."""
    (b1, a1), (b2, a2) = _k_weight_coeffs(rate)
    chans = []
    for c in range(st.shape[1]):
        X = np.fft.rfft(st[:, c])
        w = 2 * np.pi * np.fft.rfftfreq(len(st), 1 / rate) / rate
        X *= np.sqrt(_biquad_mag2(b1, a1, w) * _biquad_mag2(b2, a2, w))
        chans.append(np.fft.irfft(X, len(st)))
    y = np.stack(chans, 1)
    blk, hop = int(0.4 * rate), int(0.1 * rate)
    z = np.array([(y[i:i + blk] ** 2).mean(0).sum() for i in range(0, len(y) - blk, hop)])
    L = -0.691 + 10 * np.log10(z + 1e-12)
    g = z[L > -70]
    if len(g) == 0:
        return -120.0
    rel = -0.691 + 10 * np.log10(g.mean()) - 10
    g2 = z[(L > -70) & (L > rel)]
    return float(-0.691 + 10 * np.log10(g2.mean()))


# ======================================================================
# Procedural photographic toolkit (value-based shading, no outlines).
# Everything is computed from code: soft masks, lambert shading on
# ellipsoids and capsules, cast shadows, tone curves, halation, grain.
# ======================================================================

from PIL import Image as _Image, ImageDraw as _Draw, ImageFilter as _Filter


def C(v):
    """Colour helper: a grey value (0..1) or an RGB tuple 0..255 -> float array 0..1."""
    if isinstance(v, (int, float)):
        return np.array([v, v, v], np.float32)
    v = np.asarray(v, np.float32)
    return v / 255.0 if v.max() > 1.5 else v


class Photo:
    """A float RGB canvas with a camera. World coords -> screen: (p - c) * s + centre."""

    def __init__(self, w=W, h=H, cam=(1.0, W / 2, H / 2), light=(-0.55, -0.6, 0.58)):
        self.w, self.h = w, h
        self.a = np.zeros((h, w, 3), np.float32)
        self.s, self.cx, self.cy = cam
        l = np.array(light, np.float32)
        self.light = l / np.linalg.norm(l)

    # -- camera
    def P(self, x, y):
        return ((x - self.cx) * self.s + self.w / 2, (y - self.cy) * self.s + self.h / 2)

    def Pl(self, pts):
        return [self.P(x, y) for x, y in pts]

    def world(self, xx, yy):
        return ((xx - self.w / 2) / self.s + self.cx, (yy - self.h / 2) / self.s + self.cy)

    # -- low level
    def _box(self, pts, pad):
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        x0, y0 = int(max(0, math.floor(min(xs) - pad))), int(max(0, math.floor(min(ys) - pad)))
        x1, y1 = int(min(self.w, math.ceil(max(xs) + pad))), int(min(self.h, math.ceil(max(ys) + pad)))
        if x1 <= x0 or y1 <= y0:
            return None
        return x0, y0, x1, y1

    def _mask(self, spts, box, blur, kind="poly"):
        x0, y0, x1, y1 = box
        m = _Image.new("L", (x1 - x0, y1 - y0), 0)
        d = _Draw.Draw(m)
        if kind == "poly":
            d.polygon([(x - x0, y - y0) for x, y in spts], fill=255)
        elif kind == "ellipse":
            (cx, cy), (rx, ry) = spts
            d.ellipse([cx - rx - x0, cy - ry - y0, cx + rx - x0, cy + ry - y0], fill=255)
        elif kind == "line":
            pts, wdt = spts
            d.line([(x - x0, y - y0) for x, y in pts], fill=255, width=max(1, int(round(wdt))), joint="curve")
        if blur > 0.3:
            m = m.filter(_Filter.GaussianBlur(blur))
        return np.asarray(m, np.float32)[..., None] / 255.0

    def _grid(self, box):
        x0, y0, x1, y1 = box
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        return xx, yy

    def _comp(self, box, m, col, alpha=1.0, mode="normal"):
        x0, y0, x1, y1 = box
        reg = self.a[y0:y1, x0:x1]
        m = m * alpha
        if mode == "multiply":
            reg[:] = reg * (1 - m) + reg * col * m
        elif mode == "add":
            reg[:] = reg + col * m
        elif mode == "screen":
            reg[:] = 1 - (1 - reg) * (1 - col * m)
        else:
            reg[:] = reg * (1 - m) + col * m

    def _colour(self, color, box):
        """color may be a constant or callable(wx, wy) -> (h, w, 3) or (h, w) array."""
        if callable(color):
            xx, yy = self._grid(box)
            wx, wy = self.world(xx, yy)
            c = color(wx, wy)
            if c.ndim == 2:
                c = np.repeat(c[..., None], 3, 2)
            return c.astype(np.float32)
        return C(color)

    # -- grounds
    def ground(self, top, bottom=None, axis="y"):
        top = C(top)
        bottom = top if bottom is None else C(bottom)
        f = np.linspace(0, 1, self.h if axis == "y" else self.w, dtype=np.float32)
        g = top[None, :] * (1 - f[:, None]) + bottom[None, :] * f[:, None]
        if axis == "y":
            self.a[:] = g[:, None, :]
        else:
            self.a[:] = g[None, :, :]

    def field(self, fn, box=None, mode="normal", alpha=1.0, mask=None):
        """Apply fn(wx, wy) -> colour over a screen box (default full frame)."""
        box = box or (0, 0, self.w, self.h)
        c = self._colour(fn, box)
        m = np.ones((box[3] - box[1], box[2] - box[0], 1), np.float32) if mask is None else mask
        self._comp(box, m, c, alpha, mode)

    # -- shapes
    def poly(self, pts, color, blur=0.7, alpha=1.0, mode="normal", grad=None):
        sp = self.Pl(pts)
        box = self._box(sp, blur * 3 + 2)
        if not box:
            return
        m = self._mask(sp, box, blur)
        c = self._colour(color, box)
        if grad is not None:  # (p0, v0, p1, v1) multiplier gradient in world coords
            (gx0, gy0), v0, (gx1, gy1), v1 = grad
            xx, yy = self._grid(box)
            wx, wy = self.world(xx, yy)
            dx, dy = gx1 - gx0, gy1 - gy0
            u = np.clip(((wx - gx0) * dx + (wy - gy0) * dy) / (dx * dx + dy * dy + 1e-9), 0, 1)
            c = c * (v0 + (v1 - v0) * u)[..., None]
        self._comp(box, m, c, alpha, mode)

    def rect(self, x0, y0, x1, y1, color, **k):
        self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], color, **k)

    def stroke(self, pts, width, color, blur=0.6, alpha=1.0, mode="normal"):
        sp = self.Pl(pts)
        wpx = width * self.s
        box = self._box(sp, wpx + blur * 3 + 2)
        if not box:
            return
        m = self._mask((sp, wpx), box, blur, "line")
        self._comp(box, m, self._colour(color, box), alpha, mode)

    def blob(self, cx, cy, rx, ry, color, blur=0.7, alpha=1.0, mode="normal"):
        (sx, sy) = self.P(cx, cy)
        box = self._box([(sx - rx * self.s, sy - ry * self.s), (sx + rx * self.s, sy + ry * self.s)], blur * 3 + 2)
        if not box:
            return
        m = self._mask(((sx, sy), (rx * self.s, ry * self.s)), box, blur, "ellipse")
        self._comp(box, m, self._colour(color, box), alpha, mode)

    def ellipsoid(self, cx, cy, rx, ry, color, amb=0.3, spec=0.0, shine=18, blur=0.8, alpha=1.0, light=None, rim=0.0):
        L = self.light if light is None else np.array(light, np.float32) / np.linalg.norm(light)
        (sx, sy) = self.P(cx, cy)
        Rx, Ry = rx * self.s, ry * self.s
        box = self._box([(sx - Rx, sy - Ry), (sx + Rx, sy + Ry)], blur * 3 + 2)
        if not box:
            return
        xx, yy = self._grid(box)
        nx, ny = (xx - sx) / max(Rx, 1e-3), (yy - sy) / max(Ry, 1e-3)
        r2 = np.clip(nx * nx + ny * ny, 0, 1)
        nz = np.sqrt(1 - r2)
        lam = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)
        shade = amb + (1 - amb) * lam
        c = self._colour(color, box) * shade[..., None] + spec * (lam ** shine)[..., None] + rim * (r2 ** 4)[..., None]
        m = self._mask(((sx, sy), (Rx, Ry)), box, blur, "ellipse")
        self._comp(box, m, c, alpha)

    def capsule(self, p, q, r0, r1, color, amb=0.3, spec=0.0, shine=14, blur=0.8, alpha=1.0, light=None):
        """A shaded tapered cylinder from p to q (limbs, poles, plank edges)."""
        L = self.light if light is None else np.array(light, np.float32) / np.linalg.norm(light)
        sp, sq = self.P(*p), self.P(*q)
        R0, R1 = r0 * self.s, r1 * self.s
        R = max(R0, R1)
        box = self._box([sp, sq], R + blur * 3 + 2)
        if not box:
            return
        xx, yy = self._grid(box)
        dx, dy = sq[0] - sp[0], sq[1] - sp[1]
        ll = dx * dx + dy * dy + 1e-9
        u = np.clip(((xx - sp[0]) * dx + (yy - sp[1]) * dy) / ll, 0, 1)
        px, py = sp[0] + u * dx, sp[1] + u * dy
        ox, oy = xx - px, yy - py
        rr = R0 + (R1 - R0) * u
        d = np.sqrt(ox * ox + oy * oy) / np.maximum(rr, 1e-3)
        inside = d <= 1.0
        nz = np.sqrt(np.clip(1 - d * d, 0, 1))
        dist = np.sqrt(ox * ox + oy * oy) + 1e-6
        nx, ny = ox / dist * d, oy / dist * d
        lam = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)
        shade = amb + (1 - amb) * lam
        c = self._colour(color, box) * shade[..., None] + spec * (lam ** shine)[..., None]
        m = inside.astype(np.float32)
        if blur > 0.3:
            mi = _Image.fromarray((m * 255).astype(np.uint8)).filter(_Filter.GaussianBlur(blur))
            m = np.asarray(mi, np.float32) / 255.0
        self._comp(box, m[..., None], c, alpha)

    def shadow(self, pts, strength=0.5, blur=6, kind="poly"):
        """Darken (multiply) a soft region: cast shadows, contact shadows."""
        if kind == "poly":
            self.poly(pts, 0.0, blur=blur, alpha=strength)
        else:
            (cx, cy), (rx, ry) = pts
            self.blob(cx, cy, rx, ry, 0.0, blur=blur, alpha=strength)

    def light_patch(self, pts, amount=0.4, blur=4, color=1.0):
        self.poly(pts, color, blur=blur, alpha=amount, mode="screen")

    # -- finishing
    def image(self):
        return _Image.fromarray((np.clip(self.a, 0, 1) * 255).astype(np.uint8))


_NOISE = {}


def _noise_bank(shape, size, key):
    k = (shape, size, key)
    if k not in _NOISE:
        rs = np.random.RandomState(hash(key) % 1000)
        bank = []
        for _ in range(8):
            h, w = shape
            n = rs.normal(0, 1, (int(h / size) + 2, int(w / size) + 2)).astype(np.float32)
            img = _Image.fromarray(((n * 40) + 128).clip(0, 255).astype(np.uint8)).resize((w, h), _Image.BICUBIC)
            bank.append((np.asarray(img, np.float32) - 128) / 40)
        _NOISE[k] = bank
    return _NOISE[k]


def value_noise(wx, wy, scale, seed=0, octaves=3):
    """Smooth procedural noise on world coords (for mottled light, skin, foliage, stains)."""
    out = np.zeros_like(wx)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        f = (2 ** o) / scale
        ph = seed * 1.7 + o * 3.1
        out += amp * (np.sin(wx * f * 1.3 + ph) * np.sin(wy * f * 1.7 - ph * 0.7)
                      + np.sin((wx * 0.8 - wy * 0.6) * f * 2.1 + ph * 2) * 0.5)
        tot += amp * 1.5
        amp *= 0.5
    return out / tot


def finish(ph, look, frame_index=0):
    """Photographic finish. look keys:
    bw, gamma, contrast (S-curve), lift, gain, halation (amount, threshold, radius),
    soft (lens blur px), grain (amount, size), vignette, tint (rgb), saturation, chroma_blur, scan."""
    a = np.clip(ph.a, 0, 1.2)
    if look.get("bw"):
        g = a[..., 0] * 0.3 + a[..., 1] * 0.59 + a[..., 2] * 0.11
        a = np.repeat(g[..., None], 3, 2)
    if look.get("saturation") is not None and not look.get("bw"):
        g = a.mean(2, keepdims=True)
        a = g + (a - g) * look["saturation"]
    if look.get("soft"):
        img = _Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).filter(_Filter.GaussianBlur(look["soft"]))
        a = np.asarray(img, np.float32) / 255.0
    hal = look.get("halation")
    if hal:
        amt, thr, rad = hal
        hi = np.clip((a.mean(2) - thr) / (1 - thr), 0, 1)
        hm = _Image.fromarray((hi * 255).astype(np.uint8)).filter(_Filter.GaussianBlur(rad))
        hm = np.asarray(hm, np.float32)[..., None] / 255.0
        tint = C(look.get("halation_tint", (1.0, 1.0, 1.0)))
        a = 1 - (1 - a) * (1 - hm * amt * tint)
    if look.get("chroma_blur") and not look.get("bw"):
        y = a.mean(2, keepdims=True)
        ch = a - y
        img = _Image.fromarray(((ch * 0.5 + 0.5).clip(0, 1) * 255).astype(np.uint8)).filter(_Filter.GaussianBlur(look["chroma_blur"]))
        a = y + (np.asarray(img, np.float32) / 255.0 - 0.5) * 2
    g = look.get("gamma", 1.0)
    a = np.clip(a, 0, 1) ** g
    k = look.get("contrast", 0.0)
    if k:
        a = a + k * (a - 0.5) * (1 - np.abs(2 * a - 1))  # gentle S
        a = np.clip(a, 0, 1)
    lift, gain = look.get("lift", 0.0), look.get("gain", 1.0)
    a = lift + (gain - lift) * a
    if look.get("tint") is not None:
        a = a * C(look["tint"])
    v = look.get("vignette", 0.0)
    if v:
        yy, xx = np.mgrid[0:ph.h, 0:ph.w].astype(np.float32)
        r = np.hypot((xx - ph.w / 2) / (ph.w / 2), (yy - ph.h / 2) / (ph.h / 2))
        a = a * (1 - v * np.clip(r - 0.35, 0, None) ** 1.6)[..., None]
    gr = look.get("grain")
    if gr:
        amt, size = gr
        bank = _noise_bank((ph.h, ph.w), size, "g%.2f" % size)
        n = bank[frame_index % len(bank)]
        mid = 1 - np.abs(2 * a.mean(2) - 1) * 0.6
        if look.get("bw"):
            a = a + (n * amt * mid)[..., None]
        else:
            n2 = bank[(frame_index + 3) % len(bank)]
            a = a + (n * amt * mid)[..., None] + (n2 * amt * 0.4 * mid)[..., None] * np.array([1, -0.5, -0.5], np.float32)
    if look.get("scan"):
        a[::2] *= 1 - look["scan"]
    return _Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))


# -- people, drawn as shaded volumes -----------------------------------------

def skeleton(x, y, s=1.0, pose="stand", phase=0.0, facing=1, arm=None, arm2=None, lean=0.0):
    """Joint positions for a standing/walking/sitting/reaching person, feet at (x, y). Height 170*s."""
    h = 170 * s
    hip = (x + lean * 10 * s * facing, y - h * 0.5)
    neck = (x + lean * 30 * s * facing, y - h * 0.83)
    if pose == "sit":
        hip = (x, y - h * 0.3)
        neck = (x + (4 + lean * 20) * s * facing, y - h * 0.64)
    head = (neck[0] + 3 * s * facing, neck[1] - h * 0.075)
    legs = []
    if pose in ("walk", "run"):
        amp = 0.42 if pose == "walk" else 0.8
        a = math.sin(2 * math.pi * phase) * amp
        for sgn in (1, -1):
            th = a * sgn
            knee = (hip[0] + math.sin(th) * h * 0.25 * facing, hip[1] + math.cos(th) * h * 0.25)
            bend = max(0, -math.sin(2 * math.pi * phase) * sgn) * 0.6 + 0.08
            foot = (knee[0] + math.sin(th - bend) * h * 0.25 * facing, knee[1] + math.cos(th - bend) * h * 0.25)
            legs.append((knee, foot))
    elif pose == "sit":
        for sgn, dx in ((1, 0), (-1, -4)):
            knee = (hip[0] + h * 0.24 * facing + dx * s, hip[1] - 2 * s)
            foot = (knee[0] + 4 * s * facing, y)
            legs.append((knee, foot))
    elif pose == "kneel":
        hip = (x, y - h * 0.3)
        neck = (x + 30 * s * facing, y - h * 0.58)
        head = (neck[0] + 10 * s * facing, neck[1] - h * 0.07)
        legs = [((hip[0] + h * 0.1 * facing, y - 4 * s), (hip[0] - h * 0.12 * facing, y)), ((hip[0] + h * 0.2 * facing, hip[1] + h * 0.05), (hip[0] + h * 0.22 * facing, y))]
    else:
        legs = [((x - 5 * s, y - h * 0.25), (x - 7 * s, y)), ((x + 5 * s, y - h * 0.25), (x + 7 * s, y))]
    sh = (neck[0], neck[1] + h * 0.03)
    if pose in ("walk", "run"):
        a = math.sin(2 * math.pi * phase) * (0.45 if pose == "walk" else 0.9)
        angs = [-a, a]
    else:
        angs = [math.radians(arm) if arm is not None else 0.1, math.radians(arm2) if arm2 is not None else -0.08]
    arms = []
    for th in angs:
        el = (sh[0] + math.sin(th) * h * 0.18 * facing, sh[1] + math.cos(th) * h * 0.18)
        th2 = th * 1.2 if abs(th) > 0.6 else th
        hand = (el[0] + math.sin(th2) * h * 0.17 * facing, el[1] + math.cos(th2) * h * 0.17)
        arms.append((el, hand))
    return {"s": s, "h": h, "hip": hip, "neck": neck, "head": head, "legs": legs, "arms": arms, "sh": sh, "facing": facing, "pose": pose}


def person(ph, sk, outfit, face=True):
    """Draw a person from a skeleton as shaded volumes.
    outfit: skin, top, bottom, hair, shoes (values or callables), hat ('scarf'|'brim'|None), bare_arms."""
    s, h, f = sk["s"], sk["h"], sk["facing"]
    skin, top, bottom = outfit.get("skin", 0.72), outfit.get("top", 0.5), outfit.get("bottom", 0.25)
    hair, shoes = outfit.get("hair", 0.12), outfit.get("shoes", 0.1)
    arm_col = skin if outfit.get("bare_arms") else top
    hip, neck, head = sk["hip"], sk["neck"], sk["head"]
    # far limbs first (slightly darker)
    (k2, f2), (k1, f1) = sk["legs"][1], sk["legs"][0]
    leg_col = outfit.get("legs", bottom)
    dark = lambda c: (lambda wx, wy: c(wx, wy) * 0.8) if callable(c) else C(c) * 0.8
    ph.capsule(hip, k2, 9 * s, 7 * s, dark(leg_col), amb=0.35)
    ph.capsule(k2, f2, 7 * s, 5 * s, dark(outfit.get("shin", leg_col)), amb=0.35)
    ph.ellipsoid(f2[0] + 6 * s * f, f2[1] - 2 * s, 10 * s, 4 * s, shoes, amb=0.4, spec=0.2)
    el, hd = sk["arms"][1]
    ph.capsule(sk["sh"], el, 6 * s, 5 * s, dark(arm_col), amb=0.35)
    ph.capsule(el, hd, 5 * s, 4 * s, dark(skin if outfit.get("bare_arms") or outfit.get("bare_forearms") else arm_col), amb=0.35)
    ph.ellipsoid(hd[0], hd[1], 4.5 * s, 5 * s, C(skin) * 0.85 if not callable(skin) else skin, amb=0.4)
    # torso: skirt or trousers, then chest
    if outfit.get("skirt"):
        ph.poly([(hip[0] - 13 * s, hip[1] - 6 * s), (hip[0] + 13 * s, hip[1] - 6 * s), (hip[0] + 22 * s, hip[1] + h * 0.2), (hip[0] - 22 * s, hip[1] + h * 0.2)],
                bottom, blur=0.8, grad=((hip[0] - 22 * s, 0), 0.6, (hip[0] + 22 * s, 0), 1.05))
    ph.capsule(hip, k1, 10 * s, 7.5 * s, leg_col, amb=0.35)
    ph.capsule(k1, f1, 7.5 * s, 5 * s, outfit.get("shin", leg_col), amb=0.35)
    ph.ellipsoid(f1[0] + 6 * s * f, f1[1] - 2 * s, 10 * s, 4 * s, shoes, amb=0.4, spec=0.25)
    # torso: shoulders wider than the waist, shaded across its width toward the light
    sw, ww = 17 * s, 12.5 * s
    nx_, ny_ = neck
    hx_, hy_ = hip
    lx = ph.light[0]
    gl, gr = (0.55, 1.08) if lx > 0 else (1.08, 0.55)
    ph.poly([(nx_ - sw, ny_ + 3 * s), (nx_ + sw, ny_ + 3 * s), (hx_ + ww, hy_ + 2 * s), (hx_ - ww, hy_ + 2 * s)], top, blur=1.0,
            grad=((min(nx_, hx_) - sw, 0), gl, (max(nx_, hx_) + sw, 0), gr))
    ph.ellipsoid(nx_ - sw * 0.55, ny_ + 7 * s, 8 * s, 7 * s, top, amb=0.35)
    ph.ellipsoid(nx_ + sw * 0.55, ny_ + 7 * s, 8 * s, 7 * s, top, amb=0.35)
    if outfit.get("collar"):
        ph.poly([(nx_ - 5 * s, ny_ + 2 * s), (nx_ + 5 * s, ny_ + 2 * s), (nx_, ny_ + 14 * s)], outfit["collar"], blur=0.7)
    ph.capsule((neck[0], neck[1] + 4 * s), (head[0], head[1] + 6 * s), 4.8 * s, 4.2 * s, skin, amb=0.3)
    # near arm
    el, hd = sk["arms"][0]
    ph.capsule(sk["sh"], el, 6.5 * s, 5.5 * s, arm_col, amb=0.3)
    ph.capsule(el, hd, 5.5 * s, 4.2 * s, skin if outfit.get("bare_arms") or outfit.get("bare_forearms") else arm_col, amb=0.3)
    ph.ellipsoid(hd[0], hd[1], 4.8 * s, 5.4 * s, skin, amb=0.35)
    # head
    hr = 11.5 * s
    ph.ellipsoid(head[0], head[1], hr * 0.86, hr, skin, amb=0.28, spec=0.06)
    # profile: brow, nose, chin toward the facing side; an ear behind
    ph.ellipsoid(head[0] + hr * 0.72 * f, head[1] + hr * 0.12, hr * 0.2, hr * 0.26, skin, amb=0.35, spec=0.08)
    ph.ellipsoid(head[0] + hr * 0.38 * f, head[1] + hr * 0.72, hr * 0.42, hr * 0.32, skin, amb=0.3)
    ph.ellipsoid(head[0] - hr * 0.2 * f, head[1] + hr * 0.08, hr * 0.16, hr * 0.24, C(skin) * 0.9 if not callable(skin) else skin, amb=0.3)
    hat = outfit.get("hat")
    if face and ph.s * s > 1.2:
        ex = head[0] + 4 * s * f
        for k, dx in enumerate((-3.5, 3.5)):
            ph.blob(ex + dx * s * 0.8, head[1] - 1 * s, 1.6 * s, 1.0 * s, 0.08, blur=0.6, alpha=0.8)
        ph.blob(head[0] + 8.5 * s * f, head[1] + 2.5 * s, 1.6 * s, 2.6 * s, C(skin) * 0.7 if not callable(skin) else 0.4, blur=1.2, alpha=0.6)
        ph.blob(head[0] + 5 * s * f, head[1] + 6.5 * s, 3 * s, 1.1 * s, outfit.get("lips", 0.3), blur=0.7, alpha=0.7)
    # hair mass
    if outfit.get("hair_style", "short") == "up":
        ph.ellipsoid(head[0] - 3 * s * f, head[1] - hr * 0.55, hr * 0.95, hr * 0.7, hair, amb=0.2, spec=0.25)
        ph.ellipsoid(head[0] - 7 * s * f, head[1] - hr * 0.9, hr * 0.55, hr * 0.45, hair, amb=0.2, spec=0.25)
    elif outfit.get("hair_style") == "long":
        ph.ellipsoid(head[0] - 4 * s * f, head[1] - hr * 0.3, hr * 0.95, hr * 0.85, hair, amb=0.2, spec=0.2)
        ph.capsule((head[0] - 6 * s * f, head[1]), (head[0] - 8 * s * f, head[1] + hr * 1.3), 7 * s, 5 * s, hair, amb=0.2)
    else:
        ph.ellipsoid(head[0] - 2.5 * s * f, head[1] - hr * 0.45, hr * 0.9, hr * 0.62, hair, amb=0.2, spec=0.3)
    if hat == "brim":
        ph.ellipsoid(head[0], head[1] - hr * 0.75, hr * 1.7, hr * 0.32, outfit.get("hat_col", 0.15), amb=0.3, spec=0.1)
        ph.ellipsoid(head[0], head[1] - hr * 1.05, hr * 0.95, hr * 0.6, outfit.get("hat_col", 0.15), amb=0.3, spec=0.1)
    elif hat == "bucket":
        ph.poly([(head[0] - hr * 1.5, head[1] - hr * 0.1), (head[0] + hr * 1.5, head[1] - hr * 0.1), (head[0] + hr * 0.9, head[1] - hr * 1.5), (head[0] - hr * 0.9, head[1] - hr * 1.5)],
                outfit.get("hat_col", 0.95), blur=1.0, grad=((head[0] - hr * 1.5, 0), 0.7, (head[0] + hr * 1.5, 0), 1.05))
    elif hat == "scarf":
        ph.ellipsoid(head[0] - 1 * s * f, head[1] - hr * 0.5, hr * 1.0, hr * 0.68, outfit.get("hat_col", 0.9), amb=0.35)
    elif hat == "band":
        ph.capsule((head[0] - hr, head[1] - hr * 0.4), (head[0] + hr, head[1] - hr * 0.5), 2.6 * s, 2.6 * s, outfit.get("hat_col", 0.6), amb=0.3)
    return sk


def cast_shadow(ph, sk, dx=0.9, dy=0.18, strength=0.45, blur=5):
    """A ground shadow thrown away from the light: a sheared silhouette of the body."""
    x, y = sk["legs"][0][1]
    h = sk["h"] if sk["pose"] != "sit" else sk["h"] * 0.6
    base = ((sk["legs"][0][1][0] + sk["legs"][1][1][0]) / 2, max(sk["legs"][0][1][1], sk["legs"][1][1][1]))
    w = 16 * sk["s"]
    ph.shadow([(base[0] - w, base[1]), (base[0] + w, base[1]), (base[0] + w + h * dx, base[1] + h * dy), (base[0] - w * 0.4 + h * dx, base[1] + h * dy - 4)], strength, blur)
    ph.shadow(((base[0], base[1]), (w * 1.4, 4 * sk["s"])), strength * 0.8, 3, kind="ellipse")


def subtitle(img, text, y=None, size=26, who=None, color=(250, 250, 245), font_kind="sans"):
    """Film subtitle: white type with a dark soft shadow (no band), centred."""
    if not text:
        return img
    d = _Draw.Draw(img, "RGBA")
    f = font(font_kind, size)
    y = img.size[1] - 44 if y is None else y
    s = (who + ": " if who else "") + text
    for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2), (2, 2), (-1, 1), (1, -1)):
        d.text((img.size[0] / 2 + ox, y + oy), s, font=f, fill=(0, 0, 0, 170), anchor="mm")
    d.text((img.size[0] / 2, y), s, font=f, fill=tuple(color) + (255,), anchor="mm")
    return img


def band_text(img, items, top=True, h=26, size=13, color=(236, 236, 230), bg=(0, 0, 0)):
    """Info set in a letterbox band, like a slate. items: [(x, text, anchor)]."""
    d = _Draw.Draw(img, "RGBA")
    W_, H_ = img.size
    y0 = 0 if top else H_ - h
    d.rectangle([0, y0, W_, y0 + h], fill=tuple(bg) + (255,))
    f = font("mono", size)
    for x, s, anc in items:
        d.text((x, y0 + h / 2), s, font=f, fill=tuple(color) + (255,), anchor=anc)
    return img


class PhotoFilm(Film):
    """Film whose picture function returns a finished PIL image: picture(t, k) -> Image."""

    def frame(self, k):
        return self._picture(k / self.fps, k).convert("RGB")


def ink_on(img, t=0.0, k=0):
    """Wrap an existing PIL image as an Ink canvas (for cards and type)."""
    ink = Ink(t, k, img.size, boil=0, wobble=0)
    ink.img = img.convert("RGB")
    ink.d = _Draw.Draw(ink.img, "RGBA")
    ink._grain = False
    return ink


def photo_card(kicker, title, sub=None, ground=(12, 12, 12), fg=(238, 236, 230), accent=(200, 196, 186), serif=True, k=0, look=None):
    """A title card in the manner of the film's own titles: plain type on a flat ground, with grain."""
    ph = Photo()
    ph.ground(C(ground))
    img = finish(ph, look or {"grain": (0.03, 1.2)}, k)
    ink = ink_on(img)
    ink.text((W / 2, H / 2 - 64), kicker, "mono", 15, accent, anchor="mm")
    ink.text((W / 2, H / 2 - 6), title, "serif" if serif else "sans", 52, fg, anchor="mm")
    if sub:
        ink.text((W / 2, H / 2 + 50), sub, "mono", 15, accent, anchor="mm")
    return ink.img


def fade_img(img, f, color=(0, 0, 0)):
    if f >= 1:
        return img
    return _Image.blend(_Image.new("RGB", img.size, color), img, max(0.0, f))


def photo_envelope(ph, x, y, w=30, h=20, open_=0.0, paper=0.93, angle=0.0, shade=0.25):
    ca, sa = math.cos(angle), math.sin(angle)

    def R(px, py):
        return (x + px * ca - py * sa, y + px * sa + py * ca)
    ph.shadow([R(-w / 2 + 2, -h / 2 + 4), R(w / 2 + 3, -h / 2 + 4), R(w / 2 + 3, h / 2 + 4), R(-w / 2 + 2, h / 2 + 4)], 0.35, 2.5)
    ph.poly([R(-w / 2, -h / 2), R(w / 2, -h / 2), R(w / 2, h / 2), R(-w / 2, h / 2)], paper, blur=0.6,
            grad=(R(-w / 2, -h / 2), 1.0, R(w / 2, h / 2), 1 - shade))
    ph.poly([R(-w / 2, h / 2), R(0, h * 0.05), R(w / 2, h / 2)], C(paper) * 0.86, blur=0.6)
    tip = lerp(h * 0.1, -h * 1.0, open_)
    ph.poly([R(-w / 2, -h / 2), R(w / 2, -h / 2), R(0, tip)], C(paper) * (0.8 if open_ < 0.5 else 0.97), blur=0.6)
    if open_ < 0.5:
        ph.blob(*R(0, tip - 1), w * 0.07, w * 0.07, 0.35, blur=0.6)  # the seal


def photo_key(ph, x, y, s=1.0, angle=0.0, col=0.72, spec=0.5):
    ca, sa = math.cos(angle), math.sin(angle)

    def R(px, py):
        return (x + (px * ca - py * sa) * s, y + (px * sa + py * ca) * s)
    ph.shadow(((R(2, 3)[0], R(2, 3)[1]), (10 * s, 9 * s)), 0.3, 2 * s, kind="ellipse")
    ph.ellipsoid(*R(0, 0), 9 * s, 9 * s, col, amb=0.35, spec=spec)
    ph.blob(*R(0, 0), 3.8 * s, 3.8 * s, C(col) * 0.25, blur=0.6)
    ph.capsule(R(8, 0), R(40, 0), 2.6 * s, 2.6 * s, col, amb=0.35, spec=spec)
    ph.rect(*R(30, 2), *R(34, 9), C(col) * 0.85, blur=0.5)
    ph.rect(*R(36, 2), *R(40, 7), C(col) * 0.85, blur=0.5)

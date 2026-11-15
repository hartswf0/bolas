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

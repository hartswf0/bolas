"""Handmade film kit for the Oulipo SCION proofs.

Everything here is drawn and synthesized from scratch: frames are painted with
PIL from code, sound is built sample by sample with numpy, and ffmpeg only
encodes the result. No stock footage, no generated imagery, no sample packs.

A film script looks like:

    from kit import Film, Ink, ...
    film = Film("anemic-cinema", seconds=22)
    def frame(t, ink):           # ink is an Ink canvas for this frame
        ink.paper()
        ink.line([(100, 100), (400, 300)], width=3)
    film.picture(frame)
    film.sound(lambda mix: mix.bell(2.0))
    film.render()

Run from this directory:  python3 films/<slug>.py   (writes assets/films/<slug>.mp4 + .webp)
"""

from __future__ import annotations

import math
import os
import random
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
OUT = PROJECT / "assets" / "films"
FONTS = PROJECT / "assets" / "fonts"

W, H = 960, 540
FPS = 24
RATE = 44100

# Palette shared with operator.css so the films sit on the page.
PAPER = (243, 239, 228)
PAGE = (250, 247, 239)
INK = (36, 32, 29)
MUTED = (101, 92, 82)
RULE = (210, 199, 184)
ACCENT = (129, 44, 58)
WASH = (235, 224, 209)
BRASS = (176, 138, 62)
NIGHT = (22, 22, 28)


# ---------------------------------------------------------------- easing ---

def clamp(x, lo=0.0, hi=1.0):
    return lo if x < lo else hi if x > hi else x


def ramp(t, a, b):
    """0 before a, 1 after b, linear between."""
    if b == a:
        return 1.0 if t >= b else 0.0
    return clamp((t - a) / (b - a))


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease(t, a, b):
    return smooth(ramp(t, a, b))


def lerp(a, b, x):
    return a + (b - a) * x


def lerp2(p, q, x):
    return (lerp(p[0], q[0], x), lerp(p[1], q[1], x))


def mix_color(c1, c2, x):
    return tuple(int(round(lerp(a, b, clamp(x)))) for a, b in zip(c1, c2))


def window(t, a, b):
    """True while a <= t < b."""
    return a <= t < b


# ----------------------------------------------------------------- fonts ---

_font_cache = {}


def font(kind="sans", size=28):
    files = {
        "serif": "instrument-serif.woff2",
        "sans": "instrument-sans.woff2",
        "mono": "ibm-plex-mono.woff2",
    }
    key = (kind, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(str(FONTS / files[kind]), size)
    return _font_cache[key]


# ----------------------------------------------------------------- canvas ---

class Ink:
    """A drawing surface with a hand-made line.

    `boil` re-seeds the jitter a few times per second so lines shimmer the way
    redrawn animation drawings do. Set boil=0 for rock-steady geometry.
    """

    def __init__(self, t, frame_index, size=(W, H), boil=8, wobble=1.2, seed=0):
        self.t = t
        self.i = frame_index
        self.w, self.h = size
        self.img = Image.new("RGB", size, PAPER)
        self.d = ImageDraw.Draw(self.img, "RGBA")
        self.wobble = wobble
        step = int(frame_index * boil / FPS) if boil else 0
        self.rng = random.Random(seed * 7919 + step)

    # -- grounds
    def paper(self, color=PAPER, grain=True):
        self.d.rectangle([0, 0, self.w, self.h], fill=color)
        self._grain = grain
        return self

    def fill(self, color):
        self.d.rectangle([0, 0, self.w, self.h], fill=color)

    # -- jitter
    def j(self, amount=None):
        a = self.wobble if amount is None else amount
        return self.rng.uniform(-a, a)

    def _rough(self, pts, amount=None, subdiv=10):
        """Subdivide a polyline and push the points slightly off true."""
        out = []
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            n = max(1, int(math.hypot(x1 - x0, y1 - y0) / subdiv))
            for k in range(n):
                f = k / n
                out.append((x0 + (x1 - x0) * f + self.j(amount), y0 + (y1 - y0) * f + self.j(amount)))
        out.append((pts[-1][0] + self.j(amount), pts[-1][1] + self.j(amount)))
        return out

    # -- strokes
    def line(self, pts, color=INK, width=2.5, rough=True, amount=None, alpha=255):
        pts = [tuple(p) for p in pts]
        if rough:
            pts = self._rough(pts, amount)
        c = tuple(color[:3]) + (alpha,)
        w = max(1, int(round(width)))
        self.d.line(pts, fill=c, width=w, joint="curve")
        if w >= 3:
            r = w / 2
            for x, y in (pts[0], pts[-1]):
                self.d.ellipse([x - r, y - r, x + r, y + r], fill=c)

    def stroke(self, pts, color=INK, width=3, taper=True, alpha=255, amount=None):
        """Brush stroke: width swells in the middle and tapers at the ends."""
        pts = self._rough([tuple(p) for p in pts], amount, subdiv=4)
        n = len(pts)
        c = tuple(color[:3]) + (alpha,)
        for k, (x, y) in enumerate(pts):
            f = k / max(1, n - 1)
            r = width * (math.sin(math.pi * f) ** 0.6 if taper else 1) / 2 + 0.4
            self.d.ellipse([x - r, y - r, x + r, y + r], fill=c)

    def poly(self, pts, fill=None, color=INK, width=2.5, alpha=255, rough=True):
        pts = [tuple(p) for p in pts]
        closed = pts + [pts[0]]
        if fill is not None:
            f = tuple(fill[:3]) + ((fill[3],) if len(fill) == 4 else (alpha,))
            self.d.polygon(self._rough(closed, subdiv=14) if rough else closed, fill=f)
        if color is not None and width:
            self.line(closed, color, width, rough=rough, alpha=alpha)

    def rect(self, x0, y0, x1, y1, fill=None, color=INK, width=2.5, alpha=255, rough=True):
        self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], fill, color, width, alpha, rough)

    def circle(self, cx, cy, r, fill=None, color=INK, width=2.5, alpha=255, steps=None, rough=True):
        steps = steps or max(12, int(r * 0.8))
        pts = [(cx + r * math.cos(2 * math.pi * k / steps), cy + r * math.sin(2 * math.pi * k / steps)) for k in range(steps)]
        self.poly(pts, fill, color, width, alpha, rough)

    def ellipse(self, cx, cy, rx, ry, fill=None, color=INK, width=2.5, alpha=255, rough=True, angle=0.0):
        steps = max(16, int(max(rx, ry) * 0.8))
        ca, sa = math.cos(angle), math.sin(angle)
        pts = []
        for k in range(steps):
            a = 2 * math.pi * k / steps
            x, y = rx * math.cos(a), ry * math.sin(a)
            pts.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
        self.poly(pts, fill, color, width, alpha, rough)

    def arc(self, cx, cy, r, a0, a1, color=INK, width=2.5, alpha=255):
        steps = max(6, int(abs(a1 - a0) * r / 6))
        pts = [(cx + r * math.cos(lerp(a0, a1, k / steps)), cy + r * math.sin(lerp(a0, a1, k / steps))) for k in range(steps + 1)]
        self.line(pts, color, width, alpha=alpha)

    def hatch(self, x0, y0, x1, y1, gap=7, angle=45, color=INK, width=1.2, alpha=150):
        """Pen hatching clipped to a rectangle."""
        layer = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        dd = ImageDraw.Draw(layer)
        a = math.radians(angle)
        dx, dy = math.cos(a), math.sin(a)
        span = int(math.hypot(x1 - x0, y1 - y0)) + gap
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        for k in range(-span, span, gap):
            ox, oy = cx - dy * k, cy + dx * k
            p = (ox - dx * span + self.j(), oy - dy * span + self.j())
            q = (ox + dx * span + self.j(), oy + dy * span + self.j())
            dd.line([p, q], fill=tuple(color[:3]) + (alpha,), width=max(1, int(width)))
        mask = Image.new("L", (self.w, self.h), 0)
        ImageDraw.Draw(mask).rectangle([x0, y0, x1, y1], fill=255)
        layer.putalpha(ImageChops.multiply(layer.getchannel("A"), mask))
        self.img.paste(layer, (0, 0), layer)
        self.d = ImageDraw.Draw(self.img, "RGBA")

    # -- type
    def text(self, xy, s, kind="sans", size=28, color=INK, anchor="la", alpha=255, spacing=6, align="left"):
        f = font(kind, size)
        c = tuple(color[:3]) + (alpha,)
        if "\n" in s:
            self.d.multiline_text(xy, s, font=f, fill=c, anchor=anchor, spacing=spacing, align=align)
        else:
            self.d.text(xy, s, font=f, fill=c, anchor=anchor)

    def text_size(self, s, kind="sans", size=28):
        box = self.d.textbbox((0, 0), s, font=font(kind, size))
        return box[2] - box[0], box[3] - box[1]

    def caption(self, s, alpha=1.0, y=None, size=24, kind="serif", color=INK, band=True):
        """Subtitle line along the bottom. Our films carry voice as captions."""
        if alpha <= 0 or not s:
            return
        y = self.h - 46 if y is None else y
        tw, th = self.text_size(s, kind, size)
        if band:
            self.d.rectangle([self.w / 2 - tw / 2 - 14, y - th / 2 - 10, self.w / 2 + tw / 2 + 14, y + th / 2 + 12],
                             fill=PAGE + (int(215 * alpha),))
        self.text((self.w / 2, y), s, kind, size, color, anchor="mm", alpha=int(255 * alpha))

    def label(self, xy, s, size=14, color=MUTED, alpha=255, anchor="la"):
        self.text(xy, s, "mono", size, color, anchor=anchor, alpha=alpha)

    def card(self, title, sub=None, alpha=1.0, ground=PAPER, color=INK):
        """Full title card."""
        self.d.rectangle([0, 0, self.w, self.h], fill=tuple(ground) + (int(255 * alpha),))
        self.text((self.w / 2, self.h / 2 - (14 if sub else 0)), title, "serif", 54, color, anchor="mm", alpha=int(255 * alpha))
        if sub:
            self.text((self.w / 2, self.h / 2 + 36), sub, "mono", 15, MUTED, anchor="mm", alpha=int(255 * alpha))

    # -- compositing
    def paste(self, img, xy=(0, 0), alpha=1.0):
        img = img.convert("RGBA")
        if alpha < 1:
            a = img.getchannel("A").point(lambda v: int(v * alpha))
            img.putalpha(a)
        self.img.paste(img, (int(xy[0]), int(xy[1])), img)
        self.d = ImageDraw.Draw(self.img, "RGBA")

    def layer(self):
        """A transparent sheet to draw on and paste back (for opacity, transforms)."""
        sheet = Ink(self.t, self.i, (self.w, self.h), wobble=self.wobble)
        sheet.img = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        sheet.d = ImageDraw.Draw(sheet.img, "RGBA")
        sheet.rng = self.rng
        return sheet

    def vignette(self, strength=0.35):
        self._vignette = strength

    def finish(self):
        img = self.img.convert("RGB")
        if getattr(self, "_vignette", 0):
            img = Image.composite(img, Image.new("RGB", img.size, (0, 0, 0)), _vignette_mask(img.size, self._vignette))
        if getattr(self, "_grain", True):
            img = _add_grain(img, self.i)
        return img


_vcache = {}


def _vignette_mask(size, strength):
    key = (size, strength)
    if key not in _vcache:
        w, h = size
        y, x = np.mgrid[0:h, 0:w]
        r = np.hypot((x - w / 2) / (w / 2), (y - h / 2) / (h / 2))
        m = np.clip(1 - strength * np.clip(r - 0.45, 0, None) ** 1.5 * 1.6, 0, 1)
        _vcache[key] = Image.fromarray((m * 255).astype(np.uint8), "L")
    return _vcache[key]


_grain_bank = None


def _add_grain(img, i):
    global _grain_bank
    if _grain_bank is None:
        rs = np.random.RandomState(11)
        bank = []
        for _ in range(6):
            g = rs.normal(0, 4.0, (img.size[1] // 2, img.size[0] // 2)).astype(np.float32)
            g = np.kron(g, np.ones((2, 2), np.float32))[: img.size[1], : img.size[0]]
            bank.append(g)
        fibre = rs.normal(0, 1, (img.size[1], img.size[0])).astype(np.float32)
        fibre = np.array(Image.fromarray(((fibre * 30) + 128).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6)), np.float32) - 128
        _grain_bank = (bank, fibre * 0.6)
    bank, fibre = _grain_bank
    a = np.asarray(img, np.float32)
    if a.shape[:2] != bank[0].shape:
        return img
    a += (bank[(i // 2) % len(bank)] + fibre)[..., None]
    return Image.fromarray(a.clip(0, 255).astype(np.uint8))


# ------------------------------------------------------------------ sound ---

class Mix:
    """A mono/stereo sound bed built from first principles."""

    def __init__(self, seconds, rate=RATE, seed=0):
        self.rate = rate
        self.n = int(seconds * rate)
        self.L = np.zeros(self.n, np.float64)
        self.R = np.zeros(self.n, np.float64)
        self.rs = np.random.RandomState(seed)

    def t(self, seconds):
        return np.arange(int(seconds * self.rate)) / self.rate

    def add(self, sig, at, gain=1.0, pan=0.0):
        """Place a signal at `at` seconds. pan -1 left, +1 right."""
        i = int(at * self.rate)
        if i >= self.n or len(sig) == 0:
            return
        sig = sig[: self.n - i] * gain
        lg, rg = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
        self.L[i:i + len(sig)] += sig * lg * 1.414
        self.R[i:i + len(sig)] += sig * rg * 1.414

    # -- envelopes
    def env(self, n, attack=0.005, decay=0.3, sustain=0.0, release=0.05, hold=None):
        r = self.rate
        a, d, rl = int(attack * r), int(decay * r), int(release * r)
        h = n - a - d - rl if hold is None else int(hold * r)
        h = max(0, h)
        e = np.concatenate([np.linspace(0, 1, max(a, 1)), np.linspace(1, sustain, max(d, 1)),
                            np.full(h, sustain), np.linspace(sustain, 0, max(rl, 1))])
        return np.pad(e, (0, max(0, n - len(e))))[:n]

    # -- sources
    def tone(self, freq, seconds, wave="sine", vibrato=0.0):
        t = self.t(seconds)
        ph = 2 * np.pi * np.cumsum(np.full(len(t), freq) * (1 + vibrato * np.sin(2 * np.pi * 5.2 * t))) / self.rate
        if wave == "sine":
            return np.sin(ph)
        if wave == "tri":
            return 2 / np.pi * np.arcsin(np.sin(ph))
        if wave == "square":
            return np.tanh(4 * np.sin(ph)) * 0.6
        if wave == "saw":
            return sum(np.sin(k * ph) / k for k in range(1, 12)) * 0.5
        raise ValueError(wave)

    def noise(self, seconds, color="white"):
        x = self.rs.normal(0, 1, int(seconds * self.rate))
        if color == "pink":
            x = np.cumsum(x)
            x -= np.convolve(x, np.ones(400) / 400, "same")
            x /= (np.abs(x).max() + 1e-9)
        elif color == "brown":
            x = np.cumsum(x)
            x -= np.convolve(x, np.ones(2000) / 2000, "same")
            x /= (np.abs(x).max() + 1e-9)
        return x

    def lowpass(self, x, cutoff):
        return self.band(x, 0, cutoff)

    def band(self, x, lo, hi):
        """FFT band-pass; fine for short sounds and beds."""
        X = np.fft.rfft(x)
        f = np.fft.rfftfreq(len(x), 1 / self.rate)
        X[(f < lo) | (f > hi)] = 0
        return np.fft.irfft(X, len(x))

    # -- instruments
    def bell(self, at, freq=660, seconds=3.5, gain=0.35, pan=0.0):
        """Inharmonic struck bell."""
        t = self.t(seconds)
        partials = [(0.5, 1.0, 1.2), (1.0, 0.8, 1.0), (1.19, 0.5, 0.8), (1.56, 0.45, 0.7),
                    (2.0, 0.35, 0.5), (2.51, 0.25, 0.4), (3.01, 0.18, 0.3)]
        sig = sum(a * np.sin(2 * np.pi * freq * r * t) * np.exp(-t / (seconds * dk * 0.35)) for r, a, dk in partials)
        sig[: int(0.002 * self.rate)] *= np.linspace(0, 1, int(0.002 * self.rate))
        self.add(sig / 3, at, gain, pan)

    def ring(self, at, seconds=2.0, gain=0.25, pan=0.0, freq=1800):
        """Telephone/electric bell: fast amplitude-modulated pair."""
        t = self.t(seconds)
        sig = (np.sin(2 * np.pi * freq * t) + 0.6 * np.sin(2 * np.pi * freq * 1.27 * t)) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 22 * t)))
        sig *= self.env(len(t), 0.01, 0.05, 1.0, 0.1)
        self.add(sig * 0.5, at, gain, pan)

    def click(self, at, gain=0.3, pan=0.0, bright=4000, seconds=0.03):
        x = self.noise(seconds) * np.exp(-np.linspace(0, 8, int(seconds * self.rate)))
        self.add(self.band(x, 200, bright), at, gain, pan)

    def thud(self, at, freq=70, gain=0.5, pan=0.0, seconds=0.35):
        t = self.t(seconds)
        f = freq * (1 + 1.5 * np.exp(-t * 30))
        sig = np.sin(2 * np.pi * np.cumsum(f) / self.rate) * np.exp(-t * 12)
        self.add(sig + 0.2 * self.noise(seconds) * np.exp(-t * 40), at, gain, pan)

    def step(self, at, gain=0.22, pan=0.0, surface="stone"):
        bright = {"stone": 3500, "wood": 1800, "water": 1200, "gravel": 6000}[surface]
        sec = 0.09 if surface != "water" else 0.25
        x = self.noise(sec) * np.exp(-np.linspace(0, 6, int(sec * self.rate)))
        sig = self.band(x, 80, bright)
        if surface == "wood":
            t = self.t(sec)
            sig += 0.6 * np.sin(2 * np.pi * 140 * t) * np.exp(-t * 40)
        self.add(sig, at, gain, pan)

    def steps(self, start, end, every=0.5, gain=0.2, surface="stone", pan_from=0.0, pan_to=0.0):
        k, t = 0, start
        while t < end:
            p = lerp(pan_from, pan_to, ramp(t, start, end))
            self.step(t + self.rs.uniform(-0.015, 0.015), gain * (0.85 if k % 2 else 1.0), p, surface)
            t += every
            k += 1

    def drone(self, at, seconds, freqs=(55, 82.5, 110), gain=0.08, pan=0.0, attack=1.5, release=1.5):
        sig = sum(self.tone(f, seconds, "sine", vibrato=0.002) * (1 / (k + 1)) for k, f in enumerate(freqs))
        sig *= self.env(len(sig), attack, 0.01, 1.0, release)
        self.add(sig, at, gain, pan)

    def room(self, at, seconds, gain=0.03, hum=50):
        """Room tone: pink air plus mains hum."""
        n = self.noise(seconds, "pink") * 0.7 + 0.15 * np.sin(2 * np.pi * hum * self.t(seconds))
        n *= self.env(len(n), 0.4, 0.01, 1.0, 0.4)
        self.add(n, at, gain, -0.2)
        self.add(self.noise(seconds, "pink") * self.env(len(n), 0.4, 0.01, 1.0, 0.4) * 0.7, at, gain, 0.2)

    def wind(self, at, seconds, gain=0.06):
        x = self.noise(seconds, "brown")
        lfo = 0.6 + 0.4 * np.sin(2 * np.pi * 0.15 * self.t(seconds) + self.rs.uniform(0, 6))
        self.add(x * lfo * self.env(len(x), 1.0, 0.01, 1.0, 1.0), at, gain)

    def water(self, at, seconds, gain=0.08):
        x = self.band(self.noise(seconds), 300, 2500)
        # random droplets
        for _ in range(int(seconds * 14)):
            k = self.rs.randint(0, max(1, len(x) - 2000))
            f = self.rs.uniform(600, 1800)
            tt = np.arange(1500) / self.rate
            x[k:k + 1500] += 2.5 * np.sin(2 * np.pi * (f + 4000 * tt) * tt) * np.exp(-tt * 60)
        x *= 0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 0.31 * self.t(seconds)))
        self.add(x * self.env(len(x), 0.8, 0.01, 1, 0.8) * 0.4, at, gain)

    def note(self, at, freq, seconds=0.4, gain=0.18, pan=0.0, wave="tri", attack=0.01, decay=0.25, sustain=0.3):
        sig = self.tone(freq, seconds, wave) * self.env(int(seconds * self.rate), attack, decay, sustain, 0.08)
        self.add(sig, at, gain, pan)

    def pluck(self, at, freq, seconds=1.2, gain=0.2, pan=0.0):
        """Karplus-Strong string."""
        n = int(seconds * self.rate)
        p = max(2, int(self.rate / freq))
        buf = self.rs.uniform(-1, 1, p)
        out = np.empty(n)
        for k in range(n):
            out[k] = buf[k % p]
            buf[k % p] = 0.996 * 0.5 * (buf[k % p] + buf[(k + 1) % p])
        self.add(out, at, gain, pan)

    def murmur(self, at, seconds, gain=0.08, pitch=120, pan=0.0, seed=None):
        """Voice-like murmur under a caption: formant-filtered buzz with syllable rhythm.

        It is not speech. It marks that someone is talking without inventing words."""
        rs = np.random.RandomState(seed if seed is not None else self.rs.randint(1 << 30))
        t = self.t(seconds)
        f0 = pitch * (1 + 0.06 * np.sin(2 * np.pi * 1.3 * t) + 0.03 * rs.normal(0, 1) * np.sin(2 * np.pi * 0.4 * t))
        ph = 2 * np.pi * np.cumsum(f0) / self.rate
        buzz = sum(np.sin(k * ph) / k for k in range(1, 30))
        out = np.zeros_like(buzz)
        # three vowel formants that drift per syllable
        syl = 0.18
        nsyl = int(seconds / syl) + 1
        vowels = [(730, 1090, 2440), (270, 2290, 3010), (300, 870, 2240), (530, 1840, 2480), (570, 840, 2410)]
        for s in range(nsyl):
            a, b = int(s * syl * self.rate), int(min(seconds, (s + 1) * syl) * self.rate)
            if a >= b:
                continue
            seg = buzz[a:b]
            F = vowels[rs.randint(len(vowels))]
            y = sum(self.band(seg, f * 0.85, f * 1.15) * g for f, g in zip(F, (1.0, 0.5, 0.25)))
            y *= np.hanning(len(y)) ** 0.5 * (0.4 if rs.rand() < 0.15 else 1.0)
            out[a:b] += y
        out *= self.env(len(out), 0.05, 0.01, 1.0, 0.1)
        out /= (np.abs(out).max() + 1e-9)
        self.add(out, at, gain, pan)

    def whoosh(self, at, seconds=0.5, gain=0.12, pan=0.0):
        x = self.band(self.noise(seconds), 300, 5000) * np.hanning(int(seconds * self.rate))
        self.add(x, at, gain, pan)

    def reverb(self, amount=0.25, size=1.0):
        """Small Schroeder-ish room: a few feedback combs."""
        for ch in (self.L, self.R):
            wet = np.zeros_like(ch)
            for k, d in enumerate((1116, 1188, 1277, 1356)):
                d = int(d * size)
                y = ch.copy()
                for _ in range(5):
                    y = np.concatenate([np.zeros(d), y[:-d]]) * 0.62
                    wet += y / 4
            ch += wet * amount

    def master(self):
        st = np.stack([self.L, self.R], 1)
        peak = np.abs(st).max()
        if peak > 0:
            st = st / max(peak, 1.0) * 0.89  # only attenuate; keep declared silence silent
            rms = math.sqrt((st ** 2).mean())
            if rms > 0 and peak < 0.25:
                st *= min(4.0, 0.2 / max(rms, 1e-6), 0.89 / max(np.abs(st).max(), 1e-9))
        fade = int(0.05 * self.rate)
        st[:fade] *= np.linspace(0, 1, fade)[:, None]
        st[-fade:] *= np.linspace(1, 0, fade)[:, None]
        return (st * 32767).astype(np.int16)


# ------------------------------------------------------------------- film ---

class Film:
    def __init__(self, slug, seconds, size=(W, H), fps=FPS, boil=8, wobble=1.2, seed=0):
        self.slug = slug
        self.seconds = seconds
        self.size = size
        self.fps = fps
        self.boil = boil
        self.wobble = wobble
        self.seed = seed
        self._picture = None
        self._sound = None
        self.poster_at = seconds * 0.4

    def picture(self, fn):
        self._picture = fn
        return fn

    def sound(self, fn):
        self._sound = fn
        return fn

    def frame(self, k):
        t = k / self.fps
        ink = Ink(t, k, self.size, self.boil, self.wobble, self.seed)
        ink.paper()
        self._picture(t, ink)
        return ink.finish()

    def render(self, out_dir=OUT, preview=None):
        """Encode picture and sound. `preview=[t, ...]` writes PNG stills only."""
        out_dir.mkdir(parents=True, exist_ok=True)
        if preview is None and len(sys.argv) > 1 and sys.argv[1] == "--stills":
            preview = [float(x) for x in sys.argv[2:]] or [self.seconds * f for f in (0.1, 0.3, 0.5, 0.7, 0.9)]
        if preview:
            pdir = HERE / "stills" / self.slug
            pdir.mkdir(parents=True, exist_ok=True)
            for t in preview:
                self.frame(int(t * self.fps)).save(pdir / f"{t:06.2f}.png")
            print("stills ->", pdir)
            return
        total = int(round(self.seconds * self.fps))
        with tempfile.TemporaryDirectory() as tmp:
            wav = Path(tmp) / "a.wav"
            mix = Mix(self.seconds, seed=self.seed)
            if self._sound:
                self._sound(mix)
            pcm = mix.master()
            with wave.open(str(wav), "wb") as wf:
                wf.setnchannels(2)
                wf.setsampwidth(2)
                wf.setframerate(RATE)
                wf.writeframes(pcm.tobytes())
            mp4 = out_dir / f"{self.slug}.mp4"
            cmd = ["ffmpeg", "-y", "-loglevel", "error",
                   "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{self.size[0]}x{self.size[1]}", "-r", str(self.fps), "-i", "-",
                   "-i", str(wav),
                   "-c:v", "libx264", "-preset", "slow", "-crf", "28", "-pix_fmt", "yuv420p", "-tune", "animation",
                   "-c:a", "aac", "-b:a", "96k", "-shortest", "-movflags", "+faststart", str(mp4)]
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
            poster_k = int(self.poster_at * self.fps)
            for k in range(total):
                img = self.frame(k)
                if k == poster_k:
                    img.save(out_dir / f"{self.slug}.webp", quality=82)
                proc.stdin.write(img.tobytes())
                if k % (self.fps * 5) == 0:
                    print(f"  {self.slug}: {k / self.fps:5.1f}s / {self.seconds}s", flush=True)
            proc.stdin.close()
            if proc.wait() != 0:
                raise SystemExit("ffmpeg failed")
        print(f"wrote {mp4.relative_to(PROJECT)} ({mp4.stat().st_size / 1e6:.1f} MB)")


# ------------------------------------------------------------- figures ---

def figure(ink, x, y, s=1.0, pose="stand", phase=0.0, facing=1, color=INK, width=2.6, hat=False, coat=None, arm=None):
    """A drawn person, feet at (x, y). pose: stand, walk, sit, reach, run.

    `phase` advances the walk cycle (0..1 per stride). `arm` overrides the
    forward arm as an (angle_degrees) from straight down."""
    h = 120 * s
    head_r = 11 * s
    hip = (x, y - h * 0.48)
    neck = (x, y - h * 0.84)
    if pose == "sit":
        hip = (x, y - h * 0.36)
        neck = (x + 2 * facing * s, y - h * 0.72)
    head = (neck[0] + 1 * facing * s, neck[1] - head_r * 1.25)
    # legs
    if pose in ("walk", "run"):
        amp = 0.5 if pose == "walk" else 0.85
        a = math.sin(2 * math.pi * phase) * amp
        legs = []
        for sgn in (1, -1):
            th = a * sgn
            knee = (hip[0] + math.sin(th) * h * 0.25 * facing, hip[1] + math.cos(th) * h * 0.25)
            bend = max(0, -math.sin(2 * math.pi * phase) * sgn) * 0.5 + 0.1
            foot = (knee[0] + math.sin(th - bend) * h * 0.24 * facing, knee[1] + math.cos(th - bend) * h * 0.24)
            legs.append([hip, knee, foot])
    elif pose == "sit":
        knee = (hip[0] + h * 0.24 * facing, hip[1])
        legs = [[hip, knee, (knee[0] + 2 * facing, y)], [hip, (knee[0] - 5 * facing, hip[1] + 2), (knee[0] - 4 * facing, y)]]
    else:
        legs = [[hip, (x - 4 * s, y - h * 0.24), (x - 6 * s, y)], [hip, (x + 4 * s, y - h * 0.24), (x + 6 * s, y)]]
    for leg in legs:
        ink.line(leg, color, width)
    # body / coat
    if coat:
        shoulder_w = 13 * s
        ink.poly([(neck[0] - shoulder_w, neck[1] + 4 * s), (neck[0] + shoulder_w, neck[1] + 4 * s),
                  (hip[0] + shoulder_w * 1.2, hip[1] + 10 * s), (hip[0] - shoulder_w * 1.2, hip[1] + 10 * s)],
                 fill=coat, color=color, width=width * 0.8)
    else:
        ink.line([neck, hip], color, width)
    # arms
    sh = (neck[0], neck[1] + 8 * s)
    if pose in ("walk", "run"):
        a = math.sin(2 * math.pi * phase) * (0.5 if pose == "walk" else 0.9)
        arms = [-a, a]
    elif pose == "reach":
        arms = [math.radians(arm if arm is not None else 80), 0.15]
    elif pose == "sit":
        arms = [math.radians(arm if arm is not None else 35), 0.25]
    else:
        arms = [math.radians(arm) if arm is not None else 0.12, -0.12]
    hands = []
    for th in arms:
        elbow = (sh[0] + math.sin(th) * h * 0.2 * facing, sh[1] + math.cos(th) * h * 0.2)
        hand = (elbow[0] + math.sin(th * 1.15) * h * 0.18 * facing, elbow[1] + math.cos(th * 1.15) * h * 0.18)
        ink.line([sh, elbow, hand], color, width)
        hands.append(hand)
    ink.circle(head[0], head[1], head_r, fill=PAGE, color=color, width=width)
    if hat:
        ink.line([(head[0] - head_r * 1.5, head[1] - head_r * 0.5), (head[0] + head_r * 1.5, head[1] - head_r * 0.5)], color, width)
        ink.rect(head[0] - head_r * 0.9, head[1] - head_r * 1.6, head[0] + head_r * 0.9, head[1] - head_r * 0.5, fill=color, color=color, width=1)
    return {"head": head, "hands": hands, "hip": hip, "neck": neck}


def key_shape(ink, x, y, s=1.0, angle=0.0, color=BRASS, outline=INK):
    """The brass key that recurs across the station seed."""
    ca, sa = math.cos(angle), math.sin(angle)

    def P(px, py):
        return (x + (px * ca - py * sa) * s, y + (px * sa + py * ca) * s)

    ink.circle(*P(0, 0), 9 * s, fill=color, color=outline, width=max(1.5, 2 * s))
    ink.circle(*P(0, 0), 3.5 * s, fill=PAPER, color=outline, width=1.2)
    ink.poly([P(8, -2.5), P(40, -2.5), P(40, 2.5), P(8, 2.5)], fill=color, color=outline, width=max(1.2, 1.6 * s))
    ink.poly([P(30, 2.5), P(34, 2.5), P(34, 9), P(30, 9)], fill=color, color=outline, width=1.2)
    ink.poly([P(36, 2.5), P(40, 2.5), P(40, 7), P(36, 7)], fill=color, color=outline, width=1.2)


def envelope(ink, x, y, w=60, h=40, open_=0.0, color=PAGE, outline=INK, angle=0.0):
    ink.rect(x - w / 2, y - h / 2, x + w / 2, y + h / 2, fill=color, color=outline, width=2)
    tip_y = lerp(y + 2, y - h * 0.95, open_)
    ink.poly([(x - w / 2, y - h / 2), (x + w / 2, y - h / 2), (x, tip_y)], fill=WASH if open_ > 0.5 else color, color=outline, width=1.8)


def bench(ink, x, y, w=220, color=INK, fill=(150, 110, 70)):
    ink.rect(x - w / 2, y - 48, x + w / 2, y - 40, fill=fill, color=color, width=2)
    ink.rect(x - w / 2, y - 78, x + w / 2, y - 70, fill=fill, color=color, width=2)
    for px in (x - w / 2 + 14, x + w / 2 - 14):
        ink.line([(px, y - 40), (px, y)], color, 3)
        ink.line([(px, y - 70), (px, y - 48)], color, 2)


def door(ink, x, y, w=90, h=170, open_=0.0, fill=(120, 96, 80), color=INK, sign=None):
    ink.rect(x - w / 2 - 8, y - h - 8, x + w / 2 + 8, y, fill=None, color=color, width=3)
    ww = w * (1 - 0.85 * open_)
    ink.rect(x - w / 2, y - h, x - w / 2 + ww, y, fill=fill, color=color, width=2.5)
    ink.circle(x - w / 2 + ww - 12, y - h / 2, 4, fill=BRASS, color=color, width=1.5)
    if sign:
        ink.rect(x - 32, y - h - 36, x + 32, y - h - 14, fill=PAGE, color=color, width=1.5)
        ink.label((x, y - h - 25), sign, 11, INK, anchor="mm")


def clock(ink, x, y, r, hours, color=INK, face=PAGE):
    ink.circle(x, y, r, fill=face, color=color, width=3)
    for k in range(12):
        a = 2 * math.pi * k / 12
        ink.line([(x + math.cos(a) * r * 0.82, y + math.sin(a) * r * 0.82), (x + math.cos(a) * r * 0.94, y + math.sin(a) * r * 0.94)], color, 2, rough=False)
    ha = 2 * math.pi * (hours / 12) - math.pi / 2
    ma = 2 * math.pi * (hours % 1) - math.pi / 2
    ink.line([(x, y), (x + math.cos(ha) * r * 0.5, y + math.sin(ha) * r * 0.5)], color, 4, rough=False)
    ink.line([(x, y), (x + math.cos(ma) * r * 0.78, y + math.sin(ma) * r * 0.78)], color, 2.5, rough=False)
    ink.circle(x, y, 3, fill=color, color=color, width=1, rough=False)


def platform(ink, horizon=330, color=INK, ground=WASH):
    """A one-point-perspective station platform."""
    ink.d.rectangle([0, horizon, ink.w, ink.h], fill=ground)
    ink.line([(0, horizon), (ink.w, horizon)], color, 2)
    vp = (ink.w * 0.62, horizon - 60)
    for x in (-200, 120, 1100, 1500):
        ink.line([(x, ink.h), lerp2((x, ink.h), vp, 0.75)], color, 1.6, alpha=170)
    for k in range(7):
        yy = lerp(horizon, ink.h, (k / 7) ** 1.6)
        ink.line([(0, yy), (ink.w, yy)], RULE, 1, alpha=180)
    return vp

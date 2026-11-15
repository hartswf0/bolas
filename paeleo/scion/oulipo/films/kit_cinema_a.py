"""Extra helpers for the cinema-A group of films (Machine, Homme qui dort,
Lieux d'une fugue, Ellis Island, Styrène, Zazie). Builds on kit.py; does not
modify it. Everything is drawn or synthesized in code."""
from __future__ import annotations

import hashlib
import math

import numpy as np
from PIL import Image

from kit import *  # noqa: F401,F403
from kit import FPS, INK, NIGHT, PAGE, PAPER, RULE, Ink, ease, lerp


# ------------------------------------------------------------ timelines ---

def segment(t, segs):
    """segs: list of (name, seconds). Returns (name, local_t, dur, start)."""
    a = 0.0
    for name, d in segs:
        if t < a + d:
            return name, t - a, d, a
        a += d
    name, d = segs[-1]
    return name, d, d, a - d


def starts(segs):
    out, a = {}, 0.0
    for name, d in segs:
        out.setdefault(name, a)
        a += d
    return out


def fade_edges(ink, local, dur, f=0.3, color=NIGHT):
    x = min(1.0, local / f if f else 1, (dur - local) / f if f else 1)
    if x < 1:
        ink.d.rectangle([0, 0, ink.w, ink.h], fill=tuple(color) + (int(255 * (1 - max(0, x))),))


def tag(ink, xy, s, size=13, fg=PAGE, bg=NIGHT, anchor="la", alpha=230, pad=6):
    """Mono label on a small solid band (slates, record lines)."""
    if not s:
        return
    tw, th = ink.text_size(s, "mono", size)
    x, y = xy
    if anchor[0] == "m":
        x -= tw / 2
    elif anchor[0] == "r":
        x -= tw
    ink.d.rectangle([x - pad, y - pad + 1, x + tw + pad, y + th + pad + 2], fill=tuple(bg) + (alpha,))
    ink.text((x, y), s, "mono", size, fg)


def title_card(ink, title, sub=None, ground=NIGHT, fg=PAGE, subfg=RULE, size=50):
    ink.fill(ground)
    ink.text((ink.w / 2, ink.h / 2 - (16 if sub else 0)), title, "serif", size, fg, anchor="mm")
    if sub:
        ink.text((ink.w / 2, ink.h / 2 + 34), sub, "mono", 14, subfg, anchor="mm")


# ------------------------------------------------------------ shot pool ---

def build_clip(fn, n, size, boil=8, wobble=1.2, seed=0, ground=PAPER):
    """Render an n-frame source clip once. fn(k, u, ink) with u = k/(n-1)."""
    frames = []
    for k in range(n):
        ink = Ink(k / FPS, k, size, boil, wobble, seed)
        ink.paper(ground)
        fn(k, k / max(1, n - 1), ink)
        frames.append(ink.img.convert("RGB"))
    return frames


def frames_hash(frames):
    h = hashlib.sha1()
    for f in frames:
        h.update(f.tobytes())
    return h.hexdigest()


def rot_paste(ink, img, cx, cy, angle_deg, alpha=1.0):
    r = img.convert("RGBA").rotate(angle_deg, resample=Image.BICUBIC, expand=True)
    ink.paste(r, (cx - r.width / 2, cy - r.height / 2), alpha)


# ------------------------------------------------------------ voice-ish ---

VOWELS = [(730, 1090, 2440), (270, 2290, 3010), (300, 870, 2240), (530, 1840, 2480), (570, 840, 2410), (440, 1020, 2240)]


def chant(mix, at, n_syll, syl=0.3, caesura=None, gap=0.4, pitch=130, gain=0.12, pan=0.0, seed=0):
    """Measured syllable pulses (a sung/spoken metre without words).

    Returns the onset time of every syllable so picture cuts can be placed on
    or against them. With `caesura=6` a gap is left after syllable 6."""
    rs = np.random.RandomState(seed)
    onsets = []
    t = at
    for s in range(n_syll):
        onsets.append(t)
        last_of_half = caesura and (s + 1) % caesura == 0
        stress = last_of_half or s == n_syll - 1
        d = syl * (1.45 if stress else 1.0)
        tt = mix.t(d)
        f0 = pitch * (1.0 - 0.10 * s / n_syll) * (1.06 if stress else 1.0) * (1 + 0.02 * np.sin(2 * np.pi * 5 * tt))
        ph = 2 * np.pi * np.cumsum(f0) / mix.rate
        buzz = sum(np.sin(k * ph) / k for k in range(1, 24))
        F = VOWELS[rs.randint(len(VOWELS))]
        y = sum(mix.band(buzz, f * 0.85, f * 1.15) * g for f, g in zip(F, (1.0, 0.5, 0.25)))
        cons = mix.band(mix.noise(0.03), 2500, 7000) * 0.4
        y[: len(cons)] += cons * np.abs(y).max()
        y *= mix.env(len(y), 0.025, 0.05, 0.75, 0.08)
        y /= np.abs(y).max() + 1e-9
        mix.add(y, t, gain * (1.15 if stress else 1.0), pan)
        t += d + 0.02
        if last_of_half and s + 1 < n_syll:
            t += gap
    return onsets


def paper_flutter(mix, at, seconds=1.2, gain=0.08, pan=0.0):
    n = mix.noise(seconds)
    x = mix.band(n, 1500, 6000)
    tt = mix.t(seconds)
    am = (0.5 + 0.5 * np.sin(2 * np.pi * 11 * tt + 3 * np.sin(2 * np.pi * 1.3 * tt))) ** 3
    mix.add(x * am * mix.env(len(x), 0.05, 0.01, 1.0, 0.3), at, gain, pan)


def heartbeat(mix, at, until, bpm=72, accel=0.0, gain=0.35):
    t = at
    while t < until:
        mix.thud(t, 48, gain, 0, 0.25)
        mix.thud(t + 0.22, 44, gain * 0.7, 0, 0.25)
        b = bpm + accel * (t - at)
        t += 60.0 / b


def phone_ring(mix, at, gain=0.2, pan=0.0):
    """Old two-bell telephone: two bursts per ring."""
    mix.ring(at, 0.45, gain, pan, freq=1450)
    mix.ring(at + 0.6, 0.45, gain, pan, freq=1450)


def train_rumble(mix, at, seconds, gain=0.15, pan_from=-0.6, pan_to=0.6, chuff=None):
    x = mix.lowpass(mix.noise(seconds, "brown"), 400)
    x /= np.abs(x).max() + 1e-9
    x *= mix.env(len(x), seconds * 0.3, 0.01, 1.0, seconds * 0.4)
    n = len(x)
    pan = np.linspace(pan_from, pan_to, n)
    i = int(at * mix.rate)
    m = min(n, mix.n - i)
    if m <= 0:
        return
    lg = np.cos((pan[:m] + 1) * math.pi / 4) * 1.414
    rg = np.sin((pan[:m] + 1) * math.pi / 4) * 1.414
    mix.L[i:i + m] += x[:m] * lg * gain
    mix.R[i:i + m] += x[:m] * rg * gain
    if chuff:
        t = at
        while t < at + seconds:
            mix.click(t, gain * 0.9, lerp(pan_from, pan_to, (t - at) / seconds), 1800, 0.05)
            t += chuff


def chant_times(at, n_syll, syl=0.3, caesura=None, gap=0.4):
    """Onsets and end time that `chant` will produce with the same arguments."""
    onsets, t = [], at
    for s in range(n_syll):
        onsets.append(t)
        last_of_half = caesura and (s + 1) % caesura == 0
        stress = last_of_half or s == n_syll - 1
        t += syl * (1.45 if stress else 1.0) + 0.02
        if last_of_half and s + 1 < n_syll:
            t += gap
    return onsets, t

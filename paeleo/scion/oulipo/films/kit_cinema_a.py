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


# ===================================================== photographic look ===
# Value-based rendering: shapes become height fields, shaded by a light, then
# graded like film stock (tone curve, toning, halation, vignette, grain).

from PIL import ImageDraw, ImageFilter


def blur_arr(a, r):
    """Gaussian blur of a float array (H,W) or (H,W,3) in 0..1 via PIL."""
    if r <= 0:
        return a
    if a.ndim == 2:
        im = Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8), "L")
        return np.asarray(im.filter(ImageFilter.GaussianBlur(r)), np.float32) / 255
    im = Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8), "RGB")
    return np.asarray(im.filter(ImageFilter.GaussianBlur(r)), np.float32) / 255


def fnoise(w, h, seed=0, octaves=5, base=4, persist=0.55):
    """Fractal value noise in 0..1 (for stone, paper, haze, skin)."""
    rs = np.random.RandomState(seed)
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        n = base * (2 ** o)
        g = rs.rand(max(2, int(h * n / w) + 2), n + 2).astype(np.float32)
        im = Image.fromarray((g * 255).astype(np.uint8), "L").resize((w, h), Image.BICUBIC)
        out += amp * np.asarray(im, np.float32) / 255
        tot += amp
        amp *= persist
    out /= tot
    return (out - out.min()) / (out.max() - out.min() + 1e-6)


def vgrad(h, w, top, bottom, gamma=1.0):
    f = (np.linspace(0, 1, h, dtype=np.float32) ** gamma)[:, None, None]
    return np.asarray(top, np.float32)[None, None] / 255 * (1 - f) + np.asarray(bottom, np.float32)[None, None] / 255 * f + np.zeros((1, w, 1), np.float32)


def poly_mask(w, h, pts, blur=0):
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).polygon([tuple(p) for p in pts], fill=255)
    if blur:
        m = m.filter(ImageFilter.GaussianBlur(blur))
    return np.asarray(m, np.float32) / 255


def ellipse_mask(w, h, cx, cy, rx, ry, blur=0):
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=255)
    if blur:
        m = m.filter(ImageFilter.GaussianBlur(blur))
    return np.asarray(m, np.float32) / 255


def comp(base, color, mask):
    """Composite a flat colour (0..255 tuple or HxWx3 array 0..1) through a mask."""
    c = np.asarray(color, np.float32)
    if c.ndim == 1:
        c = c / 255
    return base * (1 - mask[..., None]) + c * mask[..., None]


def box_blur(a, r, passes=3):
    """Separable box blur of a float array (approximately Gaussian after 3 passes)."""
    r = int(max(1, r))
    out = a.astype(np.float32)
    for _ in range(passes):
        for ax in (0, 1):
            c = np.cumsum(np.pad(out, [(r + 1, r) if k == ax else (0, 0) for k in range(out.ndim)], mode="edge"), axis=ax)
            n = out.shape[ax]
            out = (np.take(c, np.arange(2 * r + 1, 2 * r + 1 + n), axis=ax) - np.take(c, np.arange(0, n), axis=ax)) / (2 * r + 1)
    return out


class Relief:
    """Tiny height-field renderer: ellipsoids, capsules and bevelled slabs
    with a z-buffer, then Lambert + specular shading from one light."""

    def __init__(self, w, h, bg=None):
        self.w, self.h = w, h
        self.z = np.full((h, w), -1e6, np.float32)
        self.col = np.zeros((h, w, 3), np.float32) if bg is None else bg.astype(np.float32).copy()
        self.bg = self.col.copy()
        self.gloss = np.zeros((h, w), np.float32)
        self.trans = np.zeros((h, w), np.float32)
        self.hit = np.zeros((h, w), bool)

    def _grid(self, x0, y0, x1, y1):
        x0, y0 = max(0, int(x0)), max(0, int(y0))
        x1, y1 = min(self.w, int(x1) + 1), min(self.h, int(y1) + 1)
        if x0 >= x1 or y0 >= y1:
            return None
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        return (slice(y0, y1), slice(x0, x1)), xx, yy

    def _write(self, sl, hgt, inside, color, gloss, trans=0.0, tex=None):
        cur = self.z[sl]
        win = inside & (hgt > cur)
        cur[win] = hgt[win]
        c = np.asarray(color, np.float32) / 255
        cc = self.col[sl]
        if tex is not None:
            cc[win] = c * tex[win][:, None]
        else:
            cc[win] = c
        self.gloss[sl][win] = gloss
        self.trans[sl][win] = trans
        self.hit[sl][win] = True

    def ellipsoid(self, cx, cy, rx, ry, depth=None, base=0.0, color=(200, 200, 200), gloss=0.0, angle=0.0, trans=0.0, tex=None):
        r = max(rx, ry)
        g = self._grid(cx - r, cy - r, cx + r, cy + r)
        if g is None:
            return
        sl, xx, yy = g
        ca, sa = math.cos(angle), math.sin(angle)
        u = ((xx - cx) * ca + (yy - cy) * sa) / rx
        v = (-(xx - cx) * sa + (yy - cy) * ca) / ry
        q = 1 - u * u - v * v
        inside = q > 0
        hgt = base + (depth if depth is not None else min(rx, ry)) * np.sqrt(np.clip(q, 0, 1))
        self._write(sl, hgt, inside, color, gloss, trans, None if tex is None else tex[sl])

    def capsule(self, p0, p1, r, r1=None, depth=None, base=0.0, color=(200, 200, 200), gloss=0.0, trans=0.0):
        r1 = r if r1 is None else r1
        R = max(r, r1)
        g = self._grid(min(p0[0], p1[0]) - R, min(p0[1], p1[1]) - R, max(p0[0], p1[0]) + R, max(p0[1], p1[1]) + R)
        if g is None:
            return
        sl, xx, yy = g
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        L2 = dx * dx + dy * dy + 1e-6
        f = np.clip(((xx - p0[0]) * dx + (yy - p0[1]) * dy) / L2, 0, 1)
        px, py = p0[0] + f * dx, p0[1] + f * dy
        d = np.hypot(xx - px, yy - py)
        rr = r + (r1 - r) * f
        q = 1 - (d / rr) ** 2
        inside = q > 0
        hgt = base + (depth if depth is not None else 1.0) * rr * np.sqrt(np.clip(q, 0, 1))
        self._write(sl, hgt, inside, color, gloss, trans)

    def slab(self, pts, height=20.0, bevel=6.0, base=0.0, color=(200, 200, 200), gloss=0.0, trans=0.0, tex=None):
        m = poly_mask(self.w, self.h, pts)
        if bevel > 0:
            mb = blur_arr(m, bevel) * m
            mb = np.clip(mb * 2.0, 0, 1)
        else:
            mb = m
        hgt = base + height * mb
        sl = (slice(0, self.h), slice(0, self.w))
        self._write(sl, hgt, m > 0.5, color, gloss, trans, tex)

    def dent(self, cx, cy, rx, ry, depth, angle=0.0, color=None, mix=1.0):
        """Push the surface in (eye sockets, creases); optionally tint it."""
        r = max(rx, ry)
        g = self._grid(cx - r, cy - r, cx + r, cy + r)
        if g is None:
            return
        sl, xx, yy = g
        ca, sa = math.cos(angle), math.sin(angle)
        u = ((xx - cx) * ca + (yy - cy) * sa) / rx
        v = (-(xx - cx) * sa + (yy - cy) * ca) / ry
        q = np.clip(1 - u * u - v * v, 0, 1)
        m = (q > 0) & self.hit[sl]
        self.z[sl] -= depth * q * m
        if color is not None:
            c = np.asarray(color, np.float32) / 255
            k = (np.sqrt(q) * mix * m)[..., None]
            self.col[sl] = self.col[sl] * (1 - k) + c * k

    def field(self, z, color=(200, 200, 200), tex=None, gloss=0.0):
        """Cover the whole frame with a surface of height z (cloth, walls, ground)."""
        self.z = z.astype(np.float32).copy()
        c = np.asarray(color, np.float32) / 255
        self.col = np.broadcast_to(c, (self.h, self.w, 3)).copy()
        if tex is not None:
            self.col *= tex[..., None]
        self.gloss[:] = gloss
        self.hit[:] = True

    def bump(self, cx, cy, rx, ry, depth, angle=0.0, color=None, mix=1.0, soft=False):
        """Raise the existing surface (nose, cheeks, lips) and optionally tint it."""
        r = max(rx, ry)
        g = self._grid(cx - r, cy - r, cx + r, cy + r)
        if g is None:
            return
        sl, xx, yy = g
        ca, sa = math.cos(angle), math.sin(angle)
        u = ((xx - cx) * ca + (yy - cy) * sa) / rx
        v = (-(xx - cx) * sa + (yy - cy) * ca) / ry
        q = np.clip(1 - u * u - v * v, 0, 1)
        m = self.hit[sl]
        prof = q * q if soft else np.sqrt(q)
        self.z[sl] += depth * prof * m
        if color is not None:
            c = np.asarray(color, np.float32) / 255
            k = (np.clip(q * 4, 0, 1) * mix * m)[..., None]
            self.col[sl] = self.col[sl] * (1 - k) + c * k

    def paint(self, mask, color, alpha=1.0):
        """Tint the surface colour through a 0..1 mask (eyes, lips, labels)."""
        c = np.asarray(color, np.float32) / 255
        k = (mask * alpha)[..., None]
        self.col = self.col * (1 - k) + c * k

    def render(self, light=(-0.5, -0.6, 0.75), amb=0.3, diff=0.8, spec=0.6, shin=40, rim=0.0, shadow=None, smooth=0):
        z = np.where(self.hit, self.z, 0.0).astype(np.float32)
        if smooth:
            z = box_blur(z, smooth)
        gy, gx = np.gradient(z)
        gx = np.clip(gx, -4, 4)
        gy = np.clip(gy, -4, 4)
        n = np.stack([-gx, -gy, np.ones_like(gx)], -1)
        n /= np.linalg.norm(n, axis=-1, keepdims=True)
        l = np.asarray(light, np.float32)
        l /= np.linalg.norm(l)
        d = np.clip((n * l).sum(-1), 0, 1)
        hv = l + np.array([0, 0, 1], np.float32)
        hv /= np.linalg.norm(hv)
        s = np.clip((n * hv).sum(-1), 0, 1) ** shin
        shade = amb + diff * d
        if rim:
            shade += rim * (1 - n[..., 2]) ** 2
        out = self.col * shade[..., None] * (1 - self.trans[..., None] * 0.4) + self.col * self.trans[..., None] * 0.5
        out += (spec * s * self.gloss)[..., None]
        out = np.where(self.hit[..., None], out, self.bg)
        return np.clip(out, 0, 1)

    def silhouette(self):
        return self.hit.astype(np.float32)


def cast_shadow(bg, mask, dx, dy, blur, strength=0.6):
    """Darken bg (HxWx3, 0..1) by an offset, blurred copy of mask."""
    m = np.roll(np.roll(mask, int(dy), 0), int(dx), 1)
    m = blur_arr(m, blur)
    return bg * (1 - strength * m[..., None])


_grain_cache = {}


def photo(arr, mono=False, tone=None, contrast=1.0, pivot=0.45, gamma=1.0, lift=0.0, crush=0.0, gain=1.0, sat=1.0,
          blur=0.7, halation=0.0, hal_color=(1.0, 0.75, 0.55), hal_r=12, vignette=0.35, grain=0.035, grain_size=1.3,
          seed=0, haze=None):
    """Film-like grade of a float RGB array 0..1; returns a PIL image."""
    a = np.asarray(arr, np.float32)
    if blur:
        a = blur_arr(a, blur)
    if mono:
        y = a[..., 0] * 0.3 + a[..., 1] * 0.59 + a[..., 2] * 0.11
        a = np.repeat(y[..., None], 3, -1)
    if sat != 1.0 and not mono:
        y = (a[..., 0] * 0.3 + a[..., 1] * 0.59 + a[..., 2] * 0.11)[..., None]
        a = y + (a - y) * sat
    a = np.clip(a * gain, 0, 1)
    if gamma != 1.0:
        a = a ** gamma
    if contrast != 1.0:
        a = np.clip(pivot + (a - pivot) * contrast, 0, 1)
        a = a * a * (3 - 2 * a) * 0.35 + a * 0.65  # gentle shoulder/toe
    if crush:
        a = np.clip((a - crush) / (1 - crush), 0, 1)
    if halation:
        y = a.mean(-1)
        hi = np.clip((y - 0.72) / 0.28, 0, 1)
        hb = blur_arr(hi, hal_r)
        a = np.clip(a + halation * hb[..., None] * np.asarray(hal_color, np.float32), 0, 1)
    if haze is not None:
        hc, ha = haze
        a = a * (1 - ha) + np.asarray(hc, np.float32) / 255 * ha
    if lift:
        a = lift + a * (1 - lift)
    if tone is not None:
        sm, hm = (np.asarray(c, np.float32) for c in tone)  # multiplicative tints for shadows / highlights
        y = a.mean(-1, keepdims=True)
        a = np.clip(a * (sm * (1 - y) + hm * y), 0, 1)
    h, w = a.shape[:2]
    if vignette:
        key = (w, h, vignette)
        if key not in _grain_cache:
            yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
            r = np.hypot((xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2))
            _grain_cache[key] = np.clip(1 - vignette * np.clip(r - 0.35, 0, None) ** 1.6, 0, 1)[..., None]
        a = a * _grain_cache[key]
    if grain:
        rs = np.random.RandomState(seed % 100000)
        gh, gw = int(h / grain_size) + 1, int(w / grain_size) + 1
        g = rs.normal(0, 1, (gh, gw)).astype(np.float32)
        g = np.asarray(Image.fromarray(np.clip(g * 40 + 128, 0, 255).astype(np.uint8), "L").resize((w, h), Image.BILINEAR), np.float32)
        g = (g - 128) / 40
        y = a.mean(-1, keepdims=True)
        a = a + grain * g[..., None] * (0.35 + 0.65 * (1 - np.abs(y - 0.5) * 1.6).clip(0.2, 1))
    return Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8), "RGB")


def to_arr(img):
    return np.asarray(img.convert("RGB"), np.float32) / 255


def put(ink, pil_img, xy=(0, 0)):
    """Paste a finished photographic image onto the frame and disable kit grain."""
    ink.img.paste(pil_img, (int(xy[0]), int(xy[1])))
    ink.d = ImageDraw.Draw(ink.img, "RGBA")
    ink._grain = False


# --------------------------------------------------- hand lettering -------
# A single-stroke capital alphabet for felt-pen lettering (unit box, y down).
_HAND = {
    "A": [[(0, 1), (0.35, 0), (0.7, 1)], [(0.14, 0.62), (0.56, 0.62)]],
    "B": [[(0, 0), (0, 1), (0.45, 1), (0.6, 0.85), (0.45, 0.52), (0, 0.5)], [(0, 0), (0.42, 0), (0.55, 0.15), (0.42, 0.48)]],
    "C": [[(0.65, 0.12), (0.45, 0), (0.15, 0.05), (0, 0.5), (0.15, 0.95), (0.45, 1), (0.65, 0.88)]],
    "D": [[(0, 0), (0, 1), (0.35, 1), (0.62, 0.75), (0.62, 0.25), (0.35, 0), (0, 0)]],
    "E": [[(0.6, 0), (0, 0), (0, 1), (0.6, 1)], [(0, 0.5), (0.45, 0.5)]],
    "F": [[(0.6, 0), (0, 0), (0, 1)], [(0, 0.5), (0.45, 0.5)]],
    "G": [[(0.65, 0.12), (0.45, 0), (0.15, 0.05), (0, 0.5), (0.15, 0.95), (0.45, 1), (0.65, 0.85), (0.65, 0.55), (0.4, 0.55)]],
    "H": [[(0, 0), (0, 1)], [(0.6, 0), (0.6, 1)], [(0, 0.5), (0.6, 0.5)]],
    "I": [[(0.1, 0), (0.1, 1)]],
    "J": [[(0.5, 0), (0.5, 0.8), (0.3, 1), (0.05, 0.85)]],
    "K": [[(0, 0), (0, 1)], [(0.6, 0), (0, 0.6)], [(0.2, 0.45), (0.62, 1)]],
    "L": [[(0, 0), (0, 1), (0.55, 1)]],
    "M": [[(0, 1), (0.05, 0), (0.4, 0.6), (0.75, 0), (0.8, 1)]],
    "N": [[(0, 1), (0, 0), (0.62, 1), (0.62, 0)]],
    "O": [[(0.35, 0), (0.05, 0.15), (0, 0.5), (0.1, 0.9), (0.35, 1), (0.62, 0.88), (0.7, 0.5), (0.6, 0.1), (0.35, 0)]],
    "P": [[(0, 1), (0, 0), (0.45, 0), (0.6, 0.15), (0.6, 0.35), (0.45, 0.5), (0, 0.5)]],
    "Q": [[(0.35, 0), (0.05, 0.15), (0, 0.5), (0.1, 0.9), (0.35, 1), (0.62, 0.88), (0.7, 0.5), (0.6, 0.1), (0.35, 0)], [(0.45, 0.75), (0.75, 1.05)]],
    "R": [[(0, 1), (0, 0), (0.45, 0), (0.6, 0.15), (0.6, 0.35), (0.45, 0.5), (0, 0.5)], [(0.25, 0.5), (0.62, 1)]],
    "S": [[(0.6, 0.12), (0.35, 0), (0.08, 0.1), (0.08, 0.38), (0.55, 0.6), (0.6, 0.88), (0.35, 1), (0, 0.9)]],
    "T": [[(0, 0), (0.7, 0)], [(0.35, 0), (0.35, 1)]],
    "U": [[(0, 0), (0, 0.8), (0.2, 1), (0.45, 1), (0.62, 0.8), (0.62, 0)]],
    "V": [[(0, 0), (0.35, 1), (0.7, 0)]],
    "W": [[(0, 0), (0.2, 1), (0.42, 0.35), (0.62, 1), (0.85, 0)]],
    "X": [[(0, 0), (0.62, 1)], [(0.62, 0), (0, 1)]],
    "Y": [[(0, 0), (0.33, 0.5), (0.66, 0)], [(0.33, 0.5), (0.33, 1)]],
    "Z": [[(0, 0), (0.62, 0), (0, 1), (0.65, 1)]],
    "0": [[(0.3, 0), (0.05, 0.2), (0.05, 0.8), (0.3, 1), (0.55, 0.8), (0.55, 0.2), (0.3, 0)]],
    "1": [[(0.1, 0.2), (0.3, 0), (0.3, 1)]],
    "2": [[(0.05, 0.2), (0.3, 0), (0.55, 0.15), (0.5, 0.45), (0, 1), (0.6, 1)]],
    "3": [[(0.05, 0.1), (0.3, 0), (0.55, 0.15), (0.5, 0.4), (0.25, 0.5), (0.55, 0.65), (0.55, 0.88), (0.3, 1), (0, 0.9)]],
    "4": [[(0.45, 1), (0.45, 0), (0, 0.7), (0.62, 0.7)]],
    "5": [[(0.55, 0), (0.1, 0), (0.05, 0.45), (0.35, 0.4), (0.58, 0.6), (0.5, 0.92), (0.25, 1), (0, 0.9)]],
    "6": [[(0.5, 0.05), (0.25, 0), (0.05, 0.4), (0.05, 0.8), (0.3, 1), (0.55, 0.8), (0.5, 0.55), (0.3, 0.48), (0.05, 0.6)]],
    "7": [[(0, 0), (0.6, 0), (0.2, 1)]],
    "8": [[(0.3, 0.5), (0.05, 0.3), (0.3, 0), (0.55, 0.3), (0.3, 0.5), (0.02, 0.75), (0.3, 1), (0.58, 0.75), (0.3, 0.5)]],
    "9": [[(0.55, 0.4), (0.3, 0.52), (0.05, 0.35), (0.25, 0), (0.55, 0.2), (0.5, 0.6), (0.3, 1)]],
    ".": [[(0.05, 0.95), (0.1, 1.0)]],
    "·": [[(0.05, 0.5), (0.1, 0.52)]],
    "-": [[(0.05, 0.5), (0.45, 0.5)]],
    "*": [[(0.25, 0.1), (0.25, 0.5)], [(0.05, 0.2), (0.45, 0.4)], [(0.45, 0.2), (0.05, 0.4)]],
    "'": [[(0.1, 0), (0.05, 0.25)]],
}


def hand_text(draw, x, y, s, size, color=(20, 18, 20), width=3, seed=1, spacing=0.3):
    """Felt-pen capitals with slight per-letter wobble. Returns end x."""
    rs = random.Random(seed)
    for ch in s.upper():
        if ch == " ":
            x += size * 0.55
            continue
        strokes = _HAND.get(ch)
        if strokes is None:
            x += size * 0.5
            continue
        sk = rs.uniform(-0.05, 0.05)
        sc = size * rs.uniform(0.94, 1.06)
        dy = rs.uniform(-0.04, 0.04) * size
        wmax = 0
        for st in strokes:
            pts = [(x + (px + sk * (1 - py)) * sc + rs.uniform(-0.6, 0.6), y + dy + py * sc + rs.uniform(-0.6, 0.6)) for px, py in st]
            if len(pts) == 2 and math.hypot(pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]) < 6:
                r = width * 0.8
                draw.ellipse([pts[0][0] - r, pts[0][1] - r, pts[0][0] + r, pts[0][1] + r], fill=color)
            else:
                draw.line(pts, fill=color, width=width, joint="curve")
            wmax = max(wmax, max(px for px, _ in st))
        x += (wmax + spacing) * sc
    return x


import random  # noqa: E402  (used by hand_text)


# ------------------------------------------------------- figures in relief --

SKIN = (222, 182, 152)


def face(R, cx, cy, s=1.0, skin=SKIN, hair=(78, 64, 52), look=(0.0, 0.0), turn=0.0, mouth=0.0, smile=0.0,
         eyes_open=1.0, fringe=1.0, hair_len=1.0, base=0.0, tex=None, cap=None, lips=(176, 104, 98), iris=(80, 60, 44),
         neck=True, collar=None):
    """A head in relief, about 300*s px tall, centred at (cx, cy). Built as one
    surface (skull + jaw) with features pushed in or raised on it, then painted.
    turn -1..1 slides the features sideways (head turned)."""
    W_, H_ = R.w, R.h
    ox = 40 * s * turn
    if neck:
        R.capsule((cx + ox * 0.2, cy + 100 * s), (cx + ox * 0.1, cy + 230 * s), 66 * s, 74 * s, depth=0.7, base=base - 40 * s, color=mix_color(skin, (120, 80, 70), 0.15))
        if collar is not None:
            R.slab([(cx - 440 * s, cy + 520 * s), (cx - 330 * s, cy + 270 * s), (cx - 150 * s, cy + 215 * s), (cx - 60 * s, cy + 195 * s), (cx, cy + 290 * s),
                    (cx + 60 * s, cy + 195 * s), (cx + 150 * s, cy + 215 * s), (cx + 330 * s, cy + 270 * s), (cx + 440 * s, cy + 520 * s)],
                   height=90 * s, bevel=40 * s, base=base - 20 * s, color=collar, gloss=0.08)
            R.slab([(cx - 75 * s, cy + 190 * s), (cx, cy + 300 * s), (cx - 10 * s, cy + 320 * s), (cx - 120 * s, cy + 240 * s)], height=14 * s, bevel=4 * s, base=base + 70 * s, color=collar)
            R.slab([(cx + 75 * s, cy + 190 * s), (cx, cy + 300 * s), (cx + 10 * s, cy + 320 * s), (cx + 120 * s, cy + 240 * s)], height=14 * s, bevel=4 * s, base=base + 70 * s, color=collar)
    R.ellipsoid(cx, cy - 10 * s, 112 * s, 140 * s, depth=110 * s, base=base, color=skin, gloss=0.12)
    R.ellipsoid(cx + ox * 0.3, cy + 62 * s, 84 * s, 82 * s, depth=96 * s, base=base, color=skin, gloss=0.12)
    for side in (-1, 1):
        ear_x = cx - side * 106 * s * (1 - 0.5 * max(0, side * turn))
        R.ellipsoid(ear_x, cy + 4 * s, 15 * s, 30 * s, depth=18 * s, base=base + 20 * s, color=mix_color(skin, (170, 100, 90), 0.2))
    fx = cx + ox
    R.bump(fx, cy - 52 * s, 80 * s, 20 * s, 8 * s, soft=True)                     # brow
    for side in (-1, 1):
        R.bump(fx + side * 54 * s, cy + 34 * s, 36 * s, 28 * s, 9 * s + 6 * s * smile, soft=True)   # cheeks
        R.dent(fx + side * 44 * s, cy - 20 * s, 34 * s, 22 * s, 12 * s)            # sockets
    R.bump(fx + ox * 0.3, cy + 2 * s, 13 * s, 42 * s, 16 * s, soft=False)          # nose bridge
    R.bump(fx + ox * 0.35, cy + 32 * s, 20 * s, 14 * s, 12 * s, soft=True)         # nose tip
    for side in (-1, 1):
        R.bump(fx + ox * 0.3 + side * 15 * s, cy + 38 * s, 9 * s, 7 * s, 5 * s, soft=True)
    R.dent(fx + ox * 0.3, cy + 52 * s, 12 * s, 8 * s, 4 * s)                       # philtrum
    R.bump(fx, cy + 104 * s, 34 * s, 18 * s, 8 * s, soft=True)                     # chin
    yy, xx = np.mgrid[0:H_, 0:W_].astype(np.float32)
    # eyes (painted onto the socket floor)
    for side in (-1, 1):
        ex, ey = fx + side * 44 * s, cy - 18 * s
        ry = 11.5 * s * max(0.08, eyes_open)
        m = np.clip(1 - ((xx - ex) / (24 * s)) ** 2 - ((yy - ey) / ry) ** 2, 0, 1)
        m = np.clip(m * 6, 0, 1)
        R.paint(m, (228, 224, 216))
        if eyes_open > 0.25:
            ix, iy = ex + look[0] * 9 * s, ey + look[1] * 4 * s
            mi = np.clip(1 - ((xx - ix) ** 2 + (yy - iy) ** 2) / (9.5 * s) ** 2, 0, 1) * (m > 0.2)
            R.paint(np.clip(mi * 5, 0, 1), iris)
            mp = np.clip(1 - ((xx - ix) ** 2 + (yy - iy) ** 2) / (4.2 * s) ** 2, 0, 1) * (m > 0.2)
            R.paint(np.clip(mp * 5, 0, 1), (10, 8, 8))
            mh = np.clip(1 - ((xx - ix - 3 * s) ** 2 + (yy - iy + 3 * s) ** 2) / (2 * s) ** 2, 0, 1)
            R.paint(np.clip(mh * 4, 0, 1) * (m > 0.2), (250, 250, 250))
        R.bump(ex, ey - ry - 3 * s, 25 * s, 5 * s, 3 * s, soft=True, color=mix_color(skin, (120, 80, 70), 0.3), mix=0.5)  # lid crease
        # brow hair
        mb = np.clip(1 - ((xx - ex - side * 4 * s) / (27 * s)) ** 2 - ((yy - (ey - 30 * s + ((xx - ex) / (27 * s)) ** 2 * 4 * s)) / (5 * s)) ** 2, 0, 1)
        R.paint(np.clip(mb * 3, 0, 1), hair, 0.85)
    # mouth
    mw = 30 * s + 16 * s * smile
    my = cy + 74 * s - 4 * s * smile
    curve = lambda x: ((x - fx - ox * 0.3) / mw) ** 2 * (-10 * s * smile)
    ml = np.clip(1 - ((xx - fx - ox * 0.3) / mw) ** 2 - ((yy - my - curve(xx)) / (7 * s + 18 * s * mouth)) ** 2, 0, 1)
    R.bump(fx + ox * 0.3, my, mw, 8 * s, 4 * s, soft=True)
    R.paint(np.clip(ml * 4, 0, 1), lips, 0.8)
    if mouth > 0.12:
        mo = np.clip(1 - ((xx - fx - ox * 0.3) / (mw * 0.85)) ** 2 - ((yy - my - 2 * s - curve(xx)) / ((4 + 16 * mouth) * s)) ** 2, 0, 1)
        R.paint(np.clip(mo * 5, 0, 1), (50, 22, 22))
        if smile > 0.3:
            mt = mo * (yy < my - 2 * s + (4 + 16 * mouth) * s * 0.1 + curve(xx))
            R.paint(np.clip(mt * 6, 0, 1), (232, 226, 210))
    # hair: crescent over the skull + fringe, painted and raised
    hm = ellipse_mask(W_, H_, cx - ox * 0.1, cy - 66 * s, 120 * s, 98 * s, blur=2 * s)
    face_m = ellipse_mask(W_, H_, fx, cy + 26 * s - 6 * s * fringe, 102 * s, 128 * s - 12 * s * fringe, blur=6 * s)
    hm = np.clip(hm - face_m, 0, 1)
    if hair_len > 1.0:
        for side in (-1, 1):
            hm = np.maximum(hm, ellipse_mask(W_, H_, cx + side * 104 * s, cy + 50 * s * hair_len, 34 * s, 100 * s * hair_len * 0.7, blur=3 * s) * (1 - face_m))
    t = tex if tex is not None else 1.0
    R.z += hm * 18 * s * R.hit
    hc = np.asarray(hair, np.float32) / 255
    k = hm[..., None]
    R.col = R.col * (1 - k) + (hc * (t[..., None] if isinstance(t, np.ndarray) else t)) * k
    R.gloss = R.gloss * (1 - hm) + 0.5 * hm
    if cap is not None:
        R.ellipsoid(cx, cy - 112 * s, 126 * s, 54 * s, depth=40 * s, base=base + 100 * s, color=cap, gloss=0.2)
        R.ellipsoid(cx + 40 * s, cy - 74 * s, 120 * s, 18 * s, depth=10 * s, base=base + 128 * s, color=cap, gloss=0.2)


def hair_tex(w, h, seed=0, angle_stretch=8):
    """Streaky hair texture (multiplier ~0.6..1.2)."""
    rs = np.random.RandomState(seed)
    g = rs.rand(h // angle_stretch + 2, w // 2 + 2).astype(np.float32)
    im = Image.fromarray((g * 255).astype(np.uint8), "L").resize((w, h), Image.BICUBIC)
    return 0.6 + 0.6 * np.asarray(im, np.float32) / 255


def person(R, x, y, hgt=300, phase=0.0, pose="stand", facing=1, coat=(60, 60, 64), trousers=(40, 40, 44), skin=SKIN,
           hair=(40, 30, 24), base=0.0, hat=None, arm=None, gloss=0.15, child=False):
    """A full figure in relief, feet at (x, y). Shaded volumes, no outlines."""
    s = hgt / 300.0
    hip = (x, y - 150 * s)
    sh_y = y - 250 * s
    headr = (24 if not child else 28) * s
    swing = math.sin(2 * math.pi * phase) * (0.45 if pose == "walk" else 0.8 if pose == "run" else 0.0)
    # legs
    for k, sg in enumerate((1, -1)):
        th = swing * sg
        knee = (hip[0] + math.sin(th) * 75 * s * facing, hip[1] + math.cos(th) * 75 * s)
        bend = max(0, -math.sin(2 * math.pi * phase) * sg) * (0.6 if pose != "stand" else 0) + 0.05
        if pose == "sit":
            knee = (hip[0] + 70 * s * facing, hip[1] + 4 * s)
            foot = (knee[0] + 4 * facing * s, y)
        else:
            foot = (knee[0] + math.sin(th - bend) * 72 * s * facing, knee[1] + math.cos(th - bend) * 72 * s)
        b = base + (0 if k == 0 else 4)
        R.capsule(hip, knee, 17 * s, 14 * s, base=b, color=trousers, gloss=gloss)
        R.capsule(knee, foot, 14 * s, 11 * s, base=b, color=trousers, gloss=gloss)
        R.ellipsoid(foot[0] + 10 * s * facing, foot[1] - 4 * s, 18 * s, 8 * s, base=b + 6, color=(24, 22, 22), gloss=0.5)
    # torso (coat)
    R.capsule((x, sh_y + 20 * s), hip, 40 * s, 44 * s, depth=0.8, base=base + 10, color=coat, gloss=gloss)
    R.ellipsoid(x, hip[1] + 14 * s, 46 * s, 36 * s, depth=26 * s, base=base + 8, color=coat, gloss=gloss)
    R.capsule((x - 30 * s, sh_y + 10 * s), (x + 30 * s, sh_y + 10 * s), 20 * s, base=base + 12, color=coat, gloss=gloss)
    # arms
    if pose == "reach":
        arms = [math.radians(arm if arm is not None else 80), -0.1]
    elif pose == "sit":
        arms = [math.radians(arm if arm is not None else 30), 0.3]
    else:
        arms = [-swing * 1.1, swing * 1.1]
    hands = []
    for k, th in enumerate(arms):
        shp = (x + (26 if k == 0 else -26) * s * facing, sh_y + 12 * s)
        el = (shp[0] + math.sin(th) * 62 * s * facing, shp[1] + math.cos(th) * 62 * s)
        hd = (el[0] + math.sin(th * 1.1 + (0.4 if pose == "run" else 0)) * 58 * s * facing, el[1] + math.cos(th * 1.1) * 58 * s)
        b = base + (30 if k == 0 else 2)
        R.capsule(shp, el, 13 * s, 11 * s, base=b, color=coat, gloss=gloss)
        R.capsule(el, hd, 11 * s, 9 * s, base=b, color=coat, gloss=gloss)
        R.ellipsoid(hd[0], hd[1] + 4 * s, 10 * s, 12 * s, base=b + 4, color=skin, gloss=0.2)
        hands.append(hd)
    # neck and head
    R.capsule((x, sh_y + 4 * s), (x + 2 * s * facing, sh_y - 20 * s), 11 * s, base=base + 14, color=skin)
    hx, hy = x + 4 * s * facing, sh_y - 20 * s - headr
    R.ellipsoid(hx, hy, headr * 0.88, headr, depth=headr, base=base + 16, color=skin, gloss=0.15)
    R.ellipsoid(hx + 6 * s * facing, hy - 2 * s, 5 * s, 5 * s, depth=4 * s, base=base + 16 + headr, color=skin)
    R.ellipsoid(hx - 5 * s * facing, hy - headr * 0.35, headr * 0.95, headr * 0.72, depth=headr * 0.8, base=base + 20, color=hair, gloss=0.3)
    if hat is not None:
        R.ellipsoid(hx, hy - headr * 0.75, headr * 1.6, headr * 0.25, depth=6 * s, base=base + 40, color=hat, gloss=0.2)
        R.ellipsoid(hx, hy - headr * 1.0, headr * 0.95, headr * 0.55, depth=headr * 0.6, base=base + 44, color=hat, gloss=0.2)
    return {"head": (hx, hy), "hands": hands, "hip": hip}


def subtitle(ink, s, alpha=1.0, y=None, size=26, color=(245, 245, 240), kind="serif"):
    """White film subtitle with a soft dark edge (no band)."""
    if alpha <= 0 or not s:
        return
    y = ink.h - 44 if y is None else y
    a = int(255 * alpha)
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (2, 2), (-2, 2), (2, -2), (-2, -2)):
        ink.text((ink.w / 2 + dx, y + dy), s, kind, size, (0, 0, 0), anchor="mm", alpha=int(a * 0.55))
    ink.text((ink.w / 2, y), s, kind, size, color, anchor="mm", alpha=a)

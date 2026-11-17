"""99 ways: the 'charcoal-card' medium kit (HANDMADE in code + one FORAGED ground).

- Ground: the teuf-teuf wall, i.e. the real rock of "Cueva de las manos - detalle.jpg" (Suzko, CC BY-SA 3.0,
  local copy films/sources/teuf-teuf/hands_cueva.jpg, decoded with PIL only), its plain upper-left rock
  (no painted figures) flattened to a pale wash exactly as teuf-teuf did (high-pass relief at low gain),
  mirror-tiled to the panel size, and printed through the teuf-teuf greenish-sepia ramp.
- Puppets: articulated grey-card puppets cut from the b1m2 control-point figures (agent, stranger) and scenery
  (desk, window, clock, cupboard, SERVICE door); every piece is a separate card with charcoal rubbed in
  (darker toward its cut edges), its own small drop shadow, and a brass split pin (brad) at the shoulder and
  elbow; a blown charcoal spray halo is laid on the wall round each figure before it is pinned up.
- Lettering: the shared pen hand (pen99), fattened and rubbed as charcoal for sound lettering.
All work is in luminance 0..1; tone() maps to RGB at the end."""
import math
import random
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/kit")
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import pen99  # noqa: E402
from pen99 import penlib  # noqa: E402
import b1m2 as B  # noqa: E402

ROOT = pen99.ROOT
CUEVA = ROOT / "films/sources/teuf-teuf/hands_cueva.jpg"

# the teuf-teuf reference ramp (films/swarm/teuf-teuf/layout_wall.py RAMP_L / RAMP_C), copied as data
RAMP_L = np.array([0.00, 0.12, 0.33, 0.68, 0.87, 0.94, 1.00], np.float32)
RAMP_C = np.array([[15, 17, 9], [43, 44, 31], [89, 90, 73], [179, 176, 152],
                   [223, 217, 188], [239, 232, 202], [251, 243, 213]], np.float32)


def tone(l):
    l = np.clip(l, 0, 1)
    out = np.empty(l.shape + (3,), np.float32)
    for c in range(3):
        out[..., c] = np.interp(l, RAMP_L, RAMP_C[:, c])
    return out


_ROCK = None


def rock_tile():
    """High-pass relief of the plain rock (upper-left of the photograph, above the painted guanacos)."""
    global _ROCK
    if _ROCK is None:
        a = np.asarray(Image.open(CUEVA).convert("RGB")).astype(np.float32) / 255.0
        L = cv2.cvtColor(a, cv2.COLOR_RGB2LAB)[..., 0]
        crop = L[0:215, 0:470]
        hp = cv2.GaussianBlur(crop, (0, 0), 1.2) - cv2.GaussianBlur(crop, (0, 0), 18)
        broad = cv2.GaussianBlur(crop, (0, 0), 18) - cv2.GaussianBlur(crop, (0, 0), 60)
        _ROCK = (hp / 100.0, broad / 100.0)
    return _ROCK


def wall(w, h, seed=0, level=0.885, hp_gain=0.55, broad_gain=0.35, scale=2.2):
    hp, br = rock_tile()
    t = hp * hp_gain + br * broad_gain
    t = np.vstack([t, t[::-1]])
    t = np.hstack([t, t[:, ::-1]])
    t = cv2.resize(t, (int(t.shape[1] * scale), int(t.shape[0] * scale)), interpolation=cv2.INTER_CUBIC)
    rnd = random.Random(seed)
    reps_y, reps_x = h // t.shape[0] + 2, w // t.shape[1] + 2
    big = np.tile(t, (reps_y, reps_x))
    oy, ox = rnd.randrange(0, t.shape[0]), rnd.randrange(0, t.shape[1])
    return (level + big[oy:oy + h, ox:ox + w]).astype(np.float32)


def grain(h, w, seed, sigma=0.9):
    rng = np.random.default_rng(seed)
    n = rng.standard_normal((h, w)).astype(np.float32)
    return cv2.GaussianBlur(n, (0, 0), sigma)


def spray(lum, m, seed, reach=26, strength=0.32):
    """Blown charcoal round a figure: dust falls off away from its cut edge, speckled."""
    if m.max() == 0:
        return
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * reach + 1,) * 2)
    d = cv2.GaussianBlur(cv2.dilate(m, k).astype(np.float32) / 255, (0, 0), reach * 0.7)
    rng = np.random.default_rng(seed)
    sp = (rng.random(m.shape) < 0.20).astype(np.float32)
    sp = cv2.GaussianBlur(sp, (0, 0), 0.8) * 2.2
    halo = np.clip(d, 0, 1) * (0.45 + 0.55 * np.clip(sp, 0, 1))
    lum *= (1 - strength * halo)


def drop(lum, m, off=(5, 6), blur=3.0, op=0.30):
    sh = np.zeros_like(m)
    dx, dy = off
    sh[dy:, dx:] = m[:m.shape[0] - dy, :m.shape[1] - dx]
    s = cv2.GaussianBlur(sh.astype(np.float32) / 255, (0, 0), blur) * op
    lum *= (1 - s)


def card_piece(lum, m, t, seed, edge=0.22, rub=0.06):
    """Lay one cut card piece of base tone t (0..1) with charcoal rubbed in, darker at its cut edges."""
    a = m.astype(np.float32) / 255
    if a.max() == 0:
        return
    d = cv2.distanceTransform((m > 127).astype(np.uint8), cv2.DIST_L2, 3)
    e = np.exp(-d / 7.0)
    g = grain(*m.shape, seed, 1.1)
    fib = grain(*m.shape, seed + 1, 3.5)
    val = t * (1 - edge * e) + rub * g * (0.5 + t) + 0.03 * fib
    lum[:] = lum * (1 - a) + np.clip(val, 0, 1) * a


ROLE_TONE = dict(trousers=0.20, waistcoat=0.12, shirt=0.62, tie=0.08, skin=0.50, hair=0.10, ear=0.44,
                 sleeve=0.62, garter=0.0, pencil=0.86, glass_in=0.50, sleeve_far=0.50, skin_far=0.40,
                 coat=0.26, collar=0.40, skin_s=0.55, hat=0.10, bow=0.70, glove=0.20, eye=0,
                 desk=0.30, window=0.24, clock=0.20, dial=0.92, hand=0.06, cupboard=0.28, door=0.40,
                 shelf=0.20, sdoor=0.34, lamp=0.20, chair=0.16)


def pin_up(lum, shapes, seed, tones=None, halo=True, halo_reach=24, halo_strength=0.30, piece_shadow=True):
    """Pin up a set of b1m2 Shapes as charcoal card pieces. Holes cut through to what lay beneath."""
    tones = dict(ROLE_TONE, **(tones or {}))
    h, w = lum.shape
    solid = [s for s in shapes if not s.hole]
    union = B.raster(solid, w, h, ss=1) if solid else np.zeros((h, w), np.uint8)
    if halo:
        spray(lum, union, seed, halo_reach, halo_strength)
    bg = lum.copy()
    drop(lum, union, (7, 9), 4.0, 0.30)
    pins = []
    for i, s in enumerate(sorted(shapes, key=lambda s: s.z)):
        m = B.raster([B.Shape(s.pts, s.role, smooth=s.smooth)], w, h, ss=2)
        if s.role == "pin":
            c = s.pts.mean(0)
            pins.append(c)
            continue
        if s.hole:
            a = m.astype(np.float32) / 255
            if s.role in ("inside", "pendwin"):
                lum[:] = lum * (1 - a) + 0.08 * a           # the dark inside
            elif s.role == "dial":
                card_piece(lum, m, 0.93, seed + i * 13, edge=0.08, rub=0.02)   # the pale dial card
            else:
                lum[:] = lum * (1 - a) + bg * a
            continue
        if piece_shadow:
            drop(lum, m, (3, 4), 2.0, 0.22)
        card_piece(lum, m, tones.get(s.role, 0.3), seed + i * 13)
    for c in pins:
        brad(lum, c[0], c[1], 7)
    return union


def brad(lum, x, y, r):
    """A split-pin head: small domed disc, rim dark, a highlight."""
    h, w = lum.shape
    yy, xx = np.mgrid[0:h, 0:w]
    x0, x1, y0, y1 = int(max(0, x - r - 4)), int(min(w, x + r + 5)), int(max(0, y - r - 4)), int(min(h, y + r + 5))
    if x1 <= x0 or y1 <= y0:
        return
    sx, sy = xx[y0:y1, x0:x1], yy[y0:y1, x0:x1]
    d = np.sqrt((sx - x) ** 2 + (sy - y) ** 2)
    a = np.clip(r + 0.5 - d, 0, 1)
    hl = np.exp(-((sx - x + r * 0.35) ** 2 + (sy - y + r * 0.35) ** 2) / (r * 0.5) ** 2)
    v = 0.55 - 0.25 * (d / r) + 0.4 * hl
    sub = lum[y0:y1, x0:x1]
    sub[:] = sub * (1 - a) + v * a


def rub_mask(m, seed, smear=(6, 3), keep=0.82):
    """A lettering/drawing mask as charcoal: broken by grain, with a finger smear."""
    a = m.astype(np.float32) / 255
    g = grain(*m.shape, seed, 0.8)
    a2 = a * np.clip(keep + 0.35 * g, 0, 1)
    sm = np.zeros_like(a)
    dx, dy = smear
    sm[dy:, dx:] = a[:a.shape[0] - dy, :a.shape[1] - dx]
    sm = cv2.GaussianBlur(sm, (0, 0), 4) * 0.22
    return np.clip(np.maximum(a2, sm), 0, 1)


def place(dst, m, cx, cy, deg=0.0):
    """Max-paste mask m centred on (cx, cy), rotated deg (clockwise)."""
    h, w = m.shape
    M = cv2.getRotationMatrix2D((w / 2, h / 2), -deg, 1.0)
    M[0, 2] += cx - w / 2
    M[1, 2] += cy - h / 2
    out = cv2.warpAffine(m, M, (dst.shape[1], dst.shape[0]), flags=cv2.INTER_LINEAR)
    np.maximum(dst, out, out=dst)
    return out


def sfx(lum, text, cx, cy, cap, seed, deg=0.0, weight=0.20, dark=0.07, fatten=0, halo=0.0, alpha=1.0):
    """Sound lettering: the pen hand, fattened, rubbed in charcoal; optional pale chalk knock-out."""
    m = pen99.letter([text], cap, seed, weight=weight)
    if fatten:
        m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * fatten + 1,) * 2))
    pm = np.zeros(lum.shape, np.uint8)
    place(pm, m, cx, cy, deg)
    if halo:
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(halo) * 2 + 1,) * 2)
        hm = cv2.GaussianBlur(cv2.dilate(pm, k), (0, 0), 1.5).astype(np.float32) / 255
        lum[:] = lum * (1 - hm) + 0.93 * hm
    a = rub_mask(pm, seed) * alpha
    lum[:] = lum * (1 - a) + dark * a
    return pm


def charcoal_line(lum, pts, w, seed, dark=0.08, tremor=1.0, alpha=1.0):
    m = np.zeros(lum.shape, np.uint8)
    penlib.brush_line(m, pts, w, seed, tremor)
    a = rub_mask(m, seed, smear=(3, 2), keep=0.9) * alpha
    lum[:] = lum * (1 - a) + dark * a
    return m


def balloon_card(lum, rx, ry, centre, tip, seed, paper=0.965, tail_w=0.30, bend=0.10):
    """A wordless cut-card balloon: the shared balloon outline (penlib.balloon_piece) with no letters."""
    cap = 40
    # size the empty balloon by a run of spaces in the pen hand (advance of ' ' * cap)
    adv = penlib.GLYPHS[" "][0] * cap + cap * 0.1
    n = max(1, int(round((rx - cap * 0.35) / 1.18 * 2 / adv)))
    lines = [" " * n] * max(1, int(round(((ry - cap * 0.30) / 1.10 * 2) / (cap * 1.42))))
    b = penlib.balloon_piece(lines, cap, (tip[0] - centre[0], tip[1] - centre[1]), seed, tail_w=tail_w, bend=bend)
    h, w = lum.shape
    cx, cy = b["center"]
    ox, oy = int(round(centre[0] - cx)), int(round(centre[1] - cy))

    def put(m):
        out = np.zeros((h, w), np.uint8)
        Hc, Wc = m.shape
        ys, xs = max(0, oy), max(0, ox)
        ye, xe = min(h, oy + Hc), min(w, ox + Wc)
        if ye > ys and xe > xs:
            out[ys:ye, xs:xe] = m[ys - oy:ye - oy, xs - ox:xe - ox]
        return out
    pm, im = put(b["paper"]), put(b["ink"])
    drop(lum, pm, (5, 7), 3.5, 0.32)
    card_piece(lum, pm, paper, seed, edge=0.05, rub=0.02)
    a = rub_mask(im, seed + 3, smear=(2, 2), keep=0.92)
    lum[:] = lum * (1 - a) + 0.08 * a
    ys, xs = np.nonzero(pm)
    return (xs.min(), ys.min(), xs.max(), ys.max())


def rhythm(lum, x0, xc_y, syl, seed, unit=46, amp=40, thick=(13, 20), gap=20, fade_from=None):
    """Draw the voice of a line with no words: one charcoal dash per syllable, set at its pitch,
    stressed syllables longer and heavier; ('|', w) is a pause, ('glyph', s, cap) a pen-hand mark.
    Returns the x after the last mark."""
    x = x0
    rnd = random.Random(seed)
    k = 0
    for it in syl:
        if it[0] == "|":
            x += it[1]
            continue
        if it[0] == "g":
            s, cap, dy = it[1], it[2], (it[3] if len(it) > 3 else 0)
            m = pen99.letter([s], cap, seed + 50 + k, weight=0.16)
            pm = np.zeros(lum.shape, np.uint8)
            mh, mw = m.shape
            place(pm, m, x + mw / 2 - cap * 0.5, xc_y + dy + cap * 0.12)
            a = rub_mask(pm, seed + 60 + k)
            lum[:] = lum * (1 - a) + 0.07 * a
            x += mw - cap * 0.9
            k += 1
            continue
        pitch, stress = it
        L = unit * (1.35 if stress else 0.85)
        y = xc_y - pitch * amp
        w = thick[1] if stress else thick[0]
        al = 1.0
        if fade_from is not None and k >= fade_from:
            al = max(0.35, 1.0 - 0.18 * (k - fade_from + 1))
        charcoal_line(lum, [(x, y + rnd.uniform(-2, 2)), (x + L * 0.5, y - pitch * 4 + rnd.uniform(-2, 2)),
                            (x + L, y - pitch * 8)], w, seed + k * 7, alpha=al)
        x += L + gap
        k += 1
    return x


def panel_rgb(lum):
    return tone(lum)


def speech(lum, syl, centre, tip, seed, unit=34, amp=40, thick=(11, 17), gap=12, ry=84, fade_from=None, pad=58):
    """A wordless balloon sized to the rhythm it carries."""
    dummy = np.zeros_like(lum)
    x_end = rhythm(dummy, 0, lum.shape[0] // 2, syl, seed, unit, amp, thick, gap, fade_from)
    wdt = x_end
    box = balloon_card(lum, wdt / 2 + pad, ry, centre, tip, seed)
    rhythm(lum, centre[0] - wdt / 2 + 6, centre[1] + 8, syl, seed, unit, amp, thick, gap, fade_from)
    return box

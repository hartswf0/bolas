"""99 ways, page 20 "Across the tracks" (point of view; medium: charcoal-card).
Seen from the far platform: the station a small lit box beyond two tracks, the figures tiny in its windows,
the balloons long-tailed across the rails toward us. Every panel keeps the same far eye: our own platform edge
at the foot of the frame, the rails between, the station small in the middle distance.
Charcoal-card kit (charcoal99.py): grey card pieces rubbed with charcoal, a blown spray, the teuf-teuf rock wall
as the sky's grain. Interior figures are the b1m2 cut agent and scenery at 0.14 scale seen through lit windows;
the stranger is a small back-view card puppet made here (she stands outside on the platform, facing the glass).
Run: python3 -I p20_across_the_tracks.py"""
import math
import random
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import charcoal99 as C  # noqa: E402
import b1m2 as B  # noqa: E402
from b1m2 import agent, desk, clock, cupboard, service_door, Shape, R_, circle_pts  # noqa: E402
import pen99  # noqa: E402
from pen99 import penlib  # noqa: E402

N, PID, TITLE = 20, "across-the-tracks", "Across the tracks"
W, H = 2200, 2850
BOXES = [(110, 110, 2090, 810),
         (110, 850, 1080, 1450), (1120, 850, 2090, 1450),
         (110, 1490, 1080, 2090), (1120, 1490, 2090, 2090),
         (110, 2130, 1080, 2730), (1120, 2130, 2090, 2730)]
S_IN = 0.14          # interior figure scale
SOFT = 0.95

LINES = {"q": ["Pardon me —", "have you the right time?"], "a": ["Ten past four,", "by the clock."],
         "t": ["Much obliged!"], "f": ["Well, here I am...", "and what for?"]}
CAPS = ["From the far platform, across the tracks: Randolph station, a September afternoon. "
        "In the lit office the agent reads his memo.",
        "4:09. He gets up and crosses the office.",
        "A lady at the ticket window stops him.",
        "He looks up at the office clock.",
        "She goes off down the platform.",
        "Cupboard open: the key on its hook.",
        "The SERVICE door stays shut."]


# ------------------------------------------------------------------ the card kit for this page
# Every card is rubbed with the foraged rock (the teuf-teuf Cueva de las manos plain-rock relief, charcoal99.rock_tile,
# CC BY-SA 3.0, Suzko) sampled at its own offset and scale, then worked over with charcoal hatching (broken parallel
# strokes, heavier toward the cut edges and in patches; on dark cards the strokes are lifted, like an eraser), cut
# with scissor facets or torn (ragged edge with a pale fibrous rim), and dropped with its own shadow.
_RT = {}


def rock_patch(h, w, seed, scale=None):
    rnd = random.Random(seed * 7 + 3)
    sc = scale or rnd.uniform(0.9, 1.6)
    key = round(sc, 1)
    if key not in _RT:
        hp, br = C.rock_tile()
        t = hp + br * 0.6
        t = np.vstack([t, t[::-1]])
        t = np.hstack([t, t[:, ::-1]])
        _RT[key] = cv2.resize(t, (int(t.shape[1] * key), int(t.shape[0] * key)), interpolation=cv2.INTER_CUBIC)
    t = _RT[key]
    if rnd.random() < 0.5:
        t = t.T
    ry, rx = h // t.shape[0] + 2, w // t.shape[1] + 2
    big = np.tile(t, (ry, rx))
    oy, ox = rnd.randrange(0, t.shape[0]), rnd.randrange(0, t.shape[1])
    return big[oy:oy + h, ox:ox + w].astype(np.float32)


def lowf(h, w, seed, sigma):
    g = C.grain(h, w, seed, sigma)
    return g / (g.std() + 1e-6)


def hatch_field(h, w, seed, spacing=None, angle=None):
    """Charcoal hatching: broken parallel strokes at a hand-chosen angle (0..1 stroke strength)."""
    rnd = random.Random(seed * 13 + 1)
    th = math.radians(angle if angle is not None else rnd.choice([38, 46, 54, 128, 136, 144]) + rnd.uniform(-5, 5))
    sp = spacing or rnd.uniform(5.5, 8.0)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    ph = (xx * math.cos(th) + yy * math.sin(th)) / sp * 2 * math.pi + 1.2 * lowf(h, w, seed + 2, 9)
    stroke = np.clip((np.sin(ph) - 0.45) / 0.55, 0, 1)
    brk = np.clip(0.45 + 0.9 * lowf(h, w, seed + 3, 2.2), 0, 1)
    return stroke * brk


def bbox(m, pad=6):
    ys, xs = np.nonzero(m)
    if len(ys) == 0:
        return None
    H_, W_ = m.shape
    return max(0, ys.min() - pad), min(H_, ys.max() + pad + 1), max(0, xs.min() - pad), min(W_, xs.max() + pad + 1)


def tear(m, seed, amp=3.2):
    """Tear a card: a ragged, fibrous edge in place of the clean cut."""
    bb = bbox(m, 10)
    if bb is None:
        return m
    y0, y1, x0, x1 = bb
    sub = cv2.GaussianBlur(m[y0:y1, x0:x1].astype(np.float32) / 255, (0, 0), 1.6)
    h, w = sub.shape
    n = 0.10 * lowf(h, w, seed, 2.0) + 0.06 * lowf(h, w, seed + 1, 0.8)
    out = m.copy()
    out[y0:y1, x0:x1] = ((sub + n * amp / 3.2) > 0.5).astype(np.uint8) * 255
    return out


def card_k(lum, m, t, seed, edge=0.22, rub=0.06, hatch=None, torn=False, rock=1.0):
    """Lay one card of base tone t: rock-rubbed, charcoal-hatched, darker at its cut edges, torn rim if torn."""
    bb = bbox(m)
    if bb is None:
        return
    y0, y1, x0, x1 = bb
    mm = m[y0:y1, x0:x1]
    a = mm.astype(np.float32) / 255
    h, w = mm.shape
    d = cv2.distanceTransform((mm > 127).astype(np.uint8), cv2.DIST_L2, 3)
    e = np.exp(-d / 6.0)
    rk = rock_patch(h, w, seed)
    g = C.grain(h, w, seed, 1.7)
    val = t * (1 - edge * e) + rock * 1.15 * rk * (0.45 + t) + rub * 0.5 * g * (0.5 + t)
    hk = (0.13 if t < 0.9 else 0.035) if hatch is None else hatch
    if hk > 0:
        hf = hatch_field(h, w, seed + 11)
        patch = np.clip(0.30 + 0.70 * e + 0.45 * lowf(h, w, seed + 12, 14), 0, 1)
        if t < 0.3:
            val += hk * 0.9 * hf * patch                       # lifted strokes on a dark card
        else:
            val -= hk * hf * patch * (0.6 + 0.4 * t)
    if torn:
        fr = ((d > 0) & (d < 2.4)).astype(np.float32) * np.clip(0.6 + 0.6 * lowf(h, w, seed + 13, 0.9), 0, 1)
        val = val * (1 - 0.75 * fr) + 0.90 * 0.75 * fr
    sub = lum[y0:y1, x0:x1]
    sub[:] = sub * (1 - a) + np.clip(val, 0, 1) * a


C.card_piece = card_k      # this page only: the figures pinned by charcoal99.pin_up get the same rubbed cards


def scissor_poly(pts, seed, jog=1.4, step=16):
    """Hand-cut outline: each straight edge cut in short scissor strokes that wander a little."""
    rnd = random.Random(seed)
    out = []
    P_ = list(pts)
    for i in range(len(P_)):
        p0, p1 = np.array(P_[i], float), np.array(P_[(i + 1) % len(P_)], float)
        L = np.linalg.norm(p1 - p0)
        n = max(1, int(L / step))
        nrm = np.array([-(p1 - p0)[1], (p1 - p0)[0]]) / (L + 1e-6)
        for k in range(n):
            q = p0 + (p1 - p0) * k / n
            out.append(tuple(q + nrm * (rnd.uniform(-jog, jog) if k else 0)))
    return out


def strip(lum, x0, y0, x1, y1, t, seed, edge=0.18, torn=False, hatch=None, shadow=True):
    return poly(lum, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], t, seed, edge=edge, torn=torn, hatch=hatch, shadow=shadow)


def poly(lum, pts, t, seed, edge=0.2, shadow=True, torn=False, hatch=None, cut=True, rock=1.0):
    m = np.zeros(lum.shape, np.uint8)
    pp = scissor_poly(pts, seed) if cut and not torn else pts
    cv2.fillPoly(m, [np.int32(np.array(pp) * 4)], 255, cv2.LINE_AA, shift=2)
    if torn:
        m = tear(m, seed)
    if shadow:
        C.drop(lum, m, (4, 5), 2.5, 0.28)
    card_k(lum, m, t, seed, edge=edge, rub=0.035, hatch=hatch, torn=torn, rock=rock)
    return m


def tree_card(lum, x, base, kind, size, seed, t):
    """A hand-cut tree: a round lobed crown, a tall poplar, a tiered fir or a low bush, each its own outline."""
    rnd = random.Random(seed)
    h, w = lum.shape
    m = np.zeros((h, w), np.uint8)
    if kind == "round":
        cy = base - size * 1.25
        for k in range(rnd.randint(6, 9)):
            a_ = rnd.uniform(0, 2 * math.pi)
            rr = size * rnd.uniform(0.0, 0.55)
            r_ = size * rnd.uniform(0.38, 0.62)
            cv2.circle(m, (int(x + rr * math.cos(a_) * 1.2), int(cy + rr * math.sin(a_) * 0.8)), int(r_), 255, -1)
        trunk = [(x - size * 0.09, cy + size * 0.3), (x + size * 0.08, cy + size * 0.3), (x + size * 0.12, base), (x - size * 0.13, base)]
    elif kind == "poplar":
        hgt = size * rnd.uniform(3.0, 3.8)
        pts = []
        n = 9
        for k in range(n + 1):
            f = k / n
            wdt = size * 0.42 * math.sin(math.pi * min(1, f * 1.15)) ** 0.7 * rnd.uniform(0.75, 1.15)
            pts.append((x + wdt, base - size * 0.3 - hgt * f))
        left = []
        for k in range(n, -1, -1):
            f = k / n
            wdt = size * 0.42 * math.sin(math.pi * min(1, f * 1.15)) ** 0.7 * rnd.uniform(0.75, 1.15)
            left.append((x - wdt, base - size * 0.3 - hgt * f))
        cv2.fillPoly(m, [np.int32(pts + left)], 255)
        trunk = [(x - size * 0.06, base - size * 0.5), (x + size * 0.06, base - size * 0.5), (x + size * 0.08, base), (x - size * 0.08, base)]
    elif kind == "fir":
        tiers = rnd.randint(3, 5)
        hgt = size * rnd.uniform(2.2, 2.9)
        for k in range(tiers):
            f0 = k / tiers
            yb = base - size * 0.35 - hgt * f0 * 0.82
            wd = size * (0.95 - 0.6 * f0) * rnd.uniform(0.9, 1.1)
            cv2.fillPoly(m, [np.int32([(x - wd, yb), (x + wd, yb + rnd.uniform(-4, 4)), (x + rnd.uniform(-3, 3), yb - hgt * 0.42)])], 255)
        trunk = [(x - size * 0.07, base - size * 0.4), (x + size * 0.07, base - size * 0.4), (x + size * 0.09, base), (x - size * 0.09, base)]
    else:   # bush
        for k in range(rnd.randint(4, 6)):
            cv2.circle(m, (int(x + rnd.uniform(-1, 1) * size * 0.8), int(base - size * rnd.uniform(0.25, 0.5))),
                       int(size * rnd.uniform(0.3, 0.5)), 255, -1)
        m[int(base):, :] = 0
        trunk = None
    # re-cut the crown's outline as straight scissor facets (approxPolyDP), so it reads as cut card, not a blob
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if trunk is not None:
        poly(lum, trunk, max(0.10, t - 0.22), seed + 1, edge=0.15)
    if cs:
        cnt = max(cs, key=cv2.contourArea)
        ap = cv2.approxPolyDP(cnt, max(1.5, size * 0.06), True)[:, 0, :].astype(float)
        poly(lum, [tuple(p) for p in ap], t, seed + 2, edge=0.18, torn=(kind == "bush"), cut=False)


def lady_back(cx, foot, h=100, walk=0.0, face=0):
    """A small back-view card puppet of the stranger: hat, head, coat, skirt, two legs. face=0 back view,
    face=-1 walking away to the left (profile: brim forward, legs apart)."""
    s = h / 100.0
    out = []
    lx = 5 * s if face == 0 else 9 * s
    for k, d in enumerate((-1, 1)):
        off = d * (lx + walk * 10 * s)
        out.append(Shape([(cx + off - 3 * s, foot - 26 * s), (cx + off + 3 * s, foot - 26 * s), (cx + off + 3.5 * s, foot),
                          (cx + off - 4 * s, foot)], "trousers", smooth=False, z=-1))
        out.append(Shape([(cx + off - 5 * s, foot - 3 * s), (cx + off + (2 if face == 0 else -7) * s, foot - 3 * s),
                          (cx + off + (5 if face == 0 else 1) * s, foot + 1), (cx + off - 6 * s, foot + 1)], "hair", smooth=False, z=-1))
    out.append(Shape([(cx - 13 * s, foot - 60 * s), (cx + 13 * s, foot - 60 * s), (cx + 19 * s, foot - 24 * s),
                      (cx - 19 * s, foot - 24 * s)], "coat", smooth=False))
    out.append(Shape([(cx - 14 * s, foot - 86 * s), (cx - 4 * s, foot - 90 * s), (cx + 4 * s, foot - 90 * s), (cx + 14 * s, foot - 86 * s),
                      (cx + 16 * s, foot - 56 * s), (cx - 16 * s, foot - 56 * s)], "coat", z=1))
    out.append(Shape(circle_pts(cx + (0 if face == 0 else -2 * s), foot - 95 * s, 7.5 * s, 12), "skin_s", z=2))
    bx = cx + (0 if face == 0 else -4 * s)
    out.append(Shape([(bx - 14 * s, foot - 97 * s), (bx + 14 * s, foot - 97 * s), (bx + 10 * s, foot - 101 * s),
                      (bx + 7 * s, foot - 110 * s), (bx - 7 * s, foot - 110 * s), (bx - 10 * s, foot - 101 * s)], "hat", z=3))
    return out


def ballast(lum, y0, y1, seed):
    h, w = lum.shape
    g = C.grain(h, w, seed, 1.4)
    yy = np.arange(h)[:, None].astype(np.float32)
    band = ((yy >= y0) & (yy < y1)).astype(np.float32)
    band = cv2.GaussianBlur(band, (0, 0), 1.5)
    val = 0.40 + 0.03 * g + 1.1 * rock_patch(h, w, seed + 1, 1.0) - 0.08 * hatch_field(h, w, seed + 2, 6.5, 172)
    # stones: charcoal dabs and lifted flecks
    rnd = random.Random(seed)
    st = np.zeros((h, w), np.float32)
    for _ in range(int(w * max(0, y1 - y0) / 600)):
        sx_, sy_ = rnd.uniform(0, w), rnd.uniform(y0, y1)
        cv2.ellipse(st, (int(sx_), int(sy_)), (rnd.randint(2, 4), rnd.randint(1, 3)), rnd.uniform(0, 180), 0, 360,
                    rnd.choice((-1.0, 1.0)), -1)
    val += 0.07 * st
    lum[:] = lum * (1 - band) + np.clip(val, 0, 1) * band


def track(lum, y_far, y_near, seed, x0=0, x1=None, gauge_w=(5, 9)):
    """One track seen straight across: sleepers as short dark cards running toward us, two rails along."""
    h, w = lum.shape
    x1 = w if x1 is None else x1
    rnd = random.Random(seed)
    step = 22 + (y_near - y_far) * 0.18
    x = x0 - rnd.uniform(0, step)
    sl = np.zeros((h, w), np.uint8)
    while x < x1 + step:
        top, bot = y_far - 4, y_near + 6
        dx = rnd.uniform(-1.5, 1.5)
        cv2.fillPoly(sl, [np.int32(np.array([(x, top), (x + step * 0.42, top), (x + step * 0.48 + dx, bot),
                                             (x - step * 0.04 + dx, bot)]) * 4)], 255, cv2.LINE_AA, shift=2)
        x += step
    C.drop(lum, sl, (2, 3), 1.5, 0.25)
    C.card_piece(lum, sl, 0.22, seed + 1, edge=0.15, rub=0.03)
    for k, (yy, ww) in enumerate(((y_far, gauge_w[0]), (y_near, gauge_w[1]))):
        m = np.zeros((h, w), np.uint8)
        cv2.fillPoly(m, [np.int32(np.array([(x0, yy - ww), (x1, yy - ww), (x1, yy + ww * 0.6), (x0, yy + ww * 0.6)]) * 4)],
                     255, cv2.LINE_AA, shift=2)
        C.drop(lum, m, (0, 3), 1.6, 0.35)
        C.card_piece(lum, m, 0.16, seed + 3 + k, edge=0.1, rub=0.03)
        hl = np.zeros((h, w), np.uint8)
        cv2.line(hl, (x0, int(yy - ww + 1)), (x1, int(yy - ww + 1)), 255, max(1, int(ww * 0.35)), cv2.LINE_AA)
        a = C.rub_mask(hl, seed + 5 + k, smear=(1, 1), keep=0.75)
        lum[:] = lum * (1 - 0.8 * a) + 0.86 * 0.8 * a


def lettered_balloon(lum, lines, cap, centre, tip, seed, tail_w=0.16, bend=0.06):
    b = penlib.balloon_piece([pen99.clean(l) for l in lines], cap, (tip[0] - centre[0], tip[1] - centre[1]), seed,
                             tail_w=tail_w, bend=bend)
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
    C.drop(lum, pm, (5, 7), 3.5, 0.32)
    card_k(lum, pm, 0.965, seed, edge=0.04, rub=0.015, hatch=0.02, rock=0.45)
    a = C.rub_mask(im, seed + 3, smear=(1, 1), keep=0.97)
    lum[:] = lum * (1 - a) + 0.06 * a


def caption_card(lum, text, x, y, maxw, seed, cap=36):
    lines = B.wrap(text, cap, maxw)
    m = B.letter_left(lines, cap, seed)
    mh, mw = m.shape
    bw, bh = mw + int(cap * 0.1), mh + int(cap * 0.1)
    pts = [(x, y), (x + bw, y + 2), (x + bw - 2, y + bh), (x + 1, y + bh - 1)]
    cm = poly(lum, pts, 0.95, seed + 1, edge=0.05, hatch=0.02, rock=0.45, torn=True)
    lm = np.zeros(lum.shape, np.uint8)
    B.blit_mask(lm, m, int(x + cap * 0.55 - cap * 0.5 + 6), int(y + 4))
    a = C.rub_mask(lm, seed + 2, smear=(1, 1), keep=0.97)
    lum[:] = lum * (1 - a) + 0.07 * a
    return bh


# ------------------------------------------------------------------ the far view
def scene(w, h, beat, seed, sx=None, foreground=False):
    """beat: dict(agent=dict(...)|None, where='W1'|'W2'|'W3', lady=dict|None, cup=deg, key=bool)."""
    sx = w * 0.5 if sx is None else sx
    by = int(h * 0.60)                # station platform level
    lum = C.wall(w, h, seed, level=0.80, hp_gain=0.55, broad_gain=0.45, scale=1.6)
    yy = np.arange(h)[:, None].astype(np.float32)
    # the sky rubbed in charcoal: long broken strokes, heavier in patches high up (no smooth gradient)
    sk = hatch_field(h, w, seed + 5, 9.0, 174) * np.clip(0.25 + 0.5 * lowf(h, w, seed + 6, 40), 0, 1)
    lum -= 0.10 * sk * np.clip(1.3 - yy / by, 0, 1)
    # distant hills and trees (cards, pale -> far)
    rnd = random.Random(seed)
    hill = [(0, by - 95)]
    for k in range(9):
        hill.append((w * (k + 0.5) / 9, by - 120 - 70 * math.sin(k * 0.9 + seed % 7) ** 2 - rnd.uniform(0, 30)))
    hill += [(w, by - 100), (w, by + 10), (0, by + 10)]
    poly(lum, hill, 0.62, seed + 1, edge=0.10, shadow=True, torn=True)
    # a second, nearer torn ridge, darker
    hill2 = [(0, by - 40)]
    for k in range(13):
        hill2.append((w * (k + 0.5) / 13, by - 52 - 30 * math.sin(k * 1.3 + seed % 5) ** 2 - rnd.uniform(0, 14)))
    hill2 += [(w, by - 44), (w, by + 10), (0, by + 10)]
    poly(lum, hill2, 0.52, seed + 2, edge=0.12, shadow=True, torn=True)
    kinds = ["round", "poplar", "fir", "bush", "round", "poplar", "round", "fir"]
    tx = rnd.uniform(-20, 40)
    k = 0
    while tx < w + 20:
        if abs(tx - sx) > 320:
            kind = kinds[(k + seed) % len(kinds)] if rnd.random() < 0.7 else rnd.choice(kinds)
            tree_card(lum, tx, by - 6 + rnd.uniform(-6, 4), kind, rnd.uniform(22, 40), seed + 10 + 7 * k,
                      rnd.uniform(0.34, 0.50))
        tx += rnd.uniform(60, 150)
        k += 1
    # telegraph poles along the far side
    for k, px in enumerate(np.arange(sx - 520, sx + 600, 260)):
        if 0 < px < w and abs(px - sx) > 300:
            poly(lum, [(px - 3, by - 175), (px + 3, by - 175), (px + 4, by + 4), (px - 4, by + 4)], 0.20, seed + 40 + k, shadow=False)
            poly(lum, [(px - 22, by - 168), (px + 22, by - 168), (px + 22, by - 163), (px - 22, by - 163)], 0.20, seed + 50 + k, shadow=False)
    if 0 < sx - 520 or sx + 600 < w:
        wire = np.zeros((h, w), np.uint8)
        for dy in (0, 0):
            cv2.line(wire, (0, by - 160), (w, by - 160), 255, 1, cv2.LINE_AA)
        a = C.rub_mask(wire, seed + 60)
        lum[:] = lum * (1 - 0.5 * a) + 0.2 * 0.5 * a

    # ---- the lit interior (rendered on its own, shown through the windows)
    inside = np.full((h, w), 0.95, np.float32)
    lit = np.zeros((h, w), np.uint8)
    lit[max(0, by - 260):by + 10, max(0, int(sx) - 300):int(sx) + 300] = 255
    card_k(inside, lit, 0.93, seed + 69, edge=0.0, hatch=0.035, rock=0.75)
    fl = np.zeros((h, w), np.uint8)
    fl[by - 40:by + 10, max(0, int(sx) - 300):int(sx) + 300] = 255
    card_k(inside, fl, 0.80, seed + 70, edge=0.0, hatch=0.10, rock=0.4)        # the office floor, hatched
    shapes = []
    shapes += desk(sx - 225, by - 62, 80, by - 2, drawers=1)
    shapes += clock(sx + 22, by - 125, 10, hh=4, mm=10 if beat.get("clock10") else 8, pend=False)
    C.pin_up(inside, [s for s in shapes if s.role != "pin"], seed + 71, halo=False, piece_shadow=False)
    # cupboard and SERVICE door cut at this distance as plain cards (no panel slits: they would read as noise)
    cx0, cy0, cx1, cy1 = sx + 124, by - 128, sx + 170, by - 14
    poly(inside, [(cx0 - 4, cy0 - 7), (cx1 + 4, cy0 - 7), (cx1 + 4, cy0), (cx0 - 4, cy0)], 0.20, seed + 72, edge=0.1)
    poly(inside, [(cx0, cy0), (cx1, cy0), (cx1, cy1), (cx0, cy1)], 0.30, seed + 73, edge=0.12)
    if beat.get("cup", 0) > 0:
        poly(inside, [(cx0 + 4, cy0 + 4), (cx1 - 4, cy0 + 4), (cx1 - 4, cy1 - 4), (cx0 + 4, cy1 - 4)], 0.17, seed + 74, shadow=False)
        for fy in (0.35, 0.68):
            yy_ = cy0 + (cy1 - cy0) * fy
            poly(inside, [(cx0 + 4, yy_), (cx1 - 4, yy_), (cx1 - 4, yy_ + 3), (cx0 + 4, yy_ + 3)], 0.25, seed + 75, shadow=False)
        leaf = [(cx0, cy0), (cx0 - 34, cy0 - 6), (cx0 - 34, cy1 + 6), (cx0, cy1)]
        poly(inside, leaf, 0.50, seed + 76, edge=0.15)
        if beat.get("key", True):     # the brass key on its hook inside the door leaf, with its paper tag
            kx, ky = cx0 - 18, cy0 + 26
            km = np.zeros((h, w), np.uint8)
            cv2.circle(km, (int(kx), int(ky)), 5, 255, 2, cv2.LINE_AA)
            cv2.line(km, (int(kx), int(ky + 5)), (int(kx), int(ky + 26)), 255, 3, cv2.LINE_AA)
            cv2.line(km, (int(kx), int(ky + 24)), (int(kx + 5), int(ky + 24)), 255, 2, cv2.LINE_AA)
            C.drop(inside, km, (1, 2), 1, 0.4)
            C.card_piece(inside, km, 0.92, seed + 77, edge=0.05)
            strip(inside, kx + 3, ky + 10, kx + 13, ky + 17, 0.98, seed + 78, edge=0.0)
    else:
        kb = np.zeros((h, w), np.uint8)
        cv2.circle(kb, (int(cx1 - 8), int((cy0 + cy1) / 2)), 2, 255, -1)
        C.card_piece(inside, kb, 0.85, seed + 79)
    dx0, dy0, dx1, dy1 = sx + 188, by - 136, sx + 232, by - 4
    poly(inside, [(dx0 - 4, dy0 - 5), (dx1 + 4, dy0 - 5), (dx1 + 4, dy1), (dx0 - 4, dy1)], 0.22, seed + 80, edge=0.1)
    poly(inside, [(dx0, dy0), (dx1, dy0), (dx1, dy1), (dx0, dy1)], 0.38, seed + 81, edge=0.12)
    kb = np.zeros((h, w), np.uint8)
    cv2.circle(kb, (int(dx1 - 8), int(by - 66)), 3, 255, -1)
    C.card_piece(inside, kb, 0.85, seed + 82)
    # the SERVICE card on the door: a pale fleck
    strip(inside, dx0 + 9, dy0 + 14, dx1 - 9, dy0 + 24, 0.98, seed + 83, edge=0.0)
    if beat.get("agent"):
        ak = dict(beat["agent"])
        fig = [s for s in agent(**ak) if s.role != "pin"]
        C.pin_up(inside, fig, seed + 76, halo=False, piece_shadow=False)

    # ---- the station: a small dark card box with three lit windows
    WIN = {"W1": (sx - 232, by - 138, sx - 128, by - 56), "W2": (sx - 72, by - 146, sx + 52, by - 46),
           "W3": (sx + 80, by - 150, sx + 240, by - 34)}
    glow = np.zeros((h, w), np.float32)
    for (x0, y0, x1, y1) in WIN.values():
        glow[int(by + 6):int(by + 40), int(x0 - 10):int(x1 + 10)] = 1
    glow = cv2.GaussianBlur(glow, (0, 0), 14)
    body = np.zeros((h, w), np.uint8)
    cv2.rectangle(body, (int(sx - 265), int(by - 175)), (int(sx + 265), int(by)), 255, -1)
    C.spray(lum, body, seed + 80, reach=18, strength=0.22)
    C.drop(lum, body, (6, 7), 4, 0.3)
    C.card_piece(lum, body, 0.30, seed + 81, edge=0.15)
    # clapboard lines rubbed across the card
    cl = np.zeros((h, w), np.uint8)
    for yb in range(int(by - 168), int(by), 11):
        cv2.line(cl, (int(sx - 262), yb), (int(sx + 262), yb), 255, 1, cv2.LINE_AA)
    a = C.rub_mask(cl, seed + 82, keep=0.6) * 0.5
    lum[:] = lum * (1 - a) + 0.12 * a
    # windows: cut through to the lit interior, with a dark frame card
    for k, (x0, y0, x1, y1) in WIN.items():
        lum[int(y0):int(y1), int(x0):int(x1)] = inside[int(y0):int(y1), int(x0):int(x1)]
        fr = np.zeros((h, w), np.uint8)
        cv2.rectangle(fr, (int(x0) - 6, int(y0) - 6), (int(x1) + 6, int(y1) + 6), 255, -1)
        cv2.rectangle(fr, (int(x0), int(y0)), (int(x1), int(y1)), 0, -1)
        cv2.rectangle(fr, (int(x0) - 9, int(y1)), (int(x1) + 9, int(y1) + 7), 255, -1)      # sill
        C.card_piece(lum, fr, 0.14, seed + 90 + len(k), edge=0.1)
    # roof (hipped), chimney, eave shadow
    roof = [(sx - 300, by - 172), (sx + 300, by - 172), (sx + 230, by - 238), (sx - 230, by - 238)]
    C.spray(lum, cv2.fillPoly(np.zeros((h, w), np.uint8), [np.int32(roof)], 255), seed + 95, reach=14, strength=0.2)
    poly(lum, [(sx + 120, by - 270), (sx + 146, by - 270), (sx + 146, by - 220), (sx + 120, by - 220)], 0.18, seed + 96)
    poly(lum, roof, 0.13, seed + 97, edge=0.2)
    # the name board on the gable side, pale card, tiny pen lettering
    nb = strip(lum, sx - 115, by - 206, sx + 115, by - 176, 0.90, seed + 98, edge=0.04)
    t = pen99.letter(["RANDOLPH"], 19, seed + 99, weight=0.17)
    tm = np.zeros((h, w), np.uint8)
    C.place(tm, t, sx, by - 191 + (t.shape[0] / 2 - 19 * 1.15 + 19 * 0.5))
    a = C.rub_mask(tm, seed + 100, keep=0.95)
    lum[:] = lum * (1 - a) + 0.08 * a
    # station platform (pale stone card) and the light falling on it from the windows
    strip(lum, sx - 420, by, sx + 420, by + 24, 0.62, seed + 101, edge=0.12)
    poly(lum, [(sx - 420, by + 24), (sx + 420, by + 24), (sx + 420, by + 34), (sx - 420, by + 34)], 0.26, seed + 102, shadow=False)
    gmod = np.clip(0.55 + 4.0 * rock_patch(h, w, seed + 104, 1.2) + 0.35 * hatch_field(h, w, seed + 105, 7, 176), 0, 1.3)
    lum[:] = np.clip(lum + 0.18 * glow * gmod * (yy > by), 0, 1.0)
    if beat.get("lady"):
        lk = dict(beat["lady"])
        C.pin_up(lum, lady_back(**lk), seed + 103, halo=False,
                 tones=dict(coat=0.24, skin_s=0.55, hat=0.08, trousers=0.18, hair=0.06))

    # ---- the tracks between us and them
    y_b0 = by + 34
    ballast(lum, y_b0, h, seed + 110)
    span = h - y_b0
    track(lum, y_b0 + span * 0.16, y_b0 + span * 0.30, seed + 120, gauge_w=(3, 4))
    track(lum, y_b0 + span * 0.48, y_b0 + span * 0.72, seed + 130, gauge_w=(5, 7))
    # our own platform edge at the foot of the frame (the place we stand)
    ye = h - int(span * 0.14)
    poly(lum, [(0, ye), (w, ye - 2), (w, h), (0, h)], 0.58, seed + 140, edge=0.08)
    strip(lum, 0, ye - 2, w, ye + 9, 0.93, seed + 141, edge=0.02)              # painted edge line
    if foreground:
        # a lamp post and the end of a bench on our platform: big, dark, near
        px = 140
        poly(lum, [(px - 14, -10), (px + 14, -10), (px + 18, h), (px - 18, h)], 0.10, seed + 150)
        poly(lum, [(px - 56, 40), (px + 56, 40), (px + 34, 120), (px - 34, 120)], 0.12, seed + 151)
        lm = np.zeros((h, w), np.uint8)
        cv2.ellipse(lm, (px, 128), (26, 14), 0, 0, 360, 255, -1)
        C.card_piece(lum, lm, 0.92, seed + 152, edge=0.05)
        bx = w - 330
        for k, (a0, a1) in enumerate(((ye - 120, ye - 96), (ye - 78, ye - 56))):
            poly(lum, [(bx, a0), (w + 10, a0 - 2), (w + 10, a1), (bx, a1)], 0.16, seed + 153 + k)
        for lx_ in (bx + 40, w - 60):
            poly(lum, [(lx_ - 9, ye - 60), (lx_ + 9, ye - 60), (lx_ + 11, ye + 40), (lx_ - 11, ye + 40)], 0.12, seed + 160 + int(lx_))
    return lum, WIN, by


# ------------------------------------------------------------------ the panels
def ag(where, by, sx, **k):
    """Agent pose inside the office; interior floor hidden under the sills (by - 6)."""
    base = dict(floor=by - 6, scale=S_IN, pencil_deg=200)
    base.update(k)
    return base


def P(i, show_text=True):
    x0, y0, x1, y1 = BOXES[i]
    w, h = x1 - x0, y1 - y0
    seed = 2000 + 100 * i
    sx = w * 0.5 if i == 0 else w * 0.5
    by = int(h * 0.60)
    if i == 0:
        beat = dict(agent=ag("W1", by, sx, x=sx - 176, face=1, sh=34, el=-40, tilt=10, seated=True))
    elif i == 1:
        beat = dict(agent=ag("W2", by, sx, x=sx - 20, face=1, legs=(22, -20), sh=-22, el=24),
                    lady=dict(cx=sx - 360, foot=by + 20, h=112, walk=0.5, face=-1))
    elif i == 2:
        beat = dict(agent=ag("W2", by, sx, x=sx + 26, face=-1, sh=10, el=24, tilt=2),
                    lady=dict(cx=sx - 30, foot=by + 20, h=112))
    elif i == 3:
        beat = dict(agent=ag("W2", by, sx, x=sx - 22, face=1, tilt=-26, sh=6, el=20), clock10=True,
                    lady=dict(cx=sx - 30, foot=by + 20, h=112))
    elif i == 4:
        beat = dict(agent=ag("W2", by, sx, x=sx + 40, face=1, legs=(18, -16), sh=-14, el=20), clock10=True,
                    lady=dict(cx=sx - 250, foot=by + 20, h=112, walk=0.6, face=-1))
    elif i == 5:
        beat = dict(agent=ag("W3", by, sx, x=sx + 176, face=-1, legs=(10, -8), sh=64, el=18), cup=112, clock10=True)
    else:
        beat = dict(agent=ag("W3", by, sx, x=sx + 176, face=-1, legs=(3, -3), sh=50, el=120, wr=8, pencil_deg=40, tilt=6),
                    cup=112, clock10=True)
    lum, WIN, by = scene(w, h, beat, seed, sx=sx, foreground=(i == 0))
    if not show_text:
        return lum
    # captions: a pale card at the top left
    caption_card(lum, CAPS[i], 26, 22, (w - 160) if i == 0 else (w - 90), seed + 7, cap=38 if i == 0 else 36)
    # balloons sit on our side of the rails, their tails running across the tracks to the tiny speaker
    if i == 2:   # her question: from the lady at the window
        lettered_balloon(lum, LINES["q"], 46, (w * 0.36, h - 110), (sx - 30, by - 90), seed + 8)
    if i == 3:   # his answer, from inside the window
        lettered_balloon(lum, LINES["a"], 48, (w * 0.68, h - 110), (sx - 6, by - 98), seed + 8)
    if i == 4:   # her thanks as she goes
        lettered_balloon(lum, LINES["t"], 50, (w * 0.27, h - 105), (sx - 254, by - 88), seed + 8)
    if i == 6:   # his line at the open cupboard
        lettered_balloon(lum, LINES["f"], 46, (w * 0.36, h - 110), (sx + 166, by - 116), seed + 8)
    return lum


def build(n_panels=7, text_last=True):
    page = pen99.sheet99().astype(np.float32)
    for i, box in enumerate(BOXES):
        if i >= n_panels:
            break
        x0, y0, x1, y1 = box
        lum = P(i, show_text=(text_last or i < n_panels - 1))
        # one light softening of the pixel-level charcoal dust (0.95 px) so the page stays inside the 1.2 MB JPEG budget;
        # the rock rub, hatching and card edges are 3-20 px features and survive it
        lum = cv2.GaussianBlur(lum, (0, 0), SOFT)
        rgb = C.tone(lum)
        m = np.zeros((H, W), np.uint8)
        m[y0:y1, x0:x1] = 255
        penlib.shadow_onto(page, m, off=6, blur=5, opacity=0.30)
        page[y0:y1, x0:x1] = rgb
    bm = penlib.border_mask((H, W), BOXES[:n_panels], w=10, seed=2090)
    penlib.ink_onto(page, bm, color=np.array([20, 21, 14], np.float32))
    return page


def main():
    page = build()
    img, size = B.save_page(page.copy(), N, PID, TITLE)
    if "--page-only" in sys.argv:
        print("bytes", size)
        return
    frames = []
    for n in range(1, 8):
        f = build(n, text_last=False) if n in (3, 4, 5, 7) else build(n)
        pen99.folio(f, N, TITLE)
        frames.append(f)
        if n in (3, 4, 5, 7):
            f = build(n)
            pen99.folio(f, N, TITLE)
            frames.append(f)
    # keep 8: drop the plain build of 7 panels before the last? keep the balloon arrivals for 3, 5 and 7
    keep = [0, 1, 2, 3, 6, 7, 9, 10]
    frames = [frames[k] for k in keep]
    nb = B.save_beats(N, frames)
    print("bytes", size, "beats", nb)


if __name__ == "__main__":
    main()

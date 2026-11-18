"""99 ways, page 52 "From the hill" (reduction and expansion; medium: charcoal-card).
Extreme long shots: the station small in its Vermont valley, the balloons reaching across the land.
No figure is taller than a tenth of its panel (the agent is a speck in a lit window, the stranger a 26 px card).

One valley, cut and rubbed once as charcoal cards (the page-20 card kit: rock-rubbed, hatched, torn ridges,
hand-cut trees; charcoal99 + p20_across_the_tracks helpers), seen from the hill above the station in six frames:
the far range, the wooded ridge, the patchwork of fields and hedgerows, the river and the railway along it, the
village with its white church, the tiny station with three lit windows, and our own hill crest with its trees
in the foreground. The four canon lines verbatim in cut-card balloons whose tails run across fields and river
down to the speck of the speaker. Captions on torn pale cards in the shared pen hand.
Run: python3 -I p52_from_the_hill.py [--page-only]"""
import math
import random
import sys

import cv2
import numpy as np

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import charcoal99 as C  # noqa: E402
import b1m2 as B  # noqa: E402
import p20_across_the_tracks as T  # noqa: E402  (its import sets C.card_piece = T.card_k, the page-20 rubbed card)
from p20_across_the_tracks import poly, strip, tree_card, lady_back, card_k, hatch_field, lowf  # noqa: E402
import pen99  # noqa: E402
from pen99 import penlib  # noqa: E402

N, PID, TITLE = 52, "from-the-hill", "From the hill"
W, H = 2200, 2850
BOXES = [(110, 110, 2090, 800),
         (110, 840, 1080, 1415), (1120, 840, 2090, 1415),
         (110, 1455, 1080, 2030), (1120, 1455, 2090, 2030),
         (110, 2070, 2090, 2730)]
VW, VH = 2000, 760              # the one valley, in its own px
SX, SY = 1180, 452              # the station's platform line in the valley
SOFT = 1.05
LINES = {"q": ["Pardon me —", "have you the right time?"], "a": ["Ten past four,", "by the clock."],
         "t": ["Much obliged!"], "f": ["Well, here I am...", "and what for?"]}
CAPS = ["From the hill above the White River: Randolph, Vermont, a September afternoon. Down there, in the "
        "station office, the agent reads his memo, 4:15, the SERVICE door, and gets up for the key.",
        "A lady at the ticket window calls to him.",
        "He looks at the office clock.",
        "She thanks him and goes off along the platform.",
        "He opens the cupboard: the key hangs on its hook.",
        "And there he stands. The key stays on its hook; the SERVICE door stays closed."]
# each panel's crop of the valley (x0, y0) and its size: a slow pan along the valley, the station kept small
CROP = {0: (10, 30), 1: (520, 120), 2: (700, 150), 3: (560, 170), 4: (760, 130), 5: (10, 120)}


def ridge(w, y, amp, n, seed, phase):
    rnd = random.Random(seed)
    pts = [(-20, y)]
    for k in range(n):
        pts.append((w * (k + 0.5) / n, y - amp * (0.5 + 0.5 * math.sin(k * 0.8 + phase)) ** 1.6 - rnd.uniform(0, amp * 0.3)))
    return pts + [(w + 20, y), (w + 20, VH), (-20, VH)]


def lerp_path(pts, xs):
    p = np.array(pts, float)
    return np.interp(xs, p[:, 0], p[:, 1])


VP = (1010.0, 236.0)          # where the valley runs off into the far range


def valley(seed=5200):
    lum = C.wall(VW, VH, seed, level=0.84, hp_gain=0.55, broad_gain=0.45, scale=1.6)
    yy = np.arange(VH)[:, None].astype(np.float32)
    sk = hatch_field(VH, VW, seed + 5, 9.0, 176) * np.clip(0.25 + 0.5 * lowf(VH, VW, seed + 6, 40), 0, 1)
    lum -= 0.09 * sk * np.clip(1.2 - yy / 260, 0, 1)
    rnd = random.Random(seed)
    # the far range (pale torn card) and a nearer blue-grey range
    poly(lum, ridge(VW, 250, 160, 7, seed + 1, 0.4), 0.74, seed + 1, edge=0.10, torn=True)
    poly(lum, ridge(VW, 262, 70, 12, seed + 2, 1.9), 0.64, seed + 2, edge=0.12, torn=True)
    # the valley floor: fields in a perspective grid running off toward VP, hedgerows along their edges
    tones = [0.93, 0.86, 0.78, 0.70, 0.60, 0.48, 0.90, 0.82]
    ys = [250, 262, 278, 298, 322, 352, 388, 430, 480, 540, 610, 690, 790]
    bases = np.arange(-2600, 4800, 300)
    for r in range(len(ys) - 1):
        ya, yb = ys[r], ys[r + 1]
        fa, fb = (ya - VP[1]) / (VH - VP[1]), (yb - VP[1]) / (VH - VP[1])
        for c in range(len(bases) - 1):
            j = rnd.uniform(-40, 40)
            xa0, xa1 = VP[0] + (bases[c] + j - VP[0]) * fa, VP[0] + (bases[c + 1] + j - VP[0]) * fa
            xb0, xb1 = VP[0] + (bases[c] + j - VP[0]) * fb, VP[0] + (bases[c + 1] + j - VP[0]) * fb
            if max(xa1, xb1) < -40 or min(xa0, xb0) > VW + 40:
                continue
            t = rnd.choice(tones)
            poly(lum, [(xa0, ya), (xa1, ya), (xb1, yb), (xb0, yb)], t, seed + 300 + r * 60 + c, edge=0.16, shadow=False,
                 hatch=rnd.choice([0.05, 0.10, 0.16]))
            if t < 0.55:                                     # a woodlot: dots of tree cards
                for k in range(int(3 + 6 * fb)):
                    u, v = rnd.random(), rnd.random()
                    tx = (xa0 + (xa1 - xa0) * u) * (1 - v) + (xb0 + (xb1 - xb0) * u) * v
                    tree_card(lum, tx, ya + (yb - ya) * v, "round", 3 + 9 * fb, seed + 400 + r * 60 + c * 7 + k, 0.30)
        hm = np.zeros((VH, VW), np.uint8)                    # the row's hedgerow
        cv2.line(hm, (0, int(yb)), (VW, int(yb)), 255, max(1, int(1 + 3 * fb)), cv2.LINE_AA)
        a = C.rub_mask(hm, seed + 600 + r, keep=0.8)
        lum[:] = lum * (1 - 0.7 * a) + 0.22 * 0.7 * a
        for k in range(int(4 + 10 * fb)):
            if rnd.random() < 0.6:
                tree_card(lum, rnd.uniform(0, VW), yb + 1, rnd.choice(["round", "bush", "poplar"]),
                          2.5 + 9 * fb, seed + 700 + r * 40 + k, rnd.uniform(0.26, 0.40))
    # the river: from the far end of the valley, meandering down toward us and off to the left
    ts = np.linspace(0, 1, 60)
    rx = VP[0] - 40 - 700 * ts ** 1.3 + 120 * np.sin(ts * 9.0) * ts
    ryy = VP[1] + 30 + (VH - VP[1] + 40) * ts ** 1.15
    rw = 2 + 26 * ts ** 1.4
    nrm = np.stack([np.gradient(ryy), -np.gradient(rx)], 1)
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-9
    L_ = np.stack([rx, ryy], 1)
    for wmul, t, sd in ((1.0 + 0.0, 0.30, 800), (0.72, 0.95, 801)):          # dark banks, then the pale water
        ww = (rw * wmul + (4 if t < 0.5 else 0))[:, None]
        side_a, side_b = L_ + nrm * ww, L_ - nrm * ww
        poly(lum, [tuple(p) for p in side_a] + [tuple(p) for p in side_b[::-1]], t, seed + sd, edge=0.05, shadow=False,
             torn=True, hatch=0.03)
    # the railway: off the far end, through the station, and down across the valley to the right
    rails = [(640, 296), (SX - 140, SY - 24), (SX, SY + 6), (SX + 300, SY + 56), (VW + 40, VH + 20)]
    xs2 = np.linspace(rails[0][0], VW + 40, 140)
    ys2 = lerp_path(rails, xs2)
    bed = [(x, y_ - 2.5 - 3 * (y_ - VP[1]) / VH) for x, y_ in zip(xs2, ys2)] + \
          [(x, y_ + 2.5 + 3 * (y_ - VP[1]) / VH) for x, y_ in zip(xs2[::-1], ys2[::-1])]
    poly(lum, bed, 0.30, seed + 810, edge=0.1, shadow=False, hatch=0.03)
    # the valley's two wooded sides closing in from left and right (dark torn cards with firs)
    left = [(-20, 160), (180, 182), (380, 236), (560, 300), (650, 352), (600, 420), (430, 470), (220, 520), (-20, 560)]
    right = [(VW + 20, 150), (1830, 176), (1660, 232), (1520, 290), (1440, 330), (1500, 380), (1700, 430), (VW + 20, 470)]
    for k, (sh, t) in enumerate(((left, 0.44), (right, 0.48))):
        poly(lum, sh, t, seed + 820 + k, edge=0.14, torn=True, hatch=0.14)
        P_ = np.array(sh, float)
        for j in range(90):
            x = rnd.uniform(P_[:, 0].min(), P_[:, 0].max())
            yv = rnd.uniform(P_[:, 1].min(), P_[:, 1].max())
            if cv2.pointPolygonTest(np.float32(P_), (float(x), float(yv)), False) > 0:
                tree_card(lum, x, yv, rnd.choice(["fir", "fir", "round"]), 4 + 7 * (yv - 150) / 420,
                          seed + 830 + 100 * k + j, rnd.uniform(0.24, 0.36))
    # the village: farm houses and barns about the station, the white church with its steeple
    for k, (hx, hy, s) in enumerate([(SX - 250, SY - 36, 1.0), (SX - 196, SY - 58, 0.8), (SX - 150, SY - 20, 0.9),
                                     (SX + 160, SY - 34, 1.0), (SX + 226, SY - 12, 1.1), (SX + 300, SY - 64, 0.8),
                                     (780, 330, 0.9), (1600, 560, 1.5), (360, 640, 1.6), (1330, 300, 0.7)]):
        house(lum, hx, hy, s, seed + 900 + 10 * k, t=rnd.choice([0.95, 0.30, 0.26, 0.92]))
    church(lum, SX - 330, SY - 50, seed + 990)
    return lum


def house(lum, x, y, s, seed, t=0.9):
    w_, h_ = 18 * s, 11 * s
    poly(lum, [(x - w_ / 2, y - h_), (x + w_ / 2, y - h_), (x + w_ / 2, y), (x - w_ / 2, y)], t, seed, edge=0.12)
    poly(lum, [(x - w_ / 2 - 3 * s, y - h_), (x + w_ / 2 + 3 * s, y - h_), (x + w_ / 4, y - h_ - 9 * s), (x - w_ / 4, y - h_ - 9 * s)],
         0.18, seed + 1, edge=0.1)


def church(lum, x, y, seed):
    poly(lum, [(x - 16, y - 18), (x + 16, y - 18), (x + 16, y), (x - 16, y)], 0.95, seed, edge=0.06)
    poly(lum, [(x - 19, y - 18), (x + 19, y - 18), (x + 8, y - 30), (x - 8, y - 30)], 0.22, seed + 1)
    poly(lum, [(x + 6, y - 34), (x + 16, y - 34), (x + 16, y), (x + 6, y)], 0.96, seed + 2, edge=0.05)
    poly(lum, [(x + 4, y - 34), (x + 18, y - 34), (x + 11, y - 62)], 0.20, seed + 3)


def station(lum, beat, seed):
    """the station, about 120 px wide: dark card box, hipped roof, three lit windows, pale platform. Inside, specks."""
    x0, x1, top = SX - 56, SX + 56, SY - 30
    strip(lum, SX - 110, SY, SX + 110, SY + 7, 0.80, seed, edge=0.08)              # platform
    body = [(x0, top), (x1, top), (x1, SY), (x0, SY)]
    poly(lum, body, 0.28, seed + 1, edge=0.12)
    poly(lum, [(x0 - 9, top), (x1 + 9, top), (x1 - 12, top - 17), (x0 + 12, top - 17)], 0.12, seed + 2)
    WIN = {"W1": (x0 + 8, top + 7, x0 + 30, SY - 6), "W2": (SX - 12, top + 6, SX + 12, SY - 5),
           "W3": (x1 - 32, top + 6, x1 - 8, SY - 4)}
    for k, (a0, b0, a1, b1) in WIN.items():
        strip(lum, a0, b0, a1, b1, 0.96, seed + 3 + len(k), edge=0.02, shadow=False)
    # the agent: a speck (head and body cut as one 9 x 14 px card) in the window of the beat
    w, dx, pose = beat.get("agent", ("W1", 0, "stand"))
    a0, b0, a1, b1 = WIN[w]
    cx = (a0 + a1) / 2 + dx
    fm = np.zeros(lum.shape, np.uint8)
    cv2.ellipse(fm, (int(cx * 4), int((b1 - 12) * 4)), (3 * 4, 3 * 4), 0, 0, 360, 255, -1, cv2.LINE_AA, shift=2)
    cv2.fillPoly(fm, [np.int32(np.array([(cx - 4, b1 - 9), (cx + 4, b1 - 9), (cx + 5, b1), (cx - 5, b1)]) * 4)], 255,
                 cv2.LINE_AA, shift=2)
    if pose == "chin":
        cv2.line(fm, (int(cx * 4), int((b1 - 6) * 4)), (int((cx - 3) * 4), int((b1 - 10) * 4)), 255, 6, cv2.LINE_AA, shift=2)
    card_k(lum, fm, 0.10, seed + 20, edge=0.05, hatch=0.0)
    if beat.get("cup"):                                     # the cupboard opened: a dark slot and its pale leaf in W3
        strip(lum, a1 - 8, b0 + 2, a1 - 2, b1 - 1, 0.12, seed + 21, edge=0.0, shadow=False)
        strip(lum, a1 - 11, b0 + 1, a1 - 8, b1, 0.70, seed + 22, edge=0.0, shadow=False)
    if beat.get("lady"):
        lx, walk, face = beat["lady"]
        C.pin_up(lum, lady_back(SX + lx, SY + 3, h=26, walk=walk, face=face), seed + 30, halo=False, piece_shadow=False,
                 tones=dict(coat=0.20, skin_s=0.55, hat=0.06, trousers=0.16, hair=0.06))
    return WIN


def hill_crest(lum, w, h, seed, tilt):
    """our own hill: a dark torn card across the foot of the frame, its trees and a fence near and big"""
    rnd = random.Random(seed)
    y0, y1 = h - 120 - tilt, h - 70 + tilt
    pts = [(-20, y0)] + [(w * f, y0 + (y1 - y0) * f + rnd.uniform(-10, 10)) for f in np.linspace(0.05, 0.95, 14)] + \
          [(w + 20, y1), (w + 20, h + 10), (-20, h + 10)]
    poly(lum, pts, 0.34, seed + 1, edge=0.12, torn=True, hatch=0.12)
    for k, f in enumerate((0.06, 0.18, 0.84, 0.93)):
        x = w * f
        base = y0 + (y1 - y0) * f + 26
        if rnd.random() < 0.85:
            tree_card(lum, x, base, ["fir", "round", "poplar", "fir"][k], rnd.uniform(16, 24), seed + 10 + k, 0.24)
    for k, f in enumerate(np.linspace(0.30, 0.70, 7)):    # fence posts along the crest
        x = w * f
        yb = y0 + (y1 - y0) * f + 18
        poly(lum, [(x - 3, yb - 26), (x + 3, yb - 26), (x + 4, yb), (x - 4, yb)], 0.15, seed + 30 + k, shadow=False)


BEATS = [dict(agent=("W1", 0, "stand")),
         dict(agent=("W2", -2, "stand"), lady=(-24, 0.0, 0)),
         dict(agent=("W2", 3, "stand"), lady=(-24, 0.0, 0)),
         dict(agent=("W2", 3, "stand"), lady=(-74, 0.6, -1)),
         dict(agent=("W3", -2, "stand"), cup=True),
         dict(agent=("W3", -2, "chin"), cup=True)]
_VAL = None


def P(i, show_text=True):
    global _VAL
    if _VAL is None:
        _VAL = valley()
    x0, y0, x1, y1 = BOXES[i]
    w, h = x1 - x0, y1 - y0
    lum = _VAL.copy()
    WIN = station(lum, BEATS[i], 5300 + 10 * i)
    cx, cy = CROP[i]
    lum = lum[cy:cy + h, cx:cx + w].copy()
    if lum.shape != (h, w):
        lum = cv2.resize(lum, (w, h))
    hill_crest(lum, w, h, 5400 + 10 * i, tilt=(i % 3) * 12)
    sx, sy = SX - cx, SY - cy
    if not show_text:
        return lum
    T.caption_card(lum, CAPS[i], 26, 22, (w - 160) if i == 0 else (w - 90), 5500 + 10 * i, cap=36)
    # the balloons sit far from the speaker, up in the sky or down on our hill, their tails across the land
    if i == 1:
        T.lettered_balloon(lum, LINES["q"], 44, (w * 0.30, h - 150), (sx - 24, sy - 22), 5601, tail_w=0.14)
    if i == 2:
        a0, b0, a1, b1 = WIN["W2"]
        T.lettered_balloon(lum, LINES["a"], 46, (w * 0.78, h - 140), ((a0 + a1) / 2 - cx + 4, b1 - cy + 3), 5602, tail_w=0.14)
    if i == 3:
        T.lettered_balloon(lum, LINES["t"], 50, (w * 0.24, h - 120), (sx - 74, sy - 22), 5603, tail_w=0.14)
    if i == 5:
        a0, b0, a1, b1 = WIN["W3"]
        T.lettered_balloon(lum, LINES["f"], 48, (w * 0.70, h - 130), (a1 - cx - 3, b1 - cy + 3), 5605, tail_w=0.12)
    return lum


def build(n_panels=6, text_last=True):
    page = cv2.GaussianBlur(pen99.sheet99().astype(np.float32), (0, 0), 1.2)
    for i, box in enumerate(BOXES):
        if i >= n_panels:
            break
        x0, y0, x1, y1 = box
        lum = P(i, show_text=(text_last or i < n_panels - 1))
        lum = cv2.GaussianBlur(lum, (0, 0), SOFT)
        rgb = C.tone(lum)
        m = np.zeros((H, W), np.uint8)
        m[y0:y1, x0:x1] = 255
        penlib.shadow_onto(page, m, off=6, blur=5, opacity=0.30)
        page[y0:y1, x0:x1] = rgb
    bm = penlib.border_mask((H, W), BOXES[:n_panels], w=10, seed=5290)
    penlib.ink_onto(page, bm, color=np.array([20, 21, 14], np.float32))
    return page


def main():
    page = build()
    img, size = B.save_page(page.copy(), N, PID, TITLE)
    print("bytes", size)
    if "--page-only" in sys.argv:
        return
    frames = []
    for n in range(1, 7):
        if n in (2, 3, 4, 6):
            f = build(n, text_last=False)
            pen99.folio(f, N, TITLE)
            frames.append(f)
        f = build(n)
        pen99.folio(f, N, TITLE)
        frames.append(f)
    keep = [0, 1, 2, 4, 6, 7, 8, 9]       # P1; P2 silent, P2 question; P3 answer; P4 silent, thanks; P5; P6 line
    frames = [frames[k] for k in keep]
    print("beats", B.save_beats(N, frames))


if __name__ == "__main__":
    main()

"""Page 99 Marginalia (reader and object; medium: photo-cutout).

Page 01 reprinted small: the base page's own master (films/sources/99-ways/masters/01-template.png, the Rothstein /
ANRC / LoC photo-cutout page) printed at 0.56 as a photographic print with a white border, pasted slightly askew
on the LoC 1934 sheet with a cast shadow. Round it, an annotator's PENCIL notes (the shared pen hand drawn in
graphite grey, grained by the sheet's own tooth) each labelled with its event, E0 to E5, and each with a pencil
leader that runs onto the print and rings the evidence: the memo, the TICKET OFFICE balloon, the clock at 4:10, the
emptied window, the key on its hook, the pencil at the chin with the key unmoved and the SERVICE door shut.
Run: python3 -I p99_marginalia.py [--page-only]
"""
import math
import random
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import b1m2 as B  # noqa: E402
from b1m2 import pen99, penlib  # noqa: E402

N, PID, TITLE = 99, "marginalia", "Marginalia"
W, H = 2200, 2850
S = 0.56                                  # reprint scale
TILT = -0.8                               # degrees, the print laid a little askew
AT = (1100, 1405)                         # centre of the print on the page
GRAPHITE = np.array([62, 62, 70], np.float32)
NCAP = 31
SHEET = pen99.sheet99()

_src = np.asarray(Image.open(B.MASTERS / "01-template.png").convert("RGB")).astype(np.float32)
SRC_H, SRC_W = _src.shape[:2]
BORDER = 26                               # white border of the print, in page px


def M_print():
    c = np.array([SRC_W / 2, SRC_H / 2])
    return penlib.T(*AT) @ penlib.R(TILT) @ penlib.S(S) @ penlib.T(-c[0], -c[1])


def P(x, y):
    """page-01 px -> page-99 px"""
    return tuple(map(float, penlib.apply(M_print(), (x, y))))


def lay_print(pg):
    M = M_print()
    a = np.full((SRC_H, SRC_W), 255, np.uint8)
    g = cv2.warpPerspective(_src, M, (W, H), flags=cv2.INTER_AREA, borderValue=0)
    am = cv2.warpPerspective(a, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
    ab = (am > 127).astype(np.uint8) * 255
    k = cv2.getStructuringElement(cv2.MORPH_RECT, (2 * BORDER + 1, 2 * BORDER + 1))
    bm = cv2.dilate(ab, k)
    penlib.shadow_onto(pg, bm, off=7, blur=6, opacity=0.36)
    bf = bm.astype(np.float32)[..., None] / 255
    pg[:] = pg * (1 - bf) + np.array([247, 245, 239], np.float32) * bf
    af = am.astype(np.float32)[..., None] / 255
    # a photographic print of the page: one gentle neutral grade, slightly lower contrast than the original
    gr = 0.93 * g + 10
    pg[:] = pg * (1 - af) + gr * af


# ------------------------------------------------------------------ pencil
TOOTH = None


def graphite(pg, mask, alpha=0.96):
    """lay a pencil mask: graphite grey, broken by the paper's tooth (from the LoC sheet's own grain)"""
    global TOOTH
    if TOOTH is None:
        g = SHEET.mean(2)
        hp = g - cv2.GaussianBlur(g, (0, 0), 3)
        TOOTH = np.clip(0.80 + hp / (np.abs(hp).std() * 6 + 1e-6), 0.45, 1.0)
        rnd = np.random.default_rng(99)
        TOOTH = TOOTH * np.clip(1 - 0.25 * rnd.random((H, W)), 0.6, 1)
    a = (mask.astype(np.float32) / 255 * alpha * TOOTH)[..., None]
    pg[:] = pg * (1 - a) + GRAPHITE * a


def ring(m, c, rx, ry, seed, w=4.6):
    """a quick pencil ring, overshooting its start"""
    rnd = random.Random(seed)
    t0 = rnd.uniform(0, 6.28)
    ts = np.linspace(t0, t0 + 2 * math.pi * 1.12, 70)
    pts = [(c[0] + rx * (1 + 0.04 * math.sin(3 * t)) * math.cos(t), c[1] + ry * (1 + 0.05 * math.cos(2 * t)) * math.sin(t))
           for t in ts]
    penlib.brush_line(m, pts, w, seed, tremor=1.2)


def leader(m, a, b, seed, rr=0, w=3.8, via=()):
    """a pencil leader from the note (a) toward a target (b), stopping at its ring (rr), with an arrowhead"""
    for v in via:                     # a bent leader: straight runs to each waypoint first
        penlib.brush_line(m, [a, v], w, seed + 50, tremor=0.8)
        a = v
    a, b = np.array(a, float), np.array(b, float)
    d = b - a
    L = np.hypot(*d)
    u = d / L
    e = b - u * (rr + 6)
    mid = (a + e) / 2 + np.array([-u[1], u[0]]) * L * 0.06       # a slight bow, as a hand draws it
    pts = [tuple(a + (mid - a) * t * 2) if t < 0.5 else tuple(mid + (e - mid) * (t - 0.5) * 2) for t in np.linspace(0, 1, 30)]
    penlib.brush_line(m, pts, w, seed, tremor=0.8)
    ue = (e - np.array(pts[-4])) / (np.hypot(*(e - np.array(pts[-4]))) + 1e-6)
    for s in (1, -1):
        ang = math.radians(28) * s
        r = np.array([[math.cos(ang), -math.sin(ang)], [math.sin(ang), math.cos(ang)]])
        q = e - (r @ ue) * 26
        penlib.brush_line(m, [tuple(e), tuple(q)], w, seed + 3 + s)


def note_mask(lines, seed):
    return B.letter_left(lines, NCAP, seed, weight=0.105)


# each note: event, lines, top-left (page px), anchor point on the note for leaders, [(target page-01 px, rx, ry)]
NOTES = [
    ("E0", ["E0  the errand: memo on the desk -", "'4:15 - open SERVICE door. Key in", "cupboard.' Desk left empty (P2);",
            "he walks past the shut cupboard (P3)."], (130, 150), "bl",
     [((372, 822), 130, 76), ((1660, 420), 130, 160)]),
    ("E1", ["E1  the question,", "through the TICKET", "OFFICE glass: she", "stays outside;", "only her voice", "comes in."],
     (120, 1000), "r", [((330, 1120), 165, 120)]),
    ("E2", ["E2  he looks", "up: the clock", "says 4:10 =", "'Ten past four'.", "(5 min to spare!)"],
     (1772, 900), "l", [((1410, 1180), 95, 150, [(1336, 1150)])]),
    ("E3", ["E3  'Much", "obliged!' -", "the window is", "empty now. The", "break is over."],
     (1772, 1420), "l", [((1830, 1440), 150, 100)]),
    ("E4", ["E4  cupboard", "open: the key", "on its hook,", "tag SERVICE,", "in plain view."],
     (120, 1800), "r", [((290, 2300), 85, 165)]),
    ("E5", ["E5  pencil to the chin: 'what for?'  Key still on", "its hook (same as P7); SERVICE door still shut."],
     (560, 2290), "t", [((1590, 2490), 85, 95), ((1160, 2380), 62, 135), ((1950, 2045), 100, 52)]),
]
SUMMARY = (["So: the errand went out of his head between E1 and E4.", "Key stays put. Door stays shut. Goal not met."],
           (560, 2470))
HEADER = (["p. 01, read again with a pencil:", "where does each event show?"], (1230, 190))


def draw_note(pg, k):
    ev, lines, (x, y), side, targets = NOTES[k]
    m = np.zeros((H, W), np.uint8)
    lm = note_mask(lines, 9900 + 10 * k)
    B.blit_mask(m, lm, int(x), int(y))
    h, w = lm.shape
    anchors = {"bl": (x + 120, y + h + 4), "r": (x + w - 10, y + NCAP * 0.6), "l": (x + 6, y + NCAP * 0.6),
               "t": (x + w * 0.5, y - 4)}
    for j, tg in enumerate(targets):
        t, rx, ry = tg[:3]
        via = [v for v in (tg[3] if len(tg) > 3 else ())]
        c = P(*t)
        rxs, rys = rx * S, ry * S
        ring(m, c, rxs, rys, 9950 + 10 * k + j)
        a = anchors[side]
        if side == "t":
            a = (min(max(c[0], x + 40), x + w - 40), y - 6)
        if side == "bl" and j == 1:
            a = (x + w - 60, y + h + 4)
        leader(m, a, c, 9970 + 10 * k + j, rr=min(rxs, rys) * 0.9, via=via)
    graphite(pg, m)


def build(upto=6, summary=True):
    pg = SHEET.copy()
    lay_print(pg)
    hm = np.zeros((H, W), np.uint8)
    lm = note_mask(HEADER[0], 9990)
    B.blit_mask(hm, lm, *HEADER[1])
    y = HEADER[1][1] + lm.shape[0] + 4
    penlib.brush_line(hm, [(HEADER[1][0] + 8, y), (HEADER[1][0] + lm.shape[1] - 40, y - 3)], 3.4, 9991)
    graphite(pg, hm)
    for k in range(upto):
        draw_note(pg, k)
    if summary and upto >= 6:
        m = np.zeros((H, W), np.uint8)
        B.blit_mask(m, note_mask(SUMMARY[0], 9998), *SUMMARY[1])
        graphite(pg, m)
    return pg


def finish(p):
    p = np.clip(np.round(p), 0, 255).astype(np.uint8)
    pen99.folio(p, N, TITLE)
    return p


if __name__ == "__main__":
    page = build()
    img, size = B.save_page(page, N, PID, TITLE)
    print("jpeg bytes", size)
    if "--page-only" not in sys.argv:
        fr = [np.asarray(Image.fromarray(finish(build(u, summary=(u == 6)))).resize((960, 1242), Image.LANCZOS))
              for u in range(0, 7)]
        print("beats", B.save_beats(N, fr))

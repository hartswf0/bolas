"""Page 27 Out of order (reader and object; medium: photo-cutout).

The eight page-01 photo panels (99-ways-template rest layers: Rothstein 1937 agent and clock, ANRC 1922 key,
HANDMADE memo, cards, hook, tag; the c1 lines on cut-paper balloons in the shared pen hand) are cut out as
separate prints with a white scissor margin and scattered across the LoC 1934 sheet out of their reading order.
A small numbered paper tag pinned to each print gives the order 1-8. Nothing else tells the order.
Run: python3 -I p27_out_of_order.py [beats]
"""
import math
import random
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/kit")
from b1m2 import *  # noqa
import build_page01 as p01  # noqa: E402

N, PID, TITLE = 27, "out-of-order", "Out of order"
SHEET = pen99.sheet99()
BCAP_K = 1.12          # balloon caps enlarged against page 01 so the scattered (smaller) prints stay legible
TAG_PAPER = np.array([244, 226, 160], np.float32)   # yellowed tag card

# reading order key -> (centre on the page, scale vs the 2550 page-01 panel, rotation deg)
LAY = {
    "P3": ((440, 525), 0.740, -5.0),
    "P6": ((1110, 497), 0.740, 3.5),
    "P1": ((1758, 548), 0.740, 4.5),
    "P5": ((515, 1350), 0.740, 2.5),
    "P2": ((1240, 1420), 0.740, -4.0),
    "P4": ((1826, 1335), 0.740, 4.5),
    "P8": ((600, 2245), 0.740, -3.0),
    "P7": ((1655, 2205), 0.740, 5.0),
}
ORDER = ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8"]


def panel_img(k):
    """Page-01 rest panel with its c1 balloon (caps x BCAP_K), at the 2550 scale."""
    c, used = p01.panel_rest(k)
    i = ORDER.index(k)
    for (pk, oid, lines, cap, spk, ev) in p01.BAL:
        if pk != k:
            continue
        o = p01.OLD[k][0]
        p01.balloon_on(c, lines, int(round(cap * BCAP_K)), o["tail_tip_panel_px"], o["centre_panel_px"], 7300 + i * 11)
    return c, used


def print_piece(k):
    """The panel as a cut print: photo + white scissor margin, its own float RGB and alpha, plus ink border."""
    c, used = panel_img(k)
    (cx, cy), s, deg = LAY[k]
    h0, w0 = c.shape[:2]
    w, h = int(round(w0 * s)), int(round(h0 * s))
    ph = cv2.resize(c, (w, h), interpolation=cv2.INTER_AREA)
    m = 22  # white print margin
    W, H = w + 2 * m, h + 2 * m
    rgb = np.zeros((H, W, 3), np.float32)
    rgb[:] = penlib.PAPER_CUT
    rgb[m:m + h, m:m + w] = ph
    # a thin hand-ruled edge round the photo, like page 01's frames
    bm = penlib.border_mask((H, W), [(m, m, m + w, m + h)], 5, 2700 + ORDER.index(k))
    penlib.ink_onto(rgb, bm)
    # scissor-cut outer edge: a slightly irregular quadrilateral with faceted cuts
    rnd = random.Random(2750 + ORDER.index(k))
    q = [(rnd.uniform(0, 7), rnd.uniform(0, 7)), (W - rnd.uniform(0, 7), rnd.uniform(0, 7)),
         (W - rnd.uniform(0, 7), H - rnd.uniform(0, 7)), (rnd.uniform(0, 7), H - rnd.uniform(0, 7))]
    a = np.zeros((H, W), np.uint8)
    cv2.fillPoly(a, [np.int32(np.array(q) * 4)], 255, cv2.LINE_AA, shift=2)
    return rgb, a, used


def lay(page, rgb, a, centre, deg, lift=0.0):
    H, W = a.shape
    M = cv2.getRotationMatrix2D((W / 2, H / 2), -deg, 1.0)
    M[0, 2] += centre[0] - W / 2
    M[1, 2] += centre[1] - H / 2
    sz = (page.shape[1], page.shape[0])
    A = cv2.warpAffine(a, M, sz, flags=cv2.INTER_LINEAR)
    G = cv2.warpAffine(rgb, M, sz, flags=cv2.INTER_LINEAR)
    penlib.shadow_onto(page, A, off=9 + lift, blur=7 + lift, opacity=0.42)
    af = A.astype(np.float32)[..., None] / 255
    page[:] = page * (1 - af) + G * af
    return M


def tag(page, n, at, seed):
    """A small round paper tag with the reading number, pinned with a brass-headed pin."""
    r = 50
    cx, cy = at
    rnd = random.Random(seed)
    pts = [(cx + r * (1 + rnd.uniform(-0.03, 0.03)) * math.cos(t), cy + r * (1 + rnd.uniform(-0.03, 0.03)) * math.sin(t))
           for t in np.linspace(0, 2 * math.pi, 26, endpoint=False)]
    pm = np.zeros(page.shape[:2], np.uint8)
    cv2.fillPoly(pm, [np.int32(np.array(pts) * 4)], 255, cv2.LINE_AA, shift=2)
    penlib.shadow_onto(page, pm, off=6, blur=4, opacity=0.5)
    comp(page, pm, TAG_PAPER)
    ring = np.zeros(page.shape[:2], np.uint8)
    penlib.brush_line(ring, [(cx + (r - 9) * math.cos(t), cy + (r - 9) * math.sin(t))
                             for t in np.linspace(0.3, 0.3 + 2 * math.pi, 40)], 5, seed + 1)
    comp(page, ring, INK)
    lm = np.zeros(page.shape[:2], np.uint8)
    put_mask(lm, letter([str(n)], 50, seed + 2, weight=0.17), cx + 2, cy + 6)
    comp(page, lm, INK)


def tag_pos(k):
    """Upper-left corner of the print, nudged inward, in page coordinates."""
    rgb, a, _ = PIECES[k]
    H, W = a.shape
    (cx, cy), s, deg = LAY[k]
    M = cv2.getRotationMatrix2D((W / 2, H / 2), -deg, 1.0)
    M[0, 2] += cx - W / 2
    M[1, 2] += cy - H / 2
    p = M @ np.array([20.0, 20.0, 1.0])
    return float(p[0]), float(p[1])


PIECES = {}


def build(tags=8, drop_order=None):
    page = SHEET.copy()
    if not PIECES:
        for k in ORDER:
            PIECES[k] = print_piece(k)
    # prints are dropped in a scattered order (not the reading order), so overlaps say nothing about order
    for k in (drop_order or list(LAY.keys())):
        rgb, a, _ = PIECES[k]
        (cx, cy), s, deg = LAY[k]
        lay(page, rgb, a, (cx, cy), deg)
    for i, k in enumerate(ORDER[:tags]):
        tag(page, i + 1, tag_pos(k), 2790 + i * 7)
    return page


def overlaps():
    """Fraction of each print's area hidden under later-dropped prints (should stay small)."""
    out = {}
    masks = {}
    for k in LAY:
        rgb, a, _ = PIECES[k]
        H, W = a.shape
        (cx, cy), s, deg = LAY[k]
        M = cv2.getRotationMatrix2D((W / 2, H / 2), -deg, 1.0)
        M[0, 2] += cx - W / 2
        M[1, 2] += cy - H / 2
        masks[k] = cv2.warpAffine(a, M, (2200, 2850)) > 127
    keys = list(LAY)
    for i, k in enumerate(keys):
        later = np.zeros((2850, 2200), bool)
        for k2 in keys[i + 1:]:
            later |= masks[k2]
        out[k] = round(float((masks[k] & later).sum() / masks[k].sum()), 3)
    allm = np.zeros((2850, 2200), bool)
    for m in masks.values():
        allm |= m
    ys, xs = np.nonzero(allm)
    return out, [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]


if __name__ == "__main__":
    page = build()
    img, size = save_page(page, N, PID, TITLE)
    ov, bbox = overlaps()
    print("jpeg bytes", size, "hidden fraction", ov, "bbox", bbox)
    if len(sys.argv) > 1 and sys.argv[1] == "beats":
        frames = []
        for t in (0, 2, 4, 6, 8):
            p = np.clip(np.round(build(tags=t)), 0, 255).astype(np.uint8)
            pen99.folio(p, N, TITLE)
            frames.append(np.asarray(Image.fromarray(p).resize((960, 1242), Image.LANCZOS)))
        save_beats(N, frames)

"""99 ways, page 32 "How to forget a key" (pen-hand). An instruction sheet: a parts list and six numbered
imperative steps, each with an arrowed line diagram, teach the reader to forget a key. E0-E5 in order, the four
canon lines verbatim inside the steps, the outcome kept (step 6: leave the key, do not open the door).
All HANDMADE: the shared pen hand (pen99 / penlib) for lettering; the diagrams are pen outlines traced from the
b1m2 control-point figures and scenery (visible part of each piece, occlusion respected) with penlib.brush_line;
arrows, callouts and the 'do not' sign drawn with the same pen. Ground: the LoC 1934 sheet.
Run: python3 -I p32_how_to_forget.py"""
import math
import random
import sys

import cv2
import numpy as np

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import b1m2 as B  # noqa: E402
from b1m2 import agent, stranger, desk, window, clock, cupboard, service_door, Shape, R_  # noqa: E402
import pen99  # noqa: E402
from pen99 import penlib  # noqa: E402

N, PID, TITLE = 32, "how-to-forget", "How to forget a key"
W, H = 2200, 2850
INK = np.array([18, 17, 16], np.float32)
RED = np.array([150, 40, 30], np.float32)      # a second pen for the warning sign only

CELLS = []
for r, y0 in enumerate((790, 1415, 2040)):
    for c, x0 in enumerate((110, 1120)):
        CELLS.append((x0, y0, x0 + 970, y0 + 610))

STEPS = [
    ["Read the memo: \"4:15 - open SERVICE", "door. Key in cupboard.\" Get up and", "set off for the cupboard."],
    ["Halfway across, let a stranger at the", "ticket window stop you:", "\"Pardon me — have you the right time?\""],
    ["Look up at the clock (it says 4:10).", "Answer:", "\"Ten past four, by the clock.\""],
    ["Accept her thanks:", "\"Much obliged!\"", "Let her go. Walk on."],
    ["Open the cupboard. Look straight at", "the brass key on its hook", "(tag: SERVICE)."],
    ["Put your pencil to your chin. Ask:", "\"Well, here I am... and what for?\"", "Leave the key on its hook."],
]


# ------------------------------------------------------------------ pen helpers
def text(mask, s, x, base, cap, seed, weight=0.13):
    m = pen99.letter([s], cap, seed, weight=weight)
    top = int(round(base - cap * 1.15))
    left = int(round(x - cap * 0.6))
    B.blit_mask(mask, m, left, top)


def text_c(mask, s, cx, base, cap, seed, weight=0.13):
    m = pen99.letter([s], cap, seed, weight=weight)
    top = int(round(base - cap * 1.15))
    B.blit_mask(mask, m, int(cx - m.shape[1] / 2), top)
    return m.shape[1] - cap * 1.2


def line(mask, pts, w, seed, tremor=0.7):
    penlib.brush_line(mask, pts, w, seed, tremor)


def circle(mask, cx, cy, r, w, seed, a0=0, a1=360, n=None):
    n = n or max(16, int(r * 0.6))
    pts = [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in np.linspace(a0, a1, n)]
    line(mask, pts, w, seed, 0.4)


def arrow(mask, pts, w, seed, head=26):
    pts = [np.array(p, np.float32) for p in pts]
    if len(pts) == 3:   # quadratic curve through a control point
        a, c, b = pts
        pts = [(1 - t) ** 2 * a + 2 * (1 - t) * t * c + t ** 2 * b for t in np.linspace(0, 1, 30)]
    elif len(pts) == 2:
        pts = [pts[0] + (pts[1] - pts[0]) * t for t in np.linspace(0, 1, 8)]
    line(mask, [tuple(p) for p in pts], w, seed)
    d = pts[-1] - pts[-3]
    d = d / (np.linalg.norm(d) + 1e-6)
    n = np.array([-d[1], d[0]])
    tip = pts[-1]
    line(mask, [tuple(tip - d * head + n * head * 0.55), tuple(tip), tuple(tip - d * head - n * head * 0.55)], w, seed + 1, 0.3)


def dashed(mask, pts, w, seed, dash=22, gap=16):
    p = np.array(pts, np.float32)
    seg = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))])
    L = seg[-1]
    s, k = 0.0, 0
    while s < L:
        e = min(L, s + dash)
        q = [np.array([np.interp(t, seg, p[:, 0]), np.interp(t, seg, p[:, 1])]) for t in np.linspace(s, e, 4)]
        line(mask, [tuple(v) for v in q], w, seed + k, 0.2)
        s = e + gap
        k += 1


def trace(mask, shapes, w, seed, skip=()):
    """Pen outline of b1m2 shapes: visible part of each piece (z-ordered label image), each contour one pen line."""
    pts = np.vstack([s.pts for s in shapes])
    x0, y0 = np.floor(pts.min(0)).astype(int) - 12
    x1, y1 = np.ceil(pts.max(0)).astype(int) + 12
    lw, lh = int(x1 - x0), int(y1 - y0)
    lab = np.zeros((lh * 2, lw * 2), np.int32)
    ordered = sorted(shapes, key=lambda s: s.z)
    for i, s in enumerate(ordered, 1):
        c = (s.curve() - np.array([x0, y0])) * 2
        c = cv2.approxPolyDP(np.int32(c * 4).reshape(-1, 1, 2), 4, True)
        tmp = np.zeros_like(lab, np.uint8)
        cv2.fillPoly(tmp, [c], 255, cv2.LINE_8, shift=2)
        lab[tmp > 0] = 0 if s.hole else i
    k = 0
    for i, s in enumerate(ordered, 1):
        if s.hole or s.role in skip:
            continue
        m = (lab == i).astype(np.uint8)
        if m.sum() < 30:
            continue
        cs, _ = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
        for cc in cs:
            if len(cc) < 12:
                continue
            p = cc[:, 0, :].astype(np.float32) / 2 + np.array([x0, y0])
            p = p[::3]
            p = np.vstack([p, p[:1]])
            k += 1
            line(mask, [tuple(v) for v in p], w, seed + k, 0.35)


def key_outline(mask, kx, ky, scale, w, seed, tag=True, deg=0):
    km = np.zeros(mask.shape, np.uint8)
    B.paste_mask(km, B.key_alpha(), kx, ky, scale, deg)
    km = (km > 120).astype(np.uint8)
    cs, _ = cv2.findContours(km, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    for j, cc in enumerate(cs):
        if len(cc) < 10:
            continue
        p = cc[:, 0, :][::3].astype(np.float32)
        p = np.vstack([p, p[:1]])
        line(mask, [tuple(v) for v in p], w, seed + j, 0.25)
    ys, xs = np.nonzero(km)
    top = ys.min()
    line(mask, [(kx - 22 * scale / 0.3, top - 14), (kx + 2, top - 14), (kx + 2, top + 6)], w + 1, seed + 20)
    if tag:
        tx, ty = kx + 30 * scale / 0.3, ky + 10
        line(mask, [(kx + 4, ky - 30 * scale / 0.3), (tx, ty + 8)], max(2, w - 2), seed + 21, 0.3)
        cap = int(22 * scale / 0.3)
        tw = cap * 5.6
        line(mask, [(tx, ty), (tx + tw, ty + 6), (tx + tw - 4, ty + cap * 1.7), (tx - 2, ty + cap * 1.6), (tx, ty)], w, seed + 22, 0.3)
        text(mask, "SERVICE", tx + cap * 0.5, ty + cap * 1.25, cap, seed + 23, 0.14)
    return (xs.min(), ys.min(), xs.max(), ys.max())


def memo_slip(mask, x, y, cap, seed, lines=("4:15 - open", "SERVICE door.", "Key in cupboard.")):
    w = cap * 9.8
    h = cap * 1.42 * len(lines) + cap * 1.4
    line(mask, [(x, y), (x + w, y + 4), (x + w - 3, y + h), (x + 2, y + h - 3), (x, y)], 4, seed, 0.3)
    for i, l in enumerate(lines):
        text(mask, l, x + cap * 0.6, y + cap * 1.6 + i * cap * 1.42, cap, seed + 1 + i)
    return (x, y, x + w, y + h)


# ------------------------------------------------------------------ the sheet
def header(mask):
    text(mask, "HOW TO FORGET A KEY", 130, 236, 104, 3201, weight=0.15)
    text(mask, "Instruction sheet  /  Randolph station office  /  one person", 134, 330, 40, 3202)
    text(mask, "Time required: 5 minutes (4:10 - 4:15)  /  No tools", 134, 396, 40, 3203)
    line(mask, [(110, 430), (2090, 433)], 7, 3204)


def parts(mask):
    """YOU WILL NEED: six parts, each drawn, each counted."""
    text(mask, "YOU WILL NEED:", 134, 512, 46, 3210, weight=0.15)
    y_lab = 750
    xs = [250, 560, 860, 1180, 1530, 1880]
    # memo
    memo_slip(mask, xs[0] - 115, 560, 25, 3220)
    text_c(mask, "1 x memo", xs[0], y_lab, 36, 3221)
    # pencil
    line(mask, [(xs[1] - 80, 660), (xs[1] + 70, 590)], 14, 3222, 0.2)
    line(mask, [(xs[1] + 70, 590), (xs[1] + 98, 580), (xs[1] + 80, 602)], 5, 3223, 0.2)
    text_c(mask, "1 x pencil", xs[1], y_lab, 36, 3224)
    # clock
    trace(mask, clock(xs[2], 620, 58, hh=4, mm=10, pend=False), 4, 3225)
    text_c(mask, "1 x wall clock", xs[2], y_lab, 36, 3226)
    # stranger at window
    ws, sill = window(xs[3] - 70, 540, 140, 150, sill=670, header=26)
    trace(mask, ws[:5] + stranger(xs[3], 672, face=-1, scale=0.42), 3, 3227)
    text_c(mask, "1 x stranger", xs[3], y_lab, 36, 3228)
    # cupboard
    cup, _ = cupboard(xs[4] - 60, 560, 120, 140)
    trace(mask, cup, 3, 3229)
    text_c(mask, "1 x cupboard", xs[4], y_lab, 36, 3230)
    # key
    key_outline(mask, xs[5] - 40, 625, 0.17, 3, 3231)
    text_c(mask, "1 x brass key", xs[5], y_lab, 36, 3232)


def step_frame(mask, i, cell):
    x0, y0, x1, y1 = cell
    sd = 3300 + i * 40
    for k, (a, b) in enumerate((((x0, y0), (x1, y0 + 1)), ((x1, y0), (x1 - 1, y1)), ((x1, y1), (x0, y1 - 1)), ((x0, y1), (x0 + 1, y0)))):
        line(mask, [a, b], 5, sd + k, 0.6)
    circle(mask, x0 + 66, y0 + 66, 44, 7, sd + 5)
    text_c(mask, str(i + 1), x0 + 66, y0 + 66 + 26, 58, sd + 6, weight=0.16)
    for j, l in enumerate(STEPS[i]):
        text(mask, l, x0 + 136, y0 + 66 + j * 60, 40, sd + 10 + j)


def diag1(m, cell):
    x0, y0, x1, y1 = cell
    fy = y1 - 40
    dk = desk(x0 + 190, fy - 150, 220, fy)
    for s_ in dk:
        s_.z += 20
    trace(m, agent(x0 + 110, fy, face=1, scale=0.36, legs=(14, -6), lean=10, tilt=4, sh=34, el=-20, pencil_deg=200) + dk, 4, 3403)
    memo_slip(m, x0 + 250, fy - 222, 16, 3402)
    cup, _ = cupboard(x1 - 200, fy - 230, 130, 230)
    trace(m, cup, 4, 3404)
    arrow(m, [(x0 + 400, fy - 240), (x0 + 580, fy - 340), (x1 - 220, fy - 160)], 6, 3405)
    dashed(m, [(x0 + 110, fy + 14), (x1 - 210, fy + 14)], 4, 3406)
    text_c(m, "you", x0 + 110, fy + 2 - 330 * 1.0, 30, 3407)


def diag2(m, cell):
    x0, y0, x1, y1 = cell
    fy = y1 - 40
    ws, sill = window(x1 - 330, fy - 320, 200, 320, sill=fy - 130, header=52)
    trace(m, ws[:5] + stranger(x1 - 230, fy - 128, face=-1, scale=0.56), 4, 3411)
    text_c(m, "TICKET", x1 - 230, fy - 320 + 40, 24, 3412)
    trace(m, agent(x0 + 300, fy, face=1, scale=0.36, sh=10, el=24, pencil_deg=200), 4, 3413)
    dashed(m, [(x0 + 60, fy + 14), (x0 + 300, fy + 14)], 4, 3414)
    # the path to the cupboard, interrupted: a stop bar
    dashed(m, [(x0 + 360, fy + 14), (x0 + 470, fy + 14)], 4, 3415)
    line(m, [(x0 + 480, fy - 10), (x0 + 480, fy + 38)], 8, 3416, 0.2)
    arrow(m, [(x1 - 360, fy - 220), (x0 + 520, fy - 280), (x0 + 430, fy - 250)], 5, 3417)
    text_c(m, "?", x0 + 560, fy - 300, 60, 3418)


def diag3(m, cell):
    x0, y0, x1, y1 = cell
    fy = y1 - 40
    cx, cy = x1 - 320, fy - 220
    trace(m, clock(cx, cy, 100, hh=4, mm=10, pend=False), 4, 3421)
    for k, (dx, dy) in enumerate(((0, -76), (76, 0), (0, 76), (-76, 0))):
        pass
    text_c(m, "4:10", cx, cy + 162, 40, 3422)
    trace(m, agent(x0 + 200, fy, face=1, scale=0.36, legs=(3, -3), tilt=-24, sh=6, el=20, pencil_deg=190), 4, 3423)
    # eye-line
    dashed(m, [(x0 + 222, fy - 268), (cx - 110, cy - 20)], 4, 3424)
    arrow(m, [(cx - 150, cy - 10), (cx - 110, cy - 18)], 4, 3425, head=20)


def diag4(m, cell):
    x0, y0, x1, y1 = cell
    fy = y1 - 40
    ws, sill = window(x0 + 330, fy - 320, 220, 320, sill=fy - 130, header=52)
    trace(m, ws[:5] + stranger(x0 + 470, fy - 128, face=1, scale=0.56), 4, 3431)
    text_c(m, "TICKET", x0 + 440, fy - 320 + 40, 24, 3432)
    arrow(m, [(x0 + 600, fy - 220), (x0 + 700, fy - 250), (x1 - 40, fy - 230)], 6, 3434)
    text_c(m, "to the platform", x1 - 170, fy - 170, 28, 3435)
    trace(m, agent(x0 + 120, fy, face=1, scale=0.36, legs=(22, -20), sh=-22, el=24, lean=4, pencil_deg=200), 4, 3436)
    arrow(m, [(x0 + 40, fy + 16), (x0 + 270, fy + 16)], 5, 3437)
    text_c(m, "on to the cupboard", x0 + 160, fy + 2 - 330, 26, 3438)


def diag5(m, cell):
    x0, y0, x1, y1 = cell
    fy = y1 - 40
    cup, ins = cupboard(x0 + 310, fy - 280, 170, 280, open_deg=112)
    trace(m, cup, 4, 3441)
    ix0, iy0, ix1, iy1 = ins
    kx, ky = (ix0 + ix1) / 2 + 6, iy0 + 72
    key_outline(m, kx, ky, 0.12, 3, 3442, tag=False)
    trace(m, agent(x0 + 110, fy, face=1, scale=0.36, legs=(14, -12), sh=64, el=18, pencil_deg=200), 4, 3443)
    # magnifier callout
    zx, zy, zr = x1 - 210, fy - 200, 150
    circle(m, zx, zy, zr, 6, 3444)
    line(m, [(kx + 14, ky - 10), (zx - zr * 0.96, zy - zr * 0.28)], 3, 3445, 0.2)
    line(m, [(kx + 14, ky + 50), (zx - zr * 0.92, zy + zr * 0.38)], 3, 3446, 0.2)
    key_outline(m, zx - 40, zy, 0.30, 4, 3447, tag=True)
    text_c(m, "LOOK", x0 + 280, fy - 300, 34, 3448, weight=0.15)
    arrow(m, [(x0 + 330, fy - 310), (x0 + 380, fy - 330), (kx - 16, ky - 40)], 5, 3449, head=20)


def diag6(m, red, cell):
    x0, y0, x1, y1 = cell
    fy = y1 - 40
    cup, ins = cupboard(x0 + 300, fy - 280, 170, 280, open_deg=112)
    trace(m, cup, 4, 3451)
    ix0, iy0, ix1, iy1 = ins
    kx, ky = (ix0 + ix1) / 2 + 6, iy0 + 72
    key_outline(m, kx, ky, 0.12, 3, 3452, tag=False)
    trace(m, service_door(x0 + 560, fy - 300, 130, 300), 4, 3453)
    line(m, [(x0 + 575, fy - 266), (x0 + 675, fy - 264), (x0 + 674, fy - 232), (x0 + 576, fy - 234), (x0 + 575, fy - 266)], 3, 3454, 0.2)
    text_c(m, "SERVICE", x0 + 625, fy - 240, 17, 3455)
    trace(m, agent(x0 + 100, fy, face=1, scale=0.36, legs=(3, -3), sh=50, el=120, wr=8, pencil_deg=40, tilt=6), 4, 3456)
    text_c(m, "?", x0 + 215, fy - 270, 64, 3457, weight=0.14)
    # the 'do not' signs: over a hand taking the key, over the opening door
    for k, (cx, cy) in enumerate(((x1 - 150, fy - 230), (x1 - 150, fy - 70))):
        circle(red, cx, cy, 62, 7, 3460 + k * 5)
        line(red, [(cx - 44, cy - 44), (cx + 44, cy + 44)], 7, 3461 + k * 5, 0.2)
    key_outline(m, x1 - 150, fy - 238, 0.07, 3, 3470, tag=False)
    # little door with arrow (opening) under the second sign
    line(m, [(x1 - 180, fy - 40), (x1 - 180, fy - 110), (x1 - 130, fy - 110), (x1 - 130, fy - 40)], 3, 3471, 0.2)
    arrow(m, [(x1 - 172, fy - 76), (x1 - 136, fy - 76)], 3, 3472, head=10)


DIAGS = [diag1, diag2, diag3, diag4, diag5, None]


def build(n_steps=6):
    page = cv2.GaussianBlur(pen99.sheet99().astype(np.float32), (0, 0), 0.6)   # paper grain softened a touch (file-size target)
    ink = np.zeros((H, W), np.uint8)
    red = np.zeros((H, W), np.uint8)
    header(ink)
    parts(ink)
    for i in range(n_steps):
        cell = CELLS[i]
        step_frame(ink, i, cell)
        dc = (cell[0], cell[1] + 220, cell[2], cell[3])
        if i == 5:
            diag6(ink, red, dc)
        else:
            DIAGS[i](ink, dc)
    if n_steps == 6:
        text(ink, "Result: the key stays on its hook; the SERVICE door stays shut.", 134, 2712, 38, 3490)
    penlib.ink_onto(page, ink, INK)
    penlib.ink_onto(page, red, RED, alpha=0.9)
    return page


def main():
    page = build()
    img, size = B.save_page(page.copy(), N, PID, TITLE)
    frames = []
    for n in range(0, 6):
        f = build(n)
        pen99.folio(f, N, TITLE)
        frames.append(f)
    frames.append(img.astype(np.float32))
    nb = B.save_beats(N, frames)
    print("bytes", size, "beats", nb)


if __name__ == "__main__":
    main()

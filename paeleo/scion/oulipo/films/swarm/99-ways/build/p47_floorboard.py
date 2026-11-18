"""Page 47 Floorboard (point of view; medium: shadow-puppet).

The camera lies on the office floor. Every panel is a lit shadow screen (page 05's screen: lamp hotspot, the LoC
1934 sheet as paper fibre) with black cut-paper puppets pressed on it: the floor itself is a black strip whose
board seams are cut as slits that let the light through, converging to a vanishing point just above the floor
line; boots, trouser legs, chair and desk legs stand on it at the size a floor-level eye sees them, so the frame
cuts every figure at the knee or thigh. No face, no torso: the b1m2 agent puppet is laid at 2-3x so that his hip
lies above the panel top. Beyond the counter (an old counter on legs, open below) the stranger is only her hem,
ankles and shoes, held back from the screen (soft and grey). The clock, the open cupboard and the brass key on its
hook are seen from below, high up in the frame. Lines come down from above in balloons whose tails leave the panel
top. Run: python3 -I p47_floorboard.py [beats]"""
import json
import math
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
from b1m2 import *  # noqa
from p05_noir import screen, sil, far, brass_key, SIL, BOXES, cap_slip  # noqa

N, PID, TITLE = 47, "floorboard", "Floorboard"
BCAP = 46
LIGHT = np.array([226, 214, 186], np.float32)
WARM = np.array([238, 220, 170], np.float32)

Q = ["Pardon me —", "have you the", "right time?"]
A_ = ["Ten past four,", "by the clock."]
TH = ["Much", "obliged!"]
F = ["Well, here I am...", "and what for?"]


# ------------------------------------------------------------------ floor-level pieces (HANDMADE cut paper)
def floor_strip(img, horizon, vp_x, seed, n=16, lit=LIGHT):
    """The floor: a dim grey board strip below the floor line (a grey paper gel); the board seams cut in black, converging to (vp_x, horizon-40)."""
    h, w = img.shape[:2]
    m = np.zeros((h, w), np.uint8)
    m[horizon:] = 255
    yy = np.arange(h, dtype=np.float32)[:, None]
    ramp = np.clip((yy - horizon) / max(1, h - horizon), 0, 1)
    floor_col = np.array([112, 100, 86], np.float32)
    comp(img, m, floor_col)
    img *= (1 - 0.35 * ramp[..., None] * (m[..., None] > 0))      # the boards darken toward the camera
    slits = np.zeros((h, w), np.uint8)
    vy = horizon - 40
    for k in range(-n, n + 1):
        xb = vp_x + k * w / 7.0
        y0 = horizon + 3
        t0 = (y0 - vy) / (h - vy)
        x0 = vp_x + (xb - vp_x) * t0
        penlib.brush_line(slits, [(x0, y0), (xb, h)], max(1.5, 1.2 + abs(k) * 0.25), seed + k, tremor=0.3)
    # cross joints (board ends), a few, foreshortened
    for j, yy in enumerate((horizon + 14, horizon + 40, horizon + 90)):
        x_a = (j * 211 + seed * 37) % max(1, w - 200)
        penlib.brush_line(slits, [(x_a, yy), (x_a + 120 + 40 * j, yy)], 1.6, seed + 50 + j, tremor=0.2)
    comp(img, slits, SIL, 0.75)


HIPS = []
BOOT = [(-46, 318), (44, 318), (54, 336), (92, 346), (122, 360), (128, 384), (-50, 384), (-54, 350)]


def legs(x, floor, face, s, step=(8, -8), lean=0):
    """The agent puppet's legs at floor-eye scale (b1m2 TROUSER outline, his hip above the frame) with HANDMADE
    laced boots; the torso and everything above it is never laid."""
    s = max(s, (floor + 30) / 380.0)           # the rule: his hip (waist) always lies above the panel top
    hip_h = 380 * s
    HIPS.append(float(floor - hip_h))
    base = Mx(x, floor - hip_h, 0, s, face < 0) @ Mx(0, 0, lean)
    out = []
    for k, a in enumerate(step):
        L = base @ Mx(0, 0, -a)
        out.append(Shape(tf(L, TROUSER), "trousers", z=-1 if k == 1 else 0))
        out.append(Shape(tf(L, BOOT), "boot", smooth=False, z=-1 if k == 1 else 0))
        for j in range(3):                                  # lace holes: light through the boot
            out.append(Shape(tf(L, circle_pts(20 + j * 16, 336 + j * 4, 3.2, 8)), "lace", hole=True, z=1))
        out.append(Shape(tf(L, bar_pts((-50, 372), (126, 372), 3)), "welt", hole=True, smooth=False, z=1))
    return out


def chair(x, floor, s=1.0, skew=0.0):
    """A wooden office chair from floor level: four legs, a stretcher, the seat's underside at the top."""
    out = []
    top = floor - 470 * s
    for dx, f in ((-150, 1.0), (150, 1.0), (-95, 0.86), (95, 0.86)):
        xb = x + dx * s + skew * 60
        xt = x + dx * s * 0.92 + skew * 20
        fl = floor - (1 - f) * 120 * s
        out.append(Shape(bar_pts((xt, top), (xb, fl), 22 * s * f), "chair", smooth=False))
    out.append(Shape(bar_pts((x - 150 * s, floor - 160 * s), (x + 150 * s, floor - 160 * s), 14 * s), "chair", smooth=False))
    out.append(R_(x - 175 * s + skew * 20, top - 40 * s, x + 175 * s + skew * 20, top, "chair"))
    return out


def desk_legs(x0, x1, floor, top):
    s = [R_(x0, top, x0 + 40, floor, "desk"), R_(x1 - 40, top, x1, floor, "desk"), R_(x0 - 20, top - 30, x1 + 20, top, "desk"),
         R_(x1 - 260, top, x1 - 40, floor - 30, "desk")]
    s.append(R_(x1 - 230, top + 60, x1 - 70, top + 66, "slit", hole=True, z=1))
    s.append(Shape(circle_pts(x1 - 150, top + 100, 9, 10), "slit", hole=True, z=1))
    return s


def counter(x0, x1, floor, top, kick=230):
    """The ticket counter on its legs, open below: a top board and a front panel stopping `kick` px above the floor."""
    return [R_(x0, top, x1, floor - kick, "counter"), R_(x0, floor - kick, x0 + 34, floor, "counter"),
            R_(x1 - 34, floor - kick, x1, floor, "counter"), R_(x0 - 30, top - 26, x1 + 30, top, "counter")]


def hem_and_shoes(x, floor, s=1.0, face=1, step=0.0):
    """HANDMADE: the stranger's skirt hem, ankles and shoes (Louis heel), the only part of her a floor eye sees."""
    f = face
    out = []
    hem_y = floor - 210 * s
    pts = [(x - 120 * s, hem_y - 700 * s), (x + 120 * s, hem_y - 700 * s), (x + 150 * s + step * 20, hem_y)]
    for k in range(7):                                   # scalloped hem
        t = 1 - k / 6
        xx = x - 150 * s + 300 * s * t + step * 20
        pts.append((xx, hem_y + (12 * s if k % 2 else 0)))
    pts.append((x - 150 * s + step * 20, hem_y))
    out.append(Shape(pts, "skirt", smooth=False))
    for k, (dx, lift) in enumerate(((-45, 0.0), (45, step))):
        ax = x + dx * s + (step * 40 * s if k == 1 else 0)
        fy = floor - lift * 40 * s
        out.append(Shape(bar_pts((ax, hem_y - 10 * s), (ax, fy - 40 * s), 26 * s), "ankle", smooth=False))
        shoe = [(ax - 30 * s * f, fy - 44 * s), (ax + 10 * s * f, fy - 50 * s), (ax + 60 * s * f, fy - 18 * s),
                (ax + 74 * s * f, fy), (ax - 4 * s * f, fy), (ax - 16 * s * f, fy - 14 * s), (ax - 24 * s * f, fy),
                (ax - 34 * s * f, fy)]
        out.append(Shape(shoe, "shoe", smooth=False))
    return out


def cupboard_from_below(img, x0, x1, top, bottom, open_frac, seed, key=True):
    """The cupboard seen from the floor: its plinth, the lit inside up high, the door leaf swung toward us on the
    left jamb; the key on its hook seen from below (foreshortened, high in the inside)."""
    h, w = img.shape[:2]
    inside = np.zeros((h, w), np.uint8)
    cv2.rectangle(inside, (x0 + 26, top + 20), (x1 - 26, bottom - 70), 255, -1)
    sh = [R_(x0, top - 30, x1, top + 20, "cup"), R_(x0, top, x0 + 26, bottom, "cup"), R_(x1 - 26, top, x1, bottom, "cup"),
          R_(x0 - 14, bottom - 70, x1 + 14, bottom, "cup")]
    shelf_y = int(top + (bottom - top) * 0.52)
    sh.append(R_(x0 + 26, shelf_y, x1 - 26, shelf_y + 22, "cup"))
    if open_frac <= 0:
        sh.append(R_(x0 + 26, top + 20, x1 - 26, bottom - 70, "cup"))
    m = raster(sh, w, h)
    if open_frac > 0:
        comp(img, inside, WARM, 0.85)
    comp(img, m, SIL)
    info = {}
    if open_frac > 0:
        dw = (x1 - x0) * open_frac
        leaf = [Shape([(x0, top - 10), (x0 - dw, top - 40), (x0 - dw, bottom + 30), (x0, bottom)], "door", smooth=False)]
        comp(img, raster(leaf, w, h), SIL)
        if key:
            kx, ky = (x0 + x1) / 2, top + 40
            hk = raster([Shape(bar_pts((kx - 4, top + 16), (kx - 4, ky), 10), "h", smooth=False)], w, h)
            comp(img, hk, SIL)
            brass_key(img, kx + 4, ky + 120, 0.30, deg=0, glow=True)
            tag = np.zeros((h, w), np.uint8)
            cv2.fillPoly(tag, [np.int32([(kx + 20, ky + 150), (kx + 120, ky + 170), (kx + 114, ky + 210), (kx + 14, ky + 190)])], 255, cv2.LINE_AA)
            comp(img, tag, np.array([238, 230, 206], np.float32))
            lm = np.zeros((h, w), np.uint8)
            put_mask(lm, letter(["SERVICE"], 20, seed, weight=0.17), int(kx + 67), int(ky + 182))
            comp(img, lm, SIL)
            info = dict(key_px=[kx, ky + 120])
    return info


def service_door_from_below(img, x0, x1, top, bottom):
    """The SERVICE door, shut, from the floor: its lower panels and a line of light under it."""
    h, w = img.shape[:2]
    sd = [R_(x0, top, x1, bottom - 8, "sdoor")]
    for (a, b) in ((0.15, 0.85),):
        for e in (rect(x0 + (x1 - x0) * a, top + 80, x0 + (x1 - x0) * b, top + 86),
                  rect(x0 + (x1 - x0) * a, bottom - 120, x0 + (x1 - x0) * b, bottom - 114),
                  rect(x0 + (x1 - x0) * a, top + 80, x0 + (x1 - x0) * a + 6, bottom - 114),
                  rect(x0 + (x1 - x0) * b - 6, top + 80, x0 + (x1 - x0) * b, bottom - 114)):
            sd.append(Shape(e, "slit", hole=True, smooth=False, z=1))
    comp(img, raster(sd, w, h), SIL)
    gap = np.zeros((h, w), np.uint8)
    cv2.rectangle(gap, (x0 + 6, bottom - 8), (x1 - 6, bottom), 255, -1)
    comp(img, cv2.GaussianBlur(gap, (0, 0), 1.5), WARM)


def wall_clock_high(img, cx, cy, r, seed):
    s = clock(cx, cy, r, hh=4, mm=10, swing=6)
    comp(img, raster(s, img.shape[1], img.shape[0]), SIL)


def down_balloon(img, lines, x, y, tip_x, seed, cap=BCAP):
    """Balloon whose tail rises out of the panel top: the speaker is above the frame."""
    return balloon(img, lines, cap, (x, y), (tip_x, -60), seed, tail_w=0.26, bend=0.08)


# ------------------------------------------------------------------ panels
def pnl(key, hot=(0.5, 0.42)):
    x0, y0, x1, y1 = BOXES[key]
    w, h = x1 - x0, y1 - y0
    return screen(w, h, x0, y0, hot=hot, spread=0.95), w, h


def P1(st):     # E0: under the desk
    img, w, h = pnl("P1", (0.55, 0.45))
    hz = h - 120
    floor_strip(img, hz, w * 0.52, 4701)
    comp(img, raster(desk_legs(140, 640, hz + 2, 330), w, h), SIL)
    comp(img, raster(chair(560, hz + 30, s=0.95), w, h), SIL)
    comp(img, raster(legs(470, hz + 70, 1, 2.05, step=(4, -14)), w, h), SIL)
    cap_slip(img, "4:09. Up on the desk, out of sight, the memo: 4:15, open the SERVICE door; key in cupboard.", 600, 4702)
    return img


def P2(st):     # E0: he gets up and sets off
    img, w, h = pnl("P2", (0.40, 0.45))
    hz = h - 120
    floor_strip(img, hz, w * 0.6, 4711)
    comp(img, raster(chair(200, hz + 24, s=0.95, skew=0.6), w, h), SIL)
    comp(img, raster(legs(560, hz + 70, 1, 2.05, step=(26, -22), lean=4), w, h), SIL)
    cap_slip(img, "The chair scrapes back. The boots set off.", 470, 4712)
    return img


def P3(st):     # E1: the question
    img, w, h = pnl("P3", (0.40, 0.52))
    hz = h - 110
    floor_strip(img, hz, w * 0.45, 4721)
    cnt = counter(-40, 380, hz + 4, 140, kick=300)
    far(img, hem_and_shoes(200, hz - 6, s=0.55, face=1), blur=2.2)
    comp(img, raster(cnt, w, h), SIL)
    comp(img, raster(legs(560, hz + 70, -1, 2.05, step=(6, -6)), w, h), SIL)
    down_balloon(img, Q, 200, 330, 120, 4722)
    cap_slip(img, "Beyond the counter: a hem.", 440, 4723)
    return img


def P4(st):     # E2: the answer; the clock up the wall
    img, w, h = pnl("P4", (0.5, 0.25))
    hz = h - 110
    floor_strip(img, hz, w * 0.5, 4732)
    wall_clock_high(img, 420, 230, 80, 4731)
    comp(img, raster(legs(170, hz + 70, 1, 2.05, step=(2, -2)), w, h), SIL)
    down_balloon(img, A_, 330, 520, 120, 4733)
    cap_slip(img, "Up the wall: 4:10.", 420, 4734)
    return img


def P5(st):     # E3: the thanks, she goes
    img, w, h = pnl("P5", (0.42, 0.52))
    hz = h - 110
    floor_strip(img, hz, w * 0.45, 4741)
    cnt = counter(-40, 340, hz + 4, 140, kick=300)
    far(img, hem_and_shoes(130, hz - 6, s=0.55, face=-1, step=1.0), blur=2.2)
    comp(img, raster(cnt, w, h), SIL)
    comp(img, raster(legs(480, hz + 70, -1, 2.05, step=(6, -6)), w, h), SIL)
    down_balloon(img, TH, 190, 330, 120, 4742)
    cap_slip(img, "The hem turns away.", 420, 4743)
    return img


def P6(st):     # E4: the cupboard opens; the key from below
    img, w, h = pnl("P6", (0.5, 0.35))
    hz = h - 110
    floor_strip(img, hz, w * 0.45, 4752)
    info = cupboard_from_below(img, 260, 620, 80, hz + 4, 0.42, 4751)
    comp(img, raster(legs(760, hz + 70, -1, 2.05, step=(10, -12)), w, h), SIL)
    cap_slip(img, "The cupboard door swings open. High up, on its hook: the key.", 430, 4753, y=h - 330)
    st["P6"] = info
    return img


def P7(st):     # E5: the forgetting
    img, w, h = pnl("P7", (0.42, 0.38))
    hz = h - 110
    floor_strip(img, hz, w * 0.5, 4762)
    info = cupboard_from_below(img, 150, 470, 80, hz + 4, 0.42, 4761)
    service_door_from_below(img, 800, 1010, 140, hz + 4)
    comp(img, raster(legs(610, hz + 70, -1, 2.05, step=(2, -3)), w, h), SIL)
    down_balloon(img, F, 700, 150, 600, 4763)
    cap_slip(img, "The boots stand still. The key stays. Under the SERVICE door, light: it stays shut.", 430, 4764, y=h - 330)
    st["P7"] = info
    return img


PANELS = [("P1", P1), ("P2", P2), ("P3", P3), ("P4", P4), ("P5", P5), ("P6", P6), ("P7", P7)]


def build(upto=7):
    page = pen99.sheet99()
    st = {}
    boxes = []
    for i, (k, fn) in enumerate(PANELS):
        if i >= upto:
            continue
        x0, y0, x1, y1 = BOXES[k]
        page[y0:y1, x0:x1] = fn(st)
        boxes.append(BOXES[k])
    frame_border(page, boxes, w=12, seed=4790)
    return page, st


if __name__ == "__main__":
    page, st = build(7)
    img, size = save_page(page, N, PID, TITLE)
    print("jpeg bytes", size)
    if len(sys.argv) > 1 and sys.argv[1] == "beats":
        frames = []
        for u in range(1, 8):
            p, _ = build(u)
            p = np.clip(np.round(p), 0, 255).astype(np.uint8)
            pen99.folio(p, N, TITLE)
            frames.append(p)
        save_beats(N, frames)

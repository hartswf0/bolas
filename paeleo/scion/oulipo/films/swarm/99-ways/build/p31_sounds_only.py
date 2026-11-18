"""99 ways, page 31 "Sounds only" (charcoal-card). No words: the incident is told in sound lettering
(scrape, tap, tick, tok, creak) and the four lines become wordless balloons that carry only their rhythm
(one charcoal dash per syllable at its pitch, stressed syllables heavier) and their end mark (? . ! ...?).
Articulated grey-card puppets with brass split pins, charcoal rubbed in, pinned on the teuf-teuf rock wall.
Run: python3 -I p31_sounds_only.py"""
import json
import math
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import charcoal99 as C  # noqa: E402
import b1m2 as B  # noqa: E402
from b1m2 import agent, stranger, desk, window, clock, cupboard, service_door, Shape, R_, circle_pts  # noqa: E402
import pen99  # noqa: E402
from pen99 import penlib  # noqa: E402

N, PID, TITLE = 31, "sounds-only", "Sounds only"
W, H = 2200, 2850
G = 40
ROWS = [(110, 956), (996, 1842), (1882, 2728)]
BOXES = [(110, ROWS[0][0], 1080, ROWS[0][1]), (1120, ROWS[0][0], 2090, ROWS[0][1]),
         (110, ROWS[1][0], 743, ROWS[1][1]), (783, ROWS[1][0], 1416, ROWS[1][1]), (1457, ROWS[1][0], 2090, ROWS[1][1]),
         (110, ROWS[2][0], 1080, ROWS[2][1]), (1120, ROWS[2][0], 2090, ROWS[2][1])]

# the four lines as rhythm only: (pitch -1..1, stressed) per syllable; ('|', px) pause; ('g', mark, cap)
Q = [(0.05, True), (-0.15, False), (-0.05, False), ("|", 34), (0.0, False), (-0.1, False), (-0.2, False),
     (0.25, True), (0.75, True), ("g", "?", 84, -10)]                     # Pardon me - have you the right time?
A_ = [(0.35, True), (0.2, True), (0.05, True), ("|", 30), (-0.05, False), (-0.15, False), (-0.55, True),
      ("g", ".", 92, 20)]                                                  # Ten past four, by the clock.
T_ = [(0.35, True), (0.0, False), (0.7, True), ("g", "!", 84, -4)]       # Much obliged!
F_ = [(0.25, True), ("|", 30), (0.0, False), (-0.1, False), (-0.25, True), ("g", "...", 70, 28), ("|", 26),
      (-0.2, False), (0.15, True), (0.6, True), ("g", "?", 80, -10)]     # Well, here I am... and what for?

FLOOR_TONE = 0.30


def floor_band(lum, fy, seed):
    """A rubbed charcoal floor: the ground line and a dark band below it."""
    h, w = lum.shape
    yy = np.arange(h)[:, None].astype(np.float32)
    g = C.grain(h, w, seed, 2.0)
    band = np.clip((yy - fy) / 18.0, 0, 1) * (0.55 + 0.1 * g)
    lum *= (1 - band * 0.62)
    C.charcoal_line(lum, [(0, fy), (w * 0.5, fy + 2), (w, fy - 1)], 7, seed + 1, tremor=1.4)


def memo_card(lum, x, y, w, h, seed, deg=-4):
    """The memo as a pale card: '4:15', a key drawn, an arrow to a cupboard drawn. No words."""
    m = np.zeros(lum.shape, np.uint8)
    pts = np.array([(x, y), (x + w, y + 3), (x + w - 2, y + h), (x + 2, y + h - 2)], np.float32)
    c = pts.mean(0)
    a = math.radians(deg)
    R = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
    pts = (pts - c) @ R.T + c
    cv2.fillPoly(m, [np.int32(pts * 4)], 255, cv2.LINE_AA, shift=2)
    C.drop(lum, m, (4, 6), 3, 0.35)
    C.card_piece(lum, m, 0.95, seed, edge=0.05, rub=0.02)
    d = np.zeros(lum.shape, np.uint8)
    t = pen99.letter(["4:15"], 44, seed + 1, weight=0.15)
    C.place(d, t, x + w * 0.30, y + h * 0.30, deg)
    def P(px, py):   # memo-local point -> canvas, rotated with the card
        p = np.array([x + px, y + py]) - c
        return tuple(R @ p + c)
    # key pictogram
    kx, ky = w * 0.66, h * 0.30
    pts_ring = [P(kx - 30 + 12 * math.cos(t_), ky + 12 * math.sin(t_)) for t_ in np.linspace(0, 6.3, 20)]
    penlib.brush_line(d, pts_ring, 4, seed + 2, 0.3)
    penlib.brush_line(d, [P(kx - 18, ky), P(kx + 34, ky)], 4, seed + 3, 0.3)
    penlib.brush_line(d, [P(kx + 22, ky), P(kx + 22, ky + 12)], 4, seed + 4, 0.3)
    penlib.brush_line(d, [P(kx + 32, ky), P(kx + 32, ky + 10)], 4, seed + 5, 0.3)
    # arrow -> cupboard pictogram
    ay = h * 0.70
    penlib.brush_line(d, [P(w * 0.12, ay), P(w * 0.58, ay)], 4, seed + 6, 0.4)
    penlib.brush_line(d, [P(w * 0.50, ay - 12), P(w * 0.59, ay), P(w * 0.50, ay + 12)], 4, seed + 7, 0.3)
    bx = w * 0.68
    for a_, b_ in (((bx, ay - 34), (bx + 52, ay - 34)), ((bx + 52, ay - 34), (bx + 52, ay + 30)),
                   ((bx + 52, ay + 30), (bx, ay + 30)), ((bx, ay + 30), (bx, ay - 34)),
                   ((bx + 26, ay - 34), (bx + 26, ay + 30))):
        penlib.brush_line(d, [P(*a_), P(*b_)], 4, seed + 8, 0.3)
    al = C.rub_mask(d, seed + 9, smear=(2, 1), keep=0.95)
    lum[:] = lum * (1 - al) + 0.08 * al


def key_card(lum, kx, ky, scale, seed, deg=0.0):
    """The brass key as a light card cut on the ANRC key silhouette (99-ways-template cutout), on its hook,
    with a blank paper tag on a string."""
    h, w = lum.shape
    km = np.zeros((h, w), np.uint8)
    B.paste_mask(km, B.key_alpha(), kx, ky, scale, deg)
    km = np.where(km > 120, 255, 0).astype(np.uint8)
    ys, xs = np.nonzero(km)
    top = ys.min()
    hk = np.zeros((h, w), np.uint8)
    penlib.brush_line(hk, [(kx - 26, top - 16), (kx + 2, top - 16), (kx + 2, top + 8)], 8, seed)
    a = C.rub_mask(hk, seed)
    lum[:] = lum * (1 - a) + 0.1 * a
    C.drop(lum, km, (4, 5), 2.5, 0.35)
    C.card_piece(lum, km, 0.80, seed + 1, edge=0.25)
    # tag: blank card on a string
    tx, ty = kx + 26, ky + (ys.max() - ky) * 0.15
    st = np.zeros((h, w), np.uint8)
    penlib.brush_line(st, [(kx + 4, ky - 10), (tx + 14, ty + 6)], 3, seed + 2, 0.4)
    a = C.rub_mask(st, seed + 3)
    lum[:] = lum * (1 - a) + 0.15 * a
    tg = np.zeros((h, w), np.uint8)
    pts = np.array([(tx, ty), (tx + 70, ty + 8), (tx + 64, ty + 46), (tx - 6, ty + 38)], np.float32)
    cv2.fillPoly(tg, [np.int32(pts * 4)], 255, cv2.LINE_AA, shift=2)
    C.drop(lum, tg, (3, 4), 2, 0.3)
    C.card_piece(lum, tg, 0.93, seed + 4, edge=0.05)
    return km


def service_card(lum, x, y, seed):
    """The SERVICE card, without its word: a pale card carrying the key drawn small (the door the key opens)."""
    m = np.zeros(lum.shape, np.uint8)
    cv2.fillPoly(m, [np.int32(np.array([(x, y), (x + 120, y + 2), (x + 119, y + 56), (x + 1, y + 54)]) * 4)], 255,
                 cv2.LINE_AA, shift=2)
    C.drop(lum, m, (3, 4), 2, 0.3)
    C.card_piece(lum, m, 0.94, seed, edge=0.05, rub=0.02)
    d = np.zeros(lum.shape, np.uint8)
    cx, cy = x + 34, y + 28
    penlib.brush_line(d, [(cx - 13 + 11 * math.cos(t), cy + 11 * math.sin(t)) for t in np.linspace(0, 6.3, 18)], 4, seed + 1, 0.2)
    penlib.brush_line(d, [(cx - 2, cy), (cx + 62, cy)], 4, seed + 2, 0.2)
    penlib.brush_line(d, [(cx + 48, cy), (cx + 48, cy + 13)], 4, seed + 3, 0.2)
    penlib.brush_line(d, [(cx + 59, cy), (cx + 59, cy + 10)], 4, seed + 4, 0.2)
    a = C.rub_mask(d, seed + 5)
    lum[:] = lum * (1 - a) + 0.08 * a


def chair(x, floor, back_deg=-10):
    seat_y = floor - 230
    s = [R_(x - 70, seat_y, x + 70, seat_y + 20, "chair"),
         Shape(B.bar_pts((x - 60, seat_y + 20), (x - 66, floor), 16), "chair", smooth=False),
         Shape(B.bar_pts((x + 60, seat_y + 20), (x + 66, floor), 16), "chair", smooth=False)]
    a = math.radians(back_deg)
    top = (x - 70 + 260 * math.sin(a), seat_y - 260 * math.cos(a))
    s.append(Shape(B.bar_pts((x - 66, seat_y + 10), top, 18), "chair", smooth=False))
    s.append(Shape(B.bar_pts((x - 66 + 200 * math.sin(a), seat_y - 200 * math.cos(a)),
                             (x + 10 + 200 * math.sin(a), seat_y - 190 * math.cos(a)), 14), "chair", smooth=False, z=1))
    return s


# ------------------------------------------------------------------ panels
def P1(st):
    w, h = 970, 846
    lum = C.wall(w, h, 3101)
    fy = 742
    floor_band(lum, fy, 3102)
    C.pin_up(lum, clock(800, 150, 66, hh=4, mm=8, pend=False), 3103, halo_reach=14)
    C.sfx(lum, "tick", 800, 268, 36, 3104, deg=-6, weight=0.16)
    C.pin_up(lum, chair(170, fy, back_deg=-24), 3105)
    C.pin_up(lum, agent(330, fy + 4, face=1, scale=0.74, legs=(14, -6), lean=10, tilt=4, sh=34, el=-20, pencil_deg=200), 3106)
    C.pin_up(lum, desk(440, 470, 400, fy), 3107)
    memo_card(lum, 560, 330, 230, 150, 3108)
    C.sfx(lum, "SCRRAPE!", 215, 630, 74, 3109, deg=-8, weight=0.21, fatten=1, halo=7)
    for k, xx in enumerate((110, 160, 210)):
        C.charcoal_line(lum, [(xx, fy - 30 - k * 6), (xx - 50, fy - 26 - k * 6)], 5, 3110 + k)
    return lum


def P2(st):
    w, h = 970, 846
    lum = C.wall(w, h, 3201)
    fy = 742
    floor_band(lum, fy, 3202)
    cup, _ = cupboard(760, 300, 230, 440)
    C.pin_up(lum, cup, 3203)
    C.pin_up(lum, agent(470, fy + 4, face=1, scale=0.74, legs=(22, -20), sh=-22, el=24, lean=4, pencil_deg=200), 3204)
    for k, (xx, yy, cap) in enumerate(((80, 700, 40), (190, 672, 46), (300, 700, 52))):
        C.sfx(lum, "TAP", xx, yy, cap, 3210 + k, deg=-4 + 5 * k, weight=0.19, halo=5)
    # motion: three rubbed trail strokes behind him
    for k, yy in enumerate((330, 420, 510)):
        C.charcoal_line(lum, [(250, yy), (330, yy + 2)], 5, 3220 + k, alpha=0.6)
    return lum


def window_panel(seed, stranger_kw, w=633, h=846):
    lum = C.wall(w, h, seed)
    fy = 742
    floor_band(lum, fy, seed + 1)
    ws, sill = window(250, 220, 330, 560, sill=560, header=70)
    ws = ws[:5]          # frame, posts, sill, counter: no glazing bars across her face
    # platform side seen through the panes: a paler grey
    pane = np.zeros((h, w), np.uint8)
    pane[290:560, 250:580] = 255
    a = pane.astype(np.float32) / 255
    lum[:] = lum * (1 - 0.25 * a) + 0.74 * 0.25 * a
    st_shapes = stranger(415 + stranger_kw.pop("dx", 0), sill + 4, scale=1.1, **stranger_kw)
    C.pin_up(lum, st_shapes, seed + 2, halo_reach=12, halo_strength=0.18,
             tones=dict(coat=0.36, collar=0.52, skin_s=0.66, hat=0.10, bow=0.78, glove=0.16))
    C.pin_up(lum, ws, seed + 3, halo_reach=10, halo_strength=0.15)
    return lum, sill


def P3(st):
    lum, sill = window_panel(3301, {"glove": True, "face": -1})
    C.pin_up(lum, agent(30, 742 + 4, face=1, scale=0.70, sh=10, el=24, tilt=2, pencil_deg=200), 3302)
    C.sfx(lum, "tok tok", 470, 600, 40, 3303, deg=-6, weight=0.18, fatten=1, halo=5)
    C.speech(lum, Q, (330, 128), (390, 330), 3304, unit=30, amp=44, gap=10, pad=50)
    return lum


def P4(st):
    w, h = 633, 846
    lum = C.wall(w, h, 3401)
    fy = 742
    floor_band(lum, fy, 3402)
    C.pin_up(lum, clock(410, 190, 120, hh=4, mm=10, pend=True, swing=10), 3403, halo_reach=16)
    C.sfx(lum, "TICK", 200, 100, 60, 3404, deg=-10, weight=0.21, fatten=1, halo=6)
    C.sfx(lum, "tock", 560, 470, 44, 3405, deg=8, weight=0.18, fatten=1, halo=4)
    C.pin_up(lum, agent(200, fy + 4, face=1, scale=0.64, legs=(3, -3), tilt=-24, sh=6, el=20, pencil_deg=190), 3406)
    x0, x1 = 300, 610
    C.speech(lum, A_, (430, 610), (240, 262), 3407, unit=28, amp=40, gap=10, pad=46)
    return lum


def P5(st):
    lum, sill = window_panel(3501, {"dx": 60, "face": 1, "tilt": -4})
    C.pin_up(lum, agent(-10, 742 + 4, face=1, scale=0.70, legs=(18, -16), sh=-14, el=20, pencil_deg=200, lean=3), 3502)
    C.speech(lum, T_, (330, 128), (480, 300), 3503, unit=40, amp=46, thick=(12, 19), gap=14)
    for k, (xx, yy, cap) in enumerate(((440, 690, 42), (520, 650, 32), (576, 618, 24))):
        C.sfx(lum, "tok", xx, yy, cap, 3510 + k, deg=4, weight=0.18, fatten=1, halo=3, alpha=1.0 - 0.2 * k)
    return lum


def cupboard_panel(seed, agent_kw, open_deg, line=False, w=970, h=846):
    lum = C.wall(w, h, seed)
    fy = 742
    floor_band(lum, fy, seed + 1)
    C.pin_up(lum, service_door(700, 230, 200, 512), seed + 2, halo_reach=12, halo_strength=0.18)
    service_card(lum, 740, 282, seed + 3)
    cup, ins = cupboard(380, 300, 240, 440, open_deg=open_deg)
    door = [s for s in cup if s.role == "door"]
    rest = [s for s in cup if s.role != "door"]
    C.pin_up(lum, rest, seed + 4, halo_reach=14)
    if ins is not None:
        ix0, iy0, ix1, iy1 = ins
        key_card(lum, (ix0 + ix1) / 2 + 20, iy0 + 128, 0.30, seed + 5)
    C.pin_up(lum, door, seed + 6, halo=False)
    C.pin_up(lum, agent(**agent_kw), seed + 7)
    return lum, ins


def P6(st):
    lum, ins = cupboard_panel(3601, dict(x=170, floor=746, face=1, scale=0.70, legs=(14, -12), sh=64, el=18, pencil_deg=200), 112)
    C.sfx(lum, "CREEEAK", 520, 150, 66, 3602, deg=-10, weight=0.21, fatten=1, halo=7)
    ix0, iy0, ix1, iy1 = ins
    C.sfx(lum, "tink", ix1 + 40, iy0 + 300, 34, 3603, deg=10, weight=0.16, halo=4)
    return lum


def P7(st):
    lum, ins = cupboard_panel(3701, dict(x=150, floor=746, face=1, scale=0.70, legs=(3, -3), sh=50, el=120, wr=8,
                                         pencil_deg=40, tilt=6), 112)
    if st.get("line", True):
        C.speech(lum, F_, (540, 128), (232, 300), 3702, unit=34, amp=40, gap=12, fade_from=6)
    if st.get("ticks", True):
        for k, (xx, yy) in enumerate(((880, 820), (930, 790))):
            pass
        C.sfx(lum, "tick . . .", 812, 806, 30, 3704, deg=-3, weight=0.14, alpha=0.75)
    return lum


PANELS = [P1, P2, P3, P4, P5, P6, P7]


def build(n_panels=7, st=None):
    st = st or {}
    page = pen99.sheet99().astype(np.float32)
    for i, (fn, box) in enumerate(zip(PANELS, BOXES)):
        if i >= n_panels:
            break
        x0, y0, x1, y1 = box
        lum = fn(st if i == n_panels - 1 else {})
        assert lum.shape == (y1 - y0, x1 - x0), (fn.__name__, lum.shape, (y1 - y0, x1 - x0))
        rgb = C.tone(lum)
        m = np.zeros((H, W), np.uint8)
        m[y0:y1, x0:x1] = 255
        penlib.shadow_onto(page, m, off=6, blur=5, opacity=0.30)
        page[y0:y1, x0:x1] = rgb
    shown = BOXES[:n_panels]
    bm = penlib.border_mask((H, W), shown, w=10, seed=3190)
    penlib.ink_onto(page, bm, color=np.array([20, 21, 14], np.float32))
    return page


def main():
    page = build()
    img, size = B.save_page(page.copy(), N, PID, TITLE)
    # beats: the page fills sound by sound, panel by panel; the last beat is the forgetting rhythm trailing off
    frames = []
    for n in range(1, 7):
        f = build(n)
        pen99.folio(f, N, TITLE)
        frames.append(f)
    f = build(7, {"line": False, "ticks": False})
    pen99.folio(f, N, TITLE)
    frames.append(f)
    frames.append(np.asarray(Image.open(B.MASTERS / f"{N:02d}-{PID}.png")).astype(np.float32))
    nb = B.save_beats(N, frames)
    print("bytes", size, "beats", nb)


if __name__ == "__main__":
    main()

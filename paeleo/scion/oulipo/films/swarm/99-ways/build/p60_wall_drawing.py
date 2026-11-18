"""99 ways, page 60 "Wall drawing" (medium and material; medium: charcoal-card).

The page is one stretch of the station office wall: lime plaster (the teuf-teuf rock relief from
"Cueva de las manos - detalle.jpg", Suzko, CC BY-SA 3.0, flattened to a pale wash by charcoal99.wall, with
HANDMADE patching, cracks, nail holes and a ghost where a notice once hung), a skirting board and the floor.
Three parts of the room are REAL on that wall, built as grey charcoal cards (charcoal99.pin_up, each card
with its own shadow): the wall clock (4:10) hanging on its nail, the office cupboard standing at the wall
(its door opens on the left jamb; inside, the ANRC 1922 key cutout on its hook with a SERVICE tag), and the
SERVICE door in its architrave with its SERVICE card. Everything else is DRAWN on the plaster in charcoal:
six rough panel frames, the agent and the stranger (outlines of the b1m2 figure model, hatched and
smudged), desk, memo, ticket window, captions and balloons in the shared pen hand rubbed as charcoal.
The drawn agent looks up at the real clock; the last drawn frame is drawn round the real cupboard and door.
Run: python3 -I p60_wall_drawing.py"""
import math
import random
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import charcoal99 as C  # noqa: E402
import b1m2 as B  # noqa: E402
from b1m2 import agent, stranger, desk, window, clock, cupboard, service_door, Shape, R_, circle_pts, bar_pts  # noqa: E402
import pen99  # noqa: E402
from pen99 import penlib  # noqa: E402

N, PID, TITLE = 60, "wall-drawing", "Wall drawing"
W, H = 2200, 2850
SKIRT_TOP, SKIRT_BOT = 2598, 2712          # the real skirting board; floor below
DARK = 0.07

# drawn frames (charcoal on the plaster)
D = {1: (140, 150, 860, 1000), 2: (900, 150, 1440, 1000), 3: (1480, 150, 2060, 1000),
     4: (140, 1045, 1000, 1590), 5: (1040, 1045, 2060, 1590), 6: (140, 1640, 2060, 2580)}
# the real things on the wall
CLOCK = (330, 1185, 96)                     # cx, cy, r  (inside drawn frame 4)
CUP = (1090, 1920, 380, 760)                # x0, y0, w, h  (stands on the floor, before the skirting)
SDOOR = (1650, 1730, 340, 982)              # x0, y0, w, h  (down to the floor)


# ------------------------------------------------------------------ the wall
def plaster(seed=6000):
    lum = C.wall(W, H, seed, level=0.905, hp_gain=0.42, broad_gain=0.30, scale=3.0)
    rng = np.random.default_rng(seed)
    # broad lime-wash unevenness and two patched areas (fresher, smoother plaster)
    n = rng.random((12, 10)).astype(np.float32)
    n = cv2.resize(n, (W, H), interpolation=cv2.INTER_CUBIC)
    lum += (n - 0.5) * 0.045
    for (cx, cy, rx, ry) in ((1720, 1300, 210, 120), (330, 2280, 160, 220)):
        m = np.zeros((H, W), np.uint8)
        pts = [(cx + rx * (1 + 0.12 * math.sin(5 * t)) * math.cos(t), cy + ry * (1 + 0.1 * math.cos(7 * t)) * math.sin(t))
               for t in np.linspace(0, 6.28, 40)]
        cv2.fillPoly(m, [np.int32(pts)], 255, cv2.LINE_AA)
        a = cv2.GaussianBlur(m.astype(np.float32) / 255, (0, 0), 3)
        sm = cv2.GaussianBlur(lum, (0, 0), 6)
        lum[:] = lum * (1 - a) + (sm + 0.025) * a
        edge = cv2.morphologyEx(m, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)).astype(np.float32) / 255
        lum *= 1 - 0.10 * cv2.GaussianBlur(edge, (0, 0), 1.0)
    # the ghost of a notice that hung here once (cleaner rectangle, four pin holes)
    gx0, gy0, gx1, gy1 = 1515, 1080, 1735, 1240
    g = np.zeros((H, W), np.float32)
    g[gy0:gy1, gx0:gx1] = 1
    g = cv2.GaussianBlur(g, (0, 0), 4)
    lum += 0.03 * g
    for (x, y) in ((gx0 + 8, gy0 + 8), (gx1 - 8, gy0 + 8), (gx0 + 8, gy1 - 8), (gx1 - 8, gy1 - 8)):
        hole(lum, x, y, 3)
    # cracks: thin wandering dark lines with a lighter lip
    rnd = random.Random(seed)
    for (x, y, ang, L) in ((60, 1010, -0.3, 360), (2150, 610, 2.7, 300), (1010, 2540, -1.9, 250), (1320, 120, 1.7, 220)):
        pts = [(x, y)]
        a = ang
        for k in range(int(L / 9)):
            a += rnd.uniform(-0.35, 0.35)
            x, y = x + 9 * math.cos(a), y + 9 * math.sin(a)
            pts.append((x, y))
        m = np.zeros((H, W), np.uint8)
        penlib.brush_line(m, pts, 2.2, rnd.randrange(10000), 0.4)
        lip = np.zeros_like(m)
        lip[2:, 1:] = m[:-2, :-1]
        lum += 0.04 * lip.astype(np.float32) / 255
        lum *= 1 - 0.42 * m.astype(np.float32) / 255
        if rnd.random() < 0.8:
            j = len(pts) // 2
            bx, by = pts[j]
            b = [(bx, by)]
            for k in range(14):
                a2 = ang + 0.9 + rnd.uniform(-0.3, 0.3)
                bx, by = bx + 7 * math.cos(a2), by + 7 * math.sin(a2)
                b.append((bx, by))
            m2 = np.zeros((H, W), np.uint8)
            penlib.brush_line(m2, b, 1.6, rnd.randrange(10000), 0.3)
            lum *= 1 - 0.35 * m2.astype(np.float32) / 255
    for (x, y) in ((1960, 260), (760, 1700), (2000, 1140)):
        hole(lum, x, y, 4)
    return lum


def hole(lum, x, y, r):
    yy, xx = np.ogrid[int(y - 8):int(y + 9), int(x - 8):int(x + 9)]
    d = np.sqrt((xx - x) ** 2 + (yy - y) ** 2)
    sub = lum[int(y - 8):int(y + 9), int(x - 8):int(x + 9)]
    sub *= 1 - 0.55 * np.clip(r + 0.5 - d, 0, 1)
    sub += 0.03 * np.clip(r + 2.5 - d, 0, 1) * (d > r)


def card_rect(lum, x0, y0, x1, y1, t, seed, shadow=True, edge=0.22):
    m = np.zeros(lum.shape, np.uint8)
    rnd = random.Random(seed)
    pts = [(x0 + rnd.uniform(-1.5, 1.5), y0 + rnd.uniform(-1.5, 1.5)), (x1 + rnd.uniform(-1.5, 1.5), y0 + rnd.uniform(-1.5, 1.5)),
           (x1 + rnd.uniform(-1.5, 1.5), y1 + rnd.uniform(-1.5, 1.5)), (x0 + rnd.uniform(-1.5, 1.5), y1 + rnd.uniform(-1.5, 1.5))]
    cv2.fillPoly(m, [np.int32(np.array(pts) * 4)], 255, cv2.LINE_AA, shift=2)
    if shadow:
        C.drop(lum, m, (6, 8), 4.0, 0.34)
    C.card_piece(lum, m, t, seed, edge=edge)
    return m


def skirting_and_floor(lum):
    # floor: pale scrubbed boards seen edge-on
    fl = lum[SKIRT_BOT:, :]
    g = C.grain(fl.shape[0], W, 6101, 2.5)
    fl[:] = 0.70 + 0.05 * g
    for y in range(SKIRT_BOT + 28, H, 36):
        lum[y:y + 2, :] *= 0.86
    m = card_rect(lum, -10, SKIRT_TOP, W + 10, SKIRT_BOT, 0.52, 6102)
    card_rect(lum, -10, SKIRT_TOP - 12, W + 10, SKIRT_TOP + 4, 0.62, 6103)      # the moulding
    return m


def real_clock(lum):
    cx, cy, r = CLOCK
    # its nail and the string of shadow it leaves on the plaster
    C.pin_up(lum, clock(cx, cy, r, hh=4, mm=10, pend=True, swing=7), 6201, halo=False)
    C.brad(lum, cx, cy - r - 18, 6)


def real_cupboard(lum, open_deg, key=True):
    x0, y0, w, h = CUP
    cup, ins = cupboard(x0, y0, w, h, open_deg=open_deg)
    door = [s for s in cup if s.role == "door"]
    rest = [s for s in cup if s.role != "door"]
    C.pin_up(lum, rest, 6301, halo=False, tones=dict(cupboard=0.34, shelf=0.22))
    if ins is not None and key:
        ix0, iy0, ix1, iy1 = ins
        key_card(lum, (ix0 + ix1) / 2 + 10, iy0 + 175, 0.40, 6302)
    C.pin_up(lum, door, 6303, halo=False, tones=dict(door=0.46))
    return ins


def key_card(lum, kx, ky, scale, seed):
    """The brass key: the ANRC 1922 cutout (99-ways-template) cut as a pale card, on a hook, SERVICE tag."""
    h, w = lum.shape
    km = np.zeros((h, w), np.uint8)
    B.paste_mask(km, B.key_alpha(), kx, ky, scale, 0)
    km = np.where(km > 120, 255, 0).astype(np.uint8)
    ys, xs = np.nonzero(km)
    top = ys.min()
    hk = np.zeros((h, w), np.uint8)
    penlib.brush_line(hk, [(kx - 30, top - 18), (kx + 2, top - 18), (kx + 2, top + 10)], 9, seed)
    a = C.rub_mask(hk, seed)
    lum[:] = lum * (1 - a) + 0.62 * a
    C.drop(lum, km, (4, 6), 2.5, 0.40)
    C.card_piece(lum, km, 0.84, seed + 1, edge=0.25)
    tx, ty = kx + 34, ky + (ys.max() - ky) * 0.10
    st = np.zeros((h, w), np.uint8)
    penlib.brush_line(st, [(kx + 4, ky - 14), (tx + 12, ty + 8)], 3, seed + 2, 0.4)
    a = C.rub_mask(st, seed + 3)
    lum[:] = lum * (1 - a) + 0.15 * a
    tag_card(lum, tx, ty, "SERVICE", 22, seed + 4, tilt=8)


def tag_card(lum, x, y, text, cap, seed, tilt=0.0, pad=(14, 10)):
    m = pen99.letter([text], cap, seed, weight=0.15)
    mh, mw = m.shape
    bw, bh = mw - cap * 1.0 + 2 * pad[0], cap * 1.0 + 2 * pad[1]
    pts = np.array([(x, y), (x + bw, y), (x + bw, y + bh), (x, y + bh)], np.float32)
    c = pts.mean(0)
    a = math.radians(tilt)
    R = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
    pts = (pts - c) @ R.T + c
    cm = np.zeros(lum.shape, np.uint8)
    cv2.fillPoly(cm, [np.int32(pts * 4)], 255, cv2.LINE_AA, shift=2)
    C.drop(lum, cm, (3, 5), 2.5, 0.32)
    C.card_piece(lum, cm, 0.95, seed, edge=0.05, rub=0.02)
    lm = np.zeros(lum.shape, np.uint8)
    C.place(lm, m, c[0], c[1] + cap * 0.12, tilt)
    al = lm.astype(np.float32) / 255
    lum[:] = lum * (1 - al) + 0.06 * al


def real_service_door(lum):
    x0, y0, w, h = SDOOR
    # architrave
    for (a, b, c, d) in ((x0 - 46, y0 - 46, x0 + w + 46, y0), (x0 - 46, y0 - 46, x0, SKIRT_BOT + 2),
                         (x0 + w, y0 - 46, x0 + w + 46, SKIRT_BOT + 2)):
        card_rect(lum, a, b, c, d, 0.50, 6401 + int(a))
    card_rect(lum, x0, y0, x0 + w, SKIRT_BOT + 2, 0.62, 6404, shadow=False, edge=0.05)   # the panel mouldings' ground
    sd = service_door(x0 + 18, y0 + 20, w - 36, h - 20)
    C.pin_up(lum, sd, 6402, halo=False, tones=dict(sdoor=0.38))
    tag_card(lum, x0 + w / 2 - 92, y0 + 120, "SERVICE", 40, 6403, pad=(18, 12))


def charcoal_stick(lum):
    """The stick of charcoal the drawing was made with, left on the skirting ledge (a cut card)."""
    m = np.zeros(lum.shape, np.uint8)
    pts = [(600, SKIRT_TOP - 30), (742, SKIRT_TOP - 40), (746, SKIRT_TOP - 22), (604, SKIRT_TOP - 12)]
    cv2.fillPoly(m, [np.int32(np.array(pts) * 4)], 255, cv2.LINE_AA, shift=2)
    C.drop(lum, m, (4, 6), 3.0, 0.4)
    C.card_piece(lum, m, 0.05, 6501, edge=0.1)
    dust = np.zeros(lum.shape, np.uint8)
    rng = np.random.default_rng(6502)
    for k in range(90):
        x, y = 560 + rng.normal(0, 70), SKIRT_TOP - 14 + abs(rng.normal(0, 4))
        cv2.circle(dust, (int(x), int(y)), int(rng.integers(1, 3)), 255, -1)
    lum *= 1 - 0.5 * cv2.GaussianBlur(dust.astype(np.float32) / 255, (0, 0), 0.8)


# ------------------------------------------------------------------ charcoal drawing on the plaster
TONE = dict(C.ROLE_TONE, desk=0.40, window=0.55, chair=0.30)


def hatch_mask(h, w, spacing, ang, seed):
    m = np.zeros((h, w), np.uint8)
    rnd = random.Random(seed)
    a = math.radians(ang)
    dx, dy = math.cos(a), math.sin(a)
    nx, ny = -dy, dx
    L = h + w
    for k in range(-L, L, spacing):
        cx, cy = w / 2 + nx * k, h / 2 + ny * k
        p0 = (cx - dx * L + rnd.uniform(-3, 3), cy - dy * L)
        p1 = (cx + dx * L, cy + dy * L + rnd.uniform(-3, 3))
        cv2.line(m, (int(p0[0] * 4), int(p0[1] * 4)), (int(p1[0] * 4), int(p1[1] * 4)), 255,
                 rnd.choice((2, 3)), cv2.LINE_AA, shift=2)
    return m


def draw(lum, shapes, seed, line_w=5.0, lift=0.85):
    """Draw b1m2 shapes on the plaster view `lum` in charcoal: each nearer shape lifts (erases) what lies
    under it, dark roles are hatched and finger-smudged, every shape outlined with a charcoal stick."""
    h, w = lum.shape
    bg = lum.copy()
    rnd = random.Random(seed)
    for i, s in enumerate(sorted(shapes, key=lambda s: s.z)):
        if s.role in ("pin",):
            continue
        m = B.raster([Shape(s.pts, s.role, smooth=s.smooth)], w, h, ss=2)
        if m.max() == 0:
            continue
        a = m.astype(np.float32) / 255
        if not s.hole:
            lum[:] = lum * (1 - a * lift) + bg * a * lift
            t = TONE.get(s.role, 0.5)
            if t < 0.45:
                sp = 7 if t < 0.15 else (10 if t < 0.3 else 14)
                hm = hatch_mask(h, w, sp, 52 + rnd.uniform(-6, 6), seed + i)
                if t < 0.15:
                    hm = np.maximum(hm, hatch_mask(h, w, 11, -38, seed + i + 500))
                hm = (hm.astype(np.float32) * a).astype(np.uint8)
                al = C.rub_mask(hm, seed + i, smear=(4, 3), keep=0.75) * 0.85
                lum[:] = lum * (1 - al) + DARK * al
                sm = cv2.GaussianBlur(a, (0, 0), 5) * (0.45 - t) * 0.55
                lum *= 1 - sm
        elif s.role in ("inside", "pendwin"):
            hm = hatch_mask(h, w, 7, 45, seed + i)
            hm = (hm.astype(np.float32) * a).astype(np.uint8)
            al = C.rub_mask(hm, seed + i) * 0.85
            lum[:] = lum * (1 - al) + DARK * al
        cs, _ = cv2.findContours((m > 127).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        lm = np.zeros((h, w), np.uint8)
        for c in cs:
            if len(c) < 6:
                continue
            p = c[:, 0, :].astype(np.float32)
            p = np.vstack([p, p[:1]])[::2]
            small = cv2.contourArea(c) < 400
            penlib.brush_line(lm, p, (line_w * 0.6 if small else line_w) * rnd.uniform(0.9, 1.15), seed + i * 7, 0.6)
        al = C.rub_mask(lm, seed + i * 3, smear=(3, 2), keep=0.86)
        lum[:] = lum * (1 - al) + DARK * al


def stroke(lum, pts, w, seed, dark=DARK, alpha=1.0):
    C.charcoal_line(lum, pts, w, seed, dark=dark, tremor=1.2, alpha=alpha)


def write(lum, lines, x, y, cap, seed, weight=0.15):
    """Charcoal lettering, left-aligned at (x, first baseline y), the pen hand rubbed on plaster."""
    m = B.letter_left(lines, cap, seed, weight)
    pm = np.zeros(lum.shape, np.uint8)
    B.blit_mask(pm, m, int(x - cap * 0.6), int(y - cap * 1.15))
    al = C.rub_mask(pm, seed, smear=(3, 2), keep=0.9)
    lum[:] = lum * (1 - al) + DARK * al


def wall_balloon(lum, lines, at, tip, seed, cap=46):
    """A balloon drawn on the plaster: its ground rubbed clean with a rag (lighter), outline and lettering
    in charcoal (penlib.balloon_piece outline, the shared pen hand)."""
    b = penlib.balloon_piece([pen99.clean(l) for l in lines], cap, (tip[0] - at[0], tip[1] - at[1]), seed, tail_w=0.26)
    h, w = lum.shape
    cx, cy = b["center"]
    ox, oy = int(round(at[0] - cx)), int(round(at[1] - cy))

    def put(m):
        out = np.zeros((h, w), np.uint8)
        Hc, Wc = m.shape
        ys, xs = max(0, oy), max(0, ox)
        ye, xe = min(h, oy + Hc), min(w, ox + Wc)
        if ye > ys and xe > xs:
            out[ys:ye, xs:xe] = m[ys - oy:ye - oy, xs - ox:xe - ox]
        return out
    pm, im = put(b["paper"]), put(b["ink"])
    pa = cv2.GaussianBlur(pm.astype(np.float32) / 255, (0, 0), 6)
    lum[:] = lum * (1 - 0.55 * pa) + 0.975 * 0.55 * pa
    al = C.rub_mask(im, seed + 3, smear=(3, 2), keep=0.9)
    lum[:] = lum * (1 - al) + DARK * al


def frame(lum, box, seed):
    x0, y0, x1, y1 = box
    rnd = random.Random(seed)
    j = lambda: rnd.uniform(-4, 4)
    for (a, b) in (((x0 - 10, y0 + j()), (x1 + 14, y0 + j())), ((x1 + j(), y0 - 12), (x1 + j(), y1 + 10)),
                   ((x1 + 12, y1 + j()), (x0 - 12, y1 + j())), ((x0 + j(), y1 + 12), (x0 + j(), y0 - 10))):
        mid = ((a[0] + b[0]) / 2 + j(), (a[1] + b[1]) / 2 + j())
        stroke(lum, [a, mid, b], 7.5, rnd.randrange(99999))


def view(lum, box, pad=0):
    x0, y0, x1, y1 = box
    return lum[y0 - pad:y1 + pad, x0 - pad:x1 + pad]


# ------------------------------------------------------------------ the drawn panels
def drawn_memo(v, x, y, seed):
    """the memo slip drawn on the wall, tilted, with its pencilled note"""
    pts = [(x, y), (x + 282, y - 8), (x + 288, y + 112), (x + 4, y + 120)]
    v_bg = v.copy()
    m = np.zeros(v.shape, np.uint8)
    cv2.fillPoly(m, [np.int32(pts)], 255, cv2.LINE_AA)
    a = m.astype(np.float32) / 255
    v[:] = v * (1 - 0.6 * a) + 0.975 * 0.6 * a
    stroke(v, pts + [pts[0]], 4.5, seed)
    write(v, ["MEMO", "4:15 - open SERVICE door.", "Key in cupboard."], x + 18, y + 30, 21, seed + 1, 0.16)


def D1(lum):
    v = view(lum, D[1])
    fl = 800
    stroke(v, [(10, fl), (360, fl + 3), (710, fl - 2)], 6, 6601)
    draw(v, desk(330, 560, 330, fl), 6602)
    draw(v, agent(240, fl, face=1, scale=0.62, legs=(12, -6), lean=10, tilt=6, sh=34, el=-10, pencil_deg=200), 6603)
    drawn_memo(v, 362, 470, 6604)
    write(v, B.wrap("Randolph, 1937. The memo says: 4:15, open the SERVICE door; the key is in the cupboard. "
                    "The agent gets up for the key.", 34, 600), 36, 64, 34, 6605)


def D2(lum):
    v = view(lum, D[2])
    fl = 800
    stroke(v, [(10, fl), (270, fl - 3), (530, fl + 2)], 6, 6611)
    draw(v, agent(230, fl, face=1, scale=0.62, legs=(22, -20), sh=-22, el=24, lean=4, pencil_deg=200), 6612)
    for k, yy in enumerate((330, 420, 520)):
        stroke(v, [(60, yy), (130, yy + 2)], 5, 6613 + k, alpha=0.7)
    write(v, ["Off across the office,", "toward the cupboard..."], 36, 64, 34, 6616)
    # an arrow onward
    stroke(v, [(380, 760), (500, 760)], 6, 6617)
    stroke(v, [(470, 738), (502, 760), (470, 782)], 6, 6618)


def D3(lum):
    v = view(lum, D[3])
    fl = 800
    stroke(v, [(10, fl), (290, fl + 2), (570, fl - 2)], 6, 6621)
    ws, sill = window(250, 330, 270, 470, sill=640, header=60)
    draw(v, stranger(385, sill + 4, face=-1, scale=1.0, glove=True), 6622)
    draw(v, ws[:5], 6623)
    write(v, ["TICKET OFFICE"], 268, 372, 22, 6624, 0.17)
    draw(v, agent(70, fl, face=1, scale=0.55, sh=8, el=20, tilt=2, pencil_deg=200), 6625)
    write(v, ["...but a lady at the ticket", "window stops him:"], 30, 58, 30, 6626)
    wall_balloon(v, ["Pardon me —", "have you the", "right time?"], (320, 222), (390, 440), 6627, cap=38)


def D4(lum):
    v = view(lum, D[4])
    fl = 520
    stroke(v, [(10, fl), (380, fl + 2), (750, fl - 2)], 6, 6631)
    draw(v, agent(760, fl, face=-1, scale=0.47, legs=(3, -3), tilt=-26, sh=6, el=20, pencil_deg=190), 6632)
    write(v, ["He looks up at the clock", "(a real one, on its nail):"], 330, 56, 32, 6633)
    # a charcoal arrow from his eye to the real clock
    stroke(v, [(700, 140), (520, 150), (300, 150)], 5, 6634, alpha=0.8)
    stroke(v, [(326, 130), (296, 150), (326, 172)], 5, 6636, alpha=0.8)
    wall_balloon(v, ["Ten past four,", "by the clock."], (500, 400), (700, 250), 6635, cap=38)


def D5(lum):
    v = view(lum, D[5])
    fl = 520
    stroke(v, [(10, fl), (560, fl + 2), (1110, fl - 2)], 6, 6641)
    ws, sill = window(110, 190, 250, 330, sill=444, header=56)
    draw(v, stranger(190, sill + 4, face=-1, scale=0.70, tilt=-4), 6642)
    draw(v, ws[:5], 6643)
    write(v, ["TICKET OFFICE"], 120, 228, 20, 6644, 0.17)
    draw(v, agent(560, fl, face=1, scale=0.47, legs=(18, -16), sh=-14, el=20, pencil_deg=200, lean=3), 6645)
    wall_balloon(v, ["Much", "obliged!"], (430, 110), (250, 240), 6646, cap=40)
    write(v, ["She goes. He goes on", "to the cupboard,", "down there."], 650, 70, 32, 6647)


def D6(lum, line=True):
    v = view(lum, D[6])
    ox, oy = D[6][0], D[6][1]
    write(v, ["He opens the cupboard:", "the key hangs on its hook."], 36, 66, 34, 6651)
    # the drawn agent stands on the real skirting, before the real cupboard
    fl = D[6][3] - oy - 14
    stroke(v, [(10, fl), (420, fl + 2), (840, fl - 1)], 6, 6655)
    draw(v, agent(640, fl, face=1, scale=0.92, legs=(3, -3), sh=50, el=120, wr=8, pencil_deg=40, tilt=6),
         6652, line_w=6.0)
    if line:
        wall_balloon(v, ["Well, here I am...", "and what for?"], (300, 330), (600, 330), 6653, cap=44)
        write(v, ["The key stays on its hook.", "The SERVICE door stays closed."], 36, 760, 32, 6654)


DRAWN = [D1, D2, D3, D4, D5]


def build(n_drawn=6, cup_open=112, line=True):
    lum = plaster()
    for i, fn in enumerate(DRAWN[:n_drawn]):
        frame(lum, D[i + 1], 6700 + i)
        fn(lum)
    if n_drawn >= 5:
        # the long charcoal arrow from frame 5 down the wall toward the real cupboard
        stroke(lum, [(1880, 1300), (1700, 1560), (1500, 1830)], 7, 6648)
        stroke(lum, [(1494, 1778), (1496, 1836), (1548, 1812)], 7, 6649)
    if n_drawn >= 6:
        frame(lum, D[6], 6706)
        D6(lum, line)
    skirting_and_floor(lum)
    real_service_door(lum)
    real_clock(lum)
    real_cupboard(lum, cup_open)
    charcoal_stick(lum)
    return C.tone(lum)


def main():
    page = build()
    img, size = B.save_page(page.copy(), N, PID, TITLE)
    print("bytes", size)
    frames = []
    for st in (dict(n_drawn=0, cup_open=0), dict(n_drawn=1, cup_open=0), dict(n_drawn=3, cup_open=0),
               dict(n_drawn=4, cup_open=0), dict(n_drawn=5, cup_open=0), dict(n_drawn=5, cup_open=60),
               dict(n_drawn=6, cup_open=112, line=False)):
        f = build(**st)
        f = np.clip(np.round(f), 0, 255).astype(np.uint8)
        pen99.folio(f, N, TITLE)
        frames.append(f)
    frames.append(np.asarray(Image.open(B.MASTERS / f"{N:02d}-{PID}.png")))
    print("beats", B.save_beats(N, frames))


if __name__ == "__main__":
    if "--page" in sys.argv:
        img, size = B.save_page(build(), N, PID, TITLE)
        print("bytes", size)
    else:
        main()

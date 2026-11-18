"""Page 06 Turntable (medium and material; medium: spiral-disc).

A HANDMADE slotted picture disc (phenakistiscope type): eight sectors printed round a card disc, the
agent standing at the same place in each so that, spun before a mirror and seen through the rim slots,
he walks; the office passes behind him from the memo to the open cupboard. The beats and the four lines
are lettered round the rim in the shared pen hand; an inked spiral turns at the hub.
Figures: the b1m2 cut-paper model printed in ink; the key: the ANRC 1922 cutout as a brass spot colour.
"""
import math
import random
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
from b1m2 import *  # noqa

N, PID, TITLE = 6, "turntable", "Turntable"
NS = 6
R = 960                     # disc radius on the page (px)
CX, CY = 1100, 1090         # disc centre
TW = int(math.pi * 2 * R / NS) + 40
CARD = np.array([236, 226, 204], np.float32)
PRINT = np.array([24, 21, 20], np.float32)
RED = np.array([168, 58, 40], np.float32)
BRASS = np.array([206, 154, 60], np.float32)
SHEET = pen99.sheet99()

V_FEET = R - int(0.235 * R)         # agent's feet (inner)
FIG_SC = 0.43

SECTORS = [
    dict(ev="E0", text=["Memo: 4:15 - open SERVICE door.", "Key in cupboard. He sets off."], scene="walk1"),
    dict(ev="E1", text=["She: \"Pardon me — have you", "the right time?\""], scene="window_ask"),
    dict(ev="E2", text=["He: \"Ten past four,", "by the clock.\""], scene="clock"),
    dict(ev="E3", text=["She: \"Much obliged!\"", "and she goes."], scene="window_go"),
    dict(ev="E4", text=["He opens the cupboard: the brass", "key on its hook, tagged SERVICE."], scene="key"),
    dict(ev="E5", text=["\"Well, here I am... and what for?\"", "The key stays. The door stays shut."], scene="forget"),
]


def wedge_halfwidth(v):
    return math.pi / NS * (R - v)


def tile(k, sec):
    t = np.zeros((R, TW, 3), np.float32) + CARD
    m = np.zeros((R, TW), np.uint8)
    cx = TW / 2
    feet = V_FEET
    sc = sec["scene"]
    shapes = []
    brass = []
    if sc == "desk":
        shapes += agent(cx - 30, feet - 10, face=1, scale=FIG_SC, seated=True, tilt=14, sh=40, el=70, pencil_deg=60, lean=6)
        shapes += desk(cx - 20, feet - 130, 150, feet)
    elif sc in ("walk1", "walk2"):
        legs = (22, -20) if sc == "walk1" else (-6, 8)
        shapes += agent(cx, feet, face=1, scale=FIG_SC, legs=legs, sh=-20 if sc == "walk1" else 14, el=20, pencil_deg=200)
        shapes += desk(cx - 230, feet - 130, 150, feet) + lamp(cx - 110, feet - 240, 110)
    elif sc in ("window_ask", "window_go"):
        ws, sill = window(cx - 215, feet - 360, 130, 360, sill=feet - 170, header=40)
        shapes += ws
        go = sc == "window_go"
        shapes += stranger(cx - 150 - (18 if go else 0), sill + 12, face=-1 if go else 1, scale=0.62, glove=not go)
        shapes += agent(cx, feet, face=-1 if not go else 1, scale=FIG_SC, legs=(4, -4) if not go else (18, -16),
                        sh=6, el=16, pencil_deg=190)
    elif sc == "clock":
        shapes += clock(cx - 150, feet - 360, 52, swing=8)
        shapes += agent(cx, feet, face=-1, scale=FIG_SC, legs=(3, -3), tilt=-20, sh=6, el=20, pencil_deg=190)
    elif sc in ("key", "forget"):
        c, ins = cupboard(cx + 95, feet - 320, 130, 310, open_deg=112)
        shapes += c
        brass.append(ins)
        if sc == "forget":
            shapes += agent(cx, feet, face=1, scale=FIG_SC, legs=(3, -3), sh=48, el=118, wr=8, pencil_deg=40, tilt=6)
        else:
            shapes += agent(cx, feet, face=1, scale=FIG_SC, legs=(12, -10), sh=40, el=40, wr=0, pencil_deg=200)
    m = raster(shapes, TW, R)
    comp(t, m, PRINT)
    for ins in brass:
        ix0, iy0, ix1, iy1 = ins
        kx, ky = (ix0 + ix1) / 2, iy0 + (iy1 - iy0) * 0.45
        ka = key_alpha()
        km = np.zeros((R, TW), np.uint8)
        paste_mask(km, ka, kx, ky, 0.23)
        comp(t, cv2.dilate(km, np.ones((3, 3), np.uint8)), PRINT)
        comp(t, km, BRASS)
        if sec["scene"] == "key":
            lt = letter(["SERVICE"], 14, 600 + k, weight=0.17)
            card = np.zeros((R, TW), np.uint8)
            tx, ty = int(kx + 4), int(ky + 62)
            cv2.rectangle(card, (tx - lt.shape[1] // 2 + 4, ty - 12), (tx + lt.shape[1] // 2 - 4, ty + 12), 255, -1)
            comp(t, card, np.array([246, 240, 226], np.float32))
            lm = np.zeros((R, TW), np.uint8)
            put_mask(lm, lt, tx, ty)
            comp(t, lm, RED)
    # rim text: two rows, centred, each row along an arc
    tm = np.zeros((R, TW), np.uint8)
    rows_v = (int(R * 0.225), int(R * 0.30))
    for i, line in enumerate(sec["text"]):
        lm = letter([line], 44, 610 + 10 * k + i, weight=0.14)
        hw = wedge_halfwidth(rows_v[i]) * 2 - 30
        if lm.shape[1] > hw:
            s = hw / lm.shape[1]
            lm = cv2.resize(lm, (int(lm.shape[1] * s), int(lm.shape[0] * s)), interpolation=cv2.INTER_AREA)
        put_mask(tm, lm, cx, rows_v[i])
    # sector number at the rim, between the slots, in red
    nm = np.zeros((R, TW), np.uint8)
    put_mask(nm, letter([str(k + 1)], 50, 640 + k, weight=0.18), cx, R - int(0.912 * R))
    return t, tm, nm


def spiral_mask(size, r_out, turns=5.5, seed=66):
    m = np.zeros((size, size), np.uint8)
    c = size / 2
    pts = []
    n = 1400
    for i in range(n):
        t = i / (n - 1)
        a = t * turns * 2 * math.pi
        r = 18 + t * (r_out - 18)
        pts.append((c + r * math.sin(a), c - r * math.cos(a)))
    penlib.brush_line(m, pts, 15, seed, tremor=0.5)
    return m


def disc(rot_deg=0.0):
    """The printed disc, RGBA float (2R x 2R), rotated by rot_deg (clockwise)."""
    tiles = [tile(k, s) for k, s in enumerate(SECTORS)]
    atlas = np.concatenate([t[0] for t in tiles], axis=1)
    tatlas = np.concatenate([t[1] for t in tiles], axis=1)
    natlas = np.concatenate([t[2] for t in tiles], axis=1)
    D = 2 * R
    yy, xx = np.mgrid[0:D, 0:D].astype(np.float32)
    dx, dy = xx - R + 0.5, yy - R + 0.5
    r = np.sqrt(dx * dx + dy * dy)
    th = np.arctan2(dx, -dy) - math.radians(rot_deg)
    th = np.mod(th, 2 * np.pi)
    sw = 2 * np.pi / NS
    k = np.floor((th + sw / 2) / sw).astype(np.int32) % NS
    dth = th - k * sw
    dth = (dth + np.pi) % (2 * np.pi) - np.pi
    # pictures: each sector a flat, upright print (no bending); lettering: along the arcs
    thc = k * sw
    a_ = dx * np.sin(thc + math.radians(rot_deg)) - dy * np.cos(thc + math.radians(rot_deg))
    b_ = dx * np.cos(thc + math.radians(rot_deg)) + dy * np.sin(thc + math.radians(rot_deg))
    up = (b_ + TW / 2 + k * TW).astype(np.float32)
    vp = (R - a_).astype(np.float32)
    img = cv2.remap(atlas, up, vp, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    u = (dth * r + TW / 2 + k * TW).astype(np.float32)
    v = (R - r).astype(np.float32)
    tmask = cv2.remap(tatlas, u, v, cv2.INTER_LINEAR)
    nmask = cv2.remap(natlas, u, v, cv2.INTER_LINEAR)
    # card fibre (the 1934 sheet, rotated with the disc)
    fib = SHEET[CY - R:CY + R, CX - R:CX + R].mean(axis=2)
    fib = fib - fib.mean()
    Mrot = cv2.getRotationMatrix2D((R, R), -rot_deg, 1.0)
    fib = cv2.warpAffine(fib, Mrot, (D, D), borderMode=cv2.BORDER_REFLECT)
    img += fib[..., None] * 0.8
    # sector rules, spiral hub, slots, rim
    ink = np.zeros((D, D), np.uint8)
    for j in range(NS):
        a = math.radians(rot_deg + (j + 0.5) * 360 / NS)
        p0 = (R + 0.20 * R * math.sin(a), R - 0.20 * R * math.cos(a))
        p1 = (R + 0.84 * R * math.sin(a), R - 0.84 * R * math.cos(a))
        penlib.brush_line(ink, [p0, p1], 4, 700 + j, tremor=0.4)
    for rr, wdt in ((0.20 * R, 5), (0.84 * R, 5), (0.995 * R - 4, 7)):
        pts = [(R + rr * math.sin(2 * math.pi * i / 720), R - rr * math.cos(2 * math.pi * i / 720)) for i in range(721)]
        penlib.brush_line(ink, pts, wdt, int(rr), tremor=0.3)
    sp = spiral_mask(int(0.40 * R), 0.175 * R)
    s0 = R - sp.shape[0] // 2
    Ms = cv2.getRotationMatrix2D((sp.shape[1] / 2, sp.shape[0] / 2), -rot_deg, 1.0)
    sp = cv2.warpAffine(sp, Ms, sp.shape[::-1])
    ink[s0:s0 + sp.shape[0], s0:s0 + sp.shape[1]] = np.maximum(ink[s0:s0 + sp.shape[0], s0:s0 + sp.shape[1]], sp)
    comp(img, ink, PRINT)
    comp(img, tmask, PRINT)
    comp(img, nmask, RED)
    alpha = (r <= R - 1).astype(np.float32)
    slot = np.zeros((D, D), np.uint8)
    for j in range(NS):
        a = (j + 0.5) * 2 * math.pi / NS + math.radians(rot_deg)
        p0 = (R + 0.855 * R * math.sin(a), R - 0.855 * R * math.cos(a))
        p1 = (R + 0.965 * R * math.sin(a), R - 0.965 * R * math.cos(a))
        cv2.line(slot, (int(p0[0] * 4), int(p0[1] * 4)), (int(p1[0] * 4), int(p1[1] * 4)), 255, 4 * 15, cv2.LINE_AA, shift=2)
    hole = (r <= 14).astype(np.uint8) * 255
    cut = np.maximum(slot, hole)
    alpha *= 1 - cut.astype(np.float32) / 255
    return img, alpha, cut


def build(rot=0.0):
    page = SHEET.copy()
    img, alpha, cut = disc(rot)
    D = 2 * R
    big = np.zeros(page.shape[:2], np.uint8)
    big[CY - R:CY + R, CX - R:CX + R] = (alpha * 255).astype(np.uint8)
    penlib.shadow_onto(page, big, off=14, blur=10, opacity=0.45)
    sub = page[CY - R:CY + R, CX - R:CX + R]
    a = alpha[..., None]
    sub[:] = sub * (1 - a) + img * a
    # the slots: cut through the card, the shadowed sheet shows in them
    sh = cv2.GaussianBlur(cut, (0, 0), 3).astype(np.float32) / 255
    sub *= (1 - 0.86 * sh * (cut > 0))[..., None]
    # pin through the hub
    pin = np.zeros(sub.shape[:2], np.uint8)
    cv2.circle(pin, (R, R), 22, 255, -1, cv2.LINE_AA)
    comp(sub, pin, np.array([92, 84, 70], np.float32))
    cv2.circle(pin, (R, R), 22, 0, -1)
    cv2.circle(pin, (R - 6, R - 6), 7, 255, -1, cv2.LINE_AA)
    comp(sub, pin, np.array([220, 214, 200], np.float32))
    return page


def legend(page):
    """Reading directions under the disc, in the pen hand: text, a side-view diagram, a turning arrow."""
    m = np.zeros(page.shape[:2], np.uint8)
    lines = ["Spin the disc with its", "pictures facing a mirror.", "Look through a slot:",
             "he walks from the memo to", "the cupboard, beats 1 to 6."]
    blit_mask(m, letter_left(lines, 46, 680), 130, 2160)
    # side view: eye -> slot in the disc (edge on) -> mirror
    y = 2420
    ex, dxs, mx = 1290, 1560, 1960
    pts = [(ex - 46 + 92 * t, y - 26 * math.sin(math.pi * t)) for t in np.linspace(0, 1, 30)]
    penlib.brush_line(m, pts, 6, 681)
    pts = [(ex - 46 + 92 * t, y + 26 * math.sin(math.pi * t)) for t in np.linspace(0, 1, 30)]
    penlib.brush_line(m, pts, 6, 682)
    cv2.circle(m, (ex + 14, y), 13, 255, -1, cv2.LINE_AA)
    penlib.brush_line(m, [(dxs, y - 330), (dxs, y - 18)], 16, 683)       # the disc, edge on, with its slot
    penlib.brush_line(m, [(dxs, y + 18), (dxs, y + 230)], 16, 684)
    penlib.brush_line(m, [(dxs - 20, y + 236), (dxs + 20, y + 236)], 8, 689)
    penlib.brush_line(m, [(mx, y - 260), (mx, y + 230)], 12, 685)        # the mirror
    for k in range(10):
        yy = y - 250 + k * 50
        penlib.brush_line(m, [(mx + 6, yy), (mx + 36, yy + 26)], 4, 686 + k)
    for k in range(9):                                                   # dashed sight line
        x0 = ex + 70 + k * 64
        if x0 + 34 < mx - 10:
            penlib.brush_line(m, [(x0, y), (x0 + 34, y)], 5, 700 + k)
    for lab, x, yy in (("eye", ex - 40, y + 90), ("slot", dxs - 150, y - 90), ("mirror", mx - 190, y + 250),
                       ("pictures on", dxs + 40, y - 250), ("this side", dxs + 40, y - 195)):
        blit_mask(m, letter_left([lab], 36, 720 + len(lab)), int(x), int(yy))
    comp(page, m, PRINT)
    a = np.zeros(page.shape[:2], np.uint8)
    pts = [(CX + (R + 50) * math.sin(math.radians(t)), CY - (R + 50) * math.cos(math.radians(t))) for t in range(108, 146)]
    penlib.brush_line(a, pts, 9, 690, tremor=0.3)
    tip = np.array(pts[-1])
    d = tip - np.array(pts[-4])
    d /= np.linalg.norm(d)
    for s_ in (-1, 1):
        rot = np.array([[math.cos(s_ * 2.6), -math.sin(s_ * 2.6)], [math.sin(s_ * 2.6), math.cos(s_ * 2.6)]])
        q = tip + rot @ d * 42
        penlib.brush_line(a, [tuple(tip), tuple(q)], 9, 691 + s_)
    comp(page, a, RED)
    return page


def slot_view(k):
    """What the spinner sees: sector k brought to the top, the rest of the page dark, the slot lit."""
    page = build(-k * 360 / NS)
    legend(page)
    p = np.clip(np.round(page), 0, 255).astype(np.uint8)
    pen99.folio(p, N, TITLE)
    p = p.astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dx, dy = xx - CX, yy - CY
    r = np.sqrt(dx * dx + dy * dy)
    th = np.abs(np.arctan2(dx, -dy))
    win = ((th < math.pi / NS) & (r < R * 0.99)).astype(np.float32)
    win = cv2.GaussianBlur(win, (0, 0), 6)
    p *= (0.18 + 0.82 * win)[..., None]
    return np.asarray(Image.fromarray(np.clip(p, 0, 255).astype(np.uint8)).resize((960, 1242), Image.LANCZOS))


if __name__ == "__main__":
    page = build(0.0)
    legend(page)
    img, size = save_page(page, N, PID, TITLE)
    print("jpeg bytes", size)
    if len(sys.argv) > 1 and sys.argv[1] == "beats":
        save_beats(N, [slot_view(k) for k in range(NS)])

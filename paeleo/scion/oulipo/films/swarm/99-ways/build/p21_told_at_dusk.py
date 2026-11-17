"""99 ways, page 21 "Told at dusk" (time and order; medium: rol-cutout).
Framed at six in the evening: the agent stands at the still-closed SERVICE door and goes back over the afternoon;
the incident sits in six warm afternoon prints laid inside a dusk frame.
Grammar of the rol-cutout kit (build_page04: press prints with white scissor margins, pasted caption slips with
red numbers, jumping red/black cover lettering in the shared pen hand). Material:
- the evening: the 99-ways-template rest layers of P3 (Rothstein 1937 office: the agent before the cupboard whose
  right leaf carries the SERVICE card), printed in a cold blue-grey tone with the lamp lit; the office clock cut out
  (99-ways-template LoC clock pieces) with its own hands re-set on the arbor to 6:00;
- the afternoon: the 99-ways-template rest layers P1, P4, P5, P6, P7, P8 in the warm sepia of page 04, with the
  stranger as the Agence Rol 34852 cutout (as on page 04) seen through the ticket-window glass in E1 and leaving in E3.
Run: python3 -I p21_told_at_dusk.py"""
import json
import math
import random
import sys

import cv2
import numpy as np
from PIL import Image

KIT = "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/kit"
sys.path.insert(0, KIT)
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import pen99  # noqa: E402
from pen99 import penlib, ROOT  # noqa: E402
import build_page04 as K  # noqa: E402  (rol-cutout kit: paste, affine, slip, jumpy, balloon, sepia, woman)
import build_page01 as b01  # noqa: E402
from cutpaper99 import hexc  # noqa: E402
import b1m2 as B  # noqa: E402

N, PID, TITLE = 21, "told-at-dusk", "Told at dusk"
W, H = pen99.PAGE_W, pen99.PAGE_H
CANON = json.load(open(ROOT / "films/swarm/99-ways/canon.json"))
LN = {k: v["text"] for k, v in CANON["incident"]["lines"].items()}
OLD = K.OLD
PCS = ROOT / "films/sources/99-ways-template/page-cartoonist/pieces"
MAN = json.load(open(PCS / "manifest.json"))

DUSK, DUSK_HI = hexc("#2f3442"), hexc("#454b5c")
BUTTER, RED, BLACK, SLIP, PRINT_W = K.BUTTER, K.RED, K.BLACK, K.SLIP, K.PRINT_W
LAMP = np.array([255, 214, 140], np.float32)

Q = ["Pardon me —", "have you the", "right time?"]
A = ["Ten past four,", "by the clock."]
T = ["Much", "obliged!"]
F = ["Well, here I am...", "and what for?"]
assert " ".join(Q) == LN["question"] and " ".join(A) == LN["answer"] and " ".join(T) == LN["thanks"] and " ".join(F) == LN["forgetting"]

CROPS = {"P1": (0, 160, 740, 930), "P4": (0, 300, 560, 883), "P5": (40, 0, 940, 937),
         "P6": (0, 200, 600, 883), "P7": (0, 0, 1000, 980), "P8": (150, 0, 1150, 980)}
# key, event, time slip, caption (the afternoon, as he goes back over it), balloon
CELLS = [
    ("P1", "E0", "4:08", ["He had his memo:", "open the SERVICE", "door at 4:15. Up", "he got."], None),
    ("P4", "E1", "4:09", ["On his way, a lady", "at the window:"], (Q, 38, (0.50, 0.17))),
    ("P5", "E2", "4:10", ["He looked at", "the clock:"], (A, 42, (0.50, 0.16))),
    ("P6", "E3", "4:10", ["She thanked him", "and went."], (T, 48, (0.55, 0.20))),
    ("P7", "E4", "4:11", ["He opened the", "cupboard. There", "hung the key."], None),
    ("P8", "E5", "4:11", ["And there he stood."], (F, 38, (0.45, 0.15))),
]


HER_AT = {"P4": (150, 335), "P6": (100, 285)}


def rest(key):
    c, used = b01.panel_rest(key)
    x0, y0, x1, y1 = CROPS[key]
    return c[y0:y1, x0:x1].mean(axis=2), (x0, y0), used


def rol_woman(g_print, key):
    """Paste the Rol 34852 stranger into a print (behind the ticket-window glass), in print px."""
    g, a = K.woman()
    g = g.mean(axis=2)
    g, a = g[:600], a[:600].astype(np.float32) / 255          # head and shoulders
    if key == "P4":
        s, cx, top, flip, op = 0.42, 140, 300, False, 0.80
    else:               # P6: she turns from the window, leaving to the left
        s, cx, top, flip, op = 0.48, 95, 250, True, 0.75
    if flip:
        g, a = g[:, ::-1], a[:, ::-1]
    gh, gw = int(g.shape[0] * s), int(g.shape[1] * s)
    g = cv2.resize(g, (gw, gh), interpolation=cv2.INTER_AREA)
    a = cv2.resize(a, (gw, gh), interpolation=cv2.INTER_AREA)
    a = cv2.GaussianBlur(a, (0, 0), 0.8) * op               # seen through the glass
    a *= np.clip((gh - np.arange(gh)[:, None]) / (gh * 0.30), 0, 1)       # lost below the counter
    x0 = int(cx - gw / 2)
    ph, pw = g_print.shape
    ys, ye = max(0, top), min(ph, top + gh)
    xs, xe = max(0, x0), min(pw, x0 + gw)
    sub_a = a[ys - top:ye - top, xs - x0:xe - x0]
    sub_g = g[ys - top:ye - top, xs - x0:xe - x0] * 0.92 + 14       # a little veiled by the glass
    g_print[ys:ye, xs:xe] = g_print[ys:ye, xs:xe] * (1 - sub_a) + sub_g * sub_a
    return g_print


def dusk_tone(g, lamp_xy=None):
    """The evening print: a cold blue-grey toning of the same photograph, darkened, the lamp lit."""
    L = np.clip(g / 255.0, 0, 1) ** 1.35
    lo, hi = np.array([22, 26, 40], np.float32), np.array([168, 178, 200], np.float32)
    rgb = lo + (hi - lo) * L[..., None]
    if lamp_xy is not None:
        h, w = g.shape
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        d2 = (xx - lamp_xy[0]) ** 2 + (yy - lamp_xy[1]) ** 2
        glow = np.exp(-d2 / (2 * 150 ** 2)) * 0.55 + np.exp(-d2 / (2 * 40 ** 2)) * 0.6
        rgb = rgb + (LAMP - rgb) * np.clip(glow, 0, 0.9)[..., None] * (0.35 + 0.65 * L[..., None])
    return rgb


def clock_six(scale):
    """The office clock cut out, its own hands re-set on the arbor to 6:00. Returns rgb, alpha (uint8)."""
    case = np.asarray(Image.open(PCS / "clock.case.png")).astype(np.float32)
    g = case[..., 0].copy()
    a = case[..., 3].copy()
    arb = MAN["pieces"]["clock.case"]["pivots_local"]["arbor"]
    ox, oy = MAN["pieces"]["clock.case"]["bbox_src"][:2]
    h, w = g.shape
    for n, ang in (("clock.hour", 180.0), ("clock.minute", 0.0)):
        im = np.asarray(Image.open(PCS / f"{n}.png")).astype(np.float32)
        p = MAN["pieces"][n]
        hx, hy = p["bbox_src"][:2]
        piv = p["pivots_local"]["arbor"]
        rot = ang - p["source_angle_deg"]
        # piece px -> case px: translate so its arbor lands on the case arbor, rotate about that arbor
        M = cv2.getRotationMatrix2D((float(piv[0]), float(piv[1])), -rot, 1.0)
        M[0, 2] += arb[0] - piv[0]
        M[1, 2] += arb[1] - piv[1]
        hg = cv2.warpAffine(im[..., 0], M, (w, h), flags=cv2.INTER_CUBIC)
        ha = cv2.warpAffine(im[..., 3], M, (w, h), flags=cv2.INTER_LINEAR) / 255
        g = g * (1 - ha) + hg * ha
    # the hands' old positions are painted on the case itself? the cartoonist's case has its hands removed
    g = cv2.resize(g, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    a = cv2.resize(a, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    return g, a.astype(np.uint8)


def dots(img, p0, p1, n, r0, r1, seed):
    """Thought dots: small cut-paper discs from the remembering head toward the afternoon."""
    for k in range(n):
        t = k / (n - 1)
        x = p0[0] + (p1[0] - p0[0]) * t
        y = p0[1] + (p1[1] - p0[1]) * t - math.sin(t * math.pi) * 40
        r = r0 + (r1 - r0) * t
        m = np.zeros((H, W), np.uint8)
        cv2.circle(m, (int(x), int(y)), int(r), 255, -1, cv2.LINE_AA)
        K.shadow(img, m, off=(4, 5), blur=3, op=0.35)
        a = m.astype(np.float32)[..., None] / 255
        img[:] = img * (1 - a) + BUTTER * a
        cs, _ = cv2.findContours((m > 127).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        im = np.zeros((H, W), np.uint8)
        cv2.drawContours(im, cs, -1, 255, 4, cv2.LINE_AA)
        penlib.ink_onto(img, im, BLACK)


def light_slip(img, lines, cap, x, y, w, seed, deg=0.0, colour=None):
    """A caption slip on the dusk frame (pale card, pen lettering)."""
    return K.slip(img, lines, cap, x, y, w, seed, deg=deg)


def build(reveal=8):
    """reveal: 1 evening frame only; 2..7 + afternoon prints one by one; 8 + the closing evening slip."""
    img = pen99.sheet99().astype(np.float32)
    F_ = img.mean(axis=2) - img.mean()
    # ---- the evening frame: a dusk-blue card round the whole page
    fx0, fy0, fx1, fy1 = 110, 110, 2090, 2730
    yy = np.linspace(0, 1, fy1 - fy0)[:, None, None]
    img[fy0:fy1, fx0:fx1] = DUSK_HI * (1 - yy) + DUSK * yy + F_[fy0:fy1, fx0:fx1, None] * 1.2
    # the dusk print: the agent at the still-closed SERVICE door, 6 p.m.
    c, used3 = b01.panel_rest("P3")
    g = c.mean(axis=2)[0:880, 0:730]
    rgb = dusk_tone(g, lamp_xy=(640, 640))
    ph, pw = g.shape
    s = 780 / ph
    M = K.affine(150 + pw * s / 2 + 20, 140 + 780 / 2, s, 1.0, pw, ph)
    K.paste(img, rgb, np.full((ph, pw), 255, np.uint8), M, margin=16, op=0.5)
    head = M @ np.array([450.0, 470.0, 1.0])
    # the clock at six, cut out and pasted on the frame
    cg, ca = clock_six(0.95)
    crgb = K.sepia(np.dstack([cg] * 3), 0.05) * 0.86
    ch, cw = cg.shape
    K.paste(img, crgb, ca, K.affine(1060, 140 + ch / 2 + 20, 1.0, -2.0, cw, ch), margin=8, margin_col=hexc("#e9e4d6"), op=0.5)
    # cover lettering and the evening caption
    K.jumpy(img, "Six o'clock.", 1250, 300, 108, 2110, colours=(hexc("#f0c24a"), hexc("#f6efdc")))
    K.slip(img, ["Evening, the same day.", "The SERVICE door is still", "shut. He stands before it", "and goes back over the",
                 "afternoon..."], 44, 1255, 400, 760, 2111, deg=-0.8)
    # ---- the afternoon: a warm butter card laid inside the frame
    ax0, ay0, ax1, ay1 = 170, 1000, 2030, 2580
    am = np.zeros((H, W), np.uint8)
    cv2.fillPoly(am, [np.int32(np.array([(ax0, ay0 + 4), (ax1, ay0), (ax1 - 3, ay1), (ax0 + 2, ay1 - 3)]) * 4)], 255,
                 cv2.LINE_AA, shift=2)
    K.shadow(img, am, off=(9, 12), blur=8, op=0.5)
    a = am.astype(np.float32)[..., None] / 255
    t = np.linspace(0, 1, H)[:, None, None] ** 0.6
    card = K.BUTTER_TOP * (1 - t) + BUTTER * t + F_[..., None] * 0.8
    img[:] = img * (1 - a) + card * a
    K.jumpy(img, "That afternoon", 230, 1085, 70, 2112)
    # thought dots from his head (evening) down onto the afternoon card
    dots(img, (870, 600), (880, 960), 5, 9, 24, 2113)
    rec = {}
    ROWS = [(1130, 1590), (1610, 2070), (2090, 2550)]
    COLS = [(200, 1100), (1100, 2000)]
    for i, (key, ev, tm, cap_lines, bal) in enumerate(CELLS):
        if i >= reveal - 1:
            continue
        r, col = divmod(i, 2)
        y0, y1 = ROWS[r]
        x0, x1 = COLS[col]
        g, off, used = rest(key)
        if key in ("P4", "P6"):
            g = rol_woman(g, key)
        ph, pw = g.shape
        sc = 430 / ph
        dw = pw * sc
        left = (col == 0)
        px = x0 + 30 + dw / 2 if left else x1 - 30 - dw / 2
        py = (y0 + y1) / 2
        deg = [-1.0, 1.1, 0.8, -0.9, -1.2, 1.0][i]
        rgb = K.sepia(np.dstack([g] * 3)).astype(np.float32)
        M = K.affine(px, py, sc, deg, pw, ph)
        K.paste(img, rgb, np.full((ph, pw), 255, np.uint8), M, margin=14, op=0.4)
        # caption slip with red number and its time
        sw = 330
        lw_ = pen99.letter(cap_lines, 36, 2120 + i).shape[1]
        ww_ = max(sw, lw_ + int(36 * 0.6))
        sx = (px + dw / 2 + 24) if left else (px - dw / 2 - ww_ - 24)
        ww, hh = K.slip(img, cap_lines, 36, sx, y0 + 60, sw, 2120 + i, deg=[0.8, -0.6, -1.0, 0.7, 0.9, -0.8][i],
                        num=i + 1, num_right=left)
        tmm = pen99.letter([tm], 46, 2130 + i, weight=0.17)
        K.ink_at(img, tmm, sx + ww / 2 - tmm.shape[1] / 2, y0 + 60 + hh + 8, hexc("#8a3a1c"))
        if bal:
            lines, cap, ctr = bal
            P = lambda q: M @ np.array([q[0], q[1], 1.0])
            cx, cy = P((ctr[0] * pw, ctr[1] * ph))
            o = OLD[key][0]["tail_tip_panel_px"]
            tip = P((o[0] - off[0], o[1] - off[1]))
            if key in HER_AT:            # her lines: the tail goes to the Rol stranger behind the glass
                tip = P(HER_AT[key])
            let = pen99.letter(lines, cap, 1)
            rx = let.shape[1] * 0.5 * 1.18 + cap * 0.35
            ry = let.shape[0] * 0.5 * 1.10 + cap * 0.30
            lo, hi = px - dw / 2 + rx + 6, px + dw / 2 - rx - 6
            cx = float(np.clip(cx, lo, hi)) if lo < hi else float(px)
            cy = max(cy, py - 215 + ry + 8)
            K.balloon(img, lines, cap, (cx, cy), tip, 2140 + i)
        rec[key] = dict(event=ev, time=tm, caption=" ".join(cap_lines), print_layers=used,
                        balloon=(" ".join(bal[0]) if bal else None), rol_stranger=key in ("P4", "P6"))
    if reveal >= 8:
        # the frame closes: back to six o'clock
        K.slip(img, ["Six o'clock still. The key hangs on its hook; the SERVICE door stays shut;",
                     "and what he came for, he cannot say."], 40, 250, 2600, 1700, 2150, deg=0.3)
    pen99.folio(img, N, TITLE)
    return np.clip(np.round(img), 0, 255).astype(np.uint8), rec, used3


def main():
    page, rec, used3 = build(8)
    out_png = B.MASTERS / f"{N:02d}-{PID}.png"
    out_jpg = B.PAGES_OUT / f"{N:02d}-{PID}.jpg"
    Image.fromarray(page).save(out_png, compress_level=6)
    Image.fromarray(page).save(out_jpg, quality=90)
    size = out_jpg.stat().st_size
    print("bytes", size)
    if "--page-only" in sys.argv:
        return
    frames = [build(j)[0] for j in range(1, 8)] + [page]
    B.save_beats(N, frames)
    json.dump(rec, open(B.SRC / f"p21_rec.json", "w"), indent=1)


if __name__ == "__main__":
    main()

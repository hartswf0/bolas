"""Page 73 Cover (layout and page grammar; medium: rol-cutout).

The incident as the front cover of a 1937 story paper (our own invented title, STATION STORIES): masthead on a red
band, dateline strip, one dramatic picture (the 99-ways-template Rothstein rest layers of the forgetting, recomposed
without balloons: the agent, pencil to his chin, before the open cupboard and the key on its hook, the SERVICE card
behind), and cover lines that carry E0-E5. The masthead ear holds the Agence Rol 34852 woman (page 04's cutout) as
the lady at the window. Cover grammar of the rol-cutout kit (kit/build_page04: butter ground, warm grey band,
jumping red/black lettering letter by letter in the shared pen hand, pasted slips; no font).
Run: python3 -I p73_cover.py [beats]
"""
import sys

import cv2
import numpy as np

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/kit")
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import pen99  # noqa: E402
from pen99 import penlib  # noqa: E402
import build_page01 as b01  # noqa: E402
import build_page04 as k4  # noqa: E402
from cutpaper99 import hexc  # noqa: E402
from b1m2 import save_page, save_beats  # noqa: E402

N, PID, TITLE = 73, "cover", "Cover"
W, H = pen99.PAGE_W, pen99.PAGE_H
RED, BLACK, SLIP, BAND, CREAM = k4.RED, k4.BLACK, k4.SLIP, k4.BAND, hexc("#fff3d2")
MAST = hexc("#b8240c")
PIC = (110, 590, 2090, 2160)


def text_ink(img, lines, cap, x, y, colour, seed, centre=False, weight=0.13):
    m = pen99.letter(lines, cap, seed, weight=weight)
    if centre:
        x = x - m.shape[1] / 2
    k4.ink_at(img, m, x - cap * 0.6, y, colour)
    return m.shape


def picture(img):
    c, used = b01.panel_rest("P8")
    x0, y0, x1, y1 = PIC
    bw, bh = x1 - x0 - 36, y1 - y0 - 36
    s = bw / c.shape[1]
    g = cv2.resize(c, (bw, int(c.shape[0] * s)), interpolation=cv2.INTER_CUBIC)
    oy = max(0, (g.shape[0] - bh) // 2 - 10)
    g = g[oy:oy + bh]
    g = k4.sepia(np.dstack([g.mean(axis=2)] * 3), 0.10)
    # the print: white border, pasted with its shadow
    m = np.zeros((H, W), np.uint8)
    m[y0:y1, x0:x1] = 255
    k4.shadow(img, m, op=0.4)
    img[y0:y1, x0:x1] = k4.PRINT_W
    img[y0 + 18:y0 + 18 + bh, x0 + 18:x0 + 18 + bw] = g
    return used, s, oy


def masthead(img):
    img[110:470, 110:2090] = img[110:470, 110:2090] * 0.12 + MAST * 0.88
    text_ink(img, ["EVERY THURSDAY"], 34, 150, 120, CREAM, 7301)
    text_ink(img, ["No. 371  -  5 CENTS"], 34, 1260, 120, CREAM, 7302)
    k4.jumpy(img, "STATION STORIES", 170, 375, 148, 7303, colours=(CREAM, BLACK))
    img[470:548, 110:2090] = BLACK * 0.92 + img[470:548, 110:2090] * 0.08
    text_ink(img, ["SEPTEMBER 23, 1937  -  A COMPLETE RAILWAY TALE IN THIS ISSUE"], 36, 1100, 472, CREAM, 7304,
             centre=True)
    # the ear: a round print of the lady at the window, and the price
    g, a = k4.woman()
    g, a = g[:430], a[:430]
    cx, cy, r = 1880, 270, 150
    disc = np.zeros((H, W), np.uint8)
    cv2.circle(disc, (cx, cy), r + 12, 255, -1, cv2.LINE_AA)
    k4.shadow(img, disc, op=0.4)
    dm = disc.astype(np.float32)[..., None] / 255
    img[:] = img * (1 - dm) + k4.PRINT_W * dm
    inner = np.zeros((H, W), np.uint8)
    cv2.circle(inner, (cx, cy), r, 255, -1, cv2.LINE_AA)
    im = inner.astype(np.float32)[..., None] / 255
    img[:] = img * (1 - im) + (BAND * 0.6 + 255 * 0.4) * im
    s = 360 / g.shape[0]
    M = k4.affine(cx - 6, cy + 30, s, 0, g.shape[1], g.shape[0])
    lay = img.copy()
    k4.paste(lay, k4.sepia(np.dstack([g.mean(2)] * 3)), a, M, margin=0, sh=False)
    img[:] = img * (1 - im) + lay * im


def cover_slip(img, lines, cap, x, y, w, seed, deg=0.0, red=False):
    if not red:
        return k4.slip(img, lines, cap, x, y, w, seed, deg=deg)
    let = pen99.letter(lines, cap, seed)
    lh, lw = let.shape
    hh, ww = lh + int(cap * 0.5), max(w, lw + int(cap * 0.6))
    rgb = np.zeros((hh, ww, 3), np.float32) + RED
    a = np.zeros((hh, ww), np.uint8)
    cv2.fillPoly(a, [np.array([(4, 6), (ww - 3, 2), (ww - 5, hh - 4), (3, hh - 2)], np.int32)], 255)
    L = np.zeros((hh, ww), np.uint8)
    oy, ox = (hh - lh) // 2, (ww - lw) // 2
    L[oy:oy + lh, ox:ox + lw] = let
    rgb = rgb * (1 - L[..., None] / 255.0) + CREAM * (L[..., None] / 255.0)
    k4.paste(img, rgb, a, k4.affine(x + ww / 2, y + hh / 2, 1.0, deg, ww, hh), sh=True, op=0.35)
    return ww, hh


LINES = {
    "E0": (["4:15, said the memo:", "open the SERVICE door!", "The key? In the cupboard."], False),
    "E1": (["Then a lady at the window:", "\"Pardon me — have you", "the right time?\""], True),
    "E2": (["\"Ten past four,", "by the clock.\""], False),
    "E3": (["\"Much obliged!\"", "- and she was gone."], True),
}


def build(reveal=9):
    img, _ = k4.ground()
    masthead(img)
    used, s, oy = picture(img)
    if reveal >= 2:     # the story title on a butter ribbon over the picture's top
        ww, hh = 1240, 190
        rgb = np.zeros((hh, ww, 3), np.float32) + SLIP
        al = np.zeros((hh, ww), np.uint8)
        cv2.fillPoly(al, [np.array([(0, 8), (ww - 40, 0), (ww, hh // 2), (ww - 36, hh - 2), (2, hh - 8), (34, hh // 2)], np.int32)], 255)
        k4.paste(img, rgb, al, k4.affine(150 + ww / 2, 640 + hh / 2, 1.0, 1.2, ww, hh), sh=True, op=0.4)
        k4.jumpy(img, "The SERVICE Key!", 220, 770, 120, 7311)
    ys = [1010, 1280, 1520, 1700]
    for i, k in enumerate(("E0", "E1", "E2", "E3")):
        if reveal >= 3 + i:
            lines, red = LINES[k]
            cover_slip(img, lines, 40, 1530, ys[i], 530, 7320 + i, deg=[1.2, -0.9, 0.8, -1.1][i], red=red)
    # foot band: E4 and E5
    if reveal >= 7:
        img[2190:2730, 110:2090] = img[2190:2730, 110:2090] * 0.1 + BAND * 0.9
        k4.jumpy(img, "He opens the cupboard -", 170, 2310, 92, 7330, colours=(CREAM, BLACK))
        k4.jumpy(img, "and there hangs the KEY!", 330, 2440, 92, 7331, colours=(CREAM, RED))
    if reveal >= 8:
        cover_slip(img, ["\"Well, here I am...", "and what for?\""], 50, 170, 2510, 700, 7332, deg=-1.5)
        text_ink(img, ["The SERVICE door stays shut!", "Why did he come? Read it inside."], 40, 1500, 2520, CREAM, 7333,
                 centre=True)
    return img, used


if __name__ == "__main__":
    page, used = build()
    img, size = save_page(page, N, PID, TITLE)
    print("jpeg bytes", size, used)
    if len(sys.argv) > 1 and sys.argv[1] == "beats":
        frames = []
        for r in (1, 2, 3, 4, 6, 7, 8):
            p = np.clip(np.round(build(r)[0]), 0, 255).astype(np.uint8)
            pen99.folio(p, N, TITLE)
            frames.append(cv2.resize(p, (960, 1242), interpolation=cv2.INTER_AREA))
        save_beats(N, frames)

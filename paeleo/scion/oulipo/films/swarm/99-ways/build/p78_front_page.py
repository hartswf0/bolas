"""Page 78 Front page (medium and material; medium: rol-cutout).

The incident as the front page of an invented local paper (THE VALLEY LANTERN, ours), the morning after:
masthead, dateline, a two-line headline with its deck, a column of report carrying E0-E5 and the four lines
verbatim, a press photograph of the scene (Rothstein's 1937 Randolph station, LoC), the agent before the open
cupboard (the 99-ways-template Rothstein rest layers, P7, without balloons), the lady at the window as an outlined
halftone (the Agence Rol 34852 cutout of page 04: the rol-cutout kit), captions, and one small notice.
Every photograph goes through a HANDMADE 45-degree dot screen (as a 1937 newspaper block was made); all lettering is
the shared pen hand (pen99), no font. Beats: the page made up on the stone, block by block.
Run: python3 -I p78_front_page.py [beats]
"""
import math
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/kit")
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import pen99  # noqa: E402
from pen99 import penlib  # noqa: E402
import build_page01 as b01  # noqa: E402
import build_page04 as k4  # noqa: E402
from cutpaper99 import hexc  # noqa: E402
from b1m2 import save_page, save_beats, letter_left, wrap, ROOT  # noqa: E402

N, PID, TITLE = 78, "front-page", "Front page"
W, H = pen99.PAGE_W, pen99.PAGE_H
NEWS = hexc("#ebe4d3")
INKN = hexc("#17140f")
STATION = ROOT / "films/sources/99-ways/forage/p74/t_v2400.jpg"


# ------------------------------------------------------------------ tools
def ground():
    F = pen99.sheet99().mean(axis=2)
    F = F - F.mean()
    return np.zeros((H, W, 3), np.float32) + NEWS + F[..., None] * 0.55


def halftone(g, pitch=7.0, deg=45.0, gain=1.0):
    """HANDMADE dot screen: g gray float 0..255 -> ink coverage 0..1 (round dots growing into a chequer)."""
    h, w = g.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    a = math.radians(deg)
    u = (xx * math.cos(a) + yy * math.sin(a)) / pitch
    v = (-xx * math.sin(a) + yy * math.cos(a)) / pitch
    s = (np.cos(2 * np.pi * u) + np.cos(2 * np.pi * v)) / 2      # -1..1 spot function
    t = (s + 1) / 2                                             # 0 at cell corners .. 1 at cell centres
    dark = np.clip((1 - g / 255.0) * gain, 0, 1)
    dark = dark * 0.94 + 0.03                                   # the screen never prints pure white or solid
    cov = np.clip((t - (1 - dark)) / 0.10 + 0.5, 0, 1)
    return cov


def print_block(img, g, x0, y0, x1, y1, alpha=None, gain=1.0, rule=True):
    """Print a gray picture g (resized to the box) as a halftone block in news ink; optional outline alpha."""
    bw, bh = x1 - x0, y1 - y0
    gg = cv2.resize(g.astype(np.float32), (bw, bh), interpolation=cv2.INTER_AREA)
    cov = halftone(gg, gain=gain)
    if alpha is not None:
        aa = cv2.resize(alpha.astype(np.float32), (bw, bh), interpolation=cv2.INTER_AREA) / 255.0
        cov = cov * aa
    cov = cv2.GaussianBlur(cov, (0, 0), 0.6)
    sub = img[y0:y1, x0:x1]
    sub[:] = sub * (1 - cov[..., None] * 0.93) + INKN * (cov[..., None] * 0.93)
    if rule:
        m = np.zeros((H, W), np.uint8)
        cv2.rectangle(m, (x0, y0), (x1, y1), 255, 3, cv2.LINE_AA)
        penlib.ink_onto(img, m, INKN)


def text(img, lines, cap, x, y, seed, centre=False, weight=0.13, colour=None, bold=0):
    """lines at (x, y) = top-left of the first line's cap box (or centre x)."""
    if centre:
        m = pen99.letter(lines, cap, seed, weight=weight)
        x = x - m.shape[1] / 2
        xo = 0
    else:
        m = letter_left(lines, cap, seed, weight=weight)
        xo = cap * 0.6
    if bold:
        m = cv2.dilate(m, np.ones((bold, bold), np.uint8))
    k4.ink_at(img, m, x - xo, y - cap * 1.15 + cap, INKN if colour is None else colour)
    return m.shape


def hrule(img, x0, x1, y, w=3):
    m = np.zeros((H, W), np.uint8)
    penlib.brush_line(m, [(x0, y), (x1, y)], w, int(x0 + y), tremor=0.25)
    penlib.ink_onto(img, m, INKN)


def vrule(img, x, y0, y1, w=3):
    m = np.zeros((H, W), np.uint8)
    penlib.brush_line(m, [(x, y0), (x, y1)], w, int(x + y0), tremor=0.25)
    penlib.ink_onto(img, m, INKN)


# ------------------------------------------------------------------ material
def station_gray():
    g = np.asarray(Image.open(STATION).convert("L")).astype(np.float32)
    g = g[230:1560, 90:2290]                      # inside the negative's rebate: roof, platform, tracks
    return np.clip((g - 20) / (230 - 20), 0, 1) ** 0.9 * 255


def agent_gray():
    c, used = b01.panel_rest("P7")
    g = c.mean(axis=2)
    return g[20:960, 60:1000], used


# ------------------------------------------------------------------ copy (ours)
Q, A, T, F = (pen99.clean(s) for s in ("Pardon me — have you the right time?", "Ten past four, by the clock.",
                                         "Much obliged!", "Well, here I am... and what for?"))
REPORT = [
    "RANDOLPH, Sept. 24. - The SERVICE door of Randolph station was not opened at 4:15 yesterday afternoon, as "
    "the agent's own memo said it should be.",
    "The agent was at his desk with the memo before him: \"4:15 - open SERVICE door. Key in cupboard.\" He rose "
    "and set off across the office for the brass key.",
    "On his way a lady at the ticket window stopped him. \"" + Q + "\" she asked.",
    "The agent looked up at the office clock, which stood at 4:10. \"" + A + "\" he told her.",
    "\"" + T + "\" said the lady, and she left the window.",
    "The agent went on to the cupboard and opened it. The brass key, tagged SERVICE, hung on its hook in plain view.",
    "There, pencil to his chin, he was heard to say: \"" + F + "\"",
    "The key stayed on its hook. The SERVICE door stayed closed.",
]
COL_CAP, COL_X0, COL_X1 = 35, 120, 700


def build(reveal=9):
    img = ground()
    # --- masthead
    text(img, ["WEATHER: fair and cool"], 30, 120, 118, 7801)
    text(img, ["THREE CENTS"], 30, 1880, 118, 7802)
    hrule(img, 110, 2090, 170, 4)
    text(img, ["THE VALLEY LANTERN"], 150, 1100, 192, 7803, centre=True, weight=0.17, bold=5)
    hrule(img, 110, 2090, 395, 3)
    text(img, ["Vol. XLI, No. 38      RANDOLPH, VERMONT, FRIDAY, SEPTEMBER 24, 1937      Four Pages"], 32, 1100, 408,
         7804, centre=True)
    hrule(img, 110, 2090, 462, 7)
    hrule(img, 110, 2090, 474, 2)
    if reveal >= 2:     # --- headline and deck
        text(img, ["STATION AGENT FORGETS"], 128, 1100, 500, 7810, centre=True, weight=0.16, bold=5)
        text(img, ["ERRAND AT CUPBOARD"], 128, 1100, 672, 7811, centre=True, weight=0.16, bold=5)
        text(img, ["Brass Key Stays on Its Hook; SERVICE Door Not Opened"], 54, 1100, 846, 7812, centre=True,
             weight=0.15, bold=2)
        hrule(img, 110, 2090, 935, 3)
    used = []
    if reveal >= 3:     # --- the press photograph: the scene
        print_block(img, station_gray(), 750, 960, 2090, 1770, gain=1.0)
        text(img, ["THE SCENE. Randolph station, seen from the tracks. The ticket office,",
                   "where the agent keeps his desk, his clock and his cupboard, is within."], 33, 760, 1792, 7820)
    vrule(img, 725, 960, 2720, 2)
    if reveal >= 4:     # --- the column of report
        text(img, ["LADY AT WINDOW", "ASKED THE TIME"], 44, (COL_X0 + COL_X1) / 2 - 10, 962, 7830, centre=True,
             weight=0.15, bold=2)
        hrule(img, 250, 570, 1092, 2)
        y = 1118
        lh = int(COL_CAP * 1.42)
        paras = REPORT if reveal >= 5 else REPORT[:4]
        for i, p in enumerate(paras):
            ls = wrap(p, COL_CAP, COL_X1 - COL_X0 - 10)
            text(img, ls, COL_CAP, COL_X0 + (0 if i == 0 else 0), y, 7840 + i)
            y += lh * len(ls) + 12
        col_end = y
    else:
        col_end = None
    hrule(img, 750, 2090, 1900, 2)
    if reveal >= 6:     # --- the agent at the cupboard; the lady (Rol cutout, outlined halftone)
        g, used = agent_gray()
        print_block(img, g, 760, 1925, 1395, 2560, gain=1.05)
        text(img, ["THE AGENT before the open", "cupboard. The key hangs on", "its hook, at left."], 33, 770, 2582, 7850)
        wg, wa = k4.woman()
        wg = wg.mean(axis=2)
        hh = 640
        ww = int(wg.shape[1] * hh / wg.shape[0])
        x0 = 1745 - ww // 2
        a8 = (wa > 127).astype(np.uint8) * 255
        print_block(img, wg, x0, 1925, x0 + ww, 1925 + hh, alpha=a8, gain=1.0, rule=False)
        text(img, ["THE LADY AT THE WINDOW,", "who asked the time.", "She has not been identified."], 33, 1440, 2582,
             7851)
        vrule(img, 1418, 1925, 2720, 2)
    if reveal >= 7:     # --- one small notice under the column
        bx0, by0 = 760, 2668
        text(img, ["LOST: one errand, at Randolph station, between desk and cupboard. Finder please call at the office."],
             28, 1425, by0, 7860, centre=True)
        m = np.zeros((H, W), np.uint8)
        cv2.rectangle(m, (bx0, by0 - 18), (2090, by0 + 44), 255, 2, cv2.LINE_AA)
        penlib.ink_onto(img, m, INKN)
    return img, used, col_end


if __name__ == "__main__":
    page, used, col_end = build()
    img, size = save_page(page, N, PID, TITLE)
    print("jpeg bytes", size, "column ends at", col_end, used)
    if len(sys.argv) > 1 and sys.argv[1] == "beats":
        frames = []
        for r in (1, 2, 3, 4, 5, 6, 7):
            p = np.clip(np.round(build(r)[0]), 0, 255).astype(np.uint8)
            pen99.folio(p, N, TITLE)
            frames.append(cv2.resize(p, (960, 1242), interpolation=cv2.INTER_AREA))
        save_beats(N, frames)

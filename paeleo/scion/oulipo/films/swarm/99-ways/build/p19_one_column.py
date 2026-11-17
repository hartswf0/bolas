"""99 ways, page 19 "One column" (layout and page grammar; medium: engraving-puppet).
Ten wide, shallow storyboard panels stacked in ONE column, read top to bottom; no two panels side by side. Each board:
a graphite board number in the left gutter, a strip of cream card with the cut-paper ENGRAVING PUPPETS of page 03
(AGENT = the Harper's Weekly 1863 telegraph operator, LoC cph.3c11072, cut at the joints and pinned; STRANGER = the
hatted woman of the 1867 Steinway Hall engraving, LoC cph.3c32079; his table and the glazed window from the 1863 plate),
the set in the shared pen hand (clock, cupboard on its left jamb, key with SERVICE tag, SERVICE door, memo), the four
canon lines as cut-paper balloons, and a pinned commentary slip.
Reuses films/swarm/99-ways/kit/build_page03.py (puppet cutting and the pen set). Run: python3 -I p19_one_column.py"""
import json
import random
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/kit")
import pen99  # noqa: E402
from pen99 import penlib, ROOT  # noqa: E402
from cutpaper99 import hexc  # noqa: E402
import build_page03 as b3  # noqa: E402

CANON = json.load(open(ROOT / "films/swarm/99-ways/canon.json"))
C = [c for c in CANON["constraints"] if c["id"] == "one-column"][0]
LN = {k: v["text"] for k, v in CANON["incident"]["lines"].items()}
SRC = ROOT / "films/sources/99-ways"
OUT_JPG = ROOT / "assets/pages/99-ways/19-one-column.jpg"
OUT_PNG = SRC / "masters/19-one-column.png"
BEATS = SRC / "beats/19"
W, H = pen99.PAGE_W, pen99.PAGE_H
OPS = b3.OPS
pen, letters, Mof, lay = b3.pen, b3.letters, b3.Mof, b3.lay

X0, X1 = 196, 2090
PW = X1 - X0
PH = 222
GAP = 40
Y0 = 116
GY = PH - 18
SA = 0.188          # agent puppet scale (about 200 px tall)
SW = 0.25           # stranger puppet scale

Q = ["Pardon me —", "have you the right time?"]
A = ["Ten past four,", "by the clock."]
T = ["Much obliged!"]
F = ["Well, here I am...", "and what for?"]
assert " ".join(Q) == LN["question"] and " ".join(A) == LN["answer"] and " ".join(T) == LN["thanks"] and " ".join(F) == LN["forgetting"]
BCAP = 32

BOARDS = [  # n, event, commentary slip
    (1, "E0", "4:08. The memo on his desk."),
    (2, "E0", "4:09. He rises."),
    (3, "E0", "He sets off for the cupboard."),
    (4, "E1", "On his way, a lady at the window."),
    (5, "E2", "He looks up at the clock."),
    (6, "E2", "4:10. He tells her."),
    (7, "E3", "She thanks him and goes."),
    (8, "E3", "He walks on."),
    (9, "E4", "He opens the cupboard: the key."),
    (10, "E5", "The key stays. The door stays shut."),
]


def sdoor(c, x0, y0, x1, y1, seed):
    pen(c, [(x0, y1), (x0, y0), (x1, y0), (x1, y1)], 4, seed)
    pen(c, [(x1 - 16, (y0 + y1) / 2), (x1 - 8, (y0 + y1) / 2)], 5, seed + 1)
    cx = (x0 + x1) / 2
    pen(c, [(cx - 44, y0 + 22), (cx + 44, y0 + 22), (cx + 44, y0 + 50), (cx - 44, y0 + 50)], 2.5, seed + 2, closed=True)
    letters(c, ["SERVICE"], 16, cx, y0 + 36, seed + 3)


def cupboard(c, x0, y0, x1, y1, open_k, seed):
    """cupboard on the left jamb, as build_page03 but at storyboard scale (key s=0.7)"""
    pen(c, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 4, seed, closed=True)
    if open_k > 0:
        for i, yy in enumerate(np.linspace(y0 + 70, y1 - 20, 3)):
            pen(c, [(x0 + 6, yy), (x1 - 6, yy)], 2.5, seed + 10 + i)
        b3.key(c, x0 + (x1 - x0) * 0.42, y0 + 10, 0.62, seed + 30)
        dx = (x1 - x0) * (1 - 0.85 * open_k)
        pen(c, [(x0, y0), (x0 - dx * 0.55, y0 - 12 * open_k), (x0 - dx * 0.55, y1 + 12 * open_k), (x0, y1)], 4, seed + 40)
    else:
        pen(c, [(x1 - 12, (y0 + y1) / 2 - 8), (x1 - 12, (y0 + y1) / 2 + 8)], 4, seed + 41)
        pen(c, [(x0 + 10, y0 + 10), (x1 - 10, y0 + 10), (x1 - 10, y1 - 10), (x0 + 10, y1 - 10)], 2, seed + 42, closed=True)


def window(c, P, x, seed, behind=None):
    """the glazed window from the 1863 plate, lettered TICKET OFFICE, in the back wall; whoever stands on the platform
    side is seen THROUGH it: the plate's engraved line is printed over her (multiplied), its paper left clear"""
    M = Mof(0.62, 0, np.array([140, 280]) * OPS, (x, GY - 96))
    pc = P["window"]
    ox, oy = pc["origin"]
    MM = (np.vstack([M, [0, 0, 1]]) @ np.array([[1, 0, ox], [0, 1, oy], [0, 0, 1]], np.float64))[:2]
    a = cv2.warpAffine(pc["a"], MM, (PW, PH), flags=cv2.INTER_LINEAR)
    rgb = cv2.warpAffine(pc["rgb"].astype(np.float32), MM, (PW, PH), flags=cv2.INTER_AREA)
    ab = (a > 127).astype(np.uint8) * 255
    pm = penlib.scissor(ab, 4)
    penlib.shadow_onto(c, pm, off=4, blur=3, opacity=0.25)
    edge = cv2.subtract(pm, cv2.erode(ab, np.ones((3, 3), np.uint8)))
    c[:] = c * (1 - edge[..., None] / 255 * (pm[..., None] > 0)) + b3.CARD * (edge[..., None] / 255 * (pm[..., None] > 0))
    if behind is not None:
        behind()
    af = (a.astype(np.float32) / 255)[..., None]
    c[:] = c * (1 - af) + c * (rgb / b3.CARD) * af
    letters(c, ["TICKET", "OFFICE"], 15, x, GY - 70, seed)


def balloon(c, lines, cap, centre, tip, seed):
    b = penlib.balloon_piece([pen99.clean(l) for l in lines], cap, (tip[0] - centre[0], tip[1] - centre[1]), seed,
                             tail_w=0.20, bend=0.08)
    penlib.lay_balloon(c, b, centre)


def mouth_of(foot, flip):
    """the agent's mouth for a standing puppet at foot (scale SA)"""
    return (foot[0] + (6 if flip else -6), foot[1] - 168)


DESK_X, CLOCK_X, WIN_X, CUP = 300, 640, 1000, (1480, 50, 1610)
SDOOR = (1690, 44, 1810)


def office(c, P, n, open_k=0.0, woman=None):
    """the same office frieze in every board 2-10: desk + memo, clock, ticket window (her behind it), cupboard, SERVICE door"""
    lay(c, P["table"], Mof(0.22, 0, np.array([250, 980]) * OPS, (DESK_X, GY + 2)))
    b3.memo(c, DESK_X - 38, GY - 128, 0.3, 1921 + n, deg=-4)
    b3.clock(c, CLOCK_X, 46, 26, 4, 9 if n < 5 else 10, 1940 + n)
    behind = (lambda: b3.woman(c, P, (WIN_X + woman[0], GY + 2), SW, flip=woman[1])) if woman else None
    window(c, P, WIN_X, 1950 + n, behind)
    cupboard(c, CUP[0], CUP[1], CUP[2], GY - 6, open_k, 1930 + n)
    sdoor(c, SDOOR[0], SDOOR[1], SDOOR[2], GY, 1935 + n)


def panel(n, P, with_line=True):
    c = np.zeros((PH, PW, 3), np.float32) + b3.CARD + (np.random.RandomState(1900 + n).rand(PH, PW, 1) - 0.5) * 1.2
    b3.ground_line(c, 0, PW, GY, 1910 + n)
    s = SA
    if n > 1:
        office(c, P, n, open_k={9: 0.75, 10: 1.0}.get(n, 0.0), woman={4: (0, False), 5: (0, False), 6: (0, False), 7: (30, True)}.get(n))
    if n == 1:      # E0 close: the memo, his finger on it
        b3.memo(c, 820, 112, 0.62, 1920, deg=-3)
        hand = np.array([336, 446], np.float32) * OPS
        M = Mof(0.5, 35, hand, (930, 150))
        lay(c, P["armU"], M, lift=3)
        lay(c, P["armF"], M, lift=4)
    elif n == 2:
        b3.agent(c, P, (470, GY + 2), s, arms=(0, 0, 0))
    elif n == 3:
        b3.agent(c, P, (700, GY + 2), s, arms=(12, 0, -8), flip=True)
    elif n == 4:
        b3.agent(c, P, (820, GY + 2), s, arms=(12, 0, -8), flip=True, head=8)
        if with_line:
            balloon(c, Q, BCAP, (1250, 66), (WIN_X + 22, 50), 1960)
    elif n in (5, 6):
        b3.agent(c, P, (800, GY + 2), s, arms=(60, 150, 0), head=-14)
        if with_line and n == 6:
            balloon(c, A, BCAP, (1250, 66), (812, 42), 1961)
    elif n == 7:
        b3.agent(c, P, (820, GY + 2), s, arms=(0, 0, 0), flip=True)
        if with_line:
            balloon(c, T, BCAP + 2, (1260, 60), (WIN_X + 44, 52), 1962)
    elif n == 8:
        b3.agent(c, P, (1250, GY + 2), s, arms=(12, 0, -8), flip=True)
    elif n == 9:
        b3.agent(c, P, (1390, GY + 2), s, arms=(-62, 30, 0), flip=True)
    else:
        h = b3.agent(c, P, (1390, GY + 2), s, arms=(47, 132, 0), head=-6, flip=True)
        pen(c, [(h[0] + 1, h[1] + 2), (h[0] - 3, h[1] - 19)], 3.5, 1980)
        if with_line:
            balloon(c, F, BCAP, (1110, 62), (1400, 46), 1981)
    return c


def slip(pg, text, x, y, seed):
    """a torn commentary slip pinned to the board (as page 03's slips)"""
    return b3.slip(pg, [text], 28, x, y, seed)


def build(upto=10, line_on=None):
    pg = pen99.sheet99()
    P = b3.load_puppets()
    for (n, ev, txt) in BOARDS:
        if n > upto:
            continue
        y = Y0 + (n - 1) * (PH + GAP)
        pg[y:y + PH, X0:X0 + PW] = panel(n, P, with_line=(line_on is None or n < upto or line_on))
        bm = penlib.border_mask(pg.shape[:2], [(X0, y, X0 + PW, y + PH)], 7, 1990 + n)
        penlib.ink_onto(pg, bm)
        hole = np.zeros(pg.shape[:2], np.uint8)
        cv2.circle(hole, (X0 + 22, y + 22), 8, 255, -1, cv2.LINE_AA)
        penlib.ink_onto(pg, hole, hexc("#2a2622"))
        # board number in the left gutter, graphite
        m = pen99.letter([f"{n}"], 46, 1995 + n)
        sub = np.zeros(pg.shape[:2], np.uint8)
        yy = y + PH // 2 - m.shape[0] // 2
        xx = 110 + (70 - m.shape[1]) // 2 + 4
        sub[yy:yy + m.shape[0], xx:xx + m.shape[1]] = m
        penlib.ink_onto(pg, sub, b3.GRAPH)
        # commentary slip, pinned across the board's top edge at the left (over the wall, clear of the figures)
        slip(pg, txt, X0 + 46, y - 22, 2000 + n)
    pen99.folio(pg, 19, C["title"])
    return np.clip(np.round(pg), 0, 255).astype(np.uint8)


def main():
    for p in (OUT_JPG.parent, OUT_PNG.parent, BEATS):
        p.mkdir(parents=True, exist_ok=True)
    page = build(10)
    Image.fromarray(page).save(OUT_PNG, compress_level=6)
    Image.fromarray(page).save(OUT_JPG, quality=90, dpi=(300, 300))
    size = OUT_JPG.stat().st_size
    print("jpeg", size)
    if "--page-only" in sys.argv:
        return
    for f in BEATS.glob("b*.png"):
        f.unlink()
    # the film's beat: boards pinned down the column one by one, the camera reading top to bottom
    seq = [2, 4, 6, 7, 9, 10]
    bd = []
    for j, up in enumerate(seq, 1):
        im = page if up == 10 else build(up)
        Image.fromarray(im).resize((960, 1242), Image.LANCZOS).save(BEATS / f"b{j:02d}.png")
        bd.append(f"b{j:02d}: boards 1-{up} pinned down the column (board {up}: {BOARDS[up - 1][1]})")
    record = {
        "n": 19, "id": C["id"], "title": C["title"], "rule": C["rule"], "medium": C["medium"], "family": C["family"],
        "canon_revision": CANON["revision"], "declares": C["declares"],
        "file": str(OUT_JPG.relative_to(ROOT)), "master": str(OUT_PNG.relative_to(ROOT)), "beats_dir": str(BEATS.relative_to(ROOT)),
        "build": "films/swarm/99-ways/build/p19_one_column.py",
        "sources": ["99-ways:loc-harpers-1863-army-telegraph-operator", "99-ways:loc-1867-dickens-tickets-steinway",
                    "99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"],
        "made": [
            "ten storyboard boards, each a 1894 x 222 px strip of cream card, stacked in one column with 40 px gutters; board numbers 1-10 in graphite in the left gutter; a punched hole at each board's corner",
            "AGENT and STRANGER as the engraving puppets of page 03 (films/swarm/99-ways/kit/build_page03.py: the 1863 telegraph operator cut at the joints and pinned with brass pins; the 1867 hatted woman cut along a drawn path; the operator's table and glazed window from the same plate), printed as ink on cream card, re-posed per board",
            "set in the shared pen hand (HANDMADE): memo with the canon text, wall clock at 4:10, cupboard hinged on the left jamb with the key on its hook and SERVICE tag, SERVICE door lettered SERVICE, TICKET OFFICE on the window",
            "the four canon lines as cut-paper balloons in the shared pen hand (penlib.balloon_piece); ten torn commentary slips pinned with brass pins (build_page03.slip)",
            "hand-ruled borders (penlib.border_mask); folio '19 / One column' (pen99.folio)"],
        "events": {f"board {n}": f"{ev}: {t}" for (n, ev, t) in BOARDS},
        "lines": LN,
        "beat": "the boards are pinned down the single column one after another, so the story is read as a camera tilting down a storyboard",
        "beat_frames": bd,
        "self_check": {"size_px": [page.shape[1], page.shape[0]], "jpeg_bytes": size, "jpeg_quality": 90,
                       "in_target_0.4_1.2MB": 400000 <= size <= 1200000,
                       "panels": len(BOARDS), "columns": 1, "panel_px": [PW, PH], "panel_aspect": round(PW / PH, 2),
                       "side_by_side_panels": 0, "lines_verbatim": True,
                       "pending": "independent blind reading not run by the maker"},
    }
    json.dump(record, open(ROOT / "films/swarm/99-ways/pages/19.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps(record["self_check"], indent=1))


if __name__ == "__main__":
    main()

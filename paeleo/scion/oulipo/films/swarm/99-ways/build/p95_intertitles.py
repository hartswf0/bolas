"""Page 95 Intertitles (genre; medium: rol-cutout).

A silent picture in one reel. Below an ornate main title card, twelve cells in a checkerboard: pantomime pictures
alternate with ornate title cards, so that every one of the four canon lines is read on a card between two pictures
and no balloon appears anywhere. Pictures: the 99-ways-template Rothstein rest layers recomposed WITHOUT their
balloons (kit/build_page01.panel_rest: P1 desk and memo, P5 under the clock at 4:10, P8 the open cupboard and the
forgetting; the last shot is P8 without the agent, irised in on the key on its hook); the stranger is the Agence Rol
34852 woman (page 04's cutout) pasted behind the TICKET OFFICE glass of rest layer P6. Every picture is printed as a
toned film frame inside a black gate with rounded corners and pasted as a print (kit/build_page04 paste, sepia).
Title cards: HANDMADE black cards with a pen-drawn cream double rule, corner scrolls and lettering in the shared hand.
Run: python3 -I p95_intertitles.py [beats]
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
from b1m2 import save_page, save_beats  # noqa: E402

N, PID, TITLE = 95, "intertitles", "Intertitles"
W, H = pen99.PAGE_W, pen99.PAGE_H
CW, CH = 633, 506
XS = (110, 110 + CW + 40, 110 + 2 * (CW + 40))
YS = [560 + r * (CH + 40) for r in range(4)]
CARD = hexc("#151311")
CREAM = hexc("#efe6cf")
TONE = hexc("#f1dfb8")
REST = b01.REST
SHEET = pen99.sheet99()

# the reel, cell by cell (row-major): ("pic", key, event) or ("card", lines, cap, kind)
REEL = [
    ("pic", "desk", "E0"),
    ("card", ["His memo:", "open the SERVICE door", "at 4:15. The key is", "in the cupboard."], 42, "title"),
    ("pic", "lady_ask", "E1"),
    ("card", ['"Pardon me —', 'have you the', 'right time?"'], 54, "line:STRANGER"),
    ("pic", "clock", "E2"),
    ("card", ['"Ten past four,', 'by the clock."'], 56, "line:AGENT"),
    ("pic", "lady_thanks", "E3"),
    ("card", ['"Much obliged!"'], 60, "line:STRANGER"),
    ("pic", "cupboard", "E4-E5"),
    ("card", ['"Well, here I am...', 'and what for?"'], 54, "line:AGENT"),
    ("pic", "iris_key", "E5"),
    ("card", ["The key stays on its hook;", "the SERVICE door", "stays closed.", "", "THE END"], 38, "end"),
]


# ------------------------------------------------------------------ the pictures
def _gray(c):
    return c.mean(axis=2) if c.ndim == 3 else c


def rest_without(key, drop=()):
    d = REST / key
    import json
    c = None
    for r in json.load(open(d / "layers.json"))["layers"]:
        n = r["name"]
        if n.startswith("b_") or n == "border" or any(n.startswith(p) for p in drop):
            continue
        im = np.asarray(Image.open(d / r["file"])).astype(np.float32)
        if c is None:
            c = im[..., :3].copy()
        else:
            a = im[..., 3:4] / 255
            c = c * (1 - a) + im[..., :3] * a
    return c


def lady_frame(thanks=False):
    """Rest layer P6 (the empty TICKET OFFICE window, from inside the office) with the Rol 34852 woman behind the glass."""
    bg = _gray(rest_without("P6"))                     # 940 x 600
    g, a = k4.woman()                                   # bust from her full-length cutout
    g, a = _gray(g)[:640], a[:640]
    s = 0.62 if not thanks else 0.60
    deg = 0 if not thanks else -7                       # a small bow of the head and shoulders for the thanks
    cx = 380 if not thanks else 420
    cy = 250 + 640 * s / 2 + (0 if not thanks else 18)
    if thanks:                                          # turning to go: the cutout reversed
        g, a = np.ascontiguousarray(g[:, ::-1]), np.ascontiguousarray(a[:, ::-1])
    M = k4.affine(cx, cy, s, deg, g.shape[1], g.shape[0])
    ww = cv2.warpAffine(g, M, (bg.shape[1], bg.shape[0]), flags=cv2.INTER_CUBIC)
    aa = cv2.warpAffine(a, M, (bg.shape[1], bg.shape[0])).astype(np.float32) / 255
    aa[700:] = 0                                        # the counter is in front of her
    glass = 0.82                                        # seen through the glass: a little haze from the pane
    out = bg * (1 - aa * glass) + (ww * 0.86 + 28) * aa * glass
    # the gilt TICKET OFFICE letters are on the glass, in front of her: lay their light strokes back
    loc = cv2.GaussianBlur(bg, (0, 0), 9)
    lm = np.clip((bg - loc - 14) / 22, 0, 1)
    lm[:280] = 0; lm[620:] = 0
    out = out * (1 - lm * aa) + bg * (lm * aa)
    return out


def picture(kind):
    """Return a grey frame image at the cell's aspect (1.25)."""
    if kind == "desk":
        c = _gray(rest_without("P1"))[290:290 + 592, 0:740]
    elif kind == "clock":
        c = _gray(rest_without("P5"))[130:130 + 776, 0:970]
    elif kind == "cupboard":
        c = _gray(rest_without("P8"))[28:28 + 952, 0:1190]
    elif kind == "iris_key":
        c = _gray(rest_without("P8", drop=("clerk",)))[300:300 + 480, 0:600]
    elif kind == "lady_ask":
        c = lady_frame(False)[250:250 + 480, 0:600]
    elif kind == "lady_thanks":
        c = lady_frame(True)[250:250 + 480, 0:600]
    c = cv2.resize(c, (CW - 40, CH - 40), interpolation=cv2.INTER_AREA)
    if kind == "iris_key":                               # iris in on the key and its SERVICE tag
        h, w = c.shape
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        kx, ky = 200 / 600 * w, 290 / 480 * h
        r = np.sqrt((xx - kx) ** 2 + ((yy - ky) * 1.0) ** 2)
        c = c * np.clip((205 - r) / 6, 0, 1)
    return c


def gate_mask(w, h, r=34):
    m = np.zeros((h, w), np.uint8)
    cv2.rectangle(m, (r, 0), (w - r, h), 255, -1)
    cv2.rectangle(m, (0, r), (w, h - r), 255, -1)
    for (x, y) in ((r, r), (w - r, r), (r, h - r), (w - r, h - r)):
        cv2.circle(m, (x, y), r, 255, -1, cv2.LINE_AA)
    return m


def lay_picture(img, kind, x0, y0):
    c = picture(kind)
    # the print: a black film gate with rounded corners, toned picture inside
    pm = np.zeros((H, W), np.uint8)
    cv2.rectangle(pm, (x0, y0), (x0 + CW, y0 + CH), 255, -1)
    k4.shadow(img, pm, op=0.40)
    img[y0:y0 + CH, x0:x0 + CW] = CARD
    g = np.clip((c - 10) / 235, 0, 1)
    rgb = (g ** 1.05)[..., None] * TONE
    yy, xx = np.mgrid[0:CH - 40, 0:CW - 40].astype(np.float32)
    v = 1 - 0.22 * (((xx - (CW - 40) / 2) / (CW / 2)) ** 2 + ((yy - (CH - 40) / 2) / (CH / 2)) ** 2)
    rgb = rgb * v[..., None]
    gm = gate_mask(CW - 40, CH - 40).astype(np.float32)[..., None] / 255
    sub = img[y0 + 20:y0 + CH - 20, x0 + 20:x0 + CW - 20]
    sub[:] = sub * (1 - gm) + rgb * gm


# ------------------------------------------------------------------ the title cards
def ornament(m, x0, y0, w, h, seed):
    """Pen ornament of a title card: double rule, corner scrolls, a lozenge top and bottom (HANDMADE strokes)."""
    for ins, wd in ((22, 5), (34, 2)):
        pts = [(x0 + ins, y0 + ins), (x0 + w - ins, y0 + ins), (x0 + w - ins, y0 + h - ins), (x0 + ins, y0 + h - ins), (x0 + ins, y0 + ins)]
        penlib.brush_line(m, pts, wd, seed + ins, tremor=0.25)
    for k, (cx, cy, sx, sy) in enumerate(((x0 + 34, y0 + 34, 1, 1), (x0 + w - 34, y0 + 34, -1, 1),
                                          (x0 + 34, y0 + h - 34, 1, -1), (x0 + w - 34, y0 + h - 34, -1, -1))):
        sp = []
        for i in range(60):
            t = i / 59 * 2.2 * math.pi
            r = 34 * (1 - i / 75)
            sp.append((cx + sx * (r * math.cos(t) * 0.9 + 16), cy + sy * (r * math.sin(t) * 0.9 + 16)))
        penlib.brush_line(m, sp, 3, seed + 50 + k, tremor=0.2)
    for cy, s in ((y0 + 34, 1), (y0 + h - 34, -1)):
        cx = x0 + w / 2
        lz = [(cx - 26, cy), (cx, cy - 11), (cx + 26, cy), (cx, cy + 11), (cx - 26, cy)]
        cv2.fillPoly(m, [np.int32(np.array(lz) * 4)], 255, cv2.LINE_AA, shift=2)
        for d in (-1, 1):
            curl = [(cx + d * (36 + 70 * i / 20), cy + s * 9 * math.sin(i / 20 * math.pi)) for i in range(21)]
            penlib.brush_line(m, curl, 2.5, seed + 80 + d, tremor=0.2)


def lay_card(img, lines, cap, x0, y0, w, h, seed):
    pm = np.zeros((H, W), np.uint8)
    cv2.rectangle(pm, (x0, y0), (x0 + w, y0 + h), 255, -1)
    k4.shadow(img, pm, op=0.40)
    F = SHEET[y0:y0 + h, x0:x0 + w].mean(axis=2)
    img[y0:y0 + h, x0:x0 + w] = CARD + (F - F.mean())[..., None] * 0.35
    m = np.zeros((H, W), np.uint8)
    ornament(m, x0, y0, w, h, seed)
    let = pen99.letter([l if l else " " for l in lines], cap, seed + 1, weight=0.15)
    lh, lw = let.shape
    assert lw < w - 30, (lines, lw, w)
    k4.ink_at(img, let, x0 + w / 2 - lw / 2, y0 + h / 2 - lh / 2 + cap * 0.1, CREAM)
    penlib.ink_onto(img, m, CREAM)


def main_title(img):
    x0, y0, w, h = 110, 130, 1980, 390
    lay_card(img, [" "], 40, x0, y0, w, h, 9500)
    k4.jumpy(img, "THE SERVICE KEY", 560, y0 + 200, 120, 9501, colours=(CREAM,))
    m = pen99.letter(["A photoplay in one reel  -  Randolph station, Vermont, 1937"], 40, 9502, weight=0.14)
    k4.ink_at(img, m, 1100 - m.shape[1] / 2, y0 + 262, CREAM)


def build(n=12):
    img = SHEET.copy()
    main_title(img)
    rec = []
    for i, cell in enumerate(REEL[:n]):
        x0, y0 = XS[i % 3], YS[i // 3]
        if cell[0] == "pic":
            lay_picture(img, cell[1], x0, y0)
            rec.append(dict(cell=i + 1, kind="picture", shot=cell[1], event=cell[2]))
        else:
            lay_card(img, cell[1], cell[2], x0, y0, CW, CH, 9510 + 7 * i)
            rec.append(dict(cell=i + 1, kind="title card", text=" ".join(l for l in cell[1] if l), role=cell[3]))
    return img, rec


def _fol(p):
    p = np.clip(np.round(p), 0, 255).astype(np.uint8)
    pen99.folio(p, N, TITLE)
    return p


def beats():
    return [cv2.resize(_fol(build(n)[0]), (960, 1242), interpolation=cv2.INTER_AREA) for n in (1, 2, 4, 6, 8, 10, 12)]


if __name__ == "__main__":
    page, rec = build()
    img, size = save_page(page, N, PID, TITLE)
    print("jpeg bytes", size)
    import json
    json.dump(rec, open("/tmp/claude-0/-home-user/a99ec93a-6f31-57b0-a2ec-fb930dfe1aad/scratchpad/p95_rec.json", "w"), indent=1)
    if len(sys.argv) > 1 and sys.argv[1] == "beats":
        print("beats", save_beats(N, beats()))

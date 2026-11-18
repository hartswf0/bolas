"""Page 08 Lipogram (formal / Oulipian rule; medium: stencil-dye).

No letter e anywhere on the page. Six panels printed as HANDMADE stencils in flat dyes (indigo, madder,
ochre, verdigris, umber), each colour its own cut stencil with paper ties (bridges) and its own slight
misregistration, the dye pooling at the stencil edges. Figures and set pieces come from the b1m2 cut
model; the key is the ANRC 1922 cutout used as a stencil. Captions and the four rewritten lines are in
the shared pen hand. Substitutions: SERVICE -> SRVC (card and tag), TICKET OFFICE -> RANDOLPH STATION,
'key' in the memo -> a drawn key.
"""
import math
import random
import re
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
from b1m2 import *  # noqa

N, PID, TITLE = 8, "without-e", "Lipogram"
SHEET = pen99.sheet99()
INDIGO = np.array([44, 62, 112], np.float32)
MADDER = np.array([170, 66, 46], np.float32)
OCHRE = np.array([206, 152, 52], np.float32)
VERDI = np.array([84, 124, 102], np.float32)
UMBER = np.array([46, 36, 32], np.float32)
WASH = np.array([226, 206, 160], np.float32)
SKIN = np.array([232, 190, 150], np.float32)

GW, GH = 970, 846
COLS = (110, 1120)
ROWS = (110, 997, 1884)
BOXES = {f"P{r * 2 + c + 1}": (COLS[c], ROWS[r], COLS[c] + GW, ROWS[r] + GH) for r in range(3) for c in range(2)}

TEXT = {
    "cap1": "Randolph, 1937. A railway man at his post finds a slip: unlock SRVC door at 4:15. Up, and off to his cupboard.",
    "cap2": "Halfway, a woman at his window calls out:",
    "cap3": "Our man looks up at a wall clock:",
    "cap4": "His visitor nods and walks off.",
    "cap5": "At his cupboard. Door flung back: a brass thing hangs on its hook, with a tag: SRVC.",
    "cap6": "Brass stays on its hook. SRVC door stays shut.",
    "q": ["Pardon! Do you know", "what o'clock it is?"],
    "a": ["It's 4:10, by", "that clock."],
    "t": ["Thank you", "kindly!"],
    "f": ["So, I'm at my cupboard...", "and what for?"],
    "memo": ["4:15: unlock SRVC door.", "        in cupboard."],
    "window": "RANDOLPH STATION",
    "card": "SRVC",
    "title": TITLE,
}


def all_text():
    out = []
    for v in TEXT.values():
        out += v if isinstance(v, list) else [v]
    return out


def check_no_e():
    bad = [t for t in all_text() if re.search("[eE]", t)]
    assert not bad, bad
    return True


# ------------------------------------------------------------------ the stencil print
def noise(h, w, seed, scale=40):
    rng = np.random.default_rng(seed)
    n = rng.random((h // scale + 3, w // scale + 3)).astype(np.float32)
    n = cv2.resize(n, (w + 3 * scale, h + 3 * scale), interpolation=cv2.INTER_CUBIC)[:h, :w]
    f = rng.random((h, w)).astype(np.float32)
    f = cv2.GaussianBlur(f, (0, 0), 1.2)
    return n * 0.7 + f * 0.3


def ties(mask, seed, every=260, width=5):
    """Cut the paper ties a stencil needs: thin unprinted bridges across larger openings."""
    rng = random.Random(seed)
    h, w = mask.shape
    n, lab, stats, _ = cv2.connectedComponentsWithStats((mask > 127).astype(np.uint8))
    out = mask.copy()
    for i in range(1, n):
        x, y, bw, bh, area = stats[i]
        if area < 9000:
            continue
        k = max(1, int(max(bw, bh) / every))
        for j in range(k):
            if bh >= bw:
                yy = int(y + bh * (j + 1) / (k + 1) + rng.uniform(-20, 20))
                a = rng.uniform(-0.25, 0.25)
                p0, p1 = (x - 5, yy - a * bw / 2), (x + bw + 5, yy + a * bw / 2)
            else:
                xx = int(x + bw * (j + 1) / (k + 1) + rng.uniform(-20, 20))
                a = rng.uniform(-0.25, 0.25)
                p0, p1 = (xx - a * bh / 2, y - 5), (xx + a * bh / 2, y + bh + 5)
            band = np.zeros_like(mask)
            cv2.line(band, (int(p0[0]), int(p0[1])), (int(p1[0]), int(p1[1])), 255, width, cv2.LINE_AA)
            band = np.where(lab == i, band, 0).astype(np.uint8)
            out = np.where(band > 0, np.minimum(out, 255 - band), out)
    return out


def dye(canvas, mask, color, seed, shift=(0, 0), strength=0.92, bridge=True):
    """Print one stencil: ties, misregistration, mottle, edge pooling; multiplied onto the paper."""
    m = ties(mask, seed) if bridge else mask
    if shift != (0, 0):
        M = np.float32([[1, 0, shift[0]], [0, 1, shift[1]]])
        m = cv2.warpAffine(m, M, (m.shape[1], m.shape[0]))
    a = m.astype(np.float32) / 255
    a = cv2.GaussianBlur(a, (0, 0), 0.8)
    edge = np.clip(a - cv2.GaussianBlur(a, (0, 0), 6), 0, 1)
    mot = noise(*m.shape, seed=seed)
    dens = np.clip(strength * (0.80 + 0.28 * mot) + 0.5 * edge, 0, 1.15)
    tint = color / 255.0
    f = 1 - (1 - tint)[None, None, :] * (a * dens)[..., None]
    canvas *= np.clip(f, 0, 1)
    return canvas


def M(shapes, w, h, roles=None, holes=True):
    return raster(shapes, w, h, roles=roles, holes=holes, facet=0.8)


SHIFT = {"wash": (0, 0), "indigo": (3, -2), "madder": (-3, 2), "ochre": (2, 3), "verdi": (-2, -3), "umber": (1, 1), "skin": (-1, 2)}


STAGE = {"dyes": None, "text": True}
ORDER = ["wash", "ochre", "verdi", "indigo", "madder", "skin", "umber"]


def print_panel(w, h, layers, seed):
    """layers: list of (name, mask). Returns float RGB panel on the 1934 sheet."""
    c = np.ones((h, w, 3), np.float32) * 255
    col = {"wash": WASH, "indigo": INDIGO, "madder": MADDER, "ochre": OCHRE, "verdi": VERDI, "umber": UMBER, "skin": SKIN}
    for i, (name, mask) in enumerate(layers):
        if STAGE["dyes"] is not None and name not in STAGE["dyes"]:
            continue
        dye(c, mask, col[name], seed + 17 * i, shift=SHIFT[name], strength=0.55 if name == "wash" else 0.92,
            bridge=name not in ("wash", "skin"))
    return c


def fig_layers(shapes, w, h):
    """Split the cut model into dye stencils by role."""
    HOLES = {"slit", "dial", "pendwin", "inside", "glass", "pin"}
    R_ = lambda roles: M(shapes, w, h, roles=roles | HOLES)
    return {
        "indigo": R_({"waistcoat", "hat", "window"}),
        "madder": R_({"coat", "bow", "tie", "clock"}),
        "umber": R_({"trousers", "hair", "pencil", "hand", "eye", "glass_arm", "garter", "button"}),
        "skin": R_({"skin", "skin_s", "ear", "skin_far", "glove"}),
        "ochre": R_({"cupboard", "door", "shelf", "desk", "lamp"}),
        "verdi": R_({"sdoor"}),
    }


def merge(dst, src):
    for k, v in src.items():
        dst[k] = np.maximum(dst.get(k, np.zeros_like(v)), v)
    return dst


def wall(w, h, floor):
    m = np.zeros((h, w), np.uint8)
    m[:floor] = 255
    f = np.zeros((h, w), np.uint8)
    f[floor:] = 255
    return m, f


def caption(c, text, seed, cap=38, width=None):
    if not STAGE["text"]:
        return 0
    width = width or (c.shape[1] - 70)
    lines = wrap(text, cap, width)
    m = np.zeros(c.shape[:2], np.uint8)
    blit_mask(m, letter_left(lines, cap, seed), 22, 18)
    comp(c, m, INK)
    return int(18 + len(lines) * cap * 1.42 + 10)


def bal(c, lines, at, tip, seed, cap=46):
    if not STAGE["text"]:
        return 0
    b = penlib.balloon_piece([pen99.clean(l) for l in lines], cap, (tip[0] - at[0], tip[1] - at[1]), seed, tail_w=0.26)
    penlib.lay_balloon(c, b, at)


def layers_for(fig, w, h, extra=None, wall_floor=None, holes_from=None):
    L = fig_layers(fig, w, h)
    if extra:
        merge(L, extra)
    out = []
    if wall_floor is not None:
        wm, fm = wall(w, h, wall_floor)
        out.append(("wash", wm))
        L["umber"] = np.maximum(L["umber"], (fm * 0.0).astype(np.uint8))
        L.setdefault("verdi", np.zeros((h, w), np.uint8))
        L["verdi"] = np.maximum(L["verdi"], fm)
    for k in ("ochre", "verdi", "indigo", "madder", "skin", "umber"):
        if k in L:
            out.append((k, L[k]))
    return out


def key_stencil(w, h, x, y, scale, deg=0):
    m = np.zeros((h, w), np.uint8)
    paste_mask(m, key_alpha(), x, y, scale, deg)
    return m


# ------------------------------------------------------------------ panels
def P1(st):
    w, h = GW, GH
    floor = 760
    fig = agent(420, floor + 6, face=1, scale=0.62, legs=(10, -8), sh=10, el=40, pencil_deg=200, lean=2)
    fig += desk(520, 560, 330, floor)
    lay = layers_for(fig, w, h, wall_floor=floor)
    c = print_panel(w, h, lay, 801)
    c *= SHEET[:h, :w].mean(axis=2, keepdims=True) / SHEET.mean()
    top = caption(c, TEXT["cap1"], 811)
    # the memo slip on the desk: 'key' drawn, not written
    if not STAGE["text"]:
        return c
    box = slip(c, 560, 440, TEXT["memo"], 30, 812, paper=np.array([248, 244, 230], np.float32), tilt=-3, shadow=0.35)
    km = key_stencil(w, h, 622, 522, 0.115, deg=90)
    dye(c, km, UMBER, 813, bridge=False)
    return c


def window_panel(seed, stranger_kw, agent_kw, cap_key):
    w, h = GW, GH
    floor = 760
    ws, sill = window(70, 230, 330, 600, sill=560, header=70)
    for s in ws:
        s.role = "window"
    fig = list(ws)
    fig += stranger(235 + stranger_kw.pop("dx", 0), sill + 4, scale=1.15, **stranger_kw)
    fig += agent(**agent_kw)
    lay = layers_for(fig, w, h, wall_floor=floor)
    # the panes: the platform beyond, a pale madder wash under the stranger
    pane = np.zeros((h, w), np.uint8)
    pane[300:560, 70:400] = 255
    lay.insert(1, ("ochre", (pane * 0.0).astype(np.uint8)))
    c = print_panel(w, h, lay, seed)
    c *= SHEET[:h, :w].mean(axis=2, keepdims=True) / SHEET.mean()
    lm = np.zeros((h, w), np.uint8)
    if not STAGE["text"]:
        return c
    l = letter([TEXT["window"]], 30, seed + 5, weight=0.17)
    s_ = min(1.0, 330 / l.shape[1])
    l = cv2.resize(l, (int(l.shape[1] * s_), int(l.shape[0] * s_)), interpolation=cv2.INTER_AREA)
    put_mask(lm, l, 235, 230 + 37)
    comp(c, lm, np.array([246, 240, 222], np.float32))
    caption(c, TEXT[cap_key], seed + 7)
    return c


def P2(st):
    c = window_panel(820, {"glove": True}, dict(x=720, floor=GH + 30, face=-1, scale=0.62, sh=8, el=20, tilt=-3, pencil_deg=190), "cap2")
    bal(c, TEXT["q"], (700, 180), (340, 370), 821, cap=42)
    return c


def P3(st):
    w, h = GW, GH
    floor = 760
    fig = clock(300, 360, 110, swing=8) + agent(640, floor + 6, face=-1, scale=0.64, legs=(3, -3), tilt=-22, sh=6, el=20, pencil_deg=190)
    lay = layers_for(fig, w, h, wall_floor=floor)
    c = print_panel(w, h, lay, 830)
    c *= SHEET[:h, :w].mean(axis=2, keepdims=True) / SHEET.mean()
    caption(c, TEXT["cap3"], 831)
    bal(c, TEXT["a"], (330, 690), (600, 610), 832)
    return c


def P4(st):
    c = window_panel(840, {"dx": -40, "face": -1, "tilt": -4}, dict(x=720, floor=GH + 30, face=-1, scale=0.62, sh=4, el=10, tilt=2, pencil_deg=190), "cap4")
    bal(c, TEXT["t"], (560, 190), (300, 360), 841)
    return c


def cupboard_panel(seed, agent_kw, cap_key, sdoor):
    w, h = GW, GH
    floor = 760
    c0, c1, cw, ch = 300, 320, 300, 420
    cup, ins = cupboard(c0, c1, cw, ch, open_deg=112)
    fig = list(cup)
    if sdoor:
        fig += service_door(700, 300, 210, 460)
    fig += agent(**agent_kw)
    lay = layers_for(fig, w, h, wall_floor=floor)
    ix0, iy0, ix1, iy1 = ins
    kx, ky = (ix0 + ix1) / 2, iy0 + 120
    lay.append(("ochre", key_stencil(w, h, kx, ky, 0.27)))
    c = print_panel(w, h, lay, seed)
    c *= SHEET[:h, :w].mean(axis=2, keepdims=True) / SHEET.mean()
    if not STAGE["text"]:
        return c
    hk = np.zeros((h, w), np.uint8)
    penlib.brush_line(hk, [(kx - 22, ky - 104), (kx + 3, ky - 104), (kx + 3, ky - 88)], 7, seed + 3)
    comp(c, hk, UMBER)
    slip(c, int(kx + 8), int(ky + 34), [TEXT["card"]], 26, seed + 4, paper=np.array([248, 244, 230], np.float32), pad=(12, 4), tilt=8, shadow=0.3)
    if sdoor:
        slip(c, 760, 352, [TEXT["card"]], 34, seed + 5, paper=np.array([248, 244, 230], np.float32), pad=(16, 6), shadow=0.3)
    caption(c, TEXT[cap_key], seed + 6, width=GW - 70)
    return c


def P5(st):
    return cupboard_panel(850, dict(x=170, floor=766, face=1, scale=0.60, legs=(14, -12), sh=60, el=20, pencil_deg=200), "cap5", sdoor=False)


def P6(st):
    c = cupboard_panel(860, dict(x=150, floor=766, face=1, scale=0.60, legs=(3, -3), sh=50, el=120, wr=8, pencil_deg=40, tilt=6), "cap6", sdoor=True)
    if st.get("line", True):
        bal(c, TEXT["f"], (560, 178), (215, 300), 861, cap=44)
    return c


PANELS = [("P1", P1), ("P2", P2), ("P3", P3), ("P4", P4), ("P5", P5), ("P6", P6)]


def build(state=None):
    state = state or {}
    check_no_e()
    page = SHEET.copy()
    for k, fn in PANELS:
        x0, y0, x1, y1 = BOXES[k]
        page[y0:y1, x0:x1] = fn(state.get(k, {}))
    frame_border(page, list(BOXES.values()), w=10, seed=8800)
    return page


if __name__ == "__main__":
    page = build()
    img, size = save_page(page, N, PID, TITLE)
    print("jpeg bytes", size)
    if len(sys.argv) > 1 and sys.argv[1] == "beats":
        frames = []
        for k, dyes in enumerate([ORDER[:1], ORDER[:2], ORDER[:3], ORDER[:4], ORDER[:6], ORDER[:7], ORDER[:7]]):
            STAGE["dyes"], STAGE["text"] = set(dyes), k == 6
            p = np.clip(np.round(build()), 0, 255).astype(np.uint8)
            pen99.folio(p, N, TITLE)
            frames.append(np.asarray(Image.fromarray(p).resize((960, 1242), Image.LANCZOS)))
        save_beats(N, frames)

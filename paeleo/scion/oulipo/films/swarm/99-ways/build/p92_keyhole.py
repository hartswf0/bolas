"""Page 92 Through the keyhole (point of view; medium: stencil-dye).

Seen from inside the SERVICE room, through the keyhole of its door. Every panel is the inside of that door, printed
from an umber stencil (its paper ties left showing as thin pale bridges), with an ochre escutcheon and a keyhole-shaped
opening; through the opening, in page 08's flat dyes (wash, verdigris, indigo, madder, ochre, skin, umber), the
office: desk, ticket window, clock. The agent comes nearer panel by panel, toward the cupboard beside this door,
until in the last he stands at the keyhole itself. The door never opens. The cupboard is beside the door and out of
view; only its swinging leaf, with the brass key hanging inside it, comes into the keyhole's edge at E4.
Method: build/p08_lipogram.py (dye, ties, print_panel, fig_layers); figures and furniture: build/b1m2.py; key: the
ANRC 1922 cutout as a stencil. Lettering in the shared pen hand. Run: python3 -I p92_keyhole.py [beats]
"""
import math
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import b1m2 as B  # noqa: E402
from b1m2 import agent, stranger, desk, window, clock, lamp, Shape, R_  # noqa: E402
import pen99  # noqa: E402
from pen99 import penlib  # noqa: E402
import p08_lipogram as S  # noqa: E402

N, PID, TITLE = 92, "keyhole", "Through the keyhole"
W, H = 2200, 2850
PW, PH = 960, 750
COLS = (110, 1130)
CAPB = 74
ROWS = [110 + CAPB + r * (PH + CAPB + 40) for r in range(3)]
BOXES = [(COLS[c], ROWS[r], COLS[c] + PW, ROWS[r] + PH) for r in range(3) for c in range(2)]
SHEET = pen99.sheet99()

CAPS = ["Behind the SERVICE door, at its keyhole: he reads his memo, gets up.",
        "A lady at the ticket window.",
        "He looks up at the clock.",
        "She thanks him and goes. He comes this way.",
        "The cupboard beside this door swings open.",
        "He stands right at the keyhole. The door stays shut."]


def keyhole(w, h, cx, cy, r, scale=1.0):
    """The keyhole opening: a round head and a flared slot (mask)."""
    m = np.zeros((h, w), np.uint8)
    cv2.circle(m, (int(cx), int(cy)), int(r * scale), 255, -1, cv2.LINE_AA)
    t, b = r * 0.62 * scale, r * 1.20 * scale
    pts = np.array([(cx - t, cy + r * 0.3 * scale), (cx + t, cy + r * 0.3 * scale), (cx + b, cy + r * 2.9 * scale),
                    (cx - b, cy + r * 2.9 * scale)], np.float32)
    cv2.fillPoly(m, [np.int32(pts * 4)], 255, cv2.LINE_AA, shift=2)
    return m


KH = dict(cx=PW / 2, cy=235, r=150)


def escutcheon(w, h):
    """The brass plate round the keyhole: a rounded shield (ochre), the keyhole reserved through it."""
    m = np.zeros((h, w), np.uint8)
    cx, cy, r = KH["cx"], KH["cy"], KH["r"]
    cv2.ellipse(m, (int(cx), int(cy + r * 1.1)), (int(r * 1.85), int(r * 2.65)), 0, 0, 360, 255, -1, cv2.LINE_AA)
    for dx, dy in ((-r * 1.35, -r * 0.6), (r * 1.35, -r * 0.6), (-r * 1.35, r * 2.9), (r * 1.35, r * 2.9)):
        pass
    return m


def screws(w, h):
    m = np.zeros((h, w), np.uint8)
    cx, cy, r = KH["cx"], KH["cy"], KH["r"]
    for dy in (-r * 1.15, r * 3.35):
        cv2.circle(m, (int(cx), int(cy + dy)), 14, 255, -1, cv2.LINE_AA)
    return m


def scene(i, w, h):
    """The office beyond the door, as dye layers (before masking by the keyhole). Returns (layers dict, notes)."""
    floor = 560
    L = {}
    wm = np.zeros((h, w), np.uint8)
    wm[:floor] = 255
    fm = np.zeros((h, w), np.uint8)
    fm[floor:] = 255
    shapes = []
    # the far wall: desk at left, ticket window right of centre, clock above
    shapes += desk(330, 440, 180, floor) + lamp(330, 330, 110)
    ws, sill = window(530, 230, 120, 330, sill=230 + 330 * 0.6, header=46)
    shapes += ws
    shapes += clock(470, 120, 40, hh=4, mm=10 if i >= 2 else 9, pend=True, swing=6 if i % 2 else -6)
    extra = {}
    if i in (1, 2, 3):      # the stranger behind the glass
        st = stranger(590 + (-16 if i == 3 else 0), sill + 18, face=-1 if i == 3 else -1, scale=0.55,
                      tilt=-8 if i == 3 else 0, glove=(i == 1))
        shapes = st + shapes
    fig = None
    if i == 0:
        fig = agent(470, floor + 4, face=1, scale=0.36, legs=(10, -8), sh=-6, el=30, lean=4, pencil_deg=200, far_arm=(16, 16))
    elif i == 1:
        fig = agent(480, floor + 6, face=1, scale=0.38, legs=(6, -6), sh=8, el=20, tilt=-2, pencil_deg=190)
    elif i == 2:
        fig = agent(430, floor + 10, face=-1, scale=0.40, legs=(4, -4), sh=6, el=16, tilt=-26, pencil_deg=190, lean=-3)
    elif i == 3:
        fig = agent(500, floor + 150, face=1, scale=0.62, legs=(22, -20), sh=-22, el=26, lean=4, pencil_deg=200, far_arm=(22, 20))
    elif i == 4:
        fig = agent(560, floor + 560, face=-1, scale=1.05, legs=(4, -4), sh=70, el=-10, wr=0, pencil_deg=200, tilt=2)
    elif i == 5:
        fig = agent(600, 1590, face=-1, scale=1.68, sh=40, el=128, wr=-14, pencil_deg=90, tilt=-4, lean=-2)
    if fig is not None:
        shapes = shapes + fig
    L = S.fig_layers(shapes, w, h)
    # the near figure covers what is behind it: knock the far things out of its silhouette
    if fig is not None and i >= 3:
        sil = B.raster([s for s in fig if not s.hole], w, h)
        far = S.fig_layers([s for s in shapes if s not in fig], w, h)
        near = S.fig_layers(fig, w, h)
        for k in L:
            L[k] = np.where(sil > 127, near.get(k, np.zeros_like(sil)), far.get(k, np.zeros_like(sil))).astype(np.uint8)
        wm = np.where(sil > 127, 0, wm).astype(np.uint8)
        fm = np.where(sil > 127, 0, fm).astype(np.uint8)
    # glass of the ticket window: a pale wash only
    L["wash"] = wm
    L["verdi"] = np.maximum(L.get("verdi", np.zeros_like(fm)), fm)
    key = None
    if i >= 4:   # the cupboard's leaf swings into view at the left edge, the brass key on its hook inside it
        leaf = np.zeros((h, w), np.uint8)
        x_in = 405 if i == 4 else 415
        cv2.fillPoly(leaf, [np.int32(np.array([(150, 40), (x_in, 90), (x_in, 700), (150, 740)]) * 4)], 255, cv2.LINE_AA, shift=2)
        for k in L:
            L[k] = np.where(leaf > 127, 0, L[k]).astype(np.uint8)
        L["madder"] = np.maximum(L["madder"], leaf)
        km = np.zeros((h, w), np.uint8)
        B.paste_mask(km, B.key_alpha(), x_in - 30, 300, 0.30)
        L["madder"] = np.where(km > 127, 0, L["madder"]).astype(np.uint8)  # the brass key: ochre on the madder leaf
        L["ochre"] = np.maximum(L["ochre"], km)
        key = km
    return L, dict(floor=floor, sill=sill, fig=fig, key=key)


def panel(i, words=True):
    w, h = PW, PH
    L, info = scene(i, w, h)
    kh = keyhole(w, h, KH["cx"], KH["cy"], KH["r"])
    for k in L:
        L[k] = (L[k].astype(np.float32) * (kh / 255.0)).astype(np.uint8)
    door = np.full((h, w), 255, np.uint8)
    esc = escutcheon(w, h)
    door = np.where(esc > 127, 0, door).astype(np.uint8)
    plate = np.where(kh > 127, 0, esc).astype(np.uint8)
    rim = np.where(kh > 127, 0, cv2.dilate(kh, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))).astype(np.uint8)
    plate = np.where(rim > 127, 0, plate).astype(np.uint8)
    door = np.maximum(door, rim)
    layers = [("wash", L["wash"]), ("ochre", np.maximum(L["ochre"], plate)), ("verdi", L["verdi"]),
              ("indigo", L["indigo"]), ("madder", L["madder"]), ("skin", L["skin"]), ("umber", np.maximum(L["umber"], door)),
              ("umber", screws(w, h))]
    c = np.ones((h, w, 3), np.float32) * 255
    col = {"wash": S.WASH, "indigo": S.INDIGO, "madder": S.MADDER, "ochre": S.OCHRE, "verdi": S.VERDI, "umber": S.UMBER,
           "skin": S.SKIN}
    for j, (name, mask) in enumerate(layers):
        S.dye(c, mask, col[name], 9200 + i * 31 + j * 7, shift=S.SHIFT[name], strength=0.55 if name == "wash" else 0.92,
              bridge=name not in ("wash", "skin"))
    # the light: the office is lit, the SERVICE room dark (a second umber pass, faint, over the door only)
    S.dye(c, door, S.UMBER, 9290 + i, strength=0.35, bridge=False)
    return c, info


def balloon(c, lines, at, tip, seed, cap=40):
    b = penlib.balloon_piece([pen99.clean(l) for l in lines], cap, (tip[0] - at[0], tip[1] - at[1]), seed, tail_w=0.22, bend=0.10)
    penlib.lay_balloon(c, b, at)


def memo_slip(c, seed):
    """The memo on the desk, half cut off by the keyhole's edge (declared)."""
    kh = keyhole(PW, PH, KH["cx"], KH["cy"], KH["r"])
    tmp = c.copy()
    B.slip(tmp, 352, 392, ["4:15 - open", "SERVICE door.", "Key in cupboard."], 16, seed,
           paper=np.array([246, 242, 228], np.float32), tilt=-3, shadow=0.3, pad=(12, 8))
    a = (kh.astype(np.float32) / 255)[..., None]
    c[:] = c * (1 - a) + tmp * a


TICKET = None


def ticket_letters(c, seed):
    kh = keyhole(PW, PH, KH["cx"], KH["cy"], KH["r"])
    m = pen99.letter(["TICKET", "OFFICE"], 14, seed, weight=0.17)
    lm = np.zeros((PH, PW), np.uint8)
    B.put_mask(lm, m, 590, 253)
    lm = (lm.astype(np.float32) * kh / 255).astype(np.uint8)
    B.comp(c, lm, np.array([236, 226, 196], np.float32))


LINES = {1: (["Pardon me — have", "you the right time?"], (250, 640), (560, 340)),
         2: (["Ten past four,", "by the clock."], (190, 110), (440, 300)),
         3: (["Much obliged!"], (790, 120), (560, 300)),
         5: (["Well, here I am...", "and what for?"], (220, 620), (420, 300))}


def build(upto=6, words=True):
    page = SHEET.copy()
    for i in range(upto):
        x0, y0, x1, y1 = BOXES[i]
        c, info = panel(i)
        if i < 4:
            ticket_letters(c, 9300 + i)
        if i == 0:
            memo_slip(c, 9310)
        c *= SHEET[y0:y1, x0:x1].mean(axis=2, keepdims=True) / SHEET.mean()
        if words and i in LINES:
            lines, at, tip = LINES[i]
            balloon(c, lines, at, tip, 9320 + i, cap=40 if i != 5 else 38)
        page[y0:y1, x0:x1] = c
    if words:
        m = np.zeros((H, W), np.uint8)
        for i in range(upto):
            x0, y0, x1, y1 = BOXES[i]
            lines = B.wrap(CAPS[i], 34, PW - 20)
            B.blit_mask(m, B.letter_left(lines, 34, 9400 + i), x0 + 4, y0 - CAPB + 10 - (len(lines) - 1) * 44 + 4)
        penlib.ink_onto(page, m)
    B.frame_border(page, BOXES[:upto], w=10, seed=9490)
    return page


def single(i, words=True):
    """One keyhole panel, scaled to a beat frame (960 x 1242): the film looks through the keyhole."""
    c, info = panel(i)
    if i < 4:
        ticket_letters(c, 9300 + i)
    if i == 0:
        memo_slip(c, 9310)
    if words and i in LINES:
        lines, at, tip = LINES[i]
        balloon(c, lines, at, tip, 9320 + i, cap=40 if i != 5 else 38)
    fr = SHEET[:1242, :960].copy()
    y = (1242 - PH) // 2
    fr[y:y + PH] = c
    m = np.zeros((1242, 960), np.uint8)
    B.blit_mask(m, B.letter_left(B.wrap(CAPS[i], 34, 900), 34, 9400 + i), 20, 120)
    penlib.ink_onto(fr, m)
    return fr


def main():
    page = build()
    img, size = B.save_page(page, N, PID, TITLE)
    print("jpeg", size)
    if "beats" in sys.argv:
        print("beats", B.save_beats(N, [single(i) for i in range(6)]))


if __name__ == "__main__":
    main()

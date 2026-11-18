"""Cercle vicieux — a four-page panel palindrome: nine unique panels, 17 occurrences,
hinge X opening page 3 after a page turn. The film is a guided reading."""
import math
from PIL import Image, ImageDraw
from kit import *
from kit_comics import *

SLUG = "cercle-vicieux"
PW, PH = 2400, 1350
CW, CH = 850, 590           # standard panel
XW, XH = 520, 1220          # hinge: tall column
G = 40
LS = 38                     # lettering size

FLOOR = 470


def bg(ink, w, h, door_x=None):
    station_bg(ink, w, h, FLOOR)
    if door_x is not None:
        door_s(ink, door_x, FLOOR, 130, 250)


# ---------------------------------------------------------- the nine panels
def pA(ink, w, h):
    bg(ink, w, h, door_x=720)
    person(ink, 190, 555, 1.25, "visitor", 1, mouth="o", brows="worried", eyes="wide",
           arms={"front": (25, 70), "back": (20, 60)},
           holding=lambda k, hf, hb: envelope_s(k, hf[0] + 4, hf[1] - 6, 74, 48))
    o = person(ink, 520, 555, 1.25, "porter", -1, mouth="shout", brows="angry", look=(-1, 0),
               arms={"front": (88, 92), "back": (-10, -5)})
    balloon(ink, 470, 105, "You! Stay right there.", LS, tail=(510, 210), maxw=440)


def pB(ink, w, h):
    bg(ink, w, h)
    bench_s(ink, 640, 560, 380, 1.2)
    person(ink, 330, 575, 1.45, "visitor", 1, mouth="wavy", brows="worried", look=(1, -0.2),
           arms={"front": (30, 100), "back": (25, 95)},
           holding=lambda k, hf, hb: envelope_s(k, (hf[0] + hb[0]) / 2 + 6, hf[1] - 10, 96, 62))
    balloon(ink, 560, 115, "I was only told to wait on the bench.", LS, tail=(400, 220), maxw=420)


def pC(ink, w, h):
    bg(ink, w, h, door_x=140)
    person(ink, 430, 585, 1.5, "porter", 1, mouth="flat", brows="angry", look=(1, 0),
           arms={"front": (60, 75), "back": (-8, -4)})
    balloon(ink, 640, 115, "Who sent you?", LS + 4, tail=(520, 215), maxw=320)


def pD(ink, w, h):
    # close-up, hands and envelope; the key half out of the paper (in or out?)
    ink.d.rectangle([0, 0, w, h], fill=WALL2)
    ink.hatch(0, 0, w, h, gap=16, angle=60, color=RULE, alpha=120)
    cx, cy = w / 2, h / 2 + 30
    # sleeves
    _ = None
    for sx, col, sgn in ((0, VCOAT, 1), (w, VCOAT, -1)):
        ink.poly([(sx, cy - 40), (cx - sgn * 210, cy - 30), (cx - sgn * 210, cy + 80), (sx, cy + 120)], fill=col, color=INK, width=4)
    for sgn in (1, -1):
        hx = cx - sgn * 225
        ink.ellipse(hx + sgn * 30, cy + 20, 46, 36, fill=SKIN, color=INK, width=4)
    # envelope (big, open flap)
    ex0, ey0, ex1, ey1 = cx - 190, cy - 80, cx + 190, cy + 120
    ink.rect(ex0, ey0, ex1, ey1, fill=PAGE, color=INK, width=4)
    ink.poly([(ex0, ey0), (ex1, ey0), (cx, ey0 - 120)], fill=WASH, color=INK, width=4)
    ink.line([(ex0, ey1), (cx, ey0 + 90), (ex1, ey1)], RULE, 3)
    ink.circle(cx, ey0 - 60, 16, fill=ACCENT, color=INK, width=2)
    ink.line([(cx - 10, ey0 - 64), (cx + 12, ey0 - 52)], PAGE, 3)  # broken seal
    # the key half in the envelope
    key_shape(ink, cx - 60, ey0 - 10, 4.2, angle=-1.25)
    ink.rect(ex0 + 2, ey0 + 2, ex1 - 2, ey0 + 4, fill=PAGE, color=PAGE, width=1, rough=False)
    for sgn in (1, -1):  # thumbs over the front
        ink.ellipse(cx - sgn * 165, cy + 10, 22, 14, fill=SKIN, color=INK, width=3)


def pE(ink, w, h):
    bg(ink, w, h, door_x=700)
    o = person(ink, 330, 590, 1.5, "porter", 1, mouth="frown", brows="worried", look=(0.6, -1),
               arms={"front": (150, 175), "back": (-6, -3)})
    hx, hy = o["hands"]["front"]
    key_shape(ink, hx + 6, hy - 14, 2.2, angle=-1.2)
    balloon(ink, 580, 100, "This opens the service door.", LS, tail=(430, 200), maxw=360)


def pF(ink, w, h):
    bg(ink, w, h)
    bench_s(ink, 480, 600, 620, 1.5)
    key_shape(ink, 400, 600 - 100, 2.2)
    person(ink, 760, 600, 1.4, "visitor", -1, mouth="frown", brows="flat", look=(-1, 0.6),
           arms={"front": (55, 40), "back": (-10, -6)})
    balloon(ink, 300, 115, "Then I don't want it.", LS, tail=(700, 250), maxw=360)


def pG(ink, w, h):
    bg(ink, w, h, door_x=650)
    person(ink, 300, 585, 1.5, "porter", 1, mouth="flat", brows="angry", look=(1, 0), back=False,
           arms={"front": (-10, -4), "back": (10, 6)})
    balloon(ink, 300, 100, "Nobody goes through that door.", LS, tail=(330, 205), maxw=430)


def pH(ink, w, h):
    bg(ink, w, h)
    bell_s(ink, 640, 90, 1.6)
    person(ink, 330, 600, 1.5, "visitor", 1, mouth="o", brows="worried", look=(0.7, -1), eyes="wide",
           arms={"front": (150, 160), "back": (10, 30)})
    balloon(ink, 300, 95, "Then who rang the bell?", LS, tail=(345, 215), maxw=360, kind="whisper")


def pX(ink, w, h):
    station_bg(ink, w, h, 1060, dado=760)
    cx = w / 2
    # cord from the bell down into the door frame
    bell_s(ink, cx - 34, 210, 2.2, ringing=True)
    ink.line([(cx + 40, 330), (cx + 40, 760), (cx + 40, 790)], (120, 90, 50), 4)
    door_s(ink, cx, 1060, 240, 380, u=1.5)
    ink.circle(cx + 40, 645, 8, fill=BRASS, color=INK, width=2)  # cord pulley at the frame
    # light and feet under the door
    ink.rect(cx - 120, 1052, cx + 120, 1060, fill=(250, 228, 150), color=None, width=0)
    for fx in (cx - 40, cx + 30):
        ink.ellipse(fx, 1056, 22, 5, fill=INK, color=INK, width=1)
    sfx(ink, cx, 90, "DRRRING!", 84, angle=-6)
    caption_box(ink, 30, 400, "The bell can only be rung from behind that door.", 34, maxw=400, anchor="lt")


PANELS = {k: make_panel(CW, CH, f, seed=i + 1) for i, (k, f) in
          enumerate([("A", pA), ("B", pB), ("C", pC), ("D", pD), ("E", pE), ("F", pF), ("G", pG), ("H", pH)])}
PANELS["X"] = make_panel(XW, XH, pX, seed=9)
SPEECH = {"A": ("porter", "You! Stay right there."), "B": ("visitor", "I was only told to wait on the bench."),
          "C": ("porter", "Who sent you?"), "D": (None, ""), "E": ("porter", "This opens the service door."),
          "F": ("visitor", "Then I don't want it."), "G": ("porter", "Nobody goes through that door."),
          "H": ("visitor", "Then who rang the bell?"), "X": (None, "")}

ORDER = list("ABCDEFGH") + ["X"] + list("HGFEDCBA")
# symmetry check on IDs and on art bytes
assert ORDER == ORDER[::-1] and len(ORDER) == 17 and len(set(ORDER)) == 9
IDS = {k: art_id(v) for k, v in PANELS.items()}

# ---------------------------------------------------------- the four pages
TOP = (PH - 2 * CH - G) / 2


def grid2x2(board, ids, x0):
    rects = []
    for k, pid in enumerate(ids):
        r, c = divmod(k, 2)
        rects.append(board.place(PANELS[pid], x0 + c * (CW + G), TOP + r * (CH + G)))
    return rects


def folio(board, n):
    ink = board.ink()
    ink.label((board.m + PW / 2, board.m + PH - 26), f"— {n} —", 22, MUTED, anchor="mm")


PAGES = []
# page 1: title column + A B / C D
b = Board(PW, PH)
grid_x = PW - 60 - 2 * CW - G
ink = b.ink()
tx = b.m + 60 + XW / 2
ink.text((tx, b.m + 300), "Cercle", "serif", 120, INK, anchor="mm")
ink.text((tx, b.m + 410), "vicieux", "serif", 120, INK, anchor="mm")
ink.label((tx, b.m + 520), "a palindrome in 17 panels", 34, MUTED, anchor="mm")
key_shape(ink, tx - 60, b.m + 700, 3.0)
ink.label((tx, b.m + 880), "read it forward.", 34, INK, anchor="mm")
ink.label((tx, b.m + 940), "it will read you back.", 34, INK, anchor="mm")
PAGES.append((b, grid2x2(b, "ABCD", grid_x), "ABCD"))
folio(b, 1)
# page 2: E F / G H, centred
b = Board(PW, PH)
PAGES.append((b, grid2x2(b, "EFGH", (PW - 2 * CW - G) / 2), "EFGH"))
folio(b, 2)
# page 3: hinge column X + H G / F E
b = Board(PW, PH)
rx = b.place(PANELS["X"], 60, (PH - XH) / 2)
PAGES.append((b, [rx] + grid2x2(b, "HGFE", 60 + XW + G), "XHGFE"))
folio(b, 3)
# page 4: D C / B A + colophon column
b = Board(PW, PH)
rects = grid2x2(b, "DCBA", 60)
ink = b.ink()
cx = b.m + 60 + 2 * CW + G + (PW - 60 - 2 * CW - G) / 2
ink.text((cx, b.m + 520), "fin", "serif", 110, INK, anchor="mm")
ink.label((cx, b.m + 620), "(or: début)", 24, MUTED, anchor="mm")
key_shape(ink, cx - 60, b.m + 760, 3.0, angle=math.pi)
PAGES.append((b, rects, "DCBA"))
folio(b, 4)

# verify every placed occurrence equals the canonical art bytes
flat = "".join(p[2] for p in PAGES)
assert flat == "".join(ORDER), flat
for b, rects, ids in PAGES:
    for r, pid in zip(rects, ids):
        crop = b.img.crop(tuple(int(v) for v in r))
        assert art_id(crop) == IDS[pid], pid

# ---------------------------------------------------------- reading script
SEG = []   # (t0, t1, kind, payload)
T = 0.0
EVENTS = []  # (t, panel_id) for sound
HOLD, MOVE = 2.0, 0.5
for pi, (b, rects, ids) in enumerate(PAGES):
    sh = Shots()
    full = fit_box(b.page(), pad=0.0)
    sh.add(full, 2.6 if pi == 0 else 0.9, 0)
    for r, pid in zip(rects, ids):
        if pid == "X":
            top = fit_box((r[0], r[1], r[2], r[1] + 560), pad=0.06)
            bot = fit_box((r[0], r[3] - 640, r[2], r[3]), pad=0.04)
            t_arr = sh.add(top, 1.6, MOVE)
            EVENTS.append((T + t_arr - 1.6, "X"))
            sh.add(bot, 2.6, 1.1)
            continue
        sh.add(fit_box(r, pad=0.03), HOLD, MOVE)
        EVENTS.append((T + sh.t - HOLD, pid))
    sh.add(full, 2.2 if pi < 3 else 3.2, 0.8)
    SEG.append((T, T + sh.t, "page", (b, sh)))
    T += sh.t
    if pi < 3:
        SEG.append((T, T + 1.0, "turn", (pi, pi + 1)))
        T += 1.0
SEG.append((T, T + 5.5, "ledger", None))
T += 5.5
DUR = T

film = Film(SLUG, seconds=round(DUR, 2), boil=0, wobble=0)
grayscale_frames(film)
film.poster_at = [s for s in SEG if s[2] == "page"][2][0] + 2.6


def page_view(pi, t):
    b, sh = PAGES[pi][0], [s for s in SEG if s[2] == "page"][pi][3][1]
    seg = [s for s in SEG if s[2] == "page"][pi]
    return view(b.img, sh.at(t - seg[0]))


def full_view(pi):
    b = PAGES[pi][0]
    return view(b.img, fit_box(b.page(), pad=0.0))


FULL = [full_view(i) for i in range(4)]

# ledger: thumbnails of the flattened path
THUMB = {k: v.resize((int(v.width * 0.104), int(v.height * 0.104)), Image.LANCZOS) for k, v in PANELS.items()}


def ledger(ink, t):
    ink.fill(NIGHT)
    ink.text((W / 2, 46), "flattened reading order", "serif", 34, PAGE, anchor="mm")
    sc = 0.104
    tw, th = int(CW * sc), int(CH * sc)
    x0, gap = 40, 10
    rows = (150, 330)
    for k, pid in enumerate("ABCDEFGH"):
        x = x0 + k * (tw + gap)
        for r, y in enumerate(rows):
            ink.paste(THUMB[pid], (x, y))
            n = k + 1 if r == 0 else 17 - k
            ink.label((x + tw / 2, y - 16), f"{n}", 13, RULE, anchor="mm")
            ink.label((x + tw / 2, y + th + 18), pid, 20, BRASS, anchor="mm")
    ax = x0 + 8 * (tw + gap) + 30
    xt = THUMB["X"]
    xy = (rows[0] + rows[1] + th) / 2 - xt.height / 2
    ink.paste(xt, (ax, xy))
    ink.d.rectangle([ax - 3, xy - 3, ax + xt.width + 3, xy + xt.height + 3], outline=ACCENT + (255,), width=3)
    ink.label((ax + xt.width / 2, xy - 16), "9", 13, RULE, anchor="mm")
    ink.label((ax + xt.width + 34, xy + xt.height / 2), "X", 24, ACCENT, anchor="mm")
    ink.line([(x0, rows[0] - 34), (ax - 12, rows[0] - 34), (ax + 20, xy - 26)], RULE, 2, rough=False)
    ink.line([(ax + 20, xy + xt.height + 26), (ax - 12, rows[1] + th + 44), (x0, rows[1] + th + 44)], RULE, 2, rough=False)
    ink.label((W / 2, 460), "A B C D E F G H  X  H G F E D C B A  ·  17 occurrences · 9 unique · single centre", 16, PAGE, anchor="mm")
    ink.label((W / 2, 490), "each pair is the same image bytes; the shout that accuses in panel 1 protects in panel 17", 15, RULE, anchor="mm")
    a = min(1, (t) / 0.6)
    if a < 1:
        ink.d.rectangle([0, 0, W, H], fill=NIGHT + (int(255 * (1 - a)),))


@film.picture
def frame(t, ink):
    for t0, t1, kind, pay in SEG:
        if t0 <= t < t1:
            break
    if kind == "page":
        b, sh = pay
        ink.paste(view(b.img, sh.at(t - t0)))
        if t0 == 0 and t < 0.6:
            ink.d.rectangle([0, 0, W, H], fill=NIGHT + (int(255 * (1 - t / 0.6)),))
    elif kind == "turn":
        a, bb = pay
        ink.paste(page_turn(FULL[a], FULL[bb], smooth((t - t0) / (t1 - t0))))
    else:
        ledger(ink, t - t0)


@film.sound
def sound(mix):
    mix.room(0, DUR, 0.025)
    for t0, t1, kind, pay in SEG:
        if kind == "turn":
            mix.whoosh(t0 + 0.1, 0.7, 0.16)
            mix.click(t0 + 0.75, 0.2, 0.2, 2500)
    for t, pid in EVENTS:
        who, line = SPEECH[pid]
        if who:
            # identical clip for both occurrences: the seed is the panel id
            voice(mix, t + 0.25, line, 108 if who == "porter" else 182, -0.3 if who == "porter" else 0.3, 0.09, seed=ord(pid))
        elif pid == "D":
            mix.click(t + 0.3, 0.12, 0, 6000, 0.12)  # paper
            mix.click(t + 0.55, 0.1, 0, 6000, 0.1)
        elif pid == "X":
            mix.ring(t + 0.2, 1.6, 0.16)
            mix.thud(t + 2.2, 50, 0.2)
    mix.bell(DUR - 5.5, 392, 4.0, 0.14)
    mix.reverb(0.18)


if __name__ == "__main__":
    print("art ids:", IDS)
    print("duration", DUR)
    film.render()

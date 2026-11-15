"""Quatre-vingt-quinze — a 3x3 crossed grid. Across (A..I) it is a lost-key story at the
station; down (A D G B E H C F I) it is about who set up the encounter. Same nine cells,
same final cell I; the centre E answers a note in one route and a bell in the other."""
import math
from PIL import Image, ImageDraw
from kit import *
from kit_comics import *

SLUG = "quatre-vingt-quinze"
PW, PH = 2400, 1350
LM, TM, G = 100, 80, 34
CW = int((PW - LM - 40 - 2 * G) / 3)
CH = int((PH - TM - 40 - 2 * G) / 3)
LS = 34
FL = 300  # floor line inside a cell


def bg(ink, w, h, dado=200):
    station_bg(ink, w, h, FL, dado=dado)


def cap(ink, text, x=14, y=14, maxw=430, anchor="lt"):
    caption_box(ink, x, y, text, 28, maxw=maxw, anchor=anchor)


def cA(ink, w, h):
    bg(ink, w, h)
    clock(ink, 610, 110, 46, 4 + 10 / 60)
    person(ink, 330, 420, 1.15, "visitor", 1, pose="walk", phase=0.2, mouth="flat", look=(1, 0),
           arms={"front": (40, 80), "back": (-20, -10)},
           holding=lambda k, hf, hb: envelope_s(k, hf[0] + 6, hf[1] - 4, 70, 46))
    cap(ink, "A sealed envelope. No stamp.", maxw=380)


def cB(ink, w, h):
    bg(ink, w, h)
    bell_s(ink, 300, 80, 2.0, ringing=True)
    ink.line([(368, 196), (368, 250), (w + 10, 250)], (120, 90, 50), 4)
    sfx(ink, 560, 120, "DING", 70, angle=-10)
    cap(ink, "The bell rang once.", maxw=300, y=h - 14, anchor="lb")


def cC(ink, w, h):
    bg(ink, w, h)
    person(ink, 360, 450, 1.25, "visitor", -1, mouth="frown", brows="worried", look=(-0.5, 1), eyes="wide", sweat=True,
           arms={"front": (-15, 30), "back": (-15, 30)})
    balloon(ink, 520, 80, "My key... I had it this morning.", LS, tail=(420, 140), maxw=380)


def cD(ink, w, h):
    ink.d.rectangle([0, 0, w, h], fill=WALL2)
    ink.hatch(0, 0, w, h, gap=16, angle=60, color=RULE, alpha=110)
    cx, cy = w / 2, h / 2 + 40
    for sx, sgn in ((0, 1), (w, -1)):
        ink.poly([(sx, cy - 20), (cx - sgn * 250, cy - 10), (cx - sgn * 250, cy + 70), (sx, cy + 100)], fill=VCOAT, color=INK, width=4)
        ink.ellipse(cx - sgn * 235, cy + 30, 38, 30, fill=SKIN, color=INK, width=3)
    ink.rect(cx - 200, cy - 50, cx + 200, cy + 110, fill=PAGE, color=INK, width=4)
    ink.poly([(cx - 200, cy - 50), (cx + 200, cy - 50), (cx, cy - 150)], fill=WASH, color=INK, width=4)
    # the note card, pulled half out
    ink.poly([(cx - 150, cy - 175), (cx + 120, cy - 190), (cx + 135, cy - 40), (cx - 140, cy - 30)], fill=(252, 250, 244), color=INK, width=3)
    ink.text((cx - 120, cy - 160), "You dropped this.", "serif", 44, (40, 50, 110))
    key_shape(ink, cx - 60, cy - 70, 2.6, angle=-0.05)


def cE(ink, w, h):
    bg(ink, w, h)
    o = person(ink, 300, 470, 1.3, "visitor", 1, mouth="flat", brows="angry", eyes="side", look=(1, 0),
               arms={"front": (60, 120), "back": (-6, -3)})
    hx, hy = o["hands"]["front"]
    key_shape(ink, hx + 2, hy - 14, 2.4, angle=-1.0)
    balloon(ink, 540, 75, "So someone was watching.", LS, tail=(390, 120), maxw=330, kind="whisper")


def cF(ink, w, h):
    bg(ink, w, h)
    bench_s(ink, 380, 380, 520, 1.3)
    key_shape(ink, 330, 380 - 88, 2.3)
    cap(ink, "It wasn't her key. She left it where it could be seen.", maxw=460)


def cG(ink, w, h):
    bg(ink, w, h, dado=180)
    vp = (w * 0.7, 160)
    for x in (-200, 200, 900, 1400):
        ink.line([(x, h), lerp2((x, h), vp, 0.7)], RULE, 2)
    person(ink, 470, 380, 0.95, "visitor", 1, back=True, pose="walk", phase=0.6, arms={"front": (-15, -5), "back": (15, 8)})
    cap(ink, "She did not look back.", maxw=320, y=h - 14, anchor="lb")


def cH(ink, w, h):
    bg(ink, w, h)
    ink.line([(-10, 60), (420, 60), (420, 92)], (120, 90, 50), 4)
    door_s(ink, 420, FL, 130, 210, u=1.0)
    ink.circle(420, 96, 7, fill=BRASS, color=INK, width=2)
    cap(ink, "The bell cord runs behind this door.", maxw=270, x=w - 14, anchor="rt", y=70)


def cI(ink, w, h):
    bg(ink, w, h)
    door_s(ink, 480, FL, 130, 210, u=1.0)
    ink.rect(420, FL - 6, 540, FL, fill=(250, 228, 150), color=None, width=0)
    for fx in (455, 505):
        ink.ellipse(fx, FL - 3, 13, 3.5, fill=INK, color=INK, width=1)
    bench_s(ink, 200, 400, 300, 1.1)
    key_shape(ink, 160, 400 - 75, 1.9)
    cap(ink, "The door stayed shut.", maxw=300, y=h - 14, x=w - 14, anchor="rb")


FUNCS = dict(A=cA, B=cB, C=cC, D=cD, E=cE, F=cF, G=cG, H=cH, I=cI)
RED = {WALL: SPOT_L, WALL2: SPOT_L, FLOOR: SPOT, ACCENT: SPOT}
CELLS = {k: make_panel(CW, CH, f, seed=i + 1, treat=RED if k in "BDFH" else {ACCENT: SPOT})
         for i, (k, f) in enumerate(FUNCS.items())}
IDS = {k: art_id(v) for k, v in CELLS.items()}
ACROSS = list("ABCDEFGHI")
DOWN = [ACROSS[r * 3 + c] for c in range(3) for r in range(3)]
assert "".join(DOWN) == "ADGBEHCFI" and sorted(DOWN) == ACROSS and ACROSS[-1] == DOWN[-1] == "I"

board = Board(PW, PH)
RECT = {}
for k, pid in enumerate(ACROSS):
    r, c = divmod(k, 3)
    RECT[pid] = board.place(CELLS[pid], LM + c * (CW + G), TM + r * (CH + G))
bi = board.ink()
for k, pid in enumerate(ACROSS):
    x0, y0, x1, y1 = RECT[pid]
    bi.d.text((x0 + 4, y0 - 6), pid, font=lfont(24, "Bold"), fill=MUTED, anchor="lb")
for r in range(3):
    y = board.m + TM + r * (CH + G) + CH / 2
    bi.d.text((board.m + LM / 2, y), f"{r + 1}", font=lfont(40, "Bold"), fill=SPOT, anchor="mm")
    bi.line([(board.m + 30, y + 36), (board.m + 70, y + 36)], SPOT, 4, rough=False)
    bi.d.polygon([(board.m + 72, y + 28), (board.m + 86, y + 36), (board.m + 72, y + 44)], fill=SPOT)
for c in range(3):
    x = board.m + LM + c * (CW + G) + CW / 2
    bi.d.text((x, board.m + 30), "|||"[: c + 1].replace("|", "I"), font=lfont(34, "Bold"), fill=INK, anchor="mm")
    bi.line([(x + 40, board.m + 14), (x + 40, board.m + 48)], INK, 4, rough=False)
    bi.d.polygon([(x + 32, board.m + 48), (x + 48, board.m + 48), (x + 40, board.m + 62)], fill=INK)
for r in range(4):
    for c in range(4):
        jx = board.m + LM + c * (CW + G) - G / 2
        jy = board.m + TM + r * (CH + G) - G / 2
        for k in range(4):
            a = k * math.pi / 4 + 0.2
            bi.line([(jx - 16 * math.cos(a), jy - 16 * math.sin(a)), (jx + 16 * math.cos(a), jy + 16 * math.sin(a))], SPOT, 4)
for pid in ACROSS:
    assert art_id(board.img.crop(tuple(int(v) for v in RECT[pid]))) == IDS[pid]

FULL = fit_box(board.page(), pad=0.0)


def centre(pid):
    x0, y0, x1, y1 = RECT[pid]
    return ((x0 + x1) / 2, (y0 + y1) / 2)


def scr(pt):
    x0, y0, x1, y1 = FULL
    return ((pt[0] - x0) / (x1 - x0) * W, (pt[1] - y0) / (y1 - y0) * H)


# ---------------------------------------------------------- reading
TITLE = 2.6
sh = Shots()
sh.add(FULL, 2.4, 0, tag=("intro", None))
sh.add(FULL, 1.9, 0, tag=("card", 0))
VISITS = []
for route, ids in enumerate((ACROSS, DOWN)):
    for n, pid in enumerate(ids):
        sh.add(fit_box(RECT[pid], pad=0.04), 1.95, 0.5, tag=("cell", (route, n)))
        sh.marks.insert(len(sh.marks) - 1, (sh.t - 2.45, ("cell", (route, n))))
        VISITS.append((sh.t - 1.95, route, n, pid))
    sh.add(FULL, 2.6, 0.8, tag=("path", route))
    if route == 0:
        sh.add(FULL, 1.9, 0, tag=("card", 1))
sh.add(FULL, 5.4, 0, tag=("both", None))
DUR = round(TITLE + sh.t, 2)
film = Film(SLUG, seconds=DUR, boil=0, wobble=0)
film.poster_at = TITLE + VISITS[4][0] + 1.0

ROUTES = [("ROUTE 1 · ACROSS", "rows, left to right: what happened at the station", SPOT),
          ("ROUTE 2 · DOWN", "columns, top to bottom: who set the encounter up", INK)]


def minimap(ink, route, n):
    s, x0, y0 = 22, W - 3 * 22 - 20, 16
    ink.d.rectangle([x0 - 8, y0 - 8, x0 + 3 * s + 8, y0 + 3 * s + 8], fill=NIGHT + (200,))
    ids = (ACROSS, DOWN)[route]
    col = ROUTES[route][2]
    pts = []
    for k, pid in enumerate(ACROSS):
        r, c = divmod(k, 3)
        cx, cy = x0 + c * s + s / 2, y0 + r * s + s / 2
        ink.d.rectangle([x0 + c * s + 2, y0 + r * s + 2, x0 + c * s + s - 2, y0 + r * s + s - 2], outline=RULE + (255,), width=1)
    for pid in ids[: n + 1]:
        k = ACROSS.index(pid)
        r, c = divmod(k, 3)
        pts.append((x0 + c * s + s / 2, y0 + r * s + s / 2))
    if len(pts) > 1:
        ink.line(pts, col, 3, rough=False)
    ink.circle(*pts[-1], 5, fill=col, color=col, width=1, rough=False)
    ink.label((x0 - 14, y0 + 1.5 * s), f"{n + 1}/9", 13, PAGE, anchor="rm")


def draw_path(ink, route, alpha=230, upto=9):
    ids = (ACROSS, DOWN)[route]
    off = (-14, -14) if route == 0 else (14, 14)
    pts = [(scr(centre(p))[0] + off[0], scr(centre(p))[1] + off[1]) for p in ids]
    path_overlay(ink, pts, ROUTES[route][2], 5, size=15, alpha=alpha, upto=upto)


@film.picture
def frame(t, ink):
    if t < TITLE:
        ink.card("Quatre-vingt-quinze", "one grid · two reading routes · the same nine cells")
        if t > TITLE - 0.4:
            ink.d.rectangle([0, 0, W, H], fill=PAPER + (int(255 * (t - TITLE + 0.4) / 0.4),))
        return
    tt = t - TITLE
    ink.paste(view(board.img, sh.at(tt)))
    kind, arg = sh.tag_at(tt) or ("intro", None)
    if kind == "card":
        a = min(1, (tt - [m for m, tg in sh.marks if tg == (kind, arg)][0]) / 0.3)
        ink.d.rectangle([0, H / 2 - 70, W, H / 2 + 70], fill=NIGHT + (int(215 * a),))
        title, sub, col = ROUTES[arg]
        ink.text((W / 2, H / 2 - 16), title, "serif", 50, PAGE, anchor="mm", alpha=int(255 * a))
        ink.line([(W / 2 - 150, H / 2 + 14), (W / 2 + 150, H / 2 + 14)], col, 4, rough=False, alpha=int(255 * a))
        ink.label((W / 2, H / 2 + 36), sub, 16, PAGE, anchor="mm", alpha=int(255 * a))
    elif kind == "cell":
        route, n = arg
        t0 = [m for m, tg in sh.marks if tg == (kind, arg)][0]
        if tt - t0 < 1.1:
            minimap(ink, route, n)
    elif kind == "path":
        t0 = [m for m, tg in sh.marks if tg == (kind, arg)][0]
        draw_path(ink, arg, upto=1 + int(clamp((tt - t0) / 1.6) * 8))
    elif kind == "both":
        t0 = [m for m, tg in sh.marks if tg == (kind, arg)][0]
        draw_path(ink, 0, 200)
        draw_path(ink, 1, 200)
        a = min(1, (tt - t0) / 0.5)
        ex, ey = scr(centre("E"))
        ink.circle(ex, ey, 70, color=PAGE, width=4, rough=False, alpha=int(255 * a))
        ink.caption("E follows the note across, the bell down · both routes end on I", a, y=H - 20, size=17, kind="sans")


@film.sound
def sound(mix):
    mix.room(0, DUR, 0.03)
    lines = {"C": ("My key... I had it this morning.", 182), "E": ("So someone was watching.", 170)}
    for t0, route, n, pid in VISITS:
        t = TITLE + t0
        mix.click(t - 0.2, 0.08, 0.3 if route else -0.3, 2500)
        if pid in lines:
            voice(mix, t + 0.3, lines[pid][0], lines[pid][1], 0.1, 0.08, seed=ord(pid))
        elif pid == "B":
            mix.bell(t + 0.2, 660, 2.0, 0.18)
        elif pid == "D":
            mix.click(t + 0.3, 0.12, 0, 7000, 0.15)
        elif pid in "AG":
            mix.steps(t + 0.1, t + 1.8, 0.42, 0.12, "stone")
        elif pid == "I":
            mix.thud(t + 0.4, 48, 0.12)
    for route in (0, 1):
        t0 = TITLE + [m for m, tg in sh.marks if tg == ("card", route)][0]
        mix.note(t0, 392 if route == 0 else 294, 1.2, 0.08, 0, "tri")
    mix.reverb(0.15)


if __name__ == "__main__":
    print("ids", IDS, "dur", DUR)
    film.render()

"""Boucle-là ! — one page, seven occurrences A B C H C B A. Two people dispute who
left a note; the hinge shows it was addressed to the accuser."""
import math
from PIL import Image, ImageDraw
from kit import *
from kit_comics import *

SLUG = "boucle-la"
PW, PH = 2400, 1350
G = 40
RH = (PH - 2 * 60 - 2 * G) / 3          # row height
CW = (PW - 2 * 50 - 2 * G) / 3          # small panel width
HW = PW - 2 * 50                        # hinge width
CW, RH, HW = int(CW), int(RH), int(HW)
LS = 38
FL = 330


def bg(ink, w, h):
    station_bg(ink, w, h, FL, dado=200)


def folded_note(k, x, y, s=1.0):
    k.poly([(x - 30 * s, y - 20 * s), (x + 30 * s, y - 24 * s), (x + 32 * s, y + 18 * s), (x - 28 * s, y + 22 * s)], fill=PAGE, color=INK, width=3)
    k.line([(x - 29 * s, y), (x + 31 * s, y - 3 * s)], RULE, 2)


def pA(ink, w, h):
    bg(ink, w, h)
    o = person(ink, 230, 560, 1.35, "porter", 1, mouth="shout", brows="angry", look=(1, 0),
               arms={"front": (120, 150), "back": (-6, -3)},
               holding=lambda k, hf, hb: None)
    hx, hy = o["hands"]["front"]
    folded_note(ink, hx + 10, hy - 30, 1.5)
    person(ink, 640, 560, 1.35, "visitor", -1, mouth="flat", brows="flat", look=(-1, 0))
    balloon(ink, 400, 72, "Who left this note on the bench?", LS, tail=(280, 165), maxw=520)


def pB(ink, w, h):
    bg(ink, w, h)
    person(ink, 380, 580, 1.45, "visitor", -1, mouth="smirk", brows="sly", look=(-1, 0), eyes="side",
           arms={"front": (40, 150), "back": (-40, -150)})
    balloon(ink, 520, 70, "Don't look at me.", LS + 2, tail=(420, 170), maxw=360)


def pC(ink, w, h):
    bg(ink, w, h)
    o = person(ink, 330, 590, 1.5, "porter", 1, mouth="frown", brows="angry", eyes="side", look=(1, 0),
               arms={"front": (85, 95), "back": (-6, -3)})
    point_hand(ink, o["hands"]["front"], 1, 1.5)
    balloon(ink, 470, 70, "Then why are you smiling?", LS, tail=(370, 170), maxw=440)


def pH(ink, w, h):
    bg(ink, w, h)
    bench_s(ink, 300, 420, 420, 1.2)
    person(ink, 380, 600, 1.45, "porter", 1, mouth="o", brows="worried", eyes="wide", look=(1, 0),
           arms={"front": (20, 10), "back": (-10, -5)})
    # the note, opened, held by the visitor toward the reader
    vx = 1720
    person(ink, vx, 600, 1.45, "visitor", -1, mouth="smile", brows="raised", look=(-1, 0),
           arms={"front": (110, 80), "back": (100, 120)})
    nx0, ny0, nx1, ny1 = 900, 40, 1500, 350
    ink.poly([(nx0, ny0 + 8), (nx1, ny0), (nx1 + 6, ny1), (nx0 + 4, ny1 + 6)], fill=PAGE, color=INK, width=4)
    ink.line([(nx0 + 2, (ny0 + ny1) / 2 + 4), (nx1 + 3, (ny0 + ny1) / 2)], RULE, 3)
    ink.text((nx0 + 40, ny0 + 30), "For the Porter —", "serif", 52, (40, 50, 110))
    ink.text((nx0 + 40, ny0 + 105), "the brass key is yours.", "serif", 44, (40, 50, 110))
    ink.text((nx0 + 40, ny0 + 165), "You know which door.", "serif", 44, (40, 50, 110))
    key_shape(ink, nx1 - 150, ny1 - 50, 2.3, angle=-0.2)
    ink.rect(nx1 - 175, ny1 - 70, nx1 - 135, ny1 - 40, fill=(240, 236, 200, 170), color=None, width=0)  # tape
    for sx in (nx0 - 10, nx1 + 10):
        pass
    balloon(ink, 1980, 80, "It says “for the Porter.”", LS, tail=(1770, 190), maxw=420)


PANELS = {"A": make_panel(CW, RH, pA, seed=1), "B": make_panel(CW, RH, pB, seed=2),
          "C": make_panel(CW, RH, pC, seed=3), "H": make_panel(HW, RH, pH, seed=4)}
IDS = {k: art_id(v) for k, v in PANELS.items()}
ORDER = list("ABCHCBA")
assert ORDER == ORDER[::-1] and ORDER.count("H") == 1
LINES = {"A": ("porter", "Who left this note on the bench?"), "B": ("visitor", "Don't look at me."),
         "C": ("porter", "Then why are you smiling?"), "H": ("visitor", "It says for the Porter.")}
ACTS = ["accuses", "denies", "presses", "reveals", "squirms", "gloats", "pleads"]

board = Board(PW, PH)
RECTS = []
for k, pid in enumerate(ORDER):
    if k < 3:
        RECTS.append(board.place(PANELS[pid], 50 + k * (CW + G), 60))
    elif k == 3:
        RECTS.append(board.place(PANELS[pid], 50, 60 + RH + G))
    else:
        RECTS.append(board.place(PANELS[pid], 50 + (k - 4) * (CW + G), 60 + 2 * (RH + G)))
bi = board.ink()
bi.label((board.m + PW / 2, board.m + 30), "BOUCLE-LÀ", 22, MUTED, anchor="mm")
for r, pid in zip(RECTS, ORDER):
    assert art_id(board.img.crop(tuple(int(v) for v in r))) == IDS[pid]

# ---------------------------------------------------------- reading
FULL = fit_box(board.page(), pad=0.0)
sh = Shots()
sh.add(FULL, 2.4, 0)
EV = []
for k, (r, pid) in enumerate(zip(RECTS, ORDER)):
    if pid == "H":
        x0, y0, x1, y1 = r
        sh.add(fit_box((x0, y0, x0 + 1150, y1), pad=0.03), 1.6, 0.6)
        EV.append((sh.t - 1.6, pid, k))
        sh.add(fit_box((x0 + 1100, y0, x1, y1), pad=0.03), 3.2, 1.2)
    else:
        sh.add(fit_box(r, pad=0.04), 2.5, 0.55)
        EV.append((sh.t - 2.5, pid, k))
sh.add(FULL, 4.0, 0.9)
T_ANN = sh.t
sh.add(FULL, 7.0, 0)
TITLE = 2.6
DUR = round(TITLE + sh.t, 2)

film = Film(SLUG, seconds=DUR, boil=0, wobble=0)
grayscale_frames(film)
film.poster_at = TITLE + EV[3][0] + 2.5


def to_screen(box, pt):
    x0, y0, x1, y1 = box
    return ((pt[0] - x0) / (x1 - x0) * W, (pt[1] - y0) / (y1 - y0) * H)


@film.picture
def frame(t, ink):
    if t < TITLE:
        ink.card("Boucle-là", "three panels · one hinge · the same three, backwards")
        if t > TITLE - 0.4:
            ink.d.rectangle([0, 0, W, H], fill=PAPER + (int(255 * (t - TITLE + 0.4) / 0.4),))
        return
    tt = t - TITLE
    box = sh.at(tt)
    ink.paste(view(board.img, box))
    if tt >= T_ANN:
        a = min(1, (tt - T_ANN) / 0.6)
        for k, r in enumerate(RECTS):
            if ORDER[k] == "H":
                x, y = to_screen(FULL, (r[0] + 20, r[3] - 20))
            else:
                x, y = to_screen(FULL, (r[0] + 14, r[3] - 14))
            s = f"{k + 1}·{ORDER[k]} {ACTS[k]}"
            tw, th = ink.text_size(s, "mono", 14)
            ink.d.rectangle([x, y - th - 10, x + tw + 12, y], fill=NIGHT + (int(220 * a),))
            ink.label((x + 6, y - th - 7), s, 14, PAGE if ORDER[k] != "H" else BRASS, alpha=int(255 * a))


@film.sound
def sound(mix):
    mix.room(0, DUR, 0.025)
    mix.bell(0.3, 523, 2.5, 0.10)
    for t, pid, k in EV:
        who, line = LINES[pid]
        t += TITLE
        if pid == "H":
            mix.click(t + 0.1, 0.2, 0.1, 7000, 0.2)    # paper unfolds
            mix.click(t + 0.35, 0.16, 0.1, 7000, 0.15)
            mix.bell(t + 0.6, 330, 3.5, 0.16)          # the single hinge cue
            voice(mix, t + 2.0, line, 182, 0.35, 0.09, seed=ord(pid))
        else:
            # repeated voice clips: the same seed for both occurrences of a panel
            voice(mix, t + 0.25, line, 108 if who == "porter" else 182, -0.35 if who == "porter" else 0.35, 0.09, seed=ord(pid))
    mix.reverb(0.15)


if __name__ == "__main__":
    print("art ids", IDS, "dur", DUR)
    film.render()

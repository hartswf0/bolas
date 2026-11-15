"""99 Ways to Tell a Story · Template — the neutral baseline, set in the station office.
The clerk leaves the desk, hears a question from the platform, answers, reaches the key
cupboard and forgets why. Then a compressed retelling and the porter's point of view."""
import math
from PIL import Image, ImageDraw
from kit import *
from kit_comics import *

SLUG = "99-ways-template"
PW, PH = 2400, 1350
CW, CH = 740, 590
G = 40
LS = 36
FLY = 500                    # office floor line
DESK = (190, 370)
CUP = (560, 715)

# ---------------------------------------------------------- canonical event ledger
EVENTS = [("E1", "leaves the desk (errand: the service key)"),
          ("E2", "a question from the platform: “what time is it?”"),
          ("E3", "answers: “ten past four!”"),
          ("E4", "reaches the key cupboard"),
          ("E5", "forgets why (the key stays on its hook)")]


def office(ink, w, h, cupboard_open=False, ox=0):
    ink.d.rectangle([0, 0, w, FLY], fill=(226, 214, 190))
    ink.d.rectangle([0, FLY - 120, w, FLY], fill=(206, 190, 162))
    ink.line([(0, FLY - 120), (w, FLY - 120)], INK, 3)
    ink.d.rectangle([0, FLY, w, h], fill=(170, 136, 100))
    for k in range(1, 5):
        yy = FLY + (h - FLY) * (k / 5) ** 1.2
        ink.line([(0, yy), (w, yy)], (140, 108, 78), 2)
    ink.line([(0, FLY), (w, FLY)], INK, 3)
    # doorway to the platform, far left
    ink.rect(-10 + ox, 170, 120 + ox, FLY, fill=(244, 236, 214), color=INK, width=4)
    ink.line([(-10 + ox, 430), (120 + ox, 430)], RULE, 2)
    ink.d.text((55 + ox, 200), "PLATFORM", font=lfont(15, "Bold"), fill=MUTED, anchor="mm")
    # clock above the desk
    clock(ink, 250 + ox, 110, 44, 4 + 10 / 60)
    # desk, lamp, ledger and the errand note
    x0, x1 = DESK[0] + ox, DESK[1] + ox
    ink.rect(x0, 380, x1, 396, fill=WOOD, color=INK, width=3)
    ink.rect(x0 + 8, 396, x0 + 60, FLY, fill=(130, 94, 60), color=INK, width=3)
    ink.line([(x1 - 14, 396), (x1 - 14, FLY)], INK, 5)
    ink.poly([(x0 + 70, 380), (x0 + 150, 374), (x0 + 152, 366), (x0 + 72, 372)], fill=PAGE, color=INK, width=2)
    ink.line([(x1 - 30, 380), (x1 - 30, 330), (x1 - 60, 316)], INK, 3)
    ink.poly([(x1 - 80, 302), (x1 - 46, 302), (x1 - 52, 324), (x1 - 74, 324)], fill=(120, 140, 90), color=INK, width=2)
    ink.rect(x0 + 10, 352, x0 + 56, 378, fill=CAPTION, color=INK, width=1.5)
    ink.d.text((x0 + 33, 365), "KEY!", font=lfont(13, "Bold"), fill=ACCENT, anchor="mm")
    # key cupboard
    c0, c1 = CUP[0] + ox, CUP[1] + ox
    ink.rect(c0, 170, c1, FLY, fill=(120, 88, 60), color=INK, width=4)
    if cupboard_open:
        ink.rect(c0 + 12, 182, c1 - 12, FLY - 12, fill=(70, 52, 40), color=INK, width=2)
        for r, row in enumerate((("S", BRASS), ("", (170, 170, 160)), ("", (170, 170, 160)))):
            pass
        for k in range(3):
            for j in range(3):
                hx, hy = c0 + 40 + j * 40, 230 + k * 70
                ink.circle(hx, hy, 3, fill=PAGE, color=INK, width=1, rough=False)
                col = BRASS if (k, j) == (0, 1) else (176, 176, 168)
                key_shape(ink, hx, hy + 12, 0.9, angle=math.pi / 2, color=col)
        # doors swung open
        ink.poly([(c0, 170), (c0 - 60, 190), (c0 - 60, FLY - 20), (c0, FLY)], fill=(134, 100, 70), color=INK, width=3)
        ink.poly([(c1, 170), (c1 + 40, 190), (c1 + 40, FLY - 20), (c1, FLY)], fill=(134, 100, 70), color=INK, width=3)
    else:
        ink.line([((c0 + c1) / 2, 170), ((c0 + c1) / 2, FLY)], INK, 3)
        for sx in (-12, 12):
            ink.circle((c0 + c1) / 2 + sx, 340, 5, fill=BRASS, color=INK, width=1.5)
    ink.rect(c0 + 34, 140, c1 - 34, 164, fill=PAGE, color=INK, width=2)
    ink.d.text(((c0 + c1) / 2, 152), "KEYS", font=lfont(14, "Bold"), fill=INK, anchor="mm")


def offstage(ink, text, cx=240, cy=95, size=LS):
    """A voice from the platform: the tail runs into the doorway."""
    return balloon(ink, cx, cy, text, size, tail=(70, 250), maxw=300)


# ---------------------------------------------------------- baseline panels (objective)
def b1(ink, w, h):
    office(ink, w, h)
    ink.rect(380, FLY - 96, 470, FLY - 84, fill=WOOD, color=INK, width=3)          # chair
    for lx in (388, 462):
        ink.line([(lx, FLY - 84), (lx, FLY)], INK, 4)
    ink.line([(466, FLY - 96), (472, FLY - 190)], INK, 5)
    person(ink, 430, FLY, 1.2, "clerk", -1, pose="sit", mouth="flat", brows="flat", look=(-0.6, 0.6),
           arms={"front": (75, 100), "back": (65, 95)})
    caption_box(ink, w - 14, 14, "Four o'clock. The service key is wanted.", 26, maxw=260, anchor="rt")


def b2(ink, w, h):
    office(ink, w, h)
    person(ink, 430, FLY + 30, 1.2, "clerk", 1, pose="walk", phase=0.15, mouth="flat", look=(1, 0))
    offstage(ink, "What time is it?")


def b3(ink, w, h):
    office(ink, w, h)
    person(ink, 440, FLY + 30, 1.2, "clerk", -1, mouth="open", brows="raised", look=(-1, -1))
    balloon(ink, 560, 90, "Ten past four!", LS, tail=(470, 190), maxw=260)


def b4(ink, w, h):
    office(ink, w, h, cupboard_open=True)
    person(ink, 500, FLY + 30, 1.2, "clerk", 1, mouth="flat", look=(1, 0), arms={"front": (80, 70)})


def b5(ink, w, h):
    office(ink, w, h, cupboard_open=True)
    person(ink, 470, FLY + 30, 1.2, "clerk", 1, mouth="flat", brows="worried", look=(1, -0.3), arms={"front": (10, 5)})
    balloon(ink, 410, 95, "Hm.", LS + 4, tail=(470, 190), maxw=200)


def b6(ink, w, h):
    office(ink, w, h, cupboard_open=True)
    person(ink, 470, FLY + 30, 1.2, "clerk", -1, mouth="wavy", brows="worried", look=(-1, -0.5),
           arms={"front": (160, 200), "back": (-8, -4)})
    balloon(ink, 300, 100, "...now what did I come over here for?", 32, tail=(450, 195), maxw=330, kind="thought")


BASE = [make_panel(CW, CH, f, seed=i + 1) for i, f in enumerate((b1, b2, b3, b4, b5, b6))]
BASE_EVENTS = [["E1"], ["E1", "E2"], ["E3"], ["E4"], ["E5"], ["E5"]]


# ---------------------------------------------------------- compressed retelling (2 panels)
def c1(ink, w, h):
    office(ink, w, h)
    person(ink, 430, FLY + 30, 1.2, "clerk", 1, pose="walk", phase=0.15, mouth="open", look=(-1, -0.5))
    offstage(ink, "What time is it?", 230, 80, 32)
    balloon(ink, 560, 210, "Ten past four!", 32, tail=(470, 260), maxw=240)


def c2(ink, w, h):
    office(ink, w, h, cupboard_open=True)
    person(ink, 470, FLY + 30, 1.2, "clerk", -1, mouth="wavy", brows="worried", look=(-1, -0.5),
           arms={"front": (160, 200), "back": (-8, -4)})
    balloon(ink, 300, 100, "...what was I getting?", 34, tail=(450, 195), maxw=300, kind="thought")


COMP = [make_panel(CW, CH, f, seed=20 + i) for i, f in enumerate((c1, c2))]
COMP_EVENTS = [["E1", "E2", "E3"], ["E4", "E5"]]


# ---------------------------------------------------------- the porter's point of view (3 panels)
def platform_side(ink, w, h, clerk_pose=None):
    station_bg(ink, w, h, FLY, dado=330)
    # the office hatch in the wall: a small window onto the room
    hx0, hy0, hx1, hy1 = 330, 150, 690, 370
    ink.rect(hx0 - 10, hy0 - 10, hx1 + 10, hy1 + 10, fill=(90, 74, 62), color=INK, width=3)
    ink.d.rectangle([hx0, hy0, hx1, hy1], fill=(214, 200, 176))
    ink.d.text(((hx0 + hx1) / 2, hy0 - 26), "OFFICE", font=lfont(16, "Bold"), fill=INK, anchor="mm")
    # inside: the cupboard, small, seen through the hatch
    ink.rect(hx0 + 220, hy0 + 30, hx0 + 300, hy1, fill=(120, 88, 60), color=INK, width=2)
    if clerk_pose == "cupboard":
        ink.rect(hx0 + 228, hy0 + 38, hx0 + 292, hy1, fill=(70, 52, 40), color=INK, width=1.5)
        key_shape(ink, hx0 + 260, hy0 + 70, 0.6, angle=math.pi / 2)
        person(ink, hx0 + 170, hy1 + 90, 0.62, "clerk", -1, mouth="wavy", brows="worried", look=(-1, -0.5),
               arms={"front": (160, 200), "back": (-8, -4)})
    elif clerk_pose == "walk":
        person(ink, hx0 + 120, hy1 + 90, 0.62, "clerk", 1, pose="walk", phase=0.15, mouth="open", look=(-1, 0))
    ink.d.rectangle([hx0 - 12, hy1 + 11, hx1 + 12, FLY - 2], fill=WALL2)      # wall hides the legs
    ink.rect(hx0, hy1 - 6, hx1, hy1 + 14, fill=WOOD, color=INK, width=3)  # counter ledge
    bench_s(ink, 170, FLY + 40, 260, 1.1)


def v1(ink, w, h):
    platform_side(ink, w, h, "walk")
    person(ink, 150, FLY + 40, 1.15, "porter", 1, pose="sit", mouth="open", look=(1, -0.6))
    balloon(ink, 180, 80, "What time is it?", LS, tail=(160, 215), maxw=260)


def v2(ink, w, h):
    platform_side(ink, w, h, None)
    o = person(ink, 150, FLY + 40, 1.15, "porter", 1, pose="sit", mouth="flat", look=(0.3, 1), arms={"front": (70, 140)})
    hx, hy = o["hands"]["front"]
    ink.circle(hx + 8, hy - 6, 13, fill=BRASS, color=INK, width=2.5)   # his own watch, unopened
    balloon(ink, 510, 70, "Ten past four!", LS, tail=(500, 160), maxw=260)


def v3(ink, w, h):
    platform_side(ink, w, h, "cupboard")
    person(ink, 150, FLY + 40, 1.15, "porter", 1, pose="sit", mouth="smirk", brows="raised", look=(1, -0.4),
           arms={"front": (40, 90)})
    balloon(ink, 510, 70, "...?", LS, tail=(500, 180), maxw=160, kind="thought")
    caption_box(ink, 14, 14, "From the bench he never saw why the clerk got up.", 24, maxw=260)


POV = [make_panel(CW, CH, f, seed=30 + i) for i, f in enumerate((v1, v2, v3))]
POV_EVENTS = [["E2"], ["E3"], ["E4", "E5"]]


# ---------------------------------------------------------- pages
def page(panels, cols, title, sub):
    rows = (len(panels) + cols - 1) // cols
    ph = 150 + rows * CH + (rows - 1) * G + 60
    b = Board(PW, max(ph, 760))
    gx = (PW - cols * CW - (cols - 1) * G) / 2
    ink = b.ink()
    ink.text((b.m + gx, b.m + 70), title, "serif", 60, INK, anchor="ls")
    ink.label((b.m + gx, b.m + 112), sub, 24, MUTED)
    rects = []
    for k, im in enumerate(panels):
        r, c = divmod(k, cols)
        rects.append(b.place(im, gx + c * (CW + G), 150 + r * (CH + G)))
    return b, rects


PAGES = [page(BASE, 3, "Template", "the baseline · six panels · one fixed, objective view"),
         page(COMP, 2, "Compressed", "the same five events in two panels"),
         page(POV, 3, "From the bench", "the porter's point of view: E1 is out of his reach")]
PAGE_EVENTS = [BASE_EVENTS, COMP_EVENTS, POV_EVENTS]
for evs in PAGE_EVENTS:
    assert {e for p in evs for e in p} <= {e for e, _ in EVENTS}
assert sorted({e for p in BASE_EVENTS for e in p}) == [e for e, _ in EVENTS]
assert sorted({e for p in COMP_EVENTS for e in p}) == [e for e, _ in EVENTS]


def baseline_board():
    """Used by 99-ways-subjective for the side-by-side comparison."""
    return PAGES[0][0]


# ---------------------------------------------------------- reading script
if __name__ == "__main__" or True:
    TITLE = 2.6
    SEG = []
    T = TITLE
    SPEAK = []
    for pi, (b, rects) in enumerate(PAGES):
        if pi > 0:
            SEG.append((T, T + 1.6, "card", pi))
            T += 1.6
        sh = Shots()
        full = fit_box(b.page(), pad=0.0)
        sh.add(full, 2.0 if pi == 0 else 1.2, 0)
        for k, r in enumerate(rects):
            hold = 2.5 if pi == 0 else 2.6
            sh.add(fit_box(r, pad=0.03), hold, 0.5)
            SPEAK.append((T + sh.t - hold, pi, k))
        sh.add(full, 4.0 if pi == 0 else 2.6, 0.8)
        SEG.append((T, T + sh.t, "page", (b, sh)))
        T += sh.t
    SEG.append((T, T + 6.5, "ledger", None))
    DUR = round(T + 6.5, 2)

CARDS = {1: ("Retelling 1 · compressed", "fewer panels, same incident"),
         2: ("Retelling 2 · another point of view", "the porter, from the platform bench")}

film = Film(SLUG, seconds=DUR, boil=0, wobble=0)
grayscale_frames(film)
film.poster_at = TITLE + 2.0 + 3 * 3.0 + 1.0


def ledger(ink, lt):
    ink.fill(NIGHT)
    ink.text((W / 2, 50), "event ledger", "serif", 36, PAGE, anchor="mm")
    cols = [("baseline", BASE_EVENTS), ("compressed", COMP_EVENTS), ("porter", POV_EVENTS)]
    x0, y0 = 60, 120
    for j, (name, _) in enumerate(cols):
        ink.label((560 + j * 130, y0 - 24), name, 15, BRASS, anchor="mm")
    for i, (eid, desc) in enumerate(EVENTS):
        y = y0 + 18 + i * 62
        ink.label((x0, y), eid, 18, ACCENT)
        ink.text((x0 + 48, y - 3), desc, "sans", 19, PAGE)
        for j, (name, evs) in enumerate(cols):
            ps = [str(k + 1) for k, p in enumerate(evs) if eid in p]
            s = "p" + ",".join(ps) if ps else "—"
            ink.label((560 + j * 130, y + 8), s, 17, PAGE if ps else MUTED, anchor="mm")
    ink.label((W / 2, H - 46), "outcome fixed in every version: the brass key stays on its hook", 15, RULE, anchor="mm")
    a = min(1, lt / 0.5)
    if a < 1:
        ink.d.rectangle([0, 0, W, H], fill=NIGHT + (int(255 * (1 - a)),))


@film.picture
def frame(t, ink):
    if t < TITLE:
        ink.card("99 Ways · Template", "a neutral baseline for the station office")
        if t > TITLE - 0.4:
            ink.d.rectangle([0, 0, W, H], fill=PAPER + (int(255 * (t - TITLE + 0.4) / 0.4),))
        return
    for t0, t1, kind, pay in SEG:
        if t0 <= t < t1:
            break
    if kind == "page":
        b, sh = pay
        ink.paste(view(b.img, sh.at(t - t0)))
    elif kind == "card":
        title, sub = CARDS[pay]
        ink.card(title, sub)
    else:
        ledger(ink, t - t0)


@film.sound
def sound(mix):
    mix.room(0, DUR, 0.03)
    # a station clock ticking in the office
    k = 0
    while k * 1.0 < DUR - 7:
        mix.click(TITLE + k, 0.035, -0.5, 3000, 0.02)
        k += 1
    lines = {(0, 1): ("What time is it?", 108, -0.8), (0, 2): ("Ten past four!", 150, 0.1),
             (0, 4): ("Hm.", 150, 0.1), (1, 0): ("What time is it? Ten past four!", 130, -0.3),
             (2, 0): ("What time is it?", 108, -0.3), (2, 1): ("Ten past four!", 150, 0.6)}
    for t, pi, k in SPEAK:
        if (pi, k) in lines:
            s, p, pan = lines[(pi, k)]
            voice(mix, t + 0.3, s, p, pan, 0.08)
        if (pi, k) in ((0, 1), (1, 0)):
            mix.steps(t + 0.2, t + 1.8, 0.45, 0.14, "wood")
        if (pi, k) in ((0, 3), (1, 1)):
            mix.click(t + 0.3, 0.2, 0.4, 1500, 0.25)  # cupboard door creak
    for t0, t1, kind, pay in SEG:
        if kind == "card":
            mix.note(t0 + 0.1, 392, 1.0, 0.07, 0, "tri")
    mix.reverb(0.15)


if __name__ == "__main__":
    print("dur", DUR)
    film.render()

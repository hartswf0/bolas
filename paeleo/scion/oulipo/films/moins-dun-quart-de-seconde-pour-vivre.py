"""Moins d'un quart de seconde pour vivre — iconic iteration: one plate (a visitor on a
bench with an unopened envelope) repeated eight times; only the balloon plane changes.
Strip 1: she talks herself into waiting. Strip 2: the same pose becomes an alibi."""
import math
from PIL import Image, ImageDraw
from kit import *
from kit_comics import *

SLUG = "moins-dun-quart-de-seconde-pour-vivre"
PW, PH = 2400, 1350
G = 40
PWID = (PW - 2 * 50 - 3 * G) // 4
PHGT = 540
LS = 34
STRIP_Y = (150, 150 + PHGT + 120)


def plate(ink, w, h):
    station_bg(ink, w, h, 450, dado=300)
    door_s(ink, 480, 450, 100, 210, u=0.9)
    bell_s(ink, 0, 230, 1.2)
    bench_s(ink, 250, 530, 440, 1.3)
    person(ink, 230, 530, 1.45, "visitor", 1, pose="sit", mouth="flat", brows="flat", look=(0.3, 0.1),
           arms={"front": (30, 95), "back": (40, 110)},
           holding=lambda k, hf, hb: envelope_s(k, hf[0] + 2, hf[1] - 8, 96, 62))


PLATE = make_panel(PWID, PHGT, plate, seed=7, treat={WALL: "black", WALL2: "black", FLOOR: "white", WOOD: "white", DOORC: "white"})
PLATE_ID = art_id(PLATE)
HEAD = (230 + 3 * 1.45, 530 - 208 * 1.45)
MOUTH = (HEAD[0] + 18, HEAD[1] - 62)  # tails stop above the hat, never on the face

# balloon plane: one transparent sheet per occurrence. None = wordless.
OFF = (PWID - 4, 120)  # an off-panel speaker, right
STRIPS = [
    ("1 · she waits", [
        [("The bell first. Then I open it. That's the rule.", (270, 82), MOUTH, "speech")],
        [("That was a pigeon. Not the bell.", (270, 78), MOUTH, "speech")],
        None,
        [("I'm very good at waiting.", (270, 78), MOUTH, "speech")],
    ]),
    ("2 · her alibi", [
        [("Where were you at four?", (340, 62), OFF, "speech"), ("Right here.", (140, 200), (HEAD[0] - 20, HEAD[1] - 50), "speech")],
        [("On this bench. Ask the pigeons.", (270, 78), MOUTH, "speech")],
        [("And the service key?", (330, 80), OFF, "speech")],
        [("Look. The envelope is still sealed.", (270, 80), MOUTH, "speech")],
    ]),
]


def balloon_layer(items):
    k = Ink(0, 0, (PWID, PHGT), boil=0, wobble=0.9, seed=3)
    k.img = Image.new("RGBA", (PWID, PHGT), (0, 0, 0, 0))
    k.d = ImageDraw.Draw(k.img, "RGBA")
    for text, (cx, cy), tail, kind in items or []:
        balloon(k, cx, cy, text, LS, tail=tail, maxw=440 if tail is MOUTH else 360, kind=kind)
    return k.img


LAYERS = [[balloon_layer(it) if it else None for it in panels] for _, panels in STRIPS]

board = Board(PW, PH)
bi = board.ink()
RECTS = []
for s, (label, panels) in enumerate(STRIPS):
    row = []
    y = STRIP_Y[s]
    bi.text((board.m + 50, board.m + y - 22), label, "serif", 52, INK if s == 0 else ACCENT, anchor="ls")
    for p in range(4):
        x = 50 + p * (PWID + G)
        r = board.place(PLATE, x, y)
        lay = LAYERS[s][p]
        if lay is not None:
            board.img.paste(lay, (int(r[0]), int(r[1])), lay)
        row.append(r)
    RECTS.append(row)
bi.label((board.m + PW - 50, board.m + STRIP_Y[0] - 30), f"plate {PLATE_ID} × 8", 22, MUTED, anchor="rs")
# a board without balloons: the artwork-only raster
ART = Board(PW, PH)
for s in range(2):
    for p in range(4):
        ART.place(PLATE, 50 + p * (PWID + G), STRIP_Y[s])
hashes = {art_id(ART.img.crop(tuple(int(v) for v in r))) for row in RECTS for r in row}
assert hashes == {PLATE_ID}, hashes

# clean copy of the board with an empty balloon plane, for fades
BARE = board.img.copy()
for row in RECTS:
    for r in row:
        BARE.paste(PLATE, (int(r[0]), int(r[1])))

# ---------------------------------------------------------- reading
TITLE = 3.0
FULL = fit_box(board.page(), pad=0.0)
sh = Shots()
sh.add(FULL, 2.2, 0)
REVEAL = []  # (t, strip, panel)
for s in range(2):
    x0, y0 = RECTS[s][0][0], RECTS[s][0][1]
    strip_box = fit_box((x0, y0 - 90, RECTS[s][3][2], RECTS[s][3][3]), pad=0.02)
    sh.add(strip_box, 1.6, 0.9)
    for p in range(4):
        sh.add(fit_box(RECTS[s][p], pad=0.05), 2.9, 0.55)
        REVEAL.append((sh.t - 2.9, s, p))
    sh.add(strip_box, 2.6, 0.7)
sh.add(FULL, 7.5, 0.9)
DUR = round(TITLE + sh.t, 2)

film = Film(SLUG, seconds=DUR, boil=0, wobble=0)
grayscale_frames(film)
film.poster_at = TITLE + REVEAL[7][0] + 2.0


def board_at(tt):
    """The board with the balloon plane faded in panel by panel during the reading."""
    img = BARE.copy()
    for (t0, s, p) in REVEAL:
        lay = LAYERS[s][p]
        if lay is None:
            continue
        a = clamp((tt - t0 - 0.35) / 0.35)
        if a <= 0:
            continue
        r = RECTS[s][p]
        if a < 1:
            l2 = lay.copy()
            l2.putalpha(lay.getchannel("A").point(lambda v: int(v * a)))
            lay = l2
        img.paste(lay, (int(r[0]), int(r[1])), lay)
    return img


_cache = {}


@film.picture
def frame(t, ink):
    if t < TITLE:
        ink.card("Less than a quarter second", "one drawing, eight times · only the words move")
        ink.label((W / 2, H / 2 + 70), "after Menu & Trondheim", 13, MUTED, anchor="mm")
        if t > TITLE - 0.4:
            ink.d.rectangle([0, 0, W, H], fill=PAPER + (int(255 * (t - TITLE + 0.4) / 0.4),))
        return
    tt = t - TITLE
    # only rebuild the board while a balloon is fading
    key = tuple(int(clamp((tt - t0 - 0.35) / 0.35) * 12) for t0, s, p in REVEAL)
    if key not in _cache:
        _cache.clear()
        _cache[key] = board_at(tt)
    ink.paste(view(_cache[key], sh.at(tt)))
    if tt > sh.t - 7.5 + 1.0:
        a = clamp((tt - (sh.t - 6.5)) / 0.6)
        ink.caption("artwork layer identical in all eight panels · panel 3 of strip 1 is wordless", a, y=H - 18, size=16, kind="sans")


@film.sound
def sound(mix):
    mix.room(0, DUR, 0.03)
    mix.wind(0, DUR, 0.02)
    for t0, s, p in REVEAL:
        t = TITLE + t0 + 0.4
        items = STRIPS[s][1][p]
        if items is None:
            continue  # declared silence: room tone only
        for k, (text, _, tail, _) in enumerate(items):
            off = tail == OFF
            voice(mix, t + k * 1.1, text, 96 if off else 185, 0.7 if off else 0.0, 0.09 if not off else 0.07)
        if s == 0 and p == 1:  # the pigeon, not the bell
            for k in range(3):
                mix.note(t - 0.3 + k * 0.28, 310 - k * 12, 0.25, 0.06, 0.5, "sine", 0.04, 0.15, 0.2)
    mix.bell(DUR - 6.5, 523, 4.0, 0.12, -0.4)
    mix.reverb(0.2)


if __name__ == "__main__":
    print("plate", PLATE_ID, "dur", DUR)
    film.render()

"""Un homme qui dort — one 35-second photo-film, screened twice.

Foraged FSA/OWI photographs (Esther Bubley's Washington boardinghouse, 1943;
a rooming-house stairway, 1935): a man in bed, a man in the upstairs hall
while the telephone rings, someone else answering it, a held shot of a man at
his desk with only room tone, and the same stairway twice (the same image
with the same move, frame for frame). The camera is always the photographer's,
never his. The
second-person narration is the same seven lines both times: in pass 1 every
line arrives 1.2 s before the action it names, in pass 2 1.3 s after it.
"""
import math
from kit_cinema_a import *

WALL = (196, 194, 188)
SHADE = (62, 68, 82)
BLANKET = (150, 156, 170)
FLOOR = (150, 140, 128)
LEAD, LAG = -1.2, 1.3

PICT = [("bed", 6.0), ("phone", 8.0), ("held", 7.0), ("stairsA", 6.0), ("stairsB", 8.0)]
PLEN = sum(d for _, d in PICT)  # 35 s
RINGS = [7.0, 8.8, 10.6]
LINES = [(2.0, "You wake. Nothing in the room asks you to."),
         (7.0, "The telephone rings in the hall. You let it ring."),
         (10.6, "It rings again. You hear it as if through a wall."),
         (12.6, "Someone else answers. You stay where you are."),
         (21.5, "You go down the stairs."),
         (27.5, "You go down the same stairs."),
         (30.6, "Nobody is waiting at the bottom.")]
CAP = 2.0
SEGS = [("title", 2.0), ("card1", 1.4), ("pass1", PLEN), ("card2", 1.4), ("pass2", PLEN)]
TOTAL = sum(d for _, d in SEGS)
ST = starts(SEGS)


# --------------------------------------------------------------- shots ---
# Foraged: Esther Bubley's 1943 boardinghouse photographs and a 1935 rooming-
# house stairway, all FSA/OWI (Library of Congress, no known restrictions).
# Each photograph is cropped once inside its negative border; the only camera
# operation is a slow push, and the stairway carries the identical push twice.

SRC = SOURCES / "un-homme-qui-dort"
# (file, crop box inside the negative border)
PHOTOS = {"bed": ("loc_2017862344.jpg", (0.05, 0.40, 0.86, 0.93)),
          "hall": ("loc_2017862356.jpg", (0.12, 0.08, 0.90, 0.93)),
          "phone": ("loc_2017862346.jpg", (0.04, 0.08, 0.86, 0.80)),
          "held": ("loc_2017862343.jpg", (0.06, 0.07, 0.86, 0.93)),
          "stairs": ("loc_2017714055.jpg", (0.0, 0.0, 0.94, 0.88))}
IMG = {k: photo_fit(SRC / f, (W + 200, H + 112), box=b, gray=True) for k, (f, b) in PHOTOS.items()}


def stair_move(lt):
    """The one stairway move, used for both flights (same function, same frames)."""
    return push(IMG["stairs"], min(lt, 6.0), 6.0, 1.02, 1.16, (0.42, 0.40), (0.56, 0.62))


def picture_at(t):
    seg, lt, dur, a = segment(t, PICT)
    if seg == "bed":
        return seg, push(IMG["bed"], lt, dur, 1.0, 1.10, (0.5, 0.5), (0.55, 0.45))
    if seg == "phone":
        if lt < 4.6:  # he stays in the hall while it rings
            return seg, push(IMG["hall"], lt, 4.6, 1.0, 1.0, (0.5, 0.4), (0.5, 0.4))
        return seg, push(IMG["phone"], lt - 4.6, 3.4, 1.0, 1.05, (0.5, 0.45), (0.5, 0.45))
    if seg == "held":
        return seg, push(IMG["held"], 0, 1, 1.0, 1.0)  # held: no move at all
    return seg, stair_move(lt)  # stairsA and stairsB: identical


def lines_for(off):
    return [(a + off, a + off + CAP, s) for a, s in LINES]


GREY = (180, 180, 178)


def score_strip(ink, t, off):
    x0, x1, y = 150, 810, 18
    ink.d.rectangle([x0 - 90, y - 10, x1 + 12, y + 26], fill=(0, 0, 0, 150))
    ink.line([(x0, y), (x1, y)], (120, 120, 120), 1, rough=False)
    ink.line([(x0, y + 14), (x1, y + 14)], (120, 120, 120), 1, rough=False)
    ink.text((x0 - 82, y - 7), "action", "mono", 10, GREY)
    ink.text((x0 - 82, y + 7), "voice", "mono", 10, (250, 250, 250))
    for a, _ in LINES:
        xa = lerp(x0, x1, a / PLEN)
        ink.line([(xa, y - 5), (xa, y + 5)], GREY, 2, rough=False)
        xv = lerp(x0, x1, (a + off) / PLEN)
        ink.line([(xv, y + 9), (xv, y + 19)], (250, 250, 250), 2, rough=False)
    h0, h1 = lerp(x0, x1, 14 / PLEN), lerp(x0, x1, 21 / PLEN)
    ink.d.rectangle([h0, y + 2, h1, y + 12], fill=(90, 90, 90, 180))
    px = lerp(x0, x1, t / PLEN)
    ink.line([(px, y - 8), (px, y + 22)], (255, 255, 255), 1, rough=False)


_rf = SRC / "Model_500_Telephone_British_ring.ogg"
RING = load_audio(_rf, 0.0, 1.6) * np.concatenate([np.ones(int(1.45 * RATE)), np.linspace(1, 0, int(0.15 * RATE))])[: int(1.6 * RATE)] if _rf.exists() else None

film = Film("un-homme-qui-dort", seconds=TOTAL, boil=0, wobble=0)
film.poster_at = ST["pass1"] + 17.0


@film.picture
def frame(t, ink):
    seg, lt, dur, _ = segment(t, SEGS)
    ink._grain = False
    if seg == "title":
        title_card(ink, "Un homme qui dort", "the same pictures twice · the same words twice · the voice moves", ground=(0, 0, 0), fg=(240, 240, 236), subfg=(150, 150, 150))
        fade_edges(ink, lt, dur, 0.3, (0, 0, 0))
        return
    if seg in ("card1", "card2"):
        title_card(ink, "Track 1 · the voice ahead" if seg == "card1" else "Track 2 · the voice after",
                   f"each line {abs(LEAD):.1f} s before what it names" if seg == "card1" else f"each line {LAG:.1f} s after what it names",
                   ground=(0, 0, 0), fg=(240, 240, 236), subfg=(150, 150, 150), size=44)
        fade_edges(ink, lt, dur, 0.25, (0, 0, 0))
        return
    off = LEAD if seg == "pass1" else LAG
    pseg, img = picture_at(lt)
    ink.paste(img)
    _, l2, d2, _ = segment(lt, PICT)
    fade_edges(ink, l2, d2, 0.12, (0, 0, 0))
    for a, b, s in lines_for(off):
        if a <= lt < b:
            subtitle(ink, s, alpha=min(1, (lt - a) / 0.15, (b - lt) / 0.2), size=27)
    if pseg == "held" and not any(a <= lt < b for a, b, _ in lines_for(off)):
        tag(ink, (W - 20, H - 30), "room sound only", 11, GREY, (0, 0, 0), anchor="ra", alpha=140)
    score_strip(ink, lt, off)
    tag(ink, (20, H - 30), "TRACK 1 · ahead" if seg == "pass1" else "TRACK 2 · after", 11, (230, 230, 230), (0, 0, 0), alpha=150)


@film.sound
def sound(mix):
    for pas, off in (("pass1", LEAD), ("pass2", LAG)):
        p = ST[pas]
        mix.room(p, PLEN, 0.06, hum=50)
        mix.click(p + 1.9, 0.1, -0.3, 1500, 0.08)   # bedsprings
        mix.thud(p + 2.1, 90, 0.1, -0.3)
        for r in RINGS:
            if RING is not None:
                mix.add(RING, p + r, 0.32, 0.45)
            else:
                phone_ring(mix, p + r, 0.2, 0.45)
        # stairs: the same footfalls on both flights (same clip, same steps)
        for base in (21.0, 27.0):
            for s in range(12):
                mix.step(p + base + 0.3 + s * (5.1 / 12) + 0.25, 0.3, lerp(-0.6, 0.6, s / 11), "wood")
        # the narration, as a murmur under each caption
        for i, (a, b, s) in enumerate(lines_for(off)):
            mix.murmur(p + a + 0.1, CAP - 0.35, 0.15, 108, 0.0, seed=20 + i)
    mix.reverb(0.12, 0.8)


if __name__ == "__main__":
    film.render()

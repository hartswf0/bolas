"""Un homme qui dort — one 35-second picture, screened twice.

A man wakes, lets a telephone ring, sits in a held shot with only room tone,
and goes down the same staircase twice (the staircase shot is one rendered
clip reused frame for frame). The camera never takes his viewpoint. The
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
         (7.0, "The telephone rings. You let it ring."),
         (10.6, "It rings again. You hear it as if through a wall."),
         (12.6, "You look away, towards the window."),
         (21.5, "You go down the stairs."),
         (27.5, "You go down the same stairs."),
         (30.6, "Nobody is waiting at the bottom.")]
CAP = 2.0
SEGS = [("title", 2.0), ("card1", 1.4), ("pass1", PLEN), ("card2", 1.4), ("pass2", PLEN)]
TOTAL = sum(d for _, d in SEGS)
ST = starts(SEGS)


# --------------------------------------------------------------- shots ---
# High-contrast black-and-white photography: hard side light, deep blacks,
# soft grain, close framing, shadow doubles on the wall.

LIGHT = (-0.5, -0.45, 0.75)
HAIR_T = hair_tex(W, H, 4)
CLOTH = box_blur(fnoise(W, H, 8, octaves=4, base=3), 6) * 40
GRADE = dict(mono=True, contrast=1.5, pivot=0.42, crush=0.05, blur=0.8, vignette=0.55, grain=0.055, grain_size=1.5,
             halation=0.12, hal_color=(1, 1, 1), hal_r=10)


def s_bed(t):
    """Overhead: the face on the pillow; eyes open at 2.0, he sits up out of frame at 3.1."""
    R = Relief(W, H)
    R.field(CLOTH, (236, 236, 232), tex=0.92 + 0.08 * fnoise(W, H, 9, 3, 6))
    R.ellipsoid(470, 220, 360, 190, depth=70, base=20, color=(244, 244, 240), gloss=0.05)
    R.dent(470, 230, 170, 120, 26)
    up = ease(t, 3.1, 4.4)
    cy = lerp(230, -330, up)
    s = lerp(0.92, 1.25, up)
    if cy > -300:
        face(R, 470, cy, s, look=(0.0, 0.0), eyes_open=ease(t, 1.8, 2.3) * (1 - up), hair=(70, 62, 56), tex=HAIR_T, base=60, neck=False)
    # blanket from the chin down, its folds from the same cloth noise
    blank = poly_mask(W, H, [(0, 400), (960, 380), (960, 540), (0, 540)], blur=6)
    R.z += blank * (90 + CLOTH * 1.5)
    R.col = R.col * (1 - blank[..., None]) + np.asarray((120, 120, 124), np.float32) / 255 * blank[..., None]
    return R.render(light=LIGHT, amb=0.2, diff=0.75, spec=0.15, smooth=5)


def phone_obj(R, x, y, ringing, t):
    dx = 3 * math.sin(t * 90) if ringing else 0
    R.slab([(x - 110 + dx, y), (x + 110 + dx, y), (x + 86 + dx, y - 80), (x - 86 + dx, y - 80)], height=70, bevel=10, base=120, color=(28, 28, 30), gloss=0.9)
    R.capsule((x - 120 + dx, y - 104), (x + 120 + dx, y - 104), 26, depth=1.0, base=200, color=(22, 22, 24), gloss=1.0)
    R.ellipsoid(x - 120 + dx, y - 100, 36, 30, base=200, color=(22, 22, 24), gloss=1.0)
    R.ellipsoid(x + 120 + dx, y - 100, 36, 30, base=200, color=(22, 22, 24), gloss=1.0)
    R.ellipsoid(x + dx, y - 36, 40, 30, depth=10, base=190, color=(210, 210, 206), gloss=0.5)


def s_phone(t):
    """Across the room: him on the bed edge, his shadow double on the wall, the telephone foreground left."""
    wall = vgrad(H, W, (210, 210, 206), (150, 150, 148)) * (0.92 + 0.08 * fnoise(W, H, 3, 3, 4))[..., None]
    lit = np.clip(np.linspace(1.2, 0.35, W, dtype=np.float32), 0, 1)[None, :, None]
    R = Relief(W, H, bg=wall * lit)
    look = ease(t, 6.6, 7.4)
    turn = lerp(0.35, -0.7, look)
    face(R, 610, 250, 0.82, look=(lerp(0.3, -0.9, look), 0.1), turn=turn, hair=(70, 62, 56), tex=HAIR_T, collar=(200, 200, 196))
    R.slab([(420, 440), (820, 440), (900, 540), (340, 540)], height=60, bevel=16, base=0, color=(90, 90, 92))
    ringing = any(r <= t + 6.0 < r + 1.05 for r in RINGS)
    a = R.render(light=LIGHT, amb=0.2, diff=0.78, spec=0.2, smooth=5)
    a = cast_shadow(a, R.silhouette(), 150, 18, 10, 0.75)  # the shadow double
    R2 = Relief(W, H, bg=a)
    phone_obj(R2, 190, 520, ringing, t)
    b = R2.render(light=LIGHT, amb=0.2, diff=0.9, spec=1.0, shin=60, smooth=2)
    return blur_arr(b, 0) if not ringing else b


_HELD = None


def s_held(t):
    """Held shot: his head against the wall, the double on the wall behind. Only room sound."""
    global _HELD
    if _HELD is None:
        wall = vgrad(H, W, (238, 238, 234), (200, 200, 196)) * np.clip(np.linspace(1.08, 0.62, W, dtype=np.float32), 0, 1)[None, :, None]
        R = Relief(W, H, bg=wall)
        face(R, 360, 250, 1.12, look=(-0.3, 0.15), turn=0.25, hair=(74, 66, 58), tex=HAIR_T, collar=(226, 226, 222))
        a = R.render(light=(-0.6, -0.4, 0.7), amb=0.18, diff=0.8, spec=0.2, smooth=6)
        _HELD = cast_shadow(a, R.silhouette(), 330, 10, 3, 0.78)  # the shadow double on the wall
    return _HELD


def s_stairs(k, u, ink):
    t = k / FPS
    wall = vgrad(H, W, (150, 150, 148), (70, 70, 70))
    R = Relief(W, H, bg=wall)
    steps, x0, y0, x1, y1 = 12, 40, 110, 900, 500
    sw, sh = (x1 - x0) / steps, (y1 - y0) / steps
    for s_ in range(steps):
        xa = x0 + s_ * sw
        ya = y0 + (s_ + 1) * sh
        R.slab([(xa, ya), (xa + sw + 2, ya), (xa + sw + 2, 540), (xa, 540)], height=20 + s_ * 6, bevel=3, base=0, color=(200, 200, 196))
    R.capsule((0, y0 - 90), (x1 + 60, y1 - 90), 6, base=200, color=(30, 30, 30), gloss=0.8)
    p = ramp(t, 0.3, 5.4) * 1.18 - 0.05
    s_f = p * steps
    xs = x0 + s_f * sw
    ys = y0 + (math.floor(max(0, s_f)) + 1) * sh if s_f > 0 else y0
    if xs < 1060:
        person(R, xs, ys, 230, phase=s_f / 2, pose="walk", coat=(36, 36, 38), trousers=(24, 24, 26), hair=(20, 20, 20), base=150)
    a = R.render(light=(-0.6, -0.7, 0.5), amb=0.3, diff=0.9, spec=0.3, smooth=2)
    # hard window light falling across the stairs, and his long shadow
    beam = poly_mask(W, H, [(300, 0), (640, 0), (980, 540), (480, 540)], blur=14)
    a = a * (0.45 + 0.75 * beam[..., None])
    if xs < 1060:
        fig = Relief(W, H)
        person(fig, xs, ys, 230, phase=s_f / 2, pose="walk", base=150)
        a = cast_shadow(a, fig.silhouette(), 120, -14, 4, 0.6)
    ink.img = Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8))


STAIRS = [np.asarray(f, np.float32) / 255 for f in build_clip(s_stairs, int(6 * FPS), (W, H), boil=0, wobble=0, seed=5)]


def picture_at(t):
    seg, lt, dur, a = segment(t, PICT)
    if seg == "bed":
        return seg, s_bed(lt)
    if seg == "phone":
        return seg, s_phone(lt)
    if seg == "held":
        return seg, s_held(lt)
    k = min(len(STAIRS) - 1, int(lt * FPS))
    return seg, STAIRS[k]  # stairsA and stairsB are the same frames


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


film = Film("un-homme-qui-dort", seconds=TOTAL, boil=0, wobble=0)
film.poster_at = ST["pass1"] + 17.0


@film.picture
def frame(t, ink):
    seg, lt, dur, _ = segment(t, SEGS)
    ink._grain = False
    if seg == "title":
        title_card(ink, "Un homme qui dort", "the same picture twice · the same words twice · the voice moves", ground=(0, 0, 0), fg=(240, 240, 236), subfg=(150, 150, 150))
        fade_edges(ink, lt, dur, 0.3, (0, 0, 0))
        return
    if seg in ("card1", "card2"):
        title_card(ink, "Track 1 · the voice ahead" if seg == "card1" else "Track 2 · the voice after",
                   f"each line {abs(LEAD):.1f} s before what it names" if seg == "card1" else f"each line {LAG:.1f} s after what it names",
                   ground=(0, 0, 0), fg=(240, 240, 236), subfg=(150, 150, 150), size=44)
        fade_edges(ink, lt, dur, 0.25, (0, 0, 0))
        return
    off = LEAD if seg == "pass1" else LAG
    pseg, arr = picture_at(lt)
    put(ink, photo(arr, seed=int(t * FPS), **GRADE))
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

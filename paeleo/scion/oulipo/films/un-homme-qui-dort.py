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

def room_box(ink, light=0.0):
    ink.fill(mix_color(SHADE, WALL, 0.55 + 0.35 * light))
    ink.poly([(180, 60), (780, 60), (780, 330), (180, 330)], fill=mix_color(WALL, PAGE, 0.3 * light), color=INK, width=2)
    ink.poly([(180, 330), (780, 330), (960, 540), (0, 540)], fill=FLOOR, color=INK, width=2)
    ink.line([(0, 0), (180, 60)], INK, 2)
    ink.line([(960, 0), (780, 60)], INK, 2)
    ink.poly([(520, 100), (680, 100), (680, 230), (520, 230)], fill=mix_color((90, 100, 120), (235, 232, 215), light), color=INK, width=3)
    ink.line([(600, 100), (600, 230)], INK, 2)
    ink.line([(520, 165), (680, 165)], INK, 2)
    if light > 0:
        ink.poly([(520, 330), (680, 330), (760, 470), (470, 470)], fill=(240, 232, 205, int(90 * light)), color=None)


def s_bed(t, ink):
    light = ease(t, 0, 5)
    room_box(ink, light * 0.6)
    # bed in perspective, lower left
    ink.poly([(90, 380), (520, 380), (600, 500), (40, 500)], fill=(225, 222, 214), color=INK, width=2.5)
    ink.rect(70, 300, 110, 500, fill=(120, 96, 80), color=INK, width=2)
    up = ease(t, 2.0, 3.1)
    hip = (290, 430)
    ang = lerp(math.pi * 1.02, math.pi * 1.5, up)  # lying (head on the pillow, left) -> sitting up
    neck = (hip[0] + math.cos(ang) * 110, hip[1] + math.sin(ang) * 110)
    head = (hip[0] + math.cos(ang) * 136, hip[1] + math.sin(ang) * 136)
    ink.ellipse(150, 420, 46, 18, fill=PAGE, color=INK, width=2)  # pillow
    ink.line([hip, neck], SHADE, 9)
    ink.circle(head[0], head[1], 18, fill=PAGE, color=INK, width=2.5)
    if up > 0.5:
        ink.line([(neck[0], neck[1] + 14), (neck[0] + 40, neck[1] + 60), (neck[0] + 80, neck[1] + 70)], INK, 3)
    bx = lerp(170, 280, up)
    ink.poly([(bx, 410), (560, 400), (590, 480), (bx - 10, 470)], fill=BLANKET, color=INK, width=2.5)
    # chair with clothes
    ink.rect(700, 360, 780, 372, fill=(120, 96, 80), color=INK, width=2)
    ink.line([(705, 372), (700, 440)], INK, 3)
    ink.line([(775, 372), (780, 440)], INK, 3)
    ink.line([(775, 360), (785, 280)], INK, 3)
    ink.poly([(740, 300), (790, 290), (780, 380), (735, 370)], fill=SHADE, color=INK, width=2)


def phone(ink, x, y, ringing):
    dx = 2.5 * math.sin(ink.t * 90) if ringing else 0
    ink.poly([(x - 46 + dx, y), (x + 46 + dx, y), (x + 36 + dx, y - 34), (x - 36 + dx, y - 34)], fill=INK, color=INK, width=2)
    ink.circle(x + dx, y - 16, 11, fill=PAGE, color=INK, width=2)
    ink.poly([(x - 52 + dx, y - 44), (x + 52 + dx, y - 44), (x + 44 + dx, y - 56), (x - 44 + dx, y - 56)], fill=INK, color=INK, width=2)
    if ringing:
        for r in (70, 90):
            ink.arc(x, y - 40, r, -math.pi * 0.35, -math.pi * 0.08, INK, 2)
            ink.arc(x, y - 40, r, -math.pi * 0.92, -math.pi * 0.65, INK, 2)


def s_phone(t, ink):
    ink.fill(WALL)
    ink.d.rectangle([0, 380, 960, 540], fill=FLOOR)
    ink.line([(0, 380), (960, 380)], INK, 2)
    # bed edge and the seated man (seen from across the room)
    ink.rect(120, 330, 470, 400, fill=(225, 222, 214), color=INK, width=2.5)
    ink.poly([(120, 330), (470, 330), (470, 352), (120, 360)], fill=BLANKET, color=INK, width=2)
    turn = ease(t, 6.6, 7.2)
    figure(ink, 300, 432, 1.25, "sit", facing=1 if turn < 0.5 else -1, coat=SHADE, arm=30)
    # table with telephone and the sealed envelope
    ink.rect(640, 330, 860, 344, fill=(120, 96, 80), color=INK, width=2)
    ink.line([(660, 344), (660, 470)], INK, 4)
    ink.line([(840, 344), (840, 470)], INK, 4)
    ringing = any(r <= t + 6.0 < r + 1.05 for r in RINGS)
    phone(ink, 710, 330, ringing)
    envelope(ink, 805, 318, 64, 26)
    # door frame we look through (outside his viewpoint)
    ink.d.rectangle([0, 0, 70, 540], fill=SHADE)
    ink.d.rectangle([890, 0, 960, 540], fill=SHADE)
    ink.d.rectangle([0, 0, 960, 40], fill=SHADE)
    ink.line([(70, 40), (70, 540)], INK, 3)
    ink.line([(890, 40), (890, 540)], INK, 3)
    ink.line([(70, 40), (890, 40)], INK, 3)


def s_held(t, ink):
    ink.fill(mix_color(SHADE, WALL, 0.4))
    ink.poly([(330, 70), (630, 70), (630, 360), (330, 360)], fill=(232, 230, 214), color=INK, width=4)
    ink.line([(480, 70), (480, 360)], INK, 3)
    ink.line([(330, 215), (630, 215)], INK, 3)
    sway = 6 * math.sin(t * 0.9)
    ink.poly([(300, 60), (360 + sway, 60), (350 + sway * 1.5, 380), (296, 380)], fill=(170, 150, 140), color=INK, width=2)
    ink.d.rectangle([0, 400, 960, 540], fill=FLOOR)
    ink.line([(0, 400), (960, 400)], INK, 2)
    ink.rect(420, 405, 540, 415, fill=(120, 96, 80), color=INK, width=2)
    ink.line([(430, 415), (430, 470)], INK, 3)
    ink.line([(530, 415), (530, 470)], INK, 3)
    figure(ink, 470, 470, 1.5, "sit", facing=-1, coat=(40, 42, 50), color=(30, 30, 36), arm=20)


def s_stairs(k, u, ink):
    t = k / FPS
    ink.fill((176, 172, 166))
    ink.hatch(0, 0, 960, 540, gap=11, angle=-30, color=(150, 146, 140), width=1, alpha=120)
    steps, x0, y0, x1, y1 = 12, 60, 130, 900, 480
    sw, sh = (x1 - x0) / steps, (y1 - y0) / steps
    pts = [(0, y0), (x0, y0)]
    for s in range(steps):
        pts += [(x0 + s * sw, y0 + (s + 1) * sh), (x0 + (s + 1) * sw, y0 + (s + 1) * sh)]
    pts += [(960, y1), (960, 540), (0, 540)]
    ink.poly(pts, fill=(120, 108, 96), color=INK, width=2.5)
    ink.line([(0, y0 - 80), (x0, y0 - 80)] + [(x1, y1 - 80), (960, y1 - 80)], INK, 3)
    for s in range(0, steps + 1, 2):
        ink.line([(x0 + s * sw, y0 + s * sh - 80), (x0 + s * sw, y0 + s * sh)], INK, 2)
    ink.line([(480, 0), (480, 40)], INK, 2)
    ink.circle(480, 52, 12, fill=(250, 236, 190), color=INK, width=2)
    p = ramp(t, 0.3, 5.4) * 1.18 - 0.05
    s_f = p * steps
    xs = x0 + s_f * sw
    ys = y0 + (math.floor(max(0, s_f)) + 1) * sh if s_f > 0 else y0
    if xs < 1000:
        figure(ink, xs, ys, 0.9, "walk", phase=s_f / 2, facing=1, coat=SHADE, hat=True)


STAIRS = build_clip(s_stairs, int(6 * FPS), (W, H), boil=6, wobble=1.1, seed=5)


def picture_at(t, ink):
    seg, lt, dur, a = segment(t, PICT)
    if seg == "bed":
        s_bed(lt, ink)
    elif seg == "phone":
        s_phone(lt, ink)
    elif seg == "held":
        s_held(lt, ink)
    else:
        k = min(len(STAIRS) - 1, int(lt * FPS))
        ink.paste(STAIRS[k])  # stairsA and stairsB are the same frames
    return seg


def lines_for(off):
    return [(a + off, a + off + CAP, s) for a, s in LINES]


def score_strip(ink, t, off):
    x0, x1, y = 150, 810, 20
    ink.d.rectangle([x0 - 90, y - 10, x1 + 12, y + 26], fill=NIGHT + (160,))
    ink.line([(x0, y), (x1, y)], RULE, 1, rough=False)
    ink.line([(x0, y + 14), (x1, y + 14)], RULE, 1, rough=False)
    ink.text((x0 - 82, y - 7), "action", "mono", 10, PAGE)
    ink.text((x0 - 82, y + 7), "voice", "mono", 10, (230, 150, 160))
    for a, _ in LINES:
        xa = lerp(x0, x1, a / PLEN)
        ink.line([(xa, y - 5), (xa, y + 5)], PAGE, 2, rough=False)
        xv = lerp(x0, x1, (a + off) / PLEN)
        ink.line([(xv, y + 9), (xv, y + 19)], (230, 150, 160), 2, rough=False)
    h0, h1 = lerp(x0, x1, 14 / PLEN), lerp(x0, x1, 21 / PLEN)
    ink.d.rectangle([h0, y + 2, h1, y + 12], fill=BRASS + (140,))
    px = lerp(x0, x1, t / PLEN)
    ink.line([(px, y - 8), (px, y + 22)], ACCENT, 2, rough=False)


film = Film("un-homme-qui-dort", seconds=TOTAL, boil=6, wobble=1.1)
film.poster_at = ST["pass1"] + 9.5


@film.picture
def frame(t, ink):
    seg, lt, dur, _ = segment(t, SEGS)
    if seg == "title":
        title_card(ink, "Un homme qui dort", "the same picture twice · the same words twice · the voice moves")
        fade_edges(ink, lt, dur, 0.3)
        return
    if seg in ("card1", "card2"):
        title_card(ink, "Track 1 · the voice ahead" if seg == "card1" else "Track 2 · the voice after",
                   f"each line {abs(LEAD):.1f} s before what it names" if seg == "card1" else f"each line {LAG:.1f} s after what it names", size=44)
        fade_edges(ink, lt, dur, 0.25)
        return
    off = LEAD if seg == "pass1" else LAG
    pseg = picture_at(lt, ink)
    ink.vignette(0.45)
    for a, b, s in lines_for(off):
        if a <= lt < b:
            ink.caption(s, alpha=min(1, (lt - a) / 0.15, (b - lt) / 0.2), size=26)
    if pseg == "held" and not any(a <= lt < b for a, b, _ in lines_for(off)):
        tag(ink, (W - 20, H - 30), "room sound only", 11, RULE, NIGHT, anchor="ra", alpha=150)
    score_strip(ink, lt, off)
    tag(ink, (20, H - 30), "TRACK 1 · ahead" if seg == "pass1" else "TRACK 2 · after", 11, PAGE, NIGHT, alpha=170)


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

"""Les Lieux d'une fugue — a fictional childhood departure told over present-day places.

Three places, drawn as they are now: a doorway, a junction, a station bench.
The doorway is shot twice from the same position (morning, evening). Over
the evening doorway the voice remembers the bench; then the bench itself
returns, in declared silence. Every shot carries its place_id and capture
time; every recollection carries its status and an interval, not a date.
"""
import math
from PIL import Image
from kit_cinema_a import *

STONE = (196, 186, 170)
PAVE = (172, 166, 156)
DOOR = (78, 92, 86)

SEGS = [("title", 2.5), ("door_am", 10.0), ("junction", 10.0), ("door_pm", 13.0), ("bench", 11.0), ("record", 7.0)]
TOTAL = sum(d for _, d in SEGS)
ST = starts(SEGS)
SLATES = {"door_am": "PLACE 01 · doorway · present · captured 08:10",
          "junction": "PLACE 02 · junction · present · captured 08:40",
          "door_pm": "PLACE 01 · doorway · present · captured 18:55 · same position",
          "bench": "PLACE 03 · station bench · present · silence"}
# (segment, from, to, text) - all recollections; status line shown above
VOICE = [("door_am", 1.2, 4.8, "I left by this door, I think. I was nine, or ten."),
         ("door_am", 5.4, 9.2, "It was winter, roughly. My coat was too big."),
         ("junction", 1.0, 4.8, "At the corner the pavement splits. I took the left one,"),
         ("junction", 5.0, 9.0, "the one that goes down to the station. Or I believe it does."),
         ("door_pm", 1.4, 5.2, "There was a bench in the hall. I sat with my satchel on my knees."),
         ("door_pm", 5.8, 9.2, "A bell rang somewhere above me. I didn't know what it was for."),
         ("door_pm", 9.6, 12.4, "Someone walked me home. I don't remember who.")]


def facade(ink, evening):
    sky = mix_color((214, 222, 226), (58, 62, 84), evening)
    ink.fill(sky)
    wall = mix_color(STONE, (112, 102, 100), evening)
    ink.d.rectangle([90, 0, 870, 420], fill=wall)
    for y in range(30, 420, 34):
        ink.line([(90, y), (870, y)], mix_color(RULE, (90, 82, 80), evening), 1, alpha=150)
    # windows
    for x in (170, 640):
        lit = evening > 0.5 and x == 640
        ink.rect(x, 70, x + 130, 230, fill=(250, 214, 140) if lit else mix_color((150, 164, 170), (40, 44, 58), evening), color=INK, width=3)
        ink.line([(x + 65, 70), (x + 65, 230)], INK, 2)
        ink.line([(x, 150), (x + 130, 150)], INK, 2)
        ink.rect(x - 10, 230, x + 140, 242, fill=mix_color(PAGE, (120, 110, 104), evening), color=INK, width=2)
    # the door
    ink.rect(400, 150, 560, 420, fill=mix_color(DOOR, (40, 48, 46), evening), color=INK, width=3)
    for yy in (180, 300):
        ink.rect(420, yy, 540, yy + 100, fill=None, color=INK, width=1.5)
    ink.circle(540, 300, 5, fill=BRASS, color=INK, width=1.5)
    ink.rect(455, 118, 505, 142, fill=PAGE, color=INK, width=1.5)
    ink.text((480, 130), "14", "serif", 20, INK, anchor="mm")
    ink.rect(380, 420, 580, 438, fill=mix_color((210, 202, 190), (100, 94, 90), evening), color=INK, width=2)
    # pavement with seams
    ink.d.rectangle([0, 438, 960, 540], fill=mix_color(PAVE, (78, 76, 80), evening))
    ink.line([(0, 438), (960, 438)], INK, 2)
    for x in range(-600, 1600, 120):
        ink.line([(480 + (x - 480) * 0.45, 438), (x, 540)], INK, 1.2, alpha=120)
    ink.line([(0, 482), (960, 482)], INK, 1.2, alpha=120)
    if evening > 0.5:
        # lamp above the door and its pool of light; long shadow of the step
        ink.line([(480, 96), (480, 108)], INK, 2)
        ink.circle(480, 100, 9, fill=(255, 226, 150), color=INK, width=2)
        ink.poly([(380, 438), (580, 438), (680, 540), (290, 540)], fill=(255, 220, 150, 60), color=None)
    else:
        ink.poly([(870, 0), (960, 0), (960, 540), (760, 540), (870, 420)], fill=(0, 0, 0, 30), color=None)


def junction(ink, t):
    ink.fill((214, 222, 226))
    ink.d.rectangle([0, 230, 960, 540], fill=(150, 146, 140))
    ink.line([(0, 230), (960, 230)], INK, 2)
    # two roads leaving the corner
    ink.poly([(440, 540), (560, 540), (300, 230), (230, 230)], fill=(110, 108, 108), color=INK, width=2)
    ink.poly([(560, 540), (700, 540), (760, 230), (690, 230)], fill=(110, 108, 108), color=INK, width=2)
    # the pavement island between them, with its seam
    ink.poly([(560, 540), (300, 230), (690, 230)], fill=PAVE, color=INK, width=2)
    for f in (0.25, 0.5, 0.75):
        a = lerp2((560, 540), (300, 230), f)
        b = lerp2((560, 540), (690, 230), f)
        ink.line([a, b], INK, 1.2, alpha=140)
    ink.line([(560, 540), (495, 230)], ACCENT, 2.2)  # the seam the voice follows
    # houses at the horizon
    for x, w, h in ((40, 160, 120), (210, 90, 90), (780, 150, 130)):
        ink.rect(x, 230 - h, x + w, 230, fill=STONE, color=INK, width=2)
    # lamp post and sign
    ink.line([(620, 470), (620, 220)], INK, 4)
    ink.rect(520, 236, 612, 262, fill=PAGE, color=INK, width=2)
    ink.text((576, 249), "GARE", "mono", 13, INK, anchor="mm")
    ink.poly([(530, 249), (544, 241), (544, 257)], fill=INK, color=INK, width=1, rough=False)
    ink.line([(544, 249), (556, 249)], INK, 3, rough=False)
    # a passing car in the present
    cx = lerp(1100, -200, ramp(t, 3.0, 6.5))
    ink.rect(cx, 196, cx + 110, 228, fill=(150, 60, 60), color=INK, width=2)
    ink.circle(cx + 22, 228, 9, fill=INK, color=INK, width=1)
    ink.circle(cx + 88, 228, 9, fill=INK, color=INK, width=1)


def build_bench():
    w, h = 1152, 648
    ink = Ink(0, 0, (w, h), boil=0, wobble=1.0, seed=3)
    ink.paper((206, 200, 188))
    for x in range(0, w, 64):
        ink.line([(x, 0), (x, 430)], RULE, 1, alpha=150)
    for y in range(0, 430, 32):
        ink.line([(0, y), (w, y)], RULE, 1, alpha=120)
    ink.d.rectangle([0, 430, w, h], fill=(164, 156, 144))
    ink.line([(0, 430), (w, 430)], INK, 2)
    for x in (200, 420, 640):
        ink.rect(x, 60, x + 130, 230, fill=(236, 236, 224), color=INK, width=3)
        ink.line([(x + 65, 60), (x + 65, 230)], INK, 2)
    ink.poly([(200, 430), (330, 430), (420, 648), (170, 648)], fill=(240, 236, 220, 90), color=None)
    ink.poly([(640, 430), (770, 430), (900, 648), (620, 648)], fill=(240, 236, 220, 90), color=None)
    clock(ink, 905, 120, 46, hours=4 + 10 / 60)
    door(ink, 1010, 430, 100, 190, sign="SERVICE")
    bench(ink, 520, 520, 300)
    return ink.img.convert("RGB")


BENCH = build_bench()


def bench_view(t):
    z = 1.0 + 0.14 * ease(t, 0, 11)
    cw, ch = 1152 / z, 648 / z
    cx, cy = lerp(576, 540, ease(t, 0, 11)), lerp(324, 380, ease(t, 0, 11))
    cx = min(max(cx, cw / 2), 1152 - cw / 2)
    cy = min(max(cy, ch / 2), 648 - ch / 2)
    box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
    return BENCH.resize((W, H), Image.BICUBIC, box=box)


film = Film("les-lieux-dune-fugue", seconds=TOTAL, boil=3, wobble=1.0)
film.poster_at = ST["door_pm"] + 3.0


@film.picture
def frame(t, ink):
    seg, lt, dur, _ = segment(t, SEGS)
    if seg == "title":
        title_card(ink, "Les Lieux d’une fugue", "three places as they are now · one voice remembering")
    elif seg in ("door_am", "door_pm"):
        facade(ink, 0.0 if seg == "door_am" else 1.0)
    elif seg == "junction":
        junction(ink, lt)
    elif seg == "bench":
        ink.paste(bench_view(lt))
    elif seg == "record":
        ink.fill(NIGHT)
        ink.text((60, 44), "record", "serif", 38, PAGE)
        rows = [("shot", "place_id", "capture", ""),
                ("1", "01 doorway", "08:10 present", ""),
                ("2", "02 junction", "08:40 present", ""),
                ("3", "01 doorway", "18:55 present", "same place_id, later capture_time"),
                ("4", "03 bench", "present", "silence · image-time anchor")]
        for i, r in enumerate(rows):
            y = 110 + i * 28
            for x, c in zip((60, 130, 290, 470), r):
                ink.text((x, y), c, "mono", 14, RULE if i == 0 else PAGE)
        ink.line([(60, 262), (900, 262)], MUTED, 1, rough=False)
        notes = ["recollections · first person, past · interval 'roughly winter', age 'nine or ten'",
                 "bench memory placed over shot 3 by the edit: a juxtaposition, not a claim",
                 "remembered bench = PLACE 03?  inferred · unverified · kept uncertain",
                 "route doorway, junction, station: as remembered, not as proven",
                 "the bell is heard only as remembered (filtered); no bell in the present"]
        for i, n in enumerate(notes):
            ink.text((60, 286 + i * 30), n, "mono", 14, BRASS if "unverified" in n else PAGE)
        fade_edges(ink, lt, dur, 0.4)
        return
    if seg in SLATES:
        tag(ink, (18, 16), SLATES[seg], 12, PAGE, NIGHT, alpha=170)
    for s, a, b, txt in VOICE:
        if s == seg and a <= lt < b:
            al = min(1, (lt - a) / 0.25, (b - lt) / 0.25)
            ink.caption(txt, alpha=al, size=25)
            tag(ink, (W / 2, H - 92), "voice · recollection · roughly winter, age nine or ten", 11, RULE, NIGHT, anchor="ma", alpha=int(150 * al))
    fade_edges(ink, lt, dur, 0.5)


@film.sound
def sound(mix):
    rs = mix.rs
    a = ST["door_am"]
    # present morning: air, distant traffic, a few birds
    mix.wind(a, 10, 0.04)
    mix.room(a, 10, 0.02)
    for k in range(9):
        t0 = a + 0.6 + k * 1.05 + rs.uniform(0, 0.4)
        f = rs.uniform(2600, 3800)
        tt = mix.t(0.12)
        chirp = np.sin(2 * np.pi * np.cumsum(f + 1800 * np.sin(np.pi * tt / 0.12)) / mix.rate) * np.hanning(len(tt))
        mix.add(chirp, t0, 0.05, rs.uniform(-0.7, 0.7))
    j = ST["junction"]
    mix.wind(j, 10, 0.05)
    train_rumble(mix, j + 2.6, 4.4, 0.10, 0.8, -0.8)  # the passing car
    mix.whoosh(j + 4.2, 1.2, 0.08, -0.2)
    p = ST["door_pm"]
    mix.room(p, 13, 0.025, hum=50)
    mix.wind(p, 13, 0.02)
    # the remembered bell: muffled, far, slightly detuned
    bell = Mix(5.0, seed=9)
    bell.bell(0.0, 523, 4.0, 0.6)
    bell.bell(0.9, 494, 3.0, 0.3)
    x = mix.lowpass(bell.L, 1400)
    mix.add(x, p + 5.8, 0.25, 0.3)
    mix.add(mix.lowpass(bell.L, 900), p + 5.8 + 0.09, 0.12, -0.4)
    for i, (s, a0, b0, txt) in enumerate(VOICE):
        mix.murmur(ST[s] + a0 + 0.15, b0 - a0 - 0.4, 0.07, 165, 0.0, seed=40 + i)
    mix.reverb(0.18, 1.1)
    # declared silence over the bench: nothing at all
    b0, b1 = int(ST["bench"] * mix.rate), int((ST["bench"] + 11.0) * mix.rate)
    fade = int(0.4 * mix.rate)
    for ch in (mix.L, mix.R):
        ch[b0 - fade:b0] *= np.linspace(1, 0, fade)
        ch[b0:b1] = 0
        ch[b1:] = 0


if __name__ == "__main__":
    film.render()

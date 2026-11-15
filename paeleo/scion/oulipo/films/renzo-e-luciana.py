"""Renzo e Luciana — two co-workers, one overlapping break, one watched doorway.
CUT 1 plays the original shift; CUT 2 moves Bruno's bell to 12:03 and the safe window closes."""
import math
from kit_cinema_b import *

S_PER_MIN = 5.0
CUT = 26.5            # seconds per cut; clock runs 11:59:42 .. 12:05:00
PRE = 1.5             # local seconds before 12:00
SC = Score([(0, 3.0, "title"), (3.0, 7.5, "rule"), (7.5, 7.5 + CUT, "cut1"), (7.5 + CUT, 10.0 + CUT, "card2"),
            (10.0 + CUT, 10.0 + 2 * CUT, "cut2"), (10.0 + 2 * CUT, 17.0 + 2 * CUT, "ledger")])
film = Film("renzo-e-luciana", seconds=SC.total, boil=6, wobble=1.0, seed=3)
film.poster_at = SC.start("cut1") + PRE + 2.0 * S_PER_MIN

FLOOR = 470
DOOR_X = 600          # partition wall with the doorway the supervisor watches
ADA_HOME, BRUNO_HOME = 165, 350
BENCH_X = 790
ADA_COAT, BRUNO_COAT = (150, 66, 60), (66, 88, 118)

# ---- schedules (minutes after 12:00) ------------------------------------
SCHED = {
    "cut1": {"ada": (0, 3), "bruno": (0, 4), "unwatched": (1, 4), "window": (1, 3)},
    "cut2": {"ada": (0, 3), "bruno": (3, 7), "unwatched": (1, 4), "window": None},
}
# actor x keyframes (minute, x)
PATHS = {
    "cut1": {
        "ada": [(-9, ADA_HOME), (1.0, ADA_HOME), (1.6, BENCH_X - 40), (2.4, BENCH_X - 40), (3.0, ADA_HOME), (9, ADA_HOME)],
        "bruno": [(-9, BRUNO_HOME), (1.15, BRUNO_HOME), (1.7, BENCH_X + 40), (3.45, BENCH_X + 40), (3.9, BRUNO_HOME), (9, BRUNO_HOME)],
    },
    "cut2": {
        "ada": [(-9, ADA_HOME), (1.0, ADA_HOME), (1.6, BENCH_X - 40), (2.9, BENCH_X - 40), (3.5, ADA_HOME), (9, ADA_HOME)],
        "bruno": [(-9, BRUNO_HOME), (3.0, BRUNO_HOME), (3.55, BENCH_X + 10), (9, BENCH_X + 10)],
    },
}
# supervisor gaze: (from, to, target)
GAZE = {
    "cut1": [(-9, 1, "door"), (1, 4, "ledger"), (4, 9, "door")],
    "cut2": [(-9, 1, "door"), (1, 3.2, "ledger"), (3.2, 3.95, "floor"), (3.95, 9, "door")],
}
CAPS = {
    "cut1": [(1.75, 2.05, "ADA", "For us. Open it."), (2.15, 2.4, "BRUNO", "Third floor, over the canal?"),
             (2.4, 2.65, "ADA", "Sunday. Don't be early."), (3.45, 3.8, "", "(the doorway is still unwatched)")],
    "cut2": [(1.8, 2.3, "ADA", "(where is he?)"), (2.35, 2.8, "BRUNO", "(stamping — his bell has not rung)"),
             (2.9, 3.15, "", "she leaves the sealed envelope on the bench"), (3.18, 3.42, "ADA", "Bench."),
             (3.5, 3.9, "SUPERVISOR", "Late from break, Ada. Noted."), (4.0, 4.6, "", "he finds the brass key alone")],
}


def path_x(keys, m):
    for (m0, x0), (m1, x1) in zip(keys, keys[1:]):
        if m0 <= m < m1:
            f = (m - m0) / (m1 - m0)
            return lerp(x0, x1, f), (x1 - x0) / (m1 - m0)
    return keys[-1][1], 0.0


def clock_str(m):
    secs = int(round(m * 60))
    hh, mm, ss = 12, 0, 0
    total = 12 * 3600 + secs
    return f"{total // 3600:02d}:{(total % 3600) // 60:02d}:{total % 60:02d}"


def gaze_at(cut, m):
    for a, b, g in GAZE[cut]:
        if a <= m < b:
            return g
    return "door"


# ---- drawing ------------------------------------------------------------

def set_room(ink, m, cut):
    ink.d.rectangle([0, 112, W, FLOOR], fill=(236, 230, 216))
    ink.d.rectangle([0, FLOOR, W, H], fill=WASH)
    ink.line([(0, FLOOR), (W, FLOOR)], INK, 2.5)
    ink.line([(0, 112), (W, 112)], INK, 2)
    # corridor beyond the partition is cooler
    ink.d.rectangle([DOOR_X + 14, 113, W, FLOOR], fill=(224, 222, 210))
    # partition wall and doorway
    ink.rect(DOOR_X, 113, DOOR_X + 14, 300, fill=(190, 178, 160), color=INK, width=2)
    ink.line([(DOOR_X, 300), (DOOR_X + 14, 300)], INK, 2)
    ink.line([(DOOR_X + 7, 300), (DOOR_X + 7, FLOOR)], MUTED, 1, alpha=90)
    # conveyor at Ada's station
    ink.rect(50, 392, 270, 410, fill=(120, 116, 110), color=INK, width=2)
    for x in (70, 250):
        ink.line([(x, 410), (x, FLOOR)], INK, 2.5)
    off = (m * 60 * 1.6) % 60
    for k in range(5):
        bx = 50 + ((k * 60 + off) % 220)
        ink.rect(bx, 370, bx + 30, 392, fill=(198, 160, 110), color=INK, width=1.6)
    # Bruno's service desk
    ink.rect(290, 380, 420, FLOOR, fill=(170, 140, 104), color=INK, width=2.4)
    ink.label((355, 425), "SERVICE DESK", 11, INK, anchor="mm")
    ink.rect(310, 366, 350, 380, fill=PAGE, color=INK, width=1.4)  # forms
    # wall clock
    clock(ink, 140, 200, 34, 12 + m / 60)
    # supervisor booth
    ink.rect(430, 140, 580, 262, fill=(205, 214, 214), color=INK, width=3)
    ink.hatch(432, 142, 578, 260, gap=11, angle=60, color=(150, 170, 175), width=1, alpha=70)
    ink.line([(430, 262), (430, FLOOR)], INK, 2.5)
    ink.line([(580, 262), (580, FLOOR)], INK, 2.5)
    ink.label((505, 278), "SUPERVISOR", 11, INK, anchor="mm")
    # corner: crates, bench, closed service door
    for (x0, y0) in ((626, 410), (676, 410), (640, 352)):
        ink.rect(x0, y0, x0 + 50, y0 + 58, fill=(184, 150, 100), color=INK, width=2)
        ink.line([(x0, y0), (x0 + 50, y0 + 58)], INK, 1.2, alpha=140)
    bench(ink, BENCH_X, FLOOR, w=170)
    door(ink, 905, FLOOR, w=70, h=160, open_=0.0, sign="SERVICE")
    ink.label((780, 132), "SAFE CORNER · not visible from the booth", 11, MUTED, anchor="mm")


def supervisor(ink, m, cut):
    g = gaze_at(cut, m)
    hx, hy = 505, 205
    ink.rect(470, 228, 540, 262, fill=(60, 58, 60), color=INK, width=2)  # shoulders
    ink.circle(hx, hy, 15, fill=PAGE, color=INK, width=2.4)
    ink.rect(hx - 17, hy - 22, hx + 17, hy - 12, fill=INK, color=INK, width=1)
    if g == "door":
        ink.line([(hx + 13, hy + 1), (hx + 19, hy + 3)], INK, 2.4)
        eye = (hx + 8, hy - 2)
        tgt = [(DOOR_X - 4, 300), (DOOR_X + 22, FLOOR)]
    elif g == "floor":
        ink.line([(hx - 13, hy + 1), (hx - 19, hy + 3)], INK, 2.4)
        eye = (hx - 8, hy - 2)
        tgt = [(110, 340), (300, FLOOR)]
    else:
        ink.line([(hx - 3, hy + 13), (hx + 2, hy + 17)], INK, 2.4)
        ink.rect(486, 240, 526, 252, fill=PAGE, color=INK, width=1.5)  # ledger
        eye = None
    if eye:
        a = 0.5 + 0.15 * math.sin(m * 10)
        ink.d.polygon([eye, tgt[0], tgt[1]], fill=ACCENT + (int(60 * a + 25),))
        for q in tgt:
            ink.line([eye, q], ACCENT, 1.6, alpha=200)
    word = {"door": "watching the doorway", "ledger": "reading the ledger", "floor": "looks at the floor"}[g]
    ink.label((505, 152), word, 11, ACCENT if eye else MUTED, anchor="mm")


def actor(ink, cut, who, m):
    x, v = path_x(PATHS[cut][who], m)
    walking = abs(v) > 1
    facing = 1 if v > 0 else -1
    if not walking:
        facing = -1 if x > DOOR_X else 1
        if who == "ada" and x < DOOR_X:
            facing = -1 if cut == "cut1" or m < 1 else 1
        if who == "bruno" and x < DOOR_X:
            facing = 1
    phase = x / 70.0
    coat = ADA_COAT if who == "ada" else BRUNO_COAT
    pose = "walk" if walking else "stand"
    arm = None
    # particular business
    if not walking:
        if who == "ada" and x < DOOR_X and 0 <= m < 1:
            pose, arm = "reach", 120  # pours coffee from a thermos
        if who == "bruno" and x < DOOR_X and cut == "cut2" and m < 3:
            pose, arm = "reach", 70 + 25 * abs(math.sin(m * 60 * 2.2))  # stamping forms
        if who == "bruno" and x < DOOR_X and cut == "cut1" and 0 <= m < 1:
            pose, arm = "reach", 95  # winding his watch
        if who == "ada" and x > DOOR_X and pose == "stand":
            pose, arm = "reach", 70
        if who == "bruno" and x > DOOR_X and pose == "stand":
            pose, arm = "reach", 75
    s = 1.0
    pts = figure(ink, x, FLOOR - 2, s, pose, phase, facing, coat=coat, arm=arm, hat=False)
    if who == "ada":
        hx, hy = pts["head"]
        ink.arc(hx, hy - 2, 12, math.pi, 2 * math.pi, INK, 5)  # scarf of hair
    ink.label((x, FLOOR + 20), who.upper(), 12, coat, anchor="mm")
    return x, pts


def props(ink, cut, m, ada, bruno):
    (ax, apts), (bx, bpts) = ada, bruno
    hand_a, hand_b = apts["hands"][0], bpts["hands"][0]
    if cut == "cut1":
        if m < 1.85:
            envelope(ink, hand_a[0], hand_a[1], 30, 20)
        elif m < 2.0:
            p = lerp2(hand_a, hand_b, ease(m, 1.85, 2.0))
            envelope(ink, p[0], p[1], 30, 20)
        elif m < 2.4:
            envelope(ink, hand_b[0], hand_b[1] + 6, 30, 20, open_=ease(m, 2.05, 2.15))
            if m > 2.12:
                key_shape(ink, hand_b[0] - 10, hand_b[1] - 22, 0.6, angle=-0.4)
                bench_key_glint(ink, hand_b[0] + 4, hand_b[1] - 30, m * 60)
        elif m < 3.4:
            envelope(ink, BENCH_X + 10, FLOOR - 52, 30, 20, open_=1)
            key_shape(ink, hand_b[0] - 10, hand_b[1] - 6, 0.6, angle=-0.4)
        if 2.32 <= m < 2.42:  # hands touch
            mid = lerp2(hand_a, hand_b, 0.5)
            ink.circle(mid[0], mid[1], 6, fill=ACCENT, color=INK, width=1.5)
    else:
        if m < 2.9:
            envelope(ink, hand_a[0], hand_a[1], 30, 20)
        elif m < 3.62:
            envelope(ink, BENCH_X - 20, FLOOR - 52, 30, 20)
        elif m < 3.85:
            envelope(ink, hand_b[0], hand_b[1] + 6, 30, 20, open_=ease(m, 3.65, 3.78))
        else:
            envelope(ink, BENCH_X - 20, FLOOR - 52, 30, 20, open_=1)
            key_shape(ink, hand_b[0] - 10, hand_b[1] - 20, 0.6, angle=-0.4 + 0.2 * math.sin(m * 40))
            bench_key_glint(ink, hand_b[0] + 4, hand_b[1] - 28, m * 60)
        # the box that falls off the unattended conveyor
        if 3.05 <= m:
            f = ease(m, 3.05, 3.15)
            ink.rect(262, lerp(370, FLOOR - 22, f), 292, lerp(392, FLOOR, f), fill=(198, 160, 110), color=INK, width=1.6)


def header(ink, cut, m, local):
    sc = SCHED[cut]
    ink.d.rectangle([0, 0, W, 111], fill=PAGE)
    ink.line([(0, 111), (W, 111)], RULE, 1.5, rough=False)
    title = "CUT 1 · original shift" if cut == "cut1" else "CUT 2 · late bell"
    ink.label((24, 18), title, 14, ACCENT)
    bars = [("ADA", [sc["ada"]], ADA_COAT), ("BRUNO", [sc["bruno"]], BRUNO_COAT),
            ("DOOR UNWATCHED", [sc["unwatched"]], (120, 150, 120)),
            ("MEETING WINDOW", [sc["window"]] if sc["window"] else [], ACCENT)]
    X = timeline_bar(ink, 24, 690, 34, -0.3, 5.0, bars, now=m, label_w=124, row=12, gap=4, font_size=11)
    for mm in range(0, 6):
        ink.label((X(mm), 102), f"12:0{mm}", 10, MUTED, anchor="mm")
    if not sc["window"]:
        ink.label((X(2.2), 86), "none — breaks no longer overlap", 10, ACCENT, anchor="mm")
    ink.text((830, 46), clock_str(m), "mono", 34, INK, anchor="mm")
    # exposure state, carried forward
    seen = cut == "cut2" and m >= 3.5
    ink.label((830, 84), "EXPOSURE: " + ("Ada late · on record" if seen else "none"), 12, ACCENT if seen else MUTED, anchor="mm")


def play_cut(ink, cut, local):
    m = (local - PRE) / S_PER_MIN
    set_room(ink, m, cut)
    supervisor(ink, m, cut)
    bruno = actor(ink, cut, "bruno", m)
    ada = actor(ink, cut, "ada", m)
    props(ink, cut, m, ada, bruno)
    header(ink, cut, m, local)
    # bell flash
    for b in bells(cut):
        if b[0] <= m < b[0] + 0.12:
            ink.label((140, 250), "BELL", 14, ACCENT, anchor="mm")
            for r in (44, 52):
                ink.arc(140, 200, r, -2.4, -0.7, ACCENT, 2)
    for a, b, who, line in CAPS[cut]:
        if a <= m < b:
            al = min(1, (m - a) / 0.04, (b - m) / 0.04)
            if who:
                speaker_caption(ink, who, line, al, y=H - 30, who_color=ACCENT)
            else:
                ink.caption(line, al, y=H - 30, size=20, color=MUTED)


def bells(cut):
    # (minute, label, pan)
    if cut == "cut1":
        return [(0, "both breaks", 0.0), (3, "Ada back", -0.5), (4, "Bruno back", 0.0)]
    return [(0, "Ada's break", -0.5), (3, "Ada back / Bruno's late break", 0.0)]


@film.picture
def frame(t, ink):
    name, local, a, b = SC.at(t)
    if name == "title":
        section_card(ink, "AFTER RENZO E LUCIANA · MONICELLI / CALVINO 1962", "One break, one doorway", "two co-workers · a private commitment · a supervisor's sightline")
    elif name == "rule":
        ink.fill(PAGE)
        ink.label((W / 2, 70), "THE RULE", 15, ACCENT, anchor="mm")
        ink.text((W / 2, 130), "No private meetings on shift.", "serif", 40, INK, anchor="mm")
        ink.text((W / 2, 180), "The supervisor watches the only doorway to the corner.", "serif", 28, MUTED, anchor="mm")
        lines = ["Ada's break        12:00 – 12:03",
                 "Bruno's break      12:00 – 12:04",
                 "doorway unwatched  12:01 – 12:04   (supervisor at his ledger)",
                 "safe meeting       12:01 – 12:03"]
        for k, s in enumerate(lines):
            ink.text((200, 250 + k * 38), s, "mono", 20, ACCENT if k == 3 else INK)
        ink.label((W / 2, 440), "Ada carries a sealed envelope. Nobody at work may know why.", 14, MUTED, anchor="mm")
    elif name in ("cut1", "cut2"):
        play_cut(ink, name, local)
    elif name == "card2":
        section_card(ink, "CUT 2 · same rule, same people", "The late bell", "Bruno's break moves to 12:03 – 12:07 · overlap with Ada: none")
    else:
        ink.fill(PAGE)
        ink.label((W / 2, 50), "RULE LEDGER", 15, ACCENT, anchor="mm")
        rows = [("", "CUT 1 · original", "CUT 2 · late bell"),
                ("breaks", "overlap [12:00,12:03)", "overlap: none"),
                ("meeting", "12:01:42 – 12:02:24 in corner", "none · a look in the doorway"),
                ("envelope", "hand to hand", "left sealed on the bench"),
                ("brass key", "Bruno, 12:02:10", "Bruno, 12:03:50, alone"),
                ("exposure", "none", "Ada 30 s late · on record"),
                ("service door", "closed", "closed")]
        for k, (a1, b1, c1) in enumerate(rows):
            y = 110 + k * 50
            col = ACCENT if k == 0 else INK
            ink.text((70, y), a1, "mono", 16, MUTED)
            ink.text((230, y), b1, "mono" if k else "serif", 17 if k else 26, col)
            ink.text((580, y), c1, "mono" if k else "serif", 17 if k else 26, col)
            if k:
                ink.line([(60, y - 14), (900, y - 14)], RULE, 1, rough=False)
        ink.label((W / 2, 480), "the small action that kept it: the envelope left where only he would sit", 14, ACCENT, anchor="mm")
    edge_fade(ink, t, a, b, 0.35)


@film.sound
def sound(mix):
    T = SC.total
    for cut in ("cut1", "cut2"):
        c0 = SC.start(cut)

        def at(m):
            return c0 + PRE + m * S_PER_MIN
        # machine room: drone + press thuds every 0.75 s
        mix.drone(c0, CUT, (49, 73.5, 98), gain=0.05, attack=0.6, release=0.6)
        k = 0.0
        while k < CUT - 0.5:
            mix.thud(c0 + k, 60, 0.12, -0.4, 0.25)
            mix.click(c0 + k + 0.37, 0.05, -0.5, 3000)
            k += 0.75
        for m, lab, pan in bells(cut):
            mix.ring(at(m), 1.6, 0.16, pan, 1650)
        # footsteps from the paths
        for who in ("ada", "bruno"):
            keys = PATHS[cut][who]
            for (m0, x0), (m1, x1) in zip(keys, keys[1:]):
                if x0 != x1 and m1 - m0 < 2:
                    mix.steps(at(m0), at(m1), 0.42, 0.14, "stone", (x0 / W) * 2 - 1, (x1 / W) * 2 - 1)
        for a, b, who, line in CAPS[cut]:
            if who in ("ADA", "BRUNO") and not line.startswith("("):
                mix.murmur(at(a) + 0.1, (b - a) * S_PER_MIN - 0.3, 0.07, 210 if who == "ADA" else 120, 0.4, seed=int(a * 100))
            if who == "SUPERVISOR":
                mix.murmur(at(a) + 0.1, (b - a) * S_PER_MIN - 0.3, 0.09, 95, -0.4, seed=7)
        if cut == "cut1":
            mix.click(at(2.12), 0.25, 0.5, 7000)   # key clink
            mix.click(at(2.14), 0.18, 0.5, 9000)
        else:
            for k in range(int(3.0 * S_PER_MIN / 0.55)):
                tt = at(0) + k * 0.55
                if tt < at(3.0):
                    mix.thud(tt, 140, 0.13, -0.1, 0.12)   # Bruno stamping forms
            mix.thud(at(3.12), 90, 0.4, -0.7, 0.3)        # box falls off the conveyor
            mix.click(at(2.92), 0.12, 0.5, 2500)          # envelope set on bench
            mix.click(at(3.8), 0.25, 0.5, 7000)
            mix.click(at(3.82), 0.18, 0.5, 9000)
    mix.bell(SC.start("card2") + 0.2, 392, 2.4, 0.12)
    mix.bell(SC.start("ledger") + 0.3, 523, 3.5, 0.1)
    mix.reverb(0.15, 1.2)


if __name__ == "__main__":
    film.render()

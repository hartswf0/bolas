"""Le Chant du styrène — here, le chant du laiton: a reverse tour from a cast key.

Prologue: the key is left on the station bench (station record, kept apart).
Tour: finished key -> sand mould -> molten brass -> copper and zinc ingots,
i.e. back along the declared process edges of sand-cast yellow brass. Four
original French alexandrines (6+6), carried by a measured, wordless chant of
twelve syllable pulses per line with an audible pause at the caesura. Cut 1
falls in the caesura of line 2; cut 2 falls against it, mid-word, on
syllable 4 of line 3; cut 3 falls on the line break.
"""
import math
from PIL import Image
from kit_cinema_a import *

VELVET = (30, 40, 70)
GLOW = (255, 150, 50)
COPPER = (184, 100, 62)
ZINC = (164, 172, 180)
SAND = (206, 186, 150)

VERSE = [("Cette clé de laiton", "qu’on laisse sur le banc,", "This brass key that one leaves on the bench,"),
         ("Remontons vers le moule,", "un creux de sable blanc.", "let us climb back to the mould, a hollow of white sand."),
         ("Plus tôt, le laiton fond", "et rougit au creuset,", "Earlier, the brass melts and reddens in the crucible,"),
         ("Et plus tôt, zinc et cuivre", "en lingots, sans projet.", "and earlier still, zinc and copper, in ingots, with no purpose.")]
SYL, GAP = 0.32, 0.45

PRE = [("title", 2.4), ("prologue", 4.6)]
TOUR0 = sum(d for _, d in PRE)
LINE_T = []
t = TOUR0 + 0.8
for _ in VERSE:
    on, end = chant_times(t, 12, SYL, 6, GAP)
    LINE_T.append((on, end))
    t = end + 0.9
TOUR_END = LINE_T[-1][1] + 1.6
CUT1 = (LINE_T[1][0][5] + SYL * 1.45 + 0.02 + LINE_T[1][0][6]) / 2  # middle of the L2 caesura pause
CUT2 = LINE_T[2][0][3]                                               # onset of syllable 4 of L3, inside "laiton"
CUT3 = LINE_T[3][0][0] - 0.45                                        # line break before L4
SHOTS = [("finish", TOUR0, CUT1), ("mould", CUT1, CUT2), ("melt", CUT2, CUT3), ("stock", CUT3, TOUR_END)]
CHECK = 6.0
TOTAL = TOUR_END + CHECK


def finish(ink, lt, d):
    ink.fill(VELVET)
    ink.hatch(0, 0, W, H, gap=6, angle=70, color=(40, 52, 88), width=1, alpha=160)
    ang = -0.25 + 0.12 * math.sin(lt * 0.6)
    s = 5.6
    cx, cy = W / 2 - 110 * math.cos(ang), H / 2 - 10 - 110 * math.sin(ang)
    ink.ellipse(W / 2 + 16, H / 2 + 50, 230, 22, fill=(10, 14, 30, 120), color=None)
    key_shape(ink, cx, cy, s, angle=ang, color=(200, 160, 70))
    # a glint travelling down the shank
    g = (lt * 0.35) % 1.0
    gx, gy = cx + math.cos(ang) * s * lerp(8, 40, g), cy + math.sin(ang) * s * lerp(8, 40, g)
    for r, a in ((16, 70), (8, 160), (3, 255)):
        ink.circle(gx, gy - 4, r, fill=(255, 245, 210, a), color=None)


KEYMASK = None


def s_mould(ink, lt, d):
    ink.fill((60, 48, 40))
    ink.rect(150, 70, 810, 470, fill=(120, 88, 56), color=INK, width=4)   # the flask
    ink.rect(180, 100, 780, 440, fill=SAND, color=INK, width=2)
    rs = np.random.RandomState(1)
    for _ in range(500):
        x, y = rs.uniform(185, 775), rs.uniform(105, 435)
        ink.d.point((x, y), fill=(170, 150, 116))
    # the cavity: the key's negative, plus the sprue and runner
    cx, cy, s = 300, 270, 4.4
    key_shape(ink, cx, cy, s, angle=0, color=(120, 100, 76), outline=(90, 74, 58))
    ink.rect(cx + 40 * s, cy - 7, 700, cy + 7, fill=(120, 100, 76), color=(90, 74, 58), width=2)
    ink.circle(710, cy, 26, fill=(120, 100, 76), color=(90, 74, 58), width=2)
    # backward shot: the rough casting comes down out of the air into its hollow
    f = ease(lt, 0.2, d - 0.4)
    lift = 1 - f
    sc = s * (1 + 0.22 * lift)
    ox, oy = -30 * lift, -60 * lift
    if lift > 0.02:
        ink.ellipse(cx + 90 * s / 4.4 + 20, cy + 30, 190 * (1 + lift * 0.3), 30, fill=(0, 0, 0, int(70 * lift)), color=None)
    rough = (176, 140, 70)
    key_shape(ink, cx + ox, cy + oy, sc, angle=0, color=rough)
    ink.rect(cx + ox + 40 * sc, cy + oy - 6, cx + ox + 40 * sc + (700 - cx - 40 * s) * (sc / s), cy + oy + 6, fill=rough, color=INK, width=2)
    ink.circle(cx + ox + 40 * sc + (710 - cx - 40 * s) * (sc / s), cy + oy, 24 * sc / s, fill=rough, color=INK, width=2)
    tag(ink, (18, 16), "STEP 2 · sand mould, opened · shot runs backward (casting returns to its hollow)", 12, PAGE, NIGHT, alpha=190)


def s_melt(ink, lt, d):
    ink.fill((26, 20, 22))
    for r, a in ((380, 30), (260, 40), (160, 50)):
        ink.circle(430, 260, r, fill=(120, 50, 20, a), color=None)
    # mould below with sprue cup
    ink.rect(300, 420, 760, 540, fill=(120, 88, 56), color=INK, width=3)
    ink.rect(320, 420, 740, 440, fill=SAND, color=INK, width=2)
    ink.circle(560, 430, 16, fill=(60, 40, 30), color=INK, width=2)
    # backward shot: the pour retracts and the crucible tilts back upright
    f = ease(lt, 0.2, d - 0.3)
    tilt = lerp(0.85, 0.15, f)
    px, py = 470, 210
    ca, sa = math.cos(tilt), math.sin(tilt)

    def P(x, y):
        return (px + x * ca - y * sa, py + x * sa + y * ca)
    lip = P(70, -70)
    stream_len = max(0.0, 1 - f * 1.25)
    if stream_len > 0:
        end = lerp2(lip, (560, 430), stream_len)
        for w, c in ((20, (255, 120, 30, 90)), (10, GLOW), (4, (255, 230, 150))):
            ink.line([lip, ((lip[0] + end[0]) / 2 + 12, (lip[1] + end[1]) / 2), end], c, w)
    ink.poly([P(-70, -70), P(70, -70), P(52, 80), P(-52, 80)], fill=(70, 62, 60), color=INK, width=3)
    ink.poly([P(-62, -60), P(62, -60), P(58, -30), P(-58, -30)], fill=GLOW, color=(255, 200, 120), width=2)
    ink.line([P(-90, 0), P(-200, 20)], (60, 60, 64), 8)   # tongs
    ink.line([P(90, 0), P(200, 20)], (60, 60, 64), 8)
    rs = np.random.RandomState(int(lt * 12))
    for _ in range(14):
        x, y = lip[0] + rs.normal(0, 60), lip[1] + rs.normal(60, 70)
        ink.circle(x, y, rs.uniform(1, 3), fill=(255, 210, 120), color=None)
    tag(ink, (18, 16), "STEP 3 · molten brass, c. 950 °C · shot runs backward (the pour climbs home)", 12, PAGE, NIGHT, alpha=190)


def s_stock(ink, lt, d):
    ink.fill((52, 56, 60))
    ink.rect(60, 330, 900, 360, fill=(120, 96, 70), color=INK, width=3)
    ink.d.rectangle([60, 360, 900, 540], fill=(70, 62, 56))

    def ingot(x, y, col, lab):
        ink.poly([(x, y), (x + 150, y), (x + 136, y - 46), (x + 14, y - 46)], fill=col, color=INK, width=2.5)
        ink.line([(x + 18, y - 40), (x + 132, y - 40)], mix_color(col, PAGE, 0.4), 2)
        ink.text((x + 75, y - 22), lab, "mono", 16, INK, anchor="mm")
    for i in range(3):
        ingot(110 + i * 165, 330, COPPER, "Cu")
    ingot(140 + 0 * 165, 284, COPPER, "Cu")
    for i in range(2):
        ingot(620 + i * 140, 330, ZINC, "Zn")
    ink.text((W / 2, 392), "raw stock · copper 63 · zinc 37 · yellow brass, as declared", "mono", 14, RULE, anchor="mm")
    tag(ink, (18, 16), "STEP 4 · raw stock · shot runs forward", 12, PAGE, NIGHT, alpha=190)


def prologue(ink, lt):
    ink.fill((214, 206, 190))
    for x in range(0, W, 60):
        ink.line([(x, 0), (x, 330)], RULE, 1, alpha=150)
    ink.d.rectangle([0, 330, W, H], fill=WASH)
    ink.line([(0, 330), (W, 330)], INK, 2)
    door(ink, 790, 330, 90, 170, sign="SERVICE")
    bench(ink, 420, 420, 300)
    down = ease(lt, 0.4, 1.8)
    away = ease(lt, 2.6, 3.6)
    kx, ky = 420, lerp(200, 368, down)
    if lt < 2.4:
        key_shape(ink, kx - 20, ky, 1.2, angle=0.1)
    else:
        key_shape(ink, kx - 20, 368, 1.2, angle=0.1)
    hy = lerp(150, 350, down) - 400 * away
    ink.poly([(kx - 30, -20), (kx + 20, -20), (kx + 24, hy - 30), (kx - 34, hy - 30)], fill=(70, 82, 98), color=INK, width=2)
    ink.ellipse(kx - 5, hy - 12, 26, 22, fill=(224, 196, 170), color=INK, width=2)
    tag(ink, (18, 16), "prologue · station record · the key is left on the bench", 12, PAGE, NIGHT, alpha=190)


def verse_overlay(ink, t):
    for i, ((on, end), (h1, h2, gloss)) in enumerate(zip(LINE_T, VERSE)):
        a, b = on[0] - 0.3, end + 0.5
        if not (a <= t < b):
            continue
        al = min(1, (t - a) / 0.25, (b - t) / 0.25)
        y = H - 74
        ink.d.rectangle([0, y - 34, W, H], fill=NIGHT + (int(200 * al),))
        lit = sum(1 for o in on if o <= t)
        f1 = PAGE if lit >= 1 else RULE
        ink.text((W / 2 - 22, y - 8), h1, "serif", 30, PAGE, anchor="rm", alpha=int(255 * al))
        ink.text((W / 2, y - 8), "/", "serif", 30, (225, 120, 130), anchor="mm", alpha=int(255 * al))
        ink.text((W / 2 + 22, y - 8), h2, "serif", 30, PAGE if lit > 6 else RULE, anchor="lm", alpha=int(255 * al))
        ink.text((W / 2, y + 26), gloss, "mono", 12, RULE, anchor="mm", alpha=int(220 * al))
        # twelve syllable pips, 6 + 6
        for s in range(12):
            x = W / 2 - 150 + s * 24 + (24 if s >= 6 else 0)
            on_ = s < lit
            ink.circle(x, y - 44, 5, fill=(BRASS if on_ else (70, 70, 80)) + (int(255 * al),), color=None, rough=False)
    for c, lab in ((CUT1, "cut on the caesura"), (CUT2, "cut against the caesura · syll. 4, mid-word"), (CUT3, "cut on the line break")):
        if c <= t < c + 1.4:
            tag(ink, (W - 18, 16), lab, 12, PAGE, ACCENT, anchor="ra", alpha=int(230 * (1 - ramp(t, c + 1.0, c + 1.4))))


def check_card(ink, lt):
    ink.fill(NIGHT)
    ink.text((60, 44), "order check", "serif", 36, PAGE)
    ink.text((60, 104), "process edges   raw stock  >  melt  >  mould + pour  >  casting  >  finish", "mono", 14, RULE)
    ink.text((60, 134), "tour            finish, mould, melt, raw stock   (reverse dependency order)   passes", "mono", 14, PAGE)
    ink.text((60, 164), "counter-case    finish, raw stock, casting   skips an edge                 fails", "mono", 14, (236, 160, 170))
    ink.text((60, 194), "shot direction  steps 2 and 3 run backward; that does not change the process order", "mono", 14, RULE)
    for i, ((on, end), (h1, h2, gloss)) in enumerate(zip(LINE_T, VERSE)):
        y = 262 + i * 46
        ink.text((W / 2 - 22, y), h1, "serif", 26, PAGE, anchor="rm")
        ink.text((W / 2, y), "/", "serif", 26, (225, 120, 130), anchor="mm")
        ink.text((W / 2 + 22, y), h2, "serif", 26, PAGE, anchor="lm")
    ink.text((60, 262 + 46 * 1 - 22), "cut 1 in the pause", "mono", 12, (236, 160, 170))
    ink.text((60, 262 + 46 * 2 - 22), "cut 2 inside “laiton”", "mono", 12, (236, 160, 170))
    ink.text((60, 262 + 46 * 3 - 22), "cut 3 at the line break", "mono", 12, (236, 160, 170))
    ink.text((W / 2, H - 30), "alexandrines, 6+6 · L2 moule and L4 cuivre elide across the caesura · metre heard as 12 pulses, not words",
             "mono", 11, RULE, anchor="mm")


film = Film("le-chant-du-styrene", seconds=TOTAL, boil=6, wobble=1.1)
film.poster_at = (CUT2 + CUT3) / 2


@film.picture
def frame(t, ink):
    if t < PRE[0][1]:
        title_card(ink, "Le Chant du laiton", "a reverse tour from a cast key · four alexandrines")
        fade_edges(ink, t, PRE[0][1], 0.3)
        return
    if t < TOUR0:
        prologue(ink, t - PRE[0][1])
        fade_edges(ink, t - PRE[0][1], PRE[1][1], 0.3)
        return
    if t >= TOUR_END:
        check_card(ink, t - TOUR_END)
        fade_edges(ink, t - TOUR_END, CHECK, 0.4)
        return
    for name, a, b in SHOTS:
        if a <= t < b:
            break
    lt, d = t - a, b - a
    {"finish": finish, "mould": s_mould, "melt": s_melt, "stock": s_stock}[name](ink, lt, d)
    if name == "finish":
        tag(ink, (18, 16), "STEP 1 · finished key · held", 12, PAGE, NIGHT, alpha=190)
    verse_overlay(ink, t)
    if t > TOUR_END - 0.4:
        fade_edges(ink, t - (TOUR_END - 0.4), 0.4, 0.4)


@film.sound
def sound(mix):
    p = PRE[0][1]
    mix.room(p, 4.6, 0.03)
    mix.click(p + 1.8, 0.3, 0, 5000, 0.03)  # key on wood
    mix.bell(p + 0.2, 659, 3.0, 0.08, -0.4)
    # bed under the tour: low drone and a slow plucked figure, two notes per hemistich
    mix.drone(TOUR0, TOUR_END - TOUR0, (65.4, 98.0, 130.8), 0.06, attack=1.0, release=1.5)
    for i, (on, end) in enumerate(LINE_T):
        root = (196, 220, 175, 147)[i]
        mix.pluck(on[0], root, 1.6, 0.08, -0.3)
        mix.pluck(on[6], root * 1.5, 1.6, 0.07, 0.3)
        chant(mix, on[0], 12, SYL, 6, GAP, pitch=150 - i * 6, gain=0.13, seed=70 + i)
    # material sounds per step
    a, b = SHOTS[1][1], SHOTS[1][2]
    mix.add(mix.band(mix.noise(b - a), 2000, 8000) * mix.env(int((b - a) * mix.rate), 0.3, 0.01, 1, 0.3), a, 0.025)
    a, b = SHOTS[2][1], SHOTS[2][2]
    roar = mix.lowpass(mix.noise(b - a, "brown"), 600)
    roar /= np.abs(roar).max() + 1e-9
    mix.add(roar * mix.env(len(roar), 0.1, 0.01, 1, 0.3), a, 0.12)
    for k in range(30):
        mix.click(a + mix.rs.uniform(0, b - a), 0.05, mix.rs.uniform(-0.6, 0.6), 7000, 0.01)
    a = SHOTS[3][1]
    for k, f in enumerate((1800, 2400, 1500)):
        mix.note(a + 0.6 + k * 0.5, f, 0.6, 0.05, (k - 1) * 0.5, "sine", 0.002, 0.4, 0.0)
    for c in (CUT1, CUT2, CUT3):
        mix.thud(c, 60, 0.18)
    mix.reverb(0.16, 1.0)


if __name__ == "__main__":
    print(f"cuts at {CUT1:.2f} {CUT2:.2f} {CUT3:.2f}; total {TOTAL:.1f}s")
    film.render()

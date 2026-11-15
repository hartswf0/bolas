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


# ------------------------------------------------------------------ look ---
# Saturated, glossy forms on pure black, lit like studio product shots:
# hard speculars, translucent colour, soft out-of-focus coloured lights.

YEL = (255, 196, 30)
RED_P = (210, 30, 30)
BLUE_P = (30, 70, 230)
BLACK = np.zeros((H, W, 3), np.float32)
GR = dict(sat=1.35, contrast=1.15, pivot=0.35, crush=0.03, blur=0.6, halation=0.3, hal_color=(1.0, 0.8, 0.5), hal_r=14,
          vignette=0.25, grain=0.025, grain_size=1.2)
LT = (-0.45, -0.7, 0.6)


def bokeh(arr, items):
    """Out-of-focus coloured lights: (cx, cy, rx, ry, color, strength)."""
    for cx, cy, rx, ry, col, k in items:
        m = ellipse_mask(W, H, cx, cy, rx, ry, blur=max(rx, ry) * 0.25)
        arr = arr + m[..., None] * np.asarray(col, np.float32) / 255 * k
    return np.clip(arr, 0, 1)


def key_relief(R, x, y, s, angle=0.0, color=YEL, base=0.0, gloss=1.0, trans=0.35):
    ca, sa = math.cos(angle), math.sin(angle)

    def P(px, py):
        return (x + (px * ca - py * sa) * s, y + (px * sa + py * ca) * s)
    n = 20
    ring = [P(9 * math.cos(2 * math.pi * k / n), 9 * math.sin(2 * math.pi * k / n)) for k in range(n + 1)]
    for p0, p1 in zip(ring, ring[1:]):
        R.capsule(p0, p1, 3.4 * s, base=base, color=color, gloss=gloss, trans=trans)
    R.capsule(P(10, 0), P(40, 0), 2.6 * s, base=base, color=color, gloss=gloss, trans=trans)
    for bx0, bx1, by in ((29, 34, 9.5), (35.5, 40, 7.5)):
        R.slab([P(bx0, 1), P(bx1, 1), P(bx1, by), P(bx0, by)], height=4.5 * s, bevel=1.2 * s, base=base, color=color, gloss=gloss, trans=trans)
    R.ellipsoid(*P(40, 0), 3 * s, 3 * s, base=base, color=color, gloss=gloss, trans=trans)


def finish(lt, d):
    bg = bokeh(BLACK, [(W * 0.7, 150, 330, 26, BLUE_P, 0.55), (180, 380, 70, 70, BLUE_P, 0.5), (820, 400, 26, 26, RED_P, 0.6),
                       (110, 120, 18, 18, YEL, 0.4)])
    R = Relief(W, H, bg=bg)
    ang = -0.22 + 0.10 * math.sin(lt * 0.6)
    s = 6.0
    key_relief(R, W / 2 - 120 * math.cos(ang), H / 2 - 30 - 120 * math.sin(ang), s, ang)
    g = (lt * 0.3) % 1.0
    lt_ = (lerp(-0.9, 0.2, g), -0.7, 0.6)
    return R.render(light=lt_, amb=0.25, diff=0.75, spec=1.6, shin=70, smooth=1), "STEP 1 · finished key · held"


KEY_HOLE = None


def s_mould(lt, d):
    """A red glossy mould block holding the key's negative; the casting sinks back into it."""
    bg = bokeh(BLACK, [(820, 90, 60, 60, BLUE_P, 0.4), (120, 470, 30, 30, YEL, 0.3)])
    R = Relief(W, H, bg=bg)
    R.slab([(130, 120), (830, 120), (830, 440), (130, 440)], height=60, bevel=12, base=0, color=RED_P, gloss=0.8, trans=0.2)
    # carve the hollow: a key-shaped negative pressed into the top face
    cav = Relief(W, H)
    cx, cy, s = 290, 280, 4.4
    key_relief(cav, cx, cy, s, 0, color=(255, 255, 255))
    cav.capsule((cx + 40 * s, cy), (700, cy), 2.4 * s)
    cav.ellipsoid(712, cy, 26, 26)
    hole = cav.hit.astype(np.float32)
    zc = np.where(cav.hit, cav.z, 0)
    R.z -= hole * (zc + 8)
    R.col = R.col * (1 - 0.45 * hole[..., None])
    # backward shot: the rough casting (with sprue) comes down out of the air into its hollow
    f = ease(lt, 0.2, d - 0.4)
    lift = 1 - f
    sc = s * (1 + 0.22 * lift)
    ox, oy = -30 * lift, -70 * lift
    k = sc / s
    key_relief(R, cx + ox, cy + oy, sc, 0, color=YEL, base=50 + 120 * lift, trans=0.25)
    R.capsule((cx + ox + 40 * sc, cy + oy), (cx + ox + 40 * sc + (700 - cx - 40 * s) * k, cy + oy), 2.4 * sc, base=50 + 120 * lift, color=YEL, gloss=1.0)
    R.ellipsoid(cx + ox + 40 * sc + (712 - cx - 40 * s) * k, cy + oy, 26 * k, 26 * k, base=50 + 120 * lift, color=YEL, gloss=1.0)
    a = R.render(light=LT, amb=0.25, diff=0.75, spec=1.4, shin=60, smooth=1)
    if lift > 0.02:
        pass
    return a, "STEP 2 · the mould and its hollow · shot runs backward (the casting returns)"


def s_melt(lt, d):
    bg = bokeh(BLACK, [(430, 230, 300, 260, (255, 90, 10), 0.18), (820, 120, 40, 40, BLUE_P, 0.4)])
    R = Relief(W, H, bg=bg)
    R.slab([(300, 430), (760, 430), (760, 540), (300, 540)], height=50, bevel=10, base=0, color=RED_P, gloss=0.8)
    R.dent(560, 440, 22, 12, 20)
    f = ease(lt, 0.2, d - 0.3)
    tilt = lerp(0.85, 0.15, f)
    px, py = 470, 210
    ca, sa = math.cos(tilt), math.sin(tilt)

    def P(x, y):
        return (px + x * ca - y * sa, py + x * sa + y * ca)
    R.slab([P(-70, -70), P(70, -70), P(52, 80), P(-52, 80)], height=70, bevel=20, base=60, color=(40, 50, 120), gloss=1.0)
    R.slab([P(-60, -66), P(60, -66), P(56, -40), P(-56, -40)], height=12, bevel=4, base=125, color=(255, 170, 40), gloss=0.6)
    R.capsule(P(-90, 0), P(-230, 30), 9, base=110, color=(60, 60, 80), gloss=1.0)
    R.capsule(P(90, 0), P(230, 30), 9, base=110, color=(60, 60, 80), gloss=1.0)
    lip = P(70, -70)
    stream = max(0.0, 1 - f * 1.25)
    a = R.render(light=LT, amb=0.25, diff=0.75, spec=1.3, shin=60, smooth=1)
    if stream > 0:
        end = lerp2(lip, (560, 440), stream)
        m = np.zeros((H, W), np.float32)
        for k in range(30):
            q = lerp2(lip, end, k / 29)
            m = np.maximum(m, ellipse_mask(W, H, q[0] + 10 * math.sin(k / 5), q[1], 9, 9))
        a = comp(a, (255, 200, 80), blur_arr(m, 2))
        a = np.clip(a + blur_arr(m, 18)[..., None] * np.array([1.0, 0.45, 0.05]) * 0.8, 0, 1)
    glow = ellipse_mask(W, H, *P(0, -55), 70, 18, blur=20)
    a = np.clip(a + glow[..., None] * np.array([1.0, 0.5, 0.1]) * 0.7, 0, 1)
    rs = np.random.RandomState(int(lt * 12))
    for _ in range(18):
        x, y = lip[0] + rs.normal(0, 70), lip[1] + rs.normal(60, 80)
        a = comp(a, (255, 220, 140), ellipse_mask(W, H, x, y, rs.uniform(1.5, 3.5), rs.uniform(1.5, 3.5)))
    return a, "STEP 3 · molten brass, c. 950 °C · shot runs backward (the pour climbs home)"


def s_stock(lt, d):
    bg = bokeh(BLACK, [(160, 110, 90, 90, BLUE_P, 0.35), (840, 120, 30, 30, YEL, 0.5)])
    R = Relief(W, H, bg=bg)

    def ingot(x, y, col, base=0):
        R.slab([(x, y), (x + 160, y), (x + 144, y - 56), (x + 16, y - 56)], height=50, bevel=12, base=base, color=col, gloss=1.0, trans=0.15)
    for i in range(3):
        ingot(100 + i * 175, 380, (200, 70, 30))
    ingot(140, 322, (200, 70, 30), base=40)
    for i in range(2):
        ingot(630 + i * 160, 380, (110, 140, 235))
    a = R.render(light=LT, amb=0.25, diff=0.8, spec=1.3, shin=50, smooth=1)
    return a, "STEP 4 · raw stock: copper (Cu) and zinc (Zn) · shot runs forward"


def prologue(lt):
    bg = bokeh(BLACK, [(780, 140, 90, 90, BLUE_P, 0.45), (150, 100, 20, 20, YEL, 0.4)])
    R = Relief(W, H, bg=bg)
    # the bench: two red slats on dark legs
    for y0 in (300, 360):
        R.slab([(150, y0), (760, y0 - 6), (760, y0 + 30), (150, y0 + 36)], height=30, bevel=8, base=20, color=RED_P, gloss=0.9)
    for x0 in (190, 700):
        R.capsule((x0, 400), (x0, 520), 10, base=10, color=(50, 50, 70), gloss=1.0)
    down = ease(lt, 0.4, 1.8)
    away = ease(lt, 2.6, 3.6)
    ky = lerp(120, 300, down) if lt < 2.4 else 300
    key_relief(R, 400, ky, 2.2, 0.1, base=60)
    hy = lerp(80, 280, down) - 420 * away
    R.capsule((440, hy - 300), (440, hy - 40), 34, base=90, color=(30, 50, 140), gloss=0.5)
    R.ellipsoid(430, hy - 20, 34, 30, base=100, color=(236, 170, 130), gloss=0.4)
    a = R.render(light=LT, amb=0.25, diff=0.75, spec=1.3, shin=60, smooth=1)
    return a, "prologue · station record · the key is left on the bench"


def verse_overlay(ink, t):
    for i, ((on, end), (h1, h2, gloss)) in enumerate(zip(LINE_T, VERSE)):
        a, b = on[0] - 0.3, end + 0.5
        if not (a <= t < b):
            continue
        al = min(1, (t - a) / 0.25, (b - t) / 0.25)
        y = H - 74
        ink.d.rectangle([0, y - 58, W, H], fill=(0, 0, 0, int(170 * al)))
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
    ink.fill((0, 0, 0))
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


film = Film("le-chant-du-styrene", seconds=TOTAL, boil=0, wobble=0)
film.poster_at = (CUT2 + CUT3) / 2


@film.picture
def frame(t, ink):
    if t < PRE[0][1]:
        title_card(ink, "Le Chant du laiton", "a reverse tour from a cast key · four alexandrines", ground=(0, 0, 0))
        fade_edges(ink, t, PRE[0][1], 0.3)
        return
    if t < TOUR0:
        arr, lab = prologue(t - PRE[0][1])
        put(ink, photo(arr, seed=int(t * FPS), **GR))
        tag(ink, (18, 16), lab, 12, (240, 240, 240), (0, 0, 0), alpha=170)
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
    arr, lab = {"finish": finish, "mould": s_mould, "melt": s_melt, "stock": s_stock}[name](lt, d)
    put(ink, photo(arr, seed=int(t * FPS), **GR))
    tag(ink, (18, 16), lab, 12, (240, 240, 240), (0, 0, 0), alpha=170)
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

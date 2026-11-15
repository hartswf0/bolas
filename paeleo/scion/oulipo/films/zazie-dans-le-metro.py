"""Zazie dans le métro — a 20-second chase for the 4·10 train to the sea.

The girl in the red coat wants the train (setup, with a clean continuity
cut). A jump cut takes her two kilometres in one stride, which lands her at
the back of a queue; a match cut turns the queue into the bars of a locked
gate; the envelope becomes a ticket (gate opens), then a paper dart (the
letter catches the train, she doesn't). The key that falls out stays on the
bench. Then a negative control: the same jump cut with the anchor (red coat,
beret, envelope) removed.
"""
import math
from kit_cinema_a import *

RED = (186, 52, 52)
SKY = (206, 220, 228)
CHASE = 20.0
SEGS = [("title", 2.0), ("chase", CHASE), ("card", 1.6), ("control", 4.2), ("beats", 4.4)]
TOTAL = sum(d for _, d in SEGS)
ST = starts(SEGS)
SHOTS = [("streetA", 0.0, 3.4), ("streetB", 3.4, 5.6), ("front", 5.6, 10.4), ("gate", 10.4, 13.6),
         ("platform", 13.6, 18.0), ("bench", 18.0, 20.0)]
CUTS = {3.4: "continuity cut", 5.6: "jump cut · two kilometres in one stride", 10.4: "match cut · the queue becomes a gate"}
QUEUE_X = [430, 500, 570, 640, 710, 780, 850, 920]


# ------------------------------------------------------------------ look ---
# Warm 1960 colour negative: saturated skin and browns, shallow focus (soft
# backgrounds, sharp figures), halation in the highlights, fine grain.

GIRL_SKIN = (238, 172, 138)
GIRL_HAIR = (118, 62, 30)
BERET = (34, 40, 70)
GR = dict(sat=1.25, contrast=1.12, pivot=0.45, blur=0.9, tone=((1.06, 0.95, 0.82), (1.04, 1.0, 0.92)), halation=0.16,
          hal_color=(1.0, 0.7, 0.45), hal_r=14, vignette=0.42, grain=0.035, grain_size=1.4, gain=1.02)
LT = (-0.5, -0.6, 0.7)
HT = hair_tex(W, H, 7)
_PLATES = {}


def plate(name):
    """Background plates, painted once in soft colour and thrown out of focus."""
    if name in _PLATES:
        return _PLATES[name]
    if name == "streetA":
        a = vgrad(H, W, (236, 222, 196), (200, 180, 150))
        for x, w, c in ((0, 260, (196, 140, 96)), (260, 220, (150, 160, 120)), (480, 260, (214, 176, 130)), (740, 220, (170, 120, 110))):
            a = comp(a, c, poly_mask(W, H, [(x, 40), (x + w, 60), (x + w, 400), (x, 400)]))
            for wx in range(x + 30, x + w - 40, 70):
                for wy in (90, 210):
                    a = comp(a, (60, 50, 44), poly_mask(W, H, [(wx, wy), (wx + 40, wy), (wx + 40, wy + 70), (wx, wy + 70)]))
        a = comp(a, (120, 110, 100), poly_mask(W, H, [(0, 400), (W, 400), (W, H), (0, H)]))
        a = blur_arr(a, 7)
        # the sign, nearer the lens, less blurred
        sg = np.zeros_like(a)
        img = Image.new("RGB", (W, H), (0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rectangle([590, 60, 900, 170], fill=(244, 238, 222))
        d.text((745, 98), "GARE", font=font("serif", 44), fill=(30, 26, 24), anchor="mm")
        d.text((745, 144), "the 4·10 to the sea", font=font("mono", 17), fill=(170, 40, 40), anchor="mm")
        d.polygon([(905, 100), (935, 115), (905, 130)], fill=(244, 238, 222))
        m = poly_mask(W, H, [(590, 60), (900, 60), (938, 115), (900, 170), (590, 170)])
        a = a * (1 - m[..., None]) + blur_arr(np.asarray(img, np.float32) / 255, 1.2) * m[..., None]
        a = comp(a, (60, 56, 52), poly_mask(W, H, [(740, 170), (752, 170), (752, 400), (740, 400)], blur=2))
    elif name == "streetB":
        a = vgrad(H, W, (226, 214, 190), (190, 170, 140))
        for x, w, c in ((0, 300, (130, 140, 160)), (300, 200, (206, 170, 120)), (500, 260, (180, 176, 150)), (760, 200, (160, 120, 100))):
            a = comp(a, c, poly_mask(W, H, [(x, 60), (x + w, 50), (x + w, 330), (x, 330)]))
            for wx in range(x + 30, x + w - 40, 64):
                a = comp(a, (70, 60, 54), poly_mask(W, H, [(wx, 110), (wx + 36, 110), (wx + 36, 170), (wx, 170)]))
        a = comp(a, (178, 168, 152), poly_mask(W, H, [(0, 330), (W, 330), (W, 410), (0, 410)]))
        a = comp(a, (92, 88, 90), poly_mask(W, H, [(0, 410), (W, 410), (W, H), (0, H)]))
        a = comp(a, (60, 110, 170), ellipse_mask(W, H, 700, 200, 24, 24))
        a = blur_arr(a, 5)
    elif name in ("front", "gate"):
        a = vgrad(H, W, (214, 224, 230), (230, 220, 200))
        a = comp(a, (212, 190, 156), poly_mask(W, H, [(200, 20), (W, 20), (W, 330), (200, 330)]))
        if name == "front":
            a = comp(a, (110, 86, 70), poly_mask(W, H, [(420, 330)] + [(640 + 220 * math.cos(math.pi + math.pi * k / 30), 330 + 220 * math.sin(math.pi + math.pi * k / 30)) for k in range(31)]))
            img = Image.new("RGB", (W, H), (212, 190, 156))
            ImageDraw.Draw(img).text((640, 60), "GARE", font=font("serif", 46), fill=(50, 40, 34), anchor="mm")
            a = np.minimum(a, np.asarray(img, np.float32) / 255 + (1 - poly_mask(W, H, [(540, 30), (740, 30), (740, 95), (540, 95)]))[..., None])
        else:
            img = Image.new("RGB", (W, H), (212, 190, 156))
            ImageDraw.Draw(img).text((680, 90), "QUAIS · DÉPARTS", font=font("mono", 26), fill=(50, 40, 34), anchor="mm")
            a = np.minimum(a, np.asarray(img, np.float32) / 255 + (1 - poly_mask(W, H, [(480, 60), (880, 60), (880, 120), (480, 120)]))[..., None])
        a = comp(a, (176, 164, 146), poly_mask(W, H, [(0, 330), (W, 330), (W, H), (0, H)]))
        a = blur_arr(a, 3.5)
    else:  # platform
        a = vgrad(H, W, (216, 206, 186), (180, 170, 150))
        a = comp(a, (130, 96, 76), poly_mask(W, H, [(60, 40), (160, 40), (160, 220), (60, 220)]))
        img = Image.new("RGB", (W, H), (0, 0, 0))
        ImageDraw.Draw(img).text((110, 28), "SERVICE", font=font("mono", 14), fill=(250, 245, 230), anchor="mm")
        a = np.maximum(a, np.asarray(img, np.float32) / 255)
        a = comp(a, (120, 116, 110), poly_mask(W, H, [(0, 220), (W, 220), (W, 370), (0, 370)]))
        a = comp(a, (226, 214, 190), poly_mask(W, H, [(0, 370), (W, 370), (W, H), (0, H)]))
        a = blur_arr(a, 3)
    _PLATES[name] = a
    return a


def envelope_r(R, x, y, w=44, h=30, base=120):
    R.slab([(x - w / 2, y - h / 2), (x + w / 2, y - h / 2), (x + w / 2, y + h / 2), (x - w / 2, y + h / 2)], height=6, bevel=2, base=base, color=(244, 240, 228), gloss=0.2)
    R.ellipsoid(x, y, 6, 6, depth=4, base=base + 6, color=(190, 30, 30), gloss=0.8)


def key_r(R, x, y, s=1.0, angle=0.0, base=40):
    ca, sa = math.cos(angle), math.sin(angle)

    def P(px, py):
        return (x + (px * ca - py * sa) * s, y + (px * sa + py * ca) * s)
    ring = [P(9 * math.cos(2 * math.pi * k / 16), 9 * math.sin(2 * math.pi * k / 16)) for k in range(17)]
    for p0, p1 in zip(ring, ring[1:]):
        R.capsule(p0, p1, 3.2 * s, base=base, color=(214, 168, 70), gloss=1.0)
    R.capsule(P(10, 0), P(40, 0), 2.5 * s, base=base, color=(214, 168, 70), gloss=1.0)
    R.slab([P(30, 1), P(34, 1), P(34, 9), P(30, 9)], height=4 * s, bevel=1, base=base, color=(214, 168, 70), gloss=1.0)
    R.slab([P(36, 1), P(40, 1), P(40, 7), P(36, 7)], height=4 * s, bevel=1, base=base, color=(214, 168, 70), gloss=1.0)


def girl(R, x, y, pose, phase, facing=1, anchor=True, arm=None, env=True, hgt=250):
    coat = (186, 46, 40) if anchor else (60, 90, 140)
    f = person(R, x, y, hgt, phase, pose, facing, coat=coat, trousers=(236, 172, 138), hair=GIRL_HAIR if anchor else (40, 34, 30),
               skin=GIRL_SKIN, hat=BERET if anchor else None, arm=arm, base=60, gloss=0.25, child=True)
    if anchor and env:
        hx, hy = f["hands"][0]
        envelope_r(R, hx + 14 * facing, hy - 8, base=200)
    return f


QUEUE_COATS = [(70, 64, 60), (120, 92, 66), (80, 92, 110), (96, 70, 50), (60, 70, 64), (130, 110, 90), (70, 64, 80), (110, 80, 60)]


def queue(R, t):
    for i, qx in enumerate(QUEUE_X):
        sway = math.sin(t * 2 + i) * 2
        person(R, qx + sway, 450, 330 + 14 * (i % 3), 0, "stand", 1, coat=QUEUE_COATS[i], trousers=(50, 48, 50),
               hat=(40, 36, 34) if i % 2 == 0 else None, base=20)


def gate(R, open_):
    for i, qx in enumerate(QUEUE_X):
        side = -1 if i < 4 else 1
        x = qx + side * 300 * open_ * (0.4 + 0.15 * abs(i - 3.5))
        R.capsule((x, 450), (x, 130), 9, base=40, color=(30, 30, 34), gloss=1.0)
        R.ellipsoid(x, 122, 12, 16, base=40, color=(170, 130, 50), gloss=1.0)
    if open_ < 0.05:
        for y in (190, 400):
            R.capsule((QUEUE_X[0] - 10, y), (QUEUE_X[-1] + 10, y), 7, base=44, color=(30, 30, 34), gloss=1.0)
        R.ellipsoid(675, 300, 16, 16, base=50, color=(200, 160, 60), gloss=1.0)


def train(R, x0):
    for c in range(3):
        x = x0 - c * 340
        R.slab([(x - 320, 120), (x, 120), (x, 350), (x - 320, 350)], height=60, bevel=16, base=0, color=(40, 100, 80), gloss=0.7)
        for w in range(4):
            wx = x - 296 + w * 74
            R.slab([(wx, 150), (wx + 54, 150), (wx + 54, 220), (wx, 220)], height=4, bevel=2, base=60, color=(220, 230, 220), gloss=1.0)
        for wx in (x - 260, x - 60):
            R.ellipsoid(wx, 356, 22, 22, base=40, color=(30, 30, 30), gloss=0.8)


def bench_r(R, x, y, w=260):
    for y0 in (y - 70, y - 40):
        R.slab([(x - w / 2, y0), (x + w / 2, y0), (x + w / 2, y0 + 14), (x - w / 2, y0 + 14)], height=14, bevel=4, base=10, color=(150, 100, 60), gloss=0.3)
    for px in (x - w / 2 + 18, x + w / 2 - 18):
        R.capsule((px, y - 30), (px, y), 6, base=6, color=(40, 36, 34), gloss=0.6)


def chase_arr(t, anchor=True):
    for name, a, b in SHOTS:
        if a <= t < b:
            break
    lt = t - a
    if name == "streetA":
        R = Relief(W, H, bg=plate("streetA"))
        # medium close: she looks up at the sign (the goal), then dashes off right
        go = ease(lt, 1.9, 3.3)
        cx = lerp(330, 1300, go ** 1.4)
        face(R, cx, 250, 0.95, skin=GIRL_SKIN, hair=GIRL_HAIR, look=(0.8, -0.7), turn=0.3, smile=0.4 + 0.4 * ease(lt, 1.0, 1.6), mouth=0.15,
             hair_len=1.25, tex=HT, cap=BERET, collar=(186, 46, 40))
        envelope_r(R, cx + 210, 470 - 40 * ease(lt, 0.5, 1.2), 90, 60, base=260)
        return R.render(light=LT, amb=0.3, diff=0.8, spec=0.3, smooth=4)
    if name == "streetB":
        R = Relief(W, H, bg=plate("streetB"))
        x = lerp(-60, 540, lt / 2.2)
        girl(R, x, 470 - (24 * math.sin(math.pi * ramp(lt, 1.6, 2.2)) if lt > 1.6 else 0), "run", lt * 2.6)
        return R.render(light=LT, amb=0.3, diff=0.8, spec=0.4, smooth=2)
    if name == "front":
        R = Relief(W, H, bg=plate("front"))
        queue(R, lt)
        if lt < 0.5:
            girl(R, lerp(120, 200, lt / 0.5), 470 - 24 * math.sin(math.pi * (0.5 + lt)), "run", 2.6 * (2.2 + lt), anchor=anchor)
        elif lt < 1.4:
            girl(R, lerp(200, 330, ease(lt, 0.5, 1.4)), 470, "run", lt * 2.6, anchor=anchor)
        else:
            tap = (lt * 3) % 1 < 0.5
            girl(R, 340, 470, "stand", 0, anchor=anchor, arm=40 if tap else 10)
        return R.render(light=LT, amb=0.3, diff=0.8, spec=0.4, smooth=2)
    if name == "gate":
        R = Relief(W, H, bg=plate("gate"))
        op = ease(lt, 1.6, 2.4)
        gate(R, op)
        person(R, 905, 460, 360, 0, "reach" if 1.0 <= lt < 2.0 else "stand", -1, coat=(36, 46, 76), trousers=(30, 34, 50), hat=(30, 36, 60), arm=150, base=20)
        if lt < 1.0:
            girl(R, 340, 470, "stand", 0)
        elif lt < 2.6:
            girl(R, 340, 470, "reach", 0, arm=150)
        else:
            girl(R, lerp(340, 1000, ease(lt, 2.6, 3.2)), 470, "run", lt * 2.6)
        return R.render(light=LT, amb=0.3, diff=0.8, spec=0.5, smooth=2)
    if name == "platform":
        R = Relief(W, H, bg=plate("platform"))
        tx = lerp(700, 1900, ease(lt, 0.0, 4.4) * 0.6 + 0.4 * ramp(lt, 0, 4.4) ** 2)
        train(R, tx)
        bench_r(R, 300, 500)
        if lt < 1.4:
            girl(R, lerp(-20, 460, lt / 1.4), 500, "run", lt * 2.8)
        elif lt < 2.4:
            f = girl(R, 460, 500, "reach", 0, arm=100, env=False)
            hx, hy = f["hands"][0]
            fold = ramp(lt, 1.4, 2.0)
            R.slab([(hx, hy - 14 + 8 * fold), (hx + 40 + 10 * fold, hy - 4), (hx, hy + 8 - 6 * fold)], height=4, bevel=1, base=220, color=(244, 240, 228))
            kf = ease(lt, 1.9, 2.3)
            key_r(R, lerp(hx, 300, kf), lerp(hy, 440, kf), 0.9, kf * 2.4, base=200)
        else:
            girl(R, 460, 500, "reach", 0, arm=160, env=False)
            f_ = ramp(lt, 2.4, 3.1)
            dx, dy = lerp(500, 780, f_), lerp(380, 180, f_) - 60 * math.sin(math.pi * f_)
            if f_ < 1:
                R.slab([(dx, dy), (dx - 34, dy - 9), (dx - 26, dy + 7)], height=4, bevel=1, base=220, color=(244, 240, 228))
        if lt >= 2.3:
            key_r(R, 300, 440, 0.9, 2.4, base=30)
        return R.render(light=LT, amb=0.3, diff=0.8, spec=0.6, smooth=2)
    # bench: close-up, she laughs; the key on the bench in the foreground
    R = Relief(W, H, bg=blur_arr(plate("platform"), 6))
    face(R, 470, 230, 1.0, skin=GIRL_SKIN, hair=GIRL_HAIR, look=(0, 0.1), smile=1.0, mouth=0.7 * ease(lt, 0.2, 0.6), eyes_open=0.55,
         hair_len=1.25, tex=HT, cap=BERET, collar=(186, 46, 40))
    R.slab([(0, 470), (W, 470), (W, H), (0, H)], height=30, bevel=6, base=300, color=(150, 100, 60), gloss=0.3)
    key_r(R, 640, 500, 2.2, 2.4, base=340)
    return R.render(light=LT, amb=0.3, diff=0.8, spec=0.5, smooth=4)


def chase(t, ink, anchor=True):
    put(ink, photo(chase_arr(t, anchor), seed=int(t * FPS) + (0 if anchor else 7), **GR))
    for name, a, b in SHOTS:
        if a <= t < b and name == "bench":
            subtitle(ink, "The letter caught the 4·10. The key stayed on the bench.", size=24)


def beats(ink, lt):
    ink.fill(NIGHT)
    ink.text((60, 42), "beat contract", "serif", 36, PAGE)
    rows = ["goal       the 4·10 train · she points at the sign (0:01)",
            "cut 3.4    continuity: exits right, enters left · the clean reference",
            "cut 5.6    jump: two kilometres in a stride  >  she lands at the back of a queue",
            "cut 10.4   match: queue becomes gate bars  >  she needs a way through",
            "prop       envelope: letter  >  ticket (gate opens)  >  dart (letter leaves on the train)",
            "payoff     the route fails; the key falls out and stays on the bench · service door shut",
            "control    same jump with coat, beret and envelope removed: reads as someone else"]
    for i, r in enumerate(rows):
        ink.text((60, 110 + i * 46), r, "mono", 14, PAGE if i != 6 else BRASS)
    fade_edges(ink, lt, 4.4, 0.3)


film = Film("zazie-dans-le-metro", seconds=TOTAL, boil=0, wobble=0)
film.poster_at = ST["chase"] + 19.0


@film.picture
def frame(t, ink):
    seg, lt, dur, _ = segment(t, SEGS)
    if seg == "title":
        title_card(ink, "Zazie dans le métro", "one goal · three places · one envelope, read three ways")
        fade_edges(ink, lt, dur, 0.3)
    elif seg == "chase":
        chase(lt, ink)
        for c, lab in CUTS.items():
            if c <= lt < c + 1.3:
                tag(ink, (W - 18, 16), lab, 12, PAGE, ACCENT, anchor="ra", alpha=200)
    elif seg == "card":
        title_card(ink, "Negative control", "the same jump cut · anchor removed", size=42)
        fade_edges(ink, lt, dur, 0.25)
    elif seg == "control":
        tt = 3.4 + lt * (4.0 / 4.2)
        chase(tt, ink, anchor=tt < 5.6)
        tag(ink, (18, 16), "control · after the jump: blue coat, no beret, no envelope", 12, PAGE, NIGHT, alpha=200)
    else:
        beats(ink, lt)


@film.sound
def sound(mix):
    c = ST["chase"]
    mix.wind(c, CHASE, 0.03)
    # a walking-bass chase figure, faster once she runs
    bass = [110, 131, 147, 165, 147, 131]
    t, k = c + 1.8, 0
    while t < c + 13.6:
        mix.pluck(t, bass[k % len(bass)], 0.5, 0.12, -0.2)
        t += 0.25
        k += 1
    mix.steps(c + 0.0, c + 1.0, 0.33, 0.12, "stone")
    mix.steps(c + 1.8, c + 5.4, 0.19, 0.12, "stone", -0.6, 0.6)
    mix.whoosh(c + 5.45, 0.4, 0.25, 0.5)        # the impossible stride
    mix.thud(c + 5.62, 80, 0.3)
    mix.steps(c + 5.7, c + 7.0, 0.19, 0.12, "stone")
    for k in range(6):                            # impatient foot
        mix.click(c + 7.2 + k * 0.33, 0.12, 0, 1800, 0.04)
    # match cut: a twanged slide, then the guard's whistle and the gate
    tt = mix.t(0.5)
    tw = np.sin(2 * np.pi * np.cumsum(np.linspace(330, 160, len(tt))) / mix.rate) * np.exp(-tt * 6)
    mix.add(tw, c + 10.4, 0.2)
    mix.add(mix.tone(2600, 0.5, vibrato=0.03) * mix.env(int(0.5 * mix.rate), 0.01, 0.1, 0.8, 0.1), c + 11.4, 0.08, 0.5)
    mix.click(c + 12.0, 0.3, 0.3, 2500, 0.08)
    mix.steps(c + 13.0, c + 15.0, 0.19, 0.12, "stone")
    train_rumble(mix, c + 13.4, 5.4, 0.18, -0.2, 0.9, chuff=0.36)
    mix.bell(c + 13.8, 587, 3.0, 0.12)
    paper_flutter(mix, c + 15.0, 0.6, 0.06)
    mix.click(c + 15.9, 0.3, -0.3, 6000, 0.03)    # the key on the bench
    mix.note(c + 15.92, 2400, 0.4, 0.05, -0.3, "sine", 0.002, 0.3, 0.0)
    mix.whoosh(c + 16.0, 0.7, 0.1, 0.4)
    mix.pluck(c + 18.3, 98, 1.6, 0.1)
    mix.pluck(c + 18.6, 92.5, 1.8, 0.1)
    # control: the same cut, same sounds
    k = ST["control"]
    mix.steps(k, k + 2.0, 0.19, 0.12, "stone", -0.6, 0.6)
    mix.whoosh(k + 2.05, 0.4, 0.25, 0.5)
    mix.thud(k + 2.2, 80, 0.3)
    mix.steps(k + 2.3, k + 4.0, 0.19, 0.12, "stone")
    mix.room(ST["beats"], 4.4, 0.02)


if __name__ == "__main__":
    film.render()

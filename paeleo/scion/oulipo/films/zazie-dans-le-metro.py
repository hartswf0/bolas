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


def girl(ink, x, y, pose, phase, facing=1, anchor=True, arm=None, env=True):
    coat = RED if anchor else (70, 96, 130)
    f = figure(ink, x, y, 1.0, pose, phase, facing, coat=coat, arm=arm)
    hx, hy = f["head"]
    if anchor:
        ink.ellipse(hx - 2 * facing, hy - 9, 13, 5, fill=INK, color=INK, width=1)  # beret
        ink.circle(hx - 2 * facing, hy - 15, 2.5, fill=INK, color=INK, width=1)
        if env:
            ex, ey = f["hands"][0]
            envelope(ink, ex + 10 * facing, ey - 4, 32, 21)
            ink.circle(ex + 8 * facing, ey - 3, 3, fill=ACCENT, color=None)
    return f


def street(ink, palette, sign=False, stop=False):
    ink.fill(SKY)
    x = 0
    for k, (w, h, c) in enumerate(palette):
        ink.rect(x, 300 - h, x + w, 300, fill=c, color=INK, width=2.5)
        for wx in range(int(x) + 20, int(x + w) - 30, 50):
            for wy in range(320 - h, 270, 60):
                ink.rect(wx, wy, wx + 26, wy + 34, fill=(230, 232, 226), color=INK, width=1.5)
        x += w
    ink.d.rectangle([0, 300, W, 400], fill=(178, 172, 162))
    ink.line([(0, 300), (W, 300)], INK, 2)
    ink.d.rectangle([0, 400, W, H], fill=(100, 98, 100))
    ink.line([(0, 400), (W, 400)], INK, 3)
    for xx in range(0, W, 120):
        ink.line([(xx, 470), (xx + 60, 470)], PAGE, 4, rough=False)
    if sign:
        ink.line([(250, 400), (250, 220)], INK, 4)
        ink.rect(150, 190, 360, 250, fill=PAGE, color=INK, width=2.5)
        ink.text((255, 208), "GARE", "serif", 24, INK, anchor="mm")
        ink.text((255, 236), "the 4·10 to the sea", "mono", 12, ACCENT, anchor="mm")
        ink.poly([(362, 220), (390, 220), (390, 210), (410, 225), (390, 240), (390, 230), (362, 230)], fill=INK, color=None, rough=False)
        clock(ink, 620, 120, 34, hours=4 + 6 / 60)
    if stop:
        ink.line([(700, 400), (700, 230)], INK, 4)
        ink.circle(700, 220, 22, fill=(60, 110, 160), color=INK, width=2)
        ink.text((700, 220), "BUS", "mono", 11, PAGE, anchor="mm")
        ink.rect(560, 250, 660, 400, fill=(160, 120, 70), color=INK, width=2)  # kiosk
        ink.text((610, 272), "JOURNAUX", "mono", 11, PAGE, anchor="mm")


def front(ink):
    ink.fill(SKY)
    ink.rect(240, 40, 960, 330, fill=(214, 196, 166), color=INK, width=3)
    ink.d.pieslice([420, 90, 860, 520], 180, 360, fill=(120, 100, 84))
    ink.arc(640, 305, 220, math.pi, 2 * math.pi, INK, 3)
    ink.text((640, 70), "GARE", "serif", 34, INK, anchor="mm")
    clock(ink, 360, 150, 40, hours=4 + 9 / 60)
    ink.d.rectangle([0, 330, W, H], fill=(178, 172, 162))
    ink.line([(0, 330), (W, 330)], INK, 2)


def queue(ink, t, shuffle=0.0):
    for i, qx in enumerate(QUEUE_X):
        sway = math.sin(t * 2 + i) * 2
        figure(ink, qx + sway, 440, 1.3 + 0.06 * (i % 3), "stand", facing=1, coat=((60, 60, 64), (98, 84, 70), (70, 82, 98))[i % 3], hat=i % 2 == 0)


def gate(ink, open_):
    ink.fill(SKY)
    ink.d.rectangle([0, 330, W, H], fill=(178, 172, 162))
    ink.line([(0, 330), (W, 330)], INK, 2)
    ink.rect(380, 120, 960, 330, fill=(214, 196, 166), color=INK, width=3)
    ink.text((680, 150), "QUAIS · DÉPARTS", "mono", 18, INK, anchor="mm")
    for i, qx in enumerate(QUEUE_X):
        side = -1 if i < 4 else 1
        x = qx + side * 300 * open_ * (1 if i >= 4 else 1) * (0.4 + 0.15 * abs(i - 3.5))
        ink.line([(x, 440), (x, 270)], INK, 7)
        ink.poly([(x - 8, 272), (x, 250), (x + 8, 272)], fill=INK, color=INK, width=1)
    if open_ < 0.05:
        ink.line([(QUEUE_X[0] - 10, 300), (QUEUE_X[-1] + 10, 300)], INK, 5)
        ink.line([(QUEUE_X[0] - 10, 420), (QUEUE_X[-1] + 10, 420)], INK, 5)
        ink.circle(675, 370, 12, fill=BRASS, color=INK, width=2)


def guard(ink, x, y, salute):
    f = figure(ink, x, y, 1.35, "reach" if salute else "stand", facing=-1, coat=(40, 52, 80), hat=True, arm=150 if salute else None)
    return f


def train(ink, x0):
    for c in range(3):
        x = x0 - c * 330
        ink.rect(x - 310, 210, x, 360, fill=(46, 84, 70), color=INK, width=3)
        for w in range(4):
            wx = x - 290 + w * 72
            ink.rect(wx, 236, wx + 52, 280, fill=(220, 226, 214), color=INK, width=2)
        for wx in (x - 260, x - 60):
            ink.circle(wx, 362, 18, fill=INK, color=INK, width=1)
    ink.poly([(x0, 210), (x0 + 40, 240), (x0 + 40, 360), (x0, 360)], fill=(46, 84, 70), color=INK, width=3)


def platform_bg(ink):
    ink.fill((210, 204, 192))
    for x in range(0, W, 60):
        ink.line([(x, 0), (x, 200)], RULE, 1, alpha=150)
    door(ink, 120, 200, 70, 150, sign="SERVICE")
    ink.d.rectangle([0, 360, W, H], fill=WASH)
    ink.line([(0, 380), (W, 380)], INK, 3)
    ink.d.rectangle([0, 200, W, 360], fill=(150, 146, 140))
    bench(ink, 300, 470, 200)


def chase(t, ink, anchor=True):
    for name, a, b in SHOTS:
        if a <= t < b:
            break
    lt = t - a
    if name == "streetA":
        street(ink, [(240, 150, (196, 160, 120)), (260, 190, (170, 176, 150)), (220, 130, (210, 186, 150)), (300, 170, (180, 150, 140))], sign=True)
        look = ease(lt, 0.9, 1.4)
        if lt < 1.0:
            girl(ink, lerp(40, 200, lt / 1.0), 440, "walk", lt * 1.5)
        elif lt < 1.8:
            girl(ink, 200, 440, "reach", 0, arm=150)  # she points at the sign: the goal
        else:
            girl(ink, lerp(200, 1000, ease(lt, 1.8, 3.4) ** 1.1), 440, "run", lt * 2.6)
    elif name == "streetB":
        street(ink, [(300, 180, (150, 160, 180)), (200, 140, (200, 170, 130)), (260, 200, (190, 190, 170)), (200, 150, (160, 130, 120))], stop=True)
        x = lerp(-40, 520, lt / 2.2)
        pose = "run"
        girl(ink, x, 440 - (18 * math.sin(math.pi * ramp(lt, 1.6, 2.2)) if lt > 1.6 else 0), pose, lt * 2.6, anchor=anchor or True)
    elif name == "front":
        front(ink)
        queue(ink, lt)
        if lt < 0.5:  # lands mid-stride, same pose as she left
            girl(ink, lerp(120, 200, lt / 0.5), 440 - 18 * math.sin(math.pi * (0.5 + lt)), "run", 2.6 * (2.2 + lt), anchor=anchor)
        elif lt < 1.4:
            girl(ink, lerp(200, 330, ease(lt, 0.5, 1.4)), 440, "run", lt * 2.6, anchor=anchor)
        else:
            tap = (lt * 3) % 1 < 0.5
            girl(ink, 340, 440, "stand", 0, anchor=anchor, arm=40 if tap else 10)
        if lt > 1.8:
            ink.text((QUEUE_X[0] + 240, 270), "· · ·", "mono", 22, INK, anchor="mm")
    elif name == "gate":
        op = ease(lt, 1.6, 2.4)
        gate(ink, op)
        guard(ink, 900, 440, 1.0 <= lt < 2.0)
        if lt < 1.0:
            girl(ink, 340, 440, "stand", 0)
        elif lt < 2.6:
            girl(ink, 340, 440, "reach", 0, arm=150)  # the envelope shown as a ticket
            if lt > 1.2:
                tag(ink, (360, 270), "TICKET", 12, INK, PAGE, anchor="ma", alpha=240)
        else:
            girl(ink, lerp(340, 1000, ease(lt, 2.6, 3.2)), 440, "run", lt * 2.6)
    elif name == "platform":
        platform_bg(ink)
        tx = lerp(700, 1900, ease(lt, 0.0, 4.4) * 0.6 + 0.4 * ramp(lt, 0, 4.4) ** 2)
        train(ink, tx)
        if lt < 1.4:
            gx = lerp(-20, 440, lt / 1.4)
            girl(ink, gx, 470, "run", lt * 2.8)
        elif lt < 2.4:  # folds the envelope into a dart; the key drops out
            girl(ink, 440, 470, "reach", 0, arm=100, env=False)
            fold = ramp(lt, 1.4, 2.0)
            ink.poly([(470, 395 - 8 * fold), (500 + 10 * fold, 402), (470, 410 + 6 * (1 - fold))], fill=PAGE, color=INK, width=1.5)
            ky = lerp(400, 420, ease(lt, 1.9, 2.3))
            kx = lerp(462, 330, ease(lt, 1.9, 2.3))
            key_shape(ink, kx, ky, 0.7, angle=ease(lt, 1.9, 2.3) * 2.4)
        else:
            girl(ink, 440, 470, "reach", 0, arm=160, env=False)
            f = ramp(lt, 2.4, 3.1)
            dx, dy = lerp(480, 760, f), lerp(390, 255, f) - 60 * math.sin(math.pi * f)
            if f < 1:
                ink.poly([(dx, dy), (dx - 30, dy - 8), (dx - 24, dy + 6)], fill=PAGE, color=INK, width=1.5)
        if lt >= 2.3:
            key_shape(ink, 310, 420, 0.7, angle=2.4)
    else:
        platform_bg(ink)
        key_shape(ink, 310, 420, 0.7, angle=2.4)
        girl(ink, lerp(400, 640, ease(lt, 0.6, 2.0)), 470, "walk", lt * 1.6, env=False)
        ink.caption("The letter caught the 4·10. The key stayed on the bench.", size=22)


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


film = Film("zazie-dans-le-metro", seconds=TOTAL, boil=10, wobble=1.4)
film.poster_at = ST["chase"] + 11.4


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

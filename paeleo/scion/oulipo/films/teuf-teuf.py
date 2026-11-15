"""Teuf-Teuf — foraged plates and a handmade mechanism.

Each trial opens on a real, public-domain or CC picture of people moving a load that way
(Wikimedia Commons), then the same load is moved in a handmade simulation: same load,
same constant push arrow, same seven-second window, same stage. Drag, loose rollers,
wheels on axles; a counter-check removes the axle; a closing strip compares distances."""
import math
from pathlib import Path
from kit import *
from kit_anim import run, kenburns, load_src, text_ext

film = Film("teuf-teuf", seconds=40.4, boil=0, wobble=0, seed=3)
film.poster_at = 31.0
SRC = Path(__file__).resolve().parent / "sources" / "teuf-teuf"

G = 430            # ground line
PX = 70            # pixels per metre
X0 = 230           # crate front edge at 0 m
CW, CH = 120, 80   # crate
HAND_Y = G - 40    # the push acts at the same height in every trial
PUSH = 7.0         # same push window in every trial
LEAD = 0.3
ROLL_R = 12
WHEEL_R = 20
PLATE = 3.0
TRIAL = 7.6
TITLE = (0.0, 2.6)
SEQ = []           # (start, end, kind, name)
_t = TITLE[1]
for name in ("drag", "roll", "wheel"):
    SEQ.append((_t, _t + PLATE, "plate", name)); _t += PLATE
    SEQ.append((_t, _t + TRIAL, "trial", name)); _t += TRIAL
COUNTER = (_t, _t + 2.6); _t += 2.6
SUMMARY = (_t, 40.4)
SECT = {n: (a, b) for a, b, k, n in SEQ if k == "trial"}

# foraged plates: file, start crop, end crop, caption, credit line (licences in credits/teuf-teuf.json)
PLATES = {
    "drag": ("drag_djehutihotep.jpg", (0, 0, 955, 537), (110, 140, 560, 393),
             "I · Dragging. A colossus lashed to a sledge, hauled by rows of men on ropes.",
             "J. G. Wilkinson (1854) after the el-Bersheh relief · public domain · Wikimedia Commons"),
    "roll": ("roll_nineveh_c.jpg", (0, 0, 1280, 720), (330, 170, 890, 485),
             "II · Rollers. A colossal bull on a sledge, logs laid under it, levers behind.",
             "A. H. Layard, Nineveh and Babylon (1882), Kouyunjik relief · no known restrictions · Commons"),
    "wheel": ("wheel_ljubljana.jpg", (0, 100, 1280, 820), (60, 120, 1220, 772),
              "III · Wheel and axle. A wooden wheel and its axle, from the Ljubljana Marshes.",
              "photo Petar Milošević (2020) · CC BY-SA 4.0 · Wikimedia Commons"),
}
HANDS = ("hands_cueva.jpg", (0, 0, 960, 540), (100, 120, 860, 547),
         "Cueva de las Manos (detail), photo Suzko · CC BY-SA 3.0 · Wikimedia Commons")


# ------------------------------------------------------------- mechanics ---

def drag_m(tau):
    """Stick-slip: nine lurches in the push window, 1.2 m total."""
    tau = clamp(tau, 0, PUSH)
    n = 9
    per = PUSH / n
    k = min(n - 1, int(tau / per))
    f = (tau - k * per) / per
    if tau >= PUSH:
        k, f = n - 1, 1.0
    return 1.2 * (k + smooth((f - 0.45) / 0.35)) / n


def roll_load_m(tau):
    tau = clamp(tau, 0, PUSH)
    if tau < 2.2:
        return 1.5 * smooth(tau / 2.2)
    if tau < 4.8:
        return 1.5
    return 1.5 + 1.5 * smooth((tau - 4.8) / 2.2)


def wheel_m(tau):
    return 8.0 * ease(tau, 0, 6.0)


def roll_sim(tau):
    """Integrate the loose rollers: under the load they travel at half its speed;
    once their centre is behind the crate they stay where they fell. At 2.2–3.8 s the
    pusher carries the rear roller to the front."""
    tau = clamp(tau, 0, PUSH)
    L0 = X0 - CW
    rollers = [dict(x=L0 + r, a=0.0, carried=False) for r in (18, 60, 102)]
    dt = 1 / 240
    s, prevL = 0.0, L0
    picked = None
    while s < tau:
        s = min(tau, s + dt)
        L = X0 - CW + roll_load_m(s) * PX
        dL = L - prevL
        prevL = L
        if picked is None and s >= 2.5:
            picked = min(range(3), key=lambda k: rollers[k]["x"])
            rollers[picked]["carried"] = True
        if picked is not None and s >= 3.8 and rollers[picked]["carried"]:
            rollers[picked]["carried"] = False
            rollers[picked]["x"] = L + CW + 8
        for r in rollers:
            if r["carried"]:
                continue
            rel = r["x"] - L
            if 0 <= rel <= CW:
                r["x"] += dL / 2
                r["a"] += (dL / 2) / ROLL_R
    return rollers, picked


def carry_pose(tau, L):
    """Pusher x (hands) and what it holds during the roller carry."""
    if tau < 2.2 or tau >= 4.8:
        return L, False, 0.0
    if tau < 2.5:   # stoop and pick up
        return L - 6, False, ease(tau, 2.2, 2.45)
    if tau < 3.5:
        return lerp(L - 6, L + CW + 60, ease(tau, 2.5, 3.5)), True, 1.0
    if tau < 3.8:
        return L + CW + 60, tau < 3.8, 1 - ease(tau, 3.5, 3.8)
    return lerp(L + CW + 60, L, ease(tau, 3.8, 4.8)), False, 0.0




# --------------------------------------------------------------- drawing ---
# The trials are a plain working diagram: exact geometry, no texture, no figure.
# The push is a constant red arrow at the same height; contacts are red dots.

def plate(ink, name, lt, dur):
    f, b0, b1, cap, cred = PLATES[name] if name in PLATES else (HANDS[0], HANDS[1], HANDS[2], "", HANDS[3])
    img = kenburns(load_src(SRC / f), b0, b1, lt / dur)
    ink.paste(img)
    ink.d.rectangle([0, H - 78, W, H], fill=(18, 16, 14, 215))
    if cap:
        ink.text((28, H - 70), cap, "serif", 25, PAGE)
    text_ext(ink, (30, H - 32), cred, "sans", 13, RULE)


def stage(ink):
    ink.fill(PAGE)
    ink.d.rectangle([0, G, W, H], fill=WASH)
    ink.line([(0, G), (W, G)], INK, 2.5, rough=False)
    for m in range(0, 9):
        x = X0 + m * PX
        ink.line([(x, G + 8), (x, G + 18)], INK, 1.6, rough=False)
        ink.label((x, G + 22), f"{m} m", 11, MUTED, anchor="ma")
        if m < 8:
            ink.line([(x + PX / 2, G + 8), (x + PX / 2, G + 13)], MUTED, 1, rough=False)
    # the station: bench at 8 m, the service door (closed) on the wall line
    bx = 885
    ink.rect(bx - 75, G - 48, bx + 75, G - 40, fill=(150, 110, 70), color=INK, width=2, rough=False)
    ink.rect(bx - 75, G - 78, bx + 75, G - 70, fill=(150, 110, 70), color=INK, width=2, rough=False)
    for px in (bx - 61, bx + 61):
        ink.line([(px, G - 40), (px, G)], INK, 3, rough=False)
    ink.rect(500, G - 150, 570, G, fill=(196, 186, 170), color=INK, width=2, rough=False)
    ink.circle(558, G - 75, 3.5, fill=BRASS, color=INK, width=1, rough=False)
    ink.label((535, G - 168), "SERVICE", 11, INK, anchor="ma")
    ink.label((X0 + 8 * PX + 6, G + 36), "bench", 11, ACCENT)


def crate(ink, L, bottom, angle=0.0, pivot=None):
    pts = [(L, bottom - CH), (L + CW, bottom - CH), (L + CW, bottom), (L, bottom)]
    env = [(L + CW / 2 - 29, bottom - CH - 25), (L + CW / 2 + 29, bottom - CH - 25), (L + CW / 2 + 29, bottom - CH - 1), (L + CW / 2 - 29, bottom - CH - 1)]
    if angle:
        px, py = pivot
        ca, sa = math.cos(angle), math.sin(angle)
        rot = lambda p: (px + (p[0] - px) * ca - (p[1] - py) * sa, py + (p[0] - px) * sa + (p[1] - py) * ca)
        pts, env = [rot(p) for p in pts], [rot(p) for p in env]
    ink.poly(pts, fill=(196, 160, 112), color=INK, width=2.5, rough=False)
    ink.line([pts[0], pts[2]], (120, 86, 50), 1.6, rough=False)
    ink.line([pts[1], pts[3]], (120, 86, 50), 1.6, rough=False)
    ink.poly(env, fill=PAGE, color=INK, width=2, rough=False)
    ink.line([env[0], lerp2(env[2], env[3], 0.5), env[1]], INK, 1.4, rough=False)
    c = lerp2(env[0], env[2], 0.5)
    ink.circle(c[0], c[1] + 2, 4, fill=ACCENT, color=None, width=0, rough=False)


def roller(ink, x, a, alpha=255, cy=None):
    cy = G - ROLL_R if cy is None else cy
    ink.circle(x, cy, ROLL_R, fill=(176, 132, 82), color=INK, width=2, alpha=alpha, rough=False)
    ink.line([(x, cy), (x + math.cos(a) * ROLL_R, cy + math.sin(a) * ROLL_R)], INK, 1.6, alpha=alpha, rough=False)


def wheel(ink, cx, cy, ang):
    ink.circle(cx, cy, WHEEL_R, fill=PAGE, color=INK, width=3, rough=False)
    for k in range(6):
        a = ang + k * math.pi / 3
        ink.line([(cx, cy), (cx + math.cos(a) * (WHEEL_R - 2), cy + math.sin(a) * (WHEEL_R - 2))], INK, 1.6, rough=False)
    ink.circle(cx, cy, 5, fill=BRASS, color=INK, width=1.5, rough=False)
    ink.circle(cx, G, 3, fill=ACCENT, color=None, width=0, rough=False)


def cart(ink, L, ang):
    by = G - 2 * WHEEL_R - 10
    for rel in (14, 106):
        wheel(ink, L + rel, G - WHEEL_R, ang)
        ink.rect(L + rel - 4, by + 8, L + rel + 4, G - WHEEL_R, fill=INK, color=INK, width=1, rough=False)
    ink.rect(L - 10, by, L + CW + 10, by + 10, fill=(150, 110, 70), color=INK, width=2.5, rough=False)
    return by


def push(ink, L, y, active=True):
    a = 255 if active else 70
    ink.line([(L - 96, y), (L - 14, y)], ACCENT, 5, alpha=a, rough=False)
    ink.poly([(L - 16, y - 9), (L - 1, y), (L - 16, y + 9)], fill=ACCENT, color=None, alpha=a, rough=False)
    ink.label((L - 100, y - 9), "F", 15, ACCENT, anchor="ra", alpha=a)


def header(ink, num, title, sub, tau):
    ink.d.rectangle([0, 0, W, 86], fill=PAPER)
    ink.line([(0, 86), (W, 86)], RULE, 1.5, rough=False)
    ink.text((28, 18), num, "serif", 40, ACCENT)
    ink.text((96, 20), title, "serif", 34, INK)
    ink.label((98, 60), sub, 13, MUTED)
    cx, cy, r = W - 64, 43, 26
    ink.circle(cx, cy, r, fill=WASH, color=INK, width=2, rough=False)
    f = clamp(tau / PUSH)
    if f > 0:
        pts = [(cx, cy)] + [(cx + r * math.sin(2 * math.pi * f * k / 40), cy - r * math.cos(2 * math.pi * f * k / 40)) for k in range(41)]
        ink.d.polygon(pts, fill=ACCENT + (170,))
    ink.label((cx - r - 12, cy - 8), f"push {min(max(tau, 0), PUSH):3.1f}/7 s", 12, INK, anchor="ra")


def readout(ink, m):
    ink.d.rectangle([20, 100, 210, 136], fill=PAPER)
    ink.label((30, 106), f"load moved {m:4.2f} m", 15, INK)


def caption(ink, s, a=1.0):
    ink.caption(s, a, size=21)


@film.picture
def frame(t, ink):
    ink._grain = False
    if t < TITLE[1]:
        plate(ink, "hands", t, TITLE[1])
        ink.d.rectangle([0, 0, W, H - 78], fill=(0, 0, 0, 90))
        ink.text((W / 2, 190), "Teuf-Teuf", "serif", 80, PAGE, anchor="mm")
        ink.label((W / 2, 256), "one load · three ways to move it · same push, same seven seconds", 15, PAGE, anchor="mm")
        return
    for a, b, kind, name in SEQ:
        if a <= t < b:
            if kind == "plate":
                plate(ink, name, t - a, b - a)
            else:
                trial(ink, name, t - a - LEAD)
            fade = min(1, (t - a) / 0.2, (b - t) / 0.2)
            break
    else:
        if t < COUNTER[1]:
            counter(ink, t - COUNTER[0])
            fade = min(1, (t - COUNTER[0]) / 0.2, (COUNTER[1] - t) / 0.2)
        else:
            summary(ink, t - SUMMARY[0])
            fade = min(1, (t - SUMMARY[0]) / 0.25)
    if fade < 1:
        ink.d.rectangle([0, 0, W, H], fill=(0, 0, 0, int(255 * (1 - fade))))


def trial(ink, name, tau):
    stage(ink)
    if name == "drag":
        m = drag_m(tau)
        L = X0 - CW + m * PX
        if m > 0.01:
            for k in range(3):
                ink.line([(X0 - CW + 6, G - 1 - k * 2), (L + CW - 4, G - 1 - k * 2)], MUTED, 1, alpha=120, rough=False)
        crate(ink, L, G)
        f = (clamp(tau, 0, PUSH) % (PUSH / 9)) / (PUSH / 9)
        if 0.45 < f < 0.8 and 0 < tau < PUSH:
            ink.label((L + CW / 2, G - CH - 52), "slip", 13, ACCENT, anchor="ma")
        else:
            ink.line([(L, G - 1), (L + CW, G - 1)], ACCENT, 3, rough=False)
            if 0 < tau < PUSH:
                ink.label((L + CW / 2, G - CH - 52), "stick", 13, MUTED, anchor="ma")
        push(ink, L, HAND_Y, 0 < tau < PUSH)
        header(ink, "I", "Dragging", "contact: the whole base, wood on stone · it sticks, then slips", tau)
        readout(ink, m)
        if tau > PUSH:
            caption(ink, "1.2 m in seven seconds. Most of the push turns into scraping.", ease(tau, PUSH, PUSH + 0.2))
    elif name == "roll":
        m = roll_load_m(tau)
        L = X0 - CW + m * PX
        rollers, picked = roll_sim(max(0, tau))
        for r in rollers:
            if not r["carried"]:
                roller(ink, r["x"], r["a"])
                if 0 <= r["x"] - L <= CW:
                    ink.circle(r["x"], G - 2 * ROLL_R, 2.5, fill=ACCENT, color=None, width=0, rough=False)
                    ink.circle(r["x"], G, 2.5, fill=ACCENT, color=None, width=0, rough=False)
        crate(ink, L, G - 2 * ROLL_R)
        if picked is not None and rollers[picked]["carried"]:
            # the back roller is lifted and carried round to the front (dotted path)
            u = ease(tau, 2.5, 3.8)
            x0, x1 = rollers[picked]["x"], L + CW + 8
            for q in range(0, 21):
                v = q / 20
                ink.circle(lerp(x0, x1, v), G - ROLL_R - math.sin(math.pi * v) * 150, 1.5, fill=MUTED, color=None, width=0, rough=False)
            roller(ink, lerp(x0, x1, u), u * 6, cy=G - ROLL_R - math.sin(math.pi * u) * 150)
        push(ink, L, HAND_Y - 2 * ROLL_R, (0 < tau < 2.2) or (4.8 < tau < PUSH))
        header(ink, "II", "Rolling on loose cylinders", "contact: two lines per roller · rollers travel at half the load's speed", tau)
        readout(ink, m)
        if 2.2 < tau < 4.8:
            caption(ink, "The back roller has fallen out. The push stops while it is carried round.")
        elif tau > 5.6:
            caption(ink, "…and it falls out again. 3.0 m.", ease(tau, 5.6, 5.8))
    else:
        m = wheel_m(tau)
        L = X0 - CW + m * PX
        rl, _ = roll_sim(PUSH)
        for r in rl:
            roller(ink, r["x"], r["a"], alpha=55)
        by = cart(ink, L, m * PX / WHEEL_R)
        crate(ink, L, by)
        push(ink, L, HAND_Y - 2 * WHEEL_R - 10, 0 < tau < 6.0)
        header(ink, "III", "Wheels on axles", "contact: one point per wheel · the axle carries the turn with the load", tau)
        readout(ink, m)
        if 0.6 < tau < 4.2:
            ink.caption("THE WHEEL:  “I’m a roller that was asked to stay.”", ease(tau, 0.6, 0.8) * (1 - ease(tau, 4.0, 4.2)), size=22, color=ACCENT)
        if tau >= 6.0:
            caption(ink, "8 m: the load reaches the bench before the push window closes.", ease(tau, 6.0, 6.2))


def counter_state(tau):
    x = 90 * smooth(clamp(tau / 1.6))
    L0 = X0 - CW
    L = L0 + x
    wx, angs = [], []
    for rel in (14, 106):
        free = L0 + rel + x / 2
        if rel - x / 2 < -10:
            free = L0 + rel + (rel + 10)
        wx.append(free)
        angs.append((free - (L0 + rel)) / WHEEL_R)
    drop = clamp((x - 2 * (14 + 10)) / 18)
    return L, wx, angs, drop


def counter(ink, tau):
    stage(ink)
    L, wx, angs, drop = counter_state(tau)
    by = G - 2 * WHEEL_R - 10
    for k in range(2):
        wheel(ink, wx[k], G - WHEEL_R, angs[k])
        ink.label((wx[k], G - WHEEL_R - 46), "no axle", 11, ACCENT, anchor="ma")
    dy = drop * (G - 10 - by)
    bed = [(L - 10, by), (L + CW + 10, by), (L + CW + 10, by + 10), (L - 10, by + 10)]
    bed = [(x, y + dy * (1 - (x - L + 10) / (CW + 20))) for x, y in bed]
    ink.poly(bed, fill=(150, 110, 70), color=INK, width=2.5, rough=False)
    ang = math.atan2(dy, CW + 20)
    crate(ink, L, by, angle=-ang, pivot=(L + CW + 10, by))
    push(ink, L, HAND_Y - 2 * WHEEL_R - 10 + dy * 0.5, tau < 1.6)
    header(ink, "×", "Counter-check: axle removed", "same cart, same push · the wheels are loose discs under the bed", tau)
    caption(ink, "Without the axle the wheels lag at half speed and drop out: rollers again.", ease(tau, 0.4, 0.6))


def summary(ink, tau):
    ink.fill(PAGE)
    ink.text((W / 2, 46), "Same load · same push · seven seconds", "serif", 34, INK, anchor="mm")
    rows = [("drag", "I  drag", 1.2), ("roll", "II  loose rollers", 3.0), ("wheel", "III  wheels on axles", 8.0)]
    for k, (name, label, m) in enumerate(rows):
        y = 150 + k * 120
        f, b0, b1, *_ = PLATES[name]
        thumb = kenburns(load_src(SRC / f), b1, b1, 1, (176, 99))
        ink.paste(thumb, (24, y - 80))
        ink.label((210, y - 74), label, 15, INK)
        x0 = 330
        ink.line([(x0, y), (x0 + 8 * 60, y)], INK, 2, rough=False)
        for mm in range(9):
            ink.line([(x0 + mm * 60, y), (x0 + mm * 60, y + 8)], MUTED, 1, rough=False)
        grow = ease(tau, 0.2 + k * 0.4, 1.0 + k * 0.4)
        xm = x0 + m * 60 * grow
        ink.d.rectangle([x0, y - 6, xm, y - 2], fill=ACCENT + (200,))
        ink.rect(xm - 40, y - 36, xm, y - 8, fill=(196, 160, 112), color=INK, width=2, rough=False)
        ink.label((xm + 8, y - 28), f"{m * grow:3.1f} m", 15, ACCENT)
    ink.label((W / 2, H - 26), "the plates show how each method was used; the order shown is mechanical, not a dated history", 12, MUTED, anchor="mm")


@film.sound
def sound(mix):
    R = mix.rate
    # title: two engine puffs, "teuf-teuf"
    for k, at in enumerate((0.35, 0.75)):
        x = mix.band(mix.noise(0.16), 120, 900) * np.exp(-np.linspace(0, 7, int(0.16 * R)))
        mix.add(x, at, 0.5, -0.2 + 0.4 * k)
    mix.room(0.0, 40.4, gain=0.02)
    for a, b, kind, name in SEQ:
        if kind == "plate":
            mix.whoosh(a, 0.5, 0.06)

    def speed_env(fn, a, b, rate=200):
        n = int((b - a) * R)
        ts = np.arange(0, b - a, 1 / rate)
        v = np.abs(np.gradient([fn(tt) for tt in ts], 1 / rate))
        return np.interp(np.arange(n) / R, ts, v)

    # I drag: scraping proportional to slip speed
    a = SECT["drag"][0] + LEAD
    v = speed_env(drag_m, 0, PUSH)
    scrape = mix.band(mix.noise(PUSH), 500, 3500) * (v / (v.max() + 1e-9)) ** 0.8
    mix.add(scrape, a, 0.35)
    per = PUSH / 9
    for k in range(9):
        mix.thud(a + k * per + per * 0.8, 90, 0.18)
    # II rollers: wooden rumble while moving, clonk as a roller falls out, steps during the carry
    a = SECT["roll"][0] + LEAD
    v = speed_env(roll_load_m, 0, PUSH)
    rum = mix.lowpass(mix.noise(PUSH, "brown"), 380) * (v / (v.max() + 1e-9))
    mix.add(rum / (np.abs(rum).max() + 1e-9), a, 0.4)
    prev = roll_sim(0)[0]
    out_seen = set()
    for k in range(1, int(PUSH * 40)):
        tt = k / 40
        rs, _ = roll_sim(tt)
        L = X0 - CW + roll_load_m(tt) * PX
        for i, r in enumerate(rs):
            if not r["carried"] and r["x"] - L < 0 and (i, tt > 4.8) not in out_seen:
                out_seen.add((i, tt > 4.8))
                mix.thud(a + tt, 160, 0.4)
                mix.click(a + tt, 0.2, 0, 1500)
    mix.steps(a + 2.5, a + 3.5, 0.25, 0.14, "stone", -0.2, 0.3)
    mix.step(a + 3.75, 0.3, 0.3, "wood")
    mix.steps(a + 3.85, a + 4.8, 0.25, 0.12, "stone", 0.3, -0.2)
    # III wheels: one soft tick per sixth of a revolution, a light rumble, the bell on arrival
    a = SECT["wheel"][0] + LEAD
    last = 0
    for k in range(int(6.0 * 100)):
        tt = k / 100
        spokes = int(wheel_m(tt) * PX / WHEEL_R / (math.pi / 3))
        if spokes > last:
            last = spokes
            mix.click(a + tt, 0.07, 0.1, 2500)
    v = speed_env(wheel_m, 0, 6.0)
    mix.add(mix.lowpass(mix.noise(6.0, "pink"), 250) * (v / v.max()), a, 0.12)
    mix.murmur(a + 0.7, 3.2, gain=0.07, pitch=210, pan=0.1)
    mix.bell(a + 6.0, 660, 3.0, 0.35, 0.4)
    # counter-check: rumble, then the rear drops and grinds
    a = COUNTER[0]
    mix.add(mix.lowpass(mix.noise(1.4, "brown"), 300) * np.hanning(int(1.4 * R)), a, 0.25)
    mix.thud(a + 0.95, 120, 0.5)
    mix.add(mix.band(mix.noise(0.6), 500, 3000) * np.exp(-np.linspace(0, 5, int(0.6 * R))), a + 1.0, 0.18)
    # summary: three plucks, one per bar
    for k, f in enumerate((196, 247, 330)):
        mix.pluck(SUMMARY[0] + 0.6 + 0.4 * k, f, 1.5, 0.16, -0.3 + 0.3 * k)
    mix.reverb(0.12)


if __name__ == "__main__":
    run(film)

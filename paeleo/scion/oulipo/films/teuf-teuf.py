"""Teuf-Teuf — one load, one push, three mechanisms: drag, loose rollers, wheels on axles.
Same stage, same load, same push window (7 s) and same hand height in every trial.
A counter-check removes the axle; a closing strip compares distances."""
import math
from kit import *
from kit_anim import run, hatch_poly

film = Film("teuf-teuf", seconds=30.5, boil=6, wobble=0.9, seed=3)
film.poster_at = 21.0

G = 430            # ground line
PX = 70            # pixels per metre
X0 = 230           # crate front edge at 0 m
CW, CH = 120, 80   # crate
HAND_Y = G - 78    # same hand height in every trial
PUSH = 7.0         # same push window in every trial
TITLE = (0.0, 1.8)
SECT = {"drag": (1.8, 9.4), "roll": (9.4, 17.0), "wheel": (17.0, 24.6)}
LEAD = 0.3
COUNTER = (24.6, 27.2)
SUMMARY = (27.2, 30.5)
ROLL_R = 12
WHEEL_R = 20


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

def backdrop(ink, ghost=None):
    ink.paper()
    ink.d.rectangle([0, 92, W, G], fill=(236, 228, 214))
    for y in range(120, G, 34):
        ink.line([(0, y), (W, y)], RULE, 1, alpha=140, amount=0.4)
    ink.line([(0, 300), (W, 300)], MUTED, 2, alpha=180)
    hatch_poly(ink, [(0, 300), (W, 300), (W, G), (0, G)], gap=9, angle=70, color=MUTED, alpha=45)
    door(ink, 520, G, w=78, h=160, sign="SERVICE")
    clock(ink, 300, 170, 30, 7.25)
    bench(ink, 885, G, w=150)
    ink.d.rectangle([0, G, W, H], fill=WASH)
    ink.line([(0, G), (W, G)], INK, 2.5)
    # ruler
    for m in range(0, 9):
        x = X0 + m * PX
        ink.line([(x, G + 8), (x, G + 18)], INK, 1.6, rough=False)
        ink.label((x, G + 22), f"{m} m", 11, MUTED, anchor="ma")
        if m < 8:
            ink.line([(x + PX / 2, G + 8), (x + PX / 2, G + 13)], MUTED, 1, rough=False)
    ink.label((X0 + 8 * PX + 6, G + 8), "bench", 11, ACCENT)


def crate(ink, L, bottom, tilt=0.0):
    """Crate whose LEFT edge is at L, bottom edge at `bottom`; envelope on top."""
    x0, x1, y1, y0 = L, L + CW, bottom, bottom - CH
    pts = [(x0, y0 + tilt), (x1, y0), (x1, y1), (x0, y1 + tilt)]
    ink.poly(pts, fill=(196, 160, 112), color=INK, width=2.5)
    hatch_poly(ink, pts, gap=7, angle=-60, color=(120, 86, 50), alpha=90)
    for f in (0.33, 0.66):
        ink.line([(x0, lerp(y0, y1, f) + tilt * (1 - f * 0)), (x1, lerp(y0, y1, f))], INK, 1.6)
    ink.line([(x0 + 4, y1 + tilt - 4), (x1 - 4, y0 + 4)], INK, 1.8)
    envelope(ink, L + CW / 2, y0 - 13 + tilt / 2, w=58, h=24)
    ink.circle(L + CW / 2, y0 - 10 + tilt / 2, 4, fill=ACCENT, color=INK, width=1)


def pusher(ink, hx, hy, phase, stoop=0.0, carrying=False, walk=False):
    """Leaning pusher with both hands at (hx, hy). stoop bends to the ground."""
    lean = math.radians(28 if not walk else 6)
    sx, sy = hx - (38 if not walk else 10), hy - 6 - 30 * (1 if walk else 0)
    sy += stoop * 26
    hipx, hipy = sx - math.sin(lean) * 52, sy + math.cos(lean) * 52
    head = (sx + math.sin(lean) * 15 + 3, sy - math.cos(lean) * 15 - 4)
    for sgn in (1, -1):
        a = math.sin(2 * math.pi * phase) * 0.45 * sgn
        footx = hipx + math.sin(a) * 40 - (14 if not walk else 0)
        kx, ky = lerp(hipx, footx, 0.5) + 6, lerp(hipy, G, 0.5) - 4 * abs(a)
        ink.line([(hipx, hipy), (kx, ky), (footx, G - 1)], INK, 3)
        ink.line([(footx, G - 1), (footx + 9, G - 1)], INK, 3)
    ink.line([(sx, sy), (hipx, hipy)], INK, 3.4)
    ink.poly([(sx - 7, sy - 2), (sx + 8, sy + 2), (hipx + 7, hipy + 2), (hipx - 9, hipy - 2)], fill=(92, 104, 120), color=INK, width=2)
    tx, ty = (hx, hy + stoop * 62) if not carrying else (sx + 16, sy + 4)
    for off in (0, 4):
        ex, ey = lerp(sx, tx, 0.5) - 2, lerp(sy, ty, 0.5) + 8
        ink.line([(sx, sy + off), (ex, ey + off), (tx, ty + off)], INK, 2.6)
    ink.circle(head[0], head[1], 10, fill=PAGE, color=INK, width=2.4)
    ink.line([(head[0] - 9, head[1] - 7), (head[0] + 9, head[1] - 9)], INK, 3)   # cap brim
    return (tx, ty)


def roller(ink, x, a, alpha=255, color=(176, 132, 82), dashed=False):
    cy = G - ROLL_R
    ink.circle(x, cy, ROLL_R, fill=color + (alpha,) if alpha < 255 else color, color=INK, width=2, alpha=alpha)
    ink.circle(x, cy, 4, fill=(120, 86, 50), color=INK, width=1, alpha=alpha)
    ink.line([(x, cy), (x + math.cos(a) * ROLL_R, cy + math.sin(a) * ROLL_R)], INK, 1.6, alpha=alpha, rough=False)


def wheel(ink, cx, cy, ang, axle=True):
    ink.circle(cx, cy, WHEEL_R, fill=PAGE, color=INK, width=3)
    for k in range(6):
        a = ang + k * math.pi / 3
        ink.line([(cx, cy), (cx + math.cos(a) * (WHEEL_R - 2), cy + math.sin(a) * (WHEEL_R - 2))], INK, 1.6, rough=False)
    ink.circle(cx, cy, 5, fill=BRASS, color=INK, width=1.5, rough=False)
    ink.circle(cx, G, 3, fill=ACCENT, color=None, width=0, rough=False)  # ground contact


def cart(ink, L, ang, axle=True, rear_drop=0.0, wheel_rel=(14, 106)):
    """Platform whose left edge is L; bed at G-50..G-40."""
    by = G - 2 * WHEEL_R - 10
    drop = rear_drop * (by + 10 - G + 10)  # rear end falls to the ground
    bed = [(L - 10, by - drop * 0 + 0), (L + CW + 10, by), (L + CW + 10, by + 10), (L - 10, by + 10)]
    bed = [(x, y + (-drop) * (1 - (x - L + 10) / (CW + 20))) for x, y in bed]
    for k, rel in enumerate(wheel_rel):
        wx = L + rel if axle else rel
        wheel(ink, wx, G - WHEEL_R, ang if axle else ang[k])
        if axle:
            ink.rect(L + (wheel_rel[k]) - 5, by + 8, L + wheel_rel[k] + 5, G - WHEEL_R, fill=INK, color=INK, width=1, rough=False)
    ink.poly(bed, fill=(150, 110, 70), color=INK, width=2.5)
    return by


def header(ink, num, title, sub, tau):
    ink.d.rectangle([0, 0, W, 86], fill=PAGE)
    ink.line([(0, 86), (W, 86)], RULE, 1.5, rough=False)
    ink.text((28, 18), num, "serif", 40, ACCENT)
    ink.text((88, 20), title, "serif", 34, INK)
    ink.label((90, 60), sub, 13, MUTED)
    # push clock: same 7-second window in every trial
    cx, cy, r = W - 64, 43, 26
    ink.circle(cx, cy, r, fill=WASH, color=INK, width=2, rough=False)
    f = clamp(tau / PUSH)
    if f > 0:
        pts = [(cx, cy)] + [(cx + r * math.sin(2 * math.pi * f * k / 40), cy - r * math.cos(2 * math.pi * f * k / 40)) for k in range(41)]
        ink.d.polygon(pts, fill=ACCENT + (170,))
    ink.label((cx - r - 12, cy - 8), f"push {min(tau, PUSH):3.1f}/7 s", 12, INK, anchor="ra")


def force_arrow(ink, hx, active=True):
    y = HAND_Y - 70
    a = 255 if active else 80
    ink.line([(hx - 92, y), (hx - 30, y)], ACCENT, 4, alpha=a, rough=False)
    ink.poly([(hx - 30, y - 8), (hx - 16, y), (hx - 30, y + 8)], fill=ACCENT, color=None, alpha=a, rough=False)
    ink.label((hx - 100, y - 8), "F", 14, ACCENT, anchor="ra")


def readout(ink, m, best=None):
    ink.d.rectangle([20, 100, 196, 136], fill=PAGE + (230,))
    ink.label((30, 106), f"load moved {m:4.2f} m", 15, INK)


# --------------------------------------------------------------- picture ---

@film.picture
def frame(t, ink):
    if t < TITLE[1]:
        ink.fill(PAPER)
        ink.text((W / 2, 200), "Teuf-Teuf", "serif", 72, INK, anchor="mm")
        ink.label((W / 2, 262), "a demonstration of three mechanisms", 16, MUTED, anchor="mm")
        ink.label((W / 2, 290), "same load · same push · same seven seconds", 14, ACCENT, anchor="mm")
        crate(ink, W / 2 - CW / 2, 430)
        ink.line([(260, 430), (700, 430)], INK, 2)
        return
    for name, (a, b) in SECT.items():
        if a <= t < b:
            tau = t - a - LEAD
            section(ink, name, tau, t)
            fade = min(1, (t - a) / 0.2, (b - t) / 0.2)
            if fade < 1:
                ink.d.rectangle([0, 0, W, H], fill=PAPER + (int(255 * (1 - fade)),))
            return
    if t < COUNTER[1]:
        counter(ink, t - COUNTER[0])
        return
    summary(ink, t - SUMMARY[0])


def section(ink, name, tau, t):
    backdrop(ink)
    if name == "drag":
        m = drag_m(tau)
        L = X0 - CW + m * PX
        # scratch trail and dust at the sliding contact
        if m > 0.01:
            for k in range(3):
                ink.line([(X0 - CW + 6, G - 1 - k * 2), (L + CW - 4, G - 1 - k * 2)], MUTED, 1, alpha=120)
        crate(ink, L, G)
        slipping = 0.45 < ((clamp(tau, 0, PUSH) % (PUSH / 9)) / (PUSH / 9)) < 0.8 and 0 < tau < PUSH
        if slipping:
            for k in range(7):
                ink.circle(L + 8 + k * 16 + ink.j(4), G - 3 + ink.j(2), 2 + ink.rng.random() * 2, fill=MUTED, color=None, alpha=150)
        else:
            ink.line([(L, G - 1), (L + CW, G - 1)], ACCENT, 3, alpha=200)  # whole base in contact
        hx = L
        pusher(ink, hx, HAND_Y, m * 2.2 if tau > 0 else 0)
        force_arrow(ink, hx, 0 < tau < PUSH)
        header(ink, "I", "Dragging", "contact: the whole base, wood on stone · it sticks, then slips", max(0, tau))
        readout(ink, m)
        if tau > PUSH:
            ink.caption("1.2 m in seven seconds. Most of the push turns into scraping.", ease(tau, PUSH, PUSH + 0.2), size=21)
    elif name == "roll":
        m = roll_load_m(tau)
        L = X0 - CW + m * PX
        rollers, picked = roll_sim(max(0, tau))
        for k, r in enumerate(rollers):
            if not r["carried"]:
                roller(ink, r["x"], r["a"])
                rel = r["x"] - L
                if 0 <= rel <= CW:
                    ink.circle(r["x"], G - 2 * ROLL_R, 2.5, fill=ACCENT, color=None, width=0, rough=False)
                    ink.circle(r["x"], G, 2.5, fill=ACCENT, color=None, width=0, rough=False)
        crate(ink, L, G - 2 * ROLL_R)
        hx, carrying, stoop = carry_pose(max(0, tau), L)
        walking = 2.45 < tau < 4.8
        hand = pusher(ink, hx, HAND_Y, (hx - X0) / 60, stoop=stoop, carrying=carrying, walk=walking)
        if carrying:
            r = rollers[picked]
            ink.circle(hand[0] + 4, hand[1] + 8, ROLL_R, fill=(176, 132, 82), color=INK, width=2)
            ink.circle(hand[0] + 4, hand[1] + 8, 4, fill=(120, 86, 50), color=INK, width=1)
        force_arrow(ink, L, (0 < tau < 2.2) or (4.8 < tau < PUSH))
        header(ink, "II", "Rolling on loose cylinders", "contact: two thin lines per roller · rollers travel at half the load's speed", max(0, tau))
        readout(ink, m)
        if 2.2 < tau < 4.8:
            ink.caption("The back roller has fallen out. The load waits while it is carried round.", 1, size=20)
        elif tau > 5.6:
            ink.caption("…and it falls out again. 3.0 m.", ease(tau, 5.6, 5.8), size=21)
    else:
        m = wheel_m(tau)
        L = X0 - CW + m * PX
        # ghosts of the rollers left behind in trial II
        rl, _ = roll_sim(PUSH)
        for r in rl:
            roller(ink, r["x"], r["a"], alpha=60, color=(200, 190, 175))
        ang = m * PX / WHEEL_R
        by = cart(ink, L, ang)
        crate(ink, L, by)
        pusher(ink, L, HAND_Y, m * 0.9, walk=False)
        force_arrow(ink, L, 0 < tau < 6.0)
        header(ink, "III", "Wheels on axles", "contact: one point per wheel · the axle carries the turn with the load", max(0, tau))
        readout(ink, m)
        if 0.6 < tau < 4.2:
            ink.caption("THE WHEEL:  “I’m a roller that was asked to stay.”", ease(tau, 0.6, 0.8) * (1 - ease(tau, 4.0, 4.2)), size=22, color=ACCENT)
        if tau >= 6.0:
            ink.caption("8 m: the load reaches the bench before the push window closes.", ease(tau, 6.0, 6.2), size=20)
            # the bell above the bench
            sw = math.sin((tau - 6.0) * 14) * math.exp(-(tau - 6.0) * 2) * 0.5
            bx, byy = 870, 250
            ink.line([(bx, 226), (bx, 236)], INK, 2)
            ink.poly([(bx - 14 + 10 * sw, byy + 16), (bx + 14 + 10 * sw, byy + 16), (bx + 8, byy - 12), (bx - 8, byy - 12)], fill=BRASS, color=INK, width=2)
        if tau < 6.0:
            bx, byy = 870, 250
            ink.line([(bx, 226), (bx, 236)], INK, 2)
            ink.poly([(bx - 14, byy + 16), (bx + 14, byy + 16), (bx + 8, byy - 12), (bx - 8, byy - 12)], fill=BRASS, color=INK, width=2)


def counter_state(tau):
    x = 90 * smooth(clamp(tau / 1.6))
    wrel0 = (14, 106)
    L0 = X0 - CW
    L = L0 + x
    wx, angs = [], []
    for rel in wrel0:
        # loose wheel: under the bed it travels at half the bed's speed; once behind it stays
        free = L0 + rel + x / 2
        exit_x = None
        if rel - x / 2 < -10:  # passed out of the back
            xe = 2 * (rel + 10)
            free = L0 + rel + xe / 2
        wx.append(free)
        angs.append((free - (L0 + rel)) / WHEEL_R)
    drop = clamp((x - 2 * (14 + 10)) / 18)
    return L, wx, angs, drop


def counter(ink, tau):
    backdrop(ink)
    L, wx, angs, drop = counter_state(tau)
    by = G - 2 * WHEEL_R - 10
    for k in range(2):
        wheel(ink, wx[k], G - WHEEL_R, angs[k])
    bed = [(L - 10, by), (L + CW + 10, by), (L + CW + 10, by + 10), (L - 10, by + 10)]
    dy = drop * (G - 10 - by)
    bed = [(x, y + dy * (1 - (x - L + 10) / (CW + 20))) for x, y in bed]
    ink.poly(bed, fill=(150, 110, 70), color=INK, width=2.5)
    sheet = ink.layer()
    crate(sheet, L, by)
    ang = math.degrees(math.atan2(dy, CW + 20))
    rot = sheet.img.rotate(ang, resample=Image.BICUBIC, center=(L + CW + 10, by))
    ink.paste(rot)
    for k in range(2):
        ink.label((wx[k] - 6, G - WHEEL_R - 40), "×", 22, ACCENT)
    pusher(ink, L, HAND_Y, tau)
    if drop > 0.5:
        for k in range(5):
            ink.circle(L - 6 + k * 6 + ink.j(3), G - 4 + ink.j(2), 2, fill=MUTED, color=None, alpha=160)
    header(ink, "×", "Counter-check: axle removed", "same cart, same push · the wheels are loose discs under the bed", min(PUSH, tau))
    ink.caption("Without the axle the wheels lag at half speed and drop out: rollers again.", ease(tau, 0.4, 0.6), size=20)
    fade = min(1, tau / 0.2, (COUNTER[1] - COUNTER[0] - tau) / 0.2)
    if fade < 1:
        ink.d.rectangle([0, 0, W, H], fill=PAPER + (int(255 * (1 - fade)),))


def summary(ink, tau):
    ink.fill(PAPER)
    ink.text((W / 2, 52), "Same load · same push · seven seconds", "serif", 36, INK, anchor="mm")
    rows = [("I  drag", 1.2), ("II  loose rollers", 3.0), ("III  wheels on axles", 8.0)]
    for k, (name, m) in enumerate(rows):
        y = 150 + k * 112
        x0, x1 = 300, 300 + 8 * 70
        ink.label((40, y - 12), name, 16, INK)
        ink.line([(x0, y), (x1, y)], INK, 2, rough=False)
        for mm in range(9):
            ink.line([(x0 + mm * 70, y), (x0 + mm * 70, y + 8)], MUTED, 1, rough=False)
        grow = ease(tau, 0.2 + k * 0.4, 1.0 + k * 0.4)
        xm = x0 + m * 70 * grow
        ink.d.rectangle([x0, y - 6, xm, y - 2], fill=ACCENT + (200,))
        ink.rect(xm - 44, y - 40, xm, y - 8, fill=(196, 160, 112), color=INK, width=2)
        ink.label((xm + 8, y - 30), f"{m * grow:3.1f} m", 15, ACCENT)
    ink.label((W / 2, H - 30), "order shown is mechanical, not a dated history", 12, MUTED, anchor="mm")
    fade = min(1, tau / 0.25)
    if fade < 1:
        ink.d.rectangle([0, 0, W, H], fill=PAPER + (int(255 * (1 - fade)),))


# ----------------------------------------------------------------- sound ---

@film.sound
def sound(mix):
    R = mix.rate
    # title: two engine puffs, "teuf-teuf"
    for k, at in enumerate((0.35, 0.75)):
        x = mix.band(mix.noise(0.16), 120, 900) * np.exp(-np.linspace(0, 7, int(0.16 * R)))
        mix.add(x, at, 0.5, -0.2 + 0.4 * k)
    mix.room(1.8, 28.5, gain=0.02)

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

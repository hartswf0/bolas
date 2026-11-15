"""La mort en ce jardin — three people, one dry bag, one plank that holds one.
An immaculate wedding shoe (with the brass key in it) floats into reach and the crossing order changes.
Version A: it lands at 9.5 s. Version B: the identical shoe animation lands 5 s earlier."""
import math
from kit_cinema_b import *

VLEN = 24.0
SC = Score([(0, 3.0, "title"), (3.0, 5.5, "cardA"), (5.5, 5.5 + VLEN, "A"), (5.5 + VLEN, 8.0 + VLEN, "cardB"),
            (8.0 + VLEN, 8.0 + 2 * VLEN, "B"), (8.0 + 2 * VLEN, 14.0 + 2 * VLEN, "compare")])
film = Film("la-mort-en-ce-jardin", seconds=SC.total, boil=6, wobble=1.1, seed=9)
film.poster_at = SC.start("A") + 10.6

BANK_Y = 352          # feet level on both banks and on the plank
L_EDGE, R_EDGE = 300, 680
WATER_Y = 372
COATS = {"ezra": (110, 108, 100), "lio": (70, 110, 86), "mara": ACCENT}
BAG = (214, 170, 44)
HEAD = 270            # waiting position at the head of the plank
FAR = {"ezra": 870, "lio": 800, "mara": 735}

# timing (local seconds within a version)
VERS = {
    "A": {"shoe": 9.5, "holder": "lio",
          "cross": [("ezra", 5.0, 9.0), ("mara", 12.0, 16.0), ("lio", 16.5, 20.5)]},
    "B": {"shoe": 4.5, "holder": "ezra",
          "cross": [("lio", 7.5, 11.5), ("mara", 12.0, 16.0), ("ezra", 16.5, 21.0)]},
}
CAPS = {
    "A": [(0.8, 4.0, "EZRA", "Plank takes one. Me, then Lio. Mara and the bag last."),
          (9.8, 11.7, "LIO", "A wedding shoe. Dry. There's a key in it."),
          (11.8, 14.6, "LIO", "Mara, go now, bag up high. I've only one hand."),
          (21.0, 22.4, "MARA", "Whose key is it?"), (22.4, 23.8, "LIO", "Nobody's, yet.")],
    "B": [(0.8, 4.0, "EZRA", "Plank takes one. Me, then Lio. Mara and the bag last."),
          (4.8, 6.6, "EZRA", "A wedding shoe. Dry. There's a key in it."),
          (6.7, 9.6, "EZRA", "Lio, you first. Mara, the bag. I'll come last with this."),
          (21.0, 22.4, "MARA", "Whose key is it?"), (22.4, 23.8, "EZRA", "Nobody's, yet.")],
}
START = {"ezra": HEAD, "lio": 205, "mara": 140}


def queue_positions(v, t):
    """Where each person stands at local time t. People on the near bank shuffle up to the plank head."""
    cr = VERS[v]["cross"]
    pos = {}
    waiting = [n for n, a, b in cr if t < a]
    if t < VERS[v]["shoe"] + 2.0:   # the new order takes effect once it has been decided
        waiting = [n for n in ("ezra", "lio", "mara") if n in waiting]
    for name, a, b in cr:
        if t >= b:
            pos[name] = (FAR[name], "stand", 1)
        elif t >= a:
            f = (t - a) / (b - a)
            x = lerp(HEAD, FAR[name], smooth(f) * 0.15 + f * 0.85)
            pos[name] = (x, "walk", 1)
    # near-bank queue in the order still to go
    slots = [HEAD, 205, 140]
    for k, name in enumerate(waiting):
        target = slots[k]
        pos[name] = (target, "stand", 1)
    # before anything happens, keep the planned standing order
    for name in pos:
        if pos[name][1] == "stand" and t < 5 and pos[name][0] < L_EDGE:
            pos[name] = (START[name], "stand", 1)
    return pos


def smooth_queue(v, t):
    """Ease shuffles in the queue by averaging positions over the last 0.6 s."""
    out = {}
    samples = [queue_positions(v, max(0, t - d)) for d in (0, 0.15, 0.3, 0.45, 0.6)]
    for name in samples[0]:
        xs = [s[name][0] for s in samples]
        x0, pose, facing = samples[0][name]
        if pose == "stand" and x0 < L_EDGE:
            x = sum(xs) / len(xs)
            moving = abs(xs[0] - xs[-1]) > 2
            out[name] = (x, "walk" if moving else "stand", facing)
        else:
            out[name] = samples[0][name]
    return out


def check_plank_law():
    for v in VERS:
        for k in range(int(VLEN * 24)):
            t = k / 24
            on = [n for n, (x, p, f) in queue_positions(v, t).items() if L_EDGE + 5 < x < R_EDGE - 5]
            assert len(on) <= 1, (v, t, on)


check_plank_law()


def shoe_shape(ink, x, y, s=1.0, angle=0.0, glow=True):
    if glow:
        for r, a in ((34, 30), (24, 50)):
            ink.d.ellipse([x - r * s, y - r * s * 0.6, x + r * s, y + r * s * 0.6], fill=(255, 255, 246, a))
    ca, sa = math.cos(angle), math.sin(angle)

    def P(px, py):
        return (x + (px * ca - py * sa) * s, y + (px * sa + py * ca) * s)
    sole = [P(-22, 6), P(18, 6), P(24, 2), P(22, -4), P(4, -2), P(-12, -14), P(-20, -14), P(-24, -2)]
    ink.poly(sole, fill=(255, 254, 248), color=(120, 110, 100), width=1.8)
    ink.line([P(-18, -14), P(-16, 14)], (120, 110, 100), 2.4)  # heel
    ink.line([P(-10, -10), P(10, -2)], (200, 190, 170), 1.2)   # bow line
    ink.circle(*P(-4, -9), 3, fill=(240, 236, 226), color=(150, 140, 120), width=1)


def shoe_track(v, t):
    """Shoe position: identical drift relative to its landing time; then held."""
    ta = VERS[v]["shoe"]
    d = t - ta
    if d < -4.5:
        return None
    if d < 0:
        f = (d + 4.5) / 4.5
        x = lerp(R_EDGE - 20, L_EDGE + 30, smooth(f) * 0.3 + f * 0.7)
        return ("float", x, WATER_Y - 4 + 3 * math.sin(t * 3.1), 0.15 * math.sin(t * 2))
    if d < 0.9:
        return ("float", L_EDGE + 30, WATER_Y - 4 + 3 * math.sin(t * 3.1), 0.15 * math.sin(t * 2))
    return ("held", None, None, 0)


def scene(ink, v, t):
    # tiled underpass wall
    ink.d.rectangle([0, 0, W, BANK_Y], fill=(214, 216, 206))
    for y in range(20, BANK_Y, 34):
        ink.line([(0, y), (W, y)], (190, 194, 184), 1, alpha=200, rough=False)
    for y in range(20, BANK_Y, 68):
        for x in range(0, W, 60):
            ink.line([(x, y), (x, y + 34)], (190, 194, 184), 1, rough=False)
            ink.line([(x + 30, y + 34), (x + 30, y + 68)], (190, 194, 184), 1, rough=False)
    # high-water stain
    ink.d.rectangle([0, 262, W, 270], fill=(170, 160, 130, 90))
    # blocked station exit on the near bank
    door(ink, 80, BANK_Y, w=80, h=170, sign="EXIT")
    for k in range(3):
        ink.line([(36 + k * 6, 210 + k * 30), (124 - k * 6, 240 + k * 30)], (90, 90, 90), 3)
    ink.label((80, 140), "shut · flooded beyond", 11, ACCENT, anchor="mm")
    # stairs up on the far bank
    for k in range(6):
        ink.rect(890 - k * 0 + k * 12, BANK_Y - (k + 1) * 26, W + 10, BANK_Y - k * 26, fill=(200, 196, 182), color=INK, width=1.8)
    ink.d.rectangle([900, 40, W, 160], fill=(252, 246, 220))
    ink.label((925, 30), "OUT", 12, INK, anchor="mm")
    # banks
    ink.rect(-10, BANK_Y, L_EDGE, H + 10, fill=(150, 140, 124), color=INK, width=2.5)
    ink.rect(R_EDGE, BANK_Y, W + 10, H + 10, fill=(150, 140, 124), color=INK, width=2.5)
    # water
    ink.d.rectangle([L_EDGE, WATER_Y, R_EDGE, H], fill=(78, 104, 112))
    for k in range(6):
        y = WATER_Y + 8 + k * 26
        pts = [(x, y + 3 * math.sin(x / 30 + t * 1.6 + k)) for x in range(L_EDGE, R_EDGE + 1, 20)]
        ink.line(pts, (130, 160, 166), 1.5, alpha=160)
    ink.label((490, 512), "deep water", 12, (190, 210, 214), anchor="mm")


def plank(ink, sag):
    pts = [(L_EDGE - 20, BANK_Y + 2)]
    for k in range(1, 10):
        f = k / 10
        pts.append((lerp(L_EDGE - 20, R_EDGE + 20, f), BANK_Y + 2 + sag * math.sin(math.pi * f)))
    pts.append((R_EDGE + 20, BANK_Y + 2))
    ink.line(pts, (120, 84, 52), 8)
    ink.line([(p[0], p[1] + 4) for p in pts], INK, 1.5)


def ledger_panel(ink, v, t, pos):
    holder = VERS[v]["holder"]
    st = shoe_track(v, t)
    on = [n for n, (x, p, f) in pos.items() if L_EDGE + 5 < x < R_EDGE - 5]
    ink.d.rectangle([600, 14, 944, 128], fill=PAGE + (230,))
    ink.rect(600, 14, 944, 128, color=INK, width=1.5, rough=False)
    shoe_holder = "—" if st is None else ("water" if st[0] == "float" else holder.upper())
    rows = [("plank", f"{on[0].upper() if on else 'empty'}  ({len(on)}/1)"),
            ("dry bag", "MARA"),
            ("shoe", shoe_holder),
            ("key", "—" if st is None else "in the shoe")]
    for k, (a, b) in enumerate(rows):
        ink.label((614, 24 + k * 18), a, 12, MUTED)
        ink.label((700, 24 + k * 18), b, 12, ACCENT if (a == "shoe" and st and st[0] == "held") else INK)
    done = [n.upper() for n, a, b in VERS[v]["cross"] if t >= b]
    ink.label((614, 100), "across: " + (" · ".join(done) if done else "nobody"), 12, INK)


def person(ink, name, x, pose, facing, t, v, retrieving):
    arm = None
    y = BANK_Y
    if L_EDGE < x < R_EDGE:
        y = BANK_Y + 2 + 9 * math.sin(math.pi * (x - L_EDGE + 20) / (R_EDGE - L_EDGE + 40))
    holder = VERS[v]["holder"]
    st = shoe_track(v, t)
    holding = name == holder and st and st[0] == "held"
    if retrieving:
        pose, arm = "reach", 20
    elif holding and pose == "stand":
        pose, arm = "reach", 60
    if name == "mara" and pose == "stand" and t > 4:
        pose, arm = "reach", 150   # bag held high
    s = 0.95 if name != "ezra" else 0.9
    pts = figure(ink, x, y, s, pose, x / 55, facing, coat=COATS[name], hat=(name == "ezra"), arm=arm)
    hand = pts["hands"][0]
    if name == "mara":
        bx, by = (hand if (pose == "reach" or x > L_EDGE) else pts["hip"])
        if pose == "walk":
            bx, by = pts["neck"][0] - 6, pts["neck"][1] - 26   # bag held over the head on the plank
        ink.poly([(bx - 14, by - 8), (bx + 14, by - 8), (bx + 12, by + 18), (bx - 12, by + 18)], fill=BAG, color=INK, width=1.8)
        ink.line([(bx - 8, by - 8), (bx - 4, by - 14), (bx + 4, by - 14), (bx + 8, by - 8)], INK, 1.5)
    if holding:
        hx, hy = hand if pose == "reach" else pts["hands"][0]
        shoe_shape(ink, hx + 6, hy + 2, 0.7, glow=True)
        key_shape(ink, hx + 2, hy - 2, 0.35, angle=-0.3)
        bench_key_glint(ink, hx + 14, hy - 6, t)
    ink.label((x, BANK_Y + 20 if not (L_EDGE < x < R_EDGE) else BANK_Y + 26), name.upper(), 11, PAGE, anchor="mm")
    return hand


def play(ink, v, t):
    scene(ink, v, t)
    pos = smooth_queue(v, t)
    on = [n for n, (x, p, f) in pos.items() if L_EDGE + 5 < x < R_EDGE - 5]
    plank(ink, 9 if on else 1.5)
    ta = VERS[v]["shoe"]
    holder = VERS[v]["holder"]
    retrieving_now = ta + 0.0 <= t < ta + 0.9
    st = shoe_track(v, t)
    for name in ("mara", "lio", "ezra"):
        x, pose, facing = pos[name]
        if x > R_EDGE and pose == "stand":
            facing = -1
        person(ink, name, x, pose, facing, t, v, retrieving_now and name == holder)
    if st and st[0] == "float":
        shoe_shape(ink, st[1], st[2], 1.0, st[3])
    ledger_panel(ink, v, t, pos)
    lab = "VERSION A · shoe lands at 9.5 s" if v == "A" else "VERSION B · same shoe, lands at 4.5 s"
    ink.label((20, 18), lab, 13, ACCENT)
    ink.label((20, 36), f"t = {t:4.1f} s", 12, MUTED)
    for a, b, who, line in CAPS[v]:
        if a <= t < b:
            speaker_caption(ink, who, line, min(1, (t - a) / 0.2, (b - t) / 0.2), who_color=COATS[who.lower()] if who.lower() != "ezra" else INK)


@film.picture
def frame(t, ink):
    name, local, a, b = SC.at(t)
    if name == "title":
        section_card(ink, "AFTER LA MORT EN CE JARDIN · BUÑUEL / QUENEAU 1956", "One plank, one bag, one shoe",
                     "the plank holds one person · the shoe is the only impossible thing: it stays dry")
    elif name == "cardA":
        section_card(ink, "VERSION A", "The shoe lands late", "plan: Ezra · Lio · Mara (bag)  ·  shoe in reach at 9.5 s")
    elif name == "cardB":
        section_card(ink, "VERSION B", "The same shoe, 5 s earlier", "identical drift and frames, shifted · in reach at 4.5 s")
    elif name in ("A", "B"):
        play(ink, name, local)
    else:
        ink.fill(PAGE)
        ink.label((W / 2, 60), "CROSSING ORDER · one person on the plank at a time (checked every frame)", 14, ACCENT, anchor="mm")
        rows = [("plan", "Ezra  ·  Lio  ·  Mara + bag", INK),
                ("A · late shoe", "Ezra  ·  Mara + bag  ·  Lio + shoe", INK),
                ("B · early shoe", "Lio  ·  Mara + bag  ·  Ezra + shoe", INK)]
        for k, (lab, order, col) in enumerate(rows):
            y = 150 + k * 80
            ink.text((90, y), lab, "mono", 18, MUTED)
            ink.text((330, y - 8), order, "serif", 36, col)
            ink.line([(80, y + 46), (880, y + 46)], RULE, 1, rough=False)
        ink.text((W / 2, 420), "Whoever lifts the shoe has one hand left, so the bag goes before them.", "serif", 24, INK, anchor="mm")
        ink.label((W / 2, 462), "bag: Mara throughout · shoe: from the water to its finder · key: inside the shoe · exit door: shut", 13, MUTED, anchor="mm")
        shoe_shape(ink, W / 2, 506, 0.9)
    edge_fade(ink, t, a, b, 0.35)


@film.sound
def sound(mix):
    mix.drone(0, 3, (110, 165), gain=0.03)
    for v in ("A", "B"):
        c0 = SC.start(v)
        mix.water(c0, VLEN, 0.12)
        mix.room(c0, VLEN, 0.02)
        mix.bell(c0 + 0.3, 330, 3.0, 0.08, -0.8)  # the station bell, far up the stairs
        for name, a, b in VERS[v]["cross"]:
            mix.steps(c0 + a, c0 + b, 0.5 if name != "ezra" else 0.6, 0.2, "wood", -0.4, 0.5)
            for k in range(int((b - a) / 1.3)):
                t = c0 + a + 0.4 + k * 1.3
                sig = mix.tone(70 + 15 * math.sin(k), 0.35, "saw") * mix.env(int(0.35 * RATE), 0.05, 0.2, 0.2, 0.1)
                mix.add(mix.lowpass(sig, 400), t, 0.08, 0)  # plank creak
        ta = c0 + VERS[v]["shoe"]
        # the shoe's arrival: a small glassy figure, identical in both versions (shifted)
        for k, f in enumerate((1318, 1568, 1976)):
            mix.note(ta - 1.2 + k * 0.18, f, 0.9, 0.05, 0.6, "sine", 0.005, 0.6, 0.0)
        mix.add(mix.band(mix.noise(0.5), 300, 2500) * np.hanning(int(0.5 * RATE)), ta + 0.3, 0.25, -0.3)  # hand in the water
        mix.click(ta + 0.8, 0.18, -0.3, 8000)
        for a, b, who, line in CAPS[v]:
            mix.murmur(c0 + a + 0.1, b - a - 0.3, 0.07, {"EZRA": 105, "LIO": 140, "MARA": 210}[who], -0.2, seed=int(a * 10))
    mix.bell(SC.start("compare") + 0.2, 392, 4.0, 0.1)
    mix.reverb(0.3, 1.4)


if __name__ == "__main__":
    film.render()

"""Mauro Martino, Exercises in Style — controlled variation with a coded procedural generator.
generate(manifest, seed, t) draws the bus version of the station seed. Baseline, then two deltas
(camera: overhead; treatment: cyanotype), each with the same two seeds, side by side at equal size."""
import math
import random as _random
from PIL import Image
from kit_cinema_b import *

CLIP = 6.6                      # every clip has the same duration
CW, CH = 440, 248               # every clip has the same display size
SEEDS = (11, 29)
BASE = {"scene": "bus-seed", "camera": "side", "treatment": "ink"}
CONDS = [("baseline", {}), ("delta camera", {"camera": "overhead"}), ("delta treatment", {"treatment": "cyanotype"})]
SEC = 8.6
SC = Score([(0, 3.5, "title")] + [(3.5 + k * SEC, 3.5 + (k + 1) * SEC, f"c{k}") for k in range(3)]
           + [(3.5 + 3 * SEC, 3.5 + 3 * SEC + 8.0, "grid"), (11.5 + 3 * SEC, 18.0 + 3 * SEC, "report")])
film = Film("mauro-martino-exercises-in-style", seconds=SC.total, boil=6, wobble=1.0, seed=2)
film.poster_at = SC.start("grid") + 3.5
CLIP_AT = 1.0                   # clip starts this long into each section

# protected anchors: fixed times, independent of seed and condition
ANCHORS = [("A1", "boards", 0.4), ("A2", "bell", 2.2), ("A3", "opens envelope", 2.9),
           ("A4", "key left on seat", 4.0), ("A5", "alights", 5.4), ("A6", "service door shut", 6.5)]
SEAT_X, KEY_X = 252, 280


def manifest(delta):
    m = dict(BASE)
    m.update(delta)
    return m


def extras(seed):
    """Everything the seed controls: other passengers, the street, the visitor's coat."""
    r = _random.Random(seed)
    seats = [100, 175, 330]
    r.shuffle(seats)
    n = r.randint(2, 3)
    sitters = [(seats[k], r.choice([(70, 96, 120), (120, 96, 70), (90, 110, 80), (140, 80, 90)])) for k in range(n)]
    stander = r.uniform(150, 340) if r.random() < 0.75 else None
    street = [r.uniform(0, 900) for _ in range(5)]
    coat = r.choice([(96, 60, 70), (60, 70, 100), (100, 84, 50)])
    rain = r.random() < 0.4
    return {"sitters": sitters, "stander": stander, "stander_coat": (80, 80, 90), "street": street, "coat": coat, "rain": rain}


def visitor_state(t):
    """(x, pose, arm, action) for the visitor; identical in every condition."""
    if t < 0.4:
        return None
    if t < 1.2:
        return (lerp(432, 390, ramp(t, 0.4, 1.2)), "walk", None, "")
    if t < 1.9:
        return (lerp(390, SEAT_X, ramp(t, 1.2, 1.9)), "walk", None, "")
    if t < 4.4:
        arm = 170 if 2.0 <= t < 2.4 else (80 if 2.6 <= t < 4.2 else 40)
        return (SEAT_X, "sit", arm, "sit")
    if t < 5.1:
        return (lerp(SEAT_X, 390, ramp(t, 4.4, 5.1)), "walk", None, "")
    if t < 5.9:
        return (lerp(390, 470, ramp(t, 5.1, 5.9)), "walk", None, "")
    return None


def bus_offset(t):
    """Street scroll: stopped, moving, stopped."""
    if t < 1.6:
        return 0.0
    if t < 4.6:
        return (t - 1.6) * 120 - 30 * smooth(ramp(t, 1.6, 2.4)) + 30 * smooth(ramp(t, 3.8, 4.6))
    return 3.0 * 120


def treat(name, c=None):
    """Treatment palettes."""
    return c


class Palette:
    def __init__(self, treatment):
        self.t = treatment
        if treatment == "ink":
            self.ground, self.line, self.body, self.glass, self.floor, self.key = (236, 230, 214), INK, (206, 176, 96), (214, 226, 226), (150, 140, 124), BRASS
            self.seat, self.road = (130, 90, 70), (120, 116, 110)
        else:
            self.ground, self.line, self.body, self.glass, self.floor, self.key = (26, 56, 100), (228, 238, 244), (44, 90, 142), (34, 72, 120), (30, 66, 112), (246, 232, 170)
            self.seat, self.road = (70, 120, 170), (20, 46, 84)

    def coat(self, c):
        if self.t == "ink":
            return c
        lum = (0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]) / 255
        return mix_color((60, 110, 160), (200, 220, 236), lum * 1.4)


def generate(m, seed, t, frame_index):
    """Draw one frame of one clip. Returns (image, coverage dict)."""
    P = Palette(m["treatment"])
    ink = Ink(t, frame_index, (CW, CH), boil=6, wobble=0.9, seed=seed)
    ink.d.rectangle([0, 0, CW, CH], fill=P.ground)
    X = extras(seed)
    cov = {}
    if m["camera"] == "side":
        cov = side_view(ink, P, X, t)
    else:
        cov = overhead_view(ink, P, X, t)
    if m["treatment"] == "cyanotype":
        # a printed, sun-exposed look: horizontal exposure lines
        for y in range(0, CH, 4):
            ink.d.line([(0, y), (CW, y)], fill=(255, 255, 255, 10))
    ink.rect(1, 1, CW - 2, CH - 2, color=P.line, width=2, rough=False)
    return ink.img, cov


def side_view(ink, P, X, t):
    off = bus_offset(t)
    # street beyond the windows
    for k, sx in enumerate(X["street"]):
        x = (sx - off * (1 + 0.2 * k)) % (CW + 200) - 100
        ink.line([(x, 30), (x, 205)], P.line, 2, alpha=120)
        ink.circle(x, 30, 8, fill=P.glass, color=P.line, width=1.4)
    if X["rain"]:
        for k in range(30):
            rx = (k * 53 + t * 260) % CW
            ry = (k * 37 + t * 480) % CH
            ink.d.line([(rx, ry), (rx - 3, ry + 9)], fill=tuple(P.line) + (90,), width=1)
    ink.d.rectangle([0, 214, CW, CH], fill=P.road)
    # bus body
    ink.rect(16, 36, 424, 206, fill=P.body, color=P.line, width=2.5)
    for k in range(6):
        wx = 30 + k * 64
        if (wx + 52 > 110 and wx < 160) or wx + 52 > 362:
            continue
        ink.rect(wx, 50, wx + 52, 108, fill=P.glass, color=P.line, width=1.6)
    ink.d.rectangle([20, 120, 420, 200], fill=tuple(P.body) + (255,))
    ink.line([(20, 192), (420, 192)], P.line, 2)
    for wx in (80, 360):
        ink.circle(wx, 208, 16, fill=P.floor, color=P.line, width=2)
    # rear service door: always shut (anchor A6)
    ink.rect(118, 54, 152, 192, fill=P.glass, color=P.line, width=2)
    ink.line([(135, 54), (135, 192)], P.line, 1.6)
    ink.label((135, 46), "SERVICE", 9, P.line, anchor="mm")
    # front door: opens to board and alight
    open_ = max(ease(t, 0.1, 0.4) * (1 - ease(t, 1.3, 1.6)), ease(t, 4.8, 5.1) * (1 - ease(t, 6.0, 6.3)))
    ink.rect(368, 54, 406, 192, fill=P.ground if open_ > 0.5 else P.glass, color=P.line, width=2)
    if open_ <= 0.5:
        ink.line([(387, 54), (387, 192)], P.line, 1.6)
    # bell cord along the ceiling
    pull = 1.0 if 2.0 <= t < 2.4 else 0.0
    cord = [(30, 44), (240, 44 + 6 * pull), (410, 44)]
    ink.line(cord, (200, 60, 60) if P.t == "ink" else P.key, 1.5)
    if 2.15 <= t < 2.6:
        ink.circle(410, 44, 6, fill=P.key, color=P.line, width=1)
    # seats
    for sx in (100, 175, SEAT_X, KEY_X + 50, 330):
        pass
    for sx in (100, 175, SEAT_X, 330):
        ink.rect(sx - 14, 150, sx + 22, 160, fill=P.seat, color=P.line, width=1.4)
        ink.rect(sx - 18, 118, sx - 12, 160, fill=P.seat, color=P.line, width=1.4)
    for sx, coat in X["sitters"]:
        figure(ink, sx, 190, 0.62, "sit", 0, 1, color=P.line, coat=P.coat(coat), width=1.8)
    # the key on the seat (A4)
    if t >= 4.0:
        key_shape(ink, KEY_X - 8, 148, 0.45, color=P.key, outline=P.line)
    v = visitor_state(t)
    hands = None
    if v:
        x, pose, arm, act = v
        p = figure(ink, x, 190, 0.62, pose, x / 40, -1 if pose == "walk" else 1,
                   color=P.line, coat=P.coat(X["coat"]), width=1.8, hat=True, arm=arm)
        hands = p["hands"][0]
        if t < 3.8:
            o = ease(t, 2.7, 3.1)
            envelope(ink, hands[0] + 4, hands[1], 18, 12, open_=o, color=PAGE if P.t == "ink" else P.glass, outline=P.line)
    # a standing passenger holding the pole (seed); drawn in front
    occluded_key = False
    if X["stander"] is not None:
        sx = X["stander"]
        ink.line([(sx + 8, 40), (sx + 8, 192)], P.line, 2)
        figure(ink, sx, 192, 0.66, "reach", 0, 1, color=P.line, coat=P.coat(X["stander_coat"]), width=1.8, arm=160)
        occluded_key = abs(sx - KEY_X) < 22
        occluded_env = abs(sx - SEAT_X) < 18
    else:
        occluded_env = False
    return {"A1": True, "A2": True, "A3": not occluded_env, "A4": not occluded_key, "A5": True, "A6": True}


def overhead_view(ink, P, X, t):
    off = bus_offset(t)
    # road markings scroll under the bus
    for k in range(12):
        x = (k * 60 - off) % (CW + 60) - 30
        ink.d.rectangle([x, 226, x + 30, 230], fill=tuple(P.line) + (110,))
        ink.d.rectangle([x, 16, x + 30, 20], fill=tuple(P.line) + (110,))
    # bus floor plan (front to the right)
    ink.rect(24, 40, 416, 210, fill=P.floor if P.t == "ink" else P.body, color=P.line, width=2.5)
    ink.d.rectangle([24, 110, 416, 140], fill=tuple(P.ground) + (120,))  # aisle
    # doors on the kerb side (bottom edge)
    ink.rect(118, 204, 152, 214, fill=P.glass, color=P.line, width=2)  # service door, shut
    ink.label((135, 224), "SERVICE", 9, P.line, anchor="mm")
    open_ = max(ease(t, 0.1, 0.4) * (1 - ease(t, 1.3, 1.6)), ease(t, 4.8, 5.1) * (1 - ease(t, 6.0, 6.3)))
    ink.rect(368, 204, 406, 214, fill=P.ground if open_ > 0.5 else P.glass, color=P.line, width=2)
    # seats: two rows
    for sx in (100, 175, SEAT_X, KEY_X + 0, 330):
        for sy in (60, 168):
            ink.rect(sx - 13, sy, sx + 13, sy + 26, fill=P.seat, color=P.line, width=1.3)
    # bell push on the pole in the aisle
    ink.circle(300, 125, 5, fill=P.key if 2.15 <= t < 2.6 else P.glass, color=P.line, width=1.4)
    if 2.15 <= t < 2.6:
        ink.circle(300, 125, 5 + 30 * ramp(t, 2.15, 2.6), color=P.key, width=1.5, alpha=int(220 * (1 - ramp(t, 2.15, 2.6))))

    def person(x, y, coat, hat=False):
        ink.ellipse(x, y, 13, 9, fill=P.coat(coat), color=P.line, width=1.6)
        ink.circle(x, y, 6, fill=P.line if hat else (230, 200, 170) if P.t == "ink" else P.glass, color=P.line, width=1.2)
    for sx, coat in X["sitters"]:
        person(sx, 181, coat)
    if t >= 4.0:
        key_shape(ink, KEY_X - 8, 180, 0.4, color=P.key, outline=P.line)
    v = visitor_state(t)
    if v:
        x, pose, arm, act = v
        if t < 1.2:
            y = lerp(236, 125, ramp(t, 0.4, 1.2))
            x = 388
        elif t < 1.9:
            y = lerp(125, 181, ramp(t, 1.75, 1.9))
        elif t < 4.4:
            y = 181
        elif t < 5.1:
            y = lerp(181, 125, ramp(t, 4.4, 4.6))
        else:
            x, y = 388, lerp(125, 250, ramp(t, 5.1, 5.9))
        person(x, y, X["coat"], hat=True)
        if 1.9 <= t < 3.8:
            o = ease(t, 2.7, 3.1)
            envelope(ink, x + 4, y - 18, 16, 10, open_=o, color=PAGE if P.t == "ink" else P.glass, outline=P.line)
    if X["stander"] is not None:
        person(X["stander"], 125, X["stander_coat"])
    # overhead: nothing occludes, but the arm reaching for the bell cannot be seen (only the push lights)
    return {"A1": True, "A2": True, "A3": True, "A4": True, "A5": True, "A6": True}


# ---------------------------------------------------------------- layout ---

COVERAGE = {}


def measure_coverage():
    """Ask the generator, at each anchor's own time, whether that anchor is visible."""
    for k, (name, delta) in enumerate(CONDS):
        for seed in SEEDS:
            for aid, nm, at in ANCHORS:
                _, cv = generate(manifest(delta), seed, at, int(at * FPS))
                COVERAGE[(k, seed, aid)] = cv[aid]


def clip_time(local):
    return clamp(local - CLIP_AT, 0, CLIP - 1 / FPS)


def draw_manifest(ink, x, y, m, delta, size=14):
    s = "{ " + ", ".join(f"{k}: {v}" for k, v in m.items()) + " }"
    ink.label((x, y), "manifest", 11, MUTED)
    xx = x
    ink.text((xx, y + 16), "{ ", "mono", size, INK)
    xx += ink.text_size("{ ", "mono", size)[0] + 4
    for k, (key, val) in enumerate(m.items()):
        piece = f"{key}: {val}" + (", " if k < len(m) - 1 else " }")
        ink.text((xx, y + 16), piece, "mono", size, ACCENT if key in delta else INK)
        xx += ink.text_size(piece, "mono", size)[0] + 8


def cov_dots(ink, x, y, cov, light=False):
    for k, (aid, name, at) in enumerate(ANCHORS):
        ok = cov.get(aid, True)
        cx = x + k * 58
        ink.circle(cx, y, 5, fill=(90, 140, 90) if ok else ACCENT, color=INK, width=1, rough=False)
        ink.label((cx + 9, y - 7), aid if ok else aid + " hid", 11, MUTED if ok else ACCENT)


def run_cond(k, local, ink):
    name, delta = CONDS[k]
    m = manifest(delta)
    ink.fill(PAGE)
    ink.label((30, 26), f"CONDITION {k + 1} / 3 · {name.upper()}", 14, ACCENT)
    draw_manifest(ink, 30, 44, m, delta)
    ct = clip_time(local)
    fi = int(ct * FPS)
    for j, seed in enumerate(SEEDS):
        img, cov = generate(m, seed, ct, fi)
        x0 = 30 + j * (CW + 40)
        ink.paste(img, (x0, 112))
        ink.label((x0, 372), f"seed {seed}", 13, INK)
        full = {aid: COVERAGE[(k, seed, aid)] for aid, _, _ in ANCHORS}
        cov_dots(ink, x0 + 66, 380, full)
    ink.label((30, 414), "t = " + f"{ct:4.1f} s / {CLIP} s", 12, MUTED)
    # anchor ticker
    for aid, nm, at in ANCHORS:
        if at <= ct < at + 0.9:
            ink.label((W / 2, 440), f"{aid} · {nm}", 16, ACCENT, anchor="mm")
    ink.label((W / 2, 500), "same seeds, same anchor times, same clip size · only the highlighted field changes", 13, MUTED, anchor="mm")


def run_grid(local, ink):
    ink.fill(PAGE)
    ink.label((W / 2, 22), "ALL SIX SAMPLES TOGETHER · rows: condition · columns: seed", 13, ACCENT, anchor="mm")
    ct = clip_time(local)
    fi = int(ct * FPS)
    gw, gh = 272, 153
    for k, (name, delta) in enumerate(CONDS):
        m = manifest(delta)
        y0 = 40 + k * (gh + 8)
        ink.label((24, y0 + gh / 2 - 8), name, 13, INK)
        ink.label((24, y0 + gh / 2 + 10), ", ".join(f"{a}: {b}" for a, b in delta.items()) or "(none)", 11, ACCENT if delta else MUTED)
        for j, seed in enumerate(SEEDS):
            img, _ = generate(m, seed, ct, fi)
            ink.paste(img.resize((gw, gh), Image.LANCZOS), (360 + j * (gw + 14), y0))
            if k == 0:
                ink.label((330 + j * (gw + 14) + gw / 2, 30 + 0), "", 1)
    for j, seed in enumerate(SEEDS):
        ink.label((360 + j * (gw + 14) + gw - 6, 44), f"seed {seed}", 11, MUTED, anchor="ra")


def run_report(ink):
    ink.fill(PAGE)
    ink.label((W / 2, 40), "OBSERVED IN THESE SIX SAMPLES (not a claim about generators in general)", 14, ACCENT, anchor="mm")
    lines = []
    for k, (name, delta) in enumerate(CONDS):
        hid = [f"{aid} (seed {s})" for s in SEEDS for aid, _, _ in ANCHORS if not COVERAGE.get((k, s, aid), True)]
        lines.append((name, "all six anchors visible in both seeds" if not hid else "hidden: " + ", ".join(hid)))
    for k, (a, b) in enumerate(lines):
        y = 100 + k * 56
        ink.text((70, y), a, "mono", 16, MUTED)
        ink.text((290, y - 4), b, "serif", 24, INK)
    notes = ["camera: overhead keeps every anchor but drops the gesture: the bell reads only as the lit push",
             "treatment: cyanotype changes ground, line and fill; positions and timing are untouched",
             "seeds: same seed, same passengers in every condition; the generator is exactly repeatable",
             "intended effect appeared in 2 / 2 samples for each delta"]
    for k, s in enumerate(notes):
        ink.label((70, 300 + k * 34), s, 14, INK)
    ink.label((W / 2, 480), "a standing passenger (seed-placed) can cover the seat in side view: that is a seed effect, not a delta effect", 12, MUTED, anchor="mm")


@film.picture
def frame(t, ink):
    name, local, a, b = SC.at(t)
    if name == "title":
        section_card(ink, "AFTER MAURO MARTINO · EXERCISES IN STYLE · 2023", "Controlled variation",
                     "a coded procedural generator · one baseline · two deltas · two matched seeds each")
    elif name.startswith("c"):
        run_cond(int(name[1]), local, ink)
    elif name == "grid":
        run_grid(local, ink)
    else:
        run_report(ink)
    edge_fade(ink, t, a, b, 0.3, color=PAGE if name != "title" else NIGHT)


def clip_sound(mix, at):
    # engine idles, pulls away, stops
    n = mix.noise(CLIP, "brown")
    tt = mix.t(CLIP)
    level = 0.5 + 0.5 * np.clip((tt - 1.6) / 0.8, 0, 1) * np.clip((4.6 - tt) / 0.8, 0, 1)
    eng = (np.sin(2 * np.pi * (38 + 14 * level) * tt) * 0.5 + n * 0.6) * level
    mix.add(eng, at, 0.12)
    for dt in (0.1, 4.8):
        mix.add(mix.band(mix.noise(0.5), 1500, 7000) * np.hanning(int(0.5 * RATE)), at + dt, 0.12, 0.6)  # door hiss
    mix.steps(at + 0.4, at + 1.9, 0.4, 0.12, "wood", 0.6, 0.0)
    mix.steps(at + 4.4, at + 5.9, 0.4, 0.12, "wood", 0.0, 0.7)
    mix.note(at + 2.2, 1046, 0.5, 0.12, 0.4, "sine", 0.002, 0.4, 0)
    mix.note(at + 2.45, 784, 0.6, 0.1, 0.4, "sine", 0.002, 0.5, 0)
    mix.add(mix.band(mix.noise(0.3), 2000, 8000) * np.hanning(int(0.3 * RATE)), at + 2.8, 0.06, 0)  # paper
    mix.click(at + 4.0, 0.2, 0, 8000)
    mix.click(at + 4.02, 0.14, 0, 9500)


@film.sound
def sound(mix):
    for k in range(3):
        clip_sound(mix, SC.start(f"c{k}") + CLIP_AT)
    clip_sound(mix, SC.start("grid") + CLIP_AT)
    mix.bell(0.4, 523, 2.5, 0.08)
    mix.reverb(0.08)


measure_coverage()
print("coverage:", {k: v for k, v in COVERAGE.items() if not v} or "all anchors visible")

if __name__ == "__main__":
    film.render()

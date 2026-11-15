"""La Cité Raymond Queneau — one locked 25 s picture edit of the station below the housing blocks,
played twice: MIX A scores it as a welcoming place, MIX B as a watched one. Same frames, same loudness."""
import hashlib
import math
from kit_cinema_b import *

PIC = 25.0
SC = Score([(0, 3.0, "title"), (3.0, 5.5, "cardA"), (5.5, 5.5 + PIC, "A"), (5.5 + PIC, 8.0 + PIC, "cardB"),
            (8.0 + PIC, 8.0 + 2 * PIC, "B"), (8.0 + 2 * PIC, 14.0 + 2 * PIC, "end")])
SHOTS = [(0, 4.5, "blocks"), (4.5, 9.0, "arrive"), (9.0, 11.0, "bell"), (11.0, 15.5, "open"),
         (15.5, 19.0, "window"), (19.0, 23.0, "leave"), (23.0, 25.0, "door")]
KEY_CUT = 15.5
TARGET_DB = -23.0   # LUFS, K-weighted, gated (BS.1770 style)
HASHES = {"A": {}, "B": {}}
LOUD = {}
V_COAT = (86, 72, 98)


class LockedFilm(Film):
    """Picture passes are drawn from the same master: local time AND local frame index,
    so boil, grain and jitter repeat exactly in both passes."""

    def frame(self, k):
        t = k / self.fps
        name, local, a, b = SC.at(t)
        if name in ("A", "B"):
            kl = k - int(round(a * self.fps))
            ink = Ink(kl / self.fps, kl, self.size, self.boil, self.wobble, self.seed)
            ink.paper()
            master(kl / self.fps, ink)
            img = ink.finish()
            HASHES[name][kl] = hashlib.sha1(img.tobytes()).hexdigest()
            return img
        return super().frame(k)


film = LockedFilm("la-cite-raymond-queneau", seconds=SC.total, boil=6, wobble=1.1, seed=12)
film.poster_at = SC.start("A") + 17.0


# ---------------------------------------------------------------- picture master ---

def sky(ink, top=(206, 196, 196), bottom=(240, 224, 204)):
    for y in range(0, H, 6):
        ink.d.rectangle([0, y, W, y + 6], fill=mix_color(top, bottom, y / H))


def blocks(ink, t, dx=0.0, lit_seed=3):
    rng = random.Random(lit_seed)
    for bx, bw, bh, col in ((60, 250, 300, (196, 186, 172)), (360, 300, 360, (186, 178, 166)), (700, 220, 280, (200, 190, 176))):
        x0 = bx + dx
        ink.rect(x0, 420 - bh, x0 + bw, 420, fill=col, color=INK, width=2)
        for r in range(int((bh - 30) / 34)):
            for c in range(int((bw - 20) / 30)):
                wx, wy = x0 + 14 + c * 30, 420 - bh + 18 + r * 34
                lit = rng.random() < 0.28
                ink.rect(wx, wy, wx + 18, wy + 22, fill=(246, 214, 140) if lit else (120, 124, 132), color=INK, width=1, rough=False)


def shot_blocks(ink, t):
    sky(ink)
    blocks(ink, t, dx=-18 * t / 4.5)
    # footbridge and platform canopy in front
    ink.d.rectangle([0, 420, W, H], fill=(150, 142, 130))
    ink.rect(-10, 380, W + 10, 396, fill=(110, 104, 98), color=INK, width=2)
    for x in range(20, W, 90):
        ink.line([(x - 8 * t / 4.5, 396), (x - 8 * t / 4.5, 470)], INK, 3)
    ink.line([(0, 470), (W, 470)], INK, 2)


def station_wide(ink, t, visitor=None, key_on_bench=False, env_on_bench=False):
    ink.d.rectangle([0, 0, W, H], fill=(226, 220, 206))
    # the blocks seen behind the platform wall
    ink.d.rectangle([0, 0, W, 150], fill=(206, 198, 196))
    for k in range(9):
        x = 30 + k * 110
        ink.rect(x, 40, x + 80, 150, fill=(190, 182, 172), color=MUTED, width=1.2)
        for r in range(3):
            for c in range(3):
                ink.d.rectangle([x + 8 + c * 24, 50 + r * 32, x + 22 + c * 24, 68 + r * 32], fill=(130, 132, 138) if (k + r + c) % 5 else (240, 210, 140))
    ink.line([(0, 150), (W, 150)], INK, 2)
    platform(ink, 330)
    door(ink, 820, 330, w=80, h=170, sign="SERVICE")
    bench(ink, 430, 350, w=230)
    clock(ink, 150, 220, 34, 12.0 + t / 600)
    if env_on_bench:
        envelope(ink, 470, 350 - 52, 40, 26, open_=1)
    if key_on_bench:
        key_shape(ink, 390, 350 - 50, 0.8, angle=0.1)
        bench_key_glint(ink, 400, 290, t)
    if visitor:
        x, pose, arm, env = visitor
        p = figure(ink, x, 352 if pose != "sit" else 350, 1.5, pose, x / 60, 1, coat=V_COAT, hat=True, arm=arm)
        if env:
            h = p["hands"][0]
            envelope(ink, h[0] + 6, h[1] - 2, 40, 26)


def shot_arrive(ink, t):
    f = ramp(t, 0, 3.4)
    x = lerp(-40, 400, f)
    pose = "walk" if f < 1 else "sit"
    station_wide(ink, t, (x, pose, 60 if pose == "sit" else None, True))


def shot_bell(ink, t):
    ink.d.rectangle([0, 0, W, H], fill=(214, 208, 196))
    ink.hatch(0, 0, W, H, gap=18, angle=80, color=(190, 184, 172), width=1, alpha=120)
    ink.rect(380, 60, 580, 90, fill=(110, 100, 90), color=INK, width=3)
    sw = math.sin(max(0, t - 0.3) * 9) * 0.45 * math.exp(-max(0, t - 0.3) * 1.3) if t > 0.3 else 0
    cx, cy = 480, 100
    ca, sa = math.cos(sw), math.sin(sw)
    shape = [(-22, 0), (22, 0), (34, 90), (70, 150), (-70, 150), (-34, 90)]
    pts = [(cx + px * ca - py * sa, cy + px * sa + py * ca) for px, py in shape]
    ink.poly(pts, fill=BRASS, color=INK, width=3)
    clap = (cx - 160 * sa, cy + 160 * ca)
    ink.circle(clap[0], clap[1], 14, fill=(90, 70, 40), color=INK, width=2)
    ink.line([(cx, cy), clap], INK, 3)


def shot_open(ink, t):
    ink.d.rectangle([0, 0, W, H], fill=(200, 170, 130))
    # bench slats close up
    for k in range(4):
        y = 300 + k * 60
        ink.rect(-10, y, W + 10, y + 46, fill=(160, 120, 80), color=INK, width=2.5)
    o = ease(t, 0.8, 1.8)
    envelope(ink, 480, 320, 300, 190, open_=o)
    # hands
    for sx in (-1, 1):
        hx = 480 + sx * 170
        ink.ellipse(hx, 360, 40, 26, fill=(232, 200, 170), color=INK, width=2.2)
        ink.line([(hx + sx * 30, 360), (hx + sx * 140, 470)], V_COAT, 26)
    if t > 1.8:
        y = lerp(300, 170, ease(t, 1.8, 3.0))
        key_shape(ink, 400, y, 4.0, angle=0.05)
        if t > 3.0:
            bench_key_glint(ink, 560, y - 10, t)


def shot_window(ink, t):
    ink.d.rectangle([0, 0, W, H], fill=(186, 178, 166))
    ink.hatch(0, 0, W, H, gap=10, angle=0, color=(170, 162, 150), width=1, alpha=120)
    ink.rect(280, 70, 680, 470, fill=(246, 222, 160), color=INK, width=4)
    ink.line([(480, 70), (480, 470)], INK, 3)
    ink.line([(280, 270), (680, 270)], INK, 3)
    # silhouette behind the glass
    ink.circle(470, 220, 44, fill=(70, 60, 64), color=(70, 60, 64), width=1)
    ink.poly([(400, 470), (400, 320), (430, 280), (510, 280), (540, 320), (540, 470)], fill=(70, 60, 64), color=(70, 60, 64), width=1)
    raise_ = ease(t, 0.9, 1.6)
    if raise_ > 0:
        ax, ay = lerp(540, 600, raise_), lerp(400, 190, raise_)
        ink.line([(530, 320), (ax, ay)], (70, 60, 64), 24)
        ink.circle(ax, ay - 10, 18, fill=(70, 60, 64), color=(70, 60, 64), width=1)
    # curtain parts
    c = ease(t, 0.0, 0.8)
    for side in (-1, 1):
        x_in = 480 + side * lerp(10, 170, c)
        x_out = 480 + side * 200
        ink.poly([(x_out, 70), (x_in, 70), (x_in + side * 12, 470), (x_out, 470)], fill=(236, 232, 222, 235), color=INK, width=1.6)
        for k in range(4):
            xx = lerp(x_in, x_out, (k + 1) / 5)
            ink.line([(xx, 75), (xx + side * 6, 465)], (200, 194, 180), 1.4)
    ink.rect(250, 470, 710, 490, fill=(160, 150, 140), color=INK, width=2.5)


def shot_leave(ink, t):
    if t < 1.2:
        station_wide(ink, t, (400, "sit", 30, False), key_on_bench=t > 0.6, env_on_bench=True)
    else:
        x = lerp(420, 1010, ease(t, 1.2, 4.0))
        station_wide(ink, t, (x, "walk", None, False), key_on_bench=True, env_on_bench=True)


def shot_door(ink, t):
    ink.d.rectangle([0, 0, W, H], fill=(214, 206, 192))
    ink.hatch(0, 0, W, 420, gap=34, angle=0, color=(190, 184, 172), width=1.4, alpha=160)
    door(ink, 560, 470, w=220, h=380, sign=None)
    ink.rect(500, 50, 620, 80, fill=PAGE, color=INK, width=2)
    ink.label((560, 65), "SERVICE", 16, INK, anchor="mm")
    ink.circle(560, 30, 12, fill=(250, 240, 200), color=INK, width=2)
    ink.d.rectangle([0, 470, W, H], fill=(160, 120, 80))
    key_shape(ink, 140, 500, 2.2, angle=-0.1)
    bench_key_glint(ink, 240, 490, t)


SHOT_FN = {"blocks": shot_blocks, "arrive": shot_arrive, "bell": shot_bell, "open": shot_open,
           "window": shot_window, "leave": shot_leave, "door": shot_door}


def master(t, ink):
    for a, b, name in SHOTS:
        if a <= t < b:
            SHOT_FN[name](ink, t - a)
            return
    SHOT_FN["door"](ink, t - 23.0)


# ---------------------------------------------------------------- cards ---

@film.picture
def frame(t, ink):
    name, local, a, b = SC.at(t)
    if name == "title":
        section_card(ink, "AFTER LA CITÉ RAYMOND QUENEAU · AZAM / FIRODE 1998", "One picture, two accounts",
                     "a 25 s locked edit · played twice · two synthesized soundtracks at one loudness")
    elif name == "cardA":
        section_card(ink, "PASS 1 · MIX A", "A welcoming place", f"same picture master · loudness {LOUD.get('A', TARGET_DB):.1f} LUFS")
    elif name == "cardB":
        section_card(ink, "PASS 2 · MIX B", "A watched place", f"same picture master · loudness {LOUD.get('B', TARGET_DB):.1f} LUFS")
    else:
        ink.fill(PAGE)
        ink.label((W / 2, 60), "WHAT WAS HELD AND WHAT CHANGED", 15, ACCENT, anchor="mm")
        n = sum(1 for k, h in HASHES["A"].items() if HASHES["B"].get(k) == h)
        tot = int(PIC * FPS)
        same = f"{n} / {tot} frames identical before encoding" if HASHES["B"] else "(frame check runs during the render)"
        rows = [("picture", same),
                ("order / cadence", f"{len(SHOTS)} shots · 24 fps · 960×540 · cuts at 4.5 9 11 15.5 19 23 s"),
                ("loudness", f"A {LOUD.get('A', 0):.1f} LUFS  ·  B {LOUD.get('B', 0):.1f} LUFS  (K-weighted, gated)"),
                ("bell", "A: a soft high chime  ·  B: a low clang with a held hum"),
                ("key cut 15.5 s", "A: music only — the melody answers the wave"),
                ("", "B: voice only — a filtered radio murmur and a shutter click"),
                ("departure", "A: one set of steps · B: a second set follows")]
        for k, (lab, s) in enumerate(rows):
            y = 110 + k * 50
            ink.text((70, y), lab, "mono", 15, MUTED)
            ink.text((250, y - 4), s, "serif", 23, INK)
        ink.label((W / 2, 480), "the event record does not change: arrive · bell · open · key on bench · leave · door shut", 13, MUTED, anchor="mm")
    edge_fade(ink, t, a, b, 0.3)


# ---------------------------------------------------------------- sound ---

def mix_a(m):
    """Welcoming: courtyard voices, birds, a melody, a soft bell. Music-only at the key cut."""
    m.room(0, PIC, 0.02)
    # children / neighbours far off (non-verbal murmurs), cut out under the key cut
    for k, (at, d, p) in enumerate([(0.3, 3.0, 260), (2.6, 2.4, 300), (5.0, 3.2, 230), (11.5, 3.0, 280), (19.5, 3.0, 250)]):
        m.murmur(at, d, 0.05, p, (-0.6, 0.6)[k % 2], seed=40 + k)
    for k in range(18):
        at = 0.4 + k * 1.3 + m.rs.uniform(0, 0.4)
        if KEY_CUT <= at < 19:
            continue
        t = m.t(0.12)
        sig = np.sin(2 * np.pi * (3200 + 1800 * t / 0.12) * t) * np.hanning(len(t))
        m.add(sig, at, 0.05, m.rs.uniform(-0.8, 0.8))
    m.steps(4.5, 7.9, 0.48, 0.12, "stone", -0.6, 0.0)
    m.steps(20.2, 23.0, 0.5, 0.1, "stone", 0.1, 0.8)
    # melody: a simple major tune in plucks, thinned in the bell shot
    tune = [(0, 392), (0.5, 440), (1.0, 494), (1.5, 587), (2.5, 494), (3.0, 440), (3.5, 392)]
    for base in (0.5, 4.8, 11.3, 19.2):
        for dt, f in tune:
            m.pluck(base + dt, f, 1.0, 0.11, 0.2)
    # key cut, music only: the phrase answers the raised hand
    for dt, f in [(0.0, 587), (0.4, 659), (0.8, 784), (1.6, 740), (2.0, 784), (2.6, 988)]:
        m.pluck(KEY_CUT + dt, f, 1.4, 0.15, 0.0)
        m.note(KEY_CUT + dt, f / 2, 0.7, 0.05, 0, "tri")
    m.bell(9.3, 880, 3.0, 0.22, 0.0)
    m.bell(23.2, 660, 2.0, 0.12, 0.0)
    for f in (196, 247, 294):
        m.note(23.0, f, 2.0, 0.05, 0, "tri", 0.3, 0.6, 0.6)


def mix_b(m):
    """Watched: hum, low drone, a clanging bell, doubled steps. Voice-only at the key cut."""
    t = m.t(PIC)
    hum = (np.sin(2 * np.pi * 100 * t) + 0.4 * np.sin(2 * np.pi * 200 * t) + 0.2 * np.sign(np.sin(2 * np.pi * 100 * t))) * 0.25
    gate = np.ones_like(t)
    a, b = int(KEY_CUT * RATE), int(19.0 * RATE)
    gate[a:b] = 0.0
    sm = np.convolve(gate, np.ones(2000) / 2000, "same")
    m.add(hum * sm, 0, 0.05, 0.3)
    drone = sum(m.tone(f, PIC, "sine", 0.003) for f in (41, 43.5, 82)) * sm
    m.add(drone, 0, 0.08, 0)
    m.steps(4.5, 7.9, 0.48, 0.12, "stone", -0.6, 0.0)
    m.steps(4.75, 8.1, 0.48, 0.07, "gravel", -0.9, -0.5)    # someone else's steps, a beat behind
    m.steps(20.2, 23.0, 0.5, 0.1, "stone", 0.1, 0.8)
    m.steps(20.5, 23.5, 0.5, 0.08, "gravel", -0.8, 0.2)
    m.bell(9.3, 233, 4.0, 0.32, 0.0)
    m.bell(9.32, 247, 4.0, 0.2, 0.0)
    for k in range(3):
        m.click(11.2 + k * 1.1, 0.05, 0.7, 2000)  # relay ticks
    # key cut, voice only: a filtered radio murmur and one shutter click
    r = Mix(3.5, seed=77)
    r.murmur(0, 3.4, 1.0, 150, 0, seed=78)
    v = r.band(r.L, 400, 2600)
    v = np.tanh(v * 3) * 0.6
    m.add(v, KEY_CUT + 0.05, 0.25, 0.5)
    m.click(KEY_CUT + 1.3, 0.35, 0.6, 9000, 0.02)
    m.click(KEY_CUT + 1.38, 0.25, 0.6, 5000, 0.04)
    # door: the hum swells and cuts
    m.drone(23.0, 2.0, (55, 58), 0.08, 0, 0.5, 0.05)


@film.sound
def sound(mix):
    stA = sub_mix(PIC, mix_a, seed=1)
    stB = sub_mix(PIC, mix_b, seed=2)
    gA = 10 ** ((TARGET_DB - lufs(stA)) / 20)
    gB = 10 ** ((TARGET_DB - lufs(stB)) / 20)
    stA, stB = stA * gA, stB * gB
    place(mix, stA, SC.start("A"))
    place(mix, stB, SC.start("B"))
    mix.bell(SC.start("cardA") + 0.1, 523, 1.8, 0.05)
    mix.bell(SC.start("cardB") + 0.1, 523, 1.8, 0.05)
    # replicate kit.Mix.master's single overall gain so the cards report what is actually heard
    st = np.stack([mix.L, mix.R], 1)
    peak = np.abs(st).max()
    g = 0.89 / max(peak, 1.0)
    st2 = st * g
    if peak * g < 0.25 * 0.89 / 0.89 and peak < 0.25:
        rms = math.sqrt((st2 ** 2).mean())
        g *= min(4.0, 0.2 / max(rms, 1e-6), 0.89 / max(np.abs(st2).max(), 1e-9))
    LOUD["A"], LOUD["B"] = lufs(stA * g), lufs(stB * g)
    print(f"  loudness A {LOUD['A']:.2f} LUFS · B {LOUD['B']:.2f} LUFS (stem gains {gA:.2f}, {gB:.2f}; master {g:.2f})")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--stills":
        # stills of the master use picture time
        pass
    film.render()

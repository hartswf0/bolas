"""Exercices de style — station. A six-beat ledger and four retellings, each set as
kinetic type with its own motion rule: reverse log, sensory inventory, rigid notice,
the key as narrator. A closing matrix checks every telling against the six beats."""
import math
from PIL import Image, ImageDraw, ImageFilter
from kit import *
from kit_anim import run, typed, wrap

film = Film("exercices-de-style", seconds=67.0, boil=0, wobble=0, seed=2)
film.poster_at = 40.0

LEDGER = [
    ("b1", "07:11", "A visitor arrives at the empty station carrying a sealed envelope."),
    ("b2", "07:12", "A bell rings."),
    ("b3", "07:13", "The visitor opens the envelope."),
    ("b4", "07:13", "Inside is a brass key."),
    ("b5", "07:14", "The visitor leaves the key on the bench."),
    ("b6", "07:15", "The visitor walks away. The service door stays closed."),
]
SECTIONS = [  # (start, end, id)
    (0.0, 3.0, "title"),
    (3.0, 12.5, "base"),
    (12.5, 24.0, "A"),
    (24.0, 36.0, "B"),
    (36.0, 48.0, "C"),
    (48.0, 60.0, "D"),
    (60.0, 67.0, "matrix"),
]
HEAD = {
    "base": ("0", "Baseline", "the event ledger · six beats, frozen"),
    "A": ("A", "Log, reverse order", "rule: newest entry first · clock runs back · cause-to-effect arrows unchanged"),
    "B": ("B", "Sensory inventory", "rule: only what the clerk behind frosted glass could sense · gaps recorded"),
    "C": ("C", "Notice", "rule: the form exists first; facts must fit its boxes"),
    "D": ("D", "The key, narrating", "rule: first person, an object's senses · dark until the envelope opens"),
}

REVERSE = [
    ("07:15:40", "departure, west · service door still closed", "b6"),
    ("07:14:55", "key set down on bench, centre slat", "b5"),
    ("07:13:30", "envelope contents: one brass key", "b4"),
    ("07:13:05", "envelope opened by visitor", "b3"),
    ("07:12:00", "bell · one ring", "b2"),
    ("07:11:20", "arrival · one visitor · one sealed envelope", "b1"),
]
# sensory: (appear-at local, column, text, beat)
SENSE = [
    (0.8, "SEEN (frosted)", "a dark coat-shape, arriving", "b1"),
    (1.2, "SEEN (frosted)", "something pale and oblong in its hand", "b1"),
    (2.2, "HEARD", "the bell: one stroke, slightly flat", "b2"),
    (3.4, "HEARD", "paper tearing, short", "b3"),
    (4.3, "SEEN (frosted)", "a glint, gold, for a second", "b4"),
    (5.3, "HEARD", "a small hard tap on wood", "b5"),
    (6.3, "HEARD", "steps, leaving, fading west", "b6"),
    (7.1, "HEARD", "no door — nothing opened", "b6"),
    (7.9, "SMELLED", "wet stone; nothing new", None),
]
SENSE_COLS = ["SEEN (frosted)", "HEARD", "SMELLED"]
OMIT = "not accessible: what glinted (b4 is a glint, not yet a key) · recorded omission"
FORM = [
    ("DATE / TIME", "07:11 – 07:15", "b1"),
    ("LOCATION", "Platform 1, waiting bench", "b1"),
    ("PERSONS", "1 · visitor · not identified", "b1"),
    ("ITEM ON ARRIVAL", "1 envelope · sealed", "b1"),
    ("SIGNAL", "bell · rang once · 07:12", "b2"),
    ("ITEM OPENED", "envelope · by visitor", "b3"),
    ("ITEM FOUND", "1 key · brass", "b4"),
    ("ITEM LEFT", "key · on bench", "b5"),
    ("DEPARTURE", "visitor · on foot · 07:15", "b6"),
    ("SERVICE DOOR", "closed · not opened · not tested", "b6"),
    ("ACTION REQUIRED", "none", None),
]
KEY_LINES = [
    (0.4, "For three days I was folded into paper, in the dark.", "b1"),
    (2.0, "A ring, far off, came through the paper.", "b2"),
    (3.6, "A tear — and light.", "b3"),
    (5.0, "A warm hand held me up. I was the thing inside.", "b4"),
    (6.8, "Then wood, cold, along my whole length.", "b5"),
    (8.4, "Its steps went away. Nothing has opened since.", "b6"),
]
LIGHT_AT = 3.75
MATRIX = [
    ("0 baseline", "ledger", "✓✓✓✓✓✓"),
    ("A reverse log", "order reversed", "✓✓✓✓✓✓"),
    ("B sensory", "access-limited", "✓✓✓~✓✓"),
    ("C notice", "fixed format", "✓✓✓✓✓✓"),
    ("D key speaks", "object voice", "✓✓✓✓✓✓"),
]


def section_at(t):
    for a, b, k in SECTIONS:
        if a <= t < b:
            return a, b, k
    return SECTIONS[-1]


def header(ink, key, alpha=1.0, dark=False):
    n, title, rule = HEAD[key]
    col = PAGE if dark else INK
    ink.text((40, 26), n, "serif", 54, ACCENT if not dark else BRASS, alpha=int(255 * alpha))
    ink.text((96, 32), title, "serif", 40, col, alpha=int(255 * alpha))
    ink.label((98, 82), rule, 13, RULE if dark else MUTED, alpha=int(255 * alpha))
    ink.line([(40, 108), (920, 108)], RULE if not dark else (70, 66, 70), 1.2, rough=False)


def tick(ink, x, y, s=1.0, color=ACCENT, partial=False):
    if partial:
        ink.line([(x - 7 * s, y), (x + 7 * s, y)], color, 2.4 * s, rough=False)
        ink.line([(x - 3 * s, y + 5 * s), (x + 3 * s, y + 5 * s)], color, 1.4 * s, rough=False)
        return
    ink.line([(x - 7 * s, y), (x - 2 * s, y + 6 * s), (x + 8 * s, y - 7 * s)], color, 2.6 * s, rough=False)


def chip(ink, x, y, b, on=True, dark=False):
    c = BRASS if on else (RULE if not dark else (70, 66, 70))
    ink.circle(x, y, 13, fill=c, color=None, width=0, rough=False)
    ink.text((x, y + 1), b, "mono", 12, NIGHT if on else MUTED, anchor="mm")


# -------------------------------------------------------------- sections ---

def s_title(ink, lt):
    ink.text((W / 2, 210), "Exercices de style", "serif", 70, INK, anchor="mm")
    ink.label((W / 2, 272), "one station incident · a baseline and four retellings", 16, MUTED, anchor="mm")
    ink.label((W / 2, 298), "each retelling applies one rule you can see working", 14, ACCENT, anchor="mm")


def s_base(ink, lt):
    header(ink, "base")
    for k, (b, tm, s) in enumerate(LEDGER):
        a = ease(lt, 0.4 + k * 1.05, 0.8 + k * 1.05)
        if a <= 0:
            continue
        y = 150 + k * 56
        dx = (1 - a) * 30
        chip(ink, 64, y + 14, b)
        ink.label((96 + dx, y + 6), tm, 15, MUTED, alpha=int(255 * a))
        ink.text((170 + dx, y), s, "serif", 27, INK, alpha=int(255 * a))
    if lt > 7.2:
        ink.caption("Every retelling below must keep these six facts, or record what it leaves out.", ease(lt, 7.2, 7.5), size=19)


def s_reverse(ink, lt):
    header(ink, "A")
    # clock running backwards 07:15:40 -> 07:11:20
    t0, t1 = 15 * 60 + 40, 11 * 60 + 20
    f = ease(lt, 0.3, 7.5)
    now = t0 + (t1 - t0) * f
    m, s = int(now // 60), int(now % 60)
    ink.text((920, 30), f"07:{m:02d}:{s:02d}", "mono", 30, ACCENT, anchor="ra")
    ink.label((920, 70), "clock runs back", 12, MUTED, anchor="ra")
    shown = []
    for k, (stamp, text, b) in enumerate(REVERSE):
        hh, mm, ss = (int(v) for v in stamp.split(":"))
        sec = mm * 60 + ss
        if now <= sec + 0.5:
            shown.append(k)
    for k in shown:
        stamp, text, b = REVERSE[k]
        y = 150 + k * 52
        hh, mm, ss = (int(v) for v in stamp.split(":"))
        appear = (t0 - (mm * 60 + ss)) / (t0 - t1) * 7.2 + 0.3
        txt = typed(text, lt, appear, 60)
        ink.label((50, y + 4), stamp, 17, ACCENT)
        ink.text((160, y), txt, "mono", 19, INK)
        chip(ink, 790, y + 14, b)
    # causal arrows: drawn once the log is complete, still running cause -> effect (upward)
    if lt > 8.0:
        a = ease(lt, 8.0, 9.0)
        for k in range(5):
            y_cause = 150 + (k + 1) * 52 + 14
            y_eff = 150 + k * 52 + 14
            x = 836 + (k % 2) * 22
            yy = lerp(y_cause, y_eff, a)
            ink.line([(x, y_cause), (x, yy)], ACCENT, 2.2, rough=False)
            if a > 0.95:
                ink.poly([(x - 6, y_eff + 10), (x + 6, y_eff + 10), (x, y_eff + 1)], fill=ACCENT, color=None, rough=False)
        ink.label((900, 470), "arrows: cause -> effect", 12, ACCENT, anchor="ra")
        ink.caption("Read top to bottom, time runs back. The arrows still point forward.", ease(lt, 9.0, 9.3), size=19)


_blur_cache = {}


def blurred_text(s, size, radius):
    key = (s, size, radius)
    if key not in _blur_cache:
        f = font("serif", size)
        tmp = ImageDraw.Draw(Image.new("L", (1, 1)))
        bx = tmp.textbbox((0, 0), s, font=f)
        im = Image.new("RGBA", (bx[2] + 20, bx[3] + 20), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((10, 10), s, font=f, fill=INK + (255,))
        _blur_cache[key] = im.filter(ImageFilter.GaussianBlur(radius))
    return _blur_cache[key]


def s_sense(ink, lt):
    header(ink, "B")
    # frosted pane, left
    colx = {"SEEN (frosted)": 50, "HEARD": 360, "SMELLED": 690}
    for c, x in colx.items():
        ink.label((x, 126), c, 14, ACCENT)
        ink.line([(x, 148), (x + 270, 148)], RULE, 1, rough=False)
    rows = {c: 160 for c in SENSE_COLS}
    for at, col, text, b in SENSE:
        if lt < at:
            continue
        a = ease(lt, at, at + 0.4)
        x = colx[col]
        y = rows[col]
        lines = wrap(ink, text, "serif", 23, 250)
        rows[col] += 26 * len(lines) + 22
        for i, line in enumerate(lines):
            if col.startswith("SEEN"):
                im = blurred_text(line, 23, 1.0 + 3 * (1 - a))
                ink.paste(im, (x - 10, y - 10 + i * 26), alpha=a)
            else:
                ink.text((x + (1 - a) * 14, y + i * 26), line, "serif", 23, INK, alpha=int(255 * a))
        if b:
            chip(ink, x + 258, y + 10, b) if False else ink.label((x + 270, y + 2), b, 11, BRASS, anchor="ra")
    if lt > 8.6:
        a = ease(lt, 8.6, 9.0)
        ink.d.rectangle([50, 440, 910, 474], fill=WASH + (int(255 * a),))
        ink.label((62, 449), OMIT, 13, ACCENT, alpha=int(255 * a))


def s_notice(ink, lt):
    header(ink, "C")
    x0, y0, x1 = 120, 124, 840
    ink.rect(x0, y0, x1, y0 + 384, fill=PAGE, color=INK, width=2, rough=False)
    ink.d.rectangle([x0, y0, x1, y0 + 36], fill=INK)
    ink.text((x0 + 16, y0 + 8), "STATION INCIDENT NOTICE", "mono", 18, PAGE)
    ink.text((x1 - 16, y0 + 8), "No. 0712", "mono", 18, PAGE, anchor="ra")
    # boxes are there from frame one; content types in
    cps = 34
    at = 0.6
    for k, (lab, val, b) in enumerate(FORM):
        y = y0 + 46 + k * 30
        ink.line([(x0, y + 28), (x1, y + 28)], RULE, 1, rough=False)
        ink.line([(x0 + 230, y), (x0 + 230, y + 28)], RULE, 1, rough=False)
        ink.label((x0 + 14, y + 7), lab, 13, MUTED)
        ink.text((x0 + 246, y + 4), typed(val, lt, at, cps), "mono", 17, INK)
        at += len(val) / cps + 0.12
    if lt > at + 0.3:
        a = ease(lt, at + 0.3, at + 0.5)
        s = 1 + 0.6 * (1 - a)
        stamp = Image.new("RGBA", (260, 90), (0, 0, 0, 0))
        dd = ImageDraw.Draw(stamp)
        dd.rectangle([4, 4, 255, 85], outline=ACCENT + (210,), width=5)
        dd.text((130, 46), "FILED · NO ACTION", font=font("mono", 22), fill=ACCENT + (210,), anchor="mm")
        stamp = stamp.resize((int(260 * s), int(90 * s))).rotate(-9, expand=True, resample=Image.BICUBIC)
        ink.paste(stamp, (775 - stamp.width / 2, 488 - stamp.height / 2), alpha=a)


def s_key(ink, lt):
    light = ease(lt, LIGHT_AT, LIGHT_AT + 0.8)
    bg = mix_color(NIGHT, PAPER, light)
    ink.fill(bg)
    header(ink, "D", dark=light < 0.5)
    for at, text, b in KEY_LINES:
        if lt < at:
            continue
        k = KEY_LINES.index((at, text, b))
        a = ease(lt, at, at + 0.6)
        y = 140 + k * 54
        col = mix_color(PAGE, INK, light) if at < LIGHT_AT else INK
        ink.text((96 + (1 - a) * 20, y), text, "serif", 30, col, alpha=int(255 * a))
        ink.label((880, y + 12), b, 11, BRASS, anchor="ra", alpha=int(255 * a))
    # the speaker, small, bottom right: on the bench after line 5
    if lt > 6.8:
        a = ease(lt, 6.8, 7.3)
        ink.rect(560, 470, 900, 482, fill=(150, 110, 70), color=INK, width=1.5, alpha=int(255 * a), rough=False)
        key_shape(ink, 690, 462, 1.0)


def s_matrix(ink, lt):
    ink.text((W / 2, 50), "One incident, five tellings", "serif", 40, INK, anchor="mm")
    ink.label((W / 2, 90), "rows: each telling and its single rule · columns: the six ledger beats", 13, MUTED, anchor="mm")
    cx0 = 470
    for j in range(6):
        chip(ink, cx0 + j * 64, 136, f"b{j + 1}")
    for i, (name, rule, marks) in enumerate(MATRIX):
        y = 186 + i * 54
        a = ease(lt, 0.3 + i * 0.3, 0.6 + i * 0.3)
        ink.text((60, y - 12), name, "serif", 26, INK, alpha=int(255 * a))
        ink.label((260, y - 4), rule, 13, MUTED, alpha=int(255 * a))
        ink.line([(60, y + 22), (880, y + 22)], RULE, 1, rough=False)
        for j, m in enumerate(marks):
            if a > 0.9:
                tick(ink, cx0 + j * 64, y, 1.1, ACCENT, partial=(m == "~"))
    if lt > 2.4:
        ink.label((W / 2, 470), "~ = present only as a glint; the omission is declared in B", 13, ACCENT, anchor="mm")
        ink.label((W / 2, 494), "no telling adds an ending · the visitor always leaves · the door never opens", 13, MUTED, anchor="mm")


@film.picture
def frame(t, ink):
    a, b, k = section_at(t)
    lt = t - a
    ink.paper()
    {"title": s_title, "base": s_base, "A": s_reverse, "B": s_sense, "C": s_notice, "D": s_key, "matrix": s_matrix}[k](ink, lt)
    fade = min(1, lt / 0.3, (b - t) / 0.3)
    if fade < 1:
        ink.d.rectangle([0, 0, W, H], fill=PAPER + (int(255 * (1 - fade)),))


# ----------------------------------------------------------------- sound ---

def typewriter(mix, at, n, cps, gain=0.15):
    for k in range(n):
        mix.click(at + k / cps + mix.rs.uniform(-0.008, 0.008), gain * mix.rs.uniform(0.6, 1.0), mix.rs.uniform(-0.2, 0.2), 4500, 0.02)


@film.sound
def sound(mix):
    R = mix.rate
    mix.room(0, 67, gain=0.012)
    # baseline: one soft pencil tap per beat
    for k in range(6):
        mix.click(3.0 + 0.4 + k * 1.05, 0.12, 0, 1500)
        mix.note(3.0 + 0.4 + k * 1.05, [262, 294, 330, 349, 392, 440][k], 0.6, 0.05, 0, "sine")
    # A: reversed ticks (swelling attack, sudden stop) and the log typing in
    a = 12.5
    for k in range(int(8 / 0.5)):
        n = int(0.12 * R)
        x = mix.band(mix.noise(0.12), 800, 4000) * np.linspace(0, 1, n) ** 3
        mix.add(x, a + 0.3 + k * 0.5, 0.12)
    for k, (stamp, text, b) in enumerate(REVERSE):
        mm, ss = int(stamp.split(":")[1]), int(stamp.split(":")[2])
        appear = ((15 * 60 + 40) - (mm * 60 + ss)) / (260) * 7.2 + 0.3
        typewriter(mix, a + appear, min(len(text), 40), 60, 0.06)
    # B: the actual sounds, each when the clerk notes it
    a = 24.0
    mix.steps(a + 0.6, a + 1.6, 0.45, 0.1, "stone", -0.6, -0.2)
    mix.bell(a + 2.1, 523, 3.0, 0.25, -0.2)
    mix.add(mix.band(mix.noise(0.45), 1500, 7000) * np.exp(-np.linspace(0, 4, int(0.45 * R))), a + 3.3, 0.14)
    mix.click(a + 5.2, 0.3, 0.1, 2500)
    mix.thud(a + 5.2, 240, 0.12, 0.1, 0.1)
    mix.steps(a + 6.2, a + 8.0, 0.45, 0.1, "stone", 0.0, -0.9)
    # C: typewriter through the form, carriage bell, stamp
    a = 36.0
    at = 0.6
    for lab, val, b in FORM:
        typewriter(mix, a + at, len(val), 34, 0.13)
        at += len(val) / 34 + 0.12
        mix.note(a + at - 0.1, 2100, 0.25, 0.03, 0, "sine")
    mix.thud(a + at + 0.35, 80, 0.5)
    mix.click(a + at + 0.35, 0.3, 0, 2000)
    # D: inside the envelope (muffled), then the room opens
    a = 48.0
    mix.drone(a, LIGHT_AT + 0.4, (55, 82.5), gain=0.06, attack=0.6, release=0.4)
    tt = mix.t(2.0)
    muffled = mix.lowpass(sum(np.sin(2 * np.pi * 523 * r * tt) * np.exp(-tt * 2) for r in (0.5, 1, 1.19, 2)), 500)
    mix.add(muffled / np.abs(muffled).max(), a + 2.0, 0.2)
    mix.add(mix.band(mix.noise(0.4), 1500, 8000) * np.exp(-np.linspace(0, 4, int(0.4 * R))), a + 3.6, 0.25)
    mix.drone(a + LIGHT_AT, 12 - LIGHT_AT, (220, 330, 440), gain=0.025)
    mix.click(a + 6.8, 0.3, 0.1, 2500)
    mix.thud(a + 6.8, 240, 0.12, 0.1, 0.1)
    mix.steps(a + 8.4, a + 10.4, 0.45, 0.1, "stone", 0.2, 0.9)
    # matrix: one chord
    for k, f in enumerate((262, 330, 392, 523)):
        mix.pluck(60.3 + k * 0.08, f, 2.5, 0.12, -0.3 + 0.2 * k)
    mix.reverb(0.12)


if __name__ == "__main__":
    run(film)

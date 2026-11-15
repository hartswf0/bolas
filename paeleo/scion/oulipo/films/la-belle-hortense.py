"""La Belle Hortense — station. Six modules, six motifs (key, bell, coat, bench, receipt,
locked door). Each module uses every motif exactly once, in an order produced by applying
the sextine permutation [6,1,5,2,4,3] to the previous module's order. The motif chips
visibly travel to their new places between modules. Module 1 is the station episode;
the coat is background there and evidence by module 5."""
import math
import re
from kit import *
from kit_anim import run, hatch_poly

film = Film("la-belle-hortense", seconds=71.0, boil=0, wobble=0, seed=4)
film.poster_at = 47.0

MOTIF = {"A": "key", "B": "bell", "C": "coat", "D": "bench", "E": "receipt", "F": "door"}
PERM = [6, 1, 5, 2, 4, 3]


def permute(order):
    return [order[p - 1] for p in PERM]


ORDERS = [list("ABCDEF")]
for _ in range(6):
    ORDERS.append(permute(ORDERS[-1]))
assert ORDERS[1] == list("FAEBDC") and ORDERS[6] == list("ABCDEF")

MODULES = [
    ("07:11", "the platform", [
        "07:11. A visitor arrives with a sealed envelope; it holds a brass KEY.",
        "The BELL rings once. Nobody comes.",
        "Someone's folded COAT lies drying at the far end, its pocket torn.",
        "The visitor sets the find on the near end of the BENCH and leaves.",
        "Underfoot, a café RECEIPT: ordinary litter.",
        "The service DOOR stays shut.",
    ]),
    ("08:00", "the porter", [
        "08:00. The porter tries the service DOOR: still locked.",
        "The visitor's KEY is gone.",
        "The café clerk writes a RECEIPT for every tea.",
        "The porter says the 07:20 BELL sent him running to Platform 2.",
        "He says he never sat on the BENCH.",
        "His COAT is on his back now, dry.",
    ]),
    ("08:20", "the clerk", [
        "The clerk remembers a folded COAT, then none.",
        "Only the station-master opens the service DOOR, and he is away.",
        "She saw the porter sit down on the BENCH with his tea.",
        "She saw no KEY. She wasn't looking for one.",
        "When the BELL went, he jumped up, grabbing his things.",
        "Her book holds a RECEIPT: one tea, 07:19.",
    ]),
    ("08:40", "the litter", [
        "The porter's own RECEIPT turns up underfoot: 07:19, one tea.",
        "So he sat, on his folded COAT, to keep dry.",
        "At the BELL he snatched it up in one movement.",
        "Now it hangs on the hook by the service DOOR.",
        "On the platform there is still no KEY.",
        "The BENCH is searched slat by slat: empty.",
    ]),
    ("09:00", "the hook", [
        "On the BENCH: the find set down at 07:15, the porter seated at 07:19.",
        "The RECEIPT and the clerk agree on that.",
        "Whoever has the KEY may not know it.",
        "On its hook, the COAT hangs crooked, heavy on one side.",
        "It swings against the DOOR with a small metal tick.",
        "The BELL for the 09:05 has not rung yet.",
    ]),
    ("09:05", "the lining", [
        "The 09:05 BELL rings. Nobody boards.",
        "The clerk lays the porter's things along the BENCH.",
        "Not the service DOOR: that was never the question.",
        "The RECEIPT, the tea, the hurry, the snatch.",
        "She shakes the COAT. The torn pocket rattles.",
        "Out of the lining slides the brass KEY.",
    ]),
]

# hard checks: each module uses every motif exactly once, in the permuted order
WORDS = {v: re.compile(r"\b" + v + r"s?\b", re.I) for v in MOTIF.values()}
for m, (_, _, lines) in enumerate(MODULES):
    for k, line in enumerate(lines):
        want = MOTIF[ORDERS[m][k]]
        for w, rx in WORDS.items():
            n = len(rx.findall(line))
            assert n == (1 if w == want else 0), (m + 1, k + 1, w, line)

TITLE = (0.0, 3.0)
MOD = 9.8
STARTS = [3.0 + i * MOD for i in range(5)]
PAUSE = (STARTS[-1] + MOD, STARTS[-1] + MOD + 2.4)
STARTS.append(PAUSE[1])
END = (STARTS[-1] + MOD, 71.0)
TRANS = 1.2
LINE0, LINE_GAP = 1.4, 1.3

CHIP_Y = 150
CHIP_X0, CHIP_DX, CHIP_W = 78, 136, 124


def chip_x(i):
    return CHIP_X0 + i * CHIP_DX + CHIP_W / 2


# ---------------------------------------------------------------- icons ---

def icon(ink, letter, cx, cy, s=1.0, col=INK):
    if letter == "A":
        key_shape(ink, cx - 16 * s, cy, 0.8 * s)
    elif letter == "B":
        ink.poly([(cx - 12 * s, cy + 10 * s), (cx + 12 * s, cy + 10 * s), (cx + 7 * s, cy - 10 * s), (cx - 7 * s, cy - 10 * s)], fill=BRASS, color=col, width=1.6, rough=False)
        ink.circle(cx, cy + 13 * s, 3 * s, fill=col, color=None, width=0, rough=False)
    elif letter == "C":
        ink.poly([(cx - 6 * s, cy - 13 * s), (cx + 6 * s, cy - 13 * s), (cx + 14 * s, cy - 6 * s), (cx + 11 * s, cy + 14 * s), (cx - 11 * s, cy + 14 * s), (cx - 14 * s, cy - 6 * s)],
                 fill=(92, 104, 120), color=col, width=1.6, rough=False)
        ink.line([(cx, cy - 13 * s), (cx, cy + 14 * s)], PAGE, 1.2, rough=False)
    elif letter == "D":
        ink.rect(cx - 18 * s, cy - 2 * s, cx + 18 * s, cy + 3 * s, fill=(150, 110, 70), color=col, width=1.4, rough=False)
        ink.rect(cx - 18 * s, cy - 12 * s, cx + 18 * s, cy - 8 * s, fill=(150, 110, 70), color=col, width=1.4, rough=False)
        for x in (cx - 14 * s, cx + 14 * s):
            ink.line([(x, cy + 3 * s), (x, cy + 13 * s)], col, 2, rough=False)
    elif letter == "E":
        pts = [(cx - 10 * s, cy - 14 * s), (cx + 10 * s, cy - 14 * s), (cx + 10 * s, cy + 12 * s)]
        for k in range(5):
            pts.append((cx + 10 * s - (k + 0.5) * 4 * s, cy + (14 if k % 2 == 0 else 10) * s))
        pts.append((cx - 10 * s, cy + 12 * s))
        ink.poly(pts, fill=PAGE, color=col, width=1.4, rough=False)
        for k in range(3):
            ink.line([(cx - 6 * s, cy - 8 * s + k * 6 * s), (cx + 6 * s, cy - 8 * s + k * 6 * s)], MUTED, 1, rough=False)
    elif letter == "F":
        ink.rect(cx - 10 * s, cy - 15 * s, cx + 10 * s, cy + 15 * s, fill=(120, 96, 80), color=col, width=1.6, rough=False)
        ink.circle(cx + 5 * s, cy, 2 * s, fill=BRASS, color=None, width=0, rough=False)


def chip(ink, letter, cx, cy, hot=0.0, evidence=False):
    x0, x1 = cx - CHIP_W / 2, cx + CHIP_W / 2
    fill = mix_color(PAGE, (246, 226, 214), hot)
    ink.rect(x0, cy - 26, x1, cy + 26, fill=fill, color=ACCENT if hot > 0.5 else RULE, width=2 if hot > 0.5 else 1.4, rough=False)
    icon(ink, letter, x0 + 28, cy, 0.9)
    ink.text((x0 + 54, cy - 13), MOTIF[letter], "serif", 22, INK)
    ink.label((x1 - 8, cy + 8), letter, 11, MUTED, anchor="ra")
    if evidence:
        ink.d.rectangle([x0, cy + 28, x1, cy + 46], fill=ACCENT)
        ink.label((cx, cy + 30), "now evidence", 11, PAGE, anchor="ma")


# --------------------------------------------------------------- frames ---

def rich_line(ink, x, y, s, size, alpha, hot_letter):
    """Draw s with its single upper-case motif word in accent."""
    f = font("serif", size)
    m = re.search(r"\b(KEY|BELL|COAT|BENCH|RECEIPT|DOOR)\b", s)
    parts = [(s, INK)] if not m else [(s[:m.start()], INK), (m.group(1).lower(), ACCENT), (s[m.end():], INK)]
    for txt, col in parts:
        if not txt:
            continue
        ink.text((x, y), txt, "serif", size, col, alpha=alpha)
        if col == ACCENT:
            w = f.getlength(txt)
            ink.d.line([(x, y + size + 3), (x + w, y + size + 3)], fill=ACCENT + (alpha,), width=2)
        x += f.getlength(txt)


def order_strip(ink, upto, current=None):
    x = 40
    for m in range(6):
        s = "".join(ORDERS[m])
        col = ACCENT if m == current else (INK if m < upto else RULE)
        ink.text((x, 500), s, "mono", 17, col)
        ink.label((x, 482), f"M{m + 1}", 10, MUTED)
        x += 92
    ink.label((W - 40, 500), "next[i] = prev[p(i)] · p = 6 1 5 2 4 3", 12, MUTED, anchor="ra")


def module_frame(ink, m, lt):
    clock, place, lines = MODULES[m]
    order = ORDERS[m]
    prev = ORDERS[m - 1] if m > 0 else None
    # header
    ink.text((40, 22), f"Module {m + 1}", "serif", 40, INK)
    ink.label((210, 38), f"{clock} · {place}", 15, MUTED)
    ink.label((W - 40, 38), "order  " + " ".join(order), 15, ACCENT, anchor="ra")
    ink.line([(40, 80), (920, 80)], RULE, 1.2, rough=False)
    # chips: travel from previous slot to new slot during the transition
    u = ease(lt, 0.1, TRANS)
    for i, letter in enumerate(order):
        x_new = chip_x(i)
        if prev is None:
            a = ease(lt, 0.1 + i * 0.12, 0.4 + i * 0.12)
            x, y = x_new, CHIP_Y + (1 - a) * 20
            if a <= 0:
                continue
        else:
            j = prev.index(letter)
            x_old = chip_x(j)
            x = lerp(x_old, x_new, u)
            y = CHIP_Y - math.sin(math.pi * u) * (14 + 7 * abs(i - j))
            if 0 < u < 1:
                path = [(lerp(x_old, x_new, q / 16), CHIP_Y - 26 - math.sin(math.pi * q / 16) * (14 + 7 * abs(i - j))) for q in range(17)]
                ink.line(path, ACCENT, 1.4, rough=False, alpha=110)
        k_line = i
        hot = 0.0
        t_line = LINE0 + k_line * LINE_GAP
        if t_line <= lt < t_line + LINE_GAP:
            hot = ease(lt, t_line, t_line + 0.2)
        evidence = (m == 4 and letter == "C" and lt > LINE0 + 3 * LINE_GAP) or (m == 3 and letter == "E" and lt > LINE0)
        chip(ink, letter, x, y, hot, evidence)
        ink.label((x - CHIP_W / 2, CHIP_Y - 40), str(i + 1), 11, MUTED) if u >= 1 or prev is None else None
    if prev is not None and lt < TRANS + 0.4:
        ink.label((W / 2, CHIP_Y + 40), "apply [6,1,5,2,4,3]: slot i takes the motif from slot p(i)", 13, ACCENT, anchor="ma")
    # the six sentences, one per slot
    for k, s in enumerate(lines):
        t_line = LINE0 + k * LINE_GAP
        if lt < t_line:
            continue
        a = ease(lt, t_line, t_line + 0.35)
        y = 206 + k * 44
        ink.label((48, y + 8), f"{k + 1}", 13, ACCENT if t_line <= lt < t_line + LINE_GAP else MUTED)
        rich_line(ink, 74 + (1 - a) * 16, y, s, 24, int(255 * a), order[k])
    order_strip(ink, m + 1, m)


def title_frame(ink, lt):
    ink.text((W / 2, 190), "La Belle Hortense", "serif", 70, INK, anchor="mm")
    ink.label((W / 2, 250), "a station mystery in six modules", 16, MUTED, anchor="mm")
    ink.label((W / 2, 276), "six motifs, once each per module · order turned by the sextine [6,1,5,2,4,3]", 14, ACCENT, anchor="mm")
    for i, l in enumerate("ABCDEF"):
        a = ease(lt, 0.6 + i * 0.12, 0.9 + i * 0.12)
        if a > 0:
            chip(ink, l, chip_x(i), 380 + (1 - a) * 20)


def pause_frame(ink, lt):
    ink.fill(NIGHT)
    ink.text((W / 2, 220), "Pause.", "serif", 64, PAGE, anchor="mm")
    ink.text((W / 2, 290), "Where did the visitor's find go? Everything you need has been shown.", "serif", 26, RULE, anchor="mm")
    ink.label((W / 2, 340), "name your answer, and the motif that changed your mind", 14, BRASS, anchor="mm")


def end_frame(ink, lt):
    ink.text((W / 2, 40), "The grid", "serif", 38, INK, anchor="mm")
    ink.label((W / 2, 74), "six modules · every motif once per row · a seventh turn returns the first order", 13, MUTED, anchor="mm")
    gx0, gy0, dx, dy = 300, 110, 62, 54
    cols = {"A": BRASS, "B": (120, 140, 90), "C": (92, 104, 120), "D": (150, 110, 70), "E": MUTED, "F": ACCENT}
    rows = 7
    # paths of each motif through the grid
    for l in "ABCDEF":
        a = ease(lt, 0.4, 2.4)
        pts = [(gx0 + ORDERS[r].index(l) * dx, gy0 + r * dy) for r in range(rows)]
        n = max(1, int(a * (rows - 1) * 10))
        path = []
        for q in range(n + 1):
            f = q / 10
            r = min(rows - 2, int(f))
            path.append(lerp2(pts[r], pts[r + 1], f - r))
        if len(path) > 1:
            ink.line(path, cols[l], 3 if l == "A" else 1.8, rough=False, alpha=230 if l in "AC" else 120)
    for r in range(rows):
        ink.label((gx0 - 60, gy0 + r * dy - 8), f"M{r + 1}" if r < 6 else "(M7)", 13, MUTED if r < 6 else ACCENT)
        for i, l in enumerate(ORDERS[r]):
            x, y = gx0 + i * dx, gy0 + r * dy
            ink.circle(x, y, 19, fill=PAGE, color=cols[l], width=2.2, rough=False)
            icon(ink, l, x + (4 if l == "A" else 0), y, 0.62)
    ink.label((700, 120), "key  (bold path)", 13, BRASS)
    ink.label((700, 144), "coat: background in M1,", 13, (92, 104, 120))
    ink.label((700, 162), "evidence by M5", 13, (92, 104, 120))
    if lt > 2.6:
        a = ease(lt, 2.6, 3.0)
        ink.label((700, 210), "clue chain", 13, ACCENT, alpha=int(255 * a))
        chain = ["M1·3 coat on the bench", "M3·3 porter sits there", "M4·2 sits on his coat", "M4·3 snatches it at the bell",
                 "M5·4 it hangs heavy", "M5·5 metal tick", "M6·6 the key falls out"]
        for k, c in enumerate(chain):
            ink.label((700, 232 + k * 20), c, 12, INK, alpha=int(255 * a))


@film.picture
def frame(t, ink):
    ink.paper()
    if t < TITLE[1]:
        title_frame(ink, t)
        lt, span = t, TITLE[1]
    elif PAUSE[0] <= t < PAUSE[1]:
        pause_frame(ink, t - PAUSE[0])
        lt, span = t - PAUSE[0], PAUSE[1] - PAUSE[0]
    elif t >= END[0]:
        end_frame(ink, t - END[0])
        lt, span = t - END[0], 99
    else:
        m = max(i for i, s in enumerate(STARTS) if s <= t)
        lt = t - STARTS[m]
        span = MOD
        module_frame(ink, m, lt)
    fade = min(1, lt / 0.25, (span - lt) / 0.25)
    if fade < 1:
        ink.d.rectangle([0, 0, W, H], fill=PAPER + (int(255 * (1 - fade)),))


# ----------------------------------------------------------------- sound ---

def motif_sound(mix, letter, at):
    R = mix.rate
    if letter == "A":  # key: a small bright clink
        tt = mix.t(0.6)
        sig = (np.sin(2 * np.pi * 2630 * tt) + 0.6 * np.sin(2 * np.pi * 3710 * tt)) * np.exp(-tt * 9)
        mix.add(sig, at, 0.12, 0.2)
    elif letter == "B":
        mix.bell(at, 523, 2.4, 0.22, -0.2)
    elif letter == "C":  # coat: cloth swish
        x = mix.band(mix.noise(0.35), 150, 1400) * np.hanning(int(0.35 * R))
        mix.add(x, at, 0.22, 0.1)
    elif letter == "D":  # bench: knock on wood
        mix.thud(at, 210, 0.2, 0.0, 0.12)
        mix.click(at, 0.15, 0, 1800)
    elif letter == "E":  # receipt: a short paper tear
        x = mix.band(mix.noise(0.22), 2000, 8000) * np.exp(-np.linspace(0, 3, int(0.22 * R)))
        mix.add(x, at, 0.1, 0.3)
    elif letter == "F":  # locked door: a latch that doesn't give
        mix.thud(at, 65, 0.35)
        mix.click(at + 0.05, 0.2, -0.2, 2500)


@film.sound
def sound(mix):
    mix.room(0, 71, gain=0.012)
    for i, l in enumerate("ABCDEF"):
        mix.click(0.6 + i * 0.12, 0.08, -0.5 + 0.2 * i, 2000)
    for m, start in enumerate(STARTS):
        if m > 0:
            mix.whoosh(start + 0.1, 1.0, 0.06)
            for i in range(6):
                mix.click(start + TRANS - 0.05 + i * 0.015, 0.06, -0.5 + 0.2 * i, 3000)
        for k, letter in enumerate(ORDERS[m]):
            motif_sound(mix, letter, start + LINE0 + k * LINE_GAP)
    mix.drone(PAUSE[0], 2.4, (73.4, 110), gain=0.05, attack=0.3, release=0.6)
    for k, f in enumerate((262, 330, 392, 523, 659, 784)):
        mix.pluck(END[0] + 0.4 + k * 0.33, f, 1.6, 0.1, -0.5 + 0.2 * k)
    mix.reverb(0.12)


if __name__ == "__main__":
    run(film)

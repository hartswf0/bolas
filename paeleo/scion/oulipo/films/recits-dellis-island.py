"""Récits d'Ellis Island — a closed halt, then two witnesses who disagree.

Movement 1 (25 s): what the site shows. An empty platform, a painted notice
with a date, the bench, an undated station diagram. No voices.
Movement 2 (25 s): what two staged, fictional witnesses say about the last
train. Each line is attributed (speaker, segment timecode, staged label).
They agree on the seed (envelope, key on the bench, service door shut) and
disagree on one detail: whether the bell rang before or after the key was
put down. The cut carries both and ends on the unresolved ledger.
"""
import math
from PIL import Image
from kit_cinema_a import *

GRASS = (118, 128, 92)
SKY = (204, 210, 204)
BRICK = (168, 120, 96)
INKC = INK
A_COL = (150, 60, 70)
B_COL = (52, 86, 120)

M = 25.0
SEGS = [("title", 2.2), ("card1", 1.6), ("m1", M), ("card2", 1.6), ("m2", M)]
TOTAL = sum(d for _, d in SEGS)
ST = starts(SEGS)
M1 = [("pan", 8.0), ("notice", 7.0), ("bench", 6.0), ("diagram", 4.0)]
M2 = [("witA", 4.6), ("benchA", 5.0), ("witB", 4.6), ("benchB", 5.0), ("ledger", 5.8)]
LINES = {"witA": ("A", "MARTHE V.", "The last train was the 18:40. A woman got off it with an envelope.", "seg A 00:14–00:19"),
         "benchA": ("A", "MARTHE V.", "The bell rang first. Then she put the key on the bench, as if told to.", "seg A 00:20–00:25"),
         "witB": ("B", "PAUL R.", "She was already on the bench when the train came in. She had a letter.", "seg B 01:02–01:07"),
         "benchB": ("B", "PAUL R.", "She put the key down before anything. The bell only rang as it pulled out.", "seg B 01:08–01:13")}


def build_platform():
    w, h = 1500, 540
    ink = Ink(0, 0, (w, h), boil=0, wobble=1.1, seed=12)
    ink.paper(SKY)
    # station building
    ink.rect(260, 110, 980, 330, fill=BRICK, color=INK, width=3)
    for y in range(126, 330, 16):
        ink.line([(260, y), (980, y)], (140, 98, 80), 1, alpha=160)
    ink.poly([(230, 110), (1010, 110), (950, 60), (290, 60)], fill=(90, 84, 82), color=INK, width=3)
    for x in (320, 470, 780):
        ink.rect(x, 160, x + 90, 280, fill=(150, 130, 100), color=INK, width=2.5)
        for k in range(4):
            ink.line([(x, 175 + k * 30), (x + 90, 185 + k * 28)], (110, 86, 64), 5)
    door(ink, 650, 330, 80, 150, fill=(96, 84, 76), sign="SERVICE")
    ink.rect(520, 72, 720, 100, fill=PAGE, color=INK, width=2)
    ink.text((620, 86), "SAINT-ORY", "serif", 22, INK, anchor="mm")
    # bell bracket
    ink.line([(900, 150), (940, 150), (940, 160)], INK, 3)
    ink.circle(940, 172, 12, fill=BRASS, color=INK, width=2)
    # notice board
    ink.rect(1040, 170, 1140, 300, fill=(120, 110, 96), color=INK, width=2)
    ink.rect(1050, 182, 1130, 248, fill=(226, 218, 196), color=INK, width=1.5)
    ink.line([(1090, 300), (1090, 330)], INK, 3)
    # platform and track
    ink.d.rectangle([0, 330, w, 400], fill=(170, 166, 156))
    ink.line([(0, 330), (w, 330)], INK, 2)
    ink.line([(0, 400), (w, 400)], INK, 3)
    ink.d.rectangle([0, 400, w, h], fill=(120, 108, 92))
    for x in range(0, w, 34):
        ink.rect(x, 438, x + 18, 500, fill=(90, 70, 54), color=None)
    for y in (450, 486):
        ink.line([(0, y), (w, y)], (80, 80, 84), 4)
    rs = np.random.RandomState(3)
    for _ in range(180):
        x, y = rs.uniform(0, w), rs.uniform(396, 540)
        ink.line([(x, y), (x + rs.uniform(-6, 6), y - rs.uniform(8, 26))], GRASS, 2)
    bench(ink, 1250, 372, 180)
    return ink.img.convert("RGB")


PLAT = build_platform()


def pan_view(f):
    x = lerp(0, 540, f)
    return PLAT.crop((int(x), 0, int(x) + W, H))


def bench_close(ink, t):
    z = 1.65 + 0.06 * t / 5
    cw, ch = W / z, H / z
    cx, cy = min(1250, 1500 - cw / 2), 330
    img = PLAT.resize((W, H), Image.BICUBIC, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))
    ink.paste(img)


def notice(ink, t):
    ink.fill((120, 110, 96))
    ink.hatch(0, 0, W, H, gap=9, angle=80, color=(100, 90, 78), width=1, alpha=140)
    ink.rect(150, 60, 810, 470, fill=(226, 218, 196), color=INK, width=3)
    ink.text((480, 130), "AVIS AU PUBLIC", "serif", 44, INK, anchor="mm")
    ink.text((480, 210), "LAST SERVICE", "mono", 34, INK, anchor="mm")
    ink.text((480, 270), "30 · IX · 1979", "mono", 48, ACCENT, anchor="mm")
    ink.text((480, 340), "18:40  for the coast", "mono", 22, MUTED, anchor="mm")
    for x, y, r in ((230, 400, 40), (700, 110, 28), (610, 420, 34)):
        ink.circle(x, y, r, fill=(120, 110, 96), color=(90, 80, 70), width=1.5)
    for x in (300, 520, 760):
        ink.line([(x, 470), (x + 4, 520)], (140, 84, 50), 3, alpha=150)
    tag(ink, (W / 2, H - 50), "trace · painted notice · reads 30 Sept 1979 · when it was painted: unknown", 12, PAGE, NIGHT, anchor="ma")


def diagram(ink, t):
    ink.fill((232, 228, 214))
    for x in range(0, W, 24):
        ink.line([(x, 0), (x, H)], (210, 214, 214), 1, rough=False)
    for y in range(0, H, 24):
        ink.line([(0, y), (W, y)], (210, 214, 214), 1, rough=False)
    c = (40, 60, 100)
    ink.rect(160, 120, 800, 260, fill=None, color=c, width=2)
    ink.text((480, 150), "BÂTIMENT VOYAGEURS", "mono", 14, c, anchor="mm")
    ink.rect(150, 260, 810, 330, fill=None, color=c, width=2)
    ink.text((210, 295), "QUAI", "mono", 13, c, anchor="mm")
    for y in (370, 400):
        ink.line([(60, y), (900, y)], c, 2)
    ink.rect(660, 280, 740, 300, fill=None, color=c, width=2)
    ink.text((700, 318), "BANC", "mono", 12, c, anchor="mm")
    ink.rect(440, 250, 480, 262, fill=c, color=c, width=1)
    ink.text((460, 236), "PORTE DE SERVICE", "mono", 11, c, anchor="mm")
    ink.circle(620, 250, 7, fill=None, color=c, width=2)
    ink.text((620, 232), "CLOCHE", "mono", 11, c, anchor="mm")
    ink.text((480, 440), "voie 1 · direction côte", "mono", 12, c, anchor="mm")
    tag(ink, (W / 2, H - 50), "trace · station diagram · undated · found in the waiting room", 12, PAGE, NIGHT, anchor="ma")


def portrait(ink, who, t):
    if who == "A":
        ink.fill((206, 196, 176))
        ink.rect(560, 60, 820, 260, fill=(230, 226, 210), color=INK, width=3)  # window
        ink.line([(690, 60), (690, 260)], INK, 2)
    else:
        ink.fill((176, 186, 180))
        ink.rect(120, 80, 360, 240, fill=(150, 120, 90), color=INK, width=3)  # picture on the wall
        ink.poly([(150, 220), (230, 130), (330, 220)], fill=(110, 130, 100), color=INK, width=2)
    ink.d.rectangle([0, 420, W, H], fill=(120, 96, 80))
    ink.line([(0, 420), (W, 420)], INK, 3)
    cx = 470 if who == "A" else 500
    coat = A_COL if who == "A" else B_COL
    ink.poly([(cx - 150, 430), (cx - 110, 320), (cx + 110, 320), (cx + 150, 430)], fill=coat, color=INK, width=3)
    ink.rect(cx - 22, 280, cx + 22, 322, fill=(224, 196, 170), color=INK, width=2)
    ink.ellipse(cx, 230, 66, 80, fill=(224, 196, 170), color=INK, width=3)
    talk = 0.5 + 0.5 * math.sin(t * 17) * math.sin(t * 5.3)
    ink.ellipse(cx, 272, 16, 3 + 6 * talk, fill=(110, 60, 60), color=INK, width=2)
    if who == "A":
        ink.poly([(cx - 74, 230), (cx - 70, 150), (cx, 130), (cx + 70, 150), (cx + 74, 230), (cx + 50, 175), (cx - 50, 175)], fill=(110, 110, 120), color=INK, width=2.5)
        for ex in (cx - 26, cx + 26):
            ink.circle(ex, 228, 17, fill=None, color=INK, width=2.5)
            ink.circle(ex, 228, 4, fill=INK, color=INK, width=1)
        ink.line([(cx - 9, 228), (cx + 9, 228)], INK, 2)
    else:
        ink.poly([(cx - 70, 180), (cx - 60, 140), (cx + 60, 140), (cx + 74, 180), (cx + 110, 186)], fill=(70, 66, 60), color=INK, width=2.5)
        for ex in (cx - 24, cx + 24):
            ink.circle(ex, 222, 4.5, fill=INK, color=INK, width=1)
        ink.stroke([(cx - 30, 258), (cx, 252), (cx + 30, 258)], (90, 80, 70), 9)
    ink.line([(cx - 4, 230), (cx - 10, 252), (cx + 4, 254)], INK, 2)


def lower_third(ink, who, name, seg):
    col = A_COL if who == "A" else B_COL
    ink.d.rectangle([40, 356, 520, 410], fill=PAGE + (235,))
    ink.d.rectangle([40, 356, 48, 410], fill=col + (255,))
    ink.text((62, 360), f"{who} · {name}", "serif", 26, INK)
    ink.text((62, 392), f"fictional witness · staged testimony · {seg}", "mono", 11, MUTED)


def speak(ink, lt, dur, who, name, text):
    al = min(1, (lt - 0.3) / 0.2, (dur - 0.25 - lt) / 0.2)
    if al > 0:
        col = A_COL if who == "A" else B_COL
        ink.caption(f"{name}  “{text}”", alpha=al, size=22, color=col)


def ledger(ink, lt):
    ink.fill(NIGHT)
    ink.text((60, 40), "two accounts · one detail unresolved", "serif", 32, PAGE)
    ink.text((60, 96), "agreed (both accounts, matches the seed): envelope · key left on the bench · service door shut", "mono", 13, RULE)
    for i, (who, name, order) in enumerate((("A", "MARTHE V.", ["bell", "key on bench", "train out"]),
                                            ("B", "PAUL R.", ["key on bench", "train in", "bell (as it leaves)"]))):
        y = 170 + i * 110
        col = A_COL if who == "A" else B_COL
        ink.text((60, y), f"{who} · {name}", "mono", 14, PAGE)
        for k, ev in enumerate(order):
            x = 260 + k * 210
            on = ease(lt, 0.3 + 0.35 * k + i * 0.9, 0.6 + 0.35 * k + i * 0.9)
            fill = (ACCENT if "bell" in ev else BRASS if "key" in ev else (90, 90, 96))
            ink.d.rounded_rectangle([x, y - 6, x + 180, y + 30], 8, fill=fill + (int(255 * on),))
            ink.text((x + 90, y + 12), ev, "mono", 13, PAGE, anchor="mm", alpha=int(255 * on))
            if k:
                ink.line([(x - 26, y + 12), (x - 6, y + 12)], RULE, 2, rough=False)
                ink.poly([(x - 6, y + 12), (x - 14, y + 7), (x - 14, y + 17)], fill=RULE, color=None, rough=False)
    on = ease(lt, 2.6, 3.2)
    ink.text((60, 410), "UNRESOLVED  was the bell before or after the key?", "mono", 16, (236, 160, 170), alpha=int(255 * on))
    ink.text((60, 444), "the bench image shows a bench today; it does not show 1979 or either memory", "mono", 13, RULE, alpha=int(255 * on))
    ink.text((60, 470), "both segments kept in the ledger · consent: staged by the author, labelled", "mono", 13, RULE, alpha=int(255 * on))


film = Film("recits-dellis-island", seconds=TOTAL, boil=4, wobble=1.0)
film.poster_at = ST["m2"] + 7.0


@film.picture
def frame(t, ink):
    seg, lt, dur, _ = segment(t, SEGS)
    if seg == "title":
        title_card(ink, "Récits d’Ellis Island", "a closed halt · what the place shows · what two people say")
    elif seg == "card1":
        title_card(ink, "I · What the site shows", "no voices · traces only", size=42)
    elif seg == "card2":
        title_card(ink, "II · The last train, twice", "two staged, fictional witnesses · attributed", size=42)
    elif seg == "m1":
        s, l2, d2, _ = segment(lt, M1)
        if s == "pan":
            ink.paste(pan_view(ease(l2, 0, d2)))
            tag(ink, (18, 16), "halt of Saint-Ory · closed · drawn 2026", 12, PAGE, NIGHT, alpha=170)
        elif s == "notice":
            notice(ink, l2)
        elif s == "bench":
            bench_close(ink, l2)
            tag(ink, (W / 2, H - 50), "the bench · today · empty", 12, PAGE, NIGHT, anchor="ma")
        else:
            diagram(ink, l2)
        fade_edges(ink, l2, d2, 0.3)
        return
    elif seg == "m2":
        s, l2, d2, _ = segment(lt, M2)
        if s in ("witA", "witB"):
            who, name, text, sg = LINES[s]
            portrait(ink, who, l2)
            lower_third(ink, who, name, sg)
            speak(ink, l2, d2, who, name, text)
        elif s in ("benchA", "benchB"):
            who, name, text, sg = LINES[s]
            bench_close(ink, l2)
            tag(ink, (18, 16), f"image: the bench today · voice: {who} {sg}", 12, PAGE, NIGHT, alpha=170)
            speak(ink, l2, d2, who, name, text)
        else:
            ledger(ink, l2)
        fade_edges(ink, l2, d2, 0.2)
        return
    fade_edges(ink, lt, dur, 0.3)


@film.sound
def sound(mix):
    m1 = ST["m1"]
    mix.wind(m1, M, 0.07)
    rs = mix.rs
    for k in range(14):  # a loose sheet of metal somewhere
        mix.click(m1 + 1 + k * 1.7 + rs.uniform(0, 0.6), 0.05, 0.6, 2500, 0.04)
    for k in range(6):
        t0 = m1 + rs.uniform(0.5, 24)
        tt = mix.t(0.3)
        caw = mix.band(mix.noise(0.3), 700, 2200) * np.hanning(len(tt)) * (0.6 + 0.4 * np.sin(2 * np.pi * 30 * tt))
        mix.add(caw, t0, 0.05, rs.uniform(-0.8, 0.8))
    m2 = ST["m2"]
    a = 0.0
    for name, d in M2:
        t0 = m2 + a
        if name in ("witA", "witB"):
            mix.room(t0, d, 0.03, hum=50 if name == "witA" else 60)
        elif name in ("benchA", "benchB"):
            mix.wind(t0, d, 0.05)
        if name in LINES:
            who = LINES[name][0]
            mix.murmur(t0 + 0.4, d - 0.8, 0.09, 190 if who == "A" else 112, -0.15 if who == "A" else 0.15, seed=len(name) * 7 + (3 if who == "A" else 5))
        if name == "ledger":
            mix.room(t0, d, 0.02)
            mix.bell(t0 + 0.3, 523, 2.0, 0.07, -0.4)       # A: bell first
            mix.click(t0 + 0.65, 0.2, -0.4, 1500, 0.05)
            mix.click(t0 + 1.2, 0.2, 0.4, 1500, 0.05)        # B: key first
            mix.bell(t0 + 1.9, 523, 2.4, 0.07, 0.4)
        a += d


if __name__ == "__main__":
    film.render()

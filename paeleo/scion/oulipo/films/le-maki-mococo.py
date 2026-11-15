"""Le Maki Mococo — a one-minute reading study of an original poem with an unfamiliar name.
Two fictional readers get sound first (Q1), then text (Q2), then an image (Q3).
They guess twice, and one of them reconsiders; the other keeps an alternate."""
import math
from kit_cinema_b import *

SC = Score([(0, 3.5, "title"), (3.5, 15.0, "Q1"), (15.0, 21.0, "R1"), (21.0, 33.0, "Q2"), (33.0, 41.0, "R2"),
            (41.0, 46.0, "Q3"), (46.0, 54.0, "R3"), (54.0, 60.0, "ledger")])
film = Film("le-maki-mococo", seconds=SC.total, boil=6, wobble=1.0, seed=21)
film.poster_at = 43.5

POEM_TITLE = "Mirlocca"
POEM = ["On the bench beside the shut door",
        "the mirlocca sleeps in paper,",
        "folded twice, and does not purr.",
        "When the bell says one, it wakes:",
        "cold and toothed, it fits a dark",
        "it has never seen — and stays."]
LINE_AT = [4.2 + k * 1.75 for k in range(6)]   # murmured reading in Q1
LINE_DUR = 1.45
CUE_SOUNDS = {1: "paper", 3: "bell", 4: "metal"}
ONDINE, BASTIEN = (150, 70, 80), (60, 92, 120)
REPLIES = [  # (start, end, who, line, cues available)
    (15.4, 18.2, "ONDINE", "Something small that rings. A bird with a bell on?", "Q1"),
    (18.2, 20.9, "BASTIEN", "Paper and a bell. A ticket? Something at a station.", "Q1"),
    (33.4, 37.2, "ONDINE", "It sleeps, it has teeth: an animal. A station cat.", "Q1 Q2"),
    (37.2, 40.9, "BASTIEN", "“Does not purr” — so not a cat. A letter? A lock?", "Q1 Q2"),
    (46.4, 50.3, "ONDINE", "Cold, toothed, fits a dark… it's the key. The mirlocca is the key.", "Q1 Q2 Q3"),
    (50.3, 53.9, "BASTIEN", "Or the key is only what the mirlocca left behind.", "Q1 Q2 Q3"),
]


def readers(ink, t, y=470, dark=False, speaking=None, s=0.9):
    col = PAGE if dark else INK
    for x, who, coat, facing in ((120, "ONDINE", ONDINE, 1), (840, "BASTIEN", BASTIEN, -1)):
        lean = 4 if speaking == who else 0
        figure(ink, x + lean * facing, y, s, "sit", 0, facing, color=col, coat=coat, arm=50 if speaking == who else 30)
        sy = y - 120 * s * 0.36
        ink.rect(x - 16, sy, x + 16, sy + 6, fill=MUTED, color=col, width=1.5)  # stool
        for lx in (x - 12, x + 12):
            ink.line([(lx, sy + 6), (lx + (lx - x) * 0.3, y)], col, 1.8)
        ink.label((x, y + 16), who.title() + " · fictional", 11, RULE if dark else MUTED, anchor="mm")


def cue_tag(ink, s, dark=False):
    ink.label((24, 22), s, 14, BRASS if dark else ACCENT)


def sound_stage(ink, t, local):
    ink.fill(NIGHT)
    cue_tag(ink, "Q1 · SOUND ONLY · released 0:03.5 · no text, no image yet", True)
    # oscilloscope of what is heard: murmur cadence per line + the three cue sounds
    cx, cy = W / 2, 230
    amp = 0.0
    tag = ""
    for k, a in enumerate(LINE_AT):
        if a <= t < a + LINE_DUR:
            amp = 0.6 + 0.4 * abs(math.sin((t - a) * 18))
            if k in CUE_SOUNDS and t - a > 0.7:
                tag = {"paper": "rustle", "bell": "bell", "metal": "small metal click"}[CUE_SOUNDS[k]]
    pts = []
    for i in range(0, 721, 6):
        x = 120 + i
        ph = i / 30 + t * 9
        yv = math.sin(ph) * math.sin(i / 720 * math.pi) * (6 + 70 * amp) * (0.7 + 0.3 * math.sin(i / 11 + t * 3))
        pts.append((x, cy + yv))
    ink.line(pts, BRASS, 2.2)
    ink.line([(120, cy), (840, cy)], (70, 70, 80), 1, rough=False)
    # line counter: which unseen line is being murmured
    for k in range(6):
        on = LINE_AT[k] <= t < LINE_AT[k] + LINE_DUR
        done = t >= LINE_AT[k] + LINE_DUR
        ink.rect(330 + k * 50, 330, 366 + k * 50, 342, fill=BRASS if on else ((90, 84, 70) if done else (40, 40, 48)), color=(80, 80, 90), width=1, rough=False)
    ink.label((W / 2, 362), "six murmured lines (no speech synthesis: a voice-like murmur carries the cadence)", 11, RULE, anchor="mm")
    if tag:
        ink.label((W / 2, 300), "heard: " + tag, 14, PAGE, anchor="mm")
    readers(ink, t, dark=True)


def poem_block(ink, x, y, upto=6.0, size=30, color=INK, gap=44, title=True):
    if title:
        ink.text((x, y - 56), POEM_TITLE, "serif", size + 12, ACCENT)
    for k, line in enumerate(POEM):
        a = clamp(upto - k)
        if a <= 0:
            break
        ink.text((x, y + k * gap), line, "serif", size, color, alpha=int(255 * a))


def text_stage(ink, t, local):
    ink.fill(PAGE)
    cue_tag(ink, "Q2 · TEXT · released 0:21 · the same six lines, now readable")
    upto = clamp(local / 1.1, 0, 6.0)
    poem_block(ink, 250, 120, upto)
    readers(ink, t)


def image_drawing(ink, x0, y0, s=1.0, t=0.0):
    """Q3: the bench, the opened envelope, the brass key, the shut door."""
    def P(x, y):
        return (x0 + x * s, y0 + y * s)
    ink.rect(*P(0, 0), *P(420, 300), fill=(236, 228, 210), color=INK, width=2.5)
    ink.hatch(*P(2, 2), *P(418, 298), gap=int(12 * s) or 6, angle=70, color=(190, 180, 160), width=1, alpha=110)
    door(ink, *P(340, 260), w=70 * s, h=150 * s, sign=None)
    ink.d.rectangle([*P(2, 260), *P(418, 298)], fill=(200, 188, 168))
    bench(ink, *P(160, 262), w=230 * s)
    envelope(ink, *P(210, 205), 60 * s, 38 * s, open_=1)
    key_shape(ink, *P(110, 210), 1.6 * s, angle=-0.15)
    bench_key_glint(ink, *P(160, 200), t)


def image_stage(ink, t, local):
    ink.fill(PAGE)
    cue_tag(ink, "Q3 · IMAGE · released 0:41 · after both earlier readings")
    poem_block(ink, 40, 150, 6, size=20, gap=30, color=MUTED)
    a = ease(local, 0.0, 0.8)
    image_drawing(ink, 470, 80, 1.0, t)
    if a < 1:
        ink.d.rectangle([468, 78, 892, 382], fill=PAGE + (int(255 * (1 - a)),))
    readers(ink, t, y=500, s=0.75)


def reply_stage(ink, t, local, which):
    cues = {"R1": "Q1", "R2": "Q1 Q2", "R3": "Q1 Q2 Q3"}[which]
    first = {"R1": "0:15", "R2": "0:33", "R3": "0:46"}[which]
    if which == "R1":
        ink.fill(NIGHT)
        dark = True
        ink.text((W / 2, 200), "?", "serif", 120, (70, 70, 84), anchor="mm")
    elif which == "R2":
        ink.fill(PAGE)
        dark = False
        poem_block(ink, 250, 120, 6, color=MUTED)
    else:
        ink.fill(PAGE)
        dark = False
        poem_block(ink, 40, 150, 6, size=20, gap=30, color=MUTED)
        image_drawing(ink, 470, 80, 1.0, t)
    cue_tag(ink, f"RESPONSE {which} · from {first} · cues available: {cues}", dark)
    speaking = None
    for a, b, who, line, c in REPLIES:
        if a <= t < b:
            speaking = who
    readers(ink, t, y=500 if which == "R3" else 470, dark=dark, speaking=speaking, s=0.75 if which == "R3" else 0.9)


def ledger(ink):
    ink.fill(PAGE)
    ink.label((W / 2, 40), "CUE AND RESPONSE ORDER · responses cite only cues already released", 14, ACCENT, anchor="mm")
    rows = [("0:03.5", "Q1", "sound: six murmured lines, rustle, bell, small click", MUTED),
            ("0:15", "R1", "O: a bird with a bell  ·  B: a ticket, a station thing", INK),
            ("0:21", "Q2", "text: the poem, unchanged", MUTED),
            ("0:33", "R2", "O: a station cat  ·  B: a letter? a lock?", INK),
            ("0:41", "Q3", "image: bench, opened envelope, brass key, shut door", MUTED),
            ("0:46", "R3", "O reconsiders: the key  ·  B keeps an alternate: what it left", ACCENT)]
    for k, (tm, cid, s, col) in enumerate(rows):
        y = 90 + k * 54
        ink.text((60, y), tm, "mono", 16, MUTED)
        ink.text((150, y), cid, "mono", 18, ACCENT if cid.startswith("Q") else INK)
        ink.text((220, y - 4), s, "serif", 24, col)
        ink.line([(50, y + 38), (910, y + 38)], RULE, 1, rough=False)
    ink.label((W / 2, 440), "what physically happened (the seed): a key was left on the bench and the door stayed shut", 13, INK, anchor="mm")
    ink.label((W / 2, 466), "what the readers made of it stays theirs · readers, voices and poem are fictional and original", 12, MUTED, anchor="mm")


@film.picture
def frame(t, ink):
    name, local, a, b = SC.at(t)
    if name == "title":
        section_card(ink, "AFTER LE MAKI MOCOCO · RIBOT / ROUBAUD", "What is a mirlocca?",
                     "sound first · then the text · then an image · two fictional readers")
    elif name == "Q1":
        sound_stage(ink, t, local)
    elif name == "Q2":
        text_stage(ink, t, local)
    elif name == "Q3":
        image_stage(ink, t, local)
    elif name in ("R1", "R2", "R3"):
        reply_stage(ink, t, local, name)
    else:
        ledger(ink)
    for c0, c1, who, line, cues in REPLIES:
        if c0 <= t < c1:
            al = min(1, (t - c0) / 0.2, (c1 - t) / 0.2)
            speaker_caption(ink, who.title() + " (fictional)", line, al, y=H - 40 if name != "R3" else 420,
                            who_color=ONDINE if who == "ONDINE" else BASTIEN, size=24)
    edge_fade(ink, t, a, b, 0.3, color=NIGHT if name in ("title", "Q1", "R1") else PAGE)


@film.sound
def sound(mix):
    mix.room(3.5, 56, 0.015)
    # Q1: the poem as a murmured reading (one voice), with three sounds the poem names
    for k, a in enumerate(LINE_AT):
        mix.murmur(a, LINE_DUR, 0.11, 160, 0.0, seed=300 + k)
        cue = CUE_SOUNDS.get(k)
        if cue == "paper":
            for j in range(3):
                mix.add(mix.band(mix.noise(0.15), 1500, 8000) * np.hanning(int(0.15 * RATE)), a + 0.8 + j * 0.16, 0.25, 0.2)
        elif cue == "bell":
            mix.bell(a + 0.9, 660, 2.6, 0.2)
        elif cue == "metal":
            mix.click(a + 0.9, 0.22, -0.1, 9000, 0.02)
            mix.click(a + 0.98, 0.16, -0.1, 7000, 0.02)
            mix.click(a + 1.1, 0.1, -0.1, 9500, 0.02)
    # replies: two distinct murmuring voices under the captions
    for c0, c1, who, line, cues in REPLIES:
        mix.murmur(c0 + 0.1, c1 - c0 - 0.3, 0.07, 215 if who == "ONDINE" else 118, -0.5 if who == "ONDINE" else 0.5, seed=int(c0 * 10))
    # cue releases are marked by one soft tone each
    for at, f in ((3.5, 392), (21.0, 440), (41.0, 523)):
        mix.note(at, f, 1.4, 0.06, 0, "sine", 0.01, 1.0, 0.2)
    # text stage: a quiet typewriter-like tick per line appearing
    for k in range(6):
        mix.click(21.0 + k * 1.1, 0.1, 0.0, 3000)
    mix.click(41.4, 0.2, 0.0, 9000, 0.02)    # the key, now seen
    mix.bell(54.2, 660, 3.5, 0.08)
    mix.reverb(0.18, 1.1)


if __name__ == "__main__":
    film.render()

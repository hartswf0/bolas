"""A CLOCKWORK PINK: the female version, about 46 seconds.

A Clockwork Orange made attractive to a female audience, rather than another look at its violence. The film's icons are
kept and turned. Alex's single painted eyelash becomes makeup that a friend helps with. The bowler hats and white
outfits become a girl gang walking arm in arm at sunset. Ludwig van becomes Ode to Joy on a music box, and the colour-field
title cards turn pink. The tagline is rewritten: "Being the adventures of a young woman whose principal interests are
friendship, tenderness and Beethoven." No footage from the 1971 film is used.

Cut paper, rendered from code, with two public-domain archive shots graded pink: a water lily (Wathen collection, New
York World's Fair, 1939-40) and a butterfly on a woman's fingertips (Insect Zoo), both via hartswf0/secondhand-motion.

    python3 tools/clockwork_pink/female_version.py SHOTS_DIR OUT_DIR
"""
import math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS, SR = 960, 540, 24, 48000
BEAT = 0.6                                                 # 100 bpm; the music and the cards share it
END = 46.0
HOT = (232, 62, 128); LILAC = (186, 150, 220); CREAM = (252, 240, 236)
SKIN = (243, 208, 186); HAIR = (34, 26, 30); BLUSH = (240, 150, 170); WHITE = (250, 248, 244)
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"; SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"

# the score
CARDS = [(0.0, "A", HOT), (1.2, "CLOCKWORK", LILAC), (2.4, "PINK", HOT)]   # colour-field titles, on the beat
FACE = (3.6, 21.0)                                        # the lash, done by a friend
INSERTS = (21.0, 30.0)                                    # the lily, the butterfly on her fingertips
WALK = (30.0, 39.6)                                       # three girls, arm in arm, at sunset
FINAL = 39.6


def smooth(u):
    u = min(1.0, max(0.0, u)); return u * u * (3 - 2 * u)


def twos(t):
    return t - (t % (2 / FPS))                            # cut paper moves on twos


def ragged(pts, seed, amp=1.2, step=6):
    out = []
    for i in range(len(pts)):
        a, b = np.array(pts[i], float), np.array(pts[(i + 1) % len(pts)], float)
        n = max(1, int(np.linalg.norm(b - a) / step))
        out += [tuple(a + (b - a) * j / n) for j in range(n)]
    r = np.random.default_rng(seed)
    return [(x + r.normal(0, amp), y + r.normal(0, amp)) for x, y in out]


def ell(cx, cy, rx, ry, a0=0, a1=2 * math.pi, n=80):
    return [(cx + rx * math.cos(a), cy + ry * math.sin(a)) for a in np.linspace(a0, a1, n)]


_r = np.random.default_rng(1)
GRAIN = np.asarray(Image.fromarray(_r.normal(128, 10, (H, W)).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8)), np.float32)[..., None] - 128


def paper(color):
    return Image.new("RGB", (W, H), color)


def piece(d, sh, poly, fill, seed, lift=(4, 5)):
    """one cut-paper piece: a lifted shadow, then the card"""
    pts = ragged(poly, seed)
    sh.polygon([(x + lift[0], y + lift[1]) for x, y in pts], fill=110)
    d.polygon(pts, fill=fill)


def finish(img, sh):
    s = sh.filter(ImageFilter.GaussianBlur(5))
    img.paste((120, 60, 80), mask=s.point(lambda v: v * 0.45))
    a = np.asarray(img, np.float32) + GRAIN * 0.5
    return np.clip(a, 0, 255)


# ---- the title cards --------------------------------------------------------
def card(text, color, size=150, sub=None):
    img = paper(color); d = ImageDraw.Draw(img)
    f = ImageFont.truetype(BOLD, size)
    while f.getlength(text) > W - 120:
        size -= 8; f = ImageFont.truetype(BOLD, size)
    d.text((W / 2, H / 2 - (30 if sub else 0)), text, font=f, fill=WHITE, anchor="mm")
    if sub:
        y = H / 2 + 60
        for line in sub:
            d.text((W / 2, y), line, font=ImageFont.truetype(SERIF, 20), fill=WHITE, anchor="mm"); y += 30
    return np.asarray(img, np.float32) + GRAIN * 0.4


# ---- the face: the lash, done by a friend ---------------------------------
def face(t):
    u = twos(t - FACE[0])
    img = paper((248, 214, 224)); d = ImageDraw.Draw(img); shL = Image.new("L", (W, H), 0); sh = ImageDraw.Draw(shL)
    cx, cy = 450, 300
    piece(d, sh, ell(cx, cy - 10, 178, 196, math.pi * 0.98, math.pi * 2.02) + [(cx + 178, cy + 90), (cx - 178, cy + 90)], HAIR, 1)   # the bob
    piece(d, sh, [(cx - 60, cy + 120), (cx + 60, cy + 120), (cx + 70, H + 20), (cx - 70, H + 20)], SKIN, 2)                          # neck
    piece(d, sh, [(cx - 190, H - 40), (cx - 60, cy + 175), (cx, cy + 215), (cx + 60, cy + 175), (cx + 190, H - 40), (cx + 200, H + 20), (cx - 200, H + 20)], WHITE, 3)   # white collar
    piece(d, sh, ell(cx, cy + 10, 132, 162), SKIN, 4)                                                                                # face
    piece(d, sh, ell(cx, cy - 92, 150, 92, math.pi, 2 * math.pi) + [(cx + 150, cy - 70), (cx - 150, cy - 70)], HAIR, 5)              # blunt bangs
    piece(d, sh, ell(cx, cy - 150, 168, 22), HOT, 6)                                                                                 # bowler brim
    piece(d, sh, ell(cx, cy - 156, 104, 132, math.pi, 2 * math.pi), HOT, 7)                                                          # bowler crown, tall and round
    d.rectangle([cx - 104, cy - 176, cx + 104, cy - 162], fill=WHITE)                                                                # hat band
    for x in (cx - 72, cx + 72):
        d.ellipse([x - 26, cy + 52, x + 26, cy + 74], fill=BLUSH)                                                                    # cheeks
    blink = 1.0
    for b in (8.6, 15.8):                                                    # two happy blinks, swapped drawings
        if 0 <= u - (b - FACE[0]) < 0.25:
            blink = 0.0
    mascara = smooth((u - 7.0) / 6.0)                                       # the lash grows with each stroke
    for side, x in ((-1, cx - 55), (1, cx + 55)):
        if blink:
            d.ellipse([x - 32, cy - 14, x + 32, cy + 14], fill=WHITE)
            d.ellipse([x - 12, cy - 12, x + 12, cy + 12], fill=(92, 58, 44)); d.ellipse([x - 5, cy - 5, x + 5, cy + 5], fill=HAIR)
            d.ellipse([x + 3, cy - 8, x + 8, cy - 3], fill=WHITE)
            d.arc([x - 34, cy - 16, x + 34, cy + 16], 190, 350, fill=HAIR, width=4)
        else:
            d.arc([x - 32, cy - 10, x + 32, cy + 12], 10, 170, fill=HAIR, width=4)
        d.arc([x - 34, cy - 52, x + 34, cy - 12], 205, 335, fill=HAIR, width=5)                                                     # brow
        if side == 1:                                           # Alex's lash, now hers: long, upper and lower, on one eye
            L = 10 + 14 * mascara
            for k in range(7):                                  # lashes sweep up and out, curling toward the outer corner
                a = math.radians(212 + k * 19)
                bx, by = x + 32 * math.cos(a), cy + (14 if blink else 4) * math.sin(a)
                ex, ey = bx + L * math.cos(a) * 0.7 + 4 * k, by + L * math.sin(a)
                d.line([(bx, by), ((bx + ex) / 2 + 2, (by + ey) / 2), (ex, ey)], fill=HAIR, width=3)
            for k in range(6):
                a = math.radians(30 + k * 24)
                bx, by = x + 30 * math.cos(a), cy + 13 * math.sin(a)
                d.line([(bx, by), (bx + 12 * math.cos(a), by + 16 * math.sin(a))], fill=HAIR, width=3)
    d.line([(cx, cy + 20), (cx - 6, cy + 58), (cx + 4, cy + 60)], fill=(200, 150, 130), width=3)                                     # nose
    smile = 6 + 10 * smooth((u - 13.5) / 2.0)
    d.chord([cx - 38, cy + 84 - smile / 2, cx + 38, cy + 104 + smile], 0, 180, fill=HOT)                                            # lips, a smile that grows
    # the friend's hand, with a mascara wand: it comes in, makes three strokes, and leaves
    come = smooth((u - 4.0) / 1.6) - smooth((u - 13.0) / 1.6)
    if come > 0.01:
        stroke = 0.0
        for s0 in (7.0, 8.9, 10.8):
            p = (u - s0) / 1.4
            if 0 <= p <= 1:
                stroke = math.sin(math.pi * p)
        hx, hy = 960 + (cx + 140 - 960) * come, cy + 150 - 40 * stroke
        piece(d, sh, [(hx - 8, hy - 40), (hx + 4, hy - 46), (hx - 86, hy - 168), (hx - 98, hy - 160)], HOT, 20)                     # wand
        d.line([(hx - 90, hy - 162), (hx - 108, hy - 190)], fill=HAIR, width=9)                                                     # brush
        piece(d, sh, ell(hx + 40, hy + 10, 62, 48), SKIN, 21)                                                                        # palm
        for k, (dx, dy) in enumerate(((-10, -40), (-28, -18), (-30, 6))):
            piece(d, sh, ell(hx + dx, hy + dy, 34, 11, 0, 2 * math.pi, 30), SKIN, 22 + k)                                         # fingers
            d.ellipse([hx + dx - 36, hy + dy - 6, hx + dx - 24, hy + dy + 6], fill=HOT)                                             # pink nails
        piece(d, sh, [(hx + 70, hy - 20), (W + 40, hy - 50), (W + 40, hy + 110), (hx + 80, hy + 50)], LILAC, 25)                    # her sleeve
    return finish(img, shL)


# ---- the archive, graded pink ---------------------------------------------
def load(shots, name):
    dd = os.path.join(shots, f"{name}-sam", "frames")
    return np.stack([np.asarray(Image.open(os.path.join(dd, f)).convert("RGB").resize((720, 540)), np.float32) for f in sorted(os.listdir(dd))])


def pinkgrade(a):
    y = (a @ np.array([0.299, 0.587, 0.114]))[..., None] / 255
    lo, hi = np.array([150, 74, 110]), np.array([255, 232, 236])
    duo = lo + (hi - lo) * (y ** 0.7)
    return duo * 0.7 + a * 0.3


def inserts(src, t):
    u = t - INSERTS[0]
    def frame(name, sp):
        fr = src[name]; x = u * 12 * sp; n = len(fr); p = 2 * n - 2; k = int(x) % p; k = k if k < n else p - k
        return fr[k]
    lily, fly = pinkgrade(frame("flower", 0.6)), pinkgrade(frame("butterfly", 0.6))
    k = smooth((u - 4.0) / 1.5)
    pic = lily * (1 - k) + fly * k
    img = np.broadcast_to(np.array([248, 214, 224], np.float32), (H, W, 3)).copy()
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).polygon(ragged(ell(W / 2, H / 2, 300, 236), 40, 2.0), fill=255)
    m = np.asarray(m.filter(ImageFilter.GaussianBlur(1.5)), np.float32)[..., None] / 255
    canvas = np.zeros((H, W, 3), np.float32); canvas[:, 120:840] = pic
    img = img * (1 - m) + canvas * m
    return img + GRAIN * 0.5


# ---- three girls, arm in arm, at sunset ------------------------------------
def walk(t):
    u = twos(t - WALK[0])
    img = Image.new("RGB", (W, H)); d = ImageDraw.Draw(img)
    for y in range(H):                                          # a pink to peach sky
        k = y / H; d.line([(0, y), (W, y)], fill=(int(250 - 10 * k), int(170 + 40 * k), int(190 - 30 * k)))
    d.ellipse([600, 180, 760, 340], fill=(255, 236, 200))      # the sun
    shL = Image.new("L", (W, H), 0); sh = ImageDraw.Draw(shL)
    for i, (x, w_, h_) in enumerate(((40, 90, 230), (160, 70, 300), (260, 110, 180), (720, 90, 260), (830, 120, 200))):
        x = x - 6 * u                                            # tower blocks drift: the estate, in pastel
        piece(d, sh, [(x, 420 - h_), (x + w_, 420 - h_), (x + w_, 420), (x, 420)], (196, 160, 210), 50 + i, (3, 3))
        for wy in range(int(430 - h_), 410, 22):
            for wx in range(int(x + 10), int(x + w_ - 10), 18):
                d.rectangle([wx, wy, wx + 8, wy + 10], fill=(255, 230, 200))
    d.rectangle([0, 420, W, H], fill=(236, 150, 170))
    step = int(u * 4) % 2                                        # a two-drawing walk, on twos
    base = -260 + 150 * u
    for g in range(3):
        x = base + g * 110; y = 300 + (4 if (step + g) % 2 else 0)
        legs = [(-14, 22), (10, -6)] if (step + g) % 2 else [(-4, 4), (4, -4)]
        for k, (lx, rx) in enumerate(legs):
            piece(d, sh, [(x - 8 + lx * 0.3, y + 70), (x + 6 + lx * 0.3, y + 70), (x + 4 + lx, y + 132), (x - 10 + lx, y + 132)], WHITE, 60 + g * 4 + k, (3, 3))
            d.rectangle([x - 14 + lx, y + 128, x + 10 + lx, y + 140], fill=HAIR)                                                     # boots
        piece(d, sh, [(x - 20, y), (x + 20, y), (x + 24, y + 76), (x - 24, y + 76)], WHITE, 70 + g, (3, 3))                        # white top
        piece(d, sh, ell(x, y - 22, 20, 24), SKIN, 74 + g, (3, 3))
        piece(d, sh, ell(x - 3, y - 26, 22, 22, math.pi * 0.9, math.pi * 2.1) + [(x + 18, y - 10), (x - 24, y - 10)], HAIR, 78 + g, (3, 3))
        piece(d, sh, ell(x, y - 46, 32, 6), HOT, 82 + g, (3, 3)); piece(d, sh, ell(x, y - 48, 18, 18, math.pi, 2 * math.pi), HOT, 86 + g, (3, 3))
        if g < 2:
            d.line([(x + 18, y + 24), (x + 92, y + 24)], fill=SKIN, width=8)                                                         # arm in arm
    return finish(img, shL)


# ---- the music: Ode to Joy on a music box, over warm chords ----------------
def music():
    n = int(END * SR); t = np.arange(n) / SR; out = np.zeros(n)
    tune = [66, 66, 67, 69, 69, 67, 66, 64, 62, 62, 64, 66, 66, 64, 64, 64,
            66, 66, 67, 69, 69, 67, 66, 64, 62, 62, 64, 66, 64, 62, 62, 62]
    lens = [1] * 12 + [1.5, 0.5, 2, 0] + [1] * 12 + [1.5, 0.5, 2, 0]
    def box(f, at, g):
        k = int(2.2 * SR); x = np.arange(k) / SR
        s = sum(a * np.sin(2 * np.pi * f * r * x) for r, a in ((1, 1), (2.0, 0.35), (3.0, 0.12), (4.16, 0.08))) * np.exp(-x * 2.8) * np.minimum(1, x / 0.003)
        a = int(at * SR); b = min(n, a + k)
        if a < n:
            out[a:b] += g * s[: b - a]
    at = 3.6
    for rep in range(2):
        for m, l in zip(tune, lens):
            if l:
                box(440 * 2 ** ((m + 12 - 69) / 12), at, 0.5 if rep == 0 else 0.42); at += l * BEAT
    for i, (_, _, _) in enumerate(CARDS):                       # a soft chime on each title card
        box(440 * 2 ** ((74 + 5 * i - 69) / 12), CARDS[i][0], 0.35)
    chords = [[146.8, 220, 293.7, 370], [110, 220, 277.2, 329.6]]   # D and A, breathing under the tune
    bar = 4 * BEAT
    for j in range(int(END / bar)):
        ch = chords[j % 2]; a0 = j * bar
        w = np.clip(1 - np.abs(t - (a0 + bar / 2)) / bar, 0, 1)
        for f in ch:
            out += 0.05 * w * np.sin(2 * np.pi * f * t + j)
    out *= np.clip((END - t) / 3, 0, 1)
    return out / np.abs(out).max() * 0.7


def picture(src, t):
    for i, (t0, text, color) in enumerate(CARDS):
        t1 = CARDS[i + 1][0] if i + 1 < len(CARDS) else FACE[0]
        if t0 <= t < t1:
            return card(text, color)
    if t < FACE[1]:
        a = face(t)
        if t > FACE[1] - 1.0:
            a = a * (1 - smooth((t - FACE[1] + 1.0))) + inserts(SRC, INSERTS[0]) * smooth((t - FACE[1] + 1.0))
        return a
    if t < INSERTS[1]:
        a = inserts(SRC, t)
        if t > INSERTS[1] - 1.0:
            a = a * (1 - smooth(t - INSERTS[1] + 1.0)) + walk(WALK[0]) * smooth(t - INSERTS[1] + 1.0)
        return a
    if t < WALK[1]:
        return walk(t)
    k = smooth((t - FINAL) / 0.6)
    fin = card("A CLOCKWORK PINK", HOT, 96, ["Being the adventures of a young woman", "whose principal interests are",
                                             "friendship, tenderness and Beethoven."])
    return walk(WALK[1] - 0.01) * (1 - k) + fin * k


SRC = None


def main(shots, od):
    global SRC
    os.makedirs(od, exist_ok=True)
    SRC = {"flower": load(shots, "flower"), "butterfly": load(shots, "butterfly")}
    wav = os.path.join(od, "pink.wav"); vid = os.path.join(od, "a-clockwork-pink.mp4")
    with wave.open(wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((music() * 32767).astype(np.int16).tobytes())
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-i", wav, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", "-c:a", "aac", "-b:a", "160k",
                           "-movflags", "+faststart", "-shortest", vid], stdin=subprocess.PIPE)
    for f in range(int(END * FPS)):
        t = f / FPS
        a = picture(SRC, t) * min(1.0, (END - t) / 1.5)
        ff.stdin.write(np.clip(a, 0, 255).astype(np.uint8).tobytes())
    ff.stdin.close(); ff.wait(); print(vid)


if __name__ == "__main__":
    main(*sys.argv[1:3])

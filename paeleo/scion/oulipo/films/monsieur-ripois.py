"""Monsieur Ripois — an interested confession at a lost-property window.
The visitor claims the envelope came back untouched; the flashback (as told) hides one gesture;
the clerk's receipt, a silent shake and the sweeper's tag let him decide otherwise."""
import math
from PIL import Image, ImageOps, ImageDraw, ImageFilter
from kit_cinema_b import *

SC = Score([(0, 3.0, "title"), (3.0, 14.0, "present1"), (14.0, 24.0, "flashback"), (24.0, 27.0, "shake"),
            (27.0, 30.0, "receipt"), (30.0, 33.0, "tag"), (33.0, 37.5, "verdict"), (37.5, 43.0, "ledger")])
film = Film("monsieur-ripois", seconds=SC.total, boil=6, wobble=1.1, seed=5)
film.poster_at = 19.6

V_COAT, C_COAT = (92, 70, 62), (70, 84, 96)
CAPS = [  # (start, end, speaker, line)
    (4.0, 7.0, "VISITOR", "I'm returning your envelope. Exactly as you lent it."),
    (7.2, 10.6, "VISITOR", "Sealed. I sat on the bench, the bell rang, I left."),
    (11.0, 13.8, "VISITOR", "Let me tell you how it was."),
    (24.6, 26.9, "CLERK", "When I lent it, it rattled."),
    (33.3, 35.6, "VISITOR", "…The bench was damp. It must have slipped out."),
    (35.8, 37.4, "CLERK", "Then I'll write what it is."),
]
FB_CUT = 19.4   # the splice in the flashback that hides the gesture


def office(ink, t, lean=0.0, clerk_pose="listen", clerk_face=-1, shake=0.0, env_on_counter=True):
    ink.d.rectangle([0, 0, W, H], fill=(232, 226, 212))
    # back wall of pigeonholes behind the clerk
    for r in range(4):
        for c in range(6):
            x0, y0 = 560 + c * 50, 130 + r * 46
            ink.rect(x0, y0, x0 + 46, y0 + 42, fill=(214, 204, 186), color=MUTED, width=1.2, alpha=180)
    ink.label((710, 118), "LOST PROPERTY", 13, INK, anchor="mm")
    # clock on the office wall
    clock(ink, 140, 120, 36, 12 + 7 / 60 + t / 3600)
    # clerk (behind counter)
    cx = 700 - lean * 26
    arm = {"listen": 10, "chin": 150, "shake": 95 + 18 * math.sin(shake * 40), "stamp": 60 + 40 * abs(math.sin(shake * 18))}[clerk_pose]
    pose = "stand" if clerk_pose == "listen" else "reach"
    pts_c = figure(ink, cx, 492, 2.3, pose, 0, clerk_face, coat=C_COAT, arm=arm)
    hx, hy = pts_c["head"]
    ink.line([(hx - 16, hy + 8), (hx + 16, hy + 8)], INK, 1.5)  # spectacles bar
    ink.circle(hx - 9, hy + 2, 7, color=INK, width=1.6)
    ink.circle(hx + 9, hy + 2, 7, color=INK, width=1.6)
    # counter and grille
    ink.rect(0, 360, W, 400, fill=(160, 124, 88), color=INK, width=2.5)
    ink.d.rectangle([0, 400, W, H], fill=(140, 108, 78))
    ink.rect(520, 96, 900, 360, fill=None, color=INK, width=3)
    for x in range(540, 900, 26):
        ink.line([(x, 98), (x, 330)], INK, 1.4, alpha=110)
    ink.rect(640, 330, 780, 360, fill=(200, 190, 170), color=INK, width=2)  # the slot
    # visitor (in front, left)
    vx = 300
    pts_v = figure(ink, vx, 560, 2.5, "reach" if 3.5 < t < 5 else "stand", 0, 1, coat=V_COAT, hat=True, arm=70 if 3.5 < t < 5 else None)
    return pts_c, pts_v


def present1(ink, local, t):
    lean = ease(local, 6.0, 7.5) * 0.8 - ease(local, 9.5, 10.5) * 0.4
    pose = "chin" if 7.6 < local < 10.6 else "listen"
    pts_c, pts_v = office(ink, t, lean, pose)
    # envelope slides under the grille
    f = ease(local, 0.7, 1.8)
    ex = lerp(420, 700, f)
    envelope(ink, ex, 350, 70, 44)
    ink.label((ex, 384), "sealed", 11, PAGE, anchor="mm", alpha=int(255 * f))


def sepia(ink, strength=1.0):
    img = ink.img.convert("RGB")
    g = ImageOps.grayscale(img)
    tone = ImageOps.colorize(g, (58, 40, 30), (238, 214, 172))
    tone = Image.blend(img, tone, strength)
    # soft oval edge
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).ellipse([40, 20, W - 40, H - 20], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(40))
    out = Image.composite(tone, Image.new("RGB", img.size, (40, 30, 24)), mask)
    ink.img = out
    ink.d = ImageDraw.Draw(ink.img, "RGBA")


def flashback(ink, local, t):
    ink.d.rectangle([0, 0, W, H], fill=(230, 226, 214))
    platform(ink, 330)
    door(ink, 820, 330, w=80, h=170, sign="SERVICE")
    bench(ink, 430, 360, w=230)
    # station clock: jumps at the splice
    clock_min = 3 + 10 / 60 + local / 60 if t < FB_CUT else 4 + 40 / 60 + (t - FB_CUT) / 60
    clock(ink, 150, 150, 40, 12 + clock_min / 60)
    ink.line([(150, 70), (150, 110)], INK, 2)
    # bell on its bracket
    sw = 0.0
    if 2.8 < local < 4.6:
        sw = math.sin((local - 2.8) * 14) * 0.5 * (1 - ramp(local, 2.8, 4.6))
    bx, by = 620, 110
    ink.line([(bx - 30, 80), (bx, 80), (bx, 92)], INK, 3)
    ca, sa = math.cos(sw), math.sin(sw)
    shape = [(-6, 0), (6, 0), (10, 18), (18, 28), (-18, 28), (-10, 18)]
    ink.poly([(bx + px * ca - py * sa, 92 + px * sa + py * ca) for px, py in shape], fill=BRASS, color=INK, width=2)
    if t < FB_CUT:
        # seated with the sealed envelope
        p = figure(ink, 400, 360, 1.5, "sit", 0, 1, coat=V_COAT, hat=True, arm=60)
        h = p["hands"][0]
        envelope(ink, h[0] + 6, h[1] - 4, 44, 30)
    else:
        # after the splice: already standing, envelope sealed on the bench, walking away
        envelope(ink, 440, 360 - 52, 44, 30)
        wx = lerp(470, 990, ease(t, FB_CUT + 0.3, 23.8))
        figure(ink, wx, 372, 1.5, "walk", wx / 60, 1, coat=V_COAT, hat=True)
    sepia(ink)
    ink.label((30, 26), "AS TOLD · the visitor's account · no independent witness", 13, (250, 230, 200))
    if FB_CUT <= t < FB_CUT + 0.09:
        ink.fill((250, 240, 220))
    if FB_CUT <= t < FB_CUT + 2.0:
        ink.label((150, 214), "the clock skips 90 s", 15, (255, 240, 210), anchor="mm", alpha=int(255 * (1 - ramp(t, FB_CUT + 1.4, FB_CUT + 2.0))))


def shake(ink, local, t):
    pts_c, _ = office(ink, t, 0.3, "shake", -1, shake=local)
    h = pts_c["hands"][0]
    envelope(ink, h[0], h[1] - 6, 70, 44, angle=0)
    ink.label((h[0], h[1] - 50), "· no sound ·", 13, ACCENT, anchor="mm", alpha=int(255 * ramp(local, 0.4, 0.8)))


def paper_insert(ink, title, rows, highlight, stamp=None, key=False):
    ink.fill((120, 100, 80))
    ink.hatch(0, 0, W, H, gap=14, angle=20, color=(100, 82, 64), width=2, alpha=120)
    ink.rect(220, 80, 740, 470, fill=PAGE, color=INK, width=2.5)
    ink.label((250, 110), title, 15, ACCENT)
    for k, s in enumerate(rows):
        y = 160 + k * 46
        ink.text((250, y), s, "mono", 20, ACCENT if k == highlight else INK)
        ink.line([(250, y + 32), (710, y + 32)], RULE, 1, rough=False)
    if key:
        key_shape(ink, 560, 420, 1.8, angle=-0.2)
    if stamp:
        a = stamp
        ink.rect(420, 360, 720, 440, fill=None, color=ACCENT, width=4, alpha=int(230 * a))
        ink.text((570, 400), "RETURNED · OPENED", "mono", 22, ACCENT, anchor="mm", alpha=int(240 * a))


def verdict(ink, local, t):
    stamping = local > 2.9
    pts_c, _ = office(ink, t, 0.0, "stamp" if stamping else "listen", -1, shake=local)
    # receipt and key now on the counter on the clerk's side
    ink.rect(640, 300, 760, 345, fill=PAGE, color=INK, width=1.8)
    ink.label((700, 312), "No. 0412", 10, INK, anchor="mm")
    if stamping:
        ink.label((700, 330), "OPENED", 12, ACCENT, anchor="mm")
    key_shape(ink, 800, 320, 0.9)
    envelope(ink, 580, 330, 56, 36, open_=0.0)
    # the look: the clerk's eyes towards the visitor
    if 0.2 < local < 2.6:
        hx, hy = pts_c["head"]
        ink.line([(hx - 30, hy), (hx - 90, hy + 10)], ACCENT, 1.5, alpha=160)


def ledger(ink, local):
    ink.fill(PAGE)
    ink.label((W / 2, 46), "CLAIM / EVIDENCE LEDGER · both records survive", 15, ACCENT, anchor="mm")
    rows = [("C1", "claim, spoken", "“sealed, exactly as you lent it”", "visitor"),
            ("E2", "flashback", "sealed on the bench; clock skips 90 s", "as told · subjective"),
            ("E3", "receipt 0412", "contents: 1 brass key, rattles", "clerk's record"),
            ("E4", "the shake", "paper only, no rattle", "heard"),
            ("E5", "sweeper's tag", "12:04 · key found on bench 1", "independent"),
            ("D1", "decision", "stamps OPENED, keeps the key", "listener")]
    for k, (i, kind, what, src) in enumerate(rows):
        y = 100 + k * 58
        ink.text((70, y), i, "mono", 20, ACCENT)
        ink.text((130, y), kind, "mono", 16, MUTED)
        ink.text((300, y - 4), what, "serif", 26, INK)
        ink.text((900, y), src, "mono", 13, MUTED, anchor="ra")
        ink.line([(60, y + 40), (900, y + 40)], RULE, 1, rough=False)
    ink.label((W / 2, 480), "the hidden gesture: opening the envelope and leaving the key", 13, MUTED, anchor="mm")


@film.picture
def frame(t, ink):
    name, local, a, b = SC.at(t)
    if name == "title":
        section_card(ink, "AFTER MONSIEUR RIPOIS · CLÉMENT / QUENEAU 1954", "The return, as told", "a visitor, a clerk, one envelope")
    elif name == "present1":
        present1(ink, local, t)
    elif name == "flashback":
        flashback(ink, local, t)
    elif name == "shake":
        shake(ink, local, t)
    elif name == "receipt":
        paper_insert(ink, "LOST PROPERTY · RECEIPT No. 0412",
                     ["issued      11:50", "item        1 sealed envelope", "contents    1 brass key", "note        rattles when shaken"], 2)
    elif name == "tag":
        paper_insert(ink, "SWEEPER'S TAG · PLATFORM 1",
                     ["time        12:04", "place       bench, platform 1", "found       1 brass key", "envelope    none seen"], 2, key=True)
    elif name == "verdict":
        verdict(ink, local, t)
    else:
        ledger(ink, local)
    for c0, c1, who, line in CAPS:
        if c0 <= t < c1:
            al = min(1, (t - c0) / 0.2, (c1 - t) / 0.2)
            speaker_caption(ink, who, line, al, who_color=ACCENT if who == "CLERK" else (92, 60, 40))
    if name in ("title", "ledger"):
        edge_fade(ink, t, a, b, 0.35)
    elif name in ("flashback",) or (name == "shake"):
        edge_fade(ink, t, a, b, 0.5, color=(40, 30, 24))


@film.sound
def sound(mix):
    T = SC.total
    mix.room(3, 11, 0.025)
    mix.room(24, 13.5, 0.025)
    for k in range(int(3 * 1), int(37 * 1)):
        if not 14 <= k < 24:
            mix.click(k, 0.04, -0.6, 2500, 0.015)   # office clock
    for c0, c1, who, line in CAPS:
        mix.murmur(c0 + 0.1, c1 - c0 - 0.3, 0.08, 135 if who == "VISITOR" else 102, -0.3 if who == "VISITOR" else 0.3, seed=int(c0 * 10))
    # envelope slides under the grille
    mix.add(mix.band(mix.noise(1.0), 1500, 6000) * np.hanning(int(RATE)) * 0.3, 3.7, 0.5, 0.1)
    # flashback: thinner, echoing
    mix.whoosh(13.8, 0.8, 0.12)
    mix.wind(14, 10, 0.05)
    mix.bell(14 + 2.8, 587, 3.2, 0.22, 0.3)
    mix.click(FB_CUT, 0.3, 0, 8000, 0.01)  # the splice
    mix.steps(FB_CUT + 0.3, 23.8, 0.46, 0.15, "stone", -0.2, 0.8)
    mix.whoosh(23.7, 0.8, 0.12)
    # the shake: paper only — no rattle
    for k in range(5):
        x = mix.band(mix.noise(0.12), 1200, 7000) * np.hanning(int(0.12 * RATE))
        mix.add(x, 24.4 + k * 0.32, 0.35, 0.3)
    # the receipt insert recalls the rattle it should have made
    for k in range(4):
        mix.click(27.6 + k * 0.28, 0.16, 0.2, 9000, 0.02)
        mix.click(27.62 + k * 0.28, 0.1, 0.25, 6000, 0.02)
    mix.click(31.0, 0.3, 0.0, 8000)   # key laid down
    mix.click(31.03, 0.2, 0.0, 9500)
    for k in range(3):
        mix.thud(36.4 + k * 0.33, 120, 0.3, 0.3, 0.15)  # stamp
    mix.bell(37.6, 440, 3.5, 0.1)
    mix.reverb(0.12, 1.0)


if __name__ == "__main__":
    film.render()

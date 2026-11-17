"""The one plate: a long-snouted creature on a bench at night, holding an unopened envelope.

Drawn once, by brush, in a 1000-unit square (rendered at 2x then reduced).
The pose is built to be ambiguous: half-lidded eye sliding toward the
envelope, mouth a flat line, both hands pinning the envelope to the lap.
"""
import hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from hand import brush, blob, catmull, arc, wobble, INK, PAPER

SS = 2.0  # supersample


def S(pts):
    return [(x * SS, y * SS) for x, y in pts]


def draw_plate(size=600, seed=7, night=True):
    W = int(1000 * SS)
    im = Image.new('L', (W, W), INK if night else PAPER)
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(seed)
    lw = 7 * SS

    # --- lamp: globe at upper left, post behind the bench back
    brush(d, S([(150, 215), (152, 440)]), 16 * SS, rng, col=PAPER, taper=(0, 0))
    brush(d, S([(141, 215), (143, 440)]), 4 * SS, rng, taper=(0, 0))
    brush(d, S([(161, 215), (163, 440)]), 4 * SS, rng, taper=(0, 0))
    blob(d, S([(110, 205), (190, 205), (170, 232), (130, 232)]), lw * 0.8, rng)
    blob(d, S([(150, 50), (215, 75), (235, 140), (200, 200), (150, 210), (98, 200), (66, 140), (88, 75)]), lw, rng, amp=1.2)
    for k in range(4):
        x0 = 118 + k * 16
        brush(d, S([(x0, 95 + k * 4), (x0 + 8, 125 + k * 4)]), 4 * SS, rng)
    # three night stars
    for (x, y) in ((330, 70), (420, 160), (930, 90)):
        brush(d, S([(x - 10, y), (x + 10, y)]), 4 * SS, rng, col=PAPER)
        brush(d, S([(x, y - 10), (x, y + 10)]), 4 * SS, rng, col=PAPER)

    # --- ground
    g = S([(-20, 860), (300, 845), (600, 852), (1020, 840), (1020, 1020), (-20, 1020)])
    d.polygon(g, fill=PAPER)
    brush(d, S(catmull([(-20, 860), (300, 845), (600, 852), (1020, 840)], 8)), lw, rng)
    for i in range(26):
        x = rng.uniform(20, 980); y = rng.uniform(880, 980)
        brush(d, S([(x, y), (x + rng.uniform(18, 40), y + rng.uniform(-3, 3))]), 4 * SS, rng)

    # --- bench: back rest, seat, legs (white planks with ink edges)
    def plank(x0, y0, x1, y1, sk=0):
        blob(d, S([(x0, y0), ((x0 + x1) / 2, y0 + sk), (x1, y0), (x1 + 6, (y0 + y1) / 2), (x1, y1), ((x0 + x1) / 2, y1 + sk), (x0, y1), (x0 - 6, (y0 + y1) / 2)]), lw, rng, amp=1.0)
    for x in (150, 830):
        plank(x - 14, 650, x + 14, 860)   # front legs
    for x in (200, 870):
        plank(x - 12, 420, x + 12, 640)   # back posts
    plank(110, 430, 900, 480, 3)
    plank(110, 510, 900, 560, -3)
    plank(80, 630, 930, 690, 2)
    # wood grain
    for (y0, y1) in ((440, 470), (520, 550), (642, 678)):
        for i in range(6):
            x = rng.uniform(140, 860)
            yy = rng.uniform(y0, y1)
            brush(d, S([(x, yy), (x + rng.uniform(40, 90), yy + rng.uniform(-2, 2))]), 3.2 * SS, rng)

    # --- creature (drawn back to front)
    # far ear hanging behind head
    blob(d, S([(520, 220), (470, 260), (440, 360), (450, 450), (480, 470), (505, 400), (530, 300)]), lw, rng)
    # body
    body = [(330, 470), (360, 380), (440, 330), (560, 330), (640, 380), (680, 480), (680, 600), (650, 665), (520, 690), (380, 680), (320, 610)]
    blob(d, S(body), lw * 1.1, rng, amp=1.0)
    # fur dashes on body
    for i in range(55):
        x = rng.uniform(350, 670); y = rng.uniform(360, 670)
        # stay inside body roughly
        if ((x - 505) / 175) ** 2 + ((y - 510) / 175) ** 2 > 0.85:
            continue
        a = rng.uniform(-0.6, 0.6)
        brush(d, S([(x, y), (x + 14 * np.sin(a), y + 20 * np.cos(a))]), 4 * SS, rng)
    # feet dangling over seat front
    for fx in (430, 560):
        blob(d, S([(fx - 35, 680), (fx + 30, 680), (fx + 55, 760), (fx + 40, 790), (fx - 20, 792), (fx - 40, 760)]), lw, rng)
        for t in (0, 1, 2):
            brush(d, S([(fx - 8 + t * 18, 770), (fx - 4 + t * 18, 790)]), 4 * SS, rng)
    # head: dome with long drooping snout to the right
    head = [(470, 250), (500, 160), (580, 110), (670, 120), (730, 170), (800, 210), (860, 250), (880, 300), (850, 335), (770, 335), (700, 345), (620, 360), (530, 345), (480, 310)]
    blob(d, S(head), lw * 1.1, rng, amp=0.8)
    # nostril, mouth (flat, deliberately unreadable)
    blob(d, S([(846, 268), (860, 262), (866, 276), (852, 284)]), 3 * SS, rng, fill=INK)
    brush(d, S(catmull([(640, 322), (720, 318), (800, 316)], 6)), 5 * SS, rng, taper=(0.4, 0.5))
    # head stubble
    for i in range(20):
        x = rng.uniform(520, 700); y = rng.uniform(150, 300)
        brush(d, S([(x, y), (x + rng.uniform(-6, 6), y + 14)]), 3.5 * SS, rng)
    # near ear: long, hanging over the shoulder
    blob(d, S([(560, 165), (520, 190), (500, 270), (510, 380), (540, 420), (565, 380), (575, 270)]), lw, rng)
    # eye: big white, upper lid lowered (ink), pupil sliding down-left
    ex, ey, er = 650, 210, 52
    eye = arc(ex, ey, er, er * 1.05, 0, 360, 40)
    d.polygon(S(eye), fill=PAPER)
    lid = arc(ex, ey, er, er * 1.05, 0, 180, 20)
    lid_line = [(ex - er, ey - 6), (ex, ey - 2), (ex + er, ey - 8)]
    d.polygon(S(lid + lid_line[::-1]), fill=INK)
    brush(d, S(eye + [eye[0]]), lw, rng, taper=(0.05, 0.05))
    brush(d, S(catmull([(ex - er - 6, ey - 4), (ex, ey + 2), (ex + er + 8, ey - 10)], 6)), lw, rng)
    d.ellipse(S([(ex - 34, ey + 2), (ex - 6, ey + 34)]), fill=INK)  # pupil, low, toward envelope
    # arms and envelope on the lap
    # far arm
    blob(d, S([(600, 420), (650, 440), (640, 560), (600, 600), (565, 580), (590, 520)]), lw, rng)
    # envelope (unopened, flap closed): slightly tilted
    env = [(400, 535), (620, 515), (632, 640), (412, 660)]
    d.polygon(S(env), fill=PAPER)
    brush(d, S(env + [env[0]]), lw * 0.9, rng, taper=(0.03, 0.03))
    brush(d, S([(400, 535), (515, 600), (620, 515)]), 5 * SS, rng)
    brush(d, S([(412, 660), (500, 598)]), 3.5 * SS, rng)
    brush(d, S([(632, 640), (530, 594)]), 3.5 * SS, rng)
    # seal dot
    d.ellipse(S([(505, 590), (525, 610)]), fill=INK)
    # hands pinning envelope edges
    blob(d, S([(360, 560), (410, 540), (440, 560), (430, 600), (390, 615), (355, 600)]), lw, rng)
    for t in range(3):
        brush(d, S([(408 + t * 9, 560), (420 + t * 9, 590)]), 3.5 * SS, rng)
    blob(d, S([(600, 560), (645, 545), (670, 575), (655, 615), (610, 620)]), lw, rng)
    for t in range(3):
        brush(d, S([(612 + t * 10, 565), (618 + t * 10, 600)]), 3.5 * SS, rng)
    # near arm from shoulder to near hand
    blob(d, S([(400, 400), (440, 410), (430, 500), (420, 560), (380, 580), (360, 540), (370, 460)]), lw, rng)

    out = im.resize((size, size), Image.LANCZOS)
    return out


def art_hash(img):
    return hashlib.sha256(img.tobytes()).hexdigest()[:16]


if __name__ == '__main__':
    p = draw_plate(800)
    p.save('/tmp/claude-0/-home-user/a99ec93a-6f31-57b0-a2ec-fb930dfe1aad/scratchpad/plate.png')
    print(art_hash(p))

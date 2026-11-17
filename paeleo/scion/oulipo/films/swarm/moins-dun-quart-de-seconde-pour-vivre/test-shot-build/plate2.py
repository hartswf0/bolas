"""Test-shot plate: the one brush plate, re-framed tighter than kf-1 (plan.md section 10).

Drawn by brush (hand.py dab chains) in a 1000-unit square, rendered at 1080 px,
reduced once to the 540 px occurrence raster, including the hand panel border.
Head + torso fill ~70% of panel height, bench cropped by the panel edges,
lamp globe top-left, upper ~35% left black for balloons, eye at ~0.45 width.
"""
import hashlib
import math
import numpy as np
from PIL import Image, ImageDraw
from hand import brush, blob, catmull, arc, wobble, INK, PAPER

PX = 540
SS = 1080 / 1000.0  # 1000 units -> 1080 px working raster
INK_V = 19          # #131313, inside the #121212-#151515 band


def S(pts):
    return [(x * SS, y * SS) for x, y in pts]


def tone(img):
    """Map the 0..255 working raster to the target ink/paper values (ink #131313, paper #FFFFFF)."""
    lut = [int(round(INK_V + v * (255 - INK_V) / 255)) for v in range(256)]
    return img.point(lut)


# --- regions the balloons may never cover (in 540 px panel coords)
EYE_BOX = (190, 180, 300, 285)
FLAP_BOX = (175, 375, 340, 455)
LAMP_BOX = (18, 30, 112, 128)
SNOUT_TIP = (480, 268)


def draw_plate(seed=11):
    W = 1080
    im = Image.new('L', (W, W), INK)
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(seed)
    lw = 8 * SS

    # stars: a few white crosses in the night
    for (x, y, s) in ((330, 48, 9), (585, 150, 7), (930, 62, 10), (760, 268, 7), (240, 300, 6)):
        brush(d, S([(x - s, y + 1), (x + s, y - 1)]), 4.2 * SS, rng, col=PAPER, taper=(0.3, 0.3))
        brush(d, S([(x + 1, y - s), (x - 1, y + s)]), 4.2 * SS, rng, col=PAPER, taper=(0.3, 0.3))

    # lamp: globe top-left, post down behind the bench
    brush(d, S([(118, 205), (121, 1010)]), 22 * SS, rng, col=PAPER, taper=(0, 0), press=0.08)
    brush(d, S([(105, 210), (108, 1010)]), 5 * SS, rng, taper=(0, 0))
    brush(d, S([(131, 210), (134, 1010)]), 5 * SS, rng, taper=(0, 0))
    blob(d, S([(78, 196), (160, 196), (146, 226), (92, 226)]), lw * 0.8, rng)            # collar
    blob(d, S([(119, 52), (176, 74), (200, 128), (176, 184), (119, 202), (62, 184), (38, 128), (62, 74)]), lw, rng, amp=1.1)
    blob(d, S([(96, 44), (142, 44), (134, 58), (104, 58)]), lw * 0.7, rng)              # cap
    # broken white highlight -> drawn as broken ink hatching inside the white globe (no glow)
    for k in range(4):
        x0 = 72 + k * 15
        brush(d, S([(x0, 96 + k * 3), (x0 + 7, 124 + k * 3)]), 4.5 * SS, rng)
    brush(d, S(arc(119, 128, 62, 58, 200, 250, 8)), 4 * SS, rng)

    # bench back: two long planks cropped by both panel edges
    def plank(y0, y1, sk=0, x0=-30, x1=1030):
        pts = [(x0, y0), ((x0 + x1) / 2, y0 + sk), (x1, y0), (x1, y1), ((x0 + x1) / 2, y1 + sk), (x0, y1)]
        blob(d, S(pts), lw, rng, amp=1.0)
    for x in (230, 860):  # back posts
        blob(d, S([(x - 15, 560), (x + 15, 560), (x + 16, 1030), (x - 16, 1030)]), lw, rng, amp=0.8)
    plank(575, 640, 4)
    plank(690, 752, -3)
    for (y0, y1) in ((588, 628), (702, 742)):
        for i in range(9):
            x = rng.uniform(-10, 980)
            yy = rng.uniform(y0, y1)
            brush(d, S([(x, yy), (x + rng.uniform(30, 80), yy + rng.uniform(-2, 2))]), 3.4 * SS, rng)
        for i in range(5):
            x = rng.uniform(0, 1000); yy = rng.uniform(y0 + 4, y1 - 4)
            d.ellipse(S([(x - 2.5, yy - 2), (x + 2.5, yy + 2)]), fill=INK)

    # far ear, behind the head
    blob(d, S([(345, 380), (300, 420), (270, 520), (282, 620), (312, 640), (336, 560), (360, 450)]), lw, rng)

    # body: big seated mass, cropped at the bottom by the seat and panel
    body = [(250, 700), (275, 600), (340, 545), (470, 530), (580, 560), (650, 640), (690, 760), (700, 900), (690, 1040), (230, 1040), (225, 880)]
    blob(d, S(body), lw * 1.1, rng, amp=1.0)
    for i in range(70):
        x = rng.uniform(260, 690); y = rng.uniform(580, 1000)
        if ((x - 470) / 215) ** 2 + ((y - 800) / 250) ** 2 > 0.8:
            continue
        a = rng.uniform(-0.6, 0.6)
        brush(d, S([(x, y), (x + 13 * math.sin(a), y + 19 * math.cos(a))]), 4.2 * SS, rng)

    # seat front plank, crossing in front of the body near the bottom edge
    plank(930, 1000, 2)
    for i in range(6):
        x = rng.uniform(-10, 980); yy = rng.uniform(942, 988)
        brush(d, S([(x, yy), (x + rng.uniform(30, 80), yy + rng.uniform(-2, 2))]), 3.4 * SS, rng)

    # head: dome with long drooping snout to the right
    head = [(300, 470), (318, 395), (372, 345), (450, 330), (528, 352), (600, 398), (700, 425), (800, 450),
            (885, 478), (912, 515), (890, 552), (820, 560), (700, 566), (600, 585), (500, 600), (390, 585), (322, 540)]
    blob(d, S(head), lw * 1.15, rng, amp=0.8)
    blob(d, S([(872, 492), (889, 486), (896, 502), (879, 510)]), 3 * SS, rng, fill=INK)     # nostril
    brush(d, S(catmull([(610, 552), (700, 546), (800, 541), (860, 538)], 6)), 5.5 * SS, rng, taper=(0.4, 0.5))  # flat mouth
    for i in range(22):
        x = rng.uniform(360, 560); y = rng.uniform(360, 470)
        if math.dist((x, y), (452, 440)) < 72:
            continue
        brush(d, S([(x, y), (x + rng.uniform(-6, 6), y + 14)]), 3.6 * SS, rng)

    # near ear: long, hanging over the shoulder on the left of the eye
    blob(d, S([(372, 358), (330, 385), (312, 470), (318, 590), (345, 650), (375, 610), (390, 480), (395, 400)]), lw, rng)
    for t in range(3):
        brush(d, S([(338 + t * 12, 470 + t * 30), (342 + t * 12, 505 + t * 30)]), 3.4 * SS, rng)

    # eye: big white, upper lid lowered (ink), pupil low toward the envelope
    ex, ey, er = 452, 440, 58
    eye = arc(ex, ey, er, er * 1.04, 0, 360, 44)
    d.polygon(S(eye), fill=PAPER)
    lid = arc(ex, ey, er, er * 1.04, 0, 180, 22)
    lid_line = [(ex - er, ey - 4), (ex, ey + 1), (ex + er, ey - 7)]
    d.polygon(S(lid + lid_line[::-1]), fill=INK)
    brush(d, S(eye + [eye[0]]), lw, rng, taper=(0.05, 0.05))
    brush(d, S(catmull([(ex - er - 7, ey - 2), (ex, ey + 4), (ex + er + 9, ey - 9)], 6)), lw * 1.1, rng)
    d.ellipse(S([(ex - 38, ey + 6), (ex - 6, ey + 40)]), fill=INK)
    d.ellipse(S([(ex - 30, ey + 12), (ex - 23, ey + 19)]), fill=PAPER)  # catch-light

    # far arm
    blob(d, S([(575, 640), (630, 665), (640, 780), (610, 830), (570, 815), (585, 740)]), lw, rng)
    # envelope: unopened, sealed flap with a diamond seal at its point
    env = [(325, 728), (640, 706), (652, 860), (338, 884)]
    d.polygon(S(env), fill=PAPER)
    brush(d, S(env + [env[0]]), lw * 0.9, rng, taper=(0.03, 0.03))
    brush(d, S([(325, 728), (488, 812), (640, 706)]), 5.5 * SS, rng)
    brush(d, S([(338, 884), (460, 806)]), 3.6 * SS, rng)
    brush(d, S([(652, 860), (516, 800)]), 3.6 * SS, rng)
    d.polygon(S([(488, 796), (503, 812), (488, 828), (473, 812)]), fill=INK)                # seal
    # illegible address scribble (a few loops, deliberately unreadable)
    sc = [(420 + i * 9, 846 + 4 * math.sin(i * 1.7)) for i in range(12)]
    brush(d, S(sc), 3 * SS, rng)
    # hands pinning the envelope edges
    blob(d, S([(262, 770), (322, 748), (356, 772), (346, 818), (300, 834), (258, 815)]), lw, rng)
    for t in range(3):
        brush(d, S([(318 + t * 10, 772), (330 + t * 10, 808)]), 3.6 * SS, rng)
    blob(d, S([(612, 770), (662, 752), (690, 786), (674, 832), (622, 838)]), lw, rng)
    for t in range(3):
        brush(d, S([(626 + t * 11, 774), (632 + t * 11, 814)]), 3.6 * SS, rng)
    # near arm from shoulder to near hand
    blob(d, S([(300, 610), (350, 625), (345, 720), (320, 780), (275, 790), (250, 740), (265, 660)]), lw, rng)

    # hand panel border: paper outside a wobbly inset contour, ink brush on it (~9 px at 540)
    m = 8
    edge = []
    for (a, b) in (((m, m), (W - m, m)), ((W - m, m), (W - m, W - m)), ((W - m, W - m), (m, W - m)), ((m, W - m), (m, m))):
        for i in range(30):
            t = i / 30
            edge.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    edge = wobble(edge, 1.6, rng, 5)
    mask = Image.new('L', (W, W), 0)
    ImageDraw.Draw(mask).polygon(edge, fill=255)
    paper = Image.new('L', (W, W), PAPER)
    im = Image.composite(im, paper, mask)
    d = ImageDraw.Draw(im)
    brush(d, edge + [edge[0]], 18, rng, taper=(0, 0), press=0.15)

    out = im.resize((PX, PX), Image.LANCZOS)
    return tone(out)


def art_hash(img):
    return hashlib.sha256(img.tobytes()).hexdigest()


if __name__ == '__main__':
    import sys
    p = draw_plate()
    p.save(sys.argv[1] if len(sys.argv) > 1 else 'plate-540.png')
    print(art_hash(p)[:16])

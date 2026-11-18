import numpy as np
from PIL import Image, ImageDraw
from ink import ink
from page import *

W = '/tmp/claude-0/-home-user/a99ec93a-6f31-57b0-a2ec-fb930dfe1aad/scratchpad/w99/'
SRC = '/home/user/bolas/paeleo/scion/oulipo/films/sources/99-ways-subjective/'
OUT = '/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways-subjective/proposals/'

pg = Image.new('RGB', (1280, 720), PAPER)
rng = np.random.default_rng(7)
P = {
    1: (30, 30, 440, 348), 2: (454, 30, 850, 348), 3: (864, 30, 1250, 348),
    4: (30, 362, 640, 690), 5: (654, 362, 940, 690), 6: (954, 362, 1250, 690),
}
plates = {
    1: (W + 'fr/aaf17c56/086.png', None, dict(dark=0.15, mid=0.42, gamma=1.2, canny=(15, 50))),
    2: (W + 'fr/b6100d97/082.png', (10, 10, 320, 240), dict(dark=0.12, mid=0.40, gamma=1.0, canny=(25, 70), sigma=1.4)),
    3: (W + 'fr/bb5ffe06/004.png', (0, 0, 290, 200), dict(dark=0.14, mid=0.42, canny=(12, 40), sigma=1.8)),
    4: (W + 'fr/af625567/017.png', (10, 30, 320, 225), dict(dark=0.12, mid=0.40, gamma=1.3, canny=(20, 60))),
    5: (W + 'fr/bb5ffe06/012.png', (60, 0, 280, 240), dict(dark=0.14, mid=0.42, canny=(12, 40), sigma=1.8)),
    6: (SRC + 'fridge_540882.jpg', (290, 230, 560, 700), dict(dark=0.10, mid=0.36, canny=(25, 70), sigma=1.3, gamma=1.2)),
}
for k, (path, crop, kw) in plates.items():
    x0, y0, x1, y1 = P[k]
    L = ink(Image.open(path), (x1 - x0, y1 - y0), crop=crop, seed=k, **kw)
    pg.paste(ink_to_rgb(L), (x0, y0))
d = ImageDraw.Draw(pg)
for k, b in P.items():
    border(d, b, 5, rng)

# hand-drawn dial substituted onto the rotoscoped wrist (the time must be readable)
import math
cx, cy, r = 448, 578, 31
d.ellipse([cx-r-5, cy-r-5, cx+r+5, cy+r+5], fill=INK)
d.ellipse([cx-r, cy-r, cx+r, cy+r], fill=PAPER)
for k in range(12):
    a = k*math.pi/6; d.line([(cx+math.sin(a)*(r-3), cy-math.cos(a)*(r-3)), (cx+math.sin(a)*(r-9), cy-math.cos(a)*(r-9))], fill=INK, width=3)
for frac, ln, w in ((1.25/12, 15, 5), (15/60, 25, 3)):
    a = frac*2*math.pi; d.line([(cx, cy), (cx+math.sin(a)*ln, cy-math.cos(a)*ln)], fill=INK, width=w)
caption(pg, (42, 40, 300, 76), 'Out of milk again.', 22)
balloon(pg, 1080, 110, 'What time\nis it?', (1250 - 30, 30), size=27, clip=P[3], rng=np.random.default_rng(3))
# tail of the offscreen voice runs out of the top of the panel
balloon(pg, 150, 420, "It's... 1:15.", (70, 690), size=27, clip=P[4], rng=np.random.default_rng(4))
balloon(pg, 800, 420, 'Thanks!', (940, 362), size=25, clip=P[5], rng=np.random.default_rng(5))
balloon(pg, 1110, 430, 'What was I\nlooking for,\nanyway?!', (1080, 690), size=23, clip=P[6], rng=np.random.default_rng(6))
pg.save(OUT + 'kf-1.png')
print('ok')

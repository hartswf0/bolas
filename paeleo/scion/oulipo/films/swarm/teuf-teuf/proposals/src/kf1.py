"""kf-1  La paroi: articulated charcoal silhouettes on a foraged rock wall.
Beat: rollers, t = 27.0 s. The block rides two logs; the third has just
rolled out behind and lies free; the carrier sets a log down in front."""
import math, sys
import numpy as np
from PIL import Image
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from common import *
from puppet import figure

GROUND = 566
img = rock_wall()
xs = np.arange(W, dtype=np.float32)
img = charcoal_band(img, lambda x: x * 0 - 40, lambda x: 58 + 22 * np.sin(x / 210 + 0.6) + 10 * np.sin(x / 67), dark=0.16, seed=3)
img = charcoal_band(img, lambda x: GROUND + 26 + 14 * np.sin(x / 260 + 1.3) + 5 * np.sin(x / 41), lambda x: x * 0 + 800, dark=0.18, seed=4)

# the ghost: where the drag stopped (beat 1), scratched in white, like the reference's engraved outlines
gx0, gy1 = 150, GROUND
ghost = [[(gx0, gy1 - 4), (gx0 + 6, gy1 - 118), (gx0 + 250, gy1 - 124), (gx0 + 258, gy1 - 2), (gx0, gy1 - 4)],
         [(gx0 - 30, gy1 + 2), (gx0 + 290, gy1 + 4)]]
img = scratch(img, ghost, width=2, seed=11, light=1.04)
# drag grooves scratched into the ground band behind
img = scratch(img, [[(60, GROUND + 40 + i * 9), (430, GROUND + 38 + i * 9)] for i in range(3)], width=1, seed=12)

# ground line: a charcoal stroke
gl = poly_mask([[(0, GROUND), (W, GROUND), (W, GROUND + 4), (0, GROUND + 5)]])
img = spray(img, gl, reach=8, density=0.25, seed=5, darkness=0.6)
img = ink_fill(img, gl * 0.9, seed=6)

# ---- the load: a dressed stone block (cut card), on two of three logs
R = 26
logs = [(628, GROUND - R, 0.0), (800, GROUND - R + 1, 0.0)]       # under the block
loose = (300, GROUND - R + 2, 0.0)                                 # rolled out behind
front = (960, GROUND - R - 1, 0.0)                             # being set down in front
bx0, bx1, btop = 590, 830, 400
bot = GROUND - 2 * R
rng_b = np.random.default_rng(5)
block = []
cx, cy = (bx0 + bx1) / 2, (btop + bot) / 2 + 4
for t in np.linspace(0, 2 * math.pi, 48, endpoint=False):
    rx, ry = (bx1 - bx0) / 2 + 40, (bot - btop) / 2 + 8
    r = 1 + 0.05 * rng_b.normal() + 0.06 * math.sin(3 * t + 1)
    x, y = cx + rx * r * math.cos(t), cy + ry * r * math.sin(t) * (1.0 if math.sin(t) < 0 else 0.92)
    y = min(y, bot + 2)
    block.append((x, y))
bm = poly_mask([block])
img = spray(img, bm, reach=20, density=0.45, seed=7)
img = ink_fill(img, bm, seed=8, dry=0.5)
# chisel marks on the block, scratched light
img = scratch(img, [[(bx0 + 20 + i * 9, btop + 12 + abs(i - 10) * 1.2), (bx0 + 60 + i * 9, btop + 30)] for i in range(0, 20, 3)], width=1, seed=13, light=0.45)

# logs end-on: black discs with a scratched ring and a radial mark (shows the turn)
def log(img, c, ang, seed):
    rr = np.random.default_rng(seed)
    m = poly_mask([[(c[0] + R * (1 + 0.05 * rr.normal()) * math.cos(t), c[1] + R * (1 + 0.05 * rr.normal()) * math.sin(t)) for t in np.linspace(0, 6.28, 28, endpoint=False)]])
    img = spray(img, m, reach=10, density=0.4, seed=seed)
    img = ink_fill(img, m, seed=seed + 1)
    ring = [(c[0] + 15 * math.cos(t), c[1] + 13 * math.sin(t)) for t in np.linspace(0, 6.3, 30)]
    rad = [(c[0], c[1]), (c[0] + 19 * math.cos(ang), c[1] + 19 * math.sin(ang))]
    return scratch(img, [ring, rad], width=1, seed=seed + 2, light=0.8)

# the logs turn at half the block's speed: block has moved 0.61 m since the
# last swap, logs have turned (distance/2)/R
for i, (x, y, _) in enumerate(logs):
    img = log(img, (x, y), 1.9 + i * 0.3, 20 + i * 3)
img = log(img, loose[:2], 4.1, 40)

# ---- puppets
pusher, J1 = figure(hip=(468, 470), lean_deg=40, feet=[(388, GROUND - 3), (466, GROUND - 3)],
                    hands=[(bx0 - 30, 440), (bx0 - 32, 462)], scale=1.05, head_tilt=-28,
                    knee_bend=(-1, -1), elbow_bend=(-1, -1))
carrier, J2 = figure(hip=(1040, 474), lean_deg=-38, feet=[(1050, GROUND - 3), (980, GROUND - 3)],
                     hands=[(front[0] + 4, front[1] - 20), (front[0] + 18, front[1] - 8)], scale=1.0,
                     head_tilt=-30, knee_bend=(1, 1), elbow_bend=(1, 1))
for k, parts in enumerate([pusher, carrier]):
    m = poly_mask(parts)
    img = spray(img, m, reach=14, density=0.35, seed=60 + k, darkness=0.7)
    img = ink_fill(img, m, seed=70 + k, dry=0.3)
img = log(img, front[:2], 0.6, 50)

# contact ticks: a small scratched mark where each log meets the ground
img = scratch(img, [[(x - 6, GROUND + 9), (x + 6, GROUND + 9)] for x, _, _ in logs + [loose]], width=2, seed=90, light=1.05)

im = finish(img, seed=1)
caption(im, "« Et moi ? » dit le rouleau qu'on laisse derrière.", y=664)
im.save(OUT + "/kf-1.png")
print("ok")

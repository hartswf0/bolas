"""kf-3  Pochoirs du mouvement: a procedural simulation printed as blown-pigment
stencils. Three bands of the same wall, the same hand, the same 7 s push.
Every 0.5 s the load leaves a negative stencil (pigment blown round it, as
round the reference's hands); the spacing of the stencils is the speed.
Beat: the comparison held at the end of the proof, t = 52.0 s (push clock 7.0 s)."""
import math, sys
import numpy as np, cv2
from PIL import Image, ImageDraw
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from common import *

rng = np.random.default_rng(3)
PX = 125.0            # px per metre
X0 = 120              # load's start (left edge)
LW, LH = 92, 58       # load size
GROUNDS = [232, 420, 606]

# ---- the simulation (same input force, same geometry; outcomes from the
# film's fixture: drag 1.2 m, rollers 3.0 m, wheels 8.0 m in 7 s)
def drag(t):          # stick-slip: each 0.7 s stroke slips 0.12 m, then sticks
    k = math.floor(t / 0.7); f = (t / 0.7) - k
    return 0.12 * (k + min(1.0, f / 0.35))
def rollers(t):       # 0.75 m/s while on logs; every 1.0 m a log falls out behind
    x = 0.0; s = 0.0; dt = 0.01; wait = 0.0
    while s < t - 1e-9:
        if wait > 0: wait -= dt
        else:
            x += 0.75 * dt
            if int((x) / 1.0) != int((x - 0.75 * dt) / 1.0): wait = 1.25   # carry it to the front
        s += dt
    return x
def wheels(t):        # rolling resistance small: the push accelerates it
    return 8.0 * (t / 7.0) ** 1.6
SIMS = [drag, rollers, wheels]
for f, want in zip(SIMS, [1.2, 3.0, 8.0]):
    assert abs(f(7.0) - want) < 0.12, (f.__name__, f(7.0))

# ---- wall: the foraged rock (Cueva de las Manos) re-toned, three bands
img = rock_wall()
img = img * 0.5 + tone(np.full((H, W), 0.93, np.float32)) * 0.5     # quieter than kf-1
img = charcoal_band(img, lambda x: x * 0 - 40, lambda x: 46 + 12 * np.sin(x / 230) + 5 * np.sin(x / 61), dark=0.18, seed=61)
for i, g in enumerate(GROUNDS[:2]):
    img = charcoal_band(img, lambda x, g=g, i=i: g + 10 + 6 * np.sin(x / 190 + i) + 3 * np.sin(x / 37),
                        lambda x, g=g, i=i: g + 34 + 8 * np.sin(x / 240 + 2 * i) + 3 * np.sin(x / 53), dark=0.2, seed=62 + i)
img = charcoal_band(img, lambda x: GROUNDS[2] + 12 + 7 * np.sin(x / 270 + 2) + 3 * np.sin(x / 45), lambda x: x * 0 + 800, dark=0.2, seed=65)

rb = np.random.default_rng(5)
def load_poly(x, g, lift=14):
    pts = []
    cx, cy = x + LW / 2, g - LH / 2 - lift
    for t in np.linspace(0, 2 * math.pi, 40, endpoint=False):
        r = 1 + 0.045 * math.sin(3 * t + 1) + 0.03 * math.sin(5 * t)
        y = cy + LH / 2 * r * math.sin(t)
        pts.append((cx + LW / 2 * r * math.cos(t), min(y, g - lift)))
    return pts

def hand_poly(x, y, s=1.0):
    """a hand, palm to the wall, fingers pointing along the push (made, not traced)"""
    parts = [("ellipse", x, y, 17 * s, 20 * s)]
    for i, (ang, L) in enumerate([(-38, 30), (-14, 40), (0, 44), (14, 40), (34, 30)]):
        a = math.radians(ang)
        bx, by = x + 12 * s * math.cos(a), y + 15 * s * math.sin(a) * 1.2
        ex, ey = bx + L * s * math.cos(a), by + L * s * math.sin(a) * 0.55
        parts.append(limb((bx, by), (ex, ey), 6 * s, 4.2 * s))
    parts.append(limb((x - 10 * s, y + 14 * s), (x + 20 * s, y + 38 * s), 7 * s, 5 * s))   # thumb
    return parts

def stencil(img, mask, strength, seed, reach=16):
    """negative stencil: pigment blown round the mask, the mask stays bare wall"""
    out = spray(img, mask, reach=reach, density=0.55 * strength, seed=seed, darkness=0.9 * strength)
    lift = cv2.GaussianBlur(mask, (0, 0), 1.0)[..., None] * 0.06 * strength
    return out * (1 - lift) + np.clip(CREAM * 1.05, 0, 255) * lift

for lane, (sim, g) in enumerate(zip(SIMS, GROUNDS)):
    # ruler: metre ticks scratched along the ground
    ticks = [[(X0 + m * PX, g - 1), (X0 + m * PX, g + 6 + (4 if m % 2 == 0 else 0))] for m in range(0, 9)]
    img = scratch(img, ticks + [[(X0 - 30, g), (X0 + 8 * PX + 70, g)]], width=1, seed=70 + lane, light=1.02)
    # the same hand at the start of every lane
    img = stencil(img, poly_mask(hand_poly(X0 - 52, g - 60, 0.9)), 1.0, 80 + lane, reach=14)
    # stencils every 0.5 s, older ones fainter
    times = np.arange(0.0, 7.0 + 1e-6, 0.5)
    xs = [X0 + sim(t) * PX for t in times]
    for j, (t, x) in enumerate(zip(times[:-1], xs[:-1])):
        st = 0.30 + 0.55 * (j / (len(times) - 1))
        img = stencil(img, poly_mask([load_poly(x, g, 24 if lane == 2 else 14)]), st, 100 + lane * 20 + j)
    # the load now: solid charcoal on its mechanism
    xn = xs[-1]
    lm = poly_mask([load_poly(xn, g, 24 if lane == 2 else 14)])
    if lane == 0:     # sledge runner
        mech = poly_mask([[(xn - 8, g - 14), (xn + LW + 14, g - 14), (xn + LW + 4, g - 3), (xn - 4, g - 3)]])
    elif lane == 1:   # three logs; the last fell out behind
        mech = poly_mask([("ellipse", xn + 18, g - 7, 7, 7), ("ellipse", xn + 72, g - 7, 7, 7),
                          ("ellipse", xn - 34, g - 7, 7, 7)])
    else:             # two wheels on an axle beam
        mech = poly_mask([("ellipse", xn + 20, g - 12, 12, 12), ("ellipse", xn + 72, g - 12, 12, 12),
                          [(xn + 14, g - 26), (xn + 80, g - 26), (xn + 80, g - 21), (xn + 14, g - 21)]])
    m = np.maximum(lm, mech)
    img = spray(img, m, reach=12, density=0.35, seed=150 + lane, darkness=0.7)
    img = ink_fill(img, m, seed=160 + lane)
    if lane == 2:     # spokes scratched in so the turn reads
        for cx in (xn + 20, xn + 72):
            img = scratch(img, [[(cx - 9 * math.cos(a), g - 12 - 9 * math.sin(a)), (cx + 9 * math.cos(a), g - 12 + 9 * math.sin(a))]
                                for a in (0.4, 1.45, 2.5)], width=1, seed=int(cx), light=0.7)

im = finish(img, seed=3)
d = ImageDraw.Draw(im)
fm = font(17, "mono"); fs = font(22, "serif-italic")
labels = ["traîné", "sur rouleaux", "sur roues"]
for lane, (sim, g) in enumerate(zip(SIMS, GROUNDS)):
    for mtr in range(0, 9):
        d.text((X0 + mtr * PX - 4, g + 10), str(mtr), font=fm, fill=(236, 230, 210))
    d.text((X0 - 78, g - 120), labels[lane], font=fs, fill=(30, 27, 24))
    v = sim(7.0)
    txt = f"{v:.1f} m".replace(".", ",")
    tx = min(X0 + v * PX + LW + 18, W - 92)
    ty = g - 64 if lane < 2 else g - 104
    d.text((tx, ty), txt, font=font(24, "mono"), fill=(30, 27, 24))
d.text((W - 210, 14), "t = 7,0 s", font=font(22, "mono"), fill=(236, 230, 210))
caption(im, "Même main, même poussée, sept secondes : seule la roue a de l'avenir.", y=664, size=25)
im.save(OUT + "/kf-3.png")
print("ok")

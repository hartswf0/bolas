"""kf-2  Ombres des relevés: figures cut out of two public-domain engravings
(Wilkinson's el-Bersheh colossus; Layard's Kouyunjik haulers and cart wheels)
as solid shadow-theatre silhouettes, recomposed on a charcoal mural ground.
Beat: the wheel, t = 40.0 s. The colossus's sledge now rides on two Layard
wheels; three haulers do what a crowd did; the crowd stands idle behind."""
import math, sys
import numpy as np, cv2
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from common import *
from cut import cut, place

GROUND = 594
rng = np.random.default_rng(7)

# ---- ground: handmade mural ground (procedural cream wash + brush mottling)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
n1 = cv2.GaussianBlur(rng.random((H, W)).astype(np.float32), (0, 0), 60)
n2 = cv2.GaussianBlur(rng.random((H, W)).astype(np.float32), (0, 0), sigmaX=30, sigmaY=4)
n1 = (n1 - n1.mean()) / n1.std(); n2 = (n2 - n2.mean()) / n2.std()
l = 0.90 + 0.035 * n1 + 0.008 * n2 + 0.02 * rng.normal(0, 1, (H, W))
img = tone(l)
img = charcoal_band(img, lambda x: x * 0 - 40, lambda x: 70 + 26 * np.sin(x / 260 + 2.0) + 9 * np.sin(x / 55), dark=0.2, seed=21)
img = charcoal_band(img, lambda x: GROUND + 22 + 16 * np.sin(x / 300 + 0.4) + 6 * np.sin(x / 47), lambda x: x * 0 + 800, dark=0.2, seed=22)
# blown dot clusters, as in the reference's upper right
dots = np.zeros((H, W), np.float32)
for cx, cy, n in [(1060, 170, 160), (90, 300, 60)]:
    for _ in range(n):
        x = int(cx + rng.normal(0, 70)); y = int(cy + rng.normal(0, 30))
        if 0 <= x < W - 4 and 0 <= y < H - 4:
            cv2.ellipse(dots, (x, y), (int(rng.integers(2, 4)), 2), float(rng.integers(0, 180)), 0, 360, 1.0, -1)
dots = cv2.GaussianBlur(dots, (0, 0), 0.7)
img = img * (1 - 0.8 * dots[..., None]) + INK * 0.8 * dots[..., None]

def shade(img, sil, line, darkness=1.0, seed=0, reach=16):
    """silhouette in charcoal; the engraving's own interior lines show as light
    scratches inside the black (the reference's grey brushed detail)"""
    img = spray(img, sil, reach=reach, density=0.35 * darkness, seed=seed, darkness=0.7 * darkness)
    m = cv2.GaussianBlur(sil, (0, 0), 0.8) * darkness
    blk = tone(np.full(sil.shape, 0.06, np.float32))
    img = img * (1 - m[..., None]) + blk * m[..., None]
    a = np.clip(line * sil, 0, 1) * 0.45 * darkness
    return img * (1 - a[..., None]) + (CREAM * 0.55) * a[..., None]

# ---- back plane: the idle crowd (Wilkinson hauler row), paler = further
crowd_s, crowd_l = cut("drag_djehutihotep.jpg", (480, 132, 1000, 221), close=3)
M1 = np.zeros((H, W), np.float32); L1 = np.zeros((H, W), np.float32)
place(M1, L1, crowd_s, crowd_l, 20, GROUND - 6 - 94 * 0.92, scale=0.92)
img = shade(img, M1, L1, darkness=0.55, seed=31, reach=10)

# ghosts of the previous mechanism: the rollers, scratched in white where they were left
img = scratch(img, [[(cx + 22 * math.cos(t), GROUND - 22 + 22 * math.sin(t)) for t in np.linspace(0, 6.3, 26)]
                    for cx in (520, 575)], width=2, seed=33, light=1.05)
img = scratch(img, [[(470, GROUND + 3), (620, GROUND + 4)]], width=2, seed=34)

# ---- the load: the colossus on its sledge (Wilkinson), now on wheels (Layard)
col_s, col_l = cut("drag_djehutihotep.jpg", (160, 12, 395, 445), keep_largest=1)
sc = 0.80
R = 48                                   # wheel radius after scaling
axle_y = GROUND - R
top = axle_y - 433 * sc + 14             # the sledge runner sits across the axles
CX = 640
M2 = np.zeros((H, W), np.float32); L2 = np.zeros((H, W), np.float32)
place(M2, L2, col_s, col_l, CX, top, scale=sc)

# a cut-card axle beam under the runner (handmade), one per wheel
beam = poly_mask([[(CX + 8, axle_y - 6), (CX + 235 * sc - 6, axle_y - 6), (CX + 235 * sc - 6, axle_y + 4), (CX + 8, axle_y + 4)]])
M2 = np.maximum(M2, beam)
img = shade(img, M2, L2, seed=35)

# wheels: the spoked cart wheels cut from the Layard plate; rim and spokes are
# the cut, the gaps open onto the wall so rotation reads frame by frame
def wheel(img, src_c, cx, cy, rot, seed):
    x0, y0 = src_c[0] - 36, src_c[1] - 36
    a = load("roll_nineveh_c.jpg")[y0:y0 + 72, x0:x0 + 72].mean(2)
    ln = np.clip((175 - a) / 90, 0, 1).astype(np.float32)
    ln = cv2.dilate(ln, np.ones((2, 2), np.uint8))
    hh, ww = ln.shape
    yy2, xx2 = np.mgrid[0:hh, 0:ww]
    rr = np.sqrt((xx2 - 36) ** 2 + (yy2 - 36) ** 2)
    ln = ln * (rr <= 34)
    ring = ((rr > 28) & (rr <= 34)).astype(np.float32)   # make the rim solid
    hub = (rr < 5).astype(np.float32)
    sil = np.clip(ln + ring + hub, 0, 1)
    s = R / 34.0
    Mw = np.zeros((H, W), np.float32); Lw = np.zeros((H, W), np.float32)
    place(Mw, Lw, sil, np.zeros_like(sil), cx - 36 * s, cy - 36 * s, scale=s, rot=rot)
    return shade(img, Mw, Lw, seed=seed, reach=8)

img = wheel(img, (1150, 208), CX + 40, axle_y, 23, 41)
img = wheel(img, (1165, 670), CX + 235 * sc - 34, axle_y, 61, 42)
# contact: a short bright scratch where each wheel meets the ground
img = scratch(img, [[(x - 7, GROUND + 7), (x + 7, GROUND + 7)] for x in (CX + 40, CX + 235 * sc - 34)], width=2, seed=43)

# ---- the three haulers (Layard), mirrored to pull to the right
hau_s, hau_l = cut("roll_nineveh_c.jpg", (0, 428, 175, 528), flip=True, close=5, thr=135)
M3 = np.zeros((H, W), np.float32); L3 = np.zeros((H, W), np.float32)
hs = 1.45
place(M3, L3, hau_s, hau_l, 880, GROUND - 100 * hs + 6, scale=hs)
img = shade(img, M3, L3, seed=51)
# the rope: a charcoal cord from the sledge prow to the haulers' hands
rope = poly_mask([[(CX + 235 * sc - 10, GROUND - 122), (905, GROUND - 78), (905, GROUND - 74), (CX + 235 * sc - 10, GROUND - 117)]])
img = ink_fill(img, rope, seed=52)

im = finish(img, seed=2)
caption(im, "La roue : « Je tourne sur place, et c'est vous qui avancez. »", y=664)
im.save(OUT + "/kf-2.png")
print("ok")

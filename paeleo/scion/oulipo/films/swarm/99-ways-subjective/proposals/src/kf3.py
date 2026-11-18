"""Direction 3: photo-collage multiplane. The panels are windows cut in the page (nearest plane); behind them
foraged photographs are cut into depth planes; the head turn is a camera yaw with per-plane parallax and smear."""
import numpy as np, cv2
from PIL import Image, ImageDraw
from page import *

W = '/tmp/claude-0/-home-user/a99ec93a-6f31-57b0-a2ec-fb930dfe1aad/scratchpad/w99/'
SRC = '/home/user/bolas/paeleo/scion/oulipo/films/sources/99-ways-subjective/'
OUT = '/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways-subjective/proposals/'

def grey(path):
    a = np.asarray(Image.open(path).convert('L'), np.float32)
    lo, hi = np.percentile(a, 1), np.percentile(a, 99.5)
    a = np.clip((a - lo) / (hi - lo), 0, 1)
    a = a ** 1.15
    return a

def fit(a, wh, crop=None):
    if crop: a = a[crop[1]:crop[3], crop[0]:crop[2]]
    Wt, Ht = wh; h, w = a.shape[:2]; s = max(Wt / w, Ht / h)
    a = cv2.resize(a, (int(w * s + .5), int(h * s + .5)), interpolation=cv2.INTER_CUBIC)
    oy, ox = (a.shape[0] - Ht) // 2, (a.shape[1] - Wt) // 2
    return a[oy:oy + Ht, ox:ox + Wt]

def smear(a, px):
    if px < 2: return a
    k = np.zeros((1, int(px)), np.float32); k[0] = 1 / int(px)
    return cv2.filter2D(a, -1, k, borderType=cv2.BORDER_REFLECT)

pg = np.full((720, 1280), 0.96, np.float32)
P = {1: (30, 30, 440, 348), 2: (454, 30, 850, 348), 3: (864, 30, 1250, 348),
     4: (30, 362, 640, 690), 5: (654, 362, 940, 690), 6: (954, 362, 1250, 690)}
def put(k, a):
    x0, y0, x1, y1 = P[k]; pg[y0:y1, x0:x1] = a

put(1, fit(grey(W + 'fr/aaf17c56/086.png'), (410, 318)))
put(2, fit(grey(W + 'fr/b6100d97/082.png'), (396, 318), (10, 10, 320, 240)))
kit = grey(SRC + 'fridge_540800.jpg')            # 960x767: dark doorway on the left, the kitchen wall to the right
put(3, fit(kit, (386, 318), (0, 0, 300, 520)))   # looking at the doorway the voice comes from
put(5, fit(grey(W + 'fr/bb5ffe06/012.png'), (286, 328), (60, 0, 280, 240)))
put(6, fit(grey(SRC + 'fridge_540882.jpg'), (296, 328), (300, 230, 560, 700)))

# ---- panel 4, multiplane head turn (camera yawing right at this frame)
x0, y0, x1, y1 = P[4]; pw, ph = x1 - x0, y1 - y0
yaw = 0.62                                           # 0 = facing doorway, 1 = facing the clock wall
wall = grey(SRC + 'fridge_540882.jpg')
far = fit(np.hstack([kit[0:420, 0:330], wall[20:440, 60:900]]), (int(pw * 2.0), ph))  # far plane: doorway .. papered wall over the refrigerator, joined at a cut
fx = int((far.shape[1] - pw) * yaw)
plate = smear(far[:, fx:fx + pw], 26)
# mid plane: the clock, cut from the 1966 film frame as an ellipse, hung on the wall plane; parallax ratio 1.35
clk = grey(W + 'fr/adfad259/010.png')
m = np.zeros(clk.shape, np.uint8); cv2.ellipse(m, (332, 218), (226, 200), -8, 0, 360, 255, -1)
cy0, cy1, cx0, cx1 = 10, 430, 100, 565
clk, m = clk[cy0:cy1, cx0:cx1], m[cy0:cy1, cx0:cx1].astype(np.float32) / 255
cs = 0.42
clk = cv2.resize(clk, None, fx=cs, fy=cs, interpolation=cv2.INTER_AREA); m = cv2.resize(m, (clk.shape[1], clk.shape[0]))
clk = smear(clk, 12); m = smear(m, 12)
cx = int(pw - 150 - (yaw - 0.62) * 900)              # enters from the right edge as yaw grows
cyp = 22
ch, cw = clk.shape
xa, xb = max(0, cx), min(pw, cx + cw); sub = slice(xa - cx, xb - cx)
# contact shadow on the wall
sh = cv2.GaussianBlur(m, (0, 0), 6)
ya = cyp + 8; plate[ya:ya + ch, xa + 6:min(pw, xb + 6)] *= (1 - 0.35 * sh[:, sub][:, :min(pw, xb + 6) - (xa + 6)])
plate[cyp:cyp + ch, xa:xb] = plate[cyp:cyp + ch, xa:xb] * (1 - m[:, sub]) + clk[:, sub] * m[:, sub]
# near plane: the doorframe jamb, cut from the same photo, crossing fastest (parallax 2.6) and blurred by speed
jamb = fit(kit, (120, ph), (40, 0, 130, 760))
jx = int(-40 - (yaw - 0.5) * 900)
jm = np.ones_like(jamb)
jj = smear(jamb * 0.45, 70); jmm = smear(jm, 70)
xa, xb = max(0, jx), min(pw, jx + 120)
if xb > xa:
    plate[:, xa:xb] = plate[:, xa:xb] * (1 - jmm[:, xa - jx:xb - jx]) + jj[:, xa - jx:xb - jx]
pg[y0:y1, x0:x1] = plate

img = Image.fromarray((np.clip(pg, 0, 1) * 255).astype(np.uint8), 'L').convert('RGB')
# the page plane: warm board with the panel windows cut out
paper = np.asarray(img).astype(np.float32)
mask = np.ones((720, 1280), bool)
for b in P.values(): mask[b[1]:b[3], b[0]:b[2]] = False
paper[mask] = np.array(PAPER, np.float32)
# window bevel shadow: the page sits in front of the photographs
sh = np.zeros((720, 1280), np.float32); sh[mask] = 1
sh = cv2.GaussianBlur(np.roll(sh, (5, 5), (0, 1)), (0, 0), 4)
paper[~mask] *= (1 - 0.5 * sh[~mask])[:, None]
img = Image.fromarray(paper.astype(np.uint8), 'RGB')
d = ImageDraw.Draw(img); rng = np.random.default_rng(9)
for b in P.values(): border(d, b, 4, rng)
caption(img, (42, 40, 300, 76), 'Out of milk again.', 22)
balloon(img, 1110, 110, 'What time\nis it?', (864, 120), size=27, clip=P[3], rng=np.random.default_rng(3))
balloon(img, 170, 610, "Twenty to\nseven!", (90, 690), size=25, clip=P[4], rng=np.random.default_rng(4))
balloon(img, 800, 410, 'Thanks!', (940, 362), size=24, clip=P[5], rng=np.random.default_rng(5))
balloon(img, 1100, 418, 'What was I\nafter, anyway?!', (1230, 690), size=22, clip=P[6], rng=np.random.default_rng(6))
img.save(OUT + 'kf-3.png'); print('ok')

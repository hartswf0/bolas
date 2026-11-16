"""Static stage planes for the test shot: Russell Lee time-clock plate (8c01492v), the pail occluder cut from it,
and the handmade CAPOREPARTO doorway. Stage is 1296x729 (WIDE = whole stage; MEDIUM = 960x540 crop, a 1.35x push)."""
import os, numpy as np, cv2, math
from PIL import Image, ImageDraw, ImageFont
B = os.path.dirname(os.path.abspath(__file__)); C = B + '/cache'
SRC = '/home/user/bolas/paeleo/scion/oulipo/films/sources/renzo-e-luciana'
SW, SH = 1296, 729
X0, Y0, X1, Y1 = 18, 160, 1014, 720
k = SW / (X1 - X0)
pl = np.asarray(Image.open(SRC + '/loc/8c01492v.jpg').convert('L'))[Y0:Y1, X0:X1]
pl = cv2.resize(pl, (SW, SH), interpolation=cv2.INTER_LANCZOS4)
CX, CY, CR = (482 - X0) * k, (228 - Y0) * k, 33 * k
# erase the photographed hands (inpaint inside the dial only); the film's own paper hands are drawn per frame
ring = np.zeros_like(pl); cv2.circle(ring, (int(CX), int(CY)), int(CR * .6), 255, -1)
hands = cv2.dilate(((pl < 110) & (ring > 0)).astype(np.uint8) * 255, np.ones((5, 5), np.uint8))
pl = cv2.inpaint(pl, hands, 5, cv2.INPAINT_TELEA)
# pail pile occluder (#45): dark objects on the pale wall in the floor zone, holes filled
reg = np.zeros_like(pl); reg[int(440):, 330:] = 255
box = ((pl < 140) & (reg > 0)).astype(np.uint8) * 255
box = cv2.morphologyEx(box, cv2.MORPH_CLOSE, np.ones((17, 17), np.uint8))
ff = box.copy(); fm = np.zeros((SH + 2, SW + 2), np.uint8); cv2.floodFill(ff, fm, (5, 5), 255)
box = box | cv2.bitwise_not(ff)
box = cv2.morphologyEx(box, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
n, lab, st, _ = cv2.connectedComponentsWithStats(box)
keep = np.zeros_like(box)
for i in range(1, n):
    if st[i, cv2.CC_STAT_AREA] > 4000: keep[lab == i] = 255
box = keep; box[SH - 22:] = 0
np.save(C + '/occ.npy', box)
# ---- handmade doorway: dark card frame cut into the wall, back room paper, a half-door counter ----
def paper(w, h, base, seed, fibre=6):
    rng = np.random.default_rng(seed); n_ = rng.normal(0, 1, (h, w)).astype(np.float32)
    f = cv2.GaussianBlur(n_, (0, 0), 1.0) * fibre * .5 + cv2.GaussianBlur(n_, (0, 0), 20) * fibre * 5
    return np.clip(base + f, 0, 255)
DX0, DY0, DX1, DY1 = 120, 150, 300, 706
np.save(C + '/door.npy', np.array([DX0, DY0, DX1, DY1]))
back = paper(DX1 - DX0, DY1 - DY0, 120, 11); back[: int((DY1 - DY0) * .55)] += 30     # far wall lighter than far floor
Image.fromarray(back.astype(np.uint8)).save(C + '/backroom.png')
fr = Image.new('RGBA', (SW, SH), (0, 0, 0, 0)); d = ImageDraw.Draw(fr)
d.rectangle((DX0 - 14, DY0 - 16, DX1 + 14, DY1 + 4), fill=(40, 40, 40, 255)); d.rectangle((DX0, DY0, DX1, DY1), fill=(0, 0, 0, 0))
# half-door counter (dark card) so the foreman reads as standing at his desk, seen from behind
cnt = paper(DX1 - DX0, DY1 - 470, 70, 4, 5).astype(np.uint8)
cnt_rgba = np.dstack([cnt] * 3 + [np.full_like(cnt, 255)])
fr.alpha_composite(Image.fromarray(cnt_rgba, 'RGBA'), (DX0, 470))
d.line((DX0, 470, DX1, 470), fill=(150, 150, 150, 255), width=3)
sign = Image.new('RGBA', (176, 30), (222, 222, 222, 255)); sd = ImageDraw.Draw(sign)
sd.text((10, 4), 'CAPOREPARTO', font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf', 17), fill=(28, 28, 28, 255))
sign = sign.rotate(-1.0, expand=True, resample=Image.BICUBIC)
fr.alpha_composite(sign, (DX0 + 2, DY0 - 58))
fr.save(C + '/doorframe.png')
# door leaf swung into the room (dark card with a frosted pane), sits in front of the puppets' far edge
leaf = Image.new('RGBA', (SW, SH), (0, 0, 0, 0)); ld = ImageDraw.Draw(leaf)
ld.polygon([(DX1 + 14, DY0 - 16), (DX1 + 66, DY0 + 24), (DX1 + 66, DY1 + 26), (DX1 + 14, DY1 + 4)], fill=(78, 78, 78, 255))
ld.polygon([(DX1 + 26, DY0 + 50), (DX1 + 56, DY0 + 74), (DX1 + 56, DY0 + 250), (DX1 + 26, DY0 + 232)], fill=(150, 150, 150, 255))
leaf.save(C + '/leaf.png')
Image.fromarray(pl).save(C + '/plate.png')
np.save(C + '/clock.npy', np.array([CX, CY, CR]))
print('stage ok', pl.shape, 'clock', CX, CY, CR, 'occ px', int((box > 0).sum()))
# where is the top of the pile per column (for placement)
cols = [(x, int(np.argmax(box[:, x] > 0))) for x in range(340, 1260, 60)]
print(cols)

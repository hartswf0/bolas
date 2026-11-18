"""KF2 · Collage on the time-clock wall: foraged FSA/OWI cutouts, articulated, occluded by the real lunch-pail pile.
Beat: original shift, 12:02 (t = 8 s): the meeting inside the safe window; the foreman, back turned, in the doorway."""
import sys; sys.path.insert(0, '.')
from common import *
import math
C = OUT + '/src/cache'
# --- plate: time clock + card rack + lunch pails (LoC fsa 8c01492v), cropped to 16:9 -----------------
pl = grey(SRC + '/loc/8c01492v.jpg')[195:721, 40:975]
sx = W / pl.shape[1]
pl = cv2.resize(pl, (W, H), interpolation=cv2.INTER_CUBIC)
plu8 = np.clip(pl, 0, 255).astype(np.uint8)
# erase the photographed clock hands; the film's own paper hands go on top (they will move per frame)
cx, cy, r = int((482 - 40) * sx), int((228 - 195) * sx), int(33 * sx)
hm = np.zeros_like(plu8); cv2.circle(hm, (cx, cy), int(r * .78), 255, -1)
ring = np.zeros_like(plu8); cv2.circle(ring, (cx, cy), int(r * .55), 255, -1)
hands = ((plu8 < 110) & (ring > 0)).astype(np.uint8) * 255
hands = cv2.dilate(hands, np.ones((5, 5), np.uint8))
plu8 = cv2.inpaint(plu8, hands, 5, cv2.INPAINT_TELEA)
pl = plu8.astype(np.float32)
# lunch-pail pile as a foreground occluder: dark objects on the pale wall, holes filled
reg = np.zeros_like(plu8); reg[430:, 340:] = 255
box = ((plu8 < 135) & (reg > 0)).astype(np.uint8) * 255
box = cv2.morphologyEx(box, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
ff = box.copy(); h_, w_ = ff.shape; fm = np.zeros((h_ + 2, w_ + 2), np.uint8); cv2.floodFill(ff, fm, (5, 5), 255)
box = box | cv2.bitwise_not(ff)
box = cv2.morphologyEx(box, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
box[700:] = 0  # floor line stays plate
canvas = Image.fromarray(np.stack([plu8] * 3, -1)).convert('RGBA')

# --- the doorway: a handmade card frame cut into the wall; through it, the back room and the foreman ----
d = ImageDraw.Draw(canvas)
DX0, DY0, DX1, DY1 = 18, 118, 158, 694
back = paper(DX1 - DX0, DY1 - DY0, base=150, seed=11, fibre=6)
back[: int((DY1 - DY0) * .62)] += 22            # far wall lighter than far floor
canvas.alpha_composite(Image.fromarray(np.stack([back.astype(np.uint8)] * 3, -1)).convert('RGBA'), (DX0, DY0))
sup = grey(SRC + '/loc/8d28363v.jpg')
ms = grabcut(sup, (312, 236, 562, 968), fg=[[(400, 260), (500, 260), (500, 600), (380, 600)], [(380, 620), (540, 620), (540, 950), (370, 950)]],
             bg=[[(312, 236), (345, 236), (345, 968), (312, 968)]])
L = layer(sup, cut_edge(ms, 4)).crop((312, 236, 562, 968)).transpose(Image.FLIP_LEFT_RIGHT)  # faces into his office: back turned to the pails
paste(canvas, L, (DX0 + 4, DY0 + 120), shadow=(5, 3), blur=5, dark=.5, scale=.62)
# door frame (dark card, cut edges) + leaf swung open into the room
fr = Image.new('RGBA', (W, H), (0, 0, 0, 0)); fd = ImageDraw.Draw(fr)
fd.rectangle((DX0 - 12, DY0 - 14, DX1 + 12, DY1), fill=(52, 50, 48, 255))
fd.rectangle((DX0, DY0, DX1, DY1), fill=(0, 0, 0, 0))
fd.polygon([(DX1, DY0), (DX1 + 34, DY0 + 26), (DX1 + 34, DY1 + 8), (DX1, DY1)], fill=(88, 86, 82, 255))
fd.rectangle((DX1 + 8, DY0 + 60, DX1 + 28, DY0 + 210), fill=(150, 150, 146, 255))  # frosted pane on the leaf
paste(canvas, fr, (0, 0), shadow=(4, 5), blur=4, dark=.55)
sign = Image.new('RGBA', (150, 26), (226, 222, 212, 255)); sd = ImageDraw.Draw(sign)
sd.text((8, 3), 'CAPOREPARTO', font=font(15), fill=(30, 30, 30))
paste(canvas, sign.rotate(-1.2, expand=True, resample=Image.BICUBIC), (DX0 - 6, DY0 - 46), shadow=(3, 4), blur=3)

# --- the couple behind the pails (safe corner): cutouts with a pivot at the hips --------------------------
lg = grey(SRC + '/loc/8d16982v.jpg'); lm = np.load(C + '/luciana.npy')
Lu = layer(lg * .92 + 10, cut_edge(lm, 7)).crop((372, 36, 672, 468))
rg = grey(SRC + '/loc/8c00283v.jpg'); rm = np.load(C + '/renzo.npy')
rm[492:] = 0
Re = layer(rg * .95, cut_edge(rm, 9)).crop((112, 302, 338, 560))
# Luciana leans in to the apple: torso rotated 6 deg about her waist (joint of the articulated cutout)
paste(canvas, Lu, (822, 262), shadow=(12, 7), blur=10, dark=.35, scale=.70, angle=6, pivot=(150, 400))
# Renzo leans back on his hands and keeps the clock in view: rotated -4 deg about the hips
paste(canvas, Re, (968, 214), shadow=(14, 7), blur=10, dark=.35, scale=1.78, angle=-4, pivot=(110, 250))
# pails re-composited in front (occlusion: the pile is what hides them from the doorway)
fg = np.dstack([np.stack([plu8] * 3, -1), cv2.GaussianBlur(box, (3, 3), 0)])
canvas.alpha_composite(Image.fromarray(fg, 'RGBA'))

# --- paper clock hands at 12:02 (hour ~1 deg, minute 12 deg) -----------------------------------------------
hl = Image.new('RGBA', (W, H), (0, 0, 0, 0)); hd = ImageDraw.Draw(hl)
def hand(ang, length, wid):
    a = math.radians(ang - 90); b = a + math.pi / 2
    tip = (cx + length * math.cos(a), cy + length * math.sin(a))
    p = [(cx + wid * math.cos(b), cy + wid * math.sin(b)), tip, (cx - wid * math.cos(b), cy - wid * math.sin(b)),
         (cx - 6 * math.cos(a), cy - 6 * math.sin(a))]
    hd.polygon(p, fill=(18, 18, 18, 255))
hand(1.0, r * .5, 3.2); hand(12.0, r * .78, 2.4); hd.ellipse((cx - 3, cy - 3, cx + 3, cy + 3), fill=(18, 18, 18, 255))
paste(canvas, hl, (0, 0), shadow=(2, 2), blur=1.5, dark=.4)
img = grain(canvas.convert('RGB'), amt=5)
img.save(OUT + '/kf-2.png'); print('kf-2', img.size)

# Split the Bain visitor cutout into articulated RGBA pieces (#1 Gilliam cutout, #2 pinned joints, #32 FK) and
# cut the Rol close-up forearm+hand (readable sleeve, shirt cuff, gloves). Writes forage/rig.json.
import cv2, numpy as np, json, math
from PIL import Image, ImageDraw, ImageFilter
F = '/home/user/bolas/paeleo/scion/oulipo/films/sources/exercices-de-style/forage/'
WS = '/home/user/bolas/paeleo/scion/oulipo/films/swarm/exercices-de-style/forage/'
cut = np.array(Image.open(F + 'visitor_rgba.png')); H, W = cut.shape[:2]
RGB = cut[..., :3].copy(); A = cut[..., 3].astype(np.float32) / 255
k = W / 555.0
def poly(pts, scale=1.0, blur=1.2):
    m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).polygon([(x * scale, y * scale) for x, y in pts], fill=255)
    return np.array(m.filter(ImageFilter.GaussianBlur(blur)), np.float32) / 255
def cap(c, r):  # round joint cap (overlap disc) at a pivot
    m = np.zeros((H, W), np.float32); cv2.circle(m, (int(c[0]), int(c[1])), int(r), 1.0, -1, cv2.LINE_AA); return m
pieces = {}; inventions = []
def save(name, rgb, alpha, pivot, parent, z, img=None):
    a = (np.clip(alpha, 0, 1) * 255).astype(np.uint8)
    ys, xs = np.where(a > 8); x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    Image.fromarray(np.dstack([rgb[y0:y1, x0:x1], a[y0:y1, x0:x1]])).save(F + f'visitor_{name}_rgba.png')
    pieces[name] = dict(file=f'films/sources/exercices-de-style/forage/visitor_{name}_rgba.png', size=[int(x1 - x0), int(y1 - y0)],
                        origin_in_crop=[int(x0), int(y0)], pivot_local=[int(pivot[0] - x0), int(pivot[1] - y0)],
                        pivot_crop=[int(pivot[0]), int(pivot[1])], parent=parent, z=z)
# joints in crop pixels
NECK = (300, 440); HIP = (430, 1230); SHOULDER = (530, 520); ELBOW = (680, 880)
HIP_F = (420, 1300); HIP_B = (505, 1300); KNEE_F = (412, 1700); KNEE_B = (503, 1700)
UPPER = [(300, 300), (400, 318), (470, 450), (488, 590), (475, 655), (420, 645), (360, 505), (300, 420)]
FORE = [(470, 560), (488, 640), (450, 725), (335, 800), (268, 795), (250, 762), (300, 700), (405, 618)]
up = poly(UPPER, k) * A; fo = poly(FORE, k) * A
armall = np.clip(up + fo, 0, 1)
# torso underlay: the coat beneath the arm is inpainted from the surrounding wool -> FLAGGED INVENTION
hole = ((armall > 0.05) * 255).astype(np.uint8)
hole_in = cv2.dilate(hole, np.ones((9, 9), np.uint8)) & ((A > 0.5) * 255).astype(np.uint8)
src2 = RGB.copy(); coat_med = np.median(RGB[(A > 0.9) & (np.arange(H)[:, None] > 700) & (np.arange(H)[:, None] < 1200)], axis=0)
src2[A < 0.6] = coat_med.astype(np.uint8)
bgr = cv2.cvtColor(src2, cv2.COLOR_RGB2BGR)
under = cv2.cvtColor(cv2.inpaint(bgr, hole_in, 15, cv2.INPAINT_TELEA), cv2.COLOR_BGR2RGB)
inventions.append(dict(piece='torso', region='coat under the left arm (inpainted, cv2.INPAINT_TELEA r=15)', px=int((hole_in > 0).sum())))
headm = poly([(70, 60), (400, 60), (400, 470), (230, 485), (60, 300)]) * A
y = np.arange(H)[:, None] * np.ones((1, W))
torso = A * (y >= 380) * (y < 1260) + A * cap(HIP, 70) * (y >= 1180)
save('head', RGB, headm, NECK, 'torso', 6)
save('torso', under, np.clip(torso, 0, 1), HIP, None, 4)
hem = A * (y >= 1150) * (y < 1600)
save('hem', RGB, hem, (HIP[0], 1160), 'torso', 5)
# upper arm with a round cap at the shoulder; forearm+cuff+pocket hand with cap at the elbow
save('upper_arm', RGB, np.clip(up + cap(SHOULDER, 34) * A, 0, 1), SHOULDER, 'torso', 7)
save('forearm_hand', RGB, np.clip(fo + cap(ELBOW, 30) * A, 0, 1), ELBOW, 'upper_arm', 8)
# legs: split the visible trousers along the seam between the lit front leg and the shaded back leg
legs = A * (y >= 1596)
split_x = lambda yy: 470 - (yy - 1585) * (15 / 520)
xs = np.arange(W)[None, :] * np.ones((H, 1))
front = legs * (xs < split_x(y)); back = legs * (xs >= split_x(y))
# thighs continue up under the coat with cloth extended from the visible trouser top -> FLAGGED INVENTION (hidden by hem)
def extend_up(mask, x0, x1, ytop, yfrom):
    m = mask.copy(); rgb = RGB.copy()
    band = RGB[yfrom:yfrom + 60, x0:x1]; band = np.concatenate([band, band[::-1]], 0)  # mirrored, no hard seam
    for yy in range(ytop, yfrom):
        rgb[yy, x0:x1] = band[(yfrom - yy) % len(band)]; m[yy, x0:x1] = 1.0
    return m, rgb
for name, part, (x0, x1), hipj, kneej, zt, zs in [('front', front, (378, 468), HIP_F, KNEE_F, 3, 3), ('back', back, (472, 560), HIP_B, KNEE_B, 1, 1)]:
    th = part * (y < kneej[1] + 26) + 0
    th_m, th_rgb = extend_up(th, x0, x1, hipj[1] - 30, 1597)
    th_m = np.clip(th_m + cap(kneej, 34) * part, 0, 1)
    inventions.append(dict(piece=f'thigh_{name}', region=f'trouser cloth y {hipj[1]-30}-1600 under the coat, tiled from the visible trouser top', px=int(((th_m > 0) & (y < 1600)).sum())))
    save(f'thigh_{name}', th_rgb, th_m, hipj, 'hem' if False else 'torso', zt)
    sh = part * (y >= kneej[1] - 26)
    save(f'shin_shoe_{name}', RGB, sh, kneej, f'thigh_{name}', zs)
def L(a, b): return round(math.dist(a, b), 1)
bones = dict(neck_to_hip=L(NECK, HIP), shoulder_to_elbow=L(SHOULDER, ELBOW), elbow_to_hand=L(ELBOW, (413, 1123)),
             hip_to_knee_front=L(HIP_F, KNEE_F), knee_to_ankle_front=L(KNEE_F, (395, 2060)),
             hip_to_knee_back=L(HIP_B, KNEE_B), knee_to_ankle_back=L(KNEE_B, (515, 2060)))
# --- Rol close-up forearm: sleeve folds + white shirt cuff + gloved hand (man.jpg, PD) for the key-lowering beat
R = np.array(Image.open(F + 'man_rgba.png')); RH, RW = R.shape[:2]; s = 2.56
m = Image.new('L', (RW, RH), 0)
ImageDraw.Draw(m).polygon([(x * s, y * s) for x, y in [(330, 470), (472, 462), (478, 560), (436, 612), (338, 645), (236, 646), (230, 572), (300, 556)]], fill=255)
mm = np.array(m.filter(ImageFilter.GaussianBlur(1.5)), np.float32) / 255 * (R[..., 3] / 255.0)
a = (mm * 255).astype(np.uint8); ys, xs2 = np.where(a > 8); x0, x1, y0, y1 = xs2.min(), xs2.max() + 1, ys.min(), ys.max() + 1
Image.fromarray(np.dstack([R[y0:y1, x0:x1, :3], a[y0:y1, x0:x1]])).save(F + 'rol_forearm_hand_rgba.png')
closeup = dict(file='films/sources/exercices-de-style/forage/rol_forearm_hand_rgba.png', size=[int(x1 - x0), int(y1 - y0)],
               pivot_local=[int(1160 - x0), int(1235 - y0)], grip_point_local=[int(700 - x0), int(1560 - y0)],
               note='Close-up only (S5b slide-out, S5c lowering). It is the Agence Rol man\'s real right forearm: coat sleeve with its fold highlights, the white shirt cuff and the hand holding gloves. A different PD print from the full-figure visitor; both wear dark wool overcoats; declared continuity cut.')
json.dump(dict(pieces=pieces, bones=bones, inventions=inventions, closeup=closeup), open(WS + 'build/_pieces.json', 'w'), indent=1)
print(json.dumps(bones), len(pieces))

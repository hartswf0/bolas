# Primary visitor: LoC Bain News Service glass negative LC-B2-623-4 (1908-09, "No known restrictions"), the unnamed
# man in overcoat and bowler at right. #29 GrabCut (box + scribble seeds) -> #31 trimap matte + decontamination.
import sys; sys.path.insert(0, '/home/user/bolas/paeleo/scion/oulipo/films/swarm/exercices-de-style/forage/build')
import cv2, numpy as np
from PIL import Image
from matte import grabcut, clean, matte, failmask
F = '/home/user/bolas/paeleo/scion/oulipo/films/sources/exercices-de-style/forage/'
g = np.array(Image.open(F + 'bain_03026_visitor_crop.png').convert('L')); H, W = g.shape
rgb = np.dstack([g] * 3)
k = W / 555.0  # seeds drawn on the 555-px-wide inspection thumbnail
P = lambda pts: (np.array(pts, np.float32) * k).astype(np.int32)
M = np.full((H, W), cv2.GC_PR_BGD, np.uint8)
body = P([(52, 1105), (62, 560), (130, 325), (100, 300), (55, 175), (70, 150), (120, 95), (130, 45), (200, 40), (250, 100), (268, 120), (250, 240), (300, 255), (390, 330), (482, 590), (505, 1045), (450, 1095), (455, 1420), (450, 1470), (180, 1470), (190, 1390), (230, 1310), (225, 1110)])
cv2.fillPoly(M, [body], cv2.GC_PR_FGD)
# sure-foreground scribbles: hat crown, face, coat front, sleeve, both trouser legs
for pts in [[(110, 70), (220, 60), (230, 150), (110, 170)], [(140, 200), (220, 200), (215, 280), (150, 290)],
            [(110, 600), (230, 400), (330, 400), (440, 640), (440, 1000), (130, 1060)],
            [(270, 1130), (360, 1130), (350, 1340), (280, 1340)], [(375, 1140), (420, 1140), (430, 1380), (395, 1385)],
            [(230, 1400), (370, 1395), (370, 1440), (220, 1445)]]:
    cv2.fillPoly(M, [P(pts)], cv2.GC_FGD)
# sure-background scribbles: white column left, stairs + rails right, lawn either side of the legs, sky above brim
for pts in [[(0, 0), (40, 0), (40, 1100), (0, 1100)], [(300, 0), (555, 0), (555, 230), (300, 230)],
            [(520, 240), (555, 240), (555, 1500), (520, 1500)], [(0, 1150), (190, 1150), (170, 1500), (0, 1500)],
            [(480, 1110), (555, 1110), (555, 1500), (470, 1500)], [(275, 120), (330, 120), (330, 230), (290, 230)],
            [(0, 0), (50, 0), (40, 150), (0, 300)],
            [(466, 700), (555, 690), (555, 1045), (503, 1045)], [(445, 1100), (520, 1100), (520, 1350), (448, 1350)]]:
    cv2.fillPoly(M, [P(pts)], cv2.GC_BGD)
outside = np.zeros((H, W), np.uint8); cv2.fillPoly(outside, [body], 255)
outside = cv2.dilate(outside, np.ones((41, 41), np.uint8))
M[(outside == 0)] = cv2.GC_BGD
hard = grabcut(rgb, M, 10, 1.0)
hard = clean(hard, open_k=5, close_k=7)
# drawn scissor paths where the soft-focus negative gives the graph cut nothing to separate (grey felt on dark window,
# lit cheek on the white column, grey trousers on grey lawn). Crop pixel coordinates, read off a 50-px grid.
HEAD = np.array([(78, 238), (92, 225), (118, 215), (115, 170), (130, 120), (170, 85), (220, 72), (280, 78), (325, 105), (345, 145), (385, 155), (390, 175), (362, 205), (345, 240), (342, 300), (352, 345), (300, 380), (270, 440), (240, 452), (215, 420), (200, 385), (170, 350), (155, 310), (150, 292), (110, 272), (82, 258)])
LEGS = np.array([(372, 1585), (566, 1585), (520, 1800), (500, 2030), (522, 2078), (470, 2106), (290, 2102), (274, 2072), (330, 2045), (350, 1960), (362, 1720)])
hp = np.zeros((H, W), np.uint8); cv2.fillPoly(hp, [HEAD], 255)
lp = np.zeros((H, W), np.uint8); cv2.fillPoly(lp, [LEGS], 255)
hard[:330] = 0; hard[1590:] = 0
hard = cv2.bitwise_or(hard, hp); hard = cv2.bitwise_or(hard, lp)
hard = clean(hard, open_k=3, close_k=5)
alpha, dec, unk = matte(rgb, hard, band=3)
Image.fromarray(np.dstack([dec, (alpha * 255).astype(np.uint8)])).save(F + 'visitor_rgba.png')
Image.fromarray(hard).save(F + 'visitor_mask.png')
Image.fromarray(failmask(alpha, unk, hard)).save(F + 'visitor_failmask.png')
seed = np.dstack([g] * 3).copy(); seed[M == cv2.GC_FGD] = (seed[M == cv2.GC_FGD] * 0.4 + np.array([0, 200, 0]) * 0.6).astype(np.uint8)
seed[M == cv2.GC_BGD] = (seed[M == cv2.GC_BGD] * 0.5 + np.array([200, 0, 0]) * 0.5).astype(np.uint8)
Image.fromarray(seed).save(F + 'visitor_seeds.jpg')
print('ok', hard.mean() / 255)

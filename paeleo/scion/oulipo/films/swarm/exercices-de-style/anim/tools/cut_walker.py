"""#29 GrabCut + #31 matte edge pass on Rol 57642 (1920) 'Homme marchant dans la rue', left man.
Coordinates authored on the 1280-px proof (S0=1280/width); scaled for any resolution."""
import sys, json, numpy as np, cv2
from PIL import Image, ImageFilter
src, outdir = sys.argv[1], sys.argv[2]
im = cv2.imread(src, cv2.IMREAD_GRAYSCALE)
h, w = im.shape; s = w / 1280.0
S = lambda v: int(round(v * s))
rgb = cv2.cvtColor(im, cv2.COLOR_GRAY2BGR)
mask = np.full((h, w), cv2.GC_BGD, np.uint8)
x0, y0, x1, y1 = S(268), S(398), S(712), S(1478)
mask[y0:y1, x0:x1] = cv2.GC_PR_BGD
# probable foreground: a figure-shaped seed
fg = np.zeros((h, w), np.uint8)
cv2.ellipse(fg, (S(498), S(470)), (S(88), S(55)), 0, 0, 360, 1, -1)      # hat
cv2.ellipse(fg, (S(505), S(545)), (S(45), S(60)), 0, 0, 360, 1, -1)      # face/beard
pts = np.array([[350, 600], [650, 600], [700, 1000], [655, 1240], [330, 1250], [290, 980]]) * s
cv2.fillPoly(fg, [pts.astype(np.int32)], 1)
mask[fg == 1] = cv2.GC_PR_FGD
# sure foreground: dark coat interior, legs, shoes
sure = np.zeros((h, w), np.uint8)
cv2.fillPoly(sure, [(np.array([[380, 640], [600, 640], [640, 1150], [360, 1180]]) * s).astype(np.int32)], 1)
for poly in ([[455, 1200], [505, 1200], [515, 1330], [480, 1330]], [[545, 1200], [595, 1200], [585, 1420], [555, 1420]],
             [[540, 1405], [595, 1405], [595, 1450], [545, 1450]], [[478, 1320], [520, 1320], [522, 1360], [488, 1360]],
             [[465, 425], [530, 425], [530, 495], [465, 495]], [[640, 820], [652, 820], [670, 1290], [660, 1290]]):
    cv2.fillPoly(sure, [(np.array(poly) * s).astype(np.int32)], 1)
mask[sure == 1] = cv2.GC_FGD
# sure background scribbles: the pavement between the legs, the woman behind his left shoulder, the street
for poly in ([[520, 1260], [540, 1260], [545, 1395], [528, 1395]], [[712, 640], [800, 640], [800, 820], [712, 820]],
             [[270, 1300], [440, 1300], [440, 1470], [270, 1470]], [[610, 1300], [640, 1300], [640, 1470], [610, 1470]],
             [[270, 400], [400, 400], [400, 560], [270, 560]], [[610, 400], [712, 400], [712, 560], [610, 560]]):
    cv2.fillPoly(mask, [(np.array(poly) * s).astype(np.int32)], cv2.GC_BGD)
bgd = np.zeros((1, 65), np.float64); fgd = np.zeros((1, 65), np.float64)
cv2.grabCut(rgb, mask, None, bgd, fgd, 6, cv2.GC_INIT_WITH_MASK)
m = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
# hand-traced head trimap (hat, face, beard against a light street: GrabCut cannot separate these tones)
HEAD = [(470,410),(520,404),(555,414),(565,455),(590,468),(589,490),(560,501),(556,530),(552,556),(549,582),(541,600),(545,616),
        (470,614),(467,582),(459,556),(446,532),(440,502),(420,500),(405,491),(407,470),(430,458),(465,454),(465,420)]
hm = np.zeros((h, w), np.uint8); cv2.fillPoly(hm, [(np.array(HEAD) * s).astype(np.int32)], 255)
m[:S(572)] = 0; m = np.maximum(m, hm)
# the pavement shows through between legs and beside the cane: light pixels there are street, not cloth
Lr = im.astype(np.float32) / 255.0
yy, xx = np.mgrid[0:h, 0:w]
street = (Lr > 0.60) & (((yy > S(1140)) ) | ((xx > S(640)) & (yy > S(780))))
m[street] = 0
m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
# keep the largest component (no background islands)
n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
big = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]); m = np.where(lab == big, 255, 0).astype(np.uint8)
# fill interior holes except the true gap between the legs
inv = 255 - m; n2, lab2, st2, _ = cv2.connectedComponentsWithStats(inv, 4)
for i in range(1, n2):
    if st2[i, cv2.CC_STAT_AREA] < (60 * s) ** 2 * 0.3 and st2[i, cv2.CC_STAT_LEFT] > 0:
        m[lab2 == i] = 255
# #31 edge pass: trimap band, guided feathering from the print's own luminance
k = max(3, S(5)) | 1
er = cv2.erode(m, np.ones((k, k), np.uint8)); di = cv2.dilate(m, np.ones((k, k), np.uint8))
band = (di > 0) & (er == 0)
L = im.astype(np.float32) / 255.0
# local fg/bg luminance estimates
fgL = cv2.blur(np.where(er > 0, L, 0), (S(25) | 1, S(25) | 1)) / (cv2.blur((er > 0).astype(np.float32), (S(25) | 1, S(25) | 1)) + 1e-4)
bgm = (di == 0).astype(np.float32)
bgL = cv2.blur(L * bgm, (S(25) | 1, S(25) | 1)) / (cv2.blur(bgm, (S(25) | 1, S(25) | 1)) + 1e-4)
a = np.clip((L - bgL) / (fgL - bgL + np.where(fgL - bgL >= 0, 1e-3, -1e-3)), 0, 1)
alpha = (m > 0).astype(np.float32)
alpha[band] = np.clip(0.5 * a[band] + 0.5 * cv2.GaussianBlur(alpha, (k, k), 0)[band], 0, 1)
alpha = cv2.GaussianBlur(alpha, (3, 3), 0.7)
# colour decontamination: pull band pixels toward the fg estimate
Ld = np.where(band, np.clip(fgL * 0.6 + L * 0.4, 0, 1), L)
out = np.dstack([Ld * 255] * 3 + [alpha * 255]).astype(np.uint8)
Image.fromarray(out, 'RGBA').save(f'{outdir}/walker_rgba_full.png')
fail = np.zeros((h, w, 3), np.uint8); fail[band] = (255, 0, 0); fail[(m > 0) & ~band] = (90, 90, 90)
Image.fromarray(fail).save(f'{outdir}/walker_failmask.png')
json.dump(dict(scale=s, size=[w, h], bbox=[x0, y0, x1, y1]), open(f'{outdir}/walker_cut.json', 'w'))
print('ok', w, h, alpha.sum() / 255)

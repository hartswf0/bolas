# Fallback visitor: Agence Rol 1917 portrait (man.jpg, PD). GrabCut (box + scribbles) -> clean -> trimap matte -> decontam.
import sys; sys.path.insert(0, '/home/user/bolas/paeleo/scion/oulipo/films/swarm/exercices-de-style/forage/build')
import cv2, numpy as np
from PIL import Image
from matte import grabcut, clean, matte, failmask
S = '/home/user/bolas/paeleo/scion/oulipo/films/sources/exercices-de-style/'
O = S + 'forage/'
g = np.array(Image.open(S + 'man.jpg').convert('L')); rgb = np.dstack([g] * 3); H, W = g.shape
M = np.full((H, W), cv2.GC_BGD, np.uint8)
cv2.rectangle(M, (150, 150), (1230, 1737), cv2.GC_PR_BGD, -1)
cv2.ellipse(M, (540, 470), (260, 330), 0, 0, 360, cv2.GC_PR_FGD, -1)
cv2.fillPoly(M, [np.array([(330, 700), (760, 640), (1060, 780), (1210, 1150), (1230, 1737), (160, 1737), (170, 1100)])], cv2.GC_PR_FGD)
for r in [(380, 210, 690, 380), (430, 380, 640, 700), (380, 850, 1050, 1650), (250, 1100, 380, 1600), (700, 1500, 850, 1620)]:
    cv2.rectangle(M, r[:2], r[2:], cv2.GC_FGD, -1)
# background scribbles: flowers/hedge debris left of the coat and right of the elbow (the known sleeve debris)
for r in [(800, 40, 1280, 560), (0, 0, 300, 700), (0, 0, 1280, 140), (820, 560, 1280, 640), (1230, 0, 1280, 1737),
          (150, 760, 230, 1000), (1215, 1150, 1280, 1737)]:
    cv2.rectangle(M, r[:2], r[2:], cv2.GC_BGD, -1)

# scissor clip (the cutout's paper edge, drawn by hand along the coat): removes hedge flowers on the left sleeve
clip = np.zeros((H, W), np.uint8)
poly = np.array([(380, 420), (690, 380), (700, 420), (690, 620), (980, 760), (1090, 900), (1150, 1100), (1215, 1300), (1235, 1362), (950, 1600), (935, 1702), (560, 1700), (205, 1700), (192, 1500), (206, 1250), (258, 1000), (316, 848), (420, 700), (430, 560), (380, 430)])
cv2.fillPoly(clip, [poly], 255)
# hat drawn as the felt really sits: dome crown + curled brim (scissor path from the full-res print)
hat = np.zeros_like(clip)
cv2.ellipse(hat, (518, 300), (150, 135), 0, 180, 360, 255, -1)
cv2.rectangle(hat, (368, 300), (668, 400), 255, -1)
cv2.fillPoly(hat, [np.array([(326, 405), (345, 392), (420, 395), (560, 380), (660, 338), (705, 322), (726, 320), (734, 330), (722, 352), (690, 384), (640, 405), (520, 418), (420, 432), (340, 432)])], 255)
clip = cv2.bitwise_or(clip, hat)
cv2.fillPoly(clip, [np.array([(670, 160), (780, 160), (780, 318), (712, 318), (672, 342)])], 0)  # dark horse head behind the right brim
M[(hat > 0) & (cv2.erode(hat, np.ones((15, 15), np.uint8)) > 0)] = cv2.GC_FGD
M[clip == 0] = cv2.GC_BGD
hard = grabcut(rgb, M, 8, 0.5)
hard = clean(cv2.bitwise_and(hard, clip), open_k=7, close_k=9)
alpha, dec, unk = matte(rgb, hard, band=4)
# remaining debris check: bright (flower) pixels in the outer 14 px of the matte are knocked out
rim = (cv2.erode(hard, np.ones((29, 29), np.uint8)) == 0) & (hard > 0)
deb = rim & (g > 150); deb[:760] = False; deb[1380:, 560:900] = False  # keep face, hand+gloves
alpha[deb] = 0
# hat: crisp scissor edge (the grey felt meets a grey background; the matte has nothing to separate, so the cut is drawn)
hz = np.zeros((H, W), bool); hz[150:440, 300:780] = True
hs = cv2.GaussianBlur((hat > 0).astype(np.float32), (0, 0), 1.0)
face = (hard > 0) & ~(hat > 0)
facex = cv2.dilate(face.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0
alpha[hz] = np.maximum(hs, np.where(facex & (hard > 0), 1.0, np.where(face, alpha, 0)))[hz]
dec[hz & (hat > 0)] = rgb[hz & (hat > 0)]
out = np.dstack([dec, (alpha * 255).astype(np.uint8)])
Image.fromarray(out).save(O + 'man_rgba.png')
Image.fromarray(hard).save(O + 'man_mask.png')
fm = failmask(alpha, unk, hard); fm[deb] = (255, 0, 255)
Image.fromarray(fm).save(O + 'man_failmask.png')
print('debris px removed', int(deb.sum()), 'alpha>0', int((alpha > 0).sum()))

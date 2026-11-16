"""SCION 29 (GrabCut) cutout of the conductor, LoC 2017844115, into rig pieces.

python3 -I cut.py <oulipo root>
Pieces (piece coords = crop box (368,285)-(680,1000) of the 791x1024 LoC jpeg):
  body    coat + head + cap + newspaper, with the forearm hole inpainted
  forearm forearm + hand (watch), hinged at the elbow
  shinN   near trouser leg + shoe, hinged at the hem
  shinF   far trouser leg, hinged at the hem
Writes RGBA-ish npz + PNG masks + failure masks to sources/.../test-shot/cut/ and rig.json.
"""
import sys, os, json
import numpy as np, cv2

ROOT = sys.argv[1] if len(sys.argv) > 1 else '/home/user/bolas/paeleo/scion/oulipo'
SRC = os.path.join(ROOT, 'films/sources/la-machine-a-tuer-le-temps/loc_2017844115.jpg')
OUT = os.path.join(ROOT, 'films/sources/la-belle-hortense/test-shot/cut')
BUILD = os.path.dirname(os.path.abspath(__file__))
os.makedirs(OUT, exist_ok=True)
X0, Y0, X1, Y1 = 368, 285, 680, 1000

im = cv2.imread(SRC)                       # decoded by OpenCV only
crop = im[Y0:Y1, X0:X1].copy()
g = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.
h, w = g.shape

# --- the scissor line: hand-placed outer envelope (nothing outside can be figure)
scissor = np.array([(112, 22), (150, 12), (222, 40), (222, 70), (205, 120), (252, 150), (268, 250),
                    (262, 320), (252, 450), (246, 620), (240, 640), (200, 642), (200, 712), (72, 712),
                    (70, 650), (22, 615), (10, 560), (40, 300), (72, 160), (112, 140), (100, 95), (106, 50)], np.int32)
env = np.zeros((h, w), np.uint8); cv2.fillPoly(env, [scissor], 1)

# --- seeds: density (the coat prints dark on the pale wall) + scribbles for pale parts
gs = cv2.GaussianBlur(g, (5, 5), 0)
dense = (gs < 0.30).astype(np.uint8) * env
gc = np.full((h, w), cv2.GC_PR_BGD, np.uint8)
gc[env == 0] = cv2.GC_BGD
gc[(dense == 1)] = cv2.GC_PR_FGD
core = cv2.erode(dense, np.ones((9, 9), np.uint8))
gc[core == 1] = cv2.GC_FGD
scrib = np.zeros((h, w), np.uint8)              # FG scribbles: face, collar, hand, newspaper, cap
for c, ax in (((148, 102), (34, 46)), ((140, 150), (30, 20)), ((150, 238), (34, 12)), ((225, 345), (18, 30)), ((160, 54), (34, 11))):
    cv2.ellipse(scrib, c, ax, 0, 0, 360, 1, -1)
gc[(scrib == 1) & (env == 1)] = cv2.GC_FGD
wallbg = np.zeros((h, w), np.uint8)             # BG scribbles: the wall left of the face, wall right of the head
cv2.rectangle(wallbg, (60, 30), (95, 120), 1, -1); cv2.rectangle(wallbg, (232, 80), (300, 140), 1, -1); cv2.rectangle(wallbg, (196, 88), (232, 138), 1, -1); cv2.rectangle(wallbg, (176, 6), (230, 30), 1, -1)
gc[wallbg == 1] = cv2.GC_BGD
bgd = np.zeros((1, 65), np.float64); fgd = np.zeros((1, 65), np.float64)
cv2.grabCut(crop, gc, None, bgd, fgd, 6, cv2.GC_INIT_WITH_MASK)
m = np.isin(gc, (cv2.GC_FGD, cv2.GC_PR_FGD)).astype(np.uint8) * env

# --- cleanup: keep the main component (no background islands), fill holes, 1-2 px alpha
n, lab, st, _ = cv2.connectedComponentsWithStats(m)
k = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]); islands = int(n - 2)
m = (lab == k).astype(np.uint8)
ff = m.copy(); fm = np.zeros((h + 2, w + 2), np.uint8); cv2.floodFill(ff, fm, (0, 0), 2)
holes = (ff == 0).astype(np.uint8); m = np.where(ff == 2, 0, 1).astype(np.uint8)
m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
alpha = cv2.GaussianBlur(m.astype(np.float32), (3, 3), 0)

# failure masks: where grabCut disagreed with the density prior, and what was removed
fail = np.zeros((h, w, 3), np.uint8)
fail[(dense == 1) & (m == 0)] = (0, 0, 255)     # dark but cut away (shadow on wall, etc.)
fail[(dense == 0) & (m == 1)] = (0, 255, 0)     # pale but kept (face, collar, paper)
fail[holes == 1] = (255, 0, 0)
cv2.imwrite(os.path.join(OUT, 'failure_mask.png'), cv2.addWeighted(crop, 0.5, fail, 0.8, 0))
cv2.imwrite(os.path.join(OUT, 'grabcut_mask.png'), (alpha * 255).astype(np.uint8))

# --- split into rig pieces
HEM = 636
fore = np.zeros((h, w), np.uint8)
cv2.fillPoly(fore, [np.array([(104, 214), (196, 212), (258, 262), (262, 312), (226, 306), (178, 290), (104, 258)], np.int32)], 1)
fore_a = alpha * fore
body_a = alpha.copy(); body_a[HEM + 6:] = 0
# fill the hole the forearm leaves in the body (the coat behind it) by inpainting from the coat
hole = (fore > 0).astype(np.uint8)
body_g = cv2.inpaint((g * 255).astype(np.uint8), cv2.dilate(hole, np.ones((5, 5), np.uint8)), 7, cv2.INPAINT_TELEA).astype(np.float32) / 255.
legs = alpha.copy(); legs[:HEM - 6] = 0
shinN = legs.copy(); shinN[:, :146] = 0; shinN[:, 204:] = 0
shinF = legs.copy(); shinF[:, :74] = 0; shinF[:, 146:] = 0
# coat stencil (the dye mask, hand-polygoned over the cut): body minus skin/collar/paper/cap
pale = cv2.GaussianBlur(((body_g > 0.50) * 1.0).astype(np.float32), (5, 5), 0)
coat = np.clip(body_a - pale, 0, 1)
coat[:84] = 0                                   # cap and above stay black
head = np.zeros((h, w), np.float32); cv2.ellipse(head, (152, 102), (56, 72), 0, 0, 360, 1, -1)
tie = np.zeros((h, w), np.float32); cv2.fillPoly(tie, [np.array([(126, 150), (146, 150), (150, 250), (128, 250)], np.int32)], 1)
coat = coat * (1 - head) * (1 - tie)
coat = cv2.GaussianBlur(coat, (3, 3), 0)
fore_coat = np.clip(fore_a - cv2.GaussianBlur(((g > 0.42) * 1.0).astype(np.float32), (5, 5), 0), 0, 1)
fore_coat[:, :172] *= 0                         # the hand itself stays skin

np.savez_compressed(os.path.join(OUT, 'pieces.npz'), g=g, body_g=body_g, body_a=body_a, fore_a=fore_a,
                    shinN=shinN, shinF=shinF, coat=coat, fore_coat=fore_coat)
for name, a in (('body', body_a), ('forearm', fore_a), ('shinN', shinN), ('shinF', shinF), ('coat_dye', coat)):
    rgba = np.dstack([body_g * 255 if name == 'body' else g * 255] * 3 + [a * 255]).astype(np.uint8)
    cv2.imwrite(os.path.join(OUT, f'{name}.png'), rgba)

rig = {
    'source': {'id': 'LoC 2017844115', 'file': 'films/sources/la-machine-a-tuer-le-temps/loc_2017844115.jpg',
               'crop_box': [X0, Y0, X1, Y1], 'licence': 'Public domain (US government work, FSA/OWI; LoC: no known restrictions)'},
    'method': 'cv2.grabCut, GC_INIT_WITH_MASK, 6 iters; seeds: density<0.30 (PR_FGD), eroded core (FGD), '
              'scribble ellipses for face/collar/hand/paper/cap (FGD), wall rectangles (BGD), outside scissor polygon (BGD)',
    'islands_removed': islands,
    'pieces': {
        'body': {'parent': None, 'pivot_hip': [172, HEM], 'mask': 'cut/body.png', 'note': 'forearm hole inpainted (TELEA r=7)'},
        'forearm': {'parent': 'body', 'pivot_elbow': [246, 292], 'limits_deg': [-14, 10], 'mask': 'cut/forearm.png'},
        'shinN': {'parent': 'body', 'pivot_hem': [172, HEM], 'limits_deg': [-38, 38], 'stretch_y': 1.5, 'mask': 'cut/shinN.png'},
        'shinF': {'parent': 'body', 'pivot_hem': [118, HEM], 'limits_deg': [-38, 38], 'stretch_y': 1.5, 'shade': 0.55, 'mask': 'cut/shinF.png'},
    },
    'dye': {'coat': '#e2011b stencil (mask cut/coat_dye.png) multiplied over the monochrome print, re-printed light'},
}
json.dump(rig, open(os.path.join(BUILD, 'rig.json'), 'w'), indent=1)
print('islands removed', islands, 'fg px', int(m.sum()))

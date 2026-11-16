"""Cut the conductor (LoC 2017844115, Jack Delano 1943, FSA/OWI, PD) into rig pieces.

python3 -I cut_conductor.py   (paths are absolute below; source decoded by OpenCV only)
Crop box (368,285)-(680,1000) of the 791x1024 LoC jpeg; all piece coords are crop coords.
Pieces: coat_panel (root), head_cap, arm (sleeve+forearm+hand, shoulder hinge), newspaper,
        thighN/thighF (trouser between hem and knee), shinN/shinF (knee to shoe).
Coat folds are preserved: the coat dye mask is a separate soft mask and the print tone is kept
in the piece (the dye multiplies over it), so the folds show through the red.
"""
import os, sys, json
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gcut import grabcut_piece, rgba, trim

ROOT = '/home/user/bolas/paeleo/scion/oulipo/films'
SRC = ROOT + '/sources/la-belle-hortense/forage/raw/loc_2017844115.jpg'
OUT = ROOT + '/sources/la-belle-hortense/forage/cut/conductor'
os.makedirs(OUT, exist_ok=True)
X0, Y0, X1, Y1 = 368, 285, 680, 1000

im = cv2.imread(SRC)
crop = im[Y0:Y1, X0:X1].copy()
g = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.
h, w = g.shape

# scissor envelope (hand-placed; includes a hand-cut line along the right arm where the wall/counter
# fringe at x 250-300, y 150-330 leaked in the earlier test cut)
scissor = [(112, 22), (150, 12), (222, 40), (222, 70), (205, 120), (240, 150), (262, 175), (270, 250),
           (264, 300), (256, 330), (252, 450), (246, 620), (240, 640), (200, 642), (200, 712), (72, 712),
           (70, 650), (22, 615), (8, 560), (40, 300), (72, 160), (112, 140), (100, 95), (106, 50)]
fg = [('ellipse', (148, 102), (34, 46)), ('ellipse', (140, 150), (30, 20)), ('ellipse', (150, 238), (34, 12)),
      ('ellipse', (228, 348), (18, 28)), ('ellipse', (160, 54), (34, 11)), ('ellipse', (150, 420), (60, 160)),
      ('ellipse', (110, 680), (25, 25)), ('poly', [(22, 570), (44, 470), (66, 470), (66, 590), (34, 600)]), ('ellipse', (172, 680), (14, 25))]
bg = [('rect', (60, 30, 95, 120)), ('rect', (236, 80, 300, 140)), ('rect', (196, 88, 232, 138)),
      ('rect', (176, 6, 230, 30)), ('rect', (275, 170, 311, 330)), ('rect', (0, 650, 60, 714)),
      ('rect', (205, 650, 311, 714))]
alpha, rep, over = grabcut_piece(crop, scissor, fg, bg, dense_thr=0.30)
cv2.imwrite(OUT + '/failure_mask.png', over)
cv2.imwrite(OUT + '/grabcut_mask.png', (alpha * 255).astype(np.uint8))

HEM = 636
KNEE = 664          # knee hinge placed below the hem: the visible trouser is split thigh/shin
SHOULDER = (238, 168)
ELBOW = (256, 294)
NECK = (150, 150)

arm_poly = np.array([(222, 150), (262, 168), (274, 255), (266, 312), (226, 308), (178, 292), (104, 260),
                     (100, 214), (196, 210), (226, 236), (226, 200)], np.int32)
head_poly = np.array([(100, 10), (226, 10), (226, 72), (200, 120), (186, 150), (150, 178), (120, 160),
                      (100, 110)], np.int32)
paper_poly = np.array([(203, 318), (256, 316), (258, 382), (204, 384)], np.int32)


def polymask(p):
    m = np.zeros((h, w), np.float32); cv2.fillPoly(m, [p], 1.0)
    return cv2.GaussianBlur(m, (3, 3), 0)


arm_m = polymask(arm_poly) * alpha
head_m = polymask(head_poly) * alpha
paper_m = polymask(paper_poly) * alpha
# coat panel: everything above the hem minus head, arm, paper; the holes the arm and paper leave are
# re-printed from neighbouring coat by inpainting (the coat behind them was never photographed)
coat_a = alpha.copy(); coat_a[HEM + 6:] = 0
coat_a = np.clip(coat_a - head_m * (1 - 0) , 0, 1)
coat_a[:130] = np.where(head_m[:130] > 0.5, 0, coat_a[:130])
hole = ((arm_m + paper_m) > 0.05).astype(np.uint8)
coat_g = cv2.inpaint((g * 255).astype(np.uint8), cv2.dilate(hole, np.ones((5, 5), np.uint8)), 9,
                     cv2.INPAINT_TELEA).astype(np.float32) / 255.
coat_a = np.maximum(coat_a, cv2.dilate(hole, np.ones((3, 3), np.uint8)).astype(np.float32) * (alpha > 0.5))
coat_a = np.clip(coat_a - head_m, 0, 1)

# legs: near leg x 146..204, far leg x 74..146 below the hem; split at the knee
legs = alpha.copy(); legs[:HEM - 4] = 0
legN = legs.copy(); legN[:, :146] = 0; legN[:, 206:] = 0
legF = legs.copy(); legF[:, :70] = 0; legF[:, 146:] = 0
thighN = legN.copy(); thighN[KNEE + 3:] = 0
shinN = legN.copy(); shinN[:KNEE - 3] = 0
thighF = legF.copy(); thighF[KNEE + 3:] = 0
shinF = legF.copy(); shinF[:KNEE - 3] = 0

# coat dye mask (stencil): coat cloth only, not the pale shirt/collar, the buttons' highlights stay printed;
# soft so the fold tones survive under the multiply
pale = cv2.GaussianBlur(((coat_g > 0.50) * 1.0).astype(np.float32), (5, 5), 0)
tie = np.zeros((h, w), np.float32)
cv2.fillPoly(tie, [np.array([(118, 140), (176, 136), (156, 250), (126, 250)], np.int32)], 1)
coat_dye = np.clip(coat_a - pale, 0, 1) * (1 - cv2.GaussianBlur(tie, (5, 5), 0))
arm_dye = np.clip(arm_m - cv2.GaussianBlur(((g > 0.42) * 1.0).astype(np.float32), (5, 5), 0), 0, 1)
arm_dye[:, :180] = 0      # hand stays skin

# run variant: the coat skirt split at the front opening (x~108) below the waist (y 440) into two flaps that
# follow the thighs, so the stride is visible in the coat itself (fix for the test-shot 'it walks, not runs')
WAIST = 440
upper = coat_a.copy(); upper[WAIST + 8:] = 0
skirt = coat_a.copy(); skirt[:WAIST - 8] = 0
xx = np.arange(w)[None, :].repeat(h, 0).astype(np.float32)
split = np.clip((xx - 108) / 3 + 0.5, 0, 1)
skirtN = skirt * split; skirtF = skirt * (1 - split)
for nm, a in (('coat_upper_dye', coat_dye * (np.arange(h)[:, None] < WAIST + 8)), ('skirtN_dye', coat_dye * skirtN),
              ('skirtF_dye', coat_dye * skirtF)):
    cv2.imwrite(f'{OUT}/{nm}.png', (np.clip(a, 0, 1) * 255).astype(np.uint8))

pieces = {
    'coat_upper': (coat_g, upper, None, {'pivot_waist': [140, WAIST], 'pivot_neck': list(NECK),
                                          'pivot_shoulder': list(SHOULDER), 'pivot_paper': [230, 318],
                                          'pivot_hipN': [150, WAIST], 'pivot_hipF': [96, WAIST]}),
    'skirtN': (coat_g, skirtN, None, {'pivot_hipN': [150, WAIST], 'pivot_hemN': [176, HEM]}),
    'skirtF': (coat_g, skirtF, None, {'pivot_hipF': [96, WAIST], 'pivot_hemF': [110, HEM]}),
    'coat_panel': (coat_g, coat_a, None, {'pivot_hip': [172, HEM], 'pivot_neck': list(NECK),
                                          'pivot_shoulder': list(SHOULDER), 'pivot_hemN': [176, HEM],
                                          'pivot_hemF': [110, HEM], 'pivot_paper': [230, 318]}),
    'head_cap': (g, head_m, None, {'pivot_neck': list(NECK)}),
    'arm': (g, arm_m, None, {'pivot_shoulder': list(SHOULDER), 'pivot_elbow': list(ELBOW)}),
    'newspaper': (g, paper_m, None, {'pivot_top': [230, 318]}),
    'thighN': (g, thighN, None, {'pivot_hip': [176, HEM], 'pivot_knee': [176, KNEE]}),
    'shinN': (g, shinN, None, {'pivot_knee': [176, KNEE], 'pivot_toe': [182, 708]}),
    'thighF': (g, thighF, None, {'pivot_hip': [110, HEM], 'pivot_knee': [108, KNEE]}),
    'shinF': (g, shinF, None, {'pivot_knee': [108, KNEE], 'pivot_toe': [104, 708]}),
}
manifest = {}
for name, (img, a, _, piv) in pieces.items():
    arr = rgba(img, a)
    t, (ox, oy) = trim(arr)
    cv2.imwrite(f'{OUT}/{name}.png', cv2.cvtColor(t, cv2.COLOR_RGBA2BGRA))
    manifest[name] = {'png': f'cut/conductor/{name}.png', 'offset_in_crop': [ox, oy], 'size': [t.shape[1], t.shape[0]],
                      'pivots_crop': piv, 'pivots_piece': {k: [v[0] - ox, v[1] - oy] for k, v in piv.items()}}
for name, a in (('coat_dye', coat_dye), ('arm_dye', arm_dye)):
    cv2.imwrite(f'{OUT}/{name}.png', (np.clip(a, 0, 1) * 255).astype(np.uint8))
# full-crop masks too (same frame as the crop) for exact re-registration
np.savez_compressed(OUT + '/pieces_fullcrop.npz', g=g, coat_g=coat_g, alpha=alpha, coat_a=coat_a, head=head_m,
                    arm=arm_m, paper=paper_m, thighN=thighN, shinN=shinN, thighF=thighF, shinF=shinF,
                    coat_dye=coat_dye, arm_dye=arm_dye)
# QA sheet: pieces exploded on mid grey + checker
sheet = np.full((h, w * 2 + 20, 3), 128, np.uint8)
sheet[:, :w] = over
cols = {'coat_panel': (40, 40, 200), 'head_cap': (200, 180, 40), 'arm': (40, 200, 200), 'newspaper': (200, 40, 200),
        'thighN': (40, 200, 40), 'shinN': (0, 120, 0), 'thighF': (200, 120, 40), 'shinF': (120, 60, 0)}
base = sheet[:, w + 20:]
for name, (img, a, _, piv) in pieces.items():
    if name == 'coat_panel':
        continue      # QA shows the run variant (upper + flaps); coat_panel = their union
    c = np.array({'coat_upper': (40, 40, 200), 'skirtN': (60, 120, 240), 'skirtF': (20, 20, 120)}.get(name, cols.get(name, (128, 128, 128))), np.float32)
    base[:] = (base * (1 - a[..., None] * 0.6) + (c * 0.6 * a[..., None]) + (g[..., None] * 255 * 0.4 * a[..., None])).astype(np.uint8)
    for v in piv.values():
        cv2.circle(base, (v[0], v[1]), 4, (255, 255, 255), -1); cv2.circle(base, (v[0], v[1]), 4, (0, 0, 0), 1)
cv2.imwrite(OUT + '/qa_pieces.png', sheet)
json.dump({'source': 'LoC 2017844115', 'crop_box': [X0, Y0, X1, Y1], 'grabcut': rep, 'pieces': manifest},
          open(OUT + '/manifest.json', 'w'), indent=1)
print(json.dumps(rep))

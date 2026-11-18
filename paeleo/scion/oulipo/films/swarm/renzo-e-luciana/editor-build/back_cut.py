"""#29 GrabCut: the foreman's BACK view from Arthur S. Siegel, Bethlehem-Fairfield shipyards 1943 (LoC 2017851145, 8d28435v).
Seeded GrabCut inside hand-drawn guide polygons (probable FG band, sure FG core), one connected piece per part.
Outputs (RGBA, grey in RGB): fb_torso.png (head+torso+trousers to mid-thigh, raised arm removed at the shoulder seam),
fb_arm.png (sleeve + glove, the pry bar cut off above and below the glove)."""
import numpy as np, cv2, json, sys
from PIL import Image
SRC = '/home/user/bolas/paeleo/scion/oulipo/films/sources/renzo-e-luciana/editor/r2back/mid/8d28435v.jpg'
OUT = '/home/user/bolas/paeleo/scion/oulipo/films/sources/renzo-e-luciana/editor/pieces_r2'
g = np.asarray(Image.open(SRC).convert('L'))
H, W = g.shape
img3 = cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)
def poly(pts): m = np.zeros((H, W), np.uint8); cv2.fillPoly(m, [np.array(pts, np.int32)], 1); return m
def cut(prob_pts, sure_pts, bg_extra=None, it=6):
    mask = np.full((H, W), cv2.GC_BGD, np.uint8)
    pr = poly(prob_pts); mask[pr > 0] = cv2.GC_PR_FGD
    band = cv2.dilate(pr, np.ones((25, 25), np.uint8)) - pr; mask[band > 0] = cv2.GC_PR_BGD
    for s in sure_pts: mask[poly(s) > 0] = cv2.GC_FGD
    if bg_extra is not None: mask[bg_extra > 0] = cv2.GC_BGD
    b, f = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    cv2.grabCut(img3, mask, None, b, f, it, cv2.GC_INIT_WITH_MASK)
    m = ((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD)).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    keep = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]); m = (lab == keep).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    # fill holes
    ff = m.copy(); cv2.floodFill(ff, None, (0, 0), 1); m = m | (1 - ff)
    return m, pr
# shoulder seam: the line from the collar point (285,318) down to the armpit (330,520)
seam = poly([(285, 300), (W, 300), (W, H), (345, H), (345, 560), (330, 520)])
# torso: head (cap) + body, x from the negative edge (48) to the right flank; arm side excluded by the seam
torso_prob = [(48, 290), (95, 290), (118, 260), (120, 225), (132, 220), (135, 150), (200, 138), (272, 165), (275, 240), (262, 285), (290, 318),
              (335, 520), (372, 740), (350, 760), (345, 962), (48, 962)]
torso_sure = [[(70, 360), (250, 360), (300, 700), (70, 700)], [(150, 160), (255, 165), (250, 250), (145, 250)], [(150, 240), (240, 240), (245, 300), (140, 330), (110, 330)], [(100, 300), (280, 310), (280, 370), (70, 370)], [(70, 760), (300, 760), (300, 950), (70, 950)]]
mt, prt = cut(torso_prob, torso_sure, bg_extra=seam & (1 - poly([(285, 300), (300, 300), (345, 560), (330, 520)])))
mt[:, :48] = 0; mt[963:, :] = 0
# sky leak at the neck/collar: the open sky of this negative is > 200; the figure (cap, skin, leather) never is
sky = cv2.morphologyEx(((g > 198) & (np.arange(H)[:, None] < 340)).astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
sky = sky & (1 - poly([(140, 228), (244, 228), (246, 305), (140, 305)]))      # the bare neck is bright too: keep it
mt = mt & (1 - sky)
n_, lab_, st_, _ = cv2.connectedComponentsWithStats(mt, 8); mt = (lab_ == 1 + np.argmax(st_[1:, cv2.CC_STAT_AREA])).astype(np.uint8)
mt = cv2.morphologyEx(mt, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
n_, lab_, st_, _ = cv2.connectedComponentsWithStats(mt, 8); mt = (lab_ == 1 + np.argmax(st_[1:, cv2.CC_STAT_AREA])).astype(np.uint8)
# arm: sleeve from the shoulder seam to the glove; bar removed outside the glove
arm_prob = [(270, 300), (330, 330), (420, 385), (560, 395), (600, 360), (620, 325), (668, 320), (690, 360), (685, 425), (650, 440),
            (610, 445), (570, 470), (480, 530), (380, 535), (320, 520), (290, 470)]
arm_sure = [[(330, 380), (430, 420), (540, 430), (560, 470), (450, 500), (340, 470)], [(615, 345), (665, 345), (670, 410), (620, 415)]]
bar = poly([(632, 0), (668, 0), (668, 335), (632, 335)]) | poly([(632, 432), (668, 432), (668, H), (632, H)])
ma, pra = cut(arm_prob, arm_sure, bg_extra=bar)
ma[:, :285] = 0
def save(m, name, box, feather=1.2):
    a = cv2.GaussianBlur(m.astype(np.float32), (0, 0), feather)
    a = np.clip((a - .1) / .8, 0, 1)
    x0, y0, x1, y1 = box
    rgba = np.dstack([g, g, g, (a * 255).astype(np.uint8)])[y0:y1, x0:x1]
    Image.fromarray(rgba.astype(np.uint8), 'RGBA').save(f'{OUT}/{name}.png')
    prev = Image.new('RGBA', (x1 - x0, y1 - y0), (255, 0, 0, 255)); prev.alpha_composite(Image.fromarray(rgba, 'RGBA'))
    prev.convert('RGB').save(f'{OUT}/prev_{name}.jpg')
    area = float(m.sum()); gd = float(poly(torso_prob if name == 'fb_torso' else arm_prob).sum())
    return {'file': f'editor/pieces_r2/{name}.png', 'crop_in_source_px': box, 'mask_area_px': area, 'guide_area_px': gd,
            'components': int(cv2.connectedComponents(m)[0] - 1)}
info = {'source': 'LoC 2017851145 (8d28435v.jpg, 996x1024)', 'fb_torso': save(mt, 'fb_torso', (40, 130, 390, 966)),
        'fb_arm': save(ma, 'fb_arm', (260, 290, 700, 560))}
# pivots in piece coordinates
info['fb_torso']['pivots'] = {'shoulder': [290 - 40, 335 - 130], 'neck': [200 - 40, 268 - 130], 'hip_cut': [196 - 40, 956 - 130], 'cap_brim': [205 - 40, 222 - 130]}
info['fb_arm']['pivots'] = {'shoulder': [290 - 260, 335 - 290], 'grip': [645 - 260, 385 - 290]}
json.dump(info, open(OUT + '/back_pieces.json', 'w'), indent=1); print(json.dumps(info, indent=1))

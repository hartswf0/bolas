"""SCION 29 (GrabCut) for the animator unit: lift every body and prop out of its photograph.

python3 -I cut.py       ->  films/sources/la-belle-hortense/animator/cut/*.png, pieces.npz, cut_log.json

Inputs (untrusted data, decoded with PIL/cv2 only):
  conductor  : test-shot GrabCut of LoC 2017844115 (cut/pieces.npz, 312x715 piece frame) -> re-split into a
               jointed runner: torso, skirt (coat tails), far sleeve, forearm, 2 thighs, 2 shins
  visitor F  : LoC 2017750548 (8a36814v.jpg)  woman walking toward camera  (front profile)
  visitor B  : LoC 2017750547 (8a36813v.jpg)  same woman walking away       (back profile)
  bench      : LoC 2013633886 Highsmith, Sacramento park bench (sac_23429.jpg)
  bell       : Commons Bahnhofsglocke_HLB_1.jpg (PD), bell body + clapper
  door       : Bourre 50866795131 (CC BY 2.0), the two door leaves of the goods shed
"""
import os, json
import numpy as np, cv2

ROOT = '/home/user/bolas/paeleo/scion/oulipo'
SRC = os.path.join(ROOT, 'films/sources')
TS = os.path.join(SRC, 'la-belle-hortense/test-shot')
AN = os.path.join(SRC, 'la-belle-hortense/animator')
DL = os.path.join(AN, 'dl')
OUT = os.path.join(AN, 'cut')
os.makedirs(OUT, exist_ok=True)
LOG = {}


def save(name, a):
    cv2.imwrite(os.path.join(OUT, name + '.png'), np.clip(a * 255, 0, 255).astype(np.uint8))


def grabcut(bgr, rect, fg=(), bg=(), iters=6, name=''):
    """rect=(x,y,w,h); fg/bg = lists of polygons (definite seeds). Returns alpha 0..1 and failure mask."""
    m = np.zeros(bgr.shape[:2], np.uint8)
    m[:] = cv2.GC_BGD
    x, y, w, h = rect
    m[y:y + h, x:x + w] = cv2.GC_PR_FGD
    for p in bg: cv2.fillPoly(m, [np.array(p, np.int32)], cv2.GC_BGD)
    for p in fg: cv2.fillPoly(m, [np.array(p, np.int32)], cv2.GC_FGD)
    b = np.zeros((1, 65), np.float64); f = np.zeros((1, 65), np.float64)
    cv2.grabCut(bgr, m, None, b, f, iters, cv2.GC_INIT_WITH_MASK)
    a = ((m == cv2.GC_FGD) | (m == cv2.GC_PR_FGD)).astype(np.uint8)
    # keep the largest component (no background islands), fill holes
    n, lab, st, _ = cv2.connectedComponentsWithStats(a, 8)
    islands = 0
    if n > 1:
        k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA])); islands = n - 2
        a = (lab == k).astype(np.uint8)
    inv = 1 - a
    n2, lab2, st2, _ = cv2.connectedComponentsWithStats(inv, 4)
    for i in range(1, n2):
        if st2[i, cv2.CC_STAT_AREA] < 60: a[lab2 == i] = 1
    a = cv2.morphologyEx(a, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    alpha = cv2.GaussianBlur(a.astype(np.float32), (3, 3), 0)          # 1-2 px edge cleanup
    edge = cv2.morphologyEx(a, cv2.MORPH_GRADIENT, np.ones((5, 5), np.uint8))
    fail = ((m == cv2.GC_PR_FGD) | (m == cv2.GC_PR_BGD)) & (edge > 0)    # uncertain boundary pixels
    LOG[name] = dict(rect=list(rect), iters=iters, islands_removed=int(islands),
                     fg_seeds=len(fg), bg_seeds=len(bg), area_px=int(a.sum()),
                     uncertain_edge_px=int(fail.sum()))
    save(name + '_alpha', alpha); save(name + '_failure', fail.astype(np.float32))
    return alpha, fail


P = {}
# ------------------------------------------------------------------ conductor: a running rig from the test-shot cut
Z = np.load(os.path.join(TS, 'cut/pieces.npz'))
PH = 900                                            # piece canvas 312 x 900 (legs extend below the photo)
def pad(a): out = np.zeros((PH, a.shape[1]), np.float32); out[:a.shape[0]] = a; return out
g = pad(Z['g']); body_a = pad(Z['body_a']); coat = pad(Z['coat']); fore_a = pad(Z['fore_a'])
shinN = pad(Z['shinN']); shinF = pad(Z['shinF'])
yy = np.arange(PH)[:, None] * np.ones((1, 312))
# far sleeve (his right arm and the coat flap it carries), hinged at the shoulder
sleeve_poly = np.array([(56, 156), (112, 166), (110, 330), (100, 470), (96, 592), (14, 592), (12, 470), (26, 330), (38, 200)], np.int32)
sl = np.zeros((PH, 312), np.uint8); cv2.fillPoly(sl, [sleeve_poly], 1)
sleeve_a = body_a * cv2.GaussianBlur(sl.astype(np.float32), (5, 5), 0)
# body under the sleeve: same silhouette, cloth re-made from the neighbouring coat (inpaint, not invented)
g8 = (g * 255).astype(np.uint8)
inner = cv2.erode(sl, np.ones((9, 9), np.uint8))
g_under = cv2.inpaint(g8, inner, 13, cv2.INPAINT_TELEA).astype(np.float32) / 255.
# torso / skirt split at the waist (coat tails hinge at 470); 24 px overlap so the seam never opens
torso_a = (body_a - sleeve_a * 0) * np.clip((500 - yy) / 24, 0, 1)
skirt_a = body_a * np.clip((yy - 462) / 6, 0, 1) * (yy < 660)
# thighs: trouser cloth taken from each shin's own top rows, stretched to thigh length (cut paper replacement)
def thigh(shin, x0, x1, hip_x):
    rows = np.where(shin.sum(1) > 5)[0]
    top = rows.min()
    cloth = g[top:top + 30, x0:x1]
    th = cv2.resize(cloth, (x1 - x0, 250), interpolation=cv2.INTER_CUBIC)
    a = np.zeros((PH, 312), np.float32); gg = np.zeros((PH, 312), np.float32)
    gg[460:710, x0:x1] = th
    poly = np.array([(hip_x - 28, 460), (hip_x + 28, 460), ((x0 + x1) // 2 + 19, 706), ((x0 + x1) // 2 - 19, 706)], np.int32)
    m = np.zeros((PH, 312), np.uint8); cv2.fillPoly(m, [poly], 1)
    a = cv2.GaussianBlur(m.astype(np.float32), (3, 3), 0)
    return gg, a, int(top)
cols = lambda s: np.where(s.sum(0) > 3)[0]
cN, cF = cols(shinN), cols(shinF)
thN_g, thN_a, topN = thigh(shinN, int(cN.min()), int(cN.max()) + 1, 170)
thF_g, thF_a, topF = thigh(shinF, int(cF.min()), int(cF.max()) + 1, 112)
P.update(g=g, g_under=g_under, coat=coat, torso_a=torso_a, skirt_a=skirt_a, sleeve_a=sleeve_a,
         fore_a=fore_a, shinN=shinN, shinF=shinF, thN_g=thN_g, thN_a=thN_a, thF_g=thF_g, thF_a=thF_a,
         body_a=body_a)
KNEE_N = (float((cN.min() + cN.max()) / 2), float(topN + 4))
KNEE_F = (float((cF.min() + cF.max()) / 2), float(topF + 4))
RIG = {
    'piece_frame': '312x900 px, the test-shot crop of LoC 2017844115 (crop box [368,285,680,1000] of loc_2017844115.jpg) padded below',
    'source': {'id': 'LoC 2017844115', 'crop_box': [368, 285, 680, 1000],
               'mask': 'films/sources/la-belle-hortense/test-shot/cut/pieces.npz (GrabCut, see test-shot-build/rig.json)'},
    'joints': {
        'root':    {'piece': 'torso', 'parent': None, 'pivot': [170, 470]},
        'skirt':   {'piece': 'skirt', 'parent': 'root', 'pivot': [160, 470], 'limits_deg': [-6, 6]},
        'sleeve':  {'piece': 'sleeve', 'parent': 'root', 'pivot': [76, 176], 'limits_deg': [-12, 12]},
        'forearm': {'piece': 'forearm', 'parent': 'root', 'pivot': [246, 292], 'limits_deg': [-30, 22]},
        'hipN':    {'piece': 'thighN', 'parent': 'root', 'pivot': [170, 470], 'limits_deg': [-35, 40]},
        'kneeN':   {'piece': 'shinN', 'parent': 'hipN', 'pivot': [round(KNEE_N[0], 1), 700.0], 'child_pivot': [round(KNEE_N[0], 1), round(KNEE_N[1], 1)], 'limits_deg': [-75, 0], 'stretch_y': 1.75},
        'hipF':    {'piece': 'thighF', 'parent': 'root', 'pivot': [112, 470], 'limits_deg': [-35, 40]},
        'kneeF':   {'piece': 'shinF', 'parent': 'hipF', 'pivot': [round(KNEE_F[0], 1), 700.0], 'child_pivot': [round(KNEE_F[0], 1), round(KNEE_F[1], 1)], 'limits_deg': [-75, 0], 'stretch_y': 1.75, 'shade': 0.55},
    },
    'angle_sign': 'cv2 convention, degrees, positive = counter-clockwise on screen; runner faces/moves screen-right, so + hip = knee forward, - knee = foot tucked back',
    'dye': {'coat': '#e2011b stencil over a locally contrast-stretched print of the coat (folds kept)', 'trousers/face/cap': 'monochrome print on cream stock'},
}
# ------------------------------------------------------------------ visitor (two replacement profiles)
vf = cv2.imread(os.path.join(DL, 'loc_8a36814v.jpg'))
a, _ = grabcut(vf, (292, 268, 92, 232), name='visitorF',
               fg=[[(328, 300), (346, 300), (346, 440), (328, 440)], [(326, 280), (350, 280), (350, 300), (326, 300)],
                   [(318, 470), (330, 470), (330, 498), (318, 498)], [(340, 470), (352, 470), (352, 498), (340, 498)]],
               bg=[[(372, 440), (430, 440), (430, 520), (372, 520)], [(250, 260), (292, 260), (292, 520), (250, 520)],
                   [(286, 462), (314, 462), (314, 504), (286, 504)], [(358, 470), (392, 470), (392, 504), (358, 504)]])
x0, y0, x1, y1 = 286, 262, 392, 504
P['visF_g'] = cv2.cvtColor(vf, cv2.COLOR_BGR2GRAY)[y0:y1, x0:x1].astype(np.float32) / 255.
P['visF_a'] = a[y0:y1, x0:x1]
vb = cv2.imread(os.path.join(DL, 'loc_8a36813v.jpg'))
a, _ = grabcut(vb, (604, 188, 132, 366), name='visitorB',
               fg=[[(640, 240), (700, 240), (700, 440), (640, 440)], [(652, 200), (690, 200), (690, 232), (652, 232)],
                   [(650, 470), (664, 470), (664, 540), (650, 540)], [(676, 470), (690, 470), (690, 545), (676, 545)]],
               bg=[[(700, 392), (770, 392), (770, 495), (700, 495)], [(708, 495), (770, 495), (770, 560), (708, 560)]])
x0, y0, x1, y1 = 596, 180, 744, 560
P['visB_g'] = cv2.cvtColor(vb, cv2.COLOR_BGR2GRAY)[y0:y1, x0:x1].astype(np.float32) / 255.
P['visB_a'] = a[y0:y1, x0:x1]
# ------------------------------------------------------------------ bench
bb = cv2.imread(os.path.join(SRC, 'les-lieux-dune-fugue/r2/bench/sac_23429.jpg'))
bb = bb[960:1400, 700:1140].copy()
a, _ = grabcut(bb, (52, 70, 380, 300), name='bench',
               fg=[[(120, 100), (220, 90), (240, 150), (140, 200)], [(330, 215), (420, 205), (420, 225), (330, 235)]],
               bg=[[(0, 0), (440, 0), (440, 40), (0, 40)], [(380, 0), (440, 0), (440, 160), (380, 160)],
                   [(175, 215), (290, 215), (290, 250), (175, 250)], [(250, 110), (300, 110), (300, 140), (250, 140)],
                   [(110, 300), (180, 300), (180, 330), (110, 330)], [(230, 240), (330, 240), (330, 260), (230, 260)]])
P['bench_g'] = cv2.cvtColor(bb, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.
P['bench_a'] = a
# ------------------------------------------------------------------ bell (body + clapper)
be = cv2.imread(os.path.join(DL, 'Bahnhofsglocke_HLB_1.jpg'))
be = be[40:520, 300:700].copy()
# hand-placed scissor polygon first (the pine fringe leaks into a plain GrabCut), GrabCut refines a +-8 px band
BELLP = np.array([(168, 0), (201, 0), (217, 30), (217, 88), (267, 105), (276, 188), (305, 263), (313, 313), (309, 334),
                  (26, 334), (22, 313), (42, 263), (88, 188), (97, 105), (151, 88), (151, 30)], np.int32)
CLAPP = np.array([(151, 330), (201, 330), (197, 463), (176, 470), (155, 463)], np.int32)
pm = np.zeros(be.shape[:2], np.uint8); cv2.fillPoly(pm, [BELLP, CLAPP], 1)
band_in = cv2.erode(pm, np.ones((17, 17), np.uint8)); band_out = cv2.dilate(pm, np.ones((17, 17), np.uint8))
gm = np.where(band_in > 0, cv2.GC_FGD, np.where(band_out > 0, cv2.GC_PR_FGD, cv2.GC_BGD)).astype(np.uint8)
gm[(pm == 0) & (band_out > 0)] = cv2.GC_PR_BGD
b_ = np.zeros((1, 65)); f_ = np.zeros((1, 65))
cv2.grabCut(be, gm, None, b_, f_, 5, cv2.GC_INIT_WITH_MASK)
a = cv2.GaussianBlur(((((gm == 1) | (gm == 3)) & (band_out > 0)) & (cv2.dilate(pm, np.ones((5, 5), np.uint8)) > 0)).astype(np.float32), (3, 3), 0)  # GrabCut may only trim, never grow past the scissor line + 2 px
fail = ((gm == 2) | (gm == 3)) & (cv2.morphologyEx((a > .5).astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((5, 5), np.uint8)) > 0)
save('bell_alpha', a); save('bell_failure', fail.astype(np.float32))
LOG['bell'] = dict(method='scissor polygon (16 pts) + clapper polygon, GrabCut refining a 17 px band', area_px=int((a > .5).sum()), uncertain_edge_px=int(fail.sum()))
bg_ = cv2.cvtColor(be, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.
yb = np.arange(be.shape[0])[:, None] * np.ones((1, be.shape[1]))
P['bell_g'] = bg_
P['bell_a'] = a * (yb < 338)
P['clap_a'] = a * (yb >= 330)
# ------------------------------------------------------------------ door leaves (Bourre goods shed)
dp = cv2.imread(os.path.join(TS, 'plates/Bourr_Loir-et-Cher_50866795131_.jpg'))
door = cv2.cvtColor(dp[457:623, 440:561], cv2.COLOR_BGR2RGB).astype(np.float32) / 255.
P['door_rgb'] = door
LOG['door'] = dict(box=[440, 457, 561, 623], method='rectangle cut along the frame of the door (straight edges, no GrabCut needed)')

np.savez_compressed(os.path.join(OUT, 'pieces.npz'), **P)
for k in ('torso_a', 'skirt_a', 'sleeve_a', 'thN_a', 'thF_a', 'visF_a', 'visB_a', 'bench_a', 'bell_a', 'clap_a'):
    save('piece_' + k, P[k])
json.dump(RIG, open(os.path.join(AN, 'rig_runner.json'), 'w'), indent=1)
json.dump(LOG, open(os.path.join(OUT, 'cut_log.json'), 'w'), indent=1)
print(json.dumps(LOG, indent=0)); print(RIG['joints']['kneeN'], RIG['joints']['kneeF'])

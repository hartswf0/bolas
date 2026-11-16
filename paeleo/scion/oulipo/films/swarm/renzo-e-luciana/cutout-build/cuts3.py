"""#29 GrabCut cutout extraction for the r3 recast: Luciana = the young woman eating an apple (Marjory Collins, Ross Heater,
Buffalo 1943, LoC 8d16982u master-TIFF crop, K=6), and the foreman FRONT view (OWI 1943, LoC 8d28363v service JPEG).
Seeded GrabCut on a band around hand-drawn scissor guides (FGD = eroded guide, PR = band, BGD = outside), morph open/close,
largest component, hole fill, 1-1.5 px feather.  Pieces -> ../../../sources/renzo-e-luciana/cutout-performance/pieces/*.png
(RGBA grey+alpha) and pieces.json (crop, pivots in piece coords, source).  Failure masks -> pieces/fail_*.png when a check fails."""
import os, json, numpy as np, cv2
from PIL import Image
SRC = '/home/user/bolas/paeleo/scion/oulipo/films/sources/renzo-e-luciana'
O = SRC + '/cutout-performance/pieces'; os.makedirs(O, exist_ok=True)
def grey(p): return np.asarray(Image.open(p).convert('L')).astype(np.uint8)
def poly(shape, p):
    m = np.zeros(shape, np.uint8); cv2.fillPoly(m, [np.array(p, np.int32)], 255); return m
def largest(m):
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    return np.where(lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]), 255, 0).astype(np.uint8) if n > 1 else m
def fill(m):
    ff = m.copy(); fm = np.zeros((m.shape[0] + 2, m.shape[1] + 2), np.uint8); cv2.floodFill(ff, fm, (0, 0), 255)
    return m | cv2.bitwise_not(ff)
def band_gc(g, guide, band=9, it=8, bg_extra=()):
    img = cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)
    lap = cv2.convertScaleAbs(cv2.Laplacian(cv2.GaussianBlur(g, (0, 0), 1.5), cv2.CV_16S, ksize=3))
    img[..., 2] = np.clip(cv2.GaussianBlur(lap, (0, 0), 3) * 3, 0, 255)            # texture channel (fabric vs wall)
    k = np.ones((band, band), np.uint8)
    m = np.full(g.shape, cv2.GC_BGD, np.uint8)
    m[cv2.dilate(guide, k) > 0] = cv2.GC_PR_BGD; m[guide > 0] = cv2.GC_PR_FGD; m[cv2.erode(guide, k) > 0] = cv2.GC_FGD
    for p in bg_extra: m[poly(g.shape, p) > 0] = cv2.GC_BGD
    b = np.zeros((1, 65)); f = np.zeros((1, 65))
    cv2.grabCut(img, m, None, b, f, it, cv2.GC_INIT_WITH_MASK)
    out = np.where((m == 1) | (m == 3), 255, 0).astype(np.uint8)
    out = cv2.morphologyEx(out, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    out = cv2.morphologyEx(out, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    return fill(largest(out))
meta = {}
def check(name, m, guide):
    """acceptance: no islands (1 component), the matte stays within the guide band, area within 15% of the guide."""
    n = cv2.connectedComponents(m)[0] - 1; ra = m.sum() / max(guide.sum(), 1)
    ok = n == 1 and .85 < ra < 1.15
    if not ok: Image.fromarray(m).save(f'{O}/fail_{name}.png')
    return {'components': int(n), 'area_vs_guide': round(float(ra), 3), 'pass': bool(ok)}
def save(name, g, m, bbox, pivots, src, feather=1.2, note=''):
    x0, y0, x1, y1 = bbox
    a = cv2.GaussianBlur(m.astype(np.float32), (0, 0), feather)[y0:y1, x0:x1]
    Image.fromarray(np.dstack([g[y0:y1, x0:x1]] * 3 + [np.clip(a, 0, 255).astype(np.uint8)]), 'RGBA').save(f'{O}/{name}.png')
    prev = np.where(m > 0, g, (g * .25 + 190).astype(np.uint8))[y0:y1, x0:x1]; Image.fromarray(prev).save(f'{O}/prev_{name}.jpg')
    meta[name] = {'file': f'pieces/{name}.png', 'source': src, 'crop_in_source_px': [x0, y0, x1, y1],
                  'pivots': {k: [v[0] - x0, v[1] - y0] for k, v in pivots.items()}, 'note': note}
# ================= Luciana (8d16982u crop x 4572-9144, y 300-6036 of the 13070x10068 master, /6 -> 762x956) =================
g = grey(SRC + '/cutout-performance/hi/lu_8d16982.png')
fig = poly(g.shape, [(300, 175), (312, 110), (360, 60), (420, 38), (500, 30), (600, 33), (650, 45), (692, 92), (724, 150), (726, 215),
                     (704, 252), (672, 268), (664, 330), (668, 385), (652, 450), (642, 560), (620, 700), (600, 780), (592, 900),
                     (248, 900), (240, 790), (214, 708), (178, 645), (128, 585), (70, 520), (32, 448), (58, 388), (98, 344),
                     (162, 314), (240, 296), (298, 286)])
bgx = [[(0, 0), (762, 0), (762, 26), (0, 26)], [(0, 470), (60, 530), (120, 600), (165, 660), (200, 730), (222, 800), (230, 956), (0, 956)],
       [(690, 290), (762, 290), (762, 956), (660, 956), (640, 760), (668, 560), (690, 440)]]
fm = band_gc(g, fig, 11, bg_extra=bgx); fm[900:] = 0
lu_q = check('lu_figure', fm, fig)
arm_g = poly(g.shape, [(440, 862), (447, 800), (455, 760), (462, 720), (468, 682), (471, 650), (467, 620), (470, 590), (480, 560),
                       (500, 550), (520, 546), (540, 528), (556, 524), (578, 532), (592, 502), (618, 492), (640, 494), (656, 510),
                       (660, 540), (654, 572), (636, 602), (612, 622), (590, 642), (572, 662), (562, 694), (562, 742), (568, 792),
                       (578, 862)])
arm = band_gc(g, arm_g, 7, bg_extra=[[(300, 380), (470, 380), (470, 540), (300, 540)]])
arm &= cv2.dilate(arm_g, np.ones((9, 9), np.uint8))
arm_q = check('lu_arm', arm, arm_g)
apple_g = np.zeros(g.shape, np.uint8); cv2.ellipse(apple_g, (553, 480), (66, 67), -10, 0, 360, 255, -1)
apple = apple_g & ~arm
head_cut = poly(g.shape, [(280, 0), (762, 0), (762, 380), (668, 385), (560, 425), (522, 446), (492, 466), (452, 470), (430, 440),
                          (404, 384), (378, 334), (356, 300), (280, 290)])
head = fm & head_cut & ~arm & ~apple_g
body = fm & ~head_cut | (fm & cv2.dilate(~head_cut & 255, np.ones((15, 15), np.uint8)))   # 7 px overlap under the head (no detachment)
body &= ~(arm & cv2.erode(arm, np.ones((5, 5), np.uint8)))
# collage backing where the lifted forearm/apple uncover the sweater and collar: Telea fill of the body piece only (never flesh:
# the uncovered zone is cardigan, sweater and the collar point; the chin edge stays on the head piece)
under = cv2.dilate(arm | apple_g, np.ones((5, 5), np.uint8)) & ~head
gb = cv2.inpaint(g, under, 7, cv2.INPAINT_TELEA)
body_full = body | (under & fm)
save('lu_body', gb, body_full, (20, 280, 700, 900), {'hip': (420, 880), 'neck': (440, 450), 'elbow': (510, 900)}, '8d16982u',
     note='cardigan, striped collar, sweater; Telea backing only where the forearm and apple are lifted off')
save('lu_head', g, head | (fm & head_cut & apple_g & ~cv2.dilate(apple_g, np.ones((3, 3), np.uint8))), (290, 20, 735, 480),
     {'neck': (440, 450), 'mouth': (515, 412), 'eye': (612, 318)}, '8d16982u', note='hairnet, curls, face in three-quarter, chin')
save('lu_arm', g, arm, (430, 480, 670, 870), {'elbow': (510, 900), 'grip': (556, 545)}, '8d16982u', note='forearm + hand (fingers in front of the apple)')
save('apple', g, apple, (480, 405, 625, 555), {'c': (553, 480), 'grip': (556, 545)}, '8d16982u', 0.9, note='the real apple in her hand; behind the fingers')
# ================= foreman FRONT: OWI 1943, LoC 8d28363v (service JPEG 996x1024): full figure, hard hat, looking down-right ====
g = grey(SRC + '/loc/8d28363v.jpg')
fg_ = poly(g.shape, [(440, 238), (480, 240), (505, 262), (512, 296), (520, 302), (505, 318), (500, 340), (522, 372), (540, 420),
                     (552, 470), (560, 505), (556, 560), (548, 585), (552, 640), (556, 720), (560, 820), (560, 962), (390, 962),
                     (372, 860), (352, 740), (348, 640), (336, 610), (330, 540), (322, 470), (322, 400), (340, 362), (382, 340),
                     (402, 320), (380, 312), (400, 296), (410, 262)])
fr = band_gc(g, fg_, 9, bg_extra=[[(0, 0), (318, 0), (318, 1024), (0, 1024)]]); fr[963:] = 0
fr_q = check('foreman_front', fr, fg_)
save('foreman_front', g, fr, (310, 228, 572, 966), {'feet': (470, 962), 'neck': (452, 330)}, '8d28363v')
json.dump({'pieces': meta, 'checks': {'lu_figure': lu_q, 'lu_arm': arm_q, 'foreman_front': fr_q}}, open(O + '/pieces.json', 'w'), indent=1)
print(json.dumps({'lu_figure': lu_q, 'lu_arm': arm_q, 'foreman_front': fr_q}))

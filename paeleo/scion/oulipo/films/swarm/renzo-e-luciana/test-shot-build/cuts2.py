"""R2 #29 GrabCut cutout extraction from hi-res LoC master-TIFF crops (fetched by tiffcrop.py; decode-only).
Pieces -> cache2/*.png (RGBA: grey + alpha) with FK pivots in piece coords -> cache2/rig.json; previews prev_*.jpg."""
import os, json, numpy as np, cv2
from PIL import Image
B = os.path.dirname(os.path.abspath(__file__)); C = B + '/cache2'; os.makedirs(C, exist_ok=True)
H = '/home/user/bolas/paeleo/scion/oulipo/films/sources/renzo-e-luciana/test-shot/r2/hi'
SRC = '/home/user/bolas/paeleo/scion/oulipo/films/sources/renzo-e-luciana'
def grey(p): return np.asarray(Image.open(p).convert('L')).astype(np.uint8)
def poly(shape, p):
    m = np.zeros(shape, np.uint8); cv2.fillPoly(m, [np.array(p, np.int32)], 255); return m
def largest(m):
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    return np.where(lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]), 255, 0).astype(np.uint8) if n > 1 else m
def fill(m):
    ff = m.copy(); fm = np.zeros((m.shape[0] + 2, m.shape[1] + 2), np.uint8); cv2.floodFill(ff, fm, (0, 0), 255)
    return m | cv2.bitwise_not(ff)
def gc(g, rect, fg=(), bg=(), it=10):
    img = cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)
    lap = cv2.convertScaleAbs(cv2.Laplacian(cv2.GaussianBlur(g, (0, 0), 1.5), cv2.CV_16S, ksize=3))
    img[..., 2] = np.clip(cv2.GaussianBlur(lap, (0, 0), 3) * 3, 0, 255)      # texture channel
    m = np.full(g.shape, cv2.GC_BGD, np.uint8); x0, y0, x1, y1 = rect; m[y0:y1, x0:x1] = cv2.GC_PR_FGD
    for p in bg: cv2.fillPoly(m, [np.array(p, np.int32)], cv2.GC_BGD)
    for p in fg: cv2.fillPoly(m, [np.array(p, np.int32)], cv2.GC_FGD)
    b = np.zeros((1, 65)); f = np.zeros((1, 65))
    cv2.grabCut(img, m, None, b, f, it, cv2.GC_INIT_WITH_MASK)
    out = np.where((m == 1) | (m == 3), 255, 0).astype(np.uint8)
    out = cv2.morphologyEx(out, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    out = cv2.morphologyEx(out, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    return fill(largest(out))                        # invariants: no background islands, no interior holes
def save(name, g, m, bbox, pivots, src, feather=1.2):
    x0, y0, x1, y1 = bbox
    a = cv2.GaussianBlur(m.astype(np.float32), (0, 0), feather)[y0:y1, x0:x1]    # ~1-2 px feather, no erosion smear
    rgba = np.dstack([g[y0:y1, x0:x1]] * 3 + [np.clip(a, 0, 255).astype(np.uint8)])
    Image.fromarray(rgba, 'RGBA').save(f'{C}/{name}.png')
    prev = np.where(m > 0, g, (g * .25 + 190).astype(np.uint8))[y0:y1, x0:x1]
    Image.fromarray(prev).save(f'{C}/prev_{name}.jpg')
    return {name: {'file': f'cache2/{name}.png', 'source': src, 'crop': [x0, y0, x1, y1],
                   'pivots': {k: [v[0] - x0, v[1] - y0] for k, v in pivots.items()}}}
rig = {}
# ---------- Luciana: Russell Lee, Lunch hour at the Pacific Parachute Company, San Diego 1942 (8d03481u, crop K=8) ----------
g = grey(H + '/lu_8d03481.png')      # 741 x 691
m = gc(g, (20, 95, 700, 620),
       fg=[[(240, 200), (330, 190), (370, 240), (360, 290), (300, 300), (250, 280)],          # face
           [(150, 150), (280, 140), (300, 190), (200, 230), (150, 220)],                     # hair
           [(90, 360), (420, 340), (430, 520), (120, 540)],                                   # smock
           [(430, 290), (560, 262), (565, 280), (440, 310)],                                  # forearm
           [(600, 265), (640, 262), (645, 300), (605, 300)]],                                 # hand
       bg=[[(395, 150), (470, 150), (470, 245), (395, 245)], [(560, 95), (741, 95), (741, 240), (600, 255), (560, 230)],
           [(665, 330), (741, 320), (741, 430), (660, 420)], [(445, 380), (741, 380), (741, 691), (445, 691)],
           [(0, 610), (741, 610), (741, 691), (0, 691)], [(400, 250), (430, 250), (430, 285), (400, 285)]])
m[600:] = 0
m &= ~poly(g.shape, [(440, 330), (741, 330), (741, 691), (440, 691)])   # lunch box, thermos, the other woman's hand
fa = poly(g.shape, [(412, 278), (520, 255), (600, 238), (690, 245), (700, 330), (640, 345), (560, 318), (470, 322), (412, 336)])
farm = m & fa
# scissor guides (the cut lines a collage artist draws), refined by the GrabCut matte
hd = poly(g.shape, [(60, 170), (80, 120), (130, 90), (200, 78), (270, 85), (315, 110), (320, 150), (300, 185), (295, 215), (303, 248),
                    (292, 262), (292, 312), (240, 312), (180, 300), (120, 304), (70, 308), (20, 305), (20, 230), (50, 200)])
bd = poly(g.shape, [(20, 300), (60, 292), (130, 284), (240, 290), (330, 296), (420, 290), (445, 300), (445, 600), (20, 600)])
head = cv2.morphologyEx(m | (hd & (g < 200)), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)) & hd & ~farm
body = m & bd & ~farm
# collage backing where the lifted forearm leaves the sleeve end: a small dark card patch in the forearm's tone
patch = np.zeros(g.shape, np.uint8); cv2.ellipse(patch, (420, 308), (16, 22), 0, 0, 360, 255, -1)
patch &= cv2.dilate(m, np.ones((5, 5), np.uint8))
gb = g.copy(); gb[patch > 0] = np.median(g[farm > 0]) * .8 + np.median(g[body > 0]) * .2   # sleeve-mouth shadow card
rig.update(save('lu_body', gb, body | patch, (20, 150, 445, 600), {'hip': (250, 590), 'neck': (250, 300), 'elbow': (418, 307)}, '8d03481u'))
rig.update(save('lu_head', g, head, (20, 75, 325, 315), {'neck': (250, 300)}, '8d03481u'))
rig.update(save('lu_arm', g, farm, (405, 235, 705, 350), {'elbow': (418, 307), 'grip': (652, 326)}, '8d03481u'))
# ---------- Renzo: Arthur S. Siegel, Dodge truck plant, Detroit, lunch hour 1942 (8d07886u, crop K=8) ----------
g = grey(H + '/re_8d07886.png')      # 448 x 830
m = gc(g, (195, 25, 448, 640),
       fg=[[(245, 110), (300, 105), (305, 175), (250, 180)], [(250, 55), (350, 50), (355, 95), (250, 100)],
           [(280, 260), (400, 250), (410, 460), (290, 470)], [(275, 195), (320, 190), (325, 230), (280, 235)]],
       bg=[[(0, 0), (190, 0), (190, 640), (0, 640)], [(0, 0), (448, 0), (448, 28), (0, 28)],
           [(395, 60), (448, 60), (448, 190), (395, 190)], [(190, 0), (230, 0), (225, 85), (190, 95)]])
m[640:] = 0; m[:, :200] = 0; m[:, 428:] = 0
hd = poly(g.shape, [(190, 20), (448, 20), (448, 178), (345, 182), (300, 205), (250, 208), (205, 192)])
head = m & hd
neck_ov = poly(g.shape, [(240, 170), (350, 170), (350, 228), (240, 228)]) & m
body = m & ~hd
rig.update(save('re_body', g, body, (195, 150, 448, 640), {'hip': (330, 600), 'neck': (290, 205)}, '8d07886u'))
rig.update(save('re_head', g, head | neck_ov, (195, 20, 448, 232), {'neck': (290, 205), 'mouth': (214, 166)}, '8d07886u'))
# ---------- apple: Marjory Collins, Ross Heater lunch, Buffalo 1943 (8d16982v), the real apple in her hand ----------
g = grey(SRC + '/loc/8d16982v.jpg')
ap = poly(g.shape, [(590, 222), (604, 211), (628, 208), (646, 216), (652, 232), (642, 247), (622, 254), (600, 256), (588, 244)])
rig.update(save('apple', g, ap, (585, 205, 656, 260), {'c': (620, 232), 'top': (622, 212)}, '8d16982v', .8))
# ---------- the CAPOREPARTO doorway: Jack Delano, Madison WI 1942 (8d03483u, crop K=5): the real door casing + back room ----------
g = grey(H + '/door_8d03483.png')    # 615 x 1026
dm = poly(g.shape, [(0, 74), (30, 76), (433, 102), (421, 978), (0, 978)])
rig.update(save('door', g, dm, (0, 70, 440, 980), {'tl': (0, 74)}, '8d03483u', .7))
# the man at the bench inside, seen from behind (the foreman at his sheets): cut free for a pinned reading sway
fm = gc(g, (238, 352, 372, 742), fg=[[(258, 430), (300, 420), (305, 600), (262, 610)], [(258, 650), (295, 650), (295, 715), (258, 715)],
                                     [(292, 372), (320, 370), (322, 400), (295, 402)]],
        bg=[[(330, 240), (372, 240), (372, 350), (330, 350)], [(200, 600), (240, 600), (240, 742), (200, 742)], [(310, 560), (372, 560), (372, 742), (310, 742)]])
fm &= poly(g.shape, [(238, 352), (340, 352), (372, 470), (372, 540), (330, 560), (315, 742), (238, 742)])
rig.update(save('foreman', g, fm, (236, 350, 374, 744), {'feet': (280, 728)}, '8d03483u'))
# clean plate under him (only ever revealed by <=2 px of sway): Telea fill of his silhouette in the door piece
dg = cv2.inpaint(g, cv2.dilate(fm, np.ones((7, 7), np.uint8)), 6, cv2.INPAINT_TELEA)
rig.update(save('door_empty', dg, dm, (0, 70, 440, 980), {'tl': (0, 74)}, '8d03483u', .7))
# ---------- near pail pile: Russell Lee, time clock and tool boxes, San Diego 1941 (8c01492u, crop K=3) ----------
g = grey(H + '/pails_8c01492.png')   # 1647 x 982
init = (g < 118).astype(np.uint8) * 255
init = cv2.morphologyEx(init, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8)); init = fill(init)
init = cv2.morphologyEx(init, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
mm = np.where(cv2.erode(init, np.ones((15, 15), np.uint8)) > 0, cv2.GC_FGD,
              np.where(cv2.dilate(init, np.ones((15, 15), np.uint8)) > 0, cv2.GC_PR_FGD, cv2.GC_BGD)).astype(np.uint8)
small = cv2.resize(g, None, fx=.5, fy=.5, interpolation=cv2.INTER_AREA); ms = cv2.resize(mm, small.shape[::-1], interpolation=cv2.INTER_NEAREST)
b = np.zeros((1, 65)); f = np.zeros((1, 65))
cv2.grabCut(cv2.cvtColor(small, cv2.COLOR_GRAY2BGR), ms, None, b, f, 6, cv2.GC_INIT_WITH_MASK)
pm = cv2.resize(np.where((ms == 1) | (ms == 3), 255, 0).astype(np.uint8), g.shape[::-1], interpolation=cv2.INTER_LINEAR)
pm = fill(largest((pm > 127).astype(np.uint8) * 255))
wall = cv2.morphologyEx(((g > 158) & (cv2.GaussianBlur(g, (0, 0), 6) > 150)).astype(np.uint8) * 255, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
pm = fill(largest(cv2.morphologyEx(pm & ~wall, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))))   # wall wedges between boxes stay wall
rig.update(save('pails', g, pm, (0, 0, g.shape[1], g.shape[0]), {'tl': (0, 0)}, '8c01492u', 1.0))
json.dump(rig, open(C + '/rig.json', 'w'), indent=1); print('ok', list(rig))

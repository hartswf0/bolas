"""#29 GrabCut cutout extraction for the test shot. Decode-only use of LoC JPEGs (PIL/cv2).
Writes RGBA pieces (grey in RGB, alpha = mask) + pivots to cache/, and failure-mask previews."""
import os, json, numpy as np, cv2
from PIL import Image
B = os.path.dirname(os.path.abspath(__file__)); C = B + '/cache'
SRC = '/home/user/bolas/paeleo/scion/oulipo/films/sources/renzo-e-luciana'
def grey(p): return np.asarray(Image.open(p).convert('L')).astype(np.uint8)
def gc(g, rect, fg=(), bg=(), it=8):
    img = cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)
    # add a local-texture channel so GrabCut separates dark shirt from dark wood by more than tone
    lap = cv2.convertScaleAbs(cv2.Laplacian(cv2.GaussianBlur(g, (0, 0), 1.5), cv2.CV_16S, ksize=3))
    img[..., 2] = cv2.GaussianBlur(lap, (0, 0), 3) * 3
    m = np.full(g.shape, cv2.GC_BGD, np.uint8); x0, y0, x1, y1 = rect; m[y0:y1, x0:x1] = cv2.GC_PR_FGD
    for p in bg: cv2.fillPoly(m, [np.array(p, np.int32)], cv2.GC_BGD)
    for p in fg: cv2.fillPoly(m, [np.array(p, np.int32)], cv2.GC_FGD)
    b = np.zeros((1, 65)); f = np.zeros((1, 65))
    cv2.grabCut(img, m, None, b, f, it, cv2.GC_INIT_WITH_MASK)
    out = np.where((m == 1) | (m == 3), 255, 0).astype(np.uint8)
    out = cv2.morphologyEx(out, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    out = cv2.morphologyEx(out, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(out)          # invariant: no background islands
    if n > 1: out = np.where(lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]), 255, 0).astype(np.uint8)
    ff = out.copy(); fm = np.zeros((out.shape[0] + 2, out.shape[1] + 2), np.uint8); cv2.floodFill(ff, fm, (0, 0), 255)
    return out | cv2.bitwise_not(ff)                                  # fill interior holes
def poly(shape, p):
    m = np.zeros(shape, np.uint8); cv2.fillPoly(m, [np.array(p, np.int32)], 255); return m
def save(name, g, m, bbox, pivots, src):
    x0, y0, x1, y1 = bbox
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    if n > 2: m = np.where(lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]), 255, 0).astype(np.uint8)
    a = cv2.GaussianBlur(m, (3, 3), 0)[y0:y1, x0:x1]                  # 1px feather
    rgba = np.dstack([g[y0:y1, x0:x1]] * 3 + [a])
    Image.fromarray(rgba, 'RGBA').save(f'{C}/{name}.png')
    prev = np.where(m > 0, g, (g * .3 + 170).astype(np.uint8))[y0:y1, x0:x1]
    Image.fromarray(prev).save(f'{C}/prev_{name}.jpg')
    return {name: {'file': f'cache/{name}.png', 'source': src, 'crop': [x0, y0, x1, y1],
                   'pivots': {k: [v[0] - x0, v[1] - y0] for k, v in pivots.items()}}}
rig = {}
# ---------- Luciana: Marjory Collins, Ross Heater lunch, OWI-23899-D (8d16982v) ----------
g = grey(SRC + '/loc/8d16982v.jpg')
m = gc(g, (372, 36, 700, 470),
       fg=[[(540, 90), (640, 70), (690, 120), (660, 250), (600, 300), (520, 290), (510, 200)],
           [(590, 230), (655, 230), (660, 300), (600, 330)], [(470, 200), (540, 200), (560, 300), (520, 380), (470, 360)],
           [(430, 172), (505, 158), (505, 345), (402, 345), (398, 240)], [(585, 330), (615, 330), (610, 410), (590, 410)]],
       bg=[[(372, 250), (384, 250), (384, 470), (372, 470)], [(372, 36), (480, 36), (420, 150), (372, 190)],
           [(668, 300), (700, 260), (700, 470), (655, 470)], [(690, 36), (720, 36), (720, 470), (690, 470)]])
m[:, 672:] = 0; m[440:] = 0
cv2.fillPoly(m, [np.array([(380, 290), (470, 330), (470, 440), (380, 440)], np.int32)], 0)  # neighbour's plaid sleeve
cv2.fillPoly(m, [np.array([(372, 36), (507, 36), (507, 131), (500, 158), (392, 181), (372, 186)], np.int32)], 0)
# forearm + hand + apple piece (elbow pin at 597,420); the cut line runs across the cardigan sleeve
fa = poly(g.shape, [(560, 425), (570, 300), (575, 255), (586, 214), (630, 205), (660, 225), (668, 262), (660, 300), (640, 330), (622, 430)])
farm = m & fa
torso = m & ~cv2.dilate(farm, np.ones((1, 1), np.uint8))
# head piece above the neck cut (neck pin 585,258): collar line from 520,240 to 650,262 is the cut
hd = poly(g.shape, [(500, 30), (700, 30), (700, 205), (640, 225), (600, 250), (560, 262), (520, 252), (500, 230)])
head = torso & hd; body = torso & ~hd
# paper backing: where the forearm is lifted away, the cardigan behind it is missing; back it with dark card
hole = cv2.dilate(farm, np.ones((9, 9), np.uint8)) & poly(g.shape, [(540, 300), (650, 300), (650, 440), (540, 440)])
gb = g.copy(); gb[hole > 0] = 50                                     # dark card backing, the tone of the cardigan
chin = cv2.dilate(farm, np.ones((9, 9), np.uint8)) & poly(g.shape, [(560, 200), (660, 200), (660, 300), (560, 300)]) & ~hd
gb[(chin > 0)] = 50
hb = g.copy(); chin2 = cv2.dilate(farm, np.ones((7, 7), np.uint8)) & hd & poly(g.shape, [(570, 205), (660, 205), (660, 262), (570, 262)])
hb[chin2 > 0] = 118                                                  # pale card where her chin was hidden by the apple
head = head | chin2
rig.update(save('lu_body', gb, body | hole | chin, (390, 150, 672, 440), {'hip': (520, 440), 'neck': (585, 258), 'elbow': (597, 420)}, '8d16982v'))
rig.update(save('lu_head', hb, head, (500, 36, 700, 270), {'neck': (585, 258)}, '8d16982v'))
rig.update(save('lu_arm', g, farm, (555, 200, 672, 440), {'elbow': (597, 420), 'apple': (618, 243)}, '8d16982v'))
# apple alone (for Version B, where she is absent): the apple cut free of her fingers with scissor arcs
ap = poly(g.shape, [(590, 222), (604, 211), (628, 208), (646, 216), (652, 232), (642, 247), (622, 254), (600, 256), (588, 244)])
rig.update(save('apple', g, ap & m, (585, 205, 656, 260), {'c': (620, 232)}, '8d16982v'))
# ---------- Renzo: Marjory Collins, Buffalo 1943, OWI-23897-D (8d16980v), the man at the dresser ----------
g = grey(SRC + '/test-shot/8d16980v.jpg')
m = gc(g, (40, 198, 470, 700),
       fg=[[(285, 220), (370, 215), (405, 260), (415, 330), (380, 380), (330, 380), (290, 330), (280, 270)],
           [(300, 380), (360, 380), (360, 430), (300, 430)], [(120, 400), (300, 370), (330, 560), (120, 600)],
           [(60, 590), (300, 560), (310, 660), (60, 680)]],
       bg=[[(40, 198), (270, 198), (270, 215), (160, 300), (160, 420), (40, 430)], [(405, 160), (480, 160), (470, 260), (420, 260)],
           [(425, 250), (470, 250), (470, 520), (440, 520), (430, 420)], [(372, 198), (520, 198), (520, 230), (372, 210)]])
m[655:] = 0
cv2.fillPoly(m, [np.array([(335, 520), (450, 520), (470, 700), (335, 700)], np.int32)], 0)   # bottles + hands: cut off below chest
hd = poly(g.shape, [(260, 190), (430, 190), (430, 360), (395, 362), (370, 392), (335, 404), (300, 392), (260, 330)])
rig.update(save('re_head', g, cv2.erode(m & hd, np.ones((5, 5), np.uint8)), (255, 195, 430, 410), {'neck': (330, 396)}, '8d16980v'))
rb = m & ~hd & poly(g.shape, [(300, 398), (255, 352), (180, 362), (120, 415), (70, 515), (45, 575), (40, 660), (470, 660), (470, 522), (366, 522), (362, 420), (345, 400)])
rig.update(save('re_body', g, rb, (40, 300, 470, 660), {'hip': (200, 650), 'neck': (330, 396)}, '8d16980v'))
# ---------- foreman, seen from behind: Siegel, Bethlehem-Fairfield, lining up at the time clock (8d28364v) ----------
g = grey(SRC + '/loc_8d28364v.jpg')
clip = poly(g.shape, [(612, 345), (640, 337), (676, 345), (678, 362), (662, 380), (655, 400), (648, 412), (645, 452), (583, 452), (588, 420), (604, 405), (621, 398), (619, 383), (609, 372)])
m = gc(g, (583, 335, 680, 452), fg=[[(625, 350), (660, 350), (660, 372), (625, 375)], [(600, 420), (640, 420), (640, 445), (600, 445)]],
       bg=[[(583, 335), (605, 335), (598, 395), (583, 395)]])
m = m & clip
rig.update(save('foreman_back', g, m & clip, (580, 335, 682, 455), {'base': (615, 452)}, '8d28364v'))
json.dump(rig, open(C + '/rig.json', 'w'), indent=1); print(json.dumps(rig)[:400])

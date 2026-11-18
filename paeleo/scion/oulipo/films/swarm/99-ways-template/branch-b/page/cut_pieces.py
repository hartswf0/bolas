"""Page-cartoonist stand-in cutter (SCION #29 GrabCut + cleanup) until cutouts/manifest.json exists.
Source: Rothstein master 8b16710u.tif reassembled at every 3rd row/col (rothstein_master_s3.png, 4360x3100,
"S3" coords) by the test shot; the clerk mask comes from GrabCut on the half-res plate (roth_H, "H" coords = S3/2).
Also cuts: Rothstein 1937 tavern clock (8b16723v) with separable hands; Bubley 1943 visitor (8d33109v);
ANRC 1922 key (test shot piece). Decodes pixels only. Run: python3 -I cut_pieces.py"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from penlib import *  # noqa

OUT = PIECES
(OUT / "failures").mkdir(parents=True, exist_ok=True)
S3 = cv2.imread(str(TEST / "rothstein_master_s3.png"), cv2.IMREAD_GRAYSCALE)        # 4360x3100
H = cv2.imread(str(TEST / "roth_H.png"), cv2.IMREAD_GRAYSCALE)                      # 2180x1550
ROTH = (30, 186, 0.88)            # one levels curve for every Rothstein Randolph piece (as the approved test shot)
Ls = levels(S3, *ROTH).astype(np.uint8)
man = {"coords": "pieces are in S3 pixels (Rothstein master / 3); H = S3 / 2", "levels": {"rothstein_8b16710": ROTH}, "pieces": {}}


def up(m):  # H mask -> S3 mask, anti-aliased edge
    m = cv2.resize(m, (S3.shape[1], S3.shape[0]), interpolation=cv2.INTER_LINEAR)
    m = cv2.GaussianBlur(m, (0, 0), 1.0)
    return np.where(m > 127, 255, 0).astype(np.uint8)


def poly(shape, pts, k=2.0):
    m = np.zeros(shape, np.uint8)
    cv2.fillPoly(m, [np.int32(np.array(pts) * k)], 255, cv2.LINE_AA)
    return np.where(m > 127, 255, 0).astype(np.uint8)


def largest(m, close=5):
    if close:
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((close, close), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats((m > 127).astype(np.uint8))
    if n <= 1:
        return m
    big = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])
    m = np.where(lab == big, 255, 0).astype(np.uint8)
    inv = cv2.bitwise_not(m)
    n, lab, st, _ = cv2.connectedComponentsWithStats((inv > 127).astype(np.uint8))
    for i in range(1, n):
        x, y, w, h, a = st[i]
        if x > 0 and y > 0 and x + w < m.shape[1] and y + h < m.shape[0] and a < 20000:
            m[lab == i] = 255
    return m


def ncomp(m):
    return int(cv2.connectedComponentsWithStats((m > 127).astype(np.uint8))[0] - 1)


def grab(img, rect, fg=(), bg=(), it=6):
    mask = np.zeros(img.shape[:2], np.uint8)
    x, y, w, h = rect
    mask[y:y + h, x:x + w] = cv2.GC_PR_FGD
    for p in fg:
        cv2.fillPoly(mask, [np.int32(p)], cv2.GC_FGD)
    for p in bg:
        cv2.fillPoly(mask, [np.int32(p)], cv2.GC_BGD)
    b, f = np.zeros((1, 65)), np.zeros((1, 65))
    cv2.grabCut(img, mask, None, b, f, it, cv2.GC_INIT_WITH_MASK)
    return np.where((mask == 1) | (mask == 3), 255, 0).astype(np.uint8)


def save(name, g, a, pivots_S3, src, note="", multi=False):
    ys, xs = np.nonzero(a)
    x0, y0, x1, y1 = xs.min() - 4, ys.min() - 4, xs.max() + 5, ys.max() + 5
    x0, y0 = max(0, x0), max(0, y0)
    gg, aa = g[y0:y1, x0:x1], a[y0:y1, x0:x1]
    cv2.imwrite(str(OUT / f"{name}.png"), np.dstack([gg, gg, gg, aa]).astype(np.uint8))
    man["pieces"][name] = {"source": src, "bbox_src": [int(x0), int(y0), int(x1), int(y1)],
                           "pivots_local": {k: [float(v[0] - x0), float(v[1] - y0)] for k, v in pivots_S3.items()},
                           "components": ncomp(aa), "multi_part": multi, "note": note}


R8B = "LoC 2017776093 Rothstein 1937 (8b16710u master, every 3rd px)"

# ------------------------------------------------------------------ the clerk
clerkH = cv2.imread(str(TEST / "pieces" / "failures" / "clerk_mask_raw.png"), cv2.IMREAD_GRAYSCALE)   # approved test-shot GrabCut
Hc = cv2.cvtColor(H, cv2.COLOR_GRAY2BGR)
# his right forearm + hand resting on the desk (below the test shot's desk cut): GrabCut, then union
arm = grab(Hc, (1040, 1180, 300, 260),
           [[(1150, 1250), (1185, 1250), (1185, 1300), (1150, 1300)], [(1095, 1365), (1150, 1365), (1150, 1405), (1095, 1405)]],
           [[(1045, 1185), (1100, 1185), (1100, 1240), (1045, 1240)], [(1210, 1400), (1335, 1400), (1335, 1435), (1210, 1435)],
            [(1240, 1330), (1335, 1330), (1335, 1360), (1240, 1360)]])
arm = cv2.bitwise_and(arm, poly(arm.shape, [(1060, 1200), (1245, 1200), (1245, 1300), (1190, 1330), (1180, 1430), (1060, 1430)], 1.0))
side = cv2.bitwise_and(poly(H.shape, [(1630, 1080), (1770, 1100), (1890, 1280), (1890, 1335), (1630, 1335)], 1.0),
                       ((H > 125) * 255).astype(np.uint8))       # his shirt side under the raised arm (missed by the test mask)
clerkH = largest(cv2.bitwise_or(cv2.bitwise_or(clerkH, arm), side), 9)
cv2.imwrite(str(OUT / "failures" / "clerk_mask_H.png"), clerkH)
clerk = up(clerkH)
shp = clerk.shape

# FK split polygons (H coords, x2 to S3): pencil strip, fist+forearm, head above the collar
pencil_poly = [(1564, 868), (1575, 867), (1600, 992), (1595, 1000), (1590, 998)]
fore_poly = [(1588, 1000), (1600, 990), (1606, 975), (1700, 972), (1752, 1075), (1905, 1280), (1905, 1345), (1770, 1345),
             (1636, 1118), (1598, 1104), (1584, 1040)]
head_poly = [(1390, 755), (1645, 755), (1610, 960), (1586, 1010), (1572, 1042), (1500, 1056), (1432, 1044), (1395, 1000)]
pen = cv2.bitwise_and(clerk, poly(shp, pencil_poly))
fore = cv2.bitwise_and(clerk, cv2.bitwise_and(poly(shp, fore_poly), cv2.bitwise_not(pen)))
fore = largest(fore, 3)
pen = largest(pen, 3)
headm = cv2.bitwise_and(clerk, poly(shp, head_poly))
headm = cv2.bitwise_and(headm, cv2.bitwise_not(cv2.dilate(fore, np.ones((3, 3), np.uint8))))
# where the pencil lay across his temple/hair, the head keeps its own pixels: rebuilt from the hair either side
pen_on_head = cv2.bitwise_and(cv2.dilate(poly(shp, pencil_poly), np.ones((13, 13), np.uint8)), poly(shp, head_poly))
head_g = cv2.inpaint(Ls, pen_on_head, 7, cv2.INPAINT_TELEA)
# restore real grain over the rebuilt strip: high-pass of the neighbouring hair, shifted 24 px left (real pixels)
hp = Ls.astype(np.float32) - cv2.GaussianBlur(Ls.astype(np.float32), (0, 0), 3)
hp_shift = np.roll(hp, -24, axis=1)
head_g = np.where(pen_on_head > 0, np.clip(head_g + hp_shift, 0, 255), head_g).astype(np.uint8)
headm = cv2.bitwise_or(headm, cv2.bitwise_and(pen_on_head, cv2.dilate(headm, np.ones((25, 25), np.uint8))))
headm = cv2.bitwise_and(headm, poly(shp, head_poly))
# silhouette of the head on the pencil side: keep only what lies inside the convex hull of the head proper
cs, _ = cv2.findContours(largest(headm, 3), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
hull = np.zeros(shp, np.uint8)
cv2.fillPoly(hull, [cv2.convexHull(max(cs, key=cv2.contourArea))], 255)
headm = largest(np.where((pen_on_head > 0), hull, headm).astype(np.uint8), 3)

# torso: everything else; behind the forearm keep the body inside the shoulder line, rebuilt from his own shirt
torso = cv2.bitwise_and(clerk, cv2.bitwise_not(headm))
body_line = poly(shp, [(1572, 1042), (1640, 1060), (1700, 1120), (1760, 1220), (1800, 1345), (1040, 1345), (1040, 1042)])
under = cv2.bitwise_and(cv2.dilate(cv2.bitwise_or(fore, pen), np.ones((9, 9), np.uint8)), clerk)
torso = np.where((under > 0) & (body_line == 0), 0, torso).astype(np.uint8)
fill = cv2.bitwise_and(under, body_line)
tg = cv2.inpaint(Ls, fill, 15, cv2.INPAINT_TELEA).astype(np.float32)
# texture transfer from a real patch of the same shirt (his right breast, 2832..3000 x 2180..2560 in S3)
patch = Ls[2180:2560, 2780:2960].astype(np.float32)
phf = patch - cv2.GaussianBlur(patch, (0, 0), 4)
ys, xs = np.nonzero(fill)
tex = np.zeros_like(tg)
py, px = phf.shape
tex[ys, xs] = phf[(ys - ys.min()) % py, (xs - xs.min()) % px]
tg = np.where(fill > 0, np.clip(tg + tex, 0, 255), Ls).astype(np.uint8)
torso = largest(torso, 3)

col = (1505 * 2, 1046 * 2)
elbow = (1866 * 2, 1316 * 2)
grip = (1597 * 2, 997 * 2)
tip = (1569 * 2, 872 * 2)
chin = (1508 * 2, 1040 * 2)
save("clerk.torso", tg, torso, {"collar": col, "elbow": elbow, "root": (1505 * 2, 1340 * 2)}, R8B,
     "shirt under the forearm rebuilt: Telea base + high-pass texture of his own shirt (no soft fill)")
save("clerk.head", head_g, headm, {"collar": col, "chin": chin, "eye": (1497 * 2, 935 * 2)}, R8B,
     "pencil removed from the temple: inpaint + shifted hair grain, outline = convex hull of the head")
save("clerk.forearm", Ls, fore, {"elbow": elbow, "grip": grip}, R8B, "fist and forearm, fingers kept")
save("clerk.pencil", Ls, pen, {"grip": grip, "tip": tip}, R8B, "the pencil, a separate FK leaf on the fist")

# fingers check
fist = fore[1950:2210, 3180:3420]
cs, _ = cv2.findContours(fist, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
c = max(cs, key=cv2.contourArea)
d = cv2.convexityDefects(c, cv2.convexHull(c, returnPoints=False))
man["fingers_check"] = {"deep_convexity_defects": int(0 if d is None else (d.reshape(-1, 4)[:, 3] / 256 > 8).sum())}

# ------------------------------------------------------------------ the office plate with the clerk removed
# fill by real pixels, by bands, each band copied whole from one fixed offset in the same photograph so its
# structure continues (wainscot beadboard from the left; wall/cupboard base from the right); the smooth desk top
# by Telea; seams feathered 6 px.
handzone = poly(shp, [(1050, 1280), (1215, 1240), (1230, 1330), (1195, 1440), (1050, 1440)])
hole = cv2.dilate(cv2.bitwise_or(clerk, handzone), np.ones((19, 19), np.uint8))
plate = Ls.astype(np.float32).copy()
Hh, Ww = Ls.shape
bands = [(0, 1890, 560), (1890, 2620, -1640)]          # (row0, row1, dx: source = target + dx)
for r0, r1, dx in bands:
    m = np.zeros_like(hole); m[r0:r1] = hole[r0:r1]
    sh = np.float32([[1, 0, -dx], [0, 1, 0]])
    srcimg = cv2.warpAffine(Ls, sh, (Ww, Hh), borderMode=cv2.BORDER_REFLECT).astype(np.float32)
    f = cv2.GaussianBlur(m, (0, 0), 6).astype(np.float32) / 255
    f = np.maximum(f, (m > 0).astype(np.float32) * 0.0)
    plate = plate * (1 - f) + srcimg * f
dm = np.zeros_like(hole); dm[2620:] = hole[2620:]
tel = cv2.inpaint(Ls, dm, 21, cv2.INPAINT_TELEA).astype(np.float32)
f = cv2.GaussianBlur(dm, (0, 0), 6).astype(np.float32) / 255
plate = plate * (1 - f) + tel * f
plate = np.clip(plate, 0, 255).astype(np.uint8)
cv2.imwrite(str(OUT / "office.plate.png"), plate)
man["office_plate"] = {"source": R8B, "size": list(plate.shape[::-1]),
                       "method": "clerk hole (mask dilated 19 px) filled row by row with the same row's real pixels from left of the hole; 5 px seam feather"}

# ------------------------------------------------------------------ cupboard set (as the approved test shot, at S3)
door_box = (1562 * 2, 398 * 2, 1858 * 2, 952 * 2)
dx0, dy0, dx1, dy1 = door_box
door = plate[dy0:dy1, dx0:dx1].copy()
cv2.imwrite(str(OUT / "cupboard.door.png"), np.dstack([door, door, door, np.full_like(door, 255)]))
man["pieces"]["cupboard.door"] = {"source": R8B, "bbox_src": list(door_box), "pivots_local": {"jamb_top": [0, 0], "jamb_bottom": [0, dy1 - dy0]}, "components": 1}
bead = Ls[2060:2600, 120:940]
inter = cv2.resize(bead, (dx1 - dx0, dy1 - dy0), interpolation=cv2.INTER_CUBIC).astype(np.float32) * 0.62
rack = Ls[418:1656, 1672:2392].astype(np.float32)
ix0, iy0 = 52, 44
rw, rh = (dx1 - dx0) - 2 * ix0, (dy1 - dy0) - iy0 - 80
inter[iy0:iy0 + rh, ix0:ix0 + rw] = cv2.resize(rack, (rw, rh), interpolation=cv2.INTER_CUBIC)
yy, xx = np.mgrid[0:dy1 - dy0, 0:dx1 - dx0].astype(np.float32)
inter = inter * (1 - 0.5 * np.exp(-yy / 90) - 0.4 * np.exp(-xx / 80))
setp = plate.astype(np.float32)
setp[dy0:dy1, dx0:dx1] = inter
cv2.imwrite(str(OUT / "set.plate.png"), np.clip(setp, 0, 255).astype(np.uint8))
man["set_plate"] = {"source": R8B, "opening_src": list(door_box),
                    "interior": "cupboard interior: beadboard of the same office x0.62 + its ticket rack (real pixels), frame shade"}

# ------------------------------------------------------------------ clock (Rothstein 1937, LoC 2017776111), hands separable
K = cv2.imread(str(MEDIA / "8b16723v.jpg"), cv2.IMREAD_GRAYSCALE)
CLK = (18, 200, 0.95)
man["levels"]["rothstein_8b16723_clock"] = CLK
Kl = levels(K, *CLK).astype(np.uint8)
Kc = cv2.cvtColor(K, cv2.COLOR_GRAY2BGR)
cm = np.zeros(K.shape, np.uint8)
cv2.circle(cm, (410, 212), 150, 255, -1)
cv2.circle(cm, (398, 470), 95, 255, -1)
cv2.fillPoly(cm, [np.int32([(305, 330), (505, 330), (480, 410), (330, 410)])], 255)
g = grab(Kc, (250, 55, 320, 520), [[(330, 140), (490, 140), (490, 290), (330, 290)], [(360, 440), (440, 440), (440, 500), (360, 500)]],
         [[(80, 600), (700, 600), (700, 620), (80, 620)], [(600, 300), (700, 300), (700, 340), (600, 340)]])
clock_a = largest(cv2.bitwise_and(cm, g), 5)
clock_a = cv2.bitwise_and(clock_a, cm)    # the whip draped over the case is outside the case circle: left out
clock_a = largest(clock_a, 3)
C0 = np.array([410.0, 212.0])
hour_poly = [(404, 214), (406, 165), (416, 140), (428, 150), (424, 172), (417, 216)]
min_poly = [(406, 208), (470, 140), (486, 132), (490, 142), (476, 154), (414, 218)]
hm = np.zeros(K.shape, np.uint8)
cv2.fillPoly(hm, [np.int32(hour_poly)], 255)
mm = np.zeros(K.shape, np.uint8)
cv2.fillPoly(mm, [np.int32(min_poly)], 255)
dark = (K < 120).astype(np.uint8) * 255
hourA = cv2.bitwise_and(hm, dark)
minA = cv2.bitwise_and(mm, dark)
face = cv2.inpaint(Kl, cv2.dilate(cv2.bitwise_or(hourA, minA), np.ones((5, 5), np.uint8)), 4, cv2.INPAINT_TELEA)
cv2.circle(face, (410, 212), 9, int(np.percentile(Kl[200:225, 398:422], 5)), -1, cv2.LINE_AA)   # the arbor boss, its own tone
save("clock.case", face, clock_a, {"arbor": tuple(C0)}, "LoC 2017776111 Rothstein 1937 clock (8b16723v)", "dial, case and pendulum box; hands removed")
save("clock.hour", Kl, hourA, {"arbor": tuple(C0)}, "LoC 2017776111", "hour hand (source reads XII)", multi=True)
save("clock.minute", Kl, minA, {"arbor": tuple(C0)}, "LoC 2017776111", "minute hand (source reads ~:08)", multi=True)
man["pieces"]["clock.hour"]["source_angle_deg"] = 0.0 + math.degrees(math.atan2(422 - 410, 212 - 157))
man["pieces"]["clock.minute"]["source_angle_deg"] = math.degrees(math.atan2(482 - 410, 212 - 150))

# ------------------------------------------------------------------ the visitor (Bubley 1943, LoC 2017861739), waist up
B = cv2.imread(str(SRC / "loc" / "8d33109v.jpg"), cv2.IMREAD_GRAYSCALE)
BUB = (20, 215, 1.0)
man["levels"]["bubley_8d33109"] = BUB
Bc = cv2.cvtColor(B, cv2.COLOR_GRAY2BGR)
vb = grab(Bc, (515, 290, 215, 330), [[(590, 330), (625, 330), (625, 360), (590, 360)], [(560, 420), (680, 420), (680, 600), (560, 600)]],
          [[(735, 300), (760, 300), (760, 620), (735, 620)], [(515, 290), (560, 290), (560, 320), (515, 320)]])
vb[620:] = 0
vb = largest(vb, 5)
save("visitor", levels(B, *BUB).astype(np.uint8), vb, {"head": (608, 340)}, "LoC 2017861739 Bubley 1943 (8d33109v)", "waist up; seen only behind the frosted glass")

# ------------------------------------------------------------------ the key (approved test-shot piece, ANRC 1922)
k = cv2.imread(str(TEST / "pieces" / "key.png"), cv2.IMREAD_UNCHANGED)
cv2.imwrite(str(OUT / "key.png"), k)
tm = json.load(open(TEST / "pieces" / "manifest.json"))["pieces"]["key"]
man["pieces"]["key"] = dict(tm, source="LoC 2017679951 ANRC 1922 (14940v)")
man["levels"]["anrc_14940_key"] = (22, 212, 0.95)

# contact sheet + components report
tiles = []
for n in ["clerk.torso", "clerk.head", "clerk.forearm", "clerk.pencil", "clock.case", "visitor", "key"]:
    im = cv2.imread(str(OUT / f"{n}.png"), cv2.IMREAD_UNCHANGED)
    a = im[..., 3:4].astype(np.float32) / 255
    chk = np.where(((np.indices(im.shape[:2]).sum(0) // 16) % 2)[..., None] == 0, 200, 120)
    comp = im[..., :3] * a + chk * (1 - a)
    s = 500 / comp.shape[0]
    tiles.append(cv2.resize(comp.astype(np.uint8), (max(8, int(comp.shape[1] * s)), 500)))
cv2.imwrite(str(OUT / "contact.jpg"), np.hstack(tiles))
json.dump(man, open(OUT / "manifest.json", "w"), indent=1)
print({k: v.get("components") for k, v in man["pieces"].items()}, man["fingers_check"])

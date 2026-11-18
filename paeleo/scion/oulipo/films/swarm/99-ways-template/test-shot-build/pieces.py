"""SCION #29 GrabCut: cut the test-shot pieces from the Rothstein master (half-res reassembly) and the
1922 ANRC key plate. Writes pieces/*.png (gray + alpha), the set plate, a manifest with source bboxes,
pivots and levels, a contact sheet and failure masks. Run: python3 -I pieces.py"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *  # noqa

PIECES.mkdir(parents=True, exist_ok=True)
(PIECES / "failures").mkdir(exist_ok=True)
H = cv2.imread(str(MEDIA / "roth_H.png"), cv2.IMREAD_GRAYSCALE)      # 2180x1550, = master/2 (every 6th px)
Hc = cv2.cvtColor(H, cv2.COLOR_GRAY2BGR)
man = {"source_scale": "roth_H = Rothstein master 8b16710u.tif sampled every 6th row/col (rows/cols 480..13560, 300..9600)",
       "levels": {"rothstein": ROTH_LEVELS, "key": KEY_LEVELS}, "pieces": {}}


def grab(img, rect, fg_polys=(), bg_polys=(), it=6):
    mask = np.zeros(img.shape[:2], np.uint8)
    x, y, w, h = rect
    mask[y:y + h, x:x + w] = cv2.GC_PR_FGD
    for p in fg_polys:
        cv2.fillPoly(mask, [np.int32(p)], cv2.GC_FGD)
    for p in bg_polys:
        cv2.fillPoly(mask, [np.int32(p)], cv2.GC_BGD)
    bgd, fgd = np.zeros((1, 65)), np.zeros((1, 65))
    cv2.grabCut(img, mask, None, bgd, fgd, it, cv2.GC_INIT_WITH_MASK)
    return np.where((mask == 1) | (mask == 3), 255, 0).astype(np.uint8)


def largest(m, close=7):
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((close, close), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    big = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])
    m = np.where(lab == big, 255, 0).astype(np.uint8)
    # fill interior holes (so no background islands inside the figure)
    inv = cv2.bitwise_not(m)
    n, lab, st, _ = cv2.connectedComponentsWithStats(inv)
    for i in range(1, n):
        x, y, w, h, a = st[i]
        if x > 0 and y > 0 and x + w < m.shape[1] and y + h < m.shape[0] and a < 4000:
            m[lab == i] = 255
    return m


def ncomp(m):
    return cv2.connectedComponentsWithStats((m > 127).astype(np.uint8))[0] - 1


def save(name, gray, alpha, bbox, pivots, note=""):
    x0, y0, x1, y1 = bbox
    g = gray[y0:y1, x0:x1]
    a = alpha[y0:y1, x0:x1]
    cv2.imwrite(str(PIECES / f"{name}.png"), np.dstack([g, g, g, a]).astype(np.uint8))
    man["pieces"][name] = {"bbox_src": [int(v) for v in bbox], "pivots_local": {k: [float(v[0] - x0), float(v[1] - y0)] for k, v in pivots.items()},
                           "components": ncomp(a), "note": note}


Lr = levels(H, *ROTH_LEVELS).astype(np.uint8)

# ---------------- the clerk (box + scribble seeds), cut at the desk line
fg_seeds = [[(1470, 1100), (1560, 1100), (1560, 1300), (1470, 1300)],          # shirt front/tie
            [(1450, 850), (1560, 850), (1560, 980), (1450, 980)],             # face
            [(1610, 1000), (1670, 1000), (1670, 1080), (1610, 1080)]]          # pencil fist
bg_seeds = [[(1100, 700), (1380, 700), (1380, 860), (1100, 860)],
            [(1700, 700), (1910, 700), (1910, 940), (1700, 940)],
            [(1880, 1000), (1910, 1000), (1910, 1200), (1880, 1200)]]
clerk = grab(Hc, (1105, 760, 800, 570), fg_seeds, bg_seeds)
cv2.ellipse(clerk, (1508, 870), (86, 98), 0, 0, 360, 255, -1, cv2.LINE_AA)      # hair lost against the dark wall
cv2.fillPoly(clerk, [np.int32([(1560, 878), (1574, 872), (1604, 990), (1590, 1000)])], 255)  # the pencil
clerk[1327:] = 0
clerk = largest(clerk)
cv2.imwrite(str(PIECES / "failures" / "clerk_mask_raw.png"), clerk)

# split polygons (FK pieces): head above the collar, forearm+fist+pencil, torso the rest
head_poly = np.int32([(1395, 760), (1640, 760), (1612, 1000), (1575, 1040), (1500, 1052), (1430, 1040), (1395, 1000)])
fore_poly = np.int32([(1561, 881), (1571, 878), (1604, 985), (1620, 976), (1700, 972), (1752, 1075), (1905, 1280), (1905, 1340),
                      (1770, 1340), (1636, 1118), (1598, 1104), (1584, 1040), (1592, 1000)])
hp = np.zeros_like(clerk); cv2.fillPoly(hp, [head_poly], 255)
fp = np.zeros_like(clerk); cv2.fillPoly(fp, [fore_poly], 255)
fore = cv2.bitwise_and(clerk, fp)
head = cv2.bitwise_and(cv2.bitwise_and(clerk, hp), cv2.bitwise_not(fp))
head = largest(head, 3)
fore = largest(fore, 3)
torso = cv2.bitwise_and(clerk, cv2.bitwise_not(head))
# behind the forearm: keep the body silhouette left of the body line, drop the rest (background)
body_line = np.int32([(1600, 1040), (1655, 1046), (1730, 1170), (1770, 1340), (1100, 1340), (1100, 1040)])
bl = np.zeros_like(clerk); cv2.fillPoly(bl, [body_line], 255)
# torso pixels under the forearm are filled from the surrounding shirt (Telea inpaint, torso only)
hole = cv2.dilate(cv2.bitwise_and(fp, clerk), np.ones((7, 7), np.uint8))
tg = cv2.inpaint(Lr, hole, 11, cv2.INPAINT_TELEA)
torso = np.where((fp > 0) & ((bl == 0) | (tg < 165)), 0, torso).astype(np.uint8)
torso = largest(torso, 3)
hg = cv2.inpaint(Lr, cv2.bitwise_and(cv2.dilate(fp, np.ones((3, 3), np.uint8)), hp), 4, cv2.INPAINT_TELEA)

# mirror the clerk so he faces the cupboard (no lettering on him)
X0, X1, Y0, Y1 = 1100, 1910, 755, 1340
def mir(a):
    s = a[Y0:Y1, X0:X1][:, ::-1].copy()
    return s
def mp(p):
    return ((X1 - 1) - p[0] + X0, p[1])  # mirrored point in a frame whose x origin is X0
Wc = X1 - X0
def mloc(p):  # source point -> mirrored local coords of the clerk frame
    return (X1 - 1 - p[0], p[1] - Y0)

collar = (1505, 1046)
elbow = (1835, 1305)
shoulder = (1660, 1050)
for name, g, a, piv in [("clerk.torso", tg, torso, {"collar": collar, "elbow": elbow, "shoulder": shoulder, "root": (1505, 1327)}),
                        ("clerk.head", hg, head, {"collar": collar}),
                        ("clerk.forearm_pencil", Lr, fore, {"elbow": elbow, "pencil_tip": (1567, 872), "fist": (1640, 1040)})]:
    gm, am = mir(g), mir(a)
    pv = {k: mloc(v) for k, v in piv.items()}
    cv2.imwrite(str(PIECES / f"{name}.png"), np.dstack([gm, gm, gm, am]).astype(np.uint8))
    man["pieces"][name] = {"bbox_src": [X0, Y0, X1, Y1], "mirrored": True,
                           "pivots_local": {k: [float(v[0]), float(v[1])] for k, v in pv.items()},
                           "components": ncomp(am)}

# fingers retained check: count convexity defects on the fist region of the forearm piece
fist = fore[960:1110, 1590:1700]
cs, _ = cv2.findContours(fist, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
c = max(cs, key=cv2.contourArea)
hull = cv2.convexHull(c, returnPoints=False)
defects = cv2.convexityDefects(c, hull)
deep = int(0 if defects is None else (defects.reshape(-1, 4)[:, 3] / 256 > 6).sum())
man["fingers_check"] = {"fist_region_src": [1590, 960, 1700, 1110], "deep_convexity_defects": deep,
                        "note": "knuckle notches retained in the mask (source shows 3-4 curled fingers)"}

# ---------------- the set plate: cupboard wall, the clerk removed (Telea), left door opened
px0, py0, px1, py1 = 1240, 150, 2140, 1020
gone = cv2.dilate(clerk, np.ones((21, 21), np.uint8))
plate = cv2.inpaint(Lr, gone, 15, cv2.INPAINT_TELEA)
door_box = (1562, 398, 1858, 952)
dx0, dy0, dx1, dy1 = door_box
door = plate[dy0:dy1, dx0:dx1].copy()
cv2.imwrite(str(PIECES / "cupboard.door.png"), np.dstack([door, door, door, np.full_like(door, 255)]))
man["pieces"]["cupboard.door"] = {"bbox_src": list(door_box), "pivots_local": {"jamb_top": [0, 0], "jamb_bottom": [0, dy1 - dy0]}, "components": 1}
# interior: back of the cupboard from the dark beadboard of the same office, ticket rack as the shelves
bead = Lr[1030:1300, 60:470]
inter = cv2.resize(bead, (dx1 - dx0, dy1 - dy0), interpolation=cv2.INTER_CUBIC).astype(np.float32) * 0.72
rack = Lr[209:828, 836:1196].astype(np.float32)
ix0, iy0 = 26, 22
rw, rh = (dx1 - dx0) - 2 * ix0, (dy1 - dy0) - iy0 - 40
rack = cv2.resize(rack, (rw, rh), interpolation=cv2.INTER_CUBIC)
inter[iy0:iy0 + rh, ix0:ix0 + rw] = rack
# the cupboard's own frame shades its interior along the top and the lit-side jamb (light from upper left)
yy, xx = np.mgrid[0:dy1 - dy0, 0:dx1 - dx0].astype(np.float32)
shade = 1 - 0.45 * np.exp(-yy / 45) - 0.35 * np.exp(-xx / 40)
inter = inter * shade
plate = plate.astype(np.float32)
plate[dy0:dy1, dx0:dx1] = inter
plate = plate[py0:py1, px0:px1]
cv2.imwrite(str(PIECES / "set.plate.png"), np.clip(plate, 0, 255).astype(np.uint8))
man["set_plate"] = {"bbox_src": [px0, py0, px1, py1], "opening_src": list(door_box),
                    "interior": "beadboard Lr[1030:1300,60:470] x0.72 + ticket rack Lr[209:828,836:1196]; frame shade top/left"}

# ---------------- P6 window plate (the lamp stays in the photograph)
win = Lr[300:1113, 30:550]
cv2.imwrite(str(PIECES / "window.plate.png"), win)
man["window_plate"] = {"bbox_src": [30, 300, 550, 1113]}

# ---------------- the key (ANRC 1922), GrabCut, ring hole kept open
K = cv2.imread(str(MEDIA / "14940v.jpg"), cv2.IMREAD_GRAYSCALE)
Kl = levels(K, *KEY_LEVELS).astype(np.uint8)
Kc = cv2.cvtColor(K, cv2.COLOR_GRAY2BGR)
km = grab(Kc, (295, 115, 205, 735), [[(395, 300), (420, 300), (420, 820), (395, 820)], [(315, 700), (360, 700), (360, 780), (315, 780)]],
          [[(340, 160), (455, 160), (455, 225), (340, 225)]])
km = largest(km, 3)
ring_in = np.zeros_like(km)
cv2.ellipse(ring_in, (398, 190), (74, 52), 0, 0, 360, 255, -1)
km = np.where((ring_in > 0) & (K > 150), 0, km).astype(np.uint8)
ys, xs = np.nonzero(km)
kb = (xs.min() - 2, ys.min() - 2, xs.max() + 3, ys.max() + 3)
save("key", Kl, km, kb, {"ring_top": (398, 132)}, "ring hole kept as background; one component")
cv2.imwrite(str(PIECES / "failures" / "key_mask.png"), km)

# ---------------- contact sheet
tiles = []
for n in ["clerk.torso", "clerk.head", "clerk.forearm_pencil", "cupboard.door", "key"]:
    im = cv2.imread(str(PIECES / f"{n}.png"), cv2.IMREAD_UNCHANGED)
    a = im[..., 3:4].astype(np.float32) / 255
    chk = np.where(((np.indices(im.shape[:2]).sum(0) // 16) % 2)[..., None] == 0, 200, 120)
    comp = im[..., :3] * a + chk * (1 - a)
    s = 400 / comp.shape[0]
    tiles.append(cv2.resize(comp.astype(np.uint8), (int(comp.shape[1] * s), 400)))
cv2.imwrite(str(PIECES / "contact.jpg"), np.hstack(tiles))
json.dump(man, open(PIECES / "manifest.json", "w"), indent=1)
print(json.dumps({k: v.get("components") for k, v in man["pieces"].items()}), man["fingers_check"])

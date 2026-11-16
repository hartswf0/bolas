# BB-08 test shot, pre-production: GrabCut extraction of the puppet pieces (SCION #29) and the rig (SCION #2).
#   python3 -I cut.py <sources/bang-bang dir> <out dir for pieces>
# Pieces: glider body + pilot torso (LIL-START), legs on the hip pin (LIL-START), crow body, head (neck pin),
# wing (shoulder pin; re-pinned so the perched engraving can fly).  Each piece is the engraving's own line printed
# in warm ink on the page's cream stock; alpha is the scissor cut.  Failure masks (GrabCut-rejected ink) are exported.
import sys, os, json
import numpy as np, cv2
from PIL import Image

SRC, OUT = sys.argv[1:3]
os.makedirs(OUT, exist_ok=True)
CARD = np.array((242, 228, 212), np.float32)
INKC = np.array((45, 38, 32), np.float32)


def fill_holes(m, maxarea):
    inv = (m == 0).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(inv, 4)
    out = m.copy()
    for i in range(1, n):
        x, y, w, h, a = st[i]
        if a < maxarea and x > 0 and y > 0 and x + w < m.shape[1] and y + h < m.shape[0]:
            out[lab == i] = 255
    return out


def keep_seeded(m, seed):
    """Keep only components touching a definite-foreground seed: no background islands."""
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    keep = set(np.unique(lab[(seed > 0) & (m > 0)])) - {0}
    return np.isin(lab, list(keep)).astype(np.uint8) * 255


def scissor(m, seed, amt=1.0):
    r = np.random.default_rng(seed); H_, W_ = m.shape
    nz = cv2.resize(r.normal(0, 1, (H_ // 10 + 2, W_ // 10 + 2)).astype(np.float32), (W_, H_), interpolation=cv2.INTER_CUBIC)
    a = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.2) + nz * amt * 40
    return np.where(a > 127, 255, 0).astype(np.uint8)


def ink_cov(img, lo=70, hi=205):
    """Engraving luminance -> ink coverage 0..1 (a steep map: printed line, not a grey photo)."""
    g = np.asarray(img.convert("L"), np.float32)
    return np.clip((hi - g) / (hi - lo), 0, 1) ** 0.85


def piece(img, mask, cov=None):
    c = ink_cov(img) if cov is None else cov
    rgb = CARD * (1 - c[..., None]) + INKC * c[..., None]
    return np.dstack([rgb, mask]).astype(np.uint8)


def grabcut(a_rgb, init, iters=6):
    bg, fg = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    m = init.copy()
    cv2.grabCut(cv2.cvtColor(a_rgb, cv2.COLOR_RGB2BGR), m, None, bg, fg, iters, cv2.GC_INIT_WITH_MASK)
    return np.where((m == cv2.GC_FGD) | (m == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)


def stats(name, m, img_ink):
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    return {"piece": name, "components": int(n - 1), "area_px": int((m > 0).sum()),
            "ink_rejected_px": int(((img_ink > 0) & (m == 0)).sum())}


rig = {"pieces": {}, "mask_stats": [], "repairs": []}

# ---------------------------------------------------------------- LIL-START: glider + pilot, legs
lil = Image.open(os.path.join(SRC, "lilienthal_start.jpg")).convert("RGB")
a = np.asarray(lil); g = cv2.cvtColor(a, cv2.COLOR_RGB2GRAY)
ink = (g < 170).astype(np.uint8) * 255
solid = cv2.dilate(ink, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
solid = cv2.morphologyEx(solid, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
solid = fill_holes(solid, 5000)
init = np.full(g.shape, cv2.GC_BGD, np.uint8)
init[solid > 0] = cv2.GC_PR_FGD
# definite-foreground scribbles: wing spars, membranes, pilot, legs
fg_scr = np.zeros_like(g)
for pts in [[(30, 133), (200, 130), (360, 215)], [(330, 270), (720, 128)], [(330, 270), (940, 330)], [(650, 30), (715, 30), (700, 80)],
            [(400, 175), (410, 240)], [(385, 285), (378, 345)], [(408, 285), (410, 345)], [(360, 222), (480, 290)]]:
    cv2.polylines(fg_scr, [np.int32(pts)], False, 255, 5)
init[(fg_scr > 0) & (solid > 0)] = cv2.GC_FGD
# background scribbles: the engraved ground under the feet (not part of the puppet)
gnd = np.zeros_like(g)
cv2.fillPoly(gnd, [np.int32([(180, 312), (352, 300), (352, 372), (180, 390)])], 255)
cv2.fillPoly(gnd, [np.int32([(426, 330), (700, 300), (700, 399), (426, 399)])], 255)
cv2.fillPoly(gnd, [np.int32([(340, 362), (440, 362), (440, 399), (340, 399)])], 255)
init[gnd > 0] = cv2.GC_BGD
cut = grabcut(a, init)
cut = keep_seeded(cut, fg_scr)
cut = fill_holes(cv2.morphologyEx(cut, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)), 5000)
cut = scissor(cut, 1)
cut = keep_seeded(cut, fg_scr)
cv2.imwrite(os.path.join(OUT, "lil_fail_mask.png"), ((ink > 0) & (cut == 0)).astype(np.uint8) * 255)

HIP = (404, 271)  # hip pin, source px: waist just under the lower wing spar
legs_poly = np.int32([(352, 271), (428, 268), (437, 276), (446, 368), (342, 368), (346, 300)])
lp = np.zeros_like(g); cv2.fillPoly(lp, [legs_poly], 255)
cap = np.zeros_like(g); cv2.circle(cap, HIP, 15, 255, -1)  # joint overlap disc (blank card, hidden under the body)
legs_m = (cut & lp)
legs_m = keep_seeded(legs_m, fg_scr & lp)
legs_m = np.maximum(legs_m, cap & ~lp)
body_m = cut.copy(); body_m[lp > 0] = 0
body_m = keep_seeded(cv2.morphologyEx(body_m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)), fg_scr & ~lp)
cov = ink_cov(lil)
cov_legs = cov.copy(); cov_legs[(cap > 0) & (lp == 0)] = 0  # the cap is blank card
for name, m, cv_ in [("glider", body_m, cov), ("legs", legs_m, cov_legs)]:
    ys, xs = np.nonzero(m); x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    p = piece(lil, m, cv_)[y0:y1, x0:x1]
    Image.fromarray(p, "RGBA").save(os.path.join(OUT, name + ".png"))
    cv2.imwrite(os.path.join(OUT, name + "_mask.png"), m[y0:y1, x0:x1])
    rig["pieces"][name] = {"file": name + ".png", "source": "LIL-START", "offset_src": [int(x0), int(y0)],
                           "pivot": [HIP[0] - int(x0), HIP[1] - int(y0)]}
    rig["mask_stats"].append(stats(name, m, ink & (lp if name == "legs" else ~lp)))
rig["pieces"]["legs"]["parent"] = "glider"
rig["pieces"]["legs"]["parent_pivot"] = rig["pieces"]["glider"]["pivot"]
rig["pieces"]["legs"]["limits_deg"] = [-60, 40]
rig["repairs"].append("legs: joint cap (r=15 px blank card) added above the waist cut so the hip wedge never opens onto the panel")

# ---------------------------------------------------------------- CROW: Specht, Brehms Tierleben 1911 (pied crow; stands in for the magpie)
crow = Image.open(os.path.join(SRC, "crow_specht_960.png")).convert("RGB")
a = np.asarray(crow); g = cv2.cvtColor(a, cv2.COLOR_RGB2GRAY)
gm = np.full(a.shape[:2], cv2.GC_BGD, np.uint8); gm[95:600, 38:925] = cv2.GC_PR_BGD
dark = g < 60
gm[95:600, 38:925][dark[95:600, 38:925]] = cv2.GC_PR_FGD
gm[200:360, 300:600] = cv2.GC_FGD; gm[330:390, 540:700] = cv2.GC_PR_FGD
cv2.fillPoly(gm, [np.int32([(600, 140), (690, 108), (800, 150), (858, 228), (770, 262), (705, 330), (560, 392), (520, 372)])], cv2.GC_FGD)
cv2.fillPoly(gm, [np.int32([(760, 250), (880, 260), (915, 330), (890, 430), (850, 515), (820, 470), (760, 400)])], cv2.GC_FGD)
cv2.fillPoly(gm, [np.int32([(40, 470), (300, 440), (470, 445), (478, 610), (40, 610)])], cv2.GC_BGD)
cv2.fillPoly(gm, [np.int32([(640, 540), (930, 520), (930, 620), (640, 620)])], cv2.GC_BGD)
box = gm[395:530, 470:660]; box[g[395:530, 470:660] > 110] = cv2.GC_BGD
seed = (gm == cv2.GC_FGD).astype(np.uint8) * 255
cm = grabcut(a, gm)
cm = keep_seeded(cm, seed)
cm = fill_holes(cv2.morphologyEx(cm, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8)), 20000)
cm = keep_seeded(scissor(cm, 4), seed)
cv2.imwrite(os.path.join(OUT, "crow_fail_mask.png"), (dark & (cm == 0)).astype(np.uint8) * 255)
# the crow's dense black would read as a grey-black blot at film scale: print it with the engraving's own white
# lines kept (lighter threshold), so the plumage is line and mass, as in the wood engraving.
ccov = np.clip((185 - g.astype(np.float32)) / 130, 0, 1)
head_poly = np.int32([(712, 150), (960, 150), (960, 545), (805, 545), (765, 405), (700, 330)])
_lo = [(705, 215), (640, 300), (520, 370), (420, 420), (330, 500), (215, 560), (170, 540)]
_ser = []  # scissor-cut primaries along the trailing edge: a serrated handmade cut, not a straight slab edge
for (xa, ya), (xb, yb) in zip(_lo[:-1], _lo[1:]):
    for k in range(4):
        t0 = k / 4; t1 = (k + 0.5) / 4
        _ser.append((xa + (xb - xa) * t0, ya + (yb - ya) * t0))
        nx, ny = -(yb - ya), (xb - xa); L = (nx * nx + ny * ny) ** 0.5
        _ser.append((xa + (xb - xa) * t1 - nx / L * 22, ya + (yb - ya) * t1 - ny / L * 22))
wing_poly = np.int32([(268, 250), (420, 150), (560, 118), (660, 130)] + _ser + [(170, 540), (230, 430), (262, 330)])
hp = np.zeros_like(g); cv2.fillPoly(hp, [head_poly], 255)
wp = np.zeros_like(g); cv2.fillPoly(wp, [wing_poly], 255)
NECK, SHOULDER = (735, 300), (640, 190)
parts = {"crow_head": cm & hp, "crow_body": cm & ~hp, "crow_wing": cm & wp & ~hp}
for name, m in parts.items():
    m = keep_seeded(m, m if name != "crow_body" else seed & ~hp)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    m = np.where(lab == 1 + int(np.argmax(st[1:, 4])), 255, 0).astype(np.uint8)
    ys, xs = np.nonzero(m); x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    p = piece(crow, m, ccov)[y0:y1, x0:x1]
    Image.fromarray(p, "RGBA").save(os.path.join(OUT, name + ".png"))
    cv2.imwrite(os.path.join(OUT, name + "_mask.png"), m[y0:y1, x0:x1])
    pv = {"crow_head": NECK, "crow_body": NECK, "crow_wing": SHOULDER}[name]
    rig["pieces"][name] = {"file": name + ".png", "source": "CROW", "offset_src": [int(x0), int(y0)], "pivot": [pv[0] - int(x0), pv[1] - int(y0)]}
    rig["mask_stats"].append(stats(name, m, (dark.astype(np.uint8) * 255) & m))
b0 = rig["pieces"]["crow_body"]["offset_src"]
rig["pieces"]["crow_head"].update(parent="crow_body", parent_pivot=[NECK[0] - b0[0], NECK[1] - b0[1]], limits_deg=[-35, 70])
rig["pieces"]["crow_wing"].update(parent="crow_body", parent_pivot=[SHOULDER[0] - b0[0], SHOULDER[1] - b0[1]], limits_deg=[-25, 95])
rig["repairs"].append("crow_wing: the folded wing is cut out as its own piece and re-pinned at the shoulder (flying pose built from the "
                      "perched engraving, Reiniger replacement practice); the body keeps its own folded wing as the far wing")
json.dump(rig, open(os.path.join(OUT, "rig.json"), "w"), indent=1)
print(json.dumps(rig["mask_stats"], indent=1))

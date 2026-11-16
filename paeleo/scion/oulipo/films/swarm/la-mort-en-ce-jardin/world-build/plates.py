# plates.py -- U1 world unit: SCION #29 GrabCut cutouts + one monotone neutral curve per plate (p2/p98 -> L35/220).
# Usage: python3 -I plates.py <world dir>   (reads <world>/plates/*.jpg and ../test-shot/plates/*.jpg; writes <world>/cut/)
# Every plate: GrabCut on the source COLOUR (colour separates brown root from green leaf; it is then discarded),
# seeds from hue/luma keys + scribble polygons, cleanup that removes background islands (components not touching the
# main piece and smaller than a floor) while KEEPING interior holes larger than a pinna gap (fern gaps stay open).
# Output piece = neutral luminance (Rec.601) through one monotone curve, RGBA, plus *_fail.png (probable-background
# pixels inside the rect = the doubt map) and cut.json (source, crop in source px, curve, seeds, component counts).
import sys, json, os
import numpy as np, cv2
from PIL import Image

WORLD = sys.argv[1]
PL = f"{WORLD}/plates"; OLD = f"{WORLD}/../test-shot/plates"; OUT = f"{WORLD}/cut"
os.makedirs(OUT, exist_ok=True)
LOG = {}


def load(path):
    rgb = np.asarray(Image.open(path).convert("RGB"), np.float32)
    return rgb, rgb @ np.float32([0.299, 0.587, 0.114])


def curve(L, mask=None, lo=35, hi=220):
    v = L[mask > 127] if mask is not None and (mask > 127).sum() > 500 else L
    p2, p98 = np.percentile(v, 2), np.percentile(v, 98)
    return np.clip(lo + (L - p2) * (hi - lo) / max(p98 - p2, 1), 0, 255), [round(float(p2), 1), round(float(p98), 1)]


def gc(rgb, m, iters=6):
    img = cv2.cvtColor(np.clip(rgb, 0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR)
    m = m.copy(); bgm, fgm = np.zeros((1, 65)), np.zeros((1, 65))
    cv2.grabCut(img, m, None, bgm, fgm, iters, cv2.GC_INIT_WITH_MASK)
    return np.where((m == 1) | (m == 3), 255, 0).astype(np.uint8), np.where(m == 2, 255, 0).astype(np.uint8)


def cleanup(fg, island_floor=0.02, hole_fill=120, open_px=0):
    """Keep the main component and any component >= island_floor of it; fill only holes < hole_fill px (pinnae gaps kept)."""
    if open_px: fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((open_px, open_px), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(fg, connectivity=8)
    if n <= 1: return fg, dict(components_before=0, kept=0)
    areas = st[1:, 4]; big = areas.max()
    keep = [k + 1 for k, a in enumerate(areas) if a >= island_floor * big]
    m = np.isin(lab, keep).astype(np.uint8) * 255
    inv = 255 - m; n2, lab2, st2, _ = cv2.connectedComponentsWithStats(inv, connectivity=4)
    filled = 0
    for k in range(1, n2):
        if st2[k, 4] < hole_fill: m[lab2 == k] = 255; filled += 1
    return m, dict(components_before=int(n - 1), kept=len(keep), islands_removed=int(n - 1 - len(keep)), small_holes_filled=filled)


def matte(m, feather=0.8):
    m = cv2.erode(m, np.ones((2, 2), np.uint8))          # pull the edge 1 px inside: kills the source-background halo
    return cv2.GaussianBlur(m.astype(np.float32), (0, 0), feather)


def save(name, L, alpha, fail, info, crop=None):
    if crop is not None:
        x0, y0, x1, y1 = crop; L = L[y0:y1, x0:x1]; alpha = alpha[y0:y1, x0:x1]; fail = fail[y0:y1, x0:x1]
    else: crop = (0, 0, L.shape[1], L.shape[0])
    ys, xs = np.nonzero(alpha > 8)
    b = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    rgba = np.dstack([L, L, L, alpha])[b[1]:b[3], b[0]:b[2]]
    Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), "RGBA").save(f"{OUT}/{name}.png")
    cv2.imwrite(f"{OUT}/{name}_fail.png", fail[b[1]:b[3], b[0]:b[2]])
    info["crop_in_source"] = [crop[0] + b[0], crop[1] + b[1], crop[0] + b[2], crop[1] + b[3]]
    info["size"] = [int(b[2] - b[0]), int(b[3] - b[1])]
    info["alpha_cover"] = round(float((alpha[b[1]:b[3], b[0]:b[2]] > 127).mean()), 3)
    LOG[name] = info
    print(name, info)


def poly(m, pts, val, W, H):
    cv2.fillPoly(m, [np.int32([(x * W, y * H) for x, y in pts])], val)


# ---------- P0 far wall: 'Huge Buttress roots' (CC BY 2.0), whole plate (back of the box, no cut) ----------
rgb, L = load(f"{OLD}/Huge_Buttress_roots_28115225997_jpg.jpg")
G, pp = curve(L)
save("P0_far", G, np.full(L.shape, 255, np.float32), np.zeros(L.shape, np.uint8), dict(source="Huge Buttress roots (28115225997)", curve_p2_p98=pp, cut="none (back plate)"))

# ---------- P1 mid: Ficus root mass (CC BY-SA 2.0). Brown root vs green leaf: hue key seeds GrabCut ----------
rgb, L = load(f"{PL}/Fig_Tree_Buttress_Roots_Ficus_sp_8727707129_jpg.jpg")
H, W = L.shape
r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
hsv = cv2.cvtColor(rgb.astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
brown = (r > g * 1.02) & (r > b * 1.12)
green = (g > r * 1.06) & (g > b)
m = np.full((H, W), cv2.GC_PR_BGD, np.uint8)
poly(m, [(.18, 0), (.78, 0), (.78, .62), (.95, .80), (.95, 1), (.30, 1), (.30, .55), (.18, .30)], cv2.GC_PR_FGD, W, H)
m[(m == cv2.GC_PR_FGD) & green & (hsv[..., 1] > 70)] = cv2.GC_PR_BGD
m[cv2.erode((brown & (L > 60)).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0] = cv2.GC_PR_FGD
poly(m, [(.50, .02), (.56, .02), (.56, .40), (.50, .40)], cv2.GC_FGD, W, H)                      # trunk core
poly(m, [(.42, .25), (.62, .25), (.62, .55), (.42, .55)], cv2.GC_FGD, W, H)                      # central root curtain
poly(m, [(.80, 0), (1, 0), (1, .40), (.80, .25)], cv2.GC_BGD, W, H)                              # lit foliage, right
poly(m, [(0, 0), (.14, 0), (.14, .55), (0, .55)], cv2.GC_BGD, W, H)                              # palm fronds, left
poly(m, [(0, .80), (.25, .80), (.25, 1), (0, 1)], cv2.GC_BGD, W, H)                              # leaf litter
poly(m, [(0, .45), (.30, .45), (.30, .62), (.27, .80), (0, .80)], cv2.GC_BGD, W, H)                # litter block, left
fg, fail = gc(rgb, m, 6)
fg, ci = cleanup(fg, island_floor=0.03, hole_fill=600)
G, pp = curve(L, fg)
save("P1_ficus_roots", G, matte(fg), fail, dict(source="Fig Tree Buttress Roots (Ficus sp.) (8727707129)", curve_p2_p98=pp,
     seeds="hue key (brown=probable fg, saturated green=probable bg) + trunk/curtain fg + foliage/litter bg polygons", **ci))

# ---------- P4 foreground root diagonal: the Ficus lower-right root run, cut separately (mirrored at placement) ----
m = np.full((H, W), cv2.GC_BGD, np.uint8)
poly(m, [(.55, .72), (.70, .74), (1, .86), (1, 1), (.62, 1), (.52, .86)], cv2.GC_PR_BGD, W, H)
sub = (m == cv2.GC_PR_BGD)
m[sub & brown] = cv2.GC_PR_FGD
m[sub & green & (hsv[..., 1] > 60)] = cv2.GC_PR_BGD
poly(m, [(.66, .80), (.80, .84), (.80, .86), (.66, .83)], cv2.GC_FGD, W, H)
fg, fail = gc(rgb, m, 6)
fg, ci = cleanup(fg, island_floor=0.05, hole_fill=300)
G, pp = curve(L, fg)
save("P4_root_diag", G, matte(fg, 1.0), fail, dict(source="Fig Tree Buttress Roots (Ficus sp.) (8727707129)", curve_p2_p98=pp,
     seeds="lower-right root run: brown key inside a hand polygon", **ci), crop=(int(.50 * W), int(.70 * H), W, H))

# ---------- P1b: 'Buttress Roots 1' flange (CC BY-SA 4.0), recut from the test-shot rect (reuse, verified) ----------
rgb, L = load(f"{OLD}/Buttress_Roots_1_jpg.jpg")
H, W = L.shape
m = np.zeros((H, W), np.uint8); m[int(H * .08):int(H * .99), 0:int(W * .99)] = cv2.GC_PR_FGD
poly(m, [(0, 0), (1, 0), (1, .12), (0, .16)], cv2.GC_BGD, W, H)
poly(m, [(.40, .62), (.47, .58), (.50, .99), (.40, .99)], cv2.GC_BGD, W, H)
poly(m, [(0, .55), (.12, .62), (.25, .99), (0, .99)], cv2.GC_BGD, W, H)
poly(m, [(.44, .20), (.52, .18), (.58, .70), (.52, .80)], cv2.GC_FGD, W, H)
poly(m, [(.65, .45), (.95, .55), (.95, .75), (.70, .62)], cv2.GC_FGD, W, H)
fg, fail = gc(rgb, m, 6)
fg, ci = cleanup(fg, island_floor=0.2, hole_fill=800)
G, pp = curve(L, fg)
save("P1b_flange", G, matte(fg), fail, dict(source="Buttress Roots 1", curve_p2_p98=pp, seeds="rect + wall/soil bg + flange fg polygons (test-shot r2 seeds)", **ci))

# ---------- P3 near: Cyathea dregei tree fern (PD), the round crown at right; pinnae gaps kept ----------
rgb, L = load(f"{PL}/Cyathea_dregei_Common_Tree_Fern_Cape_Town_jpg.jpg")
H, W = L.shape
Lb = cv2.GaussianBlur(L, (0, 0), 1.5)
m = np.full((H, W), cv2.GC_BGD, np.uint8)
poly(m, [(.60, .24), (.78, .20), (.95, .30), (.95, .58), (.80, .60), (.62, .55)], cv2.GC_PR_BGD, W, H)
inside = m == cv2.GC_PR_BGD
m[inside & (Lb > np.percentile(L[inside], 45))] = cv2.GC_PR_FGD               # the lit fronds are lighter than the shade behind
poly(m, [(.72, .40), (.86, .38), (.88, .50), (.74, .52)], cv2.GC_FGD, W, H)
fg, fail = gc(rgb, m, 5)
fg, ci = cleanup(fg, island_floor=0.004, hole_fill=40)
G, pp = curve(L, fg)
save("P3_treefern", G, matte(fg, 0.6), fail, dict(source="Cyathea dregei - Common Tree Fern - Cape Town", curve_p2_p98=pp,
     seeds="crown polygon; luma > p45 inside = probable fg; core fg; hole_fill 40 px only (pinna gaps open)", **ci))

# ---------- P3b: the left Cyathea crowns (big fern mass for the close shots' right edge) ----------
m = np.full((H, W), cv2.GC_BGD, np.uint8)
poly(m, [(.05, .14), (.35, .12), (.60, .14), (.62, .40), (.45, .58), (.12, .56), (.04, .40)], cv2.GC_PR_BGD, W, H)
inside = m == cv2.GC_PR_BGD
m[inside & (Lb > np.percentile(L[inside], 40))] = cv2.GC_PR_FGD
poly(m, [(.20, .28), (.40, .24), (.44, .34), (.24, .38)], cv2.GC_FGD, W, H)
fg, fail = gc(rgb, m, 5)
fg, ci = cleanup(fg, island_floor=0.004, hole_fill=40)
G, pp = curve(L, fg)
save("P3b_treefern_mass", G, matte(fg, 0.6), fail, dict(source="Cyathea dregei - Common Tree Fern - Cape Town", curve_p2_p98=pp, seeds="left crowns polygon + luma key", **ci))

# ---------- P3c: Colocasia heart leaves (CC BY-SA 4.0) and P3d Melba Gully fern (CC BY-SA 4.0): test-shot cuts reused ----
for nm, src in (("P3c_leaves", "P3_leaves"), ("P3d_fern_bw", "P4_fern")):
    a = np.asarray(Image.open(f"{WORLD}/../test-shot/cut/{src}.png").convert("RGBA"), np.float32)
    if nm == "P3d_fern_bw":   # the test shot's dark-pinnae key + edge taper (shot.py r2), baked into the piece here
        k = a[..., 3] * np.clip((140 - cv2.GaussianBlur(a[..., 0], (0, 0), 1.5)) / 35, 0, 1)
        hF, wF = k.shape; yy, xx = np.mgrid[0:hF, 0:wF]
        k *= np.clip(np.minimum(np.minimum(xx, wF - xx), np.minimum(yy, hF - yy)) / 90.0, 0, 1); a[..., 3] = k
    Image.fromarray(a.astype(np.uint8), "RGBA").save(f"{OUT}/{nm}.png")
    LOG[nm] = dict(source=f"test-shot r2 cut {src}.png (plates.py r2, GrabCut)", reused=True, size=[a.shape[1], a.shape[0]])

# ---------- water plates: Mekong flood (CC BY-SA 4.0) lower band, Cyathea pond band (PD); no cut, graded ----------
rgb, L = load(f"{PL}/Flooded_banks_in_the_muddy_water_of_the_Mekong_with_a_boy_ro.jpg")
H, W = L.shape
band = L[int(H * .80):H, 0:W]
G, pp = curve(band)
save("W_flood_mekong", G, np.full(band.shape, 255, np.float32), np.zeros(band.shape, np.uint8),
     dict(source="Flooded banks in the muddy water of the Mekong ... Don Khon, Laos", curve_p2_p98=pp, cut="water band y 80-100 %, no people or boats"),
     crop=None)
LOG["W_flood_mekong"]["crop_in_source"] = [0, int(H * .80), W, H]
rgb, L = load(f"{PL}/Cyathea_dregei_Common_Tree_Fern_Cape_Town_jpg.jpg")
H, W = L.shape
band = L[int(H * .82):H, int(W * .05):W]
G, pp = curve(band)
save("W_pond_cyathea", G, np.full(band.shape, 255, np.float32), np.zeros(band.shape, np.uint8),
     dict(source="Cyathea dregei - Common Tree Fern - Cape Town", curve_p2_p98=pp, cut="pond band y 82-100 % (reflections of the ferns)"))
LOG["W_pond_cyathea"]["crop_in_source"] = [int(W * .05), int(H * .82), W, H]

# BANKS_HOOK
# ---------- liana: 'Ginat Liana hanging on giant trees in Sinharaja' (CC BY-SA 4.0): the dark twisting liana, and the left forest as P0b ----
p = f"{PL}/Ginat_Liana_hanging_on_giant_trees_in_Sinharaja_Rain_forest_.jpg"
if os.path.exists(p):
    rgb, L = load(p); H, W = L.shape
    Lb = cv2.GaussianBlur(L, (0, 0), 1.2)
    m = np.full((H, W), cv2.GC_BGD, np.uint8)
    poly(m, [(.33, 0), (.40, 0), (.47, .20), (.56, .40), (.66, .62), (.66, .72), (.60, .70), (.50, .52), (.44, .38), (.35, .20)], cv2.GC_PR_BGD, W, H)
    inside = m == cv2.GC_PR_BGD
    m[inside & (Lb < 70)] = cv2.GC_PR_FGD
    m[inside & (Lb < 40)] = cv2.GC_FGD
    fg, fail = gc(rgb, m, 5)
    fg, ci = cleanup(fg, island_floor=0.08, hole_fill=200)
    G, pp = curve(L, fg)
    save("P1d_liana", G, matte(fg, 0.7), fail, dict(source="Ginat Liana hanging on giant trees in Sinharaja Rain forest of Sri Lanka", curve_p2_p98=pp,
         seeds="hand polygon along the liana; luma < 70 probable fg, < 40 fg", **ci))
    x1 = int(W * .78); band = L[:, :x1]
    G, pp = curve(band)
    save("P0b_forest", G, np.full(band.shape, 255, np.float32), np.zeros(band.shape, np.uint8),
         dict(source="Ginat Liana hanging on giant trees in Sinharaja Rain forest of Sri Lanka", curve_p2_p98=pp, cut="left 78 % (excludes the walkers at right), no cut"))
    LOG["P0b_forest"]["crop_in_source"] = [0, 0, x1, H]

# ---------- bank surface fallback/companion: Ficus plate bottom (real soil, litter and root bases), uncut ----------
rgb, L = load(f"{PL}/Fig_Tree_Buttress_Roots_Ficus_sp_8727707129_jpg.jpg")
H, W = L.shape
band = L[int(H * .78):H, :]
G, pp = curve(band)
save("B_litter_ficus", G, np.full(band.shape, 255, np.float32), np.zeros(band.shape, np.uint8),
     dict(source="Fig Tree Buttress Roots (Ficus sp.) (8727707129)", curve_p2_p98=pp, cut="soil/litter/root-base band y 78-100 %"))
LOG["B_litter_ficus"]["crop_in_source"] = [0, int(H * .78), W, H]
# ---------- flood: 'Flooded building and tree trunk ... Mekong' (CC BY-SA 4.0): water band + the fluted trunk standing in it ----
rgb, L = load(f"{PL}/Flooded_building_and_tree_trunk_in_the_muddy_water_of_the_Me.jpg")
H, W = L.shape
y0 = int(H * .80); band = L[y0:H, :]
G, pp = curve(band)
save("W_flood_trunk", G, np.full(band.shape, 255, np.float32), np.zeros(band.shape, np.uint8),
     dict(source="Flooded building and tree trunk in the muddy water of the Mekong in Si Phan Don, Laos, September 2019", curve_p2_p98=pp, cut="flood-water band y 80-100 %"))
LOG["W_flood_trunk"]["crop_in_source"] = [0, y0, W, H]
m = np.full((H, W), cv2.GC_BGD, np.uint8)
poly(m, [(.10, .25), (.26, .22), (.34, .38), (.40, .70), (.40, .78), (.10, .78), (.12, .60)], cv2.GC_PR_BGD, W, H)
inside = m == cv2.GC_PR_BGD
m[inside & (cv2.GaussianBlur(L, (0, 0), 2) < 150)] = cv2.GC_PR_FGD
poly(m, [(.24, .40), (.30, .40), (.32, .70), (.20, .72)], cv2.GC_FGD, W, H)
poly(m, [(.36, .36), (.45, .36), (.45, .66), (.37, .66)], cv2.GC_BGD, W, H)                      # bright water/wall right of trunk
fg, fail = gc(rgb, m, 6)
fg, ci = cleanup(fg, island_floor=0.05, hole_fill=500)
G, pp = curve(L, fg)
save("P1c_flood_trunk", G, matte(fg), fail, dict(source="Flooded building and tree trunk in the muddy water of the Mekong in Si Phan Don, Laos, September 2019",
     curve_p2_p98=pp, seeds="trunk polygon; luma < 150 probable fg; core fg; bright water bg", **ci))
json.dump(LOG, open(f"{OUT}/cut.json", "w"), indent=1)

# plates.py -- SCION #29 GrabCut cutout extraction for the test shot's multiplane planes.
# Usage: python3 -I plates.py <plates dir> <out dir> <shoe jpg>
# Every plate: neutral luminance conversion (Rec.601), one monotone curve p2/p98 -> L35/220,
# then cv2.grabCut (rect + seed scribbles), largest-component + hole fill, alpha cleanup (erode 1 px, feather).
# Writes RGBA PNGs, the GrabCut failure masks (probable-bg pixels inside the rect) and cut.json (transforms).
import sys, json, os
import numpy as np, cv2
from PIL import Image

SRC, OUT, SHOE = sys.argv[1:4]
os.makedirs(OUT, exist_ok=True)


def lum(path):
    a = np.asarray(Image.open(path).convert("RGB"), np.float32)
    return 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2], a


def curve(L, lo=35, hi=220, mask=None):
    v = L[mask > 0] if mask is not None else L
    p2, p98 = np.percentile(v, 2), np.percentile(v, 98)
    return np.clip(lo + (L - p2) * (hi - lo) / max(p98 - p2, 1), 0, 255), (float(p2), float(p98))


def grabcut(rgb, rect, fg=(), bg=(), iters=6):
    """rect=(x,y,w,h); fg/bg are lists of polygons (seed scribbles) in source pixels."""
    img = cv2.cvtColor(rgb.astype(np.uint8), cv2.COLOR_RGB2BGR)
    m = np.zeros(img.shape[:2], np.uint8)
    x, y, w, h = rect
    m[y:y + h, x:x + w] = cv2.GC_PR_FGD
    for p in bg: cv2.fillPoly(m, [np.int32(p)], cv2.GC_BGD)
    for p in fg: cv2.fillPoly(m, [np.int32(p)], cv2.GC_FGD)
    bgm, fgm = np.zeros((1, 65)), np.zeros((1, 65))
    cv2.grabCut(img, m, None, bgm, fgm, iters, cv2.GC_INIT_WITH_MASK)
    fgmask = np.where((m == 1) | (m == 3), 255, 0).astype(np.uint8)
    fail = np.where(m == 2, 255, 0).astype(np.uint8)          # probable-bg inside rect: failure / doubt mask
    return fgmask, fail


def cleanup(mask, keep=1, min_area=800, close=5):
    """No background islands: keep the `keep` largest components, fill holes smaller than min_area."""
    n, lab, st, _ = cv2.connectedComponentsWithStats(mask)
    order = np.argsort(-st[1:, 4])[:keep] + 1
    m = np.isin(lab, order).astype(np.uint8) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((close, close), np.uint8))
    inv = 255 - m
    n, lab, st, _ = cv2.connectedComponentsWithStats(inv)
    for k in range(1, n):
        if st[k, 4] < min_area: m[lab == k] = 255
    m = cv2.erode(m, np.ones((3, 3), np.uint8))
    return cv2.GaussianBlur(m, (0, 0), 1.0), int(n)


log = {}


def save(name, L, alpha, info):
    rgba = np.dstack([L, L, L, alpha]).astype(np.uint8)
    ys, xs = np.nonzero(alpha > 8)
    box = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1) if len(xs) else (0, 0, L.shape[1], L.shape[0])
    Image.fromarray(rgba[box[1]:box[3], box[0]:box[2]], "RGBA").save(f"{OUT}/{name}.png")
    info["crop_in_source"] = box
    log[name] = info


# P0 far wall + buttress trunk: the whole plate (no cut; it is the back of the box)
L, rgb = lum(f"{SRC}/Huge_Buttress_roots_28115225997_jpg.jpg")
G, pp = curve(L)
save("P0_far", G, np.full(L.shape, 255, np.uint8), dict(source="Huge_Buttress_roots_28115225997", curve_p2_p98=pp, cut="none (back plate)"))

# P1 mid: the left buttress flange of the same tree class from 'Buttress Roots 1' (Mokkie) -> sinuous root wall
L, rgb = lum(f"{SRC}/Buttress_Roots_1_jpg.jpg")
H, W = L.shape
rect = (0, int(H * .08), int(W * .99), int(H * .91))
bg = [[(0, 0), (W, 0), (W, int(H * .12)), (0, int(H * .16))],                      # the wall behind
      [(int(W * .40), int(H * .62)), (int(W * .47), int(H * .58)), (int(W * .50), int(H * .99)), (int(W * .40), int(H * .99))],
      [(0, int(H * .55)), (int(W * .12), int(H * .62)), (int(W * .25), int(H * .99)), (0, int(H * .99))]]  # soil
fg = [[(int(W * .44), int(H * .20)), (int(W * .52), int(H * .18)), (int(W * .58), int(H * .70)), (int(W * .52), int(H * .80))],
      [(int(W * .65), int(H * .45)), (int(W * .95), int(H * .55)), (int(W * .95), int(H * .75)), (int(W * .70), int(H * .62))],
      [(int(W * .05), int(H * .38)), (int(W * .35), int(H * .26)), (int(W * .38), int(H * .32)), (int(W * .08), int(H * .45))]]
m, fail = grabcut(rgb, rect, fg, bg)
m, nc = cleanup(m, keep=1)
G, pp = curve(L, mask=m)
save("P1_flange", G, m, dict(source="Buttress_Roots_1", curve_p2_p98=pp, rect=rect, components_before=nc))
cv2.imwrite(f"{OUT}/P1_flange_fail.png", fail)

# P3 near: Colocasia heart leaves (exclude the rose and the stone)
L, rgb = lum(f"{SRC}/Colocasia_esculenta_leaves_jpg.jpg")
H, W = L.shape
rect = (0, 0, int(W * .97), int(H * .92))
bg = [[(int(W * .70), 0), (W, 0), (W, int(H * .30)), (int(W * .78), int(H * .25))],          # rose
      [(0, int(H * .82)), (int(W * .40), int(H * .86)), (int(W * .40), H), (0, H)]]             # stone
fg = [[(int(W * .10), int(H * .15)), (int(W * .30), int(H * .10)), (int(W * .32), int(H * .55)), (int(W * .14), int(H * .60))],
      [(int(W * .55), int(H * .45)), (int(W * .80), int(H * .42)), (int(W * .82), int(H * .75)), (int(W * .60), int(H * .80))]]
m, fail = grabcut(rgb, rect, fg, bg)
m, nc = cleanup(m, keep=2)
G, pp = curve(L, mask=m)
save("P3_leaves", G, m, dict(source="Colocasia_esculenta_leaves", curve_p2_p98=pp, rect=rect, components_before=nc))
cv2.imwrite(f"{OUT}/P3_leaves_fail.png", fail)

# P4 foreground: tree-fern fronds and crozier (already b/w) cut from the light leaves behind them
L, rgb = lum(f"{SRC}/Lavers_Hill_AU_Melba_Gully_State_Park_2019_1133_bw_jpg.jpg")
H, W = L.shape
rect = (0, 0, W, H)
Lb = cv2.GaussianBlur(L, (0, 0), 2)
sd = np.sqrt(np.maximum(cv2.GaussianBlur(L * L, (0, 0), 6) - cv2.GaussianBlur(L, (0, 0), 6) ** 2, 0))
m = np.full(L.shape, cv2.GC_PR_BGD, np.uint8)
m[Lb < 90] = cv2.GC_PR_FGD                      # dark pinnae: probable fern
m[Lb < 45] = cv2.GC_FGD                         # deepest pinnae: certain fern
m[(Lb > 135) & (sd < 14)] = cv2.GC_BGD          # smooth light leaves behind: certain background
cv2.ellipse(m, (int(W * .39), int(H * .43)), (int(W * .10), int(H * .15)), 0, 0, 360, cv2.GC_FGD, -1)  # crozier
cv2.line(m, (int(W * .40), int(H * .60)), (int(W * .33), int(H * .98)), cv2.GC_FGD, 26)                 # its stem
bgm, fgm = np.zeros((1, 65)), np.zeros((1, 65))
cv2.grabCut(cv2.cvtColor(rgb.astype(np.uint8), cv2.COLOR_RGB2BGR), m, None, bgm, fgm, 5, cv2.GC_INIT_WITH_MASK)
fm = np.where((m == 1) | (m == 3), 255, 0).astype(np.uint8)
fail = np.where(m == 2, 255, 0).astype(np.uint8)
fm, nc = cleanup(fm, keep=6, min_area=60, close=3)
G, pp = curve(L, mask=fm)
save("P4_fern", G, fm, dict(source="Lavers_Hill_Melba_Gully_1133_bw", curve_p2_p98=pp, init="luma<95 probable fg + crozier seeds", components_before=nc))
cv2.imwrite(f"{OUT}/P4_fern_fail.png", fail)

# the shoe: LACMA 51.47.2a-b, right shoe of the pair, cut; satin kept as photographed except the plate curve
L, rgb = lum(SHOE)
H, W = L.shape
rect = (int(W * .30), int(H * .30), int(W * .62), int(H * .64))
sb = [[(int(W*.28), int(H*.80)), (int(W*.50), int(H*.88)), (int(W*.62), int(H*.95)), (int(W*.28), int(H*.95))]]
m, fail = grabcut(rgb, rect, bg=sb, iters=8)
m, nc = cleanup(m, keep=1)
G, pp = curve(L, lo=60, hi=232, mask=m)        # the one white object: its satin peaks above the jungle's L220
save("shoe", G, m, dict(source="LACMA 51.47.2a-b", curve_p2_p98=pp, rect=rect, components_before=nc))
cv2.imwrite(f"{OUT}/shoe_fail.png", fail)

json.dump(log, open(f"{OUT}/cut.json", "w"), indent=1)
print(json.dumps(log, indent=1))

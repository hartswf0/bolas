# SCION #29 GrabCut: cut one shoe from a LACMA museum photograph (neutral grey ground).
# usage: python3 -I cut_shoe.py <src.jpg> <out_prefix> <x0 y0 x1 y1 as fractions of width/height>
# Seeds: rect box; definite background = neutral low-chroma pixels outside a 2 px band of warm pixels (the
# grey ground and the shoe's own cast shadow are neutral; the satin, kid leather and brown sole are warm);
# definite foreground = strongly warm pixels. Graph cut (5 iterations), then alpha cleanup: largest component,
# no background islands, holes kept where they are ground (arch under the shoe), 1 px erosion, edge colour
# decontamination (edge pixels take the colour of the nearest interior pixel), 0.8 px feather.
import sys, json, numpy as np, cv2
src, out = sys.argv[1], sys.argv[2]
FILL_ALL = '--fill-holes' in sys.argv; sys.argv = [a for a in sys.argv if a != '--fill-holes']
fx0, fy0, fx1, fy1 = map(float, sys.argv[3:7])
I = cv2.imread(src); H, W = I.shape[:2]
x0, y0, x1, y1 = int(fx0 * W), int(fy0 * H), int(fx1 * W), int(fy1 * H)
lab = cv2.cvtColor(I, cv2.COLOR_BGR2LAB).astype(np.float32)
a, b = lab[..., 1] - 128, lab[..., 2] - 128
chroma = np.hypot(a, b); warm = b
# ground reference: median chroma at the image border
bord = np.concatenate([chroma[:8].ravel(), chroma[-8:].ravel(), chroma[:, :8].ravel(), chroma[:, -8:].ravel()])
g = float(np.median(bord))
mask = np.full((H, W), cv2.GC_BGD, np.uint8)
mask[y0:y1, x0:x1] = cv2.GC_PR_BGD
inside = np.zeros((H, W), bool); inside[y0:y1, x0:x1] = True
fgw = (warm > g + 9) & inside
mask[(warm > g + 5) & inside] = cv2.GC_PR_FGD
mask[cv2.erode(fgw.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0] = cv2.GC_FGD
near = cv2.dilate((warm > g + 4).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
mask[(warm < g + 2.0) & ~near & inside] = cv2.GC_BGD
bgm, fgm = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
cv2.grabCut(I, mask, None, bgm, fgm, 5, cv2.GC_INIT_WITH_MASK)
m = np.isin(mask, (cv2.GC_FGD, cv2.GC_PR_FGD)).astype(np.uint8)
m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
# the dark brown sole edge and heel top-lift: dark warm pixels adjacent to the cut (the shadow is neutral grey)
L = lab[..., 0]
sole = (L < 120) & ((b > g + 3) | (a > g + 2)) & inside
for _ in range(6):
    grow = sole & (cv2.dilate(m, np.ones((5, 5), np.uint8)) > 0) & (m == 0)
    if not grow.any(): break
    m[grow] = 1
m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
n, lb, st, _ = cv2.connectedComponentsWithStats(m, 8)
comps_before = int(n - 1)
k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA])); m = (lb == k).astype(np.uint8)
# fill holes smaller than 0.2 % of the shoe (speckle), keep large ones (ground seen through the arch)
inv = 1 - m; n2, lb2, st2, _ = cv2.connectedComponentsWithStats(inv, 4)
area = m.sum(); filled = 0
for j in range(1, n2):
    touches = lb2[0, :].tolist().count(j) or lb2[-1, :].tolist().count(j) or lb2[:, 0].tolist().count(j) or lb2[:, -1].tolist().count(j)
    if st2[j, cv2.CC_STAT_AREA] < 0.002 * area or (FILL_ALL and not touches): m[lb2 == j] = 1; filled += 1
fail = I.copy()
m_er = cv2.erode(m, np.ones((3, 3), np.uint8))
# decontaminate: edge band takes colour from the interior (inpaint the 3 px band from inside)
band = (cv2.dilate(m, np.ones((3, 3), np.uint8)) - cv2.erode(m, np.ones((7, 7), np.uint8))) > 0
clean = cv2.inpaint(I, band.astype(np.uint8) * 255, 3, cv2.INPAINT_TELEA)
alpha = cv2.GaussianBlur(m_er.astype(np.float32), (0, 0), 0.8)
ys, xs = np.where(m_er > 0); bx0, by0, bx1, by1 = xs.min() - 4, ys.min() - 4, xs.max() + 5, ys.max() + 5
rgba = np.dstack([clean, (alpha * 255).astype(np.uint8)])[by0:by1, bx0:bx1]
cv2.imwrite(out + "_rgba_raw.png", rgba)
# failure / diagnostic masks: red = removed warm pixels, blue = kept neutral pixels (possible halo)
rem = ((warm > g + 9) | sole) & (m_er == 0) & inside; halo = (m_er > 0) & (warm < g + 2)
fail[rem] = (0, 0, 255); fail[halo] = (255, 0, 0)
cv2.rectangle(fail, (x0, y0), (x1, y1), (0, 255, 0), 2)
cv2.imwrite(out + "_fail.png", fail[max(0, by0 - 40):by1 + 40, max(0, bx0 - 40):bx1 + 40])
json.dump(dict(src=src, size=[W, H], rect=[x0, y0, x1, y1], ground_chroma=g, components_before=comps_before,
               holes_filled=filled, kept_holes=int(n2 - 1 - filled), crop_in_source=[int(bx0), int(by0), int(bx1), int(by1)],
               removed_warm_px=int(rem.sum()), kept_neutral_px=int(halo.sum()), area_px=int(m_er.sum())),
          open(out + "_cut.json", "w"), indent=1)
print(open(out + "_cut.json").read())

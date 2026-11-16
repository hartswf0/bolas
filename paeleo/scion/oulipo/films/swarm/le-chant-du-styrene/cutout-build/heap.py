"""Sh5: GrabCut the real heap of orange plastic granules out of 'Granuls orange.jpg' (Lobkovs, CC BY-SA 3.0) onto black.
Seeds: rectangle around the heap + hue (orange, saturated = FG; grey steel, unsaturated = sure BG).
The granules keep their real colour (no substitution). Light: a warm key from the top-left by a per-pixel
gain on the photograph's own luminance (thin edges and the top of the heap catch the light, the base falls to black)."""
import cv2, numpy as np, json
from pathlib import Path
OUT = Path("/home/user/bolas/paeleo/scion/oulipo/films/sources/le-chant-du-styrene/cutout-puppetry-camera-unit-a-sh1-sh2a-sh2b-sh5-heap-")
img = cv2.imread(str(OUT / "heap/granuls_orange_1920.jpg"))
H, W = img.shape[:2]
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV); h, s, v = [hsv[..., i].astype(int) for i in range(3)]
orange = ((h < 18) | (h > 172)) & (s > 150) & (v > 70)
m = np.full((H, W), cv2.GC_BGD, np.uint8)
x0, y0, x1, y1 = 0, 60, int(W * 0.74), int(H * 0.86)          # heap rectangle; excludes the floor reflection
sub = m[y0:y1, x0:x1]; sub[:] = cv2.GC_PR_BGD
o = orange[y0:y1, x0:x1]; sub[o] = cv2.GC_PR_FGD
sub[cv2.erode(o.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0] = cv2.GC_FGD
sub[(s[y0:y1, x0:x1] < 70)] = cv2.GC_BGD
bgd, fgd = np.zeros((1, 65)), np.zeros((1, 65))
cv2.grabCut(img, m, None, bgd, fgd, 5, cv2.GC_INIT_WITH_MASK)
fg = ((m == 1) | (m == 3)).astype(np.uint8)
fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
n, lab, st, _ = cv2.connectedComponentsWithStats(fg, 8)
big = max(range(1, n), key=lambda i: st[i][4])
# keep the heap and single granules lying near it (real loose grains), drop everything far (perforated plate, reflections)
keep = np.zeros_like(fg)
near = cv2.dilate((lab == big).astype(np.uint8), np.ones((61, 61), np.uint8))
dropped = 0
for i in range(1, n):
    if i == big or (st[i][4] > 30 and near[lab == i].mean() > 0.5): keep[lab == i] = 1
    else: dropped += 1
fail = np.zeros((H, W, 3), np.uint8); fail[orange & (keep == 0)] = (0, 0, 255); fail[(s < 90) & (keep == 1)] = (0, 255, 255)
cv2.imwrite(str(OUT / "masks/heap_failure.png"), fail)
cv2.imwrite(str(OUT / "masks/heap_mask.png"), keep * 255)
# band placement: heap rises from and is cropped by the bottom edge, 960x408
ys, xs = np.nonzero(keep); bx0, bx1, by0, by1 = xs.min(), xs.max(), ys.min(), ys.max()
crop = img[by0:by1 + 1, bx0:bx1 + 1].astype(np.float32) / 255; a = keep[by0:by1 + 1, bx0:bx1 + 1].astype(np.float32)
a = cv2.GaussianBlur(a, (0, 0), 0.8)
sc = 1000 / crop.shape[1]   # close-up: the heap's straight photo-frame sides fall outside the band
crop = cv2.resize(crop, None, fx=sc, fy=sc, interpolation=cv2.INTER_AREA); a = cv2.resize(a, None, fx=sc, fy=sc, interpolation=cv2.INTER_AREA)
hh, ww = a.shape
plate = np.zeros((408, 960, 3), np.float32); al = np.zeros((408, 960), np.float32)
ox, oy = (960 - ww) // 2, 60 - int(hh * 0.12)           # ragged real top edge across the band, base cropped by the bottom edge
ys0, ys1 = max(0, oy), min(408, oy + hh); xs0, xs1 = max(0, ox), min(960, ox + ww)
plate[ys0:ys1, xs0:xs1] = crop[ys0 - oy:ys1 - oy, xs0 - ox:xs1 - ox][..., ::-1]; al[ys0:ys1, xs0:xs1] = a[ys0 - oy:ys1 - oy, xs0 - ox:xs1 - ox]
yy, xx = np.mgrid[0:408, 0:960].astype(np.float32)
key = np.clip(1.30 - 1.55 * ((yy - 30) / 368) - 0.45 * np.abs(xx - 600) / 600, 0.0, 1.1) ** 2.2   # warm key from above, base falls off
lum = plate @ np.array([0.299, 0.587, 0.114], np.float32)
warm = plate * key[..., None] * (0.55 + 1.1 * np.clip(lum / 0.75, 0, 1.2) ** 1.5)[..., None] * np.array([1.0, 0.92, 0.75], np.float32)
warm = np.clip(warm, 0, 1) * al[..., None]
rgba = np.dstack([warm, al])
cv2.imwrite(str(OUT / "sh5/heap_rgba_960x408.png"), cv2.cvtColor((rgba * 255 + .5).astype(np.uint8), cv2.COLOR_RGBA2BGRA))
json.dump(dict(rect=[x0, y0, x1, y1], bbox_src=[int(bx0), int(by0), int(bx1), int(by1)], scale=float(sc), offset_band=[int(ox), int(oy)],
               components=int(n - 1), dropped=int(dropped), heap_top_band_y=int(max(0, oy))), open(OUT / "sh5/heap_place.json", "w"), indent=1)
print("dropped", dropped, "place", ox, oy, ww, hh)

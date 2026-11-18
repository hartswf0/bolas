"""Density-cut the CC0 Skeletonkey.png photograph into a flat brass paper piece (and a black silhouette variant).
Hand choices: crop box of the LEFT key, threshold 118 on the grey scan, keep only the largest dark component,
fill every interior light hole except the bow hole (the stamped 'CHINA' letters are filled; the bow hole stays open)."""
import sys, json, numpy as np, cv2
from PIL import Image
src, out_dir = sys.argv[1], sys.argv[2]
g = np.array(Image.open(src).convert("L"))
x0, y0, x1, y1 = 150, 40, 470, 660          # hand-placed crop around the left key
c = g[y0:y1, x0:x1]
TH = 118
m = (c < TH).astype(np.uint8)
m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
k = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]); m = (lab == k).astype(np.uint8)
# holes = light components not touching the border
inv = 1 - m
n2, lab2, st2, cen = cv2.connectedComponentsWithStats(inv, 4)
holes = []
for i in range(1, n2):
    xx, yy, ww, hh, a = st2[i]
    if xx == 0 or yy == 0 or xx + ww >= m.shape[1] or yy + hh >= m.shape[0]:
        continue
    holes.append((a, i))
holes.sort(reverse=True)
bow = holes[0][1] if holes else None          # the largest enclosed hole is the bow hole
for a, i in holes[1:]:
    m[lab2 == i] = 1                          # fill stamped letters and specks
# smooth the cut edge slightly (scissor line), keep hole
m = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.2) > 0.5
ys, xs = np.where(m); m = m[ys.min()-4:ys.max()+5, xs.min()-4:xs.max()+5]
H, W = m.shape
edge = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((5, 5), np.uint8)) > 0
BRASS = (196, 150, 66); INK = (43, 32, 33)
rgba = np.zeros((H, W, 4), np.uint8)
rgba[m] = (*BRASS, 255)
rgba[edge & m] = (*INK, 255)
Image.fromarray(rgba).save(f"{out_dir}/key_cut.png")
sil = np.zeros((H, W, 4), np.uint8); sil[m] = (22, 16, 15, 255)
Image.fromarray(sil).save(f"{out_dir}/key_cut_silhouette.png")
hole_open = bool(bow is not None and (~m).sum() > 0)
json.dump({"source": src, "crop": [x0, y0, x1, y1], "threshold": TH, "size": [W, H],
           "bow_hole_area_px": int(holes[0][0]) if holes else 0, "filled_holes": len(holes) - 1,
           "brass": BRASS, "ink": INK, "orientation": "bow down, bit up-left (as photographed)"},
          open(f"{out_dir}/key_cut.json", "w"), indent=1)
print(W, H, holes[:3])

"""SCION #29 GrabCut + #8 constraint graph: measure the real runner photograph.

Input : r2/spritzguss.jpg (Gmhofmann, CC BY-SA 4.0, Commons), decoded with PIL/cv2 only.
Output: test-shot/geometry.json   ring ellipses, rectified radii, hub/sprue, arm polylines
        test-shot/cut_*.png       RGBA cutouts (loose rings, runner-with-rings), failure masks
"""
import json, sys
from pathlib import Path
import cv2, numpy as np

SRC = Path("/home/user/bolas/paeleo/scion/oulipo/films/sources/le-chant-du-styrene")
OUT = SRC / "test-shot"
img = cv2.imread(str(SRC / "r2/spritzguss.jpg"))
H, W = img.shape[:2]
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
h, s, v = [hsv[..., i].astype(int) for i in range(3)]

# unary seeds from hue: teal plastic vs grey/white table and its grey shadow
teal = (h > 80) & (h < 110) & (s > 90)
sure_fg = cv2.erode(teal.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
sure_bg = (s < 45)
mask = np.full((H, W), cv2.GC_PR_BGD, np.uint8)
mask[teal] = cv2.GC_PR_FGD
mask[sure_fg] = cv2.GC_FGD
mask[sure_bg] = cv2.GC_BGD
bgd, fgd = np.zeros((1, 65)), np.zeros((1, 65))
cv2.grabCut(img, mask, None, bgd, fgd, 6, cv2.GC_INIT_WITH_MASK)
fg = ((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD)).astype(np.uint8)
fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))

n, lab, stats, cent = cv2.connectedComponentsWithStats(fg, 8)
comps = [(i, stats[i]) for i in range(1, n) if stats[i][4] > 800]
islands = [int(stats[i][4]) for i in range(1, n) if stats[i][4] <= 800]
print("components", [(i, st.tolist()) for i, st in comps], "dropped islands", len(islands))

def ring_fit(m):
    cs, hier = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    outer = max(cs, key=cv2.contourArea)
    (cx, cy), (a, b), ang = cv2.fitEllipse(outer)
    holes = [c for c, hh in zip(cs, hier[0]) if hh[3] >= 0 and cv2.contourArea(c) > 80]
    hole = max(holes, key=cv2.contourArea) if holes else None
    hf = cv2.fitEllipse(hole) if hole is not None and len(hole) >= 5 else None
    return dict(cx=cx, cy=cy, major=max(a, b), minor=min(a, b), angle=ang,
                hole=None if hf is None else dict(cx=hf[0][0], cy=hf[0][1], major=max(hf[1]), minor=min(hf[1]), angle=hf[2]))

loose, assemblies = [], []
for i, st in comps:
    x, y, w, hh, area = st
    m = (lab == i).astype(np.uint8)
    if x + w < 640 and area < 20000 and w < 200:
        loose.append((i, ring_fit(m), st))
    else:
        assemblies.append((i, st))
print("loose", len(loose), "assemblies", [a[1].tolist() for a in assemblies])

# the right assembly: runner with 4 rings attached
ri = max(assemblies, key=lambda a: a[1][0])[0]
rm = (lab == ri).astype(np.uint8)
# rings on the assembly: open away the thin arms, keep discs
disc = cv2.morphologyEx(rm, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (41, 41)))
nd, dl, dst, dc = cv2.connectedComponentsWithStats(disc, 8)
on_arm = []
for j in range(1, nd):
    if dst[j][4] > 3000:
        mm = (dl == j).astype(np.uint8)
        mm = cv2.dilate(mm, np.ones((9, 9), np.uint8)) & rm
        on_arm.append(ring_fit(mm))
print("rings on runner", len(on_arm))
arms_only = rm & (1 - cv2.dilate(disc, np.ones((15, 15), np.uint8)))
# hub: densest arm pixel neighbourhood (where the four arms cross)
dens = cv2.boxFilter(arms_only.astype(np.float32), -1, (41, 41))
hy, hx = np.unravel_index(np.argmax(dens), dens.shape)
# sprue post top: the topmost arm-mask pixel within 40 px of hub column (the vertical post)
ys, xs = np.nonzero(arms_only[:, hx - 25:hx + 25])
top = int(ys.min()); topx = int(xs[ys.argmin()] + hx - 25)
# arm width from distance transform along hub->ring lines
dt = cv2.distanceTransform(rm, cv2.DIST_L2, 5)

aspect = float(np.median([r["minor"] / r["major"] for r in on_arm + [l[1] for l in loose]]))
print("ellipse aspect (minor/major)", aspect)

def rect(x, y):  # declared transform: undo the camera's foreshortening of the table plane
    return [float(x), float((y - hy) / aspect + hy)]

arms = []
for r in on_arm:
    ang = np.arctan2(r["cy"] - hy, r["cx"] - hx)
    ts = np.linspace(0.15, 0.7, 30)
    pts = [(hx + t * (r["cx"] - hx), hy + t * (r["cy"] - hy)) for t in ts]
    widths = [2 * float(dt[int(py), int(px)]) for px, py in pts]
    arms.append(dict(angle=float(ang), ring=r, width_px=float(np.median(widths))))
arms.sort(key=lambda a: a["angle"])
# loose ring -> arm mapping: match by order of angle around the loose-ring group centre
lc = np.mean([[l[1]["cx"], l[1]["cy"]] for l in loose], 0)
loose_sorted = sorted(loose, key=lambda l: np.arctan2(l[1]["cy"] - lc[1], l[1]["cx"] - lc[0]))

# export cutouts (RGBA, real shading kept) + rectified ring masks for the IoU test
rgba = np.dstack([img[..., ::-1], (fg * 255).astype(np.uint8)])
geo = dict(source="r2/spritzguss.jpg", source_url="https://commons.wikimedia.org/wiki/File:Spritzguss_teile.jpg",
           licence="CC BY-SA 4.0", author="Gmhofmann", image_size=[W, H],
           method="GrabCut (cv2.grabCut, mask init from HSV teal seeds, 6 iters), components > 800 px; ellipse fits by cv2.fitEllipse",
           declared_transform=f"rectify table plane: y' = (y - hub_y)/{aspect:.4f} + hub_y (median ring minor/major); film coords are this rectified frame scaled by the shot's plane scale",
           aspect=aspect, hub=[float(hx), float(hy)], hub_rect=rect(hx, hy), sprue_top=[topx, top],
           dropped_islands=len(islands), arms=[], loose_rings=[])
for k, (a, (li, lr, st)) in enumerate(zip(arms, loose_sorted)):
    r = a["ring"]
    x, y, w, hh, _ = st
    cut = rgba[y:y + hh, x:x + w].copy()
    cut[..., 3] = np.where(lab[y:y + hh, x:x + w] == li, 255, 0)
    cv2.imwrite(str(OUT / f"cut_ring{k}.png"), cv2.cvtColor(cut, cv2.COLOR_RGBA2BGRA))
    geo["arms"].append(dict(id=k, angle_deg=float(np.degrees(a["angle"])), width_px=a["width_px"],
                            ring_center_src=[r["cx"], r["cy"]], ring_center_rect=rect(r["cx"], r["cy"]),
                            ring_outer_R_rect=r["major"] / 2, ring_hole_r_rect=(r["hole"]["major"] / 2 if r["hole"] else r["major"] * 0.18),
                            ring_ellipse_src=r))
    geo["loose_rings"].append(dict(id=k, arm=k, bbox=[int(x), int(y), int(w), int(hh)], cutout=f"cut_ring{k}.png",
                                   ellipse_src=lr, R_rect=lr["major"] / 2,
                                   hole_r_rect=(lr["hole"]["major"] / 2 if lr["hole"] else None)))
cv2.imwrite(str(OUT / "cut_runner_with_rings.png"), cv2.cvtColor(np.dstack([img[..., ::-1], rm * 255]).astype(np.uint8), cv2.COLOR_RGBA2BGRA))
fail = np.zeros((H, W, 3), np.uint8); fail[(mask == cv2.GC_PR_FGD) & (fg == 0)] = (0, 0, 255); fail[(mask == cv2.GC_PR_BGD) & (fg == 1)] = (0, 255, 255)
cv2.imwrite(str(OUT / "grabcut_failure_mask.png"), fail)
json.dump(geo, open(OUT / "geometry.json", "w"), indent=1, default=float)
dbg = img.copy()
for a in geo["arms"]:
    e = a["ring_ellipse_src"]; cv2.ellipse(dbg, ((e["cx"], e["cy"]), (e["major"], e["minor"]), e["angle"]), (0, 0, 255), 2)
    cv2.line(dbg, (int(hx), int(hy)), (int(e["cx"]), int(e["cy"])), (0, 255, 0), 2)
    cv2.putText(dbg, str(a["id"]), (int(e["cx"]), int(e["cy"])), 0, 1, (0, 0, 0), 2)
for l in geo["loose_rings"]:
    e = l["ellipse_src"]; cv2.ellipse(dbg, ((e["cx"], e["cy"]), (e["major"], e["minor"]), e["angle"]), (255, 0, 255), 2)
    cv2.putText(dbg, str(l["id"]), (int(e["cx"]), int(e["cy"])), 0, 1, (0, 0, 0), 2)
cv2.circle(dbg, (int(hx), int(hy)), 6, (0, 0, 0), -1)
cv2.imwrite(str(sys.argv[1] if len(sys.argv) > 1 else OUT / "geometry_debug.jpg"), dbg)
print(json.dumps({k: geo[k] for k in ("hub", "aspect", "sprue_top")}), [(a["id"], round(a["angle_deg"]), round(a["width_px"], 1), round(a["ring_outer_R_rect"], 1)) for a in geo["arms"]])

"""U2 cutout puppetry: SCION #29 GrabCut + #8 constraint graph.

Input : sources/le-chant-du-styrene/r2/spritzguss.jpg (Gmhofmann, CC BY-SA 4.0), decoded with cv2 only.
Output: <OUT>/pieces/*.png   RGBA cutouts with the photograph's real pixels (teal, ungelled)
        <OUT>/masks/*.png    contour masks, failure masks
        <OUT>/geom_src.json  measured geometry in source pixels
GrabCut is seeded per region: a rectangle (outside = sure background) plus hue seeds
(teal, saturated = probable/sure foreground; unsaturated table/shadow = sure background).
"""
import json, sys
from pathlib import Path
import cv2, numpy as np

SRC = Path("/home/user/bolas/paeleo/scion/oulipo/films/sources/le-chant-du-styrene")
OUT = SRC / "cutout-puppetry-camera-unit-a-sh1-sh2a-sh2b-sh5-heap-"
img = cv2.imread(str(SRC / "r2/spritzguss.jpg"))
H, W = img.shape[:2]
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
h, s, v = [hsv[..., i].astype(int) for i in range(3)]
teal = (h > 80) & (h < 110) & (s > 90)
sure_fg = cv2.erode(teal.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
sure_bg = s < 45

RECTS = {  # x, y, w, h  (source px) - region seeds
    "bare_runner": (80, 25, 410, 330),
    "loose_rings": (20, 280, 400, 360),
    "runner_with_rings": (720, 55, 545, 490),
}

def grab(rect):
    x, y, w, hh = rect
    m = np.full((H, W), cv2.GC_BGD, np.uint8)
    sub = np.full((hh, w), cv2.GC_PR_BGD, np.uint8)
    t, f, b = teal[y:y+hh, x:x+w], sure_fg[y:y+hh, x:x+w], sure_bg[y:y+hh, x:x+w]
    sub[t] = cv2.GC_PR_FGD; sub[f] = cv2.GC_FGD; sub[b] = cv2.GC_BGD
    m[y:y+hh, x:x+w] = sub
    bgd, fgd = np.zeros((1, 65)), np.zeros((1, 65))
    cv2.grabCut(img, m, None, bgd, fgd, 6, cv2.GC_INIT_WITH_MASK)
    fg = ((m == cv2.GC_FGD) | (m == cv2.GC_PR_FGD)).astype(np.uint8)
    fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    # failure mask: hue said plastic but GrabCut said no (red), and GrabCut said yes on an unsaturated pixel (yellow)
    fail = np.zeros((H, W, 3), np.uint8)
    fail[teal & (fg == 0)] = (0, 0, 255)
    fail[(s < 70) & (fg == 1)] = (0, 255, 255)
    return fg, m, fail

def fill_holes_small(m, maxa=40):
    # tiny enclosed background pinholes inside plastic are JPEG noise; real bores are much larger
    inv = (1 - m).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(inv, 4)
    for i in range(1, n):
        if st[i][4] <= maxa:
            m[lab == i] = 1
    return m

def ring_fit(m):
    cs, hier = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    outer = max(cs, key=cv2.contourArea)
    (cx, cy), (a, b), ang = cv2.fitEllipse(outer)
    holes = [c for c, hh in zip(cs, hier[0]) if hh[3] >= 0 and cv2.contourArea(c) > 60]
    hole = max(holes, key=cv2.contourArea) if holes else None
    hf = cv2.fitEllipse(hole) if hole is not None and len(hole) >= 5 else None
    return dict(cx=float(cx), cy=float(cy), major=float(max(a, b)), minor=float(min(a, b)), angle=float(ang),
                hole=None if hf is None else dict(cx=float(hf[0][0]), cy=float(hf[0][1]), major=float(max(hf[1])), minor=float(min(hf[1]))))

def save_piece(name, mask, bbox, pad=6):
    x, y, w, hh = bbox
    x0, y0 = max(0, x - pad), max(0, y - pad); x1, y1 = min(W, x + w + pad), min(H, y + hh + pad)
    rgba = np.dstack([img[y0:y1, x0:x1], (mask[y0:y1, x0:x1] * 255).astype(np.uint8)])
    cv2.imwrite(str(OUT / "pieces" / f"{name}.png"), rgba)
    cv2.imwrite(str(OUT / "masks" / f"{name}_mask.png"), mask[y0:y1, x0:x1] * 255)
    cs, _ = cv2.findContours(mask[y0:y1, x0:x1].copy(), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    c = np.zeros((y1 - y0, x1 - x0), np.uint8); cv2.drawContours(c, cs, -1, 255, 1)
    cv2.imwrite(str(OUT / "masks" / f"{name}_contour.png"), c)
    return [int(x0), int(y0), int(x1 - x0), int(y1 - y0)]

report = dict(pieces={}, islands_dropped={}, background_islands_remaining={})
geo = dict(image_size=[W, H])

# ---- bare runner (left): one component, keep everything connected to it (gate stubs, legs, sprue)
fg, m, fail = grab(RECTS["bare_runner"])
n, lab, st, _ = cv2.connectedComponentsWithStats(fg, 8)
big = max(range(1, n), key=lambda i: st[i][4])
dropped = [int(st[i][4]) for i in range(1, n) if i != big]
# loose rings intrude at the bottom of this rect; keep the runner only
bm = fill_holes_small((lab == big).astype(np.uint8))
report["islands_dropped"]["bare_runner"] = dropped
cv2.imwrite(str(OUT / "masks/bare_runner_failure.png"), fail)
report["pieces"]["bare_runner"] = dict(bbox_src=save_piece("bare_runner", bm, st[big][:4].tolist()))

# hub, arm directions and tips (Sutherland points): angular histogram of mask pixels around the hub
dt = cv2.distanceTransform(bm, cv2.DIST_L2, 5)
dens = cv2.boxFilter(bm.astype(np.float32), -1, (41, 41))
hy, hx = np.unravel_index(np.argmax(dens), dens.shape)
ys, xs = np.nonzero(bm)
ang = np.degrees(np.arctan2(ys - hy, xs - hx)); rad = np.hypot(xs - hx, ys - hy)
hist = np.zeros(360)
for a, r in zip(ang.astype(int) % 360, rad):
    if r > 30: hist[a] += 1
hs = np.convolve(np.r_[hist[-6:], hist, hist[:6]], np.ones(7) / 7, "same")[6:-6]
peaks = [a for a in range(360) if hs[a] == max(hs[(a + d) % 360] for d in range(-20, 21)) and hs[a] > 15]
arms_b = []
for a in peaks:
    sel = (np.abs(((ang - a + 180) % 360) - 180) < 7) & (rad > 30)
    k = np.argmax(rad * sel)
    tip = [float(xs[k]), float(ys[k])]
    L = float(rad[k])
    poly = [[float(hx + t * (tip[0] - hx)), float(hy + t * (tip[1] - hy))] for t in np.linspace(0, 1, 9)]
    widths = [2 * float(dt[int(py), int(px)]) for px, py in poly[1:-1]]
    arms_b.append(dict(angle_deg=float(a), tip_src=tip, length_src=L, polyline_src=poly, width_src=float(np.median(widths)), mass=float(hs[a])))
geo["bare_runner"] = dict(hub_src=[float(hx), float(hy)], arms_all=arms_b)

# ---- loose rings
fg, m, fail = grab(RECTS["loose_rings"])
fg[:, :] = fg * (1 - bm)  # the bare runner's lower leg overlaps this rect
n, lab, st, _ = cv2.connectedComponentsWithStats(fg, 8)
comps = [i for i in range(1, n) if st[i][4] > 3000 and st[i][2] < 200 and st[i][3] < 200]
report["islands_dropped"]["loose_rings"] = [int(st[i][4]) for i in range(1, n) if i not in comps]
cv2.imwrite(str(OUT / "masks/loose_rings_failure.png"), fail)
loose = []
for i in comps:
    mm = fill_holes_small((lab == i).astype(np.uint8))
    loose.append((ring_fit(mm), mm, st[i][:4].tolist()))
loose.sort(key=lambda t: (t[0]["cy"] > 430, t[0]["cx"]))  # top row left->right, then bottom row
geo["loose_rings"] = []
for k, (rf, mm, bb) in enumerate(loose):
    bbox = save_piece(f"ring{k}", mm, bb)
    report["pieces"][f"ring{k}"] = dict(bbox_src=bbox)
    geo["loose_rings"].append(dict(id=k, ellipse_src=rf, bbox_src=bbox, piece=f"pieces/ring{k}.png"))

# ---- runner with rings (right): the real complete shot
fg, m, fail = grab(RECTS["runner_with_rings"])
n, lab, st, _ = cv2.connectedComponentsWithStats(fg, 8)
big = max(range(1, n), key=lambda i: st[i][4])
report["islands_dropped"]["runner_with_rings"] = [int(st[i][4]) for i in range(1, n) if i != big]
rm = fill_holes_small((lab == big).astype(np.uint8))
cv2.imwrite(str(OUT / "masks/runner_with_rings_failure.png"), fail)
report["pieces"]["runner_with_rings"] = dict(bbox_src=save_piece("runner_with_rings", rm, st[big][:4].tolist()))

for name, mm in [("bare_runner", bm)] + [(f"ring{k}", l[1]) for k, l in enumerate(loose)] + [("runner_with_rings", rm)]:
    # background islands: background components fully enclosed and NOT a bore (area<=40 were filled)
    inv = (1 - mm).astype(np.uint8); nn, ll, ss, _ = cv2.connectedComponentsWithStats(inv, 4)
    report["background_islands_remaining"][name] = [int(ss[i][4]) for i in range(1, nn) if ss[i][0] > 0 and ss[i][1] > 0 and ss[i][0] + ss[i][2] < W and ss[i][1] + ss[i][3] < H]
    nn, _, ss, _ = cv2.connectedComponentsWithStats(mm, 8)
    report["pieces"][name]["fg_components"] = int(nn - 1)

json.dump(dict(geo=geo, report=report), open(OUT / "geom_src.json", "w"), indent=1)

dbg = img.copy()
for a in arms_b:
    cv2.line(dbg, (int(hx), int(hy)), tuple(int(v) for v in a["tip_src"]), (0, 200, 0), 2)
    cv2.putText(dbg, f'{a["angle_deg"]:.0f}', tuple(int(v) for v in a["tip_src"]), 0, 0.6, (0, 0, 255), 2)
for k, (rf, _, _) in enumerate(loose):
    cv2.ellipse(dbg, ((rf["cx"], rf["cy"]), (rf["major"], rf["minor"]), rf["angle"]), (255, 0, 255), 2)
    cv2.putText(dbg, str(k), (int(rf["cx"]), int(rf["cy"])), 0, 1, (0, 0, 0), 2)
ov = dbg.copy(); ov[bm > 0] = (0, 0, 255); ov[rm > 0] = (0, 160, 255)
for _, mm, _ in loose: ov[mm > 0] = (255, 0, 255)
dbg = cv2.addWeighted(dbg, 0.6, ov, 0.4, 0)
cv2.imwrite(str(OUT / "masks/cut_debug.jpg"), dbg)
print(json.dumps(report, indent=0)[:1500]); print("hub", hx, hy, "peaks", peaks, [(round(a["length_src"]), round(a["width_src"], 1)) for a in arms_b])

"""U1-lite for the test shot: rectify the 1916 Agence Rol bus to a side elevation,
cut it out with GrabCut (box + scribble seeds + hand polygon), cut the two wheels
out as separate pieces, and export RGBA plates + masks + failure masks.

Input  : films/sources/<slug>/commons/rol1916.jpg (Commons, PD; decoded with PIL only)
Output : films/sources/<slug>/test-shot/plates/*.png  and  plates.json
Run    : python3 -I plates.py
"""
import json, hashlib
from pathlib import Path
import numpy as np, cv2
from PIL import Image

ROOT = Path("/home/user/bolas/paeleo/scion/oulipo")
SRC = ROOT / "films/sources/mauro-martino-exercises-in-style/commons/rol1916.jpg"
OUT = ROOT / "films/sources/mauro-martino-exercises-in-style/test-shot/plates"
OUT.mkdir(parents=True, exist_ok=True)

S = 2  # plates are made at 2x the film scale, then downsampled by the renderer
src = np.array(Image.open(SRC).convert("L"))

# --- rectification: the long side panel (front pillar .. rear corner, roof .. skirt)
# picked by hand on a gridded zoom of the source (source px)
quad_src = np.float32([[727, 405], [1075, 410], [1075, 593], [728, 609]])
# target elevation: side panel 470 x 196 film-px (true CGO side ratio ~2.4:1)
ox, oy = 270, 30             # leave room on the left for the bonnet/cab and above for the roof
sw, sh = 470, 196
quad_dst = np.float32([[ox, oy], [ox + sw, oy], [ox + sw, oy + sh], [ox, oy + sh]]) * S
Hm = cv2.getPerspectiveTransform(quad_src, quad_dst)
CW, CH = 760 * S, 330 * S
rect = cv2.warpPerspective(src, Hm, (CW, CH), flags=cv2.INTER_CUBIC, borderValue=200)

def P(x, y):  # source px -> rectified plate px
    v = Hm @ np.array([x, y, 1.0]); return v[:2] / v[2]

# --- GrabCut: rectangle prior + scribbles + hand polygon (probable FG / sure BG)
# hand polygon of the bus outline in SOURCE coords (roof, hood, under-body, platform)
poly_src = np.array([
    [528, 380], [560, 377], [585, 395], [727, 388], [1072, 398], [1078, 420], [1080, 595],
    [1050, 606], [1000, 622], [990, 646], [940, 646], [890, 622], [835, 618], [745, 626],
    [712, 672], [660, 674], [640, 650], [600, 668], [560, 668], [536, 640], [526, 560],
    [522, 470], [524, 410]], np.float32)
poly = np.array([P(x, y) for x, y in poly_src], np.int32)
img3 = cv2.cvtColor(rect, cv2.COLOR_GRAY2BGR)
mask = np.full(rect.shape, cv2.GC_BGD, np.uint8)
cv2.fillPoly(mask, [poly], cv2.GC_PR_FGD)
inner = cv2.erode((mask == cv2.GC_PR_FGD).astype(np.uint8), np.ones((25, 25), np.uint8))
mask[inner > 0] = cv2.GC_FGD
# scribbles: sure-FG strokes along roof board and lower side panel (source coords)
for a, b in [((740, 418), (1060, 420)), ((740, 560), (1060, 555)), ((700, 625), (1000, 610))]:
    cv2.line(mask, tuple(map(int, P(*a))), tuple(map(int, P(*b))), cv2.GC_FGD, 10)
# sure-BG scribble: sky gap above the roof and cobbles between wheels
for a, b in [((600, 360), (1070, 375)), ((760, 660), (900, 650))]:
    cv2.line(mask, tuple(map(int, P(*a))), tuple(map(int, P(*b))), cv2.GC_BGD, 8)
bgd = np.zeros((1, 65), np.float64); fgd = np.zeros((1, 65), np.float64)
cv2.grabCut(img3, mask, None, bgd, fgd, 6, cv2.GC_INIT_WITH_MASK)
fg = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
# alpha cleanup: keep the single largest component (no background islands), fill holes
n, lab, st, _ = cv2.connectedComponentsWithStats(fg)
keep = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
islands = int(n - 2)
fg = np.where(lab == keep, 255, 0).astype(np.uint8)
holes = fg.copy(); ff = np.zeros((fg.shape[0] + 2, fg.shape[1] + 2), np.uint8)
cv2.floodFill(holes, ff, (0, 0), 255); fg = fg | cv2.bitwise_not(holes)
fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
# failure mask: hand-polygon pixels GrabCut rejected (exported, not hidden)
polymask = np.zeros_like(fg); cv2.fillPoly(polymask, [poly], 255)
fail = cv2.bitwise_and(polymask, cv2.bitwise_not(fg))

# --- wheels: separate circular pieces (rectified ellipse -> circle)
wheels = {}
for name, (cx, cy, rx, ry) in {"front": (682, 631, 34, 42), "rear": (971, 608, 29, 38)}.items():
    c = P(cx, cy); e = P(cx + rx, cy); f = P(cx, cy + ry)
    r = int(max(np.linalg.norm(e - c), np.linalg.norm(f - c)) * 1.02)
    x0, y0 = int(c[0] - r), int(c[1] - r)
    tile = rect[y0:y0 + 2 * r, x0:x0 + 2 * r].copy()
    m = np.zeros_like(tile); cv2.circle(m, (r, r), r - 1, 255, -1)
    wheels[name] = dict(center=[float(c[0] / S), float(c[1] / S)], r=float(r / S))
    Image.fromarray(np.dstack([tile, tile, tile, m])).save(OUT / f"wheel_{name}.png")
    # remove the wheel from the body plate: inpaint the hub area with under-body dark
    cv2.circle(fg, (int(c[0]), int(c[1])), r - 2, 255, -1)
    hole = np.zeros_like(rect); cv2.circle(hole, (int(c[0]), int(c[1])), r + 2, 255, -1)
    rect = np.where(hole > 0, 38, rect).astype(np.uint8)

Image.fromarray(np.dstack([rect, rect, rect, fg])).save(OUT / "bus_rect_rgba.png")
Image.fromarray(fg).save(OUT / "bus_mask.png")
Image.fromarray(fail).save(OUT / "bus_failmask.png")
ys, xs = np.nonzero(fg)
meta = dict(
    source=str(SRC.relative_to(ROOT)),
    source_sha1=hashlib.sha1(SRC.read_bytes()).hexdigest(),
    scale=S, homography=Hm.tolist(), quad_src=quad_src.tolist(), quad_dst=(quad_dst / S).tolist(),
    bbox_film_px=[float(xs.min() / S), float(ys.min() / S), float(xs.max() / S), float(ys.max() / S)],
    side_panel=dict(x=ox, y=oy, w=sw, h=sh),
    platform_x_film_px=[float(P(1040, 500)[0] / S), float(P(1080, 500)[0] / S)],
    wheels=wheels, grabcut_iterations=6, removed_islands=islands,
    failmask_px=int((fail > 0).sum()), fg_px=int((fg > 0).sum()),
)
(OUT / "plates.json").write_text(json.dumps(meta, indent=1))
print(json.dumps({k: v for k, v in meta.items() if k != "homography"}, indent=1))

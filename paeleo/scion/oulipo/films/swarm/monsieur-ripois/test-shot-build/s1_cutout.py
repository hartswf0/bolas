"""SCION #29 GrabCut on the V0 working plate (1440x1080, from LoC master crop).
Pieces: her head+hat, his head. Plus a couple-figure matte used only for the burn-in.
Hand-drawn contour = probable foreground, its eroded core = definite fg, a dilated ring = probable bg,
outside = bg. Exports RGBA pieces, masks, failure masks (pixels where grabcut disagreed with the contour)
and the inpainted plate."""
import numpy as np, cv2, json
from PIL import Image
SRC = "/home/user/bolas/paeleo/scion/oulipo/films/sources/monsieur-ripois/test-shot/"
g = cv2.imread(SRC + "plate-1440.png", 0)
rgb = cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)
# add a local-texture channel so grabcut's GMM sees hair/curl texture vs smooth wall
tex = cv2.GaussianBlur(np.abs(cv2.Laplacian(g, cv2.CV_32F)), (0, 0), 3)
tex = np.clip(tex * 6, 0, 255).astype(np.uint8)
feat = np.dstack([g, tex, cv2.GaussianBlur(g, (0, 0), 6)])

def cut(poly, keep=None, er=25, di=19, it=8):
    P = np.zeros(g.shape, np.uint8); cv2.fillPoly(P, [np.array(poly, np.int32)], 1)
    m = np.full(g.shape, cv2.GC_BGD, np.uint8)
    m[cv2.dilate(P, np.ones((di, di), np.uint8)) > 0] = cv2.GC_PR_BGD
    m[P > 0] = cv2.GC_PR_FGD
    m[cv2.erode(P, np.ones((er, er), np.uint8)) > 0] = cv2.GC_FGD
    bg = np.zeros((1, 65)); fg = np.zeros((1, 65))
    cv2.grabCut(feat, m, None, bg, fg, it, cv2.GC_INIT_WITH_MASK)
    a = np.where((m == 1) | (m == 3), 255, 0).astype(np.uint8)
    if keep is not None:
        K = np.zeros_like(a); cv2.fillPoly(K, [np.array(keep, np.int32)], 255); a &= K
    # alpha cleanup: keep the largest component (no background islands), close pin-holes
    n, lab, st, _ = cv2.connectedComponentsWithStats(a)
    if n > 1:
        big = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]); a = np.where(lab == big, 255, 0).astype(np.uint8)
    a = cv2.morphologyEx(a, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    fail = ((a > 0) != (P > 0)).astype(np.uint8) * 255
    a = cv2.GaussianBlur(a, (0, 0), 1.2)   # soft card edge at 1440 -> ~0.6 px at output
    return a, fail

HER = [(240,170),(330,88),(420,78),(500,108),(545,150),(578,210),(592,290),(612,350),(603,382),(607,420),(592,462),(545,490),(470,497),(380,484),(300,474),(222,452),(214,400),(238,330),(248,250)]
HER_KEEP = [(200,60),(640,60),(640,470),(560,500),(470,505),(380,492),(200,470)]
HIM = [(812,118),(852,38),(922,12),(1002,18),(1052,68),(1062,160),(1048,232),(1030,292),(1008,332),(958,352),(908,346),(880,300),(850,252),(820,210)]
HIM_KEEP = [(790,0),(1090,0),(1090,330),(1040,350),(960,362),(900,356),(790,300)]
COUPLE = [(30,520),(150,470),(230,330),(330,80),(500,100),(600,330),(700,370),(800,250),(820,60),(950,10),(1060,60),(1060,300),(1180,420),(1270,560),(1330,750),(1340,880),(1380,1080),(840,1080),(780,840),(700,770),(400,700),(30,690)]

pieces = {}
for name, poly, keep, piv in [("her_head", HER, HER_KEEP, (470, 478)), ("his_head", HIM, HIM_KEEP, (958, 360))]:
    a, fail = cut(poly, keep)
    pieces[name] = dict(pivot=piv, poly=poly, area=int((a > 127).sum()), fail_px=int((fail > 0).sum()))
    cv2.imwrite(SRC + f"piece-{name}-mask.png", a); cv2.imwrite(SRC + f"piece-{name}-failmask.png", fail)
    rgba = np.dstack([g, g, g, a]); Image.fromarray(rgba, "RGBA").save(SRC + f"piece-{name}.png")
fig, ffail = cut(COUPLE, er=41, di=31, it=5)
cv2.imwrite(SRC + "matte-couple.png", fig); cv2.imwrite(SRC + "matte-couple-failmask.png", ffail)
hole = np.zeros_like(g)
for n in pieces: hole |= (cv2.imread(SRC + f"piece-{n}-mask.png", 0) > 20).astype(np.uint8) * 255
hole = cv2.dilate(hole, np.ones((9, 9), np.uint8))
plate = cv2.inpaint(g, hole, 9, cv2.INPAINT_TELEA)
cv2.imwrite(SRC + "plate-inpainted.png", plate)
json.dump({"source": "LoC 2017831564 master 8d04830u.tif crop (see plate-1440.txt)", "working_res": [1440, 1080],
           "pieces": pieces, "method": "cv2.grabCut GC_INIT_WITH_MASK on [gray, |laplacian| texture, blurred gray], contour seeds, largest-component cleanup, Telea inpaint of vacated plate"},
          open(SRC + "pieces.json", "w"), indent=1)
print(json.dumps(pieces, indent=0)[:600])

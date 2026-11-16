"""SCION #29 GrabCut cutout extraction for the present-tense rig (U2 full build).
Sources: V0 working plate (LoC 2017831564 master crop -> 1440x1080) and V1 master crop (LoC 2017831565, her gloved hand).
Seeds: hand-traced contour = probable fg; eroded core = definite fg; dilated ring = probable bg; outside = bg.
Features: [gray, |laplacian| texture, blurred gray]. Cleanup: keep largest component, close pinholes, 1.2 px feather.
Failure mask = pixels where GrabCut disagreed with the traced contour (inspected, recorded)."""
import numpy as np, cv2, json
from PIL import Image
TS = "/home/user/bolas/paeleo/scion/oulipo/films/sources/monsieur-ripois/test-shot/"
OUT = "/home/user/bolas/paeleo/scion/oulipo/films/sources/monsieur-ripois/present/"

def feats(g):
    tex = np.clip(cv2.GaussianBlur(np.abs(cv2.Laplacian(g, cv2.CV_32F)), (0, 0), 3) * 6, 0, 255).astype(np.uint8)
    return np.dstack([g, tex, cv2.GaussianBlur(g, (0, 0), 6)])

def cut(g, feat, poly, keep=None, er=25, di=19, it=8):
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
    n, lab, st, _ = cv2.connectedComponentsWithStats(a)
    if n > 1:
        big = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]); a = np.where(lab == big, 255, 0).astype(np.uint8)
    a = cv2.morphologyEx(a, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    fail = ((a > 0) != (P > 0)).astype(np.uint8) * 255
    return cv2.GaussianBlur(a, (0, 0), 1.2), fail

g = cv2.imread(TS + "plate-1440.png", 0); F = feats(g)
PIECES = {
 "her_head": dict(poly=[(290,165),(336,102),(410,86),(480,95),(500,135),(540,150),(575,200),(580,270),(600,330),(620,360),(595,385),(590,440),(560,480),(480,490),(300,480),(230,440),(220,370),(260,320),(280,240),(275,180)],
                  keep="poly", pivot=(470,478), limits=[-12, 9], parent="body(plate)", er=21, di=15,
                  note="contour traced tight to hat, curls and profile (rev. 2: the first cut carried wall and veil with it)"),
 "his_head": dict(poly=[(812,118),(852,38),(922,12),(1002,18),(1052,68),(1062,160),(1048,232),(1030,292),(1008,332),(958,352),(908,346),(880,300),(850,252),(820,210)],
                  keep=[(790,0),(1090,0),(1090,330),(1040,350),(960,362),(900,356),(790,300)], pivot=(958,360), limits=[-2, 4], parent="body(plate)"),
 "his_arm": dict(poly=[(655,352),(720,352),(780,372),(808,410),(800,450),(760,478),(700,500),(640,500),(604,474),(592,444),(620,420),(645,392)],
                 keep=None, pivot=(800,430), limits=[-6, 2], parent="body(plate)", er=15, di=13,
                 note="his right upper arm/forearm along the sofa back; the hand is hidden behind her (as in the print)"),
 "pocket": dict(poly=[(1108,700),(1182,698),(1186,732),(1110,736)], keep=None, pivot=(1145,700), limits=[0, 10], parent="body(plate)", er=5, di=9,
                note="waistcoat welt pocket (the only pocket opening visible in the print); flap lifts as the slip slides out"),
}
meta = {}
for n, d in PIECES.items():
    a, fail = cut(g, F, d["poly"], d["poly"] if d.get("keep") == "poly" else d.get("keep"), d.get("er", 25), d.get("di", 19))
    cv2.imwrite(OUT + f"piece-{n}-mask.png", a); cv2.imwrite(OUT + f"piece-{n}-failmask.png", fail)
    Image.fromarray(np.dstack([g, g, g, a]), "RGBA").save(OUT + f"piece-{n}.png")
    ys, xs = np.nonzero(a > 127)
    meta[n] = dict(source="V0 plate-1440", bbox_plate=[int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
                   pivot=list(d["pivot"]), limits_deg=d["limits"], parent=d["parent"], area=int((a > 127).sum()),
                   fail_px=int((fail > 0).sum()), fail_frac=round(float((fail > 0).sum()) / max(1, (a > 127).sum()), 3),
                   transform_to_master="master_x = 391 + x*5597/1440 + 2772 ; master_y = 456 + y*4198/1080 + 4158 (8d04830u.tif px)",
                   note=d.get("note", ""))
# her gloved hand from V1 (same sitting, same flash, LoC 2017831567 master crop x 4980..5740, y 6240..7190)
h = cv2.imread(OUT + "v1-master-hand.png", 0); FH = feats(h)
HPOLY = [(345,230),(420,212),(500,228),(560,280),(588,360),(590,470),(582,580),(560,660),(520,715),(460,738),(410,725),(370,680),(342,620),(338,520),(340,420),(342,320)]
a, fail = cut(h, FH, HPOLY, er=41, di=31, it=6)
# fade the cuff upward into the sleeve so the wrist dissolves into her (light) skirt/coat rather than ending on a hard line
yy = np.mgrid[0:h.shape[0], 0:h.shape[1]][0].astype(np.float32)
a = (a.astype(np.float32) * np.clip((yy - 215) / 60, 0, 1)).astype(np.uint8)
cv2.imwrite(OUT + "piece-her_hand-mask.png", a); cv2.imwrite(OUT + "piece-her_hand-failmask.png", fail)
Image.fromarray(np.dstack([h, h, h, a]), "RGBA").save(OUT + "piece-her_hand.png")
ys, xs = np.nonzero(a > 127)
meta["her_hand"] = dict(source="V1 = LoC 2017831565, master crop v1-master-hand.png (8d04831u.tif x 4980..5740, y 6240..7190)",
                        bbox_src=[int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())], scale_to_plate=0.49,
                        note="her right gloved hand gripping the chair arm in V1; used right-handed at the box's right end and mirrored for the left end (scale 0.49 V1-master px -> plate-1440 px, from head-size ratio)",
                        fail_px=int((fail > 0).sum()), area=int((a > 127).sum()), limits="translate only (rides on the box), wrist roll +-4 deg")
# inpaint the vacated plate: heads by row-mirroring (wall/wainscot run horizontally), the rest by Telea
plate = g.copy()
hole = np.zeros_like(g)
for n in ("his_head", "his_arm", "pocket"):
    hole |= (cv2.imread(OUT + f"piece-{n}-mask.png", 0) > 20).astype(np.uint8) * 255
plate = cv2.inpaint(plate, cv2.dilate(hole, np.ones((9, 9), np.uint8)), 9, cv2.INPAINT_TELEA)
hh = cv2.dilate((cv2.imread(OUT + "piece-her_head-mask.png", 0) > 20).astype(np.uint8), np.ones((9, 9), np.uint8))
pf = plate.astype(np.float32)
for y in range(hh.shape[0]):
    xs_ = np.nonzero(hh[y])[0]
    if len(xs_) == 0: continue
    a0, b0 = xs_.min(), xs_.max(); span = b0 - a0 + 1
    src = pf[y, max(0, a0 - span):a0][::-1] if a0 > 0 else pf[y, b0 + 1:b0 + 1 + span]
    if len(src) < span: src = np.pad(src, (0, span - len(src)), mode="reflect")
    pf[y, a0:b0 + 1] = src[:span]
cv2.imwrite(OUT + "plate-inpainted.png", np.clip(pf, 0, 255).astype(np.uint8))
json.dump(dict(working_res=[1440, 1080], pieces=meta, method="cv2.grabCut GC_INIT_WITH_MASK, contour seeds, largest-component cleanup, 1.2px feather; plate inpaint: Telea + row-mirror behind her head"),
          open(OUT + "pieces.json", "w"), indent=1)
print(json.dumps({k: (v.get("area"), v.get("fail_px")) for k, v in meta.items()}))

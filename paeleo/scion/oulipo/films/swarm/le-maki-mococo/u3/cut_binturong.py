"""U3 · GrabCut cutout of the Brehm/Specht binturong (PD engraving), seeded by hand-placed scissor points.

Hand-placed scissor line (source px of r1/brehm265.jpg, 1280x1908) traced by eye on 20 px grids:
body + head + ear tufts + three visible legs (front-left, front-right, hind) + rump + tail column,
plus the curl of the tail and the BRANCH STUB it wraps (forced foreground: a strip of the engraved
trunk cut with the tail, so the tail visibly curls round a branch as in the engraving).
GrabCut decides the fur/grass edge inside a band around the scissor line; then hand cleanup at film scale.
Output: imagecue/binturong_src_rgba.png (source orientation), binturong_src_matte.png, grabcut_debug.png
"""
import numpy as np, cv2, json
from PIL import Image, ImageDraw
SRC = "/home/user/bolas/paeleo/scion/oulipo/films/sources/le-maki-mococo/r1/brehm265.jpg"
OUT = "/home/user/bolas/paeleo/scion/oulipo/films/sources/le-maki-mococo/imagecue/"

# scissor line, clockwise from the left ear tuft (image px)
BODY = [(84, 928), (120, 948), (150, 975), (178, 1000), (205, 975), (250, 950), (300, 938), (345, 925), (375, 905),
        (402, 902), (414, 960), (420, 998), (462, 975), (505, 935), (547, 890), (580, 852), (620, 810), (700, 790), (780, 778), (850, 768),
        (878, 745), (880, 690), (885, 652),
        # tail column rises from the rump
        (912, 600), (913, 540), (945, 515), (1007, 510), (1048, 555), (1052, 660),
        (1056, 760), (1052, 822), (1020, 860), (1000, 900), (985, 940), (960, 1000), (933, 1060), (905, 1105),
        (893, 1180), (882, 1250), (850, 1275), (842, 1318), (800, 1322), (752, 1318), (748, 1285), (760, 1250),
        (765, 1200), (787, 1158), (760, 1165), (713, 1190), (690, 1215), (680, 1260), (640, 1310), (605, 1345),
        (602, 1385), (582, 1412), (520, 1418), (478, 1398), (468, 1350), (440, 1335), (405, 1328), (350, 1330),
        (336, 1385), (318, 1430), (285, 1452), (255, 1482), (213, 1497), (180, 1486), (172, 1448), (205, 1424),
        (243, 1392), (250, 1330), (268, 1262), (270, 1208), (258, 1180), (225, 1172), (212, 1130), (176, 1122),
        (172, 1080), (170, 1030), (140, 990), (100, 950)]
# left ear tuft (fine hairs GrabCut drops), forced foreground
EAR = [(80, 926), (112, 922), (162, 952), (208, 968), (200, 1012), (165, 998), (120, 958)]
# tail curl + branch stub (cut as one strip of the engraving), forced foreground
CURL = [(612, 545), (626, 492), (672, 458), (740, 440), (835, 450), (905, 470), (945, 515), (913, 540), (912, 600),
        (885, 652), (840, 648), (780, 640), (700, 650), (660, 668), (624, 664), (605, 628)]

im = np.array(Image.open(SRC).convert("RGB"))
H, W = im.shape[:2]
def poly_mask(p):
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).polygon(p, fill=255); return np.array(m) > 0
body = poly_mask(BODY); curl = poly_mask(CURL) | poly_mask(EAR)
gray = cv2.cvtColor(im, cv2.COLOR_RGB2GRAY)
darkish = cv2.blur(gray, (17, 17)) < 95                      # the animal's fur mass is dense hatching
mask = np.full((H, W), cv2.GC_BGD, np.uint8)
band = cv2.dilate(body.astype(np.uint8), np.ones((15, 15), np.uint8)) > 0
mask[band] = cv2.GC_PR_BGD
mask[body] = cv2.GC_PR_FGD
inner = cv2.erode(body.astype(np.uint8), np.ones((31, 31), np.uint8)) > 0
mask[inner & darkish] = cv2.GC_FGD
mask[cv2.erode(body.astype(np.uint8), np.ones((71, 71), np.uint8)) > 0] = cv2.GC_FGD
mask[curl] = cv2.GC_FGD
ys, xs = np.nonzero(band | curl)
x0, y0, x1, y1 = xs.min() - 30, ys.min() - 30, xs.max() + 30, ys.max() + 30
sub = im[y0:y1, x0:x1].copy(); sm = mask[y0:y1, x0:x1].copy()
# GrabCut works on local texture energy, not raw hatching: feed a smoothed image (hatching -> tone)
feat = cv2.bilateralFilter(cv2.GaussianBlur(sub, (0, 0), 2.2), 9, 40, 9)
bgd = np.zeros((1, 65), np.float64); fgd = np.zeros((1, 65), np.float64)
cv2.grabCut(cv2.cvtColor(feat, cv2.COLOR_RGB2BGR), sm, None, bgd, fgd, 8, cv2.GC_INIT_WITH_MASK)
fg = ((sm == cv2.GC_FGD) | (sm == cv2.GC_PR_FGD)).astype(np.uint8)
gc_raw = fg.copy()
# --- hand cleanup at film scale (~0.27 film px per source px: 1 film px ~ 4 source px) ---
fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13)))   # close fur gaps
fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))     # drop grass slivers
n, lab, st, _ = cv2.connectedComponentsWithStats(fg)
fg = (lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])).astype(np.uint8)
ff = fg.copy(); fm = np.zeros((fg.shape[0] + 2, fg.shape[1] + 2), np.uint8); cv2.floodFill(ff, fm, (0, 0), 1); fg = fg | (1 - ff)
# scissor smoothing: a paper cut cannot follow single hairs; blur+threshold the matte (radius ~1 film px)
fg = (cv2.GaussianBlur(fg.astype(np.float32), (0, 0), 3.0) > 0.5).astype(np.uint8)
Image.fromarray(sub).save(OUT + "binturong_src_crop.png")
Image.fromarray(fg * 255).save(OUT + "binturong_src_matte.png")
# debug: GrabCut raw (red), final matte outline (green), scissor seeds (blue)
dbg = (sub * 0.55 + 100).astype(np.uint8)
dbg[fg > 0] = sub[fg > 0]
cnts, _ = cv2.findContours(fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
cv2.drawContours(dbg, cnts, -1, (0, 200, 0), 3)
cnts2, _ = cv2.findContours(gc_raw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
cv2.drawContours(dbg, cnts2, -1, (220, 0, 0), 1)
for p in BODY + CURL + EAR:
    cv2.circle(dbg, (int(p[0] - x0), int(p[1] - y0)), 4, (0, 0, 255), -1)
Image.fromarray(dbg).save(OUT + "grabcut_debug.png")
json.dump(dict(source=SRC, crop_origin=[int(x0), int(y0)], crop_size=[int(x1 - x0), int(y1 - y0)],
               scissor_points_body=BODY, scissor_points_curl_branch=CURL, scissor_points_ear_tuft=EAR,
               grabcut=dict(iters=8, init="mask", feature="gaussian 2.2 + bilateral", fgd="inner dark hatching + erode71 + curl/branch"),
               cleanup=["close 13", "open 9", "largest component", "fill holes", "gauss 3 threshold (scissor smoothing)"],
               matte_fraction=float(fg.mean()), grabcut_raw_fraction=float(gc_raw.mean())),
          open(OUT + "binturong_cut.json", "w"), indent=1)
print(x0, y0, x1, y1, fg.mean(), gc_raw.mean())

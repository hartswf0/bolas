"""CUTOUT-SURGEON (SCION #29 GrabCut, for #1 Gilliam / #32 FK rigs) for 99-ways-template, baseline b1.

Reads only decoded pixels (PIL / OpenCV) of foraged LoC files; nothing in them is executed.
Writes RGBA pieces (grey photograph + alpha), plates, a manifest with source bboxes, pivots (piece-local
pixel coords), nominal page scales and the one levels curve per source photograph; a contact sheet;
failure/QA masks. Run:  python3 -I pieces.py
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
CUT = HERE.parent                                   # films/swarm/99-ways-template/cutouts
ROOT = CUT.parents[3]                               # .../oulipo
SRC = ROOT / "films" / "sources" / "99-ways-template"
OUT = SRC / "cutout-surgeon"
PIECES = OUT / "pieces"
FAIL = CUT / "failures"
for d in (PIECES, FAIL):
    d.mkdir(parents=True, exist_ok=True)

PAPER = 247  # white scissor-margin paper (247,246,242) is applied by bake_margin()


# ------------------------------------------------------------------ one levels curve per source photo
def levels(a, lo, hi, gamma=1.0):
    a = np.clip((a.astype(np.float32) - lo) / float(hi - lo), 0, 1) ** gamma
    return np.clip(a * 255.0 + 0.5, 0, 255).astype(np.uint8)


def grab(img, rect, fg=(), bg=(), it=6, prbg=()):
    """box + scribble seeds -> GrabCut (GMM unary costs + contrast-sensitive pairwise term) -> binary mask"""
    c = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR) if img.ndim == 2 else img
    m = np.zeros(c.shape[:2], np.uint8)
    x, y, w, h = rect
    m[y:y + h, x:x + w] = cv2.GC_PR_FGD
    for p in prbg:
        cv2.fillPoly(m, [np.int32(p)], cv2.GC_PR_BGD)
    for p in fg:
        cv2.fillPoly(m, [np.int32(p)], cv2.GC_FGD)
    for p in bg:
        cv2.fillPoly(m, [np.int32(p)], cv2.GC_BGD)
    b1, f1 = np.zeros((1, 65)), np.zeros((1, 65))
    cv2.grabCut(c, m, None, b1, f1, it, cv2.GC_INIT_WITH_MASK)
    return np.where((m == 1) | (m == 3), 255, 0).astype(np.uint8)


def cleanup(m, close=5, hole_max=None):
    """alpha cleanup: close, keep the largest component (no background islands), fill enclosed holes"""
    if close:
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((close, close), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    if n > 1:
        big = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])
        m = np.where(lab == big, 255, 0).astype(np.uint8)
    inv = cv2.bitwise_not(m)
    n, lab, st, _ = cv2.connectedComponentsWithStats(inv)
    for i in range(1, n):
        x, y, w, h, a = st[i]
        inside = x > 0 and y > 0 and x + w < m.shape[1] and y + h < m.shape[0]
        if inside and (hole_max is None or a < hole_max):
            m[lab == i] = 255
    return m


def soften(m, r=1.2):
    """1-2 px anti-aliased edge (scissor cut, not a feathered halo)"""
    return cv2.GaussianBlur(m, (0, 0), r)


def ncomp(m):
    return int(cv2.connectedComponents((m > 127).astype(np.uint8))[0] - 1)


def grain_fill(img, hole, donor_shift=(0, 0), r=6):
    """repair: Telea low-frequency fill + native grain transplanted from an adjacent patch of the same photo
    (the high-pass of the donor region, shifted by donor_shift). No synthetic noise is added."""
    base = cv2.inpaint(img, hole, r, cv2.INPAINT_TELEA).astype(np.float32)
    src = img.astype(np.float32)
    hp = src - cv2.GaussianBlur(src, (0, 0), 3)
    dy, dx = donor_shift
    hp_s = np.roll(np.roll(hp, dy, 0), dx, 1)
    lowb = cv2.GaussianBlur(base, (0, 0), 3)
    out = np.where(hole > 0, lowb + hp_s, src)
    return np.clip(out, 0, 255).astype(np.uint8)


man = {"revision": "b1", "unit": "cutout-surgeon", "coords": "pivots are piece-local pixels (x right, y down) of the piece PNG; "
       "bbox_src is [x0,y0,x1,y1] in the named source raster; source raster -> original master given per source",
       "sources": {}, "pieces": {}, "plates": {}, "qa": {}}


def put(name, gray, alpha, bbox, pivots, source, levels_, scale, note="", extra=None):
    x0, y0, x1, y1 = [int(v) for v in bbox]
    g = gray[y0:y1, x0:x1]
    a = alpha[y0:y1, x0:x1]
    f = PIECES / f"{name}.png"
    cv2.imwrite(str(f), np.dstack([g, g, g, a]).astype(np.uint8))
    rec = {"file": str(f.relative_to(ROOT)), "source": source, "bbox_src": [x0, y0, x1, y1], "size": [x1 - x0, y1 - y0],
           "pivots_local": {k: [round(float(v[0] - x0), 1), round(float(v[1] - y0), 1)] for k, v in pivots.items()},
           "levels": levels_, "scale_to_page_nominal": scale, "alpha_components": ncomp(a), "note": note}
    if extra:
        rec.update(extra)
    man["pieces"][name] = rec
    return rec


# ================================================================== SOURCES
R_PATH = SRC / "test-shot" / "rothstein_master_s3.png"
R = cv2.imread(str(R_PATH), cv2.IMREAD_GRAYSCALE)                # 4360x3100
assert R.shape == (3100, 4360), R.shape
man["sources"]["rothstein"] = {
    "loc": "2017776093", "file": str(R_PATH.relative_to(ROOT)),
    "raster": "master 8b16710u.tif (13818x10504, 8-bit grey) rows 300..9600 and cols 480..13560, every 3rd row and column "
              "(fetched by HTTP multi-range in the test shot; parsed as data). raster(x,y) -> master(480+3x, 300+3y)",
    "orientation_check": None}

# orientation/registration check of the reassembly against the LoC service JPEG 8b16710v.jpg
V = cv2.imread(str(SRC / "loc" / "8b16710v.jpg"), cv2.IMREAD_GRAYSCALE)
sx = V.shape[1] / 13818.0
vc = V[int(300 * sx):int(9600 * sx), int(480 * sx):int(13560 * sx)]
rs = cv2.resize(R, (vc.shape[1], vc.shape[0]), interpolation=cv2.INTER_AREA)
cc = {}
for lab_, im in {"as_is": rs, "flip_lr": rs[:, ::-1], "flip_ud": rs[::-1], "rot180": rs[::-1, ::-1]}.items():
    cc[lab_] = round(float(np.corrcoef(im.ravel().astype(np.float32), vc.ravel().astype(np.float32))[0, 1]), 4)
man["sources"]["rothstein"]["orientation_check"] = {"pearson_vs_8b16710v": cc, "pass": max(cc, key=cc.get) == "as_is"}
print("orientation", cc)

# levels: shirt at ~250, tie / cupboard interior at ~10. Measured on the raster, one curve for every crop.
shirt = R[2250:2550, 2650:2850]
interior = R[1950:2400, 1700:2000]                                # dark beadboard behind the desk
lo_r, hi_r = float(np.percentile(interior, 50)), float(np.percentile(shirt, 60))
ROTH_LEVELS = [round(lo_r, 1), round(hi_r, 1), 0.85]
Rl = levels(R, *ROTH_LEVELS)
man["sources"]["rothstein"]["levels"] = {"lo_hi_gamma": ROTH_LEVELS, "how": "lo = median of the dark beadboard (-> black), hi = 60th pct of the shirt front (-> paper white), gamma 0.85 lifts the mids toward high-key"}

# ================================================================== THE CLERK (Rothstein)
# seeds in raster coords (looked at on crops with coordinate ticks)
rect = (2150, 1500, 1700, 1180)                                   # x,y,w,h ; desk line ~ y 2640
fg = [[(2900, 1640), (3100, 1640), (3100, 1700), (2900, 1700)],     # hair
      [(2900, 1800), (3080, 1800), (3080, 2000), (2900, 2000)],     # face
      [(2800, 2200), (2950, 2200), (2950, 2550), (2800, 2550)],     # shirt front
      [(3000, 2200), (3050, 2200), (3050, 2500), (3000, 2500)],     # tie
      [(3250, 2080), (3380, 2080), (3380, 2160), (3250, 2160)],     # fist
      [(3500, 2350), (3620, 2350), (3620, 2480), (3500, 2480)],     # sleeve
      [(2420, 2400), (2560, 2400), (2560, 2500), (2420, 2500)],     # left sleeve
      [(2250, 2690), (2330, 2690), (2330, 2760), (2250, 2760)]]     # left fist on desk
bg = [[(2160, 1510), (2700, 1510), (2700, 1560), (2160, 1560)],
      [(3450, 1510), (3840, 1510), (3840, 1950), (3450, 1950)],
      [(2160, 1600), (2560, 1600), (2560, 2150), (2160, 2150)],
      [(3760, 2050), (3840, 2050), (3840, 2600), (3760, 2600)],
      [(2700, 2660), (3700, 2660), (3700, 2680), (2700, 2680)]]       # ledger / desk edge
clerk = grab(R, rect, fg, bg, it=6)
# the hair against the dark cupboard and the pencil are poorly separated by colour: add them by contour markup
cv2.ellipse(clerk, (3010, 1700), (165, 160), 0, 180, 360, 255, -1, cv2.LINE_AA)
pencil_line = ((3138, 1772), (3214, 1995))
cv2.line(clerk, pencil_line[0], pencil_line[1], 255, 17, cv2.LINE_AA)
clerk[2665:] = 0                                                  # below the desk line belongs to the desk
desk_arm = np.zeros_like(clerk)                                   # his left forearm+fist lie on the desk: keep them
cv2.fillPoly(desk_arm, [np.int32([(2190, 2580), (2420, 2560), (2460, 2660), (2420, 2800), (2190, 2810)])], 255)
clerk = np.where(desk_arm > 0, grab(R, (2150, 2500, 450, 360), [[(2250, 2690), (2330, 2690), (2330, 2760), (2250, 2760)]],
                                     [[(2160, 2510), (2200, 2510), (2200, 2560), (2160, 2560)]], it=5), clerk)
clerk = cleanup(clerk, 7, hole_max=6000)
cv2.imwrite(str(FAIL / "clerk_mask_full.png"), clerk)

# FK split (contour markup): head above the collar; pencil arm = sleeve from shoulder + forearm + fist + pencil
head_poly = np.int32([(2780, 1480), (3260, 1480), (3245, 1850), (3200, 1990), (3150, 2060), (3080, 2110),
                      (2990, 2135), (2900, 2110), (2830, 2050), (2780, 1900)])
arm_poly = np.int32([(3128, 1760), (3150, 1755), (3225, 1960), (3300, 2030), (3420, 2040), (3470, 2140),
                     (3520, 2250), (3700, 2420), (3790, 2560), (3800, 2665), (3560, 2665), (3470, 2560),
                     (3420, 2330), (3330, 2250), (3250, 2200), (3200, 2120), (3175, 2050)])
hp = np.zeros_like(clerk); cv2.fillPoly(hp, [head_poly], 255)
ap = np.zeros_like(clerk); cv2.fillPoly(ap, [arm_poly], 255)
arm = cleanup(cv2.bitwise_and(clerk, ap), 3)
head = cleanup(cv2.bitwise_and(cv2.bitwise_and(clerk, hp), cv2.bitwise_not(cv2.dilate(arm, np.ones((3, 3), np.uint8)))), 3)
torso = cleanup(cv2.bitwise_and(clerk, cv2.bitwise_not(cv2.bitwise_or(head, arm))), 3)
# torso hidden under the arm: the body side (shirt) up to a body line from the armpit down to the desk
body = np.zeros_like(clerk)
cv2.fillPoly(body, [np.int32([(3080, 2140), (3260, 2190), (3400, 2290), (3470, 2640), (3060, 2665)])], 255)
under = cv2.bitwise_and(cv2.bitwise_and(arm, body), cv2.bitwise_not(head))
torso = cleanup(cv2.bitwise_or(torso, under), 3)
# repair the hidden shirt with the shirt's own grain (donor: shirt 160 px to the left)
Tg = grain_fill(Rl, cv2.dilate(under, np.ones((9, 9), np.uint8)), donor_shift=(0, -160), r=9)
# repair the head where the pencil crossed the temple/ear: narrow line mask; donor: skin 26 px to the left
pen = np.zeros_like(clerk); cv2.line(pen, pencil_line[0], pencil_line[1], 255, 21, cv2.LINE_AA)
pen = cv2.bitwise_and(pen, hp)
Hg = grain_fill(Rl, pen, donor_shift=(0, -26), r=5)
# fist over the right cheek/ear edge: anything the arm covered inside the head polygon is repaired the same way
fist_over = cv2.bitwise_and(cv2.dilate(arm, np.ones((5, 5), np.uint8)), cv2.bitwise_and(hp, cv2.bitwise_not(pen)))
Hg = grain_fill(Hg, fist_over, donor_shift=(0, -30), r=5)
head = cleanup(cv2.bitwise_or(head, cv2.bitwise_and(cv2.bitwise_or(pen, fist_over), cv2.erode(hp, np.ones((25, 25), np.uint8)) &
                                                     cv2.dilate(head, np.ones((31, 31), np.uint8)))), 3)
cv2.imwrite(str(FAIL / "head_pencil_repair_mask.png"), cv2.bitwise_or(pen, fist_over))
cv2.imwrite(str(FAIL / "torso_under_arm_repair_mask.png"), under)

collar, shoulder, elbow = (2995, 2125), (3390, 2265), (3700, 2585)
fist_c, tip = (3330, 2110), pencil_line[0]
chin = (3010, 2045)
R_SC = {"P1_P3_medium_wide": 0.19, "P4_P5_P6": 0.25, "P7_P8_medium_close": 0.33}
src_r = "rothstein (LoC 2017776093)"


def bb(m, pad=6):
    ys, xs = np.nonzero(m)
    return (max(xs.min() - pad, 0), max(ys.min() - pad, 0), min(xs.max() + pad + 1, m.shape[1]), min(ys.max() + pad + 1, m.shape[0]))


put("rothstein.clerk.torso", Tg, soften(torso), bb(torso), {"collar": collar, "shoulder": shoulder, "root_desk": (3000, 2660),
    "left_fist_on_desk": (2290, 2730)}, src_r, ROTH_LEVELS, R_SC,
    "shirt hidden under the raised arm repaired (Telea low band + same-photo shirt grain, mask in cutouts/failures). Includes his "
    "left arm resting on the desk. Root sits on the desk line; translate the root for the sliding Gilliam walk.",
    {"parent": None, "children": ["rothstein.clerk.head", "rothstein.clerk.pencil_arm"]})
put("rothstein.clerk.head", Hg, soften(head), bb(head), {"collar": collar, "chin": chin, "eyes": (3000, 1880), "mouth": (3000, 1985),
    "pencil_tip_target_at_chin": (3045, 2040)}, src_r, ROTH_LEVELS, R_SC,
    "hinged at the collar (pivot); pencil strip on the temple and the fist edge over the ear repaired with same-photo skin grain. "
    "Gaze is DOWN (reading) in the only Randolph frame; see bubley82.agent.head for a matched FSA head with a level, aside gaze.",
    {"parent": "rothstein.clerk.torso", "joint": "collar"})
put("rothstein.clerk.pencil_arm", Rl, soften(arm), bb(arm), {"shoulder": shoulder, "elbow": elbow, "fist": fist_c, "pencil_tip": tip},
    src_r, ROTH_LEVELS, R_SC,
    "sleeve from the shoulder seam + forearm + fist + pencil, one piece; rotate about 'shoulder'. Pencil-to-chin pose: rotate about "
    "the shoulder so pencil_tip meets head.pencil_tip_target_at_chin (see qa.pencil_to_chin).",
    {"parent": "rothstein.clerk.torso", "joint": "shoulder"})

# fingers retained (QA): convexity defects along the fist contour
fz = arm[2010:2230, 3220:3460]
cs, _ = cv2.findContours(fz, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
c = max(cs, key=cv2.contourArea)
dfx = cv2.convexityDefects(c, cv2.convexHull(c, returnPoints=False))
man["qa"]["fingers"] = {"region_src": [3220, 2010, 3460, 2230],
                        "deep_convexity_defects_gt8px": int(0 if dfx is None else (dfx.reshape(-1, 4)[:, 3] / 256 > 8).sum()),
                        "note": "source shows the pencil fist with 3 curled fingers + thumb; notches between knuckles kept"}
# pencil-to-chin: rotation about the shoulder that brings the tip nearest the chin target (2-bone not needed if within 25 px)
tv = np.array(tip, float) - shoulder
cv_ = np.array((3045, 2040), float) - shoulder
ang = float(np.degrees(np.arctan2(cv_[1], cv_[0]) - np.arctan2(tv[1], tv[0])))
man["qa"]["pencil_to_chin"] = {"rotate_about_shoulder_deg": round(ang, 1),
                               "tip_radius_px": round(float(np.linalg.norm(tv)), 1), "chin_radius_px": round(float(np.linalg.norm(cv_)), 1),
                               "residual_px_after_rotation": round(abs(float(np.linalg.norm(tv) - np.linalg.norm(cv_))), 1),
                               "note": "positive = clockwise on screen (y down). Residual is radial: close it by sliding the arm piece "
                                       "along the shoulder->chin line (scapula shrug) or by the 2-bone split below."}
# 2-bone option: forearm+fist+pencil separate, elbow pivot
fore_poly = np.int32([(3128, 1760), (3150, 1755), (3225, 1960), (3300, 2030), (3420, 2040), (3500, 2180), (3640, 2380),
                      (3790, 2560), (3800, 2665), (3600, 2665), (3520, 2520), (3380, 2330), (3250, 2200), (3200, 2120), (3175, 2050)])
fp_ = np.zeros_like(clerk); cv2.fillPoly(fp_, [fore_poly], 255)
fore = cleanup(cv2.bitwise_and(arm, fp_), 3)
put("rothstein.clerk.forearm_pencil", Rl, soften(fore), bb(fore), {"elbow": elbow, "fist": fist_c, "pencil_tip": tip}, src_r, ROTH_LEVELS,
    R_SC, "optional 2-bone split of pencil_arm (child of pencil_arm at 'elbow'); use either pencil_arm alone or pencil_arm minus this",
    {"parent": "rothstein.clerk.pencil_arm", "joint": "elbow"})

# ================================================================== SET PIECES (Rothstein)
# ticket racks (the slanted rack case) ------------------------------------------------
rk = grab(R, (1590, 250, 1040, 1660), [[(1700, 450), (2380, 450), (2380, 1500), (1700, 1500)]],
          [[(1595, 255), (1640, 255), (1640, 1900), (1595, 1900)], [(2590, 255), (2625, 255), (2625, 1100), (2590, 1100)]], it=5)
rk = cleanup(rk, 9)
put("rothstein.ticket_racks", Rl, soften(rk), bb(rk), {"base_center": (2120, 1890)}, src_r, ROTH_LEVELS, R_SC,
    "the slanted ticket-rack case with its pigeonholes of white ticket stock (clean whites + black frame)")
# window: TICKET OFFICE glass with its frame (rectangular cut, no GrabCut needed: the frame is the edge)
wx0, wy0, wx1, wy1 = 40, 760, 1480, 1960
wm = np.zeros_like(R); wm[wy0:wy1, wx0:wx1] = 255
# lamp hangs in front of the glass: remove it from the window plate (grain fill), it becomes its own piece
lamp = grab(R, (400, 1200, 400, 330), [[(470, 1330), (700, 1330), (700, 1400), (470, 1400)]],
            [[(405, 1205), (480, 1205), (480, 1260), (405, 1260)], [(720, 1205), (795, 1205), (795, 1260), (720, 1260)]], it=5)
lamp = cleanup(lamp, 5)
cord = np.zeros_like(R)
cv2.line(cord, (572, 60), (575, 1290), 255, 15, cv2.LINE_AA)
lamp = cleanup(cv2.bitwise_or(lamp, cord), 3)
Wg = grain_fill(Rl, cv2.dilate(lamp, np.ones((7, 7), np.uint8)), donor_shift=(0, 60), r=7)
put("rothstein.window", Wg, wm, (wx0, wy0, wx1, wy1), {"glass_center": (700, 1350)}, src_r, ROTH_LEVELS, R_SC,
    "TICKET OFFICE glass, frame and counter shelf; the pendant lamp and its cord removed (same-photo grain fill) so the lamp swings")
put("rothstein.lamp", Rl, soften(lamp), bb(lamp), {"cord_top": (572, 60), "shade_center": (585, 1380)}, src_r, ROTH_LEVELS, R_SC,
    "pendant lamp with its twisted cord; pivot at cord_top for the 2-pose draught sway (S6)")
# cupboard: the tall two-leaf cupboard right of the window; left leaf = cupboard_door (jamb on its LEFT edge as seen)
cupb = (3060, 690, 4290, 1915)
cm = np.zeros_like(R); cm[cupb[1]:cupb[3], cupb[0]:cupb[2]] = 255
put("rothstein.cupboard", Rl, cm, cupb, {"left_leaf_jamb_top": (3170, 790), "left_leaf_jamb_bottom": (3170, 1715)}, src_r, ROTH_LEVELS, R_SC,
    "closed cupboard (rectangular cut). NB the clerk's head overlaps its lower left in the photo: use plate rothstein.desk_empty for a clean one")
door = (3170, 790, 3615, 1720)
put("rothstein.cupboard_door", Rl, np.full_like(R, 255), door, {"jamb_top": (3170, 790), "jamb_bottom": (3170, 1720),
    "key_hook": (3330, 1180)}, src_r, ROTH_LEVELS, R_SC,
    "left leaf of the cupboard, cut on its own edges; hinge (jamb) is its left edge. Open by scaleX 1.0->0.25 about the jamb.",
    {"joint": "jamb", "children": ["key"]})
sdoor = (3830, 790, 4260, 1720)
put("rothstein.service_door", Rl, np.full_like(R, 255), sdoor, {"hinge_top": (4260, 790), "hinge_bottom": (4260, 1720)}, src_r,
    ROTH_LEVELS, R_SC, "the cupboard's right leaf used as the closed SERVICE door (it never opens; the page-cartoonist's sign-card goes on it). "
    "No room door is visible in the Randolph frame (absence logged).")

# ================================================================== EMPTY-DESK PLATE (clerk removed)
gone = cv2.dilate(clerk, np.ones((19, 19), np.uint8))
plate = Rl.copy()
ys, xs = np.nonzero(gone)
# structured fill: rows above the counter line (y<1935) take pixels from the same row to the RIGHT of the hole (cupboard base,
# counter edge run horizontally); rows below (dark beadboard behind him) take the same row shifted LEFT by whole plank periods.
bead = Rl[2000:2550, 1550:2150].astype(np.float32).mean(0)
bead -= bead.mean()
ac = np.correlate(bead, bead, "full")[len(bead) - 1:]
period = int(np.argmax(ac[40:200]) + 40)
for y in range(ys.min(), min(ys.max() + 1, 2665)):
    row = gone[y]
    hx = np.nonzero(row)[0]
    if not len(hx):
        continue
    a, b = hx.min(), hx.max()
    w = b - a + 1
    if y < 1935:
        shift = w + 12
        src = np.clip(np.arange(a, b + 1) + shift, 0, R.shape[1] - 1)
        src = np.where(src > 4250, np.arange(a, b + 1) - (w + 12), src)
    else:
        k = int(np.ceil((w + 12) / period))
        src = np.arange(a, b + 1) - k * period
        src = np.where(src < 1520, src + 2 * k * period, src)
    plate[y, a:b + 1] = Rl[y, np.clip(src, 0, R.shape[1] - 1)]
desk_rows = gone.copy(); desk_rows[:2665] = 0
plate = grain_fill(plate, desk_rows, donor_shift=(0, -420), r=11)
# seam band: blend 6 px across the hole edge
edge = cv2.subtract(cv2.dilate(gone, np.ones((7, 7), np.uint8)), cv2.erode(gone, np.ones((7, 7), np.uint8)))
plate = np.where(edge > 0, cv2.GaussianBlur(plate, (0, 0), 1.6), plate).astype(np.uint8)
pf = PIECES / "rothstein.desk_empty.png"
cv2.imwrite(str(pf), plate)
man["plates"]["rothstein.desk_empty"] = {"file": str(pf.relative_to(ROOT)), "source": src_r, "bbox_src": [0, 0, 4360, 3100],
    "levels": ROTH_LEVELS, "how": f"clerk mask dilated 19 px removed. Above the counter line (y<1935): same-row transplant from the right "
    f"(cupboard base). Below: same-row transplant shifted by whole beadboard plank periods ({period} px, autocorrelation). "
    "Desk-top rows (y>=2665): Telea low band + same-photo grain. 6 px seam blend.", "repair_mask": "cutouts/failures/desk_empty_mask.png"}
cv2.imwrite(str(FAIL / "desk_empty_mask.png"), gone)
Rp = PIECES / "rothstein.full_levelled.png"
cv2.imwrite(str(Rp), Rl)
man["plates"]["rothstein.full_levelled"] = {"file": str(Rp.relative_to(ROOT)), "source": src_r, "bbox_src": [0, 0, 4360, 3100],
                                            "levels": ROTH_LEVELS, "how": "the whole raster with its one levels curve (for any further crop)"}

# ================================================================== CLOCK (Rothstein, Smuggler's Notch, 1937)
C = cv2.imread(str(OUT / "raw" / "clock_master_s4.png"), cv2.IMREAD_GRAYSCALE)   # 1375x2100
man["sources"]["clock"] = {"loc": "2017776111", "file": str((OUT / "raw" / "clock_master_s4.png").relative_to(ROOT)),
                           "raster": "master 8b16723u.tif (13084x16388) rows 800..9200, cols 3900..9400, every 4th; raster(x,y) -> master(3900+4x, 800+4y)"}
dial = C[300:1050, 280:1050]
CL = [round(float(np.percentile(C[150:350, 200:300], 10)), 1), round(float(np.percentile(dial, 80)), 1), 0.95]
Cl = levels(C, *CL)
man["sources"]["clock"]["levels"] = {"lo_hi_gamma": CL, "how": "lo = 10th pct of the dark case rim, hi = 80th pct of the dial"}
# the hub: darkest blob near the dial centre
hub = (666, 651)
sub = cv2.GaussianBlur(C[hub[1] - 40:hub[1] + 40, hub[0] - 40:hub[0] + 40], (0, 0), 4)
yy, xx = np.unravel_index(np.argmin(sub), sub.shape)
hub = (hub[0] - 40 + int(xx), hub[1] - 40 + int(yy))
# case + dial + pendulum box (GrabCut), the whip behind it excluded
case = grab(C, (40, 20, 1260, 2060), [[(300, 400), (1000, 400), (1000, 1000), (300, 1000)], [(450, 1500), (850, 1500), (850, 1800), (450, 1800)]],
            [[(1150, 60), (1370, 60), (1370, 700), (1150, 700)], [(0, 300), (60, 300), (60, 500), (0, 500)]], it=6)
case = cleanup(case, 9)
# hands: dark thin strokes inside the dial, connected to the hub; hour (short, ~toward XII) and minute (long, toward II)
dialmask = np.zeros_like(C); cv2.circle(dialmask, hub, 400, 255, -1)
dark = ((cv2.GaussianBlur(C, (0, 0), 1.0) < np.percentile(dial, 25)) & (dialmask > 0)).astype(np.uint8) * 255


def hand_mask(angle_deg, length, width):
    m = np.zeros_like(C)
    a = np.radians(angle_deg)
    p2 = (int(hub[0] + length * np.sin(a)), int(hub[1] - length * np.cos(a)))
    p0 = (int(hub[0] - 40 * np.sin(a)), int(hub[1] + 40 * np.cos(a)))
    cv2.line(m, p0, p2, 255, width)
    return m, p2


# find hand angles by ray darkness
angs = np.arange(0, 360, 1.0)
score = []
for a in angs:
    r = np.arange(60, 330)
    px = (hub[0] + r * np.sin(np.radians(a))).astype(int); py = (hub[1] - r * np.cos(np.radians(a))).astype(int)
    score.append(float((dark[py, px] > 0).mean()))
score = np.array(score)
order = np.argsort(-score)
a1 = angs[order[0]]
a2 = next(angs[i] for i in order if min(abs(angs[i] - a1), 360 - abs(angs[i] - a1)) > 25)


def reach(a):
    r = np.arange(40, 420)
    px = (hub[0] + r * np.sin(np.radians(a))).astype(int); py = (hub[1] - r * np.cos(np.radians(a))).astype(int)
    on = dark[py, px] > 0
    last = 40
    for i, v in enumerate(on):
        if v: last = r[i]
        elif r[i] - last > 25: break
    return int(last)


L1, L2 = reach(a1), reach(a2)
(minute_a, minute_L), (hour_a, hour_L) = ((a1, L1), (a2, L2)) if L1 > L2 else ((a2, L2), (a1, L1))
mm, mtip = hand_mask(minute_a, minute_L + 8, 30)
hm, htip = hand_mask(hour_a, hour_L + 8, 46)
mhand = cleanup(cv2.bitwise_and(dark, mm), 3); hhand = cleanup(cv2.bitwise_and(dark, hm), 3)
cv2.circle(mhand, hub, 16, 255, -1); cv2.circle(hhand, hub, 22, 255, -1)
mhand = cv2.dilate(mhand, np.ones((3, 3), np.uint8)); hhand = cv2.dilate(hhand, np.ones((3, 3), np.uint8))
# face without hands: dial repaired under both hands (dial grain donor 18 px across)
face_g = grain_fill(Cl, cv2.dilate(cv2.bitwise_or(mhand, hhand), np.ones((7, 7), np.uint8)), donor_shift=(18, 18), r=6)
put("clock.face", face_g, soften(case), bb(case), {"hub": hub, "hang_top": (hub[0], 30)}, "clock (LoC 2017776111)", CL,
    {"P5_wall_clock": 0.22}, "the whole schoolhouse clock (case, dial, pendulum box) with both hands removed and the dial repaired; "
    "the whip hanging behind it is excluded.")
put("clock.hour", Cl, soften(hhand), bb(hhand, 4), {"hub": hub, "tip": htip}, "clock (LoC 2017776111)", CL, {"P5_wall_clock": 0.22},
    "hour hand, pivot 'hub'", {"angle_in_photo_deg_cw_from_12": float(hour_a), "set_to_4_10_rotate_deg": round(125.0 - float(hour_a), 1)})
put("clock.minute", Cl, soften(mhand), bb(mhand, 4), {"hub": hub, "tip": mtip}, "clock (LoC 2017776111)", CL, {"P5_wall_clock": 0.22},
    "minute hand, pivot 'hub'", {"angle_in_photo_deg_cw_from_12": float(minute_a), "set_to_4_10_rotate_deg": round(60.0 - float(minute_a), 1),
                                 "S5_tick_from_4_09": round(54.0 - float(minute_a), 1)})
man["qa"]["clock_hands"] = {"photo_time_reads": f"hour {hour_a:.0f} deg, minute {minute_a:.0f} deg (cw from XII)", "hub": hub,
                            "target": "4:10 = hour 125 deg, minute 60 deg"}
cv2.imwrite(str(FAIL / "clock_hands_mask.png"), cv2.bitwise_or(mhand, hhand))

# ================================================================== KEY (ANRC 1922)
K = cv2.imread(str(SRC / "test-shot" / "14940v.jpg"), cv2.IMREAD_GRAYSCALE)
KL = [22, 212, 0.95]
Kl = levels(K, *KL)
km = grab(K, (295, 115, 205, 735), [[(395, 300), (420, 300), (420, 820), (395, 820)], [(315, 700), (360, 700), (360, 780), (315, 780)]],
          [[(340, 160), (455, 160), (455, 225), (340, 225)]])
km = cleanup(km, 3, hole_max=0)
ring_in = np.zeros_like(km); cv2.ellipse(ring_in, (398, 190), (74, 52), 0, 0, 360, 255, -1)
km = np.where((ring_in > 0) & (K > 150), 0, km).astype(np.uint8)
man["sources"]["key"] = {"loc": "2017679951", "file": "films/sources/99-ways-template/test-shot/14940v.jpg", "levels": {"lo_hi_gamma": KL}}
put("key", Kl, soften(km), bb(km, 3), {"ring_top": (398, 132)}, "key (LoC 2017679951)", KL, {"P7_P8": 0.2},
    "bow ring hole kept open (background); hangs from the door's key_hook by 'ring_top'",
    {"parent": "rothstein.cupboard_door", "joint": "key_hook"})

# ================================================================== VISITOR (Bubley 1943)
B = cv2.imread(str(SRC / "loc" / "8d33109v.jpg"), cv2.IMREAD_GRAYSCALE)
BL = [round(float(np.percentile(B[300:800, 520:715], 3)), 1), round(float(np.percentile(B[300:800, 520:715], 97)), 1), 1.0]
Bl = levels(B, *BL)
vm = grab(B, (515, 280, 205, 545), [[(600, 320), (640, 320), (640, 400), (600, 400)], [(580, 450), (670, 450), (670, 650), (580, 650)],
                                    [(620, 700), (660, 700), (660, 780), (620, 780)]],
          [[(515, 282), (545, 282), (545, 330), (515, 330)], [(690, 282), (718, 282), (718, 330), (690, 330)]], it=6)
vm = cleanup(vm, 5)
man["sources"]["bubley_visitor"] = {"loc": "2017861739", "file": "films/sources/99-ways-template/loc/8d33109v.jpg", "levels": {"lo_hi_gamma": BL}}
put("bubley.visitor", Bl, soften(vm), bb(vm, 3), {"feet": (625, 812), "head": (625, 300)}, "bubley_visitor (LoC 2017861739)", BL,
    {"P4_behind_glass": 0.9}, "1024-px service JPEG (she is small and soft behind the glass layer, so the master is not needed)")

# ================================================================== MATCHED FSA HEAD (Bubley 1943, Washington Court House)
A = cv2.imread(str(OUT / "raw" / "bubley82_head_master.png"), cv2.IMREAD_GRAYSCALE)   # 1300x1600 window of 8d33082u.tif
AL = [round(float(np.percentile(A[1100:1550, 400:560], 20)), 1), round(float(np.percentile(A[1000:1400, 700:1100], 80)), 1), 0.92]
Al = levels(A, *AL)
man["sources"]["bubley82"] = {"loc": "2017861713", "file": str((OUT / "raw" / "bubley82_head_master.png").relative_to(ROOT)),
                              "raster": "master 8d33082u.tif (4617x4710) rows 1700..3300, cols 2100..3400 at full resolution",
                              "levels": {"lo_hi_gamma": AL}}
s = A.shape[1] / 650.0                                  # seed coords were read on a 650-wide preview
P = lambda pts: [(int(x * s), int(y * s)) for x, y in pts]
am = grab(A, tuple(int(v * s) for v in (140, 95, 300, 400)),
          [P([(220, 170), (330, 170), (330, 330), (220, 330)]), P([(260, 380), (320, 380), (320, 430), (260, 430)])],
          [P([(140, 95), (180, 95), (180, 140), (140, 140)]), P([(415, 120), (440, 120), (440, 300), (415, 300)]),
           P([(140, 250), (160, 250), (160, 400), (140, 400)])], it=6)
am[int(455 * s):] = 0
am = cleanup(am, 5)
put("bubley82.agent.head", Al, soften(am), bb(am), {"collar": P([(285, 455)])[0], "chin": P([(270, 400)])[0], "eyes": P([(240, 245)])[0]},
    "bubley82 (LoC 2017861713)", AL, {"P8_medium_close": 0.36},
    "CANDIDATE replacement head (Gilliam substitution): a matched FSA ticket agent (glasses, white coat, dark tie) whose gaze is level and "
    "off to his right, i.e. away from the key. A different man from the Randolph agent: use only if the director accepts the swap.")

# ================================================================== scissor-margin helper output + contact sheet
def bake_margin(rgba, px):
    """white scissor margin of `px` pixels (in the piece's own pixels) around the alpha, paper (247,246,242), slightly irregular"""
    a = rgba[..., 3]
    pad = px + 4
    rgba = cv2.copyMakeBorder(rgba, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=(0, 0, 0, 0))
    a = rgba[..., 3]
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * px + 1, 2 * px + 1))
    m = cv2.dilate((a > 127).astype(np.uint8) * 255, k)
    m = cv2.approxPolyDP if False else m
    m = soften(m, 0.9)
    out = np.zeros_like(rgba)
    out[..., 0], out[..., 1], out[..., 2] = 242, 246, 247   # BGR
    out[..., 3] = m
    al = a[..., None].astype(np.float32) / 255
    out[..., :3] = (rgba[..., :3] * al + out[..., :3] * (1 - al)).astype(np.uint8)
    return out


tiles = []
for name, rec in man["pieces"].items():
    im = cv2.imread(str(ROOT / rec["file"]), cv2.IMREAD_UNCHANGED)
    sc = (rec["scale_to_page_nominal"] or {"x": 0.25})
    s0 = list(sc.values())[-1]
    mpx = max(2, int(round(8 / s0)))
    mb = bake_margin(im, mpx)
    cv2.imwrite(str(PIECES / f"{name}.margin.png"), mb)
    rec["file_with_margin"] = str((PIECES / f"{name}.margin.png").relative_to(ROOT))
    rec["margin_px_local"] = mpx
    a = mb[..., 3:4].astype(np.float32) / 255
    chk = np.where(((np.indices(mb.shape[:2]).sum(0) // 24) % 2)[..., None] == 0, 120, 70).astype(np.float32)
    comp = mb[..., :3] * a + chk * (1 - a)
    for k, (px, py) in rec["pivots_local"].items():
        cv2.circle(comp, (int(px + mpx + 4), int(py + mpx + 4)), max(4, int(6 / s0 / 3)), (0, 0, 255), -1)
    h = 360
    t = cv2.resize(comp.astype(np.uint8), (max(40, int(comp.shape[1] * h / comp.shape[0])), h), interpolation=cv2.INTER_AREA)
    t = cv2.copyMakeBorder(t, 0, 24, 0, 8, cv2.BORDER_CONSTANT, value=(255, 255, 255))
    cv2.putText(t, name.replace("rothstein.", "r.")[:30], (4, h + 17), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1)
    tiles.append(t)
rows, row, wsum = [], [], 0
for t in tiles:
    if wsum + t.shape[1] > 2400 and row:
        rows.append(row); row, wsum = [], 0
    row.append(t); wsum += t.shape[1]
rows.append(row)
W = max(sum(t.shape[1] for t in r) for r in rows)
sheet = np.vstack([np.hstack(r + [np.full((r[0].shape[0], W - sum(t.shape[1] for t in r), 3), 255, np.uint8)]) for r in rows])
pl = cv2.resize(cv2.cvtColor(plate, cv2.COLOR_GRAY2BGR), (W, int(3100 * W / 4360)), interpolation=cv2.INTER_AREA)
sheet = np.vstack([sheet, pl])
cv2.imwrite(str(CUT / "contact.jpg"), sheet, [cv2.IMWRITE_JPEG_QUALITY, 86])

# tone stats per piece (levelled, inside alpha): share of pixels L>220 and L<40, to steer plate choice toward high-key
for name, rec in man["pieces"].items():
    im = cv2.imread(str(ROOT / rec["file"]), cv2.IMREAD_UNCHANGED)
    g = im[..., 0][im[..., 3] > 127]
    rec["tone"] = {"pct_L_gt_220": round(float((g > 220).mean() * 100), 1), "pct_L_lt_40": round(float((g < 40).mean() * 100), 1),
                   "median": int(np.median(g))}
json.dump(man, open(HERE / "pieces_out.json", "w"), indent=1)
print(json.dumps({k: (v["alpha_components"], v["tone"]) for k, v in man["pieces"].items()}, indent=0))
print("period", period, "qa", man["qa"])

"""S5/S7 FLIGHT, repair round 2 -- SCION-29 cuts.

STAGE: LoC 2017714056 (Carl Mydans, Sept 1935, archival TIFF 8a00242a.tif, already on disk from r1):
the rooming-house stairwell, a dark flight with a lit handrail, turned balusters and a stringer.
  near plane = handrail + balusters (GrabCut: balusters vs the dark gaps, seeded by local contrast)
               + stringer/soffit below the lower string + left newel/post + right newel post.
  far plane  = the rest of the plate (risers, wall, pale ceiling), untouched: no fill is needed
               because nothing is removed from this plate.
CLIMBER: LoC 2017862340 (Esther Bubley, Jan 1943, master TIFF 8d33583u.tif) -- the S3/S4 sitter himself.
  UB  = head + torso (GrabCut, hair matting band), pivot at the hip.
  TH  = a thigh-length strip of his own pinstripe trouser leg, pivot at the hip end.
  SH  = a shin-length strip of the same leg, pivot at the knee end.
  (the second leg is a second instance of TH/SH, drawn behind; declared.)
  All climber pieces are flopped left-right (he faces up the flight) -- declared.
Run: python3 -I s5_cut.py"""
import sys
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/un-homme-qui-dort/editor-r3-build")
from ed3 import *  # noqa

# ------------------------------------------------------------------ stage (Mydans) ---
CROP = (1650, 1100, 3480, 2129)        # 1830 x 1029 plate px -> 960 x 540 (s = 0.5246, a downscale)
cx0, cy0, cx1, cy1 = CROP
s = W / (cx1 - cx0)
gM, curveM, _ = graded_plate("2017714056")
G = gM[cy0:cy1, cx0:cx1].copy()
hh, ww = G.shape


def scr2pl(pts):
    return [((x / s), (y / s)) for x, y in pts]      # screen px -> crop-local plate px


def line_y(xa, ya, xb, yb):
    return lambda x: ya + (x - xa) * (yb - ya) / (xb - xa)


rail_top = line_y(100, 336, 868, 103)
rail_bot = line_y(100, 394, 868, 180)
lstr_top = line_y(100, 514, 868, 363)
X = np.arange(ww) * 1.0
Y = np.arange(hh)[:, None] * 1.0
xs_scr = X * s
ys_scr = Y * s
in_x = (xs_scr >= 96) & (xs_scr <= 872)
rail = in_x & (ys_scr >= rail_top(xs_scr) - 3) & (ys_scr <= rail_bot(xs_scr) + 2)
zone = in_x & (ys_scr > rail_bot(xs_scr) + 2) & (ys_scr < lstr_top(xs_scr))
below = in_x & (ys_scr >= lstr_top(xs_scr))
left_post = poly_mask(G.shape, [scr2pl([(0, 283), (108, 283), (112, 372), (156, 540), (0, 540)])]) > 0
right_post = poly_mask(G.shape, [scr2pl([(864, 92), (878, 0), (960, 0), (960, 540), (803, 540), (820, 372), (864, 182)])]) > 0

# balusters vs gaps inside the baluster zone: seeds from local horizontal contrast, then GrabCut
g8 = (G * 255).astype(np.uint8)
loc = cv2.blur(G, (61, 9))
d = G - loc
fg_seed = zone & (d > 0.035)
bg_seed = zone & (d < -0.035)
m = np.full(G.shape, cv2.GC_BGD, np.uint8)
m[zone] = cv2.GC_PR_BGD
m[zone & (d > 0)] = cv2.GC_PR_FGD
m[fg_seed] = cv2.GC_FGD
m[bg_seed] = cv2.GC_BGD
m[rail | below | left_post | right_post] = cv2.GC_FGD
init = m.copy()
den = cv2.bilateralFilter(g8, 7, 0.08 * 255, 5)
bgd = np.zeros((1, 65), np.float64); fgd = np.zeros((1, 65), np.float64)
cv2.setRNGSeed(44)
cv2.grabCut(cv2.cvtColor(den, cv2.COLOR_GRAY2BGR), m, None, bgd, fgd, 5, cv2.GC_INIT_WITH_MASK)
hard = np.isin(m, (cv2.GC_FGD, cv2.GC_PR_FGD)).astype(np.uint8)
# balusters are near-vertical: open with a vertical element so single-row speckle in the gaps goes
bal = (hard & zone.astype(np.uint8))
bal_v = cv2.morphologyEx(bal, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25)))
bal_v = cv2.morphologyEx(bal_v, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 15)))
# balusters are straight turned posts: vote along their (estimated) common slant so each column of the
# zone is wholly baluster or wholly gap (removes the blotchy GrabCut edge; the change is a failure mask)
yy_, xx_ = np.nonzero(zone)
best = None
for th in np.deg2rad(np.arange(-20, 20.5, 1.0)):
    xp = np.round(xx_ - (yy_ - hh / 2) * np.tan(th)).astype(int)
    xp -= xp.min()
    tot = np.bincount(xp); on = np.bincount(xp, weights=bal_v[yy_, xx_])
    fr_ = on / np.maximum(tot, 1)
    v = float(np.var(fr_[tot > 20]))
    if best is None or v > best[0]:
        best = (v, th, xp, fr_)
_, TH_BAL, xp, fr_ = best
# label each slanted column by its own luminance against the local run of columns (a turned post is
# lit; the gap behind it is dark), with the GrabCut vote breaking near-ties
totc = np.bincount(xp); lum = np.bincount(xp, weights=G[yy_, xx_]) / np.maximum(totc, 1)
_pad = np.pad(lum, 30, mode="edge")
base = np.array([np.median(_pad[i:i + 61]) for i in range(len(lum))])
score = (lum - base) + 0.01 * (fr_ - 0.5)
score = np.convolve(score, np.ones(3) / 3, mode="same")
bal_c = np.zeros_like(bal_v); bal_c[yy_, xx_] = (score[xp] > 0).astype(np.uint8)
fail_vote = (bal_c != bal_v) & zone
bal_v = bal_c
near = np.clip(bal_v + rail + below + left_post + right_post, 0, 1).astype(np.uint8)
fail = (((bal != bal_v) & zone) | fail_vote).astype(np.uint8)
near_a = feather(near, 0.8)
near_a[rail | below | left_post | right_post] = 1.0

R = E3 / "rgba"; Mk = E3 / "masks"; F = E3 / "failure_masks"
save_gray(R / "S5r3_far_stair.png", G)
save_rgba(R / "S5r3_near_rail_balusters.png", G, near_a)
save_mask(Mk / "S5r3_near_mask.png", near)
save_mask(Mk / "S5r3_baluster_zone.png", zone)
save_mask(F / "S5r3_balusters_cleanup_changed.png", fail)
save_mask(F / "S5r3_grabcut_init_fg_seeds.png", (init == cv2.GC_FGD))
gap_frac = float(1 - bal_v[zone].mean())

# ------------------------------------------------------------------ climber (Bubley) ---
gB, curveB, _ = graded_plate("2017862340")
VX0, VY0, VS = 1634, 1906, 2.724          # view-grid -> plate (diagnostic grid used to place seeds)


def V(pts):
    return [(VX0 + x * VS, VY0 + y * VS) for x, y in pts]


REG = (3150, 1900, 4850, 3700)
rx0, ry0, rx1, ry1 = REG
B = gB[ry0:ry1, rx0:rx1].copy()
def L(pts):
    return [(x - rx0, y - ry0) for x, y in pts]

HALF = 0.5
Bs = cv2.resize(B, None, fx=HALF, fy=HALF, interpolation=cv2.INTER_AREA)
def Ls(pts):
    return [((x - rx0) * HALF, (y - ry0) * HALF) for x, y in pts]

fgB = [Ls(V([(800, 60), (930, 60), (950, 200), (800, 200)])),          # hair / face
       Ls(V([(800, 220), (930, 220), (960, 260), (820, 290)])),          # chin, collar
       Ls(V([(760, 300), (1100, 330), (1130, 560), (800, 520)])),       # jacket
       Ls(V([(620, 350), (780, 345), (800, 410), (640, 420)])),          # clasped hands
       Ls(V([(860, 520), (1150, 520), (1150, 600), (860, 600)]))]        # waist
bgB = [Ls(V([(590, 0), (760, 0), (740, 120), (760, 260), (650, 300), (590, 300)])),   # wall left of head
       Ls(V([(1000, 0), (1170, 0), (1170, 300), (1080, 260), (1010, 200), (990, 60)])),  # wall + cast shadow right
       Ls(V([(1165, 0), (1200, 0), (1200, 660), (1165, 660)])),
       Ls(V([(985, 105), (1085, 110), (1095, 255), (1005, 250), (988, 180)])),          # his cast shadow on the wall
       Ls(V([(590, 430), (700, 440), (790, 480), (880, 560), (880, 660), (590, 660)]))]  # lap / thighs
rectB = (0, 0, Bs.shape[1], Bs.shape[0])
hardB, initB = grabcut(Bs, rectB, fg_polys=fgB, bg_polys=bgB)
upper = poly_mask(Bs.shape, [Ls(V([(590, 0), (1200, 0), (1200, 615), (900, 570), (800, 480), (700, 432), (590, 425)]))])
hardB = hardB & upper
bodyB, failB, stB = cleanup(hardB, poly_mask(Bs.shape, fgB), max_hole=3000)
bodyB = cv2.resize(bodyB, (B.shape[1], B.shape[0]), interpolation=cv2.INTER_NEAREST)
UB_a, unkB = matting_band(B, bodyB, r=6, blend=0.7)
UB_g = decontaminate(B, UB_a)

# leg strips: oriented quads along his near trouser leg (plate px); internal cut lines are hidden
# behind the rail / balusters in staging. Each strip keeps only pixels GrabCut calls figure.
LEG = (1634 + 150 * VS, 1906 + 450 * VS, 1634 + 800 * VS, 1906 + 1000 * VS)
lx0, ly0, lx1, ly1 = [int(v) for v in LEG]
Lg = gB[ly0:ly1, lx0:lx1].copy()
def LL(pts):
    return [(VX0 + x * VS - lx0, VY0 + y * VS - ly0) for x, y in pts]
fgL = [LL([(330, 560), (680, 520), (690, 580), (360, 640)]), LL([(300, 680), (420, 680), (470, 950), (330, 950)])]
bgL = [LL([(560, 650), (800, 620), (800, 1000), (540, 1000)]), LL([(150, 450), (420, 450), (420, 500), (150, 520)])]
hardL, _ = grabcut(Lg, (0, 0, Lg.shape[1], Lg.shape[0]), fg_polys=fgL, bg_polys=bgL)
legm, failL, stL = cleanup(hardL, poly_mask(Lg.shape, fgL), max_hole=4000)
# thigh strip: from (700,555) [hip end] to (400,600) [knee end]; shin strip: (360,650) [knee] to (430,920)
def strip(p0, p1, wv):
    p0 = np.array(p0, float); p1 = np.array(p1, float)
    dvec = (p1 - p0) / np.linalg.norm(p1 - p0); n = np.array([-dvec[1], dvec[0]]) * wv / 2
    return LL([tuple(p0 + n), tuple(p1 + n), tuple(p1 - n), tuple(p0 - n)])
TH_pts = ((700, 556), (400, 598)); SH_pts = ((365, 655), (432, 925))
TH_m = (poly_mask(Lg.shape, [strip(*TH_pts, 104)]) & legm).astype(np.uint8)
SH_m = (poly_mask(Lg.shape, [strip(*SH_pts, 108)]) & legm).astype(np.uint8)

np.savez_compressed(E3 / "json" / "s5r3_pieces.npz", G=G, near_a=near_a.astype(np.float32),
                    UB_g=UB_g.astype(np.float32), UB_a=UB_a.astype(np.float32), Lg=Lg.astype(np.float32),
                    TH_a=feather(TH_m, 1.0), SH_a=feather(SH_m, 1.0))
save_mask(Mk / "S5r3_climber_UB_mask.png", bodyB); save_mask(Mk / "S5r3_climber_matting_band.png", unkB)
save_mask(Mk / "S5r3_leg_mask.png", legm); save_mask(Mk / "S5r3_TH_mask.png", TH_m); save_mask(Mk / "S5r3_SH_mask.png", SH_m)
save_mask(F / "S5r3_climber_cleanup_changed.png", cv2.resize(failB, (B.shape[1], B.shape[0]), interpolation=cv2.INTER_NEAREST))
save_mask(F / "S5r3_leg_cleanup_changed.png", failL)
save_rgba(R / "S5r3_climber_UB.png", UB_g, UB_a); save_rgba(R / "S5r3_TH.png", Lg, feather(TH_m, 1.0)); save_rgba(R / "S5r3_SH.png", Lg, feather(SH_m, 1.0))
man = {"stage_plate": "2017714056", "stage_file": "u1-picture/raw/loc_2017714056_a.tif (LoC 8a00242a.tif)", "crop": CROP, "scale": s,
       "stage_curve": curveM, "climber_plate": "2017862340", "climber_file": "8d33583u.tif", "climber_curve": curveB,
       "UB_region_plate": REG, "leg_region_plate": [lx0, ly0, lx1, ly1],
       "view_to_plate": {"x0": VX0, "y0": VY0, "scale": VS}, "TH_axis_view": TH_pts, "SH_axis_view": SH_pts,
       "rail_lines_screen": {"top": [[100, 336], [868, 103]], "bottom": [[100, 394], [868, 180]], "lower_string_top": [[100, 514], [868, 363]]},
       "baluster_zone_gap_fraction": round(gap_frac, 3), "baluster_slant_deg": round(float(np.rad2deg(TH_BAL)), 1), "grabcut_cleanup": {"UB": stB, "leg": stL},
       "fills_invented": "none on the stage (nothing removed); climber pieces are decontaminated at the matte edge only"}
dump(E3 / "json" / "s5r3_cut.json", man)
ov = np.dstack([G, G, G]).copy(); ov[near > 0] = ov[near > 0] * 0.5 + np.array([0.5, 0.0, 0.0])
Image.fromarray((cv2.resize(ov, (960, 540), interpolation=cv2.INTER_AREA) * 255).astype(np.uint8)).save(E3 / "diag" / "s5r3_near_overlay.png")
ob = np.dstack([B, B, B]).copy(); ob[bodyB > 0] = ob[bodyB > 0] * 0.5 + np.array([0, 0, 0.5])
Image.fromarray((cv2.resize(ob, None, fx=0.25, fy=0.25, interpolation=cv2.INTER_AREA) * 255).astype(np.uint8)).save(E3 / "diag" / "s5r3_UB_overlay.png")
ol = np.dstack([Lg, Lg, Lg]).copy(); ol[TH_m > 0] = ol[TH_m > 0] * 0.5 + np.array([0.5, 0, 0]); ol[SH_m > 0] = ol[SH_m > 0] * 0.5 + np.array([0, 0.5, 0])
Image.fromarray((cv2.resize(ol, None, fx=0.25, fy=0.25, interpolation=cv2.INTER_AREA) * 255).astype(np.uint8)).save(E3 / "diag" / "s5r3_legs_overlay.png")
print(json.dumps({"gap_frac": gap_frac, "UB": stB, "leg": stL, "TH_px": int(TH_m.sum()), "SH_px": int(SH_m.sum())}))

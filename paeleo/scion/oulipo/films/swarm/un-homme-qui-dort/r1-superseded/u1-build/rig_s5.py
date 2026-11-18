"""S5 FLIGHT-1 rig: LoC 2017811447, a powder-plant employee going upstairs (Vachon 1940).
Planes (back to front): far = wallpaper wall + door frame (the man and his cast shadow removed, wall rebuilt by
patch-copying the plate's own wallpaper: INVENTED, mask exported); figure = the man (GrabCut) with the plaid coat
as an attached second piece; near = handrail + balusters (GrabCut, the shield plane).
The stair line is MEASURED on the plate (handrail top edge, least squares over 50 columns)."""
import numpy as np
import cv2
from lib import *

PID = "2017811447"
RAIL_M, RAIL_C = 0.8354, 271.69        # measured: rail dark-top edge y = C + M x (plate px), rms 4.0 px
RAIL_B_M, RAIL_B_C = 0.8223, 329.67    # measured: rail bottom edge
ANCHOR = (430.0, 975.0)                # figure anchor in the plate (foot point under the coat hem)
F = 0.62                               # figure scale on the stair (rail depth / the plate's foot-of-stair depth)
FOOT_BELOW_RAIL = 272.0                # 0.85 m rail height at 320 px/m (newel: rail 700 -> floor 975)
FOOTFALLS = [20.8, 21.35, 21.9, 22.45, 23.0]
NEAR_MAX_Y = 540


def rail_top(x):
    return RAIL_C + RAIL_M * x


def build(write=True):
    g, crop = load_plate(PID)
    x0, y0, x1, y1 = crop
    valid = np.zeros(g.shape, np.uint8); valid[y0:y1, x0:x1] = 1
    rep = {}
    # ---------- the man (SCION-29) ----------
    fg = [[(400, 82), (450, 98)], [(410, 140), (420, 220)], [(480, 260), (500, 450)], [(545, 300), (560, 420)],
          [(370, 430), (395, 600)], [(470, 490), (480, 600)], [(400, 660), (430, 950)], [(300, 800), (560, 800)],
          [(440, 230), (470, 240)], [(560, 650), (580, 800)]]
    bg = [[(334, 140), (344, 255)], [(370, 48), (470, 50)], [(492, 95), (500, 200)], [(612, 150), (622, 300)],
          [(150, 600), (200, 900)], [(100, 390), (250, 500)], [(620, 620), (680, 900)], [(330, 300), (345, 380)],
          [(60, 600), (80, 950)]]
    hard, _, _ = grabcut(g, (290, 55, 615, 975), fg, bg)
    seed = lines_mask(g.shape, fg, 9)
    clean, fail, st = cleanup(hard, seed)
    rep["grabcut_man"] = st
    plaid_zone = poly_mask(g.shape, [[(232, 560), (345, 532), (420, 578), (520, 606), (565, 612), (612, 820), (612, 975), (232, 975)]])
    coat_m = clean * plaid_zone
    body_m = clean * (1 - plaid_zone)
    a_body = feather(body_m, 1.0); a_coat = feather(coat_m, 1.0)
    # overlap: the body continues 4 px under the coat's top fold
    a_body = np.maximum(a_body, (cv2.dilate(coat_m, np.ones((9, 9), np.uint8)) * clean * (1 - coat_m)).astype(np.float32))
    g_body = unpremult_edge(g, a_body, body_m); g_coat = unpremult_edge(g, a_coat, coat_m)
    # ---------- the banister (near, shield) ----------
    rail_poly = [(42, RAIL_C + RAIL_M * 42 - 17), (372, RAIL_C + RAIL_M * 372 - 17), (372, RAIL_B_C + RAIL_B_M * 372 + 3), (42, RAIL_B_C + RAIL_B_M * 42 + 3)]
    bal = [(44, 64), (74, 116), (124, 166), (174, 216), (229, 267), (288, 312)]
    bal_polys = [[(a, RAIL_B_C + RAIL_B_M * a - 4), (b, RAIL_B_C + RAIL_B_M * b - 4), (b, 975), (a, 975)] for a, b in bal]
    fgn = [[(60, rail_top(60) + 25), (330, rail_top(330) + 25)]] + [[((a + b) / 2, RAIL_B_C + RAIL_B_M * b + 15), ((a + b) / 2, 530)] for a, b in bal[:5]]
    bgn = [[(60, rail_top(60) - 40), (330, rail_top(330) - 40)]] + [[(b + 5, RAIL_B_C + RAIL_B_M * (b + 5) + 20), (b + 5, 530)] for a, b in bal[:5]]
    hard_n, _, _ = grabcut(g, (42, 250, 380, NEAR_MAX_Y + 30), fgn, bgn, prfg_polys=[rail_poly] + bal_polys, line_w=5)
    zone = np.clip(poly_mask(g.shape, [rail_poly] + bal_polys), 0, 1)
    near_m = (hard_n & cv2.dilate(zone, np.ones((5, 5), np.uint8))) | cv2.erode(zone, np.ones((7, 7), np.uint8))
    near_m = near_m * (1 - cv2.dilate(clean, np.ones((3, 3), np.uint8)))
    near_m[NEAR_MAX_Y:] = 0
    near_m = near_m * valid
    near_clean, fail_n, st_n = cleanup(near_m.astype(np.uint8), lines_mask(g.shape, fgn, 5))
    rep["grabcut_banister"] = st_n
    # rail segment hidden by the man's brown coat (x 300..372): copied along the rail direction from x-70 (INVENTED)
    rail_m = poly_mask(g.shape, [rail_poly])
    hidden_rail = (rail_m & cv2.dilate(clean, np.ones((3, 3), np.uint8))).astype(np.uint8)
    hidden_rail[NEAR_MAX_Y:] = 0
    gn = g.copy()
    ys, xs = np.nonzero(hidden_rail)
    sh = 70
    gn[ys, xs] = g[np.clip(np.round(ys - RAIL_M * sh).astype(int), 0, g.shape[0] - 1), np.clip(xs - sh, 0, g.shape[1] - 1)]
    near_clean = np.clip(near_clean + hidden_rail, 0, 1).astype(np.uint8)
    a_near = feather(near_clean, 0.9)
    # ---------- far wall: remove the man and his cast shadow; rebuild wallpaper by patch-copy ----------
    shadow = poly_mask(g.shape, [[(498, 228), (578, 232), (618, 300), (624, 480), (612, 565), (478, 565)]])
    hole = cv2.dilate(np.clip(clean + shadow, 0, 1).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11)))
    hole[580:] = 0
    hole = hole * valid
    wall_src = valid.copy(); wall_src[:, 652:] = 0; wall_src[560:] = 0
    wall_src = wall_src * (1 - cv2.dilate(hole, np.ones((15, 15), np.uint8)))
    xx = np.arange(g.shape[1])[None, :]; yy = np.arange(g.shape[0])[:, None]
    wall_src = wall_src * (yy < (RAIL_C + RAIL_M * xx - 20)).astype(np.uint8)
    far = quilt_fill(g, hole, wall_src, patch=40, overlap=10, cands=1200, seed=47)
    # under the banister (seen only in a 16 px band when the near plane slides): filled from the wall side
    band_hole = (near_clean * valid).astype(np.uint8)
    far = inpaint(far, band_hole, 5)
    inv_far = np.clip(hole + band_hole, 0, 1).astype(np.float32)
    far_alpha = valid.astype(np.float32); far_alpha[600:] = 0  # rows below 600 are never in the window
    if write:
        save_mask(SRC / "masks" / "S5_man_grabcut_hard.png", hard)
        save_mask(SRC / "masks" / "S5_man_clean.png", clean)
        save_mask(SRC / "masks" / "S5_body.png", body_m)
        save_mask(SRC / "masks" / "S5_plaid_coat.png", coat_m)
        save_mask(SRC / "masks" / "S5_near_banister.png", near_clean)
        save_mask(SRC / "masks" / "S5_cast_shadow_removed.png", shadow)
        save_mask(SRC / "failure_masks" / "S5_man_cleanup_changes.png", fail)
        save_mask(SRC / "failure_masks" / "S5_banister_cleanup_changes.png", fail_n)
        save_mask(SRC / "failure_masks" / "S5_banister_gc_vs_polygon_disagreement.png", (zone ^ (hard_n & zone)) * (np.arange(g.shape[0])[:, None] < NEAR_MAX_Y))
        save_mask(SRC / "fills" / "S5_wall_rebuilt_wallpaper_patchcopy.png", hole)
        save_mask(SRC / "fills" / "S5_wall_invented_under_banister.png", band_hole)
        save_mask(SRC / "fills" / "S5_rail_segment_copied_along_rail.png", hidden_rail)
        rep["rgba"] = {
            "S5_figure_body.png": save_rgba(SRC / "rgba" / "S5_figure_body.png", g_body, a_body),
            "S5_figure_plaid_coat.png": save_rgba(SRC / "rgba" / "S5_figure_plaid_coat.png", g_coat, a_coat),
            "S5_near_banister.png": save_rgba(SRC / "rgba" / "S5_near_banister.png", gn, a_near),
            "S5_far_wall_rebuilt.png": save_rgba(SRC / "rgba" / "S5_far_wall_rebuilt.png", far, far_alpha),
        }
    layers = [
        Layer("far_wall", far, far_alpha, K["far"], 0, invented=inv_far),
        Layer("fig_body", g_body, a_body, K["fig"], 1, pose=lambda t: fig_pose(t, 0.0), role="figure"),
        Layer("fig_coat", g_coat, a_coat, K["fig"], 2, pose=lambda t: fig_pose(t, COAT_LAG), role="figure"),
        Layer("near_banister", gn, a_near, K["near"], 3, invented=hidden_rail.astype(np.float32)),
    ]
    return layers, rep


K = {"far": 0.55, "fig": 0.8, "near": 1.0}
S0 = W / 680.0
C0 = (384.0, 331.0)   # window x 44..724 (+ up to 35 plate px glide), y 140..522
GLIDE = 33.0          # plate px at k=1 over 19.0-24.5
COAT_LAG = 2.0 / 24   # the carried coat answers each footfall two frames late (weight, secondary motion)
DIP = 3.0             # output px per footfall
# path of the anchor along the measured stair line, solved in calibrate() so that the first figure pixel is in
# frame at 20.5 (frame 492) and the last leaves at 23.5 (frame 564); values written by calibrate()
PATH = {"xa_in": 652.0, "xa_out": -78.0, "t_in": 20.5, "t_out": 23.5}


def dip(t):
    """3 px down at each footfall, recovering over 0.25 s (audio-driven step accent, SCION-47)."""
    d = 0.0
    for f in FOOTFALLS:
        u = t - f
        if -0.5 / 24 <= u < 0.30:
            d = max(d, 1.0 if u < 1.0 / 24 else 0.5 * (1 + np.cos(np.pi * (u - 1.0 / 24) / (0.30 - 1.0 / 24))))
    return DIP * d / S0  # plate px


def anchor_x(t):
    p = PATH
    return p["xa_in"] + (p["xa_out"] - p["xa_in"]) * (t - p["t_in"]) / (p["t_out"] - p["t_in"])


def fig_pose(t, lag):
    xa = anchor_x(t)
    ya = rail_top(xa) + FOOT_BELOW_RAIL + dip(t - lag)
    return np.array([[F, 0, xa - F * ANCHOR[0]], [0, F, ya - F * ANCHOR[1]]], np.float64)


def cam(t):
    e = (t - 19.0) / 5.5
    e = min(1.0, max(0.0, e))
    return {"c0": C0, "d": (GLIDE * e, 0.0), "s0": S0}

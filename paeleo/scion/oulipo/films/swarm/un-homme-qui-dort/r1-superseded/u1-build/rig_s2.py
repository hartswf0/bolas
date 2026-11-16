"""S2 TELEPHONE rig: LoC 2017735081 (2400 px derivative of the LoC TIFF master).
Planes: far = wall, telephone, directory notice, hook board, post; near = hanging coats, cap and scarf
(GrabCut + colour-line matting on the fur collar). Slow push: wall 1.00 -> 1.04, coats 2x the wall's drift."""
import numpy as np
import cv2
from lib import *

PID = "2017735081"
SC = 0.5  # GrabCut runs on a half-size copy (grain-scale noise is below the photograph preset's interest); matte at full size


def build(write=True):
    g, crop = load_plate(PID)
    x0, y0, x1, y1 = crop
    valid = np.zeros(g.shape, np.uint8); valid[y0:y1, x0:x1] = 1
    rep = {}
    gs = cv2.resize(g, None, fx=SC, fy=SC, interpolation=cv2.INTER_AREA)
    S = lambda pts: [(x * SC, y * SC) for x, y in pts]
    fg = [[(950, 700), (900, 1500)], [(1180, 650), (1180, 1550)], [(1500, 620), (1450, 1550)], [(1870, 700), (1870, 950)],
          [(1900, 1100), (1900, 1550)], [(1780, 1120), (2050, 1160)], [(1400, 560), (1650, 560)], [(860, 560), (1050, 560)],
          [(700, 1450), (760, 1100)]]
    bg = [[(640, 430), (2000, 430)], [(2150, 600), (2160, 1560)], [(2060, 560), (2070, 900)], [(560, 650), (600, 1500)],
          [(760, 470), (2000, 455)]]
    prfg = [[(820, 505), (1300, 480), (1700, 455), (2010, 515), (2130, 1000), (2135, 1580), (630, 1580), (690, 1000), (780, 560)]]
    hard_s, _, _ = grabcut(gs, (int(560 * SC), int(440 * SC), int(2170 * SC), int(1580 * SC)),
                           [S(l) for l in fg], [S(l) for l in bg], prfg_polys=[S(p) for p in prfg], line_w=5)
    hard = (cv2.resize(hard_s.astype(np.float32), (g.shape[1], g.shape[0]), interpolation=cv2.INTER_LINEAR) > 0.5).astype(np.uint8)
    hard = hard * valid
    # the coats run off the bottom of the picture: keep that edge
    seed = lines_mask(g.shape, fg, 15)
    from lib import PRESETS
    PRESETS["photograph_2400"] = dict(PRESETS["photograph"], open_r=4, close_r=6, max_hole=6000)
    clean, fail, st = cleanup(hard, seed, preset="photograph_2400")
    rep["grabcut_coats"] = st
    fur = [[(1290, 440), (1730, 440), (1730, 990), (1290, 990)]]
    alpha, unk = matting_band(g, clean, band_poly=fur, r=6, win=15)
    # elsewhere a plain feather (cloth edges are hard)
    alpha = np.where(poly_mask(g.shape, fur) > 0, alpha, feather(clean, 1.6))
    g_near = unpremult_edge(g, alpha, clean)
    # wall plane: everything under the coats is filled from the wall side (half-size Telea, upsampled into the hole)
    hole = cv2.dilate(clean, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))) * valid
    hs = cv2.resize(hole, None, fx=0.25, fy=0.25, interpolation=cv2.INTER_NEAREST)
    gq = cv2.resize(g, None, fx=0.25, fy=0.25, interpolation=cv2.INTER_AREA)
    fq = inpaint(gq, (cv2.dilate(hs, np.ones((3, 3), np.uint8))), 9)
    fill = cv2.resize(fq, (g.shape[1], g.shape[0]), interpolation=cv2.INTER_CUBIC)
    wall = np.where(hole > 0, fill, g).astype(np.float32)
    if write:
        save_mask(SRC / "masks" / "S2_coats_grabcut_hard.png", hard)
        save_mask(SRC / "masks" / "S2_coats_clean.png", clean)
        save_mask(SRC / "masks" / "S2_coats_alpha.png", alpha)
        save_mask(SRC / "masks" / "S2_fur_unknown_band.png", unk)
        save_mask(SRC / "failure_masks" / "S2_coats_cleanup_changes.png", fail)
        save_mask(SRC / "fills" / "S2_wall_invented_under_coats.png", hole)
        rep["rgba"] = {
            "S2_near_coats.png": save_rgba(SRC / "rgba" / "S2_near_coats.png", g_near, alpha),
            "S2_far_wall_telephone.png": save_rgba(SRC / "rgba" / "S2_far_wall_telephone.png", wall, valid.astype(np.float32)),
        }
    layers = [
        Layer("far_wall_telephone", wall, valid.astype(np.float32), K["far"], 0, invented=hole.astype(np.float32)),
        Layer("near_coats", g_near, alpha, K["near"], 1),
    ]
    return layers, rep


K = {"far": 1.0, "near": 2.0}
S0 = W / 1960.0
C0 = (1120.0, 745.0)   # window 1960 x 1102.5: x 140..2100, y 194..1296 (telephone, notice, coats)
DRIFT = 40.0           # plate px at k=1 (wall) over the shot; coats 80


def cam(t):
    e = ease(t, 5.5 - 0.6, 8.5 + 0.6)  # the push is already moving at the cut in and still moving at the cut out
    return {"c0": C0, "d": (DRIFT * e, 0.0), "s0": S0, "push": 1.0 + 0.04 * e}

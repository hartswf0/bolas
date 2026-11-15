"""S1 WAKE rig: LoC 2017811426. Planes far (wall) / mid (headboard, bunk, legs+bedding, head+torso piece) / near (bedding edge, bunk frame)."""
import numpy as np
import cv2
from lib import *

PID = "2017811426"
PIVOT = (262.0, 868.0)  # hip, plate px (measured on the plate: belt line meets the left trouser seam)
SEAM = [(140, 858), (300, 862), (480, 884)]  # hip seam polyline: head+torso above, legs below


def build(write=True):
    g, crop = load_plate(PID)
    x0, y0, x1, y1 = crop
    valid = np.zeros(g.shape, np.uint8); valid[y0:y1, x0:x1] = 1
    rep = {}
    # --- SCION-29: GrabCut the man (head + torso + arms + hands) ---
    fg_lines = [[(337, 612), (337, 725)], [(190, 790), (440, 790)], [(300, 735), (300, 850)], [(240, 760), (430, 760)],
                [(370, 845), (410, 860)], [(205, 830), (290, 838)],
                [(286, 656), (288, 676)], [(380, 650), (378, 690)], [(320, 728), (360, 733)], [(337, 600), (337, 612)]]
    bg_lines = [[(175, 615), (275, 690)], [(410, 610), (690, 700)], [(55, 790), (135, 820)], [(560, 760), (680, 800)],
                [(500, 700), (560, 740)], [(150, 610), (280, 612)], [(400, 605), (700, 605)],
                [(281, 603), (283, 640)], [(395, 600), (396, 640)], [(400, 650), (400, 700)], [(268, 700), (291, 706)]]
    rect = (140, 588, 492, 892)
    hard, init, lab = grabcut(g, rect, fg_lines, bg_lines)
    below = poly_mask(g.shape, [[(0, 2000), (0, SEAM[0][1]), *SEAM, (2000, SEAM[-1][1]), (2000, 2000)]])
    hard_t = hard * (1 - below)
    seed = lines_mask(g.shape, fg_lines, 9) * (1 - below)
    clean, fail, st = cleanup(hard_t, seed)
    rep["grabcut_torso"] = st
    # feathered alpha, but the seam edge stays hard-ish and overlaps the legs by 4 px so no gap opens at the hip
    a_t = feather(clean, 1.0)
    seam_band = poly_mask(g.shape, [[(140, 850), (300, 854), (480, 876), (480, 892), (300, 870), (140, 866)]])
    a_t = np.where((seam_band > 0) & (hard > 0), 1.0, a_t)
    g_t = unpremult_edge(g, a_t, clean)
    # --- plane cuts (polygons on the plate, refined by GrabCut where an edge exists) ---
    headboard = [(150, 594), (735, 594), (742, 860), (150, 860)]
    near_poly = [[(32, 948), (300, 958), (520, 945), (640, 960), (742, 920), (742, 985), (32, 985)],   # foot edge of the bedding
                 [(690, 800), (742, 790), (742, 985), (650, 985), (660, 900)]]                  # dark bunk post, right
    m_head = poly_mask(g.shape, [headboard])
    bed_poly = [(32, 735), (150, 735), (150, 860), (742, 860), (742, 985), (32, 985)]  # bunk, bedding, legs, pillows
    m_bed = poly_mask(g.shape, [bed_poly])
    m_near = poly_mask(g.shape, near_poly)
    m_mid = np.clip(m_head + m_bed, 0, 1) * (1 - m_near)
    # --- far: whole plate; holes under nearer planes are filled (invented) so parallax never shows doubled pixels
    reveal = 16  # max relative displacement (plate px) between far and mid/near over the glide, plus margin
    kD = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * reveal + 1,) * 2)
    # only a band inside the edge of the mid plane needs inventing (what a 16 px slide can reveal)
    inner = np.clip(m_mid + m_near, 0, 1).astype(np.uint8)
    band_far = inner - cv2.erode(inner, kD)
    band_far = band_far * valid
    far = inpaint(g, (inner * valid).astype(np.uint8), 5)  # filled from the wall side only
    far_alpha = valid.astype(np.float32)
    # --- mid: headboard + bed; under the head+torso piece the mid plane is filled (it is uncovered by the lift)
    kT = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    hole_mid = cv2.dilate(clean, kT) * m_mid
    # headboard part of the hole: patch-copied from the headboard's own wood (SCION-44 texture extension);
    # the rest (sheets below) by cv2.inpaint from the same plate
    m_hb_only = poly_mask(g.shape, [headboard])
    src_hb = m_hb_only * (1 - cv2.dilate(clean, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31))))
    src_hb = src_hb * (1 - poly_mask(g.shape, [[(490, 640), (560, 640), (560, 700), (490, 700)]]))  # not the drawer knob
    src_hb[:610] = 0
    hq = (hole_mid * m_hb_only).astype(np.uint8)
    mid_g = quilt_fill(g, hq, src_hb, patch=32, overlap=8, cands=700, seed=11)
    mid_g = inpaint(mid_g, (hole_mid * (1 - m_hb_only)).astype(np.uint8), 9)
    # under the near plane, the mid plane needs a band too (near slides over it)
    # the mid plane continues under the near plane (the bunk is there); a 12 px band of it is invented
    kB = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25))
    band_mid = (m_near & cv2.dilate(m_mid, kB)).astype(np.uint8)
    m_mid_ext = np.clip(m_mid + band_mid, 0, 1).astype(np.uint8)
    mid_g = inpaint(mid_g, m_near.astype(np.uint8), 5)  # from the bunk side only
    hole_mid = np.clip(hole_mid + band_mid, 0, 1).astype(np.uint8)
    mid_a = feather(m_mid_ext, 0.8)
    # pieces
    near_a = feather(m_near, 1.0)
    inv_far = (inner * valid).astype(np.float32)
    inv_mid = hole_mid.astype(np.float32)
    if write:
        save_mask(SRC / "masks" / "S1_torso_grabcut_hard.png", hard)
        save_mask(SRC / "masks" / "S1_torso_clean.png", clean)
        save_mask(SRC / "masks" / "S1_mid_plane.png", m_mid_ext)
        save_mask(SRC / "masks" / "S1_near_plane.png", m_near)
        save_mask(SRC / "failure_masks" / "S1_torso_cleanup_changes.png", fail)
        save_mask(SRC / "fills" / "S1_far_invented_band.png", band_far)
        save_mask(SRC / "fills" / "S1_mid_invented_under_torso.png", hole_mid)
        rep["rgba"] = {
            "S1_head_torso.png": save_rgba(SRC / "rgba" / "S1_head_torso.png", g_t, a_t),
            "S1_mid_headboard_bed_legs.png": save_rgba(SRC / "rgba" / "S1_mid_headboard_bed_legs.png", mid_g, mid_a),
            "S1_near_bedding_bunkframe.png": save_rgba(SRC / "rgba" / "S1_near_bedding_bunkframe.png", g, near_a),
            "S1_far_wall.png": save_rgba(SRC / "rgba" / "S1_far_wall.png", far, far_alpha),
        }
    def pose_torso(t):
        e = ease(t, 2.0, 2.8)
        return rot_about(PIVOT[0], PIVOT[1], -5.0 * e, 0.0, -6.0 / S0 * e)
    layers = [
        Layer("far_wall", far, far_alpha, K["far"], 0, invented=inv_far),
        Layer("mid_headboard_bed_legs", mid_g, mid_a, K["mid"], 1, invented=inv_mid),
        Layer("fig_head_torso", g_t, a_t, K["mid"], 2, pose=pose_torso, role="piece"),
        Layer("near_bedding_bunkframe", g, near_a, K["near"], 3),
    ]
    return layers, rep


# camera: 16:9 window of 684 plate px (scale S0) centred on the bunk; lateral glide L->R.
S0 = W / 684.0
K = {"far": 0.55, "mid": 0.8, "near": 1.2}
GLIDE = 28.0 / S0  # 28 output px at k=1 over the shot (plate px)
C0 = (374.5, 781.6)  # window x 32.5..716.5 (+ glide), y 589..974: head top 595 to the bedding edge


def cam(t):
    e = ease(t, 0.0, 5.5) * 0.85 + 0.15 * (t / 5.5)  # eased glide, never quite stops
    return {"c0": C0, "d": (GLIDE * e, 0.0), "s0": S0}


T0, T1 = 0.0, 5.5
EVENTS = {"E1_on": 2.0, "E1_off": 2.8}

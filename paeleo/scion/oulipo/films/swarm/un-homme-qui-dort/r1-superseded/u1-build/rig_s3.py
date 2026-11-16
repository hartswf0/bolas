"""S3 REFUSE / S4 HELD rig: LoC 2017811449, the man on his bunk seen through the open doorway.
Planes: far = room (back wall, shelf, headboard, bunk; the man shares the room's depth because he lies on the bunk),
pieces = head (neck pivot), torso (waist pivot, breath branch), near = left jamb + door leaf + padlocked frame."""
import numpy as np
import cv2
from lib import *

PID = "2017811449"
NECK = (455.0, 463.0)     # head pivot (plate px): collar centre
WAIST = (450.0, 590.0)    # torso rests on the bunk here
HEAD_SPLIT = [(400, 470), (455, 458), (520, 468)]
WAIST_SPLIT = [(330, 585), (450, 575), (560, 560)]


def build(write=True):
    g, crop = load_plate(PID)
    x0, y0, x1, y1 = crop
    valid = np.zeros(g.shape, np.uint8); valid[y0:y1, x0:x1] = 1
    rep = {}
    fg_lines = [[(455, 385), (455, 455)], [(430, 420), (480, 420)], [(380, 490), (530, 490)], [(450, 470), (450, 560)],
                [(360, 520), (360, 570)], [(530, 500), (545, 545)], [(420, 520), (420, 640)], [(400, 600), (430, 650)]]
    bg_lines = [[(395, 380), (405, 450)], [(505, 380), (500, 450)], [(330, 400), (390, 440)], [(520, 400), (600, 440)],
                [(565, 470), (620, 520)], [(250, 520), (330, 560)], [(220, 600), (330, 620)], [(270, 700), (480, 720)],
                [(480, 600), (520, 640)]]
    rect = (330, 362, 600, 680)
    hard, init, lab = grabcut(g, rect, fg_lines, bg_lines)
    # man above the bunk: keep head + torso + raised leg/shoe (the legs lying on the bunk stay in the room plane)
    clean, fail, st = cleanup(hard, lines_mask(g.shape, fg_lines, 9))
    rep["grabcut_man"] = st
    head_m = clean * poly_mask(g.shape, [[(0, 0), (2000, 0), (2000, HEAD_SPLIT[-1][1]), *HEAD_SPLIT[::-1], (0, HEAD_SPLIT[0][1])]])
    torso_zone = poly_mask(g.shape, [[(0, HEAD_SPLIT[0][1]), *HEAD_SPLIT, (2000, HEAD_SPLIT[-1][1]), (2000, WAIST_SPLIT[-1][1]), *WAIST_SPLIT[::-1], (0, WAIST_SPLIT[0][1])]])
    torso_m = clean * torso_zone
    # the raised shoe/leg crosses the torso: it is NOT part of the breathing torso (it rests on the other knee)
    shoe = poly_mask(g.shape, [[(388, 505), (445, 498), (462, 560), (468, 665), (400, 668), (385, 600)]])
    torso_m = torso_m * (1 - shoe)
    a_head = feather(head_m, 1.0); a_torso = feather(torso_m, 1.0)
    # overlaps across the splits (no gap opens when pieces rotate a few degrees)
    k5 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    a_torso = np.maximum(a_torso, (cv2.dilate(head_m, k5) * clean * (1 - head_m)).astype(np.float32))
    g_head = unpremult_edge(g, a_head, head_m); g_torso = unpremult_edge(g, a_torso, torso_m)
    # room plane: fill behind the moving pieces from the same plate (headboard wood, wall, sweater-free)
    hole = cv2.dilate(np.clip(head_m + torso_m, 0, 1).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    hb = poly_mask(g.shape, [[(318, 372), (672, 372), (660, 535), (318, 535)]])
    src = hb * (1 - cv2.dilate(clean, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31))))
    src = src * (1 - poly_mask(g.shape, [[(555, 400), (600, 400), (600, 440), (555, 440)]]))  # not the knob
    room = quilt_fill(g, (hole * hb).astype(np.uint8), src, patch=28, overlap=7, cands=700, seed=3)
    room = inpaint(room, (hole * (1 - hb)).astype(np.uint8), 7)
    # near plane: doorway
    left_jamb = [(42, 24), (192, 24), (190, 744), (42, 744)]
    right = [(668, 24), (1004, 24), (1004, 744), (832, 744), (832, 668), (628, 560), (662, 262), (672, 112)]
    m_near = poly_mask(g.shape, [left_jamb, right])
    # refine the slanted door-leaf edge with GrabCut (box around the edge, polygon as probable fg)
    hard_n, _, _ = grabcut(g, (600, 24, 1004, 744), fg_lines=[[(760, 300), (780, 600)], [(900, 100), (900, 700)]],
                           bg_lines=[[(600, 330), (640, 540)], [(560, 600), (620, 700)]], prfg_polys=[right])
    leaf = poly_mask(g.shape, [right])
    leaf_ref = (cv2.dilate(leaf, np.ones((5, 5), np.uint8)) & hard_n) | cv2.erode(leaf, np.ones((9, 9), np.uint8))
    m_near = np.clip(poly_mask(g.shape, [left_jamb]) + leaf_ref, 0, 1).astype(np.uint8)
    a_near = feather(m_near, 1.0)
    # room under the near plane: band the glide can reveal
    reveal = 14
    kD = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * reveal + 1,) * 2)
    band = (m_near - cv2.erode(m_near, kD)) * valid
    # fill from the room side only: the whole near region is the hole, so jamb pixels never bleed in
    room = inpaint(room, (m_near * valid).astype(np.uint8), 5)
    inv_room = np.clip(hole + m_near, 0, 1).astype(np.float32)
    if write:
        save_mask(SRC / "masks" / "S3_man_grabcut_hard.png", hard)
        save_mask(SRC / "masks" / "S3_man_clean.png", clean)
        save_mask(SRC / "masks" / "S3_head.png", head_m)
        save_mask(SRC / "masks" / "S3_torso.png", torso_m)
        save_mask(SRC / "masks" / "S3_near_doorway.png", m_near)
        save_mask(SRC / "failure_masks" / "S3_man_cleanup_changes.png", fail)
        save_mask(SRC / "failure_masks" / "S3_doorleaf_gc_disagreement.png", (leaf ^ leaf_ref) & leaf)
        save_mask(SRC / "fills" / "S3_room_invented_behind_pieces.png", hole)
        save_mask(SRC / "fills" / "S3_room_invented_band_under_door.png", band)
        rep["rgba"] = {
            "S3_head.png": save_rgba(SRC / "rgba" / "S3_head.png", g_head, a_head),
            "S3_torso.png": save_rgba(SRC / "rgba" / "S3_torso.png", g_torso, a_torso),
            "S3_near_doorway.png": save_rgba(SRC / "rgba" / "S3_near_doorway.png", g, a_near),
            "S3_far_room.png": save_rgba(SRC / "rgba" / "S3_far_room.png", room, valid.astype(np.float32)),
        }

    def pose_torso(t):
        return np.array([[1, 0, 0], [0, 1, breath(t)]], np.float64)

    def pose_head(t):
        # glance: 3 deg toward the door (screen right, clockwise = negative) at 9.25, hold, return at 10.4
        on = ease(t, 9.25, 9.25 + 0.30)
        off = ease(t, 10.4, 10.4 + 0.45)
        ang = -3.0 * (on - off)
        M = rot_about(NECK[0], NECK[1], ang)
        M[1, 2] += breath(t)
        return M
    layers = [
        Layer("far_room", room, valid.astype(np.float32), K["far"], 0, invented=inv_room),
        Layer("fig_torso", g_torso, a_torso, K["far"], 1, pose=pose_torso, role="piece"),
        Layer("fig_head", g_head, a_head, K["far"], 2, pose=pose_head, role="piece"),
        Layer("near_doorway", g, a_near, K["near"], 3),
    ]
    return layers, rep


S0 = W / 900.0
K = {"far": 0.6, "near": 1.25}
GLIDE = 30.0 / S0          # plate px at k=1
C0 = (42 + 450 + 1.0, 470.0)   # window x 43..943 (+ glide up to 35*1.25), y 217..723


def breath(t):
    """Branch HELD-breath (invented secondary motion, flagged): torso rises <= 1.5 output px per 3.75 s cycle,
    only inside S4 (11.5-19.0), zero at both ends of the shot."""
    if t < 11.5 or t > 19.0:
        return 0.0
    ph = (t - 11.5) / 3.75
    return -(1.2 / S0) * 0.5 * (1 - np.cos(2 * np.pi * ph))  # 0 .. -1.2 output px, plate units


def cam(t):
    # S3: glide 8.5 -> rest by 10.5; S4: at rest (same end position, no motion)
    x = min(1.0, max(0.0, (t - 8.5) / 2.0))
    e = 1.0 - (1.0 - x) ** 2   # ease-out: enters moving, settles to rest at 10.5
    return {"c0": C0, "d": (GLIDE * e, 0.0), "s0": S0}

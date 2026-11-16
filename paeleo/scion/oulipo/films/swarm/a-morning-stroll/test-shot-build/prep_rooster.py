"""#29 GrabCut extraction + #32 FK piece cutting for the rooster (LoC stereo.1s08734, left lens).
Run with python3 -I. Writes sources/.../test-shot/rooster/{piece_*.png, rig.json, check_cut.png, failure_mask.png}.

Source frame: roo_crop.png (1200x1400 crop of the master TIFF) reduced to 600x700 = rig coordinates.
Facing right, as photographed.
"""
import json
import os

import cv2
import numpy as np
from PIL import Image

OUL = "/home/user/bolas/paeleo/scion/oulipo"
SRC = f"{OUL}/films/sources/a-morning-stroll/test-shot"
OUT = f"{SRC}/rooster"
os.makedirs(OUT, exist_ok=True)

# hand-placed scissor outline (rig coords), traced by eye round the bird, legs and toes included
OUTLINE = [(62, 140), (100, 116), (142, 118), (178, 160), (190, 200), (212, 230), (262, 242), (306, 232), (338, 198),
           (372, 140), (402, 104), (440, 74), (474, 58), (488, 38), (522, 40), (532, 70), (544, 102),
           (522, 116), (502, 152), (498, 200), (492, 262), (472, 332), (442, 372), (402, 400), (372, 420),
           (362, 460), (348, 500), (340, 540), (348, 575), (364, 600), (398, 614), (424, 630), (382, 638),
           (334, 628), (310, 602), (300, 562), (290, 530), (284, 506), (266, 512), (256, 542), (252, 590),
           (272, 614), (304, 632), (252, 642), (212, 637), (228, 600), (224, 560), (214, 502), (190, 452),
           (160, 402), (138, 362), (110, 302), (98, 270), (80, 230), (74, 190), (60, 152)]

# FK joint graph (rig coords): parent, pivot (pin) in rig coords
JOINTS = {
    "body": {"parent": None, "pin": (300, 470)},     # root: hip centre
    "head": {"parent": "body", "pin": (440, 300)},   # neck pin at the base of the neck
    "tail": {"parent": "body", "pin": (196, 250)},
    "leg_near": {"parent": "body", "pin": (258, 486)},
    "leg_far": {"parent": "body", "pin": (326, 476)},
}


def main():
    big = Image.open(f"{SRC}/roo_crop.png").convert("RGB")
    img = big.resize((600, 700), Image.LANCZOS)
    a = np.asarray(img)
    h, w = a.shape[:2]
    m0 = np.zeros((h, w), np.uint8)
    cv2.fillPoly(m0, [np.array(OUTLINE, np.int32)], 255)
    gm = np.full((h, w), cv2.GC_BGD, np.uint8)
    gm[cv2.dilate(m0, np.ones((13, 13), np.uint8)) > 0] = cv2.GC_PR_BGD
    gm[m0 > 0] = cv2.GC_PR_FGD
    gm[cv2.erode(m0, np.ones((13, 13), np.uint8)) > 0] = cv2.GC_FGD   # 6 px band either side is undecided
    bgd = np.zeros((1, 65), np.float64)
    fgd = np.zeros((1, 65), np.float64)
    cv2.grabCut(a[:, :, ::-1].copy(), gm, None, bgd, fgd, 6, cv2.GC_INIT_WITH_MASK)
    m = np.where((gm == cv2.GC_FGD) | (gm == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    # keep the largest component (no background islands), fill pinholes
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    m = np.where(lab == k, 255, 0).astype(np.uint8)
    inv = 255 - m
    n2, lab2, st2, _ = cv2.connectedComponentsWithStats(inv)
    for j in range(1, n2):
        if st2[j, cv2.CC_STAT_AREA] < 400:
            m[lab2 == j] = 255
    # the toes and the far leg are thin: GrabCut may drop them; keep the scissor cut there (toes retained)
    feet = np.zeros_like(m)
    feet[560:, :] = 1
    m = np.where(feet > 0, np.maximum(m, cv2.erode(m0, np.ones((3, 3), np.uint8))), m)
    alpha = cv2.GaussianBlur(m, (0, 0), 0.7)
    failure = ((m0 > 0) != (m > 0)).astype(np.uint8) * 255   # where GrabCut overruled the scissors
    Image.fromarray(failure).save(f"{OUT}/failure_mask.png")

    # neutral silver tone: albumen sepia -> luminance; stretch the white plumage toward paper white
    L = np.asarray(img.convert("L"), np.float32)
    inside = m > 128
    lo, hi = np.percentile(L[inside], [2, 97])
    t = np.clip((L - lo) / (hi - lo), 0, 1) ** 1.1
    t = np.clip((t - 0.08) / 0.75, 0, 1) ** 0.85   # the same high-key family of curve as the plate (unify)
    Lg = 10 + t * 238
    rgba = np.dstack([Lg, Lg, Lg, alpha]).astype(np.uint8)

    yy, xx = np.mgrid[0:h, 0:w]
    # piece masks with overlaps at every pin so rotation never opens a gap
    head_m = (xx > 322) & (yy < 312) & ~((xx < 405) & (yy > 266))
    tail_m = (xx < 206) & (yy < 330)
    leg_m = yy > 478
    near_m = leg_m & ((xx < 290) | ((xx < 300) & (yy < 520)))
    far_m = leg_m & ~near_m
    body_m = ~(((xx > 336) & (yy < 240)) | (tail_m & (xx < 186)) | (yy > 520))
    pieces = {"body": body_m, "head": head_m, "tail": tail_m, "leg_near": near_m, "leg_far": far_m}
    for name, pm in pieces.items():
        p = rgba.copy()
        p[..., 3] = (p[..., 3] * pm).astype(np.uint8)
        Image.fromarray(p).save(f"{OUT}/piece_{name}.png")
    Image.fromarray(rgba).save(f"{OUT}/whole.png")
    # beak tip and foot soles (rig coords) measured from the mask
    ys, xs = np.where(m[:200] > 128)
    i = np.argmax(xs)
    beak = (int(xs[i]), int(ys[i]))
    soles = {"leg_near": (240, 636), "leg_far": (372, 630)}
    ov = np.asarray(img).copy()
    ov[m < 128] = (ov[m < 128] * 0.3).astype(np.uint8)
    for nm, (px, py) in [(k_, v["pin"]) for k_, v in JOINTS.items()] + [("beak", beak)]:
        cv2.circle(ov, (int(px), int(py)), 5, (255, 0, 0), -1)
    Image.fromarray(ov).save(f"{OUT}/check_cut.png")
    json.dump({"source": "roo_crop.png at 600x700", "facing": "right", "joints": JOINTS, "beak_tip": beak,
               "soles": soles, "height_px": int(np.ptp(np.where(m > 128)[0])),
               "lum_stretch": [float(lo), float(hi)]}, open(f"{OUT}/rig.json", "w"), indent=1)
    print("beak", beak, "mask px", int((m > 128).sum()), "failure px", int((failure > 0).sum()))


if __name__ == "__main__":
    main()

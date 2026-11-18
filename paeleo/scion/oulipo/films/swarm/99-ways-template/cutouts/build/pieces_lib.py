"""helpers shared by pieces.py and plate.py"""
import cv2
import numpy as np


def levels(a, lo, hi, gamma=1.0):
    a = np.clip((a.astype(np.float32) - lo) / float(hi - lo), 0, 1) ** gamma
    return np.clip(a * 255.0 + 0.5, 0, 255).astype(np.uint8)


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



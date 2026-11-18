"""Rotoscope a photographic frame into brush-ink comic drawing (black solids, contour line, hatching)."""
import cv2, numpy as np
from PIL import Image


def ink(img, out_wh, crop=None, dark=0.22, mid=0.55, line_block=15, line_c=7, hatch=True, seed=0, hatch_ang=1, gamma=1.0, min_area=18, canny=(30, 80), lw=3, use_adapt=False, per=12, sigma=1.2):
    """img: PIL image. crop: (x0,y0,x1,y1) in source px. Returns PIL 'L' image (0 ink, 255 paper)."""
    a = np.asarray(img.convert('L'), dtype=np.float32)
    if crop:
        x0, y0, x1, y1 = crop
        a = a[y0:y1, x0:x1]
    W, H = out_wh
    # cover-fit
    h, w = a.shape
    s = max(W / w, H / h)
    a = cv2.resize(a, (int(w * s + .5), int(h * s + .5)), interpolation=cv2.INTER_CUBIC)
    oy, ox = (a.shape[0] - H) // 2, (a.shape[1] - W) // 2
    a = a[oy:oy + H, ox:ox + W]
    a = (a - np.percentile(a, 2)) / max(1, np.percentile(a, 98) - np.percentile(a, 2))
    a = np.clip(a, 0, 1) ** gamma
    u8 = (a * 255).astype(np.uint8)
    sm = cv2.bilateralFilter(u8, 9, 40, 9)
    sm = cv2.GaussianBlur(sm, (0, 0), sigma)
    L = sm.astype(np.float32) / 255
    paper = np.ones((H, W), np.float32)
    # solid blacks, with soft brush edge
    solid = (L < dark).astype(np.uint8)
    solid = cv2.morphologyEx(solid, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    solid = cv2.morphologyEx(solid, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    # contour lines from adaptive threshold
    lb = line_block | 1
    lines = cv2.adaptiveThreshold(sm, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, lb, line_c)
    lines = (lines == 0).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(lines, 8)
    keep = np.zeros(n, bool); keep[1:] = st[1:, cv2.CC_STAT_AREA] >= min_area
    lines = keep[lab].astype(np.uint8)
    # contour from Canny on the smoothed plate, thickened into a brush line
    ed = cv2.Canny(sm, canny[0], canny[1])
    ed = cv2.dilate(ed, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (lw, lw)))
    n2, lab2, st2, _ = cv2.connectedComponentsWithStats((ed > 0).astype(np.uint8), 8)
    k2 = np.zeros(n2, bool); k2[1:] = st2[1:, cv2.CC_STAT_AREA] >= min_area * 3
    ed = k2[lab2].astype(np.uint8)
    ink_m = np.maximum(solid, ed)
    if use_adapt:
        ink_m = np.maximum(ink_m, lines)
    if hatch:
        yy, xx = np.mgrid[0:H, 0:W]
        rng = np.random.default_rng(seed)
        jit = cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 6) * 6
        d1 = ((xx * hatch_ang + yy + jit) % per) < 1.5
        d2 = ((xx * -hatch_ang + yy + jit) % per) < 1.3
        h1 = (L < mid) & (L >= dark) & d1
        h2 = (L < (dark + mid) / 2) & (L >= dark) & d2
        ink_m = np.maximum(ink_m, (h1 | h2).astype(np.uint8))
    out = paper * (1 - ink_m)
    o = (out * 255).astype(np.uint8)
    o = cv2.GaussianBlur(o, (0, 0), 0.6)
    o = np.where(o > 150, 255, np.where(o < 90, 18, o)).astype(np.uint8)
    return Image.fromarray(o, 'L')

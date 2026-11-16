"""Cut a figure out of a line engraving as a solid silhouette (shadow-theatre
cutout) plus its interior line work."""
import numpy as np, cv2
from common import load


def cut(name, box, close=7, thr=150, flip=False, circle=None, keep_largest=0):
    a = load(name)
    x0, y0, x1, y1 = box
    a = a[y0:y1, x0:x1]
    g = a.mean(2)
    lines = (g < thr).astype(np.uint8)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close, close))
    c = cv2.morphologyEx(lines, cv2.MORPH_CLOSE, k)
    h, w = c.shape
    ff = np.pad(c, 1).copy()
    mask = np.zeros((h + 4, w + 4), np.uint8)
    cv2.floodFill(ff, mask, (0, 0), 2)
    ext = ff[1:-1, 1:-1] == 2
    sil = (~ext).astype(np.uint8)
    sil = cv2.morphologyEx(sil, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    if keep_largest:
        n, lab, st, _ = cv2.connectedComponentsWithStats(sil)
        order = np.argsort(-st[1:, cv2.CC_STAT_AREA])[:keep_largest] + 1
        sil = np.isin(lab, order).astype(np.uint8)
    if circle is not None:
        cx, cy, r = circle
        yy, xx = np.mgrid[0:h, 0:w]
        sil = ((xx - cx) ** 2 + (yy - cy) ** 2 <= r * r).astype(np.uint8)
    line = np.clip((thr + 40 - g) / 120.0, 0, 1)
    sil = sil.astype(np.float32)
    if flip:
        sil = sil[:, ::-1]; line = line[:, ::-1]
    return sil, line.astype(np.float32)


def place(canvas_mask, canvas_line, sil, line, x, y, scale=1.0, rot=0.0):
    """paste a cutout (mask + interior lines) at x,y (top-left) with scale/rotation"""
    H, W = canvas_mask.shape
    h, w = sil.shape
    M = cv2.getRotationMatrix2D((w / 2, h / 2), rot, scale)
    M[0, 2] += x - w / 2 + w * scale / 2
    M[1, 2] += y - h / 2 + h * scale / 2
    s = cv2.warpAffine(sil, M, (W, H), flags=cv2.INTER_LINEAR)
    l = cv2.warpAffine(line * sil, M, (W, H), flags=cv2.INTER_LINEAR)
    np.maximum(canvas_mask, s, out=canvas_mask)
    canvas_line[:] = canvas_line * (1 - s) + l
    return s

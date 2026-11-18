"""Shared helpers for the story-plates unit (run scripts with python3 -I)."""
import json
import os

import cv2
import numpy as np
from PIL import Image

OUL = "/home/user/bolas/paeleo/scion/oulipo"
SRC = f"{OUL}/films/sources/a-morning-stroll"
PLATES = f"{SRC}/plates"
W, H = 960, 540
PUSH = 0.015


def push_rects(rect):
    """Start/end source rects for a 1.5 % centred push over a shot (end rect is the start inset by 1.5 %)."""
    x0, y0, x1, y1 = rect
    w, h = x1 - x0, y1 - y0
    dx, dy = w * PUSH / 2, h * PUSH / 2
    return [list(map(float, rect)), [x0 + dx, y0 + dy, x1 - dx, y1 - dy]]


def render_crop(img, rect, out, size=(W, H)):
    x0, y0, x1, y1 = rect
    im = img.crop((int(x0), int(y0), int(x1), int(y1))).resize(size, Image.LANCZOS)
    im.save(out)
    return im


def rgba_piece(plate_rgb, alpha, out_png, out_contour):
    """#29 deliverable: RGBA piece (plate pixels + alpha) and a contour mask (1-px outline, binary)."""
    a = np.clip(alpha, 0, 255).astype(np.uint8)
    rgba = np.dstack([plate_rgb[..., :3], a])
    Image.fromarray(rgba, "RGBA").save(out_png)
    bin_ = (a > 127).astype(np.uint8)
    cnts, _ = cv2.findContours(bin_, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    c = np.zeros_like(bin_)
    cv2.drawContours(c, cnts, -1, 255, 1)
    Image.fromarray(c).save(out_contour)
    return {"px": int(bin_.sum()), "components": len(cnts)}


def drop_islands(mask, min_area, min_h=0):
    n, lab, st, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8))
    keep = np.zeros(mask.shape, np.uint8)
    for k in range(1, n):
        if st[k, cv2.CC_STAT_AREA] >= min_area and st[k, cv2.CC_STAT_HEIGHT] >= min_h:
            keep[lab == k] = 1
    return keep


def vignette(size=(W, H), corner=0.45):
    """Lens vignette multiplier (cos^4-like falloff) for the editor; corner value at the frame corners."""
    w, h = size
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.hypot((xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2)) / np.sqrt(2)
    v = 1 - (1 - corner) * r ** 2.2
    return np.clip(v, 0, 1)


def dump(obj, path):
    with open(path, "w") as f:
        json.dump(obj, f, indent=1)

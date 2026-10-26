"""Compositing: every layer is (node, affine placement, opacity, tint). Nothing is drawn here that is not a node or a
recorded synthetic op with its parameters."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def affine(pivot, dest, angle=0.0, sx=1.0, sy=1.0):
    """forward 3x3: piece px -> canvas px. angle in degrees, positive = clockwise on screen (y down)."""
    a = math.radians(angle)
    c, s = math.cos(a), math.sin(a)
    T1 = np.array([[1, 0, -pivot[0]], [0, 1, -pivot[1]], [0, 0, 1]], float)
    S = np.array([[sx, 0, 0], [0, sy, 0], [0, 0, 1]], float)
    R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], float)
    T2 = np.array([[1, 0, dest[0]], [0, 1, dest[1]], [0, 0, 1]], float)
    return T2 @ R @ S @ T1


def apply(M, p):
    v = M @ np.array([p[0], p[1], 1.0])
    return (v[0], v[1])


def place(canvas, piece, M, opacity=1.0, alpha_out=None, resample=None):
    """alpha-composite RGBA piece onto RGBA canvas with forward matrix M. alpha_out: optional L canvas to accumulate."""
    w, h = piece.size
    pts = [apply(M, p) for p in [(0, 0), (w, 0), (0, h), (w, h)]]
    x0 = max(0, int(math.floor(min(p[0] for p in pts))) - 1); y0 = max(0, int(math.floor(min(p[1] for p in pts))) - 1)
    x1 = min(canvas.size[0], int(math.ceil(max(p[0] for p in pts))) + 1); y1 = min(canvas.size[1], int(math.ceil(max(p[1] for p in pts))) + 1)
    if x1 <= x0 or y1 <= y0:
        return
    # output local (u,v) -> canvas (u+x0, v+y0) -> piece = Mi @ (u+x0, v+y0)
    Mi = np.linalg.inv(M) @ np.array([[1, 0, x0], [0, 1, y0], [0, 0, 1]], float)
    out = piece.transform((x1 - x0, y1 - y0), Image.AFFINE, tuple(Mi[:2].reshape(-1)), resample=resample if resample is not None else Image.BICUBIC)
    if opacity < 1.0:
        a = out.getchannel('A').point(lambda v: int(v * opacity))
        out.putalpha(a)
    canvas.alpha_composite(out, (x0, y0))
    if alpha_out is not None:
        alpha_out.paste(255, (x0, y0), out.getchannel('A'))

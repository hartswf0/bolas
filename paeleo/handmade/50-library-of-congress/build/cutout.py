"""Generic cut-piece blitting: a plate pixel (u, v) is the local point p = org + (u, v) / ps; the piece is rotated by a about its
rest pivot pr, moved to pn, then mapped to the screen by q = O + g * (f * x, y). Canvas: ink and coverage float arrays."""
import math
import numpy as np
from PIL import Image

def blit(canvas_ink, canvas_cov, im, org, ps, pr, pn, a, O, g=1.0, f=1, tint=None, cov_mul=1.0):
    w, h = im.size
    c0, s0 = math.cos(a), math.sin(a)
    cs = []
    for (u, v) in [(0, 0), (w, 0), (0, h), (w, h)]:
        p = (org[0] + u / ps - pr[0], org[1] + v / ps - pr[1])
        q = (c0 * p[0] - s0 * p[1] + pn[0], s0 * p[0] + c0 * p[1] + pn[1])
        cs.append((O[0] + g * f * q[0], O[1] + g * q[1]))
    H, W = canvas_ink.shape
    X0 = max(0, int(math.floor(min(c[0] for c in cs))) - 1); X1 = min(W, int(math.ceil(max(c[0] for c in cs))) + 1)
    Y0 = max(0, int(math.floor(min(c[1] for c in cs))) - 1); Y1 = min(H, int(math.ceil(max(c[1] for c in cs))) + 1)
    if X1 <= X0 or Y1 <= Y0: return None
    # inverse map: screen (X0 + i, Y0 + j) → q = ((X - O0) / (g f), (Y - O1) / g) → p = pr + R(-a)(q - pn) → u = ps (p - org)
    c, s = math.cos(-a), math.sin(-a)
    ax, ay = 1.0 / (g * f), 1.0 / g
    qx0 = (X0 - O[0]) * ax - pn[0]; qy0 = (Y0 - O[1]) * ay - pn[1]
    ua = ps * c * ax; ub = -ps * s * ay; uc = ps * (pr[0] - org[0] + c * qx0 - s * qy0)
    va = ps * s * ax; vb = ps * c * ay; vc = ps * (pr[1] - org[1] + s * qx0 + c * qy0)
    reg = im.transform((X1 - X0, Y1 - Y0), Image.AFFINE, (ua, ub, uc, va, vb, vc), resample=Image.BICUBIC)
    arr = np.asarray(reg, np.float32) / 255.
    ink, cov = arr[..., 0], arr[..., 3] * cov_mul
    ci = canvas_ink[Y0:Y1, X0:X1]; cc = canvas_cov[Y0:Y1, X0:X1]
    canvas_ink[Y0:Y1, X0:X1] = np.clip(ci * (1 - cov) + ink * cov_mul, 0, 1)
    canvas_cov[Y0:Y1, X0:X1] = cc + cov * (1 - cc)
    return (X0, Y0, X1, Y1)

def rot(v, a):
    c, s = math.cos(a), math.sin(a); return (c * v[0] - s * v[1], s * v[0] + c * v[1])
def add(a, b): return (a[0] + b[0], a[1] + b[1])
def sub(a, b): return (a[0] - b[0], a[1] - b[1])

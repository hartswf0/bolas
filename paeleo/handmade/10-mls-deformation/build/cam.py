"""SCION-10 · the camera (fixed, orthographic, looking along the porch from the street side and a little above) and the
point splatter that draws the lifted hide (and the person) in depth order."""
import numpy as np

W, H = 1280, 720
GAMMA = np.radians(36.0)      # yaw: we look a little toward the house so the wall's face and the doorway show
ELEV = np.radians(34.0)       # elevation above the floor
SCALE = 200.0                 # px per metre
F = np.array([-np.sin(GAMMA) * np.cos(ELEV), np.cos(GAMMA) * np.cos(ELEV), -np.sin(ELEV)])   # into the scene
R = np.array([np.cos(GAMMA), np.sin(GAMMA), 0.0])
UP = np.cross(R, F)
ORIGIN = np.array([280.0, 362.0])   # where the world origin (threshold, floor, centre line of the door) lands
WIDE = (SCALE, ORIGIN.copy())
# the close shot (from 21.5 s): the same camera direction, 1.65x closer, on the sill
_CS = 330.0
_cp = np.array([0.45, 0.35, 0.40])
CLOSE = (_CS, np.array([740.0, 410.0]) - _CS * np.array([_cp @ R, -(_cp @ UP)]))
CUT_T = 21.5


def use(shot):
    global SCALE, ORIGIN
    SCALE, ORIGIN = (WIDE if shot == 'wide' else CLOSE)[0], (WIDE if shot == 'wide' else CLOSE)[1].copy()


def shot_at(t):
    return 'close' if t >= CUT_T else 'wide'


def project(P):
    P = np.asarray(P, float)
    return np.stack([ORIGIN[0] + SCALE * (P @ R), ORIGIN[1] - SCALE * (P @ UP)], -1), P @ F


def unproject_floor(x, y, z=0.0):
    """screen pixel -> world point on the horizontal plane at height z."""
    # P = a R + b UP + t F ; with P.z = z
    a = (x - ORIGIN[0]) / SCALE; b = (ORIGIN[1] - y) / SCALE
    base = a[..., None] * R + b[..., None] * UP
    t = (z - base[..., 2]) / F[2]
    return base + t[..., None] * F


def splat(xy, depth, rgba, ss=2, box=None, foot=2):
    """draw points nearest-last into an ss-times supersampled canvas; returns premultiplied rgba at 1x for box (x0,y0,x1,y1)."""
    if box is None:
        x0, y0 = np.floor(xy.min(0)).astype(int) - 2; x1, y1 = np.ceil(xy.max(0)).astype(int) + 3
    else:
        x0, y0, x1, y1 = box
    x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, W), min(y1, H)
    if x1 <= x0 or y1 <= y0:
        return None
    w, h = (x1 - x0) * ss, (y1 - y0) * ss
    px = (xy[:, 0] - x0) * ss; py = (xy[:, 1] - y0) * ss
    ix = np.floor(px).astype(np.int64); iy = np.floor(py).astype(np.int64)
    order = np.argsort(-depth, kind='stable')            # far first ... near last
    cols, idxs, ranks = [], [], []
    rank = np.empty(len(depth), np.int64); rank[order] = np.arange(len(depth))
    for dx in range(foot):
        for dy in range(foot):
            jx, jy = ix + dx, iy + dy
            ok = (jx >= 0) & (jx < w) & (jy >= 0) & (jy < h)
            idxs.append((jy * w + jx)[ok]); ranks.append(rank[ok]); cols.append(np.nonzero(ok)[0])
    idx = np.concatenate(idxs); rk = np.concatenate(ranks); src = np.concatenate(cols)
    o = np.lexsort((rk, idx))
    idx, src = idx[o], src[o]
    last = np.r_[idx[1:] != idx[:-1], True]
    canvas = np.zeros((h * w, 4))
    c = rgba[src[last]]
    canvas[idx[last], :3] = c[:, :3] * c[:, 3:4]
    canvas[idx[last], 3] = c[:, 3]
    canvas = canvas.reshape(h, w, 4).reshape(h // ss, ss, w // ss, ss, 4).mean((1, 3)) if ss > 1 else canvas.reshape(h, w, 4)
    return (x0, y0, x1, y1), canvas


def over(img, layer):
    """composite a premultiplied layer (box, canvas) over img (H,W,3) in place."""
    if layer is None:
        return
    (x0, y0, x1, y1), c = layer
    img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - c[..., 3:4]) + c[..., :3]

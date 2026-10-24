"""Quick, Draw! helpers: load ndjson (drop partial last line), densify strokes,
rasterize, compute pose features from the stroke data.

Coordinates: Quick, Draw! simplified drawings live in a 0..255 box, y down.
"""
import json, math
import numpy as np
from PIL import Image, ImageDraw

QD = '/home/user/hartswf0/quickdraw'


def load(category, limit=None):
    out = []
    with open(f'{QD}/{category}.part') as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue  # partial last line
            out.append(d)
            if limit and len(out) >= limit:
                break
    return out


def strokes_np(d):
    return [np.array(s, dtype=float).T for s in d['drawing']]  # list of (n,2)


def bbox(strokes):
    P = np.concatenate(strokes)
    return P[:, 0].min(), P[:, 1].min(), P[:, 0].max(), P[:, 1].max()


def densify(strokes, step=2.0):
    out = []
    for s in strokes:
        if len(s) == 1:
            out.append(s.copy())
            continue
        pts = [s[0]]
        for a, b in zip(s[:-1], s[1:]):
            L = np.hypot(*(b - a))
            n = max(1, int(L / step))
            for k in range(1, n + 1):
                pts.append(a + (b - a) * k / n)
        out.append(np.array(pts))
    return out


def raster(strokes, N=64, pad=2, width=1):
    """Fit drawing bbox into N x N preserving aspect, anchored bottom-centre."""
    x0, y0, x1, y1 = bbox(strokes)
    w, h = max(x1 - x0, 1), max(y1 - y0, 1)
    sc = (N - 2 * pad) / max(w, h)
    img = Image.new('L', (N, N), 0)
    dr = ImageDraw.Draw(img)
    ox = (N - w * sc) / 2
    oy = N - pad - h * sc
    for s in strokes:
        pts = [((p[0] - x0) * sc + ox, (p[1] - y0) * sc + oy) for p in s]
        if len(pts) == 1:
            pts = pts * 2
        dr.line(pts, fill=255, width=width)
    return np.array(img) > 0


def features(d):
    S = strokes_np(d)
    x0, y0, x1, y1 = bbox(S)
    w, h = max(x1 - x0, 1), max(y1 - y0, 1)
    D = densify(S, 2.0)
    P = np.concatenate(D)
    u = (P[:, 0] - x0) / w  # 0..1 left..right
    v = (P[:, 1] - y0) / h  # 0..1 top..bottom
    n = len(P)
    # occupancy grid in bbox-normalized coords (24x24)
    G = np.zeros((24, 24), bool)
    gi = np.clip((v * 23.999).astype(int), 0, 23)
    gj = np.clip((u * 23.999).astype(int), 0, 23)
    G[gi, gj] = True
    # mirror symmetry of the occupancy grid (front views are symmetric)
    sym = (G & G[:, ::-1]).sum() / max(G.sum(), 1)
    # head side: ink mass in the top 35% band, left vs right
    top = v < 0.35
    hs = ((u[top] > 0.5).sum() - (u[top] < 0.5).sum()) / max(top.sum(), 1)
    # top profile: highest ink per third (smaller v = higher)
    def topv(a, b):
        m = (u >= a) & (u < b)
        return v[m].min() if m.any() else 1.0
    tl, tm, tr = topv(0, .3), topv(.35, .65), topv(.7, 1.01)
    # legs: columns with ink in the bottom 12% band -> count separate runs
    band = G[21:, :].any(0)
    runs = int(np.sum(band[1:] & ~band[:-1]) + band[0])
    # leg length: from the bottom, how many rows until a row spans > 55% width
    rowspan = np.array([(np.ptp(np.where(G[r])[0]) + 1) / 24 if G[r].any() else 0 for r in range(24)])
    legrows = 0
    for r in range(23, -1, -1):
        if rowspan[r] > 0.55 and G[r].sum() > 8:
            break
        legrows += 1
    # side ink centres of the head (the higher of left/right thirds)
    return dict(
        key_id=d['key_id'], ns=len(S), npts=int(sum(len(s) for s in S)),
        w=float(w), h=float(h), aspect=float(w / h), sym=float(sym), hs=float(hs),
        tl=float(tl), tm=float(tm), tr=float(tr), legruns=runs, legrows=legrows / 24,
        fill=float(G.mean()), recognized=d['recognized'],
    )

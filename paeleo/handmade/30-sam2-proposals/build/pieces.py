"""Mask adjudicator + manual repair artist: turns accepted SAM proposals into placeable RGBA pieces.

A piece is never unexplained pixels: it is (source, frame, polygon proposal) + recorded correction strokes
(add / sub polygons in source coordinates, or a half-plane cut through two prompt points) + mirror flag.
Everything is cut at source resolution with 4x supersampled edges, exposure-matched (luminance percentiles of the
masked region mapped to a fixed range so substitutions do not flicker), then scaled once to the stage."""
import json, math, os
import numpy as np
from PIL import Image, ImageFilter
from common import *

POSE = json.load(open(os.path.join(KIT, 'archive-dog', 'pose_agent_v8.json')))
CORR = []        # every correction stroke used, for corrections.json


def key(frame, name):
    """pose key (point prompt) for a dog frame, linearly interpolated between keyed frames"""
    ks = sorted(int(k) for k in POSE)
    if frame in ks:
        return POSE[str(frame)][name]
    lo = max(k for k in ks if k < frame); hi = min(k for k in ks if k > frame)
    a = (frame - lo) / (hi - lo)
    p, q = POSE[str(lo)][name], POSE[str(hi)][name]
    return [p[0] + a * (q[0] - p[0]), p[1] + a * (q[1] - p[1])]


def halfplane(p, q, keep_side_pt, big=2000):
    """polygon covering the half-plane bounded by the line through p,q on the side of keep_side_pt"""
    dx, dy = q[0] - p[0], q[1] - p[1]
    n = (-dy, dx)
    s = (keep_side_pt[0] - p[0]) * n[0] + (keep_side_pt[1] - p[1]) * n[1]
    if s < 0:
        n = (dy, -dx)
    L = math.hypot(dx, dy) or 1
    ux, uy = dx / L * big, dy / L * big
    nx, ny = n[0] / L * big, n[1] / L * big
    return [(p[0] - ux, p[1] - uy), (p[0] + ux, p[1] + uy), (p[0] + ux + nx, p[1] + uy + ny), (p[0] - ux + nx, p[1] - uy + ny)]


def neck_cut(frame, side='head', back=0.0):
    """the head/body boundary of a dog frame: the line through the neck key perpendicular to neck->nose.
    side='head' returns the half-plane polygon containing the nose; 'body' the other one."""
    nose, neck = key(frame, 'nose'), key(frame, 'neck')
    ax, ay = nose[0] - neck[0], nose[1] - neck[1]
    L = math.hypot(ax, ay) or 1
    neck = (neck[0] - ax / L * back, neck[1] - ay / L * back)      # move the cut back into the body (overlap for rotation)
    p = neck; q = (neck[0] - ay, neck[1] + ax)
    if side == 'head':
        return halfplane(p, q, nose)
    return halfplane(p, q, (2 * neck[0] - nose[0], 2 * neck[1] - nose[1]))


def poly_and(alpha, poly, size):
    return alpha * raster([poly], size)


_cache = {}


def cut(src, frame, mirror=False, keep=None, sub=(), add=(), scale=1.0, tone='dog', note=None, keep2=None):
    """Return (RGBA PIL image at stage scale, info) for a proposal.
    keep: list of polygons; the piece is mask AND union(keep)  (e.g. a neck half-plane)
    info: 'origin' = source coords of the crop's top-left, 'scale', 'mirror', 'W' source width, so source points map."""
    k = (src, frame, mirror, json.dumps(keep), json.dumps(keep2), json.dumps(sub), json.dumps(add), round(scale, 4), tone)
    if k in _cache:
        return _cache[k]
    im = src_frame(src, frame)
    Wd, Hd = im.size
    polys = src_masks(src)[str(frame)]
    a = raster(polys, (Wd, Hd), add=add, sub=sub)
    if keep:
        a = a * raster(keep, (Wd, Hd))
    if keep2:
        a = a * raster([keep2], (Wd, Hd))
    # 1 px choke so ground pixels at the SAM edge do not ride along
    a = np.clip((a - .3) / .7, 0, 1)
    # adjudicator: islands are not the object (SAM debris on the ground); keep the largest 4-connected component
    big = largest_component(a > .5)
    grow = big.copy()
    grow[1:, :] |= big[:-1, :]; grow[:-1, :] |= big[1:, :]; grow[:, 1:] |= big[:, :-1]; grow[:, :-1] |= big[:, 1:]
    a = a * grow
    ys, xs = np.nonzero(a > .02)
    if len(xs) == 0:
        return None
    x0, y0, x1, y1 = max(xs.min() - 3, 0), max(ys.min() - 3, 0), min(xs.max() + 4, Wd), min(ys.max() + 4, Hd)
    rgb = np.asarray(im, dtype=np.float32)[y0:y1, x0:x1] / 255.
    aa = a[y0:y1, x0:x1]
    if tone == 'dog':
        g = rgb @ np.array([.299, .587, .114], np.float32)
        full = raster(polys, (Wd, Hd))[y0:y1, x0:x1] > .5     # exposure match on the whole-dog proposal, not the part
        lo, hi = np.percentile(g[full], 1), np.percentile(g[full], 99.5)
        g = np.clip((g - lo) / max(hi - lo, 1e-3), 0, 1)
        g = .10 + .74 * g
        rgb = np.stack([g * .93, g * .95, g * 1.0], -1)
    img = np.dstack([rgb, aa])
    pim = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8), 'RGBA')
    if mirror:
        pim = pim.transpose(Image.FLIP_LEFT_RIGHT)
    w, h = pim.size
    pim = pim.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS)
    info = dict(origin=(x0, y0), crop=(x1 - x0, y1 - y0), scale=scale, mirror=mirror, W=Wd)
    _cache[k] = (pim, info)
    return _cache[k]


def to_piece(info, pt):
    """source point -> pixel inside the scaled piece"""
    x, y = pt
    x0, y0 = info['origin']; cw, ch = info['crop']
    px = x - x0
    if info['mirror']:
        px = cw - px
    return (px * info['scale'], (y - y0) * info['scale'])


def record(**kw):
    if kw not in CORR:
        CORR.append(kw)


def head_region(frame, back=6, r_scale=0.95):
    """part proposal for a head: the neck half-plane AND a disk around the head (centre between the nose and neck prompts),
    so that forelegs under a lowered head are not taken with it"""
    nose, neck = key(frame, 'nose'), key(frame, 'neck')
    cx, cy = (nose[0] + neck[0]) / 2, (nose[1] + neck[1]) / 2
    r = math.hypot(nose[0] - neck[0], nose[1] - neck[1]) * r_scale
    disk = [(cx + r * math.cos(a), cy + r * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 40, endpoint=False)]
    return [neck_cut(frame, 'head', back=back)], disk

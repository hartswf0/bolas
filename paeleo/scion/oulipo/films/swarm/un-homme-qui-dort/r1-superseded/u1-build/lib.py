"""U1 picture library: SCION-29 cutouts, SCION-44 multiplane compositing, SCION-47 action curves.

Plates are decoded with PIL only (run with python3 -I). Everything is single-channel
grey (the FSA negatives are monochrome); no tint, grain, filter or vignette is applied.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None

FILMS = Path("/home/user/bolas/paeleo/scion/oulipo/films")
SRC = FILMS / "sources" / "un-homme-qui-dort" / "u1-picture"
RAW = SRC / "raw"
for sub in ("rgba", "masks", "failure_masks", "fills", "shots", "passes", "diag"):
    (SRC / sub).mkdir(parents=True, exist_ok=True)

W, H, FPS = 960, 540, 24

# plate id -> (file, rebate crop (x0,y0,x1,y1) in that file's pixels: the picture area only)
PLATES = {
    "2017811426": ("loc_2017811426_v.jpg", (32, 32, 742, 985)),
    "2017735081": ("loc_2017735081_a2400.png", (60, 60, 2230, 1580)),
    "2017811449": ("loc_2017811449_v.jpg", (42, 24, 1004, 744)),
    "2017811447": ("loc_2017811447_v.jpg", (44, 16, 756, 975)),
    "2017714056": ("loc_2017714056_a2400.png", (50, 100, 2240, 1680)),
}


def load_plate(pid):
    f, crop = PLATES[pid]
    g = np.asarray(Image.open(RAW / f).convert("L"), dtype=np.float32) / 255.0
    return g, crop


def poly_mask(shape, polys, value=1):
    m = np.zeros(shape[:2], np.uint8)
    for p in polys:
        cv2.fillPoly(m, [np.round(np.array(p, np.float32)).astype(np.int32)], value)
    return m


def lines_mask(shape, lines, width=7):
    m = np.zeros(shape[:2], np.uint8)
    for ln in lines:
        pts = np.round(np.array(ln, np.float32)).astype(np.int32)
        cv2.polylines(m, [pts], False, 1, width)
    return m


# ------------------------------------------------------------------ SCION-29 ---
PRESETS = {
    # photograph preset: silver-gelatin grain is not body texture, so the colour model
    # sees a lightly denoised copy (bilateral, edge-preserving); edges come from the same.
    "photograph": dict(bilateral=(7, 0.08, 5), iters=8, open_r=2, close_r=3, max_hole=900, feather=1.2),
}


def grabcut(gray, rect, fg_lines=(), bg_lines=(), fg_polys=(), bg_polys=(), prfg_polys=(), preset="photograph", line_w=9):
    """cv2.grabCut with box + scribble seeds. Returns (hard mask uint8, init mask, raw gc labels)."""
    P = PRESETS[preset]
    g8 = (np.clip(gray, 0, 1) * 255).astype(np.uint8)
    d, sc, ss = P["bilateral"]
    den = cv2.bilateralFilter(g8, d, sc * 255, ss)
    img = cv2.cvtColor(den, cv2.COLOR_GRAY2BGR)
    m = np.full(gray.shape, cv2.GC_BGD, np.uint8)
    x0, y0, x1, y1 = rect
    m[y0:y1, x0:x1] = cv2.GC_PR_BGD
    if prfg_polys:
        pm = poly_mask(gray.shape, prfg_polys)
        m[(pm > 0)] = cv2.GC_PR_FGD
        m[:y0, :] = cv2.GC_BGD; m[y1:, :] = cv2.GC_BGD; m[:, :x0] = cv2.GC_BGD; m[:, x1:] = cv2.GC_BGD
    if bg_polys:
        m[poly_mask(gray.shape, bg_polys) > 0] = cv2.GC_BGD
    if fg_polys:
        m[poly_mask(gray.shape, fg_polys) > 0] = cv2.GC_FGD
    if bg_lines:
        m[lines_mask(gray.shape, bg_lines, line_w) > 0] = cv2.GC_BGD
    if fg_lines:
        m[lines_mask(gray.shape, fg_lines, line_w) > 0] = cv2.GC_FGD
    init = m.copy()
    bgd = np.zeros((1, 65), np.float64); fgd = np.zeros((1, 65), np.float64)
    cv2.setRNGSeed(29)
    cv2.grabCut(img, m, None, bgd, fgd, P["iters"], cv2.GC_INIT_WITH_MASK)
    hard = np.isin(m, (cv2.GC_FGD, cv2.GC_PR_FGD)).astype(np.uint8)
    return hard, init, m


def cleanup(hard, seed_fg, preset="photograph"):
    """Alpha cleanup: open/close, drop islands not connected to the FG seeds, fill small holes.
    Returns (clean uint8, failure mask uint8 of every pixel changed, stats)."""
    P = PRESETS[preset]
    k_o = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * P["open_r"] + 1,) * 2)
    k_c = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * P["close_r"] + 1,) * 2)
    m = cv2.morphologyEx(hard, cv2.MORPH_OPEN, k_o)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k_c)
    n, lab = cv2.connectedComponents(m, connectivity=8)
    keep = np.zeros_like(m)
    for i in range(1, n):
        comp = lab == i
        if (comp & (seed_fg > 0)).any():
            keep[comp] = 1
    islands = int(n - 1 - len(np.unique(lab[(keep > 0)])))
    # fill holes smaller than max_hole (interior speckle), keep larger ones (real gaps such as arm/body)
    inv = (1 - keep).astype(np.uint8)
    n2, lab2, st2, _ = cv2.connectedComponentsWithStats(inv, connectivity=4)
    holes = 0
    for i in range(1, n2):
        x, y, w, h, a = st2[i]
        touches = x == 0 or y == 0 or x + w >= inv.shape[1] or y + h >= inv.shape[0]
        if not touches and a <= P["max_hole"]:
            keep[lab2 == i] = 1; holes += 1
    fail = (keep != hard).astype(np.uint8)
    n3, _ = cv2.connectedComponents(keep, connectivity=8)
    return keep, fail, {"islands_removed": islands, "holes_filled": holes, "components_after": int(n3 - 1),
                        "pixels_changed_by_cleanup": int(fail.sum())}


def feather(mask, sigma=1.2):
    """Feathered alpha: edge softened by at most ~2 px (sigma 1.2)."""
    a = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), sigma)
    return np.clip(a, 0, 1)


def matting_band(gray, mask, band_poly=None, r=5, win=9):
    """Local colour-line alpha estimate in an unknown band (fur collars):
    alpha = (I - B) / (F - B) with F, B the local means of definite fg / bg pixels.
    Applied only inside band_poly (or the whole contour if None). Returns float alpha."""
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1,) * 2)
    fg = cv2.erode(mask, k); bg = 1 - cv2.dilate(mask, k)
    unk = (1 - fg - bg).astype(np.uint8)
    if band_poly is not None:
        unk = unk & poly_mask(gray.shape, band_poly)
    box = (win, win)
    sF = cv2.boxFilter(gray * fg, -1, box, normalize=False); nF = cv2.boxFilter(fg.astype(np.float32), -1, box, normalize=False)
    sB = cv2.boxFilter(gray * bg, -1, box, normalize=False); nB = cv2.boxFilter(bg.astype(np.float32), -1, box, normalize=False)
    # widen until both sides are seen
    for wbig in (21, 41):
        need = (nF < 1) | (nB < 1)
        if not need.any():
            break
        b2 = (wbig, wbig)
        sF2 = cv2.boxFilter(gray * fg, -1, b2, normalize=False); nF2 = cv2.boxFilter(fg.astype(np.float32), -1, b2, normalize=False)
        sB2 = cv2.boxFilter(gray * bg, -1, b2, normalize=False); nB2 = cv2.boxFilter(bg.astype(np.float32), -1, b2, normalize=False)
        sF = np.where(need, sF2, sF); nF = np.where(need, nF2, nF); sB = np.where(need, sB2, sB); nB = np.where(need, nB2, nB)
    F = sF / np.maximum(nF, 1e-6); B = sB / np.maximum(nB, 1e-6)
    den = F - B
    a = np.where(np.abs(den) > 0.04, (gray - B) / np.where(np.abs(den) > 0.04, den, 1), mask.astype(np.float32))
    a = np.clip(a, 0, 1)
    alpha = feather(mask)
    alpha = np.where(unk > 0, 0.5 * a + 0.5 * alpha, alpha)  # blend with the graph-cut prior: no pure-threshold halos
    alpha[fg > 0] = 1.0
    alpha[bg > 0] = np.minimum(alpha[bg > 0], 0.0 + feather(mask)[bg > 0])
    return np.clip(alpha, 0, 1), unk


def unpremult_edge(gray, alpha, mask):
    """Halo isolation: inside the soft edge, replace the cutout's colour by the colour
    of the nearest definite-foreground pixel so background does not ride along (decontamination)."""
    core = (alpha > 0.98).astype(np.uint8)
    if core.sum() == 0:
        return gray.copy()
    g8 = (gray * 255).astype(np.uint8)
    edge = ((alpha > 0.0) & (alpha <= 0.98)).astype(np.uint8)
    fixed = cv2.inpaint(g8, edge, 2, cv2.INPAINT_TELEA).astype(np.float32) / 255.0
    out = gray.copy()
    out[edge > 0] = fixed[edge > 0]
    return out


def inpaint(gray, hole, radius=6):
    g8 = (np.clip(gray, 0, 1) * 255).astype(np.uint8)
    r = cv2.inpaint(g8, hole.astype(np.uint8), radius, cv2.INPAINT_TELEA)
    return r.astype(np.float32) / 255.0


def quilt_fill(gray, hole, source, patch=40, overlap=10, cands=900, seed=44):
    """Patch-copy fill (texture extension from the plate's own pixels): fills `hole`
    in raster order with patches copied from `source` (a mask of known texture) chosen
    by SSD on the already-known overlap; seams cross-faded over the overlap."""
    rng = np.random.default_rng(seed)
    out = gray.copy()
    known = (1 - hole).astype(np.float32)
    Hh, Ww = gray.shape
    src_ok = cv2.erode(source.astype(np.uint8), np.ones((patch, patch), np.uint8), anchor=(0, 0))
    ys, xs = np.nonzero(src_ok[: Hh - patch, : Ww - patch])
    assert len(ys) > 0, "no source texture"
    hy, hx = np.nonzero(hole)
    y0, y1, x0, x1 = hy.min(), hy.max() + 1, hx.min(), hx.max() + 1
    step = patch - overlap
    ramp = np.ones((patch, patch), np.float32)
    for y in range(max(0, y0 - overlap), y1, step):
        for x in range(max(0, x0 - overlap), x1, step):
            yy, xx = min(y, Hh - patch), min(x, Ww - patch)
            region_hole = hole[yy:yy + patch, xx:xx + patch]
            if not region_hole.any():
                continue
            tgt = out[yy:yy + patch, xx:xx + patch]
            kn = known[yy:yy + patch, xx:xx + patch]
            idx = rng.choice(len(ys), size=min(cands, len(ys)), replace=False)
            best, bi = 1e18, idx[0]
            for i in idx:
                cand = gray[ys[i]:ys[i] + patch, xs[i]:xs[i] + patch]
                e = float((((cand - tgt) ** 2) * kn).sum()) / (kn.sum() + 1.0)
                if e < best:
                    best, bi = e, i
            cand = gray[ys[bi]:ys[bi] + patch, xs[bi]:xs[bi] + patch]
            # weight: known pixels keep a cross-fade, unknown take the patch
            dist = cv2.distanceTransform((1 - kn).astype(np.uint8), cv2.DIST_L2, 3) if kn.any() else np.full((patch, patch), 99, np.float32)
            wgt = np.clip(dist / overlap, 0, 1) if kn.any() else ramp
            wgt = np.where(kn > 0, 0.0, wgt)
            wgt = np.maximum(wgt, (1 - kn))  # unknown always filled
            wgt = np.where(region_hole > 0, wgt, 0.0)
            out[yy:yy + patch, xx:xx + patch] = tgt * (1 - wgt) + cand * wgt
            known[yy:yy + patch, xx:xx + patch] = np.maximum(kn, (region_hole > 0).astype(np.float32))
    return out


def save_gray(path, g):
    Image.fromarray((np.clip(g, 0, 1) * 255 + 0.5).astype(np.uint8)).save(path)


def save_mask(path, m):
    Image.fromarray((np.clip(m.astype(np.float32), 0, 1) * 255 + 0.5).astype(np.uint8)).save(path)


def save_rgba(path, g, a, bbox=None):
    g8 = (np.clip(g, 0, 1) * 255 + 0.5).astype(np.uint8)
    a8 = (np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)
    rgba = np.dstack([g8, g8, g8, a8])
    if bbox is None:
        ys, xs = np.nonzero(a8)
        bbox = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1) if len(ys) else (0, 0, 1, 1)
    x0, y0, x1, y1 = bbox
    Image.fromarray(rgba[y0:y1, x0:x1], "RGBA").save(path)
    return bbox


# ------------------------------------------------------------------ SCION-44 ---
class Layer:
    """A depth plane or articulated piece in plate coordinates.
    k: parallax factor (camera displacement multiplier); z: draw order (low = far).
    pose(t) -> 2x3 affine in plate coordinates applied before the camera (piece motion)."""

    def __init__(self, name, gray, alpha, k, z, pose=None, role="plane", invented=None):
        self.name, self.gray, self.alpha, self.k, self.z, self.pose, self.role = name, gray.astype(np.float32), alpha.astype(np.float32), k, z, pose, role
        self.invented = invented  # float mask of invented pixels in this layer (plate coords) or None
        self.pm = self.gray * self.alpha


def ident():
    return np.array([[1, 0, 0], [0, 1, 0]], np.float64)


def rot_about(px, py, deg, dx=0.0, dy=0.0):
    """Rotation by deg (screen convention: positive = counter-clockwise as seen) about (px,py), then translate."""
    M = cv2.getRotationMatrix2D((float(px), float(py)), float(deg), 1.0)
    M[0, 2] += dx; M[1, 2] += dy
    return M


def compose(A, B):
    """A after B (2x3)."""
    A3 = np.vstack([A, [0, 0, 1]]); B3 = np.vstack([B, [0, 0, 1]])
    return (A3 @ B3)[:2]


def cam_matrix(cx, cy, s):
    """plate -> output: out = s*(p - c) + centre."""
    return np.array([[s, 0, W / 2 - s * cx], [0, s, H / 2 - s * cy]], np.float64)


def layer_matrix(layer, cam, t):
    """cam(t) -> dict(c0=(x,y), d=(dx,dy) camera displacement at k=1, s0 scale, push= scale factor at k=1)."""
    c = cam(t)
    k = layer.k
    cx = c["c0"][0] + k * c["d"][0]
    cy = c["c0"][1] + k * c["d"][1]
    s = c["s0"] * (1.0 + k * (c.get("push", 1.0) - 1.0))
    M = cam_matrix(cx, cy, s)
    if layer.pose is not None:
        M = compose(M, layer.pose(t))
    return M


def composite(layers, cam, t, only=None, return_cover=False):
    acc = np.zeros((H, W), np.float32)
    aacc = np.zeros((H, W), np.float32)
    covers = {}
    for L in sorted(layers, key=lambda L: L.z):
        if only is not None and L.name not in only:
            continue
        M = layer_matrix(L, cam, t)
        pm = cv2.warpAffine(L.pm, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        a = cv2.warpAffine(L.alpha, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        acc = pm + acc * (1 - a)
        if return_cover:
            for n in list(covers):
                covers[n] = covers[n] * (1 - a)
            covers[L.name] = a.copy()
        aacc = a + aacc * (1 - a)
    if return_cover:
        return acc, aacc, covers
    return acc, aacc


def warp_invented(layers, cam, t):
    """Fraction-of-frame map of visible invented pixels."""
    inv = np.zeros((H, W), np.float32)
    for L in sorted(layers, key=lambda L: L.z):
        M = layer_matrix(L, cam, t)
        a = cv2.warpAffine(L.alpha, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
        inv = inv * (1 - a)
        if L.invented is not None:
            iv = cv2.warpAffine(L.invented * L.alpha, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
            inv = inv + iv
    return np.clip(inv, 0, 1)


# ------------------------------------------------------------------ easing ---
def smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def ease(t, a, b):
    return smooth((t - a) / (b - a)) if b > a else float(t >= b)


def sha1_rgb(img_rgb_uint8):
    return hashlib.sha1(np.ascontiguousarray(img_rgb_uint8).tobytes()).hexdigest()


def to_kit_frame(gray_out, t, k):
    """Hand the composited plate picture to kit's Ink canvas with grain off and boil 0
    (kit.paper() would otherwise add grain; kit is read, not edited)."""
    import sys
    sys.path.insert(0, str(FILMS))
    from kit import Ink  # noqa
    ink = Ink(t, k, (W, H), boil=0, wobble=0)
    ink.paper(grain=False)
    g8 = (np.clip(gray_out, 0, 1) * 255 + 0.5).astype(np.uint8)
    ink.paste(Image.fromarray(np.dstack([g8, g8, g8]), "RGB"))
    return np.asarray(ink.finish())

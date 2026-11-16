"""U1 picture library (plan-r2): plates, grade, SCION-29 cutouts, SCION-44 multiplane, stats.

Plates are decoded with PIL only; run every script with `python3 -I`.
Everything is single-channel grey from the negatives themselves. No blur, sharpening,
faux grain, vignette or tint is applied to any picture pixel. The only Gaussian in this
file is used to soften a matte's alpha edge (<= 1.2 px) and to estimate a smooth wall
under a cast shadow (flagged invented wherever it becomes visible).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None

FILMS = Path("/home/user/bolas/paeleo/scion/oulipo/films")
SRC = FILMS / "sources" / "un-homme-qui-dort"
U1 = SRC / "u1-picture-camera-drawing-team-quiet-observational-cut-scion-29-extraction-scion-44-multiplane-staging-scion-47-body-actions-aesthetic-grade-"
RAW = U1 / "raw"
OLD_RAW = SRC / "u1-picture" / "raw"          # r1 raw downloads (kept, re-verified)
for sub in ("rgba", "masks", "failure_masks", "fills", "shots", "diag", "graded", "json"):
    (U1 / sub).mkdir(parents=True, exist_ok=True)

W, H, FPS = 960, 540, 24
SS = 2  # supersample factor for warps (render at 2x, area-downsample once)

# plate id -> file, picture area (rebate excluded) in file pixels, curve class
PLATES = {
    "2017862333": dict(file=RAW / "8d33576u.tif", area=(600, 640, 4640, 4760), curve="flash1943",
                       note="Bubley Jan 1943 master TIFF 8d33576u.tif, 8-bit L 5348x5652"),
    "2017862340": dict(file=RAW / "8d33583u.tif", area=(700, 420, 4790, 4560), curve="flash1943",
                       note="Bubley Jan 1943 master TIFF 8d33583u.tif, 8-bit L 5448x5240"),
    "2017735081": dict(file=OLD_RAW / "loc_2017735081_a.tif", area=(120, 140, 4040, 2840), curve="flat1936",
                       note="Russell Lee Dec 1936 archival TIFF 8a21346a.tif (16-bit, already on disk from r1)"),
    "2017811447": dict(file=OLD_RAW / "loc_2017811447_v.jpg", area=(44, 16, 745, 975), curve="flat1936",
                       note="Vachon Dec 1940 1024px service JPEG 8c18457v.jpg"),
    "2017714056": dict(file=OLD_RAW / "loc_2017714056_a.tif", area=(110, 250, 4250, 2950), curve="flat1936",
                       note="Mydans Sept 1935 archival TIFF 8a00242a.tif (16-bit, already on disk from r1)"),
}

CURVES = {
    # a = weight of the smoothstep (midtone steepening) in the monotone curve
    "flash1943": dict(a=0.30, note="gentle toe/shoulder; flash negatives are already hard"),
    "flat1936": dict(a=0.70, note="steeper midtone: a flatter negative printed on a harder grade"),
}
L_LO, L_HI = 30.0, 244.0   # p2 -> L30 (#1e1e1e), p98 -> L244 (~#f4f4f4)
TOE_FLOOR, SHOULDER_CEIL = 22.0, 250.0


def load_plate(pid):
    """Return float32 array 0..1 of the whole file (grey), and the plate record."""
    rec = PLATES[pid]
    a = np.array(Image.open(rec["file"]))
    if a.ndim == 3:
        a = a[..., 0]
    a = a.astype(np.float32)
    a /= 65535.0 if a.max() > 255 else 255.0
    return a, rec


def make_curve(plate, rec, stats_box=None):
    """One monotone neutral curve for the plate. Input percentiles from the picture area
    (or stats_box: the union of the shots' crops, also inside the picture area)."""
    x0, y0, x1, y1 = stats_box or rec["area"]
    v = plate[y0:y1:2, x0:x1:2]
    p2, p98 = [float(x) for x in np.percentile(v, [2, 98])]
    a = CURVES[rec["curve"]]["a"]
    return dict(p2=p2, p98=p98, a=a, L_lo=L_LO, L_hi=L_HI, toe_floor=TOE_FLOOR, shoulder_ceil=SHOULDER_CEIL,
                curve_class=rec["curve"], stats_box=[int(x0), int(y0), int(x1), int(y1)])


def apply_curve(x, c):
    """Monotone curve: [p2,p98] -> [L_lo,L_hi] via (1-a)*u + a*smoothstep(u); exponential toe and
    shoulder outside with matched slope (C1), asymptotes 22 and 250. Returns float L (0..255)."""
    u = (x - c["p2"]) / (c["p98"] - c["p2"])
    a = c["a"]
    span = c["L_hi"] - c["L_lo"]
    uc = np.clip(u, 0, 1)
    mid = c["L_lo"] + span * ((1 - a) * uc + a * uc * uc * (3 - 2 * uc))
    slope = span * (1 - a)  # dL/du at both ends (smoothstep slope is 0 there)
    t = c["L_lo"] - c["toe_floor"]
    toe = c["L_lo"] - t * (1 - np.exp(np.minimum(u, 0) * slope / t))
    s = c["shoulder_ceil"] - c["L_hi"]
    sh = c["L_hi"] + s * (1 - np.exp(-np.maximum(u - 1, 0) * slope / s))
    return np.where(u < 0, toe, np.where(u > 1, sh, mid)).astype(np.float32)


def curve_table(c, n=17):
    xs = np.linspace(0, 1, n)
    return [[round(float(x), 4), round(float(y), 2)] for x, y in zip(xs, apply_curve(xs, c))]


def graded_plate(pid, stats_box=None):
    p, rec = load_plate(pid)
    c = make_curve(p, rec, stats_box)
    g = apply_curve(p, c) / 255.0
    ys = np.linspace(0, 1, 2001)
    yv = apply_curve(ys, c)
    assert np.all(np.diff(yv) >= 0), "curve not monotone"
    return g, c, rec


# ------------------------------------------------------------------ SCION-29 ---
def poly_mask(shape, polys, value=1):
    m = np.zeros(shape[:2], np.uint8)
    for p in polys:
        cv2.fillPoly(m, [np.round(np.array(p, np.float32)).astype(np.int32)], value)
    return m


def lines_mask(shape, lines, width=7):
    m = np.zeros(shape[:2], np.uint8)
    for ln in lines:
        cv2.polylines(m, [np.round(np.array(ln, np.float32)).astype(np.int32)], False, 1, width)
    return m


PRESETS = {
    # photograph preset (scan class: silver-gelatin negative). Grain is not body texture:
    # the colour model sees an edge-preserving bilateral copy; output pixels are the plate's own.
    "photograph": dict(bilateral=(7, 0.08, 5), iters=6, open_r=2, close_r=3, max_hole=600),
}


def grabcut(gray, rect, fg_polys=(), bg_polys=(), prfg_polys=(), fg_lines=(), bg_lines=(), line_w=9, preset="photograph"):
    P = PRESETS[preset]
    g8 = (np.clip(gray, 0, 1) * 255).astype(np.uint8)
    d, sc, ss = P["bilateral"]
    den = cv2.bilateralFilter(g8, d, sc * 255, ss)
    img = cv2.cvtColor(den, cv2.COLOR_GRAY2BGR)
    m = np.full(gray.shape, cv2.GC_BGD, np.uint8)
    x0, y0, x1, y1 = rect
    m[y0:y1, x0:x1] = cv2.GC_PR_BGD
    if prfg_polys:
        m[(poly_mask(gray.shape, prfg_polys) > 0)] = cv2.GC_PR_FGD
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
    return hard, init


def cleanup(hard, seed_fg, preset="photograph", max_hole=None):
    """Alpha cleanup: open/close, drop islands not touching FG seeds, fill small holes.
    Returns (clean, failure mask = every pixel changed by cleanup, stats)."""
    P = PRESETS[preset]
    max_hole = P["max_hole"] if max_hole is None else max_hole
    k_o = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * P["open_r"] + 1,) * 2)
    k_c = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * P["close_r"] + 1,) * 2)
    m = cv2.morphologyEx(hard, cv2.MORPH_OPEN, k_o)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k_c)
    n, lab = cv2.connectedComponents(m, connectivity=8)
    keep = np.zeros_like(m)
    kept = 0
    for i in range(1, n):
        comp = lab == i
        if (comp & (seed_fg > 0)).any():
            keep[comp] = 1; kept += 1
    islands = int(n - 1 - kept)
    inv = (1 - keep).astype(np.uint8)
    n2, lab2, st2, _ = cv2.connectedComponentsWithStats(inv, connectivity=4)
    holes = 0
    for i in range(1, n2):
        x, y, w, h, a = st2[i]
        touches = x == 0 or y == 0 or x + w >= inv.shape[1] or y + h >= inv.shape[0]
        if not touches and a <= max_hole:
            keep[lab2 == i] = 1; holes += 1
    fail = (keep != hard).astype(np.uint8)
    n3, _ = cv2.connectedComponents(keep, connectivity=8)
    return keep, fail, {"islands_removed": islands, "holes_filled": holes, "components_after": int(n3 - 1),
                        "pixels_changed_by_cleanup": int(fail.sum())}


def feather(mask, sigma=1.0):
    return np.clip(cv2.GaussianBlur(mask.astype(np.float32), (0, 0), sigma), 0, 1)


def matting_band(gray, mask, band_poly=None, r=6, win=11, blend=0.5):
    """Local fg/bg mean alpha estimate in an unknown band (fur, hair): alpha=(I-B)/(F-B),
    blended 50/50 with the graph-cut prior so no threshold halos. Returns alpha, unknown band."""
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1,) * 2)
    fg = cv2.erode(mask, k).astype(np.float32); bg = (1 - cv2.dilate(mask, k)).astype(np.float32)
    unk = ((1 - fg - bg) > 0).astype(np.uint8)
    if band_poly is not None:
        unk = unk & poly_mask(gray.shape, band_poly)
    sF = nF = sB = nB = None
    for w_ in (win, 31, 61):
        b = (w_, w_)
        sF_ = cv2.boxFilter(gray * fg, -1, b, normalize=False); nF_ = cv2.boxFilter(fg, -1, b, normalize=False)
        sB_ = cv2.boxFilter(gray * bg, -1, b, normalize=False); nB_ = cv2.boxFilter(bg, -1, b, normalize=False)
        if sF is None:
            sF, nF, sB, nB = sF_, nF_, sB_, nB_
        else:
            need = (nF < 1) | (nB < 1)
            sF = np.where(need, sF_, sF); nF = np.where(need, nF_, nF); sB = np.where(need, sB_, sB); nB = np.where(need, nB_, nB)
    F = sF / np.maximum(nF, 1e-6); B = sB / np.maximum(nB, 1e-6)
    den = F - B
    ok = np.abs(den) > 0.04
    a = np.clip(np.where(ok, (gray - B) / np.where(ok, den, 1), mask.astype(np.float32)), 0, 1)
    prior = feather(mask)
    alpha = np.where(unk > 0, blend * a + (1 - blend) * prior, prior)
    alpha[fg > 0] = 1.0
    return np.clip(alpha, 0, 1).astype(np.float32), unk


def decontaminate(gray, alpha):
    """Halo isolation: in the soft edge, replace colour by inpainted definite-foreground colour."""
    core = (alpha > 0.98).astype(np.uint8)
    if core.sum() == 0:
        return gray.copy()
    edge = ((alpha > 0.0) & (alpha <= 0.98)).astype(np.uint8)
    g8 = (np.clip(gray, 0, 1) * 255).astype(np.uint8)
    fixed = cv2.inpaint(g8, edge, 2, cv2.INPAINT_TELEA).astype(np.float32) / 255.0
    out = gray.copy(); out[edge > 0] = fixed[edge > 0]
    return out


def inpaint(gray, hole, radius=6):
    g8 = (np.clip(gray, 0, 1) * 255).astype(np.uint8)
    return cv2.inpaint(g8, hole.astype(np.uint8), radius, cv2.INPAINT_TELEA).astype(np.float32) / 255.0


def quilt_fill(gray, hole, source, patch=32, overlap=8, cands=700, seed=44):
    """Patch-copy fill from the plate's own texture (flagged invented)."""
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
    for y in range(max(0, y0 - overlap), y1, step):
        for x in range(max(0, x0 - overlap), x1, step):
            yy, xx = min(y, Hh - patch), min(x, Ww - patch)
            rh = hole[yy:yy + patch, xx:xx + patch]
            if not rh.any():
                continue
            tgt = out[yy:yy + patch, xx:xx + patch]
            kn = known[yy:yy + patch, xx:xx + patch]
            idx = rng.choice(len(ys), size=min(cands, len(ys)), replace=False)
            C = np.stack([gray[ys[i]:ys[i] + patch, xs[i]:xs[i] + patch] for i in idx])
            e = (((C - tgt[None]) ** 2) * kn[None]).sum((1, 2))
            cand = C[int(np.argmin(e))]
            unknown = (kn == 0).astype(np.uint8)
            if unknown.all():
                xf = np.ones_like(kn)
            else:
                dist = cv2.distanceTransform(1 - unknown, cv2.DIST_L2, 3)   # distance from unknown px
                xf = np.clip(1 - dist / overlap, 0, 1)                      # cross-fade into already-filled px
            wgt = np.where(rh > 0, np.where(unknown > 0, 1.0, xf), 0.0)
            out[yy:yy + patch, xx:xx + patch] = tgt * (1 - wgt) + cand * wgt
            known[yy:yy + patch, xx:xx + patch] = np.maximum(kn, (rh > 0).astype(np.float32))
    return out


def smooth_wall(gray, valid, sigma=60):
    """Normalized-convolution estimate of a smooth surface from valid pixels (no grain)."""
    v = valid.astype(np.float32)
    num = cv2.GaussianBlur(gray * v, (0, 0), sigma)
    den = cv2.GaussianBlur(v, (0, 0), sigma)
    return num / np.maximum(den, 1e-4)


# ------------------------------------------------------------------ files ---
def save_gray(path, g):
    Image.fromarray((np.clip(g, 0, 1) * 255 + 0.5).astype(np.uint8)).save(path)


def save_mask(path, m):
    Image.fromarray((np.clip(m.astype(np.float32), 0, 1) * 255 + 0.5).astype(np.uint8)).save(path)


def save_rgba(path, g, a, offset=(0, 0)):
    """Save tight-cropped RGBA (neutral grey). Returns bbox in the coordinates of g (+offset)."""
    a8 = (np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)
    g8 = (np.clip(g, 0, 1) * 255 + 0.5).astype(np.uint8)
    ys, xs = np.nonzero(a8)
    x0, y0, x1, y1 = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1) if len(ys) else (0, 0, 1, 1)
    Image.fromarray(np.dstack([g8, g8, g8, a8])[y0:y1, x0:x1], "RGBA").save(path)
    return [x0 + offset[0], y0 + offset[1], x1 + offset[0], y1 + offset[1]]


def sha1(path):
    return hashlib.sha1(Path(path).read_bytes()).hexdigest()


# ------------------------------------------------------------------ SCION-44 ---
def resample(img, scale):
    """Area-resample a float image/alpha from plate scale to the render scale (once per layer)."""
    h, w = img.shape[:2]
    return cv2.resize(img, (max(1, int(round(w * scale))), max(1, int(round(h * scale)))), interpolation=cv2.INTER_AREA)


class Layer:
    """A depth plane or articulated piece, prepared at render scale (SS x screen).
    gray/alpha: float arrays covering the shot's crop box (render scale);
    k: parallax factor; z: draw order; mode: 'over' or 'multiply' (cast shadow = ratio map);
    pose(fi) -> (dx, dy, angle_deg, pivot_xy) in SCREEN pixels/degrees (piece's own action)."""

    def __init__(self, name, gray, alpha, k, z, mode="over", pose=None, role="", org=(0.0, 0.0)):
        self.name, self.gray, self.alpha, self.k, self.z, self.mode = name, gray, alpha, k, z, mode
        self.org = org  # screen position (px) of the array's (0,0) at rest
        self.pose = pose or (lambda fi: (0.0, 0.0, 0.0, (0.0, 0.0)))
        self.role = role


def affine(dx, dy, ang, pivot, cam, org=(0.0, 0.0)):
    """2x3 matrix at render scale: place the array at org, rotate by ang (deg, screen CCW
    positive) about pivot (screen px), then translate by (dx,dy) + camera displacement cam."""
    th = np.deg2rad(ang)
    R = np.array([[np.cos(th), np.sin(th)], [-np.sin(th), np.cos(th)]])
    piv = np.array(pivot, np.float64) * SS
    o = np.array(org, np.float64) * SS
    t = np.array([dx + cam[0], dy + cam[1]]) * SS
    M = np.zeros((2, 3))
    M[:, :2] = R
    M[:, 2] = (np.eye(2) - R) @ piv + R @ o + t
    return M


def compose(layers, fi, cam_fn, base=None):
    """Composite layers for frame fi. cam_fn(fi)->(cx,cy, zoom, zoom_center) screen px.
    Each layer displaced by k*cam (parallax) plus its pose. Returns uint8 960x540 grey."""
    Hs, Ws = H * SS, W * SS
    out = np.zeros((Hs, Ws), np.float32) if base is None else base.copy()
    cx, cy, zoom, zc = cam_fn(fi)
    for L in sorted(layers, key=lambda l: l.z):
        dx, dy, ang, piv = L.pose(fi)
        M = affine(dx, dy, ang, piv, (L.k * cx, L.k * cy), L.org)
        if zoom != 1.0:
            # per-plane push: plane scale about zc grows with k (near planes push more)
            s = 1.0 + (zoom - 1.0) * L.k
            Z = np.array([[s, 0, (1 - s) * zc[0] * SS], [0, s, (1 - s) * zc[1] * SS], [0, 0, 1]], np.float64)
            M = (Z @ np.vstack([M, [0, 0, 1]]))[:2]
        g = cv2.warpAffine(L.gray, M, (Ws, Hs), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE if L.name.endswith("far") else cv2.BORDER_CONSTANT, borderValue=0 if L.mode == "over" else 1)
        a = cv2.warpAffine(L.alpha, M, (Ws, Hs), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE if L.name.endswith("far") else cv2.BORDER_CONSTANT, borderValue=0 if L.mode == "over" else 1)
        if L.mode == "over":
            out = g * a + out * (1 - a)
        elif L.mode == "multiply":  # gray holds the shadow ratio (<=1); alpha its extent
            out = out * (1 - a + a * g)
    small = cv2.resize(out, (W, H), interpolation=cv2.INTER_AREA)
    return (np.clip(small, 0, 1) * 255 + 0.5).astype(np.uint8)


def layer_alpha_on_screen(L, fi, cam_fn):
    Hs, Ws = H * SS, W * SS
    cx, cy, zoom, zc = cam_fn(fi)
    dx, dy, ang, piv = L.pose(fi)
    M = affine(dx, dy, ang, piv, (L.k * cx, L.k * cy), L.org)
    a = cv2.warpAffine(L.alpha, M, (Ws, Hs), flags=cv2.INTER_LINEAR, borderValue=0)
    return cv2.resize(a, (W, H), interpolation=cv2.INTER_AREA)


# ------------------------------------------------------------------ stats ---
def frame_stats(g8, head_h=None):
    """Aesthetic stats on an 8-bit frame (grey or RGB)."""
    a = np.asarray(g8)
    if a.ndim == 3:
        rgb = a.astype(np.float32)
        chroma = float((rgb.max(2) - rgb.min(2)).mean())
        L = rgb.mean(2)
    else:
        chroma = 0.0; L = a.astype(np.float32)
    p = np.percentile(L, [1, 50, 99])
    cols = [round(float(L[:, int(i * L.shape[1] / 10):int((i + 1) * L.shape[1] / 10)].mean()), 1) for i in range(10)]
    return {"mean_chroma": round(chroma, 3), "p1": round(float(p[0]), 1), "p50": round(float(p[1]), 1), "p99": round(float(p[2]), 1),
            "frac_below_60": round(float((L < 60).mean()), 3), "frac_above_220": round(float((L > 220).mean()), 3),
            "frac_60_220": round(float(((L >= 60) & (L <= 220)).mean()), 3),
            "column_mean_L_by_tenths": cols, "head_height_frac": head_h}


def to_rgb(g8):
    return np.dstack([g8, g8, g8])


def dump(path, obj):
    Path(path).write_text(json.dumps(obj, indent=1))


def texture_fill(gray, hole, source, radius=12, sigma=3.0, tile=48, seed=29):
    """Invented fill = TELEA inpaint (tone continuity) + the plate's own high-frequency residual
    (silver grain and fine texture) copied tile by tile from `source` pixels of the same plate, so
    the fill neither reads as a smooth smear nor carries added synthetic grain. Flagged invented."""
    rng = np.random.default_rng(seed)
    low = inpaint(gray, hole, radius)
    resid = gray - cv2.GaussianBlur(gray, (0, 0), sigma)
    ok = cv2.erode(source.astype(np.uint8), np.ones((tile, tile), np.uint8), anchor=(0, 0))
    ys, xs = np.nonzero(ok[: gray.shape[0] - tile, : gray.shape[1] - tile])
    out = low.copy()
    if len(ys) == 0:
        return out
    hy, hx = np.nonzero(hole)
    for y in range(hy.min(), hy.max() + 1, tile):
        for x in range(hx.min(), hx.max() + 1, tile):
            sub = hole[y:y + tile, x:x + tile]
            if not sub.any():
                continue
            i = rng.integers(len(ys))
            r = resid[ys[i]:ys[i] + sub.shape[0], xs[i]:xs[i] + sub.shape[1]]
            blk = out[y:y + tile, x:x + tile]
            blk[sub > 0] = (blk + r)[sub > 0]
    return np.where(hole > 0, np.clip(out, 0, 1), gray)

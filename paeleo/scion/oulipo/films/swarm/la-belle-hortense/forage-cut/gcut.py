"""SCION 29 GrabCut helpers for la-belle-hortense (forage-cut unit).

grabcut_piece(img, env_poly, fg_scrib, bg_scrib, dense_thr=None) -> alpha (float32 0..1), report dict, failure overlay
  img      BGR uint8 crop (decoded by OpenCV only; sources are untrusted data)
  env_poly hand-placed scissor polygon: outside is definite background (GC_BGD)
  fg_scrib list of ('ellipse', (cx,cy),(ax,ay)) | ('poly', [(x,y),...]) definite-foreground seeds
  bg_scrib same shapes, definite-background seeds
  dense_thr luminance below which pixels inside the envelope are probable foreground (dark subject on pale ground);
            None -> everything inside the envelope is probable foreground (box seed)
Cleanup: largest component only (islands counted), holes filled unless keep_holes, 3x3 open, 1-2 px feathered alpha.
"""
import numpy as np, cv2


def _draw(mask, shapes, val):
    for s in shapes:
        if s[0] == 'ellipse':
            cv2.ellipse(mask, tuple(map(int, s[1])), tuple(map(int, s[2])), 0, 0, 360, val, -1)
        elif s[0] == 'poly':
            cv2.fillPoly(mask, [np.array(s[1], np.int32)], val)
        elif s[0] == 'line':     # hand scissor stroke along thin parts (cast iron), width s[2]
            cv2.polylines(mask, [np.array(s[1], np.int32)], False, val, int(s[2]))
        elif s[0] == 'rect':
            x0, y0, x1, y1 = s[1]
            cv2.rectangle(mask, (x0, y0), (x1, y1), val, -1)
    return mask


def grabcut_piece(img, env_poly, fg_scrib=(), bg_scrib=(), dense_thr=None, iters=6, keep_holes=False, invert_dense=False, min_part=None):
    h, w = img.shape[:2]
    g = cv2.GaussianBlur(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255., (5, 5), 0)
    env = np.zeros((h, w), np.uint8)
    cv2.fillPoly(env, [np.array(env_poly, np.int32)], 1)
    gc = np.full((h, w), cv2.GC_PR_BGD, np.uint8)
    if dense_thr is None:
        prior = env.copy()
    elif isinstance(dense_thr, str) and dense_thr.startswith('lowsat'):
        # grey/black objects (bench slats, cast iron) on saturated ground (autumn leaves): saturation prior
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        sat = cv2.GaussianBlur(hsv[..., 1].astype(np.float32) / 255., (3, 3), 0)
        parts = dense_thr.split(':')
        pale = g > 0.50
        if len(parts) > 2:      # pale (slats) only above this row: below it pale is paving, not bench
            pale[int(parts[2]):] = False
        prior = (sat < float(parts[1])) & ((g < 0.22) | pale)   # dark iron or pale slat
        prior = prior.astype(np.uint8) * env
    else:
        prior = ((g > dense_thr) if invert_dense else (g < dense_thr)).astype(np.uint8) * env
    gc[prior == 1] = cv2.GC_PR_FGD
    gc[env == 0] = cv2.GC_BGD
    if isinstance(dense_thr, str):
        # colour prior is trusted away from its edge: cleaned prior = PR_FGD, a 3 px band = PR_BGD, rest = BGD
        prior = cv2.morphologyEx(prior, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
        prior = cv2.morphologyEx(prior, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
        nn, ll, ss, _ = cv2.connectedComponentsWithStats(prior)
        prior = np.isin(ll, [i for i in range(1, nn) if ss[i, cv2.CC_STAT_AREA] >= 40]).astype(np.uint8)
        band = cv2.dilate(prior, np.ones((7, 7), np.uint8))
        gc[:] = cv2.GC_BGD
        gc[(band == 1) & (env == 1)] = cv2.GC_PR_BGD
        gc[(prior == 1) & (env == 1)] = cv2.GC_PR_FGD
    fg = _draw(np.zeros((h, w), np.uint8), fg_scrib, 1)
    bg = _draw(np.zeros((h, w), np.uint8), bg_scrib, 1)
    gc[(fg == 1) & (env == 1)] = cv2.GC_FGD
    gc[bg == 1] = cv2.GC_BGD
    bgd = np.zeros((1, 65), np.float64); fgd = np.zeros((1, 65), np.float64)
    cv2.grabCut(img, gc, None, bgd, fgd, iters, cv2.GC_INIT_WITH_MASK)
    m = np.isin(gc, (cv2.GC_FGD, cv2.GC_PR_FGD)).astype(np.uint8) * env
    if isinstance(dense_thr, str):
        # thin cast-iron parts lose to the ground GMM; union with the cleaned colour-key matte (manual-contour fallback)
        m = np.maximum(m, prior * env)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    islands = 0
    if n > 1:
        if min_part:   # multi-part object (bench legs detach from seat at the cut): keep parts >= min_part px
            keep = [i for i in range(1, n) if st[i, cv2.CC_STAT_AREA] >= min_part]
            islands = int(n - 1 - len(keep))
            m = np.isin(lab, keep).astype(np.uint8)
        else:
            k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
            islands = int(n - 2)
            m = (lab == k).astype(np.uint8)
    holes = np.zeros_like(m)
    if not keep_holes:
        ff = m.copy(); fm = np.zeros((h + 2, w + 2), np.uint8)
        cv2.floodFill(ff, fm, (0, 0), 2)
        holes = (ff == 0).astype(np.uint8)
        m = np.where(ff == 2, 0, 1).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    alpha = cv2.GaussianBlur(m.astype(np.float32), (3, 3), 0)
    fail = np.zeros((h, w, 3), np.uint8)
    fail[(prior == 1) & (m == 0)] = (0, 0, 255)   # prior said figure, cut removed (red)
    fail[(prior == 0) & (m == 1)] = (0, 255, 0)   # prior said ground, cut kept (green)
    fail[holes == 1] = (255, 0, 0)                # holes filled (blue)
    over = cv2.addWeighted(img, 0.55, fail, 0.8, 0)
    rep = {'islands_removed': islands, 'fg_px': int(m.sum()), 'holes_filled_px': int(holes.sum()),
           'prior_disagree_px': int(((prior == 1) != (m == 1)).sum())}
    return alpha, rep, over


def rgba(img_gray_or_bgr, alpha):
    """RGBA uint8 (RGB order) from a gray float 0..1 / BGR uint8 image and alpha 0..1."""
    if img_gray_or_bgr.ndim == 2:
        c = np.clip(img_gray_or_bgr * 255, 0, 255).astype(np.uint8)
        rgb = np.dstack([c, c, c])
    else:
        rgb = img_gray_or_bgr[..., ::-1]
    return np.dstack([rgb, np.clip(alpha * 255, 0, 255).astype(np.uint8)])


def trim(rgba_arr, pad=2):
    """Crop to alpha bbox; returns (arr, (x0,y0)) offset in input coords."""
    a = rgba_arr[..., 3]
    ys, xs = np.nonzero(a > 8)
    if len(xs) == 0:
        return rgba_arr, (0, 0)
    x0, y0 = max(0, xs.min() - pad), max(0, ys.min() - pad)
    x1, y1 = min(a.shape[1], xs.max() + pad + 1), min(a.shape[0], ys.max() + pad + 1)
    return rgba_arr[y0:y1, x0:x1], (int(x0), int(y0))

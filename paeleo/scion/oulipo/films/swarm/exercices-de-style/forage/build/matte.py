"""#29 GrabCut + #31 trimap / alpha matting / foreground decontamination, shared by the cut scripts.
Inputs: RGB uint8 image, seed mask with cv2.GC_* labels. Outputs: alpha float [0,1], decontaminated RGB, band mask."""
import cv2, numpy as np

def grabcut(rgb, seeds, iters=8, scale=1.0):
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    H, W = seeds.shape
    if scale != 1.0:
        bgr_s = cv2.resize(bgr, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        m = cv2.resize(seeds, (bgr_s.shape[1], bgr_s.shape[0]), interpolation=cv2.INTER_NEAREST)
    else:
        bgr_s, m = bgr, seeds.copy()
    bg = np.zeros((1, 65)); fg = np.zeros((1, 65))
    cv2.grabCut(bgr_s, m, None, bg, fg, iters, cv2.GC_INIT_WITH_MASK)
    hard = np.where((m == 1) | (m == 3), 255, 0).astype(np.uint8)
    if scale != 1.0:
        hard = (cv2.resize(hard, (W, H), interpolation=cv2.INTER_LINEAR) > 127).astype(np.uint8) * 255
    return hard

def clean(hard, keep_largest=True, fill_holes=True, open_k=5, close_k=7):
    m = hard.copy()
    if keep_largest:
        n, lab, st, _ = cv2.connectedComponentsWithStats(m)
        if n > 1:
            i = 1 + np.argmax(st[1:, 4]); m = (lab == i).astype(np.uint8) * 255
    if fill_holes:
        inv = 255 - m; n, lab, st, _ = cv2.connectedComponentsWithStats(inv); H, W = m.shape
        for j in range(1, n):
            x, y, w, h, a = st[j]
            if x > 0 and y > 0 and x + w < W and y + h < H: m[lab == j] = 255
    if open_k: m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((open_k, open_k), np.uint8))
    if close_k: m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((close_k, close_k), np.uint8))
    return m

def matte(rgb, hard, band=4, win=9):
    """Trimap = erode/dilate of hard mask. In the unknown band, alpha is solved per pixel from
    local foreground / background colour estimates (sampled by inpainting each side into the band):
    alpha = <I-B, F-B> / |F-B|^2. Foreground colour is then decontaminated: F_est = B + (I-B)/alpha."""
    k = np.ones((2 * band + 1, 2 * band + 1), np.uint8)
    fg = cv2.erode(hard, k); bgm = 255 - cv2.dilate(hard, k)
    unknown = (fg == 0) & (bgm == 0)
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    # F estimate: inpaint from inside; B estimate: inpaint from outside
    F = cv2.inpaint(bgr, (255 - fg).astype(np.uint8), win, cv2.INPAINT_TELEA)
    B = cv2.inpaint(bgr, (255 - bgm).astype(np.uint8), win, cv2.INPAINT_TELEA)
    I = bgr.astype(np.float32); F = F.astype(np.float32); B = B.astype(np.float32)
    d = F - B; den = (d * d).sum(2)
    a = ((I - B) * d).sum(2) / np.maximum(den, 1e-3)
    # where F and B are too alike, fall back to a smoothed hard edge
    soft = cv2.GaussianBlur(hard.astype(np.float32) / 255, (0, 0), 1.2)
    a = np.where(den > 400, a, soft)
    a = np.clip(a, 0, 1)
    alpha = np.where(fg > 0, 1.0, np.where(unknown, a, 0.0)).astype(np.float32)
    alpha = cv2.GaussianBlur(alpha, (3, 3), 0) * (unknown | (fg > 0)) + (fg > 0) * 0  # light smoothing in band only
    alpha = np.where(fg > 0, 1.0, alpha)
    # decontaminate: in the band take the inside-estimated colour blended toward observed where alpha is high
    Fd = np.where(unknown[..., None], F * (1 - alpha[..., None]) * 0.7 + np.clip(B + (I - B) / np.maximum(alpha[..., None], 0.15), 0, 255) * (1 - (1 - alpha[..., None]) * 0.7), I)
    out = cv2.cvtColor(np.clip(Fd, 0, 255).astype(np.uint8), cv2.COLOR_BGR2RGB)
    return alpha, out, unknown

def failmask(alpha, unknown, hard):
    """Failure mask (RGB): red = unknown band, yellow = semi-opaque speckle islands outside the main body,
    blue = alpha holes inside the hard mask."""
    H, W = alpha.shape
    fm = np.zeros((H, W, 3), np.uint8)
    fm[unknown] = (200, 30, 30)
    isl = ((alpha > 0.05) & (hard == 0)).astype(np.uint8)
    fm[isl > 0] = (240, 220, 0)
    holes = (alpha < 0.5) & (cv2.erode(hard, np.ones((9, 9), np.uint8)) > 0)
    fm[holes] = (40, 80, 255)
    return fm

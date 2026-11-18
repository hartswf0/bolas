"""Shared helpers for the renzo-e-luciana proposal keyframes (decode-only use of foraged files)."""
import os, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter, ImageFont
ROOT = '/home/user/bolas/paeleo/scion/oulipo'
SRC = ROOT + '/films/sources/renzo-e-luciana'
OUT = ROOT + '/films/swarm/renzo-e-luciana/proposals'
W, H = 1280, 720
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'
def font(size, path=FONT): return ImageFont.truetype(path, size)

def grey(path):
    return np.asarray(Image.open(path).convert('L')).astype(np.float32)

def grabcut(gray, rect, fg=(), bg=(), iters=6):
    """gray float array; rect (x0,y0,x1,y1); fg/bg are polygons (lists of xy) forced as sure fg/bg."""
    img = cv2.cvtColor(np.clip(gray, 0, 255).astype(np.uint8), cv2.COLOR_GRAY2BGR)
    mask = np.zeros(gray.shape, np.uint8)
    x0, y0, x1, y1 = rect
    mask[:] = cv2.GC_BGD
    mask[y0:y1, x0:x1] = cv2.GC_PR_FGD
    for p in bg: cv2.fillPoly(mask, [np.array(p, np.int32)], cv2.GC_BGD)
    for p in fg: cv2.fillPoly(mask, [np.array(p, np.int32)], cv2.GC_FGD)
    b = np.zeros((1, 65), np.float64); f = np.zeros((1, 65), np.float64)
    cv2.grabCut(img, mask, None, b, f, iters, cv2.GC_INIT_WITH_MASK)
    m = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    # keep largest component, close holes
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    if n > 1:
        k = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]); m = np.where(lab == k, 255, 0).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    return m

def cut_edge(mask, seed=1, amp=1.2):
    """scissor edge: slight jitter + 1px hard edge, so the cutout reads as cut paper."""
    rng = np.random.default_rng(seed)
    h, w = mask.shape
    dx = cv2.GaussianBlur(rng.normal(0, 1, (h, w)).astype(np.float32), (0, 0), 9) * amp * 30
    dy = cv2.GaussianBlur(rng.normal(0, 1, (h, w)).astype(np.float32), (0, 0), 9) * amp * 30
    X, Y = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    m = cv2.remap(mask, X + dx, Y + dy, cv2.INTER_LINEAR)
    return np.where(m > 127, 255, 0).astype(np.uint8)

def layer(gray, mask):
    """RGBA PIL layer from grey + mask, with a thin pale paper rim where the cut exposes paper."""
    g = np.clip(gray, 0, 255).astype(np.uint8)
    rim = cv2.subtract(mask, cv2.erode(mask, np.ones((3, 3), np.uint8)))
    g2 = g.copy(); g2[rim > 0] = np.clip(g[rim > 0] * .4 + 150, 0, 255).astype(np.uint8)
    rgb = np.stack([g2] * 3, -1)
    return Image.fromarray(np.dstack([rgb, mask]), 'RGBA')

def paste(canvas, lay, xy, shadow=(6, 8), blur=7, dark=0.45, scale=1.0, angle=0.0, pivot=None):
    """paste an RGBA cutout with a soft cast shadow (paper lifted off the plate)."""
    if scale != 1.0:
        lay = lay.resize((max(1, int(lay.width * scale)), max(1, int(lay.height * scale))), Image.LANCZOS)
    if angle:
        lay = lay.rotate(angle, resample=Image.BICUBIC, expand=True, center=pivot)
    a = lay.split()[3]
    sh = Image.new('RGBA', lay.size, (0, 0, 0, 0))
    sh.putalpha(a.point(lambda v: int(v * dark)).filter(ImageFilter.GaussianBlur(blur)))
    canvas.alpha_composite(sh, (xy[0] + shadow[0], xy[1] + shadow[1]))
    canvas.alpha_composite(lay, xy)
    return lay

def grain(img, amt=7, seed=3):
    a = np.asarray(img.convert('RGB')).astype(np.float32)
    rng = np.random.default_rng(seed)
    n = cv2.GaussianBlur(rng.normal(0, 1, a.shape[:2]).astype(np.float32), (0, 0), .8) * amt
    a += n[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

def paper(w, h, base=200, seed=5, fibre=10):
    rng = np.random.default_rng(seed)
    n = rng.normal(0, 1, (h, w)).astype(np.float32)
    f = cv2.GaussianBlur(n, (0, 0), 1.2) * fibre * .6 + cv2.GaussianBlur(n, (0, 0), 18) * fibre * 6
    # horizontal fibre streaks
    s = cv2.GaussianBlur(rng.normal(0, 1, (h, w)).astype(np.float32), (41, 1), 0) * fibre * .8
    return np.clip(base + f + s, 0, 255)

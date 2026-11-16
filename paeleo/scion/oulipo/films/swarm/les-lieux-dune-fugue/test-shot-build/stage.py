"""Paper stage for the les-lieux-dune-fugue TEST SHOT (P01 prise B: the door opens onto the
remembered bench, closes, hard cut to P03 in silence).

Simulated tabletop capture (SCION 40): every visible piece is a scissor-cut paper piece whose
texture is a *print* of a foraged public-domain photograph (one global tone curve per print run)
on a foraged 1934 paper-stock scan. One lamp model per capture state casts true height-based
shadows (offset = dz * horizontal lamp vector / lamp height, blur grows with dz * lamp size) and
lights the cut core on the lamp side. Multiplane (SCION 44): facade 0, leaves 0.05, memory bench
0.6, memory park 1.0; parallax = truck * (1 - depth). Forward kinematics (SCION 32): wall -> jamb
-> leaf (revolute about a vertical hinge, pinhole f=1100) -> knob child (fixed in leaf space).
Pure numpy / PIL / cv2.  No kit grain, no vignette.
"""
import os, json, math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

ROOT = "/home/user/bolas/paeleo/scion/oulipo"
R2 = ROOT + "/films/sources/les-lieux-dune-fugue/r2"
TS = ROOT + "/films/sources/les-lieux-dune-fugue/test-shot"
CUT = TS + "/cut"
W, H, P = 960, 720, 12
SW, SH = W + 2 * P, H + 2 * P
F_PIN = 1100.0
rng = np.random.default_rng(1978)


def load(p):
    return np.asarray(Image.open(p).convert("RGB")).astype(np.float32) / 255.0


def lum(a):
    return a[..., 0] * 0.299 + a[..., 1] * 0.587 + a[..., 2] * 0.114


def to8(a):
    return (np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)


# ------------------------------------------------------------------ sources
DOOR_C = load(R2 + "/hs_10700_10776.jpg")      # LoC 2010719611, Columbus courthouse doorway
DOOR_S = load(R2 + "/hs_25800_25800.jpg")      # LoC 2014630119, Savannah custom house door
BENCH = load(R2 + "/bench/sac_23429.jpg")      # LoC 2013633886, Sacramento park bench
STOCK = load(TS + "/dl/ftp_blank_sheet.jpg")[300:2300, 400:2900]   # LoC musftpsets.200218222
STOCK_L = lum(STOCK)
STOCK_CREAM = STOCK.reshape(-1, 3).mean(0)


def fibre(h, w):
    """multiplicative paper-stock modulation, cut from a random spot of the 1934 sheet"""
    y = int(rng.integers(0, STOCK.shape[0] - h)) if h < STOCK.shape[0] else 0
    x = int(rng.integers(0, STOCK.shape[1] - w)) if w < STOCK.shape[1] else 0
    s = STOCK_L[y:y + h, x:x + w]
    if s.shape != (h, w):
        s = cv2.resize(s, (w, h))
    hp = s / (cv2.GaussianBlur(s, (0, 0), 25) + 1e-4)
    return (1 + 0.9 * (hp - 1))[..., None].astype(np.float32)


# ------------------------------------------------------------------ prints
def print_run(img, target, ref_L, gamma, lo=0.0, hi=1.0):
    """one global tone curve for a whole print run: out_c = target_c * (L/ref_L)**gamma"""
    L = np.clip(lum(img), 1e-4, 1)
    r = np.clip((L / ref_L) ** gamma, lo, hi)
    return (r[..., None] * np.asarray(target, np.float32)[None, None] / 255.0).astype(np.float32)


def cold_print(img):
    L = lum(img)
    L = np.clip((L - 0.04) / 0.80, 0, 1) ** 0.95
    lo, hi = np.array([0.11, 0.13, 0.165]), np.array([0.60, 0.665, 0.74])
    return (lo + L[..., None] * (hi - lo)).astype(np.float32)


# ------------------------------------------------------------------ scissors
def scissor_alpha(w, h, inset=1.0, jit=0.7, nick=0.06, ss=4):
    """a hand-scissored outline of a w x h piece: straight facets of random length with small
    angle errors, plus occasional nicks; rendered 4x and reduced (antialiased)."""
    pts = []
    corners = [(inset, inset), (w - inset, inset), (w - inset, h - inset), (inset, h - inset)]
    for k in range(4):
        (x0, y0), (x1, y1) = corners[k], corners[(k + 1) % 4]
        L = math.hypot(x1 - x0, y1 - y0)
        nx, ny = -(y1 - y0) / L, (x1 - x0) / L        # inward normal (clockwise in image coords)
        s = 0.0
        while s < L:
            f = s / L
            off = abs(rng.normal(0, jit))
            px, py = x0 + (x1 - x0) * f + nx * off, y0 + (y1 - y0) * f + ny * off
            pts.append((px, py))
            if rng.random() < nick and 6 < s < L - 6:       # a small scissor nick
                d = rng.uniform(1.5, 3.0)
                pts.append((px + (x1 - x0) / L * 1.5 + nx * d, py + (y1 - y0) / L * 1.5 + ny * d))
            s += rng.uniform(9, 38)
    im = Image.new("L", (w * ss, h * ss), 0)
    ImageDraw.Draw(im).polygon([(x * ss, y * ss) for x, y in pts], fill=255)
    return np.asarray(im.resize((w, h), Image.LANCZOS)).astype(np.float32) / 255.0


# ------------------------------------------------------------------ lamp + compositing
class Lamp:
    def __init__(self, x, y, z, size, warm=(1.0, 1.0, 1.0), shadow=0.42):
        self.x, self.y, self.z, self.size = x, y, z, size
        self.warm = np.asarray(warm, np.float32)
        self.shadow = shadow
        yy, xx = np.mgrid[0:SH, 0:SW].astype(np.float32)
        r = np.sqrt((xx - x) ** 2 + (yy - y) ** 2 + z ** 2)
        E = (z / r) ** 3
        cy, cx = SH / 2, SW / 2
        E0 = (z / math.sqrt((cx - x) ** 2 + (cy - y) ** 2 + z ** 2)) ** 3
        self.E = (0.78 + 0.22 * (E / E0) ** 0.5)[..., None] * self.warm   # soft, mostly diffuse

    def offset(self, cx, cy, z_piece, dz):
        k = dz / max(self.z - z_piece, 1)
        return (cx - self.x) * k, (cy - self.y) * k, 0.5 + dz * self.size / max(self.z - z_piece, 1)


def shift(a, dx, dy):
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    return cv2.warpAffine(a, M, (a.shape[1], a.shape[0]), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)


def cut_core(alpha, lamp, x0, y0):
    """lighter cut core on the lamp-facing edge of a piece (white paper core of a print)"""
    gy, gx = np.gradient(alpha)
    n = np.sqrt(gx * gx + gy * gy) + 1e-6
    h, w = alpha.shape
    yy, xx = np.mgrid[0:h, 0:w]
    lx, ly = lamp.x - (xx + x0), lamp.y - (yy + y0)
    ln = np.sqrt(lx * lx + ly * ly) + 1e-6
    lit = np.clip((-gx * lx - gy * ly) / (n * ln), 0, 1)       # outward normal = -grad
    edge = np.clip(n * 2.2, 0, 1) * alpha
    return (edge * lit) ** 0.8


class Piece:
    def __init__(self, name, rgb, alpha, x, y, z, zb, src, curl=0.03):
        self.name, self.rgb, self.a, self.x, self.y, self.z, self.zb, self.src = name, rgb, alpha, x, y, z, zb, src
        h, w = alpha.shape
        ang = rng.uniform(0, 2 * math.pi)
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        g = ((xx / w - .5) * math.cos(ang) + (yy / h - .5) * math.sin(ang))
        self.curl = (1 + curl * g)[..., None]
        self.fib = fibre(h, w)


def compose(base, pieces, lamp, log=None):
    """composite pieces bottom-up with height-based lamp shadows; returns rgb, alpha"""
    can = base.copy()
    A = np.zeros(can.shape[:2], np.float32) if base.ndim == 3 else None
    for p in sorted(pieces, key=lambda q: q.z):
        h, w = p.a.shape
        cx, cy = p.x + w / 2, p.y + h / 2
        dx, dy, blur = lamp.offset(cx, cy, p.z, p.z - p.zb)
        pad = int(abs(dx) + abs(dy) + 3 * blur + 4)
        X0, Y0 = max(p.x - pad, 0), max(p.y - pad, 0)
        X1, Y1 = min(p.x + w + pad, SW), min(p.y + h + pad, SH)
        sh = np.zeros((Y1 - Y0, X1 - X0), np.float32)
        ox, oy = p.x - X0, p.y - Y0
        sub = sh[max(oy, 0):oy + h, max(ox, 0):ox + w]
        sub[:] = p.a[max(-oy, 0):max(-oy, 0) + sub.shape[0], max(-ox, 0):max(-ox, 0) + sub.shape[1]]
        sh = cv2.GaussianBlur(shift(sh, dx, dy), (0, 0), blur)
        can[Y0:Y1, X0:X1] *= (1 - lamp.shadow * sh)[..., None]
        # the piece itself
        px0, py0, px1, py1 = max(p.x, 0), max(p.y, 0), min(p.x + w, SW), min(p.y + h, SH)
        sl = (slice(py0 - p.y, py1 - p.y), slice(px0 - p.x, px1 - p.x))
        core = cut_core(p.a, lamp, p.x, p.y)[sl][..., None]
        col = p.rgb[sl] * p.fib[sl] * p.curl[sl]
        col = col * (1 - 0.55 * core) + STOCK_CREAM * 0.80 * 0.55 * core
        col = col * lamp.E[py0:py1, px0:px1]
        a = p.a[sl][..., None]
        can[py0:py1, px0:px1] = can[py0:py1, px0:px1] * (1 - a) + col * a
        if A is not None:
            A[py0:py1, px0:px1] = np.maximum(A[py0:py1, px0:px1], a[..., 0])
        if log is not None:
            log.append(dict(piece=p.name, src=p.src, x=int(p.x - P), y=int(p.y - P), w=int(w), h=int(h),
                            z_px=p.z, shadow_dx=round(dx, 2), shadow_dy=round(dy, 2), shadow_blur=round(blur, 2)))
    return can, A


def crop_resize(img, x0, y0, x1, y1, w, h):
    return cv2.resize(img[y0:y1, x0:x1], (w, h), interpolation=cv2.INTER_AREA)


def plain_patch(img, sw, sh, area, avoid, tries=400):
    """find a patch of plain ashlar (no real joint inside) in the source: minimise the strongest
    row/column dip of the blurred luminance"""
    L = lum(img)
    best, bs = None, 1e9
    ax0, ay0, ax1, ay1 = area
    for _ in range(tries):
        x = int(rng.integers(ax0, ax1 - sw)); y = int(rng.integers(ay0, ay1 - sh))
        if any(not (x + sw < a0 or x > a1 or y + sh < b0 or y > b1) for a0, b0, a1, b1 in avoid):
            continue
        q = L[y:y + sh, x:x + sw]
        r, c = q.mean(1), q.mean(0)
        sc = max(np.abs(r - np.median(r)).max(), np.abs(c - np.median(c)).max())
        if sc < bs:
            best, bs = (x, y), sc
    return best

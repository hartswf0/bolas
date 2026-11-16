import numpy as np
from PIL import Image, ImageFont, ImageDraw, ImageFilter

ROOT = "/home/user/bolas/paeleo/scion/oulipo"
SRC = ROOT + "/films/sources/les-lieux-dune-fugue/r2"
OUT = ROOT + "/films/swarm/les-lieux-dune-fugue/proposals"
FONTS = ROOT + "/assets/fonts/"


def font(kind, size):
    f = {"serif": "instrument-serif.woff2", "sans": "instrument-sans.woff2",
         "mono": "ibm-plex-mono.woff2"}[kind]
    return ImageFont.truetype(FONTS + f, size)


def load(p):
    return np.asarray(Image.open(p).convert("RGB")).astype(np.float32) / 255.0


def save(a, p):
    Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)).save(p)


def lum(a):
    return a[..., 0] * 0.299 + a[..., 1] * 0.587 + a[..., 2] * 0.114


# warm sandstone ramp measured by eye against fugue1.webp (dark door ~#1d1a16,
# stone mid ~#9c8a6a, stone light ~#d8c8a4)
RAMP = [(0.0, (0.07, 0.06, 0.05)), (0.18, (0.13, 0.11, 0.09)),
        (0.5, (0.55, 0.48, 0.36)), (0.75, (0.76, 0.68, 0.53)),
        (1.0, (0.90, 0.84, 0.70))]


def warm(a, keep=0.25, gamma=1.0):
    L = np.clip(lum(a), 0, 1) ** gamma
    out = np.zeros_like(a)
    xs = [r[0] for r in RAMP]
    for c in range(3):
        out[..., c] = np.interp(L, xs, [r[1][c] for r in RAMP])
    return out * (1 - keep) + (a * out.mean() / max(a.mean(), 1e-3)) * keep


def fit_crop(a, box, size):
    x0, y0, x1, y1 = box
    im = Image.fromarray((np.clip(a[y0:y1, x0:x1], 0, 1) * 255).astype(np.uint8))
    return np.asarray(im.resize(size, Image.LANCZOS)).astype(np.float32) / 255.0

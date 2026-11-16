import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
SRC = "/home/user/bolas/paeleo/scion/oulipo/films/sources/monsieur-ripois/"
OUT = "/home/user/bolas/paeleo/scion/oulipo/films/swarm/monsieur-ripois/proposals/"
SERIF_I = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"
SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
SERIF_B = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
MONO = "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf"
rng = np.random.default_rng(1954)

def font(p, s): return ImageFont.truetype(p, s)

def subtitle(img, text, y, size=30):
    """1950s release-print subtitle: white italic serif with a thin dark edge."""
    d = ImageDraw.Draw(img); f = font(SERIF_I, size)
    w = d.textlength(text, font=f); x = (img.width - w) / 2
    for dx in (-2, -1, 0, 1, 2):
        for dy in (-2, -1, 0, 1, 2):
            d.text((x + dx, y + dy), text, font=f, fill=(12, 12, 12))
    d.text((x, y), text, font=f, fill=(244, 242, 236))

def grain(a, amt=7.0, seed=0):
    r = np.random.default_rng(seed)
    n = r.normal(0, amt, a.shape[:2])
    import cv2; n = cv2.GaussianBlur(n.astype(np.float32), (0, 0), 0.6)
    if a.ndim == 3: n = n[..., None]
    return np.clip(a.astype(np.float32) + n, 0, 255).astype(np.uint8)

def silver(gray, tone=(1.0, 0.985, 0.95)):
    """neutral-warm silver gelatin print tone for a grayscale array"""
    g = gray.astype(np.float32)
    return np.clip(np.stack([g * tone[0], g * tone[1], g * tone[2]], -1), 0, 255).astype(np.uint8)

def pillar(pic, W=1280, H=720):
    c = Image.new("RGB", (W, H), (6, 6, 6)); c.paste(pic, ((W - pic.width) // 2, (H - pic.height) // 2)); return c

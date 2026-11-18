"""Ink tools for the cercle-vicieux test shot (copied from proposals/kf_common.py; line widths made parameters)
Shared ink tools for the cercle-vicieux keyframes (deterministic, PIL/cv2/numpy only).
Everything is rendered at 2x (2560x1440) and reduced to 1280x720."""
import math, random
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter

S = 2                      # supersample
W, H = 1280 * S, 720 * S
ROOT = "/home/user/bolas/paeleo/scion/oulipo"
SRC = ROOT + "/films/sources"
LOC = SRC + "/la-machine-a-tuer-le-temps/loc_%s.jpg"
CLIPF = SRC + "/cercle-vicieux/frames/%s/%03d.png"
PAPER = 247
INK = 8


def rng(seed):
    return random.Random(seed)


# ------------------------------------------------------------ brush line
def brush_poly(d, pts, width, seed=0, closed=True, fill=INK):
    """Ink line whose width swells and thins, like a brush or nib."""
    r = rng(seed)
    P = list(pts) + ([pts[0]] if closed else [])
    for (x0, y0), (x1, y1) in zip(P, P[1:]):
        n = max(2, int(math.hypot(x1 - x0, y1 - y0) / 2))
        for i in range(n + 1):
            t = i / n
            w = width * (0.75 + 0.5 * abs(math.sin(t * math.pi + r.random() * 0.3)))
            x = x0 + (x1 - x0) * t + r.uniform(-0.6, 0.6)
            y = y0 + (y1 - y0) * t + r.uniform(-0.6, 0.6)
            d.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=fill)


def panel_frame(d, box, seed=0, width=7):
    x0, y0, x1, y1 = box
    brush_poly(d, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], width, seed)


# ------------------------------------------------------------ hand lettering
def letter_line(img, text, cx, cy, size, seed=0, color=INK, thick=None):
    """Single-stroke capitals (Hershey simplex strokes), each glyph placed by hand:
    small random baseline drift, tilt and scale, like a letterer's pen."""
    r = rng(seed)
    font = cv2.FONT_HERSHEY_SIMPLEX
    sc = size / 22.0
    thick = thick or max(2, int(size / 9))
    glyphs = []
    for ch in text:
        (gw, gh), _ = cv2.getTextSize(ch, font, sc, thick)
        glyphs.append((ch, gw * 1.0 if ch != " " else gw * 1.15))
    total = sum(g[1] for g in glyphs)
    x = cx - total / 2
    a = np.array(img)
    for ch, gw in glyphs:
        if ch != " ":
            pad = int(size * 1.6)
            tile = np.zeros((pad, pad), np.uint8)
            s2 = sc * r.uniform(0.94, 1.06)
            cv2.putText(tile, ch, (int(pad * 0.2), int(pad * 0.75)), font, s2, 255, thick, cv2.LINE_AA)
            M = cv2.getRotationMatrix2D((pad / 2, pad / 2), r.uniform(-4, 4), 1.0)
            M[0, 1] += -0.08   # slight forward lean
            tile = cv2.warpAffine(tile, M, (pad, pad))
            ox = int(x - pad * 0.2)
            oy = int(cy - pad * 0.75 + size * 0.5 + r.uniform(-1.5, 1.5) * S)
            y0, x0 = max(0, oy), max(0, ox)
            y1, x1 = min(a.shape[0], oy + pad), min(a.shape[1], ox + pad)
            if y1 > y0 and x1 > x0:
                t = tile[y0 - oy:y1 - oy, x0 - ox:x1 - ox].astype(np.float32) / 255
                reg = a[y0:y1, x0:x1].astype(np.float32)
                a[y0:y1, x0:x1] = (reg * (1 - t) + color * t).astype(np.uint8)
        x += gw
    return Image.fromarray(a), total


def wrap(text, n):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > n and cur:
            lines.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    lines.append(cur)
    return lines


def balloon(img, text, cx, cy, size, tail, seed=0, maxc=16, kind="speech", fill=255, lw=7):
    lines = wrap(text.upper(), maxc)
    lh = size * 1.45
    widths = [len(l) * size * 0.74 for l in lines]
    bw = max(widths) / 2 + size * 1.2
    bh = len(lines) * lh / 2 + size * 0.9
    d = ImageDraw.Draw(img)
    r = rng(seed)
    pts = []
    for i in range(64):
        a = i / 64 * 2 * math.pi
        k = 1 + r.uniform(-0.012, 0.012)
        pts.append((cx + math.cos(a) * bw * k, cy + math.sin(a) * bh * k))
    tx, ty = tail
    ang = math.atan2(ty - cy, tx - cx)
    b1 = (cx + math.cos(ang - 0.18) * bw * 0.85, cy + math.sin(ang - 0.18) * bh * 0.85)
    b2 = (cx + math.cos(ang + 0.18) * bw * 0.85, cy + math.sin(ang + 0.18) * bh * 0.85)
    if kind != "caption":
        d.polygon([b1, (tx, ty), b2], fill=fill)
        brush_poly(d, [b1, (tx, ty), b2], lw, seed + 1, closed=False)
    d.polygon(pts, fill=fill)
    if kind == "whisper":
        for i in range(0, 64, 2):
            brush_poly(d, [pts[i], pts[(i + 1) % 64]], lw, seed + i, closed=False)
    else:
        brush_poly(d, pts, lw, seed + 2)
    if kind != "caption":
        d.polygon([b1, (tx, ty), b2], fill=fill)
        brush_poly(d, [b1, (tx, ty)], lw, seed + 3, closed=False)
        brush_poly(d, [(tx, ty), b2], lw, seed + 4, closed=False)
    y = cy - (len(lines) - 1) * lh / 2
    for i, l in enumerate(lines):
        img, _ = letter_line(img, l, cx, y, size, seed + 10 + i)
        y += lh
    return img


def caption_box(img, text, x0, y0, size, maxc=18, seed=0, lw=7):
    lines = wrap(text.upper(), maxc)
    lh = size * 1.45
    w = max(len(l) for l in lines) * size * 0.74 + size * 1.6
    h = len(lines) * lh + size * 0.9
    d = ImageDraw.Draw(img)
    d.rectangle([x0, y0, x0 + w, y0 + h], fill=255)
    brush_poly(d, [(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h)], lw, seed)
    y = y0 + size * 0.45 + lh / 2
    for i, l in enumerate(lines):
        img, _ = letter_line(img, l, x0 + w / 2, y, size, seed + 20 + i)
        y += lh
    return img


# ------------------------------------------------------------ print stage
def bayer(n=8):
    m = np.array([[0]])
    while m.shape[0] < n:
        m = np.block([[4 * m, 4 * m + 2], [4 * m + 3, 4 * m + 1]])
    return (m + 0.5) / m.size


def ink_print(gray, lo=0.30, hi=0.66, dot=7):
    """Three-state print: solid black, white paper, and a screened mid-tone
    of round dots (the Zip-a-tone a letterer pastes in)."""
    g = gray.astype(np.float32) / 255
    out = np.full(g.shape, PAPER, np.uint8)
    out[g < lo] = INK
    mid = (g >= lo) & (g < hi)
    yy, xx = np.mgrid[0:g.shape[0], 0:g.shape[1]]
    cx = (xx % dot) - dot / 2 + 0.5
    cy = (yy % dot) - dot / 2 + 0.5
    rr = np.sqrt(cx ** 2 + cy ** 2) / (dot * 0.62)
    cover = 1 - (g - lo) / (hi - lo)      # darker -> bigger dots
    dots = rr < np.sqrt(np.clip(cover, 0, 1)) * 0.95
    out[mid & dots] = INK
    return out


def load_gray(path):
    return np.array(Image.open(path).convert("L"))


def clahe(g, clip=2.0):
    return cv2.createCLAHE(clipLimit=clip, tileGridSize=(8, 8)).apply(g)


def fit_crop(g, box_src, out_w, out_h):
    x0, y0, x1, y1 = box_src
    c = g[y0:y1, x0:x1]
    return cv2.resize(c, (out_w, out_h), interpolation=cv2.INTER_CUBIC)


def cut_line(mask, width):
    """Scissor edge: the ink outline a cut-paper piece gets when it is pasted down."""
    k = np.ones((3, 3), np.uint8)
    dil = cv2.dilate(mask, k, iterations=width)
    return (dil > 0) & ~(mask > 0)


def finish(img, path):
    img = img.convert("L").resize((1280, 720), Image.LANCZOS).convert("RGB")
    img.save(path)
    return img

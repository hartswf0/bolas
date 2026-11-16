"""Shared material for the teuf-teuf proposal keyframes.

Everything here is either decoded from foraged files in films/sources/teuf-teuf/
(PIL / cv2 decode only) or made procedurally (charcoal, spray, cut card).
"""
import math, os
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

ROOT = "/home/user/bolas/paeleo/scion/oulipo"
SRC = ROOT + "/films/sources/teuf-teuf"
OUT = ROOT + "/films/swarm/teuf-teuf/proposals"
W, H = 1280, 720
CREAM = np.array([233, 226, 204], np.float32)   # sampled from the reference ground
INK = np.array([28, 25, 22], np.float32)        # reference silhouette black
RNG = np.random.default_rng(1956)


def load(name):
    return np.asarray(Image.open(os.path.join(SRC, name)).convert("RGB")).astype(np.float32)


def cover(img, w=W, h=H, ox=0.5, oy=0.5):
    ih, iw = img.shape[:2]
    s = max(w / iw, h / ih)
    r = cv2.resize(img, (int(iw * s + 1), int(ih * s + 1)), interpolation=cv2.INTER_AREA)
    x0 = int((r.shape[1] - w) * ox); y0 = int((r.shape[0] - h) * oy)
    return r[y0:y0 + h, x0:x0 + w]


def tone(lum, lo=INK, hi=CREAM):
    """map 0..1 luminance to the reference's two-colour sepia ramp"""
    l = np.clip(lum, 0, 1)[..., None]
    return lo + (hi - lo) * l


def rock_wall(seed=0):
    """Cueva de las Manos photograph (Suzko, CC BY-SA 3.0) re-toned to the
    reference: high-pass rock grain lifted to cream, the real red stencils
    kept as soft dark hands."""
    a = load("hands_cueva.jpg")
    a = cover(a, ox=0.5, oy=0.4)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    lum = (0.30 * r + 0.59 * g + 0.11 * b) / 255.0
    red = np.clip((r - g) / 255.0 * 2.2, 0, 1)                 # the ochre/red pigment
    red = cv2.GaussianBlur(red, (0, 0), 1.2)
    base = cv2.GaussianBlur(lum, (0, 0), 40)
    hp = lum - base                                              # rock grain only
    l = 0.95 + hp * 0.85 - red * 0.95
    l = cv2.GaussianBlur(l, (0, 0), 0.7)
    return tone(l)


def charcoal_band(img, ytop_fn, ybot_fn, dark=0.10, seed=0):
    """a rubbed charcoal band between two wavy edges (like the reference's
    dark top and bottom bands)."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    xs = np.arange(W, dtype=np.float32)
    t = ytop_fn(xs)[None, :]; bt = ybot_fn(xs)[None, :]
    m = np.clip((yy - t) / 14 + 0.5, 0, 1) * np.clip((bt - yy) / 14 + 0.5, 0, 1)
    streak = cv2.GaussianBlur(rng.random((H, W)).astype(np.float32), (0, 0), sigmaX=18, sigmaY=1.5)
    streak = (streak - streak.mean()) / (streak.std() + 1e-6)
    grain = rng.random((H, W)).astype(np.float32)
    l = dark + 0.10 * streak + 0.10 * (grain > 0.8)
    l = np.clip(l, 0, 1)
    m = m[..., None]
    return img * (1 - m) + (img * 0.25 + tone(l) * 0.75) * m


def spray(img, mask, reach=22, density=0.5, seed=0, darkness=0.85):
    """airbrush / blown-pigment halo around a mask, as on the reference's
    hand stencils and silhouettes."""
    rng = np.random.default_rng(seed)
    m8 = (mask > 0.5).astype(np.uint8)
    dist = cv2.distanceTransform(1 - m8, cv2.DIST_L2, 5)
    p = np.exp(-dist / (reach * 0.45)) * (dist > 0) * (dist < reach * 2.2)
    dots = (rng.random(mask.shape) < p * density).astype(np.float32)
    dots = cv2.GaussianBlur(dots, (0, 0), 0.8) * 2.2
    haze = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), reach * 0.35) * 0.35
    a = np.clip(dots + haze, 0, 1) * darkness * (1 - mask)
    return img * (1 - a[..., None]) + INK * a[..., None]


def ink_fill(img, mask, seed=0, dry=0.18):
    """fill a silhouette with charcoal-black that has dry-brush streaks."""
    rng = np.random.default_rng(seed)
    st = cv2.GaussianBlur(rng.random(mask.shape).astype(np.float32), (0, 0), sigmaX=9, sigmaY=1.2)
    st = (st - st.mean()) / (st.std() + 1e-6)
    l = np.clip(0.06 + dry * 0.25 * np.clip(st - 0.9, 0, None), 0, 0.3)
    m = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 0.9)[..., None]
    return img * (1 - m) + tone(l) * m


def scratch(img, pts_list, width=2, seed=0, light=1.06):
    """white scratched line (the reference's engraved ghost animals)."""
    m = Image.new("L", (W * 2, H * 2), 0)
    d = ImageDraw.Draw(m)
    rng = np.random.default_rng(seed)
    for pts in pts_list:
        pp = [(x * 2 + rng.normal(0, 1), y * 2 + rng.normal(0, 1)) for x, y in pts]
        d.line(pp, fill=255, width=width * 2, joint="curve")
    a = np.asarray(m.resize((W, H), Image.LANCZOS)).astype(np.float32) / 255
    br = rng.random((H, W)) > 0.25
    a = a * br
    return img * (1 - a[..., None]) + np.clip(CREAM * light, 0, 255) * a[..., None]


def poly_mask(polys, ss=3):
    m = Image.new("L", (W * ss, H * ss), 0)
    d = ImageDraw.Draw(m)
    for p in polys:
        if isinstance(p, tuple) and p[0] == "ellipse":
            _, cx, cy, rx, ry = p
            d.ellipse([(cx - rx) * ss, (cy - ry) * ss, (cx + rx) * ss, (cy + ry) * ss], fill=255)
        else:
            d.polygon([(x * ss, y * ss) for x, y in p], fill=255)
    return np.asarray(m.resize((W, H), Image.LANCZOS)).astype(np.float32) / 255


def limb(p0, p1, w0, w1, n=8):
    """tapered capsule polygon from p0 to p1 (a cut-card limb)"""
    (x0, y0), (x1, y1) = p0, p1
    a = math.atan2(y1 - y0, x1 - x0)
    pts = []
    for i in range(n + 1):
        t = a + math.pi / 2 + math.pi * i / n
        pts.append((x1 + w1 * math.cos(t - math.pi), y1 + w1 * math.sin(t - math.pi)))
    for i in range(n + 1):
        t = a + math.pi / 2 + math.pi * i / n
        pts.append((x0 + w0 * math.cos(t), y0 + w0 * math.sin(t)))
    return pts


def fk(root, angles, lengths):
    """forward kinematics chain: returns joint positions (angles in degrees,
    each relative to its parent, 0 = pointing right, +ve = clockwise on screen)"""
    pts = [root]; a = 0.0
    x, y = root
    for ang, L in zip(angles, lengths):
        a += math.radians(ang)
        x += L * math.cos(a); y += L * math.sin(a)
        pts.append((x, y))
    return pts


def font(size, kind="serif-italic"):
    f = {"serif-italic": "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf",
         "serif": "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
         "mono": "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"}[kind]
    return ImageFont.truetype(f, size)


def caption(im, text, y=668, size=26):
    """the commentary caption: a small italic line, ink on the wall."""
    d = ImageDraw.Draw(im)
    f = font(size)
    w = d.textlength(text, font=f)
    d.text(((W - w) / 2 + 1, y + 1), text, font=f, fill=(0, 0, 0))
    d.text(((W - w) / 2, y), text, font=f, fill=(240, 234, 214))
    return im


def finish(arr, vignette=0.22, grain=5, seed=0):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    v = 1 - vignette * np.clip(r - 0.55, 0, None) ** 1.5
    a = arr * v[..., None] + rng.normal(0, grain, (H, W, 1))
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

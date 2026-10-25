"""SCION 03 Ernst · the archive iconographer: cut the source fragments out of public-domain footage and engrave them.

Each fragment: a found frame (copied into ../src/), its SAM mask, a crop, and an engraving in this plate's burin, saved as
RGBA layers in build/cache/frag_<name>.npz: ink coverage, the cut mask, and the white cut margin (the seam that can be
shown or concealed).  Run once; render.py loads the results.
"""
import json, os, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import burin

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SHOTS = '/home/user/hartswf0/secondhand-motion/shots'
SRC = os.path.join(ROOT, 'src')
CACHE = os.path.join(HERE, 'cache')

# name: (shot, frame, crop box in source px (x0,y0,x1,y1) or None for the mask's bbox, scale, line angle deg, period px, mirror)
FRAGS = {
    'lion_head': ('lion', 22, None, 2.0, 24, 3.4, False),     # the magistrate's head: 3/4, looking right
    'lion_head_b': ('lion', 21, None, 2.0, 24, 3.4, False),   # substitution partner while calling
    'lion_mask': ('lion', 17, None, 1.6, 90, 3.2, False),     # the keystone: frontal
    'hand': ('hand', 10, None, 2.0, 70, 3.2, True),           # the reaching / offered hand (mirrored to point right)
    'lantern': ('lantern', 20, None, 0.8, 0, 3.0, False),     # the hall lamp
    'mane': ('lion', 22, None, 2.0, 24, 3.4, True),           # round 2: the lion's mane as the dog's hackles (mirrored)
    'mane_r': ('lion', 22, None, 2.0, 24, 3.4, False),        # the same mane, unmirrored (for the dog facing away)
}


RADIAL = {'mane': (0.3, 0.55, 150), 'mane_r': (0.7, 0.55, 150), 'lion_head': (0.7, 0.55, 150), 'lion_head_b': (0.7, 0.55, 150), 'lion_mask': (0.5, 0.56, 110)}


def load_mask(shot, i, W, H):
    m = json.load(open(os.path.join(SHOTS, shot + '-sam', 'masks.json')))
    polys = m[str(i)]
    im = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(im)
    if shot == 'lion' and len(polys) > 1:
        polys = polys[:1]
    for p in polys:
        if len(p) >= 3:
            d.polygon([tuple(q) for q in p], fill=255)
    return im


def make(name):
    shot, i, box, sc, ang, per, mirror = FRAGS[name]
    fpath = os.path.join(SHOTS, shot + '-sam', 'frames', 'f%03d.jpg' % i)
    os.makedirs(os.path.join(SRC, shot), exist_ok=True)
    dst = os.path.join(SRC, shot, 'f%03d.jpg' % i)
    if not os.path.exists(dst):
        shutil.copy(fpath, dst)
    im = Image.open(fpath).convert('L')
    mk = load_mask(shot, i, im.width, im.height)
    if name.startswith('lion_head'):
        # the head only: cut below the mane (the body is excluded by the mask already for f022)
        pass
    bb = mk.getbbox() if box is None else box
    pad = 6
    bb = (max(0, bb[0] - pad), max(0, bb[1] - pad), min(im.width, bb[2] + pad), min(im.height, bb[3] + pad))
    im = im.crop(bb); mk = mk.crop(bb)
    if mirror:
        im = im.transpose(Image.FLIP_LEFT_RIGHT); mk = mk.transpose(Image.FLIP_LEFT_RIGHT)
    w, h = int(im.width * sc), int(im.height * sc)
    im = im.resize((w, h), Image.BICUBIC); mk = mk.resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(1.2))
    g = np.asarray(im, float) / 255
    m = np.asarray(mk, float) / 255
    if name in ('mane', 'mane_r'):
        # only the mane: the face is cut away with scissors (a disc around it), leaving a crescent of fur
        yy0, xx0 = np.mgrid[0:h, 0:w].astype(float)
        fx, fy, _ = RADIAL[name]
        r0 = np.hypot(xx0 - fx * w, (yy0 - fy * h) * 0.95)
        m = m * np.clip((r0 - 0.27 * min(w, h)) / 4.0, 0, 1)
    # tone: stretch the fragment's own range, so every fragment is cut to the same density (the seam concealed by burin)
    inside = m > 0.5
    lo, hi = np.percentile(g[inside], 3), np.percentile(g[inside], 97)
    t = np.clip((g - lo) / max(hi - lo, 1e-3), 0, 1)
    t = np.clip(t + 1.3 * (t - burin.blur(t, 3)), 0, 1)          # an engraver's emphasis of the fur and the features
    dark = np.clip(1 - t, 0, 1) ** 0.8
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    a = np.radians(ang)
    lum_b = burin.blur(t, 3)
    u = (xx * np.sin(a) + yy * np.cos(a)) / per + 1.4 * lum_b
    v = (xx * np.sin(a + 1.1) + yy * np.cos(a + 1.1)) / per
    if name in RADIAL:
        # a mane is engraved with lines that radiate from the face; the face itself with fine rings
        fx, fy, nl = RADIAL[name]
        cx, cy = fx * w, fy * h
        r = np.hypot(xx - cx, yy - cy)
        th = np.arctan2(yy - cy, xx - cx)
        u_rad = th / (2 * np.pi) * nl + 0.9 * lum_b
        u_ring = r / per + 1.2 * lum_b
        u = u_rad
        v = u_ring
    cov = burin.engrave(u, v, dark * 0.95, knee=0.66)
    # an outline at the cut, and the margin of white paper left around it by the scissors
    mm = m > 0.5
    edge = burin.edge(mm, 0.8)
    grow = burin.blur(mm.astype(float), 5) > 0.02
    margin = grow & ~mm
    cov = np.maximum(cov * m, edge * 0.8)
    np.savez_compressed(os.path.join(CACHE, 'frag_%s.npz' % name), cov=cov.astype(np.float32), mask=m.astype(np.float32),
                        margin=burin.blur(margin.astype(float), 1).astype(np.float32))
    return dict(name=name, shot=shot, frame=i, size=(w, h), crop=bb, scale=sc, mirror=mirror, src=os.path.relpath(dst, ROOT))


if __name__ == '__main__':
    os.makedirs(CACHE, exist_ok=True)
    out = [make(n) for n in FRAGS]
    json.dump(out, open(os.path.join(CACHE, 'fragments.json'), 'w'), indent=1)
    for o in out:
        print(o)

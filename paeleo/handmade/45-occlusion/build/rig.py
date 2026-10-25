"""SCION 45 · Layer dependency engineer. Semantic sublayers of the archive dog and their placement.

A 'part' is an RGBA sublayer cut from one real cel by a hand-authored holdout polygon (source px).
A 'pose' places parts by explicit 2D affine transforms (rotate about a pivot, then translate) into a dog-local canvas,
in a declared order (the dog's own small occlusion DAG: far legs < torso < near legs < head unless a pose says otherwise).
Nothing is drawn: every visible pixel of the dog is a pixel of the 1950s home movie.
Version: rig-v4
"""
import math, os, json
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
CELS = os.path.join(HERE, 'cache/cels')
_cache = {}


def cel(i):
    if i not in _cache:
        _cache[i] = Image.open(os.path.join(CELS, 'dog_%03d.png' % i)).convert('RGBA')
    return _cache[i]


def holdout(img, poly, feather=0.8):
    """Multiply the cel's alpha by a polygon matte (the part's own holdout)."""
    from PIL import ImageFilter
    m = Image.new('L', img.size, 0)
    ImageDraw.Draw(m).polygon(poly, fill=255)
    if feather:
        m = m.filter(ImageFilter.GaussianBlur(feather))
    a = np.array(img)[:, :, 3].astype(np.float32) * (np.array(m).astype(np.float32) / 255)
    out = np.array(img).copy()
    out[:, :, 3] = a.astype(np.uint8)
    return Image.fromarray(out)


# ---- part library: (source cel, holdout polygon, pivot) in source px. Authored by eye on 5x grids of each cel.
PARTS = {
    # frame 10: standing, left profile, head up (the alert watcher)
    'head10':  (10, [(55, 55), (128, 55), (128, 88), (104, 152), (55, 152)], (112, 122)),
    'torso10': (10, [(124, 55), (250, 55), (250, 176), (208, 173), (183, 167), (150, 162), (110, 159), (99, 152), (124, 88)], (160, 150)),
    'foreA10': (10, [(127, 158), (153, 158), (153, 210), (127, 210)], (140, 163)),
    'foreB10': (10, [(88, 153), (123, 153), (123, 196), (88, 196)], (114, 160)),
    'hind10':  (10, [(179, 178), (211, 178), (211, 203), (179, 203)], (195, 180)),   # round 2: cut lower, drawn behind the torso
    # frame 0: the dog seen three-quarters from behind, looking up and away: head, ear and back of the skull
    'head0':   (0, [(100, 56), (152, 56), (154, 98), (142, 120), (104, 124), (99, 100)], (124, 118)),
    # frame 2: the bushy tail (frame 10's tail is hidden behind its hind leg)
    'tail2':   (2, [(211, 126), (241, 126), (241, 163), (221, 163), (210, 151)], (214, 137)),
    # frame 28: frontal head (face to camera); used as the head mid-turn, and in silhouette as the back of the head
    'headF':   (28, [(139, 90), (207, 90), (207, 124), (196, 136), (173, 142), (150, 137), (139, 124)], (173, 136)),
}


def part(name):
    key = ('part', name)
    if key not in _cache:
        if name == 'headBack':
            _cache[key] = head_back()
        else:
            src, poly, piv = PARTS[name]
            _cache[key] = (holdout(cel(src), poly, 1.6 if name in ('hind10', 'foreA10', 'foreB10') else 0.8), piv)
    return _cache[key]


def head_back():
    """The back of the head, as a matte and a fill: the outline is the frontal head of f28 (a head's outline is the same
    from in front and from behind), the fill is the dog's own neck-and-shoulder fur from f10 pushed through that matte, so
    no face shows. Compositing, not drawing: every pixel is the dog's."""
    hf, piv = part('headF')
    a = np.array(hf)[:, :, 3]
    ys, xs = np.nonzero(a > 10)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    fur = cel(10).crop((128, 96, 192, 146)).convert('RGB').resize((x1 - x0, y1 - y0), Image.BICUBIC)
    out = np.zeros_like(np.array(hf))
    out[y0:y1, x0:x1, :3] = np.array(fur)
    out[:, :, 3] = a
    return Image.fromarray(out), piv


def affine(img, piv, theta_deg, dst, scale=(1.0, 1.0), flip=False, out_size=(384, 288)):
    """Place img so that source point piv lands at dst after rotation theta (deg, clockwise on screen) and scale.
    flip mirrors about the pivot (used only for a whole pose, never as a turn)."""
    t = math.radians(theta_deg)
    sx, sy = scale
    if flip:
        sx = -sx
    c, s = math.cos(t), math.sin(t)
    # forward: p' = R * S * (p - piv) + dst ; PIL needs inverse mapping out->in
    a, b, d_, e = c * sx, -s * sy, s * sx, c * sy
    det = a * e - b * d_
    ia, ib, id_, ie = e / det, -b / det, -d_ / det, a / det
    ox, oy = dst
    cx = piv[0] - (ia * ox + ib * oy)
    cy = piv[1] - (id_ * ox + ie * oy)
    return img.transform(out_size, Image.AFFINE, (ia, ib, cx, id_, ie, cy), resample=Image.BICUBIC)


def fwd(pt, piv, theta_deg, dst, scale=(1.0, 1.0)):
    t = math.radians(theta_deg); c, s = math.cos(t), math.sin(t)
    x, y = (pt[0] - piv[0]) * scale[0], (pt[1] - piv[1]) * scale[1]
    return (c * x - s * y + dst[0], s * x + c * y + dst[1])


def compose(layers, size=(384, 288)):
    """layers: list of (img, piv, theta, dst, scale) in back-to-front order -> RGBA canvas (dog-local)."""
    out = Image.new('RGBA', size, (0, 0, 0, 0))
    for (img, piv, th, dst, sc) in layers:
        out = Image.alpha_composite(out, affine(img, piv, th, dst, sc, out_size=size))
    return out

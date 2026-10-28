"""SCION 11 · Video Puppetry Tabletop -- the puppets.

The dog is not drawn. It is cut from the real home-movie footage in the kit
(Amateur Film New Jersey C, Home Movies collection, Internet Archive, public domain):
two frames of the same dog, each cut out with its SAM mask, each given a set of named
control handles placed by eye on that frame (the "tracked points" of the puppet).

  L  : frame 6  -- the dog in profile facing left, head raised (the watching dog)
  F  : frame 38 -- the same dog three-quarter to the camera, facing right (the turning dog)

Mirrors of these two (R = mirror L, F' = mirror F) give the other half of a turn; a paper
cut-out is turned over in the hand the same way.

Every pose the film needs is made by bending those pixels: moving-least-squares rigid
deformation (Schaefer, McPhail & Warren 2006), driven by the handle targets the
performance supplies.  Nothing on the dog is painted; its pixels are the footage's pixels.

Coordinates
  source : pixels of the 384x288 kit frame, y down
  canon  : puppet space, source px relative to the anchor (belly point on the ground),
           always written as if the dog faces LEFT (x<0 = toward its nose)
  screen : 1280x720 film pixels
"""
import json, os
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
KIT = os.path.join(ROOT, 'paeleo/handmade/kit/archive-dog')
CACHE = os.path.join(HERE, 'cache')

NAMES = ['nose', 'skull', 'throat', 'withers', 'back', 'rump', 'tailroot', 'tailmid', 'tailtip',
         'chest', 'belly', 'flank', 'fk1', 'f1', 'fk2', 'f2', 'hk1', 'h1', 'hk2', 'h2',
         'ft1', 'ft2', 'ht1', 'ht2']
BODY = ['nose', 'skull', 'throat', 'withers', 'back', 'rump', 'tailroot', 'tailmid', 'tailtip',
        'chest', 'belly', 'flank', 'ft1', 'ft2', 'ht1', 'ht2']
# leg pieces: name -> (top, knee, foot); far legs are laid under the body, near legs over it
LEGS = {'f1': ('ft1', 'fk1', 'f1'), 'h1': ('ht1', 'hk1', 'h1'), 'f2': ('ft2', 'fk2', 'f2'), 'h2': ('ht2', 'hk2', 'h2')}
FAR, NEAR = ['f1', 'h1'], ['f2', 'h2']
HEAD = ['nose', 'skull', 'throat']
TAIL = ['tailmid', 'tailtip']

# handles placed by eye on 5x enlargements of the kit frames (proof/handles_*.png shows them)
SRC = {
    'L': {'frame': 6, 'anchor': (165, 200), 'flip_src': False, 'h': {
        'nose': (91, 84), 'skull': (116, 96), 'throat': (110, 124), 'withers': (150, 108),
        'back': (183, 116), 'rump': (213, 121), 'tailroot': (224, 130), 'tailmid': (246, 146),
        'tailtip': (270, 156), 'chest': (124, 150), 'belly': (163, 154), 'flank': (199, 158),
        'ft1': (121, 152), 'fk1': (122, 172), 'f1': (120, 190), 'ft2': (142, 152), 'fk2': (138, 178), 'f2': (131, 199),
        'ht1': (188, 158), 'hk1': (192, 178), 'h1': (191, 195), 'ht2': (212, 158), 'hk2': (214, 182), 'h2': (210, 200)},
        'belly': [(110, 230), (113, 151), (124, 152), (163, 156), (199, 160), (215, 158), (224, 158), (228, 230)]},
    # frame 38 faces right in the source; its canon (facing left) is its mirror
    'F': {'frame': 38, 'anchor': (192, 198), 'flip_src': True, 'h': {
        'nose': (228, 139), 'skull': (207, 114), 'throat': (214, 160), 'withers': (196, 108),
        'back': (180, 101), 'rump': (165, 102), 'tailroot': (160, 108), 'tailmid': (157, 113),
        'tailtip': (155, 118), 'chest': (209, 172), 'belly': (188, 166), 'flank': (170, 160),
        'ft1': (187, 165), 'fk1': (187, 180), 'f1': (186, 193), 'ft2': (206, 165), 'fk2': (214, 182), 'f2': (225, 199),
        'ht1': (173, 158), 'hk1': (173, 168), 'h1': (172, 178), 'ht2': (161, 148), 'hk2': (161, 166), 'h2': (161, 182)},
        'belly': [(150, 160), (175, 162), (200, 168), (215, 168), (240, 168)]},
}
SCALE_FIX = {'L': 1.0, 'F': 1.06}  # F is a little farther from the home-movie camera


def raster_alpha(polys, W, H, ss=4, erode=True):
    im = Image.new('L', (W * ss, H * ss), 0)
    d = ImageDraw.Draw(im)
    for p in polys:
        if len(p) > 2:
            d.polygon([(x * ss, y * ss) for x, y in p], fill=255)
    if erode:
        im = im.filter(ImageFilter.MinFilter(3))
    im = im.resize((W, H), Image.LANCZOS)
    a = np.asarray(im, np.float32) / 255.
    return a


def tone(g, a):
    """lighting normalisation between keys: the dog walks from sun to shade in the source"""
    m = a > .5
    lo, hi = np.percentile(g[m], 3), np.percentile(g[m], 97)
    return np.clip((g - lo) / max(hi - lo, 1e-3) * .74 + .13, 0, 1)


def load():
    """returns {key: dict(img=gray HxW, alpha, canon=(K,2) canon handle coords, src=(K,2))}"""
    masks = json.load(open(os.path.join(KIT, 'masks.json')))
    out = {}
    for k, s in SRC.items():
        im = Image.open(os.path.join(KIT, 'frames/f%03d.jpg' % s['frame'])).convert('L')
        W, H = im.size
        g = np.asarray(im, np.float32) / 255.
        a = raster_alpha(masks[str(s['frame'])], W, H)
        g = tone(g, a)
        # per-piece masks: below the belly line every masked pixel belongs to the nearest leg (distance to
        # that leg's top-knee-foot polyline); above it, to the body. Legs fade in over 8 px above the line
        # and the body keeps those 8 px too, so a swinging leg always has paper under its joint.
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        bx, by = zip(*s['belly'])
        ycut = np.interp(xx[0], bx, by)[None, :]
        dist = {}
        for ln, (tp, kn, ft) in LEGS.items():
            pts = [s['h'][tp], s['h'][kn], s['h'][ft]]
            dm = np.full((H, W), 1e9, np.float32)
            for (ax, ay), (cx, cy) in zip(pts[:-1], pts[1:]):
                vx, vy = cx - ax, cy - ay
                u = np.clip(((xx - ax) * vx + (yy - ay) * vy) / (vx * vx + vy * vy), 0, 1)
                dm = np.minimum(dm, np.hypot(xx - ax - u * vx, yy - ay - u * vy))
            dist[ln] = dm
        D = np.stack([dist[k] for k in LEGS])
        near = np.argmin(D, 0)
        below = np.clip((yy - (ycut - 8)) / 8., 0, 1)
        pieces = {}
        for j, ln in enumerate(LEGS):
            pieces[ln] = a * below * (near == j)
        pieces['body'] = a * (1 - np.clip((yy - ycut) / 4., 0, 1))
        # the head is its own cut-out (rigid), laid over the bending neck: a spinning head would fold
        # the pixels of a single sheet (ledger attempt 3)
        hp = [s['h'][n] for n in ('nose', 'skull', 'throat')]
        hp.append(tuple(np.array(s['h']['skull']) * .55 + np.array(s['h']['throat']) * .45 +
                        (np.array(s['h']['skull']) - np.array(s['h']['nose'])) * .35))
        hm = raster_alpha([[hp[0], hp[1], hp[3], hp[2]]], W, H, erode=False)
        hm = np.clip(ndimage.gaussian_filter(np.clip(ndimage.distance_transform_edt(hm < .5) < s.get('head_pad', 9), 0, 1)
                                             .astype(np.float32), 2.0) * 1.3, 0, 1)
        pieces['head'] = a * hm
        src = np.array([s['h'][n] for n in NAMES], np.float64)
        anc = np.array(s['anchor'], np.float64)
        if s['flip_src']:
            g = g[:, ::-1].copy(); a = a[:, ::-1].copy()
            pieces = {kk: v[:, ::-1].copy() for kk, v in pieces.items()}
            src[:, 0] = W - 1 - src[:, 0]
            anc[0] = W - 1 - anc[0]
        canon = (src - anc) * SCALE_FIX[k]
        out[k] = dict(img=g, alpha=a, pieces=pieces, src=src, canon=canon, frame=s['frame'], W=W, H=H)
    return out


if __name__ == '__main__':
    P = load()
    os.makedirs(os.path.join(HERE, '..', 'proof'), exist_ok=True)
    for k, p in P.items():
        s = 4
        rgb = np.dstack([p['img']] * 3) * (0.35 + 0.65 * p['alpha'][..., None])
        im = Image.fromarray((rgb * 255).astype(np.uint8)).resize((p['W'] * s, p['H'] * s), Image.BICUBIC)
        d = ImageDraw.Draw(im)
        for n, (x, y) in zip(NAMES, p['src']):
            d.ellipse((x * s - 4, y * s - 4, x * s + 4, y * s + 4), outline=(255, 60, 60), width=2)
            d.text((x * s + 5, y * s - 6), n, fill=(80, 255, 80))
        im.save(os.path.join(HERE, '..', 'proof', 'handles_%s.png' % k))
    print('ok')

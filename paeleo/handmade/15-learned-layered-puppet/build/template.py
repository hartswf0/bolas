"""Layer/template constructor: cut f006 of Amateur Film New Jersey C into 11 layers.
Assignment = bone-Voronoi over the SAM mask (each mask pixel goes to the nearest bone, minus the bone's radius),
legs only below the belly line; every child layer also keeps a round joint cap so rotations open no gap.
Each layer's texture is extended beyond its region by nearest-pixel fill (what an occluder hid is unknown:
it is filled, and flagged as unknown in the confidence map)."""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from puppet import SKEL, PARTS, KIT, CACHE, TEMPLATE_FRAME, load_kit

os.makedirs(CACHE, exist_ok=True)
masks, _ = load_kit()
W, H = 384, 288


def poly_mask(polys, W=W, H=H):
    im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
    for p in polys:
        if len(p) >= 3:
            d.polygon([tuple(q) for q in p], fill=255)
    return np.asarray(im) > 127


def seg_dist(px, py, a, b):
    a = np.array(a, float); b = np.array(b, float); d = b - a
    t = np.clip(((px - a[0]) * d[0] + (py - a[1]) * d[1]) / (d @ d + 1e-9), 0, 1)
    return np.hypot(px - (a[0] + t * d[0]), py - (a[1] + t * d[1]))


if __name__ == '__main__':
    f = TEMPLATE_FRAME
    gray = np.asarray(Image.open(os.path.join(KIT, 'frames/f%03d.jpg' % f)).convert('L'), np.float32) / 255
    m = poly_mask(masks[str(f)])
    lab, n = ndimage.label(m)
    sizes = ndimage.sum(m, lab, range(1, n + 1)); m = lab == (1 + int(np.argmax(sizes)))
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    D = []
    belly = 152.0
    for k in PARTS:
        sk = SKEL[k]
        d = seg_dist(xx, yy, *sk['bone']) - sk['r']
        if k.endswith('_up') or k.endswith('_lo'):
            d = np.where(yy < belly - 4, 1e3, d)
        if k == 'head':
            d = np.where(xx > 135, 1e3, d)
        D.append(d)
    D = np.array(D)
    assign = np.argmin(D, 0)
    alpha = np.zeros((len(PARTS), H, W), np.float32); rgb = np.zeros_like(alpha); bbox = []
    soft = ndimage.gaussian_filter(m.astype(np.float32), 0.7)
    for i, k in enumerate(PARTS):
        reg = m & (assign == i)
        sk = SKEL[k]
        if sk['parent'] is not None:
            px, py = sk['pivot']
            cap = np.hypot(xx - px, yy - py) < (sk['r'] + (6 if k.endswith('_lo') else 3))
            reg = reg | (cap & m)
        if k.endswith('_up'):
            # the upper leg also keeps a cap over its knee, so the bent knee never opens a gap
            kx, ky = SKEL[k]['bone'][1]
            reg = reg | ((np.hypot(xx - kx, yy - ky) < sk['r'] + 4) & m)
        # soft edge only on the outside silhouette; seams between layers get a small feather
        a = ndimage.gaussian_filter(reg.astype(np.float32), 0.6)
        a = np.minimum(a * 1.4, 1) * np.clip(soft * 1.6, 0, 1)
        alpha[i] = a
        # texture: frame pixels inside the region, nearest-pixel fill outside
        idx = ndimage.distance_transform_edt(~reg, return_distances=False, return_indices=True)
        rgb[i] = gray[idx[0], idx[1]]
        ys, xs = np.nonzero(a > 0.01)
        bbox.append([xs.min() - 2, ys.min() - 2, xs.max() + 3, ys.max() + 3])
    np.savez_compressed(os.path.join(CACHE, 'template.npz'), alpha=alpha, rgb=rgb, bbox=np.array(bbox), mask=m, gray=gray, assign=assign)
    # proof: coloured layer map
    cols = np.array([[200, 120, 60], [240, 220, 80], [120, 200, 240], [90, 90, 200], [60, 60, 160], [80, 200, 90], [40, 140, 60],
                     [200, 90, 200], [140, 50, 140], [240, 80, 80], [160, 40, 40]], float)
    vis = np.stack([gray * 255] * 3, -1) * 0.5
    for i in range(len(PARTS)):
        vis += (alpha[i] > 0.5)[..., None] * cols[i] * 0.5 / max(1, 1)
    vis = np.clip(vis, 0, 255).astype(np.uint8)
    im = Image.fromarray(vis).crop((60, 60, 280, 220)).resize((660, 480), Image.NEAREST)
    d = ImageDraw.Draw(im)
    for i, k in enumerate(PARTS):
        bx = SKEL[k]['bone']
        d.line([((bx[0][0] - 60) * 3, (bx[0][1] - 60) * 3), ((bx[1][0] - 60) * 3, (bx[1][1] - 60) * 3)], fill=(255, 255, 255), width=2)
        d.text(((SKEL[k]['pivot'][0] - 60) * 3 + 4, (SKEL[k]['pivot'][1] - 60) * 3), k, fill=(255, 255, 255))
    os.makedirs(os.path.join(CACHE, '..', '..', 'proof'), exist_ok=True)
    im.save(os.path.join(CACHE, '..', '..', 'proof', 'template_layers.jpg'), quality=90)
    print('template parts', {k: int((alpha[i] > .5).sum()) for i, k in enumerate(PARTS)})

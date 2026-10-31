"""Proposal generator + object-identity linker + mask adjudicator.

For every frame of every source shot used, it records the SAM proposal (box prompt, model IoU), computes
a confidence proxy of its own and links object IDs across frames:
  stability  = IoU of this mask with its neighbours after camera compensation (a mask that jumps is suspect)
  edge       = share of the mask boundary that lies on a real image edge (gradient above the frame's 70th pct)
  area_ratio = area / running median area (catches leaks into the ground and shadows)
  conf       = sqrt(stability * edge), rejected if conf < 0.42 or area_ratio outside [0.6, 1.6]
Object identity: the mask in frame f keeps the ID of frame f-1 if their compensated IoU >= 0.45; else a new ID.
Our own proposals (person, forearm) are prompted with a box + positive/negative points and grown from colour,
so they reproduce from their prompts."""
import json, os, math
import numpy as np
from common import *

W, H = 384, 288


def set_size(src):
    global W, H
    W, H = src_frame(src, 0).size


def shift(a, dx, dy):
    out = np.zeros_like(a)
    dx, dy = int(round(dx)), int(round(dy))
    ys = slice(max(dy, 0), H + min(dy, 0)); yd = slice(max(-dy, 0), H + min(-dy, 0))
    xs = slice(max(dx, 0), W + min(dx, 0)); xd = slice(max(-dx, 0), W + min(-dx, 0))
    out[ys, xs] = a[yd, xd]
    return out


def iou(a, b):
    a = a > .5; b = b > .5
    u = (a | b).sum()
    return float((a & b).sum() / u) if u else 0.0


def edge_agreement(src, i, alpha):
    g = grad_mag(np.asarray(src_frame(src, i).convert('L')))
    thr = np.percentile(g, 70)
    m = alpha > .5
    inner = m.copy()
    inner[1:, :] &= m[:-1, :]; inner[:-1, :] &= m[1:, :]; inner[:, 1:] &= m[:, :-1]; inner[:, :-1] &= m[:, 1:]
    bnd = m & ~inner
    if bnd.sum() == 0:
        return 0.0
    # allow 1 px tolerance: max gradient in 3x3
    gm = g.copy()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            gm = np.maximum(gm, np.roll(np.roll(g, dy, 0), dx, 1))
    return float((gm[bnd] > thr).mean())


def run_shot(src, frames, cam=None, prefix='dog'):
    set_size(src)
    masks = src_masks(src)
    meta = src_meta(src)
    al = {i: raster(masks.get(str(i), []), (W, H)) for i in frames}
    # camera sign chosen by data
    sign = 1
    if cam is not None:
        def mean_iou(s):
            return np.mean([iou(shift(al[i], s * (cam[i + 1][0] - cam[i][0]), s * (cam[i + 1][1] - cam[i][1])), al[i + 1]) for i in frames[:-1]])
        sign = 1 if mean_iou(1) >= mean_iou(-1) else -1
    def comp(i, j):
        if cam is None:
            return iou(al[i], al[j])
        return iou(shift(al[i], sign * (cam[j][0] - cam[i][0]), sign * (cam[j][1] - cam[i][1])), al[j])
    areas = {i: float(al[i].sum()) for i in frames}
    rows = []
    for k, i in enumerate(frames):
        nb = [comp(i, j) for j in (frames[k - 1] if k else None, frames[k + 1] if k + 1 < len(frames) else None) if j is not None]
        stab = max(nb) if nb else 1.0
        med = float(np.median([areas[j] for j in frames[max(0, k - 4):k + 5]]))
        ar = areas[i] / med if med else 0
        edge = edge_agreement(src, i, al[i])
        conf = math.sqrt(max(stab, 0) * edge)
        ys, xs = np.nonzero(al[i] > .5)
        reasons = []
        if conf < .42: reasons.append('low confidence proxy %.2f' % conf)
        if not (.6 <= ar <= 1.6): reasons.append('area %.2fx running median (leak or loss)' % ar)
        m = meta.get(i, {})
        rows.append(dict(obj=None, src=src, frame=i, prompt=dict(box=m.get('box'), from_=m.get('from')), sam_iou=m.get('iou'),
                         area=int(areas[i]), area_ratio=round(ar, 3), stability=round(stab, 3), edge=round(edge, 3),
                         conf=round(conf, 3), bbox=[int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())] if len(xs) else None,
                         accepted=not reasons, flags=reasons))
    # identity: link each accepted proposal to the last accepted one (rejected proposals carry no identity)
    obj_n = 1; prev = None
    for r in rows:
        if not r['accepted']:
            continue
        if prev is not None:
            r['link_iou'] = round(comp(prev, r['frame']), 3)
            if r['link_iou'] < .45:
                obj_n += 1
        r['obj'] = '%s#%d' % (prefix, obj_n); prev = r['frame']
    return rows, sign


def person_proposal(i, box, pos, neg):
    """Our own proposal of the standing person in Straight Talk frames: box prompt + colour growth.
    Person pixels inside the box are saturated (smock, sleeves) or dark (hair, jeans); the door and wall are pale grey."""
    im = np.asarray(src_frame('door', i).convert('HSV'), dtype=np.float32) / 255.
    s, v = im[..., 1], im[..., 2]
    cand = (s > .16) | (v < .38)
    m = np.zeros((H, W), bool); x0, y0, x1, y1 = box
    m[y0:y1, x0:x1] = cand[y0:y1, x0:x1]
    for (x, y, r) in neg:
        yy, xx = np.ogrid[:H, :W]; m[(xx - x) ** 2 + (yy - y) ** 2 <= r * r] = False
    m = largest_component(m)
    m = fill_holes(m)
    ok = all(m[y, x] for x, y, _ in pos)
    return m, ok


def main():
    out = {}
    cam = json.load(open(os.path.join(SOURCES['dog']['dir'], 'camera.json')))
    rows, sign = run_shot('dog', list(range(50)), cam, 'dog')
    out['dog'] = dict(camera_sign=sign, rows=rows)
    for src, n, pre in (('door', 32, 'door'), ('hand', 62, 'hand'), ('sitter', 50, 'sitter')):
        nn = len(os.listdir(os.path.join(SOURCES[src]['dir'], 'frames')))
        rows, _ = run_shot(src, list(range(nn)), None, pre)
        out[src] = dict(rows=rows)
    # own person proposals in Straight Talk frames 0..6 (person seen from behind, used only as a backlit silhouette)
    pp = []
    set_size('door')
    for i in range(0, 7):
        box = (185, 10, 330, 288); pos = [(260, 150, 0), (255, 40, 0)]; neg = [(150, 150, 30), (360, 150, 20)]
        m, ok = person_proposal(i, box, pos, neg)
        Image.fromarray((m * 255).astype(np.uint8)).save(os.path.join(CACHE, 'person_f%03d.png' % i))
        pp.append(dict(obj='person#1', src='door', frame=i, prompt=dict(box=box, pos=[p[:2] for p in pos], neg=[p[:2] for p in neg],
                       rule='inside box: HSV saturation > 0.16 or value < 0.38; largest 4-component; holes filled'),
                       area=int(m.sum()), accepted=bool(ok), flags=[] if ok else ['positive point not covered']))
    out['person'] = dict(rows=pp)
    jdump(out, os.path.join(CACHE, 'proposals.json'))
    acc = [r['frame'] for r in out['dog']['rows'] if r['accepted']]
    rej = [(r['frame'], r['flags']) for r in out['dog']['rows'] if not r['accepted']]
    print('dog camera sign', sign, 'accepted', len(acc), 'rejected', rej)
    print('dog ids', sorted(set(str(r['obj']) for r in out['dog']['rows'])))
    for r in out['dog']['rows']:
        print(r['frame'], r['obj'], r['sam_iou'], r['stability'], r['edge'], r['conf'], r['area_ratio'], r['accepted'])
    for k in ('door', 'hand', 'sitter', 'person'):
        rr = out[k]['rows']; print(k, len(rr), 'accepted', sum(r['accepted'] for r in rr), sorted(set(str(r['obj']) for r in rr)))


if __name__ == '__main__':
    main()

"""Boundary cost designer: split one extracted dog into animation layers (head, torso, forelegs, hindlegs, tail)
with the same graph cut, now inside the dog's own alpha. Seeds are scribbles placed from the kit's rig keys; the
pairwise cost is uniform inside the body (weakened at image edges), so each min cut is the shortest separation between
seed sets: across the neck, across the tail root, across the top of each leg pair. The occluded region a piece leaves
behind is filled from the torso by a short inpaint (recorded as a repair, never as source pixels).

python3 pieces.py <frame> [<frame> ...]  -> build/cache/pieces/fNNN.npz  (label map + pivots, source coordinates)
"""
import os, sys, json
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from graphcut import maxflow_grid, dilate, erode, box_blur

HERE = os.path.dirname(os.path.abspath(__file__))
C = os.path.join(HERE, 'cache')
KIT = os.path.abspath(os.path.join(HERE, '../../kit/archive-dog'))
LABELS = ['torso', 'head', 'tail', 'fore', 'hind']


def seg_mask(H, W, a, b, width):
    im = Image.new('L', (W, H), 0); ImageDraw.Draw(im).line([tuple(a), tuple(b)], fill=255, width=int(width))
    return np.array(im) > 127


def disk(H, W, c, r):
    yy, xx = np.mgrid[:H, :W]
    return (xx - c[0]) ** 2 + (yy - c[1]) ** 2 <= r * r


def cut_inside(body, fgseed, bgseed, grey, w_in=30):
    """min cut separating fgseed from bgseed inside body. returns fg side (within body)."""
    H, W = body.shape
    g = box_blur(grey, 1)
    wr = np.zeros((H, W)); wd = np.zeros((H, W))
    dr = np.abs(np.diff(g, axis=1)); dd = np.abs(np.diff(g, axis=0))
    wr[:, :-1] = w_in * np.exp(-dr / 25.0) * (body[:, :-1] & body[:, 1:])
    wd[:-1, :] = w_in * np.exp(-dd / 25.0) * (body[:-1, :] & body[1:, :])
    src = np.zeros((H, W), np.int64); snk = np.zeros((H, W), np.int64)
    src[fgseed & body] = 10 ** 6; snk[bgseed & body] = 10 ** 6
    seg, _ = maxflow_grid(src, snk, np.round(wr).astype(np.int64), np.round(wd).astype(np.int64))
    return seg & body


def run(i, override=None):
    z = np.load(os.path.join(C, 'dog', 'f%03d.npz' % i))
    a = z['alpha'].astype(np.float32); rgb = z['rgb']; x0, y0 = z['origin']
    body = a > 0.5
    H, W = body.shape
    grey = rgb.mean(2).astype(np.float32)
    pose = json.load(open(os.path.join(KIT, 'pose_agent_v8.json')))
    from extract import interp_pose
    k = pose.get(str(i)) or interp_pose(pose, i)
    P = {n: np.array([k[n][0] - x0, k[n][1] - y0], float) for n in k if not n.startswith('_')}
    if override:
        for n, v in override.items():
            P[n] = np.array(v, float)
    lab = np.zeros((H, W), np.int8)  # 0 torso
    yy, xx = np.mgrid[:H, :W]
    nose, neck, chest, tail = P['nose'], P['neck'], P['chest'], P['tail']
    fore = (P['f1'] + P['f2']) / 2; hind = (P['h1'] + P['h2']) / 2
    back_y = min(neck[1], tail[1])
    # head: beyond the neck from the chest
    dn = np.linalg.norm(nose - neck)
    head_seed = disk(H, W, nose, max(4, .45 * dn)) | seg_mask(H, W, nose, nose + (nose - neck) * 0.6, 7)
    rest_seed = disk(H, W, chest, 8) | seg_mask(H, W, chest, tail, 9) | disk(H, W, fore, 6) | disk(H, W, hind, 6)
    rest_seed |= disk(H, W, neck + (chest - neck) * 0.6, 6)
    head = cut_inside(body, head_seed, rest_seed & ~head_seed, grey)
    lab[head] = 1
    rem = body & ~head
    # tail: beyond the tail key, away from the chest
    dirt = (tail - chest) / (np.linalg.norm(tail - chest) + 1e-6)
    proj = (xx - tail[0]) * dirt[0] + (yy - tail[1]) * dirt[1]
    tail_seed = rem & (proj > 18)
    tseed_rest = rem & (proj < -4)
    if tail_seed.sum() > 10:
        tl = cut_inside(rem, tail_seed, tseed_rest, grey)
        lab[tl] = 2; rem &= ~tl
    # legs: seeds from each foot up to 45 % of the way to the back line; torso seed along the back
    belly_y = back_y + 0.5 * ((fore[1] + hind[1]) / 2 - back_y)
    torso_seed = rem & (yy < back_y + 0.32 * ((fore[1] + hind[1]) / 2 - back_y))
    torso_seed |= seg_mask(H, W, neck + (chest - neck) * .3, tail - dirt * 6, 8) & rem
    for name, feet, val in (('fore', (P['f1'], P['f2']), 3), ('hind', (P['h1'], P['h2']), 4)):
        s = np.zeros((H, W), bool)
        for f in feet:
            s |= seg_mask(H, W, f, f + (np.array([f[0], belly_y]) - f) * 0.55, 6) | disk(H, W, f, 5)
        s &= rem
        other = np.zeros((H, W), bool)
        for f in ((P['h1'], P['h2']) if name == 'fore' else (P['f1'], P['f2'])):
            other |= disk(H, W, f, 6) | seg_mask(H, W, f, f + (np.array([f[0], belly_y]) - f) * 0.55, 6)
        lg = cut_inside(rem, s, (torso_seed | other) & ~s, grey)
        lab[lg] = val; rem &= ~lg
    lab[~body] = -1
    piv = {'neck': (neck + (chest - neck) * .15).tolist(), 'tail': tail.tolist(),
           'shoulder': [float(fore[0] + (neck[0] - fore[0]) * .15), float(belly_y - 4)],
           'hip': [float(hind[0]), float(belly_y - 8)], 'nose': nose.tolist(), 'fore_foot': fore.tolist(), 'hind_foot': hind.tolist(),
           'chest': chest.tolist(), 'belly_y': float(belly_y)}
    os.makedirs(os.path.join(C, 'pieces'), exist_ok=True)
    np.savez_compressed(os.path.join(C, 'pieces', 'f%03d.npz' % i), lab=lab, alpha=a, rgb=rgb, origin=z['origin'],
                        piv=json.dumps(piv))
    counts = {LABELS[v]: int((lab == v).sum()) for v in range(5)}
    print(i, counts)
    return lab, piv


def sheet(frames, out):
    cols = [(150, 150, 150), (255, 120, 60), (60, 200, 255), (120, 255, 90), (255, 230, 60)]
    ims = []
    for i in frames:
        z = np.load(os.path.join(C, 'pieces', 'f%03d.npz' % i))
        lab = z['lab']; rgb = z['rgb'].astype(np.float32)
        v = rgb * .5
        for k, c in enumerate(cols):
            v[lab == k] = rgb[lab == k] * .5 + np.array(c) * .5
        piv = json.loads(str(z['piv']))
        im = Image.fromarray(v.clip(0, 255).astype(np.uint8)); im = im.resize((im.width * 3, im.height * 3), Image.NEAREST)
        d = ImageDraw.Draw(im)
        for n, p in piv.items():
            if isinstance(p, list):
                d.ellipse([p[0] * 3 - 4, p[1] * 3 - 4, p[0] * 3 + 4, p[1] * 3 + 4], outline=(255, 0, 255)); d.text((p[0] * 3 + 5, p[1] * 3), n, fill=(255, 0, 255))
        ims.append(im)
    W = sum(im.width for im in ims); H = max(im.height for im in ims)
    s = Image.new('RGB', (W, H)); x = 0
    for im in ims:
        s.paste(im, (x, 0)); x += im.width
    s.save(out)


if __name__ == '__main__':
    fr = [int(a) for a in sys.argv[1:]]
    for i in fr:
        run(i)
    sheet(fr, os.path.join(C, 'pieces', 'sheet.jpg'))

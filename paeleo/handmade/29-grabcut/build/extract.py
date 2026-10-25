"""Segmentation operator + edge/matte specialist: cut every source frame we use out of its archive shot.

python3 extract.py dog|door|hand|all
For each frame: box (SAM bbox + margin) -> seeds (SAM eroded = hard fg, SAM dilated complement = hard bg, rig-key
scribbles = hard fg) -> GrabCut iterations (unary colour/texture models re-estimated, pairwise contrast edges, BK
graph cut) -> alpha cleanup.  The SAM mask is one input among our own: it seeds and softly biases the cut, it does not
decide it.  Writes build/cache/<shot>/fNNN.npz (alpha, rgb crop, origin, fg, sam, margin) and a JSON log.
"""
import sys, os, json, time
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from graphcut import grabcut, cleanup, poly_mask, dilate, erode, contour

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '../../../..'))
CACHE = os.path.join(HERE, 'cache')

SHOTS = {
    'dog': dict(dir=os.path.join(ROOT, 'paeleo/handmade/kit/archive-dog'), frames=list(range(50)), margin=22,
                er=5, di=8, prior_w=0.4, pose='pose_agent_v8.json'),
    'door': dict(dir=os.path.join(ROOT, 'paeleo/handmade/kit/archive-door'), frames=[20, 22, 24, 26, 28, 29, 30, 31] + [4, 8],
                 margin=12, er=6, di=10),
    'hand': dict(dir='/home/user/hartswf0/secondhand-motion/shots/hand-sam', frames=[0, 10, 20], margin=40, er=4, di=8),
}


def disk(H, W, cx, cy, r):
    yy, xx = np.mgrid[:H, :W]
    return (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r


RUMP_BG = {   # crop coords (f9 origin 55,57; f10/f11 origin 55,58)
    9: [(122, 55), (136, 58), (147, 63), (155, 73), (159, 86), (161, 97)],
    10: [(122, 54), (136, 56), (146, 61), (152, 69), (155, 80), (156, 93)],
    11: [(112, 46), (128, 48), (140, 53), (149, 62), (153, 74), (155, 86)],
}


def extra_seeds(shot, i, img, sam, x0, y0, seed):
    """shot-specific scribbles (manual contour markup, recorded here so it is versioned)."""
    H, W = seed.shape
    if shot == 'dog' and i in RUMP_BG:
        # round 2 (critic: boxy SAM hindquarter on the watching drawings): manual contour markup, a bg scribble just
        # outside the rounded rump, in crop coordinates of that frame; the cut finds the edge inside it
        from PIL import ImageDraw
        im = Image.new('L', (W, H), 0)
        ImageDraw.Draw(im).line(RUMP_BG[i], fill=255, width=6)
        seed[np.array(im) > 127] = 2
    if shot == 'hand':
        # the forearm continues off the right edge: scribble it fg; the card is the adjacent object: scribble it bg
        grey = img.mean(2)
        ys, xs = np.nonzero(sam)
        top, bot = ys.min(), ys.max()
        # forearm: bright band to the right of the SAM hand (the SAM mask stops at the wrist)
        arm = np.zeros_like(sam)
        xr = xs.max()
        band = grey > 120
        arm[:, xr - 2:] = band[:, xr - 2:]
        arm &= ~dilate(np.zeros_like(sam), 0)
        rows = np.arange(H)[:, None]
        arm &= (rows > top - 14) & (rows < bot + 4)
        seed[erode(arm, 2)] = 1
        # card: mid-grey, low-texture region below/left of the hand, away from the fingers
        card = (grey > 70) & (grey < 125) & ~dilate(sam | arm, 6)
        seed[erode(card, 3)] = 2
    return seed


def interp_pose(pose, i):
    ks = sorted(int(k) for k in pose)
    lo = max([k for k in ks if k <= i], default=None); hi = min([k for k in ks if k >= i], default=None)
    if lo is None or hi is None:
        return None
    if lo == hi:
        return pose[str(lo)]
    u = (i - lo) / (hi - lo); a, b = pose[str(lo)], pose[str(hi)]
    return {n: [a[n][0] * (1 - u) + b[n][0] * u, a[n][1] * (1 - u) + b[n][1] * u] for n in a if not n.startswith('_')}


def tri_mask(H, W, pts):
    from PIL import ImageDraw
    im = Image.new('L', (W, H), 0); ImageDraw.Draw(im).polygon([tuple(p) for p in pts], fill=255)
    return np.array(im) > 127


def dog_scribbles(k, sam, x0, y0, seed):
    """seed constraints learned from failures (ledger #2): (a) the gap under the belly between fore and hind feet is
    background (shadowed ground there matches the dog's tones and the smoothness term bridged it); (b) thin SAM
    protrusions near the tail key are the tail and are kept (graph cuts shrink thin structures)."""
    H, W = seed.shape
    P = {n: (k[n][0] - x0, k[n][1] - y0) for n in k if not n.startswith('_')}
    fx = (P['f1'][0] + P['f2'][0]) / 2; hx = (P['h1'][0] + P['h2'][0]) / 2
    if abs(hx - fx) > 25:   # side-ish view only
        top = (P['chest'][1] + P['tail'][1]) / 2
        footy = (P['f1'][1] + P['f2'][1] + P['h1'][1] + P['h2'][1]) / 4
        belly = top + 0.55 * (footy - top)
        inner_f = max(P['f1'][0], P['f2'][0]) if fx < hx else min(P['f1'][0], P['f2'][0])
        inner_h = min(P['h1'][0], P['h2'][0]) if fx < hx else max(P['h1'][0], P['h2'][0])
        sgn = 1 if fx < hx else -1
        A = (inner_f + sgn * 7, footy - 2); B = (inner_h - sgn * 7, footy - 2); C = ((inner_f + inner_h) / 2, belly + 6)
        cx, cy = (A[0] + B[0] + C[0]) / 3, (A[1] + B[1] + C[1]) / 3
        pts = [(cx + .9 * (p[0] - cx), cy + .9 * (p[1] - cy)) for p in (A, B, C)]
        if abs(B[0] - A[0]) > 14:
            seed[tri_mask(H, W, pts) & ~sam] = 2
    opened = dilate(erode(sam, 3), 3)
    thin = sam & ~opened
    yy, xx = np.mgrid[:H, :W]
    tx, ty = P['tail']; chx, chy = P['chest']
    dt = np.hypot(tx - chx, ty - chy)
    zone = (np.hypot(xx - tx, yy - ty) < 55) & (np.hypot(xx - chx, yy - chy) > dt - 4)
    seed[thin & zone] = 1
    return seed


def run(shot, frames=None):
    cfg = SHOTS[shot]
    masks = json.load(open(os.path.join(cfg['dir'], 'masks.json')))
    pose = json.load(open(os.path.join(cfg['dir'], cfg['pose']))) if cfg.get('pose') else {}
    out = os.path.join(CACHE, shot); os.makedirs(out, exist_ok=True)
    log = {}
    for i in (frames or cfg['frames']):
        t0 = time.time()
        full = np.array(Image.open(os.path.join(cfg['dir'], 'frames/f%03d.jpg' % i)).convert('RGB'))
        Hf, Wf = full.shape[:2]
        sam_full = poly_mask(masks.get(str(i), []), Hf, Wf)
        if shot == 'hand':
            # extend the box rightwards so the forearm (outside the SAM mask) can be cut too
            ys, xs = np.nonzero(sam_full)
            x0, x1 = max(0, xs.min() - cfg['margin']), Wf
        else:
            ys, xs = np.nonzero(sam_full)
            x0, x1 = max(0, xs.min() - cfg['margin']), min(Wf, xs.max() + cfg['margin'])
        y0, y1 = max(0, ys.min() - cfg['margin']), min(Hf, ys.max() + cfg['margin'])
        img = full[y0:y1, x0:x1]; sam = sam_full[y0:y1, x0:x1]
        H, W = sam.shape
        seed = np.zeros((H, W), np.int8)
        seed[erode(sam, cfg['er'])] = 1
        seed[~dilate(sam, cfg['di'])] = 2
        seed[0, :] = 2; seed[-1, :] = 2; seed[:, 0] = 2
        if shot != 'hand':
            seed[:, -1] = 2
        # rig-key scribbles (fg): small disks on the keyed nose / chest / tail / feet
        k = pose.get(str(i)) or interp_pose(pose, i)
        if k:
            for name in ('nose', 'neck', 'chest', 'tail'):
                cx, cy = k[name][0] - x0, k[name][1] - y0
                m = disk(H, W, cx, cy, 2) & sam
                seed[m] = 1
        if k and shot == 'dog':
            seed = dog_scribbles(k, sam, x0, y0, seed)
        seed = extra_seeds(shot, i, img, sam, x0, y0, seed)
        up = cfg.get('up', 2)
        if up > 1:   # source resolution: cut at 2x so thin parts (tail, leg tips, fingers) beat the shrinking bias
            img_u = np.array(Image.fromarray(img).resize((W * up, H * up), Image.BICUBIC))
            sam_u = np.array(Image.fromarray(sam.astype(np.uint8) * 255).resize((W * up, H * up), Image.BILINEAR)) > 127
            seed_u = np.array(Image.fromarray(seed).resize((W * up, H * up), Image.NEAREST))
        else:
            img_u, sam_u, seed_u = img, sam, seed
        extra = None; nbx = 1
        if shot == 'dog':
            from plate import plate_for
            from graphcut import box_blur
            pl, cnt = plate_for(i)
            d = np.abs(box_blur(full.mean(2), 1) - box_blur(pl, 1))[y0:y1, x0:x1]
            d[cnt[y0:y1, x0:x1] < 3] = 12          # plate unseen there: neutral evidence
            dq = np.digitize(d, [7, 15, 28, 45]).astype(np.int64)
            extra = np.array(Image.fromarray(dq.astype(np.uint8)).resize((W * up, H * up), Image.NEAREST)).astype(np.int64); nbx = 5
        res = grabcut(img_u, sam_u, seed_u, iters=4, prior_w=cfg.get('prior_w', 0.25) / up, extra=extra, extra_bins=nbx)
        fg_u = res['fg']
        alpha_u, cl = cleanup(fg_u, res['sm'], keep_near=0)
        # back to source resolution: alpha by area averaging (the 2x cut is supersampled coverage)
        alpha = alpha_u.reshape(H, up, W, up).mean((1, 3)) if up > 1 else alpha_u
        fg = alpha > .5
        res['margin'] = res['margin'].reshape(H, up, W, up).mean((1, 3)) if up > 1 else res['margin']
        np.savez_compressed(os.path.join(out, 'f%03d.npz' % i), alpha=alpha.astype(np.float16), rgb=img, origin=np.array([x0, y0]),
                            fg=fg, sam=sam, seed=seed, margin=res['margin'].astype(np.float16))
        disagree = int((fg != sam).sum())
        log[i] = {'box': [int(x0), int(y0), int(x1), int(y1)], 'iters': res['log'], 'cleanup': cl,
                  'sam_px': int(sam.sum()), 'cut_px': int(fg.sum()), 'disagree_with_sam_px': disagree,
                  'secs': round(time.time() - t0, 2)}
        print(shot, i, log[i]['secs'], 's', 'cut', log[i]['cut_px'], 'sam', log[i]['sam_px'], 'dis', disagree, cl, flush=True)
    path = os.path.join(out, 'log.json')
    old = json.load(open(path)) if os.path.exists(path) else {}
    old.update({str(k): v for k, v in log.items()})
    json.dump(old, open(path, 'w'), indent=1)


if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else 'all'
    fr = [int(x) for x in sys.argv[2].split(',')] if len(sys.argv) > 2 else None
    for s in (SHOTS if which == 'all' else [which]):
        run(s, fr)

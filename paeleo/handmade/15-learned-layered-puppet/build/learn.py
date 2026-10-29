"""Learn the generative layered puppet from the 50 fitted archive frames.

  view latent      psi in [0, 90] per frame (0 = profile, 90 = facing camera), from the fitted torso foreshortening
                   under an ellipse prior (body width/length W_BODY), head view psi_h from the head layer the same way.
                   Facing right is the same view mirrored (mirror symmetry of the dog is an assumption, stated).
  shape model      Nadaraya-Watson regression of the remaining shape parameters on psi (head fy, tail length,
                   leg lengths, head tilt) - what the head and legs look like from each view.
  appearance model per layer, per view bin: back-project every good frame into template space through its fitted
                   transform, weight by visibility (SAM mask x not occluded by layers above in that frame) and by view
                   kernel, shrink toward the f006 texture where support is low. Support -> per-texel confidence.
  articulation     Gaussian prior over the fitted joint rotations; Mahalanobis distance of any generated pose is its
                   out-of-distribution score.
  evaluation       leave-out (+-2 frames) reconstruction of every good frame with its held-out appearance atlas,
                   against (a) the single-drawing rig (f006 texture only) and (b) a drawing swap (nearest-view other
                   frame, cut out and box-aligned).
Outputs cache/model.npz, cache/model.json, proof/learned_atlas.jpg, proof/eval.json."""
import json, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from puppet import Template, PARTS, ORDER, transforms, render, KIT, CACHE
from fit import unpack, frame_mask, FREE

W_BODY, W_HEAD = 0.38, 0.55
BINS = np.arange(0, 91, 15.0)
SIG = 13.0
LAMBDA = 0.35
tpl = Template()
F = json.load(open(os.path.join(CACHE, 'fits.json')))
N = 50
poses = [unpack(np.array(F['frames'][str(i)]['x']), F['frames'][str(i)]['mirror']) for i in range(N)]
grays = [np.asarray(Image.open(os.path.join(KIT, 'frames/f%03d.jpg' % i)).convert('L'), np.float32) / 255 for i in range(N)]
masks = [ndimage.gaussian_filter(frame_mask(i).astype(np.float32), 0.8) for i in range(N)]


def view_of(r, w):
    r = abs(r)
    c = np.sqrt(np.clip((r * r - w * w) / (1 - w * w), 0, 1))
    return float(np.degrees(np.arccos(c)))


def fx_of(psi, w):
    c = np.cos(np.radians(psi))
    return float(np.sqrt(c * c + w * w * (1 - c * c)))


psi = np.array([view_of(p['torso']['fx'], W_BODY) for p in poses])
psi_h = np.array([view_of(p['head']['fx'], W_HEAD) for p in poses])
# frames 19-25: the SAM mask swallows the dog's shadow and the gravel (seen on proof/fits_sheet.jpg) -> excluded by eye
EXCLUDED_BY_EYE = set(range(19, 26))
quality = np.array([0.0 if (F['frames'][str(i)]['mask_suspect'] or i in EXCLUDED_BY_EYE) else float(np.clip((F['frames'][str(i)]['iou'] - 0.6) / 0.25, 0, 1)) for i in range(N)])


def backproject(i, k):
    """frame i's pixels seen through layer k, in template space, with visibility."""
    pose = poses[i]; M = transforms(pose)
    j = PARTS.index(k); x0, y0, x1, y1 = tpl.bbox[j]
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(float)
    P = M[k]
    X = P[0, 0] * xx + P[0, 1] * yy + P[0, 2]; Y = P[1, 0] * xx + P[1, 1] * yy + P[1, 2]
    g = ndimage.map_coordinates(grays[i], [Y, X], order=1, mode='nearest')
    m = ndimage.map_coordinates(masks[i], [Y, X], order=1, mode='constant')
    # occlusion by the layers drawn above k in this frame
    above = ORDER[ORDER.index(k) + 1:]
    occ = np.zeros_like(g)
    for l in above:
        _, a = render(tpl, pose, 288, 384, order=[l], alpha_only=True)
        occ = occ + ndimage.map_coordinates(a, [Y, X], order=1, mode='constant') * (1 - occ)
    vis = tpl.alpha[j, y0:y1, x0:x1] * m * (1 - occ)
    return g, vis


def build_atlas(exclude=(), view=None, cache={}):
    view = psi if view is None else view
    tex = np.zeros((len(PARTS), len(BINS)) + tpl.alpha.shape[1:], np.float32)
    conf = np.zeros_like(tex)
    for j, k in enumerate(PARTS):
        x0, y0, x1, y1 = tpl.bbox[j]
        v = psi_h if k == 'head' else view
        for b, pb in enumerate(BINS):
            num = LAMBDA * tpl.rgb[j, y0:y1, x0:x1].copy(); den = np.full(num.shape, LAMBDA, np.float32)
            for i in range(N):
                if i in exclude or quality[i] <= 0:
                    continue
                w = np.exp(-0.5 * ((pb - v[i]) / SIG) ** 2) * quality[i]
                if w < 0.02:
                    continue
                key = (i, k)
                if key not in cache:
                    cache[key] = backproject(i, k)
                g, vis = cache[key]
                ww = (w ** 4) * vis   # sharpened: the nearest good views dominate (less mush)
                num += ww * g; den += ww
            tex[j, b] = tpl.rgb[j]; tex[j, b, y0:y1, x0:x1] = num / den
            conf[j, b, y0:y1, x0:x1] = 1 - LAMBDA / den
    return tex, conf


def kreg(xq, xs, ys, ws, sig=SIG):
    w = np.exp(-0.5 * ((xq - xs) / sig) ** 2) * ws
    return float((w * ys).sum() / max(w.sum(), 1e-6))


def shape_model():
    names = {'head_fy': lambda p: p['head']['fy'], 'head_rot': lambda p: p['head']['rot'], 'tail_fx': lambda p: p['tail']['fx'],
             'fore_len': lambda p: 0.5 * (p['ff_up']['fy'] + p['fn_up']['fy']), 'hind_len': lambda p: 0.5 * (p['hf_up']['fy'] + p['hn_up']['fy'])}
    out = {}
    for n, fn in names.items():
        ys = np.array([fn(p) for p in poses])
        xs = psi_h if n.startswith('head') else psi
        out[n] = [kreg(b, xs, ys, quality) for b in BINS]
    return out


def rots(p):
    return np.array([p[k]['rot'] for k in ['head', 'tail', 'ff_up', 'ff_lo', 'fn_up', 'fn_lo', 'hf_up', 'hf_lo', 'hn_up', 'hn_lo']])


def sample_atlas(tex, view_deg, j):
    b = np.clip(view_deg / 15.0, 0, len(BINS) - 1 - 1e-6)
    b0 = int(b); t = b - b0
    return tex[j, b0] * (1 - t) + tex[j, b0 + 1] * t


def eval_frame(i, tex):
    pose = poses[i]
    textures = {k: (sample_atlas(tex, psi_h[i] if k == 'head' else psi[i], j), tpl.alpha[j]) for j, k in enumerate(PARTS)}
    g, A = render(tpl, pose, 288, 384, textures=textures)
    gb, _ = render(tpl, pose, 288, 384)
    m = (A > 0.5) & (masks[i] > 0.5)
    return float(np.abs(g - grays[i])[m].mean()), float(np.abs(gb - grays[i])[m].mean())


def swap_baseline(i):
    """drawing swap: nearest-view other frame (|j-i|>2), its masked cut-out box-aligned onto frame i's mask."""
    cands = [j for j in range(N) if abs(j - i) > 2 and quality[j] > 0]
    j = min(cands, key=lambda j: abs(psi[j] - psi[i]) + (0 if poses[j]['g']['mirror'] == poses[i]['g']['mirror'] else 200))
    mi = masks[i] > .5; mj = masks[j] > .5
    yi, xi = np.nonzero(mi); yj, xj = np.nonzero(mj)
    sx = (xi.max() - xi.min() + 1) / (xj.max() - xj.min() + 1); sy = (yi.max() - yi.min() + 1) / (yj.max() - yj.min() + 1)
    yy, xx = np.mgrid[0:288, 0:384].astype(float)
    X = (xx - xi.min()) / sx + xj.min(); Y = (yy - yi.min()) / sy + yj.min()
    mw = ndimage.map_coordinates(mj.astype(np.float32), [Y, X], order=1) > .5
    gw = ndimage.map_coordinates(grays[j], [Y, X], order=1)
    iou = (mw & mi).sum() / max((mw | mi).sum(), 1)
    m = mw & mi
    return float(iou), float(np.abs(gw - grays[i])[m].mean()) if m.any() else None, j


if __name__ == '__main__':
    tex, conf = build_atlas()
    sm = shape_model()
    R = np.array([rots(p) for p, q in zip(poses, quality) if q > 0])
    mu = R.mean(0); cov = np.cov(R.T) + np.eye(R.shape[1]) * 0.01
    # PCA of the fitted pose vectors (minus image placement) - what the archive varies along
    X = np.array([[F['frames'][str(i)]['x'][j] for j in range(3, len(FREE))] for i in range(N) if quality[i] > 0])
    Xc = X - X.mean(0); sd = Xc.std(0) + 1e-6
    U, S, Vt = np.linalg.svd(Xc / sd, full_matrices=False)
    var = (S ** 2) / (S ** 2).sum()
    pcs = [{'var': round(float(var[c]), 3), 'top': [[FREE[3 + j][0] + '.' + FREE[3 + j][1], round(float(Vt[c, j]), 2)] for j in np.argsort(-np.abs(Vt[c]))[:4]]} for c in range(4)]
    corr_view = float(np.corrcoef(U[:, 0] * S[0], psi[quality > 0])[0, 1])
    np.savez_compressed(os.path.join(CACHE, 'model.npz'), tex=tex, conf=conf, mu=mu, cov=cov)
    # evaluation
    ev = []
    for i in range(N):
        if quality[i] <= 0:
            continue
        tl, _ = build_atlas(exclude=set(range(i - 2, i + 3)))
        mae_l, mae_t = eval_frame(i, tl)
        iou_s, mae_s, j = swap_baseline(i)
        ev.append({'frame': i, 'psi': round(float(psi[i]), 1), 'fit_iou': F['frames'][str(i)]['iou'], 'mae_learned_heldout': round(mae_l, 4),
                   'mae_single_drawing_rig': round(mae_t, 4), 'swap_from': j, 'swap_iou': round(iou_s, 3), 'mae_swap': None if mae_s is None else round(mae_s, 4)})
        print(ev[-1], flush=True)
    summ = {k: round(float(np.mean([e[k] for e in ev if e[k] is not None])), 4) for k in ['fit_iou', 'mae_learned_heldout', 'mae_single_drawing_rig', 'swap_iou', 'mae_swap']}
    by = {}
    for name, lo, hi in [('profile psi<25', 0, 25), ('turning 25-60', 25, 60), ('front psi>60', 60, 91)]:
        es = [e for e in ev if lo <= e['psi'] < hi]
        if es:
            by[name] = {'n': len(es), **{k: round(float(np.mean([e[k] for e in es if e[k] is not None])), 4) for k in ['fit_iou', 'mae_learned_heldout', 'mae_single_drawing_rig', 'swap_iou', 'mae_swap']}}
    model = {'W_BODY': W_BODY, 'W_HEAD': W_HEAD, 'bins': BINS.tolist(), 'psi': psi.round(1).tolist(), 'psi_h': psi_h.round(1).tolist(),
             'quality': quality.round(2).tolist(), 'shape': sm, 'rot_mu': mu.tolist(), 'pca': pcs, 'pc1_vs_view_corr': round(corr_view, 3),
             'n_train': int((quality > 0).sum()), 'eval_summary': summ, 'eval_by_view': by}
    json.dump(model, open(os.path.join(CACHE, 'model.json'), 'w'), indent=1)
    json.dump({'summary': summ, 'by_view': by, 'frames': ev}, open(os.path.join(CACHE, '..', '..', 'proof', 'eval.json'), 'w'), indent=1)
    # proof: atlas per layer per view bin, with confidence
    rows = []
    for j, k in enumerate(PARTS):
        x0, y0, x1, y1 = tpl.bbox[j]
        row = []
        for b in range(len(BINS)):
            t = tex[j, b, y0:y1, x0:x1]; c = conf[j, b, y0:y1, x0:x1]; a = tpl.alpha[j, y0:y1, x0:x1]
            rgb = np.stack([t * a + (1 - a) * 0.15, t * a + (1 - a) * 0.15, (t * c + (1 - c) * 0.9) * a + (1 - a) * 0.15], -1)
            row.append(Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).resize((x1 - x0) * 2 and ((x1 - x0) * 2, (y1 - y0) * 2)))
        rows.append(row)
    Wd = max(sum(r.width for r in row) + 8 * len(row) for row in rows); Hd = sum(max(r.height for r in row) + 8 for row in rows)
    sheet = Image.new('RGB', (Wd, Hd), (20, 20, 24)); y = 0
    for row in rows:
        x = 0
        for r in row:
            sheet.paste(r, (x, y)); x += r.width + 8
        y += max(r.height for r in row) + 8
    sheet.save(os.path.join(CACHE, '..', '..', 'proof', 'learned_atlas.jpg'), quality=85)
    print(json.dumps({'summary': summ, 'by_view': by, 'pca': pcs, 'pc1_vs_view': corr_view}, indent=1))

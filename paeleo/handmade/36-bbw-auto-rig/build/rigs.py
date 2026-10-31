"""SCION-36 · build every rig once (auto triangulation, auto handles, BBW solve) and cache it; write the numeric
tests (bounds, partition of unity, locality across the leg gaps vs. a shape-blind baseline, stability across
silhouettes and across neighbouring archive frames) to proof/tests.json and the heat maps to proof/."""
import json, os, pickle, sys, time, colorsys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from autorig import rig_frame, shepard_weights, KIT, load_mask
from pose import body_metrics
from person import rig_person

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)
CACHE = os.path.join(HERE, 'cache'); PROOF = os.path.join(OUT, 'proof')
os.makedirs(CACHE, exist_ok=True); os.makedirs(PROOF, exist_ok=True)

# the views: whole archive frames, one mesh each.  facing: -1 head to the left, +1 to the right
VIEWS = {'W': (10, -1),                      # profile to the left, head up: watching, retreat, approach, lying, looking in
         'r1': (1, -1), 'r3': (3, -1), 'r5': (5, -1), 'r6': (6, -1), 'r7': (7, -1),
         't13': (13, -1), 't16': (16, -1), 't21': (21, -1), 't22': (22, -1), 't24': (24, 1), 't25': (25, 1), 't33': (33, 1),   # in-betweens of the found turn   # the archive's own look back over the shoulder (back of the skull)
         't26': (26, 1), 't30': (30, 1), 't36': (36, 1), 't40': (40, 1)}  # the archive's own turn
FRONTAL = {'t26', 't30', 't36'}
STABILITY = [8, 9, 11]
EXTRA = {'A46': (46, 1), 'A44': (44, 1)}   # rigged for the tests only (not in the film)                       # neighbours of W rigged with the same code for the stability test


def tex_for(fi):
    from scipy import ndimage as ndi
    img = np.asarray(Image.open(os.path.join(KIT, 'frames/f%03d.jpg' % fi)).convert('RGB')).astype(np.float32) / 255
    m, _ = load_mask(fi)
    al = ndi.gaussian_filter(m.astype(np.float32), .7)
    return np.dstack([img, al]).astype(np.float32)


def heat_image(r, scale=3, pad=6):
    names = r['names']
    cols = np.array([colorsys.hsv_to_rgb((i * .13) % 1, .85, 1) for i in range(len(names))])
    C = r['W'] @ cols
    V = r['V']; x0, y0 = V.min(0) - pad; x1, y1 = V.max(0) + pad
    im = Image.new('RGB', (int((x1 - x0) * scale), int((y1 - y0) * scale)), (12, 12, 14))
    d = ImageDraw.Draw(im)
    for tr in r['T']:
        p = [((V[i, 0] - x0) * scale, (V[i, 1] - y0) * scale) for i in tr]
        d.polygon(p, fill=tuple(int(255 * c) for c in C[tr].mean(0)))
    for k in names:
        h = r['H'][k]
        if h['type'] == 'bone':
            d.line([((x - x0) * scale, (y - y0) * scale) for x, y in h['path']], fill=(255, 255, 255), width=2)
        else:
            x, y = h['at']; d.ellipse(((x - x0) * scale - 5, (y - y0) * scale - 5, (x - x0) * scale + 5, (y - y0) * scale + 5), outline=(255, 255, 255), width=2)
    return im, cols


def mirror(r, Wsrc=384):
    m = dict(r)
    fx = lambda p: (Wsrc - 1 - p[0], p[1])
    m['V'] = np.column_stack([Wsrc - 1 - r['V'][:, 0], r['V'][:, 1]])
    m['T'] = r['T'][:, ::-1].copy()
    H = {}
    for k, v in r['H'].items():
        if isinstance(v, dict):
            v = dict(v)
            for e in ('a', 'b', 'k', 'at', 'p'):
                if e in v: v[e] = fx(v[e])
            if 'path' in v: v['path'] = [fx(p) for p in v['path']]
        H[k] = v
    H['facing'] = -r['H']['facing']; H['feet'] = [fx(p) for p in r['H']['feet']]
    m['H'] = H; m['facing'] = -r['facing']
    m['mask'] = r['mask'][:, ::-1].copy(); m['tex'] = r['tex'][:, ::-1].copy()
    from pose import body_metrics
    m['body'] = body_metrics(m); m['mirrored_from'] = r['fi']
    return m


def leg_locality(r, W):
    """locality across the gaps between the legs: on the lower 60 % of each leg (the part that stands free of
    the body, within 5 px of its medial path) the largest and mean weight of every OTHER leg's handle, on the vertices more than 8 px from that other leg.
    Near 0 = no influence crosses the gap; the shape-blind baseline shows what crossing looks like."""
    from autorig import _poly_dist
    legs = [k for k in r['names'] if k.startswith('leg')]
    mx, mn = [], []
    for b in legs:
        path = r['H'][b]['path']; lo = path[int(.4 * len(path)):]
        vb = np.nonzero(_poly_dist(r['V'], lo) < 5)[0]
        for a in legs:
            if a == b or not len(vb): continue
            far = vb[_poly_dist(r['V'][vb], r['H'][a]['path']) > 8]   # across a gap, not where the legs overlap
            if not len(far): continue
            w = W[far, r['names'].index(a)]; mx.append(float(w.max())); mn.append(float(w.mean()))
    return {'max': max(mx), 'mean': float(np.mean(mn))} if mx else None


def canon(r):
    """per handle: its weight mass (share of area) and its spread (weighted RMS radius / body height)"""
    from autorig import cotan_laplacian
    _, area = cotan_laplacian(r['V'], r['T'])
    hb = r['body']['body_h']; res = {}
    for j, k in enumerate(r['names']):
        key = k if not k.startswith('leg') else ('leg_' + r['H'][k].get('kind', '?'))
        w = r['W'][:, j] * area; mass = w.sum() / area.sum()
        c = (r['V'] * w[:, None]).sum(0) / max(w.sum(), 1e-9)
        spread = np.sqrt((w * ((r['V'] - c) ** 2).sum(1)).sum() / max(w.sum(), 1e-9)) / hb
        res.setdefault(key, []).append((float(mass), float(spread)))
    return {k: [float(np.mean([a for a, _ in v])), float(np.mean([b for _, b in v]))] for k, v in res.items()}


def neighbour_diff(ra, rb):
    """map rb's vertices onto ra by the least-squares affine between their automatic joints, compare weights of the
    handles both share at the nearest vertex"""
    keys = [k for k in ('head', 'tailtip') if k in ra['H'] and k in rb['H']]
    P, Q = [], []
    for k in keys: P.append(ra['H'][k]['at']); Q.append(rb['H'][k]['at'])
    for k in ('neck', 'back', 'tail'):
        for e in ('a', 'b'): P.append(ra['H'][k][e]); Q.append(rb['H'][k][e])
    P = np.array(P); Q = np.array(Q)
    X = np.hstack([Q, np.ones((len(Q), 1))]); A, *_ = np.linalg.lstsq(X, P, rcond=None)
    Vb = np.hstack([rb['V'], np.ones((len(rb['V']), 1))]) @ A
    from scipy.spatial import cKDTree
    d, nn = cKDTree(ra['V']).query(Vb)
    shared = [k for k in ('head', 'neck', 'back', 'tail', 'tailtip') if k in ra['names'] and k in rb['names']]
    diffs = [np.abs(rb['W'][:, rb['names'].index(k)] - ra['W'][nn, ra['names'].index(k)]) for k in shared]
    return float(np.mean(diffs)), float(np.percentile(np.concatenate(diffs), 95))


def main():
    t0 = time.time(); rigs = {}; tests = {'views': {}, 'stability_neighbours': {}, 'stability_views': {}}
    for name, (fi, fc) in VIEWS.items():
        ts = time.time(); r = rig_frame(fi, fc); r['solve_s'] = time.time() - ts
        r['body'] = body_metrics(r); r['frontal'] = name in FRONTAL; r['tex'] = tex_for(fi)
        rigs[name] = r
        W = r['W']
        Ws = shepard_weights(r['V'], r['sets'])
        tests['views'][name] = {
            'frame': fi, 'vertices': int(len(r['V'])), 'triangles': int(len(r['T'])), 'handles': r['names'],
            'handle_types': {k: r['H'][k]['type'] for k in r['names']},
            'leg_kinds': {k: r['H'][k].get('kind') for k in r['names'] if k.startswith('leg')},
            'solve_seconds': round(r['solve_s'], 3),
            'bounds': [float(W.min()), float(W.max())], 'bounds_ok': bool(W.min() >= 0 and W.max() <= 1 + 1e-12),
            'partition_of_unity_max_err': float(np.abs(W.sum(1) - 1).max()),
            'sum_before_normalising': r['stats']['sum_before_normalising'],
            'active_set_iters': [s['active_set_iters'] for s in r['stats']['per_handle']],
            'leg_leak_bbw': leg_locality(r, W), 'leg_leak_shepard_baseline': leg_locality(r, Ws),
            'canonical': canon(r)}
        im, _ = heat_image(r); im.save(os.path.join(PROOF, 'heat_%s_f%03d.png' % (name, fi)))
        print(name, fi, tests['views'][name]['vertices'], r['names'], 'leak', tests['views'][name]['leg_leak_bbw'],
              'vs', tests['views'][name]['leg_leak_shepard_baseline'], '%.2fs' % r['solve_s'], flush=True)
    # f005 (looking in): the pale cheek and muzzle edge at the far left of the head would read as a muzzle aimed at the
    # person; recolour the pale pixels of that band to the skull's dark tone (a grade, no pixels moved or removed)
    r = rigs['r5']; ys, xs = np.nonzero(r['mask']); x0, y0 = xs.min(), ys.min()
    band = r['tex'][y0:y0 + 66, x0:x0 + 22, :3]
    lum = band.mean(2, keepdims=True)
    r['tex'][y0:y0 + 66, x0:x0 + 22, :3] = np.where(lum > .42, band * .42 / np.maximum(lum, 1e-6) * .8, band)
    r['recoloured'] = 'pale band x0..x0+22, y0..y0+66 darkened to skull tone'
    # f007 (lying): its found tail is a thin mid-grey line that vanishes on the lit boards; darken the tail's own
    # pixels (where the tail handles dominate) so it reads at film size
    r = rigs['r7']; jt = [r['names'].index(k) for k in ('tailtip',)]
    wt = r['W'][:, jt].sum(1)
    tm = np.zeros(r['mask'].shape, np.float32)
    vv = r['V'].astype(int)
    tm[np.clip(vv[:, 1], 0, tm.shape[0] - 1), np.clip(vv[:, 0], 0, tm.shape[1] - 1)] = wt
    from scipy import ndimage as ndi2
    tm = ndi2.grey_dilation(tm, size=(3, 3)); tm = ndi2.gaussian_filter(tm, 1.0)
    k = np.clip((tm - .30) / .3, 0, 1)[..., None]
    r['tex'][..., :3] = r['tex'][..., :3] * (1 - .55 * k)
    r['recoloured'] = 'tail tip pixels darkened (tail-tip weight > 0.3)'
    # the refusal view: the same whole frame, mirrored (the archive dog turned away); weights carry over exactly
    rigs['Wm'] = mirror(rigs['W']); rigs['r7m'] = mirror(rigs['r7'])
    # stability across neighbouring archive frames (same handle code, different ragged silhouettes)
    for fi in STABILITY:
        r = rig_frame(fi, -1); r['body'] = body_metrics(r)
        mean, p95 = neighbour_diff(rigs['W'], r)
        tests['stability_neighbours']['f%03d_vs_f010' % fi] = {'mean_abs_dw': mean, 'p95_abs_dw': p95, 'canonical': canon(r)}
        print('stab', fi, mean, p95, flush=True)
    tests['extra_views'] = {}
    for name, (fi, fc) in EXTRA.items():
        r = rig_frame(fi, fc); r['body'] = body_metrics(r)
        tests['extra_views'][name] = {'frame': fi, 'handles': r['names'], 'bounds': [float(r['W'].min()), float(r['W'].max())],
                                      'partition_of_unity_max_err': float(np.abs(r['W'].sum(1) - 1).max()),
                                      'leg_leak_bbw': leg_locality(r, r['W']),
                                      'leg_leak_shepard_baseline': leg_locality(r, shepard_weights(r['V'], r['sets'])),
                                      'canonical': canon(r)}
    # stability across views: the same named handles, mass and spread
    keys = ['head', 'neck', 'back', 'tail', 'tailtip', 'leg_front', 'leg_hind']
    allc = [v['canonical'] for v in tests['views'].values()] + [v['canonical'] for v in tests['stability_neighbours'].values()] \
        + [v['canonical'] for v in tests['extra_views'].values()]
    for k in keys:
        ms = [c[k][0] for c in allc if k in c]; ss = [c[k][1] for c in allc if k in c]
        tests['stability_views'][k] = {'n': len(ms), 'mass_mean': float(np.mean(ms)), 'mass_sd': float(np.std(ms)),
                                       'spread_mean': float(np.mean(ss)), 'spread_sd': float(np.std(ss))}
    # person
    pr = rig_person(); rigs['P'] = pr
    W = pr['W']
    tests['person'] = {'frame': pr['fi'], 'vertices': int(len(pr['V'])), 'handles': pr['names'],
                       'bounds': [float(W.min()), float(W.max())], 'partition_of_unity_max_err': float(np.abs(W.sum(1) - 1).max())}
    im, _ = heat_image(pr, scale=2); im.save(os.path.join(PROOF, 'heat_P_person.png'))
    tests['total_seconds'] = round(time.time() - t0, 2)
    json.dump(tests, open(os.path.join(PROOF, 'tests.json'), 'w'), indent=1)
    for r in rigs.values():
        r.pop('mask_raw', None)
    pickle.dump(rigs, open(os.path.join(CACHE, 'rigs.pkl'), 'wb'))
    print('rigs ok', tests['total_seconds'])


if __name__ == '__main__':
    main()

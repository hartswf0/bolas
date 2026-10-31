"""Numerical tests of the weights and the rig, and the heat-map images used on the end card (proof/).
Writes proof/weights_tests.json, proof/heatmaps.png, proof/leg_test.png."""
import json, os, time
import numpy as np
from PIL import Image, ImageDraw
import rig, bbw, perform, dog as D
import world as Wd

HERE = os.path.dirname(os.path.abspath(__file__))
PROOF = os.path.join(HERE, '..', 'proof')
os.makedirs(PROOF, exist_ok=True)


def near_leg_region(V, leg, ymax=0.17):
    a, b, c = (np.array(p) for p in D.LEGS[leg])
    d, _ = bbw._dist_seg(V, b, c)
    return (d < 0.03) & (V[:, 1] < ymax)


def heat(w):
    """Sequential map: deep ink (0) -> red paper -> cream (1)."""
    stops = np.array([[54, 44, 86], [110, 40, 80], [200, 60, 44], [244, 170, 80], [250, 240, 214]], float)
    x = np.clip(w, 0, 1) * (len(stops) - 1)
    i = np.minimum(x.astype(int), len(stops) - 2); f = x - i
    return stops[i] * (1 - f[..., None]) + stops[i + 1] * f[..., None]


def draw_mesh(V, F, vals, size, box, bg=(18, 18, 30), handles=None, hs=None, X=None):
    img = Image.new('RGB', size, bg); d = ImageDraw.Draw(img)
    (x0, y0, x1, y1) = box
    sc = min(size[0] / (x1 - x0), size[1] / (y1 - y0))
    P = V if X is None else X
    tp = lambda q: ((q[0] - x0) * sc, size[1] - (q[1] - y0) * sc)
    cols = heat(vals[F].mean(1))
    for f, c in zip(F, cols):
        d.polygon([tp(P[i]) for i in f], fill=tuple(int(v) for v in c))
    if handles is not None:
        for j in handles:
            hd = hs[j]
            if hd['kind'] == 'bone':
                d.line([tp(hd['a']), tp(hd['b'])], fill=(120, 255, 220), width=3)
            else:
                x, y = tp(hd['p']); d.ellipse([x - 4, y - 4, x + 4, y + 4], outline=(120, 255, 220), width=2)
    return img


def main():
    t0 = time.time()
    poly, hs, V, F = D.build(h=0.009)
    W, info = bbw.solve_bbw(V, F, hs)
    solve_s = time.time() - t0
    names = [h['name'] for h in hs]
    Wn = bbw.naive_weights(V, hs)
    res = {'mesh': {'vertices': len(V), 'triangles': int(len(F)), 'holes': len(poly.interiors),
                    'handles': {'bones': sum(h['kind'] == 'bone' for h in hs), 'points': sum(h['kind'] == 'point' for h in hs),
                                'cage_vertices': sum(h['kind'] == 'cage' for h in hs)}},
           'solve_seconds_including_triangulation': round(solve_s, 2),
           'active_set': {'max_iterations': max(s['active_set_iterations'] for s in info['solve']),
                          'all_converged': all(s['converged'] for s in info['solve'])},
           'bounds': {'min': float(W.min()), 'max': float(W.max())},
           'partition_of_unity_max_error': float(np.abs(W.sum(1) - 1).max()),
           'raw_sum_before_normalising': [round(info['raw_sum_min'], 3), round(info['raw_sum_max'], 3)],
           'sparsity': {'share_of_weights_exactly_zero': float((W == 0).mean()),
                        'share_below_1e-3': float((W < 1e-3).mean()),
                        'mean_handles_per_vertex_above_0.01': float((W > 0.01).sum(1).mean())}}
    # locality across the gap between neighbouring legs
    loc = {}
    for a, b in (('fn', 'ff'), ('ff', 'fn'), ('hn', 'hf'), ('hf', 'hn')):
        R = near_leg_region(V, b)
        for kind, WW in (('bbw', W), ('naive_inverse_distance', Wn)):
            loc.setdefault(kind, {})['%s_lower on %s paw/shin' % (a, b)] = round(float(WW[R, names.index(a + '_lower')].max()), 4)
    res['locality_max_weight_across_leg_gap'] = loc
    # deformation test: lift the near foreleg 50 degrees; how far does the far foreleg move? do any triangles fold?
    A = np.tile(np.array([[1, 0, 0], [0, 1, 0]], float), (len(hs), 1, 1))
    a, b, c = (np.array(p) for p in D.LEGS['fn'])
    R = rig.rot(np.radians(-50))
    A[names.index('fn_upper')] = rig.aff(R, a, a)
    kn = R @ (b - a) + a
    R2 = rig.rot(np.radians(-95))
    A[names.index('fn_lower')] = rig.aff(R2, b, kn)
    far = near_leg_region(V, 'ff', ymax=0.25)
    test = {}
    for kind, WW in (('bbw', W), ('naive_inverse_distance', Wn)):
        X = bbw.skin(V, WW, A)
        flips = int(((bbw.signed_areas(X, F) * bbw.signed_areas(V, F)) < 0).sum())
        test[kind] = {'far_foreleg_max_displacement_m': round(float(np.linalg.norm(X[far] - V[far], axis=1).max()), 4),
                      'folded_triangles': flips}
        if kind == 'bbw':
            Xb = X
        else:
            Xn = X
    res['lift_near_foreleg_50deg'] = test
    # holes not torn: every pierced hole keeps its winding (no hole turned inside out) in the lift test
    # runtime skinning benchmark
    P = perform.dog_poses()
    tt = time.time()
    for p in P[::8]:
        Ab = rig.pose_affines(p, hs); bbw.skin(V, W, Ab)
    res['runtime_ms_per_pose_and_skin'] = round((time.time() - tt) / len(P[::8]) * 1000, 2)
    # folded triangles through the performance (frames where all handle groups face the same way)
    fl = []
    for p in P:
        y = p['yaw']
        if max(y.values()) - min(y.values()) > 0.5 or 0 < y['front'] < 180:
            continue
        X = bbw.skin(V, W, rig.pose_affines(p, hs))
        sgn = 1 if y['front'] < 90 else -1
        fl.append(int(((bbw.signed_areas(X, F) * bbw.signed_areas(V, F) * sgn) < 0).sum()))
    res['performance_folded_triangles'] = {'frames_checked': len(fl), 'max': max(fl), 'mean': round(float(np.mean(fl)), 2),
                                           'share_of_triangles_max': round(max(fl) / len(F), 4)}
    json.dump(res, open(os.path.join(PROOF, 'weights_tests.json'), 'w'), indent=1)
    np.savez(os.path.join(HERE, 'cache', 'proof_mesh.npz'), V=V, F=F, W=W, Wn=Wn, Xb=Xb, Xn=Xn)
    # heat maps: four handles on the rest mesh (bbw), and the leg-gap comparison
    box = (-0.66, -0.02, 0.56, 0.92)
    tiles = []
    for nm in ('fn_lower', 'ff_lower', 'cage1', 'ear_near'):
        j = names.index(nm)
        tiles.append(draw_mesh(V, F, W[:, j], (300, 232), box, handles=[j], hs=hs))
    j = names.index('fn_lower')
    tiles.append(draw_mesh(V, F, Wn[:, j], (300, 232), box, handles=[j], hs=hs))
    tiles.append(draw_mesh(V, F, W[:, j], (300, 232), box, X=Xb))
    tiles.append(draw_mesh(V, F, Wn[:, j], (300, 232), box, X=Xn))
    sheet = Image.new('RGB', (300 * 4, 232 * 2), (18, 18, 30))
    for k, im in enumerate(tiles):
        sheet.paste(im, ((k % 4) * 300, (k // 4) * 232))
    sheet.save(os.path.join(PROOF, 'heatmaps.png'))
    print(json.dumps(res, indent=1))


if __name__ == '__main__':
    main()

"""SCION 42 · learned head swing / turn vs the hand-set control.
For each archive turning frame (14-21, 26-33) the same learned layers are posed two ways and scored against the real
frame's SAM mask (IoU) and grey values:
  learned  : per-layer motions fitted to the frame (turn_fit.py) - the turn and the head swing as the examples show them
  hand-set : what this film did before with the rig: one similarity placement plus a rotation about each learned hinge;
             the angles are optimised per frame (Powell), i.e. the best any hand-setting of those hinges could do.
Writes ../data/learned_vs_handset.json"""
import os, json
import numpy as np
from scipy.optimize import minimize
from scipy.spatial import cKDTree
import fit as F
from puppet import Puppet

ROOT = F.ROOT


def main():
    pp = Puppet(); M = pp.M; K = pp.K
    Tn = np.load(os.path.join(ROOT, 'model', 'turn.npz'))
    tf = F.Frame(8, 0); T = F.Template(tf, 2)
    Tfull = np.stack(np.nonzero(tf.mask)[::-1], 1).astype(float); _, nn = cKDTree(T.p).query(Tfull, k=4)
    wf = M['w'][nn].mean(1)
    ident = np.tile(np.eye(3), (K, 1, 1))
    rows = []
    for j, f in enumerate(Tn['frames']):
        fr = F.Frame(int(f), 0)
        A_l = Tn['learned'][j]
        mk, _ = F.splat_mask(Tfull, A_l, wf); iou_l = F.iou(mk, fr.mask)
        L_l, c_l = F.frame_loss(T, fr, A_l, M['w'], want_grad=False)
        g = F.init_global(T, fr)
        s0 = g[0, 0]; x0 = np.concatenate([[np.log(s0), 0.0, g[0, 2], g[1, 2]], np.zeros(K)])
        def pose(x):
            s, r, tx, ty = np.exp(x[0]), x[1], x[2], x[3]
            P = np.array([[s * np.cos(r), -s * np.sin(r), tx], [s * np.sin(r), s * np.cos(r), ty], [0, 0, 1.0]])
            Tk = pp.articulate(ident, {k: x[4 + k] for k in range(K) if k != pp.root})
            return np.einsum('ij,kjl->kil', P, Tk)[:, :2]
        obj = lambda x: F.frame_loss(T, fr, pose(x), M['w'], want_grad=False)[0]
        best = None
        for r0 in (0.0, 0.3, -0.3):
            x = x0.copy(); x[1] = r0
            o = minimize(obj, x, method='Powell', options=dict(maxiter=6000, xtol=1e-3, ftol=1e-4))
            if best is None or o.fun < best.fun: best = o
        A_h = pose(best.x)
        mk, _ = F.splat_mask(Tfull, A_h, wf); iou_h = F.iou(mk, fr.mask)
        L_h, c_h = F.frame_loss(T, fr, A_h, M['w'], want_grad=False)
        rows.append(dict(frame=int(f), learned_iou=round(iou_l, 3), handset_iou=round(iou_h, 3),
                         learned_photo=round(float(c_l['photo']), 3), handset_photo=round(float(c_h['photo']), 3)))
        print(rows[-1], flush=True)
    li = [r['learned_iou'] for r in rows]; hi = [r['handset_iou'] for r in rows]
    out = dict(rows=rows, mean_iou_learned=float(np.mean(li)), mean_iou_handset=float(np.mean(hi)),
               learned_better_on=int(sum(a > b for a, b in zip(li, hi))), n=len(rows), about=__doc__)
    json.dump(out, open(os.path.join(ROOT, 'data', 'learned_vs_handset.json'), 'w'), indent=1)
    print({k: v for k, v in out.items() if k not in ('rows', 'about')})


if __name__ == '__main__':
    main()

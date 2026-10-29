"""SCION 42 · learned visibility states: the archive frames of the dog turning (14-21: left profile -> head toward the
camera -> front; 26-33: front) are fitted by the learned layers (masks frozen, motions free, hinge consistency on) and,
as the control, by the hand-cut 8-part rig from the kit keypoints under the identical fit.  The fitted poses become the
puppet's turn and head-swing states, so turning dog and profile dog are one material.
Writes ../model/turn.npz and ../data/turn_compare.json, ../proof/turn_fit.jpg
"""
import os, json
import numpy as np
from PIL import Image, ImageDraw
from scipy.spatial import cKDTree
import fit as F

ROOT = F.ROOT
SEQ = list(range(14, 22)) + list(range(26, 34))


def main():
    M = np.load(os.path.join(ROOT, 'model', 'puppet.npz'))
    w = M['w']; K = w.shape[1]; w_auth = M['w_auth']; Ka = w_auth.shape[1]
    tf = F.Frame(int(M['template_frame']), 0); T = F.Template(tf, 2)
    Tfull = np.stack(np.nonzero(tf.mask)[::-1], 1).astype(float)
    tr = cKDTree(T.p); _, nn = tr.query(Tfull, k=4)
    wf, waf = w[nn].mean(1), w_auth[nn].mean(1)
    hinge = F.boundary_pairs(T, M['lab'])
    hinge_a = F.boundary_pairs(T, M['lab_auth'])
    out = {'learned': [], 'authored': []}; rows = []; tiles = []
    for i in SEQ:
        fr = F.Frame(i, 0)
        A0 = F.init_global(T, fr)[None, None]
        A0, _, _, _ = F.fit(T, [fr], 1, w=np.ones((T.N, 1)), A=A0, iters=250, lam_conf=10.)
        res = {}
        for name, ww, wfull, KK, hg in (('learned', w, wf, K, hinge), ('authored', w_auth, waf, Ka, hinge_a)):
            A = np.repeat(A0, KK, axis=1)
            A, _, _, h = F.fit(T, [fr], KK, w=ww, A=A, iters=500, lam_conf=20., hinge=hg, lam_h=F.LAM_H)
            mk, _ = F.splat_mask(Tfull, A[0], wfull)
            res[name] = dict(iou=F.iou(mk, fr.mask), photo=float(h[-1]['photo']), mask=mk)
            out[name].append(A[0])
        rows.append(dict(frame=i, learned_iou=round(res['learned']['iou'], 3), authored_iou=round(res['authored']['iou'], 3),
                         learned_photo=round(res['learned']['photo'], 3), authored_photo=round(res['authored']['photo'], 3)))
        print(rows[-1], flush=True)
        im = np.stack([fr.im * 255] * 3, -1).astype(np.uint8)
        for nm, col in (('authored', (90, 170, 255)), ('learned', (255, 200, 40))):
            mk = res[nm]['mask']; e = mk ^ F.ndimage.binary_erosion(mk, iterations=1); im[e] = col
        t = Image.fromarray(im).resize((288, 216)); ImageDraw.Draw(t).text((4, 4), 'f%02d learned %.2f / hand-cut %.2f' % (i, res['learned']['iou'], res['authored']['iou']), fill=(255, 255, 255))
        tiles.append(t)
    S = Image.new('RGB', (288 * 8, 216 * 2))
    for j, t in enumerate(tiles): S.paste(t, ((j % 8) * 288, (j // 8) * 216))
    S.save(os.path.join(ROOT, 'proof', 'turn_fit.jpg'), quality=85)
    np.savez_compressed(os.path.join(ROOT, 'model', 'turn.npz'), frames=np.array(SEQ), learned=np.stack(out['learned']), authored=np.stack(out['authored']))
    li = [r['learned_iou'] for r in rows]; ai = [r['authored_iou'] for r in rows]
    summ = dict(frames=SEQ, rows=rows, mean_iou_learned=float(np.mean(li)), mean_iou_authored=float(np.mean(ai)),
                learned_better_on=int(sum(a > b for a, b in zip(li, ai))), n=len(rows),
                note='same template, same losses, same iterations, masks frozen; only the part split differs (learned layers vs keypoint-cut rig)')
    json.dump(summ, open(os.path.join(ROOT, 'data', 'turn_compare.json'), 'w'), indent=1)
    print({k: v for k, v in summ.items() if k != 'rows'})


if __name__ == '__main__':
    main()

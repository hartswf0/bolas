"""SCION 42 · motion library: the learned layers (masks frozen) are fitted to every usable profile frame of the source
clip, so the puppet's motion repertoire is the archive dog's own motion re-expressed as per-layer affines.
  walk_up  : frames 0-13, dog facing left, head up (it walks toward the person)
  walk_low : frames 40-46, dog facing right, head low (it walks to the bowl), mirrored to face left
Writes ../model/library.npz and ../proof/reconstruction.jpg (learned puppet re-rendered over the real frames, held-out
frames marked).  Only motions are optimised here; nothing about the layers changes.
"""
import os, json
import numpy as np
from PIL import Image, ImageDraw
import fit as F

ROOT = F.ROOT
SEQ = {'walk_up': [(i, 0) for i in range(0, 14)], 'walk_low': [(i, 1) for i in range(40, 47)]}


def main():
    M = np.load(os.path.join(ROOT, 'model', 'puppet.npz'))
    w = M['w']; K = w.shape[1]
    tf = F.Frame(int(M['template_frame']), 0)
    T = F.Template(tf, 2)
    assert np.allclose(T.p, M['p'])
    train = {(int(a), int(b)) for a, b in M['train']}
    out = {}; recon = []
    Tfull_p = np.stack(np.nonzero(tf.mask)[::-1], 1).astype(float)
    from scipy.spatial import cKDTree
    _, nn = cKDTree(T.p).query(Tfull_p, k=4); wfull = w[nn].mean(1)
    stats = []
    hinge = F.boundary_pairs(T, M['lab'])
    for name, seq in SEQ.items():
        As = []
        prev = None
        for (i, m) in seq:
            fr = F.Frame(i, m)
            if prev is None:
                A = F.init_global(T, fr)[None, None]
                A, _, _, _ = F.fit(T, [fr], 1, w=np.ones((T.N, 1)), A=A, iters=250, lam_conf=10.)
                A = np.repeat(A, K, axis=1)
            else:
                # warm start from the previous frame, shifted by the centroid motion
                A = prev.copy(); A[0, :, :, 2] += fr.cen - prevc
            A, _, _, h = F.fit(T, [fr], K, w=w, A=A, iters=450, lam_conf=20., hinge=hinge, lam_h=F.LAM_H)
            prev, prevc = A, fr.cen
            mk, _ = F.splat_mask(Tfull_p, A[0], wfull)
            iou = F.iou(mk, fr.mask)
            stats.append(dict(seq=name, frame=i, mirrored=m, iou=iou, photo=h[-1]['photo'], in_training=(i, m) in train))
            print(stats[-1], flush=True)
            As.append(A[0])
            recon.append((fr, mk, (i, m) in train, iou))
        out[name] = np.stack(As)
    np.savez_compressed(os.path.join(ROOT, 'model', 'library.npz'), **out)
    json.dump(stats, open(os.path.join(ROOT, 'data', 'library_fit.json'), 'w'), indent=1)
    # proof sheet: real frame | learned puppet silhouette outline
    tiles = []
    for fr, mk, tr, iou in recon:
        im = np.stack([fr.im * 255] * 3, -1).astype(np.uint8)
        edge = mk ^ F.ndimage.binary_erosion(mk, iterations=1)
        im[edge] = (255, 200, 40)
        t = Image.fromarray(im).resize((256, 192))
        ImageDraw.Draw(t).text((5, 4), 'f%02d%s %s IoU %.2f' % (fr.i, 'm' if fr.m else '', 'train' if tr else 'UNSEEN', iou), fill=(255, 255, 255) if tr else (120, 255, 140))
        tiles.append(t)
    cols = 7; rows = (len(tiles) + cols - 1) // cols
    S = Image.new('RGB', (256 * cols, 192 * rows))
    for j, t in enumerate(tiles): S.paste(t, ((j % cols) * 256, (j // cols) * 192))
    S.save(os.path.join(ROOT, 'proof', 'reconstruction.jpg'), quality=85)


if __name__ == '__main__':
    main()

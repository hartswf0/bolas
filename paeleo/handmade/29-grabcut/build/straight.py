"""QA inspector (round 3): longest straight run of boundary pixels (horizontal or vertical) in a mask, in pixels of the
mask's own scale. Used on the rendered dog coverage (canvas px) and on source cuts scaled to film size."""
import numpy as np
from graphcut import erode


def longest_runs(mask):
    c = mask & ~erode(mask, 1)
    best = [0, 0]
    for axis, arr in ((0, c), (1, c.T)):
        for row in arr:
            if not row.any():
                continue
            d = np.diff(np.concatenate([[0], row.astype(np.int8), [0]]))
            st = np.nonzero(d == 1)[0]; en = np.nonzero(d == -1)[0]
            m = int((en - st).max())
            best[axis] = max(best[axis], m)
    return {'h': best[0], 'v': best[1]}


if __name__ == '__main__':
    import sys, os
    from PIL import Image
    C = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache', 'dog')
    for i in [int(a) for a in sys.argv[1:]]:
        a = np.load(os.path.join(C, 'f%03d.npz' % i))['alpha'].astype(np.float32)
        h, w = a.shape; s = 1.36
        b = np.array(Image.fromarray((a * 255).astype(np.uint8)).resize((int(w * s), int(h * s)), Image.BILINEAR)) > 127
        print(i, longest_runs(b))

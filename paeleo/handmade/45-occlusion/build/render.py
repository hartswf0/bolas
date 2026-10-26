"""SCION 45 · Render verifier's harness. Renders score frames (all 768 by default) in parallel.
python3 render.py [step] [first] [last]   -> build/cache/frames/s%04d.jpg + build/cache/records/r%04d.json
Every 4th frame is also re-composited by per-pixel depth test (the verifier) and compared with the DAG composite.
"""
import json, os, sys, time
from multiprocessing import Pool
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
FD = os.path.join(HERE, 'cache/frames'); RD = os.path.join(HERE, 'cache/records')


def work(i):
    import scene
    fr, rec, layers = scene.render(i, verify=(i % 4 == 0))
    Image.fromarray((np.clip(fr, 0, 1) * 255 + 0.5).astype(np.uint8)).save(os.path.join(FD, 's%04d.jpg' % i), quality=93)
    json.dump(rec, open(os.path.join(RD, 'r%04d.json' % i), 'w'), default=float)
    return i


if __name__ == '__main__':
    os.makedirs(FD, exist_ok=True); os.makedirs(RD, exist_ok=True)
    step = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    a = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    b = int(sys.argv[3]) if len(sys.argv) > 3 else 767
    procs = int(os.environ.get('PROCS', '3'))
    idx = list(range(a, b + 1, step))
    t0 = time.time()
    with Pool(procs) as p:
        for n, i in enumerate(p.imap_unordered(work, idx, chunksize=2)):
            if n % 48 == 0:
                print('frame', i, n, '/', len(idx), round(time.time() - t0), 's', flush=True)
    print('done', len(idx), round(time.time() - t0), 's')

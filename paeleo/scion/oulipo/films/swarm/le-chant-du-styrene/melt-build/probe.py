"""probe frames + stats into a sheet (dev tool): python3 -I probe.py out.jpg t1 t2 ..."""
import sys; sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/le-chant-du-styrene/melt-build")
import melt3 as m, numpy as np
from PIL import Image
ts = [float(x) for x in sys.argv[2:]]
ims = []
for ft in ts:
    a = m.band(ft, int(round(ft * 24)))
    L = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
    print(ft, 'lt20', (L < 20).mean().round(3), 'p95', np.percentile(L, 95).round(1), 'p99', np.percentile(L, 99).round(1), 'max', L.max().round())
    ims.append(Image.fromarray(a))
sh = Image.new('RGB', (960 * 2, 408 * ((len(ims) + 1) // 2)))
for i, im in enumerate(ims): sh.paste(im, ((i % 2) * 960, (i // 2) * 408))
sh.save(sys.argv[1], quality=88)

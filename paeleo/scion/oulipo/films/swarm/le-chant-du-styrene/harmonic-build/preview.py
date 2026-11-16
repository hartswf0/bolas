import sys, time
import numpy as np, cv2
sys.path.insert(0, '.')
import trees
out = sys.argv[1]
ts = [float(x) for x in sys.argv[2:]]
tiles = []
for t in ts:
    a = time.time(); im, v = trees.frame(t); print(t, round(time.time()-a,2), 'vis', v, flush=True)
    im = (im*255+.5).astype(np.uint8)
    cv2.putText(im, f'{t:.2f}', (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (120,120,120), 1)
    tiles.append(im)
cv2.imwrite(out, cv2.cvtColor(np.vstack(tiles), cv2.COLOR_RGB2BGR))

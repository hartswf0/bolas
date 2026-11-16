# the shoe's one monotone curve, neutral: luminance, p2 -> L105, p50 -> L218, p99.5 -> L246 (piecewise-linear in
# a smooth monotone spline), R=G=B. Keeps the satin/kid relief; makes the object read as the whitest thing on screen.
import sys, json, numpy as np
from PIL import Image
src, dst = sys.argv[1], sys.argv[2]
A = np.asarray(Image.open(src).convert("RGBA"), np.float32)
Y = 0.299 * A[..., 0] + 0.587 * A[..., 1] + 0.114 * A[..., 2]
m = A[..., 3] > 200
q = np.percentile(Y[m], [2, 50, 99.5])
xs = [0, q[0], q[1], q[2], 255]; ys = [40, 105, 218, 246, 250]
out = np.interp(Y, xs, ys)
R = np.dstack([out, out, out, A[..., 3]]).clip(0, 255).astype(np.uint8)
Image.fromarray(R, "RGBA").save(dst)
yy = out[m]
print(json.dumps(dict(curve_in=[round(float(v), 1) for v in q], curve_out=[105, 218, 246],
                      shoe_luma_p=[int(np.percentile(yy, p)) for p in (5, 25, 50, 75, 95)])))

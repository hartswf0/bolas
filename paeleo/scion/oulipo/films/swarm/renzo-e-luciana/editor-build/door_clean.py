"""Retouch the Delano doorway (LoC 2017829778): remove the lab technician by copying the negative's own pixels
(window panes from the same window one/two pane rows up; wall/floor by smooth fill plus the plate's own grain residual
taken from a flat wall patch of the same negative). Output: door_clean.png (RGBA, same geometry as door.png)."""
import numpy as np, cv2
from PIL import Image
C2 = '/home/user/bolas/paeleo/scion/oulipo/films/swarm/renzo-e-luciana/test-shot-build/cache2'
OUT = '/home/user/bolas/paeleo/scion/oulipo/films/sources/renzo-e-luciana/editor'
a = np.asarray(Image.open(C2 + '/door.png')).astype(np.float32); b = np.asarray(Image.open(C2 + '/door_empty.png')).astype(np.float32)
g = a[..., 0].copy(); al = a[..., 3]
m = cv2.dilate((np.abs(a[..., 0] - b[..., 0]) > 2).astype(np.uint8), np.ones((7, 7), np.uint8)) > 0
m[:, 368:] = False                                     # never touch the right jamb
out = g.copy(); filled = ~m
H, W = g.shape
# 1. window panes (rows 176..434): copy from the same column 62*k px higher (pane period measured: muntins at 176/238/300)
for y in range(H):
    for x in np.nonzero(m[y])[0]:
        if y <= 434:
            for k in (1, 2, 3, 4):
                ys = y - 62 * k
                if ys >= 176 and filled[ys, x] and not m[ys, x]:
                    out[y, x] = g[ys, x]; filled[y, x] = True; break
# 2. wall under the window (rows 435..562): tile the visible wall strip of the same rows (x 190..207, the pilaster foot)
# 3. floor (rows 563..): tile the visible floor strip of the same rows just left of the figure (x 205..239)
# 4. bench front (x >= 322, rows 435..): tile vertically from the visible bench below the figure
rng = np.random.default_rng(4)
# per-row tone of the flat wall/floor just left of the figure (x 228..238, the first clean column band), smoothed down the rows
def _rowv(y):
    a, b = (186, 207) if y <= 562 else (150, 240)          # wall: the pilaster foot; floor: the open floor left of the figure
    v = g[y, a:b][~m[y, a:b]]; return np.median(v) if len(v) else np.nan
ROWV = np.array([_rowv(y) for y in range(H)])
ok = ~np.isnan(ROWV); ROWV = np.interp(np.arange(H), np.nonzero(ok)[0], ROWV[ok]); ROWV = cv2.GaussianBlur(ROWV.reshape(-1, 1).astype(np.float32), (0, 0), 3).ravel()
pt = g[760:820, 110:170]; GR = pt - cv2.GaussianBlur(pt, (0, 0), 2.0)      # the negative's own grain (flat floor patch)
for y in range(435, H):
    xs = np.nonzero(m[y] & ~filled[y])[0]
    if not len(xs): continue
    for x in xs:
        if x >= 322:
            ys = y
            while ys < H and m[ys, x]: ys += 1
            if ys < H:
                per = 24; src = ys + ((ys - y) % per)
                out[y, x] = g[min(src, H - 1), x]; filled[y, x] = True; continue
        out[y, x] = ROWV[y] + GR[y % GR.shape[0], x % GR.shape[1]]; filled[y, x] = True
rest = m & ~filled
if rest.any():
    out = cv2.inpaint(np.clip(out, 0, 255).astype(np.uint8), rest.astype(np.uint8), 3, cv2.INPAINT_TELEA).astype(np.float32)
# feather the seam
fm = np.clip(cv2.GaussianBlur(m.astype(np.float32), (0, 0), 4.0) * 1.6, 0, 1)
fin = g * (1 - fm) + out * fm
Image.fromarray(np.dstack([np.clip(fin, 0, 255)] * 3 + [al]).astype(np.uint8), 'RGBA').save(OUT + '/door_clean.png')
v = np.hstack([g, fin])[140:700, 100:840]
Image.fromarray(np.clip(v, 0, 255).astype(np.uint8)).save('/tmp/claude-0/-home-user/a99ec93a-6f31-57b0-a2ec-fb930dfe1aad/scratchpad/door_clean_cmp.png')
print('masked px', m.sum(), 'window-copied', (m & filled).sum(), 'smooth+grain', rest.sum())

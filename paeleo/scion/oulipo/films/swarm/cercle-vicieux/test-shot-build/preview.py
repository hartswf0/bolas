import sys; sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/cercle-vicieux/test-shot-build")
import numpy as np, cv2, time
import panels as P
O = "/home/user/bolas/paeleo/scion/oulipo/films/sources/cercle-vicieux/test-shot/work/"
t0 = time.time()
T, TH, PH, D, E, st = P.simulate_x()
print("strikes", [(round(a, 2), round(b, 2)) for a, b in st]); print("E end/peak", E[-1] / E.max(), "lag first move", T[np.argmax(np.abs(TH) > .01)], T[np.argmax(np.abs(PH) > .01)])
xs = [P.panel_x(k)[0] for k in (0, 36, 70, 124)]
print("x time", time.time() - t0)
row = np.hstack(xs)
cv2.imwrite(O + "pv_x.png", cv2.resize(row, (row.shape[1] // 4, row.shape[0] // 4), interpolation=cv2.INTER_AREA))
h = P.panel_h(83); g, _ = P.panel_g(); f = P.panel_f(); e = P.panel_e()
grid = np.vstack([np.hstack([h, g]), np.hstack([f, e])])
cv2.imwrite(O + "pv_cells.png", cv2.resize(grid, (grid.shape[1] // 3, grid.shape[0] // 3), interpolation=cv2.INTER_AREA))
print("total", time.time() - t0)

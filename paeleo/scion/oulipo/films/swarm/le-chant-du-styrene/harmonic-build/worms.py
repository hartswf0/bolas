"""no-worm check: for pellets adjacent on the same strand, how many travel together (relative displacement < 4 px)
and the coefficient of variation of the gap between them, at several times."""
import sys, json, math
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import trees as T
def positions(tr, t):
    ths, Phi, posed = tr.pose(t)
    out = []
    for p in tr.pellets:
        st = tr.strands[p["strand"]]; pts, _ = tr.strand_pts(st, ths, Phi, posed)
        ctr = pts[p["centre_i"]]
        i0 = max(0, p["centre_i"] - 1); i1 = min(len(pts) - 1, p["centre_i"] + 1)
        tg = pts[i1] - pts[i0]; tg = tg / (np.linalg.norm(tg) + 1e-6); nm = np.array([-tg[1], tg[0]])
        d, e = T.pellet_disp(p, tr, t)
        out.append((p["strand"], ctr + e * (p["jit_t"] * tg + p["jit_n"] * nm) + d, d))
    return out
res = {}
for t in (32.9, 33.2, 33.45, 33.6, 34.0):
    together = 0; pairs = 0; gaps = []
    for tr in T.FRONT_T:
        if t < tr.t_cut(): continue
        ps = positions(tr, t)
        for a, b in zip(ps[:-1], ps[1:]):
            if a[0] != b[0]: continue
            pairs += 1
            if np.linalg.norm(a[2] - b[2]) < 4.0: together += 1
            gaps.append(np.linalg.norm(a[1] - b[1]))
    g = np.array(gaps)
    res[f"{t:.2f}"] = dict(adjacent_pairs=pairs, fraction_travelling_together=round(together / max(pairs, 1), 3),
                           gap_mean_px=round(float(g.mean()), 1), gap_cv=round(float(g.std() / g.mean()), 3))
print(json.dumps(res, indent=1))
(Path(__file__).resolve().parent / "worms.json").write_text(json.dumps(res, indent=1))

import numpy as np, colorsys
from PIL import Image
def band_stats(a):
    a = np.asarray(a, np.float32)[..., :3]
    lum = a @ np.array([0.299, 0.587, 0.114])
    r, g, b = a[...,0]/255, a[...,1]/255, a[...,2]/255
    mx = np.max(a/255, -1); mn = np.min(a/255, -1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    # hue in degrees
    d = np.maximum(mx - mn, 1e-6)
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    lit = lum > 25
    hl = h[lit]
    cl = {"red": ((hl < 20) | (hl >= 340)).mean(), "orange": ((hl >= 20) & (hl < 32)).mean(),
          "amber": ((hl >= 32) & (hl < 60)).mean(), "blue": ((hl >= 190) & (hl < 260)).mean()}
    return {"frac_lum_lt_20": round(float((lum < 20).mean()), 3), "lum_median": round(float(np.median(lum)), 1),
            "lum_p95": round(float(np.percentile(lum, 95)), 1), "lum_p99": round(float(np.percentile(lum, 99)), 1),
            "lum_max": round(float(lum.max()), 1), "lit_frac": round(float(lit.mean()), 3),
            "lit_median_sat": round(float(np.median(sat[lit])), 3) if lit.any() else None,
            "hue_clusters_of_lit": {k: round(float(v), 3) for k, v in cl.items()},
            "warm_share_of_lit": round(float(cl["red"] + cl["orange"] + cl["amber"]), 3)}

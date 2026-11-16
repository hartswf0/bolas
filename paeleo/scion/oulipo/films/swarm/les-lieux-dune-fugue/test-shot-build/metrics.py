"""Measure the reference regions (sec. 6) on a film frame."""
import sys, json, numpy as np
from PIL import Image
def m(p):
    a = np.asarray(Image.open(p).convert('RGB')).astype(float); H, W = a.shape[:2]
    L = a @ [0.299, 0.587, 0.114]
    R = lambda x0, y0, x1, y1: a[int(y0*H):int(y1*H), int(x0*W):int(x1*W)]
    st = R(0.62, 0.28, 0.98, 0.80); door = R(0.16, 0.40, 0.50, 0.95); pl = R(0.62, 0.86, 0.98, 0.99)
    stL = st @ [0.299, 0.587, 0.114]
    rows = stL.mean(1)
    return dict(frame=a.reshape(-1, 3).mean(0).round(1).tolist(), p5=float(np.percentile(L, 5)), p50=float(np.median(L)),
                p95=float(np.percentile(L, 95)), stone=st.reshape(-1, 3).mean(0).round(1).tolist(), stone_sd=round(float(stL.std()), 1),
                stone_R_minus_B=round(float(st[..., 0].mean() - st[..., 2].mean()), 1),
                joint_row_min=round(float(rows.min()), 1), stone_row_median=round(float(np.median(rows)), 1),
                door=door.reshape(-1, 3).mean(0).round(1).tolist(), door_sd=round(float((door @ [0.299, 0.587, 0.114]).std()), 1),
                plinth=pl.reshape(-1, 3).mean(0).round(1).tolist())
if __name__ == '__main__':
    out = {p: m(p) for p in sys.argv[1:]}
    print(json.dumps(out, indent=1))

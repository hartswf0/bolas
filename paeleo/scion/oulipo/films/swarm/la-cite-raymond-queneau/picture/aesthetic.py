"""Plan section 9.6 numeric aesthetic test on frame t=4.0 s (k=96) + side-by-sides at 4.0 s and 21.0 s."""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import maquette as M

REF = "/home/user/bolas/paeleo/scion/oulipo/assets/references/citefilm.webp"
OUT = os.path.dirname(os.path.abspath(__file__))

def region_masks(k):
    """sample regions from the model's own geometry (wide set-up), mapped to frame px."""
    M.use_cam("wide")
    b = M.BLOCKS[2]
    def fp(pt, plane):
        x, y = M.canvas_to_frame(k, plane, *pt)
        return (x / M.SS, y / M.SS)
    fac = [fp(p, "P3") for p in M.facade_quad(b)]
    roof = [fp(M.proj(b["s_left"], b["n"] + M.RR * (1 - np.cos(t)), M.HE + M.RR * np.sin(t)), "P3") for t in np.linspace(0.05, 1.2, 12)]
    roof += [fp(M.proj(b["s_left"] - M.LEN, b["n"] + M.RR * (1 - np.cos(t)), M.HE + M.RR * np.sin(t)), "P3") for t in np.linspace(1.2, 0.05, 12)]
    masks = {}
    for name, poly in (("facade", fac), ("roof", roof)):
        m = Image.new("L", (M.PW, M.PH), 0); ImageDraw.Draw(m).polygon(poly, fill=255)
        masks[name] = np.asarray(m) > 0
    sky = np.zeros((M.PH, M.PW), bool); sky[4:40, 10:250] = True
    masks["sky"] = sky
    return masks

def check(k=96):
    a = np.asarray(M.frame(k)).astype(np.float32)
    lum = 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
    sat = a.max(2) - a.min(2)
    m = region_masks(k)
    sky = np.median(a[m["sky"]], axis=0)
    fpx = a[m["facade"]]; fl = lum[m["facade"]]
    cream = fpx[(fl > 140) & (sat[m["facade"]] < 40)]
    fac = np.median(cream, axis=0)
    rpx = a[m["roof"]]; rl = lum[m["roof"]]
    roof = np.median(rpx[(rl < 150) & (rl > 40)], axis=0)
    roofL = 0.299 * roof[0] + 0.587 * roof[1] + 0.114 * roof[2]
    p2, p50, p98 = np.percentile(lum, [2, 50, 98])
    r = np.asarray(Image.open(REF).convert("RGB")).astype(np.float32)
    rl_ = 0.299 * r[..., 0] + 0.587 * r[..., 1] + 0.114 * r[..., 2]
    tests = {
        "sky_within_12_of_(240,230,240)": bool(np.all(np.abs(sky - np.array([240, 230, 240])) <= 12)),
        "facade_R_minus_B_le_20": bool(fac[0] - fac[2] <= 20),
        "facade_within_25_of_(175,178,163)": bool(np.all(np.abs(fac - np.array([175, 178, 163])) <= 25)),
        "roof_B_ge_R": bool(roof[2] >= roof[0]),
        "roof_luma_75_130": bool(75 <= roofL <= 130),
        "luma_p50_115_170": bool(115 <= p50 <= 170),
        "mean_sat_le_30": bool(sat.mean() <= 30),
    }
    res = dict(frame=k, t=k / 24.0, method="regions from the model geometry: sky = rows 4-40, x 10-250 (open sky above the far blocks); facade = near-block facade polygon, cream pixels (luma>140, max-min<40); roof = near-block quarter-cylinder band, luma 40-150",
               sky_median=sky.round(1).tolist(), facade_cream_median=fac.round(1).tolist(), roof_median=roof.round(1).tolist(), roof_luma=round(float(roofL), 1),
               luma_p2_p50_p98=[round(float(v), 1) for v in (p2, p50, p98)], mean_saturation=round(float(sat.mean()), 1),
               reference=dict(luma_p2_p50_p98=[round(float(v), 1) for v in np.percentile(rl_, [2, 50, 98])], mean_saturation=round(float((r.max(2) - r.min(2)).mean()), 1)),
               tests=tests, passed=all(tests.values()))
    return res

def side_by_side(k, path):
    ref = Image.open(REF).convert("RGB")
    ref = ref.resize((int(ref.width * M.PH / ref.height), M.PH), Image.LANCZOS)
    f = M.frame(k)
    W = Image.new("RGB", (ref.width + 16 + M.PW, M.PH), (243, 239, 228))
    W.paste(ref, (0, 0)); W.paste(f, (ref.width + 16, 0))
    W.save(path, quality=90)

if __name__ == "__main__":
    res = check(96)
    json.dump(res, open(os.path.join(OUT, "aesthetic-check.json"), "w"), indent=1)
    print(json.dumps(res, indent=1))
    if len(sys.argv) > 1:
        side_by_side(96, os.path.join(OUT, "side-by-side-4s.jpg"))
        side_by_side(504, os.path.join(OUT, "side-by-side-21s.jpg"))

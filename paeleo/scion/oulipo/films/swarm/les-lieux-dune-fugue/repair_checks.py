"""repair_checks.py -- repair-round-1 acceptance checks (editor), on U2's lossless stage frames and on the
final render. Writes repair-1/repair_checks.json and a few crops.

  * scissor edges: every P01 piece edge inside a 300x300 stone crop (frame x 600-900, y 250-550) is
    measured on the piece's own alpha: max deviation of its contour from the fitted straight line, and
    the rendered lamp-A frame's rim (1-2 px inside the cut, on the lamp-facing sides) vs the piece's
    interior. Pass if >= 80 % of edges are non-straight (>= 1.0 px) AND >= 80 % of lamp-side edges
    show a light core (>= +4 grey levels).
  * A/B: mean abs luminance difference 0:02 vs 0:29 (>= 10) and how much of it sits in the 5 px band
    around piece boundaries (door leaves excluded).
  * P03 seams: strongest full-width horizontal step in rows 560-700 and around the trunk crown.
  * card: the 0:55 render frame is saved for the six-source / 'fictif' / licence lines.
"""
import json, os, subprocess, sys
import numpy as np, cv2
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import paper_stage as PS  # noqa

OUT = HERE + "/repair-1"
os.makedirs(OUT, exist_ok=True)
MP4 = PS.ROOT + "/assets/films/les-lieux-dune-fugue.mp4"
L = lambda im: np.asarray(im.convert("RGB")).astype(np.float32) @ np.float32([0.299, 0.587, 0.114])


def frame(t):
    out = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", MP4, "-frames:v", "1", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return Image.fromarray(np.frombuffer(out, np.uint8).reshape(720, 960, 3))


res = {}
# ---------------------------------------------------------------- scissor edges (rebuild the piece table as bake does)
PS.rng = np.random.default_rng(1978)
_, pcs = PS.build_facade()
fa = L(PS.render_shot(1, 2.0, log=False))
CX0, CY0, CX1, CY1 = 600, 250, 900, 550
edges = []
for p in pcs:
    h, w = p.a.shape
    x0, y0 = p.x - PS.P, p.y - PS.P
    if x0 + w < CX0 or x0 > CX1 or y0 + h < CY0 or y0 > CY1 or min(w, h) < 20 or p.name.startswith(("sill", "balcony")):
        continue
    m = p.a > 0.5
    rows, cols = np.nonzero(m.any(1))[0], np.nonzero(m.any(0))[0]
    for side in ("top", "bottom", "left", "right"):
        if side in ("top", "bottom"):
            xs = np.arange(cols[0] + 6, cols[-1] - 6)
            prof = np.array([np.nonzero(m[:, x])[0][0 if side == "top" else -1] for x in xs], np.float32)
            coord = xs
            gx = x0 + xs; gy = y0 + prof
        else:
            ys = np.arange(rows[0] + 6, rows[-1] - 6)
            prof = np.array([np.nonzero(m[y])[0][0 if side == "left" else -1] for y in ys], np.float32)
            coord = ys
            gx = x0 + prof; gy = y0 + ys
        inside = (gx >= CX0) & (gx < CX1) & (gy >= CY0) & (gy < CY1)
        if inside.sum() < 15:
            continue
        cf = np.polyfit(coord[inside], prof[inside], 1)
        dev = float(np.abs(prof[inside] - np.polyval(cf, coord[inside])).max())
        # rim 1-2 px inside the cut vs interior 6-10 px inside, on the rendered lamp-A frame
        sgn = 1 if side in ("top", "left") else -1
        rim, inn = [], []
        for c, pr in zip(coord[inside], prof[inside]):
            for k, lst in ((1.5, rim), (8, inn)):
                if side in ("top", "bottom"):
                    yy, xx = int(round(y0 + pr + sgn * k)), int(x0 + c)
                else:
                    yy, xx = int(y0 + c), int(round(x0 + pr + sgn * k))
                if 0 <= yy < 720 and 0 <= xx < 960:
                    lst.append(fa[yy, xx])
        lamp_side = side in ("top", "left")          # lamp A is upper left
        edges.append(dict(piece=p.name, side=side, max_dev_px=round(dev, 2), rim_minus_interior=round(float(np.mean(rim) - np.mean(inn)), 1),
                          lamp_side=lamp_side))
ns = [e for e in edges if e["max_dev_px"] >= 1.0]
ls = [e for e in edges if e["lamp_side"]]
lc = [e for e in ls if e["rim_minus_interior"] >= 4]
res["scissor_edges_300px_crop"] = dict(crop=[CX0, CY0, CX1, CY1], edges=len(edges), non_straight_ge_1px=len(ns),
                                       share_non_straight=round(len(ns) / max(1, len(edges)), 3), lamp_side_edges=len(ls),
                                       lamp_side_with_light_core=len(lc), share_light_core=round(len(lc) / max(1, len(ls)), 3),
                                       median_dev_px=float(np.median([e["max_dev_px"] for e in edges])) if edges else None,
                                       PASS=bool(len(ns) >= 0.8 * len(edges) and len(lc) >= 0.8 * len(ls)), detail=edges)
Image.fromarray(np.asarray(PS.render_shot(1, 2.0, log=False))[CY0:CY1, CX0:CX1]).save(OUT + "/stone300_A_100pct.png")

# ---------------------------------------------------------------- A/B difference
B = PS.B(); hm = B["fac"][PS.LAMP_A.name]["hmap"][PS.P:PS.P + 720, PS.P:PS.P + 960]
eb = cv2.morphologyEx(hm.astype(np.float32), cv2.MORPH_GRADIENT, np.ones((3, 3))) > 0.4
eb = cv2.dilate(eb.astype(np.uint8), np.ones((5, 5))) > 0
eb[216:, 125:525] = False
for tag, (ia, ib) in {"stage_lossless": (PS.render_shot(1, 2.0, log=False), PS.render_shot(4, 29.0, log=False)),
                      "render_mp4": (frame(2.0), frame(29.0))}.items():
    d = np.abs(L(ia) - L(ib))
    res[f"AB_diff_{tag}"] = dict(mean_abs_diff=round(float(d.mean()), 2), edge_band_mean=round(float(d[eb].mean()), 2),
                                 interior_mean=round(float(d[~eb].mean()), 2), edge_band_fraction=round(float(eb.mean()), 3),
                                 edge_to_interior_ratio=round(float(d[eb].mean() / max(d[~eb].mean(), 1e-3)), 2),
                                 PASS_ge_10=bool(d.mean() >= 10))
# shadow offsets of the deepest pieces under each lamp
rows = {}
for lamp in (PS.LAMP_A, PS.LAMP_B):
    for p in pcs:
        if p.name.startswith(("jamb-L0", "jamb-R0", "lintel-0", "lintel-2", "plaque", "headband-")):
            h, w = p.a.shape
            dx, dy, bl = lamp.offset(p.x + w / 2, p.y + h / 2, p.zb, p.z - p.zb)
            rows.setdefault(p.name, {})[lamp.name[0]] = round(float(np.hypot(dx, dy)), 2)
res["deep_piece_shadow_offset_px"] = rows

# ---------------------------------------------------------------- P03 seams
p3 = L(PS.render_shot(3, 26.0, log=False))
rowstep = np.abs(np.diff(cv2.GaussianBlur(p3, (0, 0), 0.6).mean(1)))
res["P03_seams"] = dict(max_full_width_row_step_560_700=round(float(rowstep[560:700].max()), 2),
                        median_row_step=round(float(np.median(rowstep)), 2),
                        note="row step = change of the full-width row mean between adjacent rows; a ruled seam shows as a spike")
crown = p3[200:300, 100:360]
res["P03_seams"]["crown_max_row_step_200_300"] = round(float(np.abs(np.diff(crown.mean(1))).max()), 2)
Image.fromarray(np.asarray(PS.render_shot(3, 26.0, log=False))[150:720, 40:500]).save(OUT + "/p03_trunk_litter_100pct.png")

# ---------------------------------------------------------------- card frame
frame(55.0).save(OUT + "/card_55s_render.png")
json.dump(res, open(OUT + "/repair_checks.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps({k: (v if k != "scissor_edges_300px_crop" else {kk: vv for kk, vv in v.items() if kk != "detail"}) for k, v in res.items()}, indent=1))

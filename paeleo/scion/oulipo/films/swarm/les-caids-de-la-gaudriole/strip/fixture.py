"""strip/fixture.py - section 7 fixture (#8 constraint trace) for sheet rev 1.

Writes strip/fixture.json, strip/seam-100x.png, strip/strip-flat.png and
strip/strip-folded.png from strip/strip-art.png (the one art raster).

Checks
  1  folded view == V(x') pixel for pixel, where the reference V is built by
     fold.folded_view and the candidate is an independent orthographic top view
     of the settled 3D pleat (fold.cross_section(pi, pi), exact arcs);
     also strip-folded.png re-read from disk == V.
  2  seam residuals for the frame borders, balloon top/bottom, floor line and
     the cuff/wrist band (ink runs crossing x = A-2 in P1 vs x = B+2 in P2).
  3  no orphan ink: no ink component in V that touches the seam and is too small
     to belong to a continued stroke (a cut-off scrap of a hidden line).
  4  ghost positions: every fragment's mapped position recomputed from fold.py and
     matched against sheet.json; each hidden balloon fragment is located in the
     light-box layer by template matching (mirrored for F1) within 2 u.
  5  100x seam crops: four 40 x 40 u crops of V centred on the seam.
"""
import os, sys, json, math, hashlib
import numpy as np
import cv2
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fold as F
from pen import pen

A, M, B, D, W, H = F.A, F.M, F.B, F.D, F.W, F.H
TAU = F.S.TAU
ART = os.environ.get("STRIP_ART", os.path.join(HERE, "strip-art.png"))
OUT = os.environ.get("FIXTURE_OUT", HERE)


def runs(col):
    r, on = [], None
    for y, v in enumerate(col):
        if v and on is None: on = y
        if not v and on is not None: r.append((on, y - 1)); on = None
    if on is not None: r.append((on, len(col) - 1))
    return r


def main():
    sheet = np.asarray(Image.open(ART).convert("L"))
    assert sheet.shape == (H, W), sheet.shape
    sha = hashlib.sha256(open(ART, "rb").read()).hexdigest()
    rep = {"strip_art": "strip/strip-art.png", "strip_art_sha256": sha, "sheet_rev": F._sheet["revision"]}
    sj = F._sheet
    if sj["strip_art"].get("sha256") != sha:
        rep["warning_sha_mismatch_sheet_json"] = sj["strip_art"].get("sha256")

    # ---- 1. folded view
    V = F.folded_view(sheet)
    cs = F.cross_section(math.pi, math.pi, 1.6, 1.6, du=0.05)
    tv_all = F.top_view_index(cs, np.arange(D, W))
    crease_edge_cols = [int(x - D) for x, b in zip(tv_all["X"], tv_all["in_band"]) if b]
    tv = F.top_view_index(cs, np.arange(D, W), exclude_bands=True)
    worst, cols, back = 0, 0, 0
    bad_cols = []
    for X, u, fc in zip(tv["X"], tv["u"], tv["face"]):
        if np.isnan(u) or int(X - D) in crease_edge_cols: continue
        if fc < 0: back += 1; continue
        ui = int(min(W - 1, max(0, math.floor(u))))
        if np.abs(sheet[:, ui].astype(int) - V[:, X - D].astype(int)).max() > 0: bad_cols.append([int(X - D), ui])
        worst = max(worst, int(np.abs(sheet[:, ui].astype(int) - V[:, X - D].astype(int)).max()))
        cols += 1
    rep["1_folded_eq_V"] = dict(independent_top_view_max_abs_diff=worst, columns_checked=cols,
                                back_face_columns_visible=back, mismatched_columns=bad_cols[:20], crease_edge_columns_xprime=crease_edge_cols,
                                crease_edge_note='columns where the pressed curl (0.5 u radius) is the top surface; the rolled edge of the same paper, excluded from the pixel test',
                                facet_map_err_u=dict(
                                    F0=float(np.abs(cs["X"][cs["u"] < A - 1] - (cs["u"][cs["u"] < A - 1] + D)).max()),
                                    F1=float(np.abs(cs["X"][(cs["u"] > A + 1) & (cs["u"] < M - 1)] - (2 * M - cs["u"][(cs["u"] > A + 1) & (cs["u"] < M - 1)])).max())),
                                layer_heights_u=[float(cs["z"][(cs["u"] > A + 1) & (cs["u"] < M - 1)].mean()), float(cs["z"][cs["u"] < A - 1].mean())],
                                layer_order=F.layer_order(cs))
    Image.fromarray(sheet).save(os.path.join(OUT, "strip-flat.png"))
    Image.fromarray(V).save(os.path.join(OUT, "strip-folded.png"))
    Vd = np.asarray(Image.open(os.path.join(OUT, "strip-folded.png")))
    rep["1_folded_eq_V"]["strip_folded_png_max_abs_diff"] = int(np.abs(Vd.astype(int) - V.astype(int)).max())
    rep["1_folded_eq_V"]["pass"] = worst == 0 and rep["1_folded_eq_V"]["strip_folded_png_max_abs_diff"] == 0 and back == 0

    # ---- 2. seam residuals
    ink = sheet < 128
    ra, rb = runs(ink[:, A - 2]), runs(ink[:, B + 2])
    def near(rr, y, lo, hi):
        c = [r for r in rr if lo <= (r[0] + r[1]) / 2 <= hi]
        return min(c, key=lambda r: abs((r[0] + r[1]) / 2 - y)) if c else None
    seams = []
    for cid, name, y, lo, hi in [("C7", "frame top border", 50, 35, 65), ("C9", "balloon top border", 80, 66, 95),
                                 ("C10", "balloon bottom border", 276, 260, 292), ("C11", "floor line", 792, 775, 810),
                                 ("C8", "frame bottom border", 850, 836, 866)]:
        a, b = near(ra, y, lo, hi), near(rb, y, lo, hi)
        if a and b:
            res = abs((a[0] + a[1]) / 2 - (b[0] + b[1]) / 2)
            wa, wb = a[1] - a[0] + 1, b[1] - b[0] + 1
            seams.append(dict(id=cid, what=name, P1_at_A=list(a), P2_at_B=list(b), residual_u=res,
                              width_diff_u=abs(wa - wb), pass_=bool(res <= TAU)))
        else:
            seams.append(dict(id=cid, what=name, P1_at_A=a, P2_at_B=b, residual_u=None, pass_=False, note="line missing at one side"))
    # cuff / wrist: every ink run crossing x = A-2 inside the sleeve band must have a
    # partner crossing x = B+2 within tau (outer contours and the cuff stripes)
    lo_, hi_ = F._sheet["constraints"][11]["y_band"]
    ca = [r for r in ra if lo_ <= (r[0] + r[1]) / 2 <= hi_]
    cb = [r for r in rb if lo_ <= (r[0] + r[1]) / 2 <= hi_]
    pairs = []
    for r in ca:
        c = (r[0] + r[1]) / 2
        q = min(cb, key=lambda s: abs((s[0] + s[1]) / 2 - c)) if cb else None
        pairs.append(dict(P1_at_A=list(r), P2_at_B=list(q) if q else None,
                          residual_u=abs((q[0] + q[1]) / 2 - c) if q else None))
    worst_c = max([p["residual_u"] for p in pairs if p["residual_u"] is not None] or [None]) if pairs else None
    env_a = (ca[0][0], ca[-1][1]) if ca else None; env_b = (cb[0][0], cb[-1][1]) if cb else None
    seams.append(dict(id="C12", what="miller cuff at A / porter wrist at B", runs=pairs, n_runs=[len(ca), len(cb)],
                      envelope_A=env_a, envelope_B=env_b,
                      width_A=(env_a[1] - env_a[0] + 1) if env_a else None, width_B=(env_b[1] - env_b[0] + 1) if env_b else None,
                      residual_u=worst_c,
                      rule="every P1 contour run at A has a P2 partner at B within tau; outer envelope top/bottom within tau (interior cuff/wrist hatching may differ)",
                      pass_=bool(ca and worst_c is not None and worst_c <= TAU
                                 and abs(env_a[0] - env_b[0]) <= TAU and abs(env_a[1] - env_b[1]) <= TAU)))
    rep["2_seams"] = seams
    rep["2_all_crossings"] = dict(P1_at_A=[[int(a), int(b)] for a, b in ra], P2_at_B=[[int(a), int(b)] for a, b in rb])
    rep["2_pass"] = all(s["pass_"] for s in seams)

    # ---- 3. orphan ink in V near the seam
    vi = (V < 128).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(vi, connectivity=8)
    orphans = []
    for i in range(1, n):
        x, y, w, h, area = st[i]
        if x <= A + 1 and x + w >= A - 1 and area < 40:
            orphans.append(dict(bbox=[int(x), int(y), int(x + w), int(y + h)], area=int(area)))
    # scraps of the hidden ink that end exactly at the seam on one side only
    rep["3_no_orphan_ink"] = dict(small_components_touching_seam=orphans, components_total=int(n - 1),
                                  every_V_pixel_has_sheet_source=bool(worst == 0), pass_=len(orphans) == 0)

    # ---- 4. ghost positions
    st_ = F.lightbox_stack(sheet)
    gh = []
    for fr in sj["fragments"]:
        x0, y0, x1, y1 = fr["bbox"]
        g = F.ghost_position(x0, x1)
        ok_map = abs(g["x"][0] - fr["folded"][0]) < 0.11 and abs(g["x"][1] - fr["folded"][1]) < 0.11
        rec = dict(id=fr["id"], text=fr["text"], sheet_bbox=fr["bbox"], layer=g["layer"], mirrored=g["mirrored"],
                   visible=g["visible"], expected_x=g["x"], map_matches_sheet_json=bool(ok_map))
        if fr["layer"] == "balloon" and not g["visible"]:
            tpl = sheet[int(y0) - 4:int(y1) + 4, int(math.floor(x0)) - 4:int(math.ceil(x1)) + 4]
            if g["mirrored"]: tpl = tpl[:, ::-1]
            lay = st_["layers"][g["layer"] - 1]
            band_ = lay[int(y0) - 10:int(y1) + 10]
            res = cv2.matchTemplate(band_.astype(np.float32), tpl.astype(np.float32), cv2.TM_SQDIFF)
            _, _, mn, _ = cv2.minMaxLoc(res)
            found_x0 = mn[0] + 4
            exp_x0 = g["x"][0] if not g["mirrored"] else g["x"][0]
            # for a mirrored crop, its left edge sits at 2A - ceil(x1) - 4
            exp_left = (2 * A - (int(math.ceil(x1)) + 4) + 1) if g["mirrored"] else (int(math.floor(x0)) - 4 - D)
            rec["found_left_px"] = int(mn[0]); rec["expected_left_px"] = int(exp_left)
            rec["found_err_u"] = abs(int(mn[0]) - int(exp_left))
            rec["found_y_err_u"] = abs(mn[1] - 6)
            rec["pass_"] = bool(rec["found_err_u"] <= 2 and rec["found_y_err_u"] <= 2 and ok_map)
        else:
            rec["pass_"] = bool(ok_map)
        gh.append(rec)
    rep["4_ghosts"] = gh
    rep["4_pass"] = all(g["pass_"] for g in gh)


    # ---- 6. lettering sits at the frozen fragment bboxes (L ends before the crease, R starts after it)
    txt = []
    for fr in sj["fragments"]:
        if fr["layer"] != "balloon" or fr["line"] is None: continue
        x0, y0, x1, y1 = fr["bbox"]
        f_ = A if fr["panel"] == "P1" else B
        lo, hi = (int(x0) - 14, f_ - 1) if fr["side"] == "L" else (f_ + 1, int(x1) + 14)
        band_ = ink[int(y0) - 3:int(y1) + 6, lo:hi]
        colsx = np.nonzero(band_.any(0))[0]
        if len(colsx) == 0:
            txt.append(dict(id=fr["id"], text=fr["text"], found=None, pass_=False)); continue
        gx0, gx1 = lo + int(colsx[0]), lo + int(colsx[-1])
        err = max(abs(gx0 - x0), abs(gx1 - x1))
        clear = (f_ - gx1) if fr["side"] == "L" else (gx0 - f_)
        txt.append(dict(id=fr["id"], text=fr["text"], frozen_x=[x0, x1], ink_x=[gx0, gx1], max_err_u=round(err, 1),
                        clearance_to_crease_u=int(clear), pass_=bool(err <= 8 and clear >= 8)))
    rep["6_lettering_at_frozen_bbox"] = txt
    rep["6_pass"] = all(t["pass_"] for t in txt)

    # ---- 5. 100x seam crops (40 x 40 u = 4 x 4 mm, enlarged 25 px/u)
    K = 25
    cuff_y = None
    for s in seams:
        if s["id"] == "C12" and s.get("envelope_A"): cuff_y = s["envelope_A"][0] + 8   # the sleeve top contour
    crops = [("BALLOON TOP", 80), ("BALLOON BOTTOM", 276), ("FLOOR LINE", 792), ("SLEEVE / HAND", cuff_y or 520)]
    tile = 40 * K
    out = Image.new("L", (2 * tile + 120, 2 * (tile + 110) + 40), 255)
    d = ImageDraw.Draw(out)
    meta = []
    for i, (name, y) in enumerate(crops):
        y = int(round(y))
        c = V[y - 20:y + 20, A - 20:A + 20]
        big = Image.fromarray(c).resize((tile, tile), Image.NEAREST)
        ox, oy = 40 + (i % 2) * (tile + 40), 40 + (i // 2) * (tile + 110)
        out.paste(big, (ox, oy + 70))
        d.rectangle([ox - 2, oy + 68, ox + tile + 1, oy + 71 + tile], outline=0, width=2)
        # seam ticks outside the crop (x' = A at crop column 20)
        sx = ox + 20 * K
        d.polygon([(sx - 14, oy + 40), (sx + 14, oy + 40), (sx, oy + 64)], fill=0)
        d.polygon([(sx - 14, oy + tile + 100), (sx + 14, oy + tile + 100), (sx, oy + tile + 76)], fill=0)
        pen(d, name, ox, oy, 34, ink=0, seed=700 + i)
        pen(d, "SEAM A=B", sx + 24, oy + 34, 22, ink=0, seed=720 + i)
        meta.append(dict(name=name, center_folded=[A, y], size_u=40, px_per_u=K))
    out.save(os.path.join(OUT, "seam-100x.png"))
    rep["5_seam_crops"] = dict(path="strip/seam-100x.png", crops=meta,
                               magnification="each 4 x 4 mm crop is 1000 px: 100x when shown at 0.4 mm per screen pixel")
    rep["pass_all"] = bool(rep["1_folded_eq_V"]["pass"] and rep["2_pass"] and rep["3_no_orphan_ink"]["pass_"] and rep["4_pass"] and rep["6_pass"])
    json.dump(rep, open(os.path.join(OUT, "fixture.json"), "w"), indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    return rep


if __name__ == "__main__":
    r = main()
    print(json.dumps({k: (v if k in ("pass_all", "2_pass", "4_pass") else "...") for k, v in r.items()}))
    print("folded", r["1_folded_eq_V"])
    for s in r["2_seams"]: print(s["id"], s["what"], s.get("residual_u"), s["pass_"])
    print("orphans", r["3_no_orphan_ink"]["small_components_touching_seam"])
    for g in r["4_ghosts"]:
        if not g["pass_"]: print("GHOST FAIL", g)

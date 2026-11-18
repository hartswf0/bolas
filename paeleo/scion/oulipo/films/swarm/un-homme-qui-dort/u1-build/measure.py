"""Assemble S7 (S5 frames byte-identical, then S5's last frame held), measure every shot, write
u1-contact.jpg and u1-aesthetic-compare.jpg. The reference is shown beside the frames on the comparison
sheet only (study); it is never composited into a film frame."""
import shutil
import sys
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/un-homme-qui-dort/u1-build")
from shotio import *
from PIL import ImageDraw

SW = FILMS / "swarm" / "un-homme-qui-dort"
REF = FILMS.parent / "assets" / "references" / "sommeil.webp"
SH = U1 / "shots"

# ---- S7
d7 = SH / "S7"; d7.mkdir(exist_ok=True)
for f in d7.glob("*.png"):
    f.unlink()
s5 = sorted((SH / "S5").glob("S5_*.png"))
assert len(s5) == 132
for i, f in enumerate(s5):
    shutil.copyfile(f, d7 / f"S7_{i:04d}.png")
for i in range(132, 192):
    shutil.copyfile(s5[-1], d7 / f"S7_{i:04d}.png")
sha = {s: [sha1(f) for f in sorted((SH / s).glob("*.png"))] for s in ("S1", "S2", "S3", "S4", "S5", "S6", "S7")}
assert sha["S7"][:132] == sha["S5"], "S7 != S5"
assert all(h == sha["S5"][-1] for h in sha["S7"][132:])
for s, n in SHOT_N.items():
    assert len(sha[s]) == n, (s, len(sha[s]))

R = {k: json.loads((U1 / "json" / f"{k}_render.json").read_text()) for k in ("s1", "s2", "s34", "s5", "s6")}
cov5 = R["s5"]["figure_alpha_coverage"]; scov5 = R["s5"]["shadow_alpha_coverage"]
cov7 = cov5 + [0.0] * 60; scov7 = scov5 + [scov5[-1]] * 60

# ---- per-frame neutrality (all frames) and per-shot stats on a representative frame
REP = {"S1": 30, "S2": 36, "S3": 60, "S4": round(15.0 * FPS) - 276, "S5": 72, "S6": 30, "S7": 150}
HEAD = {"S1": R["s1"]["head_height_frac"], "S3": R["s34"]["S3"]["head_height_frac"], "S4": R["s34"]["S4"]["head_height_frac"],
        "S5": R["s5"]["head_height_frac"], "S2": None, "S6": None, "S7": None}
stats = {}
for s in SHOT_N:
    files = sorted((SH / s).glob("*.png"))
    chroma_max, p1s, p99s = 0.0, [], []
    for f in files[::6]:
        a = np.asarray(Image.open(f).convert("RGB")).astype(np.float32)
        chroma_max = max(chroma_max, float((a.max(2) - a.min(2)).mean()))
        L = a.mean(2); p1s.append(float(np.percentile(L, 1))); p99s.append(float(np.percentile(L, 99)))
    rep = np.asarray(Image.open(files[REP[s]]).convert("RGB"))
    st = frame_stats(rep, HEAD[s])
    st.update({"rep_frame": REP[s], "rep_pass_t": round(SHOT_T0[s] + REP[s] / FPS, 3), "max_mean_chroma_all_sampled_frames": round(chroma_max, 3),
               "p1_range_sampled": [round(min(p1s), 1), round(max(p1s), 1)], "p99_range_sampled": [round(min(p99s), 1), round(max(p99s), 1)]})
    stats[s] = st

# ---- grain check (S4 flat wall patch vs graded source plate resampled to film scale)
g, c, _ = graded_plate("2017862340", (2200, 1500, 4790, 3196))
cx0, cy0, cx1, cy1 = R["s34"]["S4"]["crop_plate"]
src4 = cv2.resize(g[cy0:cy1, cx0:cx1], (W, H), interpolation=cv2.INTER_AREA) * 255
f4 = np.asarray(Image.open(sorted((SH / "S4").glob("*.png"))[0]).convert("L")).astype(np.float32)
def hp(a): return a - cv2.GaussianBlur(a, (0, 0), 3)
patch = (slice(60, 200), slice(60, 300))   # pale wall, upper left of S4
grain = {"patch_screen_xy": [60, 60, 300, 200], "film_highpass_std": round(float(hp(f4)[patch].std()), 3),
         "graded_source_highpass_std": round(float(hp(src4)[patch].std()), 3)}
grain["excess"] = round(grain["film_highpass_std"] - grain["graded_source_highpass_std"], 3)
grain["pass"] = grain["excess"] <= 0.5
ref = np.asarray(Image.open(REF).convert("RGB"))
ref_stats = frame_stats(ref, 0.48)

# ---- parallax ratios
def ratios(layers):
    ks = [l["k"] for l in layers]
    return {"k_by_layer": {l["name"]: l["k"] for l in layers}, "near_over_far": round(max(ks) / min(ks), 3)}
parallax = {"S1": ratios(R["s1"]["layers"]), "S2": ratios(R["s2"]["layers"]), "S3": ratios(R["s34"]["S3"]["layers"]),
            "S4": {"note": "same rig as S3, camera at rest (no glide)"}, "S5": ratios(R["s5"]["layers"]), "S6": ratios(R["s6"]["layers"]),
            "S7": {"note": "S5 frames reused"}}
parallax["S2"]["note"] = "push: per-plane scale 1+(zoom-1)*k, wall 1.04, coats 1.08"

# ---- event frames (pass-relative)
vis = [i for i, v in enumerate(cov5) if v > 0]
events = {
    "E1": {"planned_t": [2.0, 2.8], "planned_frames": [48, 67], "authored_frames": [R["s1"]["E1"]["onset_frame"], R["s1"]["E1"]["end_frame"]]},
    "E3_turn": {"planned_t": 9.25, "planned_frame": 222, "authored_frame": R["s34"]["E3_frames"]["turn_onset_pass_frame"]},
    "E3_return": {"planned_t": 10.4, "planned_frame": 250, "authored_frame": R["s34"]["E3_frames"]["return_onset_pass_frame"]},
    "E4_enter": {"planned_t": 20.5, "planned_frame": 492, "measured_first_figure_frame": 456 + vis[0], "measured_t": round((456 + vis[0]) / FPS, 4)},
    "E4_exit": {"planned_t": 23.5, "planned_frame": 564, "measured_first_empty_frame": 456 + vis[-1] + 1, "measured_t": round((456 + vis[-1] + 1) / FPS, 4)},
    "E5_footfalls": {"planned_t": [20.8, 21.35, 21.9, 22.45, 23.0], "authored_pass_frames": [456 + f for f in R["s5"]["events"]["footfall_frames"]], "dip_px": 3},
    "E6_enter": {"planned_t": 28.5, "measured_first_figure_frame": 648 + vis[0], "measured_t": round((648 + vis[0]) / FPS, 4)},
    "E6_exit": {"planned_t": 31.5, "measured_first_empty_frame": 648 + vis[-1] + 1, "measured_t": round((648 + vis[-1] + 1) / FPS, 4)},
    "E7_footfalls": {"authored_pass_frames": [648 + f for f in R["s5"]["events"]["footfall_frames"]]},
}
for k, v in events.items():
    if "planned_frame" in v:
        got = v.get("authored_frame", v.get("measured_first_figure_frame", v.get("measured_first_empty_frame")))
        v["within_1_frame"] = abs(got - v["planned_frame"]) <= 1
sh_vis7 = [i for i, v in enumerate(scov7) if v > 0]
D = {"pass_B_c5": [29.7, 32.5], "figure_gone_from_pass_t": round(27.0 + (vis[-1] + 1) / FPS, 4),
     "empty_stair_seconds_under_c5B": round(32.5 - max(29.7, 27.0 + (vis[-1] + 1) / FPS), 4),
     "shadow_gone_from_pass_t": round(27.0 + (sh_vis7[-1] + 1) / FPS, 4) if sh_vis7 else None}

# ---- contact sheet
def label(im, txt, h=38):
    out = Image.new("RGB", (im.width, im.height + h), (30, 30, 30))
    out.paste(im, (0, 0)); d = ImageDraw.Draw(out)
    d.text((6, im.height + 4), txt, fill=(239, 239, 239), font=kit.font("mono", 12))
    return out
tw, th = 320, 180
rows = []
picks = {"S1": [0, 48, 67, 131], "S2": [0, 24, 48, 71], "S3": [0, 18, 30, 60], "S4": [0, 90, 179, 179],
         "S5": [20, 50, 80, 110], "S6": [0, 20, 40, 59], "S7": [36, 72, 107, 191]}
for s, fr in picks.items():
    files = sorted((SH / s).glob("*.png"))
    ims = [label(Image.open(files[i]).convert("RGB").resize((tw, th), Image.LANCZOS),
                 f"{s} f{i:03d} t={SHOT_T0[s] + i / FPS:5.2f}") for i in fr]
    row = Image.new("RGB", (4 * (tw + 4), th + 38), (30, 30, 30))
    for j, im in enumerate(ims):
        row.paste(im, (j * (tw + 4), 0))
    rows.append(row)
sheet = Image.new("RGB", (rows[0].width, sum(r.height + 4 for r in rows)), (30, 30, 30))
y = 0
for r in rows:
    sheet.paste(r, (0, y)); y += r.height + 4
sheet.save(SW / "u1-contact.jpg", quality=88)

# ---- aesthetic comparison: reference (study only) beside one frame per shot, stats under each
def stat_txt(st):
    return (f"chroma {st['mean_chroma']:.2f}  p1 {st['p1']:.0f}  p50 {st['p50']:.0f}  p99 {st['p99']:.0f}\n"
            f"<60 {st['frac_below_60']:.3f}  >220 {st['frac_above_220']:.3f}  mid {st['frac_60_220']:.3f}"
            + (f"\nhead/frame {st['head_height_frac']:.2f}" if st.get("head_height_frac") else "\nhead/frame n/a"))
cw, ch = 400, 225
cells = []
refim = Image.open(REF).convert("RGB"); refim.thumbnail((cw, ch))
cells.append(("REFERENCE sommeil.webp (study only, not in film)", refim, stat_txt(ref_stats)))
for s in ("S1", "S2", "S3", "S4", "S5", "S6", "S7"):
    f = sorted((SH / s).glob("*.png"))[REP[s]]
    cells.append((f"{s} pass t={stats[s]['rep_pass_t']:.2f}", Image.open(f).convert("RGB").resize((cw, ch), Image.LANCZOS), stat_txt(stats[s])))
CH = ch + 84
cmp_ = Image.new("RGB", (2 * (cw + 8), 4 * CH), (30, 30, 30))
dd = ImageDraw.Draw(cmp_)
for i, (t, im, tx) in enumerate(cells):
    x, y = (i % 2) * (cw + 8), (i // 2) * CH
    cmp_.paste(im, (x, y)); dd.text((x + 4, y + ch + 4), t, fill=(245, 245, 245), font=kit.font("mono", 12))
    dd.multiline_text((x + 4, y + ch + 22), tx, fill=(214, 214, 214), font=kit.font("mono", 11), spacing=3)
cmp_.save(SW / "u1-aesthetic-compare.jpg", quality=90)

# ---- targets
tgt = {}
for s, st in stats.items():
    t = {"neutral_le_1.5": st["max_mean_chroma_all_sampled_frames"] <= 1.5, "p1_in_20_40": 20 <= st["p1"] <= 40, "p99_in_236_250": 236 <= st["p99"] <= 250}
    if s in ("S3", "S4"):
        t["bimodal_sum_ge_0.55"] = st["frac_below_60"] + st["frac_above_220"] >= 0.55
        t["below60_within_0.12_of_0.416"] = abs(st["frac_below_60"] - 0.416) <= 0.12
        t["above220_within_0.12_of_0.326"] = abs(st["frac_above_220"] - 0.326) <= 0.12
    tgt[s] = t
res = {"sha1": sha, "S5_equals_S7_first_132": sha["S7"][:132] == sha["S5"], "S7_tail_held_identical": all(h == sha["S5"][-1] for h in sha["S7"][132:]),
       "figure_alpha_coverage": {"S5": cov5, "S7": cov7}, "shadow_alpha_coverage": {"S5": scov5, "S7": scov7},
       "stats": stats, "reference_stats_measured_here": ref_stats, "targets": tgt, "grain_check": grain, "parallax": parallax,
       "events": events, "defining_beat_D": D}
dump(U1 / "json" / "measure.json", res)
print(json.dumps({"targets": tgt, "grain": grain, "events": {k: v.get("within_1_frame") for k, v in events.items()}, "D": D}, indent=0))
for s in stats:
    print(s, {k: stats[s][k] for k in ("mean_chroma", "p1", "p50", "p99", "frac_below_60", "frac_above_220", "head_height_frac")})

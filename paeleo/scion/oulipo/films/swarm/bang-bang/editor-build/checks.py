# Editor repair 1 checks: saved frames, side-by-side with the reference and kf-2, palette measurements, the
# no-identical-letter test on every slip, and file facts.  python3 films/swarm/bang-bang/editor-build/checks.py
import importlib.util, json, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image

SW = Path(__file__).resolve().parents[1]
FILMS = SW.parents[1]
PROJ = FILMS.parent
spec = importlib.util.spec_from_file_location("bb", FILMS / "bang-bang.py")
bb = importlib.util.module_from_spec(spec); sys.argv = ["x"]; spec.loader.exec_module(bb)

film = bb.main_film()
frames = {}
for f in (12, 100, 528, 540, 548, 564, 605, 700):
    im = film.frame(f); im.save(SW / f"frame_f{f:03d}.png"); frames[f] = np.asarray(im).astype(np.float32)


def lum(a): return a @ np.array([0.299, 0.587, 0.114], np.float32)


def palette(a):
    L = lum(a); ink = L < 110; mid = (L >= 110) & (L < 200); pap = L >= 200
    return {"ink_pct": round(100 * ink.mean(), 2), "mid_pct": round(100 * mid.mean(), 2),
            "paper_median": [int(v) for v in np.median(a[pap], 0)],
            "ink_median": [int(v) for v in np.median(a[L < np.percentile(L, 0.5) + 1], 0)] if ink.any() else None}


def lab(c):
    c = np.asarray(c, np.float64) / 255
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = M @ c / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.array([116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])])


meas = {}
# page region of the wide frame (the sheet only, not the desk)
cx, cy, z = bb.B.CAM_WIDE; z *= bb.KZ
x0 = int((0 - (cx - bb.OW / z / 2)) * z) + 6; x1 = int((bb.PW - (cx - bb.OW / z / 2)) * z) - 6
y0 = int((0 - (cy - bb.OH / z / 2)) * z) + 6; y1 = int((bb.PH - (cy - bb.OH / z / 2)) * z) - 6
page700 = frames[700][y0:y1, x0:x1]
meas["f700_page"] = palette(page700)
meas["f540"] = palette(frames[540])
ref = np.asarray(Image.open(PROJ / "assets" / "references" / "bang.webp").convert("RGB")).astype(np.float32)
meas["reference_bang_webp"] = palette(ref)
meas["paper_dE_vs_target_242_228_212"] = round(float(np.linalg.norm(lab(meas["f700_page"]["paper_median"]) - lab((242, 228, 212)))), 2)
# panel interior vs page (page space, sheet 2, ink excluded)
S = bb.sheet(2); Ls = lum(S)
inner = S[bb.PYS[1] + 40:bb.PYS[1] + bb.PHT - 120, bb.PX + 40:bb.PX + bb.PWID - 40]; Li = lum(inner)
outer = S[200:1600, 1500:2100]; Lo = lum(outer)
pi_med = np.median(inner[Li > 200], 0); po_med = np.median(outer[Lo > 200], 0)
meas["panel_interior_median"] = [int(v) for v in pi_med]; meas["page_median"] = [int(v) for v in po_med]
meas["panel_vs_page_dE"] = round(float(np.linalg.norm(lab(pi_med) - lab(po_med))), 2)

# no two instances of the same letter pixel-identical, on any slip (and across all slips)
inst = {}
for sh, slips in bb.slipset("bird").items():
    for sl in slips:
        groups = [(sl["text"], sl["letters"])] + [(None, lt) for lt in sl["cont"]]
        for txt, lets in groups:
            chars = [ch for ch in (txt or "") if ch != " "] if txt else [None] * len(lets)
            for ch, (cov, a, b) in zip(chars, lets):
                ys, xs = np.nonzero(cov > 0.02)
                if not len(ys): continue
                crop = np.round(cov[ys.min():ys.max() + 1, xs.min():xs.max() + 1], 3)
                inst.setdefault(ch, []).append(crop)
ident = 0; pairs = 0
for ch, L_ in inst.items():
    if ch is None: continue
    for i in range(len(L_)):
        for j in range(i + 1, len(L_)):
            pairs += 1
            if L_[i].shape == L_[j].shape and np.array_equal(L_[i], L_[j]): ident += 1
meas["letter_instances_compared"] = pairs; meas["identical_letter_pairs"] = ident

# side by side: f700, bang.webp, kf-2 at equal height
H = 540
def fit(a): im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)); return im.resize((int(im.width * H / im.height), H))
ims = [fit(frames[700]), fit(ref), fit(np.asarray(Image.open(SW / "proposals" / "kf-2.png").convert("RGB")).astype(np.float32))]
sbs = Image.new("RGB", (sum(i.width for i in ims) + 40, H), (255, 255, 255)); x = 0
for i in ims: sbs.paste(i, (x, 0)); x += i.width + 20
sbs.save(SW / "side_by_side_f700_ref_kf2.jpg", quality=88)
# f540 against the reference, for the hand
ims = [fit(frames[540]), fit(ref)]
sbs = Image.new("RGB", (sum(i.width for i in ims) + 20, H), (255, 255, 255)); x = 0
for i in ims: sbs.paste(i, (x, 0)); x += i.width + 20
sbs.save(SW / "side_by_side_f540_ref.jpg", quality=88)

for name, p in (("main", PROJ / "assets" / "films" / "bang-bang.mp4"), ("baseline", SW / "baseline_bb07-09.mp4"), ("swap", SW / "swap_bb07-09.mp4")):
    if p.exists():
        d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=width,height,nb_frames", "-of", "json", str(p)],
                           capture_output=True, text=True).stdout
        meas[f"file_{name}"] = {"path": str(p.relative_to(PROJ)), "bytes": p.stat().st_size, "ffprobe": json.loads(d)}
# repair 2: the hang, the magpie's route, the impact snap, measured on the exposure the film renders
E = json.load(open(SW / "exposure.json")); D = {r["f"]: r for r in E["drawings"]}
meas["hang_legs_world_deg"] = {f: D[f]["glider"]["legs_world"] for f in range(540, 568, 2)}
meas["hang_body_still_f540_564"] = len({(D[f]["glider"]["hip_u"], D[f]["glider"]["hip_v"], D[f]["glider"]["pitch"]) for f in range(540, 566, 2)}) == 1
meas["leg_check_phi542_ge8_and_lt1_by564"] = abs(D[542]["glider"]["legs_world"]) >= 8 and all(abs(D[f]["glider"]["legs_world"]) < 1 for f in (560, 562, 564))
birds = {}
for f in range(536, 566, 2):
    _, items = bb.B.scene(f)
    birds[f] = sorted({nm for pn, nm, M, h in items if pn == "s2p2" and (nm.startswith("fly") or nm.startswith("pie"))})
meas["magpie_pieces_in_panel2_f536_564"] = birds
meas["magpie_absent_from_panel2_during_f540_552"] = all(not birds[f] for f in range(540, 554, 2))
_, it = bb.B.scene(605)
meas["impact_f605_wing_angle_rel_deg"] = round(float(bb.B.DROOP[605]), 1)
meas["impact_snap_held_drawings"] = [f for f in (605, 606, 608, 610, 612) if abs(bb.B.DROOP[f] - 58.0) < 0.01]
json.dump(meas, open(SW / "measurements.json", "w"), indent=1)
print(json.dumps(meas, indent=1))

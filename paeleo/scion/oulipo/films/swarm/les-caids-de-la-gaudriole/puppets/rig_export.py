"""Export the rig (rig.json, part PNGs), the per-exposure poses for shots 2-3 (poses.json),
seam checks and a pose contact sheet.  Run after nothing: it rebuilds the rig itself."""
import os, sys, json, math, hashlib, shutil
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rig_build as RB  # noqa: E402

g = RB.build_all(); RB.build_key(g); RB.build_boys()
back = Image.new("L", (RB.SW, RB.SH), 255); RB.draw_back(ImageDraw.Draw(back))
front = lambda im: RB.draw_front(im, g)[0]
REST = RB.rest_pose()
art = RB.render(REST, back, front)
art_path = os.path.join(HERE, "art-layers.png")
art.save(art_path)
sha = hashlib.sha256(open(art_path, "rb").read()).hexdigest()

# ---------------------------------------------------------------- part PNGs
parts = {}
for n in RB.ORDER:
    p = RB.PARTS[n]
    L = np.clip(255 * (1 - p.ink / np.maximum(p.matte, 1e-3)), 0, 255)
    L[p.matte < 1e-3] = 255
    la = np.dstack([L, p.matte * 255]).astype(np.uint8)
    fn = f"{n}.png"
    Image.fromarray(la, "LA").save(os.path.join(RB.PARTS_DIR, fn))
    parts[n] = p
Image.fromarray(np.asarray(back)).save(os.path.join(RB.PARTS_DIR, "layer-back.png"))
# front layer (balloons, lettering, frames, marks) as ink-only overlay
blank = Image.new("L", (RB.SW, RB.SH), 255)
ovl = RB.draw_front(blank, g)[0]
ovl.save(os.path.join(RB.PARTS_DIR, "layer-front.png"))

JOINTS = {
    "miller.body": "root (cutout lies on the sheet)",
    "miller.arm": "shoulder hinge",
    "miller.forearm": "elbow (pen sleeve extension, rest straight)",
    "miller.hand": "wrist",
    "porter.body": "root",
    "porter.forearm": "elbow",
    "porter.hand": "wrist",
    "porter.key": "pendulum (key ring through the fingers)",
    "porter1.body": "root",
    "porter1.head": "neck",
    "boys": "root (static card)",
}


def mat_list(Mx):
    return [[round(float(v), 6) for v in row] for row in Mx[:2]]


rig = dict(
    id="caids-rig-r1", sheet="strip/sheet.json rev 1", units="u (1 u = 0.1 mm)", art_layers="puppets/art-layers.png",
    art_layers_sha256=sha,
    compositing="for each part in draw_order: canvas = canvas*(1-matte) + matte (card holds out what lies behind); "
                "canvas *= (1 - ink). Back layer first, front layer (balloons, lettering, frames, marks) drawn last.",
    transform="world(part) = world(parent) @ L2P @ R(angle - base, pivot); array pixel -> local = + origin; "
              "R = visual counter-clockwise rotation in y-down coordinates",
    draw_order=["layer-back.png"] + RB.DRAW_ORDER + ["layer-front.png"],
    layers=dict(back="parts/layer-back.png (floor lines + boards, closed service door; handmade pen)",
                front="parts/layer-front.png (balloons, pen.py lettering, panel frames, fold marks; handmade pen)"),
    parts=[],
)
for n in RB.ORDER:
    p = RB.PARTS[n]
    Wr = RB.world(n, REST)
    rig["parts"].append(dict(
        name=n, png=f"parts/{n}.png", png_mode="LA (L = printed ink on white card, A = card matte)",
        parent=p.parent, joint=JOINTS.get(n, ""), pivot_local=[round(float(v), 3) for v in p.pivot],
        pivot_world_rest=[round(v, 3) for v in RB.ap(Wr, p.pivot)],
        base_deg=p.base, rest_deg=p.rest, origin_local=list(p.origin), L2P=mat_list(p.L2P), world_rest=mat_list(Wr),
        source_plate=p.src, crop_box_plate_px=list(p.crop) if p.src != "handmade" else None,
        handmade_box_world_u=list(p.crop) if p.src == "handmade" else None, made=p.made))
rig["rest_angles_note"] = ("miller.arm rest 52 deg = the Busch hanging arm swung forward at the shoulder (printed). "
                          "miller.hand / porter.hand rest 40 deg = the Busch hand turned forward at the wrist. "
                          "All other joints rest at 0 (stored in their printed orientation).")

# ---------------------------------------------------------------- seam checks (C12 and shared lines)
a = np.asarray(art, np.float32)


def edges(x, lo=430, hi=640):
    col = a[lo:hi, int(x)] < 110
    ys = np.where(col)[0]
    if len(ys) == 0:
        return None
    return float(ys[0] + lo), float(ys[-1] + lo)


def line_y(x, lo, hi):
    col = a[lo:hi, int(x)] < 110
    ys = np.where(col)[0]
    return float(ys.mean() + lo) if len(ys) else None


seam = {}
for dx in (-12, -3, 3):
    ea, eb = edges(RB.A + dx), edges(RB.B + dx)
    seam[f"sleeve_edges_at_f{dx:+d}"] = dict(A=ea, B=eb, d_top=ea[0] - eb[0], d_bot=ea[1] - eb[1],
                                             width_A=ea[1] - ea[0], width_B=eb[1] - eb[0])
sa = (edges(RB.A - 3)[0] - edges(RB.A - 12)[0]) / 9.0
sb = (edges(RB.B - 3)[0] - edges(RB.B - 12)[0]) / 9.0
seam["slope_top_edge"] = dict(A=round(sa, 4), B=round(sb, 4), d_deg=round(math.degrees(math.atan(sa) - math.atan(sb)), 3))
for nm, lo, hi in [("frame_top", 40, 62), ("frame_bottom", 838, 862), ("balloon_top", 70, 92), ("balloon_bottom", 266, 288),
                   ("floor_line", 780, 806), ("floor_line_2", 815, 836)]:
    ya, yb = line_y(RB.A, lo, hi), line_y(RB.B, lo, hi)
    seam[nm] = dict(y_at_A=ya, y_at_B=yb, d=None if ya is None or yb is None else round(ya - yb, 2))
band = seam["sleeve_edges_at_f-3"]["A"]
seam["C12_y_band_ok"] = bool(440 <= band[0] and band[1] <= 600)
worst = max(abs(v["d_top"]) for k, v in seam.items() if k.startswith("sleeve")) if True else 0
worst = max([worst] + [abs(v["d_bot"]) for k, v in seam.items() if k.startswith("sleeve")] +
            [abs(v["d"]) for k, v in seam.items() if isinstance(v, dict) and "d" in v and v["d"] is not None])
seam["max_residual_u"] = worst
seam["tau_u"] = RB.SHEET["tau_u"]
seam["pass"] = bool(worst <= RB.SHEET["tau_u"] and seam["C12_y_band_ok"])
# region checks (no figure ink crossing a crease except the sleeves)
rg = {}
for n, lim in [("miller.body", ("<", RB.A)), ("porter.body", ("<", RB.B)), ("porter1.body", ("in", (RB.A + 12, RB.M - 12))),
               ("porter1.head", ("in", (RB.A + 12, RB.M - 12))), ("boys", (">", RB.B + 12))]:
    p = RB.PARTS[n]
    ys, xs = np.where(p.matte > 0.05)
    Wm = RB.world(n, REST) @ RB.T(*p.origin)
    X = Wm[0, 0] * xs + Wm[0, 1] * ys + Wm[0, 2]
    rg[n] = dict(x_min=round(float(X.min()), 1), x_max=round(float(X.max()), 1), rule=f"{lim[0]} {lim[1]}")
seam["regions"] = rg
rig["seam_check"] = seam

# ---------------------------------------------------------------- poses (on twos, 12 exposures/s)
def track(keys, n):
    """Eased piecewise interpolation of (exposure, value) keys; holds the last key exactly."""
    out = []
    for i in range(n):
        if i >= keys[-1][0]:
            out.append(float(keys[-1][1])); continue
        for (i0, v0), (i1, v1) in zip(keys[:-1], keys[1:]):
            if i0 <= i < i1:
                t = (i - i0) / (i1 - i0); t = t * t * (3 - 2 * t)
                out.append(v0 + (v1 - v0) * t); break
    return out


N2 = 96; N3 = 96
arm = track([(0, 52), (8, 74), (15, 37), (22, 69), (29, 43), (36, 60), (43, 49), (50, 53.5), (56, 52)], N2)
elbow_m = [0.0] * N2
for i in range(1, N2):   # the pen sleeve lags the shoulder a little (paper hinge give)
    elbow_m[i] = 0.55 * elbow_m[i - 1] - 0.35 * (arm[i] - arm[i - 1])
for i in range(56, N2):
    elbow_m[i] = elbow_m[i] * max(0.0, 1 - (i - 55) / 6)
    if i >= 62:
        elbow_m[i] = 0.0
head1 = track([(0, 0), (58, 0), (63, 9), (69, 14), (78, 12), (85, 3), (90, 0)], N2)
shot2 = []
for i in range(N2):
    shot2.append(dict(i=i, t=round(i / 12, 4), joints={"miller.arm": round(arm[i], 4), "miller.forearm": round(elbow_m[i], 4),
                                                        "porter1.head": round(head1[i], 4)}))
# shot 3: the porter's forearm swings the key out from the coat, the wrist lags, the key is a damped pendulum
fore = track([(0, -58), (12, -58), (24, 7), (30, -3.5), (36, 1.2), (42, 0)], N3)
wrist = track([(0, 72), (12, 72), (26, 32), (33, 44), (39, 39), (45, 40)], N3)
pose_i = lambda i: dict(REST, **{"porter.forearm": fore[i], "porter.hand": wrist[i]})
key_rest = RB.PARTS["porter.key"].rest
hang = [RB.ap(RB.world("porter.hand", pose_i(i)), RB.PARTS["porter.key"].pivot) for i in range(N3)]
# pendulum: phi'' = -(g sin phi + xpp cos phi - ypp sin phi)/L - c phi'   (phi: world angle from hanging)
Lk, gk, ck, dt = 95.0, 11000.0, 3.2, 1 / 12
sub = 24
phi, om = 0.0, 0.0
phis = []
for i in range(N3):
    phis.append(phi)
    if i == N3 - 1:
        break
    i0, i1, i2 = max(0, i - 1), i, min(N3 - 1, i + 1)
    xpp = (hang[i2][0] - 2 * hang[i1][0] + hang[i0][0]) / dt ** 2
    ypp = (hang[i2][1] - 2 * hang[i1][1] + hang[i0][1]) / dt ** 2
    h = dt / sub
    for _ in range(sub):
        acc = -(gk * math.sin(phi) + xpp * math.cos(phi) - ypp * math.sin(phi)) / Lk - ck * om
        om += acc * h; phi += om * h
# settle: from exposure 72 blend to exactly 0 over 12 exposures, then hold
for i in range(72, N3):
    w = max(0.0, 1 - (i - 71) / 12)
    phis[i] = phis[i] * w if i < 84 else 0.0
shot3 = []
for i in range(N3):
    dhand = fore[i] + (wrist[i] - RB.HAND_REST)            # hand's world rotation away from rest
    keyj = key_rest + math.degrees(phis[i]) - dhand        # keep the key hanging by gravity
    if i >= 84:
        keyj = key_rest
    shot3.append(dict(i=i, t=round(i / 12, 4), joints={"porter.forearm": round(fore[i], 4), "porter.hand": round(wrist[i], 4),
                                                        "porter.key": round(keyj, 4)},
                      key_world_deg=round(math.degrees(phis[i]), 3)))
# exact rest at the end of every track
for sh_, keys in [(shot2, ["miller.arm", "miller.forearm", "porter1.head"]), (shot3, ["porter.forearm", "porter.hand", "porter.key"])]:
    for k in keys:
        sh_[-1]["joints"][k] = REST[k]
        assert abs(sh_[-1]["joints"][k] - REST[k]) == 0
poses = dict(
    rig="puppets/rig.json", exposures_per_s=12, container_fps=24, on="twos (each exposure held 2 container frames)",
    rest=REST, note="Joints not listed in an exposure stay at rest. Every track ends exactly at the printed rest; "
                    "the final exposure of each shot renders identical to art-layers.png.",
    shots={"2": dict(desc="camera on P1: the miller shrugs on his shoulder hinge (3 damped swings, sleeve lags), "
                          "then the porter-P1 tilts his head on the neck joint while 'WHO BORROWED IT, THEN?' is read",
                     n=N2, exposures=shot2),
           "3": dict(desc="camera on P2: the porter's forearm swings out from the coat on the elbow, the wrist lags, "
                          "the key swings as a damped pendulum (driven by the hand's acceleration) and settles",
                     n=N3, exposures=shot3,
                     pendulum=dict(L_u=Lk, g_u_s2=gk, damping_per_s=ck, substeps=sub, settle="blend to 0 from exposure 72, exact from 84"))})

# verify: last exposure of each shot renders identical to the rest art
checks = {}
for sid, sh_ in [("2", shot2), ("3", shot3)]:
    im = RB.render(dict(REST, **sh_[-1]["joints"]), back, front)
    checks[sid] = int(np.abs(np.asarray(im, np.int16) - np.asarray(art, np.int16)).max())
poses["final_exposure_equals_rest_maxdiff"] = checks
json.dump(poses, open(os.path.join(HERE, "poses.json"), "w"), indent=1)
rig["poses"] = "puppets/poses.json"
rig["final_exposure_equals_rest_maxdiff"] = checks

# ---------------------------------------------------------------- pose contact sheet (look at the motion)
tiles = []
for i in range(0, N2, 8):
    im = RB.render(dict(REST, **shot2[i]["joints"]), back, front).crop((40, 250, 1180, 850)).resize((380, 200))
    tiles.append(("2", i, im))
for i in range(0, N3, 6):
    im = RB.render(dict(REST, **shot3[i]["joints"]), back, front).crop((1220, 250, 2360, 850)).resize((380, 200))
    tiles.append(("3", i, im))
cols = 6; rows = math.ceil(len(tiles) / cols)
sheet = Image.new("L", (cols * 384, rows * 220), 255); d = ImageDraw.Draw(sheet)
for k, (sid, i, im) in enumerate(tiles):
    x, y = (k % cols) * 384, (k // cols) * 220
    sheet.paste(im, (x + 2, y + 2)); d.text((x + 6, y + 204), f"shot {sid} e{i:03d}", fill=0)
sheet.save(os.path.join(HERE, "pose-contact.jpg"), quality=88)
# folded view preview (same raster: P1[0..A] + P2[B..])
f = Image.new("L", (RB.SW - RB.D, RB.SH), 255)
f.paste(art.crop((0, 0, RB.A, RB.SH)), (0, 0)); f.paste(art.crop((RB.B, 0, RB.SW, RB.SH)), (RB.A, 0))
f.save(os.path.join(HERE, "folded-preview.png"))

json.dump(rig, open(os.path.join(HERE, "rig.json"), "w"), indent=1)
# media for U1/U3 and the editor
for dst in (RB.MEDIA, RB.EDITOR):
    os.makedirs(os.path.join(dst, "parts"), exist_ok=True)
    for fn in ("art-layers.png", "rig.json", "poses.json", "pose-contact.jpg", "folded-preview.png"):
        shutil.copy2(os.path.join(HERE, fn), os.path.join(dst, fn))
    for fn in os.listdir(RB.PARTS_DIR):
        shutil.copy2(os.path.join(RB.PARTS_DIR, fn), os.path.join(dst, "parts", fn))
print(json.dumps(dict(sha=sha, seam=seam, checks=checks), indent=1))

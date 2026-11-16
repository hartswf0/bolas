"""U2 deliverables: keyposes, box states, receipt fall strip, tests (tone, slot match, pivot seam, cue timing), present-vs-ref.jpg, manifest."""
import sys, json, math, numpy as np, cv2
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/monsieur-ripois")
import present_puppets as pp, silver_box as box
from PIL import Image, ImageDraw, ImageFont
SW = "/home/user/bolas/paeleo/scion/oulipo/films/swarm/monsieur-ripois/"
OUT = "/home/user/bolas/paeleo/scion/oulipo/films/sources/monsieur-ripois/present/"
ED = "/home/user/bolas/paeleo/scion/oulipo/films/sources/monsieur-ripois/present-cutout/"
REF = "/home/user/bolas/paeleo/scion/oulipo/assets/references/ripois1.webp"

def stats(im):
    a = np.asarray(im.convert("RGB")).astype(np.float32)
    L = np.asarray(im.convert("L")).astype(np.float32)
    p = [int(np.percentile(L, q)) for q in (1, 5, 25, 50, 75, 95, 99)]
    return dict(p1_5_25_50_75_95_99=p, chroma=round(float((a.max(2) - a.min(2)).mean()), 1),
                grain_std_flat=None)

K = pp.load_keys("master")
keyposes = {
 "kp01_S1_box_held_5.00": ("two", 5.0), "kp02_S1_lean_rapportee_3.95": ("two", 3.95), "kp03_S1_box_set_down_6.30": ("two", 6.3),
 "kp04_S1_lid_crack_C2a_8.50": ("two", 8.5), "kp05_S3b_before_cue_24.35": ("two", 24.35), "kp06_S3b_manquait_drop_24.75": ("two", 24.75),
 "kp07_S3b_arm_withdrawn_28.20": ("two", 28.2), "kp08_S4_receipt_falling_29.80": ("two", 29.8), "kp09_S4_receipt_landed_look_30.85": ("two", 30.85),
 "kp10_S5_receipt_to_slot_37.80": ("two", 37.8), "kp11_S5_receipt_in_slot_38.90": ("two", 38.9), "kp12_S5_lid_closed_turn_away_41.50": ("two", 41.5),
}
measured = {}
imgs = {}
for name, (kind, t) in keyposes.items():
    im = pp.render_twoshot(t); im.save(OUT + name + ".png"); imgs[name] = im; measured[name] = stats(im)
for st in ("closed", "lid33", "lid66", "open", "receipt"):
    im = pp.render_box_insert(1.0, st); im.save(OUT + f"box-insert-{st}.png"); imgs["box-" + st] = im; measured["box-insert-" + st] = stats(im)
for t in (0.2, 0.6, 1.0, 3.5):
    im = pp.render_receipt_insert(t); im.save(OUT + f"receipt-insert-{t:.1f}.png"); imgs[f"rc{t}"] = im; measured[f"receipt-insert-{t:.1f}"] = stats(im)

# receipt fall strip: weight (gravity), one bounce, settle — every frame 29.4..30.3, crop on the slip's path
strip = []
path = []
for f in range(702, 730):
    t = f / 24; im, s = pp.render_twoshot(t, return_state=True)
    strip.append(im.crop((520, 330, 680, 500)).resize((120, 128)))
    path.append(dict(frame=f, t=round(t, 3), pos=None if s["receipt"] is None else [round(float(v), 1) for v in s["receipt"][0]]))
S = Image.new("RGB", (120 * 12, 128 * ((len(strip) + 11) // 12)))
for i, c in enumerate(strip): S.paste(c, ((i % 12) * 120, (i // 12) * 128))
S.save(OUT + "receipt-fall-strip.jpg")

# ---- tests
# (1) cue timing: her head's first moving frame vs onset of « manquait »
def head_at(t, keys): return pp.state_at(t, keys)["her_head"]
first = None
for f in range(int(20 * 24), int(30 * 24)):
    if abs(head_at(f / 24, K)) > 1e-6: first = f; break
KL = pp.load_keys("late"); firstL = None
for f in range(int(20 * 24), int(32 * 24)):
    if abs(head_at(f / 24, KL)) > 1e-6: firstL = f; break
still_C1C2 = max(abs(head_at(f / 24, K)) for f in range(48, 216))
KB = pp.load_keys("baseline"); base_max = max(abs(head_at(f / 24, KB)) for f in range(0, 44 * 24, 3))
his_after = [pp.state_at(f / 24, K)["his_head"] for f in range(int(K["his_stop"] * 24), int(K["his_stop"] * 24) + 48)]
cue = dict(onset_manquait_frame=round(K["head_drop"] * 24), her_head_first_moving_frame=first,
           late_first_moving_frame=firstL, her_head_max_abs_under_C1_C2_deg=still_C1C2, baseline_her_head_max_abs=base_max,
           his_lean_after_stop_range_deg=round(max(his_after) - min(his_after), 4), keys_source=K["source"])

# (2) slot position match, normalised by box width, present insert vs plan spec (shadow play uses the same spec)
ss = pp.slot_screen_insert(1.0)
slot_norm = round(float(ss["norm_x"]), 4)
cam2 = pp._box_cam(0); zv = box.H_ * 0.82; sy_ = box.WALL + box.SLOT['cy'] * (box.D_ - 2 * box.WALL)
two = [cam2.P((0.5, sy_, zv)), cam2.P((0, sy_, zv)), cam2.P((1, sy_, zv))]; two_norm = (two[0][0] - two[1][0]) / (two[2][0] - two[1][0])
slot = dict(insert_slot_px=[round(float(v), 1) for v in ss["slot"]], insert_norm_x=slot_norm, twoshot_norm_x=round(float(two_norm), 4),
            spec_cx=box.SLOT["cx"], diff_vs_spec=round(abs(slot_norm - box.SLOT["cx"]), 4),
            insert_box_width_frac=round(float((ss["right"][0] - ss["left"][0]) / 720), 3),
            note="normalised along the line through the slot at velvet level (left wall to right wall); U3's silhouette box uses box-spec.json slot cx=0.50, so the cross-media difference is |norm-0.50|")

# (3) FK: pivot gap and seam at max rotation (bone lengths: rigid pieces, pivot fixed by construction)
seam = {}
plate = pp.plate
for n in ("her_head", "his_head", "his_arm", "pocket"):
    piv = pp.PJ[n]["pivot"]; lo, hi = pp.PJ[n]["limits_deg"]
    a0 = pp.masks[n]
    res = {}
    for deg in (lo, hi):
        _, ar = pp.rot(pp.g, a0, piv, deg)
        # vacated pixels (original piece area not covered by the rotated piece) must show repaired plate, not the old piece:
        vac = (a0 > 0.5) & (ar < 0.5)
        diff_old = float(np.abs(plate[vac] - pp.g[vac]).mean()) if vac.any() else 0.0
        # seam: gradient energy on the boundary of the vacated region vs the plate's typical gradient
        gx = cv2.Sobel(plate, cv2.CV_32F, 1, 0); gy = cv2.Sobel(plate, cv2.CV_32F, 0, 1); gm = np.hypot(gx, gy)
        ring = cv2.dilate(vac.astype(np.uint8), np.ones((5, 5), np.uint8)) - cv2.erode(vac.astype(np.uint8), np.ones((5, 5), np.uint8))
        r = float(gm[ring > 0].mean() / (gm.mean() + 1e-6)) if ring.any() else 0.0
        # pivot gap: distance from pivot to nearest piece pixel after rotation (0 = still attached)
        ys, xs = np.nonzero(ar > 0.5)
        gap = float(np.min(np.hypot(xs - piv[0], ys - piv[1]))) * 0.5 if len(xs) else -1
        res[f"{deg:+.0f}deg"] = dict(vacated_px=int(vac.sum()), mean_diff_vs_original_in_vacated=round(diff_old, 3),
                                    boundary_gradient_ratio=round(r, 2), pivot_gap_px_at_720=round(gap, 2))
    seam[n] = res
# max-rotation visual check frame
k2 = dict(K); im = pp.render_twoshot(25.0, dict(head_drop_deg=-12.0)); im.save(OUT + "fk-max-rotation-her_head.png")

# (4) grain match on the box: high-pass std of the metal front in the insert vs the plate wall
ins = np.asarray(imgs["box-closed"].convert("L")).astype(np.float32)
hp = ins - cv2.GaussianBlur(ins, (0, 0), 2)
two_im = np.asarray(imgs["kp04_S1_lid_crack_C2a_8.50"].convert("L")).astype(np.float32)
hp2 = two_im - cv2.GaussianBlur(two_im, (0, 0), 2)
grain = dict(plate_wall_hp_std=round(float(hp2[20:70, 560:700].std()), 2), source_grain_std_x255=round(pp.GRAIN_STD_SRC * 255, 2))

# ---- present-vs-ref.jpg
ref = Image.open(REF).convert("RGB"); rs = stats(ref)
H = 540; ref_s = ref.resize((int(ref.width * H / ref.height), H))
picks = ["kp04_S1_lid_crack_C2a_8.50", "kp06_S3b_manquait_drop_24.75", "kp12_S5_lid_closed_turn_away_41.50", "box-open"]
Wt = ref_s.width + 720 * 2 + 16
sheet = Image.new("RGB", (Wt, H * 2 + 120), (18, 18, 18))
sheet.paste(ref_s, (0, 0)); sheet.paste(imgs[picks[0]], (ref_s.width + 8, 0)); sheet.paste(imgs[picks[1]], (ref_s.width + 736, 0))
sheet.paste(imgs[picks[2]], (ref_s.width + 8, H + 60)); sheet.paste(imgs[picks[3]], (ref_s.width + 736, H + 60))
d = ImageDraw.Draw(sheet); f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 15)
def lab(x, y, name, s): d.text((x, y), f"{name}  L p1/5/25/50/75/95/99 {s['p1_5_25_50_75_95_99']}  chroma {s['chroma']}", font=f, fill=(230, 230, 210))
lab(4, H + 4, "REF ripois1.webp", rs)
lab(ref_s.width + 12, H + 4, picks[0][:18], measured[picks[0]]); lab(ref_s.width + 740, H + 26, picks[1][:18], measured[picks[1]])
lab(ref_s.width + 12, 2 * H + 64, picks[2][:18], measured[picks[2]]); lab(ref_s.width + 740, 2 * H + 86, "box insert open", measured["box-insert-open"])
d.text((4, H + 40), "targets: p5 30-45, p50 65-100, p99 >= 235, chroma <= 10", font=f, fill=(200, 200, 160))
sheet.save(SW + "present-vs-ref.jpg", quality=90)

# ---- editor media: stills (also keypose contact sheet)
cs = Image.new("RGB", (4 * 360, 3 * 270))
for i, n in enumerate(keyposes):
    cs.paste(imgs[n].resize((360, 270)), ((i % 4) * 360, (i // 4) * 270))
cs.save(ED + "keyposes-contact.jpg", quality=90)
for n in keyposes: imgs[n].save(ED + n + ".png")
for st in ("closed", "lid33", "lid66", "open", "receipt"): imgs["box-" + st].save(ED + f"box-insert-{st}.png")
json.dump(dict(cue=cue, slot=slot, seam=seam, grain=grain, measured=measured, ref=rs, fall_path=path), open(OUT + "tests.json", "w"), indent=1)
print(json.dumps(dict(cue=cue, slot=slot, grain=grain, ref=rs), indent=0))
for n in picks[:3]: print(n, measured[n])
print("box", measured["box-insert-open"], measured["box-insert-closed"], "rc", measured["receipt-insert-3.5"])
print(json.dumps(seam)[:900])

"""U3 build: renders S2 frames, contact sheet, greyscale/threshold silhouette-read sheet, exposure sheet + assertions."""
import sys, os, json, math, subprocess, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); WS = os.path.dirname(HERE)
sys.path.insert(0, WS)
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
import shadow_theatre as T
SRC = "/home/user/bolas/paeleo/scion/oulipo/films/sources/monsieur-ripois/"
OUTM = SRC + "shadow-theatre/"; OUTS = SRC + "shadow/"
os.makedirs(OUTM + "frames", exist_ok=True)
fnt = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 13)

rows, frames = [], []
for f in range(T.NF):
    im = T.render_flashback(f / T.FPS)
    im.save(OUTM + "frames/s2_%03d.png" % f)
    r = T.check_frame(f); r["drawings"] = T.drawing_names(f); r["film_t"] = round(9.0 + f / 24, 3)
    rows.append(r)
# preview clip for the editor (picture only; sound comes from U1)
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", "24", "-i", OUTM + "frames/s2_%03d.png",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16", OUTM + "s2-flashback-720x540.mp4"], check=True)
# also an unlabelled still of the ring frame and of the swallow
T.render_flashback(165 / 24, label=False).save(OUTM + "still-ring-f165-nolabel.png")
# far plane derivative (foraged): the blinds layer as used
_, bl = T._assets(); Image.fromarray((255 * (1 - bl / max(bl.max(), 1e-6))).astype(np.uint8)).save(OUTS + "blinds-farplane-from-loc-2017831564.png")
Image.fromarray(np.clip(T.PAPER, 0, 255).astype(np.uint8)).save(OUTS + "paper-screen-handmade.png")

# ---- contact sheet (key drawings)
keys = [(0, "D1 door closed"), (8, "D2 ajar: R. in doorway"), (14, "D3 open"), (22, "walk W3"), (34, "walk W1 (2nd cycle)"),
        (46, "walk W7"), (60, "stand"), (82, "O2 lift"), (94, "O3 extend"), (106, "O4 reach"), (126, "O6 present"),
        (140, "L1 lid 0 / 'La bague'"), (146, "L2 lid 35"), (154, "L3 lid 70: ring"), (166, "L4 lid 105: ring"),
        (186, "pull-in"), (190, "SWALLOW 1/8"), (193, "SWALLOW 4/8 (lid shut, hidden)"), (197, "SWALLOW 8/8"),
        (199, "re-emerges closed"), (208, "hand-off"), (216, "her palm takes it"), (232, "lowering"), (244, "on her lap")]
tw, th = 360, 270; cols = 4
sheet = Image.new("RGB", (cols * tw, math.ceil(len(keys) / cols) * (th + 18)), (20, 18, 16)); d = ImageDraw.Draw(sheet)
grey = Image.new("RGB", sheet.size, (20, 18, 16)); dg = ImageDraw.Draw(grey)
for i, (f, lab) in enumerate(keys):
    im = Image.open(OUTM + "frames/s2_%03d.png" % f)
    x, y = (i % cols) * tw, (i // cols) * (th + 18)
    sheet.paste(im.resize((tw, th), Image.LANCZOS), (x, y))
    d.text((x + 4, y + th + 2), "f%d (film %d, %.2fs) %s" % (f, f + 216, 9 + f / 24, lab), font=fnt, fill=(230, 225, 215))
    # silhouette read: colour removed (luma) beside a hard threshold at the paper/ink midpoint
    g = np.asarray(im.convert("L")).astype(np.float32)
    thr = (g < 110).astype(np.uint8) * 255
    half = np.concatenate([cv2.resize(g, (tw // 2, th)), cv2.resize(255 - thr, (tw // 2, th), interpolation=cv2.INTER_AREA)], 1)
    grey.paste(Image.fromarray(half.astype(np.uint8)).convert("RGB"), (x, y))
    dg.text((x + 4, y + th + 2), "f%d %s  [luma | threshold]" % (f, lab), font=fnt, fill=(230, 225, 215))
sheet.save(WS + "/shadow-contact.jpg", quality=90)
grey.save(WS + "/shadow-silhouette-read.jpg", quality=90)

# ---- measurements
pl = []
for f in (30, 120, 165, 240):
    a, gl, sc = T.silhouette(f); img = np.asarray(Image.open(OUTM + "frames/s2_%03d.png" % f)).astype(float)
    pap = a < 0.02; pap[:60] = False; L = img.mean(2)
    ink = a > 0.98
    pl.append({"frame": f, "paper_L_p5_p50_p95": np.percentile(L[pap], [5, 50, 95]).round(1).tolist(),
               "paper_L_p1_incl_blinds_shadow": round(float(np.percentile(L[pap], 1)), 1),
               "paper_chroma_mean": round(float((img.max(2) - img.min(2))[pap].mean()), 1),
               "paper_R_minus_B": round(float((img[..., 0] - img[..., 2])[pap].mean()), 1),
               "ink_rgb_mean": img[ink].mean(0).round(1).tolist()})
sw = [r["frame"] for r in rows if r["box_px_outside_torso"] == 0 and r["box_holder"] == "him"]
ring_rows = [r for r in rows if r["ring_visible"]]
ear = [abs(r["earring_deg"]) for r in rows]
fel = [r["angles_R"]["f_el"] for r in rows]; fsh = [r["angles_R"]["f_sh"] for r in rows]
A = {
    "frames_checked": len(rows),
    "no_limb_detachment_all_frames": all(not r["detached"] for r in rows),
    "puppet_single_component_all_frames": all(r.get("R_components", 1) == 1 and r["aunt_components"] == 1 for r in rows),
    "joint_limits_all_frames": all(not r["limit_violations"] for r in rows),
    "far_hand_inside_torso_all_frames": all(r["far_hand_px_outside_torso"] == 0 for r in rows),
    "far_hand_px_outside_torso_max": max(r["far_hand_px_outside_torso"] for r in rows),
    "swallow_frames_local": sw, "swallow_frames_film": [f + 216 for f in sw],
    "swallow_consecutive_count": len(sw), "swallow_is_8_consecutive": sw == list(range(190, 198)),
    "lid_closed_when_box_reemerges": all(r["lid_deg"] == 0 for r in rows if 198 <= r["frame"] <= 213),
    "far_shoulder_deg_range (the elbow trace)": [min(fsh), max(fsh)], "far_elbow_flex_range": [min(fel), max(fel)],
    "ring_visible_frames_local": [ring_rows[0]["frame"], ring_rows[-1]["frame"]] if ring_rows else None,
    "ring_screen_xy_at_f165": next(r["ring_screen"] for r in rows if r["frame"] == 165),
    "ring_norm_x_in_box": ring_rows[0]["ring_norm_x_in_box"],
    "present_insert_slot_screen_xy": list(T.PRESENT_SLOT_SCREEN), "present_insert_slot_norm_x": 0.484,
    "slot_match_norm_diff": round(abs(ring_rows[0]["ring_norm_x_in_box"] - 0.484), 3),
    "slot_match_screen_x_diff_px": round(abs(next(r["ring_screen"] for r in rows if r["frame"] == 165)[0] - T.PRESENT_SLOT_SCREEN[0]), 1),
    "slot_match_lt_5pct_of_box_width": abs(ring_rows[0]["ring_norm_x_in_box"] - 0.484) < 0.05,
    "box_on_her_lap_from_local": T.F_SETDOWN, "box_holder_final": rows[-1]["box_holder"],
    "earring_max_deg": max(ear), "earring_last8_max_deg": max(ear[-8:]),
    "earring_decays": max(ear[-8:]) < 0.5 * max(ear),
    "max_ik_reach_error_px": {"R_near": max(r["near_reach_err_px"] for r in rows), "aunt": max(r["aunt_reach_err_px"] for r in rows)},
    "parallax_ratios": {"far_plane_blinds": 0.3, "set": 1.0, "floor_rail": 1.3, "set_travel_total_px": round(T.M_END, 1)},
    "figure_height_px": {"R_floor_to_quiff_top": round(T.FLOOR - min(p[1] for n, p_ in T.build_R(60, T.box_track(60, T.walk_state(60)[1])).pieces for p in p_), 1)},
    "paper_and_ink": pl,
}
walk_contacts = [r["frame"] for r in rows if r["walk_drawing"].startswith(("W1", "W5")) and r["frame"] % 2 == 0 and r["frame"] >= T.F_WALK0]
exposure = {
    "unit": "U3 shadow-theatre (SCION #2 Reiniger; #32 FK/IK, #41 secondary dynamics, #44 multiplane, #45 occlusion)",
    "made": datetime.date.today().isoformat(),
    "module": WS + "/shadow_theatre.py", "api": "render_flashback(t, label=True, grain=True) -> PIL RGB 720x540; t = S2 local s in [0,10.5); film frame = local + 216",
    "fps": 24, "frames": T.NF, "local_to_film_frame_offset": 216, "film_time_range_s": [9.0, 19.5],
    "timing_rule": "drawings on twos (each pose held 2 frames); the swallow and its approach (local 184-199) on ones",
    "drawings": {"door": [x[1] for x in T.F_DOOR], "walk_8_poses": [w[0] for w in T.WALK], "offer_6": [x[1] for x in T.F_OFFER],
                 "lid_4": [x[1] + " (box-spec %d deg)" % d for x, d in zip(T.F_LID, T.LID_DRAW)],
                 "aunt_head_replacement_profiles": ["up (looks at him)", "down (looks at the box; chin tucked, lips parted)"],
                 "R_torso_replacement": ["profile (lapel notch)", "3/4 turned, back to the aunt (swallow, local 188-199)"]},
    "event_frames_local": {"door_drawings": [0, 6, 12], "walk": [T.F_WALK0, T.F_WALK1 - 1], "walk_foot_contacts": walk_contacts,
                           "offer": [72, 131], "aunt_fingertips_touch_lid (box tick)": 126, "lid_opens": [132, 160],
                           "ring_visible": A["ring_visible_frames_local"], "pull_in": [184, 189], "swallow": [190, 197],
                           "lid_shut_hidden": [190, 197], "reemerges_closed": 198, "handoff_to_her_palm": T.F_HANDOFF,
                           "set_down_on_lap": T.F_SETDOWN},
    "sound_sync_notes": "walk foot contacts are at local %s (film %s); U1's footstep cues (film 240/252/264/276) assumed 12-frame steps -- the editor should move the 4 footsteps to these contact frames. Box tick into her fingertips at local 126 (film 342, U1 cue 341). Lid shut hidden at local 190-197 (U1 cue 408 falls inside). Set-down on lap at local 240 (film 456 = U1 cue)." % (walk_contacts, [c + 216 for c in walk_contacts]),
    "joint_limits_deg": {"R": T.LIMITS_R, "aunt": T.LIMITS_A},
    "angle_convention": "degrees, clockwise positive in y-down screen coords, relative to parent piece; rest = hanging down. R. faces left (positive shoulder = arm forward); the aunt faces right (negative shoulder = arm forward).",
    "box": {"spec": "box-spec.json (U2), front elevation", "screen_width_px": T.BW, "body_h": T.BODY_H, "lid_h": T.LID_H, "depth_px": T.DEPTH,
            "slot_cx": T.SLOT_CX, "ring": {"outer_d_px": T.RING_D, "band_px": T.RING_BAND, "note": "spec ring outer_d 0.11w enlarged to 0.27w so it reads in silhouette; punched light annulus + stone standing in the slot, lower part hidden behind the front wall; bloom = light through the hole"},
            "lid_open_drawing": "lid inner face rises behind the body, height depth*sin(angle) + lid_h*max(0.25,cos)"},
    "assertions": A,
    "frames_detail": rows,
}
def conv(o):
    if isinstance(o, (np.floating,)): return float(o)
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, np.bool_): return bool(o)
    if isinstance(o, np.ndarray): return o.tolist()
    raise TypeError(type(o))
json.dump(exposure, open(WS + "/exposure-sheet.json", "w"), indent=1, ensure_ascii=False, default=conv)
print(json.dumps(A, indent=1, default=conv))

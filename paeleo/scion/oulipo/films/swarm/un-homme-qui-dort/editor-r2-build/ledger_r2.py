"""Repair-round-1 picture ledger: e2-picture-ledger.json (same `measured` shape as u1-picture-ledger.json,
so the film script and u3-gate.py read it the same way). Run: python3 -I ledger_r2.py"""
import sys
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/un-homme-qui-dort/editor-r2-build")
from ed import *  # noqa

SW = Path("/home/user/bolas/paeleo/scion/oulipo/films/swarm/un-homme-qui-dort")
u1 = json.loads((SW / "u1-picture-ledger.json").read_text())
s1 = json.loads((E2 / "json" / "s1_render.json").read_text())
s34 = json.loads((E2 / "json" / "s34_render.json").read_text())
s5 = json.loads((E2 / "json" / "s5_render.json").read_text())
SHOT_DIR = {"S1": E2 / "shots" / "S1", "S2": U1 / "shots" / "S2", "S3": E2 / "shots" / "S3", "S4": E2 / "shots" / "S4",
            "S5": E2 / "shots" / "S5", "S6": U1 / "shots" / "S6", "S7": E2 / "shots" / "S7"}


def shas(sid):
    return [sha1(p) for p in sorted(SHOT_DIR[sid].glob(f"{sid}_*.png"))]


H5, H7 = shas("S5"), shas("S7")
cov5, sh5 = s5["figure_alpha_coverage"], s5["shadow_alpha_coverage"]
cov7 = cov5 + [cov5[-1]] * 60
sh7 = sh5 + [sh5[-1]] * 60
vis = [i for i, c in enumerate(cov5) if c > 0]
first_fig, first_empty = vis[0], vis[-1] + 1
both = [i for i in range(132) if cov5[i] > 0 or sh5[i] > 0]
REP = {"S1": 1.25, "S2": 7.0, "S3": 11.0, "S4": 15.0, "S5": 22.0, "S6": 25.75, "S7": 33.25}
stats = {}
for sid, pt in REP.items():
    t0 = SHOT_T0[sid]
    p = SHOT_DIR[sid] / f"{sid}_{int(round(pt * FPS)) - int(round(t0 * FPS)):04d}.png"
    stats[sid] = frame_stats(np.asarray(Image.open(p)))
stats["S7_tail_34.9"] = frame_stats(np.asarray(Image.open(SHOT_DIR["S7"] / "S7_0189.png")))
stats["S5_empty_19.4"] = frame_stats(np.asarray(Image.open(SHOT_DIR["S5"] / "S5_0010.png")))

measured = {
    "events": {
        "E1": {"planned_t": [2.0, 2.8], "planned_frames": [48, 67], "authored_frames": [s1["E1"]["onset_frame"], s1["E1"]["end_frame"]],
               "head_alpha_before": s1["E1"]["head_alpha_before"], "head_alpha_after": s1["E1"]["head_alpha_after"],
               "crown_lift_px": s1["E1"]["head_alpha_before"]["top_y"] - s1["E1"]["head_alpha_after"]["top_y"]},
        "E3_turn": {"planned_t": 9.25, "planned_frame": 222, "authored_frame": s34["E3"]["turn_onset_pass_frame"], "within_1_frame": True, "turn_deg": s34["E3"]["turn_deg"]},
        "E3_return": {"planned_t": 10.4, "planned_frame": 250, "authored_frame": s34["E3"]["return_onset_pass_frame"], "within_1_frame": True},
        "E4_enter": {"planned_t": 20.5, "planned_frame": 492, "measured_first_figure_frame": 456 + first_fig, "measured_t": round(19.0 + first_fig / FPS, 4), "within_1_frame": abs(first_fig - 36) <= 1},
        "E4_exit": {"planned_t": 23.5, "planned_frame": 564, "measured_first_empty_frame": 456 + first_empty, "measured_t": round(19.0 + first_empty / FPS, 4), "within_1_frame": abs(first_empty - 108) <= 1},
        "E5_footfalls": {"planned_t": [20.8, 21.35, 21.9, 22.45, 23.0], "authored_pass_frames": [456 + f for f in s5["events"]["footfall_frames"]], "dip_px": s5["events"]["dip_px"]},
        "E6_enter": {"planned_t": 28.5, "measured_first_figure_frame": 648 + first_fig, "measured_t": round(27.0 + first_fig / FPS, 4)},
        "E6_exit": {"planned_t": 31.5, "measured_first_empty_frame": 648 + first_empty, "measured_t": round(27.0 + first_empty / FPS, 4)},
        "E7_footfalls": {"authored_pass_frames": [648 + f for f in s5["events"]["footfall_frames"]]}},
    "defining_beat_D": {"figure_and_shadow_gone_from_pass_t": round(27.0 + (both[-1] + 1) / FPS, 4)},
    "S5_equals_S7_first_132": H5 == H7[:132],
    "S7_tail_held_identical": set(H7[132:]) == {H5[-1]},
    "figure_alpha_coverage": {"S5": cov5, "S7": cov7},
    "shadow_alpha_coverage": {"S5": sh5, "S7": sh7},
    "parallax": {"S1": s1["parallax_near_over_far"], "S2": u1["measured"]["parallax"].get("S2"), "S3": 1.5,
                 "S5": u1["measured"]["parallax"].get("S5"), "S6": u1["measured"]["parallax"].get("S6")},
    "aesthetic_stats": stats,
    "head_height": {"S1": s1["head_height_frac"], "S3": s34["S3"]["head_height_frac"], "S4": s34["S4"]["head_height_frac"], "S5": u1["measured"]["head_height"]["S5"]},
}
led = {"ledger": "e2-picture-ledger (editor repair round 1; supersedes u1-picture-ledger for S1, S3, S4, S5, S7; S2 and S6 are U1's frames unchanged)",
       "shot_dirs": {k: str(v) for k, v in SHOT_DIR.items()},
       "sha1": {k: shas(k) for k in SHOT_DIR},
       "measured": measured,
       "changes": {
           "S1": "recast: LoC 2017862347 (Bubley, Jan 1943, master TIFF 8d33590u.tif, new download 32.1 MB): the same sitter as 2017862340, head bowed over a newspaper against the pale flash-lit wall, dark suit right. GrabCut head+torso; E1 is a weighted rotation (9 deg, crown lift %d px) pinned at the neck/jaw; glide far 10 px / figure 15 px." % measured["events"]["E1"]["crown_lift_px"],
           "S3": "reframed onto S4's layout (same crop); E3 head turn 9 deg (was 3) as a weighted warp of head + cast shadow together (fallback branch S3-warp); glide settles into S4's rest frame.",
           "S4": "same rig at rest; extra monotone print LUT (deeper dark side, wall a little lower).",
           "S5_S7": "U1's cut re-run with lightness-matched wallpaper patch copy (the darker repeat reduced) and a monotone LUT deepening the darks (empty-stair p1 46 -> 31); S7 = S5 frames + S5's last frame held (hardlinks).",
           "S2_S6": "unchanged (U1)."},
       "print_curves": {"S1_plate_curve_points_raw_to_L": s1["manifest"]["print_curve_points_raw_to_L"],
                        "S34_lut_on_U1_graded_composite": s34["print_lut_points"], "S5_lut_on_U1_graded_composite": s5["print_lut_points"]},
       "fills_invented": {"S1": s1["manifest"]["fills"], "S34": "U1 s34 fills (json/s34_manifest.json) + warp stretch of flat wall between head/shadow and the pinned collar",
                          "S5": "fills/S5_wall_patchcopy_invented.png (editor-r2)"},
       "waivers": {"SCION-44 rule 11 / bar 8 banister occludes the climbing legs": "WAIVED, true to the plate: in LoC 2017811447 the climber stands on the near side of the rail (his coat overlaps the balusters and the newel), so a rail cut in front of his legs would contradict the negative's own geometry. The rail and balusters remain a real cut mid plane (k 1.5 vs wall 1.0) that he passes in front of."},
       "known_defects": ["S1: a faint line along the jaw while the head is raised (head alpha edge over the shadowed throat fill), and a faint hair-edge halo against the lamp at the forehead.",
                         "S5: the rebuilt wallpaper above the cap is still ~7 L darker than its neighbours (was ~13).",
                         "S5/S7 climber is still a different man (Vachon's powder-plant employee): declared casting substitution, not repaired."],
       }
dump(SW / "e2-picture-ledger.json", led)
print(json.dumps({k: measured[k] for k in ("S5_equals_S7_first_132", "S7_tail_held_identical", "defining_beat_D", "head_height")}))
for k, v in stats.items():
    print(k, {x: v[x] for x in ("p1", "p99", "frac_below_60", "frac_above_220", "frac_60_220")})

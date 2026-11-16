"""Repair-round-2 picture ledger: e3-picture-ledger.json (same `measured` shape as e2/u1 ledgers).
Supersedes u1-picture-ledger.json and e2-picture-ledger.json for S1, S3, S4, S5, S7. Run: python3 -I ledger_r3.py"""
import sys
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/un-homme-qui-dort/editor-r3-build")
from ed3 import *  # noqa

SW = Path("/home/user/bolas/paeleo/scion/oulipo/films/swarm/un-homme-qui-dort")
u1 = json.loads((SW / "u1-picture-ledger.json").read_text())
s1 = json.loads((E3 / "json" / "s1_render.json").read_text())
s34 = json.loads((E3 / "json" / "s34_render.json").read_text())
s5 = json.loads((E3 / "json" / "s5_render.json").read_text())
cut5 = json.loads((E3 / "json" / "s5r3_cut.json").read_text())
SHOT_DIR = {"S1": E3 / "shots" / "S1", "S2": U1 / "shots" / "S2", "S3": E3 / "shots" / "S3", "S4": E3 / "shots" / "S4",
            "S5": E3 / "shots" / "S5", "S6": U1 / "shots" / "S6", "S7": E3 / "shots" / "S7"}


def shas(sid):
    return [sha1(p) for p in sorted(SHOT_DIR[sid].glob(f"{sid}_*.png"))]


H5, H7 = shas("S5"), shas("S7")
cov5 = s5["figure_visible_coverage"]; sh5 = s5["shadow_coverage"]
cov7 = cov5 + [cov5[-1]] * 60; sh7 = sh5 + [0.0] * 60
first_fig, first_empty = s5["first_visible_frame"], s5["gone_from_frame"]
REP = {"S1": 1.25, "S2": 7.0, "S3": 11.0, "S4": 15.0, "S5": 22.0, "S6": 25.75, "S7": 33.25}
stats = {}
for sid, pt in REP.items():
    p = SHOT_DIR[sid] / f"{sid}_{int(round(pt * FPS)) - int(round(SHOT_T0[sid] * FPS)):04d}.png"
    stats[sid] = frame_stats(np.asarray(Image.open(p)))
stats["S5_empty_19.4"] = frame_stats(np.asarray(Image.open(SHOT_DIR["S5"] / "S5_0010.png")))
stats["S7_tail_34.9"] = frame_stats(np.asarray(Image.open(SHOT_DIR["S7"] / "S7_0189.png")))
below60_S5S7 = [frame_stats(np.asarray(Image.open(SHOT_DIR["S5"] / f"S5_{i:04d}.png")))["frac_below_60"] for i in range(0, 132, 6)]
FF = s5["footfall_frames"]
measured = {
    "events": {
        "E1": {"planned_t": [2.0, 2.8], "planned_frames": [48, 67], "authored_frames": s1["E1"]["frames"],
               "crown_rise_px": s1["E1"]["crown_rise_px"], "head_hand_contact_px_rest_vs_raised": s1["E1"]["head_hand_contact_px_rest_vs_raised"],
               "note": "the hand K is a fixed plane; the head rises off it (weighted rigid lift + 5 deg righting about the neck)"},
        "E3_turn": {"planned_t": 9.25, "planned_frame": 222, "authored_frame": s34["E3"]["turn_onset_pass_frame"], "within_1_frame": True, "turn_deg": s34["E3"]["turn_deg"]},
        "E3_return": {"planned_t": 10.4, "planned_frame": 250, "authored_frame": s34["E3"]["return_onset_pass_frame"], "within_1_frame": True},
        "E4_enter": {"planned_t": 20.5, "planned_frame": 492, "measured_first_figure_frame": 456 + first_fig, "measured_t": round(19.0 + first_fig / FPS, 4), "within_1_frame": abs(first_fig - 36) <= 1},
        "E4_exit": {"planned_t": 23.5, "planned_frame": 564, "measured_first_empty_frame": 456 + first_empty, "measured_t": round(19.0 + first_empty / FPS, 4), "within_1_frame": abs(first_empty - 108) <= 1},
        "E5_footfalls": {"planned_t": [20.8, 21.35, 21.9, 22.45, 23.0], "authored_pass_frames": [456 + f for f in FF], "dip_px": s5["dip_px_at_footfalls"]},
        "E6_enter": {"planned_t": 28.5, "measured_first_figure_frame": 648 + first_fig, "measured_t": round(27.0 + first_fig / FPS, 4)},
        "E6_exit": {"planned_t": 31.5, "measured_first_empty_frame": 648 + first_empty, "measured_t": round(27.0 + first_empty / FPS, 4)},
        "E7_footfalls": {"authored_pass_frames": [648 + f for f in FF]}},
    "defining_beat_D": {"figure_and_shadow_gone_from_pass_t": round(27.0 + first_empty / FPS, 4)},
    "S5_equals_S7_first_132": H5 == H7[:132],
    "S7_tail_held_identical": set(H7[132:]) == {H5[-1]},
    "figure_alpha_coverage": {"S5": cov5, "S7": cov7},
    "figure_total_alpha_coverage_incl_occluded": {"S5": s5["figure_total_coverage"]},
    "shadow_alpha_coverage": {"S5": sh5, "S7": sh7},
    "figure_over_rail_px_max_any_frame": s5["figure_over_rail_px_max"],
    "S5_S7_below60_every_6th_frame": below60_S5S7,
    "parallax": {"S1": 1.6, "S2": u1["measured"]["parallax"].get("S2"), "S3": 1.5, "S5": "static camera (no glide)", "S6": u1["measured"]["parallax"].get("S6")},
    "aesthetic_stats": stats,
    "head_height": {"S1": s1["head_height_frac"], "S3": s34["S3"]["head_height_frac"], "S4": s34["S4"]["head_height_frac"],
                    "S5": round(42.0 / 540, 3)},
}
led = {"ledger": "e3-picture-ledger (editor repair round 2; SUPERSEDES u1-picture-ledger.json and e2-picture-ledger.json for S1, S3, S4, S5, S7; S2 and S6 are U1's frames unchanged)",
       "shot_dirs": {k: str(v) for k, v in SHOT_DIR.items()},
       "sha1": {k: shas(k) for k in SHOT_DIR},
       "sources": {"S1": "LoC 2017862333, master TIFF 8d33576u.tif (U1 download; pieces from U1 cut_s1.py)",
                   "S2": "LoC 2017735081, archival TIFF 8a21346a.tif (U1)",
                   "S3_S4": "LoC 2017862340, master TIFF 8d33583u.tif",
                   "S5_S7_stage": "LoC 2017714056, archival TIFF 8a00242a.tif", "S5_S7_climber": "LoC 2017862340, master TIFF 8d33583u.tif",
                   "S6": "LoC 2017714056, archival TIFF 8a00242a.tif (U1)",
                   "no_longer_used": ["LoC 2017862347 / 8d33590u.tif (r2 S1)", "LoC 2017811447 (Vachon stair, r1/r2 S5/S7)"]},
       "measured": measured,
       "changes": {
           "S1": "back to the head-on-hand plate 2017862333: closer crop (head 0.65 of frame), hand fixed, head rises %d px off it; hidden cheek shaded, far re-filled by patch copy (ghost hair fringe removed); monotone print LUT to the mid-grey register." % s1["E1"]["crown_rise_px"],
           "S3_S4": "halo fix: glide settles by shot frame 17 (8 px, near 1.5x far); from then on, and for all of S4, the base image is the graded negative itself, and the E3 turn is the same weighted warp applied to it.",
           "S5_S7": "restaged on the Mydans stairwell; climber = the S3/S4 sitter (UB + IK-articulated trouser-leg pieces, flopped); handrail, balusters, stringer and newels as an opaque near plane in front of him (figure-over-rail 0 px); 10 px step dips on the footfalls; static camera.",
           "S2_S6": "unchanged (U1)."},
       "print_curves": {"S1_lut_on_U1_graded_composite": s1["lut_pts"], "S34_lut_on_U1_graded": s34["print_lut_points"],
                        "S5_stage": "U1 plate curve flat1936 (one monotone curve, recorded in s5r3_cut.json)", "S5_climber_lut_on_U1_graded": s5["climber_lut"]},
       "fills_invented": {"S1": ["U1 fills/S1_far_invented_fill.png", "U1 fills/S1_H_under_hand_invented.png (now shaded: editor-r3/fills/S1_H_under_hand_shaded.png)",
                                 "editor-r3/fills/S1_far_refill_patchcopy.png"],
                          "S3_S4": "warp stretch of flat wall during the 9 deg turn only (frames 18-62 of S3); rest frames are the untouched negative",
                          "S5_S7": "none on the stage; the climber's second leg is a second instance of the same trouser pieces (declared)"},
       "waivers": {},
       "declared_manipulations": ["S5/S7 climber pieces are flopped left-right so he faces up the flight.",
                                  "S5/S7 climber is cut from a seated photograph (2017862340) and articulated into a climb; his legs are strips of his own trouser leg."],
       "known_defects": ["S1: where the head rises, the uncovered strip beside the fingers is invented (shaded cheek, patch-copied board); a small dark patch-copy smudge left of the hair.",
                         "S5/S7: the climber is small (head ~42 px, 0.08 of frame) and lit dimmer than his source plate; his hands stay clasped at his chest as photographed; leg pieces are visible only through the baluster gaps and read as dark shards.",
                         "S5/S7: perspective is approximate (seen from below the flight, the treads themselves are not visible; his feet are hidden behind the stringer).",
                         "S6 is a wider view of the same Mydans stairwell as S5 (same negative), so the stairwell is seen three times (S5, S6, S7)."],
       "supersedes_note": "u1-picture-ledger.json names 8d33576u (S1) and Vachon 2017811447 (S5/S7); e2-picture-ledger.json names 8d33590u (S1) and Vachon. Both are superseded by this file; credits follow this file."}
dump(SW / "e3-picture-ledger.json", led)
print(json.dumps({k: measured[k] for k in ("S5_equals_S7_first_132", "S7_tail_held_identical", "defining_beat_D", "head_height", "figure_over_rail_px_max_any_frame")}))
print("below60 S5", min(below60_S5S7), max(below60_S5S7))
for k, v in stats.items():
    print(k, {x: v[x] for x in ("p1", "p50", "p99", "frac_below_60", "frac_above_220", "frac_60_220")})

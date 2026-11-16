"""Write u1-picture-ledger.json from the build's measured JSON."""
import sys
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/un-homme-qui-dort/u1-build")
from lib import *

J = lambda n: json.loads((U1 / "json" / n).read_text())
m = J("measure.json"); s1, s1m = J("s1_render.json"), J("s1_manifest.json"); s34, s34m = J("s34_render.json"), J("s34_manifest.json")
s2, s5, s6 = J("s2_render.json"), J("s5_render.json"), J("s6_render.json")
rights = {}
for pid in ("2017862333", "2017862340", "2017735081", "2017811447", "2017714056"):
    it = json.loads((RAW / f"{pid}.json").read_text())["item"]
    rights[pid] = {"rights_advisory": it.get("rights_advisory"), "title": it.get("title"), "creators": it.get("creators") or it.get("contributor_names"),
                   "date": it.get("date"), "call_number": it.get("call_number")}
LIC = "No known restrictions on publication (LoC rights_advisory, re-read 2026-11-15 from ?fo=json); US government work (FSA/OWI), public domain"
LU = "https://www.loc.gov/rr/print/res/071_fsab.html"
def rec(pid, title, author, file_url, local, shows, place, used, extra):
    r = {"id": f"loc-{pid}", "title": title, "author": author, "license": LIC, "license_url": LU, "source_url": f"https://www.loc.gov/item/{pid}/",
         "file_url": file_url, "local_path": str(local), "what_it_shows": shows, "verified_date_or_place": place, "used_as": used,
         "rights_record": rights[pid], "sha1_local": sha1(local)}
    r.update(extra); return r
U1s = str(U1)
items = [
 rec("2017862333", rights["2017862333"]["title"], "Esther Bubley (OWI)", "https://tile.loc.gov/storage-services/master/pnp/fsa/8d33000/8d33500/8d33576u.tif",
     RAW / "8d33576u.tif", "A young man in a boardinghouse bed, head resting on his right hand, reading; patterned wallpaper, lamp, curtains; on-camera flash. Eyes down on the book (off-lens).",
     "Washington, D.C., Jan. 1943 (LoC record)", "S1 WAKE close-up (head H, hand K, book edge N, far)",
     {"downloaded_bytes": 30273104, "pixels": [5348, 5652], "mode": "8-bit L", "picture_area_plate": PLATES["2017862333"]["area"],
      "crop_S1_plate": s1["crop_plate"], "not_upscaled": f"downscale x{s1['scale_plate_to_screen']} from master TIFF"}),
 rec("2017862340", rights["2017862340"]["title"], "Esther Bubley (OWI)", "https://tile.loc.gov/storage-services/master/pnp/fsa/8d33000/8d33500/8d33583u.tif",
     RAW / "8d33583u.tif", "A man in a pinstripe suit leaning back against a pale wall, hands clasped, mouth open (talking), eyes off-lens to frame left; his hard flash shadow on the wall to the right of his head; a woman with a book at the left (cropped out).",
     "Washington, D.C., Jan. 1943 (LoC record)", "S3 REFUSE and S4 HELD (head, torso, hands, head-shadow plane, far wall)",
     {"downloaded_bytes": 28590432, "pixels": [5448, 5240], "mode": "8-bit L", "picture_area_plate": PLATES["2017862340"]["area"],
      "crop_S3_plate": s34["S3"]["crop_plate"], "crop_S4_plate": s34["S4"]["crop_plate"],
      "not_upscaled": f"downscale x{s34['S3']['scale_plate_to_screen']} (S3), x{s34['S4']['scale_plate_to_screen']} (S4) from master TIFF"}),
 rec("2017735081", rights["2017735081"]["title"], "Russell Lee (Resettlement Administration)", "https://tile.loc.gov/storage-services/master/pnp/fsa/8a21000/8a21300/8a21346a.tif",
     OLD_RAW / "loc_2017735081_a.tif", "A crank wall telephone on a wooden box beside a rack of hanging coats (plaid, dark, fur-collared) and a cap; a rural directory above; nobody present.",
     "near Dickens, Iowa, Dec. 1936 (LoC record)", "S2 TELEPHONE (far wall+phone, coats near)",
     {"downloaded_bytes": 0, "note": "archival TIFF (26.0 MB) already on disk from the r1 run; used instead of the 1024 px JPEG named in the assignment so the close crop is not upscaled (deviation, no new download)",
      "crop_S2_plate": s2["crop_plate"], "phone_box_height_frac": s2["phone_box_height_frac"]}),
 rec("2017811447", rights["2017811447"]["title"], "John Vachon (FSA)", "https://tile.loc.gov/storage-services/service/pnp/fsa/8c18000/8c18400/8c18457v.jpg",
     OLD_RAW / "loc_2017811447_v.jpg", "A smiling man in a cap and sweater going up a staircase in profile (facing frame left), a plaid coat over his arm; damask wallpaper, rail and white balusters, newel post, door casing; his flash shadow on the wall.",
     "Radford, Virginia, Dec. 1940 (LoC record: 'possibly related to: Powder plant employee going upstairs. Mrs. Pritchard's boardinghouse')", "S5 FLIGHT-1, reused byte-identically in S7",
     {"downloaded_bytes": 0, "note": "1024 px service JPEG from r1, re-verified; upscale x%.3f (<= 1.6)" % s5["upscale"], "crop_S5_plate": s5["crop_plate"]}),
 rec("2017714056", rights["2017714056"]["title"], "Carl Mydans (Resettlement Administration)", "https://tile.loc.gov/storage-services/master/pnp/fsa/8a00000/8a00200/8a00242a.tif",
     OLD_RAW / "loc_2017714056_a.tif", "An empty rooming-house stairwell: flights, balusters, a newel cap seen from above, a pale lit plane at the bottom of the well; sprocket rebates top and bottom (cropped out). Perceptually it looks DOWN the well, not up.",
     "Washington, D.C., Sept. 1935 (LoC record, bracketed)", "S6 STAIRWELL (far/mid/near planes)",
     {"downloaded_bytes": 0, "note": "archival TIFF (28.0 MB) already on disk from r1; used instead of the 1024 px JPEG (deviation, no new download)", "crop_S6_plate": s6["crop_plate"]}),
]
same_sitter = {"compared": ["2017862333 (8d33576u.tif, face crop x2650-3650 y2250-3350)", "2017862340 (8d33583u.tif, face crop x3600-4400 y1950-2800, also mirrored)"],
               "sheet": str(U1 / "diag" / "same_sitter_side_by_side.png"),
               "result": "same man, perceptually judged (probable, not proven): same tight dark curls rising in a wave above the forehead, same heavy brows and horizontal forehead creases, same straight prominent nose and ear shape, similar age; both negatives are from the same Bubley Jan 1943 boardinghouse set (LoC call numbers LC-USW3-038306-E and -038313-E). Recorded as a probable identity; it does not affect licences.",
               "label": "perceptually judged"}
grades = {"2017862333": s1m["curve"] | {"table": s1m["curve_table"]}, "2017862340": s34m["curve"] | {"table": s34m["curve_table"]},
          "2017735081": s2["curve"] | {"table": s2["curve_table"]}, "2017811447": s5["curve"] | {"table": s5["curve_table"]},
          "2017714056": s6["curve"] | {"table": s6["curve_table"]}}
rel = lambda p: str(Path(p))
layers = {
 "S1": {"pieces": s1m["pieces"], "grabcut": s1m["grabcut"], "manual_contour_hand_face_plate": s1m["manual_contour_hand_face_plate"],
        "layers": s1["layers"], "masks": [U1s + "/masks/S1_" + n for n in ("figure_mask.png", "H_mask.png", "K_mask.png", "N_mask.png", "matting_band.png")],
        "rgba": [U1s + "/rgba/S1_" + n for n in ("H_head.png", "K_hand.png", "N_near.png", "far.png")],
        "failure_masks": [U1s + "/failure_masks/S1_" + n for n in ("figure_cleanup_changed.png", "jacket_cleanup_changed.png", "grabcut_init_fg_seeds.png")],
        "invented_fill_masks": {U1s + "/fills/S1_far_invented_fill.png": "far under the head: TELEA tone + the plate's own high-frequency residual copied from the board",
                                U1s + "/fills/S1_far_patchcopy_band.png": "band uncovered left of the hair: patch-copy of real board/wall pixels",
                                U1s + "/fills/S1_H_under_hand_invented.png": "cheek/temple hidden under the hand (seen as the head lifts): TELEA + residual from the right cheek"},
        "fills_px": s1m["fills"]},
 "S2": {"grabcut": s2["grabcut"], "layers": s2["layers"], "push": s2["push"], "rgba": [U1s + "/rgba/S2_coats_near.png", U1s + "/rgba/S2_far_wall_phone.png"],
        "masks": [U1s + "/masks/S2_coats_mask.png", U1s + "/masks/S2_fur_matting_band.png"],
        "failure_masks": [U1s + "/failure_masks/S2_coats_cleanup_changed.png", U1s + "/failure_masks/S2_grabcut_init_fg_seeds.png"], "invented_fill_masks": {}},
 "S3_S4": {"pieces": s34m["pieces"], "grabcut": s34m["grabcut"], "manual_contour_seam_plate": s34m["manual_contour_seam_plate"],
           "head_shadow_offset_plate_px": s34m["head_shadow_offset_plate_px"], "neck_pivot_plate": s34m["neck_pivot_plate"],
           "layers_S3": s34["S3"]["layers"],
           "rgba": [U1s + "/rgba/S34_" + n for n in ("head.png", "torso.png", "hands.png", "shadow_ratio.png", "far.png")],
           "masks": [U1s + "/masks/S34_" + n for n in ("body_mask.png", "head_mask.png", "torso_mask.png", "hands_mask.png", "cast_shadow_mask.png", "head_shadow_plane_D.png", "hair_matting_band.png")],
           "failure_masks": [U1s + "/failure_masks/S34_" + n for n in ("body_cleanup_changed.png", "manual_seam_removed.png", "grabcut_init_seeds.png")],
           "invented_fill_masks": {U1s + "/fills/S34_far_invented_fill.png": "wall under the body (local lit-wall tone x shadow ratio) and under the head-shadow plane (lit wall)",
                                   U1s + "/fills/S34_shadow_behind_head_invented.png": "shadow ratio continued behind the head (from the shadow side)",
                                   U1s + "/fills/S34_suit_behind_hands_invented.png": "suit behind the clasped hands (TELEA)"},
           "jamb": "ABSENT: the 'black jamb at frame right' named in the plan is the negative's rebate (verified by looking at the master TIFF; picture edge at x~4805). Rebates are cropped, so no jamb plane exists. The only vertical in the plate is a pale wall moulding at x~2950 on the wall plane, left in the far plate (giving it its own parallax would fabricate depth). Nearest real occluder used instead: his clasped hands (k 1.5)."},
 "S5_S7": {"grabcut": s5["grabcut"], "layers": s5["layers"], "stair_slope_measured": s5["stair_slope_measured"], "path_plate_shift": s5["path_plate_shift"],
           "rgba": [U1s + "/rgba/S5_" + n for n in ("climber_with_coat.png", "climber_shadow_ratio.png", "rail_balusters_mid.png", "wall_rebuilt_far.png")],
           "masks": [U1s + "/masks/S5_" + n for n in ("climber_mask.png", "shadow_mask.png", "rail_balusters_mask.png")],
           "failure_masks": [U1s + "/failure_masks/S5_" + n for n in ("climber_cleanup_changed.png", "rail_cleanup_changed.png", "grabcut_init_fg_seeds.png")],
           "invented_fill_masks": {U1s + "/fills/S5_wall_patchcopy_invented.png": "wall behind the climber, his shadow and the rail: the plate's own damask moved by its measured repeat lattice a=(44,0) b=(68,-72) px (autocorrelation)"},
           "occlusion": "In this negative the climber is IN FRONT of the rail and newel (the plaid coat overlaps both); the plan's 'banister in front of the legs' is not true to the plate, so the rail is the MID plane and he passes in front of it along a path parallel to it; his legs are below the frame line."},
 "S6": {"grabcut": s6["grabcut"], "first_run_cleanup_stats": {"islands_removed": 0, "holes_filled": 19, "pixels_changed_by_cleanup": 13663},
        "near_band_manual_markup_plate": s6["near_band_manual_markup_plate"], "far_plane_manual_contour_plate": s6["far_plane_manual_contour_plate"], "layers": s6["layers"],
        "rgba": [U1s + "/rgba/S6_" + n for n in ("near_newel_rail.png", "mid_flights.png", "far_pale_plane.png")],
        "masks": [U1s + "/masks/S6_near_mask.png", U1s + "/masks/S6_far_plane_mask.png"],
        "failure_masks": [U1s + "/failure_masks/S6_near_cleanup_changed.png (overwritten by the cached rerun: empty; the first run changed 13663 px)"],
        "invented_fill_masks": {U1s + "/fills/S6_far_extension_invented.png": "pale plane continued 30 px under the flights' edge (normalized convolution)",
                                U1s + "/fills/S6_mid_under_near_invented.png": "flights under the newel/rail (TELEA)"}},
}
camera = {"S1": {"far_dx_px": [0, 11], "near_dx_px": [0, 17.6], "ease": "smoothstep over 132 frames", "direction": "content travels right (camera right-to-left), so the uncovered edge has plate margin"},
          "S2": s2["push"], "S3": {"far_dx_px": [12, 0], "near_dx_px": [18, 0], "ease": "cubic ease-out, at rest by 10.5 (shot frame 48)"},
          "S4": "none (held; all 180 frames byte-identical)", "S5": {"far_dx_px": [0, -8], "rail_dx_px": [0, -12], "figure_cam_dx_px": [0, -12.8], "ease": "linear"},
          "S6": {"tilt_far_px": 5, "tilt_mid_px": 8, "tilt_near_px": 12, "ease": "smoothstep over 60 frames"}, "S7": "as S5, then held"}
actions = {"E1": s1["E1"] | {"branch": "S1-warp (plan fallback, SCION-34 style handle warp): a rigid head piece opened a seam under the chin; the weighted warp keeps the jaw still and lifts/rights the crown"},
           "E3": s34["E3_frames"] | {"shadow_follows": "head-shadow ratio plane rotates by the same angle about the neck pivot + measured flash offset (260, 50) plate px, on the wall plane (k 1.0) while the head is on k 1.2",
                                      "changed_state": "returns fully to the rest pose (REST 0 deg) so S4's held frames are the untouched negative; the change is that the ring has passed unanswered"},
           "E4_E5": s5["events"], "viseme_track": "declared empty: mouth never moves (S3/S4 mouth is open in the negative and stays so)",
           "HELD_breath": "branch NOT rendered (default: nothing moves in S4)"}
ledger = {
 "unit": "U1 picture (SCION-29 extraction, SCION-44 multiplane staging, SCION-47 body actions, aesthetic grade)", "film": "un-homme-qui-dort",
 "built_on": {"plan": "plan-r2", "beats": "beats-r2", "aesthetic": "aesthetic-r2"}, "date": "2026-11-15/16",
 "build_scripts": str(FILMS / "swarm/un-homme-qui-dort/u1-build"),
 "foraged_items": items, "handmade_items": [
   {"what": "cutout rigs, masks, mattes, plane splits, camera paths, action curves for S1-S7", "where": U1s, "how": "OpenCV GrabCut + cleanup + matting band + manual contour markup at skin/skin and shadow/hair seams; multiplane compositing at 2x then area-resampled; frames passed through kit.Ink(boil=0, wobble=0) with paper(grain=False), no vignette"},
   {"what": "grade curves (one monotone neutral curve per plate)", "where": "this ledger: grade_curves"},
   {"what": "u1-contact.jpg, u1-aesthetic-compare.jpg", "where": str(FILMS / "swarm/un-homme-qui-dort")}],
 "same_sitter_check": same_sitter, "grade_curves": grades, "layers": layers, "camera_paths": camera, "actions": actions,
 "shots": {k: {"dir": str(U1 / "shots" / k), "frames": n, "pass_t": [t, t + n / FPS]} for k, n, t in (("S1", 132, 0.0), ("S2", 72, 5.5), ("S3", 72, 8.5), ("S4", 180, 11.5), ("S5", 132, 19.0), ("S6", 60, 24.5), ("S7", 192, 27.0))},
 "frame_format": "960x540 RGB PNG, R=G=B (neutral), pre-caption; file names <shot>_<NNNN>.png, NNNN = frame within the shot; identical frames are hardlinks",
 "measured": {"events": m["events"], "defining_beat_D": m["defining_beat_D"], "S5_equals_S7_first_132": m["S5_equals_S7_first_132"], "S7_tail_held_identical": m["S7_tail_held_identical"],
              "figure_alpha_coverage": m["figure_alpha_coverage"], "shadow_alpha_coverage": m["shadow_alpha_coverage"], "parallax": m["parallax"],
              "aesthetic_stats": m["stats"], "reference_stats": m["reference_stats_measured_here"], "aesthetic_targets": m["targets"], "grain_check": m["grain_check"],
              "head_height": {"S1": s1["head_height_frac"], "S3": s34["S3"]["head_height_frac"], "S4": s34["S4"]["head_height_frac"], "S5": s5["head_height_frac"]}},
 "sha1": m["sha1"],
 "budget": {"new_downloads_bytes": 30273104 + 28590432 + sum((RAW / f"{p}.json").stat().st_size for p in rights), "new_downloads": ["8d33576u.tif", "8d33583u.tif", "5 LoC item JSON records"],
            "deleted_derived": ["picture-forage-camera-team-quiet-observational-cut/stair_clip_full/ (144 PNG, 1.05 MB)", "…/stair_clip_safe/ (144 PNG, 0.81 MB)",
                                "…/BRANCH_stair_gaze_clip_full/ (1.25 MB)", "…/BRANCH_stair_gaze_clip_safe/ (0.96 MB)", "…/stair_clip_full.mkv (1.71 MB)", "…/stair_clip_safe.mkv (1.29 MB)",
                                "…/BRANCH_stair_gaze_clip_full.mkv (2.06 MB)", "…/BRANCH_stair_gaze_clip_safe.mkv (1.55 MB)", "…/stills_full/ (3.79 MB)", "…/stills_safe/ (2.91 MB)",
                                "u1-picture/raw/loc_2017735081_a2400.png (1.68 MB)", "u1-picture/raw/loc_2017714056_a2400.png (2.36 MB)"],
            "deleted_bytes": 21416000, "raw_downloads_deleted": "none",
            "sources_folder_size_before_bytes": 161000000, "sources_folder_size_after_bytes": None},
 "absences": [
   {"searched": "a door jamb / dark vertical occluder at frame right in LoC 2017862340", "result": "not in the negative (it is the rebate); no other Bubley frame was substituted"},
   {"searched": "a negative of the same set where the dark side of frame is a real mass (to match the reference's dark right half)", "result": "not searched further this run; reserve LoC 2017862354 (Bubley, man in a dark hall by a wall lamp) named in the plan was not downloaded (budget/time)"},
   {"searched": "a full-resolution master of LoC 2017811447", "result": "exists (8c18457u.tif, 143.8 MB) but over budget; 1024 px JPEG used at 1.435x"},
   {"searched": "Moving Image Archive cache for picture", "result": "not used for picture: the plan's picture is stills-only (LoC negatives); MIA is U2's first source for sound"}],
 "deviations_from_assignment": [
   "S2 and S6 use the archival TIFFs already on disk (no new download) instead of the 1024 px JPEGs, to avoid upscaling the close crops.",
   "S5 climber enters lower RIGHT and exits upper LEFT: the stair in this negative rises to frame left (measured rail slope 0.826).",
   "S5 occlusion: climber in front of the rail (true to the plate); banister is the mid plane, not a near occluder of the legs.",
   "S3/S4 have no jamb plane (see layers.S3_S4.jamb). S3/S4 near plane = clasped hands.",
   "E3 returns to the exact rest pose (no residual angle) so S4 is the untouched negative.",
   "S6 reads as looking down the well, not up."],
 "known_failures_and_residuals": [
   "S3 frames ~18-55 (during the head turn): a 1 px hairline and a slightly lighter sliver at the back of the head where hair meets the cast shadow (manual seam); not visible at rest.",
   "S5 rebuilt wallpaper: one darker repeat near the middle-top of the wall (a copied patch that sat in shadow penumbra); the empty-stair frames show it.",
   "S5 entry is measured at shot frame 37 (pass 20.54 s), 1 frame after the planned 36: within the +/-1 tolerance.",
   "S6 near band also carries a wedge of the lower flight under the rail (same wood, straight lower edge) that slides 4 px against the mid plane in deep shadow.",
   "S3 tonal split is wall-heavy (above 220: 0.67 vs reference 0.33) and S4 is closer but still pale (0.47 / below 60 0.20 vs 0.42): the sum passes (>= 0.55), the per-part +/-0.12 test fails on both. The negative's lit wall is larger than the reference's; the dark mass at right is his shadow and suit, not a mirror.",
   "S7 held tail (empty stair): p1 = 46, outside 20-40, because the wallpaper frame has no deep black. S1 is mid-heavy (60-220: 0.77).",
   "The S1 book (cover ornament, top of the pages) shows at the bottom right; title letters are below the frame. S4 shows the corner of the woman's book (pages, no letters) at the lower left."],
 "media_for_editor": {"shots_png": str(U1 / "shots"), "no_clips_or_audio": "picture is stills-based; no footage was trimmed and no audio decoded by U1 (sound is U2's)"},
}
dump(FILMS / "swarm/un-homme-qui-dort/u1-picture-ledger.json", ledger)
print("ledger written")

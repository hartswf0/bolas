# Assemble rig.json (pieces, joints with pivots in parent and child space, limits, dynamics, tests, evidence, absences)
import os, json, hashlib
FILMS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
SW = os.path.join(FILMS, "swarm", "bang-bang"); BD = os.path.join(FILMS, "sources", "bang-bang", "board")
import importlib.util
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "board.py")).read().split('if __name__ == "__main__":')[0]
g = {"__file__": os.path.join(os.path.dirname(os.path.abspath(__file__)), "board.py"), "__name__": "x"}
exec(compile(src, "board.py", "exec"), g)
P, JOINTS, SCALE = g["P"], g["JOINTS"], g["SCALE"]
MAN = json.load(open(os.path.join(BD, "cut_manifest.json")))
T = json.load(open(os.path.join(BD, "tests.json")))
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
rel = lambda p: os.path.relpath(p, os.path.join(FILMS, ".."))
pieces = {}
for nm, pc in P.items():
    m = MAN["pieces"].get(nm if nm != "pilot_legs" else "legs", {})
    pieces[nm] = {"file": m.get("file", f"board/{nm.replace('paper_wing_', 'paper_wing_')}.png"), "mask": m.get("mask"),
                  "source": m.get("source", "HANDMADE"), "render_scale": SCALE[nm], "size_at_scale": [pc["w"], pc["h"]],
                  "pins_at_scale": {k: [round(float(v[0]), 2), round(float(v[1]), 2)] for k, v in pc["pv"].items()},
                  "pins_source_px": m.get("pivots"), "offset_in_source": m.get("offset_src"), "components": m.get("components", 1),
                  "interior_holes_px": m.get("interior_holes_px"), "note": m.get("note", "")}
pieces["pilot_legs"]["note"] = "the same cut legs piece (board/legs.png) at the pilot's scale"
pieces["paper_wing_root"].update(file="board/paper_wing_root.png", note="HANDMADE: cream stock cut with a scalpel-polygon, pen spar and ribs; pinned at the pilot's hand")
pieces["paper_wing_tip"].update(file="board/paper_wing_tip.png", note="HANDMADE: scalloped tip segment on a crease pin; lags and folds (#41)")
joints = []
for ch, par, ppin, cpin, lim in JOINTS:
    joints.append({"child": ch, "parent": par, "pin_on_parent": ppin, "pin_on_child": cpin,
                   "pivot_parent_space": [round(float(v), 2) for v in P[par]["pv"][ppin]], "pivot_child_space": [round(float(v), 2) for v in P[ch]["pv"][cpin]],
                   "limits_deg_rel": list(lim), "brass_split_pin": True})
rig = {
 "film": "bang-bang", "unit": "board artist and puppet cutter (SCION #29 GrabCut, #2 Reiniger, #41 Secondary Dynamics)", "direction": "Direction 2, Planche gravée",
 "scripts": {"cut": "films/swarm/bang-bang/board-build/cut.py", "board_rig_exposure_render": "films/swarm/bang-bang/board-build/board.py", "this_file": "films/swarm/bang-bang/board-build/rigjson.py"},
 "outputs": {"exposure": "films/swarm/bang-bang/exposure.json", "test_mp4": "films/swarm/bang-bang/bb08_test.mp4", "contact_sheet": "films/swarm/bang-bang/bb08_sheet.jpg",
             "pieces_dir": "films/sources/bang-bang/board/", "editor_media": "films/sources/bang-bang/board-artist-and-puppet-cutter-cutout-rig-exposure-sheet-bb-08-test-shot-/"},
 "coordinates": {"page_px": [g["PW"], g["PH"]], "panels": {"x": g["PX"], "w": g["PWID"], "h": g["PHT"], "ys": g["PYS"], "aspect": round(g["PWID"] / g["PHT"], 3)},
                 "commentary_column_x0": g["TX0"], "ground_line_v": g["GROUND"],
                 "angles": "deg, + = clockwise on screen (= nose-up for the left-facing glider; legs + = feet forward/left)", "time": "24 fps, drawings on 2s"},
 "pieces": pieces, "joints": joints,
 "dynamics": {
   "integrator": "semi-implicit (symplectic) Euler, 240 Hz (10 substeps per film frame), sampled per frame, held on 2s",
   "hip_legs": {"model": "pendulum on the hip pin driven by the body's acceleration: phi'' = [-(g - a_y) sin phi + a_x cos phi]/L - c (phi' - theta')", "g_px_s2": 588.6, "L_px": 18, "c": 4.2, "c_during_hang_f540_564": 8.6, "kick_at_f540_rad_s": 6.0, "c_after_impact": 9.0, "panel_cut_f576": "no acceleration across a cut between panels (repair 2)", "joint_stop": list(g["JD"]["legs"][3]), "run_drive": "f432-490 legs driven to +-28 deg on 4-frame alternation"},
   "paper_wing_tip": {"model": "angular spring-damper relative to the root, inertial drive = -0.9 x arm angular acceleration; crease rest 0 -> 150 deg at f106 (3rd flap)", "k": 420, "zeta": 0.18},
   "band_snap": {"model": "whip amplitude spring-damper, impulse 900 px/s at f312", "k": 700, "zeta": 0.15},
   "wing_root_droop": {"model": "repair 2: the spar snaps at f605: the outer wing whips to 58 deg, held 3 drawings f605-610, then a spring-damper onto the broken root at 40 deg; joint stop -3..62 (the intact-spar stop is gone)", "k": 700, "zeta": 0.45},
   "a1_legs": {"model": "spring to sit pose -80 deg at f150 (25 deg tuck during the hop)", "k": 500, "zeta": 0.3}},
 "tests": T,
 "tests_note": "measured from the rig and exposure (board.py tests()). pivot drift: child pin vs parent pin in panel px for every joint of every drawing. Repair 2: legs decay measured on the ON-SCREEN run: the body is at rest f540-564 (hang lengthened, slide starts f565); the legs are kicked (6 rad/s) as the body stops dead and must read |phi| >= 8 deg at f542 and < 1 deg by f564. first_failure_frame: first frame with pitch >= 15 deg and x-advance < 0.5 px/frame.",
 "aesthetic_measurements": {"wide_f700": {"ink_pct": 0.62, "midtone_pct": 0.74, "paper_median": [243, 229, 212], "ink_median": [71, 60, 52]},
                            "bb08_f540": {"ink_pct": 3.05, "midtone_pct": 3.66, "paper_median_incl_panel": [229, 217, 203], "ink_median": [70, 60, 51]},
                            "note": "PIL, luminance <120 ink, 120-200 midtone. Wide f700 ink is below the 3 % target because the slip column is still empty here (slips for BB-07/09 come from the writer unit's cues)"},
 "sources": [
  {"id": "LIL-START", "title": "File:PSM V46 D647 Lilienthal flying apparatus the start.jpg (Popular Science Monthly vol. 46, 1894-95)", "author": "Unknown author", "license": "Public domain",
   "license_url": "", "source_url": "https://commons.wikimedia.org/wiki/File:PSM_V46_D647_Lilienthal_flying_apparatus_the_start.jpg",
   "file_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/df/PSM_V46_D647_Lilienthal_flying_apparatus_the_start.jpg/960px-PSM_V46_D647_Lilienthal_flying_apparatus_the_start.jpg",
   "local_path": "films/sources/bang-bang/lilienthal_start.jpg", "sha256_16": sha(os.path.join(FILMS, "sources/bang-bang/lilienthal_start.jpg")),
   "what_it_shows": "wood engraving: a man standing in a bird-winged hang glider with a kite tail, at the start of a run",
   "verified_date_or_place": "1894-95 (Commons DateTimeOriginal); licence re-read from Commons extmetadata LicenseShortName on 2026-11-16",
   "used_as": "glider, glider_core, glider_wingR, legs; pilot_torso, pilot_arm (the pilot alone for A1/A2, spars erased and re-inked)"},
  {"id": "PENAUD-PLATE", "title": "File:Pénaud's flying models.jpg (plate 3, Balloons (Aeronautical machines), fig. 1 Pénaud's Hélicoptère)", "author": "Unknown author", "license": "Public domain",
   "license_url": "", "source_url": "https://commons.wikimedia.org/wiki/File:P%C3%A9naud%27s_flying_models.jpg",
   "file_url": "https://upload.wikimedia.org/wikipedia/commons/9/9f/P%C3%A9naud%27s_flying_models.jpg", "local_path": "films/sources/bang-bang/penaud_models.jpg",
   "sha256_16": sha(os.path.join(FILMS, "sources/bang-bang/penaud_models.jpg")),
   "what_it_shows": "engraved plate of three Pénaud models: hélicoptère (two rotors on a shaft with a twisted rubber skein), planophore, mechanical bird",
   "verified_date_or_place": "1875 (Commons DateTimeOriginal); licence re-read from Commons extmetadata on 2026-11-16",
   "used_as": "heli_top, heli_shaft, heli_bottom (A2, BB-02/03)"},
  {"id": "AUDUBON-MAGPIE", "title": "Common magpie (1. Male 2. Female), coloured lithograph by J. T. Bowen after J. J. Audubon (Birds of America, octavo edition)",
   "author": "John James Audubon (drawn from nature); lith. J. T. Bowen, Philadelphia", "license": "Public domain (published Philadelphia 1840-1844; artist d. 1851)",
   "license_url": "", "source_url": "https://www.loc.gov/pictures/item/2022643758/",
   "file_url": "https://tile.loc.gov/storage-services/service/pnp/cph/3a30000/3a32000/3a32800/3a32885r.jpg", "local_path": "films/sources/bang-bang/board/src/common_magpie_r.jpg",
   "sha256_16": sha(os.path.join(BD, "src/common_magpie_r.jpg")),
   "what_it_shows": "two magpies (Pica, black-and-white with long tail): fig. 1 male in flight seen from above, wings and tail spread; fig. 2 female alighting across a branch, wings half open",
   "verified_date_or_place": "LoC caption card: 'Col. lithograph by Bowen after Audubon, p. 99. RB Div.'; LoC rights field reads 'Rights status not evaluated' - the public-domain status rests on the 1840s publication date and the artist's death in 1851 (flag for the reviewer). Plate imprint 'Drawn from Nature by J.J. Audubon F.R.S.F.L.S.' / 'Lith. Printed & Col. by J.T. Bowen Philad.' visible in the scan",
   "used_as": "fly_body, fly_wingL, fly_wingR (the flying magpie, re-pinned at the shoulders); pie_body, pie_head (the perched commentator, branch removed). Replaces the earlier pied-crow stand-in (CROW)"}],
 "searched_and_rejected_or_absent": [
  "Commons 'Twee eksters op een tak, RP-P-2002-661.jpg' (Rijksmuseum print, CC0 per extmetadata, 1875-1939): two magpies, licence fine, but every download from upload.wikimedia.org returned HTTP 429 (retry-after 600 s) during this unit; not used",
  "Commons 'Penny Magazine 1837 155 Wing of the Magpie.jpg' (PD per extmetadata, 1837 woodcut of a spread magpie wing): wanted for the flying wing; download blocked by the same 429; not used",
  "LoC 'Die Elster und die Eule' [1846] (No known restrictions): a magpie, but costumed (bonnet, shawl) in a fable scene; rejected as off-character",
  "Commons searches 'Pica pica Brehms Tierleben', 'Elster Holzstich', 'magpie engraving', 'Bewick magpie' found only whole-book PDFs/DjVu, no single-plate magpie wood engraving in line; a true line-engraved (not lithograph) magpie was not obtained",
  "Higher-resolution Audubon scan (LoC larger TIFF) is marked 'only available at the Library of Congress'; the 385x640 JPEG was used (adequate: the bird is ~90-110 px on screen)",
  "CROW (Corvus scapulatus, Brehms Tierleben, PD) from the test shot is retired: it is a pied crow, not a magpie"],
 "repairs": MAN["repairs"],
 "mask_stats": MAN["mask_stats"],
 "failure_masks": ["board/lil_fail_mask.png", "board/penaud_fail_mask.png", "board/audubon_fly_fail_mask.png", "board/audubon_fem_fail_mask.png", "board/pilot_repair_map.png"],
 "handmade": [
  {"item": "storyboard sheets planche 1 and 2", "where": "board/sheet1.png, board/sheet2.png (board.py build_sheet)", "what": "2200x1800 cream sheet (242,228,212), duskier left margin, mirrored show-through of the facing page's hand and panels, three stacked 1.45:1 pen panels at x=253, w=715 with duskier interiors (228,216,202), a punched hole top-left of each, graphite board headers and page number"},
  {"item": "paper wing (A1)", "where": "board/paper_wing_root.png, board/paper_wing_tip.png", "what": "two cut pieces of the same cream stock with pen spar and ribs; root on the pilot's hand, tip on a crease pin"},
  {"item": "pen set: wall, flowerbed, gatepost (s1p1), turf and post (s1p2), hill and fence (s2p1), turf and fence post (s2p2), turf and flowerbed (s2p3)", "where": "board/set_s*.png (ink-only RGBA, panel-local)", "what": "jittered felt-pen strokes in warm ink (52,42,34)"},
  {"item": "brass split pins", "where": "board.py brass_pin()", "what": "rim (70,56,38), head (176,138,62), highlight; on the glider hip and on each slip"},
  {"item": "torn slip paper and the bird's hand", "where": "board.py torn_slip(), hand2()", "what": "torn cream strips; a per-letter Hershey-derived French hand: per-letter size, tilt, baseline offset, nib pressure, per-word slant, line drift, felt nib, written on letter by letter at 12-14 chars/s"},
  {"item": "annotations", "where": "board.py annotations()", "what": "inked part labels A (wing) and B (raised nose), graphite dashed horizon through the hip pin and 35 deg arc"}],
 "known_gaps": [
  "the perched magpie (pie_body) is cut from a 385x640 lithograph and printed in two values; it reads as a black-and-white long-tailed bird at film size but its repaired belly (branch removed) is simplified",
  "BB-08 is the only rendered board; BB-00..BB-10 exist in exposure.json as poses (the editor renders them); slips for boards other than BB-08 are the writer unit's",
  "the band snap is a dynamics channel (amplitude per frame in exposure.json a2.band_whip_px); the squiggle itself is to be drawn by the editor from that value",
  "rotor turning is foreshortening (scale_x = |cos phase|) of a flat cut piece, as a paper puppet would be"]
}
json.dump(rig, open(os.path.join(SW, "rig.json"), "w"), indent=1, ensure_ascii=False)
# credits: add the new foraged item if missing
cp = os.path.join(FILMS, "credits", "bang-bang.json")
cr = json.load(open(cp))
if not any("Common magpie" in c.get("title", "") for c in cr):
    s = rig["sources"][2]
    cr.append({"title": s["title"], "author": s["author"], "license": s["license"], "license_url": "", "source_url": s["source_url"], "file_url": s["file_url"],
               "used_as": "the magpie narrator: flying pose and perched commentator, cut-paper puppet pieces"})
    json.dump(cr, open(cp, "w"), indent=1, ensure_ascii=False)
print("rig.json written", len(pieces), "pieces", len(joints), "joints")

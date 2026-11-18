"""Write films/swarm/le-chant-du-styrene/melt_shot.json from the build's parameters and measured metrics."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import melt3 as m
SW = Path("/home/user/bolas/paeleo/scion/oulipo/films/swarm/le-chant-du-styrene")
MDr = "films/sources/le-chant-du-styrene/melt-simulation-camera-unit-b-test-shot-sh3a-sh3b-defining-beat-"
MD = Path("/home/user/bolas/paeleo/scion/oulipo") / MDr
met = json.load(open(MD / "metrics.json"))
iou = [r["iou"] for r in met["cavity_vs_ring_iou_plane"]]
out = {
 "unit": "U3 melt simulation (camera unit B: test shot Sh3a + Sh3b, defining beat)",
 "plan_revision": "plan.md r3", "date": "2026-11-16",
 "direction": "2 'La coulee rendue' (defining beat), built from the approved test shot with the user's fixes; no drift to another direction",
 "build_scripts": "films/swarm/le-chant-du-styrene/melt-build/ (melt3.py simulation+shading+camera, render.py frames, compare3.py metrics+sheet, preview3.py kit.py preview, ledger.py this file, probe.py dev stills)",
 "reproduce": "cd films/swarm/le-chant-du-styrene/melt-build && python3 -I render.py 415 662 && python3 -I compare3.py && python3 -I preview3.py && python3 -I ledger.py",
 "seed": m.SEED, "seed_note": "numpy RandomState(1958) for the steel quilting; smooth_noise seeds 3 (channel wobble), 100-107 (boil bank, sigma 9), 200-207 (fine boil, sigma 3); boil reseeded every 2 frames (index (k//2) mod 8)",
 "parameters": m.PARAMS,
 "renders": {
  "format": "960x408 picture band only, no captions, no letterbox, no grain (editor applies the shared grain); PNG sequences + lossless libx264rgb crf 0 mp4, 24 fps; global frame index f, film time t = f/24",
  "sh3a_dissolve_target": {"frames": "415-422 (16.29-17.58 s)", "png": MDr + "/sh3a_dissolve_target/f%04d.png", "mp4": MDr + "/sh3a_dissolve_target.mp4",
    "note": "full melt in the open mould half seen frontally with EXACTLY the sh2b_hold camera (centre (9,26) world, zoom 0.75): dissolve U2's sh2b f0415-f0422 into these 8 frames, then continue with sh3a f0423. Check overlay: " + MDr + "/dissolve_check_f0422_50pct.png"},
  "sh3a": {"t": "17.60-20.80 s", "frames": "423-499", "png": MDr + "/sh3a/f%04d.png", "mp4": MDr + "/sh3a.mp4",
    "content": "full melt (boil at 0.35 amplitude, on twos) in the cavities of the steel; frontal sh2b_hold framing held to 18.00 s, then a slow tilt to 16 deg pitch with a 7% push by 20.80 (cut C2)"},
  "sh3b": {"t": "20.80-27.60 s", "frames": "500-662", "png": MDr + "/sh3b/f%04d.png", "mp4": MDr + "/sh3b.mp4",
    "content": "closer 3/4 view (pitch 50->46 deg, yaw -9->-4, roll -6->-4.5, glide + push); fill-time field run backward: cavities empty far->near at 21.9 / 22.9 / 23.9 / 24.9 s, melt retracts up the runner, last melt down the sprue at 26.19 s; hold on four wet-lit warm hollows 26.2-27.6; focus pull from the first-emptied cavity to the sprue (0.3-4.9 s into the shot)"},
  "preview_with_sound": {"mp4": MDr + "/melt-shot-preview.mp4", "note": "kit.py review preview, film 17.60-27.60 s, letterbox + L3 caption + U1 stems; not the editor's assembly"},
 },
 "audio_for_editor": {"dir": MDr + "/audio/", "files": ["drain_17.60-27.60.wav", "meter_17.60-27.60.wav", "press_foraged_17.60-27.60.wav", "rain_17.60-27.60.wav", "room_17.60-27.60.wav"],
   "note": "44.1 kHz stereo slices (film 17.60-27.60) of the process-verse unit's stems; the picture's drain events were timed to that unit's cue sheet (cavity release 21.9/22.9/23.9/24.9, sprue glug 26.2), so drain.wav lines up without edits. press_foraged is the real Engel injection-moulding machine recording (CC BY 3.0, see evidence)."},
 "measurements": {
  "cavity_vs_ring_iou": met["cavity_vs_ring_iou_plane"], "cavity_vs_ring_iou_min": min(iou), "required_min": 0.85, "pass_iou": min(iou) >= 0.85,
  "cavity_vs_ring_iou_in_film_hold_frame": met["cavity_vs_ring_iou_film_hold"],
  "iou_method": "cavity mask (depth>0.02, generated from geometry.json ellipse + bore fits at home_centre) vs U2's ring piece alpha placed unrotated with its ellipse centre at the same home_centre (the Sh2b hold pose: rotation 0, scale 1), both in plane coords (x1.25 of source px) and again projected by the hold camera",
  "u2_hold_frame_vs_mould_outline_iou": met["u2_hold_frame_vs_mould_outline_iou"],
  "u2_hold_note": "whole-object overlap of U2's rendered f0422 (lit warm pixels) with the projected mould mask; lower than the per-ring IoU because U2's runner shows the standing sprue post and four legs, which in the mould half are a well at the hub and not channels",
  "flip_iou_left_right": met["flip_iou_lr_ud"][0], "flip_iou_up_down": met["flip_iou_lr_ud"][1], "required_flip_max": 0.8, "pass_asymmetry": met["flip_iou_lr_ud"][0] < 0.8,
  "drain_empty_film_time": met["drain_empty_film_time"], "drain_order_far_to_near": met["drain_order_far_to_near"],
  "drain_order_note": "cavity ids 0..3 = geometry.json rings 1..4 (1 left arm, 2 up-right, 3 right, 4 down). Order 3 (right, narrowest 8 px arm) -> 1 (left) -> 4 (down) -> 2 (up-right, shortest wide arm, nearest the sprue). 1.0 s between releases (test shot had 0.3 s).",
  "cavity_fill_fraction_vs_time": met["cavity_fill_fraction_vs_time"],
  "band_stats": {k: v for k, v in met.items() if k.startswith("t=") or k in ("reference_band_rows144_375", "kf2_band")},
  "stats_note": "inside the 960x408 band; luminance Rec.709; lit = lum>25; warm = hue <55 or >340 deg; blue = 200-250 deg. Plastic brightened as asked: band p99 ~164-169 during the melt (test shot ~88), max <=205 (no whites). Hollows at the end stay warm: at 27.5 s lit pixels are 0.56 warm (the hollows and runner) and 0.42 blue (the practical lamps, now visible as asked by the plan); the test shot was 0.03 warm. Blue practical present in every measured still (0.16-0.42).",
 },
 "comparison_sheet": "films/swarm/le-chant-du-styrene/melt-shot-compare-24.0s.jpg (Sh3b @24.0 s | proposals/kf-2.png | styreneA.webp band | Sh3b @27.5 s hollows, each with its band stats)",
 "fixes_from_test_shot_review": {
  "brighter_amber_cores": "source E=(1.50,1.50,1.05), alpha=(0.45,1.30,3.2), thin runner depth 0.40 vs ring 1.0-1.25: runner reads amber-orange, rings deep red; band p99 164-169, max ~204 (shared U2 roll-off knee 0.66)",
  "warm_hollows": "lasting wet coat (3.5% of depth, concentrated where walls meet floor and in the rib grooves) at a longer optical path -> dim red-amber; warm key (1.0,0.50,0.20) on the walls facing the source; no cold steel grey",
  "legible_order": "hesitation model + monotone re-timing: releases 1.0 s apart (21.9/22.9/23.9/24.9) instead of 0.3 s",
  "foraged_sound": "the process-verse unit found and licensed a real injection-moulding machine recording (CC BY 3.0); sliced here for this span and used in the preview",
  "kept": "asymmetry (flip IoU 0.13), refraction of the steel photograph through the melt surface gradient (40 px x grad), broad textured spill (narrow 6 px halo cut to 0.08 to avoid a constant-width glow), Beer-Lambert thickness colour, meniscus specular, boil on twos + Whitney oscillator bank, focus pull"},
 "techniques": {
  "8_sutherland_constraint_sketchpad": "one constraint graph (geometry.json): ring ellipse+bore attached-to home_centre (= gate + support radius, U2's contact constraint), arms = measured polylines hub->gate, sprue at hub. The cavity/channel field and the fill-time graph are generated from it; residual = IoU 0.96-0.97 (>=0.85).",
  "29_grabcut": "used through U2's GrabCut pieces/masks: channel widths are measured on bare_runner_mask.png by distance transform along each arm (13.6, 20.4, 8.0, 20.4 src px); ring silhouettes for the IoU test are the GrabCut alphas.",
  "6_whitney_harmonic": "meniscus oscillator bank: per cavity partials p=1..3 at p*w_i, w_i = 2pi*0.42*1.5^(i mod 2)*(1+0.5*(i//2)) (2:3 chain), 3-fold angular mode, advanced on twos",
  "44_multiplane": "blue practicals on their own plane (U2's lamps, same positions/colours), 0.3x drift; seen directly past the plate edge and reflected by the polished plate (x1.15, texture-modulated); plate on its own perspective plane"},
 "foraged": [
  {"id": "F-steel", "title": "Injection mold - (11).jpg", "author": "Bricetofly", "license": "CC0",
   "license_url": "http://creativecommons.org/publicdomain/zero/1.0/deed.en",
   "source_url": "https://commons.wikimedia.org/wiki/File:Injection_mold_-_(11).jpg",
   "file_url": "https://upload.wikimedia.org/wikipedia/commons/1/10/Injection_mold_-_%2811%29.jpg",
   "local_path": "films/sources/le-chant-du-styrene/kf/mold11.jpg (1280x852 copy of the 4160x2768 original, re-used from round 2)",
   "what_it_shows": "steel plates of a plastic injection mould with a slide ('systeme de tiroir pour un moule a injection plastique'), socket screws, brushed plate faces",
   "verified_date_or_place": "Commons extmetadata re-read 2026-11-16: LicenseShortName CC0, UsageTerms 'Creative Commons Zero, Public Domain Dedication', Artist Bricetofly (own work), DateTimeOriginal 2026-01-20",
   "used_as": "the mould-plate steel: texture quilted (feathered 150 px patches, seed 1958) from the photo's plain plate areas only (rows/cols 235-790/5-285, 255-435/800-1170, 615-785/800-1170) so no cavity is cut through its slide pocket; one of its real socket screws (centre 1243,182, r 36) kept at a plate corner; desaturated toward neutral steel; its high-pass machining texture is what the melt refracts, what spill and the warm key rake, and the floor of the hollows. The slide's maker's mark is not in any patch."},
  {"id": "F-runner-geometry", "title": "Spritzguss teile.jpg", "author": "Gmhofmann", "license": "CC BY-SA 4.0",
   "license_url": "https://creativecommons.org/licenses/by-sa/4.0", "source_url": "https://commons.wikimedia.org/wiki/File:Spritzguss_teile.jpg",
   "file_url": "https://upload.wikimedia.org/wikipedia/commons/e/e6/Spritzguss_teile.jpg",
   "local_path": "films/sources/le-chant-du-styrene/r2/spritzguss.jpg (via U2's geometry.json, pieces/ and masks/)",
   "what_it_shows": "teal injection-moulded runner trees with ring parts on a white table",
   "verified_date_or_place": "licence verified by U2 (cutouts.json) from Commons extmetadata 2026-11-16; not re-read by this unit",
   "used_as": "measurement only (not shown in Sh3): the cavity/channel layout, ring ellipse and bore fits, arm widths. The mould outline is a derived shape of a CC BY-SA 4.0 work; credit accordingly."},
  {"id": "E-gigaset (via U1)", "title": "Gigaset Cordless Telephone Production II - Engel Injection Moulding Machine.webm",
   "author": "Sound recordist: Kathinka Engels; photographer and video recordist: Inke Pickhardt (Work With Sounds)", "license": "CC BY 3.0",
   "license_url": "https://creativecommons.org/licenses/by/3.0",
   "source_url": "https://commons.wikimedia.org/wiki/File:Gigaset_Cordless_Telephone_Production_II_-_Engel_Injection_Moulding_Machine.webm",
   "file_url": "https://upload.wikimedia.org/wikipedia/commons/transcoded/9/9f/Gigaset_Cordless_Telephone_Production_II_-_Engel_Injection_Moulding_Machine.webm/Gigaset_Cordless_Telephone_Production_II_-_Engel_Injection_Moulding_Machine.webm.480p.vp9.webm",
   "local_path": MDr + "/audio/press_foraged_17.60-27.60.wav (slice of U1's stems/press_foraged.wav)",
   "what_it_shows": "sound of an Engel injection moulding machine running, Gigaset factory, Bocholt, 2009",
   "verified_date_or_place": "per process_graph.json (U1): Bocholt, Germany, 2009; licence read 2026-11-16 by U1; not re-read here",
   "used_as": "the real press bed under Sh3a/Sh3b (U1's fades 18.8-19.8 in, 26.4-27.4 out)"},
 ],
 "handmade": [
  {"id": "H-mould-field", "what": "cavity/channel/sprue depth field generated from geometry.json (ellipse+bore cavities with deeper rim, rib groove with 3 slots, tapered gates, sprue well)", "where": "melt-build/melt3.py"},
  {"id": "H-fill-time", "what": "fill-time field: weighted geodesic (Dijkstra, 2 px grid, normalized-convolution upsampling) from the sprue, speed 0.15+(depth/D)^0.6 (wall lag), x(w/w_med)^2 per arm (Poiseuille), x0.6 in cavities; hesitation delay (0.7 overlap) for unbalanced branches; monotone re-timing to the cue sheet; melt shown where t_drain + eta > t (equivalently T'+eta' < tau, tau running from full to 0)", "where": "melt3.py"},
  {"id": "H-melt-shading", "what": "Beer-Lambert thickness colour (two passes through the melt off the polished floor), refraction of F-steel by the melt-surface gradient, specular on the meniscus, two-scale spill on the steel, grazing-wall darkening (no glow outline), lasting wet coat in the hollows, warm raking key", "where": "melt3.py plane()"},
  {"id": "H-camera", "what": "pinhole perspective of the plate: frontal hold (=sh2b_hold) -> slow tilt (Sh3a), 3/4 glide (Sh3b), thin-lens focus pull, the shared halation + roll-off of the cutout unit", "where": "melt3.py camera()/band()"},
  {"id": "H-practicals", "what": "two defocused blue practical lamps (U2's disc and bar), own plane, 0.3x drift, plus their reflection in the plate", "where": "melt3.py practicals()"},
 ],
 "declared_substitutions": [
  "Molten polystyrene does not glow: the melt's light is the warm source reflected from the polished cavity floor through the pigmented melt (lighting choice, Beer-Lambert computed).",
  "The plate texture is quilted from plain areas of the CC0 photograph, not the photograph's own layout; the cavities are handmade from the runner geometry.",
  "In the mould half the runner's standing sprue post is a well at the hub; U2's puppet legs/post have no channel counterpart.",
  "The drain order uses a declared hesitation model (unbalanced branches fill in turn with 70% overlap) and a monotone re-timing of the fill-time field to the verse cue sheet.",
  "The runner and rings' red/amber colour follows the film's declared teal->red/amber gel substitution (U2), here computed as Beer-Lambert thickness colour."],
 "absences": [
  "No real red or amber translucent runner photograph under an allowed licence (U2/U1 search; not repeated here).",
  "No open-licence footage or photograph of molten plastic filling or draining a mould cavity was used: the Moving Image Archive cache has no plastics footage (plan.md, U1); this unit did no new search and made the melt by simulation.",
  "No open recording of melt suction/drain; the drain sound is U1's handmade drain stem."],
 "archive_cache": "Moving Image Archive cache not used for picture in this shot (procedural animation over one CC0 still); sound uses U1's Commons recording.",
 "no_material_from_the_1958_film": True,
 "new_downloads_mb": 0.0,
}
json.dump(out, open(SW / "melt_shot.json", "w"), indent=1, default=float)
print("wrote", SW / "melt_shot.json")

# A Morning Stroll: assembly (editor), plan-r1 / score-r1, repair round 1 (r2)

- **Script:** `films/a-morning-stroll.py`, using `kit.Film` at 960x540 and 24 fps. kit.py is not edited.
- **Render:** `assets/films/a-morning-stroll.mp4`, 68.0 s.
- **Checks:** `python3 films/a-morning-stroll.py --report` re-runs the assertions and rewrites `ledger.json` and the three `compare-*.jpg` sheets.
- **Direction:** Direction 1, "Rizzuto Stoop", unchanged.

The film is assembled from the units' outputs:
- **Plates, crops, mattes, geometry and grades:** `plates.json` (U1).
- **The FK rooster, tracks, shadows, door mechanisms and 2059 state machine:** `puppet.py` and `knockproof.py` (U2), imported as modules.
- **Stems:** `sound.json` (U3), placed with `mix.add`.

## Repair round 1: what changed

| Review item | Fix (material or technique, no look filter) | Measured now |
|---|---|---|
| Strikes barely readable muted | `P.POSES` strike neck -30 / head -14 (was -15/-7), a 2-frame cock (neck +12), recoil +9, body pitch -14 deg plus a further -6 on contact (V1 track rebuilt from `KP.build_track`). The whole head and neck drive ~25-30 canvas px. HANDMADE contact marks at the beak tip on E3/E4: paint or wood chips thrown off under gravity for 5 frames and a dark nick with a lit lip that stays on the leaf until the door moves; glass gets a 3-frame glint. | beak in leaf mask on E3/E4 in all four sections (asserted) |
| V1 aesthetic: soft grey, left black panel | The insert is moved off the vestibule recess (CAM_I 1662-2202). The black mass is now real light logic: the stopped watcher's hard head-and-shoulders shadow (the same OWI silhouette and 14 deg head turn as V1-A) lies on the door, and it slides off as the leaf swings into the dark hall. Kit grain is off for V1 (the print carries its own). The lens fall-off is gentler (0.45). | 9.0 s: <40 20.9 %, >200 24.8 %, black mass 14.7 % (the shadow), corner/centre 0.31, neutral |
| V1-A railing and frame edge | The climb runs N6 → N5 → N4 up the middle of the stoop, behind the near twisted bars, and stops on N4, so the comb stays in frame (bird 21-25 % of height). | bird px behind iron per 8 frames in the ledger: 1356-1550 (f0-16) and 607-777 (f56-112); 0 showing through |
| V2: grey stand-in bird, saturation | New colour bird: Highsmith's rooster (LoC highsm.61221, 2019), mirrored, GrabCut-cut into 10 FK pieces (`puppet/extract_colour.py`, `pieces/rooster_c/`), photographic colour unchanged. V2-B is reframed onto the latch edge, the brick and the iron (region (400,1006)-(933,1306)), and the bird stands at the leaf's latch edge. | 25.0 s sat 0.275 (bar 0.25; the critic's 0.28 is just missed) |
| D read as thresholded plate | B is all cut card: a door card of grey tissue with slot-cut mouldings and a pin-head knob, a vestibule board, a jamb strip, and a railing strip with square balusters and scroll rings. The watcher is a grey gel. The black bird reads on the grey door. | E3/E4 and E6-end asserts pass |
| Provenance | Four MIA sound sources were verified independently as Prelinger Archives items on archive.org, each with licenseurl creativecommons.org/licenses/publicdomain: ThirdAve1950, Formatio1936, Arteries1941, DatingDo1949. Straight Talk (1992) had no independent record, so it was dropped and the 2009 bed rebuilt from Formations. Bubley is named. The LoC items carry PD bases. The end card and note name Plennert, CC BY-SA 4.0, and declare the film CC BY-SA 4.0. The cards read "2009: plate photographed 2019, standing in" and "2059: plate photographed 2022; staged". | credits file: 11 records |
| 1959 pitch +4.3 st by peak-pick | Documented in sound.json `repair_r2_editor`. Strike 2 is strike 1 resampled by exactly 2^(3/12). The matched-filter estimate reads 3.0 st in every stem. A single-peak pick on a broadband knock over the bed is not a valid interval measure. | 3.0 st (matched filter) |

## Timecoded sequence and evidence

| Global | Segment | On screen (layer DAG) | Evidence IDs |
|---|---|---|---|
| 0.0-2.0 | Title | "A MORNING STROLL / after Grant Orchard (2011)" | sound: mia Arteries1941 room tone |
| 2.0-3.0 | Card 1959 | | v1 stem lead-in |
| 3.0-8.0 | V1·A | plate crop A with the 1.5 % push → watcher cast shadow → bird cast shadow broken at the riser, plus contact shadow → FK 1870s rooster (hops N6→N5→N4 on twos at 3.6 and 5.2, then holds and looks up) → `holdout_A_iron` in front → vignette. The watcher stops at 6.5 (E2). | loc-ppmsca.70651, loc-stereo-1s08734, loc-owi-2017861981 (Bubley); sound v1 (Prelinger ThirdAve1950, Formatio1936, Arteries1941, DatingDo1949 footsteps) |
| 8.0-14.0 | V1·B | `knockproof.compose`: plate with the watcher's shadow baked on → hall → hinged leaf (homography; the shadow fades off the leaf as it swings) → bird shadow → bird → iron → jamb → lens fall-off → contact marks. Insert 8.67-9.75. **E3 9.00 / E4 9.333**: cock, strike, chips, nick. Door 10.0-11.5. The bird leaps in and is gone behind the jamb by 13.0. | as above; sound Commons Knock_on_door (CC0) +3 st, DatingDo1949 latch, handmade creak |
| 14.0-18.0 | V1·C | the empty stoop; the watcher's shadow leaves | as V1·A |
| 18.0-19.0 | Card "2009 / plate photographed 2019, standing in" | | |
| 19.0-24.0 | V2·A | highsm.56276 preview crop A → watcher shadow → colour rooster (highsm.61221 cut-out) hops 6 treads → iron holdout | loc-highsm.56276, loc-highsm.61221, loc-owi; sound v2 (Formatio1936 traffic, handmade car swells) |
| 24.0-30.0 | V2·B | region crop (400,1006)-(933,1306) → hall → leaf by homography (`chain_theta`, stopped at 25 deg) → bird shadows → bird (only the gap shows it once inside; jamb holdout) → HANDMADE chain → pale-blue paint chips. **E3 25.00 / E4 25.333.** The bird walks into the gap and is gone at 29.0. | as above; sound handmade hollow knock, chain ticks |
| 30.0-34.0 | V2·C | wide, leaf ajar | as V2·A |
| 34.0-35.0 | Card "2059 / plate photographed 2022; staged" | | |
| 35.0-40.0 | V3·A | Commons Schiebetür (Plennert, CC BY-SA 4.0), locked off → long low-sun watcher shadow (64 % of height) → toned 1870s rooster walks the forecourt → threshold → posts and pillar → HANDMADE 7-dot strip. **X1 39.6:** one peck at the tread; dot 1 lights and refuses. | commons-schiebetuer, loc-stereo-1s08734, loc-owi; sound handmade hum, wind, denied tone |
| 40.0-46.0 | V3·B | interior → bird → sliding leaves (`DoorFSM`) → threshold → posts and pillar → strip → glass glint at the beak. **E3 41.00 / E4 41.333**: two dots, chime, slide. The bird is hidden behind the pillar by 45.0. | as above; handmade glass tap, chime, slide |
| 46.0-50.0 | V3·C | wide, door shut | |
| 50.0-51.0 | Card "1959 / diagnostic: silhouette" | | |
| 51.0-66.0 | D | Same score and cameras, as Reiniger-style card theatre on backlit paper. A/C: the stoop card from the tread polylines, the lace iron as card, the watcher as gel. B: the cut-card door, boards and railing (above), the black FK rooster with split pins, card chips. **E3 57.00 / E4 57.333.** | geometry and masks from loc-ppmsca.70651, loc-stereo-1s08734, loc-owi; identical v1 stem |
| 66.0-68.0 | End card | archives with photographers; "Sliding door photograph: Plennert, CC BY-SA 4.0. This film is CC BY-SA 4.0."; handmade list | v1 stem tail |

## Ledger and claim graph (plan §9 and §10)

`ledger.json` holds one manifest per version (V1, V2, V3, D). Each has separate `era`, `genre_tone` and `render_technique` fields, E1-E7 on identical local frames (asserted), and measured checks. `report()` asserts:
- E3/E4 global frames 216/224, 600/608, 984/992 and 1368/1376;
- the beak tip inside the door-leaf mask on E3 and E4 in every version;
- 0 bird px past the jamb at E6 end, with a monotone fall (`visible_px_f204_to_f240_step4`).

It also records:
- the X1 FSM trace;
- the V3·A watcher shadow fraction (0.639);
- V1·A behind-iron counts.

The compare sheets are `compare-1959/2009/2059.jpg`. Their numbers are in `ledger.json` under `compare`:

| Frame | Film | Bar |
|---|---|---|
| 9.0 s vs orchard3 | <40 20.9 %, >200 24.8 %, R-B 0, black mass 14.7 %, corner/centre 0.31 | met |
| 25.0 s vs AK08 | sat 0.275, <40 17.8 % | sat > 0.25 met; staging is still frontal, not a side elevation |
| 41.0 s vs AK17 | sat 0.086, >200 0.9 % | met |

## Remaining deviations and weaknesses

- **V2·B is still a frontal doorway, not AK08's side elevation.** The Highsmith region has no profile view of the door. The strike is made legible by the head drive and the paint chips instead. The bird sits at the left of the frame because the saturated brick fills the right.
- **The 1959 plate is still the soft Rizzuto print, enlarged about 1.8x in B.** It is crisper only through framing and removed grain. No sharpening was applied.
- **Two roosters.** 1959, V3 and D use the 1870s rooster; 2009 uses Highsmith's colour rooster. Commons is still rate-limited (HTTP 429), so the Leghorn hen and the CC0 Korean cock could not be fetched. The colour cut-out shows a seam at the neck.
- **The 2009 hollow knock is still handmade** (the 1959 strike plus a panel resonance). The CC BY-SA hollow-door file never downloaded.
- **No fresh muted-viewer test was run.** Legibility is the editor's own judgement from stills.
- **The 9.0 s compare frame is the insert;** grain is off there.

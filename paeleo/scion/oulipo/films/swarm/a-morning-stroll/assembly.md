# A Morning Stroll: assembly (editor), plan-r1 / score-r1, repair round 2 (r3)

- **Script:** `films/a-morning-stroll.py`, using `kit.Film` at 960x540 and 24 fps. kit.py is not edited.
- **Render:** `assets/films/a-morning-stroll.mp4`, 68.0 s.
- **Checks:** `python3 films/a-morning-stroll.py --report` re-runs the assertions and rewrites `ledger.json` and the three `compare-*.jpg` sheets.
- **Direction:** Direction 1, "Rizzuto Stoop", unchanged.

The film is assembled from the units' outputs:
- **Plates, crops, mattes, geometry and grades:** `plates.json` (U1).
- **The FK rooster, tracks, shadows, door mechanisms and 2059 state machine:** `puppet.py` and `knockproof.py` (U2), imported as modules.
- **Stems:** `sound.json` (U3), placed with `mix.add`.

## Repair round 2 (r3): what changed

| Review item | Fix | Measured now |
|---|---|---|
| V2: no chain on screen; the 25 deg stop does not read; the C wide looks closed | The chain was drawn at y 838 (region px), above the old B crop. V2-B is now three framings. **B1** (24.0-26.25) is the strike framing, moved 20 px left so the tail clears the frame edge. **Chain insert** (26.25-27.5, 3x, region (322,748)-(642,928)) shows the knob, latch edge, jamb and the HANDMADE 7-link chain (`chain_link_face/edge.png`). The chain has a fixed length: it hangs slack while the leaf swings, goes straight at 26.6, and the leaf halts with the 4 % bounce of `P.chain_theta`, on the "chain snaps taut" cue. **B2** (27.5-30.0, the full leaf, region (0,780)-(933,1305)) shows the leaf held ajar with the chain across the gap while the bird walks in under it. **V2-C** draws the same chain at the 25 deg stop in the wide. | `ledger.json` V2 `chain_on_screen`: chain px 2466 / 2740 / 2580 at 26.3 / 26.5 / 26.8 (insert); 304 at 29.0 (B2); 31-32 at 31.0 and 33.5 (C wide). Door 25.0 deg from 26.6 to 34.0. Asserted > 0. |
| 2009 knock was a filtered copy of the 1959 wood knock | Foraged: Commons "File:Knocking on wood or door.ogg" (stephan via PDSounds, Public domain, from extmetadata). One knuckle strike on a door (source 4.640-4.849 s), band 120-7000 Hz, +2 st; strike 2 is the same strike +3 st. The CC BY-SA "Shave and a haircut" file had its metadata read, but the file got HTTP 429 again, so it is not used. Onsets are unchanged (25.000 / 25.320). The stem's onset detector for 2009 now uses a 150 Hz band, and the matched-filter lag was widened (measurement fixes only). | Timbre ladder by spectral centroid: 1959 beak on wood 1581 Hz; 2009 hollow door 471 Hz (peak 325 Hz, 79 % of energy below 400 Hz); 2059 glass 3458 Hz. Final-mix onsets 9.002/9.321, 25.003/25.322, 40.999/41.320, 57.002/57.321. Matched filter 3.0 st in all stems (correlation 0.89 / 0.99 / 0.96). |
| 2009 saturation | B1 keeps the brick-dominant framing. | 25.0 s: sat 0.262 (bar 0.25) |
| 2059: no dark mass; interior edge-hardened | The stopped watcher's long low-sun shadow is now in V3-B as well, in the same world position as A/C (it was missing from B, a continuity gap). Density is 0.68 (was 0.55). The far hall seen once the glass opens is defocused (Gaussian, sigma 1.1), which removes the thumbnail's edge sharpening. | 41.0 s: <40 7.0 % (was 1.8), largest dark mass 5.3 % (was 0.1), sat 0.086, >200 0.9 % |
| Credits wording | Rizzuto: "No known restrictions on publication (LoC, Anthony Angel Collection, rights statement 730_ange)"; PD not claimed (730_ange page HTTP 403). Formations: "Jam Handy Organization for Chevrolet Motor Company (sponsor)". New record: the PD door knock. | 12 records |
| sound.json stale evidence | The four Prelinger records now carry the archive.org licenseurl (publicdomain). Straight Talk (1992) is moved to `dropped_evidence` (not in any stem). Added `repair_r3_editor`. | |
| Note | Now lists "street, room, latch and footstep sound" and the PD door knock. | 103 words |

Publishing note (reviewer): put the full TASL for Plennert in any public description: "Automatische Schiebetüre mit Schlüsselsäule" by Plennert, https://commons.wikimedia.org/wiki/File:Automatische_Schiebet%C3%BCre_mit_Schl%C3%BCssels%C3%A4ule.jpg, CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0). Keep `compare-*.jpg` internal: they contain the Studio AKA reference stills.

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
| 24.0-30.0 | V2·B | B1 24.0-26.25, region crop (380,1006)-(913,1306) → hall → leaf by homography (`chain_theta`) → bird shadows → bird → pale-blue paint chips. **E3 25.00 / E4 25.333.** Chain insert 26.25-27.5 (3x on the knob and gap): the HANDMADE chain hangs slack, goes taut at 26.6 and the leaf halts at 25 deg. B2 27.5-30.0, full leaf (0,780)-(933,1305): the leaf held ajar on the chain; the bird walks in under it (jamb holdout) and is gone by 29.0. | as above; sound Commons Knocking_on_wood_or_door (PD) +3 st, DatingDo1949 latch, handmade creak and chain ticks |
| 30.0-34.0 | V2·C | wide; the leaf held ajar at 25 deg with the HANDMADE chain across the gap (same geometry as B) | as V2·A |
| 34.0-35.0 | Card "2059 / plate photographed 2022; staged" | | |
| 35.0-40.0 | V3·A | Commons Schiebetür (Plennert, CC BY-SA 4.0), locked off → long low-sun watcher shadow (64 % of height) → toned 1870s rooster walks the forecourt → threshold → posts and pillar → HANDMADE 7-dot strip. **X1 39.6:** one peck at the tread; dot 1 lights and refuses. | commons-schiebetuer, loc-stereo-1s08734, loc-owi; sound handmade hum, wind, denied tone |
| 40.0-46.0 | V3·B | interior (defocused, sigma 1.1) → the watcher's long shadow (r3, continuous with A) → bird → sliding leaves (`DoorFSM`) → threshold → posts and pillar → strip → glass glint at the beak. **E3 41.00 / E4 41.333**: two dots, chime, slide. The bird is hidden behind the pillar by 45.0. | as above; handmade glass tap, chime, slide |
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
| 25.0 s vs AK08 | sat 0.262, <40 17.3 % | sat > 0.25 met; staging is still frontal, not a side elevation |
| 41.0 s vs AK17 | sat 0.086, >200 0.9 %, <40 7.0 %, dark mass 5.3 % | met |

## Remaining deviations and weaknesses

- **V2 is still a frontal doorway, not AK08's side elevation (reviewer condition 6, unmet).** The 2009 Highsmith plate has no profile view, and no 2005-2012 side-elevation stoop with an open licence was found in the time budget. The Highsmith region has no profile view of the door. The strike is made legible by the head drive and the paint chips instead. The bird sits at the left of the frame because the saturated brick fills the right.
- **The 1959 plate is still the soft Rizzuto print, enlarged about 1.8x in B.** It is crisper only through framing and removed grain. No sharpening was applied.
- **Two roosters.** 1959, V3 and D use the 1870s rooster; 2009 uses Highsmith's colour rooster. Commons is still rate-limited (HTTP 429), so the Leghorn hen and the CC0 Korean cock could not be fetched. The colour cut-out shows a seam at the neck.
- **The 2009 knock is now foraged** (PD door knock). The 2059 glass tap, creak, chain, slide and chime are still handmade; no clucks.
- **In the C wide the chain is small** (about 31 px). The gap reads as dark, and the chain is plain in the insert and in B2.
- **No fresh muted-viewer test was run.** Legibility is the editor's own judgement from stills.
- **The 9.0 s compare frame is the insert;** grain is off there.

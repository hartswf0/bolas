# A Morning Stroll: assembly (editor), plan-r1 / score-r1

- **Script:** `films/a-morning-stroll.py`, using `kit.Film` at 960x540 and 24 fps. kit.py is not edited.
- **Render:** `assets/films/a-morning-stroll.mp4`, 68.0 s.
- **Checks:** `python3 films/a-morning-stroll.py --report` re-runs the assertions and rewrites `ledger.json` and the three `compare-*.jpg` sheets.
- **Direction:** Direction 1, "Rizzuto Stoop", unchanged.

The film is assembled from the units' outputs:
- **Plates, crops, mattes, geometry and grades:** `plates.json` (U1).
- **The FK rooster, tracks, shadows, door mechanisms and 2059 state machine:** `puppet.py` and `knockproof.py` (U2), imported as modules.
- **Stems:** `sound.json` (U3), placed with `mix.add`.

## Timecoded sequence and evidence

| Global | Segment | On screen (layer DAG) | Evidence IDs |
|---|---|---|---|
| 0.0–2.0 | Title | "A MORNING STROLL / after Grant Orchard (2011)" in kit sans, white on #141414 | handmade; sound `title_tail.wav` (mia-ee12b007 room tone) |
| 2.0–3.0 | Card 1959 | Year card | sound: v1 stem 13.9–15.0 s as lead-in |
| 3.0–8.0 | V1·A | `plate_graded` crop A with the 1.5 % push → watcher cast shadow (OWI silhouette, light 0.85/−0.53) → bird cast shadow broken at the riser below plus contact shadow → FK rooster (`track_climb` hop cycle, one tread per 8 frames on twos, N6→N5→N4→N3, out of frame at 4.5 s local) → `holdout_A_iron` re-pasted in front → vignette → kit grain. E2: the watcher stops at 6.5 and turns its head 14°. | loc-ppmsca.70651, loc-stereo-1s08734, loc-owi-2017861981; sound v1 (mia-14c8b94b, mia-6eb03e7f, mia-ee12b007, mia-a267fee7 footsteps) |
| 8.0–14.0 | V1·B | `knockproof.compose` (U2's approved knock), re-based on story-plates' unify grade: plate → hall → hinged leaf (homography, unseen hand) → cast shadow on the leaf → bird → iron → jamb holdout → vignette. Insert on beak and leaf at 8.67–9.75 (widened 0.85x to keep the black recess). **E3 9.00 / E4 9.333**, door swings 10.0–11.5, bird leaps into the hall and is gone behind the jamb by 13.0. | loc-ppmsca.70651, loc-stereo-1s08734; sound commons-Knock_on_door (+3 st), mia-a267fee7 latch, handmade creak |
| 14.0–18.0 | V1·C | Crop A again, an empty stoop; the watcher's shadow resumes at 14.0 and slides out right | as V1·A |
| 18.0–19.0 | Card 2009 | | v2 stem lead-in |
| 19.0–24.0 | V2·A | `preview_graded` (highsm.56276), crop A with the push → watcher's short shadow at the right edge → rooster (2009 unify) hops sidewalk → 5 treads → landing (6 hops, 0.5–4.0 s local) → iron holdout (region → preview affine) | loc-highsm.56276, loc-stereo-1s08734, loc-owi-2017861981; sound v2 (mia-93053686 bed, handmade car swells) |
| 24.0–30.0 | V2·B | `region_graded`, framed (0,790)–(933,1315) so the chain shows → hall where the leaf swung → leaf by homography about the hinge (`chain_theta`: stops at 25° with a damped bounce, 26.0–26.6) → bird cast and contact shadow → bird (only the gap shows it once it enters; `holdout_jamb_right`) → HANDMADE 6-link chain (`chain_links` catenary, slack to taut) across the gap. **E3 25.00 / E4 25.333** on the kick plate. The bird walks into the gap and is gone behind the jamb at 29.0. | loc-highsm.56276, loc-stereo-1s08734; sound: handmade hollow knock (commons-Knock_on_door + panel resonance), handmade chain ticks |
| 30.0–34.0 | V2·C | Wide again with the leaf left ajar at 25° in the A view; the watcher's shadow leaves | as V2·A |
| 34.0–35.0 | Card 2059 | | v3 stem lead-in |
| 35.0–40.0 | V3·A | `plate_graded` (Commons Schiebetür), crop A, locked off (no push) → AK17 long low-sun watcher shadow (light 0.30/−0.95, 64 % of frame height) → bird walks the forecourt (walk cycle on twos) → threshold → posts and pillar → HANDMADE 7-dot strip. **X1 39.6:** one peck on the glass, dot 1 lights, refuses and blinks off; the door stays shut. | commons-schiebetuer, loc-stereo-1s08734, loc-owi-2017861981; sound v3 (handmade hum and wind, glass tap, "denied" tone) |
| 40.0–46.0 | V3·B | Crop (400,180)–(1440,765) → interior (the plate's through-glass view with the stiles inpainted, HANDMADE) → bird inside → the two leaves slide on their rails (`DoorFSM` + `slide_offset`, start 42.01) with the bird behind the glass at 45 % → threshold → bird outside → posts and pillar holdouts → strip. **E3 41.00 / E4 41.333** taps on glass, two dots lit, then chime and slide; the bird hops the threshold rail and walks behind the glass and the key pillar, 0 px by 45.0; the leaves close from 45.2. | commons-schiebetuer, loc-stereo-1s08734; sound: handmade glass tap, chime (880 → 1046.5 Hz) and air slide |
| 46.0–50.0 | V3·C | Wide; the door is shut, the dots dark, and the long shadow leaves right | as V3·A |
| 50.0–51.0 | Card "1959 / diagnostic: silhouette" | | v1 stem lead-in |
| 51.0–66.0 | D | The same V1 score, tracks and cameras as Reiniger black-card theatre on backlit warm paper:<br>• A/C: the stoop traced from the tread-nose polylines, the shadow side as one card, the lace iron as card from `holdout_A_iron`, the watcher as a grey gel shadow, and the rooster as black card with grey split pins at its FK pivots.<br>• B: the door is a card with its panel mouldings cut as a stencil from the plate, swung by the same homography, with the lamp showing through the open doorway.<br>**E3 57.00 / E4 57.333.** | loc-ppmsca.70651 (tread lines and masks only), loc-stereo-1s08734 (mask only), loc-owi-2017861981 (mask only); sound: identical v1 stem |
| 66.0–68.0 | End card | "Foraged: Library of Congress, Wikimedia Commons, movingimagearchive.com / See credits. Handmade: …" | v1 stem 12.5–14.5 s, faded |

## Ledger and claim graph (plan §9 and §10)

`ledger.json` holds one manifest per version (V1, V2, V3, D):
- separate `era`, `genre_tone` and `render_technique` fields;
- E1–E7 with the same local frame numbers in every version (asserted);
- measured checks.

**Asserted in code** (`report()` fails if any is false):

| Claim | V1 | V2 | V3 | D | How |
|---|---|---|---|---|---|
| E3/E4 global frames | 216/224 (9.0/9.333) | 600/608 (25.0/25.333) | 984/992 (41.0/41.333) | 1368/1376 (57.0/57.333) | assert against beatmap.json; E4 − E3 = 8 frames |
| Beak tip inside the door-leaf mask on E3 and E4 | yes (`leaf0`, iron excluded) | yes (`piece_leaf`) | yes (`piece_leaf_left`) | yes (same track as V1) | measured: posed beak landmark → stage → mask |
| 0 bird px past the jamb at E6 end (local 10.0) | 0 | 0 | 0 (behind post and pillar) | 0 | measured on the composite; monotone fade, see `visible_px_f204_to_f240_step4` |
| X1, V3 only | — | — | dot 1 lit from 39.63 (listening), refused at 40.13, slide 0 | — | `DoorFSM` trace in the ledger |
| Watcher shadow ≥ 40 % of frame height, V3·A | — | — | 0.64 | — | measured |

**Comparison sheets** (`compare-*.jpg`, PIL measures in `ledger.json` → `compare`):

| Frame | Film | Reference | Bar |
|---|---|---|---|
| 9.0 s vs orchard3 | <40 22.5 %, >200 20.3 %, R−B 0.0, largest black mass 17.3 %, corner/centre 0.24, bird 36.7 % of frame height | <40 21 %, >200 35 %, corner/centre 0.09 | all numeric bars met; >200 is just over 20 % |
| 25.0 s vs AK08 | sat 0.22, R−B +17 | sat 0.28 | **misses sat > 0.25.** The close on the pale-blue door is the least saturated part of the plate. Shot A measures 0.37. No crop of the region exceeds 0.231 and no saturation filter was applied. |
| 41.0 s vs AK17 | sat 0.087, >200 0.9 % | sat 0.25, >200 2.3 % | met (cool and desaturated); film darks are lighter than AK17's (<40 only 1.9 %) |

The `≥3 distinct joint configurations within 1 s of E3` claim is supported by the per-frame pose keys (cock, strike, recoil, hold) in each manifest. Bone-length invariance (0.0 px) comes from `puppet.json`. The same FK code renders every version.

## Deviations from the plan (and why)

- **V1·B is U2's knock-proof composite, not a rebuild on story-plates' new B crop.** It is the approved test shot, and it passes the beak and jamb tests. Two changes:
  - It now uses story-plates' unify grade, so one curve covers A, B and C.
  - The insert is widened to keep the black recess in frame, which lifts <40 at 9.0 s from about 6 % to 22.5 %.
- **The V2·B framing differs from story-plates'.** It is (0,790)–(933,1315) so that the handmade chain (placed at y 842, just above the knob) is in frame.
- **The V3 interior is not story-plates' `interior_opening.png`.** That file kept the meeting stile and had a min-filter texture. I rebuilt the interior from the plate with the frame members inpainted (handmade).
- **V3 entry:** the bird hops the threshold and is hidden behind the right post and the key pillar. The pillar plays the "jamb" for the 0-px assertion.
- **Grain:** kit's grain (std ≈ 4 plus fibre) is applied only to V1 and D (the silver print and the paper theatre), after the vignette rather than before. The digital plates and the cards carry no added grain.
- **The V3 wides (A/C) are locked off with no push.** That is the reference's static camera. With the push, resampling the terrazzo plate every frame cost about 2.5 MB of codec noise and took the file to 7.3 MB.
- **The V3 interior is darkened to ×0.66** so that the open doorway reads as an opening. The 1959 vignette is story-plates' `vignette_960x540.png` in A/C and U2's lens fall-off in B.

## Render

- `assets/films/a-morning-stroll.mp4`: 68.0 s, 4.5 MB (crf 28, AAC 96k).
- Poster at 9.0 s.
- Assertions pass (`--report`).

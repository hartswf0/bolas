# Exercices de style: assembly (montage editor)

- **Script:** `films/exercices-de-style.py` (new; `kit.py` not edited).
- **Output:** `assets/films/exercices-de-style.mp4`: 74.25 s, 960×540, 24 fps, 1,838,548 B (1.8 MB). Audio mean −26.9 dB, max −3.9 dB; silences only 0–1.03 s (room-tone fade-in) and 71.19–74.25 s (declared). Poster at 58.667 s.
- **Repair round 1 (2026-11-17):** see the section *Repair round 1* at the end.
- **Inputs:** `anim/es_lib.py` (page grammar and handmade objects); `anim/exposure.json` (all motion); `incident/anthology.json` (texts and timing, rev `910a7b36…`); `incident/coverage.json` (S6 table). S5c–S5d are the approved test shot, imported from `anim/test_shot_s5c.py`.
- **Checks run by the script on every run:**
  - `incident/verify.py` exits 0.
  - The timing fixtures pass.
  - INV-DOOR is asserted during render on every 6th frame.
- **Commands:** `--check` runs the full door sweep; `--sheets` writes the two comparison stills.

## Timing: the anthology's revision, not plan §7

The film follows the anthology's `timing_revision`: S5 is 46.0–68.25 and S6 is 68.25–74.25, for 74.25 s in total (plan §7 has 66 s).
- **Why:** the eight key captions need 16 s of typing at 14 chars/s.
- **What is unchanged:** S0–S4 keep the windows in §7.
- **Knock-on effect, now formally restated:** plan.md §10-R1 re-anchors the bar's S5 numbers to the S5c start (the original 54.0 s = 51.5 + 2.5 s → 58.667 s = 56.167 + 2.5 s): key still before 58.667 s, beat-5 pair at 11.0 vs 58.667 s, aesthetic frame 58.667 s. Pending the critic's sign-off.

## Timecoded sequence

| t (s) | shot | on screen | heard | evidence IDs |
|---|---|---|---|---|
| 0.0–3.0 | **S0 Titre** | Butter page; ghost « Gare » drifts 20 px; « Une gare, six faits » sets letter by letter at 14 chars/s in mixed red/black faces; band « d'après Raymond Queneau · cinq manières »; six blank strip cells | Room tone fades in | room_tone; handmade page |
| 3.0–13.0 | **S1 Le registre (baseline)** | Page-turn wipe. Berlin platform vignette; cut-paper bench; THE door at (800,100). The visitor does E1–E6 from `exposure.json` S1: walks in, looks up, tears, holds up the key, places it with no settle at 9.93, walks out. Register lines set whole and accumulate; band clock 18:00 → 18:07 | Footsteps on the walk-in contacts; bell ×3 at 4.9; tear (synth) 6.6; tick + thud 9.93; steps on walk-out contacts | rol57642, key_rex, station, bell, steps, thud, kit synth |
| 13.0–24.0 | **S2 Journal à rebours** | Rubric « porte de service : fermée, de 18:07 à 18:00 ». Tableau card (now 370×208) replays each beat forward 1.2 s, newest first. Red stamps 18:07 → 18:00, text types. **Arrows 21.6–22.45**, one every 0.13 s, 8 drawings each, upward cause → effect; E2→E3 in round red dots every 7 px with a wider bulge and a 16 px « incertain ». **Finished arrows held 1.55 s** before the 24.0 wipe | Events in reverse order, each forward: receding steps 13.2, tick + thud 14.7, tear 17.5, bell ×3 19.0, arriving steps 20.2; pen scratch per arrow | rol57642, station, bell, steps, thud, kit synth |
| 24.0–36.0 | **S3 Inventaire des sens** | GUICHET 3, frosted pane; Reiniger silhouette (mattes of the rol57642 pieces as flat cards), now 280 px tall, blurred 5 → 9 px. From 25.6 he **holds the envelope out at arm's length, a flat 40×26 px black card** clear of the coat; at 28.2 it loses a jagged top strip (torn); gone at 29.6. **Bell onset frame 634 (26.417 s): head tilts −26° over 3 frames with a −8° overshoot over 6, and the whole body starts up 12 px (+5 overshoot)**. Glint 29.75–30.25, never a key shape. « NON PERÇU » red 33.0–36.0 | Steps, bell ×3, tear, metal on wood, receding steps, all low-passed 1.3 kHz | rol57642 (rotoscoped), bell, steps, thud; handmade guichet, pane, card |
| 36.0–46.0 | **S4 Avis** | Empty six-field grid from 36.2; fields fill 0.15 s each from 37.7; footnote « cloche : consignée, non entendue » 43.6. Key drops 40 px at 42.45 and settles **beside the card at x 765** with the drawn clip; **stamp « SUITE DONNÉE : NÉANT » at 44.0 sits below the table, straddling the card edge (centre 598,393, −4°)**: no field cell is covered | Typewriter click per field (synth); tick on landing; thud for the stamp; **no bell** (declared) | key_rex, thud, kit synth |
| 46.0–51.5 | **S5a Dans l'enveloppe** | Envelope interior; ghost « Je »; cream captions key.1–2 type | Steps low-passed 300 Hz; bell ×3 low-passed 420 Hz | bell, steps; handmade envelope |
| 51.5–56.167 | **S5b La déchirure** | Straight-ahead Tear (re-cut every 2 frames, 40 frames); his own sleeve + hand reaches in (0.8 → 1.7×); envelope slides away from 55.0; captions key.3–4 | Tear crackle (synth) | rol57642 (arm), handmade tear |
| 56.167–66.25 | **S5c TEST SHOT** | **The visitor stands in full figure behind the bench from the first frame** (no rise). The close-up of his arm lowers the key: contact frame 30 (57.417), 6° → 0 settle with one 3 px bounce, still from 57.834. Released on frame 32, **the arm folds back into him over 22 frames** (fingertip, angle and scale tween to his own arm pin, geometric scale, clipped behind the bench lip), and on frame 54 his own arm piece takes over with the same transform. Walk from 58.667: 19 contacts, exits frame 222 (65.417). **Bounding-box height non-increasing on every frame 57.417–65.4 s (232 → 139 px, asserted)**. Parallax bench 1.0 > figure/door 0.55 > ghost 0.25. Door now at y 36, wholly above the bench lip | Thud + tick on the landing frame, bounce tick frame 4; one footstep grain per contact, low-passed and quieter with distance | rol57642, key_rex, steps, thud, bell (strip cell 2) |
| 66.25–68.25 | **S5d** | Key alone on the bench, door shut, captions held | Room tone | – |
| 68.25–74.25 | **S6 Matrice** | Table from `coverage.json` cell for cell; new small line « photographies d'archives (Agence Rol, 1920 ; Berlin, 1927) : rôles inventés » | One bell stroke 68.25; declared silence 71.25 | bell |

## Ledger / claim graph (deliverable §9)

- **Facts.** `incident/ledger.json` rev `910a7b36c16021d78f308a66d4f84ce71d6bdad1d1b9ddc37da43e235e6f52c9`:
  - E1 arrive 18:00, E2 cloche 18:02, E3 ouvre 18:04, E4 trouve 18:05, E5 laisse 18:06, E6 s'en va 18:07;
  - F7 porte fermée 18:00–18:07.
- **Edges.** E1 →enable E3, E3 →enable E4, E4 →enable E5, E5 →precede E6, and E2 →cue E3 (uncertain, drawn dotted).
- **Claims → events.** Per variant in `anthology.json`:
  - baseline.1–7 → E1..E6, F7;
  - rev.0 → F7, rev.1–6 → E6..E1;
  - sense.1–6 → E1..E6+F7 as percepts, sense.7 omits E4 and E5 (no access);
  - notice.1–6 → E1..E6 (+F7 in row 6), notice.n → E2;
  - key.1–8 → E1, E2, E3, E4, E5, E5, E6, F7.
- **Screen = data.**
  - The S6 table is rendered from `coverage.json` `matrix`, so it equals it cell for cell.
  - The S2 arrows come from `anthology.rev.arrows`. The script asserts that they equal the ledger edges, all drawn upward (`y_from > y_to`).
- **Verifier.** `verify.py` reports OK, and the four counterexample fixtures are rejected (NEW_ENDING ×2, EDGE_REVERSED ×2).

## Assertions in the script (`timing_fixtures`, `check_door`)

**Timing fixtures:**
- Contiguous shot schedule, total 74.25 s (between 60 and 75).
- Reverse-log stamps strictly decrease.
- Arrows equal the ledger edges and point up.
- S3 head-up frame 634 equals the bell frame 634 (tolerance ±2).
- NON PERÇU held 3.0 s (needs ≥ 2), and « clé » appears nowhere in S3.
- Empty grid shown 1.5 s (needs ≥ 1), and every row has exactly six fields.
- Landing at 57.417 against the anthology's 57.334 (2 frames, within tolerance).
- Still at 57.834, before 58.667 (S5c + 2.5 s, plan §10-R1).
- At least 8 distinct settle frames.
- The visitor is present from frame 0; his scale and his unoccluded bounding-box height never increase (57.417–65.4 s).
- Every key caption falls inside S5.

**INV-DOOR:** SHA-256 of the door's fully opaque pixels cropped from each checked frame, compared with the asset. The S5c door was moved from y 52 to y 36 so it is no longer occluded by the bench lip: **one hash, `ca782e636a38ec28`, everywhere** (S1, S2, S5c, S5d; page-turn wipe frames skipped). The script asserts the door sits wholly above the lip. As the critic noted, this is a render-time assertion; h264 output is lossy and cannot carry it.

## Aesthetic measurements (`aesthetic-measure.json`, sheet `films/stills/exercices-de-style-aesthetic.jpg`)

Page median over page-like pixels above the band (as the critic measured), band median over the band.

| frame | page | ΔE76 from #fddb8c | page-like share | band ΔE76 from #8e847b |
|---|---|---|---|---|
| 2.0 s | #fbdc8e | 1.43 | 97 % | 0.39 |
| 8.0 s | #fbdc8f | 1.71 | 71 % | 0.39 |
| 30.0 s | #fbdc8e | 1.43 | 38 % | 0.39 |
| 40.0 s | #fbda8c | 0.77 | 35 % | 0.39 |
| 58.667 s (S5c + 2.5 s, bar's 54.0 re-anchored) | #fbdd90 | 2.13 | 64 % | 0.39 |

- Title red #d6280a exactly; ghost #fdefb1, lighter than the page.
- **Beat-5 pair still:** `films/stills/exercices-de-style-beat5-pair.jpg`, S1 at 11.0 s against S5c at 58.667 s: key still, visitor in full figure behind it, same bench colours and door.

## Reader test (§10.8)

- Sheet prepared: `swarm/exercices-de-style/reader-test-unlabeled.jpg`, five frames with titles and bands masked, shuffled (key: A S3 sense, B S1 baseline, C S5 key, D S2 rev, E S4 notice).
- **Not run with an independent reader.** No fresh reader was available to this unit (no subagent or human). The editor's own answers are not blind, so they are recorded only as the prediction to test: stable fact = the service door stays shut and the key is left on the bench; detail that gained force = « Sa main était tiède » (S5) and the NON PERÇU omission (S3); most redundant pair = baseline / notice. **Open item for the critic:** show the sheet to a reader who has not seen the plan and record the three answers here.

## Repair round 1: what changed

- **S5c rise removed** (`anim/exposure.py` S5c visitor; `anim/test_shot_s5c.py` hand_layer/visitor_layer; `es_lib.Visitor.draw` gains `own_arm`): the visitor is there from frame 0; the close-up arm folds back into him; bbox height asserted non-increasing per frame.
- **Bar re-anchored formally** in plan.md §10-R1 and in `anthology.json` (`test_shot.beat5_pair_frame_s` = `settle_done_by_s` = 58.667, `bar_revision`), via `incident/build_incident.py`; `verify.py` still 342 passed, 0 failed, all four fixtures rejected.
- **Provenance reconciled:** `forage/evidence.json` rewritten from what the three scripts open (7 items: rol57642, key_rex, station, bell, room_tone, steps, thud); Bain LC-B2-623-4, Bain 04410v, loc_05494v, Rol 49112 and the old steps moved to `not_used_on_screen`; the false claim that the Rol 49112 forearm lowers the key is gone. `anim/exposure.json` no longer keeps its own evidence copy. Credits are the same seven items plus the declared kit synth.
- **Licences read from source metadata:** bell and room tone from archive.org (Prelinger, licenseurl creativecommons.org/licenses/publicdomain/, with creator and sponsor); Berlin from archive.org (Public Domain Mark 1.0, Ruttmann); Rol 57642, Rex key and Dull thud re-read from the Commons API on 2026-11-17. Records saved in `sources/exercices-de-style/editor/dl/*.meta.json` and `commons_meta.json`.
- **ShareAlike removed:** the CC BY-SA 4.0 steps are replaced by one CC BY 4.0 footfall (Gravity Sound, Commons), so no ShareAlike licence is imposed on the film.
- **S3:** envelope card, larger silhouette, a clear head-up with body start at the bell frame.
- **S2:** dotted arc distinct, label 16 px, arrows held 1.55 s.
- **S4:** stamp and key/clip off the field cells.
- **Door:** one hash.
- **Note** names the 1947 belfry frame and the rotoscoped shadow; S6 carries an on-screen « rôles inventés » line.

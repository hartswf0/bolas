# Exercices de style: assembly (montage editor)

- **Script:** `films/exercices-de-style.py` (`kit.py` not edited).
- **Output:** `assets/films/exercices-de-style.mp4`: **69.75 s**, 960×540, 24 fps, **1,745,296 B** (1.7 MB). Audio mean −26.7 dB, max −3.9 dB; silencedetect (−50 dB) finds only 0–1.03 s (room-tone fade-in) and 66.69–69.75 s (declared silence from 66.75 s; the bell's tail drops under −50 dB 0.06 s early). Poster at 54.0 s.
- **Repair rounds:** see *Repair round 2* and *Repair round 1* at the end.
- **Inputs:** `anim/es_lib.py` (page grammar and handmade objects); `anim/exposure.json` (all motion); `incident/anthology.json` (texts and timing, rev `910a7b36…`); `incident/coverage.json` (S6 table). S5c–S5d are the test shot, imported from `anim/test_shot_s5c.py`.
- **Checks run by the script on every run:** `incident/verify.py` exits 0 (342 passed, 0 failed, four fixtures rejected); the timing fixtures pass; INV-DOOR is asserted during render on every 6th frame (`--check` sweeps every 6th frame of the whole film: one hash `ca782e636a38ec28`).
- **Commands:** `--check` (door sweep), `--sheets` (beat-5 pair + aesthetic sheet), `--stills t…`.

## Timing: the bar as written (repair 2)

The round-1 re-anchor (plan §10-R1 → 58.667 s) is **withdrawn**; plan.md §10-R1 now says so. The anthology's repair-2 `timing_revision` keeps S0–S4 and the S5c start exactly as plan §7: S5a 46.0–49.333, S5b 49.333–51.5, **S5c from 51.5**. The key lands at **52.75 s** (frame 30 of S5c), settles over 10 frames (6° → 0, one 3 px bounce, ≥ 8 distinct drawings) and is **still from 53.167 s, before 54.0 s**. The camera drift now starts at S5c + 2.6 s (54.1 s), so the key layer is identical, pose and position, from 53.167 s to 54.1 s: the 53.9 → 54.0 s frame difference is confined to the visitor's first walk drawing (x 556–661). Beat-5 pair: **S1 11.0 s vs S5c 54.0 s**. S5c runs on to 61.75 s only so the visitor exits (frame 222, 60.75 s) and key.6–key.8 type at 14 chars/s; S5d 61.75–63.75; S6 63.75–69.75.

## Timecoded sequence

| t (s) | shot | on screen | heard | evidence IDs |
|---|---|---|---|---|
| 0.0–3.0 | **S0 Titre** | Butter page; ghost « Gare » drifts 20 px; « Une gare, six faits » sets letter by letter at 14 chars/s in mixed red/black faces; band « d'après Raymond Queneau · cinq manières »; six blank strip cells | Room tone fades in | room_tone; handmade page |
| 3.0–13.0 | **S1 Le registre (baseline)** | Page-turn wipe. Berlin platform vignette; cut-paper bench; THE door at (800,100). The visitor does E1–E6 from `exposure.json` S1: walks in, looks up, tears, holds up the key, places it with no settle at 9.93, walks out. Register lines set whole and accumulate; band clock 18:00 → 18:07. **Disclosure under the vignette, 3.0–13.0 s, 14 px warm black: « personnages et lieu : archives, rôles inventés »** | Footsteps on the walk-in contacts; bell ×3 at 4.9; tear (synth) 6.6; tick + thud 9.93; steps on walk-out contacts | rol57642, key_rex, station, bell, steps, thud, kit synth |
| 13.0–24.0 | **S2 Journal à rebours** | Rubric « porte de service : fermée, de 18:07 à 18:00 ». Tableau card (now 370×208) replays each beat forward 1.2 s, newest first. Red stamps 18:07 → 18:00, text types. **Arrows 21.6–22.45**, one every 0.13 s, 8 drawings each, upward cause → effect; E2→E3 in round red dots every 7 px with a wider bulge and a 16 px « incertain ». **Finished arrows held 1.55 s** before the 24.0 wipe. Strip: six equal 64 px cells, each now centred on the visitor inside its tableau and kept inside the card (no figure cut by a cell edge) | Events in reverse order, each forward: receding steps 13.2, tick + thud 14.7, tear 17.5, bell ×3 19.0, arriving steps 20.2; pen scratch per arrow | rol57642, station, bell, steps, thud, kit synth |
| 24.0–36.0 | **S3 Inventaire des sens** | GUICHET 3, frosted pane; Reiniger silhouette (mattes of the rol57642 pieces as flat cards), now 280 px tall, blurred 5 → 9 px. From 25.6 he **holds the envelope out at arm's length, a flat 40×26 px black card** clear of the coat; at 28.2 it loses a jagged top strip (torn); gone at 29.6. **Bell onset frame 634 (26.417 s): head tilts −26° over 3 frames with a −8° overshoot over 6, and the whole body starts up 12 px (+5 overshoot)**. Glint 29.75–30.25, never a key shape. « NON PERÇU » red 33.0–36.0 | Steps, bell ×3, tear, metal on wood, receding steps, all low-passed 1.3 kHz | rol57642 (rotoscoped), bell, steps, thud; handmade guichet, pane, card |
| 36.0–46.0 | **S4 Avis** | Title « Avis » in mixed faces: red A, black v and i on jumping baselines, red s. Empty six-field grid from 36.2, **fully clear of the wipe from 36.333 and held empty 1.57 s**; fields fill 0.15 s each from 37.9 (row 2 reads « cloche | non entendue | consignée »); footnote « cloche : consignée, non entendue » 43.6. Key drops 40 px at 42.45 and settles **beside the card at x 765** with the drawn clip; **stamp « SUITE DONNÉE : NÉANT » at 44.0 sits below the table, straddling the card edge (centre 598,393, −4°)**: no field cell is covered | Typewriter click per field (synth); tick on landing; thud for the stamp; **no bell** (declared) | key_rex, thud, kit synth |
| 46.0–49.333 | **S5a Dans l'enveloppe** | Envelope interior; ghost « Je »; cream captions key.1 « Je ne voyais rien. », key.2 « Une cloche, au loin. » type at 14 chars/s | Steps low-passed 300 Hz; bell ×3 low-passed 420 Hz at 47.386 | bell, steps; handmade envelope |
| 49.333–51.5 | **S5b La déchirure** | Straight-ahead Tear from 49.433 (re-cut every 2 frames, 28 frames); his own sleeve + hand reaches in from 50.65 (0.8 → 1.7×); envelope slides away 51.05–51.5; key.3 « Déchirure, et je vois. » | Tear crackle (synth) | rol57642 (arm), handmade tear |
| 51.5–61.75 | **S5c TEST SHOT** | The visitor stands in full figure behind the bench from the first frame. The close-up arm lowers the key: **contact frame 30 (52.75)**, 6° → 0 settle with one 3 px bounce, **still from 53.167**; released, the arm folds back into him over 22 frames, then his own arm piece takes over. **54.0 s: bench, door, visitor, still key** (pair frame). Walk from 54.0: 20 contacts, ≥ 19 steps, exits frame 222 (60.75). Drawn height 233 → 139 px, **non-increasing on every frame** from the landing to the exit (asserted; 0 rises this render), scale non-increasing. Parallax from 54.1: bench/key 1.0 > figure/door 0.55 > ghost 0.25. Captions key.4–key.8 at upper right, with a thin page-colour knock-out so they stay legible where the sleeve passes under them | Thud + tick on the landing frame, bounce tick 4 frames later; one footstep grain per contact, low-passed and quieter with distance | rol57642, key_rex, steps, thud, bell (strip cell 2 = belfry frame) |
| 61.75–63.75 | **S5d** | Key alone on the bench, door shut, captions held (« La porte de service n'a pas bougé. » in red) | Room tone | – |
| 63.75–69.75 | **S6 Matrice** | Table from `coverage.json` cell for cell; **disclosure** beside the strip, above the band, 15 px warm black #191304 (contrast 13.8:1 on the page), on screen 63.75–69.75: « archives : Agence Rol 1920 (photographie) ; Berlin 1927 et Communications and Our Town 1947 (films) ; rôles inventés. La clé : aquarelle d'Edna C. Rex. » | One bell stroke 63.75; declared silence 66.75 | bell |

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
- Contiguous shot schedule, total 69.75 s (between 60 and 75).
- Reverse-log stamps strictly decrease.
- Arrows equal the ledger edges and point up.
- S3 head-up frame 634 equals the bell frame 634 (tolerance ±2).
- NON PERÇU held 3.0 s (needs ≥ 2), and « clé » appears nowhere in S3.
- Empty grid shown 1.57 s after the page-turn wipe ends (asserted ≥ 1.5), and every row has exactly six fields.
- Landing at 52.75, equal to the anthology's `landing_s` 52.75.
- Still at 53.167, before `settle_done_by_s` 54.0 (the bar as written).
- At least 8 distinct settle frames.
- The visitor is present from frame 0; his scale never increases; his unoccluded drawn height may not rise by more than 1 px between drawings nor above its running minimum + 1 px, and must fall ≥ 25 % (this render: 233 → 139 px, 0 rises, i.e. strictly non-increasing).
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
| 54.0 s (S5c + 2.5 s, as the bar is written) | #fbdd90 | 2.13 | 64 % | 0.39 |

- The 54.0 s frame is the test shot (bench, door, visitor, still key), not the envelope: page ΔE76 2.13 (was 51.0 in the round-2 critique).
- Title red #d6280a exactly; ghost #fdefb1, lighter than the page.
- **Beat-5 pair still:** `films/stills/exercices-de-style-beat5-pair.jpg`, S1 at 11.0 s against S5c at 54.0 s: key still, visitor in full figure behind it, same bench colours and door.

## Reader test (§10.8)

- Sheet prepared: `swarm/exercices-de-style/reader-test-unlabeled.jpg`, five frames with titles and bands masked, shuffled (key: A S3 sense, B S1 baseline, C S5 key, D S2 rev, E S4 notice).
- **Still not run with an independent reader (repair 2).** This unit has no way to reach a person or a fresh agent: no subagent tool, and the user is not in the loop of this workflow step. The sheet's frames are unchanged in content by the retime. The editor's own answers are not blind, so they are recorded only as the prediction to test: stable fact = the service door stays shut and the key is left on the bench; detail that gained force = « Sa main était tiède » (S5) and the NON PERÇU omission (S3); most redundant pair = baseline / notice. **Open item for the critic:** show the sheet to a reader who has not seen the plan and record the three answers here.

## Repair round 2: what changed

- **Test shot on the bar's timeline (critic).** Upstream, `incident/build_incident.py` (repair 2) re-timed S5a 46.0–49.333 / S5b 49.333–51.5 with shortened S5a–S5b lines and restored `test_shot.beat5_pair_frame_s` = `settle_done_by_s` = 54.0; `anim/exposure.py` regenerated S5c from 51.5 s. This unit: the film script takes the envelope slide from the anthology (last 0.45 s of S5b, was hard-coded 55.0), the hand reach from the tear's end, the poster/pair/aesthetic frame at 54.0; `anim/exposure.py` camera drift starts at S5c + 2.6 s so the key is pixel-still (pose and position) 53.167–54.1 s; plan.md §10-R1 withdrawn. `verify.py` OK. Frame grab at 54.0 s: bench, door, visitor, still key; page ΔE76 2.13.
- **« Avis » title** set in mixed red/black faces with jumping baselines.
- **S2 strip:** six equal cells, each centred on the visitor in its tableau.
- **S4 empty grid** held 1.57 s after the wipe (asserted ≥ 1.5); the ACTION cell of row 2 no longer reads « sonnerie » (row 2: « cloche | non entendue | consignée »; upstream anthology).
- **Disclosure (reviewer).** S1 label 3.0–13.0 s under the vignette; S6 full line naming all three archives (Rol 1920 photograph; Berlin 1927 and Communications and Our Town 1947 films) and the Rex key, 15 px #191304 (13.8:1), beside the strip and unclipped, 6 s on screen. Note says « Real people and places play invented roles ».
- **Captions over the sleeve:** key captions in S5c carry a 2 px stroke in the page's own colour, so « Une main m'a sortie » stays legible while the arm passes under it.
- **Not done:** the unlabeled reader test (no independent reader reachable); the bowler (see Known weaknesses).

## Known weaknesses

- Reader test (§10.8) not run with an independent reader.
- §10.3 « bowler »: Rol 57642's hat has a rounded crown and narrow brim and reads as a bowler at film scale, but the BnF/Commons record does not name it; no catalogued PD walking man in a bowler was obtained (the Rol 1917 « Arrivée d'un homme à chapeau melon » lead was refused by Commons with HTTP 429 earlier and was not re-rigged in this round).
- The close-up sleeve that lowers the key is a 1.7× enlargement of the same print and is soft.
- S5c runs to 61.75 s, past the bar's 58.0 s window end, for the exit and typing; the bar's dated numbers (54.0 s) all hold.

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

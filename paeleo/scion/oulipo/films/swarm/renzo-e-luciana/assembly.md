# Renzo e Luciana · assembly (montage editor) — repair round 2

Film: `assets/films/renzo-e-luciana.mp4`, 72.0 s, 960×540, 24 fps. A 0–35, schedule-strip slate 35–37, B 37–72.
Script: `films/renzo-e-luciana.py` (kit.Film, kit.py unedited). Build helpers: `swarm/renzo-e-luciana/editor-build/`
(`back_cut.py` new this round; `door_clean.py`, `renzo_cut.py`; back-ups `renzo-e-luciana_r1.py`, `rig_r1.json`, `credits_r1.json`, `cues_r1.json`;
`loc_2017851145.json` = the LoC item record of the new photograph). Sound: `sound.wav` unchanged from round 1 (sound unit mix).

## What changed in repair round 2 (critic + reviewer)

| finding | repair |
|---|---|
| Foreman has no back photograph; his turn happens off screen; in MEDIUM he is cropped out | **Second real photograph, seen from behind**: Arthur S. Siegel, *Bethlehem-Fairfield shipyards… Erecting bottom shell plates*, 1943, LoC 2017851145 (No known restrictions, read from the item JSON). GrabCut (`back_cut.py`, #29) into torso+head and the raised arm (pry bar cut away). To keep **one foreman**, the back photograph wears the front photograph's hard hat and stands on the front's own legs (declared collage). He **never leaves the doorway**: FLOOR = front photograph, OFFICE = back photograph, substituted at 5.0 / 20.0 (A) and 42.0 / 57.0 (B) with a 2-frame squash each side (the cut-out turning on its feet). MEDIUM window moved to stage x 560 so the doorway, the foreman's back, the jamb and the clock are in every meeting frame. Per-frame asserts: foreman drawn and on screen in every frame; back photograph drawn iff rules facing = OFFICE. |
| Ledger said "front -> back photograph" while the film had none | Now literally true; cues.json 5.0/42.0 reworded with both LoC ids; credits record both photographs; rig.json `editor_r2` describes the rig. |
| B: Luciana eats Renzo's apple for 15 s in the foreman's view | After her bite at 55.0 (foreman still OFFICE) she bends to her pail and **drops the apple in at 55.95**; from 56.25 she stands at the clock empty-handed under his gaze (57–72), wipes her mouth at 62, punches 71.5. |
| Apple hidden by a black cross-handled object; R/L/R not legible | The stray open lid with its black hasp that stood above the near pile is cut out of the occluder piece (#45). The apple is now in clear silhouette for R 8.5, L 11.0, R 13.0. **At t = 9.92–10.5 the apple passes into Renzo's hand** (IK grip) and back to hers. |
| Seams: black left strip (WIDE), light rectangle round foreman, grey door patch (MEDIUM), neck-pin white seam | WIDE window starts at stage x 400 (the doorway print's black edge is off frame). The foreman stands exactly where the retouched-out technician stood, so his figure covers the retouch patch in both states (the "light rectangle" and the "grey patch" were that retouch). Both jambs now occlude him (#45). Front head/body pieces overlap 18 px at the neck pin (no complementary feathers → no seam). |
| Head through her face at 14.5; entrances slide rigid | 14.35–16.1 she ducks behind the pile as he rises past her. Walking now rocks the hip pin and counter-rocks the neck on each step (Renzo's arm swings on the shoulder pin), on twos; legs are below the pile line. |
| B slate was a bare letter | Restored the rule-modeler's **schedule-strip slate** (`rules.slate_frame`): Luciana's strip slides 3 minutes, the light column through all three slots closes. Staging disclosure at its foot. |
| Static 21–35 and 58–72 | Foreman: lean on the feet pin, weight shifts, a step toward camera (28.6–32.4 A; 61 B), head pans on the rules' schedule, gaze to the pile/core (25.6–27.2) and to her. B: Luciana's mouth wipe (62), glance/lean (65–66, 67.5–69), punch arm (71.1–71.8). |
| Reviewer: licence scope; staging label only on B; stale ledgers | Credits: the **whole film (picture + soundtrack) is offered under CC BY-SA 3.0** (Adaptation, s.1(a)); handmade elements carry the same licence. The disclosure line also sits on the opening of A (0–2.4 s, under the 'A' label). Commons re-read and sha1 wording fixed. rig.json: stale kit-sound "handmade" entry, two-men/no-arm "absences" and the 2017835701 `used_as` retired (kept under `retired_in_editor_r2`). cues.json room cue reworded. Note reworded. |

## Timecoded sequence

| film t | fixture | segment | on screen | sound (cues.json) | evidence |
|---|---|---|---|---|---|
| 0.0–2.4 | 12:00 | A · WIDE | 'A' label + one-line staging disclosure. Foreman (front) in the CAPOREPARTO doorway, head panning, weight shifting. | work bell | P1 P4 P5 H1 H2 H5 · S1 |
| 0.4–2.0 | 12:00 | A | Renzo walks on from the right (hip/neck rock) to his station. | steps | P3 · S2 |
| 1.0–2.6 | 12:00 | A | Luciana comes in low from the left, rises at her station by the time clock, in his sight. | steps | P2 |
| 2.8–5.0 | –12:01 | A | She takes the apple from her pail; both wait apart. | lid tick | P2 · S7 |
| 5.0 | 12:01 | A | **The foreman turns**: front → back photograph (squash on the feet pin); he reads at the office bench. | rustle | P5 P6 |
| 5.0–7.0 | 12:01–12:01:24 | A · PUSH | Both go behind the pile; WIDE → 1.35× MEDIUM, doorway and his back kept in frame. | room tone | P1–P3 P6 |
| 7.0–14.3 | 12:01:24–12:02:52 | A · MEDIUM | **MEETING** (frames 168–343). 8.5 R bite (she feeds him); 9.92–10.5 the apple passes into his hand and back (t = 10 defining frame); 11.0 L bite; 12.0 the foreman turns a sheet (arm on the shoulder pin); 13.0 R bite (core); the core to his lid by 14.0. | three bites; tap 14.0 | P2 P3 P6 H3 H6 · S6 S8 |
| 14.3–15.0 | –12:03 | A · PULL | Renzo rises and passes her (she ducks behind the pile) to the clock; **punch 15.0** (card drops a slot). | punch | P3 P1 · S7 S8 |
| 15.8–19.6 | 12:03–12:03:55 | A · WIDE | He goes off right; she waits in the corner (foreman's back still turned), then returns to the clock. | steps | P2 P6 |
| 20.0 | 12:04 | A | **The foreman turns back** (back → front); **her punch 20.0**. | punch | P5 P1 |
| 20.6–35.0 | 12:04–12:06:58 | A · WIDE | She goes off; the foreman alone: leans, shifts, gaze across the pile and the core on Renzo's lid (25.6–27.2), a step toward camera (28.6–32.4). | room tone | P1 P5 H3 |
| 35.0–37.0 | – | SLATE | Handmade schedule-strip slate: Luciana's strip slides 3 minutes, the light column closes; disclosure at the foot. | card, slide | H4 · S5 |
| 37.0–42.0 | 12:00–12:01 | B · WIDE | Same opening; Luciana absent; Renzo walks to his station. | single shorter work bell | P1 P3 P5 · S1 |
| 42.0 | 12:01 | B | The foreman turns (front → back). | rustle | P5 P6 |
| 42.0–44.0 | –12:01:24 | B · PUSH | Renzo goes to the corner alone and takes out the apple. | tick rising | P3 P2 |
| 44.0–51.3 | –12:02:52 | B · MEDIUM | He waits, head cycling clock → door → her empty place; 49.0 the foreman turns a sheet. | tick louder; rustle | P3 P6 |
| 51.0–51.3 | 12:02:48 | B | His one bite, for her; he leaves the apple on **her lid**. | bite | P3 H3 · S6 |
| 52.0 | 12:03 | B · PULL | **Late bell + his punch**; the foreman lifts his head at the bell (neck pin). | late bell, punch | S9 S7 S8 P6 |
| 52.0–53.5 | 12:03–12:03:18 | B | **Near-miss**: she comes in low behind him; he goes off right. Never both in the corner. | steps; tap 53.0 | P2 P3 |
| 53.5–55.95 | –12:03:55 | B · WIDE | Alone in the corner (his back still turned): she takes the apple from her lid, **bite 55.0**, then drops it into her pail (55.95). | lid tick, bite | P2 · S6 S7 |
| 56.25–56.8 | 12:03:55–12:04 | B | Empty-handed to her station at the clock. | steps | P2 |
| 57.0 | 12:04 | B | **The foreman turns back** (front); gaze held on her. | | P5 |
| 57.0–72.0 | 12:04–12:06:58 | B · WIDE | She waits at the clock under his eye (wipes her mouth 62, glances 65–69); he leans, steps toward her (61). **Her punch 71.5.** Hard cut 72.0. | punch | P2 P5 P1 · S7 S8 |

## Ledger (evidence IDs)

| ID | item | licence | used as |
|---|---|---|---|
| P1 | Russell Lee, *Time clock and tool boxes…*, San Diego 1941, LoC 2017789670 | No known restrictions | wall plate, clock, pail-pile occluder (one stray lid cut away), rack card |
| P2 | Marjory Collins, *Women employees eating lunches… Ross Heater*, Buffalo 1943, LoC 2017851428 | No known restrictions | Luciana (body, head + 2 jaw drawings, forearm); the apple |
| P3 | Arthur S. Siegel, *Dodge truck plant, Detroit. Lunch hour*, 1942, LoC 2017835701 | No known restrictions | Renzo (body, head + 2 jaw drawings, upper arm, forearm, hands) |
| P4 | Jack Delano, *Madison, Wisconsin… chemistry laboratory*, 1942, LoC 2017829778 | No known restrictions | the doorway and office (technician retouched out; the foreman covers the retouch) |
| P5 | Arthur S. Siegel, *Bethlehem-Fairfield… worker looking at a time clock*, 1943, LoC 2017851041 | No known restrictions | the foreman FRONT (FLOOR); its legs and hard hat also on the back view |
| **P6** | Arthur S. Siegel, *Bethlehem-Fairfield… Erecting bottom shell plates*, 1943, LoC 2017851145 (8d28435) | No known restrictions (item JSON 2026-11-16) | the foreman BACK (OFFICE): torso, head, arm |
| S1 | Model 500 Telephone British ring.ogg, CianMcCann | CC BY-SA 3.0 | work bell |
| S9 | WWS Minetelephone.ogg, Work With Sounds / K. Gutkowski | CC BY 4.0 | late bell |
| S2 | Concrete Steps 2.ogg, Pwaivers | CC BY-SA 3.0 | footsteps |
| S10 | Clock ticking.ogg, natalie | PD | tick bed |
| S5 | Book paper pages assorted.ogg, stephan | PD | rustles, slate card |
| S6 | Crunching munching grinding.ogg, stephan | PD | bites (**substitute**: pistachio husks) |
| S7 | Cupboarddoorclose.ogg, Secretlondon | CC BY-SA 3.0 | lid ticks; punch part 1 (**substitute**) |
| S8 | Knocking on wood or door.ogg, stephan | PD | taps; punch part 2 |
| S3 | Church people walking steps with reverb.ogg, stephan | PD | room tone, < 200 Hz only |
| H1–H7 | handmade | CC BY-SA 3.0 with the film | CAPOREPARTO card; paper clock hands; scissor-cut bites; schedule-strip slate; 'A' label + disclosure; jaw drawings and doorway retouch; hat+legs collage on the back foreman |

All Commons licences and sha1s: `review-2/api/commons_extmetadata.json` (2026-11-16), local sha1s match. No kit synthesis in picture or sound. Nothing from the 1962 film. `aesthetic-compare.jpg` contains the copyrighted reference still: keep it out of any published bundle.

## Claim graph (plan §9 → evidence)

1. **Clock**: minute hand measured on every frame vs 6°·τ/5 (`render-asserts.json → clock_max_err`); MeetingWindow A = [12:01,12:03), B = ∅ (rules.py asserts).
2. **Meeting only in A**: `meet_drawn` true only on A frames inside the rules meet window (asserted per frame); three bites R/L/R in clear silhouette while the foreman's back is on screen; B co-presence only 52.0–53.5; the apple ends hidden in her pail before he turns.
3. **Rule legible muted**: the foreman is on screen in every frame (asserted); his back photograph is drawn iff rules facing = OFFICE (asserted); Luciana is behind the pile only while his back is shown (`station_checks`); the slate shows her strip sliding 3 minutes and the shared light closing.
4. **Puppetry**: foreman front (feet, neck) / back (feet, hip, neck, shoulder) as two different real photographs, substituted on the switch frames listed in `performance.json → substitutions`; Renzo 5 pins, Luciana 3 pins + root; jaw drawings; walk rock on hip/neck/shoulder; keys on twos.
5. **Tone**: `aesthetic-compare.jpg/json` (t = 3, 10, 25, 47, 60 beside calvino.webp).
6. **Framing t = 10**: couple > 45 % of frame height, faces toward each other, the apple between their hands (in his hand at 9.92–10.5) near frame centre, jamb + clock + the foreman's back in frame.
7. **Provenance**: `films/credits/renzo-e-luciana.json`.

## Declared deviations

- B apple: he sets it on her lid at 51.25 (rules: 53.0); she drops it into her pail at 55.95 (rules: held to the end) so B obeys the rule.
- A: the apple is in Renzo's hand 9.92–10.5 (rules: L_wrist throughout 8.5–13.2).
- The foreman's back is a different real man in the front photograph's hat and on its legs: no back view of the same man exists in the sequences checked.
- The sound mix is unchanged from round 1: the foreman's "steps" cues now play under his weight shifts in place.

## Render (repair round 2)

`assets/films/renzo-e-luciana.mp4`: 72.00 s, 3.0 MB. `render-asserts.json`: 1728 frames; meet frames 176 (168–343); clock max error 0.29°; 1680 foreman checks (on screen, back iff OFFICE); 498 station checks; 1680 layer-order checks.
Tone (`aesthetic-compare.json`, reference median 122 / p5 22 / p95 231 / grain 10.1, chroma 0): t3 114/14/234/13.0; t10 123/30/238/11.8; t25 118/14/235/13.0; t47 128/30/242/11.9; t60 116/14/234/13.0; chroma 0 everywhere. The pail occluder's grade was changed from (46, 215, γ0.8) to (22, 215, γ1.15) so WIDE blacks are no longer clipped to 0.

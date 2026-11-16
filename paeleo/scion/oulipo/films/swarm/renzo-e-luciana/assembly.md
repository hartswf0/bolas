# Renzo e Luciana · assembly (montage editor)

The assembly script is `films/renzo-e-luciana.py`. It renders to `assets/films/renzo-e-luciana.mp4` at 960×540, 24 fps, 72.0 s. Rendering uses `kit.Film`, with kit grain switched off and no kit sound synthesis.

**Inputs:**
- `rules.json` and `rules.py` (imported): clock, schedules, locations, head-substitution times, apple states, bites, cards, camera states and the frame asserts.
- `rig.json` plus the r3 pieces: pivots, scales and levels/gamma.
- `performance.json`: the r3 test-shot keys for the meeting. They were re-timed to the `rules.json` bite frames (8.5, 11.0, 13.0) and extended to the full 72 s.
- `cues.json` and `sound.wav`: added through `mix.add`, left and right channels each divided by 1.414.

**Frame asserts:** these ran on every frame of the render. Results are in `render-asserts.json`.
- `rules.assert_frame(k, minute_deg, meet_drawn)` checks the minute hand against the one clock, the rule, and the meeting window.
  - The minute angle is *measured back off the drawn canvas* (ink centroid of the hand) and checked to within 0.5°. The maximum error over all frames is about 0.3°.
  - `meet_drawn` is derived from the drawn puppet roots: both actors are in the corner, in A only.
- `rules.assert_layer_order` checks the compositing order actually used. In the B crossing (52.0–53.5 s) the check instead asserts that every Luciana layer is drawn before every Renzo layer, as `rules.LAYER_NOTES` asks.

## Timecoded sequence

The evidence IDs are expanded in the ledger below.

| film t | fixture | segment | on screen | sound (cues.json) | evidence |
|---|---|---|---|---|---|
| 0.0–0.4 | 12:00 | A · WIDE | Clock at 12:00. The foreman faces FLOOR in the CAPOREPARTO doorway, head panning on its neck pin. | work bell (double ring) | P1 P5 P4 H1 H2 · S1 S3 S10 |
| 0.4–2.0 | 12:00 | A | Renzo slides on from the right with a stepping bob and sits up on the right-hand stack (open_right). His head goes to the clock. | R steps, foreman pacing | P3 · S2 |
| 1.0–2.6 | 12:00 | A | Luciana slides on from the left to the left end of the pile (open_left), apart from him, in full view of the doorway. | L steps | P2 |
| 2.6–3.5 | 12:00:31–42 | A | Her forearm dips into her pail (elbow pin) and comes up with the apple. | lid tick | P2 · S7 |
| 3.5–5.0 | 12:00:42–12:01 | A | Renzo's head goes to the door, then the clock, then the door. Luciana's head goes to the door. | | P2 P3 |
| 5.0 | 12:01 | A | **The foreman turns.** The Siegel front photograph is substituted by the Delano back photograph. | paper rustle; pacing stops | P5 P4 · S5 |
| 5.0–7.0 | 12:01–12:01:24 | A · PUSH | Both slide behind the pile into the corner. The camera pushes WIDE → 1.35× MEDIUM, with the plate drifting at 0.6× and the puppets and pile at 1.0×. | room tone | P1–P4 |
| 7.0–14.3 | 12:01:24–12:02:52 | A · MEDIUM | **MEETING** (frames 168–343, equal to `rules.meeting_frames.A`). Her elbow pin lifts the apple to his mouth. Bites are cut from the apple: R at 8.5, L at 11.0, R at 13.0. His head goes back to the clock between bites (watch duty). Defining frame at t = 10. | three bite crunches; tick dropped | P2 P3 H3 · S6 |
| 14.0 | 12:02:48 | A | She lids the core on his pail lid. It stays there to 12:07. | wood tap | P2 H3 · S8 |
| 14.3–15.0 | 12:02:52–12:03 | A · PULL | Renzo rises (hip and root) to the time clock. | R steps | P3 |
| 15.0 | 12:03 | A | **R punches.** A real time card cut from the plate's rack drops into an empty slot. | punch (cupboard + knock) | P1 · S7 S8 |
| 15.8–17.0 | 12:03:10–12:03:24 | A · WIDE | R goes back to his station (off right). | | P3 |
| 15.0–19.0 | 12:03–12:03:48 | A | Luciana is alone in the corner. Her hand wipes, then goes down to close her pail. | lid tick 18.0 | P2 |
| 19.0–20.6 | 12:03:48–12:04:07 | A | She rises to the clock and **punches at 20.0** (a second card drops). | L steps, punch | P2 P1 |
| 20.0 | 12:04 | A | **The foreman turns back to FLOOR** (back → front substitution). | pacing resumes | P4 P5 |
| 20.6–35.0 | 12:04–12:06:58 | A · WIDE | She exits left. Empty pails; the core sits on his lid. The foreman's head pans right, centre and left across the floor and passes over the lid. The clock reaches 12:07. | room tone, pacing fading | P1 P5 H1 H3 |
| 35.0–37.0 | – | SLATE | Handmade typed card, "B · la campanella suona in ritardo". Luciana's slotted strip slides 3 minutes, and the light through all three slots goes out. | card set down, strip slide | H4 · S5 |
| 37.0–42.0 | 12:00–12:01 | B · WIDE | The same opening as A, but Luciana is absent. Renzo comes on and sits at open_right. | single shorter work bell | P1 P3 P5 · S1 S3 |
| 42.0 | 12:01 | B | The foreman turns (the same substitution as A at t = 5). | rustle | P4 |
| 42.0–44.0 | 12:01–12:01:24 | B · PUSH | Renzo slides into the corner alone. | tick rising | P3 · S10 |
| 43.5–43.9 | 12:01:18 | B | The apple comes up out of his pocket from behind the pile edge and onto his lid (his hand is hidden by the pile). | | P2 (apple) |
| 44.0–51.3 | 12:01:24–12:02:52 | B · MEDIUM | He waits. His head substitutions cycle clock → door → empty place on the rules rhythm. The counterpart frame is at t = 47. | tick louder | P3 |
| 51.0 | 12:02:48 | B | He leans in on his root and neck pins and takes **one bite, for her** (B1, cut top-left). | bite | P3 H3 · S6 |
| 51.3–52.0 | 12:02:52–12:03 | B · PULL | He rises to the clock. | R steps | P3 |
| 52.0 | 12:03 | B | **Late bell.** Renzo punches on the same frame, and his card drops. | late bell + punch | S9 S7 S8 P1 |
| 52.0–53.5 | 12:03–12:03:18 | B | **NEAR-MISS** (36 frames on stage together). She slides on from the left, wholly behind him in the layer order. His hidden hand slides the bitten apple along the lids onto hers (52.6–53.0), and he goes off right. They are never both in the corner. | two sets of steps; wood tap 53.0 | P2 P3 |
| 53.5–56.2 | 12:03:18–12:03:52 | B · WIDE | Luciana alone in the corner. Her lid opens at 54.0. She reaches for the apple (54.2) and takes **bite 2 at 55.0** in the photograph's own pose. | lid tick, bite | P2 · S7 S6 |
| 56.2–56.8 | 12:03:52–12:04 | B | She moves to the open left end. | steps | P2 |
| 57.0–57.5 | 12:04 | B | **The foreman turns back to FLOOR.** His head pans right and then **settles on her** (front_on_luciana, held to the end). He takes one step out of the doorway (57.5–58.3). | pacing resumes | P5 |
| 57.5–71.3 | 12:04–12:06:52 | B · WIDE | She eats the two-bite apple in full view of him, legally on break. His card is in the rack. | room tone | P2 P5 P1 |
| 71.3–72.0 | 12:06:52–12:07 | B | She rises to the clock. **Her punch is at 71.5.** Hard cut at 72.0. | punch | P2 · S7 S8 |

## Ledger (evidence IDs)

All LoC items were checked as "No known restrictions" in the item JSON on 2026-11-16 (cutout-performance unit). All Commons licences were read from extmetadata on 2026-11-16 (sound unit). Each item is listed in `films/credits/renzo-e-luciana.json`.

| ID | item | licence | used as |
|---|---|---|---|
| P1 | Russell Lee, *Time clock and tool boxes…*, San Diego 1941, LoC 2017789670 | PD (FSA) | wall plate, clock body, pail-pile occluder, lids, rack time card |
| P2 | Marjory Collins, *Women employees eating lunches… Ross Heater*, Buffalo 1943, LoC 2017851428 | PD (OWI) | Luciana: body, head, forearm; the apple and its bite states |
| P3 | Arthur S. Siegel, *Dodge truck plant, Detroit. Lunch hour*, 1942, LoC 2017835701 | PD (OWI) | Renzo: torso and head |
| P4 | Jack Delano, *Madison, Wisconsin… chemistry laboratory*, 1942, LoC 2017829778 | PD (OWI) | doorway; foreman BACK |
| P5 | Arthur S. Siegel, *Bethlehem-Fairfield… worker looking at a time clock*, 1943, LoC 2017851041 | PD (OWI) | foreman FRONT (head on a neck pin) |
| S1 | Model 500 Telephone British ring.ogg, CianMcCann | CC BY-SA 3.0 | work bell |
| S9 | WWS Minetelephone.ogg, Work With Sounds / K. Gutkowski | CC BY 4.0 | late bell |
| S2 | Concrete Steps 2.ogg, Pwaivers | CC BY-SA 3.0 | all footsteps |
| S10 | Clock ticking.ogg, natalie | PD | tick bed |
| S5 | Book paper pages assorted.ogg, stephan | PD | rustles, slate card and strip |
| S6 | Crunching munching grinding.ogg, stephan | PD | bites (**substitute**: pistachio husks) |
| S7 | Cupboarddoorclose.ogg, Secretlondon | CC BY-SA 3.0 | lid ticks; first half of the punch (**substitute**) |
| S8 | Knocking on wood or door.ogg, stephan | PD | taps; second half of the punch |
| S3 | Moving Image Archive, *Valley Town* (1940), clip a11ba534 | as listed by movingimagearchive.com (largely PD); not independently verified | room tone |
| H1 | handmade | – | typed CAPOREPARTO card, pinned on the door casing (1.0× plane) |
| H2 | handmade | – | paper clock hands, drawn per frame at 4× and reduced, with their own shadow |
| H3 | handmade | – | scissor-cut bites in the real apple cut-out (A1–A3, B1–B2) |
| H4 | handmade | – | slate: typed card and slotted strips on a light box (`rules.slate_frame`, frames in `sources/renzo-e-luciana/rule-modeler/slate/`) |

No kit synthesis is used, in either picture or sound. No frame or sound comes from the 1962 film.

## Claim graph (plan §9 → evidence)

1. **Clock** reads 12:00 at t = 0 and 37, 12:02 at t = 10 and 47, and 12:06:58 at t = 34.96 and 71.96 (12:07 is reached at the cut).
   - The minute hand is measured on every frame against 6°·τ/5, and the assert passes (`render-asserts.json`).
   - `rules.json` gives MeetingWindow A = [12:01,12:03) and B = ∅.
2. **The meeting happens only in A.**
   - `meet_drawn` is true on frames 168–343, which equal the rules' meet frames. It is never true in B (asserted).
   - The apple loses three bites in A (R, L, R).
   - In B, co-presence lasts 52.0–53.5 (36 frames) and the apple ends on her lid.
3. **The rule reads without exposition.**
   - The foreman's turns at 5/42 and 20/57 are photograph substitutions, and both puppets move into the corner only after his back turns.
   - Bells, punches and bites come from `cues.json`; their onsets were measured by the sound unit at 0 ms error.
   - The picture events are keyed to the same `rules.json` times: punches at 15.0 / 20.0 / 52.0 / 71.5, bites at 8.5 / 11.0 / 13.0 / 51.0 / 55.0.
4. **Puppetry.**
   - Luciana has root, hip, neck, elbow and grip→apple. Renzo has root, hip and neck. The foreman has a feet pin and a neck pin, plus the front/back substitution.
   - Keys are on twos (12 drawings/s), eased, with overshoot on head turns. Head-substitution times come from `rules.HEADS`.
   - The foreman's front and back are two different real photographs. Nothing is mirrored, and no piece is enlarged.
5. **Tone.** See `aesthetic-compare.jpg` and `.json`: t = 3, 10, 25, 47 and 60 all PASS.
   - Chroma is 0 in every frame.
   - Medians are 114, 121, 117, 128 and 115.
   - p5 is 0, 29, 1, 28 and 1.
   - p95 is 233–237.
   - Grain (high-pass std) is 11.8–13.8.
6. **Framing at t = 10.**
   - The couple spans about 65% of frame height. She is three-quarter to near-profile toward him, and he is in profile toward her (looking up to the clock at that beat).
   - The apple sits near the frame centre, and the door jamb and clock are in frame.
7. **Provenance.** See the ledger above and `films/credits/renzo-e-luciana.json`.

## Deviations from the units' material (declared)

- **Apple in A:** `rules.APPLE` A has the core in R_hand at 13.2. Renzo has no forearm piece, so Luciana keeps it and lids it on his lid at 14.0 (r3 staging).
- **Apple in B:** "R_hand" (43.5–53.0) is rendered as the apple on *his* lid, with his hand hidden behind the pile. At 52.6–53.0 it slides along the lids to hers.
- **Pail lids:** these are not separate pieces. Lid open/close (2.8, 13.6, 18.0, 54.0) is carried by the forearm dipping behind the pile and by the sound.
- **Foreman head pans:** these are a ±7° head turn on a neck pin cut from the one front photograph. No second front pose exists.
- **Grade:** the pail pile was regraded to levels 40–215, gamma 0.8, and the wall plate to gamma 0.5 (was 26/1.12 and 0.55). This lifts the WIDE medians into 112–132. It costs crushed blacks in the WIDE frames (p5 ≈ 0–1 against the reference's 21).

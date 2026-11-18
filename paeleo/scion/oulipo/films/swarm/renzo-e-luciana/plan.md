# Renzo e Luciana · "Pausa delle dodici": swarm plan

Director plan, built from scratch on the chosen keyframe direction **2 · Collage al marcatempo** (`proposals/kf-2.png`). Prompt: `prompts/renzo-e-luciana.md`. Reference: `assets/references/calvino.webp` (catalogue/cinema.json id 7, "Marisa Solinas in a white hat seated close to Germano Giglioli", Cineteca di Bologna). The reference image is only a look target. It is never copied, traced or pasted, and no frame of the 1962 film is used.

## 1 · Creative thesis

A couple exists only in the minutes they can take from a factory: the time clock owns the hour, the foreman owns the doorway, and the stacked lunch pails are the one thing in the room that belongs to the workers. Behind the pails, two real people from 1940s photographs share one apple. She holds it up to his mouth the way Luciana holds the spoon in the reference. The rule is never explained. You see it in the clock hand, in the foreman's back, and in which of the two bodies is missing when the bell comes late.

**Bland result to avoid:** a slideshow of factory photos with a couple pasted in, or a "couple" made of two generic tokens. The puppets must *act*: attention, then intention, then gesture, then resistance, then a changed state.

## 2 · Defining beat and comparison baseline

**Defining beat (the test shot):** fixture 12:02, Version A, film t = 10 s. In one frame: (1) the wall clock reads 12:02, with its minute hand visibly advancing; (2) the foreman stands in the CAPOREPARTO doorway with his back to the floor; (3) behind the pail pile, Luciana's forearm (pinned at the elbow) lifts the apple to Renzo's mouth while his head is turned to the clock, keeping watch. Each performer does something particular: she feeds, he guards. The viewer can point at **the clock, the doorway and the gap between the two hands**.

**Counterpart frame:** Version B, fixture 12:02, t = 47 s. The clock and the pails are identical, but Renzo is alone behind the pails holding the uneaten apple, and his head swings between the clock and the empty place beside him.

**Comparison baseline:** `proposals/kf-2.png`, a still 1280 px collage built from 1024 px service JPEGs. Measured: median 97, p5 35, p95 202, high-pass grain 20.4, against the reference's 122 / 21 / 231 / 11.1. The couple fills about 30 % of frame height, and they grin at the camera with no gesture between them. The film beats the baseline only if (a) the meeting is an *animated* exchange of food on pinned joints, (b) the tones move toward the reference (§8), (c) the framing at the defining beat is closer than kf-2 (couple ≥ 45 % of frame height), and (d) B differs from A only by what the late bell causes.

## 3 · Lineage Genome and Olog

### Lineage Genome (compact)
- **Source:** *Renzo e Luciana*, the Monicelli episode of *Boccaccio '70* (1962), from Calvino's story "L'avventura di due sposi" (1958). The note that Calvino co-wrote it and that the film turns on a workplace ban on employee relationships comes from the Il Cinema Ritrovato page. It is recorded as sourced but **not independently verified** here, beyond that page.
- **Source medium:** 35 mm black-and-white narrative fiction with location realism (Milan factory, terrace, crowded flats).
- **Target medium:** a 72 s 960×540/24 fps cut-out puppet film. Real Library of Congress FSA/OWI photographs (US, 1940–43) are cut out and articulated on pins, composited with occlusion on a real time-clock wall, and scored with foraged and kit sound.
- **Preserved relation:** a couple's intimacy is shaped by an institutional schedule and an observer, and a small shared act (food) stands in for the whole relationship.
- **Changes:**
  - *Optics:* live camera becomes a fixed collage stage with slow multiplane drift and one push-in.
  - *Formalism:* narrative becomes the same encounter played under two schedules (a counterfactual pair) on one clock.
  - *Concept:* the marriage and night shift of Calvino's story become a ban on contact within one break.
  - *Sound:* dialogue and Armando Trovajoli's score become bells, time-clock punches, footsteps and room tone, with no voice.
- **Formation epochs (weight 0–100, reason):**
  - Italian neorealism / commedia all'italiana 1945–64: **85**. The source's social realism, factory and class setting, and the humour of constraint.
  - US FSA/OWI documentary photography 1935–44: **70**. All the bodies and the plate come from it. It brings the mid-tone B&W, daylight and posed-candid lunch breaks. It is American, not Italian, and that mismatch is declared.
  - Taylorist time discipline (time clocks, shift bells) 1900–1960: **60**. The rule's own technology.
  - Cut-out / collage animation (Reiniger 1920s, Gilliam 1969–74, Ernst collage 1929–34): **55**. The articulated pieces, the visible scissor edge and the pinned joints.
  - Computational schedule / counterfactual formalism (SCION 48, Olog): **40**. The A/B replay with a computed meeting window.
  - *Uncertain:* whether Monicelli's film stages a lunch-break sharing scene like ours. Not verified. Our beat is derived from the reference still and the prompt, not claimed as a quotation.

### Olog

Types (boxes):
- **Actor** {name, private_commitment, schedule: Interval, location: Place, role}. Renzo: commitment = Luciana, break [12:00,12:03), role operaio. Luciana: commitment = Renzo, break A [12:00,12:04) / B [12:03,12:07), role operaia.
- **InstitutionalRule** {observer = Foreman, trigger = observer facing the floor ∧ two actors co-present in the pail corner, scope = factory floor visible from the CAPOREPARTO doorway, visible consequence = the foreman's turn and gaze, a card pulled from the rack}.
- **Observer state** facing(t) ∈ {FLOOR, OFFICE}. The foreman faces FLOOR on [12:00,12:01) ∪ [12:04,12:07] and OFFICE (back turned, reading the time sheets) on [12:01,12:04).
- **Place**: pail corner (hidden only from the clock wall; visible from the doorway when facing = FLOOR), time clock (public), work station (offscreen right).
- **MeetingWindow** = break(R) ∩ break(L) ∩ access(corner) ∩ {t : facing(t) = OFFICE}. access(corner) = [12:01,12:04), the same interval as the foreman's back.
- **[stage]** maps each beat to puppet blocking, a framing and sound cues.

Arrows:
- an Actor *is on break during* an Interval;
- a Rule *is enforced by* an Observer, whose facing *determines* exposure(place, t);
- a MeetingWindow *is the intersection of* two break intervals, corner access and non-exposure;
- [stage] *sends* a (MeetingWindow, exposure) state to (blocking, framing, cue list).

**Central operation:** `meet(R, L, corner, t)`, the shared bite.
- **Typed preconditions:** t ∈ break(R); t ∈ break(L); t ∈ access(corner); facing(t) = OFFICE; both actors located at the corner; the apple is held by one of them.
- **Observable consequences:**
  - both puppets are behind the pail occluder in the same frame;
  - the apple's silhouette changes (a bite substitution, apple0 → apple1 → apple2);
  - Renzo's head alternates between clock and Luciana (watch duty);
  - no foreman turn is triggered;
  - room tone with no footsteps under the meeting;
  - after the meeting the bitten apple stays in a pail lid as a persistent prop (carried forward).
- **Counterexample (Version B):** break(L) = [12:03,12:07), so break(R) ∩ break(L) = ∅ and `meet` is undefined at every t. The staged consequence is a near-miss at 12:03. Renzo, punching back in, and Luciana, released by the late bell, cross at the pails for under 1.5 s. Because his break has ended the crossing is **not** a meeting, and no bite is shared. He leaves the apple, bitten once, on her pail lid, which keeps the common seed's "leaves the key on the bench and walks away". At 12:04 the foreman turns back to FLOOR and *sees her*: she is alone, legal, and eating an apple with two bites in it (one his). The exposure state is "observer sees L with R's token", and it is carried to the end.
- **Equivalence and divergence of replay:** A and B are frame-aligned on the same clock (B t = A t + 37 s). On [12:00,12:01) the two versions are **equivalent** in picture, apart from Luciana's presence. On the foreman's turns at 12:01 and 12:04 they are equivalent: the same frames and sound. They **diverge** from 12:00 in who is on the stage and from 12:03 in the punch and bell. A new camera angle (the push-in) is merged only where visibility stays equivalent: the doorway jamb and the clock remain in frame.

## 4 · Invariants (tested)

1. **One clock.** Fixture minute = 5.000 s of film. Clock angle, puppet blocking, foreman facing, and bell and punch cues are all *computed* from `rules.json` (no hand-placed timing). Assert: the minute-hand angle at version-local τ equals 6°·τ/5 within 0.5°.
2. **Rule preserved.** No frame has both actors in the corner while facing = FLOOR (assert, per frame, in both versions).
3. **Knowledge.** Neither actor acts on information they lack. In B, Renzo does not know of the late bell until it rings at 12:03, so his waiting (head to clock, then to door) continues until then.
4. **Exposure carried forward.** The A apple core and the B two-bite apple persist after their beats. The foreman, having seen Luciana at 12:04 in B, keeps his gaze on her (head substitution) until the end of the version.
5. **Meeting window** computed = [12:01,12:03) in A and ∅ in B. Assert in `rules.py`. The renderer refuses to draw `meet` outside it.
6. **Source integrity.** Every photographic piece maps to an LoC item and its pixel crop. No puppet is mirrored to fake a back view, because a back view must be a real photograph of a back. Scaling, rotation about a pin, and level/gamma grading are the only transforms.
7. **Frame-by-frame animation.** Each puppet has ≥ 3 pinned joints, keyed per frame on twos (12 drawings/s) with eased holds. The bite and head substitutions are on exact frames listed in `performance.json`.

## 5 · Timed shot / sequence list (Hard proof, §6 + fixture §7)

Total 72.0 s = **Version A 0–35 s** (12:00:00 → 12:07:00) + **slate 35–37 s** + **Version B 37–72 s** (12:00:00 → 12:07:00). Fixture clock c(τ) = 12:00 + τ/5 min, where τ is version-local time. The 35-second encounter is played twice, exactly as §6 asks.

Stage: one fixed collage set, 960×540.
- **Plane 0** (×0.6 drift): the Russell Lee time-clock-and-racks wall plate, extended to the frame.
- **Plane 1** (×1.0): the handmade CAPOREPARTO doorway. It is re-placed from kf-2's far-left position to just left of the clock, so that a 1.35× push-in on the couple can still hold the door jamb, the clock face and the couple at once.
- **Plane 2:** the puppets.
- **Plane 3:** the pail pile occluder (cut from the same plate) and the pail lids.

Camera states: WIDE (1.0×) and MEDIUM (a 1.35× push centred between the clock and the pail corner).

### Version A · orario originale

| film t | fixture | on screen | heard |
|---|---|---|---|
| 0.0–0.4 | 12:00 | WIDE. Card racks, clock at 12:00 exactly, pail pile, foreman in the doorway **facing FLOOR** (front-view cut). | **Work bell** (foraged), one ring of about 2 s |
| 0.4–5.0 | 12:00–12:01 | R enters from the right and sits at the right end of the pails, upright and in the open, with his head to the clock. L enters, sits apart at the left end and opens her pail (lid piece pivots), apple in hand. Two co-workers, not a couple. The foreman's head pans across the floor (head substitution). | Footsteps of the foreman pacing (foraged), factory room tone (foraged) |
| 5.0 | 12:01 | **The foreman turns: substitution to a real back-view cut.** He faces OFFICE and reads the sheets. | Footsteps stop; one paper rustle |
| 5.0–7.0 | 12:01 | L slides along the pile (root translation behind the occluder) into the corner. R's torso tips toward her on his hip pin (−4° to −10°). Camera eases WIDE → MEDIUM. | Room tone only |
| 7.0–15.0 | 12:01:24–12:03 | **MEETING / TEST SHOT.** L's forearm (elbow pin) lifts the apple to R's mouth, as in the reference's spoon. Bite 1 at t = 8.5, apple0→apple1, with R's head pinned forward. R's head goes back to the clock (watch). L takes bite 2 at t = 11.0 (her head-and-shoulder pin dips). Bite 3 for R at t = 13.0. At t = 14.0 he places the core in his pail lid, the small action that keeps the relationship intact. Defining frame t = 10.0. | Silence under room tone; three bite crunches (foraged), each timed to its substitution frame ±1 |
| 15.0 | 12:03 | R's break ends: he stands (hip and knee pin rise), exits left to the clock, and **punches his card** (card piece drops in the rack). Camera MEDIUM → WIDE. | Time-clock punch (foraged/kit "ka-chunk"), his footsteps |
| 15.0–20.0 | 12:03–12:04 | L alone in the corner wipes her hand and closes her pail. The core is visible in his lid. | Room tone |
| 20.0 | 12:04 | **The foreman turns back to FLOOR** (front cut) and sees only the pails. L has already moved to the open left end; she punches in. | Footsteps resume; punch |
| 20.0–35.0 | 12:04–12:07 | WIDE, slow drift. The empty pails and the core in the lid hold. The foreman's head pans across the floor and passes over the lid without stopping. The clock goes to 12:07. | Room tone, foreman steps fading |

### Slate 35.0–37.0 (handmade)
A typed card on the light box: "B · la campanella suona in ritardo". Under it, the three slotted strips from direction 3 (R [12:00,12:03), L [12:03,12:07), corner [12:01,12:04)) show that no light passes where all three slots coincide. The strips are handmade (typed and cut card, kit-drawn), not a diagram overlay on the film. A soft whoosh and the strip sliding are heard.

### Version B · campanella in ritardo (t_B = 37 + τ)

| film t | fixture | on screen | heard |
|---|---|---|---|
| 37.0 | 12:00 | The same WIDE frame as A t = 0. The foreman faces FLOOR. | Work bell: **Renzo's break only** (a single ring) |
| 37.4–42.0 | 12:00–12:01 | R enters and sits in the open, apple in his pocket. **L is absent.** | The foreman's footsteps, room tone |
| 42.0 | 12:01 | The foreman turns to OFFICE (identical frames to A t = 5). | Footsteps stop; rustle |
| 42.0–52.0 | 12:01–12:03 | R moves into the corner alone and takes out the apple. He does not eat it. His head alternates clock → door → empty place (substitution on a 2 s rhythm that tightens toward 12:03). Camera eases to MEDIUM. Counterpart frame t = 47. | Room tone; the clock's ticking rises slightly in the mix |
| 52.0 | 12:03 | **Late bell** (a second, higher bell). R must punch back in. | Late bell, R's punch |
| 52.0–53.5 | 12:03 | **NEAR-MISS.** L enters from the left as R rises. They cross at the pail pile within 1.5 s, and their heads pass in occlusion order (she behind the pail lid line, he in front). He sets the apple, bitten once (by him, at the crossing), on her pail lid and walks away. No shared bite. | Two sets of footsteps crossing, the apple set down (a small wood tap) |
| 53.5–57.0 | 12:03–12:04 | L alone in the corner finds the apple and takes bite 2. | Room tone, a bite |
| 57.0 | 12:04 | **The foreman turns back to FLOOR and his gaze settles on L** (head substitution held on her). She has moved to the open end, and she is legally on break. | Footsteps |
| 57.0–72.0 | 12:04–12:07 | WIDE. L eats the two-bite apple in full view of the foreman. R's card is punched in the rack. The clock reaches 12:07 at t = 72.0. | Room tone; at 72.0 her break-end punch, a hard cut to black |

**Declared silence:** there is no voice and no score. The meetings play under room tone so that a sound-off reading can be compared with the bells restored (§7).

### Element sources

| element | FORAGED / HANDMADE | what, from where |
|---|---|---|
| Wall, racks, clock body, pail pile | FORAGED | Russell Lee, *Time clock and tool boxes at the vocational school for aircraft construction workers, San Diego*, 1941, LoC 2017789670 (`8c01492v`). Fetch hi-res through IIIF (`tile.loc.gov/image-services/iiif/service:pnp:fsa:8c01000:8c01400:8c01492v/full/2400,/0/default.jpg`) or the TIFF only if IIIF fails. |
| Luciana (several poses) | FORAGED | Marjory Collins, Ross Heater lunch series, Buffalo 1943, LoC 2017851428 (`8d16982v`, OWI-23899-D), plus adjacent negatives of the same table (OWI-23896..23902-D; `8d16979v` is in hand) to find the same woman in other poses for real drawing substitution. Search `loc.gov/photos/?q=Ross Heater lunches&fo=json`. |
| Renzo (several poses) | FORAGED | Russell Lee, *Workers eating lunch on curb… Consolidated*, 1940, LoC 2017788376 (`8c00283v`), plus adjacent curb frames (`8c00282v`/`8c00284v` if they exist) for head and arm poses. **Alternate branch:** the boy in Arthur Siegel, *Boy and girl worker during the lunch hour*, Bethlehem-Fairfield 1943, LoC 2017853398 (`8d29158v`, in hand). He is larger, sits close to a woman, and has gentler light. Use him if the Lee man is too small at 1.35×. |
| Foreman front / back | FORAGED | Front: OWI, *Bethlehem-Fairfield… worker looking at a time clock*, LoC 2017851041 (`8d28363v`); the photographer is to be filled in from the item JSON. Back: a real back view in a hard hat from Siegel, *Lining up before a time clock*, LoC 2017851042 (`8d28364v`, in hand), or another OWI frame. Never mirrored. |
| Apple bite states | FORAGED + cut | apple0 is the real apple in L's hand in `8d16982v`. apple1 and apple2 are made by *cutting* bites (curved scissor arcs taken from the plate's paper edge) out of that same cut-out, the way a collage artist would. This is a handmade operation on the foraged piece, not paint. |
| CAPOREPARTO doorway, door leaf, sign | HANDMADE | Dark card leaf and frame, with a typed paper sign (serif caps), cast drop shadow on the wall plate. |
| Clock hands | HANDMADE | Paper hands pinned on the real clock face, redrawn each frame from the fixture clock. |
| Time cards dropping | FORAGED | A card piece cut from the plate's own rack, moved one slot. |
| Slate with light-box strips | HANDMADE | A typed card and three slotted card strips (direction 3), kit-drawn with fibre grain and cast shadows. |
| Work bell, late bell | FORAGED | Wikimedia Commons audio (PD/CC0/CC BY): factory or school bell, electric bell, hand bell. Two distinguishable pitches or timbres. Kit `mix.bell` is the fallback, recorded as such. |
| Footsteps, room tone | FORAGED | Moving Image Archive clips with source sound (factory floor, shift change) for room tone; Commons footsteps on concrete. |
| Time-clock punch, bite crunch, paper rustle | FORAGED (Commons CC0/PD) or kit synthesis if none, declared in the ledger | |

## 6 · Animation technique SCIONs (from swarms.json)

1. **#29 GrabCut — Cutout Extraction Swarm.** Every performer and prop is a real figure cut from a real photograph. GrabCut, seeded by boxes and scribbles (existing seeds are in `proposals/src/cuts.py`), runs on the hi-res IIIF files, followed by alpha cleanup (morphological open/close, 1–2 px feather). Each figure is split into **separate pieces for animation**: head, torso, upper arm and forearm with hand (and apple for L), plus the pail lids. Occluded regions revealed by rotation get a minimal paper backing, the collage convention, never painted flesh. Invariants: no background islands, fingers retained, halos isolated, failure masks exported. Applied to the plate pails (occluder), R, L, the foreman front and back, the apple, the lid and the time card. Shots: all.
2. **#32 Forward Kinematics — Hierarchical Body Logic.** Each puppet is a joint graph (root, hip, torso, neck, head, shoulder, elbow, wrist, apple attached to L's wrist) with pivots set at anatomical points in source pixel coordinates. Local rotation × parent transform is applied in order, bone lengths are invariant, and there is no head/neck detachment. The apple is an explicit attachment, kept on L's wrist until the handoff and then on the lid. Applied: A 5–15 s (lean, feed, bites, head watch), A 15 s (R stands), B 42–53.5 s (R waits, sets down the apple), B 53.5–57 s (L bites). Keys are on twos with ease-in/out holds and a 1–2 frame overshoot on the head turns for weight. Drawing substitution (#38 method) swaps the heads (clock/her/door) and the foreman front/back on exact frames, each a held state of at least 6 frames to avoid flicker.
3. **#45 Occlusion Compositing — Who Is In Front?** This is the rule made physical: concealment is literally the pail pile's alpha. Layer DAG: wall plate < door frame < foreman < door leaf < puppets < pail occluder < pail lids and apple < camera. A holdout matte from the pail pile cuts across the puppets' bodies, and contact shadows (soft, offset from the plate's key light, upper left) are cast under each piece. Assertions: layer order is correct in every frame, nothing pops at the B near-miss crossing (L passes behind R's lid line), and alpha is valid. Applied: all shots, especially A 7–15 s and B 52–53.5 s.

(#44 multiplane drift is used lightly for the plate and doorway at 0.6×/1.0×. It is not a chosen SCION.)

## 7 · Swarm units (2–4, excluding the editor and the independent reviewer)

All units read `rules.json` once it exists. Until then they read the table in §5 of this plan, which is authoritative. Base revision: this plan.

### U1 · rule-modeler (shifts, sightlines, ledger, slate)
- **Task:** Write `films/swarm/renzo-e-luciana/rules.py`, which emits `rules.json`:
  - actors, schedules A/B, foreman facing intervals, corner access;
  - computed MeetingWindow (asserts [12:01,12:03) / ∅);
  - per-beat exposure state (who sees whom, what is carried forward);
  - cue list in film seconds and frame numbers (bells, punches, turns, bites, substitutions);
  - clock-angle function;
  - camera states.
  Also build the handmade slate/light-box card (`slate.png` plus a 2 s strip-slide frame sequence, or a function the editor can call) and a schedule-and-visibility graph (`visibility.png`). Include the frame-level asserts (invariants 1, 2, 5) as functions the editor imports.
- **Output:** `films/swarm/renzo-e-luciana/rules.json` (with `rules.py`, `slate.png`, `visibility.png`). Media go in `films/sources/renzo-e-luciana/rule-modeler/`.

### U2 · cutout-performance (forage hi-res plates, cut and rig the puppets, perform two strategies, render the test shot)
- **Task:**
  - Re-verify the LoC licences (item JSON: "No known restrictions", photographer).
  - Fetch hi-res IIIF JPEGs of the 4–6 needed plates (≤ 40 MB). Search adjacent negatives for alternate poses of the same L and R and for a real foreman back view.
  - Apply #29 to make RGBA pieces with pivots, a #32 rig and #45 occluder mattes from the plate.
  - Perform Version A (hidden-feeding strategy: low behind the pails, she feeds, he watches) and Version B (waiting and handoff strategy: in the open, one bite left as a token) as per-frame joint keys in `performance.json`.
  - Render the **test shot**: the shared food behind the pails while the clock hand moves and the foreman turns, A 5–15 s, then the same span in B, 42–53.5 s (≈ 22 s mp4 with scratch sound), as proof.
  - Grade only to unify: levels/gamma per piece toward the §8 target.
- **Output:** `films/swarm/renzo-e-luciana/rig.json` (pieces: file, source item, crop, pivot, parent, z), `performance.json`, `testshot.mp4`, `testshot-contact.jpg` (with the reference side by side). Media go in `films/sources/renzo-e-luciana/cutout-performance/`.

### U3 · sound (bell, late bell, punch, footsteps, room tone, bites)
- **Task:**
  - Forage real recordings from Wikimedia Commons (licence from extmetadata) and room tone from Moving Image Archive clips with source sound (forage.py, `--media clip`; e.g. "factory|machine shop|time clock|shift").
  - Decode with ffmpeg to 44.1 kHz mono WAV and trim. Make the two bells distinct: a work bell and a higher late bell.
  - Lay out a cue sheet against the §5 times (later `rules.json`), with each cue's frame and ±1-frame tolerance.
  - Produce a full 72 s stem mix (`sound.wav`) plus separated stems, so that the sound-off and bell-restored comparison is possible.
  - Declare every kit-synthesized fallback.
- **Output:** `films/swarm/renzo-e-luciana/cues.json` (cue, t, frame, file, source, licence), `sound.wav`, and `credits-sound.json` entries. Media go in `films/sources/renzo-e-luciana/sound/`.

**Editor (run separately):** assembles `films/renzo-e-luciana.py` with `kit.Film` from `rules.json`, `rig.json`, `performance.json` and `cues.json`. It writes `films/credits/renzo-e-luciana.json` and `films/notes/renzo-e-luciana.txt`, and renders ≤ 6 MB.

## 8 · AESTHETIC TARGET (from `assets/references/calvino.webp`, 1000×755)

- **Medium:** silver-gelatin black-and-white photograph, a 1962 production still. Real people, real daylight, a crowded public place.
- **Tonal range (measured, PIL, luminance):**
  - median 122, mean 123, std 65;
  - percentiles p1 10, p5 21, p25 65, p75 179, p95 231, p99 240;
  - full blacks in hair, the doorway and shoes; clean but not clipped whites in the hat, bowl and chairs;
  - a broad, even mid-tone belly.
- **Palette:** true neutral greyscale, measured chroma 0. Six-level quantisation gives #282828, #4d4d4d, #6c6c6c, #949494, #c0c0c0 and #e1e1e1, in nearly equal areas. Film frames stay neutral (R = G = B), with no sepia or tint.
- **Light:** soft, open daylight, broadly from upper left and front. The skin has gentle modelling with no hard spot, and the shadows are soft-edged under the chairs and arms.
- **Texture:** fine photographic grain, high-pass std 11.1 at 960 px width. The surfaces carry detail: tile grid, fabric stripes, hat fringe. **Our target is high-pass 9–14.** The baseline kf-2 is 20.4 because of 2× enlargement, which is the reason for the hi-res IIIF fetch. Scissor edges and drop shadows are the only added texture, and they are real collage features, not a faux grain filter.
- **Framing and scale:** a medium two-shot at near eye level. The couple fills about 80 % of frame height, and their hands and the shared bowl sit at the centre. Faces are in near-profile toward each other, and other people are cut by the frame edges, so intimacy happens in public. **Plan:** WIDE for the rule (clock, door, pails), MEDIUM 1.35× for the meeting so the couple spans ≥ 45 % of frame height, with the hands and apple near the frame centre and the door jamb and clock still at the edges.
- **Typography:** none in the reference. The film carries only diegetic type (CAPOREPARTO sign, rack cards) and the one handmade slate. No captions over the action.
- **Pacing:** the reference is a held moment of attention. Long holds, small gestures on twos, and few camera moves (one push-in and one pull-back per version).
- **How we arrive (real material and real technique):**
  - all photographic pieces are genuine 1940s B&W gelatin prints scanned by the LoC;
  - per-piece levels/gamma only, to bring each piece's median to 115–130 and p95 ≥ 220, so pieces from three photographers share one key;
  - contact shadows offset to match the upper-left key;
  - no colour, vignette or faux grain.
  The R and L cuts are chosen and posed with faces turned toward each other (the near-profile in the reference), not grinning at the camera. If no such pose exists, their heads are rotated on the neck pin and the alternate frames are searched.

## 9 · Acceptance bar (falsifiable; a fresh critic watches the film first, then reads the ledger)

1. **Clock and schedule (measured):** the on-screen minute hand reads 12:00 at t = 0 and t = 37, 12:02 at t = 10 and t = 47, and 12:07 at t = 35 and t = 72. `rules.json` reports MeetingWindow A = [12:01,12:03) and B = ∅, and the per-frame asserts pass.
2. **The meeting happens only in A (perceptually judged + structurally verified):**
   - In A, on [5,15) s, both puppets are behind the pail pile at once while the foreman's back is turned, and the apple visibly loses three bites, alternately to R and to L.
   - In B, no frame shows both in the corner. Their only co-presence is a crossing of ≤ 1.5 s at t ≈ 52–53.5, and the apple is left on her pail lid.
   - No frame in either version has both in the corner while the foreman faces FLOOR.
3. **The rule reads without exposition (perceptually judged, sound off first):** a critic watching muted can say that the couple moves only while the foreman's back is turned, and that in B the late bell left no shared time. The critic then compares with the sound on: bells and punches land within ±1 frame of the clock events in `cues.json` (measured from waveform onsets).
4. **Genuine frame-by-frame puppetry (structurally verified + judged):**
   - each puppet has ≥ 3 pinned joints moving on different timings;
   - head and bite substitutions happen on frames listed in `performance.json`;
   - the foreman's front and back are two different real photographs, never mirrored;
   - no piece slides as a rigid slideshow layer during the meeting.
5. **Aesthetic, tonal (measured, side by side):** for frames at t = 3, 10, 25, 47 and 60, set beside `calvino.webp`:
   - chroma ≤ 2 (R = G = B);
   - median luminance 112–132;
   - p5 ≤ 30 and p95 ≥ 220;
   - high-pass grain std 8–15 at 960 px.
   The contact sheet `films/swarm/renzo-e-luciana/aesthetic-compare.jpg` shows each frame beside the reference.
6. **Aesthetic, framing and intimacy (perceptually judged, side by side):** in the defining frame (t = 10) next to the reference, the couple spans ≥ 45 % of frame height. Their faces are turned toward each other and the food passes between their hands near the frame centre (as with the bowl and spoon). The door jamb and the clock are still in frame. A critic should judge it a photograph of real people sharing food, not a poster of pasted heads.
7. **Provenance and licence (structurally verified):** every photographic piece in `rig.json` maps to an LoC item marked "No known restrictions" (photographer named). Every sound in `cues.json` has a PD/CC0/CC BY/CC BY-SA source or is declared kit synthesis. All of them appear in `films/credits/renzo-e-luciana.json`. No material comes from the 1962 film. The film is ≤ 75 s and ≤ 6 MB.

## 10 · Risks and named branches
- *Mismatched cut-outs (three photographers):* mitigate by grading per piece, consistent shadows, and choosing poses whose light comes from the upper left. Branch: the Siegel "boy and girl" couple (one photograph, one light) replaces R, and possibly L, if the critic reads the pair as pasted.
- *Constraint reads as bad luck (§8 repair):* strengthen the foreman's sightline. He takes one step out of the doorway at 12:04 in B and his gaze holds on L. Do not add text.
- *Generic couple:* keep the rule and change one strategy. In B, Renzo bites once *for her*, so the token carries his mark.
- *Retained alternatives:* direction 1, Il paravento (silhouette IK hand), and direction 3, the light-box strips (used here only as the slate).

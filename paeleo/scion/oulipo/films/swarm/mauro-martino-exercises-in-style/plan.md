# Plan: Exercises in Style (Mauro Martino), SCION controlled variation

**Direction.** Direction 1, Cut-Paper Platform (`proposals/kf-1.png`), as chosen by the user.

**Paths.**
- Workspace: `films/swarm/mauro-martino-exercises-in-style/`
- Sources: `films/sources/mauro-martino-exercises-in-style/<role>/`
- Script: `films/mauro-martino-exercises-in-style.py`. It is rebuilt from scratch on `films/kit.py` and does not use the older `kit_cinema_b` draft.

## 0 · One declared change from kf-1, and why

In kf-1 the shove frame was tagged `Δ treatment = cut paper`, with an untreated photograph as the baseline. I swap the roles:

- **Baseline:** treatment `cut-paper` (the linocut house look of the reference).
- **Δ treatment:** `photographic-plate`.

There are two reasons:

1. **The overhead constraint.** The rule of one changed field forces Δ camera = overhead to keep the baseline treatment. A 1916 photograph has no top-down view, so an overhead "photographic" condition would have to be faked. A cut-paper plan can be honestly handmade.
2. **The reference look.** With the swap, two of the three conditions (and the test shot) sit in the reference's linocut aesthetic. The photographic condition then shows the foraged material in its own greys, as a genuine treatment delta.

What does not change:
- The test shot is still the kf-1 image: the shove on the rear platform, in cut paper.
- The matched-seed logic is unchanged.

## 1 · Creative thesis

One small bus incident is frozen as an exposure sheet: world positions, joint keys, anchor times and sound. It is re-rendered under single-field instructions:

- `camera: street-side → overhead`
- `treatment: cut-paper → photographic-plate`

Each instruction is rendered with the same two seeds, 0417 and 0418.

The film is an executable procedural animatic, standing in for the unavailable text-to-video generator. That makes the leverage of each changed word visible and countable:
- what moves on screen when only `camera` changes;
- what survives;
- what disappears.

The leverage is set against the stochastic spread between two draws of the same instruction.

The film would be bland if:
- the conditions looked like three different films (no leverage control); or
- they looked identical (no leverage at all).

## 2 · Defining beat and comparison baseline

**Defining beat (the test shot).** The baseline (street-side, cut-paper), seed 0417, at 1.20 s into the clip (film time **0:05.2**).

- The platform bus has just slid to its stop. Its separate cut wheels stop turning one drawing earlier.
- Two runners in long-stride silhouettes, as in the reference, reach the open rear platform.
- The lead runner's arm drives into the long-necked young man. He tips back against the brass stanchion, which is printed black.
- His plaited-cord hatband (a braid of notches cut through the crown, plus a loose cord end) swings out. It swings back over the next ~1.5 s and decays.

**What the viewer can point to.**
- the arm contact;
- the neck angle changing from upright to about 14° back;
- the shoulder meeting the stanchion;
- the cord end lagging the head by 2 drawings.

**Comparison baseline.** The same 1.20 s instant is shown in four places:
- in seed 0418 of the baseline (0:12.2);
- in Δ treatment at 0:21.2 and 0:28.2;
- in Δ camera = overhead at 0:37.2 and 0:44.2;
- simultaneously in the 3×2 grid at 0:51.2.

**What success looks like.**
- The protected action keeps the same timing in every condition.
- Only the named field's visual effect changes.
- Seed-to-seed differences are confined to unprotected elements: runner count and positions, walker phase, gouge noise, which seated passenger vacates.

## 3 · Lineage Genome and Olog

### Lineage Genome (compact)

**Source media.**
1. Queneau, *Exercices de style* (1947): a prose incident told 99 ways. The text is in copyright; it is paraphrased only, never quoted.
2. Martino, *Exercises in Style* (2023): text-to-video and text-to-image variations of the incident (charcoal, cubism, Dada stills), exhibited at the BCA.

**Target media.** A 64 s procedural animatic with foraged 1916–1933 Paris photographs and handmade linocut-style cut-paper staging. It is a comparison film with a manifest, seeds and a coverage ledger.

**Preserved relation.** One incident is invariant while the instruction varies. A reader or viewer judges the variation against a remembered constant.

**Changes in the four axes.**

| Axis | Change |
|---|---|
| Optics | One world stage, two projections: side elevation and top-down plan. |
| Formalism | A typed manifest, one-field deltas, matched seeds, exposure sheet on twos (12 drawings/s rendered at 24 fps). |
| Concept | Queneau's variation of manner, and Martino's variation by prompt, become a *measurement of leverage*. |
| Sound | One identical foraged street/engine bed, plus one bell, in every condition. This is a declared control and is not varied. |

**Epoch weights (0–100).**

| Epoch | Weight | Reason |
|---|---|---|
| Oulipo constraint writing, 1947–1970s | 90 | The rule of variation of one incident is the work's core. |
| Controlled generative video, 2022–2023 | 85 | Martino's medium: the prompt delta. |
| Silhouette and cut-paper animation, 1920s (Reiniger) | 75 | The articulated puppets carry the action legibly. |
| Woodcut/linocut print, 1920s–1930s (Masereel, Ward) | 60 | The reference's black-on-cream carved look. *Uncertain:* whether Martino prompted for linocut or charcoal; the catalogue calls it charcoal. |
| Paris press photography, 1910s–1930s (Agence Rol, Meurisse) | 70 | This is literally the foraged material. |
| Declarative film compilation (SCION 27) | 40 | Manifest-to-frames, with parameters kept beside the output. |

**Recorded uncertainties.**
- Whether Martino fixed seeds or kept the action constant across his variants is unknown. We do not claim it.
- The Madeleine–Bastille destination comes from the Agence Rol caption, not from Queneau, whose bus line is the S. This is a recorded substitution.

### Olog (types and arrows)

**Types.**
- `Manifest = {scene, camera ∈ {street-side, overhead}, treatment ∈ {cut-paper, photographic-plate}, seed, duration=7.0, size=(960,540), generator_rev}`
- `EventAnchor = {id, action, role, prop, cue, t}`
- `PromptDelta = {baseline_hash, field, old, new, intended_effect}`
- `RenderAttempt = {engine="kit.py procedural animatic", generator_rev (sha1 of script + stage + rig files), seed, settings, conditioning (exposure sheet hash, plate ids), output (frame range in film), observation}`
- `Sample = RenderAttempt × seed`
- `Coverage = {anchor id → visible | lost | partial}`

**Arrows.**
- `apply_delta : Manifest × PromptDelta → Manifest`
- `render : Manifest × Seed × t → Frame`
- `cover : Sample → Coverage`
- `compare : Sample × Sample → Diff` (per-element)

**The central operation** is `apply_delta(M0, δ)` followed by `render(M', s)` for each s in {0417, 0418}.

**Typed preconditions.**
- P1: `M0` is frozen, and its sha1 is recorded before any variant.
- P2: `δ.field ∈ {camera, treatment}`, and `δ.new ≠ M0[δ.field]`.
- P3: `keys(diff(M0, M')) == {δ.field}`. This is asserted in code.
- P4: The seed set is identical across conditions.
  - RNG streams are keyed by `(seed, element_id)` and are never drawn by the renderer or projector.
  - So the camera or treatment cannot change what the seed decides.
- P5: The same `generator_rev`, exposure-sheet hash and anchor schedule are used across conditions. A change of engine or version starts a new experiment.
- P6: Duration (7.0 s) and display size (960×540; 300×169 in the grid) are equal.

**Observable consequences.**
- C1: The protected anchors fire on the same drawing in every sample:
  - A1 stop at 0.90 s;
  - A3 shove at 1.20 s;
  - A4 stanchion contact at 1.33 s;
  - A6 seat taken at 5.50 s;
  - A7 bell at 6.00 s.
- C2: Each anchor is either visibly present or logged as lost. Overhead is *predicted* to lose:
  - **A-neck** (the long neck), measured as 0 neck-part pixels in the projection;
  - **A6-window** (the seat seen through the window), which becomes a hat disc moving under the roof edge.
  These losses are reported, not hidden.
- C3: Pixel differences between the baseline and a delta are confined to what the field governs:
  - `camera` changes the projection of everything;
  - `treatment` changes the fill material of every part, but not one silhouette outline vertex.
  The latter is measured with an outline IoU of 1.0 on the rendered masks.
- C4: Seed 0417 and seed 0418 differ only in unprotected elements. Their protected-puppet masks match exactly in every frame.
- C5: Re-rendering `(M, s)` gives byte-identical frames. Replay is equivalent, checked by hashing frames 0, 29 and 132.

**Counterexample (must fail the check).**
- A "Δ camera = overhead" render in which the plan projector lays out runners by drawing from the shared RNG.
- Seed 0417 overhead then yields 4 runners where the side view had 3. The runner count changed although only `camera` was edited.
- Result: P4 is broken, and C4/C3 fail. The candidate is quarantined. The diff is recorded in `verify/rejected-drift.json` with a frame strip.
- The verifier unit must build this broken variant on purpose once, show that the harness catches it, and keep it as a rejected drift example.

**Where views are equivalent and where they diverge.**

| | Side vs overhead | Cut-paper vs photographic |
|---|---|---|
| Equivalent | Exposure sheet, world (x, z) positions, anchor times, sound, destination text | Every outline, every joint angle, timing, framing |
| Diverge | Visibility: the neck is lost; the window seat is lost; the cord reads as a ring rather than a braid; the destination plate is read on the roof board | Tonal range, texture, legibility of the faces of the real passengers in the windows |

No interactive work is planned.

TTL is the default (2), and theory is not skipped.

## 4 · Invariants

**I1. Protected anchors.**
- The platform bus with an open rear platform and stanchion.
- The long-necked young man with a soft felt hat and a plaited-cord band.
- One shove at 1.20 s.
- The protest gesture at 2.0–3.2 s.
- The seat taken at 5.50 s.
- The bell at 6.00 s.
- Destination `MADELEINE – BASTILLE` unchanged.

**I2. One-field deltas.** Exactly one manifest field differs from the baseline per delta. This is asserted.

**I3. Matched seeds.** Seeds 0417 and 0418 are used in all three conditions. Per-element RNG streams are used; the renderer draws nothing.

**I4. Equal clips.** Equal duration (7.0 s = 168 frames), equal display size, and an identical audio bed. The PCM of each clip window is hashed, and the hashes are equal.

**I5. Frozen sources.** Immutable source IDs: a Commons file page plus the sha1 of the downloaded bytes for every plate. Nothing on screen lacks a ledger row.

**I6. Puppet integrity.**
- Limbs never detach: joint pin distance stays below 0.5 px.
- Joint-angle limits are held.
- The animation is drawn on twos: a new pose every 2 frames, with held frames between and no tween blur.

**I7. Secondary decay.** The cord's secondary motion starts after the shove impulse (at least 1 drawing later). Its energy decays below 2 % by 3.2 s and does not wiggle when nothing drives it.

**I8. Quarantine rule.** A broken hard invariant quarantines the candidate, which is moved to `verify/quarantine/`. Work resumes from the last accepted stage, rig or plates revision.

## 5 · Timed shot list (the Hard proof, section 6)

The film runs 64.0 s at 24 fps, 960×540.

### Clip timeline

Every one of the six samples uses the same 7.0 s clip timeline (t = time inside the clip):

| t (s) | Event |
|---|---|
| 0.00–0.90 | The bus slides in from left on its own layer and decelerates (ease-out, ~6 → 0 px/frame). Its wheels rotate at v/r and stop at A1 (0.90). |
| 0.00–1.10 | Runners cross toward the platform in long strides. Seed: 3 or 4 runners. |
| 1.20 | A3 shove. |
| 1.33 | A4: the shoulder meets the stanchion, and the cord swings out. |
| 2.0–3.2 | A5 protest: the head turns to the jostler, and the forearm rises with an open hand. The jostler shrugs. |
| 3.6–4.6 | Inside, one seated passenger rises and leaves the window. The seed decides which window. |
| 4.6–5.5 | The man ducks in and is seen in the window. A6: seated at 5.50. |
| 6.00 | A7: the bell, and the conductor's hand on the cord. |
| 6.2–7.0 | The bus starts to pull away (wheels turn again). The destination plate is legible throughout. |

### Shots

| # | Film time | Dur | On screen | Heard |
|---|---|---|---|---|
| S0 | 0:00.0–0:04.0 | 4.0 | Cream paper card. The title "one incident, three instructions" is hand-set. The baseline manifest types out in monospace, cream on a black tab: `scene: platform-bus encounter · camera: street-side · treatment: cut-paper · seeds: 0417 0418 · 7.0 s`. Manifest sha1 shown. | Bed fades in (−18 dB). Soft key clicks (kit `click`, declared synthetic). |
| S1 | 0:04.0–0:11.0 | 7.0 | **BASELINE · seed 0417** (the TEST SHOT at 0:05.2). Street-side elevation. **Layers:** carved Haussmann facade band; tint-block grey upper storeys; two-tone printed rectified Rol 1916 bus with rotating cut wheels; handmade platform, chain and stanchion; gouged pavement; articulated puppets; long horizontal cast-shadow strokes. **Tag** bottom-left: `baseline · seed 0417 · t`. | The same bed. Bus brake squeal from the foraged bed if present, otherwise none added. A thud at 1.20 (shove, kit `thud`, declared). Bell at 6.00. |
| S2 | 0:11.0–0:18.0 | 7.0 | **BASELINE · seed 0418.** The protected action is identical. Differences are runner count and positions, walker phase, gouge noise, and which passenger vacates. | The identical clip audio. |
| S3 | 0:18.0–0:20.0 | 2.0 | Delta card. The manifest line `treatment: cut-paper` is struck through over 6 frames, and `photographic-plate` is typed. PromptDelta shown: intended effect "same outlines, photographic fill". | Bed continues. Key clicks. |
| S4 | 0:20.0–0:27.0 | 7.0 | **Δ treatment · seed 0417.** **Same frames and outlines, different material.** The bus is the rectified Rol cutout in its own continuous greys, with the real 1916 passengers visible in the windows. The facade is the rectified real Haussmann building from the right of the same Rol plate. The pavement is the Rol cobble plate. Puppet parts are filled with GrabCut coat, hat and trouser textures cut from the Peyriras 1933 Bourse crowd, as photographic cutout puppets on the same rig. | The identical clip audio. |
| S5 | 0:27.0–0:34.0 | 7.0 | Δ treatment · seed 0418. | Identical. |
| S6 | 0:34.0–0:36.0 | 2.0 | Delta card: `camera: street-side` struck, `overhead` typed. Intended effect: "plan view; shove as displacement". | Clicks. |
| S7 | 0:36.0–0:43.0 | 7.0 | **Δ camera = overhead · seed 0417**, in cut-paper treatment. **The plan:** a carved bus roof (ribs, cut-letter destination board along the roof edge, open platform with stanchion as a black dot); a kerb line and cornice shadow at the top edge; pavement gouges seen from above. **The puppets:** hat discs with the cord as a notched ring, plus shoulder ellipses and stride feet. **The shove:** the jostler's disc drives the man's disc onto the stanchion dot at 1.20 s. The cord end swings as a short tail. **Lost:** the neck. | Identical. |
| S8 | 0:43.0–0:50.0 | 7.0 | Δ camera · seed 0418. | Identical. |
| S9 | 0:50.0–0:58.0 | 8.0 | **Comparison grid.** Three rows (baseline / Δ treatment / Δ camera), two columns (0417 / 0418), each cell 300×169, all playing the 7.0 s clip in sync, with a 1.0 s hold on the shove frame at the end. **Anchor chips** under each cell flip cream or black at their anchor time: stop · shove · stanchion · cord · protest · seat · bell · destination · neck. On the overhead row, `neck` and `seat-in-window` flip to a struck "lost". | Identical clip audio once, then silence for the hold (declared). |
| S10 | 0:58.0–1:04.0 | 6.0 | **Coverage report card** (handmade typeset ledger). <br>• The intended-effect rate per condition, as *n of 2 inspected samples*. <br>• The anchors that disappear, with the exact anchor IDs. <br>• The seed capability: "procedural generator, seeds repeatable, verified by frame hash", which separates the observed samples from any claim about text-to-video generators in general. <br>• Rejected drift: one strip from the counterexample render. | The bed fades out. |

**Defining-beat timestamps.**
- 0:05.2 (S1)
- 0:12.2 (S2)
- 0:21.2 (S4)
- 0:28.2 (S5)
- 0:37.2 (S7)
- 0:44.2 (S8)
- 0:51.2 (the grid)

### FORAGED and HANDMADE elements

#### FORAGED

**F1. The Agence Rol bus photograph.**
- *1-6-16, nouvel autobus Madeleine-Bastille*, Agence Rol, 1916. Gallica via Commons. Already at `commons/rol1916.jpg`, 1280×911 L.
- Re-verify `LicenseShortName` through the extmetadata API.
- **Bus:** rectified with cv2.warpPerspective from its 3/4 view to a side elevation, then cut out with GrabCut and a hand polygon.
- **Wheels:** the two visible wheels are cut out separately, rectified to circles, and used as rotating pieces.
- **The real rear platform and conductor:** at x≈1040–1080.
- **The right-hand Haussmann facade:** rectified for the photographic-plate treatment.
- **The cobbles:** used as the pavement plate.

**F2. The Peyriras 1933 Bourse crowd.**
- *Grève des autobus – Place de la Bourse*, Peyriras, 1933. Gallica via Commons. Already at `commons/bourse1933.jpg`.
- **Re-verify the PD basis.** A photographer's death date or anonymous Gallica PD tag is needed. If it is not PD/CC, drop it and source coat and hat textures from Agence Rol/Meurisse 1910s–1920s crowd plates on Commons.
- **In cut-paper treatment:** the waiting crowd is cut out as GrabCut figures and printed as a black mass behind the platform, as a mid-layer.
- **In photographic-plate treatment:** the coat, hat and trouser textures fill the puppet parts.

**F3. The sound bed.**
- Search the Moving Image Archive cache for a clip with `audio.kind == "sound"`, low `speech_band`, and street, traffic, engine or bus content.
- A Commons PD or CC audio file of a bus or tram bell and street can be used instead.
- One bed and one bell are used, identical in every condition.
- If no real bell is found, use kit `bell` and declare it synthetic in the ledger.

**F4 (optional, only if Commons answers).** *Paris – Fahrgäste hinter dem Autobus* (LABW, 1955, CC BY 4.0). It is a reference for platform posture only; it is **not** traced and **not** shown. Skip it on HTTP 429.

#### HANDMADE

**H1. The carved Haussmann facade.**
- Cornice, balconies, cross-mullioned windows, mansard dormers.
- Built from tapered gouge strokes with a seeded per-cut wobble, in two blocks: a black key block and a warm-grey tint block.

**H2. The gouged pavement.**
- Long horizontal V-gouge strokes, in varied lengths and taper.
- Puppet shadows cut as horizontal slivers under the feet.

**H3. The two-tone bus print, and the platform hardware.**
- The rectified Rol bus is printed through CLAHE, a threshold and a tint-block pass.
- Handmade parts: the rear platform floor, chain, stanchion and conductor's bell cord.
- The destination board `MADELEINE – BASTILLE`, in carved capital letterforms.

**H4. The articulated silhouette puppets.**
- The cast:
  - the long-necked man (felt hat with a braided notched cord, a loose cord end, long tapered neck, narrow coat);
  - the jostler (bowler, broad back);
  - 2–3 seed-chosen runners;
  - a conductor;
  - a seated passenger.
- Parts are drawn as fluid closed spline shapes (coat tails, hands with thumbs, profile with nose and chin), never capsules.
- The parts are pinned at their joints.

**H5. The overhead plan stage.**
- The bus roof and plan pieces, and the plan forms of the same puppets.

**H6. The cards, chips and coverage ledger typography.**

## 6 · AESTHETIC TARGET

**Reference.** `assets/references/martinoCharcoal.webp` is the look for this direction. In the catalogue it is a gallery image; the main image is `martinoDada.webp`.
- `martinoDada.webp` is an aerial, illustrated, muted-colour plaza. It is consulted only as precedent for the *overhead* framing: a bus seen from high above, with people as small dark marks.
- `martinoCubism.webp` shows a steep high camera with embroidered primaries. It is not targeted.

The reference images are never copied, traced or pasted.

**Medium.** A black-on-cream relief print (linocut or woodcut) with charcoal-soft edges. It is a printed object, not a filtered photograph. We reach it by actually carving the stage procedurally and printing the real photograph through a threshold and tint block, like a photo-linocut transfer.

**Tonal range (measured with PIL on the 400×240 reference).**
- Luminance percentiles p2/p25/p50/p75/p98 = **24 / 40 / 91 / 187 / 234**.
- Mean chroma 12.6, which is nearly neutral but warm.
- It is **not pure two-tone.** About 30 % of the pixels are mid-greys (#958e85, #47443f).
- kf-1 measured 1 / 16 / 128 / 223 / 241: blacks too deep, almost no mids. The build must lift the ink to the reference's warm black and add a real second (tint) block.

**Palette (sampled, median-cut, 6 colours) and target tokens.**

| Reference colour | Share | Role |
|---|---|---|
| #22211f | 21.1 % | ink |
| #2d2c2a | 18.5 % | ink, worn |
| #47443f | 13.8 % | dark tint |
| #958e85 | 15.7 % | grey tint block |
| #d3cbbc | 17.5 % | shaded paper |
| #eee6d6 | 13.4 % | paper |

The target tokens are:
- ink (34, 33, 31)
- tint (149, 142, 133)
- paper (238, 230, 214)
- shade paper (211, 203, 188)

No pure black and no pure white.

**Light.**
- Flat and frontal, with no modelled shading on figures. They are solid silhouettes.
- Light reads only as cream gaps: lit windows, leg gaps, the arched lit platform opening.
- Shadows are long horizontal cast strokes on the pavement under the walkers, as in the reference.

**Texture.**
- Paper grain.
- Horizontal gouge streaks in the street and sky.
- Slight ink-starved, broken edges on the large black areas, made by a real per-print noise mask on the key block, re-seeded per seed (not per frame, so it does not boil).
- Charcoal-soft rather than vector-crisp edges: a 0.6–1.0 px edge feather on the print only.

**Framing and scale.**
- A dead side-on elevation.
- The bus's long side fills **55–65 % of the frame width**, its body between y≈32 % and y≈75 %.
- The facade band fills the top ~35 %. The pavement is the bottom ~25 %.
- Running figures are **~22–30 % of frame height**, overlapping the bus's lower half, in wide strides with cream between their legs.
- In S1 the platform is placed right of centre (x≈62–75 %), so the shove reads at full size.

**Typography.**
- The reference has none. On-film labels are restricted to a small monospace tag, cream on an ink tab, bottom-left, as in kf-1.
- Cards use the same paper, ink and serif or monospace from `assets/fonts`.
- The destination board is carved capitals.

**Pacing.**
- The reference implies a mid-stride instant.
- Puppets run on twos (12 drawings/s). Holds are crisp, and the stop and the shove are snapped, not tweened.
- The bus deceleration is smooth because it is a layer slide, not drawn.
- Cards are brief (2 s). Every condition has the same 7 s rhythm.

**How real material and technique reach the target.**
- The real 1916 photograph supplies the bus and the passengers in its windows: real geometry and real heads.
- Rectification gives the elevation.
- The threshold plus tint-block print gives the two blocks.
- The carved facade and gouged pavement are actual stroke-built carving.
- The puppets are real cut articulated shapes.

A grade is used only to unify the two blocks to the sampled tokens.

## 7 · Animation technique SCIONs (from `swarms.json`)

### 1. #2 Lotte Reiniger, Articulated Shadow Theater

**Why.** The proof is an act of legible action in silhouette: a shove, a protest, a seat taken. Reiniger's pinned joints, angle limits, replacement profiles and exposure sheet are exactly the rig the matched-seed logic needs. The bar reads relationships with all colour removed.

**Applied in:**
- S1, S2, S4, S5 (the same rig with the fill material swapped);
- the plan-form puppets in S7 and S8;
- an exposure sheet on twos.

Thumbs and hands stay distinct in the shove and the protest.

### 2. #29 GrabCut, Cutout Extraction

**Why.** All the foraged material must become usable animation layers:
- the bus;
- separate wheels;
- the platform and conductor;
- the Bourse crowd figures and coat textures.

These need actual GrabCut with box and scribble seeds plus a hand polygon. Its invariants are no background islands and failure masks exported.

**Applied in:**
- S1 and S2 (the printed bus, wheels and crowd mid-layer);
- S4 and S5 (photographic bus, facade and cobbles, puppet fill textures).

### 3. #41 Secondary Dynamics, Inertia and Restraint

**Why.** The cord swinging after the shove is the one secondary motion the incident asks for. Its bar is that it starts after the primary impulse and decays when the source stops, which keeps motion purposeful.

**Applied in:**
- every condition: a 3-link damped pendulum chain on the hat, driven by the head's acceleration, integrated at 24 Hz with a semi-implicit Euler step, and sampled on twos;
- the coat tail as a 1-link spring;
- in overhead, the cord end as a ring tail.

### Supporting methods, not separate SCIONs

- forward kinematics (#32) inside the Reiniger rig;
- occlusion order (#45): bus body, then puppet behind the platform rail, then stanchion in front;
- manifest compilation in the spirit of #27.

## 8 · Swarm units (section 5 roles, merged)

### U1 · plates — forager, cutter and sound (render-operator duties for sources)

**Roles combined.** Continuity owner for source IDs; puppet cutter (GrabCut); sound forage.

**Tasks.**
- Re-verify F1 and F2 licences through Commons extmetadata. Record the sha1 of each file.
- Rectify the Rol bus to an elevation (record the homography). Extract:
  - the bus body as RGBA;
  - the wheels as separate RGBA circles, with hub centres;
  - the platform and conductor;
  - the right facade plate, rectified;
  - the cobble plate.
- From Bourse 1933, extract:
  - 6–10 crowd figures as RGBA for the waiting mass;
  - coat, hat and trouser texture swatches.
- Export the failure masks.
- Forage the sound bed and bell from the MIA cache (choose by listening and inspecting). Cut it to a 7.0 s loopable clip bed plus a bell.

**Output.** `plates/plates.json`, the evidence ledger. For every item it records:
- source page, file URL, licence, sha1;
- homography, crop and mask paths;
- `used_as`;
- draft credit rows in the `films/credits` schema.

**Also.** A contact sheet `plates/plates-sheet.jpg`. Media goes in `sources/.../plates/`.

### U2 · stage — linocut carver (handmade world, both projections)

**Tasks.**
- Build the carved Haussmann facade, the gouged pavement and the platform hardware (chain, stanchion, bell cord).
- Build the carved destination board `MADELEINE – BASTILLE`.
- Make the two-tone and tint-block print of U1's rectified bus and wheels, and the black-mass print of the crowd mid-layer.
- Build the overhead plan stage (carved roof, kerb, plan gouges) from the same world coordinates.
- Produce the photographic-plate stage composites from U1's plates.

These are all deterministic functions of `(seed, element_id)` and are exposed as importable code: `stage/stage.py`. They are pure functions returning PIL RGBA layers, with no RNG draws in the renderer.

**Output.**
- `stage/stage.py`
- `stage/stage-sheet.jpg`: side cut-paper, side photographic and overhead stills at the shove instant, placed side by side with the reference at equal height, with measured percentiles and palette printed.

**Media.** `sources/.../stage/`.

### U3 · rig — continuity owner for event anchors, gesture animator and dynamics

**Tasks.**
- Write `anchors.json`: the EventAnchors (action, role, prop, cue, t) and the protected set.
- Write the frozen baseline manifest and its sha1.
- Draw the hand-made fluid spline part shapes for all puppets: coat tails, hands with thumbs, profiles, the cord hat with a braid of cut notches.
- Build the FK rig with pins and angle limits.
- Key the exposure sheet on twos for the 7.0 s clip. This includes the run cycles (6 drawings, long stride), the shove, stanchion contact, protest, duck-in and seat.
- Add the #41 cord and coat-tail dynamics.
- Add the seed-controlled unprotected variation. Per-element RNG decides: runner count, runner x and phase, walker phase, which seat vacates.
- Write the plan projection of each puppet.

**Output.**
- `rig/rig.py`: `pose(seed, t) → world parts`, `draw_side(…)`, `draw_plan(…)`, with fill material passed in by the treatment.
- `rig/anchors.json`
- `rig/exposure.json`
- `rig/shove-strip.png`: 12 consecutive drawings of the shove in side and plan view.
- `rig/cord-energy.json`: cord energy per frame, demonstrating I7.

**Media.** `sources/.../rig/`.

### U4 · verify — variant authors' delta log, render-operator pinning and coverage verifier

**Tasks.**
- Write `verify/manifests.json`: the baseline plus the two PromptDeltas, each with its diff, asserting one field.
- Write `verify/render-attempts.json`: generator_rev hashes, seeds, settings, conditioning hashes and frame ranges.
- Write the coverage harness `verify/coverage.py`. It renders masks per anchor from the rig and stage and measures:
  - anchor visibility per sample;
  - outline IoU between treatments;
  - protected-mask identity between seeds;
  - frame-hash replay;
  - per-clip audio PCM hashes.
- Build the counterexample (RNG-coupled overhead projector) once, show the harness fails it, and save `verify/rejected-drift.json` and a strip.
- Produce `verify/comparison-sheet.jpg`: all six samples at the shove instant, at equal size, plus the reference side by side.

**Output.**
- `verify/coverage.json`: the rate of intended effect per condition, the lost anchors and the capability notes.
- The sheets above.

**Media.** `sources/.../verify/`.

### Dependencies

- U1 delivers the rectified plates first. U2 and U3 can start immediately on handmade parts against placeholders that keep the same geometry.
- U4 needs U2's and U3's module APIs, and writes its manifest and counterexample against them.
- The editor (run separately by the workflow) writes `films/mauro-martino-exercises-in-style.py` on kit.py. It imports `stage.py` and `rig.py`, composes the shot list in section 5, and writes:
  - the credits file `films/credits/mauro-martino-exercises-in-style.json`, from U1's draft rows;
  - the notes file `films/notes/mauro-martino-exercises-in-style.txt`.

## 9 · Acceptance bar (falsifiable; for the fresh critic)

1. **Hard proof structure.** The film contains a baseline and exactly two single-field deltas, `camera: overhead` and `treatment: photographic-plate`. Each is shown for seeds 0417 and 0418 at 7.0 s each and at equal display size, then together in a 3×2 grid. `verify/manifests.json` shows each delta's diff touching exactly one field.
   - **Fails if:** any condition is missing, durations differ by more than 1 frame, or a manifest diff has more than one key.
2. **Protected action.** In all six samples the shove lands at clip t = 1.20 s (±1 drawing), and the seat is taken at 5.50 s. The destination `MADELEINE – BASTILLE` is legible: on the side board in the side views, on the roof board in overhead.
   - **Check:** the critic steps frames at 0:05.2, 0:12.2, 0:21.2, 0:28.2, 0:37.2 and 0:44.2.
   - **Fails if:** a sample lacks the shove or shows another destination.
3. **Leverage is traceable.**
   - The Δ treatment frames keep identical silhouettes and outline positions to the baseline at the same t (outline IoU = 1.0 in `coverage.json`), and change only the fill material, which is visibly photographic.
   - The Δ camera frames change the projection and report the long neck (and the seat in the window) as *lost* in the coverage chips and ledger.
   - Seed 0417 vs 0418 differ visibly only in unprotected elements.
   - The counterexample strip is shown as rejected drift.
   - **Fails if:** a delta changes something outside its field, or the neck loss is not reported.
4. **Frame-by-frame animation.**
   - The shove sequence is genuinely animated on twos: frame-stepping 0:05.0–0:05.8 shows at least 4 distinct drawn poses, with the arm, torso, neck and head angles changing, and the long-necked man tipping back with weight (anticipation, contact, recoil).
   - The cord begins moving 1–2 drawings after the impact and settles by about 3.2 s.
   - No limb detaches; the hands show thumbs.
   - Puppet parts are fluid spline shapes, not capsules or rectangles.
   - The bus's separate wheels visibly rotate while it moves and stop when it stops.
   - **Fails if:** the action is only pans or fades over stills.
5. **Aesthetic, side by side (measured).**
   - A baseline frame at 0:05.2 is placed next to `martinoCharcoal.webp` at equal height (`verify/comparison-sheet.jpg`). Its measured luminance p2 ≥ 15 and p98 between 222 and 242.
   - At least 12 % of its pixels lie in the mid-tone band L 70–170 (the real tint block; the reference is about 30 %, kf-1 about 10 %).
   - Mean chroma ≤ 20. The paper colour is within ΔE76 ≤ 10 of #eee6d6, and the ink within ΔE76 ≤ 10 of #22211f.
   - **Fails if:** any of these numbers is out of range.
6. **Aesthetic, side by side (perceptual).**
   - Viewing the same pair at normal size, the critic judges that the film frame reads as the same medium as the reference: a carved or cut relief print on cream.
   - It matches the framing: a long side-on bus spanning 55–65 % of the width, a facade band above, gouged pavement below, running silhouettes about a quarter of the frame tall overlapping the bus with cream between the legs, and long horizontal cast-shadow strokes.
   - It is not a filtered photograph or vector clip-art, and it is at least as strong as kf-1.
   - **Fails if:** the critic can point to a photo-filter look in the cut-paper condition, to capsule or stick limbs, or to framing off these ranges.
7. **Provenance and sound.**
   - Every foraged item on screen or heard has a row in `films/credits/mauro-martino-exercises-in-style.json` with a licence in {PD, CC0, CC BY, CC BY-SA}, verified from Commons extmetadata, or the movingimagearchive.com wording given in the brief.
   - The sound bed and bell are byte-identical across the six clip windows (PCM hashes in `coverage.json`).
   - Any synthesized sound is declared as such.
   - **Fails if:** there is an unlisted source, an NC or ND or unknown licence, or the audio differs across conditions.
8. **Honest report.** The closing card and `coverage.json` report:
   - the intended-effect rate as *n of 2 inspected samples* per condition;
   - the exact lost anchor IDs;
   - the seed capability (repeatable, verified by frame hash).

   The report separates the observed samples from claims about generators in general.
   - **Fails if:** the report claims general generator behaviour or omits a lost anchor.

## 10 · Budget

- Each unit has about 45 minutes.
- New downloads are under 75 MB. Reuse the 0.9 MB already in `sources/`.
- No git commits. No other film's files are touched.

# les-lieux-dune-fugue · swarm plan (director)

Work: `prompts/les-lieux-dune-fugue.md`. Chosen direction: **Round 2 · 3, The Paper Facade** (`proposals/kf-3.png`). The film is a cut-paper tabletop collage built from public-domain Library of Congress (Highsmith) photographs and lit by one lamp. It has no figure and no archive footage on screen. The test shot is the carriage door opening onto the remembered bench.

Revision base: proposals r2 (`proposals/src/kf3.py`, sources in `films/sources/les-lieux-dune-fugue/r2/`). The plan is rebuilt from scratch, and r2 code may be read for reference.

---

## 1 · Creative thesis

A paper model of an ordinary carriage door is "filmed" twice from the same position: once in morning lamp-light and once in evening lamp-light. The second time, the door does what memory does. Its two dark leaves swing open on their hinges, and behind them, on a deeper plane and in a different (cold, winter) light, stands the bench that the voice remembers. The door closes, and the stone is flat again. Then the real bench returns, framed exactly as before, in total silence.

The distance between the filmed present and the remembered past becomes a physical depth: the space behind a hinge. The returning places (door twice, bench twice) give orientation while the captioned voice jumps out of order.

**What would make it bland:** a crossfade of a bench photo over a door photo, uniform digital drop shadows, a "paper" texture filter, or places that look interchangeable.

## 2 · Defining beat and comparison baseline

- **Defining beat (0:31–0:41):** P01, capture B. The two warm-black paper leaves rotate open on fixed hinges: the left to 58°, the right to 64°, the right one 4 frames late. They are foreshortened and darken by cos θ against the lamp. A remembered bench is revealed on a plane at depth 0.6, lit cold and from a different direction than the stone. The camera trucks 6 px and the bench moves less than the facade. The caption reads « Le banc, c'était l'hiver, à peu près. », and the record line shows `souvenir · vers l'hiver (intervalle) · lien P01→P03 : INFÉRÉ`. The leaves then close with weight (overshoot, a thud), and a hard cut takes us to P03 in silence.
- **What the viewer should be able to point to:** "the door opened and the bench from before was behind it, in another light. Then the door shut and the real bench came back, and everything went quiet."
- **Baselines** (the critic renders or sees both):
  - (B0) the r2 direction-1 approach, a 3 s screen-blend of BENCH over DOOR-C, which is a dissolve with no hinge;
  - (B1) the chosen keyframe `proposals/kf-3.png`, which is the look to meet or beat.

  Known faults of kf-3 that the build must fix:
  - the mortar joints are thick and near-black, so the wall reads as cartoon brick (the reference joints are faint, about 14 grey-levels below the stone);
  - the door is centred in a wide shot (the reference door is left of centre and runs out of the bottom of the frame);
  - the carved jambs are too wide and ornate;
  - the bright blue "7" plaque is too big;
  - the caption bar sits at the top;
  - the drop shadows are uniform and digital, all of one offset.

## 3 · Lineage Genome (compact)

| field | value |
|---|---|
| source | *Les Lieux d'une fugue*, Georges Perec. 16 mm colour TV documentary, Paris locations, Perec's text in voice-over. (Shot c. 1976, broadcast 1978. The catalogue gives 1978; the exact dates are **uncertain**, not verified here.) |
| target | 4:3 digital short, 960×720, 24 fps (paper moves on twos, 12 fps). Cut-paper tabletop collage from PD photographs, a multiplane camera, captions as the voice, and declared silence. |
| preserved relation | Present-day empty places plus a voice that is somewhere else in time. A place returns to give orientation while the memory jumps. |
| optics | A live 16 mm camera on the street becomes a locked-off camera over a lit paper model: one point lamp, raised pieces, real cast shadows, depth-of-field by plane. |
| formalism | Typed Place and MemoryFragment records. Three independent clocks: capture_time, remembered_time and screen_time. [pair] is the only operation that joins image and memory. |
| concept | The memory is not superimposed. It is *behind the door*, and opening is a hinge operation (forward kinematics), so the memory has an architecture. |
| sound | Spoken voice becomes captions (no TTS). There is a present room/street tone, a remembered muffled bell under the memory only, a door thud, and digital silence for the return. |

Epoch weights:

| epoch | weight | reason |
|---|---|---|
| Perec's place/memory writing (*Lieux* project 1969–75, *W ou le souvenir d'enfance* 1975, *Espèces d'espaces* 1974) | 90 | It is the source of the place + uncertain-memory method. (Dates are from general knowledge and not re-verified.) |
| French essay/documentary film, 1955–78 (Resnais, Marker; voice dislocated from image) | 70 | Grammar of voice against present place. |
| Oulipo constraint practice, 1960– | 35 | Perec's films are not strictly constrained works. The link is **uncertain** and kept low. |
| Cut-paper and multiplane animation (Reiniger 1920s, Ernst 1934, Norstein 1970s, Gilliam 1970s) | 65 | The target technique: paper, depth and hinge. |
| Open archive photography (Highsmith gift to LoC, 2000s–) | 55 | The physical substance of every piece. |
| Provenance/ledger computing (2010s–) | 40 | Typed records, intervals and link status. |

### Olog

Types (boxes):

- **◻Place** — `place_id` (P01 door, P02 junction, P03 bench), `cue` (the repeatable visual cue: dark two-leaf door + "7" plaque; pavement seam fork; slatted bench + tree trunk), `adjacency` (P01→P02→P03, route), `capture_scope` (which paper pieces and source photos make the place).
- **◻Observation (shot)** — `shot_id`, `place_id`, `camera_pose` (identical for repeats), `lamp_state` (A morning: upper left, low warm; B evening: right, raking), `capture_time` (the staged time of day of the lamp, plus the source photo's real LoC date, recorded separately), `screen_time [in, out]`.
- **◻MemoryFragment** — `frag_id`, `speaker` (fictional narrator, adult), `remembered_time` (an interval or "unknown"; never exact without evidence), `place_link` (place_id + status ∈ {asserted, inferred, unknown}), `confidence`, `provenance` ("fiction written for this work"; "hearsay" where a third party is quoted), `text_fr`, `gloss_en`.
- **◻Beat** — the output of [pair].

Arrows:

- Observation —*shows*→ Place
- MemoryFragment —*claims link (status)*→ Place
- Place —*adjacent to*→ Place
- [pair] : Observation × MemoryFragment → Beat

**[pair] typed preconditions**

1. `obs.place_id` is in the Place register and `obs.camera_pose` is recorded.
2. `frag.remembered_time` is an `Interval(lo, hi, label)` or `Unknown`. An `Exact` is legal only with an evidence id.
3. `frag.place_link.status` ∈ {asserted, inferred, unknown}.
4. `frag.screen_time ⊆ obs.screen_time` (the caption lies inside the shot that carries it).
5. If `frag.place_link.place_id ≠ obs.place_id`, the beat is **dislocated** and must carry `dislocated: true`.
6. The memory image of a dislocated beat must use a light state that is not one of the stage lamp states.

**Observable consequences**

- The caption appears in serif italic within the shot's interval.
- The present-tense slate (mono, small, `P01 · prise B · soir`) stays visibly distinct from the recollection.
- Inferred links show `INFÉRÉ` on screen and in the ledger.
- A dislocated beat shows the linked place behind or inside the observed place, on its own plane and in its own light, never registered as if it were physically there.

**Counterexample for the central operation.** Pairing F5 (bench, winter) with Obs P01-B under any of these errors fails, and the beat is quarantined:

- (a) writing `remembered_time = 1952-01-12`;
- (b) writing `place_link P01→P03 status: asserted` with no evidence;
- (c) lighting the bench plane with lamp B, so it reads as a claim about the visible present ("there is a bench behind this door").

**Where replays and alternate views are equivalent, and where they diverge**

| pair of views | equivalent | diverge |
|---|---|---|
| P01-A vs P01-B | place_id, camera_pose, every piece's rigid transform, stone pixels | lamp state, shadow direction and length, capture_time, the leaves' action, sound |
| P03-first vs P03-return | place_id, plate, framing | sound (park tone vs declared digital silence), narrative status (before vs after the memory) |
| P03-present vs P03-memory (inside the door) | place_id, the same Highsmith bench | light (warm present vs cold "winter" print), time status (observation vs recollection), link status (the memory's link is INFERRED) |

TTL: default 2, so no child inquiry is planned. Interactive work: not applicable (linear film). The spatial-walkthrough variant from §8 is out of scope for this run and is recorded as not attempted.

## 4 · Invariants (hard; quarantine on breach)

- **I1 Site identity.** Each shot has exactly one place_id. P01-A and P01-B share camera pose and piece transforms exactly (measured: identical transform table, and stone-joint edge maps coincide within 1 px). P03-first and P03-return use the same plate and framing.
- **I2 Recollection status.** Every fragment's remembered_time is an interval or unknown. No exact date without evidence. Every inferred link is visible as INFÉRÉ on screen and in the ledger.
- **I3 Dislocated voice.** The voice is never synced to an on-screen action as cause and effect. It speaks from "now, elsewhere".
- **I4 Present-day default.** No enacted figure appears. The departure is carried by the door, the route and the bench. Enacted images: none (declared).
- **I5 Memory light ≠ stage light.** The memory bench plane is cold (mean B ≥ R) and lit from its own direction. The stone is warm (mean R−B ≥ 35).
- **I6 Silence.** The P03 return plus the record card is digital silence: every audio sample is 0 for at least 6 s (measured). A silence slate is shown.
- **I7 Provenance.** Every foraged pixel and sound is in `films/credits/les-lieux-dune-fugue.json` with an accepted licence. Handmade pieces are listed in the ledger.
- **I8 No style costume.**
  - Set `ink._grain = False`: no kit grain, no vignette filter.
  - Texture comes only from foraged photographs and a foraged paper scan.
  - Shadows come only from the lamp model (offset = height × tan(elevation), blur ∝ height × lamp size).
- **I9 Hinge (FK).**
  - Each leaf's hinge edge stays on its jamb in every frame (|Δx| ≤ 0.5 px).
  - The projected leaf height at the hinge is constant.
  - Studs, panels and the handle are children of the leaf and never slide.
- **Concurrency.** Three write scopes are kept separate: route evidence (U1), picture/paper stage (U2) and narration/sound (U3). If a place is re-catalogued (for example, P02's source is changed), the narration segments tied to it are blocked until U3 confirms them.

## 5 · Hard proof: timed sequence (57.0 s, 960×720, 24 fps)

Captions are the voice. Each caption has French in cream serif italic, with a small muted English gloss below it, placed low over the plinth or ground zone. Slates (present claims) are 13 px mono at top left, muted. Each paper piece moves only on twos (12 fps).

| # | time | place / shot | on screen | heard | material |
|---|---|---|---|---|---|
| 1 | 0:00.0–0:08.0 | **P01 · prise A · matin** | Frontal, locked-off paper facade. The dark two-leaf door is left of centre and runs out of the bottom of the frame. Warm ashlar blocks with faint joints, narrow carved vine jambs, a light plinth course at the bottom, a dark iron balcony band across the top edge, and a small dark "7" plaque right of the door. Lamp A is upper left and low, so each piece casts a short shadow down-right. At 0:05.5 the left leaf opens about 18° (FK, eased), holds 0.5 s, and swings shut at 0:07.0 with a 2° overshoot and settle. This is the departure, shown only by the door. | Present street/room tone, low. At 0:07.0, a door thud with a short wooden rattle. Caption F1 0:01.0–0:05.0. | Facade: HANDMADE paper pieces cut from FORAGED LoC Highsmith DOOR-C (stone, jamb carving) and DOOR-S (the two leaves), printed on a FORAGED paper-stock scan. Balcony band cut from a FORAGED LoC ironwork photo (optional). Plaque HANDMADE (lettered card). Thud: FORAGED if found, else kit thud plus click. |
| 2 | 0:08.0–0:19.0 | **P02 · carrefour** | Paper junction, frontal, slightly high. Foreground: a kerb strip and pavement whose seam forks left and right. Mid plane: two facade corners, stone. Far plane: a street receding. A lateral camera glide of 10 px (multiplane: near 1.0, mid 0.5, far 0.15) reveals the fork. At 0:13 a hand-cut paper route thread (one ochre strip) is laid along the seam in 6 drawings, following the left branch. | Street tone continues, slightly wider. Caption F2 0:09.5–0:15.5. | HANDMADE pieces from a FORAGED frontal street-corner/pavement photo (U1 selects: Highsmith/LoC PD first; fallback is `Rue_du_Soleil_rue_de_Belleville_Paris_20e.jpg`, CC BY-SA 4.0 Polymagou, cropped to stone and kerb with no signage). Route strip HANDMADE. |
| 3 | 0:19.0–0:28.0 | **P03 · banc (présent)** | Paper park: leaf-litter front strip (depth 0), the bench cutout (0.4) and its real cast shadow, tree trunks (0.7), far park (1.0). Warm present light (lamp A). A slow 8 px truck, then hold. The bench is framed so it can be recognised again: slatted back, iron arm, a trunk behind it to the left. | Park tone: wind and a few birds. Caption F3 0:20.5–0:26.0. | HANDMADE planes cut (GrabCut) from FORAGED LoC Highsmith BENCH (`sac_23429.jpg`, LoC 2013633886). |
| 4 | 0:28.0–0:44.0 | **P01 · prise B · soir** (same position) | The identical facade, with lamp B to the right and raking low, giving longer shadows down-left and a warmer, lower key. The stone joints coincide with shot 1. 0:28–0:31: held closed. Caption F4. **0:31.0–0:36.0: the leaves open** (0→58° left, 0→64° right, right leaf 4 frames late; ease-out with a 3° overshoot and settle). The camera trucks 6 px. Behind them: the memory bench (0.6) and park (1.0) in a cold blue-grey print lit from the upper left, with a haze between planes. The bench settles 2 px. 0:36–0:41: hold. Caption F5, with record line `souvenir · vers l'hiver (intervalle) · lien P01→P03 : INFÉRÉ`. 0:41.0–0:43.5: the leaves close (left first, then right) and thud at 0:43.5, leaving flat stone. 0:43.5–0:44.0: hold. | Present tone, and a slight creak while the leaves move. From 0:32 to 0:41, a remembered bell, low-passed and far (dislocated, it belongs to the memory). The present tone drops 6 dB under it. Thud at 0:43.5. | As in shot 1, plus memory planes from the same BENCH source, printed cold (a different print of the same photograph, not a filter over the stage). Bell: FORAGED (Commons PD/CC) if found, else kit bell plus lowpass. |
| 5 | 0:44.0–0:52.0 | **P03 · retour · silence** | Hard cut to the shot-3 plate and framing, held absolutely still. Slate `P03 · retour · silence déclarée`. | **Digital silence.** | Same as shot 3. |
| 6 | 0:52.0–0:57.0 | Record card | A handmade paper card on the same table and under the same lamp. It shows the route diagram P01 → P02 → P03 as cut strips, the two P01 capture times, the fragment intervals and the INFERRED link, and the credits line "photographies : Carol M. Highsmith, Library of Congress (domaine public)". | **Digital silence** continues (11 s total). | HANDMADE card, plus the same paper-stock scan. |

Voice score (nonchronological; U3 writes it and may refine the wording but not the structure):

- **F1** (shot 1): « Le numéro sept. La porte était lourde ; je l'ai tirée seule. » / *Number seven. The door was heavy; I pulled it alone.* remembered_time `Interval: un matin, avant huit heures ? (heure incertaine)`. Link P01 asserted. Confidence medium.
- **F2** (shot 2): « À l'angle, j'ai suivi la couture du trottoir, à gauche. Ou bien à droite. » / *At the corner I followed the seam in the pavement, left. Or right.* remembered_time `Interval: le même jour, plus tard (ordre incertain)`. Link P02 asserted. Confidence low on direction.
- **F3** (shot 3): « Ce banc, ou un autre. J'ai attendu longtemps ; qui, je ne sais plus. » / *This bench, or another. I waited a long time; for whom, I no longer know.* remembered_time `Unknown (durée : une heure ou un jour)`. Link P03 **inferred**.
- **F4** (shot 4, before opening; a jump in time): « Plus tard, on m'a dit que j'avais neuf ans. » / *Later I was told I was nine.* remembered_time `Interval: âge 8–10 (source : un tiers)`. provenance hearsay. No place link.
- **F5** (shot 4, the open door): « Le banc, c'était l'hiver, à peu près. » / *The bench: it was winter, roughly.* remembered_time `Interval: vers l'hiver (déc.–fév.), année inconnue`. Link P03 **inferred**. Dislocated over P01.

## 6 · Aesthetic target (reference `assets/references/fugue1.webp`, 632×480, INA still)

Measured with PIL:

| region | mean RGB | luminance | sd |
|---|---|---|---|
| frame | (89, 78, 57) | p5 19 · p50 89 · p95 149 | |
| stone (right of door) | (122, 104, 69) | 98 | 12 |
| carved jamb | (127, 108, 72) | | |
| door | (21, 19, 21) | 21 | 2 |
| plinth course | (148, 137, 121) | | |
| balcony band | (47, 39, 26) | | |
| plaque | dark, with light numerals | | |

Dominant quantised colours: (116, 99, 63), (131, 115, 82), (22, 19, 20), (123, 105, 70), (18, 18, 22), (154, 143, 122), (101, 83, 49) and (34, 26, 18). Joints are faint: the row-profile minimum is 84 against a stone median of 98.

- **Medium:** 16 mm colour reversal or print, slightly faded, soft. Here it is rebuilt as real PD photographs cut and lit as paper. The softness comes from plane focus, not a blur filter over the frame.
- **Tonal range:** compressed and low-key. There is no pure white (the p95 target is ≤ 175) and the blacks are lifted brown-black, not 0. The door is a near-featureless dark mass, with only faint panel relief.
- **Palette:** warm ochre stone (R−B ≈ 50), a brown-black door, a pale grey-buff plinth and a dark iron band. The memory plane breaks this palette on purpose (cold blue-grey) to mark another time.
- **Light:** soft, frontal-diffuse daylight with weak modelling. Our lamp keeps shadows short and soft in A and longer in B, but never theatrical. Contrast stays low.
- **Texture:** fine stone grain and faint ashlar joints. The texture comes from the Highsmith stone and the foraged paper fibre, never added noise.
- **Framing / scale:**
  - Frontal and locked off, with no sky and no figure.
  - The door is left of centre (about 13–55 % of the width), its top at about 30 % of the height, and it exits the bottom of the frame.
  - The carved jamb is a narrow band (about 5–6 % of the width).
  - A wall of 2–3 courses of ashlar fills the right.
  - A plinth course runs at about 85–100 % of the height on the right.
  - An iron balcony runs along the top 8 %.
  - The plaque is small (about 4 % of the width), right of the door at lintel height.
  - 4:3.
- **Typography:** the reference has none except the plaque numerals. The film keeps text small and low: cream serif italic for the voice, 13 px muted mono for slates. No title over the opening shot.
- **Pacing:** long locked holds (5–8 s). Motion is rare and weighty: two door events, one glide, one truck. Cuts are hard. The film ends in silence.

Real means of arriving there:

- Choose stone regions of DOOR-C with the least ornament (plain ashlar).
- Sample the reference's tonal targets only to set the paper *print* grade of each source: one global curve per source so that they unify, with no local painting.
- Keep the joints as the real gaps between butted paper blocks (1–2 px, showing the table's shadow), not drawn lines.
- Cut the door leaves from DOOR-S's real riveted door and print them dark.
- Use the foraged paper-stock scan for fibre.

## 7 · Animation technique SCIONs (read in full in `paeleo/scion/swarms.json`)

1. **SCION 40 · Physical Tabletop Capture — Paper Performance Swarm.** The paper must read as real paper on a real table under one lamp. This run has no physical camera, so we apply the tabletop's primitives honestly:
   - per-piece rigid transforms;
   - a timestamped event stream (the performance log of every leaf, strip and truck event);
   - a lamp model with position and size;
   - piece heights on spacers;
   - cut core on the lit edge;
   - fibre taken from a foraged paper scan.

   The "capture" is a render pass per lamp state. We declare it a simulated tabletop capture, not a photograph. Invariants: no wrong-ID swaps (the piece table is immutable between A and B), and capture/render sync (event times measured against frames).
   - Shot use: 1 and 4 (facade, two lamp states), 2 (junction pieces plus the route strip laid on), 3/5 (park pieces), 6 (card).
2. **SCION 44 · Multiplane Parallax — Spatial Collage Swarm.** The memory is a depth behind the door. Each shot has a depth scene graph:
   - P01: facade 0 / leaves 0.05 / void / memory bench 0.6 / memory park 1.0;
   - P02: kerb 0 / corners 0.5 / far street 1.0;
   - P03: litter 0 / bench 0.4 / trunks 0.7 / far 1.0.

   Parallax ratio is 1 − depth, focus blur ∝ distance from the focal plane, with haze between memory planes. Invariants: near moves more than far; occlusions stay coherent (stone in front of leaves, leaves in front of the bench); no foreground stretching. Shot use: 2 (glide), 3 (truck), 4 (truck during opening).
3. **SCION 32 · Forward Kinematics — Hierarchical Body Logic.** The test shot is a hinge. The joint graph is: wall (root) → jamb (fixed) → leaf (revolute about a vertical axis at the jamb edge, θ(t)) → panels, studs and handle (fixed children). The scene is projected with a pinhole at f = 1100 and shaded by the leaf normal against the lamp direction.
   - Weight comes from easing with overshoot and settle, and from the 4-frame lag between leaves. The thud lands on the closing contact frame.
   - Tests (I9): the hinge edge is fixed, the leaf height at the hinge is constant, and the children never slide.
   - Shot use: 1 (small open and slam), 4 (opening and closing).

Supporting methods used inside U2 without being separate SCIONs: GrabCut (SCION 29) for the bench and park cutouts, and occlusion order (SCION 45).

## 8 · Units (3; the editor/assembler and the independent reviewer run separately)

All units:

- read this plan, the prompt, `films/BRIEF-2.md`, `films/kit.py` and the three SCION prompts above (40, 44, 32) in full;
- save media under `films/sources/les-lieux-dune-fugue/<role>/`;
- use User-Agent `oulipo-film-research/1.0`;
- keep total new downloads under about 75 MB for the whole swarm (U1 ≤ 40 MB, U2 ≤ 15 MB, U3 ≤ 20 MB);
- finish within 45 minutes each.

### U1 · route-researcher (route evidence + place reader prep). FORAGE

- **Places:** build the Place register for P01, P02 and P03 (cue, adjacency, capture scope, source ids).
- **Licences:** re-verify the licence of every existing source on its LoC item record (DOOR-C 2010719611, DOOR-S 2014630119, BENCH 2013633886) or its Commons extmetadata. Record each source photo's real date where the record gives it, as source_capture_time.
- **Junction (P02):** forage it within the first 15 minutes and write it to `sources/.../route/junction/`. Look for a frontal street corner or pavement with a kerb and a visible seam or fork in warm stone or paving, no legible signage, and no people in the foreground. LoC Highsmith PD comes first, then Commons PD/CC0/CC BY/BY-SA. The fallback is the Rue du Soleil/Belleville photo, cropped.
- **Ironwork:** forage an optional PD ironwork balcony photo for the top band.
- **Output:** `films/swarm/les-lieux-dune-fugue/route_ledger.json`, holding:
  - places: the Place register;
  - sources: the licence evidence rows;
  - rejected: the rejected items, with reasons;
  - uncertainty: the uncertainty notes;
  - route: the route diagram as an edge list.

  Also write a credits draft at `films/swarm/les-lieux-dune-fugue/credits_draft.json` in the `films/credits` schema, and a `route.png` diagram.
- **Must not:** touch picture or sound code.

### U2 · paper-stage fabricator (location unit / image capture). HANDMADE from FORAGED

- **Paper stock:** forage one PD paper-stock scan (LoC: the blank verso or blank page of a PD item, ≤ 5 MB) into `sources/.../stage/paper/`.
- **Stage module:** build `films/swarm/les-lieux-dune-fugue/paper_stage.py`. It is pure numpy/PIL/cv2, importable, and must not edit kit.py. It provides:
  - a piece library (each piece: source id, crop, scissor-cut outline as a polyline with facets and nicks, height in mm, print grade);
  - the lamp model (states A and B, position, size, warmth);
  - a shadow pass by height;
  - cut-core rim on the lit side;
  - paper fibre from the scan;
  - slight per-piece curl shading;
  - the FK hinge leaves (θ, f = 1100, Lambert shading, children);
  - the multiplane camera (truck, parallax, focus, haze);
  - `render_shot(shot_id, t) -> PIL.Image 960×720` for shots 1–6, following §5 exactly.
- **Framing:** the facade framing must follow §6, which corrects kf-3's faults.
- **Junction:** build P02 from U1's `route/junction/` if present at build time, else from the fallback, and record which.
- **Test shot first:** shot 4, 0:28–0:44, rendered to `films/swarm/les-lieux-dune-fugue/test_shot.mp4` (silent is fine).
- **Then:** stills of every shot.
- **Comparisons:** `compare_P01.jpg` (reference | shot 1 frame | shot 4 open frame, side by side at the same height) and `compare_metrics.json` (the §6 region measurements on film frames).
- **Logs and manifest:** `stage_events.json` (the timestamped performance log), `stage_tests.json` (I1, I5, I8 and I9 measured), and `pieces_manifest.json` (every piece → source id → licence row).
- **Media:** prepared cutouts and masks go in `sources/.../stage/`.

### U3 · narration and sound writer. HANDMADE text + FORAGED / synthesized sound

- **Voice score:** write `films/swarm/les-lieux-dune-fugue/voice_score.json`. Fragments F1–F5 are MemoryFragment records with these fields: speaker, text_fr, gloss_en, remembered_time (typed interval/unknown), place_link + status, confidence, provenance, the screen_time window from §5, dislocated flag, and caption layout (serif italic fr / muted en).
  - Include a validator script `validate_voice.py` that fails on an exact date without evidence, on an unflagged inferred link, or on a caption outside its shot.
- **Sound:**
  - Forage sound (Commons PD/CC0/CC BY/BY-SA audio: street or courtyard tone, park wind/birds, heavy wooden door close, distant bell). The MIA cache clips may be tried for street tone without music or speech.
  - Decode with ffmpeg to 44.1 kHz WAV stems in `sources/.../sound/`. Where nothing licensable is found, specify the kit.Mix synthesis instead (room, wind, thud, bell + lowpass) and say so.
- **Output:** `sound_cues.json`, listing every cue with time, gain, pan, source/licence or "synthesized (kit)". Also declare the silence windows (0:44.0–0:57.0, samples = 0).
- **Must not:** touch picture.

### Editor (run separately)

- **Assembly:** build `films/les-lieux-dune-fugue.py` with `Film("les-lieux-dune-fugue", 57, size=(960,720))` and `ink._grain=False`. Frames come from `paper_stage.render_shot`, captions from `voice_score.json`, and sound from `sound_cues.json` via `mix.add`, with the silence enforced (zero samples).
- **Files to write:** `films/credits/les-lieux-dune-fugue.json` (merging `credits_draft.json`) and `films/notes/les-lieux-dune-fugue.txt` (60–110 words, saying what is foraged and what is handmade).
- **Render:** `assets/films/les-lieux-dune-fugue.mp4` (≤ 6 MB).
- **Checks:** re-run U2's and U3's tests on the assembled film, and save the side-by-side comparisons from the final render.

## 9 · Acceptance bar (falsifiable; a fresh critic checks these on the rendered film and the ledger)

1. **Proof structure.** The film runs 45–60 s and shows exactly three places: P01 door, P02 junction and P03 bench.
   - P01 appears twice from the same position. A frame from 0:02 and one from 0:29, differenced, show identical stone joints and piece positions (edge maps within 1 px), and differ only in light, with cast shadows on the opposite side.
   - P03 appears twice with identical framing.
2. **Defining beat.** Between 0:31 and 0:41 the two dark leaves visibly rotate on fixed hinges, and the leaves stay attached at the jamb in every frame.
   - The leaves foreshorten and darken as they open, with at least 6 distinct leaf drawings, the right leaf lagging the left.
   - A bench is revealed on a deeper plane. It shifts less than the facade during the truck and is lit cold, unlike the warm stone.
   - The door then closes to flat stone on a thud.
3. **Silent return.**
   - The cut after the door closes goes to P03 in the same framing as 0:19–0:28.
   - Audio from 0:44.0 to the end is digital silence (all samples 0, ≥ 6 s, measured).
   - A silence slate is visible.
4. **Aesthetic side-by-side, framing (perceptually judged).**
   - Set `compare_P01.jpg`, made from the final render, beside `fugue1.webp`.
   - Both shots must be frontal and locked off, with no sky and no figure.
   - The dark door must be left of centre, its top at about 25–35 % of the height, running out of the bottom.
   - The jambs must be narrow, the ashlar fine-jointed, and the plaque small and dark.
   - A critic should be able to call it "the same kind of shot". This fails if the door is centred in a wide shot or the joints read as dark brick mortar.
5. **Aesthetic side-by-side, tone (measured).** On the 0:03 frame:
   - the stone region mean is within ±18 per channel of (122, 104, 69), with R−B ≥ 35;
   - the door region mean luminance is ≤ 35;
   - the frame luminance p95 is ≤ 175 and p5 is ≥ 8;
   - the joint darkness is ≤ 30 grey-levels below the adjacent stone.
6. **Paper reads as real paper, not a filter.**
   - At 100 % crop every piece shows an irregular scissor edge (facets and nicks, which differ between pieces) and a lighter cut core on the lamp side.
   - Cast shadows have offsets proportional to piece height and point away from the lamp, and they swap direction between capture A and capture B.
   - No kit grain or vignette is applied (code check: `_grain=False`).
   - Every texture traces to a foraged image in `pieces_manifest.json`.
7. **Memory status is legible and honest.**
   - The voice captions (serif italic) are typographically distinct from the present-tense slates (mono).
   - F5 on screen carries an interval ("à peu près / vers l'hiver") and "INFÉRÉ".
   - `voice_score.json` passes `validate_voice.py`. It has no exact remembered date, and every inferred link is flagged.
   - Every foraged item is in `films/credits/les-lieux-dune-fugue.json` with a PD/CC0/CC BY/CC BY-SA licence verified on its record.
8. **Orientation question (perceptually judged).** After one viewing at normal speed, a critic can answer three questions:
   - which location returned: the door, from the same spot at another time, and the bench at the end;
   - that the bench seen through the door is a memory and not the present;
   - that the voice belongs elsewhere in time than the image.

Pending or unverifiable in this run: no human viewing tests occur. The spatial walkthrough of §8 is not attempted. A real Paris porte cochère photographed twice from one position has not been found (the build uses the staged repeat instead).

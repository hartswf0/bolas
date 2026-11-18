# Le Chant du styrène: swarm plan (round 3, build)

Director's plan. Base revision: `proposals/` round 2 (proposals.md, board.jpg, kf-1/2/3.png). The user chose to build all three round-2 directions as one reverse tour: **1 L'anneau revient → 2 La coulée rendue → 3 Arbres harmoniques**. Direction 2 is the test shot and the defining beat. It needs refraction and less symmetry so it does not read as neon. Earlier `films/le-chant-du-styrene.py` (the brass-key version) is superseded. Only its idea of a wordless syllable-pulse "chant" for the audible meter is carried forward. The plan is otherwise rebuilt.

**Departure from the proposal, declared.** Proposals.md budgeted about 60 s with an 8 s key prologue. The Hard proof (section 6) requires a **25 to 40 s** reverse tour, so this plan runs **38.0 s** and drops the optional station or key prologue (section 10 is optional). The user-supplied object is the moulded ring part from direction 1, not the key. The key sources (A_large_key.jpg, Four_Skeleton_Keys...) are not used.

---

## 1 · Creative thesis

Hold four small red and amber rings on black until they read as familiar, finished things. Then walk backward through what they depend on, and let each step be visibly *the shape of the one before it*:

- the ring returns to the arm of the runner it was cut from;
- the runner-and-rings is the exact hollow of a steel mould, and the melt drains out of that hollow;
- the drained melt was a forest of plastic trees, and the trees were grain.

The dependency becomes a discovery because the shape survives each step: ring = cavity, runner = channel, granule = piece of the tree. One measured alexandrine scores each step. The picture cuts once on a caesura and once against one, so the viewer can feel the difference.

**What would make it bland:** a slideshow of injection-moulding photographs with captions, glowing outlines that read as neon signage, or symmetric diagrams that explain but never transform.

## 2 · Defining beat and comparison baseline

**Defining beat (test shot, Sh3b, 20.80 to 27.60 s):** *La coulée rendue.* The runner-with-rings of the previous shot is seen lying in the open steel mould half. On the syllable *-ti-* of "retire", the picture cuts one syllable before the caesura to a closer, tilted view. There the red melt drains backward out of the four ring cavities and up the asymmetric runner into the sprue mouth. It leaves four lit, empty, ring-shaped hollows in the steel. On "un creux", the hollow is plainly the ring.

**What the viewer should be able to point to:** an empty cavity in the mould at about 26 s whose outline is the ring they saw on the runner arm at about 16 s, in the same position on the same arm. They should also see the melt leave the far cavity first and the sprue last.

**Comparison baseline:** proposals/kf-2.png, the round-2 keyframe. It has flat neon-like glowing tubes, a mirror-symmetric H runner, uniform rim glow, and a mould that is only a dim backdrop. The build passes the baseline when, side by side at the same time code, it shows the following:

- (a) the steel texture visibly displaced and refracted through the melt;
- (b) a runner whose left and right halves are not mirror images (the real runner's four-arm cross, measured from the foraged photograph, not an H);
- (c) wall-thickness shading in which thick sections are deep red and thin fronts are amber, with no constant-width glow outline;
- (d) melt light spilling onto the steel.

The secondary baselines are kf-1.png for Sh2 and kf-3.png for Sh4. Sh4 must lose kf-3's "worms" and its even neon rods.

## 3 · Lineage Genome (compact)

| field | value |
|---|---|
| source | *Le Chant du styrène*, Alain Resnais (dir.), Raymond Queneau (text), 1958, about 13 min, colour, widescreen. It was a sponsored industrial documentary. The Pechiney commission is commonly reported but is **unverified here**. The exact colour process and anamorphic system are **unknown here**. |
| target | a 38 s animated reverse tour at 960×540, 24 fps, letterboxed 2.35:1. Captions carry the voice (no TTS). Handmade sound plus at most one foraged sound. |
| preserved relation | finished object → its process prerequisites, traversed backward. Each step is scored by one alexandrine, and the verse cadence governs the cut. |
| optics change | 35 mm live photography with tracking shots becomes cutout puppetry of a foraged photograph, a procedural melt with refraction composited over a foraged CC0 mould photograph, and harmonic handmade trees. Camera moves become multiplane drifts and tilts. |
| formalism change | the process graph is explicit and checked (ProcessStep, ReverseTour, VerseLine with stable step IDs). The two cuts are coded against scansion. Cavity geometry is constrained to equal part geometry. |
| concept change | the source moves through the factory. This version moves through *shape identity*: each prior step is shown as the negative or ancestor form of the next. |
| sound change | Pierre Barbaud's score and Pierre Dux's spoken alexandrines become a performed, wordless meter. That is twelve struck-plastic syllable pulses per line with an audible caesura gap, timbred per step: hollow ring clicks, viscous low tones, granular rain. Captions give the words. |

**Formation epochs (weight 0 to 100, reason):**

- 1950s sponsored industrial documentary (process as spectacle): 90. It is the product-to-raw-stock structure itself.
- Classical French alexandrine and Queneau's constrained verse (pre-Oulipo, Oulipo founded 1960): 85. The 6+6 meter is the cue grid.
- Resnais's montage of the tracking shot and cut on rhythm: 60. It governs where cuts fall against voice.
- Visual music and harmonic motion (Whitney, 1960s and 1970s): 40. It shapes the final tree-to-grain sequence.
- Cutout and stop-motion animation (Reiniger, Gilliam): 35. The rings are puppets cut from a real photograph.
- Computational fluid and fill simulation (mould-flow, 1970s onward): 45. It drives the backward drain.
- Open-licence archive culture (Commons): 30. It is the foraging constraint.

Uncertain claims recorded as such: the sponsor, the film process, and whether the reference still's runners are polystyrene model-kit sprues are all *unverified*.

## 4 · Olog and theory of the central operation

**Types (boxes)**

- `ProcessStep`: has `process_id`, `inputs`, `outputs`, `material_evidence` (a foraged item ID or a handmade object ID), and `source_anchor` (the evidence URL).
- `ReverseTour`: an ordered list of `ProcessStep` IDs from output toward prerequisites.
- `VerseLine`: has `text`, `scansion` (12 syllables with elisions marked), `caesura_after=6`, `syllable_onsets[12]`, `cue` (`on_caesura` / `against_caesura` / `free`), and `step_id`.
- `Shot`: has `shot_id`, `step_id`, `t_in`, `t_out`, `playback` (`forward` / `backward`), `elements[]` (each FORAGED or HANDMADE with an ID).

**Process graph for injection-moulded polystyrene parts** (the process researcher verifies each edge from open evidence):

```
P1 raw_stock (PS granules/pellets) --plasticize (screw/barrel heat)--> P2 melt
P2 melt + M mould (cavities+runner+sprue) --inject, cool--> P3 shot (runner tree with parts attached)
P3 shot --degate (break/cut gates)--> P4 finished parts (+ runner scrap, regrind)
```

Arrows (aspects): `is plasticized into`, `is injected into`, `solidifies as`, `is degated into`. Reverse arrows used by the tour: `was cut from`, `is the filled hollow of`, `was melted from`.

**ReverseTour used:** `[P4 finish, P3 shot, M+P2 mould/melt, P1 raw_stock]`. The four staged steps are finished form, mould (with the shot in it), intermediate material (the melt), and raw stock. P3 and the mould are joined at the Sh2b/Sh3a cut by a shape match.

**Central operation `reverse_step(a: ProcessStep, b: ProcessStep) -> Shot pair`**

- **Typed preconditions:**
  1. `G` has a *direct* verified edge `b → a`, with `edge.evidence` non-empty and `licence ∈ {PD, CC0, CC BY, CC BY-SA}`.
  2. The shape of `a` maps to a sub-shape of `b` under a declared transform. That is ring ⊂ shot, shot = cavity ∪ channel, and granule ⊂ melt volume.
  3. `VerseLine(step_id=a or b)` exists and passes 6+6 scansion.
  4. `Shot.playback` is declared independently of the edge direction.
- **Observable consequences:**
  1. The viewer sees the step-`b` object occupy the outline of the step-`a` object, so the shape match is visible on screen.
  2. The cut or transformation lands on its cue (caesura or anti-caesura) within ±1 frame.
  3. In the ledger, each shot's `step_id` sequence is a path in reversed `G`.
- **Counterexample (the fixture of section 7):** with `G = raw_stock → casting → finish`, `[finish, casting, raw_stock]` passes. `[finish, raw_stock, casting]` fails because `finish ← raw_stock` is not a direct edge. In this film, cutting from the rings (P4) straight to pellets (P1), then to the mould, is rejected even though each image is "about plastic". A second counterexample comes from substitution. A runner photographed with a *different* ring layout from the cavity fails precondition 2 (cavity IoU < 0.85) and is quarantined even if the edge is valid.
- **Where replay and alternate views are equivalent:** Sh3b played backward (the melt drains) and played forward (the mould fills) denote the same edge `P2+M → P3`. They are structurally equivalent, and the ledger records `playback: backward`. Likewise Sh2 rings flying *onto* the runner and being broken off are the same degating edge.
- **Where they diverge:** perceptually, the backward drain reads as *undoing toward a cause* and reveals the hollow last. The forward fill would hide the hollow under the melt and end on the full part, which contradicts the beat. Reordering the tour diverges structurally and fails, as the counterexample shows.

**Unverified alternative hypotheses (kept separate):**

- The reference still's trees may be compression-moulded or a staged arrangement. They are not used as process evidence.
- Regrind returning runner scrap to P1 is a real loop. It is not part of the tour's path and is not shown as an edge.

**Interactive work:** not applicable (screen work).

**TTL:** 2 (default). No child inquiry planned.

## 5 · Invariants (hard, quarantine on break)

1. Shots follow reversed direct edges only, and the ledger `step_id` path is validated against `process_graph.json` by code, with fixture tests passing and failing as in section 7.
2. Process order and playback direction are separate fields on every shot.
3. Four original French alexandrines, 12 syllables each. The 6+6 break is marked `|` in the caption. Elision is marked in the scansion. No epic caesura: a feminine *-e* at syllable 6 must elide before a vowel.
4. Cut C1 falls at the caesura midpoint of L2, ±1 frame. Cut C2 falls on the onset of syllable 5 of L3, ±1 frame, and at least 0.6 s before L3's caesura. These are the only two verse-coded cuts. Every other cut falls in a line gap.
5. The cavity geometry in Sh3 is generated from the *same* measured ring and arm geometry as the Sh2 cutouts (one `geometry.json`). The cavity silhouette's IoU with the ring cutout silhouette is ≥ 0.85 after the declared transform.
6. Every visible or audible element is FORAGED (with a credits entry and an allowed licence) or HANDMADE (with a named object or script). Colour substitution on the teal runner is declared on screen in the credits and in notes. There are no filters faking a film look. Grain is allowed only as a unifying measure of the same strength over all shots, and is never the source of a "look".
7. Step IDs are stable. A corrected edge invalidates the shots and lines that cite it, and the editor must re-validate.

## 6 · Verse (draft, owned and verified by the process-verse unit)

Meter: classical alexandrine. The syllable pulse is 0.30 s, with a 0.45 s caesura gap after syllable 6. The onset of syllable *k* is `on + (k−1)·0.30 + (k>6)·0.45`. The caesura midpoint is `on + 2.025`.

| line | step | text | scansion | onset `on` | cue |
|---|---|---|---|---|---|
| L1 | P4 | Voici les quatre anneaux \| que la main a gardés. | Voi-ci-les-qua-tr'an-neaux \| que-la-main-a-gar-dés | 2.40 | free (no cut) |
| L2 | P3 | Chaque anneau s'en revient \| au bras qui l'a coulé. | Cha-qu'an-neau-s'en-re-vient \| au-bras-qui-l'a-cou-lé | 11.00 | **C1 on caesura, 13.025** |
| L3 | M+P2 | Le rouge se retire, \| et la forme est un creux. | Le-rou-ge-se-re-ti(re) \| et-la-for-m'est-un-creux | 19.60 | **C2 against caesura: syllable 5 "-ti-" at 20.80, caesura at 21.625** |
| L4 | P1 | L'objet était un arbre, \| et l'arbre était du grain. | L'ob-jet-é-tait-un-ar(bre) \| et-l'ar-br'é-tait-du-grain | 29.40 | free; the line ends at about 33.45, and the cut to the heap at 35.0 is in silence |

The verse writer may change wording within each line's cue contract, keeping the step, syllable count, caesura position, and where the cue syllable falls. Each line gets an English gloss for the notes, not for the screen.

## 7 · Timed shot list (38.0 s at 24 fps; letterbox 2.35, picture band 960×408 at y = 66 to 474; captions in the lower bar)

| shot | t in to out | step / playback | on screen | heard | elements |
|---|---|---|---|---|---|
| Sh1 | 0.00 to 8.60 | P4 finish / static hold | Black. Four loose rings, cut out of the real photograph, lie scattered on black, lit-through amber and red, held long enough to read. A slow 0.3× multiplane drift of two defocused blue practical lights behind (a disc and a horizontal bar, placed differently from the reference). L1 caption from 2.40 to 6.30. | Low room tone. One ring set down at 0.6 s (a plastic click). L1 as 12 hollow plastic pulses with the caesura gap. | Rings: FORAGED (*Spritzguss teile.jpg*, Gmhofmann, CC BY-SA 4.0, Commons), GrabCut cutouts. Blue lights: HANDMADE (gaussian practicals on their own plane). |
| Sh2a | 8.60 to 13.02 | P3 ← P4, degating / backward | Wide. The bare runner (the four-arm cross, cutout) is in place. The rings rise and fly on eased arcs to the arm tips with staggered starts (overlapping action), 12 fps on twos, rotation ≤ 10°. Ring 1 reaches its gate exactly at 13.02. Rings pass in front of the runner (occlusion). | L2 pulses from 11.00. Air whooshes on each ring launch. A click of ring 1 home *on the caesura*. | Runner and rings: FORAGED cutouts. Motion: HANDMADE puppetry. |
| **C1 13.02** | | | **Cut on the caesura of L2.** | | |
| Sh2b | 13.02 to 17.60 | P3 / backward then hold | Close on the right arm pair. Rings 2 to 4 snap home, and each settles ±4° under a spring and damper. Hold 15.8 to 17.6 on the complete shot (runner + 4 rings), framed to match the mould layout of the next shot. | Second hemistich of L2. Three clicks with a small rattle. Silence gap 15.9 to 17.6 except room tone. | FORAGED cutouts + HANDMADE settle. |
| Sh3a | 17.60 to 20.80 | P3 ↔ mould (shape match) / static, slow tilt | Shape-match dissolve (8 frames) from the cutout shot onto the same outline as *melt-filled cavities in the open steel mould half*. The steel is the CC0 mould photograph, cooled, dark, defocused, seen in perspective. The melt is full: deep red, refracting the steel beneath, amber at the thin edges, spilling light. | L3 from 19.60: low viscous pulses. A faint hydraulic or metallic hum enters. | Steel: FORAGED (*Injection mold - (11).jpg*, Bricetofly, CC0, Commons). Melt: HANDMADE simulation. Layout: HANDMADE from `geometry.json`. |
| **C2 20.80** | | | **Cut against the caesura (on the syllable "-ti-", 0.825 s before the break).** | | |
| Sh3b TEST SHOT | 20.80 to 27.60 | M+P2 ← P3, the fill / **backward** | Closer, tilted 3/4 view, shallow focus pulling across the mould face. The fill-time field runs backward: the far cavity empties first, the meniscus boils viscously on twos, and the melt retracts through the gates and up the runner into the sprue mouth (last at about 26.2 s). Four empty, ring-shaped, wet-lit hollows remain. Hold on the hollows 26.2 to 27.6. | "et la forme est un creux" (pulses). A slow suck or drain tone falling in pitch. At 26.80 to 27.60, a **sound-only transition**: granular pellet rain begins over the still-held empty mould, predicting the next material. | FORAGED steel + HANDMADE melt (refraction, thickness colour, asymmetric four-arm runner). |
| Sh4 | 27.60 to 35.00 | P2 ← P1, plasticizing / backward | Black. A forest of 5 to 6 handmade translucent runner trees (the same four-arm vocabulary, varied wall thickness, partly opaque), rising from below the frame edge as in the reference's framing. A back plane at 0.5×. The branch levels swing harmonically (level *k* at *k·ω_i*) and fall into alignment at 33.6 s. From 31.0, one continuous metamorphosis per tree: whole → beading → cut at pitch → pellet cloud on harmonic orbits with spacing jitter (no worms) → falling. | L4 from 29.40, granular rain thickening. On alignment at 33.6, a struck chord. | HANDMADE trees, pellets and blue lights. |
| Sh5 coda | 35.00 to 38.00 | P1 raw stock / hold | Hard cut in a line gap to a **real heap of plastic granules**, cut out of a foraged photograph onto black and lit warm. The last handmade pellets fall onto it, and the motion stops by 36.5. | The last few grains land, then silence to 38.0. | Heap: FORAGED (pellet/nurdle photograph from Commons, licence re-verified; candidates `r2/pellets.jpg`, `r2/nurdles.jpg`, `kf/pellet_azul.jpg`). Falling pellets: HANDMADE. |

Credits (on the film page, from `films/credits/le-chant-du-styrene.json`) include the colour-substitution declaration.

## 8 · AESTHETIC TARGET (from `assets/references/styreneA.webp`, 650×480; content band rows 144 to 375, so the picture is a wide band inside heavy black)

- **Medium:** 1958 35 mm colour photography of real translucent plastic, shot on black with practical coloured lights out of focus. The material reads as real, lit-through polymer, not graphics.
- **Tonal range (measured with PIL):** 77% of pixels have luminance < 20. The luminance median is 0.7, the 75th percentile is 11, the 95th is 118, and the 99th is 166. There are **no whites**. The brightest pixels are amber cores at about (247, 188, 95). The blacks are true black (#000000), and the image has very low key.
- **Palette (sampled hue clusters, pixels with luminance > 25):**
  - deep red, 34% of lit pixels: mean #711D1D, 90th percentile #A2514E;
  - orange, 18%: mean #AA6725, 90th percentile #E8A567;
  - amber or yellow, 18%: mean #DB9924, 90th percentile #F7BC5F;
  - blue practicals, 26%: mean #062551, 90th percentile #172F69.

  Median saturation is 0.91, so colour is fully saturated but dark. The blue is dim and never competes with the warm plastic.
- **Light:** backlight or underlight *through* the plastic. Thin sections are brighter and more yellow, and thick sections are deeper red. There are small specular catches on disc rims. The background light is two out-of-focus blue shapes (a soft disc and a horizontal bar).
- **Texture:** fine film grain and mild softness and halation around amber. The plastic surfaces carry small irregularities, such as gate stubs and the uneven moulded rims of discs.
- **Framing and scale:** extreme close-up. The objects fill the band's height and are cropped by its bottom edge (the trees grow up out of the frame). The view is frontal and planar, with 5 to 6 vertical trees across the width, overlapping in 2 to 3 depth planes, and the discs are about 1/12 of the band width.
- **Typography:** none in the image. Our captions are a small cream serif (#E8E2D2) in the lower letterbox bar, with a thin vertical rule at the caesura, and never over the picture.
- **Pacing:** Resnais holds and glides, and the cuts fall with the verse. In Sh1, Sh2b and Sh3b we prefer long holds to busy cutting.

**How we arrive at it with real material and real technique (not filters):**

- The rings and runner are a real photograph of moulded plastic, cut out with GrabCut and placed on true black. Their real photographic shading (the V channel) is kept. The hue is remapped through a *declared* thickness-to-colour gel ramp (red where thick, amber where thin) because the only open runner photograph is teal. The process-verse unit's forager first spends at most 10 min on Commons and LoC looking for a genuine red or amber translucent runner. If one is found, it replaces the substitution.
- The melt colour is computed from simulated thickness (Beer–Lambert absorption: red is absorbed least, so thick parts are red, thin parts amber). Refraction offsets the foraged steel beneath by the melt's surface gradient. This is physical light transport, not a colour filter.
- The blue practicals are real gaussian light planes in their own multiplane layer.
- The grade only unifies: black point, a shared warm-highlight roll-off, and one grain strength over all shots.
- The framing copies the reference's scale and cropping, not its layout. Nothing from the reference image is copied, traced or pasted.

## 9 · Animation technique SCIONs chosen (prompts read in full)

| id | title | why | applied where |
|---|---|---|---|
| 29 | GrabCut — Cutout Extraction Swarm | It turns the one real foraged runner photograph into usable RGBA puppet layers (runner, four loose rings, the second runner with rings on) and the real pellet heap into a cutout. It keeps the film's objects photographic, and its invariants (no background islands, gate stubs retained, halos isolated, failure masks exported) are testable. | Sh1, Sh2a/b (runner and ring pieces, contour masks, original-coordinate transform → `geometry.json`), Sh5 (heap). |
| 8 | Ivan Sutherland — Constraint Sketchpad Swarm | The proof's process edge *cavity = part* is a constraint relation. One constraint graph (ring centre, radius, arm, gate point; `attached-to`, `aligned-with`) drives the ring puppets' rest poses on the arms, the gate contact in Sh2, and the cavity and channel layout in Sh3. Moving a measured point changes all of them coherently. The residuals are numerically checked (IoU ≥ 0.85, gate contact ≤ 2 px). | Sh2a/b (each ring's arc ends on its gate under a contact constraint), Sh3a/b (the cavity and channel field is generated from the same graph, and the fill-time field T(x) is the path length along that graph). |
| 6 | John Whitney — Harmonic Motion Orchestra | Its final edge, P2 ← P1, needs a transformation from tree to grain that carries rhythm. Oscillator banks (branch level *k* at *k·ω_i*), a measured alignment event at 33.6 s, and a progression from sparse to dense then release map onto the tree → bead → pellet cloud → heap, with a phase visualizer and an A/B of locked ratios against detuned drift. | Sh4 (trees and pellet orbits), Sh5 (release into stillness). |

Supporting methods are taken from other prompts without separate ownership:

- #41 Secondary dynamics: the ring settle.
- #44 Multiplane: the blue light planes and the back tree plane.
- #45 Occlusion: rings in front of the runner.
- #7 Foldès metamorphosis: the continuous tree → granule substitution, drawn per frame.

At least three sequences are genuinely frame-by-frame: the ring puppetry (Sh2), the boiling meniscus drain (Sh3b), and the tree → granule metamorphosis (Sh4).

## 10 · Swarm units (the editor/assembler and the independent reviewer run separately)

All units work from this plan's revision (`plan.md` r3) and the shared timing above. They write their ledgers to `films/swarm/le-chant-du-styrene/` and their media to `films/sources/le-chant-du-styrene/<role>/`. Each finishes within about 45 min, and new downloads stay under about 75 MB in total. Shot renders are delivered as PNG sequences or lossless mp4 at 960×408 (picture band only, no captions). The editor adds the bars, captions and mix through `kit.py`.

**U1 · process-verse (process researcher + verse writer + voice/sound performer)**

- **Builds:**
  - `process_graph.json`: ProcessSteps P1 to P4 + M, with edges, open evidence URLs (Commons file pages and category descriptions of injection moulding, sprues and pellets; LoC printed matter if useful), licence, and a confidence for each edge.
  - A small validator `validate_tour.py` that passes `[finish, casting, raw_stock]` and fails `[finish, raw_stock, casting]` on the fixture, and validates this film's shot `step_id` path.
  - The four lines with scansion, elision and the syllable-onset table, and a check that C1 and C2 fall where invariant 4 says.
  - Sound stems (WAV, 44.1 kHz): the performed meter (12 struck-plastic pulses per line, with step-specific timbre and the caesura gap), the ring clicks, the drain tone, the granular rain sound-only transition (26.80 to 27.60), and the room tone.
  - Optionally one foraged industrial machine sound from the Moving Image Archive cache. The cache has no plastics footage: queries for plastic, mould and injection returned only general factory shots, so it is used for sound only, if at all, and credited.
  - A 10-minute Commons and LoC search for a genuine red or amber translucent runner, reported to U2.
- **Output:** `/home/user/bolas/paeleo/scion/oulipo/films/swarm/le-chant-du-styrene/process_verse.json`. It holds the graph, the validator result, the verse and cue sheet, and the stem paths. The media go to `films/sources/le-chant-du-styrene/process-verse/`.

**U2 · cutout puppetry (camera unit A: object and tool)**

- **Builds:**
  - GrabCut cutouts from `r2/spritzguss.jpg` (licence re-verified on Commons extmetadata): the bare runner, the four loose rings, and the runner with rings on. These come with contour masks and failure masks.
  - **`geometry.json` first, within about 10 min:** ring centres, outer and inner radii, arm polylines and gate points in source pixels and in film coordinates. U3 needs it.
  - The declared thickness-to-colour gel ramp, unless U1 finds a real red or amber runner.
  - Frame-by-frame renders of Sh1, Sh2a and Sh2b, with ring 1 home at exactly 13.02 s (frame 312.5 → frame 312/313, noted) and a spring settle.
  - The foraged heap cutout for Sh5, with its licence verified.
- **Output:** `/home/user/bolas/paeleo/scion/oulipo/films/swarm/le-chant-du-styrene/cutouts.json`. It holds the manifest of RGBA pieces, masks, the transforms, geometry, credits entries and shot render paths. The media go to `films/sources/le-chant-du-styrene/cutout/`.

**U3 · melt simulation (camera unit B: the TEST SHOT, defining beat)**

- **Builds:**
  - The cavity and channel field generated from `geometry.json`. This is the same four-arm, asymmetric layout, not a symmetric H. If `geometry.json` is late, U3 measures it from the same photograph by the same declared procedure and reconciles.
  - The fill-time field T(x): path length from the sprue, slower inside cavities, with a lag at the walls. The melt shows where T + η(x) < τ, and τ runs backward. η is boil noise reseeded on twos.
  - Beer–Lambert thickness colour and refraction of the foraged CC0 steel (`kf/mold11.jpg`, licence re-verified) through the melt's surface normal. Also melt light spill onto the steel, a specular highlight on the meniscus, a 3/4 perspective and a focus pull.
  - Renders of Sh3a (including the 8-frame shape-match dissolve target) and Sh3b. A side-by-side of the Sh3b frame at 24.0 s with `proposals/kf-2.png` and the reference. The IoU of the cavity silhouettes against U2's ring masks.
- **Output:** `/home/user/bolas/paeleo/scion/oulipo/films/swarm/le-chant-du-styrene/melt_shot.json`. It holds the parameters, seed, IoU results, symmetry measure, render paths and comparison sheet path. The media go to `films/sources/le-chant-du-styrene/melt/`.

**U4 · harmonic trees to granule (camera unit C)**

- **Builds:**
  - Handmade translucent runner trees, using the four-arm vocabulary from `geometry.json` with varied wall thickness and some opacity: 5 to 6 front trees and a back plane at 0.5×.
  - A Whitney oscillator bank, with a phase visualizer PNG and an A/B of locked ratios against detuned drift, choosing locked with alignment at 33.6 s.
  - The Foldès-style per-frame metamorphosis: tree → beads → pellets cut at a fixed pitch (each pellet is literally a piece of the tree) → orbits with spacing jitter (no worms) → fall.
  - Renders of Sh4 and of the falling handmade pellets layer for Sh5 (on a transparent background, to land on U2's real heap cutout).
- **Output:** `/home/user/bolas/paeleo/scion/oulipo/films/swarm/le-chant-du-styrene/harmonic_trees.json`. It holds the formulas, frequencies, the alignment time, render paths and the phase visualizer. The media go to `films/sources/le-chant-du-styrene/harmonic/`.

**Editor (separate):** assembles everything with `kit.py` into `films/le-chant-du-styrene.py`. It adds the bars, captions with `|`, and the mix of U1's stems. It writes the shot ledger (shot_id, step_id, playback, t_in/t_out, elements with FORAGED/HANDMADE and IDs), credits JSON and notes. It runs U1's validator over the ledger, and verifies the C1 and C2 frames.

**Reviewer (separate):** watches at normal speed, then checks the bar below.

## 11 · Acceptance bar (falsifiable; the critic checks the film and its ledger)

1. **Proof structure (structurally verified):** the film is 25 to 40 s long (target 38.0). The ledger's `step_id` path is `[P4, P3, M+P2, P1]`, and `validate_tour.py` passes it, passes the fixture `[finish, casting, raw_stock]` and rejects `[finish, raw_stock, casting]`. Every shot has a `playback` field separate from its process order. A viewer who has not seen a diagram can say "rings ← runner ← mould and melt ← pellets" after one viewing (perceptually judged).
2. **Cuts against meter (measured):** scene-cut detection on the mp4 finds a hard cut within ±1 frame of 13.02 s (L2 caesura midpoint, captions show `|` there) and one within ±1 frame of 20.80 s (L3 syllable 5). The latter is ≥ 0.6 s before L3's caesura. No other cut falls inside a spoken line.
3. **Defining beat (measured and perceptual):** in Sh3b at about 26.5 s, four empty ring-shaped hollows are visible in the steel, and the melt visibly leaves the far cavity first and the sprue last. The ledger reports cavity-versus-ring IoU ≥ 0.85 from the shared `geometry.json`. A critic placing the frame at 16.5 s beside the frame at 26.5 s can point to the same ring and its hollow on the same arm.
4. **Aesthetic A, side by side with `styreneA.webp` (measured and perceptual):** stills at 5.0, 24.0 and 32.0 s are set beside the reference. Inside the picture band, ≥ 65% of pixels have luminance < 20 and the 99th percentile luminance is ≤ 210 (no whites). Lit pixels have median saturation ≥ 0.70, and their hues fall mainly in the red, orange and amber clusters (≥ 60% of lit pixels), with a dim blue practical present in at least 2 of the 3. A critic judges the plastic to read as *lit-through translucent material*, not as neon outlines.
5. **Aesthetic B, side by side (perceptual and measured):** the stills at 16.5 s and 32.0 s beside the reference. The objects fill ≥ 55% of the band height, and in Sh4 the trees are cropped by the bottom edge of the band like the reference's. The frame is a 2.35 letterbox on true black. One grain strength is used across shots, and no shot shows a fake filter look over unsuitable material.
6. **Test shot beats baseline (perceptual and measured):** the Sh3b frame at 24.0 s beside `proposals/kf-2.png`. The runner layout is not mirror-symmetric: the left/right flipped-mask IoU is < 0.8. The steel texture is visibly displaced through the melt (refraction). The melt edge colour varies with thickness rather than as a constant-width glow, and there is light spill on the steel. The critic prefers the build to kf-2 on "reads as poured plastic, not neon".
7. **Genuine animation (perceptual):** the Sh2 rings travel on eased arcs with staggered starts and settle with overshoot. The Sh3b meniscus changes shape every 2 frames. The Sh4 trees change shape continuously into pellets with no "worm" chains. No sequence is only a pan, zoom or fade over a still.
8. **Sound and honesty (measured and structurally verified):** each line is audible as 12 pulses with a gap after the 6th, the pulse onsets agree with the cue sheet ±1 frame, and the granular rain starts ≥ 0.5 s before the Sh4 picture. Every foraged item is in `films/credits/le-chant-du-styrene.json` with PD, CC0, CC BY or CC BY-SA read from Commons extmetadata (or an archive credit in the stated form). The colour substitution of the runner is declared in the credits and notes. No material comes from the 1958 film itself.

## 12 · Repair rules carried from section 8 (for the editor)

- If the viewer can recite the process but cannot see a transformation, keep the verse and strengthen the shape match: the Sh2b → Sh3a dissolve outline, or the Sh4 bead pitch.
- If the cut reads but the rhythm strains, keep the images and compare alternate scansions at the same 0.30 s tempo.
- After two failed repairs of the same failure, state two explanations and run the smallest A/B. Keep the strongest accepted checkpoint.

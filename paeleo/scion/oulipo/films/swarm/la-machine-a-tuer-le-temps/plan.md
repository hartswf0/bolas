# La Machine à tuer le temps: production plan (SCION swarm, director)

Direction: **1 · Le cahier rebattu**, as the user chose (`proposals/kf-1.png`), with direction 3's permutation graph as a 4.5 s red-pencil coda. Nothing here departs from that direction. Paper stop-motion of a handmade spiral notebook holds a frozen pool of eight public-domain Jack Delano prints (Union Station, Chicago, 1943; LoC FSA/OWI). Between cut A and cut B the prints are lifted, re-slotted and re-numbered in red pencil frame by frame, using translation only. Inside each cut the rostrum camera pushes into a print, and the cut plays full-frame from the frozen shot pool.

Render: `films/la-machine-a-tuer-le-temps.py` with `Film(slug, seconds=66, size=(1280,720), fps=24)` from `films/kit.py`, which stays unedited. For every frame that shows a print, set `ink._grain = False`, because kit grain would change the pool's colour frame by frame and would be a style costume. The notebook frames get their texture from the paper model, not from added film grain.

---

## 1 · Creative thesis

The same eight photographs, put in a different order, make the viewer suspect a crime. Cut A reads as a routine night shift at Union Station: the clock, a mail-room woman carrying a parcel, a conductor checking the time, a soldier boarding, a red cap, reservation slips, soldiers leaving, the empty hall. Cut B opens on the red cap's long stare out of frame. The door, the woman turning back with the box, the slips left on the counter and the conductor timing something follow it, and the clock comes late, like an alibi. In B the parcel seems illicit and the red cap seems to be its look-out. The viewer has seen nothing new: the notebook shows the same prints being physically moved and re-numbered, so the change in cause can be attributed only to the edit.

**What would make it bland:** a notebook that only illustrates editing (cards slide about, nothing changes in meaning), cut B projections that are too short for the new inference to land, or hand numbers that look like a font.

## 2 · Defining beat and comparison baseline

**Defining beat (0:36.25 to 0:43.25, start of cut B).** The camera pushes into slot 1, where print 05 (the red cap) now sits under a red "1" over a struck-through "5". The glance holds for 5.0 s at half speed. Then comes a hard cut to 04 (the soldier at the train door), then 02 (the woman with the box, looking back over her shoulder toward where the red cap was looking). The viewer should be able to point to **the 05 to 04 to 02 adjacency**: the stare is now *at* the door and the parcel. In A, the same woman with the same box comes second, after the clock, and reads as work.

**Comparison baseline.** Cut A (0:06.75 to 0:26.75) uses the same eight assets in pool order 01 to 08 with near-equal holds, over the same shared bed. The baseline must read as ordinary. If A already reads as sinister, B has proved nothing. A critic compares A and B first in the shared-bed export (screening 1) and then in the final-mix film (screening 2).

## 3 · Lineage Genome (compact)

| field | value |
|---|---|
| source | Oucipo / Raymond Queneau, *La Machine à tuer le temps* dossier, c. 1974 (Drouot lot 175): a red spiral notebook inventorying 42 photographs (film frames), each pasted on a page with a typed caption on tape and a shot number in pen, plus proposals for variations in order, duration, reversal, speed, synchronisation and soundtrack. We know it only from the auction listing and its photograph. Who made which page, and whether the variations were ever shot, are **uncertain**. |
| target | A 66 s 1280×720 24 fps film with two playable cuts, made as paper stop-motion of a new handmade notebook holding a pool of 8 (not 42) PD photographs, plus a companion shared-bed export. |
| preserved relation | A fixed inventory × an explicit edit recipe gives a film. Changing only the recipe changes the film's meaning. The notebook page is the inventory. |
| optics | Movie frames become still documentary prints. Motion inside a shot comes from a rostrum push (a declared window path inside the print's native bounds, frozen into the asset). The notebook is "shot" from overhead, on twos, with stop-motion micro-jitter. |
| formalism | Pages and numbers become a typed manifest (asset_id, sha256, native bounds, LoC anchor, window path, per-frame md5), an integer-frame EDL and versioned sound stems, with a per-frame render ledger. |
| concept | Only order, duration, speed, direction and sound change. The tested variable is the inferred *motive* (routine vs illicit handoff), not chronology alone. |
| sound | The dossier had no sound. We add separately versioned stems: one shared bed (for screening 1) and two final mixes. Archival recordings are used where licensed, synthesis otherwise. |

**Formation epochs (weight 0–100, reason):**
- Kuleshov-effect montage, 1920s: **70**. Meaning made by adjacency is the theory under test. The original experiment's details are historically **uncertain**.
- Oulipo / Oucipo constraint practice, 1960–74: **95**. This is the direct source: a constraint on a finite inventory with combinatorial variation.
- FSA/OWI documentary photography, 1943: **55**. It is the actual source material. Its "ordinary" captions anchor cut A, and its plainness is what B reinterprets.
- Films made from still photographs (e.g. Marker, *La Jetée*, 1962): **40**. It shows that stills can carry a narrative. This is an analogy, not a documented influence on the dossier.
- Edit decision lists and declarative/programmatic editing (1970s EDL to SCION 27 / Remotion): **75**. Recipes are explicit, replayable and frame-indexed.
- Paper stop-motion and rostrum animation: **65**. This is the film's visible medium: the hand moves paper, and the camera is a rostrum.
- Content-addressed provenance (hashes, ledgers): **50**. It makes the frozen-pool invariant checkable.

## 4 · Olog and theory of the central operation

**Types (◻) and arrows**
- ◻ShotAsset has: `asset_id` ∈ {01..08}, `source_sha256` (LoC file), `native_bounds` (w, h of the source JPEG), `source_anchor` (loc.gov item URL), `print_op` (fixed tone map, below), `window_path` (rostrum windows W0→W1 inside native bounds, 16:9, eased), `N = 120` frames, and `frame_md5[0..119]`.
- ◻Pool has: 8 ShotAssets and `pool_hash` = sha256 of the canonical JSON manifest (sorted asset_ids, source_sha256, print_op, window_path, frame_md5 list).
- ◻PictureEdit (`edit_id`, `base_pool_hash`) is an ordered list of EditEvent: `asset_id`, `in`, `out` (source frames), `out_frames` (int > 0), `direction` ∈ {fwd, rev}, `speed` ∈ {0.5, 1, 2}.
- ◻SoundEdit (`sound_id`, `version`) has tracks (versioned wav stems), cues (`t_frame`, `track`, `sync_dep`: an EditEvent index or "none"), and offsets.
- render: Pool × PictureEdit × SoundEdit → ◻Screening (mp4 plus a per-frame ledger `{frame, segment, asset_id|notebook, src_frame, md5}`).

**Central operation: `reorder(edit) → edit′` against a fixed pool**
- *Typed preconditions:* `edit′.base_pool_hash == Pool.pool_hash`. Every `asset_id` ∈ Pool. `0 ≤ in, out ≤ N−1`. `out_frames ∈ ℕ⁺`. `out_frames == round((|out−in|+1)/speed)`. `direction` and `speed` are in their enums. No event references a frame or image outside the manifest. Any cue with `sync_dep` on a moved event is re-aligned, or its sound edit is forked.
- *Observable consequences:* every projected output frame's md5 is in `∪ frame_md5` for its asset (measured). The multiset of asset_ids in A and B is equal ({01..08} once each). In the notebook, each card's print pixels at rest equal the toned print at that scale, and a moving card differs from its rest state by translation only. The viewer names a different cause in B (perceptual).
- *Counterexample (must fail):* a "B" that gets its sinister reading from something new: a red-tinted grade on 05, a tighter crop of the box that is not in `window_path`, a drawn hand slipping the parcel, or a frame `out = 130`. The inference may change, but membership fails, so the proof fails. A second counterexample for the reading is B′ = A reversed (08→01). It passes membership but reads as rewound chronology, not a new motive, which is the case the §8 repair rule addresses.
- *Equivalent vs divergent views:* the same recipe rendered twice gives identical frame md5 (equivalent). The shared-bed export and the final-mix film have an identical picture stream (framemd5 equal) and divergent audio in the cut segments only. A vs B have the same asset multiset and divergent order, durations, speed and direction, so B's frame multiset includes held (speed 0.5) and reversed frames. Notebook segments are identical across both exports.
- *Interaction:* none. This is screen work, a single linear screening. Invitation, actions and resistance are N/A.
- TTL = 2. No child inquiry is planned. A §8 repair, if needed, runs inside the editor unit as named branches.

## 5 · Invariants

1. **Freeze before branching.** `pool-manifest.json` and `pool_hash` are written by the registrar before any recipe or sound edit is accepted. Every recipe and stem records `base_pool_hash`.
2. **Every visible print pixel resolves.** In cut segments, each output frame equals `asset[id].frame[src]` exactly (md5). In notebook segments, prints appear only as the frozen toned print at a uniform scale with integer- or subpixel translation: no rotation, warp, recolour, crop change or per-frame grain.
3. **Permitted changes only:** timing, order, repeat, omission, reverse, speed, independent audio. Geometry, colour, content and framing of every image are fixed.
4. **No other image.** No generated inserts, no drawn substitute for a photograph. The handmade notebook, tape, ink, red pencil and paper sheet are the only non-pool picture elements, and they never cover the pool with a fake.
5. **Audio-only replacement preserves the picture.** The shared-bed export and the final film share a picture stream (framemd5 equal over all 1608 frames).
6. **Licences.** The 8 LoC prints are "No known restrictions on publication" US government works. Audio is PD / CC0 / CC BY / CC BY-SA, or movingimagearchive.com listings marked as such, each credited.
7. **Hand lettering is a hand.** Every glyph instance has its own stroke jitter and pressure. It is written on over 6 to 10 frames, never pasted whole.

## 6 · The frozen pool (eight originals) — FORAGED

All eight are already in `films/sources/la-machine-a-tuer-le-temps/` (Library of Congress, tile.loc.gov; Jack Delano, 1943, FSA/OWI). The registrar re-verifies each item's "No known restrictions on publication" statement on www.loc.gov (JSON `fo=json`), records `rights_advisory` verbatim, and marks these 8 `used_as` in the credits. The other 10 candidates become `used_as: "not used"` or are removed. **No new image downloads are needed.**

| id | proof role | LoC item / file sha256 (prefix) | rostrum window path (registrar finalises by looking; 16:9 inside native bounds, edge codes "OWI-…" and rebate excluded) |
|---|---|---|---|
| 01 | clock | 2017844012 / 9b4b28be | W0: whole office counter. W1: ×1.25 toward the wall clock left of centre |
| 02 | hand with a parcel | 2017844121 / b7d952b3 | W0: woman with box, co-workers. W1: ×1.25 toward her face and the box |
| 03 | second hand | 2017844115 / 21dfafc4 (portrait) | W0: upper body incl. face and raised hand with watch. W1: ×1.2 toward the watch hand |
| 04 | door | 2017843935 / b80c501f | W0: carriage door and the backs of the soldier and the woman. W1: ×1.2 toward the door opening |
| 05 | glance | 2017843923 / e612b9fe | W0: head and shoulders. W1: ×1.3 slow push to the eyes |
| 06 | dropped receipt | 2017843913 / c77fc78a | W0: counter, clerks' hands. W1: ×1.25 toward the slips on the counter |
| 07 | person exiting | 2017843870 / 4bbe01fe | W0: the file of soldiers. W1: ×1.15 drifting toward the TRACK 2 doorway |
| 08 | empty threshold | 2017843779 / 2f085c49 | W0: waiting room with benches. W1: ×1.05, nearly still, the lone figure |

`print_op` (one fixed tone map, the "print stage", applied once): grey to warm silver-gelatin, black (24,20,18) to paper white (232,226,214). This matches the reference prints' measured range (below). The same op applies to every appearance, in the notebook and in projection.

## 7 · Timed shot list (as built: 67.0 s = 1608 frames @ 24 fps, 1280×720; first drafted as 66.0 s = 1584 f)

Segments are frame-exact. The notebook is animated **on twos** (12 drawings/s) with ±0.6 px stop-motion table jitter per drawing on the notebook layer only. Projections are on ones.

| # | time (s) | frames | on screen | element source | heard (shared-bed export / final film) |
|---|---|---|---|---|---|
| S0 | 0.00–3.00 | 0–71 | **Title.** A closed red spiral notebook on a pale table. The pasted white label reads, hand-lettered in black felt pen in my own single-stroke hand, "LA MACHINE / À TUER / LE TEMPS", and on a lower label "8 photographies · 2 montages · 1 pool". At 2.25 s the cover flips back around the coil (6 drawings, cover only). | HANDMADE: cover board #610e18 grain, labels, lettering | Room tone and a single paper flap on the flip (same in both) |
| S1 | 3.00–6.00 | 72–143 | **Inventory spread, cut A.** Two cream pages, 4 mount cards per page (2×2). Each card carries a toned print, a typed tape caption below it ("01.- L'horloge du bureau de régulation." etc., Courier, yellowed tape band) and its ink number 1–8 in pen. A red page number sits top right. The top tape reads "POOL · Union Station, Chicago, 1943 · J. Delano (LoC) · sha256 a3d3…". A red "A" is at the top left. Held, breathing on twos. | FORAGED prints 01–08 + HANDMADE notebook, cards, tape, ink | Room tone, faint station bed fading in |
| S2 | 6.00–6.75 | 144–161 | Push in (eased, 18 f) on card 1 (01) until its rostrum window W0 fills the frame. Uniform scale and translate of the whole table, with the print re-sampled from source at the target scale. The last frame matches asset 01 frame 0 (PSNR ≥ 35 dB). | camera move | Bed rises |
| S3 | 6.75–26.75 | 162–641 | **CUT A** (480 f), full-frame pool frames per recipe A (§8). No captions. | FORAGED pool assets | Screening 1: shared bed T1. Film: mix A (T3) |
| S4 | 26.75–27.50 | 642–659 | Pull out from asset 08 to the spread (card 8) | camera move | Bed falls to room tone |
| S5 | 27.50–36.50 | 660–875 | **TEST SHOT: the re-shuffle** (216 f as built: one print per page needs four page turns; drafted as 192 f, on twos; see §9). Card 01 is lifted and parked at the bottom gutter, still sliding. Then 05→slot 1, 03→5, 02→3, 04→2, 06→4, and 01→6. Each lift: the shadow grows over 4 f, the card travels 10–14 f along a slightly irregular path, overshoots 2–3 px on a spring and settles, and the shadow shrinks. Red pencil strikes the old ink number (4 f) and writes the new one stroke by stroke (6–8 f). The red "A" is struck and "B" written. Hold 0.8 s on the re-numbered spread. 07 and 08 never move. | HANDMADE animation of FORAGED cards | Paper lift / slide / tap foley and pencil scratches, synced to each event (same in both exports) |
| S6 | 36.50–37.25 | 876–893 | Push in on slot 1 (now 05, the red cap) to asset 05 W0 | camera move | Bed rises |
| S7 | 37.25–60.75 | 894–1457 | **CUT B** (564 f), full-frame per recipe B (§8) | FORAGED pool assets | Screening 1: the same shared bed T1 (same offset as in A). Film: mix B (T4) |
| S8 | 60.75–61.50 | 1458–1475 | Pull out from asset 08 to the spread (slot 8) | camera move | Bed to room tone |
| S9 | 61.50–62.50 | 1476–1499 | A loose sheet of the same notebook paper slides in over the spread (translation only, on twos, with a soft leading shadow), covering the cards. This avoids bending prints on a page turn. | HANDMADE sheet | Paper slide |
| S10 | 62.50–67.00 | 1500–1607 | **Coda, the permutation graph.** Two ink columns, "A" and "B", each listing 01–08 in hand. The red pencil draws 8 lines, each from an asset's A position to its B position, 6 f per line (lines for 07 and 08 are horizontal). Then a typed tape: "même pool · sha256 a3d308bd…2056 · 42 → 8". Last 1.0 s held. | HANDMADE | Pencil scratch per line, then the room tone ends on one clock tick |

## 8 · Edit recipes (owned by the cut-editor unit; these are the starting values)

Each asset has N = 120 frames (5.0 s push W0→W1).

**Cut A (edit_id `A1`, 480 f = 20.0 s): ordinary handoff.**
| pos | asset | in→out | dir | speed | out_frames |
|---|---|---|---|---|---|
| 1 | 01 clock | 0→59 | fwd | 1 | 60 |
| 2 | 02 parcel | 0→71 | fwd | 1 | 72 |
| 3 | 03 second hand | 0→59 | fwd | 1 | 60 |
| 4 | 04 door | 0→59 | fwd | 1 | 60 |
| 5 | 05 glance | 0→47 | fwd | 1 | 48 |
| 6 | 06 receipt | 0→59 | fwd | 1 | 60 |
| 7 | 07 exit | 0→71 | fwd | 1 | 72 |
| 8 | 08 threshold | 0→47 | fwd | 1 | 48 |

**Cut B (edit_id `B1`, 564 f = 23.5 s): the parcel seems illicit.**
| pos | asset | in→out | dir | speed | out_frames | why |
|---|---|---|---|---|---|---|
| 1 | 05 glance | 0→59 | fwd | 0.5 | 120 | long stare opens; look-out |
| 2 | 04 door | 0→47 | fwd | 1 | 48 | what he watches |
| 3 | 02 parcel | 24→95 | fwd | 1 | 72 | her look back now answers his |
| 4 | 06 receipt | 30→101 | fwd | 1 | 72 | the slip left behind, tighter in the push |
| 5 | 03 second hand | 0→59 | fwd | 1 | 60 | someone is timing it |
| 6 | 01 clock | 119→84 | rev | 1 | 36 | the clock arrives late, pulling away (alibi) |
| 7 | 07 exit | 0→59 | fwd | 1 | 60 | the getaway |
| 8 | 08 threshold | 0→95 | fwd | 1 | 96 | the empty hall held long |

The cut A and B projections are each ≥ 1.5 s, and the glance is 5.0 s, so the B inference has time to land. Named fallback branches (§8 of the prompt, held against the same pool hash): `B2-rev-adjacency` (soundtrack fixed, 04↔02 swapped), `B3-glance-hold` (05 held 7 s), and `B4-delayed-cue` (B1 picture, with the door-latch cue delayed 12 f into 04). Keep the one that changes the reading and record the controlling variable.

**Verification fixture (validator):** A_fx = [01,02,04,07], B_fx = [07,04,02,01] pass membership on `pool_hash`. An injected event with asset "X9" or an off-pool frame md5 fails. `out = 130` fails. Swapping only the audio stem leaves the framemd5 identical.

## 9 · Sound (owned by the sound unit)

- **T0 room** (all notebook segments, both exports): table and room tone. FORAGED: a quiet interior or room ambience (movingimagearchive.com clip with source sound, or Commons PD/CC). Fallback: kit `mix.room`.
- **T1 shared bed** (S3 and S7 in the screening-1 export, identical offset from each cut's frame 0): station concourse murmur, distant trains and a steady wall-clock tick at 1 Hz, not cut to the picture. FORAGED from the archive cache: railway/station clips with source sound (`forage.py "station|railroad|train|crowd|clock|tick"`; e.g. the 1966 ticking-clock close-up, a station platform). Choose by listening, and reject music beds.
- **T2 foley** (S0, S5, S9, S10, both exports): paper lift, slide, set-down taps, pencil scratch per stroke, cover flap. FORAGED if openly licensed paper/pencil recordings exist on Commons; otherwise HANDMADE synthesis (filtered noise bursts with stroke-length envelopes via `Mix`). Cued to the animator's event stream.
- **T3 mix A** (final film, S3): bed at normal level, tick steady, mail-room bustle under 02, a door latch on the 04 cut, the murmur warm, a whistle or bell under 07.
- **T4 mix B** (final film, S7): bed ducked −9 dB. The tick slows to a held silence over the 05 stare (declared silence, 2.5 s). A pre-lapped door latch sits 6 f *before* the 05→04 cut. The tick returns hard on 06, and on 01 it is the only sound. Footsteps pre-lap 07, and the hall reverb tail under 08 fades to nothing. Every cue records `sync_dep` to its B1 event index.
- No voices, no TTS. The captions are the typed tapes.

## 10 · Animation technique SCIONs

1. **SCION 40 · Physical Tabletop Capture: Paper Performance Swarm.** The film *is* a hand moving paper on a table. Applied: each mount card and the loose sheet is a rigid piece with a per-frame rigid transform restricted to translation (an invariant stricter than SCION 40's rigid transforms). It is driven by a **timestamped event stream** (`lift`, `travel`, `settle`, `setdown`, `strike`, `write`) that the sound unit also consumes, so capture and sound are synchronised by construction. Its tests, "no wrong-ID swaps" and "contact constraints survive replay", become: the card at slot k after S5 is B[k], and no card overlaps another at rest. Shots S0, S1, S5, S9 and S10.
2. **SCION 27 · Remotion: Declarative Film Compiler.** The two cuts and the re-shuffle are compiled from data. The S5 slot moves are derived from the A→B permutation. S3 and S7 are pure functions of (pool, recipe) on integer frames, and replay is deterministic (fixed seeds, so identical md5 across renders). Its bar, "cuts occur on specified frames; no missing images; audio survives exports", maps directly onto acceptance 1, 2 and 7. Shots S2–S4, S6–S8, the S5 choreography and the S10 graph.
3. **SCION 41 · Secondary Dynamics: Inertia and Restraint.** The cards must have weight: a damped spring on the translation at set-down (2–3 px overshoot, energy fully decayed within 6 drawings), a shadow offset and blur growing with lift height, and the loose sheet's leading-edge shadow. Its invariant is that "momentum response begins after primary motion; all energy decays when sources stop": nothing on the page jiggles at rest except the stop-motion table jitter. S5 and S9.
(SCION 54's provenance-graph method is folded into the registrar/validator's manifest and ledger. It is not counted as a picture technique.)

## 11 · AESTHETIC TARGET (reference `assets/references/oucipo.webp`, catalogue/cinema.json id 1)

The reference is a scanned red spiral notebook: the cover on the left and a spread of pages 15 and 16 on the right. Measured with PIL (median of regions):
- **Medium:** a real paper object photographed flat. B&W silver prints pasted on paper, typewriter text on tape, pen numbers, a red page number. Nothing is drawn over the photographs.
- **Pages:** warm cream, **#ede5d5** (left) / **#f3ebd9** (right), very low texture (σ ≈ 7 per channel). The gutter is barely darker. There is no ruled paper.
- **Cover:** oxblood red **#610e18** (σ ≈ 7), with a white label and black felt-pen capitals in an irregular hand.
- **Prints:** neutral-warm B&W. Blacks p1 ≈ 20–25 (deep shadow region #211a17), highlights p99 ≈ 221–231, midtones ≈ 60–66, and a slight warmth (median R−B ≈ +12). Crisp, with no vignette and no added grain. Landscape prints cover ~75% of the page width, placed in the upper third, with broad empty margins.
- **Tape captions:** a thin pale strip with a yellowed band through the middle (**#dfbe87**, σ ≈ 20). Small typewriter text in a faded brown-grey (≈ #a1824e on the yellow), French, in the form "15.- La jeune fille …".
- **Numbers:** shot numbers in thin dark pen (**#423a2f**), small, centred well below the caption. The page number at the top right is in red (**#b76158** at anti-aliased stroke pixels, i.e. a thin red ink).
- **Light:** flat, even, shadowless scanner or copy-stand light. Our lifted cards cast soft shadows only while lifted, and the rest state is nearly flat (shadow ≤ 3 px).
- **Framing/scale:** a whole spread, frontal and square to the camera, with the spiral coil central and fine (≈ 24 loops). Close framings in S1/S5 show at least one full card with its tape and number. Projections are full-frame prints.
- **Typography:** Courier-style typewriter for tapes, our own single-stroke hand for numbers (ink and red pencil) and felt-pen capitals for the cover.
- **Pacing:** the notebook is still and patient, with deliberate hand moves and nothing hurried. Cuts are hard cuts with no dissolves. B's holds are longer than A's.

**How we get there with real material and technique:** the eight genuinely B&W 1943 silver-gelatin negatives (not colour footage desaturated) are given one print-stage tone map to the measured range. The handmade notebook paper is modelled at the measured cream, with low-σ fibre noise, a fine wire coil, real tape strips with the yellow band and typed text set character by character with slight baseline and ink-density variation, as a typewriter does. Pen and red-pencil numbers are drawn stroke by stroke from the single-stroke glyph model in `proposals/src/common.py`, with pressure and per-instance jitter, and the red pencil gets a grainy, broken stroke (pencil, not ink) at about #b2282c core / #b76158 edge. No filter gives the prints their look: their tonality is the archive's. No reference pixels are copied or traced.

## 12 · Swarm units (2–4; the montage editor/assembler and the independent reviewer run separately)

Common rules: read `films/BRIEF-2.md`, the prompt, this plan, `films/kit.py` and the SCION prompts above (ids 40, 27, 41) in full. Put media under `films/sources/la-machine-a-tuer-le-temps/<role>/`. Do not commit, and do not touch other films. Spend at most about 45 minutes and download at most 75 MB.

**U1 · registrar-validator** (shot registrar + validator): re-verify the LoC rights of the 8 prints and update `films/credits/la-machine-a-tuer-le-temps.json` (8 used, the other 10 marked not used). Fix `print_op` and the 8 window paths by looking. Render and freeze the 8 × 120-frame rostrum assets (PNG, 1280×720, `sources/…/registrar/assets/<id>/0000.png…`). Compute frame md5s and `pool_hash`, and make a contact sheet. Write `validate.py`, which checks a recipe (preconditions above), a render ledger (every cut frame's md5 in the pool; notebook print appearances by translation only), the §8 fixture (including the must-fail cases), and framemd5 equality between two mp4s. **Output:** `swarm/la-machine-a-tuer-le-temps/pool-manifest.json` (plus `validate.py` next to it).

**U2 · notebook-animator** (handmade object + frame-by-frame animation, SCIONs 40 and 41): build the notebook rig as an importable module: cover and title flip, the cream spread with coil, mount cards (print + tape + ink number), the typewriter tape engine, the stroke-by-stroke pen and red-pencil engine with jitter and pressure, the translation-only card mover with spring settle and lift shadow, push/pull camera moves that end exactly on an asset's W0, the loose sheet and the coda graph. Emit the S5 event stream (JSON, frame-indexed) for the sound unit. Render the **test shot** (S5 + S6 + the first 3 s of 05 asset) and stills at S1, mid-S5, end of S5 and S10, beside the reference. **Output:** `swarm/la-machine-a-tuer-le-temps/notebook_rig.py` and `swarm/la-machine-a-tuer-le-temps/notebook-report.json` (stills, test-shot path, event stream, measured colour samples vs §11); media in `sources/…/notebook/`.

**U3 · cut-editors** (the rival editors under one owner, SCION 27): finalise recipes A1 and B1 against `pool_hash` and build fallback branches B2–B4. Render rough full-frame cuts with no notebook (`sources/…/editors/A1.mp4`, `B1.mp4`, plus branches) and watch them at normal speed. Record per cut the perceived cause, the person acting, and the decisive adjacency. Revise durations if A reads sinister or B reads unchanged. **Output:** `swarm/la-machine-a-tuer-le-temps/edit-recipes.json` (events, frame totals, base_pool_hash, branch notes, reading notes).

**U4 · sound-editor**: forage from the movingimagearchive.com cache first (clips with source sound), then Commons/LoC audio, licences recorded. Build stems T0–T4 as 48 kHz or 44.1 kHz wav plus a cue sheet with `sync_dep` to recipe event indices and to U2's event stream. Make the shared bed identical in both cut slots. Add the audio credits. **Output:** `swarm/la-machine-a-tuer-le-temps/sound-edit.json` (tracks, versions, cues, offsets, sources, licences); stems in `sources/…/sound/`.

Dependencies: U3 and U4 can start from this plan's fixed numbers (N = 120, recipes, frames). U2 reads `pool-manifest.json` when it exists and otherwise the §6 windows. The assembler writes `films/la-machine-a-tuer-le-temps.py` and renders two exports: the film (final mixes) and `…-shared-bed.mp4` (screening 1). It runs U1's validator on both, rewrites `films/notes/la-machine-a-tuer-le-temps.txt`, and finalises the credits.

## 13 · Acceptance bar (falsifiable; for a fresh critic with the film, the shared-bed export and the ledger)

1. **Frozen pool membership (measured).** Every frame of S3 and S7 in the ledger resolves to (asset_id, src_frame) with `0 ≤ src ≤ 119`, and its md5 equals the manifest's `frame_md5`. All recipes carry the manifest's `pool_hash`. The §8 fixture passes, and its injected-insert and `out = 130` cases fail.
2. **Audio-only replacement (measured).** The ffmpeg `framemd5` of the video stream is identical for all 1608 frames of the film and the shared-bed export. Audio differs only inside S3/S7, and within each export the T1 bed under S3 and S7 is sample-identical.
3. **Real frame-by-frame animation (structurally verified + perceptual).** In S5, each of the six moving cards differs from its rest image by translation only (NCC ≥ 0.98 after shift, no rotation or scale). Lift shadows grow and shrink over ≥ 4 frames. After S5, slot k holds B[k], with 07 and 08 never moved. Each new red number appears stroke by stroke over ≥ 6 frames, and no two instances of the same digit are pixel-identical. Watching at normal speed, the cards have weight and nothing wobbles at rest.
4. **Aesthetic, notebook vs reference (side by side).** Place a still from S1 and one from the end of S5 beside `oucipo.webp`'s spread. Measured: the page median is within 12 levels per channel of #f0e8d7, the tape band is within 25 of #dfbe87, the red numbers have R−G ≥ 50, and the cover in S0 is within 15 of #610e18. Perceptually: a viewer shown the pair takes them for pages of the same kind of dossier (flat light, broad margins, pasted B&W prints, typed tape, hand numbers), with no ruled paper, no fake grain and no vignette.
5. **Aesthetic, projections vs reference prints (side by side).** Place frames from S3 and S7 beside the reference's prints 15 and 16. Measured: luminance p1 is in 14–36, p99 in 210–238, and the median R−B in +3…+16. In the B 05 hold, consecutive frames at speed 0.5 come in identical pairs (no grain or boil on prints). Perceptually, the tonality matches genuine silver prints, not a filter.
6. **The inference changes (perceptually judged, normal speed, shared-bed screening first).** A fresh viewer describes A as routine station work and B as an illicit handoff, names the actor (the red cap as look-out and/or the woman as courier), and points to the 05→04→02 opening, or to the late clock, as the cut that changed it. The distinction survives the shared-bed screening, and the final mixes strengthen it without being necessary.
7. **Form and budget (measured).** Total 60–75 s. Cut A is 20–30 s and cut B 20–30 s. Every B projection is ≥ 1.5 s and the 05 glance is ≥ 4 s. The coda is 4–5 s and shows all 8 A→B lines plus the pool hash. Cuts fall on the recipe frames. The mp4 is ≤ 6 MB, and the poster frame comes from S5.
8. **Licences and provenance (measured).** The credits list the 8 LoC prints (used_as per shot) and every audio source with a PD/CC0/CC BY/CC BY-SA or archive-listed status and URL. No image outside the pool and the handmade notebook appears in any frame.


**Amendment (montage editor, repair round 2, 2026-11-16): the bar is read on the as-built 1608-frame timeline.** S0 0–71, S1 72–143, S2 144–161, S3 162–641 (cut A, 480 f), S4 642–659, S5 660–875 (216 f), S6 876–893, S7 894–1457 (cut B, 564 f), S8 1458–1475, S9 1476–1499, S10 1500–1607; total 67.0 s. Bars 1, 2 and 7 are measured on these ranges (bar 2: all 1608 frames). Recipe B1 is re-timed inside cut B (02 held 96 f = 4.0 s, src 24–119; 08 72 f = 3.0 s, src 0–71) so B1 cut starts are 0/120/168/264/336/396/432/492 (film 894/1014/1062/1158/1230/1290/1326/1386). Bar 6's "late clock" cue was withdrawn in round 1; B's decisive cuts are now 05→04→02 (order and duration) and, in sound, the latch before 04 plus the footsteps pre-lapping 02 and the parcel/paper cue into 06. Bar 9 (new, critic round 2): in the S3 and S7 bed, short-term RMS over 250 ms windows varies by ≥ 6 dB p10–p90, and no narrowband line stays > 20 dB above the local median for > 3 s.

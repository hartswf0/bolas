# Assembly: Exercises in Style (Mauro Martino), Direction 1 "Cut-Paper Platform"

- Script: `films/mauro-martino-exercises-in-style.py`, built on `films/kit.py` (Film, Mix). kit.py is not edited.
- Imported modules: `swarm/<slug>/stage/stage.py` (U2) and `rig/rig.py` (U3). Neither file is edited.
- Output: `assets/films/mauro-martino-exercises-in-style.mp4`, 64.0 s, 960×540, 24 fps.

**How each clip frame is made.**
- Every clip frame is `render(M, seed, t)`.
- `M = manifest(cond)` is built from `rig.baseline_manifest()`, whose sha1 is 6bb9bc5f4c9d4a1b7f4ce3a164be3cfba801fd6f.
- `manifest()` asserts that the set of keys differing from the baseline is empty for the baseline and has exactly one member for each delta.
- Frames of the six samples are rendered once into a frame cache by 4 forked workers. The grid reuses those cached frames.

## Editor-level substitutions (declared)

1. **Waiting crowd.** stage.py's `_crowd` (Peyriras 1933 Bourse plate) is rebound to U1's GrabCut cutouts A–H from Agence Rol, *Mars 1919, baraque Vilgrain*, at the same two placements. One printed alpha serves both treatments. In cut-paper the crowd is ink with sparse cream gouge lines cut where the real 1919 cloth catches light; in photographic-plate it keeps the cutouts' own greys.
2. **Photographic puppet fill.** `rig._bourse_fill` is rebound to U1's Vilgrain/Wilson 1919 swatches.
3. **The 1933 plate appears nowhere.** coverage.py traces every file a fresh-process film render opens and asserts bourse1933.jpg is not among them (`evidence.bourse1933_read_by_any_render = false`). It is listed under `evidence.absences`, not credited.
4. **Δ treatment = fill only (repair round 1).** `stage._backdrop_cut/_backdrop_photo`, `stage.bus_front` and `_crowd` are rebound so both treatments lay the SAME carved block masks and printed alphas. Photographic-plate refills them with real Rol 1916 texture (rectified upper-storey stone over facade and arcade, rectified cobbles over the street; the shopfront crop with its real pedestrians is no longer used). The outline IoU is asserted 1.0 for puppets (58 frames × 2 seeds) and for every stage layer: backdrop key blocks, crowd, bus shadow, bus body, bus front, bell tassel, both wheels.
5. **Cut-paper texture (repair round 1).** Dense horizontal gouge hatching plus pier nicks are cut through the dark arcade band. The puppets get cream knife lines wherever a front part (sleeve, forearm, hand, coat tail, skirt, hat, near leg) overlaps the body. The lines come from the drawn geometry, so they change on twos and never boil. Outlines are unchanged.
6. **Overhead roof-light (repair round 1).** The plan roof gets one cut opening over seat A (the rear bay). Seated passengers' plan forms are drawn there, clipped to the cell (`seat_cell_mask`). From above, the seat vacated (A5v, p1's disc slides out) and the seat taken (A6, the man's ringed hat disc enters at 5.50) are now visible. Only A-neck and A6w (predicted) and A4c (unpredicted) are lost.
7. **Wheels** roll by `wheel_angle_for(bus_x(0) - bus_x(t))`. They stop at A1 and roll again after A8.
8. **Bus plate.** The test-shot rectification of the same Rol 1916 photograph (same licence).
9. **Grain.** kit's per-frame grain is off; the paper grain is the stage's own, fixed per seed.
10. **Verification runs on the delivered render path.** coverage.py imports this film script as a module and renders every sample with its `render(M, seed, t)`. Its comparison sheet uses the film's own frame 0:05.2.

## Timecoded sequence

| Film time | Shot | Content | Evidence IDs |
|---|---|---|---|
| 0:00.0–0:04.0 | S0 | Title card "one incident, three instructions". The baseline manifest types out in cream on an ink tab; then the manifest sha1. | H6 (card); manifest sha1 (verify/manifests.json). Sound: street bed fade-in (F-street) plus kit clicks (synthetic). |
| 0:04.0–0:11.0 | S1 | **Baseline, seed 0417.** The test shot is at 0:05.2 (A3 shove, drawing 14). | F1 Rol 1916 (bus, wheels, window passengers), F-vilgrain (crowd mass), H1 facade, H2 pavement, H3 platform and board, H4 puppets (rig exposure sheet). Clip audio. |
| 0:11.0–0:18.0 | S2 | Baseline, seed 0418. There are 8 runners instead of 7; the protected masks are identical. | as S1 |
| 0:18.0–0:20.0 | S3 | Delta card: `treatment: cut-paper` is struck through over 6 frames and `photographic-plate` is typed. Shows diff keys {treatment}, the intended effect, and the composite note (Rol 1916 bus + facade/cobble texture, Rol 1919 crowd + cloth; board handmade). | H6. verify/manifests.json d-treatment |
| 0:20.0–0:27.0 | S4 | **Delta treatment, photographic-plate, seed 0417.** | F1 bus plate in its own greys; baseline carved facade/arcade/pavement blocks refilled with Rol 1916 stone and cobble texture (same outlines); F-vilgrain crowd in its own greys (same outline); puppets filled with F-vilgrain and F-wilson swatches; same outlines as the baseline. |
| 0:27.0–0:34.0 | S5 | Delta treatment, seed 0418. | as S4 |
| 0:34.0–0:36.0 | S6 | Delta card: `camera: street-side` is struck through and `overhead` is typed. | H6. d-camera |
| 0:36.0–0:43.0 | S7 | **Delta camera, overhead, seed 0417.** Shows the carved roof with its roof-edge board, the rear-bay roof-light over seat A, the hat discs, and the man's cord ring. | H5 plan stage, H4 plan forms (rig.plan_parts) |
| 0:43.0–0:50.0 | S8 | Delta camera, seed 0418. | as S7 |
| 0:50.0–0:57.0 | S9 | 3×2 grid of 300×169 cells, synchronized. Each row has 11 anchor chips that flip at their anchor times. On the overhead row A-neck, A4c (cord) and A6w (seat-in-window) are struck through as lost; partial chips are half-flipped; seat (A6) and vacate (A5v) flip solid via the roof-light. | verify/coverage.json lost_anchor_ids and partial_anchor_ids; clip audio |
| 0:57.0–0:58.0 | S9 hold | Hold on clip frame 29 (the shove). | Declared silence |
| 0:58.0–1:04.0 | S10 | Coverage report card and the cropped rejected-drift strip. | verify/coverage.json, verify/rejected-drift.json, verify/rejected-drift-strip.jpg (overhead rows); on-screen credits incl. CC BY engine; street bed fade-out |

## Sound ledger

**The one 7.0 s clip track** is built once by `clip_audio()` and laid at film times 4, 11, 20, 27, 36, 43 (six clip windows) and 50 (grid). It contains:
- U1 `bed_7.0s.wav`: engine from WWS CityBusMANSG220engine (Work With Sounds / Technical Museum of Slovenia, CC BY 4.0) plus street from "Sunday in the city street noise1" (cori, PD).
- U1 `bell_conductor_2.6s.wav` (qubodup Bell-ring, CC0) at t 6.00 (A7).
- Synthetic, declared: a kit `thud` at t 1.20 (A3) and a kit `click` at t 1.333 (A4).

**PCM check** (verify/coverage.json `audio_pcm`, status "measured"):
- The mastered s16 PCM, before the AAC encode, is identical in all 7 windows: sha1 `a4d07c3999c910ff21784c8cc04342aece3716ba`.
- Decoded AAC (96 kb/s) is NOT bit-identical. The windows align at lag 0, and each matches the first window at 17.0–17.7 dB SNR, about the same as decoded-vs-source (18.2 dB). This is codec loss on a noise-like bed. The S10 card says so.
- Outside the clip windows: street-bed segments and kit key clicks on the cards; 57.0–58.0 s is declared silence.

## Claim graph (section 9 acceptance bar → evidence)

- **Bar 1, proof structure.** `manifest()` asserts exactly one differing field per delta; verify/manifests.json; 2 seeds × 168 frames per condition; 3×2 grid of 300×169 cells.
- **Bar 2, protected action.**
  - The shove is at clip t 1.20 in all six samples (burn-in t 1.21 at film 5.2/12.2/21.2/28.2/37.2/44.2).
  - The seat is taken at 5.50, now visible in all six, including overhead via the roof-light (coverage A6 visible, 515 px, both seeds).
  - The board is legible on the side board and on the roof board.
- **Bar 3, leverage.**
  - Treatment outline IoU is 1.0 for puppets and all stage layers, asserted.
  - Camera losses: A-neck and A6w as predicted, plus A4c unpredicted.
  - Protected masks are identical across seeds over 168 frames, side and plan; the seed changes only the runner count (7 vs 8).
  - The RNG-coupled drift projector is rejected on 5 checks and shown on S10.
- **Bar 4, animation.** Rig exposure sheet on twos (anticipation, contact, drive, snap, recoil d13–d23); damped cord chain (rig/cord-energy.json); rotating wheels.
- **Bar 5, aesthetic.** Measured from the delivered mp4 (coverage.json `delivered_stills`). Reference: 24/40/91/187/234, mid about 30 %, chroma 12.6.

  | Still | p2/25/50/75/98 | Mid-tones | Chroma | dE paper / ink |
  |---|---|---|---|---|
  | 0:05.2 | 30/39/128/196/230 | 28.4 % | 13.4 | 1.2 / 1.3 |
  | 0:21.2 | 31/61/109/187/229 | 36.6 % | 13.1 | 1.4 / 1.5 |
  | 0:37.2 | 31/122/155/205/231 | 41.5 % | 17.2 | 0.4 / 1.7 |

  All pass. verify/comparison-sheet.jpg sets the film's own frame 0:05.2 beside martinoCharcoal.webp.
- **Bar 7, provenance.**
  - films/credits/mauro-martino-exercises-in-style.json has 6 rows (PD, CC0, CC BY 4.0, from Commons extmetadata via U1 plates/evidence/).
  - coverage.json `evidence.foraged` holds the same 6 rows, each joined to the files the film render actually read.
  - The 1933 Bourse plate is an absence, not a source: no render reads it.
  - S10 carries on-screen attribution, including the CC BY engine.
- **Bar 8, honest report.**
  - S10 and coverage.json give "2 of 2 inspected samples" per condition, the exact lost and partial IDs, and that seeds are repeatable by frame hash (frames 0, 29, 132 × 6, fresh process, generator_rev 013c0bb1ec5b).
  - The sound line quotes the measured status: pre-encode identity, lossy AAC.
  - The card also says "not claimed: anything about text-to-video generators in general".

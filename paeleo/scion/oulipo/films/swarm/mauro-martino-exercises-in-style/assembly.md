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

1. **Waiting crowd.** stage.py's `_crowd` draws the Peyriras 1933 Bourse plate. U1 judged that plate not verifiably PD in the US, so the script rebinds `stage._crowd` to U1's accepted GrabCut cutouts A–H from Agence Rol, *Mars 1919, baraque Vilgrain*.
   - The cutouts sit in the same two placements: right of the platform and left of the cab.
   - In cut-paper they are printed as an ink mass. In photographic-plate they keep their own greys.
2. **Photographic puppet fill.** `rig._bourse_fill` is rebound to U1's swatches, assigned per puppet:
   - Vilgrain 1919: coat_dark_long, coat_light_overcoat, coat_black_shawl, trouser_dark.
   - Wilson 1919: cape_officer, trouser_wilson.
   - Outlines do not depend on the fill, so the outline IoU of 1.0 still holds.
3. **Result:** the 1933 plate appears nowhere on screen.
4. **Rejected-drift strip on S10.** It is cropped to its two overhead rows (accepted and drift). Its baseline row was rendered by verify with the Bourse crowd, so it is not shown.
5. **Wheels.** The angle is `wheel_angle_for(bus_x(0) - bus_x(t))`. The wheels roll in, stop at A1 (0.90 s) and roll again after A8 (6.20 s). rig.side_frame froze them after 0.83 s.
6. **Bus plate.** stage.py uses the test-shot rectification of the same Rol 1916 photograph (same licence), with its own cab compression. U1's newer `plates/bus/bus_rgba.png` has different file names and geometry, so it was not swapped in.
7. **Grain.** kit's per-frame grain is switched off (`ink._grain = False`). The paper grain is the stage's own, fixed per seed, so nothing boils.

## Timecoded sequence

| Film time | Shot | Content | Evidence IDs |
|---|---|---|---|
| 0:00.0–0:04.0 | S0 | Title card "one incident, three instructions". The baseline manifest types out in cream on an ink tab; then the manifest sha1. | H6 (card); manifest sha1 (verify/manifests.json). Sound: street bed fade-in (F-street) plus kit clicks (synthetic). |
| 0:04.0–0:11.0 | S1 | **Baseline, seed 0417.** The test shot is at 0:05.2 (A3 shove, drawing 14). | F1 Rol 1916 (bus, wheels, window passengers), F-vilgrain (crowd mass), H1 facade, H2 pavement, H3 platform and board, H4 puppets (rig exposure sheet). Clip audio. |
| 0:11.0–0:18.0 | S2 | Baseline, seed 0418. There are 8 runners instead of 7; the protected masks are identical. | as S1 |
| 0:18.0–0:20.0 | S3 | Delta card: `treatment: cut-paper` is struck through over 6 frames and `photographic-plate` is typed. Shows diff keys {treatment} and the intended effect. | H6. verify/manifests.json d-treatment |
| 0:20.0–0:27.0 | S4 | **Delta treatment, photographic-plate, seed 0417.** | F1 bus plate in its own greys; rectified Rol facade and cobbles; F-vilgrain crowd in its own greys; puppets filled with F-vilgrain and F-wilson swatches; same outlines as the baseline. |
| 0:27.0–0:34.0 | S5 | Delta treatment, seed 0418. | as S4 |
| 0:34.0–0:36.0 | S6 | Delta card: `camera: street-side` is struck through and `overhead` is typed. | H6. d-camera |
| 0:36.0–0:43.0 | S7 | **Delta camera, overhead, seed 0417.** Shows the carved roof with its roof-edge board, the hat discs, and the man's cord ring. | H5 plan stage, H4 plan forms (rig.plan_parts) |
| 0:43.0–0:50.0 | S8 | Delta camera, seed 0418. | as S7 |
| 0:50.0–0:57.0 | S9 | 3×2 grid of 300×169 cells, synchronized. Each cell has 11 anchor chips that flip at their anchor times. On the overhead row the chips A-neck, A4c, A5v, A6 and A6w are struck through as lost, and the partial chips are half-flipped. | verify/coverage.json lost_anchor_ids and partial_anchor_ids; clip audio |
| 0:57.0–0:58.0 | S9 hold | Hold on clip frame 29 (the shove). | Declared silence |
| 0:58.0–1:04.0 | S10 | Coverage report card and the cropped rejected-drift strip. | verify/coverage.json, verify/rejected-drift.json, verify/rejected-drift-strip.jpg (overhead rows); street bed fade-out |

## Sound ledger

**The one 7.0 s clip track** is built once by `clip_audio()` and laid at film times 4, 11, 20, 27, 36, 43 and 50 s. It contains:
- U1 `bed_7.0s.wav`: the engine, from WWS CityBusMANSG220engine (CC BY 4.0), plus the street, from "Sunday in the city street noise1" (PD).
- U1 `bell_conductor_2.6s.wav` (qubodup Bell-ring, CC0) at t 6.00 (A7).
- Two synthetic sounds, both declared: a kit `thud` at t 1.20 (A3) and a kit `click` at t 1.333 (A4).

**PCM check.**
- Method: the film's kit.Mix is rebuilt in-process and mastered, and the s16 PCM of each 7.0 s window is hashed at 44.1 kHz.
- Result: all 7 windows have the identical sha1 `a4d07c3999c910ff21784c8cc04342aece3716ba`.
- This result is computed by `pcm_report()` in the script and printed on the S10 card.
- verify/coverage.json still says "pending" because coverage.py was not rerun. Its harness imports stage.py directly, with the Bourse crowd, so a rerun would not reflect the film.

**Outside the clip windows:**
- The cards carry street-bed segments and kit key clicks (synthetic, declared).
- 57.0–58.0 s is declared silence.

## Claim graph (section 9 acceptance bar → evidence)

- **Bar 1, proof structure.**
  - `manifest()` asserts exactly one differing field per delta.
  - Each condition has 2 seeds × 168 frames. The grid holds 6 cells of 300×169.
  - Source: verify/manifests.json.
- **Bar 2, protected action.**
  - The rig anchors fire on fixed drawings: A3 on d14, A6 on d66.
  - The board reads `MADELEINE – BASTILLE` on the side board and on the roof board.
  - Stills checked: 0:05.2, 0:12.2, 0:21.2 and 0:37.2.
- **Bar 3, leverage.**
  - Puppet outline IoU is 1.0, and protected masks are identical across seeds (coverage.json).
  - Overhead losses are shown on the chips and the card.
  - The drift strip is shown on the card.
- **Bar 4, animation.**
  - The rig exposure sheet is drawn on twos, with anticipation, contact, drive, snap and recoil at d13–d23.
  - The cord is a damped chain that starts at d15 and is at 0.70 % of peak energy by 3.2 s (rig/cord-energy.json).
  - The wheels rotate.
- **Bar 5, aesthetic (measured).** Baseline at t 1.20: L percentiles 33/42/128/200/232, mid-tone fraction 27 %, chroma 13.1, ΔE 0.0 to both tokens (coverage.json "aesthetic"). The crowd layer has since changed to Vilgrain; see the measurement in the editor report.
- **Bar 7, provenance.** films/credits/mauro-martino-exercises-in-style.json has 6 rows. Licences are PD, CC0 and CC BY 4.0, read from Commons extmetadata by U1 (plates/evidence/).
- **Bar 8, honest report.** The S10 card shows the "n of 2 inspected samples" rates, the exact lost and partial IDs, and the line "not claimed: anything about text-to-video generators in general".

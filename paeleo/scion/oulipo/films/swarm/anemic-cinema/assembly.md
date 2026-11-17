# Anémic cinéma · variation: assembly (editor, repair round 1)

**Output:** `assets/films/anemic-cinema.mp4`. 24.00 s, 576 frames at 960×540 and 24 fps, H.264 (kit crf 28) with AAC audio, 1.24 MB (sha1 4b962d44d2fd…).

**Assembly script:** `films/anemic-cinema.py` (sha1 ed3b9665ffb1…). It reads `score.json`, pre-renders every body and switch frame with `switch.render_frame` (2× render, real 180° shutter of 8 sub-frames of the actual rotation, INTER_AREA downsample, warm cast only on the optical discs), asserts the fixtures, then pastes the decoded frames onto the L=2 black field through `kit.Film` (`ink._grain = False` every frame, no vignette) and adds the decoded bell wav with `mix.add`. `kit.Mix.master` is replaced inside the script by a pass-through, because the kit master boosts a quiet track by up to 4×. `kit.py` is untouched.

**Variants** (`films/sources/anemic-cinema/editor/`): `anemic-cinema-silent.mp4` (S0, `--silent`), `anemic-cinema-B1.mp4` (W1 replaced by a hard cut at F126), `anemic-cinema-B2.mp4` (W1 replaced by an 18-frame dissolve). Each is the full film with only W1 or the sound changed, for side-by-side viewing.

## What changed in repair round 1

| review item | change | where |
|---|---|---|
| T2 legibility (reader lost at 1/256) | ω_read is now **1/128 rev/frame** (10 ticks of 1280; was 1/256), U2's recommendation, applied as the film's branch. The reading interval stays F288–425 (5.75 s) because the film length is fixed at 24.0 s. Under U2's reading model, 13 characters per second now loses at most 2 letters past 110° (max tilt 117°, near « …OCHE »), where 1/256 lost 15–19 letters upside down. | `switch.W_READ`, `score.json`, `glyphpaths.json → reading_speed.adopted_repair_1` |
| inner-turn crowding | the spiral now ends 0.20 ring pitch inside the innermost ring (was 0.45), so the innermost turn opens: 4 glyphs on ring 6, minimum glyph radius 33 px (was 27). All of U2's fixtures still pass. | `glyphs.R_END` |
| 'SONNE' stacking on adjacent turns | the closest radial alignment of the two SONNEs grows from 4° to 8°. This is **not solved**: both halves share their middle « DU QUAI SONNE », and one half is about one turn long. A sweep of separator width, number of halves and spiral end found no layout that separates both SONNE and QUAI by more than ~25° without overcrowding or over-opening the type. Recorded as a residual. | scratch sweep, see weaknesses |
| W1 plate change was a global crossfade | the ground now transforms **band by band with the marks, outer bands first**: u(r) = smooth((k − k0 + 1 − 2 f(r)) / 4), where f(r) is the continuous ring index at plate radius r. Each band starts with its ring's 2-frame stagger and the innermost finishes at k0+17. The front is smooth, with no hard annular edges. The warm cast follows the same map. The same applies to W2 (outer bands first back to neutral) and W3 (key-ring radii; the engraved guide grooves appear ring by ring). | `switch.plate_front` |
| W1 rotation, 2 % pair against a 3 % post-hoc band | the bar was restated **before measuring** and the 3 % band dropped: no pause; the aggregate rate over F118–152, and every entry, exit and body pair, within 1 % (asserted). The interior hybrid pairs are **reported, not passed**: W1 worst pair F138→139 is +1.82 %, which does **not** meet ±1 %. | `assembly-fixtures.json → I4_constant_omega` |
| ShareAlike notice | the note and credits[0] now give the title, author, link, licence, the changes, and the statement that the adapted key imagery is shared under CC BY-SA 4.0. | notes, credits |
| 'One plate turns throughout' | now reads "One plate turns through all four discs and the switches; title and still pass are static". | notes |
| typeface | Liberation Sans Bold (SIL OFL 1.1) is recorded among the handmade materials. | notes, H-TYPE below |
| credits against the bar | the acceptance bar is updated to name **both** keys: K0 (Noy-nac, CC BY-SA 4.0) on rings 0, 2, 4 and K1 (Llave bronce, Jorge Barrios, PD) on rings 1, 3, 5. Both are verified. | this file, credits |
| I8 cuts into the still pass | recorded as an **accepted, declared exception**: a ramp would break the byte-identity of the frozen F360, which the still pass exists to show. Each cut is a single step with no repetition, so there is no strobing. | `assembly-fixtures.json → I8_luminance_step.note` |

**Protected and unchanged:** the W1 metamorphosis stages (18 distinct single-state hybrid states; F134 = ring, ring, closing, slide, squashed, glyph, glyph), the integer 1280-tick clock, the Pompidou-like embossed type on the neutral sphere-lit plate, the L=2 black field with σ 0, the engraved grooves, the real GrabCut keys, the three bell strikes over digital silence, the byte-identical F360 still and the three-frame strip, and the credits ledger.

## Evidence IDs

| ID | item | kind | record |
|---|---|---|---|
| E-K0 | `File:Skeleton_key_(Yale_&_Towne).png`, Noy-nac, CC BY-SA 4.0 | FORAGED (Commons), then adapted: GrabCut cutout, recoloured, arranged on rings; the adaptation is shared under CC BY-SA 4.0 | credits[0], optics-ledger.json (extmetadata 2026-11-17) |
| E-K1 | `File:Llave_bronce.jpg`, Jorge Barrios, public domain (PD-self) | FORAGED (Commons), GrabCut cutout | credits[1], optics-ledger.json |
| E-BELL | `File:Striking_a_bell_15cm_large.ogg`, stephan via pdsounds.org, public domain | FORAGED sound (Wikimedia mp3 transcode, decoded with ffmpeg, only trimmed and levelled) | credits[2], sound-ledger.json, switch/bell.wav |
| H-T1 | « LA PORTE TOURNE SUR LE GOND · LE GOND TOURNE SUR LA PORTE » | HANDMADE (original; checked against Duchamp's ten disc texts) | glyphpaths.json, glyphs.py |
| H-T2 | « LA CLOCHE DU QUAI SONNE LA CLEF · LA CLEF DU QUAI SONNE LA CLOCHE » | HANDMADE | glyphpaths.json, glyphs.py |
| H-TYPE | Liberation Sans Bold capitals, SIL OFL 1.1 (system font), filled with the groove stock | HANDMADE setting of an openly licensed typeface | glyphs.py |
| H-OA | engraved eccentric ring disc: 7 rings and a core, groove pitch 2.5 px at 1× | HANDMADE procedural | optics.py, optics-ledger.json → rings |
| H-OB | key-ring layout: 6 eccentric rings, 69 slots, guide grooves | HANDMADE layout of E-K0 and E-K1 | optics.py → key_slots |
| H-SUB | Substitute W1–W3 (Foldès drawing substitution) plus the radial plate front | HANDMADE frame-by-frame animation | switch.py, score.json |
| H-TITLE | title in cream groove stock | HANDMADE type | anemic-cinema.py `title_frame` |
| F-* | fixtures asserted at assembly | measured or structural | editor/assembly-fixtures.json; unit fixtures in fixtures.json |

## Timecoded sequence (score.json frames)

| time (s) | frames | segment | ω (rev/frame) | sound | evidence |
|---|---|---|---|---|---|
| 0.00–1.00 | 0–23 | title « ANÉMIC CINÉMA · VARIATION », 6-frame fade in and out | 0 (static) | declared silence | H-TITLE, H-TYPE |
| 1.00–5.25 | 24–125 | **T1** pun disc, sphere-lit neutral plate | 1/80 (0.30 rev/s) | silence | H-T1 |
| 5.25–6.00 | 126–143 | **W1** T1→O_A drawing substitution, outside-in with a 2-frame stagger; the plate turns warm and dark band by band with the marks | 1/80, constant | bell at 5.25 s | H-SUB, E-BELL, F-I4, F-single-state |
| 6.00–10.25 | 144–245 | **O_A** engraved rings, gain 0.7→1.0, locked orbit (intended to approach) | 1/80 | silence | H-OA |
| 10.25–11.00 | 246–263 | **W2** O_A→T2 reverse substitution; the plate returns to neutral band by band | 1/80, constant | bell at 10.25 s | H-SUB, E-BELL |
| 11.00–12.00 | 264–287 | T2, ω easing from fast to reading speed | 1/80→1/128 | silence | H-T2 |
| 12.00–17.75 | 288–425 | **T2 declared reading interval**, first letter phase-locked to 12 o'clock at F288 | **1/128** (0.1875 rev/s) | silence | H-T2, F-I2 |
| 17.75–18.50 | 426–443 | **W3** T2→O_B: 69 token runs swapped in token order for real key cutouts, which slide into their slots; the black card and guide grooves arrive ring by ring | 1/128, constant | bell at 17.75 s | H-SUB, E-K0, E-K1, E-BELL |
| 18.50–21.50 | 444–515 | **O_B** key rings, gain 1.0→0.7, concave plate (intended to recede); ω eases back to 1/80 over F444–467 | 1/128→1/80 | silence | H-OB, E-K0, E-K1 |
| 21.50–23.00 | 516–551 | still pass 1: F360 frozen, byte-identical to the moving frame (asserted) | 0 (static) | silence | F-still |
| 23.00–24.00 | 552–575 | still pass 2: F360, F361 and F362 as a plain strip | 0 (static) | silence | glyphpaths.json still_pass |

## Fixtures asserted before encoding (assembly-fixtures.json, film variant)

- **I3 alternation.** The bodies run T1, O_A, T2, O_B. The test score T1, O_A, O_B, T2 fails as required, and each window belongs to its incoming disc. *Structural.*
- **I4 constant ω.** The declared ω is exact on integer ticks. Measured by polar phase correlation and a rotation-SSD search:
  - W1: aggregate 4.4949° per frame against 4.5° (0.11 %); entry, exit and body pairs ≤0.18 %; window median 0.15 %. The **worst interior hybrid pair, F138→139, is +1.82 %, a miss of the ±1 % per-pair bar, reported and not passed.**
  - W2: aggregate 0.07 %, every pair ≤0.46 %.
  - W3: 2.811° against 2.8125° (0.05 %), every pair ≤0.24 %.
  - No pauses anywhere. *Measured.*
- **I5 periodicity.** P=80 and P=128 are exact in integer ticks. *Structural.*
- **I2 glyph order.** T1 at F100 and T2 at F360 read in token order under both cw and ccw; W1 and W2 are monotone; the W3 swaps happen in token order. *Structural.*
- **Per-mark single state.** Film ghost overlap peaks at 0.21 %, against 9.6 % for B2. W1 shows 18 distinct hybrid states. *Measured and structural.*
- **Replay.** The F126–143 sha1 hashes are identical in a fresh process. *Measured.*
- **Still pass.** Part 1 equals F360 pixel for pixel. *Measured.*
- **Black field.** Corner L 2.0, σ 0.0. *Measured.*
- **I8 luminance step.** The largest step over F24–515 is 11.3 % (F428, W3), under the 25 % limit. The cuts at F516 (+190 %) and F552 (−66 %) are an accepted, declared exception, as explained above. *Measured.*

## Acceptance bar: credits (updated)

The film shows exactly three foraged items, all verified from Commons extmetadata on 2026-11-17:
- K0, Noy-nac, CC BY-SA 4.0: adapted, with the adaptation shared under CC BY-SA 4.0;
- K1, Jorge Barrios, PD-self;
- the bell, stephan via pdsounds.org, PD.

Nothing else foraged appears. The reference images appear only on the outside comparison sheets.

## Aesthetic check

- `editor-compare-08.0s-duchamp2.jpg`, F192 (O_A body, unchanged by this repair):
  - ring L p10/50/90 = 101/121/140 and R−B 21, against 99/118/139 and 18 in the reference;
  - corner L 2;
  - grooves resolved at 1:1.
- `editor-compare-15.0s-spiralTextPom.jpg`, F360:
  - neutral plate with |R−B| = 0 and a ramp from upper left to lower right;
  - letters at L ≈ 240;
  - the inner turn is now open.
- Our frame is always on the left; the reference sits beside it and is never composited.

## Sound (measured on the decoded mp4)

- Peak −14.4 dBFS.
- Onsets at 5.27, 10.27 and 17.77 s, within one frame of F126, F246 and F426.
- Zero non-silent 10 ms windows outside the three 1.5 s bell spans.

## Deliverable index (prompt section 9)

| deliverable | file | sha1 (12) |
|---|---|---|
| playable sequence | assets/films/anemic-cinema.mp4 | 4b962d44d2fd |
| silent version and the two baselines | editor/anemic-cinema-{silent,B1,B2}.mp4 | aa6b3d64da44 / bc810a9ff4da / 0fae468a77ad |
| procedural disc source | optics.py · glyphs.py · switch.py | 95d2cc0d4170 · ac7f12d6d8c1 · 33482d3db9cb |
| glyph mapping | glyphpaths.json | 202bee5bf8c5 |
| exposure and phase score | score.json | 148a8ebb8ab2 |
| still / reduced-motion view | film 21.5–24.0 s; films/stills/anemic-cinema/ | (in the film) |
| assembly | films/anemic-cinema.py | ed3b9665ffb1 |
| credits | films/credits/anemic-cinema.json (E-K0, E-K1, E-BELL) | 09000f7a41fe |
| perceptual review | **still to be done by a viewer with real-time playback** (protocol below) | – |

## Claim graph (claim → evidence → label)

- "One disc changing, not a cut" → H-SUB, F-I4, F-single-state, B1/B2 variants → measured plus structural; **the perceptual judgement is unknown**.
- "The ground transforms with the marks" → `switch.plate_front`; check visually at F128, F132, F136 and F252 → structural.
- "Constant speed through the switches" → I4 → measured: the aggregate and the edge pairs pass, **and one interior hybrid pair misses ±1 % (1.82 %)**.
- "O_A approaches, O_B recedes" → optics depth clips and the gain profiles → **unknown** (no real-time viewing).
- "T2 legible at its speed" → U2's reading model on the adopted layout (glyphpaths.json `reading_speed.adopted_repair_1`) → model only: 13 characters per second with 2 letters past 110°; at 10 characters per second the pun does not fit 5.75 s; **no live read-aloud yet**.
- "The still pass shows the same layout" → F-still → measured.
- "The material is honest" → credits with the ShareAlike notice, kit grain off, field σ 0 → measured and structural.

### Perceptual protocol still owed (real-time playback, 960×540, normal speed)
1. Watch O_A (6.0–10.25 s) and O_B (18.5–21.5 s), and record the apparent depth direction of each disc: toward the eye, away, or bistable.
2. If O_A reads as receding or bistable, reverse `optics.ECC`'s sign order or raise the gain end-point, keeping ω fixed. If O_B is weak, steepen `key_ring_set` b from 1.0→0.80 to 1.0→0.65.
3. Read T2 aloud over 12.0–17.75 s, and note where the place is lost.
4. Watch W1 next to B1 and B2.

## Known weaknesses

1. **Depth is unverified by viewing.** Stereokinetic depth can flip sign. No real-time viewer has confirmed either disc.
2. **W1 has one interior hybrid pair at +1.82 %** (F138→139), above the ±1 % per-pair bar. The closing arcs grow asymmetrically toward their neighbours, which moves the arc centroids. The declared ω is exact, the aggregate is within 0.11 %, and it is not hand-corrected.
3. **Reading time.** At 1/128 over 5.75 s, a reader at 10 characters per second cannot fit the 65-character pun (6.5 s plus a pause). At 13 characters per second, 2 letters tip past 110°. A 7.0 s interval, U2's full recommendation, would need 30 frames from another segment or a 25.25 s film.
4. **The SONNE / QUAI radial stacking** on adjacent turns is only reduced (to 8°), because it is inherent in the chiastic text.
5. **The W1 pop at F141–142** (ring 6 forms from 4 dashes, and the core appears in two steps) remains.
6. **Still-pass cuts** (+190 % and −66 % steps) are an accepted exception to I8.
7. **The title** is a quiet L≈140 line, so the film opens nearly dark for 1 s.
8. **The warm cast** on the optical discs is a global RGB gain (grade), not a property of the material. The critic marked this optional, and it is unchanged.

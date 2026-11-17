# Anémic cinéma · variation: assembly (editor)

**Output:** `assets/films/anemic-cinema.mp4`. It runs 24.00 s: 576 frames at 960×540 and 24 fps, H.264 (kit crf 28) with AAC audio, 1.18 MB (sha1 1b5179ccb914…).

**Assembly script:** `films/anemic-cinema.py` (sha1 716278ac161d…). It does five things:
1. Reads `score.json`.
2. Pre-renders every body and switch frame with `switch.render_frame`. Each frame is rendered at 2× and integrated through a 180° shutter of 8 sub-frames of the real rotation, then downsampled with INTER_AREA. The warm grade goes on the optical discs only.
3. Asserts the fixtures.
4. Pastes the decoded frames onto the L=2 black field through `kit.Film`, with `ink._grain = False` on every frame and no vignette.
5. Adds the decoded bell wav with `mix.add`.

`kit.Mix.master` is replaced inside the script by a pass-through, because the kit master boosts a quiet track by up to 4×. `kit.py` itself is untouched.

**Variants**, all in `films/sources/anemic-cinema/editor/`:
- `anemic-cinema-silent.mp4`: S0, `--silent`.
- `anemic-cinema-B1.mp4`: W1 replaced by a hard cut at F126.
- `anemic-cinema-B2.mp4`: W1 replaced by an 18-frame dissolve.

Each is the full film with only W1 or the sound changed, so it can be watched side by side with the main film.

## Evidence IDs

| ID | item | kind | record |
|---|---|---|---|
| E-K0 | `File:Skeleton_key_(Yale_&_Towne).png`, Noy-nac, CC BY-SA 4.0 | FORAGED (Commons) → GrabCut cutout | credits/anemic-cinema.json [0], optics-ledger.json (manifest, extmetadata 2026-11-17) |
| E-K1 | `File:Llave_bronce.jpg`, Jorge Barrios, public domain (PD-self) | FORAGED (Commons) → GrabCut cutout | credits [1], optics-ledger.json |
| E-BELL | `File:Striking_a_bell_15cm_large.ogg`, stephan via pdsounds.org, public domain | FORAGED sound (Wikimedia mp3 transcode, decoded with ffmpeg, then only trimmed and levelled) | credits [2], sound-ledger.json, switch/bell.wav (sha1 842139d76c71…) |
| H-T1 | pun « LA PORTE TOURNE SUR LE GOND · LE GOND TOURNE SUR LA PORTE » | HANDMADE (original; checked against Duchamp's ten disc texts) | glyphpaths.json, glyphs.py |
| H-T2 | pun « LA CLOCHE DU QUAI SONNE LA CLEF · LA CLEF DU QUAI SONNE LA CLOCHE » | HANDMADE | glyphpaths.json, glyphs.py |
| H-OA | engraved eccentric ring disc: 7 rings and a core, groove pitch 2.5 px at 1× | HANDMADE procedural | optics.py, optics-ledger.json → rings |
| H-OB | key-ring layout: 6 eccentric rings, 69 slots, guide grooves | HANDMADE layout of E-K0/E-K1 | optics.py → key_slots |
| H-SUB | Substitute W1–W3 (Foldès drawing substitution) | HANDMADE frame-by-frame animation | switch.py, score.json |
| H-TITLE | title in cream groove stock | HANDMADE type | anemic-cinema.py `title_frame` |
| F-* | fixtures asserted at assembly | measured / structural | sources/anemic-cinema/editor/assembly-fixtures.json; full unit fixtures in fixtures.json |

## Timecoded sequence (score.json frames)

| time (s) | frames | segment | ω (rev/frame) | sound | evidence |
|---|---|---|---|---|---|
| 0.00–1.00 | 0–23 | title « ANÉMIC CINÉMA · VARIATION », 6 f fade in and out | 0 | declared silence | H-TITLE |
| 1.00–5.25 | 24–125 | **T1** pun disc, sphere-lit neutral plate | 1/80 (0.30 rev/s) | silence | H-T1 |
| 5.25–6.00 | 126–143 | **W1** T1→O_A, drawing substitution outside-in, 2 f stagger; F134 = ring, ring, closing, slide, squashed, glyph, glyph | 1/80, constant | bell at 5.25 s | H-SUB, E-BELL, F-I4, F-single-state |
| 6.00–10.25 | 144–245 | **O_A** engraved rings, gain 0.7→1.0, locked orbit (meant to approach) | 1/80 | silence | H-OA |
| 10.25–11.00 | 246–263 | **W2** O_A→T2, reverse substitution | 1/80, constant | bell at 10.25 s | H-SUB, E-BELL |
| 11.00–12.00 | 264–287 | T2, ω easing fast → read | 1/80→1/256 | silence | H-T2 |
| 12.00–17.75 | 288–425 | **T2 declared reading interval**, phase-locked at F288 | 1/256 (0.094 rev/s) | silence | H-T2, F-I2 |
| 17.75–18.50 | 426–443 | **W3** T2→O_B: 69 token runs swapped in token order for real key cutouts, which slide into slots | 1/256, constant | bell at 17.75 s | H-SUB, E-K0, E-K1, E-BELL |
| 18.50–21.50 | 444–515 | **O_B** key rings, gain 1.0→0.7, concave plate (meant to recede); ω eases back to 1/80 over F444–467 | 1/256→1/80 | silence | H-OB, E-K0, E-K1 |
| 21.50–23.00 | 516–551 | still pass 1: F360 frozen (byte-identical to the moving frame, asserted) | 0 | silence | F-still |
| 23.00–24.00 | 552–575 | still pass 2: F360, F361 and F362 as a plain strip (311×175 each, x=324, y=3/182/361) | 0 | silence | glyphpaths.json still_pass |

## Fixtures asserted before encoding (assembly-fixtures.json, film variant)

- **I3 alternation.** The bodies run T1, O_A, T2, O_B. The test score T1, O_A, O_B, T2 fails as required, and each window belongs to its incoming disc. *Structurally verified.*
- **I4 constant ω.** The declared ω is exact on integer ticks. Measured by polar phase correlation on this film's frames:
  - W1: median error 0.10 %, maximum 2.0 % (interior hybrid pair), mean 4.5025° per frame against 4.5°;
  - W2: maximum 0.11 %;
  - W3: maximum 0.32 %;
  - no pauses.

  *Measured.*
- **I5 periodicity.** P=80 and P=256 hold exactly. *Structurally verified.*
- **I2 glyph order.** T1 at F100 and T2 at F360 read in order under both cw and ccw, W1 and W2 are monotone, and the W3 swaps happen in token order. *Structurally verified.*
- **Per-mark single state.** The film's maximum ghost overlap is 0.21 % against B2's 9.6 %. W1 shows 18 distinct hybrid states. *Measured and structurally verified.*
- **Replay.** The sha1 hashes of F126–143 are identical in a fresh process. *Measured.*
- **Still pass.** Part 1 equals F360 pixel for pixel. *Measured.*
- **Black field.** Corner L 2.0, σ 0.0. *Measured.*
- **I8 luminance step.** The largest step over F24–515 is 8.9 % (F253). Two hard cuts are declared and not asserted: into still pass 1 at F516 (+186 %) and into the strip at F552 (−66 %). *Measured.*

## Aesthetic check (measured on the film's frames)

- **8.0 s (F192) beside duchamp2:**
  - ring L p10/50/90 = 101/121/140, R−B 21.2, corner L 2.0;
  - the radial scan at row 270 alternates ring 15–16 px with gaps of 16, 11, 9, 8 px, so the gaps are eccentric and narrow on one side;
  - grooves survive encoding (high-frequency energy of the decoded frame is 93 % of the source in a 100 px crop).
  - Sheet: `editor-compare-08.0s-duchamp2.jpg`.
- **15.0 s (F360) beside spiralTextPom:**
  - plate |R−B| = 0, ramp L 205 at upper left to 58 at lower right;
  - letters p99 L 242.
  - Sheets: `editor-compare-15.0s-spiralTextPom.jpg` and `editor-compare-03.0s-spiralTextPom.jpg`.
- On every sheet our frame is on the left and the reference image sits beside it, never composited into the film.

## Sound (measured on the decoded mp4)

- Peak −14.4 dBFS.
- Onsets at 5.27, 10.27 and 17.77 s, within 1 frame of F126, F246 and F426.
- Zero non-silent 10 ms windows outside the three 1.5 s bell spans.

## Deliverable index (prompt section 9) with revisions

| deliverable | file | sha1 (12) |
|---|---|---|
| playable sequence | assets/films/anemic-cinema.mp4 | 1b5179ccb914 |
| silent version and the two baselines | editor/anemic-cinema-{silent,B1,B2}.mp4 | aef5d49d8ef4 / 14adc6fba9b3 / a73cbbc6e202 |
| procedural disc source | optics.py · glyphs.py · switch.py | 95d2cc0d4170 · 7635c806e42e · cd95be579bd6 |
| glyph mapping | glyphpaths.json | 3b6d23102475 |
| exposure/phase score | score.json (+ switch/phase_visualizer.png) | 6c0f99f4b03d |
| still / reduced-motion view | film 21.5–24.0 s; films/stills/anemic-cinema/ | (in the film) |
| assembly | films/anemic-cinema.py | 716278ac161d |
| credits | films/credits/anemic-cinema.json (3 items: E-K0, E-K1, E-BELL) | aaa4338bf90b |
| perceptual review | **not done yet.** It is left to the independent critic: depth of O_A and O_B, reading T2 aloud, and W1 against B1/B2 | – |

## Claim graph (claim → evidence → label)

- "One disc changing, not a cut" → H-SUB, F-I4, F-single-state, B1/B2 variants → measured plus structural; **the perceptual judgement is unknown**.
- "O_A approaches, O_B recedes" → optics depth clips, gain profiles in score.json → **unknown** (still frames only).
- "T2 legible at its speed" → U2 reading model (glyphpaths.json reading_speed) → **unknown, at risk.** U2's model predicts the reader is lost at 1/256 over 5.75 s (see weaknesses).
- "Still pass shows the same layout" → F-still → measured.
- "Material is honest" → credits, kit grain off, field σ 0 → measured and structurally verified.

## Known weaknesses

1. **Reading speed.** The scored ω_read is 1/256 over F288–425. This follows plan section 6 as assigned and was kept by U3. U2's reading model recommends 1/128 over 168 frames and predicts that at 1/256 a reader at 13 characters per second is lost near « LA CLEF » in the second half. That change was not made: it is a director's call and would retime W3, O_B and the still pass. `switch.W_READ` and `READ` are parameterised if it is adopted.
2. **Depth is unconfirmed by viewing.** The sign of stereokinetic depth can flip.
3. **O_A eccentricity.** It is milder than duchamp2: the centres drift only 11 px per ring.
4. **W1 pop at F141–142.** Ring 6 forms from 4 dashes and the core appears in two steps. This was noted by U3 and not hand-corrected.
5. **Two hard cuts into the still pass.** The luminance steps are +186 % at F516 and −66 % at F552. They are single steps, not strobing, but they break the 25 % rule of I8, which is declared only for the title.
6. **Title luminance.** The title is a quiet L≈140 line, so the film opens nearly dark for 1 s.

# Anémic cinéma · variation: assembly (editor, repair round 2)

**Output:** `assets/films/anemic-cinema.mp4`. 24.00 s, 576 frames at 960×540 and 24 fps, H.264 (kit crf 28) with AAC audio, 1.13 MB (sha1 5c743f077633…).

**Assembly script:** `films/anemic-cinema.py` (sha1 3f0a98bc4800…). It reads `score.json`, pre-renders every body and switch frame with `switch.render_frame` (2× render, real 180° shutter of 8 sub-frames of the actual rotation, INTER_AREA downsample, warm cast only on the optical discs), asserts the fixtures, then pastes the decoded frames onto the L=2 black field through `kit.Film` (`ink._grain = False` every frame, no vignette) and adds the decoded bell wav with `mix.add`. `kit.Mix.master` is replaced inside the script by a pass-through, because the kit master boosts a quiet track by up to 4×. `kit.py` is untouched.

**Variants** (`films/sources/anemic-cinema/editor/`): `anemic-cinema-silent.mp4` (S0, `--silent`), `anemic-cinema-B1.mp4` (W1 replaced by a hard cut at F126), `anemic-cinema-B2.mp4` (W1 replaced by an 18-frame dissolve). Each is the full film with only W1 or the sound changed.

## What changed in repair round 2

The film now meets the bar **as written**; no clause of the bar is amended by this file.

| review item | change | where |
|---|---|---|
| reading speed changed the bar (1/128, P=128) | **restored ω_read = 1/256 rev/frame = 0.09375 rev/s (5 ticks of 1280), P = 256.** The ease into it runs over steps 265–287, the reading interval F288–425 is constant at 5 ticks, W3 runs at 5 ticks, and the ease back to 1/80 runs over 445–467. The assembly now asserts W_READ = 5, P_read = 256, a constant reading interval, and θ(k+80) ≡ θ(k) on every held 1/80 stretch. Repair 1's 1/128 is withdrawn. | `switch.W_READ`, `score.json` (sha1 6c0f99f4b03d) |
| stale fixtures.json and glyphpaths.json | `switch_fixtures.py` re-run on the final score and the final rendered frames: W3 declared ω = 5/1280, I5 ω_read P = 256 (exact integer). `python3 -I glyphs.py dump` re-run (θ_read from score.json). The `still_pass` block now carries θ(F360) from score.json (3.028692 rad), and `reading_speed.adopted_repair_2` records the restored speed and its risk. | `fixtures.json`, `glyphpaths.json` |
| second key K1 (Llave bronce) outside the bar | **K1 dropped.** Every one of the 69 keys is now K0 (Noy-nac, CC BY-SA 4.0); rings 1, 3, 5 carry the same cutout mirrored (teeth down). `optics.KEY_FILES = {K0}`. Asserted at assembly: credits list exactly the K0 key and the bell, and every key slot is K0. K1's files stay in sources, unused and uncredited. | `optics.py`, credits, `optics-ledger.json` |
| W1 pair F138→139 at +1.82 % | Two changes, neither touches θ. (1) The closing arcs now grow **symmetrically** about each dash's own angle (half-width = 0.8 × the mean half-gap), so their centroids stay put. That alone moved the pair to −1.53 %. Holding any one ring there brought it under 0.4 %, so the cause was that all three angular rings (4, 5, 6) changed shape in the same pair. (2) The innermost ring now holds its glyphs two frames longer (it starts at k0+14) and runs squash → slide → closing → ring, ending on the same frame k0+17. **Every W1 pair, F118–152, is now within ±1 %; the worst is F135→136 at 0.81 %.** The bar is asserted for all three windows, hybrid pairs included. | `switch._segs_close`, `switch.ring_stage`, `assembly-fixtures.json` |
| note's sound claim | the note now says "trimmed, faded and levelled", and credits[1] records the fade. | notes, credits |

**Protected and unchanged:** the outer-first W1 metamorphosis (still 18 distinct single-state hybrid states; F134 = ring, ring, closing, slide, squashed, glyph, glyph); the engraved cream ring stock with real grooves; the neutral sphere-lit text plates with embossed white capitals; the GrabCut key cutouts; the three bell strikes on exact cues over digital silence, plus the silent variant; the integer 1280-tick clock; the byte-identical F360 still (1.5 s) and the three-frame strip; grain off, with field L 2 and σ 0; reference images used only on the outside comparison sheets.

## Evidence IDs

| ID | item | kind | record |
|---|---|---|---|
| E-K0 | `File:Skeleton_key_(Yale_&_Towne).png`, Noy-nac, CC BY-SA 4.0 | FORAGED (Commons), then adapted: GrabCut cutout, recoloured, arranged on rings; the adaptation is shared under CC BY-SA 4.0 | credits[0], optics-ledger.json (extmetadata 2026-11-17) |
| E-BELL | `File:Striking_a_bell_15cm_large.ogg`, stephan via pdsounds.org, public domain | FORAGED sound (Wikimedia mp3 transcode, decoded with ffmpeg, trimmed, faded and levelled) | credits[1], sound-ledger.json, switch/bell.wav |
| H-T1 | « LA PORTE TOURNE SUR LE GOND · LE GOND TOURNE SUR LA PORTE » | HANDMADE (original; checked against Duchamp's ten disc texts) | glyphpaths.json, glyphs.py |
| H-T2 | « LA CLOCHE DU QUAI SONNE LA CLEF · LA CLEF DU QUAI SONNE LA CLOCHE » | HANDMADE | glyphpaths.json, glyphs.py |
| H-TYPE | Liberation Sans Bold capitals, SIL OFL 1.1 (system font), filled with the groove stock | HANDMADE setting of an openly licensed typeface | glyphs.py |
| H-OA | engraved eccentric ring disc: 7 rings and a core, groove pitch 2.5 px at 1× | HANDMADE procedural | optics.py, optics-ledger.json → rings |
| H-OB | key-ring layout: 6 eccentric rings, 69 slots (all K0, mirrored on rings 1, 3, 5), guide grooves | HANDMADE layout of E-K0 | optics.py → key_slots |
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
| 11.00–12.00 | 264–287 | T2, ω easing from fast to reading speed | 1/80→1/256 | silence | H-T2 |
| 12.00–17.75 | 288–425 | **T2 declared reading interval**, first letter phase-locked to 12 o'clock at F288 | **1/256** (0.09375 rev/s), constant | silence | H-T2, F-I2 |
| 17.75–18.50 | 426–443 | **W3** T2→O_B: 69 token runs swapped in token order for real key cutouts, which slide into their slots; the black card and guide grooves arrive ring by ring | 1/256, constant | bell at 17.75 s | H-SUB, E-K0, E-BELL |
| 18.50–21.50 | 444–515 | **O_B** key rings, gain 1.0→0.7, concave plate (intended to recede); ω eases back to 1/80 over F444–467 | 1/256→1/80 | silence | H-OB, E-K0 |
| 21.50–23.00 | 516–551 | still pass 1: F360 frozen, byte-identical to the moving frame (asserted) | 0 (static) | silence | F-still |
| 23.00–24.00 | 552–575 | still pass 2: F360, F361 and F362 as a plain strip | 0 (static) | silence | glyphpaths.json still_pass |

## Fixtures asserted before encoding (assembly-fixtures.json, film variant)

- **I3 alternation.** The bodies run T1, O_A, T2, O_B. The test score T1, O_A, O_B, T2 fails as required, and each window belongs to its incoming disc. *Structural.*
- **I4 constant ω.** The declared ω is exact on integer ticks (W1, W2: 16/1280; W3: 5/1280). Measured on the rendered frames by polar phase correlation and a rotation-SSD search, with **every pair asserted within ±1 %** and no pause:
  - W1 (F118–152, 4.5°): worst pair F135→136 at 0.81 %, aggregate 0.06 %;
  - W2 (F238–272): worst 0.13 %;
  - W3 (F418–452, 1.40625°): worst 0.27 %.
  *Measured.*
- **I5 periodicity.** P = 80 at 0.30 rev/s and P = 256 at 0.09375 rev/s, exact in integer ticks (16×80 = 5×256 = 1280). θ(k+80) ≡ θ(k) is checked on every held 1/80 stretch of the score. No 256-frame stretch at 1/256 exists in a 24 s film (the 1/256 run is F288–444, 157 frames), so P = 256 is asserted on the fixed clock. *Structural.*
- **I2 glyph order.** T1 at F100 and T2 at F360 read in token order under both cw and ccw; W1 and W2 are monotone; the W3 swaps happen in token order. *Structural.*
- **Per-mark single state.** Film ghost overlap peaks at 0.15 %, against 9.6 % for B2. W1 shows 18 distinct hybrid states. *Measured and structural.*
- **Replay.** The F126–143 sha1 hashes are identical in a fresh process. *Measured.*
- **Still pass.** Part 1 (F516–551, 1.5 s) equals F360 pixel for pixel. *Measured.*
- **Credits match the bar.** The credits list exactly the K0 key and the bell; every key slot is K0. *Structural.*
- **Black field.** Corner L 2.0, σ 0.0. *Measured.*
- **I8 luminance step.** The largest step over F24–515 is 10.9 % (F428, W3), under the 25 % limit. The cuts at F516 and F552 into and inside the still pass remain the declared exception (a ramp would break the byte-identical F360). *Measured.*

U3's own `fixtures.json` was re-run on the same score and frames: I3, I4 (now with the ±1 % every-pair criterion), I5, I2, single state, replay, W1 beat states and sound all pass.

## Credits against the bar

The film shows exactly two foraged items, both verified from Commons extmetadata on 2026-11-17, as the bar requires:
- the key K0, `File:Skeleton_key_(Yale_&_Towne).png`, Noy-nac, CC BY-SA 4.0, adapted, with the adaptation shared under CC BY-SA 4.0;
- the bell, `File:Striking_a_bell_15cm_large.ogg`, stephan via pdsounds.org, PD.

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
| playable sequence | assets/films/anemic-cinema.mp4 | 5c743f077633 |
| silent version and the two baselines | editor/anemic-cinema-{silent,B1,B2}.mp4 | aa0062e31e5c / a83e4631b571 / 7f8a50c935c1 |
| procedural disc source | optics.py · glyphs.py · switch.py | 850567a546ac · ac7f12d6d8c1 · bd2a548a9f4a |
| glyph mapping | glyphpaths.json | cee5625c2a64 |
| exposure and phase score | score.json | 6c0f99f4b03d |
| unit fixtures (re-run on the final score) | fixtures.json | (this round) |
| still / reduced-motion view | film 21.5–24.0 s; films/stills/anemic-cinema/ | (in the film) |
| assembly | films/anemic-cinema.py | 3f0a98bc4800 |
| credits | films/credits/anemic-cinema.json (E-K0, E-BELL) | 3b57ec71591e |
| perceptual review | **still to be done by a viewer with real-time playback** (protocol below) | – |

## Claim graph (claim → evidence → label)

- "One disc changing, not a cut" → H-SUB, F-I4, F-single-state, B1/B2 variants → measured plus structural; **the perceptual judgement is unknown**.
- "The ground transforms with the marks" → `switch.plate_front`; check visually at F128, F132, F136 and F252 → structural.
- "Constant speed through the switches" → I4 → measured: **every pair within ±1 %** in W1, W2 and W3 (worst 0.81 %); declared ω exact → measured plus structural.
- "Periodicity at 0.30 and 0.09375 rev/s" → I5 → structural (P = 80, P = 256 exact in integer ticks).
- "O_A approaches, O_B recedes" → optics depth clips and the gain profiles → **unknown** (no real-time viewing).
- "T2 legible at 0.09375 rev/s" → U2's reading model (glyphpaths.json `reading_speed`) → **model says the reader is fed the text slowly at 12 o'clock and must follow it into the inverted sector; no live read-aloud yet**. The F360 still (1.5 s) and the strip are the static reading.
- "The still pass shows the same layout" → F-still → measured.
- "Only the bar's foraged items" → credits assert, key slots all K0 → structural; licences from extmetadata → verified.
- "The material is honest" → credits with the ShareAlike notice, kit grain off, field σ 0 → measured and structural.

### Perceptual protocol still owed (real-time playback, 960×540, normal speed)
1. Watch O_A (6.0–10.25 s) and O_B (18.5–21.5 s), and record the apparent depth direction of each disc: toward the eye, away, or bistable.
2. If O_A reads as receding or bistable, reverse `optics.ECC`'s sign order or raise the gain end-point, keeping ω fixed. If O_B is weak, steepen `key_ring_set` b from 1.0→0.80 to 1.0→0.65.
3. Read T2 aloud over 12.0–17.75 s at 0.09375 rev/s, and note where the place is lost (the likely spots: the inner turn around « CLOCHE », and the « QUAI | SONNE » wrap).
4. Watch W1 next to B1 and B2.

## Known weaknesses

1. **Depth is unverified by viewing.** Stereokinetic depth can flip sign. No real-time viewer has confirmed either disc.
2. **Legibility at the bar's speed is the main risk.** At 1/256 over 5.75 s, U2's model loses a 13-character-per-second reader in the second half (15–19 letters pass upside down), and a 10-character-per-second reader needs 6.5 s for the 65-character pun. The speed is fixed by the bar, so it is not changed here; the frozen F360 is the fallback reading. No live read-aloud has been done.
3. **The SONNE / QUAI radial stacking** on adjacent turns is only reduced (to 8°), because it is inherent in the chiastic text.
4. **The innermost ring's metamorphosis is shorter** (4 steps, no dash-at-glyph stage) because it holds its glyphs 2 frames longer to keep W1 within ±1 %. A small pop remains at F141–142, where the core appears in two steps.
5. **The odd key rings repeat K0 mirrored**, so O_B has less variety than with two keys.
6. **Still-pass cuts** (+190 % and −66 % steps) are an accepted exception to I8. The still is exactly 1.5 s, which meets the bar's minimum.
7. **The title** is a quiet L≈140 line, so the film opens nearly dark for 1 s.
8. **The warm cast** on the optical discs is a global RGB gain (grade), not a property of the material.

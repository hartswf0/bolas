# Anémic cinéma: swarm plan (director)

Direction: **2 "Le cerne se délie"** is the spine (proposals/kf-2.png). **3 "Anneaux de clefs"** (kf-3.png) supplies the second optical disc. I have not drifted from that direction. One correction to the proposal is needed: the test shot was phrased as "pun disc → ring disc → key-ring disc". Two optical discs in a row would fail the strict-alternation fixture (section 7), so the reading disc sits between them: **T1 → O_A → T2 → O_B**. The defining switch, T1 unbinding into O_A, keeps exactly the form the user chose.

Revision base: prompts/anemic-cinema.md as read on 2026-11-16, proposals/kf.py, and the sources already in films/sources/anemic-cinema/. The previous films/anemic-cinema.py is superseded. Its notes file says "all drawn and synthesized in code", and that will be rewritten.

---

## 1 · Creative thesis

One flat, constantly turning plate trains two acts of attention.
- **Depth:** the eye falls into eccentric rings.
- **Reading:** the eye chases a sentence round the same surface.

The film's event is the hand-over itself. The plate does not stop and the speed does not change. Only the *kind* of mark changes, drawing by drawing. Letters break into dashes, the dashes slide onto eccentric circles, and the circles close into grooved rings. When this works, the viewer feels their gaze being re-tasked rather than the picture being cut. Later, the same trick runs the other way: the letters of the reading sentence become real keys, and the key rings sink away.

The result would be **bland** if any of these happened:
- a cut or cross-dissolve between discs;
- the speed changing at the switch;
- rings that read as flat targets with no depth;
- a spiral that cannot be read at its chosen speed.

## 2 · Defining beat and comparison baseline

**Defining beat:** the switch W1, frames 126–143 (5.25–6.00 s). The spinning pun disc T1 unbinds into the engraved ring disc O_A at a constant 0.30 rev/s (1/80 rev per frame).

What the viewer should be able to point to:
- (a) a held frame around F134 that shows outer turns already closed as rings, one turn in dashes, and the inner turns still letters;
- (b) the rotation visibly continuing through every one of the 18 frames;
- (c) after the switch, the rings that were read a moment earlier now pull the eye inward or outward.

**Baseline (control), rendered from the same code by a flag:**
- **B1 "cut":** identical discs and ω, with W1 replaced by a hard cut at F126.
- **B2 "dissolve":** an 18-frame cross-dissolve T1→O_A at the same ω.

The beat succeeds if, side by side, viewers describe the main film as *one disc changing* and B1/B2 as *two discs*. The independent reviewer records this.

## 3 · Lineage Genome (compact)

| field | value |
|---|---|
| source | *Anémic cinéma*, Duchamp with Man Ray and Marc Allégret, 1926: 35 mm silent film, about 7 min, alternating rotating optical discs (nested eccentric rings) with discs carrying spiral French puns (MoMA, Centre Pompidou) |
| target | 24.0 s, 960×540, 24 fps, mp4 with sound. Procedural engraved discs, original French puns, real foraged key photographs cut out with GrabCut, a foraged real bell recording |
| preserved relation | alternation of a *depth* disc and a *reading* disc on one flat plane turning about a fixed centre, seen by a fixed camera |
| optics change | the cards are not photographed: a fixed virtual camera with a 180° shutter (8 sub-frames, real temporal integration) and 2× area supersampling. Softness comes from motion integration and resampling, not from an added filter |
| formalism change | integer frame clock; ω chosen with integer periods (80 and 256 frames per revolution); GlyphPath as data; the ExposureSequence as a score with fixtures |
| concept change | in 1926 the discs were joined by cuts (I believe so; *uncertain*, not verified frame by frame). Here the **switch is the event**, done by drawing substitution |
| sound change | the original was silent. Here a real bell strike cues each switch as a *declared contemporary intervention*, with declared silence elsewhere, plus a fully silent variant (section 8) |

**Formation epochs (weight 0–100):**
- Duchamp's optical machines, 1920–35 (Rotary Glass Plates, Rotary Demisphere, Anémic cinéma, Rotoreliefs): **95**. This is the direct source of the disc and the alternation.
- Rrose Sélavy wordplay and Dada/Surrealist puns, 1920s (Desnos): **70**. The text discs are puns, and ours must be original.
- The stereokinetic effect in perception research (Benussi/Musatti, about 1924; later kinetic-depth work by Wallach and O'Connell, 1953): **70**. This is why eccentric rings seem to have depth. *The exact dates and how much Duchamp knew of it are uncertain.*
- Visual music and computed harmonic motion (Whitney, 1960s–70s): **45**. It gives the inspectable ω curves and integer periods.
- Oulipo constraint, 1960 onward: **50**. The chiasmus pun is a self-imposed constraint: the second half permutes the first.
- Kinetic typography (title design, concrete poetry): **35**.
- Contemporary procedural rendering: **55**. It is the means: deterministic, replayable and testable.

**Uncertain claims recorded as such:**
- the original rotation speeds;
- whether the original used any transitions;
- the division of labour between Man Ray and Allégret.

None of these is used as a fact in the film.

## 4 · Olog and the central operation

**Types:**
- `Disc` = {id, kind ∈ {optical, text}, radius_px, source ∈ {procedural, glyph-layout, foraged-cutout}, dir = −1 (ccw on screen), ω: FrameIndex → rev/frame}
- `Token` = a character of a Pun with an index i
- `GlyphPath`: Token i ↦ (r_i, φ_i, tangent_i, turn_i), with φ increasing clockwise and r decreasing (inward spiral, letter tops facing out)
- `RingSet`: k ↦ (r_k, cx_k, cy_k, width_k, groove_pitch)
- `ExposureSequence`: FrameIndex (int) ↦ (disc_id, θ_k, state ∈ {body, switch})
- `project`: PlanarMark × θ ↦ pixels. It rotates rigidly about (480, 270) in a fixed view, with no 3D.
- `Substitute`: (D_from, D_to, window [k0, k0+18), ω) ↦ 18 hybrid frames. **This is the central operation.**

**Arrows:**
- `θ_{k+1} = θ_k + 2π·dir·ω(k)`, which is one rotation for the whole film. Every disc reads θ from the shared plate.
- `turn_i`: Token → ring k (the correspondence used by Substitute)
- `exposure(k).disc.kind` alternates between consecutive bodies.

**Preconditions of Substitute (typed, all checked by asserts):**
1. `kind(D_from) ≠ kind(D_to)`.
2. `ω(k)` is constant over the whole window, including k0−1 and k0+18, and is equal for both discs: the same value, not merely close.
3. Both discs share the centre (480, 270) and θ_k. There is one plate.
4. There is a correspondence c: glyph runs → rings that is order-preserving. Turn j of the spiral maps to ring j from outside in, and glyph i's arc lies in ring c(i)'s radial band after the radial slide, within ±1 band-width (a Sutherland constraint).
5. Window length ≥ 12 frames (18 is used), with a per-ring stagger of 2 frames.
6. At every frame, each mark is in exactly one state (glyph, dash or ring segment). There is no per-pixel blending between the two discs beyond antialiasing.

**Observable consequences:**
- The rotation never pauses. The measured per-frame angle step equals 2π/80 through F125–F144 (by polar phase-correlation of rendered frames, ±1 %).
- Hybrid frames show turns in mixed states, outer first.
- Ring count rises 0→7 monotonically and glyph count falls len(pun)→0 monotonically.
- No frame contains a full T1 and a full O_A superimposed.
- The ExposureSequence assigns the window to the incoming disc.

**Counterexample (must fail the fixtures):**
- An 18-frame cross-dissolve T1→O_A at the same 1/80 rev/frame. It meets preconditions 1–3 but breaks 6: ghost letters overlie whole rings, and mid-window pixels show 50 % blends. It reads as two discs. This is baseline B2.
- A second counterexample: substitution where O_A enters at 0.50 rev/s. It breaks 2, and the switch reads as a cut.

**Equivalence and divergence of replay and alternate views:**
- **Replay:** deterministic (seeded, integer clock), so two renders are byte-identical per frame (sha1 of frames is equivalent).
- **cw vs ccw:** GlyphPath order is equivalent. Apparent depth may diverge, because depth sign is bistable and is tested, not assumed.
- **Still pass vs moving:** the layout is equivalent (same GlyphPath, same pixels at the chosen θ), but legibility diverges. That divergence is what the still pass shows.
- **100× crop:** groove aliasing diverges by speed and is measured.
- **Half-size viewing:** grooves vanish, so judge at the intended 960×540.

Not interactive: invitation, actions and the rest are N/A. The reduced-motion view is the still pass, plus `stills/` frames.

## 5 · Invariants

- **I1 Flat plane:** all marks are planar and transform only by rigid rotation θ about (480, 270). There is no perspective, scaling of the plate, or 3D. (Radial slides inside Substitute are planar redrawings, not camera moves.)
- **I2 Glyph order:** GlyphPath order equals token order of the pun string, under both cw and ccw rotation, and at every frame where glyphs exist.
- **I3 Strict alternation:** disc bodies follow T, O, T, O. Two consecutive bodies of the same kind fail. Switch windows belong to the incoming disc.
- **I4 Constant speed at switches:** ω is identical across each switch window.
- **I5 Periodicity:** at a fixed ω, θ(k+P) ≡ θ(k) mod 2π, with P = 80 frames (0.30 rev/s) and P = 256 frames (0.09375 rev/s). Asserted exactly in integer arithmetic.
- **I6 Legibility of kinds:** every body frame is classifiable as ring or text at a glance. Only the 18-frame windows are hybrid.
- **I7 Honest material:**
  - kit grain is disabled (`ink._grain = False`);
  - no vignette, faux scratches, dust, sprockets, flicker or gate weave in the motion picture;
  - every foraged item is credited with a verified licence;
  - no Duchamp pixels and no reference pixels.
- **I8 Safe playback:** no strobing faster than the bell cues, and the luminance change between frames stays under 25 % of the frame mean, except at the title in and out.

## 6 · Exposure / phase score: timed shot list (Hard proof, 24.0 s, 576 frames at 24 fps)

ω_fast = 1/80 rev/frame (0.30 rev/s); ω_read = 1/256 rev/frame (0.09375 rev/s). All rotation is counter-clockwise on screen.

| # | frames | time (s) | on screen | ω | heard | material |
|---|---|---|---|---|---|---|
| 0 | 0–23 | 0.00–1.00 | black field. Small title "anémic cinéma · variation" in the cream ring stock, fading in and out over 6 frames each | – | silence (declared) | HANDMADE type |
| 1 | 24–125 | 1.00–5.25 | **T1**, the pun disc: sphere-lit grey plate, bright cream capitals cut from the groove stock, inward clockwise spiral with tops out and open spacing (pitch ≥ 1.6× cap height) | ω_fast | silence | HANDMADE (procedural plate plus original pun T1) |
| W1 | 126–143 | 5.25–6.00 | **Switch T1→O_A, the defining beat**, drawing substitution outside-in. For ring k (k=0..6), starting at F126+2k, over 6 frames: glyph → glyph shrinks to a dash of its own arc length (2 f) → dash slides radially onto ring k's eccentric circle (2 f) → dashes close into a continuous grooved ring (2 f) | ω_fast, constant | **bell strike at F126** (foraged), decaying under the window | HANDMADE + FORAGED sound |
| 2 | 144–245 | 6.00–10.25 | **O_A**, the engraved ring disc: 7 nested eccentric cream rings with fine grooves on the lit plate, gaps the same width as the rings, as in the reference. It **expands toward the eye**: ring centres walk outward with radius, the innermost ring brightest, and the eccentric gain rises 0.7→1.0 over the shot. The plate is lit as convex (key light upper left) | ω_fast | silence | HANDMADE |
| W2 | 246–263 | 10.25–11.00 | Switch O_A→T2: the reverse substitution (ring → dashes → glyphs of T2, outside-in) | ω_fast, constant | bell strike at F246 | HANDMADE + FORAGED sound |
| 3 | 264–425 | 11.00–17.75 | **T2, the reading disc**. ω eases ω_fast → ω_read over F264–287. **Declared reading interval F288–425 (5.75 s) at a constant ω_read.** The pun is about keys and bells, and the 12 o'clock point feeds the reading order | ω_fast→ω_read, then constant | silence | HANDMADE (original pun T2) |
| W3 | 426–443 | 17.75–18.50 | Switch T2→O_B: each glyph of T2 is swapped, in token order and outside-in, for a **real key cutout** of its arc length. The keys then slide into tangential bow-to-bit chains on 6 eccentric rings | ω_read, constant | bell strike at F426 | FORAGED keys (GrabCut) + HANDMADE layout |
| 4 | 444–515 | 18.50–21.50 | **O_B**, the key-ring disc: 6 tight eccentric rings of keys over faint engraved guide grooves on a black-card plate. It **recedes**: the offset order is reversed (innermost ring trails away), inner rings are smaller and darker, the eccentric gain falls 1.0→0.7, and the plate is lit as concave (key light lower right). ω eases ω_read→ω_fast over F444–467, then holds | ω_read→ω_fast | silence | FORAGED + HANDMADE |
| 5 | 516–551 | 21.50–23.00 | **Still pass**, part 1: the T2 frame F360 frozen at full size. It shows the same pixels as in motion | 0 | silence | (from shot 3) |
| 5b | 552–575 | 23.00–24.00 | Still pass, part 2: three consecutive T2 frames (F360–362) stacked as a plain vertical strip on black, each about 175 px tall. These are real frames: no sprocket holes, no edge printing | 0 | silence, ending in a final bell decay tail from F426, already gone | (from shot 3) |

Sound totals:
- three real bell strikes, each decaying in about 1.2 s and peaking at −14 dBFS or below;
- everything else is digital silence, declared in the notes;
- **variant S0:** the fully silent render (`--silent`), kept for the section 8 comparison.

## 7 · Elements: FORAGED vs HANDMADE

- **HANDMADE: engraved ring disc O_A.** Procedural: 7 eccentric rings and a central grooved core, with ring widths about equal to the gaps and a groove pitch of about 3 px at 2× render. The groove stock is a cream band modulated by `cos(2π d / pitch)`, with the sphere-lit plate under it. Source: `optics.py`.
- **HANDMADE: text discs T1 and T2.** Two original French puns (chiasmus constraint, about 45–70 characters each) written by the language unit. They must not be Duchamp's, and they are checked against the known list of Duchamp's disc texts. The letters are rasterised from LiberationSans-Bold and filled with the *same groove stock* as the rings, so letters and rings are visibly one material. Source: `glyphs.py`, with `glyphpaths.json`.
- **FORAGED: skeleton key.** `File:Skeleton_key_(Yale_&_Towne).png`, Wikimedia Commons, by Noy-nac, **CC BY-SA 4.0**, read from extmetadata on 2026-11-16 (LicenseShortName "CC BY-SA 4.0", "Own work", 2816×1024). It is already in sources as key_yale_towne_1280.png.
  - Optional: a second, different key (PD/CC0 photograph on Commons or LoC "No known restrictions") for variety in the inner rings.
  - Cut out with real `cv2.grabCut` and exported as RGBA plus failure masks.
- **FORAGED: bell strike.** A real recording of a single bell (handbell, station or school bell, ship's bell) on Commons, licensed PD, CC0, CC BY or CC BY-SA. Alternatively, a bell heard in a Moving Image Archive clip with source sound (search `bell|station|school|church|ring`), cut to one clean strike. It is decoded with ffmpeg to wav and only trimmed and levelled.
- **Moving Image Archive footage:** **not used on screen**. Reason: the proof calls for made objects (discs), and the proposal search turned up nothing round, frontal and B&W enough. The only role for the cache is the bell sound, if Commons fails.
- **Previously foraged, rejected:** cp_pour_*.png (*Command Performance*, 1942; licence unverified). It must not appear.

## 8 · Animation technique SCIONs (from swarms.json, prompts read in full)

1. **#6 John Whitney: Harmonic Motion Orchestra.** It carries the plate's single θ clock, the ω curves with integer periods (80/256 frames), the eccentric-gain envelopes that produce approach (O_A) and recession (O_B), and the per-ring phase offsets.
   - From its method: a **parametric score** (`score.json`) and a **phase visualizer** (a strip plot of θ, ω and ring gain per frame). Its "A/B rational lock against detuned drift" becomes a comparison of O_A with locked ring phases versus O_A with a 2 % detuned ring orbit, judged for depth.
   - Numerical invariant: I5 periodicity. Viewing judgement: does O_A pulse toward the eye?
   - Shots: all; W1–W3 hold ω.
2. **#7 Peter Foldès: Drawn Metamorphosis.** It carries the switches: key contours (glyph, dash, ring segment, key), point correspondences (glyph i ↔ arc on ring c(i)), in-between fields (shrink, radial slide, close), transformation pacing (2-frame stagger, 6 frames per ring), discontinuity markers (the substitution frame where a dash becomes a key), and hand-authored exception frames wherever interpolation looks bad.
   - Its bar: the transformation reads in greyscale, there are no unintended topology flips, and key recognitions hold at the planned frames.
   - Its inquiry, "geometric interpolation vs discontinuous substitution", is run as a comparison on W1.
   - Shots: W1, W2, W3.
3. **#29 GrabCut: Cutout Extraction Swarm.** It carries the real keys: a mask-seeded graph cut (luminance seeds, border as definite background), keeping the largest component, with **no background islands**, **bit teeth and the bow's hole retained**, and residual halos isolated. It exports RGBA pieces, the contour mask and a failure-mask overlay, with original-coordinate transforms recorded in a manifest.
   - Shots: W3 and O_B.

Considered and not chosen:
- #39 Drawing Substitution, because Foldès covers discrete swaps plus in-betweens and #39 is about multiview turns;
- #44 Multiplane, because it would break the flat-plane invariant;
- #8 Sutherland, whose constraint is kept as precondition 4 without adopting the whole swarm.

## 9 · AESTHETIC TARGET (from catalogue/cinema.json: spiralTextPom.webp [Centre Pompidou], duchamp2.webp [MoMA])

These were sampled with PIL on 2026-11-16.

**spiralTextPom.webp (text disc reference):**
- **Medium:** a monochrome 35 mm print, three successive frames on the strip. **Neutral grey**: R=G=B in every luminance band.
- **Field:** pure black (L≈2, noise σ≈0).
- **Plate:** a sphere-lit grey disc, lit from the top and upper left. The ramp runs from L 214 at the top and 200 at the upper left, through 142 at the centre, to 78 at the lower right and 62 at the bottom.
- **Letters:** near white (L 230–249, band mean (230, 233, 232)), bold rounded sans capitals with soft edges and a slight bloom. They look raised, like embossed card lit from above.
- **Layout:** the text runs clockwise in an inward spiral of about 3 turns, with tops facing out.
- **Framing:** the disc fills about 94 % of the frame height.

**duchamp2.webp (optical disc reference):**
- **Medium:** a photograph of a printed or painted disc, with a **warm** cast.
- **Field:** very dark warm (22, 22, 19).
- **Rings:** cream-grey with a core of (131, 124, 111), so R−B ≈ 20. The band mean for L 90–160 is (126, 121, 108).
- **Gaps:** black, (29, 29, 24) between rings. The rings are about as wide as the gaps (row 256 scan: alternating runs of about 16 px rings and 16 px gaps at 460 px).
- **Grooves:** fine concentric grooves are visible inside each ring.
- **Geometry:** the rings are eccentric. Their centres drift horizontally, so the gaps are thinner on one side.
- **Framing:** the disc is about 71 % of the frame height, centred, with matte, soft light.

**Rhythm (both):** one centred disc, slow, steady turning, nothing else in frame.

**Our target:**
- **Format:** 960×540 on a black field. Disc radius 232 px (diameter about 86 % of H), centred.
- **Text discs (T1, T2):**
  - neutral grey plate, |R−B| ≤ 4;
  - light from the upper left, ramp L ≈ 210 → 60;
  - letters L ≥ 225, slightly embossed (a 1–2 px shadow cast down and right, from the same light);
  - bold sans capitals with tops out, inward clockwise spiral;
  - **more spacing than the reference** (direction 3 instruction): tracking +15 % and turn pitch ≥ 1.6× cap height. The kf-2 crowding at 44 px pitch / 30 px type is to be opened by at least 15 %.
- **Optical discs:**
  - O_A: rings in the warm cream band, L 110–140 with R−B 12–25, on a plate kept dark (L 30–60) so the rings dominate as in duchamp2; ring width ≈ gap width; grooves resolved at 1:1.
  - O_B: real keys printed into the same warm cream range, with faint engraved guide grooves under each chain.
- **Softness ("1926 film-strip softness"):** reached by **real technique**:
  - 2× supersampled area rendering;
  - a 180° shutter integrating 8 sub-frames of the actual rotation (motion blur arises only where the plate actually moves fast);
  - letter bloom computed from the same light model.

  **Kit grain is off; no added grain, noise, sprockets or vignette.** Grading only unifies: the warm cast is applied to the optical discs, and the text discs stay neutral, as in their respective references.
- **Typography:** title in small cream caps; no subtitles.
- **Pacing:** long steady bodies of 3–7 s and brief 0.75 s switches.

## 10 · Swarm units (3; the editor/assembler and the independent reviewer run separately)

Shared field contract, for all units:
- canvas 960×540, centre (480, 270), plate radius R = 232;
- render at 2× (1920×1080 internal, R = 464) and downsample with INTER_AREA;
- θ in radians, counter-clockwise positive on screen; θ comes from `score.json` only;
- each unit writes an importable, deterministic Python module (`python3 -I`, absolute paths, seed 1926) to the workspace, and media to `films/sources/anemic-cinema/<role>/`;
- every renderer returns float32 L (0–255) plus alpha at 2× size, with a tint tag ("warm" or "neutral").

### U1 Optical designer and key cutter (optics)
- **Owns:** O_A procedural engraved ring disc; GrabCut key cutout(s); O_B key-ring disc; the depth tuning.
- **Reads:** the #6 and #29 prompts.
- **Writes:**
  - `films/swarm/anemic-cinema/optics.py` with `ring_set(gain)`, `render_rings(theta, gain, ring_mask=None)`, `ring_segment_mask(k, a0, a1)`, `key_sprite(i)`, `render_keys(theta, gain, placed=None)` and `key_slots()`. `key_slots()` returns the ordered tangential slots for W3.
  - **Ledger:** `films/swarm/anemic-cinema/optics-ledger.json`: ring geometry, groove pitch, the GrabCut manifest (source file, licence verified from extmetadata, crop transform, mask stats: island count = 0, teeth retained) and depth tests.
  - **Depth tests:** two motion profiles per disc (offset gain rising vs falling; locked vs 2 % detuned) rendered as 4 s test clips at ω_fast, plus a 100× crop aliasing measurement of the grooves at ω_fast and ω_read. Record the chosen profile with the reason.
  - **Media:** `films/sources/anemic-cinema/optics/` holds the key RGBA, mask, failure overlay, test clips and frames compared beside duchamp2.
- **Budget:** about 45 min, under 20 MB downloads.
- **Acceptance:**
  - an O_A frame beside duchamp2 meets the section 9 numbers;
  - the key matte has no islands and keeps its teeth;
  - O_B reads as rings of keys, not scattered keys.

### U2 Language agent and glyph layout (language)
- **Owns:** the two original French puns and the text discs T1 and T2.
- **Reads:** the #7 prompt (for the correspondence with rings).
- **The puns:**
  - Both use the chiasmus constraint.
  - T1 is the door pun. kf-2's « LA PORTE DE SERVICE NE REND PAS SERVICE · LE SERVICE DE LA PORTE NE REND PAS LA PORTE » may be kept or improved.
  - T2 is about the key and the bell, from the station seed.
  - Neither may be Duchamp's.
  - Write an English gloss of each for the notes.
- **The layout:**
  - GlyphPath with turn spacing opened by at least 15 % against kf-2;
  - an exact correspondence of spiral turns to O_A's 7 rings (turn j ↔ ring j, glyph arcs within ring bands after the slide);
  - per-glyph sprites for substitution.
- **Reading speed:** choose and justify it (section 8 repair). Compare ω_read = 1/256 with a slower 1/384 rev/frame and with a longer exposure at 1/256. Read each at intended size and record at what point the reading position is lost.
- **Writes:**
  - `films/swarm/anemic-cinema/glyphs.py` with `glyph_path(pun)`, `render_text(pun, theta, visible=None)` and `glyph_sprite(pun, i)`;
  - `films/swarm/anemic-cinema/glyphpaths.json`, with each pun's tokens, (r, φ, tangent, turn) per glyph, the ring correspondence and fixture results for cw/ccw order;
  - the still-pass layout spec;
  - media in `films/sources/anemic-cinema/language/`: reading tests and T2 frames compared beside spiralTextPom.
- **Budget:** about 45 min, no downloads.

### U3 Switch animator, timing verifier and sound (switch)
- **Owns:**
  - `score.json`, the ExposureSequence: per frame k, the disc, θ_k, ω_k, state, gain and the substitution stage per ring/glyph;
  - **Substitute**, the three drawing-substitution windows W1–W3, built frame by frame on top of U1 and U2's modules;
  - the fixtures:
    - I3 alternation;
    - I4 constant ω across windows, both declared and *measured* from rendered frames by polar phase correlation;
    - I5 exact periodicity;
    - I2 order;
    - the per-mark single-state check, which must fail on B2;
    - replay hash;
  - baselines B1 (cut) and B2 (dissolve);
  - the bell foraging, from Commons first and the MIA cache as fallback.
- **Writes:**
  - `films/swarm/anemic-cinema/switch.py`;
  - `films/swarm/anemic-cinema/score.json`;
  - `films/swarm/anemic-cinema/fixtures.json` (each test with pass/fail and evidence label);
  - `films/swarm/anemic-cinema/test-shot.mp4` (F100–F270 plus W3–O_B: the TEST SHOT, the pun disc unbinding into rings at constant speed, then T2→O_B receding, rendered with the bell) and `baselines/B1.mp4`, `B2.mp4`;
  - `films/swarm/anemic-cinema/sound-ledger.json` (bell source, licence from extmetadata or the archive page, trim points; cue frames 126/246/426);
  - media in `films/sources/anemic-cinema/switch/`: bell.wav, W1 frame strip (18 frames contact sheet), phase visualizer plot.
- **Credits:** append the key and bell entries to `films/credits/anemic-cinema.json`, replacing the stale file content with only verified items.
- **Budget:** about 45 min, bell download under 10 MB.

**Dependencies:**
- U1 and U2 work in parallel against the shared field contract. Their only coupling is the ring radii, which U1 publishes first in `optics-ledger.json` → `rings`. U2 reads them to set spiral turn radii, so the order is ring geometry, then glyph layout.
- U3 consumes both. U3 may stub with kf.py's functions until they land.
- The editor then writes `films/anemic-cinema.py`, which imports the three modules, uses kit `Film` at 960×540 with `ink._grain = False`, and adds the bell via `mix.add`. It also renders the silent variant and rewrites `films/notes/anemic-cinema.txt`.

## 11 · Acceptance bar (falsifiable; for the fresh critic)

1. **Structure and material:** the rendered film lasts 18–25 s (target 24.0).
   - `score.json` lists disc bodies T1, O_A, T2, O_B, so there are two original optical and two original text discs.
   - The alternation fixture passes on it, and fails on a test score with O_A, O_B adjacent.
   - `films/credits/anemic-cinema.json` lists every foraged item (key CC BY-SA 4.0 by Noy-nac, the bell with a verified licence) and nothing else.
   - The puns are not Duchamp's.
   - *Evidence label: structurally verified.*
2. **The switch is one disc changing:**
   - Frames F126–143 show at least 6 distinct hybrid states in which some turns are letters, one is in dashes and some are rings, outer first.
   - Measured rotation per frame through F120–F150 is 4.5° ±1 % (ω_fast), with no pause.
   - The per-mark single-state check passes on the film and fails on B2.
   - Watching the film beside B1/B2, the critic can name W1 as a transformation, not a cut or dissolve.
   - *Measured, and perceptually judged.*
3. **Periodicity and order:**
   - θ(k+80) ≡ θ(k) and θ(k+256) ≡ θ(k) (mod 2π), asserted exactly at a fixed ω.
   - Reading T2's still frame (F360) along the spiral from outer to inner reproduces the T2 pun string exactly, character for character.
   - GlyphPath order equals token order under both cw and ccw.
   - *Measured, and structurally verified.*
4. **Depth:** at intended size and speed, the critic reports O_A (6.0–10.25 s) appearing to push toward the eye and O_B (18.5–21.5 s) appearing to recede, or records exactly where either fails. *Perceptually judged; a failure triggers the section 8 repair, holding speed and changing offset or spacing.*
5. **Legibility:**
   - The critic can read the whole T2 pun aloud during the declared reading interval (12.0–17.75 s, F288–425) at normal playback, and states where, if anywhere, they lost their place.
   - The still pass (21.5–24.0 s) shows the identical layout frozen for at least 1.5 s.
   - *Perceptually judged.*
6. **Aesthetic A, side by side with duchamp2.webp.** Measured on the frame at 8.0 s beside the reference:
   - field corners have L ≤ 25;
   - ring pixels fall mainly in L 110–140, with a warm cast of R−B 12–25;
   - ring width ≈ gap width (ratio 0.7–1.4 on a radial scan);
   - fine concentric grooves are visible at 1:1;
   - the disc is 75–92 % of frame height.

   The critic also judges that the pair "belong to the same family of object" without its being a copy. *Measured, and perceptually judged.*
7. **Aesthetic B, side by side with spiralTextPom.webp.** Measured on the frames at 15.0 s (T2) and 3.0 s (T1) beside the reference:
   - black field with L ≤ 6;
   - neutral plate (|R−B| ≤ 4) with a top-left → bottom-right ramp spanning at least 120 L levels;
   - letters with L ≥ 225, tops facing out, inward clockwise spiral;
   - turn pitch ≥ 1.6× cap height (more open than the reference).

   No faux texture: black-field noise σ ≤ 1.5 and kit grain disabled in code. *Measured, and structurally verified.*
8. **Real cutouts and real sound:**
   - In O_B, the keys are recognisably the foraged key photograph: bit teeth and the bow's hole are visible at 1:1, with no background islands or halos in the 100× crop.
   - The three bell strikes coincide (±1 frame) with F126, F246 and F426.
   - Elsewhere the track is silent.
   - A silent variant exists for comparison.
   - *Measured, and perceptually judged.*

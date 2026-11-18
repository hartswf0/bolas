# Le Chant du styrène: assembly (editor, repair round 2)

- Script: `films/le-chant-du-styrene.py` (kit.Film; kit.py not edited, a `Film2` subclass only swaps the encoder CRF 28 -> 21). Render: `assets/films/le-chant-du-styrene.mp4`, 38.000 s, 912 frames, 960x540, 24 fps, 5.4 MB, poster `assets/films/le-chant-du-styrene.webp` at 24.0 s.
- Repair round 2 renders: `editor-build/melt3f.py` + `render_melt2.py` / `render_sh3b2.py` (Sh3a, dissolve target, Sh3b) and `editor-build/sh4v3.py` (Sh4), frames in `films/sources/le-chant-du-styrene/editor-repair2/`. Sh1 and the Sh5 pellet layer remain the round-1 renders below.
- Repair round 1 renders, made by the editor on the units' code without editing it: `editor-build/sh1v2.py` (Sh1), `editor-build/melt3e.py` + `render_melt.py` (Sh3a, dissolve target, Sh3b), `editor-build/sh4v2.py` (Sh4 and the Sh5 pellet layer). Frames are in `films/sources/le-chant-du-styrene/editor-repair/` (git-ignored, 154 MB of PNG). Sh2a, Sh2b and the heap are U2's, unchanged. No new downloads (one Commons metadata read for the Gigaset credit).
- Letterbox 2.35: band y = 66 to 474, bars zeroed after the grain. The band is feathered over 4 px at the top and over 6 px plus 2 black px at the bottom, so the encoder's 8x8 block at rows 472-479 does not bleed. Measured on the mp4: top bar max 3; bottom bar rows 476-479 max 9 in 24 of 912 frames (p99.99 = 2), 0-1 below that.
- Captions: cream (#E8E2D2) serif, 23 px, in the lower bar, hemistichs either side of a thin rule at x = 480. They use U1's text, including L2 "nourri".
- In-picture declarations, small and dim in the upper bar: each starting at its shot head: "photographie réelle, couleur substituée" (0.0-17.6 s, through Sh2a and Sh2b), "acier photographié, coulée simulée" (17.6-27.6 s), "tiges photographiées, couleur substituée, fonte et granulés simulés" (27.6-35.0 s), "tas photographié, chute dessinée" (35.0-38.0 s).
- Grade, shared over every shot: black point 3, soft knee at 196 with a ceiling of 222, then kit's single grain strength on the band only.
- Mix: U1's seven stems through `Mix.add`, plus these changes, all mixing:
  - **Press bed −6 dB** (gain 0.5).
  - **Ducking around meter onsets:**
    - ring events around each L2 pulse (−45 to +110 ms, to 0.10);
    - drain and press around each L3 pulse (−90 to +130 ms), and under the L3 caesura gap;
    - rain around each L4 pulse (to 0.12).
  - **L2 meter +2 dB** while the rings land.
  - **Added sounds:**
    - Two more set-downs at 1.25 and 1.85 s, reusing U1's own 0.60 s set-down.
    - A short struck attack (click plus 150 Hz thud) on each L3 pulse.
  - The end is still silent.
- Ledger: `shot_ledger.json`. Validator: `python3 -I validate_tour.py --json` (shot_ledger.json is now the default; `--planned` checks plan.md's shots) exits 0 with `all_ok: true` (`validate_result.json`).
- Cut detection on the mp4: `cut_detection.json`. Meter measurement on the mp4's audio: `meter_measure.json` (from `editor-build/onsets.py`). Review sheets: `assembly-compare-{05.0,16.5,24.0,26.5,32.0}s.jpg` and `assembly-compare-sheet.jpg`, each film still beside styreneA.webp and kf-2.png, with stats in `assembly_band_stats.json`.

## Timecoded sequence

| t (s) | frames | shot · step · playback | picture | sound | evidence IDs |
|---|---|---|---|---|---|
| 0.00–8.60 | 0–206 | Sh1 · P4 · static | Four loose rings cut from the photograph, red/amber gel. Set down one by one at 0.60, 1.25 and 1.85 with a spring settle. Ring0 turns 16° in the plane (2.9–8.4). A warm light passes across the rings (3.0–8.0). Blue practicals. | room; set-downs 0.60, 1.25, 1.85; L1 meter 2.40–6.45 | F-runner, H-gel, H-puppetry, H-lightpass, H-practicals-u2, H-stems, H-tag-1 |
| 8.60 | 206\|207 | hard cut (line gap) | | | |
| 8.60–13.02 | 207–312 | Sh2a · P3 · backward | Wide. Rings fly on eased arcs, on twos, staggered. Ring 1 is home on f312. | launches, L2 meter from 11.00, ring-1 snap 13.000 | F-runner, H-puppetry, H-constraints, H-gel, H-stems |
| **13.02 C1** | **312\|313** | **hard cut on the L2 caesura** (detected: diff 8.2 against a neighbour maximum of 2.6) | | | |
| 13.02–17.60 | 313–422 | Sh2b · P3 · backward→hold | Rings 2–4 home at 14.00, 14.70 and 15.30, then a glide to the complete shot and a hold | snaps and rattles, ducked under L2 pulses 9–12 | F-runner, H-puppetry, H-constraints |
| 17.29–17.58 | 415–422 | 8-frame shape-match dissolve | Sh2b hold into the melt-filled mould through the same camera (cavity IoU 0.96–0.97; geometry unchanged) | | H-mould-field, F-steel |
| 17.60–20.80 | 423–499 | Sh3a · M+P2 · static/tilt | Full melt in the CC0 steel: neutral grey plate with the photograph's own grinding marks (turned 34°), melt coloured by thickness (deep red core, pale amber edge) | press bed in at 18.8 (−24 dB), L3 meter from 19.60 with struck attacks | F-steel, F-runner-geometry, H-mould-field, H-melt-shading, H-camera, F-gigaset, H-tag-3 |
| **20.80 C2** | **499\|500** | **hard cut on L3 syllable 5** (diff 10.0 against 1.4) | | | |
| 20.80–27.60 | 500–662 | Sh3b · M+P2 · backward | 3/4 view from the left of the plate, so the right-arm cavity that empties first (21.9) is visibly the farthest; then 22.9, 23.9, 24.9, sprue last at 26.19; focus pulls far cavity → sprue. Grinding streaks bend inside each arm (refraction 80 px × surface gradient); arm thickness tapers hub → gate, so the melt runs deep red to pale amber. Emptied hollows are recesses: dark floor, far wall lit by the key, near lip's shadow, no closed bright contour. | drain tone and suctions (ducked under the pulses), sprue glug 26.2, **sound-only pellet rain from 26.80** | F-steel, F-runner-geometry, H-fill-time, H-melt-shading, H-camera, F-gigaset, H-stems, H-tag-3 |
| 27.60 | 662\|663 | hard cut (line gap) | | | |
| 27.60–35.00 | 663–839 | Sh4 · P1 (plasticize shown backward) · backward | 6 + 5 articulated cutout trees whose every rod is a piece of the **real photographed runner** (arms straightened along their measured polylines; real gloss catches, mould lines, edge irregularities, darker core), gelled amber / orange / deep red; no ring discs. Whitney harmonic swing (locked ratios). From 32.05 each irregular-length piece softens at its own time (ends round, it shortens and swells), is released 32.45–32.85, flies its own orbit, **freezes to the heap's granule orange**, is at rest on the chord at 33.60, then falls. | L4 meter 29.40–33.45, rain ducked under each pulse, chord 33.60 | F-runner, H-gel, H-cutout-trees, H-bank, H-metamorphosis, H-practicals-u4, F-heap (colour measurement), H-stems, H-tag-4 |
| 35.00 | 839\|840 | hard cut (line gap) | | | |
| 35.00–38.00 | 840–911 | Sh5 · P1 · static | Real heap of orange granules on black. 34 handmade pellets, drawn frozen in the heap's colour, land on it and are still by 36.375. | last grains, room fades from 36.6, silence | F-heap, H-sh5-pellets, H-stems, H-tag-5 |

## Claim graph (what is asserted, and on what)

- **Edges shown (reverse tour):**
  - P4 ← degate ← P3: *Spritzguss teile.jpg*, Gunpla gate photos; confidence 0.95.
  - P3 ← inject+cool ← M+P2: *Injection molding diagram.svg*, *Mold cavity.jpg*; confidence 0.92.
  - M+P2 ← plasticize ← P1: the PD schematic *Injection moulding process (1).png*; confidence 0.88.
  - Source: `process_graph.json`, checked by `validate_tour.py`.
- **Where the plasticize edge is on screen (repair round 2):** Sh4's trees are made of the runner's photographed material (the shot form), with no finished-part discs. They are shown softening into drops before they part, and the drops freeze into granules, so pellets → melt → tree reads in the tour's direction. The trees are not claimed to be a real object: their form is a declared stylisation and the melting is simulated (tagged). Regrind stays an unverified hypothesis; the pieces part only after they have visibly gone soft.
- **Shape and identity measurements:**
  - ring = cavity: IoU 0.963–0.969.
  - Runner asymmetry: flip IoU 0.129.
  - Each granule is its own cut length of strand.
  - No chains form: pieces have irregular lengths (0.8–2.3 rod widths, so no even bead pitch), each softens and is released at its own random time, and each flies its own harmonic orbit to a scattered rest at 33.60 (stills checked at 32.7, 33.3, 33.6).
- **Cuts:** C1 at 312\|313 and C2 at 499\|500, both detected exactly on the mp4.
- **Meter, measured on the mp4** (rise of each onset over the 60 ms before it; offset of the envelope peak from the cue):

  | line | band | lowest pulse rise | largest onset error | caesura gap below hemistich |
  |---|---|---|---|---|
  | L1 | 500–2000 Hz | 40.6 dB | 5 ms | 14.5 dB |
  | L2 | 2.5–6 kHz | 8.4 dB | 5 ms | −1.5 dB |
  | L3 | 200–400 Hz | 21.3 dB | 20 ms | 16.0 dB |
  | L3 | 500–2000 Hz | 9.7 dB | 5 ms | 16.6 dB |
  | L4 | 2.5–6 kHz | 27.5 dB | 5 ms | 9.5 dB |

  The L2 gap sits under the protected ring-1 snap and the C1 cut at 13.000.
- **Declared, not evidenced:**
  - the runner's red/amber colour (a gel over the teal photograph; tagged in the picture);
  - the melt's glow (a lighting choice, since molten PS does not glow; tagged "coulée simulée");
  - the drain order (a hesitation model re-timed to the verse);
  - the stylised tree vocabulary, built from the photographed runner's rods (no discs);
  - the freezing in flight. Real pelletising cuts cooled strands; the drop-freeze is a declared, legible stand-in.
- **Kept out as unverified:** regrind; how the reference still was made; the polymer of the runner photograph.

## Stats at the review stills (band only; `assembly_band_stats.json`)

| still | lum<20 | p99 | lit sat median | warm | blue |
|---|---|---|---|---|---|
| 5.0 Sh1 | 0.92 | 90 | 0.98 | 0.95 | 0.05 |
| 16.5 Sh2b | 0.92 | 117 | 0.98 | 0.97 | 0.03 |
| 24.0 Sh3b | 0.69 | 164 | 0.86 | 0.73 | 0.27 |
| 26.5 Sh3b hollows | 0.88 | 57 | 0.64 | 0.26 | 0.74 |
| 32.0 Sh4 | 0.76 | 181 | 0.88 | 0.86 | 0.14 |
| styreneA | 0.78 | 182 | 0.91 | 0.73 | 0.27 |
| kf-2 | 0.83 | 107 | 0.87 | 0.88 | 0.12 |

## Repairs (critic round 1; plan section 12)

The critic's items, in order:

- **1b, melt ← pellets:** Sh4 re-staged as melt rising into tree forms that bead, freeze into granules and fall onto the real heap.
- **4b, translucency:** lensing core, deeper red rim from the grazing path, bloom inside the material, streak speculars and liquid surface waves. The flat-fill look is reduced but not gone at full frame (see the weaknesses).
- **Reunion:** dropped. The drops are separated at every frame from cut + 0.3 s.
- **Steel:** texture contrast raised and steel exposure ×2. Hollows are now single recesses. The CRF goes 28 → 21.
- **L2 and L3 meter:** ducked, with struck attacks, and re-measured (table above).
- **Sh1:** staggered set-downs, a ring turned in the plane, a light pass. Mean frame difference is 0.46 on a 0–255 scale.
- **Grain:** measurable at CRF 21.

Reviewer items done: in-picture tags; the notes clause on glow and drain order; press bed −6 dB; bar bleed reduced; the Gigaset credit now uses the exact .webm title, with the unverified "(2009)" dropped (Commons gives "2010s").

Protected and unchanged: the C1 and C2 cut positions, the shape-match dissolve, the drain order and its cues, the 0.8 s rain lead, the palette, the true-black bars, the practicals, the declared colour substitution, the credits ledger, and the validator with its playback/step split.

## Repairs (critic and reviewer round 2)

| finding | repair | check |
|---|---|---|
| Sh3b melt: flat yellow bars, no steel through them | Channel thickness 1.20 at the hub tapering to 0.70 at the gate (±16% noise along the arm); the 0.14 thickness floor is gone, so the edge thins to pale amber and the core is deep red-orange; refraction gain 40 → 80 | `assembly-crop24-3x.png`: grinding streaks change angle inside the vertical arm; edge hue runs orange-red to amber along each arm |
| Steel read as grainy brown | No warm multiply on bare steel; neutral grey; the photograph's own horizontal grinding marks isolated by a 61 px directional average of its high-pass, turned 34° so the streaks cross every arm obliquely; the plate falls off into black with distance | stills 21.5 / 24.0 / 26.5 s |
| Hollows lit by thin bright rim lines | Recess model: the far wall (steel ahead along the light direction, from the camera side) is lit, the near lip casts a shadow 18 px long on a dark floor; channel walls at 0.35 so no bright line; speculars only on live melt | `assembly-crop26.5-2x.png`: open, one-sided lit walls, no closed contour |
| Drain order not legible as far → near | Sh3b is now seen from the left of the plate (yaw −97 → −91°), so the right-arm cavity, which empties first, is the farthest and smallest in frame | 21.5 s still |
| Sh4 trees read as vector illustration; drawn discs | Trees rebuilt (`sh4v3.py`) from the real photographed runner arms (GrabCut piece), gelled, articulated; ring discs removed | `assembly-compare-32.0s.jpg` |
| Beaded-chain stage 31.8–32.5 | Irregular piece lengths and per-piece random soften/release times, all within 32.05–32.85; ease-out orbits move the pieces apart at once | stills 32.7 / 33.3 |
| Tag gap over Sh2a/Sh2b; tags started late | Tags start at shot heads; the substitution tag runs 0.0–17.6 s; Sh4 tag declares the photographed rods, the substitution and the simulation | stills 10.0 / 16.5 s |
| Credits provenance; Gigaset author | `license_source` on every entry (LicenseShortName from Commons extmetadata, re-read 2026-11-16); "via" moved to a `source` field | `films/credits/le-chant-du-styrene.json` |
| Validator default | `validate_tour.py` with no argument now reads shot_ledger.json | exits 0, `validate_result.json` |

Unchanged: the cuts (C1 312|313, C2 499|500 detected), Sh1–Sh2 puppetry, the 0.96 IoU dissolve geometry, the meniscus on twos, the backward drain, the sound (meter measurements in `meter_measure.json` still apply), the letterbox, the credits ledger's four items.

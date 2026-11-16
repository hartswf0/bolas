# Le Chant du styrène: assembly (editor, round 3)

- Script: `films/le-chant-du-styrene.py` (kit.Film, kit.py not edited). Render: `assets/films/le-chant-du-styrene.mp4`, 38.000 s, 912 frames, 960x540, 24 fps, 1.59 MB, plus the poster `assets/films/le-chant-du-styrene.webp` at 24.0 s.
- Letterbox 2.35: the picture band is at y = 66 to 474 and the bars are true black (zeroed after the grain). Captions sit in the lower bar: cream (#E8E2D2) Instrument Serif at 23 px, hemistich 1 right-aligned and hemistich 2 left-aligned around a thin rule at x = 480 (the 6+6 break). Hemistich 2 sits at 38% until its first syllable, then brightens.
- Grade (shared over all shots): black point 3, then a soft highlight knee at 196 with a ceiling of 222, so no whites. Grain is one strength, kit's `_add_grain`, on the band only. Units delivered ungrained bands with an identical roll-off already applied, so nothing else is graded.
- Mix: all seven of U1's stems through `Mix.add` at U1's suggested gains (meter 1.0, ring_events 1.0, drain 0.9, rain 0.8, chord 0.8, room 1.0, press_foraged 1.0), L/R kept, then kit master. Peak −2.9 dBFS; the last 0.15 s is digital silence.
- Ledger: `shot_ledger.json`. Validator: `python3 -I validate_tour.py --ledger shot_ledger.json --json` gives exit 0 and `all_ok: true` (`validate_result.json`). Path `[P4, P3, M+P2, P1]`, playback field on every shot, duration 38.0, C1/C2 ok, other cuts in line gaps.
- Cut detection: `cut_detection.json`.

## Timecoded sequence

| t (s) | frames | shot · step · playback | picture | sound | evidence IDs |
|---|---|---|---|---|---|
| 0.00–8.60 | 0–206 | Sh1 · P4 · static | four loose rings on black, cut from the photograph, red/amber gel, one set down at 0.6 s; blue practicals 0.3× | room, set-down click 0.60, L1 meter 2.40–6.45 (hollow ring clicks) | F-runner, H-gel, H-puppetry, H-practicals-u2, H-stems |
| 2.40–7.35 | | caption L1 | *Voici les quatre anneaux \| que la main a gardés.* | | H-verse |
| 8.60 | 206\|207 | hard cut (line gap) | | | |
| 8.60–13.02 | 207–312 | Sh2a · P3 · backward | wide: rings fly on eased arcs, on twos, staggered 10.30/11.10/11.80/12.50, in front of the bare runner; ring 1 home on f312 (13.000) | launch ticks + whooshes, L2 meter from 11.00 (runner clicks), ring-1 snap 13.000 | F-runner, H-puppetry, H-constraints, H-gel, H-stems |
| **13.02 C1** | **312\|313** | **hard cut on the L2 caesura (13.025)** | caption rule `\|` on screen | | |
| 13.02–17.60 | 313–422 | Sh2b · P3 · backward→hold | close on the right arm pair, rings 2–4 home 14.00/14.70/15.30 with spring settle; glide to the complete shot, hold 15.8– | snaps + rattles; room only 15.9–17.6 | F-runner, H-puppetry, H-constraints |
| 11.00–15.95 | | caption L2 | *Chaque anneau s'en revient \| au bras qui l'a nourri.* (U1's corrected text) | | H-verse |
| 17.29–17.58 | 415–422 | 8-frame shape-match dissolve | Sh2b hold → melt-filled mould seen through the same camera (per-ring cavity IoU 0.96–0.97) | | H-mould-field, F-steel |
| 17.60–20.80 | 423–499 | Sh3a · M+P2 · static/tilt | full melt in the cavities of the CC0 steel, frontal to 18.0, then a slow tilt | press bed (foraged) fades in 18.8, L3 meter from 19.60 (viscous low tones) | F-steel, F-runner-geometry, H-mould-field, H-melt-shading, H-camera, F-gigaset |
| **20.80 C2** | **499\|500** | **hard cut against the L3 caesura, on syllable 5 "re" (0.79 s before the caesura midpoint 21.625)** | | | |
| 20.80–27.60 | 500–662 | Sh3b · M+P2 · backward (TEST SHOT) | 3/4 view, focus pull; the melt drains backward: cavities empty far→near 21.9/22.9/23.9/24.9, sprue last 26.19; four wet-lit ring hollows held 26.2–27.6 | drain tone 21.0–26.3, suctions on each release, sprue glug 26.2, press bed out by 27.4, **sound-only pellet rain from 26.80** | F-steel, F-runner-geometry, H-fill-time, H-melt-shading, H-camera, F-gigaset, H-stems |
| 19.60–24.55 | | caption L3 | *Le rouge se retire, \| et la forme est un creux.* | | H-verse |
| 27.60 | 662\|663 | hard cut (line gap) | | | |
| 27.60–35.00 | 663–839 | Sh4 · P1 · backward | 6 + 5 handmade translucent runner trees, harmonic swing; from 31.0 bead → cut → pellets on orbits → reunion at 33.60 → fall | L4 meter 29.40–33.45 (granular), rain thickening, chord 33.60 | H-trees, H-bank, H-metamorphosis, H-practicals-u4, F-runner-geometry (measurement only) |
| 29.40–34.35 | | caption L4 | *L'objet était un arbre, \| et l'arbre était du grain.* | | H-verse |
| 35.00 | 839\|840 | hard cut (line gap, after L4) | | | |
| 35.00–38.00 | 840–911 | Sh5 · P1 · static | real heap of orange granules on black; 34 handmade pellets land, still by 36.375 | last grains, room fades 36.6, silence | F-heap, H-sh5-pellets, H-stems |

## Claim graph (what is asserted, and on what)

- **Edges shown (reverse tour):** P4 ← degate ← P3 (Spritzguss teile.jpg shows loose rings beside a runner with rings; Gunpla gate-nub photos, conf. 0.95) · P3 ← inject+cool ← M+P2 (Injection molding diagram.svg, Mold cavity.jpg, conf. 0.92) · M+P2 ← plasticize ← P1 (PD schematic *Injection moulding process (1).png*, conf. 0.88). Source: `process_graph.json`, validated by `validate_tour.py`.
- **Shape-identity claims and their measurements:** ring = cavity (IoU 0.963–0.969, `melt_shot.json`); runner asymmetric (flip IoU 0.129); granule = piece of the tree (each pellet is its cut stretch of strand, `harmonic_trees.json`); reunion at 33.60 (0° / 0 px analytically; frame 806 is 0.88° / 2 px off).
- **Verse-coded cuts:** C1 13.025 (L2 caesura mid) and C2 20.80 (L3 syll. 5), both detected within ±1 frame in the mp4.
- **Declared, not evidenced:** the red/amber colour of the runner (gel substitution over the teal photo); the melt's glow (a lighting choice, since molten PS does not glow); the drain order (a hesitation model re-timed to the verse); the stylised tree vocabulary.
- **Kept out as unverified:** regrind; how the reference still was made; the polymer of the runner photograph.

## Stats at the review stills (band only; `assembly_band_stats.json`, sheets `assembly-compare-*.jpg`, `assembly-compare-sheet.jpg`)

| still | lum<20 | p99 | lit sat med | warm | blue |
|---|---|---|---|---|---|
| 5.0 Sh1 | 0.93 | 85 | 0.96 | 0.81 | 0.19 |
| 16.5 Sh2b | 0.93 | 112 | 0.95 | 0.86 | 0.14 |
| 24.0 Sh3b | 0.73 | 156 | 0.85 | 0.78 | 0.22 |
| 26.5 Sh3b hollows | 0.85 | 57 | 0.80 | 0.59 | 0.39 |
| 32.0 Sh4 | 0.75 | 182 | 0.90 | 0.85 | 0.15 |
| styreneA band | 0.57 | 196 | 0.88 | 0.70 | 0.28 |
| kf-2 | 0.84 | 101 | 0.84 | 0.86 | 0.14 |

The plan's bar is lum<20 ≥ 0.65, p99 ≤ 210 and saturation ≥ 0.70, and it is met at 5.0, 24.0 and 32.0. Blue practicals are present in all three.

## Repairs (plan section 12)

No repair was triggered at assembly. The shape match is carried by the units' common `geometry.json` (dissolve IoU 0.96–0.97), and the cut times come out of the shot boundaries exactly. The editor's only choices were caption layout and timing, the shared knee, and grain on the band only, to keep the bars true black.

# les-lieux-dune-fugue · assembly (editor)

Film: `assets/films/les-lieux-dune-fugue.mp4`, built by `films/les-lieux-dune-fugue.py`.
- kit.Film('les-lieux-dune-fugue', 57, size=(960,720)), boil=0, with `ink._grain = False` and no vignette.
- Each frame is `paper_stage.render_shot(shot, t, "none")`, rendered from U2's bake cache. Slates and captions are laid over it from `voice_score.json`.
- Sound follows `sound_cues.json`. Each cue goes in through `mix.add`, then a light reverb (amount 0.06). The samples ramp to zero over 43.94–44.0 and are zeroed from 44.0 to the end. `master()` only rescales, so the zeros stay at zero.

Checks on the render are in `verify_assembly.py`, which writes `assembly_checks.json`, `compare_P01.jpg`, `compare_metrics.json` and `assembly_stage_tests.json`.

## Evidence IDs

| id | kind | item | licence |
|---|---|---|---|
| DOOR-C | foraged photo | Highsmith, Kinnerary US Courthouse doorway, Columbus OH, 2009 (LoC 2010719611) | PD: "No known restrictions on publication" |
| DOOR-S | foraged photo | Highsmith, US Custom House door, Savannah GA, 2013 (LoC 2014630119) | PD (same) |
| BENCH | foraged photo | Highsmith, park bench, Sacramento CA, 2012 (LoC 2013633886) | PD (same) |
| STOCK | foraged scan | Federal Theatre Project, blank sheet, 1934 (LoC musftpsets.200218222) | PD, US government work |
| JUNCTION-FB | foraged photo | Polymagou, *Rue du Soleil, rue de Belleville, Paris 20e* (Commons) | CC BY-SA 4.0 |
| BELL-MURBACH | foraged sound | Amada44, *Church Bells of Murbach* (Commons), 2018 | CC BY-SA 3.0 |
| H-STAGE | handmade | scissor outlines, backing cards, lamp A/B, memory light M, multiplane camera (paper_stage.py) | this work |
| H-FK | handmade | FK hinge rig and gravity fall/bounce of the leaves | this work |
| H-PLAQUE / H-ROUTE / H-CARD | handmade | the "7" plaque, the route strip, the record card | this work |
| H-TEXT | handmade | F1–F5 and the record lines (voice_score.json) | fiction for this work |
| H-SND | handmade | present tone, park tone, creaks, knock, thuds (kit.Mix synthesis, synth_stems.py) | this work |

JUNC-M (Marville, *Rue Tirechappe*) is foraged and verified PD, but it is **not used**. U2 baked P02 before U1's `route/junction/` existed, so it is left out of the credits. Note that re-running `paper_stage.py bake` would now pick `route/junction/fallback_…` by alphabetical order and apply generic crops to it. Do not re-bake without fixing `junction_source()`.

## Timecoded sequence

| # | in–out | shot | picture evidence | captions / flags | sound evidence |
|---|---|---|---|---|---|
| 1 | 0:00.0–0:08.0 | P01 · prise A · matin | DOOR-C, DOOR-S, STOCK, H-STAGE (lamp A), H-PLAQUE; left leaf lifts 5.5, falls (H-FK), contact 7.0 | F1 1.0–5.0 (asserted P01) | C01 present tone (H-SND); C02 creak 5.5; C03 thud 7.0 |
| 2 | 0:08.0–0:19.0 | P02 · carrefour | JUNCTION-FB near and far planes, DOOR-C corners (mid); 10 px glide; H-ROUTE laid 13.0–15.0 in 6 drawings | F2 9.5–15.5 (asserted P02) | C04 tone, spread wider (H-SND) |
| 3 | 0:19.0–0:28.0 | P03 · banc (présent) | BENCH warm print, GrabCut bench, hand-cut trunk, litter strip; 8 px truck | F3 20.5–26.0 + `lien → P03 : INFÉRÉ` 21.0–26.0 | C05 park tone (H-SND) |
| 4 | 0:28.0–0:44.0 | P01 · prise B · soir | same piece table as shot 1 under lamp B. Leaves open at 31.0 (right leaf 4 frames late) onto the BENCH cold print (light M, depth 0.6/1.0). Closed by hand from 41.0. Contacts 43.1 L, 43.5 R | F4 28.4–31.0 (hearsay, age 8–10); F5 36.0–41.0 + `souvenir · vers l'hiver (intervalle) · lien P01→P03 : INFÉRÉ` 36.5–41.0 | C06 tone ducked −6 dB 32–41; C07/C08 creaks 31.05/31.22; **C09 BELL-MURBACH 32.0–41.0**; C10 creak 41.1; C11 knock 43.1; C12 thud 43.5 |
| 5 | 0:44.0–0:52.0 | P03 · retour · silence déclarée | the shot-3 end plate, held still | none | **digital silence** |
| 6 | 0:52.0–0:57.0 | record card | H-CARD on STOCK, DOOR-C route strips, under lamp A | (card text: intervals, INFÉRÉ links, photo credits) | **digital silence** |

## Claim graph (sec. 3 Olog, as realised)

```
Obs P01-A (shot 1, lamp A) ─shows→ P01 ←shows─ Obs P01-B (shot 4, lamp B)   [same pose, same piece table: I1]
Obs P02   (shot 2)         ─shows→ P02
Obs P03-1 (shot 3) ─shows→ P03 ←shows─ Obs P03-2 (shot 5, same plate, silence)
F1 ─asserted→ P01   [pair F1×P01-A]
F2 ─asserted→ P02   [pair F2×P02]
F3 ─INFERRED→ P03   [pair F3×P03-1, flag on screen]
F4 ─unknown (no place, hearsay)   [pair F4×P01-B]
F5 ─INFERRED→ P03   [pair F5×P01-B: DISLOCATED; memory plane lit by M ≠ A,B; flag on screen]
P01 ─adjacent (asserted)→ P02 ─adjacent (inferred arrival)→ P03   (narrative order, not geography; route.png)
```

## Measured on the final render

All of these come from `assembly_checks.json`.

**File**
- 57.0 s, 960×720, 24 fps, H.264 video with AAC audio, 1.26 MB.

**Silence**
- From 44.0 to 57.005 the decoded AAC has 573,520 stereo samples and every one is 0 (13.0 s). **PASS.**
- The last non-zero sample is at 43.901 s. The mix ramps to zero over 43.80–43.90 because the AAC encoder rang ±2 LSB for about 16 ms after a hard cut at 44.0. The first encode failed this test for that reason.
- The sound was then remuxed with `--remux`: same encoder settings, video stream copied.

**Tone at 0:03** (plan §9.5)
- Stone (126,105,68), R−B 58.5.
- Door luminance 25.3.
- Luminance p5 21.3, p95 127.1.
- Joint darkness 11.9.
- **All PASS.**

**I1 on the render**
- Stone edges at 0:02 against 0:29 coincide within 1 px for 0.856 (A in B) and 0.801 (B in A). The rest of each edge map is the shadow side of the gaps, which changes with the lamp.
- On U2's lossless frames the figures are 0.905 and 0.858. The piece table and alpha maps are identical, so the geometry is identical.
- P03 at 27.9 against 48.0: mean absolute difference 1.25 levels, which is mp4 noise. On U2's own frames they are pixel-identical.

**I5 on the render**
- Memory plane (87.5, 96.9, 109.2), with B ≥ R.
- Stone R−B 67.4.
- **PASS.**

**Defining beat**
- The mean of the door region goes from 23 (closed) to 66 (open) over 31.0–32.5 and holds open.
- 31 distinct door-region drawings between 31 and 36.
- At 43.9 the door is closed again (23.3).

**U2 stage tests, re-run** (`assembly_stage_tests.json`)
- I9 PASS: hinge drift 0 px, hinge height range 0, stud slide 0.
- Maximum opening 60.9° left and 67.2° right; the right leaf lags 4 frames.
- Contacts at 7.0 and 43.5.

**Voice**
- `validate_voice.py` PASS with 0 errors, and all 5 counterexamples are rejected.
- Captions show at 3.0, 12.0, 23.0, 29.5 and 38.5, and none show at 0.5, 7.5, 17, 27.5, 33, 42 or 48.

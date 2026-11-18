# Bang Bang: assembly (editor)

`films/bang-bang.py` builds the film. It renders through kit.Film at 1280x720 (repair 1; the board camera is written for 960 and scaled by 4/3), 24 fps, 30.0 s, 720 frames. It imports the board unit's rig and dynamics (`board-build/board.py`: pieces, joint chain, spring-dampers, camera, sets) without editing them. On top of those it adds the editor layer:
- the slips from `cues.json`: one pen, a write-on per letter, the strike and the correction, all in the handmade joined cursive of `editor-build/cursive.py` (repair 1; no typeface glyphs)
- the graphite English gloss, one paragraph per panel in the right half of the commentary column
- the on-page fiction line under each planche title: "M. Pique-Vent, inventeur inventé - vols imaginés"
- the typed baseline strips
- the rubber band and tally
- the timed A/B labels
- the frame-range headers and the vertical margin note
- the page turn
- the BB-08 camera that keeps the slip column visible
- the stem mix

Evidence IDs (ledger.json, rig.json, cues.json):

| ID | What it is |
|---|---|
| LIL-START | PSM V46 D647, the glider and pilot |
| PENAUD-PLATE | Pénaud's hélicoptère (one id in ledger, cut_manifest, rig and here) |
| AUDUBON-MAGPIE | Bowen/Audubon, LoC |
| SND-PICA-PD | magpie chatter |
| MIA-AIR-A / MIA-AIR-B | FWS field air |
| EV-PENAUD-RUBBER, EV-PENAUD-CONTRA | rotor mechanism claims (source) |
| EV-LIL-WEIGHTSHIFT | weight-shift glider (source) |
| EV-NOSEHIGH-SLOW-a | nose-high costs speed, past a critical angle the wing stalls (source: FAA Pilot's Handbook of Aeronautical Knowledge, US government work; cited, not fetched) |
| EV-NOSEHIGH-SLOW-b | full stop, still hang, tail-first slide (fiction, A3) |

Fictions are A1 paper wing (handmade), A2 rotor use and A3 flight (on real machines), and the inventor Pique-Vent.

## Sequence

| time | frames | board | picture | slips / sound | evidence |
|---|---|---|---|---|---|
| 0.0-1.0 | 0-24 | BB-00 | Wide: planche 1. Three empty punched panels, mirrored show-through, graphite headers with frame ranges. | air fades in, sheet settle f6 | handmade sheet; MIA-AIR-A/B |
| 1.0-8.0 | 24-192 | BB-01 | Push-in to panel 1 (60 %, frame edge just past the slip column). Pique-Vent on the wall with the handmade paper wing (repair 2: a curved membrane with a bowed leading-edge spar, scalloped trailing edge, fanned creases and a turned-down tip corner). 3 flaps; the tip lags and creases (#41). Hop f134, sits f154. The magpie on the gatepost turns its head in 6 held steps. Label A at f60. | S1 f28/30-91 "Il s'est fait une aile en papier."; S1b f105/107-135 "La mienne obéit."; S1c "pof." f154. Chatter f29, rustles, pof f154 | LIL-START, AUDUBON-MAGPIE, A1 (fiction), SND-PICA-PD |
| 8.0-14.2 | 192-340 | BB-02/03 | Slide to panel 2. The hélicoptère in his hand, the rotor turned on 2s. The pen skein kinks more with each turn and a graphite tally reaches 12. Release f254: it rises about 120 px. Snap f312: the band end whips (BAND spring) and the machine tips and drops f331. Label B at f300. | S2 f200/203-250; S2b f252/255-306 "Lui reste en bas. C'est sage."; S2c "clac." f312. Creaks, whirr, snap f312, thump f331 | PENAUD-PLATE, EV-PENAUD-RUBBER, EV-PENAUD-CONTRA, A2 |
| 14.2-16.0 | 340-384 | BB-04/05 (sheet 1 panel 3) | The glider puppet is dropped into sheet-1 panel 3 at f340 as the referent of S3; its shadow shrinks as it lands. | S3 f343/346-389 "Enfin, les grandes ailes." | LIL-START |
| 16.0-18.0 | 384-432 | BB-06 | Pull out to wide f384-396. Planche 1 flips up on its top binding f396-408 (foreshortened, edge shadow) to reveal planche 2 with its key poses. Shadow settles f408-418. Push to panel 1 f420. | page-turn flip f408, sheet lands f418 | handmade |
| 18.0-21.0 | 432-504 | BB-07 | Run-up downhill, legs driven ±28° on the hip pin, lift-off f490 (the shadow offset grows). | S4 f430/433-466 "Face au vent. Bien."; footfalls, wind | LIL-START, EV-LIL-WEIGHTSHIFT, A3 |
| 21.0-24.0 | 504-576 | BB-08 (test shot) | Push-in 58 to 61 % with the slip column whole. Pitch 5 to 35°, x-advance decays to 0 by f540. Hang f540-564 (body still): the legs are thrown forward as the body stops dead (3.6° at f540, 23.5° at f542, peak 29.4° at f544) and swing back to -0.7° by f564. Tail-first slide from f565. The panel is empty of the bird until f554; the magpie enters high over the glider f554-566 (never over the pilot), flares f566-571 and lands on the post f571-576. Graphite 35° arc, A and B labels. | S5 f476/480-525 "Il lève le nez pour monter". Strike f528-530, "s'arrêter" above it f531-547. S5b f547/549-592 "Moi aussi, pour me poser." Wind cut and pin tick f528, declared silence f540-553, whoosh peak f557 | LIL-START, AUDUBON-MAGPIE, EV-NOSEHIGH-SLOW-a (source), EV-NOSEHIGH-SLOW-b / A3 (fiction) |
| 24.0-27.5 | 576-660 | BB-09 | Panel 3: the slide steepens, the nose drops, impact f605 (drawn on ones). The right wing's spar SNAPS: the outer wing whips down to 58° and is held f605-610 (3 drawings), then sags onto the broken root at 40° with one bounce; legs settle by f624. From f576 the magpie perches at panel 3 right, head down toward the wreck (editor fix for the "Krach !" witness gate). It lands beside the wreck f638, two hops, a peck. | S6 f589/593-605 "Krach !" completes on f605; S6b f615/617-638 "Un peu vite."; S6c f636/639-674 "Mais au bon endroit." Thump and crumple f605, chatter f614 | LIL-START, AUDUBON-MAGPIE |
| 27.5-30.0 | 660-720 | BB-10 | Pull out to wide planche 2: run, stall at 35°, wreck. All slips stacked one group per panel, with the struck "monter" and the vertical graphite note "BB-08 f504-576 voir B". | chatter f682, air out | handmade |

## Variants

- **baseline_bb07-09.mp4** (f432-660, 9.5 s): the same picture. Sheet-2 slips are replaced by the human reporter's typed newsprint strips (IBM Plex Mono typed per character, no correction): "Course d'élan." / "L'appareil se cabre." + "Il décroche." / "Il s'écrase." + "Échec.". It uses the writer unit's baseline mix, with no pin tick and no chatter.
- **swap_bb07-09.mp4** (f432-660): the cues_swap.json slips. The BB-09 slips are on panel 1 and "Face au vent. Bien." is on panel 3. The picture is unchanged and the sound is the full mix, f432-660. S6c's overlap with S5 is declared in cues_swap.json and kept as written.

## Claim graph

Image facts come from the exposure sheet and the comments from the cues:
- **nose up then stop.** The image fact is pitch at 15.0° on the f528 drawing (exposure.json) and x-advance at 0.39 px/frame on f533. The comment is S5 "monter" struck on f528, then "s'arrêter". The contrast: to a flier, raising the nose is braking.
- **contact.** The image fact is impact f605. The comment is "Krach !", completing f605. The contrast comes from S6b/S6c: too fast, but the right place, a landing.
- **mechanism claims.** These are carried only by the image: the rotor (EV-PENAUD-*) and weight shift (EV-LIL-WEIGHTSHIFT). No slip names a person or a machine.

## Repair round 1 (editor)

| Unmet item | Fix | Measured |
|---|---|---|
| Hershey Script hand | `editor-build/cursive.py`: a joined French cursive drawn for this film. Each lowercase letter is one stroke written as control points; a word is one Catmull-Rom spline, so letters join. Every instance moves its points by its own noise, size and width; slant wanders and the baseline drifts across the whole line; felt-nib weight follows stroke direction. `hand_shim.py` routes every hand on the page through it (slips, headers, labels, 35°, margin note, show-through). | 1171 same-letter pairs compared across all slips: 0 pixel-identical. Side by side with bang.webp: side_by_side_f540_ref.jpg |
| Commentary not dominant at f700 | x-height ~23 page px (was ~12), slips 384 px wide, plus a graphite English paragraph per panel to their right (x-height ~26) filling the column | f700 page ink 1.37 %, midtones 2.34 % (reference 1.26 % / 2.89 %) |
| Toned panel fill | removed; the panel is the page paper | interior median (242, 228, 212) vs page (241, 227, 211), dE 0.16 |
| Credits for the MIA air | author USFWS (NCTC, America's Wildest Places Vol. 2), licence read from archive.org gov.fws.aws.2.9 / 2.8 (licenseurl creativecommons.org/licenses/publicdomain); ledger credits_draft now equals credits/bang-bang.json | - |
| Audubon magpie licence | basis stated: PD by age, date from the edition not the LoC record (LoC: rights not evaluated); corroborated by the same octavo edition on Commons, LicenseShortName "Public domain", Copyrighted False | - |
| 960x540 | 1280x720 | ffprobe 1280x720, 30.000 s, 2.56 MB |
| Fiction not on screen | graphite line under each planche title, x-height ~23 page px (~9 px in the wide shots) | visible in frame_f012.png and frame_f700.png |
| EV-NOSEHIGH-SLOW uncited | split into -a (source, FAA handbook) and -b (fiction, A3) in ledger.json | - |
| Note | rewritten: the Jabely/Queneau dossier disclosed, fiction scope corrected, the pen hand is handmade (no Hershey any more) | 106 words |
| assembly.md f529 | corrected to f528 | - |

Not done: the optional leg polish (f576 pop, larger post-stall overshoot); the exposure sheet is unchanged, so the protected stall and impact anchors are exactly as before. Sound unchanged (same stems and gains).

## Acceptance (re-measured after repair 2, 2026-11-16; measurements.json, rig.json tests)

1. **Stall readable from the image alone:** first failure frame f533 (pitch 21.7°, x-advance 0.39 page px/frame); glider still f540-564 (x and y range 0.0 px); visible leg swing over the hang (29° peak at f544); spar snap held at the impact.
2. **Cue anchors:** nose 15° at f529, strike f528 (Δ1, unchanged); "Krach !" completes f605 and the thump is at f605 (stems unchanged); f540-553 air only; magpie whoosh peak f557 now inside the flight f554-571.
3. **Witness gate:** lexicon 15/15, texts unchanged.
4. **f700 vs bang.webp:** paper median (240,226,210), dE 0.7; panel vs page dE 0.16; ink median (58,48,39) vs reference (69,57,46); midtones 2.35 % (ref 2.89 %); ink 1.34 % (ref 1.26 %; brief 3-9 % not met, at the reference's own level). side_by_side_f700_ref_kf2.jpg.
5. **f540:** ink 2.60 %, midtones 3.11 %, ink median (53,42,34); 1171 same-letter pairs, 0 identical.
6. **Puppet animation:** pivot drift max 3e-05 px; no angle-limit violations; legs on screen |phi| 23.5° at f542, -0.74° at f564, under 1° from f559, body at rest throughout (no counterfactual); BB-01 head 6 held steps; the magpie flies f554-571 above the glider and lands on the post, re-enters and lands by the wreck f620-638 in BB-09; no magpie in panel 2 f540-552; legs after impact settle in 19 frames; wing snap held f605-610 then rest at f616 (1 bounce).
7. **Proof completeness:** 30.000 s, 720 frames, 1280x720, 2.59 MB mp4 + 78 KB webp; baseline and swap 9.5 s each (0.64 / 0.70 MB); boards BB-00 to BB-10 numbered contiguously with ranges matching exposure.json; 6 credited foraged items, all public domain with basis recorded; ledger evidence resolves every id used (AUDUBON-MAGPIE, SND-PICA-PD, PENAUD-PLATE, LIL-START, MIA-AIR-A/B).

## Repair round 2 (editor)

`board-build/board.py` was changed (backup `board-build/board.round2-before.py`; editor round-1 script kept as `editor-build/bang-bang.round1.py`) and re-run, regenerating exposure.json, rig.json tests, bb08_test.mp4 and bb08_sheet.jpg from the same code the film renders.

| Item | Fix | Measured |
|---|---|---|
| Hang: no visible secondary motion, decay counterfactual | Hang f540-564; hip pendulum kicked 6 rad/s at f540 as the body stops dead; hang damping 8.6; test on the on-screen run. No acceleration across the f576 panel cut (removes the old 73°/-55° leg pop). | legs_world f540 3.6, f542 23.5, f544 29.4, f552 11.0, f556 3.4, f560 0.1, f564 -0.7; f576 -43.0 continuous with f574 |
| Magpie covers the pilot f548-550 | Flight f554-571 along the panel top, above the glider; flare and landing on the post f566-576; the held "bird on post" key no longer shows before it has flown there | no magpie in panel 2 f540-552 |
| BB-01 wing reads as a ladder | paper_wing() redrawn: curved membrane, bowed leading-edge spar, scalloped trailing edge, fanned faint creases, turned-down tip corner; pivots unchanged | frame_f100.png |
| No damage at impact | Spar snap: outer right wing whips to 58°, held f605/606/608/610, sags onto the broken root at 40°; joint stop widened to -3..62 once broken; f605 drawn on ones | frame_f605.png |
| One ink (optional) | engraving pieces remapped so their darkest line is (70,58,46) (was 45,38,32); softens the perched magpie | f700 ink median (58,48,39) |
| Board numbering (optional) | Sheet 1 panel 3 = BB-04/05 f340-384; BB-02/03 f192-340; exposure BOARDS match; S3 cue board_id BB-04/05 (timing/text unchanged) | - |
| Ledger ids (reviewer) | AUDUBON-MAGPIE and SND-PICA-PD added to evidence[]; Brehms, Penny wing, crow, xeno-canto marked not used (superseded); PENAUD-PLATE everywhere; Audubon date "octavo printings 1840-1871"; FAA citation recorded as not re-fetched | - |

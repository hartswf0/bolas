# teuf-teuf: assembly (montage editor, repair 2)

Film: `assets/films/teuf-teuf.mp4`, 44.0 s, 1280×720, 24 fps, 3.2 MB. Control without captions: `assets/films/teuf-teuf-nocaption.mp4` (3.1 MB).
Build order: `layout_wall.py` → `animator-build/anim.py` → `animator-build/report.py` → `merge_animation.py` → `films/teuf-teuf.py` → `verify_sheet.py` → `score_from_render.py` → `editor_compare.py` → `build_ledger.py`.

## One ledger
The critic found that the picture and the proof had split. `motion.py` (the fixture the frames are drawn from) is now the only motion law. `verify_sheet.py` rewrites `exposure.json` from the render's per-frame records and runs the asserts in `mechanism.json` on those same frames. **All pass** (`asserts.all_pass = true`). sim.py's 250 px sheet is kept in `superseded/`.

| invariant | measured on the rendered frames |
|---|---|
| 1 same challenge | one 180 px mask (sha1 in exposure.json); the front edge starts at 330 px in every trial; 7.0 s of push each (drag 4.5–11.5, rollers 14.0–17.6 + 19.6–23.0, wheel 26.0–33.0); hands at stone-local y −80/−60 in every trial; front edge at 1.20 m (11.5 s), 3.00 m (23.0 s), 8.00 m (33.0 s); counter-check stops at 0.88 m |
| 2 contact | planted-foot slide ≤ 0.014 px; hand residual 0 px (drag, heave, log D pick-up and set-down); roller slip 0.010 px/frame; log tangency 0 px; wheel angle = Δx/R (error 0.002 px) |
| 3 continuity | no undeclared jumps. Declared cuts: 13.0, 25.0, 34.0 (trial resets: real cuts through 2 held-black frames with a scratch wipe) and 16.2, 18.8 (camera, same τ; load step 1 frame of motion) |
| 7 secondary | nothing moves before its first impulse; slowest decay 0.58 s |
| captions | measured first visible frame, caption mp4 vs control: lags +0.45, +0.40, +0.43, +0.43 s after the bar's causes |

## Sequence (timecode → evidence)
| time (s) | shot | content | evidence |
|---|---|---|---|
| 0.0–4.0 | 0 wall wakes | toned Cueva wall fades up; white-scratched title (1.2 s write-on); lineage line 1.6–3.9 « d'après Teuf-Teuf de Jean Jabely (1956) · légendes originales » (register R1); pusher walks in | F1 Cueva (Suzko, CC BY-SA 3.0); H title, puppets |
| 4.0–13.0 | 1 drag | 9 stick-slip lurches to 1.2 m; carrier hauls the rope; 1.2 m ghost at 11.7. Caption 1 at 6.87 (4th stick begins 6.51) | H runner, rope, ghost; S scrape (synth), steps (Pwaivers CC BY-SA 3.0, Gravity Sound CC BY 4.0) |
| 12.92–13.17 | reset cut | down to black, held black, scratch wipe, up | H |
| 13.0–14.0 | 2 substitute I | stone levered up in 3 frames; three bark logs rolled in; settles | H logs; S knocks (PDSounds, PD) |
| 14.0–16.2 | 3a rollers wide | 0.5 s push-in to ×1.28 (14.0–14.5); logs turn and drift back at v/2 | rumble (synth) |
| 16.2–18.8 | 3b close-up ×2.2 (test shot) | log A squeezed out at 16.93, stops at 17.44 ("tok"); caption 2 « Et moi ? » at 17.78 (the only nonhuman line); stone waits from 17.6 | same τ as the wide; plate B = crop of the same master |
| 18.8–21.0 | 3c wide (×1.28 framing) | carrier sets log D down in front (18.4–19.3); push resumes at 19.6; stone rides onto D at 20.5 | knocks |
| 21.0–25.0 | 3d/3e | rolls to 3.0 m (23.0); log B also left behind (21.68); pull back to the full wall 23.0–23.6; 3 m ghost | thud (synth) |
| 24.92–25.17 | reset cut | held black, scratch wipe | |
| 25.0–34.0 | 4 wheel and axle | plank cart; wheels are the GrabCut Ljubljana wheel; 8.0 m by 33.0; carrier walks ahead of the load throughout; passes 3 m at 28.61; caption 3 at 28.97 | F2 wheel (P. Milošević, CC BY-SA 4.0); plank knock once per turn |
| 33.92–34.17 | reset cut | held black, scratch wipe | |
| 34.0–38.0 | 5 counter-check | pins pulled 34.7; caption 4 at 35.04; loose wheels drift back; rear wheel rolls out 35.88, kicked out behind and drawn in front of the pusher's legs, settles behind him 36.88 (tok); platform's rear falls 0.30 s, lands 36.17; grinds to a stop at 0.88 m (36.23) | pin click, knock, landing thud + plank knock, grind (synth), tok + rebound (PDSounds) |
| 38.0–44.0 | 6 comparison | three ghosts; figures sit; the loose wheel lying behind the pusher rocks with a tok at 41.0; end line written on 39.8–40.8 and held to 44.0 (staged-sequence label on its own line, then the sources) | provenance |

Sound: mean −23.3 dB, peak −0.2 dB, no silence of 0.5 s or more below −45 dB. Foraged: PDSounds knock and church air (PD), Pwaivers steps (CC BY-SA 3.0), Gravity Sound gravel (CC BY 4.0). Synthesized: scrape, rumble, grind, scratch and thud. The film never reads `sound/raw/`.

## Repair 2 (critic + reviewer, round 2)
- **Wall a smooth wash** (`layout_wall.py`): rock high-pass 0.25→0.10, broad relief 0.55→0.12, yellow 0.30→0.04; the real red spray prints dark only round the two stencils (the spiral and other red marks under the ground line fade to a faint stain); 2 large guanacos above the action kept black, every other body faded to 6 % (below 10 % contrast, none in the close-up window); two white scratched line guanacos added and the engraved bovid strengthened (handmade). Interior wash luminance std (σ3 blur, pale mask eroded 12 px) at 7.0/17.5/30.0 s: 10.9/8.6/10.6 → 7.5/7.8/7.8, and the open wash grew from 32 % to 46–53 % of frame. Plate pale std 19.9→15.8 (A), 15.4→10.9 (B).
- **Lower hand**: re-cut from the photograph's red at a finer threshold (all five fingers), holes filled: a true pale stencil in a dark blown halo, no internal mark.
- **Bands**: rub contrast ×1.85 about the mean (streaky black-to-grey, like the reference's bands); means now (85,85,69) top, (100,99,81) bottom — darker than plan §7, traded to keep ≥ 12 % below 60 after the wall was emptied.
- **Counter-check**: rear wheel kicked out behind (−260 px/s, rolling resistance 260 px/s²), drawn in front of the pusher's legs, lies behind him through shot 6; platform rear falls in 0.30 s (uniform acceleration, 7 frames); grind deceleration 380 px/s² so it rests just after landing (0.88 m ≤ 1.2). Sheet at 12 fps: `counter-sheet-r2.jpg`.
- **Wheel trial**: carrier walks at front + 100 px the whole trial, never half-hidden behind the stone.
- **Wide roller shots**: 0.5 s push-in to ×1.28 (plates cropped from the same master; top band kept at screen scale as in B).
- **Register R9**: 1.8 m × 1.26 m boulder (180 × 126 px), 2.3 m figures, 0.68 m wheels.
- **Score**: `score.json`/`score.md` regenerated by `score_from_render.py` from exposure.json, assembly-cues.json and mechanism.json (onsets 6.87/17.78/28.97/35.04, caption 4 cause the pin pull 34.7, end line 39.8–44.0, stop 0.88 m, log stop 17.44).
- **Lineage**: named on screen (1.6–3.9 s) and in the note; no material from the 1956 film.
- **Credits**: `licence_checked` date on every entry.

## Repairs to the critic's list
- **Ledger:** fixed as described above.
- **Contact:** a root contact solve in `Puppet.build`. Gait feet now carry across segment boundaries, and the sit-down feet count as planted only once the pose has settled.
- **Captions:** timed to the bar's causes, including the pin pull.
- **Resets:** now real cuts, not dissolves.
- **Wall** (`layout_wall.py`):
  - The photograph's own hand shapes print pale inside handmade blown halos.
  - Only the 8 largest guanacos stay black.
  - Rock high-pass is 0.25 and the bands are pressed darker.
  - The close-up carries the top band.
- **Figures** (×1.06):
  - The pale joint seams are gone.
  - Edges get a dry-brush fringe and the halo is a blown-pigment spray.
  - Ghosts are hidden in the close-up, which removes the stray line.
- **Review:** the end line is held 3.2 s. Typo fixed. Air synthesis is declared. The film's licence is stated as CC BY-SA 4.0. Dead sound entries are flagged in `build_score.py`.

Tone (`tone-final.json`, `compare-final.jpg`):

| time | pale luminance | pale rgb | pixels below 60 |
|---|---|---|---|
| 7.0 s | 212 | (220,214,185) | 15.4 % |
| 17.5 s | 209 | (216,211,182) | 25.0 % |
| 30.0 s | 212 | (220,214,185) | 16.3 % |

Figure crop beside the bull: `compare-pusher-bull.jpg`.

## Known weaknesses
- The pusher is cropped at the left edge whenever the load is at 0 m (the starts of shots 0, 2 and 4).
- Faded guanacos remain as very faint grey ghosts (6 %).
- Band means are darker than the plan's (85/100 vs 99/120 rgb).
- The stone comes to rest 0.06 s after the platform lands.
- The upper stencil's hand outline comes from a convex hull, so it is wedge-shaped at the wrist.
- Wagon and quern recordings were never fetched (HTTP 429), so rumble and grind remain synthesized.

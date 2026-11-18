# Assembly — les-caids-de-la-gaudriole (montage editor, r1)

Film: `assets/films/les-caids-de-la-gaudriole.mp4`, 63.0 s, 960x540, 24 fps container, stop-motion on twos (12 exposures/s), 5.39 MB, H.264 + AAC.
Script: `films/les-caids-de-la-gaudriole.py` (kit.Film; kit.py untouched). All strip art in every exposure = `strip/strip-art.png`,
sha256 44b0d0c3e02adf6ed1e116f7a4b08262733a0a71ea15e4f9670bbf9d79fbd137, the same file the page (`assets/pages/les-caids-de-la-gaudriole.png`, U1 `strip/page.py`, unchanged in r1) uses.
No added grain; the texture is the paper scan. The tabletop is a computed stop-motion (every exposure rendered in code from the real scans); the credit card and notes say so.

## Repair r1 (what changed and why)
1. **F0 drop-out on landing (B2b/B3).** Cause: in `shots/build/render_shots.py` the SETTLE states used a positive F0 lag, which bent F0's free edge DOWN to z = -5.7 u, through F3 and the table, so the z-buffer put F3 in front of part of F0 (the straight-edged hole at f0805-f0808 and f1141-f1144). The early fold also dipped F0's tail as low as -54 u under the table (A rises before M lifts F1). Fixes: (a) SETTLE lags reversed: the free edge springs up 16 u, then 7 u, then lies flat; (b) new `table_contact()` constraint: from the first point where the raw curve would go below z = 0, the tail lies flat on the table, face up, arc length preserved (paper cannot pass through the table). Shots 5 and 7 re-rendered (94 and 53 distinct exposures), stems re-cut (`sound_shots.py`), the r0 renderer kept as `render_shots.r0.py`.
2. **Fixture over all exposures** (`shots/build/occlusion_check.py`, run inside `render_shots.run`): per exposure (i) z >= 0 and no self-crossing of the cross-section; (ii) where F0 is the top layer at every X (38 exposures of shot 5, 54 of shot 7), a facet-ID buffer must show F0 over F0's whole projected footprint (eroded 1 px); fail on any region > 4 output px. Result: geometry_ok_all true, pixel_ok_all true, max wrong pixels 4 (scattered edge pixels, no region). Control: the r0 settle state fails it (z_min -5.72, 304,002 wrong px in one region). Summaries in `shots/fold-events.json` → shots.5/7.occlusion_summary.
3. Film frames f0790-f0815 and f1125-f1150 re-extracted from the new mp4 and viewed: miller, sack and balloon whole through every settle exposure.
4. First folded still hold lengthened: 0:33.75-0:35.5 (1.75 s; was 1.25 s).
5. Rights: all Commons licences re-read live (editor/extmeta-1.json, -2.json). Bell attribution confirmed from extmetadata: "Work With Sounds / Konrad Gutkowski", CC BY 4.0, now on the credit card with "one strike cut, faded, re-levelled" (r0 card wrongly named LVR). Wreckless (1935) PD confirmed from archive.org item metadata (Jam Handy Organization, licenseurl publicdomain). file_url/license_url gaps filled; resized local copies declared with original sha1.
6. Credit card and notes now state the table, fold and light box are rendered in code from the scans (claim-scope fix).

## Timecoded sequence

| Time | Seg | Exposures | Picture | Sound | Evidence |
|---|---|---|---|---|---|
| 0:00–0:03 | title | 36 | "FOLDED DIALOGUE" / "AFTER LÉCROART - OUBAPO - FIGURES W. BUSCH 1865", pen.py strokes written 3 letters per exposure on the paper scan | room tone fades in | paper-scan; strip/pen.py |
| 0:03–0:07 | shot 1 | 48 | sheet falls, turns, lands on the table, corner lift 34/12/3 u, contact shadow tightens | ticks, rustle + thud | tabletop/shot-1; busch-mm_*, paper-scan, wood-scan, paper-foley, thud |
| 0:07–0:15 | shot 2 | 96 | onto P1; miller's shrug (3 damped swings about 52°), porter-P1 head tilt; ends on the printed pose | bell 0:08; tick per moved exposure | puppets/rig.json, poses.json; rendered per exposure in the film script, drift (45,-15,0) |
| 0:15–0:23 | shot 3 | 96 | to P2; porter's forearm swings the key out, wrist lags, key pendulum damps to rest | ticks | poses.json shot 3; drift (40,-10,0) |
| 0:23–0:26 | shot 4 | 36 | stepped pull-back to the open strip, still 2.0 s (open reading) | room tone | OPEN state, no jitter |
| 0:26–0:34 | shot 5 | 96 | THE FOLD: 4 rest, 86 fold (A mountain leads, M valley, 40 u curl bands, back-face show-through, height-driven shadows), 3 settle (free edge springs 16 → 7 u → flat), 3 still | tick per exposure, landing thud | tabletop/shot-5; fixture-shots.json; occlusion_summary; strip/fixture.json |
| 0:34–0:42 | shot 6 | 96 | FLAT state: still 1.5 s (1.75 s with shot 5's end), stepped push-in across the seam on "THE KEY? I HAD IT / IN MY POCKET / ALL ALONG.", drop to sleeve→hand→key join, pan to "OH? REALLY?" (1.5 s). Key printed and still | near silence (ducked); bell 0:40 | RS.section(FLAT) = V(x') per fixture |
| 0:42–0:50 | shot 7 | 96 | folded, unfold (24), open 1 s, refold (24), settle, hold 2.25 s | ticks, thud | tabletop/shot-7; occlusion_summary |
| 0:50–0:59 | shot 8 | 108 | straight down on the light box: room light, switch 0:51, 3 s ramp, 3 s hold with ghosts (A..M mirrored at 2A−x, M..B unmirrored at x−D), ramp down, clean folded reading | switch on/off, synthesised hum (declared) | tabletop/shot-8; lightbox-still.png |
| 0:59–1:03 | credits | 48 | 10 pen-lettered lines: sources, licences, CC BY attributions with modification notice, what is rendered in code | room tone fades out | credits json |

Reading-state holds (camera and lamp still): open 0:24–0:26 (2.0 s); folded 0:33.75–0:35.5 (1.75 s) and 0:47.75–0:50 (2.25 s); light box at full lamp ~0:54–0:57 (3 s).

## Stills for the critic
`films/stills/les-caids-de-la-gaudriole/still-0{12,20,30,36,55}.png` and `side-0NN.jpg` (film frame | fold_extract-000.webp | kf-1, kf-2 for 0:55), regenerated from r1. Extra: 033.60.png (landing exposure, the r0 failure point), 047.50.png.

## Ledger notes
- Mix: stems' relative levels kept, whole mix scaled once to 0.8 peak. Bell 0:08 from the shot-2 fx stem; bell 0:40 = shots/sound/bell-strike.wav at 0.6.
- The settled film exposure is checked geometrically (cross-section = V(x'), fixture-shots.json) and by the facet-ID test, not by a pixel diff of the perspective frame against V.
- sound_shots.py now skips muxing shots whose exposures are not on disk (2, 3: rendered by the film script).

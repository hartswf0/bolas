# Assembly — les-caids-de-la-gaudriole (montage editor, r0)

Film: `assets/films/les-caids-de-la-gaudriole.mp4`, 63.0 s, 960x540, 24 fps container, stop-motion on twos (12 exposures/s), 5.4 MB, H.264 + AAC.
Script: `films/les-caids-de-la-gaudriole.py` (kit.Film; kit.py untouched). All strip art in every exposure = `strip/strip-art.png`,
sha256 44b0d0c3e02adf6ed1e116f7a4b08262733a0a71ea15e4f9670bbf9d79fbd137, the same file the page (`assets/pages/les-caids-de-la-gaudriole.png`, built by U1 `strip/page.py`) uses.
No added grain (ink.paper(grain=False)); the texture is the paper scan.

## Timecoded sequence

| Time | Seg | Exposures | Picture | Sound | Evidence |
|---|---|---|---|---|---|
| 0:00–0:03 | title | 36 | "FOLDED DIALOGUE" / "AFTER LÉCROART - OUBAPO - FIGURES W. BUSCH 1865", pen.py strokes written 3 letters per exposure on the neutral paper scan | room tone fades in | paper-scan; strip/pen.py |
| 0:03–0:07 | shot 1 | 48 | sheet falls, turns and lands on the wood table, corner lift 34/12/3 u, contact shadow tightens | ticks, landing rustle + thud | U3 tabletop/shot-1; busch-mm_*, paper-scan, wood-scan, paper-foley, thud |
| 0:07–0:15 | shot 2 | 96 | stepped move onto P1; miller's shrug (3 damped swings about 52°), porter-P1 head tilt; ends exactly on the printed pose | bell at 0:08; one tick per moved exposure | puppets/rig.json, poses.json shot 2; rendered here per exposure with shots/build/render_shots.py, drift corrected to (45,-15,0) |
| 0:15–0:23 | shot 3 | 96 | crosses to P2; porter's forearm swings the key out, wrist lags, key pendulum damps to rest | ticks | poses.json shot 3; rendered here, drift (40,-10,0), starts from shot 2's end camera |
| 0:23–0:26 | shot 4 | 36 | stepped pull-back to the whole open strip (12 exp), still hold 2.0 s: the open reading | room tone | rendered here, OPEN state, no jitter |
| 0:26–0:34 | shot 5 | 96 | THE FOLD: 4 rest, 86 fold (A mountain leads, M valley, 40 u curl bands, back-face show-through, height-driven shadows, ~1 u jitter, ±2% flicker), 3 settle, 3 still | one paper tick per exposure, landing thud | U3 tabletop/shot-5; shots/fixture-shots.json; strip/fixture.json |
| 0:34–0:42 | shot 6 | 96 | settled folded state (FLAT): 1 s still hold, stepped push-in, reads "THE KEY? I HAD IT / IN MY POCKET / ALL ALONG." left to right across the seam, drops to sleeve→hand→key join (held 0.8 s), pans to "OH? REALLY?" (held 1.5 s). Key stays printed and still (amendment) | near silence (room tone ducked); bell at 0:40 | rendered here from RS.section(FLAT), the state U3's fixture shows = V(x') |
| 0:42–0:50 | shot 7 | 96 | replay: folded, unfold (24), open 1 s, refold (24), settle, hold 2.25 s | ticks, thud | U3 tabletop/shot-7 |
| 0:50–0:59 | shot 8 | 108 | straight down on the light box: room light, switch (0:51), 3 s lamp ramp, 3 s hold with ghosts (A..M mirrored at 2A−x, M..B unmirrored at x−D), ramp down, clean folded reading | switch on/off, synthesised 100 Hz hum (declared), room tone | U3 tabletop/shot-8; shots/lightbox-still.png; bell, switch |
| 0:59–1:03 | credits | 48 | pen-lettered sources and licences on the paper scan | room tone fades out | credits json |

Reading-state holds (camera and lamp still): open 0:24–0:26 (2.0 s) and 0:45.5–0:46.5 (1 s, replay); folded 0:34–0:35 + 0:48–0:50; light box at full lamp ~0:54–0:57 (3 s).

## Stills for the critic
`films/stills/les-caids-de-la-gaudriole/still-0{12,20,30,36,55}.png` and `side-0NN.jpg` (film frame | reference fold_extract-000.webp | kf-1, or kf-2 for 0:55).

## Ledger notes
- Sound levels: the stems' relative levels are kept; the whole mix is scaled once to 0.8 peak so kit's master does not auto-gain. Bell 0:08 comes from U3's shot-2 fx stem; bell 0:40 = shots/sound/bell-strike.wav at 0.6.
- Disk: the volume was full (shared with other works). To render, U3's superseded shot-2/shot-3 exposure PNGs (old drift; the film re-renders those shots in memory) were moved, not deleted, to /dev/shm/caids/parked/ (tabletop/shot-2, shot-3 and editor/exposures-shot-2, -3). They are regenerable with `python3 shots/build/render_shots.py 2 3`; /dev/shm does not survive a reboot.
- No bar change proposed by the editor.

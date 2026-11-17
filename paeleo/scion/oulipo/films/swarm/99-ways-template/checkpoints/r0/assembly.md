# Assembly — 99-ways-template (b1, Direction 2), render r0

**Film:** `assets/films/99-ways-template.mp4`
- 960×540, 24 fps, 71.5 s (1716 frames), 3.7 MB.
- h264 + aac. Audio mean −33.9 dB, peak −8.4 dB.

**Rendering:**
- Built by `films/99-ways-template.py` with kit.Film, synthetic grain off.
- Each frame pastes the page art. The current panel is re-rendered per frame by `anim/panels.py`, which overrides FK joints on `page/build_page.py`.
- Panels before the current one show their rest pose, which is the page art. Panels after it show the first pose of their own shot.

**Evidence IDs:**

| ID | Item |
|---|---|
| R | LoC 2017776093, Rothstein, Randolph agent |
| CL | LoC 2017776111, Rothstein clock |
| BU | LoC 2017861739, Bubley visitor / station front |
| K | LoC 2017679951, ANRC key |
| SH | LoC musftpsets.200218222, the 1934 sheet |
| s:room | MIA "Panama by Air (Reel 4)" 1914 |
| s:tick | Commons "Clock ticking.ogg" |
| s:door | Commons "Squeaky door.ogg" |
| s:latch | Commons "Door handle creaking.ogg" |
| s:chair | Commons "Creaky wooden swivel chair.ogg" |
| s:steps | Commons "Church people walking steps with reverb.ogg" |
| s:thud | Commons "Dull thud.ogg" |
| s:train | Commons "Train sounds from Iowa", CC BY 3.0 |
| syn:bell | counter bell, synthesized (declared) |
| syn:paper | paper handling, synthesized (declared) |
| H | handmade: borders, balloons, glyphs, memo, SERVICE card, hook, tag, ledger card |

## Sequence

| Time | Shot | Picture | Sound | Evidence |
|---|---|---|---|---|
| 0:00–0:04 | S0 | The sheet fills the frame, then the camera pulls out to the whole page. 32 border strokes rule in on twos; each panel's first pose is laid down as its box closes. Eases to P1. | syn:paper, s:room | SH, H, R |
| 0:04–0:09 | S1 · P1 | Head dips two poses on the collar. Push-in on the memo (1.18×), held 1.5 s. Two pencil taps. Pull back. | s:tick, pencil tap (s:tick filtered) | R, H (memo) |
| 0:09–0:14 | S2 · P2 | Anticipation dip, 4 rise poses with the head lagging, slide out right. The empty chair and desk remain. | s:chair, s:steps | R (office plate) |
| 0:14–0:19 | S3 · P3 | Gilliam stepping walk, 5 steps with a ±6 px bob, past the SERVICE card on the closed door. | s:steps | R, H |
| 0:19–0:24 | S4 · P4 | Halts. The visitor shifts behind the glass. Bell. "What time is it?" lands at 0:20.67 (tail out left through the window). Head swings 3 steps. | syn:bell, s:thud | R, BU |
| 0:24–0:29 | S5 · P5 | Head up 2 steps. The minute hand ticks onto the 2, overshoots and settles at 4:10. "Ten past four!" lands at 0:26.33. | s:tick close, s:thud | R, CL |
| 0:29–0:34 | S6 · P6 | Empty window. "Thanks!" lands at 0:29.67, tail exiting left. The lamp sways 3 poses about its cord. | s:thud, receding s:steps, s:train −6 dB | R |
| 0:34–0:39 | S7 · P7 | Arrives in 7 steps. Latch, then the door swings on its fixed jamb through 7 foreshortened poses (outer face, then inner face), overshoot and settle. The key appears on its hook. | s:steps, s:latch, s:door | R, K, H |
| 0:39–0:46 | S8 · P8 | Head tilts 3 steps. The arm dips, then rises 4 poses to the chin; 2 scratches. "What the hell was I looking for, anyway?" lands at 0:42.5. Read hold, then a 2 s hold with the key unmoved. | s:thud, then one s:tick in the hold | R, K, H |
| 0:46–0:52 | S9 | Pull back to the whole page. P1→P8 each lift one shadow-step in R0 order (0.5 s each). Full-page hold. | s:room | all of the above |
| 0:52–0:59 | S10 · D1 | Page turn. Label hold. C1: bell, then "What time is it?" lands at 0:54.58 and "Ten past four!" at 0:55.58. Camera to C2: creak, then "Thanks!" at 0:57.25 and the forgetting balloon at 0:58.17. | syn:paper, syn:bell, s:thud, s:door | R, CL, K, SH, H |
| 0:59–1:07.5 | S11 · D2 | Page turn. Label. V1: the visitor at the window, bell from inside. V2: "What time is it?" at 1:03.17, tail out the bottom. V3: "Ten past four!" at 1:04.58, then "Thanks!" at 1:05.33. V4: she walks off on twos from her V1 place to the left edge; far back, the clerk at the open cupboard. | s:train 0 dB, syn:bell, s:thud, s:steps | BU, R, CL, K |
| 1:07.5–1:11.5 | S12 | Ledger card: a handmade timetable, E0–E5 (with E3b) × B/D1/D2. Rules are pen-ruled on twos; rows are written in order. Cells read shown / implied / omitted from coverage.json, with the implied cues and the outcome line beneath. | syn:paper, s:tick ×2, syn:bell | SH, H |

## Measured (`editor_checks.json`, asserted by the script)

- **Rest frames:** every shot's last frame, and its action-and-balloon end, match the page crop at panel scale. Mean abs difference is 0.0 for S1–S8 (limit ≤4).
- **Film scale:** the rendered film frame matches the same camera over the untouched page, inside the panel. Mean abs difference is 0.0 for S1–S8.
- **Balloons:** land frames match `timing.json` (S4 f40, S5 f56, S6 f16, S8 f84). Each has a +9 px bounce on the frame before and is hidden 4 frames earlier.
- **Derivative rest layers:** composites match their page crops, mean abs difference ≤0.12.
- **FK:** see `anim/fk_test.json`. Pivot drift is 0.0 px and the key offset changes by 0.0 px. These values are by construction (from the joint matrices).

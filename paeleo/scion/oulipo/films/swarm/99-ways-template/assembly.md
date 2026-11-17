# Assembly — 99-ways-template (b1, Direction 2), render r2 (branch A promoted)

**r2 (branch A promoted over r1):** picture and sound are unchanged from r1. The render is byte-identical to `branch-a/99-ways-template.mp4` and to r1. r2 changes the rights record only:
- `films/credits/99-ways-template.json`: LoC sheet licence quotes LoC's statement, with `license_url`, `file_url` and a credit line. The six Commons PD sounds are recorded as PD-author. Panama by Air (1914) is PD by date only, with no archive statement read. The CC BY 3.0 train is recorded as modified and has a ready attribution line.
- `films/notes/99-ways-template.txt` (103 words): the cutouts are "pieces cut by hand from the photographs", and the CC BY recordist (Glaneur de sons, modified) is credited.
- The P8 gaze gap is still open. Branch A found no up-looking head of this sitter in the reachable archives (see `branches.md`).

**Film:** `assets/films/99-ways-template.mp4`
- 960×540, 24 fps, 72.5 s (1740 frames), 3.6 MB.
- h264 + aac.

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
| H | handmade: borders, balloons, glyphs, dialogue, memo, SERVICE card, TICKET OFFICE card, RANDOLPH nameboard, hook, tag, ledger card |
| Rr | R plates repaired with pixels of R itself (editor/plate_repair.py) |

## Sequence

| Time | Shot | Picture | Sound | Evidence |
|---|---|---|---|---|
| 0:00–0:04 | S0 | The sheet fills the frame, then the camera pulls out to the whole page. 32 border strokes rule in on twos; each panel's first pose is laid down as its box closes. Eases to P1. | syn:paper, s:room | SH, H, R |
| 0:04–0:09 | S1 · P1 (E0) | Head dips two poses on the collar. Push-in on the memo (1.18×), held 1.5 s. Two pencil taps. Pull back. | s:tick, pencil tap | R, H (memo) |
| 0:09–0:14 | S2 · P2 (E1) | Anticipation dip, 4 rise poses with the head lagging, slide out right. Rest = the page: desk and chair empty, only his shoulder at the right edge (r1). | s:chair, s:steps | R, Rr |
| 0:14–0:19 | S3 · P3 (E1) | r1: new camera on the closed double cupboard, no desk. He enters from the left and walks in 5 Gilliam steps (±7 px bob, head lagging) to stand before the right leaf with the SERVICE card. | s:steps | R, H |
| 0:19–0:24 | S4 · P4 (E2) | He steps in and halts on the bell. Nobody behind the glass (r1). "What time is it?" lands at 0:20.67, tail out left through the window. Head swings up toward the voice in 3 steps. | syn:bell, s:thud | R |
| 0:24–0:29 | S5 · P5 (E3) | r1: un-mirrored, facing the clock. Head up 2 steps; the minute hand ticks onto the 2, overshoots, settles at 4:10. "Ten past four!" lands at 0:26.33. | s:tick close, s:thud | R, CL |
| 0:29–0:34 | S6 · P6 (E3b) | Empty window. "Thanks!" lands at 0:29.67, tail exiting left. The lamp sways 3 poses about its cord. | s:thud, receding s:steps, s:train | R |
| 0:34–0:39 | S7 · P7 (E4) | Arrives in 7 steps. Latch, then the door swings on its fixed jamb through 7 foreshortened poses, overshoot and settle. The key appears on its hook. | s:steps, s:latch, s:door | R, Rr, K, H |
| 0:39–0:46 | S8 · P8 (E5) | r1: un-mirrored, facing away from the key. Head tilts up in 3 steps on the collar; arm dips, then rises 4 poses until the pencil tip meets the chin; 2 scratches. "Now... what did I come over here for?" lands at 0:42.5 with one bounce. Read hold, then a 2 s hold; the key never moves. | s:thud, one s:tick | R, Rr, K, H |
| 0:46–0:52 | S9 | Pull back to the whole page; P1→P8 lift one shadow-step each in R0 order. Full-page hold. | s:room | all |
| 0:52–0:59 | S10 · D1 | Page turn. C1: bell, "What time is it?" 0:54.58, "Ten past four!" 0:55.58. C2: creak, "Thanks!" 0:57.25, the forgetting balloon 0:58.17. | syn:paper, syn:bell, s:thud, s:door | R, Rr, CL, K, SH, H |
| 0:59–1:08.5 | S11 · D2 | Page turn. V1: the visitor at the TICKET OFFICE window under the RANDOLPH board; bell; "What time is it?" 1:01.58, tail to her mouth (r1). V2: the empty desk through the glass. V3: "Ten past four!" 1:04.67. V4: she walks off on twos to the left edge; "Thanks!" 1:07.08, tail to her mouth (r1); far back, the clerk at the open cupboard. | s:train, syn:bell, s:thud, s:steps | BU, R, CL, K, H |
| 1:08.5–1:12.5 | S12 | Ledger card E0–E5 (with E3b) × B/D1/D2, pen-ruled on twos, cells from coverage.json, outcome line beneath. Blind readers stop before this (reader cut, see status.md). | syn:paper, s:tick ×2, syn:bell | SH, H |

## Measured (`editor_checks.json`, asserted by the script)

- **Rest frames:** every shot's last frame, and its action-and-balloon end, match the page crop at panel scale. Mean abs difference is 0.0 for S1–S8 (limit ≤4).
- **Film scale:** the rendered film frame matches the same camera over the untouched page, inside the panel. Mean abs difference is 0.0 for S1–S8.
- **Balloons:** land frames match `timing.json` (S4 f40, S5 f56, S6 f16, S8 f84; read from timing.json shots[].balloons). Each has a +9 px bounce on the frame before and is hidden 4 frames earlier.
- **Derivative rest layers:** composites match their page crops, mean abs difference ≤0.12.
- **FK:** see `anim/fk_test.json`. Pivot drift is 0.0 px and the key offset changes by 0.0 px. These values are by construction (from the joint matrices).

# boucle-là : assembly (editor)

Script `films/boucle-la.py` (kit.Film, 960×540, 24 fps, 66.0 s). Output `assets/films/boucle-la.mp4` (4.96 MB). Frame state = U3 `page-ghost.png` + U3 `frames/<ID>/` pasted at each occurrence's crop rect from its slot start (drawing 0 until the sequence starts, last drawing = page crop after); from 58.5 s the state is U3 `page.png` itself (ghost + all held drawings == page.png, max diff 0). Nothing re-drawn. Camera = eased keys over that raster; during each held occurrence a flat white surround isolates the panel (no gradient). Panel scale 0.8025 and H scale 0.559 (validator matcher grid), framing snapped to whole output pixels so paired occurrences give bit-identical film frames.

Evidence IDs: **EV-D** Daumier print (CC0, cut by U1: `films/sources/boucle-la/panel-artist/cut/`), **EV-BELL** Commons bell (CC0), **EV-RUS** Commons paper rustle (PD), **HM-PAGE** U3 page/frames/ghost/annotation (handmade from EV-D + U2 lettering), **HM-LET** U2 lettering, balloons, note, margin.

| Time (s) | Segment | Picture | Sound | Evidence |
|---|---|---|---|---|
| 0.0–3.0 | Page establish | whole page fitted; furniture inked, all 7 story panels ghost 22 % | rustle, onset 0.4 (page laid down) | HM-PAGE, HM-LET, EV-RUS |
| 3.0–5.5 | Margin & title | ease into LE MOT / OU QUI L'A LAISSÉ ? (3.9–4.6 hold), slide to A | — | HM-LET |
| 5.0–11.5 | o1 A (r1c1) | A inked from 5.0; seq 5.5–7.17 (20 drawings on 2s); balloon 6.08; hold to 11.25 | paper tick 5.47 | EV-D, HM-PAGE, HM-LET, EV-RUS |
| 11.5–18.0 | o2 B (r1c2) | slide 11.5–12.0; seq 12.0–13.67; balloon 12.42; hold | tick 11.97 | same |
| 18.0–24.5 | o3 C (r1c3) | slide 18.0–18.5; seq 18.5–20.17; balloon 19.0; hold | tick 18.47 | same |
| 24.5–37.0 | o4 H (r2) | drop to wide H 24.5–25.3 (drawing 0 on white); seq 26.0–28.75: heads in, note lifts, card flip drawings 19–24 (27.58–28.0); **28.0 face-out, ground spot black**; balloon 28.5; held drawing from 28.75; push to note face 31–35; hold 35–37 | rustle 27.3 (faded out by 27.8); **bell onset 28.00 (only one)** | EV-D, HM-PAGE, HM-LET, EV-RUS, EV-BELL |
| 37.0–39.5 | Pull-back | full page 38.2–38.6: rows 1–2 inked, row 3 ghost; slide to r3c1 | bell decay | HM-PAGE |
| 39.0–45.5 | o5 C′ (r3c1) | identical frames to o3 (seq 39.5) | identical tick | same as o3 |
| 45.5–52.0 | o6 B′ (r3c2) | identical frames to o2 (seq 46.0) | identical tick | same as o2 |
| 52.0–58.5 | o7 A′ (r3c3) | identical frames to o1 (seq 52.5) | identical tick | same as o1 |
| 58.5–61.6 | Clean page | pull back to page.png fitted, held clean | silence | HM-PAGE |
| 61.6–66.0 | Route trace | U3 annotation layer revealed along its route polyline 61.6–64.4 (tags appear as the line passes), hold, fade to clean page 65.2–65.9 | silence | HM-PAGE |

## Ledger (measured)
- Pair identity in the film (`edit.json` → `pair_film_frame_identity`, `python3 films/boucle-la.py --verify`): o1/o7, o2/o6, o3/o5 each 138/138 film frames sha256-equal, from sequence start to the departure fade.
- Fixture (`fixture-report.json`, run after this render): film suite PASS — held frames match page crops (NCC ≥ 0.99, MAD 6.1–6.6 panels, ~3 H); paired holds MAD ≈ 1.4; exactly one bell onset at 28.000 s vs face-out 28.0 s. B2 PASS.
- Voices: OFF (user note on the test shot). `--voices` restores U2's grains, one file per ID, at each balloon frame.
- Room tone: none foraged, none synthesized.

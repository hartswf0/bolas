# Assembly: moins-dun-quart-de-seconde-pour-vivre

**Film:** `assets/films/moins-dun-quart-de-seconde-pour-vivre.mp4`, 66.0 s, 24 fps, 960×540, 2.6 MB, h264/aac.
**Script:** `films/moins-dun-quart-de-seconde-pour-vivre.py` (kit.Film). Every frame uses `paper(grain=False)`, with no vignette and boil 0.
**Page:** `assets/pages/moins-dun-quart-de-seconde-pour-vivre.png`, 2480×1754. It is built by the same script (`build_page`) from the same `plate-540.png` and balloon PNGs.
**Camera:** a crop of the handmade page.
- At every panel slot it is at scale 1 with integer offsets, so the panel sits at frame x 210–750.
- Pull-backs resample the page with a BOX filter.

**Fixture:** `deliverables/equality-check.json` (all_pass = true).

## Evidence IDs
**Data files**
- **P:** the plate `plate-540-55b62d4cc2a2` (plate.json).
- **SL:** the stroke ledger `strokes.json`, 41 strokes.
- **LIB:** the #38 library and decoded settle (plate.json `library_38`).
- **BL:** `balloons.json` panels and write-on schedule.
- **PL:** `balloons.json` page_lettering.
- **SND:** `sound.json` and `cues.build()`.
- **CUE:** cue checks in `deliverables/film-sound-checks.json`.
- **EQ:** `deliverables/equality-check.json`.

**Bar and invariants:** B1–B5 and V1–V4 are in plan.json; I1–I6 are the plan invariants.

## Timecoded sequence

| Time (frames) | Segment | On screen | Heard | Evidence |
|---|---|---|---|---|
| 0:00.00–0:04.46 (0–107) | S0 draw-on | Camera 1:1 on A1. The plate is brushed on dab by dab in ledger order: stars, lamp, bench, body, head, eye, arms, envelope, flecks, fur. It is slow, then fast. | One low-passed real pen grain per brush stroke (41). Ambience fades in. | SL, `plate-artist/prologue-schedule.json`, CUE, B3 |
| 0:04.50–0:05.54 (108–133) | S0 settle (#38) | Decoded path: eye-centre 6 → eye-half 4 → eye-closed 3 → canonical 3 → chest-in 5 → canonical 5 (min hold 3). It ends sha-equal on the canonical plate. | Ambience. | LIB, V1, I5 |
| 0:05.58–0:06.00 (134–143) | S0 hold | Frozen canonical plate. Asserted in script: `PROLOGUE[-1] == PLATE`. | Ambience. | P, I1 |
| 0:06.00–0:06.75 (144–161) | S1 pull-back | Eased log-zoom from 1:1 to the full page (scale 0.30). | Ambience. | — |
| 0:06.75–0:07.75 (162–186) | S1 stamps | The plate appears unchanged, hard cut, in A2, A3, A4, B1, B2, B3, B4, one every 4 frames. | One real pen-tap, low-passed, per stamp (7). | P, I1, #17 |
| 0:07.83–0:08.63 (188–207) | S1 labels | Header, header-right, "A — TO WAIT" and "B — THE ALIBI" are written stroke by stroke in parallel. Strokes are re-brushed with the letterer's brush at pen position, scaled to 19 frames. | One grain per label stroke (92). | PL, CUE, B3 |
| 0:09.00–0:10.00 (216–239) | S2 push in | Eased zoom into A1, landing at 1:1 on frame 240. | Ambience. | — |
| 0:10.00–0:15.00 (240–359) | A1 | The outline is drawn (frames 0–4.5 of the panel), a 2-frame lift, the tail stub, then "IF I OPEN IT, / I'LL KNOW." written in pen order. Written by 0:12.08, then held for 2.92 s. | 26 grains plus a tap at the full stop. | BL, CUE, EQ holds.A1 |
| 0:15.00–0:15.58 (360–373) | move | Eased lateral slide at 1:1, integer offsets, no fade. | Ambience. | — |
| 0:15.58–0:21.00 (374–503) | A2 | "IF I DON'T, / I CAN STILL / HOPE." Written by 0:18.08, then held for 2.92 s. | 33 grains plus a tap. | BL, CUE, EQ |
| 0:21.00–0:21.58 (504–517) | move | Slide. | Ambience. | — |
| **0:21.58–0:26.00 (518–623)** | **A3 silence** | **No balloon. Art and camera are still for 4.42 s.** The black above the head is empty and the lamp is visible. | **Ambience only:** 0 cues, pen-track peak 0.0. Measured mix about −37 dB RMS. | BL beats (Silence), CUE A3_cues = 0, B5, #47 |
| 0:26.00–0:26.58 (624–637) | move | Slide. | — | — |
| 0:26.58–0:31.00 (638–743) | A4 | "HOPE IT IS, / THEN." Written by 0:28.21, then held for 2.79 s. | 24 grains plus a tap. | BL, CUE, EQ |
| 0:31.00–0:33.50 (744–803) | S3 strip A | Eased pull-back (14 frames) to the whole of strip A (scale 0.40), then held for reading. Strip B is still unlettered below. | Ambience. | — |
| 0:33.50–0:35.00 (804–839) | S4 travel | Eased down to B1 at 1:1. | Ambience. | — |
| **0:35.00–0:40.50 (840–971)** | **B1** | "ME? I'VE BEEN / ON THIS BENCH / SINCE NINE." Written by 0:38.46, then held for 2.04 s. | 51 grains, a tap at "?" and a tap at the full stop. | BL, CUE, EQ, B1 |
| 0:40.50–0:41.00 (972–983) | move | Slide, 0.5 s. | — | — |
| **0:41.00–0:44.50 (984–1067)** | **B2** | "ASK THE LAMP." sits upper right, so the lamp globe is uncovered (0 px coverage). Written by 0:42.42, then held for 2.08 s with the camera still. | 21 grains plus a tap. | BL placement, EQ, B1 |
| 0:44.50–0:45.00 (1068–1079) | move | Slide. | — | — |
| **0:45.00–0:49.50 (1080–1187)** | **B3** | "AND LOOK - / STILL SEALED." The flap is uncovered (0 px). Written by 0:47.29, then held for 2.21 s. This is the poster frame (47.5 s). | 31 grains plus a tap. | BL, EQ, B1 |
| 0:49.50–0:50.00 (1188–1199) | move | Slide. | — | — |
| **0:50.00–0:57.00 (1200–1367)** | **B4** | "WHY WOULD I / OPEN SOMEONE" is written, then **a 10-frame pen hold (0:52.58–0:52.96, panel frames 62–70)** with the partial string on screen and the balloon boil frozen. Then "ELSE'S?" is written. Written by 0:53.50, then held for 3.50 s. | 39 grains. The pen hold has 0 cues and a pen-track peak of 0.0. A tap at "?". | BL pen_hold, CUE B4_hold_cues = 0, B5 |
| 0:57.00–0:58.50 (1368–1403) | S5 pull-back | Eased zoom to the full page, both strips at the same size. | Ambience. | — |
| 0:58.50–0:61.00 (1404–1463) | S5 footer | Footer "THE ART LAYER IS IDENTICAL IN ALL EIGHT PANELS · SHA256 55B62D4CC2A2" is written stroke by stroke over 60 frames. | 86 soft real grains, one per footer stroke. | PL, film-sound-checks footer_cues |
| 0:61.00–0:64.00 (1464–1535) | S5 swap | The top row's balloon plane alternates every 18 frames: B-set, A-set, B-set, A-set. The art never changes. | Ambience. | V2, #17, I2 |
| 0:64.00–0:65.75 (1536–1577) | S5 hold | The final page, identical to the page PNG at film scale. | Ambience fading out over the last 2 s. | — |
| 0:65.75–0:66.00 (1578–1583) | cut | Black (#141414). | Fade. | — |

## Ledgers

**Equality fixture (EQ)**
- Art-only sha256 is identical across the 8 page panels.
- Art-only sha256 is identical across every frame of all 8 film panel slots: 1 distinct hash per slot, equal to the plate.
- Every hold frame equals its page panel pixel for pixel, art and lettering.
- Page panel = plate + balloon PNG, so I2 holds.
- Strings: A has 3 distinct strings plus the A3 Silence DialogueBeat; B has 4.
- Negative controls all FAIL strict mode:
  - plate pasted at x+1 in B3 (43,346 px differ);
  - plate-crop1px.png;
  - plate-mouth-redraw.png in B4 (955 px).

**Sound (CUE)**
- 373 cues from `cues.build(s1=dict(stamp_t0=6.75, header_t0=7.8333))`.
- Scheduled onset vs stroke onset is at most 1.0 frame; measured, at most 0.029 frame.
- One grain per stroke in every lettered panel. A3: 0 cues. B4 pen hold: 0 cues.
- No cue falls in a post-balloon hold.
- 86 footer grains are added in the film script.
- Nothing is synthesized.

**Credits:** `films/credits/moins-dun-quart-de-seconde-pour-vivre.json`.
- Writing with inkpen.ogg: PD, stephan / pdsounds.org.
- Grillenzirpen Mödling: CC BY-SA 4.0, DrTrumpet.
- The licences were re-read from Commons extmetadata by the sound unit on 2026-11-17. The editor's re-query was rate-limited (HTTP 200 "too many requests"), so it was not repeated.

## Departures and notes
- Panel starts are rounded to whole frames (A2, A3 and A4 start 0.017 s before the plan's 15.6, 21.6 and 26.6 s), as the sound unit also does. The A3 silence therefore lasts 4.42 s.
- The footer is not in the plan's S1. It is written on in S5 (58.5–61.0) so that no lettering appears all at once.
- During write-on, the page header and labels are re-brushed with the letterer's brush and seeds. At completion the published PNG is shown, which differs from the re-brush by at most 6 grey levels at stroke edges: letter.py was edited after the PNGs were saved. This is invisible, and balloons are unaffected: their final frames are byte-equal to the PNGs.
- The 2-frame pen lift between strokes is applied between words and lines (writer-letterer amendment 1).

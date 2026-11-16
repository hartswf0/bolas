# Status: la-cite-raymond-queneau (montage editor, repair round 1, 2026-11-16)

## Current preview
- Reel, A first: `assets/films/la-cite-raymond-queneau.mp4`, 75.0 s, 960×540, 5.04 MB (poster `.webp`).
- Reel, B first: `out/reel-BA.mp4`, 75.0 s, 5.04 MB.
- Blind screening sequences (silent control, then two unlabelled passes, no captions): `out/screening-S-A-B.mp4`, `out/screening-S-B-A.mp4`.
- Fixtures: `out/edition-{A,B,X,C}.mp4`, `out/control-silent.mp4`; captions `out/{A,B,X}.vtt` (written editions, fiction) and `out/{A,B,X}-speech.vtt` (recorded speech only: empty this round).

## Revisions
| revision | state |
|---|---|
| `2d659ecc16bf5d13b47eb3729b08d40a1fb54ff9` (r2) | **current, accepted, protected**; unchanged in this round |
| `e467efc03aba944aa00e1281895f888a45c831e3` (r1) | superseded, archived in `out/revisions/` |

## Acceptance (plan §9)
| # | condition | status | value |
|---|---|---|---|
| 1 | Picture identity | **measured, pass** | A, B, X, C, silent: 720/720 framemd5 vs master (960×464, tb 1/24). Screening sequences: each 720-frame segment md5-equal. Reel passes sha1-equal 720/720 before encoding; decoded PSNR rows 0–463: 99 dB (identical) in AB and BA. |
| 1b | Negative controls | **measured, all FAIL as required, deleted** | one-frame shift 0/720, frame 0 dropped 0/720, burned caption 0/720 |
| 2 | Loudness | **measured, pass** | final mp4 ebur128: A −23.0 LUFS / −2.1 dBTP, B −23.0 / −2.9, X −23.1 / −2.1, C −23.1 / −3.9; silent = digital zero. Reel passes −24.0 / −24.0 LUFS after kit's master gain (0.0 LU apart). Per-stem gains and loudness in `out/mix.json`. |
| 3 | Window score timing | **measured, pass** | B: relay clicks at 0 ms declared, measured onset ≤ +6 ms. A: 22 cues, offsets 120–400 ms, std 87.9 ms, **no consecutive repeat by source** (fixed: f406 orchestral 78, f427 creak, f470 distant door). |
| 3 | Locatable beat, perceptual | **pending, fresh viewers** | captions no longer state the reading; the reel bands are blank in both passes |
| 4 | Crossover 16.0–17.5 s, stem isolation | **measured, pass** | A: music only (−8.8 dBFS, others −240). B: voice stem only (−14.3, others −240). |
| 4 | Crossover: real radio speech on f384 | **FAIL (remaining failure)** | `cuemap-compare.json` `B_crossover_real_speech.pass = false`: f384 carries a handmade squelch, not speech. Lingua Libre downloads refused with HTTP 429 throughout this round. |
| 5 | Frame-by-frame animation | structurally verified (picture unit) | walker joint angles f200–362, P6/P1 = 6.7 |
| 6 | Numeric aesthetic, 4.0 s | measured, pass (r2, unchanged) | `out/aesthetic-check.json` |
| 7 | Perceptual side-by-side | pending review | `out/side-by-side.jpg` (internal only: contains the reference still) |
| 8 | Provenance | **structurally verified** | 18 credits, PD/CC0/CC BY/CC BY-SA (+ LoC "no known copyright restrictions"); every BY/BY-SA author in the note and on the reel's 72–75 s card; derived soundtracks B, C and reel declared CC BY-SA 4.0 |
| 8 | Fiction label | **done** | title card 0–2.5 s; VTT FICTION notes; real street name removed from a1 |
| 8 | Fresh-viewer readings | **not run** | `out/readings.json`: protocol, empty readings (no viewers available to an automated editor; nothing invented) |

## Remaining failures
1. **No real speech** in any edition (condition 4's radio speech; A's "toi", "bonsoir", "bonne nuit"). Every file is licence-verified and wired; see the re-run order in `assembly.md`.
2. **No fresh-viewer readings** of the silent control, A, B or X.
3. Picture defects carried from the picture unit (protected master, not reopened): S4 lamp head at the top edge with a faint pool; walker ~25–30 px tall; near-block roof partly cropped at 4.0 s.

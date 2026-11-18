# Status: la-cite-raymond-queneau (montage editor, repair round 2, 2026-11-16)

## Current preview
- Reel, A first: `assets/films/la-cite-raymond-queneau.mp4`, 75.0 s, 960×540, 4.13 MB.
- Reel, B first: `out/reel-BA.mp4`, 75.0 s, 4.13 MB.
- Blind screening sequences (silent control, then two unlabelled passes, no captions): `out/screening-S-A-B.mp4`, `out/screening-S-B-A.mp4`.
- Fixtures: `out/edition-{A,B,X,C}.mp4`, `out/control-silent.mp4`.
  - Each mp4 carries only a transcript of real recorded speech (B and X: one cue).
  - The written editions, which are fiction, are sidecars: `out/edition-{A,B,X}.written-fiction.vtt`, identical to `out/{A,B,X}.vtt`. Each opens with a NOTE FICTION, and none has a line at 16.0–17.5 s.

## Revisions
| revision | state |
|---|---|
| `90f1417b48de31c0113ca2ec2e874d1bf3f9d2ec` (r3) | **current, accepted**: fuller curved zinc roofs (rise 6.6 m), lower facades, cut-edge highlights and 1–2 px contact shadows, more visible paper fibre, wider boulevard, camera further back; S2 is a 3.4× longer lens from the same eye-level position (walker 90–110 px tall); lamp lowered, pool brighter. **No event frame changed** (`event_frames_changed: []`). |
| `2d659ecc16bf5d13b47eb3729b08d40a1fb54ff9` (r2) | superseded, archived with its editions and reels in `out/revisions/r2-2d659ecc/` |
| `e467efc03aba944aa00e1281895f888a45c831e3` (r1) | superseded, archived |

## Acceptance (plan §9)
| # | condition | status | value |
|---|---|---|---|
| 1 | Picture identity | **measured, pass** | A, B, X, C and silent all match the master at 720/720 framemd5 (960×464, tb 1/24). Screening segments match 720/720 each. Reel passes are sha1-equal at 720/720 before encoding, with decoded PSNR on rows 0–463 at min 78.4 dB and mean 98.9 dB (AB and BA). |
| 1b | Negative controls | **measured, all FAIL as required, deleted** | one-frame shift 0/720, frame 0 dropped 0/720, burned caption 0/720 |
| 2 | Loudness | **measured, pass** | Final mp4s: A −23.0 LUFS / −2.1 dBTP, B −23.0 / −3.6, X −23.1 / −2.8, C −23.0 / −3.8; silent is digital zero. Reel passes are −24.0 / −24.0 LUFS (0.0 LU apart). |
| 3 | Window score timing | **measured, pass** | B: relay click on every window frame, onset ≤ +6 ms. A: offsets 120–400 ms, std 87.9 ms, no consecutive repeat by source. |
| 3 | Locatable beat, perceptual | **pending: fresh viewers** | `out/readings.json` NOT RUN |
| 4 | Crossover 16.0–17.5 s, stem isolation | **measured, pass** | A: music only (−8.8 dBFS, the other stems −240). B: voice only (−10.1, the other stems −240). |
| 4 | Crossover: real speech at f384 | **measured, pass (structural)** | `B_crossover_real_speech.pass = true`. The source is LoC National Jukebox "French lesson no. 1" (Victor 1917, US PD), a 1.25 s phrase radio-filtered, onset +50 ms after a squelch on f384, 97.8 % of its energy in 300–3000 Hz. Captioned in B/X as « [radio : une voix d'homme, mots indistincts] ». Whether the words are intelligible was not checked by ear. |
| 5 | Frame-by-frame animation | structurally verified | walker FK joint angles f200–362 (now legible at ~100 px in S2); window-16 silhouette rise, head turn and curtain |
| 6 | Numeric aesthetic, 4.0 s (decoded r3) | **measured, pass** | sky (241,233,239); facade (181,184,169); roof (93,104,109), luma 101; luma p2/p50/p98 61.5/120.2/236.3; sat 20.3 |
| 7 | Perceptual side-by-side | pending review | `out/side-by-side.jpg` (internal only: it contains the reference still) |
| 8 | Provenance | **structurally verified** | 19 credits, all PD / CC0 / CC BY / CC BY-SA, each with a licence URL and an "adapted" marker. The LoC sheet is PD under a stated basis (blank sheet, no copyrightable expression). The Victor credit is corrected (no arranger). Typefaces are OFL (`out/typeface-credits.json`, reel card). |
| 8 | Fiction label | **done** | Title card; NOTE FICTION in every written VTT; written editions are no longer muxed as default subtitle tracks |
| 8 | Reel does not state readings | **done** | the end card says only "soundtrack A / soundtrack B"; the readings live in plan/readings.json |
| 8 | Fresh-viewer readings | **not run** | protocol only; nothing invented |

## Remaining failures
1. **No fresh-viewer readings** (conditions 3, 4-X, 8d). An automated editor cannot supply them.
2. **The Lingua Libre French words are still missing.** "quarante-sept", "toi", "bonsoir" and "bonne nuit" all returned HTTP 429 from upload.wikimedia.org throughout this round (11 spaced attempts, 05:46–06:12). B's radio voice is a real but indistinct 1917 phrase. A still uses hums in place of words, with no captions.
3. The cut-paper look is still a computed paper model, not a photographed one. The perceptual judgement is pending.

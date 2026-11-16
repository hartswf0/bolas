# La belle Hortense: assembly, revision E3 (editor repair round 2)

Film: `assets/films/la-belle-hortense.mp4`, 66.0 s, 960×540, 24 fps, 5.0M (5 146 115 bytes). Script: `films/la-belle-hortense.py` (kit.Film; kit.py not edited). Structure: S3 (S2 with re-staged on-screen text for I.4, II.2, II.6 and III.4, and the II.2 caption naming the conductor). `verify.py structure.json` passes (`verify_S3.txt`); `verify.py baseline.json` fails 14 checks. At render time the script asserts σ(ABCDEF) = FAEBDC, σ⁶ = id, no duplicate motif in any module, and that the red slot word equals order_i[k] at every slot midpoint.

## Sequence

0.0–3.0 s, title: TITLE_E3 is a pan exposure over the V.3 run stage (MEADOW + SHED strips, 40 sub-frames over 160 px of travel per frame, one fixed print curve). The type block is Hortense Slab: "Jacques / Roubaud" in black, stacked above "La belle / Hortense" in red, then the sextine lines and the fiction label.

| slot | time (s) | motif | function | clip | evidence | clue |
|---|---|---|---|---|---|---|
| I.1 | 3.0–4.5 | MANTEAU | background | I1_manteau_E3 | COND (dyed coat panel) + MEADOW | K0 |
| I.2 | 4.5–6.0 | CLOCHE | action | I2_cloche_E3 | BELL, BELL-SND + MEADOW | – |
| I.3 | 6.0–7.5 | CLÉ | action | I3_cle_E2 | KEY + MEADOW | – |
| I.4 | 7.5–9.0 | BANC | action | I4_banc_E3 | BENCH + MEADOW | K1 |
| I.5 | 9.0–10.5 | REÇU | action | I5_recu_E3 | TICKET/print RECEIPT, PAPER + MEADOW | – |
| I.6 | 10.5–12.0 | PORTE | background | I6_porte_E3 | SHED, HANDLE/HINGE/LOCK + MEADOW | – |
| II.1 | 12.0–13.5 | PORTE | action | II1_porte | SHED, HANDLE/HINGE/LOCK + MEADOW | – |
| II.2 | 13.5–15.0 | MANTEAU | action | II2_manteau_E3 | COND (dyed coat panel) + MEADOW | K2 |
| II.3 | 15.0–16.5 | REÇU | evidence | II3_recu | TICKET/print RECEIPT, PAPER + MEADOW | K4 |
| II.4 | 16.5–18.0 | CLOCHE | action | bell_strike | BELL, BELL-SND + MEADOW | – |
| II.5 | 18.0–19.5 | BANC | absence | bench_empty | BENCH + MEADOW | K3 |
| II.6 | 19.5–21.0 | CLÉ | absence | II6_cle_E3 | KEY + MEADOW | – |
| III.1 | 21.0–22.5 | CLÉ | false-lead | III1_cle_E2 | KEY + MEADOW | – |
| III.2 | 22.5–24.0 | PORTE | evidence | III2_porte | SHED, HANDLE/HINGE/LOCK + MEADOW | K9 |
| III.3 | 24.0–25.5 | BANC | evidence | bench_empty | BENCH + MEADOW | K5 |
| III.4 | 25.5–27.0 | MANTEAU | background | III4_manteau_E3 | COND (dyed coat panel) + MEADOW | K6 |
| III.5 | 27.0–28.5 | CLOCHE | evidence | bell_strike | BELL, BELL-SND + MEADOW | K7 |
| III.6 | 28.5–30.0 | REÇU | evidence | III6_recu | TICKET/print RECEIPT, PAPER + MEADOW | K8 |
| IV.1 | 30.0–31.5 | REÇU | evidence | IV1_recu | TICKET/print RECEIPT, PAPER + MEADOW | – |
| IV.2 | 31.5–33.0 | CLÉ | false-lead | I4_banc_E3 | KEY + MEADOW | K10 |
| IV.3 | 33.0–34.5 | CLOCHE | false-lead | bell_strike | BELL, BELL-SND + MEADOW | – |
| IV.4 | 34.5–36.0 | PORTE | evidence | IV4_porte | SHED, HANDLE/HINGE/LOCK + MEADOW | K11 |
| IV.5 | 36.0–37.5 | MANTEAU | action | IV5_manteau_E2 | COND (dyed coat panel) + MEADOW | – |
| IV.6 | 37.5–39.0 | BANC | absence | bench_empty | BENCH + MEADOW | – |
| V.1 | 39.0–40.5 | BANC | action | V1_banc_E2 | BENCH + MEADOW | – |
| V.2 | 40.5–42.0 | REÇU | action | V2_recu_E2 | TICKET/print RECEIPT, PAPER + MEADOW | – |
| V.3 | 42.0–43.5 | MANTEAU | evidence | V3_manteau_clean | COND (dyed coat panel) + MEADOW | R1 |
| V.4 | 43.5–45.0 | CLÉ | evidence | V4_cle_E2 | KEY + MEADOW | R2 |
| V.5 | 45.0–46.5 | PORTE | action | V5_porte | SHED, HANDLE/HINGE/LOCK + MEADOW | – |
| V.6 | 46.5–48.0 | CLOCHE | action | bell_strike | BELL, BELL-SND + MEADOW | – |
| VI.1 | 48.0–49.5 | CLOCHE | closure | VI1_cloche | BELL, BELL-SND + MEADOW | – |
| VI.2 | 49.5–51.0 | BANC | evidence | I4_banc_E3 | BENCH + MEADOW | – |
| VI.3 | 51.0–52.5 | PORTE | closure | VI3_porte | SHED, HANDLE/HINGE/LOCK + MEADOW | – |
| VI.4 | 52.5–54.0 | REÇU | closure | VI4_recu | TICKET/print RECEIPT, PAPER + MEADOW | – |
| VI.5 | 54.0–55.5 | CLÉ | closure | VI5_cle | KEY + MEADOW | – |
| VI.6 | 55.5–57.0 | MANTEAU | background | I1_manteau_E3 | COND (dyed coat panel) + MEADOW | – |

57.0–66.0 s, end card: the six orders as rows, with the braid strands (coat in red), σ⁶ = id, the fiction label and the credits. It is all set in Hortense Slab (print.json ENDCARD + editor/cards.py).

Evidence IDs: COND = LoC 2017844115; VISITOR-F/-B = LoC 2017750548/2017750547; BENCH = LoC 2013633886; SHED/MEADOW = Bourré 50866795131/50866798791 (CC BY 2.0); BELL = Bahnhofsglocke HLB 1 (PD); KEY = Skeletonkey.png (CC0); ENVELOPE-LOC = LoC 2010652109. Sounds: BELL-SND, STEPS, HANDLE, HINGE, LOCK, KEYS-SND, PAPER (scenes.json evidence.foraged). Handmade items are in print.json: RECEIPT, PLATE6, SLOT-TYPE, REPLAY-TAG, ENDCARD, HOOK, KEY-OUTLINE, TYPEFACE. The rigs and dye are RIG, RIG-E3 and DYE in scenes.json.

## E3 changes (from the critic's and reviewer's round-2 lists)

- **I.4 (7.5–9.0).** The visitor stands clear of the bench's left end; the gap measured from her body to the bench is ≥ 30 px in every frame. Her upper arm (newly cut from the body along the sleeve) and her forearm hinge out over the coat. The key hangs from her hand by its bow, is let go at 0.50 s, falls on g = 2600 px/s² onto the open folded skirt, rocks and lies. The coat is now 0.30 scale on the bench's left half, in every I-module shot.
- **II.2 (13.5–15.0).** The conductor (cap; his own print undyed and narrowed, so he wears no coat) walks in and reaches out. He closes his hand on the collar, steps back with the coat, and the key's bow glints in the fold for frames 17–22. He swings the coat on, becomes the red-coated figure, and walks off. The caption is "Le contrôleur reprend son manteau. / The conductor takes back his coat."
- **II.6 (19.5–21.0).** A red grease-pencil outline of the key on the empty seat, beside the receipt with "une clé" struck through. The motif CLÉ is now shown.
- **III.4 (25.5–27.0).** The runner is in the middle plane at 0.275 scale, about 28 % of frame height.
- **Type.** Courier 10 Pitch and the DejaVu σ are gone. All type is Hortense Slab, drawn for this film (editor/typeface.py → sources/…/editor/type/). print.py, cards.py and the slot, receipt, plate and end-card PNGs were re-rendered, and so was every clip with baked type (II1, II3, III2, III6, IV1, IV4, VI3, VI4, I5, V2).
- **Records.** print.json has HOOK, KEY-OUTLINE and TYPEFACE. scenes.json evidence is at E3: ENVELOPE-LOC and KEYS-SND, HANDLE, HINGE, LOCK, PAPER and BELL-SND have been added; the typed envelope, the "key tinks synthesised" absence and FONT are marked superseded. The credits credit the V.4 grass crop to Bourré 50866798791. ledger.json editor_E3 records the live Commons re-check of 2026-11-16 (review-2/commons_retry.txt). The fiction label has been widened to cover Highsmith, Jolivet and the 1861 envelope.

## Silhouette checks (SCION 2)

`sources/…/editor/checks/sil_board_E3.png`, `sil_E3.json`:
- **I.4.** The figure and the bench are separate shapes, with the arm bridging to the coat.
- **II.2.** The conductor is a separate figure: at 0.30 s (entering), at 1.10 s (wearing the coat) and at 1.35 s (walking off). He touches the bench only at the grab (0.62 s).
- **V.3.** The test shot is unchanged.

## Measured on the final film's frames

From `sources/…/editor/measures/final_film.json`, measured on encoded mp4 frames rather than from the test shot: key g 2919.5 px/s² (authored 2600), RMS 3.1 px over 6 frames, axis rotation -253.4 °/s; bell τ 2.2 s, f 1.06 Hz, amplitude 24.9°; parallax far/mid/ground/near 61.2/104.9/175.5/280.5 px/frame; pivot max 3.5e-13 px.
- The key's axis angle is mod 180° on a blurred, partly occluded blob, so its rotation rate is indicative only. The fall is a clean parabola.
- The bell τ is longer than the authored 1.5 s because the clapper is included in the mask.

## Claim graph

S = "the conductor carried the key away in the fold of his coat".
- **Supports:** K0 (I.1, 3.0), K1 (I.4, 7.5), K2 (II.2, 13.5) and K3 (II.5, 18.0), all before 21.0 s.
- **Corroborates:** K6 (III.4) and K10 (IV.2 replay).
- **ALT-1 (the visitor took it back)** is refuted by K4 (II.3) and K8 (III.6).
- **ALT-2 (a thief)** is refuted by K9 (III.2) and K11 (IV.4).
- **ALT-3 (the bell)** is refuted by K5 (III.3) and K7 (III.5).
- **Reveals** R1 (V.3) and R2 (V.4) are typed as reveals and are not necessary supports.

## Fresh reader

Reader R1, a separate Claude session that had never seen the film or its files, was given stills from 0 to 39.0 s without sound and stopped at 39.0 s. The full record is in `reader-log.md`.

- **Q1.** The key is in the red coat's fold or pocket, carried off by the conductor.
- **Q2.** The coat, at 8.25 s and 14.25 s, plus the I·4 replay.
- **Q5.** I.4.
- **Confidence.** 75.
- **Q7.** The rotating order was noticed.

Score: **solved, fair-play pass**. This is perceptually judged: the reader is a model working from stills, not a human watching with sound.

## Baseline

`films/swarm/la-belle-hortense/la-belle-hortense-baseline.mp4` (15.5 s): story order, no coat in I, so the reveal is unsupported. verify.py rejects baseline.json with 14 failed checks.

## Stills and boards

- Stills: `films/stills/la-belle-hortense/{001.50,003.75,008.25,014.60,020.25,021.00,026.25,031.75,039.00,043.30,060.50}.png`.
- Boards beside hortense.webp: `board-43.3.jpg` and `board-title.jpg`.

## Known weaknesses

- **Visitor.** She is a small, soft source (about 1.1× upscale). Her raised arm has a straight cut edge where the sleeve was separated.
- **II.2 conductor.** His no-coat state is his coat print, darkened and narrowed. It reads as a dark jacket, not a different garment. The coat swing-on is a 0.22 s slide plus a 0.12 s cross-dissolve to the red rig, which is a replacement cut rather than a fully articulated dressing.
- **I.4 silhouette.** The key on the coat is inside the coat's silhouette. It reads as a separate shape only while it hangs from her hand.
- **Tonal range.** The film's highlights are still short of the cover's (p95 about 163 against 228).

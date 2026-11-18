# La Machine à tuer le temps: assembly (montage editor)

**Revision: repair round 2.** Film script `films/la-machine-a-tuer-le-temps.py`, built against:
- pool_hash `7e50704ce76934d73e25d32ad82b9fdb6e9db4e7ae0cacb560fcea0f49745164` (pool-manifest.json, unchanged since round 1)
- recipes A1 and B1 (edit-recipes.json; B1 re-timed in round 2: 02 held 96 f, 08 72 f, cut B still 564 f)
- `notebook_rig.py` (U2, amended in round 2: cover centred, S5 locked on the spread, caption 03, B tape)
- sound stems v2 (`sound_build.py` + `sound_crowd.py`, sound-edit.json version v2)

**Exports**
- **Film (screening 2):** `assets/films/la-machine-a-tuer-le-temps.mp4`. 67.00 s, 1608 frames, 1280×720, 24 fps, 3.67 MB. Poster `…webp` = film frame 869 (the re-numbered spread with the tape "B : récit inventé").
- **Shared-bed export (screening 1):** `assets/films/la-machine-a-tuer-le-temps-shared-bed.mp4`. 67.00 s, 1608 frames, 3.67 MB.

**Ledger:** `swarm/la-machine-a-tuer-le-temps/render-ledger.json`, one entry per output frame (md5 of the RGB24 frame handed to ffmpeg).

**Timeline.** As built, 1608 f (67.0 s); plan.md §7 and §13 now carry these ranges (amendment at the end of §13). S5 is 216 f because one print per page needs four page turns.

## Timecoded sequence → evidence

Evidence IDs: LoC-01…LoC-08 = pool-manifest `evidence[id]` (Jack Delano, 1943, FSA/OWI, "No known restrictions"); mia-ef7bfc89 (Wreckless, 1935) and mia-a11ba534 (Valley Town, 1940) = sound-edit `evidence_foraged` (Prelinger, archive.org PD mark re-read 2026-11-16); H-* = handmade.

| seg | timecode | frames | picture (source) | evidence | sound: film / shared-bed |
|---|---|---|---|---|---|
| S0 | 0:00.00–0:03.00 | 0–71 | The closed oxblood cover, centred in frame, felt-pen title "LA MACHINE / À TUER / LE TEMPS" and "8 PHOTOGRAPHIES / 2 MONTAGES . 1 POOL"; the cover flips at 2.25 s (6 drawings) while the camera eases onto the spread | H-cover, H-felt-pen | T0 room (mia-ef7bfc89) + T2 cover flap; identical |
| S1 | 0:03.00–0:06.00 | 72–143 | Spread p.1–2: prints 01 and 02 pasted with typed tapes, ink "1"/"2", red "A" and page numbers; locked off | LoC-01, LoC-02, H-notebook, H-tape, H-pen | T0 + T1 preroll (concourse fades in); identical |
| S2 | 0:06.00–0:06.75 | 144–161 | Push in on page 1, ending on asset 01 frame 0 | LoC-01 | bed rises; identical |
| S3 | 0:06.75–0:26.75 | 162–641 | **CUT A** (A1, 480 f), frozen pool PNGs 01→08. Starts: 01 @6.75, 02 @9.25, 03 @12.25, 04 @14.75, 05 @17.25, 06 @19.25, 07 @21.75, 08 @24.75 | LoC-01…08 | film: T3 mix A (warmed concourse, bustle under 02, latch on the 04 cut, whistle mia-a11ba534 under 07) / shared: T1 concourse bed |
| S4 | 0:26.75–0:27.50 | 642–659 | Pull out from asset 08 (src 47) to spread 4 | LoC-08 | T1 bed fall; identical |
| S5 | 0:27.50–0:36.50 | 660–875 | **TEST SHOT: the re-shuffle**, framed on the spread (83 % of frame width). Riffle back to spread 1; twelve lift/travel/set-down moves, translation only, cards carried off frame to the table parks and brought back; spring settles, lift shadows; red-pencil strikes and stroke-by-stroke new numbers (02→3, 03→5, 01→6, 06→4, 05→1, 04→2); "A" struck, "B" written, then the typed tape "B : récit inventé" laid on page 1 (local f 190); hold | LoC-01…08 (cards), H-notebook, H-red-pencil, H-tape | T2 foley on 85 events; identical |
| S6 | 0:36.50–0:37.25 | 876–893 | Push in on page 1 (now 05 under a red "1", the B tape above) to asset 05 frame 0 | LoC-05 | bed rise; identical |
| S7 | 0:37.25–1:00.75 | 894–1457 | **CUT B** (B1, 564 f). Starts: 05 held @37.25 (5.0 s, each pool frame twice), 04 @42.25 (2.0 s), 02 @44.25 (**4.0 s**, src 24–119: the push lands on her look back over the box), 06 @48.25 (3.0 s, the slips on the counter), 03 @51.25, 01 pulling back from the clock @53.75, 07 @55.25, 08 @57.75 (3.0 s) | LoC-05, 04, 02, 06, 03, 01, 07, 08 | film: T4 mix B (bed −9 dB; declared silence cut f 60–119; latch 6 f before 04; **close footsteps pre-lap 02 by 14 f**; **parcel set down 5 f before 06, a paper slip drawn across the counter 2 f before 06**; tick hard on 06, under 03, alone on 01; footsteps pre-lap 07; tail to zero under 08) / shared: T1 bed at the same cut-relative offset as in A |
| S8 | 1:00.75–1:01.50 | 1458–1475 | Pull out from 08 (src 71) to spread 4 | LoC-08 | room tone only; identical |
| S9 | 1:01.50–1:02.50 | 1476–1499 | A loose sheet slides in over spread 4 (translation, leading shadow) | H-sheet | paper slide; identical |
| S10 | 1:02.50–1:07.00 | 1500–1607 | **Coda:** ink columns A 01–08 and B 05 04 02 06 03 01 07 08; 8 red-pencil lines at 6 f each; typed tape "même pool . sha256 7e50704c...5164 . 42 -> 8"; typed label (S9–S10, ≈4.6 s): "Photographies : Jack Delano, 1943, FSA/OWI, Library of Congress. Légendes et récit B inventés ; les personnes photographiées n'y ont aucune part." | H-coda | pencil per line; T0 ends on one clock tick at f 1584; identical |

## Ledger and claim graph (plan §4, §13)

```
LoC master TIFF (sha256, LoC-0k) ──print_op + window_path──▶ asset k frames 0..119 (frame_md5) ──▶ pool_hash 7e50704c…
pool_hash ──▶ recipes A1, B1 (base_pool_hash) ──expand──▶ S3/S7 ledger rows {edit_id, asset_id, src_frame, md5}
                                                        └─ md5 == pool frame_md5 (1044/1044 rows)
master pyramid ──sample_print(k) at one table scale──▶ notebook prints (print_md5 const, rot 0, translation dx,dy)
notebook_rig events.json (85) ──▶ T2 foley cues;  recipe cut_points ──▶ T3/T4 cues (sync_dep: edit_id + event)
picture stream ──identical──▶ film.mp4 + shared-bed.mp4 (framemd5 1608/1608 equal); audio differs only in S3/S7
```

**Measured (logs in `sources/…/assembly/`: validate-log.txt, measures.json, bed-check.json, pcm-identity-r2.json, compare.jpg)**

1. **Pool membership.** `validate.py ledger render-ledger.json --recipes edit-recipes.json`: PASS. 1044 cut frames, md5 = manifest frame_md5; A1/B1 equal the expanded recipes, contiguous; cut_points film frames checked. 564 notebook frames: rot 0, one table scale per asset, constant print_md5; leaf-turn frames flagged `turning`.
2. **Recipes.** `validate.py recipe edit-recipes.json --full-pool A1 B1 --sound sound-edit.json`: PASS (every v2 cue's sync_dep names a real event).
3. **Fixture.** `validate.py all`: PASS, failure cases fail as they should.
4. **Audio-only replacement.** `validate.py framemd5 film shared --expect-audio-differs`: PASS, 1608/1608 frames; pre-encode md5s equal in-process. Pre-encode int16 PCM bit-identical in S0, S1, S2, S4, S5, S6, S8, S9, S10.
5. **Acceptance 4 (decoded mp4).** S1 page L (238,228,204) / R (241,231,207), tape band (226,196,149), red R−G 101 (S1) / 124 (S5 end), S0 cover (96,12,22): all in band.
6. **Acceptance 5 (decoded mp4).** S3 01/02/04/07 and S7 05/04/02/01/08: p1 18.7–30.7, p99 213.7–221.7, median R−B +8…+13, all in band; B 05 hold in identical pre-encode pairs.
7. **Form.** 67.0 s; cut A 20.0 s, cut B 23.5 s; every B projection ≥ 1.5 s, 05 glance 5.0 s, 02 now 4.0 s; coda 4.5 s with all 8 lines and the hash; mp4 3.67 MB; poster from S5.
8. **Bar 9 (new, the critic's falsifiable sound test)** on the delivered mp4 audio: shared-bed export S3 RMS p10–p90 7.7 dB, S7 7.6 dB, longest narrowband line 0.51 s; film S3 8.8 dB / 0.60 s, S7 28.4 dB / 0.28 s. All pass (≥ 6 dB, ≤ 3 s). Method: 250 ms RMS windows; STFT nfft 8192, hop 2048, line = bin > 20 dB over the ±40-bin local median.

## Picture-reuse report

| asset | A frames (src) | B frames (src) | src shared A∩B | src never projected |
|---|---|---|---|---|
| 01 | 60 (0–59) | 36 (119→84 rev) | 0 | 24 |
| 02 | 72 (0–71) | 96 (24–119) | 48 | 0 |
| 03 | 60 (0–59) | 60 (0–59) | 60 | 60 |
| 04 | 60 (0–59) | 48 (0–47) | 48 | 60 |
| 05 | 48 (0–47) | 120 (0–59, each twice) | 48 | 60 |
| 06 | 60 (0–59) | 72 (30–101) | 30 | 18 |
| 07 | 72 (0–71) | 60 (0–59) | 60 | 48 |
| 08 | 48 (0–47) | 72 (0–71) | 48 | 48 |

A and B hold the same asset multiset {01..08}, each once. No inserts.

## Accepted edit checkpoint

A1 + B1 (round-2 timing), mix A and mix B v2. Branches B2, B3 (round-1 timing) and B4 (picture = B1) stay on file in edit-recipes.json, not rendered.

## Repair round 2 (critic + reviewer)

| finding | change | evidence now |
|---|---|---|
| T1 bed static synthetic noise, brick-wall shelves, steady lines, hum | concourse rebuilt from events in `sound_crowd.py`: 123 unintelligible talker utterances (drifting glottal source, a new vowel each syllable, all-pole formant cascade, distance and air absorption) on a ±8 dB crowd swell; 9 passing walkers; 2 unintelligible PA fragments with slap echo; trolley, case set down, far steam; trains with noise-burst rail joints; two-band hall IR. Every filter in sound_build.py now smooth (Butterworth magnitude), no kit brick wall; the 60 Hz hum sine removed from T0. Commons Tampere still HTTP 429 (14:17) | bed-check.json: falsifiable test passes on stems and decoded mp4 (see 8 above) |
| B rests on one cue; no handoff | order and duration only: 02 held 3.0→4.0 s (src 24–119) right after 04, its push ending on her look back over the box; 06 (slips) follows directly; 08 shortened 4.0→3.0 s so cut B stays 564 f. Second decisive cue in sound (mix B): close footsteps pre-lap 04→02 by 14 f and arrive with her; the parcel set down 5 f before 06 and a paper slip drawn across the counter as 06 opens (parcel exchanged for paper) | edit-recipes.json repair_round_2, B1/B4 cut_points 0/120/168/264/336/396/432/492; sound-edit.json cues T4 at 154, 259, 262 |
| no fresh-viewer screening | **not run**: this assembler cannot recruit a human viewer, and a model reading its own film is not a fresh viewer. Protocol stays in plan §13.6: shared-bed export first, then the film; log cause, actor, cut | bar 6 pending |
| S0 stray mark after "LA", gap in "MACHINE", cover off-centre | the "À" accent lowered and lengthened so it reads as the accent of line 2, not a mark under line 1; the "I" stroke centred in its narrow advance (closes "MACH INE" and "PHOTOGRAPH IES"); S0 camera centred on the closed cover, easing onto the spread during the flip | S0 still in compare.jpg |
| S5 spread small, parked cards clipped | S5 locked on the spread view (spread = 83 % of frame width). Spread + two 808-px card stacks cannot fit at ≥ 75 %, so the parks are moved just outside the copy-stand frame: a parked card is never shown clipped; it is carried out of frame and brought back in (12-f travels). Checked: 0 S5 frames show a parked card in frame | rig check above |
| plan figures on 1584 f | plan.md §7 rows S5–S10, invariant 5, bar 2 and a §13 amendment now use the 1608-f ranges; bars 1, 2, 7 measured on them | plan.md |
| caption 03 over-claims | tape retyped "03.- Un contrôleur, sa montre à la main."; credits quote updated | credits entry 11 |
| disclaimer only at the coda | typed tape "B : récit inventé" laid on page 1 beside the red "B" (S5 local 190), visible in the S5 hold and the S6 push, before cut B | poster frame 869 |
| typeface and cover title not credited | handmade credit names Courier 10 Pitch © 1989–1992 Bitstream Inc. (xfonts-scalable, permissive notice read from the package copyright) and the cover title lettering | credits |
| sound-edit licence wording stale | evidence_foraged now carries the credits' PD-mark licence (re-read 2026-11-16) | sound-edit.json |

## Repair round 1 (critic + reviewer)

| finding | change | evidence now |
|---|---|---|
| B1 film frames stale by 24 | edit-recipes.json B* re-serialised from `notebook_rig.TL`: film_start_frame 894, cut_points 894/1014/1062/1134/1206/1266/1302/1362; B4 latch at film f 1026 | `validate.py ledger` now checks film_start_frame and every cut_points.film_frame; PASS; a copy with the old 870 values fails as it should |
| audio differs outside S3/S7 | mix A trimmed at cut f 480 with a 6 f crossfade into the T1 fall (S4 carries the T1 fall in both exports); mix B trimmed at 564; shared bed fades over cut-B f 552–563 (S8 empty in both); T0 room copied so A's and B's frames 0..479 carry the same samples, A dip now rises under S4 | pre-encode int16 PCM is bit-identical in S0, S1, S2, S4, S5, S6, S8, S9, S10 (sha256 per segment in `sources/…/assembly/pcm-identity.json`). Decoded AAC residual: S0/S1 exact, S8 −61.9 dB, S10 −58.8 dB, S2/S4/S5/S6/S9 −44 to −52 dB RMS (worst frame −36 dB at S5). These remain because kit's ffmpeg AAC at 96 kb/s carries encoder state across frames; the input is identical, so they are codec residue, not a mix difference |
| T1 sample identity unproven | hashed in-process | shared-bed export PCM over cut A f 0–479 = cut B f 0–479: sha256 462aa36f57aa39ec…6617 for both (array_equal True) |
| sync_dep {event:"end"} | sound_build.py and sound-edit.json now name event 7 with at:"out" | `validate.py recipe … --sound sound-edit.json` PASS unpatched |
| table jitter at rest | `notebook_rig.jitter` returns the view unchanged (locked-off copy stand) | 335 rest pairs identical pre-encode; decoded interframe difference on them mean 0.010, max 0.15 levels (half res); S1 mean 0.001; S5 final hold 0.000; coda hold ≤0.001 |
| 04 p1 / 01 p99 out of band | one levels change per asset in registrar_build.LEVELS_OVERRIDE: 04 lo 11→22, 01 hi 188→183; pool re-frozen (determinism re-checked, all 8 True), card prints and notebook pyramids rebuilt | decoded: 04 p1 28.7–30.7 (A f360/410, B f1020), 01 p99 215.7–220.0 (f165/215/1274); every checked shot in band (`assembly/measures.json`) |
| B picture cues invisible | claims withdrawn instead of re-cutting: 05 is declared a held print (5 s, each frame twice); 01 is a pull back from the clock, no "reversed clock" claim. B rests on order and duration: 05 (5 s stare) → 04 → 02 | recipes `why`/`reads_as`, credits used_as, note |
| invented captions styled as documentary | tapes cut back to what one photograph shows: 02 "Une femme porte un colis.", 04 "La porte d'un wagon ; un soldat sur le seuil.", 05 "Le porteur regarde l'objectif.", 06 "Des bons de réservation sur le comptoir.", 07 "Des soldats passent devant la voie 2.", 08 "…presque vide, à une heure du matin." 01 drops "on pointe" | the fiction label typed on the coda sheet, legible at 720p (≈17 px Courier) for ≈4.6 s |
| credits incomplete | archive audio now names producer/sponsor and the archive.org PD mark (re-read today from archive.org/metadata), clip file references, Valley Town whistle-only excerpt measured; two handmade entries (picture, synthesised sound) with the caption text and per-segment use | `films/credits/la-machine-a-tuer-le-temps.json`, 12 entries |
| note inaccurate | rewritten: "drawn … rendered", "reordered and retimed", no reception claim | `films/notes/la-machine-a-tuer-le-temps.txt` (110 words) |

## Known gaps

- **Bar 6 unscreened.** No fresh viewer has watched either export. The B reading now rests on 05 (5 s stare) → 04 → 02 (4 s look back) → 06 (slips), plus in mix B the latch before 04, the footsteps into 02 and the parcel/paper cue into 06. Still no frame shows a parcel changing hands; under the shared bed the picture carries it alone.
- **No foraged station sound.** The concourse, trains, tick, latch, footsteps and foley are synthesised (declared); Commons kept answering HTTP 429. The bed passes the critic's numeric test, but nobody has listened to it on speakers; its high band is dark (a distant hall) and the 1 Hz tick is prominent.
- **S5 parks are off frame** (a deliberate deviation from "parked cards fully in frame": the geometry does not allow both at ≥ 75 % fill).
- Decoded AAC audio still differs slightly outside S3/S7 although the PCM handed to ffmpeg is identical (kit's fixed 96 kb/s AAC carries encoder state).
- The editors' rough-cut B1.mp4 and its strip are of the round-1 timing; the film is rendered from the frozen PNGs and is authoritative.

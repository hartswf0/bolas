# La Cité Raymond Queneau: assembly (montage editor, repair round 1)

Master revision: **`2d659ecc16bf5d13b47eb3729b08d40a1fb54ff9`** (r2, protected, unchanged in this round). It replaced r1 `e467efc0…` (archived in `out/revisions/`) with one global mid-tone levels curve (gamma 0.93). No geometry, timing or event frame changed. Nothing in this repair touches the picture.

## What repair round 1 changed

| Finding | Repair |
|---|---|
| Captions printed the reading ('quelqu'un regarde la rue', 'Ici, tout le monde se connaît') over synth hum / squelch, so A/B was caused by words | The reel's band now carries **only transcripts of real recorded speech** (`out/{A,B,X}-speech.vtt`, built by `editor/speech_vtt.py` from cues whose source is a foraged speech recording). No speech recording could be downloaded, so both bands are blank paper and identical: a blind reading can only come from the sound. The written caption editions (fiction) stay in the edition files as a second, non-default subtitle track titled "written edition (fiction; not speech)", and are quoted only on the end table. |
| No real voice; f384 'voice' is squelch | **Not fixed.** upload.wikimedia.org and the Commons API answered HTTP 429 to every request again in this round (05:30 to the end of the round, spaced 150 s). Lingua Libre "quarante-sept" (Poslovitch, Estrie; CC0), "toi", "bonsoir", "bonne nuit" are licence-verified and wired: dropping them into `sources/.../sound-{A,B}/raw/` and re-running the steps below puts them in, captions them and flips the `B_crossover_real_speech` check. f384 in B is **a caption-free handmade radio squelch on the voice stem, not speech**. |
| cues-A consecutive repeats (f384/f406 music box, f470/f492 latch) and a false `consecutive_repeat` flag | f406 is now the orchestral 78 heard through a wall (music stem, so the crossover stays music-only), f427 a door-handle creak, f470 a distant door. The flag is now computed on `source_ledger_id` (the actual recording or generator), not on the label; `cuemap.py` checks the same and fails the map on any repeat. Result: no repeat, std 87.9 ms. |
| No silent control / blind sequence | `out/screening-S-A-B.mp4` and `out/screening-S-B-A.mp4`: silent control, then the two passes, no captions, no labels (each 720-frame segment md5-equal to the master). |
| No viewer readings | **Not run**: no fresh human viewers are available to this agent. `out/readings.json` holds the protocol and an empty readings list; nothing is invented. |
| mix.json had 0.0 stem gains with a pointer | `out/mix.json` now lists, per edition and stem, the team pre-gain, the editor gain, the total from unity and the stem's measured loudness/true peak in that mix. |
| Credits not where the reel said; no derived-work licence | Reel gains a 72–75 s attribution card (all six CC BY / BY-SA items with author, licence, URL; the CC BY-SA 4.0 licence of editions B, C and the reel; the LoC credit line). The note carries the same block. |
| LoC licence overstated | Now "No known copyright restrictions (Library of Congress rights statement); used as public domain", credit line "Library of Congress, Music Division, Federal Theatre Project Collection". |
| Victor 78 credited as 'Carl Flisch', called 'a song' | Victor Schrammel-Orchester (performers), Millöcker (composer, « O, du himmelblauer See »), Carl Flisch (arranger), via publicdomainproject.org; "orchestral 78" everywhere. |
| Fiction not labelled; real street name in caption a1 | Title card (0–2.5 s): "fiction: a paper model, not the real estate; any names and logs are invented" and "no voice is recorded: the passes carry no captions; listen". a1 no longer names the street. Both VTTs open with a FICTION note. |

## Screening reel: `assets/films/la-cite-raymond-queneau.mp4` (75.0 s, 960×540, 5.04 MB)

| reel time | segment | content | evidence IDs |
|---|---|---|---|
| 0.0–2.5 | title card | lineage "after La Cité Raymond Queneau, Azam & Firode 1998"; "one picture, two soundtracks"; fiction and no-voice labels; silent | (none) |
| 2.5–4.0 | card "1" | unlabelled as to reading; silent | (none) |
| 4.0–34.0 | pass 1 = edition A | master frames 0–719 pasted pixel-exact into rows 0–463; rows 464–539 blank paper band (speech-only captions: none heard); sound `mix-A.wav` | picture: paper-loc-blank, paper-kraft, paper-vintage + HANDMADE model. A: latch_open, door_close, handle_creak, faucet, footstep, car_pass, kettle, radio_song + HANDMADE wind, room tone, bag rustle, music box, cupboard, spoon, hums |
| 34.0–35.5 | card "2" | silent | (none) |
| 35.5–65.5 | pass 2 = edition B | same 720 frames (sha1 equal 720/720 before encoding; decoded PSNR 99 dB, identical); same blank band; sound `mix-B.wav` | B: click_heating, typewriter_wws, typewriter_ding, shutter_holga, wind_pine, hum_mainsbrum, metro_buzzer + HANDMADE drone, radio squelch |
| 65.5–72.0 | end table | which pass was A/B; picture identity; framemd5 per edition; both loudness values; window 16's own cues in A and B; the two written editions' last line | out/identity-report.json, out/mix.json, cues-A/B.json, sound-A/A.vtt, sound-B/B.vtt |
| 72.0–75.0 | attribution card | six CC BY / BY-SA credits with URLs; derived-work licence CC BY-SA 4.0; LoC credit line | films/credits/la-cite-raymond-queneau.json |

`out/reel-BA.mp4` is the B-first counterpart (75.0 s, 5.04 MB).

## The picture master (30.000 s, 720 frames), with each edition's cues

| frames | shot | picture event (edl.json) | A (domestic) | B (surveillance) |
|---|---|---|---|---|
| 0–191 | S1 wide, track left, daylight | win00_on f146, win13_on f168 | far car (car_pass); latch +260 ms (latch_open), cupboard +140 ms (HM) | relay click on the frame (click_heating) over 50 Hz hum (hum_mainsbrum), wind (wind_pine), drone (HM) |
| 192–383 | S2 wide, half-speed track | step contacts f200–345, door_open f334, door_close f374, windows | footstep (footstep) per contact, bag rustle +4 frames (HM); latch+creak f334; door shut f374 | typewriter key (typewriter_wws) per contact; door buzzer (metro_buzzer) f334; re-latch f374 |
| **384** | **key cut** to S3 | win47_on f384 | **music only**: music-box phrase (HM) | **voice stem only**: handmade radio squelch (HM). Not speech. |
| 406 | S3 | win60_on | orchestral 78 through a wall (radio_song, music stem) | key-off squelch (HM, voice stem) |
| 492–566 | S3 key shot, dusk | win16_on **f492**, silhouette_rise f502–518, head_turn f538–552, curtain_slide f552–566 | f492 door latch +150 ms (latch_open), f502 kettle begins to sing (kettle), f538 hummed tune (HM, no caption) | f492 relay click, f518 typewriter bell then carriage (typewriter_ding, typewriter_wws), all stems digital zero f538–565, f566 shutter (shutter_holga) |
| 624–719 | S4 wide, track right | lamp_on f660, win16_off f696 | the 78 from an open window, a bus (car_pass slowed) | drone thins, keystroke chatter, click f696 |

## Claim graph (plan §3)

- `PictureEvent` ∈ master 2d659ecc (`picture/edl.json`, 45 events).
- `CueClaim` → `PictureEvent`: 42 A claims and 39 B claims resolve, no frame drift (`out/cuemap-compare.json`).
- `SoundVersion` {A, B, X, C, silent} → `attach` (`-c:v copy`) → `Edition` (`out/edition-*.mp4`, `out/control-silent.mp4`), and → `out/screening-S-*.mp4` (blind sequences).
- `Edition` → framemd5 = `master.framemd5` 720/720 for each (`out/identity-report.json`); negative controls (one-frame shift, frame 0 dropped, burned caption) all FAIL and are deleted.
- `Caption` → only from a `CueClaim` whose source is a foraged speech recording (`out/speech-captions.json`: 0 in A, 0 in B this round). Written editions are `Fiction`, never `Caption` in the reel.
- Every foraged item → `films/credits/la-cite-raymond-queneau.json` (18 items).

## Re-run order (when the speech files land)

```
cd films/swarm/la-cite-raymond-queneau
(cd sound-A && python3 -I build_A.py && python3 -I make_ledger.py commons-extmetadata.json)
(cd sound-B && python3 -I build_B.py && python3 -I make_ledger.py)
python3 -I editor/speech_vtt.py && python3 -I editor/cuemap.py && python3 -I editor/mix.py && python3 -I editor/editions.py
cd ../../.. && python3 films/la-cite-raymond-queneau.py && python3 films/la-cite-raymond-queneau.py --order BA && python3 films/la-cite-raymond-queneau.py --verify
cd films/swarm/la-cite-raymond-queneau && python3 -I editor/credits.py   # plus speech entries in editor/speech-credits.json
```

`out/side-by-side.jpg` and `picture/side-by-side-*.jpg` contain the copyrighted reference still: internal review files only, never published with the film.

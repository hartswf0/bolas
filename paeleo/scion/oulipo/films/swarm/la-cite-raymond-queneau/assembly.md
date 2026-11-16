# La Cité Raymond Queneau: assembly (montage editor, repair round 2)

Master revision: **`90f1417b48de31c0113ca2ec2e874d1bf3f9d2ec`** (r3). It replaces r2 `2d659ecc…`, which is archived with its editions and reels in `out/revisions/r2-2d659ecc/`. No event frame changed (`event_frames_changed: []`), so both sound teams' cues still resolve with zero drift. Steps 1–5 were re-run on r3.

## What repair round 2 changed

| Finding | Repair |
|---|---|
| B's key cut had no real speech: f384 was a squelch, and speech-captions were empty | f384 in B now carries **real recorded speech**: a 1.25 s phrase from LoC National Jukebox "French lesson no. 1" (Victor 18419, 1917, A. G. H. Spiers and R. Werrenrath; US public domain since 2022 under the MMA). It is band-limited to 350–2600 Hz and saturated as a radio voice between two squelches, with onset +50 ms after the channel opens on the cut frame. It is captioned only as what can honestly be claimed: « [radio : une voix d'homme, mots indistincts] » (`out/B-speech.vtt`, `out/X-speech.vtt`; `speech-captions.json` B: 1, X: 1). `cuemap-compare.json` reports `B_crossover_real_speech.pass = true`. Lingua Libre "quarante-sept" is still wired first but stayed HTTP 429. |
| Edition mp4s showed fiction captions as the default track, untitled | The mp4s carry **only** the transcript of recorded speech; ffmpeg's mov muxer cannot keep a mov_text track non-default or titled. The written editions ship as sidecars, `out/edition-{A,B,X}.written-fiction.vtt`. Each opens with NOTE FICTION (X now has one too), and **none has a line at 16.0–17.5 s**: a written line there would put words in a voice that does not say them. `identity-report.json` records `subtitle_streams` per edition. This deviates from the step-3 command (`-map 2 -c:s mov_text` with the written VTT) on purpose. |
| Victor 78 credited to an "arranger" | Now credited as Victor Schrammel-Orchester (performers); Carl Millöcker (composer); Commons Artist field: Carl Flisch; via publicdomainproject.org; recorded 11 Sep 1922. The change is made in the credits JSON, the note and the reel card. |
| No licence URL or "modified" marker on the card or in the note; typefaces not credited | Every credit now has a `license_url` and a `modified` field. The 72–75 s card prints each CC BY / BY-SA item with its source URL, licence URL and "adapted". The note says the same. The OFL typefaces are on the card and in `out/typeface-credits.json`. |
| The LoC sheet was "no known copyright restrictions", outside the allowed set | Recorded as **Public domain**, on the stated basis that it is an unmarked blank sheet with no copyrightable expression (only clean areas are cropped), with the LoC rights statement kept. |
| Material read as vector flats; the roof was a thin mansard band | New master r3. Roofs are a full, tall curved zinc quarter (rise 6.6 m, run 3.6 m), with larger dormers and an upper skylight row. Facades are lower (GF 3.0 m, floors 2.6 m). Every cut piece (balconies, dormers, caps, skylights) casts a 1–2 px soft contact shadow, and each layer gets an extra tight contact shadow under its 6 px overcast shadow. Cut edges are lighter and more ragged, and the facade's paper fibre is graded 2.7× (was 1.9×). The boulevard is wider (a second carriageway) and the camera stands further back (NOFF 16 m), so the blocks sit in the upper part of the frame as in the reference. |
| Walker 25–30 px: gait illegible | S2 is now the same eye-level position with a **3.4× longer lens** (the documentary zoom), centred on the entrance. The walker is 90–110 px tall, so the stride, contact holds, bag lag and door-jamb clipping at f346–362 can be seen. |
| S4 lamp head at the top edge; faint pool | The lamp is 0.8 m lower and its pool gain is ×1.9. |
| End card stated the readings | It now says only "soundtrack A" / "soundtrack B", and the "written editions" row is removed. The readings live only in the plan and `out/readings.json`. |
| No fresh viewers | **Not run** (`out/readings.json`, protocol unchanged, readings empty). |

## Screening reel: `assets/films/la-cite-raymond-queneau.mp4` (75.0 s, 960×540, 4.13 MB)

| reel time | segment | content | evidence IDs |
|---|---|---|---|
| 0.0–2.5 | title card | lineage "after La Cité Raymond Queneau, Azam & Firode 1998"; "one picture, two soundtracks"; fiction label; 'words under the picture transcribe real recorded voices only'; silent | (none) |
| 2.5–4.0 | card "1" | unlabelled as to reading; silent | (none) |
| 4.0–34.0 | pass 1 = edition A | master frames 0–719 pasted pixel-exact into rows 0–463; rows 464–539 paper band, blank (A has no recorded speech); sound `mix-A.wav` | picture: paper-loc-blank, paper-kraft, paper-vintage + HANDMADE model. A: latch_open, door_close, handle_creak, faucet, footstep, car_pass, kettle, radio_song + HANDMADE wind, room tone, bag rustle, music box, cupboard, spoon, hums |
| 34.0–35.5 | card "2" | silent | (none) |
| 35.5–65.5 | pass 2 = edition B | same 720 frames (sha1 equal 720/720 before encoding; decoded PSNR min 78.4 / mean 98.9 dB); band shows « [radio : une voix d'homme, mots indistincts] » 16.0–17.55 s (pass time), the only caption; sound `mix-B.wav` | B: click_heating, typewriter_wws, typewriter_ding, shutter_holga, wind_pine, hum_mainsbrum, metro_buzzer, LOC:jukebox-26299 (radio voice) + HANDMADE drone, radio squelches |
| 65.5–72.0 | end table | which pass was soundtrack A / B (no reading named); picture identity; framemd5 per edition; both loudness values; window 16's own cues in A and B | out/identity-report.json, out/mix.json, cues-A/B.json, sound-A/A.vtt, sound-B/B.vtt |
| 72.0–75.0 | attribution card | six CC BY / BY-SA credits with source URL, licence URL and 'adapted'; Victor 78 and LoC 1917 voice; OFL typefaces; derived-work licence CC BY-SA 4.0; LoC credit line | films/credits/la-cite-raymond-queneau.json |

`out/reel-BA.mp4` is the B-first counterpart (75.0 s, 4.13 MB).

## The picture master (30.000 s, 720 frames), with each edition's cues

| frames | shot | picture event (edl.json) | A (domestic) | B (surveillance) |
|---|---|---|---|---|
| 0–191 | S1 wide, track left, daylight | win00_on f146, win13_on f168 | far car (car_pass); latch +260 ms (latch_open), cupboard +140 ms (HM) | relay click on the frame (click_heating) over 50 Hz hum (hum_mainsbrum), wind (wind_pine), drone (HM) |
| 192–383 | S2 tele (3.4× lens, same eye level), half-speed track | step contacts f200–345, door_open f334, door_close f374, windows | footstep (footstep) per contact, bag rustle +4 frames (HM); latch+creak f334; door shut f374 | typewriter key (typewriter_wws) per contact; door buzzer (metro_buzzer) f334; re-latch f374 |
| **384** | **key cut** to S3 | win47_on f384 | **music only**: music-box phrase (HM) | **voice stem only**: squelch on the frame (HM), then a real radio voice +50 ms (LOC:jukebox-26299, words indistinct, captioned as such), closing squelch |
| 406 | S3 | win60_on | orchestral 78 through a wall (radio_song, music stem) | key-off squelch (HM, voice stem) |
| 492–566 | S3 key shot, dusk | win16_on **f492**, silhouette_rise f502–518, head_turn f538–552, curtain_slide f552–566 | f492 door latch +150 ms (latch_open), f502 kettle begins to sing (kettle), f538 hummed tune (HM, no caption) | f492 relay click, f518 typewriter bell then carriage (typewriter_ding, typewriter_wws), all stems digital zero f538–565, f566 shutter (shutter_holga) |
| 624–719 | S4 wide, track right | lamp_on f660, win16_off f696 | the 78 from an open window, a bus (car_pass slowed) | drone thins, keystroke chatter, click f696 |

## Claim graph (plan §3)

- `PictureEvent` ∈ master 90f1417b (`picture/edl.json`, 45 events).
- `CueClaim` → `PictureEvent`: 42 A claims and 39 B claims resolve, no frame drift (`out/cuemap-compare.json`).
- `SoundVersion` {A, B, X, C, silent} → `attach` (`-c:v copy`) → `Edition` (`out/edition-*.mp4`, `out/control-silent.mp4`), and → `out/screening-S-*.mp4` (blind sequences).
- `Edition` → framemd5 = `master.framemd5` 720/720 for each (`out/identity-report.json`); negative controls (one-frame shift, frame 0 dropped, burned caption) all FAIL and are deleted.
- `Caption` → only from a `CueClaim` whose source is a foraged speech recording (`out/speech-captions.json`: A 0, B 1, X 1: LOC:jukebox-26299 → win47_on f384). Written editions are `Fiction`: sidecar files only, never a muxed track, never in the reel.
- Every foraged item → `films/credits/la-cite-raymond-queneau.json` (19 items, each with licence URL and modification marker); typefaces → `out/typeface-credits.json`.

## Re-run order (when the Lingua Libre files land in `sources/.../sound-{A,B}/raw/`; build_B prefers them over the LoC voice)

```
cd films/swarm/la-cite-raymond-queneau
(cd sound-A && python3 -I build_A.py && python3 -I make_ledger.py commons-extmetadata.json)
(cd sound-B && python3 -I build_B.py && python3 -I make_ledger.py)
python3 -I editor/speech_vtt.py && python3 -I editor/cuemap.py && python3 -I editor/mix.py && python3 -I editor/editions.py
python3 -I editor/credits.py      # before the reel: its attribution card reads the credits JSON
cd ../../.. && python3 films/la-cite-raymond-queneau.py && python3 films/la-cite-raymond-queneau.py --order BA && python3 films/la-cite-raymond-queneau.py --verify
```
After a picture change: `editor/rebuild_after_master.sh` (render_master.py now overwrites master.framemd5 with -y).

`out/side-by-side.jpg` and `picture/side-by-side-*.jpg` contain the copyrighted reference still: internal review files only, never published with the film.

# Assembly: un-homme-qui-dort (montage editor, plan-r2 / beats-r2 / aesthetic-r2), repair round 1

- **Deliverable:** `assets/films/un-homme-qui-dort.mp4`: 72.000 s, 1728 frames, 960×540 at 24 fps, H.264 + AAC, 2.89 MB (2,889,887 bytes). Poster `assets/films/un-homme-qui-dort.webp` at film 52.0 s (S4, pass II).
- **Script:** `films/un-homme-qui-dort.py`: `kit.Film(slug, 72.0, boil=0, wobble=0)`, `ink.paper(BLACK, grain=False)` on every frame, `vignette` never called. Pre-caption PNGs are pasted unchanged; shot folders come from `e2-picture-ledger.json` → `shot_dirs`.
- **Repair-round picture** (editor-made, same rules as U1; scripts in `editor-r2-build/`, media in `films/sources/un-homme-qui-dort/editor-r2/`):
  - `s1_wake.py`: S1 recast on LoC 2017862347 (new master TIFF `8d33590u.tif`, 32.1 MB, rights re-read from `editor-r2/raw/2017862347.json`).
  - `s34_refuse_held.py`: S3/S4 restaged from U1's own S34 cut pieces (`u1 json/s34_layers.npz`).
  - `s5_flight.py`: a copy of U1's `s5.py`, with the changes marked `R1`; it writes S5 and S7.
  - `ledger_r2.py`: writes `e2-picture-ledger.json`, with measured events, coverage, SHA-1s, stats, head heights, waivers and defects.
  - S2 and S6 are U1's frames, unchanged.
- **Checks:**
  - `editor-final-timings.json`: the script's invariant report.
  - `editor-check.py`, `editor-check.json` and `editor-aesthetic-final.jpg`: decoded-mp4 measurements beside `assets/references/sommeil.webp`, which is used for study only and is never in the film.
  - `editor-gate-picture.json` and `editor-gate-report.json`: the u3-gate run.
- **Site:** `index.html` and `s/un-homme-qui-dort/index.html` were regenerated with `build.py`'s own functions, written only to those two pages. Prompts, the README and other films' pages were not written. Both pages now embed the current credits and note.
- **Evidence labels:** **[M]** measured · **[S]** structurally verified (by construction or by an assertion in code) · **[P]** perceptually judged (by the editor only, unless stated) · **[U]** unknown.

## 1. Timecoded sequence list (film seconds)

**Evidence IDs:**
- **Plates:** `loc-2017862347` (S1, new), `loc-2017862340`, `loc-2017735081`, `loc-2017811447`, `loc-2017714056`.
- **Sound (U2):** `SRC-ROOM`, `SRC-BELL`, `SRC-STEPS`.
- **Voice (U3):** `c1`–`c5`, `font-instrument-serif`.
- **Handmade:**
  - `H-CARD`: the cards.
  - `H-CAP`: the caption setting.
  - `H-RIG1`: U1's cutouts and rigs.
  - `H-RIG2`: the editor's r1 cutouts, warps and print curves.

| film t | segment / shot | picture | caption (track) | sound | evidence |
|---|---|---|---|---|---|
| 0.000–1.000 | CARD-I | "I", Instrument Serif #efefef on #1e1e1e | — | room handle pre-roll | H-CARD, SRC-ROOM |
| 1.000–6.500 | A · S1 WAKE | Bubley close-up of the same sitter, head bowed over the paper against the pale wall, dark suit at right. Glide: far 10 px, figure 15 px. E1 at pass 2.0–2.8 (film 3.0–3.8): the head lifts (9° weighted rotation, crown up 15 px). | c1 "You open your eyes." 1.80–3.00 | room only (withheld cue) | loc-2017862347, H-RIG2, c1, SRC-ROOM |
| 6.500–9.500 | A · S2 TELEPHONE | Lee wall phone, push 1.00→1.04, coats at 2× | c2 5.80–7.05 | rings 1 and 2 at 7.0 and 8.6 | loc-2017735081, H-RIG1, SRC-BELL, c2 |
| 9.500–12.500 | A · S3 REFUSE | Bubley 2017862340 on S4's layout. The glide (12 px far / 18 px hands) settles into S4's rest frame. At pass 9.25 (film 10.25) the head and its cast shadow turn 9° toward the bell; they hold, then return at 10.4 (film 11.4). | c3 8.80–10.00 | ring 3 at 10.0, ring-off to 11.88 | loc-2017862340, H-RIG1 (pieces), H-RIG2 (warp, print), SRC-BELL, c3 |
| 12.500–20.000 | A · S4 HELD (SIL-H) | the same framing at rest; 180 identical frames | **none** | room only | loc-2017862340, SRC-ROOM |
| 20.000–25.500 | A · S5 FLIGHT 1 | Vachon stair. Empty until pass 20.54, then the climb with 5 step dips; empty from 23.5. Print LUT deepens the darks. | c4 20.30–21.60 (empty stair) | near footfalls 21.8–24.0 | loc-2017811447, H-RIG1, H-RIG2, SRC-STEPS, c4 |
| 25.500–28.000 | A · S6 STAIRWELL | Mydans, three-plane tilt | — | 2 distant footfalls 26.2 and 26.95 | loc-2017714056, H-RIG1, SRC-STEPS |
| 28.000–36.000 | A · S7 FLIGHT 2 + TAIL | S5's 132 frames byte-identical, then S5's last frame held for 60 frames | c5 28.30–31.10 (empty stair) | footfalls 29.8–32.0, then room | loc-2017811447, SRC-STEPS, c5 |
| 36.000–37.000 | CARD-II | "II" | — | room post-roll cross-faded (equal power) into the pre-roll that continues into pass II | H-CARD, SRC-ROOM |
| 37.000–42.500 | B · S1 | same frames | c1 40.20–41.40 (after the lift at 39.0–39.8) | same stems | as above |
| 42.500–45.500 | B · S2 | " | c2 44.20–45.45 (overlaps the unbound ring 2) | " | " |
| 45.500–48.500 | B · S3 | " | c3 47.20–48.40 | " | " |
| 48.500–56.000 | B · S4 SIL-H | " | **none** | room only | " |
| 56.000–61.500 | B · S5 | " | c4 58.70–60.00, wholly on figure-visible frames = **Bl** | " | " |
| 61.500–64.000 | B · S6 | " | — | " | " |
| 64.000–72.000 | B · S7 | " | c5 66.70–69.50. Figure and shadow are gone from 68.50, so 1.0 s of empty stair = **D** | " | " |

**Audio.** These arrays are added with `mix.add` at film 1.0 and 37.0 with identical gains:
- `ST-BELL`, `ST-STEPS-NEAR` and `ST-STEPS-ABOVE` (U2's 44.1 kHz copies);
- the room tone, taken as the 35 s core of U2's `ST-ROOM-HANDLES-37s`.

The core equals `ST-ROOM` sample for sample from 62 ms onward. U2's `kit44k1/ST-ROOM.wav` starts with 24 ms of digital silence (a resampler edge), which made a dropout at each pass start, so the editor no longer uses it.

## 2. Claim graph and evidence

| claim | evidence | label |
|---|---|---|
| 72.0 s, ≤ 6 MB | ffprobe 72.000 s, 1728 frames; 2.89 MB | M |
| Pass I picture = pass II picture | both passes index the same 840 PNG paths (`segment()`); per-shot decode error is identical in A and B | S + M |
| S5 = S7 27.0–32.5 | SHA-1 of decoded pixels, 132/132 equal; the 60-frame tail is S5's last frame (script assert before render; `e2-picture-ledger` S5_equals_S7_first_132 = true) | S |
| Identical strings, order and durations | script assert; gate I6 | S |
| Onsets = event ∓1.2 ± 0.05 | asserted against measured E1 (frame 48 → 2.0), E4 (20.5417) and E6 (28.5417), and against U2-placed E2 (6.0) and E3 (9.0). Offsets: c1–c3 −1.2/+1.2; c4–c5 −1.242/+1.158 | M (E1, E4, E6) + S (E2, E3) |
| No caption in SIL-H (0.1 s guard) | script assert; decoded video has 0/180 caption frames in SIL-H per pass, band-zone error ≤ 1.73 (encode noise) | S + M |
| SIL-H audio: non-zero floor, no transient > 6 dB | decoded final audio: floor −43.03/−43.02 dBFS; max 50 ms +2.59/+2.50 dB; max 10 ms +4.92/+4.82 dB (A/B) | M |
| No room-tone restart at 37.0 | 500 ms RMS 34–39 s stays between −42.7 and −43.6 dBFS; no zero run at 1.0 or 37.0 (10 ms minimum −53.7 dBFS, within the recording's own range) | M |
| D ≥ 0.8 s | 24 frames (1.000 s) of zero figure and shadow alpha under c5.B, film 68.5–69.5 | M + S |
| Bl: c4.B inside the figure interval | 31/31 frames have figure alpha > 0 | M + S |
| Pass I c4/c5 begin on the empty stair | coverage 0.0 at both onsets | M |
| `u3-gate.py` passes the final timings | `--picture editor-gate-picture.json --sound u2-sound-ledger.json`: 105 checks, 0 failed. `--selftest`: "He hears it through the wall." (and the forged-person variant), c4.A → 18.8, and c2.B → 8.7 are all rejected | M |
| Every frame neutral | max mean chroma over every 12th decoded frame = 0.000 | M |
| p1 in 20–40, p99 in 236–250 on every shot | decoded frames: S1 27/244, S2 30/245, S3 26/242, S4 26/242, S5 23/244, S6 31/248, S7 tail 31/244 (was 46) | M |
| S3/S4 bimodality, each part within ±0.12 of 0.416/0.326 | S3 and S4 (decoded, pass I and II): below60 0.319, above220 0.358 (sum 0.677). Δ = −0.097 / +0.032 → **pass** | M |
| S1 in the family (60–220 band ≤ 0.55, the critic's target) | S1 below60 0.324, above220 0.374, mid 0.302 (reference 0.416/0.326/0.257) | M |
| Head height S1 ≥ 0.35, S3 ≥ 0.35, S4 ≥ 0.42 | 0.745 / 0.595 / 0.595 from the head masks (crops from master TIFFs, downscaled ×0.44, never upscaled) | M + S |
| Same sitter in S1 and S3/S4 | same curly hair, ear, nose and the same pinstripe suit and tie in 2017862347 and 2017862340 (same Bubley set, Jan 1943) | P (probable) |
| Visible proof actions | S1 crown rises 15 px (head-alpha top 65 → 50) over frames 48–67. S3: head + shadow turn 9° over 8 frames from pass frame 222, return from 250 | M |
| Each print curve is a single monotone neutral curve | S1: PCHIP through recorded control points (raw → L). S3/S4 and S5: monotone LUT on U1's graded composite, which at rest equals U1's graded plate, so plate → curve → LUT is one monotone map. All curves are asserted monotone in code | S |
| No grain, vignette, cream or rebate added | grain=False, no vignette call, chroma 0, rebates cropped. The S4 wall patch high-pass σ rose from 3.47 to 4.30: the negative's own grain steepened by the print curve, nothing synthesized | S + M |
| The figures are real GrabCut cutouts that move | RGBA, masks and failure masks on disk (U1 and editor-r2); motion visible in `diag/s1_strip.png` and `diag/s3_turn_pair.png` | S + P |
| Banister occludes the climbing legs (bar 8 / SCION-44 rule 11) | **WAIVED, true to the plate**: in 2017811447 the climber is on the near side of the rail (his coat overlaps the balusters and newel). The rail remains a real mid plane (k 1.5) that he passes in front of. Recorded in `e2-picture-ledger.json` → waivers | S (waiver) |
| Same photographic family as the reference | `editor-aesthetic-final.jpg`, editor only. S1, S3 and S4 are hard flash, pale wall, deep dark suit mass and a close head; S3/S4 have the cast-shadow double beside the head. No fresh critic has judged this round | P (editor) / U (independent) |
| No POV; gaze never meets the lens | S1 eyes down; S3/S4 eyes off left; the S5 climber looks off left | P |
| No speech or music audible | U2 measurements and spectrograms only; **no human has listened to the final mix** | U |
| "You" lands on the viewer in D and not in Bl | not tested | U |
| Every foraged item credited with an accepted licence | `films/credits/un-homme-qui-dort.json`, 9 entries: 5 LoC plates ("No known restrictions", re-read from the item JSON), 3 Commons sounds (CC BY 4.0, CC BY 4.0, CC BY 3.0), and Instrument Serif (OFL 1.1). The Vachon and Mydans titles now use LoC's "[Untitled photo, possibly related to: …]" wording and LoC dates (1940 Dec.; [1935 Sept.]). 2017862333 was removed, since it is no longer on screen | S |
| The page as served carries credits and note | regenerated pages contain Minetelephone, TU Delft, Gravity Sound, 8d33583u, 8a21346a, 8c18457, 8a00242a, 8d33590u and Instrument Serif. The note begins "One 35-second picture is shown twice with the same five". No credit entry is a "test" or "candidate" item | M |

## 3. Repairs against the review

| unmet item | repair | result |
|---|---|---|
| S3/S4 tone | reframed S3 onto S4's layout; a deeper monotone print LUT | 0.319/0.358, within ±0.12 [M] |
| S1 not the family | recast on 2017862347 (the same man, pale wall, dark suit); new master TIFF; harder print | 0.324/0.374/0.302 [M] |
| S7 tail p1 46 | S5 LUT deepens the stair's darks (identity preserved: S7 is S5's frames) | p1 31 [M] |
| banister occlusion | formal waiver, true to the plate | waived [S] |
| head turn 3° → 8–12°, S1 lift ≥ 15 px | S3 9° with its shadow (weighted warp); S1 crown 15 px | done [M] |
| same man throughout | S1 now the same sitter as S3/S4; the **climber is still Vachon's man** | partial; declared |
| darker wallpaper repeat | lightness-matched patch copy | reduced (about 13 → 7 L darker than neighbours) [M] |
| room-tone restart at 37.0 | equal-power card-II cross-fade, plus the room core from the handles file (fixes the 24 ms dropout too) | smooth [M] |
| stale page | the two pages regenerated | done [M] |
| credit titles and dates; typeface | corrected; Instrument Serif added | done [S] |
| human listen, fresh critic | not possible in this run | **open** [U] |

## 4. Known weaknesses

1. **The climber in S5/S7 is a different man** (declared casting substitution). The repair asked for the same man or a convincing anonymous double. No openly licensed stair plate of the Bubley sitter exists in the set searched (37 Bubley boardinghouse items), and his face is readable in profile.
2. **S1 warp residue.** While the head is raised, a faint line runs along the jaw where the head's alpha edge meets the shadowed throat fill (invented and flagged), and a faint hair-edge halo shows against the lamp.
3. **Remaining fill and staging residue:**
   - The S5/S7 rebuilt wallpaper above the cap is still about 7 L darker than its neighbours.
   - U1's S6 near-layer wedge slides about 4 px in shadow.
   - The S4 lower-left corner shows the woman's book corner (pages only).
4. **S3 and S4 share one framing**, so the 11.5 cut joins identical frames and reads as one continuous 10.5 s observation (S3 and S4 differ only by the glide and the turn). The plan asked for S4 "cut closer", but the plate's rebate and the woman's book allow no wider S3 that keeps the tone.
5. **His expression in S3/S4 is the plate's own:** pursed lips, half amused, not the reference's blankness.
6. **Grain.** The print curves steepen the negative's own grain on the wall (σ 3.47 → 4.30), so the wall is grainier than the reference's clean white (0.86). Nothing is synthesized.
7. **Budget.** New downloads this round: one master TIFF of 32.1 MB. With U1's 59.1 MB, that totals 91 MB against the plan's 75 MB. The editor-r2 media folder is 167 MB of derived frames and pieces.
8. **Not yet done:**
   - No human has listened to the mix.
   - No fresh critic has judged S1/S3/S4 against the reference.
   - The D-vs-Bl viewer test has not been run.
   - `u3-referent-audit.json` still says PENDING U1; the gate was run on the editor's measured picture file instead.

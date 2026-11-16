# Assembly: un-homme-qui-dort (montage editor, plan-r2 / beats-r3 / aesthetic-r2), repair round 2

- **Deliverable:** `assets/films/un-homme-qui-dort.mp4`: 72.000 s, 1728 frames, 960×540 at 24 fps, H.264 + AAC, 2.24 MB (2,238,917 bytes). Poster `assets/films/un-homme-qui-dort.webp` at film 52.0 s (S4, pass II).
- **Script:** `films/un-homme-qui-dort.py`: `kit.Film(slug, 72.0, boil=0, wobble=0)`, `ink.paper(BLACK, grain=False)` on every frame, `vignette` never called. Pre-caption PNGs are pasted unchanged; shot folders come from `e3-picture-ledger.json` → `shot_dirs`.
- **Repair-round-2 picture** (editor-made under the same rules; scripts in `editor-r3-build/`, media in `films/sources/un-homme-qui-dort/editor-r3/`, 170 MB of derived frames/pieces; **no new download** this round):
  - `s1_r3.py`: S1 back on LoC 2017862333 (U1's master TIFF `8d33576u.tif` and U1's SCION-29 pieces).
  - `s34_r3.py`: S3/S4 from U1's pieces and the graded negative (halo fix).
  - `s5_cut.py` + `s5_r3.py`: S5/S7 restaged on the Mydans stairwell with the S3/S4 sitter as climber.
  - `u3_build_ledger_r3.py`: U3's builder with the r3 changes (c1 text, S5 performer, viseme note) → `u3-clause-ledger.json`, `takeA.srt`, `takeB.srt`.
  - `ledger_r3.py` → `e3-picture-ledger.json` (supersedes `u1-picture-ledger.json` and `e2-picture-ledger.json`, both now carry a `superseded` field).
  - `beats.json` is now **beats-r3**: c1 text and the S1/S5/S6/S7 plate descriptions changed; every time, event and offset is unchanged (r2 copies in `r2-superseded/`).
  - S2 and S6 are U1's frames, unchanged.
- **Checks:** `editor-final-timings.json` (script invariants), `editor-check.py` → `editor-check.json` + `editor-aesthetic-final.jpg` (decoded mp4 beside `assets/references/sommeil.webp`, which is study only and never in the film), `editor-gate-picture.json` + `editor-gate-report.json` (u3-gate), `review-3-gate-selftest.txt`.
- **Site:** `index.html` and `s/un-homme-qui-dort/index.html` regenerated with `build.py`'s own functions (only those two files written).
- **Evidence labels:** **[M]** measured · **[S]** structurally verified · **[P]** perceptually judged (editor only) · **[U]** unknown.

## 1. Timecoded sequence list (film seconds)

Evidence IDs: plates `loc-2017862333` (S1), `loc-2017735081` (S2), `loc-2017862340` (S3/S4 and the S5/S7 climber), `loc-2017714056` (S5/S7 stage, S6); sound (U2) `SRC-ROOM`, `SRC-BELL`, `SRC-STEPS`; voice (U3) `c1`–`c5`, `font-instrument-serif`; handmade `H-CARD` (cards + declaration line), `H-CAP` (caption setting), `H-RIG1` (U1 cutouts/rigs), `H-RIG3` (editor r3 cutouts, IK climb, warps, LUTs).

| film t | segment / shot | picture | caption (track) | sound | evidence |
|---|---|---|---|---|---|
| 0.000–1.000 | CARD-I | "I" #efefef on #1e1e1e, under it: "Animated from FSA/OWI photographs, Library of Congress, 1935–43: / figures cut out of the negatives and moved; some background filled in." (#d6d6d6) | — | room handle pre-roll | H-CARD, SRC-ROOM |
| 1.000–6.500 | A · S1 WAKE | Bubley 2017862333 close-up (head 0.65 of frame): head resting on his hand, dark board and wallpaper behind. Glide 10 px (near 1.6× far). **E1 pass 2.0–2.8 (film 3.0–3.8): the hand stays; the head rises 35 px off it and rights 5°** | c1 "You lift your head." 1.80–3.00 | room only (withheld cue) | loc-2017862333, H-RIG1, H-RIG3, c1 |
| 6.500–9.500 | A · S2 TELEPHONE | Lee wall phone, push 1.00→1.04, coats 2× | c2 5.80–7.05 | rings 1, 2 at 7.0, 8.6 | loc-2017735081, H-RIG1, SRC-BELL, c2 |
| 9.500–12.500 | A · S3 REFUSE | Bubley 2017862340 on S4's layout; 8 px glide settles by pass 9.21; at pass 9.25 (film 10.25) head + cast shadow turn 9° toward the bell, return at 10.4 (film 11.4) | c3 8.80–10.00 | ring 3 at 10.0, ring-off to 11.88 | loc-2017862340, H-RIG1, H-RIG3, SRC-BELL, c3 |
| 12.500–20.000 | A · S4 HELD (SIL-H) | the untouched graded negative, 180 identical frames | **none** | room only | loc-2017862340, SRC-ROOM |
| 20.000–25.500 | A · S5 FLIGHT 1 | Mydans dark flight, static camera. Empty until pass 20.5; **the S3/S4 man climbs behind the handrail**, legs (IK) between the balusters, 10 px dip on each footfall; gone behind the right newel post from 23.5 | c4 20.30–21.60 (empty stair) | near footfalls 21.8–24.0 | loc-2017714056, loc-2017862340, H-RIG3, SRC-STEPS, c4 |
| 25.500–28.000 | A · S6 STAIRWELL | the same Mydans stairwell, wider, three-plane tilt (U1) | — | 2 distant footfalls 26.2, 26.95 | loc-2017714056, H-RIG1, SRC-STEPS |
| 28.000–36.000 | A · S7 FLIGHT 2 + TAIL | S5's 132 frames byte-identical, then S5's last (empty) frame held 60 frames | c5 28.30–31.10 (starts on the empty stair) | footfalls 29.8–32.0, room | loc-2017714056, loc-2017862340, SRC-STEPS, c5 |
| 36.000–37.000 | CARD-II | "II" + the same declaration | — | room post-roll cross-faded into pre-roll | H-CARD, SRC-ROOM |
| 37.000–42.500 | B · S1 | same frames | c1 40.20–41.40 (after the lift, 39.0–39.8) | same stems | as above |
| 42.500–45.500 | B · S2 | " | c2 44.20–45.45 (overlaps unbound ring 2) | " | " |
| 45.500–48.500 | B · S3 | " | c3 47.20–48.40 | " | " |
| 48.500–56.000 | B · S4 SIL-H | " | **none** | room only | " |
| 56.000–61.500 | B · S5 | " | c4 58.70–60.00 wholly on figure-visible frames = **Bl** | " | " |
| 61.500–64.000 | B · S6 | " | — | " | " |
| 64.000–72.000 | B · S7 | " | c5 66.70–69.50; figure gone from 68.50 → 1.0 s of empty stair = **D** | " | " |

Audio: U2's `ST-BELL`, `ST-STEPS-NEAR`, `ST-STEPS-ABOVE` (44.1 kHz copies) and the 35 s core of `ST-ROOM-HANDLES-37s`, added with `mix.add` at film 1.0 and 37.0 with identical gains (unchanged from round 1).

## 2. Claim graph and evidence

| claim | evidence | label |
|---|---|---|
| 72.0 s, ≤ 6 MB | ffprobe 72.000 s, 1728 frames, 2.24 MB | M |
| Pass I picture = pass II picture | same 840 PNG paths; decode error identical A/B per shot (`editor-check.json`) | S + M |
| S5 = S7 27.0–32.5 | SHA-1 of the 132 PNGs equal; tail = S5 last frame (script assert; `e3` `S5_equals_S7_first_132`) | S |
| Identical strings, order, durations | script assert; gate I6 | S |
| Onsets = event ∓1.2 ± 0.05 | against measured E1 (frame 48 → 2.0), E4 (first visible frame 492 → 20.500), E6 (28.500) and U2-placed E2/E3: all offsets exactly −1.2 / +1.2 | M + S |
| No caption in SIL-H | script assert; decoded video 0/180 caption frames per pass, band-zone error ≤ 1.77 | S + M |
| SIL-H audio floor non-zero, no transient > 6 dB | decoded: floor −43.03/−43.02 dBFS; max 50 ms +2.59/+2.50 dB; max 10 ms +4.92/+4.82 dB | M |
| D ≥ 0.8 s | 24 frames (1.000 s) of zero visible figure (and no shadow plane) under c5.B, film 68.5–69.5 | M + S |
| Bl: c4.B inside the figure interval | 31/31 frames figure-visible | M + S |
| `u3-gate.py` passes final timings | `--picture editor-gate-picture.json --sound u2-sound-ledger.json`: 105 checks, 0 failed; `--selftest` rejects "He hears it through the wall." (and forged-person variant), c4.A → 18.8, c2.B → 8.7 | M |
| **E1 legible: head lifts off the hand** | hand K is a fixed plane; head-alpha crown 189 → 154 px (**35 px rise**, ≥ 30); head/hand contact pixels 553 → 291 | M |
| **c1 promises only what is shown** | c1 rewritten "You lift your head." (r2 "You open your eyes." retired); eyes are the plate's own, down, off-lens | S + P |
| **Climber = the S3/S4 sitter** | all climber pieces are cut from LoC 2017862340, the S3/S4 negative itself (UB mask `S5r3_climber_UB_mask.png`, legs `S5r3_TH/SH_mask.png`) | S |
| **Banister occludes the climbing legs** | handrail, balusters, stringer and newels are an opaque near plane composited over the figure; figure-over-rail = **0 px on every frame** (screen px whose render px are all opaque near equal the stage exactly). Waiver removed | M + S |
| **S5/S7 dark mass** | below L60 0.596–0.615 on every 6th S5 frame (bar ≥ 0.30); decoded S5 0.609, S7 0.604 | M |
| **Articulated climb, step dip ≥ 8 px** | two-bone IK legs (thigh 98.6, shin 98.6 px, knee forward), stance/swing gait planted at frames 499/512/526/539/552; hip dip 10.0 px at each footfall (vs ±6 frames) | M |
| "He climbs, not slides" at 24 fps | editor only; legs read as dark shards through the baluster gaps | P (editor) / U (fresh viewer) |
| S1 toward the reference mid-grey register | decoded S1 p50 71–72 (reference 94; within ±40), below60 0.355, above220 0.054–0.058 (reference 0.326: **S1 is low on whites**) | M |
| S3/S4 bimodality within ±0.12 | decoded 0.320/0.357 (Δ −0.096/+0.031) | M |
| S3/S4 p50 within ±40 of 94 (critic's proposed bar) | **fails: 207** (pale-wall-dominant layout, protected); recorded, not changed | M |
| S3 crown notch / halo removed | from shot frame 17 on (incl. the whole turn) and all of S4, the base image is the graded negative itself, no matte edge | S + P |
| Every frame neutral; p1 20–40, p99 236–250 | max mean chroma 0.000 (every 12th decoded frame); p1 26–31, p99 242–248 on all shots | M |
| Head height | S1 0.651, S3/S4 0.595 (master-TIFF crops, downscaled); S5 climber head ≈ 0.08 | M |
| Same sitter in 2017862333 and 2017862340 | same Bubley set (Jan 1943), curly hair, ear, nose; LoC captions differ ("A clerk in the U.S. Navy Department…" / "A boardinghouse philosopher") | P (probable) |
| No POV; gaze never meets lens | S1 eyes down; S3/S4 off left; climber looks ahead up the flight | P |
| Mouth | no mouth motion authored; mouths are the plates' own (S1 closed; S3/S4/S5 pursed as photographed); U3 ledger viseme note corrected | S |
| Staged/composite nature labelled on screen | cards I and II carry the declaration line (2 s total) | S |
| No speech or music audible | U2 measurements/spectrograms only; **no human has listened** | U |
| Same photographic family as the reference (fresh critic) | **no fresh critic this round** (no reviewer agent available to the editor); editor-only comparison in `editor-aesthetic-final.jpg` | P (editor) / U |
| "You" lands on the viewer in D and not in Bl | not tested with a viewer | U |
| Every foraged item credited, accepted licence | `films/credits/un-homme-qui-dort.json`, 8 entries: 4 LoC FSA/OWI items ("No known restrictions", rights re-read from item JSON 2026-11-16), 3 Commons sounds (CC BY 4.0, CC BY 4.0, CC BY 3.0), Instrument Serif (OFL 1.1). Removed: 2017862347 and 2017811447 (no longer on screen) | S |

## 3. Repairs against review round 2

| unmet item | repair | result |
|---|---|---|
| climber a different man | recast from the S3/S4 negative (2017862340) itself | done [S] |
| S5/S7 white wallpaper, no dark mass | restaged on the Mydans stairwell 2017714056 | below60 ≥ 0.596 [M] |
| banister occlusion waived | opaque near plane over the figure; waiver deleted | 0 px over rail [M] |
| sticker glide, no legs | IK-articulated trouser-leg pieces, footfall-timed gait, 10 px dips | done [M]; reading [U] |
| S1 no hand / eyes / halo | back to head-on-hand 2017862333; hand fixed, head +35 px; c1 → "You lift your head."; hidden cheek shaded, ghost hair fringe re-filled | done [M]; invented strip remains [P] |
| S1 too white | monotone LUT, p50 204 → 72 | done [M] |
| ledgers disagree | e3 ledger; u1 and e2 marked superseded; credits follow e3 | done [S] |
| nothing on screen says these are cutouts | declaration line on both cards | done [S] |
| note overstates "same man" | note says "probably the same sitter"; rewritten | done [S] |
| viseme note wrong | corrected in the r3 clause ledger | done [S] |
| S3 crown notch | negative used as the base through the turn and the hold | done [S] |
| Vachon file_url | moot: Vachon no longer used | — |
| fresh critic, human listen, D-vs-Bl viewer | not possible in this run | **open** [U] |

## 4. Known weaknesses

1. **Climber scale and reading.** He is small (head ≈ 42 px), dimly printed, hands clasped at his chest as in the seated photograph; his legs are strips of his own trouser leg, visible only between balusters as dark shards. Pieced from a seated pose and flopped left-right (declared). Feet are always hidden behind the stringer; the perspective from below the flight is approximate.
2. **S1 invented strip.** Where the head rises, the strip next to the fingers is invented (shaded cheek fill) and a patch-copied dark smudge sits left of the hair.
3. **S1 tone.** p50 is in the reference's register but whites are scarce (above220 0.055 vs 0.326): the wallpaper/curtain plate is mid-toned, not bimodal.
4. **S3/S4 p50 207** fails the critic's proposed ±40 p50 bar; left as protected.
5. **The Mydans stairwell appears three times** (S5, S6 wider, S7). S6 is the same negative as S5.
6. **The S3/S4 turn warp** stretches a little flat wall (top-left edge streaks from border replication during the 9° turn).
7. **Not done:** fresh critic, human listening, viewer test of D vs Bl; `u3-referent-audit.json` still says PENDING U1 (the gate was run on the editor's measured picture file instead).
8. **Budget:** sources folder 708 MB (mostly derived PNG sequences: editor-r2 167 MB is now unused and could be deleted; editor-r3 170 MB).

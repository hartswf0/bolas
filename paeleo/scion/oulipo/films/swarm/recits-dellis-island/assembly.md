# Assembly · Récits d'Ellis Island · plan-r1 (montage editor)

These files were assembled on 2026-11-15:
- **Script:** `films/recits-dellis-island.py` (sha256 `bd5d893d…`).
- **Inputs:** traces.json, sounds.json, testimony.json, claims.json and captions.srt, all as delivered by U1, U2 and U3. The script reads them and never edits them.

| render | path | dur | size | sha256 |
|---|---|---|---|---|
| public cut (order AB) | `assets/films/recits-dellis-island.mp4` | 60.000 s | 3.00 MB | `c863d45b…` |
| baseline (private) | `films/swarm/recits-dellis-island/baseline.mp4` | 14.0 s | 0.92 MB | `a27e0c8c…` |
| branch `order-BA` (private) | `films/swarm/recits-dellis-island/order-BA.mp4` | 60.000 s | 3.00 MB | `6c58897e…` |

All renders are 960×540 at 24 fps (1440 frames for the 60 s cuts), with AAC stereo sound.
- **Image handling:** foraged images are pasted as decoded pixels. They are only cropped or reframed with bicubic resampling. There is no grain (`paper(grain=False)`), no vignette and no tint.
- **Sound handling:** foraged sounds are decoded with ffmpeg to 44.1 kHz mono and placed with `mix.add`. Nothing is synthesised.

## 1 · Timecoded sequence → evidence IDs (public cut)

| film time | dur | picture | evidence on screen | heard |
|---|---|---|---|---|
| 0.0–3.0 | 3.0 | Handmade title card, with "witnesses and last train invented; photographs show a real disused halt, Bourré (Loir-et-Cher), standing in" | H | Silence to 2.2 s, then S3 in |
| **Movement I** 3.0–4.5 | 1.5 | Card "I · What the site shows · no voices" | H | S3 |
| 4.5–11.0 | 6.5 | T1 full frame, 6 % lateral reframe (raw box [0,144,1805,1159] → [115,144,1920,1159]) | T1 tag: author, CC BY 2.0, "23 Jan 2021, 13:58 (EXIF, measured)", place stated | S3 (tag on the bottom band) |
| 11.0–16.0 | 5.0 | T2 closed door, slight push-in ([0,202,1920,1282] → [0,288,1690,1238]) | T2 tag: "shows the door shut that day, nothing more" | S3, plus S4 at low level 11–16 s (rumble peak about 13.5 s); S4 tag from 12.4 s |
| 16.0–22.5 | 6.5 | T6, the 1904 PO map: full sheet (16.0–17.2), log-zoom to the printed date (17.2–19.0), held with a labelled marker (to 19.9), travel to "Bourré" on the Tours–Vierzon line (19.9–21.1), held with a labelled marker | T6 tag: "printed Mars 1904 (read on the sheet) · names Bourré on the Tours-Vierzon line · does not show the halt · public domain" | S3 thinned to 0.55 |
| 22.5–28.0 | 5.5 | **T1 platform crop**, `T1_platform_crop.png` unchanged; fades to paper at 27.4–28.0 | T1 tag: "shows this platform on that day · no bench, no bell, no key visible" | S3, fading to silence by 28.6 |
| 28.0–30.0 | 2.0 | Card "II · The last train, twice · two fictional witnesses · staged testimony · voices are captions · silence declared" | H | Declared silence |
| **Movement II** 30.0–32.5 | 2.5 | Testimony record A (`sheet_A1.png`), line A1 highlighted | H tag; caption **A1** (seg A 00:14.0–00:18.0) | Declared silence (no room recording) |
| 32.5–38.5 | 6.0 | **Beat A**: T1 platform crop, same file, same tag | T1 tag + "heard" line; captions **A2** 32.5–36.0, **A3** 36.0–38.5 | S3 low (file 4.0 s onward); **S1 bell 33.6**; **S2 keys 35.4** |
| 38.5–41.0 | 2.5 | T7 Méliès 1896, 60 frames | T7 tag: "Vincennes, 1896 · another station, another century · illustrates, does not prove"; caption **A4** | Silent (declared) |
| 41.0–43.5 | 2.5 | Testimony record B (`sheet_B1.png`), line B1 | H tag; caption **B1** (seg B 01:02.0–01:04.5) | Declared silence |
| 43.5–49.5 | 6.0 | **Beat B**: the same T1 crop and the same tag | Captions **B2** 43.5–46.0, **B3** 46.0–48.2, **B4** 48.2–49.5 | S3 low (the *same* stretch of the file as under A); **S2 keys 44.6**; **S1 bell 47.6** |
| 49.5–55.0 | 5.5 | Handmade ledger card (claim graph), with chips lit in sync with the replays | C1, C2, C3 (UNRESOLVED), C4 scope, agreed facts | S1 49.9 L, S2 50.6 L (A's order); S2 51.6 R, S1 52.4 R (B's order) |
| **Coda** 55.0–60.0 | 5.0 | Handmade sources and permissions card | Every ID: T1 T2 T6 T7 S1 S2 S3 S4, testimony A/B, H; notes the order-BA branch | Silence |

Every caption carries:
- its label from testimony.json, verbatim, in the witness colour (A blue, B ochre);
- the EN text from testimony.json;
- a right-aligned "EN tr. of FR · rev 1".

The script asserts that each caption's label, text and film time equal captions.srt.

## 2 · Ledger / claim graph as projected (deliverable §9)

```
segA:A2 (00:18.0–00:22.5) --supports--> C1 "A recalls bell before key"
segB:B2,B3 (01:04.5–01:10.5) --supports--> C2 "B recalls key before bell"
C3 "bell rang before the key, on the night"   status DISPUTED · UNRESOLVED
    segA:A2 --supports-- ; segB:B2 --disputes-- ; segB:B3 --disputes-- ; T1 --leaves_open--
C4 "a door was shut on 23 Jan 2021"  <--supports-- T2 (that day only; not the night in the accounts)
C5 "built 1869"  <--leaves_open-- T3 uploader description     (not projected; T3 not used)
C6 "the image proves A's memory"     BLOCKED · project=false · Match set = []   (not projected)
agreed: envelope · key left on the bench · service door shut  <-- A1 A2 A3 B1 B2 B4
```

The ledger card projects C1–C4 and the agreed row. On the card:
- C3 is marked UNRESOLVED.
- The card states "T1 … supports neither order (leaves open)" and "No image-to-memory match on file".
- C6 is not projected.

## 3 · §3.2 preconditions: how the script enforces them

Run `python3 films/recits-dellis-island.py --check` to execute all of these without rendering.

1. **Licences.** Every used Trace and Sound (T1 T2 T6 T7 S1 S2 S3 S4) must match `Public domain|PD…|CC0|CC BY[ v]|CC BY-SA[ v]` and must not contain NC, ND, fair use or unknown. CC BY and CC BY-SA items also need a licence URL.
   - The script also checks the sha256 of every pasted or mixed file against its evidence record (I5): T1 raw and crop, T2 raw, T6 raw and sheet, the first and last T7 frames, S1–S4, and sheets A1 and B1.
2. **Movement I has no testimony.** No M1 shot has testimony or captions, and no M1 source card contains a quotation mark (`" « » “ ” „`).
3. **Consent.** Each segment's consent must be in {authored-fiction, granted, missing} and have a use scope.
   - If consent is missing, `OUT_DIR` becomes `films/swarm/recits-dellis-island/private/`, and an assert refuses `assets/films`.
   - Dry run: `--check --simulate-missing-consent B` prints "PUBLIC EXPORT BLOCKED → …/private".
4. **Testimony over a trace.** Every such shot (both beats and T7) must have a tag that starts with the trace ID and states its scope ("shows", "illustrates" or "does not"). Every caption label must carry `X · NAME`, "fictional witness · staged" and `seg X`.
5. **Image proves memory.** A claim whose text matches "image proves" or "proves … memory" may be projected only if a Match exists. C6 must also stay `project=false` while the Match set is empty.
6. **Disputed evidence kept.** C3's testimony refs (A2, B2, B3) must all be in the cut, and its trace (T1) must be used. Both movements must be exactly 25.0 s, and the shots must be contiguous and sum to 25.0 s.
7. **Further checks.**
   - Each caption's transcript revision must equal its segment's revision.
   - No line contains "Bourr" (I8).
   - Each line ID's speaker must match its label.
   - Bell and key order must be S1 before S2 inside Beat A and S2 before S1 inside Beat B.

## 4 · Measurements on the render (`assets/films/recits-dellis-island.mp4`)

- **Duration** is 60.000 s; ffprobe counts 1440 frames. **Size** is 3,001,923 bytes.
- **Onsets** (from the decoded AAC, 2 ms envelope, 30 % threshold): bell 33.606 / keys 35.401 under A; keys 44.602 / bell 47.606 under B. Ledger replays: 49.906 (L −11.7 / R −24.0 dB), 50.602 L, 51.602 R, 52.406 (R −11.8 / L −24.1 dB). All are within ±0.01 s of plan §6.
- **Beat A vs Beat B frame diff:** decoded frames at 34 s and 45 s, rows 0–457 (everything above the caption band). Mean absolute difference 0.067/255, max 37 (H.264 noise only). The source frames before encoding are identical (diff 0.0).
- **Declared silences are digital zero:** 0–2.2, 28.7–30, 30–32.5, 38.6–41, 41–43.5 and 55.1–60 all measure −180 dB.
- **Levels:**
  - Movement I bed: −37 dB RMS. The T6 stretch, where S3 thins, is −40.7 dB.
  - Bell strikes: about −14.5 dB RMS over 250 ms.
  - Key hits: about −27 dB RMS. They are a short transient; the peaks are comparable to the bell's.

## 5 · Baseline and branch

- **`baseline.mp4`** (private; the conventional cut the beat must beat) runs 14 s.
  - Only account A is used: A1–A4 as bare captions, with no speaker, interval or staged label.
  - The picture is a slow push-in on the T1 crop. The bell is at 3.6 s and the keys at 5.4 s.
  - The T7 insert has no tag. B is dropped and there is no ledger and no source card.
  - It exists for comparison only and must not be published.
- **`order-BA.mp4`** (private named branch, plan §3.5 divergent view). B's block plays first and A's second:
  - B: sheet B1 30.0–32.5; Beat B 32.5–38.5, keys at 33.6 and bell at 36.6.
  - A: sheet A1 38.5–41.0; Beat A 41.0–47.0, bell at 42.1 and keys at 43.9; T7 with A4 47.0–49.5.
  - The ledger (49.5–55.0) and the claim graph are identical; this part is equivalent.
  - The coda states "THIS IS BRANCH order-BA … private".
  - It is not merged into the public cut.

## 6 · What is foraged, what is handmade, what is declared

- **Foraged (Commons):**
  - T1, T2: Daniel Jolivet, CC BY 2.0.
  - T6: PO map of March 1904, BnF, public domain.
  - T7: Méliès 1896, public domain.
  - S1: Olga Ernst, CC BY-SA 4.0.
  - S2: Gravity Sound, CC BY 4.0.
  - S3: Robert EA Harvey, CC BY-SA 4.0.
  - S4: Juandev, CC BY-SA 3.0.
  - Full records are in `films/credits/recits-dellis-island.json`.
- **Not used:** T3, T4 and T5 are alternates now that T6 was found. S3b and S4b are alternates. S5 (a cathedral, not a small room) was declined, and declared silence is used under the sheets instead.
- **Handmade:** the title and section cards; the testimony records (U3; the script uses only A1 and B1 on screen); the caption bands; the ledger card; the coda card; and the two map markers, each labelled "(marker added)".
- **Declared silence:** the opening to 2.2 s, the interstitial card, both sheets, T7 (silent film), and the coda.

## 7 · Known weaknesses (for the reviewer)

- **S2 is keys hitting a tree, not a key set on a bench.** It is tagged "keys against wood · recorded elsewhere", and the coda says it is not a key on a bench.
- **S1 is a mechanical station signal bell** (Fridingen, DE), not a hand-rung platform bell. Its attack clips slightly.
- **S4 is very low under S3's bed and may be barely perceptible.** Nobody has listened to any of the audio; it was checked only by measurement and spectrogram.
- **The fonts lack ě, ř, š, Ž and →.** S4's Czech title is shown on the coda without accents, and the card says so. Arrows are drawn as shapes or written as "then". The credits JSON keeps the exact title.
- **Some tags are small.** The T6 marker labels are small mono text, and the "heard" line in the beats is about 11–13 px. The source-card text is dense for a 6 s shot, which needs a perceptual check in viewing conditions.
- **The local images are Commons 1920 px thumbnails, not the originals** (HTTP 429 on originals). Their sha256 values are of the thumbnails.
- **B4's caption lasts only 1.3 s** (48.2–49.5).
- **Not yet done:** an independent reviewer's viewing, and a test of whether the photo reads as proof (§2 failure test). If that test fails, the §8 repair (move T7 before Beat A, or add a source card to Beat A) is ready but not rendered.

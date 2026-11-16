# Assembly: Monsieur Ripois / « Rien n'y manquait »

Editor's assembly of `films/monsieur-ripois.py` (kit `Film`, 960×540, 24 fps, 44.0 s, 1056 frames). The picture is 720×540 (4:3), centred, with 120 px of black pillarbox on each side. The script imports `present_puppets.py` (U2) and `shadow_theatre.py` (U3) and mixes U1's `mix-<variant>-loud.wav` (U1's mix, loudness-normalised with two-pass ffmpeg loudnorm; master measures -23.3 LUFS integrated, true peak -2.3 dBFS) with `mix.add` (L/R), as listed in `sound-manifest.json`. All three cuts come from the same script:

| cut | command | output |
|---|---|---|
| master | `python3 films/monsieur-ripois.py` | `assets/films/monsieur-ripois.mp4` |
| baseline | `--baseline` | `films/swarm/monsieur-ripois/cuts/monsieur-ripois-baseline.mp4` |
| late | `--late` | `films/swarm/monsieur-ripois/cuts/monsieur-ripois-late.mp4` |
| P4 check only | `--check` | stdout |

## Timecoded sequence (master), with evidence IDs (ledger.json)

| shot | time (s) | frames | content | claims / evidence | sources |
|---|---|---|---|---|---|
| S0 | 0.00–2.00 | 0–47 | Black; « Rien n'y manquait » in white serif italic, fading in (7–19) and out (36–48). Room tone comes in at 1.5 s. | — | handmade type |
| S1 | 2.00–9.00 | 48–215 | Present two-shot. The box sits on HER lap between the two heads (centre ~46 % of picture width), its foot behind the foreground sofa arm, her right forearm (coat sleeve and glove, one jointed piece) holding its left end. She sets it down (132–150) on « en main propre ». He leans in on « rapportée » (82–94). Her head holds 0° under C1/C2. Her thumbs lift the lid 10 % on « ouverte » (185–196). Captions CAP-C1a 60–130 (parts at 60/82/101), CAP-C1b 130–158, CAP-C2a 173–216. | C1, C2a; E1 (room, observed: the box on her lap is consistent with C1: it is back in the family's hands) | V0 plate, GrabCut pieces and sofa-arm occluder, V1 sleeve+glove, handmade box; sounds: clock, room tone, chair creak (82), knock as set-down (144), cupboard clasp tick (186) |
| S2 | 9.00–19.50 | 216–467 | Shadow flashback, warm paper, « — selon lui — » on every frame. Door (3 drawings) and walk, with feet on parquet at 234/242/250/258. Offer (288–347). Aunt opens the lid and the ring shows as punched light (348–376; ring visible 368–405). **Swallow**: the box is inside his torso silhouette for 406–413 and the lid shuts there, heard at 408. Hand-off (430), set on her lap (456). Captions CAP-C2b « La bague y était. » 355–394 and CAP-S2d 422–466. | C2b, C3-prep; **E2** (teller, subjective; silent on the palm) | handmade puppets, set and paper; V0 blinds far plane; muffled, reverberant bed (650 Hz low-pass, 1.6 s IR) |
| S3a | 19.50–21.50 | 468–515 | **Cut frame 468**: present insert of the open box on her lap with the ring slot **empty** (slot norm_x 0.485; the ring was at 0.500 in S2). The bed is dry again and the tint and label are gone on this frame. | **E3a** (material: contests C3, not who did it) | handmade box (no added grain); V0 lap fabric plane (print grain on it only); V1 sleeve+glove |
| S3b | 21.50–29.00 | 516–695 | Two-shot, box open. « Rien n'y » 567, « manquait. » appended at **586**. Her head starts its −11° drop at 586 (first changed frame 587) over 8 frames and holds. His lean (552→) stops at 586. 648–672: his right arm comes off the sofa back (CUE-3h, the hidden hand), with a cloth rustle. | C3 (asserted, contested by E3a); ListenerState: infers contradiction | as S1 |
| S4 | 29.00–31.50 | 696–755 | A folded slip slides out of his waistcoat welt pocket (held ~7 frames, 706–713, 1.3x larger than round 0), falls with gravity onto his thigh toward her, bouncing once (paper tick at 718). Her head turns to it from 734. | **E3b** (material) appears | as S1; Commons paper |
| S4i | 31.50–36.00 | 756–863 | Receipt insert: her gloves unfold it in 3 drawings (756/770/784), then a slow push onto « Engagé le 14 mars 1953 · une bague or, un brillant · Déposant : A. R. ». | **E3b** contests C3 directly and dates EV3 to the day of EV1 | handmade receipt; V0 lap plane; V1 glove; Commons paper unfolds |
| S5 | 36.00–43.00 | 864–1031 | Two-shot. Her arm carries the folded receipt (in her glove since the insert) over the box and lowers it into the slot (893–922). The lid closes in 2 drawings (940–948) with a dry click at 948 (39.5 s). She turns away (972–982) as a cutout card turn: the head card narrows edge-on over 4 frames, swaps to its mirrored card and opens over 4 frames, so her face ends toward frame-left, away from him, dropped 14°; her figure leans back 8 px (picture) following 2 frames behind. She holds. He does not move. No caption. Tone fades from 42.0. | ListenerState: withholds a reply, closes the case | as S1; Commons cupboard close as lid click |
| S6 | 43.00–44.00 | 1032–1055 | Black, silence. | — | — |

### Variants (same script, same S2 frames: replay equivalence of E2)

- **baseline**:
  - S3a is replaced by the two-shot (lid closed; CUE-2a lid lift omitted).
  - Her head is 0° throughout.
  - No receipt, no slot, no lid click. The two-shot holds from 29.0 s and fades to black over 42.0–43.0.
  - U1's `mix-baseline.wav` drops the clasp, receipt and lid sounds.
- **late**: identical to the master except her head drop, which starts at frame 610 (first changed frame 611), i.e. line end 598 + 12. His lean completes to +4° before she drops. The sound is identical.

### Cue-timing assertions (P4), run by the script before every render

The script runs `check_cues()` against `dialogue-cues.json` before each render, and the render aborts if any of these checks fails:

- master: first changed head frame 587 vs « manquait » onset 586 (±2). His lean stops within 6 frames.
- late: 611 ≥ 598 + 12.
- baseline: the head never moves.
- In all three cuts, her head is unchanged before frame 586, and every `assertions[variant]` row has `action_onset_frame ≥ onset_frame`.

## Claim / evidence ledger (summary of ledger.json; deliverable §9)

```
EV1 box returned 14 March ─┬─ asserted by C1 « …rapportée chez votre tante le 14 mars, en main propre » (S1)
                           ├─ supported by E1 (box on her lap; room, observed)          S1
                           └─ supported by E2 (shadow play; teller, subjective)        S2
EV2 aunt opens, ring there; R. closes lid; palms ring behind his body
                           ├─ first half asserted by C2 « Elle l'a ouverte… La bague y était » (S1/S2c)
                           ├─ E2 stages the first half and HIDES the palm (box swallowed 406–413)
                           └─ C3 « Rien n'y manquait » (S3b) asserts it complete: contested by
                                 E3a empty slot (S3a, material, ambiguous as to who) and
                                 E3b receipt (S4i, material, « une bague or, un brillant », 14 mars, A. R.)
EV3 R. pawns the ring the same day ── shown only by E3b
EV4 aunt passes box to listener, slot empty ── E3a
CUT(C2 → E2 → return): P1 distinct ids/files ✔  P2 perspective mark in S2 only ✔  P3 shared box-spec ✔  P4 ✔
```

## Revisions and files

- Script: `films/monsieur-ripois.py`. Credits: `films/credits/monsieur-ripois.json` (2 LoC items and 8 Commons sounds). Notes: `films/notes/monsieur-ripois.txt`.
- Critic sheet: `films/swarm/monsieur-ripois/assembly-vs-ref.jpg`, with S1, S3b and S5 frames decoded from the master mp4 beside `ripois1.webp`, plus measured stats.
- Editor changes to unit outputs:
  - U1 `build_sound.py`: the four footsteps were moved to U3's foot contacts (234/242/250/258).
  - The four missing Commons one-shots (Door handle creaking, Squeaky door hinge, Cupboarddoorclose, Knocking on wood or door) were downloaded and their licences read from the saved extmetadata.
  - `build_sound.py` and `write_manifest.py` were then rerun, so `sound-manifest.json` now exists with no missing sounds.

## Repair round 1 (critic pass=false; reviewer pass=true)

| critic note | repair | check |
|---|---|---|
| S2 carried synthetic grain | `render_flashback(grain=False)`; the editor also replaces U3's paper (it had rng mottle + random fibres) with the backlight falloff alone (214 centre -> ~180 edges, +5 % warm). Paper modulation now = backlight + foraged blinds far plane. | high-pass std of a flat paper patch (y100–160, x150–230) over all 126 drawings: 0.112–0.115, max change 0.003 (< 0.2) — `assembly-vs-ref.json` |
| print grain, vignette, defocus on made objects | `tone(..., gmask)` lays the sampled print grain only where the Vachon plate shows (box, slip, glove and sleeve masked out, in the two-shot and both inserts). Inserts: the flash pool lights only the photographed lap plane; the box keeps its own geometric shading graded to the plate's black/white points; the receipt gets a linear camera-right key gradient, no radial vignette. The receipt's back side now shows its own print through, mirrored (was a flat grey card). | code: `present_puppets.py` tone/render_box_insert/render_receipt_insert |
| box on HIS thigh, disembodied gloves, pasted look | Box re-staged on HER lap between the heads (screen x 524–787 of 1440 = 36–55 %, centre ~46 %), foot occluded by the foreground sofa arm (new GrabCut-free edge-traced matte `sofa-arm-occluder-mask.png`, `editor-build/sofa_arm_mask.py`), contact shadow on her coat. Her glove is now one piece with its coat sleeve (GrabCut of the same V1 crop, `piece-her_arm-mask.png`, `editor-build/arm_piece.py`), the forearm emerging from her own coat; one hand, as the photograph's anatomy allows (her left arm rests on the sofa back in V0). Box blurred to the plate's softness (sigma 2.4 px at 1440 = 1.2 px at 720). `silver_box.py`: metal falloff and specular streak moved to the camera-RIGHT flash side (it fell off the wrong way). | `assembly-vs-ref.jpg` |
| turn away unreadable; infill seam | Card turn with mirrored replacement head (see S5); the infill strip right of her profile was repainted from the plate's border column, and a ring across the old head contour re-inpainted (Telea) with the print's own grain restored. Limit note: the head card now ranges -14..+9° plus the mirror state (declared deviation from U2's -12..+9). | frames 972–1031 |
| mix too quiet (-34.6 LUFS) | two-pass loudnorm of U1's mixes (`mix-*-loud.wav`, listed in `sound-manifest.json`); silences S0/S6 remain digital silence | master: -23.3 LUFS I, -2.3 dBFS TP |
| receipt slip-out too small/brief | slip 1.3x, slide-out phase 0.40 of the cue (≈7 frames) | frames 706–713 |
| reviewer: note, comment, ledger wording | note rewritten (blinds tied to 2017831564, all 8 sounds named, the BY-SA one credited); `cut_pieces.py` comment fixed; ledger E1 softened to "consistent with C1", pocket = waistcoat welt everywhere | — |

Licence of the film: because two cue sounds derive from Cupboarddoorclose.ogg (CC BY-SA 3.0, Secretlondon), the soundtrack (and so the film as distributed) is offered under CC BY-SA 3.0 or later, with the attributions in `films/credits/monsieur-ripois.json`.

Protected as asked: hard cut at 468 (tint, label and reverberant bed drop on the same frame); 8-frame box swallow (406–413); captions-only voice with « Rien n'y » / « manquait. » split at 586, head drop first frame 587, `--late` 611; receipt wording; cut-card puppets and slow blinds plane; the Vachon plate and its tone.

Untouched U2/U3 originals kept for comparison: `editor-build/present_puppets.u2-original.py`, `editor-build/silver_box.u2-original.py`.

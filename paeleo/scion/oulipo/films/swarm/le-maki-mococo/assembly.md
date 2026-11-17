# le-maki-mococo · Assembly (editor rev E2)

- **Built on:** plan.md rev P1, poem `poem-r1`, cue_timeline.json (U1, rebuilt 2026-11-17 with line 3), mouth_rig.py/json (U2-r2), gong_rig.py and image_cue.json (U3).
- **Script:** `films/le-maki-mococo.py`. It renders `assets/films/le-maki-mococo.mp4`: 65.0 s, 960x540, 24 fps, 1.44 MB.
- **Test shot:** `films/sources/le-maki-mococo/editor/test_shot.mp4` (4.5 s) is 0:15.5–0:18.0 cut straight to 0:38.0–0:40.0.
- **Image-first baseline:** `films/sources/le-maki-mococo/editor/le-maki-mococo-image-first.mp4` (17.5 s). It is the separate condition `branches.image_first`, not a repair.
- **Comparison frames and measurements:** `films/sources/le-maki-mococo/editor/compare_06.0.png` and `compare_46.0.png`; measurements in `editor_measure.json`.

## Editor decisions (declared)

1. **Line 3 is filled, so there is no gap.** upload.wikimedia.org still returned 429 for original files. Commons *mp3 transcodes* of the same files did download, using UA `oulipo-film-research/1.0` with slow retries: Vealhurl *popcorn*, and Grendelkhan *smells, of, never, rings, pop, corn*. About 0.1 MB in total.
   - Licences were already read from extmetadata by U1 (`u1/meta.json`).
   - U1's `build_voice.py` and `make_timeline.py` were re-run. The voice is now 10.19 s and all 16 words are real recordings. U1's fixture check passed.
2. **Staging, option (b).** The measured voice runs past the plan's 0:10 and 0:24 response times. Each guess is therefore said 0.4 s after the voice it answers ends:
   - R1 is said at 12.59 (label 0:12);
   - R2 is said at 26.09 (label 0:26).
   - Reader A's gong is assembled only after R1 is said (T_ASM 13.04).
   - The gong is set swinging by R2 (T_SWING 26.09).
   - Cue times are unchanged (2.0 / 15.5 / 38.0) and P1 is re-asserted.
3. **S6: the mouth says the single "binturong" at 41.0.** It uses U1's S6 visemes, so the only voice heard in S6 is lip-synced. Surprise runs 38.3–41.0, then the speech, then back to surprise.
4. **S4 emphasis is done by greying.** The poem ink is already near-black, so the other words grey and "hangs", "swings" and "never rings" return to full ink one by one. Glyph alpha and boxes never change.
5. **Licences.** Grendelkhan's recordings are **CC0**, not CC BY-SA, according to extmetadata. Only Vealhurl's two words are CC BY-SA 4.0. The credits use the licence actually read.

## Timecoded sequence → evidence

| # | film time | picture | sound | evidence IDs / sources |
|---|---|---|---|---|
| S0 | 0:00–0:02 | Paper mouth at rest, one 1° breath. Strip ○○○. Empty cord and knot. | Room tone (kit, declared) | HANDMADE `mouth_rig` pose `rest`; `gong_rig` cord/knot |
| S1 | 0:02.0–0:12.19 | **Q_sound ●**. Mouth speaks the poem from U1's measured visemes (MBP on b/p, A widest on -rong). No text. | `voice_poem.wav` at 2.0 | voice-Grendelkhan-{in,the,dark,it,hang,is(/z/),and,swing,smells,of,never,rings}, voice-Vealhurl-{binturong,popcorn} |
| S2 | 0:12.2–0:15.5 | R1 caption (0:12.59–15.25). Silent "hm", then a slight open. Gong assembled one wedge per 2 frames from 13.04, then labelled "Reader A's picture (guess)". | Room tone; 12 paper ticks (kit) | R1 (cue_timeline.responses); HANDMADE gong wedges `imagecue/wedge_00..11` |
| S3 | 0:15.5–0:25.69 | **Q_text ●**. The voice replays; each syllable's letters land on its measured onset with a rose cursor. Mouth synced on the same seg_ids. **TEST SHOT 15.5–18.0.** | `voice_poem.wav` at 15.5 (identical bytes) | same voice IDs; glyph table `mouth_rig.GLYPHS` (sha1 asserted) |
| S4 | 0:25.9–0:31 | Lip set B (mauve). Jaw eases to 2.8°. R2 caption (26.09–31.6). Gong swings as a damped pendulum. Poem greys and "hangs", "swings", "never rings" come forward one by one. | Room tone; one cord creak (kit) | R2; HANDMADE |
| S5 | 0:31–0:38 | Expressive hold: lip set A, closed, one slow breath (34.5 s). Pendulum settles. ○ image still empty. | **Declared silence**: room tone only (measured RMS 0.0008 ≈ -62 dBFS) | — |
| S6 | 0:38.0–0:44 | **Q_image ●** at 38.00. The 12 wedges tear loose one per 3 frames, bottom first, and fall ballistically in front of the animal. Brehm/Specht binturong revealed hanging by its tail from the **same knot**. Slow surprise; "binturong" said at 41.0. Engraving label at 39.6. | 12 paper tears + 12 landings, flop 38.5, soft creak (all kit, declared); `voice_binturong.wav` at 41.0. **No ring.** | brehm-265 (Commons, PD); cutout `imagecue/binturong_hang_rgba.png`; voice-Vealhurl-binturong |
| S7 | 0:44–0:52 | "O", then the mouth closes. R3 caption (44.0–51.8), stepping back to 60% when R4 enters (48.5–51.8, 3.3 s ≥ 2.5 s). | Room tone | R3 (shift clue "by its tail" ← Q_image), R4 (alternate) |
| S8 | 0:52–1:00 | Poem at full ink in the same boxes. Red pencil under "hangs" in two strokes (52.0–52.9 and 53.1–53.8). Mouth speaks L1. Binturong still. | `voice_L1.wav` at 52.0 | voice IDs for L1; HANDMADE pencil |
| S9 | 1:00–1:05 | End card: "Same poem. Sound 0:02 · text 0:15 · image 0:38. Readers A and B are fictional." Credits line. | Silence (room tone ends at 60.0) | — |

The cue strip (● released / ○ not yet) and a timestamp `m:ss.d` are drawn on every frame, 0:00–1:05.

## Asserted in the script (every run, including stills)

- **Invariant 1, cue order.** The script asserts:
  - Q_sound 2.0 < Q_text 15.5 < Q_image 38.0;
  - the first voice sample is at Q_sound;
  - no syllable onset falls before Q_text, and the type layer's alpha is 0 at 0.0 and at 15.458;
  - gong_rig's Q_image equals 38.0 (the engraving is not drawn before it; U3's own assert).
- **Invariant 2, poem fixed.** The script checks:
  - the cue_timeline lines equal `mouth_rig.POEM`;
  - the glyph-box table sha1 is constant;
  - the "hangs" alpha crop is identical at 24, 46 and 58 s;
  - the full poem alpha at 30 s equals the alpha at 38, 46 and 59.9 s.
  - Measured: the "hangs" alpha diff between 0:24 and 0:46 is 0, and the knot is at (850, 150).
- **Invariant 3, P1.** The script checks:
  - every shown response's cites were released at or before `t_said`;
  - every caption appears at or after `t_said`;
  - all speakers are "(fictional)";
  - the counterexample X1 is rejected;
  - R3 contains "by its tail" and cites Q_image, while R1 and R2 do not cite Q_image;
  - R4 is held for at least 2.5 s;
  - the gong is assembled after R1.
- **Invariant 7, no ring.** `mix.bell` and `mix.ring` are replaced by functions that raise. Every SFX kind is one of tick, creak, tear, land or flop, and the fracture window 38–44 s contains only tear, land, flop and creak.

## Reader-response audit (the ledger as shown on screen)

| id | speaker | t_said | label | cites (released at) | quoted span (verbatim) | hypothesis → next observation |
|---|---|---|---|---|---|---|
| R1 | Reader A (fictional) | 12.59 | 0:12 | sound (2.0) | "A gong? Something you strike — bin, tu, RONG." | struck metal, onomatopoeia → spelling would test it ("never rings" would contradict) |
| R2 | Reader B (fictional) | 26.09 | 0:26 | sound (2.0), text (15.5) | "It hangs and swings… a lantern? A bell that's gone quiet?" | suspended, silent object → a picture would test whether it is an object at all |
| R3 | Reader A (fictional) | 44.0 | 0:44 | text (15.5), image (38.0) | "Oh — it hangs by its tail. 'Never rings': it was never a gong." | **shift from R1, clue "by its tail" ← Q_image** → re-hearing L1 tests "hangs/swings" as the animal's movement |
| R4 | Reader B (fictional) | 48.5 | 0:48 | text, image | "Maybe. It still swings like a lantern — I'd want to see it move." | alternate kept open → moving footage (not released) would decide |
| X1 | (counterexample) | 10.0 | — | image | "an animal that hangs by its tail" | **quarantined**: Q_image 38 > 10 (P1 fails) |
| B1, B2 | image-first branch | 13.69, 15.69 | — | image (2.0), sound (3.0) | see cue_timeline `branches.image_first` | staged; rendered as the 17.5 s baseline. No gong is ever imagined, so "hangs" carries no shift |

**Which clue shifted the reading?** The image (Q_image 0:38): the tail on the knot. It was checked against the text ("never rings"). **Was an alternate kept?** Yes: R4, held 3.3 s. **Does the cut preserve the order in which clues became available?** Yes. The strip, the audio placements and the type layer are all asserted against the same cue times.

## Fiction / consent ledger

- **Readers A and B** are fictional, with no participant. They are labelled "(fictional)" on every caption and on the end card.
- **Real people** are only the Lingua Libre speakers:
  - Grendelkhan, CC0, 13 words plus the /z/ of "is";
  - Vealhurl, CC BY-SA 4.0, "binturong" and "popcorn".
- They published these recordings themselves on Commons, and that is the consent scope. They are credited by username and are never presented as the readers.
- Their single words are re-ordered into a poem they never read. The end card says so.

## Declared synthesis and silences

- **Kit synthesis (non-speech only):**
  - room tone;
  - 12 pin ticks (S2);
  - cord creaks (S4, S6);
  - 12 paper tears and 12 landings (S6);
  - a low card "flop" (38.5).
- **No paper-tear recording:** the one PD candidate stayed at HTTP 429 (U3).
- **No ring. No synthetic speech.**
- **Silences:**
  - 0–2;
  - 12.19–15.5;
  - 25.69–41.0 (S5 31–38 is the declared expressive silence);
  - 41.77–52;
  - 55.08–65 (end card silent from 60).

## Acceptance 6–7 (measured, editor_measure.json; frames beside maki.webp)

| measure | 0:06 | 0:46 | target |
|---|---|---|---|
| skin median ΔE76 vs #CA9A8A | 3.4 | 3.4 | < 12 |
| lip median ΔE76 vs #9D565D | 5.7 | 5.6 | < 15 |
| lip span (height / width) | 42.0% / 30.8% | 40.7% / 30.1% | ≥ 35% / ≥ 22% |
| skin right edge | x 42.2% | x 42.2% | < 45% |
| skin cut by the top and bottom edges | yes | yes | yes |
| face area (skin + lips + cavity) | 40.5% | 40.6% | 35–50% |
| white field (right half, excluding layers) | 255/255/255 | 255/255/255 | ≥ 250 |
| luma < 80, left (mouth) half | 0.8% of frame, 95% of it in the mouth | 0.8% | ≤ 4%, cavity only |
| luma P5 / P25 / P50 | 126 / 161 / 255 | 91 / 148 / 249 | ref 97 / 167 / 255 |

At 0:46 the frame as a whole is 4.5% below luma 80. That dark mass is the black B&W engraving and the caption ink, in the right field (declared off-palette in plan §7). It is not in the mouth region.

## Pending (not judged here)

- An ear check of lip sync at normal speed was not done: there is no audio playback in this environment. The timing is verified structurally against U1's waveform-measured onsets and the mp4's audio envelope. Voiced spans in the render start at 2.00, 15.50, 41.15 and 52.00, matching the placements.
- The independent critic review has not been run.

# le-maki-mococo · Assembly (editor rev E4, repair round 2)

- **Built on:** plan.md rev P1, poem `poem-r1`, cue_timeline.json (U1, line 3 filled; responses re-staged by `editor_ledger.py`), mouth_rig.py/json (U2-r2 + E3 material repair), gong_rig.py / image_cue.json (U3) with the gong re-made by `u3/make_gong.py` (E3).
- **Script:** `films/le-maki-mococo.py` renders `assets/films/le-maki-mococo.mp4`: 65.0 s, 960x540, 24 fps, 1.78 MB (1,776,917 bytes).
- **Test shot:** `films/sources/le-maki-mococo/editor/test_shot.mp4` (4.5 s): 0:15.5–0:18.0 cut straight to 0:38.0–0:40.0, rebuilt with the E4 teeth and gong.
- **Image-first baseline:** `films/sources/le-maki-mococo/editor/le-maki-mococo-image-first.mp4` (17.5 s), the separate condition `branches.image_first`.
- **Ledger tools (E4):** `python3 films/le-maki-mococo.py --dump-ledger` writes `editor_e4_dump.json` (the cut's own SFX list, decoder paths, gestures); `editor_ledger_e4.py` merges it into `cue_timeline.json` and `mouth_rig.json`; `editor_room_levels.json` holds the room-tone levels measured on the decoded mp4.
- **Measurements:** `editor_measure.json` (acceptance 6–7, frames beside maki.webp: `editor/compare_06.0.png`, `compare_46.0.png`) and `e3_check.json` (repair acceptance tests, measured on the decoded mp4; script `e3_check.py`).

## Repair round 2 (critic + reviewer) — what changed (E4)

1. **Ledger of record = the mix (disclosure).** `cue_timeline.json` → `declared_silences_and_synth` is now written from the film's own `sfx_events()` (= `gong_rig.events()` + the pencil), not by hand: `sfx_events` lists all **41** synthesised events at their mixed times, and `synthesized_effects` groups them: 12 ticks **13.158–14.075**, cord creak **26.562** (S4), 12 tears **38.000–39.375**, 12 landings **38.776–40.318**, flop **38.500**, soft creak **39.100** (S6), pencil scratch **52.0–52.9 / 53.1–53.8** (S8; this sound was declared before but not mixed: it is now mixed). Silences carry the levels measured on the decoded E4 mp4 (`editor_room_levels.json`): S0 **-55.5**, S5 **-65.2**, S7 **-55.5 dBFS** (the stale "-40 dB" is gone). **Invariant 8** (new, asserted on every render): ledger `sfx_events` == mixed SFX, kind and time within one frame; `fixture_check.sfx_ledger` records it. Heard peaks in the decoded mp4: creak 26.73 (0.35 s hanning swell from onset 26.56), flop 38.50, soft creak 39.25 (from 39.10), first tick 13.16.
2. **Q_image 'what'** now reads "…cut out and re-hung by us by its tail from the knot (in the original it stands, tail round a branch)".
3. **Brehm credit corrected** to the tags actually on the Commons page: `{{PD-scan|PD-old-70-1923}}` **and** `{{CC-BY-2.0}}` (BHL Flickr upload, FlickreviewR pass). Scan attributed "Biodiversity Heritage Library, CC BY 2.0 tag on Commons" with the Flickr link, beside the PD status; "PD-old-70-expired" removed from credits and image_cue.json. The end card says it too.
4. **Framing metric settled (declared, not substituted).** On maki.webp the whole flesh mass is **38.6%** and skin alone at most **~31%**, so the bar's 35–50% describes the flesh mass. plan.md bar 7 now says so (editor amendment E4, original wording quoted). Skin alone in the film is **27.6% (0:06) / 28.4% (0:46): below 35%, a declared deviation.** Zooming would not help: the lip front is the zoom centre, so a closer crop enlarges the lips and *lowers* the skin share while skin must stay left of 45%.
5. **Guess times in the bar.** plan.md (editor amendment E4) makes the acceptance times the staged ones, R1 **0:12.625**, R2 **0:26.125**; `plan_t_said` 10.0 / 24.0 and the reason stay in the ledger.
6. **Teeth rebuilt as cut paper** (`mouth_rig.Rig._teeth`): 8 upper and 5 lower teeth, each its own small piece of cream card with its own scissor wobble, size and tone, fibre and grain, a lit cut edge, glued back to front so each front tooth casts a small soft shadow on the one behind; the upper lip's cast shadow falls on them. No ruled lines.
7. **Gong re-made to read as a gong** (`u3/make_gong.py`, E4 block): darker bronze-ink card; a separate glued **rim flange** (own wobbly inner cut edge, lit edge, shadow cast onto the face, printed line); a wide **embossed boss** (pressed card dome in matte tone steps, printed groove round it, cast shadow); sparser printed hammer marks. Max luma 198 (matte). Sound unchanged, no ring.
8. **mouth_rig.json** decoder paths regenerated from the render's own decoded path over the measured voice spans: S1 2.0–12.19, S3 15.5–25.69, S6 38–44, S8 52–55.08. MBP on twos at 5.33–5.50, 6.17–6.25, 7.33–7.50 (m of "smells"), 8.25–8.50 ("popcorn"), 10.42–10.50, 11.33–11.50 (the b's of each "binturong"; closures lead the 5.40 / 6.29 / 10.53 / 11.42 onsets by one decoder lead frame). Flicker over the whole 65 s path: **0**. `gesture_events()` retimed to the staged responses: the 'hm' at 10.0 that overlapped L4 is gone ('hm' now 12.425, after the voice ends).
9. **End card** adds the Vealhurl Commons file links and a pointer to the credits file for all 14 links (BY-SA attribution: title, author, source, licence).

## Repair round 1 (critic + reviewer) — what changed

1. **Material: the mouth is now visibly cut paper** (`mouth_rig.py`, marked E3). The continuous airbrushed relief is replaced by a *stack of flat paper sheets*: each piece's tone is quantised into cut steps (3 per side), each step edge is a hand-wobbled contour, the lighter sheet is lit on its up-left cut edge and casts a small soft shadow down-right on the sheet below. Paper formation grain (1–3 px) and long fibres on skin and lips. Scissor wobble raised (WOBBLE 1.7, with a ~17 px wavelength term). The specular glaze blob and glints are gone; the gloss is a separate cut sheet of pale glazed tissue on the lower lip with its own edge and shadow. Inter-layer cast shadows strengthened (upper lip on lower lip/teeth, head on jaw, lower lip on chin).
   - Measured on the decoded mp4 (`e3_check.json`): lower-lip band-pass (1–3 px) luma std **5.96–6.45** at 0:06, 0:17, 0:29, 0:46, 0:54 (target ≥ 4). Contour deviation from a smooth (σ 12 px) curve per 20 px window: median max deviation 1.07 px (lower lip), 0.97 (upper lip), 1.21 (head); 60 % / 42 % / 76 % of windows ≥ 1 px. *Not every* 20 px window reaches 1 px (declared).
2. **The gong is a printed ochre card**, not lit metal (`u3/make_gong.py`, E3 block): flat ochre card with the gong printed in brown ink (rim band, shoulder line, hammer marks as printed crescents), the boss a second paler card disc glued on with a lit edge and cast shadow; fibre + grain; no specular. Source max luma 190; rendered (eroded mask, 0:20) see `e3_check.json` `gong_max_luma` (≤ 240).
3. **Ledger = cut.** `editor_ledger.py` writes the staged times into cue_timeline.json: R1 t_said **12.625** (label 0:12), R2 **26.125** (label 0:26), frame-aligned, with `plan_t_said` 10.0 / 24.0 kept and the reason (the measured voice ends at 12.19 / 25.69; option b). `on_screen_label` is now exactly what is drawn for all four responses (R3/R4 cites in strip order "text, image (0:38)"), plus `first_frame_shown`. `u1/fixture_check.py` now checks against the responses' own t_said and was re-run: passed, no warnings. The film asserts ledger label == drawn label and first frame == t_said (± 1 frame); the caption is visible from that frame.
4. **R1's caption no longer spells the word before Q_text:** "A gong? Something you strike." (plan text kept as `quoted_span_plan`; declared revision).
5. **Medial p of "popcorn" closes.** For a C-V-C syllable whose vowel is shorter than 0.13 s, the flanking closures are trimmed to one pair of frames and the vowel gets the middle; every MBP is held ≥ 0.09 s. Decoded path S1 8.25–8.63: MBP MBP MBP MBP **O O MBP MBP** LNT LNT (S3 identical, 21.75–22.13). Flicker 0. Every "binturong" still closes on b.
6. **Cavity wedge at 0:08.2 / 0:21.7 ("of", F/V pose)** removed: the cavity card and the lower-teeth/tongue card are trimmed behind the tucked lip.
7. **mouth_rig.json** `timing_status` = `measured` (U2's provisional note kept as `timing_note_U2`).
8. **Closer framing:** the mouth is framed 1.35x closer about the lip front (432, 150); speech poses now span ≥ 54 % of frame height (see acceptance table). Lip set B measured ΔE76 9.3–10.6 by U2 (< 15), unchanged colours.
9. **Room tone:** (E3 claimed this; it was only fixed in this file. E4 fixes it in the ledger itself, item E4-1.)
10. **Engraving disclosure (reviewer):** from the first frame of Q_image (0:38.0) the label reads "cut out from Brehm, 1895 (engraved by F. Specht) / hung here by us, by its tail, from our cord; / in the original it stands, tail round a branch". The end card repeats it; credits `used_as` says it too, and notes the Commons 1280 px thumbnail and the four Brehm co-authors from the Artist field.
11. **BY-SA obligations:** end card and credits state the edits (trimmed, loudness-matched, re-ordered, /z/ splices) and declare the soundtrack CC BY-SA 4.0 (ShareAlike). Note corrected to "14 single-word recordings (16 words)".

## Editor decisions (declared)

1. **Line 3 is filled, so there is no gap.** upload.wikimedia.org still returned 429 for original files. Commons *mp3 transcodes* of the same files did download, using UA `oulipo-film-research/1.0` with slow retries: Vealhurl *popcorn*, and Grendelkhan *smells, of, never, rings, pop, corn*. About 0.1 MB in total.
   - Licences were already read from extmetadata by U1 (`u1/meta.json`).
   - U1's `build_voice.py` and `make_timeline.py` were re-run. The voice is now 10.19 s and all 16 words are real recordings. U1's fixture check passed.
2. **Staging, option (b).** The measured voice runs past the plan's 0:10 and 0:24 response times. Each guess is therefore said 0.4 s after the voice it answers ends:
   - R1 is said at 12.625 (label 0:12; E3: now also the ledger time);
   - R2 is said at 26.125 (label 0:26; E3: now also the ledger time).
   - Reader A's gong is assembled only after R1 is said (T_ASM 13.075).
   - The gong is set swinging by R2 (T_SWING 26.125).
   - Cue times are unchanged (2.0 / 15.5 / 38.0) and P1 is re-asserted.
3. **S6: the mouth says the single "binturong" at 41.0.** It uses U1's S6 visemes, so the only voice heard in S6 is lip-synced. Surprise runs 38.3–41.0, then the speech, then back to surprise.
4. **S4 emphasis is done by greying.** The poem ink is already near-black, so the other words grey and "hangs", "swings" and "never rings" return to full ink one by one. Glyph alpha and boxes never change.
5. **Licences.** Grendelkhan's recordings are **CC0**, not CC BY-SA, according to extmetadata. Only Vealhurl's two words are CC BY-SA 4.0. The credits use the licence actually read.

## Timecoded sequence → evidence

| # | film time | picture | sound | evidence IDs / sources |
|---|---|---|---|---|
| S0 | 0:00–0:02 | Paper mouth at rest, one 1° breath. Strip ○○○. Empty cord and knot. | Room tone (kit, declared) | HANDMADE `mouth_rig` pose `rest`; `gong_rig` cord/knot |
| S1 | 0:02.0–0:12.19 | **Q_sound ●**. Mouth speaks the poem from U1's measured visemes (MBP on b/p, A widest on -rong). No text. | `voice_poem.wav` at 2.0 | voice-Grendelkhan-{in,the,dark,it,hang,is(/z/),and,swing,smells,of,never,rings}, voice-Vealhurl-{binturong,popcorn} |
| S2 | 0:12.2–0:15.5 | R1 caption (0:12.625–15.25; ledger t_said 12.625). Silent "hm" (12.425), then a slight open. Printed card gong (rim flange, embossed boss) assembled one wedge per 2 frames from 13.075, then labelled "Reader A's picture (guess)". | Room tone; 12 paper ticks 13.158–14.075 (kit) | R1 (cue_timeline.responses); HANDMADE gong wedges `imagecue/wedge_00..11` |
| S3 | 0:15.5–0:25.69 | **Q_text ●**. The voice replays; each syllable's letters land on its measured onset with a rose cursor. Mouth synced on the same seg_ids. **TEST SHOT 15.5–18.0.** | `voice_poem.wav` at 15.5 (identical bytes) | same voice IDs; glyph table `mouth_rig.GLYPHS` (sha1 asserted) |
| S4 | 0:25.9–0:31 | Lip set B (mauve). Jaw eases to 2.8°. R2 caption (26.125–31.6; ledger t_said 26.125). Card gong swings as a damped pendulum. Poem greys and "hangs", "swings", "never rings" come forward one by one. | Room tone; one cord creak 26.562 (kit) | R2; HANDMADE |
| S5 | 0:31–0:38 | Expressive hold: lip set A, closed, one slow breath (34.5 s). Pendulum settles. ○ image still empty. | **Declared silence**: room tone only, measured **-65 dBFS** (decoded mp4, 31.5–37.5), 10 dB under the rest of the room tone (-55 dBFS) | — |
| S6 | 0:38.0–0:44 | **Q_image ●** at 38.00. The 12 wedges tear loose one per 3 frames, bottom first, and fall ballistically in front of the animal. Brehm/Specht binturong revealed hanging by its tail from the **same knot**. Disclosure label from 38.0 ("cut out from Brehm … hung here by us … in the original it stands"). Slow surprise; "binturong" said at 41.0. | 12 paper tears 38.000–39.375 + 12 landings 38.776–40.318, flop 38.500, soft creak 39.100 (all kit, declared); `voice_binturong.wav` at 41.0. **No ring.** | brehm-265 (Commons, PD); cutout `imagecue/binturong_hang_rgba.png`; voice-Vealhurl-binturong |
| S7 | 0:44–0:52 | "O", then the mouth closes. R3 caption (44.0–51.8), stepping back to 60% when R4 enters (48.5–51.8, 3.3 s ≥ 2.5 s). | Room tone | R3 (shift clue "by its tail" ← Q_image), R4 (alternate) |
| S8 | 0:52–1:00 | Poem at full ink in the same boxes. Red pencil under "hangs" in two strokes (52.0–52.9 and 53.1–53.8). Mouth speaks L1. Binturong still. | `voice_L1.wav` at 52.0; pencil scratch 52.0–52.9, 53.1–53.8 (kit) | voice IDs for L1; HANDMADE pencil |
| S9 | 1:00–1:05 | End card: "Same poem. Sound 0:02 · text 0:15 · image 0:38. Readers A and B are fictional." Credits: 14 recordings, edits stated, soundtrack CC BY-SA 4.0; engraving cut out and re-hung, original pose stated. | Silence (room tone ends at 60.0) | — |

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
- **Invariant 7, no ring.** `mix.bell` and `mix.ring` are replaced by functions that raise. Every SFX kind is one of tick, creak, tear, land, flop or scratch, and the fracture window 38–44 s contains only tear, land, flop and creak.
- **Invariant 8 (E4), ledger = mix.** After mixing, the list of mixed SFX equals `cue_timeline.json` `declared_silences_and_synth.sfx_events` (same kinds, times within 1/24 s); the render refuses to run otherwise.

- **E3 additions.** Ledger `on_screen_label` == the drawn label, `first_frame_shown` == the caption's first frame (± 1 frame), captions start on a frame; `t_said` read from the ledger (no override in the script).

## Reader-response audit (the ledger as shown on screen)

| id | speaker | t_said | label | cites (released at) | quoted span (verbatim) | hypothesis → next observation |
|---|---|---|---|---|---|---|
| R1 | Reader A (fictional) | 12.625 | 0:12 | sound (2.0) | "A gong? Something you strike." (E3 revision; plan text kept as quoted_span_plan) | struck metal, onomatopoeia → spelling would test it ("never rings" would contradict) |
| R2 | Reader B (fictional) | 26.125 | 0:26 | sound (2.0), text (15.5) | "It hangs and swings… a lantern? A bell that's gone quiet?" | suspended, silent object → a picture would test whether it is an object at all |
| R3 | Reader A (fictional) | 44.0 | 0:44 | text (15.5), image (38.0) | "Oh — it hangs by its tail. 'Never rings': it was never a gong." | **shift from R1, clue "by its tail" ← Q_image** → re-hearing L1 tests "hangs/swings" as the animal's movement |
| R4 | Reader B (fictional) | 48.5 | 0:48 | text, image | "Maybe. It still swings like a lantern — I'd want to see it move." | alternate kept open → moving footage (not released) would decide |
| X1 | (counterexample) | 10.0 | — | image | "an animal that hangs by its tail" | **quarantined**: Q_image 38 > 10 (P1 fails) |
| B1, B2 | image-first branch | 13.69, 15.69 | — | image (2.0), sound (3.0) | see cue_timeline `branches.image_first` | staged; rendered as the 17.5 s baseline. No gong is ever imagined, so "hangs" carries no shift |

**Which clue shifted the reading?** The image (Q_image 0:38): the tail on the knot. It was checked against the text ("never rings"). **Was an alternate kept?** Yes: R4, held 3.3 s. **Does the cut preserve the order in which clues became available?** Yes. The strip, the audio placements and the type layer are all asserted against the same cue times.

## Fiction / consent ledger

- **Readers A and B** are fictional, with no participant. They are labelled "(fictional)" on every caption and on the end card.
- **Real people** are only the Lingua Libre speakers:
  - Grendelkhan, CC0, 12 files: 11 words plus the /z/ of "is";
  - Vealhurl, CC BY-SA 4.0, "binturong" and "popcorn".
- They published these recordings themselves on Commons, and that is the consent scope. They are credited by username and are never presented as the readers.
- Their single words are re-ordered into a poem they never read. The end card says so.

## Declared synthesis and silences (= cue_timeline.json declared_silences_and_synth, E4)

- **Kit synthesis (non-speech only), at mixed times:** room tone 0–60; 12 pin ticks 13.158–14.075 (S2); cord creak 26.562 (S4); 12 paper tears 38.000–39.375 and 12 landings 38.776–40.318 (S6); card flop 38.500; soft cord creak 39.100 (S6); red-pencil scratch 52.0–52.9 and 53.1–53.8 (S8). 41 events in `sfx_events`; invariant 8 asserts ledger == mix.
- **Room tone levels (decoded E4 mp4):** S0 -55.5 dBFS, S5 -65.2 dBFS (declared quieter hold), S7 -55.5 dBFS.
- **No paper-tear recording:** the one PD candidate stayed at HTTP 429 (U3).
- **No ring. No synthetic speech.**
- **Silences (no voice):** 0–2; 12.19–15.5; 25.69–41.0 (S5 31–38 is the declared expressive silence); 41.77–52; 55.08–65 (end card in digital silence from 60).

## Acceptance 6–7 (measured on the E4 render, editor_measure.json; frames beside maki.webp)

| measure | 0:06 | 0:46 | target |
|---|---|---|---|
| skin median ΔE76 vs #CA9A8A | 4.7 | 4.7 | < 12 |
| lip median ΔE76 vs #9D565D | 6.1 | 5.5 | < 15 |
| lip span (height / width), speech pose LNT / rest | 56.9% / 41.7% | 54.8% / 40.6% | ≥ 35% / ≥ 22% |
| skin right edge | x 41.1% | x 41.2% | < 45% |
| skin cut by top and bottom edges | yes | yes | yes |
| flesh mass (skin + lips + cavity), the amended bar 7 | 40.9% | 41.3% | 35–50% (reference 38.6%) |
| skin alone (declared deviation) | **27.6%** | **28.4%** | below the original 35% wording; reference skin alone ≈ 31% |
| white field (right half, excluding layers) | 255/255/255 | 252/252/252 | ≥ 250 |
| luma < 80 in the mouth (left) half | 1.5% of frame | 1.0% | ≤ 4%, cavity only |
| luma P5 / P25 / P50 | 96 / 155 / 255 | 81 / 139 / 242 | ref 97 / 167 / 255 |
| cut-paper material (e3_check.json) | lower-lip 1–3 px luma std 5.96 | 6.45 | ≥ 4 |
| "hangs" alpha diff 0:24 vs 0:46 | 0 | | 0 |

At 0:46 the darker P5 / P50 come from the black B&W engraving, its disclosure label and the caption ink in the right field (declared off-palette in plan §7), not from the mouth.

## Pending (not judged here)

- An ear check of lip sync at normal speed was not done: there is no audio playback in this environment. The timing is verified structurally against U1's waveform-measured onsets and the mp4's audio envelope. Voiced spans in the render start at 2.00, 15.50, 41.15 and 52.00, matching the placements.
- The independent critic/reviewer pass of the E4 render has not been run.
- Scissor wobble reaches ≥ 1 px in 42–76 % of 20 px windows (median max deviation about 1 px), not in every window.
- The tone steps on the skin read as layered paper at film size; at 4x the paper grain is the dominant texture.

# le-maki-mococo · Director's plan (SCION swarm, rev P1)

Base revision: `prompts/le-maki-mococo.md` (as read 2026-11-16) + `proposals/proposals.md` (frozen proof).
Chosen direction: **2 "Paper Mouth" (spine) + 3 "Gong to Animal" (image cue)**. Direction 1 (archive lecturer) is dropped from the main film because of the consent problem with an identifiable person; it survives only as a note in the baseline branch. No drift from the chosen direction.

Render target: `films/le-maki-mococo.py` with `kit.Film` (960x540, 24 fps, 44.1 kHz), ~65 s, ≤ 6 MB.

---

## 1 · Creative thesis

One fixed four-line poem and one paper mouth. The viewer watches a reading **change while not one letter of the poem changes**. First a real voice says the poem with nothing to read. Then the words type themselves under the mouth, syllable by syllable. Last, an image arrives. Two fictional readers guess from what they have so far: "a gong", then "a lantern / a bell gone quiet". When the picture comes, the paper gong they imagined breaks off its cord and an animal is hanging there by its tail. One reader reconsiders and the other keeps a doubt.

The film would be bland if the cues dissolved into one another, so that the viewer could not tell which clue did the work. It would also be bland if the mouth only flapped, or if the image simply told the answer before a reader found it.

**Poem (original, frozen, revision `poem-r1`):**

```
L1  In the dark it hangs and swings,
L2  binturong, binturong,
L3  smells of popcorn, never rings —
L4  binturong, binturong.
```

The binturong (bearcat, *Arctictis binturong*) is real. It hangs by a prehensile tail, and it really does smell of popcorn: its scent marks contain 2-AP, the compound that gives popcorn its smell. That scent claim is well attested but was not re-checked in this run, so it is labelled *unknown/recalled*.

## 2 · Defining beat and comparison baseline

**Defining beat (0:44–0:52).** The word **"hangs"** sits at the same pixel position in L1 at 0:24 and at 0:44.
- At 0:24 the thing on the cord is Reader B's swinging gong/lantern.
- At 0:44 the same cord and knot hold the Brehm binturong head-down by its tail.
- Reader A says "Oh — it hangs by its tail. 'Never rings': it was never a gong."

The viewer should be able to **point at "hangs"**, and at the knot on the cord, and say that the word did not move but what it means did. A red-pencil underline draws itself under "hangs" at 0:52.

**Comparison baseline: the image-first condition.** It uses the same poem, voice and layout, but the Brehm image is released at 0:02, before the sound. In the baseline, guess 1 is expected to be "an animal hanging, a kind of monkey" and no gong is ever imagined. The "hangs" beat then carries no shift. This is a *new condition*, not a repair (§7): it gets its own trace in `cue_timeline.json → branches.image_first`. The editor renders it as a ~15 s variant (`--image-first` flag) only if the time budget allows. Otherwise it stays a ledger branch, and its responses are marked *staged prediction, not rendered*.

## 3 · Lineage Genome (compact)

| field | value |
|---|---|
| source media | a poem (Roubaud, "Le Maki Mococo"); a short documentary film of young readers voicing it (Ribot); a pedagogical reading dossier (AFL) |
| target medium | a one-minute cut-paper animation with kinetic typography, real foraged speech and a foraged 19th-c. engraving |
| preserved relation | **an unfamiliar real animal name, met first as sound, makes readers build and revise a meaning while the text stays fixed.** The maki mococo is a lemur, and our binturong plays the same part. |
| optics change | a photographed child's mouth in profile becomes a handmade, articulated paper mouth in profile. The framing (mouth left, white field right) is kept. |
| formalism change | explicit cue release (sound to text to image), a visible cue strip on every frame, and a response ledger with citation limits |
| concept change | real children become clearly fictional readers A and B (captions); the reading is staged as evidence, not as documentary |
| sound change | the reading voice is a word-collage of real volunteer recordings (Lingua Libre, CC BY-SA). There is no synthesis of speech. A declared silence is used for thought. |

**Formation epochs (weight 0–100):**
- **Oulipo constrained poetry, 1960s–80s (Roubaud): 70.** The poem-as-game and the strange-name riddle come from it.
- **French reading pedagogy, 1970s–90s (AFL "lecture" movement): 85.** The proof is a reading exercise. It is uncertain how closely Ribot's film follows the AFL protocol: the dossier PDF and the Vimeo film were not inspected in this run.
- **Silhouette/cut-paper animation, 1920s (Reiniger) to the 1970s (Gilliam): 55.** The pinned paper pieces and replacement profiles come from it.
- **19th-century natural-history wood engraving (Brehm, Specht): 40.** It is the image cue's medium and the source of the "prehensile tail" fact.
- **Kinetic typography, 1950s–2000s: 45.** Letters land as syllables are said.
- **Open crowd speech corpora, 2010s–20s (Lingua Libre/Wiktionary): 60.** It makes a real voice possible without TTS. It is also uncertain: whether one speaker covers every word is to be measured by U1.

Uncertain claims are recorded as such. The reference still (`maki.webp`) is captioned "child speaking"; we have not watched Ribot's film.

## 4 · Olog (typed state, central operation)

Types:
- `◻ TextSegment{seg_id: "L1".."L4" | "L1.w5"(word) | "L1.w5.s1"(syllable), revision: "poem-r1", display_order:int, read_order:int, glyph_box: (x,y,w,h) once typeset}`
- `◻ Cue{cue_id: "Q_sound"|"Q_text"|"Q_image", channel: sound|text|image, t_avail: seconds, linked_line: seg_id[]}`
- `◻ ReaderResponse{resp_id, speaker: "Reader A (fictional)"|"Reader B (fictional)", consent: "fictional — no participant", quoted_span: str (verbatim from ledger), t_said, cites: cue_id[], hypothesis: str, next_observation: str}`
- `◻ HangingThing{anchor: cord knot (x,y) fixed, identity: gong | lantern? | binturong, layer: hypothesis | cue}`
- `◻ Viseme{t, shape: rest|M/B/P|A(open)|O|E/I|U/W|F/V|L/N/T, jaw_deg, lip_set: A(warm)|B(cool)}`

Arrows:
- `release : Cue → Time`.
- `cites : ReaderResponse → set(Cue)`.
- `typesets : (Cue=Q_text, Syllable) → GlyphBox at onset(syllable)`.
- `voices : Syllable → (onset, offset) in voice.wav` (measured).
- `drives : (onset, offset, phoneme class) → Viseme`.
- `rewrite : HangingThing(gong) ↦ HangingThing(binturong)` (collage rule).

**Central operation: `admit_reading(r: ReaderResponse)`.**
- **Typed preconditions**
  - (P1) for every `q ∈ r.cites`, `release(q) ≤ r.t_said`;
  - (P2) the poem revision shown at `r.t_said` is `poem-r1`, with glyph boxes identical to every earlier frame where they were shown;
  - (P3) `r.quoted_span` is in the ledger verbatim and attributed;
  - (P4) `rewrite(gong→binturong)` fires only at `t ≥ release(Q_image)`, and only while the cord anchor and the "hangs" glyph box are unchanged.
- **Observable consequences**
  - The response caption appears on screen with its label "READER X (fictional) · m:ss · cites: …".
  - The cue strip then shows ● for exactly the cited cues or more, never a cited cue still ○.
  - The response's `next_observation` names what the next cue would test.
  - In the reconsideration, the caption explicitly names the clue that shifted it ("by its tail", which comes from the image).
- **Counterexample (rejected)**
  - A Reader A caption at 0:10 saying "an animal that hangs by its tail": it cites Q_image, but release(Q_image)=38 > 10, so P1 fails and the caption is quarantined.
  - Likewise, moving the engraving to 0:02 with guess 1 unchanged ("a gong?") is not a repair but a mislabelled condition. It must become `branches.image_first` with new responses.
- **Replay / alternate views**
  - **Equivalent:** replaying the mp4, scrubbing to any frame, and reading `cue_timeline.json` give the same release order. The on-frame cue strip *is* the ledger at that t.
  - The mouth-only stream and the text-only stream share segment IDs, so they agree on which syllable is current.
  - **Divergent:**
    - the listening-first film vs the image-first baseline (different responses, separate traces);
    - reading the poem off the final frame vs watching it arrive: the final frame alone cannot show that "hangs" was once a gong.

Interactive work: not applicable (screen work). TTL: default 2, unused.

## 5 · Invariants (hard; a break quarantines the candidate)

1. **Cue order** is sound (0:02) < text (0:15.5) < image (0:38). The cue strip (● released / ○ not yet) and the timestamp are on every frame from 0:00 to the end card.
2. **Poem fixed:** the four lines are the same string throughout. Once a glyph is typeset, its box never moves; fades and greys are allowed, but no reflow and no edits. The test is numeric: a glyph-box table is asserted equal across frames.
3. **Citation:** no caption cites a cue released after its own `t_said` (assert in script).
4. **Fiction/consent:** readers A and B are labelled "(fictional)" on screen and in the ledger.
   - The only real people are the Lingua Libre speakers. Their recordings were published by them under CC BY-SA 4.0, which is the consent scope.
   - They are credited by username and are never presented as Readers A or B.
5. **Responses verbatim:** captions are printed exactly as `quoted_span`. A shortened span keeps the "…" and the full text stays in the ledger.
6. **No speech synthesis:** every audible word is a real recording.
   - Silences are declared in the ledger.
   - Non-speech effects (paper ticks, room tone) may be kit-synthesized and are declared as such.
7. **The gong never rings:** when it breaks there is no metallic ring, only paper (the poem says "never rings").
8. **Material honesty:** every visible element is either HANDMADE (paper mouth, paper gong, cord, type, red pencil) or FORAGED (Brehm engraving, Lingua Libre voice). There are no photographic filters and the reference image is never pasted or traced.

## 6 · Timed shot list (the Hard proof, §6, exactly)

Layout zones at 960x540:
- **Mouth:** x 0–430 (skin may bleed off the left, top and bottom edges).
- **Poem type column:** x 455–735, y 120–330, Caladea 30 px, ink #2a2422.
- **Cord and hanging thing:** x 760–940, cord from y 0 to the knot at (850, 150).
- **Caption band:** x 455–940, y 395–520, Inter 19–21 px with an Inter Medium 13 px label.
- **Cue strip and timestamp:** top-right, y 22, Inter 13 px, muted #6b625b.
- **Field:** pure white everywhere else.

| # | time | on screen | heard | material |
|---|---|---|---|---|
| S0 | 0:00–0:02 | The paper mouth at rest, lips closed, on white. A tiny breath lifts the lower jaw 1° as the paper rocks on its pins. Cue strip ○ sound ○ text ○ image. | Room tone only (declared, kit `room`). | HANDMADE mouth. |
| S1 | 0:02–0:09.5 | **SOUND cue.** The mouth speaks the whole poem. Jaw angle and lip replacements follow the measured syllables of the recording: closed on b/m/p, wide on "-RONG", round on "pop-". **No text.** At 0:02 the cue strip becomes ● sound. | The poem in a real voice: a word-collage of Lingua Libre recordings, ~7 s. | FORAGED voice (Commons, LL-Q1860 eng, CC BY-SA 4.0). HANDMADE mouth. |
| S2 | 0:10–0:15 | **Guess 1, Reader A.** Lip set A (warm rose) stays. The mouth shapes a silent "hm" (pursed), then opens slightly. Caption: `READER A (fictional) · 0:10 · cites: sound` / "A gong? Something you strike — bin, tu, RONG." From 0:11.5, Reader A's picture is assembled in the right field: a cut bronze-card gong, one wedge per 2 frames, pinned to the cord and labelled small "Reader A's picture (guess)". | Room tone. Paper ticks as the wedges are pinned (kit `click`, declared). | HANDMADE gong + cord. |
| S3 | 0:15.5–0:23 | **TEXT cue.** The cue strip becomes ● text. The poem is spoken again, and each syllable's letters type into the column *on that syllable's measured onset*, with a rose cursor. The mouth is synced to the same syllable IDs. **TEST SHOT segment** (L1 from 0:15.5 to ~0:18). | The same voice-collage (replayed, identical bytes). | FORAGED voice. HANDMADE type and mouth. |
| S4 | 0:23.5–0:31 | **Guess 2, Reader B.** A replacement swap: the lip paper changes to set B (cooler mauve). The jaw drops 2° (thinking). Caption: `READER B (fictional) · 0:24 · cites: sound, text` / "It hangs and swings… a lantern? A bell that's gone quiet?" The gong swings on the cord as a damped pendulum, and the words "hangs", "swings" and "never rings" darken one by one (no glyph moves). | Room tone. The cord creaks once (kit, declared). | HANDMADE. |
| S5 | 0:31–0:38 | **Expressive hold.** Lip set returns to A; the mouth is closed with one slow breath. The pendulum settles. Nothing new is released; ○ image is still empty. | **Declared silence** (room tone at -40 dB). | HANDMADE. |
| S6 | 0:38–0:44 | **IMAGE cue.** The cue strip becomes ● image at 0:38.00. The gong's 12 wedges come loose one per 3 frames (0:38.0–0:39.5). Each falls on a ballistic path with spin and lands below frame. Behind them, revealed by occlusion, the Brehm/Specht binturong hangs head-down from the **same knot**: a cutout with a white paper margin, rotated so the tail meets the knot. It sways with the pendulum's residual motion, then settles. The mouth opens slowly (surprise, no speech). | Paper wedges tick and fall. **No ring.** At 0:41 the single word "binturong" is heard once, the same Lingua Libre take. | FORAGED engraving (Commons, PD). HANDMADE gong and cord. |
| S7 | 0:44–0:52 | **Reconsideration, Reader A.** The mouth makes an "O" replacement, then closes. Caption: `READER A (fictional) · 0:44 · cites: image (0:38), text` / "Oh — it hangs by its tail. 'Never rings': it was never a gong." At 0:48.5 a second caption keeps the alternate alive: `READER B (fictional) · 0:48` / "Maybe. It still swings like a lantern — I'd want to see it move." | Room tone. | HANDMADE + FORAGED (engraving stays). |
| S8 | 0:52–1:00 | **Poem unchanged.** All four lines are at full ink, in the same glyph boxes. A red pencil underline draws itself under **"hangs"** stroke by stroke (0:52–0:54). The mouth speaks L1 once more, synced. The binturong hangs at right. | Voice: L1 only (same takes). | FORAGED + HANDMADE. |
| S9 | 1:00–1:05 | End card on white: "Same poem. Sound 0:02 · text 0:15 · image 0:38. Readers A and B are fictional." It also gives the credits line (Brehm/Specht PD; voice: Lingua Libre speakers [usernames], CC BY-SA 4.0; mouth, gong, type handmade). | Silence. | HANDMADE type. |

### Element ledger (FORAGED / HANDMADE)

- **Voice: FORAGED.**
  - Search Commons for Lingua Libre English word recordings (`LL-Q1860 (eng)-<speaker>-<word>.wav`) for: in, the, dark, it, hangs, and, swings, binturong, smells, of, popcorn, never, rings.
  - Already verified: `File:LL-Q1860 (eng)-Vealhurl-binturong.wav`, CC BY-SA 4.0, speaker Vealhurl.
  - Prefer one speaker for all words. If a word is missing, use another Lingua Libre speaker, then Wiktionary `En-us-<word>.ogg` / `En-uk-<word>.ogg` (licence read from extmetadata).
  - If "popcorn" is missing, build it from "pop" + "corn".
  - If a word is still missing, it is a *declared gap*: the mouth mouths it silently and the ledger says so.
- **Image cue: FORAGED.**
  - `films/sources/le-maki-mococo/r1/brehm265.jpg`, from *Brehm's Life of Animals* p. 265, "The Binturong", engraving signed Specht. Commons `File:Brehm's Life of animals (Page 265) (6220164475).jpg`.
  - Licence: Public domain, to be re-verified from extmetadata.
  - `bertuch.jpg` and `farquhar.jpg` are not used.
- **Paper mouth: HANDMADE.** A cut-paper puppet of 9–11 pieces with fibre/mottle texture, scissor-wobble edges, a lit paper edge and a soft cast shadow. Geometry is original and not traced from the reference.
- **Gong and cord: HANDMADE.** A bronze card disc with hammered rings, cut into 12 wedges, on a twisted cord with a knot.
- **Type and red pencil: HANDMADE.** Caladea and Inter (system OFL fonts), plus a red-pencil stroke with pressure and grain.
- **Effects: HANDMADE/declared.** Room tone, paper ticks and a cord creak, made with kit synthesis.
- **Archive cache: checked, not used.** The Moving Image Archive cache has no clean profile mouth on white; Direction 1's lecturer is ruled out on consent grounds. A "gong|bell|chime" search returned only a 1947 belfry. Not using it is a deliberate choice: this is a handmade animation with two foraged items.

## 7 · AESTHETIC TARGET (from `assets/references/maki.webp`, catalogue `variations.json` id 25)

The reference is a single 640x360 video still: an extreme close-up of a mouth in profile facing right, with lips parted and the upper teeth showing.

- **Medium:** photographic video of real skin. We answer it with handmade cut paper lit like relief. We do not fake the photograph: no photo filter, no airbrushed gradients pretending to be skin.
- **Tonal range: high-key.** Luma percentiles are measured as P5=97, P25=165, P50=255. Only 2.4% of pixels are darker than 80, and that is the mouth cavity alone. More than half the frame is pure 255.
- **Palette (sampled with PIL; 8-colour median-cut plus region means):**
  - **Field:** #FFFFFF (σ=0), about 54% of the frame.
  - **Skin light:** #D3A394, #CA9A8A; cheek mean (199,153,136).
  - **Skin shade:** #AC8071, the jaw-edge shadow around (167,134,124).
  - **Skin highlight:** #E8C4B9.
  - **Lips:** #7D4E47 in shadow; lower-lip mean (157,86,93) ≈ #9D565D.
  - **Mouth cavity:** (66,26,23) ≈ #421A17.
  - **Teeth:** off-white, warm grey in shadow.
- **Light:** soft, frontal-left and diffuse. There are no hard cast shadows on the field; the face simply ends against white. The modelling is gentle: a glossy highlight on the lower lip and soft shading under the jaw.
- **Texture:** smooth skin with faint compression softness. Our equivalent is a fine paper fibre on the *skin pieces only*, with lit cut edges. The white field stays white (only very faint card tooth is allowed, mean ≥ 250).
- **Framing/scale:** the face fills the left ~44% (skin stops at x≈282/640). The frame cuts it at the nose base (top) and the neck (bottom). The lips are *large*: they span roughly x 14–44% and y 5–50% of the frame. The mouth is the whole subject. Nothing else is in the reference: no props and no type.
- **Typography:** the reference has none. Our type therefore lives only in the white field and stays quiet: dark warm ink, Caladea for the poem, Inter for labels. It never overlaps the skin.
- **Pacing:** the reference is one held close-up, and the film should feel like one held close-up. The mouth is animated at 12 fps on twos (paper), the field is static, cues are few and holds are long.

**Where kf-2 must be beaten.**
- kf-2's skin (#EEB9A0) is too pale and peach, and its field is off-white with grain.
- Its lips are thin, flat lozenges about 25% of frame height. The reference lips are fuller, glossier and occupy ~45%.
- **Required of U2:**
  - skin median ΔE76 < 12 from #CA9A8A;
  - lip median ΔE76 < 15 from #9D565D;
  - lips (upper + lower, open pose) spanning ≥ 35% of frame height and ≥ 22% of frame width;
  - a lower-lip gloss highlight;
  - the mouth cavity as the only dark mass;
  - skin confined to x < 45% of the width, cut by the top and bottom frame edges.

**Bronze and engraving (off-palette).** Keep them in the right field and small (the gong is ≤ 180 px wide; the binturong ≤ 300 px tall). The mouth remains the dominant subject in every shot.

## 8 · Animation technique SCIONs

1. **#47 Sound-to-Action: Viseme and Gesture Swarm.** The film's first cue *is* a voice, and the mouth must visibly say it.
   - **Method:** phoneme timing is measured from the real recordings (word onsets from the collage, and syllable onsets from energy minima inside each word, checked by ear and against the waveform). This gives a viseme track at 24 fps, quantized to 12 fps on twos.
   - Expressive holds (S5) carry silence as thought, and gestures (hm, the slow surprise, "O") carry the readers.
   - **Bar:** closures on b/m/p, no flapping in silence, the reaction spaced after the cue.
   - **Applies to:** S1, S3, S8 (speech); S2, S4, S6, S7 (silent gestures).
2. **#38 Dynamic Pose Selection: Drawing Library Swarm.** The mouth is a *library of ≤ 10 cut drawings per lip set*: rest, M/B/P, A, O, E/I, U/W, F/V, L/N/T, hm, surprise.
   - **Method:** a decoder chooses the replacement per frame from the viseme target. It applies a transition cost that penalises A↔closed jumps on a single frame, and a minimum hold of 2 frames.
   - The key surprise and "O" poses are protected from smoothing.
   - **Bar:** no flicker, and source drawings stay stable (the same piece bytes on every use).
   - **Applies to:** every mouth frame.
   - **Rig:** the jaw/lower-lip/chin group rotates about an off-screen hinge as forward kinematics (Reiniger-style pinned joints, 0–10°). The lips are substitutions; the jaw is articulation.
3. **#43 Collage Graph Rewriting: Identity Change Swarm.** The proof's turn *is* an identity rewrite: the thing on the cord goes from a gong (hypothesis layer) to a binturong (cue layer).
   - **Typed rule:** `replace(HangingThing.gong → HangingThing.binturong)`.
     - Preconditions: `t ≥ release(Q_image)`, anchor = the same knot, the "hangs" glyph is unchanged.
     - Graphic bridge: the cord, the knot and the swing phase.
   - **Method:** split the gong into 12 wedges, each of which exits by a ballistic fall with spin (secondary dynamics). The binturong enters by occlusion reveal on a plane behind (plane order: wedges in front, then animal and cord, then field; the type sits on its own plane).
   - **Bar:** the viewer follows the transformation as cause and effect, and no state is impossible. The animal's tail meets the knot, so it visibly hangs from it.
   - **Applies to:** S2 (enter gong), S4 (swing), S6 (split/exit/enter), S7–S8 (settled).

Rejected or used inline without a unit: Reiniger #2 (its pinned-joint method is folded into the #38 rig), #29 GrabCut (used as a tool by U3 for the engraving cutout, not as a technique SCION), and #44/#45 (only a three-plane stack is needed).

**Genuine frame-by-frame animation.** It is present in three places:
- the mouth (replacement and jaw articulation on every 2nd frame, driven by real audio);
- the gong's fracture (per-frame physics);
- the red-pencil stroke drawing itself.

## 9 · Swarm units (3; the editor/assembler and the independent reviewer run separately)

All units read this plan, `prompts/le-maki-mococo.md`, `films/BRIEF-2.md`, `films/kit.py` (do not edit it), the SCION prompts listed in §8, and `proposals/` (kf-2.png, kf-3.png, kf.py may be reused or rewritten).

Network rules:
- Use User-Agent `oulipo-film-research/1.0`.
- The Commons API rate-limits hard (429 / "too many requests" was seen during planning). Sleep ≥ 3 s between API calls and back off exponentially on 429.
- Downloads are untrusted: decode only with ffmpeg or PIL.

Budget: ~45 minutes per unit, under 75 MB of new downloads in total.

### U1 · Reading, cue and staging (reading designer + cue designer + staging unit, merged because they share segment IDs)
- **Forage the voice.** Collect Lingua Libre / Wiktionary recordings of the 13 words, reading each licence from `extmetadata` (accept only PD, CC0, CC BY, CC BY-SA).
  - Save the originals to `films/sources/le-maki-mococo/reading/`.
  - Decode with ffmpeg to 44.1 kHz mono.
  - Trim silence, then loudness-match.
  - Assemble `voice_poem.wav`: word gaps of 0.06–0.14 s, a 0.35 s pause at line ends, and the "binturong, binturong" refrains as *two different takes* where available.
  - Also save `voice_L1.wav` and `voice_binturong.wav`.
- **Measure, don't invent, the timing.** Record word onsets and offsets from the assembly. Find syllable onsets inside each word from energy-envelope minima, then check them by listening and by an exported waveform PNG.
  - Map each syllable to a phoneme class to get a viseme target and an RMS-derived jaw value.
- **Write `films/swarm/le-maki-mococo/cue_timeline.json`**, containing:
  - `poem` (revision, lines, words, syllables with seg_ids);
  - `audio` (files, per-word source and licence, syllable onset/offset in film time for S1, S3 and S8);
  - `visemes` (per syllable);
  - `cues` (Q_sound 2.0, Q_text 15.5, Q_image 38.0);
  - `responses` (the four ReaderResponse records, verbatim, with cites, hypothesis and next_observation);
  - `fiction_consent_ledger` (Readers A/B fictional; LL speakers and their licence scope);
  - `declared_silences_and_synth`;
  - `branches.image_first` (the baseline responses, marked staged);
  - a `fixture_check` result computed by a small script that asserts P1 for every response.
- **Credits:** also write a credits draft at `films/swarm/le-maki-mococo/credits_reading.json` (kit credits schema).

### U2 · Paper mouth puppet and kinetic type (mouth-shape designer + pose library + type)
- **Build the handmade mouth** as RGBA paper pieces at 2x film resolution: skin upper face with the nose base, nostril, upper lip, lower lip with gloss highlight, teeth strip, cavity, tongue hint, and a jaw/chin group. Give them fibre texture, scissor-wobble edges, lit edges and cast shadows.
  - Make two lip-paper colourways: A warm rose, B cooler mauve.
  - Make the replacement library of ≤ 10 poses per set (see §8.2), with the jaw on an FK hinge.
  - Meet the §7 numeric targets: palette ΔE, lip span, skin confined left, white field.
  - Save the pieces and a pose sheet PNG in `films/sources/le-maki-mococo/mouth/`.
- **Write `films/swarm/le-maki-mococo/mouth_rig.py`** (importable, pure PIL/numpy, deterministic, reading pieces from the sources dir):
  - `mouth_layer(t, viseme_track, lip_set) -> RGBA 960x540`;
  - `decode(viseme_targets) -> per-frame pose ids` (the #38 decoder with hold and transition costs);
  - `type_layer(t, syllable_onsets, glyph_table) -> RGBA` (kinetic typesetting: Caladea 30 px, letters land on syllable onsets, rose cursor, and a fixed glyph-box table exported for the invariant test);
  - `underline_layer(t)` (the red-pencil stroke for "hangs").
- **Write `films/swarm/le-maki-mococo/mouth_rig.json`** with the pose library, the decoder path for S1, the measured palette and spans versus targets, and a side-by-side PNG (frame vs reference, saved in sources/mouth/).
- **Render `films/sources/le-maki-mococo/mouth/mouth_test.mp4`:** S3's L1 with voice and typing. Use U1's `cue_timeline.json` when present; if it is not, use provisional onsets marked `provisional`.

### U3 · Image cue: gong to binturong (forager + matte compositor + transformation dramaturg)
- **Re-verify the Brehm licence** from Commons extmetadata, and record it.
- **Cut the binturong** out of `r1/brehm265.jpg` with cv2.grabCut, seeded by hand-placed scissor points along the body and tail. Clean the busy grass/fur edge by hand at film scale and keep a 4–6 px white paper margin with a soft cast shadow.
  - Rotate it so the tail tip meets the knot and it hangs head-down. Do not mirror it or warp it beyond rotation and scale.
  - Save the RGBA and its matte in `films/sources/le-maki-mococo/imagecue/`.
- **Make the handmade gong:** a bronze card disc (hammered rings, card edge and boss) split into 12 wedge RGBA pieces, plus a twisted cord and knot.
- **Write `films/swarm/le-maki-mococo/gong_rig.py`:**
  - `hang_layer(t, cues) -> RGBA 960x540` over the whole film, covering assembly (S2), damped pendulum (S4–S5), fracture at 38.0 (wedge release one per 3 frames, ballistic with spin), occlusion reveal and the binturong's sway and settle (S6–S8);
  - `events()`, listing the tick and creak times for the mix.
- **Write `films/swarm/le-maki-mococo/image_cue.json`** with the rewrite rule and its preconditions, the graph trace (gong enter → swing → split → exit, binturong enter), wedge trajectories, the anchor coordinates asserted constant, the licence record, and the `credits_imagecue.json` entries.
- **Optional:** a CC0/PD paper-tear recording from Commons for the wedge falls; if none is found, kit `click` (declared). **Never a ring.**
- **Save a contact strip PNG** of the frames 37.9–40.0 s in sources/imagecue/.

### Editor/assembler (run by the workflow; noted here for the contract)
- **First, the TEST SHOT:** 0:15.5–0:18 (the mouth says L1 while its words type) cut directly to 0:38.0–0:40 (the first gong-to-binturong frames).
- **Then the full film:** `films/le-maki-mococo.py` imports `mouth_rig.py` and `gong_rig.py` and reads `cue_timeline.json`.
  - It asserts invariants 1–3 and 7.
  - It writes `films/credits/le-maki-mococo.json` and `films/notes/le-maki-mococo.txt`.
  - It renders and saves side-by-side comparison frames.

## 10 · Acceptance bar (falsifiable; a fresh critic checks it by watching the film at normal speed, then reading the ledger)

1. **Cue order is visible and true** *(structural + perceptual).*
   - Watching, the critic hears the poem spoken by a real human voice before any poem word is on screen.
   - The words then type themselves, and only then does the engraving appear.
   - The cue strip turns ● at 0:02 / 0:15.5 / 0:38 (±1 frame), matching `cue_timeline.json`.
   - **Fails if** any poem glyph or any part of the engraving is visible before its cue time.
2. **No anachronistic reading** *(measured).*
   - Every caption's "cites" is a subset of the cues shown ● in that frame.
   - Guess 1 mentions nothing visual from the engraving, and guess 2 mentions nothing about a tail or animal.
   - The reconsideration names the image clue ("by its tail").
   - **Fails if** any caption cites or uses a cue later than its timestamp.
3. **Defining beat** *(measured + perceptual).*
   - In frames at 0:24 and 0:46, the bounding box of "hangs" is identical (pixel diff of the glyph box = 0 apart from ink tone).
   - The cord knot is at the same coordinate.
   - At 0:24 a gong hangs from the knot; at 0:46 the binturong hangs from the same knot by its tail.
   - A viewer can point at "hangs" as the word whose meaning changed.
   - **Fails if** the poem reflows, a word changes, or the animal is not attached to the knot.
4. **Mouth speaks the voice** *(perceptual + structural).*
   - In S1/S3/S8 the lips close on the b of each "binturong" and on the p's of "popcorn", and open widest on "-rong".
   - The mouth does not move during the declared silence S5 apart from at most one breath.
   - The pose decoder path in `mouth_rig.json` shows no single-frame pose flicker.
5. **Alternate preserved** *(structural).* After the reconsideration, Reader B's caption keeps a different plausible reading on screen for ≥ 2.5 s. The ledger stores all four responses verbatim, with speaker labelled fictional, `t_said`, cites, hypothesis and next_observation.
6. **Aesthetic, side-by-side colour/tone** *(measured).*
   - Place frames 0:06 and 0:46 beside `maki.webp` at equal height.
   - The white field (the right 50%, excluding type, cord and animal) has a mean of ≥ 250 in every channel.
   - Skin median is within ΔE76 < 12 of #CA9A8A, and lip median within ΔE76 < 15 of #9D565D.
   - The darkest mass in the mouth region is the cavity (luma < 80, ≤ 4% of the frame).
7. **Aesthetic, side-by-side framing and material** *(perceptual + measured).*
   - In the same comparison, the flesh mass (skin + lips + cavity) occupies 35–50% of the frame *(editor amendment E4: was "skin"; see below)*, the skin is confined to the left 45%, and it is cut by the top and bottom edges.
   - The lips span ≥ 35% of frame height in an open pose; the mouth reads as the whole subject, with fuller lips, a lower-lip gloss and rose-flesh tones.
   - On close inspection it is visibly cut paper: fibre, scissor-wobble edges, lit edges, small cast shadows. It must not be a smooth vector shape or a photo filter.
   - The reference is not traced: a critic overlaying the two outlines finds no contour match.
8. **Honest material and sound** *(structural).*
   - `films/credits/le-maki-mococo.json` lists every foraged item (Brehm/Specht PD; each Lingua Libre word file with speaker and CC BY-SA 4.0) with source and file URLs.
   - The ledger declares every synthesized effect and every silence.
   - No ring is heard when the gong breaks, and no synthetic speech is heard anywhere.
   - Film length is 60–70 s and file size ≤ 6 MB.

**Editor amendments (E4, repair round 2; the director's original wording is kept in the notes here).**
- *Bar 7, framing.* The original bar read "skin occupies 35–50% of the frame". Measured on `maki.webp`, the whole flesh mass (every non-white pixel) is 38.6% and skin alone is at most ~31%, so the band describes the flesh mass, not skin alone. Skin alone in the film is 27–29% (reported in `editor_measure.json` as `skin_area_frac`, a declared deviation): with skin confined to x < 45% and lips ≥ 35% of frame height, skin alone cannot reach 35%.
- *§6 S2 / S4, guess times.* The plan's 0:10 (R1) and 0:24 (R2) assumed a 7 s reading; the measured voice runs to 12.19 / 25.69. The acceptance times are therefore the staged ones: **R1 at 0:12.625, R2 at 0:26.125** (each 0.4 s after the voice it answers ends, on a frame). `cue_timeline.json` keeps `plan_t_said` 10.0 / 24.0 and the reason; P1 is unaffected (no cite changes).

Evidence labels for the reviewer: measured (1-timing, 2, 3-diff, 6, 8-size); structurally verified (5, 8-credits); perceptually judged (3-point, 4, 7). The reviewer must also say whether the cut preserves the order in which clues became available (§7).

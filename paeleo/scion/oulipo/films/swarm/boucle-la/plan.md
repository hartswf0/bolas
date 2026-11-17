# boucle-là: director's plan (SCION swarm, Direction II "Daumier à la colle")

Work: `prompts/boucle-la.md`. Chosen direction: II, keyframe `proposals/kf-2.png` (the look to meet or beat).
The acceptance bar, reader questions, intended reading and deliverables are frozen in `plan.json`.
If a maker thinks a condition is wrong, they write the change and the reason to `amendments.md` and keep working to the bar as written.

**Story.** The common seed (station, envelope, brass key) is **not used**. Direction II already tells its own story: Daumier's couple quarrelling in their bedroom over a note.
The fixed facts are these:
- Odette holds a folded note throughout.
- Its face reads « À MA CHÈRE ODETTE ».
- Nobody's facts change between the halves. Only the reader's knowledge changes.

---

## 1 · Creative thesis, and what would make it bland

**Thesis.** The same three drawings, with the same three balloons, are read twice. The first time Odette is the prosecutor and Gustave the suspect. Then one line turns the note's face toward the reader. It is addressed to her, the accuser. Now the identical drawings play the other way: Gustave holds the leverage and Odette is the one explaining herself.

The film's job is to make the viewer *feel* the identical "MOI ?! TU CROIS QUE J'AI QUE ÇA À FAIRE ?" change from a defence into a jab, before they notice the symmetry.

**What would make it bland:**
1. A hinge that only reveals a fact without turning the speech acts. Example: "C'EST LE FACTEUR".
2. Paired panels that differ slightly, because they were re-rendered, re-posed or re-lettered. The claim then becomes "similar", and similar is not identical.
3. Pale, grey, brownish crayon figures floating on white. This was kf-2's weakness: panels A, B and C hold only about 3 % black against Lécroart's 25–30 %.
4. Pans and fades over still cut-outs, with nothing animated.
5. A film that explains the reversal in captions instead of letting adjacency do it.
6. Symmetry flagged before meaning. Route labels and the "A B C H C B A" overlay may appear only after the return has played.

## 2 · Defining beat and baseline

**Defining beat.** It runs from H (24.5–37.0 s) into B′ (45.5–52.0 s).
- At 27.0–28.0 s the note turns face-out between the two heads over 6 drawings.
- On the frame it lands face-out (28.0 s), the panel ground cuts to spot black and the single bell strikes.
- Gustave's balloon « À MA CHÈRE ODETTE... » TIENS. C'EST POUR TOI. appears.
- Then the identical B returns: the same art, the same balloon and the same voice clip.

**What the viewer points to:**
- **(a)** the note's lettered face in the black hinge panel, which shows the note was meant for the accuser;
- **(b)** the second B balloon, now heard as sarcasm ("you think I'd waste my time writing *you* notes?");
- **(c)** the second A, now a feeble counter-accusation.

**Comparison baselines:**
- **Formal baseline:** the same page read as A B C H only, with no return. Every line keeps its first function, so nothing repeated changes meaning. The return must add a reading that this baseline lacks.
- **Aesthetic baseline:** `proposals/kf-2.png` beside the reference `assets/references/extract-001.webp`, at the same display size.

## 3 · Lineage Genome and Olog

### Lineage Genome (compact)

| Field | Value |
|---|---|
| Source | Étienne Lécroart, *Boucle-là !*. A printed comics page in a palindromic panel order around a central line, black-and-white pen and ink. Published in the Oubapo context. *Date and first venue uncertain:* we believe it appeared in L'Association's *Oupus* volumes (1997 or later); not verified here. |
| Target | (a) one print page, a PNG of at least 2400 px; (b) a 66 s film (960×540, 24 fps) that performs the page's reading route over the identical art. |
| Preserved relation | Story panels mirror around one unpaired hinge, with identical art and words. Pragmatic meaning changes by adjacency alone. Title and furniture sit outside the mirror. |
| Optics changes | Pen caricature becomes collage cut-outs of a real 1839 Daumier crayon lithograph, pushed to black and white by levels. The page is read by a camera, panel by panel. |
| Formalism changes | About 40 occurrences become 7 (A B C H C B A). The hinge is made visible as a full-width spot-black panel. The film enforces reading order, and the final hold restores the page's simultaneity. |
| Concept changes | The quarrel's object is a note whose addressee is the turn. |
| Sound changes | A page has no sound. Here there is one foraged voice clip per letter, sample-identical across each pair, plus one bell as the hinge cue, following the prompt's section 8. |

**Epoch weights (0–100):**

| Epoch | Weight | Reason |
|---|---|---|
| Oubapo, 1990s | 95 | Constraint comics and Lécroart's palindrome are the direct parent. |
| French caricature lithography, 1830s (Daumier, *Le Charivari*) | 70 | The actual material, and the big-nosed conjugal-quarrel type Lécroart inherits. *The causal lineage is an interpretive claim.* |
| Oulipian palindrome, 1960s–70s (e.g. Perec's palindrome, 1969) | 55 | The constraint family, at the level of letters rather than panels. |
| Gilliam cut-out animation, 1969–74 | 60 | The animation method: pinned found engravings and the paper jerk. |
| Reiniger pinned-joint puppets, 1920s | 20 | Joints only. |
| Töpffer page grammar, 1830s | 20 | A contemporary of Daumier; the page as a reading sequence. |
| Motion comics and camera-over-page reading, 2000s | 30 | The film's route grammar. |

### Olog (types and arrows)

**Types:**
- `Occurrence` (o1…o7)
- `PanelArt` (an immutable id A, B, C or H, carrying an RGBA panel raster plus its exposure sheet; identity is the sha256 of the held drawing and of every frame)
- `Speaker` (Odette, Gustave)
- `BalloonText` (an exact UTF-8 string plus a lettering seed)
- `SpeechAct` (accuse, deny, press, reveal, deflect, jab, counter-accuse)
- `KnowledgeState` (whether the addressee is known: unknown or known)
- `Leverage` (Odette, Gustave)

**Arrows:**
- `art_of: Occurrence → PanelArt`
- `speaker_of: PanelArt → Speaker`
- `text_of: PanelArt → BalloonText`
- `context_of: Occurrence → (prev Occurrence, next Occurrence, KnowledgeState)`
- `act_of: (PanelArt, context) → SpeechAct`
- `leverage_after: Occurrence → Leverage`

The ◻(ExchangePanel), ◻(SpeechAct) and ◻(Hinge) boxes are the first three arrows, `act_of`, and the uniqueness of `art_of(o4)`.

### Central operation `Mirror(seq, h)`

**Typed preconditions:**
1. `seq: List[PanelID]`, and `len(seq) == 7`.
2. `seq[3] == h`, and `h` occurs exactly once.
3. `seq[i] == seq[6-i]` for i in 0..2, and the three paired ids are distinct.
4. For each pair, `art_of` resolves to one cached raster. The held drawing is byte-identical, and the frame sequence is identical frame for frame.
5. `speaker_of` and `text_of` (string and lettering seed) are identical for each pair.
6. Title, loop arrow, route, panel-ID letters and signature are not members of `seq`.
7. Note state is part of the art: in A, B and C the note is back-out with the address hidden; in H it is face-out.

**Observable consequences:**
- A reader can lay the two B panels side by side and find no difference of line, tone, word or letterform.
- `act_of(B, before H) = deny` but `act_of(B, after H) = jab`. Likewise A goes from accuse to counter-accuse, and C from press to deflect.
- `leverage_after` moves from Odette (o1–o3) to Gustave (o4–o7).
- A blind reader locates the turn at H without being told.

**Counterexamples:**
- **Structural fail, speaker swap.** `[A,B,C,H,C,B*,A]`, where B* is B's art with the balloon tail moved to Odette. Precondition 5 breaks and the fixture must fail.
- **Structural fail, reversed letters.** A balloon whose letters are reversed (« ? ERIAF À AÇ ... »). This confuses a panel palindrome with a letter palindrome, and the fixture must fail.
- **Legal but inert.** The hinge « IL FAIT FROID ICI. » passes every structural test, yet `act_of` is unchanged for every pair and leverage stays with Odette. Structure is necessary, not sufficient, and this is why the reader test is blocking.
- **Legal separate candidate.** A second hinge (e.g. H3 below) with the same pair sequence. It is a different named branch, not a violation.

**Where replay and alternate views agree, and where they diverge:**
- **Agree:** the paired frames are identical across film occurrences and across page and film. Each panel's animation lands on exactly the page drawing.
- **Diverge:**
  - Meaning, speech act and leverage diverge.
  - Story order and page direction diverge: row 3 is read left to right, as page grammar requires, while the story runs backward through C B A.
  - The page lets both B panels be seen at once. The film forbids this until the final hold.

**Interactive?** No. The film is linear and the page is a printed object.

## 4 · Invariants (section 4)

- **I1.** The complete story sequence mirrors around H, preserving art and words exactly. The test is byte identity of cached rasters and frame hashes.
- **I2.** Title, loop arrow, route list, panel IDs and signature live outside the mirrored sequence, in the left margin column and the gutters.
- **I3.** Pragmatic change happens by adjacency alone. It is recorded in `speech-acts.json` for each occurrence.
- **I4.** Ownership rules:
  - The panel artist (U1) owns the immutable drawings.
  - The writer (U2) may pitch competing hinge lines.
  - A changed panel label or balloon invalidates **both** occurrences of that pair, so the pair is re-rendered from one source.
- **I5.** Hinge candidates are grouped by the speech-act change they produce, before layout (`hinge-alternatives.md`).
- **I6.** Every artifact records owner, base revision (the sha256 of its inputs), the read and write sets, and its acceptance condition, in that unit's JSON. A broken invariant quarantines the candidate, the work resumes from the last accepted state, and the evidence is logged.
- **I7.** Page and film share the art. The film never re-draws a panel: it animates rig poses whose final drawing *is* the page panel.

## 5 · Hard proof: the page

**Canvas.** 3200 × 1800 px, landscape 16:9, white ink-page ground #FBFBFB. The film camera (960×540) moves over this exact raster.

| Zone | Rect (x0, y0, x1, y1) | Content | Source |
|---|---|---|---|
| Margin column | 0, 0, 540, 1800 | "LE MOT" hand-lettered large (cap height about 120); "OU QUI L'A / LAISSÉ ?" (cap height about 50); a drawn loop arrow (a pen ellipse with arrowhead); the route lettered "A B C H C B A"; "ÉTUDE · OUBAPO"; small credit "d'après DAUMIER 1839" | HANDMADE pen strokes (U2) |
| Row 1 | 560, 40, 3170, 620 | Panels **A** \| **B** \| **C**, each about 850 × 580, with 30 px gutters | U1 art + U2 balloons, composed by U3 |
| Row 2 | 560, 650, 3170, 1150 | **H**, full width, spot-black ground | U1 + U2, composed by U3 |
| Row 3 | 560, 1180, 3170, 1760 | **C** \| **B** \| **A**, the identical rasters of row 1 | the same cache |
| Gutters | — | Small panel-ID letters (A, B, C, H) at the bottom-right corner, outside the panel art | furniture |

**Borders.** Hand-inked wobbly rectangles about 6 px thick. Balloons may overlap a top border, as Lécroart's do.

### The panels

The man is on the left and the woman on the right, as Daumier arranged them. Framing is closer than kf-2: waist-up, or knees-up at the widest. The heads sit in the middle third and the figures fill at least 60 % of the panel height. Balloons take the top 35–40 %, with tails to the speaker's mouth.

| ID | Speaker | Balloon (exact) | Posture (canonical held drawing) | Note |
|---|---|---|---|---|
| **A** | Odette | ET ÇA ?! C'EST TOI QUI L'AS LAISSÉ, CE MOT ? | Her forearm raised, the note held up at his face. Her head tilted forward and down at him. Gustave's head drawn back. | back-out, in her hand |
| **B** | Gustave | MOI ?! TU CROIS QUE J'AI QUE ÇA À FAIRE ? | His forearm flipped up, palm out in a "Moi ?!" shrug. His head jerked back, nose up. Her note lowered. | back-out, low |
| **C** | Odette | ALORS DE QUI IL EST ?! | Her whole-body lean forward. The note pushed toward him. His forearm down. | back-out, pushed out |
| **H** | Gustave | « À MA CHÈRE ODETTE... » TIENS. C'EST POUR TOI. | Both heads swung in over the note. He leans in, pointing at it. She recoils slightly, head back. The panel ground is spot black. | **face-out**, lettered « À MA CHÈRE / ODETTE », between them at chest height |

**Routes, written to `route.json`.**
- **Reading route (story order):** A(r1c1), B(r1c2), C(r1c3), H(r2), C(r3c1), B(r3c2), A(r3c3). This is the natural Z-order of the page.
- **Mirror check route:** pairs (r1c1, r3c3), (r1c2, r3c2), (r1c3, r3c1).
- **Hinge:** r2.

### Element sources

- **FORAGED.** Honoré Daumier, *Mœurs conjugales* no. 3, "Et les cinq francs de ce matin ?…", 1839.
  - Rijksmuseum RP-P-OB-41.183, via Wikimedia Commons, **CC0**. Already in `films/sources/boucle-la/daumier/` with `meta.json`.
  - U1 re-verifies the licence through the Commons extmetadata API and downloads the **original-resolution** file (about 2.4 MB) to `sources/boucle-la/panel-artist/`.
  - It supplies: the two figures; the head, forearm and body pieces; and optionally the print's own dark backdrop crayon mass as a spot-black collage piece.
  - Optional second plate: another CC0 *Mœurs conjugales* print from the Rijksmuseum on Commons, only if needed to source a clean replacement hand for Gustave (Gilliam substitution).
- **HANDMADE:**
  - all lettering (the stroke alphabet in `proposals/kf_common.py`, seeded per balloon);
  - balloons and tails, panel borders, floor line and wall rail;
  - the note, cut paper with its lettered face;
  - margin furniture and panel IDs.
- **FORAGED (sound).**
  - Voice clips: short real-speech grains from openly licensed recordings. The first choice is movingimagearchive.com clips with source sound; Commons audio is the alternative. A female voice is needed for A and C, a male voice for B and H.
  - Bell: one real hand-bell or service-bell recording from Commons (PD, CC0, CC BY or CC BY-SA).
  - Paper rustle for the note turn: Commons or the archive.
  - If no licensed speech is found, the declared fallback is `kit.Mix.murmur` seeded per letter. It is synthesized and is stated as such in the notes.

## 6 · Hard proof: the film (timed shot list; total 66.0 s, 960×540, 24 fps)

**How each occurrence animates:**
- An occurrence slot starts with a 0.5 s camera slide.
- Its panel then animates on 2s (12 drawings/s) from a neutral entry pose into its canonical pose: at least 8 distinct drawings, with Gilliam paper jerk and a 2–3 drawing settle.
- It then **holds exactly the page drawing**.
- The balloon appears whole, never typed on, on the drawing where the speaker's head accent lands.
- The voice clip starts on that same frame.
- Panels not yet read show at 22 % ghost over the page. Row 3 waits as a ghost until the return.

| # | Time (s) | On screen | Heard |
|---|---|---|---|
| 0 | 0.0–3.0 | The whole page, fitted. Furniture fully inked; every story panel a ghost. | Room tone (foraged, low), a paper sound |
| 1 | 3.0–5.0 | Camera eases into the margin, so "LE MOT / OU QUI L'A LAISSÉ ?" reads, then slides to A. | — |
| A | 5.0–11.5 | Panel A at about 1.1× panel width. Odette's forearm lifts the note (drawings 1–8); her head nods on the stress; Gustave's head draws back; settle; hold. Balloon A at about 6.2 s. | Voice clip A (female) at the balloon frame |
| B | 11.5–18.0 | Slide to B. Gustave's forearm flips up and his head jerks back on "MOI"; her note drops. Balloon B. | Voice clip B (male) |
| C | 18.0–24.5 | Slide to C. Odette's body lean forward about the feet; the note is pushed out. Balloon C. | Voice clip C (female) |
| H | 24.5–37.0 | Camera drops to row 2 and frames the wide hinge. At 26.0–26.5 both heads swing in (6 drawings). At 27.0–28.0 the note turns from back to face over 6 drawings: a card flip with foreshortened width, a substitution at edge-on, and paper rustle. **At 28.0, on the face-out drawing, the ground cuts to spot black and the bell strikes.** At 28.5 Gustave's balloon. A 28.5–31 settle: she recoils, head back. At 31–35 a slow camera push toward the note face. At 35–37 hold. | Rustle 27.0, **bell 28.0** (the only one), voice clip H (male) at 28.5, then the bell decay |
| 2 | 37.0–39.0 | Camera pulls back to show the page with rows 1 and 2 inked and row 3 still ghosted, then slides down-left to row 3's C. | Silence and room tone |
| C′ | 39.0–45.5 | Row 3, C. The **identical** exposure sheet and drawings as C. | The **identical** voice clip C, sample for sample |
| B′ | 45.5–52.0 | Row 3, B. Identical to B. *The defining comparison.* | Identical clip B |
| A′ | 52.0–58.5 | Row 3, A. Identical to A. | Identical clip A |
| 3 | 58.5–61.5 | Pull back to the whole page, every panel inked. Hold, clean. | Room tone |
| 4 | 61.5–66.0 | A film-only annotation layer, outside the panel interiors. The route A→B→C→H→C→B→A is traced as a thin pen line through the panels in order. A small speech-act tag sits under each panel in the gutters (accuse / deny / press / **reveal** / deflect / jab / counter-accuse). Then it fades back to the clean page. | Silence, then a short tail of room tone |

**Sound is purposeful:**
- one voice clip per occurrence, each pair sample-identical;
- one bell, at the hinge frame only;
- a rustle on the turn;
- no music.

## 7 · Technique SCIONs (read in full in `paeleo/scion/swarms.json`)

### SCION 29: GrabCut, cut-out extraction swarm (owner U1)

**Why.** The direction stands or falls on a clean cut: the couple, cut out of one print, with Gustave's forearm free of Odette's fingers where their hands meet, and no backdrop islands.

**Native primitives kept:**
- foreground and background unary costs;
- pairwise edge terms;
- box and scribble seeds;
- graph cut;
- alpha cleanup.

GrabCut is seeded per piece: a box plus FG/BG scribbles saved as PNG seed maps. Where it fails on lithograph crayon (kf-2 found that it does), U1 follows the SCION's section 6 and compares seeded GrabCut against tonal matting and against *manual contour markup* (hand-placed polygon snips, which are also the Gilliam scissor edge). The winner is chosen per piece and recorded.

**Numeric invariant:**
- each piece's alpha is exactly one connected component (no background islands);
- no alpha pixel of Gustave's pieces lies inside Odette's hand-marked region, and vice versa;
- failure masks are exported.

**Perceptual achievement.** At 100 % page view the cut edge reads as a deliberate scissor edge that keeps Daumier's crayon contour, with the fingers intact.

### SCION 32: forward kinematics, hierarchical body logic (owner U1 defines the rig, U3 animates)

**Why.** The palindrome needs the *same* drawing replayed. A rig of rigid pinned paper pieces, driven by an exposure sheet of joint angles, makes each pair one data object.

**Joint graph:**
- feet pivot (root, whole-figure lean) → body → neck pin → head;
- body → elbow pin → forearm (with hand);
- for Odette, hand anchor → note.

The primitives are local transform, parent transform, bone length (pivot-to-pivot), pivot offsets and view-specific anchors (the note anchor).

**Numeric invariant:**
- transforms multiply root→leaf in a fixed order;
- the neck-to-elbow and elbow-to-hand distances stay constant within 0.5 px across every frame;
- the joint coincidence error is ≤ 1 px, so there is no head/neck detachment;
- the note's anchor stays on Odette's hand to ≤ 1 px.

**Perceptual achievement.** Each canonical pose reads as its speech act: the accusing raise, the "Moi ?!" shrug and head jerk, the pressing lean, the hinge lean-in and recoil. Motion has weight: the lean leads from the feet and the head lags one drawing.

### SCION 1: Terry Gilliam, comic cut-out metamorphosis (owner U3 for timing and substitution; the editor for impact sound)

**Why.** Gilliam's theorem fits: start from what the image already implies (a quarrelling couple), then move the smallest necessary fragment (a forearm, a head, one slip of paper) to produce the gag. The note's turn is his substitution object.

**Native primitives kept:**
- engraved figures and source-image crops;
- pivot joints;
- matte layers;
- the substitution object (the note: its back drawing swapped for its face drawing at edge-on);
- the semantic transformation graph (note back → note face → leverage flip);
- held frames and impact sound (the bell on the cut-to-black frame).

**Numeric invariant:**
- motion is on 2s: every drawing is held exactly 2 frames at 24 fps, verified by frame difference;
- each occurrence ends in a held drawing of at least 3.0 s;
- the bell onset falls within ±1 frame of the face-out drawing.

**Perceptual achievement:**
- paper boundaries look intentional, with a white scissor margin and contact shadows;
- the transformation *causes* action: the note's face causes Odette's recoil and the leverage flip;
- every beat reads at phone size.

## 8 · Swarm units (makers only; editor, blind readers, critic and reviewer run separately)

### U1 · Panel artist and cut-out surgeon

- **Mode:** both.
- **Inputs:** the Daumier print and this plan.
- **Media:** `sources/boucle-la/panel-artist/`.
- **Output:** `films/swarm/boucle-la/cutouts.json`, a manifest with:
  - pieces and file paths;
  - seeds and method per piece;
  - pivots, bone lengths and the joint graph;
  - levels used;
  - canonical poses A, B, C and H plus entry poses;
  - licence re-verification;
  - sha256 per piece.
- **Contact sheet:** `films/swarm/boucle-la/cutouts.jpg`, showing pieces, failure masks and the four canonical poses composited on white.
- **Duties:**
  - Owns the immutable drawings. Gives each line a clear posture.
  - Re-verifies CC0 and downloads the original resolution.
  - Cuts clean pieces with no fragments of the other figure.
  - Pushes the crayon to ink by levels only: per-piece black and white points, no threshold or posterize over the frame. Starting points: black point at about luminance 95, white point at about 200, since the paper is #E4C9B1 and the backdrop is about (99,90,81).
  - Optionally cuts the print's dark bed and wall crayon as a spot-black set piece.
  - Writes and runs its own rig assertions (bone lengths, connectivity). These are maker self-checks, not validation.

### U2 · Dialogue writer, letterer and sound forager

- **Mode:** both.
- **Media:** `sources/boucle-la/dialogue-writer/`.
- **Outputs:**
  - `films/swarm/boucle-la/script.json`: ExchangePanel records with id, speaker, exact text, lettering seed, the balloon PNG path, the tail anchor and the voice clip path with its in/out points;
  - `films/swarm/boucle-la/speech-acts.json`: paired speech-act annotations and leverage per occurrence;
  - `films/swarm/boucle-la/hinge-alternatives.md`: at least 4 hinge lines grouped by the speech-act change they produce, with one lettered alternative hinge balloon rendered for each group;
  - lettered balloons, the note face, the title column and route lettering as RGBA PNGs at page resolution;
  - foraged voice clips and the bell (decoded with ffmpeg to wav, with licences recorded in `sound.json`).
- **Duties:**
  - Keeps or improves the proposal lines, but every line must be reversible: it must read as a different act after H.
  - Lettering is the handmade stroke alphabet in crisp black capitals. The pen is heavier than kf-2's so it holds at page fit.

### U3 · Page compositor and animator

- **Mode:** handmake.
- **Depends on:** U1 and U2.
- **Media:** `sources/boucle-la/page-animator/`.
- **Outputs:**
  - `assets/pages/boucle-la.png` (3200×1800);
  - `films/swarm/boucle-la/page.json`: panel rects, the cache key and sha256 per panel ID, exposure sheets per occurrence (joint angles per drawing, holds), and the frame-sequence directory per ID;
  - `films/swarm/boucle-la/route.json`: the panel ID path, pairs and hinge;
  - rendered panel frame sequences at page scale under `sources/boucle-la/page-animator/frames/<ID>/`, so that the paired occurrences *use the same directory*;
  - `assets/pages/boucle-la-annotated.png`: the page with the route line and speech-act tags in the gutters only.
- **Duties:**
  - Applies SCION 32 for posing and SCION 1 for timing on 2s, the jerk, the note substitution and the H cut to black.
  - The final frame of each sequence equals the page crop.

### U4 · Palindrome validator

- **Mode:** handmake (code).
- **Depends on:** U3. It must not edit art.
- **Media:** `sources/boucle-la/validator/`.
- **Output:** `films/swarm/boucle-la/fixture.py`, run with `python3 -I`, plus `films/swarm/boucle-la/fixture-report.json`.
- **Tests:**
  - **Positive:** `[A,B,C,H,C,B,A]` passes; page-crop identity for each pair; frame-hash identity of the paired sequences; balloon string and speaker identity.
  - **Negative, which must fail:** speakers swapped on the second B; the letters reversed within one balloon; a one-pixel edit to one paired panel.
  - **Alternative:** a different hinge with the same pairs passes as a separately named candidate.
  - Joint invariants from `cutouts.json` and `page.json`.
- When the editor's mp4 exists, it also checks that the held frames match the page and that the bell is a single onset within ±1 frame.

### Editor (run by the workflow)

- Writes `films/boucle-la.py` using `kit.Film`, and renders `assets/films/boucle-la.mp4`.
- Pastes U3's frame sequences and page raster with camera moves along the shot list. Panels are never re-drawn.
- Mixes U2's foraged clips, sample-identical per pair, plus the single bell.
- Writes `films/credits/boucle-la.json` and `films/notes/boucle-la.txt`.
- Writes `films/swarm/boucle-la/status.md`: preview, revision hashes, decisive review and remaining failure.

## 9 · AESTHETIC TARGET

Targets: the reference `extract-001.webp` (Lécroart) and the chosen keyframe `kf-2.png`. Values are sampled with PIL.

**Medium.** A printed black-and-white comics page: pen, brush and spot blacks on white. Here the figures are a real crayon lithograph cut out and collaged, and all furniture and lettering is pen.

**Tonal range.** The reference is about 24 % black (<60) overall and 31 % in a typical row. It is about 18–20 % mid-grey, almost all antialias and print. About 57 % is white (>200). Blacks are solid at #0D0D0D (13,13,13). Whites are #FBFBFB (251,251,251).

kf-2 reaches 23 % black overall, but only because of the black H panel. Its panel A holds 3 % black and 14 % mid-grey, which is too pale.

The target:
- the crayon's darkest strokes and Daumier's dark backdrop masses (about (99,90,81) in the print) go to solid ink;
- the paper (#E4C9B1, (228,201,177)) goes to white;
- the mid-tones become crisp crayon texture, not a grey haze;
- chroma is about 0: no brown cast anywhere on the page.

**Palette.**

| Role | Value |
|---|---|
| Ink | #0D0D0D to #111111 |
| Page | #FBFBFB |
| Ghost | 22 % ink on page, film only |

Nothing else.

**Light.** Flat print light. There are no gradients or vignettes. Contact shadows under the paper pieces are at most a faint 2–4 px offset: paper on paper, read as collage.

**Texture.** The lithographic crayon grain inside the figures, kept by levels. Pen lines with slight hand wobble. The white scissor margin about 3–4 px at page scale around each cut-out. No added grain or filter.

**Framing and scale.**
- Lécroart frames two-shots waist-up, with heads in the middle third and balloons filling the top third.
- Frame tighter than kf-2: figures fill at least 60 % of panel height.
- In the reference, panels are small and dense. Our 7-panel page has larger panels, so the figures must be scaled up to match the *density*, with black borders about 6 px at 3200 px.

**Typography.**
- Hand-lettered capitals, single-stroke, slightly irregular, filling irregular oval balloons with thin pen outlines and pointed tails.
- Balloons may break a panel's top border.
- The title "LE MOT" is lettered large in the left margin, like the reference's "boucle-là !".

**Pacing.**
- Each panel acts briefly, about 1.5–2.5 s of drawings on 2s, then holds long enough to read: at least 3 s.
- The hinge is the only long beat, about 12 s.
- The return is read at the same pace as the first pass, so identity is felt.
- One bell, no music.

## 10 · The bar (frozen copy; plan.json is authoritative)

- **B1** (blocking, structurally verified): HARD PROOF PAGE: assets/pages/boucle-la.png (>=2400 px long side; planned 3200x1800) is one page of exactly seven story occurrences read in natural Z order as A B C (row 1), H (full-width row 2, spot-black ground), C B A (row 3); two people (Odette, Gustave, cut from the Daumier print) dispute who left a note; the hinge balloon and the note's lettered face « À MA CHÈRE ODETTE » show the note was meant for Odette, the accuser; title/loop arrow/route/IDs sit only in the margin and gutters; every balloon is legible at full-page fit on a 1920 px wide screen.
- **B2** (blocking, measured): FIXTURE (section 7): fixture.py passes [A,B,C,H,C,B,A]; for each pair the two page crops are pixel-identical (max abs diff 0) and the film's paired occurrences use identical frame sequences (per-frame sha256 equal) with identical speaker, balloon string and voice clip samples; H occurs once. The negative cases — speakers swapped on the second B, letters reversed within one balloon, a 1-px edit to one paired panel — each make the fixture FAIL; a different hinge with the same pair sequence passes as a separately named candidate.
- **B3** (blocking, perceptually judged): REVERSAL READS WITHOUT EXPLANATION: a fresh blind reader, after one natural reading of the page or one viewing of the film and before being told of any symmetry, names the hinge line as the one that shifted leverage, names at least one repeated line (B expected) whose meaning changed and states both meanings, and says Odette is on the attack before the hinge and on the defensive after it.
- **B4** (blocking, structurally verified): GENUINE MATERIAL, GENUINELY ANIMATED: the figures are cut from the real Daumier lithograph (Rijksmuseum RP-P-OB-41.183, CC0 re-verified from Commons extmetadata, credited); at 100% page view no piece carries fragments of the other figure (Gustave's forearm free of Odette's fingers) and no background islands; lettering, balloons, borders and the note are handmade. In the film every occurrence is animated frame by frame on pinned rigid pieces (>=8 distinct drawings per occurrence; the note turns through >=4 foreshortened drawings in H), joints never visibly detach, and each occurrence lands on and holds exactly its page drawing. Nothing is a pan/fade over a still alone.
- **B5** (blocking, perceptually judged): AESTHETIC SIDE BY SIDE: shown beside extract-001.webp and kf-2.png at the same size, the page reads as a crisp black-and-white ink comics page — white ground with no brown paper cast, solid blacks present in every story panel (crayon masses pushed to ink by levels, not a threshold/posterize over the frame), a spot-black hinge panel, hand-lettered capitals in oval balloons with tails, figures framed waist- to knee-up filling >=60% of panel height — and a viewer judges it at least as crisp and dark as kf-2 and closer to the reference than kf-2.
- **B6** (blocking, measured): THE FILM PERFORMS THE READING: assets/films/boucle-la.mp4, 55–75 s, plays at normal speed with sound; the camera walks A→B→C→H→C→B→A over the identical page raster; row 3 is visibly waiting as a ghost until the return; exactly one bell onset, within ±1 frame of the note's face-out drawing in H; the whole page is held clean before any route/speech-act annotation appears.
- **V1** (advisory, measured): Each of panels A, B, C on the page has >=10% pixels darker than luminance 60 (kf-2 panel A: ~3%; reference rows ~25–31%) and page chroma p99 <= 4.
- **V2** (advisory, perceptually judged): Gilliam paper quality: motion on 2s with held drawings, a visible intentional scissor margin and faint contact shadows; head accents land on the voice clip stresses; every beat reads at 480 px width.
- **V3** (advisory, measured): FK invariants: bone lengths constant within 0.5 px and joint coincidence error <=1 px over every rendered drawing; the note anchor stays on Odette's hand <=1 px.
- **V4** (advisory, structurally verified): mp4 <= 6 MB; films/credits/boucle-la.json lists every foraged item (print, voice clips, bell, rustle) with licence and source URL; notes say plainly what is foraged and what is handmade (synthesized murmur declared if used).

## 11 · Deliverables (section 9)

- `/home/user/bolas/paeleo/scion/oulipo/assets/pages/boucle-la.png`
- `/home/user/bolas/paeleo/scion/oulipo/assets/pages/boucle-la-annotated.png`
- `/home/user/bolas/paeleo/scion/oulipo/assets/films/boucle-la.mp4`
- `/home/user/bolas/paeleo/scion/oulipo/films/swarm/boucle-la/route.json`
- `/home/user/bolas/paeleo/scion/oulipo/films/swarm/boucle-la/speech-acts.json`
- `/home/user/bolas/paeleo/scion/oulipo/films/swarm/boucle-la/hinge-alternatives.md`
- `/home/user/bolas/paeleo/scion/oulipo/films/swarm/boucle-la/script.json`
- `/home/user/bolas/paeleo/scion/oulipo/films/swarm/boucle-la/cutouts.json`
- `/home/user/bolas/paeleo/scion/oulipo/films/swarm/boucle-la/page.json`
- `/home/user/bolas/paeleo/scion/oulipo/films/swarm/boucle-la/fixture.py`
- `/home/user/bolas/paeleo/scion/oulipo/films/swarm/boucle-la/fixture-report.json`
- `/home/user/bolas/paeleo/scion/oulipo/films/swarm/boucle-la/turning-point.md`
- `/home/user/bolas/paeleo/scion/oulipo/films/swarm/boucle-la/status.md`
- `/home/user/bolas/paeleo/scion/oulipo/films/boucle-la.py`
- `/home/user/bolas/paeleo/scion/oulipo/films/credits/boucle-la.json`
- `/home/user/bolas/paeleo/scion/oulipo/films/notes/boucle-la.txt`

Section 9: single readable page (boucle-la.png); panel ID path (route.json); paired speech-act annotations (speech-acts.json + annotated page); hinge alternatives (hinge-alternatives.md with lettered alternates); independently located turning point (turning-point.md, written from the blind readers' answers, not by a maker); readable status view (status.md).

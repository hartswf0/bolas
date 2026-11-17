# Plan: Moins d'un quart de seconde pour vivre · Iconic iteration

Director's plan. Base revision: proposals/ (keyframes kf-1..3, board.jpg), chosen **Direction 1, "Brush plate, written balloons"** (kf-1.png). Prompt: `prompts/moins-dun-quart-de-seconde-pour-vivre.md`. The bar is in `plan.json`, and it is frozen. Makers propose changes in `amendments.md` and keep working to the bar as written.

The work is a page plus a film. The page holds two four-panel strips over one brush-ink plate. The film performs the reading of that page.

---

## 1 · Creative thesis

One drawing that never changes becomes two different situations, and only the words change it. The creature sits on a park bench at night, holding an unopened envelope. Its eyelid is half down, its pupil is slid toward the envelope, and its mouth is a flat line.

- **Strip A, "to wait":** the creature talks itself into not opening the envelope. Its third panel is silent.
- **Strip B, "the alibi":** the same pose answers an unseen questioner and uses the picture itself as evidence: the bench, the lamp, the sealed flap.

The last balloon of B, "WHY WOULD I OPEN SOMEONE ELSE'S?", gives away that the envelope is not the creature's. The same sideways eye, unchanged by one pixel, now reads as guilt.

**What would make it bland:**
- balloons that describe the picture ("I'm sitting on a bench with a letter");
- a B4 line that only confirms innocence;
- a silent panel that reads as a missing balloon rather than a decision;
- an eye or mouth quietly redrawn to "help" the joke, so the art does the work and the words don't;
- lettering in a typed font or set all at once, so nothing is actually written;
- a film that is a slideshow of finished panels with fades;
- grey, soft, filtered "comic look" instead of hard black and white;
- the camera wandering, so the identical art is not felt as identical.

## 2 · Defining beat and comparison baseline

**Defining beat: the hinge of strip B, written on in sequence.** In the film this runs from 0:35.0 to 0:57.0, B1 through B4. The test-shot core is B1 to B3:
1. "ME? I'VE BEEN ON THIS BENCH SINCE NINE."
2. "ASK THE LAMP." The lamp globe stays visible and is pointed to by the words alone.
3. "AND LOOK - STILL SEALED." The drawn flap is unchanged.

Then B4 lands. The pen stops for 10 frames after "SOMEONE" before writing "ELSE'S?".

A viewer should be able to point to four things:
- (a) the lamp that B2 cites, uncovered by any balloon;
- (b) the sealed flap that B3 cites;
- (c) the words "SOMEONE ELSE'S", and the moment they make the same eye look guilty;
- (d) across the whole page, the identical eye in all eight panels, and the empty black above the head in A3.

**Comparison baseline:**
1. The reference strip (`assets/references/iteration-001.webp`, Menu and Trondheim): four identical frog plates, a wordless panel 3, and a short deflating last line.
2. The chosen keyframe kf-1.png: same plate ×8 and the same lines, but the ear crosses the tails, the lamp is hidden in most panels, and the framing is looser than the reference.

The result must at least match kf-1, and should beat it on framing and on keeping the lamp clear. It is set beside both at the same strip width.

## 3 · Lineage Genome (compact)

| Field | Value |
|---|---|
| Source medium | Printed black-and-white humour strip. Menu and Trondheim, *Moins d'un quart de seconde pour vivre*, 1991 edition (L'Association). Four panels, one repeated drawing, hand-lettered balloons, a wordless beat. |
| Target media | (1) A print-resolution comics page: two four-panel strips over one plate. (2) A 24 fps screen film that performs the page's reading order, with the balloons written on, a timed declared silence, and a same-size comparison. |
| Preserved relation | The image is held constant and the dramatic use varies. Words, withholding and repetition make a stationary drawing a changing situation. The last balloon re-reads the expression. One panel is silent. |
| Optics change | Fixed page → a camera at 1:1 panel scale (a 540 px panel fills the 540 px frame height). Reading time is imposed by pen speed and holds. The silence gets a duration, not only a space. |
| Formalism change | Repetition by reproduction → repetition **verified by hash**. Plate bytes, crop, scale and frame are asserted equal; balloons are on a separate RGBA plane; there are negative controls. |
| Concept change | One strip → two strips over the same plate (wait vs alibi), compared at the same size. The image is used as testimony ("ask the lamp"). |
| Sound change | Silent print → a foraged night ambience and a pen-on-paper scratch tied to each written stroke. Panel A3 is a declared silence: ambience only. |

**Formation epochs (weight 0–100):**

| Epoch | Weight | Reason |
|---|---|---|
| L'Association / OuBaPo constraint comics, 1990–93 | 90 | The direct source. Menu and Trondheim were among the founders of OuBaPo. *Uncertain:* OuBaPo's founding is usually dated 1992, after this 1991 edition, so the strip is "pre-OuBaPo constraint practice" rather than an OuBaPo product. |
| Oulipo constraint writing, 1960– | 60 | A rule fixed before writing; variation under constraint. Exercices de style is the sibling. |
| Franco-Belgian gag strip | 40 | The four-beat setup, turn, beat, payoff. |
| Limited animation / held drawings (UPA → South Park) | 45 | Reused assets as an expressive grammar (#17). |
| Kinetic typography and write-on titling | 40 | Lettering as the moving element. |
| Content hashing and version control | 70 | The invariant becomes testable. Anachronistic to the source, but central to this proof. |

*Uncertain claims, recorded as such:*
- whether the original iterations were made by photocopying a single drawing or by redrawing (unknown, not verified);
- edition details beyond "1991, L'Association" (not verified);
- the Louis-Honoré PDF, p. 23, was not re-read in this run (uninspected).

## 4 · Olog and the central operation

**Types (boxes):**
- **◻Plate:** `{plate_id, sha256, crop=(0,0,540,540), scale=1, frame="hand border", source="handmade brush strokes", stroke_ledger}`.
- **◻BalloonLayer:** `{layer_id, panel, strings[], rgba_png, sha256, stroke_schedule, tail_target}`.
- **◻Silence:** `{panel, duration_s, sound="ambience only"}`.
- **◻PanelOccurrence:** `{strip, slot 1..4, plate_id, balloon: BalloonLayer | Silence}`.
- **◻DialogueBeat:** `{speaker, addressee, intention, transition_in_listener_understanding}`.
- **◻Strip:** an ordered set of 4 PanelOccurrences.
- **◻Reading:** the reader's understanding after each beat, including the meaning assigned to "the eye".

**Arrows:**
- PanelOccurrence —shows→ Plate (many-to-one; for the strict proof, one Plate for all 8).
- PanelOccurrence —carries→ BalloonLayer ⊔ Silence.
- DialogueBeat —is realized by→ PanelOccurrence.
- Strip —induces→ Reading.
- Reading —assigns meaning to→ the Plate's eye.

**Central operation: `iterate(plate, [b1, b2, b3, b4]) → Strip`.**

Typed preconditions:
1. The Plate is frozen: sha256 is recorded in `plate.json` before any balloon is lettered. Balloon makers read the plate and never write it.
2. Every occurrence references the same `plate_id`, with crop (0,0,540,540), scale 1 and the same hand border.
3. Each b_i is either a BalloonLayer (an RGBA PNG on its own plane, composited over the art) or a Silence. A Silence is still a DialogueBeat, with speaker = creature and intention = withhold or decide.
4. Balloons may move in layout, but may not cover the eye, the envelope flap, or (in B2) the lamp globe.
5. The last DialogueBeat's transition is not "continue": it changes what the eye means.

Observable consequences:
- The art-only raster of all 8 page panels, and of all 8 film panel holds, is sha256-equal.
- Strings differ: A has 3 non-empty strings plus 1 silence; B has 4.
- Readers give different meanings for the same eye at A4 and at B4.
- Readers report A3 as a beat in which something happens (deciding, giving up the question), not as an error.

**Counterexamples (the operation must reject or fail these):**
- (i) *Graphic drift.* The B4 eye is lowered 2 px to look guilty. The reading may change, but the strict fixture fails, because the art did the work. The candidate is quarantined.
- (ii) *Description.* B4 = "I'M JUST WAITING HERE." The invariant passes but the thesis fails: the words describe the image and the reading does not change. Repair per section 8: keep the image and write one line that gives a different reason for the same posture.
- (iii) *One-pixel crop.* The plate is pasted at x+1 in one panel. The fixture fails. This is a negative control.

**Equivalence and divergence across views:**
- *Equivalent:* page and film are identical in art and in final lettering. At each film panel hold, the 540×540 panel region of the last frame of the hold equals the page panel region pixel for pixel. This is measured on frames before encoding, and is possible because the film panel scale is 1:1 with the page.
- *Equivalent:* the film's closing full-page comparison shows the same strips as the page.
- *Divergent:*
  - the film imposes order and tempo;
  - the silence of A3 has a 4.4 s duration in the film and only an area on the page;
  - B4 exists in the film as a partial string ("WHY WOULD I OPEN SOMEONE…") for 10 frames, a suspense the page cannot hold;
  - balloon outlines are drawn before their letters only in the film.

*Replay:* rendering is deterministic (seeded). Replay is byte-equivalent before encoding.

*Interactive:* none; this is a page and a linear film. TTL = 2 (default); the run proceeds.

## 5 · Invariants (section 4)

- **I1 (strict art identity).** The art layer is one raster `plate-540.png` (sha256 recorded). All 8 page occurrences and all 8 film panel holds use the same bytes, crop (0,0,540,540), scale 1 and frame. Assert in code.
- **I2 (separate plane).** Balloons are RGBA layers composited over the art. Removing them restores the art-only raster exactly.
- **I3 (no graphic drift at 100×).** Before any reading is scored, a pixel diff of the 8 art-only rasters must be all zeros. On failure, quarantine the candidate, resume from the last accepted plate, and record the evidence.
- **I4 (page = film).** Art and final lettering are identical in page and film, at 1:1.
- **I5 (substitutions only outside the strips).** The eye and breath move only in the prologue, before the plate is frozen and published. Inside every strip panel and every hold, the art is the canonical plate. The film does not add breathing in the silent panel: there, the silence is carried by timing and sound, per #47.
- **I6 (determinism, no grain).**
  - Every Ink frame is built with `paper(grain=False)`, or with `_grain=False`, because kit grain would break identity.
  - No vignette.
  - Balloon "boil" happens only while a balloon is being written, then locks to the published balloon PNG.

**Concurrency.**
- The plate artist publishes one immutable art layer.
- The writer-letterer branches only on balloons. Alternate lines are kept as named branches (`branch-a/`, `branch-b/`), never merged silently.
- Balloon collisions are solved in layout, never by editing the art.
- Each candidate records owner, base plate sha, read and write sets, changed fields, the tests run, the artifact, and its acceptance condition, in the unit's JSON.

## 6 · Common seed

The section 10 station seed is **not used**, because the chosen direction tells another story. Its park bench at night and the lamp are part of the joke ("ASK THE LAMP"), and the envelope stays **unopened** in both strips. The seed's brass key, bell and opening of the envelope would contradict that.

## 7 · The page (hard proof, page form)

**File:** `assets/pages/moins-dun-quart-de-seconde-pour-vivre.png`. It is 2480 × 1754 px (A4 landscape at 300 dpi), white paper (#FAF9F8 to #FFFFFF), ink near black (#0E0E0E to #151515). All lettering is handmade and written in the same pen hand as the balloons.

| Zone | y (px) | Content |
|---|---|---|
| Header | 70–150 | Hand-lettered left: "ONE PLATE, TWO STRIPS". Right, small: "after Menu & Trondheim, 1991". |
| Strip A label | 220–275 | "A — TO WAIT", lettered. |
| Strip A panels | 290–830 | 4 × 540 px square panels at x = 106, 682, 1258, 1834 (gutter 36). |
| Strip B label | 920–975 | "B — THE ALIBI". |
| Strip B panels | 990–1530 | The same x positions. |
| Footer | 1620–1690 | Small lettering: "the art layer is identical in all eight panels · sha256 xxxxxxxxxxxx". |

- **Panel art:** `plate-540.png`, pasted 8× at scale 1, inside a hand brush border about 9 px wide. The border is drawn once as part of the plate occurrence frame, and is identical in all eight.

**Lettering, in reading order** (capitals, the film's single-stroke pen hand, centred in a white balloon with a wobbly brush outline, the tail toward the snout and mouth):

| Panel | Lines | Balloon placement |
|---|---|---|
| A1 | IF I OPEN IT, / I'LL KNOW. | Upper left, clear of the lamp globe where possible. |
| A2 | IF I DON'T, / I CAN STILL / HOPE. | — |
| A3 | *(no balloon: declared silence)* | The black above the head is empty, and the lamp is fully visible. |
| A4 | HOPE IT IS, / THEN. | Short, like the reference's deflating last line. |
| B1 | ME? I'VE BEEN / ON THIS BENCH / SINCE NINE. | — |
| B2 | ASK THE LAMP. | Placed upper right, so the **lamp globe at upper left stays fully uncovered**. |
| B3 | AND LOOK - / STILL SEALED. | Must not cover the envelope flap. |
| B4 | WHY WOULD I / OPEN SOMEONE / ELSE'S? | — |

**Route.** The reading order is A1→A2→A3→A4, then B1→B2→B3→B4, left to right and top to bottom. There is no other route.

**Comparison condition.** Both strips are printed at the same size, with the art held constant. That is the page itself.

## 8 · Film shot list

The film is 66.0 s at 24 fps, 960 × 540. At 1:1, a page panel of 540 px fills the frame height, and parts of the neighbouring panels and gutters show at the sides. The camera is a crop of the page (handmade page art), so the page and film share pixels.

**Sound sources:**
- FORAGED night ambience: crickets or a quiet park at night, very low, with no music.
- FORAGED pen-on-paper scratch, cut into grains, one grain per written stroke. The grain length follows the stroke length and the gain follows the stroke speed (#47).
- A soft tap where the pen lifts at each full stop or question mark.
- Synthesized sound is allowed only as a fallback, and must be declared.

| # | Time | On screen | Heard |
|---|---|---|---|
| S0 Prologue: drawing the plate | 0:00.0–0:06.0 | Camera at 1:1 on panel A1's position: a black ground in the hand border. The plate is brushed on straight-ahead, stroke by stroke, in the plate's recorded stroke order: lamp post, globe, bench slats, body mass, ear, snout, eye, envelope, fur dashes, ground dashes. Strokes start slow, then come fast (about 4.5 s). 4.5–5.6 s: the #38 library settle, ≤5 substitution drawings decoded by DP with minimum 3-frame holds. The eye slides from centre to the envelope, there is one blink, then an exhale (the chest mass lowers about 3 px), and the last frame lands **exactly** on the canonical plate. 5.6–6.0 s: hold; the plate is frozen. | Brush/pen scratch per stroke; the ambience fades in from 0. |
| S1 The page is printed | 0:06.0–0:09.0 | The camera pulls back to the full page (about 0.36 scale). The 7 other panels receive the plate, one hard appearance per panel every 4 frames, unchanged. Strip labels and the header are written on, about 0.8 s. Unlettered page: 8 identical panels. | Ambience; a soft paper tap per panel. |
| S2 Push in | 0:09.0–0:10.0 | Eased move into A1, landing at 1:1. | Ambience. |
| A1 | 0:10.0–0:15.0 | The balloon outline is drawn (8 frames), then "IF I OPEN IT, / I'LL KNOW." is written at about 9 glyphs/s (≈2.2 s), then held. | Scratch per stroke; ambience. |
| move | 0:15.0–0:15.6 | Lateral slide, page at 1:1. | — |
| A2 | 0:15.6–0:21.0 | Outline, then "IF I DON'T, / I CAN STILL / HOPE." (≈2.4 s), then hold. | Scratch. |
| move | 0:21.0–0:21.6 | Slide. | — |
| **A3** | **0:21.6–0:26.0** | **No balloon. Nothing moves: the art and the camera are still for 4.4 s.** The empty black above the head is the event. | **Declared silence: ambience only. No scratch, no tap, no music.** |
| move | 0:26.0–0:26.6 | Slide. | — |
| A4 | 0:26.6–0:31.0 | Outline, then "HOPE IT IS, / THEN." (≈1.6 s), then a 2.5 s hold. | Scratch, then a tap at the full stop. |
| S3 Strip A whole | 0:31.0–0:33.5 | Pull back to strip A complete, 4 panels in frame. Hold for reading. | Ambience. |
| S4 Travel | 0:33.5–0:35.0 | Down the page to B1, landing at 1:1. | — |
| **B1** | **0:35.0–0:40.5** | Outline, then "ME? I'VE BEEN / ON THIS BENCH / SINCE NINE." (≈3.5 s), then hold. | Scratch. |
| move | 0:40.5–0:41.0 | Slide. | — |
| **B2** | **0:41.0–0:44.5** | "ASK THE LAMP." (≈1.2 s), then a 2 s hold. The lamp at upper left is uncovered; the camera does not move, so the reader's eye goes to the lamp. | Scratch; ambience. |
| move | 0:44.5–0:45.0 | Slide. | — |
| **B3** | **0:45.0–0:49.5** | "AND LOOK - / STILL SEALED." (≈2.2 s), then hold. The flap is uncovered. | Scratch. |
| move | 0:49.5–0:50.0 | Slide. | — |
| **B4** | **0:50.0–0:57.0** | "WHY WOULD I / OPEN SOMEONE" is written. **The pen holds for 10 frames**, then "ELSE'S?" is written. A 3.0 s hold on the finished panel: the same eye, now guilty. | Scratch; silence during the pen hold; a tap at the "?". |
| S5 Comparison | 0:57.0–1:06.0 | 57.0–58.5: pull back to the full page, both strips at the same size. 58.5–61.0: hold. 61.0–64.0: the strip A row's balloon plane and strip B's balloon set alternate over that one row every 18 frames, 2 cycles; the art does not change, only the words switch. 64.0–66.0: the full page is held, then cut to black in the last 6 frames. | Ambience, fading out over the last 2 s. |

**Animated frame by frame:**
- the plate draw-on and settle (S0);
- every balloon outline and every letter (written stroke by stroke on ones, with the pen position advancing along each stroke's path at a velocity with ease in and ease out, and a 2-frame pen lift between strokes);
- the panel-arrival stamps.

**Balloon plane in motion.** While a balloon is being written, the balloon plane may re-jitter every 2 frames ("boil"). It locks to the published balloon PNG when writing ends.

## 9 · Elements: foraged or handmade

| Element | Status | What |
|---|---|---|
| Plate (creature, bench, lamp, envelope, ground, stars) | HANDMADE | A brush-ink drawing built from pressure-varying dab chains with tapered ends (proposals/src/plate.py and hand.py as the base). White masses on a black night ground, as in kf-1, re-framed tighter (§10). Recorded as an ordered stroke ledger. |
| Envelope | HANDMADE | Drawn into the plate, with a sealed flap (a visible diamond seal at the point) and, on its face, an illegible scribble of an address. The LoC 1865 envelope from the proposals is **not used**. Thresholding a photograph into the plate would be a filter over real material, and a legible "someone else's" address would pre-empt B4 in every panel. The env1861, env1862 and env1865 files stay unused, and are not credited because they do not appear. |
| Eye/breath substitution library (prologue only) | HANDMADE | ≤5 redrawn variants of the plate, each differing from the canonical plate only inside an eye or chest mask. |
| Balloons and lettering | HANDMADE | A single-stroke capital pen hand (hand.py base), with per-glyph variation and a real stroke order. Wobbly brush balloon outlines. No typed font anywhere on the page or in the panels. |
| Hand panel borders, header, labels, footer | HANDMADE | The same brush and pen. |
| Night ambience | FORAGED | Look first in the Moving Image Archive cache for a clip with real night-exterior sound, judged by listening, not by title. Otherwise Wikimedia Commons audio ("crickets night", "night ambience park"), with the licence read from extmetadata: PD, CC0, BY or BY-SA. |
| Pen/brush on paper scratch | FORAGED | Commons audio: "writing pen paper", "pencil writing", "dip pen". PD, CC0, BY or BY-SA. Fallback: a synthesized band-limited noise grain, declared in the notes. |
| Speech | none | The voice is the balloons. No TTS. |

## 10 · Aesthetic target

Sources: the reference `assets/references/iteration-001.webp` (800×196, four panels) and the chosen keyframe `proposals/kf-1.png`. Samples were taken with PIL in this session.

**Medium.** Brush and pen ink on paper, reproduced in pure black and white, like a photocopied small-press strip. The drawing is a real brush line: thick-thin contour, tapered ends, dry-brush breaks.

**Tonal range** (measured):
- *Reference:* 33% dark (luma < 60), 55% light (> 200), and 12% mid. The mid share is mostly antialiasing and photocopy edge, not grey fill.
- *kf-1:* 42% dark, 53% light, 5% mid.
- *Target:* two tones. Mid share ≤ 12% (edges only), no grey fills, no gradients, no shading.

**Palette** (sampled):
- *Reference:* ink ≈ RGB (16,16,16) to (21,21,21); paper ≈ (250,250,250) to (255,255,255); a stray grey (177,177,177) on edges.
- *kf-1:* ink (0,0,0), paper (255,255,255).
- *Target:*
  - ink #121212 to #151515. Pure 0 is allowed, but the reference sits at about 18.
  - paper #FAF9F8 to #FFFFFF.
  - No colour anywhere: R = G = B ± 2.

**Light.** Flat, graphic, no modelled light. "Night" is carried by a black panel ground with white masses and a few white stars. The lamp globe has broken white highlight strokes, not a glow. There are no gradients, no blur and no vignette.

**Texture.** Only what the brush makes: dab-chain wobble, fur dashes, wood-grain flecks, slightly ragged balloon outlines. **No added grain or noise filter.** Kit grain is off, which also protects I1.

**Framing and scale.**
- *Reference:* square panels (≈190 px in an 800 px strip), a heavy black border, gutters ≈ 7% of panel width. The creature fills the panel and is cropped by the panel edge at the bottom, with balloons in the remaining black above.
- *kf-1 is looser:* the creature is about 60% of panel height and the full bench is shown.
- *Target:*
  - Square 540 px panels with a ≈9 px brush border and a gutter of 36 px (6.7%).
  - Re-frame tighter than kf-1: the head and torso fill about 70% of panel height. The bench seat and back are cropped by the left and right panel edges, and the feet and ground may be cropped at the bottom. The lamp globe stays inside the top-left of the panel.
  - The upper ~35% stays black and empty for balloons, on both sides of the head.
  - The eye is about 0.45 panel-width from the left, so balloons never cover it.

**Typography.**
- Hand-lettered capitals in a single-stroke pen hand, at the size where 12–14 glyphs fit a balloon line. The reference uses a small casual hand and three-line balloons; kf-1 uses capitals.
- The stroke weight on the page is about 3.5–4 px at 540 px panels.
- Balloons are white, with a slightly wobbly brush outline about 5 px thick and a short tapered tail to the snout.
- The page header and labels are in the same hand, larger. No typeset fonts.

**Pacing.**
- The reference rhythm is setup, development, silence, short deflation. The last balloon is the shortest.
- In the film:
  - the pen writes at about 9 glyphs/s;
  - each balloon is held for at least 2 s after it is written;
  - A3's silence is held for 4.4 s;
  - B4 has a 10-frame pen hold before "ELSE'S?";
  - camera moves between panels are short (0.5–0.6 s, eased) and there are no fades between panels.

## 11 · Technique SCIONs (from swarms.json, read in full)

### #17 South Park: Repeatable Graphic Grammar (the core)

**Why.** The whole proof is a restricted, reusable graphic grammar. One cutout plate, a stage template (the panel), and dialogue carried by repeatable assets. "Limited animation should function as expressive style."

**Native primitives kept:**
- the shape kit, which is the plate as one asset;
- the expression atlas, reduced to one expression on purpose;
- a reusable stage template (the panel occurrence frame);
- the dialogue layer, which is the balloon plane.

**Applied:**
- S0–S1: the plate is published once and pasted unchanged into 8 panels.
- In every panel, only the balloon plane changes.
- S5: balloon sets are swapped over one row.

**Numeric invariant.** sha256(art-only raster) is equal for all 8 page panels and all 8 film holds, and the negative controls fail.

**Perceptual achievement.** The repetition is felt as deadpan comic timing, not as laziness. The speaker is always legible and the recurring asset is consistent. Scenes can be revised (an alternate line) without redrawing anything.

**Acceptance tests:**
- the speaker is legible (tails to the snout);
- the asset is consistent;
- timing carries the joke;
- a line can be revised with no art change.

### #47 Sound-to-Action: Viseme and Gesture Swarm

**Why.** "Allowing silence to animate thought." The silent A3 and the 10-frame pen hold in B4 are the dramatic engine. Sound events must drive the writing action, and there must be "no mechanical flapping in silence".

**Native primitives kept:**
- audio events: one per stroke onset;
- timing: the stroke and glyph schedule plays the role of phoneme timing;
- expressive holds: A3, the B4 pen hold, the post-balloon holds;
- sonic perspective: the ambience is distant and the pen is close.

Visemes are replaced by pen strokes. The mouth stays closed by invariant, which is #47's "mouth closures at relevant events", kept as a permanent closure.

**Applied:**
- In every lettered panel, each scratch grain is aligned to its stroke.
- In A3 and the B4 pen hold, nothing moves and there is no scratch.

**Numeric invariant.** Every scratch-grain onset falls within ±1 frame of a stroke onset in the letterer's schedule. Zero grains fall inside A3 (0:21.6–0:26.0) or inside the B4 pen hold.

**Perceptual achievement.** You hear the words being written. The silence of A3 is heard as the creature deciding, not as a dropout.

**Acceptance tests:**
- no flapping in silence;
- impact cue and reaction appropriately spaced (the pen hold, then "ELSE'S?").

### #38 Dynamic Pose Selection: Drawing Library Swarm (prologue only)

**Why.** The direction allows the eye and breath to move "by tiny drawing substitutions only where the constraint allows". That is only before the plate is frozen. #38 builds coherent motion from a sparse library of drawings, with minimum-duration holds, and protects the key pose.

**Native primitives kept:**
- illustrated candidate states, ≤5 drawings: eye-centre, eye-half, eye-closed (blink), chest-in, and the canonical plate;
- a transition matrix that penalizes flicker and forbids eye-closed → chest-in in one frame;
- a DP decoder over a target action curve (look toward the envelope, blink, exhale, rest);
- minimum-duration holds of 3 frames.

**Applied in S0** at 4.5–5.6 s. The decoder must end on the canonical plate.

**Numeric invariant:**
- every library drawing differs from the canonical plate only inside its declared mask (diff bounding box ⊆ mask);
- the decoded path's last state is the canonical plate (sha equal);
- no state is held for fewer than 3 frames.

**Perceptual achievement.** The creature visibly settles into the pose it will hold for the rest of the film: a look, a blink, a breath. It reads as alive, not flickering. The key pose (the pupil on the envelope) is not averaged away.

**Acceptance tests:**
- no flicker;
- the key pose is protected;
- the source art is stable.

**Rejected for this proof:**
- #2 Reiniger and #45 occlusion (Direction 2's material);
- #40 tabletop (Direction 3);
- #7 Foldès metamorphosis, because metamorphosis is exactly what the strict proof forbids inside the strips.

## 12 · Units (maker units; the editor, readers, critic and reviewer run separately)

### U1 · plate-artist (HANDMAKE)

**Output:** `films/swarm/moins-dun-quart-de-seconde-pour-vivre/plate.json`. Media go in `films/sources/moins-dun-quart-de-seconde-pour-vivre/plate/`.

**Builds:**
1. The canonical brush plate, drawn at 1080 px and reduced once to `plate-540.png`, the one occurrence raster. Its sha256 goes in plate.json. The plate also includes the hand border.
2. `strokes.json`: the ordered stroke ledger (each stroke's dabs, pressures and order). Rendering the strokes cumulatively must end byte-equal to the canonical plate. `render_upto(n)` code is provided for the draw-on.
3. The #38 library (≤5 drawings plus masks) and a decoded settle path for S0.
4. A balloon-safe mask: where balloons may sit, excluding the eye, snout tip, envelope flap and lamp globe.
5. Negative controls: `plate-crop1px.png` and `plate-mouth-redraw.png`.

The plate is re-framed tighter, per §10. The ear must not run into the upper balloon zones.

Code lives in that folder (copied from proposals/src/plate.py and hand.py).

### U2 · writer-letterer (HANDMAKE)

**Output:** `films/swarm/moins-dun-quart-de-seconde-pour-vivre/balloons.json`. Media go in `films/sources/moins-dun-quart-de-seconde-pour-vivre/letterer/`.

**Writers' room:**
- Two competing four-beat arcs per strip. The chosen lines (§7) are fixed, and the B1–B3 test-shot lines are locked.
- At least one named alternate per strip, kept in `branch-a/` and `branch-b/`.
- A DialogueBeat ledger: speaker, addressee (B has an unseen questioner), intention, and transition in the listener's understanding. A3 is recorded as a Silence beat.

**Letterer:**
- RGBA balloon layers A1, A2, A4 and B1–B4, each 540×540 and transparent outside the balloon. A3 is a silence entry with no file.
- Placement inside the safe mask from U1. B2 keeps the lamp clear and B3 keeps the flap clear.
- The write-on schedule per balloon: outline strokes, then glyph strokes in pen order, with start and end frames, point paths and pen lifts. It includes the B4 10-frame hold, and frames are counted from each panel's start.
- The page header, labels and footer lettering, as RGBA in the same hand.
- Proof: the final schedule frame equals the published PNG.

### U3 · sound (FORAGE plus small handmade grain engine)

**Output:** `films/swarm/moins-dun-quart-de-seconde-pour-vivre/sound.json`. Media go in `films/sources/moins-dun-quart-de-seconde-pour-vivre/sound/`.

**Forage:**
- the night ambience and a pen-on-paper scratch, from the MIA cache first (by listening) and then Commons audio;
- licences read from extmetadata;
- ≤ 20 MB.

**Build:**
- Decoded WAVs and a grain bank cut from the real scratch.
- A function or script that takes U2's write-on schedule and the film timeline (§8) and emits a cue list: one grain per stroke, length following the stroke, gain following velocity, and taps at the full stop and question mark.
- The ambience bed with the declared A3 silence.
- Draft credits entries.

**Proof:** a printed check that the cue onsets match the stroke onsets, and that there are zero cues inside A3 and the B4 hold.

### Editor (run by the workflow, not a maker unit)

The editor builds:
- `films/moins-dun-quart-de-seconde-pour-vivre.py` with kit.Film (Ink frames with grain off);
- the page;
- the strips;
- the deliverables listed below, the equality check, credits, notes and assembly.md.

## 13 · Deliverables (section 9)

All paths are absolute:

- `/home/user/bolas/paeleo/scion/oulipo/assets/pages/moins-dun-quart-de-seconde-pour-vivre.png`: the page, 2480×1754.
- `/home/user/bolas/paeleo/scion/oulipo/assets/films/moins-dun-quart-de-seconde-pour-vivre.mp4`: the film, 66 s.
- `…/films/swarm/moins-dun-quart-de-seconde-pour-vivre/deliverables/strip-A.png` and `strip-B.png`: the two four-panel strips.
- `…/deliverables/plate-canonical.png` and `…/deliverables/page-unlettered.png`: the unlettered canonical art.
- `…/deliverables/balloons/A1.png A2.png A4.png B1.png B2.png B3.png B4.png` and `…/deliverables/balloons/balloons.json`: the balloon layer files, with A3 as a silence entry.
- `…/deliverables/equality_check.py` and `…/deliverables/equality-check.json`: the asset equality check. It covers the 8 page panels, the 8 film holds, the page = film comparison, and the negative controls failing.
- `…/deliverables/reader-comparison.jpg` and `…/deliverables/reader-comparison.md`: both strips at the same size with the art held constant, plus the collated blind-reader answers.
- `/home/user/bolas/paeleo/scion/oulipo/films/moins-dun-quart-de-seconde-pour-vivre.py`, `films/credits/moins-dun-quart-de-seconde-pour-vivre.json`, `films/notes/moins-dun-quart-de-seconde-pour-vivre.txt` and `…/swarm/moins-dun-quart-de-seconde-pour-vivre/assembly.md`.

## 14 · The bar

Summary only; plan.json is authoritative and frozen.
- **Blocking:**
  - **B1:** the proof reads.
  - **B2:** the fixture passes, including the negative controls and page = film.
  - **B3:** genuinely handmade, genuinely animated, foraged sound credited.
  - **B4:** the aesthetic holds against the reference and kf-1.
  - **B5:** the silence and the pen sound work.
- **Advisory:**
  - **V1:** the prologue settle.
  - **V2:** the comparison swap.
  - **V3:** the alternate-line branches.
  - **V4:** the size budget.

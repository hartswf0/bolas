# Cercle vicieux: the service door. Director's plan

- **Prompt:** `prompts/cercle-vicieux.md`, Long-form panel palindrome, after Étienne Lécroart (2000).
- **Chosen direction:** 2, "Shadow door" (`proposals/kf-2.png`). Direction 1's FSA material folds in as *profiles*: real porter and passenger heads are cut from LoC photographs and printed solid black.
- **Story:** the common seed from section 10, with one variation, given in §1.
- **Status:** the plan is rebuilt from scratch, and the bar in `plan.json` is frozen. Any change goes to `amendments.md`.

---

## 0 · Creative thesis

The same black paper puppet changes what it is doing because of what it now stands next to. Panel A opens the book: a porter flings his arm out in front of a visitor walking towards the service door and shouts "YOU! STAY RIGHT THERE." It reads as an accusation, because the bell has just rung and the stranger looks like the one who rang it.

The hinge comes after one purposeful page turn. Panel X shows the only thing in the book that is seen once: a hand behind the frosted glass of the service door, pulling the bell cord. Nobody can come out of that door.

Eight panels later the identical drawing of A closes the book, with the same balloon, the same swing of the bell and the same pose. Now the porter's arm is a barrier between the visitor and the glass. The reader should feel that A was protection all along, and that the first reading was the reader's own mistake.

**What would make it bland:**
- The back half plays as a rewind or a duplicate. That happens if the hinge only adds a fact the forward half already implied.
- The hand is staged too vaguely to be a hand, or is shown twice. Once means once.
- The silhouettes are blocky rectangles with no profile, so no one acts.
- Grey wash floods the page.
- The camera pans and fades over static panels, so nothing moves with weight.
- The film's panels differ from the page's panels, which breaks the identity the whole proof rests on.
- The lettering is so small that a phone viewer reads only shapes.

## 1 · Defining beat and comparison baseline

**Defining beat.** It runs from the page 2 → 3 turn (≈ 33.3–34.8 s) through X (34.8–40.0 s) and into H (40.0–43.5 s).
- The leaf turns away from H, where the visitor asks "THEN WHO RANG THE BELL?".
- X opens page 3: a tall column holding the caption box "THE BELL CAN ONLY BE RUNG FROM BEHIND THAT DOOR."
- The blurred shadow of a hand behind the frosted pane grips the cord and pulls twice. The bell swings twice, with the clapper lagging, and the light under the door flickers. The porter, his back to us, tilts his head up.
- Then the identical H panel answers the caption with the same question, which now has an answer nobody wants.

**The payoff.** It comes at 63.5–67.5 s, the closing A.
- A viewer should point to the frosted pane in X and say "someone is behind the glass: they rang it".
- They should then point to the last A and say "he isn't accusing her, he's keeping the visitor away from that door".

**Comparison baseline.**
- `proposals/kf-2.png`, the chosen keyframe. It already has the layout, but its puppets are blocky, its lace is thin and its screens are too grey (42 % mid-tone pixels).
- The previous film, `films/cercle-vicieux.py`, with its drawn cartoon people and synthesized murmurs. It had the palindrome right, but the hinge was a caption and a "DRRRING!" sound effect, with no image of an agent.
- The reference page `assets/references/cercle1.webp` is the tonal and typographic bar: pure black on white, hand capitals, round balloons.

To win, the work must:
- **beat kf-2:** finer profiles cut from real photographs, scissor-jog edges, punched lace, near-white screens, and genuine frame-by-frame motion;
- **beat the old film:** the hinge is an *image* of the hidden ringer.

**Story variation from the seed.** Everything in the seed appears: the visitor, the sealed envelope, the bell, the brass key, the bench and the service door that stays closed.
- The bell rings *at the start*, and its cause is revealed by X.
- The key is left on the bench in F. "Walks away" becomes the visitor stepping back from the bench in F, and leaving after the last page, off the page.

**Canonical chronology,** kept outside the page as the section 10 rule asks:
1. X: a hand behind the door pulls the cord, the bell rings, and the porter looks up.
2. A: the visitor walks in towards the door, and the porter stops the visitor.
3. B, then C.
4. D: the envelope is opened and the key is found.
5. E: the porter identifies the key.
6. F: the key is left on the bench.
7. G, then H.
8. The visitor leaves (off-page). The door never opens.

The forward reading puts X in the middle as a revelation of what happened *first*. That is why the backward leg is a second reading of the evidence.

## 2 · Lineage Genome (compact)

| field | value |
|---|---|
| source medium | Printed bande dessinée album: *Cercle vicieux*, L'Association, 2000, a 30-page panel palindrome (OuBaPo). Brush and pen ink, 2×3 grids, hand lettering. |
| target media | (a) A 4-page printed silhouette comic. (b) A 72 s rostrum film that performs the reading of those same pages. |
| preserved relation | The flattened reading order is a palindrome around a single hinge panel. Each mirrored occurrence is the *same* artwork and balloon (identity, not redraw). Meaning changes through neighbours. |
| optics change | Line drawing becomes backlit shadow theatre: solid black puppets on near-white screens (Reiniger). The camera is a rostrum that reads panel by panel. The page turn is a physical leaf. |
| formalism change | 30 pages → 4 pages and 9 panels, with 17 occurrences. A panel's motion cycle and sound cue count as part of its immutable artwork. Pages are recto-only, so every page boundary is a concealing turn. |
| concept change | The hinge is an image of a hidden agent (the hand behind the glass), placed on the purposeful turn. The repeated first panel inverts from accusation to protection. |
| sound change | The silent book gets a per-panel sound cue, identical at both occurrences: foraged bell and room tone, plus paper and key. Speech stays lettered; there is no TTS. |

**Formation epochs** (weight 0–100):

| weight | epoch | reason |
|---|---|---|
| 90 | OuBaPo/Oulipo constraint comics, 1987–2000 | Direct source of the constraint. |
| 70 | Reiniger silhouette film, 1919–1936 | Material and technique of the puppets, pins and backlight. |
| 40 | Content-addressed verification, hashing and diff, 1990s– | The identity invariant is tested on bytes. |
| 30 | Töpffer / early newspaper strip grid, 1830s–1910s | The Z reading order and page turn as an act of suspense. |
| 20 | FSA/OWI documentary photography, 1935–44 | The foraged real profiles of a red cap and a passenger. |
| 10 | Railway-station melodrama, the closed door and the bell | Genre furniture. |

**Uncertain claims** are recorded as uncertain.
- "30 pages" and "reverses at its midpoint" come from the L'Association catalogue page. They are not independently inspected beyond one reference page.
- The Contrebandes description of balloon identity across the turn is uninspected.
- I do not claim Lécroart used a single-panel hinge rather than a seam.

## 3 · Olog and the central operation

**Types (◻):**

| type | holds |
|---|---|
| ◻Panel | `id ∈ {A,B,C,D,E,F,G,H,X}`, `art_hash` (sha256 of the ordered frame sequence of its cycle plus its held still), `lettering` (exact string and balloon kind), `speaker ∈ {porter, visitor, caption, none}`, `anchors` (bell, door pane, bench, key, envelope, positions in panel coordinates), `size` (w×h px), `cycle` (n frames @24 fps, posed on twos), `sound_cue` (sha256 of its PCM) |
| ◻Occurrence | `index 0..16`, `panel_id`, `page 1..4`, `slot` (grid cell), `t_in`, `t_out` |
| ◻ReadingOrder | `List[Occurrence]` flattened across pages, Z order (left→right, top→bottom) |
| ◻StoryRole | `occurrence → (purpose, prev_neighbour, next_neighbour)` |
| ◻Page | `n`, `grid`, `occurrences`, `preceded_by_turn: bool` (true for all; pages are recto-only) |

**Arrows:**
- `shows: Occurrence → Panel`
- `on: Occurrence → Page`
- `plays: Occurrence → StoryRole`
- `[mirror]: prefix:List[PanelID] × hinge:PanelID → ReadingOrder`, defined by `prefix ++ [hinge] ++ reverse(prefix)`

**Central operation:** `mirror([A,B,C,D,E,F,G,H], X)`.

**Typed preconditions:**
1. `prefix` is a non-empty `List[PanelID]` with distinct IDs.
2. `hinge ∉ prefix`.
3. Every ID resolves to exactly one immutable ◻Panel with `art_hash`, `lettering`, `speaker`, `cycle` and `sound_cue` fixed at a known revision.
4. The page layout puts occurrence 8 (X) in the first reading slot of a page whose previous boundary is a turn.

**Observable consequences:**
- `len(order) = 17`.
- `|set(order)| = 9`.
- `order == reversed(order)`.
- For every `i ≠ 8`, the occurrences `i` and `16−i` have identical `art_hash`, `lettering` and `sound_cue`. In the page PNG, their panel crops are byte-identical. In the film, their frame sequences are identical frame for frame.
- X occurs exactly once, as the first panel of page 3. The hand behind the glass appears in X only; the pane in A, G and E is plain lit glass.
- `StoryRole(occ0) ≠ StoryRole(occ16)`. Accusation becoming protection is a *perceptual* consequence, checked by blind readers, not by code.

**Counterexamples:**
- `[A,B,C,X,C,B′,A]`, where B′ drops one word ("I WAS TOLD TO WAIT ON THE BENCH.") or moves the bench by one pixel. It is still a palindrome of *labels*, but the hash check fails. The validator must reject it.
- `[A,B,C,X,X,C,B,A]` fails the single-centre check. It is the seam variant: it passes only a seam check with a doubled centre, which is a different hinge type.
- A structurally perfect sequence where readers see only a rewind passes the code and fails the thesis. Section 8's repair applies: keep every panel and change which state X makes inferable.

**Replay equivalence and divergence:**
- Equivalent: reading the page and watching the film give the same flattened order and the same artwork per occurrence, and the turns conceal equally. The film shows one page and never previews the next.
- Divergent:
  - The film enforces dwell, sound and the order of attention.
  - On paper the eye can glance ahead within a page, for example see A at the bottom right of page 4 before D.
  - Only the film plays the motion cycles. The page shows each panel's held still, which is the cycle's final frame.
  - Rewatching the film, or re-reading backwards, is equivalent by construction: a palindrome replays identically in both directions at the level of panel IDs. Inside each panel time still runs forward; panel cycles are never reversed.

**Interaction and TTL.** This is not interactive work; the page and film are read at the reader's pace. TTL is 2 (the default) and is not consumed by this plan.

## 4 · Invariants (section 4)

- **I1 Identity.** Every mirrored occurrence points to the exact original panel. For the pair (i, 16−i), the same `art_hash` gives an identical still in the page and identical frames in the film, with the same lettering, the same balloon geometry and the same sound cue. No re-render per occurrence: the page and the film both read from the one canonical `panels/<ID>/` export.
- **I2 Single hinge.** We declare a **single hinge panel**, X. It is not a seam. X is the only panel with one occurrence. The seam variant with a doubled centre is a post-acceptance experiment (section 8) and is not the deliverable.
- **I3 Format freedom.** Grids may change per page (title column on p1, X column on p3, colophon column on p4). The flattened order A B C D E F G H X H G F E D C B A never changes. Every paired panel has the same pixel size, and X is the only tall panel.
- **I4 Ownership.** The panel unit owns panel IDs and their cycles. The page assembly and the film *derive* the suffix from the same IDs; they never redraw. A patch to any panel invalidates both its occurrences and the transitions next to them. The validator re-runs over the page PNG and the film after every export.
- **I5 Revision.** Each export records `{owner, base_revision (registry sha), read_set, write_set, changed_fields, tests, artifact, acceptance}` in `validation/symmetry.json`. Integration is checked against the expected registry sha. A broken hard invariant quarantines that candidate in `validation/quarantine/`, and work resumes from the last passing export.
- **I6 Once means once.** Only X may contain the hand, and the service door is never drawn open.

## 5 · Hard proof: the four pages (section 6), exactly

**Page format:**
- Landscape 2400×1350 px per page, which is kf-2's format at print resolution (≈ 254 mm wide at 240 dpi), on neutral white paper.
- **Recto-only booklet:** each page is printed on its own leaf and read one at a time, so every page boundary is a turn that hides the next page.
- I kept kf-2's landscape page (the user's pick) and did not move to portrait spreads. In a spread, pages 2 and 3 would face each other and X would be visible before the turn. Recto-only makes the turn real.

**Panel sizes, fixed for all occurrences:**
- **Paired cell:** 800×590 px.
- **X:** 600×1210 px, the height of two cells plus a gutter.
- **Gutter:** 30 px. Borders are 5–7 px, hand-inked and jogged.
- **Margins:** 60 px. The folio is "- n -", hand-lettered and centred at the foot.

**Page layouts:**

| page | left column (600 px) | 2×2 grid, Z order |
|---|---|---|
| p1 | title block, not a panel: hand-lettered "CERCLE VICIEUX", "the service door", a silhouette bell vignette | **A B / C D** |
| p2 | none: the 2×2 grid is centred, and the margins hold only the folio | **E F / G H** |
| p3 | **X**, a tall column (x 60–660) | **H G / F E** |
| p4 | colophon block on the *right* side, mirroring p1's title: "FIN" and the credits line, not a panel | **D C / B A** |

- On p3, X is read first; it is tall and top-left.
- p4's grid sits on the left. A is the bottom-right panel of the book, just as A was the first top-left cell after the title.

**Flattened route:**

| occurrences | page | panels |
|---|---|---|
| 0–3 | p1 | A B C D |
| 4–7 | p2 | E F G H |
| 8–12 | p3 | X H G F E |
| 13–16 | p4 | D C B A |

The hinge X sits at occurrence 8 of 17, opening page 3 after the purposeful turn from H.

**The nine canonical panels.**
- Lettering is single-stroke hand capitals, set glyph by glyph.
- Balloons are round with tails, except where noted.
- Sound is identical at both occurrences.
- Cycle lengths are in seconds at 24 fps, posed on twos (12 poses/s). The page still is the cycle's final pose.

| ID | speaker / lettering | stage and action (handmade unless stated) | cycle | sound cue |
|---|---|---|---|---|
| **A** | porter: "YOU! STAY RIGHT THERE." | Arched wall. The service door is at right, with its frosted pane lit plain and empty, and the bell on a bracket above it. The porter stands *between* the door and the visitor. The visitor enters from the left, mid-step, envelope in hand. | 4.0 s. The bell swings ±0.30 rad, decaying to rest by 3.2 s, with the clapper lagging. The porter's forearm rises from his side to palm-out in 6 poses with a 2-pose overshoot. The visitor's lifted foot lowers and freezes. | foraged handbell, one ring; one footstep |
| **B** | visitor: "I WAS ONLY TOLD TO WAIT ON THE BENCH." | The bench (lace-punched slats), the visitor sitting down with the envelope on their lap, the porter at the panel's edge | 3.0 s. Hips pivot to sit (4 poses); the head turns to the porter (substitution between two cut profiles). | room tone; a bench creak |
| **C** | porter: "WHO SENT YOU?" | A close two-shot. The porter leans in; his head is a cut FSA red-cap profile. The visitor holds up the *sealed* envelope (punched wax-seal lace). | 2.5 s. The porter leans 8° about his hip pin; the envelope lifts. | room tone |
| **D** | none (silent) | Hands and envelope, close. The flap lifts and a brass key slides out into the palm. The key is a solid silhouette with a punched bow. | 3.5 s. The flap (paper, spring-damped) opens; the key slides 6 px per pose, drops and bounces twice. | paper; key clink |
| **E** | porter: "THIS OPENS THE SERVICE DOOR." | The porter holds the key up towards the door, which is dark and closed, at the right edge (kf-2 p3 panel 5). | 3.0 s. The arm raises the key (shoulder and elbow pins); the key sways from his fingers and settles. | small key jingle |
| **F** | visitor: "THEN I DON'T WANT IT." | The key lies on the bench, and the visitor steps back from it, hand withdrawn (kf-2 p3 panel 4). | 3.0 s. The key is set down, rocks and settles; the visitor takes one step back. | key on wood; one step |
| **G** | porter: "NOBODY GOES THROUGH THAT DOOR." | The porter beside the closed door, a black slab with a thin line of light under it (kf-2 p3 panel 3) | 3.0 s. His head turns to the door (2 profile substitutions); his arm points. | low room hum |
| **H** | visitor: "THEN WHO RANG THE BELL?" (dashed whisper balloon) | The visitor points at the bell, which is still and at rest (kf-2 p3 panel 2). | 3.5 s. The arm lifts to point (4 poses), then holds. | near-silence, room tone only |
| **X** | caption box (rectangular): "THE BELL CAN ONLY BE RUNG FROM BEHIND THAT DOOR." | Tall. The bell on a bracket, its cord running down into the door frame. The service door's frosted pane is backlit from behind. **On the glass, the blurred shadow of a hand gripping the cord: seen once in the book.** The porter has his back to us, at left. The light under the door spills onto a black floor. | 5.2 s. The hand-shadow pulls down twice (on twos, blurred because it is behind glass), and each pull impulses the bell (damped pendulum, clapper at 1.6× lag). The cord's slack follows. The light under the door flickers with the hand. The porter's head tilts up over 4 poses. The final pose has the hand at rest, gripping the cord, and the bell nearly still. | foraged bell rung twice, muffled; cord creak |

## 6 · Timed shot list for the film

The film runs 72 s at 24 fps, in 960×540 kit frames, rendered from the 2400×1350 page art (downsampled, or cropped by the camera).
- **Camera:** a rostrum push from the full page into each panel, then a pull-back at each page end.
- **Dwell:** a panel's dwell equals its cycle length plus a hold. It is the same at both occurrences, so the cycles match frame for frame.
- **The page turn** is a physical leaf: a perspective-warped page lifting at the right edge, its shadow tied to the angle, and the next page underneath, revealed only as the leaf passes.

| # | time (s) | on screen | heard |
|---|---|---|---|
| 0 | 0.0–2.5 | Title page block: the p1 title column held full-frame. | room tone fades in (foraged station ambience) |
| 1 | 2.5–4.0 | Page 1 full | room tone |
| 2 | 4.0–8.0 | **A** (cycle 4.0) | A cue: bell, footstep |
| 3 | 8.0–11.0 | **B** | B cue |
| 4 | 11.0–13.5 | **C** | C cue |
| 5 | 13.5–17.0 | **D** | D cue |
| 6 | 17.0–18.0 | Pull back to page 1 | room tone |
| 7 | 18.0–19.2 | Turn 1, leaf | paper turn |
| 8 | 19.2–20.0 | Page 2 full | room tone |
| 9 | 20.0–23.0 | **E** | E cue |
| 10 | 23.0–26.0 | **F** | F cue |
| 11 | 26.0–29.0 | **G** | G cue |
| 12 | 29.0–32.5 | **H**, then a hold on the whisper balloon | H cue (near-silence) |
| 13 | 32.5–33.3 | Pull back to page 2 | silence: the room tone dips |
| 14 | 33.3–34.8 | **Turn 2, the purposeful one**: slower, and the leaf's shadow crosses X before it is seen | paper turn, then silence |
| 15 | 34.8–40.0 | **X** (cycle 5.2): the camera opens on the full tall column, then pushes to the pane as the hand pulls | X cue: muffled bell twice, cord |
| 16 | 40.0–43.5 | **H** (identical) | H cue |
| 17 | 43.5–46.5 | **G** | G cue |
| 18 | 46.5–49.5 | **F** | F cue |
| 19 | 49.5–52.5 | **E** | E cue |
| 20 | 52.5–53.3 | Pull back to page 3, with X and the 2×2 in view together | room tone |
| 21 | 53.3–54.5 | Turn 3 | paper turn |
| 22 | 54.5–58.0 | **D** | D cue |
| 23 | 58.0–60.5 | **C** | C cue |
| 24 | 60.5–63.5 | **B** | B cue |
| 25 | 63.5–67.5 | **A** (identical) | A cue: the same bell, the same footstep |
| 26 | 67.5–69.5 | Pull back to page 4 full, colophon block | room tone |
| 27 | 69.5–72.0 | Hold on page 4, fading to paper white | room tone fades |

**Panel-sequence invariant in the film.** Over the panel's own pixels, before the camera transform, the frames from `t_in` to `t_in + cycle` are the panel's canonical cycle. The camera framing for the dwell on each panel is also identical for the two occurrences, so the editor uses one camera move per panel ID.

## 7 · FORAGED vs HANDMADE ledger

**HANDMADE:**
- The silhouette puppets, porter and visitor. They are polygon bodies with scissor-jog edges, pinned at neck, shoulders, elbows and hips, with punched lace (buttons, the diamond hem, the cap badge, the seal).
- The hand-shadow puppet for X.
- The bell, clapper, bracket and cord.
- The service door with its frosted pane.
- The bench, envelope, key, arched-wall rear pane and backlit screens with tissue fibre.
- Panel borders, balloons and caption box, and all hand lettering.
- The title and colophon blocks, folios and the page-leaf turn.

**FORAGED:**
- **Puppet profiles (rig unit).** Search the Library of Congress (`www.loc.gov/photos`, FSA/OWI, "No known restrictions"). Look for:
  - a railway porter or red cap in a peaked cap, in clean profile. The candidate is LoC 2017843923, *Red cap at the Union Station*, which must be re-downloaded and its rights re-verified.
  - a traveller in a hat and coat in profile. The candidate is LoC 2017843935, or a frontal-profile alternative.
- **How the profiles are used.** GrabCut extracts each head and shoulder contour. It is printed **solid black** as the puppet's head profile, so the silhouette's outline is a real person's outline. No photographic tone appears on the page.
- **Pose timing.** Optionally, one Moving Image Archive clip of a passenger sitting on a station bench, or of a porter gesturing. It is used only to rotoscope joint angles for B's sit and A's arm. The figure is never shown.
- **Sound (panel unit):**
  - A real handbell or door bell recording, first from the Moving Image Archive clips with sound (`forage.py "bell|station|railway"`), then from Commons (`.ogg/.wav/.flac`, PD/CC0/CC BY/CC BY-SA from extmetadata).
  - Station or room ambience from the same archive.
  - A page-turn or paper sound from Commons if one with a free licence exists; otherwise kit synthesis, declared as such.
- **Credits:** every foraged item is credited in `films/credits/cercle-vicieux.json`.
- **Re-use rule.** Earlier LoC files in other works' source folders are *not* read in place. They are re-fetched into `films/sources/cercle-vicieux/puppet-rig/`, with their rights re-verified.

No material from *Cercle vicieux* itself is used. The reference page is studied only and never traced or pasted.

## 8 · AESTHETIC TARGET

The targets are the reference (`assets/references/cercle1.webp`, a Lécroart page) and the chosen keyframe (`proposals/kf-2.png`). The work must meet or beat kf-2 in craft, while pulling its tones towards the reference's absolute black and white.

- **Medium:** printed ink comic page. On it, the drawing is shadow theatre: cut black card puppets laid on backlit tissue screens and photographed flat, as Reiniger did.
- **Tonal range.** These samples were taken with PIL from quantised palettes.
  - **Reference:**
    - The paper is white `#FFFFFF`/`#FEFEFE`/`#F2F2F2`, and the ink is black `#010101`/`#191919`.
    - The only grey is `#8F8F8F`, and it appears only as anti-aliasing.
    - Pixels by luma: 64 % above 200, 22 % below 60, 13 % in between.
  - **kf-2:**
    - The ink is `#080808` and the paper `#F9F9F9`.
    - The screens are `#BCBCBC`/`#9F9F9F`/`#EDEDED`, with a `#606060` falloff.
    - Pixels by luma: 29 % above 200, 28.5 % below 60, **42 % in between**. That is too grey.
  - **Target:**
    - **Ink:** `#080808` solid.
    - **Paper:** neutral `#FAFAF8` with no warm cast.
    - **Screens:** a hot centre at `#F2F2F0` falling to no darker than `#C8C8C6` at the panel edges.
    - **Rear arches:** a single tissue layer at `#B4B4B2`.
    - **The frosted pane in X:** `#F6F2E6`, the only warm tint, lit from behind. The hand shadow is at `#6E6E6E`, blurred.
    - **Overall:** mid-tone luma 60–200 should be **≤ 30 %** of page pixels.
- **Light:** backlit. Each screen has a hot centre near the action and falls off towards the borders. In A, G and X a thin bright line sits under the service door, the one light source *from behind* the door.
- **Texture:**
  - Tissue fibre appears in the screens only.
  - The edges of every puppet show visible scissor jogs.
  - The lace holes are punched through black (buttons, diamonds, badge, seal, bell band).
  - The border lines are hand-jogged.
  - There is no grain or filter over the page.
- **Framing and scale:** mostly medium two-shots and full figures, like the reference.
  - Figures stand at 60–75 % of panel height on a solid black floor band, about 12 % of the panel height.
  - C and D are the close-ups.
  - X is a tall full-height view of the door: the scale of a person against a door.
- **Typography:**
  - Single-stroke hand capitals, each glyph placed with slight drift and tilt (kf-2's hand).
  - Round white balloons with tails and a black 3–4 px line. The whisper balloon in H is dashed, and X uses a rectangular caption box.
  - Cap height is about 2.2 % of the page height (≈ 30 px at 1350).
- **Pacing:** each panel holds 2.5–4 s, and X holds 5.2 s.
  - Page turns take 1.2 s. The p2→p3 turn takes 1.5 s, with a breath of silence before it.
  - Motion is posed on twos, with holds after each gesture settles. Nothing wiggles while a balloon is being read.

## 9 · Animation technique SCIONs (from `swarms.json`)

### SCION 2: Lotte Reiniger, Articulated Shadow Theater

**Why this SCION.** The direction *is* shadow theatre, and its theorem is the proof's: acting must be legible through contour and limited articulation. The relationship in A must invert while the pose stays the same.

**Native primitives kept:**
- backlit character shapes;
- pinned joints with joint-angle limits;
- replacement profiles, for the head turns in B and G;
- contact planes: the floor band, the bench and the cord;
- an exposure sheet per panel, kept in `panels.json`.

**How each panel uses it:**

| panels | what the puppetry does |
|---|---|
| A | The palm-out arm, on shoulder and elbow pins, with an overshoot. The visitor's step lowers through the hip and knee pins. |
| B | The sit. |
| C | The lean. |
| E | The key raise. |
| F | The step back. |
| G | The head substitution. |
| H | The point. |
| X | The porter's head tilt, and the hand-shadow puppet, which is a separate hand with finger pins gripping the cord. |

- **Numeric invariant:**
  - A child piece's pin stays coincident with its parent's pin to within ≤ 1 px in every frame, so limbs never detach.
  - Joint angles stay within their declared limits.
  - Poses change only on twos: frames 2k and 2k+1 are identical within a panel's moving part.
- **Perceptual achievement:**
  - With all colour removed (the page is already B&W), A reads as stop/accusation on page 1 and barrier/protection on page 4.
  - The hand in X reads as a *hand gripping a cord*: the thumb is distinguishable, and the shape does not merge with the cord into a blob.

### SCION 41: Secondary Dynamics, Inertia and Restraint

**Why this SCION.** The bell is the story's evidence. Its swing must show weight, and show *when* it was struck, in A and in X. The key's drop and settle in D, E and F carries the story's object. The cord in X ties the hand to the bell physically.

**Native primitives kept:**
- springs and dampers;
- mass proxies: bell, clapper, key, cord segments;
- a semi-implicit Euler integrator at a 1/240 s substep, sampled on twos;
- collision boundaries: the bench top, the palm and the panel border;
- primary pose impulses: the porter's arm in A has *no* effect on the bell, while the hand's two pulls in X do.

**How each panel uses it:**

| panels | what moves |
|---|---|
| A | The bell, already swinging as the cycle starts, decays. |
| X | Two impulses from the cord. |
| D | The envelope flap and the key bounce. |
| E | The key sways from the fingers. |
| F | The key rocks and settles on the bench. |
| H | The bell is at rest. That is an invariant too. |

- **Numeric invariant:**
  - The bell's swing energy decays to under 2 % of its peak before the end of each panel's cycle, so every cycle ends on its page still.
  - The response begins after the impulse (the clapper lags the bell, lag > 0).
  - There is no interpenetration with the bench, bracket or border in the final pose.
- **Perceptual achievement:**
  - In X the viewer *feels* the two pulls in the bell.
  - The key lands with weight.
  - There is no purposeless wiggle while a balloon is read.

### SCION 43: Collage Graph Rewriting, Identity Change

**Why this SCION.** Its theorem, that an image becomes a new actor while its identity is kept, is the palindrome's thesis stated as a grammar. It keeps panel identity separate from its role in the sequence, which is source anchor 3.

**Native primitives kept:**
- a typed entity graph: Panel, Occurrence, StoryRole and Page nodes;
- rewrite rules: `[mirror]`, plus the seam variant `[mirror-seam]` as a named alternative branch;
- motif tags: bell, pane, key, bench, envelope;
- visual anchors in panel coordinates;
- scene-event contracts, for example "the hand appears only in X" and "the door never opens".

**How it is applied:**
- `registry.json` is the graph.
- The page assembly and the film are both *derived* from it by the rule, and the validator replays the rule on the exported bytes.
- At the defining beat, the motif "pane" changes role: plain light in A and G, an agent in X, and then, remembered, a threat in the closing A.

- **Numeric invariant:**
  - For each `i ≠ 8`, `art_hash(occ i) == art_hash(occ 16−i)` on the page crops *and* on the film's panel frames.
  - Exactly one node has a single occurrence.
  - Every rewrite meets its preconditions (§3).
- **Perceptual achievement:** the viewer follows the change of role without a key. "Same drawing, different meaning" is pointed to by a blind reader.

**Considered and not chosen:**
- **44, Multiplane:** its depth would fight the flat comic page. Only a small parallax is allowed, on the leaf turn.
- **29, GrabCut:** used as a *tool* for the foraged profiles, not as the governing technique.
- **32, FK:** subsumed under Reiniger's pins.

## 10 · Swarm units (section 5, merged)

The montage editor, the blind readers, the critic and the reviewer are run separately by the workflow. No maker validates its own work.

| unit | merges | output (inspectable) | media |
|---|---|---|---|
| **U1 story-page** | story designer + page designer | `registry.json` (panel registry, lettering, speakers, anchors, StoryRole of all 17 occurrences, canonical chronology), `layout.json` (editable page layout), `pages/p1–p4.png`, `assets/pages/cercle-vicieux.png`, `hinge-comparison.png`, `hinge-comparison.md` | `films/sources/cercle-vicieux/story-page/` |
| **U2 puppet-rig** | puppet cutter + hinge engineer + dynamics modeler | `rig/rig.py` (puppets as polygons with pins and limits; profile heads from LoC GrabCut; dynamics module), `rig/rig-sheet.png`, `rig/rig-tests.json`, `rig/credits-rig.json` | `films/sources/cercle-vicieux/puppet-rig/` |
| **U3 panels** | drawing and lettering unit + gesture animator + sound for the panel cues | `panels/<ID>/0000.png…` (canonical cycles), `panels/<ID>/still.png`, `panels/panels.json` (sizes, exposure sheet, per-frame sha256, still sha, lettering, sound-cue sha), `panels/contact.png`, `panels/cues/<ID>.wav`, `panels/credits-panels.json` | `films/sources/cercle-vicieux/panels/` |
| **U4 validator** (not a maker) | symmetry validator | `validation/validate.py` (runs the fixture and checks the real exports), `validation/symmetry.json` (results with revision and evidence labels) | `films/sources/cercle-vicieux/validator/` |

**Order of work:**
1. U1 writes `registry.json` and `layout.json`, and U2 builds the rig, in parallel.
2. U3 builds the panels from both.
3. U1 assembles the pages from U3's stills.
4. U4 validates the pages.
5. The editor builds the film.
6. U4 re-validates the film.

## 11 · Section 9 deliverables

- `assets/pages/cercle-vicieux.png`: the four-page readable comic, imposed 2×2 on one print sheet (≥ 4800 px wide).
- `films/swarm/cercle-vicieux/pages/p1.png` … `p4.png`: the single pages at 2400×1350.
- `films/swarm/cercle-vicieux/registry.json`: the canonical panel registry.
- `films/swarm/cercle-vicieux/layout.json`: the editable page layout.
- `films/swarm/cercle-vicieux/validation/validate.py` and `validation/symmetry.json`: the flattened path and the reversal test, with the fixture.
- `films/swarm/cercle-vicieux/hinge-comparison.png` and `hinge-comparison.md`: X opening p3 after the turn, compared with X as the fifth panel at the end of p2 (no turn). Same order, a different 4/5/4/4 vs 4/4/5/4 split.
- `films/swarm/cercle-vicieux/reader-notes.md`: blind-reader notes, written by the readers' step.
- `assets/films/cercle-vicieux.mp4` (with `.webp` from kit), `films/cercle-vicieux.py`, `films/credits/cercle-vicieux.json` and `films/notes/cercle-vicieux.txt`.

## 12 · Bar

The bar is in `plan.json` and is frozen.

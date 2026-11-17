# Moins d'un quart de seconde pour vivre · Iconic iteration: three directions

**Stage.** In all three directions the comics page is the stage: four panels in a row show one creature in one pose, and only the balloons change. The creature is a new character drawn for this film, not a trace of the reference frog. It is long-snouted and seated on a park bench under a lamp, holding an unopened envelope. Its eyelid is half down and its pupil slides toward the envelope, so the pose reads as patience, guilt or boredom depending on the words. In every keyframe the art layer is checked byte for byte across panels by an `assert` in its script: D1 is 8 of 8 identical, D2 4 of 4, D3 4 of 4. The balloons always sit on their own plane.

**Hard proof (shared by all three).** There are two four-panel strips over the same plate.
- **Strip A, "to wait":**
  1. "IF I OPEN IT, I'LL KNOW."
  2. "IF I DON'T, I CAN STILL HOPE."
  3. *(silent)*
  4. "HOPE IT IS, THEN."
- **Strip B, "the alibi":**
  1. "ME? I'VE BEEN ON THIS BENCH SINCE NINE."
  2. "ASK THE LAMP."
  3. "AND LOOK - STILL SEALED."
  4. "WHY WOULD I OPEN SOMEONE ELSE'S?"

In each strip the last balloon changes how the reader sees the same eye. In A it reads as resignation. In B the reader learns the envelope belongs to someone else, so the sideways glance turns guilty.

**Defining beat:** the silent third panel of A, followed by the B4 line that turns the same expression into an alibi.

**Comparison baseline:** the reference strip, which has four identical frog plates and a wordless panel 3. **Success test:** a viewer can point to (a) the empty panel 3, (b) "SOMEONE ELSE'S", and (c) the identical eye in every panel.

**Planned film (about 60 s, 24 fps):**
- 0:00–0:04: the plate arrives.
- 0:04–0:27: strip A, about 5.5 s per panel. Panel 3 is held 4 s in declared silence: room tone only, no balloon.
- 0:27–0:30: page turn.
- 0:30–0:53: strip B.
- 0:53–0:60: A and B side by side at the same size. The art is held and the balloons flicker between the two strips.

**SCION prompts checked:**
- `prompts/moins-dun-quart-de-seconde-pour-vivre.md`.
- The newer `prompts/oubapo.md`: one plate under two orders of captions, with a hinge balloon. This gives the A/B comparison close and the rule that both strips use one letterer.
- `prompts/exercices-de-style-animated.md`: a locked exposure sheet with timing kept as a separate branch, and the 288-frame lock at 24 fps. This is used for the per-balloon write-on and swing timing, so that retiming never touches the art.

**Technique SCIONs** from `swarms.json`:
- #17 South Park: repeatable graphic grammar, the core of the strict plate.
- #2 Reiniger: articulated shadow theatre.
- #1 Gilliam and #3 Ernst: cutout and collage.
- #40 physical tabletop capture.
- #41 secondary dynamics.
- #44 multiplane parallax.
- #45 occlusion compositing.
- #32 forward kinematics.
- #47 sound-to-action.
- #38 dynamic pose selection.
- #48 state machines, used for the strict and loose modes.

Moving Image Archive cache searched:
- "frog|toad|pond|lily", "bench|waiting|seated|letter|envelope" and "reading|holding|sitting" (sheets looked at).
- The best seated candidates were an amateur garden-chair film (46cd8d58: two sitters, undated, rights unknown) and *Farmer Miller Goes Into High Gear* (1920, b066405d: hands holding an *opened* letter).
- I tried auto-rotoscoping the 320×240 garden-chair clip. It came out unreadable ink noise, and neither clip gives one figure with an unopened envelope.
- So no direction is archive-footage-led. All three are animation-led. Foraged material comes in where it is the real object: the envelope.

**Foraged (all public domain by date):**
- LoC ppmsca 34859, *Prisoner's letter envelope addressed to Dr. Geo. Brown, Barre, Mass.*, 1865, Liljenquist Family Collection, Library of Congress. https://tile.loc.gov/storage-services/service/pnp/ppmsca/34800/34859v.jpg. It carries an "PRISONER'S LETTER · EXAMINED" hand-stamp, a 3¢ stamp and a manuscript address. It is used in D2.
- Two other 1861–62 envelopes were downloaded and rejected, because their Confederate stamps would read as political imagery: ppmsca 33548 and 33544.
- Total new downloads: about 0.9 MB, in `films/sources/moins-dun-quart-de-seconde-pour-vivre/`. These still need entries in `films/credits/moins-dun-quart-de-seconde-pour-vivre.json` at build time.

Scripts are in `proposals/src/`:
- `hand.py`: brush dabs, and a 26-letter plus punctuation and digit single-stroke hand alphabet made for this film, with per-letter jitter and stroke-order write-on.
- `plate.py`: the one plate.
- `kf1.py`, `kf2.py`, `kf3.py`, `board.py`.

---

## 1 · BRUSH PLATE, WRITTEN BALLOONS (kinetic hand lettering over a frozen ink plate) · `kf-1.png`

- **Beat shown: 0:47.** Strip A is complete above, with its silent panel 3. Strip B panel 4 is being written: "WHY WOULD I / OPEN SOM…". The pen is mid-stroke, and the reader is about to learn whose envelope it is.
- **Material (handmade).**
  - One brush-ink plate drawn in code as real brush strokes, not a filter. Each line is a chain of pressure-varying dabs with tapered ends. It has white masses on a black night ground, fur dashes, wood grain on the bench and broken highlights on the lamp. This matches the reference's pure black and white, its heavy brush contour and its black panel grounds.
  - Balloons are lettered stroke by stroke in the film's own single-stroke capitals.
  - Plate hash `1a37d5ecc393a291`, ×8 identical.
- **Technique and motion:**
  - #17 Repeatable graphic grammar: the plate is published once and pasted unchanged.
  - Kinetic typography written on frame by frame. Each balloon outline is drawn first, on about 6 frames. Then the letters follow in stroke order at a hand's pace, about 9 letters per second, so the pen travel is the animation.
  - The silent panel is a hold with no balloon: the empty black above the head becomes the event.
  - Line boil exists only on the balloon plane: 2-frame lettering re-jitter while writing, then the lettering locks.
  - At the 0:53 comparison, the A and B balloon planes cross-flicker over one unchanged plate.
  - #47 sound-to-action: a pen-scratch track follows the stroke lengths.
- **Risk:**
  - The most faithful to the reference, and the least spectacular. The motion is all lettering, so it depends on the writing and timing being good.
  - The creature's ear crosses the balloon tails. The tails need a final layout pass in which balloons may move but the art may not.

## 2 · LIGHTBOX PUPPET, HINGED BALLOONS (articulated silhouette theatre with a foraged envelope) · `kf-2.png`

- **Beat shown: 0:41,** strip B panel 3. "AND LOOK - STILL SEALED." has just been carried in on its rod. Its right leaf is still turning open on a paper hinge, at 38% foreshortened, and the card swings 11° on its pin. Panel 4 is still empty: the same pose waits for its last line.
- **Material:**
  - Handmade:
    - A scissor-faceted black-card silhouette of the same creature, bench and lamp.
    - Knife-cut holes for the eye, mouth, nostril and fur slits.
    - Brass paper-fastener pins at the neck, shoulders and knee.
    - Four windows of fibrous translucent paper over one warm lamp, with an opaque board between them.
    - Balloons are black cards with the letters knife-cut out, so the words glow.
  - Foraged: the 1865 "PRISONER'S LETTER · EXAMINED" envelope (LoC, PD), cut out and laid in the puppet's hands. The backlight shows its handwriting and stamp. The alibi is literally an examined letter addressed to someone else (Mr Geo. Brown), which pays off "SOMEONE ELSE'S".
- **Technique and motion:**
  - #2 Reiniger silhouette theatre.
  - #32 FK: the puppet is articulated at its pins, but it is pinned in one pose for the whole proof. The four windows are byte-identical (asserted).
  - All motion is on the balloon plane. Each balloon card enters on a wire rod from the top of the frame on a damped pendulum (#41: about 1.2 s settle, 2–3 overshoots, shot on ones). Its hinge leaf then opens over 8 frames, so the line is "unfolded" rather than written.
  - The silent panel in strip A is an empty window: the rod comes down with no card and goes away again.
  - #44: there are two depth planes. The rod's soft penumbra moves with its swing while the puppet stays sharp on the screen.
  - Faint room tone, and a card tap on each arrival.
- **Risk:**
  - Silhouette loses the reference's white-on-black drawing inside the figure. The eye and slits carry the expression and must read at phone size.
  - The hinge is subtle in a still. In motion it is clear, but the half-turned leaf compresses the words ("LOOK" reads "LOX" mid-turn).
  - Backlit-paper texture must stay identical per window in strict mode, so there is no flicker of the lamp.

## 3 · PROOF PRESS AND LETTER STAMPS (top-down stop-motion of a handmade print shop) · `kf-3.png`

- **Beat shown: 0:12,** strip A panel 2. Four impressions of the block are already pulled on one paper strip. A cut-paper balloon has been pasted on panel 2, and "IF I DON'T, / I" has been pressed in letter by letter. The wooden "C" stamp is lifted above its spot, with its shadow thrown down-right, about to press. Its place in the tray below is empty.
- **Material (handmade):**
  - A white-line relief block of the creature: the brush plate cut as a relief, so what was ink is cut away.
  - It is pulled four times through one fixed impression model, with paper tooth, roller starvation, edge squash and gouge chatter. The four prints are the same bytes.
  - A paper strip and a wooden table.
  - A tray of 32 wooden letter stamps, each showing its guide letter on top.
  - Pasted cut-paper balloons with scissor edges and small drop shadows.
  - Letters pressed one rubber stamp at a time, each with its own ink density.
- **Technique and motion:**
  - #40 Physical tabletop capture: rigid per-piece transforms on an overhead copy stand.
  - Stop-motion on twos. The prologue (0:00–0:04) shows the block coming down four times on a registration jig.
  - Then, per panel:
    1. the balloon paper slides in and is pressed flat (3 frames of lift shadow shrinking);
    2. each letter stamp leaves the tray, travels, and drops: a 4-frame lift-and-press, with the shadow offset tied to height, as in #44 depth from shadow;
    3. it lifts and leaves the impression.
  - The silent panel 3 gets a balloon paper with no letters, or none at all (both cuts are tested).
  - #45 occlusion: the stamp's body always covers its own target.
  - Sound: a thunk and a wooden click per letter. That gives a natural rhythm, and the silence in panel 3 becomes audible.
- **Risk:**
  - The palette is warmer and more "object" than the reference's flat photocopied page. It matches the reference's black/white massing and repetition, not its paper.
  - The relief look shares its drawing with D1, so they are related. The difference is medium and motion, not character.
  - The most hand-built of the three: lots of per-letter keyframes, about 160 stamps across both strips.
  - The table's wood grain is procedural and still looks too regular. It needs a real wood scan (PD or CC0 from Commons, which was rate-limited today) or a hand-painted texture.

---

## Recommendation

**Direction 1 (Brush plate, written balloons)** is the spine. It is the most faithful to the reference: pure black and white, brush contour, black grounds, hand lettering inside the panel. It makes the strict proof visible at once, with eight identical plates and the words alone doing the work. The write-on gives real frame-by-frame animation without ever touching the art layer.

From **Direction 3**, take the letter-press rhythm in sound only: give each written letter a soft click so that the silent panel 3 is heard as well as seen.

From **Direction 2**, take one thing: the **foraged 1865 "PRISONER'S LETTER · EXAMINED" envelope**. Cut it, ink it to the plate's black and white, and draw it into the plate as the creature's envelope before the plate is frozen. It gives the alibi strip its payoff ("SOMEONE ELSE'S", addressed to Mr Geo. Brown) without breaking the invariant.

If the user wants the more spectacular animation, choose Direction 2 as a whole. Its rod-and-hinge balloons are the strongest movement of the three, at the cost of the reference's drawn interior.

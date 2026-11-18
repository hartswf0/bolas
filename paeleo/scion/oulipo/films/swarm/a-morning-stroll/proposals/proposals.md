# A Morning Stroll: three proposed directions

**Reference:** `assets/references/orchard3.webp`, the 1959 section.
- A black-and-white ink-line street of brownstones, stoops with iron railings, scalloped trees and parked cars.
- Large flat black masses (the stoop's shadow side) against white paper.
- Heavy vignette and film grain.
- A numbered chicken seen from behind on the sidewalk.

The gallery stills (2009 flat colour, 2059 photoreal with a long cast shadow) set the era ladder.

**Frames.** Each keyframe is 1280x720. The builder is `proposals/kf.py` (deterministic: `python3 kf.py`). The board is `board.jpg`, the reference beside the three keyframes.

## The encounter (frozen for all directions)

**CoreBeat.** A walker on a morning sidewalk stops to watch a chicken climb a brownstone stoop and knock twice on the door with its beak. The door opens and the chicken goes in. The walker goes on. The door is the "unlikely place".

**Protected signatures:**
- **Gesture:** two beak strikes on the door, 0.32 s apart.
- **Sound cue:** "tok . tok", the same rhythm and pitch interval in all three eras. It is wood in 1959, a hollow composite door in 2009, and a synthetic chime that the 2059 door answers in 2059.
- **Watcher:** stops, and turns their head toward the stoop.

**Per-version timing, 15 s each, so the film is about 50 s with title cards:**
- 0–3 s: walk-in.
- ≈3.5 s: the watcher notices, as the chicken mounts the stoop.
- ≈6.0 s: the knock.
- ≈8.5–10 s: entry.
- 10–15 s: the walker goes on.

**Film times of the knock:** 0:06, 0:22 and 0:38.

**Escalation:** in 2059 the door reads the knock rhythm as an access code and slides open (the new environmental affordance). In 1959 someone has to open it.

**Baseline:** the same event timing shown as a plain wide shot, with no technique-specific staging.

**Downloads:** about 2.1 MB in total, in `films/sources/a-morning-stroll/r2/`. All are from the Library of Congress, and every one is marked "No known restrictions on publication".
- **S. `ppmsca.70651`**: *[Detail of stoop showing staircases and decorative handrails]*, July 1959. Angelo Rizzuto, Anthony Angel Collection. LoC item 2020636795. Its year matches the reference's 1959 era exactly.
- **R. `stereo.1s08734`**: *[Portrait of a rooster]*, Schreiber & Sons, Philadelphia, 1870s ("Animal studies from nature"). LoC item 2017651475. PD.
- **O. `2017861981.jpg`**: an OWI photograph (negative OWI-37752-E, c.1943) of travellers waiting at a bus terminal, already in `sources/a-morning-stroll/` from round 1. The photographer is probably Esther Bubley. I did not re-confirm this because LoC rate-limited me, so **record it as unverified**. FSA/OWI, PD (US Gov).
- **Spares:**
  - Highsmith stoops (`highsm.56225` is a terrier atop a Philadelphia stoop; `highsm.56276` is a stoop): Carol M. Highsmith Archive, PD. These are candidates for the 2009 plate.
  - `3c31917`: one-legged rooster, c.1924, PD.
  - `ppmsca.59644`: *Hen & chickens*, poster, 1901, PD.

**Not found.**
- The Moving Image Archive cache has no chicken on a street.
  - "Chicken of Tomorrow" (1948) shows only processing and crowds.
  - Its best street plates are "A Place to Live" (1948, a row-house street, `211e6206`) and "Arteries of New York City" (1941, `ee12b007`), and neither has a stoop close enough to stage on.
- Commons returned HTTP 429 at once, so nothing was searched there.

---

## 1 · Rizzuto Stoop (foraged photograph + cutout puppet; the one archive-led direction)

**Beat and time.** The noticing beat, ≈3.5 s into the 1959 version (0:03.5). The rooster is on the third tread from the top. The watcher stays off-frame bottom-left, and her long morning shadow is laid up the granite treads toward it. This echoes the 2059 reference still's cast shadow.

**Material.**
- **S** is the plate: the real 1959 stoop, its lace iron railing and granite treads, cropped to 16:9 and tone-matched to the reference's high-key b/w.
- **R** is the rooster.
- **O** is the woman in the light coat, used only as her shadow.

**Technique.**
- **#29 GrabCut:** a hand-placed scissor outline of 44 points on the stereo card, refined by GrabCut in a 7 px band.
- **#32 Forward Kinematics:** the cut is split into three pinned pieces (legs, body, head-and-neck). The split pins are visible.
- **#45 Occlusion:** a top-hat filter re-mattes the plate's own balusters in front of the puppet, so the rooster stands *behind* the near railing.
- **The shadow:** GrabCut silhouette, then an affine shear, then a sawtooth row-shift with the tread period, so the shadow breaks over each riser, then blur at 72 % opacity.
- **#44 Multiplane Parallax:** plate, shadow, puppet and railing matte are four planes.
- **#27 Remotion EDL:** the timing fixtures.

**How it moves, frame by frame (12 fps, on twos for the puppet).**
- **Hop cycle:** 6 drawings' worth of joint poses (crouch, lift, airborne, land), climbing one tread per 8 frames.
- **Knock:** the head piece rotates −22° about the neck pin and back, twice, 4 frames apart.
- **Shadow:** it slides 2 px per frame until the walker stops, then holds. Only its head turns, through a re-sheared head piece.
- **Plate:** it has a 1.5 % slow push. The railing matte is recomputed per frame so occlusion stays exact.
- **Eras:**
  - 2009 swaps the plate to a Highsmith stoop.
  - 2059 swaps it to the same stoop under a new technique (still to choose; see risk).

**Risk.**
- This is the archive-led one. It reads as photomontage, not as Orchard's drawn line.
- The rooster's 1870s albumen tone and angle do not match the plate's light. It looks pasted in until we add a contact shadow and a grade (partly done).
- There is a single rooster pose, so turns need other foraged birds (#39 substitution) or the head pivot only.
- The door is out of frame in this crop, so the knock needs a second plate from the top of S.
- The 2009 and 2059 plates are not yet foraged at matching camera height.

## 2 · Pen Number (handmade pen-line drawing with boiling line + kinetic type)

**Beat and time.** The knock, ≈6.0 s into the 1959 version (0:06). This is the defining beat. The chicken has its beak on the black door, with white strike ticks. "TOK TOK" is lettered by hand above the door: seven glyphs, each cut and rotated, the second word larger. A man in a hat with a newspaper turns his head to it in the foreground. Brownstones, a fire escape, a scalloped tree, a lamp, a parked car and a far tenement row make up the street.

**Material.** Fully handmade, with no foraged pixels.
- It is drawn by a seeded pen model: each stroke is resampled, then wobbled by a phase-shifted sine plus noise, with nib width varying along the stroke, drawn at 2x and reduced.
- It has flat grey washes, solid black masses (the door, glazing, the areaway, the coat), stippled stone risers, broken-dash brick coursing, then grain and vignette.
- The composition is my own side elevation of a stoop, not a trace of the reference's one-point street. The chicken is my own hen design, with the reference's **number** idea as a stencil "1".

**Technique.**
- **#7 Foldès Drawn Metamorphosis** and **#38 Dynamic Pose Selection:** an 8-drawing knock cycle from a pose library.
- **#13 / #41 Secondary Dynamics:** the comb and tail lag.
- Kinetic typography for the cue.
- **#17 Repeatable Graphic Grammar:** the same stroke model with era-specific nibs.

**How it moves, frame by frame.**
- **Boiling line:** every stroke is redrawn with a new seed every 2 frames (the `Pen(seed)` argument), as a hand redraw would be.
- **Chicken:** its poses are substituted from the drawn library (hop, hop, crest, strike 1, recoil, strike 2, wait, enter).
- **Letters:** they appear one per frame on the strike frames, scale 1.3→1.0 over 3 frames, then hold rotated.
- **Watcher:** the walk is a 6-drawing cycle that freezes on the "notice" frame. The head is replaced by a turned drawing.
- **Eras:** each one keeps the event score and changes the drawing system.
  - 2009: felt-tip flat colour.
  - 2059: white line on black glow, where the door "reads" the TOK letters as they appear.

**Risk.**
- This is the closest to the reference's medium. It must not drift into a pastiche of Orchard's chicken and design, so keep the hen design and the side-elevation staging.
- The pen model is still somewhat mechanical in the long straight lines. The reference has more confident, variable brush-pen weight.
- The previous build of this film used a similar engraved/cel/glow era ladder (for the station seed). The difference has to be the street and stoop staging and the kinetic-type cue.

## 3 · Lace Door (articulated silhouette theatre, Reiniger method)

**Beat and time.** The entry, ≈9.0 s into the 2059 version (0:41). This is the third version's escalation.
- The door has *slid aside by itself* after the two knocks, and a row of sensor holes above it glows.
- The chicken, as an articulated black card puppet, is lifting one leg over the sill into the brightest paper, the hall light.
- The watcher, a pinned silhouette with a hat and a coffee cup, has stopped mid-stride on the sidewalk under the lamp.

**Material.** Fully handmade on a simulated light table.
- **Black card:** the figures, tree, lamp, stoop, cornice, fire escape, and a lace railing of cut scrolls.
- **Tissue layers for greys:** the far houses at one layer, the house at two.
- **Backlit paper:** a graded glow with fibre noise.
- **A tissue wedge:** light spills down the treads.
- **Split pins:** they catch the light as grey dots at every joint.
- The b/w tonal range and the vignette aim at the reference. The black masses and scalloped tree echo its design.

**Technique.**
- **#2 Reiniger Articulated Shadow Theater:** the main method.
- **#32 FK:** chicken joints at neck, hip and knee, and walker joints at neck, shoulder and hip.
- **#44 Multiplane Parallax:** far tissue, house, card and figure planes, separated at 0.2x, 0.5x, 1x and 1x for the camera drift.
- **#48 State Machines:** the 2059 door (closed → listen → open on the "tok . tok" rhythm, refuse on a wrong rhythm), which makes the affordance testable.
- **#45 Occlusion:** the sill and the door leaf.

**How it moves, frame by frame (12 fps, on ones for the chicken).**
- Each puppet is a set of rigid card pieces rotating about pins, with no deformation. The chicken's head bob is a 4-frame pin rotation, and the leg lift is hip, then knee, then toe.
- The door leaf slides 6 px per frame into the wall over 18 frames. The spill wedge widens with it.
- The sensor dots light one per frame in the knock rhythm.
- **Eras by paper and light, not by drawing:**
  - 1959: warm paper, and the door is a hinged leaf opened by an unseen hand.
  - 2009: a coloured gel layer.
  - 2059: cold paper, with the door answering by itself.
- **Diagnostic render:** the 2059 version in direction-2 pen line with identical timing, which separates era from technique.

**Risk.**
- Silhouettes lose the white chicken that the reference relies on. Its identity has to come from profile alone (comb, tail and beak are strong), and it cannot be seen against the black stoop, only against light. So every chicken beat must be staged against paper or the doorway.
- The 2059 "futurity" rests on small cues (the sliding leaf, the sensor row). It needs one more environmental affordance shown earlier in the version.
- The cut-scroll lace is still simpler than Reiniger's real filigree.

---

## Recommendation

**Build direction 3, Lace Door, as the spine, with direction 2, Pen Number, as the first and second eras and as the diagnostic render.**

Silhouette theatre does what the proof needs most:
- The single gesture (two beak strikes, then the entry) is legible as pure profile in any era.
- Paper, tissue and light change the world without touching the event score.
- The 2059 door-answers-the-knock state machine makes the third version's escalation something the viewer can point to: the door opens without a hand.

Direction 2 is closest to the reference's ink-line look, and its kinetic "TOK TOK" makes the matched sound cue visible as well as audible, so it is the best 1959 opening and the right alternate technique for the style-isolation diagnostic.

Direction 1 is the strongest *foraged* frame: a real 1959 stoop and a real cast shadow. Its rooster, however, is a single pasted pose. Keep its Rizzuto plate and its cast-shadow idea as a possible 2009 photographic-collage era if the user wants an archive voice in the triptych.

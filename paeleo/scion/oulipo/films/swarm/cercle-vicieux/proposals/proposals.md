# Cercle vicieux: three proposed directions

**Reference.** `assets/references/cercle1.webp` is one page of Lécroart's book.
- Six panels in a 2×3 grid, drawn in brush and pen ink. Each figure has a closed contour and the blacks are solid: doors, jackets, wall panels.
- There is no grey. Tone is either solid black or white paper.
- The lettering is hand-drawn capitals in round balloons with tails.
- The framing is mostly medium two-shots. The page grid is the stage, and the camera never leaves it.

**Story and Hard proof.** I kept the current film's station story, the panel IDs and the fixture `A B C D E F G H X H G F E D C B A`: 9 unique panels and 17 occurrences.
- **The hinge** is X: *"The bell can only be rung from behind that door."* It is a single hinge panel, the tall column that opens page 3 after a page turn.
- **The opening panel A** (*"You! Stay right there."*) reads as an accusation the first time. As the last panel it reads as protection: the porter is keeping the visitor away from whoever is behind the door.

**Timing.** Planned for a film of about 60 s:

| span | content |
|---|---|
| 0–2 s | title |
| 2–14 s | page 1: A B C D |
| 15–26 s | page 2: E F G H |
| 26.8–28.2 s | page turn |
| 28.2–31.5 s | hinge X |
| 31.5–43 s | rest of page 3: H G F E |
| 44–58 s | page 4: D C B A; the closing A is at 55–58 s |

**Rule for animating inside panels.** A panel is an immutable artwork ID, and its motion counts as part of that artwork. Both occurrences of a panel therefore play the *same* cycle, forward, frame for frame. Nothing plays reversed, and the second reading changes only through the panel's neighbours. The validator hashes each panel's frame sequence, not just one still.

**Builders.** `kf1.py`, `kf2.py` and `kf3.py`, with shared ink tools in `kf_common.py`. Each is deterministic: run it as `python3 -I kfN.py`. The masks are saved in `films/sources/cercle-vicieux/cutouts/`.

**Downloads.** About 0 MB of new downloads. Everything came from material already on disk: the Moving Image Archive cache and LoC and Commons files already fetched for other films. Decoded frames went to `films/sources/cercle-vicieux/frames/`.

---

## 1 · Union Station cutouts (kf-1.png)

- **The beat.** Page 4 (D C / B A) at **56.0 s**, during the closing A.
- **What changes.** The porter's forearm has swung up from checking his watch. The same cutout gesture now stands between the visitor and the SERVICE door.
- **What the viewer should be able to point to:** "he's blocking the door now, not her."

**Material.** All of it is foraged, except for small handmade pieces.

| item | source | licence | used as |
|---|---|---|---|
| *Conductor checking his time in the telegraphers' office, Union Station* (Jack Delano, 1943), LoC 2017844115 | on disk | public domain, FSA/OWI; LoC: no known restrictions | porter puppet: body and forearm |
| *Red cap at the Union Station*, LoC 2017843923 | on disk | same | panel C |
| *Soldier departing at the Union Station*, LoC 2017843935 | on disk | same | visitor puppet: a man in a light coat, seen from behind |
| *The main waiting room of Union Station at 1 a.m.*, LoC 2017843779 | on disk | same | benches plate for B and D |
| `File:Skeletonkey.png` | Commons | CC0 | the key |

The envelope, the service door, the wall hatching, the panel borders and the lettering are handmade. The lettering uses single-stroke capitals placed glyph by glyph with drift and tilt.

**Technique.**
- **SCIONs:** 1 (Gilliam cutout metamorphosis), 29 (GrabCut extraction), 32 (forward kinematics), 45 (occlusion compositing), 50 (LoC print stage).
- **The cut.** Each figure is extracted with GrabCut and split at real joints: forearm at the elbow, head at the neck, the visitor's arm at the shoulder. Each piece is printed to the reference's tonal range of solid black, a round-dot screen and paper. It gets a scissor-edge ink outline and is pasted into hand-inked panels.
- **How it moves frame by frame.** The puppet is animated on twos (12 poses/s) by rotating pieces about their pins. In A, the forearm goes from −0° to −40° over 10 poses with a two-pose overshoot. In B, the visitor's head turns, done as a substitution between two cut heads. In D, the key slides out of the envelope 6 px per pose. The camera stays on the page and moves between panels as a rostrum push.
- **The page.** The grid never changes. Page turns are a flat slide, so the stage stays the comic page.

**Risk.**
- The photographs are 1943 Chicago, but the reference is a cartoon line. The dot-screen print brings the tone close, but not the drawing hand.
- The visitor is seen only from behind, because no clean frontal PD figure was on disk. The head reads as a pale cone at small size, and a frontal figure needs a new LoC search.
- The porter's forearm rotation is limited by a foreshortened sleeve. A bigger "stop" gesture needs a re-cut, or a second photograph for the arm.

## 2 · Shadow door (kf-2.png)

- **The beat.** Page 3 at **29.0 s**, the hinge X, just after the page turn.
- **What we see.** The service door's frosted pane is lit from the far side, and the blurred shadow of a hand gripping the bell cord falls on it. The bell above is mid-swing, and the porter stands with his back to us, looking up.
- **The point.** This is the only panel where the viewer sees *behind* the door, and the only panel that occurs once.
- **What the viewer should be able to point to:** "someone is on the other side of the glass."

**Material.** All handmade.
- The silhouette puppets are cut as polygons with scissor-jog edges, hinged with paper fasteners at the neck, shoulders, elbows and hips. Lace is punched through them: buttons, a diamond hem, the cap badge, a filigree band on the bell.
- The backlit screen falls off from a hot centre and carries tissue fibre.
- The station arches are a second grey tissue layer on a rear pane.
- The lettering is the same hand lettering as in direction 1.
- There is no foraged image. Foraged sound could come later, such as a Commons PD/CC0 handbell.

**Technique.**
- **SCIONs:** 2 (Reiniger articulated shadow theatre), 32 (FK), 44 (multiplane parallax), 41 (secondary dynamics: the bell and its clapper as a damped pendulum, the cord's slack).
- **How it moves frame by frame.** Each puppet is posed on twos about its pins, the way Reiniger moved her figures under a fixed camera.
- **In X:**
  - The bell swings ±0.28 rad and decays over 1.5 s.
  - The clapper lags behind the bell at 1.6× its angle.
  - The hand-shadow on the pane pulls down twice, blurred because it is on the far side of the glass.
  - The light under the door flickers when the hand moves.
  - The porter's head tilts up over 4 poses.
- **Depth.** The arches pane sits at 0.6× parallax during the page-turn slide.
- **The other panels.** H G F E repeat the cycles that page 2 gave them, with identical frames.

**Risk.**
- Silhouette drops the reference's line and facial comedy. Faces become profiles, and the acting must live in hands and posture.
- The figures here are still blocky: a Reiniger standard needs finer cut profiles and more lace.
- Grey screens also drift from the reference's pure black and white. This can be fixed by keeping the screen near white and the tissue light.

## 3 · Platform 1927, inked (kf-3.png)

- **The beat.** The page turn at **27.6 s**. The leaf of page 2 has passed vertical, and its back shows the faint show-through of E F G H. The hinge column X is uncovered for the first time: the sliding doors and the call-board of *The Electric House*.
- **What the viewer should be able to point to:** "the bell-board is behind the door."

**Material.** All of it is foraged, from the Moving Image Archive cache.

| clip | film | used in | rights |
|---|---|---|---|
| b6e217eb | *Berlin: Symphony of a Great City* (Ruttmann, 1927), platform at dawn, a train arriving | H | PD by date: US 1927 work; Ruttmann died 1941 |
| bb5ffe06 | *The Electric House* (Keaton/Cline, 1922), sliding doors and call-board | X and G | US public domain, pre-1929 |
| 1184d1d4 | *The Playhouse* (Keaton/Cline, 1921), lobby figures | E and F | US public domain, pre-1929 |

- **Licences are not yet confirmed.** The cache has no licence field. All three are pre-1929 US releases, but each needs to be confirmed against a Commons or LoC record before the film ships.
- **Handmade parts:** panel borders, balloons, lettering, the page leaf.

**Technique.**
- **SCIONs:** 28 (mask/rotoscope plate foundry), 44 (multiplane parallax for the leaf), 45 (occlusion: the leaf's shadow on page 3), 43 (collage graph rewriting: the same footage given a new role by its panel ID).
- **How each frame is rotoscoped.** Every archive frame goes through five steps:
  1. It is enlarged and bilateral-smoothed.
  2. Its contours are traced as an ink line (Canny on a blurred image, dilated, specks under 260 px dropped).
  3. The shadows are filled solid.
  4. The mid-tones are screened with dots.
  5. Line and blacks are recomputed for each frame, so the drawing boils like a hand-traced roto.
- **Playback inside the panels.** The panels play their clips at 12 fps. The train in H advances and the doors in G slide.
- **The page turn.** It is a perspective-warped leaf. Its angle runs from 0° to 180° over 1.4 s on an ease-in-out, with the gutter shadow tied to the angle and the show-through switching on past 90°.

**Risk.**
- This is the archive-led direction, and the footage does not hold the story's two characters. The porter and visitor become whoever the clip offers, so the hard proof's "accusation → protection" reading of A depends heavily on lettering.
- The sources are 320×240, so fine detail is invented by the tracer. Faces turn to blots, and *The Playhouse* frames are very dark.
- Rights for the three clips are unconfirmed.
- It is closest to a "filter over footage" of the three directions. The answer to that is that the frames are chosen per panel ID and redrawn, not graded.

---

## Recommendation

**Build direction 2, Shadow door, as the base, and carry direction 1's cutout hand into it.**

- **Direction 2** makes the hinge visible as an image: the hand behind the frosted glass appears once, on the purposeful page turn. Silhouette also keeps the reference's absolute black and white.
- **Its animation** is genuine frame-by-frame puppetry, a fixed camera on posed pinned figures, and every panel cycle can be hashed for the symmetry check.
- **Its main weakness** is the loss of Lécroart's faces and line comedy. To answer that, I would give the porter and visitor one foraged photographic face each, cut as a Gilliam-style head with the same pins as the silhouette body. The cut heads would come from the LoC red cap portrait and a frontal visitor still to be found.
- **Direction 1** is the stronger second choice if the user wants recognisable people and the page as collage.
- **Direction 3** should stay a reference cut only, since its clip rights and its characterless footage both work against the proof.

# 99 Ways to Tell a Story · Template: three proposed directions

**Reference:** `assets/references/madden1.webp`, Madden's Template page.
- Eight panels in three tiers, with white gutters and hand-ruled borders.
- Brush-and-pen black-and-white: large spotted blacks (the doorway, the stair, the fridge interior) and fine contour line.
- Hand-lettered, mixed-case balloons: "What time is it?", "It's 1:15.", "Thanks!" and "What the hell was I looking for, anyway?"

**Current site film:** a clean vector line restyle of the station seed. All three directions below replace that costume with real material, and they keep the page grammar (panels, gutters, balloons, lettering) as the stage.

**Frames.** Each keyframe is 1280x720. They are built by `proposals/kf.py`, which is deterministic (`python3 -I kf.py`). The board is `board.jpg`: the reference plus the three keyframes, each labelled.

## Frozen incident (the same for all three directions)

The station seed, as the site film already uses it:

| Event | What happens | Time in a ~60 s film |
|---|---|---|
| E1 | The clerk leaves the desk (a note about the service key) | 0:04 |
| E2 | "What time is it?" comes from the platform, out of view | 0:09 |
| E3 | He answers "Ten past four!" | 0:14 |
| E4 | He reaches the key cupboard | 0:20 |
| E5 | He forgets why ("What the hell was I looking for, anyway?"), and the key stays on its hook | 0:24 |

After that:
- 0:30: a page hold (the reading).
- 0:34: the compressed retelling (two panels).
- 0:46: the new point of view (from the platform bench, so E1 is out of view).
- 0:56: the ledger.

Each direction shows a different central beat, so the three frames also cover the event graph between them.

**Downloads:** 2.3 MB of the ~40 MB budget, in `films/sources/99-ways-template/`.

**From the Library of Congress** (each item JSON was read for its rights statement):
- **FSA/OWI photographs**, "No known restrictions on publication":
  - `8b16710v`: Arthur Rothstein, *Railroad station agent. Randolph, Vermont*, 1937, LoC 2017776093.
  - Spares: Wolcott `8c11760v` (2017802673) and `8c11830v` (2017802742); Bubley `8d33077v` (2017861708) and `8d33109v` (2017861739).
- **The paper**: `blank.jpg`, Nels Astner, *[Unidentified Production: Sketch no. 27, Blank Sheet of Paper]*, 1934. Federal Theatre Project Collection, LoC musftpsets.200218222. LoC states it knows of no copyright and treats the material as US Government work.
  - It is a real 1934 sheet with tape on its edges, and it is the page ground of all three frames.
  - Rights assessment is formally "your responsibility", so treat it as PD-USGov and record that wording in the credits.

**From the Moving Image Archive cache** (local clips, no download):
- `3b9d2889`: *Two Pay Days (Part I)*, 1927, a clerk at his ledger. Its source time is 187.3 s.
- `bb5ffe06`: *The Electric House* (Keaton), 1922, panelled cupboard doors that open onto pigeonholes.
- Both are US releases from before 1929, so they are public domain by date.
- The cache index has no licence field, so the PD claim rests on the year. A second check against the archive page is still needed.

**Not usable or not found:**
- The cache has no "man gets up and walks to a cupboard" shot.
- *Bookkeeping and You* (1947) has a wristwatch close-up that would be ideal for "Ten past four", but its rights are unverified, so it is not used.
- Commons returned HTTP 429 to generator searches, so no Commons paper scan was used.

---

## 1 · Brush-Ink Rotoscope (`kf-1.png`)

**Beat and time.** E2, the question, at **0:09**. The tier has three panels:
- **Wide panel:** the clerk lifts his head.
- **Inset above:** the next drawing, a close-up of the head turning.
- **Inset below:** the key cupboard, closed and waiting, with KEYS lettered on it.

The "What time is it?" balloon has its tail run out of the panel and across the gutter, so the voice comes from another room.

**Material.**
- *Two Pay Days* (1927): frames at 0.25 s and 0.5 s of the clip.
- *The Electric House* (1922): a frame at 1.0 s.
- The 1934 LoC paper as the page.
- All of them are PD.

**Technique.** This is Fleischer-style rotoscope, done as real tracing rather than a filter. Each archive frame is re-drawn as ink in three passes:
1. **Spotted blacks:** tone regions are cut as simplified polygons and filled solid.
2. **Contour lines:** contours are re-drawn as tapered, tremor-wobbled brush strokes, with a fine pen pass in the lights for the glasses, knuckles and paper.
3. **Hatching:** the mid-greys get ruled hatching.

SCIONs:
- **#38 Dynamic Pose Selection** (drawing library): pick the frames worth tracing.
- **#7 Foldès** drawn metamorphosis: in-betweens.
- **#45 Occlusion** for the balloons.

**How it moves.** The film runs at 12 fps on twos.
- Every traced frame is a new drawing, so the line boils naturally, as hand rotoscope does. Each drawing gets its own stroke seed, and the seed is held for two frames.
- The head-up gesture is the real 1927 performance, traced drawing by drawing.
- The clerk then rises and leaves (E1). The 1927 reel has no rise, so the swarm needs a handmade substitution here: about 8 drawings interpolated by #7.
- The cupboard opening (E4) is traced from Keaton's doors swinging onto pigeonholes, at source 5–7 s.
- The panels are fixed. The balloons are lettered in stroke by stroke: Hershey single-stroke pen glyphs, set letter by letter with jitter.

**Risk.**
- The two plates come from two different men and rooms. They may read as two places unless the cupboard is re-staged in the same wood panelling, which the 1927 office has.
- Thresholds have to be tuned per shot. At 320x240 the faces are drawn from very few source pixels.
- The method is still algorithmic tracing. It looks like ink, but no human hand drew it, so it can drift toward "filter" if the hatching runs everywhere. Hatching is already cut back.
- The lettering is Hershey Simplex, not a real hand alphabet.

## 2 · Photo-Fumetti Cutout (`kf-2.png`)

**Beat and time.** E5, forgetting, at **0:24**. There are two panels:
- **Narrow panel:** the TICKET OFFICE window. "Thanks!" comes back from the platform, like Madden's own "Thanks!" panel.
- **Wide panel:** the cupboard of the same office. Its door is swung open on a paper hinge onto shelves of tickets. The clerk stands before it, pencil to his chin, under "What the hell was I looking for, anyway?"

**Material.** All of it comes from one Rothstein 1937 FSA photograph (PD, LoC 2017776093):
- The window, the cupboard, the ticket rack used as the cupboard's contents, and the clerk himself.
- He is cut out of his desk (GrabCut), and his place at the desk is filled from the surrounding office (inpaint), so **the desk is really left empty**.

Wolcott's and Bubley's FSA agents are on hand for the platform voice and the bench point of view. The 1934 sheet is the page.

**Technique.** Gilliam-style articulated photo cutout, in a fumetti page.
- **#29 GrabCut** extraction.
- **#1 Gilliam** cutout with a white scissor margin and a cast shadow.
- **#32 Forward Kinematics:** the head is a separate piece hinged at the collar, and the door is hinged on its jamb with perspective foreshortening.
- **#45 Occlusion:** the cut-paper balloons cast shadows.
- **#44 Multiplane** for the pan across the tier.

**How it moves.** The film runs at 12 fps on twos, with paper jitter on each piece.
- **E1:** the clerk piece slides out of the desk photograph, and the inpainted empty chair is revealed.
- **Walk to the cupboard:** he crosses the gutter as a sliding, bobbing cutout, in true Gilliam stepping: the torso translates while the head bobs on its hinge.
- **E4:** the door piece swings in 5 foreshortened stages.
- **E5:** the head tilts back in 3 steps to look up at the shelves. The pencil-arm, a separate piece, rises to the chin.
- **Balloons:** they drop in as paper with one bounce. The "Thanks!" tail points out through the ticket window.

**Risk.**
- This is the most archive-led direction. It may feel like collage rather than drawing, and it departs most from Madden's pure ink line.
- Photographic grey has to be pushed toward high-key black and white without looking filtered.
- The seated source pose limits him to waist-up framing, which is legitimate comics cropping. A full walk across panels needs either a standing FSA figure or Gilliam-style sliding (no legs).
- The inpainted desk needs a check up close.

## 3 · Cut-Paper Shadow Page (`kf-3.png`)

**Beat and time.** E3, the answer, at **0:14**. There are three windows cut in one black card:
- **Left:** the empty desk, the lamp, the pushed-back chair, and the office clock at ten past four. "What time is it?" enters from off-panel left, from the platform doorway.
- **Middle:** the clerk, mid-stride, his head turned back with his mouth cut open: "Ten past four!"
- **Right:** the key cupboard, with the key on its hook behind the fretwork.

The clerk **straddles the gutter**: his torso passes behind the card, and his forward foot appears in the next panel.

**Material.**
- **Handmade:** a Reiniger hinged silhouette puppet (head, torso, thighs, shins, feet, upper arms, forearms and hands, all as faceted scissor-cut card with rivet holes) and the set pieces.
- **Foraged:** the 1934 LoC sheet, backlit as the light-table screen. It is the only foraged item.

**Technique.**
- **#2 Lotte Reiniger** articulated shadow theatre.
- **#32 FK** puppet rig from the hip.
- **#44 Multiplane:** the far layer (doorway, window, clock) is tissue further from the glass, so it is grey and soft.
- **#41 Secondary Dynamics:** coat-tail and toe lift, with a soft halo where the card lifts off the glass.
- **#48 State Machines** for the puppet's walk, turn and halt states.
- The page grid is a black card mask laid over **one continuous stage**, so the panels are windows onto a single space.

**How it moves.** The film runs at 12 fps, and each pose is a real FK key, as in stop-motion of a real card.
- **The walk:** an 8-pose cycle carries the puppet from desk to cupboard behind the card. It disappears into the gutters and reappears in the next window, so the comic's panel-to-panel closure becomes literal continuous motion.
- **E2:** the head pivots back on its rivet.
- **E3:** the mouth notch opens in 2 drawings while the balloon is pinned on.
- **E4:** the cupboard door swings.
- **E5:** the hand reaches toward the hook, stops, and drops.
- **Light:** the backlight breathes slightly, as a real lamp under paper does.

**Risk.**
- The silhouette gives up Madden's interior line, so faces and expressions must be carried by profile and gesture alone. The "forgot" beat needs a very clear stopped hand and a dropped head.
- Black gutters invert the reference's white gutters. A variant could use front-lit white card.
- The puppet is drawn by code as cut polygons, not cut from physical paper.

---

## SCION prompts this film needs, not yet in `swarms.json`

These came up while building the frames. They are candidates for new technique SCIONs:
- **Panel-Gutter Continuity (comics closure as camera).** A continuous stage seen through a page mask. It would carry rules for when a body may be hidden by a gutter, how long a gutter may "hold" an action, and balloon-tail routing across gutters.
- **Hand Lettering and Balloon Placement.** Reading order, tail aim at the speaker's mouth or at an off-panel source, letter-by-letter reveal timed to the sound. This would replace the Hershey stand-in with a foraged PD lettering alphabet.
- **Line Boil and Drawing Hold.** How many frames to hold each traced drawing, stroke-seed reuse, and boil amplitude versus readability, for rotoscope on twos.
- **Fumetti Page Builder.** Photo-comic page grammar: crop to the beat, tone match across plates from different photographers, and a provenance ledger per panel. This sits between #50 LoC and #1 Gilliam.

## Recommendation

**Direction 1, Brush-Ink Rotoscope, as the main body. Direction 3's continuous-stage-behind-the-gutters as the move for the compressed retelling.**
- Direction 1 is closest to the reference's medium: black brush masses, fine contour, hatching and lettered balloons on a real sheet.
- It is genuinely frame-by-frame: every frame is a new traced drawing of a real 1927 performance.
- It answers the user's note directly. It goes beyond the clean vector restyle with ink drawn from real footage, and the animation happens inside the fixed panels.
- Its main gap is the rise from the desk, which needs 6–10 interpolated drawings.
- Direction 3's mask trick makes a strong second operator for the derivative pages. The page card slides while one figure walks under it, which keeps the beat comparison legible.
- Direction 2 is the strongest single image for E5, and the most "real". Keep it in reserve as the new-point-of-view derivative (the platform's photograph view), not as the baseline.

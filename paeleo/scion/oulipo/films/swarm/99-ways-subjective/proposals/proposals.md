# 99 Ways to Tell a Story · Subjective: three directions

**Stage.** The comic page stays the stage. In all three directions a 6-panel page (3 over 3, 16:9) is the frame and the animation happens inside the panels and across the gutters.

**Frozen event sheet** (shared by all three): E1 the hands are busy at work (typing or typesetting) and the caption says the errand ("Out of milk again."). E2 the errand is written down. E3 **unseen interruption**: "What time is it?" comes from offscreen, and the balloon's tail leaves the panel. E4 **head or wrist turn**: the time-piece enters the picture only after the turn, and the protagonist answers. E5 the offscreen voice says "Thanks!" while the hand opens the cupboard or refrigerator. E6 **failed outcome**: the hand hangs in front of the shelves. "What was I looking for, anyway?!"

**Comparison baseline.** The current site film (a clean black-and-white line restyle of the station/office incident) and Madden's Template page. **Success test:** a viewer can point to (a) the balloon tail exiting the frame before anyone is seen, (b) the time-piece absent before the turn and present after it, and (c) the empty hand at the end.

**Planned film timing (about 60 s):** E1 0:00–0:08 · E2 0:08–0:14 · E3 0:14–0:20 · E4 turn 0:20–0:30 · E5 0:30–0:42 · E6 0:42–0:54 · then the objective page shown beside the subjective one, 0:54–0:60.

SCION prompts checked: `prompts/99-ways-subjective.md`, the newer `prompts/oubapo.md` (the comics workshop prompt with a nine-panel route and hinge caption, which feeds the page grammar and caption order) and `prompts/exercices-de-style-animated.md` (exposure sheet, a 288-frame lock, and timing and framing kept as separate branches, used for the per-panel exposure sheets below). From `swarms.json`: #2 Reiniger, #3 Ernst collage, #29 GrabCut, #32 FK, #33 IK, #38 Dynamic pose selection, #39 Multiview drawing substitution, #40 Physical tabletop capture, #44 Multiplane parallax, #45 Occlusion compositing.

---

## 1 · INKED RUSHES (rotoscope, animation-led) · `kf-1.png`

- **Beat shown:** E4 at **0:26**, after the wrist turn. The watch has rotated into view and the answer balloon has arrived. Panel 3's offscreen "What time is it?" is still held above it.
- **Material (foraged).** Every panel is traced from real footage.
  - P1: *Learning to Set Type* (1959), hands at a composing stick (Moving Image Archive cache, clip aaf17c56).
  - P2: *Singing Wires* (1951), a hand with a pencil over a notebook (b6100d97).
  - P3 and P5: *The Electric House* (Keaton, 1922, PD-US by date), a panelled door and the cupboard opening (bb5ffe06).
  - P4: *Bookkeeping and You* (1947), a wrist that turns to show a wristwatch (af625567, frames 014→017).
  - P6: NARA 540882, "Mrs. E. R. Kunz … at the electric refrigerator" (Russell Lee, 1946, **Public domain**, Wikimedia Commons). The reaching arm becomes "my" arm.
  - The watch dial is a handmade inked substitution, so 1:15 can be read.
- **Technique:**
  - Rotoscope done frame by frame. Each source frame (12 fps, on twos) is turned into ink: solid blacks below a luminance threshold, Canny contours thickened into a brush line, and two-direction hatching in the mid-tones. The hatch phase is re-seeded each frame so the line "boils" the way hand-inked rushes do.
  - #39 Multiview drawing substitution: the hand-drawn dial replaces the photographed one during the wrist turn, in three drawings (edge-on, ¾, face).
  - #38 Dynamic pose selection: the source sub-ranges that read best as POV are picked per panel.
  - Only the active panel moves. Earlier panels freeze on their last drawing, the way a page fills as you read it.
  - The balloon tail of E3 stays outside the frame. Its murmur is panned left.
- **Risk:**
  - Moving Image Archive titles still need a title-by-title PD check (1947, 1951 and 1959 educational films are probably PD for non-renewal, but this is not verified).
  - Rotoscoped 320×240 sources go blotchy where the source has no edges. P3 and P6 are still hard to read and need hand clean-up (manual mattes and redrawn contours).
  - Lettering is a typeface, not hand lettering.

## 2 · PAPER HANDS (backlit cut-paper puppets, animation-led, handmade) · `kf-2.png`

- **Beat shown:** E3→E4 at **0:24**, the head turn. In P3 the offscreen question has arrived on a black rod pushed in from above the panel: the voice is literally a card held in from outside the frame. In P4 the kitchen strip has been pulled left (its pull-tab sticks out into the gutter), and the wall clock has slid in at the right. It is absent in every earlier frame.
- **Material (handmade).** The page is a lightbox: fibrous translucent paper in each panel, an opaque board in the gutters. Everything is cut-paper silhouette with scissor-faceted edges:
  - a typewriter with punched keys
  - a pinned MILK note
  - the stair and banister
  - window, kettle and wall clock (translucent dial inlay)
  - the refrigerator and its shelves
  - **articulated hand puppets** with forearm, palm, two-segment fingers and thumb, joined at brass pins
  - card balloons on rods
  - No foraged pixels.
- **Technique:**
  - #2 Reiniger articulated shadow theatre: silhouette only, no internal texture.
  - #32 FK chains for each hand. Joint angles are keyed on an exposure sheet and shot on ones for the reach, on twos for the holds.
  - #33 IK pins: fingertips stay on the keys, the pencil or the handle.
  - #40 Tabletop paper capture logic: per-piece rigid transforms with timestamps.
  - #44 Two depth planes: pieces against the screen are sharp, hands nearer the lamp are soft and throw a penumbra. The shadow offset breathes as a hand lifts.
  - The head turn is a physical **panorama strip drawn through the panel window**, with a constant-velocity pull and a 2-frame ease. Pieces on the strip move together, and the clock enters as the strip passes the frame edge.
  - Rod balloons wobble on a damped spring (#41).
- **Risk:**
  - The hands are the whole performance. The current pieces read as gloves at small sizes, and P1 and P5 need cleaner finger silhouettes and more pose drawings.
  - It is warmer and softer than Madden's pen line. It matches his black/white massing, not his line.
  - There is a lot of hand-built rigging per panel.

## 3 · DEEP PAGE (photo-collage multiplane, the one archive-led direction) · `kf-3.png`

- **Beat shown:** E4 at **0:23**, mid-yaw. The camera eye is swinging right from the doorway (where the voice came from) to the papered wall. The far plane is speed-smeared. The clock, cut from film, is hung on the wall plane and moves at a different parallax rate, and the dark door jamb (near plane) has just whipped out of frame.
- **Material (foraged):**
  - NARA 540800 and 540882 (Russell Lee, 1946, **Public domain**, Commons): the doorway, the papered wall, the refrigerator interior and the reaching arm.
  - *ALASKAN EARTHQUAKE* (1966, Moving Image Archive cache, adfad259): the wall clock, cut as an ellipse. It is stopped at about twenty to seven, so the answer balloon says "Twenty to seven!"
  - Clips aaf17c56, b6100d97 and bb5ffe06 as in direction 1, kept photographic.
  - Handmade: the page plane with its windows cut out, the inked borders, the balloons and the caption.
- **Technique:**
  - #3 / #29 cutouts (GrabCut and elliptical mattes).
  - #44 multiplane: far wall ×1.0, clock ×1.35, jamb ×2.6, with a smear in proportion to each plane's speed.
  - #45 occlusion DAG: page in front of the jamb, the jamb in front of the clock, the clock on the wall. A contact shadow ties the clock to the wall.
  - The page itself is the nearest plane and throws a bevel shadow into each window.
  - Inside the panels the footage plays at its own rate. Across panels, the yaw is continuous: P3's last frame and P4's first share one camera pose.
- **Risk:**
  - The 1966 clock clip's licence is not verified (it may be a US-government production). The fallback is a PD clock photo from Commons, which was rate-limited during this stage.
  - It is the direction closest to an archive edit and the furthest from Madden's ink.
  - The collage seam in the far plane is visible.

---

## Recommendation

**Build 1 · INKED RUSHES, and take its time-piece turn from 2.** It is closest to the reference's medium, tonal range and framing: brush-black solids, white page, hands from below, balloons breaking the frame. The motion is genuinely frame by frame. Every drawing comes from a real gesture, and the boiling line makes it plainly drawn rather than filtered. The wrist turn in *Bookkeeping and You* already does the proof's "object enters only after a turn" in one real gesture.

Borrow from PAPER HANDS the visible mechanism for the offscreen voice: the balloon enters on its tail from beyond the gutter before anything else in the panel moves.

Before the swarm build:

- clean P3 and P6 by hand (redrawn contours over the rotoscope)
- hand-letter the balloons
- confirm the PD status of the three educational films
- log the credits in `films/credits/99-ways-subjective.json`

Build sources for these keyframes are in `proposals/src/`. The scripts expect the frames that were extracted into the session scratchpad. Re-extract them with `ffmpeg -i <clip> -vf fps=4` from the cache paths named above.

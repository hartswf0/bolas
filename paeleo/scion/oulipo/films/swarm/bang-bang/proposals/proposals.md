# Bang Bang: three proposed directions

**Reference.** `assets/references/bang.webp` is page 2 of the Jabely/Queneau dossier (Drouot / Aguttes).
- Black felt pen on cream paper.
- Three ruled panels are stacked in the left column. Each has an inked punch dot at its top left.
- Queneau's commentary runs in a loose hand down the right column, one paragraph per panel. It uses A/B/C/D part labels, an arrow and a struck-out word.
- The ink of the facing page shows faintly through the paper.
- The tonal range is two values only: ink and paper.

**Defining beat.** It is taken from the Hard proof, a 25–35 s animatic, here planned at 30 s.
- **The attempts:**
  - **0–8 s:** the paper wing.
  - **8–16 s:** the rubber-band rotor.
  - **16–30 s:** the glide.
- **The failure as a board sequence, 18–27.5 s:**
  - **BB-07, 18.0–21.0 s:** run-up.
  - **BB-08, 21.0–24.0 s:** nose up 35°, the stall.
  - **BB-09, 24.0–27.5 s:** fall. "Krach" lands at 25.2 s.
- **First readable failure frame:** BB-08 at about 22 s, when the nose is above the horizon and forward motion stops.
- **The narrator's reframe.** The bird has the ability the man is trying to build. It reads the nose-up pitch as a landing flare ("Moi aussi je lève le nez : c'est pour me poser"), so in its account the crash is a too-quick landing, not a failure.
- **Baseline.** The same boards with the narration of a human reporter, who calls it a failure.

All three keyframes show BB-08 or the BB-08/09 join.

**Builder.** `proposals/kf.py` (with `proposals/pen.py`) builds all three frames and the board. It is deterministic.
```
python3 -I films/swarm/bang-bang/proposals/kf.py films/sources/bang-bang films/swarm/bang-bang/proposals assets/references/bang.webp 123
```
- **Pen toolkit.** `pen.py` holds the handmade pen toolkit:
  - Jittered, pressure-varied ink strokes (Catmull-Rom curves, hatching).
  - Cream paper.
  - A hand built from OpenCV's single-stroke Hershey script. Each word is re-set with its own slant, size, baseline drift and a small smooth displacement, then inked with a slanted felt-tip nib. Accents are drawn as separate strokes.
- **What the hand is not.** It is not a copy of Queneau's hand, and none of the drawings are traced from the reference.

**Foraged material.** About 0.6 MB of new downloads (budget ~40 MB), all in `films/sources/bang-bang/`:

| id | item | source | licence | used in |
|---|---|---|---|---|
| CROW | *Corvus scapulatus (Brehms Tierleben)*, Friedrich Specht, 1911, 960 px thumbnail | Commons `File:Corvus_scapulatus_(Brehms_Tierleben).png` | **Public domain** (extmetadata) | kf-2 (new download) |
| LIL-START | *PSM V46 D647 Lilienthal flying apparatus the start* (Popular Science Monthly, 1894–95) | Commons | **Public domain** | kf-2 (already in `credits/bang-bang.json`) |
| PENAUD | *Pénaud's flying models* (plate, 1875) | Commons | **Public domain** | kf-2 (already in credits) |
| DIVE | *Century of Progress Exposition: Wings of a Century* (1933). Clip `55c605ed`, 29.7 s, 320×240, silent; frames at 9.75 / 13.25 / 14.75 / 20.0 s | Moving Image Archive local cache, [page](https://www.movingimagearchive.com/sources/century-of-progress-exposition-wings-of-a-century-95835f19?clip=55c605ed-9ddd-563f-89b4-acf69aaed8f6) | **Unverified.** It is a 1933 US exposition film, probably PD through non-renewal, but the cache has no licence field. Confirm on the archive page before the build. | kf-3 (four frames, about 0.2 MB of PNG) |

**Searched and not used.**
- **Moving Image Archive cache.** I searched aviation, glider, flying machine, bird, pigeon, gull and wing.
  - The cache has no early glider or ornithopter footage. The hit "Inventor's homemade flying machine collapsing on takeoff" is a 1931 amusement ride.
  - The bird hits are 2005 refuge flocks, in colour. They could serve as sound or flock texture only.
- ***F-42 First Flying Machines*** (San Diego Air & Space Museum, Commons, **Public domain**, 86 s, 23 MB). This is real early-aviation failure footage and the better archive source for direction 3. Commons answered HTTP 429 on every attempt over about 6 minutes, so I could not download it. It is the first fetch for the build if direction 3 is chosen.

---

## 1 · Le Carnet de l'oiseau (handmade pen storyboard, drawn frame by frame): **recommended**

**Beat and time.**
- **The moment shown.** The keyframe stops at **≈24.6 s**:
  - BB-07 and BB-08 are fully drawn.
  - BB-09 is still being drawn. Its last strokes, the inventor's lower wing and a leg, are not yet down.
- **The voice column at that moment:**
  - It is writing its sixth line, "Donc il se pose. Très bien, un peu vite…", and the write-on has stopped at "un".
  - "monter" is already struck out and replaced by "s'arrêter". The struck word is the narrator correcting the human reading of the mechanism.
- **The witness:**
  - In BB-07 it sits on the chimney.
  - In BB-08 it flies level beside the stalled inventor, which shows that it can do what he cannot.
  - In BB-09 it stands on the flowerbed.
- **Parts list.** A and B label the wing and the 35° nose, as Queneau labels his parts.

**Material.**
- **All handmade, built for this film:**
  - Pen strokes on cream paper.
  - The inventor, "Monsieur Pique-Vent", is fictional: a bowler hat, a moustache, and two ribbed paper wings strapped to his arms.
  - A pigeon in perched and flying poses.
  - Roof, chimney, tiles and flowerbed.
  - The hand-lettered commentary.
  - Graphite timing notes in the margin, which carry the board fixture: BB-id and frame range.
  - A mirrored show-through of the facing page, at 4.5 % density.
- **Foraged:** nothing in the frame.
- **Sound:** the pigeon coos already in `credits/bang-bang.json` (*Pigeons at NTR Trust Bhavan*, CC BY-SA 4.0) and a pen-scratch room tone.

**Technique SCIONs and how it moves.**
- **#7 Foldès, Drawn Metamorphosis**, and **#38 Dynamic Pose Selection.**
  - Each board is a run of separately drawn poses on 2s (12 drawings/s): BB-07 has 6 run poses, BB-08 has 6 pitch-up poses from 5° to 35°, and BB-09 has 8 fall poses.
  - `pen.Ink` re-jitters every stroke on every drawing, so the line boils the way a redrawn line does. It is never one drawing being moved.
- **#32 Forward Kinematics.**
  - The inventor's pose is set as joint angles: body pitch, wing lift, legs.
  - Each drawing is inked from those angles, so the 35° on the page is the 35° in the drawing.
- **#47 Sound-to-Action.**
  - Commentary writes on letter by letter with the `upto` parameter, about 14 characters/s.
  - Each line is anchored to its board. The pen reaches "Krach!" on the frame the inventor's head meets the flowerbed (25.2 s), and the FX thump lands on that frame.
  - The strike-through of "monter" happens at 22.0 s, the first readable failure frame.
- **Camera.**
  - A slow push from the full page into the active board, and back out.
  - A pin-dot wipe from panel to panel.
  - The page turns at 16 s from page 6 (the rotor) to page 7.

**Risk.**
- **Closeness to the reference.** This direction sits closest to the reference, so it must avoid looking like a pastiche of Queneau's page. Mitigations:
  - The hand is plainly Hershey-derived, not an imitated Queneau hand.
  - The figures are my own.
  - The board fixture lives in the graphite margin.
- **Small panels.** At 1280×720 the stacked panels are about 370×200, so the stall needs the push-in to read.
- **The hand looks set.** The Hershey hand is more even than a real felt pen. A second nib pass with ink pooling at stroke ends would help.
- **Existing film.** The current `films/bang-bang.py` is already a pencil animatic. This direction has to beat it on two points: drawing substitution instead of one moved drawing, and a split voice/image page instead of captions under a frame.

---

## 2 · Planche gravée (articulated cut-paper puppets from PD engravings)

**Beat and time.**
- **The moment shown.** **BB-08, ≈22.5 s**, the stall.
  - Lilienthal's glider and its pilot, cut from the 1894 engraving, pitch nose-up 32° above a torn-card ground.
  - The legs swing forward on their own split pin.
  - The earlier attempts lie on the ground: Pénaud's rubber-band hélicoptère (attempt 2, its band snapped), and Pénaud's aéroplane nose-down in the turf.
- **The witness.** Specht's crow stands on the wrecked rotor. Its head is pinned at the neck and tipped up 58° to watch.
- **The voice.** A torn slip pinned to the board reads "Il lève le nez. Moi aussi, quand je veux m'arrêter."
- **Fiction.** The scene is visibly fictional: real engraved machines, recombined into one invented afternoon.

**Material.**
- **Foraged:** LIL-START, PENAUD and CROW (all public domain, Commons; table above).
- **Cutting:**
  - The engravings are cut out with a line-art scissor mask (ink dilation, closing, small holes filled, a wobbled scissor edge).
  - The crow is cut with GrabCut, seeded by hand: its white collar and head are forced to foreground, and the stones under its feet to background.
  - The engraving ink is printed onto cream card, so the collage keeps the reference's two-value range.
- **Handmade:**
  - The torn ground strip and the card gable with pen tiles.
  - The storyboard frame and its punch dot.
  - The handwritten slip and the brass split pins.
  - The cast shadows. The flying piece's shadow is offset 26/40 px, the grounded pieces' 5/6 px, which reads as height above the card.

**Technique SCIONs and how it moves.**
- **#1 Gilliam, Comic Cutout Metamorphosis**, and **#43 Collage Graph Rewriting:** the machines are real engravings re-assembled into one fictional event.
- **#2 Reiniger, Articulated Theater**, and **#32 Forward Kinematics.**
  - The puppets have three pivot trees: glider to hip pin to legs, crow body to neck pin to head, and rotor blades on the hélicoptère's shaft.
  - They are animated on 2s with eased angles:
    - The glider pitches from -8° to -32° over 21–23 s and then stalls.
    - From 23.2 s it slides tail-first, and the legs counter-swing ±25°, driven by **#41 Secondary Dynamics** (a damped spring on the hip).
    - The crow's head steps through 4 held angles, so it tracks the pilot in birdlike jerks rather than smooth turns.
- **#29 GrabCut**: cutout extraction.
- **#44 Multiplane Parallax.**
  - There are three card planes: ground, gable, sky card.
  - The flying piece has a growing shadow offset. The shadow closes as the glider falls and meets the glider at impact, and that contact frame is the "Krach".
- **#47 Sound-to-Action:** each slip drops in with a paper-flap sound on the frame its line begins.

**Risk.**
- **Real names.** Lilienthal and Pénaud were real people. The proof asks for a *fictional* inventor, so the film must:
  - say nothing that names them, or
  - keep the card visibly a montage: the slip says "Monsieur Pique-Vent", and the credits name the engravings.
- **Scale and style.** Scale and engraving style differ between pieces: Specht's crow is dense wood engraving, the PSM glider is open line. Printing both on the same cream card helps but does not fully unify them.
- **The stall.** It must read from silhouette alone at 22 s, and the engraving's own perspective (the glider seen three-quarter) weakens it. A cleaner side-view glider engraving would help, for example the *PSM* Lilienthal soaring plates, which I have not yet foraged.

---

## 3 · Le Plongeon (archive-led: the 1933 high dive, rotoscoped pen wings)

**Beat and time.**
- **The moment shown.** **BB-08, ≈22 s.**
  - A real 1933 swallow dive from the exposition tower is held at source 13.25 s, the instant the diver is level against the clouds.
  - It is shown as a large mounted print. The bird has inked onto it:
    - A: a pair of scalloped paper wings on his arms.
    - B: the dashed, level glide "he hopes for".
    - C: the solid arc down "that I know".
  - The bird draws itself sitting on the tower top.
- **The board sequence.** Below the print, three small prints run leap (9.8 s) → nose drops (14.8 s) → splash (20.0 s).
- **The voice.** The right column carries the bird's reading: "Il ouvre les bras pour planer. C'est juste ; mais l'air ne le porte pas, alors il choisit l'eau. Raisonnable. … Plouf."

**Material.**
- **Foraged:** DIVE (Moving Image Archive cache, licence to confirm), four frames.
- **Handmade:**
  - The print mounts (corners, border, warm silver tone).
  - The pen wings, paths and labels.
  - The commentary and the drawn bird.
- **If F-42 can be fetched:** a real glider-crash shot from *First Flying Machines* (PD) replaces or follows the dive as attempt 3.

**Technique SCIONs and how it moves.**
- **#28 Mask and Performance Plate**, with step-printing.
  - The clip runs inside the big print, step-printed at 8 fps from 9.0 to 15.5 s of source. That maps to 21–24 s of film, so the leap and level hold are slowed.
  - The print then cuts to the splash at 24.0 s.
- **Rotoscope**, with **#46 Registration** and **#33 IK contact.**
  - The diver's silhouette is tracked per frame: the darkest blob in the sky, which the measurement put at 173–233 × 76–88 px at 13.25 s.
  - The paper wing is re-inked on every frame, rooted at the tracked shoulder, with spar angle following the arm.
  - The wing and the B/C paths draw on as the diver levels out.
  - When the body pitches down, the wing is left behind in mid-air and flutters down on its own (**#41**). This is the bird's joke: the paper wing glides, the man does not.
- **#47 Sound-to-Action:** the line "alors il choisit l'eau" finishes writing on the splash frame, and there is a real water sound under "Plouf".

**Risk.**
- **Licence (biggest risk).** DIVE's licence is unverified. If it is not PD, the direction falls back to F-42, which is still blocked by Commons rate limits.
- **Fit to the Hard proof.** It fits the proof less well.
  - The diver is a real 1933 performer, not a fictional inventor, and the dive is a stunt, not a mechanism attempt. The film would have to make the fiction visible, which here is the inked wings.
  - The archive has no paper-wing or rubber-band-rotor attempt, so attempts 1–2 would have to be handmade inserts.
- **Image quality.** At 320×240 the print is soft at this size, and the diver is about 60 px wide in the source.

---

## Recommendation

**Choose direction 1, Le Carnet de l'oiseau.**
- **It is the object.** The reference is a made object, a pen storyboard page, so Brief 2 asks us to handmake that object, and only this direction makes it at full fidelity:
  - two-value ink on cream;
  - stacked punched panels with the voice in a separate column;
  - part labels, struck-out words, show-through.
- **It makes the thesis visible.** Voice and image disclose different information on the same page:
  - The panels show the 35° nose and the fall.
  - The column shows the bird correcting "monter" to "s'arrêter".
  - That correction is where the bird's ability, flight, reframes the failure as a landing.
- **It meets the proof exactly.** It shows a fictional inventor, a paper wing, a rotor and a failed glide, with a board sequence and frame ranges on the page.
- **It is cheap and fully licensed.** It needs no new downloads.

**Borrow from direction 2** the brass split-pin articulation and the cast-shadow height for one insert: the rubber-band rotor (attempt 2, 8–16 s) as a cut-paper Pénaud hélicoptère pinned onto page 6. That puts one real foraged mechanism into the fiction.

**Keep direction 3** as a named branch only if *F-42 First Flying Machines* (PD) can be downloaded.

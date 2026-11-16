# Exercises in Style (Mauro Martino): three proposed directions

**Reference.** The reference is `assets/references/martinoCharcoal.webp`, the board tile. The gallery adds `martinoDada.webp` and `martinoCubism.webp`. All three are generated stills of one incident: a Paris bus and its passengers.
- **Charcoal:** linocut or cut-paper black on cream. A long bus side, walking silhouettes, a Haussmann facade.
- **Cubism:** embroidered or cross-stitched thread on a blue ground, seen from a steep high camera. Primaries.
- **Dada:** an aerial illustrated plaza.

What carries the work is one incident held still while the instruction changes.

**Frames.** Each keyframe is 1280x720. The builder is `proposals/kf.py` (deterministic: `python3 kf.py`). The board is `board.jpg`.

## The frozen encounter (shared by all directions)

**EventAnchor.** A platform bus stops. On the open rear platform, a long-necked young man in a soft felt hat, with a plaited cord where the ribbon should be, is jostled by a neighbour. He protests and then takes a free seat. The bus does not change destination.

**Protected cues:**
- the platform
- the long neck
- the cord hat
- one shove, at 1.2 s into each condition
- the seat taken, at 5.5 s

**Structure, about 60 s:**
- 0:00–0:12: baseline (street-level side camera, house treatment).
- 0:12–0:16: manifest card.
- 0:18–0:30: Δ treatment.
- 0:34–0:46: Δ camera = overhead.
- 0:48–0:60: side-by-side comparison at equal size, with coverage tallies.

**Seeds and samples.** Each condition has two draws, seeds 0417 and 0418, which jitter puppet timing, stitch noise or archive pick. That makes the stochastic spread visible.

**Sound.** One foraged or synthesised bus bell and engine bed, identical in every condition, as a declared control.

**Fixture.** The overhead variant changes only `camera` in the manifest. A missing jostle or a changed destination fails coverage.

**Downloads.** 0.9 MB in total, in `films/sources/mauro-martino-exercises-in-style/`.
- **`commons/rol1916.jpg`**: *1-6-16, nouvel autobus Madeleine-Bastille*, Agence Rol, 1916. Gallica via Commons. **Public domain.** <https://commons.wikimedia.org/wiki/File:1-6-16,_nouvel_autobus_Madeleine-Bastille_-_btv1b6946541g.jpg>
- **`commons/bourse1933.jpg`**: *Grève des autobus – Place de la Bourse, le public attendant la reprise*, Peyriras, 1933. Gallica via Commons. **Public domain.** <https://commons.wikimedia.org/wiki/File:Grève_des_autobus_-_Place_de_la_Bourse,_le_public_attendant_la_reprise_-_btv1b90350369.jpg>
- **`mia/ggc_*.png`**: frames from *Golden Gate City*, a high-angle cable car being boarded on a turntable. Moving Image Archive clip `86343393`. **Rights unverified:** the cache has no licence field and no year.
- **`mia/form_*.png`**: frames from *Formations* (1936), an overhead intersection. MIA clip `6eb03e7f`. **Rights unverified.**

**Not obtained.** *Paris – Fahrgäste hinter dem Autobus* (LABW Staatsarchiv Freiburg, 1955, CC BY 4.0) shows passengers on a real rear platform, but Commons returned HTTP 429 on every request for it. Retry it before the build; it would make the best platform plate.

**Other cache searches.** I searched for bus, omnibus, tram, streetcar, passenger, platform, overhead and aerial. *Berlin: Symphony of a Great City* (1927, PD in the US) has stills of men in felt hats (`5e2dccff`) and is a good spare.

---

## 1 · Cut-Paper Platform (animation-led: articulated silhouette theatre on a foraged cutout)

**Beat and time.** The shove in the Δ treatment = cut paper condition, at 1.2 s into that condition (0:19.2 of the film, as the frame's tag reads). The jostler's arm drives into the long-necked man, and he tips back against the stanchion. His cord shows as a braid of cut-through notches in the hat crown.

**Material.**
- **Foraged:** the 1916 CGO bus (Rol, PD), cut out with GrabCut plus a hand polygon. It is printed two-tone through CLAHE and a threshold, so the real passengers' heads survive in the windows as black paper.
- **Handmade:**
  - the carved Haussmann facade, the gouged pavement and the arched lit gap, built procedurally from tapered gouge strokes;
  - the rear platform, its chain and stanchion;
  - six articulated silhouette puppets.

**Technique SCIONs.**
- #2 Reiniger, articulated shadow theatre
- #29 GrabCut, cutout extraction
- #32 forward kinematics
- #41 secondary dynamics
- #45 occlusion compositing
- #27 declarative film compiler, for the manifest

**How it moves.**
- **Puppets:** they run on twos at 12 fps. Each joint angle is keyed per frame through FK, with no in-betweening blur, the way paper joints click.
- **Bus:** the cutout slides in on one layer, about 6 px per frame, decelerating to the stop. The wheels are separate circular cutouts that rotate.
- **The cord:** a 3-link chain under secondary dynamics, so it swings after the shove.
- **Walkers:** the foreground walkers loop a 6-pose walk cycle.
- **Per condition:**
  - Δ treatment re-prints the same rig from the same keys and seed, so only the treatment changes.
  - Δ camera re-poses the paper stage as a top-down plan of the platform. There the neck vanishes: the anchor loss is reported.

**Risk.**
- The puppets are still geometric (capsule limbs, block coats) next to the reference's fluid silhouettes. They need hand-drawn part shapes for the coat, hands and profile before the build.
- The cut-paper "treatment" is also the house look, so the baseline treatment must be visibly different. I propose the plain Rol photograph cutout, untreated, on a grey ground.

## 2 · Stitched Overhead (animation-led: procedural embroidery simulation)

**Beat and time.** The same shove under Δ camera = overhead, seed 0417, sample 1 of 2, at 0:35.2 of the film. Seen from above, the jostler is a red-coated disc with a bowler brim, overlapping the long-necked man's shoulders. His hat crown is ringed by the plaited cord as a two-tone whipped stitch. A running-stitch thread marks the shove vector.

**What it proves.** From overhead, the long neck, the anchor that carries the story, is not visible. The coverage report will log it as the anchor that disappears under this delta.

**Material.** Wholly handmade, as an executable procedural animatic:
- **Scene graph:** street, kerbs, trees, the bus roof with its ribs and the line-S plate, the open platform, and hats and shoulders from above.
- **Rendering:** the graph is rasterised to a 160x90 label grid, then sewn. Each cell is a cross-stitch: an under-stitch, an over-stitch with jitter, and a sheen thread on twill denim, with back-stitch outlines.
- **Palette:** the cubism and embroidery reference's blue ground, orange, red, yellow and green.

**Technique SCIONs.**
- #6 Whitney, harmonic motion, for the stitch shimmer
- #43 collage graph rewriting, for one scene graph and many renderers
- #44 multiplane parallax, for trees over road
- #27 Remotion-style declarative compiler (manifest to frames)

**How it moves.**
- The scene graph is evaluated per frame at 12 fps and re-sewn every frame.
- Cells whose label is unchanged keep their seeded stitch, so the street is stable. Cells the bus or passengers enter are re-stitched. Motion therefore reads as thread being re-sewn along the leading edge.
- The two seeds differ only in stitch jitter and a ±2-frame offset of the shove, which makes the stochastic spread visible.
- The side-camera baseline is the same graph projected as an elevation and sewn the same way. Δ camera swaps only the projection.

**Risk.**
- At 8 px cells the passengers are small. The platform may need a 6 px cell or a slow push-in that keeps the duration matched.
- Cross-stitch aliasing on diagonals could read as a pixel-art filter. Keep the shading per thread, not per pixel, and add visible thread ends.

## 3 · The Archive Answers (archive-led; kinetic typography; the one footage direction)

**Beat and time.** The delta reveal, at about 0:30. The typed manifest strikes `camera: street level` and types `overhead`, and the sample grid swaps from the baseline draws to the delta draws. Coverage chips then score each sample against the frozen anchors.

**The conceit.** The archive is the generator. Each prompt is a retrieval query against the Moving Image Archive cache's CLIP-indexed shots, and real returned shots are the "samples". The film is an honest comparison sheet: one changed field, two draws per condition, anchors ticked or failed, and drift rejected.

**Material.**
- Baseline:
  - Peyriras 1933 (PD), hats massed at the bus stop.
  - Agence Rol 1916 (PD), the platform bus.
- Delta:
  - *Golden Gate City*, a cable car boarded from above (rights unverified).
  - *Formations* (1936), overhead cars at an intersection with no bus and no encounter (rights unverified).
- Handmade: typed manifest and coverage chips.

**Technique SCIONs.**
- #53 civic footage performer
- #51 montage research
- #27 declarative film compiler
- #54 provenance graph (every frame carries its source ID)
- kinetic type, typed character by character with a cursor

**How it moves.**
- The manifest types at 14 characters per second, and the strike draws across in 6 frames.
- The clips play in their cells at their native 320x240 (cache) or as slow 2 % Ken-Burns drifts on stills.
- The red anchor ring is hand-placed per frame on the encounter.
- Chips flip green or red on the frame where the anchor is visible or lost.

**Risk.**
- This is the weakest as animation: it is a sheet, not a scene.
- The two MIA clips have no verified licence, and the Formations clip may need replacing with a PD overhead street from Commons or LoC before it can ship.
- The cable car is not a bus, which is recorded honestly as a partial anchor.

---

## Recommendation

**Build direction 2, Stitched Overhead, as the spine.** Fold in direction 1's cut-paper rig as the Δ treatment condition.

**Why 2.** It is the most literal executable procedural animatic the Hard proof asks for. A single scene graph with a manifest gives true matched seeds and lets you swap one field at a time:
- `camera` changes the projection;
- `treatment` changes the renderer, either stitch or cut paper.

Every condition then shares the same action keys, duration and sound. The critic can trace a change to exact frames, and the overhead view makes the "anchor that disappears" (the long neck) visible as a result, not an assertion.

**Why fold in 1.** Its foraged 1916 bus brings real Paris material and the reference's black-and-cream charcoal look into the treatment delta.

**Direction 3.** Keep it as the closing 12 s comparison sheet if the MIA rights can be confirmed. Otherwise drop it.

# les-lieux-dune-fugue: round 2, three directions (proposal stage, no film rendered)

The reference is `assets/references/fugue1.webp`: a frontal, locked-off 16 mm shot of a black carriage door in pale warm ashlar. The surround is carved and there is a small number plaque. No one is in the frame.

The defining beat comes from the Hard proof. **The memory of the bench is laid over the doorway, and then the bench returns in silence.**

This round follows the user's notes:

- Direction 1 continues the r1 line the user chose (r1 #1 + #3). This time the door is a frontal dark doorway in pale warm stone.
- Directions 2 and 3 are animation-led.

Commons was still returning HTTP 429, so this round's material comes from the Library of Congress and the Moving Image Archive cache. Downloads this round total about 11 MB, in `films/sources/les-lieux-dune-fugue/r2/`. The build scripts are in `proposals/src/` (`kf1.py`, `kf2.py`, `kf3.py`, `common.py`).

## Foraged material (all checked on the item record)

| id | item | rights | used in |
|---|---|---|---|
| DOOR-C | Carol M. Highsmith, *Exterior doorway, Joseph P. Kinnerary U.S. Courthouse, Columbus, Ohio*, LoC 2010719611 | "No known restrictions on publication" (Highsmith gift, public domain) | 1 (plate), 2 (traced background), 3 (stone blocks, carved jambs and lintel) |
| DOOR-S | Highsmith, *Exterior door. U.S. Custom House, Savannah, Georgia*, LoC 2014630119 | No known restrictions | 3 (the two door leaves) |
| BENCH | Highsmith, *Park bench in Sacramento*, LoC 2013633886 | No known restrictions | 1 (memory layer), 3 (far plane + bench cutout) |
| WALK | *Alice in Wonderland* (W. W. Young, 1915), Moving Image Archive clip `147f497d`, t = 1.5–3.3 s | Public domain (US, pre-1929) | 2 (rotoscope source only; no pixels of the film appear) |

Rejected:

- Muybridge *Animal Locomotion* pl. 562 (LoC, PD) would be an ideal walk cycle, but the walker is a nude child. It is downloaded but not used.
- *Brooklyn Goes to San Francisco* (1947, in the MIA cache) has a good walking shot, but its rights are unverified.
- The Washington "Post Office Department" door has legible agency signage and glass doors.

---

## 1 · Bench in the Door, warm stone (`kf-1.png`). Archive-led

- **Beat / time:** the central beat, about 00:31 of 00:56. Doorway P01, second capture from the same position. The remembered bench P03 shows *only through the dark of the opening*. Voice: « Le banc, c'était l'hiver, à peu près. » The memory is tagged "vers l'hiver" (an interval) and its link is marked INFERRED.
- **Material:** DOOR-C as the plate, BENCH as the memory. Both are photographs used whole and graded. Nothing is drawn.
- **Techniques:**
  - SCION 45, Occlusion Compositing. The matte is the plate's own darkness inside the opening, so the stone, the jamb carving and the hanging lantern stay in front of the memory.
  - SCION 29, GrabCut, to refine the matte at the jamb edge in the build.
  - SCION 44, Multiplane Parallax, used very lightly.
  - SCION 54, Provenance Graph, for the on-screen ledger line.
- **Motion:**
  - The plate is locked off, as in the reference.
  - The memory screen-blends in over 3 s (this keyframe is at about 60 %) and drifts 1–2 px per second on its own plane. It holds through the line and fades out, leaving the empty dark opening.
  - Then a hard cut to the bench in silence.
  - The last 6 s are the r1 handmade place record (r1 kf-3), with the bench print swapped for BENCH. The "SILENCE" field is stamped there.
- **Risk:**
  - The building is a US federal courthouse, not a Paris porte cochère. The frontal pale ashlar, carved surround and dark opening match the reference well, but the "warm" is partly a grade (the source stone is cooler and greyer).
  - The proof needs "one place twice from the same position". There is only one Highsmith exposure of this door, so capture 1 has to be the same photo at another grade or crop. That is an honest limit to record in the ledger, not a solution.
  - The opening is a recess with glass doors deep inside. It is not a closed wooden leaf like the reference.
  - The urns and shrubs at the frame edges are busier than the reference. The build should crop tighter or accept them.

## 2 · La marche: rotoscoped line walk (`kf-2.png`). Animation-led

- **Beat / time:** the departure walk P01 → P02, about 00:10–00:20 (keyframe 00:14). The child leaves the dark doorway toward the viewer. Voice: « Je suis sortie par la porte cochère. Personne ne l'a vue se refermer. »
- **Material:**
  - Handmade line drawing on toned paper.
  - The walker is **rotoscoped** from WALK. The key drawing (frame 19) was traced by hand over a 4× enlargement of the source frame: eighteen strokes, spline-smoothed, ink-jittered. The earlier frames 09–17 are traced from their own mattes and left as red and blue pencil roughs with their frame numbers.
  - The doorway background is traced from DOOR-C, with its edges re-drawn as strokes. It has a three-tone watercolour lay-in of warm stone and a dark door wash, and fades into blank paper.
  - The pavement seam and kerbs are hand-ruled.
- **Techniques:**
  - SCION 7, Peter Foldès, Drawn Metamorphosis, for the line language and the option to let the last drawing of the walk turn into the bench.
  - SCION 38, Dynamic Pose Selection: which source frames become keys.
  - SCION 29, GrabCut, and SCION 30, SAM 2, to matte each source frame before tracing.
  - SCION 41, Secondary Dynamics, for hair and hem settle on the stop.
  - SCION 54, Provenance Graph: each drawing records its source frame and time.
- **Motion:**
  - The walker animates at 12 drawings/s ("on twos"), one new tracing per source frame across about 3.6 s of the 1915 shot. The shot is slowed to 1.5× by holding drawings, never by warping.
  - The ink boils at 3 re-seeds per second.
  - The background is drawn once and held, as an animation background is.
  - The onion-skin roughs persist and fade, so the route of the walk stays on the page as a trace. A static figure would not show the route.
  - At the junction the line drawing stops, and the pavement seam is redrawn as the route line (P01 → P02 → P03).
- **Risk:**
  - The source is 320×240. The key drawings need hand tracing (as here), so it is about 40 drawings for 3.5 s of walk. Auto-traced roughs are crude.
  - It is an enacted, costumed fiction image (Carroll's Alice), so under §4 it must be declared an alternate method. Only the *traced* line appears, never the film's pixels.
  - It moves away from photographic frontality. The warm stone and dark door are kept only in the wash.

## 3 · The Paper Facade: cutout collage + multiplane (`kf-3.png`). Animation-led

- **Beat / time:** the central beat staged as an opening, about 00:30–00:38 (keyframe 00:34). The carriage door's two leaves swing inward, and behind them, on a deeper plane, is the remembered bench in another light. This is the frontal, warm stone, dark door look of the reference, rebuilt in cut paper.
- **Material:** a handmade collage.
  - The facade is built block by block from ashlar pieces cut from DOOR-C's plain wall, each with a ragged scissor edge, a light cut rim and its own shadow.
  - The carved jambs and lintel are cut from DOOR-C as raised pieces.
  - The two dark leaves are cut from DOOR-S, toned warm-black.
  - The far plane is BENCH's park, printed cool.
  - The bench is a separate GrabCut cutout from BENCH on its own plane.
  - A small hand-cut enamel number plaque ("7", not the reference's 18).
- **Techniques:**
  - SCION 1, Gilliam Cutout, and SCION 3, Ernst Collage Grammar, for the cut-paper building.
  - SCION 32, Forward Kinematics: each leaf is a card hinged on its jamb, rotated by θ and projected with a pinhole camera (f = 1100). The leaf foreshortens and shades by cos θ.
  - SCION 5, Norstein, and SCION 44, Multiplane Parallax. Facade (depth 0) → leaves (0.35) → bench (0.6) → park (1.0), with a haze between planes and shadow offset and blur set by depth.
  - SCION 45, Occlusion Compositing.
  - SCION 40, Physical Tabletop Capture, if the build prints and shoots the pieces under one lamp.
- **Motion:**
  - 0–3 s: the closed paper door is held frontal, like the reference.
  - 3–7 s: the leaves open on eased hinge angles, 0 → 58° left and 0 → 64° right, with the right leaf 4 frames late, at 12 fps.
  - Meanwhile the camera trucks 6 px, and the planes separate by parallax.
  - The bench cutout settles 2 px.
  - Then the leaves close again, the facade is flat stone again, and the film cuts to the bench in silence (the r1 place record can end it).
- **Risk:**
  - The ragged-edge and shadow treatment can read as a digital "paper" effect unless the build prints the pieces and photographs them (SCION 40). That is recommended.
  - The bench is partly hidden by the right leaf at 64°. Choose its x position against the final angle.
  - The courthouse carving is larger and more ornate than the reference's vine-carved surround.

---

## Recommendation

**Spine: direction 3 (The Paper Facade), with direction 1's double exposure kept for the return of P01 and the r1 place record as the silent ending.** Direction 2's line walk is the bridge between them (P01 → P02).

Direction 3 is the one that *animates the defining beat*. The door opening onto the remembered bench is something a viewer can point to. Its frontal, warm stone, dark door look is closest to the reference, and every piece of it comes from foraged public-domain photographs, cut and operated on rather than filtered.

Direction 1 keeps the user's r1 choice: the bench seen through the dark of a real doorway, without animation. It is the "same place twice" partner of the paper facade.

Direction 2 gives the film its route between places, and the walk leaves a visible trace. Cap it at about 8 s of rotoscope to keep the drawing budget bounded.

Before the swarm build:

1. Print the facade pieces and shoot them under one lamp (SCION 40), or at least keep shadows and cut edges consistent across frames.
2. Hand-trace about 40 walk drawings from WALK.
3. Have the route researcher look again on Commons, once the 429s clear, for a true Paris porte cochère photographed twice from one position. It would replace DOOR-C in direction 1.

# La Machine à tuer le temps: three directions

Reference: the red Oucipo spiral notebook (Drouot lot 175). Black-and-white prints pasted on cream pages, typed captions on yellowed tape, shot numbers in pen, and a red page number. The Hard proof needs eight originals (clock, hand with parcel, second hand, door, glance, dropped receipt, exit, empty threshold), an ordinary cut A, and a cut B in which the parcel seems illicit.

**Shared frozen pool.** Eight Jack Delano FSA/OWI photographs of Union Station, Chicago, 1943, from the Library of Congress. Every item is marked "No known restrictions on publication" and is a US government work in the public domain. They were already downloaded in `films/sources/la-machine-a-tuer-le-temps/` and are listed in `films/credits/la-machine-a-tuer-le-temps.json`. This stage downloaded nothing new (0 MB).
Pool sha256 over the eight files: `a3d308bd38b67cc3a54277bb50030206b8356b78fac7895b175dfc1b36eb2056`.

| id | shot | LoC item |
|---|---|---|
| 01 | horloge (clock) | 2017844012, dispatcher's office with wall clock |
| 02 | main au colis (hand with parcel) | 2017844121, mail-room woman carrying a box and glancing back |
| 03 | trotteuse (second hand) | 2017844115, conductor checking his watch, looking off |
| 04 | porte (door) | 2017843935, soldier at the train door |
| 05 | regard (glance) | 2017843923, red cap staring out of frame |
| 06 | reçu tombé (dropped receipt) | 2017843913, reservation slips on the counter |
| 07 | sortie (exit) | 2017843870, soldiers going back to camp |
| 08 | seuil vide (empty threshold) | 2017843779, main waiting room at 1 a.m. |

Cut A = 01 02 03 04 05 06 07 08 (an ordinary handoff). Cut B = 05 04 02 06 03 01 07 08: the glance comes first, then the door, then the parcel, and the clock arrives late. The film runs about 60 s: a title (0–3 s), cut A (3–28 s), and cut B (30–56 s), all over one shared sound bed. Both final mixes follow.

The scripts that built the keyframes are in `proposals/src/`. `common.py` holds the pool and print, tape and hand-lettering helpers. `kf1.py`, `kf2.py`, `kf3.py` and `board.py` build the images, and `puppets.py` holds the shadow-puppet rigs.

---

## 1 · Le cahier rebattu (paper stop-motion of the dossier), animation-led

- **Beat, about 0:31.** Cut B begins by being re-made in the notebook. The page holds 05 regard beside 02 main au colis. Their old cut-A numbers (5, 2) are struck through in red pencil and re-numbered 1 and 3. Print 01 horloge is still sliding across the gutter toward a later slot.
- **Material.** Foraged: the pool prints, toned as silver-gelatin prints with only the negative rebate trimmed. Handmade: the spiral notebook spread (paper, wire coils, gutter shading), typed tape captions in French (Courier) in the dossier's style ("05.- Le porteur regarde hors du champ, vers la consigne."), and the numbers, written stroke by stroke with my own single-stroke hand-lettering, in ink and in red pencil.
- **Techniques.** SCION 40 (Physical Tabletop Capture, paper performance), SCION 43 (Collage Graph Rewriting: the order of the pages is the graph), SCION 27 (Declarative Film Compiler: the slot moves are driven from the B recipe).
- **How it moves.** Shot on twos (12 drawings/s). Between cuts the camera stays locked on the open notebook. Each print is lifted (its shadow grows over 4 frames), translated to its new slot along a slightly irregular path, and set down (shadow shrinks). It is translated only, never rotated or warped, so its image geometry stays frozen. The red pencil writes the new number stroke by stroke, one segment per frame. A page turn (6 drawings of the sheet bending around the coil) carries us to the next spread. Inside each cut, a print is "projected": the camera pushes into it until it fills the frame, and it plays for its recipe duration. The film is the dossier being executed.
- **Risk.** Least risky to read and closest to the reference. The risk is that it turns into a document about editing more than a film where cause changes. The cut B projections must be held long enough for the inference to land, so the notebook plays only between the cuts. The hand-lettering has to look like a hand, not a font, which needs jitter and pressure.

## 2 · Ombres de la consigne (articulated shadow theatre), animation-led

- **Beat, about 0:38 (cut B, shots 1–3).** The conductor glances at his watch. The woman with the parcel turns her head back toward him on her way to the lit door of the CONSIGNE. A receipt drops between them. The red second hand of the station clock is at 51 s.
- **Material.** Handmade: two jointed card puppets cut as polygons, posed from the Delano photographs of the conductor (03) and the mail-room woman (02). Each is a forward-kinematics chain of torso, head, upper arm, forearm, thigh, shin and shoe. Also handmade: the station clock with its punched tick ring, the doorway with its lit transom, the punched receipt, and the station floor band. Foraged: the far plane is the Union Station colonnade from pool shot 08, thresholded into a faint paper layer behind the screen (a multiplane backdrop). The screen is warm backlit paper with an oxblood vignette, the notebook's red.
- **Techniques.** SCION 2 (Lotte Reiniger, Articulated Shadow Theater), SCION 32 (Forward Kinematics), SCION 44 (Multiplane Parallax), SCION 45 (Occlusion Compositing). I tried SCION 29 (GrabCut) on the Delano prints, but the masks lost the head profiles that silhouettes depend on, so the puppets were cut by hand.
- **How it moves.** Each of the eight pool shots is an animated shadow shot rendered once and frozen, for example the walk cycle with the parcel (8 poses on twos), the head turn (3 key angles eased over 10 frames), the watch lift, the door swing, the receipt's falling tumble (simulated), the exit and the empty doorway. The FK joint angles are keyed per frame. The two cuts then only re-order and re-time those frozen renders, so the SCION invariant still holds on the animation pool. The far plane drifts at 0.3× the foreground for parallax.
- **Risk.** It looks the most like an animation and has the strongest genre pull, since a silhouette plus a parcel already suggests espionage. That could make cut A read as illicit too, which weakens the contrast. The shared-sound screening will test this. The puppets are drawn by me, so they are less faithful to the reference's photographic medium. The red-and-cream palette carries the link to the notebook.

## 3 · La permutation (archive prints with edit-recipe typography), archive-led

- **Beat, about 0:47 (cut B, position 05/08, B timecode 17:08).** The conductor checking his time (03) now arrives after the glance, the door, the parcel and the receipt, so his look reads as watching for someone late. Beside the print, the permutation graph draws the identical pool in A order and in B order with a line for each asset. The line for the current shot is red, and the frozen pool hash is shown.
- **Material.** Foraged: the pool prints, shown full height, untouched apart from the trimmed rebate and print toning. Handmade: the typed tape caption, and the recipe and permutation typography (asset id, in/out, duration, direction).
- **Techniques.** SCION 27 (Declarative Film Compiler: the screen shows the recipe it executes), SCION 54 (Provenance Graph: each visible frame resolves to an asset), kinetic typography.
- **How it moves.** The prints themselves cut hard on the recipe frames, with no motion on the photographs. The typography animates. Each permutation line draws itself over 6 frames when its shot starts. The timecode counts per frame. The tape caption types itself on at 2 characters per frame. Between A and B, all eight lines re-route at once, so the viewer sees that the pool stayed the same and only the wiring moved.
- **Risk.** This is the least animated direction, close to a diagram of the method. The split screen makes each print smaller, which weakens the glance. It probably suits a closing "proof" section better than a whole film.

---

## Recommendation

Make **direction 1, Le cahier rebattu**, the film's body. It is the closest to the reference (spiral notebook, pasted B&W prints, typed tape, numbering in pen and red), it is animation-led with a real handmade object, and its central animation, prints physically re-slotted and re-numbered, *is* the Oucipo operation. Every projected frame is an untouched pool photograph, so the frozen-pool invariant is visible, not just asserted. Borrow direction 3's permutation graph as a 4–5 s coda, drawn on the last notebook page in red pencil, for the reuse report. Keep direction 2 as the alternative if the user wants a more fully animated film, accepting that it brings in its own genre colour.

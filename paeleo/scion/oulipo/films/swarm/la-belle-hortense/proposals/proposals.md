# La Belle Hortense: three proposed directions

**Reference.** `assets/references/hortense.webp` is the Points paperback cover.
- It is a photograph of a running figure (a red top, a black skirt and a pale leg), taken while the camera panned.
- The ground and background are smeared into long horizontal streaks: saturated green, with ochre and red earth at the foot.
- The figure is cropped tight. The head is out of frame.
- The type is a slab typewriter face: the author in black, the title in red.
- The palette is red, green and black. The light is flat daylight.

**Motif grid (Hard proof).**
- **Motifs:** A manteau (coat), B cloche (bell), C clé (key), D banc (bench), E reçu (receipt), F porte (locked service door).
- **Permutation:** `[6,1,5,2,4,3]`. `kf.py` asserts the fixture: I→II is `FAEBDC`, six applications return to `ABCDEF`, and no module repeats a motif.

| module | order |
|---|---|
| I | A B C D E F: manteau, cloche, clé, banc, reçu, porte |
| II | F A E B D C |
| III | C F D A B E |
| IV | E C B F A D |
| V | D E A C F B: banc, reçu, **manteau**, clé, porte, cloche |
| VI | B D F E C A |

**The mystery.**
- **Module I, the seed, kept intact.** A visitor arrives with a sealed envelope. A bell rings. She opens it and finds a brass key. She leaves the key on the bench, on top of a dark overcoat that lies folded there. Nobody remarks on the coat: it is background. She walks away, and the service door stays shut.
- **Module II.** The conductor comes in. The door is locked. He takes *his coat* off the bench and puts it on (slot 2). He finds the receipt from the envelope, and then an empty bench. The key is "missing".
- **Modules III and IV** offer the false explanations: the visitor, a thief, the bell.
- **Module V.** The coat returns as evidence. The conductor runs back in it (slot 3), and the key slips from its fold (slot 4). The door opens (slot 5), and the bell rings when it opens (slot 6).
- **Solvability.** A reader can solve it at the end of module II: the key was laid on the coat, and the coat left with him. The reveal leans on module I and module II, not on its own first appearance.
- **Motif that changes role:** the coat, from background to evidence.

**Defining beat.**
- **Timing:** a film of about 60 s. Title 0–3 s, then six modules of 9 s each (I 3–12, II 12–21, III 21–30, IV 30–39, V 39–48, VI 48–57), then an end card.
- **The beat:** inside module V each slot lasts 1.5 s, so the coat slot runs **42.0–43.5 s** and the key slot starts at 43.5. All three keyframes stop at about **43.3 s**: the coat has returned and the key is about to be seen.
- **Comparison baseline:** the same six modules cut in story order with no permutation, where the coat never comes back in a fixed slot.
- **What the viewer should be able to point to:** "the red coat was on the bench in the first scene."

**Builder.** `proposals/kf.py` is deterministic. Run it as `python3 -I kf.py /home/user/bolas/paeleo/scion/oulipo`.

**Material.** About 0.2 MB of new downloads (the budget was ~40 MB). I also wrote about 13 MB of PNG frames decoded from the local archive cache with ffmpeg. Everything is in `films/sources/la-belle-hortense/`.

| id | item | source | licence | used in |
|---|---|---|---|---|
| COND | *Chicago, Illinois. Conductor checking his time in the telegraphers' office…* (Jack Delano, FSA/OWI, 1943), LoC 2017844115 | local copy in `sources/la-machine-a-tuer-le-temps/`, from loc.gov/item/2017844115 | **Public domain** (US government work; LoC: no known restrictions) | kf-1 (cutout puppet) |
| SHED / MEADOW | *Bourré (Loir-et-Cher)* 50866795131 and 50866798791, Daniel Jolivet | Commons (local copies in `sources/recits-dellis-island/`) | **CC BY 2.0**, credit Daniel Jolivet | kf-1 (plate), kf-2 (pan-exposed meadow) |
| KEY | `File:Skeletonkey.png` (960 px thumbnail) | Commons, new download | **CC0** (extmetadata) | kf-1 |
| VINC | *Arrivée d'un train gare de Vincennes* (Méliès, 1896), webm | Commons (local copy in `sources/recits-dellis-island/`) | **Public domain** | kf-3 (main shot, frame at 22.0 s) |
| MIA-banc | *Amateur Film Children Playing Near Hudson*, clip 46cd8d58 | Moving Image Archive cache | **Unverified** (amateur film; no licence field in the cache) | kf-3 strip |
| MIA-reçu | *Two Pay Days (Part I)* (1927), clip 3b9d2889 | MIA cache | **Unverified.** A 1927 US film is probably PD. | kf-3 strip |
| MIA-clé | *Key to Our Horizons* (1952), clip 7102b861 | MIA cache | **Unverified** | kf-3 strip |
| MIA-porte | *Dating: Do's and Don'ts* (1949, Coronet), clip a267fee7 | MIA cache | **Unverified.** It is widely circulated as Prelinger PD; confirm. | kf-3 strip |
| MIA-cloche | *Communications and Our Town* (1947), clip 381d177e | MIA cache | **Unverified** | kf-3 strip |
| Type | Courier 10 Pitch Bold and Regular (Bitstream, X11 Type1) | system font | Bitstream donated it to the X Consortium under a free licence | all |

**Searched and not used.**
- The MIA cache has almost no colour material and no coat, bench-with-key or receipt footage. "Bench" hits are courtrooms and wicker chairs.
- *Berlin: Symphony of a Great City* (b6e217eb, an empty platform) is the better module-I establishing shot for direction 3. Its rights also need confirming.
- Commons search answered HTTP 429 intermittently, and LoC answered 503 throughout, so no new LoC fetch was possible. Every LoC item here was already on disk, with its rights advisory read by an earlier film.

---

## 1 · Le manteau rouge (articulated cutout, multiplane, stencil colour): **recommended**

**Beat and time.** Module V, slot 3, at **≈43.3 s**.
- The conductor runs back toward the station in the coat that lay on the bench in module I.
- The key has just slipped from the coat's hem and falls behind him.
- The typed module caption reads "V. / le manteau revient", and the slot line puts MANTEAU in third place.
- This is the beat where a motif that was background becomes evidence.

**Material.**
- **The runner:** an FSA/OWI conductor in an ankle-length overcoat, cut out by density and inside a hand-placed scissor line, with the shirt and collar holes filled.
- **The plate:** the Bourré goods shed with its shut door, quoined in red and white, standing on grass (CC BY 2.0).
- **The key:** CC0.
- **The type:** a typewriter face, in the cover's black and red.

**Techniques.**
- **Articulated cutout and FK:** Lotte Reiniger SCION 2 and Forward Kinematics SCION 32.
  - The rig has three pieces: the body, and two substitution shins hinged at the coat hem.
  - The shins are the cut leg stretched 1.7×, used twice. The far leg is printed darker.
  - The body leans 9° into the run.
  - The stride is a sinusoid at about 2.3 Hz, so each frame advances the phase by 0.1 cycle.
- **Multiplane parallax:** SCION 44.
  - There are three planes: the shed, mid grass, and a near grass band.
  - The camera pans with the runner, so the far plane moves about 90 px per frame and the near band about 260 px per frame.
- **Shutter integration.**
  - Each frame is the mean of 36 sub-frame renders over a 180° shutter.
  - So the streaks on the ground are real camera-pan smear of a real photograph, and the shins blur because they really swing during the exposure. This is the cover's own physics: a panned shot of a runner.
  - The key falls 16 px and turns 14° inside the exposure.
- **Stencil colour (Pathécolor-style), for SCIONs 45 and 54.**
  - The plate is reprinted in black and white. Each colour is then laid in as a transparent dye through a cut mask:
    - **Green:** the grass, keyed from the original's own hues.
    - **Red:** the brick quoins.
    - **Red:** the coat. The cap, face, collar and newspaper are left out of the stencil.
    - **Brass:** the key.
  - The dyes are a fixed motif code for the whole film: the coat is always red and the key is always brass.
- **How the frame moves across the film.**
  - In module I the same coat lies folded on the bench as a still, dyed piece. It is red but unremarked.
  - In module II the conductor lifts it and puts it on (a cutout swap).
  - In module V it comes back running, as in this frame.

**Risk.**
- One photograph is doing the work of a running man, so close-ups of the legs will show the trick. Running reads mainly through the lean, the shin swing and the smear.
- A second FSA figure with visible legs, walking, would strengthen the rig. Search LoC once it answers.
- Bourré is already used in *Récits d'Ellis Island*. A fresh green halt from Commons would avoid the repeat.
- The cut has a slight wall fringe at the right arm. It needs a hand touch-up before the build.
- The visitor of module I still needs her own cutout, from a second FSA figure in a coat.

## 2 · La grille tourne (kinetic typography, harmonic motion)

**Beat and time.** It is the same beat, at **≈43.3 s**, shown as type.
- The sextine grid is typed row by row. Rows I–IV are set, with a braid of thin strands showing where each motif moved, and the coat's strand is red.
- In row V, "banc" and "reçu" are set. "manteau" is in flight along its IV→V strand into slot 3, smeared by the exposure.
- Below the grid, the module's clause is being typed: "le manteau revient / en cour▌".

**Material.**
- **Handmade:** the grid, the braid and the type, set in Courier 10 Pitch Bold like the cover's slab face.
- **Foraged:** the ground is the Bourré meadow (CC BY 2.0). It was exposed through a real 420 px pan over 60 positions, printed row by row for contrast, then stencilled green above and ochre/red below.
- The result is the cover's streaked field, made from a real meadow rather than a texture.

**Techniques.**
- **Harmonic motion:** John Whitney SCION 6.
  - Every motif word travels between modules on a smoothstep path from its old slot to its new one, so the permutation is literally the choreography.
  - The six travels are staggered by slot (1.5 s each), so a viewer learns the braid by watching it and can predict the next row.
- **Frame-by-frame integration of the moving word.** The moving word is rendered at 40 sub-positions, weighted toward arrival, so it lands sharp.
- **State machine for the write-on:** SCION 48. The clause write-on runs at a typewriter's rate, with a cursor; it pauses on the evidential word.
- **Sound.** Typewriter strikes give the slot clock, and a bell rings on slot 6. These are Commons CC0/CC BY recordings already used elsewhere in the project.

**Risk.**
- It proves the form best and the mystery worst. A viewer can follow the permutation without ever seeing the coat on the bench, so the clue lives only in the words.
- The mitigation is that each word carries its clause ("sur le manteau plié", "il prend son manteau").
- At 25 px the grid is dense on a phone. The film would zoom into the active row.

## 3 · Le passager de Vincennes (archive recut; the one archive-led direction)

**Beat and time.** Module V, slot 3, at **≈43.3 s**.
- **The main shot:** in Méliès' 1896 *Arrivée d'un train gare de Vincennes*, a passenger in a long pale duster walks off the platform toward the camera. He is isolated by a period iris and his coat is stencilled red; the rest of the frame is in a green tint bath.
- **The right column:** module V in permutation order, as six archive shots (bench, receipt, coat, key-at-lock, door, belfry), with slot 3 lit.

**Material.**
- **Foraged:** Méliès 1896 (Commons PD) and five Moving Image Archive cache clips (rights unverified), with a typed red caption.
- **Handmade:** only the stencil, the iris matte and the type.

**Techniques.**
- **Collage montage:** Frank Mouris SCION 4 and the Provenance Graph SCION 54.
  - Each module is six archive shots, one per motif, cut in the permutation's order.
  - A motif keeps the same source shot each time it returns, so a return can be recognised as a return.
- **Iris and stencil, frame by frame:** Occlusion Compositing SCION 45.
  - The iris closes on whichever motif holds the slot.
  - The coat's red stencil is re-cut per frame, following the walking figure. That is rotoscope tracking: roughly 36 hand-placed keyed polygons for 1.5 s, interpolated.

**Risk.**
- It is the most "archive edit" and the least animated. The mystery is weak, because the coat in shot V.3 is a different man's coat in a different century from module I's bench, so the clue is a matching cut, not a fact.
- Five of the six strip sources have unverified rights.
- The 360p sources upscale soft.
- It cannot carry "the key was laid on the coat" without a handmade insert.

---

## Recommendation

**Direction 1, Le manteau rouge.**
- **It is the only direction where the clue is an image.** The viewer sees the red coat on the bench in module I and sees that same red coat running back in module V. The defining beat is therefore pointable ("the red coat was on the bench") without reciting the formula.
- **It meets the reference on its own terms:**
  - A tight-cropped runner, in red against streaked green, with slab type in black and red.
  - The streak is produced by the same physics: a real pan exposure over real photographs.
- **The colour carries the mystery.** The fixed stencil-dye code (coat red, key brass) also works as the motif signature that the SCION invariants ask for.
- **Use direction 2 inside it.** Its braid can become the end card and the per-module slate (a 2 s typed row before each module), which keeps the permutation visible without making it the film.
- **Drop direction 3**, except possibly the Berlin empty-platform shot as a module-I establishing plate once its rights are confirmed.

# Le Chant du styrène: three proposed directions

Reference: `assets/references/styreneA.webp`. Translucent red and amber injection sprues lit against black in a scope frame, with soft blue lights out of focus behind. The defining beat is a **finished product held long enough to read, then shown with the runner and mould that explain it**. Each frame below is 1280x720 with 2.35 letterbox bars. The voice is a lower caption: one original alexandrine, with `|` marking the 6+6 break (scansion is given under each direction). Keyframe scripts are in the session scratchpad, and the downloads are in `films/sources/le-chant-du-styrene/kf/` (about 2.4 MB in total).

Planned tour (about 38 s, reverse dependency order): prologue key (0–6 s) → **finished part** (6–13) → **part on its runner** (13–20) → **open mould, empty cavity** (20–28) → **pellets / raw polystyrene** (28–36) → coda (36–40).

---

## 1 · Carotte sur noir (foraged still, cut out)
- **Beat / time:** step 2, the part still on its runner, at about 14–20 s. The cut into this shot falls on the caesura of "Avant d'être la pièce, | elle était le canal". Scansion: A-vant-d'ê-tre-la-piè(ce) | el-l'é-tait-le-ca-nal. The final -ce elides before "elle", giving 6+6.
- **Material:** "Gunpla multi color sprue.jpg" by Gravis, CC BY-SA 4.0, https://commons.wikimedia.org/wiki/File:Gunpla_multi_color_sprue.jpg. This is a real polystyrene kit runner with the gate tabs "a/b" still on it. The blue light bar and light disk behind it are handmade.
- **Technique:** #29 GrabCut. A hue-seeded GrabCut mask separates the sprue from the wooden table, and the edge is eroded and feathered. #44 Multiplane parallax: in the film the sprue plate drifts about 40 px left over 6 s, the blurred blue lights move at 0.3x, and the rim glow breathes. #45 Occlusion keeps the sprue in front of the lights.
- **Risk:** the plastic is blue and green, not the reference's red and amber. I did not recolour it, because that would be a costume. A red or amber runner photo would need more foraging. A modern Gunpla sprue reads as a hobby kit, not 1958 industry. Faint orange wood fringe survives on a few edges.

## 2 · La main, le grain (archive + Commons hinge)
- **Beat / time:** the coda at about 36 s. This is the Hard proof's cut on the caesura. "Ce jouet dans la main | fut grain dans une main" (Ce-jou-et-dans-la-main | fut-grain-dans-u-ne-main, 6+6, classical diaeresis on jou-et). The cut lands exactly on the break, with the same gesture of a hand holding plastic across it. Because finished → raw skips two process edges, this is a recap shape-match **outside** the reverse tour, not one of its edges. It must not count as a tour step: the direct-edge fixture would fail.
- **Material:** left plate from the Moving Image Archive cache, clip b18d7dcd from *New World Through Chemistry* (DuPont, Eastmancolor, probably 1950s): hands working a moulded orange plastic piece. Archive page: https://www.movingimagearchive.com/sources/ (slug in `allways-forage/index.json`). Right plate: "ABS granule.jpg" by Jacorna, CC BY-SA 4.0, https://commons.wikimedia.org/wiki/File:ABS_granule.jpg. Only an exposure match was applied (mean and std matched to the archive plate), no grade.
- **Technique:** #27 Declarative compiler. Cut times are tied to caesura cue times in the EDL. #43 Collage graph rewriting: the hand keeps its identity while the object changes from product to grain. In the film this is a hard cut in time, not a split. The keyframe shows both sides of the hinge.
- **Risk:** **the licence of the archive clip is not verified.** It is probably public domain (pre-1964, not renewed), but that is unconfirmed, so it needs a PD check or a Commons or LoC substitute. The granules are ABS, not polystyrene, so they must be swapped for a polystyrene pellet image. The source is 320x240 and soft. It is the least like the reference (no black field).

## 3 · La clé et son creux (handmade shot in a foraged mould)
- **Beat / time:** steps 2→3, the shot lifted from the open mould half with its empty key cavities below, at about 20–24 s. This is the central reveal of the Hard proof: product, then negative form. It also links to the prologue key from the common seed. "La clé pend à sa branche, | et sa forme est en creux" (La-clé-pend-à-sa-bran(che) | et-sa-for-m'est-en-creux, 6+6).
- **Material:** handmade. The polystyrene shot is built as geometry: sprue cone, runner, gates and three keys. It is shaded from a distance-field tube profile, so thick sections are deep red and thin sections pass amber light, with specular highlights. It also casts a shadow. The mould-half steel is foraged: "Injection mold - (11).jpg" by Bricetofly, CC0, https://commons.wikimedia.org/wiki/File:Injection_mold_-_(11).jpg. It is darkened and defocused, and the cavities are cut into it as recesses with a lit lip.
- **Technique:** #8 Constraint sketchpad. The shot and its cavities share one layout function, so the negative always matches the part exactly. This is a verifiable process edge. #45 Occlusion and shadow. #41 Secondary dynamics: in the film the shot rises out of its cavities with the ejector, hangs, and swings a few degrees. Run backward, it settles back into its creux. Shot direction is labelled separately from process order, as the invariant requires.
- **Risk:** the plastic still looks somewhat like flat graphics. It needs real refraction or a backlit, physically modelled pass to match the reference's glow. The mould photo is modern aluminium tooling. The keys must read as keys at the size they appear on the runner.

---

## Recommendation
Build **3 · La clé et son creux** as the spine of the film. It is the only direction that shows the defining beat, product and then its negative, inside one controllable, verifiable frame. It carries the brass key of the prologue into polystyrene, and its palette (red and amber on near-black) aims straight at the reference without tracing it.

Use **1 · Carotte sur noir** as the real-photograph step 2 inside the tour, so the film is not entirely simulation. Forage a red or amber runner first if one exists.

Keep **2** only as the caesura-cut coda, after the archive clip's licence is verified and the ABS granules are replaced with polystyrene pellets. Until then, do not use it.

# Exercices de style: three proposed directions

**Reference:** `assets/references/styleBook.webp`, the Gallimard Jeunesse illustrated edition. It has:
- a warm cream-to-butter page;
- huge ghosted type in pale yellow;
- a red title in mixed, jumping faces over black "de Style";
- a small green-and-cream Paris bus;
- a strip of tiny vignettes by many illustrators;
- a flat grey band with white sans type.

All three keyframes are built on that page grammar: cream page, ghost word, mixed red/black title, a vignette strip of the six beats with the current beat ringed in red, and a grey band. Each one changes only the material inside the page, so the cover becomes the film's frame, and each retelling is an "illustrator" working under one rule.

**Incident (frozen ledger, the prompt's common seed), 60 s film:**
1. 18:00 the visitor arrives at the empty station with a sealed envelope.
2. 18:02 a bell rings.
3. 18:04 the visitor opens the envelope.
4. 18:05 the visitor finds a brass key.
5. 18:06 the visitor leaves the key on the bench.
6. 18:07 the visitor walks away. The service door stays closed.

**Planned film:**
- 0–6 s: baseline.
- Then four retellings of about 12 s each: reverse log ≈6–18 s, sensory inventory ≈18–30 s, notice ≈30–42 s, object narrator ≈42–54 s.
- 54–60 s: coverage matrix.

**Files:**
- Builder: `proposals/kf.py`, deterministic.
- Mattes: `proposals/work/mattes.py` and `proposals/work/man.py`.
- Archive frames: `proposals/work/*.png`, extracted with ffmpeg from the Moving Image Archive cache.
- New downloads: about 1.0 MB in `films/sources/exercices-de-style/`. All licences were read from Commons `extmetadata`.

---

## 1 · Narré par la clé (articulated photographic cutout, animation-led)

**Beat and time.** Object narrator, beat 5, "the key is left on the bench", at ≈0:44.
- The camera sits at key height on the bench.
- The visitor is a cutout passing behind it.
- The key speaks in red/black italic captions: « On m'a posée sur le banc. Sa main était tiède… La porte de service n'a pas bougé. »

**Material.**
- **Key:** *Key*, Edna C. Rex, Index of American Design watercolour, 1935–42, NGA 24027. **CC0.** `commons.wikimedia.org/wiki/File:Edna_C._Rex,_Key,_1935-1942,_NGA_24027.jpg`. It is cut off its own cream paper by a colour-distance matte, so the hole in the bow stays open.
  - A first candidate was rejected: D.J. Grant's *Brass Key* (NGA 24024, CC0) has a ward pattern that reads as a swastika.
- **Visitor:** *Portrait d'homme en pardessus et chapeau melon*, Agence Rol (BnF Gallica). **Public domain.** `commons.wikimedia.org/wiki/File:Portrait_d%27homme_en_pardessus_et_chapeau_melon_-_btv1b53000537g.jpg`. Cut out with hand-seeded GrabCut, then a polygon clip.
- **Bench:** handmade cut paper in the cover bus's green and cream, with jittered scissor edges and a fibre tooth.

**Technique SCIONs.**
- #1 Gilliam cutout
- #29 GrabCut
- #32 Forward Kinematics (head/hat layer pinned at the collar; arm layer to come)
- #44 Multiplane Parallax
- #45 Occlusion (the key in front of the bench lip)
- #41 Secondary Dynamics
- #43 Collage Graph Rewriting (key → narrator node)

**How it moves, frame by frame, on 2s at 12 fps.**
- The visitor is a three-layer puppet: hat+head, coat, and a re-cut forearm. He steps through 8 replacement poses: a scale drop of 3% per step, a 6 px bob, and a head tilt of ±2° about the collar pin.
- The hand puppet lowers the key. The key layer then lands with a damped settle (rotation 6° → 0° over 10 frames) and one bounce.
- The bench and ghost word "Je" parallax at 0.4x against the figure as he leaves frame left.
- Captions type in word by word, synced to the key's "breaths" (frame holds).

**Risk.**
- The Rol portrait is front-facing and waist-up, so "walks away" has to be staged as passing, unless a full-figure walking cutout is foraged (more Rol searches are queued).
- The GrabCut fringe on the left sleeve still holds flower debris and needs alpha matting (#31).
- The watercolour key is painted, not photographed. That fits the illustrated edition, but it is a second register beside the photographic visitor.

## 2 · Inventaire des sens (silhouette shadow theatre, animation-led)

**Beat and time.** Sensory inventory, beat 2, "a bell rings", at ≈0:24.
- The witness is the clerk behind frosted ticket-window glass (GUICHET 3, the stencil read backwards).
- The clerk gets only diffusion: a lit pane, a shadow that jerks its head up, a bell's shiver.
- The typed card lists what was sensed, and records the omission in red: « NON PERÇU : ce qu'il a fait de la clé ». This satisfies the fixture: the cause is omitted because the observer had no access, and the omission is declared.

**Material.** All handmade.
- An articulated Reiniger-style silhouette puppet: thigh, shin, shoe, upper arm, forearm, hand, envelope, coat, head and bowler, each a separate polygon on a pin, posed by joint angles in `kf.py:puppet()`.
- A cut-paper window frame.
- A procedural frosted-glass pane (luminous falloff, blur, frost noise).
- A typed inventory card.
- No foraged bytes. Candidate foraged sound for the build: the Moving Image Archive *Communications and Our Town* (1947) belfry clip has real bell audio.

**Technique SCIONs.**
- #2 Reiniger articulated shadow theatre
- #32 Forward Kinematics (joint chain)
- #33 IK (feet pinned to the floor line during the startle)
- #41 Secondary Dynamics (coat skirt, bell)
- #48 State Machine (the clerk's card only gains a line when a sense event fires)
- #47 Sound-to-Action (the bell strike drives the shadow's jerk and the shiver rings)

**How it moves, frame by frame.**
- The puppet is re-posed every frame from keyed joint curves and re-blurred through the glass (blur radius 5 px, rising to 9 px as the figure steps back from the pane).
- On the bell, three frames of rapid head-up and arm-up, then a 6-frame overshoot.
- The bell shadow swings ±8° and decays over 18 frames, with concentric shiver arcs at 70/45/25 % alpha.
- The card line « une cloche — trois coups » types on the first strike, and the timestamp ticks.
- At 18:05 the pane shows only a brief bright glint. No key shape is ever drawn sharp.

**Risk.**
- The silhouette must read as a man with a bowler and an envelope through heavy diffusion. At strong blur it becomes a blob (currently borderline).
- The strip cells in this keyframe are flat swatches; they need small shadow vignettes.
- Being handmade, this has the least tie to the cover's photographic vignettes. It leans on the cover's palette and type instead.

## 3 · Journal à rebours (foraged archive, reverse log; the one archive-led direction)

**Beat and time.** Reverse log, beat 6 shown first, "walks away", at ≈0:08.
- The log types newest-first: 18:07 → 18:00, with the clock running backwards.
- Hand-ruled red arrows in the margin still point from cause to effect (upward, against the reading order). This makes the fixture visible: presentation order changes, causal edges are preserved.
- The vignette strip runs 6 → 1.

**Material.** Moving Image Archive cache, 320×240 shots:
- *Berlin: Symphony of a Great City* (Ruttmann, 1927; published 1927, so public domain in the US since 2023). Clip `b6e217eb`, the empty platform at dawn with two figures walking away (main picture, and beat 1 `berlin-01`).
- *Amateur film, children playing near Hudson* `46cd8d58`: figure on a park seat (beat 5).
- *Bookkeeping and You* (1947) `af625567`: a hand at a machine (beat 4).
- *Verkade's fabrieken te Zaandam* (1930) `95f7caf3`: a lid opened under an iris (beat 3).
- *Communications and Our Town* (1947) `381d177e`: the belfry (beat 2).

Licence status: the Berlin film is PD-US. The others are Prelinger-type ephemeral and educational films served by the Moving Image Archive; their PD status is **unverified per item** and must be checked on each source page before the build. Commons transcodes are the fallback.

**Technique.** Mainly montage, plus:
- #27 Remotion EDL (reversed cut list, with per-shot timecode)
- #43 Collage Graph Rewriting (event ledger → reversed presentation, edges preserved)
- #51 Mouris montage research

**How it moves.**
- Each beat is a shot, cut newest-first.
- Inside each shot the footage plays **forward** (time is not reversed, only order).
- The log line types on the cut, the arrow from its cause draws upward over 8 frames, and the strip cursor steps left.

**Risk.**
- Archive "fit" is loose: no shot contains an envelope or a brass key. Beats 3–5 are stand-ins, so the film's claim rests on the log.
- At 320×240 the material is soft when enlarged.
- It is the least animated direction, and it echoes the existing typographic film's reverse log.

---

## Recommendation

**Build Direction 1, Narré par la clé, as the film's frame.** It is the closest to the reference:
- a real painted key and a real 1910s Paris photograph, cut out and laid on a cream page;
- the green and cream of the cover bus;
- mixed red/black type.

It also performs the most distinctive retelling, the object narrator. Then take **Direction 2's shadow-theatre pane as the sensory-inventory episode** inside the same page grammar. It is the most cinematic, and it answers the fixture's "omission recorded" test directly.

Use Direction 3 only as the 12 s reverse-log episode, with the Berlin 1927 platform as its main plate.

Before the build:
- forage a full-figure walking Rol cutout for the departure;
- alpha-matte the visitor;
- verify the licence of each Moving Image Archive item;
- write `films/credits/exercices-de-style.json`.

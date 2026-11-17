# Exercices de style: SCION swarm plan (build round)

- **Slug:** `exercices-de-style`.
- **Prompt:** `prompts/exercices-de-style.md`.
- **Workspace:** this folder.
- **Media:** `films/sources/exercices-de-style/<role>/` (git-ignored).
- **Revision base:** `proposals/`, round 1.
- **Chosen direction:** **1 · Narré par la clé** (`proposals/kf-1.png`). It is the frame and the TEST SHOT.
- **Folded in:** Direction 2's frosted-glass shadow theatre becomes the sensory-inventory episode, inside the same page grammar.
- **Direction 3 (archive reverse log) is not built as a montage.** The reverse log is animated with the same puppet tableaux. That keeps the film animation-led, and it avoids the stand-in footage that Direction 3 admitted to for beats 3–5. Its one useful find, the 1927 Berlin platform, may appear only as a single PD station vignette if the forager prefers it to a Rol station photograph (§9).

The old `films/exercices-de-style.py` is not used as a base: it is a synthesized-sound typographic film. Its key/man downloads can be reused once their licences are re-verified (key2 is CC0, man is PD; both already have `extmetadata` records in `proposals/work/sources.jsonl`). `key.jpg` (D.J. Grant) is **rejected** because its wards read as a swastika.

---

## 1 · Creative thesis

**Form changes what someone notices in an ordinary event.** One page, one station, six facts, and five tellings: a plain record, then four illustrators who each work under one rule. The page grammar of the illustrated edition stays fixed. The cream page, the ghost word, the mixed red/black title, the vignette strip and the grey band are the "book", and each retelling is a new hand inside it. So the viewer's eye is free to notice only what the *rule* changes:
- **Reverse log:** the order changes, and the causes still point forward.
- **Sensory inventory:** what the clerk could not see is declared in red.
- **Notice:** the event shrinks to boxes. The boxes are shown empty first.
- **Object narrator:** what gains force is warmth, a coat seen from below, and a door that does not move.

**What would make it bland:**
- five slides of the same sentence in different fonts;
- a puppet that slides instead of walking;
- a key that is simply *placed*, not dropped and settled;
- captions that announce the rule instead of letting it act on the telling.

## 2 · Defining beat and comparison baseline

**Defining beat: TEST SHOT S5c, 51.5–58.0 s, the key narrates beat 5.**
- The camera sits at key height on a cut-paper bench in the green and cream of the cover bus.
- The real CC0 painted key (Edna C. Rex, NGA 24027) is lowered into frame. It lands with a damped settle: 6° → 0° over 10 frames, with one 3 px bounce on frame 4, and a clink.
- The real PD Agence Rol visitor, cut out and articulated, then **walks away**. His legs swing, he bobs and he recedes, all in the midground, toward frame left.
- The service door at frame right stays shut.
- The key's first-person captions type word by word: « On m'a posée sur le banc. / Sa main était tiède, / puis il n'y eut que son manteau. / *La porte de service n'a pas bougé.* » (the last line in red).

**When the beat works, the viewer can point to three things:**
1. the key is the camera: we are low, on the wood, and he is large and then small;
2. the hand's warmth and the receding coat are new details that no other telling has;
3. the door is the same door as in the baseline, and it is still closed.

**Comparison baseline: S1 "Le registre", 3.0–13.0 s.**
- The same six beats in plain chronological order.
- The same puppet, the same bench and the same door, seen in a neutral eye-level medium-wide shot.
- One plain roman caption per beat. Beat 5 is the line « 18:06 Le visiteur laisse la clé sur le banc. » over a 1.6 s neutral pose, with no settle and no narration.

The baseline frame at 11.0 s and the TEST SHOT frame at 54.0 s are exported side by side (`films/stills/exercices-de-style-beat5-pair.jpg`). The difference between them *is* the claim.

**Negative fixture (not in the film; run by the verifier):** a key-narrator variant whose last line is « Il est revenu me chercher. » It invents a new ending, and `verify.py` must reject it (prompt §7).

## 3 · Theory

### 3.1 Compact Lineage Genome

| field | value |
|---|---|
| source media | Queneau, *Exercices de style* (Gallimard 1947): prose, 99 retellings of one S-bus incident. The later illustrated Gallimard edition has contributions by many illustrators; its cover is our reference. *The edition year is uncertain here; the BnF anchor identifies it but it was not read in this session.* |
| target media | A ≈66 s film, 960×540, 24 fps, animated on twos (12 drawings/s) for the puppets. It has a cream printed-page grammar, foraged B&W photographic cutouts, a foraged painted key, handmade cut paper, a handmade silhouette puppet and a handmade printed notice. Captions are the voice. Sound is foraged (bell, steps, room) plus kit impacts. |
| preserved relation | One fixed mundane incident and many rule-bound retellings. An anthology of "illustrators" on one book grammar. The rule can be inferred from what it does to the telling. |
| optics change | The illustrator-per-exercise becomes a *technique-per-variant*: cutout puppetry, shadow theatre behind frosted glass, a printed form, and an object's point of view. The lens is the operator, e.g. key height in the test shot, or diffusion for the clerk. |
| formalism change | Each style becomes a typed operator on a frozen event ledger, with machine-checked coverage and a closing coverage matrix on screen. |
| concept change | The bus becomes a station (the prompt's common seed): envelope, bell, brass key, bench, closed service door. |
| sound change | The spoken or written voice becomes captions. The reverse operator is carried into sound: the sound events play in reverse *order*, and each one plays forward. The key's point of hearing is muffled through paper until the tear. The clerk's point of hearing is through glass. The notice has typing and a stamp only, and it declares that the bell is "recorded, not heard". |

**Formation epochs (weight 0–100, with reason):**
- **Oulipo / Queneau constraint writing, 1947–1960: 90.** The operators and the fixed incident are the work's core.
- **Illustrated-book cover design (Gallimard Jeunesse illustrated edition): 75.** The page grammar is the aesthetic target. *Exact date uncertain.*
- **Paris press photography (Agence Rol, 1904–1937): 50.** It is the actual material of the visitor. A 1910s overcoat and bowler belong to Queneau's world.
- **Gilliam cutout animation, 1969–1974: 60.** Photographic fragments on pivot joints, with held frames and impact sound.
- **Reiniger silhouette theatre, 1919–1926: 55.** The sensory episode is a shadow on glass.
- **Index of American Design watercolour, 1935–1942: 35.** The key is a painted record of a real object. It sits in a second register, which suits an illustrated edition.
- **Computational coverage checking: 40.** `verify.py` and the matrix make the formal claim testable.

### 3.2 Olog

**Types:**
- **◻ Incident** `I@rev`, frozen in `incident/ledger.json`, with a sha256 recorded in `rev`. It has:
  - **events** E1–E6, each with `id, t, actor, action, object, outcome`:
    - E1 18:00 visitor *arrives* at the empty station, holding a sealed envelope. Outcome: visitor present, envelope sealed.
    - E2 18:02 the station bell *rings*. Actor: bell. Outcome: sound.
    - E3 18:04 visitor *opens* the envelope. Outcome: envelope torn open.
    - E4 18:05 visitor *finds* a brass key in it. Outcome: key in hand.
    - E5 18:06 visitor *leaves* the key on the bench. Outcome: key on bench.
    - E6 18:07 visitor *walks away*. Outcome: visitor absent.
  - **state fact** F7: the service door is closed at every t in [18:00, 18:07]. It is never opened.
  - **causal edges** (typed):
    - E1 →enable E3 (he has the envelope);
    - E3 →enable E4 (access to the contents);
    - E4 →enable E5 (he holds the key);
    - E5 →precede E6 (he leaves hands-free; a temporal edge, declared);
    - E2 →cue E3: a *weak* edge, **declared uncertain**. The bell may prompt the opening; no telling may assert it as a cause.
  - **roles:** visitor; bell; key (object); bench (place); service door (witness object); clerk (an observer *added by the sensory operator*, behind GUICHET 3, who is not an actor in the incident).
- **◻ StyleOperator** `O = {id, input_domain: Incident@rev, protected: set⊆{E1..E6,F7,edges}, mutable: dims⊆{order, access, format, voice, timing, sound-order}, accept: predicate}`. The four operators:
  - **O_rev** (reverse log). Mutable: {order, sound-order}. Protected: all events, F7, all edges. Accept:
    - the presentation order is exactly [E6..E1];
    - the displayed timestamps strictly decrease;
    - every drawn arrow goes from cause to effect (on screen: from the lower line up to the higher line);
    - each tableau plays forward in time.
  - **O_sense** (clerk's sensory inventory). Mutable: {access}. Protected: E1, E2, E3, E6, F7 as *perceived*. Accept:
    - every event is either asserted as a percept (sound, shadow, glint) or listed in `omissions` with `reason: "no access"`;
    - E4 and E5 may be reduced to percepts ("un éclat", "métal sur bois"), and their object identity ("clé") must appear in the red NON PERÇU line;
    - no cause is asserted.
  - **O_notice** (rigid-format notice). Mutable: {format}. Protected: all events, F7. Accept:
    - every row matches the fixed field grid `N° | HEURE | LIEU | OBJET | ACTION | ÉTAT`;
    - no free sentence outside the grid, except the one stamp;
    - empty boxes are visible before they are filled.
  - **O_object** (narrated by the key). Mutable: {voice, access}. Protected: E3–E6 and F7 as the key perceives them; E1–E2 as darkness and muffled sound. Accept:
    - every caption is in the key's first person (je / me / m');
    - no claim lies outside the key's access;
    - the last event is E6 and F7 is affirmed;
    - no event after 18:07.
- **◻ Retelling** `R = Retell(O, I@rev) = {variant_id, operator, base_rev, claims:[{text, events:[Eid], kind: assert|percept|omit}], omissions:[{event, reason}], timing:[{event, t_in, t_out}]}`. It merges into `incident/anthology.json` by `variant_id`.

**The central operation, `Retell(O, I@rev) → R`:**
- **Typed preconditions:**
  1. `I.rev` equals the frozen ledger hash; if the facts change, a new rev is made and every R is reopened;
  2. `O.input_domain` accepts I;
  3. `O.protected ⊆ facts(I)`;
  4. `O.mutable ∩ protected = ∅`;
  5. the variant has exactly one primary operator.
- **Observable consequences:**
  - (a) `coverage(R) ∪ omissions(R) ⊇ O.protected`. On screen, the closing matrix ticks each cell, or circles it red as "omis · déclaré".
  - (b) `edges(R) = edges(I)` for O_rev. They are visible as the upward red arrows.
  - (c) final event of R = E6, and F7 is asserted. The door layer is pixel-identical in every frame where it appears.
  - (d) the dimension named in `O.mutable` is measurably different from the baseline's; the others are equal.
- **Counterexample (must fail):** O_object' outputs « …puis il est revenu me chercher. » This claims an event E7 that is not in I. Then `final_event(R) ≠ E6`, which violates (c), and `verify.py` exits non-zero with `NEW_ENDING`. A second counterexample: an O_rev that draws its arrows in reading order (downward, E6→E5…) reverses the causal edges, which violates (b) and gives `EDGE_REVERSED`.

**Equivalence and divergence across replays or views:**
- **Baseline ≡ reverse log** on the fact set and the edge set (structurally verified by `verify.py`). They **diverge** only in presentation order and sound order.
- **Baseline ≡ notice** on the fact set. They **diverge** in sentence constraint.
  - *Redundancy risk:* the notice can collapse into the baseline, since both list facts in order.
  - *Repair rule:* the notice must show the empty grid first and reduce every event to fields ("ÉTAT : fermée", "SUITE DONNÉE : néant"), with no verbs of feeling.
- **Sensory inventory** diverges in its fact set: the key's identity is replaced by "un éclat". That omission is recorded.
- **Key narrator** diverges in access: E1 and E2 appear only as darkness and a muffled bell.
- **TTL** is 2 (default). This is not interactive work, so the invitation/action items do not apply.

## 4 · Invariants

1. **INV-LEDGER.** All variants cite `ledger.json@rev`. Facts are never edited downstream.
2. **INV-COVER.** Each variant covers E1–E6 and F7, or lists each omission with a reason (`verify.py`).
3. **INV-ENDING.** No variant ends anywhere but E6 with the door closed. There is no E7.
4. **INV-EDGES.** The reverse log's arrows equal the ledger's edges in direction. E2→E3 is drawn dotted, as "uncertain".
5. **INV-DOOR.** The handmade door layer is one RGBA asset, never transformed, and pixel-identical in every frame where it is visible. It is the visual F7 (measured by a frame-hash test).
6. **INV-PUPPET.** It is the same visitor rig in S1, S2 and S5 (S3's silhouette is rotoscoped from it). Bone lengths are constant, the head never detaches from the collar pin, and the feet do not slide during foot contacts (FK/contact test from #32/#33).
7. **INV-ONE-OP.** Each variant has one primary operator. Equivalent effects count as one approach.
8. **INV-MATERIAL.** Every pixel is foraged (credited, PD/CC0/CC BY/BY-SA) or handmade. No filter fakes a photographic look, no faux grain, and no reference pixels.
9. **INV-BASELINE.** S1 is rendered with no operator. It is kept as `exercices-de-style-baseline.mp4` (the S1 window) for comparison.

## 5 · Aesthetic target (from `assets/references/styleBook.webp`)

Sampled with PIL from the 400×599 reference.

| element | measured | what the film does |
|---|---|---|
| page ground | median **#fddb8c**. The 5–95 % range runs from the page's yellow at about #fdd887 to a light cream at #ffefb2. L\* is about 89. Warm butter, *not* pale cream. | Page base **#fddb8c**, with a soft handmade vertical gradient to #fee498 (the cover is lighter at its top-centre). The keyframe `kf-1` page (#fdf0c5) is **too pale**; correct it. |
| ghost type | **lighter** than the page: #fdefb1, L\* about 94.5 against 88.6. Huge, cropped by the page edge, in a light condensed serif and script. | Ghost word per episode (« Gare », « Rebours », « Sens », « Avis », « Je ») at 360–480 px in #fdefb1, *lighter* than the page. `kf-1` made it darker (#f0e0a0); fix that. |
| title red | **#d6280a**, a hot vermilion. The letters are condensed, with jumping sizes and baselines and mixed faces. | Episode titles are set letter by letter in mixed faces: Instrument Serif italic, Liberation Serif bold, FreeSans. Each letter gets its own size (±25 %) and baseline (±8 px). The colour alternates red **#d6280a** and black **#191304** by word, as on the cover's « Exercices » / « de Style ». |
| black | **#191304**, a warm black | All ink text |
| bus green | **#283716** dark bottle green, with cream window bands and a yellow side panel | The cut-paper bench (slats #283716 to #2f4a20, with a cream #efe6c8 rail) and the service door (green with a cream stencil « SERVICE »). Every one is cut-paper polygons with jittered scissor edges and a darker cut edge. The texture is real paper tooth built procedurally on the flat colour, never noise grain over photographs. |
| vignette strip | A row of about 12 small square cells, about 5.7 % of page height, each a different illustrator, sitting directly on the grey band, with thin cream gutters | A strip of six cells (one per beat), 44×44 px, at y ≈ 382–426 directly above the band. Each cell shows a thumbnail **rendered from that beat's own frame** in the current episode, so the strip changes by episode, like a different illustrator per cell. The current beat is ringed in red. |
| grey band | **#8e847b**, a warm grey (std about 18: printed and slightly mottled), with a white humanist sans on it. About 30 % of the portrait cover. | The band is 108 px (20 %, adapted for 16:9) in #8e847b, with a light paper mottle. The episode name is in white Instrument Sans at 40 px, and the clock / « EXERCICE n · OPÉRATEUR » in small caps at 15 px. `kf-1` used a neutral #92928e; warm it. |
| light | Flat print light. The only shadows are a small product-shot drop shadow under the bus and soft lift-shadows under pasted pieces. | Cutouts get a 6–10 px soft offset shadow (paper lifted off the page). There is no vignette and no lens effect. In S3 alone, the light comes from *behind* the frosted pane: that is the shadow-theatre exception, declared. |
| texture | Printed card: smooth, with a faint halftone in the vignettes | The photographs keep their own silver grain (real). The key keeps its watercolour wash (real). The paper and band get a mottle from the paper fibre. **No synthetic film grain.** |
| framing and scale | Big empty page. The title sits in the middle third; the object (the bus) is small and pushed to the right edge. | The text block is upper right or centre. Figures are small against a lot of page; only the TEST SHOT goes close (key height, the key about 45 % of frame width). |
| pacing | (a still) | A calm book rhythm: held tableaux at 1.4–2 s per beat, puppets on twos, typing at about 14 chars/s, hard cuts between episodes on a page-turn wipe. |

**Medium:** printed book page plus pasted real photographs and painting, i.e. collage on a cover. The photographic material must be **genuinely black-and-white**: chroma of the visitor cutout below 6 before any warm tone. Its only grade is a slight sepia-toward-page tint (≤ 8 %), which unifies it with the butter page. The vignettes in the reference are colour illustrations. Ours are frames of our own scenes, so they are mixed media too.

**The look has to come from real material:**
- a real silver-print figure;
- a real watercolour key;
- cut-paper polygons in sampled colours;
- real typesetting.

Never trace, copy or paste the reference itself. The cover's title, the bus and the illustrations do not appear. The only echo is the grammar: colours, layout bands and type behaviour.

## 6 · Technique SCIONs (from `swarms.json`, read in full)

1. **#1 Terry Gilliam: Comic Cutout Metamorphosis.** Real photographic fragments on pivot/card joints, held frames and impact sound, and a substitution object (key → narrator). This is the whole cutout grammar of S1, S2, S4 and S5. Its bar applies: paper boundaries look intentional, each collision/hold/reveal lands on its frame, and every fragment is linked to its source.
2. **#29 GrabCut: Cutout Extraction Swarm** (with **#31 Alpha Matting** as its edge pass). The visitor (a full walking figure if found) and the key must be cut from real scans. Its bar applies: no background islands, fingers retained, the halo isolated, and true RGBA plus failure masks exported. The flower debris on the Rol portrait's left sleeve is a known failure to fix with a trimap and matte.
3. **#2 Lotte Reiniger: Articulated Shadow Theater.** S3, the clerk's sensory inventory. A silhouette puppet with pinned joints, 12 fps, behind diffusion. Its bar applies: the action reads with colour removed, limbs never detach, and shadows do not merge into blobs at their blur.

**Supporting methods, applied within these (their prompts were read):**
- **#32 Forward Kinematics.** The walk: hip → thigh → shin → shoe, with the collar pin for the head and the wrist for the envelope and key.
- **#41 Secondary Dynamics.** The key's settle and the coat hem lag. Energy must decay to zero.
- **#44 Multiplane Parallax.** In the test shot, the near bench lip moves 1.0×, the key 1.0×, the visitor 0.55× and the ghost « Je » 0.25×. Near moves more than far.

**Applied, shot by shot:**
- **S1, S2:** #29 cutout pieces, #1 pivot puppet, #32 FK poses for the six beats (arrive-walk, startle at bell, tear, find, lay down, walk off).
- **S3:** #2 silhouette.
  - The puppet is *handmade*: a polygon contour traced (rotoscoped) from the forager's walking figure matte. It is split into head + bowler, torso + coat, upper and lower arms, hand + envelope, thighs, shins and shoes, all on pins.
  - Joint-angle curves are keyed on an exposure sheet.
  - It is composited behind a procedural frosted pane, with blur 5 → 9 px as he steps back.
  - The bell strike drives a 3-frame head-up and a 6-frame overshoot (#47-style sound-to-action, kept inside #2).
- **S4:** #1 substitution. The key cutout is clipped to the notice; it drops 40 px and settles (#41).
- **S5a–b:** handmade straight-ahead tear: an envelope-paper edge, re-cut every 2 frames, which opens a rip of light, drawn frame by frame.
- **S5c (TEST):** #29/#31 pieces, #1 + #32 walk on twos, #41 key settle, #44 three-plane parallax.

## 7 · Timed shot list (the Hard proof, prompt §6)

Format: 24 fps, 960×540, **66.0 s total**. The page grammar is present in every shot: page, ghost, mixed-face title, strip, band.

| shot | time | on screen | heard | material |
|---|---|---|---|---|
| **S0 Titre** | 0.0–3.0 | The butter page. The ghost « Gare » slides 20 px (back plane). The mixed red/black title « Une gare, six faits » sets letter by letter. The band reads « d'après Raymond Queneau · cinq manières ». Six empty strip cells. | Foraged room tone (empty hall) fades in | page, type, band: HANDMADE. Room tone: FORAGED (MIA clip with source sound, e.g. an empty hall or station; or Commons CC0/PD) |
| **S1 Le registre (BASELINE)** | 3.0–13.0 | Eye-level medium-wide. A foraged B&W station photograph sits upper left in a deckled-edge frame (the "window"). On the page are the green bench and the closed service door (right). The visitor puppet performs E1–E6 in order, 1.6 s per beat: walks in from the right and stops, looks up at the bell, tears the envelope, holds up the key, lays it on the bench (no settle, just placed), walks out left. One plain roman caption per beat at the top right (« 18:00 Un visiteur arrive à la gare vide, une enveloppe cachetée à la main. » … « 18:07 Il s'en va. La porte de service reste fermée. »). Each strip cell fills with a thumbnail of its beat. The band clock reads 18:00 → 18:07. | Steps (foraged), the bell at E2 (foraged real bell), a paper tear (foraged or kit), a key on wood (kit click), receding steps | Visitor: FORAGED Agence Rol full figure (Commons, PD) cut and rigged. Station: FORAGED (Commons Agence Rol / Gallica gare or salle d'attente, PD, or LoC Bain "railroad station" with no known restrictions). Bench, door, frame: HANDMADE cut paper |
| **S2 Journal à rebours** | 13.0–24.0 | The ghost « Rebours ». The log types **newest first**: 18:07, 18:06 … 18:00, one line per 1.4 s, each beside a small held tableau of that beat's puppet pose, which **plays forward** for 1.2 s. The band clock counts **backwards**. The strip cursor steps 6 → 1. At 21.5–23.5, hand-ruled red arrows draw *upward* from cause to effect over 8 frames each: E1→E3, E3→E4, E4→E5, E5→E6, and E2→E3 dotted, labelled « incertain ». | The S1 sound events **in reverse order**, each played forward: receding steps, clink, tear, bell, arriving steps. A pen scratch as each arrow draws. | Puppet: FORAGED cutout (the same rig). Arrows, log: HANDMADE |
| **S3 Inventaire des sens** | 24.0–36.0 | The ghost « Sens ». A cut-paper ticket window, with « GUICHET 3 » stencilled and read backwards, holding a lit frosted pane. Behind it the silhouette visitor arrives, jerks his head up at the bell (3 frames up, 6-frame overshoot), tears (the shadow's arms part), shows a brief bright **glint** at 18:05 (no key shape is ever sharp), stoops at the bench, and leaves. A typed inventory card adds a line only when a sense event fires: « pas sur la pierre · une ombre à chapeau », « la cloche — trois coups · l'ombre lève la tête », « papier déchiré », « un éclat, bref », « métal sur bois », « les pas s'éloignent · la porte de service : aucun bruit ». At 33.0–36.0 the red line reads « NON PERÇU : ce qu'il y avait dans l'enveloppe ; ce qu'il a laissé sur le banc. » | The real bell heard through glass (the same foraged recording, low-passed), steps, tear, clink, room tone. The sound drives the shadow's action. | Silhouette puppet, pane, window, card: HANDMADE. Contour rotoscoped from the FORAGED walking figure. Bell: FORAGED |
| **S4 Avis** | 36.0–46.0 | The ghost « Avis ». A printed notice card « AVIS — OBJET TROUVÉ ». The full grid of empty boxes is shown for 1.5 s first: `N° | HEURE | LIEU | OBJET | ACTION | ÉTAT`, six rows. Then the fields fill row by row in mono type: e.g. « 5 | 18:06 | banc, quai | clé laiton | déposée | — », « 6 | 18:07 | sortie | — | départ | porte de service : FERMÉE ». The foraged key cutout drops onto the card under a drawn paper clip and settles. At 44.0 a red rubber stamp « SUITE DONNÉE : NÉANT » lands, with a 2-frame squash. A footnote in the grid: « cloche : consignée, non entendue ». | Typewriter clicks (kit), the stamp thud (kit thud), and **no bell**: that silence is declared in the grid | Notice, stamp: HANDMADE. Key: FORAGED CC0 painting |
| **S5a Narré par la clé: dans l'enveloppe** | 46.0–49.0 | The ghost « Je ». The page darkens to the inside of the envelope (lamp-through-paper brown). The key's captions are in cream italics: « Je ne voyais rien. Une cloche, très loin, à travers le papier. » | The same bell, heavily muffled (low-passed): E2 from inside | HANDMADE envelope paper. Bell: FORAGED |
| **S5b la déchirure** | 49.0–51.5 | A torn edge of light opens across the frame, **straight-ahead frame by frame**: the fibre edge is re-cut every 2 frames. A hand (a cut piece of the Rol hand) slides the key out. Caption: « Puis une déchirure, et la lumière. Une main m'a sortie. » | Paper tear (foraged) | HANDMADE tear. Hand: FORAGED cutout piece |
| **S5c TEST SHOT: beat 5** | 51.5–58.0 | At key height, the green bench lip runs across the lower third. The key is lowered in by the hand and **lands** (rotation 6° → 0° over 10 frames, one bounce, 2-frame hold), and the hand withdraws. The visitor in full figure **walks away** to frame left in the midground: an FK walk on twos with alternating legs, at least 2 full steps, the coat hem lagging, the scale falling 3 % per step, and a 6 px bob. Three-plane parallax: bench 1.0, figure 0.55, ghost « Je » 0.25. The closed door is at frame right. The captions type word by word, red/black italic, upper right: « On m'a posée sur le banc. / Sa main était tiède, / puis il n'y eut que son manteau. / *La porte de service n'a pas bougé.* » The strip ring is on cell 5. | A clink at the landing (frame-exact), steps synced to foot contacts and receding (gain and low-pass falling), then room tone | Key, visitor: FORAGED (CC0 / PD) cut and articulated. Bench, door: HANDMADE |
| **S5d** | 58.0–60.0 | Hold: the key alone on the bench, the door shut, and the strip ring moving to 6. The last caption remains. The final 0.5 s has only room tone. | Steps gone, room tone | – |
| **S6 Matrice** | 60.0–66.0 | The coverage matrix as a printed table on the page: rows E1–E6 + « porte fermée », columns registre / rebours / sens / avis / clé. Ticks type in. The *rebours* column shows its order numbers 6..1. The *sens* × E4/E5 cells are circled red « omis · déclaré ». The *clé* × E1/E2 cells read « ouï, non vu ». The band reads « même incident · cinq règles ». | One bell stroke at 60.0 (foraged), then a declared silence from 63 s | HANDMADE |

**Captions:** French, as in the book. No English line on screen (it would clutter the band); English goes in the notes and credits only.

**Duration:** ≤ 75 s. **Size:** ≤ 6 MB.

## 8 · Sound

**Foraged first: MIA clips with source sound.**
- Candidate `381d177e` *Communications and Our Town* (1947): a belfry with bells. Extract one clean strike.
- An empty-hall or station room tone from MIA.
- Steps on stone and a paper tear: MIA, or Commons PD/CC0/CC BY recordings.

**Kit synthesis only where nothing suitable is found:** typewriter `click`, stamp `thud`, key `click` on wood. Each is declared in the notes. One bell recording is used everywhere, processed by the episode's point of hearing (full / reversed order / through glass / absent-declared / muffled), so the *sound* carries the operator (prompt §8).

## 9 · Swarm units (prompt §5)

These are merged for coupling. The montage editor/assembler and the independent reviewer are run separately by the workflow.

### U1 · incident-editor + constraint verifier (writers merged)

- **Freeze first.** Write `incident/ledger.json` with E1–E6, F7, the typed edges (E2→E3 marked uncertain), roles and `rev` = sha256 of the canonical JSON.
- **Write the five texts** under their operator cards (`incident/anthology.json`, by variant_id, `base_rev`): baseline, reverse, sense, notice, key. Each claim is linked to event IDs and has a `kind`, and the omissions carry reasons. Add per-caption timing that matches §7.
- **Write `incident/verify.py`.** It checks INV-COVER, INV-ENDING, INV-EDGES, INV-ONE-OP, the notice grid regex, key first-person voice and the descending timestamps, and it runs the two counterexamples (NEW_ENDING, EDGE_REVERSED), which must fail. Its result goes to `incident/coverage.json`, which also feeds the S6 matrix.
- **Merge note.** The four writers are merged under one owner because the captions are short and coupled to the timing. The independence of the operators is checked by `verify.py`'s operator-signature test instead: each variant differs from the baseline in exactly its declared mutable dimension. That merge is recorded.
- **Output:** `films/swarm/exercices-de-style/incident/anthology.json` (plus `ledger.json`, `verify.py`, `coverage.json`). Media: none (`sources/exercices-de-style/incident/` holds only the counterexample fixtures).

### U2 · forager + cutout surgeon + rigger (#29, #31, #32)

- **Forage.** MIA cache first, then Commons and LoC.
  - **The visitor:** a full-figure **walking** man in overcoat and bowler. Try Agence Rol / Gallica on Commons ("Agence Rol" + passant, boulevard, homme marchant, chapeau melon) and the LoC Bain News Service, 1910s, "No known restrictions". He should walk sideways or three-quarter away, with legs visible below the coat. The existing waist-up Rol portrait is the fallback for close and medium shots.
  - **The station:** one B&W empty station, platform or waiting-room photograph with a bench, PD.
  - **Sound:** bell, room tone, steps, tear (§8).
  - Re-verify `key2.jpg` (CC0) and `man.jpg` (PD) from `extmetadata`.
- **Cut.** Run GrabCut with box + scribble seeds, then a trimap, alpha matting and colour decontamination. Remove the flower debris from the sleeve. Then split the figure into articulated RGBA pieces: hat+head, torso+coat, coat hem, upper arm, forearm+hand, thighs, shins+shoes. Joints overlap with round caps; occluded joint regions are filled as *flagged inventions*.
- **Rig.** Write the FK rig (`rig.json`: pieces, pivots, parents, bone lengths, z-order), plus a 12-drawing walk cycle and the six beat poses as joint-angle tables.
- **Key.** Cut the key with its bow hole open (reuse `key_cut.png` if it passes the #29 bar).
- **Ledger.** Record every item with title, author, licence, licence_url, source_url, file_url, bytes and used_as.
- Keep new downloads under 75 MB.
- **Output:** `films/swarm/exercices-de-style/forage/evidence.json`, plus `forage/rig.json` and a draft `films/credits/exercices-de-style.json`. Media: `films/sources/exercices-de-style/forage/`: originals, `*_rgba.png` pieces, masks, failure masks, wavs, and a contact sheet `cutout-check.jpg` against light, dark and page grounds.

### U3 · animator + page-maker (#1, #2, #41, #44; handmade objects)

- **Build the handmade page objects** as reusable RGBA or code:
  - the butter page with its gradient and fibre mottle;
  - ghost words;
  - the mixed-face title setter;
  - the green cut-paper bench and the **single fixed door asset**;
  - the deckled vignette frame, ticket window and frosted pane;
  - the notice grid and stamp;
  - the envelope interior and the straight-ahead tear sequence.
- **Build the Reiniger silhouette puppet** for S3, rotoscoped from U2's walking matte, with its exposure sheet.
- **Write the motion curves** as exposure sheets in JSON, frame-indexed at 24 fps on twos: the S1 beat performances, the S3 shadow, the S4 key drop, and the S5c walk, key settle and parallax.
- **Render a playable test shot**, S5c at 6.5 s with sound, through `kit.py` (no edits to kit), as `sources/exercices-de-style/anim/test-shot.mp4`. Also export the beat-5 pair still against the S1 frame, and an aesthetic side-by-side against the reference.
- **Library.** Provide `anim/es_lib.py` with the functions the editor imports (page, title, strip, band, bench, door, puppet draw-from-rig, silhouette, notice, tear).
- **Dependencies:** U2 `rig.json`. Start with the proposal's `man_cut`/`key_cut` and swap when U2 delivers. U1 `anthology.json` supplies the caption text and timing.
- **Output:** `films/swarm/exercices-de-style/anim/exposure.json` (plus `anim/es_lib.py`). Media: `films/sources/exercices-de-style/anim/` (test-shot.mp4, stills, RGBA objects).

**Editor (run separately):** writes `films/exercices-de-style.py` from `es_lib.py`, `rig.json`, `exposure.json` and `anthology.json` per §7. Also: mix the sound, render, write `films/notes/exercices-de-style.txt` (60–110 words, forage vs handmade) and finalise the credits.

## 10 · Acceptance bar (falsifiable; for a fresh critic watching the film and reading the ledger)

1. **Shared incident, structurally verified.**
   - `python3 incident/verify.py` exits 0 on `anthology.json@rev`.
   - Every variant covers E1–E6 + F7, or lists each omission with a reason.
   - Both counterexamples (« Il est revenu me chercher. »; downward arrows) are rejected, with the codes NEW_ENDING and EDGE_REVERSED.
   - The S6 matrix on screen equals `coverage.json`, cell for cell.
2. **Reverse log keeps causes, perceptually and by measurement.**
   - In 13–24 s the on-screen timestamps run 18:07 → 18:00 and the band clock decreases.
   - Five arrows are visible, each going from a cause line up to its effect line, with E2→E3 dotted.
   - Inside each tableau the visitor moves *forward* in time (no reversed motion).
   - The sound events play in reverse order: the steps are heard before the bell.
3. **Sensory omission recorded.**
   - In 24–36 s, no frame shows a sharp key shape (only a glint).
   - The red « NON PERÇU » line is legible for ≥ 2 s.
   - The shadow's head-up starts within 2 frames of the bell's onset.
   - Watched with colour removed, the silhouette reads as a man in a bowler, holding an envelope.
4. **Rigid notice.** In 36–46 s the full empty grid is visible for ≥ 1 s before any field fills, and every filled row has exactly the six fields `N° | HEURE | LIEU | OBJET | ACTION | ÉTAT`.
5. **TEST SHOT animated, frame by frame (51.5–58 s).**
   - The key goes through ≥ 8 distinct settle frames, and the energy decays to a still pose before 54 s.
   - The clink coincides with the landing frame (±1 frame).
   - The visitor's legs alternate through ≥ 2 full steps, each foot contact paired with a step sound, and his height decreases monotonically.
   - The near bench moves more than the figure, which moves more than the ghost word.
   - All captions are in the key's first person.
   - The beat-5 pair still (S1 at 11.0 s vs S5c at 54.0 s) shows the same bench, door and visitor, from different heights.
6. **Aesthetic A: palette, by side-by-side comparison.** A sheet of the frames at 2.0, 8.0, 30.0, 40.0 and 54.0 s, each placed beside `styleBook.webp` (resized to equal height).
   - The median page colour of each frame, sampled outside figures and text, is within ΔE76 ≤ 10 of the reference page median #fddb8c.
   - The grey band median is within ΔE76 ≤ 10 of #8e847b.
   - The ghost word is *lighter* than the page (as in the reference).
   - The title red is within ΔE76 ≤ 15 of #d6280a.
   - Judged perceptually: the critic would shelve the frames as pages "of the same book".
7. **Aesthetic B: grammar and material, by side-by-side crop.**
   - Next to the reference's title, strip and band crops, every episode frame shows: a mixed-face red/black title with jumping baselines; a strip of six square cells sitting directly on the band; a warm grey band with white sans.
   - The visitor cutout's chroma is below 6 before tint (genuine B&W silver print).
   - The key shows its real watercolour wash.
   - There is no synthetic grain, no vignette filter, and no pixel copied from the reference.
8. **Material, credits, format.**
   - Every foraged item on screen or in the mix appears in `films/credits/exercices-de-style.json` with a PD, CC0, CC BY or CC BY-SA licence read from its source metadata, and `forage/evidence.json` matches it.
   - The door layer's hash is identical in every frame where it appears (INV-DOOR).
   - Duration is 60–75 s, the file is ≤ 6 MB, and the sound is audible (not silent) except for the declared silences.
   - Shown the four variants unlabeled, a reader can name the stable fact (the closed door, the key left on the bench), a new detail that gained force, and the most redundant pair. The predicted answer is baseline/notice; if it is any other pair, record it.

### 10-R1 · withdrawn (repair round 2, 2026-11-17)

The round-1 re-anchoring of the §10.5–§10.6 S5 numbers to 58.667 s is withdrawn; the bar stands exactly as written above. The film was retimed instead (anthology `timing_revision`, repair 2): S5a 46.0–49.333, S5b 49.333–51.5, S5c starts at 51.5 s, the key lands at 52.75 s and is still from 53.167 s (before 54.0 s), and the beat-5 pair is S1 11.0 s vs S5c 54.0 s. S5c continues past 58.0 s (to 61.75 s) only so that the visitor actually exits and the last key captions type at 14 chars/s; S5d 61.75–63.75, S6 63.75–69.75 (total 69.75 s, inside §10.8's 60–75 s). Nothing in §10 is revised.

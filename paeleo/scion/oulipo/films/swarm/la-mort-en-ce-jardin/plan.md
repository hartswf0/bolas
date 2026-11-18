# SCION swarm plan: la-mort-en-ce-jardin ("Material resistance and surreal interruption"), plan r1

Revision: plan-r1, 2026-11-16. Director. The prompt `prompts/la-mort-en-ce-jardin.md` was read in full (sections 1–10 and the source anchors). Chosen direction: **Direction 1, "Trois sur la planche"** (`proposals/kf-1.png`). It is kept, and pushed toward the reference: a denser, photographic, wet mid-grey jungle built from foraged plant and root photographs as real multiplane layers.

Inputs at this revision (immutable source IDs):
- `assets/references/bunuel.webp` (MoMA / Photofest publicity still). It is studied and measured only, never copied, traced or pasted.
- `proposals/kf-1.png` and `proposals/kf.py`: these hold the existing FK puppet code, which may be reused and improved.
- `films/sources/la-mort-en-ce-jardin/shoe_lacma_bar.jpg` and `shoe_lacma_oxford.jpg`. The proposals stage recorded both as PD; that must be re-verified.
- `mangrove_a/b.jpg` were rejected as colour and sunlit. They may serve as greyscale texture only if U1 judges them usable.
- The earlier `films/la-mort-en-ce-jardin.py`, which used the kit_cinema_b look (coloured coats, a brass key), is **superseded**. No code or timing is inherited from it. The brass key is dropped: one interruption, not two.

---

## 0. AESTHETIC TARGET (reference `assets/references/bunuel.webp`, 1000×677, 1.48:1)

Catalogue entry `cinema.json` slug `la-mort-en-ce-jardin`: "Two people shelter among jungle roots in a black-and-white publicity still", MoMA / Photofest. It has no gallery.

What it shows: a close two-shot. A woman with wet, tangled pale hair kneels and looks down at a man lying among roots. He wears a patterned headband. Mud and sweat film their faces, shirts and hands. Behind them rise a giant buttress-root trunk, a hanging liana, big heart-shaped leaves and a fern at the right. A diagonal root or trunk crosses the lower left and lower right. There is no sky.

Measured with PIL/numpy (luma):

| property | reference | kf-1 (chosen keyframe, picture area) | what the film must do |
|---|---|---|---|
| Medium | silver-gelatin b/w production still | grey card plus soft 320×240 film stills | b/w photographic plates plus real-looking paper; no colour |
| Neutrality | mean RGB 112.3/112.3/112.3, chroma 0.0 | neutral | exact neutral; mean \|R−B\| ≤ 2. No cream kit PAPER and no sepia. |
| Tonal range L p1/p5/p25/p50/p75/p95/p99 | 35/38/59/105/161/206/229 | 26/34/59/84/109/152/190 | lift blacks to ≥ 30. **Raise highlights**: kf-1 lacks the reference's p95 ≈ 206 (wet skin, pale shirt, lit leaves). Midtone p50 ≈ 95–120. |
| Shares | 25 % below L60, 6.3 % above L200 | 25 % below 60, 0.6 % above 200 | keep the dark share; add real speculars (wet leaf, plank top, shoe, faces) |
| Palette (6-colour quantise) | #2d2d2d 24 % · #454545 14 % · #5b5b5b 15 % · #848484 18 % · #acacac 18 % · #cccccc 12 % | darker and narrower | anchor black #2d2d2d, anchor white #cccccc (shoe satin up to ~#e6e6e6) |
| Detail / texture | high-pass σ (r = 2 px) 12.3; mean gradient 14.4 | 8.4; 4.65 | **the largest gap.** The jungle must be dense real photographic detail (leaf veins, bark, fern pinnae), not a blurred plate. Target gradient ≥ 10 over the picture. |
| Light / space | column means L→R 75 99 111 92 126 136 127 116 115 121; row means top→bottom 89 89 102 124 142 124 | top-heavy dark band | soft overcast top light. Darker upper canopy, brighter middle (figures, water), a dark root diagonal low left. No hard cast shadows, no sky. |
| Framing / scale | close two-shot; heads ≈ 0.25 of frame height; frame crammed edge to edge | wide; figures ≈ 0.6 H | wide shots for the plank law, plus **at least two close shots** (S5 retrieval and S6 hand-off) where a puppet head is ≥ 0.20 H and foliage fills ≥ 70 % of the non-figure area |
| Typography | none in still | serif caption | French captions in kit `serif` 24 px, #e6e6e6 on a #2d2d2d band at 55 % opacity. Ledger lettering is handwritten pencil on card (handmade). |
| Pacing | still | — | 12 poses/s on twos; few cuts (8 per version); one held 2 s close on the shoe in the hand |

**How the film arrives there with real material and real technique**
1. **Foraged photographic jungle in four depth planes.** Each plane is a real PD/CC photograph, cut out with GrabCut and alpha cleanup:
   - **P0 far wall:** dense b/w rainforest interior.
   - **P1 mid trunks:** a giant buttress-root trunk and lianas.
   - **P3 near:** big leaves and a tree fern, defocused by real depth blur proportional to plane distance. This is the only blur allowed.
   - **P4 foreground:** a diagonal root crossing a lower corner, as in the reference.

   Search Commons first for b/w or early photographs (19th–early 20th c. botanical or expedition plates, USDA/USFS, Kew-style herbarium photos are not wanted, living forest only), then the LoC "No known restrictions" set (e.g. Panama Canal / Philippines / Puerto Rico forest photographs, Detroit Publishing). The movingimagearchive cache is used only as a fallback for the far plane and for water motion: *Indisch allerlei* 1920, *Robinson Crusoe* 1927, *The Green Promise* 1949 swamp. Colour photographs may be used only after a neutral luminance conversion that preserves their own light (overcast, not sunlit).
2. **Handmade puppets reach the reference's skin.** Grey card puppets are re-modelled:
   - cloth folds and sleeve breaks;
   - B's wet hair as many cut strands;
   - C's headband with a pencilled pattern.

   Real charcoal-and-water mud is simulated as a physical deposit: a smudge mask stamped with paper-grain modulation, darker in creases. Sweat highlights are a separate thin specular pass (L 200–225) on brow, cheek and knuckles. The card has a real paper-fibre texture generated as a fibre field, not a grain filter.
3. **Grade only to unify.** One monotone curve per foraged plate maps its p2/p98 to L 35/220, then the plate is desaturated to neutral. Puppet cards are painted in the same range. No faux grain, scratches, vignette or flicker: `Film(..., boil=0, wobble=0)`, `ink.paper(grain=False)`, no `ink.vignette`.
4. **Pillarbox 1.48.** The picture is 800×540 centred in 960×540, with #1b1b1b bars.

---

## 1. Creative thesis

Three cut-paper people must cross a flood channel on one plank that bears one person, with one dry bag and an overhead liana. A wedding shoe, white, dry and photographically real in a world of card and charcoal, drifts to the foot of the plank.

The shoe earns its strangeness by costing a hand. Crossing takes one hand on the liana, and the bag takes the other. Whoever keeps the shoe can no longer carry the bag. So the woman's decision to pick it up rewrites who carries the group's only dry stock and who crosses last into the rising water.

The same shoe, frame-identical, arriving 7 s earlier, rewrites the order differently, because fewer people are committed. The surreal object is ornamental unless it moves the bag and the risk. Here it moves both, and the viewer can count hands.

Bland would be:
- a pretty floating shoe nobody needs to touch;
- a slideshow of jungle photos with pans;
- puppets that slide rather than bear weight on a plank that never bends;
- grey drawn trees instead of real roots.

## 2. Defining beat and comparison baseline

- **Defining beat D (Version L, "late", interruption at 14.0 s).** At **18.0–20.4 s, S5 close**, B (mud-faced woman, bag in her left hand, near bank) watches the shoe touch the plank foot. She pushes the bag into C's arms (bag holder B→C, logged at 18.4) and kneels. Her fingers close on the heel (shoe holder water→B, 19.6). She rises with the shoe against her chest; her other hand reaches for the liana.

  The viewer can point to these frames:
  - the bag changes hands **before** the shoe is touched, which is the choice;
  - then, at 21.5–23.5, the pencilled ledger on the bank card is struck through and rewritten from « 1 A · 2 B (sac) · 3 C » to « 1 A · 2 C (sac) · 3 B ».
- **Alternate V (Version E, "early", interruption at 7.0 s).** The shoe layer is byte-identical: the same 150 frames of drift, bob and ripple, shifted −7.0 s. A is still at the plank head, not yet committed. B hands the bag to A (B→A 11.4) and takes the shoe (12.6). The ledger becomes « 1 B (chaussure) · 2 A (sac) · 3 C ». B crosses first, while the water is lowest.
  - Divergence: in L, B goes last into the highest water. In E, she goes first and C goes last.
  - Equivalence: the shoe's pixels, path and arrival point; the retrieval gesture's pose keys (the same 29-frame pose sequence); the outcome "the shoe's holder does not carry the bag".
- **Baseline Bl (no shoe).** Order 1 A · 2 B (sac) · 3 C, with no rewrite. It is not a full sequence in the film. It is shown as the top line of the end-card ledger, rendered in the ledger JSON as a full world trace, and available as `--baseline` stills (S3/S6 frames with the shoe layer off) for the critic.
- **Success condition.** A fresh viewer can answer without captions:
  1. Who carries the bag after the shoe, in each version?
  2. Why can't the woman carry both?
  3. Who crosses last?

  The answers must differ between L and E in "who crosses last".

## 3. Lineage Genome (compact)

| field | value |
|---|---|
| source | *La Mort en ce jardin*, Luis Buñuel, 1956, Franco-Mexican colour feature; screenplay credits include Raymond Queneau (per MoMA). The publicity still used as reference is b/w. Fugitives cross a jungle, and incongruous objects interrupt survival (a Paris postcard; a crashed airliner's luxuries). The details of the later jungle section are from general film knowledge and are **uncertain**. |
| target | 73 s screen proof, 960×540, 24 fps, ≤ 6 MB: two versions (L 36 s, E 30 s), title and cards, and a 3.5 s ledger comparison |
| preserved relation | a concrete survival logistic (route, load, support) is redirected by one incongruous civilised object that someone *chooses* to hold |
| optics change | 35 mm colour live action becomes articulated grey card puppets (handmade) on foraged photographic multiplane jungle, with one photographic object (the shoe). This is a declared change of optics. |
| formalism change | implicit continuity becomes an explicit world-state machine (plank occupancy ≤ 1, hands ≤ 2, possession log) checked every frame |
| concept change | Buñuel's objects comment ironically. Here the object must cost a hand and reallocate the bag and the risk. The early/late alternate tests timing as cause. |
| sound change | dialogue becomes French captions (no TTS). Foraged water and jungle ambience, plus handmade foley (plank creak, card-on-card tap, splash). |

Formation epochs (weight 0–100, reason):
- **Surrealist object / dépaysement** (Breton, Magritte, 1924–1940), weight **80**: the wedding shoe as the displaced object. That Buñuel's late films derive directly from this is a common claim and is **uncertain** in its specifics.
- **Buñuel's Mexican adventure cycle** (1946–1960), weight **60**: genre survival plus interruption.
- **Oulipo constraint practice** (Queneau co-writing, 1956 predates the Oulipo, founded 1960), weight **35**: the fixed rule (plank = 1, hands = 2) and permutation of an order. The causal link is **uncertain** and is used as method, not attribution.
- **Cut-out and silhouette animation** (Reiniger 1926; Starewicz; Norstein's *Tale of Tales* 1979 multiplane), weight **55**: the technique.
- **Collage graph rewriting** (SCION 43, source anchor), weight **50**: substitution with a readable consequence chain.
- **Logistics puzzles** (river-crossing problems, Alcuin c. 800), weight **40**: crossing order under capacity constraint. The structural analogy is mine, not historical.

## 4. Olog

**Types**
- `Person` {id ∈ {A, B, C}; A = tall man with a hat, B = woman with wet hair, C = man with a patterned headband; hands: [L, R] each ∈ {free, liana, bag, shoe}; bank ∈ {N, P (plank), F}; x (px)}
- `Plank` {span N→F, capacity = 1, occupant: Person | null, deflection (px) = f(occupant load, position)}
- `Liana` {overhead, N→F. Rule: whoever is on the plank holds it with exactly one hand.}
- `Bag` {holder: Person | ground(N) | ground(F); must stay dry (y above water line)}
- `Shoe` {holder: water | Person | ground; first_appearance t; drift path id `SHOE-DRIFT-1`}
- `Water` {level(t), rising 0 → +18 px over each version; danger = clearance between level and plank top}
- ◻(WorldState) {t, routes = [N→P→F], resource stock {bag: 1, shoe: 0|1}, supports {plank, liana}, obstacles {water}, positions}
- ◻(GroupDecision) {t, chooser, alternatives [{order, bag carrier, last crosser, water clearance at last crossing}], costs, resulting allegiance (who holds the group's stock)}
- ◻(Interruption) {object = Shoe, first_appearance (L 14.0 / E 7.0), material affordance = "graspable, buoyant, dry inside, occupies one hand", rule exception = none (the shoe obeys the same physics; its immaculate dryness is the one declared impossibility, scoped to the shoe only), next consequence = holder's hand is occupied}

**Central operation `retrieve(p: Person, s: Shoe, t)`, then `reallocate(order)`**

Typed preconditions:
1. s.holder = water, and s is within reach r ≤ 60 px of p's hand at t (the shoe is at the plank foot).
2. p.bank = N (not on the plank): a person on the plank has liana + bag/shoe, so has no free hand.
3. p has a free hand at t, *or* p first performs `handoff(bag, p → q)` with q.bank = N, q ≠ on the plank, and q has a free hand.
4. Plank occupant ≠ p at t.

Observable consequences:
- s.holder := p, and the shoe is parented to p's hand bone (FK) for every later frame.
- p can no longer carry the bag across. The order is recomputed so the bag carrier is a person with one free hand.
- The ledger line is struck and rewritten on screen within 4 s.
- The new order's last crosser faces water clearance c_last. This is logged and differs between L and E.

**Counterexample (must fail the gate):** B picks up the shoe while still holding the bag and then crosses holding liana + bag + shoe. That is three hands, which violates `hands ≤ 2`, so the candidate is quarantined. A second counterexample: C steps onto the plank at 24.0 while A has not yet stepped off at F. That gives plank occupancy 2 and fails §7. A third: the bag is absent from every hand and both grounds for any frame without a logged handoff, a "disappeared possession", which fails.

**Replay / alternate equivalence:**
- **Equivalent:** shoe layer frames (hash-identical, shifted 168 frames = 7.0 s); retrieval pose keys; S1 and S2 frames (byte-identical between L and E); jungle planes.
- **Divergent:** bag carrier (C vs A), crossing order, last crosser (B vs C), water clearance at the last crossing (L: B at 4 px; E: C at 6 px; both logged), the ledger text, and the version length (36 vs 30 s, because E's decision lands before anyone has crossed).

## 5. Invariants (checked every frame by `assert` in the film script and written to the ledger)

1. Plank occupancy ≤ 1 at every frame (feet on the plank span). This is the material law, never changed.
2. Each person has ≤ 2 hands. The plank occupant has exactly one hand on the liana.
3. Bag count = 1 and shoe count ≤ 1. Every frame has exactly one holder per object. Holder changes only at a logged `handoff` or `retrieve` event, with the hands within 40 px at the event frame.
4. Bag y (bottom) is above the water level at every frame.
5. The shoe's immaculate dryness and whiteness is the **only** declared impossible behaviour. Its scope is the shoe itself: no mud appears on it even after handling.
6. Positions persist across cuts. The close shots S5 and S6 derive from the same world state as the wide shots (the camera reframes; the world does not jump).
7. The interruption layer in E is the L layer shifted by −7.0 s (frame-hash equality over 150 frames).
8. Licences: every foraged item is PD / CC0 / CC BY / CC BY-SA, read from extmetadata or the LoC rights field, and recorded in `films/credits/la-mort-en-ce-jardin.json`.

---

## 6. Hard proof: timed shot list (total 73.0 s)

Picture: 800×540 in 960×540. Animation: 24 fps, poses on twos (12 per s), joint angles eased between keys and quantised to whole degrees.

Wide = the whole crossing (plank about 520 px long, puppets about 0.45 H). Close = head ≥ 0.20 H.

| # | film time | dur | shot | on screen | heard |
|---|---|---|---|---|---|
| T | 0.0–2.0 | 2.0 | title | handmade card: « La planche » / « trois · un sac · une planche » pencilled on grey card | water ambience fades in |
| **Version L (late), local t = film t − 2.0** | | | | | |
| L-S1 | 2.0–5.0 (0–3) | 3.0 | wide, lateral multiplane glide R→L, 60 px at P2 | P0–P4 jungle; channel; plank N→F; liana; A, B (bag in her L hand), C on N bank. Caption « La planche n'en porte qu'un. » | foraged water/stream, insects; liana creak |
| L-S2 | 5.0–8.0 (3–6) | 3.0 | medium on N-bank card | A pencils the ledger on the torn bank card: « 1 A · 2 B (sac) · 3 C » (stroke-by-stroke handwriting animation) | pencil on card (handmade foley) |
| L-S3 | 8.0–14.5 (6–12.5) | 6.5 | wide | A crosses: right hand on the liana, the plank deflects up to 9 px under him, step cycle with weight (hip drop, foot plant); reaches F at 12.5. B steps to the plank head. | plank creak per step (handmade), water |
| L-S4 | 14.5–20.0 (12.5–18) | 5.5 | wide → slow push-in 8 % | **14.0 local: the shoe first appears** at frame right upstream, drifting on a spline across the water plane, bobbing ±3 px over 0.9 s, rippled reflection, broken ripple rings. B turns her head (12 fps steps). C: « Laisse-la. » (16.0) | a hollow tap of the shoe on the plank at 17.6 |
| **L-S5 (D)** | 20.0–22.4 (18–20.4) | 2.4 | **CLOSE** at the plank foot; B's head 0.24 H; fern and root planes fill the frame | 18.4: B pushes the bag into C's hands (B→C). 18.8–19.6: B kneels, the hand card overlaps the shoe (occlusion). 19.6: shoe holder → B. She lifts it to her chest. Mud on her knuckles, the white satin clean. | water lap close, card rustle; silence of insects 19.4–20.0 (declared) |
| L-S6 | 22.4–26.0 (20.4–24) | 3.6 | CLOSE two-shot B and C (C head 0.22 H) → cut to the ledger insert 21.5–23.5 | C holds the bag high; B: « Je ne peux pas tout porter. » The ledger line is struck through in 8 frames and rewritten: « 1 A · 2 C (sac) · 3 B ». | pencil scratch |
| L-S7 | 26.0–32.0 (24–30) | 6.0 | wide | C crosses with liana + bag held high. Water rising (+10 px). Arrives F at 29.6; plank empty 29.6–30.0. | creak, water louder |
| L-S8 | 32.0–38.0 (30–36) | 6.0 | wide, then hold | B crosses last with liana + shoe; water clearance down to 4 px, the plank dips into the water at its centre; splash on her shins (a mud plane darkens). Arrives F at 35.0. Hold: A, C (bag), B (shoe) on the F bank. Caption « Elle la garde. » | splash, then water only |
| card | 38.0–39.5 | 1.5 | card | « Plus tôt » (handmade card) | room-quiet water |
| **Version E (early), local t = film t − 39.5** | | | | | |
| E-S1 | 39.5–42.5 (0–3) | 3.0 | = L-S1 (byte-identical frames) | same | same |
| E-S2 | 42.5–45.5 (3–6) | 3.0 | = L-S2 | same ledger « 1 A · 2 B (sac) · 3 C » | same |
| E-S3 | 45.5–50.0 (6–10.5) | 4.5 | wide | A steps to the plank head. **7.0 local: the same shoe, same frames,** drifts in. A turns. | identical shoe tap at 10.6 |
| E-S4 (=D′) | 50.0–52.4 (10.5–12.9) | 2.4 | CLOSE, same framing as L-S5 | B pushes the bag into **A's** hands (B→A 11.4); kneels; takes the shoe (12.6). The same pose sequence as L-S5. | same foley |
| E-S5 | 52.4–54.5 (12.9–15) | 2.1 | ledger insert | struck and rewritten: « 1 B (chaussure) · 2 A (sac) · 3 C » | scratch |
| E-S6 | 54.5–69.5 (15–30) | 15.0 | wide, three crossings | B crosses 15–19.5 (low water); A with the bag 19.8–24.4; C last 24.8–29.4, water up to 6 px clearance. Hold on F. Caption « C passe le dernier. » | creaks, splash on C |
| cmp | 69.5–73.0 | 3.5 | handmade ledger card | three pencilled lines: « sans chaussure : 1 A · 2 B (sac) · 3 C » / « 14 s : 1 A · 2 C (sac) · 3 B » / « 7 s : 1 B · 2 A (sac) · 3 C », with the last crosser underlined | water out |

Sound: foraged first (water, stream, rain, jungle/insect ambience from movingimagearchive clips with source sound, or Commons audio, PD/CC). Foley that nothing foraged supplies (plank creak, card tap, pencil) is synthesized with the kit Mix and declared in the notes.

## 7. Element sourcing (FORAGED / HANDMADE)

| element | kind | what / where |
|---|---|---|
| P0 far jungle wall | FORAGED | dense rainforest interior, b/w or neutral-convertible, ≥ 1200 px wide: Commons (search "rainforest interior", "buttress roots", "Ceiba", "Ficus roots", "tropical forest 1900", "Panama forest") or LoC (Panama Canal Zone, Philippines, Detroit Publishing "jungle"). Fallback: archive *Robinson Crusoe C* 1927 stills. |
| P1 buttress-root trunk, lianas | FORAGED | a buttress-root photograph cut out with GrabCut (the trunk with its flanges), placed left of centre as in the reference |
| P3 near leaves and fern | FORAGED | big-leaf (Alocasia / Monstera / banana / Heliconia) and tree-fern photographs, GrabCut-cut, depth-blurred by plane |
| P4 foreground root diagonal | FORAGED | a root or fallen trunk photograph, cut, low-left corner |
| water surface | FORAGED + HANDMADE | archive water motion (*Indisch allerlei* 1920 or *The Green Promise* 1949 swamp loop), graded dark, plus handmade wave-cut card strips sliding at 4/7/11 px per frame as a second plane |
| banks | HANDMADE | torn card with charcoal mud and root fingers (cut from P4 texture where possible) |
| plank | HANDMADE | pale card scored with grain, a deflecting beam (bends as a 2-segment polyline) |
| liana | HANDMADE + FORAGED | a foraged liana cut, if available; otherwise a twisted-paper cord |
| puppets A/B/C | HANDMADE | grey card, 15+ pieces each, split pins, pencil faces, charcoal mud, sweat speculars, B's hair strands, C's patterned headband, A's hat |
| dry bag | HANDMADE | dark oilcloth card bag with a strap and a tie |
| wedding shoe | FORAGED | LACMA 51.47.2a-b *Pair of Woman's Bar Shoes (Wedding)*, Commons. Re-read the extmetadata licence (expected PD, LACMA public-domain image). Right shoe GrabCut-cut. Spare: LACMA M.83.156.1a-b (oxford), for the §8 second object. |
| ledger | HANDMADE | pencil handwriting animated stroke by stroke on the bank card |
| captions | HANDMADE (typographic) | French, kit serif |
| sound | FORAGED + HANDMADE | see §6 |

## 8. Animation technique SCIONs (from `swarms.json`; prompts read in full)

1. **#32 Forward Kinematics: Hierarchical Body Logic.** Every puppet is a joint graph (root/hip → spine → neck → head; shoulder → elbow → wrist → hand; hip → knee → ankle → foot), with props (bag, shoe) parented to hand bones on possession.
   - Bone lengths are invariant, checked numerically per frame.
   - There is no head/neck detachment.
   - Applied in S3/S7/S8/E-S6 (walk with weight on the plank, the hand on the liana), S5/E-S4 (kneel, reach, grasp, rise) and S6 (lifting the bag).
   - Deliverable: `rig.json`, a transform test, and an errors-by-joint report.
2. **#44 Multiplane Parallax: Spatial Collage Swarm.** Five planes with depths and parallax ratios:
   - P0 0.15×;
   - P1 0.35×;
   - P2 (water, banks, plank, puppets) 1.0×;
   - P3 1.5×;
   - P4 2.0×.

   Depth blur rises with distance from the P2 focus plane. Occlusion edges: P3 leaves cross in front of the puppets in close shots. Applied in S1 (lateral glide), S4 (push-in) and the close shots (P3/P4 framing the faces as in the reference). Invariant: near planes move more than far ones, with no foreground stretching (no upscale > 1.6× on any plate).
3. **#29 GrabCut: Cutout Extraction Swarm.** Real cutouts of:
   - the shoe;
   - the buttress trunk;
   - the fern and leaves;
   - the root diagonal;
   - the liana.

   Each is an RGBA piece with a contour mask, failure masks and an original-coordinate transform. Invariants: no background islands, and fern pinnae retained. Applied in U1 for the plates and U3 for the shoe.

Supporting methods (not separate scions, used within units):
- #45 occlusion (hand over shoe, shoe over reflection);
- #48 state machine (plank/hands law);
- #41 secondary dynamics (bob, plank spring, hair strands);
- #43 collage graph rewriting (the shoe → hand → bag → order chain, as the source anchor).

## 9. Swarm units (3; the montage editor and the independent critic run separately)

All units fork from plan-r1. Media go under `films/sources/la-mort-en-ce-jardin/<role>/`; specs and ledgers go under `films/swarm/la-mort-en-ce-jardin/`. Budget: ~45 min each, with new downloads ≤ 75 MB in total (U1 ≤ 50 MB, U3 ≤ 20 MB, U2 0 MB). Every unit reads the full prompts for #32, #44 and #29 in `swarms.json`.

- **U1 World & jungle planes** (world unit + multiplane + GrabCut on plates). Output: `world.json` plus `plates/` contact sheet `world-sheet.jpg`. Media: `sources/.../world/`.
  - Forage and licence-verify P0–P4 and the water plate.
  - Cut them out with GrabCut and alpha cleanup.
  - Grade them to the target curve.
  - Write the multiplane scene graph (plane depths, ratios, blur, camera paths for S1/S4/close shots).
  - Write the full WorldState trace for L, E and the baseline: water level(t), plank deflection, positions, plank occupancy, and the water clearance for the last crossing.
  - Produce one 800×540 composited jungle test frame per framing (wide, close), with measured tonal and gradient stats against the reference.
- **U2 Performance & puppets** (performance unit + FK). Output: `performance.json`, with the rig, pose keys per shot, the possession/hand event log and the gate results. Also `puppet-sheet.png`. Media: `sources/.../performance/`.
  - Re-model A/B/C as handmade card puppets (folds, hair strands, headband pattern, mud deposit, sweat specular).
  - Build the FK rig and the pose keys: walk-with-weight on the deflecting plank, kneel-reach-grasp-rise (shared between L-S5 and E-S4), bag lift and hand-off.
  - Write the invariant gate (`gate.py`: plank ≤ 1, hands ≤ 2, holders logged, bone lengths) and make the three counterexamples fail it.
  - Render the test shot L-S5 as a close PNG sequence over U1's planes once available, or over kf-1's planes until then.
- **U3 Object & sound** (object/sound team). Output: `interruption.json` (shoe source, licence, cutout, drift spline, 150-frame layer with per-frame hashes, contact/tap time, alternate shift) and `sound.json` (cue list with sources and licences). Media: `sources/.../object-sound/`.
  - Re-verify the shoe's licence.
  - Cut it out at the best available resolution.
  - Render the drift/bob/reflection/ripple layer as a frame sequence (RGBA PNG).
  - Forage the water/jungle ambience and water-lap/splash sounds (archive clips with sound first, then Commons audio).
  - Synthesize the creak, tap and pencil foley with the kit Mix where nothing foraged fits.
  - Deliver the mixed stems as WAV.
  - Prepare the oxford-shoe variant (§8 second object, same affordance) as a stills comparison only.

The editor (separate) assembles `films/la-mort-en-ce-jardin.py` with `kit.py` from these outputs, writes the credits, the notes and `ledger.json` (per-frame world/possession audit), and renders.

## 10. Acceptance bar (falsifiable; a fresh critic checks it by watching `assets/films/la-mort-en-ce-jardin.mp4` and reading the ledger)

1. **One on the plank.** No frame shows two puppets' feet on the plank span. The ledger's per-frame `plank_occupant` never lists two. Specifically, in L-S7 C steps on only after A has stepped off at F, and B only after C. (measured + perceptually checked)
2. **The shoe costs a hand and moves the bag.** In both versions the bag visibly changes hands, B→C in L at film 20.4 and B→A in E at film 50.9, **before** B touches the shoe. After the retrieval, the shoe stays in B's hand in every later frame and B never carries the bag. The ledger possession log has no holder change without an event. (perceptually judged + structurally verified)
3. **Timing changes the order.** The final crossing order differs between versions (L: A, C, B; E: B, A, C), and the last crosser differs (B vs C). The 150 shoe-layer frames are hash-identical between versions, offset by exactly 7.0 s. (measured)
4. **Aesthetic, tone and neutrality (side by side).** Frames at film 21.2 (L-S5 close) and 3.5 (L-S1 wide) are placed beside `bunuel.webp`, with the picture area measured:
   - p5 within 30–45, p50 within 90–125, p95 ≥ 185;
   - mean |R−B| ≤ 2;
   - a viewer judges the three as the same tonal world: soft overcast mid-grey, lifted blacks, unclipped highlights. (measured + perceptually judged)
5. **Aesthetic, density and framing (side by side).** In the same comparison, the close frame shows:
   - real photographic foliage (buttress trunk, big leaves, fern) filling ≥ 70 % of the non-figure picture area;
   - a puppet head ≥ 0.20 of frame height, with mud on face/hands and a visible sweat highlight;
   - mean luma gradient over the picture ≥ 10 (reference 14.4; kf-1 4.65).

   No plate is upscaled > 1.6×, and no blur is applied except per-plane depth blur. Each plant layer traces to a credited PD/CC source. (measured + perceptually judged)
6. **Animated with weight, frame by frame.** In the plank crossings the puppets step (feet plant and lift, hips drop), the plank deflects under the occupant and springs back when empty, and the retrieval is a sequence of distinct poses (kneel, reach, grasp, rise), not a slide or a fade. Bone lengths are constant: the ledger's `rig_error_max` < 0.5 px. (perceptually judged + measured)
7. **Danger is visible and sound is purposeful.** In each version the last crosser's crossing shows the water at its highest (clearance ≤ 6 px, the plank dipping, a splash heard). Audible cues align within 2 frames with the shoe tap, the bag hand-off rustle and each plank step. Ambience is foraged and credited, and synthesized foley is declared in the notes. The film is ≤ 75 s and ≤ 6 MB. (measured + perceptually judged)
8. **Licences.** Every foraged item is in `films/credits/la-mort-en-ce-jardin.json` with a PD/CC0/CC BY/CC BY-SA licence read from source metadata, or the archive formula. Nothing comes from Buñuel's film or the MoMA still. (structurally verified)

## 11. Repair rules (prompt §8) pre-registered
- If the shoe reads as ornamental: keep its design and make the hand cost more legible, by adding a close on B's hands (liana + shoe) as she steps onto the plank.
- If physical credibility fails: keep the decision and repair the earlier support (plank deflection, liana tension, water level).
- Second object test: the oxford wedding shoe (same affordance) versus, as the editor's optional still comparison, a foraged PD brass ship's lantern. Same mechanics, different social meaning. Recorded as stills only, within budget.

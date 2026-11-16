# La Belle Hortense: director's plan (SCION swarm, revision P1)

- **Direction:** Direction 1, *Le manteau rouge* (`proposals/kf-1.png`), as chosen by the user.
- **This plan is rebuilt from scratch.** Earlier `films/la-belle-hortense.py`, its notes and its credits are not a base. Foraged files that are already on disk may be reused, but only after their licences are re-verified.
- **Format:** 960×540 at 24 fps (kit.py), 66.0 s, at most about 6 MB, with picture and sound.

---

## 1 · Creative thesis

A red coat lies folded on a station bench in the first scene. Nobody looks at it: it is set dressing. The visitor lays the brass key *on it*.

Every module re-deals the same six motifs in the order the sestina permutation [6,1,5,2,4,3] dictates. Each time, the coat is pushed into another slot and plays another role: background, then something taken away, then a distant red speck, then a blur.

In module V the permutation brings the coat to slot 3. The coat comes running back, as a tight, pan-smeared red body on streaked green, the cover's own image. The key drops out of its hem.

The viewer should feel that the form *delivered* the evidence: the clue was in plain sight from 3.0 s, and its return at the slot the order assigned is what turns it into proof.

**What would make it bland:**
- Six modules that read as a checklist, where each motif is shown and ticked off.
- A coat that only matters once it is announced.
- Grey archive stills slid sideways under captions.

## 2 · Defining beat and comparison baseline

**Defining beat (the TEST SHOT).** Module V, slot 3 (MANTEAU), runs **42.0–43.5 s**, with the key-drop at about **43.2 s**.
- The conductor runs back toward the goods shed in the red coat.
- The frame is cropped as tight as the cover: the coat fills at least 55 % of the frame height and the head is at or above the top edge.
- The ground and the shed are smeared into horizontal green streaks by a real pan exposure.
- The brass key slips from the coat's fold and falls behind his swinging shin.
- Type in the lower left:
  - `V.` in black.
  - `le manteau revient` in red slab type.
  - The slot line in black: `banc · reçu · MANTEAU · clé · porte · cloche`, with MANTEAU in red.

**Comparison baseline.** The same six scenes cut in story order with no permutation. In the baseline the coat appears only when the conductor takes it (II) and never returns in a fixed slot, and the key is simply found at the end. The baseline gets rendered as a 20 s diagnostic: I.4 → II.2 → V.3 → V.4 in plain order, with the coat absent from I.1.

The comparison tells us whether the viewer can *point back* to the clue. In the baseline the reveal depends on its own first appearance, so it fails §7.

**What the viewer should be able to point to:** "the red coat was on the bench in the first scene, and she put the key on it."
- The critic checks this against the frames at 3.75 s and 8.25 s, and against 43.3 s.

## 3 · Lineage Genome (compact)

| field | value |
|---|---|
| source | *La Belle Hortense*, Jacques Roubaud, novel (Ramsay 1985; Points paperback). Prose; a parodic detective novel. |
| target | A 66 s animated film: cutout puppetry, multiplane and stencil colour over foraged photographs, with typed captions and foraged sound. |
| preserved relation | Motif recurrence governed by a fixed permutation, where recurrence changes what a reader can infer (the formal order generates evidential value). |
| optics change | Prose → a lateral pan-exposed camera. The streak gets stronger as the mystery tightens: none in I, partial in II–IV, full at V.3 (the cover's optics arrive at the beat). |
| formalism change | The sestina's line-end words → six 1.5 s *time slots* per 9 s module. Position = time. |
| concept change | The novel's comic mystery is reduced to one misplaced key, using the six prompt motifs (manteau, cloche, clé, banc, reçu, porte). |
| sound change | Silent page → bell as clock and alibi. A foraged station-bell strike sounds exactly in each module's cloche slot, and a typewriter click marks every slot start. |

**Formation epochs (weight 0–100 and reason):**

| epoch | weight | reason |
|---|---|---|
| Troubadour sestina (Arnaut Daniel, late 12th c.) | 70 | The source of the spiral permutation [6,1,5,2,4,3] (Poetry Foundation gloss). |
| Oulipo generalisation of the sestina (Queneau's *quenine*, Roubaud's n-ines, 1960s–70s) | 85 | Roubaud's own constraint lineage. *How exactly the permutation governs the Hortense novels is uncertain here* (BnF names a sextine-organised cycle; we do not claim a chapter-level mapping). |
| Roubaud, *Hortense* cycle (1985–90) | 90 | The work itself: parody of the detective form, and a narrator who exposes his rules. |
| Golden-age fair-play detection (Knox/Van Dine rules, 1928–29) | 60 | "The reader can explain the solution from available clues." |
| Points paperback cover (pan-blurred runner) | 80 | The aesthetic target (see §9). Photographer not identified: *unknown*. |
| Reiniger articulated cutout (1926) | 60 | Hinged puppets cut from photographs; the run and walk cycles. |
| Pathé stencil colour (Pathécolor, c. 1905–30) | 55 | Hand-cut dye masks over monochrome prints: red coat, green grass, brass key. |
| FSA/OWI documentary photography (1935–44) | 40 | The source of the bodies (US government work, PD). |
| Multiplane (Disney 1937; Norstein 1979) | 45 | A layered stage and depth-ratio pans. |

## 4 · Theory: Olog

**Types.**
- `◻(Motif)` = {id ∈ {A manteau, B cloche, C clé, D banc, E reçu, F porte}, signature, permitted_functions}.
  - Signatures are fixed for the whole film:
    - **A manteau:** the coat panel cut from LoC 2017844115, dyed red #e2011b.
    - **B cloche:** the station bell cutout plus the Fridingen strike recording.
    - **C clé:** the CC0 skeleton-key photo, dyed brass.
    - **D banc:** the Highsmith PD park-bench cutout.
    - **E reçu:** the handmade ticket "REÇU N° 6".
    - **F porte:** the shut goods-shed door of the Bourré photo, quoined red/white.
  - Functions ⊆ {background, action, absence, false-lead, evidence, closure}.
- `◻(Module)` = {index i ∈ I..VI, order oᵢ (6-tuple), slot times, appearances[6], knowledge_in, knowledge_out}.
- `◻(Permutation)` σ: oᵢ₊₁[k] = oᵢ[σ[k]−1], with σ = [6,1,5,2,4,3].
- `◻(Clue)` = {id, event (module, slot, t), supports claim, reveal_window}.
- `◻(Claim)` S = "the conductor carried the key away in the fold of his coat".

**Central operation: `return_as_evidence(M=A, module=V, slot=3)`.**

*Typed preconditions:*
1. `oV = σ⁴(oI)`, and `oV[3] = A`. This is structurally verified: DEACFB has A in slot 3.
2. M = A appeared with function *background* in a module before V. Here that is I.1 (3.0–4.5), on the bench, uncaptioned.
3. There is a clue event linking C to A before the reader checkpoint. Here that is I.4 (key placed on the coat) and II.2 (the coat lifted with a brass glint in its fold).
4. Every support of S has t < 39.0 s (the fresh-reader stop), and at least one support has t ≤ 21.0 s.
5. A's signature in V.3 is identical to I.1: the same source pixels, the same dye and the same cut contour.
6. No module contains A twice.

*Observable consequences:*
- At 43.3 s a viewer sees the same red coat they saw on the bench, now worn and running, and sees the key leave it.
- A paused viewer at 39.0 s can already name S, or the false leads: the visitor or a thief.
- Pointing back to frame 3.75 s or 8.25 s explains the solution without the formula.

*Counterexample (the operation fails):* the baseline cut.
- There the coat is first seen in II.2 or V.3, so V.3's evidence rests on its own first appearance. That breaks §7's clue test.
- A second counterexample: if module V's order were any other order, for example DEACBF swapped, the coat would still be in slot 3 but the module is not σ(oIV). The verifier rejects it as a sequence violation before any scene is rendered.

**Replay and alternate views.**
- **Equivalent views:**
  - IV.2 and VI.2 replay the exact pixels of I.4 inside a typed frame ("I·4"). They are the same view, so the identity of the evidence cannot drift.
  - The end-card matrix is equivalent to the slot lines.
- **Divergent views:**
  - V.3 is a *new* view of the coat: worn, running and smeared. Its identity is carried only by the cut contour and the red dye, so if the dye or the cut differs from I.1, the views diverge and the beat fails.
  - III.4 shows the coat at a distance as a red speck crossing the far plane. It diverges deliberately: it is recognisable by colour alone and is a fair but quiet clue.

**Fixture (§7).**
- [A,B,C,D,E,F] → [F,A,E,B,D,C], and σ⁶ = id.
- The orders: I ABCDEF, II FAEBDC, III CFDABE, IV ECBFAD, V DEACFB, VI BDFECA (computed and checked).
- A duplicate in any module fails.
- A final reveal that depends on its own first appearance fails.

## 5 · Invariants (protected)

1. **Permutation:** each module order = σ(previous order), with module I = ABCDEF. Every motif appears exactly once per module, in its slot, during that slot's 1.5 s. Slot start = 3.0 + 9(i−1) + 1.5(k−1) s.
2. **Signature identity:** a motif keeps one source and one dye across all its appearances.
   - The coat is always red #e2011b ± (8° hue).
   - The key is always brass (≈ #c9a23a).
   - The grass is always the green dye.
   - No other object is red except the brick quoins of the shed, and the title/slot type.
3. **Fair play:** S is deducible from events at ≤ 21.0 s. Nothing at or after the reveal (43.2 s) is a necessary support.
4. **Clue causality:** a clue move that changes when S becomes inferable re-opens every later module (§4 of the prompt). The structure unit re-runs `verify.py` after any such change.
5. **Puppet integrity (Reiniger / FK):**
   - Joints are pinned.
   - The distance from each child pivot to its parent pivot is constant within 1 px in every frame.
   - The joint angle limits hold (knee 0–75°, hip −35–40°, bell ±38°).
   - No limb detaches.
6. **Multiplane:** the parallax ratio near > mid > far in every pan frame, and occlusion order is fixed. From back to front: shed / station → grass mid → bench and coat → figure → near grass band → type.
7. **Material honesty:** every pixel is either foraged (with a recorded licence) or a named handmade object. The streak comes from real temporal integration of translated photographs. Colour comes from dye masks over a monochrome print. There is no grain, blur or tint filter over unsuitable material.
8. **Source IDs are immutable.** Every cutout records its source file, crop box, mask file and licence.

## 6 · Timed shot list: Hard proof (§6) carried out exactly

**Conventions for every module:**
- **Lower-left type block:**
  - The module numeral is black, Courier 10 Pitch Bold, 44 px.
  - A red caption in 30 px slab type.
  - A slot line in 18 px black, giving the six motifs in module order. The active slot word is set in caps and red.
- **Captions are the voice.** They are short French lines. An English gloss of the same line is set at 60 % size under the caption, in black.
- **A typewriter click (synthesised with `kit.click`)** sounds at each slot start.
- **Bell strikes** use the foraged *Glockenschlagwerk Bahnhof Fridingen* recording (CC BY-SA 4.0). They sound only in the cloche slot of each module: I.2, II.4, III.5, IV.3, V.6, VI.1.
- **Ambience:** `kit.wind` at a low level, plus foraged steps where walking occurs.
- **Stage:**
  - The plates are the Bourré photographs by Daniel Jolivet (CC BY 2.0):
    - the goods shed with its shut door, 50866795131;
    - the shed seen from across the meadow, 50866798791;
    - the station house with the BOURRÉ sign, 50866891867.
  - The plates are printed B&W and then stencil-dyed.
- **Pan-streak strength:** 0 in module I, up to about 0.4 in II–IV, 1.0 at V.1–V.4, settling in VI.

| t (s) | slot | on screen | heard | material |
|---|---|---|---|---|
| 0.0–3.0 | title | The green-streaked ground: a real 420 px pan exposure of the Bourré meadow (50866798791), 48 sub-frames, dyed green above and ochre/earth below. `Jacques` / `Roubaud` in black and `La belle Hortense` in red, set like the cover. A small line: `six modules · [6,1,5,2,4,3]`. | One distant bell strike at 0.4 s; wind. | FORAGED plate and bell. HANDMADE typesetting. |
| **I** 3.0–12.0 | ABCDEF | The station, still camera, no streak. This is the seed from §10, kept intact. | | |
| 3.0–4.5 | I.1 manteau | Wide: the bench downstage right, with a dark **red coat folded on it**. No caption names it. Caption: `Une gare vide.` / *An empty station.* | Wind, a click. | FORAGED: bench (Highsmith PD), station house plate. Coat = coat panel cut from LoC 2017844115, folded by 3 hinged cut pieces, dyed red. |
| 4.5–6.0 | I.2 cloche | The bell on its wall bracket swings (FK pendulum, clapper as child joint). The visitor enters left, walking (articulated cutout), with a sealed envelope. | Bell strike at 4.6; gravel steps. | FORAGED: bell (Commons PD/CC photo of a station bell); visitor (LoC FSA/OWI woman in a coat, walking, PD). |
| 6.0–7.5 | I.3 clé | Medium close on her hands: the envelope flap hinges open and the brass key slides out (cutout, frame by frame). `une clé de laiton` / *a brass key* | Paper tear (foraged or synth noise burst), a click. | HANDMADE envelope (cut paper object, typed address "Bourré, quai"), or a FORAGED PD envelope photo. Key: CC0 Skeletonkey.png. |
| 7.5–9.0 | I.4 banc | Wide again. She **lays the key on the bench, on the red coat**. Contact shadow; she straightens. `Elle la laisse sur le banc.` / *She leaves it on the bench.* | A soft key-on-cloth tap. | as above |
| 9.0–10.5 | I.5 reçu | A small ticket slips from the envelope and flutters to the gravel (paper-fall physics: drift plus rotation). | A paper flutter. | HANDMADE: the receipt, a real typeset ticket "REÇU N° 6 · une clé · porte de service · remise au banc", with a red number stamp. |
| 10.5–12.0 | I.6 porte | She walks off right. Slow push on the goods-shed door: shut. `La porte de service reste fermée.` / *The service door stays shut.* | Receding steps, then silence under wind. | FORAGED: shed plate 50866795131. |
| **II** 12.0–21.0 | FAEBDC | The conductor. A small pan begins (streak 0.15–0.4). | | |
| 12.0–13.5 | II.1 porte | Tight on the door: the conductor's hand tries the handle. Locked. `Fermée.` / *Locked.* | Handle rattle (*Door handle creaking*, PD). | FORAGED: hand from LoC 2017844115; door plate. |
| 13.5–15.0 | II.2 manteau | At the bench the red coat is lifted out of frame. For 6 frames **a brass glint shows in its fold**. Cut (behind the bench occluder) to the conductor already wearing the coat. `Il reprend son manteau.` / *He takes back his coat.* | Cloth rustle (filtered noise), a click. | Coat swap through an occlusion holdout (SCION 45 method inside the multiplane). |
| 15.0–16.5 | II.3 reçu | He picks up the ticket. Insert of the receipt: the line `remise au banc` is legible. | A paper sound. | HANDMADE receipt. |
| 16.5–18.0 | II.4 cloche | The bell swings: a train is due. He hurries off left; the camera pans; first streaks. | Bell strike at 16.6; steps. | as above |
| 18.0–19.5 | II.5 banc | The empty bench, held. `Le banc est vide.` / *The bench is empty.* | Wind only. | |
| 19.5–21.0 | II.6 clé | The key is absent: the receipt line `une clé` is struck through in red, typed over. `Où est la clé ?` / *Where is the key?* | Typewriter strike-through clicks. | HANDMADE type. |
| **III** 21.0–30.0 | CFDABE | False lead 1: the visitor took it back. | | |
| 21.0–22.5 | III.1 clé | The visitor's cut hand, closed and turning. `Elle l'a reprise ?` / *Did she take it back?* | A click. | FORAGED visitor cutout. |
| 22.5–24.0 | III.2 porte | The door: still locked; a rattle. | Rattle. | |
| 24.0–25.5 | III.3 banc | Low under the bench: gravel and nothing (multiplane gravel plane slides). | Wind. | Bench cutout; Bourré ground. |
| 25.5–27.0 | III.4 manteau | Wide, far plane: **a small red figure crosses the far end of the meadow** (the conductor in the coat, at 1/5 scale). Background, uncaptioned. | Faint steps. | Same coat cutout, same dye. |
| 27.0–28.5 | III.5 cloche | The bell swings with no one near. `La cloche sonne seule.` / *The bell rings by itself.* | Bell strike at 27.1. | |
| 28.5–30.0 | III.6 reçu | The receipt again: `remise au banc` is underlined in red. She left it; she did not take it back. | Typewriter strike. | |
| **IV** 30.0–39.0 | ECBFAD | False lead 2: a thief, or the bell-ringer. | | |
| 30.0–31.5 | IV.1 reçu | The ticket's number `N° 6` matches the painted `6` on the shed door (handmade enamel plate laid on the door plate). `Porte n° 6.` | A click. | HANDMADE plate. |
| 31.5–33.0 | IV.2 clé | A typed frame `I·4` replays the exact pixels of I.4: the key on the red coat (an equivalent view). `Un voleur ?` / *A thief?* | A short reversed bell tail (from the same recording). | Replay of I.4. |
| 33.0–34.5 | IV.3 cloche | The bell's rope; the bell swings. `Ou la cloche ?` / *Or the bell?* | Bell strike at 33.1. | |
| 34.5–36.0 | IV.4 porte | Close on the keyhole: dark, locked. | Rattle. | |
| 36.0–37.5 | IV.5 manteau | A red blur sweeps across the near plane (coat sleeve, streak 0.6), coming back toward us. | A whoosh. | Same coat. |
| 37.5–39.0 | IV.6 banc | The empty bench. `Qui a la clé ?` / *Who has the key?* holds. **The fresh reader stops here (39.0 s).** | Silence (declared) after a click. | |
| **V** 39.0–48.0 | DEACFB | The return. The streak at full strength. | | |
| 39.0–40.5 | V.1 banc | The bench; the camera starts a fast pan right and the streaks build. | Running steps begin far off. | |
| 40.5–42.0 | V.2 reçu | The ticket lifts off the gravel in the wind of the runner and flutters through the streak. | Paper flutter. | |
| **42.0–43.5** | **V.3 MANTEAU** | **TEST SHOT.** The conductor runs back in the red coat, cropped tight (coat ≥ 55 % of frame height, head at the top edge). Shins swing at 2.3 Hz, the body leans 9°, the shed and grass are smeared by 36-sub-frame pan integration. At ≈43.2 the key slips from the hem and falls, turning. `V.` / `le manteau revient` / slot line with MANTEAU in red. | Steps at stride rate (*Concrete Steps 2*, CC BY-SA 3.0, cut as grains); pan whoosh. | FORAGED: conductor (PD), plates (CC BY 2.0), key (CC0). HANDMADE: rig, dye masks, type. |
| 43.5–45.0 | V.4 clé | The key lands brass-on-green, bounces once and lies still; his hand takes it. `La clé était dans le pli.` / *The key was in the fold.* | A key tink (*Keys hitting tree 2*, CC BY 4.0, or the CC0 lock recording). | |
| 45.0–46.5 | V.5 porte | Key in the lock: the door leaf swings open on its hinge (cutout, horizontal foreshortening), dark inside. | Latch then hinge (*lock-3-open*, CC0; *Squeaky door hinge*, PD). | |
| 46.5–48.0 | V.6 cloche | The bell rings as the door opens: a full strike. | Bell strike at 46.6. | |
| **VI** 48.0–57.0 | BDFECA | Closure. The streak decays to 0. | | |
| 48.0–49.5 | VI.1 cloche | The bell settles: damped pendulum to rest. | The strike's tail. | |
| 49.5–51.0 | VI.2 banc | A typed frame `I·4` replays the key laid on the red coat (equivalent view). `Elle l'avait posée sur le manteau.` / *She had laid it on the coat.* | A click. | |
| 51.0–52.5 | VI.3 porte | The door stands open. | Room tone. | |
| 52.5–54.0 | VI.4 reçu | A red stamp `RENDU` thumps onto the ticket. | A stamp thud (`kit.thud`). | HANDMADE stamp. |
| 54.0–55.5 | VI.5 clé | The key hangs on its hook (slight pendulum). | A soft tink. | |
| 55.5–57.0 | VI.6 manteau | The coat lies folded on the bench again: background, as in I.1. | Wind. | |
| 57.0–66.0 | end card | The handmade motif × module matrix (6 × 6, Courier). Rows are typed on one per 0.5 s, with braid strands drawn between each motif's slots. The coat strand is red and the rest are black. Then the line `σ⁶ = id · ABCDEF`, and credits in small type. | One final bell at 57.2, then silence 63–66 (declared). | HANDMADE. |

The film ends at 66.0 s.

## 7 · Animation technique SCIONs

**SCION 29 · GrabCut, Cutout Extraction Swarm.** Every body and prop is a real photograph and must be lifted out as a clean animation layer.
- The cut list:
  - the conductor (LoC 2017844115);
  - the visitor (a new LoC FSA/OWI figure);
  - the bench (Highsmith PD);
  - the bell;
  - the key (CC0);
  - the door leaf.
- Method: `cv2.grabCut` with box and scribble seeds, then a hand-placed scissor polygon where the wall fringe leaks (the conductor's right arm), then 1–2 px alpha cleanup.
- Pieces are kept separate: coat panel, head and cap, hand, newspaper, each shin.
- Acceptance tests:
  - no background islands;
  - fingers retained;
  - failure masks exported;
  - the halftone and grain of the source are not mistaken for edge.

**SCION 2 · Lotte Reiniger, Articulated Shadow Theater**, used with the joint-graph rules of FK 32. It gives pinned joints, joint limits and replacement profiles: what the run, walk, bell and envelope need.
- **Conductor rig:**
  - The root is the coat and body. The head and cap are fixed to it.
  - The arm and hand are hinged at the shoulder.
  - There are two substitution shins hinged at the hem: the cut leg stretched 1.7×, the far one printed darker.
  - Run phase advance is 0.1 cycle per frame.
- **Visitor rig:** the body, plus two legs with knee hinges, plus the forearm with the envelope.
- **The bell:** the yoke is pinned; the clapper is a child pendulum. A damped oscillator gives θ(t) = θ₀e^(−t/τ)cos ωt.
- **The envelope:** the flap is hinged at the fold.
- **The folded coat on the bench:** the same coat panel cut into 3 hinged pieces and folded flat.
- Silhouette read test: every acting beat (I.4 lay key, II.2 lift coat, V.3 run and drop) must read with colour removed. The critic views a greyscale threshold of those frames.

**SCION 44 · Multiplane Parallax, Spatial Collage Swarm.** The station is a 2.5D stage built from foraged photographs.
- The planes, from far to near:
  - far sky and trees;
  - the shed or station house;
  - mid grass;
  - the bench plane;
  - the figure plane;
  - a near grass band.
- Parallax ratios: far 0.35, mid 0.6, bench 0.8, figure 1.0 (camera-locked in V.3), near 1.6.
- **The cover's streak is produced here.** Each output frame is the mean of N sub-frames (N = 36, 180° shutter) of the moving stage. The streak length per plane equals that plane's travel during the exposure. The figure, which the camera tracks, stays sharp except where its shins really swing.
- Streak strength follows the camera speed curve in §6.
- Occlusion order follows §5.6. The II.2 coat swap is a holdout behind the bench plane.

**Stencil colour** (a method shared by all three; Pathécolor practice). Each plate is printed monochrome. Then green, red and brass dye masks are cut, keyed from the original hues where it is the grass, hand-polygoned for the coat. The dye is laid as a multiply/transparent colour, so the photograph's tone shows through the dye.

## 8 · Aesthetic target (from `assets/references/hortense.webp`, the Points cover)

The reference is studied but never copied, traced or pasted.

**Medium.** A colour photograph of a running figure, taken with a panning camera. The figure is partly sharp and partly smeared; the ground and background are smeared into long horizontal streaks.

**Tonal range (measured).**
- Luma percentiles: p5 = 0, p25 = 57, p50 = 86, p75 = 126, p95 = 228.
- This is a dark-mid image with true blacks (the skirt is #000000) and a few hot highlights (the cream leg, around #e0c96a to #e1e5b2).
- Median HSV saturation is 170/255: strongly saturated.

**Palette (sampled with PIL; quantised plus region medians).**
- Red top: **#e2011b**.
- Black skirt: **#000000**.
- Black type: **#010201**.
- Green streaks:
  - yellow-green **#6ba334**, **#80b13b**, **#b2ae44**;
  - mid green **#2f9036**, **#46a63d**;
  - deep green **#0a7732**, **#1b4c22**.
- Earth at the foot: ochre **#837030** and red earth **#8d3b24**.
- Highlight: cream **#e1e5b2**.
- The title red is darker than the top red (quantised around #a50917).

**Light.** Flat, overcast-to-bright daylight with no hard cast shadows. The Bourré plates are overcast, which fits.

**Texture.** All texture is motion texture. In the lower half the luminance gradient is stronger vertically than horizontally (ratio gy/gx = 1.55, measured), which is the signature of horizontal streaks. There is no added grain.

**Framing and scale.**
- The figure is cropped very tight. The head is out of frame and the torso fills the top third.
- A leg crosses the middle as a pale diagonal.
- The streaked ground fills the lower half under the type.
- **The film's V.3 must be framed tighter than kf-1:** at least 55 % of frame height is coat, and the cap is at the top edge or cropped. kf-1 showed the whole figure at about 75 % height with the head inside the frame. We move toward the cover.

**Typography.**
- A slab typewriter face, set left and stacked: the author in black and larger (`Jacques` / `Roubaud`), the title in red.
- We use Courier 10 Pitch Bold (Bitstream, X11 free licence; `/usr/share/fonts/X11/Type1/c0583bt_.pfb`) in black #010201 and red #a50917 / #e2011b.

**Pacing.** The cover is one instant of speed. The film earns it: still in I, drifting in II–IV, full speed only at V.3, still again in VI.

**How we get there with real material and technique:**
- Red and green come from stencil dye over a real monochrome print of a real FSA coat and real Bourré grass, not from a colour filter.
- The streak comes from a real pan exposure: temporal integration of the moving stage.
- The tight crop is real camera framing of the rig.
- A grade is applied only to unify: one shared curve per plate so the dyed greens sit within the sampled green range.

## 9 · Swarm units

These units come from prompt §5. Coupled tasks are merged, giving 4 units. The montage editor/assembler and the independent reviewer are run separately by the workflow.

All media goes under `films/sources/la-belle-hortense/<role>/`. All inspectable outputs go under `films/swarm/la-belle-hortense/`.

**U1 · structure.** Combines the combinatorial editor, mystery designer and verifier.
- It writes `structure.json`:
  - the six orders;
  - slot times;
  - each appearance's function, on-screen content, caption (FR + EN) and sound cue;
  - knowledge_in and knowledge_out per module;
  - the clue graph (clue → claim, with t and the reveal window);
  - the alternative explanations and what refutes each.
- It writes `verify.py`. The script runs on structure.json alone and asserts:
  - σ maps each module to the next;
  - σ⁶ = id;
  - there are no duplicates;
  - every support of S is at t < 39.0 and some support is at t ≤ 21.0;
  - the reveal (V.3/V.4) is not a necessary support of itself;
  - each cloche slot has a bell cue.
- It also writes `baseline.json`, the story-order counter-cut, and shows that verify.py rejects it.
- Its log is `verify.txt`.
- It owns the fresh-reader protocol text, `reader-protocol.md`: stop at 39.0, name the leading explanation and the motif that changed it.

**U2 · forage-cut.** Combines forager, licence verifier and GrabCut cutter (SCION 29).
- **Re-verify the licences of on-disk items:**
  - LoC 2017844115 (from LoC JSON if reachable, else the earlier record in `credits/la-machine-a-tuer-le-temps.json`);
  - Bourré 50866795131, 50866798791 and 50866891867 (Commons extmetadata);
  - Skeletonkey.png (CC0);
  - the Highsmith park bench (from `les-lieux-dune-fugue` sources);
  - the Fridingen bell, Concrete Steps 2, Door handle creaking, Squeaky door hinge, Keys hitting tree 2, and lock-3-open.
- Copy these items into this film's sources.
- **Forage new items** (under 75 MB in total):
  - **The visitor:** a woman in a coat, walking, with legs visible, with a handbag or letter. LoC FSA/OWI "No known restrictions", or a Commons PD-USGov image.
  - **A station bell on a bracket:** Commons, a PD/CC photo (e.g. "Bahnhofsglocke", "cloche de gare").
  - Optionally a PD envelope photo.
  - Check the MIA cache once (forage.py) for bell or door sound with source audio. *Communications and Our Town* (1947, 381d177e) has a belfry. Credit any use as "via movingimagearchive.com".
- **Cut** each into RGBA pieces with masks and failure masks.
- **Write `rig.json`:** for every piece, its source id, crop box, pivot points, parent and angle limits.
- **Outputs:**
  - `swarm/la-belle-hortense/ledger.json`: each item with title, author, licence, licence_url, source_url, file_url, local path, used_as and verification date.
  - `swarm/la-belle-hortense/rig.json`.
  - A draft of `films/credits/la-belle-hortense.json` with the same records.
  - Cutouts in `sources/la-belle-hortense/forage/`.

**U3 · animator.** Combines the authors of the scenes, the Reiniger rig, multiplane, stencil and pan exposure (SCIONs 2 and 44).
- Build a reusable `scene` module: the stage, the dye masks, the shutter integrator and the rigs from rig.json.
- **Render the TEST SHOT V.3 first** (42.0–43.5 plus 0.5 s handles). Write `testshot.mp4` and the still `testshot_43.3.png`, plus a side-by-side board of the still next to hortense.webp.
- Then render the remaining animated beats as prepared clips or frame functions:
  - I.1–I.6, the walk, envelope, key lay and receipt fall;
  - II.2, the coat lift and swap;
  - the bell swing (all cloche slots);
  - III.4, the far red crossing;
  - IV.5, the near blur;
  - V.1–V.5;
  - VI.1, the bell damping.
- Write `scenes.json`: for each slot, its frame function or clip path, the plane list, the parallax ratios, the streak strength, the rig poses, and the invariant checks (pivot distance and parallax order) as measured.
- Media goes in `sources/la-belle-hortense/animator/`.

**U4 · print-sound.** Combines handmade print and sound design.
- **Handmade print objects:**
  - the receipt "REÇU N° 6" (with the strike-through, underline and RENDU stamp states);
  - the envelope, if not foraged;
  - the enamel `6` door plate;
  - the title card type;
  - the slot-line and caption typesetting;
  - the end-card matrix with braid strands.
- **The sound:** decode the foraged recordings to wav with ffmpeg, cut each cue, and lay the cue sheet.
  - Bell strikes at exactly 0.4, 4.6, 16.6, 27.1, 33.1, 46.6 and 57.2.
  - Slot clicks at every slot start.
  - Steps, latch, hinge, tink and wind.
  - Declared silences at 37.5–39.0 (after the click) and 63–66.
- **Outputs:**
  - `swarm/la-belle-hortense/sound_cues.json`: t, file, gain, source id and licence.
  - `swarm/la-belle-hortense/print.json`: each handmade object and its file.
  - PNGs in `sources/la-belle-hortense/print-sound/print/`.
  - WAVs in `sources/la-belle-hortense/print-sound/sound/`.

**Dependencies.**
- U1 and U2 start at once.
- U3 needs U2's rig.json and cutouts. It starts with the conductor and plates, which are already on disk.
- U4 needs U1's captions and slot times. These are fixed in this plan, so U4 can start at once.
- The editor assembles `films/la-belle-hortense.py` with kit.py from U1–U4's outputs.

## 10 · Acceptance bar

The fresh critic checks these by watching the film and reading the ledger.

1. **Permutation on screen (structurally verified and measured).**
   - `verify.txt` passes: I ABCDEF → II FAEBDC → … → VI BDFECA, σ⁶ = id, and no duplicates.
   - Sampling the film at t = 3.75 + 9(i−1) + 1.5(k−1), the red-caps word in the slot line equals oᵢ[k] for all 36 slots.
   - The motif shown in each sampled frame is that motif.
2. **Background → evidence (perceptually judged and structurally verified).**
   - The frames at 3.75 s and 8.25 s show the red coat on the bench, and the key laid on it at 8.25 s. No caption names the coat before II.2.
   - The frame at 43.3 s shows the same coat, with the same source id and cut in rig.json, worn and running, with the key leaving its hem.
   - A viewer can say "the red coat was on the bench in the first scene."
3. **Fair play and reachability (structurally verified and perceptually judged).**
   - In `structure.json` the supports of S lie at ≤ 21.0 s, and none is at or after 43.2 s. `baseline.json` fails verify.py.
   - A fresh reader paused at 39.0 s records a leading explanation and the motif that changed it, before seeing V. The record goes in the reader log.
4. **Aesthetic side by side, colour and texture (measured and perceptually judged).**
   - Put the film frame at 43.3 s beside hortense.webp on one board.
   - The coat region's median hue must be within ±8° of #e2011b, with saturation ≥ 0.75.
   - Green-dyed pixels must cover ≥ 25 % of the frame.
   - The lower half's gy/gx gradient ratio must be ≥ 1.3, against 1.55 for the reference. That shows horizontal pan streaks, made by sub-frame integration that scenes.json documents, not by a blur filter.
   - The critic judges the two as the same family: red on streaked green with black.
5. **Aesthetic side by side, framing and type (measured and perceptually judged).**
   - On the same board, the coat spans ≥ 55 % of frame height in V.3 and the head is at or past the top edge.
   - On a second board, the 1.5 s title frame beside the cover shows a stacked slab typewriter face, with the author in black and the title in red, over a real streaked green ground.
6. **Genuine frame-by-frame animation (measured).**
   - In V.3, the shins change pose on every frame.
   - The falling key's measured positions fit a parabola, and it rotates.
   - The bell angle follows a damped oscillation over its slots.
   - Every pivot-to-parent distance stays constant within 1 px.
   - The parallax order near > mid > far holds in every pan frame.
   - The I.4, II.2 and V.3 actions read in a greyscale silhouette view.
7. **Sound on the clock (measured).**
   - Onsets of the foraged bell recording occur within ±0.1 s of 0.4, 4.6, 16.6, 27.1, 33.1, 46.6 and 57.2 s, and nowhere else.
   - A slot click sounds at every slot start.
   - The declared silences are present.
8. **Material honesty (structurally verified).**
   - Every element named in scenes.json traces to `credits/la-belle-hortense.json` with PD, CC0, CC BY or CC BY-SA, or to a named handmade object in print.json.
   - Nothing comes from the novel or its cover.
   - The film is ≤ 75 s and ≤ about 6 MB.

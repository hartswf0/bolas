# Bang Bang: swarm plan (Direction 2, "Planche gravée")

Revision base: `proposals/kf-2.png` + `proposals/kf.py` / `pen.py` (deterministic, seed 123). Film slug `bang-bang`. Render through `films/kit.py` (`Film`, 960x540, 24 fps). Planned length **30.0 s** (Hard proof window 25–35 s).

## 1 · Creative thesis

The narrator is a **magpie**. It already has the ability the man is trying to build. The image and the voice report the same three attempts, but they tell you different things.
- **The image** is articulated cut-paper puppets made from real 1870s–1890s flying-machine engravings, pinned to a cream storyboard sheet. It shows the **mechanism**: what the paper wing, the rubber-band rotor and the glider physically do.
- **The voice** is the magpie's handwritten slips, pasted in the right-hand column. It gives the **witness's valuation**: what a flier thinks the man is doing, and why that is reasonable.

The man thinks he is climbing. The bird knows that a raised nose is how you stop, so it calmly corrects its own slip from *monter* to *s'arrêter*, and to the bird the crash reads as a landing that was a bit quick.

## 2 · Defining beat and baseline

- **Defining beat: BB-08, the stall (21.0–24.0 s).**
  - The engraved glider pitches nose-up from 5° to 35°.
  - Its forward drift decays to zero.
  - The pilot's legs swing forward on their own brass split pin.
  - The glider hangs still for 0.6 s and then begins to slide back.
  - On the slip, at **22.0 s** (frame 528), the pen strikes through *monter* and writes *s'arrêter* above it.
- **What the viewer should be able to point to:**
  - (a) The frame where the nose is above the horizon line and the puppet's x stops advancing. This is the first readable failure frame, planned at **f528–f540**.
  - (b) The strike landing on that same frame.
  - (c) The legs, which are still swinging after the body has stopped. This is secondary motion on the pin.
- **Baseline.** The same BB-07–09 boards, unchanged image, with a human reporter's slips (typed newspaper strip, no correction): "L'appareil se cabre, décroche, s'écrase. Échec." The editor renders it as `baseline_bb07-09.mp4` (9.5 s). The bird version passes if the critic reports an inference from the bird's voice that the baseline does not carry (stopping or landing, not failure). It must also carry no new fact about the mechanism that the image does not show.

## 3 · Lineage Genome (compact)

| field | value |
|---|---|
| source | *Bang Bang*, Jean Jabely and Raymond Queneau, c. 1958 dossier (Gazette Drouot lot 186): a felt-pen storyboard of early flying machines, with Queneau's commentary spoken by a bird. The reference is page 2. |
| source medium | Ink on cream paper. Stacked ruled panels in the left column, each with a punched dot. A handwritten commentary column on the right. A/B/C/D part labels, an arrow, a struck-out word. Show-through from the facing page. |
| target medium | A 30 s screen animatic. Cut-paper engraving puppets animated frame by frame on 2s, on a storyboard sheet, with the commentary on pasted paper slips. Foraged ambience and a magpie call, plus handmade FX. |
| preserved relation | Image column = the mechanism. Commentary column = the bird's account. They are joined panel by panel, and the commentary is allowed to correct itself (the struck word). |
| optics change | Pen drawings become real 19th-century engraved line, printed onto cream card. A camera pushes in to the active panel. Cast shadow encodes height. |
| formalism change | The static board becomes timed boards. Each BB-id carries a frame range, and the cue anchor is frame-exact. |
| concept change | Queneau's historical names and dates are replaced by one **fictional** inventor ("Monsieur Pique-Vent") operating real engraved machines. This is a visible montage, and the slips name no historical person. |
| sound change | The silent page gains a foraged magpie call, field air and handmade paper and pin FX. The voice stays written; no TTS exists. |

**Formation epochs (weight 0–100):**
- **1870s–1890s aeronautical engraving (Pénaud 1871–75, Popular Science Monthly 1894–95): 90.** The puppet bodies are literally these prints.
- **1950s Oulipo-adjacent storyboard dossier (Jabely/Queneau, c. 1958): 85.** The page grammar and the bird narrator come from it.
- **1920s Reiniger cut-out theatre: 60.** Pinned joints, contour-led acting, held poses.
- **1970s Gilliam collage animation: 35.** Engravings recombined into a comic event. This is kept low, so the joke never hides the mechanism.
- **Early animation on 2s / exposure sheets (1910s–30s): 40.** The timing grammar.

**Uncertain claims.** The exact date of the dossier ("c. 1958") and whether Queneau wrote every line are uncertain; both follow the Drouot listing. Pénaud's hélicoptère is rubber-powered. That is widely documented, but the ledger must cite a source or mark the claim *uncertain*.

## 4 · Olog and central operation

- **◻Witness** `W = {id: "PIE", kind: magpie, affordances: [flies, lands, perches, hops, sees wind in feathers], perceptual_limits: [sees only what is in the panel and its own field; no names, dates, numbers, physics terms; cannot read], attitude: calm, approving, literal-minded}`.
- **◻Attempt** `A = {id, mechanism, action, material_outcome, status: source|fiction, evidence_id}`. There are three:
  - **A1, paper wing.** HANDMADE fiction. Ribbed paper wing strapped to one arm. Flapping bends the tip; he hops off a low wall, the paper folds back and he lands on his seat. The outcome is "pof".
  - **A2, rubber-band rotor.** The *machine* is SOURCE: Pénaud's hélicoptère, foraged engraving, rubber-powered (evidence `EV-PENAUD-*`). Using it is fiction. He winds it, it rises about 1 panel-height, the band snaps and it drops.
  - **A3, glide.** The *machine* is SOURCE: the Lilienthal apparatus, PSM 1894. The flight is fiction. He runs, lifts off, pitches up, stalls, slides back and crashes.
- **◻StoryboardCue** `C = {board_id, frame_range[f0,f1), attempt_id, image_event, image_event_frame, comment_text, comment_anchor_frame, fx[], contrast: str}`. The invariant is `|image_event_frame − comment_anchor_frame| ≤ 1` for anchored cues. `contrast` names the inference that the comment adds and the image does not.

**Central operation: `reframe(C): (Attempt event, Witness) → comment`.**
- **Typed preconditions:**
  1. The `image_event` is visible in-panel at its frame. It is a structural property of the exposure sheet.
  2. The Witness can perceive it: the bird's head is in the panel, or the event lies within the bird's field (the head angle points at the event ±30°).
  3. `comment_text` uses only Witness vocabulary. It passes the lexicon gate: no proper names, years, numbers or physics jargon such as *décrochage*, *incidence* or *portance*. The graphite board header may say "le décrochage", because the board artist writes it, not the bird.
  4. The comment is not a paraphrase of the image. `contrast ≠ ""`, and the contrast is a value or comparison drawn from the bird's own ability.
- **Observable consequences:**
  - Ink strokes of the comment begin within ±1 frame of `comment_anchor_frame`.
  - The FX (slip-paste flap, pin tick, thump) lands on the same frame.
  - The reader can state two different facts:
    - from the image: "the nose rose and it stopped"
    - from the slip: "for a bird, raising the nose is how you stop and land"
- **Counterexample (fails).**
  - At BB-08, a slip reads "Il cabre à 35°, la vitesse tombe sous la vitesse de décrochage." It fails two gates:
    - Witness gate: numbers and jargon.
    - Precondition 4: it is a paraphrase of the image.
  - A second counterexample: the slip reads "Il tombe." at 25.2 s. It merely explains the drawing, so there is no contrast. Repair rule §8: keep the attempt and replace the comment with a different point of comparison.
- **Replay and alternate views:**
  - **Equivalent.** Swapping the BB-07 and BB-09 slips is a valid experiment, because the bird is in frame for both. The image facts are unchanged, so image-only reads are equivalent.
  - **Divergent.** Moving the *monter→s'arrêter* correction from BB-08 to BB-07 breaks the anchor: during the run-up the nose is level, so "stop" has no referent. The combined read diverges even though both components exist.
  - **Image-only and voice-only reads.** Image-only must yield "it failed". Voice-only must yield "he landed sensibly". They are allowed to disagree; that disagreement is the work.
  - **Changing A3 from failure to success** (an alternate branch) invalidates the contrast fields of BB-08 and BB-09, and they must be rewritten. This is noted in the cue file as `depends_on_outcome: true`.

## 5 · Invariants

1. **Evidence or visible fiction.**
   - Every mechanism claim, such as rubber-powered or weight-shift glider, carries an `evidence_id` in the ledger or is marked fiction.
   - The scene stays visibly a montage: pinned pieces, card edges, cast shadows. No slip names Lilienthal or Pénaud.
2. **Stable narrator viewpoint.** One bird (PIE), one hand, one paper stock, first person throughout. Graphite board headers are the board artist's, not the bird's.
3. **Distinct inference.** Each crucial image and its cue contribute different information, as in Olog precondition 4.
4. **Attempt and consequence.** Each attempt shows both. The A3 consequence is the crash at f605 (25.2 s), with the wreck held to the end.
5. **Puppet integrity** (Reiniger and GrabCut gates).
   - Pieces never detach.
   - Each pivot is a fixed point in both parent and child coordinates (numeric test: drift of 1 px or less).
   - No background islands in the cutout masks.
   - Joint angles stay within declared limits.
6. **Secondary energy decays** (#41). Leg and wing-tip swing begins after the primary motion changes and decays to under 1° within 1.0 s once the body is still. No idle wiggle.
7. **Two-value page.** Only ink (the engraving line and the pen) and cream paper. The only exceptions are brass pin heads, soft cast shadows and the graphite margin; there are no grey card fills. This fixes kf-2's grey ground.
8. **Licence.** PD, CC0, CC BY or CC BY-SA, read from Commons extmetadata or the LoC rights field, and recorded in `films/credits/bang-bang.json`.

## 6 · AESTHETIC TARGET (from `assets/references/bang.webp`, 1000x844, sampled with PIL)

- **Medium.** A real made object: a storyboard sheet with ink line on cream paper. Here the ink line is *printed engraving line* (foraged) plus *pen line* (handmade: frames, labels, slips' hand, ground line).
- **Tonal range.** Two values.
  - Measured: about 1.6 % of pixels are ink (luminance below 120); about 2.6 % are midtones (120–200). Those midtones are almost all antialiasing and show-through. The paper is about 96 %.
  - Target: ink coverage of 3–9 % per frame, because the engravings are denser than pen. There must be no large grey fills. Midtone pixels, excluding shadows, stay under 8 %.
- **Palette (measured):**
  - Page paper: RGB **(242, 228, 212)**.
  - Panel interior, slightly duskier: **(228, 216, 202)**.
  - Left margin: **(234, 220, 203)**.
  - Show-through ghost: about **(206, 195, 185)**.
  - Darkest ink median: **(65, 53, 41)**, a warm brown-black felt pen with cores near **(40, 34, 30)**.
  - The film's paper must be this warm cream, not the cooler kit `PAPER` (243, 239, 228) or kf-2's greyish card. Engraving ink is printed at warm black (45, 38, 32), not neutral black. Brass pins **(176, 138, 62)** are the only colour accent and stay small.
- **Light.** Flat, even scanner or copy-stand light with no vignette drama. Cast shadows are soft and warm, (150, 130, 110) at under 35 % opacity, and only under pieces lifted off the card.
- **Texture.**
  - Paper tooth and low mottling.
  - The facing page shows through mirrored at 4–5 % density.
  - The engraving's own hatching and stipple is the only body texture. No added grain beyond kit default; no film-grain costume.
- **Framing and scale.** The reference stacks three landscape panels (about 1.45:1) in the left column, about 28 % of page width. Commentary fills the right column, one paragraph per panel, aligned to its panel. Each panel has a punched dot at top-left, 10–12 px at reference scale.
  - **Wide page shots** (0–1.0 s, 16.0–17.5 s, 27.5–30.0 s) show the full sheet with three stacked panels and slip column. This is the comparison frame.
  - **Active-panel push-ins**: the panel fills about 62 % of frame width, and the slip column stays visible at right.
- **Typography.**
  - **Bird's slips**: a loose French hand, built with the handmade `pen.hand` (Hershey-derived, per-word slant and baseline drift, felt nib), at about 11–14 characters/s write-on. It is not a typeset font: this fixes kf-2's set-looking slip. Each slip is a torn cream paper strip, the same paper stock, pasted with a brass pin.
  - **Board headers** (BB-id, seconds, "le décrochage") and the English gloss under each slip are in graphite.
  - **Part labels** A and B are inked in the panel, as in the reference.
  - There is **one struck-out word**: *monter*.
- **Pacing.** Page time, not cartoon time. Hold each pose on 2s (12 drawings/s). Hold 0.5–0.8 s after each consequence. Use one camera move per board. The FX are sparse.

**How we get there with real material.**
- Foraged engravings are thresholded and printed as ink onto the cream paper colour, so their line becomes the page's ink rather than a pasted grey photo.
- Every handmade object is drawn in the same warm ink on the same paper.
- Grading is limited to mapping each source's paper to (242, 228, 212) and its ink to (45, 38, 32).

## 7 · Technique SCIONs

| id | title | why | applied where |
|---|---|---|---|
| **2** | Lotte Reiniger: Articulated Shadow Theater | The puppet *is* the mechanism. A pinned hierarchy (glider→hip pin→legs; magpie body→neck pin→head; rotor shaft→blades; inventor torso→shoulder→wing) with joint limits and an exposure sheet makes the stall legible through contour and pose alone. "Relationships read with all colour removed" matches the two-value page. | All boards. The exposure sheet drives every frame on 2s. The magpie's head steps through held angles, in bird-like jerks. BB-08 is acted entirely in silhouette and pose. |
| **29** | GrabCut: Cutout Extraction Swarm | The puppets must be cut from real engravings that contain adjacent objects: the pilot is entangled in the wing spars, the magpie sits on a ground line, and the helicoptère has a caption. GrabCut with scribble seeds, plus line-art closing and manual contour repair, gives clean RGBA pieces with no background islands, and the failure masks are exported. | Pre-production (unit 2): about 9 pieces from 3–4 engravings. Repaired regions (for example the pilot's hands behind spars) are re-inked by hand and logged. |
| **41** | Secondary Dynamics: Inertia and Restraint | The test shot hinges on follow-through: the legs keep swinging after the body stops. The paper wing's tip lags and folds, and the rotor's snapped band whips. Springs and dampers driven by primary pose impulses, decaying to rest, make weight readable. | BB-01 (paper-wing tip, 2 segments), BB-03 (band snap whip), BB-08/09 (hip pin spring, wing-root droop at impact). Semi-implicit Euler at 240 Hz substeps, sampled on 2s. |

The supporting methods borrowed in passing are FK (#32, the pose as joint angles) and Sound-to-Action (#47, the cue anchors). They are not separate owners.

## 8 · Timed shot list: Hard proof (§6) carried out exactly

Total 30.0 s = 720 frames at 24 fps. The animation is on 2s. Every board row carries its frame range, a source or fiction id, the observed action and the cue. FORAGED and HANDMADE elements are listed per shot.

| board | time / frames | on screen | heard | elements |
|---|---|---|---|---|
| **BB-00** page | 0.0–1.0 / f0–24 | The full cream sheet, "planche 1". Three empty punched panels in the left column, a blank slip column, show-through. | Field air fades in; paper settle. | HANDMADE sheet, panels, punch dots, graphite "Bang Bang — planche 1". FORAGED air (MIA refuge clip, see unit 3). |
| **BB-01** paper wing | 1.0–8.0 / f24–192 | Push into panel 1. Pique-Vent (the cut PSM pilot puppet) stands on a pen-drawn garden wall with a **ribbed paper wing** strapped to his right arm. The magpie is on a gatepost at left. He flaps 3 times; the arm pivots ±40°. The wing tip lags (#41) and on the third flap folds back. He hops at 5.6 s, sinks and sits down on the flowerbed at **6.4 s (f154)**. The magpie's head tracks him in 4 held angles. Label **A** on the wing. | Paper rustle on each flap; a soft "pof" (thud, low) at f154. Magpie chatter at 1.2 s as the first slip pastes. | FORAGED: PSM pilot puppet (`PSM V46 D647`, PD); magpie engraving (Brehms *Elster*/*Pica pica*, PD, or fallback `Corvus scapulatus (Brehms)`, PD, flagged "pied crow, not a magpie"). HANDMADE: the paper wing, an actual cut cream piece with pen ribs; wall; flowerbed; panel frame. |
| | | Slip 1 (pasted 1.2 s): *"Il s'est fait une aile en papier."* Slip 1b (4.2 s): *"Le papier plie quand il veut. Le mien, quand je veux."* Slip 1c at f154: *"…pof."* The graphite gloss is in English. | | HANDMADE slips (pen hand). |
| **BB-02/03** rotor | 8.0–16.0 / f192–384 | A wipe to panel 2 (pin-dot iris). Pénaud's **hélicoptère** (cut engraving, two rotors on a shaft) is held in the pilot's hands. Winding 8.0–10.5 s: the top rotor turns in steps, and a graphite tally counts the turns (12). Release at **10.6 s**: the rotors counter-turn, decelerating with the band's unwinding; it rises about 120 px and the magpie looks up. At **13.0 s (f312)** the band snaps: a pen squiggle whips (#41) and the machine tips and drops onto the turf at 13.8 s. Label **B** at the band. | Rubber creak per winding step; a flutter whirr on release; "clac" (click) at f312; small thump at f331. Magpie chatter at 11.0. | FORAGED: `Pénaud's flying models` plate 3, fig. 1 (PD). HANDMADE: the band as a pen line, tally, ground. |
| | | Slip 2 (8.4 s): *"Ensuite, un moulin à élastique."* Slip 2b (11.0 s): *"Il le lâche, et le moulin monte tout seul. Lui reste en bas. C'est sage : il faut bien quelqu'un pour regarder."* Slip 2c at f312: *"clac."* | | |
| **BB-06** page turn | 16.0–18.0 / f384–432 | Pull out to the full sheet. The page turns (a card flip, rendered as a foreshortened scale-x with an edge shadow) to "planche 2": three stacked panels, BB-07/08/09, each holding its key pose in still form. The camera pushes into panel 1. | Paper turn; air. | HANDMADE sheet 2. |
| | | Slip 3 (16.6 s): *"Enfin, les grandes ailes."* | | |
| **BB-07** run-up | 18.0–21.0 / f432–504 | The glider puppet (PSM Lilienthal apparatus with pilot, legs on the hip pin) runs down a pen hill, right to left. Legs alternate on 2s at ±28°. The glider bobs ±2°. The magpie is on a fence post. Lift-off at **20.4 s (f490)**; the cast-shadow offset starts growing (height). | Footfalls on turf (kit `step`, grass), wind rising. | FORAGED glider (PD). HANDMADE hill, fence, shadow. |
| | | Slip 4 (18.3 s): *"Il court face au vent. Bien."* | | |
| **BB-08** stall (TEST SHOT) | 21.0–24.0 / f504–576 | A push-in tightens to about 75 % of the frame. Pitch θ eases from 5° to **35°** over f504–f540. Forward x-speed decays to zero by **f540 (22.5 s)**. Legs swing forward on the hip pin (spring k, damping ζ≈0.25), overshooting about 18°. **Hang**: f540–f554, still, nose up, legs still swinging and decaying. The magpie takes off and **flies level past him**, flap cycle on 2s, showing the ability he lacks. It flares nose-up itself at f560 to brake, which is the same gesture done right. From f556 the glider slides **tail-first** backward and down. Part labels: **A** the wing, **B** the raised nose, with a pen arc marked "35°" in graphite (board artist's). The header is "BB-08 21.0–24.0 s le décrochage" (graphite). | Wind cuts out at f528. **Declared silence** f540–f554: air bed only, no FX. A pin tick at f528 as the strike lands. A wing-flap whoosh as the magpie passes (f548–f560). | FORAGED glider, magpie (flying pose: cut from a PD flying-corvid engraving if found, else a handmade flying pose built by re-pinning the cut wing piece; logged). HANDMADE arc, labels, horizon line. |
| | | Slip 5 (21.2 s): *"Il lève le nez pour ~~monter~~"*. The strike lands at **22.0 s (f528)** and *"s'arrêter"* is written above it f528–f548. Slip 5b (23.0 s): *"Moi aussi, quand je veux me poser."* | | |
| **BB-09** fall | 24.0–27.5 / f576–660 | Push to panel 3. The tail-first slide steepens; the nose drops through the horizon at 24.6 s. The shadow converges on the glider. **Impact f605 (25.2 s)**: shadow and glider touch. The right wing piece droops on its root pin (#41, one bounce). The legs whip and settle by f636. The wreck is held. The magpie lands beside the wreck at **26.6 s** with a clean flare, a two-hop settle, then pecks once. | **Thump at f605** (kit `thud` + paper crumple) and a magpie chatter burst at 25.6 s; then air. | FORAGED glider, magpie. HANDMADE flowerbed, ground, shadows. |
| | | Slip 6 (24.2 s): *"Donc il se pose."* Slip 6b, write-on reaches *"Krach !"* at f605. Slip 6c (26.0 s): *"Un peu vite. Mais au bon endroit."* | | |
| **BB-10** board | 27.5–30.0 / f660–720 | Pull out to the full sheet 2: three stacked panels holding their key poses (run, stall at 35°, wreck), with the bird's slips stacked in the right column, aligned one per panel, and *monter* visibly struck. A graphite margin note runs vertically beside panel 2 (the reference's marginal device): "BB-08 f504–576". Hold 1.5 s. | Air fades; one last soft chatter at 28.4 s; out. | HANDMADE. |

The first readable failure frame is planned at **f528–f540**: the nose is above the horizon and x-advance falls under 0.5 px/frame. The critic locates it independently.

**Baseline render** (editor): `baseline_bb07-09.mp4`, f432–f660, with the same picture and the human reporter's slips: *"L'appareil se cabre."* / *"Il décroche."* / *"Il s'écrase. Échec."* There is no strike and no magpie chatter.

## 9 · Swarm units (the editor/assembler and independent reviewer run separately)

**Unit 1: Invention researcher and forager** (`mode: forage`).
- **Licences.** Re-verify the licences of LIL-START, PENAUD, CROW and LIL-LOC from Commons extmetadata. Forage on Commons:
  - (a) A PD **magpie** engraving (*Pica pica*, Brehms Tierleben or a similar wood engraving), sitting and, if possible, flying.
  - (b) Optionally, a PD side-view Lilienthal engraving (PSM plates), only if it reads the stall better than D647.
  - (c) A magpie call recording (CC BY / BY-SA / PD).
- **Moving Image Archive.** Audition the cache (`forage.py`, clips `7ad22207`, `a8cb43a2` and others) for clean outdoor air or field ambience, and confirm the US-government (FWS) status from the page.
- **Evidence and fiction ledger.** Write one entry per mechanism claim, with citations and a status of source, fiction or uncertain.
- **Outputs.** `films/swarm/bang-bang/ledger.json` (sources with licence, file hash and used_as; evidence; fiction ids A1–A3) and a draft of `films/credits/bang-bang.json` entries. Media go in `films/sources/bang-bang/research/`. Keep new downloads under 30 MB.

**Unit 2: Board artist and puppet cutter** (`mode: both`; SCION #29, #2, #41).
- **Cutting.** Cut the RGBA pieces with GrabCut seeds and line-art closing:
  - glider body and pilot torso
  - legs (separate, on the hip pin)
  - helicoptère shaft and rotors
  - magpie body and head (neck pin)
  - a flying magpie
  - the PSM pilot alone for A1 and A2, with the occluded spar region re-inked by hand and logged as a repair
- **Handmade pieces.** Build the paper wing, both sheets (warm cream, show-through), the punched panels, the wall, hill, fence and flowerbed, the brass pins, and torn slip paper.
- **Rig and exposure sheet.** Write a rig with pivots and limits, and a per-frame exposure sheet on 2s for all boards. Implement the spring-damper for the hip, wing tip and band.
- **Test render.** Render **BB-08 alone** (f504–576) as `bb08_test.mp4` plus a contact sheet, with tests: pivot drift of 1 px or less, angle limits held, decay under 1° within 1 s.
- **Outputs.** `films/swarm/bang-bang/rig.json` (pieces, source ids, pivots, limits, mask stats), `exposure.json`, `bb08_test.mp4`, `bb08_sheet.jpg`. Pieces and masks go in `films/sources/bang-bang/board/`.

**Unit 3: Writer and timing/sound** (`mode: both`; #47 cue anchoring).
- **Text.** Finalise the magpie's slips (French, with English graphite gloss), the struck word, and the baseline reporter text. Run the lexicon/witness gate on every line.
- **Cues.** Write the cue sheet with frame anchors and contrast fields (`depends_on_outcome` flags).
- **Stems.** Build the sound stems:
  - foraged magpie chatter and field air (from unit 1's picks)
  - handmade FX: paper flap per slip, wing rustle, rubber creak, band snap, pin tick, thump + crumple, page turn
  - the declared silence f540–f554
- **Swap experiment.** Prepare the BB-07/BB-09 slip-swap variant cue file.
- **Outputs.** `films/swarm/bang-bang/cues.json` (one row per cue: board, frame range, attempt id, image_event + frame, text, anchor frame, fx, contrast, witness-gate result) and `films/swarm/bang-bang/stems.json` (each stem: path, sources, peaks at anchor frames). WAVs go in `films/sources/bang-bang/sound/`.

The editor assembles `films/bang-bang.py` from rig, exposure, cues and stems via kit, plus the baseline.

## 10 · Acceptance bar (falsifiable; verify by watching, then by the ledger)

1. **Stall readable from the image alone.** With the sound muted and the slips masked, a viewer of BB-08 at normal speed can name "the nose went up and it stopped, then fell back". The first frame where x-advance falls under 0.5 px/frame with θ ≥ 15° lies in f520–f545 (measured from `exposure.json`). Labels: perceptually judged plus measured.
2. **Cue anchor.** The strike through *monter* begins within ±1 frame of the nose crossing 15° (planned f528). The "Krach !" write-on and the thump peak both land within ±1 frame of the shadow-contact frame (f605), measured from `cues.json` and the stem peaks.
3. **Distinct inference and witness gate.** Every slip passes the lexicon gate (no names, years, numbers or physics terms). In the BB-07–09 comparison against the baseline render, the critic can write one sentence each:
   - image-only: failure
   - voice-only: a deliberate stop or landing
   - combined: the bird reframes the failure as reasonable

   If voice-only and image-only yield the same claim, this fails.
4. **Aesthetic, side by side (page).** Frame f700 (wide board) beside `bang.webp`:
   - three stacked landscape panels in the left column, each with a punched dot
   - commentary aligned one paragraph per panel in the right column
   - a visible struck word and A/B part labels
   - paper median within ΔE ≤ 6 of (242, 228, 212)
   - darkest-ink median within 25 RGB units of (65, 53, 41)
   - no grey card fills; non-shadow midtone pixels under 8 % (measured with PIL)
5. **Aesthetic, side by side (line and hand).** Frame f540 beside the reference: all figure line is real engraving or pen ink in the same warm black on cream, and the slip text is visibly handwritten (variable baseline and slant), not a set font. Perceptually judged against both `bang.webp` and `proposals/kf-2.png`; it must meet or beat kf-2 on unity of ink and paper.
6. **Genuine frame-by-frame puppet animation.**
   - The legs swing on their pin and keep moving after the body stops (f540–f554), decaying to under 1° within 1 s of the body coming to rest.
   - No piece detaches: pivot drift of 1 px or less (rig test log).
   - The magpie's head changes angle in at least 4 held steps in BB-01.
   - The magpie flies and lands in BB-08/09.
7. **Proof completeness and ledger.**
   - Duration 25–35 s.
   - All three attempts (paper wing, rubber-band rotor, failed glide) show attempt and consequence, and the failure is a 3-board sequence with BB-ids and frame ranges visible on the page.
   - Every foraged item is in `films/credits/bang-bang.json` with a PD, CC0, CC BY or CC BY-SA licence read from metadata.
   - Every mechanism claim in `ledger.json` has an evidence id or a fiction tag.
   - No slip names a historical person.

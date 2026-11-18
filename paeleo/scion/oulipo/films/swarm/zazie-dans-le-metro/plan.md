# Zazie dans le métro: SCION swarm plan (round 3, build)

Slug `zazie-dans-le-metro`. The prompt is `prompts/zazie-dans-le-metro.md`, and the swarm workspace is this folder. Revision base: `proposals/` round 2. The user chose direction **2 · Zazie en papier** as the spine, with **3 · Bouche de métro** as the title gag. This plan is rebuilt from scratch on those two directions. Direction 1, the photograph of a real child, is **dropped entirely**: the user forbids any photograph of a real child, so `r2/Little_girl_*.jpg`, `Laughing_Girl_*.jpg`, `Young_girl_*.jpg` and `girl_mask.png` must not appear on screen or in the credits.

## 1 · Creative thesis

A paper girl wants one simple thing, a ride. The métro is on strike, so she runs for the tram instead. Paris then rewrites the chase three times:
- it moves her two kilometres in one frame;
- it turns her own laughing word, *Doukipudonktan*, into the queue that blocks her;
- it turns that queue into the stairs onto the tram's top deck.

She laughs through all of it. Her laugh, her orange collar and her wind-blown auburn bob are the anchor that survives every impossible cut.

Queneau's verbal play becomes a physical prop. The letters of the word are cut from paper, and they are first teeth, then a queue, then steps. Malle's editing tricks become operations on paper layers over real Paris plates.

**What would make it bland:** a slideshow of photochroms with a sticker girl sliding across them, a laugh that reads only because the caption says so, and letter tiles that are a title card rather than an object that gets in her way.

## 2 · Defining beat and comparison baseline

**Defining beat (the TEST SHOT, 6.0–9.0 s).** A close-up of the paper girl laughing with her hair blowing on the rue Royale, Madeleine columns soft behind her. On frame 192 (8.000 s) there is a jump cut. The face, collar, mouth phase and hair state are unchanged, but the plate behind is now the Place de Clichy, with *her tram* in it. When the beat succeeds, the viewer can point to two things:
1. "she's laughing", said with the sound off, before the cut;
2. "she's suddenly somewhere else, and closer to the tram", said at frame 192.

**Comparison baseline: cut B, the continuity control** (`zazie-dans-le-metro-control.mp4`).
- Frames 0–143 (0–6 s) are identical to cut A: the same straightforward chase.
- From 6 s it continues by ordinary continuity cuts. There is a reverse angle down the adjacent boulevard de la Madeleine at 8.0 s. At 12.4 s an ordinary cut shows her waiting in a real queue of paper commuters at the stop. She boards normally at about 18 s.
- The cut points (8.0 s, 12.4 s) and durations are the same as cut A, so the comic timing can be compared cut for cut.

**Negative control** (`zazie-dans-le-metro-negctl.mp4`, 3 s): the 7.0–10.0 s window of cut A with the puppet layer removed (anchor removed). The plate swap P1 → P2 must read as a plain change of location, not a gag (§7 of the prompt).

## 3 · Theory

### 3.1 Compact Lineage Genome

| field | value |
|---|---|
| source media | Queneau's novel *Zazie dans le métro* (1959, prose in néo-français: "Doukipudonktan" = *d'où qu'il pue donc tant*). Malle's film (1960), 35 mm Eastmancolor, 1.37:1, with undercranked chases, jump cuts and impossible continuity. |
| target media | A 22 s 4:3 picture, pillarboxed in a 960x540 / 24 fps kit render. An articulated **cut-paper puppet** (handmade), animated on twos (12 drawings/s), over **defocused PD Photochrom plates of Paris** (Detroit Publishing Co., c.1890–1900, Library of Congress). Captions are the voice. Sound is foraged street, tram and paper sounds plus kit-synthesized impacts. |
| preserved relation | A child's single goal survives a city that keeps changing the terms. A verbal ambiguity is turned into a physical setup and a filmic payoff. The laughing close-up is the emotional anchor. |
| optics change | Live-action lens defocus becomes a plate-plane blur, and the puppet sits on a sharper plane in front (multiplane depth). Eastmancolor print warmth is reached by choosing and grading real photochrom colour, not by a film filter. |
| formalism change | Camera and edit tricks become **operations on layers**: replace the plate under a fixed anchor layer (jump cut), and rewrite the identity of the tile nodes (match cut). |
| concept change | The métro strike is kept. The pursued vehicle is the horse-drawn tram with an *impériale* (top deck) from the Place Clichy plate, the vehicle Paris actually had in the plates' era. "Faire la queue" is made literal as a queue of letters. |
| sound change | Spoken dialogue becomes captions. Voice is absent by rule (no TTS, and no real child's voice). Impacts, holds and offscreen cues are scored. |

**Formation epochs (weight 0–100, with reason):**
- **Nouvelle Vague editing, 1959–60: 85.** Jump cuts and impossible continuity are the core operations under test.
- **Queneau and Oulipo verbal play, 1947–60: 80.** The prop is a word. The match cut depends on reading it.
- **Silent slapstick chase, Sennett and Keaton, 1912–28: 65.** The straightforward chase, the obstacle, and recovery by an absurd route. Malle is *commonly reported* to have quoted silent comedy. Treat this as an uncertain claim.
- **Reiniger articulated cutout, 1919–1950s: 60.** Pinned paper joints, replacement pieces and exposure sheets.
- **Photochrom colour printing, 1890–1910: 40.** It is the actual material of the city plates, and its tonal limits shape the palette.
- **Spring-damper secondary motion in computer animation, 1980s–2010s: 45.** Hair follow-through.
- **Graph-rewriting and collage identity change, Ernst 1929 to computational rewriting: 35.** The prop identity chain.

### 3.2 Olog (typed)

Objects (types):
- `Protagonist` = paper puppet **Z**, with articulated pieces (see §8).
- `Goal` = *ride the promised vehicle*. It is declared before any operation.
- `Vehicle` = tram cutout **V**: one RGBA cutout from LoC P2. It is the same pixels wherever it appears.
- `Location` ∈ {L1 rue Royale / Madeleine (P1), L2 place de Clichy (P2), L3 place du Châtelet (P3)}, and for the control only, L1b boulevard de la Madeleine (P4). L1b is adjacent to L1, so continuity is plausible.
- `Prop` = tile set **T** = 14 cut-paper letter tiles D-O-U-K-I-P-U-D-O-N-K-T-A-N. Its identity carries a `reading` ∈ {teeth, queue, steps}.
- `Anchor` = (Z silhouette bbox, collar colour region, mouth index, hair spring state, screen direction), and for vehicle anchoring, V.
- `Cut` ∈ {continuity, jump, match}.
- `Gag` = (goal, setup prop, conventional expectation, reversal, recovery beat).
- `Route` = graph of entrances, exits, obstacles and match anchors (§5.2).
- `GagOperation` changes one of {screen time, screen direction, object identity, apparent place} under a declared exception.

Arrows:
- `Z —wants→ Goal —names→ V`
- `Shot —at→ Location`
- `Cut —joins→ (Shot_out, Shot_in)`
- `Cut —preserves→ Anchor`
- `T —reading→ {teeth|queue|steps}`
- `T(queue) —blocks→ Z`
- `T(steps) —supports→ Z —boards→ V`
- `Gag —has→ consequence —changes→ distance(Z, V)`

#### Central operation: `AnchoredJumpCut(s_out, s_in, f)`. It changes *apparent place* under the declared exception "the city moves, the girl does not".

Typed preconditions (all must hold; the editor asserts them in code):
1. `Goal` declared: shot 1 holds the goal caption and the vehicle on screen for ≥ 1.5 s before frame `f`.
2. `Location(s_out) ≠ Location(s_in)`, and the real distance is impossible to run in 1/24 s. Madeleine → place de Clichy is about 2 km; *approximate, from the map, recorded as uncertain*.
3. Anchor continuity across `f-1 → f`:
   - puppet root transform centroid Δ ≤ 8 px and scale Δ ≤ 3 %;
   - mouth index follows the exposure sheet with no reset;
   - hair spring state (angle, velocity per strand) is carried, not re-initialised;
   - collar region hue is unchanged.
4. Screen direction is unchanged (wind and gaze both to frame right).
5. **V** is identifiable within 24 frames after `f` (in plate P2 it is the native tram, and V is the same cutout).

Observable consequences:
- With the sound off, a viewer reports a location change *and* that the girl did not move.
- The laugh visibly continues through the cut: the mouth cycle 4-5-4-6 runs on.
- **Downstream event:** distance(Z, V) drops. In L1 the tram was leaving frame right. In L2 it is ahead in mid-frame, so the gag advances the goal and is not random.
- The ledger shows `plate_id` changing at frame 192 while `anchor` fields stay within tolerance.

Counterexamples (must fail):
- **Negative control:** remove Z at the cut (`negctl.mp4`). It reads as an establishing-shot change with no joke and no anchor.
- **Broken anchor:** move Z by 120 px and reset the mouth to index 1 at the cut. It reads as a continuity error, not an intended trick.
- **No goal:** delete shot 1. The jump is a random surreal swap. Section 8 of the prompt says: lengthen the setup.

#### Second operation: `TileRewrite(T, teeth → queue → steps)`. It changes *object identity*.
- **Preconditions:**
  - same 14 tile objects (same glyph, paper colour and cut outline);
  - at the 12.4 s match cut, the lower tile row's baseline y and spacing are preserved within ±6 px between the last mouth frame and the first L3 frame;
  - each rewrite is triggered by an on-screen cause: TAN drops the jaw and the tiles fall; the queue's bump knocks them over into a stair.
- **Consequences:**
  - the queue blocks Z, an impact event with a sound on the contact frame;
  - the stair lets Z reach V's top deck.
- **Counterexample:** the tiles land at a different height (−60 px) or a different spacing. The match is lost and the queue reads as new, unrelated objects.

### 3.3 Where replay and alternate views agree and diverge

| interval | cut A (gag) | cut B (continuity control) | relation |
|---|---|---|---|
| 0.0–6.0 s | setup and straightforward chase, L1 | identical frames | **equivalent**: assert a per-frame mean abs diff < 1.0 |
| 6.0–8.0 s | laugh close-up, L1 | laugh close-up, L1 | equivalent picture; sound may differ only by the pre-cut hold |
| 8.0 s | jump cut to L2, anchor held | continuity cut to reverse angle on L1b; Z placed by eye-trace continuity | **diverge**: place |
| 10.0–12.4 s | bouche de métro, tiles as teeth | ordinary MCU of her saying the word, tiles as teeth (the same prop is set up) | equivalent setup information, different reveal |
| 12.4 s | match cut, tiles become the queue (obstacle) | plain cut to a paper-commuter queue at the stop; she waits | **diverge**: identity |
| 15.5–18.0 s | tiles become the stair onto the *impériale* | she steps on at the platform | **diverge**: route |
| 18.0–20.0 s | she rides on top, laughing | she rides inside, laughing | equivalent goal resolution |

The work is not interactive. Invitation, actions, resistance, memory and exit are N/A. TTL = 2 (default). No child inquiry is planned.

## 4 · Invariants

1. **Objective preserved.** Every shot after 2.0 s shows Z either moving toward V or V itself. Screen direction for "toward the tram" is always left → right.
2. **Anchor at every discontinuous cut.** These cuts are 8.0 s (jump) and 12.4 s (match). Z, or T in the mouth→queue case, survives within the §3.2 tolerances. The ledger proves it numerically.
3. **One vehicle.** V is a single cutout asset and is never redrawn. In L1 it is composited, in L2 it is native to the plate (the same source pixels), and in L3 it is composited.
4. **One prop, two reinterpretations.** T has 14 tiles from 10 s to the end. No tile is created or destroyed after 10.0 s: count them in the ledger.
5. **Each effect has a reversal and a consequence.** The jump brings her closer to V. The queue blocks her: she bounces, a setback. The stair gets her up: recovery.
6. **Clean continuity reference.** Cut B exists, is the same length, and shares frames 0–143.
7. **Material honesty.**
   - Everything on screen is FORAGED (LoC PD plates, the V cutout, real paper scans) or HANDMADE (the puppet pieces, tiles, the street plaques, captions).
   - There is no photograph of a real child and no frame or sound from Malle's film.
   - There are no filters faking a look. The grade is used only to unify the plates with each other and with the paper.
8. **Frame-by-frame animation.** The puppet pose changes on twos throughout the laugh, run and climb shots. It is not a held cel being panned.

Concurrency note (prompt §4):
- Gag slots are S1 to S8 below. A timing edit to S3/S4 may merge with a redraw of the mouth pieces only if the silhouette at frames 191/192 survives.
- The queue-as-obstacle gag and the continuity "she waits in the queue" are mutually exclusive setup states. They are forked as cut A and cut B, never merged.
- Every candidate records owner, base revision (`proposals/` r2 plus this plan), read and write sets, the test it targets, and its artifact.

## 5 · Hard proof: timed shot list (cut A, 20.0 s proof + 2.0 s tail = 22.0 s, 528 frames)

### Picture

The picture is 4:3, 720x540, centred in 960x540 with black pillars. The puppet animates on twos. Captions are in Instrument Serif (the kit font), cream (#efe4cc) at ~22 px, set low, appearing 6 frames after the action they voice.

| # | time (frames) | on screen | heard | material |
|---|---|---|---|---|
| S1 setup A | 0.00–2.00 (0–47) | **MS, L1 rue Royale.** The Madeleine columns are soft behind (P1, blur r≈10 px at 720 w). Z, seen from the waist up at frame left, faces right. A handmade paper métro sign has a GRÈVE strip pasted across it, top left. At 0.5 s, V (the tram) crosses the far plane L→R, and her head turns to track it (FK neck +12°). At 1.25 s her arm points (shoulder and elbow pins). Caption at 0.4: « Le métro ? En grève. » Caption at 1.3: « …le tram, alors ! » | Street ambience (foraged). Tram bell, offscreen right at 0.35 s, before V enters. Hooves. | P1 FORAGED (LoC 2001698526, PD). V FORAGED (cut from LoC P2). Z, sign and strip HANDMADE. |
| S2 chase | 2.00–6.00 (48–143) | **The same straightforward chase.** A MLS profile of Z, full figure, running L→R. Run cycle of 8 drawings on twos, 0.67 s per stride, with pinned thighs, shins, upper arms and forearms. The camera holds while she moves across. P1 drifts at 0.25x, and a foraged lamp-post or tree foreground plane at 1.4x. V is ahead at frame right and pulls away: its gap grows from 180 to 320 px. The bob bounces (secondary). | Footsteps on stone, synced to foot contacts. Tram bell receding. Ambience. | P1 and V FORAGED. Foreground plane FORAGED: a cutout from P1 or P4 trees. Z HANDMADE. |
| S3 test shot, laugh | 6.00–8.00 (144–191) | **CU, L1. Framing as the reference** (§7). She stops, out of breath, and *laughs*. The cues are all visible: eyes squeezed into crescents, lower lids pushed up, cheek pieces raised 6 px, brows up, head rocking ±4° on the neck pin and tipping back 3°, shoulders shaking 3 px on alternate twos. The mouth replacement cycle is 1-4-5-4-6-4… (closed, grin, open-gap, open-wide, gasp). A gust from 6.6 s drives 10 fringe strands and 4 slivers to the right across her right eye. 2 slivers detach and leave frame. **Hold:** at 7.67–8.00 s the head freezes at full laugh, mouth 5, hair at peak. | Ambience thins. Wind gust (foraged or kit). **Declared silence at 7.67–8.00 s, a hold.** No voice. | P1 FORAGED. Z HANDMADE. |
| S4 jump cut | **8.000 s (frame 192)** to 10.00 (192–239) | **JUMP CUT.** The same CU, pose and mouth phase; the hair spring state is carried over. The plate is now **L2 place de Clichy** (P2, blurred r≈10). The tram V sits ahead mid-frame in its native position. A handmade street plaque "PLACE DE CLICHY" pops in at top right at frame 196. The laugh resumes at 8.08. At 9.0 her eyes open and her gaze locks on the tram (eye replacement piece), with a tiny gulp (mouth 2). | Hard cut back into ambience, a busier square. The tram bell is now close, centre. A paper "snap" on the plaque. | P2 FORAGED (LoC 2002707975, PD). Plaque HANDMADE. |
| S5 bouche de métro (title gag) | 10.00–12.40 (240–297) | **Push-in from the S4 CU to ECU on her mouth, 10.0–10.5.** It is a multiplane push: the face plane scales 1→3.2 and the hair plane faster. The open mouth *becomes* the métro entrance: a paper tunnel of rings, with the Clichy plate as the faraway light. The teeth are cream letter tiles. The upper row is DOUK · IPU, with her gap between K and I. The lower row is DONKTAN. She says the word: the jaw opens and closes 4 frames per syllable, DOU·KI·PU·DONK·TAN, and each tile pops 6 px on its syllable. Caption « Doukipudonktan ! » at 10.6. On TAN (11.9) the jaw drops fully. The loose N tilts, then all 7 lower tiles drop out one per 3 frames under gravity (secondary dynamics: rotate, then settle). | One pitched paper-tile click per syllable. A low tunnel resonance. A clatter cascade on the fall. | Mouth, tunnel and tiles HANDMADE. P2 FORAGED, seen far inside. |
| S6 match cut → queue | **12.40 s (frame 297/298)** to 15.50 (298–371) | **MATCH CUT.** The 7 falling lower tiles, now upright, land in a row at the *same screen height and spacing* (±6 px). They are the queue at the tram stop, **L3 place du Châtelet** (P3, blurred). The plaque reads "PLACE DU CHÂTELET". Each tile has two small paper feet. Caption at 12.6: « faire la queue… » Z enters left at 13.0, running (run cycle), and hits the queue at 13.6, the contact frame. Her squash pose comes from a pose library piece. She bounces back 60 px with her hair flung forward (secondary). The tiles wobble and **tip in a domino cascade** to the right, 14.2–15.0, settling into a rising stair because each tile leans on the next. V waits at the stop, frame right. | **Impact** on the contact frame (a real paper-and-card clack plus a kit thud). A held beat of silence (0.25 s) after the bounce. Then domino ticks, 3 frames apart, rising in pitch. | P3 FORAGED (LoC 2001698539, PD). V FORAGED. Tiles and Z HANDMADE. |
| S7 recovery, the stair | 15.50–18.00 (372–431) | Z climbs the tile stair. There are 4 steps, each a pinned-leg climb pose, with the foot contact kept on the tile tops. This is the Reiniger contact plane, done as handmade inverse posing: the foot pin is locked and the hip is solved. The last tile is the step onto V's *impériale* (top deck). At 17.4 she sits down on the top deck. | Footsteps on card (higher, hollower). The tram bell rings twice: departure. Hooves start. | Same as above. |
| S8 resolution | 18.00–20.00 (432–479) | **CU on the top deck, framed as the reference.** The P3 plate slides right to left at 0.3x and V's rail plane at 1x, so the tram moves. A steady breeze blows her hair to frame right, with damped oscillation that settles (energy decays). She laughs (mouth cycle). The last lower tile, the N, flutters past (prop consequence). Caption at 18.4: « Zazie a pris le tram. » | Hooves and rumble, ambience, then a gentle breeze. | P3 FORAGED. Z HANDMADE. |
| tail | 20.00–22.00 (480–527) | Handmade cut-paper title card on a dark brown ground: « Zazie dans le métro ». The tiles spell it, with the N tile reused. Below it: « d'après Queneau — plaques : Library of Congress, Detroit Publishing Co. (domaine public) ». | Ambience fades. One final tile click. | HANDMADE. Credits text from the ledger. |

### Cut B (continuity control)

Cut B is the same 22 s.
- Frames 0–143 are identical to cut A.
- **S3** is identical.
- **S4b** (8.0 s): a continuity reverse angle on L1b, boulevard de la Madeleine (P4, `madeleine.jpg`, LoC 2001698544). Z enters the same screen side, and V is farther ahead.
- **S5b**: MCU, with her saying "Doukipudonktan" (same mouth cycle and teeth tiles, no push-in).
- **S6b** (12.4 s): a plain cut to L3. A queue of 7 handmade paper commuters stands at the stop, and Z joins the end.
- **S7b**: she steps aboard normally.
- **S8b**: CU inside the tram, laughing.
- The tail is the same.

### Negative control

`negctl.mp4` is 7.0–10.0 s of cut A rendered without Z (and without the plaque). It is the plate swap alone.

### Sound

Sound plan (prompt §7: test whether impact, pause and offscreen cue improve the timing):
- **Offscreen cue:** the tram bell at 0.35 s, off right, before V is seen.
- **Pause:** the declared silence at 7.67–8.00 before the jump cut, and 0.25 s after the queue impact.
- **Impacts:** the queue contact at 13.6, the domino ticks, the syllable clicks.
- **Sound-off pass:** the critic watches muted first, and the ledger records what was read.

## 6 · Element sources (FORAGED / HANDMADE)

### FORAGED

**Library of Congress Photochrom plates.** All are Detroit Publishing Co. and marked "No known restrictions". The forager re-verifies each on its loc.gov item page and records the rights statement text. The files already exist in `films/sources/zazie-dans-le-metro/r2/`:
- **P1** `loc_05184.jpg`, *The Madeleine, and rue Royale* (2001698526): L1.
- **P2** `loc_09974.jpg`, *Place Clichy* (2002707975): L2 and the source of V.
- **P3** `loc_05196.jpg`, *Place du Châtelet* (2001698539): L3.
- **P4** `madeleine.jpg`, *Boulevard de la Madeleine* (2001698544): L1b, control only.
- **Higher resolution:** fetch larger tile.loc.gov versions of P1–P3 if available (the r2 files are 1024 px). The CU shots crop deep, so a 2–3k source keeps the defocus clean rather than mushy.

**Vehicle V.**
- The default is the horse tram with *impériale* in P2, cut out by hand-seeded `cv2.grabCut` and refined by hand polygon. It is soft (≈150 px).
- The forager should also search LoC and Commons for a **sharper PD photograph of a Paris horse tram or omnibus with impériale**. Search terms: "omnibus Paris", "tramway Paris 1900", "impériale", Detroit Publishing, Commons Category:Horse-drawn omnibuses in Paris, PD-old.
- If one is found, V becomes that cutout everywhere *except* that L2 keeps P2's native tram. In that case the V asset must match its silhouette and colour (impériale, side livery) closely enough that a viewer accepts it as the same vehicle. Otherwise use the P2 tram everywhere.

**Real paper scans for the puppet's material.**
- Sources: Commons PD or CC0 scans of blank or coloured paper, kraft, card and tissue (e.g. blank endpapers of PD books, "paper texture" CC0). Also LoC blank versos.
- Each puppet piece is a cut shape whose fill is a crop of a real paper scan. The scan is dyed to the piece colour by multiply or levels. That is a real material in a chosen colour, recorded per piece in `rig.json`, and not procedural noise.

**Sound.** Wikimedia Commons audio (PD, CC0, CC BY, CC BY-SA only):
- a tram or hand bell;
- horse hooves on cobbles;
- a city street or square ambience (pre-1964 or field recordings);
- paper and card handling: flicks, clacks, a stack falling.

Moving Image Archive clips with source sound (pre-1964, PD status per the shared rules) for street murmur and traffic. Candidates, to be judged by listening: *Coney Island* crowd, the *Golden Gate City* old bus, 1930s–50s street shots. Nothing post-1964 unless it is a US-government work.

**Moving Image Archive footage.** Not used for picture by default: this is an animation. Optional *only* as a foreground plane silhouette, e.g. a passing pedestrian rotoscoped as a paper cutout. It is not needed.

### HANDMADE

- **Puppet Z:**
  - back-hair bob in 3 tones;
  - 10 fringe strands plus 4 slivers in 5 tones;
  - **ears**, left and right, with inner-ear shade;
  - face sheet, with chin-shadow and eye-socket tissue overlays;
  - tissue cheeks, separate so they can rise;
  - brows;
  - eye replacements: crescent-squeezed ×2, half, open-looking-right;
  - a folded nose tab;
  - **upper and lower lip pieces**;
  - a mouth replacement library of 6, with a gap-tooth upper set;
  - jaw;
  - neck;
  - orange collar in 2 tones, plus the fold;
  - brown jumper torso;
  - upper and lower arms, hands, thighs, shins and shoes for the body rig;
  - brass split pins at every joint.
- **Tile set T:** 14 letter tiles, real paper with the letters typeset in a bold serif, plus paper feet for the queue reading.
- **Signs:** the métro sign plus a GRÈVE strip; street plaques for Clichy and Châtelet; the title card.
- **Mouth tunnel:** paper rings plus a dark throat.
- **Control commuters:** 7 for cut B.
- **Captions.**

## 7 · AESTHETIC TARGET (from `assets/references/zazie1.webp`, 1000x750, studied and sampled with PIL)

**Medium.** A 35 mm Eastmancolor frame, 4:3, in live-action close-up with shallow depth of field. We reach it with **real cut paper in real colours, lit as one object on a tabletop**, in front of **real colour photochrom plates thrown out of focus**. We do not paint a fake film look.

**Framing and scale** (measured on the reference; the CU shots S3, S4 and S8 must match):
- The head spans x ≈ 25–75 % of picture width, i.e. head width ≈ 50 %.
- The crown is at ≈ 24 % height, the brows at ≈ 52 %, the mouth at ≈ 82 %, and the chin is at or below the bottom edge (≈ 97 %). The face is cut off at the chin and the collar barely shows.
- The face is centred slightly right of centre.
- The fringe sweeps from upper left to right, and strands cross the right eye (frame right).
- Hair flies beyond the head silhouette at top right.

**Tonal range.**
- Picture luma (RGB mean) percentiles: p5 = 21, p50 = 90, p95 = 148, max ≈ 200.
- It is a **low-key, soft, compressed print**. There are no paper whites. The brightest areas, the teeth and the pale pillars, are about 150–200.
- Mean saturation (HSV S) ≈ 92/255.
- Kf-2 overshot: its p50 was 106 and p95 203, its background #e4d09f was yellow, its skin #eabd9f too pale and its hair #864726 too orange. **This build must come down to the reference.**

**Palette** (sampled averages):

| region | colours |
|---|---|
| hair | crown #684d3c, dark fringe #412312, side shadow #2c1504, lit strands #765b48 (warm brown-auburn, *not* orange) |
| skin | cheek #b47059, forehead #b6785e, neck shadow #a5664b (rosy terracotta, warm and fairly dark) |
| lips | #b76756 |
| teeth | ivory in shadow #a2755c, top highlight ≈ #d8c6a8 |
| mouth interior | #220d04 |
| background | pale pillars #8a8574, dark pillar gaps #272119, sky/top #787064, olive at left #46452b, lower #665e52 (grey-olive, desaturated) |
| collar | saturated orange, the only strong chroma, kept small at the bottom edge |

**Light.** Soft overcast daylight from upper left, so the face is a little brighter on frame left. There are gentle shadows under the fringe and at the jaw. The paper pieces get small real drop shadows (offset ≈ 3–5 px down and right, blur 4 px, 35 % opacity) because they are layered card. Shadows are cast *on* the face by the fringe, which is a separate plane.

**Texture.** Fine film grain plus soft defocus behind. In our build that comes from the paper fibre of the real scans and the photochrom halftone/lithographic grain inside the blurred plates. Kit grain stays at its default. **No added film-grain or colour filters.**

**Plates.** Photochroms are yellow-sepia and bright, so to unify them with the reference:
- blur r ≈ 10–14 px at 720 px picture width (the columns stay recognisable as pale verticals);
- grade toward neutral grey-olive: lower the gamma, desaturate about 30 %, and pull blue up slightly;
- target the plate region p50 ≈ 85–100.

This is a unifying grade on real material. It is allowed and recorded.

**Typography.** The reference has none. The film's own type is:
- captions in Instrument Serif, cream #efe4cc on a faint dark band, small and low;
- tiles in a bold serif on cream paper (#e6d6b8), letters in dark red-brown (#7a2a1c);
- plaques in a dark bluish enamel colour, muted (#2f3f55), with cream letters.

**Rhythm.**
- The puppet animates on twos.
- Laugh shakes on a 4-frame alternation.
- The cuts are hard. There is a 1/3 s hold before the jump cut.
- The chase is brisk at 0.67 s per stride.
- Shots are 2–4 s. The film is short and does not linger.

**Side-by-side tests.** The editor produces `compare-ref.jpg`, which places the reference (scaled to 720x540) beside film frames 7.6 s, 8.1 s and 19.0 s, with the metrics printed underneath. See acceptance conditions A7 and A8.

## 8 · Animation technique SCIONs chosen (prompts read in full)

### #2 Lotte Reiniger: Articulated Shadow Theater, applied in colour

**Why.** The spine is an articulated cut-paper puppet with pinned joints, joint-angle limits, replacement profiles (mouths and eyes), contact planes and exposure sheets. Its bar transfers directly:
- limbs never detach;
- the point of support stays stable on contact;
- relationships read with **all colour removed**. We run a greyscale, silhouette-read test of S2, S6 and S7.

**Applied:**
- **S1:** neck and arm FK point.
- **S2:** run cycle with joint limits (knee 0–110°, elbow 0–130°).
- **S3/S4:** head rock on the neck pin, plus mouth and eye replacement by exposure sheet.
- **S6:** squash pose from the pose library.
- **S7:** climb with the foot pinned to the tile-top contact plane.
- **S8:** laugh again.

The exposure sheet (frame → pose and replacement IDs) is the canonical state.

### #41 Secondary Dynamics: Inertia and Restraint Swarm

**Why.** The test shot lives or dies on the hair blowing. Its bar is the invariant we need: momentum begins *after* primary motion, and all energy decays when the sources stop, with no purposeless wiggle.

**Applied:**
- Each of the 10 fringe strands and 4 slivers is a damped angular spring (paper inertia prior: stiff, light), pinned at the crown and driven by the head rotation and a wind-force curve. The wind curve has gust events at 6.6 s, 18.0 s and the S2 run.
- It is integrated at 24 Hz with semi-implicit Euler, and **the state is carried across the 8.0 s jump cut**.
- The collar fold also gets a spring, as do the falling tiles in S5 (rotation plus settle) and the S6 bounce-back hair fling.
- Unit tests:
  - the strand-angle lag behind head motion is 2–3 frames;
  - energy is below 10 % within 1 s of the gust ending;
  - strands do not penetrate the face plane in important frames. The fringe is drawn in front by design, so "penetration" means strand roots leaving the crown.

### #43 Collage Graph Rewriting: Identity Change Swarm

**Why.** The proof demands one prop reinterpreted twice, plus a match cut that turns a queue into an obstacle. Its typed entity graph with replace/merge/split rules, visual anchors and scene-event contracts is exactly the `TileRewrite` operation. Its bar is: every rewrite meets its preconditions, identity is retained, and the viewer follows.

**Applied:**
- `gag-route.json` holds the entity graph. Its nodes are T1..T14, V, Z and L1..L3, and it holds the rewrite rules:
  - teeth → queue (cause: the jaw drop on TAN; anchor: the row baseline y);
  - queue → obstacle (cause: Z's collision);
  - queue → steps (cause: the domino cascade).
- Each rewrite is asserted in the render script.
- The same graph types V's identity across L1, L2 and L3.

**Subsidiary methods, not separate SCIONs:**
- #44 multiplane parallax: plate 0.25x, puppet 1x, slivers and foreground 1.4x, plus the S5 push-in.
- #29 GrabCut: V and foreground cutouts.
- #38 pose selection: mouth and pose libraries.

## 9 · Swarm units (4 units; the montage editor/assembler and the independent reviewer are run separately by the workflow)

All units read this plan, the prompt, BRIEF-2, and SCION prompts #2, #41 and #43 in full. Each finishes within about 45 minutes. Base revision: this plan. Do not touch other films or kit.py.

### U1 · gag-layout (gag writer + layout unit, merged because the word→action table and the route plot share the timing)

- **Owner of:** the word-to-gag table, the route graph (entrances, exits, obstacles, match anchors per shot), eye trace, the exposure sheet (frame-exact timings for S1–S8 and cut B), the cut fixtures, and the TileRewrite entity graph.
- **Output:** `films/swarm/zazie-dans-le-metro/gag-route.json`, with these keys:
  - `word_to_gag`;
  - `route` (nodes and edges per location);
  - `shots` (A and B, frame ranges, screen positions of Z, V and T in 720x540 picture coords, eye-trace targets);
  - `exposure_sheet` (frame → body pose id, mouth id, eye id, gust value);
  - `cuts` (frame, type, anchor tolerances);
  - `entity_graph`;
  - `timecoded_gag_cues`.
- **Also:** `layout-boards.jpg`, rough position boards of one frame per shot drawn on the blurred plates. Media go in `films/sources/zazie-dans-le-metro/layout/`.
- **Acceptance:** the JSON validates against the §3.2 preconditions. The A and B shots share frames 0–143. The tile row y at frame 297 equals the queue y at frame 298.

### U2 · forager (plates, vehicle, provenance)

- **Owner of:**
  - re-verifying P1–P4 licences on loc.gov;
  - fetching higher-res tiles (≤ 30 MB total);
  - searching for a sharper PD tram/omnibus with impériale;
  - cutting out V (GrabCut plus hand polygon, alpha-feathered edge) and one foreground tree or lamp-post plane from P1/P4;
  - making the graded, defocused plate set at the §7 targets (r ≈ 12 px, grey-olive);
  - measuring plate luma.
- **Output:** `films/swarm/zazie-dans-le-metro/evidence-ledger.json`, a list of `{id, title, author, license, license_url, source_url, file_url, local_path, sha256, size, used_as, rights_text_quoted, checked_on}`. It also holds a `credits_draft` array in the `films/credits/<slug>.json` schema and a `rejected` list, which includes the r2 child photographs, marked "excluded: real child, user rule".
- **Media:** `films/sources/zazie-dans-le-metro/forage/`, containing:
  - `P1_blur.png`, `P2_blur.png`, `P3_blur.png`, `P4_blur.png` at 720x540 plus 20 % overscan for drift;
  - the sharp crops;
  - `V_tram.png` (RGBA);
  - `fg_plane.png`;
  - `plates-sheet.jpg`.
- **Acceptance:** every item is PD, CC0, CC BY or CC BY-SA with quoted rights text. V's alpha edge has no halo above 2 px. Plate p50 is in 85–100.

### U3 · puppet (cutter + hinge engineer + gesture animator + secondary dynamics)

- **Owner of:**
  - foraging 3–6 real paper scans (Commons PD/CC0, ≤ 15 MB, and record them in its own ledger section, `puppet-paper` in `rig.json`);
  - building every HANDMADE piece in §6 as an RGBA sprite, with a real-paper fill, a scissor-cut edge from the geometry and a drop shadow;
  - the FK rig (pins, angle limits);
  - the mouth and eye replacement libraries;
  - the run cycle (8 drawings), squash, climb (4) and sit poses;
  - the spring hair solver with unit tests;
  - the tile set T.
- **Hair:** must use ≥ 5 tones from §7. **Ears, lips, cheek lift and crow's-foot creases** are mandatory, so that it does not read as clip-art.
- **Output:**
  - `films/swarm/zazie-dans-le-metro/rig.json` (pieces, pivots, limits, z-order, paper source per piece, palette, spring params, test results);
  - `films/swarm/zazie-dans-le-metro/test-shot.mp4`, the S3 → S4 laugh and jump cut, 6.0–10.0 s, rendered with kit `Film` on U2's plates (or r2 plates blurred locally if U2 is not done) with the sound declared silent;
  - `puppet-sheet.jpg`, all pieces plus the 6 mouths plus the run cycle;
  - `silhouette-read.jpg`, S2/S6/S7 poses in greyscale.
- **Media:** `films/sources/zazie-dans-le-metro/puppet/` (sprites and a `puppet.py` module the editor imports, which is a rig and sprite loader, not a film).
- **Acceptance:**
  - the test shot reads as laughing with the sound off, as judged by U3's own frame sheet and marked perceptual, pending the reviewer;
  - the strand lag is 2–3 frames and energy decays below 10 % in 1 s (measured);
  - across frame 191 → 192 the root centroid Δ ≤ 8 px (measured);
  - the head-width/picture-width ratio at frame 190 is 0.45–0.55.

### U4 · sound (impacts and holds)

- **Owner of:** foraging and licence-checking the bell, hooves, street ambience and paper-clack recordings (Commons; archive clip audio decoded with ffmpeg; ≤ 25 MB), trimming them, and building the cue sheet against U1's frame cues (taking §5 timings if U1 is not done yet).
- **Holds:** the declared silences at 7.67–8.00 s and 13.6–13.85 s.
- **Synthesis:** syllable clicks, thud and domino ticks with kit `Mix` where no real recording fits, marked as synthesized.
- **Output:** `films/swarm/zazie-dans-le-metro/sound-cues.json`, a list of `{t, frame, cue, file|synth, gain, pan, purpose: impact|hold|offscreen|bed, licence entry}` for cut A and cut B. Ledger entries for the recordings are in the same file.
- **Media:** `films/sources/zazie-dans-le-metro/sound/`: trimmed 44.1 kHz wavs plus `soundbed-preview.wav` (22 s, cut A).
- **Acceptance:** every cue lands within 1 frame of its picture event. Silence is in the hold windows (RMS < −50 dBFS). Every recording carries a licence entry.

### The editor (run by the workflow) then

- writes `films/zazie-dans-le-metro.py` (kit `Film`, importing `puppet/puppet.py`, reading `gag-route.json` and `sound-cues.json`);
- renders cut A `assets/films/zazie-dans-le-metro.mp4`, cut B `zazie-dans-le-metro-control.mp4` and `negctl.mp4`;
- writes the frame ledger `films/swarm/zazie-dans-le-metro/frame-ledger.json` (per frame: plate_id, Z root transform, mouth/eye id, strand energy, tile readings and count);
- writes `compare-ref.jpg`, `films/credits/zazie-dans-le-metro.json` (from U2/U3/U4) and `films/notes/zazie-dans-le-metro.txt`.

## 10 · Acceptance bar (falsifiable; for a fresh critic watching the render and reading the ledgers)

- **A1, goal legible sound-off.** A muted viewer of cut A can say, by 4.0 s, "she wants to catch the tram (the métro is on strike)". The GRÈVE sign, her point at V and V on screen all appear within 0–2.0 s. *Fails* if the goal needs the end caption to be understood.
- **A2, the same straightforward chase, plus the control.** Cut B exists at the same duration. Frames 0–143 of A and B have a mean abs diff < 1.0 (measured). In S2, Z runs L→R with V ahead, and the gap to V grows.
- **A3, jump cut for impossible distance.**
  - At frame 191 → 192 the ledger's `plate_id` changes P1 → P2 while the Z root centroid Δ ≤ 8 px, scale Δ ≤ 3 %, the mouth id follows the exposure sheet and the strand state is continuous (measured).
  - A viewer reports "same girl, different place, closer to the tram".
  - In `negctl.mp4` the same swap without Z reads as a plain location change.
- **A4, the laugh reads with sound off (the test shot).**
  - Over 6.0–8.0 s, ≥ 4 distinct mouth replacements appear, eyes are crescents, the cheek pieces rise ≥ 5 px, and the head rocks.
  - A muted viewer says "laughing" without prompting (perceptual).
  - The hair strands lag the head by 2–3 frames and their energy decays below 10 % within 1 s of the gust ending (measured from the ledger).
  - The pose changes at least every 2 frames: frame-by-frame animation, not a held sprite.
- **A5, match cut: queue into obstacle, with consequence.**
  - At 12.4 s (frames 297/298) the lower tile row's baseline y and spacing match the queue row within ±6 px (measured).
  - Z collides with the queue at 13.6 s, with a visible bounce and an impact sound within 1 frame.
  - The collision causes the domino stair that she then climbs. A gag with no downstream event fails.
- **A6, one prop reinterpreted twice; three locations.**
  - The same 14 tiles (count constant from 10.0 s; same glyphs) read as teeth (10–12.4 s), then as the queue/obstacle (12.4–15.5 s), then as stairs (15.5–18 s).
  - Three distinct plates, L1, L2 and L3, are on screen, with the plaques naming L2 and L3.
  - She ends on V's top deck by 18 s.
- **A7, aesthetic framing side by side.** In `compare-ref.jpg`, the reference sits beside film frames at 7.6 s, 8.1 s and 19.0 s:
  - head width / picture width is 0.45–0.55;
  - the crown is at 18–30 % of height and the mouth at 75–88 %;
  - fringe strands cross the right eye, frame right;
  - the plate behind is visibly defocused but its pale verticals are recognisable.

  A critic comparing them judges the CU "as close as the reference" (perceptual plus measured).
- **A8, aesthetic palette and tone side by side.** On the same compare sheet, over the 720x540 picture region of the CU frames:
  - luma p50 is 75–105 and p95 ≤ 175, with < 0.5 % of pixels above 235;
  - mean hair colour is within ΔE76 ≤ 18 of #5a3e2e, and mean skin within ΔE76 ≤ 18 of #b47059;
  - the plate region's HSV-S mean ≤ 110;
  - the hair shows ≥ 5 distinct tones, and ears and lips are visible.

  A critic judges the warm Eastmancolor print feel as reached with real paper and real plates, not filters (perceptual). Kf-2 fails this test (bg #e4d09f, p95 203), and the build must beat it.

**Provenance gate (checked alongside):**
- every foraged item is in `films/credits/zazie-dans-le-metro.json` as PD, CC0, CC BY or CC BY-SA, with quoted rights;
- no photograph of a real child, and no Malle or Queneau-edition material;
- all puppet pieces are handmade from foraged real paper scans;
- the film is ≤ 6 MB.

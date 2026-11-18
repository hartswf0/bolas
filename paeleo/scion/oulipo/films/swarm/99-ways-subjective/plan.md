# 99 Ways to Tell a Story · Subjective: director's plan (rebuilt from scratch)

Direction: **2 · PAPER HANDS** (`proposals/kf-2.png`), chosen by the operator. Test shot: **E4**, where the wrist turns, the watch comes into view and the answer balloon "Quarter past one!" arrives from offscreen.

Story: we use the household anecdote from the chosen direction (milk, stairs, the time, the refrigerator, forgetting), **not** the station seed in section 10. The proof asks for "a six-panel household anecdote". The direction already tells that story, and it is the anecdote Madden's Template and Subjective pages retell. The station seed's roles map onto it as a structural rhyme: the bell becomes the offscreen question, the envelope becomes the MILK note, the brass key left on the bench becomes the milk left on the shelf, and the service door that stays closed becomes the visitor who is never seen. The objective baseline page is built in this work from the same event ledger (see "Paired page"). It does not reuse 99-ways-template, which is a different (station-office) story and belongs to another work.

---

## 1 · Creative thesis, and what would make it bland

**Thesis.** You are inside a pair of paper hands on a lamp-lit page. Everything you know is what those hands touch, where the eye turns, and what a voice from beyond the panel border says. The six beats are the same as in the objective version. Only access to them changes. The page is a lightbox and the hands are scissor-cut puppets on brass pins, so restricted sight becomes physical. The voice's balloon is a card pushed in on a rod from behind the opaque gutter board. The time exists only once the eye drops and a wrist turns.

**Bland would be:**
- a POV that is just tighter crops of a normal scene (arbitrary crops, section 8);
- hands that read as mittens or gloves at phone size;
- balloons that simply fade in;
- a watch or clock that is merely cut in, with no turn causing it;
- paper texture as a filter laid over vector shapes;
- a camera that slides panel to panel while nothing inside the panels is animated;
- any glimpse of the protagonist's face, or of the other person (a disembodied reverse shot).

## 2 · Defining beat and comparison baseline

**Defining beat: E4, film 0:27.0–0:39.0 (core 0:29.0–0:36.5), page panel P4.**
- At the start of P4 the eye still looks down the stair. Panel P3's question balloon is still held in the gutter above it.
- The head turns down and left: the panorama strip carrying the stair and banister is pulled up and right through the panel window.
- The left forearm rises from below the panel's bottom edge, where it was outside the field of view, with its shirt cuff buttoned.
- The right hand's pinch pulls the cuff back.
- The wrist turns through three replacement drawings: strap edge-on, ¾, then the dial face. The translucent dial inlay lights up, with hands at **1:15**.
- Only then does the own-voice balloon **"Quarter past one!"** arrive. It enters from beyond the panel's bottom edge, the speaker's own mouth, and its tail runs off the bottom of the frame.

What the viewer should be able to point to:
1. No time-piece exists anywhere in P1–P3 or in the first frames of P4.
2. The head turn (the stair sliding away) and the wrist turn are what bring the watch in.
3. The dial reads 1:15 and the answer matches it.
4. The questioner is never seen. Their balloon's tail leaves the panel.

**Comparison baselines.**
- (a) Madden's *Subjective* page (`assets/references/madden2.webp`): close first-person framing, hands from below, watch panel "It's 1:15.", hand on the refrigerator handle "Thanks!", "What the hell was I looking for, anyway?!".
- (b) Our own **objective baseline page** built from the same ledger (wide shots that show the protagonist's whole figure and the housemate in the living room).
- (c) The chosen keyframe `kf-2.png` is the look to meet or beat.

## 3 · Lineage Genome (compact) and Olog

**Genome.**
- Source medium: a one-page comic of 8 panels, pen and brush, B/W (Madden 2005, after Queneau's *Exercices de style*, 1947).
- Target medium: a 6-panel backlit cut-paper page (print PNG), plus a ~70 s film that performs its reading.
- Preserved relation: one event sequence with its participants, causality and endpoint, seen through one participant's eye pose.
- Changes:
  - optics: a pen-line camera becomes a lightbox. Silhouette means occlusion, and near-lamp pieces cast a penumbra;
  - formalism: drawn panels become articulated puppets on pinned joints, with replacement profiles and an exposure sheet;
  - concept: restricted information becomes physical restriction. The gutter board is literally opaque, and voices arrive from behind it;
  - sound: Madden's page is silent. The film adds diegetic foraged sound and a muffled offscreen voice placed toward the speaker.

**Epoch weights.**

| Epoch | Weight | Reason |
|---|---|---|
| Comics exercises in style: Queneau 1947 → Oubapo → Madden 2005 | 90 | The source of the constraint |
| Silhouette animation: Reiniger 1919–1930s | 70 | The medium of the target |
| First-person cinema experiments, e.g. *Lady in the Lake* (1947) | 35 | Uncertain as a causal influence on Madden; recorded as uncertain |
| Shadow theatre / lightbox and overhead-projector performance | 30 | |
| Digital compositing, the occlusion DAG (Porter–Duff 1984) | 30 | The method, not the look |

**Olog (types).**
- ◻ **Event** `{id E1..E6, order, participants {P = protagonist, H = housemate}, objects, causal links, outcome}`. Frozen in `continuity/event-ledger.json`.
- ◻ **EyePose** `{panel, t, position (room, height), yaw, pitch, fov (≈70° h)}`, one or more per panel. P4 has a keyed pose curve (pre-turn → post-turn).
- ◻ **Object** `{id, room, position, occluders}`: typewriter, coffee cup, MILK note, pencil, stair, banister, watch (on the left wrist, under the cuff), refrigerator, shelves, milk bottle. H counts as an object for visibility purposes.
- ◻ **Observation** `{event_id, channel ∈ {sight, sound, own-speech, other-speech balloon, inference}, evidence (piece IDs / balloon ID / sound-cue ID), access_condition}`.
- **[observe]**: (Event, EyePose(t), Objects) → set of Observations. An object is drawable at t ⇔ it lies in the FOV cone of EyePose(t) ∧ it is not occluded (holdout by the cuff, the gutter board or another piece). Speech from an undrawable speaker ⇒ a balloon whose tail exits the panel edge facing the speaker's bearing, and a sound cue panned to that bearing.

**Preconditions of [observe] (typed).**
1. `event_id ∈ ledger` (frozen).
2. `EyePose(t)` is defined for every film frame and for every page panel.
3. Every drawn piece carries `object_id` and `visible_reason ∈ {in_fov, reflection(supported geometry)}`. There are no reflections in this work.
4. Every balloon carries `speaker`. If `speaker ∉ visible(t)`, the tail must cross the panel border.
5. Own-speech balloons have their tail toward the bottom-centre edge, which is the mouth below the eye.

**Observable consequences.**
- In every frame and panel before the E4 turn starts, watch-dial pixel area = 0. After the turn it is > 0 (a structural visibility assertion).
- H is never drawn in the subjective page or film.
- Both "What time is it?" and "Thanks!" have tails that leave their panel on the edge facing H's bearing. In P3 that is the upper left (living room off the stair foot). In P5 it is the left (the living room is behind-left of the refrigerator).
- The answer "Quarter past one!" agrees with the dial.
- P6 ends with the milk bottle on the shelf and the hand open, not touching it. The endpoint matches the baseline.

**Counterexample (the central operation fails).** Any of these breaks [observe]:
- a panel that cuts to the protagonist's face saying "Quarter past one!" (a disembodied reverse shot, which fails strict mode);
- the watch drawn on the left wrist in P1 while the cuff is buttoned over it (visible while occluded);
- a wall clock that appears in P4 with no change in EyePose;
- the housemate's silhouette drawn at the foot of the stair in P3 while the eye is pitched down at the treads (outside the FOV).

**Replay and alternate views.**
- *Equivalent* across the objective and subjective versions: event IDs E1–E6, their order, who speaks which line, the time 1:15, and the endpoint (milk stays on the shelf, the hand is empty, the MILK note stays upstairs on the desk board).
- *Diverge*:
  - the objective version shows who H is and where H sits (an armchair in the living room, with a newspaper), and the protagonist's whole body;
  - only the objective version shows that the MILK note is left behind on the desk while the protagonist stands at the refrigerator;
  - the subjective version alone gives the felt order of access: the voice before the speaker (never), and the time only after the turn.
- Witness swap (section 8 inquiry, recorded but not built): through H's eyes, the typewriter, the note, the watch and the shelves all become inaccessible. The protagonist is known only through sound and their voice.

Interactive work: not applicable. This is a page and a linear film. TTL = 2 (default).

## 4 · Invariants

- **I1 Canon.** Participants P and H, causality and outcome are fixed by `event-ledger.json`. Any change means a new ledger revision and invalidates the dependent panels.
- **I2 Access.** Every visible piece is accessible from that panel's EyePose. Outside-view events (H speaking) come only by balloon and sound. There are no reflections.
- **I3 No disembodied reverse.** P is seen only as hands, forearms and cuffs entering from the lower frame edges, at the angles an eye above them allows.
- **I4 Turn-gated object.** The watch dial is absent until the E4 head turn and wrist turn. This is asserted per frame.
- **I5 Puppet integrity** (Reiniger and IK invariants below). Pins hold, joint limits hold, and contacts hold during contact intervals.
- **I6 Page = film.** The film's panel art is the page art. Each panel's settled frame in the film is the page panel.
- **Concurrency.** Hands, sets and speech are built independently against the frozen ledger and visibility map. A change of EyePose re-triggers that panel's visibility check. All pieces have immutable IDs (`hand.R.palm.v3`, `set.P3.banister`, …) recorded in each unit's ledger with owner, base revision, read and write sets, and tests.

## 5 · Technique SCIONs (read in full in `../../../swarms.json`)

| id | title | why |
|---|---|---|
| **2** | Lotte Reiniger: Articulated Shadow Theater | The medium itself: backlit silhouettes, pinned joints, joint-angle limits, foreground and midground shadows, **replacement profiles** (the wrist turn and the refrigerator door), contact planes, exposure sheets. "Never rescue weak action with internal textures." |
| **33** | Inverse Kinematics: Contact and Reach | The subjective view is made of hands reaching things. Fingertips on keys, pencil on paper, palm on the banister, pinch on the cuff, grip on the door handle, and the *deliberate non-contact* in P6. World objects respond after contact. FK chains (forearm → palm → finger segments) are posed by two-bone IK with pole hints. |
| **45** | Occlusion Compositing: Who Is In Front? | The source anchor of the work ("derive the picture from who can see what"). The occlusion DAG decides what the eye can see: the gutter board in front of the balloon rods, the cuff as holdout over the watch, the hand in front of the shelves and behind the door edge, contact shadows and penumbra on the screen. |

**Applying them shot by shot.**
- **P1 typing.**
  - #2: two articulated hands, each with forearm, cuff, palm, 4 fingers × 2 segments and a 3-piece thumb.
  - #33: fingertip IK targets on punched keys. A key dips 4 px only after its fingertip arrives. The exposure sheet keys strikes on ones.
  - #45: hands sit nearer the lamp (soft penumbra); the typewriter sits against the screen (sharp).
- **P2 note.**
  - #33: pencil-tip IK target that follows the stroke path of the hand-lettered word MILK. The letters appear stroke by stroke, straight ahead, frame by frame.
  - #2: a pencil-grip replacement palm.
- **P3 stair.**
  - #33: palm-to-banister contact slides along the rail. The stair treads step up on a footfall cadence, with a 2-frame settle on each tread.
  - #45: the question balloon's rod enters from behind the gutter board, which occludes the rod.
  - #41-style damped spring on the card (secondary motion only, not a chosen SCION).
- **P4 (defining).**
  - #45: the panorama strip is pulled through the window (the head turn).
  - #2: the left forearm rises; joint limits are respected.
  - #33: the right-hand pinch holds the cuff edge while the cuff slides back. The cuff is the holdout, so its slide reveals the strap.
  - #2 replacement profiles: wrist edge-on → ¾ → face, swapped on the wrist pin with no scale pop. The dial inlay (translucent tracing paper) lights up.
  - Then the own-voice balloon arrives from below the bottom edge.
- **P5 refrigerator.**
  - #33: hand grip on the handle, then a pull. The door responds after contact, as a replacement-profile swing (#2) in 4 drawings.
  - The interior brightens (a brighter backlight patch, which is how a lightbox would show it).
  - The "Thanks!" rod enters from the left gutter (#45).
- **P6 shelves.**
  - #33: a reach that stops short. The fingertip-to-bottle distance stays ≥ 25 px at all times (a deliberate miss), with fingers flexing and opening twice.
  - Own balloon. The final hold.

**Numeric invariants** (measured by the units on their own renders; the decisive judgement stays perceptual):
- #2: child pivot to parent pin residual ≤ 1 px in every frame. Joint angles stay inside the declared limits.
- #33: fingertip-to-target residual ≤ 2 px for the whole of every declared contact interval. The world object responds 1–3 frames after contact, never before.
- #45: the layer order matches the DAG in every frame, alpha ∈ [0,1], there are no pops at crossings, and watch-dial area = 0 before the E4 turn start frame.

**Perceptual achievements** (judged by viewing):
- #2: with colour removed, thumbs and fingers stay distinct in grasp poses, and the action reads.
- #33: the hands visibly choose and reach their targets, and the P6 hand visibly fails to take the bottle.
- #45: the voice is felt to come from beyond the page, and every piece sits on one stage.

## 6 · Hard proof: page layout, frozen events, timed film

### Page (`assets/pages/99-ways-subjective.png`, 3200 × 1800 px, 16:9, reading order Z: P1 → P2 → P3 / P4 → P5 → P6)

Page coordinate frame (px). The outer margin is 70 and the gutters 35, in opaque dark board.

| Panel | Box (x0,y0,x1,y1) | Event | EyePose | On the panel (all HANDMADE cut paper on lightbox unless stated) | Lettering |
|---|---|---|---|---|---|
| P1 | 70,70,1090,875 | **E1** errand set | seated, pitch −40°, yaw 0 | the typewriter silhouette with punched round keys and a paper sheet in the platen; **both hands typing** with buttoned cuffs (watch hidden under the left cuff); a black coffee cup on its saucer at right, with no milk (a dark full cup) | caption box (tracing paper, upper left): "This coffee needs milk." |
| P2 | 1125,70,2115,875 | **E2** errand written | seated, pitch −10°, yaw +20° (to the board above the desk) | the cork/board edge; a pinned slip of tracing paper; the right hand with pencil-grip palm writing **MILK** (hand-lettered, ink appears stroke by stroke); the left hand rests at the lower-left edge, cuffed | the word MILK on the slip (part of the art) |
| P3 | 2150,70,3130,875 | **E3** unseen interruption | standing on the stair, pitch −45°, yaw 0 | stair treads and the banister rail descending to the lower right; the right hand sliding on the rail; the foot of the stair opening at the lower left (dark doorway to the living room) | **other-speech balloon** "What time is it?" (vellum card on a black rod that enters from behind the top gutter; tail exits the panel's upper-left corner toward the living room) |
| P4 | 70,910,1600,1730 | **E4** turn → watch → answer (DEFINING) | foot of the stair; pitch −45° → −70°, yaw 0 → −25° | final drawing: the stair strip has gone except the banister post at the far right edge; the left forearm diagonally from the lower left, cuff pushed back by the right hand's pinch; the **wristwatch dial face-up at 1:15** (translucent inlay, black hands) | **own balloon** "Quarter past one!" (tail exits the bottom edge, centre-left) |
| P5 | 1635,910,2360,1730 | **E5** thanks / reach | kitchen, facing the refrigerator, pitch −15° | the refrigerator door swung open (4th profile), its handle in the right hand's grip, the interior glowing brighter | **other-speech balloon** "Thanks!" (rod from behind the left gutter; tail exits the left edge, behind-left = living room) |
| P6 | 2395,910,3130,1730 | **E6** failed outcome | at the open refrigerator, pitch −5° | three shelves with jars and packets, and the **milk bottle on the middle shelf, plainly visible**; the right hand open, hanging in front of it, not touching | **own balloon** "What was I after, anyway?!" (tail exits the bottom edge) |

**Route.** There is one reading route: P1 → P2 → P3 → P4 → P5 → P6, the Z order. The film performs it. Route annotations go in `routes.json`, which gives the camera path, the dwell per panel, and each balloon's entry path and tail exit edge.

**Paired page (objective baseline, `assets/pages/99-ways-subjective-baseline.png`, 3200 × 1800, same lightbox and the same cut-paper world, wide shots).**
- P1: the protagonist's full figure at the typewriter.
- P2: pinning the note.
- P3: on the stair; H in an armchair in the living room asking.
- P4: the protagonist checks the watch.
- P5: at the refrigerator; H's "Thanks!" from the armchair, behind.
- P6: in front of the open refrigerator, empty-handed. The MILK note is still on the desk board upstairs, seen in a cut-away corner.

It has the same event IDs and the same endpoint.

### Frozen event sheet (owned by the continuity unit; the ledger is frozen before any art is accepted)

- **E1** P is typing. The errand is formed: get milk for the black coffee.
- **E2** P writes the MILK note and pins it to the board, then leaves it there.
- **E3** P goes downstairs. H, unseen in the living room, asks "What time is it?".
- **E4** P looks down and turns the wrist to the watch (1:15) and answers "Quarter past one!".
- **E5** H says "Thanks!". P opens the refrigerator.
- **E6** P faces the shelves with the milk in plain view, does not take it, and says "What was I after, anyway?!". The milk stays on the shelf.

### Film (`assets/films/99-ways-subjective.mp4`, 1280×720, 24 fps, ~70 s, ≤ 6 MB)

The camera is a crop of the page-resolution canvas at time t. Moves between panels are 0.8 s, eased, travelling across the gutter board. Only the active panel animates. Panels already read hold their final drawing. Panels not yet read sit in their opening drawing, with no balloons. The lamp is never "off", because the page is a lightbox throughout.

| Time | Shot | On screen | Heard (FORAGED unless stated) |
|---|---|---|---|
| 0:00–0:03 | whole page | all six panels in their opening drawings, balloons absent; a faint lamp warm-up (the backlight rises 85% → 100% over 1 s) | the lamp switch click and the room tone (foraged) |
| 0:03–0:11 | P1 | push in; both hands type on ones, the keys dip after contact, the carriage advances; the caption card slides in at 0:05 | typewriter keys and carriage (foraged recording) |
| 0:11–0:18 | P2 | the right hand writes MILK stroke by stroke (≈2.5 s), presses the pin, withdraws | pencil on paper; one typewriter return before it |
| 0:18–0:27 | P3 | treads step up on a footfall cadence, the palm slides along the rail; at **0:22.5** the rod pushes the card "What time is it?" in from behind the top gutter (damped spring), and the steps stop | footsteps on a wooden stair; at 0:22.3 a muffled voice (foraged speech, low-passed and unintelligible, panned −0.7 left) |
| **0:27–0:39** | **P4 (defining)** | 0:27–0:29 hold on the stair (P3's balloon is still visible at the frame's top edge); **0:29–0:32 head turn**: the strip pulls up-right at constant velocity with a 2-frame ease, and the stair leaves; 0:30.5–0:33 the left forearm rises from the bottom edge, cuffed; 0:32.5–0:34 the right pinch pulls the cuff back; **0:34–0:35.5 the wrist turns** (edge → ¾ → face, 6 frames per drawing) and the dial lights; **0:36.5 "Quarter past one!"** arrives from below the bottom edge; hold to 0:39 | the steps stop; a sleeve rustle; the watch tick fades in **only once the dial is visible**; silence under the answer |
| 0:39–0:47 | P5 | the hand reaches, grips the handle (contact) and pulls; the door swings through 4 profiles; the interior brightens; **0:42.5 "Thanks!"** pushed in from the left gutter | the refrigerator door unseals; the muffled voice again, panned left; the compressor hum starts |
| 0:47–0:57 | P6 | the hand rises before the shelves and stops short of the milk bottle; the fingers open and flex twice; at **0:51 "What was I after, anyway?!"** arrives from below; the hand hangs; hold | the refrigerator hum; one clink of a jar settling |
| 0:57–1:02 | whole page | the camera pulls back to the full page, which is now identical to the page PNG | the hum continues, then fades |
| 1:02–1:10 | paired pages | the subjective page (left) beside the objective baseline page (right), each 640 px wide on the dark board; held | room tone; the watch tick, faint |

**Exposure sheet rules.** Contacts and reaches are on ones. Holds and finger flexes are on twos. Replacement swaps happen on frame boundaries only, with no dissolves between profiles.

**FORAGED versus HANDMADE.**
- **HANDMADE:**
  - the lightbox page (fibrous translucent paper generated as a sheet, opaque board gutters);
  - every silhouette piece (hands, cuffs, typewriter, cup, note, pencil, stair strip, banister, watch with its tracing-paper dial, refrigerator, shelves, jars, milk bottle);
  - the balloon cards and rods;
  - all lettering (a single-stroke pen alphabet built for this work, mixed case after Madden);
  - the objective baseline page and its full-figure puppets.

  All of these are cut as scissor-faceted polygons, rigged and animated in code. They are not drawings filtered to look like paper.
- **FORAGED (reference motion, not pixels on screen):**
  - the hand key poses are rotoscoped from real gestures: typing (*Singing Wires*, 1951, cache b6100d97; *Learning to Set Type*, 1959, aaf17c56), the wristwatch turn (*Bookkeeping and You*, 1947, af625567), and the refrigerator reach (NARA 540882, Russell Lee 1946, PD, Commons; it is already in `films/sources/99-ways-subjective/`).
  - The traced contours set the piece proportions and the keyed joint angles. The pixels are never shown.
  - These are credited as "used_as: reference motion for puppet key poses".
- **FORAGED (sound):** typewriter, footsteps on wooden stairs, pencil on paper, a wristwatch tick, a refrigerator door and hum, a lamp switch, and a sleeve or cloth rustle.
  - Look first in the Moving Image Archive cache (clips with source sound; check that each is usable), then on Wikimedia Commons audio (PD, CC0, CC BY, CC BY-SA only, read from extmetadata).
  - The muffled offscreen voice is a public-domain spoken-word recording (e.g. a LibriVox PD recording on Commons, or a PD archive clip with speech). It is low-passed until the words are unintelligible. Captions carry the words.

## 7 · Aesthetic target (from `kf-2.png`, the look to meet or beat, and `assets/references/madden2.webp`)

- **Medium.** A backlit lightbox comic page. Translucent fibrous paper fills the panels, and the gutters are opaque board. The art is scissor-cut black card silhouettes with faceted edges, plus brass pin heads at the joints. Balloons are vellum cards on thin black rods. There is no line art inside a silhouette: Reiniger's rule, and Madden's solid-black massing.
- **Tonal range.**
  - kf-2 measured: panel paper median **#dfd7c9** (223,215,201) at the centre, falling to about **#d8cfc0** at the panel edges (lamp falloff); silhouette black **#0f0e0d**; gutter board **#3a3732 / #383530**.
  - Dark area inside the panels is 32–59% (kf-2). Madden's reference page is 27% dark, near-pure **#010101** on **#fefefe**.
  - Target: silhouette 10–20 L, paper 200–240 L, very few mid-tones except the soft penumbra of near-lamp pieces and the warm note paper.
- **Palette.**
  - paper cream #e9e1d2 (warmest centre) / #dfd7c9 / #d8cfc0;
  - MILK note and dial inlay tan #d9cab0;
  - balloon vellum #f6f2e6;
  - board #3a3732;
  - silhouette #0f0e0d;
  - brass pins #786234 (measured mean 120,98,52), tiny, under 0.3% of the area.
  - No other hues.
- **Light.** One lamp behind each panel, centred slightly upper-left (a radial falloff of about 35% to the corners), with fibre visible in transmitted light. Pieces against the screen are sharp. Hands nearer the lamp are softer and throw a penumbra offset of 4–10 px, which breathes as a hand lifts. The P5 refrigerator interior is a brighter patch.
- **Texture.**
  - Paper: long fibres plus cloud. It is part of the generated sheet, not a grain overlay on the film.
  - Silhouette edges: scissor facets of 6–12 px at page resolution.
  - The gutter board has a faint felt texture.
  - The film adds no film grain, vignette or line boil. Use `boil=0, wobble=0` in kit and draw the page canvas over the whole frame.
- **Framing and scale.** Madden's first-person framing: forearms and hands enter from the lower edges at the angle of an eye above them, close on the object worked on. Hands must fill 20–40% of the panel in P1, P2, P4 and P6. The P4 watch dial is at least 18% of the panel height so 1:15 reads at phone size. Fingers are cleaner and slimmer than kf-2: a visible gap between every finger in open poses, a distinct thumb, knuckle breaks at the two-segment joints, and fingernail-level facets. They must not read as mittens.
- **Typography.** Mixed-case hand lettering like Madden's, in black ink on the vellum card. Balloon text cap height is at least 2.4% of the page height. The caption is on a rectangular tracing-paper card.
- **Pacing.** One panel at a time, each a little scene. Contacts are snappy (on ones), holds quiet (on twos). Balloons arrive on a short damped spring, never as a fade. The defining beat gets the longest dwell (12 s).

## 8 · Units (makers only; the montage editor, blind readers, critic and reviewer are run separately by the workflow)

All units read this plan, the prompt, and SCIONs #2, #33 and #45 in full. They save media under `films/sources/99-ways-subjective/<role>/`.

1. **continuity-voice**: merges the prompt's continuity agent and writer. Output: `films/swarm/99-ways-subjective/continuity/event-ledger.json`. It also writes:
   - `continuity/visibility-map.json` and `continuity/visibility-map.png`: EyePose per panel and per P4 keyframe, FOV, the objects allowed and forbidden, H's bearing, and each balloon's speaker and exit edge;
   - `continuity/speech.json`: the balloon texts, entry paths, rod geometry, tail exits and timing;
   - `continuity/sound-cues.json`, plus the foraged and processed audio stems in `sources/.../continuity/`, and their credits entries;
   - `continuity/lettering.py` and `continuity/lettering-sheet.png`: the hand-built single-stroke alphabet and every balloon and caption lettered.
2. **hands** (viewpoint artist and puppeteer): rotoscopes the foraged hand gestures into key-pose contours, cuts and rigs the articulated hands, and animates them against exposure sheets for every panel. Output: `films/swarm/99-ways-subjective/hands/e4-test.mp4`. It also writes:
   - `hands/hands.py`, the rig plus `render(panel, t) -> RGBA` layers and pin and contact logs;
   - `hands/pose-sheet.png`, every pose drawing at page and phone sizes, plus a colour-removed read;
   - `hands/exposure-sheets.json`;
   - `hands/residuals.json`.

   It owns the watch, cuff and dial pieces, because they are rigged to the wrist.
3. **set** (lightbox and set builder): makes the lightbox page plate, the panel sets as cut-paper RGBA pieces with a depth plane each, the P4 panorama strip, the refrigerator door's 4 replacement profiles, shelves and milk, the balloon rod and card pieces (lettered from continuity's sheet), the layer DAG and penumbra compositor, and the **objective baseline page**. Output: `films/swarm/99-ways-subjective/set/plate-sheet.png`. It also writes:
   - `set/set.py` with `render(panel, t, hand_layers) -> panel RGB`;
   - `set/targets.json`: the world-space contact targets (key centres, pencil path, rail line, cuff edge, handle, bottle) in page px, read by hands;
   - `set/layer-dag.json`;
   - `set/baseline-page.png`.

Coupling contract: continuity → (hands, set). set → `targets.json` → hands. hands → layers → set's compositor. The coordinate frame is page px at 3200 × 1800 as tabled above.

**Editor** (run separately): `films/99-ways-subjective.py` composes the page canvas at time t from set and hands. It writes the page PNG (the final state at t = 57 s), the baseline page, and the film, all through kit's `Film`. It also writes `routes.json` and the deliverables below, and the credits and notes.

## 9 · Bar (frozen in `plan.json`), questions, intended reading, deliverables

See `plan.json`. It is not to be changed by makers. Proposed changes go in `amendments.md`.

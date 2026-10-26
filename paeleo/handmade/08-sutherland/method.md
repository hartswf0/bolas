# PAE-02 · SCION 08 · Ivan Sutherland: Constraint Sketchpad

## The swarm and its language

SCION-IVAN-SUTHERLAND. The native language is Sketchpad's: points, lines and arcs held by constraints, a constraint graph solved by *relaxation*, instances attached to a skeleton, and a light pen that changes relationships instead of redrawing points. The film is a Sketchpad session on a simulated vector display. In the 3 s title the drawing gets built: a crooked door frame relaxes square under its parallel, perpendicular and equal-length constraints, with the error counting down on screen. Then the drawing is operated. Each prompt is a light-pen manipulation, and the dog is never one of them.

- **Thesis (viewing):** you move a hand, and the rest of the body responds. A dragged hand pulls the arm to full length, bends the torso and leaves the feet planted. The display says the goal is **UNSATISFIABLE** and shows the gap as a dashed rubber band to the pen. The dog can't be selected. It only answers circumstances.
- **Numerical invariant (measured):** every hard constraint holds within 1 mm on every frame. Measured worst case: dog 0.20 mm, person 0.23 mm, door 0.00 mm.

## How it is built (build/, `make.sh` runs everything)

| file | role |
|---|---|
| `solver.py` | Graph of 3-D points (metres). Typed constraints: `Dist` (bone), `Pin` (inverse mass 0: a planted foot), `Floor` and `Wall` (inequalities: supported-on, behind), `Bend` (joint limit: the elbow chooses its side), soft `Plane`, soft `Goal`, `Attach` (attached-to), point masses. Gauss-Seidel relaxation alternates soft requests with hard projections, then runs hard-only passes with over-relaxation (ω = 1.5) until the worst hard error is under 0.2 mm or 150 passes. Each frame warm-starts from the last. Goals are rate-limited to 9 cm/frame, so nothing teleports. |
| `world.py` | The solve pass. It builds the dog (24 points, 77 hard constraints), the person (17 points, 35), the door leaf (hinge pinned, equal edges, equal diagonals), the porch, house and dusk as 3-D line primitives, and the pen script. It solves all 768 scene frames and writes the display data and sound events. |
| `render.py` | Composes a display file per frame and rasterises it as a vector CRT. Lines are plotted as spots. The beam draws the file in order at 150k spots/s, so recently drawn spots carry the blue-white P7 flash and the rest glow yellow-green. Two frames of persistence. Window clipping at the console line. Strokes of the house, door and light that fall behind a body are removed (hidden lines). The interior light is the door opening clipped by **Sutherland–Hodgman** against the leaf edge, then filled with scan-line hatching. |
| `sound.py` | numpy synthesis. Fans, 60 Hz hum, relays, and a display buzz whose pitch falls as the display file grows. Teletype clicks for every typed character. Pen ticks and drag hiss. The person's voice is loudspeaker tones: hard square-wave calls and soft harmonic phrases with reverb. Door creak, then a warm drone that follows the door angle. Paws come from the solver's own planting events, panned by x. There are also a settling sound, tail thumps while lying and wagging, and a breath. |
| `check.py` | Writes `trace.json` and `checks.json`. |
| `font.py` | A stroke font drawn for the display. |
| `strip.py` | Diagnostic crops around the dog. Not used by the film. |

**The dog.** Spine W–M–P. Neck and head W–N–Z. A 3-segment tail. Four legs: shoulder or hip (a real variable held rigidly to the spine), elbow or stifle, carpus or hock, paw. Bone ratios are medians over the 25 rig keys of the real archive dog (`pose_agent_v8.json`), scaled to a 0.62 m torso. After viewing I shortened the neck (×0.95) and head (×0.82), because the rig's "neck" key sits low and the first dog read as a horse. The score's acting becomes *requests*: withers and croup heights from crouch and lie, neck angle from head, head yaw toward the door from look, chin to the paws from rest, ear angle, and tail angle and wag. Feet follow a lateral-sequence walk whose phase is distance travelled (0.55 m per cycle, the score's walk_phase rate), plus yaw travel, so the dog steps as it turns. A stance paw is pinned. A swing paw is a goal on an arc. The solver makes the body satisfy all of it. Its outline is attached to the solved bones: torso, neck and head as splines through body-frame offsets, legs as tapered capsules. The graph itself is drawn dimly underneath, and planted points carry ground symbols.

**Staging.** A facade elevation with 14° of camera elevation. x runs along the porch (score metres). The dog's lane is 0.18 m out from the wall face, over the sill slab. The door is hinged on the right jamb and swings in. During 24.6–26.2 s the scale knob zooms from 150 to 200 px/m toward the sill.

**Pen script (the prompts).** Point at the head for *call*. Grab the hand and drag it toward the dog for *reach*. Drag the pelvis to a goal marker for *sit beside*. Drag the door handle (hinge constraint) for *open*. Drag the hand low for *offer*. Point for *soft*. Then the pen parks for the whole approach.

## Invariants: how they were measured (checks.json)

Measured on the solved graph, and on the rasterised dog spots for screen position:

1. **Choices at their times.** Onsets are measured from the dog's own geometry, not the score's state:
   - retreat: centre velocity above +0.05 m/s at **1.042** (score 1.0)
   - stops backing: the speed starts to brake at **2.333** (2.333)
   - refuse: nose drops 2 cm at **3.417** (3.417). The body passes 15° of turn at 3.542.
   - turns back to look: withers start to rise at **7.500** (7.458)
   - approach: velocity below −0.05 at **14.708** (14.708)
   - lie down: withers drop 2 cm at **23.833** (23.792)
   - looks in: muzzle more than 15° into the house at **26.542** (26.4)

   All are within ±0.25 s. Caveat: I chose the signal per choice. With a different signal, two land outside the window: the head-rise measure for "stops backing" fires at 1.58 because the head bobs during the walk, and the score's own body-turn act starts 0.45 s after the refusal. I made the body begin turning at the refusal instead of following that lag.
2. **Never enters.** The threshold is a hard `Wall` constraint: between the sill ends, no dog point may pass the door plane. The minimum z of any dog point inside the jambs is +0.0001 m. The minimum centre x is 0.570 (limit 0.56). On the last frame the dog is lying with 11 of its 24 points between the jambs and 13 outside. 50.9% of its rendered spots lie between the jambs.
3. **Commands push, circumstances earn.** The call moves the dog from 3.00 to 3.95 m. The reach turns it from facing (cos 1.0) to back turned (−0.97). Before the approach (14.71), the person is seated at 6.25, the door is past 70° at 6.50, the hand is below 0.45 m at 6.54 (by then the seated hand is already low; the pen sets the offered hand at 6.85–7.25), and the soft voice starts at 7.4.
4. **x follows the score.** The solved centre minus the score's x is at most 2.9 cm (mean 1.3 cm). The approach covers 3.413 m against the score's 3.406, with identical timing. Screen x against score x, wide camera: 151.9 px/m. The fit RMS is 11 px, because the centroid moves with the head and tail. The retreat goes +x, away from the door.

**Solver honesty.** Hard residuals are printed live on the console every frame. The unsatisfiable reach runs 29 frames, with a gap of up to 3.9 m. Planted paws slip 0 by construction (inverse mass 0). The largest single-frame point move is 14.5 cm for the dog: a carpus while it gets up and turns at 7.96 s, which is fast but visible as motion, not a jump. For the person it is 12 cm, the elbow during the reach.

## What failed and what changed

See `ledger.jsonl`. In short:
- Dependent hips could not be pulled by the legs. They became rigid-linked variables.
- Gauss–Seidel was slow along a chain pinned at both feet. I added over-relaxation.
- Under the reach, the whole person tipped like a plank. Point masses fixed it.
- The dog read as a horse. The proportions were redrawn.
- Getting up reached back to pins left from before the turn.
- Looking in pointed the neck straight up. Rotation is now gentler, with a dotted sight line ("aligned-with the door axis").
- The door leaf showed through the bodies. I added hidden-line removal.
- The nose crossed the door plane by 13 cm. The threshold became a constraint.
- Releasing the reach snapped the hand 76 cm in one frame. Goals are now rate-limited.

## What is protected / not done / unknown

- No pixels from any source appear. The archive dog is used only as measured proportions. QuickDraw, archive frames, masks, found footage, PAE-00 `stage.js` and the lenses were not used. Only the score and `machine.js` constants (sill, door width) were read.
- The person is a mannequin, and the voice is tones, not words. The typed prompts are the score's own text.
- Not built: an interactive constraint editor, a unit-test suite, or a mobile operator page. The SCION deliverable contract asks for these. This brief asks for a film, so the solver is exercised only by the film and by `check.py`.
- **Unknown:** no independent critic has watched this, and no human has. I looked at extracted frames and contact strips (title, every choice, the end card) but did not watch it at normal speed with sound. I checked the audio only by level: −19 dB mean, −1.1 dB peak. The flash band from the display-file refresh is visible as a moving brighter zone in the door hatching. That is intended, but it may read as flicker.

## Repair pass after critic round 1 (PASS, narrow)

The critic's ranked repair conditions, and what changed. Every passing element was kept as it was: the light-pen drags, HAND GOAL UNSATISFIABLE, THE DOG IS NOT SELECTABLE, and the dog lying across the sill.

1. **The head turns to the door as the dog rises (7.46–7.80).** The head now has its own yaw in the graph, which leads the shoulders by up to 143°. It starts moving at 7.458, and over 0.25 s the chin-on-paws pull fades out. Two things had been holding it back, and I found both in the solver trace rather than guessing: the no-teleport limit (9 cm/frame) and the leftover rest pose. The fix is a per-point speed limit: 13 cm/frame for the poll and 17 cm/frame for the nose, because a head can whip round faster than a body. Looked at: by 7.75 the head points at the door while the body is still rising, and by 8.15 the body has followed. Measured: the largest single-frame point move is now 17.8 cm, the nose at 7.79 s. The previous worst was 14.5 cm.
2–3. **The turns are rotations in depth, not mirror flips.** Yaw was already a graph parameter, but the body turned as one rigid plank. Every parallel projection has one direction in which a plank collapses edge-on. The dog now has **two yaws**: forequarters (W–M) and hindquarters (M–P). It turns as a U, bending at mid-back. Each pair of legs solves its joint limits in its own half's plane. The torso outline and three new cross-section rings are attached per half, so a body turned toward the camera reads as a barrel, not a line. The projection is now oblique (nearer points sit to the left, ×0.45) with 24° of elevation, so depth shows as a diagonal. Both turns pass through the camera side. Refusal: the forequarters go at 3.45 over 0.42 s and the hindquarters at 3.62 over 0.45 s. The head turns with the shoulders here; a leading head had to cross the body and tangled the drawing. Coming round: head, then forequarters at 7.58, then hindquarters at 7.85. Looked at, honestly: 3.75–3.85 is still a compact curled cluster for about 3 frames, legible as a dog curling rather than a clean silhouette. By 3.95 the back is clearly turned, head to the right.
4. **The soft voice is ≥6 dB below the call.** Measured on the final mix, bed included: 1.0 s call window −10.5 dB, 7.4 s window −20.5 dB, 26.4 s window −20.4 dB. The bed alone is about −22 dB.
5. **The look-in reads without the sight line.** The neck lifts by an extra 22° times the score's look value, and the head yaws a full radian toward the door. Looked at: between 26.4 and 26.7 the head rises clearly and turns into the doorway.
- **Phosphor trails no longer ghost the person during the zoom.** Earlier frames' persistence is now redrawn at the current scale-knob setting, so objects leave trails but a zoom does not smear.
- **The porch-roof fascia was removed.** Once the oblique moved it, it read as a beam floating across the house.

Measured after the repair:
- `tools/paeleo/check_handmade.py`: ALL OK (I1–I4).
- Own checks: all seven choice onsets within 0.25 s (unchanged times), and the hard residuals.
- Hard residuals: dog ≤ 0.20 mm, person ≤ 0.24 mm.
- The threshold constraint holds: the closest point inside the jambs is at z = +0.0001.
- The final lying dog has 52% of its rendered spots between the jambs.

A new cost of the U-turn: the midpoint of withers and croup drifts up to 15.7 cm off the score's x during the two turns, because the spine bends. Mean drift over the scene is 1.9 cm, and the approach still covers 3.398 m against the score's 3.406.

Not done: no new critic round. This repair is judged from my own frame strips, not from normal-speed viewing.

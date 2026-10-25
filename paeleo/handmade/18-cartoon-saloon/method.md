# SCION 18 · Cartoon Saloon — Painterly Puppet Discipline · the threshold, handmade

**State at hand-off:** a watchable 38 s film (`film.mp4`, 10.1 MB, 912 frames, H.264 + AAC, faststart). The checker
(`tools/paeleo/check_handmade.py`) reports ALL OK on my own trace. That is a builder's statement, not acceptance:
no independent critic has seen it yet.

## Thesis
The dog is a drawing, and it should look like the same drawing from the first frame to the last. That holds when it is
afraid, when it turns its back, when it lies down and when the camera comes close. The rig is there to protect the line and
the acting. It must not flatten them. The scene would go bland if the rig did the acting (a puppet sliding on a tween), if
the turns collapsed edge-on, or if the close-up thickened the line as if the camera were zooming into a picture.

## Swarm (one agent, roles merged)
Illustration art director, animation lead, hybrid rig/drawing supervisor, painterly compositor and performance editor were
all one agent working in one coupled codebase. Splitting them would have cost more in hand-offs than it saved. The
**independent style critic is not me**: it is the critic the caller assigns. I looked at my own frames at every choice
(listed in `ledger.jsonl`). That is not approval.

## Native formal language, as built
- **Layered drawings.** The exterior, the patterned interior and the cut-away architecture are each painted once into
  their own layer (per camera framing). Door leaf, light, hearth, stars, person and dog are separate per-frame layers.
  The dog has its own canvas, so it can be measured and graded alone. (`build/world.js`, `build/scene.js`)
- **Expression / turn sheet.** `build/sheet.js` is the model sheet, written point by point:
  - dog bodies: profile stand, crouch and lie; three-quarter rear (Q1); rear (RV); three-quarter rear lying.
  - five heads: profile, back-of-head 3/4, rear, three-quarter front (looking back over the shoulder), and "looking in"
    (back of the head to the viewer, muzzle into the room).
  - the woman standing and sitting.
  - Rendered as the rig uses them in `proof/turnsheet.png`.
- **Selective deformable rig.** The rig touches only:
  - two-bone legs solved to feet planted on the boards;
  - a six-link tail;
  - the neck that joins a substituted head to the body;
  - the woman's near arm (rest, reach, low).
  Everything else is drawing selection or in-betweening between authored drawings of the same part, by arclength
  resampling from a fixed start point. No mirroring of a profile: Q2 is the mirror of a three-quarter drawing.
- **Hand-painted textures.** Synthesized watercolour washes (`build/textures.py`, seeded FFT noise) are multiplied into
  each filled shape, with the pattern attached to the part. Each shape also gets a pooled-pigment edge. Paper grain goes
  on once, in screen space.
- **Compositing palettes.** Cool dusk outside. Warm lamplight in the room and in the pool of light from the open door.
  The dog's layer is graded by where it stands: cool on the far porch, warm as it comes into the light.
- **Shot style contract.**
  - One locked side elevation of a cut-away house and porch: the room is shown in section, the door frame is the cut
    wall, and the sill is a raised board.
  - World x is the score's x (threshold 0, sill 0.56, steps 4.9). Screen x = 320 + 180·x. The floor is at y = 600.
  - One intentional camera move: a slow push-in from 21.6 s to 25.0 s, to 1.85× on the threshold. It makes a matched
    wide / medium pair, and the medium holds through the ending.
  - Lines are tapered brush ribbons built in screen pixels, self-coloured (darker than the fill), with a fixed noise per
    drawing so they never boil.

## How the dog is made and how it moves
- **Body.** A rust-and-cream dog drawn as closed curves. It has a deep chest bib, a sickle tail with a cream tip, and big
  ears whose shape is in-betweened from "flat" to "pricked" (the ear is the first thing to react to the call).
- **Walk.** A gait solver plants each paw on the boards. A paw in stance does not move in the world. Swing paws lift and
  land ahead in the direction of travel (that includes backing away). Stride 0.40 m, duty 0.62, a lateral walk sequence.
  The body's x is exactly the score's x, so the approach covers the same distance at the same pace. Measured stance slip:
  **0.0 cm** over 1,346 stance-frame pairs (`build/cache/gaitcheck.json`).
- **Turns (3.46–3.72 s away; 8.12–8.6 s back), timed on twos.** The dog steps through L → Q1 → RV → Q2. Each frame is
  an in-between of two adjacent authored views, and its head is swapped for the view's head drawing. The forefeet lift
  and swing round first.
- **Refusal.** It holds Q2 (rump toward the door and the viewer, head away), then lies down with its back turned
  (4.2–4.85 s) and drops its head to rest. Ears flick at the door (6.2 s) and at the soft voice (7.05 s) before the head
  moves.
- **7.46 s.** The head is substituted for the three-quarter-front head over the shoulder, looking at the door. Then the
  dog rises and the body follows round.
- **Approach (14.7 s on).** The head is low and visibly below the line of the back for the whole approach. Ears are
  relaxed back, the tail low with a small wag.
- **Lying down (23.72–24.4 s).** The torso is in-betweened stand → lie, the forelegs extend on the boards and the hind
  legs fold. It lies across the sill: chest, forelegs and head inside the door frame, haunch and tail outside on the
  porch.
- **Come in (26.4 s).** The ears prick first. At 26.62 s the head drawing changes to "looking in" (back of the head to
  the viewer, muzzle into the room), with tail thumps on the boards. At 28.33 s it turns back, lowers its chin to its
  paws, closes its eyes and stays.

## Measured (from my own render)
**Choice onsets.** Detected in the dog layer's pixels and drawn geometry (`trace.json` → `measured_onsets`). The trace
`state` changes at these measured times; it is not copied from the score.

| choice | score | measured | dt | how it was detected |
|---|---|---|---|---|
| retreat | 1.000 | 1.042 | +0.042 | silhouette top drops (the ears go back); paws start to travel at 1.125 |
| watch | 2.333 | 2.458 | +0.125 | the head rises past the cowering/alert midpoint |
| refuse | 3.417 | 3.500 | +0.083 | silhouette width departs >6% (the turn begins) |
| watch | 7.458 | 7.500 | +0.042 | the drawn muzzle points back at the door |
| approach | 14.708 | 14.708 | 0.000 | the head drops and the paws start toward the door |
| lie_down | 23.792 | 23.875 | +0.083 | the top of the body over its centre drops |
| looks in | 26.400 | 26.458 | +0.058 | the ears prick; the head drawing changes at 26.62 |

**Invariants** (`invariants.json`): I1–I4 all ok.
- I2: x never below 0.59; ends at 0.59.
- I3: r = 0.999 on `x_world_measured`. The camera moves, so x is inverted from the measured screen centroid through the
  recorded camera.
- I4: back turned for 95.8% of refuse frames.

**Line quality, the numerical invariant of the theorem.** Mean dog line width is 1.600 px on screen across all 768
frames, including the 1.85× close-up. SD 0.0095 px, CV 0.6%. Static layers are re-painted, never scaled, for each
framing.

**Sound levels** (`build/cache/levels.json`):
- calls −23.2 dBFS RMS;
- soft lines −36.0 dBFS, 12.8 dB quieter than the calls;
- room tone −47.2 dBFS, so the soft voice is 11.2 dB above it.

## Looked at (by me, the builder)
- Contact sheets of the turns, frame by frame, before and after each repair.
- The walk at 16.0–16.75 s.
- The refusal, the look back, the push-in, the look-in and the settle.
- The four stills, the title and end cards.
- Whole-film sheets at 1 s intervals, extracted from `film.mp4` itself.

## What failed and what I changed
1. **Turns.** A rear-view in-between collapsed into a tall tangle ("giraffe"), and the tail swung the long way round.
   I redrew the rear view broader and lower and fixed the mirrored tail angle. The deepest cause was different: the
   mirrored outline had reversed winding, so the in-between paired opposite points and collapsed to a sliver. Keeping
   the winding fixed it. Every turn frame I looked at now reads as a dog.
2. **Lying legs went through the floor, and the knee bends were reversed.** I clamped folded joints to the boards and
   swapped the bend sides.
3. **A leg was stretched to the door at 1.08 s.** The swing start was uninitialised. I initialised it and measured the
   slip.
4. **The ending was too small to read.** The nose touched the woman's hand, and the look-in read as looking up at her.
   I added the push-in, with line weight compensated, and moved her seat further into the room. I also drew a new
   head (back of the head to the viewer) for looking in.
5. **The light from the door was weak.** I strengthened the pool and glow, and the room warms when the door opens.
6. **Small fixes.** The title fell back to a default serif (fixed with explicit font loads). The yard was unpainted, and
   the roof was a flat wedge (now thatch strokes).

## Still weak (my own reading; the critic may find more)
- The dog is small in the wide shot (about 140 px long). Expressions before 21.6 s are carried by ears, head angle and
  posture more than by the face.
- The three-quarter and rear views are simpler drawings than the profile. At normal speed the turn passes in about
  6 drawings.
- The cut-away convention: the room is visible before the door opens. "Light comes out" is staged as a warm pool and
  glow that grow with the door's swing. That is a stylistic exception, not physical light.
- The look-in may still read partly as looking at the door leaf rather than deep into the room.
- The voice is formant synthesis: prosody-like, but not intelligible words. **I cannot listen to sound.** Everything
  about the audio is measured levels and timing, not hearing.
- The woman is a secondary puppet: an in-betweened stand/sit pair and one rigged arm. Her stepping aside is quick.

## What I did not do
- No independent critique was run. There is no critic report from me, and I do not approve my own work.
- No branch forks: the repairs did not stall twice on one failure.
- No operator page was published. `index.html` in this folder is a local page only.
- No found footage, doodles or archive masks are used in the picture. The archive dog was only inspected (one frame and
  the pose keys) as a reference.
- No git.

## Rebuild
`build/make.sh` runs the whole chain: textures → render (Chromium canvas, `render.mjs`) → gait check → trace → sound →
mux → stills → checker. Intermediates go in `build/cache/`. `build/sheet.html` with `sheetTest()` renders the model
sheet.

## Round 2 (after critic round 1: PASS, narrow)

These repairs answer the critic's five conditions. Everything else is unchanged.

1. **Tail at 8.00–8.21 s.** The look-back head now sits over the far shoulder, and the tail hangs out and down off the
   rump until the body turns. I looked at every frame from 7.92 to 8.33 s: the tail is at the rump, away from the head.
2. **Light from the door, 6.2–7.4 s.**
   - The uniform haze is gone.
   - A soft-edged wedge of lit air now falls from the opening onto the boards, with a pool brightest at the sill. The sill
     and the door frame catch it, and all of it grows with the door's swing.
   - The cut-away room is held dim until the door opens, so the open door is what adds the light.
   - I looked at every frame from 6.0 to 7.5 s.
3. **Rear view, 3.65–3.72 s.** The head and ears stand above the shoulders, and the hind legs are drawn in front of the
   rump. I looked at every frame from 3.58 to 3.83 s.
4. **The low hand.** It is now an open palm, turned up and held level toward the dog at knee height, 1.55× larger, with a
   pale cuff that separates it from the sleeve.
5. **The retreat crouch.** The legs fold under the body instead of splaying. The gait is tighter: stride 0.34 m, paw
   offset at most 33 cm from the body centre. Stance slip is still 0.0 cm.

**Re-measured after the rebuild:**
- Choice onsets are unchanged: +0.042, +0.125, +0.083, +0.042, 0.000, +0.083 s; the look-in is +0.058 s.
- Checker: ALL OK. r = 0.999; back turned for 95.8% of refuse frames.
- Line width: 1.600 px, CV 0.6%.
- Soft voice: 12.8 dB under the calls and 11.2 dB above the room tone.
- `film.mp4`: 10.1 MB.

**Not done:** I did not attempt a wholesale redesign of the dog's silhouette (the optional condition 5, "a more designed
shape"). The turnaround is kept as the critic saw it.

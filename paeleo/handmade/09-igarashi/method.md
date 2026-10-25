# SCION 09 · Takeo Igarashi — the threshold, as-rigid-as-possible

PAE-02 cohort 3. `film.mp4`: 38.0 s, 1280×720, 24 fps, H.264 + AAC, 3.4 MB (912 frames: 72 title, 768 scene, 72 end card).
Rebuild: `bash build/make.sh`. Runtime demo and operator page: `demo.html`.

## Thesis

What a viewer should get: the dog is one sheet of drawn paper that bends like paper, and it still reads as the same dog in
every pose. Its local shape holds (the eye, the nose, the brass tag on its collar never smear) while the body cowers, turns
its back, sits, comes with its head low and lies across the sill. The passage that matters most is the refusal and the
turn back (3.4–8.3 s): what makes it bland or false is a flat figure mirrored or squashed edge-on. Here every frame of
both turns is a whole drawing, bent by the solver.

## Swarm (merged roles; one builder ran all of them, in sequence)

There was one agent here, not six. The prompt's roles became stages, each leaving an artifact it could be checked by:

| role | artifact |
|---|---|
| Illustrator | `build/drawings.js` → `assets/drawings/*.png`: six dog drawings (standing profile, standing from behind, sitting from behind, lying, head in profile, back of the head) and two person drawings (standing, sitting), each person drawing in two layers (body, near arm) |
| Mesh builder | `build/mesh.py` → `assets/mesh/*.json`: a grid triangulation clipped to each drawing's alpha, explicit cuts, handles, feature-protect masks |
| Rig handle designer | `build/rig.js`: turns each score frame into handle targets, knee IK, the stepping simulation, which drawing is shown when |
| Optimization engineer | `build/arap.js`: the solver, with the inversion repair |
| Performance profiler | `diagnostics.json` `frame_ms`; the demo prints the solve time per drag |
| Independent shape critic | **not done here.** The builder does not approve its own work; the critic is the next step |

## Native formal language, as built

- **Triangulated mesh.** Grid cells of 6–9 px that touch any ink, two triangles each, numbered row by row so the system
  has a narrow band (bandwidth 19–75). The standing dog: 1,413 vertices, 2,488 triangles.
- **Control handles.** Small vertex sets (about 1.6 cells across, the person's head bigger), each pulled to a target
  point. The handle point is the centroid of its vertices. The rig sets the handles: withers, back, hip, belly, neck
  socket, tail middle and tip, four feet, four knees or hocks, and on the heads the skull, muzzle, neck and ear tips.
- **Local rotation estimates.** Each iteration, every triangle gets its best rotation in closed form (2D Procrustes over
  its three cotangent-weighted edges). So does every handle whose rotation the rig leaves free. The feet are held level.
- **Energy minimization.** E = Σ w_t Σ_e c_e ‖(x_i−x_j) − R_t(p_i−p_j)‖² + λ Σ handle terms. The global step is one banded
  Cholesky solve for x and one for y. The factor is computed once per handle set and reused every frame. Each frame runs 8
  iterations warm-started from the previous frame, or 40 after a drawing swap.
- **Feature-protect masks.** Triangles inside the eye, nose and collar tag (head in profile), the buckle and nose tip
  (back of the head), and the person's eye and buttons get rigidity weight 40.
- **Explicit cuts and draw swaps** (the prompt's repair when rigid shapes refuse a gesture). There are two cuts in the
  standing dog's mesh, made by duplicating vertices: one between the near and far forelegs, one at the tail notch. The
  turns, the sit and the lie are swaps between whole drawings. ARAP bends each drawing across a swap, for example the
  back view's front end swinging round.
- Time base: the score's frames (24 fps, frame i = scene frame i). Coordinates: drawings at 364 px/m (the dog ×1.15);
  the stage at x_screen = 320 + 190·x metres on the line y = 590. The camera is fixed.

## How the dog moves

- **Watch.** The standing profile breathes. Its head, ears and tail follow the score's acts.
- **Retreat (1.0).** It flinches down: withers 13 px, hips 24 px (drawing px), head down, ears flat, tail low. Then it
  backs away. Its feet come from a stepping simulation: each foot is either planted on the boards or in the air on a step,
  so nothing slides. Measured: in 1,519 planted-foot frame pairs the rendered feet moved at most 0.01 px.
- **Refuse (3.42).** For 2 frames the head drops. Then the head turns away: the back-of-head drawing goes on the profile
  body, so the head leads the turn. At 3.625 the body swaps to the back view, its front end still swung toward the door,
  and ARAP swings it round by 3.83. At 4.75 it swaps to sitting with its back turned. The head droops as the score's
  `rest` rises.
- **Watch (7.46).** The head swaps to the profile head looking back over its shoulder at the door, on the frame of the
  choice. At 7.75 it stands (back view, head still on the door). From 7.95 the front end swings toward the door. At 8.21
  the profile takes over.
- **Approach (14.71).** It walks toward the door. The head comes down over 0.35 s and stays below the withers line for
  the whole approach: measured skull below withers in 100% of approach frames after the first 0.35 s. The tail is low
  with a small wag.
- **Lie down (23.79).** It crouches: the legs fold by IK and the forefeet step forward. At 24.125 it swaps to the lying
  drawing, which settles from slightly high. The head is up, then drops to the paws.
- **Come in (26.4).** The head swaps to the back of the head, raised, with the nose tip peeking. That puts the back of
  its head toward us and its muzzle into the lit hall. At 28.1 the profile head comes back and settles to the paws. It
  stays.
- **The person** is ARAP too. The near arm is its own layer with an IK elbow: a beckon on the first call, a reach on the
  second, resting on the knee, then offered low at 6.8. The person steps aside in four planted steps, then a short bend
  and a swap to the seated drawing on the crate. The head bows slightly on the soft lines.
- **The world.** The house front, door, hall, porch, railing, dusk and light spill are drawn in canvas at render time.
  The door swings in from its right hinge. The hall light comes on with it, the light fans onto the boards and the dusk
  deepens over the 32 s. The moon and trees are Quick, Draw! drawings stroked as chalk.

## Measured (from the render; `trace.json`, `diagnostics.json`, `invariants.json`)

`check_handmade.py`: **ALL OK**.
- I1: all six choices at dt 0.
- I2: min x 0.59, end x 0.59.
- I3: r = 1.0 on x_screen, the alpha centroid of the read-back dog layer.
- I4: back turned in 96.9% of refuse frames. The first 2 frames are the flinch, still facing the door.

Choice onsets measured from rendered signals, not from the state label:

| choice | score t | measured t | dt | signal |
|---|---|---|---|---|
| retreat | 1.000 | 1.083 | +0.083 | withers drop > 2 px or centroid moves away > 1.5 px |
| watch | 2.333 | 2.333 | 0 | top of the dog rises 3 px above its cowering height |
| refuse | 3.417 | 3.542 | +0.125 | rendered muzzle on the far side of the neck from the door |
| watch | 7.458 | 7.458 | 0 | rendered muzzle back on the door side |
| approach | 14.708 | 14.750 | +0.042 | centroid moves toward the door > 1.5 px |
| lie down | 23.792 | 23.958 | +0.166 | rendered withers 4 px below the walking height |
| looks in | 26.4 | 26.458 | +0.058 | the back-of-head drawing is shown on the lying dog |

Solver bar:
- **Inverted triangles: 0 in all 768 frames for every piece.** Before the repairs there were up to 42 in a frame (see below).
- Normalized ARAP energy, worst frame: 0.11 on the dog body.
- Worst protected-feature distortion max|σ−1|: 0.009 on the dog's heads, 0.088 on the person's buttons and eye.
- Smallest triangle area ratio: 0.0008 on a dog-head triangle (an ear flattening, nearly collapsed but not flipped).
- Frame time with rig, solve and full compositing: mean 105 ms and p95 164 ms, in headless Chromium on SwiftShader (no
  GPU). The solve alone is about 10–15 ms per piece, so it runs at interactive rates on this machine. No target device
  was tested.
- At the end, 44.5% of the dog's rendered width is inside the door frame (head, forelegs, chest). The tail is outside.

ARAP against weighted skinning (`proof/arap_vs_skinning.png`, `proof/proof.json`): same mesh, same handle targets, and
skinning is given ARAP's own handle rotations, so it is not a straw man.

| pose | ARAP inverted (raw → repaired) | skinning inverted | energy ARAP / skinning |
|---|---|---|---|
| head low 19.0 s | 0 → 0 | 25 | 0.017 / 0.14 |
| crouch onto sill 24.08 s | 2 → 0 | 53 | 0.034 / 0.13 |
| cowering 1.8 s | 0 → 0 | 78 | 0.025 / 0.14 |
| back view swinging 3.67 s | 1 → 0 | 0 | 0.015 / 0.036 |

Feature protection (`proof/feature_protect.png`): the head in profile under a hard pose has eye, nose and tag distortion
0.05 with the masks and 0.68 without them.

Sound, measured from the mix (`build/cache/sound_levels.json`):
- The calls average −18.8 dBFS RMS. The soft lines average −30.1 to −30.6, **11.3 dB quieter**.
- Room tone (air, crickets, the warm chord) is −39.0 dBFS while the light is on and −49.4 before it. The soft voice sits
  about 9 dB above it.
- Peak −1.5 dBFS.

## Looked at (perceptually judged by the builder only; not a critic's verdict)

I looked at every frame of both turns (3.42–3.96 s and 7.42–8.38 s), the walk (15.5–17.1 s, every second frame),
contact sheets of the whole film at 2 fps, the four stills and the end card. In my judgement:
- every turn frame reads as a dog (profile, head turned away, back view, sitting back view, looking over the shoulder);
- the back is unmistakable from 3.625 s;
- the head is low through the approach;
- the lying dog is flat across the sill, front inside the frame and tail out;
- the look-in reads in depth (the back of the head against the lit hall).

## What failed and what changed (`ledger.jsonl`)

1. **The first back views read as a dog facing us.** In the 3/4 rear drawing and the first back of the head, a dark
   central patch looked like a face mask. Both were redrawn as a true back view: two haunches with the tail between
   them, heel pads, the spine and saddle receding, the backs of the ears, a collar buckle at the nape and only the nose
   tip peeking.
2. **Feet were splayed at rest and stretched at the start of a walk.** This came from a phase gait. It was replaced by a
   stepping simulation in which feet are planted or lifted, never slid.
3. **ARAP itself turned triangles over** (up to 42 in a frame).
   - Causes: knees bending the wrong way on near-straight legs, the tail pressed into the rump notch, the forelegs
     bridged by cells through the paper margin, and the back view's hips and belly lowered too far.
   - Repairs: explicit bend directions (knees forward, hocks back), a limited tail tuck, level paws, two mesh cuts,
     halved rear lowering, and an inversion repair. The repair makes any triangle that flips and its neighbours ×4
     stiffer and solves again. The stiffening is kept, so each mesh accumulates a heat map of where this rig fails.
4. **Handle targets were offset from their own vertices**: the target point was the named point, not the vertex
   centroid. This caused a constant 0.33 shear on the seated person's top button. Handle points are now centroids.
5. **The person's step aside smeared the shoes.** One planted foot was held while the body moved a metre. It is now four
   alternating steps.
6. **The lie-down onset first measured 0.67 s late.** The criterion used the top of the bounding box, which the head
   defines. It now uses the rendered withers.
7. **Rendering took 2–3 s a frame** because of canvas readback on the GPU-backed canvas. It now runs with a software 2D
   canvas, at about 0.3 s a frame.

## What is still weak

- **The dog is small in a wide, fixed frame,** about 230 px long standing and 300 px lying. Faces and the tag are legible
  at 1280×720 but not at phone size.
- **Leg bends are rubbery.** ARAP bends a leg along its length, not at a joint, so the cower and the crouch onto the sill
  look like bent paper strips. That is the lineage's look, but a critic may read it as boneless. The swinging foot
  sometimes overlaps the other leg in the walk.
- **Swaps are hard cuts between drawings.** The x-centre of the dog jumps a little at the profile ↔ back-view swaps,
  because the drawings have different centres.
- **The head-to-neck joins show a seam** when the head is low (the collar edge over the body's neck stub).
- **The voice is flite TTS.** It is intelligible as text on screen, but I cannot hear how mechanical it sounds.
- **The person's acting is minimal.** There is no mouth movement, only head and arm handles.

## What was not done / unknown

- **No independent critic has seen this film.** Nothing here is a pass.
- **I cannot listen.** The sound was checked only by measurement (levels, event timing from the rig). How it actually
  sounds is unknown.
- **No human viewing.** No target-device or mobile performance test.
- **No reusable rig-metadata export** beyond the mesh JSONs (handles, cuts, weights). The repair heat map stays in
  memory and is not written out.
- **The archive dog footage was looked at once** as a contact sheet for a shepherd's build. Nothing from it (pixels,
  masks, keys) is in the film.
- **The typed prompts are not shown.** The person's spoken words appear quietly at the foot of the frame.

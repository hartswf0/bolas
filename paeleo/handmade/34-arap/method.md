# SCION 34 · ARAP — the threshold, bent as rigidly as possible

PAE-02 cohort 5. `film.mp4`: 38.0 s, 1280×720, 24 fps, H.264 + AAC, faststart, about 3.6 MB
(912 frames: 72 title, 768 scene, 72 end card; the end card draws the rest mesh and the lying mesh with their
handles). Rebuild: `bash build/make.sh`.

## Thesis

The prompt's theorem: *bend engraved and photographed characters while preserving local proportions and recognizable
material structure.* I took the engraving half.

The dog is an engraving: ink lines on paper, with hatching that runs along each limb and around the barrel of the
body. It is a triangle mesh, and every pose is an as-rigid-as-possible solve from a few constrained patches. A naive
warp would stretch the hatching, crowd it and turn it over. ARAP keeps the line spacing and the eye and nose intact
while the body cowers, turns its back, lies down, comes with its head low and lies across the sill.

The passage that matters most is the refusal and the turn back (3.4–8.6 s). What would make it bland is a profile
mirrored edge-on, or a mesh that rubber-bands.

**Numerical invariant:** inverted triangles per frame, measured on every solved mesh (see below).
**Judged only by viewing:** whether the dog reads as one creature in every frame of both turns, and on the sill.

## Material: why not the photograph

I first looked at the archive dog (`kit/archive-dog`, 50 frames at 384×288).
- The dog in it is about 130 px long, blurred and grey.
- Its SAM mask merges the hind legs and drops the tail.
- At film size it reads as a smudge.

Swarm 10 (MLS) warps one image. So I drew the dog in code instead, as an engraving (`build/engrave.py`,
`build/draw_dog.py`):
- Each part is a mask with its own hatch field: lengthwise on the torso, along the limb axis on the legs (bunched toward
  the edges as on a cylinder), and along the muzzle on the head.
- Line width follows a light computed from a "puffy" height field. Shadowed parts get cross-hatching. A darker saddle
  is cut into the back.
- The proportions (body length about 1.7 × chest height, neck about 0.3 of the body) were read as numbers from the
  archive dog's rig keys. None of its pixels are in the film.

The person and the place are engraved the same way, so the whole film is one material.

## Swarm (merged roles; one builder ran all of them, in sequence)

| role | artifact |
|---|---|
| Mesh tessellator | `build/mesh.py` → `assets/mesh/*.npz`: Poisson-disk outline samples (9 mm) and interior samples (17 mm, 8 mm inside protected features), triangulated by scipy Delaunay. A triangle is kept only if its centroid and six edge points are inside the drawing, which separates the legs and the ears. Dog profile: 1,086 vertices / 1,653 triangles; profile head 265 / 420; rear view 469 / 730 + 156 / 218; front view 503 / 786 + 267 / 406 |
| Local-global solver | `build/arap.py` |
| Control handle artist | `build/rig.py`, `build/prig.py`, `build/perform.py` (the score → handle targets; the stepping simulation; the turn schedule) |
| Visual protector | rigidity weight 30 on the eye and nose triangles; the inversion repair and the flip guard |
| Frame regression analyst | `build/render.py` measurements → `build/trace.py` → `trace.json`; `build/proof.py` → `proof/` |
| Independent quality critic | **not done.** I do not approve my own work |

## The solver: how it differs from Swarm 09 (Igarashi)

I read only 09's `method.md`. It solves per-triangle rotations (2D Procrustes over each triangle's three
cotangent-weighted edges) with soft handle penalties (λ), one banded Cholesky in JavaScript, on a grid mesh (6–9 px
cells) over drawn, flat-filled paper figures.

Mine differs in solve, mesh and material:
- **Rotations per vertex cell, not per triangle** (Sorkine & Alexa 2007). For each vertex,
  S_i = Σ_j w_ij (p_i − p_j)(x_i − x_j)ᵀ and the rotation has a closed form, θ_i = atan2(S01 − S10, S00 + S11).
  The global right-hand side is Σ_j w_ij/2 (R_i + R_j)(p_i − p_j).
- **Hard handles by elimination, not penalties.** Constrained vertices are removed from the system. The free block
  L_FF of the cotangent Laplacian (weights clamped positive, scaled per triangle by its rigidity) is factored once per
  mesh with SuperLU (`scipy.sparse.linalg.splu`). Each global step is two back-substitutions.
- **Warm starts.** Each frame starts from the last solution and runs 8 iterations. A new view starts from rest with 40.
  The solve is 10–30 ms per piece on this machine (numpy).
- **Mesh.** A conforming Delaunay triangulation of Poisson samples that follows the drawing's outline, not a raster
  grid.
- **Material.** Engraved line fields, not filled paper. The structure ARAP protects is the hatching itself.
- **Inversion repair.** When triangles turn over, they and their one-ring are stiffened ×3 (capped at ×400) and solved
  again, up to 10 rounds. The stiffening then relaxes ×0.93 a frame back toward 1, so the repair map follows the pose
  rather than piling up (my first version piled up; see failures). A last flip guard pulls the free vertices of any
  still-inverted triangle halfway to their one-ring mean.
- **The look over the shoulder is a Jacobian flip.** The head mesh has a second solver whose rest shape is reflected
  (determinant −1, triangle order reversed). 09 swapped to a separately drawn head.
- **Similar to 09, to say plainly:** the turns are substitutions between views bridged by ARAP, the head leads the
  turn, and stiffening is used as a repair. The prompt's own §6 prescribes this ("change the handle topology, rest mesh
  or add substitution art").

## Handles: few, rigid patches; IK places the knees

**Profile body: 16 handles.**
- Shoulder patch and hip patch. Body pitch comes from the line between them.
- Neck tip, swung about the shoulder by the head act.
- Tail middle and tail tip (tail act, wag).
- Four paws and four wrist/hock patches. Each is a few vertices.
- Three knee patches placed by two-bone IK. The near hind knee has none, because the thigh drawing covers it and ARAP
  decides that bend.
- The knee and ankle patches turn with the bones measured from the IK joints. That fixed the first render's tangles
  (see failures).

**Head: 4 handles** (skull, nose, two ear tips). Ear act 0 folds the tips back by 1.25 rad, and ARAP bends the ears.

Everything else is ARAP's: the bend of every leg, the belly, the neck, the chest's barrel, the fold of the ears, the
crease when the dog lies.

**Rear and front views:** 7–9 handles each (paws, back or chest, hip or neck, knees, tail tip). Crouch, a wagging tail
and a width ("arrival") parameter drive them.

## How the dog moves (score frame = scene frame; camera A wide to 20.5 s, then B closer on the sill)

- **Watch (0–1.0).** The profile breathes (4 mm, 2.4 s). Head up, ears pricked.
- **Retreat (1.0).**
  - The score's crouch rises to 0.9: the shoulders drop 85 mm and the hips 110 mm. The head drops, the ears fold flat
    and the tail tucks under, with its tip curled.
  - It backs away 0.9 m on planted feet. Stepping is an event simulation: a planted paw never moves in the world. A paw
    swings (0.22 s, 45 mm lift) only when it lags 9 cm behind its neutral place, at most two at a time and never both
    of a pair.
- **Refuse (3.417).**
  1. 3.42–3.50: the head drops.
  2. 3.54–3.63: the head mesh flips (the reflected rest shape), so the muzzle points away over its back.
  3. 3.67–3.83: substitution to the rear view (haunches, tail, the back of the head). It arrives 35% wide and narrows,
     and the head swings behind the shoulders from left to right.
  4. 3.875: the profile again, facing away and arriving foreshortened (72% → 100% width over 3 frames). Head low, tail
     tucked.
  5. 4.3–5.0: it lies down with its back to the door. 5.8–6.5: its chin goes down (score `rest`).
- **Watch (7.458).**
  1. On the frame of the choice, the head mesh flips again: the lying dog looks back over its shoulder at the opened
     door.
  2. 7.5–8.2: it gets up (score `lie` 0.84 → 0.08) still looking back.
  3. 8.25–8.50: the front view, with its head turned a quarter toward the door.
  4. 8.54: the profile facing the door, arriving foreshortened.
- **Approach (14.708).**
  - It walks to the sill on planted feet. The head comes down over 0.35 s and is held below the back line.
  - Measured: the rendered muzzle is below the rendered shoulder patch in **100%** of approach frames after 15.05 s.
  - The tail is low with a small wag.
- **Lie down (23.792).**
  - The pose goes from standing to a deep crouch (paws planted, forefeet reaching) to a sphinx lie. The forelegs lie
    straight forward, the hind legs fold under, the tail lies back along the boards and the back is flat.
  - At the end 0.56 of the rendered dog's area is left of the door plane (head, chest, forelegs). The rump and tail stay on the
    porch.
- **Come in (26.4).** The neck stretches 14% and the head lifts and reaches into the lit room, ears pricked, tail
  sweeping the boards. From 28.3 the chin goes to the paws and it stays.
- **The person.**
  - Engraved meshes: standing, seated, and the near arm as its own mesh (shoulder, elbow, hand handles).
  - She beckons twice on the first call, then leans and reaches on the second.
  - She backs into the room in three planted steps and bends toward the stool. The seated drawing takes over and
    settles from 60 mm high.
  - She offers the hand low from 6.8 and bows her head a little on each soft line.
- **The place.**
  - A cutaway, seen from the side. The wall is cut at the door (poché). The door leaf swings into the room, from a
    sliver (ajar) to a full panel at 6.2–7.3.
  - The light comes out with it: a warm band on the boards and warm air that lights the figures. The dog and the person
    are lit by the same light map, so the dog warms as it enters the beam.
  - Dusk darkens over the 32 s. Moon and trees are Quick, Draw! strokes in pale chalk.

## Measured (from the render: `trace.json`, `proof/proof.json`, `build/cache/sound_levels.json`)

`python3 tools/paeleo/check_handmade.py paeleo/handmade/34-arap`: **ALL OK** (I1–I4).
- I3 uses `x_world_measured`: the rendered alpha centroid back-projected through each camera.
- I4: the facing is measured on screen. The rendered muzzle points away, or the rear view shows, in 97% of refuse
  frames. The first 3 frames are the head drop, still facing the door.

Choice onsets, measured from rendered signals (not from the state labels):

| choice | score t | measured t | dt | signal |
|---|---|---|---|---|
| retreat | 1.000 | 1.000 | 0 | dog drops > 3 px or moves away > 1.5 px |
| watch | 2.333 | 2.333 | 0 | top of the dog rises 3 px above its cowering low |
| refuse | 3.417 | 3.542 | +0.125 | rendered muzzle points away from the door |
| (back shown in profile) | — | 3.875 | — | whole body facing away |
| watch | 7.458 | 7.458 | 0 | rendered muzzle points to the door |
| approach | 14.708 | 14.750 | +0.042 | centroid moves toward the door > 1.5 px |
| lie down | 23.792 | 23.792 | 0 | rendered shoulder patch 3 px below its walking height |
| looks in | 26.4 | 26.458 | +0.058 | muzzle lifts and reaches into the doorway > 2 px |

Solver bar:
- **Inverted triangles: not zero.** 38 of 768 frames (4.9%) keep 1–6 inverted triangles after repair (49 in all). Most are
  single sliver triangles at the front of the stifle or the wrist crease while the dog cowers, refuses or settles. They
  are not visible at film size, but the bar is not met. `trace.json` has the count per frame.
- Normalized ARAP energy on the dog body: worst frame about 0.26.
- **Against a naive warp** (`proof/arap_vs_naive.jpg`): same mesh, same handle targets, the naive warp being Shepard
  inverse-distance interpolation of the handle moves. Body mesh only:

| pose | ARAP inverted | naive inverted | mean / p95 stretch, ARAP | mean / p95 stretch, naive |
|---|---|---|---|---|
| head low | 0 | 51 | 0.081 / 0.28 | 0.19 / 0.83 |
| cowering | 0 | 40 | 0.15 / 0.38 | 0.37 / 0.96 |
| lying | 0 | 274 | 0.24 / 0.61 | 0.52 / 1.00 |

Sound (`build/cache/sound_levels.json`, measured on the mix):
- Calls −18.5 and −16.8 dBFS RMS. Soft lines −32.2, −31.1, −31.6: **14 dB quieter**.
- Room tone −48 dBFS mid-film, −54 at the start.
- Voice onsets 1.00, 3.40, 7.41, 10.41, 26.41 s. Peak −3 dBFS.

## Looked at (perceptually judged by the builder only; not a critic's verdict)

- Contact sheets of the whole scene at 1 s.
- Every second frame of the refusal (3.17–4.08) and of the turn back (7.33–8.96).
- The walk at 17.3–18.4 and the lie at 24–31 s, as close crops. The four stills and the end card.

In my judgement:
- the cower reads;
- the head leads the turn away, the rear view reads as a dog seen from behind, and the turned profile shows its rump
  to the door by 3.875;
- the look back over the shoulder at 7.46 reads as a look back;
- the front view with the head toward the door bridges the turn back;
- the head is low throughout the approach;
- the dog lies flat across the sill with the front inside the door frame and the tail on the porch.

## What failed and what changed (`ledger.jsonl`)

1. **The photograph** was too small and soft to carry a dog at film size. I changed to an engraving drawn in code.
2. **The engraving had no light** (the height field was too flat) and showed fingerprint rings on contour hatching.
   Fixes: a puffy height field, unclamped limb hatching, and directional hatch on the masses.
3. **The dog vanished into the dusk:** the same light on figure and ground. Figures now get a paler light than the
   background.
4. **Lying inversions (11–19).** Wrist patches were rotated the wrong way, and paw and ankle patches touched (triangles
   between two rigid patches cannot be repaired by any solve). I fixed the signs, separated the patches, and made joint
   patches turn with their bones. The lying pose then had 0 inversions.
5. **First full render: 62–140 inversions a frame in the cower and the refusal.** My stiffening compounded forever, and
   the knee patches were held at angle 0 while the legs swung. I stopped the render, capped and decayed the stiffening,
   rotated the joint patches with the bones and added a flip guard. The residual is above.
6. **The look-away head** first showed as a crumpled "beak". The reflected head solver was warm-started from an
   unreflected shape and ARAP cannot undo a reflection. It now cold-starts from the rest head placed rigidly.
7. **Energy spikes of 0.8 in the walk** came from over-long hind steps. I shortened the step trigger and target (12/13 cm
   → 9/9 cm). Worst energy is now 0.26.
8. **Lie-down onset measured +0.58 s late.** The criterion used the top of the dog, which the rising head defines. It
   now uses the rendered shoulder patch.
9. **On the sill the back humped and the tail hung under the floor.** The lying shoulder and hip patches no longer
   squeeze the spine, and the tail lies back along the boards.

## What is still weak

- **Residual single-triangle inversions** in 4.9% of frames (above). The bar "no triangle inversions" is not met.
- **Legs are rubbery and the dog is lean and leggy**, near a hyena or coyote. ARAP bends a strip along its length,
  so the cower and the walk look like bent tubes of hatching.
- **The views are hard swaps.** Profile → rear → profile and lying-profile → front → profile change silhouette in one
  frame. Width "arrival" and foreshortening soften this, but there are no drawn in-betweens.
- **The rear and front views are smaller and plainer** than the profile.
- **The camera A dog is small** (about 190 px long). The engraving lines are about 3 px apart there and may shimmer
  under compression.
- **The lit railing.** After the door opens, the beam's haze lightens the railing behind the dog, which flattens it.
- **The voice is my own formant synthesizer.** I cannot hear it. It is likely robotic, so the words are also shown
  quietly at the foot of the frame.
- **The person** is plain. She has no mouth movement and her steps back are short shuffles under the smock.

## What was not done / unknown

- **No independent critic has seen this film.** Nothing here is a pass.
- **No listening.** The sound was measured, not heard.
- **No mobile operator page** and no side-by-side playback video. The counterexample set is stills (`proof/`).
- **Feet are planted by construction** in the stepping simulation. That the rendered paw pixels do not slide was not
  measured separately.
- **The deformed mesh cache is not kept** (it is regenerated by `render.py`). The rendered frames are deleted after
  encoding to keep the folder lean.

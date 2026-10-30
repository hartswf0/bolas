# SCION 37 · Weighted Skinning (Mesh Attachment Laboratory), the threshold

## Thesis

The dog is **one continuous skin** attached to a skeleton by per-vertex weights. It has no parts, cut-outs or substitutions:
every frame shows the same closed surface (7,173 vertices, 14,344 triangles, Euler characteristic 2, no boundary edges)
stretching and folding over moving bones. The swarm's primitives are its working objects: vertex-to-bone weights,
bind/rest matrices, skeletal motion clips, region masks (the coat), and corrective deformation. Here the correction is
dual-quaternion skinning, chosen over linear blend skinning because LBS was measured to collapse at the joints this film
uses hardest. A bland version would be a rigid maquette with a fur shader, or a mesh that never shows the bones underneath.

## How the dog is built (all in `build/`, numpy and scipy only)

- **Sculpture → mesh** (`mesh.py`). A signed-distance sculpture (smooth unions of round cones and ellipsoids laid on the rest
  skeleton; the left and right sides joined with a hard min so the legs do not web) is polygonised by **surface nets** at
  1.75 cm, then the largest component is kept and lightly Taubin-smoothed. The facets are left visible (intentional angularity).
- **Skeleton** (`rig.py`). 27 deforming bones: pelvis, spine, chest, neck1, neck2, head, two ears, three tail bones, and four
  legs with four bones each. Rest frames are axis-aligned, so bind = Trans(p_j); skin matrix S_j = G_j · bind_j⁻¹.
- **Weights** (`mesh.py heat_weights`). Pinocchio bone heat: solve (L + M·H) w_j = M·H·p_j on the cotangent Laplacian with
  H = 12/d² to the nearest bone segment. In place of Pinocchio's visibility test, limb bones may not be "nearest" to the
  flank or the back. The weights are pruned to the top 4 per vertex and renormalised (max |Σw − 1| = 3e-16). The maps are in
  `proof/weights_*.png` and on the end card.
- **Skinning** (`rig.py`). Both LBS and DQS (Kavan et al.: blended unit dual quaternions, with antipodality fixed against
  the heaviest bone, then normalised) are implemented. **The film is skinned with DQS**, and the person is skinned the same way.
- **Coat** (`texture.py`). The film pixels of the public-domain archive dog (*Amateur Film New Jersey C*): 8,969 patches of
  10×10 px from 25 frames, taken inside its SAM masks eroded by 3 px, upscaled ×3.2 and quilted with feathered edges inside
  painted **region masks** (dark saddle, dark muzzle and ear backs, lighter socks), with a sepia grade. The texture is mapped
  by bind-pose side-projection UVs, so it is fixed to the surface: it stretches with the skin and does not swim. The eye,
  nose and lip line are painted by hand, because the archive head is about 20 px.

## How it moves (`perform.py`, from the score)

- The root follows the score's x (X = x − 0.17 m, which puts the body centre over the sill at x = 0.59). The yaw comes from
  the score's turn with my own easing. The refusal turns away through the rear view and is fully turned at 3.97 s. The turn
  back passes through the front view.
- **Feet:** a gait clock advances only when a girdle must travel, by translation or by turning. Each swinging foot aims at
  where its hip will be at mid-stance (the whole root path is known in advance). Two-bone IK in the leg plane, with an
  abduction roll, holds each pastern upright. Planted paws slide **0.0 mm per frame** (audited in `perform.py`).
- **Lying** is a sphinx clip (forearms flat, hind legs folded, hocks on the ground) blended in by the score's `lie`.
- **Head leads at 7.46 s:** the look-back bends the spine, chest, neck1, neck2 and head round over the near shoulder, with a
  head tilt (a real twist along the neck), while the body is still down. The body rises at 7.62–8.05 s and turns at 7.80–8.75 s.
- **Coming, head low:** the score's head channel, plus an extra neck drop on the approach, keeps the skull under the back line.
- **Across the sill:** from 24.45 s the head attends to the person's low hand (turned about 80° to the left). On *come in*
  (26.4 s) it swings into the room and stretches forward, with the muzzle past the jamb. From behind, the camera sees the
  back of the head (measured: muzzle pointing away from the camera in 100% of frames from 26.6 to 28.2 s; muzzle reaches
  X = −0.31 m, inside the room, which starts at X = 0.20). Then the chin goes down on the paws and the dog stays.
- Ears, tail tuck and wag come from the score's acting channels. Signs were checked on renders after one error (ledger 11).

The person is a second skinned mesh (19 bones, faceless). Their keyed clips follow the score's circumstances: call, reach,
step aside, sit on the crate, low hand, and a small nod while speaking. The door opens inward from ajar (48°) to 102° at
6.2–7.0 s, and the room light rises with it. Its beam, and the dog's shadow in it, fall on the porch boards.

**Cameras:** A, the whole porch, from 0 to 14.9 s; a dolly to C, side-on for the approach, from 14.9 to 17.6 s; a dolly to
B, behind the dog at the sill so that looking in reads in depth, from 21.6 to 24.2 s. Because the camera moves, the trace
carries `x_world_measured`.

## LBS vs DQS (measured, `proof/skinning_metrics.json`, `proof/stress_twist.json`)

Same weights, skeleton and pose for every one of the 768 frames. The ring measure is the mean distance of a joint's blend-ring
vertices from the skinned bone chain, relative to the bind pose.

| joint (worst frame for LBS) | LBS | DQS |
|---|---|---|
| left hock, refusal lie 5.83 s | 0.71 | 0.90 |
| left elbow, 4.54 s | 0.75 | 0.88 |
| left stifle, 4.67 s | 0.78 | 0.88 |
| neck, look-back 7.92 s | 0.97 | 1.00 |
| smallest LBS blend determinant | 0.27 (hock, 5.83 s) | 1 by construction |
| **stress test: neck twisted 160° at one joint** | **0.64**, det down to 0.03 (candy wrapper) | **0.86** |

In the film's own motion the twist is spread over several neck joints, so LBS loses only about 3% at the neck. The bending
legs in the lies are where LBS fails in the film. The candy wrapper itself is shown in the stress test
(`proof/stress_test_twist.mp4`, `proof/stress_twist_160.png`): the neck is wound to 160° under a printed ring ornament, which
is the lineage's "tattoo held intact". DQS keeps girth but bulges slightly at extreme bends (ring up to 1.04). I judged that
acceptable, so no extra corrective shapes were added. Side-by-side clips of the film's look-back and lie-down under both
methods are in `proof/lbs_vs_dqs_stress.mp4`, with stills in `proof/lbs_vs_dqs_*.png`.

## Invariants (measured from the render's own G-buffer, `trace.json`)

`render.py` records, for each frame, the pixels the rasterizer actually covered with the dog's skin: the world position of
each pixel and a per-pixel "head-ness" interpolated from the head and neck bone weights. Onsets are taken from these
records, not from the score's labels:

| choice | score | measured | signal |
|---|---|---|---|
| retreat | 1.000 | 0.958 | body moves away / crouches by more than 1 cm |
| watch | 2.333 | 2.333 | head rises more than 2 cm from its retreat low |
| refuse | 3.417 | 3.417 | head pixels start to turn away (more than 3 px) |
| watch (turns to look) | 7.458 | 7.542 | head pixels start to come round |
| approach | 14.708 | 14.750 | body moves toward the door by more than 1.5 cm |
| lie down | 23.792 | 23.958 | back drops more than 2 cm below its walking low |
| looks in | 26.4 | 26.417 | head moves toward the room |

`check_handmade.py` reports **ALL OK** (I1–I4). Other measurements: 93% of refusal frames show the head turned away; the skull top (ears included) is below the back on 100% of approach frames (15.0–23.7 s, mean margin 9 cm); at the end, 30% of the visible dog is inside the door frame and 14% is inside the room, with the tail on the porch;
the smallest dog in any frame is 13,278 px. Sound (`build/cache/levels.json`): calls −20.9 dBFS RMS, soft voice −32.9
(12.0 dB quieter), room tone −48.9 (the soft voice is 16 dB above it). Claw touch-downs on the approach: 17.1 dB above room tone per event, 7.2 dB over the whole approach window.

## Repair round 1 (after the independent critic: narrow fail on the rise)

- **The rise, 7.85–8.30 s.** The look-back had asked for up to 158° of head yaw while the body still faced away, so the neck
  folded over the body into a knot. The body then yawed while rising with the neck upright, which read as a giraffe.
  The new route: the dog rises in profile first (lie 1→0 by 8.00 s), then the body yaws (7.98–8.85 s). The head's yaw
  relative to the body is capped at 115°, so it looks back over the near shoulder and never over the hip. The neck is
  carried forward during the turn, and the head tilt is halved. I checked 12 frames from 7.60 to 8.60 s extracted from
  `film.mp4`.
- **The approach.** An extra neck drop and ears laid back. The skull top, ears included, is below the back on 100% of
  frames from 15.0 to 23.7 s (mean margin 9 cm, measured).
- **Proportions.** The muzzle is 4.5 cm shorter (mesh and weights rebuilt). The dark saddle mask now ends at the withers,
  so there is no ridge along the neck.
- **In the film itself:** a 1.35 s inset at 23.95–25.30 s compares the hock folding in the lie-down, side-on, under linear
  blend (stained red where the blended matrix loses volume) and under dual quaternions (what the film uses).
- **Claws** are louder (see the levels above).

## What failed and what I changed

See `ledger.jsonl`. The main changes were diffuse weights and a top-4 crack (fixed by a local heat constant and limb
visibility); the archive warp, which was incoherent, became a quilted coat; the person's arm webbed to the torso (fixed with
separated sculpture and arm weights barred from the torso); a camera behind the dog made the head read above the back
(fixed with a side-on camera for the approach); "looking in" did not read as a change (fixed by attending to the person
first); the tail rose when it should tuck (a sign error).

## What I did not do, and what is weak

- No real fur, and no secondary motion: no skin jiggle or tail dynamics.
- The voice is a formant synthesizer, so the words are also given as subtitles.
- The skin self-intersects slightly where the folded hind legs meet the belly in the lie. No collision solve was added.
- The coat's side projection streaks a little along the spine and belly, where the projection is degenerate.
- The person is a plain mannequin. The yard and sky are simple.
- No independent critic has watched this. I looked at frames extracted from `film.mp4`; my reading is perceptual and unverified.
- Perceptual claims (it reads as a dog in every turn frame, the look-in reads in depth) are my judgement from stills. The
  numbers above are measured.

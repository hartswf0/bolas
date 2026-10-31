# SCION-36 · Bounded Biharmonic Weights — Auto-Rig Swarm · PAE-02 method

## Thesis
Reduce manual weight painting for **irregular archival silhouettes** while keeping influences localized, stable and
interpretable. The proof here: the dog of PAE-02 is not drawn, not cut into puppet pieces and not a maquette. It is
whole frames of a real dog from a 1930s-50s home movie (*Amateur Film New Jersey C*, public domain), each frame
used as **one mesh** with its own ragged SAM edge, motion blur and grain, rigged **automatically** from its shape and
deformed by **bounded biharmonic weights (BBW)**. Nothing about the weights is painted by hand: the only per-frame
input is one facing bit (head left or right).

## The swarm (roles merged where the coupling was tight; one builder ran them, so they are roles, not separate agents)
| role | artifact it made or checked |
|---|---|
| Geometry preprocessor | `build/autorig.py: load_mask, triangulate` — SAM polygon → raster → 2 px grid triangulation keeping only triangles whose centroid is inside the mask, largest component (so the mesh never bridges the gaps between legs) |
| Handle layout agent | `layout_handles` — medial axis (scikit-image), 4/8-safe skeleton graph, spur pruning, endpoints → feet, head, tail; spine path; leg paths; front/hind by where they join the spine |
| Weight optimizer | `bbw` — minimise ½wᵀ(L M⁻¹ L)w with cotangent L and lumped M, w=1 on its handle, 0 on the others, 0≤w≤1, primal active set per handle on the sparse system, then normalised |
| Concavity counterexample hunter | `rigs.py: leg_locality, shepard_weights` — the same handles with shape-blind inverse-distance weights as the counterexample; leak measured across the leg gaps |
| Rig QA | `proof/tests.json`, heat maps `proof/heat_*.png` |
| Independent deform critic | **not run here** — the brief assigns an independent critic after delivery. I do not approve my own work. |

## Native formal language, as used
* **Polygon/mesh**: one triangle mesh per archive frame (1,100–2,300 vertices).
* **Mixed handle types**: POINT handles (nose, tail tip), BONE handles (neck, back, tail, each leg). **Cages were not
  used**: on these silhouettes the bones carried every gesture the score asks for; a cage handle was not needed and I did
  not build one.
* **Constrained biharmonic optimisation**: per handle, bounds active-set, then partition of unity.
* **Weight heat maps**: `proof/heat_*.png`, also on the end card (the exact weights the film is skinned with).
* **Runtime skinning**: `build/skin.py` — linear blend of one 2×3 affine per handle, then a vectorised textured
  rasteriser that maps the archive pixels and their own alpha onto the deformed mesh, depth-sorted (legs behind the body
  standing; forepaws in front lying).
* Typed state: `pose.py` turns a handful of numbers (neck angle, fold, crouch, swing per leg, tail, push) into handle
  affines; `render.py: placement` maps source pixels to the screen (scale by depth, shear along the porch, foreshortening).
* Time base: the score's 24 fps frame index; one score frame = one film frame.

## How the dog is built and moved
* **Views (whole frames)**: f010 (profile to the left, head up) carries watching, retreat, approach, lying across the
  sill, looking in. The same frame **mirrored** carries the turned back (refusal, lying with chin down). The two turns go
  through the archive's **own** turning frames f019 → f026 → f030 → f036 → f040 (the found dog really turns from left
  through facing the camera to right in those frames), each auto-rigged the same way; reversed and lying for the turn back
  at 7.46 s. No cross-dissolve anywhere: a frame is replaced by the next frame of the same archive motion.
* **Movement**: the BBW-skinned mesh does the acting: the neck bone lowers the head (below the back on the approach),
  legs swing on the score's walk phase, the body sinks and the legs fold (forelegs forward, hind legs tucked) to lie, the
  tail tucks, the muzzle pushes level through the doorway to look in. The dog slides along the score's x through a
  pinhole camera; it sits on a contact shadow.
* **Turn back to look (7.46 s)**: lying, hips down, the dog comes round through the reversed turn frames and is facing
  the door, still lying, by 7.71 s; it rises only from 7.8 s.

## The person, the place, the sound
* Person: one frame of *Straight Talk* (NTIS 1992, public domain), a woman seen from behind, cut by colour and rigged
  with the same BBW code (head point, chest bone, hip bone, arm bone); a silhouette against the room's light behind a
  half door. She leans and reaches (arm bone), steps aside and sits (lowered; her legs are out of the found frame and stay
  hidden), and offers a hand low.
* Place: a porch at dusk computed from a pinhole camera: clapboard wall, half door (the lower leaf swings in at 6.2 s and
  the light pool comes out), window, porch boards. The camera closes in on the sill from 21.5 s to 25 s.
* Sound (`sound.py`, no samples): room tone, crickets, projector whir; formant murmurs with the shape of the words
  (no words), calls pressed and loud, the soft voice breathy and ≥ 6 dB lower; paws on the walk phase, latch, creak, hum.

## Numeric invariants (measured, `proof/tests.json`)
RESULTS_PLACEHOLDER

## What failed and what I changed
LEDGER_PLACEHOLDER

## What I did not do / what is unknown
* No cage handles. No independent critic run by me. No real lying dog exists in the materials: lying is made by the
  BBW deformation of the standing profile (sinking body, forelegs forward, hind legs folded).
* The person's legs are not in the found frame; she is cropped by the half door, then by shadow.
* Back-of-head view: the archive has none usable at the sill; looking in is the muzzle pushed level into the lit room.
* Front/hind leg labels are automatic and sometimes wrong on the blurred frontal turn frames; there they only shorten.

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
  through the archive's **own** turning frames f026 → f030 → f036 → f040 (the found dog really turns from left
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
All measured by `build/rigs.py` on the meshes the film is skinned with.
| frame | vertices | BBW solve | bounds | partition of unity (max err) | sum before normalising | mean leak across leg gaps, BBW / shape-blind baseline | max leak, BBW / baseline |
|---|---|---|---|---|---|---|---|
| f010 (W, and mirrored) | 2245 | 0.62 s | [0, 1] | 3e-16 | 0.995–1.193 | 0.0020 / 0.0062 | 0.198 / 0.176 |
| f026 | 1350 | 0.36 s | [0, 1] | 2e-16 | 0.999–1.130 | 0.0041 / 0.0124 | 0.089 / 0.086 |
| f030 | 1162 | 0.29 s | [0, 1] | 2e-16 | 0.979–1.204 | 0.0000 / 0.0082 | 0.000 / 0.047 |
| f036 | 1311 | 0.27 s | [0, 1] | 2e-16 | 0.999–1.131 | 0.0042 / 0.0111 | 0.140 / 0.077 |
| f040 | 1778 | 0.45 s | [0, 1] | 2e-16 | 0.999–1.061 | 0.0078 / 0.0120 | 0.162 / 0.111 |
| f046 (test only) | — | — | [0, 1] | — | — | 0.0106 / 0.0184 | 0.317 / 0.242 |
| f044 (test only) | — | — | [0, 1] | — | — | 0.0005 / 0.0023 | 0.014 / 0.013 |

* **Bounds and partition of unity**: hold exactly on every view (bounded active set, then normalisation). Before
  normalisation the per-handle solves already sum to 0.98–1.20.
* **Locality across the gaps between legs** (lower 60 % of each leg, vertices more than 8 px from the other leg):
  the MEAN leak is 2–10× lower than the shape-blind inverse-distance baseline on every frame. The MAX leak is **not**
  lower: on the blurred frames a few vertices near where two legs join the body carry 0.1–0.3 of the other leg. Honest
  result: BBW keeps the leg gaps clean on average, but the found silhouettes' merged leg tops still leak locally.
* **Stability across silhouettes**: neighbouring archive frames f008, f009, f011 rigged by the same code and mapped onto
  f010 by an affine fit of their automatic joints: mean |Δw| 0.049, 0.028, 0.036 (95th percentile 0.34, 0.20, 0.21).
  Across all 10 rigged dog frames, the weight spread of each named handle (RMS radius / body height) varies little:
  head 0.106 ± 0.021, neck 0.178 ± 0.041, back 0.189 ± 0.048, front leg 0.190 ± 0.031, hind leg 0.168 ± 0.029.
  Weight MASS varies more (back 0.20 ± 0.12) because the number of legs found differs per frame (2–4).
* Runtime: one frame of LBS + rasterisation of the dog is ~0.1 s in numpy; the scene renders 768 frames in ~6 min on 4 cores.
* Person (Straight Talk f000): 2911 vertices, 4 handles, bounds [0, 1], partition error 2e-16.

**Measured onsets** (from the render's own geometry, `trace.json: onsets_measured`): retreat 1.125 s (+0.125),
watch 2.292 s (−0.041), refuse 3.417 s (0.000, the flinch: head drops >8 %), turn back to look 7.625 s (+0.167, head on
the door side of the tail while lying), approach 14.750 s (+0.042), lie down 23.833 s (+0.041), look in 26.417 s
(+0.017). `check_handmade.py`: ALL OK (I3 r = 0.997 on x_world_measured, refusal share turned 0.94).
**Sound** measured from the encoded film (mono RMS): calls −10.3 / −9.3 dB, soft voice −22.8 / −22.9 / −22.5 dB
(≥ 12 dB under the calls), room tone −34.5 dB. The first call starts at 0.92 s, before the retreat (1.125 s); the soft
voice starts at 7.40 s before the turn back, and "come in" at 26.30 s before the look in.

## What failed and what I changed
See `ledger.jsonl` for every attempt. In short:
* Skeleton pruning ate the legs (8-connected staircase corners read as branch points) → graph links diagonals only when no
  4-neighbour links them; pruning in two passes only.
* Leg-leak metric first counted vertices where two found legs overlap → measured only across real gaps (> 8 px).
* View A (f046, head in the bowl) skinned into a shapeless lying blob → the refusal uses f010 mirrored; f046/f044 kept
  only as test silhouettes.
* Turn frame f019 read as a double image (two heads, motion blur) → removed; the turn uses f026–f040.
* First camera: the lying dog sheared steeply and read as climbing → path made diagonal near the door, shear clipped and
  halved while lying, a visible sill board added, the camera closes in on the sill.
* The rest pose folded the head under the chest (neck 2.1 rad) → lying neck capped at 1.05 rad.
* Hind leg hung down while lying → folds 1.45 rad forward and compresses.
* Person mask kept the door edge as a "head" and later lost the head → cut the edge, close the thin neck.
* The person sat in front of the dog's muzzle → moved left; the dog's lying spot moved right so the muzzle is over the
  lit floor.

## What I did not do / what is unknown
* No cage handles. No independent critic run by me. No real lying dog exists in the materials: lying is made by the
  BBW deformation of the standing profile (sinking body, forelegs forward, hind legs folded).
* The person's legs are not in the found frame; she is cropped by the half door, then by shadow.
* Back-of-head view: the archive has none usable at the sill; looking in is the muzzle pushed level over the sill
  into the lit room (a ~34 source-px push of the neck and head handles). It is a modest movement; a critic may find it small.
* The turn frames are the archive's own motion but each lasts 1–2 film frames; the lying turn back (7.40–7.60 s) goes
  through four small curled frontal frames and is fast. Frontal frames read smaller than the profile.
* The person is a back view used as a silhouette; her "hand offered low" is the arm bone swung down to the floor, a dark
  wedge, not a drawn hand.
* No independent critic verdict exists yet; I have only looked at my own frames (extracted from the encoded film).
* Front/hind leg labels are automatic and sometimes wrong on the blurred frontal turn frames; there they only shorten.

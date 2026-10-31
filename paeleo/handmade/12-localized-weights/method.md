# PAE-02 · SCION 12 · Alec Jacobson — Localized Deformation Weights

**Swarm.** SCION 12, after the bounded biharmonic weights of Jacobson, Baran, Popović and Sorkine (2011). This is a new
operation inspired by that work; it is not a claim that its authors made or endorsed it.

**Theorem the film tries to prove.** A 2D puppet with a deliberately concave, pierced shape can be moved by a handful of
mixed handles (points, bones, a cage) with weights computed automatically, and the weights stay local: a leg moves without
dragging the leg a finger away, and the lace holes do not tear.

## Native formal language, as used

| primitive | here |
|---|---|
| character mesh | one red cut-paper dog in profile (`build/dog.py`): unions of tapered strokes and a Catmull-Rom torso, pierced with **30 lace holes**, each at least about 2 cm across its narrow side so they read at the wide shot (two six-petal rosettes, a medallion with four drops, four back piercings, three belly crescents, eye, ear slits, chest and thigh drops). Near and far legs sit 10–25 mm apart; the two ears share a base. Triangulated with constrained Delaunay (the `triangle` library) with every handle as a PSLG constraint: **5,512 vertices, 9,924 triangles**. |
| point / bone / cage handles | **12 bones** (neck, head, upper and lower segment of each of four legs, two tail segments), **2 points** (ear tips), and a **6-vertex torso cage** whose edges run through the mesh interior (weights linear along cage edges, as in the paper). |
| bounded weights | for each handle j: minimise ½ wⱼᵀ (L M⁻¹ L) wⱼ (cotangent Laplacian L, lumped mass M), wⱼ = 1 on handle j and 0 on the others, 0 ≤ wⱼ ≤ 1; solved as a box-constrained QP by a primal-dual active-set method I wrote in `build/bbw.py` (scipy sparse LU per active set); then normalised to a partition of unity. |
| sparsity and smoothness | the lower bound is active on most of the mesh: 85 % of all weights are exactly 0; on average 2.4 handles per vertex carry more than 0.01. |
| rest-pose shape controls | each handle carries a full affine; the posed affines come from the score's acting state (`build/rig.py`), then linear blend skinning. |

The person is the swarm prompt's second proof subject, "a coat-wearing human": ink-blue paper, the same solver, 8 bones,
a point for the hair knot and a 4-vertex cage for the coat skirt that bends over the thighs when they sit (4,959 vertices).

## Numerical invariants (measured, `proof/weights_tests.json`)

* bounds: min 0.000, max 1.000; partition of unity: max |Σw − 1| = 3e-16 (the raw sums before normalising ranged 0.84–2.02,
  as the paper also reports for unnormalised BBW).
* every active-set solve converged (≤ 26 iterations); solve incl. triangulation ≈ 8 s on this shared CPU; posing + skinning
  ≈ 3.4 ms per frame (offline solve, runtime skinning separated, as the swarm's inquiry asks).
* **locality across the gap**: the largest weight a lower-leg bone has on the neighbouring leg's shin and paw is **0.000**
  for all four pairs; naive inverse-distance (Shepard, power 2) weights give 0.12–0.21.
* **lift test**: rotate the near foreleg 50° at the shoulder (and 95° at the wrist), all other handles still: the far
  foreleg moves **0 mm** with BBW; with the naive weights it is dragged up to **56 mm** and 86 triangles fold. Both results are
  drawn on the end card from the same mesh.
* folding through the performance: in frames where the whole dog faces one way, at most 231 of 9,924 triangles (2.3 %)
  fold, at the hip and neck joints in the deepest bends (lying, chin on paws). They are inside the silhouette (one sheet, one
  colour), so they do not show, but they exist; LBS with bone weights folds at sharp joint bends, and I did not add a
  dual-quaternion or ARAP correction.

## How the dog moves (operation)

* **Walking**: feet are planted. The gait phase comes from the distance the dog actually travels in the score (stride
  0.5 m, stance 60 %), so stance paws stay fixed on the boards while the body moves; two-bone IK places each leg.
* **Head low on the approach**: the neck rotates down so the top of the head is below the back. Measured from the deformed
  mesh: head top below the withers in 97 % (skull top more than 5 cm below the withers; the remaining frames are the 0.45 s ease-in at 14.7 s) of approach frames.
* **Turns are a yaw ripple through the handle groups.** A flat profile turned as one card goes edge-on (it did, ledger 4).
  Instead each handle group yaws through 180° in 0.34 s, head first, then shoulders and hips together (onsets 3.42 / 3.54 s
  and, for the turn back, head 7.36 s, body 8.00 s; see the repair round below). Limbs have depth: near legs and ear at +z, far ones at −z,
  so mid-turn the projection puts two forelegs (two hind legs, two ears) side by side, as a dog seen head-on. While the groups
  face different ways the dog is drawn as paper layers in depth order, each with its own cut edge and shadow. The tail never
  goes below half width (a paper tail edge-on is a stick); it flicks across.
* **Turning back to look (7.458)**: the head group comes round first, raised over the shoulder and level, muzzle toward the
  door, while the body is still lying facing away; the body gets up and follows at 8.0 s.
* **Lying across the sill** (23.8 s): legs fold by blending each bone's angle from the standing IK pose to a sphinx pose
  (forearms forward, hocks back); the torso drops 0.235 m. The dog's torso centre is drawn at score x − 0.12 m, so lying at
  x = 0.59 its forelegs and head are past the wall's outer face (x = 0.30) and its muzzle reaches into the lit room; tail and
  hindquarters stay on the porch.
* **Looking in** (26.4): the neck reaches forward and level (the score's head > 1 becomes reach, not rise), the ears prick,
  and the head yaws 62° away from the camera into the depth of the room (the ears part, the muzzle foreshortens); the muzzle moves further into the room (measured: muzzle world x -0.13 m at 26.3 s → -0.16 m at 27.5 s; the wall's inner face is at 0.00). No lift toward the light or the person.

## Repair round 1 (after the critic's DOES NOT PASS)

* **Turns (3.5–3.9 s, 8.0–8.35 s):** each handle's *shape* (its affine's linear part) no longer narrows below a floor of its
  width: torso cage 42 %, legs 85 %, head 50 %, tail 50 %; at 90° it flips sides instead. The torso and the leg pairs are
  nearly mirror-symmetric, so the flip does not show; the head, neck and tail keep their true continuous positions, and the
  head leads by 0.12 s (shoulders and hips now turn together). Checked frame by frame on film.mp4: every frame has a head and
  legs about 6 px or more wide at the wide shot.
* **Looking in (26.4–26.9):** the head stays low (no lift toward the hand); it reaches forward and yaws 62° away from the
  camera, so the muzzle foreshortens into the doorway and the two ears part.
* **Muzzle:** redrawn shorter and deeper with a nose; the weights were re-solved automatically.
* **Lace:** 30 bolder holes instead of 34 small ones; the end card's count comes from the mesh.
* **Sound:** voices get a 0.16 s release and a short room reverb; the second call no longer stops dead.

## Repair round 2 (critic: PASS, narrowly)

* First turn: the head now comes round in 0.22 s, so at 3.62–3.67 it is in profile, with muzzle and eye, on the top layer
  while the body folds.
* Looking in: the head yaws 70° away from the camera, and the paper behind the eye hole closes as it turns (the eye goes out
  of sight). What faces the viewer is the back of the head and the two ears; the head stays level and low.
* Lying (4.6–7.4, 28.5–32): chin on the paws with the nose tipped down 22° and the neck bent less, so the neck and head no
  longer line up into one long snout; ears stay at least two-thirds up while lying.
* assets.json now says 30 holes, matching the cards and the mesh.

## The place

A dollhouse section through the doorway, all cut paper drawn in code (`build/world.py`): the room with lace wallpaper whose
holes show the lamp-lit layer behind, the door leaf (seen in section it opens into a panel against the room), the wall cut
hatched with pierced slots, the sill, the porch with a lattice skirt, scalloped fascia, roof with gingerbread trim, the steps
at 4.9 m, and dusk (stars, a pierced moon, two layers of hills and trees). Because the section is a side view, "across the
sill" is horizontal on screen: the threshold axis of the house *is* the screen's x. The camera holds wide until the
approach, then closes on the door (its moves are recorded; `x_world_measured` in the trace maps the rendered dog back
through the camera).

## Sound

All synthesized (`build/sound.py`): a source-filter formant voice (sawtooth glottal source, three time-varying formant
resonators, phonemes typed by hand) for "Come here." ×2, "It's all right." ×2 and "Come in."; it is intelligible only
roughly, so the words also appear as cream paper captions beside the person (speech, not labels: the dog's state is never
printed). Voices start 40 ms before the score's voice onset. Paper ticks on every paw plant (same gait as the picture),
rustles on each turn and when it lies down, door latch and creak, stool creak, crickets, low air, a warm pad when the light
comes out. Measured in the encoded film: RMS over 0.9 s from each line's onset, from the audio of film.mp4: calls about −16.6 dBFS; soft lines about −28 to −30 dBFS (11 dB or more under the calls); dusk air between lines about −55 dBFS.

## Measured choice onsets (from the render, `trace.json` → `onsets_measured`)

* retreat (backs away), score 1.000 → **1.083 s**
* watch (head comes up, ears prick), score 2.333 → **2.333 s**
* refuse (head starts to turn away), score 3.417 → **3.417 s**
* watch (head comes round to the door), score 7.458 → **7.458 s**
* approach (comes closer), score 14.708 → **14.667 s**
* lie_down (back lowers at the sill), score 23.792 → **23.833 s**
* looks in (muzzle moves into the room), score 26.4 → **26.375 s**

All seven are within ±0.25 s of the score; `check_handmade.py` reports ALL OK (I1–I4).

## What failed and what I changed

See `ledger.jsonl`. In short: a 38k-vertex mesh from unresampled union rings; bones crossing lace holes; a naive active set
that did not converge; paws that touched and leaked weight; a whole-body turn that went edge-on; a ripple turn that folded
into a lump (fixed with depth layers, limb depth, a flicking tail); a smiling moon; a hidden reaching arm.

## What is still weak (my own view; an independent critic judges)

* Mid-turn frames (about 3.62–3.72 s, 8.12–8.18 s) are still compact: the head folds over the chest for two or three
  frames, and the shape flip at 90° is a small one-frame change, near-invisible because torso and leg pairs are near-symmetric.
* The voice is a crude formant synthesizer; the captions carry the words.
* Some triangles fold at hip and neck in deep bends (invisible in one colour, but present).
* "Across the sill in depth" is solved as a section view, not as a 3/4 view into depth.

## What I did not do

No kit footage, archive frames, Quick, Draw! drawings or web images; no recorded sound; no 3D maquette. No independent
critic was run by me; no human viewing is claimed. I did not implement dual-quaternion skinning, ARAP refinement or the
paper's cage-based variant for the whole shape, nor an interactive editor; the "mobile operator page" of the prompt was not
made (the film, the heat maps and the tests are the deliverable here).

# SCION 42 · Neural Layered Puppet (Few-Shot Structure Swarm) · PAE-02 threshold

**Thesis.** A few frames of a real dog should be enough to find *which parts it has and where they hinge*, without
anyone drawing the cuts. The film shows that found structure honestly (seams and pins on the dog, the layer map on the
title card) and shows where it runs out: wherever the examples had nothing, the pose is a hand-set override on the
learned hinges, and the turns are not the puppet at all but archive frames of the dog turning.

## Native formal language, as built
- **Example frames**: *Amateur Film New Jersey C* (public domain), kit frames. Training: 8, 2, 5, 11, 13 (left profile,
  head up) and 42, 44 mirrored (head low). Held out: 3, 7, 10, 12, 43m, 45m.
- **Layered mesh**: the stride-2 points inside the SAM mask of template frame 8 (1991 points). Each carries layer
  weights; each layer has one affine per frame; a point moves by the weighted blend (linear blend of layer motions).
- **Differentiable rendering / consistency losses** (numpy, hand-written gradients, Adam; `build/fit.py`): squared
  distance transform of the target mask at each warped point, coverage of every target pixel, normalised grey-value
  match, a non-conformality penalty per layer, and a hinge-consistency loss (two adjacent layers must carry their shared
  border to the same place).
- **Structure discovery**: (1) one global affine per frame; (2) 18 k-means patches each fitted with its own motion; (3)
  greedy merging of adjacent patches by the least-squares cost of sharing one affine (hierarchy in
  `proof/merge_hierarchy.jpg`: K=3 already splits the fore leg off, K=4 the head); (4) EM over crisp layers: M-step fits
  motions, E-step re-labels points by how well each layer's motion explains them over all frames, with a Potts prior
  (ICM, labels may only spread from neighbours). Hinges = the point on each shared border with the least rms
  disagreement across frames; the tree = minimum spanning tree of those, rooted at the largest layer.
- **Latent pose**: per-layer affines relative to the root layer; library re-fitted to source frames 0-13 and 40-46
  (masks frozen, `build/library.py`); the walk is looped where the learned pose comes back closest to itself (frames 0-8).
- **Visibility states**: profile-L (puppet), profile-R (same puppet mirrored: the source's right-facing frames were in
  training), view (whole archive frame), look-back (head and neck layers mirrored about their learned hinge).

## What was learned, and how well (measured)
- 8 layers: head+throat, neck/crown, shoulder, fore leg, trunk (root), back, rump/tail, hind legs. Hinges at neck,
  shoulder, elbow, hip, tail; rms disagreement 2.4-4.8 px at template scale (`data/fit_report.json`).
- Held-out silhouette IoU (masks frozen, motions fitted on 6 unseen frames): **learned 0.758, hand-cut 8-part rig from
  the kit keypoints 0.767, one rigid cut 0.715**. The learned split is no better than an authored split on
  silhouettes; it finds a comparable split without being told. Variants (β 2/4, hinge weight 0.01-0.05, K 8/10):
  0.754-0.772 (`data/model_selection.json`).
- Rejected: soft layers scored 0.831 but were not layers (mean max weight 0.20, layer affines rotating 40° and
  scaling 0.5, "hinges" 40-75 px apart). K=8 was chosen by held-out IoU in that earlier soft sweep (plateau from K=8);
  the crisp K sweep was not completed.
- Library re-fit IoU 0.66-0.995 for walk_up; walk_low (3/4 view, head in a bowl) comes out frog-like relative to the
  trunk and is used only for its head/neck local motion.
- Confidence map: `proof/confidence.png` (per-point photometric residual, hinge rms rings).

## How the dog moves
Learned: layers, hinges, body motion of the walk (source poses looped), the slight head-low. Override (hand-set
rotations about learned hinges; pale pins on screen; 74% of scene frames carry some override): leg swing keyed to the
score's walk phase (stance sweep sized to the 0.55 m stride), head carried low (−48°/−18° on neck/head), lying (fore leg
forward, hind leg folded, trunk lowered), chin down, the look in (head and neck carried forward into the room).
Turns (3.42-3.88 s and 7.88-8.34 s): archive frames 15, 16, 17, 31, 38, 40, 41 shown whole in sequence (front of the
dog toward the camera, then round). At 7.458 the lying dog's head and neck are drawn mirrored over its turned back
(look-back), it rises, then the turn-back views.

## Invariants (measured from the render, `trace.json` summary)
Onsets: retreat 1.042 (+0.04), watch 2.375 (+0.04), refuse 3.417 (0), watch 7.458 (0), approach 14.708 (0), lie down
23.792 (0), look in 26.292 (−0.11). Checker: ALL OK. Head under the back line for the whole approach: 9.6-14 px (median
12.2). Ends at x = 0.59, alpha bbox x 328-548 across the door reveal (screen x 400-490): head inside, rump outside.
Feet during the approach: 36% of foot-frames planted, median foot/body speed 0.72 (partial sliding remains).
Sound: calls −20.6/−17.1 dBFS rms, soft lines −32 to −35 (≥ 11.6 dB quieter), room tone −54.8.

## What is weak / not done
- The dog's surface is a lumpy grey archive texture; at film scale it reads as a dog mainly by outline and gait.
- The look-back (7.46-7.88) is crude: a mirrored head over the back, with a visible seam.
- Turn views are a different, smoother texture and scale-matched by eye-rule (area/height), not by the model.
- Feet still slide part of the time; the far fore leg does not exist in the template (one fore leg in profile).
- "Looking in" reads as reaching forward into the lit room; the head is never seen from behind (no such view in the source).
- No rear-view, lying, or turning examples exist in the source: those are not learned, and are labelled as such.
- Not done: rig-only control *film* (only the numeric comparison), operator page, independent critic run, crisp-layer K sweep.
- Judged by looking at sampled frames only (contact sheets), not by watching at normal speed.

Rebuild: `build/make.sh` (`--sweep` also re-runs the slow model-selection sweep).

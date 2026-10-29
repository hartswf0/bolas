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

## Round 2: where the learned model beats hand-setting (measured)
- `build/turn_fit.py`: the learned layers and the hand-cut rig fitted (masks frozen) to 16 archive turning frames
  (14-21, 26-33): IoU 0.752 vs 0.752 - the learned *split* does not beat a hand-cut split.
- Re-training the layers with turning frames added (`PUPPET_VIEWS=1`) did not help (turning frames held out: 0.759 vs
  0.767; reverted, `data/fit_report_views_experiment.json`).
- `build/hinge_control.py`: learned per-layer *motion* vs the best possible hand-set pose on the same learned hinges
  (similarity + one rotation per hinge, optimised per frame): **IoU 0.752 vs 0.697, learned better on 13 of 16 frames,
  photometric residual 0.92 vs 1.02** (`data/learned_vs_handset.json`). This is the measured win, and it is what the
  turns now use. Caveat: the learned motion has more degrees of freedom (an affine per layer).

## How the dog moves (round 3)
Every frame of the dog is the puppet: seamed and pinned throughout, no archive footage on screen.
- **Turns are learned motion.** Both turns pose the puppet at its learned fits of the archive turning frames
  (`turn_fit.py`; the poses that beat the best hand-set hinge pose on 13 of 16 frames). Turn away (3.417-3.97): profile
  → fits of frames 15, 16, 17, 30 → the front-on fit 30 mirrored about the dog's centre line (where the body changes
  side) → fits of 40 and 41 (mirrored source) → profile with the back to the door. Turn back (8.0-8.55): head already
  round → mirrored fit 30 → fits 30, 17, 16, 15 → profile. Each fit is placed by its own fitted silhouette at the
  puppet's height; the largest frame-to-frame height change inside the turn windows is under 10%.
- **Look back (7.458-7.82).** The head proper (head layer above its learned hinge with the neck) pivots on that hinge,
  the arc kept at shoulder height, mirrored as it passes vertical; the throat stays with the body. The muzzle tip (the
  template's nose point) is left of the hinge, toward the door, from 7.625 s, and stays there while the dog rises
  (7.56-8.0) and into the turn back.
- **Look in (26.4-27.4).** The head lifts off the paws and the muzzle is brought level (head −38° on its hinge),
  pointing left into the lit room; head centre reaches x = 345 px, the jamb is at 376.5 px.
- **Head carried low** eases in over 3 frames after each change of intention (1.0 s, 14.708 s).
- Override (hand-set rotations on learned hinges; pale pins): leg swing, head low, lying, chin down, look back, look in.
  Learned: layers, hinges, walk body motion, both turns. The tail is cut from archive frame 6 and pinned to the rump layer.
- Section 7: the learned *split* only ties the hand-cut split, so it is kept for its structure and said so on the cards;
  the learned *motion* beats hand-setting, so it carries the turns. The end card shows learned and best hand-set poses
  side by side on five archive turning frames with the real outline drawn over each.

## Invariants (measured from the render, `trace.json` summary)
Onsets: retreat 1.083 (+0.08), watch 2.375 (+0.04), refuse 3.417 (0), watch 7.458 (0; muzzle toward the door from
7.625), approach 14.708 (0), lie down 23.792 (0), look in 26.25 (−0.15). Checker: ALL OK. Head below the back line on
99% of approach frames (median 26 px; the first frames ease in). Ends at x = 0.59, bbox x 302-582 across the reveal
(376.5-462), tail x 504-582 on the porch. Feet: 33% planted, median foot/body speed 0.82. Camera: static, 1 m = 190 px,
threshold at screen x 310.

## What is weak / not done
- The turn poses are a profile texture carried onto 3/4 and front silhouettes: they read as a dog turning in outline, the
  surface stays a side view; the front-on mirror at frame 30 is a one-frame change of side.
- The look back is a small dark head turned over the shoulder at this scale; legible on single frames only up close.
- Feet still slide part of the time; the template has one fore leg; texture is lumpy grey.
- The learned split ties the hand-cut split; only the learned motion beats hand-setting.
- Not done: rig-only control film, operator page, crisp-layer K sweep. Judged from sampled frames of the encoded film.

Rebuild: `build/make.sh` (`--sweep` also re-runs the slow model-selection sweep).

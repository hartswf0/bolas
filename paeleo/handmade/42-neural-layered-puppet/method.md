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

## How the dog moves (round 4)
**Plainly: the acting is rig-driven.** Backing off, the turned back, the approach, lying, the look back and the look in
are hand-set rotations or shifts on the learned hinges, timed by the score. The learned model gives the parts and hinges,
the walk's body motion, and the two turns (the cards say this).
- **Turns** (3.417-3.97, 8.0-8.55): the puppet at its learned fits of archive turning frames 15, 16, 17 (which beat the
  best hand-set hinge pose, 13 of 16 frames), placed by their own silhouettes at the puppet's height; the body changes
  side at fit 17, mirrored about the dog's centre line. The front-on fits (30) were dropped: they read as a two-humped
  tangle. Single back line on every frame.
- **Look back** (7.458-7.68): the head proper narrows toward the camera on its learned hinge, then is replaced by a head
  turned round, cut from archive frame 39 (3/4 view: muzzle, eye, collar), mirrored so the nose points to the door, pinned
  at the hinge; held while the dog rises and until 8.09. Measured: nose left of the hinge from 7.583.
- **Look in** (26.4 to the end): the lit inner doorway of the room is now beside the jamb (screen x 238-352), the seated
  person beyond it at x 72; the head lifts, the muzzle comes level and is carried 12 template px into the doorway: the
  muzzle tip sits inside the lit rectangle and stays there to 31 s.
- **Legible head**: the head layer's contrast is lifted and its outer edge drawn as a thin pale rim; seams and pins are
  fainter and smaller but visible.
- Tail: cut from archive frame 6, pinned to the learned rump layer.

## Invariants (measured from the render, `trace.json` summary)
Onsets: retreat 1.083 (+0.08), watch 2.375 (+0.04), refuse 3.417 (0), watch 7.458 (0; nose toward the door from
7.583), approach 14.708 (0), lie down 23.792 (0), look in 26.25 (−0.15). Checker: ALL OK. Head below the back line on
99% of approach frames (median 26 px; the first frames ease in). Ends at x = 0.59, bbox x 302-582 across the reveal
(376.5-462), tail x 504-582 on the porch. Feet: 33% planted, median foot/body speed 0.82. Camera: static, 1 m = 190 px,
threshold at screen x 310.

## What is weak / not done
- The turn poses are a profile texture carried onto 3/4 and front silhouettes: they read as a dog turning in outline, the
  surface stays a side view; the front-on mirror at frame 30 is a one-frame change of side.
- The look back borrows a head from archive frame 39 (a cut piece, not the learned layers); its join to the neck is soft
  but visible up close.
- Feet still slide part of the time; the template has one fore leg; texture is lumpy grey.
- The learned split ties the hand-cut split; only the learned motion beats hand-setting.
- Not done: rig-only control film, operator page, crisp-layer K sweep. Judged from frames extracted from the encoded film, not normal-speed viewing.

Rebuild: `build/make.sh` (`--sweep` also re-runs the slow model-selection sweep).

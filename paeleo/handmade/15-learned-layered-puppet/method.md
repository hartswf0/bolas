# SCION 15 · Learned Layered Puppet — PAE-02, the threshold

*After Poursaeed, Kim, Shechtman, Saito, Belongie, "Neural Puppet: Generative Layered Cartoon Characters" (2019). An interpretation, not a claim of their method or endorsement.*

## Thesis

The archive gives us 50 frames (4 s) of one real dog walking toward a person, turning once through its front and lowering its head to a bowl. The scene needs a dog that backs away, turns its back, lies down, looks back over its shoulder, comes head low, lies across a sill and looks into a room. **Almost none of that is in the archive.** The swarm's question: what does a layered puppet *learned* from those 50 frames generate when the score asks for poses it never saw, and where does it fail? The film shows the generated poses (corrected where the model fails); the failures themselves are shown on the end card and in `proof/raw_vs_corrected.jpg`.

## Native formal language → artifacts

| primitive | where it is |
|---|---|
| 2.5D layered mesh template | `build/puppet.py`, `build/template.py`: 11 layers (torso, head, tail, 4 legs × upper/lower) cut from archive frame f006 by bone-Voronoi over its SAM mask; hand-authored skeleton; fixed layer order (far legs behind the torso, near legs and head in front); each leg column carries a lateral depth so the legs part when the dog faces the camera (`dogmodel.LAT`). |
| sparse example drawings | the 50 archive frames (+ 25 frames of agent keypoints); 37 used for learning after rejecting 19–25 (mask swallows the shadow, judged by eye on `proof/fits_sheet.jpg`), 23 and 49 (mask area). |
| correspondence | per-frame fitted transforms template→frame for every layer (`proof/fits.json`), used to back-project each frame's pixels into template space. |
| differentiable render loss | soft-alpha union of the warped layers vs the SAM mask at three blur levels + keypoints + priors + temporal prior; `scipy.optimize.least_squares` with **finite-difference** gradients (no autodiff; PyTorch not installed). 26 parameters per frame. |
| visibility layers | occlusion by the layers above is computed per frame in back-projection; far legs fade toward the front view; at the 90° view the two mirror solutions swap (a 4°-wide crossfade). |
| uncertainty estimates | per-texel confidence of each learned atlas (support of the view kernel); per-frame OOD score = Mahalanobis distance of the generated joint rotations under the learned Gaussian × view support. It is written to `trace.json` (`ood`, `mahal`, `view_support`) and sonified as a faint detuned tone (−37 dBFS peak). |

**What is learned** (`build/learn.py`, numbers in `proof/eval.json`, `proof/model.json`):
- a view latent ψ (0 profile … 90 facing camera) per frame from the fitted torso foreshortening under an ellipse prior (width/length 0.38, stated assumption); head view ψ_h the same way. Left/right mirror symmetry of the dog is assumed.
- Nadaraya–Watson regression on ψ of head tilt, head height, tail length, fore/hind leg length (e.g. the archive teaches that in front views the head layer sits tilted ~0.5 rad down and squashed to ~0.55 height).
- per-layer, view-conditioned texture atlases (7 bins, 0–90°), kernel-weighted back-projection with shrinkage toward the f006 texture where support is low (`proof/learned_atlas.jpg`, blue = low confidence: the tail almost everywhere).
- a Gaussian prior over 10 joint rotations. PCA of fitted poses: PC1 holds 34 % of variance and correlates r = 0.67 with the view latent (the archive's main variation is the turn).

## Measured: how well it learned

- Fit IoU (rendered silhouette vs SAM mask, at 96×72) mean **0.73** over 50 frames; profile 0.74, turning 0.68, front 0.80; worst 0.33 (frame 23, bad mask). First fit attempt at 192×144 reached 0.82–0.92 on profile frames but was too slow on the shared machine and was killed (ledger 2).
- **Held-out appearance** (each frame reconstructed with an atlas built without frames i±2), mean abs. grey error: learned **0.098** vs single-drawing rig (f006 texture on the same fitted pose) **0.107** vs drawing swap (nearest-view other frame cut out and box-aligned) **0.098**. With a softer kernel (w²) the learned atlas reached 0.093. So: the learned appearance beats the one-drawing rig everywhere (profile 0.084 vs 0.091, turning 0.116 vs 0.125, front 0.110 vs 0.122) but only **ties** the drawing swap on appearance. Its advantage is shape: the swap matches the target silhouette at IoU 0.64, the fitted puppet at 0.73 — but the puppet is fitted to that silhouette, so this comparison favours it. Honest summary: the learned model adds articulation and view continuity; its textures are blurrier than a raw archive frame.

## How the dog moves

Score `act` values → controls (`build/controls.py`) → pose (`build/dogmodel.py`):
- **view**: φ 0→180 for the refusal turn (3.42–3.82 s, through the front view), back 8.0–8.6 s; the head has its own view and **comes round over the shoulder at 7.46–7.72 s while the body is still lying facing away** (head layer reflected about its joint — a pose the archive never shows).
- **feet**: a planted-foot gait planner by distance walked (stride 0.42 m, duty 0.62, lateral-sequence phases); stance feet are fixed in the world and two-link IK solves each leg; walking backward (retreat) replays the same planner in reverse. Paw taps in the sound are emitted at the same stance onsets (46 taps).
- **lying**: torso lowered to 26 template px; legs blend to authored folded angles (correction, below).
- **head low** (approach): act.head 0.45 → head layer rotated ~0.85 rad down, below the back line for the whole approach.
- **look in** (26.4 s): body stays; head muzzle levels into the lit doorway, foreshortened, face side in shadow (correction).
- world X of the torso centre = score x − 0.35 m (static oblique camera, 210 px/m), so lying at x = 0.59 puts head and forelegs inside the door frame and the tail outside.

## Model alone vs film (failures isolated, not hidden)

`proof/raw_vs_corrected.jpg` (also on the end card). "Model alone" = joint rotations clamped to the learned range (μ ± 2.5σ), head view tied to the body view, the head's away-view folded onto the toward-view.
1. **Lying**: the learned range has no folded legs; the model alone produces a crouching dog with legs bent under/through the floor. Correction: authored fold angles (sphinx forelegs, folded hind legs). OOD stays high (0.84–0.88) — flagged, not hidden.
2. **Looking back over the shoulder**: the model ties head view to body view, so it never looks back. Correction: independent head view, reflected head; the reflected head first pointed at the sky because its tilt wasn't reflected (fixed: reflected tilt).
3. **Looking in**: a 2.5D layer cannot tell a head turned away from one turned toward the camera — the model shows the 3/4 *face*. Correction: profile texture, shortened 42 %, face darkened; muzzle levelled into the doorway. Perceptually weakest correction.
4. **Front view of the turns**: x-only foreshortening stands the head and neck upright ("giraffe"). Correction: head tipped toward the camera with ψ_h; far legs fade behind near legs.

## Measured onsets (from the render; `trace.json` → `onsets_measured`)

Criteria on the rendered dog: retreat = body lowers/moves away; watch = crouched back rises 2 px; refuse = head direction swings >12°; watch again = nose points back at the door; approach = centroid moves 2 px toward the door; lie = top of the dog drops 3 px; look in = head direction turns >8°.

| choice | score | measured | dt |
|---|---|---|---|
| retreat | 1.000 | 1.000 | 0.000 |
| watch | 2.333 | 2.375 | +0.042 |
| refuse | 3.417 | 3.417 | 0.000 |
| watch (turns to look) | 7.458 | 7.625 | +0.167 |
| approach | 14.708 | 14.750 | +0.042 |
| lie down | 23.792 | 23.833 | +0.041 |
| look in | 26.4 | 26.417 | +0.017 |

`check_handmade.py`: ALL OK (I1–I4). The first retreat→watch criterion (bbox height) caught gait bob at 1.83 s and failed I1; I changed the criterion to the top of the dog, not the animation (ledger 9).

Sound (`proof/sound_levels.json`): calls −18.0 dBFS RMS, soft voice −31.0 (13 dB quieter), room tone −47.5. Voices are flite speech synthesis.

## Protected / invariants

Numerical: the six choices ±0.25 s; dog never inside (x ≥ 0.56); position correlation with score x (checker r reported in invariants.json); refusal frames show the back. Feet: stance feet fixed in world coordinates by construction (IK reach error reported per frame as `reach_err`; non-zero where legs cannot reach in crouch/lie). Judged only by viewing: whether the generated poses read as one dog.

## What is weak (looked at, not measured)

- The dog is soft and blurry (384×288 archive, averaged atlases) and lilac-grey; the head reads as a dark mass without a clear muzzle in many frames.
- The two front-view frames of each turn are still a knot of legs; the 3.6 s still catches one.
- The look-back head reads as "head turned back" mostly by silhouette; the look-in reads by darkening, not by a real back-of-head view.
- The OOD score is not very discriminating: ~0.5 even while standing (the learned rotation Gaussian is narrow), 0.84–0.88 lying. It ranks correctly but is not calibrated.
- Fits of frames 33–48 (head lowered to the bowl) are poor (IoU 0.54–0.75); their heads are misplaced, so head atlases at 45° are partly wrong.
- Template changes (bigger knee caps) came after the fits; fits were not redone (learning was).
- The person is a plain drawn silhouette; it turns toward the door at 22 s by scaling through edge-on.

## What I did not do

No autodiff, no neural network (PyTorch not available; nothing large installed): "learned" here means optimisation-fitted poses plus nonparametric regression/averaging. No independent critic review yet. No operator page. No use of the door footage (a real 1992 face), Quick, Draw! or other found shots. The template skeleton and the corrections are hand-authored and listed above. Rebuild: `build/make.sh` (fit takes 10–40 min on a loaded machine).

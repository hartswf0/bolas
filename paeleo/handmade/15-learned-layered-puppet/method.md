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
| visibility layers | occlusion by the layers above is computed per frame in back-projection; far legs switch off (hard, never translucent) above 62°; the mirror solution swaps inside the skipped 55–125° band of each whip-around turn. |
| uncertainty estimates | per-texel confidence of each learned atlas (support of the view kernel); per-frame OOD score = Mahalanobis distance of the generated joint rotations under the learned Gaussian × view support. It is written to `trace.json` (`ood`, `mahal`, `view_support`) and sonified as a faint detuned tone (−37 dBFS peak). |

**What is learned** (`build/learn.py`, numbers in `proof/eval.json`, `proof/model.json`):
- a view latent ψ (0 profile … 90 facing camera) per frame from the fitted torso foreshortening under an ellipse prior (width/length 0.38, stated assumption); head view ψ_h the same way. Left/right mirror symmetry of the dog is assumed.
- Nadaraya–Watson regression on ψ of head tilt, head height, tail length, fore/hind leg length (e.g. the archive teaches that in front views the head layer sits tilted ~0.5 rad down and squashed to ~0.55 height).
- per-layer, view-conditioned texture atlases (7 bins, 0–90°), kernel-weighted back-projection with shrinkage toward the f006 texture where support is low (`proof/learned_atlas.jpg`, blue = low confidence: the tail almost everywhere).
- a Gaussian prior over 10 joint rotations. PCA of fitted poses: PC1 holds 30 % of variance and correlates r = 0.80 with the view latent (the archive's main variation is the turn).

## Measured: how well it learned

- Fit IoU (rendered silhouette vs SAM mask, at 96×72) mean **0.71** over 50 frames (final end-to-end rebuild; 0.73 in round 1 with the older template); learning frames: profile 0.75, turning 0.67, front 0.76; worst frame 23 (bad mask). First fit attempt at 192×144 reached 0.82–0.92 on profile frames but was too slow on the shared machine and was killed (ledger 2).
- **Held-out appearance** (each frame reconstructed with an atlas built without frames i±2), mean abs. grey error (final rebuild): learned **0.096** vs single-drawing rig (f006 texture on the same fitted pose) **0.109** vs drawing swap (nearest-view other frame cut out and box-aligned) **0.098**. By view: profile 0.075 / 0.085 / 0.092, turning 0.118 / 0.135 / 0.102, front 0.107 / 0.120 / 0.106. So the learned appearance beats the one-drawing rig in every view and beats the swap on profile frames, but loses to the swap while turning. Silhouette: swap IoU 0.68 vs fitted puppet 0.72 — the puppet is fitted to that silhouette, so this favours it. Honest summary: the learned model adds articulation and view continuity; its textures are blurrier than a raw archive frame.

## How the dog moves

Score `act` values → controls (`build/controls.py`) → pose (`build/dogmodel.py`):
- **view**: the refusal turn (3.42–3.82 s) is a whip-around: 0→55°, one cut to 125°, then →180°. The turn back (8.0–8.5 s) goes 0→55° and then through three solid intermediate views (≈70°, 90°, 110°, round 4) before reaching 125–180°, so there is no single-frame mirror pop. Far legs are hidden by a hard visibility switch above 40°, never faded, so no turn frame shows more than four legs; and the mirror crossfade was removed (it made ghost limbs); the head has its own view and **comes round over the shoulder at 7.46–7.72 s while the body is still lying facing away** (head layer reflected about its joint — a pose the archive never shows).
- **feet**: a planted-foot gait planner by distance walked (stride 0.42 m, duty 0.62, lateral-sequence phases); stance feet are fixed in the world and two-link IK solves each leg; walking backward (retreat) replays the same planner in reverse. Paw taps in the sound are emitted at the same stance onsets (46 taps).
- **lying**: torso lowered to 26 template px. The near foreleg lies flat forward and ends in a drawn rounded paw pad. Far legs and both hind leg segments are hidden under the body (round 4: no hind leg stretched back), and the tail rests along the boards. In round 2 the legs splayed like flippers or talons with hook feet. While standing, the lower-leg bend is clamped to ±0.6 rad so no paw curls into a hook. There is a slow breathing swell (2.2 %, 2.3 s period) while lying. All of this is correction.
- **head low** (approach): act.head 0.45 → head layer rotated ~0.6 rad down and its neck joint dropped 30 template px. Measured on the render, 15.0–23.5 s: top of the head layer is **13.4 px (min) / 19.4 px (mean)** below the withers point (`trace.json` → `head_low_approach`).
- **look in** (26.4 s): the head lifts off the paws, held roughly level, and is swapped for a **back-of-head layer**. Its outline is a skull curve with two folded dog ears, united with the learned head layer's own neck, so it stays attached. Its fill is the learned head-layer fur texture at 72 % brightness, rim-lit along the outline (round 4; in round 3 it was a flat dark polygon with cat ears and a gap at 27.2 s). It sits inside the door frame and is held from 27.0 to 28.2 s, then it settles back. This is a correction (round 3; in round 2 it was a dark tapered plume).
- world X of the torso centre = score x − 0.25 m, and the dog's path runs at Z = −0.25 m, nearer the camera than the door's centre line (static oblique camera, 210 px/m). The person sits on a crate at Z = 1.35 m, so the dog's feet are always lower in frame than the person's shoes and its body clears their legs (critic, round 1: it used to walk through the shins). Lying at x = 0.59 still puts head and forelegs inside the door frame and the tail outside.

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
| watch | 2.333 | 2.417 | +0.084 |
| refuse | 3.417 | 3.417 | 0.000 |
| watch (turns to look) | 7.458 | 7.625 | +0.167 |
| approach | 14.708 | 14.750 | +0.042 |
| lie down | 23.792 | 23.833 | +0.041 |
| look in | 26.4 | 26.417 | +0.017 |

`check_handmade.py`: ALL OK (I1–I4). The first retreat→watch criterion (bbox height) caught gait bob at 1.83 s and failed I1; I changed the criterion to the top of the dog, not the animation (ledger 9).

Sound (`proof/sound_levels.json`): calls −18.0 dBFS RMS, soft voice −31.0 (13 dB quieter), room tone −44.9. flite's leading silence is now trimmed. Call onsets measured from the voice band of the encoded film.mp4: **0.938 s** and **3.358 s**, both before the gesture and the dog's reaction (1.00 and 3.42); in round 2 they were about 1.30 and 3.70. Voices are flite speech synthesis.

## Protected / invariants

Numerical: the six choices ±0.25 s; dog never inside (x ≥ 0.56); position correlation with score x (checker r reported in invariants.json); refusal frames show the back. Feet: stance feet fixed in world coordinates by construction (IK reach error reported per frame as `reach_err`; non-zero where legs cannot reach in crouch/lie). Judged only by viewing: whether the generated poses read as one dog.

## What is weak (looked at, not measured)

- The dog is soft and blurry (384×288 archive, averaged atlases); door-light tint on the dog was reduced in round 2 so it stays grey. The head reads as a dark mass without a clear muzzle in many frames.
- The turns are whip-arounds that skip the front view: honest about the model's limit, but a fast cut rather than a continuous turn.
- The look-back head reads as "head turned back" mostly by silhouette; the look-in reads by darkening, not by a real back-of-head view.
- The OOD score is not very discriminating: ~0.5 even while standing (the learned rotation Gaussian is narrow), 0.84–0.88 lying. It ranks correctly but is not calibrated.
- Fits of frames 33–48 (head lowered to the bowl) are poor (IoU 0.54–0.75); their heads are misplaced, so head atlases at 45° are partly wrong.
- Template changes (bigger knee caps) came after the fits; fits were not redone (learning was).
- The person is a plain drawn silhouette on a drawn crate. From round 3 the body never turns; only the head profile snaps toward the door at 22.5 s (in round 2 the whole figure squashed edge-on). The offered hand drops below knee height and forward toward the dog by 7.15 s (round 4).

## What I did not do

No autodiff, no neural network (PyTorch not available; nothing large installed): "learned" here means optimisation-fitted poses plus nonparametric regression/averaging. Round 1 independent critic: does not pass, narrowly; five repair conditions met in round 2 (see ledger 11–12). Round 2 critic: does not pass, narrowly; five more conditions (look-in, lying paws, person turn, call timing, end-card contradiction) addressed in round 3 (ledger 13). Round 3 critic: does not pass, narrowly (the look-in head was a different material, five limbs in the turn back, hind legs stretched while lying, hand not low, assets entries); repaired in round 4 (ledger 14). Round 4 not yet reviewed. Rounds 3–4 re-rendered, re-mixed and re-encoded from the round-2 fits and model (no re-fit); encode.sh uses CRF 25; film 3.9 MB. Body height lowered (standing hip height 55 template px) so the IK feet reach the boards (mean reach error 2 px); in round 3 legs near the sill ended in the air and read as cut by the sill board. No operator page. No use of the door footage (a real 1992 face), Quick, Draw! or other found shots. The template skeleton and the corrections are hand-authored and listed above. Rebuild: `build/make.sh` was run end to end in round 2 (about 75 min on the shared machine) and ended ALL OK.

# SCION 35 · Moving Least Squares, Gesture Warp: method

**Thesis.** A few handles cause fast, expressive bending of a non-rigid print, and the print itself shows where the warp distorted it. The dog, the person and the porch are a two-colour risograph made in code: a blue plate and an orange plate, each screened into round dots, overprinted on cream stock, with the orange plate slightly off register. The dog's dots belong to the dog's own print space, not the screen. When MLS bends the dog, its dot grid stretches, shears and compresses on screen, and that distortion is left visible, not smoothed away. The porch is screened in screen space with a finer dot (5 px against the dog's 9 px), so the two grids do not merge.

## Swarm (as run)
One builder ran these roles in sequence. No separate agents ran, and no independent critic has reviewed this yet.
- **Control designer:** the view prints, the anchors and the keys (`dogprint.py`, `anim.py`).
- **Numerical MLS developer:** `common.mls` (affine, similarity and rigid, after Schaefer et al. 2006), the forward mesh and splat, the merge and fold guards (`render.py`).
- **Feature-tracking critic:** onsets and facing measured from the rendered layers (`measure.py`).
- **Parameter selector:** per-family proof (`proof_families.py`), which moved the neck from affine to similarity on measurement.
- **GPU engineer:** none. The work is NumPy on CPU, at about 1 s per frame on an idle core.

## Native formal language
- **Control anchors.** 37 named body points (nose, skull, eyes, ear bases and tips, poll, throat, withers, back, croup, rump, chest, belly, tail 0–3, and four joints on each leg). They mean the same body point in every view print.
- **Per-region families.** Each print is ten cut layers, and each layer has its own handle subset and MLS family:
  - rigid: skull and ears;
  - similarity: neck, legs and tail;
  - affine: the loose coat (torso).
- **Influence falloff.** Weights are `1/|p−v|^(2α)`, with α = 1.0 for skull and ears, 1.2 for the coat, 1.4 for the neck, 1.6 for the tail and 1.8 for the legs.
- **Per-frame trajectories.** Two sources, both keyed to the score:
  1. View keys interpolated with a monotone cubic over body yaw, head yaw/pitch and stand→lie.
  2. The score's acting values per frame: head, crouch, ears, tail, wag, rest, look and walk phase. Paws are planted from the score's walk phase (11.5 rad/m, measured), so stance feet hold in the world.
- **Motion stretch.** A handle that moves faster than the body is drawn out along its motion, capped at 7 px, so fast swings smear the dots.
- **View prints (13).** The full list and contact sheet are in `assets.json` and `proof/view_prints.jpg`: profile, three-quarter, rear, lying, look-back and look-in. A print swaps at the midpoint of a swing. Both prints are warped to the same handles on that frame, so the swap happens behind the gesture. There is no cross-dissolve anywhere.
- **The guide.** A 37-point stick guide places the shapes and handles. It is never drawn. What you see is always a print bent by MLS.

## Distortion, measured and shown
Every frame records, per layer, the singular values of the warp on an 8-print-px grid: anisotropy of the dot grid (s1/s2), area range, folded cells and handle error. The foot of every frame prints the largest anisotropy per family.

| family | median max-anisotropy | 95th percentile | max |
|---|---|---|---|
| affine (coat) | 1.03 | 1.12 | 2.6 |
| similarity (neck, legs, tail) | 1.06 | 1.88 | 5.9 |
| rigid (skull, ears) | 1.03 | 1.40 | 2.5 |

- Folded cells: 0 in every family.
- Handle error: ≤ 6e-8 px.

**Hard proof** (`proof/families.*`): the same handle move under four family assignments. Anisotropy:

| assignment | neck | fore leg |
|---|---|---|
| all affine | 20.9 | 13.9 |
| all similarity | 12.3 | 1.95 |
| all rigid | 82.9 (folds) | 30.9 (folds) |

That measurement is why the neck became similarity.

## Measured onsets (from the rendered layers; signals in `trace.json` summary)

| choice | score time | measured | signal |
|---|---|---|---|
| retreat | 1.000 | 1.000 | centroid moves away |
| watch | 2.333 | 2.375 | head rises from the cower |
| refuse | 3.417 | 3.500 | head swings away |
| watch | 7.458 | 7.417 | head swings toward the door, hips down |
| approach | 14.708 | 14.708 | centroid moves toward the door |
| lie down | 23.792 | 23.958 | back drops |
| looks in | 26.4 | 26.25 | head moves into the doorway |

- End state: lying, 7391 dog px inside the door plane and 7612 outside, tail outside.
- `check_handmade.py`: ALL OK.

## Sound (measured from the mix)
- Calls: −22.6 and −20.6 dBFS RMS.
- Soft voice: −37.5, −37.2 and −33.7 dBFS, at least 11 dB under the calls.
- Room tone: −57 dBFS.
- Every voice starts before the dog reacts: 0.90, 3.26, 7.30, 10.32 and 26.26 s.

## What failed and what changed
`ledger.jsonl` has the full list. The main ones:
- **Rigid MLS could not absorb the print's 2× scale.** MLS now runs in film units.
- **2D-lerped handles tore the print in the turns.** Coincident left/right pairs separated. Fixed by moving handles along the guide, merging handles that sit close together, falling back to similarity when handles are collinear, and keeping only centre-line handles on the coat.
- **The head vanished in the rear view.** Its handles all merged into one point. Such a layer is now translated instead.
- **The neck folded in the swings.** A fold guard now re-solves a folding layer as a two-handle similarity. It fired in 377 layer-frames: 371 neck, 6 legs, and 0 on coat or skull.
- **Lie onset was measured late.** It is now measured on the back, not the ears.
- **The look-in read as a lift.** The neck is now kept forward and level.

## What is still weak (looked at, not resolved)
- **Approach neck.** During the head-low approach the neck mostly runs on the fold guard (two-handle similarity), not on its full handle set.
- **Swing frames.** The rear three-quarter frames around 3.58 s and 8.25 s show a tall, thin neck for a frame or two.
- **The person** is a crude hooded figure. The low hand stops near the knee and reads as "low and forward" more than "offered".
- **The look-in head** is small at full frame.
- **The sill** reads as a light strip in perspective. The doorway is a cut-away convention.
- **The voice** is a formant synthesiser. It is intelligible as speech-like calls, but I did not listen to it here (no audio playback); only the levels were measured.

## What I did not do
- No kit material (archive dog or door, Quick, Draw!, found footage) was used.
- No independent critic has seen this.
- No operator page.
- No GPU.
- No git.

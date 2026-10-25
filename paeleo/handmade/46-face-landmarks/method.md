# SCION 46 · Face Landmark Registration — Recasting Anatomy · the threshold, handmade

## Thesis

The dog's choices live in its face. A head is a plate that can be swapped; what must survive the swap is
attachment (it stays on the neck), direction (it looks where the dog means), and expression (ears, eyes, mouth).
So the dog is built as interchangeable view-specific head and body plates, and the refusal is the face *withdrawn*:
the face plate is replaced by the back of the head. The defining passage is that substitution in both directions:
3.42 s the face leaves (it turns its back), 7.46 s the face comes back over its shoulder, 26.4 s the face leaves again,
this time into the lit room (*looks in*), and stays. Bland would be: one head plate slid around, a mirror flip for every turn.

## Swarm (one agent, roles merged; no role is claimed as a separate run)

| Role | Artifact it made |
|---|---|
| Face geometry engineer | `build/geom.py` (landmark vectors, camera, similarity / affine / two-point fits), `build/pose.py` (solver) |
| Source face annotator | `build/face_source.py` → `cache/face/manifest.json` (hand-annotated landmarks, measured registration of mouth frames) |
| Perspective estimator | camera + view-matching in `build/register.py` (azimuth of head and torso vs. camera, hysteresis) |
| Expression animator | `build/rig.py` (score → pivots, ear / lid / mouth / tail controls, head leads every turn) |
| Rights / consent reviewer | `assets.json` (every piece, its source and rights) |
| Independent likeness critic | **not run here**: the brief assigns an independent critic after delivery. I did not approve my own work. |

## Native formal language, as built

- **Landmark vector.** The dog has a body vector (withers, rump, chest, brisket, belly, neck base, shoulder and hip
  joints, flanks, tail base) and a head vector (skull pivot, nose tip, stop, both eyes, both ear bases, chin, throat,
  cranium, occiput, cheeks), in metres, dog-local. The person's face has its own (bridge, nose tip, upper lip, mouth, chin, pivot) in source pixels.
- **Fits.** Every dog plate carries its landmarks in its own (canonical, orthographic) frame. Each frame it is placed only by a
  least-squares affine fit from those landmarks to the solver's projected landmarks (`registration.json` keeps view, mirror side,
  the 2×3 fit, its residual and anisotropy per frame). Ears and neck use two-point fits (base→tip, neck pivot→skull pivot).
  The person's face, a source portrait, is placed by **similarity only** (never sheared). The door, a source photograph, is
  rectified by a projective fit and re-projected each frame by another projective fit onto its swinging panel.
- **Skull / neck pivots.** Neck base on the torso, skull pivot 0.17 m along the neck; head yaw leads the body on every turn
  (by at most 70° while the body turns, so no headless frame).
- **Eye / mouth controls.** Lids (blinks at chosen moments, heavy when resting), iris gaze, the white of a worried eye; mouth line,
  open wedge and tongue for the sigh; ears from flat to pricked (score `ear`), flicks toward the soft voice.
  The person's mouth is substitution among three source frames (closed, half, open), chosen by the voice's syllable envelope.
- **View-matching.** Head plates at 45° (three-quarter front), 90° (side), 135° (three-quarter back), 180° (back);
  torso plates at 90°, 135°, 180°. The other half-circle is the same plates mirrored *by the fit itself* (left/right landmarks swapped).
- **Temporal smoothing.** One-Euro filters on lift, pitch, neck elevation, head pitch, ear and tail (cutoff rises with speed, so
  action is kept); view hysteresis of 7° so substitution never flickers.
- **Time base:** score frame i, t = i/24. **World:** metres, threshold plane X = 0, inside negative. **Mapping:** the dog's
  mid-body X = score x − 0.55, so at the score's sill (0.56) its front half is inside the door frame.

## How the dog moves

Torso pivots from the score (`x`, crouch, lie), heading turned through the far side (away from the camera) both ways:
watching 172° → back turned 318° (3.46–3.92 s), back again 7.98–8.55 s. A stepper plants each foot in the world and steps it
only when the body has moved off it or the leg would over-reach (looking six frames ahead), so nothing slides while it bears
weight; two-bone IK places elbow/stifle; lying sends the paws to their lying places (forepaws out, hind legs folded). The tail is a
five-pivot chain (`tail` act from high to tucked, `wag`). The paw sounds are those foot contacts.

## World

A cut-away house (the near wall below the lintel is removed, a stage convention, only the door's near casing stays, in front of
whoever crosses the threshold); a lamp-lit room; the porch, steps, railing, yard and treeline at dusk. The warm light on the porch
is the lit part of the doorway projected from the lamp, and the dog's and person's shadows are their landmarks projected from the
lamp. The camera holds wide while the dog keeps its distance and comes closer only as it does (15.2–24.6 s).

## Sound (synthesized; I cannot listen to it)

Formant-synthesized voice ("come here" ×2 loud, "it's all right" ×2 and "come in" soft), paws from the stepper's contacts, door
creak as it swings, the room's hum and a clock that get louder once the door is open, collar tag on turns, a breath when it lies
down, wind and crickets. Measured: see *Evidence*.

## What failed and what I changed (full list in `ledger.jsonl`)

SEE_LEDGER

## Evidence

SEE_EVIDENCE

## What I did not do

- No independent critic was run by me; no human has watched or listened to the film.
- The voice is not intelligible speech: it is pitched, timed syllables with consonant noise. Whether it reads as "come here" is unknown.
- The person's face exists only in profile (the source never shows another view), so the person never turns their head; their
  forehead, cranium and back of head are drawn (the hat covers the forehead the source never showed). The cartoon's own light
  bands are kept (graded, not repainted).
- No Quick, Draw! drawings and no archive-dog pixels are in the picture (the archive dog was a reference for coat and markings).
- The SCION's original proof (three faces recast on one actor) is replaced by the brief's scene; I did not recast the person.

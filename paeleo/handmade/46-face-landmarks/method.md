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

1. **first 5 test frames**: legs read as jointed stilts, neck a white giraffe tube, head too small for the face to carry choices, treeline read as mountains, the cut wall hid the person in the doorway, ears like horns. *Changed:* limbs drawn as one outline through the pivot chain; head landmarks cast 1.22x; neck shorter/wider, collar narrower; treeline of rounded crowns; near wall removed below the lintel.
2. **close-up test**: the near jamb's thickness face became a wide dark pillar over the lying dog's shoulders. *Changed:* jamb face removed; only the thin near casing is drawn in front of whatever crosses the threshold.
3. **turn test 3.4-4.0 s**: the head led so far that a back-of-head plate sat on a side-view body: a headless bulb for 2-3 frames. *Changed:* head lead clamped to 70 deg while the body turns; body turn starts 3.46 s.
4. **look-in test 27.5 s**: the three-quarter-back head plate still read as a face (eye sliver, nose tip): looking in read as looking at the person. *Changed:* redrew the 135 plate as the face withdrawn: back of skull, ear backs, cheek edge, receding muzzle, no eye.
5. **stepper check**: reach was measured to the floor instead of the wrist/hock, so feet stepped 12 times a second even standing still; legs over-reached at the turns. *Changed:* reach measured to the IK end; stepper looks 6 frames ahead and steps on over-reach; planted-foot drift now 0.0013 m/frame max.
6. **partial full render**: in the wide shot the seated person was cut off at the left edge for 6-16 s, so the changed circumstances were not visible. *Changed:* wide camera re-centred and widened; person sits at the score's x = -1.25; hand offered forward and low.
7. **spectrogram (image only; I cannot listen)**: crickets a loud, regular band at ~4.5 kHz throughout. *Changed:* crickets halved and slowly modulated.
8. **timing (measured)**: look-in onset measured at 26.67 s (+0.27, outside tolerance). *Changed:* head turn into the room 26.36-26.62 s; measured 26.54 s.
9. **full render 1**: film 14.3 MB (over 12 MB). *Changed:* x264 -tune animation crf 25: 2.66 MB; still looked at, flat colour intact.
10. **full render 1, end**: the offered hand overlapped the lying dog's head at 28 s: read as taking the hand, and look-in read as toward the person. *Changed:* the hand is drawn back to rest low once the dog lies (24.3-25.6 s); look-in turned deeper into the room; frames 576-767 re-rendered.

## Evidence

**Measured from the render's registration (proof/choices_measured.json):**

| choice | score t | measured onset | dt | how measured |
|---|---|---|---|---|
| retreat | 1.0 | 1 | +0.000 | first frame the placed torso moves back (away from the door) by more than 4 mm |
| watch_1 | 2.333 | 2.417 | +0.084 | first frame after the retreat the ears are back up past halfway (ear control) |
| refuse | 3.417 | 3.583 | +0.166 | first frame the head plate shown is a face-withdrawn view (three-quarter back or back) |
| watch_2 | 7.458 | 7.625 | +0.167 | first frame after 7 s the head plate shown is a face view again (side or three-quarter front) |
| approach | 14.708 | 14.75 | +0.042 | first frame the placed torso moves toward the door by more than 4 mm |
| lie_down | 23.792 | 23.875 | +0.083 | first frame the torso is more than 2 cm lower than standing |
| look_in | 26.4 | 26.542 | +0.142 | first frame after 26 s the face is withdrawn into the room (three-quarter-back head plate) |

**Checker** (`tools/paeleo/check_handmade.py`): I1 choices True, I2 threshold True (min x_score 0.6051, end 0.6051), I3 direction True (r = 1.0, x_world_measured), I4 refusal True (share turned 0.959).

**SCION numeric invariants (proof/invariants_numeric.json):** head attachment error max 0.943 cm (mean 0.354); eyes inside their head plate 100% of 587 drawn eyes; planted-foot drift max 0.001289 m/frame; source face similarity-only (anisotropy 1, shear 0); head below the withers for 100% of the approach (worst margin 0.021 m); 11 head and 6 body substitutions.

**Sound levels (measured from the stems, build/cache/sound_levels.json):** calls -17.15 dBFS RMS, soft voice -30.67 (-13.52 dB vs calls), room tone -43.73 (soft is 13.06 dB above it). Heard: never (I cannot listen).

**Looked at** (Read on extracted frames): the four stills, the 0.5 s contact sheet (proof/contact_sheet.jpg), dog-centred crops of both turns, the refusal lie, the look-in and the end. **Perceptual judgements (mine, not a critic's):** the turned back reads by ~3.8 s as rump, tail tucked, head turned away; the face returns over the shoulder at ~7.6 s; head low on the approach reads; the end shows the dog across the sill, front lit warm inside, tail outside, back of head into the room. **Unknown:** whether the voice reads as words; how the substitutions feel at normal speed (I saw frames, not playback).


## Still weak

- The refusal's lie-down (4.5–7.4 s) seen from behind is a rounded lump with folded legs; it reads as 'lying, turned away' but not crisply.
- At 3.6 s (the still) the dog is mid-turn; the back is fully shown only from ~3.8 s.
- Legs are simple tapered outlines; the walk is plausible but stiff. The 135° torso is cushion-like.
- The person's cartoon face keeps its source's light bands, which can read as a striped mask or beard.
- In the wide shots the dog's face is small (~55 px head), so eye controls only really read in the close shot.

## What I did not do

- No independent critic was run by me; no human has watched or listened to the film.
- The voice is not intelligible speech: it is pitched, timed syllables with consonant noise. Whether it reads as "come here" is unknown.
- The person's face exists only in profile (the source never shows another view), so the person never turns their head; their
  forehead, cranium and back of head are drawn (the hat covers the forehead the source never showed). The cartoon's own light
  bands are kept (graded, not repainted).
- No Quick, Draw! drawings and no archive-dog pixels are in the picture (the archive dog was a reference for coat and markings).
- The SCION's original proof (three faces recast on one actor) is replaced by the brief's scene; I did not recast the person.

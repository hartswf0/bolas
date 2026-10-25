# SCION-24 · Live2D Cubism — Portrait Volume Illusion · The threshold, handmade

PAE-02, cohort 3. One agent working alone, in this folder only. The name is a lineage of method. There is no Cubism SDK or
Editor here: the primitives (parameter axes, keyforms, view interpolation, deformers, eye/mouth controls, physics, expression
state) were built from scratch in `build/rig.js` and `build/motion.js` and rendered with canvas paths in headless Chromium.

## Thesis

The viewer should read a mind in a flat drawing: a dog whose head, eyes and ears turn **separately** from its body, so that
attention visibly comes before action. Eyes move first, the head follows two or three frames later, the body last. The
defining passage is the end: the dog lies across the sill, hears *come in*, turns its head **into the depth of the lit room**
(back of the head to the viewer), holds, and lays its head back down. The look is the choice, and the restraint after it is
the answer. Bland would be: a puppet that slides between poses, a head that only lifts, a label that says "stays".

Protected conditions (from the SCION bar and the brief): gaze and head turn separable; face proportions stable across views;
silhouette appropriate to view; lips never drift into the wrong depth; the six choices on time; never inside the house; the
refusal shows the back; the approach head low; feet do not slide; the look-in reads in depth; the soft voice quieter than the
calls; restraint reads as choice.

## The swarm (merged; one agent)

| Role | Artifact it built or verified |
|---|---|
| Portrait analyst | looked at archive-dog frames f000, f012, f024, f036, f049 for coat pattern and proportions (study only); `proof/sheet_*.png` |
| Parametric deformer artist | `build/rig.js`: parameter table, head keyform table, deformer hierarchy, art meshes |
| Expression director | `build/motion.js`: the acting sheet (tracks for body yaw, head yaw/pitch/roll, gaze, brows, mouth, blinks, ear lags), the speech script |
| Head-turn continuity checker | `build/keyform_test.js` (`proof/keyform_test.json`), strips of every turn looked at frame by frame |
| View-limit tester | `proof/sheet_head.png` (yaw −90..180 × pitch), `proof/sheet_body.png`, `proof/sheet_pose.png`; pitch keys added when the blend exceeded its bound |
| Independent acting critic | **not run here.** The builder cannot approve its own work; a separate critic is to judge the film against the brief and this bar. |

All roles were merged into one agent because the coupling (one rig file, one acting sheet) was tighter than any parallel gain.

## Native formal language, as built

- **Parameter axes** (`proof/params.json`): ParamBodyAngleX, ParamAngleX/Y/Z, ParamEyeBallX/Y, ParamEyeOpen, ParamBrowWorry,
  ParamMouthOpen, ParamEarPrick, ParamTail, ParamWag, ParamCrouch, ParamLie, ParamRest, ParamNeck, ParamBreath. Each has a
  range (the source-sensitive limit) and a named driver (score act, acting sheet, or solver).
- **Keyforms and view interpolation**: the head is a table of keyforms, 16 yaw keys (every 22.5°) × 5 pitch keys (−35,
  −17.5, 0, 17.5, 35). A keyform holds the 2D positions and depths of named landmarks (muzzle base and tip, nose, both eyes and
  their corners, brows, both ears' bases and both tips — flat and pricked —, lip corners, chin, jaw hinge) and the projected
  ellipses of skull, cheeks, jowl and the two markings. At run time the head is the bilinear blend of the four nearest keys;
  shapes (tapered muzzle hull, almond eyes, ear leaves) are regenerated from the blended landmarks. The keyforms were authored
  from a turnaround guide (the landmarks rotated and projected once at load) with per-key corrections (`KEY_FIX`); the guide
  itself is never drawn.
- **Deformers**: a hierarchy of rotation deformers: root (score x, the torso middle) → body yaw → body pitch/height (crouch,
  lie, breath) → torso art meshes (chest, waist and rump volumes, with saddle, blaze and belly markings clipped to them) →
  neck (takes 0.55 of the head-to-body yaw difference) → head keyform blend → roll → eyes, brows, ears, nose, mouth; four
  legs (shoulder/hip → elbow/knee → wrist/hock → paw) solved by a two-bone solve to planted feet; a 7-segment tail chain; a
  collar tag. *There is no warp lattice;* I say so because the end card first claimed one and was corrected.
- **Eye/mouth controls**: almond eyes with an iris that moves inside the lid (so the white shows when the eyes slide to the
  back corner: the "whale eye" at 3.46 s, 6.3 s and 7.5 s), blink/open, brow pips that rise and draw in, a jaw that drops
  about the hinge landmark; the mouth line is drawn only while an eye faces the viewer.
- **Physics**: tail pendulum chain (targets from score act.tail and act.wag, follow-through down the chain, swing from body
  yaw), ear pendulums driven by head angular acceleration, collar-tag pendulum whose swings also cue the jingle.
- **Expression state**: the acting sheet in `motion.js` plus the score's acts; worry (brows, ears flat, tail tucked, crouch,
  faster breath), refusal (heavy lids, chin on paws, eyes still listening backward), softening (ears one at a time to the
  voice), settled (slow blinks, mouth a little open, a sigh at 29.15 s).
- **Coordinates and time base**: world metres (x along the porch, threshold 0, inside negative; y up; z toward the viewer),
  a raised side projection (depth lowers a point by 0.2 z; vertical planes facing the viewer are undistorted, so a profile is
  exact), 24 fps, 768 scene frames aligned to the score frame for frame. The house is drawn **in section** (the near wall cut
  away, as a stage set) so that the threshold can be seen from the side; light reaches the porch only through the doorway.

## How the dog moves

The score's x drives the rig root (the torso middle). The six choices are performed at their frames: backing away (1.00 s)
is a crouched walk backward with tail tucked and ears flat; it stops and lifts at 2.33; at 3.42 the eyes slide back, the head
swings away and the body turns 0 → 190° **through the view toward the viewer** (chest to camera) by 3.93, then lies down facing
away with its chin on its paws. While refusing, its eyes still go back toward the door when the latch clicks (6.3 s). At 7.46 it
rises; the head comes round over the shoulder by 7.75–7.92 (again through the face-to-camera view), the body follows 8.06–8.78.
While it considers (camera on its portrait, 10.3–13.4 s) the gaze goes to the low hand, to the light, back to her, an ear turns
to *all right*. At 14.71 it comes, head below the line of its back; at 23.79 it lies down with head and forepaws between the
jambs and its tail outside; at *come in* (26.42 s) its ears and eyes go first and the head turns into the depth of the room;
it holds there to 28.0 and lays its head down on its paws, and stays.

Feet: a stepping solver keeps every paw planted until its home under the body has moved more than a threshold away (or the leg
nears full reach), then swings it through the air to where the home will be, with diagonal coordination. Planted paws never
move; `build/legcheck.js` measures 0 frames where a planted paw is beyond its leg's reach (so the drawn paw never leaves its
planted point).

## Staging and sound

Camera (all zooms about a fixed screen point): a 1.2× two-shot for the calls and the refusal; out to the wide as she sits and
opens the door; a 2.9× portrait of the dog 10.3–13.4 s while it considers; wide for the whole approach (so its distance and
pace read); in to 1.75× at the sill. Because the camera moves, every trace frame has `x_world_measured`.

Sound is synthesized in `build/sound.py`: a formant voice (glottal pulse train + breath through moving formant resonators,
consonant bursts) speaking the lines of the speech script that also opens the person's mouth; a paw on the boards for every
footfall the gait solver actually planted (96 cue events from the render, including tag jingles, the lie-down flops and the
sigh); her steps, the bench creak, the latch and hinge; dusk wind and crickets outside, a clock and a fire inside that become
louder as the door opens.

## Measured (from the render, `proof/`)

- Checker: `python3 tools/paeleo/check_handmade.py` → **ALL OK** (I1 choices, I2 threshold, I3 direction r on
  x_world_measured, I4 refusal).
- Choice onsets measured from the drawn geometry of each frame (`proof/onsets.json`; spine points, head and nose positions,
  inverted through that frame's camera): retreat 1.000 s, stop 2.333, refuse 3.417, turn to look 7.458, approach 14.708,
  lie down 23.792 (all dt 0.000); the look-in head movement starts 26.500 (+0.10 s after the score's 26.4).
  Back shown (spine pointing away from the door) from 3.708 s; nose round to the door again at 7.750 s.
- `proof/measures.json`: refusal frames with the back turned 92.8%; skull below the withers on 97.2% of approach frames (the
  first ~0.3 s the head is still lowering); approach 3.406 m measured = 3.406 m in the score; retreat 1.000 m away from the door;
  end: lying, x_score 0.59, nose at x = −0.04 m (inside the door frame, which spans −0.22 to 0.40), tail tip at 1.31 m
  (outside); the nose never goes below −0.044 m, so no part of the dog enters the house (inside is x < −0.22).
- `proof/keyform_test.json`: view interpolation error at every in-between angle (2.5° steps × 7 pitches) at most 0.075 of the
  skull radius; skull area within 1.4% of the guide; the near lip corner inside the muzzle/jowl/cheek meshes in all 845 views
  where the mouth is drawn; far eye hidden in profile; both eyes in the front view.
- `proof/sound_levels.json` (stems, 90th-percentile 21 ms RMS while each line plays): calls −10.5 and −9.8 dBFS; soft lines
  −21.0, −21.1, −21.9 dBFS (≥ 10.5 dB quieter than the quietest call); room tone −47.5 dBFS (soft voice ≥ 25.6 dB above it).
- Film: 1280×720, 24 fps, 912 frames, 38.0 s, H.264 + AAC, faststart, 3.3 MB.

## Looked at (by the builder, not a critic)

Turnaround and pose sheets; frame strips of both turns, the walk, the lying and the look-in at full size; whole-film contact
sheets every 0.5 s (three rounds); the four stills; the title and end cards; spectrograms of a call and a soft line
(`proof/spectrogram_*.png`).

## What failed and what changed (full list in `ledger.jsonl`)

- The look-in first read as *looking up*: the pitch was lifted, and the person sat on the same line as the room. Repaired by
  removing the lift, turning the head yaw into the depth of the room, and seating her toward the viewer, so "looking at her"
  (toward camera) and "looking in" (away) are different directions.
- The dog lay in front of the doorway, not in it: the wall was made deeper and the jamb sections drawn in front of the dog.
- The torso was too long; the rim light showed inner mesh edges; the wide shot made the watch unreadable; camera moves lost the
  dog mid-move; shortened legs made planted paws over-reach; the pitch blend exceeded my interpolation bound (repaired by
  commissioning ±17.5° pitch keys, as the SCION prescribes, rather than widening the tolerance); the first voice was buried in a
  wrongly normalized reverb; the end card claimed warp deformers that do not exist.

## Still weak / unknown

- **Sound is unheard.** I cannot listen. The voice is a crude formant synthesizer; whether the words are intelligible is
  unknown. Levels and spectra are measured; nothing about how it sounds is known.
- The refusal turn and the turn back each pass through 3–4 frames of a frontal dog with clustered legs; they read as a dog to
  me in strips, but an independent viewer at speed has not judged them.
- At the look-in the near eye never fully disappears (the head stops at −54° yaw); it reads to me as the back of the head
  turned into the room, but this is a perceptual call, not a measurement.
- In the wide shots the dog is ~180 px long; the acting there is mostly posture, not face.
- The house in section is a stage convention: the viewer sees the room through the cut throughout; only the light on the porch
  depends on the door.
- The body's views come from a guide skeleton of points plus 2D volumes; the head is the only truly keyformed part. A critic may
  find the torso closer to a projected maquette than to drawn angle keys.
- Rights: everything was made here; the archive dog was only looked at. Fonts are the repository's (`tools/paeleo/fonts/`).

## What I did not do

No independent critique was run (not mine to run). No human watched or listened. No Live2D/Cubism software was used. No
material was fetched. No git. Nothing outside this folder was written. `paeleo/threshold/stage.js` and
`paeleo/scion/lenses.js` were not imported; the other swarms' folders were not opened.

## Rebuild

`build/make.sh` (node + Playwright Chromium, python3 with numpy, ffmpeg). Intermediates in `build/cache/`.

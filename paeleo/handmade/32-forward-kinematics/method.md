# SCION 32 · Forward Kinematics — Hierarchical Body Logic

PAE-02, cohort 8. The threshold scene built bottom-up as a hierarchy of pinned parts. The builder does not approve this work;
an independent critic judges it.

## The native formal language, and how it is kept

The primitives of this swarm are **joint graph, local transform, parent transform, bone lengths, pivot offsets and
view-specific anchors**. They are the working project, not a style laid over pixels:

- `build/rig.js` holds the **typed joint graph**: each joint is `[name, parent, pivot offset in the parent's frame]` with a
  fixed rotation order. The dog has 31 joints, the person 25. Every world transform is
  `parent_world × T(pivot offset) × RY(yaw) × RZ(pitch) × RX(roll)`, evaluated root-first. Nothing else positions a part.
- **No IK anywhere.** No per-frame solve, no constraint pass, no look-at. Poses are local angles only.
- **Bone lengths** are the pivot offsets; they never change. The toy is built in its own units and stands on the porch at
  1.4× (a uniform scale in the root transform), so a bone's world length is 1.4 × its offset.
- **Pivot offsets**: child limb boards sit 14 mm further out on their pins than their parents, as on a real jointed toy;
  the body turns about its middle (a pivot offset in the root), not about the hind pin.
- **View-specific anchors**: the head sits on a swivel peg whose pivot offset has three authored values, *profile*,
  *three-quarter* and *rear* (`HEAD_ANCHORS`). Each frame the head's angle to the camera picks the weights, blended
  continuously so a view change cannot pop. In the rear view the pivot rises and centres so the back of the skull sits
  square over the neck with both ears clear; in profile it hangs the skull forward of the neck.
- **Props and clothing are in the tree.** The dog's red felt saddle cloth is buttoned to the waist pin and has two hanging
  flaps per side (2-link chains); its drop ears are 2-link chains on the skull; its tail is five beads on a cord (5-link
  chain, the wag is a yaw wave in which each bead lags its parent by 0.7 rad). The person's cardigan cuffs hang on their own
  joint under each elbow, the hem panels on the spine, the jaw on the head.

## The dog: what it is made of, and how it moves

A carved and painted wooden toy, drawn in code (`build/scene.js`): a hind block and a chest block joined by a brass waist pin,
a neck block, a head with a separate muzzle, a black nose bead, painted eyes and a red painted mouth line; four legs of two
flat boards and a black paw block each, every pivot a visible brass pin; two black two-leaf drop ears; a five-bead tail
(red, cream, red, cream, black). Cream paint with brush streaks and a few brown patches on the hind block; red felt cloth with
a yellow stitched hem. The blocks are superquadrics with flat facets, so they read carved rather than turned.

How it moves — every degree of freedom is a local angle:

- **Walking, backing away, coming**: the animator laid out 8 key poses per stride cycle (contact, three through stance,
  lift-off, three through swing) for two body heights (upright, crouched). The key angles were worked out once with the law
  of cosines for where the paw should be at that key; at render time hip and knee angles are only *interpolated* between keys
  (periodic Catmull-Rom over gait phase) and blended by crouch. The gait phase advances with the distance the score's `x`
  travels (backwards when it backs away). The paw block is counter-rotated by the animator to stay flat. Between keys the paw
  drifts: that is the measured foot slip, below.
- **Turning its back (3.42 s)**: the head swings away first (neck and head yaw, 3.42–3.66), the body yaws 155° about its
  middle from 3.47 to 4.05, each paw stepping up three times; then it lies down facing away (the lying fold is an authored key
  pose) and rests its chin.
- **Turning back to look (7.46 s), after round 1**: the head swings round on the near (camera) side, low and at muzzle level
  (neck and head yaw share 205° relative to the body, the chest block curls a little), 7.44–7.66: the face and an eye are seen
  as it comes round and the muzzle points at the door by 7.62 with the hips on the boards. It rises 7.72–8.1, stands square
  (each paw set under its pin while the legs are free) and turns back under its held head on the same side, 205° over 2.1 s at
  a near-constant speed with four paw steps, so planted paws slide at most 29 mm a frame.
- **Lying across the sill**: the last fold is spread over 0.6 s (23.72–24.32), at most 14° per frame on any joint.
- **Turning back to look (7.46 s)**: while the body still lies, the neck yaws 88° and the head 58° over the shoulder, muzzle
  level, toward the open door (7.44–7.72); the body rises at 7.62–8.05 and turns back 7.95–8.75 as the neck unwinds.
- **Coming, head low (14.7 s)**: the neck is carried 58° down while approaching: the top of the head stays about 10 cm under
  the withers (rig, world metres) for the whole approach.
- **Lying across the sill (23.8 s)**: the dog walks straight at the door along the line X = 0, perpendicular to the sill;
  it lies with its chest block and head inside the door frame and its hind block and tail outside.
- **Looking in (26.4 s)**: the neck levels and pushes forward; neck and head yaw away from the camera, into the room: the
  camera, behind the dog's right shoulder, sees the back of the skull and both ears with the lit room beyond.

The person is a carved figure too: stands in the doorway and calls (jaw open, a beckon), reaches with a long lean, steps out
and sits against the wall beside the door, then offers the right hand low, palm up, across the near leg.

## Proof: the transform test suite (`build/fktest.js` → `proof/fk_tests.json`, `proof/errors_by_joint.json`)

All measured from the rig over all 768 scene frames.

| test | what | result |
|---|---|---|
| T1 bone lengths | every joint's world distance to its parent ÷ 1.4 vs its pivot offset (54 bones, dog and person) | max error **4.6e-16 m** |
| T1 view anchor | the neck→head pivot changes by design between its three anchors | world length 0.149–0.169 m, equal to the anchor in use every frame |
| T2 multiply order | each world matrix re-derived by walking its chain root-first | max matrix error 4.4e-16 |
| T3 propagation | right hip +12° (frame 400) | its 2 descendants follow the hip's own rigid change to 5.3e-16; the other 28 joints move **0** |
| | left shoulder −15° (400) | 2 descendants, 4.4e-16; others 0 |
| | waist yaw +20° (216) | 17 descendants incl. **saddle cloth and both flap chains**, neck, head, ears, front legs: 4.4e-16; others 0 |
| | pelvis pitch +8° (700, lying) | 29 descendants, 3.3e-16 |
| | person right shoulder +10° (600) | elbow, wrist, thumb and the **cardigan cuff** follow, 4.4e-16; others 0 |
| | person spine −8° (600) | 16 descendants incl. both **hem panels**, 4.4e-16 |
| T4 walking slip | planted paw (stance phase while the score moves), horizontal displacement per frame | mean **1.9 mm**, max 9.0 mm in the stride; max 18.9 mm at the set-off (14.7–15.4 s), where the square stance hands back to the stride keys (607 paw-frames) |
| T4 stance drift | touchdown to lift-off, per stance | mean 16.5 mm; max 21 mm in the stride, **146 mm** for the first stance of the set-off (the hand-back) (36 stances) |
| T4 standing | planted while the dog stands | mean 0.05 mm, max 6.4 mm (at turn ends) |
| T4 turning away (3.47–4.05) | planted paws while the body yaws 155° in 0.6 s | mean 33 mm/frame, **max 84 mm/frame** (18 paw-frames): visible scuffing |
| T4 turning back (7.95–10.1) | body yaws 205° on a trapezoid speed profile, standing square, four paw steps | mean 19.6 mm/frame, **max 28.7 mm/frame** (76 paw-frames) |
| T4 height | planted paw sole vs the boards | sinks 0.3–13 mm (never floats) |

`proof/errors_by_joint.json` lists every joint. `proof/joint_overlay.jpg` draws the joint graph projected over four frames
of the final film, with the right hip +12° and right shoulder −15° in blue: only their descendants move.
The paw taps in the sound are placed on the touchdown events T4 reports (64 footfalls).

The **numeric invariant** is T1+T3: bone lengths constant and children following parents exactly.
The **artistic achievement judged only by viewing** is whether a pinned wooden toy, moved only by angles, reads as a dog that
chooses: backing from the call, turning its back, looking round at the open door, coming head low, lying across the sill.

## The six choices, measured on the render

Measured by `build/trace.py` from the id pass of each rendered frame (visible pixels, same camera and depth test) and the
rig's nose and skull projected with that frame's camera. All within ±0.25 s; `check_handmade.py`: **ALL OK** (I1–I4).

| choice | score | measured | dt | measure |
|---|---|---|---|---|
| backs away | 1.000 | 1.042 | +0.04 | silhouette centroid, back-projected to the dog's line, > 2 cm away from the door |
| stops, watches | 2.333 | 2.375 | +0.04 | top of the visible head rises > 2 cm above its lowest point in the retreat |
| turns its back | 3.417 | 3.458 | +0.04 | muzzle direction on screen turns > 10° (the head leads); muzzle points away from the door from **3.625 s** |
| turns back to look | 7.458 | 7.542 | +0.08 | muzzle-to-door angle on screen falls > 10° (the head swings round low on the near side, face and eye to the camera, muzzle on the door by 7.62 while the hips stay down; the body rises 7.72–8.1) |
| comes, head low | 14.708 | 14.833 | +0.13 | centroid > 2 cm toward the door; top of the head ~10 cm under the withers (rig) for the whole approach |
| lies across the sill | 23.792 | 23.708 | −0.08 | top of the visible silhouette (metres over the floor at the dog) drops > 2 cm |
| looks in | 26.4 | 26.292 | −0.11 | visible head centroid moves > 4 px (it first lowers, then lifts level and turns into the room) |

The dog is in every frame (minimum 9,812 visible dog pixels). It never passes the score's sill position (x ≥ 0.59); at the end
its chest block and head are inside the door frame, its hind block and bead tail outside.

## Sound

All synthesized (`build/sound.py`): a source-filter formant voice (glottal pulses and breath through three resonators per
phoneme), wooden knocks on every paw touchdown that FK reports (`cache/footfalls.json`), the clatter of blocks and a felt rustle
when it lies, the door creak, the person's steps, crickets, wind and a warm room hum once the door is open.
Levels (RMS of the mixed track, measured): calls −15.3 and −15.2 dBFS; soft phrases −29.7, −31.2, −28.2 dBFS: the soft
voice is **12.9 dB under the calls** and 17.7 dB above the room tone (−48.9 dBFS). Voice onsets (scene time): calls 0.95 and
3.34 s, soft 7.30, 10.40, *come in* 26.30 s, each at or before the dog's reaction. The voice is a synthesizer: it has the shape
and pitch of the phrases, not necessarily words a listener will make out.

## What failed and what I changed

See `ledger.jsonl` for every attempt. In short: the first wide made the dog tiny and the dog read as a cow (patches, horn-like ears); I rebuilt the ears as drop
ears, cut the patches, built the toy 1.4× and re-staged the wide nearly in profile so the refusal shows the dog's flank with
its rump to the door and the look-back reads as a profile turn of the head. Turning about the hind pin slid the paws 0.2 m a
frame; turning about the body's middle with stepping paws halved that (still the weakest contact). The look-in did not read
from a low side camera (the jamb hid the head); the end camera now looks over the dog's back into the lit room. The voice
first had almost no upper harmonics (a hum); a Rosenberg pulse and lip radiation gave it formants.

## What is protected

The joint graph and rotation order (any change re-runs T1–T3); the walk keys (any change re-runs T4); the six choice
timings (re-measured from every render by `build/trace.py`); the dog never crosses the score's sill position (x ≥ 0.59).

## What is weak, and what I did not do

- **Turning away still slides.** Pure FK with sagittal legs cannot hold a paw while the body yaws; the quick 0.6 s refusal
  turn slides planted paws up to 84 mm a frame (kept quick so the back shows by 3.9). The slow turn back stays within 29 mm.
- **The set-off at 14.7** hands the square stance back to the stride keys: one stance drifts 146 mm over 0.8 s (≤19 mm/frame).
- **Paws sink** up to 13 mm into the boards at a few moments (start of the lie-down, crouched backing).
- **The dog is small in the wide** (about 110 px tall at x = 4) because the door, the person and the dog at 4 m must share it.
- The look-back's head swing (205° relative to the body) is more than a real dog's neck; the toy's swivel peg allows it.
- The person is stiff (a peg figure); its step aside is three authored strides with its feet sliding (not measured).
- The look-in is a modest movement (lift level, turn into the room); the camera sees the back of the skull and both ears.

What I did not do: no IK, no physics, no secondary-dynamics solver (all chains are authored angles); no kit material, no web
images, no recordings; no independent critic run (the builder does not approve its own work); no mobile operator page;
I did not listen to the sound (levels and spectrograms only).

## Evidence labels

- **Measured**: T1–T4 numbers (computed from the rig every frame); choice onsets (from the render's id pass and projected rig
  points with each frame's camera); voice levels (RMS of the mixed track); frame counts and file size (ffprobe).
- **Structurally verified**: the rotation order and the propagation of a changed hip/shoulder through descendants.
- **Perceptually judged by the builder only**: whether the choices read on screen — from frames extracted from the final
  film.mp4 (`proof/choices_full.jpg`, `proof/choices_crop.jpg`). Not independently judged yet.
- **Unknown**: how the synthesized voice reads to a listener (I cannot listen; I checked levels and onsets only).

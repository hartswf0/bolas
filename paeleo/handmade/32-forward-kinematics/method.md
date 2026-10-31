# SCION 32 · Forward Kinematics — Hierarchical Body Logic

PAE-02, cohort 8. The threshold scene built bottom-up as a hierarchy of pinned parts. The builder does not approve this work;
an independent critic judges it.

## The native formal language, and how it is kept

The primitives of this swarm are **joint graph, local transform, parent transform, bone lengths, pivot offsets and
view-specific anchors**. They are the working project, not a style laid over pixels:

- `build/rig.js` holds the **typed joint graph**: each joint is `[name, parent, pivot offset in the parent's frame]` with a
  fixed rotation order. The dog has 31 joints, the person 26. Every world transform is
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

NUMBERS_HERE

## The six choices, measured on the render

ONSETS_HERE

## Sound

All synthesized (`build/sound.py`): a source-filter formant voice (glottal pulses and breath through three resonators per
phoneme), wooden knocks on every paw touchdown that FK reports (`cache/footfalls.json`), the clatter of blocks and a felt rustle
when it lies, the door creak, the person's steps, crickets, wind and a warm room hum once the door is open.
SOUND_HERE

## What failed and what I changed

See `ledger.jsonl` for every attempt. LEDGER_HERE

## What is protected

The joint graph and rotation order (any change re-runs T1–T3); the walk keys (any change re-runs T4); the six choice
timings (re-measured from every render by `build/trace.py`); the dog never crosses the score's sill position (x ≥ 0.59).

## What is weak, and what I did not do

WEAK_HERE

## Evidence labels

- **Measured**: T1–T4 numbers (computed from the rig every frame); choice onsets (from the render's id pass and projected rig
  points with each frame's camera); voice levels (RMS of the mixed track); frame counts and file size (ffprobe).
- **Structurally verified**: the rotation order and the propagation of a changed hip/shoulder through descendants.
- **Perceptually judged by the builder only**: whether the choices read on screen — from frames extracted from the final
  film.mp4 (`proof/choices_full.jpg`, `proof/choices_crop.jpg`). Not independently judged yet.
- **Unknown**: how the synthesized voice reads to a listener (I cannot listen; I checked levels and onsets only).

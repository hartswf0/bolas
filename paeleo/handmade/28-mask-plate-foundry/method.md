# SCION 28 · After Effects: Mask and Performance Plate Foundry

## Thesis

Archive plates from four unrelated public-domain films are composited into one dusk shot: a 1941 hand, a 1992 NTIS
door and hallway, a cold-weather training film's seated figure, and a dog from a New Jersey home movie. The dog's
acting (backing away, turning its back, looking round, coming with its head low, lying across the sill, looking in)
comes from masks, parented transforms, plate substitution and holdouts keyed to the score. It is not the home movie's
own action played back. The result would be bland if it looked like cut-outs pasted on a backdrop. So every plate
shares one camera, one dusk grade, one door-light function and one grain target.

## The compositor (build/comp.py, about 230 lines of numpy and PIL)

Each primitive is a typed object:

- **BezierMask**: a closed path whose bezier tangents are computed automatically (Catmull-Rom). Vertex lists can be
  keyframed with eased interpolation. Each mask has feather (gaussian px), expansion (dilate/erode px) and a mode
  (add or subtract).
- **Xform**: a parented 2-D transform (anchor, position, scale, rotation, flip). Its world matrix is the parent's world
  matrix times its own local matrix.
- **CornerPin**: four source corners mapped through a DLT homography to a world quad projected by `camera.py`, a
  locked pinhole camera (f = 1060 px). Every set plate is pinned this way: room wall, side wall, interior floor, door
  leaf, facade, casing, sill and porch.
- **Track**: a keyed 2-D point. Three tracks are used. The home movie's `camera.json` is inverted to stabilise the
  yard before a median stack. I measured that the best integer alignment equals minus the track on frames 5, 10, 15
  and 20. The pose keys (neck, nose) carry the replaced head in turn 2. The dog's root track is the score's x through
  the camera.
- **Holdout**: a full-frame matte that removes a layer where something nearer stands in front. The doorway is a
  holdout cut into the facade. The facade, casing and sill mattes hold out the dog wherever it is past the threshold
  (screen x < the path's crossing of the facade plane). They also hold out the standing person, who is inside.
- **Keys**: a luma key cuts the 1941 arm, inside a garbage matte that leaves out the card it holds. An inverse luma
  key removes the snow around the seated figure. A difference key of the woman against a stabilised clean plate was
  tried and failed (ledger 3), so she is a hand-drawn 24-vertex roto.
- **Light and grain matching**: every dog plate is luma-matched (mean 0.30, std 0.15) and choked 1.6 px (no halo of the source's bright ground). Its ambient is set from the measured dusk band behind it (wall and floor at t = 1 s, luma 0.129): the dog sits at 1.35x that luma with half its blue tint, and a contact shadow from its own matte darkens the floor under it. One function,
  `light_at()`, models a lamp inside the room shining through the aperture the door leaf leaves open. That function
  lights the porch floor, the sill, the dog card and the person. The dusk ambient tint is shared. Each layer's grain
  is measured (high-pass MAD inside its eroded matte), and noise is added to reach a common target of 0.016. The
  measured values are in `build/cache/measure.json` → `grain`. Round 1 removed the 8-bit rounding from the measure; the values are now measured (the dog about 0.002 before matching), and about 0.016 is added (ledger 10).

## The dog

All of the dog comes from *Amateur Film New Jersey C*:

- **Rig plate f010** (standing, facing the door). Its SAM polygon is redrawn as a bezier matte and split by masks into:
  - a body (head and the legs below the belly line subtracted);
  - three leg layers, with the near hind leg duplicated, darkened and offset as the far hind leg;
  - a head with upper neck.

  The legs hinge on shoulder and hip pivots. The head hinges on the neck pivot. All are parented to the body, which
  is parented to the root track.
- **Walk**: the feet are locked to the floor. The gait phase comes from the distance the dog actually travels (stride
  0.5 m, 60 % stance), so the planted foot holds while the body passes over it. The footfall sounds use the same
  phase.
- **Head**: elevation is mapped from the score's head and rest values. During the approach it is held 33° below
  horizontal, under the line of the back.
- **Lying across the sill**: the dog's centre is 0.33 m nearer the house than the score's x, so its head and forequarters lie in the lit doorway past the sill (round 2: 0.42 m) and its rump and tail lie outside the right casing, on the porch. The body drops by the leg length. The belly mask is keyed by the score's `lie` value (two keys:
  standing, then lying, which rounds the haunch). The forelegs rotate 90° to lie forward and the hind legs fold 62°.
  None of the materials has a lying dog, so this pose is built entirely from masks and transforms.
- **Turn 1 (3.45–3.95 s)**: the dog's own turn plates f013, f030, f032, f036, three frames each, with hard cuts and
  no dissolves. Each plate was chosen from a cut-out sheet of f013–f041 because it shows one legible head; f016 (head
  hidden) and f040 (smeared double head) were rejected in round 1. The dog then reads as the mirrored rig with its back
  to the door, and it lies down (4.2–5.0 s). A tail from f019 hangs on the rump, tucks with the score's tail value,
  wags, and lies on the porch.
- **Turn 2 (7.46 s)**: the head leads. The f010 profile head, unmirrored, rides the mirrored, still-lying body's neck
  track, held up over the shoulders, so the muzzle points screen-left at the door while the body still lies away
  (round 2: the f038 frontal face of round 1 read as looking at the camera). The body rises from 7.5 to 8.0 s. The
  turn plates f038, f037, f013 then play, four frames each, each with its own single head.
- **Looking in (26.5–28.2 s)**: the head is swapped for the f000 plate, which shows the back of the dog's head. It is
  set level on the neck track with its mask extended down the neck so it overlaps the body (no gap), scaled to 0.78 and lit from behind, so its dark back faces the camera against the lit
  room. In this camera the room's depth and the seated person both lie to screen-left. A profile head would therefore
  read as looking at the person (ledger 6), which is why the back of the head is used.

## Measured (from the render's dog matte, and from the encoded film.mp4)

Choice onsets, detected from the matte (movement, head height, the plate in use, matte height):

| choice | score | measured |
|---|---|---|
| retreat | 1.000 | 1.000 |
| watch | 2.333 | 2.417 |
| refuse | 3.417 | 3.458 |
| watch (head comes round) | 7.458 | 7.500 |
| approach | 14.708 | 14.792 |
| lie down | 23.792 | 23.917 |
| looks in | 26.4 | 26.5 |

`build/cache/film_checks.json` also has:

- the film: 912 frames, 38.0 s, H.264 and AAC, faststart, about 9.3 MB;
- the audio, measured on the film's own AAC track: the calls average about −20.7 dBFS, the soft lines are about 13 dB
  under them and about 19 dB over the room tone.

At the end the dog lies with 34 % of its matte past the threshold, and 1,168 px are held out by the facade and sill. `check_handmade.py` reports ALL OK.

## Looked at

I looked at frames extracted from film.mp4: contact sheets of both turns (every two frames), an overview every 2.5 s,
and the sill sequence from 23 to 31 s. These were checked by eye only and are not a critic's verdict.

## What failed and what changed

The full list is in `ledger.jsonl`:

- The difference key failed and was replaced by roto.
- The first set was too bright, its floor tiles showed seams, and the lamp was on the wrong side, so no light reached
  the floor.
- The head rotation sign was inverted (the head lifted while approaching).
- The dog looked ghostly pale, the lit dog was overexposed, and the seated figure was orange and oversized.
- The first look-in head was an upright blob. The level profile head that replaced it read as looking at the person.
- The grain matcher at first measured zero noise because of a masking bug in the measurement. It was fixed for the
  final render.

## Still weak

- The source is 384×288 and blurry, so the dog is soft.
- The part seams (neck, shoulders) show on close viewing.
- The stone facade, made from resampled blocks, is busy and a little CG-regular.
- The back-of-head look-in reads as a dark rounded head turned away. It is ambiguous at small size.
- The seated person is the standing roto with straight legs swung forward: a stiff sit.
- The voice is a formant synthesizer and sounds synthetic.
- The tail is thin (the f019 cut) and reads only at full size.

## Not done

- No independent critic has seen this. I have not approved it.
- No Quick, Draw! drawings are used.
- No other found shots are used beyond those listed in `assets.json`.
- No 3-D model, and no generative model.
- No editable project file for After Effects: the "editable composition" is the Python comp (`rig.py`,
  `setplates.py`).

## Round 1 repair

The critic's round 1 verdict was DOES NOT PASS (`reviews/round1.md`). Each repair condition and its fix is in
ledger 9–10, and the measured evidence is in `build/cache/film_checks.json`. Also changed: the person is now one
body throughout (the Straight Talk roto, split at the hip and sat down on a hip pivot), so the Survival Stresses
figure is no longer used. The lamp law is identical inside and outside, which removed the light seam at the
threshold. The sill holdout is dilated by 1 px, which removed the dashed line.

## Round 2 repair (critic 2: PASS, narrow)

- **Across the sill**: the dog's centre is now 0.42 m nearer the house than the score's x, so about a third of its
  matte is past the threshold. The sill is a raised board (0.13 m), and its front edge visibly cuts off the forelegs
  and lower chest inside, through the holdout. The rump overlaps the right casing, which is correct because it is
  outside, in front of the casing. The tail hangs onto the porch.
- **Look-back (7.46–8.0 s)**: a profile head with the muzzle to screen-left, at the neck end.
- **Look-in**: the mask follows the dark back of the head and its pointed ear tips. A thin warm rim of hall light
  grazes the skull edge (upper 45 % of the head only).
- **Door light**: inside the cone the dog's dusk ambient gives way to a warm lamp colour (1.0, 0.62, 0.30).
- **Hind legs**: when lying they fold 105° forward, foreshortened, and are drawn behind the body.

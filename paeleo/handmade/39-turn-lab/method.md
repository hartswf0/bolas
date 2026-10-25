# SCION 39 · Multiview Drawing Substitution — Turn Lab · method

**Thesis.** A flat drawing of a dog cannot rotate. Squashing or mirroring it through edge-on is what makes the "giraffe", the
box and the tangle. This studio never rotates a drawing. It keeps a small **atlas of views**: profile, rear three-quarter and
rear, each drawn separately, with flips for the other side. A turn is a **substitution**: the next drawing replaces the
current one at the same pivots. Every frame of a turn is therefore a finished drawing of the dog. The defining passages are
the two turns, at 3.42 s (it turns its back) and 7.46 s (it turns back to look).

What would make it bland: a profile cut-out sliding back and forth, flipping left and right; labels doing the acting.

## The swarm, and what each role actually built

All roles were run by one agent. None of them is an independent person; see "honest evidence".

| role | artifact |
|---|---|
| view analyst | looked at the kit dog (Amateur Film New Jersey C, f000/f015/f030/f045) for markings and proportions; chose which views the scene needs (V0, V45, V90 and their flips; head H-45, H0, H45, H90) |
| new drawing curator | `build/dog.js` VIEWS and HEADS: hand-placed outline points, a standing and a lying drawing per rear view with the same point count, a separate lying-haunch drawing for the hind legs |
| pivot alignment engineer | `RIG` in `build/dog.js`: one table of canonical dog dimensions (neck base, tail root, shoulders, hips, standing and lying) projected into each view, so every view has its own pivots from the same body. Also the **parent-frame anchor**: the torso's area centroid is placed on the score's x in every view, so a swap never moves the body sideways |
| turn animator | `build/controller.js`: BODY_KEYS, HEAD_KEYS, REST_KEYS, blinks, ear flicks, a gait with feet planted from the distance travelled, and turn steps at every swap |
| identity continuity critic | `build/identity_loop.py` → `proof/identity_loop.json` (measured; see below) |
| independent rotation reviewer | **not run here.** The brief assigns an independent critic. `proof/reviewer_frame_index.json` lists the frames they should look at first |

## Native formal language, as kept in the project

- **Orientation states.** Body yaw ∈ {0, 45, 90, 135, 180} (0 = facing the door), one discrete drawing each. Head yaw is a
  continuous world angle, but what is drawn is always the nearest head view. Typed in `DOG.build(pose)`.
- **View-specific pivots.** `proj(th, X, Y, Z)` places the canonical landmarks for view `th` (oblique depth K = 0.25). The
  neck joint is computed from that view's neck base, so the head is always attached at its own view's pivot.
- **Topology correspondences.** The same part ids in every view: torso, saddle, pale chest, neck, collar, head, ear_near,
  ear_far, eyes, nose, tail, four legs or haunches. A part a view cannot show is left out, not faked: there are no eyes on
  H45 or H90, and the chest blaze appears only in profile.
- **Drawing atlas.** `proof/atlas_v3.png` (current), with `atlas_v1.png` and `atlas_v2.png` as the earlier states.
- **Turn transition choreography.** The head leads (attention), the body follows one view at a time (resistance and
  commitment), and the feet step at each swap (the turn happens on the floor). Within one view, interpolation is allowed
  where it is safe: lying (matched points, hind first), crouch, ears, neck and head pitch, tail. Interpolation never runs
  *between* views. The door leaf is the one continuous rotation in the film, because a door really is a plane.
- **Time base.** Score frames, 24 fps, t = i/24. The scene is aligned frame for frame (scene frame i = film frame i + 72).
- **Mapping.** Lateral u (m, door centre 0) = score x − 0.39. The camera is static. The dog walks 0.55 m out from the wall
  and steps in to 0.32 m as it turns into the doorway.

## How the dog moves through the score

- 0–1.0 watches in profile. 1.0–2.33 backs away from the call, crouched (score crouch 0.9), head and ears down, tail
  tucked, still facing the person. The feet walk backwards with the distance travelled.
- **3.42 the refusal turn** (call + reach). The head swings away first: H0 → H45 (3.46) → H135 (3.52) → H180 (3.62). The body
  follows: V0 → V45 (3.50) → V90 rear (3.58: the back faces the door and the camera) → V135 (3.71). It holds V135 standing,
  then lies down in V135 with its back to the door (4.2–5.0, hind first), then rests its chin, still facing away.
- 6.2 the door opens: one ear flicks toward the sound, and the dog does not turn. 7.4 the soft voice.
- **7.46 turning back.** The head comes first: H180 → H135 → H90 → H45 → H0, so it is looking at the open door by 7.64,
  over its shoulder, still lying. Then it rises (7.5–8.0), and only then does the body come round: V135 → V90 (8.10) →
  V45 (8.22) → V0 (8.34).
- 8.3–14.7 watches the open, lit door, the seated person and the low hand.
- 14.71–23.0 approaches in profile with the head held below the line of the back the whole way (neck angle −7°, head
  pitched down). The feet are planted (stride 0.55 m, duty 0.7), so the travel is in the steps.
- 22.95–23.1 at the door: head to H45, body to V45, so its front faces into the doorway. From 23.79 it lies down across the
  sill: forepaws and head inside the door frame, haunch and tail outside on the porch boards. It looks at the person (H0)
  and rests.
- **26.4 "Come in."** Ears up, head lifts and turns H0 → H45 → H90 into the lit room (26.55–26.76), held to 28.24, then it
  turns back and lays the chin down again (28.5–29.2). It stays.

## Invariants: measured on the film's own render

`trace.json` comes from an **id-mask pass** of every frame: the dog is redrawn in flat id colours at half resolution and the
pixels are measured. The x position is the centroid of the torso alone. Facing is measured from where the head pixels sit
relative to the torso. Posture is measured from the torso top above the dog's ground line. The `state` field is the
orientation controller's state: the choice being performed, which follows the score.

- `check_handmade.py`: **ALL OK**. I1: all six choices at dt = 0.000 (the performed state switches on the score frame).
  I2: min x 0.584, end x 0.585 (sill 0.56). I3: r = 1.000. I4: share turned 0.959.
- N1, anchor stationary across substitutions: max |Δx| of the torso centroid at a body swap is **1.4 px** (measured).
- N2, scale: the bbox height ratio at swaps is 0.92–1.28 (the larger values are head swaps that coincide with lifting the head
  from rest). The area ratio is 0.72–1.48, because a dog seen from behind covers less of the picture than one seen side-on.
  That difference belongs to the drawing, not to scale: the canonical heights are the same in every view.
- N3, identity features: the saddle is visible in every frame. The collar is visible in every frame except scene frame 181
  (7.54 s), where the head is in its rear view behind the lying body.
- Sound (measured from the synthesized mix, `proof/sound_levels.json`): the soft lines are 13.4 dB below the calls, and
  18.1 dB above the room tone.

## What failed and what changed (see ledger.jsonl)

1. The first atlas (v1) used an oblique K = 0.40. Lying three-quarter views read as sitting up, and the rear view was a tall
   stalk. K was dropped to 0.25 and V45/V90 were redrawn around the new projected landmarks.
2. The neck was a thin stalk with an un-inked wedge. It was widened and made its own layer, always drawn behind the torso.
3. Folded hind legs zigzagged above the back when lying (the IK picked the wrong knee). Joint choice is now by pose
   (forward when standing, low when lying). Lying hind legs still read as raised knees, so the hind leg is now **substituted**
   by a separate haunch drawing when lying. Hind legs are not folded.
4. The first ending lay in the V90 rear view. It read as a dog sitting in the doorway. It was replaced by V45 lying across
   the sill, diagonally, front in the frame and rump and tail out. The mapping changed from x − 0.59 to x − 0.39 so the
   final lie sits correctly.
5. The measured x jumped 10–20 px at swaps, and the end x read 0.517, failing I2. Cause: legs drawn over the torso changed the
   visible-pixel centroid. Fix: the body is anchored on the torso's area centroid in every view, and the trace measures a
   torso-only mask. Result: 1.4 px, and I2 holds.
6. At 3.6 s the back was not yet shown. The refusal turn now reaches V90 at 3.58.
7. The warm door light washed the saddle out near the door. It was reduced, and the cast shadow fades out near the door.
8. The title ran off the card, and the end card claimed a lying version for every drawing. The title was resized and the
   claim corrected.

## What is still weak (my view, not a verdict)

- The V90 rear drawing is narrow and tall next to the profile, and reads as a dark saddle on thin hocks. It is on screen for
  about 0.1 s in each turn.
- At V45 with the H90 head, the head is small and partly hidden behind the shoulders.
- The person is simple, and the seated legs read as one dark wedge. The step-aside is a quick front-view swap.
- The voice is a crude formant synthesizer. I cannot listen to it, so its intelligibility and character are unknown. The
  words are given as subtitles for that reason. Footfalls are synthesized pads placed at measured foot landings.
- The ink "boil" is very slight. The style is clean vector-drawn rather than visibly hand-drawn.

## Honest evidence

- **Measured:** every number above, the checker result, and the sound levels.
- **Looked at by the builder (not independent):** atlas proofs v1–v3, both turns frame by frame (scene frames 80–100 and
  176–208), the lying frames, stills every 0.5 s, and 22 frames extracted from the encoded `film.mp4`, including both cards.
- **Not done:** no independent critic run. No human viewing. No listening: I cannot hear the sound, and its quality is
  unknown beyond spectrograms and levels. No forked competing hypotheses for the turns; the first approach held up under my
  own viewing, so no fork was earned. Quick, Draw!, found frames and the archive door were not used.
- **Rights:** everything on screen and in the soundtrack was made here. The archive dog was used as a looking reference only,
  and its source is public domain (`assets.json`).

## Method library (technique → conditions → proof clip → failures → repair → rejected)

- **Substitution turn, head leads.** Use it for a flat character turning more than 45°. Proof: scene 3.42–3.80 and 7.46–8.40.
  It failed with a thin rear neck and a giraffe silhouette; repaired with a shorter, wider neck layer behind the torso.
  Rejected: squash-through-edge-on, mirror at 90°.
- **Anchor on the torso centroid.** Use it whenever views differ in shape. Proof: N1 = 1.4 px. It failed at first because
  the pixel centroid was occluded by legs; repaired by measuring a torso-only pass.
- **Part substitution inside a pose** (haunch for a folded hind leg). Use it when an interpolated joint cannot read. Proof:
  the lies at 4.2–5.0 and 23.8–24.6.
- **Planted gait from distance.** Feet are fixed while in stance. Proof: the approach. Weakness: swing feet stop mid-air if
  the dog stops mid-step, so lift is scaled by speed.

## Rebuild

`bash build/make.sh` runs controller → render (Playwright/Chromium canvas) → trace → sound → assemble (ffmpeg) → identity
loop → `check_handmade.py`. The intermediates go to `build/cache/` (git-ignored).

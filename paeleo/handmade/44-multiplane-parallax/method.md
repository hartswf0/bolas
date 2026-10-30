# SCION 44 · Multiplane Parallax (spatial collage swarm): method

## Thesis and the defining passage

Space is the medium. The threshold is a stack of cut planes at measured depths, and the camera only translates through that
stack (it never rotates). Depth comes from parallax, occlusion edges and focus, not from a painted backdrop. The defining
passage runs from 26.4 to 28.5 s. The dog lies across the sill. The camera passes through the railing plane and comes down
low behind it, and the dog turns its head into the lit room. We see the back of its head and both ears against the room
floor, and the room (lamp, table, picture, bowl) slides behind the door jamb at its own deeper rate. The result would be bland
if the room were a flat backdrop pasted into the door hole, or if the dog were one flat card.

## The planes (build/world.py; full list with depths in proof/scene_graph.json)

| plane | depth Z (m; wall = 0) | made from (all public domain unless noted) |
|---|---|---|
| sky | 140 | a dusk gradient, with torn bands of cumulus from *Top Of The Cloud* graded to dusk; the moon is a real Quick, Draw! drawing (CC BY 4.0, key_id in assets.json) |
| far trees | 46 | dark pines luminance-keyed from the Golden Gate windmill footage (tree-only boxes), feathered, flipped and repeated |
| near trees | 16 | the same source at a larger scale and darker |
| yard | ground quad, Y = −0.5 | Blackwater refuge reeds, tiled and darkened |
| room back wall | 3.6 | plaster grain from the warm wall behind the *Anthracite* lantern; the windmill frame as a picture on the wall |
| room floor | quad, Z 0 to 3.6 | boards with grain from the corral logs of *Billie, the Buffalo Baby*; the bowl from *Amateur Film New Jersey C* |
| lamp and table | 2.3 | the bulb from *Light Of Your Life* (masked), a table drawn as a silhouette |
| door leaf | quad on a hinge | the white door with the curtained window, cut from *Straight Talk*; 46° (ajar) to 102° (open) from 6.2 s |
| curtain | 0.06 | the curtain from the same door, translucent |
| house wall | 0 | clapboards carrying the grain of the *Straight Talk* door; the door opening and the window are holes (occlusion edges) |
| porch floor | quad, Z −2.1 to 0 | boards laid along Z, so they converge on the vanishing point |
| steps | −1.0 | stone from the gate pillar in the home movie |
| porch front | −2.1 | edge board (logs) |
| railing | −2.1 | posts, bottom rail and beam cut from the logs; this nearest plane works as a shield |

Parallax ratios at 19 s, in pixels of screen motion per metre of camera truck: sky 7, far trees 20, near trees 48,
room wall 120, lamp 143, house wall 213, the dog's plane 253, railing 385. These are computed from the camera track
(f = 1000 px) and are structurally exact. Focus follows the dog. Each card plane is pre-blurred at four levels and
the level is chosen by circle of confusion, so the railing and the sky soften when the dog is sharp. Fog is set per plane.

Camera track (common.CAM_KEYS, pchip):
- 0 to 7.4 s: wide, so the call, the retreat, the refusal, the person sitting and the door opening all stay in one frame.
- 7.4 to 14.6 s: crane down behind the railing.
- 14.6 to 23.7 s: truck left with the approach, slower than the dog, and push in.
- 23.7 to 26.3 s: settle at the sill.
- 26.3 to 28.5 s: pass through the railing plane, low (0.5 m), centred on the door.

## The dog: a stack of collage pieces at their own depths (build/dog.py, render.draw_piece)

The dog is 30 paper pieces. Each one is cut from the real dog of *Amateur Film New Jersey C*: its tawny flank, its dark
saddle, its pale chest, its face, and the darker muzzle and nose. The pieces are:
- legs: upper, lower and paw for each foreleg; thigh, shank, metatarsus and paw for each hind leg
- body: flank, saddle, chest, rump, and three tail pieces
- head: neck, ruff, skull, muzzle, nose, two eyes and two ears

Each piece is a tapered capsule or a triangle. Its outline gets fixed per-piece scissor jitter, a pale cut rim, paper
grain and a drop shadow, and it is laid on a 3D point of a small skeleton. Every piece is a film-parallel card at its own
depth, sorted with all the other layers, so when the camera moves the near legs slide against the far legs and the head
against the chest. The parts separate in depth by up to about 0.2 m. The head pieces have depth > 0 at the end, so the
wall jamb occludes them correctly.

Turns are real rotations of the skeleton, and the pieces re-stack as it turns. Facing us, the chest and the face come in
front. Looking into the room, the muzzle goes behind the skull and the neck, so the back of the head shows. Nothing is
mirrored or squashed edge-on.

- **Feet.** A planner keeps planted feet fixed in the world. A foot steps only when its target has moved more than 7 cm, and
  only while its same-girdle partner is planted. The same plant events trigger the nail clicks in the sound.
- **Legs.** Two-bone IK (inverse kinematics).
- **Lying.** Forelegs flat forward, hind legs folded beside the hip, tail on the boards outside.
- **Acting.** Lie, crouch, ear, tail, wag, rest and head height come from the score's `act`. Three things are re-timed:
  - The refusal turn is done by 3.80 s. The head leads and is done by 3.64 s. The dog ends at 378° (rear to the door,
    three-quarters away from us), so we see its back.
  - At 7.458 the head swings round to the door (to 186°) in 0.2 s while the body is still down. The body rises, then turns
    from 7.85 to 8.75 s.
  - At 26.4 the head turns to 88° (straight into the room, +Z) in 0.32 s. The head lift is capped, so this is a turn
    into depth, not a lift toward the light. At 28.45 the head settles back down onto the paws.
- **Approach path.** The head is pitched −26°, clearly below the line of the back. The path bends in depth over the last
  metre and ends with the root at Z = −0.18. The head and forepaws end inside the door frame (Z > 0, |x| < 0.46) and the
  hindquarters and tail stay on the porch.

The person is built the same way: smock, hair, sleeve and trousers from *Straight Talk*, and the offered hand from *The
Door to Heaven*. The head is a cut-paper profile, drawn by code, so no face is shown. The person is backlit by the room.

## Measured, not assumed (trace.json, invariants.json)

**How the trace is measured.**
- *Position.* Per frame the renderer keeps a dog pass: the alpha of the dog pieces after every nearer occluder. The
  flank, saddle, skull and nose pieces are recorded as laid and unprojected at the depth they were laid at.
  - `x_world_measured` is the torso piece's world X. Its correlation with the score's x is 1.000. This is nearly
    tautological, because the torso is laid where the score puts the root.
  - `x_centroid_world` is the dog-pass centroid unprojected at the root depth. Its correlation is 0.9998, with a maximum
    offset of 0.10 m.
- *Facing.* From skull to nose as laid.
- *Posture.* From the height of the back.
- *State.* Classified only from those measurements:
  - speed of the torso
  - facing
  - back height
  - head above or below the back
  - nearness to the sill

**Measured onsets vs the score** (all within ±0.25 s; the checker reports ALL OK):

| choice | score t (s) | measured t (s) | dt (s) |
|---|---|---|---|
| retreat | 1.000 | 1.167 | +0.167 |
| watch | 2.333 | 2.417 | +0.084 |
| refuse | 3.417 | 3.542 | +0.125 |
| watch | 7.458 | 7.583 | +0.125 |
| approach | 14.708 | 14.625 | −0.083 |
| lie_down | 23.792 | 23.917 | +0.125 |
| looks in (muzzle within 22° of +Z) | 26.4 | 26.542 | +0.142 |

**Other checks.**
- The head is inside the door frame in 50 of 50 frames from 26.7 to 28.7 s.
- During the refusal, 100% of the frames have the dog facing away.
- The smallest share of the head left visible behind occluders is 0.55, at 17.9 s, behind a railing post.
- The dog is in every frame: the smallest dog pass is 6,739 px.
- There is one one-frame classification blip, 'approach' at 3.50 s, where the torso centre swings during the refusal turn.

**Film and sound.**
- The film is 912 frames (768 scene frames), H.264 + AAC with faststart, 3.7 MB.
- Sound (proof/audio_levels.json) is measured on the mix and checked again on the decoded film audio:
  - calls are about −19.5 dBFS
  - soft lines about −31.8 dBFS (12.3 dB quieter)
  - the wind bed is −41 dBFS
  - "come in" alone is about 7 dB below the calls on the film audio

**What was looked at.** I looked at frames extracted from film.mp4: a contact sheet, crops of both turns frame by frame,
the approach, the last 8 s, and the four stills. The full film was not watched at normal speed. Nobody has listened to the
sound; only its levels were measured.

## What failed and what changed

The full record is in ledger.jsonl.
- **Wall.** Clapboards collaged from mixed sources read as noise with black gaps. They are now continuous boards that keep
  only the found grain.
- **Trees.** The tree boxes carried windmill sails. They are now tree-only boxes, feathered.
- **Top rail.** The top rail cut across the dog's head when the camera craned down, so I removed it.
- **Forelegs.** The lying forelegs folded upward. They are now laid flat.
- **Frontal view.** The frontal view was tall and narrow. The legs are now wider apart, the body bulkier, and the head lower
  while the dog faces us.
- **Person.** The person read as a robot. The head is now a profile silhouette.
- **Lamp.** The lamp glow and a repeated dark object in the plaster made smudges. I fixed the glow fill and changed the
  plaster crop.
- **Onsets.**
  - A centroid-based speed called the dog rising "approach" at 7.6 s, and the late head turns put the refuse and watch
    onsets near the tolerance. The speed now comes from the laid torso piece, and the head turns are faster.
  - Retreat flickered. It is now defined as backing away with the head below the back.
  - The refusal heading went from 360° to 378° so that its back is what we see.

## Repair round (after the independent critic: PASS, narrow)

- **Head versus tail, 3.9–7.4 s.** The head pieces (skull, neck, muzzle, ears) now carry a warm lit cut rim, and the ears are in the tan face fragment. The tail is in the pale flank fragment, thinner and tapered. The near-black yard and tree-ground field behind the dog was lifted to a mid dusk grey-blue. I checked film frames at 4.0, 5.5 and 7.0 s, and the rimmed head reads distinctly from the pale tail.
- **Credit.** The end card now credits the moon to the Quick, Draw! dataset by Google Creative Lab and contributors, CC BY 4.0, with its key_id.
- **Optional fixes.**
  - Tail taps lowered: on the film audio, 26.4–27.4 s now peaks at −19.1 dBFS against a −6.6 dBFS call peak.
  - Bulb scaled to 0.27× the table width.
  - The head-lead onset was left unchanged; its first door-facing frame is 7.583 s.

## What is weak and what I did not do

- **What is still weak.**
  - The dog is small (about 150 px) in the wide first 14 s.
  - Its legs read as tubes with round joints, which is a cut-paper puppet idiom. The hind leg is simplified.
  - From behind, lying at the sill, its body is a lumpy stack. The near thigh disc dominates.
  - The person is crude.
  - The voice is a formant synthesizer, so the words are only roughly intelligible.
- **What I did not do.**
  - No independent critic was run. This work is not self-approved.
  - No operator page was made.
  - No forks were compared.
  - There are no typed prompts on screen.

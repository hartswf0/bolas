# SCION 11 · Connelly Barnes, Video Puppetry Tabletop: the threshold

**Swarm:** 11, Connelly Barnes, *Video Puppetry: A Performative Interface for Cutout Animation* (2008). This is a prompt inspired by that work. It is not a claim that the authors made or endorsed it.

**Thesis.** Barnes's puppets are paper cut-outs that the camera tracks as rigid pieces. Here the cut-out is a strip of real home movie. The dog is the actual dog from *Amateur Film New Jersey C*, a public-domain home movie in the kit. Two frames of it are cut out with their masks. Every pose in the film is made by **bending those pixels**: rigid moving-least-squares deformation driven by named control handles. The footage bends; nothing about the dog is drawn. The world around it is a tabletop stage of cut card. The person is a jointed paper puppet with one real hand, cut from public-domain film. A plain version would be one that swapped frames from the clip and called them animation. Here the clip supplies only two drawings' worth of pixels, and every motion comes from deforming them.

## Native formal language → what is in the project

| primitive | here |
|---|---|
| paper cut-outs | dog keys L (kit frame 6) and F (frame 38), plus their mirrors R and F'; the forearm and hand; the stage cards; the person's card pieces |
| per-piece masks | each dog key is split into body, rigid head and four legs: `build/puppets.py`, `proof/handles_*.png` |
| tracked transforms | 24 named handles per dog key (source px → canon puppet space → screen); the person's pieces move by rigid transforms; the hand moves by a two-point similarity |
| background stage | `build/stage.py`: card layers with jittered edges, fibre texture and drop shadows; a door card hinged on the jamb |
| recorded performance graph | `data/performance.json`: the editable performance clip, one record per frame (dog x, turn axis k, pose channels, gait feet; person; door). Edit one channel and re-render, and nothing else changes |
| hand occlusions | none of the puppeteer's hands appear; the only hand on screen belongs to the character |
| overhead camera | one fixed, slightly high tabletop camera, with a vignette and grain |

**Coordinates and time.** The film runs at 24 fps, frame-locked to the score (scene frame i = score frame i). Screen x of the dog's anchor is 320 + 200 px/m × x_score. The threshold x=0 is the door's centre line, and the door opening (−0.46 to 0.46 m) is the 228–412 px hole in the wall card. The ground line runs at y=612 and draws in to y=530 (the sill) over the last metre, with scale shrinking 16% toward the wall.

## How the dog is built and moved (`build/rig.py`)

- **Pose controls → handle targets.** These are written in canon space (facing left, anchor at the belly point on the ground). The controls are crouch (the top line sinks, the knees give), lie (the body lowers to the floor, the forelegs reach forward, the hind legs fold forward), head (rotation about the root of the neck, capped at 68°; lower than that, the neck reaches down), rest (chin on the floor), look (head level, pushed into the doorway, muzzle shortened, darkened), tail and wag (rotation about the tail root), and feet (gait offsets).
- **Bending.** Each piece is warped backwards, so that every film pixel asks where it came from in the kit frame. The warp is rigid MLS in complex form: weights 1/d^2.3 for the body and 1/d^3.2 for each leg (3 handles each). The head is rigid, and the neck under it follows 35% of the head's rotation. Draw order: far legs, body, near legs, head.
- **Walking.** This is a four-beat walk with a 0.46 m stride and 65% stance. In stance a foot's offset is exactly the negative of the body's travel, so held feet do not slide. That is true by construction, not measured in the image. The same function runs backwards for the retreat, so the feet step backwards.
- **Turning.** The turn axis runs L → F' → F → R. The profile and three-quarter keys morph into each other: handle positions interpolate, and the two images dissolve over the middle 16% of the segment. F' and F are mirror images. Morphing between them folded the face (ledger 2), so they are **swapped like cut-outs** at their own shapes, with a slight narrowing as the face passes the camera. The refusal turn runs 3.42–3.86 s and is fully turned by 3.86. The turn back runs 7.46–7.96 s, rising as it turns, and the face is toward the camera and then the door by about 7.6–7.7 s.
- **No lying dog in the source.** The lying poses are bends of the standing frames (front legs rotated forward onto the boards, hind legs folded).

## Measured, by what

- `trace.json` is measured on the rendered silhouette (alpha > 0.5) and on where the head piece's pixels landed. Onsets, each found on a signal named in the trace:
  - retreat 1.000 s (Δ 0.000)
  - watch 2.333 (0.000)
  - refuse 3.417 (0.000)
  - watch 7.458 (0.000)
  - approach 14.792 (+0.084)
  - lie down 23.792 (0.000)
  - looks in 26.417 (+0.017)

  The zeros arise because the performance starts each move on the score's frame and the measures fire on the first pixel of movement.
- Checker: **ALL OK**.
  - I3: correlation of x_screen with x_score is 0.9999.
  - I4: facing measured from head versus centroid; the turned back holds through the refusal except 4 frames mid-turn.
  - Final frame: lying, with 45% of the silhouette's pixels inside the door frame's x-span and the tail outside.
- Sound, measured in film.mp4 with ffmpeg volumedetect:
  - calls −17.6 dB
  - soft lines −32 dB (14 dB quieter)
  - room tone −47 dB (soft is 15 dB above it)

  The synthesis-side numbers are in `data/sound_levels.json`.
- Frames: 768 scene frames and 912 film frames, 38.0 s, H.264 + AAC, faststart, 11.06 MB.
- **Numeric invariant that does not fully hold:** "the footage bends but never folds" (the Jacobian determinant of the warp is > 0 inside every piece). It is measured per frame (`warp_det_min`). It is violated somewhere in 324 of 768 frames, and below −0.5 in 31. The violations are local folds, mostly in the lying legs and the compressed walking legs. I did not measure how many pixels they cover.

## Looked at (perceptual, by me, the builder; not a verdict)

Contact sheets of 20 film times, 1:1 crops of the turns (`proof/turn_*.jpg`), the look-in (`proof/look_in_*.jpg`) and the stills. The refusal turn and the turn back read as the same dog through a three-quarter view toward the camera. The approach carries the head below the back. The lying dog is across the sill with its head against the lit room.

## What is weak

- The dog is small in a wide fixed shot (about 230 px long). The source is 384×288 home movie, so its detail is soft.
- The mid-turn frames are blobby. Swapping F' for F is a one-frame jump of the face.
- The lying legs are the least convincing part: they fold, as measured above.
- The voice is formant synthesis and sounds synthetic.
- Ears and mouth have no control.
- The person's paper body is plain.

## What I did not do

There was no physical tabletop, no live capture, and no puppeteer: the performance is computed from the score. Preview latency was not measured, because nothing here is live. No independent critic has seen this yet. I did not use the kit's door footage or the Quick, Draw! drawings. I did not use a camera move.

## Rebuild

`build/make.sh` runs puppets → stage → perform → render → trace → sound → cards → assemble → checker, and then deletes the rendered frames.

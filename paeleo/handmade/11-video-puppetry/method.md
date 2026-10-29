# SCION 11 · Connelly Barnes, Video Puppetry Tabletop: the threshold

**Swarm:** 11, Connelly Barnes, *Video Puppetry: A Performative Interface for Cutout Animation* (2008). This is a prompt inspired by that work. It is not a claim that the authors made or endorsed it.

**Thesis.** Barnes's puppets are paper cut-outs that the camera tracks as rigid pieces. Here the cut-out is a strip of real home movie. The dog is the actual dog from *Amateur Film New Jersey C*, a public-domain home movie in the kit. Two frames of it (6 and 38) are cut out with their masks. Every pose is made by moving those pixels: the body sheet is bent by moving-least-squares deformation, and the head, tail and legs are rigid pieces of the same frames turned at their joints. The footage bends; nothing about the dog is drawn. The world around it is a tabletop stage of cut card. The person is a jointed paper puppet with one real hand, cut from public-domain film. A plain version would be one that swapped frames from the clip and called them animation. Here the clip supplies only two drawings' worth of pixels, and every motion comes from deforming them.

## Native formal language → what is in the project

| primitive | here |
|---|---|
| paper cut-outs | dog keys L (kit frame 6) and F (frame 38), plus their mirrors R and F'; the forearm and hand; the stage cards; the person's card pieces |
| per-piece masks | each dog key is split into a body sheet (bends), and head-with-neck, tail and four legs (rigid): `build/puppets.py`, `proof/handles_*.png` |
| tracked transforms | 24 named handles per dog key (source px → canon puppet space → screen); the person's pieces move by rigid transforms; the hand moves by a two-point similarity |
| background stage | `build/stage.py`: card layers with jittered edges, fibre texture and drop shadows; a door card hinged on the jamb |
| recorded performance graph | `data/performance.json`: the editable performance clip, one record per frame (dog x, turn axis k, pose channels, gait feet; person; door). Edit one channel and re-render, and nothing else changes |
| hand occlusions | none of the puppeteer's hands appear; the only hand on screen belongs to the character |
| overhead camera | one fixed, slightly high tabletop camera, with a vignette and grain |

**Coordinates and time.** The film runs at 24 fps, frame-locked to the score (scene frame i = score frame i). Screen x of the dog's anchor is 320 + 200 px/m × x_score. The threshold x=0 is the door's centre line, and the door opening (−0.46 to 0.46 m) is the 228–412 px hole in the wall card. The ground line runs at y=612 and draws in to y=530 (the sill) over the last metre, with scale shrinking 16% toward the wall.

## How the dog is built and moved (`build/rig.py`, after the critic's repair round)

- **Only the body sheet bends.** The torso is bent by rigid moving-least-squares deformation on 12 body handles, backward-mapped (each film pixel asks where it came from in the kit frame). Weights are 1/d^2.3.
- **The rest are rigid cut-outs of the same frame, pinned at joints.** Head-with-neck is cut off along a neck line and the tail along a tail line. The four legs are split below a belly line by distance to each leg's axis. Each piece is placed by the least-squares rigid fit of its own handles to their targets. Big moves are joint rotations, not bends, so they cannot tear: the head going down to 57° for the approach and 72° for chin-on-floor, the legs folding for the lie, the tail tucking. This is Barnes's jointed paper puppet, with real footage as the paper. In version 1 a single sheet bent this far tore: there was a crescent swirl at the head and folded legs (ledger 1–3, 7).
- **Walking.** This is a four-beat walk with a 0.46 m stride and 65% stance. Each leg swings rigidly about its top so that its foot sits where the planner puts it, and in stance that place exactly cancels the body's travel. The body is let down by the stance feet's rise. The retreat runs the same function backwards.
- **Lying.** There is no lying dog in the source, and the brief's lesson asks for no standing legs. The body sheet goes down level (hindquarters as low as the shoulders). Going down or getting up, the rigid legs stay vertical under the body, and the porch boards hide what passes below them. At the end the near foreleg goes forward onto the boards. The far and both hind legs fade out under the lying body. Masks are cleaned by binary closing plus 1.6 px smoothing. The neck piece overlaps the body by 10 px, so there is no seam at the neck cut.
- **Approach.** The head drop is spread over 5 frames from 14.58. The head top, ear tufts included (any pixel with a trace of the head), is at least 6.9 px below the withers line throughout 14.9–23.6 s (measured).
- **Turning to look (7.46).** Still lying with its back turned, the dog's head piece is cut to the unmirrored profile head: muzzle left, toward the door, low and level, pinned where the head was. This is the head turned round over the shoulder, and it holds to 7.92. The body lies until 7.78, rises over 7.78–8.08 and turns through the three-quarter keys over 7.80–8.25.
- **Looking in (26.4).** The kit has no clean back of the head: a kit-frame-0 piece tried in rounds 1–2 read as a lump and has been retired. So the brief's other option is used. The profile head is held level (never lifted) and the neck reaches 24 px in over the sill, so the muzzle and ear sit inside the door frame against the lit room. There is no head swap, so there is no double head.
- **Turning.** The turn axis runs L → F' → F → R. Profile and three-quarter keys morph into each other: handle positions interpolate, and the images dissolve over the middle 16% of a segment. F' and F are mirror images, so they are swapped like cut-outs with a slight narrowing as the face passes the camera. The refusal turn runs 3.42–3.86 s.

## Measured, by what

- `trace.json` is measured on the rendered silhouette (alpha > 0.5) and on where the head piece's pixels landed. Onsets, each found on a signal named in the trace:
  - retreat 1.000 s (Δ 0.000)
  - watch 2.375 (+0.042)
  - refuse 3.417 (0.000)
  - watch 7.458 (0.000)
  - approach 14.708 (0.000)
  - lie down 23.833 (+0.041)
  - looks in 26.417 (+0.017)

  The zeros arise because the performance starts each move on the score's frame and the measures fire on the first pixel of movement.
- Checker: **ALL OK**.
  - I3: correlation of x_screen with x_score is 0.9999.
  - I4: facing measured from head versus centroid; the turned back holds through the refusal except 4 frames mid-turn.
  - Final frame: lying, with 38% of the silhouette's pixels inside the door frame's x-span and the tail outside.
- Sound, measured in film.mp4 with ffmpeg volumedetect:
  - calls −17.6 dB
  - soft lines −32 dB (14 dB quieter)
  - room tone −47 dB (soft is 15 dB above it)

  The synthesis-side numbers are in `data/sound_levels.json`.
- Frames: 768 scene frames and 912 film frames, 38.0 s, H.264 + AAC, faststart, 7.29 MB (the last build re-encoded the scene once from the previous encode to correct the end card; ledger 18).
- **Numeric invariant "the footage bends but never folds"** (the Jacobian determinant of the body-sheet warp is > 0 inside the sheet), measured per frame as `warp_det_min`:
  - Version 1 broke it in 324/768 frames.
  - After the repair it breaks it in **6/768**, all inside the turn morphs.
  - Rigid pieces cannot fold.
- **Repair 4, measured on the render:** from 14.8 to 23.7 s, the top of the head pixels sits below the withers line in **213/213** frames (ear tufts counted; at least 6.9 px below in 14.9–23.6) (`head_top_px` against `withers_line_px` in trace.json).
- The dog's right edge stays ≤ 1232 px in 4.4–7.4 s, and the corner post now starts at 1262 px.

## Looked at (perceptual, by me, the builder; not a verdict)

Contact sheets of 20 film times, 1:1 crops of the turns (`proof/turn_*.jpg`), the look-in (`proof/look_in_*.jpg`) and the stills. After the repair: full-resolution crops of the refusal lie, the sill lie, the look-in and the approach (`proof/repair3_*.jpg`, extracted from film.mp4 itself), and look-in frames extracted from film.mp4 itself. The look-in reads as a dark back of a head against the lit room at 26.55–27.8 s. Since round 2 there is no dissolve: the swap is one cut each way.

## What is weak

- The dog is small (about 230 px long) in a wide fixed shot, and soft (384×288 source).
- The chin-down head at the sill (28.4 s onward) is a dark, blurry mass rather than a crisp muzzle, ear and eye.
- The turned-round head at 7.46–7.92 is small and grey against the dog's own dark ruff. At film scale it is legible but not crisp.
- While the dog goes down (about 4.4–4.7 s) the vertical leg, cut by the boards, looks blocky for a few frames.
- The mid-turn frames are blobby, and the swap between F' and F is a one-frame jump.
- The rigid legs swing like a paper puppet's: there is no knee bend.
- The voice is formant synthesis and sounds synthetic.

## What I did not do

There was no physical tabletop, no live capture, and no puppeteer: the performance is computed from the score. Preview latency was not measured, because nothing here is live. Three independent critic rounds have judged it (DOES NOT PASS each time, with repairs since); this version has not been re-judged. I did not use the kit's door footage or the Quick, Draw! drawings. I did not use a camera move, and I did not add a visible puppeteer's hand (optional in the critique).

## Rebuild

`build/make.sh` runs puppets → stage → perform → render → trace → sound → cards → assemble → checker, and then deletes the rendered frames.

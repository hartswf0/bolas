# SCION 45 · Occlusion Compositing — who is in front? · PAE-02 cohort 3

**Thesis.** A threshold is an occlusion problem. Whether the dog is outside, at the door or in it is decided, frame by
frame, by *who is in front of whom*: the dog in front of the porch post or behind it, the person's arm in front of the
door casing or behind it, and at the end the dog lying across the sill with its hindquarters in front of the right-hand
jamb and its forequarters behind it, in the doorway. The defining passage is that last image: one body that is both behind
and in front of the same piece of wood, which a single global z-order cannot draw. The bland version would be a dog
pasted over a door.

## The swarm (one agent, roles merged)

I worked alone; the SCION roles were merged because every one of them touches the same per-frame record. Each built or
checked a concrete artifact:

| role | artifact |
|---|---|
| Matte artist | `build/cels.py` (dog cels: SAM matte AND hand garbage mattes), `build/rig.py` PARTS (holdout polygons that split a cel into head / torso / legs), `build/plates.py` |
| Layer dependency engineer | `build/scene.py`: typed RGBA layers with depth (scalar or per-pixel depth pass), the occlusion DAG built from overlaps every frame, topological compositing, splitting into semantic sublayers by an object's own depth pass |
| Scene continuity agent | `build/dog.py` (which real frame or which re-assembled pose at each score frame), `build/person.py` |
| Shadow designer | the light pass (doorway light through the leaf as a holdout, actors' cast shadows), contact-shadow pass, in `scene.py` |
| Render verifier | `render.py` (re-composites every 4th frame by per-pixel depth test and compares with the DAG composite), `measure.py` (trace, onsets, assertions) |
| Independent spatial critic | **not me.** Nothing here is approved by the builder; the critic has not yet seen the film. |

## Native formal language, kept as first-class state

- **RGBA layers.** Every element is a premultiplied RGBA layer with a type (`sky`, `back`, `wall`, `frame`, `support`,
  `prop`, `actor`) and a source. Coordinates: world metres, `x` along the porch (the score's x; the doorway spans
  x in [-0.46, 0.46]), `D` depth in front of the wall (inside the house is D < 0), `h` height. Stage camera is
  cabinet-oblique: `X = 640 + (x - fx)·s`, `Y = 360 + (0.38·D - h + fh)·s`, keyed in `CAM_KEYS`. Time base: score frame
  `i` at 24 fps.
- **Occlusion DAG.** For every pair of layers that overlap on screen, an edge far→near is decided from depth at the
  overlap pixels; supports (porch floor, sill) sit under what stands on them; the room sits behind anyone in the doorway.
  The frame is composited in topological order. Each frame's order, edges and overlaps are in the render record.
- **Holdout mattes.** The wall's opening is its holdout; the door leaf is a holdout for the doorway light; the casing
  holds out the dog's loin and the person's hand; the porch post holds out the walking dog at 18 s.
- **Depth/alpha passes.** The dog, the person and the leaf carry per-pixel depth. Where an object is both behind and in
  front of the same occluder, it is split by its own depth pass into `_in` (behind the casing plane D = 0.04 m) and
  `_out` sublayers, never forced into one z. Each frame records whether the merged object would have made a cycle.
- **Contact shadows.** The lowest band of each actor's alpha flattened onto its support and blurred; drawn into the
  floor, sill and room-floor layers, so every occluder in front of the dog also holds out its shadow.
- **Overlap events.** Per frame: who hides the dog and by how many pixels; per pair of layers, when the edge between them
  flips. Intervals are in `measured.json` (`dog_hidden_by`, `person_vs_frame`).

Numerical invariant (tested): the DAG is acyclic every frame, every order flip happens with zero overlap (no pop), alpha
is valid, the per-pixel depth re-composite agrees with the DAG composite. Artistic achievement (only by viewing): the
lying dog reads as half in the doorway and half out, because of the jamb, not because of a label.

## The dog: what it is made of, and how it moves

Every visible pixel of the dog is a pixel of the real dog in *Amateur Film New Jersey C* (Home Movies, Internet Archive,
public domain), from the kit's 50 frames and SAM masks. Nothing of it is drawn; it is re-lit (its luminance is coloured by
the dusk ambient and the doorway light, plus a rim pass).

- **Substitution of real frames.** The footage contains a real turn: left profile (f0-19), facing the camera (f22-35),
  right profile with the head low (f40-47). The refusal turn (3.42 s) plays the dog's own turn, one real frame per film
  frame, through the camera-facing frames (`TURN_AWAY`), so it is never a mirror flip or a squash. The turn back
  (7.95-8.8) goes the other way: two camera-facing frames, then 3/4 and profile frames with the head on the door side
  (`TURN_BACK`). Profile cels are registered by the rump, which barely moves when the head does, so a head change never
  slides the body; camera-facing cels by their centre.
- **Re-timed walks.** The head-low walk is f43-45 (round 2: f42, f46, f47 dropped), shown mirrored as a whole pose so it faces the door; from score x = 2.05 to the
  sill (round 3) the frame-10 profile parts walk instead, legs swinging 15° about their upper pivots, so the same parts then lie down. The cel index is
  the distance travelled divided by a 0.30 m stride (three cels per stride), so the drawings account for the travel; backing
  away plays the same cycle backward.
- **Re-assembled parts.** The footage has no lying dog. Lying is built from frame 10 cut into five sublayers (head, torso,
  near foreleg, far foreleg, hind lower leg) by hand-authored holdout polygons, plus the bushy tail cut from frame 2
  (frame 10's tail is hidden behind its leg), rotated about pivots: the hind end goes down first, then the chest; the
  forelegs lie forward, the hind paw tucks under, the tail is laid out on the boards and sweeps with the score's wag. The head turns are substitutions of
  head sublayers: profile away → frontal head (f28) → profile toward the door laid over the shoulder (7.46-7.6), and, for
  *looking in* (round 2), the real head of frame 0, where the archive dog is seen three-quarters from behind looking up
  and away: its ear and the back of its skull toward the camera, tilted into the lit hall (T: the same cut at 78% width
  mid-turn; B: full width).
- **In depth.** The lying body is angled 31° into the doorway (its depth pass slopes 0.6 m per m) and its depth pass
  crosses the casing plane (D = 0.005 m) at x = 0.575 m, at the right jamb's outer edge: `dog_in < jamb_R < dog_out`.

Mapping: the dog's body centre in world metres is `x - 0.14` (one fixed offset for the whole film), so the approach covers
the score's distance at the score's pace; the last 1.3 m it angles in toward the doorway. The dog is scaled to a big dog
(shoulder about 0.70 m). Of the kit's 50 frames, 19 are composited (`build/cache/cels_used.json`, `assets.json`).

Camera: a fixed-lens stage camera that only reframes (`CAM_KEYS`): the caller and the dog in one frame for both commands
(0-4.7 s), out to take in the bench and the door as it opens (5.9-7.0) and holding that two-shot (round 2: no push at the turn back, so the person stays
in frame) through the waiting, then it follows the approach in to the sill and
closes slowly on the threshold to the end. Because it moves, the trace carries `x_world_measured`.

## The person, the house, the sound

The person is the one element that is a matte and nothing else: a dark shape drawn here (capsules from a small joint set),
rim-lit by the doorway; only the offered hand is a real image (*Door to Heaven*, 1941). It calls pointing at the boards,
calls again and reaches (the reaching arm comes out in front of the casing: the person is split too), steps out and sits
on a bench beside the door, reaches round the left jamb to push the door (its hand behind the jamb, on the leaf), and
offers the hand low. The hallway seen through the door and the door panel are from *Straight Talk* (NTIS), the bulb from
*Light Of Your Life B*, the sky from *Top Of The Cloud*. The house, porch, sill, casing, bench and post are drawn.

Sound is composited like the picture. The voice is synthesized (flite `slt`, run locally). The room (lamp hum, a clock) is
a sound layer *behind the door*: while the door is ajar it is held out (low-passed, -14 dB); when the door opens the
holdout lifts. Foley comes from the dog's own substitutions (a claw tick at each walk-cel change, a scuffle on the turn,
the body meeting the boards). Measured (not listened to): see `build/cache/audio_levels.json` and the numbers below.

## Measured, looked at, unknown

**Measured on the render** (`measure.py` → `trace.json`, `measured.json`; `check_handmade.py` → `invariants.json`):

| choice | score t (s) | measured onset (s) | dt | measured by |
|---|---|---|---|---|
| retreat | 1.000 | 1.0 | +0.000 | head drops below the line of the back (dog alpha: front-quarter top vs middle top) or its measured position moves back |
| watch | 2.333 | 2.333 | +0.000 | head back above the line of the back |
| refuse | 3.417 | 3.417 | +0.000 | the dog's own pixels change three frames running (the real turn starts) |
| watch | 7.458 | 7.458 | +0.000 | first movement of the lying dog's pixels (the head comes up); the composited head looks to the door from 7.54 |
| approach | 14.708 | 14.708 | +0.000 | head drops below the line of the back, or it moves toward the door |
| lie_down | 23.792 | 23.958 | +0.166 | the dog alpha's height falls three frames running (it goes down, hind end first) |
| looks in | 26.400 | 26.5 | +0.100 | top of the lying dog rises as the head turns into the doorway (h_top); what turns is judged by viewing |
| settles and stays | 28.300 | 28.208 | -0.092 | back-of-head pixels gone; chin back down |

- PAELEO invariants: **ALL OK**. I1 all six within ±0.25 s (dt 0, 0, 0, 0, 0, +0.166);
  I2 min/end score x 0.59/0.59; I3 r = 1.0 on
  `x_world_measured` (the dog-alpha centroid through the known camera, + the fixed 0.14 m offset); I4 back turned in
  96% of refusal frames.
- Occlusion assertions over all 768 frames: DAG acyclic every frame: True; depth conflicts:
  0; alpha valid every frame: True; order flips while
  overlapping (pops): 0; per-pixel depth re-composite vs DAG composite: 192
  frames checked, 0 disagree by more than 50 px.
- The split is needed, not decorative: in 238 frames (22.1–32.0 s) merging
  `dog_in` and `dog_out` back into one layer makes a 2-cycle with `jamb_R`; for the person, 14 frames (the push, 6.04–6.58 s,
  the hand behind the left jamb).
- Overlap events: the porch post hides the walking dog 18.17–20.38 s; the right jamb hides the dog's loin 22.13–32.0 s;
  the person's reaching arm passes in front of the right jamb 3.54–4.58 s.
- At the end 66% of the dog's pixels are behind the casing plane (head, chest, forelegs,
  in the doorway) and the rest, hindquarters and tail, in front of it; at most 75% is ever behind it.
  The measured centroid in score units reaches 0.541 (below the 0.56 sill) only because the lying
  body's centroid is pulled forward by the outstretched forelegs and head; the hindquarters stay outside in every frame.
- Contact shadow under the dog's bottom contour: share of contour columns with shadow just beneath, min
  0.979, median 1.0.
- Sound (RMS, dBFS, over 80% of each line, bed included): calls [-16.78, -15.84], soft lines [-30.14, -29.9, -28.25], room tone
  -45.71. The soft voice is 11.5 dB under the calls and
  15.6 dB over the room tone. Film integrated loudness -19.1 LUFS (ffmpeg ebur128).
- Film: 912 frames, 38.0 s, 1280×720, 24 fps, H.264 + AAC, 4.0 MB.

**Looked at** (Read on extracted images): contact sheets of every third frame of a review render and of the final render
around every choice; the four stills; the proof sheets in `proof/` (mattes of `dog_in`, `dog_out`, the jamb, the post,
the person, with the DAG order and edges); frames decoded from `film.mp4` at 4.0, 7.6, 19, 25.5, 27.5, 31.5 s and both cards.

**Unknown**: I cannot play video or listen. I have not seen the film at normal speed, so the rhythm of the substitutions
(the six-cel head-low walk, the 13-frame turn, the pop where the walking cel gives way to the re-assembled lying dog at
23.79 s) is judged only from stills. The sound is unheard. Whether the back-of-head reads as *looking in* is for the critic.

## What failed and what changed

See `ledger.jsonl` (one line per attempt). The main ones: the lying dog's first assembly (prongs, a leg through the
floor); a NaN that blacked out half a frame; the hallway plate showing only its floor because the oblique stage lifts deep
things; spurious DAG conflicts on antialiased edges (fixed by typing supports and the room, not by loosening the test);
the lying dog first coming out entirely "in" or on the porch in front of the door (fixed by one fixed body-centre
offset and angling the body into the doorway so its depth pass crosses the casing); the seated person's push arm
invisible because its depth pass put it inside the wall, where the facade correctly held it out; the turn back passing
through camera-facing frames; the look-in head as a black ball.

## Method library (technique → conditions → proof clip → failures → repair → rejected)

- **Split by own depth pass** → an object crossing a thin occluder in depth (dog across the jamb, arm through the
  casing) → 24-32 s, 3.5-4.6 s, 6.0-6.6 s → a global z-order makes it all-in or all-out → `_in/_out` sublayers at the
  occluder's plane, with a per-frame "cycle if merged" flag → rejected: hand-painted per-frame mattes; forcing the dog
  in front of the jamb.
- **Supports under standers** → floors and sills under actors → every frame → antialiased edges produced fake conflicts
  → typed `support` edges → rejected: relaxing the conflict threshold.
- **Real turn by substitution** → a turn the footage actually contains → 3.42-3.96 s, 8.0-8.8 s → mirror flip collapses
  edge-on → play the dog's own turn; skip camera-facing frames when the head must stay on the door → rejected: squash.
- **Parts re-assembly for poses the footage lacks** → lying, head turned in → 4.2-7.5 s, 23.8-32 s → seams at the neck,
  size pop from a 3/4 walk cel to the profile rig → head overlaps the neck; start the lie head-low → rejected: a drawn
  lying dog; a 3D maquette.
- **Holdout for sound** → a sound source behind a door → 0-7 s → (not listened to) → low-pass + gain tied to the door
  angle → rejected: a cut-in of room tone.

## What I did not do

- No independent critic has seen it; I did not approve it.
- I cannot listen: the sound is measured (levels, timing) and unheard.
- No Quick, Draw! drawings, no web images, no models. The person is drawn, not found.
- The person's position "beside the door" is placed at x = -1.05 m on this porch's bench, not the score's -1.25 (the
  person is not part of the invariants; the dog's mapping is the one fixed offset above).
- No git, nothing outside this folder.


## Round 2 (after critic round 1: DOES NOT PASS)

What the critic found, what caused it, what changed. Everything was re-rendered (768 frames), `trace.json` rewritten
from the render, `check_handmade.py`: **ALL OK**.

1. **The jamb defect (blocking).** Cause: a bug in my own affine. The dog layer's forward map was
   `y = Ya + k(v - va) + shear·(x - Xa)`, but the constant term missed `-shear·k·cx·ua`, so every sheared dog (the last
   1.3 m of the approach and the whole lie) was drawn about 90 px *below* its anchor: on the porch, in front of the sill,
   while its depth pass said it was behind the casing. The depth buffer was right and the picture was wrong, so the
   order read as impossible. Fixed: the front half now lies on the sill and the interior boards (at 28.0 s its paws and
   belly sit on the sill, at that floor's screen height), the jamb covers the body where it crosses, and the hindquarters
   lie on the porch in front of it. The crossing moved to x = 0.575, the jamb's own outer edge, so the in/out boundary is
   the jamb's edge and not a straight matte cut on the hindquarters.
2. **Looking in.** The filled outline and the narrow sliver are gone. The head is the real head of frame 0, where the
   dog is seen from behind and to one side with its ear toward the camera, tilted toward the lit hall. It is never
   narrower than 78% of its own width. There is no halo: it is lit like the body and warmed a little by the room.
3. **Turns.** I removed cels 15, 17, 19 and 20 from the turn away (the box with legs, the two heads). It now goes from the
   left profile through the camera-facing frames 26-33 and the 3/4 right frames, and is held from 3.88 s in a clear
   facing-away profile (the frame-10 standing pose, mirrored as a whole). Turning back: the head lies level over the
   shoulders toward the door (it was nose-up, which read as a seal's neck). The rise takes 7.60-7.80, then camera-facing
   frame 26, then the left profile frame 14 with the head toward the door from 7.92 s. The 3/4 sniffing frames 17 and 19
   are gone.
4. **Walk.** I dropped the headless "boulder" (f47), the blurred f46 and f42 (which read as two heads). The cycle is now
   f43-45.
5. **Shadows, edges, framing.** I added a wide occlusion pool to the contact shadow, so the dog sits on the dark boards
   too (shadow under the bottom contour: min 0.985, median
   1.0). The hind-leg part is cut lower, feathered and drawn behind the torso, so
   its cut never shows. The rim light is halved and the head halo removed. There is no push at 7.6, so the person is in
   frame at 7.8.

Measured after round 2: onsets dt 0 / 0 / 0 / 0 / 0 / +0.166, looks in +0.10, settles -0.09.
- The ordering never forms a loop, there are no depth conflicts, no order flips while two layers overlap, and alpha is
  valid in every frame.
- The per-pixel re-composite was checked on 192 frames; none differ by more than 50 px.
- The dog is split at the jamb in 238 frames.
- At the end 70% of the dog's pixels are behind the door-frame plane.
- The look-in onset is now measured as a >10% one-frame change of the dog's own pixels (the head swap), since the new
  head does not raise the dog's height.

Looked at, every frame: 3.42–4.63, 7.42–8.63, 23.67–24.63 and 26.29–28.50, as crops around the dog, plus decoded film
frames. Still weak:
- f43 still has a slightly tangled head.
- The lying refusal is a rough assembly.
- The rising pose at 7.7–7.8 is a lump with the head on top.
- Whether the frame-0 head reads as *looking in* is for the critic.
- The walk glides a few px during cel holds.
- I have not heard the sound (unchanged since round 1).


## Round 3 (after critic round 2: DOES NOT PASS, close)

1. **The walk-in through the jamb (22.1–24.4).** There were two causes:
   - *The walk cels.* The head-low cels are a three-quarter-front view, so their hind feet sit higher in the picture than
     their front feet. Angled into the doorway, that put the hindquarters up on the siding.
   - *The depth path.* It let the body cross the frame plane to the right of the opening, so the part between the jamb
     and that crossing was held out by the wall: the rear shrank to a sliver, then popped back when the lying parts took
     over at 23.79.

   Changes:
   - From score x = 2.05 on (from about 20.6 s), the frame-10 profile parts walk. Their feet are level, and the same
     parts then lie down, so there is no drawing swap at the sill.
   - The depth crossing is held at the right jamb's outer edge (x = 0.575) for the whole walk-in.
   - The hind-leg part overlaps the torso and is drawn behind it, so there is no gap and no visible cut.

   Measured on the dog's alpha pass right of the casing, every frame 22.1–24.4 (`build/cache/rear_metric.json`):
   - The lowest hindquarter pixel is at most 4.9 px above the porch line.
   - The largest change in rear area between adjacent frames is 5.8%.
2. **7.63–7.83: one head.** I removed the head laid over the shoulder. Now the frontal head comes round on the rising
   body (to 7.68), then the real standing cel 28 faces the camera (7.68–7.80), then cel 26, then the left profile cel 14
   with the head toward the door from 7.92.
3. **Voice before response.** flite puts 0.27–0.35 s of silence before each line. It is now trimmed, and each line is
   placed by its audible onset:
   - "Come here" at 0.82 s; the retreat is at 1.00.
   - The second call at 3.24 s; the refusal is at 3.417.
   - "It's all right" at 7.28 s; the turn is at 7.458.
   - "Come in" at 26.3 s; the look-in is at 26.50.

   An envelope check on the mixed track finds the first loud sample at 0.87, 3.28, 7.33 and 26.38 s. Levels are
   unchanged: the soft voice is 11.4 dB under the calls and 16.2 dB
   over the room tone.
4. **Contact shadow and edges.** The shadow is now cast down onto the boards under the feet and belly. It is kept only
   at or below the dog's own bottom contour, so there is no halo over the siding. Shadow under the bottom contour: min
   0.928, median 0.981. The cels now bleed the
   dog's own colour into their transparent border, so resampling no longer pulls a dark or light fringe from the
   footage's background.
5. **The black fade at 0.00 is gone.** The scene now cuts straight in from the title card.

After the re-render, `check_handmade.py` gives ALL OK. Onsets: dt 0 / 0 / 0 / 0 / 0 / +0.166, looks in +0.10.
- No ordering loops, no conflicts and no pops; alpha valid; the per-pixel re-composite differs by more than 50 px on 0
  of 192 frames.
- The dog is split at the jamb in 239 frames.
- Note: the first full render stopped at frame 562 on a bug in the ordering code (an overlap of exactly one pixel). I
  fixed it and rendered the remaining 206 frames with the same code.

Looked at, every frame: 21.79–24.50 and 7.50–8.00 (crops around the dog), plus the decoded film at the scene start.

Still weak:
- The walking profile parts are my own small rig, not real footage, for the last 1.45 m. They are the dog's real
  pixels, but the swing is computed.
- The rig's lowered head shows two lobes (the ear and the head).
- The rise at 7.67 is one frame of a half-risen body with the frontal head.
- The walk cels glide a few px during holds.
- The sound is measured, not heard.

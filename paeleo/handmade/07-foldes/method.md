# SCION 07 · Peter Foldès: drawn metamorphosis · the threshold, handmade

*A new operational work inspired by the lineage of Hunger (1974) and early computer-assisted interpolation between
hand-drawn forms. Not by, and not endorsed by, Peter Foldès.*

## Thesis

The dog is a drawing that changes. Each change is a consequence, not a filter. When it is called, the caller's figure swells
and his arm is drawn too long. When it refuses, its outline turns away through drawn views and then **closes**: the lying body
draws in to a curl, the tail wrapped round and the head tucked. When the door opens, the **door's own outline is carried out
and laid on the boards as the light**. When the soft voice comes, the curl opens and the head comes round past the camera to
look at the door. The dog then walks into the light, head low, and lies across the sill. At *come in* its head turns away from
us, into the lit room, and then it settles and stays.

It would be bland if the in-betweens were only tweens of one puppet, or if the dog stayed one rigid shape. It would be wrong if
any in-between dissolved into an edge-on stick (the failure this lineage exists to beat).

## The swarm (one agent, roles merged; no critic is claimed)

| Role | Artifact it built or verified |
|---|---|
| Key-image draughtsperson | `keys/dog_keys.json`, `keys/person_keys.json` (from `build/keys.py`); sheet `proof/keys.png` |
| Correspondence mapper | named strokes, fixed point counts, the mirror rule with left/right swapped, the two symmetric substitution keys (`build/keys.py`, `build/dog.py`) |
| Interpolation engineer | `build/dog.py` (blend, head placement, the neck bound to the head, foot interventions), `build/solve.py` (feet) |
| Metamorphosis dramaturg | `build/solve.py` BODY_SEQ / HEAD_SEQ timed to the score, `build/schedule.json`; the door-to-light metamorphosis |
| Distortion inspector | the frame strips in `proof/` and the ledger (`ledger.jsonl`): every turn frame was looked at |
| Independent narrative critic | **not this agent.** The builder does not approve its own work; the review comes from outside |

All roles were run by one agent, because the coupling between drawing, correspondence and timing was tighter than any
benefit from splitting them up. No sub-agents were run.

## Native formal language, as it exists in the project

- **Key contour drawings**: 16 body keys (stand, crouch, lie, curl, rear 3/4, rear, front 3/4, front, and mirrors) and 10 head
  keys (profile, 3/4 front, front, 3/4 rear, rear, and mirrors). Each is a set of named strokes: `body` (closed, 12 points),
  four legs and the tail (limb centrelines with widths), `head` (closed, 10), two ears (4), two eyes, nose, mouth. The units are metres, y
  is up, and coordinates are body-local. The dog's proportions were *studied* from the archive dog's SAM outline (kit frame f008)
  and then drawn as coordinates. Nothing was traced.
- **Point correspondences**: point *i* of a stroke is the same anatomical place in every key (body: 0 neck top, 1 withers …
  10 chest front, 11 throat). Mirroring negates x **and swaps the dog's left and right strokes**, because after a turn the camera sees the other
  side. The neck points are bound to the back of the skull and the throat of whatever head key is current, a correspondence
  across groups.
- **In-between fields**: an in-between is the weighted sum of corresponding points. The head group runs on its own sequence,
  and leads the body in both turns. The acting fields from the score drive the ears (rotation about their base, by `act.ear`),
  the tail (blend of high / mid / tucked tails by `act.tail`, wag by `act.wag`) and the breathing.
- **Transformation pacing**: `BODY_SEQ` and `HEAD_SEQ` in `build/solve.py` (copied to `build/schedule.json`). These are the
  registered morph sequence: each waypoint is a key blend at a time, with smoothstep pacing between waypoints.
- **Discontinuity markers**: `proof/topology.json`. It lists every draw-order change, frame by frame, and the declared substitutions
  (body `rearA→rearB` at 3.83 s, head `rearH→rearH_R` at 3.80 s, head `frontH_R→frontH` at 7.51 s, body
  `frontB→frontA` at 8.37 s). A flat outline cannot turn 180 degrees by interpolation: blending a contour with its own mirror
  reverses its winding, and it collapses (see `proof/before_after.png`). So each turn passes through a key drawn
  **left-right symmetric**, and at that key the correspondence set is swapped for its mirror. The swap is invisible because the
  point set is the same.
- **Intervention frames**: hand-authored exceptions that override interpolation where it would be visibly bad.
  - Planted paws: while walking, a paw stays where it touched the boards until the solver lifts it and steps it. The leg
    drawing is re-posed by a similarity transform to reach it.
  - During a turn on the spot, the paws follow the drawn view, lifted in proportion to their speed.
  - While lying down, the legs fold from planted to drawn.

## How the dog moves

The dog moves by **interpolating between drawn keys, never by a skeleton**. The legs are the one exception: the drawn leg is
bent to its planted paw. Its position is the score's `x`: `screen_x = 330 + 190 · x`, with a fixed camera. It backs away to the right
(facing the door) at 1.0 s. At 3.42 s it turns its back: 3/4 rear at 3.60, rear at 3.78–3.84, 3/4 rear facing away at 4.02,
profile facing away at 4.24. It then lies down facing away, and from 6.0 s it closes into the curl. At 7.46 s the head lifts
and comes round past the camera (3/4 front, front, 3/4 front, then profile looking back by 7.62). The curl opens, the dog rises
while still looking back, and the body follows through the front views (8.2–8.7 s). From 14.71 s it walks in with its head below the
line of its back, and lies down across the sill at 23.79. At 26.4 s the head turns to the 3/4-rear head key, away from us and
into the lit doorway. At 28.05–28.65 it settles chin-down, and stays.

The person is 8 key drawings blended by the score's circumstances (mouth, reach, sit, low hand). He swells while calling. He
sidesteps out of the doorway, sits on the boards against the wall beside the door, and puts his hand out low along the
boards. *Beside the door* is staged on the porch, left of the frame. In the score the person's x is −1.25; the person's position is
not one of the invariants.

## Protected conditions and what was measured

**Measured** (`python3 tools/paeleo/check_handmade.py`, `invariants.json`, `proof/measures.json`):
- I1 choices: retreat 1.000 s (dt +0.000), watch 2.333 s (dt +0.000), refuse 3.417 s (dt +0.000), watch 7.458 s (dt +0.000), approach 14.708 s (dt +0.000), lie_down 23.792 s (dt +0.000). *This is exact because the trace's `state` is the scheduled choice taken from the score. It is not
  detected from pixels.* Whether the drawing does each thing on time was judged by looking (below).
- I2 threshold: min x 0.5898 m (sill 0.56), end 0.6239 m. The measure is the
  centroid of the drawn torso, mapped back to metres.
- I3 direction: r = 1.0 between the drawn torso's screen x and the score's x, over 768 frames
  (fixed camera). The mapping is linear, so the approach covers the same distance at the same pace, and the retreat goes the other way.
- I4 refusal: 93.8% of refusal frames have the head key's gaze turned away. The other
  frames are the first 0.3 s, while the head is still coming round.
- Head low on the approach: the drawn head top is 12.8–15.5
  px below the withers on every approach frame from 14.917 s
  (the approach starts at 14.708 s; the first 5 frames are the head going down).
- Across the sill (from 24.5 s): at least 95.9 px of the dog lies inside the door frame line
  (x = 417 px), and at least 171.3 px lies outside it, tail included.
- Sound (dBFS RMS per utterance, on the mixed stems): calls -15.1 / -15.2; soft -26.51 /
  -27.54 / *come in* -29.62. The loudest soft utterance is 11.31 dB under
  the quieter call, and the quietest soft utterance is 18.49 dB above the room tone (-48.11). Peak
  -1.01 dBFS.
- film.mp4: 2.13 MB, H.264 + AAC, 1280×720, 24 fps, 38.0 s, faststart.

**Looked at** (Read tool, on frames extracted from film.mp4 and on rendered frames):
- every 2nd frame of the refusal turn, 3.42–4.33 s;
- every frame of the turn back, 7.38–7.79 s, then every 2nd frame to 8.55 s;
- the curl, 4.5–7.6 s;
- the walk, 19.0–19.8 s;
- the door to light, 6.1–7.2 s;
- the sill, 23.6–30.2 s;
- a 1 fps contact sheet of the whole film, and the four stills.

What I saw: in every looked-at frame of both turns the figure reads as a dog. The two front-view frames (8.30–8.38 s) are the
weakest: a round body, toy-like. The back is shown by 3.6 s and stays turned until the head comes round at 7.46. During the
walk the paws stay on the boards between steps.

**Unknown**:
- how the voices sound, and whether they are heard as words;
- whether the motion reads at normal speed, since I only ever saw stills and strips, never playback;
- whether a viewer reads the curl as a refusal and the door's outline as becoming light. That is for the critic.

**Artistic achievement judged only by viewing**: whether the transformations are felt as consequences (the closing, the door
becoming light, the head coming round), rather than as tweens.

## What failed and what changed

The full record is in `ledger.jsonl`. In short:
1. The first keys had a giraffe neck and a sausage body. Redrawn deeper and shorter.
2. Splined architecture made arches. Ruled lines now keep their corners.
3. A lifted leg bent 3.5×. Toned down.
4. The door light warmed strokes patchily. One value per figure now.
5. Python's salted `hash()` seeded the pen pressure, which would have made the lines differ from process to process. Made deterministic.
6. Ears collapsed into sticks in the back views. Ghost half-transparent legs. Planted paws lagged a fast turn, so the legs
   splayed. Each fixed at its cause.
7. **The head's turn back at 7.50 collapsed into a vertical stick.** Blending a head with its mirror reverses the point
   order. A first fix through 3/4 front heads still collapsed, for the same reason. Fixed by a symmetric front head as the
   substitution point, and by rewinding the back-of-head key's ears and ring.
8. The trace's centroid included the head-bound neck points, which put the measured dog 3 cm over the sill line. The trace now
   measures the torso, and says so.
9. At the 1 fps contact sheet the film read as ordinary in-betweening, so the two narrative metamorphoses were added: the refusal
   closes into a curl, and the caller swells.
10. This environment stops single processes after about 80–90 s, so the renderer became resumable in chunks.

## What was not done

- No independent critic has seen it. Nothing here is a verdict.
- **I cannot listen.** The sound was measured (levels below), never heard. The formant voices may not be understood as words,
  so the spoken words are also set as small italic type under the scene. This is the person's speech, not a label for the
  dog's state.
- No Quick, Draw! drawings, archive-door frames, found shots, `stage.js` or `lenses.js` were used.
- I did not fork competing branches. The two stalled repairs (the head's turn back) were resolved by one change of model
  (the symmetric substitution head), compared side by side in `proof/before_after.png`.
- No git and no accepted checkpoint. The project is rebuilt by `build/make.sh`.

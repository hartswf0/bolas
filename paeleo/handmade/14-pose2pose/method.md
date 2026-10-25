# SCION 14 · Nora Willett, Pose2Pose Casting: the threshold, handmade

*A lineage of method, not an endorsement.*

## Thesis
The dog is never moved, only **cast**. A small illustration bank of finished ink drawings is matched to a recorded
performance (the PAELEO machine's decision trace) by a dynamic-programming path. On every frame the dog is one whole
drawing from the bank, held until a better one is worth the cost of changing. The viewer should see a dog that decides.
They should never see a puppet being bent. The film would be bland if the path picked median standing drawings and the
choices vanished into small shifts. So the rare gestures (head round to the door, listening, looking in) have drawings
of their own.

## The swarm (one agent, roles kept as stages with their own artifacts)
| role | artifact | file |
|---|---|---|
| Pose extractor (+ action editor) | typed pose vector per score frame, 4 recorded action edits | `build/poses.py` → `build/cache/poses.json` |
| Representative-pose curator | k-means clusters of the performance vs the bank, rare gestures, unexplained error | `build/curate.py` → `proof/clusters.json` |
| Illustrator | the illustration bank (41 dog drawings, 13 person drawings) and the atlas | `build/bank.py`, `build/dogparts.py`, `build/personparts.py` → `bank/bank.json`, `proof/pose_atlas.png` |
| Sequence optimizer | Viterbi path and placement | `build/solve.py` → `proof/path.json` |
| Action editor | spoken lines, staging, sound from the path, trace | `build/cues.py`, `build/scene.js`, `build/sound.py`, `build/finish.py` |
| Independent critic | **not run by me.** The brief assigns an outside critic. I did not approve this work. | |

## Native formal language, as built
- **Input poses**: per frame, `yaw` (0 = facing the door, 180 = back turned), `lie`, `crouch`, `head`, `look`, `rest`, `ear`,
  `tail`, `moving`, `back` (backing vs forward), gait `phase` (from distance travelled, 11.42 rad/m as in the score), `wag`
  (amplitude × a 2.1 Hz sweep), `over` (head over the shoulder), `listen`. Time base: score frame `i`, 24 fps.
- **Representative clusters**: k = 14 over those vectors. Every cluster's nearest drawing is within distance 1.0, which
  counts as explained. The first pass left two clusters unexplained: the dog getting up at 7.6 s (1.98) and the refusal
  lie (1.07). The rising cluster got a new drawing, `situp_R`, and dropped to 0.93.
- **Illustration bank**: drawings set by hand from a construction kit: torso points, neck, a head in profile,
  three-quarter, front or back view, two-bone legs, tail, saddle, ring of ruff and socks. Each one is inked with one
  outer contour and a flat wash. Units: film px at 190 px/m, origin on the ground under the dog. Walking (8) and backing
  (8) drawings are set on a **gait chart**. Each paw is planted for 60% of a 0.55 m cycle and slides backward in the body
  frame at exactly the travel speed, so in the world it stays put. Flops (mirror copies) exist as separate drawings for
  the other facing. They are never used as turn in-betweens.
- **Pose distance**: weighted squared differences per feature, with `yaw` circular. Weights are in `solve.py`.
- **Transition penalty**: `0.7 + 0.15 × distance(drawing a, drawing b)`, with +100 between the backing and walking cycles.
  A big pose jump costs more than going through the drawn in-betweens, so turns pass through three-quarter and front
  views.
- **Viterbi path**: one drawing per frame, 768 frames. 100 drawing changes, no 1-frame holds, 39 of 41 dog drawings used.
- **Placement**: a gait drawing is put where its phase says along the score's travelled distance, so paws are pinned. A
  held drawing keeps its spot. When a walk ends, the next drawing is placed where the last one's paws stood.

**Numerical invariant (tested)**: planted paws never slide. The largest slide of a planted paw, measured while a drawing
is held or the cycle advances, is **1.38 px** (rounding). A paw can also jump when the action changes and a different
drawing replaces it. Those jumps were measured separately: up to 33 px, at the end of the retreat (2.625 s), where the dog
gathers its feet in one drawing change.
**Artistic achievement judged only by viewing**: whether the dog reads as deciding: the backing, the turned back, the
head coming round, the low approach, the lying down, and looking in and staying.

## Staging
A front elevation of a porch at dusk, with a fixed camera. The door is at x = 0 in the house wall. It is hinged on the
right jamb and swings into the room. The dog walks the boards parallel to the wall: screen x = 300 + 190·x_score. The
retreat goes right and the approach goes left over the score's distance at the score's pace. The person stands in the
doorway, steps aside to a bench at x = −1.25 and sits. The door opens from 6.2 s and the room's light falls out over a
threshold stone. The dog lies on that stone with its forequarters between the jambs (103 px inside the frame) and its
hindquarters and tail outside (141 px). It looks in by turning the back of its head to us, toward the lit room behind it,
not toward the person. The dusk deepens over 32 s. Spoken lines are captioned when they are spoken: calls are upright
and bold, the soft voice is small italic. There are no state labels.

## Action edits (recorded in `poses.json`)
- E1: the refusal turn starts at the choice (3.417 s) and completes by 3.88 s, so the back is shown by 3.625 s. The score
  turns the body 3.9–4.6 s.
- E2: at 7.458 s the head comes round over the shoulder first, and the body follows on the score.
- E3: for 1.1 s after each soft voice, while standing, the dog lifts its nose to listen.
- E4: the person walks aside first and then sits. The score does both at once.

## Measured (from the render; `trace.json` → `onsets`, `invariants.json`)
check_handmade: **ALL OK**. I1 dt: retreat +0.083 s, watch +0.042, refuse +0.041, watch (turns back to look) +0.000,
approach +0.084, lie down +0.083. I2: min x 0.59, ends 0.59. I3: r = 0.999 on the measured pixel centroid. I4: 95.8% of
refusal frames have the head turned away.
Pixel and paw measures: the body first moves back at 1.083 s and first moves forward at 14.792 s. Motion stops after the
retreat at 2.375 s. The back is first shown at 3.625 s and held until 7.458 s. The body faces the door again at 8.25 s.
The dog goes down (sits) at 23.875 s and lies low (pixel centroid) at 24.125 s, +0.33 s after the score's choice. It
looks in at 26.542 s (+0.14 after 26.4) and settles chin on paws at 28.208 s.
`state` in the trace is classified from the drawing on screen, not copied from the score. A backing drawing held still for
3+ frames counts as watching (pixel-checked). `facing` is where the head points.
Sound, measured on the AAC in film.mp4: the calls are −12.2 / −10.1 dBFS RMS, the soft voice −23.3 dBFS (11–13 dB quieter)
and the room tone −47.6 dBFS.

## Looked at
The atlas sheets after every bank change; contact sheets of 3.42–4.0 s, 7.33–8.67 s and 23.1–29.2 s; a 0.25 s overview
of the whole scene; the four stills; the title and end cards; the path trace.

## What failed and what I changed
See `ledger.jsonl`. Main items:
- The front view of the dog first read as a box or helmet. I redrew it with the head three-quarter, leading the turn.
- The first back-of-head looked like a ball. I redrew it with both ears and a cheek sliver.
- Giraffe necks: I lowered the head bases.
- A backing→walking flip caused a 65 px paw slide. I forbade that transition and made held drawings keep their spot.
- An unexplained rising cluster: I added new artwork.
- Walk offsets delayed the measured onsets. Walks now start where the score is.
- Fixes to the end card and to the claims it makes.

## Still weak
- The front-view in-between (2 frames at 3.63 s) is the plainest drawing. It is box-like up close.
- The dog is small in a wide fixed shot (about 190 px long), and it is darker in front of the wall mid-approach.
- The person is a simple figure. Its walking aside is quick and low contrast.
- The look-in head is small. It reads against the bright doorway, but whether it reads *as looking in* is for the critic.
- A paw jumps (up to 33 px) where one action changes to another. Nothing slides.
- The voice is a crude formant synthesizer. **Nobody has listened to it**, including me. I cannot hear. Levels and a
  spectrogram were checked; intelligibility is unknown.

## Not done
- No independent critic was run here. No operator page was published (a local `index.html` exists).
- No video pose extraction from the archive dog: the performance is the score. The archive was a drawing reference only.
- No Quick, Draw! drawings or other found shots were used. No git.

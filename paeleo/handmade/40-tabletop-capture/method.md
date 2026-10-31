# SCION 40 · Physical Tabletop Capture — Paper Performance Swarm (PAE-02, cohort 9)

**Theorem:** fingers moving paper on a table can be turned into reusable, editable film acting.
**The honest constraint:** there was no camera, no table and no performer here. The "capture" in this film was
**synthesized here** (build/plate.py) and the film says so on the inset and on the end card. What is real is the
pipeline: from the synthesized plate's *pixels alone* the tracker recovers the camera, the hands, every paper piece's
rigid transform and identity, and an event stream; the film is rendered only from that recovered data, with new
paper skins on a new paper set.

## The swarm (roles merged where coupling was tight; all run as scripts in `build/`)

| role | artifact | script |
|---|---|---|
| Puppet fabricator | 59 cards cut twice: *plate* style (white card, marker line, fiducial tab) and *skin* style (coloured cut paper) | `cards.py` |
| Camera calibration agent | layout sheet with 4 corner fiducials and a metre ruler; homography from the plate | `set.py`, `track.py` |
| Live capture technician | the performers' sheet (which card lies where, which hand holds what, per frame) and the synthesized overhead plate | `perform.py`, `hands.py`, `plate.py` |
| Tracking recovery agent | calibration, hand mattes, per-piece rigid transforms + card identity, event stream, error report | `track.py` |
| Motion editor | replay with skins; the one edit (neck contact constraint); trace measured from the render | `replay.py`, `render.py` |
| Sound | formant-synth voice; paper foley driven by the recovered event stream | `sound.py` |
| Independent performance critic | **not run by this swarm** — an independent critic judges the film | — |

`build/make.sh` runs everything in order.

## Native formal language (typed, preserved in the project)

- **Coordinates.** *stage* (1280×720, the layout sheet = the picture plane, y down), *plate* (the overhead camera image,
  `H_stage→plate`), *card* (each piece's image, anchor point), *score* (metres along the porch, 24 fps).
  Mapping: the sill (0.56 m) sits on the wall line at stage x = 330; 1 m = 200 px; outside is to the right.
- **Fiducials.** 6×6-cell squares: black ring, 4×4 data (7 id bits, 6 complement bits, parity, two orientation cells).
  Every plate card carries one on a paper tab; the sheet carries four (ids 120–123) at its corners.
- **Texture tracking / optical flow.** Lucas–Kanade (Gauss–Newton, coarse-to-fine over 3 levels) aligning each card's
  own printed texture to the rectified frame: rigid (x, y, θ) + clamped gain/bias, Tukey robust weights, the hand
  matte weighted out. Only the head piece is solved for rotation (the performers turn heads; the other pieces are
  slid); their angle comes from the fiducial.
- **Hand mattes.** Background difference against the clean plate (shadow test on brightness ratio + chroma) AND a 2-D
  Gaussian skin-chroma model (log R/G, log B/G) *learned from the take* (foreground pixels the pieces cannot explain).
- **Per-piece rigid transforms + identity.** Five pieces: dog body, dog head, person, door leaf, light tissue. A swap
  (one card taken off, another put down at the same tab position) is read from the fiducial; when the fiducial is
  under a hand, the card is identified by its texture (every card of the family aligned at the prediction; the best
  unoccluded fit wins).
- **Timestamped event stream.** `data/events.jsonl`: `acquired`, `swap`, `hand_on`/`hand_off`, `move`, per piece,
  recovered from the tracked data. The sound's paper foley is generated from it.

## The capture (synthesized) — what it is

White-card puppets with fiducial tabs lie on a pencilled layout sheet on a wooden table, seen by a slightly rotated,
keystoned overhead camera (lamp falloff, blur, sensor noise, JPEG). Four archive hands (one public-domain shot from
*The Door to Heaven*, 1941, SAM-matted; forearm traced and extended; two mirrored as left hands) reach in from the
table edges and pinch the tabs: one on the dog's body, one on its head, one on the person, one on the door and light.
They occlude markers and cards, which is the point: hand exclusion has to work. The plate is the inset of the film.

## The dog

What the viewer sees of the dog is **paper cards** moved by **recovered rigid transforms** and **swaps**:
37 body cards (stand; 8 walk-low cards carrying the head under the back line; 8 crouched back-away cards; 8 upright
steps; rear-three-quarter / rear / rear-three-quarter / right turns; settle and lie both ways; front-three-quarter /
front / front-three-quarter for the turn back) and 11 head cards (profiles with ears up / back / flat; 45°, rear,
135° and the 58° "looking in" card with the back of the head to us and the muzzle going into the room; front views).
Each card's silhouette was drawn with a small geometric guide (ellipsoids and limbs posed per card, one fixed view)
so the views agree; the guide never moves in the film. The torso of each card is cut as one sheet; legs, tail, ears
are glued-on pieces. **Walking:** a walk card advances exactly 12.5 px (stride 0.5 m / 8 cards) and its stance feet are
drawn 12.5 px further back, so planted feet do not slide; the card is placed by the hand at each step.
**Turns:** substitution through the three-quarter and rear cards (refusal at 3.42 s: 45° → rear → 135° → right) and back
through the front cards (8.1–8.6 s), always one card at a time, so there is never a double image.
**Head leads at 7.46:** the head card (pinned at the neck) comes round first — R → 135° → rear → left profile — on the
lying, right-facing body, eye level toward the door, while the hips are still down; the body rises at 7.8.
**Lying across the sill:** `b_lie_L` lies on the wall line: the head and forelegs are in the lit room, the tail on the
porch, with a contact shadow under it.

## Protected invariants (measured)

See `invariants.json` (checker), `data/onsets.json` (choices measured on the rendered layers),
`data/tracking_error.json` (recovered vs the synthesized truth), `data/contact.json`, `data/sound_levels.json`.
| choice | score t | measured on render | dt |
|---|---|---|---|
| retreat | 1.000 | 1.0 | 0.0 |
| watch | 2.333 | 2.333 | 0.0 |
| refuse | 3.417 | 3.458 | 0.041 |
| watch | 7.458 | 7.458 | 0.0 |
| approach | 14.708 | 14.708 | 0.0 |
| lie_down | 23.792 | 23.833 | 0.041 |
| looks_in | 26.400 | 26.583 | 0.183 |

Tracking (recovered from the plate vs the synthesized truth, all 768 frames): calibration 0.33 px mean / 0.73 px max over the stage (fiducial reprojection 1.18 px rms).

| piece | card id correct | position err mean / p95 / max px | angle err mean / max deg |
|---|---|---|---|
| dog.body | 100.0% | 0.30 / 0.45 / 0.5 | 0.00 / 0.0 |
| dog.head | 100.0% | 0.47 / 0.50 / 19.0 | 0.15 / 9.3 |
| person | 100.0% | 0.21 / 0.22 / 0.3 | 0.00 / 0.0 |
| door | 100.0% | 0.70 / 4.62 / 13.1 | 0.00 / 0.0 |
| light | 100.0% | 0.43 / 0.28 / 24.5 | 0.00 / 0.0 |

Hand matte IoU against the true matte: 0.72 mean, 0.61 at the 10th percentile (158 frames). Head-to-neck gap before the contact constraint: 0.52 px mean, 0.84 p95, 19.0 max (one-frame occlusion outliers). Sound: quietest call is 9.7 dB above the loudest soft line; softest voice 31.0 dB above room tone; every voice starts before or at the dog's reaction (0.95 / 3.36 / 7.36 / 10.36 / 26.36 s). Film: 912 frames, 38.0 s, 1.9 MB.

Looked at (perceptually, by the builder, on frames extracted from the encoded film.mp4): contact sheets at 16 times, frame-by-frame strips of both turns (3.40–4.10 s, 7.85–8.75 s), crops of 7.3/7.5 (head comes round, hips down) and 27/28 s (back of the head toward us, muzzle in the lit room, tail on the porch), stills, title and end card. Not looked at: every frame; the audio was measured, not listened to.

## What failed and what changed

See `ledger.jsonl` (one line per attempt). In short: the first cards were a segmented maquette with table legs
(fixed by one-sheet torsos and fitted limbs); the tracker's free gain collapsed onto blank paper (clamped); the
fiducial grid read missed by half pixels (replaced by a small blob search); head and body tabs overlapped in rear and
right-facing views so each hid the other's marker (head tab raised); the light tissue rotated under flow (rotation
only for the head); markers hidden under the hands lost the card identity (texture identification added); the
lying dog's muzzle touched the person's hand so looking in read as looking at the hand (person moved in, hand lower).

## What was not done (honest evidence)

- **No physical capture.** No camera, table, paper or performer; the plate is synthesized, and the tracking error is
  measured against that synthetic truth, which is cleaner than a real camera (no real motion blur, no lens distortion,
  hands pasted rather than lit).
- The performers' sheet (perform.py) is keyed to the score by hand; it is the "performance". The tracker never reads it
  (only `--eval` does, after tracking).
- The second hard-proof clause (replay on a different set with a new skin) is what the film is; a second, different
  skin was not made.
- No independent critic was run by this swarm; no human watched it. The mobile operator page was not made.
- Voice is a crude formant synthesizer, not a recorded voice.

## Still weak (builder's view; the critic decides)

- The dog is small in the frame (about 190 px long) and the cards are clean and diagrammatic; the paper reads as
  paper, but the drawing is plainer than hand-cut work.
- The rear-three-quarter turn cards crowd four legs into a small space for ~4 frames each; they read as a dog turning,
  not as a beautiful drawing.
- Substitution is visible as substitution: walk cards step on 3–5 frame holds (stop-motion cadence), and head turns are
  three-card swaps over ~0.2 s.
- The tracked head has a few single-frame errors under hand occlusion (max 19 px before the neck constraint pins it).
- The synthesized voice is robotic.

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
  frame, through the camera-facing frames (`TURN_AWAY`), so it is never a mirror flip or a squash. The turn back (8.0-8.8)
  goes the other way through 3/4 frames that keep the head on the door side (`TURN_BACK`).
- **Re-timed walks.** The head-low walk is f42-47, shown mirrored as a whole pose so it faces the door. The cel index is
  the distance travelled divided by a 0.30 m stride (six cels per stride), so the drawings account for the travel; backing
  away plays the same cycle backward.
- **Re-assembled parts.** The footage has no lying dog. Lying is built from frame 10 cut into five sublayers (head, torso,
  near foreleg, far foreleg, hind lower leg) by hand-authored holdout polygons, rotated about pivots: the hind end goes
  down first, then the chest; the forelegs lie forward, the hind paw tucks under. The head turns are substitutions of
  head sublayers: profile away → frontal head (f28) → profile toward the door laid over the shoulder (7.46-7.6), and, for
  *looking in*, the profile head foreshortened as it turns away (T), then the frontal-head outline shown from behind (B):
  dusk on the back of the skull and the room's light around its edge.
- **In depth.** The lying body is angled 31° into the doorway (its depth pass slopes 0.6 m per m), so it crosses the
  casing plane under the right jamb: `dog_in < jamb_R < dog_out`.

Mapping: the dog's body centre in world metres is `x - 0.14` (one fixed offset for the whole film), so the approach covers
the score's distance at the score's pace; the last 1.3 m it angles in toward the doorway.

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

MEASURED_BLOCK

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

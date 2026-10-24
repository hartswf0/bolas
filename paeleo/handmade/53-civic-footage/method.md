# PAE-02 · SCION 53 · Atlanta Moving Image: Civic Footage Performer

**The threshold, re-performed by a dog from a home movie.** Film: `film.mp4` (1280×720, 24 fps, H.264 + AAC, 38.0 s, 912 frames).

## The swarm and its language

SCION 53's theorem is to give footage an afterlife without erasing its documentary status: keep timecodes, place, people,
source descriptions and permissions coupled to every fragment. So the film is built like a moviola bench, not a seamless
composite:

- **Top: four source monitors** (DOG, DOOR, PERSON, HAND). Each shows the unmodified archive frame in use at that moment,
  the outline of what was cut from it, and its record: title, year, rights, clip id, frame number, seconds in the clip, film
  timecode where the catalogue lets us derive one ("film offset unknown" where it does not), and the operation applied.
- **Middle: the composed scene**, labelled on screen as `COMPOSED SCENE · archive fragments re-performed · not a recorded event`.
- **Bottom: the score**: its 32 s timeline, the six choices as event tags, the playhead, the dog's state and `x`, the
  person's circumstances (voice, hand, posture, door), and the prompt as a catalogue event line.

These are the swarm's primitives from its prompt: collection and clip ids, timecoded segments, event tags, rights state,
scene geography (the side-view metre line `x_screen = 372 + 185·x`). The per-frame transform ledger is `build/edl.json`
(for every scene frame: which archive frame each fragment shows and with what operation); the source manifest is `assets.json`.

## How the dog is built and moved

No drawing. The dog is the real dog in *Amateur Film New Jersey C* (undated home movie, Internet Archive, public domain),
cut out by its SAM polygon on every frame and placed by its alpha centroid on the score's `x`. Its own frames perform:

| time | choice | what the footage does | operation |
|---|---|---|---|
| 0–1.0 | watch | f000–f011, looking up, facing the door | play 1:1 |
| 1.0 | backs away | the side-on walk f042–f048, mirrored to face the door and run **backward**; frame stepped by distance travelled | mirror + reverse |
| 2.33 | watches | f004–f012 | ping-pong 2:3 |
| 3.42 | turns its back | **the dog's own turn away from the person in the home movie** (f015–f020, f026–f044, f021–25 cut: their masks swallow the shadow) | play 1:1 |
| 4.6–7.4 | lies, back turned | f043–f047 grain loop, **folded** | COMPOSED |
| 7.46 | turns back to look | head lifts (fold pivot), stands, then its turn away played **in reverse** f044→f015 | composed + reverse 5:4 |
| 9–14.7 | waits | f000–f015 | ping-pong 1:2 |
| 14.71 | comes, head low | f042–f048 mirrored, head low, stepped by distance (feet move with ground covered) | mirror |
| 23.79 | lies across the sill | f043–f047 mirrored, folded | COMPOSED |
| 26.4 | hears *come in*: looks in, then settles | head pivots up toward the doorway, then down to the floor | COMPOSED |

**What was composed, exactly**: the footage has no lying dog. Lying is made by splitting the cut-out at the neck,
compressing the rows below the belly line (legs, to 10 % height, darkened) and lowering body and head by the same amount;
the head piece pivots at the neck (`build/lib.py: fold`). The seam at the neck is visible and was kept, not hidden: it is a
cut-out joint. Every composed frame says `COMPOSED: FOLD` on the dog monitor, and the projector tick goes silent while it holds.

The person standing in the doorway is the coat and legs of the person the dog greets in the same home movie (hand-drawn
matte, the frame's top and left edges faded where the footage ends: we do not invent the rest of them). The seated person is
*Survival Stresses* (1961), substituted by a hard cut at the score's `sit = 0.5`. The hand (reach, then low) is *The Door to
Heaven* (1941), mirrored, its card left out. The door is *Straight Talk* (1992): the closing swing f027→f022 run backward is
the door opening; its warm hallway, kept in its own colour (the only colour in the scene), is the light. Walls and path are
the stone pillar and gravel of the house in the home movie. The sill, the dusk light, the warm fan of light from the door and
the dog's contact shadow are computed.

## Sound (synthesized, numpy)

The projector: one tick per archive-frame change of the dog (higher when the footage runs backward, none on composed folds),
so the operation is audible. The person: formant-synthesized voice tones following the contours of *come here* (high, fast,
loud, twice), *it's all right* (low, breathy, twice) and *come in*; they are not speech and the end card says so. The door:
latch, creak, then the room tone of inside. The dog: paw taps per walking frame, a breath and a thump when it lies, its collar
when it lifts its head. Wind and synthetic crickets under the scene.

## Invariants: measured (build/check.py → build/check.json, from trace.json measured on the render)

`trace.json` is written by the renderer from the composited dog alpha: centroid (x_screen, y_screen), x mapped back to
metres, height, head-end height, nose/tail px, share of alpha inside the door frame. `facing` comes from the archive frame and
mirror flag (structural, not measured from pixels).

1. **Choice times** (±0.25 s): retreat op change 1.000 (motion onset 1.125); watch 2.333; refuse op change 3.417 (first
   frame not facing the door 3.917, back fully turned 4.417); turns back: head lift measured 7.583 (facing the door again 8.542);
   approach op change 14.708 (motion 14.833); lie down op change 23.792 (height below 80 % of standing at 24.000); looks in:
   head-end lift 26.333. PASS. Caveat: the op-change times are guaranteed by construction; the measured pixel events
   (motion, height, head) are the stronger evidence and are listed beside them. The full turn of the back takes 1 s of real
   footage, so the back is fully turned 1.0 s after the choice begins.
2. **Never enters**: min measured x 0.587 m (sill 0.56); the nose never passes the door frame's inner edge (min 342 px vs
   287 px); at the end 35 % of the dog's alpha lies inside the door frame's outer edge, 65 % outside; posture lying. PASS.
3. **Commands push away**: +0.93 m after the call; back turned at 4.42 after the reach (3.4). Seated person on screen from
   5.96, door opening from 6.21, low hand from 6.83, soft voice 7.4 (score), all before the approach (14.83). PASS.
4. **x follows the score**: max |measured − score| 0.003 m; approach 3.408 m measured vs 3.406 m score, mean speed 0.377
   vs 0.377 m/s; retreat goes away from the door. PASS.

## Looked at, not measured

The builder looked at: contact sheets of all kit and candidate shots; the four stills; 36-frame contact sheets of draft 1
and the final; the title and end cards; zoomed crops of the lying passages and of the turn back. Perceptual judgement
(builder's, not a critic's): the retreat, the turned back, the turn back and the head-low approach read clearly; the lying
reads as low and settled into the light but not unambiguously as a lying dog (folded legs, visible neck seam); the standing
person in the doorway is dark and partial (coat and legs only) and may read as a shadow; the right half of the stage (the yard)
is mostly empty dusk.

## What failed and what changed (ledger.jsonl)

Mirrored stone tiling made symmetric faces (replaced with laid blocks). The door's light was invisible (warmth re-measured by
hue, gap exposure-lifted). A forelegs-forward "sphinx" lie was tried and rejected (legs rotated below the floor). The walk
loop first included two still-frontal frames and flickered (restricted to f042–f048). The look-in head lift was too small and
the height proxy hid it (stronger pivot; head-end measure added).

## What was not done

- No independent critic has watched the film; this is the builder's report. The prompt's tribunal verdict is still owed.
- The sound was not listened to (no audio device); only per-0.5 s RMS and peaks were measured.
- No mobile operator page was published (the brief's deliverables are files in this folder).
- No gate weave or grain was added: the grain is the footage's own; the static plates (wall, path) are single frames and do
  not crawl. Film timecodes are derived from catalogue offsets (dog: start_seconds; seated and hand: the clip file's ms range)
  and were not checked against the films; the door clip's offset in its film is unknown and is shown as unknown.
- The dog's home movie is undated; the catalogue's own review notes say "dog identity unclear". We do not name or date the
  people or the place.

## Rebuild

`build/make.sh` (render.py → ffmpeg, sound.py, mux, stills, check.py). Sources are copied under `sources/`.

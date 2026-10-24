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
- **Bottom: the score**: the time and frame, the prompt, the person's circumstances (voice, hand, posture, door) and an
  unlabelled timeline with ticks at the six choices. Round 2 removed the dog's state and the choice names from the screen, so
  the choices must read from the picture. All text in the scene is 16 px or larger.

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
| 4.6–7.4 | lies, back turned | f044 held, **folded** | COMPOSED |
| 7.46 | turns back to look | comes round through its own frontal frames f033→f028 to f015 (facing the door at 7.625 s); legs folded while the score's `lie` is high, rising by 8.0 s | play + COMPOSED squash |
| 9–14.7 | waits | f000–f015 | ping-pong 1:2 |
| 14.71 | comes, head low | f042–f048 mirrored, head low, stepped by distance (feet move with ground covered) | mirror |
| 23.79 | lies across the sill | f044 mirrored, held, folded (`fold2`) | COMPOSED |
| 26.4 | hears *come in*: looks in, then settles | head piece pivots from 40° (chin on the floor) to ~95° (pointing up into the lit doorway), 26.5–28.3 s, then down; body does not move | COMPOSED |

**What was composed, exactly**: the footage has no lying dog, and no other found shot has a lying dog (the lion in *Andy's
Animal Alphabet* lies, but a lion standing in for this dog would be a false history, so it was not used). Lying is made from
f044 by `build/lib.py: fold2` (round 2): per column, everything below a belly line running from the chest to the hindquarters
is folded to 6 % height and darkened, and everything above is lowered so the belly rests on the porch; the head is a separate
piece pivoted at the neck. The seam at the neck is visible and was kept, not hidden: it is a
cut-out joint. Every composed frame says `COMPOSED: FOLD` on the dog monitor, and the projector tick goes silent while it holds.

The person standing in the doorway (round 2) is the woman in *Straight Talk* (1992) herself: the whole door shot is mirrored
so that she faces the porch, standing in the half-open door with her hand on the knob (f010–f013); at 5.42 s her own step out
of the doorway (f013–f019) is played as recorded while the crop re-frames to the door. (Round 1 used the coat and legs of the
person in the dog's home movie; the critic found it ghosted, and no found shot gives a standing caller with head and torso.)
The seated person is
*Survival Stresses* (1961), substituted by a hard cut at the score's `sit = 0.5`. The hand (reach, then low) is *The Door to
Heaven* (1941), mirrored, its card left out; for the reach it slides out of the woman's hand at the knob. The door is the same
*Straight Talk* shot: after she leaves it swings to (f023–f024, ajar) and, run backward f024→f022, opens; its warm hallway, kept in its own colour (the only colour in the scene), is the light. Walls and path are
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
(round 1, builder's own): the lying read as low but ambiguous, and the doorway person as a shadow. The critic agreed and
failed it; see Round 2 below for what changed. The right half of the stage (the yard) is still mostly empty dusk.

## What failed and what changed (ledger.jsonl)

Round 1: mirrored stone tiling made symmetric faces (replaced with laid blocks). The door's light was invisible (warmth re-measured by
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

## Round 2: critic round 1 (`reviews/round1.md`, DOES NOT PASS) and the repairs

| repair condition | what changed | evidence |
|---|---|---|
| 1. lying across the sill at 23.79–24.5 s | `fold2`: legs folded to 6 %, body lowered onto the porch, body held still | measured from 24.5 s: back line (least-squares fit to the body's top edge) max 10.1°; 55–57 % of the dog's length inside the jamb's outer edge; tail at 560 px vs jamb 457 px; height drops below 80 % of standing at 24.0 s. Looked at 23.8, 24.0, 24.25, 24.5 s. |
| 2. look in at 26.4–27.4 s | head pivots to ~95° toward the lit doorway, 26.5–28.3 s, then lowers to rest; body x spread after 24.5 s 0.001 m | head-end lift measured from 26.458 s; still at 27.0 and 28.0 s looked at |
| 3. comes round at 7.46 s, no double exposure | recorded frames f033→f028→f015, skipping the blurred f016–f020; two composite head tries rejected (ledger 11, 12) | facing the door from 7.625 s (structural); zoom of 7.42–8.5 s looked at, no doubled frames |
| 4. solid person in the doorway | the Straight Talk woman, mirrored, opaque, head and torso | stills 0.5, 3.0, 3.9, 4.2, 5.0 s looked at |
| 5. labels, text size, halos | state labels and choice names removed; HUD and cards in 16 px; dog mask eroded 1 px, feather 0.9 | stills looked at |

`python3 tools/paeleo/check_handmade.py paeleo/handmade/53-civic-footage`: ALL OK (I1–I4). `build/check.py`: all PASS, plus
the new `lying_shape`.

Still open after round 2: no second critic pass yet. The rising at 7.5–8.0 s squashes the legs of frontal and side frames,
and the dog looks squat for about half a second. The lying dog still stands about 0.5 m tall at the back: it reads as lying
low, with no paws visible. The sound is unchanged and still not listened to.

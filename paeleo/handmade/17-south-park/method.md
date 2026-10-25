# SCION 17 · South Park: repeatable graphic grammar. The threshold, handmade

## Thesis

A deliberately restricted cut-out grammar (flat construction-paper pieces, a few drawn direction states, an expression
atlas, a mouth atlas, one flat stage template) can carry the threshold scene's six choices as acting, not as labels. The
limits are the style: the dog turns by **substitution between drawings**, never by squashing a flat piece through
edge-on. Drawings are **held on twos**, and every pose is a whole, readable drawing.

The scene would be bland if the dog were a puppet that tweens. It would fail if a turn passed through a non-dog, if the
refusal did not show the back, or if the voice carried the story and the dog did not.

## The swarm (merged: one agent, roles kept as modules)

| role (SCION 17) | artifact | module |
|---|---|---|
| Style bible editor | palette, primitive cuts, fixed scissor wobble, merge-group inking | `build/kit.py`, `build/paint.py` |
| Cutout asset designer | cast bible: Biscuit (dog), Maren (person) | `build/dog.py`, `build/person.py`, `proof/cast_bible_*.png` |
| Dialogue animator | phoneme chart → mouth atlas and voice | `build/dialogue.py`, `build/sound.py` |
| Scene template builder | THE PORCH stage template, door drawings, light, two framings | `build/stage.py` |
| Timing/acting director | score → performance per frame; sound events cut to picture | `build/direct.py` |
| Independent comedy critic | **not run here.** The builder cannot approve its own work. | (the caller's critic) |

The roles are merged because one renderer couples them all and a hand-off would cost more than it saves. No agent runs
were simulated.

## Native formal language (typed, versioned)

- **Shape kit** (`kit-v1`): a piece is a closed polygon in centimetres in a figure frame (y up, origin on the ground), with
  one paper colour, z, a tag and an optional merge group. Each cut has a seeded wobble keyed by name, so a piece is the same
  piece in every frame. Allowed operations: translate, rotate about a pivot, turn a whole profile drawing over, replace
  (substitute). Nothing is scaled non-uniformly except Maren's head, which is a fixed 1.4× cut-out proportion.
- **Face direction states, dog** (`biscuit-v1`): body P (profile), Q (three-quarter front), F (front); head P, Q, F,
  QB (three-quarter back), B (back of the head). P and Q exist facing both ways as complete drawings.
- **Posture drawings**: STAND (a two-segment leg rig whose feet are placed on the floor and solved to: `kit.ik2`) and
  LIE (a separate lying drawing with belly, elbows and hocks on the floor, so no raised hindquarters can occur).
- **Expression atlas, dog**: eye OPEN/WIDE/HALF/CLOSED × brow NEUTRAL/WORRY/DOWN/UP × ear PRICK/HALF/FLAT; head stops
  UP/MID/LOW/DOWN standing and UP/MID/CHIN/HIGH lying; a head-tilt pivot; the tail on a pivot; pupils as eyelines.
- **Person** (`maren-v1`): one three-quarter direction state (she never turns from the dog), STAND/CROUCH/SIT, arms and
  legs solved to hand/foot targets, eyes/brows/tilt, and a **mouth atlas** of ten drawings: REST MBP AA EE OH OO CONS S L SMILE.
- **Phoneme chart** (`dialogue-v1`): each line is timed phonemes. One table maps phoneme → mouth drawing. The same list
  drives the formant voice, so lips and voice share one source and cannot drift apart.
- **Stage template** (`porch-v1`): world in metres, threshold x = 0, door opening [−0.46, 0.46] drawn frontally (flat-stage
  convention: the set faces the camera; the figures play along the line of the wall's foot), sill 0.56, steps 4.9. The door
  is three drawings (AJAR 56°, WIDE 74°, OPEN 87°), and the door light is a function of which drawing is up. Framings: WIDE
  (188 px/m) and CLOSE (330 px/m), with a hard cut at frame 606 (25.25 s).
- **Time base**: scene frame i = score frame i at 24 fps. Poses are sampled on twos (frame i shows pose frame i − i mod 2).
  Cuts and sound run on ones.

## How the dog is built and moved

Biscuit is about 25 paper pieces: a hull-cut body with a saddle patch and cream blaze, a neck that follows the head stop,
a red collar and gold tag, two-segment legs with oval paws (far legs darker), a two-piece tail, and a head of skull, snout,
muzzle, nose, eye, pupil, lid, brow and ears. He moves in four ways, all native to the grammar:

1. **Substitution** for every change of view or posture. The refusal turn is P → Q (3.42 s) → F (3.50) → P turned over
   (3.58); every frame is a whole dog. The turn back is head first: front-view head at 7.46, then the profile head looking
   back over his shoulder (7.54), rise (7.62–7.75), then body Q → F → Q → P (8.00–8.25). Lying down is STAND lowered →
   LIE drawing. Looking in is head P → QB → B (back of the head, framed by the lit hall) at 26.50–26.58, held to 27.96.
2. **Planted feet.** While walking, the gait (`direct.gait`: stride 0.42 m, lateral sequence, 65 % stance) puts each paw on
   the porch, where it stays in world coordinates until its swing. The knees are solved, and the body drops just enough for
   every planted paw to reach the floor, so the bob comes from the feet. Retreat uses the same gait backwards (crouched, ears
   flat, tail tucked); the approach uses it forwards with the head at LOW, below the line of the back.
3. **Pivots**: the tail angle (from the score's `tail`, plus `wag`; when lying, the tail lifts and falls back to the boards,
   and each return is a thump in the sound), the head tilt (10.55–11.9 s, at the second *it's all right*), the pupils (eyelines
   to her face, her low hand, the doorway, the floor away from her).
4. **Position** along the porch: the dog's figure origin is placed at the score's x through the camera mapping. Nothing
   else moves him.

## The person, the door, the circumstances (invariant 3)

Calls are commands: *Come here.* (1.0 s), with her leaning and beckoning; then *Hey! Come here!* (3.4 s), with her arm
reaching out at the dog. The captions are bold capitals on a tilted white slip, and the dog backs away, then turns his back.
Then she steps aside on planted feet (5.40–5.96), pushes the door wide as she lowers herself (door WIDE 6.20, OPEN 6.33,
creak, the light spills out and the hall warms), sits beside the door (6.54), and offers a hand low, palm up, reaching into
the edge of the light (6.8–7.25). Then the soft lines: *it's all right.* (7.4, 10.4), in small italic lower case, with
lidded eyes and a smile. All of this happens before the dog comes at 14.71. *come in.* (26.4) is soft too, and he looks in,
then settles, chin on paws, and stays.

## Sound

All of it is synthesized (`build/sound.py`). Voice: a cascade formant synthesizer (glottal pulse, three time-varying
resonators, a frication branch). Calls are bright and loud; soft lines are breathy and lower. Room: dusk wind and two
crickets. Foley at the director's events: a paw tap at every foot contact of the gait, the collar tag on turns, the flop,
a huff, her steps, sitting, the door creak, a low warm hum through the door once it is open, and tail thumps. There is one
comic beat: a falling two-note pluck under the sulking flop (4.78 s).

## Protected (what must not break)

- The four PAELEO invariants (measured by `tools/paeleo/check_handmade.py` on `trace.json`).
- Every frame of every turn is a complete drawing; no flat piece is squashed through edge-on.
- The LIE drawing has no standing legs. The front half lies inside the door frame and the tail lies outside.
- The head is below the line of the back for the whole approach.
- No state or choice labels on screen. The only words on screen are her spoken words.
- Soft voice ≥ 6 dB below the calls and above the room.

## Evidence (honest)

**Measured** (my own trace, checker run on it): see `invariants.json` and the numbers in the report below. The trace's
`x_screen`/`y_screen` are centroids of the dog's painted silhouette, rasterised at 1× from the same pieces the frame paints.
`x_world_measured` is that centroid back through the frame's camera. `facing` comes from the painted nose relative to the
painted skull. While the back of the head is up (`look = in`), no nose is painted and facing is recorded as 1 (toward the
door) by rule, not by measurement. `x_score` is the score's x at which the dog was staged; `x_anchor_measured` is the painted
body piece's centre in metres. Voice levels: RMS over voiced samples of each synthesized line before mixing
(`build/cache/levels.json`): calls −14.3 and −12.6 dBFS, soft lines −28.1, −27.8 and −28.6 dBFS, room tone −61 dBFS.

**Looked at** (Read tool on images): both cast bibles, ten proof frames, contact sheets decoded from `film.mp4` of the
refusal turn (3.30–4.95 s), the turn back (7.25–8.60), the walk (18.00–18.66, frame by frame), the lie-down and the
look-in, and the four stills.

**Unknown**: how the film sounds. I cannot listen. The voice's intelligibility is not known, which is one reason the
spoken words are also captioned. Whether the timing is funny or moving to a viewer is unknown. No independent critic has
seen it yet.

## What failed and what I changed

See `ledger.jsonl`. In short: seams inside the silhouette (fixed with merge-group inking); a tucked tail that read as a
fifth leg; a back of the head whose nape patch read as a mouth; a face too small for the mouth atlas; a light-mask haze on
the wall; the moon hidden by the porch roof; a refusal still mid-turn at 3.6 s (turn tightened to 3.42–3.58); and a head
that only reached the line of the back in the approach (head stop lowered, neck and collar rebuilt to follow the head).
Two whole-film renders were killed from outside mid-run (exit 144, memory flat), so the build now renders in 96-frame
chunks, one process each, and concatenates them.

**Still weak** (my own reading, not a critic's): the dog is small in the wide shot (about 210 px long); the half-down
frame at 23.97 s hides the forelegs behind the blaze; the front and three-quarter turn drawings are on screen for only two
frames each; the person has one view; the voice is a crude synth whose intelligibility I could not hear.

**Stopping point**: the film is watchable and the four invariants hold on the measured trace. I stopped there, not at a
no-progress boundary. Next is an independent critic round.

## What I did not do

- No independent critic round (not mine to run). No human viewing or listening.
- No archive footage, no found frames, no archive dog. The dog is drawn, so there is no question of a found-footage dog
  that was never filmed lying down. The only found material is five Quick, Draw! doodles, cut into the backdrop.
- Maren has a single direction state; she never turns around in this scene.
- The voice is a crude formant synth, not a recorded performance. The words are captioned because of that.
- No operator page beyond this folder's files. No snapshot or versioning system beyond module version strings and the
  ledger (git was not to be run).

## Living method library

| technique | applicable when | proof clip | observed failure | repair | rejected alternative |
|---|---|---|---|---|---|
| turn by substitution P→Q→F→P(turned over), on twos | a flat figure must turn 180° | 3.42–3.58 s, 8.00–8.25 s | Q front view read as only a head on legs at small size | keep Q/F only 2 frames each; the profile on both sides carries the read | mirror-squash through edge-on |
| head-first turn (front head, then the profile head over the shoulder) | attention must change before the body does | 7.46–7.75 s | none seen | | turn the whole body at once (reads late) |
| planted-foot gait with solved knees and a foot-limited bob | the figure travels | 14.7–23.8 s | head too high in the approach | lower head stop + following neck | a 4-drawing walk cycle (slides) |
| separate LIE drawing | lying is a posture, not a squashed stand | 4.75 s, 24.08 s | | | lowering the standing rig to the floor (knees jut, hindquarters up) |
| back-of-head drawing B against the lit hall | looking *into* a frontal doorway | 26.58–27.96 s | nape patch read as a mouth | remove the patch | raise the profile head (reads as looking up or at her) |
| one phoneme list for mouth and voice | any dialogue | 1.0, 3.4, 7.4, 10.4, 26.4 s | voice intelligibility unknown | captions in the speaker's register | separate lip timing |
| caption register (bold tilted capitals vs small italic lower case) | loud vs soft speech | | | | the same type for both |

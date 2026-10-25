# SCION 52 · Gilliam Ephemera — reconstruct the method

PAE-02, the threshold, handmade. One agent working alone, with the SCION 52 prompt and `BRIEF.md`.

## What this is, and what it is not

A reconstruction of a **cut-out collage method** (photographic prints cut with scissors, hinged with pins, slid and
swapped on a lit table under a rostrum camera, shot a few frames per placement) applied to the threshold scene, built
only from public-domain prints in the kit and card I made.

- **No archive was consulted.** The research starting point in the prompt (a 1974 BBC demonstration on YouTube) was not
  reachable from here and I have not seen it, nor any Gilliam film or the SCION 01 film. Everything below about "the
  method" is **inference** from general, widely described cut-out practice (pinned joints, hinged jaws, substitution of a
  whole card for a turn, a mirrored print for the other side, held frames, airbrushed backgrounds), not a claim about what
  that demonstration shows. I claim no ephemera and no Gilliam image: none is in the film.
- **No paper was cut by hand and nothing was filmed on a real table.** The prompt's own hard proof (a physical paper
  gesture, filmed, then matched digitally) was replaced by the brief's scene, and it could not have been done here anyway.
  The tabletop is digital: pieces are raster cut-outs moved by rigid transforms only (see the protected conditions).

## The studio (smallest capable swarm, merged into one agent)

| role (prompt) | what I actually built or checked |
|---|---|
| broadcast source researcher | could not reach the broadcast: marked uninspected; no claim made from it |
| tabletop craft observer | a cut-out lexicon written as code (`build/table.py`, `build/puppets.py`): pin, slide, swivel, flop, substitute, hold, expose |
| cutout fabricator | `build/cut_pieces.py`: every piece cut from a named source frame by a scissor polygon (and its SAM matte), hand-tinted, paper core left at the edge; `proof/cutting_sheet.jpg` is the reconstruction drawing (pieces with their pins) |
| digital method translator | `build/xsheet.py` (exposure sheet), `build/render.py` (rostrum camera), `build/world.py` (set and lamps) |
| shot historian | `xsheet.json`: one row per exposure, every card's placement; `assets.json`: every piece's source print and rights |
| independent authenticity critic | **not me.** The builder cannot approve; an independent critic judges the film |

## Native formal language, as it exists in the project

- **Source prints**: `sources/` holds copies of the 16 frames used (dog, door, face, forearm, lamp, trees, cloud). Each
  piece in `assets.json` names its frame, archive URL, clip id and rights (all public domain), and its cut polygon in
  source pixels.
- **Physical materials**: prints are toned and hand-tinted (a three-stop dye ramp and an uneven wash), cut tight with the
  light paper core showing at the scissor edge, and cast a small shadow on what lies under them. Card pieces I made
  (crate, shoes, moon, black paper behind the jaw) are listed as drawn.
- **Cuts / pivots**: the dog is one print (home movie frame f006) cut into seven pieces: head, torso, tail, near and far
  forelegs, near and far hind legs, with pins at neck, shoulders, hips and tail root, and overlapping joint discs so a
  turned joint shows no gap. The person is a collage, as the method does it: a face in a hat (Vision of the Wild f010,
  flopped to face the dog) with its chin cut free and pinned at the ear over a scrap of black paper (the hinged jaw), a
  smock (Straight Talk f000), jeans cut at the knee (Straight Talk f013), a forearm that held a card (Door to Heaven f000).
- **Camera frame interval**: `xsheet.json` has 245 exposures for 768 frames. Every exposure is held at least 2 frames
  (on twos), re-phased so each choice starts its own exposure, and held longer whenever nothing on the table is touched
  (longest hold 24 frames). A card that is touched is never put back exactly (a small placement error per exposure on
  the head, tail and person); untouched cards do not move. Film grain changes every frame; the lamp flickers a little
  per exposure.
- **Shot breakdown**: one locked-off rostrum shot (the camera does not move), the facade face-on, the porch running along
  it; space is `x_screen = 290 + 210 · x_metres` (threshold at the door centre, the door opening at ±0.46 m = 193..387 px).
- **Rights advisory**: `assets.json`; nothing of unknown rights is used; Quick, Draw! was not used; no web image, no
  model-generated image.
- **Reconstruction drawings**: `proof/cutting_sheet.jpg`.

## How the dog moves (the operation)

- **Walking**: the leg cards swivel on their pins. Each foot's offset from its pin is linear in the distance travelled
  while it is down, so the foot stays where it was put on the boards; from a standing start each foot stays where it stood
  until its first swing. Measured from the placed transforms: 270 consecutive-exposure pairs of a planted foot, mean slip
  0.43 px, max 1.89 px (the leg prints are slightly slanted, the stance law assumes vertical).
- **Backing away (1.00 s)**: the same legs run backwards, head card dropped, tail tucked, body tilted down at the rear.
- **Turning (3.42 s and 8.08 s)**: never a squash or a mirror sweep. **Substitution**: the profile is lifted off and a
  second print of the same dog, facing the camera with its head turning, is laid in its place for two exposures; then the
  **flopped** puppet (a mirrored print, because the back of a photograph is white paper). Every frame of both turns is a
  whole photographed dog.
- **The refusal**: back to the door from 3.42 s (measured facing −1 on 100% of refusal frames), then it lies down facing
  away, chin on paws.
- **Turning to look (7.458 s)**: the head card alone is turned over (mirrored) on the neck pin while the body still lies
  facing away: the head comes round to the door on the choice frame. It then rises and turns by the turning card.
- **Coming, head low (14.708 s)**: the head card is swivelled down; measured, the head card's centroid is below the top
  line of the back on all 218 approach frames (median 12 px below).
- **Lying down across the sill (23.792 s)**: the archive dog was never filmed lying. Solved in the language: the legs
  swivel flat (forelegs forward along the boards, hind legs folded), the body card comes down onto the boards, rear not
  raised. It ends with 50% of its pixels inside the door frame on screen (head and shoulders in the lit doorway, hindquarters
  and tail outside), on the porch plane: it never goes through.
- **Looking in (26.4 s)**: there is no print of the back of the dog's head; I constructed one (fur cut from the same
  print's saddle to the outline of the skull and hanging ears of the front-facing print) and substitute it for the head
  card from 26.42 s to 28.08 s, so the back of the head is toward the viewer and the muzzle is into the room. Then the
  profile head comes back and lowers, chin on paws, and stays.

The person: calls with the hinged jaw opening on the voice (the jaw is driven by a mouth chart read from the voice takes,
as an animator reads a track), reaches with the forearm card, steps aside, sits on the crate (thighs swivel at the hip
pin), offers the hand low and forward, and nods. The door is a **substitution set** of five prints of a real door
swinging (Straight Talk f024 → f022 → f020 → a strip of its edge): found motion re-timed and reversed. Light coming out is
the table lamp: a warm lamp in the room whose light falls on the boards and the dog through as much of the doorway as the
door uncovers.

## Protected conditions and invariants

Numerical (measured, `proof/measured.json`, `invariants.json`):

- PAELEO check: `check_handmade.py` ALL OK (I1 choices, I2 never inside / ends on the sill, I3 direction, I4 refusal).
- **Onsets measured from the render**, not from labels (trace.json is measured from the rendered dog layer each exposure):
  retreat 1.000 s (head drop / backward travel), stops and head comes up 2.333, back turned 3.417, head turned to the
  door 7.458, approach 14.708 (head drops and travel begins), lies down 23.792 (body top drops), looks in 26.417. All within
  0.02 s of the score.
- **Rigidity** (structural, asserted in `table.place`): every placement is a rotation + translation (+ mirror), |det| = 1;
  no piece is ever scaled, bent or warped after it is cut.
- **Camera interval**: every exposure ≥ 2 frames (100%).
- **Sound** (measured on the synthesized stems): calls −18.3 dBFS active RMS, soft voice −31.4 (13.2 dB quieter than the
  calls), room tone −46.9 (soft voice 15.5 dB above it). `proof/sound_rms_dbfs.png` is the track's level over time.

Judged only by viewing (not by me): whether the choices read as choices, whether the collage is legible and has the
expressive roughness the method promises, whether the dog reads as a dog in every frame.

## The sound

Synthesized. Voice: flite speech synthesis (ffmpeg's libflite, voice "slt"), two calls and three soft lines; each line's
first sound starts 0.15–0.2 s before the dog's choice so the cause is heard before the effect. Room tone of dusk air and
crickets; claws on boards placed at each foot-fall of the gait (from the exposure sheet); a whimper as it turns its back;
breaths as it lies down and settles; a dry tap of card when a card is swapped (the turns, the head cards); a door creak;
a reed-organ chord when the lamp's light comes out, and another when it lies across the sill. **I cannot listen**: levels
and timing are measured; whether it sounds good is unknown. The synthetic voice is plainly synthetic.

## What failed and what I changed (see ledger.jsonl)

- First head cut took the whole mane: lying, the dog read as a seal. Cut the head smaller at the neck line.
- A chest point of the torso card poked below the boards when lying (a triangle under the chest). Re-cut the chest.
- The face print looks down and to the left, not right: the head and jaw are flopped on the table, the jaw re-cut with
  the hinge at the ear.
- Feet slid up to 10 px at the start of the approach (blending into the gait). Replaced by a planted start: each foot
  stays where it stood until its first swing. Max slip now 1.9 px.
- The trace's facing first measured head position against the torso, so the look back at 7.458 read as 8.08. Facing is
  now measured as the direction the head card points from the neck pin.
- The voice takes had 0.25 s of leading silence: the dog backed away before the call was heard. Trimmed and led.
- Lying bodies were tilted rear-up 3°; levelled. The low hand was too low to read as offered; extended.
- Disk full mid-encode (shared machine); the film is a two-pass 2.1 Mb/s encode (10.7 MB).

## What is still weak (my view, not a verdict)

- The dog is small in a wide, locked-off shot (about 210 px long); the archive print is blurry and its head reads as a
  blob with a raised muzzle; at times it looks more hyena than dog.
- The half-way exposures of lying down and getting up (legs part-swivelled) look like a sprawl for two or three
  exposures.
- The person is crude: a box-edged hat card, wide smock, the face mostly in shadow; the closed jaw shows its cut as a line.
- The back-of-head card is constructed, not found, and simple.
- Rigid single-piece legs cannot bend, so the crouch is mild.
- The voice is synthetic; music and effects are synthetic.

## What I did not do

No physical paper, no filmed tabletop test, no access to the broadcast or any Gilliam material, no independent critique
(that is for the critic), no camera moves, no on-screen typed prompts (the voice carries the prompts), no Quick, Draw!,
no publishing of an operator page outside this folder (a local `index.html` is here).

## Rebuild

`build/make.sh` (cut pieces → voice → exposure sheet → render + trace → cards → sound → measure → stills → encode →
check). Intermediates in `build/cache/` (regenerable; scene frames are deleted after encoding to keep the shared disk lean).

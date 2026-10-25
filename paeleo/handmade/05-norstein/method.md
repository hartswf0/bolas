# SCION 05 · Yuri Norstein: atmospheric multiplane cinema. The threshold, handmade

## Thesis (what the viewer should feel)

Depth, obscurity and reveal carry the dog's mind. While it is commanded, fog fills the porch between the door and the dog,
and the dog is a dark shape in it. When the circumstances change (the person sits, the door opens), light comes out of the
house and passes through that fog toward the dog. The dog comes along the light with its head low and lies down where the
light meets the porch. When it is told to *come in*, the focus follows its look deep into the lit room, to the bowl on the
floor (the expected distant object), and comes back to the dog, which stays by the nearer hand. Without the depth this
would be bland: a dog walking left across a flat set.

## The swarm (smallest capable, merged roles)

One builder session played the coupled roles: multiplane cinematographer and depth-stage engineer (`common.py` camera and
focus curves, `render.py` compositor), atmospheric light specialist (fog fields, door light), cutout animator (`dog.py`,
`person.py`) and sonic-space composer (`sound.py`). The roles were merged because every choice crosses them: the fog's density
at the dog is tuned against the dog's silhouette and the focus schedule in the same frame. **No independent critic has
judged this film yet.** Every judgement below that says "looked" is the builder looking at its own frames, which the doctrine
says cannot approve the work.

## Native formal language, as first-class objects in the build

- **Glass planes at z distances.** Painted once in world metres and laid at depth Z under a pinhole camera
  (`build/world.py` -> `build/cache/planes`; the graph is exported to `proof/scene.json`). Far to near: sky (Z 400),
  far trees (32), fog (22), near trees and fence (15), yard, fog (10), the room's back wall (8.2), the room's floor
  (ray-cast), the lamp, chair and bowl (6.6), the room's haze (5.6), the door leaf and the jamb reveals (5.05 to 5.97),
  the house front with the doorway cut out (5.0), the porch boards, sill, step and fascia (ray-cast, 3.8 to 5.0),
  haze (4.88), the person (5.02 -> 4.70) and the dog (4.55 -> 4.81) in depth order, the porch fog bank (4.25),
  posts and eave (3.85), ground fog (2.9), hanging leaves (2.1), weeds (1.9). Parallax is not a per-layer speed number:
  it follows from Z under a camera that pans (X), drops (Y) and trucks in (Z).
- **Diffusion and fog fields.** Six fog planes. Their density is keyed from real time-lapse cloud footage (*Top Of The Cloud*,
  public domain): white and unsaturated pixels are fog. The bank's top edge becomes the undulating top of the ground fog;
  the inside of the bank becomes haze. Each field is shaped by a profile in world X and Y and lit by the door light. The
  porch bank is an actor with four states recorded per frame (`atmosphere` in trace.json): **obscure** (1.0 to 6.2 s: the
  bank between door and dog thickens and rolls out toward the dog), **lure** (6.2 to 14.7 s: lit by the door, drawn in
  toward the light), **reveal** (14.7 to 23.8 s: it parts along the dog's way), **suspend** (23.8 s on: it hangs still).
  The fog also thins round the dog itself, most at each of its choices, so the silhouette is readable exactly when it acts.
- **Exposure and focus schedule.** One curve each (`common.py`, `proof/scene.json`). The film opens focused on the weeds
  and finds the dog by 0.95 s; it racks into the room as the door opens (6.3 to 7.38 s) and back to the dog before it
  turns; at *come in* it holds on the dog while its head turns in (26.45 to 26.95), then racks into the room to the bowl
  (27.3 to 27.55) and back to the dog by 27.95. Exposure: the blue hour darkens by 12 % over the scene while the house
  light grows. Defocus is per glass: blur = 16 px × |z − z_focus| / z.
- **Cutout silhouette.** The dog and the person are flat cutouts, painted dark, edged by the light (see below).
- **Depth audio.** Every source is placed by where it is on screen and given distance and a reverb send; the room is heard
  muffled through the ajar door and opens up when the door opens and as the camera comes in; the dog's footfalls are muffled
  while the fog obscures.

Time base: scene frame i at 24 fps, t = i/24; world: metres, X along the porch (the score's x, door centred at 0, sill
at 0.56, steps at 4.9), Y up, Z depth. Dependencies: Python 3, numpy, Pillow, ffmpeg. Seeds are fixed in the scripts.

## The dog: what it is made of and how it moves

**Round 2 (current): a library of hand-cut replacement pieces, hinged.** A Norstein puppet is a set of flat, painted
pieces hinged at joints and moved by hand under the camera, with replacement pieces (another head, another body) for new
angles. The dog is now exactly that (`build/pieces.py`):

- **The library** (`build/cache/pieces/`, cut once): body pieces per view (L facing the door, BL three-quarter rump to us,
  B rear, FL three-quarter chest to us, F front; R, BR, FR are the same pieces turned over, as a cutout painted on both
  sides) and per posture (standing, half crouch, full crouch; three stages of lying down, so lying down and getting up are
  replacement drawings, not a tween); head pieces per view (the same eight views, five drawn), per ear state (laid back,
  half, pricked) and eyes open or shut, the turned-away heads drawn in lost profile (cheek and ear, no eye); separate
  pieces for upper and lower foreleg, thigh, shin and hock, two paws (side and front), three tail pieces and a neck.
- **How a piece is made:** its outline is taken off the maquette at that view (the maquette is the cutting guide, like an
  animator's sculpted reference), then cut: the edge wobbles like a scissor cut and, on coat pieces, breaks into short hairs;
  it is painted once with its own brush strokes along its grain and the archive dog's coat grain; the cut edge is darkened.
  A piece never changes shape between frames.
- **Per frame:** the maquette, posed by the controller and the foot solver, is only a guide for where the hinges are. The
  pieces are chosen (body view and posture, head view, ears, eyes), hinged on those points (rotated in the plane; a limb
  piece may stretch a little along its length to keep a planted paw on its spot), laid on the dog's glass far to near, the
  far legs laid in their shadowed cut, and each piece casts a soft shadow on the pieces under it. The pieces' names are in
  trace.json for every frame.
- A turn is a run of substitutions: the refusal goes L, BL, B, BR, R (the rear piece shows the back); the turn back to the
  door goes R, FR, F, FL, L with the head piece already in profile toward the door.

Round 1 (superseded): the same maquette was flattened every frame into projected ellipses (a rig look the critic rejected).
Its proportions still come from the archive dog's rig keys (kit/archive-dog, frame 0).

Acting (`dog.py controller`): the six choices and their times come from the score; the body performs them this way:

- **Retreat (1.0 s).** Backs away, crouched, hindquarters dropped, tail tucked, ears flat, head low. The feet step backwards.
- **Refusal (3.42 s).** Turns away from the camera, head leading (spine bend and neck), through the rear view at about 3.65 s,
  done by 3.92 s; the head is carried high enough in the turn to show above the back, then sinks; it lies down with its back to the
  door and its chin on its paws (the score's lie and rest values) until 7.46.
- **Turning to look (7.46 s).** The chin comes off the paws at 7.36; the head lifts and is replaced in two steps (front
  view at about 7.5, profile toward the door from 7.56) and the profile head is held, looking at the door, while the dog
  stands (lying pieces 0.66, 0.33, standing) and the body is replaced round through the front view (8.0 to 8.95 s).
- **Watching (9 to 14.7 s).** Faces the door; small looks between the low hand and the light; breathing; a blink.
- **Coming (14.71 s).** Walks toward the door with the neck held 40 degrees below level, so the head is below the line of
  the back for the whole approach; its path angles in toward the doorway over the last 1.6 m.
- **Lying down across the sill (23.79 s).** Lowers to the boards in about 0.6 s: forelegs along the boards, hind legs folded
  under the haunch, tail out on the porch. The front of the dog is in the doorway's span and in its light; the back half
  and the tail are outside.
- **Looking in (26.4 s).** Ears up, the head piece is replaced by the lost-profile head (turned away from the camera, into
  the room) and lifted toward the lit doorway; the tail sweeps the boards; the focus follows the look into the room from
  26.85 s (the bowl sharp at 27.25 to 27.5) and returns by 27.95; then the chin goes down onto the paws, facing the
  person's low hand, and the eyes close (30.3 s).

Feet are solved, not tweened: a foot on the boards keeps its world position until the body has left it by 11 cm (7 cm
while turning), then it is lifted (a sine arc) and put down ahead; at most two feet are off the boards, never two on one
side or two of one girdle. While lying, the legs take an explicit folded pose. The footfalls the solver reports are the
times of the nail clicks in the sound.

The person is a flat jointed cutout in profile (head, hair, torso coat, two arms, hands, two legs, feet) keyed to the
score's circumstances: beckoning on the first call, leaning and reaching on the second, stepping back out of the doorway,
sitting on the boards beside the door, the near hand down on the boards, palm up, the head bowed on the soft words.
In the doorway it is backlit (dark, ringed with warm light); seated, it is lit on the side toward the door.

## The camera as attention

Wide on the doorway and the dog for the calls; as the person steps aside and sits (4.3 to 5.5 s) the camera eases back
and left, so the person sitting, the door opening (6.2 s) and the low hand are fully on screen with the dog (round 1
pushed in on the dog here and lost them at the frame edge; the critic flagged it). Focus goes into the room as the door
opens (6.25 to 7.12 s) and is back on the dog before it turns to look; the porch fog bank lifts off the dog from 6.6 s.
During the approach the camera pans with the dog and trucks in (14.6 to 23.6 s), the near posts and weeds passing with
real parallax; at the sill it settles closer still.

## Sound (synthesized here; nothing recorded)

Air (shaped noise), crickets in the yard, the room's hum and clock heard through the door, a formant-synthesized voice
(two calls, *come here*; soft *it's all right* twice; soft *come in*), nail clicks at the solver's footfalls, the body
going down to the boards with a breath out (twice), the tail on the boards while it looks in, a long sigh as it settles,
a latch and a creak as the door swings in, a sparse score of glass tones entering with the light and resolving at the sill.

Measured levels (proof/audio_levels.json; RMS dBFS of each stem's active samples after the master gain): calls
-15.47 and -12.78; soft *it's all right* -25.97 and -26.38; soft *come in* -26.98;
room tone in those windows -35.15 and -33.81. The soft voice is
10.5 dB under the quieter call and at least 6.83 dB over the room tone.
**Measured, not heard:** the builder cannot listen. proof/spectrogram.png pictures the final mix (0-12 kHz over the 38 s); it is a picture of the sound, not a listening.

## Protected conditions and measurements

`python3 tools/paeleo/check_handmade.py paeleo/handmade/05-norstein` -> **ALL OK** (invariants.json).

| score t (s) | choice | measured first frame (s) | dt |
|---|---|---|---|
| 1 | retreat | 1.0833 | +0.083 |
| 2.333 | watch | 2.4167 | +0.084 |
| 3.417 | refuse | 3.5833 | +0.166 |
| 7.458 | watch | 7.5 | +0.042 |
| 14.708 | approach | 14.7917 | +0.084 |
| 23.792 | lie_down | 23.9167 | +0.125 |

- I2: the measured position never goes below 0.5661 m (sill 0.56) and ends at 0.5974 m.
  At the end 41 % of the dog's silhouette lies within the doorway's span (X < 0.46 m) and the tail end is at
  1.26 m, outside the jamb; the front of the dog is in the door's light (measured from the render: trace.json,
  inside_frame_share, tail_end_x).
- I3: correlation of the measured position (x_world_measured, the torso pass centroid unprojected at the dog glass depth,
  because the camera moves) with the score's x: r = 1.0 over 768 frames.
  The mapping is the identity (the porch is the score's X axis), so the approach covers the same distance at the same pace.
- I4: 100 % of the refusal frames are measured facing away.
- Head low on the approach: in every frame measured as coming, the head pass's top is below the torso pass's top
  (head_above_back between -0.139 and -0.021 of the silhouette height).
- Feet: planted feet do not move in the solver (0 m over 1,522 planted foot-frames while standing or walking). The drawn
  paw sits at the end of the leg chain and lags a planted foot by at most 1.2 cm. Three single frames in the two spins
  (3.58, 8.29, 8.54 s) have three feet off the boards. While lying down and getting up, the legs fold by an explicit
  pose and the paws do move on the boards; they are not held there.

**How the trace is measured** (assemble.py): position = the centroid of the torso ID pass, unprojected at the dog glass's
depth; facing = which side of the laid head piece's hinge its nose lies on (left = to the door); travel = the paws and
the body moving together (7-frame smoothing); height = the silhouette height in metres at the dog's depth (lying < 0.55 m).
State: lying at the sill -> lie_down; facing away -> refuse; travelling away from the door at > 0.08 m/s with the head
below its alert carriage -> retreat; travelling toward it at > 0.12 m/s, sustained 0.75 s -> approach; otherwise watch.
These thresholds are a measurement model the builder chose and tuned against this render (see ledger 11-13). They are a
structural record, not a judgement that the choices read.

## What failed and what changed (full list in ledger.jsonl)

1. **maquette pose sheet v1 (proof/poses_a.png, first version).** Saw: reads as a bear/pig: torso too fat, legs short and splayed, thick stick tail, ears tiny; rear view a blob; lying hind legs sprawl back like a frog Changed: slimmer chest/waist/hip, bigger head and ears, thin tapering tail
2. **pose sheet v2 at film scale.** Saw: dog-like; legs bend too much (too long for the height), a lifted paw detached from its leg mid-turn, approach head level with the back (not below) Changed: shorter limbs; paws attached to the IK chain end; depth tone inside the puppet (far pieces darker)
3. **pose sheet v3 (proof/poses_b.png).** Saw: front and rear views read (chest+forelegs; rump+hind legs+tucked tail), the look-back over the shoulder reads; approach head still at the back line; lying hind thigh sticks out Changed: approach neck angle -40 deg (head below the withers); lying pose re-cut
4. **first composited frames 1, 3.6, 9, 19, 28 s.** Saw: structure works (doorway light, porch, person, dog), but there is no fog to speak of; the person sits in a squat floating below the boards; still at 28 s caught mid rack-focus Changed: fog colour lighter, density from cloud footage with contrast; sit pose re-angled; return rack ends by 27.85 s
5. **frames with keyed cloud fog.** Saw: fog reads as real fog, but the cloud bank top edge painted a cloud line across the wall; the dog at 3.6 s is nearly lost in it Changed: two fog sources: the bank edge only for ground fog and the bank (tops at 0.75 and 1.55 m), the cloud interior for haze; darker coat; fog thins round the dog, most at its choices
6. **lying pose sheet (proof/poses_d, poses_e).** Saw: lying read as a cat about to pounce (chest high, neck stood up, ears like spikes) Changed: torso lowered to the boards, haunch widened, neck capped at 22 deg when lying, ears shortened, look-in yaw reduced so the muzzle shows
7. **sound v1 levels (proof/audio_levels.json).** Saw: soft voice 12.7 dB under the calls, but only 3 dB over the room tone Changed: soft voice +2.3 dB, room -3 dB: soft 10.5 dB under calls, 6.8 dB over room (measured; not listened to)
8. **camera v2: push in on the refusal, pull back as the door opens.** Saw: the dog is larger in its refusal; the look back (7.46) still faced the camera from the front end of the body: the chin-on-paws rest pose held the head at the front Changed: rest released at 7.36, head lifted to 48 deg during the look back, yaw to -2.8 rad, spine bend -0.7: the muzzle now points back over the shoulder, above the back line (proof/poses_f.png)
9. **contrast at the choices.** Saw: dog lum ~56 vs surround ~76: murky grey in grey fog Changed: coat darker (50,42,39), cool rim 0.5, fog clears 60-95% round the dog at its choices
10. **process error (not a film attempt).** Saw: to stop my own render I ran pkill -f render.py, which matches every render.py on this shared machine; it very likely killed other swarms' renders (03-ernst, 06-whitney, 54-provenance-graph were running render.py). Their processes restarted afterwards. Changed: stop only by PID from now on; reported to the caller
11. **full cut r1 (768 frames, 2200 s on a shared, loaded machine); check_handmade.** Saw: I1 failed: the measured refusal came at 3.83 s (score 3.417): facing was measured from head vs torso centroid, which flips only when the head passes the middle of the body; the look back was measured late for the same reason; the trace had spurious "approach" runs during turns in place; lying was not detected at the sill because silhouette height was in pixels while the camera trucks in Changed: facing measured from the cut nose piece against the skull piece; travel measured on the paws and the torso together; height in metres at the dog glass; coming must be sustained 0.75 s, backing 0.25 s
12. **acting repairs for the measured choices.** Saw: the dog kept its head low for 0.3 s after the score says it stops backing (2.33): the choice to watch did not read Changed: head comes up at 2.33 while the body still drifts; the refusal turn shortened to 3.40-3.92 with the head leading by 0.55 rad
13. **check after repairs.** Saw: ALL OK: choices at +0.167, +0.042, +0.208, +0.084, +0.167, +0.083 s; min x 0.566, end x 0.597; r = 1.0; refusal turned 100 % Changed: -
14. **looked at the cut at 2 fps (proof sheets) and the four stills at full size.** Saw: at 28 s the head reads as looking at the person, not into the room Changed: looking-in head yaw -0.5 -> -0.82 rad and lowered; in silhouette against the doorway the muzzle then hides: the rack focus into the room carries the rest of the beat (judgement, not measured)
15. **foot audit.** Saw: planted feet never move in the solver (0 m over 1522 planted foot-frames), but in the quick refusal turn the body outran a forefoot by up to 15 cm, so the drawn paw (at the end of the leg chain) dragged; on walking strides it lagged up to 3 cm Changed: a foot the leg cannot hold steps at once; faster steps while spinning; legs 1 cm longer per segment: drawn-paw lag on planted feet now <= 1.2 cm; three single frames with 3 feet off the boards in the spins (3.58, 8.29, 8.54 s)

## Honest evidence

- **Measured:** the trace (from the render's torso and head ID passes and the silhouette, unprojected at the dog glass's
  depth), the PAELEO invariants (`check_handmade.py`), the audio levels (RMS of the synthesized stems after the master
  gain), file size and format of film.mp4.
- **Structurally verified:** that the dog's state, position, facing and posture in trace.json come from the render's own
  passes and not from the score (the score's state is kept beside it as `state_score`); that every asset in assets.json is
  public domain or made here.
- **Looked at (by the builder only):** extracted frames and crops at every repair (proof/ and the stills). The builder judged
  the turns, the look back, the head-low approach and the lying pose from those frames. That is not acceptance.
- **Unknown:** how the film plays at normal speed to a fresh viewer; how the sound sounds. The builder cannot listen: the
  synthesized voice is very likely mechanical, and whether *come here* and *it's all right* are intelligible is unknown.
  No independent critic has watched the film.

## What this swarm did not do

- No Quick, Draw! drawings, no archive door footage, no other found shots were used (listed in assets.json).
- No independent critic run; no forked competing branches (no failure has yet resisted two meaningful fixes).
- No real voice recording; no lip or mouth animation on the person.
- The door light does not cast the dog's shadow onto the boards (only a soft contact shadow under each figure).
- The operator page (index.html) is a local file, not published.

## Round 2: the critic's repairs and what was done

Critic round 1 (reviews/round1.md): DOES NOT PASS, close. Repairs as ranked by the coordinator, and what changed:

1. **Turning to look (7.46).** The chin is released at 7.36; the head is replaced by a front head at about 7.46 to 7.5
   and by the profile head toward the door from 7.54, which is held (looking at the door) through the rise and the
   body's turn to 8.95. Measured: facing (nose of the laid head piece vs its hinge) is 'door' from 7.50 s. The porch fog
   bank lifts off the dog from 6.6 s and the fog clears round the dog at 7.0, 7.46, 7.9 and 8.4 s; focus is back on the
   dog by 7.12 s. Looked at: every frame 7.29 to 8.58 s (contact sheet of crops): no headless frame; legs visible
   throughout the rise.
2. **Looking in (26.4).** The head piece is replaced at 26.46 s by the lost-profile head (turned away from the camera, no
   eye) and lifted into the lit doorway; focus follows from 26.85 s to the bowl (27.25 to 27.5) and returns by 27.95.
   Looked at: every frame 26.21 to 27.21 s.
3. **Language.** The dog is now a library of hand-cut, painted replacement pieces hinged per frame (see "The dog" above);
   21 body and head pieces plus 11 limb, neck, tail and paw pieces are in use (build/cache/render.log).
4. **Framing.** The camera no longer pushes in on the refusal; it eases back and left from 4.3 to 5.5 s, so the person
   sitting (5.4) and the door opening (6.2) are fully on screen (looked at 5.42, 6.21, 6.67, 7.0 s).
5. **Hindquarters.** The hind legs are separate pieces laid over or under the body piece by depth, so thigh, shin and
   hock keep their shapes in the crouch (1.4 to 2.3) and the rise (7.5 to 7.7) (looked at).

Kept: the glass planes and parallax, the fog's four states, the focus pull to the bowl, the head-low approach, the sound
(unchanged, re-synthesized from the same seed and the new footfalls).

## Round 3: the critic's repairs and what was done

Critic round 2 (reviews/round2.md): DOES NOT PASS (narrowly). What changed:

1. **Looking in.** A dedicated back-of-head piece is cut by hand (skull, both ears standing, darker nape; no face, no
   eye): the maquette's back view had its ears edge-on. From 26.46 the head goes to the lost profile and from 26.67 to
   the back of the head, turned straight away into the room toward the bowl at level gaze, held until the focus pull
   begins at 26.96 (looked at every frame 26.21-27.17).
2. **Hindquarters.** In the retreat crouch the rump drops less and the tail hangs behind the hocks instead of tucking
   between them; every cut edge that lies over another piece now shows a thin pale seam, and the far legs are lighter,
   so thigh, shin and hock of both hind legs read separately (looked at every frame 1.21-2.50; the legs are still dark
   against a dark wall in fog). Lying down and getting up: the paw travels and the joints bend by IK (no crossing).
   The guide is posed at the chosen pieces' own view angles, which removed the ghost at 3.75.
3. **The walk as replacement pieces.** The dog is shot on twos: each placement of its pieces is held two frames while
   the camera and fog move on ones; the seams are visible (looked at every frame 15.00-16.00).
4. assets.json describes the piece library; the person is grounded on its lowest point every frame and sits through a
   squat; the audio master peak is 0.75 (film -2.3 dBFS by ffmpeg volumedetect).

## What is still weak (the builder's view, for the critic to confirm or overturn)

- The dog is small in the wide shots (about 180 px long) and fog-soft through the refusal; at 6.3 to 7.2 s, while the
  camera pulls back and focus is in the room, it is barely visible. That is the obscure state, but the critic may find
  it too dim.
- Looking in (26.4 s): when the muzzle turns into the room it hides behind the skull, so the silhouette shows a round head
  with pricked ears against the doorway. The rack focus into the room carries the rest of the beat. It may read as
  "looking up" or "looking at the person".
- The rear-view body piece (about 3.6 s, two frames) is the most generic drawing; the limbs are plain strips, so the
  puppet reads as a jointed toy as much as a painted Norstein figure.
- The back-of-head piece is simple (a round with two ears): it may read as feline.
- The person still passes through a brief squat with the seat off the boards (about 5.7-5.9 s).
- The dog is still dim in the fog during the refusal (4.5 to 7.2 s), by design of the obscure state.
- The ears are pointed and stiff; the person is a plain mannequin-like cutout.
- The voice is formant-synthesized and almost certainly mechanical; intelligibility is unknown.
- Trace thresholds were tuned against this render (see above).

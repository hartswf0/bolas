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

A Norstein cutout is a set of flat pieces moved under the camera, with replacement pieces for new angles. Here the
replacement pieces are cut every frame from a small 3D maquette: chest, waist, hip, back and withers ellipsoids, a neck
of three ellipsoids, skull, muzzle and nose, ears as flat triangles, legs as tapered strips (two segments in front, three
behind), a six-segment tail. Each frame each ellipsoid becomes the flat ellipse it projects to, each limb a flat strip,
each ear a triangle; the pieces are laid on the dog's glass far to near, the far legs painted darker, and the whole
cutout is painted with a coat grain cut from the archive dog's own film, its edge broken into short hairs. The maquette's
proportions come from the archive dog's rig keys (kit/archive-dog, frame 0). Because every piece keeps its thickness, a
turn passes through a real rear view (rump, hind legs, the head carried above the back) and a real front view (chest,
forelegs, face) instead of an edge-on sliver.

Acting (`dog.py controller`): the six choices and their times come from the score; the body performs them this way:

- **Retreat (1.0 s).** Backs away, crouched, hindquarters dropped, tail tucked, ears flat, head low. The feet step backwards.
- **Refusal (3.42 s).** Turns away from the camera, head leading (spine bend), through the rear view at about 3.8 s, done by
  4.12 s; the head is carried high enough in the turn to show above the back, then sinks; it lies down with its back to the
  door and its chin on its paws (the score's lie and rest values) until 7.46.
- **Turning to look (7.46 s).** The chin comes off the paws at 7.36, the head lifts high and swings back over the shoulder
  to the door, muzzle pointing left, by 7.58; it stands (7.5 to 8.0) and the body follows through the front view (8.0 to
  8.95 s).
- **Watching (9 to 14.7 s).** Faces the door; small looks between the low hand and the light; breathing; a blink.
- **Coming (14.71 s).** Walks toward the door with the neck held 40 degrees below level, so the head is below the line of
  the back for the whole approach; its path angles in toward the doorway over the last 1.6 m.
- **Lying down across the sill (23.79 s).** Lowers to the boards in about 0.6 s: forelegs along the boards, hind legs folded
  under the haunch, tail out on the porch. The front of the dog is in the doorway's span and in its light; the back half
  and the tail are outside.
- **Looking in (26.4 s).** Ears up, the head turns in toward the lit room, the tail sweeps the boards; then the chin goes
  down onto the paws, facing the person's low hand, and the eyes close slowly (30.3 s).

Feet are solved, not tweened: a foot on the boards keeps its world position until the body has left it by 11 cm (7 cm
while turning), then it is lifted (a sine arc) and put down ahead; at most two feet are off the boards, never two on one
side or two of one girdle. While lying, the legs take an explicit folded pose. The footfalls the solver reports are the
times of the nail clicks in the sound.

The person is a flat jointed cutout in profile (head, hair, torso coat, two arms, hands, two legs, feet) keyed to the
score's circumstances: beckoning on the first call, leaning and reaching on the second, stepping back out of the doorway,
sitting on the boards beside the door, the near hand down on the boards, palm up, the head bowed on the soft words.
In the doorway it is backlit (dark, ringed with warm light); seated, it is lit on the side toward the door.

## The camera as attention

Wide on the doorway and the dog for the calls; while the dog refuses, the camera pushes in and drops toward it (4.15 to
5.7 s), so the turned back is seen close in the fog; as the door opens it pulls back to the wide (6.05 to 7.4 s), so the
seated person, the low hand and the light are on screen before the dog turns to look; during the approach it pans with the
dog and trucks in (14.6 to 23.6 s), the near posts and weeds passing with real parallax; at the sill it settles closer still.

## Sound (synthesized here; nothing recorded)

Air (shaped noise), crickets in the yard, the room's hum and clock heard through the door, a formant-synthesized voice
(two calls, *come here*; soft *it's all right* twice; soft *come in*), nail clicks at the solver's footfalls, the body
going down to the boards with a breath out (twice), the tail on the boards while it looks in, a long sigh as it settles,
a latch and a creak as the door swings in, a sparse score of glass tones entering with the light and resolving at the sill.

MEASURED_AUDIO

## Protected conditions and measurements

MEASURED_INVARIANTS

## What failed and what changed (full list in ledger.jsonl)

LEDGER_SUMMARY

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

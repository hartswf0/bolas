# SCION 23 · Spine — Skeletal Motion Runtime · PAE-02 threshold

## Thesis

The dog is a game-ready actor and the film is its runtime playing. Nothing in the 32 s scene is animated by hand
frame by frame: a 2D skeletal runtime (written for this film, `build/runtime.py`) reads a skeleton JSON, a clip
library and a track timeline and poses the dog for each of the 768 score frames. The dog's choices come from *which
clip is queued when*, and the body stays a body because the blends are made of bone rotations, attachment swaps and
slot reorders, never of stretched pictures.

What would make it bland: a flipped sprite at the turns, feet skating on the boards, and a head that waits for the
body. Those three are what the runtime is built to avoid.

## The actor (files in `actor/`)

- `dog.skel.json` — 28 bones (root, hips, chest, neck, head, two ears, three tail bones, three bones per foreleg,
  four per hind leg, four IK targets), transform mode "noScale"; 20 slots with draw order; one skin with **region
  attachments** (head in 7 views, neck in 2, ears in 3, 14 leg segments near/far) and **weighted mesh attachments**
  (the torso in 4 body views, skinned to hips and chest; the tail, skinned along tail1-3); 4 **IK constraints**
  (two-bone legs; the paw, and for hind legs the metatarsus, keep their posed world angle).
- `actors.png` + `actors.atlas` (libgdx/Spine text format) + `actors.atlas.json` — the **texture atlas**, 46 regions
  (dog and person), painted in code.
- `dog.clips.json` — the **clip library**: idle, cringe-back, turn-away, lie, look-back, rise, stalk-walk,
  lie-across, look-in, settle. Each clip has bone timelines (rotate/translate/scale), slot attachment timelines,
  draw-order timelines, IK-mix timelines and events (whimper, thump, jingle, sigh). Values are absolute local values.
- `dog.timeline.json` — the **track timeline**: clips queued on track 0 (body) and track 1 (head) with mix durations.
  The end card draws this file.
- `person.skel.json`, `person.clips.json` — the person, a second, simpler actor (one clip baked from the score).

### How the views are made (turns)

Spine has no 3D. Turnarounds are authored: `build/turnaround.py` is a turnaround sheet — the dog's joints in its own
3D frame, posed by a few acting parameters (lie, crouch, neck, head, ears, tail) and projected through the film's
camera at a body view angle (0 = facing the door, 90 = back to the camera, 135 = facing away and right). It is used
only at authoring time: to place each view's setup, to bake every clip key into 2D bone values, and to lay out the
painted regions. The runtime never sees 3D.

A turn (turn-away 0→135 deg, rise 135→0 deg) is therefore a clip whose keys walk the bones through the views, swap
the torso mesh (views 0/45/90/135), the head region (0/45/68/90/112/135), the neck and ear regions and the leg
attachments (near legs lit, far legs shadowed), and re-key the draw order: the far legs and far ear go behind the
torso, at 90 deg the hind legs and tail come in front and the head goes behind, at 135 deg the dog's right side is
the near side. In between keys the torso mesh foreshortens through its hips/chest skinning, so swaps land on a
silhouette that already matches. The head of turn-away runs 0.12 s ahead of the body.

### The track mixer

`AnimationState` keeps entries per track; within a track the incoming clip cross-fades the outgoing one channel by
channel over its mix duration (positions linear, rotations by the short arc, IK mix linear); attachments and draw
order switch at alpha 0.5. Track 1 (head) is layered over track 0 on the neck, head and ear channels and the head
attachment; an empty entry mixes it out. At 7.40 s `look-back` on the head track lifts the head off the paws and
turns it over the shoulder to the door while track 0 is still playing `lie`; `rise` starts on track 0 at 7.62 s;
the head track hands back at 7.95 s. At 26.35 s `look-in` turns the head into the room (head view 68 deg: the back
of the skull and both ears to the viewer, muzzle level, inside the lit doorway); `settle` lays the chin on the paws.

### Feet

The legs are not keyed while standing or walking: the dog's root rides the score's x (root motion separated from
joint motion), and a foot planner plants each paw where it landed and holds it there by IK while the IK mix is on.
A paw steps (timed swing with a lift) when the pose wants it elsewhere or the leg nears full reach; at most two paws
swing, never both of one girdle; in the fast scramble backwards (> 0.4 m/s) it trots in diagonal pairs. Lying and
rising clips key the IK mix down to 0 and fold the legs by FK. Touch-downs are events: they make the paw sounds.

## What the dog is made of, how it looks

Painted game-art parts: tan coat, dark saddle, cream chest and muzzle, banded gouache shading (cool violet shadows,
warm lights), dry-brush strokes, a wash, paper grain, and a slight broken warm-brown outline that is drawn only along
the long sides of limb parts so joints tuck under. The set and the person are painted in the same hand. Seen beside
swarms 19 (flat outlined cartoon), 25 (flat vector), 33 (lit capsules) and 37 (textured 3D), this is a painted
cut-out actor.

## Protected (and how it was checked)

MEASURED_BLOCK

## What failed and what I changed (ledger.jsonl has each attempt)

- First atlas: the torso and head as ray-cast ellipsoid unions read as a pile of balls (a maquette). Changed: the
  silhouette is rounded and lit from a soft 2D height field, flatter gouache bands, more strokes.
- First assembly: capsule legs with outlines at both ends read as a jointed mannequin (too close to swarm 33), the
  neck as a pipe, the head too small. Changed: outlines only on the long sides; near upper legs drawn under the
  torso; head 1.2x; a tapered neck with a dorsal stripe per side (two authored attachments).
- Look-in first used head view 45 (reads as a profile with an eye). Added authored head views at 68 and 112 deg so
  the look-in shows the back of the skull and both ears.
- Legs: the first lying fold sent hind paws through the floor (angle interpolation). Changed: paw and hock targets
  travel above the floor and the leg is re-solved, so no bone changes length. IK bend sides flipped in the crouch;
  fixed by choosing the knee by the sign of cross(girdle->target, girdle->knee) and lowering the hock in a crouch.
- The foot planner left hind paws 40 cm behind in the 0.76 m/s scramble backwards (gait rules blocked steps);
  fixed with a candidate loop that skips blocked legs and a diagonal-pair trot above 0.4 m/s.
- The forelegs could not reach their footprint standing (2.5 cm short); lengthened 1 cm per segment.

## What is weak

WEAK_BLOCK

## What I did not do

- No independent critic was run by me; I looked at frames myself, which is not approval.
- No real Spine editor or official runtime: the JSON follows Spine's shape (bones, slots, skins, region and weighted
  mesh attachments, IK, timelines, events, a libgdx atlas) but it is my own runtime and conventions (absolute
  timeline values, full draw-order lists, "keepWorldRotation" on IK); it will not load in Esoteric's runtimes as is.
- No mobile operator page, no frame-rate benchmark on a phone; the runtime poses all 768 frames in about 3 s on this
  machine (Python), measured once, not a device benchmark.
- No found footage, kit images or Quick, Draw! drawings: everything is made in code.
- The voice is a formant murmur, not intelligible speech; the words are given as subtitles.

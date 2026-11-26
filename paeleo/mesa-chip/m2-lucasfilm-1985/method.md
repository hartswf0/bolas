# SCION-LUCASFILM-1985 · Lucasfilm Computer Division 1985: convex shard CG. PAE-09, MESA CHIP

**Film:** `film.mp4` (960×540, 24 fps, H.264 + AAC, 24 s). **Rebuild:** `python3 build/render.py` (numpy, Pillow, scipy, ffmpeg).

## Thesis
A creature of flat glass acts, because every pose is keyed by hand and every shard catches its own highlight.

- **The dope sheet.** `build/dopesheet.py`; each key's reason is in `dopesheet.json`.
  - Uncle Mesa's poses: settle, aim, recoil, down, kneel, sit.
  - The knight's poses: look, crouch, air, land, draw, guard, raise, strike.
  - The walk is a keyed cycle (contact, down, passing, up) laid step by step, with Catmull-Rom in-betweens. There is no motion capture and no procedural walk.
- **Ground contact.** The lowest point of each pose is put on the ground, so weight lands.
- **The knight's shards.** 160 convex shards with their own normals, so the highlight travels across the armour and across every falling shard as it tumbles.
- **The passes.** A beauty pass and a separate specular pass with bloom.
- **Motion blur.** Four jittered sub-frames per frame across a 180° shutter.
- **The rack focus.** One computed rack: on Uncle Mesa coming down, to the knight in the far window at the head turn, and back when it leaps.
- **Uncle Mesa** is painted as the plate actor, soft, with a key-light gradient and his own grain: a Black man in his sixties with a long white beard and gold-lensed round glasses, in a cream wide-brimmed hat, a white guayabera-style shirt with the MESA CHIP badge, khaki trousers and dark boots.

## Made of
- `build/dopesheet.py` (the keys) and `build/render.py` (FK, the shard skin, the passes, the plate, the sound);
- the sound: low strings, boot heels on the keyed contacts, glass-and-steel feet, the sword's ring, a glass cascade per shot and the strike's thud.

## Repairs after critic round 1

- **The rack focus.** It finishes on the knight before the head turn, and the visor swings further.
- **The hat.** It stays on the floor until he takes it up as he rises, so it is never in two places.
- **The get-up.** It takes 0.65 s, with one knee down and a hand on the floor.
- **The gun.** It stays down once he sits.
- **Uncle Mesa.** The beard is now distinct from the shirt (whiter, with its own edge, longer), with two round gold lenses, guayabera pleats and pockets.
- **The step.** Brighter.
- **A coda light.** It crosses the pile.
- **Motion blur.** Six sub-frames instead of four.
- **The paint is matte** and holds its colour in shadow. Brighter light scales the glass rather than clipping it, and the light shafts multiply what they fall on, so every shard keeps its hue.
- **The later shots** lie under the earlier ones.

## Measured (from this film's own label mask and pixels, `invariants.json`)

- **I1, events at time:** hold. turns_head 3.0→3.00, steps_out 4.5→4.58, draws 6.0→6.00, raises_gun 6.5→6.58, hit_1 9.5→9.50, knocked_down 12.2→12.29, gets_up 14.0→14.00, hit_2 15.0→15.00, hit_3 16.0→16.00, hit_4 17.0→17.00, hit_5 18.0→18.00, shatter 19.5→19.50, sits 22.0→22.12.
- **I2, out of the glass:** holds. Inside the window in 100% of frames before 4.5 s, outside it in 100% after 5.5 s.
- **I3, the pieces stay, in their colour:** holds. Hue held by shot: #2fd0d8 95%, #f2a83a 92%, #e85aa8 92%, #f2d04a 96%, #2a9a5a 81%, #d8342c 94%.
- **I4, the distance follows the score:** holds. 100% of 335 frames within ±15 %, r = 0.998.

## Judged, not measured
Whether the weight shifts before steps, whether the highlights read as per shard, and whether the knight looks like it could break.

## Known limits
The plate is a painted backdrop, not live action, and Uncle Mesa is a painted figure standing in for the plate actor. The feet can slide a little during the advance, because the keyed cycle is not locked to the score's speed.

# CINEOSIS hybrid pilot: validation record

Each passage puts the crash-lab dummies into the real example clip for that sign on the cineosis-lab periodic table. There are six signs, chosen to test the hardest integration cases. Two fresh critics reviewed the work, one per round. Neither had seen it made, and both judged the frames at 24 fps, not still images.

## The six plates

| Sign | Plate | Case it tests |
|---|---|---|
| 38 Peaks of the present | Hotel and Restaurant Workers: a laid dining table, static, black and white | Occlusion through a rattan chair, and a real glass passing between media |
| 28 Strong destiny | Singing Wires: two men at a desk with an oil lamp | Light: the lamp is turned down and the whole plate is relit |
| 2 Liquid perception | National Wildlife Refuges of Alaska: a raft drifting midstream | Riders on a moving support, with a floating camera |
| 42 Bodies of gest | Mission of Apollo/Soyuz: a row of dignitaries, handheld | Shared floor and scale beside real people |
| 29 Weak destiny | Cabeza Prieta: a ranger on a desert track, camera rising | A moving camera, and occlusion behind a walking person |
| 39 Sheets of the past | Court to Court: a palace corridor, gliding camera | A moving camera, with past copies planted on the floor |

## How each passage is made

- **Plate:** a segment with no cuts, at 24 fps.
- **Camera:** a pinhole camera fitted to the plate.
- **Camera moves:** tracked per frame:
  - raft: template matching and ECC alignment
  - row: phase correlation
  - desert and corridor: floor-feature homographies
- **Animation:** the crash-lab rig, authored in a world laid out to the plate and checked by the lab checker.
- **Dummy layers:** rendered per actor as transparent layers from the plate camera's direction, then mapped into the plate.
- **Shadows:** projected along the plate's light onto walls, desk, cargo and ground.
- **Occlusion mattes:**
  - the rattan chair, keyed on a clean plate
  - polygons for the table, lamp and cargo heap, carried by the track
  - an ISNet matte for the ranger
- **Look:**
  - grade matched to the plate (mono or colour)
  - shading toward the light
  - passed through the plate's native 320×240 resolution, so the softness matches
  - grain
- **Sound:** the plate's own track, or ambience where the plate is looped, with foley placed from foot contacts.

## Rig checker (lab metrics)

- Five worlds are clean.
- In 2 Lq, Bola's loss of balance is flagged as unbalanced, which is intended.
- In 2 Lq, Dot overreaches for 6 frames.

## Critic verdicts

| Sign | Round 1 | Round 2 (after fixes) | Largest failure still visible |
|---|---|---|---|
| 39 Sp | Weak | **Meets the bar** | Copies are barely translucent. Bola only peeks in during the opening tilt. |
| 38 Pp | Weak | Weak | The lifted glass reads as a white smear, not a glass. The patch where it stood has a hard rectangular edge. |
| 42 Bg | Misses | Weak | Toe-down feet at rest. Footsteps stop before the steps do. |
| 28 Sd | Weak | Weak | The knob turn is not visible, so the dim seems to come before her hand. She casts no hard lamp shadow. Her toon scale breaks the size rule. |
| 2 Lq | Misses | Misses | The fall, the catch and the sit do not read. The dummies tower over the crew. The cargo matte is a rectangle. |
| 29 Wd | Misses | Misses | Her feet are not on his ground line at the right scale, so she floats or looks too big. Her reveal from behind him leaks. Her shadow is weak. |

### What the critics confirmed works

- Tracking holds dummies to moving plates within about 2 px (39).
- Wall shadows agree with the plate's own shadows (38).
- The rattan-chair occlusion holds (38).
- The plate dims with the lamp in linear light (28).
- Sound lands on events (38, 28).

## Pipeline fixes needed before the other 39 signs

1. **One scale-and-contact solve per plate, with an automatic gate.**
   - Use the horizon or ground plane and a person in shot.
   - Reject the render if Bola's foot line and head height disagree with her depth or with the 85%-of-a-man rule.
   - Fix one Bola look and grade it per plate.
2. **Proper occlusion and contact.**
   - Roto or keyed mattes instead of rectangles.
   - Flat planted feet with contact shadows.
   - Cast-shadow direction and hardness taken from the plate's key light.
3. **A legibility gate on the action before rendering.**
   - The beat must actually be animated, at a scale where it reads.
   - Cause must come before effect.
   - Any real prop gets its own clean element.
   - Footsteps come from the contacts the animation actually produces.

## Changes from round 1 to round 2

| Sign | Changes |
|---|---|
| 38 | Chair matte keyed to the rattan strokes only. Glass patch feathered. Toast moved toward Bola. |
| 28 | Push-in on the desk. Toon scale enlarged. Globe now dims with the room. Stronger lamp-side shading. |
| 2 | Tighter following crop. Larger toons. Softer, less saturated grade. Bigger stumble and a held catch. |
| 42 | Bola moved to the end of the row, so she is no longer cut up between the men. Soft overhead contact shadow. |
| 29 | Scale measured against the ranger and corrected. Path moved toward the rut. Starts hidden behind him. |
| 39 | Copies made Bola-yellow at 50%. Stronger reflections. |

## Limits

- The crowd plate for 5 Dividual was tried and dropped. Neither human-segmentation model could separate a dense crowd at 320×240, so it is not in the pilot.
- Looped plates (38, 42) cannot carry their own sound past 3.4 s, so they use ambience.
- Dummies have no motion blur.
- Camera tracks are 2D homographies. Parallax off the ground plane is not modelled.

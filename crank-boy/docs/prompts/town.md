# The Town: one world, seven games

Use this to extend `shorts/world.html`, the seven series cards joined as one playable world, or to add an eighth card to it. Read `docs/prompts/shorts.md` first: the Town reuses every cut piece, plate and rule from the shorts.

## The idea

The most useful thing in JibJab is not the face swap. It is a film whose cast can be replaced without making the film again. The Town takes that literally. A **performance** (turn a handle, push a rod, pull a lever) is kept apart from the **actor** who performs it, so any handle-holder cut from any card can stand in any other card's place. The choreography does not change; only the cast does.

Three more lines run through it:

- **Gilliam's collage logic.** Found pictures become performers and do what they were never drawn to do, through the smallest cut that breaks what the picture implies.
- **The CINEOSIS archive path.** Real shots from the cineosis-lab library enter each card as a surface already in the picture: a mirror, a screen, a floor, a sky, a fire.
- **Secondhand Motion's drawn layer.** Real Quick, Draw! doodles (CC BY 4.0, the records Secondhand Motion chose for its own cartoons) are drawn on top as a second, looser world: the power line's poles, the flying books, the waving hands, the hose, the skateboard.

## The rules of the world

1. **One crank.** Nothing runs unless somebody turns the crank in the school. Power travels the drawn line and reaches each card later the farther it is from the boy.
2. **Every card is a game.** Each district has one goal, one input, and one operator its short did not use.
3. **The cast is recastable.** Each handle-holder is cut into an upper body that performs and legs that stay planted. Recasting scales the new actor to the old one's height and stands them on the same feet.
4. **Same engine, two outputs.** `world.html` is the game. `world.html?film` steps the same world from a fixed script, and `shorts/tools/render.mjs world` renders it as the cartoon.

## The districts

| Card | Operator for the game | Input | Goal |
|---|---|---|---|
| À l'école | Tabletop capture: the crank is performed, not keyed | the dial | twelve books down the wires |
| Un frotteur électrique | Sketchpad constraints | drag a brush | polish two thirds of the floor |
| The barber | Character Animator triggers | left or right on the beat | sixteen clean cuts |
| Phonograph and cinema | JibJab recastable performance | hold to speak, or the microphone; choose who answers | the screen answers as long as you spoke |
| Air cabs over Paris | Rive state machines | up and down | fares from the waving hands to the star |
| Flying firemen | State machines that refuse | aim at the fire | put it out; without pressure the flyers refuse |
| Motor skates | Drawing substitution | alternate strides | a hundred metres; a bad stride swaps in the fallen drawing |

## The recasting test

Adapted from the proof in Watson's notes on a recastable cinema engine: one scene, three actors, six actions. The project page runs the structural parts in the browser and says plainly which parts are not built:

- [x] All three actors keep their own proportions (uniform scale only).
- [x] The legs stay planted while the upper body performs (no time-varying transform on the lower piece).
- [x] Recasting changes the appearance, not the choreography (the performance is a function of the actor's height only).
- [x] The upper body stays attached at the hip (both pieces share one pivot).
- [ ] Front-to-profile turns: not built. Each actor exists in one view only.
- [ ] Grasp and release a shared prop; collide, fall and recover: not built.

## What to borrow next

Not yet used, and the clearest next steps: as-rigid-as-possible and moving-least-squares deformation (Igarashi 2005; Schaefer, McPhail and Warren 2006), so that a cut figure can bend instead of only rotating. Pose2Pose (Willett et al. 2020), to choose between drawings by dynamic programming when a figure turns. Video Puppetry (Barnes et al. 2008), to perform the cut pieces with real paper under a phone camera. A typed actor format, so that the same performance can be compiled to the game, the film and a CINEOSIS passage.

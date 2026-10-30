# SCION 20 · Toon Boom Harmony — Production Rig Foundry · PAE-02 method

**What this is.** The 32 s threshold scene built as a small TV cel production: a drawing library, an exposure sheet,
a node network, palettes, and a renderer that evaluates the network frame by frame. The look is late-century TV cel:
inked characters (heavier silhouette line, lighter inner lines), a hard tone pass and a rim highlight on a painted
gouache background. It is meant to look nothing like 17 (South Park) or 18 (Cartoon Saloon): shaded, lit and inked, not flat.
No Harmony software was used. The *language* is Harmony's, rebuilt in about 1,700 lines of JS/Python. Everything you see and hear was made in code. No photograph, archive frame, Quick, Draw! doodle or web image is used.

## The swarm (honest)
The SCION prompt asks for six roles. One agent played all of them, in sequence: rig supervisor, drawing substitution
artist, node-compositing engineer, scene integrator and pipeline reviewer. No independent critic has watched the film yet.
That verdict belongs to the critic who receives it next. The builder does not approve its own work.

## Native formal language → files
| primitive | where | what it does |
|---|---|---|
| **Drawing library** | `build/01_library.js` → `scene/library.json` | 106 drawings in metres (y up), each a list of shapes with a named colour style, ink line paths and a drawing layer (under/main/over), plus its **anchors** (neck, tail, ear_near, ear_far, mouth). Substitutions align on these anchors. |
| **Palette** | `scene/palette.json` | 27 named colour styles in a **dusk** palette and a **lamp** palette, plus tone and highlight colours for each light. |
| **Exposure sheet** | `build/02_xsheet.py` → `scene/xsheet.json`, `scene/xsheet.tsv` | One row per frame: the drawing exposed in each column (dog_body, dog_head, dog_ear, dog_tail, person, mouth), the peg values, the tail-chain rotations, the door swing, the light and the camera. The `.tsv` is readable like a paper xsheet, with holds marked `|`. |
| **Track breakdown** | `scene/track.json` | Voice syllables (also drive the mouth column), footfalls computed from the walk drawings, tail thumps, door, steps. The sound reads this, so picture and sound share one timing. |
| **Node network** | `build/03_graph.py` → `scene/nodegraph.json` | 26 nodes: ExposureSheet, DrawingLibrary, Palette, Camera, Light, Background, Pegs (door, person, dog, head, tail), Elements (DOOR, PERSON, MOUTH, BODY, HEAD, EAR, TAIL), CurveDeformer (NECK), ChainDeformer (CHAIN_tail), Composite (COMP_dog, COMP_scene), CastShadow, Text, Grade, Write. Dependency and cycle test on build; topological order stored. |
| **Evaluator** | `build/render.html` + `build/harmony.js` (Chromium canvas, driven by `build/render.js`) | Evaluates the graph per frame in topological order. It refuses to start if any input is missing or a node type has no implementation. |
| **Element passes** | `harmony.js: H$.element` | Per element: **Outline** (the matte dilated 1.3 px in ink), then colour and line, then **Tone** (the matte minus the matte shifted toward the key light, multiplied in the tone colour), then **Highlight** (a band 2–6.5 px inside the lit edge, screened). |
| **Light** | `Light` node + `drawLight` | Door spill amount from the door swing. Per element it mixes the dusk and lamp palettes by how much door light reaches the dog's x, and swings the key from the moon (upper right) to the door (low left). This is the lighting shift. |
| **Painted background** | `build/background.js` | Washes and gradients, then 90,000 gouache dabs that sample the wash. No ink. |

**Time base:** 24 fps, scene frames 0–767 = score frames. **Space:** metres along the porch as in the score; base screen
`bx = 315 + 198·x`, `by = 620 − 198·y`; the camera multiplies by `cam_z` about `(cam_cx, cam_cy)`. **Source provenance:** `assets.json` (111 entries, all original).

## How the dog is built
- **Body**: 57 whole drawings. They are stand, crouch, three 16-drawing walk cycles (upright, crouched for backing away, head-low stalk), two lowering/rising breakdowns, lying (sphinx, forelegs forward, near haunch and tucked hind foot), and turn drawings: front, three-quarter front, back (rump to camera) and three-quarter back, the last two crouched.
  Legs are tapered tubes on two-bone IK with the stifle forward and the elbow back. The far legs use darker colour styles.
- **Walks**: each walk drawing is built at a gait phase (lateral sequence, duty 0.62, stride 0.55 m) with the stance feet moving back exactly as the body moves forward. The xsheet picks the drawing from the distance travelled, and the dog peg is nudged by the phase-quantisation remainder.
  So the **planted feet hold**: the regression suite measures a 4.2 mm maximum slide.
- **Heads**: 9 drawings: profile, three-quarter front and front (each with eyes open or shut), three-quarter back, back, and **deep**. Deep shows the back of the skull with the muzzle a level sliver going away; it is drawn for looking in.
  Ears: 18 drawings (6 views × pricked/half/flat), authored in the head's frame and split over the under (far ear) and over (near ear) layers. Tails: 7 rest chains with white tips.
- **Deformation chains** for the in-between flex. The **neck** is a curve deformer: a rest tube is mapped onto a Bézier from the body's neck anchor to the head peg, so the head can lead the body.
  The **tail** is a 6-joint FK chain whose rotations come from the xsheet (wag, sway, thumps on the boards).
- **No cross-dissolve anywhere**: every frame exposes exactly one drawing per column. Turns are 3-frame substitutions (on threes); holds are on twos (head peg eases every second frame); walks are on ones.

## How it moves (the six choices, as drawings)
| t | choice | what is exposed |
|---|---|---|
| 1.0 | backs away | Ears flat, head down, tail tucked, the crouched walk cycle played in reverse as x grows (person: call drawing, mouth on syllables) |
| 2.333 | watches | Head comes up, ears prick, upright walk set as it eases to a stop |
| 3.417 | turns its back | q3back → back (rump to camera, head beyond) → q3back mirrored → crouch facing away. The back is fully shown by 3.79 s; it lies down facing away by 4.8 s and puts its chin on its paws (person: reach) |
| 7.458 | turns back to look | **The head leads**: the head drawing goes q3front → front → q3front → profile toward the door (muzzle to the door by 7.63 s) while the body still lies. The body then rises facing away and turns through q3front → front → q3front to stand facing the door by 8.5 s |
| 14.708 | comes, head low | Stalking walk (lwalk): neck angled down, head peg below the line of the back the whole way, ears half, tail low with a slight wag |
| 23.792 | lies down across the sill | lower1 → lower2 → lie. The forequarters and head are inside the door frame and the haunch and tail are outside (61 % of the dog's matte inside the frame at the end, measured) |
| 26.4 | looks in, settles, stays | Ears prick at "come in"; the head comes up level and swaps to **deep**: back of the head to us, muzzle inside the room toward a lit hall in the back wall. 100 % of the head matte is inside the room. The tail thumps. At 28.2 s it settles, chin on paws, eyes shut |

The person: 10 drawings (stand, call, reach ×2, step ×2, sitting down, sit, offering a hand low ×2) and 4 mouths lip-synced to the syllables.
The door is a flat panel on a swing peg: ajar at 22°, it swings open 6.2–7.05 s all the way back against the inside of the front wall, where this section view sees it edge-on. The light comes out onto the porch and the dog's palette turns warm.

## Measured (from the render, `trace.json`)
The trace is read back from the canvas every frame: the dog's composite matte and the head element's matte, with the camera undone (`x_world_measured`). Onset rules are written in `build/06_trace.py`.

| choice | score | measured | dt |
|---|---|---|---|
| retreat | 1.000 | 1.167 | +0.167 (the head drop first moves the centroid toward the door) |
| watch | 2.333 | 2.333 | 0 |
| refuse | 3.417 | 3.417 | 0 |
| watch (head leads) | 7.458 | 7.458 | 0 |
| approach | 14.708 | 14.708 | 0 |
| lie_down | 23.792 | 23.792 | 0 |
| looks in (not a checked choice) | 26.4 | 26.625 | +0.225 |

`check_handmade.py`: **ALL OK** (I1–I4). Regression suite `build/09_regress.py` → `build/regress.json`: graph has no broken dependencies; every exposure is a library drawing; no blend or opacity fields; anchors present; ear views match head views; planted feet ≤ 4.2 mm; onsets ±0.25 s; dog never inside (x ≥ 0.56); ends 61 % in the door frame; film 912 frames, 1280×720, 3.5 MB.
**Sound, measured in the final mix:** calls −10.7 dB RMS, soft voice −25.1 dB (**14.4 dB under the calls**), room tone −42.2 dB (soft voice 17.1 dB above it).

## Sound
Everything is synthesized in `build/05_sound.py`. Voice: a sawtooth glottal source through three formant resonators per vowel, with noise for k/h/s and breath. The calls are pushed; the soft lines are breathy and quieter.
Dusk: crickets and wind; a room hum enters once the door is open. Wood: pads (with a claw click) at every footfall the walk drawings make, the person's steps, the stool's creak, the door's latch and creak, and the tail thumping the boards.
The dog: a small whine as it turns back to look, sniffs on the approach, a sigh when it settles. Music: a warm pad enters with the light, plucked notes as it comes, chords at the sill. The words are synthesized murmurs, so they are subtitled (the person's words, never the dog's state).

## What failed and what changed
See `ledger.jsonl`. In short:
- Thin "greyhound" legs → thicker legs.
- A grey dusk palette → a lighter dusk palette.
- A meerkat neck on the look-back → a lower, over-the-shoulder head joint.
- A spider-legged breakdown → rebuilt.
- The first look-in lifted the head toward the person (the named failure) → a new back-of-head drawing, level, with a camera push.
- The open door panel blocked the room the dog looks into → the door now swings flat against the wall and a lit hall gives depth.
- Two onsets mis-measured on the first full render → the 2.333 beat made explicit in drawings, and the lie-down measured by the body's centroid dropping.
- A tail that read as a fifth leg in the breakdowns → the lying tail.

## What is still weak (builder's view, unconfirmed by a critic)
- In the wide shot (0–23 s) the dog is small: about 50 px of head. The head-lead turn reads in the extracted frames, but it is small on a phone.
- The lowering/rising breakdowns (lower1/lower2, 6 frames each) are rough drawings.
- The person's step aside alternates two step drawings, so the feet are not planted.
- The voice is a formant murmur; the words live in the subtitles.
- The cutaway shows the lit room from the start. "Light comes out" is carried by the door swinging wide, the spill on the porch and the dog's palette going warm, not by a dark room lighting up. The door's swing reads as widening then narrowing to edge-on, which some viewers may find odd.
- The tone pass is a matte-shift approximation (one crescent per element), not hand-painted tone shapes.
- Whether the look-in reads *in depth* is a perceptual question. The structure is there: back of the head to us, muzzle 100 % inside the room, aimed at the lit hall. It has not been judged by anyone but the builder.

## What was not done
- No real Toon Boom Harmony and no `.xstage` scene package. The scene package is the `scene/` folder plus `build/`.
- No kit material was used: not the archive dog, archive door, Quick, Draw! or found frames.
- No independent critic run, and no forked branches.
- No camera moves before 23 s.
- No hand-drawn tone shapes and no line-weight pressure.
- `build/make.sh` rebuilds everything (about 6 min: render about 4.7 min). Rendered frames are deleted after encoding.

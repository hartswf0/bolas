# SCION 27 · Remotion — the threshold as a declarative film

**Thesis.** The film is a function: `frame = f(score, cast, time, seed 27)`. Nothing in it is keyed by hand on a timeline and
nothing is drawn by hand on a canvas: a compiler pass turns the PAELEO score into a typed scene manifest (one record per
frame), and frame-pure React components turn each record into SVG. Remotion renders the 912 frames. The viewer's central
experience is that the dog decides: commands push it away; the changed circumstances (the person sitting, the door
swinging open, the light coming out onto the boards, the low hand, the soft voice) earn it. The defining passage is
7.46 s, when the head comes round over the shoulder toward the light before the body follows. Bland would be a dog that
slides along the porch like a cursor, or labels on screen doing the acting.

## The swarm (merged roles, one builder)

All roles were run by one agent; the coupling (camera ↔ wall clipping ↔ measurement) was tighter than any hand-off.

| Role | Artifact it owns |
|---|---|
| Scene DSL architect | `build/solve.ts`: score → `build/cache/manifest.json` (schema `scion27.manifest/1`, a contract check that fails on any non-finite channel) |
| Composition developer | `build/src/` (React/TSX): `index.tsx` (Film, Scene, DogMatte compositions), `comp/World.tsx`, `comp/Actors.tsx`, `lib/dogRig.ts`, `lib/personRig.ts` |
| Render engineer | `build/rlib.mjs`, `build/render.mjs`: one bundle, one browser contract; any browser console error fails the render |
| Audio timing integrator | `build/sound.py`: the manifest's sound events → `mix.wav`, `audio.json` |
| Reproducibility tester | `build/measure.py` (the dog measured from its own matte render → `trace.json`), `build/repro.mjs` (frames rendered twice, hashes compared → `repro.json`) |
| Independent editor / critic | **not this agent.** The verdict belongs to the independent critic. |

## Native formal language, as built

- **Typed scene manifest.** Per frame: the dog's plan position `X` (= score x, metres), heading, head yaw, `lie, crouch,
  head, ear, tail, wag, rest, look` (from the score's act channels, with my acting layer on heading/head yaw), four paw
  positions from the gait solver, the person's pose parameters, the door angle and lamp level, the camera (pos, target,
  focal), the spoken line. Types: `DogPose`, `PersonPose` in `lib/*.ts`.
- **Component graph.** `<Film>` = `<Sequence>` title (72) + `<Scene>` (768) + end card (72) + `<Audio>`. `<Scene>` =
  Sky, Yard, Room (clipped to the opening), Facade, Frame, Porch (with the light spill), Railing, `<Person>`, `<Dog>`.
  `<Dog>` reads one manifest frame and nothing else: no state, no effects, no clock.
- **Frame/time mapping.** Scene frame *i* = score frame *i* = film frame 72 + *i*, 24 fps. The camera is a pure function
  of scene time (`camAt(t)`), stored per frame in the manifest so measurement can invert it.
- **Composition functions.** `ramp`, `keyed`, `interpolate` (Remotion) for every channel; `random(seed)` (Remotion) for
  stars, trees and board ends; a seeded hash for ear twitches.
- **Deterministic seed.** 27. No `Math.random`, no wall clock anywhere in the pipeline.
- **Audio tracks.** One mix synthesised from the event list; muxed by Remotion's `<Audio>`, re-encoded AAC.

**Numerical invariant tested:** the PAELEO checker (I1–I4) on a trace measured from the render, plus frame-hash equality
across two independent renders. **Artistic achievement judged only by viewing:** whether the turned back, the look over
the shoulder at 7.46 s and the look into the room read as a dog's decisions.

## How the dog is made and how it moves

- **Made of:** 34 tapered capsules (two discs and their tangents, i.e. round-capped strokes) and two ear triangles, placed
  on a 3-D joint graph and projected by one pin-hole camera, depth-sorted, one dark outline pass under flat fills. Saddle,
  tan legs, cheeks and pips, dark upper muzzle: a shepherd's markings, because the archive dog is a shepherd type.
  Proportions are measured, not guessed: medians of 10 side-on rig keys of the archive dog
  (`kit/archive-dog/pose_agent_v8.json`), normalised by chest→tail length (neck 0.881 L, chest 0.475 L, tail root
  0.76 L, nose→neck 0.706 L, neck→chest 0.425 L), L = 0.72 m. No pixel of the archive footage is shown.
- **Why capsules (the turn lesson):** a capsule seen end-on is a disc, so the dog has a body from every angle. Both turns
  pass through a **front view of its face**, not an edge-on card. The refusal turns 175° through the camera side
  (heading 180° → 5°, 3.43–3.88 s), head leading by up to 50°; the turn back (7.56–8.40 s) lets the head come round
  first (up to 140° over the shoulder, 7.40–7.60 s) while the dog is still rising from the boards.
- **Legs:** two-bone IK per leg (elbow back on the forelegs, stifle forward on the hind legs, a pastern/metatarsus
  segment). **Feet:** a stepping solver in `solve.ts` keeps every paw planted in world space until the body has carried
  its rest target more than 7.5 cm away (or it has been untidy for 14 frames); a step then swings it, with lift, to the
  target the body will want a few frames later, at most two paws in the air and never two on one side. The same solver
  makes the walk, the backing-away, the pivot on the spot and the settling. Lying down and getting up blend the paws
  between their planted places and a sphinx pose (forearms flat, hocks on the boards) with a small lift. Every paw plant
  is also a sound event.
- **Acting layer over the score:** the score's `turn` channel finishes the refusal only at ~5 s; I retimed the visible turn
  to 3.43–3.88 s so the back is shown by 3.9 s and held until 7.46. While coming, the head is lowered from 14.4 s (before
  the first step) and stays below the back; on the way past the person's low hand the head goes to it (a sniff, 20.9–22.4
  s). At 26.4 s (*come in*) the head lifts, the neck extends, and the muzzle goes into the lit room, yawed 18° away from
  the camera so the back of the head faces us; at 28.3 it settles chin on paws and stays.
- **The place.** A façade with a doorway (wall X 0.34–0.50 m), a threshold stone, a furnished lit room (only visible
  through the opening: everything inside is clipped to it), a porch whose boards end at the steps at 4.9 m. The door hangs
  on the near jamb; ajar (55°) it lets out a thin wedge of light; at 6.2 s it swings to 106° on a draught (wind gust and
  creak in the sound) and the wedge widens down the porch to the dog. The wedge is geometry: lamp → unblocked opening →
  floor; the dog and person cast lamp shadows only inside it. Dusk deepens over 32 s; stars come out.
- **Camera.** Wide and still until 15.4 s; a slow push-in (zoom 1500 → 2550 px and a small dolly along the same line)
  15.4–23.6 s; held. Because it moves, `trace.json` carries `x_world_measured`.

## What was measured (from `trace.json`, `invariants.json`, `audio.json`, `repro.json`)

`measure.py` reads the **DogMatte** composition: the same `<Dog>` component, same camera and wall clipping, flat matte
colours (body green, neck magenta, skull blue, muzzle red). The state per frame is read from those pixels, not copied from
the score (rules are written into `trace.json`).

| choice | score | measured onset | dt |
|---|---|---|---|
| watch → retreat | 1.000 | 1.000 | 0.000 |
| retreat → watch | 2.333 | 2.417 | +0.084 |
| watch → refuse | 3.417 | 3.583 | +0.166 |
| refuse → watch (turns to look) | 7.458 | 7.458 | 0.000 |
| watch → approach | 14.708 | 14.667 | −0.041 |
| approach → lie_down | 23.792 | 23.833 | +0.041 |
| hears *come in* → looks in | 26.4 | 26.500 | +0.100 |

- I1–I4 `ALL OK` (check_handmade.py). I3 r = 0.999 on `x_world_measured` (body centroid back-projected through the
  frame's camera onto the dog's line). I4: muzzle points away from the door in the refusal frames.
- Head below the line of the back (screen pixels, head incl. ears vs the top of the body): 100 % of the score's approach
  frames (14.71–23.79 s).
- Voice: calls −17.9 / −17.0 dBFS RMS, soft lines −27.8 / −28.3 / −28.9 dBFS → soft is 9.9 dB quieter than the calls
  and 25 dB above the room tone (−53.7 dBFS, scene 12.5–14.5 s), measured on the synthesised mix before AAC.
- Determinism (`repro.json`): 10 scene frames (0, 30, 86, 100, 180, 216, 456, 576, 650, 767) rendered as PNG in two
  fresh bundles and browser sessions, SHA-256 equal 10/10, and equal to the previous run of the same manifest. With the
  default GL backend (`swangle`) 2 of 10 frames differed by one level on scattered pixels below y = 509; removing every
  blur filter did not fix it; switching the backend to `swiftshader` did (4 runs, all equal). The film, matte and stills
  are all rendered under that contract. One machine only: cross-machine equality is **unknown**.
- Film: 912 frames, 1280×720, 24 fps, 38.016 s, H.264 + AAC, faststart, 3.97 MB.

## What failed and what I changed (full list in `ledger.jsonl`)

1. Refusal turned away from the camera → a rear-view blob with the low head hidden. Turned it through the camera side.
2. Muzzle read as an anteater's tube → rebuilt the head (crown, cheeks, dark upper muzzle, pips, bigger ears).
3. Door hinged on the far jamb hid the room when open → rehung on the near jamb; ajar angle raised so light leaks.
4. The head inside the door frame was hidden by the near jamb → moved the dog's line to Z = −0.30 m.
5. Dog too small at the sill in a still wide shot → push-in. A dolly to a nearer camera folded geometry behind the lens
   (added near-plane clipping) and then showed the dog from behind with its head behind the wall; rejected for a zoom along
   the wide camera's own line.
6. Measurement: lie onset read late (neck and head counted as body), lying-while-facing-the-door labelled lie_down,
   screen perspective put a far head "above" the back. Fixed by a separate neck matte, metres-at-depth heights, the sill
   condition for lie_down, and a lower head (and ears) in the approach.
7. A comment swallowed two manifest fields (ear, tail) → a full film rendered with NaN paths and no tail. Added the
   manifest contract check in `solve.ts` and a render guard that fails on any browser error; re-rendered.
8. The doorway hole and its clip path were projected once at module load (t = 0 camera); during the push-in a phantom
   wall cut off the dog's head. Projections are now per frame.
9. Frame hashes differed between runs under `swangle`; fixed by the `swiftshader` contract (see above). It also cut the
   film render from ~17–27 min to under a minute on this loaded machine.

## What is still weak (my view; the critic decides)

- The lying dog, seen from behind-left, is a brown mass with the legs mostly hidden; it reads as lying but not elegantly.
- The rising-and-turning frames (~7.6–8.0 s) are a busy knot of body and head; every frame has a face or a back, but
  it is the least clean passage.
- The person is a faceless mannequin with a nose; adequate as a circumstance, not as a character.
- The voice is a 3-formant synthesiser; captions carry the words. **I cannot listen**: intelligibility, timbre and
  whether the mix is pleasant are unknown. Only levels, timing and a spectrogram were inspected.

## What I did not do

- No landscape/portrait or second casting (the SCION hard proof was replaced by the brief's scene).
- No cross-machine frame comparison (one machine only).
- No operator approval of the Remotion License tier (flagged in `assets.json`).
- No archive footage, Quick, Draw! drawings or found frames are used; the archive dog contributes measured proportions only.
- No independent critique: that is not mine to give.

## Rebuild

`bash paeleo/handmade/27-remotion/build/make.sh` (installs Remotion into `build/cache/deps` on first run). The film
renders in about a minute with `gl: swiftshader`.

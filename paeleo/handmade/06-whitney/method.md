# SCION 06 · John Whitney — Harmonic Motion Orchestra · the threshold, handmade

## Thesis

The dog is a body of light made of oscillators. The film's harmonic structure is the dog's relation to the house: the
dog breathes at a rate that wants to be 3, the house (the light in the door, the porch floor, the stars) pulses at 2.
The calls throw that relation out of tune: the dog pants, the 3:2 slides, the fifth beats, the moon (a Lissajous trail of
the two oscillators) smears and turns. The changed circumstances (the person sitting, the door opening, the low hand,
the soft voice) put coupling into the bank. The 3:2 locks while the dog is still watching (about 11 s), it comes in
locked, and when it lies across the sill the twisted lines of its body unwind into straight engraved lines (the
reunion, 24 s). Then come in, a look into the light, and release: the field thins and the bed falls away.

What would make it bland: procedural shimmer that means nothing, a dog that reads as a wireframe toy, a tangle on the
turns, a light that floods the dog out. I watched for all of these (see "what failed").

## Swarm (merged; one builder, no self-approval)

The prompt's smallest swarm was merged into one builder because the parts are tightly coupled. Each role is a file:

| role | artifact |
|---|---|
| motion mathematician | `build/harmonic.py`: oscillator bank, coupling, envelopes, the 3:2 relation psi |
| choreographic composer | `build/harmonic.py: choreography(), person(), door()`: score to pose state |
| visual counterpoint arranger | `build/figures.py` (bodies as tubes of helical lines), `build/render.py` (the field) |
| audio synchronizer | `build/audio.py`: tones, voice, footfalls from the trace |
| renderer | `build/render.py` (numpy splat + persistence; no GPU) |
| independent rhythm critic | **not me.** An independent critic judges the film. I have not approved it. |

## Native formal language, kept as named objects

- **Periodic functions / parametric trajectories.** Every mark is a point on a curve. A body is a set of tubes; a tube
  carries 6-11 meridian lines of dots along a centre line; their phase is
  `phi(s,t) = 0.35 h W0 (t-24) + h * 1.6 sin(W0 (t-24)/2) * s`, with W0 = 2 pi / 8 s and h a harmonic number per tube
  (torso 1, neck 2, head 3, legs 4-5, tail 6). The lines wind into helices and unwind straight at 0, 8, 16 and 24 s.
- **Oscillator bank.** `theta_house` at 0.40 Hz; `theta_dog` at a natural rate of 0.6 Hz x (1 + 0.55 pressure +
  0.12 (1 - invitation) + 0.03 detune), coupled by `K(t)` (zero until 7.4 s, then rising) through
  `-K sin(2 theta_dog - 3 theta_house)`. Stars pulse at integer multiples of the house phase; the porch light carries a
  travelling wave at the house phase; the dog's girth and the ripple on its rings follow `theta_dog`; its wag is at
  2 x theta_dog.
- **Phase relationships.** psi = 2 theta_dog - 3 theta_house. Gait: a lateral-sequence walk as phase offsets of one stride
  (LH 0, LF 1/4, RH 1/2, RF 3/4), stance 62 %, stride 0.56 m, driven by the signed distance the body travels forward, so a
  planted foot stays where it is in the world (backing away runs the cycle backwards).
- **Event envelopes.** Pressure (the calls and the reach), invitation (sit, door, low hand, soft voice), call wavefronts
  that strike the dog (agitation impulses at the arrival time of each wavefront: the body bristles and reddens), the door
  swing, the reunion bloom in the sound.
- **Compositional field.** Porch planks, facade lattice, door frame and sill, door leaf, interior, door light (a haze
  built from points and blurred), stars, the moon as the phase visualizer, density (sparse 0.38 -> dense 1.0 -> release
  0.25) and persistence (accumulation grows with density).
- **Coordinates and time.** World metres: u = x_score - 0.45 along the porch (facade outer face u = 0, inner face
  u = -0.30), y up, z toward the camera. Time base t = i / 24 on the score's frames. The camera is fixed (wide) until
  14.9 s, dollies with the approach, and is fixed (close on the sill) from 23.7 s.

## How the dog is built

A skeleton in metres, proportioned from the archive dog's rig keys (kit `pose_agent_v8.json`, frame 0: chest to tail
base 90 px taken as 0.80 m of torso; the other keys scaled by the same factor): spine (rump to withers to chest), neck,
skull and muzzle, four legs of three segments (fore: shoulder, elbow, wrist, paw; hind: hip, stifle, hock, paw, with
two-bone IK to the paw targets), a seven-segment tail, two ear triangles, two eye points and a nose point. Every part is
a tube of meridian dot-lines with a radius profile (deep chest, tuck-up waist). The dog is a genuine 3D object: its
turns are rotations about the vertical axis, seen through a perspective camera, and the dots are shaded like a light
pen: rims (the silhouette) bright, the near face medium, the far face dim. In front of the door light the dog's own
dots cast a soft occlusion, so its body stands dark against the light with its dots bright on it.

## How it moves (and where the score drives it)

- position: the score's x, mapped u = x - 0.45 (the same metres at the same pace; retreat away, approach toward).
- body yaw: one full revolution over the film. Refusal 3.43-3.90 s through facing away from the camera (its back to the
  door by 3.8 s); turning back 7.72-8.55 s through facing the camera.
- head yaw leads the body (attention before gesture): at 3.40 s it starts away; at 7.46-7.70 s the head comes round over
  the shoulder to the door while the body still lies turned away; the body rises (7.70-8.10) and turns after it.
- head pitch from the score's `head` through my mapping; during the whole approach the pitch is capped at -30 degrees,
  so the head is below the line of the back (measured as `head_below_back_m` in the trace).
- lie, rest (chin on the paws), crouch, ears, tail, wag from the score's `act` curves. Lying is its own pose, not a
  squashed stand: elbows on the floor, forearms flat ahead, hind legs folded to the side, tail on the porch floor.
- on the sill: 24.4-25.2 s the head turns toward the person's low hand; at 26.45 s (come in, softly) it turns back
  into the lit doorway and lifts (the score's `look`); from 28.2 s it settles, chin down, facing in, and stays.

## Protected invariants and what was measured

`python3 tools/paeleo/check_handmade.py paeleo/handmade/06-whitney` -> see `invariants.json` and the report.

- I1: `trace.json` `state` is the score's state at that frame (the render is driven by the score, so this check is
  structural). Because of that I also classify each frame from the drawn geometry alone (`state_seen`, rules in
  `render.py: seen_states`) and report its timing in `proof/seen_states.json`.
- I2/I3: `x_world_measured` is the drawn torso centre's screen point back-projected through that frame's camera onto the
  walking plane; I3 uses it (the camera moves).
- I4: `facing` from the drawn chest and rump screen positions.
- The 3:2 lock (`proof/phase.json`, `proof/phase.png`): |d psi/dt| max < 0.05 rad/s from 14.7 s to the end; mean > 3 rad/s
  under the commands. A/B: the same bank with K = 0 drifts at 0.23 rad/s through the approach (the detuned branch).
- Sound (`proof/audio.json`): voice stem RMS over its active samples; soft voice vs calls and room tone.

## What failed and what I changed

See `ledger.jsonl` (one line per attempt). In short: rings read as a coil spring -> meridian lines; trails smeared the walk
-> two persistence buffers; the field drowned the dog -> dimmer lattice; the bottom half of the frame was empty -> lower
camera; the end was tiny and lost in the door frame -> a dolly to a close sill shot; the door did not read as lit -> a
haze field; the light flooded the lying dog -> occlusion mask from the dog's own dots; the look-back made a giraffe neck
-> smaller head lift; the high curled tail read fox-like on the approach -> lower tail mapping.

## What I did not do

- No independent critic was run by me, and I did not approve the film.
- No blind rhythm comparison (it needs viewers who are not me). No mobile operator page.
- The A/B of lock vs drift is numerical (`proof/phase.*`); I did not render a drift version of the film.
- I cannot listen. The sound was measured (levels, timing of events by construction), not heard. Whether the formant
  voice is intelligible as words is unknown; subtitles carry the words.
- Ears, eyes and paws are small at the wide camera; whether they read at normal speed was judged only from stills.
- Quick, Draw!, the archive frames' pixels, the masks and the found-frames library were not used.

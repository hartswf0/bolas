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

## Measured results (build 6, the delivered film)

- checker: ALL OK. I1 every choice dt = 0.000 s (structural: `state` is the score's label); I2 min x 0.59, end 0.59;
  I3 r = 1.000 on x_world_measured; I4 share of refusal frames turned = 0.928.
- seen from the drawn geometry only (`proof/seen_states.json`): retreat +0.208 s; watch +0.042 s; refuse +0.166 s; watch +0.167 s; approach -0.041 s; lie_down +0.208 s.
- head below the line of the back during the approach: min 0.078 m, max 0.078 m over 218 frames (positive = below).
- 3:2 lock: |d psi/dt| max 0.0000 rad/s from 14.7 s to the end; mean 3.37 rad/s under the commands; the K = 0 branch
  drifts at 0.226 rad/s through the approach.
- sound: calls -17.1 / -17.1 dBFS, soft voice -30.0 / -30.3 / -29.2 dBFS (soft 12.1 dB below the calls), room tone -57.5 dBFS;
  34 footfall ticks placed on the frames where a drawn foot plants.
- film.mp4: 1280x720, 24 fps, H.264 + AAC, 38.0 s, 912 video frames, 2.6 MB, faststart.

Looked at (Read on images): test frames, contact sheets of the retreat, both turns (every frame region 3.45-3.80 and
7.90-8.30 s), the approach, the sill sequence, film frames at scene 9 s and 28 s after compression, a 1 fps and a 0.5 s
sheet of the whole film, the four stills. Not looked at: every frame at normal speed (I cannot play video).

## What failed and what I changed

See `ledger.jsonl` (one line per attempt). In short: rings read as a coil spring -> meridian lines; trails smeared the walk
-> two persistence buffers; the field drowned the dog -> dimmer lattice; the bottom half of the frame was empty -> lower
camera; the end was tiny and lost in the door frame -> a dolly to a close sill shot; the door did not read as lit -> a
haze field; the light flooded the lying dog -> occlusion mask from the dog's own dots; the look-back made a giraffe neck
-> smaller head lift; the high curled tail read fox-like on the approach -> lower tail mapping; in the turns the
rump-on and chest-on frames collapsed into a ball of bright end-on rings -> the spine curls into a C toward the turn
(head leads, rear follows) and rim brightness fades for tubes seen end-on; lying on the sill reached the lying pose
late -> it goes down 23.79-24.12 s. Two early builds were killed mid-render (another swarm's `pkill -f render.py` on the
shared machine); every later build was checked by frame count.

## Still weak

- The middle frames of both turns (about 3.60-3.72 s and 8.05-8.20 s) are the weakest drawings: a curled body seen
  3/4 from behind / chest-on, dimmer than the profile. They read as a body with legs; whether they read as a dog at
  normal speed is for the critic.
- In the wide shot (0-15 s) the dog is about 300 px long and the ears, eyes and paws are small.
- The person is a coarse figure (a lantern head, a block torso).
- The still at 3.6 s catches the dog mid-turn (its back fully to the door from about 3.8 s).

## What I did not do

- No independent critic was run by me, and I did not approve the film.
- No blind rhythm comparison (it needs viewers who are not me). No mobile operator page.
- The A/B of lock vs drift is numerical (`proof/phase.*`); I did not render a drift version of the film.
- I cannot listen. The sound was measured (levels, timing of events by construction), not heard. Whether the formant
  voice is intelligible as words is unknown; subtitles carry the words.
- Ears, eyes and paws are small at the wide camera; whether they read at normal speed was judged only from stills.
- Quick, Draw!, the archive frames' pixels, the masks and the found-frames library were not used.

## Round 2 (after critic round 1: DOES NOT PASS, close)

The critic's ranked repairs and what I changed (the critic's report is in `reviews/round1.md`, not edited):

1. **Look-in 26.6-28.0 pointed up.** The look now keeps the head near level (pitch blended to +4 degrees) and turns the
   muzzle 58 degrees away from the camera, into the depth of the room, toward a hearth at the back of the room
   (u -2.45, z -3.6), which is seen through the open door from the close camera. Before it (24.4-26.4) the head turns
   the other way, toward the person's low hand, so the look-in is a visible head turn from the person to the room.
2. **Inside and outside were not legible.** The room is now a distinct interior in point-lines: warm floorboards running
   into the room and a back wall of horizontal lines (drawn as a cutaway; the back wall is shown only where it is seen
   through the door, elsewhere it is faint), lit by the hearth and by the door. The porch stays cool dots. The close
   camera is higher (1.45 m) so both floors read as planes. My mapping became u = x - 0.52, so on the sill the head and
   forelegs lie beyond the inner face of the frame, the hindquarters on the porch boards, the tail outside. The person
   sits inside, beside the frame on the near side, hand low near the dog's head. The door's light slab was removed (the
   room itself is the light; only a low glow at the sill).
3. **The 3:2 was only in the moon.** The phase relation psi now drives the main field:
   - the dog's meridian lines: rotation 0.25 h psi and twist 1.5 sin(psi) per tube. While psi drifts (the calls, the
     refusal) the lines stream round the body and wind and unwind; as the bank locks (about 7.5-12 s) they slow and
     stand straight and still. (This replaces the 8 s clock twist of round 1.)
   - the porch planks: every plank dot is displaced along the porch by 0.045 sin(5 z + 2 u - psi): rippling under the
     calls, still once locked.
   - the light's wave on the porch runs at 3/2 of the house phase and is aimed at the dog, so when locked its crest
     reaches the dog exactly as the dog's breath peaks (the dog's brightness pulses at theta_dog); its reach grows with
     the lock (1.2 m -> 4.2 m), so through 9-14 s the light visibly travels out to the watching dog.
   The moon stays as an addition.
4. **7.9-8.4 upright torso / flung leg.** The body now rises in place first (7.66-8.02) and turns standing (8.00-8.70),
   with no spine curl on this turn (seen from above, the curl read as a sloped, rearing body); the head stays near the
   line of the back while it looks over its shoulder; the tail is shorter and a tucked tail curls under.
5. **Soft voice vs bed.** The oscillator bed ducks by 14 dB from 0.6 s before each soft line to its end; measured: the
   1-3 kHz band of each soft line against the mix in the 0.5 s before it (`proof/audio.json`).

Kept: the 3D refusal turn with its curl, the head-low approach, the voice wavefronts, the sound arc, the moon.

Round 2 measured: checker ALL OK (same trace measures as round 1, rewritten from the round 2 render); seen choices
retreat +0.21, watch +0.04, refuse +0.17, watch +0.17, approach -0.04, lie_down +0.21 s; scene 768 / film 912 frames,
38.0 s, 2.6 MB. Soft lines' 1-3 kHz band above the mix in the 0.5 s before: 28.2, 21.1, 51.5 dB. Looked at: every frame
7.79-8.50 s and 24.0-28.4 s (small tiles; `proof/r2_rise_every_frame.png`, key frames `proof/r2_sill_keys.png`) and
drift-to-lock crops (`proof/r2_drift_to_lock.png`). Still weak after round 2: the interior floor's far part extends to
the right of the door frame (it is behind the facade but the facade lattice is faint); the person is faint; in the
look-in we see the back of the dog's head, so "looking in" depends on the hearth being visible in the doorway.

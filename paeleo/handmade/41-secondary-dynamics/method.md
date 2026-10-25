# SCION 41 · Secondary Dynamics — the threshold, handmade

**Thesis.** The dog's choices are primary motion: they come from the PAELEO score and the swarm's own timing of turns, head
and feet. Everything that hangs off the dog and the people (ears, tail, coat, collar tag, scarf, the door, the shrub) is
secondary. It is solved, never keyframed, so that it shows what the bodies are made of and how hard they moved, and then
it stops. The theorem in my prompt is to let secondary objects reveal material and momentum without causing continuous
purposeless wiggle. In this film nothing moves unless something moved it, and every part comes to rest in the holds. The
film would be bland if the secondaries were ornaments: a tail that sways while the dog stands still, a scarf that floats.
It would be false if they were decoration that passed through bodies.

**Defining passage.** 3.4–8.7 s. The second call and the reach make the dog spin away (its tag ticks and its tail swings
out and wraps), lie down with its back turned, and brush the shrub. The door is pulled and swings to its stop on its own
momentum (it knocks at 6.20 s), and the light comes out over the dog's back. At the soft voice the head comes round first,
the ears flick up, and the body follows the head.

## The swarm (one agent, roles merged)

The SCION roles were all held by this one agent, because the coupling (pose → collider → chain → sound event) made
handing work across agents cost more than it saved: material dynamics modeler (`build/dynamics.js`), pose coupling
engineer and contact specialist (`build/scene.js`), animation tuner (presets, timing), and integration QA
(`build/test_dynamics.js`, `build/test_scene.py`, `tools/paeleo/check_handmade.py`). The **independent expressive
critic was not me** and has not run yet. Nothing here is a critic's verdict.

## Native formal language (first-class, typed)

Units are metres, seconds and kilograms. World axes: X runs along the porch and is the score's x directly (threshold 0,
outside positive, sill board at 0.26–0.66, wall faces at 0.30 and 0.50, steps at 4.9); Y is up; Z runs across the porch,
toward the camera. The time base is 24 fps, and every solver is sub-stepped 8 times inside a frame. The camera is a
pinhole whose framing is itself a critically damped spring: it follows what must be visible and never overshoots.

| primitive | type (in → out) | where |
|---|---|---|
| spring-damper, continuous integrator | `exactStep(x, v, target, f Hz, ζ, dt, a)` → `[x, v]`: the closed-form step of a damped oscillator, unconditionally stable | dynamics.js |
| discrete integrator | `eulerStep(...)`: semi-implicit Euler (a test shows it blows up at 1/24 s on a 9 Hz spring, which is why chains sub-step) | dynamics.js |
| mass proxy | `MassProxy(material, gain).step(anchor world pos, dt)` → 3D offset (m): coat tufts lag behind their anchor's acceleration | dynamics.js |
| spring chain | `Chain(material, n).step(pose targets[n], boundaries, dt, sub, t0)`: pose springs, damping relative to the moving pose, air drag, inextensible segments, contacts → `p[n]`, contact-onset `events` | dynamics.js |
| collision boundary | `{type: plane\|sphere\|capsule, …, v}`: optional velocity, interpolated per substep; contacts are inelastic in the boundary's frame | dynamics.js |
| hinge | `Hinge({I, k, c, friction, min, max, restitution}).impulse(J).step(dt)` → angle, stop events | dynamics.js |
| primary pose impulse | the score's acting values, plus this swarm's timings (`bodyYaw`, `headHeading`, `headRoll`), the foot stepper, and the person's keyframed gestures; the door gets one impulse from her hand at 5.0 s | scene.js |
| material prior | `MATERIALS`: f (Hz), ζ, mass, drag for hair, ear, fur, cloth, paper, wood, foliage and metal, plus `none` (no secondary motion) | dynamics.js |

**Numeric invariants (measured, `proof/assertions.json`).**

- A1: in the holds, every secondary part's energy is below 1e-3 of its peak (worst: tag 4.7e-4).
- A2: the tail tip responds 1, 2 and 14 frames after the retreat, the refusal turn and the approach begin.
- A3: no interpenetration. The minimum signed gaps, collision radii included, are: tail 0, scarf 0, belly 1.9 cm,
  jambs 31 cm.
- A4: planted feet move at most 2.1 mm between frames.
- A5: the head is below the back in 218/218 approach frames.
- A6: all seven choices are measured from the render, with onsets +0.08 to +0.14 s after the score.
- A7: the soft voice is 13.3 dB under the calls and 23.9 dB over the room tone.

**Artistic achievement judged only by viewing.** Each secondary part should read as a material (hair, leather, wool,
wood, leaves) and as the consequence of a choice the dog or the person just made. That is for the critic.

## How the dog is built and moved

The dog is made of spheres and capsules: six torso spheres, a neck and a head, a muzzle with eyes and a nose, four legs
(two-bone IK), two ear flaps, a seven-node tail, and a collar with a tag. It is drawn as one silhouette per part, with an
outline, volume gradients, a blurred dark saddle and coat strokes. Its proportions and coat were studied by eye from the
kit's archive dog, a shepherd type; nothing of the archive is drawn. Its position is the score's x. I rendered it,
measured the drawn layer's centroid, unprojected that centroid back to the walking plane and compared it with the score:
the correlation is r = 1.00.

- **Turns are real 3D rotations of the rig, never mirroring.** The refusal turns *away* from the viewer, so the rump and
  back come round to us and the back is fully turned by 3.9 s. The turn back at 7.458 goes the other way, through the
  camera side. The head comes round first and points at the door within 0.18 s; the dog rises while looking back over its
  shoulder, and the body follows at 7.86–8.62 s.
- **The feet are planted by a stepper.** A foot lifts only when its ideal position under the moving body is too far
  away, and only while the other foot of its girdle is planted. It lands where the body will be (the whole score is known,
  so the stepper can look ahead). Paw touchdowns are sound events.
- **Lying across the sill is a sphinx pose**, made of explicit joints blended with the IK. The forelegs lie flat inside
  the door frame and the hind legs are folded at the sides. The belly is on the boards (gap ≥ 0). The chest lies on the
  sill, the head and forelegs are inside the frame, and the tail lies out on the porch, colliding with the floor; at
  "come in" its wag sweeps the boards.
- **The head leads the body.** In the refusal spin it leads by 0.08 s. It turns at 7.46. It drops as the dog decides to
  come, from 14.3 s, so it is low for the whole approach. At "come in" it swings from turned toward the porch to looking
  into the lit room, then lowers onto the paws, and the dog stays.

## Inertia signatures (the catalog), with their no-secondary alternatives

| material | prior | used for | signature seen in the numbers | with `none` |
|---|---|---|---|---|
| hair | 2.4 Hz, ζ 0.34 | tail plume | settles in 1.2 s after the wag, 2 swings | the tail goes 3.8 cm into the floor when lying |
| leather / cartilage | 3.6 Hz, ζ 0.30 | ear tips | 0.83 s, 2 flicks after the rise | ears snap rigidly with the head |
| fur | 3.0 Hz, ζ 0.45 | coat tufts (4 mass proxies) | small lag, no rebound | the coat is painted on |
| cloth (wool) | 0.95 Hz, ζ 0.22, drag 1.6 | scarf | drapes on chest and lap, settles in 3.6 s after sitting | goes 8.9 cm into the lap |
| wood | I 3.9 kg·m², friction 0.42 N·m | door leaf | glides 1.2 s after one pull, knocks on the stop, rests | (kept dynamic in all presets) |
| foliage | 2.2 Hz, ζ 0.11 | shrub stems | 3 decaying swings in 1.96 s after the dog leaves | stays still through the dog |
| metal | pendulum, ζ 0.04 | collar tag | 15 ticks, all at real events | silent |
| paper | 1.6 Hz, ζ 0.12, drag 5 | **not in the scene** (unit-tested only) | — | — |

The synchronized split view (`proof/presets.mp4`, portrait, 3 rows) shows no-secondary, tuned and underdamped (×0.35)
running at once over 3.2–9.6 s and 26.1–29.2 s. The underdamped tail takes 3.4 s and 7 swings to settle after the wag,
the shrub 5.1 s and 11 swings. I could only judge that difference in numbers and in stills, not in motion.

## Living method library

| technique | applies when | proof clip | observed failure | repair pattern | rejected alternative |
|---|---|---|---|---|---|
| pose-spring chain + PBD segments + contacts | a part hangs off a moving body (tail, ears, scarf, stems) | presets.mp4 | a contact stream from a resting tag (72/s) | boundaries carry velocity, interpolated per substep; inelastic contact; anchors kept outside their own colliders; contact onset with hysteresis | louder debounce in the sound (hides a solver fault) |
| mass proxy on an anchor's acceleration | coat tufts | film 3.4–4 s | stripes when anchored on the head (≈20 m/s² in a spin) | anchor on the body, clamp the offset | anchoring on the head |
| hinge with friction + one impulse | a heavy door pushed once | film 5.0–6.2 s | the hinge never rested (friction chatter) | static friction holds it | a keyframed door |
| impulse size solved for timing | the door must reach its stop at the score's 6.2 s | — | — | bisection on J (2.44 N·m·s) | animating the angle |
| look-ahead foot stepper | walking, backing, turning in place | turns in ledger 4 | none seen | — | walk-phase cycling (slides on turns) |
| 3D turn through a chosen side | the refusal (away from viewer) and the look back (toward viewer) | ledger 8 | refusal still at 3.6 s showed the face | turn the other way round | mirror flip |

## What is protected

The six choice times and their visible onsets (A6). The dog never inside: the minimum x is 0.59 and it ends at 0.59.
The approach covers the score's distance at its pace, and the retreat goes the other way (I3, r = 1.00). The back is
turned through the refusal (I4, 0.948). The head is low for the whole approach. There is no interpenetration at the sill,
jambs, floor or lap. Every secondary part's energy decays in the holds. The soft voice sits ≥ 6 dB under the calls. And
the claim on the end card is true.

## What failed and what I changed

The ledger has 11 entries. The main ones:

- The staging was worked out geometrically before drawing: a cutaway, and a door hinged on the far jamb so the open leaf
  sits behind the dog's head instead of in front of it.
- In the first frames I fixed ball joints, the lying pose, the fur, over-warm light, the treeline and banded spill.
- In the turns I fixed coat stripes and a late head at 7.46.
- The head was above the back for the first 4 approach frames, so it now drops as the dog decides to come.
- The collar tag chattered. Four hypotheses, each tested in turn; all four fixes are kept.
- The refusal still at 3.6 s showed the face, so the refusal now turns the other way round.
- In the sound, the consonants of the soft lines peaked too loud.

## What I did not do, and what is unknown

- **Sound was not listened to.** It was measured (RMS per line, envelope plot, peaks) and placed from the solver's
  events. I don't know whether the formant voice is intelligible as "come here", "it's all right" and "come in". It is
  certainly synthetic.
- **No human or independent critic has watched it.** All perceptual statements above are my own looking at extracted
  frames (about 120 frames across the work); I did not watch it play at speed.
- Paper is in the material catalog and unit tests but not in the scene. I made no proof clips for single materials
  beyond the preset split view.
- The SCION operator page is `index.html`: a local page with the film, the comparison and the links. It is not published
  anywhere.
- **Weak, by my own looking:**
  - From 0 to 6 s the dog is dim against the dark railing.
  - The door's opening reads mostly through the light, because in side view the leaf is already broad.
  - In the wide shot (5–14 s) the dog is about 250 px long, so ear and tag motion is small on screen.
  - The legs read as turned capsules (toy-like).
  - The person is simple and has almost no face.
- "State" in `trace.json` is the score state my rig executed. The choice onsets measured from the render are in
  `proof/assertions.json` (A6), independent of those labels.

## Rebuild

`bash build/make.sh` runs the unit tests, the three presets, the render with measurement, the sound, the assembly
(`film.mp4`, `trace.json`, `stills/`), the assertions, the split view and the PAELEO checker. It takes about 4 minutes.
Intermediates go in `build/cache/` (git-ignored).

## Round 2 (after critic round 1: does not pass, close)

The repairs the critic asked for, in rank order:

1. **Look-in.** The neck now has one length (0.25 m, measured at every frame). The head rotates about the neck base and
   never stretches, so the collar stays at the base. At 24.6–25.4 the head settles turned out toward the porch. At
   26.42–26.85 it yaws into the doorway past the person and lifts. From 28.0 the chin goes down onto the paws.
2. **Open door.** The leaf is now hung on the near jamb. The person stands on the sill with the door ajar behind her and
   pushes it open as she steps back in. The impulse is re-solved (4.19 N·m·s) so that the leaf reaches its stop at 6.20
   s. Opened flat against the near jamb, the leaf lies in the section plane and is cut away with the near wall, which is
   the cutaway convention the whole set already uses. From 6.2 s the doorway is an empty, lit opening, and the head and
   forepaws lie in it. Trade-off: once open, the leaf itself is no longer visible; the opening reads through the empty
   lit doorway, the jamb, the lintel and the light.
3. **Ears.** Each ear is drawn as one closed leaf-shaped path, built in screen space from the solved base, mid node and
   tip, so it cannot split. Coat strokes are removed from the upper neck. The ear material (3.6 Hz, ζ 0.30) settles in
   0.83 s after the rise, with 2 flicks.
4. **Turn back.** The head comes round to point at the door by 7.66 s (head direction along x is -0.93 at 7.7 s). The
   body follows at 7.86–8.62.
5. **Standing.** Shorter leg bones keep the standing legs near-straight under the body. The feet were already planted
   (2.1 mm maximum slide).

The checker and assertions A1–A7 still pass. I looked at every frame from 26.21 to 28.58 s and from 7.42 to 8.42 s. Not
addressed: the dog is still dim at dusk (0–6 s), and the lie-down is still quick. The sound has still not been listened to.

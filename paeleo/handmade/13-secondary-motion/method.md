# SCION 13 · Nora Willett — Secondary Motion · PAE-02 threshold

**Swarm language.** Secondary Motion for Performed 2D Animation (Willett, Li, Popović, Berthouzoz, Finkelstein 2017), as a
studio: performed *primary trajectories* of rigid paper pieces, and *secondary rig links* hung from them, each an
*inertial spring-damper* with *collision masks* under *wind and gravity*. Here the dog is made of its own secondary links: a
long-coated dog of crepe- and tissue-paper fringe, so that material and intention are carried by the coat, ears, tail plume
and dewlap rather than by a silhouette.

**Thesis.** The viewer should read the dog's state from how its paper moves: the coat flattens and the tail tucks when it
is called; the ears flick to the soft voice before the head comes round; the coat swings, lags and settles as it lies down;
in the last seconds the wind lifts a few fringe tips while the dog stays still. What would make it bland: a generic
oscillation on everything (see `proof/compare_none_generic_tuned.mp4`).

## How the dog is built (build/scene.js, build/draw.js)

- **Primary pieces (performed trajectories).** Six torso discs on a spine whose height bends for crouch (rear lower) and
  lying (front first, rear 0.13 s later); two neck discs, a skull, two muzzle discs and a nose; four two-bone legs with
  paws. Performed curves, keyed to the score's choice times: body heading (turns its back 3.44–3.78 s through facing the
  viewer, turns back 8.05–8.80 s), head heading (leads the body: 3.40–3.70 s; over the shoulder to the door 7.44–7.68 s with
  the body still lying; into the room, away from the camera, 26.45–26.95 s), lie, chin-rest, head height (low on the
  approach), fear. x, crouch, ears, tail, wag and "moving" come from the score. Stance feet stay planted: their offset
  falls exactly as distance travelled grows (stride 0.56 m, the score's own walk-phase rate); swing feet lift.
- **Secondary links (264 on the dog).** 180 body strips (15 rings × 12 rows, jittered), 20 neck-ruff, 10 head (forelock,
  cheeks, beard), 3 dewlap, 2 five-node ear flaps with 16 feather strips hung from the moving ear links (second order), a
  six-node tail with 20 feather strips, 12 leg feathers. Elsewhere: 8 curtain strips, 34 reeds, the person's 7 hair strands,
  2 scarf tails, 3 coat tails. The door leaf is a driven spring-damper hinge.
- **Solver.** Per node: a = k(r − p) − c(v − v_r) + g·grav + drag(w − v), semi-implicit Euler, 4 substeps per frame
  (dt = 1/96 s), inextensible links by follow-the-leader projection, then collisions, then a speed clamp. r is the rest
  shape the primary piece carries this substep (interpolated between frames), v_r its velocity, w the wind.
- **Material presets** (k 1/s², c 1/s, gravity scale, drag 1/s): crepe fur 70 / 7 / 0.35 / 1.4, rising to 230 / 17 when
  afraid (the coat is held flat, sleek and back along the body); ruff 60 / 6.5; ear 120 / 7.5 / 0.55 / 0.6; feathers 45 / 6;
  tail 95 / 8; dewlap 22 / 3.2 / 0.8 (loose, it lags); curtain 6 / 2.2 / 1 / 2.4; reed 140 / 2.6 (springy, little damping,
  stiffer at the root); hair 28 / 4.2; scarf 9 / 4.2; coat tails 30 / 6. Tip nodes are softer (k × 0.35–0.7).
- **Collision masks.** Fur, ears, tail: the floor and the dog's own discs (torso, neck, skull, muzzle). Curtain: floor,
  the dog, the person's arm, torso and head. Reeds: the dog. Hair: her head and torso. Scarf: her torso. Coat tails: the
  floor and her legs.
- **Forces.** Gravity; a gust field from the yard toward the house (named gusts at 5.4, 12.8, 19.6, 30.4 s), none indoors;
  a draft out of the doorway when the door opens (6.15–8.2 s).
- **Where intention is carried.** Rest-shape targets change with the dog's state: fear blends the coat's rest direction from
  "hanging, a little fluffed" to "pressed back along the body" and stiffens it (refusal, retreat); the tail's rest angle
  follows the score's tail value (tucked under on the refusal); ears move from flat to semi-pricked, and receive an
  impulse 60 ms after each soft-voice onset (the flick); lying turns the coat's rest direction out and back so it spreads on
  the boards. The coat, ear and tail motions are not keyed: they are what the solver does with those targets.
- **Drawing.** Orthographic diorama camera (yaw +16°, pitch 12°) from the porch side, house cut in section at the door's
  near edge. Each strip is a torn ribbon with a glued rounded top, a crease line and a torn tip; rows overlap like shingles
  (sort key = view depth + height above the spine), discs are torn tissue circles, everything shaded by a cool dusk ambient
  plus the warm lamp wedge through the doorway. Paper-fibre overlay.

## Staging of the hard moments

- Refusal: a turn through a front view (every frame a dog: `stills`, frames 3.40–3.90 s were looked at one by one); the
  coat flattens and the tail tucks; it lies down facing away (4.25–4.95 s), chin down.
- 7.46: ears flick at the soft voice, the head comes round over the near shoulder to the door (muzzle level, 3/4 toward
  us), the body still down; it rises at 7.86 and turns its body 8.05–8.80.
- Approach: head held below the back line for the whole walk (measured 100 % of frames 15.2–23.6 s).
- Lying across the sill: torso on the porch side, neck over the sill, skull, muzzle and forepaws inside the room, tail out
  on the boards; legs folded (forelegs forward, hind legs out to the side under the coat).
- Looking in (26.4): the neck stretches in and the head turns into the room's depth, away from the camera: the back of the
  skull (dark crown) between the two ears, inside the lit room; the person sits nearer the camera, so it is not a look at her.

## Measured (from the encoded film's own render pass; build/cache/summary.json, trace.json)

Onsets measured from the dog's mask pass (score time → measured): retreat 1.000 → 1.125 (centroid moves away > 2 cm);
watch 2.333 → 2.375 (head starts to rise); refuse 3.417 → 3.542 (head starts to turn), back shown (snout right of skull)
3.583; turn back 7.458 → 7.542 (head moves toward the door), muzzle toward the door 7.583; approach 14.708 → 14.792;
lie down 23.792 → 23.958 (torso drops > 2 cm); looks in 26.4 → 26.5 (head moves 2 cm further in). End: lying, head
centroid at x = −0.10 m (inside the threshold at x = 0); while looking in −0.30 m. Checker: ALL OK (I3 r = 1.0 on
x_world_measured, I4 share turned 0.93). Voices: calls −16.8/−16.4 dBFS RMS, soft −27.3/−27.8/−29.7 dBFS (10.5 dB under),
room tone −42.6 dBFS; each voice starts 40 ms before the dog's reaction. Film 912 frames, 38.0 s, 4.7 MB, H.264 + AAC,
faststart. Numeric assertions (`proof/assertions.json`, 8/8): the coat's energy peaks after the lying onset (24.13 s) and
is below 15 % of that peak by 25.0 s (the pose stops at 24.55 s); ear-energy peaks 0.10–0.22 s after each soft voice; fur-tip distance from
the spine drops 0.248 → 0.197 m on the refusal; tail tip drops 0.32 → 0.24 m.

## What failed and what changed

See `ledger.jsonl`. In short: a picket-fence/mop coat → overlapping shingles; a room-side camera would have turned "looking
in" into looking at us → camera moved to the porch side; the near jamb cut the lying dog in two → house cut at the door's
edge; the curtain hid the head → drawn to the far half; the facing measure (head vs torso centroid) was late for the
over-the-shoulder look → measured from snout vs skull; a nose drawn over the back of the skull → depth-ordered muzzle.

## What is weak (looked at, not fixed)

- At the wide framing (0–14 s) the standing dog is about 170–210 px tall (ears included) and its head about 60 px; the ear flick and the coat's lag read, but small.
- Crouched and flattened on the refusal, the dog can read as a hedgehog for a few frames.
- The back of the head when looking in is legible but small and busy (cheek fringe and ruff in front of it).
- Lying, the near-side coat still hangs a little like a skirt rather than spreading flat.
- The voices are formant-synthesized and only roughly intelligible; the person is a simple paper puppet.
- The camera moves (pull back 4.6–6.4 s, push in 14.8–24.2 s); x_world_measured unprojects through it.

## What I did not do

No kit footage, Quick, Draw! drawing or archive frame is used; no maquette; no text on screen during the scene; no
independent critic was run by me (the builder does not approve its own work); no mobile operator page. The solver is not
a reproduction of the 2017 paper's system; it is the same primitives built here.

## Rebuild

`bash build/make.sh` (≈3 min): render.js (scene + measurements) → sound.py → assemble.py (film, trace, stills, checker)
→ test_motion.py → comparison clip. `build/look.py` extracts frames from the encoded film for looking.

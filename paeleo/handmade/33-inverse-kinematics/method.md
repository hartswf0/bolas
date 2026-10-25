# SCION 33 · Inverse Kinematics — Contact and Reach · the threshold, handmade

## The swarm

One agent working alone, holding the six roles of the prompt in turn: contact dramaturg (which contacts carry each choice), IK solver builder (`build/geom.py`, `build/perform.py`), support/counterbalance animator (the footfall planner, the person's lean and brace), prop interaction engineer (the door), stability tester (`build/proof.py`: assertions, residual curves, analytic-vs-FABRIK comparison). The sixth role, the independent acting critic, is **not** filled: the builder cannot approve its own work. No critic has seen this film yet.

## Thesis

Action has consequences you can see: a paw that is planted stays planted until the body has carried its home away; a hand that reaches either arrives or visibly falls short; the door gives only after it is pushed, and it is heavy; the dog's chin finds its own paws. The commands are reaches that cannot arrive (the hand stretched toward a dog 3.4 m away, residual stays at metres); the invitation is a hand put down on the boards, a target the dog can choose to come to. What would make it bland: a dog that slides, a door that opens by itself on cue, a hand that ends where the animator wanted rather than where the arm can go.

## Native formal language, as used

- **World-space targets**: every paw lock, the dog's head look-target (the person, the boards ahead, the low hand, the lit room), the chin-on-paws target, the person's hand targets (door edge, thigh, the dog, the boards), feet keys.
- **Joint-angle limits**: two-bone chains cannot straighten past 0.999 of their length nor fold the middle joint under 18°; neck pitch limits (standing −0.80..0.74, lying up to 0.94 of the neck); head yaw relative to the body 1.25 rad standing, 2.35 rad lying or looking back (the look back over the shoulder at 7.46 s is at this limit, with a spine bend of 0.30 rad).
- **Pole vectors**: fore elbows bend back, hind stifles forward (and out, when lying); person's knees forward, elbows down/back.
- **Contact states**: plant, lift, release, touch, grip, bear weight, resist-then-give, stop — all in `data/contacts.json`, all placed from the rig and the door simulation, and every sound in the film is placed from this list.
- **Planted-foot locks**: the footfall planner (`Planner` in `perform.py`): a leg lifts when its home, predicted 0.12 s ahead, has left its lock by a threshold, under support rules (never both legs of one side, never both fores or both hinds) — or at once, whatever the rules, when the leg can no longer hold the paw (the reach-gap test). It lands where the home will be at touchdown, a little beyond.
- **Residual metrics**: `data/residuals.json` per frame (each leg's reach residual and bend side, planted flags, planted-paw slip, chin residual, the person's chains, the door angle); `proof/contact_timeline.png` draws them against the score's choices.

Typed boundaries: world metres (X along the porch = the score's x, threshold plane at X = 0.40, sill edge 0.56, steps 4.9; Y up; Z toward camera A), scene frame i = 0..767 at 24 fps on the score's clock. Inputs: the score JSON. Outputs: `build/cache/pose.pkl`, `data/*.json`, frames, `trace.json`. Two fixed camera set-ups (A wide, B closer on the sill), one cut at 20.5 s mid-approach, same side of the action.

## The dog: what it is made of and how it moves

A shepherd-type constraint rig: pelvis and chest points, a neck, skull and muzzle, ears, a seven-link tail, and four three-segment legs (upper arm / forearm / pastern; thigh / shank / metatarsus). Each leg is solved every frame by analytic two-bone IK from the shoulder or hip to a wrist/hock point set from the paw target and a pastern direction (near-vertical standing, flat along the boards lying). It is drawn as what it is: tapered capsules on joints, the torso, head and tail as merged volumes, each limb bone with its own outline and a ring at the elbows, stifles, wrists and hocks; far-side limbs darker; lit by the dusk and, once the door opens, by the door light, which also casts the body's shadow on the boards. Proportions were studied (numbers only) from the archive dog's rig keys (*Amateur Film New Jersey C*, public domain): body/leg ratio 1.75. No archive pixel is used.

How each choice is carried:
- **Retreat (1.0 s)**: crouch, head low, tail tucked, and the dog walks backward — the planner steps the paws behind it, the claws scrabble.
- **Watch (2.33)**: the head comes back up (measured onset is the head rising).
- **Refuse (3.42)**: a real 3D turn in place through facing the camera, the head leading; paws step (fast 0.14 s swings, released when out of reach); the back is to the door by 3.75 s (measured) and the dog lies down facing away, chin on paws.
- **Turn back to look (7.46)**: the chin leaves the paws and the head comes round over the shoulder to the door at the neck's limit; then the forelegs re-plant, it rises, and turns (8.1–8.85) through facing the camera again.
- **Approach (14.71)**: the head goes down from 14.42 s and stays below the back line for every approach frame (measured: 218 of 218, min 16 px below); paws planted and stepped by the planner, no slide (planted slip 0.0 m measured); its eyes go from the lit boards to the person's low hand.
- **Lie down (23.79)**: forepaws walk out to their lying place, front lowers then rear, belly on the boards (sound: body settles, sigh); forequarters inside the door frame, nose in the room, tail on the porch.
- **Come in (26.4)**: the head lifts and turns into the lit room (the score's `look` drives the target from the boards to the room); at 28.0 it settles, chin on paws, and stays.

## The person and the door

Same language: capsules on two-bone chains, keyed world-space targets, locked feet. It holds the door edge (grip) and pats its thigh while calling; on the second call it steps onto the sill, leans with hips back, and its hand reaches for the dog — a target 3.4 m beyond the arm, so the arm straightens and the residual stays at metres: the command can't arrive. It lets go (the door drifts nearly shut on its own weight, the light narrows), steps aside, bears weight on one hand and sits against the wall. It twists and reaches back to the door edge: the hand touches at 5.96 s, the door holds against static friction until 6.08 s (resist), gives, the hand follows only while it can reach the edge (release 6.19 s), and the heavy door coasts on to its stop (7.04 s). The light comes out by 6.2 s. Then the hand goes down to the boards, palm up, and stays.

## Protected (measured, `data/assertions.json`, `trace.json`, `invariants.json`)

- Planted-paw slip: 0.0 m per frame, all frames.
- Bend direction: 0 inverted knees/elbows (3072 leg chains).
- Reach residual: within 1 cm except a handful of frames in the turns and the lie-downs (see the report numbers in `data/assertions.json`); the swinging ones are drawn with the paw carried on the leg; **the planted ones (2 frames) are real failures**, kept visible here rather than hidden.
- Analytic vs FABRIK on every leg chain: `data/solver_compare.json`.
- The door moves only after the hand's contact and static friction.
- Choice onsets measured from the render (silhouette mask, head and muzzle on screen), not from the state label: in `trace.json` → `summary.onsets_measured`, all within ±0.25 s.
- Soft voice vs calls (RMS of the voice stems as placed): `data/sound_levels.json`.

## Artistic achievement judged only by viewing

Whether the dog reads as a dog that decides — the backing away, the turned back, the look round, the slow low coming, the lying across the sill, the look in and the staying — and whether the reach-that-cannot-arrive against the hand-put-down reads as the difference between command and invitation. Not judged by the builder.

## What failed and what changed

See `ledger.jsonl` (one line per attempt). In short: turns first left paws behind (0.37 m residual) → release-on-reach-gap and fast turn steps; the first dog read as a llama (vertical neck, segmented sausage body) → shorter limited neck, merged body volumes, new proportions; the look back pointed at the camera → rest released, lying neck limit; the door would not open, then was pushed by an absent hand → rebuilt so torque exists only while the hand reaches the edge; the end was too small and dark in the wide → one cut to a closer set-up; a rear camera along the light was tried and rejected (the lying dog became a lump); the synthetic call had no upper formants (seen on a spectrogram) → formant gains raised.

## What was not done / unknown

- No independent critic has seen it; no human has watched it; **nobody has listened to the sound** — levels and formant structure were only measured and looked at on spectrograms. The synthetic voices may sound robotic.
- No interactive constraint scene (the prompt's deliverable 8 asks for one): only `operator.html`, a static mobile page with the film, proofs and links.
- No git checkpoint (the brief forbids git); `build/make.sh` rebuilds everything from the score.
- The chest-to-ground and limb lengths are a shepherd-type estimate checked only against the keys' ratios.
- The trace's `state` is the score's label; the evidence that the choices happen on screen is the measured onsets.

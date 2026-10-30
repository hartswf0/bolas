# SCION-48 · State Machines — Characters That Can Refuse · PAE-02 the threshold

## Thesis

The refusal is the dog's own decision. Nothing in this film keys the dog's choices: a machine that perceives, wants and
remembers chooses them, frame by frame, from the circumstances of the score (the call, the reach, the standing figure, the
sitting person, the open door, the low hand, the soft voice). The machine was then tuned, as a dog is learned, until its own
decisions fell on the score's times. The film shows those decisions only as behaviour; the machine itself is shown honestly on
the end card (its states and the transitions it actually took, its drive curves, its choice times against the score), never
as labels in the scene.

What would make it bland: an obedient dog (the default every state-machine character slides back to), labels doing the
acting, a puppet whose turns are keyed rather than chosen.

## Native formal language and the material

States, guards, transitions, priorities, action windows, intentions, persistent world data. The material had to be native to
that idea, and different from swarm 25 (vector capsules) and 27 (programmatic web render): the scene is shown on a **display
board of 320 × 180 cells**, each cell itself a tiny two-state machine: a flip-disc, black on one face and straw-yellow on the
other, that holds its state with no power (persistent world data, literally), plus LEDs. One rule governs the board: **what
gives light is lit** (the sky, the room behind the door, the moon: LED cells) and **what receives light is flipped** (the dog,
the person, the boards, the house: discs; tone is the density of flipped discs, a 4 × 4 ordered dither). A cell that changes
state is drawn mid-flip for that one frame, and every flip clicks on the soundtrack. The cut to the closer shot at 24.625 s is
the controller rewriting the board column by column (8 frames). The person's words appear on a destination-sign strip of the
board while they are spoken; the dog's states never appear.

## The machine (build/machine.py)

One tick per film frame (24 Hz), two ticks of perceptual latency (it hears 80 ms late).

- **Perception.** Hearing is all-round (call, soft voice). Seeing goes where the head points: `vis = clamp(0.5 + 0.7·cos(gaze))`,
  so a dog with its back turned does not see the door open or the hand lowered. It keeps a **world model** of what it last
  saw (sitting, door open, low hand); the light on the boards reaches it a little even facing away.
- **Drives.** *Pressure* (the push: call + reach × proximity, smoothed); *fear* (rises with pressure and with a standing
  figure in the doorway, falls faster when it has seen the person sit); *memory of being pressed*; *curiosity* (kicked by a soft
  voice, a door changing, a hand lowering; decays); *trust* (grows with the remembered invitation — sitting, open door, low
  hand, soft voice — slowed by fear squared, eaten by pressure).
- **Utilities.** watch = 0.35 + 0.6·curiosity·(1−fear); retreat = pressure·(0.6+fear)·room-behind;
  refuse = pressure·(0.6+fear)·(no room)·1.2 + reach (and, once refusing, a sulk of 0.30 + 0.40·fear);
  approach = 2.2·(trust − 0.6) + 0.35 − 2·fear, guarded by "door open and person sitting, as seen";
  lie_down = 2 on arrival at its chosen place. The current behaviour gets a hysteresis margin; each has a minimum dwell
  (action window) that only danger (retreat, refuse) may cut short.
- **Sub-states.** refuse {turn, sulk: lies down with its back turned}; lie_down {settle, rest: chin on paws, look_in: while
  curiosity is above 0.567}.
- **Not entering.** A candidate *cross* is scored at the sill (trust − 1.25) and logged per frame (`U_cross`); it never wins.
  That is the dog's threshold cost, persistent world data, not a wall in the code.
- **Body layer.** The head turns with a 0.09 s time constant, the body with a rate limit and only once standing: the head
  leads at 7.5 s because heads are faster, not because a key says so. Posture, tail, ears, crouch, wag follow drives.

**Tuning** (build/tune.py, ledger.jsonl rounds 1–3): coordinate descent over 11 physical parameters (trust gain, pace,
braking, curiosity decay, look threshold, pressure smoothing, backing speed, acceleration, room, hysteresis) minimising the
machine's choice-time errors and its x against the score's x. The score's dog states are never an input. Two structural fixes
were needed, not parameter tweaks: the arrival guard (approach used to give up 2 cm short), and splitting *pressure* (commands
only) from *unease* (a standing figure) so that backing stops when the calling stops.

Machine decisions against the score (first frame in the new state, s): see `trace.json → machine_onsets`
| choice | score | machine | dt |
|---|---|---|---|
| watch -> retreat | 1.0 | 1.125 | +0.125 |
| retreat -> watch | 2.333 | 2.5 | +0.167 |
| watch -> refuse | 3.417 | 3.5417 | +0.125 |
| refuse -> watch | 7.458 | 7.5 | +0.042 |
| watch -> approach | 14.708 | 14.6667 | -0.041 |
| approach -> lie_down | 23.792 | 23.7917 | -0.000 |
| lie_down.rest -> lie_down.look_in | 26.4 | 26.5 | +0.100 |
| lie_down.look_in -> lie_down.rest | 28.1 | 28.0833 | -0.017 |

## The dog (build/render.py)

A body of 27 rounded segments (deep chest, tucked loin, neck, skull, muzzle, black nose, two ears, four legs, three tail
segments) posed every frame from the machine's body layer and ray-cast as a signed-distance field into the board's cells.
It is never drawn: it exists only as the set of discs the controller flips. Legs are always solved by two-bone IK from foot
targets (stance feet travel backward at exactly the body's speed, walking phase from its own travel, signed so that backing
away walks backward); postures move the foot targets, never blend joints. Its readable marks are made of the board too: a ring
of black discs around it, black discs at depth breaks and where the head meets the body, one black disc per visible eye,
a darker saddle.

The world is a ray-cast porch, house, door on a hinge, steps, yard, a lit room with a chair and a picture, the lamp's light
through the doorway (with the dog's and person's shadows), dusk sky with a tree line. Two cameras: wide until the dog has
lain down, then the closer shot of the sill.

## Measured (from the render, trace.json → measured_onsets)

| choice (measured on the board) | score | measured | dt |
|---|---|---|---|
| retreat (backs away) | 1.0 | 1.167 | +0.167 |
| retreat -> watch (stops backing) | 2.333 | 2.375 | +0.042 |
| refuse (head swings away) | 3.417 | 3.542 | +0.125 |
| refuse -> watch (head comes round) | 7.458 | 7.5 | +0.042 |
| approach (comes) | 14.708 | 14.625 | -0.083 |
| lie_down (lowers onto the sill) | 23.792 | 23.917 | +0.125 |
| looks in (head lifts into the doorway) | 26.4 | 26.5 | +0.100 |
| settles (chin back down) | 28.1 | 28.125 | +0.025 |

How measured: backing/coming = velocity of the torso cells cast onto the path; head swings = head-cell centroid moving > 6–8 px against the body cells; lying = height of the dog cells dropping 7 %. Smoothing (±2 frames) can pull an onset a frame or two early (approach −0.08 s). Look-in is measured as the moment the settling head reverses and rises/pushes forward by more than 6 px.

Invariants (tools/paeleo/check_handmade.py): ALL OK — I1 all six within 0.17 s (state = the machine's); I2 min x 0.6175, end 0.6175; I3 r = 0.998 on x_world_measured; I4 back turned in 98 % of refusal frames (facing measured from the cells).

Sound (cache/sound_levels.json, measured on the synthesized stems): calls -16.5 dBFS RMS, soft phrases -28.3 (11.8 dB under the calls), room tone -47.6 (19.3 dB under the soft voice); peak 0.85.

## Protected conditions

The machine is never given the score's states; the dog's body never sets x (the machine does); facing is measured from the
cells (head cells against body cells); x_world_measured is the dog's centroid cast back onto its path; the soft phrases stay at
least 6 dB under the calls and above room tone; no state names in the scene.

## What failed and what changed

See ledger.jsonl. In short: an untuned machine came 1.1 s early and never lay down; the push was confused with unease;
the first board had the dog the same density as the porch; the room leaked outside the house; the lamp sat behind the opened
door; the dog's head hung while turned away (read as grazing); the turn back tangled the legs (joints blended while turning);
looking in was a lift of the head toward the light. Each was repaired at its cause.

## What is weak, unknown, not done

- After the critic's round (ledger 13): the lying pose was refolded (hips below shoulders, hind legs flat, tail laid along the porch outside the jamb) and the close camera raised; the rise no longer swings the legs with the spine; the refusal turn keeps the tail and ears visible. One end-on frame remains at 3.63 s.
- Scale: in the wide shot the dog is ~200 px long. The refusal turn passes through a rear view (rump, back of the head) at
  3.6–3.8 s; the turn back passes a front view at 8.1–8.4 s, and while it rises (7.9–8.2 s) the legs unfold during the
  first part of the turn and read busy.
- Film checked on frames extracted from film.mp4 (proof/film_turn1.jpg, film_turn2.jpg, film_look.jpg, film_lie.jpg, film_wide.jpg).
- The person is a secondary, simplified figure; the seated pose reads as a figure on the boards with bright hands, little more.
- Voices are formant-synthesized: intelligible as prosody more than as words; the captions carry the words.
- The board dither shimmers where things move (that is the material, but it costs detail).
- Not done: an interactive runtime / playable page, mobile playtests, an independent critic run (by design: a separate critic
  judges this). Not measured: human comprehension.

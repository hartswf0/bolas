# SCION 30 · SAM 2: Prompted Mask Proposal Swarm

**Thesis.** Propose masks at scale, keep every one inspectable, and refuse to infer parts the frames do not show.
The threshold scene is built only from *accepted mask proposals* of real archive frames. Each proposal keeps its
prompt (DINO box, our point prompts), its object ID, a confidence proxy and its correction strokes. The dog is never
drawn, and when no frame shows a part the part is kept out of view, never invented.

## Native formal language, as used here

| primitive | where it lives |
|---|---|
| boxes, points, masks | `proposals/proposals.json`: per source frame, the SAM 2.1 proposal (Grounding DINO box, model IoU) and our own prompts (person: box + positive/negative points). Pose keys from `kit/archive-dog/pose_agent_v8.json` are used as **point prompts** to split part proposals (neck point, tail root). |
| object IDs | `dog#1` is linked through all 48 accepted frames (the linker compares each proposal with the last accepted one after camera compensation, IoU ≥ 0.45). The door breaks into `door#1…#5` because the person occludes it in *Straight Talk*. Rejected proposals get no ID. Also `hand#1`, `sitter#1`, `person#1`. |
| confidence proxy | `conf = sqrt(stability × edge)`. Stability is the IoU with the neighbouring masks after camera compensation (the sign of the camera track was chosen from the data). Edge is the share of the mask boundary lying on a real image edge. Rejected if conf < 0.42 or the area is outside 0.6–1.6× the running median. **Rejected: f23** (conf 0.41, area 4.45×, a leak into the ground) and **f49** (area 1.72×). |
| correction strokes | `proposals/corrections.json`: 8 strokes, each with polygon/rule and reason (legs region, tail box, head disk ∩ neck half-plane, debris removal, forearm add, bag-spread removal, silhouette closing and fade). |
| source-frame linkage | every rendered frame lists in `trace.json → proposals` the source frame(s), mirror flag and part used. The end card is a contact sheet of every dog frame used, with its confidence and the parts taken. |
| refusals | `proposals/refusals.json`. |

A numerical invariant that can be tested: `tools/paeleo/check_handmade.py` gives ALL OK. Also measured: soft voice
RMS −24.6 dB against calls at −13.3 dB (10.3 dB under), with room tone at −61.5 dB (`build/cache/sound_levels.json`).
Artistic achievement judged by viewing only: does a dog cut from 1930s home-movie frames read as one animal that makes choices?

## The dog: what it is made of and how it moves

All the dog material comes from 50 frames (384×288, 12 fps) of *Amateur Film New Jersey C* (public domain): 28 distinct
frames are used. Movement is **re-timed found motion by substitution of proposals**. Each proposal is placed by its
measured alpha centroid on the score's `x` (`x_screen ≈ 985 − 205·(x − 0.59)`), with its feet line on the porch.

- **Watch:** f38/f39 as shot (three-quarter, facing the door, face visible), alternating every 7 frames.
- **Retreat (1.0 s):** the head drops (f39→f42), then the f42–f45 step is played **backwards**, with its phase locked to the distance from the score, so the dog backs away step by step.
- **Refusal turn (3.42 s):** the source's own 180° turn played in reverse (f38→f36→…→f26→f17→f14→f5→f3→f2). The dog turns through facing the camera to its side, and by 3.71 s (f17) its side and rump are toward the door. It holds f2/f1/f0, the rear three-quarter view with the dark back of the head, from 3.96 s to 7.46 s.
- **Turn back (7.46 s):** the same source turn played forward (f17→f26→f29→f32…f39). In f29–f36 the source dog's head is already turned right toward the door while its body still faces the camera, (superseded in round 1: see below).
- **Approach (14.71 s):** the head lowers (f39→f42), then f42–f45 (a four-frame step; f42 ≈ f46 by aligned-mask IoU 0.73) is played forward, phase-locked to distance. The source dog was walking to its bowl, so its head is below its back for the whole walk.
- **Lying (23.79 s):** no frame shows this dog lying. The f04 proposal (level back, mirrored so it faces the door) **sinks whole behind the porch board** as the score's `lie` rises. The camera stands low in the yard, so the board hides everything below the floor line. Once it is down, the lying dog is an assembly: the f04 body, a tail part from f19 (lying back outside the door), and head part proposals substituted at the neck prompt point. These are f40 (level, muzzle forward), f44 (lower) and f47 (nose down). Its front half is past the wall section into the lit room, and the tail is outside.
- **Looking in (26.4 s):** the head proposal changes from f47 (nose down) to f40 (level, muzzle forward into the lit room) at 26.417 s, and settles back to f47 at about 28.3 s.

## The world

The stage is a cut-away section at dusk. On the left is the porch, seen from low in the yard (porch front board and lattice). The wall
section and doorway gap are at x 985–1020, and the lamp-lit room is on the right. All of this, the sky and the light coming out
of the door are computed (numpy). The door leaf is *Straight Talk* f31 (door#5), foreshortened by its swing angle.
The standing person is our own box + colour proposal on *Straight Talk* f02, shown as a backlit silhouette. The frame cuts
her at mid-thigh, so the silhouette fades into the dark of the doorway, and no legs or face are made. The reaching arm
(3.4–4.6 s) is hand#1 f20 (*Door to Heaven*, 1941) as a silhouette. She steps aside into the room at 5.4 s and, from 5.9 s,
the sitting person is *Survival Stresses* f36 (a hooded figure in a sleeping bag, facing the door). The low hand (6.8 s)
is hand#1 f30 with its forearm stroke, kept on the inside of the sill.

Sound is all synthesized: flite voice (slt), with calls at 0.70 and 3.05 s and soft lines at 7.05, 10.40 and 25.95 s, each starting
before the reaction. Also room tone and crickets, the door's latch and creak at 6.15–7.1 s, paw ticks fired only when
the walk proposal changes, the body settling and an exhale when it lies.

## Measured onsets (from the rendered dog layer, `trace.json → summary.measured_onsets`)

retreat 0.875 (−0.125) · watch 2.417 (+0.084) · refuse 3.417 (0.000) · watch 7.458 (0.000) · approach 14.708 (0.000) ·
lie down 23.708 (−0.084) · look in 26.417 (+0.017). Signals: rate of silhouette change (the idle hold changes once in
7 frames, a choice changes every frame or two), leaving the backing gait, sustained lowering of the body top, and the head
proposal change. The retreat onset is early because the change-rate window catches the last idle substitution at 0.875 s.
The dog visibly cringes at 1.00 s.

## What failed and what changed (see ledger.jsonl)

- Object identity broke at f23 (a rejected leak). The linker now links across rejected proposals → one `dog#1`.
- The first watch frames (m9–m11, mirrored) had the head pointed at the sky. Then m3/m4 still read as howling. The fix was f38/f39 as shot (head level, face toward the door), which also removed every mirror swap from watch, retreat and the turns.
- f19/f21 in the refusal turn showed a double body (the mask took in the shadow) and were removed from the path.
- Lying, attempt 1: f44 with the legs clipped at the floor. The head went under the floor and a leg stuck out. Attempt 2: f04 with its own head rotated about the neck. The white chest showed as an open jaw, and rotation is a pose the source does not show. Attempt 3: head part proposals from other frames on the f04 body. The neck half-plane took legs with the head, so a disk around the nose/neck prompts was added. Attempt 4: a legless body was visible floating while it lowered. The camera moved low behind a porch board, and the whole proposal now sinks behind it.
- The sitter in f25 was only the bag: the SAM mask had missed the head. Changed to f36, whose mask includes the hooded head. A colour-preserving grade keeps the hood readable.
- A white speck above the rump came from the tail box, which was tightened.

## What is protected, what is weak, what was not done

Protected: the score timing (ALL OK), the dog never inside (min x 0.59), every dog pixel traceable to a proposal.
Weak (judged by me, not by an independent critic): the source is 384×288 and soft. At 1.65× the dog is mottled, and its
ears and eyes are barely legible. The rear view is a three-quarter view (f0–f2), not a straight one. Through both turns the
dog passes through facing the camera. Substitution reads as a slightly stepped 12-fps motion, and the walk loops a 4-frame
step. The lying body is a straight-backed torso whose lower half is hidden. The board hides the paws for the whole film. The
score's ear/tail/wag and lying-during-refusal are not performed (no evidence). The voice is a synthetic flite voice.
Not done: no new segmentation model was run here (no GPU/network). The proposals are the precomputed SAM 2.1 masks,
re-adjudicated. The operator page, the separate critic agent and branch forks of the SCION prompt were not run. No human has watched the film.

## Round 1 repairs (critic: DOES NOT PASS, reviews/round1.md)

- **Looking in:** restaged. From 26.417 s the lying body takes the f01 head, mirrored. That is the rear three-quarter head with the dark back of the skull and ears toward the viewer, and the back of the head has evidence in f0–f2. It is set 20 source px lower because f1's neck is raised. The sitter moved right and the low hand withdraws by 25.8 s, so the head points into the lit room above her, not onto her lap.
- **Turn back at 7.46:** the f01 refusal body is held while the head parts f33 and then f36 (both pointing toward the door) take its neck point for 6 frames, a composite of real heads. The body changes view at 7.71 through f36, f38 and f39. The lumpy f17/f26 frames are gone. This replaces my earlier claim that the forward source turn led with the head: the critic saw the whole dog swap view at once.
- **Refusal turn:** f17, f16 and f14 are removed (f26 → f5 → f3 → f2), so every frame from 3.72 to 3.93 is legible.
- **Walk loop:** f42 (garbled head) is removed everywhere; the step is f43–f45.
- **Seams and tint:** part boundaries are feathered (2 px at source scale), and the lying warm tint ramps with the drop.
- Measured onsets now: 0.875, 2.417, 3.417, 7.458 (first head-part change), 14.625, 23.708, look in 26.417.

## Round 2 repairs (critic: PASS narrowly, reviews/round2.md)

- **Look-in head:** a curved correction stroke on f01 removes the straight SAM edge that ran down the person's coat, along with its pale throat band. The head edge is feathered 3 px. The swap is eased f47 → f40 (3 frames) → f01 mirrored, and the reverse on the way out.
- **Backing away:** an evidence refusal. No frame shows this dog stepping backwards, so it no longer runs a forward stride in reverse. It backs in shuffles: 4 frames held, 2 moving, and the held drawing (f43/f44) changes only at a shuffle.
- **Lying down:** the m4 body now sinks with the level f40 head, so the muzzle never rises above the withers. The raised m4 head is no longer shown.
- **Measured onsets:** 0.875, 2.417, 3.417, 7.458, 14.625, 23.792; look in 26.417.

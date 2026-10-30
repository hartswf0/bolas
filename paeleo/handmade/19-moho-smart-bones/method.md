# SCION 19 · Moho Pro — Smart-Bone Character Laboratory · PAE-02 method

## Thesis
A dog that keeps one body through every view. Its choices at the threshold are carried by a rig, not redrawn per shot: bones
with IK legs, Smart-Bone corrective actions that re-sculpt the mesh when a bone bends, and a head switch layer whose drawing
is chosen by a view-control bone. The defining passage is the turn back at 7.46 s: the head leads over the far shoulder
through the back-of-head drawing while the body is still lying, then the body follows through its own back view.
What would make it bland: a profile cut-out mirrored at the turns, or a 3D maquette with an outline shader.

## The drawn look (chosen against 37, 33, 25, 34)
I looked at one still each (9.0 s) from 37 (textured 3D mesh), 33 (wooden mannequin), 25 (flat vector cut-out with
gradients) and 34 (engraved line hatching). This film is a single variable-width ink contour over flat fills on paper grain:
each group's ink is the union of its shapes swollen by the line weight and laid twice with a down-right offset (thin on the
lit side, heavy on the shadow side); the flat fill goes on top; patches (cream bib, muzzle, socks, inner ears) are clipped to
the fill; details are tapered brush strokes. The dog is ochre with cream bib, muzzle and socks, so front and back read apart.

## The rig (build/rig.js)
- **Bones.** root, pelvis, spine, withers, neck, head, two view-control bones (view_body ψb, view_head ψh), per leg a 3-bone
  chain (upper, lower, paw), three tail bones, two ears: 25 bones counting both sides. Legs are IK constraints: 2-bone solve to
  the wrist/hock with the paw segment's angle set by the pose (near-vertical standing, flat when lying); elbows bend back,
  stifles forward, fixed by sign.
- **Vector mesh.** The torso is a chain of sculpted masses (rump, hip, waist, ribs, chest, withers, neck) bound to the spine
  and neck bones; legs and tail are tapered masses on their bones; one contour wraps them.
- **Smart-Bone corrective actions** (table in `proof/corrections.json`, version rig-v3): *neck-turn* (head yaw relative to the
  body, 25-120°: shoulder bulge toward the turn, neck shortens 12% so the jaw clears the shoulder, a skin-fold stroke, ears
  swing back), *spine-curl* (crouch: back arches, belly tucks, rump drops), *leg-fold-hind* (stifle angle 100-40°: the haunch
  grows round), *leg-fold-fore* (elbow angle 120-60°: elbow nub, chest lowers between the forearms), *head-down* (neck pitch:
  nape crest and neck base thicken, throat fold), *jaw-rest* (chin on paws: chin and jowl flatten, lid).
- **Switch layers.** Head: five drawings (profile, three-quarter front, front, three-quarter back, back; the other three of
  eight views are mirrors), chosen by ψh snapped to 45°. Each drawing has its own composition and lines (front: blaze,
  symmetric eyes, mouth "w"; three-quarter back: muzzle behind the skull, cheek edge, ear backs, nape strokes; back: ear backs,
  fur parting). All five are positioned from one head landmark sheet, so heights and joints agree. The body has one switch:
  the chest bib exists only while the chest faces the camera. The body's view is continuous (its bone layout is projected from
  one turnaround sheet by ψb), so it foreshortens rather than pops.

## How it moves (build/perform.js)
The score's x, state and acts drive the controls. Mapping: U = x − 0.42 (U is my porch in metres, outer wall face at 0;
the dog's mid-spine). The gait is a footfall planner: distance along the dog's own forward axis drives each foot's phase;
in stance a foot is world-fixed (measured slip ≤ 1.0 mm), in swing it lifts. Turns: refusal at 3.40-3.64 s, head first
through three-quarter front (3.46) → front (3.50) → three-quarter front (3.54) → profile (3.58); body facing flips at 3.54 (the dog turns its back through the view facing us);
then it crouches, lies down and rests its chin, back to the door. Turn back: rest lifts at 7.40, the head goes over the far
shoulder (three-quarter back 7.54, back 7.58, three-quarter back 7.62, profile toward the door 7.67) while the body is
still lying; the body rises 7.70-8.05 and turns through its back view 8.02-8.55. Approach: head pitched so the skull top is
below the withers in every approach frame. Lying across the sill: chest over the sill board, head and forepaws in the room,
hips and tail on the porch. *Come in* (26.4): the head view turns to three-quarter back at 26.54, the back of the head toward us and
the muzzle into the lit room, level (not lifted); at 28.1 it turns back and settles chin on paws.

The person is staged in the same line: in the doorway calling and reaching, then steps out and sits on a stool beside the
door with the house wall at their back, pushes the door open (it swings back flat to the inner wall), offers a hand low.
Sitting on the porch side keeps the dog's look into the room pointing away from them.

## Sound (build/sound.py)
Synthesized: crickets and air; a formant voice (Come here ×2, It's all right ×2, Come in); paw taps at the gait's
measured touch-downs; thuds when the dog lies down; a door creak and the room's hum after it opens; a sigh when it settles.
Measured (`proof/levels.json`): calls −19.7/−17.9 dB RMS, soft phrases −33.2/−33.9/−31.4 dB: soft is 11.8 dB under the
calls and 15.8 dB over the room tone (−49.7 dB).

## Evidence (labelled)
- **Measured** from the render (`trace.json` summary; a mask pass gives the dog's pixel centroid, the rig gives facing,
  layer and heights): onsets are listed in `trace.json` → `summary.measured_onsets_s`. Back turned in 94/97 refusal frames
  (the first three are the turn itself); head below the back 218/218 approach frames; dog pixels in 768/768 frames
  (min 10,264 px); end: lying, 50% of the dog's pixels left of the outer wall face, nose 0.67 m inside, tail tip 0.85 m out.
- **Numeric rig tests** (`proof/rig_tests.json`): T1 head drawings share skull top, chin, eye/nose and ear-tip heights in all
  eight views (spread 0; this is structural, the views come from one sheet, and it confirms no drawing rescales the head);
  T2 every leg segment equals its sheet length in every frame (max error 7e-16 m; projected in profile frames 1.2e-5 m);
  T3 no elbow/stifle reversal over 768 frames; T4 stance feet slip ≤ 1.0 mm; T5 every frame has a head drawing and the
  layer sequences of both turns and the look-in.
- **Checker**: `tools/paeleo/check_handmade.py` ALL OK (I1-I4), I3 on x_world_measured (the camera zooms after 14.7 s).
- **Looked at** (frames extracted from film.mp4): both turns every second frame, the stills, the look-in, the cards.
- **Not judged by me**: whether it reads as a performance. An independent critic decides.

## What failed and what changed
See `ledger.jsonl` and `proof/failure_atlas.json`. In short: spindly first proportions (head 1.22×, thicker masses); the
front view with a hanging head read as a lump (head held up through the turn); flattened ears drawn edge-on as sticks; the
look-in first pointed at the person's hand and the open door hid the room (person restaged outside, door swung flat);
foot slip and length drift found by tests and removed; the chest bib showing on the back view at 8.27 (made a switch);
the 3.6 s still caught the front-view drawing (refusal turn tightened to six frames).

## Still weak / not done
- The body has no separate front/back drawings: at front-on it is a short column with bunched legs for two frames.
- Head drawings are switched on 45° snaps with no in-betweens; the turns are drawings on ones/twos, deliberately.
- The person is simple and does not walk convincingly when stepping out (0.8 s).
- Not Moho itself: a Moho-style rig in JavaScript (no .moho project file). No mobile operator page. No independent critic
  was run by me. No kit footage, masks or Quick, Draw! drawings were used.
- Rebuild: `build/make.sh` (render, trace, tests, sound, cards, encode, stills, check; frames deleted after encoding).

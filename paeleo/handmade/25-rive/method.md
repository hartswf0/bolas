# SCION 25 · Rive: the threshold as an interactive puppet state machine

## The swarm, honestly

One agent did all of this alone, with the roles merged: interaction dramaturg, state machine architect, animator, UI and input integrator, and event tester. No other agent ran. **No independent critic has seen the film.** The SCION prompt asks for a separate player-experience critic. That critic has not run yet, and nothing here is approved.

## Thesis

A dog that cannot be ordered. The viewer can read every decision from the body: the turned back, the head coming round before the body does, the low head on the approach, and the look into the lit room before it settles where it is. The commands push it away; the changed circumstances earn it. The result would be bland if the dog behaved like a menu: states snapping from one to the next, a turn played as a mirror flip, labels doing the acting. The one passage everything depends on is 7.46 s. The head leads, over the camera-side shoulder, while the body still lies with its back to the door. Only then does the body follow.

## Native formal language: built here, because the Rive runtime is not available

`build/rive.js` is a small runtime with Rive's primitives:

- **Artboard** (`build/puppet.json`). It holds the bones in a body frame (f forward, y up, l lateral, in metres) and the shapes bound to them: the torso as a union of two capsules (chest–waist and waist–rump; the waist sits higher, which gives the tuck-up), the neck, skull, muzzle and mask, nose, eyes, ears as curved triangles, the tail as a five-segment tapered chain, and four legs. The coat pattern (tan body, dark saddle, pale chest) is shapes clipped to the torso.
- **Keyed clips.** Single-key poses (stand, crouch, lie, rest, lookIn, head and tail poses) and looping keyed clips (breath, wag). They are combined by **1D blend states** on number inputs and by additive layers.
- **Typed inputs.** Number inputs: mood, speed, crouch, lie, rest, head, ear, tail, wag, look. Triggers: heard, call. Boolean: doorOpen.
- **State machine.** Three layers. Each layer checks its transitions in **explicit priority order**; the first one whose conditions all hold wins, and there are no self-transitions.
  - **Facing**: FacePerson → TurningAway → BackTurned → HeadLeads → TurningBack → FacePerson. This is the only layer allowed to rotate the body. Both turns go through the dog's front (the face toward the camera), never through an edge-on flip.
  - **Body**: Stand, Walk, Backing and Down, driven by speed and lie.
  - **Attention**: Alert, Rest and LookIn. LookIn has priority over Rest, and Rest over Alert.
- **IK constraints.** The legs are two-bone IK in 3D with poles: the elbow points back, the stifle points forward, and the pastern and hock lie flat when the dog is down.
- **A stepping solver.** Each foot stays planted in the world until its home under the body moves past a threshold. It then swings to a new spot; at most two feet are in the air, and pairs are coordinated. A landing fires a `footfall` event. When the dog lies down, the paws fold toward the authored lying pose.
- **Deterministic event trace.** Every transition, footfall and world change is an event with a time (`events.jsonl`). The sound is synthesized from those events.

**What decides and what acts.** The PAELEO score decides, and `build/drive.js` sets its values as inputs each frame, the way a Rive host app does. The puppet's own state machine decides *how* each decision is performed. It adds behaviour the score does not contain:

- The turn away starts at the state change (3.417 s) and finishes by 3.84 s. The score's own `turn` value would only cross over at about 4.1 s.
- The head leads at 7.458 s, before the body has risen.
- The body turns back only once lie < 0.12, so the dog never rotates while it is still lying down.

**The world.** Metres under a fixed oblique camera: screen x = 355 + 210·(X + 0.28·Z), screen y = 598 − 210·Y + 63·Z. The house is drawn in section: the dollhouse cut runs through the near edge of the doorway. The interior is warm and lamp-lit, with a door leaf hinged on the inner face, a sill stone and a lintel. Light from the doorway falls on the porch as a pool. While the person stands in the doorway, their body blocks it and throws a shadow toward the dog. Once they step aside, sit down and push the door open, the light comes out and the dog throws a long shadow away from the door. The person is a second, simpler puppet: a 2D profile with two-bone IK arms and legs. It cups a hand to its mouth to call, reaches for the dog, sits on a stool, pushes the door wide, offers a low hand and tilts its head for the soft voice.

**Mapping of space.** The score's x (the centre of the dog's body) is placed in the world at X = x − 0.24 m. The door's outer face is at X = 0.25 and its inner face at X = −0.25. At the end the dog's front paws are at X = −0.196, inside the frame, and its tail tip is at 0.965, out on the porch. The camera never moves, so x_screen = 355 + 210·(x − 0.24). The approach covers the score's distance at the score's pace: 209.4 screen px per score metre, measured.

## Materials

Everything the viewer sees or hears was drawn or synthesized in this folder. The archive dog (*Amateur Film New Jersey C*, Internet Archive, public domain) was **studied**. I read the numbers of its rig keys to set the proportions, and I looked at four of its frames for the coat pattern. None of its pixels, masks or outlines are in the film. Quick, Draw!, archive-door and the found frames are not used. See `assets.json`.

## Protected conditions (numeric) and the result

All measured on the render. For the choice onsets, "measured" means from the rendered dog layer or from the pose that was drawn; how each onset is detected is in `build/finalize.py`.

| check | measured |
|---|---|
| retreat 1.00 | 1.042 s: the dog layer starts moving away |
| watch 2.33 | 2.417 s: smoothed layer speed under 60 % of its retreat mean |
| refuse 3.42 | 3.458 s: the drawn head yaw leaves 180°; the back is shown (muzzle right of the body) from 3.625 s |
| watch 7.46 | 7.500 s: the nose moves; the head's world yaw passes 120° toward the door at 7.708 s |
| approach 14.71 | 14.708 s |
| lie down 23.79 | 23.875 s: the top of the dog layer sinks |
| looks in 26.4 | 26.500 s: the muzzle tip is more than 3 cm deeper into the room than the skull; settles at 28.167 s |
| refusal frames with the back turned | 94.8 %; every frame from 3.9 s to 7.458 s |
| approach frames with the skull top below the back line | 100 % (from 15.2 s) |
| planted-foot slide | 0.0 m (maximum frame-to-frame displacement of any planted foot) |
| furthest the dog ever reaches into the house | X = −0.249 (the inner face is −0.25) |
| soft voice vs calls | 15.5 dB quieter; 12.7 dB above room tone (RMS over the 50 ms windows where each sounds) |
| state graph | no dead-end states (every state has an outgoing transition) |
| `tools/paeleo/check_handmade.py` | ALL OK (I1–I4) |
| film | 912 frames, 38.0 s, 1280×720, H.264 + AAC, 2.7 MB |

**Mobile test.** `build/test_page.js` opens the operator page at iPhone 13 size in headless Chromium:

- tap to first advance takes 0.45–1.2 s;
- the scene clock keeps time (73–83 frames in 2.5 s), with pictures dropped under software rendering at about 55–80 ms per frame;
- the dog's hit area answers a touch;
- the layer states survive a change of view (another camera on the same rig);
- there is no horizontal scroll.

This ran on a headless browser, not on a real phone.

**Judged only by viewing (not by me):** whether the refusal and the coming read as a dog's own choices rather than obedience to a timeline.

## What I looked at

- Contact sheets and dog crops of the retreat, both turns, the head lead, the approach, the lie-down, the look-in and the end.
- The four stills, the title and end cards, and a whole-film sheet at 1.5 s intervals.
- The operator page on a phone-sized viewport.

## What failed and what I changed

The full record is in `ledger.jsonl`.

- **The neck.** It was too long: a giraffe when alert. I shortened it.
- **Chin on the paws.** The neck folded straight down, leaving a hood of ears. I clamped it.
- **The head lead.** It first showed the face to the camera instead of looking back over the shoulder. I fixed the angle and carried the head over the near shoulder.
- **The second turn.** Its end-on frames tangled because the feet were left behind. The feet now step faster while turning; this is improved, not solved.
- **The backing gait.** The hind feet trailed behind the rump; I shortened the gait lead.
- **Light.** The dog washed out in the warm light; I gave it a thin contour.
- **File size.** The film was 59.7 MB because of moving grain; it is now 2.7 MB.
- **The lying paws.** They reached 3 cm into the room; I moved the mapping out.
- **The page.** At first it fell behind the clock on a slow device.
- **The end card.** It said "nothing slides". The paws do move along the floor as the dog folds down, so the card now says "a planted foot never slides (measured)".

## Still weak

- **The end-on frames of the turns** (about 3.6–3.7 s and 8.3 s) are compact and busy: legs overlap, and the head sits low against the chest. They read as a dog turning, but they are the least clear frames.
- **The person** is a simple flat profile. They "step aside" by backing into the room without turning, and nothing causes the door to open except their arm.
- **The house section** (the cut faces, the lintel block, the big pale far reveal) is legible but plain.
- **The look-in** depends on reading depth from the back of the skull and the ears; at full size it reads, but small it may look like "head up".
- **The dog is small** in frame (about 130 px tall standing) because the fixed camera has to hold both the room and the far end of the porch.

## Not done

- **No sound was heard.** Levels were measured, but I cannot listen. Whether the formant-synthesized voices sound like speech, rather than tones with consonant noises, is unknown.
- **No interactive dramaturgy beyond the score.** The page replays the score live through the puppet; the viewer cannot change the circumstances. A player cannot call or sit, so the theorem's "permit meaningful refusal" is shown, not played.
- **No real Rive file or runtime** was used, and no `.riv` was exported.
- **No branch forks or competing hypotheses** were tried.
- **No real device** was used for the touch test.
- **No independent critic** has watched the film.

## Rebuild

`sh paeleo/handmade/25-rive/build/make.sh` runs everything in order:

1. the event test;
2. the render (Playwright canvas into ffmpeg);
3. the sound synthesis from the event trace;
4. the mux;
5. `trace.json` and the acceptance tests;
6. the state-graph SVG;
7. the stills;
8. the mobile page test;
9. the checker.

Intermediates go in `build/cache/`.

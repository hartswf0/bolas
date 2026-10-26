# SCION 16 · JibJab — Recastable Performance Studio · the threshold, handmade

## Thesis

One directed performance that accepts any cast without being performed again. The dog's choices live in the **performance**
(a body plate and a head track solved from the PAELEO score); who the dog *is* lives in a **face slot**. The film is cut with
a cut-paper head; `proof/comparison.mp4` plays the identical performance with a stranger's Quick, Draw! dog and with the
home-movie dog's own face, plus the bare plate with its empty slot. What would make it bland: a head pasted on a puppet that
moves like a screensaver; a recast that changes the acting.

## Swarm (one agent, roles merged)

I worked alone; the six roles of the prompt were merged because each one's output is the next one's input, in one file each.
No agent runs are claimed beyond that.

| role | artifact it built |
|---|---|
| performance director | `build/perform.py` → `performance.json` (channels, timing leads: the head leads the turn back at 7.46, comes low from the first step at 14.71) |
| plate choreographer | the body plate: 3D anchors (spine circles, four two-segment legs, tail chain, neck), the stepping solver, the lying substitution |
| face-fitting specialist | `build/prep.py` → `cast/*/` views with socket and nose landmarks, ear slots, `cast/manifest.json` |
| mask/occlusion compositor | `build/scene.js`: body layer and head layer composited by depth (the head goes under the body when it faces away), the collar as neck matte, door clipped to the opening; `matte-manifest.json` |
| audio editor | `build/sound.py` → synthesized voice, paws from the solver's contacts, tag, door, room; `sound-levels.json` |
| blind recast critic | **not done by me.** The independent critic is the reviewer who receives this film. |

## Native formal language, as used

- **Body plate**: a cut-out dog body (circles swept along a spine, capsule legs, tail chain), placed by world anchors (x along
  the porch in score metres, d into the screen, y up), drawn as flat cards in an oblique view, furred by multiplying in a tile
  of the archive dog's own coat (Amateur Film New Jersey C f008, public domain). It is the same in every casting.
- **Face slot**: a card placed by landmark alignment — its `socket` sits on the collar point; it is rotated by the head
  track's pitch and chosen by its yaw among five views (L, BL, B and their mirrors R, BR). Each cast supplies L, BL, B.
- **Hair/neck matte**: the collar (dark leather with a tag) is drawn over the seam between plate and slot; the ears are a
  separate slot, rotated by the score's `ear` channel, where the cast provides them (paper: yes; doodle: the profile's own ear
  stroke; home movie: no). The person's face slot has a hair matte behind and in front of a Quick, Draw! face.
- **Cast manifest**: `cast/manifest.json`: per cast, its views, landmarks, ear angles, source and rights, likeness note.
- **Tracking curves**: `performance.json` frames: x, d, body yaw, head yaw, neck angle, head pitch, lie, crouch, rest, look,
  ear, tail, wag; `build/cache/skeleton.json`: per-frame anchors.
- **Timecoded occlusion and contact**: `matte-manifest.json`: spans of slot view and head-under-body order; 93 paw contacts
  (the frames where a foot lands; a planted foot never moves until it lifts).
- **Time base**: 24 fps, scene frame i = 0…767, placed after a 72-frame title; film 912 frames, 38.0 s.

## How the dog is built and moved

- **Walk and retreat**: the stepping solver keeps every foot planted in world space until it is too far from where its
  socket will be 1/6 s later; then it swings (lift 6 cm) and lands there. At most two feet swing (three in a turn), never both of
  a pair while walking. The retreat backs away still facing the person (the score's intention), crouched, head low, tail tucked.
- **Turns** (3.42 s away, 7.46 s back) are rotations of the plate's anchors, not mirrors: the body passes rump-to-camera at
  about 3.9 s, the head card swaps L → BL → B → BR. Turning back, the head leads (7.46–7.95 s) and the body follows (7.72–8.55 s).
  A neck pointing away from the camera is foreshortened so the head sits on the shoulders (no "giraffe").
- **Refusal**: it lies down with its back to the door and the person, body yaw 40° (facing right and away), head resting.
- **Coming, head low**: the neck angle follows the score's `head`; on approach the head is pulled down within 0.22 s of the
  first step and stays below the line of the back.
- **Lying across the sill**: the body lowers, forepaws slide forward, the hind legs are substituted by folded haunches; body
  yaw 148° so the front half and head are inside the door frame (head past the wall plane), hindquarters and tail outside.
- **Looking in (26.4 s)**: the head turns from the person (L) to the back of the head (B) into the lit room, then settles back.
- **Position**: screen x = 290 + 205·x_score (px); the depth path takes the dog diagonally toward the sill over the last 1.5 m
  (it changes screen y only). The camera does not move.

## The world

A clapboard house front at dusk, the door from *Straight Talk* (NTIS, public domain; frame f028, the empty door, rectified)
hinged on the right jamb and swung by an affine transform, clipped to the opening; a warm room behind it; the light spill on the
boards; the garden and back railing against a dusk sky; a Quick, Draw! moon. The person is a cut-paper body plate with a
Quick, Draw! face (key_id 4675852618956800) as its face slot: calls with a cupped hand and a lean, reaches, steps aside and
sits, pushes the door open (6.2 s), offers a hand low. Spoken lines are shown as captions (bold for calls, small italic for the
soft voice). The dog's state and the choice names are never printed.

## Sound

All synthesized (`build/sound.py`): a three-formant voice for "Come here." (calls), "It's all right." and "Come in." (soft,
breathy); paws from the 93 solver contacts; the collar tag on the turns and the start of the approach; thumps when it lies;
sighs; a latch and creak when the door opens and a warm room hum that rises after it; crickets in the garden; a few plucked notes
at the approach, the lie and the settle. **I cannot listen**; what is known is measured.

## Protected invariants and what was measured

Measured from the render (mattes read back from the canvas every frame, `build/measure.py` → `trace.json`). The trace's `state`
is segmented at onsets detected in these measurements, not copied from the score.

| choice | score t | measured onset | signal |
|---|---|---|---|
| retreat | 1.000 | 1.042 | torso matte moves right |
| watch | 2.333 | 2.375 | head matte rises out of the crouch |
| refuse | 3.417 | 3.417 | head matte drops / swings away |
| watch (turns back) | 7.458 | 7.583 | head matte swings back toward the door |
| approach | 14.708 | 14.708 | torso matte moves left |
| lie down | 23.792 | 23.875 | torso matte drops |
| looks in | 26.4 | 26.417 | head matte rises and turns; view becomes back of head |

(Current build, r8; `trace.json` → `summary.onsets`.)
Also measured: head below the line of the back on 99% of approach frames; facing away on 89% of refusal frames (the first
0.3 s is the turn itself); the end matte spans x 272–512 px against door jambs at 196–384 px (112 px inside the frame, 128 px
outside); x_screen correlation with the score's x r = 1.00. `check_handmade.py`: ALL OK. Sound (`sound-levels.json`): calls
≈9 dB louder than the soft lines; the quietest soft line ≈8 dB above the bed (window RMS).

**Viewed by me (not a verdict)**: extracted frames of every choice from `film.mp4` and turn sequences at 0.1 s.
**Not judged by anyone yet**: whether the choices read as choices at normal speed; whether the acting survives every recast.

## What failed and what changed

See `ledger.jsonl`. In short: a sausage-shaped body and joint seams (re-proportioned, union outlines); the collar reading as a
tongue (moved under the head, darkened); a giraffe neck at 7.9–8.1 s (less oblique, foreshortened neck); feet lagging in the
turn (predictive landing); a grasshopper knee when lying (forward-down bend, then a haunch substitution); doodle heads floating
off the collar (face fitting on the drawing's own neck point); late measured onsets for lying and looking in (detectors moved to
the torso and head mattes); head not low at the start of the approach (head pulled low within 0.22 s); the turn barely begun
at 3.6 s (faster ease).

## Still weak

- The lying body is a pile of capsules; it reads as lying, not as a soft relaxed animal.
- The home-movie cast: the archive has no legible profile or back of its head, so its profile slot is a mirrored 3/4 face
  looking at the camera, and its back views are its fur in a drawn silhouette. The doodle BL view is a join of two strangers'
  drawings and looks it. These are face-view authoring limits, recorded rather than hidden.
- Rear view during the turns is narrow; the tail is hard to see there.
- The synthesized voice is crude formant speech; intelligibility is unknown.
- The dog is small in frame (about 200 px long) because the fixed camera holds the porch from door to x = 4 m.

## What I did not do

No independent critic; no human viewing; no listening. No hat exchange (the SCION's own proof scene is replaced by the brief's).
No real person's face; the *Straight Talk* woman is not used (f028 has only the door). No web images, no generated images.
No git. Nothing written outside this folder.

---

# Round 2 (after reviews/round1.md: DOES NOT PASS, narrowly)

## What changed

1. **The dog is now made of the archive dog.** The body plate is no longer drawn capsules with a coat tile. It is cut from the
   footage itself (`build/plate.py`): torso, neck, foreleg upper and lower, two hind legs from f008 (profile, walking left), the
   tail from f006, each a SAM-mask cut intersected with a piece polygon, graded to one duotone with the film's own grain left in.
   The pieces are re-posed on the same performance by two-point affine maps (shoulder→hip, base→collar, socket→knee→foot); the
   stepping solver still plants every foot. No drawn outline remains on the dog's body.
2. **The turns are the dog's own turn.** In the footage the dog turns from facing left, through the camera, to facing right
   (f016–f044). Those eight frames, cut out and placed by their pose keys (feet on the root, head disc at the face slot), are
   the turns, re-timed: 3.44–3.88 s away (facing away by 3.9 s), 7.76–8.40 s back. Their heads are matted out and filled from the
   coat; the face slot sits where the head was.
3. **Turning to look:** the head now leads hard: from 7.46 s it swings over its shoulder (F view, face to us at ~7.58) and is in L,
   muzzle at the door, by 7.70 s while the body is still lying facing away; the body follows on the plates.
4. **Lying:** the body plate lowers to 0.12 m with both sockets level (the hip cannot rise above the shoulder), flattens 16%,
   the hind legs go behind the torso, the forelegs forward along the boards, the tail lies along the boards.
5. **The face slot** gains F and FL views in every cast. The drawn casts (paper, doodle) are graded into the plate's duotone
   with grain; the doodle stickers are toned from white to the plate's paper colour. The home-movie cast is rebuilt in five
   views at the plate's scale (f008, f038, f028, and a B made from the f028 head with its face filled from its own crown).
6. HEADSCALE 1.42 → 1.15 (the caricature head is smaller on a real body); the collar is the dog's own pale collar colour.

## Why the main cast is still the paper head (option a, not b)

I looked at every head of the archive dog at film size (f004, f008, f044–f047): profile and head-down heads are 30–40 px of
blur that do not read as a face. A photographic main cast would have made the choices (head low, looking in) unreadable. So
the film follows repair option (a): the body plate is the archive dog; the head is the paper slot graded into it. The
home-movie head is in `proof/comparison.mp4`, honestly weak.

## Measured (round 2 build)

Onsets measured from the render: retreat 1.000 (score 1.000), watch 2.375 (2.333), refuse 3.417 (3.417), turns back 7.542
(7.458), approach 14.708 (14.708), lie down 23.875 (23.792), looks in 26.375 (26.4). Head below the back on 100% of approach
frames; facing away on 95% of refusal frames; end matte x 292–512 px against jambs 196–384 (92 px in, 128 px out); I3 r = 1.00.
`check_handmade.py`: ALL OK. Film 912 frames, 38.0 s, 3.7 MB. Sound re-synthesized from the new contacts (89): calls 9.4 dB over
the soft lines, the quietest soft line 8.5 dB over the bed.

## Looked at (by me; not a verdict)

Frames from `film.mp4` at 3.5–3.9, 4.5, 7.5–8.3, 9, 19, 23.80–24.20, 26.6–31.5; the comparison reel at 3, 7.7 and 27 s; the four
stills; the end card.

## Still weak after round 2

- The body is photographic but the head is a graded paper card: the dog reads as a real dog wearing a cartoon head (that is
  the JibJab image), not as a seamless dog.
- Rig pieces are cut from one blurry 384×288 frame; the forelegs are thin and pale and read as sticks when lying.
- The turn plates are standing frames: the turn-back starts while the score's dog is still rising (a small pop at 7.76 s).
- Lying is a composed pose (no lying dog exists in the footage).
- The home-movie cast's profile and back are barely legible; the doodle cast's 3/4 views reuse the front drawing.
- I cannot listen.

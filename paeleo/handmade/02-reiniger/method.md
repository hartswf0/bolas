# SCION-02 · Lotte Reiniger · the threshold as a shadow theatre

`film.mp4`: 38 s, 1280×720, 24 fps, H.264 + AAC (3 s title, the 32 s scene aligned to the score frame for frame, 3 s card saying what it is made of).

## Thesis

Emotional action made legible through contour alone. No faces, no textures that carry acting. The ears, the tail and the line of the back do the performing. The dog's refusal is the whole silhouette turning away. Its consent is an outline lying across the door frame. A bland version would be a generic tweened dog sliding along a floor. Ours has its paws planted, so every step is a contact.

## Native formal language, as typed primitives (`build/theatre.py`)

- **Backlit shapes, planes and densities.** The screen is a light field: the dusk wash, the doorway interior, the window, the door glow, the porch wedge, the lantern, the moon and the stars. Every plane multiplies it by its transmission, `1 − density·mask`. The far hills are tissue at 0.22, the garden trees 0.42, the facade card 0.66, the lace curtain 0.6, the door leaf 0.80 and the black card 0.975. Holes cut in card (lace, eyes, lattice, the curtain) let the lamp through.
- **Pieces and pins.** Every piece is a polygon in its own frame, in metres, rotated about a pin. The dog has 23 pieces on 22 pins. The two body pieces end in arcs centred on the spine pin (a round lap joint), so the back line stays continuous at any hinge angle.
- **Joint-angle limits.** Front elbows bend back and hind stifles bend forward (the IK bend sign). Elbow and stifle angles are checked every frame and violations are logged. There were 0 in the final render.
- **Contact planes.** `ground(x)` is the porch floor at 0 plus the sill stone, 4.5 cm high across the opening. `DogRig.step` is a paw-contact solver. A paw in stance keeps its world position. A paw in swing travels on an arc to a touchdown placed in the direction of motion, so the retreat (backwards) and the approach (forwards) both plant. Gait phase comes from the score's `walk_phase` (11.4 rad/m measured), with stance at 64 % and a lateral-sequence walk. When the dog lies over the sill, the forequarters tilt up by the sill's height.
- **Replacement profiles.** A turn is a flat puppet rotating on its rod: profile foreshortened by `|turn|` (minimum 0.4), then near edge-on a replacement front-view body. There are four heads: the profile; the same piece flipped on its pin (looking back over the shoulder); an end-on head facing the viewer (the averted face, ears flattening outward with the score's `ear`); and an end-on head from behind (looking in through the door). The person has three hands (pointing, open grasp, palm-up offer), each with its own thumb lobe, plus an open-mouth head.
- **Exposure sheet.** `exposure-sheet.csv` records, per scene frame: the head and body replacements, spine height, the fore/hind/neck/head/ear/tail angles, the four paws (x, y, stance), the person's hand, mouth, skirt, lean and arm, and the door leaf.

## How the dog is built and moved

Its proportions were measured, not traced, from the archive pose keys of *Amateur Film New Jersey C*. Frame 8, a clean profile, gives chest to tail-root 110 px, chest 64 px, neck 89 px and nose 109 px, scaled to 0.80 m of body. Frames 19–23 give the head-low range. The SAM masks were looked at in `study/` and are too blobby to cut from. The puppet was then cut by hand-placed control points.

Every channel is driven by the score: `x`, `turn`, `crouch`, `lie`, `ear`, `tail`, `wag`, `head`, `rest`, `look`, `walk_phase` and `moving`. The screen mapping is `X = 352 + 175·x`, the same pace and distance as the score. The measured approach is 3.401 m against the score's 3.41 m. The measured retreat is 0.972 m against 0.999 m, going the other way.

Acting rules added on top of the score, as an operation, without changing any timing:

1. **The head leads every turn.** At 3.417 s the head swaps to the end-on face turned toward us, low with ears flat. That is the visible start of the refusal, before the score's body turn at 3.9 s. At 7.458 s, lying with its back to the door, the head swings back over the withers to look at the light. Only then does the body rise and turn.
2. **Both turns pass through the front-view replacement**, which is consistent with the head turning toward the viewer first.
3. **"Looks in" is the head from behind:** raised, both ears up, the muzzle gone into the house. "Stays" is chin on paws, still lying across the frame.

## The person, the door, the place

The person is a profile silhouette in a long dress with a lace hem. Her bun and clip were drawn after the woman in the *Straight Talk* frames. She calls by pointing at the floor in front of her, and reaches by lunging so the open hand clears the door casing into the air. Then she steps aside and kneels on her heels beside the door, and offers the hand palm-up, low, beyond her knees.

The door leaf is tissue, hinged on the right jamb, ajar at 0.45 of the opening. It opens on the *Straight Talk* swing: the leaf-mask widths of frames 31→18, reversed and held two scene frames per archive frame from 6.2 s. Light then floods the arch, the screen and a wedge across the porch.

The dusk deepens over the 32 s and stars come out. The spoken lines are lamp-lit lettering in the porch plaque: commands in upright type, soft words in italic. The camera is locked, like a rostrum over the glass table.

## Sound

The sound is synthesized in numpy (`build/sound.py`). Voices are instruments: a muted horn for the calls, harder and with a clashing organ stab at the reach; a flute for "it's all right" and the rising "come in"; a clarinet for the dog's question at the turn back and its theme on the approach. Each paw touchdown from the contact solver is a pizzicato pluck, panned to the dog's screen x: descending while it backs away, rising through D major pentatonic as it comes. Low strings sigh a semitone down at the refusal and a soft drum marks the turn. The door is a harp glissando on the archive swing, then a warm organ. There is a harp roll and a sigh when it lies down, a suspended bell chord and soft tail brushes while it looks in, and an open D chord that stays. Crickets and air run throughout.

## What is protected (invariants)

These are measured from the render (`build/check.py` reads the rendered dog mask and separately rendered muzzle and cranium masks), in `build/out/invariants.json` and `trace.json`.

| choice | score t | measured t | how measured |
|---|---|---|---|
| retreat | 1.000 | 1.000 | silhouette centroid starts moving away (> 0.5 px/frame) |
| retreat → watch | 2.333 | 2.333 | silhouette top lifts out of the crouch (≥ 2 px in 2 frames) |
| refuse | 3.417 | 3.542 | muzzle mask stops pointing at the door |
| refuse → watch (turns to look) | 7.458 | 7.625 | muzzle mask points at the door again |
| approach | 14.708 | 14.708 | centroid moves toward the door |
| lie down | 23.792 | 23.792 | silhouette height drops > 3 cm |
| come in → looks in | 26.4 | 26.583 | muzzle disappears (head into the house); settles back to profile at 28.08 |

- **Never enters.** The silhouette's left extent never passes −0.126 m. The inner jamb is at −0.46.
- **Ends across the threshold.** The last frame spans −0.126 to 1.411 m across the outer jamb at 0.46: paws and head in the door frame, hindquarters on the porch.
- **Commands before refusals, circumstances before the approach.** The call is at 1.0 and the retreat starts at 1.0. The reach is at 3.4 and the refusal follows. She kneels by 5.96, the door is open by 7.13 (opening from 6.2), the hand is low by 7.0 and the soft voice comes at 7.42, all before the approach at 14.71. These are structural: read from the puppet state that drew the frame.
- **Position.** The silhouette centroid stays within 0.075 m of the score x, which includes the shape offset of head, tail and lying.
- **Viewed, not measured.** Every frame was rendered with 0 joint-limit violations. In the silhouette-only test (`study/silhouette-read-test.png`: pixels darker than 24/255 black, everything else white), every relationship still reads in my viewing.

## What I looked at

- Contact sheets of the archive.
- A dog design sheet across 12 poses.
- Preview frames.
- Frame strips from the encoded film: retreat, walk, refusal 3.33–4.58 s and return 7.33–8.67 s.
- Four sheets of six frames (24 frames) across the scene, the four stills, and the title and end cards.

## What failed, and what I changed

The full list is in `ledger.jsonl`:

- The lace border erased the porch.
- The elbows bent the wrong way.
- The first dog was a barrel-chested jackal.
- The person turned into a man in trousers while sitting, and the bench hid the offered hand. She now kneels.
- The back had a bump at the spine pin, fixed with the round lap joint.
- Three tries at the refusal head: over the shoulder read as a blob, from behind read as headless, and the face toward us was kept.
- The grasping hand merged with the door casing, so the reach became a lunge.
- Card lettering was dim and misplaced.
- A stab set the sound level.
- Squashed mid-turn profiles looked like an ostrich.

## What I did not do; what is unknown

- **No independent critic was run.** I had no means here to spawn one, and my own checks are not approval. The brief's critic will judge.
- **I could not listen to the sound.** It is checked only structurally (cue sheet, events, levels per 2 s: RMS about 0.07–0.21 in the scene and quieter on the end card, peak ≤ 0.92).
- I did not view the 4 s archive excerpt at normal speed.
- I did not watch the film at normal speed in a player. I watched extracted frames and strips only, so the rhythm at 24 fps is judged from frames, not playback.
- **Weak spots I can see:**
  - The front-view replacement during the turn back, at about 8.1–8.2 s, is a little cat-like.
  - The 1–2 foreshortened frames at each turn are crude.
  - The dog is small in a locked wide shot, about 170 px long.
- No Quick, Draw! or found-frames material was used.
- No mobile operator page was made (it is not in the brief's deliverables).

## Rebuild

`build/make.sh`: `stage.py` → `rig.py` → `render.py` (about 5.5 min on 4 cores) → `sound.py` → ffmpeg mux → `check.py stills`.

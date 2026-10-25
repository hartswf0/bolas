# PAE-02 · SCION 50 · Library of Congress, Historical Print Stage

The film is **Pl. I, The Threshold**, an engraved motion study. The scene is one plate: a sectional elevation of a house wall,
its doorway and a porch at dusk. It is line-engraved and hand-coloured, and under the image is the key a print room would
print. The dog is engraved after frames of a public-domain home movie. Wherever the scan cannot support a gesture, the plate
says so and marks the gesture as invented.

## Studio and swarm (what actually ran)

One agent did all of this work, playing the roles the prompt names, in turns. No other agents were run.

| role | artifact it built or checked |
|---|---|
| collection navigator | read the kit's rights records; picked dog f006 (a clean left profile) and f030–f044 (the dog's own turn; f016, f017, f026, f028 tried and dropped in round 2), door f030, *The Door to Heaven* hand f000, and the stone pillar in dog f000 |
| historical metadata critic | `assets.json`: one entry per visible piece, each with its item URL, clip id, rights, scan crop, illustration type, and what is documented vs inferred |
| visual forager | `proof/source_sheet.jpg`: each scan beside what was engraved from it |
| rigging researcher | `build/rig.py`, `build/dogpose.py`: f006 traced into 11 cut pieces, forward kinematics, two-bone IK with pinned stance feet |
| documentary ethics reviewer | the margin key, the cards and this file. The title card first claimed "every movement is invented", which was false: the two turns are documented frames. It was corrected |
| independent scene reviewer | **not me.** I did not approve the film; the verdict belongs to the critic |

The Library of Congress collections were not reachable from here. **No LoC item was used, and none is claimed.** The prompt's
item-level language (item permalink, rights advisory, artist/date, scan crop, illustration type, inferred vs documented tags)
is applied to the kit's rights-recorded Internet Archive / NTIS material.

## Native formal language, as built

- **Item / permalink and rights advisory.** Every plate links to its archive item and rights state, in `assets.json` and on
  screen. The margin key names the film, collection and rights of the dog drawing currently on stage.
- **Scan crop.** The margin shows a toned thumbnail of the scan frame the current drawing is engraved after. It changes frame
  by frame during the turns (f030 … f044) and reads f006 otherwise.
- **Illustration type.** Three types appear: "engraving after a photograph" (dog, door, hand, stone), "drawn" (person, room,
  porch, sky) and "designed analog" (the back of the dog's head).
- **Inferred vs documented, made visible without labels doing the acting.** When the dog is a documented frame (the two
  turns), it is shown as photographed: its outline comes from the frame's mask and there are no pins. When it is re-posed from
  cut pieces (invented motion), small **red brads** sit at its joints, and the key's second line turns red: "frame 006 cut
  into 11 pieces and re-posed: invented motion". The dog's state and the choice names never appear on screen.
- **Typed, versioned state.** The plates are built from the kit by scripts. All coordinates are in scan pixels, mapped to
  the screen by K = 1.44 px per scan px and 190 px/m. The time base is the score's 24 fps frame index, and the camera is
  static.

**Numerical invariant** (measured, `trace.json` and `invariants.json`): the six choices, measured from the dog layer of the
render, fall within ±0.25 s of the score. Also measured: stance feet do not slide (`proof/feet.json`).
**Artistic achievement judged only by viewing**: whether a blurred 1930s-style home-movie dog, engraved and cut, can act
refusal and trust.

## How the dog is made and moved

- **Material.** *Amateur Film New Jersey C*, f006: the dog in left profile, about 130 scan px long. I traced its contour by
  hand over a 4× gridded enlargement into 7 parts (head with neck, torso, tail, and four legs). I then split each leg at its
  joint, giving 11 pieces. Each piece is printed with a line screen whose line width follows the scan's own luminance
  (contrast-stretched), with lines that bend over the form and a cross-hatch in the darks. The head piece is cut out by a thin
  white line of paper, as a wood engraver parts overlapping forms. The eye, nostril, mouth line and ear fold are drawn,
  because the scan is unreadable at that size; they are recorded as inferred.
- **Moving it.** Each piece is rotated about a hand-placed joint. The legs are solved by two-bone IK in a lateral-sequence
  walk (duty 0.62, stride 0.46 m) driven by the distance the score's x travels. Stance feet are pinned in world space, so
  feet account for the travel: the solved stance feet move 0.38 px/frame at most and 0.01 px/frame on average. Crouch, tail,
  lying, head height, resting and looking come from the score's `act` channels, mapped to angles. Breathing and a slow idle
  head move only during holds.
- **The turns are substitution, not mirroring.** The refusal (3.46–3.96 s) shows 7 whole documented frames of the film's own
  turn: f030 ×4, f033 ×2, f036, f038, f040, f043, f044 ×2. They run from facing the camera (head visible) to right profile,
  re-timed and engraved through the same screen at render time, at the neighbouring cut-piece dog's height, centroid and mean
  tone (round 2). Every frame of the turn is a
  photographed dog, never a squashed one. The dog then becomes the cut-piece dog as a **reversed impression** (a mirrored
  print, a historical reproduction fact), so its back is turned by 3.96 s. It lies down facing away with its chin on its paws.
- **Turning to look (7.458 s, on the frame).** The head piece is substituted: the unmirrored left-facing head is pinned to the
  reversed body's neck, so the head comes round over the shoulder to the door while the body still lies turned away. The body
  then rises (7.5–8.0). It turns back through two documented frames in reverse (f033, f030, 8.04–8.62 s) and stands facing
  the door.
- **Coming, head low.** The head is rotated down about the withers, so the nose sits below the line of the back for the whole
  approach. The walk is slow, crouched a little, with bent joints.
- **Lying across the sill.** No frame of the film shows this dog lying, so the lying is **invented from cut pieces**: the
  torso drops onto the boards, the forelegs reach forward along the sill, and the hind legs fold under. The head, forepaws
  and chest lie inside the door's reveal, in the lamp light. The haunch and tail lie out on the porch. Centre x = 0.59 m.
- **Looking in (26.4 s).** The head lifts off the paws and pushes forward into the doorway. At 26.72 s it is substituted by a
  **designed analog**: the back of the head, ears and nape toward the viewer, turned away from us into the lit room. No
  frame shows it, so it is drawn and toned with the scan's neck tone, and recorded as inferred. At 28.2 s the profile head
  returns and settles onto the paws. The dog stays.

**The person** is drawn: an engraved figure in a long coat. Its hand is engraved after *The Door to Heaven* (1941) f000,
mirrored. In the source that hand holds a card lettered SORROW; the card is cropped away, and the crop is recorded. The
person stands in the doorway and calls with a beckoning arm. On the second call she leans out and reaches. Then she steps
back into the room, sits on a low stool beside the door and offers the hand low into the doorway. The door then swings open
(the Straight Talk leaf, foreshortened by sin of the angle), and lamp light floods the reveal and falls across the porch in a
widening wedge. That light is a hand-coloured wash. At "Come in." she draws her hand back to her lap. Her words are printed
as legends on small paper slips (the typed prompts are not shown).

**Sound** is synthesized in `build/sound.py`; nothing is recorded:
- formant-synthesized calls ("come here", twice each time);
- a breathier soft voice ("it's all right" ×3, "come in");
- dusk air and crickets, and warm room air and a low hum once the door opens;
- a paper riffle at every substitution of the dog's drawing (the turns, the head coming round, the back of the head);
- claws and pads at each footfall the render logged;
- a door creak and knock;
- a body on boards and an exhale when the dog lies down, and a settled sigh at 28.6 s.

## Measured, looked at, unknown

**Measured** (from this render; `trace.json`, `invariants.json`, `sound.json`, `proof/feet.json`):

| choice | score t | measured onset | dt | detector (on the dog layer) |
|---|---|---|---|---|
| retreat | 1.000 | 1.083 | +0.083 | centroid moving away > 0.25 px/frame |
| watch | 2.333 | 2.500 | +0.167 | backing below half its peak speed and the head rising |
| refuse | 3.417 | 3.458 | +0.041 | silhouette changes (documented turn frame on stage) |
| watch (turns to look) | 7.458 | 7.458 | 0.000 | head piece crosses to the door side of the neck joint |
| approach | 14.708 | 14.708 | 0.000 | centroid moving toward the door |
| lie down | 23.792 | 23.792 | 0.000 | centroid sinking > 1 px/frame |
| looks in | 26.4 | 26.417 | +0.017 | head moving forward into the doorway |

- `check_handmade.py`: **ALL OK** for I1, I2, I3 and I4. I2: the minimum x_score is 0.59 and the end is 0.59. I3: r = 1.00 (as
  rounded by the checker) between the measured screen centroid x and the score's x, over 768 frames. I4: 0.979 of the refusal
  frames are measured turned away; the first frames of the turn are still left profile.
- Voice RMS (the voiced samples of the voice stem, at mix gain): calls −9.3 and −8.1 dB. The soft voice is −23.9 dB, which is
  **14.65 dB** below the calls and **15.1 dB** above the room tone (−39.0 dB, 12–14 s).
- `film.mp4`: 1280×720, 24 fps, H.264 + AAC, 912 frames, 38.0 s, about 4.7 MB, faststart.

**Looked at** (frames extracted from `film.mp4` and viewed): every frame of both turns, a consecutive walk and a
consecutive retreat, a sweep every 0.5–1.5 s across the scene, the four stills, and both cards.

**Unknown:**
- **I cannot listen.** Whether the synthesized voice is intelligible as "come here" / "it's all right" is unknown; it is
  likely to sound buzzy and synthetic. The words are also printed as legends.
- Whether the turn frames read as a dog at normal speed. They are blurred home-movie frames, and a couple of the
  facing-camera frames are blob-like.
- Whether the red brads read as "invented" or only as decoration.

## What failed and what I changed

The steps are in `ledger.jsonl`. In short:
- The first head trace was a hammer; I redrew it and drew the features in.
- Head-low at first did not go below the back; I remapped the angles.
- The hand was twice too big.
- The person first sat outside on a bench, and the approaching dog walked through her lap. I moved her inside, beside the
  door, which matches the score's place for her.
- A raised profile head read as looking up or at her, so I added the back-of-head plate.
- f018's mask included its shadow and read as a bear, so I dropped it.
- The documented frames printed darker than the puppet; I lightened them.
- The stance feet slid up to 6.5 px/frame because of a moving-weighted foot target, a crouch offset and IK over-reach. I
  removed both terms, shortened the stride and bent the knees while walking; the slide is now ≤ 0.38 px/frame.
- The title card's claim was false; I corrected it.

## What is still weak

- The facing-camera turn frames (f030–f040) are still soft at this size, though each shows a head and legs; the turn goes
  from left profile straight to facing the camera (the documented left-to-front frames were the lumps and are gone), so it
  is a jump-cut of a turn rather than a sweep. The turn back is two held drawings.
- The cut-piece dog's tail is a rigid plank, and its folded hind legs are a clutter of small shapes when lying.
- The person is a stiff toy-theatre figure; her seated skirt is boxy.
- The person is never shown opening the door: it opens on its own, as in the description's passive voice.
- The fieldstone and the porch are generic.

## What I did not do

- I used no LoC sources.
- I made no Quick, Draw! use.
- I ran no independent critic and approve nothing myself.
- I published no operator page; `index.html` in this folder is a local page only.
- I made no git commits.
- I made no second branch. Fixes converged without two failed repairs of the same defect.

## Rebuild

`build/make.sh` runs everything from the kit and the score: fonts, plates, world, person, render, trace, feet, assets, source
sheet, sound, mux, check and probe. Intermediates go to `build/cache/`.

## Round 2 (after critic round 1: does not pass, narrowly)

Repairs, each against the critic's ranked conditions:

1. **Every turn frame reads as a dog.** The critic named 3.458–3.500 and 8.458–8.541 as headless lumps (f016, f017). I
   dropped them. Looking at every frame again, I also dropped f026 and f028, whose heads are bowed out of sight. The turns stay
   documented: out = f030 ×4, f033 ×2, f036, f038, f040, f043, f044 ×2 (3.458–3.917); back = f033 ×7, f030 ×7 (8.04–8.58).
   The key names each frame shown. I looked at every frame 3.40–3.98 and 8.00–8.71 in `film.mp4`: each shows a head (face or
   ear on the right) and legs. That is perceptual, my own look, not the critic's.
2. **No jump at the swaps.** The turn frames are now engraved at render time at exactly the height and centroid x of the
   cut-piece dog on either side of the turn (interpolated across it), on its ground line. Their tone is normalised to the
   cut-piece dog's mean scan tone, with the same line period, cross-hatch and contour. Measured bbox heights at the swaps (`trace.json`): 189 → 182 px
   at 3.458, 153 → 154 at 3.958, 190 → 184 at 8.04, 190 → 195 at 8.62 (before round 2: 189 → 175, 174 → 154, 190 → 172,
   175 → 195). A residual 3–4 % step remains.
3. **Sound.** Footfalls during 14.7–23.8 are louder and have a board resonance; the minimum is **8.7 dB** over the median
   cricket bed in 60 ms windows (29 footfalls). The door creak is 9.8 dB over the preceding second. A body-on-boards thud and
   exhale now land at 23.85 s, **8.3 dB** over the bed. All of this is in `sound.json`. I still cannot listen.
4. **End card = assets.json.** The dog is after 8 frames (f006, f030, f033, f036, f038, f040, f043, f044). The wall is after
   f000 of the same film, listed separately in both.
5. **Optional, done.** The head piece's paper parting and contour fade out where the neck meets the shoulders. The speech is
   now lettered into the plate (engraved italic with a hairline of paper round it), not white boxes.

Unchanged and kept: the plate key and scan thumbnail, the red pins only on invented motion, the over-the-shoulder look at
7.458, the back-of-head look-in, the sphinx lie. `check_handmade.py`: ALL OK. Onsets: +0.083, +0.167, +0.041, 0, 0, 0
(look-in +0.017). Film: 912 frames, 38.0 s, 4.7 MB.

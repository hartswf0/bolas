# SCION-01 · Terry Gilliam: comic cutout metamorphosis. PAE-02, the threshold

**Film:** `film.mp4` (1280×720, 24 fps, H.264 + AAC, 38.0 s, 912 frames: a 3 s title, the 32 s scene frame for frame on the score, a 3 s "made of" card).
**Rebuild:** `build/make.sh` (fetch sources, fonts, assets, sound, render, check, manifest, stills, mux). Python 3 + numpy + Pillow + fontTools, and ffmpeg.

## Thesis

Every piece of the world is a scrap of public-domain film, cut out with scissors (SAM masks, or a drawn scissor line where no mask existed), turned into an engraving by hatching its own luminance, and hinged on pins. The joke comes from substitution: **a command turns things into other things, and a changed circumstance lets them be themselves again.**

- *Come here* (1.00 s): the woman's head becomes a giant cartoon shouting mouth (*We Learn About the Telephone I*), and on the same frame the dog's head becomes a **door**, the Straight Talk door it is being called through. The dog shuts, crouches, tail tucked, and backs away. At 2.33 s the door-head creaks back into a dog's head (watch).
- *Call again and reach* (3.42 s): the arm telescopes across the whole porch, sleeve card after sleeve card, ending in the grabbing hand from *The Door to Heaven*. On the same frame the dog **turns its card over**. Its back is blank white card with the engraving ghosting through, rubber-stamped **NO**. It lies down with its back to the house.
- The woman hops aside and sits (5.4 s). The door swings in on its hinge, and the coat wall inside lights up warm (6.2 s). The *same* found hand is laid low and still on the boards (6.8 s), the same fragment in a new circumstance. *It's all right* (7.4 s) is spoken by a paper slip and carried by a butterfly (*Insect Zoo*) that leaves the hand, flies to the dog and comes back. At 7.46 s the card turns back over to its engraved front: it looks.
- It waits (the score holds about 7 s). At 14.71 s it comes, head low, on pinned legs that swing with the distance actually travelled. At 23.79 s it folds down across the sill: the head and forelegs are inside the door frame, the rump and tail are out on the boards. The camera cuts in at 25.42 s and holds there. *Come in* (26.4 s): the butterfly flies in through the door, the dog's head leans into the doorway after it on a stretched paper neck, then it puts its chin on its paws and stays.

What would make it bland: a smooth tween of a borrowed rig, substitutions that are only decoration, a refusal that is just a mirrored sprite. The substitutions here carry the meaning: the shut door-head, the stamped back, the hand that grabs and then rests. A blank card back is literally the dog turning its back.

## Native formal language and how it was used

| primitive | where |
|---|---|
| engraved figures | `build/common.py:engrave`: parallel burin lines whose width follows darkness and which bend over the blurred tone, a second set crossing only the darkest tones, a firm cut contour, a 1.5 px bare-card scissor margin, and a hand-colour wash mixed from the source's own colour. Drawn parts (boards, casing, steps, sill, sky field) go through the same hatching (`render.py:hatched`). |
| source-image crops | every card names its frame and crop or mask (`assets.json`, `sources/`). |
| pivot/card joints | dog: head on the neck, two forelegs on the shoulder (the far one is the near one duplicated and darkened), two hind legs on the hips, tail on the rump, a stretched neck strip; woman: head, torso, two legs on the hip. Pivots are in card pixels in `build/cache/cards.json`. |
| matte layers | the SAM masks; the woman cut by colour/darkness against the white wall minus the SAM door mask; the hand cut by luminance on black; the dog's body card minus an inner head polygon. |
| substitution objects | door-head, shouting mouth, the card back with its stamp, the telescoping sleeve arm, the hand laid low, the butterfly as the soft voice, the cloud outline reused as the hills. |
| semantic transformation graph | command → (head: mouth) and (dog head: door, dog card: back); open door + low hand + soft voice → (dog head: dog, card: front) → approach; *come in* → butterfly goes in, head goes after it, settles. |
| held frames, impact sound | poses are animated **on twos**, but every score event lands on its exact frame (`render.py:held`). Snaps instead of tweens: the crouch, the door-head, the 6-frame card turn, the 5-frame door swing with a wobble, a hard camera cut. Every gag has a synthesized impact (`build/cache/sound_events.json`). |

**Time base:** scene frame *i* = score frame *i* (24 fps, 768 frames), placed after the 72-frame title. **Space:** the house front in elevation. Score metres map to screen as `x_px = 300 + 185·x`, so the threshold (centre of the door opening) is at 300 px, the door opening runs 215–385 px, and the porch steps are at 1206 px. The dog's body centre sits on `x_px` and its paws on y = 622. From frame 610 on, a rostrum cut-in (crop at (0, 236), ×1.6) holds on the sill.

## How the dog is built and moved

- **Source:** *Amateur Film New Jersey C* (Home Movies, Internet Archive, public domain), kit frame f008, the cleanest left-facing standing profile, with its SAM mask. It is cut into head (+neck), body, near foreleg, near and far hind legs and a neck strip, at 1.45 × source scale. f008 shows no tail, so the tail is cut from the dog's own back fur under a drawn tail-shaped scissor line. An eye highlight and a nose dot are drawn on, because the photographed head is a dark mass.
- **Moved from the score.** Body x comes from `dog.x`. Crouch, lie, head, tail, wag, rest and look come from `dog.act`. Walking legs swing ±24° with a phase taken from the distance travelled. Crouching lowers the card and splays the legs. Lying folds the forelegs 82° forward and the hind legs 76°, and drops the body to the boards. Rest rotates the head down onto the paws. Look pushes the head 38 px forward, raises it to level and stretches the neck strip.
- **Overrides of the score's smooth acts, so that choices read as choices:** on the retreat frame the crouch (0.85), the lowered head and the tucked tail arrive at once, together with the door-head. The turn (`act.turn`) is replaced by a 6-frame card flip (scale-x by a cosine, never exactly edge-on) that starts on the choice frame. The lie-down at 23.79 s folds over 10 frames from the choice frame.

## Invariants: measured, from the render

`render.py` composites the dog into its own RGBA layer each frame and measures that layer: the alpha centroid of the body card, the bounding box, the mean luminance (the blank back is pale), the warmth of the door-side 28% (the door-head is grey, the dog ochre) and the body's drop. `check.py` turns these into `trace.json` and `build/checks.json`. The detection thresholds were set by me after reading the signal values, so this is a builder's measurement, not an independent one.

| choice | score t | measured onset (signal) | Δ |
|---|---|---|---|
| watch → retreat | 1.000 | 1.000 (crouch + door-head on frame 24; x moving away by 1.167) | 0 |
| retreat → watch | 2.333 | 2.333 (door-head gone; crouch released 2.417) | 0 |
| watch → refuse | 3.417 | 3.417 (card starts turning; blank back shown 3.583) | 0 |
| refuse → watch | 7.458 | 7.500 (turn starts; front shown 7.583) | +0.04 |
| watch → approach | 14.708 | 14.833 (measured x down 3 cm) | +0.13 |
| approach → lie down | 23.792 | 23.833 (body drops; fully down 24.0) | +0.04 |
| hears *come in*: looks in, settles | 26.4 | 26.5 head moves into the door frame; settled 28.5 | +0.10 |

All are within ±0.25 s. Other results:
- **Never enters:** minimum measured x is 0.59 m, the same as the score's minimum (sill 0.56).
- **Ends across the threshold:** the final dog bounding box spans 258–570 px against the door opening's edge at 385 px. That puts 127 px inside the frame and 185 px out on the porch, and the measured posture is lying.
- **Follows the score:** maximum |x_measured − x_score| is 0.031 m (mean 0.003 m), using a calibrated constant card-centroid offset per side of the card. The retreat is +0.996 m measured against +0.996 m in the score. The approach is 3.406 m in 9.08 s in both.
- **Commands push away:** x goes from 3.00 m at the first call to 4.00 m after the second.
- **Circumstances before the approach:** she sits at 5.42 s, the door opens and the light comes on at 6.21 s, the low hand at 6.83 s, the soft voice and butterfly at 7.4 s. The approach is at 14.71 s. These times come from the score, and I looked at the rendered frames to confirm each one is on screen.

## What was looked at (perceptual, by the builder only)

I looked at the card contact sheets, probe frames, four contact sheets over the whole scene, full-size frames extracted from the encoded video (4.2, 6.7, 10.6, 13.6, 30.0, 31.0 s film time), a 1 fps sheet of the final `film.mp4`, the title and end cards, and the four stills. At thumbnail size these all read: the shouting mouth with *COME HERE!*, the door-head, the stamped blank back, the lit door, the head-low walk, the dog lying half in the frame. **No independent critic has watched this film. I have not heard the sound.** It was checked only as numbers, as an RMS profile per second. The voices are crude additive formant synthesis and may not be intelligible as words. The paper slips carry the words.

## What failed and what changed (see `ledger.jsonl`)

- The first engraving was mud: cross-hatching everywhere and the scissor margin hatched over. I masked the ink to the card and lightened the tones.
- The first body card still contained the head, so rotating the head card left a ghost head behind it. The body card now has an inner head polygon removed.
- The sky came out white because the gradient was in 0–255, not 0–1. A bush cut became rectangles. Its replacement, the cloud's own outline, came out as large dark hills, and I kept that.
- The tiled stone pillar first made dark figure-like blotches. I re-cropped it to the lit stones.
- Hands: the butterfly-hand cut was fragmented and unreadable as a low hand, and an engraved cartoon face for the soft voice read as a striped block. The soft voice therefore keeps the woman's own head and is spoken by the slip and the butterfly. The low hand is now the same *Door to Heaven* hand laid low, a substitution rhyme instead of a second, weaker source.
- At first the card flip passed through exactly edge-on, so the dog vanished for two frames and the measurement broke. The flip now uses quarter-frame phases.
- The look-in was unreadable in the wide shot, so I added a hard rostrum cut-in at 25.42 s and a longer head lean with a stretched paper neck.
- The first detector for the door-head (pale pixels) could not see it, because the door-head is greyish but not pale. It was replaced by a warmth (R−B) measure.

## What I did not do / limits

- The SCION prompt's own hard proof scene (dignitary → fish → door → crowd) was replaced by this scene, as the brief requires. No fish is used.
- No independent critic, no human viewing, no listening test. The "pass / reference stronger / inconclusive" verdict is left to the critic.
- I did not make the operator page or the three alternate final beats as renders. As text, the three alternate final beats are: (a) the stamp on the card's back changes from NO to a faint *maybe* as it settles; (b) the door-head returns once, as a tiny open door, when it hears *come in*; (c) the butterfly comes back out and lands on its head, and it still stays.
- The woman is seen from behind throughout, because the found woman is filmed from behind. Her jeans come from another frame of the same shot. The middle hold (8–14.7 s) is mostly still, as the score asks. Only the butterfly and the clouds move.
- Measurements are of my own dog layer before compositing; a critic re-measuring from `film.mp4` pixels would need their own segmentation. After the cut-in, `x_screen` / `y_screen` in `trace.json` are in film pixels and `x_stage` is in pre-camera pixels.

## Protected

The six choice frames and the snaps that land on them; the door-head ↔ open-door rhyme; the NO-stamped back; the same hand grabbing, then resting; the butterfly leading the look-in; the dog ending half in the door frame and never past x = 0.59 m.

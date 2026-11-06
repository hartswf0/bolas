# THEORY OF PLAY — Contaminant Jelly (third version)

The game runs on the film's own renderer (`../contaminant.html?play=1`). It keeps the film's jellyfish, archive frames, Afterlight look and censor, and changes the rules so that each verb has exactly one rule. A rule is taught when you first meet it, not in a menu.

## Third version: time, after the critics (round 2)
Two independent critics played the second version. Both returned **reference stronger**.
- **Play tester.** A bot that only taps toward the target took all 14 frames in about 50 s. Arrow keys did nothing. Matching dissolved into jump cuts by the sixth cut. The pulse made no difference.
- **Operative theorist.** Nothing accumulates. The water, the jellyfish and the reel forget what the player did; the game runs on clock time, not duration.

Repairs:
- **The intro.** A gate screen (one gold dot beating: "tap · sound on") leads into about 10.6 s of sequence:
  - Three archive frames are scanned into existence as lidar point clouds and lifted into depth by luminance, under a slow orbit ("AN ARCHIVE").
  - On beat 8 the censor's bell burns the frame with the touch from the touch outward, and its points lift as embers ("WHAT THE CENSOR CUT").
  - All the points converge into the jellyfish ("THE JELLYFISH KEEPS"), and it ignites on beat 14.
  - The music cues each beat: heartbeat, then bell, then a rising wash, then the birth. It can be skipped.
- **The water becomes the film.** What you carry is printed into the water along your path, then diffuses, rises like heat and fades, a long exposure after AFL-14/17. Two frames painted into the same water double-expose.
- **The worm.** The jellyfish's last 5 s trail behind it as soft gaussian splats. Each is tinted the colour of the frame carried at that moment, rising and cooling to the afterimage's blue (AFL-07 spacetime, AFL-17 worms).
- **Scars.** A burn leaves a charred scar in the water that keeps spreading for the rest of the round.
- **Duration in the reel.** Each shot plays for as long as you carried it, scaled so the reel runs about 12 s. A burned shot first holds still on the moment it burned.
- **The time-image, as a resource.** Stop stroking for 2 s and time stops:
  - the clock pauses
  - the world and the censor's beam slow to a quarter
  - the pulse drops out of the music
  - the water stops fading

  You have 12 s of held time per round (the blue hairline). It is a way past the beam.
- **A time arc.** In the last 30 s the censor grows strict: its beam widens and burns anything you carry, not only touches.
- **Circulation.** A spliced frame returns to the water 6 s later, as the archive returns to circulation in the film. The reel has no cap, the round always ends on the clock, and you score cuts and your longest run of matches.
- **The pulse.** A stroke on the pulse (±0.09 s) gets 1.45× push; an off-beat tap gets 0.55×.
- **Keyboard.** Fixed: arrow keys and WASD now swim. A keys-only bot scored 21 cuts.
- **Phones.** Text is 1.6× larger on touch screens, and portrait shows "turn your phone sideways".

Measured with bots at 1280×720, one 90 s round each:

| bot | cuts | burns |
|---|---|---|
| strokes on the pulse | about 33 | 7 |
| taps every 450 ms | about 30 | 3 |
| keys only | 21 | 5 |

There were no page errors. The pulse helps the bot only by about 10%, short of the play tester's 25% target, because the bot's travel is not the bottleneck. How much it helps a person is unknown.

## The loop (second version, kept where not changed above)
1. **Swim.** One tap, swipe, click or key press is one stroke of the bell; the bell then glides. Holding a finger, the mouse button or a key strokes once immediately, then on every pulse.
2. **Catch.** Swim into a frame that glows gold. The frame then plays **inside the jellyfish's bell**; the game does not cut away from the world. Tap or click the jellyfish (or press space) to watch it full screen. Tap again to return.
3. **Splice.** Carry it into the dashed circle around the sun. It flies into your reel, the strip at the top.
4. **Match.** The next frame must share a visible feature with the last frame on your reel (hand, door, glow, person, animal, ground, body, up). Catchable frames glow and show the shared word; the others are dim and bounce you off with "no match". If nothing left matches, any frame is allowed as a jump cut.
5. **The censor.** The sun's beam sweeps the water, faster as time runs out. A frame with a touch in it is marked with a red dot before you catch it. Carry it through the beam and the beam turns red, the phone buzzes, a crackle rises, and after 0.6 s in the light it burns. It then sinks to the floor, and you can dive for it and lift it back; it stays in your reel, pink-scarred. Frames without a touch are never at risk.
6. **The reel.** When time runs out, or when all 14 frames are spliced, your reel plays full screen. Each frame's camera travels from the feature it shares with the frame before to the one it shares with the frame after, so every cut lands on the match.

## Mastery: the pulse
The music runs at 96 bpm, and a ring closes on the bell on every beat.
- **On the pulse:** a stroke within ±0.11 s of the beat (latency-corrected) is *on the pulse*. It gives 25% more push, adds resonance and plays a chime. Resonance (the gold arc round the bell) raises stroke power by up to 2× and decays slowly.
- **Mashing:** strokes under 0.2 s apart are weak and drain resonance.

## Feedback on every input
| event | sight | sound | touch |
|---|---|---|---|
| stroke | bell snaps, bubbles | thump + water breath | 8–20 ms |
| on the pulse | ring flash, arc fills | chord chime | 10·30·14 ms |
| catch | 3-frame hitstop, frame plays in the bell, match word pops | a bell at the frame's pitch | 28 ms |
| no match | frame bounced, "no match" | two dull taps | 6 ms |
| splice | frame flies to the strip, sun flares | rising arpeggio (+ shimmer for a kept touch) | 20·40·40 ms |
| in the beam with a touch | red beam, red glow round the bell | crackle | 10 ms every 0.14 s |
| burn | screen shake, frame burns in the bell | the censor's out-of-key bell + nitrate crackle | 40·30·120 ms |
| watch | full-screen frame | whoosh | — |

## The music is the edit
The pad and the heartbeat play on their own. The melody is your reel: each spliced frame adds its note, and burned frames are muffled. See [SCION_GARDEN_AFTER_ENO.md](SCION_GARDEN_AFTER_ENO.md).

## The magic circle
- The game no longer cuts away to inserts, and has no separate cool phase or story timer.
- The film-grain "glitch" layer (scratches, flicker, red blinks) is gone from play; only a soft vignette remains.
- The title screen teaches three verbs; contextual hint lines teach each rule when it first matters, and disappear once it has been used.

## Spoil-sports
- **The masher:** meets weak strokes.
- **The idler:** sees the hint line and the dotted hairline to the nearest catchable frame.
- **The player who ignores the beam:** loses time to burns, but never loses a frame for good.

## Measured (scripted bot, headless Chromium, no page errors)
| viewport | result |
|---|---|
| 1280×720 desktop | completed all 14 in about 49 s, with 3 burns and 3 rescues |
| 844×390 touch | completed all 14 in about 50 s, with 2 burns; tap-on-jellyfish watch opened and closed |

The bot always steers toward the hairline, so the round may be too easy for a skilled player. That is unknown until a person plays it.

**Not measured:** how it feels, whether the music is good, and whether a first-time player learns the rules from the title screen and hints. No person has played this version yet.

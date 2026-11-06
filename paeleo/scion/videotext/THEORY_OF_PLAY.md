# THEORY OF PLAY — Contaminant Jelly (second version)

The game runs on the film's own renderer (`../contaminant.html?play=1`). It keeps the film's jellyfish, archive frames, Afterlight look and censor, and changes the rules so that each verb has exactly one rule. A rule is taught when you first meet it, not in a menu.

## The loop (one round is 90 s)
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

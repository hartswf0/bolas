# THEORY OF PLAY — the jellyfish swim

The game is the film's own renderer (`../contaminant.html?play=1`).

**Verb.** *Stroke.* A jellyfish does not glide on its own. It pulses, then coasts. Each input is one pulse:
- swipe: stroke along the swipe
- tap: stroke toward the point
- hold: strokes on a steady beat
- arrow keys: strokes

After a stroke, the body glides and water drag slows it (velocity × 0.3 per second).

**Rhythm (mastery).** Strokes 0.33–0.72 s apart build *resonance*:
- Resonance raises stroke power by up to 2×, brightens the body and fills the bar in the strip.
- Mashing (strokes under 0.22 s apart) weakens each stroke to 35% and drains resonance.

Skill shows as a number that only rhythm raises.

**Feedback (two channels or more on every input).**
| input | sight | sound | touch |
|---|---|---|---|
| stroke | tentacles snap, speed streaks, camera pulls back | low thump + water breath | 8–24 ms vibration, scaled by resonance |
| catch | 4-frame hitstop, pulse ring, frame joins strip | catch tone | 28 ms; censored frame: stutter pattern |
| release at sun | projection | — | 16 ms |
| censor's bell | burn | bell | 30·40·90 ms |
| bump a frame that doesn't rhyme | frame nudged | — | 6 ms |

**Stakes.** Only a frame that rhymes with your last catch will come with you. Under the censor, a touched frame burns at the sun. When the projector cools, dive and lift the burned frames back.

**Magic circle and its breaks.**
- *Inserts take control:* shortened to 0.95 s, and the HUD is hidden during them.
- *Losing the jellyfish:* an off-screen chevron points to it.
- *Not yet repaired (from the critics):* score causality, a censor that can't be seen before it burns, and a dead cool phase.

**Spoil-sports.**
- *The masher* meets weaker strokes.
- *The idler* drifts to a stop. An idle hint is still missing.

**Measured (headless script, 844×390):**
- swipe right moved dx 117, dy 8
- rhythmic strokes reached resonance 0.64
- mashing brought resonance to 0.00
- tap left-down moved dx −9, dy 22
- no page errors

**Not measured:** how it feels in the hand. Vibration only works on Android browsers (iOS Safari ignores `navigator.vibrate`). No person has played it yet.

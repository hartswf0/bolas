
## writer-letterer (U2), 2026-11-17

**1. "2-frame pen lift between strokes" vs "about 9 glyphs/s" (unit assignment, not plan.json).**
Taken literally (every stroke ≥1 ink frame + 2 lift frames) the balloons need A1 72, A2 93, A4 66, B1 147, B2 57, B3 87, B4 111 writing frames; B1 alone (147 f = 6.1 s) exceeds its 5.5 s slot before any hold, and the rate falls to ~5 glyphs/s. The bar's pacing (9 glyphs/s, holds ≥2 s, slot times) cannot be met that way.
*Built instead:* 9 letters/s (alphanumerics; punctuation and lifts inside that budget), a 2-frame pen lift between words and between lines, 0.4-frame lifts between strokes inside a word, the 10-frame B4 hold after SOMEONE exactly. Every stroke still has its own onset and point path in balloons.json, so the sound unit gets one onset per stroke.
*Proposed change:* read the 2-frame lift as "between words / lines".

**2. B1 at 9 letters/s plus a 2.0 s hold is exactly at the edge of its 5.5 s slot.** B1 is written at 9.16 letters/s so the hold is exactly 48 frames (2.0 s). That is within "about 9 glyphs/s". A strict 9.0 would need B1's slot 0.1 s longer, and that would push the next camera move below 0.5 s. So no change is proposed; this is recorded for the editor only.

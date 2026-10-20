# The gust test · critic round 3

*Round 3 fresh review of repaired test.* A separate agent that did not make the work, started Oct 18 00:31 EDT. Brief and report verbatim. File paths in the brief are the working paths on the day.

## The brief

```
You are an independent reviewer of a 7-second animation test of a small handmade cardboard puppet. You did not make it and have not been told what the shot is meant to show.

ANIMATION: /home/claude/puppet/review3/seq_1.png then seq_2.png = every second frame (12 fps), left to right, top to bottom, labeled with frame and time. Full-size frames: /home/claude/puppet/review3/full_f*.jpg. Stills, not playback; say when a judgment needs playback.

PART A, answer before reading Part B's method notes: describe beat by beat (with times) what the character notices, does, and how its attitude changes; what causes it and from which direction; then rate how clearly the attitude change reads through the body alone, 1–5, with one line on why.

PART B. SOURCES (the real puppet): /home/claude/puppet/review3/source_07.jpg, source_09.jpg, source_10.jpg, source_05.jpg. Method, disclosed: frames 0–21 are the unaltered photograph 09. After that, the puppet is that photograph cut into its cardboard segments and rotated about its joints. Revealed background is reconstructed. The head's right side face is generated plain cardboard. The scarf tail is the photographed tissue bent along a chain. White wind streaks and soft contact shadows are generated. Verify each item with measurements where you can:
1. The head's side face shares the front face's right edge with no background gap, and the right pin enters it (f038–f166).
2. The viewer-right foot does not move at all after f000 (bottom edge and corners within 1 px).
3. The viewer-left foot lifts, clears the box top, lands back within 2 px of the box top, and does not slide afterwards.
4. No ghost smear or pale blob in the revealed sky beside the head or where the right hand was (f088–f166).
5. No light halo or fringe around moved parts (left leg at f049–f064, lowered right arm at f106–f166).
6. Wind streaks pass behind the puppet, never across it.
7. Anything else that breaks identity (face marks, pins, connectors, torn edges drifting) or physical presence.
For each item: PASS or FAIL, with frame and pixel evidence.
End with the single largest remaining gap. Under 450 words.
```

## The report

**PART A (written before reading the method notes)**
- **0–0.9 s:** The puppet stands on the box with both arms raised wide and its face toward the gap and the two hikers. The pose reads as open or triumphant. The scarf already streams to viewer-right.
- **~1.0 s:** Thin white streaks appear, running horizontally. With the scarf direction, they put the wind as coming from viewer-left.
- **1.6–2.0 s:** The head tilts and turns, so its side face shows. Its gaze shifts down and toward viewer-left, the direction the wind comes from.
- **2.0–3.0 s:** The viewer-left leg lifts, swings out about 60 px and comes back. At the same time the raised arm drops to horizontal, pointing forward, and the torso leans into the wind. It reads as bracing.
- **3.7–4.4 s:** The other arm falls from outstretched to hanging at the side.
- **4.4–6.9 s:** Everything holds still.
- **Attitude change:** open and exultant becomes braced and guarded against a wind from viewer-left.
- **Rating: 2/5.** The poses change a lot, but there is no anticipation and no reaction to a specific gust. The head turn is ambiguous, and the last 2.5 s are dead. Easing would need playback to judge.

**PART B**
1. **Head side face: FAIL.** At f038 and f166, the left third of the side panel is pale grey with cloud texture showing through it, so it is not plain cardboard. The panel is also an upright rectangle while the front face is tilted about 15°. The pin does enter it.
2. **Right foot: FAIL, small.** The bottom (y=920) and right edge (x=747) are constant from f024 to f166. But at the switch to the cutout (f022), the left edge jumps from x=675 to 683: the torn fringe is trimmed off and a grey contact disc appears. After f024 it is stable within 1 px.
3. **Left foot: PASS, but the clearance is marginal.** In contact-sheet pixels (1 px = 3.2 full px), the foot lifts at f046, peaks at f060–062 (bottom about 39 px up, x shifted about 64 px), and is back at 149/173/291 by f074. It is identical through f166, so there is no slide. At f059 the sole is within a few px of the box's back edge, so it barely clears.
4. **Ghost smear or pale blob: FAIL.** There is a hard-edged rectangle of cloud texture pasted into the blue sky beside the head (about x680–780, y150–230) at f088–f166. There is also a grey vertical smudge where the right hand was (about x940–980, y420–500). It is already visible at f088 and persists to f166.
5. **Halo around moved parts: FAIL.** There is a pale fringe around the left leg at f059, and a white rim around the lowered hand at f106 and f166. The unmoved right shin and foot also get a halo from f024 on, so the whole cutout carries it.
6. **Wind streaks: PASS on inspection.** Streaks end at the leg and thigh edges (for example f059 at the knee, f024 at x720,y715), and I saw none crossing the body.
7. **Other: FAIL.**
   - The contact shadows are flat grey discs wider than the soles (f166).
   - The same edge trimming as item 2 shows at the cut from photo to cutout at f022.
   - Face marks, both pins and the scarf hold their identity.

**Single largest remaining gap:** The head side face, together with the pasted cloud block beside it. The head is where the viewer looks, and it shows a see-through grey panel and a rectangular patch of the wrong sky, both of which say "composite" on every frame from 1.6 s to the end.

Crops I used are in /tmp/claude-0/-home-claude/4fcf2301-cc19-5f90-be19-3bb1b3367fc1/scratchpad/ (head_166.png, hand_166.png, feet_166.png, leg59.png, rfoot.png).

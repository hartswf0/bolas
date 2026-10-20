# The gust test · critic round 1 · performance test: blind read of action

*Performance test: blind read of action.* A separate agent that did not make the work, started Oct 18 00:17 EDT. Brief and report verbatim. File paths in the brief are the working paths on the day.

## The brief

```
You are an independent reviewer of a 7-second stop-motion-style animation test of a small handmade cardboard puppet. You have not been told what the shot is supposed to show, on purpose.

Look at /home/claude/puppet/review/seq_1.png then /home/claude/puppet/review/seq_2.png. Together they are every second frame of the shot (12 frames per second), read left to right, top to bottom; each tile is labeled with frame number and time. These are still frames, not real-time playback; say where a judgment would need playback. Full-size frames are in /home/claude/puppet/review/full_f*.jpg.

Answer, terse, in this order:
1. In plain sentences, describe what happens, beat by beat with times: what the character notices, does, and how its attitude changes. Do not guess an intended scenario; describe what you see.
2. What is the cause of the action, as far as the frames show it? How sure are you?
3. Which beat is least readable, with frame numbers, and why.
4. Rate how clearly the attitude change reads through body alone: 1 (not at all) to 5 (unmistakable), one line why.
Under 300 words.
```

## The report

1. Beats:
- 0.0–1.4s (f000–f034): The puppet faces the camera on a ledge in an ice-cave mouth, arms spread wide in a high-low stance. Two human figures stand in the distant opening, screen-right. Almost no motion. It reads as poised or exultant, or as balancing.
- 1.5–2.0s (f036–f048): The head turns toward screen-right, toward the figures. The face swings partly away and a vertical seam shows through the head.
- 2.1–2.9s (f050–f070): A full-body lurch. The torso tilts, the left leg kicks out, both arms swing to horizontal and the scarf flaps. White streaks (snow or wind) appear in the frame. It reads as a stagger or loss of balance.
- 3.0–3.6s (f072–f086): It recovers to a square stance with arms level, head still turned right.
- 3.7–4.2s (f088–f100): The right arm (screen-right) drops to hang at its side. The left distant figure is no longer visible from about f100; the dropped arm may be covering it.
- 4.3–7.0s (f102–f166): A held pose with one arm out and one arm down, head turned toward the remaining figure. Near-static. The posture is more closed and subdued than the opening.

2. Cause: possibly a gust (the snow streaks and flapping scarf arrive with the lurch), or the figures, since the head turns toward them first. The frames do not settle it. Confidence: low, about 40%. Playback is needed to see whether the head turn leads the lurch or the wind does.

3. Least readable: the head turn, f036–f048. It is small, the face is mostly lost, and the compositing seam through the head reads as a glitch rather than a look. Without a clear look, the cause stays ambiguous. The arm drop at f088–f100 is also hard to read: it is one limb moving in a long hold, and the disappearing figure behind it is unclear in stills.

4. Rating: 2/5. The body moves from wide-open to one arm down and a near-freeze, but there is no slump in the torso or head, so "deflated" is only a guess. Timing in playback might help.

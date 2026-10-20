# Trouttown: Tempus Fugit · critic round 4

*Critic review of passage v4 tail.* A separate agent that did not make the work, started Oct 19 15:11 EDT. Brief and report verbatim. File paths in the brief are the working paths on the day.

## The brief

```
You are an independent critic for an animated short; you did not build it; do not edit project files. Give a verdict PASS or NOT YET with timestamped evidence.

Read the round-3 report first: /tmp/claude-0/critic_v3.md. Its one BLOCKING issue: the "fitter bolts the elbow's top flange to the spout" beat was not on screen (elbow top mouth tilted and offset from the downspout, no visible fastener, wrench working at Boone's head height, Boone's head overlapping the elbow's lower mouth after release so the elbow could read as resting on his head).

A fix was made, and only the affected stretch was re-rendered: /home/claude/lab/tfu/renders/passage_v4_tail_29-42.mp4 (passage time 29–42 s; file time 0 = passage 29 s). Frame grabs named by passage time: /home/claude/lab/tfu/validation/v4/f_<t>.jpg (960 px wide; view with Read). Extract more with ffmpeg (file time = passage time − 29) to /tmp/claude-0/ only. Per-frame data: /home/claude/lab/tfu/clips/brace_discover_redirect.json.

Intended fix: after the swing (31.4–34.2) the elbow hangs centred under the downspout end, joined by a dark tarred-cloth sleeve with two metal band clamps; from 36.6–39.6 the fitter tightens the clamp bolt using a wrench on a long bar (bolts visibly enlarge); Boone leans back as he releases (40–41.6) so his head clears the lower mouth; the elbow stays put after release.

Judge: (1) does the joint now read as a connection between spout and elbow (sleeve + clamps)? (2) is the fitter's tightening at that joint legible? (3) after release, does the elbow read as held by the joint rather than floating or resting on Boone? (4) do all the round-3 PASS items in this stretch still hold (arch clear, water into arch, gradual drain with residual, trickle on right, Boone's head visible, apprentice clearing)? (5) any new problems, distinguishing blocking from polish. Write report to /tmp/claude-0/critic_v4.md and return it in full, concise.
```

## The report

The verdict is NOT YET. The tightening beat now reads at the joint. One blocking item remains: Boone's head is still against the elbow after he lets go. The report is at /tmp/claude-0/critic_v4.md, and my full-resolution crops are in /tmp/claude-0/v4c/.

## Against your five questions

**1. Does the joint read as a spout-to-elbow connection? Partly.**
- The gap is closed. From 33.5 s on, a dark piece runs continuously from the spout end to the elbow, and the elbow does not move from 37.5 s.
- It does not read as a cloth sleeve. It is a flat upside-down triangle with fan lines, so it looks like a funnel hanging off the spout.
- The "two band clamps" are drawn as two grey bars forming a "7": one across the top, one down the left edge to a bolt at the tip. They look like struts or a bracket, not bands around a pipe.
- The elbow is rotated 82.6 degrees (from elbow_M), so its upper mouth faces right while the spout runs straight down. The triangle bridges a 90-degree mismatch. Round 3 asked for the mouth to sit on one axis under the spout, and that was not done.

**2. Is the tightening legible? Yes, PASS.**
- From 36.5 to 39.5 s the fitter raises a long bar to the lower bolt at the tip of the triangle.
- The bolt is a small dot at 36.0 s and a large hex at 37.0–38.5 s.
- It is small at 960 px, but the reach up to the spout reads.

**3. After release, is the elbow held by the joint? Not yet.**
- It no longer floats, because it stays still.
- Boone barely leans back: his rotation goes from 0.02 to −0.14 by 41.5 s.
- At 41.95 s, his best frame, his head (about x 1142–1245, y 458–530 at 1080p) still overlaps the elbow's lower barrel by about 15 px or more. There is no gap at any point from 40 to 41.95 s.
- The elbow sits left of and above his head, pressed against it, so his head can still read as propping it up.

**4. Round-3 PASS items: all still hold.**
- **Arch clear:** the apprentice stays left of the left jamb; Boone and the fitter stay right of the right jamb.
- **Water into the arch:** it hits the closed brick at 34.5 s and enters the opening from 36 s.
- **Drain with residual water:** pool_level falls 95 → 82 → 68 → 44 → 29 → 19 → 13.5 from 35.5 to 41.5 s, and a shallow sheet is still visible at 41.8 s.
- **Trickle on the right:** strands at 33.5–34.5 s, then only drips from 36 s.
- **Boone's head visible:** from 34.5 s to the end.
- **Apprentice clearing:** chips at 33.5 s, exposed brick at 34.5 s, bricks falling in at 36 s, opening clear from 37.5 s.

## 5. Problems, ranked
1. **Blocking: Boone's head touches the elbow from 40 to 41.95 s.** Move his root about 50 units to the right, or lean him to about −0.3 rad by 41 s. That should open a visible gap of at least 20 px at 1080p.
2. **Should fix in the same pass (polish only if a makeshift join is acceptable): the joint shape.** Either rotate the elbow so its upper mouth sits on the spout's axis, or draw the sleeve as a wrap over both pipe ends with two bands across it.
3. **Polish, carried over:** at 33.0–33.5 s the water seems to start from Boone's torso, left of the elbow mouth. At 33.5 s the right-side strands still pass the fitter with no splash.
4. **Polish:** the tightening is small at 960 px. A short turn of the bar or a brief push-in would help.

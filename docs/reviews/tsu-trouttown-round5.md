# Trouttown: Tempus Fugit · critic round 5

*Critic review of passage v5 tail.* A separate agent that did not make the work, started Oct 19 15:35 EDT. Brief and report verbatim. File paths in the brief are the working paths on the day.

## The brief

```
You are an independent critic for an animated short; you did not build it; do not edit project files. Verdict PASS or NOT YET, with timestamped evidence.

Read the round-4 report first: /tmp/claude-0/critic_v4.md. Blocking item: Boone's head touched the elbow from 40 to 41.95 s after release (no visible gap), so the elbow could read as resting on his head. Should-fix: the spout-to-elbow joint read as a flat funnel/triangle with strut-like "clamps" rather than a cloth sleeve with band clamps.

Fix made; re-rendered stretch: /home/claude/lab/tfu/renders/passage_v5_tail_33-42.mp4 (file time 0 = passage 33 s). Grabs named by passage time: /home/claude/lab/tfu/validation/v5/f_<t>.jpg (960 px; view with Read). Extract more with ffmpeg (file time = passage − 33) into /tmp/claude-0/ only.

Intended: the joint is now a thick dark tarred-cloth hose that leaves the spout end straight down and bends into the elbow's upper rim along the elbow's axis, with cloth wraps across it and two metal band clamps across the hose, each with a bolt (bolts enlarge 36.6–39.6 as the fitter tightens with a wrench on a long bar). After letting go at 40.0 Boone leans back and side-steps right (40.3–41.5) so his head clears the elbow by a visible gap.

Judge: (1) is there a visible gap between Boone's head and the elbow from about 40.6 s to the end (≥ ~20 px at 1080p by the end)? (2) does the joint now read as a sleeve/hose with band clamps connecting spout and elbow? (3) is the tightening still legible and the elbow still steady after release? (4) any regressions in this stretch (water into arch, drain with residual, Boone's head visible, crew placement, feet planted / not sliding during the side-step, Boone not colliding with the fitter's step box)? (5) new problems, blocking vs polish. Write to /tmp/claude-0/critic_v5.md and return it in full, concise.
```

## The report

I judged the round-5 render as PASS. The round-4 blocking item is fixed, but four should-fix items remain. The report is at /tmp/claude-0/critic_v5.md and is reproduced in full below. My frames, crops and foot strips are in /tmp/claude-0/v5c/.

# Critic report, round 5: passage_v5_tail_33-42.mp4 (passage 33–42 s)

Evidence: the provided grabs (f_34 to f_41.95) and my own 1080p frames, crops and foot strips at 33.5–41.95 s (in /tmp/claude-0/v5c/: full_*.png, crop_*.png, jstack.png, s1.png, s2.png, feet.png, feet2.png). All pixel figures are at 1080p.

## 1. Gap between Boone's head and the elbow: PASS (from 41.0 s)
- **40.0–40.3 s:** the head is still against the elbow's lower barrel and mouth while he starts to lean.
- **40.6 s:** the head is moving away, but its top-left corner still meets the mouth rim. There is no gap yet.
- **40.9 s:** a gap of about 10–15 px opens.
- **41.2 s to the end:** the gap is clear, about 40–50 px. The head's left edge is about 40 px right of the barrel. The head top is about 45 px below the mouth flange (crop_41.95, s2.png). A viewer no longer reads his head as propping up the elbow.
- The gap is about 0.3 s later than the intended 40.6 s, but it meets the bar of at least 20 px by the end.

## 2. Joint reads as a sleeve or hose with band clamps: PARTIAL (should-fix, not blocking)
- **Better than round 4.** The flat triangle and the strut "7" are gone. A dark piece runs continuously from the spout down onto the elbow's upper end (jstack.png at 35, 37.5, 39.6 and 41.95 s).
- **It reads as a rounded bag, not a hose.**
  - The shape is a peanut- or balloon-shaped dark blob with fan lines. Its lower lobe is pasted over the end of the elbow's mouth, which still faces right.
  - There is no visible bend from vertical into the elbow's axis, and no tube walls or diameter you can follow. The "cloth wraps" read as radial lines, not wraps.
- **Clamps.**
  - One grey band runs horizontally across the hose with a bolt at its left end. This one reads as a band clamp.
  - The second "clamp" is a short vertical bar with a bolt dot at its top. It runs along the hose, not across it, so it reads as a strut or tab.
- **Fix:**
  - Give the hose parallel side walls of about pipe width, and draw a visible curve that meets the mouth flange from its open end.
  - Draw the second band horizontally across the lower part of the hose, parallel to the first.

## 3. Tightening legible; elbow steady after release: PASS
- **Tightening (36.6–39.6 s).** The fitter raises a long bar to the left bolt of the upper band. The hex head is visible at 37.5 and 38.5 s (c375.png, crop_38.5).
- **Bolt growth.** The bolt is a small dot at 35 s, a large hex at 37.5–39.6 s, and a larger dot than at the start at 41.95 s.
- **Still small at 960 px.** The tightening shows as a thin stick (polish, carried over).
- **Elbow steady.** I compared the elbow, the wall grate and the arch from 40.0 to 41.95 s by image registration. The elbow shifts (5, 8) px and the grate (−1, 6) px. The arch shifts (13, 3) px.
  - All three move together, which fits a slow camera drift or zoom; the elbow does not move relative to the wall.
  - It does not sag or drop after release.

## 4. Regressions
- **Water into the arch: PASS.** The stream enters the opening from about 36 s to the end.
- **Drain with residual: PASS.** The waterline falls steadily (f_36 → f_38 → f_41.95), and a shallow sheet remains at 41.95 s.
- **Boone's head visible: PASS** throughout.
- **Apprentice: PASS.** He stays left of the left jamb.
- **Crew placement: REGRESSION (should-fix).** From 41.2 s Boone's side-step puts him in front of the fitter.
  - The fitter's face is hidden behind Boone's head; only the fin, a strip of vest and the tail show (s2.png, f_41.95).
  - At 40.6–40.9 s Boone's right arm also swings across the fitter's torso.
  - The worker who made the fix is hidden during the "it holds" beat.
- **Feet: FAIL (should-fix).**
  - The right foot steps cleanly: it lifts and lands at 40.5–40.9 s (feet.png).
  - The left boot then slides about 35 px right from 41.0 to 41.5 s with no visible lift. It stays flat on the floor line (feet2.png).
- **Step box: FAIL (should-fix).** From 40.9 s to the end Boone's right boot overlaps the front-left of the fitter's step box by about 20–40 px. Both rest on the same floor line, so it reads as his foot going into the box, not standing in front of it (s2.png at 41.5 and 41.95 s).

## 5. Problems ranked
- **Blocking:** none.
- **Should-fix:**
  1. Left-foot slide, 41.0–41.5 s. Add a second lift-and-plant step, or keep the left foot pinned and let the hips carry the lean.
  2. Boone's boot overlaps the step box, 40.9 s to the end. End the side-step about 40 px further left of the box, or move the box right.
  3. The fitter is hidden behind Boone at 41.2–41.95 s. Pull the fitter right or forward, or shorten Boone's step so that the fitter's face stays visible. Do this without closing the head gap.
  4. The joint reads as a bag, not a hose, and the second clamp runs along the hose instead of across it (see section 2).
- **Polish:**
  - The gap opens at about 40.9 s rather than 40.6 s.
  - At 33.5 s the stream still seems to start from Boone's torso (carried over).
  - The tightening is small at 960 px.

## Verdict: PASS
- The round-4 blocking item is resolved. From 41.0 s Boone's head clears the elbow by a visible 40–50 px, and the elbow holds steady relative to the wall.
- No new blocking issues.
- Four should-fix items remain, all in Boone's side-step and the joint drawing: the left-foot slide, the boot overlapping the step box, the fitter being hidden, and the joint reading as a bag rather than a hose.

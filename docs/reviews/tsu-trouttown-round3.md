# Trouttown: Tempus Fugit · critic round 3

*Critic review of passage v3.* A separate agent that did not make the work, started Oct 19 14:41 EDT. Brief and report verbatim. File paths in the brief are the working paths on the day.

## The brief

```
You are an independent critic for an animated short. You did not build it; do not edit any project files. Judge strictly and give a verdict: PASS or NOT YET, with timestamped evidence.

Material:
- Render: /home/claude/lab/tfu/renders/tempus_fugit_passage_v3.mp4 (42 s, 24 fps). Frame grabs: /home/claude/lab/tfu/validation/v3/f_<t>.jpg (view with Read). Extract more with ffmpeg if needed, writing only under /tmp/claude-0/ (e.g. `ffmpeg -loglevel error -ss 33.5 -i <render> -frames:v 1 -vf scale=960:-1 /tmp/claude-0/c3_33.5.jpg`).
- Per-frame data: /home/claude/lab/tfu/clips/brace_discover_redirect.json (frames[i].contact_err in world units; Boone ~390 units tall; after 40.0 s palms are marked released).
- Previous critic report (round 2): /tmp/claude-0/critic_v2.md — read it first.

Story intent: Boone (cardboard puppet) holds a copper elbow under a downspout in a flooding inlet chamber while a trout fitter bolts it to the wrong outlet; the joint fails (10.5–12.2 s: spray across Boone's forearm, the fitter's wrench slips and he lurches); the water rises and soaks Boone; the apprentice carries a backward-running clock to the ledge; hand close-up 17–19 s; labelled black-and-white RECONSTRUCTION of an old stone arch 19–25 s; the fitter chalks the arch outline with chalk on a long lath from outside the arch (27.4–30.4 s), then walks back and climbs onto his step; the apprentice pries the patch (31–35 s); Boone swings the elbow toward the arch, re-grips one hand at a time onto the elbow's underside and side-steps right out from under the stream (31.4–35 s); bricks fall in (35.2–36.6 s); water pours into the arch, the pool drains over several seconds leaving a shallow residual; the fitter bolts the elbow's top flange to the spout (36.4–39.8 s) so it holds by itself; Boone lets go (40–41.6 s), still soaked.

Check that each round-2 fix is resolved: (1) elbow no longer floats after release; (2) Boone's head visible and water not appearing to come from his body after the swing; (3) characters clear of the arch outline (allow the apprentice's bar crossing the seam while prying); (4) wrench slip legible; (5) fitter's movement natural (walk + step-up, no slide/teleport); (6) forearm wetness visible mid-passage; (7) drain gradual with residual water; (8) right water column reads as a trickle not a wire. Re-confirm the round-2 PASS items still hold (flat wall before 17 s, arch registration, water into arch, label, fitter present in reconstruction, apprentice clearing, no artefacts). Note any NEW problems, ranked.

Write the report to /tmp/claude-0/critic_v3.md and return it in full. Be concise: criteria with PASS/FAIL + evidence, ranked remaining fixes, overall verdict. Distinguish blocking issues from polish.
```

## The report

Verdict: NOT YET. Seven of the eight round-2 fixes are resolved and every earlier PASS item still holds. One blocking issue remains: the "fitter bolts the elbow's top flange to the spout" beat is not on screen. Full report below; also saved at /tmp/claude-0/critic_v3.md.

# Critic report, round 3: tempus_fugit_passage_v3.mp4 (42 s, 24 fps, 1920x1080)

## Round-2 fixes

1. **Elbow no longer floats after release: FAIL (partly improved).**
   - What improved: `elbow_M` is fixed from about 39.3 s (x 1764.2, y 676.6) to 42 s. In the 640 px grabs at 40.5 and 41.5 s, the top of the elbow looks joined to the downspout.
   - What still fails at full resolution (crops at 37.4, 39.2, 41.2 and 41.95 s):
     - The elbow's top mouth is tilted about 35 degrees, opening up and to the right.
     - The downspout ends behind the right half of that mouth, offset by about half a pipe diameter. The two are not on one axis.
     - No flange contact, clamp or bolt is visible.
   - The fitter never works at that joint. From 36.3 to 39.9 s his wrench stays at Boone's head height, about y 400–430 in the 1080p frame. The joint is at about y 220–290.
   - After release (41.2–42 s), the top of Boone's head still overlaps the elbow's lower mouth by about 45 px. The elbow can still read as resting on his head.

2. **Boone's head visible, water not coming from his body: PASS.**
   - From 34.0 s to the end, his head and face are visible to the right of the lower mouth (34.0, 34.6, 35.2, 37, 38.5, 39.5, 41.5 s).
   - The stream leaves from the mouth's lower-left lip.
   - Polish: at 33.2–33.6 s, during the swing, the mouth covers his head and the water seems to start from his head.

3. **Characters clear of the arch outline: PASS.**
   - At 28.5–30.5 s the fitter chalks with the lath from outside the left jamb.
   - From 33.6 s the apprentice stands left of the left jamb; only his bar is inside the outline.
   - Boone stays right of the right jamb from 33.6 s on.
   - The fitter walks across the front of the outline at 31.0–31.6 s on his way back. As a foreground pass, this is acceptable.

4. **Wrench slip legible: PASS.**
   - The fitter's head, hat and wrench are now in view.
   - The wrench is up at the joint at 10.7–11.3 s.
   - At 11.5–11.7 s it swings down and to the left, and his body tilts and drops.
   - He recovers at 12.1 s.
   - Polish: the spray bursts to the right of Boone's hand and does not cross his forearm.

5. **Fitter's movement natural: PASS, with small notes.**
   - Walk: 30.42–32.3 s, about 560 units, with the thighs alternating (±0.5 rad, roughly 0.85 s cycle). Peak speed is 440 units/s, a brisk walk.
   - Step-up: 32.33–32.7 s, 70 units, along an arc.
   - There is no slide and no teleport.
   - Notes:
     - His y position pops 7 units in one frame at 30.42 s.
     - The feet may skate slightly.
     - There is a hard cut at 31.0 s (zoom 1.75 to 1.15) with him mid-stride; continuity holds across it.

6. **Forearm wetness visible mid-passage: PASS.**
   - At 26 and 30 s the forearms near the hands are clearly darker than the torso. At 6 s they are the same tan as the torso.
   - The hand close-up at 18 s reads dark and wet, with drops.

7. **Drain gradual with residual water: PASS.**
   - `pool_level` falls 95 (35.6 s) → 82 (36.5 s) → 68 (37 s) → 44 (38 s) → 29 (39 s) → 18.6 (40 s) → 12.9 (42 s). That is a decaying curve over about 6 s.
   - A shallow sheet of water is still visible at 41.5 s.

8. **Right water column reads as a trickle: PASS.**
   - It thins from several strands (33–34.8 s) to two (35.3 s), then one faint strand (35.7 s), then drips only from 36.0 s.
   - Polish: at 35.3–35.7 s it is still one or two straight hairlines. It also passes through the fitter with no splash.

## Round-2 PASS items, re-checked

- **Flat wall before 17 s: PASS.** At 0, 6, 14.5 and 16 s the wall shows brick, the wavy seam, then flat concrete.
- **Arch registration: PASS.** The chalk at 30.5 s matches v2 (seam x 135, chalk x 190–355, mouth about x 570 at 640 px). The reconstruction framing is also the same as v2 (arch x 150–300 at 21 and 24.8 s).
- **Water into the arch: PASS.** Water enters the arch from 36.2 s on. At 33.2–35.2 s it hits the still-closed brick, which works as anticipation.
- **Label: PASS.** It shows at 21 s and fades by 24.8 s.
- **Fitter present in the reconstruction: PASS.** He is in colour at the right at 21 and 24.8 s.
- **Apprentice clearing: PASS.** He carries the clock at 14.5 s and it is on the ledge at 16 s. Chips fall at 32.3–33.6 s, brick is exposed at 34.0–35.2 s, and bricks fall in at 36.2 s.
- **No artefacts: PASS.** The elbow wobbles by ±4 units on a cycle of about 0.33 s from 35 to 39.3 s. It reads as strain, not jitter.

## New problems, ranked

1. **Blocking: the repair beat is not on screen.**
   - The fitter's wrench works at Boone's head, not at the top flange where the elbow meets the spout.
   - That joint is offset and tilted, with no visible fastener.
   - Fix:
     - Line the elbow's top mouth up directly under the spout end, on one axis.
     - Move the wrench target up to that flange; this may need a taller step or a raised arm.
     - Add visible bolts or a band clamp.
     - Leave clear space between Boone's head and the lower mouth after 40 s.
2. Polish: at 33.2–33.6 s the mouth hides Boone's head and the water seems to come from his head.
3. Polish: the failure spray at 10.7–12.0 s does not cross his forearm.
4. Polish: the right column passes through the fitter with no splash (33–35.7 s), and it is briefly a hairline at 35.3–35.7 s.
5. Polish: the fitter's 7-unit y pop at 30.42 s, and possible foot skate.
6. Minor, carried over: in the reconstruction Boone stands on a stone block that is not there in the present.
7. Note: `contact_err` palm values are about 1e-13 throughout and switch to "released" at 40 s. They still do not prove the hands are visibly on the elbow.

## Verdict: NOT YET

Seven of the eight round-2 fixes are resolved, and all earlier PASS items hold. The one blocking issue is local: align the joint, move the wrench target up to the flange, add a visible clamp, and clear Boone's head at 40–42 s. Once that is done, this should pass.

Working crops and contact sheets: /tmp/claude-0/c3/ (sheet_slip.jpg, sheet_g.jpg, sheet_w.jpg, sheet_h.jpg, sheet_m.jpg, sheet_e.jpg, sheet_k.jpg, sheet_t.jpg). No project files were edited.

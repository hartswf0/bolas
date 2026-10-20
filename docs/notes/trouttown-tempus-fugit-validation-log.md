# Validation log: Trouttown: Tempus Fugit

Built from the files on disk by build_validation_log.py. The builder did not pass its own work: each passage verdict below came from a separate critic agent that saw only the renders, the frame grabs and the contact data.

## Deliverables

- `renders/trouttown_tempus_fugit.mp4`: 1920x1080 @ 24/1 fps, 208.38 s, audio: yes
- `renders/tempus_fugit_passage_v3.mp4`: 1920x1080 @ 24/1 fps, 42.00 s, audio: yes
- `renders/passage_v5_tail_33-42.mp4`: 1920x1080 @ 24/1 fps, 9.00 s, audio: yes
- `renders/thumbnail.jpg`: present
- `renders/youtube_description.txt`: present
- `archives/source_manifest.json`: present
- `validation/epistemic_ledger.md`: present
- `validation/limitations.md`: present
- `clips/brace_discover_redirect.json`: present
- `shots/manifest.json`: present

## Registered assets and atlases

- `atlases/boone_poses.json`: 80 sprites packed into 2048x4699; 80 carry sockets. Every rect was checked pixel-for-pixel against its source file at pack time, and the source files are kept.
- `atlases/props.json`: 9 sprites packed into 2048x720; 8 carry sockets. Every rect was checked pixel-for-pixel against its source file at pack time, and the source files are kept.
- `atlases/rig_boone.json`: 29 sprites packed into 2048x349; 29 carry sockets. Every rect was checked pixel-for-pixel against its source file at pack time, and the source files are kept.
- `atlases/rig_crew.json`: 48 sprites packed into 2048x649; 48 carry sockets. Every rect was checked pixel-for-pixel against its source file at pack time, and the source files are kept.
- assets/boone: 90 asset manifests; all have id and provenance
- assets/props: 8 asset manifests; all have id and provenance

## Contacts in the defining passage (brace_discover_redirect)

- left_palm: max 0.00, mean 0.000 world units over 921 gripping frames (Boone is ~390 units tall)
- right_palm: max 0.00, mean 0.000 world units over 921 gripping frames (Boone is ~390 units tall)
- left_sole: max 0.39, mean 0.237 world units over 921 gripping frames (Boone is ~390 units tall)
- right_sole: max 0.39, mean 0.028 world units over 921 gripping frames (Boone is ~390 units tall)
- What this measures: the distance between the solved hand or sole socket and its target socket on the collar or floor. After the release at 40.0 s the palm entries are marked `released` rather than reported as zero.
- Contact events (begin, change, lift, replant, release) and the ten authored states are listed in the clip manifest.
- Pool level: peak 95, at 41.9 s 13 (the drain leaves a residual sheet). The clock runs only while the water presses, frames 194–884.

## Independent review rounds

### Round 1 (passage v1)
Verdict: NOT YET. Faults: the arch was visible before discovery; the failure and the result were not shown; the damage did not read; the clock popped in; the fitter vanished in the reconstruction; the reconstruction was unlabelled; there was a stray diagonal artefact; the aftermath was static. All were addressed in v2.

### Round 2 (passage v2)
# Critic report: tempus_fugit_passage_v2.mp4 (42 s, 24 fps)

## Criteria

1. **Flat left wall before 17 s: PASS.** At 0, 3, 6, 9, 12.2, 14.5 and 16 s the left side is brick, then a wavy seam, then flat concrete. No arch moulding is visible.

2. **Reconstruction arch registered to the chalk outline: PASS.** The reconstruction (20.5–24.8 s) uses the same framing as 25.5 s (the elbow mouth is at about x 490 in both). In that framing the arch spans x 150–300. That is about 60 px right of the brick/concrete seam and about 190 px left of the elbow mouth. At 30.5 s the camera is about 1.1x closer (seam at x 130, mouth at x 570), so the arch should land at about x 196–361. The chalk is at x 190–355, top at y about 125. At 37 s the opened arch sits just right of the ledge's end, the same relationship as the reconstruction. Registration holds within a few pixels.

3. **Water through the elbow into the arch, right column thinning, floor lower by 41 s: PASS.** Water runs from the elbow into the opening at 33, 34, 35, 35.6, 36.2, 37, 38.5 and 40 s. The right-hand column is full at 34 s, thinner at 36.2 s, and a thin line from 37 s on. The pool level goes from 95 to 80 (36.0 s) to 13 (37.0 s) to 0 (39.0 s). The floor is dry at 38.5 and 41.5 s.

4. **Failure shown 10.5–12.2 s: PARTIAL, counted as FAIL.**
   - The spray is clear: droplets burst at the joint and water falls at 10.8, 11.0, 11.5, 11.6 and 11.8 s.
   - The wrench slip does not read. The fitter's head is hidden behind the elbow for the whole joint shot. His arm moves, but the wrench is a tiny grey bar at his shoulder and no slip is visible (contact sheet 10.6–12.2 s).
   - The spray falls straight down to the right of Boone's hand, not across his forearm.

5. **Soaked cardboard reads darker: PARTIAL.**
   - Legs: below the waterline they read darker from about 12 s, though part of that is the water tint. At 37–41.9 s the shins and boots are clearly darker than the torso.
   - Forearm: it is not visibly darker at 30.5 s (close crop shows the same tone as the torso), even though `arm_wet` = 1.0 from about 12 s. It reads darker only near the end, at 39.5–41.9 s.

6. **Apprentice clears the patch; clock carried and set down: PASS.**
   - The clock is carried 14.2–15.8 s and set on the ledge (14.5, 15.2, 16 s); it does not pop in.
   - The pry bar is in hand from 31 to 36 s.
   - Chips fall at 32 s, brick shows behind the patch at 33–34 s, and bricks fall into the opening at 36.2 s.
   - Minor: the apprentice already holds the clock at the ledge from 0 s, so the carry is short (about 120 units).

7. **Fitter present during the reconstruction: PASS.** He is visible in colour at the right at 19.4, 20.5, 23 and 24.8 s.

8. **Reconstruction labelled on screen: PASS.** "RECONSTRUCTION / drawn for this film, not a record" shows at 19.4–23 s and fades by 24.8 s.

9. **No strut or artefacts; aftermath not static: PASS, with notes.**
   - No diagonal strut appears anywhere.
   - The aftermath has motion: the flow continues, the arms release over 40–41.7 s and the camera drifts.
   - Two new problems sit in this stretch: the elbow hangs in mid-air after the release, and the right column renders as a wire-like double line (fixes 1 and 8 below).

Contact data: across 1.6–40 s, the largest palm error is about 1e-12 and the largest sole error is 0.38 units. However, the palm errors stay at about 1e-12 after 41.67 s, when the arm angles are all 0 and the hands are visibly off the elbow. So `contact_err` does not measure whether the hands are really on the elbow. Do not use it as proof of grip.

## Remaining fixes, most important first

1. **The elbow floats after Boone lets go (41.67–42 s).** `elbow_M` stays frozen at the same position from 39 s to the end. When the arms drop, nothing holds the elbow; it reads as resting on Boone's head. The fix is to seat it visibly (on the downspout end, wedged in the arch, or set down) or have it drop.
2. **Boone's head is hidden from about 33 s to the end.** The elbow is held over and in front of his head, so he reads as headless, with a pipe for a head. The water appears to pour out of his head and chest (crops at 37, 39.5 and 41.9 s). The upper mouth also faces sideways under the downspout instead of capturing it, so where the water enters the elbow is unclear. Restage so his head stays visible and the elbow clearly takes the downspout flow.
3. **Characters overlap the opening.**
   - At 30.5 s the fitter stands inside the chalk outline as it is drawn.
   - At 33–36 s the apprentice's bar and Boone's left side cross the arch jambs.
   - At 37–41.9 s Boone's shoulder and forearm overlap the right jamb.
   - Keep bodies clear of the outline so the shape reads.
4. **The wrench slip is illegible (10.5–12.2 s).** Re-frame or offset the fitter so his head, hands and wrench are visible during the slip, and make the slip a clear jerk. Optionally route the spray across Boone's forearm, as the brief says.
5. **The fitter moves unnaturally (30.5–31.25 s).** He slides about 340 units behind Boone in 0.75 s, about 450 units/s, with no walk cycle. He then jumps up 70 units onto the box in a single frame (31.17 s to 31.25 s).
6. **The forearm wetness does not show mid-passage.** `arm_wet` is 1.0 from about 12 s, but the forearm is not visibly darker until about 39 s. Darken it from 12.2 s on.
7. **The drain is too fast and too clean.** The pool goes from 95 to 0 in about 2.5 s (36–38.5 s), and the floor is then completely dry. Leave a residual sheet, puddles or wet staining.
8. **The thin right water column looks like a wire.** From 38 s it renders as two parallel hairlines. Make it read as a trickle.
9. **Minor:** in the reconstruction, Boone stands on a stone block that does not exist in the present.

## Verdict: NOT YET

The main problems from last round are fixed:
- the flat wall before 17 s
- arch registration
- the drain through the arch
- the label
- the fitter's presence in the reconstruction
- the apprentice's clearing
- the strut

The wrench slip still doesn't read. The forearm damage shows only at the end. Two new problems need fixing before this passes: the elbow hangs in mid-air after the release, and Boone's head is hidden behind the elbow through the payoff.

### Round 3 (passage v3)
# Critic report, round 3: tempus_fugit_passage_v3.mp4 (42 s, 24 fps, 1920x1080)

## Round-2 fixes

1. **Elbow no longer floats after release: FAIL (partial improvement).**
   - Improved: `elbow_M` is fixed from about 39.3 s (x 1764.2, y 676.6) to 42 s. In the 640 px grabs (40.5 and 41.5 s), the elbow's top looks joined to the downspout.
   - At full resolution the joint is not convincing (crops at 37.4, 39.2, 41.2 and 41.95 s):
     - The elbow's top mouth is tilted about 35 degrees, opening up and to the right.
     - The downspout ends behind the right half of that mouth, offset about half a pipe diameter. The two are not on one axis.
     - No flange contact, clamp or bolt is visible.
   - The fitter never works at that joint. From 36.3 to 39.9 s his wrench stays at Boone's head height, around y 400–430 in the 1080p frame. The spout joint is around y 220–290. So the beat "bolts the top flange to the spout" does not appear on screen.
   - After release (41.2–42 s), the top of Boone's head still overlaps the elbow's lower mouth by about 45 px, so it can still read as resting on his head.
2. **Boone's head visible; water not coming from his body: PASS.**
   - From 34.0 s to the end his head box and face are visible to the right of the lower mouth (34.0, 34.6, 35.2, 37, 38.5, 39.5, 41.5 s).
   - The stream leaves the mouth's lower-left lip.
   - Polish: at 33.2–33.6 s, mid-swing, the mouth covers his head and the stream seems to start from his head.
3. **Characters clear of the arch outline: PASS.**
   - At 28.5–30.5 s the fitter chalks from outside the left jamb, using the lath.
   - From 33.6 s on, the apprentice stands left of the left jamb with only his bar inside the outline.
   - Boone stays right of the right jamb from 33.6 s on (36.2, 37, 39.5, 41.5 s).
   - Note: the fitter walks across the front of the outline at 31.0–31.6 s while walking back. This is a foreground pass and acceptable.
4. **Wrench slip legible: PASS.**
   - The fitter's head, hat and wrench are now in view during the joint close-up.
   - The wrench is up at the joint at 10.7–11.3 s.
   - At 11.5–11.7 s the wrench swings down and to the left, and his body tilts and drops.
   - He recovers at 12.1 s.
   - Polish: the spray still bursts to the right of Boone's hand at the outlet (10.7–12.0 s). It does not cross his forearm.
5. **Fitter's movement natural: PASS, with small notes.**
   - Walk: 30.42–32.3 s, about 560 units, with alternating thigh swing (plus or minus 0.5 rad, roughly 0.85 s cycle). Peak speed is 440 units/s, a brisk walk.
   - Step-up: 32.33–32.7 s, 70 units, on an arc.
   - There is no slide and no teleport.
   - Notes: the y position pops 7 units in one frame at 30.42 s, when the chalk pose hands over to the walk. The stride may be slightly longer than the leg swing covers, so there may be mild foot skate. There is a hard cut at 31.0 s (zoom 1.75 to 1.15) with him mid-stride; continuity holds.
6. **Forearm wetness visible mid-passage: PASS.**
   - At 26 and 30 s the forearm segments near the hands are clearly darker brown than the torso. At 6 s they are the same tan as the torso.
   - The hand close-up at 18 s reads dark and wet, with drops on it.
7. **Drain gradual with residual water: PASS.**
   - `pool_level`: 95 (35.6 s), 82 (36.5 s), 68 (37 s), 44 (38 s), 29 (39 s), 18.6 (40 s), 12.9 (42 s). That is a decaying curve over about 6 s.
   - At 41.5 s a shallow sheet is still visible on the floor.
8. **Right water column reads as a trickle: PASS.**
   - Several strands at 33–34.8 s, two at 35.3 s, one faint strand at 35.7 s, then only drips from 36.0 s.
   - Polish: at 35.3–35.7 s it is still one or two straight hairlines for about half a second. The column also passes through the fitter's body with no splash or occlusion (33–35.7 s).

## Round-2 PASS items re-checked

- **Flat wall before 17 s: PASS.** At 0, 6, 14.5 and 16 s the wall shows brick, then a wavy seam, then flat concrete.
- **Arch registration: PASS.** The chalk geometry at 30.5 s is the same as in v2 (seam x 135, chalk x 190–355, mouth about x 570 at 640 px). The reconstruction framing (arch x 150–300 at 21 and 24.8 s) is also unchanged.
- **Water into the arch: PASS.** Water enters the opening from 36.2 s to the end. It hits the still-closed brick at 33.2–35.2 s, which is acceptable as anticipation.
- **Label: PASS.** "RECONSTRUCTION / drawn for this film, not a record" shows at 21 s and fades by 24.8 s.
- **Fitter present in the reconstruction: PASS.** He is in colour at the right at 21 and 24.8 s.
- **Apprentice clearing: PASS.**
  - The clock is carried at 14.5 s and is on the ledge at 16 s.
  - Chips fall at 32.3–33.6 s, brick is exposed at 34.0–35.2 s, and bricks fall in at 36.2 s.
- **No artefacts: PASS.**
  - The elbow wobbles plus or minus 4 units with about a 0.33 s period from 35 to 39.3 s. It reads as strain while held, not jitter.
  - The dark band at the right edge of the frame is consistent with the set and is not an artefact.

## New problems, ranked

1. **(Blocking) The repair beat is not on screen.** The fitter's wrench works at Boone's head, not at the top flange and spout joint. That joint is offset and tilted, with no visible bolt or clamp. Fix all four:
   - Make the elbow's top mouth line up on one axis directly under the spout end.
   - Move the fitter's wrench target up to that flange. He may need a taller step or a raised arm.
   - Add visible bolts or a band clamp.
   - Leave clear air between Boone's head and the lower mouth after 40 s.
2. (Polish) At 33.2–33.6 s the elbow mouth occludes Boone's head and the water seems to come from his head. Offset the swing path or the head by a few units.
3. (Polish) The failure spray at 10.7–12.0 s does not cross Boone's forearm, as the brief describes.
4. (Polish) The right column passes through the fitter with no splash (33–35.7 s). It is also briefly a hairline at 35.3–35.7 s.
5. (Polish) The fitter's y position pops 7 units at 30.42 s; possible foot skate on the walk.
6. (Minor, carried over) In the reconstruction Boone stands on a stone block that does not exist in the present.
7. (Note) `contact_err` palm values are about 1e-13 throughout and switch to `released` at 40 s. They still do not prove a visual grip.

## Verdict: NOT YET

Seven of the eight round-2 fixes are resolved, and every earlier PASS item still holds. One blocking issue remains: the payoff "the fitter bolts the elbow's top flange to the spout so it holds by itself" is not shown. The wrench works about 150 px below the joint, and the joint itself is misaligned with no fastener. This is a small, local fix (alignment, wrench target, a visible clamp, head clearance at 40–42 s). Once it is done, the passage should pass.

### Round 4 (passage v4, 29-42 s)
# Critic report, round 4: passage_v4_tail_29-42.mp4 (passage 29–42 s)

Evidence: the provided grabs (f_30 to f_41.8), my own full-resolution crops at 33.0–41.95 s (in /tmp/claude-0/v4c/), and `brace_discover_redirect.json` (elbow_M, pool_level, boone.rot).

## 1. Does the joint read as a spout-to-elbow connection? PARTIAL
- **Improved.** The gap is closed. From 33.5 s to the end, a dark piece runs continuously from the downspout end to the elbow's upper mouth (crops at 37.0, 38.5 and 41.95 s). The elbow is static from 37.5 s (x 1767.7, y 737.6).
- **Not a sleeve with clamps.** The dark piece is a flat inverted triangle with fan lines, so it reads as a funnel or hopper hanging off the spout. The "two band clamps" are drawn as two grey bars that form a "7": one across the top of the triangle, one running diagonally down its left edge to a bolt dot at the tip. They read as struts or a bracket, not bands around a pipe.
- **Axes still do not match.** The elbow is rotated 82.6 degrees (elbow_M). Its upper mouth faces right while the spout runs vertically. The triangle covers that 90-degree mismatch instead of wrapping one coaxial joint. Round 3 asked for the mouth to sit on one axis under the spout; this was not done.

## 2. Is the fitter's tightening at the joint legible? PASS
- From 36.5 to 39.5 s the fitter (`fitter_tool` = wrench) raises a long grey bar from his hand straight up to the joint.
- The hex head sits on the lower bolt at the tip of the triangle (crops at 37.0 and 38.5 s).
- The bolt is a small dot at 36.0 s and a large hex at 37.0–38.5 s. After the tool leaves, it is a larger round head at 41.95 s.
- The action now happens at the joint, not at Boone's head. At 960 px (f_37.5, f_39) it is a thin stick, but the reach up to the spout reads.

## 3. After release, is the elbow held by the joint rather than floating or resting on Boone? NOT YET
- The elbow does not move after release, so it no longer reads as floating.
- Boone's head still does not clear the elbow:
  - His lean is small: boone.rot goes from 0.02 to −0.09 at 41.0 s and −0.14 at 41.5 s.
  - At 41.95 s, the best case, his head box spans about x 1142–1245 and y 458–530 in the 1080p frame.
  - The elbow's lower barrel and mouth rim end at about x 1157 at that height. His head overlaps the barrel by about 15 px, and by more along the top-left corner of the box. No gap shows at any point from 40.0 to 41.95 s.
- The mass of the elbow sits left of and above his head, pressed against it (crops at 40.5 and 41.95 s, f_41.8). A viewer can still read his head as propping it up. This undercuts the payoff that the elbow now holds by itself.

## 4. Round-3 PASS items in this stretch
- **Arch clear: PASS.**
  - The apprentice stays left of the left jamb (34.5, 36, 39, 41.8 s).
  - Boone and the fitter stay right of the right jamb.
- **Water into the arch: PASS.** The stream hits the closed brick at 34.5 s, then enters the opening from 36 s to the end (f_36, f_37.5, f_39, f_41.8).
- **Gradual drain with residual: PASS.** pool_level goes 95 (35.5 s), 82 (36.5 s), 68 (37 s), 44 (38 s), 29 (39 s), 19 (40 s), 13.5 (41.5 s). A shallow sheet is still visible at 41.8 s.
- **Trickle on the right: PASS.**
  - Strands at 33.5–34.5 s, then drips only from 36 s.
  - Polish carried over: at 33.5 s the strands still pass the fitter with no occlusion or splash.
- **Boone's head visible: PASS.** His face is visible from 34.5 s to the end.
- **Apprentice clearing: PASS.** Chips at 33.5 s, exposed brick at 34.5 s, bricks falling in at 36 s, the opening clear from 37.5 s.

## 5. New or remaining problems
1. **(Blocking) Boone's head touches the elbow after release (40–41.95 s).**
   - Fix: move Boone's root right by about 50 units, or lean him further (rot of about −0.3 by 41 s), so that a visible gap of at least 20 px at 1080p opens between the head box and the elbow's barrel and lower mouth by 41.0 s.
2. **(Should fix; polish if the director accepts a makeshift join) The joint is drawn as a triangular funnel with a strut "7" instead of a sleeve with band clamps, and the elbow mouth faces sideways rather than up.**
   - Either rotate the elbow so its upper mouth is coaxial under the spout,
   - or draw the sleeve as a wrap that visibly covers both pipe ends, with two bands crossing it at right angles to the pipe.
3. **(Polish, carried over) At 33.0–33.5 s the stream seems to start from Boone's torso, left of the elbow mouth (crop at 33.5 s).**
4. **(Polish) The tightening is small at 960 px.** A short turn of the bar, or a brief two-frame push-in, would help.

## Verdict: NOT YET
- The main round-3 gap is fixed: the fitter now visibly tightens a bolt at the spout joint (36.5–39.5 s), and the elbow stays put.
- One blocking item remains: Boone's head is still against the elbow after release (40–41.95 s), so "it holds by itself" stays ambiguous. This is a small pose or position change.
- The joint geometry (a triangle bridging a sideways mouth, struts instead of bands) is the next-weakest point and should be fixed in the same pass.

### Round 5 (passage v5, 33-42 s): PASS
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

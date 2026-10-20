# The gust test · critic round 4

*Round 4 fresh check of repairs.* A separate agent that did not make the work, started Oct 18 00:42 EDT. Brief and report verbatim. File paths in the brief are the working paths on the day.

## The brief

```
You are an independent reviewer of a 7-second animation test of a handmade cardboard puppet. You did not make it. Judge only what you see; measure pixels where you can.

ANIMATION: /home/claude/puppet/review4/seq_1.png then seq_2.png = every second frame (12 fps), left to right then top to bottom, labeled. Full-size frames (1280x960): /home/claude/puppet/review4/full_f*.jpg. Stills, not playback.
SOURCES (real puppet): /home/claude/puppet/review4/source_07.jpg, source_09.jpg, source_10.jpg, source_05.jpg.
Method, disclosed: frames 0–21 are the unaltered photograph 09. After that, the puppet is that photograph cut into cardboard segments and rotated about its joints, except the viewer-right shin and foot, which never move and stay as photographed. Revealed background is reconstructed. The head's right side face is generated plain cardboard. Wind streaks and a soft contact shadow under the lifted foot are generated.

Check each item, PASS or FAIL with frame and pixel evidence:
1. The head side face (f038–f166) is a solid cardboard-coloured plane attached to the front face's right edge, following the head's tilt, with no background showing through or between, and the right pin entering it.
2. Beside the head on the right (f088–f166): no pasted rectangle of cloud texture and no hard-edged block in the sky. A soft blend into the ice edge is acceptable.
3. Where the right hand used to be (about x 880–1000, y 380–520 in full frames, f106–f166): no vertical bar or smear.
4. No pale halo or fringe around moved parts: the left leg at f049–f064, the lowered right arm and hand at f106–f166, and the torso and head edges.
5. The f021→f022 cut from photo to cut-out: list any visible change (edge trimming, colour, contact disc).
6. The viewer-left foot lands back flush on the box top and stays put. The viewer-right foot never moves.
7. Anything else that breaks identity or physical presence.
Then the single largest remaining gap, and whether the test is now fit to show as a first performance test (yes/no with one line). Under 400 words.
```

## The report

**Review of puppet test 4 (stills only)**

1. **Head side face: FAIL.** The side plane is solid and follows the tilt, but a pale strip about 6–8 px wide runs between it and the front face at full-frame x≈615–640, y≈95–180. At f166 the pixel at (618,130) is (166,179,187), which is the ice-blue background, while the cardboard on either side is about (35,22,5). So the two faces don't join, and background shows between them. The pin's flat head sits on top of the side face. It doesn't clearly enter it.

2. **Sky beside the head: FAIL.** f088–f166 have a hard-edged pale block at roughly x 872–990, y 435–500. At x=920 the colour jumps from (174,204,240) to (216,223,233) between y 448 and 456, a horizontal step. There is also a straight vertical edge at x≈872 that you can see in a zoomed crop. It reads as a pasted rectangle, not a soft blend into the ice.

3. **Former right-hand area: FAIL.** The same block sits inside x 880–1000, y 380–520 from f106 to f166. It isn't a thin bar, but it is a flat rectangle with a vertical edge where the original hand was.

4. **Halo or fringe: FAIL.**
   - f049: a pale sliver at the left knee, and light edging along the bottom-left of the thigh.
   - f059: a light outline around the lifted thigh and shin.
   - f106–f166: whitish edges along the lowered upper arm and the hand.
   - Torso right edge (x≈655–665): light fringing throughout.

5. **f021→f022 cut.** Mean colour is unchanged; torso, head and right shin all hold at about (36,22,11). A difference image shows changes only along the silhouette:
   - Edges trimmed all round. The white tape on the torso sides (x≈530–545 and 670–690) and on the thigh and shin edges is partly removed.
   - The needle at the left hand (≈300,150) disappears.
   - The scarf outline and the string at the right hand change.
   - The glue blobs where the feet meet the box are mostly kept.

   The edge trimming will read as a pop at the cut.

6. **Feet: PASS.** At f074 the left foot is back at the same x (≈475–545) as in f000 and sits flush on the box top. The right shin and foot show zero difference from f000.

7. **Other problems.**
   - From f106 on, the lowered forearm and hand cover the left of the two background hikers.
   - In f166 the hand hangs below the forearm with a visible gap of about 15 px at y≈520–540 (sky shows through the wrist), so it looks detached.
   - The generated wind streaks are crisp white dashes. Several cross the puppet's legs (f049, f059, f074), which breaks depth.

**Largest remaining gap:** the reconstructed sky rectangle where the right hand used to be (items 2 and 3). It is on screen for the last 2.5 seconds, next to the focal area. The head seam is close behind it.

**Fit to show as a first performance test:** No. The motion holds up, but the sky block, the gap in the head and the streaks crossing the legs show the compositing and pull attention from the puppet.

Crops and the f000/f022 difference image are in the scratchpad: /tmp/claude-0/-home-claude/4fcf2301-cc19-5f90-be19-3bb1b3367fc1/scratchpad/

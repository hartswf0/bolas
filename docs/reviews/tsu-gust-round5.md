# The gust test · critic round 5

*Round 5 fresh final check.* A separate agent that did not make the work, started Oct 18 00:51 EDT. Brief and report verbatim. File paths in the brief are the working paths on the day.

## The brief

```
You are an independent reviewer of a 7-second animation test of a handmade cardboard puppet. You did not make it. Judge only what you see; measure pixels where you can.

ANIMATION: /home/claude/puppet/review5/seq_1.png then seq_2.png = every second frame (12 fps), left to right then top to bottom, labeled. Full-size frames (1280x960): /home/claude/puppet/review5/full_f*.jpg. Stills, not playback.
SOURCES (real puppet): /home/claude/puppet/review5/source_07.jpg, source_09.jpg, source_10.jpg, source_05.jpg.
Method, disclosed: frames 0–21 are the unaltered photograph 09. From frame 22 on, the puppet is that photograph cut into cardboard segments and rotated about its joints, except the viewer-right shin and foot, which never move and stay as photographed. Revealed background is reconstructed. The head's right side face is generated plain cardboard. Wind streaks and a soft contact shadow under the lifted foot are generated. The real puppet has white tape along some edges and is backlit, so some pale edging is genuine: compare against frame 0 before calling it a halo.

PART A, before anything else: describe in 3–5 lines what the character does and feels, and what causes it. Rate how clearly the attitude change reads through the body alone, 1–5.

PART B, PASS or FAIL with frame and pixel evidence:
1. The head reads as one box: side face joined to the front face along one fold, no background between them, pin entering the side.
2. No hard-edged block, rectangle or bar in the sky beside the head or where the right hand used to be (f106–f166).
3. Pale edging around moved parts that is not present on the same edges at f000.
4. The f021→f022 cut: what visibly changes?
5. Feet: the viewer-left foot lands flush and stays put; the viewer-right foot never moves.
6. Wind streaks never cross the puppet.
7. Forearm and hand stay joined at the elbow (f106–f166).
8. Anything else that breaks identity or physical presence.
Then the single largest remaining gap, and: fit to show as a first performance test? yes/no, one line. Under 400 words.
```

## The report

**PART A.** For 22 frames the puppet holds the photographed pose: arms open and one hand raised toward the cave mouth, which reads as exultant. Wind streaks appear from f022. Around f050–f064 it braces: the viewer-left arm swings out level, the viewer-left foot lifts and plants again, and the head squares up. From f088 to f106 the head tips over toward its own left, away from the climbers. The viewer-right arm drops and hangs limp, and it holds that slump to the end. The change reads as exultant, then braced, then deflated. Nothing on screen causes the deflation: the wind thins out just as it slumps, and the pointing arm and the drooped arm send mixed signals. **Rating: 2/5.**

**PART B**
1. **PASS, with flags.** The side face joins the front face along one fold, with no sky between them, and the pin enters the side face (f064, f106). Two problems: a 2–3 px bright orange line runs down the fold (about x=715 at f064), which f000 does not have. And at f064 the tops of the two faces line up but the bottom of the side face is about 17 px higher than the front, so it does not read as a box in perspective.
2. **FAIL.** At f106 and f166 there is a darker filled patch in the sky where the hand was at f000. It has a hard vertical left edge at x≈944, y≈440–505. Row 470 steps from 214 down to 186–198 between x=940 and x=948, and the patch runs to about x=980.
3. **FAIL.** At f106 there is a 2–4 px whitish rim around the viewer-left thigh and shin, plus a smooth pale smear of background about 25 px wide left of the thigh (x≈470–500, y≈615–740). At f000 those edges are clean and speckled snow sits right up against them.
4. **The f021→f022 cut:** 15,768 px change by more than 30 levels, all along the outline (lighter 8,365, darker 7,403). The torso's pale left edge is trimmed about 4 px (at y=450 the dark edge moves from x=537 to x=541). A dark smear appears beside the shin (y=850, x=466–474 drops from about 230 to 70–125). The pins are redrawn. Playback will show this as the outline shrinking and shimmering on the cut.
5. **PASS.** Compared with f000, the viewer-right foot differs by a mean of 1.0 in every sampled frame, so it never moves. The viewer-left foot lifts at f049–f064 (diff 18–43), then from f074 on returns to 8.1, the same value as at f022, so it lands exactly back in place and stays. A dark band under the lifted foot at f059 reads as a slab more than a shadow.
6. **PASS** in the frames I inspected at full size (f064, f088, f106). Every streak sits in the background, including the one at (640,815) between the legs. I did not check every frame.
7. **PASS.** The forearm and hand connect through a pale tab, and the same tab is on the wrist at f000. There is a white sliver along the bottom of the hand at about (760–790, 640–650).
8. **Knee break:** at f106 the viewer-right thigh has moved but the shin is fixed, and there is a gap of about 5 px between the thigh's lower end (y≈735) and the knee block (y≈740, x≈685–722) with no pin bridging it. Physically, that leg is broken.

**Largest remaining gap:** the edges of the moved parts (the rims, the smears, the patch in the sky and the outline shift at the cut) show that it is a photo cutout. Close behind is the knee break.

**Fit to show as a first performance test? Yes,** as an internal test: the staging and pose sequence work. It is not ready for an outside audience until the edges and the knee are fixed.

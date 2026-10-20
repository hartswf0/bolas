# The gust test · critic round 1 · identity and physical presence tests

*Identity and physical presence tests.* A separate agent that did not make the work, started Oct 18 00:17 EDT. Brief and report verbatim. File paths in the brief are the working paths on the day.

## The brief

```
You are an independent reviewer of a 7-second animation test of a handmade articulated cardboard puppet. You did not make it. Judge only what you see.

SOURCES (the real puppet, photographed): /home/claude/puppet/review/source_07.jpg, source_09.jpg, source_10.jpg (front, backlit against a TV screen on a black box), source_05.jpg and source_01.jpg (side/rear views, earlier, no scarf).
ANIMATION: /home/claude/puppet/review/seq_1.png and seq_2.png = every second frame (12 fps), left to right, top to bottom, frame numbers labeled. Full-size frames: /home/claude/puppet/review/full_f*.jpg. These are stills, not playback; say when a judgment needs playback.
Method disclosed so you can check it: frames 0–23 are the unaltered photograph 09. After that, the puppet is the same photograph cut into its cardboard segments and rotated about their joints; the background behind moved parts was reconstructed; the head's right side face is reconstructed (not photographed); the scarf tail is the photographed tissue bent along a chain; small white wind streaks are generated.

Run two tests. For each failure give frame numbers, the largest gap, and an acceptance condition.

IDENTITY TEST: Does it stay this photographed object? Check the drawn face (two eye lines, smile), clear push-pin fasteners on both sides of the head, long rectangular torso, segmented limbs with dark joint connectors, block feet, white tissue scarf with torn fringe, torn edges and seams staying on their own surfaces, proportions. Flag anything added that the real puppet lacks, and anything that drifts or swims.

PHYSICAL PRESENCE TEST: support and contact (which foot carries weight, does a planted foot slide or sink, does a lifted foot clear the box top), joint pivots (do segments rotate about plausible joints, gaps or overlaps at joints), lighting consistency (backlit rim light), revealed background where parts moved (smears, ghosts, seams), scarf behaviour (does it respond to wind and body), camera.

Then: the single highest-leverage repair, and the strengths to preserve.
Format: IDENTITY: verdict + findings. PHYSICAL: verdict + findings. REPAIR: one. PRESERVE: list. Under 450 words.
```

## The report

IDENTITY: FAIL. The head breaks identity. The body passes.

- Head, f052–f166, worst at f059–f166. The reconstructed right side is drawn as a second, separate panel. A hard black vertical line and a visible gap divide it from the front face, so the head reads as two boxes, not one. The silhouette widens by about 25% (front face plus panel is roughly 210 px wide at f106, against 170 px at f000). The right push-pin now goes through a window cut in that panel, which the real head does not have (source_09, 10). Acceptance: one continuous box with a single folded corner edge, no dark seam line, total width within 10% of a correct foreshortening of the source, and the pin seated on the cardboard surface.
- Face lines and smile stay on the front face and do not drift between f000 and f166. Pass.
- Tone jump, f000 to f024: the frame description says frames 0–23 are the untouched photo, but every cut segment from f024 on is darker and redder than f000. The tan colour and the backlit edge glow are lost. Acceptance: mean segment luminance and hue within about 5% of f000.
- Torso, limb segments, joint connectors, block feet, torn edges and seams all stay on their own surfaces. Nothing swims. Pass.
- Scarf, f064–f068: a second white strip drapes over the right shoulder (it hangs below the scarf at x≈760–800, y≈260–350). It reads as a ghost copy of the scarf. Acceptance: a single scarf, fringe connected to the knot.

PHYSICAL: PARTIAL.

- Weight and contact: the right foot stays planted at the same pixels from f000 to f166, which is good. The left foot lifts at f052–f060, clears the box top, and lands about 17 px left of its starting spot. It casts no shadow and shows no contact darkening on landing. Acceptance: a contact shadow under the foot and no sideways slide after f070. Whether the landing reads as a step or a slide needs playback.
- Joints: the arms rotate about plausible shoulder and elbow points. The connector gaps stay consistent. Pass.
- Background repair:
  - From f096 to f166 the left hiker is erased, leaving a smear at f106 and nothing at f166.
  - There is a pale vertical rectangle seam at x≈930–960, y≈450–510, at f106 and f166.
  - At f024 there are blue box-shaped halos around both pins and white outlines around the shins and feet.
  - Acceptance: both hikers intact in every frame, and no edges outlined in rectangles or light halos when frames are flipped against f000.
- Lighting: the backlit rim is lost on cut segments (see the tone jump).
- Scarf motion: the tail bends with the head turn and the wind. Its timing needs playback.
- Wind streaks are small and do not get in the way.
- Camera is locked. Pass.

REPAIR: Rebuild the head turn as one rigid box. Either limit the turn to the angle the photographed front face can carry, or draw the side face as a continuous foreshortened plane with no black seam and correct width. This failure is visible in every frame after f052 and is the main reason the puppet stops reading as the photographed object.

PRESERVE:
- The planted right foot as the fixed anchor
- Rotation about joints with the connector gaps kept
- Face lines that stay put
- The torn edges and seams carried with each segment
- The locked camera
- The understated wind streaks
- The scarf tail following the body

Two still-only judgments need playback: the left foot's landing (step or slide) and the scarf timing.

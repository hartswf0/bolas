# SCION 06 · critic round 2 · DOES NOT PASS (narrowly)

Method. I rendered the film headless at 1280x720 through window.PAE_SEEK: 393 frames, one every 0.5 s across 0–32 s plus every frame in the ten windows. I read them as contact sheets and as full-resolution frames, and checked the 390x844 layout once. I judged the picture before reading window.PAE_CHECK, and read the source only for PAE_SEEK and to verify the cards. I read round1.md only after writing the per-choice judgments below.

Material and lineage. Everything visible is points of light: a teal dotted outline, cream flour dots, a dotted knife and plate, and an amber dotted penny. The flour total is 996 in every frame, and the sack gains exactly the 396 dots the plate and air lose. The sack's outline is a harmonic sum (sin/sin3 gravity terms, cos2/cos4 width and shoulders, two Fejer peaks for the corners, a crown-dip sum) sampled as dots. Its mood shows in its own dots: the interior drifts from ragged stipple when detuned toward clean spiral and radial order when locked. The round-1 one-frame regime swaps are gone. Consecutive frames now change continuously; I checked 6.79–6.92 and 4.00–4.12 frame by frame, and PAE_CHECK gives a maximum interior jump of 0.059 at 4.08. The body is moved by damped oscillators retargeted at score times, and the gait and grain flights are named on the card as scheduled. Built and moved in the lineage's language: yes, with the exceptions in the next paragraph.

Claims. The card names two scheduled things: the cycloid gait blocks and the grain phasors. Two more scheduled paths are not named. (a) The penny from 21.0 to 22.4 is a cosine-eased interpolation between two fixed endpoints, the tower top and the catch point, plus a 0.26 m sine arc (pennyAt, source lines 284–286). That is a tween in everything but name. On screen it also makes the penny rise about 0.3 m after the tower is cut (0.915 at 21.0 to 1.23 at 21.9) before it drops, so it reads as tossed up, not as falling. (b) The knife strike is a fixed ((1-cos)/2)^10 window over 0.5 s at each cut time (kpulse), not a spring. The bar says any scheduled path must be named on the card. These two are not, so that claim is false as published.

Choices.
- Flinch (1.00): reads. At 1.00–1.04 the sack squashes wide and low (29%), shifts left, rebounds tall by 1.12, and settles by about 1.3.
- Flinch less (4.00): reads. There is a visible squash at 4.04 (about 15%), a smaller shift left (−0.07), and a rebound at 4.12. It is clearly smaller than flinch 1.
- Notice (6.5): reads. At 6.58–6.79 the corners shoot up, the body rises and narrows, and it tilts slightly toward the tower. This comes before any travel.
- Come head low (9.0–14.0): reads, narrowly. From 9.17 the whole body tips forward toward the tower, the rear corner is high, the leading corner is low and ahead, and seven hops carry it. The hop clearance is small but visible, about 13 px at 1280. It reads as decided. The silhouette at 9.25–9.6 and 10.5–11.5 is an odd forward-tipped shell with the leading corner jutting like a snout, though the base stays flat.
- Prop (14.5): reads, weakly. From 14.6 the sack's right flank flattens against the tower's leaning face, low and wide. The trace holds the lean at 0.146 against a driven 0.31 through 15–18, but the lean is small enough that the eye has to work to see the hold.
- Brace (18.0): reads. At 18.04–18.2 the sack compresses hard (height 0.534 to 0.434) and holds against the face through 20.9. Two things weaken it. The sack's centre slides back about 0.07 m (x 0.293 to 0.226) while the right edge stays on the face. And the tower's lean doubles at the cut (0.15 to 0.31), so the tower is not visibly stopped. It reads as the sack being loaded more heavily, which is acceptable.
- Leap (21.4): reads. The sack is squat at 21.42, stretched tall and off the table by 21.50–21.54, and the corners whip.
- Catch (22.4): reads. The penny settles into the notch between the corners at 22.17–22.3 and stays there through the landing.
- Land (23.0): reads. There is a wide squash at 23.08–23.25 with the penny on top and a two-sided dot cloud.
- Gather (24.5–28.5): reads, and is the best passage. Grains leave the pile in arcs into the sack, the plate empties, and the sack rises to 0.94.
- Stay (30.0–31.2): reads. The sack is full and still at x 0.80, the knife hovers about 0.19 above the penny, and it withdraws at 31.25–31.38. The withdrawal takes about three frames, which reads as a yank.

Does the sack read as a flour sack in every frame? Mostly. Act 1 (0–6.5) is now right: the lower third is wider, the bottom is flat on the table, two corners sit over a dipped crown, and it reads as a half-empty sack. The approach reads as a tipped sack. The frames that fail are three runs:
- 18.1–21.0: a long low slab with a squared right end and a single hump, like a slipper or shoe. The second corner is lost in the face contact, so there are not two corners (see 18.25, 19.0, 20.5).
- 6.8–8.9 and 22.0–22.9: tall pointed upright corners over a V crown read as a cat-head or owl silhouette.
- 27.5–32: the full sack has the same pointed ears and reads more as a cat or owl than as a tied flour sack. The pooled bottom helps but does not cancel it.
None of these runs reads as a generic blob, a heart or a Lissajous figure. They are recognisably the same character, but the corner shape drifts toward the animal. The line of action is legible in notice, approach, prop and leap. In the final stand it is a vertical, which is correct.

Craft defects.
- Act 1 is small in frame. Its tower is legible now, and the cuts at 1.0 and 4.0 are visible.
- After cut 3 (18.1–21.0) the tower reads as a curving plume of dots, not a packed tower. Its top arcs out over the sack and the penny hangs on the plume.
- The penny rises after the collapse (see Claims).
- The knife exits in about three frames.
- At 390x844 the film fills the top half and the page does not scroll (scroll height 844). The flour counters, phasor inset and check table sit below, and the table scrolls inside the panel. The layout is acceptable.

PAE_CHECK compared with the picture. All onsets fall within 0.21 s of the score; the largest offset is "stays" at 29.79 against 30.0. Volume stays within 1.2% outside the gather, flour is conserved, the penny stays on top, and the end is at x 0.80, height 0.94. The numbers agree with the picture except in two places. braceRetreat reports −0.009, but the trace x falls 0.07 m from 18.0 to 19.0. And the lower-over-upper shape metric passes every frame before 21, while the 18–21 slab has lost a corner, which that metric does not measure.

Round 1's five repair conditions:
1. Lower third wider, flat bottom, two corners from 0 to 21: met for 0–18. Not met for 18.1–21.0, where one corner is lost.
2. Interior regime flicker: met.
3. Head low and visible hops: met. The lean is forward and down, and the hop clearance is about 13 px.
4. Flinches: met. Squash 29% and 15%, stretch-back, hop ends at 1.3.
5. Brace: compression met (19%, held). The tower lean holding visibly is not met: the lean steps from 0.15 to 0.31 at cut 3.

Verdict: DOES NOT PASS (narrowly). The picture is now close to a pass: all ten choices read, the material language is consistent, and the round-1 flicker and Act 1 shape faults are fixed. It stops short for two reasons. The film's own card is untrue about what is scheduled: the penny's flight is a tween that the card does not name. And the brace slab loses the sack's two corners for 3 s.

Repair conditions, ranked:
1. Make the claims true. Either name the penny flight (21.0–22.4) and the knife-strike pulse on the "Moved by" card as scheduled paths, or drive the penny with an integrated oscillator or ballistic step. In either case the penny's height must not rise after 21.0; it should fall monotonically from the tower top to the catch.
2. From 18.0 to 21.0, two distinct corners must be visible above the crown in every frame. The face contact may flatten the flank, but not the near corner. Check 18.25, 19.0 and 20.5.
3. Brace without retreat: the sack's centroid x must move by less than 0.02 m between 17.9 and 20.9. PAE_CHECK.braceRetreat must be computed from that centroid, so it agrees with the trace.
4. The corners should read as sack corners, not ears. At 7.5, 22.5 and 30.0, each corner peak's height above the crown dip should be at most about 1.5 times its base width, with rounded tips, so the figure stops reading as a cat or owl head.
5. The tower holds at the prop and the brace: from 14.6 to 20.9 the drawn tower lean should change by less than 0.03 rad. In particular it must not step at cut 3, so the viewer sees the sack stop it.

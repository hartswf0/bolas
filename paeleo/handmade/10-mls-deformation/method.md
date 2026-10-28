# SCION-10 · Schaefer, McPhail & Warren — MLS Deformation · PAE-02 the threshold

## The swarm and its language

Lineage: *Image Deformation Using Moving Least Squares* (Schaefer, McPhail & Warren, SIGGRAPH 2006). The native formal
language is the paper's: **control-point pairs, line-segment handles, local weighting (w = 1/|p − v|^2α), the affine /
similarity / rigid families, feature protection**. The theorem the swarm proves here: an artist moves a few landmarks and
the image between them follows as a continuous sheet; the family is chosen by what the material does.

The swarm's roles were merged into one builder (this file's author): MLS mathematician (build/mls.py), landmark placement
(build/pose.py, build/dog.py `place`), contour designer (the hide and its handle set, build/paint_dog.py), fast evaluator
(lattice evaluation, build/dog.py `Hide.warp`), counterexample hunter (the strips in proof/). **No independent critic was
run by me**; the brief assigns that to an outside critic. I do not approve this film.

## What the dog is made of

**One image.** `assets/dog_hide.png` is a dog's coat painted flat in numpy, laid out like a pelt: the dark saddle down the
middle, both flanks to either side, the four legs reaching out from the flank edges, the head with eyes, nose and ears, the
tail. It is 760 × 528 px at 400 px per metre. Nothing else of the dog exists: **no skeleton, no cut pieces, no second
drawing, no frame swaps.** (The kit's archive dog was looked at once; a side-view frame was rejected because it cannot
turn its back without a mirror — similarity and rigid MLS cannot reflect, and affine MLS passes through an edge-on sliver,
exactly the collapse the first six swarms were failed for.)

**The handles.** 48 point handles and 19 line-segment handles sit on the hide (proof/handles_on_hide.jpg, and on the end
card): the spine (tail base → croup → mid-back → withers), the back edges and the belly line on both flanks, the neck, each
leg (belly → knee → paw), the tail, and a cluster of 15 head handles (skull, crown, cheeks, eyes, jaw, muzzle, nose, ear
bases). The line-segment handles are the paper's second handle type; I integrate their weight with 3-point Gauss quadrature
along the segment instead of the paper's closed form (stated, not hidden).

**The warp.** Every frame the handles get 3D targets (porch x, y and height z) and the whole hide is solved by **affine MLS
from 2D to 3D** (the affine formula is the same matrix solve with a 3-column right-hand side). The flanks fold down into
sides, the legs reach down to the boards, the head stands up on the neck: a pelt becomes a body. The paper's solve is
evaluated on a 6-px lattice of the hide and bilinearly interpolated between lattice points, as the paper does. Normals come
from the lattice's own derivatives, so the lifted sheet is lit like a surface. The sheet is point-splatted in depth order
with the person and depth-tested against the set (walls, jambs, sill).

**Which family, and why (looked at).** proof/variants_strip.jpg and the end card show one pose, the same handles, in the
three families (x, y by the family; height by affine): similarity thins the legs to threads; rigid swells and wrinkles them;
affine keeps the hide's parts in proportion and is the only one that can fold the flanks under the back. The film uses
affine. **Feature protection** is done in the paper's way: the head's 15 handles move together as one rigid transform
(yaw and pitch of the head), so near the head the affine solution is that rigid motion and the face does not shear.

**Weight exponent (measured by looking).** proof/alpha_strip.jpg: α = 1.0 / 1.3 / 1.6 / 2.0 on a retreat pose and a lying
pose. Below 2 the far flank spikes between handles (a row of points on the back line pulls the sheet into teeth); α = 2.0
is smooth. ALPHA = 2.0.

## How it moves (the score → the handles)

`build/pose.py` reads the score frame by frame and moves only handles:

- **Position.** The body centre is at porch x_world = x_score − 0.49, on a line 0.12 m to the far side of the doorway's centre
  (so the lying dog is not hidden by the near jamb). The approach covers 3.41 m in the score's 9.1 s at the score's pace;
  the retreat goes the other way.
- **Gait.** Paws are handles that stay where they were put on the boards until the body has moved too far from them
  (7.5 cm), then step on a diagonal (0.24–0.30 s swings, 7 cm lift); the diagonals alternate; when the body turns faster
  than 1 rad/s all four may step quickly (0.15 s). 86 footfalls; each one is a tap in the sound. Held paws do not slide.
- **Turns are rotations of the handle set** in the floor plane, plus a curl of the centre line (1.3 rad/m at mid-turn), with
  the head leading. The refusal turn passes through facing the camera (we see the face going away from the door) and is
  led by the head from 3.42 s so the back is shown by 3.9 s (lesson of the first six). At 7.46 s the head comes round
  first, 2.1 rad over the shoulder toward the door and the camera, while the dog is still lying; the body gets up and
  follows from 7.85 to 8.85 s (the score's own turn crosses 0 at 8.1 s). In both turns the rubber-sheet quality is honest:
  the neck sheet twists and the flank on the inside of the curl compresses (proof/turn_away_strip.jpg, turn_back_strip.jpg).
- **Posture.** Crouch lowers withers and croup (hind lower when afraid), ears flatten (ear tips drawn back and down), the tail
  tucks (tail handles swing down and under the belly). Head height = withers + (head − 0.75)·0.85 so the approach head
  (score head 0.45) is ~0.26 m below the back line for the whole approach.
- **Lying.** The sphinx: the belly line goes to the boards and spreads, the front paws reach forward, the hind paws come
  forward beside the hips, chest at 0.30 m, croup at 0.21 m, the tail sweeps to the side on the boards. Across the sill: the
  chest and forelegs in the door frame, the head inside the doorway, hindquarters and tail on the porch.
- **Looking in (26.4 s).** Lying, the head first rests turned toward the person (1.25 rad toward their side); on *come in*
  the head lifts and swings to point straight into the lit room — from our camera we see the back of its head and the
  ears against the light — then lowers and settles, still there.

## The world

A porch at dusk seen from the street side, a little above (orthographic camera, yaw 36°, elevation 34°). Two fixed
framings and one cut: the wide shot (200 px/m) holds the whole porch until 21.5 s; then a closer shot (330 px/m, same
direction) on the sill for the end of the approach, the lie-down and the look-in. Because the scale changes at the cut,
trace.json carries x_world_measured (the rendered trunk centroid along the porch, in score metres), which the checker uses. Ray-cast in numpy plane by plane: boards, steps, railing, the house wall with clapboards, the doorway with
its jambs and sill, the door leaf, the room (floorboards, a rug), the yard. The lamp inside lights the porch only through
the doorway and past the leaf; when the door opens (6.2–7.0 s) the light comes out across the boards. The person is a
faceless figure of shaded capsules: calls from the doorway, reaches, steps out and aside, sits against the wall beside the
door, offers a hand low. Captions are the person's spoken words only; nothing on screen names the dog's state.

Sound (build/sound.py, all synthesized): room tone (wind, crickets), a formant voice (*Come here* ×2 loud; *It's all right*
×2 and *Come in* soft), the paws' taps at every footfall, nails scrabbling in the turns, the body going down and a breath,
tail thumps when it looks in, the latch and the creak, the warm room's hum and a clock. Measured (proof/sound_levels.json):
calls ≈ −19.7 dBFS, soft words −28.8 … −30.8 dBFS (≥ 8.9 dB quieter), room tone −41.6 dBFS (soft words ≥ 10.8 dB above it).

## What is protected (invariants) and how it was tested

- PAELEO I1–I4: `tools/paeleo/check_handmade.py` on trace.json (results in invariants.json).
- **Measured, not copied**: trace.json is written from each rendered frame's own buffers (cache/raw/*.json from render.py):
  the dog's visible-pixel centroid after the depth test (x_screen, y_screen), the rendered trunk and head samples in world
  metres (facing = head toward the door from the trunk; back and head heights), velocity of the rendered trunk. The state
  column is inferred from those measurements (rules in build/measure.py), with the score's state kept beside it. Onsets in
  proof/onsets.json.
- MLS numerical invariants (proof/mls_selftest.json): handles hit their targets, identity and rigid motions reproduced.
- One artistic achievement judged only by viewing: whether the lifted pelt reads as one living dog in every frame of the
  turns and the lie-down — that is for the critic.

ONSETS_PLACEHOLDER

## What failed and what I changed

See ledger.jsonl (17 entries). The decisive ones: the first turn folded the hide into a tangle (curl too strong, paws left
behind) → softer curl and quick steps while turning; the gait gave every step to one diagonal → alternation; the back
silhouette grew teeth between handles → line-segment handles and α = 2; the dog turned grey and box-like in the dusk light →
light that keeps the coat's colour and a dog's section (deep chest, tucked belly).

## What is still weak (my own view, not a verdict)

- The dog is small in the wide shot (about 260 px long) until the cut at 21.5 s; the face is not readable in detail there.
- The legs are rubber: tubes from the flank, no joints; in the turns a front leg can stretch and sweep.
- At 8.2 s the head is ahead of the body by 120° and the neck sheet twists across the shoulder.
- Ears are thin in profile; the half-flat ears of the approach read as small wings.
- The lying hind legs splay sideways more than a real dog's.
- The voice is a formant synthesizer: the words are recognisable mainly with the captions.

## What I did not do

- No independent critic was run; no human viewing. I looked at extracted frames and strips only (not normal-speed playback).
- The paper PDF was not fetched in this session; formulas were written from the paper's published equations and verified
  numerically, not against its figures.
- No closed-form line-segment integration (quadrature instead). No rigid or similarity MLS in the film itself (shown only
  in the comparison). The person is not an MLS sheet (capsules). No mobile operator page.
- A scratch-file name collision in the shared scratch directory once showed me a contact sheet from another swarm's film;
  I did not use it, and moved my scratch files to a private folder.

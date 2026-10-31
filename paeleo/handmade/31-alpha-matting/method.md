# SCION 31 · Alpha Matting — the threshold, handmade

PAE-02, cohort 4. One agent working alone in this folder with the SCION 31 prompt (Alpha Matting: Hair, Lace and Smoke
Swarm) and `paeleo/handmade/BRIEF.md`. The SCION hard proof (a lace veil and engraved hair, rotated over light, dark and
moving backgrounds) is replaced by the brief's scene; its bar, inquiry and doctrine were kept.

## Thesis

The dog at the threshold is a real dog from a 1930s-era New Jersey home movie, lifted out of its sunlit gravel path by
solving its matte, and set down on a porch at dusk. Everything the viewer sees of it is the archive's own fur, carried
across the edge without the old daylight coming with it. The defining passage is the end: the dog lying across the sill
in front of the lit doorway, its fur edge lit from behind, its head turning in. What would make it bland: a cookie-cut
outline (a hard SAM polygon pasted on a background), a halo of sunlit gravel round the fur, or a dog that is a texture
poured into a drawn shape.

## Native formal language, as built

Typed primitives, all in `build/lib_matte.py`, kept as files in `build/cache/` (regenerable):

| primitive | type | where |
|---|---|---|
| **Trimap** | int8 (H,W): 1 sure foreground, 0 sure background, −1 unknown | `trimap()`: SAM outline (or a hand-drawn outline in `build/polys.py`) eroded/dilated by edge-class widths |
| **Fractional alpha** | float (H,W) | `solve()`: colour-line projection of each unknown pixel onto its local F–B line (F and B extended into the band by normalized convolution), confidence-weighted against the outline prior where F≈B, guided filter (He) refinement, a mild 0.06–0.94 curve so no unintended veil remains |
| **Foreground-colour estimation** | float (H,W,3) | inversion of the compositing equation where alpha ≥ 0.6, extended interior colour where alpha ≤ 0.12, blended between |
| **Decontamination** | — | the recovered F replaces the observed pixel in the edge band; F is clamped to ±0.15 of the extended interior so a bright gravel speck read as fur does not carry its brightness; the clouds' blue sky is removed from their F |
| **Premultiplied alpha** | float (H,W,4), rgb ≤ a | every layer is stored, scaled (`resize_premult`), rotated (`rot_premult`), interpolated between frames and composited (`over`) premultiplied; light is added as emission (alpha 0) |
| **Edge texture** | — | fur kept from the solve (narrow band, small eps); grain renewed per frame inside alpha only; edge colour match: an edge pixel may not be lighter than the solid fur beside it; light wrap only from what is behind the dog in depth (wall, doorway, sky; never the floor), unblurred, so fur glows only where light really is behind it |

Edge classes (the method library's first entries, each with its own trimap widths and solver settings):
fur (dog: erode 2 / dilate 3), hair + fabric (woman: drawn outline, erode 4 / dilate 3), skin on black (hand: erode 7 /
dilate 4), painted wood (door leaf: erode 1 / dilate 2), sheer curtain (luminance-keyed fabric density in the door
window), smoke (clouds: trimap from saturation, guided filter r2, sky blue removed), foliage (computed tree line: a
fractional matte from fbm and leaf noise).

Coordinates and time: scene frame i = score frame i, 24 fps, 768 frames. Screen x = 330 + 190·x_score (camera static, the
threshold at x 330, the door opening 243–417, the porch steps at 1261). Source frames are 384×288, 12 fps; the dog is
composited at 1.55× in premultiplied form. Seed 31.

Numerical invariant (tested): premultiplied colour never exceeds its alpha (`premult_ok`): all 50 dog mattes, every
world matte, and all 96 stress-fixture frames pass (`build/cache/dog/log.json`, `build/cache/world_log.json`,
`proof/edge_log.json`). The edge log also checks for a bright rim (band foreground luminance > core + 0.08): 0 of 96.
Artistic achievement judged only by viewing: whether the fur edge reads as fur at dusk, without a pasted outline.

## The swarm (merged roles, one agent)

The prompt's six roles were merged because one agent did all the building: trimap designer (SAM outlines, the drawn
woman and forearm outlines), matte solver (`lib_matte.py`), hair/detail specialist (the fork below, the F clamp),
composite background tester (`build/stress.py`: light / dark / moving checker while the archive dog turns and the matte
rotates ±25°), image fidelity reviewer (me, looking at frames). **The independent edge critic has not run**: the brief
says an independent critic will judge the film; I did not approve it.

## How the dog is built and moved

**What it is made of.** 10 frames of the archive dog (*Amateur Film New Jersey C*, Home Movies, Internet Archive, public
domain) appear: 9, 13, 14, 26, 30, 33, 45, and, for heads only, 5, 28 and 31. All 50 are matted.

**How it moves: substitution of whole matted frames, chosen by the score.**

- *Watching* (0–1 s, 2.33–3.42 s): held frames 9 and 13, the grain renewed each frame. The long watch (8.8–14.7 s)
  shifts among the archive dog's own frames 12–13–14 (its small attention changes), never a frozen still.
- *Backing away* (1.0–2.33 s), **rebuilt in repair round 2**: first the head ducks. Frame 13 is cut along a soft
  diagonal from the chest to the withers, and its head and neck pivot down about the withers (0°, 18°, 36°, 54°), held
  where it stands so its paws do not move. Then a **backing gait made from one matte**: frame 45 (head low) mirrored to
  face the door, split into body, fore pair and hind pair, overlapping under the body. The body follows the score. Each
  leg pair is sheared so its paw stays planted for 70% of a 0.22 m step while the body moves back over it, then lifts
  and steps back for 30%. The pairs are half a step apart. The gait starts 30 px and ends 26 px off the score, easing
  to it over 9 frames, so its head meets the bridge drawings. That offset is fed to the leg solver as body travel, so
  the planted paws still hold while it closes. At the stop, the bridge plays in reverse (54°, 36°, 18°) into frame 13.
- *Turning its back* (3.42 s): a turn **through the dog's front**, chosen from its own frames at 12 fps: 14 (three-quarter
  left), 26 (facing the camera), then 30 and 33 (frontal body, head three-quarter right with a clear muzzle and ear), then
  frame 9 mirrored (profile, facing away). The head goes left → centre → right and never jumps sides. Then it **lies down
  with its back to them** (score lie = 1 from 4.5 s) and lowers its chin. (Repair round 1: the archive's own turn, frames
  16–22, read as dark tangles and was dropped. Repair round 3: 28 and 31 replaced by 30 and 33; their heads were soft
  masses.)
- *Turning back to look* (7.46 s), **repair round 3**: the body stays down while the head comes round through the dog's
  front over five frames. The steps are the away-facing head lifted off the paws, then the heads of frames 31
  (three-quarter right), 28 (front) and 14 (three-quarter left), each cut by a soft box and seated on the lying dog's
  neck, then the level door-facing profile at 7.625 s. Under a bridge head, the top of the old head (an ear-tip rim) is
  cleared from the body so nothing is left floating. The dog rises (7.66–8.0 s), then turns back through its front:
  33 and 30 mirrored (frontal body, muzzle toward the door), 14, 14, then the watching frames.
- *Coming, head low* (14.71 s), **repair round 3**: the head lowers through the same bridge drawings as the retreat's duck
  (frame 13, neck pivoted 18°/36°/54°). Then it walks on the **planted-paw gait** (frame 45 mirrored, head low), run
  forward with a 60% stance: paws hold while planted and step forward lifted. The approach has no held-drawing changes.
  The four archive walk drawings (43, 44, 45, 48) were dropped: their feet could not be registered within 15 px, because
  frame 48 hides the front leg that frame 43 plants.
- *Lying across the sill* (23.79 s) and *looking in* (26.4 s): **a labelled reconstruction.** The archive dog was never
  filmed lying. It is built from frame 9's matte (profile, head up), with heads from frames 5, 14, 28 and 31 and a tail
  tuft from frame 13, as the end card says. Frame 9's matte is split by complementary soft masks into body, two forelegs,
  hind legs and head; the forelegs pivot forward at the elbows onto the floor, the hind legs fold (compress) under the
  haunch, the body lowers, the head stays up (sphinx), then is **substituted** by frame 5's head, which the camera saw from
  behind (the dog looking up and away: back of the skull and ears toward the viewer), then pivots down to rest the chin
  on the paws (28.2–28.9 s). The belly cut is given a synthesized strand fringe (reconstruction, labelled here and on the
  end card). While lying facing the door the matte is set 48 px further in, so its head and forelegs are inside the door
  frame and its haunch and tail outside.

**The rest of the world.** The woman is a matte of the woman in *Straight Talk* (NTIS 1992, public domain), seen from
behind at her door, graded to a near-silhouette for dusk; her legs are drawn (the source is cut at the thigh). Her reach
and her low offered hand are the matted hand and forearm from *Door to Heaven* (1941, public domain). The door leaf and its
curtained window are the leaf from *Straight Talk* frame 31, rectified; the room light passes through the curtain's
fabric density. The clouds, and the density of the haze in the door's beam, are the 62 frames of *Top of the Cloud*
(public domain) matted as smoke and interpolated premultiplied. House, porch, sill, steps, sky, tree line, room, door
light, the dog's cast shadow (its own alpha projected onto the floor away from the door light) and grain are computed.

**Sound** (synthesized, `build/sound.py`, no recordings): dusk air and crickets; a synthesized voice (additive harmonics
under formant envelopes: "come here" ×3, "it's all right" ×2, "come in"); claws on the boards at every walk-frame change
measured in the render trace; a scrabble as it rises; fur on wood and a soft thump as it lies down (4.45 s, 24.0 s); the
person's steps and cloth as she moves aside and sits; the door's creak (6.2 s) and the room's warm air after it opens; a
sigh as it settles (28.55 s). **I cannot listen**: levels below are measured, how it sounds is unknown to me.

## Protected conditions (measured: see the end of this file, `trace.json`, `invariants.json`)

The six choices at their times; the dog never past the sill in the score's x; lying across the threshold at the end;
screen x following the score; back turned during the refusal; the soft voice ≥ 6 dB below the calls and above the room
tone; premultiplication correct; no bright rim from the source daylight.

## What failed and what I changed (full list in `ledger.jsonl`)

1. First fur matte over-blurred (wide band, large eps): a smoky veil. Forked three hypotheses (`proof/fork_fur_ABC.jpg`);
   promoted B (narrow band, small eps, alpha curve). Bright gravel specks near the paws were fixed in foreground recovery
   (the F clamp), not by blurring the matte, as the SCION inquiry says.
2. The woman's loose drawn outline put the white door into sure-foreground (a pale smear in her hair). Redrew a tight
   outline from a gridded zoom.
3. The drawn forearm outline rode above the arm (a black slab). Lowered it and widened the unknown band.
4. First scene: dog small and ghost-pale; frame 22 held for the refusal was an unreadable hunch; the curtain window read
   as wood. Scaled up, darkened the grade, made the refusal the archive turn followed by lying down with its back turned.
5. The lying dog built from frame 45 (head-low walk) read as a crouching blob. Rebuilt from frame 9; then fixed seams from
   over-compositing split pieces (legs now overlap under the body), a foreleg dragged by the head piece (round head mask),
   both forelegs pivoting in one piece (split, each grounded to the floor line).
6. The lying dog in front of the bright doorway was washed out and floated above the sill; it is now backlit (darker,
   light-wrapped edge) and grounded.
7. Tree line moved down so the dog stands against the dusk glow rather than dark trees.
8. The standing woman read as seen from behind (bun, smock): graded to a silhouette so only her outline and hair edge
   read.

9. **Repair round 1 (independent critic: DOES NOT PASS).** Conditions and what changed:
   1. Sky through the thigh at 4.40–4.60 / 7.80–7.95 s: the folded hind-leg piece was being faded, so body + hind no longer
      added up to solid. Removed the fade (hind piece clipped below the floor line instead) and composited the pieces with
      union alpha (interior of the silhouette forced solid, colour un-premultiplied and re-premultiplied). Measured on the
      sprite over 21 lie values × 3 configurations: minimum interior alpha 1.000.
   2. Illegible turn frames 16–22 and the head jumping sides at the mirrored cut: replaced by a turn through the front
      (14, 15, 26, 28, 31 → mirrored 9; back: 26, 26, 15, 14). Looked at every frame 3.75–4.20 and 8.00–8.55 s.
   3. Pale outline on siding and porch at the sill: light wrap now unblurred and only from behind in depth (not from the
      floor), edge colour clamped to the adjacent solid fur, contact shadow under the dog. Looked at 2× crops 24.2–30 s.
   4. Look-back 7.50–8.0 s: hard substitution (no dissolve double), muzzle rotated level toward the door, head lifted clear.
   5. Look-in: head-back piece cut only across the neck (skull and ears keep their own matte edge, no oval sticker, no seam
      ring); speck filter tightened (alpha support test r6 > 0.18); walk frames 42, 46, 47 dropped (headless blobs).
   Optional: claws on the approach raised 6 dB, with a second paw half a step later.

10. **Repair round 2 (independent critic: DOES NOT PASS, narrowly).** Conditions and what changed. The original
    builder began this round (the gait, the calls moved earlier) but did not record it. Its successor finished, measured
    and recorded it. All numbers are measured on frames and audio decoded from the encoded `film.mp4` (`build/verify.py`
    → `proof/round3_verify.json`; its sheets were replaced by round 3's). The dog's mask on screen is |film − no-dog plate|, where the
    plate is the same frame rendered with `NODOG=1` (same grain seeds, same shadows).
    1. *Retreat skated (a forward walk slid backward):* the backing gait above. Each planted paw holds within **2.60 px**
       (fore pair, 5 plants) and **2.42 px** (hind pair, 4 plants) while the body travels 203 px.
    2. *Calls on the reaction frame:* "come here" now starts at **0.63 s** (0.37 s before the retreat at 1.00 s; the body
       moves from 1.29 s). The repeat comes at 1.60 s, and the second call at **2.95 s**, 0.47 s before the turn and the
       reach at 3.42 s. "It's all right" starts at 7.43 s, before the look-back at 7.46 s; "come in" at 25.90 s, before the
       look-in at 26.4 s. The calls are −23.3 to −24.0 dBFS and the soft words −33.9 to −35.4 dBFS: **9.96 dB** between
       the quietest call and the loudest soft word.
    3. *Matte debris at 9.2–10.0 s:* this was a hooked strand above the shoulder in frame 14, attached to the outline, so
       the largest-component filter kept it. It is cut by hand (source px 149–165 × 100–110). On the film, the only extra
       pieces at 9.0–10.2 s are 4–7 px edge pieces within **3 px** of the body. Looked at 4×, they are the tail tip and a
       leg edge, cut off by the tree line in the mask, and one fur wisp.
    4. *Pale rim at 26.5–28.3 s:* the light grey of the throat fur, lifted by the warm door grade, made a pale contour
       against the dark lower doorway. A new edge-colour stage (`derim_edge`, applied wherever the dog is placed): inside
       a 5 px band at the edge, a pixel may be no lighter than the brighter of the fur core beside it and the backdrop
       behind it. Against the bright doorway nothing changes; against the dark lower doorway the edge falls to the fur's
       own value. On the film, **18 of 5,298** edge pixels against the lower doorway are lighter than both sides by more
       than 0.03 (at most 2.8% of the edge in any frame); on average the edge is 0.032 darker than the brighter side.
       There are **0** ear-tip specks. The look-in head is now a hard substitution; the earlier 0.16 s dissolve had left a
       faint double head at 26.50 and 28.29 s.
    5. *Pops at 2.375 and 23.833 s:* the retreat is bridged as described above. The lie-down now starts 45% lowered,
       with the head carried forward-low (no longer curled under). Its inward slide has its own ramp, starting 24 px back,
       so it meets the crouched walk frame. The head point is the centroid of the solid matte in the 45 px nearest the
       side the dog faces; the earlier outermost-column "nose" jumped to a forward paw. Its largest one-frame step is
       **22.1 px** in 0.83–2.54 s and **17.5 px** in 23.58–25.0 s (render: 21.6 and 7.6 px).

11. **Repair round 3 (independent critic round 3: PASS, narrowly; one last round).** All numbers are measured on the
    encoded film (`proof/round4_verify.json`, sheets `proof/r4_*.jpg`).
    1. *Siding through the legs at 22.2–23.8 s; ghost legs at 23.62–23.79 s:* the matte was solid. The light wrap was
       the cause: it weighted "edge" by distance from the interior, so a thin leg counted as all edge, and up to 60% of
       its colour was replaced by the siding behind it. Wrap now acts only on truly fractional alpha (4a(1−a), none above
       0.97). The approach no longer uses frame 45 as a held drawing (item 5), so its faded hind legs are gone. Measured:
       the siding pattern (no-dog plate minus the same plate with unlined siding) regressed against the film inside the
       dog's alpha ≥ 0.95. Body transfer is 0.002 (max 0.020); legs −0.016 (max 0.103), against a control of 0.085 (the
       noise floor), so the dog is opaque within noise. The test was validated: it reads 1.01–1.04 outside the dog.
       Render check: removing the siding lines changes solid dog pixels by 0.19 grey levels on average, against 4.78
       outside.
    2. *Look-back snap at 7.46 s:* the head now comes round through the dog's front over five frames (see "How it
       moves"). The largest step of the head piece is **34.4 px** on the film (render 34.3). A rejected alternative,
       swinging the profile head 180° over the back, left it floating on a stalk.
    3. *Soft voice:* "It's all right" now starts at **7.11 s**, 0.35 s before the look-back. It is **9.96 dB** under the
       quietest call.
    4. *Frontal heads at 3.71–3.83 and 8.04–8.17 s:* frames 30 and 33 (head three-quarter, muzzle and ear clear), and
       the same frames mirrored for the turn back. Local contrast alone (tested at 1.9× and 2.8×) only made the mottled
       coat busier.
    5. *Feet at drawing changes in the approach:* the approach now walks on the planted-paw gait (60% stance), so there
       are **0** held-drawing changes. Planted paws hold within **2.38 px**, and the largest one-frame paw move (a swing)
       is **15.9 px**. The head lowers at 14.71 s through the retreat's bridge drawings.
    Protected, re-measured on the film: retreat paws within 1.74 px; calls at 0.63 / 1.60 / 2.95 s; at 9.0–10.2 s,
    only 4–5 px edge pieces within 3 px of the body; look-in rim 48 edge px (under 6% of the edge in any frame),
    0 specks; head steps 22.3 px (0.83–2.54 s) and 8.4 px (23.58–25.0 s).

12. **Repair round 4 (independent critic round 4: DOES NOT PASS, narrowly; the last round before a pause).**
    *My round 3 claim that the legs were opaque was wrong.* My siding test sampled only the dog's alpha ≥ 0.95, so it
    never looked at the pale limb: a partly transparent fringe (tail or far hind leg) hanging below frame 45's rump.
    Frame 45 also has its hind pair lifted mid-stride, so the gait carried floating hind feet through the approach (in
    the retreat the tree line hid them). Numbers below are measured on the encoded film (`proof/round5_verify.json`,
    sheets `proof/r5_*.jpg`), and the crops were looked at at 2×: `proof/r5_crop_22.25s.jpg`, `r5_crop_23.00s.jpg`,
    `r5_crop_23.75s.jpg`.
    1. *Ghost leg, siding through legs and rump:* the hanging fringe is cut. The bent far hind leg is hidden behind the
       near one (a reconstruction: the dog shows one hind leg in side view). Alpha in the gait is hardened (0.2→0,
       0.75→1). Now every dog pixel with alpha ≥ 0.3 over the siding is measured: transfer 0.012 mean, 0.043 max (rear
       half 0.044; legs 0.116 max against a control of 0.017). At most 2.6% of the dog's pixels (its outer fringe) are
       below alpha 0.95.
    2. *Hind feet:* the near hind leg is lengthened from the hip, so its paw stands on the floor line. Planted hind feet
       are within **2 px** of the floor on the film (1 px in the render) and level with the front paw within 5 px.
    3. *The 23.79→23.83 swap:* over its last five walking frames the walker's hindquarters sink (34 source px, a
       per-column shift from the shoulder to the rump, with the hind leg folding at the boards). The lie-down then starts
       15% lowered. At the swap, the hip drops **3.6 px** and the head moves **28.2 px**. The largest hip drop in any
       frame of 23.33–24.42 s is 15.6 px. The drawing still changes tone and length there (the lying sprite is the other,
       lighter side of the dog).
    4. *The fin and the tail:* the fin was the corner where a straight crest cut met the hole left for the head. The
       shoulder is now cut to a rounded line. A tail tuft (frame 13's tail, its alpha hardened, seated at the rump) shows
       outside the jamb at the sill and at the rear in the refusal. It is small: frame 9 has no tail, so the tuft is a
       reconstruction.
    5. *Reach:* she reaches 6 frames ahead of the score, so the hand is out from **3.167 s**, 0.25 s before the turn.
    Kept, re-measured: look-back largest step 34.9 px; soft voice 0.35 s ahead of the look, 9.96 dB under the calls;
    frontal heads; retreat paws 1.55 px; approach paws 2.18 px, with 0 held-drawing changes; fragments at 9–10 s within
    6 px of the body; look-in rim 37 edge px, 0 specks.

## What is still weak (my own view; not a verdict)

- At 23.83 s the walker is replaced by the lying reconstruction. Head and hip carry through, but the dog's tone and
  length change in one frame. The tail tuft is small.
- The walking dog shows one hind leg (the far one is hidden), and the near one is lengthened from the hip.
- Whole-body swaps between frames 13 and 14 in the long watch (9.33 and 10.17 s) are not bridged.

- The look-back bridge joins heads from three archive frames on the lying body. Frame 14's head ends in a soft vertical
  edge where its box cut runs through shoulder fur (one frame, 7.58 s), and at 7.46 s a crescent of sky shows between
  the shoulder tuft and the lifted head.
- The approach is now the same single drawing (frame 45, legs sheared in two pairs) as the retreat. It is steadier than
  the four-drawing walk, but less varied: the body does not bob or change, only the legs move.

- At the start and end of the retreat (1.13→1.17 s and 2.29→2.33 s) and at the sill (23.79→23.83 s) the head is now
  continuous, but the drawing still changes in one frame: upright to crouched body, and at the sill from the walk's
  white-collar side to the lying sprite's lighter side. The 54° bridge drawing shows a small notch at the withers.
- The backing gait moves two leg pairs, each sheared as one piece (the two legs of a pair move together), and lifts a
  swinging paw only 5 px. Against the dark tree line the paws are low in contrast.
- The render's head point still jumps more than 30 px at the turns through the front (3.46–3.88 s, 8.0–8.2 s) and at
  each switch between frames 13 and 14 in the long watch.


- The turns are now three-drawing substitutions through the dog's front (0.4 s): legible frame by frame, but a cut
  sequence rather than a continuous turn; frame 26 (front, head low) is small and dark.
- The mirrored gait shows the other side of the dog (the white collar side) from the unmirrored holds.
- The lying dog is a reconstruction; its folded hind legs are compressed and hidden rather than folded. The look-in head
  (frame 5 from behind) shows the skull and one clear ear tip; the muzzle is not visible, so depth rests on the back of the head.
- The woman's legs are drawn shapes; her reach is a borrowed forearm, and her calling has no visible mouth (she is a
  silhouette). The curtain in the door window is too small at playback size to read as fabric.
- The voice is synthesized formants, not a human voice; how intelligible it is, I do not know.

## What I did not do

No independent critic was run by me. No human viewing. No listening. No Quick, Draw! drawings, no web images, no model
images. I did not import `paeleo/threshold/stage.js` or `paeleo/scion/lenses.js`, did not look at other swarms' folders,
and did not run git. No operator page was published as an artifact; `operator.html` in this folder is a local page.

## Evidence (last build: make.sh v10, which renders, encodes, checks, verifies on the film and deletes the frames)

**Checker (`invariants.json`): ALL OK.** All six choices are on time (I1). The dog never goes past the sill and ends
across it (I2). It moves in the score's direction (I3). Its back is turned through the refusal (I4).

**Measured on the encoded film** (`proof/round5_verify.json`): the round 4 conditions and the kept ones, as listed in
item 12. The round 3 numbers in `proof/round4_verify.json` include a siding test that did not sample the pale limb; do not rely on it.

**End across the sill**: head and forelegs inside the door frame, haunch and tail tuft outside (see `trace.json`, `end`).

**Sound**: calls −23.3 to −24.0 dBFS and soft words −35.4 dBFS on the film's AAC track: 9.96 dB apart. Not listened to.

**Film**: 1280×720, 24 fps, H.264 two-pass 2.1 Mb/s + AAC 160k, faststart, 912 frames, 38.000 s, 10.66 MB. The folder is 56 MB, with frames deleted.

**Looked at**: frames decoded from film.mp4, full frame and cropped at 1×–3×, in every repair window. **Not looked at**: normal-speed playback. **Not listened to**: the sound.

**Status**: repair round 4 done; awaiting independent review. Not accepted.

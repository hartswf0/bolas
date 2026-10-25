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

**What it is made of.** 13 frames of the archive dog (*Amateur Film New Jersey C*, Home Movies, Internet Archive, public
domain) appear: 9, 12–15, 26, 28, 31, 43–45, 48 and, for the head only, 5. All 50 are matted.

**How it moves: substitution of whole matted frames, chosen by the score.**

- *Watching* (0–1 s, 2.33–3.42 s): held frames 9 and 13, the grain renewed each frame. The long watch (8.8–14.7 s)
  shifts among the archive dog's own frames 12–13–14 (its small attention changes), never a frozen still.
- *Backing away* (1.0–2.33 s): the archive dog's head-low walk (43, 44, 45, 48), mirrored to face the door, **played backward**,
  one frame per 0.068 m of the score's travel, so the feet account for the distance. Head low, as the score's crouch.
- *Turning its back* (3.42 s): a turn **through the dog's front**, chosen from its own frames at 12 fps: 14, 15 (three-quarter
  left), 26, 28 (facing the camera), 31 (three-quarter right), then frame 9 mirrored (profile, facing away). The head goes
  left → centre → right and never jumps sides. Then it **lies down with its back to them** (score lie = 1 from 4.5 s) and
  lowers its chin. (Repair round 1: the archive's own turn, frames 16–22, read as dark tangles and was dropped.)
- *Turning back to look* (7.46 s): the head comes round at once (a hard substitution, no dissolve), over the shoulder,
  muzzle level toward the door (the head piece kept unmirrored and lifted clear of the back of the mirrored lying body);
  it rises (7.66–8.0 s), then turns back through its front: 26, 26, 15, 14, then the watching frames.
- *Coming, head low* (14.71 s): frames 14, 15 (head lowering), then the head-low walk mirrored, advanced by distance
  travelled (3.4 m at the score's pace).
- *Lying across the sill* (23.79 s) and *looking in* (26.4 s): **a labelled reconstruction.** The archive dog was never
  filmed lying. One solved matte (frame 9, profile, head up) is split by complementary soft masks into body, two forelegs,
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

## What is still weak (my own view; not a verdict)

- The turns are now three-drawing substitutions through the dog's front (0.4 s): legible frame by frame, but a cut
  sequence rather than a continuous turn; frame 26 (front, head low) is small and dark.
- The walk loops four frames (42, 46, 47 dropped: head lost in a tangle); the loop seam and the skip 45→48 are visible to an attentive eye. Feet: frames advance by distance at a stride
  estimated from the source, not measured per foot (the kit's rig keys for 44–49 are interpolated, not tracked).
- The mirrored walk shows the other side of the dog (the white collar side) from the unmirrored holds.
- The lying dog is a reconstruction; its folded hind legs are compressed and hidden rather than folded. The look-in head
  (frame 5 from behind) shows the skull and one clear ear tip; the muzzle is not visible, so depth rests on the back of the head.
- The woman's legs are drawn shapes; her reach is a borrowed forearm, and her calling has no visible mouth (she is a
  silhouette). The curtain in the door window is too small at playback size to read as fabric.
- The voice is synthesized formants, not a human voice; how intelligible it is, I do not know.

## What I did not do

No independent critic was run by me. No human viewing. No listening. No Quick, Draw! drawings, no web images, no model
images. I did not import `paeleo/threshold/stage.js` or `paeleo/scion/lenses.js`, did not look at other swarms' folders,
and did not run git. No operator page was published as an artifact; `operator.html` in this folder is a local page.

## Evidence (last build: make.sh v5, then frames 80–91, 192–205, 350–361 re-rendered; measured)

**Checker (`invariants.json`): ALL OK.** I1 retreat 1.000 s (dt +0.000), watch 2.333 s (dt +0.000), refuse 3.458 s (dt +0.041), watch 7.458 s (dt +0.000), approach 14.708 s (dt +0.000), lie_down 23.833 s (dt +0.041). I2 min x_score 0.59, end 0.59. I3 r = 0.999. I4 back turned in 0.938 of refusal frames. State labels in `trace.json` are read from the pose the render chose.

**Onsets measured from the render**: retreat_motion_starts 1.208 s; retreat_motion_stops 2.375 s; turn_away_first_new_frame 3.458 s; back_turned_first_frame 3.708 s; head_toward_door_again 7.458 s; approach_motion_starts 14.875 s; approach_head_lowers_first_frame 14.708 s; lie_sequence_first_frame 23.833 s; lying_half_down 24.167 s; refusal_lies_down_full 4.917 s; looks_in_first_frame 26.500 s; looks_in_last_frame 28.208 s.

**End across the sill**: solid dog x 272.8–513.8 px vs door opening 243–417 px: 144.2 px inside the frame, 96.8 px outside.

**Sound (RMS dBFS)**: calls -23.1 / -23.6 / -23.0; soft words -35.0 / -35.0; come in -33.6; room tone -58.8 / -51.7. Calls − loudest soft word 10.51 dB; quietest soft word − room tone 16.69 dB. Not listened to.

**Mattes**: premult_ok on 50/50 dog mattes and all world mattes; stress fixture: 0 premultiplication failures, 0 bright rims in 96 frames. Lying sprite: minimum alpha inside the silhouette 1.000 over 21 lie values × 3 configurations (refusal, look-back rise, sill).

**Film**: 1280×720, 24 fps, H.264 two-pass 2.1 Mb/s + AAC 160k, faststart, 912 frames, 38.000 s, 10.69 MB; 768 scene frames.

**Looked at**: extracted frames only (contact sheets, frame-by-frame sheets of both turn windows, 2× crops of the sill). **Not**: normal-speed playback, the sound.

**Status**: repair round 1 done against the critic's five conditions; awaiting re-review. Not accepted.

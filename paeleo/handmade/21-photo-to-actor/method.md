# SCION 21 · Cartoon Animator, Photo-to-Actor Factory · PAE-02 threshold

**Thesis.** Turn a photographed dog into an actor fast enough for an archive, and catch the places where an automatic face rig gets the animal's anatomy wrong. The dog in this film is made only from six frames of one real dog in a 1950s-style home movie (*Amateur Film New Jersey C*, public domain). In that footage it walks to a food bowl. It never backs away from a call, refuses, lies across a sill or looks into a house. Every one of those actions is the PAELEO score, retargeted onto a rig built from the stills.

## Native formal language (kept as working primitives in `actor/` and `build/`)

| primitive | where | typed inputs → outputs |
|---|---|---|
| photo masks | `build/prep.py` | archive frame + SAM polygons (kit `masks.json`) ∩ hand cut polygon (`build/spec.py`) → feathered alpha at 2× source px |
| body template | `build/spec.py` JOINTS/LEGS, `build/actor.py` | profile frame f009: shoulder, hip, neck base, head pivot, tail root; 4 legs × 2 segments with bend direction. Template px = f009 source px; 150 template px = 1 m; screen = 1.2 × template |
| photo-textured parts | `actor/parts/*.png`, `actor/parts.json` | torso, neck, 8 leg strips (f009), tail (f012); each records source frame, crop box, anchors and operation |
| face landmarks | `build/fit.py` → `actor/landmarks.json` | eyes, nose, ear bases, chin, jaw hinge per head: automatic, tests, correction, error |
| expression controls | `actor.Head.compose(ear, mouth, brow)` | ear patches rotate about the ear-base landmark, the jaw patch rotates about the jaw hinge, the brow patch shifts. The uncovered fur is filled from a blurred copy of the head (no hole, no second ear) |
| angle artwork | heads: front f038, three-quarter f037, profile f009, lowered f046, back of head f000. Whole bodies: f038, f037, f000 | chosen by **sprite replacement** from the view state, with no cross-fades |

Coordinates: scene 1280×720 at 24 fps, static camera. Ground at y = 612. Threshold x = 0 at screen 330, 180 px per metre. The doorway ±0.46 m runs from 247 to 413 px. **Mapping:** the score's x is the dog's loins, so body centre = 330 + 180·x − 54. With the dog lying at the sill (x = 0.59), the head, forelegs and front half of the body are inside the door frame and the hips and tail are outside. Time base: score frame i is scene frame i, and film frame = i + 72.

## How the dog is built and moved

- **Photograph preparer.** Six dog frames are copied to `sources/dog/` and their SAM masks to `sources/masks_used.json`. Each part is cut as SAM ∩ hand polygon, then developed (grey, autocontrast, unsharp 60 %). Heads get a soft elliptical cut, so no square background corners remain. The back of the head is luminance-keyed to its dark fur, because its SAM mask includes the bright path behind it.
- **Retargeting operator** (`build/perform.py`). The score's acting values (`lie`, `crouch`, `head`, `rest`, `look`, `ear`, `tail`, `wag`) become controls on the template:
  - shoulder and hip drop (lie, crouch);
  - neck angle and muzzle angle from `head` (piecewise tables);
  - chin on the paws (`rest`);
  - the back of the head into the doorway (`look`).
- **Paws.** Each paw is a two-bone IK target. While a paw is in stance it stays planted in the world. The gait phase is the dog's own cumulative distance travelled divided by an 82 template-px stride (0.55 m, the score's walk-phase rate), with the four legs in a lateral sequence. The photographed legs therefore carry the travel, and nothing slides while held. Lying feet blend to a sphinx pose: forelegs forward, hind legs folded with the stifle forward.
- **The turns are sprite replacement, never mirroring or squashing a flat figure:**
  - 3.417 s (refusal): f82 profile body with the three-quarter head, then f83 the three-quarter body (f037), f84 the front body (f038), f85 the three-quarter body mirrored, then from f86 the profile rig mirrored with its back turned. It then lies down facing away, chin on the paws, tail tucked.
  - 7.458 s (the head leads): f179 front head, f180 three-quarter head, then from f181 the profile head mirrored back over the shoulder, with the muzzle toward the door while the body is still down (score lie = 0.93 → 0.43 over 7.46–7.67 s). The body gets up facing away with its head turned back, passes through the photographed back view (f000) at f192–195, and stands in profile toward the door from f196.
- **Facial performer.** Ears follow `act.ear` (flat when called, pricked when the door opens). The brow rises with fear (`crouch`). The mouth opens in a slow pant once the door is open and the dog watches, and stays shut when it is afraid or resting.
- **Look in (26.4 s).** The profile head first foreshortens (x-scale 1 → 0.6). It is then replaced by the back-of-head artwork, slightly smaller (further away), dark against the lit hallway, with a warm rim from the doorway. Afterwards it settles back to chin on paws.

**The room is made consistent with the photographic grain:**
- The person, the door leaf and the lit hallway come from *Straight Talk* (NTIS, public domain). The person is graded to a backlit silhouette and moved as photo parts (torso, two leg halves, arm): she calls, reaches, steps aside, sits with her knees up and offers her hand low.
- The sky is one frame of *Top of the Cloud* (public domain).
- The house boards, porch planks, railing, steps, tree line and lamp light are computed. They share one tone curve, dusk grade, vignette and per-frame grain with the photographs.

## Automatic landmark fit and where it failed (`actor/landmarks.json`, `proof/review_pairs.jpg`, `proof/expression_auto_vs_corrected.jpg`)

The automatic fitter is a generic frontal portrait rig. It puts symmetric eyes at 42 % of the cut's height, the nose at 68 % and the chin at the bottom, then snaps the eyes and nose to the darkest local minimum. Anatomy tests check it.

| head (frame) | mean error / head diagonal | verdict | failure |
|---|---|---|---|
| front (f038) | 0.098 | accepted, auto landmarks used | none tested; ear bases about 13–20 px low on these drop ears |
| three-quarter (f037, mirrored) | 0.117 | accepted at the edge of tolerance | first run 0.288 because mirroring swapped the left/right labels. That was our bug, fixed |
| profile (f009) | 0.337 | rejected, hand-corrected | two eyes on a head that shows one; the nose snapped to the dark ear/neck patch, behind the eye |
| lowered (f046) | 0.181 | rejected, hand-corrected | the same two failures; the template chin lands on the white neck ruff |
| back of head (f000) | 0.181 (ears only) | rejected, hand-corrected | the fitter placed a whole face on the back of a head. The correction keeps the two ears and declares the face absent |

The rule learned from these five inspections (`actor/compat.json`): accept the frontal rig only for frontal and three-quarter cuts with error below 0.12 and no failed anatomy test. Send profile, lowered and back views to hand annotation. The review pair shows what an uncorrected jaw would do: on the profile, the automatic jaw patch tears open the throat instead of the mouth.

## Measured (from the render: `trace.json`, `build/measure.py`)

Onsets are measured on the dog's rendered alpha layer, by the rule named in `trace.json → onsets_measured`:

| choice | score | measured | dt | rule |
|---|---|---|---|---|
| retreat | 1.000 | 1.042 | +0.042 | centroid moves away > 0.5 px/frame |
| watch | 2.333 | 2.250 | −0.083 | head end rises 3 px from its lowest point in the retreat |
| refuse | 3.417 | 3.417 | 0.000 | mask change (the turn's first sprite) |
| watch (turns to look) | 7.458 | 7.458 | 0.000 | head-end change while the body lies |
| approach | 14.708 | 14.750 | +0.042 | centroid moves toward the door > 0.3 px/frame |
| lie down | 23.792 | 23.833 | +0.041 | back line drops 3 px |
| looks in | 26.400 | 26.542 | +0.142 | head end rises 4 px above rest |

- `check_handmade.py` reports **ALL OK** (I1–I4). The refusal shows the turned back in 94 of 97 refuse frames.
- Head below the back line on the approach: the minimum is 17.5 px, the median 37 px. This is measured as the mean height of the leading quarter of the mask against the top of the mid-back. The leading quarter includes the forelegs, so it is a proxy.
- Sound, measured on the film's decoded audio: calls −10 to −11 dBFS RMS, soft voice −24 dBFS (about 14 dB under), room tone about −41 dBFS.
- Film: 912 frames, 38.0 s, H.264 + AAC, faststart, 9.07 MB.

## Looked at (perceptual, by the builder, not a verdict)

Frames were extracted from **film.mp4** and inspected at full resolution:
- every frame of both turns (scene 80–87 and 178–198): one dog in each, no double image;
- 0, 1.04, 1.67, 2.25, 3.42–3.62, 5.0, 7.46–8.25, 9, 12.5, 14.71, 14.88, 19, 22.5, 23.83, 24.17, 25, 26.54, 26.88, 27.5, 28, 30 and 31.96 s.

The four stills are taken from the encoded film. I have not watched the film at normal speed with sound. The audio was checked by level measurement only.

## What failed and what changed

The full record is `ledger.jsonl`. In short:
- the development was posterised, so it was softened;
- heads had square corners, so they got an elliptical cut;
- the lying dog was barely inside the frame, so the score x was mapped to the loins;
- the look-in read as a lift toward the light, so the back of the head was keyed dark, lowered, widened, made smaller and rim-lit;
- the person's arm crossed her body, so its anchors were fixed;
- the film was 30 MB because of the grain, so the grain was halved and the CRF changed;
- the dog was still facing the viewer at 3.6 s, so the turn was tightened;
- the approach began with the head up, so the head now drops with the decision;
- mirrored landmark labels were swapped, which was fixed;
- a stale measurement file was found and removed.

## Weak / unknown

- The source dog is about 100 px high and blurred. Close up, the photographed heads are smears with a few features: eyes and nose are only legible on the front and three-quarter heads. The expression controls work as specified but are barely visible at film scale.
- The back-of-head artwork is the dark fur mass of one frame (f000) with a single clear ear point. It reads as a dark head turned into the light, but it is the least certain view.
- The body's turn through the back view (8.00–8.12 s) is a visible pop, which is the nature of sprite replacement with only one back frame. The hind legs cross into an X shape at the stifles.
- The person, seated, is a dark lump; her face is never seen (she comes from a back-view shot).
- The dog is small in a static wide frame.
- The lying pose is the standing f009 torso lowered, with the legs re-posed. No lying dog exists in the material.

## Not done

- No camera moves; no independent critic run by me.
- The hand corrections are by one annotator with no second pass.
- The compatibility classifier is a rule from five inspected heads, not a trained model.
- No mobile operator page.
- The hand-sam shot and Quick, Draw! drawings were not used.
- No pixel of the dog is drawn by hand, but the house and porch are computed, not photographed.

**Stop condition:** watchable and the invariants hold. Independent critique is pending.

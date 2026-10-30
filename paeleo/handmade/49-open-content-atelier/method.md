# PAE-02 · SCION 49 · Getty & Smithsonian — Open-Content Atelier

**The threshold, cut from open-access museum objects.** The dog, the person, the door, the room, the floor and the dusk are
all cut from eight Smithsonian American Art Museum images marked CC0 through Smithsonian Open Access. Nothing is drawn by
hand. Only the light is computed: the dusk grade, the warm wedge from the open door, and a rim on the dog's head when it
enters the room's light. The title and end cards are typeset.

## The atelier's language

The native primitives of this swarm are the **item record and the cut**. Every piece on screen is a *part*. A part carries
its source `idsId`, the EDAN record (item URI, record URL, object number), the museum's own rights fields, the polygon of the
scissors line in source pixels, the key that refined the cut, and its pivots. `assets.json` is the registry and per-item
rights manifest, and `build/parts.py` is the transformation history in code. The animation moves parts. It does not move
pixels.

The two ontologies are kept side by side. The museum describes a *hand-coloured lithograph of a pointer in a woodcock
cover*. The animator's tags for the same print are *walks, bends at neck, swings tail, legs hinge at shoulder and hip, hock
folds back*. The museum describes *Juno* as a lithograph. To the animator it *lies, rests chin on paws, lifts head, reaches
in*. The left pointer in *On a Point* has its head turned over its shoulder, so it *looks back*. Edouart's cut-paper
silhouettes *stand, sit, reach*, and they hide their own seams because black paper joins invisibly. The screen door *opens
out*. The historical metadata in `sources/meta/records_fetched.jsonl` is never altered.

## Collections research and rights (what was measured)

- **Reachability (measured on 2026-10-30).** The session proxy refused `api.si.edu`, `collections.si.edu`, `ids.si.edu`,
  `data.getty.edu`, `www.getty.edu`, `media.getty.edu`, Art Institute, Met, Wikimedia and archive.org (CONNECT 403). Only
  the **Smithsonian Open Access S3 open-data bucket** answered. **The Getty Open Content program could not be reached, so no
  Getty object is used.** The swarm keeps its name; the film does not pretend otherwise.
- **Search.** `build/fetch_meta.py` and `build/fetch_grep.py` streamed all 256 SAAM EDAN shards. They kept only rows whose
  record *and* image are marked `CC0`: 1,655 dog/door/porch/seated rows, plus the Muybridge and silhouette/Currier passes.
  The full index is in `sources/meta/candidates.tsv`. Muybridge's *Animal Locomotion* dog plates are not in SAAM's CC0 set,
  so there is no photographic walk cycle.
- **Fetch.** `build/fetch_media.py` checks both `metadata_usage.access` and `online_media.usage.access == CC0` before
  downloading `media/saam/<idsId>.jpg`. It logs every byte to `sources/downloads.jsonl`: 36 images, **71.8 MB**, plus about
  104 MB of streamed metadata of which only matching rows were kept. Used images are kept at ≤1800 px. The 28 reviewed but
  unused images are kept as 800 px review copies.
- **Faces.** No photographs of people are used. The person is a cut-paper silhouette by Edouart (1840s profiles, marked
  CC0); its only features are a profile outline and a white collar.

## How the dog is made

Three hand-coloured lithographs of liver-and-white pointers, one breed and one printmaking family, used by role:

| role | object | parts |
|---|---|---|
| standing, walking, retreating, turning, approaching | Currier & Ives, *Woodcock Shooting* (SAAM 1973.122.4) | head+ear, torso+neck, tail, foreleg (near; far = darkened copy), hind thigh + hind shank (near; far = darkened copies) |
| lying (refusal and the sill), resting, looking in | N. Currier, *Juno* (SAAM 1973.122.5) | lying body with folded legs and curled tail, head |
| the head that leads at 7.46 s, and the three-quarter head mid-turn | C. Parsons, *American Field Sports, "On a Point"* (SAAM 1973.122.13) | head turned over the shoulder |

**Cutting.** Polygons were drawn on gridded crops of each print (`build/grid.py`). A colour key keeps the cream fur and
liver patches and drops the green, blue and dark ground. Then come morphological closing, small-hole fill and the largest
component. Juno has its own key, because her dark liver patch matched the ground.

**Moving.**
- Position follows the score's `x`, at 185 px/m and the same pace. The retreat goes right and the approach goes left.
- The forelegs are rigid cuts hinged at the shoulder. The hind leg is two cuts (hip to hock, hock to paw) solved by
  two-bone IK, with the hock bending back as in the print.
- Feet are planted by **distance travelled**: the gait phase is distance divided by a 0.28 m stride. A stance foot is
  exactly world-fixed, and the paw clicks in the sound are triggered by the same formula.
- Head angle, crouch, tail and wag come from the score's `act` channels.
- **Turns are substitutions, not squashes.** The body foreshortens to no less than 0.62 of its width. The *On a Point*
  three-quarter head swings through the frontal view, and the body flips behind it. No frame is edge-on.
- **Lying is a substitution** to *Juno* once the puppet has folded its legs; this happens at 4.0–4.6 s and from 23.8 s.
- **The head leads at 7.458 s.** The look-back head appears on Juno's lying body, muzzle to the door, and rises over 0.3 s.
  The body rises at 7.8 s (substitution to the standing cut with the head still back) and comes round at 7.95–8.45 s.
- **Looking in (26.4 s).** Juno's head rises off the paws and moves 12 cm forward, low and level, past the inner face of
  the wall into the lit room. It is warmed by the room light and gets a rim. Then it settles back, chin on paws.

**Stage.** The house is shown in cutaway section, like a museum period-room diorama. The room is on the left (Andrews,
*Interior of a House*). The wall is cut through, with a lintel and two casing strips. The threshold stone runs out to the
sill at 0.56 m, then the porch boards (strips of Andrews's floor). The dusk beyond is MacGilvary's *Twilight after the
Rain*. López's carved *Screen Door* opens **outward**, as screen doors do, against the dusk. Its width is drawn as
W·sin(angle) of its swing. When it opens (6.2–6.9 s) the room's light falls out onto the porch, and the room's clock and
fire become audible. The camera holds still until 21 s, then pushes in to 1.32× by 24.3 s. `x_world_measured` in the trace
undoes the camera.

**The person.** Edouart's standing man is cut at hip and knee. Calls lean him forward. The reaching arm is the pointing arm
of Edouart's *Boy with Dog*, mirrored and hinged at the shoulder. It goes straight at the dog at 3.4 s and is offered low
from 6.8 s. He backs three steps onto a bench cut from Andrews's interior and sits.

**Sound** (`build/sound.py`). The voices are flite speech synthesis: *Come here!* and *Come here! Come on!* are loud; *It's
all right* (twice) and *Come in* are slower and low-passed. Everything else is synthesized: room tone, crickets outside,
the room's clock and fire behind the door, the latch and creak, the person's steps and bench, paw clicks at every foot
plant, thumps when the dog lies, tail thumps during the look-in, and a closing sigh. **Measured on the film's audio:**
calls −20.9 dB RMS, soft lines −29.3 to −31.3 dB (≥ 8.3 dB quieter), room tone −44.4 dB.

## What is protected (tested numerically)

`python3 tools/paeleo/check_handmade.py` reports **ALL OK** (`invariants.json`). Choice onsets are **measured from the
render** by `build/trace.py`, not copied from the score. Each detector runs on the rendered dog layers: centroid motion,
the drawn head's pitch and direction, body width, and how far the body has sunk.

| choice | score | measured onset | dt |
|---|---|---|---|
| retreat (body centroid moves away > 3 mm/frame) | 1.000 | 1.000 | 0.000 |
| watch (head pitch starts to rise) | 2.333 | 2.333 | 0.000 |
| refuse (head drops / body begins to turn) | 3.417 | 3.417 | 0.000 |
| watch (drawn head points at the door while the body faces away) | 7.458 | 7.458 | 0.000 |
| approach (centroid moves toward the door > 3 mm/frame) | 14.708 | 14.708 | 0.000 |
| lie_down (body sinks > 1.5 cm below its last-0.5 s median) | 23.792 | 23.958 | +0.166 |
| look in (nose moves > 3 cm into the room) | 26.4 | 26.375 | −0.025 |

The body is turned away (facing −1) from 3.71 s; I4 share turned = 0.93. During the approach the drawn head's top is 15–30
px below the back line (median 24 px). This is measured from the render geometry. Film: 912 frames, 38.000 s, 1280×720,
H.264 + AAC, faststart, 3.8 MB.

**Structurally verified, not pixel-measured.** `facing` and the head direction come from the transformed pivot points of
the parts actually drawn: the same matrices that drew the frame, not a separate model.

## Looked at (perceptually judged by the builder; not an approval)

Frames were extracted from the final `film.mp4` every 0.25 s, with full-resolution crops of both turns (3.42–4.75 s and
7.25–8.5 s), the approach and the lie (14.75–25 s), and the look-in (25–29 s). In those frames:

- Every frame of both turns shows a dog.
- There are no dissolves anywhere, so no ghosting.
- The back is turned by 3.8 s and kept until the head leads at 7.458 s.
- The lying dog has no raised hindquarters. Its head and forelegs are inside the door frame and its rump and curled tail are
  outside on the porch.

## What failed and what changed (see `ledger.jsonl`)

- The door opening inward hid the lit room. The screen door now opens outward.
- The hind legs were single straight cuts and read as sticks. They are now two cuts with IK, and the neutral foot is set
  back under the hock.
- The mid-turn head was oversized and the body was squashed to 0.42 width (it read as a box). The head was re-cut and
  scaled, and the body width floor is now 0.62.
- *Juno* was 1.5× too big against the standing cut. She was rescaled.
- **Look-in, four tries.**
  1. A stretched neck made of copies of the head cut gave **double ears**. Rejected as a double image.
  2. A black contre-jour silhouette was unreadable at film scale. Rejected.
  3. A neck-only filler still left a gap.
  4. The root fix: a thinner wall, so a 12 cm reach takes the muzzle past the inner face with no stretch. This is kept.
- The narrow lit "reveal" in the doorway read as a pillar and showed under the chin as an orange slab. The room now
  continues to the outer wall face.
- The look-back head popped up in one frame. It now rises over 0.3 s.

## Still weak (known)

- **The dog changes print when it lies down and gets up.** The standing pointer (Woodcock) and *Juno* are different dogs:
  different markings and a heavier chest. A viewer may read the 4.6 s and 7.8 s and 23.9 s swaps as cuts between dogs. The
  end card names the three prints.
- **Mid-turn heads come from a third print** (liver head with a blaze) for about four frames per turn.
- **The look-in reads as "head pushed into the room".** It is low and level, past the inner wall face and away from the
  person's hand, which is higher and further left. But the head stays the three-quarter cut, so the back of the head is
  never shown. A critic may still read it as looking toward the person. This is the most likely failure.
- The dog is small in the wide shot (about 250 px long) until the push-in.
- Legs are rigid cuts with a slight stretch (0.82–1.12) along their axis. The walk is a creeping gait, true to the
  stalking print but not a natural trot.
- The person's seated legs show a step where the thigh cut meets the coat.

## Not done

- No Getty object (host refused).
- No independent critic was run by this builder.
- No mobile operator page. The SCION prompt asks for one; the brief's deliverables do not.
- No 3D models (the bucket has `3d/`; avoided as a maquette).
- No photographs of real people.

## Rebuild

Run `build/make.sh`: parts → render (768 frames, about 5 min on 4 cores) → sound → cards → `assemble.sh` (trace, assets,
encode, frame-count check, stills from the film, invariant check) → delete the rendered frames. Sources are already in
`sources/`. The fetch scripts document how they were obtained.

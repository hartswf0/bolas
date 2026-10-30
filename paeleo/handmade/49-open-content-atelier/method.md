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
folds back*. The same cuts, hinged differently, also *lie, rest chin on paws, look back over the shoulder, turn the head away*. Edouart's cut-paper
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

## How the dog is made (revision 2: one dog)

**One pointer, one print.** The whole dog is cut from Currier & Ives, *Woodcock Shooting* (SAAM 1973.122.4): head with ear,
torso with neck, tail, foreleg (near; the far one is a darkened copy), hind thigh and hind shank (near; far copies darkened).
Every pose is these same pieces hinged differently. Revision 1 swapped in *Juno* (1973.122.5) for lying and *On a Point*
(1973.122.13) for the look-back head; the critic saw three dogs, so both prints are now unused (kept as review copies).

- **Cutting.** Polygons were drawn on gridded crops (`build/grid.py`). A colour key keeps the cream fur and liver patches
  and drops the green, blue and dark ground.
- **Walking.** Position follows the score's `x`. Feet are planted by distance travelled, with a gait phase of distance
  divided by a 0.28 m stride. The hind leg is two cuts solved by two-bone IK, with the hock behind. **Measured on the
  render:** across 82 weight-bearing frame pairs between 14.7 and 23.6 s, the near hind paw drifts at most 0.1 px. In
  swing it lifts up to 12.5 px (18–20 s). The paw clicks in the sound use the same formula.
- **Turning.** The body is never squashed by more than 15% (width 0.85–1.0); it flips at the middle of the turn and the
  head travels with it. No frame is edge-on, and there is no other print.
- **Lying** is an action, not a swap. Over 0.6 s (15 frames) the torso lowers 54 source px to the floor, and the rear goes
  down first (a 9° haunch pitch). The forelegs reach forward along the floor. The hind thigh folds forward along the belly,
  with the shank back along the floor; the angles are blended linearly so the leg swings down, never over the back. The tail
  lowers to the floor. This happens at 4.0–4.7 s (refusal, back to the door) and from 23.62 s (the sill).
- **Rest.** The same head drops, chin toward the paws.
- **The head leads at 7.458 s.** While the body still lies with its back to the door, the head narrows and mirrors about
  the neck over 4 frames (7.375–7.54 s), so the muzzle points back at the door over the shoulder. The body rises from
  7.62 s with the head held back, then comes round at 7.95–8.45 s.
- **Looking in (26.4 s), revision 4.** There is no view change. The engraved profile head lifts off the paws to level
  over 0.45 s (26.3–26.75 s), and a neck of the same dog's nape fur reaches forward. The muzzle tip goes to −0.255 m
  (measured), 27 cm past the room-side jamb at +0.02 m, into the lit room. It points level and a touch down into the
  room's depth, well below the person's offered hand. It holds there, then from 28.1 s settles back chin-down over 0.5 s.
  Revisions 2–3 showed a constructed back of the head (the ear twice on a crown of fur); the critic read it as a blank
  face toward the camera, so it was dropped.
- **Look-back rise (7.54–8.17 s).** The same nape cut fills the chest under the head turned over the shoulder, so there
  is no bare cut edge.

**Stage.**
- The house is shown in cutaway section, like a museum period-room diorama.
- **Room:** Andrews, *Interior of a House* (1916.6.39). It continues to the outer face of the door frame, so the doorway is
  an opening.
- **Wall:** cut through, with a lintel and two casing strips. The door frame runs from 0.02 to 0.46 m, matching the score's
  door opening; the threshold stone runs out to the sill at 0.56 m.
- **Porch and dusk:** porch boards (strips of Andrews's floor); the dusk is MacGilvary's *Twilight after the Rain*
  (1913.3.3).
- **Door:** López's carved *Screen Door* (1989.30.3) opens outward (6.2–6.9 s) and the room's light falls onto the porch.
- **Camera:** still until 21 s, then a push-in to 1.32× by 24.3 s. `x_world_measured` undoes the camera.
- **At the end** the dog lies with the front of its torso, its forelegs and its head inside the door frame. Its rump is on
  the porch, and its tail lies on the boards outside, against the screen door.

**The person.** Edouart's standing man is cut at hip and knee (*Father, Mother, and Boy*, 1981.172.33). His arm is the
pointing arm of *Boy with Dog* (1981.172.31): it reaches straight at the dog at 3.4 s and is offered low from 6.8 s. He backs
onto a bench cut from Andrews's interior.

**Sound** (`build/sound.py`). The voices are flite speech synthesis; everything else is synthesized. **Measured on the
mix:** calls −20.9 dB RMS, soft lines −29.2 to −31.3 dB (at least 8.3 dB quieter), room tone −44.4 dB.

## What is protected (tested numerically)

`python3 tools/paeleo/check_handmade.py` reports **ALL OK** (`invariants.json`). Choice onsets are **measured from the
render** by `build/trace.py`, not copied from the score. Each detector runs on the rendered dog layers: centroid motion,
the drawn head's pitch and direction, body width, and how far the body has sunk.

| choice | score | measured onset | dt |
|---|---|---|---|
| retreat (body centroid moves away > 3 mm/frame) | 1.000 | 1.042 | +0.042 |
| watch (head pitch starts to rise) | 2.333 | 2.333 | 0.000 |
| refuse (head drops / body begins to turn) | 3.417 | 3.417 | 0.000 |
| watch (drawn head points at the door while the body faces away) | 7.458 | 7.500 | +0.042 |
| approach (centroid moves toward the door > 3 mm/frame) | 14.708 | 14.708 | 0.000 |
| lie_down (body sinks > 1.5 cm below its last-0.5 s median) | 23.792 | 23.750 | −0.042 |
| look in (nose moves > 3 cm into the room) | 26.4 | 26.417 | +0.017 |

The body is turned away (facing −1) from 3.71 s; I4 share turned = 0.93. During the approach the drawn head's top is 15–30
px below the back line (median 24 px). This is measured from the render geometry. Film: 912 frames, 38.000 s, 1280×720,
H.264 + AAC, faststart, 3.8 MB.

**Structurally verified, not pixel-measured.** `facing` and the head direction come from the transformed pivot points of
the parts actually drawn: the same matrices that drew the frame, not a separate model.

## Looked at (perceptually judged by the builder; not an approval)

Frames were extracted from the final `film.mp4` every 0.25 s, with full-resolution crops of both turns (3.42–4.75 s and
7.25–8.5 s), the approach and the lie (14.75–25 s), and the look-in (25–29 s). In those frames:

- Every frame of both turns, and of every lie and rise, shows the same dog (one print).
- There are no dissolves anywhere, so no ghosting.
- The back is turned by 3.8 s and kept until the head leads at 7.458 s.
- The lying dog has no raised hindquarters. Its head, forelegs and the front of its torso are inside the door frame, and
  its rump and tail are outside on the porch.

## What failed and what changed (see `ledger.jsonl`)

**Revision 1** (before the critic):
- The door opened inward and hid the room; it now opens outward.
- The hind legs read as sticks; they became thigh and shank with IK.
- The mid-turn head was oversized and the turning body squashed into a box; both were re-cut and limited.
- The look-in failed four times: double ears, an unreadable silhouette, a neck gap, and finally a wall-thickness fix.
- The narrow doorway reveal read as a pillar; the room now continues to the frame.

**Critic verdict on revision 1: does not pass.** The dog was three dogs, with one-frame swaps at 4.467, 7.467, 7.80 and
24.18 s. The lie-down was a one-frame swap landing 0.39 s late. The look-in showed a three-quarter face aimed at the
hand. The torso was not inside the frame at 28 s. The hind feet were not seen to plant.

**Revision 2** fixes these at the root (round-2 critic: narrow pass, with a further repair asked for the look-in shading and in-betweens, the look-back neck, and the turn squash; done in revision 3):
- One print's dog for every pose.
- Lying is a 15-frame fold, haunches first.
- The head looks back by mirroring about the neck.
- The look-in shows the back of the same dog's head.
- The door frame matches the score's door opening (to 0.46 m), so the lying torso enters it.
- The hind neutral foot moved forward so the leg bends visibly; swing lift is 26 source px; paw drift is measured.
- A linear angle blend stops the folding hind leg from flipping over the back.
- No rim or neck stretch remains.

## Still weak (known)

- **The look-in is a profile reach, not a turn of the head into depth.** It relies on the muzzle being visibly inside the
  lit room.
- **Lying is a folded cut-out.** The legs are rigid cuts, so the lying dog is a "sphinx" with a low, lumpy outline, and the
  print's stalking torso stays fat.
- **The walk is a creep**, true to the stalking print but not a natural trot.
- **The look-back head** is the profile head mirrored (it narrows over 4 frames first). There is no intermediate
  three-quarter view.
- The dog is small (about 250 px) in the wide shot.
- **The step at the person's knee is not fixed** (optional repair).

## Not done

- No Getty object (host refused).
- No independent critic was run by this builder; the verdict above came from the coordinator's critic.
- No mobile operator page.
- No 3D models.
- No photographs of people.

## Rebuild

Run `build/make.sh`: parts → render (768 frames, about 5 min on 4 cores) → sound → cards → `assemble.sh` (trace, assets,
encode, frame-count check, stills from the film, invariant check) → delete the rendered frames. Sources are already in
`sources/`. The fetch scripts document how they were obtained.

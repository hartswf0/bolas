# SCION 51 · Academy Mouris Collection — Montage Research · PAE-02 threshold

## Evidence boundary (read first)

I did **not** view, download or use anything from the Academy Film Archive's Caroline and Frank Mouris Collection. It is not
accessible from here, and this swarm had no network access to it. What this film tests are montage *mechanisms*
associated with collage filmmaking in general (an inventory of found images sorted into imagery classes, a measured shot
rhythm, narrated words treated as image), on independently licensed material: 30 public-domain archive frames from the
kit's found shots (`kit/found-frames.json`), plus my own drawing, geometry and synthesis. No claim of formal influence
from specific Mouris films is made, because I have not seen them.

How this differs from the swarms that went before (I did not look at their films or code; this is from the brief):
04 made the figures from the edges of a torrent of tiny tiles. 01, 43, 49 and 52 did collage. Here there are **no tiles and no
mosaic**. The dog is one steady body, and whole images are substituted onto it and onto the room, one at a time, on a cutting
score. The words of the narration are a separate image layer of cut letters.

## The swarm (roles merged; one builder, executed here)

film archivist + image corpus organizer (the inventory), montage analyst (the cutting score), rights liaison (assets.json,
evidence boundary), sound/voice editor (sound.py). The **independent critic is not me**: I have not approved this film.
Everything below marked *looked at* was judged by me, the builder, on frames from the encoded film.

## Native formal language: the first-class objects

| object | file | what it is |
|---|---|---|
| collection inventory | `inventory.json`, `proof/inventory_sheet.jpg` | 44 typed records: source shot, frame, crop, **imagery class** (fur, hard, eyes, paws, doors, lamps, hands, voices, soft), **temperature** (cold / neutral / warm), allowed layers |
| cutting score (shot rhythm) | `cutting-score.json` | 80 cuts over 768 frames. Each cut is a whole-image substitution, held for a measured number of frames, with its reason |
| narrated words | `words.json` | each spoken phrase as cut letters, with its letter sources, one word per syllable onset, and the voice that speaks it |
| pose state | `build/cache/poses.json` (regenerable by `choreo.py`) | per frame: the dog's position, yaw, head yaw, neck and muzzle angles, lying, crouch, ears, tail, walk distance; the person's pose |
| rights | `assets.json` | source title, archive URL, clip id, rights and the operation for every asset |

Time base: 24 fps, scene frame i = t·24, film frame = i + 72. World: metres; door centre x = 0, facade outer face z = 0;
the dog's body centre is at z = x_score − 0.34 on the line x = 0.

### Measured cutting score (`cutting-score.json → rhythm_by_section`)

| section | cuts | mean hold (frames) | temperature |
|---|---|---|---|
| 0–1.0 s, dusk | 2 | 12 | neutral |
| 1.0–2.33 s, *come here* | 16 | 2.0 | cold, hard (tiger, broom, wheel, ladder, shovel; facade: train, signal, clock, trumpet) |
| 2.33–3.42 s | 5 | 5.2 (3, 4, 5, 6, 8) | neutral, slowing |
| 3.42–4.6 s, call + reach | 15 | 2.3 | cold, hard |
| 4.6–6.2 s, steps aside, sits | 4 | 8.3 | neutral |
| 6.2–7.4 s, door opens, hand low | 3 | 9.7 | warm (lamps begin in the room) |
| 7.4–9.4 s, *it's all right* | 3 | 16 | warm, soft (cat, horse mane, rabbit, sleeping bag; flower, basket) |
| 10.4–11.6 s, soft again | 2 | 21 | warm |
| 14.7–23.8 s, approach | 14 | 15.6 | warm; **one cut per footfall** (every 0.275 m of travel) |
| 26.4–27.4 s, *come in* | 1 | 24 | lamps only |
| 27.4–32 s, stays | 4 | 27.5 (24, 30, 36, 46) | warm, slowing to stillness |

The calls cut at 12 substitutions per second. The soft voice and the light cut at 1 to 1.5 per second. Each cut is audible:
cold cuts make a dry splice tick, warm cuts a soft brush, so the rhythm can be heard as well as seen.

## How the dog is built and moved

- **Body.** About 250 spheres built in `build/lib.py`: a 15-sphere torso with a chest, a neck, skull, muzzle, nose, two eyes,
  two ears, a 14-sphere tail, four two-bone legs (12 spheres per bone) and paws. The renderer ray-casts them exactly, with
  depth. The silhouette, the 3D shading (dusk key light, the warm door light, a rim light) and a dark contour drawn from the
  depth buffer never cut. **Only what the dog is made of cuts.**
- **Substitution.** At every cut the coat (torso, neck, head, ears, legs, tail), the eyes and the paws each take a new whole
  image from the class that fits the moment. The image is luminance-normalised, then tinted to the moment's temperature
  (cold blue-grey, neutral, warm amber), held to a narrow value range, and **pinned to the body** in rest-pose coordinates
  with tri-planar projection, so it turns with the dog and does not slide over it. This is what keeps the dog one dog:
  shape, value and outline stay constant while texture and colour change.
- **Moving.** The position is the score's `x`. The legs walk by distance: a trot whose feet are planted in the world during
  stance (stride 0.55 m, from the walk distance actually travelled), and they also step round during turns in place.
  Turns are true 3D yaw rotations of the body, so there is no edge-on collapse. Acting follows the score's channels
  (crouch, ears, tail, lie, wag), with direction where the lessons require it:
  - **refusal:** the head turns away first (3.42–3.72 s), the body follows (3.46–4.0 s) and ends in profile with its back to
    the door. It then lies with its chin down (4.2–5.6 s), facing away.
  - **7.46 s:** the head leads. Lifted and with the muzzle level, it comes round to the door by 7.72 s while the body is still
    lying turned away. The body rises and turns from 7.62 to 8.55 s.
  - **approach:** the neck is at −40° and the ears are laid back, so the head is below the line of the back.
  - **sill:** it lies across the sill in depth: forelegs extended and its head inside the door frame, hind legs folded flat
    along the flank, tail on the porch.
  - **26.4 s, come in:** the head pushes forward and turns into the lit room, toward −x, away from the camera, kept level and
    never lifted. The back of the head and both ears face the viewer. It settles again at 28.2–29.2 s.
- **Room.** The facade, the door leaf and the lit interior are planes ray-cast per pixel, and they take whole images on the
  same score: hard images on the calls; doors and lamps once the door opens. The floor planks, clapboard lines and door
  frame are drawn and stay constant, to anchor the space. The camera is static to 15.2 s, then pushes in toward the door
  (15.2–23.6 s) so that the sill is legible. The trace therefore records `x_world_measured`.
- **Person.** A simple body of spheres with a dark coat. Its offered hand carries the *hands* class images.
- **Words.** Each spoken word appears at its voice onset as letters cut in a glyph shape (Big Shoulders Display for the calls,
  Literata for the soft voice) from inventory images of the matching class, on cut-paper chips. The calls fall away when
  they end; the soft words fade.
- **Sound** (`sound.py`, all synthesized): a formant voice speaks the same words at the same frames as the letters. There
  are also the cut grains, footfalls derived from the walk, the person's steps, a door creak, breaths, and dusk room tone
  with a low hum once the light is on.

## Measured (from the render and the encoded film)

- Frame counts: scene 768, film 912 frames, 38.0 s (ffprobe `-count_frames`). H.264 + AAC, faststart.
- Choice onsets, measured from the render buffers with the protocol in `build/trace.py` (head angle from the visible muzzle
  or skull pixels in world space, speed of the visible torso, torso height). See `trace.json → summary` and `invariants.json`.
- Approach: share of approach frames with the measured head top below the measured back top is reported in
  `trace.json → summary.approach_head_below_back_share`. The misses are the first ~0.3 s, while the head is still coming
  down, and the last 0.2 s, when it starts to lie down.
- End: share of visible dog pixels past the outer face of the door, and the tail's world z (outside), are in
  `trace.json → summary`.
- Voices: `sound-levels.json`, RMS of each spoken-word window on the final mix.

## Protected invariants

Numeric: the six choices within ±0.25 s, the dog never inside (x ≥ sill), the dog's position correlates with the score's x,
the back is turned during the refusal (the checker), and the soft voice is ≥ 6 dB under the calls and above the room tone
(`sound-levels.json`).
Judged only by viewing: whether the substituted dog reads as one animal at full speed and not as flicker, and whether the
rhythm of the cuts feels like pressure on the calls and like permission on the soft voice.

## What failed and what I changed

See `ledger.jsonl`. In short:
- Wrong first crops: faces where fur was wanted, blank frames. I re-cropped from the full frames.
- Beaded legs and tail: more and closer spheres.
- A head-yaw sign error meant the head did not lead at 7.46 s.
- The end was framed too obliquely, and the person covered the dog.
- The renderer was too slow on the shared machine, so I restructured it.
- The first checker run failed I1: the speed-based state rules produced spurious onsets during turns in place. The protocol
  now needs sustained motion, a lowered and then raised head, and a ≥100° turn before a return.
- The approach head was above the back because of the pricked ears.
- Only 1.7% of the dog was past the threshold. I moved the mapping 0.24 m toward the door.
- The upright hind thigh looked like a post when lying, so the thigh now lies flat.
- The offered hand read as a knob: the person now leans toward the dog and opens a palm.
- The apostrophe was missing from the cut letters.

## What is still weak (my view; the critic decides)

- The person is a plain, rather puppet-like body of spheres.
- The coat substitutions on the soft passages are all warm and similar, so the change there is gentle and may read as
  shimmer rather than as a cut.
- The formant voice is intelligible only with the letters' help.
- The dog's sphere construction shows faint ridges on the legs.
- The interior is suggested by lamp images rather than built.

## What I did not do

I did not view the Mouris collection, use any frame of the kit's archive dog or door, or use any Quick, Draw! drawing. There
was no independent critic run, no human viewing and no real voice recording. The mobile operator page from the SCION prompt
is not built: the brief's deliverables replace it.

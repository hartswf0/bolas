# SCION 51 · Academy Mouris Collection — Montage Research · PAE-02 threshold

## Evidence boundary (read first)

I did **not** view, download or use anything from the Academy Film Archive's Caroline and Frank Mouris Collection. It is not
accessible from here, and this swarm had no network access to it. What this film tests are montage *mechanisms*
associated with collage filmmaking in general (an inventory of found images sorted into imagery classes, a measured shot
rhythm, narrated words treated as image), on independently licensed material: 39 public-domain archive frames (`sources/`) from the
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
| cutting score (shot rhythm) | `cutting-score.json` | 68 cuts over 768 frames. Each cut is a whole-image substitution, held for a measured number of frames, with its reason |
| narrated words | `words.json` | each spoken phrase as cut letters, with its letter sources, one word per syllable onset, and the voice that speaks it |
| pose state | `build/cache/poses.json` (regenerable by `choreo.py`) | per frame: the dog's position, yaw, head yaw, neck and muzzle angles, lying, crouch, ears, tail, walk distance; the person's pose |
| rights | `assets.json` | source title, archive URL, clip id, rights and the operation for every asset |

Time base: 24 fps, scene frame i = t·24, film frame = i + 72. World: metres; door centre x = 0, facade outer face z = 0;
the dog's body centre is at z = x_score − 0.34 on the line x = 0.

### Measured cutting score (`cutting-score.json → rhythm_by_section`)

| section | cuts | mean hold (frames) | temperature |
|---|---|---|---|
| 0–1.0 s, dusk | 2 | 12 | neutral |
| 1.0–2.33 s, *come here* | 10 | 3.2 (2-2-2-8 cycle) | cold, hard (tiger, alarm clock, wheel, traffic light, ladder, broom, frying pan; facade: train, signal, clock, trumpet) |
| 2.33–3.42 s | 5 | 5.2 (3, 4, 5, 6, 8) | neutral, slowing |
| 3.42–4.6 s, call + reach | 9 | 3.8 (2-2-2-8 cycle) | cold, hard |
| 4.6–6.2 s, steps aside, sits | 4 | 8.3 | neutral |
| 6.2–7.4 s, door opens, hand low | 3 | 9.7 | warm (lamps begin in the room) |
| 7.4–9.4 s, *it's all right* | 3 | 16 | warm (cat, rabbit, lantern on the body) |
| 10.4–11.6 s, soft again | 2 | 21 | warm |
| 14.7–23.8 s, approach | 14 | 15.6 | warm; **one cut per footfall** (every 0.275 m of travel) |
| 26.4–27.4 s, *come in* | 1 | 24 | lamps only |
| 27.4–32 s, stays | 4 | 27.5 (24, 30, 36, 46) | warm, slowing to stillness |

The calls cut about 7–8 times per second, three 2-frame flashes and then one 8-frame recognisable hold. The soft voice and the light cut at 1 to 1.5 per second. Each cut is audible:
cold cuts make a dry splice tick, warm cuts a soft brush, so the rhythm can be heard as well as seen.

## How the dog is built and moved (round 2, after critic round 1: DOES NOT PASS)

Round 1 showed a shaded 3D figure with a faint duotone texture. The critic called it a maquette with a style laid over it.
In round 2 **the viewer sees only cut images**:

- **What you see.** The dog is a collage of flat cut-outs: body, neck, head, four legs and tail. Each piece is a cut from a
  whole public-domain image: the subject's SAM-mask box, so a tiger, a cat's face, a wheel, a lantern. The image keeps its
  own colour and light, with no tint and no shading. The cut makes the silhouette: a thin paper margin, then a dark scissor
  line, with dark cut lines where the pieces meet or overlap. At every cut on the score the body, neck and tail take one
  new image (`dog_body`) and the head and legs take another (`dog_head_legs`, images without faces, so the head reads by its
  dog shape: small soft ears, a long muzzle, a dark nose). Each image is mapped flat onto its piece's screen box, so the
  content shows large: on the calls the tiger fills the body.
- **What drives it (invisible).** The round-1 pose solve of about 170 spheres is kept only as the scissors' path and the
  layer order: which piece is in front, and where its outline runs. It walks by distance (planted trot, stride 0.55 m) and
  turns in true 3D yaw. Its shading is not rendered on the dog.
- **Recognition on the calls.** The calls cut in a 2-2-2-8 cycle. Every fourth image is held for 8 frames and drawn from the
  identifiable pool (tiger, wheel, train, alarm clock, traffic light), so at least one is recognisable every second.
- **Soft voice, light, sill.** Only recognisable warm images go on the body: cat, cow, rabbit, horse, monkey, flower,
  basket, lantern, light bulb. From 23.79 s the body takes only images without faces (flower, basket, lantern, bulb), so the
  head at the sill reads as a dog.
- **Acting** is unchanged from round 1: the head leads the refusal turn and the turn back at 7.46; head low on the approach;
  lying across the sill with forelegs and head inside the frame. **Lying, the hind legs now fold under the body.** At
  26.4 s the head turns into the lit room, level, with the back of the head toward the viewer.
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


### Measured onsets of this film (`trace.json → summary`, checker `invariants.json`: ALL OK)

| score | measured | dt |
|---|---|---|
| 1.000 watch → retreat | 1.000 | 0.000 |
| 2.333 retreat → watch | 2.500 | +0.167 |
| 3.417 watch → refuse | 3.542 | +0.125 |
| 7.458 refuse → watch (head leads) | 7.583 | +0.125 |
| 14.708 watch → approach | 14.708 | 0.000 |
| 23.792 approach → lie down | 23.833 | +0.041 |
| 26.4 *come in*: looks in | 26.625 (head leaves the door axis by > 12°) | +0.225 |

The I3 position correlation is r = 1.0 on `x_world_measured`. On the approach, the head is below the back in 96.8% of
frames. At the end, 18.6% of the visible dog pixels are past the outer face of the door (forelegs and head), the tail is at
z = 0.80 m (outside), and the posture is lying. During the refusal the dog faces away in 97.9% of frames. Voices: calls
−14.9 dBFS mean, soft −25.3 (10.3 dB under; loudest soft word −22.9 vs quietest call −16.0), room tone −47.7. Every
voice starts at or before the reaction it causes: 1.0/1.0, 3.4/3.54, 7.4/7.58, 26.4/26.6. The film is 912 frames, 38.0 s,
6.4 MB (round 2).

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

## Round 2 verification (on the encoded film.mp4, proof/r2_*.jpg)

The tiger is recognisable on the body at 1.25–1.58 s and 1.83–2.17 s. On the soft passages the body carries cat, rabbit,
lantern, light bulb and flower. At the sill it lies with the hind legs folded under and a long-muzzled head; the images
there are basket, light bulb, flower and lantern. The second "it's" is on screen at 10.417 s. The end card names only
images held for at least 6 frames on the dog.

## What is still weak (my view; the critic decides)

- The head piece is small, so its image is mostly texture. Pieces are mapped to their screen boxes, so the images inside
  the moving legs slide as the legs swing.

- The person is a plain, rather puppet-like body of spheres. In the end framing the offered hand points toward the
  camera's left rather than toward the dog.
- The formant voice is intelligible only with the letters' help.
- The interior is suggested by lamp images rather than built.

## What I did not do

I did not view the Mouris collection, use any frame of the kit's archive dog or door, or use any Quick, Draw! drawing. There
was no independent critic run, no human viewing and no real voice recording. The mobile operator page from the SCION prompt
is not built: the brief's deliverables replace it.

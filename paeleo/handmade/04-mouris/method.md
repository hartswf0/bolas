# PAE-02 · SCION 04 · Frank Mouris: the threshold as an image torrent

**Film:** `film.mp4` (1280×720, 24 fps, H.264 + AAC, 38.0 s: a 3 s title, the 32 s scene frame for frame with the score, a 3 s made-of card).
**Rebuild:** `build/make.sh` (Python 3 + numpy + Pillow + ffmpeg, about 12 min on 4 CPUs).

## Thesis
In *Frank Film* a life is told by a flood of found pictures whose speed and recurrence carry the meaning. Here the dog, the person,
the door, the house, the dusk and the light are each a **mould** filled by a flood of tiny real archive frames. The subject of
the pictures means something: the dog is made of animals (giraffe, horse, cow, cat, lion, tiger, rabbit, sheep, monkey,
rhinoceros, a migrating herd, and the real archive dog), the person of faces, eyes, hats and bodies, the hand of hands, the door
of doors, the house of cups, stoves, clocks and books, the light of lanterns, bulbs and stars, the dusk of clouds, sea, river,
bats and swans. The speed of the flood is the scene's pressure: frantic under *Come here*, re-made at every choice, slowing as the
dog lies down, nearly held at the end, when each held picture only plays its own shot forward. What would make it bland is a
uniform boil. So the rate is tied to the score and to two deliberate holds (11.9–14.6 s: the wait; 29.0–32 s: chin on paws).

## Native formal language, as it is kept in the project
- **Image corpus:** `build/01_library.py` cuts 55 public-domain shots (2,238 frames, SAM masks) into tiles: the whole frame and the
  SAM subject box, at 64×48, 32×24, 16×12 and 8×6. Each tile keeps shot, frame, mean colour and luminance (`build/cache/library.json`).
- **Salience / montage clusters:** the pools in `01_library.py` (`animal`, `person`, `face`, `hand`, `door`, `house`, `light`, `sky`,
  `floor`, `yard`, `alarm`, `soft`). A tile is chosen from its pool by luminance among 5 random candidates, avoiding the shot it
  replaces; its mean is shifted to the mould's guide colour and its own contrast is kept, so the picture stays visible.
- **Rhythmic slots:** per layer and per frame, a replacement probability (`build/02_render.py`, rates block). The rate is driven by
  the score: the call envelope, the dog's `threat` and `moving`, the lying amount, the holds, and a 100 % re-making of the dog for
  2 frames at each choice (an image accent you can see and hear).
- **Word/image alignments:** the voice is shown as letters made of pictures. *COME HERE.* is alarm clocks, traffic lights,
  ambulances, trumpets and cannons (fast boil); *it's all right.* is flowers, swans, clouds, butterflies (slow); *come in.* is
  lamps. The torrent eats the words when the voice stops.
- **Recurring motifs:** each call sends a ring of alarm pictures out from the person's mouth across wall, sky and floor at 950 px/s
  (it reaches the dog as it backs away); each soft phrase sends a slow ring of flowers (260 px/s); the door opening sends a ring of
  lamps and bulbs (520 px/s): the light comes out as pictures.
- **Voice transcript:** the score's `voice` timeline (call / soft / none) → `SPEECH` in `02_render.py` and the formant voice in `04_sound.py`.

## How the dog is built and moved
The dog's mould (`build/scene.py: dog_parts`) is a computed silhouette in metres, nose to the door, driven only by the score's
`act` values for each frame: crouch, lie, head, ear, tail, wag, rest, look, walk_phase, moving, turn. Torso: a closed spline
between shoulder and hip; legs: capsule chains (standing and lying joint sets blended by `lie`; feet swing with `walk_phase`);
tail angle from `tail` (high → tucked) with `wag`; head height and pitch from `head`, chin on the paws from `rest`, head
foreshortened into the doorway from `look`; ears pricked/flat from `ear`. `turn` flips and squashes the whole cut-out (a card
turning), so the refusal shows its back. The dog is drawn 1.3× a real dog's size so its pictures can be seen. Its position is the
score's `x` in metres (body centre), mapped through one camera: static at 175 px/m until 24.6 s, then a 2.8 s push-in to 245 px/m
after the dog has reached the sill (the approach itself is filmed with a fixed camera).
The mould is never shown: it is filled by the quadtree of animal tiles (32×24 inside, 16×12/8×6 at edges and shading
boundaries), the far legs and ears are given a darker guide, the eye is one found eye frame cut to a circle, and a dark rim
detaches the figure from the boiling ground. Tiles are anchored to the dog, so its pictures travel with it.

The right door jamb is laid over the dog: lying across the sill, its front half is in the doorway and its back half outside.

## Invariants: measured (from the render, `trace.json` and `build/cache/invariants.json`)
`trace.json` is measured per frame from the dog's rendered moulds (not copied from the score): torso-polygon centroid (`x_screen`,
`y_screen`, inverted through the camera to `x_world_measured`), head centroid against torso (`facing`, `head_dx_m`), height of the
back (`posture`), head height, extent. Probes in `05_assemble.py`, each against the score time:

| choice | cue measured on the render | score t | measured t |
|---|---|---|---|
| backs away | x starts increasing | 1.000 | 1.000 |
| stops, watches | head comes up out of the crouch | 2.333 | 2.333 |
| refuses | cowers (head drops), then turns its back | 3.417 | 3.417 |
| turns back to look | head lifts | 7.458 | 7.500 |
| approaches | x starts decreasing | 14.708 | 14.708 |
| lies down at the sill | back lowers | 23.792 | 23.833 |
| hears *come in*: looks in | head rises | 26.400 | 26.458 |

Also measured: the turn of the back itself runs 3.92 → 4.13 s (this is the score's own `turn` curve; the decision at 3.417 is
seen as cowering, ears flattening and tail tucking, and as a full re-making of the dog's pictures); facing measured away from
4.125 to 8.125 s. Retreat goes +x (away from the door). Approach distance 3.41 m measured vs 3.41 m in the score, same frames, same
pace. Max |x_measured − x_score| = 0.033 m. Minimum measured x = 0.558 m (the score's 0.56 sill less 2 mm of pixel quantization).
Final frame: lying, facing the door, body extent −0.53…1.53 m, i.e. across the 0.46–0.58 m jamb, front in the doorway, back
outside. Commands before the dog comes: the call rings and *COME HERE* letters at 1.0 and 3.4 s, the reach at 3.4–4.6 s; changed
circumstances visible before 14.7 s: sitting (5.4 s), door open and light flooding out (6.2 s), low hand (6.8 s), *it's all
right* (7.4 s, 10.4 s).

## Looked at (perceptually judged by the builder, not an independent critic)
Stills and contact sheets at 0.5–31 s across three renders, consecutive-frame crops during the call and the final hold, the
title and made-of cards, the four stills in `stills/`. Judged: the dog reads as a dog in every state; backing away, the turned
back, lying with its back to the door, turning to look, the head-low approach, lying across the sill and looking in are legible
in stills; the call letters are legible; the boil is visibly frantic during calls and nearly still at the end.

## Sound (synthesized, `build/04_sound.py`)
Every replaced picture is a click, from `build/cache/stats.json` (dog: woody, panned with the dog; ground: paper ticks; words:
harsh): the torrent is heard, dense under the calls, sparse ticks in the holds. A 24 Hz projector purr; crickets that thin out
when the light comes; a formant voice (glottal pulses through moving formants) saying the calls loud and the soft phrases
breathy; the door's stick-slip creak at 6.2 s; paw thumps at each step of the score's `walk_phase`; a huff at the refusal, an
exhale at the lie-down and at chin-on-paws; a warm chord that rises with the door light. Measured: per-second RMS 0.21–0.25
under the calls, 0.04–0.07 in the wait, peaks ≤ 0.89. **Not heard by anyone:** no listening was possible here; the formant voice
is surely not intelligible as English, so the words on screen carry the speech.

## What failed and what changed (see `ledger.jsonl`)
- Background as loud as the figures → contrast lowered, wall darkened, dog enlarged 1.3×.
- The boil looked static although 75 % of tiles were replaced: colour matching kept choosing the same brown giraffe shot →
  weaker colour weight, random candidates, avoid the replaced shot.
- The lit dog went flat yellow against the yellow doorway → red-brown base, lower light gain.
- Head was a blank disc → one found face cut to the head; offered hand read as a bowl → forearm and hand built from hand pictures.
- First invariant probes missed two choices by 0.29 and 0.54 s: they measured the wrong cue (x stopping, the turn) instead of the
  cue the score acts on at the choice; centroid included neck and haunch → torso-only measurement.

## What I did not do / unknown
- No independent critic has seen it; no human has watched or listened to it at normal speed. My viewing is of extracted frames.
- Quick, Draw! drawings were not used. The archive door (`kit/archive-door`) and the found `door` shot are the same film (*Straight Talk*).
- Not drawn as pictures: the moulds themselves (computed), the dark rims, the dog's nose darkening, the floor shadow and the
  doorway glow (computed grades). Every visible texture is an archive frame.
- The made-of card counts are tile placements (a tile replaced counts again), not distinct pictures.
- The SCION's operator page and critic report were not produced; this brief's deliverables replace them.

---

## Round 2 (after critic round 1: PASS, narrow)
The critic was right that round 1 was a calm mosaic inside a drawn outline. Repairs, in the critic's order:

1. **Tiles carry the body.** The drawn black rim, the drawn eye circle and the darkened nose are gone. The dog, the person and the
   words are *ragged* layers (`torrent.py`, `ragged=True`): the quadtree descends to a 4×3 tile level at their edges, and a cell is
   painted whole if the shape covers more than half of it, else not at all. So the silhouette is the edge of the pictures. A soft,
   offset shadow under each such layer separates it from the ground, like a paper cut-out lifted off the page (a computed grade,
   not a line). The dog's eye is one small found eye picture, pasted whole (8×6, 16×12 after the push-in), not clipped to a circle.
   The made-of card now says exactly this: the figures and words end where their pictures end; the set is clipped to computed
   shapes; shadows and the glow are computed grades.
2. **Recognisable pictures.** Dog tiles keep 40 % of their own colour (`keep=0.4`). Two larger flank pictures (52×39 px, 73×55
   after the push-in, `keep=0.6`) are pasted on the torso, clipped only to the dog's own tile edges, replaced at 0.6× the dog's
   rate and at every burst. Proof: `stills/proof-tiles-9s.png`, `-19s.png`, `-28s.png`, taken from the delivered compressed
   film (looked at, zoomed: a cat's face and a herd on the flank at 19 s; a lion and a rhinoceros at 28 s).
3. **Rhythm.** The dog is fully re-made for 6 frames at every choice and for 4 frames when its turn crosses zero. At the two
   pivotal choices (3.417 refuse, 23.792 lie down) the **whole frame** is re-cut for 12 frames (every layer replaced every frame).
   Two holds, 11.9–14.6 s and 29–32 s. `rhythm.png` / `rhythm.json`: mean frame-to-frame difference of the scene (whole
   frame and a box around the dog, from `trace.json`). Measured means (whole frame / dog): first call 1.0–2.3 s 12.1 / 15.3; burst 3.42–3.92 s 19.4 / 22.0;
   burst 23.8–24.3 s 18.4 / 18.4; holds 12–14.5 s 0.7 / 0.6 and 29.2–31.9 s 0.9 / 0.9 (out of 255). The rise from 24 to 26.5 s is the camera push-in, not the torrent. The dog's colour now follows the score's
   `trust` (cold dusk grey at 0.1, warm brown-orange at 0.9), with the door light at only 0.35 gain, so no switch happens at 17–20 s.
4. **Approach, head low.** New head carriage in `scene.py`: at the score's head = 0.45 the head centre is 0.07 m below the
   neck base, below the line of the back (checked on flat moulds at 15, 17.5, 20.8, 23.3 s).
5. **Looking in.** With the score's `look`, the head turns away from us into the doorway. The muzzle shortens to nothing, the eye
   disappears, and both ears are seen from behind, with the head in front of the lit interior (frames 26.6–28.0 looked at).
- End-on views: the flip is never thinner than 0.62 (`flip = sign·(0.62 + 0.38·|turn|)`), so the turn is a cut-out turned
  over, marked by a burst, not a squashed table. The offered hand is a cut-out of hand pictures keeping 55 % of their own colour.
  The title subtitle is 52 px.
- Size: `film.mp4` is now a two-pass x264 encode at 2.1 Mb/s plus AAC 128 kb/s (about 10.6 MB). A crf-12 master stays in `build/cache`.

Measured after round 2 (`build/cache/invariants.json`; `tools/paeleo/check_handmade.py` → `invariants.json`: ALL OK). All seven
choice probes are within 0.06 s, as in round 1. The turn of the back runs 4.00–4.13 s (the score's own turn). Minimum measured
x 0.558 m; max |x − score| 0.033 m; the approach covers 3.41 m (score: 3.41 m). The dog ends lying across the jamb, facing the door.

Not done or unknown in round 2: still no human viewing or listening; the cowering, turning dog at 3.9–4.1 s is a low, cold,
crouched shape. I judge it to read as an animal, but that is the builder's judgement. The set (wall, door, floor) is still clipped to smooth computed
shapes, not ragged.

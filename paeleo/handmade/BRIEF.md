# PAE-02 · The threshold, handmade: the brief every swarm receives

## What PAELEO is testing

PEO is Prompt · Ekphrasis · Operation. In PAE-00 one description (a dog at a threshold that may refuse) was operated once, in
cut paper. PAE-01 showed the 54 SCION swarms as *lenses* on that same paper scene: overlays on one drawing. That proves too
little. A lens maps a style on top; it does not make anything.

PAE-02 holds the **prompt and the ekphrasis constant** and lets the **operation** differ completely. Every swarm receives the same
description and the same score of the dog's choices, and builds the scene **from the bottom up**: its own assets, its own
materials, its own way of making a body move. If the description is truly operative, the dog's choices survive every
operation (they are measurable), while everything else (what the dog is made of, how it moves, what the place is, what it
sounds like) belongs to the swarm. One description, many worlds; the invariants are the proof.

## The ekphrasis (the description you must operate)

> Dusk. A doorway, with a sill. A person in the doorway; a dog outside, on the porch.
> The person calls: *Come here.* The dog backs away. The person calls again and reaches for it. The dog turns its back.
> The person steps aside and sits down beside the door. The door opens and light comes out. A hand is offered, low.
> *It's all right*, softly. The dog turns back to look, waits, and in its own time comes, head low, and lies down across the
> sill: half in the doorway, half out. *Come in.* The dog looks in, through the door, and stays where it is.

The viewer must be able to understand the dog and not control it. Commands push it away; changed circumstances earn it.

## The score (what must survive your operation)

`paeleo/handmade/score/threshold-score.json` is the dog's decision trace from the PAELEO machine
(`paeleo/threshold/machine.js`), 32 s at 24 fps (768 frames). Per frame: the dog's `state`, its position `x` along the porch
in metres (threshold at 0, porch steps at 4.9), its facing, its acting intentions (`act`: turn, lie, crouch, ear, tail, wag,
head, rest, look, walk phase), the person's circumstances, the door, and the prompt on screen. Its six choices:

| t (s) | choice |
|---|---|
| 1.00 | watch → retreat (backs away from the call) |
| 2.33 | retreat → watch |
| 3.42 | watch → refuse (turns its back) |
| 7.46 | refuse → watch (turns back to look; the door has opened) |
| 14.71 | watch → approach (head low) |
| 23.79 | approach → lie down (across the sill) |
| 26.4 | hears *come in*: looks in, then settles, and stays |

**Invariants your film must keep** (they are the PAELEO test):

1. The six choices happen at their times, ±0.25 s, and read **as choices on screen** (a viewer can see backing away, the turned
   back, turning to look, coming, lying down, looking in and staying).
2. The dog never enters the house. It ends lying across the threshold, part inside the door frame and part outside.
3. Commands (call, reach) visibly push it away; the changed circumstances (sitting, the open door, the low hand, the soft voice)
   are visible before it comes.
4. Your dog's position follows the score's `x` in your own space (you choose the mapping, but the approach covers the same
   distance at the same pace, and the retreat goes the other way).

Everything else is yours: what the dog, the person, the door and the dusk are made of; whether there are tags or prompts on
screen (the typed prompts are optional; if you show them, show them your way); how the camera works; the sound.

## Build from the bottom up, in your swarm's language

Read your SCION prompt (verbatim, below in your assignment) as the studio you are. Its *native formal language* is what you
build with. Its *hard proof scene* is replaced by this one, but its *bar*, its *evolving inquiry* and its *doctrine* hold.

- **Do not** draw the PAE-00 paper dog and restyle it. Do not import `paeleo/threshold/stage.js` or `paeleo/scion/lenses.js` for
  drawing. You may read `machine.js` and the score.
- **Make your own assets** the way your lineage would: cut them from found footage, draw them, build them as constraints, as
  silhouettes, as doodles, as mosaics, as real footage re-performed. Record where every piece came from.
- **Move them your way**: substitution, pivots, constraint solving, re-timing found motion, drawing-to-drawing selection,
  harmonic rates. Not a generic tween over a borrowed rig.

## Materials you may use (rights recorded)

- `paeleo/handmade/kit/archive-dog/`: 50 frames (384×288, 12 fps) of a real dog approaching a person by a house with a bowl,
  from *Amateur Film New Jersey C* (Home Movies, Internet Archive, public domain), with SAM masks per frame (`masks.json`:
  frame → list of polygons), rig keys (`pose_agent_v8.json`: nose, neck, chest, tail, fore and hind feet) and a 4 s excerpt.
- `paeleo/handmade/kit/archive-door/`: 32 frames of a person opening a door, from *Straight Talk* (NTIS, public domain), with
  SAM masks.
- `paeleo/handmade/kit/quickdraw/`: real Quick, Draw! dog doodles (`quickdraw.ndjson`, one drawing per line, strokes as
  [[x...],[y...]]), CC BY 4.0, Google Creative Lab and contributors; credit it and keep each drawing's `key_id`.
- `/home/user/hartswf0/quickdraw/<category>.part`: thousands of real Quick, Draw! drawings per category (dog 4,164, door
  7,818, house 7,013, hand 5,690, face 4,294, moon 6,214, tree 4,520, fence 6,390, stairs 9,456), ndjson, CC BY 4.0. The
  last line of each file may be partial; drop it. Copy only the drawings you use into your folder, with their `key_id`.
- `paeleo/handmade/kit/found-frames.json`: 98 more public-domain archive shots (3,841 frames, each with SAM masks) under
  `/home/user/hartswf0/secondhand-motion/shots/<category>-sam/` (fish, hand, face, eye, cloud, lantern, horse, cat, door,
  ladder …), each with its source title and rights. Copy what you use into your folder and list it.
- Anything you draw, synthesize or compute yourself.
- **Not allowed**: anything whose rights are unknown (unknown is not permission), WarGames or any commercial film, images
  fetched from the web, generated images from a model you cannot run here.

## Tools here

Python 3 with numpy and Pillow (pip install of other packages may work; cv2 and scipy are not installed), Node 22 with
Playwright and its Chromium (canvas rendering, e.g. pipe `toDataURL` JPEGs into ffmpeg), ffmpeg. No GPU. No network to the
archive. Fonts: `tools/paeleo/fonts/` (Big Shoulders Display, JetBrains Mono, Literata, woff2, with `local.css`).

## What the first six taught (read before you start)

Six swarms built this scene before you (01 Gilliam, 02 Reiniger, 04 Mouris, 08 Sutherland, 38 drawing library, 53 civic
footage); all six passed an independent critic, most only after a repair round. Do not look at their films or code: your
operation must be your own. But every one of them failed first in the same few places, and the critics will look there:

- **Turns.** A flat figure turned by mirroring or squashing collapses edge-on into a tangle, a box or a "giraffe" for a few
  frames (3.5–4.3 s and 7.5–8.5 s). Every frame of both turns must read as a dog, in your language.
- **The refusal must show the back**, clearly, by about 3.9 s, and keep it until 7.46.
- **Turning to look (7.46).** The head must come round to the door on time; a rise that still faces away reads late.
- **Coming, head low.** The head must sit visibly below the line of the back for the whole approach, not only near the end.
- **Feet.** Nothing slides while held: if your dog walks, the feet or the drawings must account for the travel.
- **Lying down across the sill.** The body really lies (no raised hindquarters, no standing legs), with a clear part of it
  inside the door frame and the tail outside. If your materials have no lying dog, say so and solve it in your language.
- **Looking in (26.4).** The head must turn into the lit doorway, not just up or toward the person.
- **No labels doing the acting.** Do not print the dog's state or the choice names on screen during the scene.
- **The soft voice** must be at least 6 dB quieter than the calls, and above any room tone.
- **Claims must be true.** If the end card says "nothing is drawn", nothing may be drawn.

House rules learned the hard way:

- `film.mp4` ≤ 12 MB, H.264 with `-movflags +faststart` (the page streams it).
- Name the stills `stills/still_03.6s.jpg`, `still_09.0s.jpg`, `still_19.0s.jpg`, `still_28.0s.jpg` (JPEG, 1280×720); put any
  other proof images elsewhere (e.g. `proof/`).
- If your camera moves, add `x_world_measured` (metres, measured from your render) to every trace frame; the checker uses it.
- Put regenerable intermediates in `build/cache/` (git-ignored) and keep the folder lean.
- Run `python3 tools/paeleo/check_handmade.py paeleo/handmade/<your folder>` and look at your own frames before you stop.
- The machine is shared with other swarms rendering at the same time. Never use pattern kills (`pkill -f`, `killall`); stop
  only PIDs you started. After every build, check the frame count (768 scene frames, film 38.0 s).
- Record each choice's onset as measured from your render, not only the score's state label, so timing is evidence.

## Deliverables, all inside your folder `paeleo/handmade/<nn>-<slug>/` (touch nothing outside it)

- `film.mp4`: 1280×720, 24 fps, H.264 + AAC. A 3 s title card (`PAE-02 · SCION <nn> · <name>`), the 32 s scene aligned to the
  score frame for frame, then a 3 s card saying what it is made of. 38 s in all. Sound is part of the work.
- `trace.json`: what your dog actually did, per scene frame: `{i, t, state, x_score, x_screen, y_screen, facing, posture}`,
  measured from your own render, so the invariants can be checked.
- `assets.json`: every asset: what it is, where it came from (file path, source title, archive URL, key_id), rights, and the
  operation that made it (crop, mask, trace, halftone, drawn, synthesized).
- `method.md`: your swarm, the native formal language you used, how the dog is built and moved, what is protected, what failed
  and what you changed, and what you did not do. Honest evidence: say what was measured, what was looked at, what is unknown.
- `build/`: the scripts that make the film from the kit and the score, so it can be rebuilt (`build/make.sh` runs them all).
- `stills/`: four stills from the scene, at 3.6 s (refusal), 9 s (watching), 19 s (approach) and 28 s (lying across the sill).
- `ledger.jsonl`: one line per attempt and what you saw.

Check your own film by extracting frames and looking at them (Read tool on images) before you stop. Do not approve your own
work: an independent critic will judge it against this brief and your SCION prompt's bar. Do not run git; do not commit.
Stop when the film is watchable and the invariants hold, or when you hit a justified no-progress boundary; say which.

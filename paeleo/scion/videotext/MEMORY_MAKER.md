# MEMORY MAKER — how it was made

`maker.html` is a Dreams-style maker and player in the Contaminant / Afterlight world. It was built with the [video-to-game](https://github.com/lovisdotio/video-to-game) flow, adapted so that the design video and every asset come from our own film and archive. No fal or other generative model was used.

## Swim the films (the ocean)
Each of eight of our own films is an image-jellyfish: thousands of flecks coloured from the film, its bell cycling through sixteen frames of it (`memory-maker/films/*.jpg`, made with ffmpeg; the list is in `memory-maker/films.json`). The films:
- Contaminant Jelly
- the film without words
- Two cuts of one take
- PAELEO 00
- Library of Congress
- The Flour Tower
- It's All Right
- Abominable House

Swim into one and you are inside the film:
- **You are the projector's motor.** The real video plays only while you swim; your speed is its speed (×0.25 to ×2.5), and when you let go, it stops. The film's own sound plays and the score drops out.
- **The present frame floats ahead of you** as a field of flecks lifted by its light.
- **The frames you pass stay behind** as faint echoes, the film laid out in space as time.
- **Catch a moment** (the button, or C) and it becomes a small jellyfish of that image that follows you.
- **Surface** to swim to another film.
- **Play your moments** (two or more) and they play as a memory, each with its film and time code.

Measured: inside a film, the video advanced 7.2 s during 3 s of swimming and stopped within 2 s of letting go. Two moments were caught and played back with no page errors.

## The loop (after Dreams' make, play and remix)
- **Shape (the maker).** Fourteen public-domain archive frames float as clouds of light ("flecks", after Dreams' BubbleBath engine).
  - Pick frames one after another to build a memory of up to nine frames.
  - A frame that shares a visible feature with the one before it joins with a gold cut ("hand", "door"); otherwise the join is a blue jump.
  - Hold a frame in your memory to make it last longer, from 0.5 to 5 s.
  - Tap it to take it out.
  - A small wisp of light, the imp, is your hand on desktop.
- **Dream (possess and play).** You are the jellyfish, also made of flecks.
  - Your memory stands ahead of you in the dark, one frame after another. The longer a frame was held, the longer the swim to it.
  - Each frame is mist from afar. Steer onto its gold ring, the feature it shares with the frame before, and it comes into focus.
  - A frame with a touch carries the censor's sweeping red light. Cross through it and the frame burns.
  - Controls: touch or click and hold where you want to go, or arrow keys / WASD. The bell pulses you forward on the beat.
- **The film.** Your memory plays back as film:
  - each frame lasts as long as you held it
  - each is as sharp as you reached it (blurred where you missed)
  - burned frames show the burn
  - the camera travels from each frame's shared feature to the next, so every cut lands on its match
- **Share and remix.** The memory lives in the link (`#m=...`, three characters per frame: frame and duration). Opening a shared link offers "Dream this shared memory"; Remix takes it into the maker.

## The flow, step by step
| step | video-to-game | here |
|---|---|---|
| 1 Video | generate a gameplay clip | our own film, `../contaminant/cinema/film.mp4` (62 s) |
| 2 Study | `study_video.py` | 248 frames, 29 cuts. Palette #040402 #16120c #292319 #453a27 #66573a (near-black to warm umber), plus the jellyfish's gold and the cool afterimage blue |
| 3 Assets | fal images, 3D, sound | the 14 archive frames sampled in code into 10,800 flecks each, with depth lifted from luminance. The jellyfish is built from 2,000 flecks. The score is generated in WebAudio: a pad, a heartbeat, and the memory's notes |
| 4 Build | Three.js, state contract | Three.js 0.160 (vendored, MIT), custom gaussian fleck shader with additive blending, `window.__mm()` state |
| 5 Match the look | side-by-side pairs | `memory-maker/side_by_side.jpg`: film at 20 s against dream mode, and film at 6 s against the memory's film playback |
| 6 Play it | scripted take | a bot shapes a memory (bulb, lantern, butterfly, tool, door), holds one frame to 2.3 s, dreams it by holding toward each gold ring, and reaches the film and end card |

## Spec written from the study
- **Camera.** Close third person on the jellyfish, nearly on the axis of the frames. Archive frames are shown full-frame in sepia; the reel sits in a gate.
- **Hero.** A gold domed jellyfish with hairline tentacles; the glow cools toward blue.
- **Mechanic.** Carrying archive frames, matching them by a visible feature, and the censor's burn.
- **Key moment.** A frame coming into focus out of the dark, and the matched cut.
- **Look.** Near-black ground, warm sepia, gold glow, an iris vignette, film grain, no HUD beyond one hint line.

## Measured (headless Chromium, software GL)
- No page errors from title through shape, dream, film and end.
- The scripted dream took about 28 s for five frames.
- 9–16 fps in the maker under software rendering. That reflects the CPU renderer, not a GPU; real-device frame rate is unmeasured.

## Differs from the flow (honestly)
- **No generated video or fal assets.** The design video is our film and the assets are the archive. This is deliberate: it is a counter-archive, and every frame has recorded provenance (PAE-02 manifests under `../../handmade/`).
- **No 3D models.** Everything is points, after Dreams' flecks and Afterlight's splats.
- **Dream mode is not a copy of the film's camera.** It is a corridor of frames the film never shows. The side-by-side shows the shared palette and grade, not identical shots.
- **Not yet played by a person.** Tablets and phones were tested only as a desktop viewport.

# PAE-03 · How the cuts and openings were made

Everything here was built from the six self-measuring films in `../films/`. The scripts are kept as they ran; their paths point at the working folders they were made in (`/home/claude/...`), so read them as a record rather than a one-command build.

## The world camera (`world-camera/`)
Every film records the sack and the penny in its own world metres (`window.PAE_TRACE`). `calibration.json` maps each film's metres to its canvas, measured from known points (the tower at x = 0.8 m, the table at y = 0, the penny at y ≈ 0.95 m). With that, one virtual camera can shoot all six films in a single shared world: a cut between films keeps the sack in the same place, pose and scale, and only the material changes.
- `film.py` is the shot list: story time per shot, which film, camera keyframes or a lock on the current film's sack, speed ramps, crossfades, shakes. It writes the crop for every frame.
- `cap.js` seeks each film (`PAE_SEEK`) and screenshots exactly that crop at high resolution. Slow motion is real: the films are sampled between their own frames.
- `compose.py` assembles the frames and titles.

## The openings (`openings/` and `../live/`)
Three title sequences, each playable live in `../live/`:
1. **Picture book**: ink on paper; the sack pours its own flour into the mug, and the game is acted step by step.
2. **Flour grains**: about 20,000 grains under one lamp. Upside-down letters are poured, packed, flipped, given a penny, cut on four turns, collapsed; the sack's hop; the flour rises into the title.
3. **Cel tower**: the same game, but every brick is an animation cel cut around the sack from one of the six films (`atlas.jpg`, 24 frames per film, captured by `celcap.js`), each playing its own loop.

## The sound (`sound/`)
The flour-sack test for sound is the one-source exercise: score a scene with a single material and no melody to lean on, so feeling has to come from rhythm, density, pitch and weight. Here the one material is the grain: `gran.py` builds every sound from short windowed grains. Each cel landing is a pitched grain (the tower plays a rising A-minor pentatonic as it stacks), the pour is a grain hiss, the knife and collapse are grain bursts, the title chord is one grain per arriving cel. `score_gran.py` re-voices the film's score from grains with the same cue sheet as `score.py`.

## The other cuts
- `compilation/`: the 4-minute cut of all six films with title cards and the YouTube description.
- `frankenstein/`: the 40-second cut with sewn seams and 59 cuts across bodies under one score.
- `short/`: the vertical short, framed by hand per shot.

#!/bin/sh
# SCION 16 JibJab: rebuild everything from the kit and the score. Run from anywhere.
set -e
D=$(cd "$(dirname "$0")/.." && pwd)
cd "$D"
mkdir -p build/cache stills proof
python3 build/prep.py                      # face slots (three casts), fur plate, door plate, Quick, Draw! drawings used
python3 build/plate.py                     # the body plate: rig pieces and turn plates cut from the archive dog footage
python3 build/perform.py                   # the one performance: channels, stepping solver, events
python3 build/sound.py                     # synthesized sound from the performance's events; sound-levels.json
node build/render.mjs film paper build/cache/video-paper.mp4 build/cache/measure-paper.json
ffmpeg -y -loglevel error -i build/cache/video-paper.mp4 -i build/cache/sound.wav -c:v copy -c:a aac -b:a 128k -shortest -movflags +faststart film.mp4
python3 build/measure.py paper             # trace.json from the render's own mattes
python3 build/manifest.py                  # matte manifest: slot views and occlusion spans, contacts
node build/render.mjs grid build/cache/grid.mp4      # comparison viewer: the same performance in three casts + the plate
ffmpeg -y -loglevel error -i build/cache/grid.mp4 -ss 3 -i build/cache/sound.wav -c:v copy -c:a aac -b:a 96k -shortest -movflags +faststart proof/comparison.mp4
node build/render.mjs stills paper stills 3.6,9,19,28 named
for c in paper doodle home; do node build/render.mjs stills $c proof/casts 3.9,7.7,19,27.2; done
python3 /home/user/bolas/tools/paeleo/check_handmade.py "$D"
ffprobe -v error -count_frames -show_entries stream=codec_name,nb_read_frames,duration -of compact film.mp4

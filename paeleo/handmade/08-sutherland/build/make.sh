#!/bin/sh
# SCION 08 · Sutherland — rebuild film.mp4, trace.json, checks.json and stills from the kit and the score.
set -e
cd "$(dirname "$0")"
python3 world.py            # solve pass: constraint graphs, pen script, relaxation, sound events
python3 render.py           # display files -> vector-CRT raster -> _cache/video.mp4 (+ render_meas.json)
python3 sound.py            # numpy synthesis -> _cache/sound.wav
python3 check.py            # ../trace.json, ../checks.json
ffmpeg -y -loglevel error -i _cache/video.mp4 -i _cache/sound.wav -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart ../film.mp4
# stills: 3.6 s, 9 s, 19 s, 28 s of the scene (scene starts after the 3 s title)
for t in 3.6 9 19 28; do
  ss=$(python3 -c "print(3 + $t + 0.5/24)")
  ffmpeg -y -loglevel error -ss "$ss" -i ../film.mp4 -frames:v 1 -q:v 2 "../stills/still_${t}s.jpg"
done
echo done

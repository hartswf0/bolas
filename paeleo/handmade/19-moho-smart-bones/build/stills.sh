#!/bin/bash
# stills taken from the encoded film (scene t + 3 s title)
cd "$(dirname "$0")/.."
for t in 03.6 09.0 19.0 28.0; do ffmpeg -y -loglevel error -ss $(python3 -c "print($t+3+0.001)") -i film.mp4 -frames:v 1 -q:v 3 stills/still_${t}s.jpg; done
ls -la stills

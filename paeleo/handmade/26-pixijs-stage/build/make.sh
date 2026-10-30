#!/usr/bin/env bash
# SCION-26 · PixiJS archive stage: rebuild film.mp4, trace.json, stills from the kit and the score.
# Needs: python3 (numpy, Pillow), node 22, Playwright + its Chromium (global install here: /opt/node22/lib/node_modules/playwright), ffmpeg.
# PixiJS is installed into build/node_modules and deleted after the build to keep the folder lean. To reinstall:
#     (cd build && npm install pixi.js@7.4.2)
set -euo pipefail
cd "$(dirname "$0")/.."
B=build; C=build/cache; mkdir -p $C stills proof
[ -f $B/node_modules/pixi.js/dist/pixi.min.js ] || (cd $B && npm install --no-audit --no-fund pixi.js@7.4.2)
python3 $B/atlas.py                                  # cut fragments -> build/atlas/atlas.png + atlas.json
node $B/render.js film                               # stage -> build/cache/video.mp4 (912 frames) + measure.json
python3 $B/sound.py                                  # -> build/cache/sound.wav (paws timed to measured feet)
# two-pass H.264 at 2.1 Mbit/s keeps the grain and stays under 12 MB
(cd $C && ffmpeg -y -loglevel error -i video.mp4 -c:v libx264 -preset slow -b:v 2100k -pass 1 -passlogfile p2 -an -f null /dev/null && \
 ffmpeg -y -loglevel error -i video.mp4 -i sound.wav -map 0:v -map 1:a -c:v libx264 -preset slow -b:v 2100k -pass 2 -passlogfile p2 \
   -pix_fmt yuv420p -c:a aac -b:a 128k -shortest -movflags +faststart ../../film.mp4 && rm -f p2*)
python3 $B/trace.py                                  # -> trace.json (measured onsets)
python3 $B/assets.py                                 # -> assets.json
# stills from the encoded film (scene t + 3 s title)
for s in 03.6 09.0 19.0 28.0; do
  ffmpeg -y -loglevel error -ss $(python3 -c "print($s+3+0.02)") -i film.mp4 -frames:v 1 -q:v 3 stills/still_${s}s.jpg
done
python3 ../../../tools/paeleo/check_handmade.py . || true
ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 film.mp4
echo "remove node_modules: rm -rf $B/node_modules"

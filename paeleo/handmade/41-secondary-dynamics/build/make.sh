#!/usr/bin/env bash
# SCION 41 · Secondary Dynamics — rebuild the film from the score.  bash build/make.sh   (from anywhere)
# Needs: node 22 + playwright (chromium), python3 + numpy + Pillow, ffmpeg. About 4 minutes on 4 CPUs.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; TOP="$(dirname "$HERE")"
export NODE_PATH="${NODE_PATH:-/opt/node-tools/node_modules}"
mkdir -p "$HERE/cache" "$TOP/stills" "$TOP/proof"
node "$HERE/test_dynamics.js"                      # unit tests of the dynamics library
node "$HERE/scene.js" tuned                        # primary poses from the score + secondary solve -> cache/sim.json
node "$HERE/scene.js" none                         # the no-secondary-motion alternative (comparison only)
node "$HERE/scene.js" loose                        # underdamped preset (comparison only)
node "$HERE/render.js" film                        # picture + measurements from the drawn dog layer
python3 "$HERE/sound.py"                           # synthesized voice + foley from the solver's events
python3 "$HERE/assemble.py"                        # film.mp4, trace.json, stills/
python3 "$HERE/test_scene.py"                      # the bar's numeric assertions -> proof/assertions.json
# synchronized split view of the damping presets -> proof/presets.mp4
C="$HERE/cache"
for seg in "A 77 230" "B 626 700"; do set -- $seg
  LABEL="no secondary motion" node "$HERE/render.js" clip "$C/sim-none.json" "$C/cmp$1-none.mp4" $2 $3 &
  LABEL="tuned (the film)" node "$HERE/render.js" clip "$C/sim.json" "$C/cmp$1-tuned.mp4" $2 $3 &
  LABEL="underdamped x0.35" node "$HERE/render.js" clip "$C/sim-loose.json" "$C/cmp$1-loose.mp4" $2 $3 &
  wait
  ffmpeg -loglevel error -y -i "$C/cmp$1-none.mp4" -i "$C/cmp$1-tuned.mp4" -i "$C/cmp$1-loose.mp4" \
    -filter_complex "[0]scale=640:360[a];[1]scale=640:360[b];[2]scale=640:360[c];[a][b][c]vstack=3" -c:v libx264 -crf 22 -pix_fmt yuv420p "$C/stack$1.mp4"
done
ffmpeg -loglevel error -y -i "$C/stackA.mp4" -i "$C/stackB.mp4" -filter_complex "[0][1]concat=n=2:v=1" -c:v libx264 -crf 22 -pix_fmt yuv420p -movflags +faststart "$TOP/proof/presets.mp4"
python3 "$(cd "$TOP/../../.." && pwd)/tools/paeleo/check_handmade.py" "$TOP"

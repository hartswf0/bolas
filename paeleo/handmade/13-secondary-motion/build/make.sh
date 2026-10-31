#!/usr/bin/env bash
# SCION 13 · Secondary Motion — rebuild everything from the score.   bash build/make.sh   (from anywhere)
# Needs: node 22 + playwright (chromium), python3 + numpy + Pillow, ffmpeg. About 4 minutes on 4 CPUs.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; TOP="$(dirname "$HERE")"; C="$HERE/cache"
export NODE_PATH="${NODE_PATH:-/opt/node-tools/node_modules}"
mkdir -p "$C" "$TOP/stills" "$TOP/proof"
node "$HERE/render.js" film tuned            # primary trajectories + secondary solve + drawing + mask measurements -> cache/scene.mp4, measure.json
python3 "$HERE/sound.py"                     # synthesized voices and foley driven by the solver -> cache/sound.wav
python3 "$HERE/assemble.py"                  # film.mp4, trace.json, stills/, invariants.json (runs the PAELEO checker)
python3 "$HERE/test_motion.py"               # numeric assertions -> proof/assertions.json
# with/without playback: the same primary motion with no secondary motion, a generic oscillator, and the tuned presets
for seg in "A 78 130 640,250" "B 566 612 420,380"; do set -- $seg
  for pre in none generic tuned; do
    node "$HERE/render.js" clip $pre "$C/cmp$1-$pre.mp4" $2 $3 "$pre" &
  done; wait
  ffmpeg -loglevel error -y -i "$C/cmp$1-none.mp4" -i "$C/cmp$1-generic.mp4" -i "$C/cmp$1-tuned.mp4" \
    -filter_complex "[0]crop=640:360:${4%,*}:${4#*,}[a];[1]crop=640:360:${4%,*}:${4#*,}[b];[2]crop=640:360:${4%,*}:${4#*,}[c];[a][b][c]hstack=3,scale=1440:270" \
    -c:v libx264 -crf 22 -pix_fmt yuv420p "$C/stack$1.mp4"
done
ffmpeg -loglevel error -y -i "$C/stackA.mp4" -i "$C/stackB.mp4" -filter_complex "[0][1]concat=n=2:v=1,setpts=2*PTS" -r 24 -c:v libx264 -crf 22 -pix_fmt yuv420p -movflags +faststart "$TOP/proof/compare_none_generic_tuned.mp4"
rm -f "$C"/cmp*.mp4 "$C"/stack*.mp4
du -sh "$TOP"

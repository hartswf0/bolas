#!/bin/sh
# Rebuild PAE-02 SCION 47 from nothing but the score, CMU Flite and this folder's code.
# Needs: python3 (numpy, scipy), node 22 + playwright chromium (NODE_PATH), ffmpeg, libflite 2.2 with voice cmu_us_slt.
set -e
B=$(cd "$(dirname "$0")" && pwd); F=$(dirname "$B")
export NODE_PATH=${NODE_PATH:-/opt/node-tools/node_modules}
python3 "$B/voice.py"        # synthesize the lines, read phoneme timing from the synthesizer
python3 "$B/plot_align.py"   # proof/alignment.png
python3 "$B/plan.py"         # place the lines and the world's sounds: audio_timeline.json
python3 "$B/xsheet.py"       # exposure sheet: dog sprite keys, person pose + visemes, door, light; foley.json
python3 "$B/mix.py"          # synthesize foley, mix, measure loudness: cache/mix.wav, audio_measure.json
node "$B/render.js" film     # picture (title + 768 scene frames + end card) and the ID-pass measurements
python3 "$B/measure.py"      # trace.json: measured onsets, positions, facing, posture, lip-sync assertions
ffmpeg -y -loglevel error -i "$B/cache/picture.mp4" -i "$B/cache/mix.wav" -c:v copy -c:a aac -b:a 160k -movflags +faststart -shortest "$F/film.mp4"
python3 "$B/stills.py"       # stills/ from the film
python3 "$B/plot_mix.py"     # proof/mix_levels.png
python3 "$F/../../../tools/paeleo/check_handmade.py" "$F"

#!/bin/bash
# SCION 19 · rebuild everything from the score: render, measure, test, sound, cards, encode, stills, check
set -e
cd "$(dirname "$0")"
rm -rf cache/frames cache/seq
node render.js scene cache/frames                 # 768 scene frames + measures.json (pixel mask + rig geometry)
python3 trace.py                                   # ../trace.json
node tests.js                                      # ../proof/rig_tests.json, ../proof/corrections.json
python3 sound.py                                   # cache/scene.wav, ../proof/levels.json
node render.js card title cache/title.jpg
node render.js card end cache/end.jpg
bash assemble.sh                                   # ../film.mp4
bash stills.sh                                     # ../stills/
rm -rf cache/frames/*.jpg cache/seq                # keep the disk lean
python3 ../../../../tools/paeleo/check_handmade.py ..

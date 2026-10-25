#!/bin/sh
# Rebuild SCION-GRABCUT's threshold from the kit and the score. Intermediates go to build/cache (regenerable).
set -e
B=$(cd "$(dirname "$0")" && pwd)
cd "$B"
python3 plate.py                 # clean background plate of the dog shot (source image restorer)
python3 extract.py dog           # graph-cut every dog frame (BK max-flow, GrabCut iterations, alpha cleanup)
python3 extract_world.py         # woman, door panel, hand (cut from its card), pillar, shrub, bowl
python3 cards.py                 # title + end cards
rm -f cache/measure*.json
python3 render.py                # 768 scene frames + measure.json (measured from the rendered dog layers)
python3 trace.py                 # trace.json + measured choice onsets
python3 sound.py                 # sound.wav + sound_levels.json
python3 export_pieces.py         # RGBA pieces, contour masks, failure masks, transforms -> ../pieces
sh assemble.sh                   # film.mp4
python3 stills.py                # stills/
python3 ../../../../tools/paeleo/check_handmade.py ..
python3 assets.py

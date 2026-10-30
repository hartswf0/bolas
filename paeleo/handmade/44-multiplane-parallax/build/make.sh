#!/bin/sh
# Rebuild SCION 44 Multiplane Parallax from the kit, the archive frames and the score (~6 min on 3 cores).
set -e
cd "$(dirname "$0")"
python3 world.py                                   # build the collage planes (check)
python3 render.py 0 768 3 & P0=$!                  # the multiplane camera: 768 scene frames + measurements
python3 render.py 1 768 3 & P1=$!
python3 render.py 2 768 3 & P2=$!
wait $P0 $P1 $P2
test "$(ls cache/frames/s*.jpg | wc -l)" -eq 768
python3 sound.py                                   # synthesize and place the sound in depth; measure levels
python3 scene.py                                   # export the depth scene graph, camera path, assets.json
python3 assemble.py                                # trace.json (measured states), cards, film.mp4, stills from the film
rm -rf cache/frames cache/film                      # rendered frames are regenerable; keep the folder lean
python3 ../../../../tools/paeleo/check_handmade.py ..

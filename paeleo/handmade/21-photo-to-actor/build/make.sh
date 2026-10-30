#!/bin/bash
# SCION 21 . Photo-to-Actor Factory . rebuild everything from the kit and the score.
# python3 (numpy, Pillow, fontTools), ffmpeg with libflite. ~4 min on 4 cores.
set -e
cd "$(dirname "$0")/.."
mkdir -p build/cache
python3 build/prep.py          # photograph preparer: frames + SAM masks -> photo-textured parts, angle artwork, sources/
python3 build/fit.py           # landmark fitter: automatic fit, anatomy tests, recorded hand corrections, review pairs
python3 build/perform.py       # retargeting operator + facial performer: score -> actor controls per frame
python3 build/sound.py         # voices (flite), dusk, door, paws on touchdown frames -> scene.wav, sound-levels.json
build/render_all.sh            # 768 scene frames (JPEG, build/cache/frames) + per-frame dog measurements
python3 build/cards.py         # title + end card
CRF=${CRF:-23} build/assemble.sh   # film.mp4: 3 s + 32 s + 3 s, 912 frames, H.264 + AAC, faststart
python3 build/measure.py       # trace.json with measured onsets
for pair in "03.6:158" "09.0:288" "19.0:528" "28.0:744"; do   # stills are taken from the encoded film
  ffmpeg -hide_banner -loglevel error -y -i film.mp4 -vf "select='eq(n\,${pair#*:})'" -vsync 0 -q:v 2 -frames:v 1 "stills/still_${pair%:*}s.jpg"
done
(cd ../../.. && python3 tools/paeleo/check_handmade.py paeleo/handmade/21-photo-to-actor)
find build/cache/frames -name '*.jpg' -delete   # rendered frames are deleted after encoding (shared disk)

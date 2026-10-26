#!/bin/sh
# SCION 46 · rebuild everything from the kit and the score
set -e
cd "$(dirname "$0")"
python3 face_source.py     # source face annotator: cut + landmarks + registration manifest
python3 rig.py             # score -> pose state (pivots, controls, camera)
python3 pose.py            # solver: landmark vectors, stepper, IK, tail chain
python3 register.py        # view-matching + fits per plate (registration manifest)
./render_all.sh            # 768 scene frames
python3 sound.py           # synthesized sound, measured levels
python3 cards.py           # title / end cards
./assemble.sh              # film.mp4
python3 measure.py         # trace.json + measured choices + numeric invariants
python3 stills.py          # stills/ and proof sheets
python3 ../../../../tools/paeleo/check_handmade.py ..

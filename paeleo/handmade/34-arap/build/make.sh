#!/bin/bash
# Rebuild SCION 34 from the score: drawings -> meshes -> performance -> ARAP render -> sound -> cards -> film -> trace.
set -e
cd "$(dirname "$0")"
python3 draw_dog.py && python3 draw_dog.py views && python3 draw_person.py
python3 mesh.py P_body P_head R0_body R0_head F0_body F0_head Q_stand Q_sit Q_arm
python3 perform.py
rm -f cache/measure_*.json
python3 render.py 0 353 & P1=$!
python3 render.py 353 768 & P2=$!
wait $P1 $P2
python3 sound.py
python3 cards.py
bash assemble.sh
python3 trace.py
python3 stills.py
python3 ../../../../tools/paeleo/check_handmade.py ..
rm -rf cache/frames      # frames are regenerable; keep the folder lean

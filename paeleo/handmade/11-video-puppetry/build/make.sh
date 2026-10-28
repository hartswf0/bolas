#!/usr/bin/env bash
# SCION 11 · rebuild everything from the kit and the score:
# puppets (cut-outs + handles proof) -> stage -> performance -> render (bent footage) -> trace -> sound -> cards -> film
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p cache ../stills ../proof ../data
python3 puppets.py
python3 stage.py
python3 perform.py
WORKERS=${WORKERS:-3} python3 render.py
python3 trace.py > /dev/null
python3 sound.py > /dev/null
python3 cards.py
bash assemble.sh
python3 ../../../../tools/paeleo/check_handmade.py ..
rm -rf cache/frames   # the house rule: rendered frames do not stay on the shared disk

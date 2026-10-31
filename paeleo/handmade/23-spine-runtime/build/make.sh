#!/usr/bin/env bash
# SCION 23 · rebuild everything from the score: atlas -> skeleton + clips -> set -> performance (runtime) ->
# render -> trace -> sound -> cards -> film -> check
set -euo pipefail
cd "$(dirname "$0")"
python3 atlas.py           # paint the atlas (actor/actors.png, .atlas, .atlas.json)
python3 author.py          # actor/dog.skel.json, dog.clips.json, person.skel.json, person.clips.json
python3 set.py             # the painted set plate and door
python3 perform.py         # actor/dog.timeline.json; runtime over 768 frames; proof/geometry.json
WORKERS=${WORKERS:-3} python3 render.py
python3 measure.py > /dev/null   # trace.json from the rendered pixels
python3 sound.py > /dev/null     # cache/film.wav, proof/levels.json
python3 cards.py
bash assemble.sh

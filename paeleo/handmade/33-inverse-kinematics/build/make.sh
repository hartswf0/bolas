#!/usr/bin/env bash
# SCION 33 · rebuild the film from the score: set -> performance (IK) -> render -> trace -> sound -> cards -> film
set -euo pipefail
cd "$(dirname "$0")"
OUTDIR=..
python3 bg.py
python3 perform.py
WORKERS=${WORKERS:-3} python3 render.py
python3 trace.py > /dev/null
python3 sound.py
python3 cards.py
python3 proof.py
bash assemble.sh

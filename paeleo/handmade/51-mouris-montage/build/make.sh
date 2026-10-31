#!/usr/bin/env bash
# SCION 51 · rebuild the film from the kit's found shots and the score.
# inventory -> choreography -> cutting score + words -> render (3 workers) -> trace -> sound -> cards + encode -> assets -> check
set -euo pipefail
cd "$(dirname "$0")"
FOLDER="$(cd .. && pwd)"
python3 inventory.py
python3 choreo.py
python3 cuts.py
mkdir -p cache/frames cache/meas
find cache/frames -name 's*.jpg' -delete
pids=()
for k in 0 1 2; do python3 render.py "$k" 768 3 & pids+=($!); done
for p in "${pids[@]}"; do wait "$p"; done
n=$(find cache/frames -name 's*.jpg' | wc -l); [ "$n" -eq 768 ] || { echo "expected 768 scene frames, got $n"; exit 1; }
python3 trace.py
python3 sound.py
python3 assemble.py encode
python3 assets.py
python3 proof.py
# rendered frames are regenerable: delete them after encoding (shared disk)
find cache/frames -name 's*.jpg' -delete
cd "$FOLDER/../../.." && python3 tools/paeleo/check_handmade.py "$FOLDER"

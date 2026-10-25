#!/bin/sh
# render the 768 scene frames in 4 parallel slices (contiguous, so the plate cache is reused)
cd "$(dirname "$0")"
rm -f cache/trace_parts/*.json
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
python3 -c "import render; render.static()"
python3 render.py 0 192 & python3 render.py 192 384 & python3 render.py 384 576 & python3 render.py 576 768 &
wait

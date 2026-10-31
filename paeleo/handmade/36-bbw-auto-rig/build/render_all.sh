#!/bin/bash
# render the 768 scene frames in 4 parallel chunks (only the PIDs started here are waited on)
cd "$(dirname "$0")"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
rm -f cache/meas_*.json
pids=()
for c in "0 192" "192 384" "384 576" "576 768"; do
  python3 render.py $c > cache/render_${c// /_}.log 2>&1 &
  pids+=($!)
done
for p in "${pids[@]}"; do wait $p || exit 1; done
ls cache/frames/s*.jpg | wc -l

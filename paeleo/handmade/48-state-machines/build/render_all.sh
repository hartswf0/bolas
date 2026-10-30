#!/bin/bash
# render the 768 scene frames on 4 processes (each process renders its own range; waits only for its own PIDs)
cd "$(dirname "$0")"
mkdir -p cache/frames
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
pids=()
for r in "0 200" "200 400" "400 590" "590 768"; do
  python3 render.py $r > cache/render_${r// /_}.log 2>&1 &
  pids+=($!)
done
for p in "${pids[@]}"; do wait $p; done
ls cache/frames | wc -l

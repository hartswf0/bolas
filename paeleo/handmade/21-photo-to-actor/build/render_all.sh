#!/bin/bash
# render the 768 scene frames in 4 parallel slices (PIDs recorded; only these are waited on)
cd "$(dirname "$0")/.."
rm -f build/cache/measure_*.json build/cache/alpha_*.npz
pids=()
for s in "0 191" "192 383" "384 575" "576 767"; do
  python3 build/render.py $s & pids+=($!)
done
for p in "${pids[@]}"; do wait $p; done
ls build/cache/frames/*.jpg | wc -l

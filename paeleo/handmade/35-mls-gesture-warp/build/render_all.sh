#!/bin/bash
# render the 768 scene frames in 4 worker processes (each writes its own frames; PIDs are only our own)
cd "$(dirname "$0")"
N=768; P=${P:-4}
pids=()
for k in $(seq 0 $((P-1))); do
  a=$((k*N/P)); b=$(((k+1)*N/P))
  python3 render.py $a $b > cache/render_$k.log 2>&1 &
  pids+=($!)
done
for p in "${pids[@]}"; do wait $p || { echo "worker $p failed"; exit 1; }; done
ls cache/frames/*.jpg | wc -l

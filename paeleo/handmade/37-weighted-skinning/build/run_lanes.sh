#!/bin/bash
# render the 768 scene frames in N parallel lanes (default 3); each lane is a PID this script started and waits for
cd "$(dirname "$0")"
N=${LANES:-3}; pids=()
for ((k=0;k<N;k++)); do
  a=$((768*k/N)); b=$((768*(k+1)/N))
  python3 render.py $a $b > cache/lane$k.log 2>&1 &
  pids+=($!)
done
wait "${pids[@]}"
ls cache/frames/*.jpg | wc -l

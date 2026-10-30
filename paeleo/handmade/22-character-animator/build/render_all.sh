#!/bin/sh
# render the 768 scene frames on 4 workers; waits only on the PIDs it started
cd "$(dirname "$0")"
rm -rf cache/frames cache/measure
pids=""
for k in 0 1 2 3; do
  python3 render.py $k 4 & pids="$pids $!"
done
for p in $pids; do wait $p; done
n=$(ls cache/frames | wc -l)
echo "rendered $n frames"
[ "$n" -eq 768 ] || { echo "frame count wrong"; exit 1; }

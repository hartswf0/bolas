#!/bin/sh
# renders the 768 scene frames in 3 parallel chunks (only PIDs started here are waited on)
cd "$(dirname "$0")"
mkdir -p cache/frames
python3 render.py 0 256 --out cache/frames & P1=$!
python3 render.py 256 512 --out cache/frames & P2=$!
python3 render.py 512 768 --out cache/frames & P3=$!
wait $P1 $P2 $P3
ls cache/frames | wc -l

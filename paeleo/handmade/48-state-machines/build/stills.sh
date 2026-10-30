#!/bin/bash
# the four stills, taken from the final film (scene frame + 72 title frames)
set -e
cd "$(dirname "$0")/.."
mkdir -p stills
for pair in "03.6 86" "09.0 216" "19.0 456" "28.0 672"; do
  set -- $pair
  n=$(( $2 + 72 ))
  ffmpeg -y -loglevel error -i film.mp4 -vf "select=eq(n\,$n)" -vframes 1 -q:v 2 stills/still_$1s.jpg
done
ls -la stills

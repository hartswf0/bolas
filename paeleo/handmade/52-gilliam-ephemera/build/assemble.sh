#!/bin/sh
# Title (72) + scene (768) + end card (72) = 912 frames = 38.0 s at 24 fps, with the synthesized track.
set -e
B=$(cd "$(dirname "$0")" && pwd); C="$B/cache"; OUT="$B/../film.mp4"
rm -rf "$C/seq"; mkdir -p "$C/seq"
n=0
for p in t s e; do
  for f in $(ls "$C/frames" | grep "^$p" | sort); do
    ln -s "$C/frames/$f" "$C/seq/$(printf '%04d' $n).jpg"; n=$((n+1))
  done
done
echo "frames: $n"
ffmpeg -hide_banner -loglevel error -y -framerate 24 -i "$C/seq/%04d.jpg" -i "$C/sound.wav" \
  -c:v libx264 -preset slow -crf ${CRF:-25} -pix_fmt yuv420p -c:a aac -b:a 160k -shortest \
  -movflags +faststart "$OUT"
ls -l "$OUT"

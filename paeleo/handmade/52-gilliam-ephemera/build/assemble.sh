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
# two-pass at a fixed bitrate so the film stays under the page's 12 MB limit
cd "$C"
ffmpeg -hide_banner -loglevel error -y -framerate 24 -i "$C/seq/%04d.jpg" -c:v libx264 -preset slow -b:v ${VBR:-2100k} \
  -pass 1 -passlogfile "$C/x264pass" -pix_fmt yuv420p -an -f mp4 /dev/null
ffmpeg -hide_banner -loglevel error -y -framerate 24 -i "$C/seq/%04d.jpg" -i "$C/sound.wav" \
  -c:v libx264 -preset slow -b:v ${VBR:-2100k} -pass 2 -passlogfile "$C/x264pass" -pix_fmt yuv420p \
  -c:a aac -b:a 128k -shortest -movflags +faststart "$OUT"
rm -f "$C"/x264pass*
ls -l "$OUT"

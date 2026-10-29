#!/bin/bash
# title (72) + scene (768) + end (72) = 912 frames at 24 fps, with the sound; then the four stills
set -e
B="$(cd "$(dirname "$0")" && pwd)"; R="$(dirname "$B")"; C="$B/cache"
L="$C/list.txt"; : > "$L"
for k in $(seq -f %03g 0 71); do echo "file '$C/cards/t$k.jpg'" >> "$L"; done
for k in $(seq -f %04g 0 767); do echo "file '$C/frames/$k.jpg'" >> "$L"; done
for k in $(seq -f %03g 0 71); do echo "file '$C/cards/e$k.jpg'" >> "$L"; done
ffmpeg -hide_banner -loglevel error -y -r 24 -f concat -safe 0 -i "$L" -i "$C/sound.wav" -map 0:v -map 1:a \
  -c:v libx264 -preset slow -crf 25 -pix_fmt yuv420p -r 24 -c:a aac -b:a 128k -t 38 -movflags +faststart "$R/film.mp4"
mkdir -p "$R/stills"
for s in 03.6 09.0 19.0 28.0; do
  i=$(python3 -c "print('%04d' % round(float('$s')*24))"); cp "$C/frames/$i.jpg" "$R/stills/still_${s}s.jpg"
done
ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames,width,height -show_entries format=duration,size -of compact "$R/film.mp4"

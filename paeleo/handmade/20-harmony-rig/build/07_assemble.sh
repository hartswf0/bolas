#!/bin/sh
# SCION 20 · 07: title (72) + scene (768) + end card (72) = 912 frames -> film.mp4 (H.264 + AAC, faststart), then stills
# taken FROM THE FILM, then the rendered frames are deleted (the disk is shared).
set -e
D=$(cd "$(dirname "$0")/.." && pwd); C="$D/build/cache"; S="$C/seq"
rm -rf "$S"; mkdir -p "$S"
n=0
for f in $(ls "$C"/frames/t*.jpg | sort) $(ls "$C"/frames/s*.jpg | sort) $(ls "$C"/frames/e*.jpg | sort); do
  ln -s "$f" "$S/$(printf %05d $n).jpg"; n=$((n+1))
done
echo "frames in sequence: $n"; [ "$n" -eq 912 ] || { echo "expected 912 frames"; exit 1; }
ffmpeg -y -loglevel error -framerate 24 -i "$S/%05d.jpg" -i "$C/sound.wav" -c:v libx264 -preset slow -crf 21 -maxrate 2300k -bufsize 4600k \
  -pix_fmt yuv420p -c:a aac -b:a 160k -movflags +faststart -shortest "$D/film.mp4"
ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames,codec_name,width,height,r_frame_rate -of compact "$D/film.mp4"
ffprobe -v error -show_entries format=duration,size -of compact "$D/film.mp4"
mkdir -p "$D/stills"
for t in 03.6 09.0 19.0 28.0; do
  ffmpeg -y -loglevel error -ss $(python3 -c "print(3+float('$t')+0.5/24)") -i "$D/film.mp4" -frames:v 1 -q:v 2 "$D/stills/still_${t}s.jpg"
done
rm -rf "$S"

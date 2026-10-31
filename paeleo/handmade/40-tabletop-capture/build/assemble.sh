#!/bin/sh
# encode film.mp4 (912 frames, H.264 + AAC, faststart), cut the stills from the encoded film, delete the frames.
set -e
cd "$(dirname "$0")"
F=..
n=$(ls cache/film/*.jpg | wc -l)
[ "$n" -eq 912 ] || { echo "expected 912 frames, have $n"; exit 1; }
ffmpeg -y -loglevel error -framerate 24 -i cache/film/%04d.jpg -i cache/sound.wav \
  -c:v libx264 -preset slow -crf 23 -pix_fmt yuv420p -tune animation \
  -c:a aac -b:a 128k -shortest -movflags +faststart $F/film.mp4
mkdir -p $F/stills
for t in 03.6 09.0 19.0 28.0; do
  s=$(python3 -c "print(3+float('$t')+0.5/24)")
  ffmpeg -y -loglevel error -ss $s -i $F/film.mp4 -frames:v 1 -q:v 2 $F/stills/still_${t}s.jpg
done
ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 $F/film.mp4
ls -l $F/film.mp4
rm -f cache/film/*.jpg

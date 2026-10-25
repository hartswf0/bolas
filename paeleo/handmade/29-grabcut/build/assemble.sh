#!/bin/sh
# title (72) + scene (768) + end (72) frames + sound -> film.mp4 (1280x720, 24 fps, H.264 + AAC, faststart)
set -e
B=$(cd "$(dirname "$0")" && pwd); C=$B/cache; F=$(dirname "$B")
rm -rf $C/seq; mkdir -p $C/seq
n=0
for f in $(ls $C/cards/t*.jpg | sort); do ln -s $f $C/seq/$(printf '%04d' $n).jpg; n=$((n+1)); done
for f in $(ls $C/frames/s*.jpg | sort); do ln -s $f $C/seq/$(printf '%04d' $n).jpg; n=$((n+1)); done
for f in $(ls $C/cards/e*.jpg | sort); do ln -s $f $C/seq/$(printf '%04d' $n).jpg; n=$((n+1)); done
echo "frames: $n"
ffmpeg -y -loglevel error -framerate 24 -i $C/seq/%04d.jpg -i $C/sound.wav -c:v libx264 -preset slow -crf 25 -pix_fmt yuv420p \
  -c:a aac -b:a 128k -ar 48000 -shortest -movflags +faststart $F/film.mp4
ffprobe -v error -show_entries format=duration,size -of default=nw=1 $F/film.mp4

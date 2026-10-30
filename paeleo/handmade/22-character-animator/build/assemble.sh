#!/bin/sh
# title (72) + scene (768) + end card (72) = 912 frames, 38.0 s; H.264 + AAC, faststart, <= 12 MB
set -e
cd "$(dirname "$0")"
rm -rf cache/seq && mkdir -p cache/seq
i=0
while [ $i -lt 72 ]; do ln -s ../title.jpg cache/seq/$(printf %04d $i).jpg; i=$((i+1)); done
j=0
while [ $j -lt 768 ]; do ln -s ../frames/$(printf %04d $j).jpg cache/seq/$(printf %04d $((j+72))).jpg; j=$((j+1)); done
k=0
while [ $k -lt 72 ]; do ln -s ../endcard.jpg cache/seq/$(printf %04d $((k+840))).jpg; k=$((k+1)); done
ffmpeg -y -loglevel error -framerate 24 -i cache/seq/%04d.jpg -i cache/scene_audio.wav \
  -filter_complex "[1:a]adelay=3000|3000,apad=whole_dur=38,atrim=0:38,afade=t=in:st=2.9:d=0.1,afade=t=out:st=35.0:d=1.5[a]" \
  -map 0:v -map "[a]" -c:v libx264 -preset slow -crf 22 -maxrate 2000k -bufsize 4000k -pix_fmt yuv420p -s 1280x720 \
  -vf "fade=t=in:st=0:d=0.5,fade=t=out:st=37.4:d=0.6" -c:a aac -b:a 128k -t 38 -movflags +faststart ../film.mp4
ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 ../film.mp4
ls -l ../film.mp4

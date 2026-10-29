#!/usr/bin/env bash
# SCION 11 · title (72) + scene (768) + end card (72) = 912 frames, 38.0 s, with the synthesized sound
set -euo pipefail
cd "$(dirname "$0")"
C=cache
n=$(ls $C/frames/*.jpg | wc -l)
[ "$n" -eq 768 ] || { echo "scene frames: $n (want 768)"; exit 1; }
rm -f $C/list.txt
for i in $(seq -w 0 71); do echo "file 'cards/title_$i.jpg'" >> $C/list.txt; echo "duration 0.0416667" >> $C/list.txt; done
for i in $(seq -f %04g 0 767); do echo "file 'frames/$i.jpg'" >> $C/list.txt; echo "duration 0.0416667" >> $C/list.txt; done
for i in $(seq -w 0 71); do echo "file 'cards/end_$i.jpg'" >> $C/list.txt; echo "duration 0.0416667" >> $C/list.txt; done
echo "file 'cards/end_71.jpg'" >> $C/list.txt
ffmpeg -y -loglevel error -f concat -safe 0 -i $C/list.txt -i $C/film.wav \
  -vf "fps=24,format=yuv420p" -frames:v 912 -c:v libx264 -preset slow -crf 23 -tune film \
  -c:a aac -b:a 128k -shortest -movflags +faststart ../film.mp4
ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 ../film.mp4
ls -la ../film.mp4
# stills from the scene (scene frame = t * 24)
for s in 03.6 09.0 19.0 28.0; do
  f=$(python3 -c "print('%04d' % round(float('$s')*24))")
  cp $C/frames/$f.jpg ../stills/still_${s}s.jpg
done

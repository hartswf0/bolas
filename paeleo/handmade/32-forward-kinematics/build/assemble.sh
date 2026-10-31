#!/usr/bin/env bash
# SCION 32 · cards + scene + sound -> ../film.mp4 (38 s, 912 frames), then the four stills from the encoded film
set -euo pipefail
cd "$(dirname "$0")"
C=cache
ffmpeg -y -loglevel error -loop 1 -framerate 24 -i $C/title.png -t 3 -vf "fade=in:0:12,fade=out:60:12,format=yuv420p" -c:v libx264 -crf 14 $C/title.mp4
ffmpeg -y -loglevel error -loop 1 -framerate 24 -i $C/end.png -t 3 -vf "fade=in:0:10,format=yuv420p" -c:v libx264 -crf 14 $C/end.mp4
ffmpeg -y -loglevel error -i $C/title.mp4 -i $C/scene.mp4 -i $C/end.mp4 -i $C/sound.wav \
  -filter_complex "[0:v][1:v][2:v]concat=n=3:v=1:a=0,format=yuv420p[v]" -map "[v]" -map 3:a \
  -c:v libx264 -preset slow -crf ${CRF:-24} -profile:v high -r 24 -c:a aac -b:a 128k -movflags +faststart -shortest ../film.mp4
NF=$(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 ../film.mp4)
NS=$(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 $C/scene.mp4)
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 ../film.mp4)
SIZE=$(stat -c %s ../film.mp4)
echo "film frames $NF (want 912), scene frames $NS (want 768), duration $DUR, bytes $SIZE"
mkdir -p ../stills
for pair in "03.6:158" "09.0:288" "19.0:528" "28.0:744"; do
  name=${pair%%:*}; fr=${pair##*:}
  ffmpeg -y -loglevel error -i ../film.mp4 -vf "select=eq(n\,$fr)" -vsync 0 -frames:v 1 -q:v 2 ../stills/still_${name}s.jpg
done
ls -la ../stills

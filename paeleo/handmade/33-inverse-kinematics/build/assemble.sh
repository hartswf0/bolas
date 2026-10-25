#!/usr/bin/env bash
# SCION 33 · assemble the film from rendered frames, cards and the mix; stills; check
set -euo pipefail
cd "$(dirname "$0")"
OUTDIR=..
n=$(ls cache/frames/*.png | wc -l); [ "$n" -eq 768 ] || { echo "expected 768 scene frames, got $n"; exit 1; }
ffmpeg -y -loglevel error \
  -loop 1 -framerate 24 -t 3 -i cache/title.png \
  -framerate 24 -i cache/frames/%04d.png \
  -loop 1 -framerate 24 -t 3 -i cache/end.png \
  -i cache/film.wav \
  -filter_complex "[0:v]fade=t=out:st=2.5:d=0.5,format=yuv420p[a];[1:v]format=yuv420p[b];[2:v]fade=t=in:st=0:d=0.5,format=yuv420p[c];[a][b][c]concat=n=3:v=1:a=0[v]" \
  -map "[v]" -map 3:a -c:v libx264 -preset slow -crf 23 -pix_fmt yuv420p -r 24 -c:a aac -b:a 128k -movflags +faststart -t 38 $OUTDIR/film.mp4
for s in 03.6 09.0 19.0 28.0; do
  i=$(python3 -c "print('%04d' % round(float('$s')*24))")
  python3 -c "from PIL import Image; Image.open('cache/frames/$i.png').convert('RGB').save('$OUTDIR/stills/still_${s}s.jpg', quality=90)"
done
ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames,width,height -show_entries format=duration,size -of compact $OUTDIR/film.mp4
python3 ../../../../tools/paeleo/check_handmade.py ..

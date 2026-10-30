#!/usr/bin/env bash
# Assemble film.mp4 from rendered frames + cards + sound; trace, assets, stills, invariant check.
set -euo pipefail
cd "$(dirname "$0")"
python3 trace.py                 # ../trace.json (measured onsets)
python3 assets.py                # ../assets.json (registry + rights manifest)
n=$(ls cache/frames/f_*.jpg | wc -l); [ "$n" -eq 768 ] || { echo "expected 768 scene frames, got $n"; exit 1; }
ffmpeg -hide_banner -loglevel error -y \
  -framerate 24 -i cache/cards/title_%04d.jpg -framerate 24 -i cache/frames/f_%04d.jpg -framerate 24 -i cache/cards/end_%04d.jpg \
  -i cache/sound.wav \
  -filter_complex "[0:v][1:v][2:v]concat=n=3:v=1:a=0,format=yuv420p[v]" -map "[v]" -map 3:a \
  -c:v libx264 -preset slow -crf 21 -profile:v high -r 24 -c:a aac -b:a 160k -ar 48000 -movflags +faststart -shortest ../film.mp4
nf=$(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 ../film.mp4)
echo "film frames: $nf (expect 912)"; [ "$nf" -eq 912 ] || exit 1
# stills from the FINAL film (scene t + 3 s title): 3.6 s, 9 s, 19 s, 28 s
mkdir -p ../stills
for s in 03.6 09.0 19.0 28.0; do
  f=$(python3 -c "print(72 + round(float('$s') * 24))")
  ffmpeg -hide_banner -loglevel error -y -i ../film.mp4 -vf "select=eq(n\,$f)" -frames:v 1 -q:v 2 "../stills/still_${s}s.jpg"
done
python3 ../../../../tools/paeleo/check_handmade.py ..

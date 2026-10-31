#!/bin/bash
# SCION-36 · Bounded Biharmonic Weights — rebuild PAE-02 from the kit and the score.
# needs: python3 numpy Pillow, plus   pip install scipy scikit-image   (installed for this build: scipy 1.18.1, scikit-image 0.26.0)
set -e
cd "$(dirname "$0")"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
python3 -c "import scipy, skimage" 2>/dev/null || pip install scipy scikit-image
mkdir -p cache
python3 rigs.py                 # auto triangulation, auto handles, BBW solve, tests -> ../proof/tests.json, heat maps
./render_all.sh                 # 768 scene frames (JPEG in cache/frames), measurements in cache/meas_*.json
python3 trace.py                # ../trace.json with the measured onsets
python3 sound.py cache/sound.wav
python3 cards.py
n=$(ls cache/frames/s*.jpg | wc -l); [ "$n" = 768 ] || { echo "scene frames: $n (need 768)"; exit 1; }
ffmpeg -loglevel error -y \
  -loop 1 -framerate 24 -t 3 -i cache/title.png \
  -framerate 24 -i cache/frames/s%04d.jpg \
  -loop 1 -framerate 24 -t 3 -i cache/endcard.png \
  -i cache/sound.wav \
  -filter_complex "[0:v]format=yuv420p,setsar=1,fade=in:0:12[a];[1:v]format=yuv420p,setsar=1[b];[2:v]format=yuv420p,setsar=1,fade=out:60:12[c];[a][b][c]concat=n=3:v=1:a=0[v]" \
  -map "[v]" -map 3:a -c:v libx264 -preset slow -crf 25 -maxrate 2200k -bufsize 4400k -pix_fmt yuv420p -r 24 \
  -c:a aac -b:a 128k -t 38 -movflags +faststart ../film.mp4
python3 stills.py
nf=$(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 ../film.mp4)
echo "film frames: $nf (need 912)"; ls -l ../film.mp4
rm -rf cache/frames             # keep the folder lean: the frames are regenerable
python3 ../../../../tools/paeleo/check_handmade.py ..

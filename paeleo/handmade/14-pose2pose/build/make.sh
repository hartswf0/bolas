#!/bin/sh
# Rebuild SCION 14 (Pose2Pose casting) from the score: bank -> poses -> clusters -> path -> picture -> sound -> film -> trace.
set -e
H="$(cd "$(dirname "$0")" && pwd)"; F="$H/.."
mkdir -p "$H/cache" "$F/proof" "$F/stills"
python3 "$H/bank.py"                      # ILLUSTRATOR: the illustration bank
node "$H/atlas.js" "$F/bank/bank.json" "$F/proof/pose_atlas.png" 9 1   # the pose atlas sheet
python3 "$H/poses.py"                     # POSE EXTRACTOR + action edits
python3 "$H/cues.py"                      # spoken lines
python3 "$H/solve.py" > "$H/cache/solve.log"   # SEQUENCE OPTIMIZER: Viterbi path + placement
python3 "$H/curate.py" > "$H/cache/curate.log" # CURATOR: clusters vs bank
node "$H/render.js" film                  # picture + per-frame measurement of the dog
python3 "$H/sound.py" > "$H/cache/sound.log"   # sound from the path
ffmpeg -y -loglevel error -i "$H/cache/picture.mp4" -i "$H/cache/sound.wav" -c:v copy -c:a aac -b:a 160k -ar 48000 -shortest -movflags +faststart "$F/film.mp4"
python3 "$H/finish.py" > "$H/cache/finish.log" # trace, onsets, proofs
python3 "$H/assets.py" > /dev/null
for s in 3.6 9.0 19.0 28.0; do
  n=$(python3 -c "print(72+round($s*24))")
  ffmpeg -y -loglevel error -i "$F/film.mp4" -vf "select=eq(n\,$n)" -frames:v 1 -q:v 2 "$F/stills/still_$(printf '%04.1f' $s)s.jpg"
done
ffprobe -v error -count_frames -show_entries stream=codec_name,nb_read_frames:format=duration,size -of compact "$F/film.mp4"

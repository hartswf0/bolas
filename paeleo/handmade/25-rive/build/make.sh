#!/bin/sh
# SCION-25 RIVE: rebuild the film from the puppet, the runtime and the score.  sh paeleo/handmade/25-rive/build/make.sh
set -e
B=$(cd "$(dirname "$0")" && pwd); F=$(dirname "$B"); C="$B/cache/film"
mkdir -p "$C" "$F/stills" "$F/proof"
node "$B/test_events.js"                               # event tester: state machine headless, planted-foot slide
node "$B/render.js" "$C"                                # 912 frames -> picture.mp4, render-trace.json (measured trace + event log)
python3 "$B/sound.py" "$C/render-trace.json" "$C/sound.wav" "$C/levels.json"
ffmpeg -y -loglevel error -i "$C/picture.mp4" -i "$C/sound.wav" -c:v copy -c:a aac -b:a 160k -movflags +faststart "$F/film.mp4"
python3 "$B/finalize.py"                                # trace.json, events.jsonl, proof/acceptance.json
python3 "$B/graph.py"                                   # proof/state-graph.svg from puppet.json
for t in 03.6 09.0 19.0 28.0; do
  n=$(python3 -c "print(72 + round(float('$t') * 24))")
  ffmpeg -y -loglevel error -i "$F/film.mp4" -vf "select=eq(n\,$n)" -frames:v 1 -q:v 2 "$F/stills/still_${t}s.jpg"
done
node "$B/test_page.js" || true                          # mobile acceptance of the operator page
python3 "$(dirname "$(dirname "$(dirname "$F")")")/tools/paeleo/check_handmade.py" "$F"
ffprobe -v error -count_frames -show_entries stream=nb_read_frames:format=duration,size -of compact "$F/film.mp4"

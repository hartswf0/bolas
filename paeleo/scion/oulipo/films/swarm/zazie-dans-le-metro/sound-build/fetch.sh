#!/bin/bash
# downloads queue entries into raw/, waiting out 429s
D=/home/user/bolas/paeleo/scion/oulipo/films/sources/zazie-dans-le-metro/sound/raw
Q=/home/user/bolas/paeleo/scion/oulipo/films/swarm/zazie-dans-le-metro/sound-build/fetch-queue.txt
end=$((SECONDS+2400)); 
while [ $SECONDS -lt $end ]; do
  pending=0
  while read -r u; do
    [ -z "$u" ] && continue
    f=$(basename "$u" | python3 -I -c "import sys,urllib.parse;print(urllib.parse.unquote(sys.stdin.read().strip()))")
    [ -s "$D/$f" ] && continue
    code=$(curl -sS -A "oulipo-film-research/1.0" -o "$D/.tmp" -w "%{http_code}" "$u")
    if [ "$code" = "200" ]; then mv "$D/.tmp" "$D/$f"; echo "$(date +%T) OK $f"; sleep 4; else echo "$(date +%T) $code $f"; rm -f "$D/.tmp"; pending=1; break; fi
  done < "$Q"
  if [ $pending = 0 ]; then n=$(grep -c . "$Q"); h=$(ls "$D" | wc -l); [ "$h" -ge "$n" ] && { echo done; exit 0; }; fi
  sleep 300
done

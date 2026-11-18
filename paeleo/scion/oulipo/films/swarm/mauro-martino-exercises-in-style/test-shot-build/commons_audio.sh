#!/bin/bash
# One Commons search for a street/traffic field recording, with backoff on 429.
OUT=/home/user/bolas/paeleo/scion/oulipo/films/sources/mauro-martino-exercises-in-style/test-shot
until grep -q done /tmp/claude-0/-home-user/a99ec93a-6f31-57b0-a2ec-fb930dfe1aad/tasks/bfrqt0zfo.output 2>/dev/null; do sleep 5; done
for i in 1 2 3 4 5 6 7 8 9 10; do
  c=$(curl -sS -A "oulipo-film-research/1.0" -G "https://commons.wikimedia.org/w/api.php" -d action=query -d generator=search -d gsrnamespace=6 \
     --data-urlencode "gsrsearch=traffic street filemime:audio/ogg" -d gsrlimit=30 -d prop=imageinfo -d "iiprop=url|size|extmetadata" \
     -d "iiextmetadatafilter=LicenseShortName|Artist|ImageDescription" -d format=json -o $OUT/audio-street.json -w "%{http_code}")
  [ "$c" = 200 ] && { echo ok; break; }
  sleep $((15*i))
done

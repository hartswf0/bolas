#!/bin/sh
# SCION 31 Alpha Matting: rebuild the threshold film from the kit, the copied sources and the score.
set -e
cd "$(dirname "$0")"
python3 prep_dog.py          # 50 archive dog frames -> trimaps -> solved mattes (cache/dog)
python3 prep_world.py        # woman, hand, door leaf + curtain, 62 cloud frames (cache/)
python3 proof_dog.py 9 22 45 # matte diagnostics -> proof/
python3 proof_world.py
python3 fork_fur.py          # the A/B/C fur-matte fork, kept as a regression view
python3 stress.py            # stress composite (light / dark / moving) + edge log + RGBA variants -> proof/
python3 cards.py
rm -f cache/trace_part_*.json
python3 render.py --frames 0:256 & P1=$!
python3 render.py --frames 256:512 & P2=$!
python3 render.py --frames 512:768 & P3=$!
wait $P1 $P2 $P3
python3 assemble.py          # trace.json, stills, sound (sound.py), film.mp4
ls cache/frames | wc -l
python3 ../../../../tools/paeleo/check_handmade.py ..
python3 verify.py > /dev/null   # round 3: the repair conditions measured on the encoded film -> ../proof/round3_verify.json, r3_*.jpg
rm -rf cache/frames cache/trace_part_*.json cache/seq.txt   # rendered frames are not kept (shared disk)

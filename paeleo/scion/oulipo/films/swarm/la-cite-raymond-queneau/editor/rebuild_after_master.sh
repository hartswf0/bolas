#!/bin/bash
# Re-run every step that depends on the picture master after a new master revision (plan §4.1).
set -euo pipefail
SW=/home/user/bolas/paeleo/scion/oulipo/films/swarm/la-cite-raymond-queneau
PROJ=/home/user/bolas/paeleo/scion/oulipo
cd "$SW/picture"
python3 make_edl.py                 # edl.json names the new revision; event frames unchanged
python3 determinism.py              # 10 random frames re-rendered, sha1 equal
python3 aesthetic.py                # model-render numeric test (picture/aesthetic-check.json)
rm -f "$PROJ/films/sources/la-cite-raymond-queneau/editor/master.rgb24"
ffmpeg -v error -y -i "$SW/out/master.mp4" -f rawvideo -pix_fmt rgb24 "$PROJ/films/sources/la-cite-raymond-queneau/editor/master.rgb24"
cd "$SW"
python3 -I editor/cuemap.py         # step 1 against the new revision
python3 -I editor/mix.py            # step 2 (audio unchanged; re-measured)
python3 -I editor/editions.py       # steps 3-4
python3 -I editor/aesthetic_check.py  # step 7 on the decoded master
cd "$PROJ"
python3 films/la-cite-raymond-queneau.py              # step 5 reel (A first)
python3 films/la-cite-raymond-queneau.py --order BA   # counterbalanced reel
rm -f "$SW/out/reel-BA.webp"
python3 films/la-cite-raymond-queneau.py --verify     # decoded PSNR + pass loudness into identity-report.json
cd "$SW" && python3 -I editor/credits.py

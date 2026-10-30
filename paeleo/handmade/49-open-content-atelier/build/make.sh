#!/usr/bin/env bash
# PAE-02 · SCION 49 · Open-Content Atelier — rebuild the film from the CC0 sources and the score.
# Sources: sources/media/*.jpg (reduced copies of Smithsonian Open Access images) + sources/meta/*.jsonl (their EDAN records).
# To refetch them from the Smithsonian Open Access S3 distribution (network): see fetch_meta.py / fetch_grep.py / fetch_media.py.
set -euo pipefail
cd "$(dirname "$0")"
python3 parts.py                 # semantic cropper: cut every part (polygon + key) -> cache/parts
python3 render.py                # 768 scene frames -> cache/frames, measurements -> cache/measure.json
python3 sound.py                 # cache/sound.wav, ../sound.json
python3 cards.py                 # title + end cards -> cache/cards
bash assemble.sh
# keep the folder lean: rendered frames are regenerable
rm -rf cache/frames cache/cards

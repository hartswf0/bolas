#!/usr/bin/env python3
"""Hear what a clip actually says: word timings by Whisper (run with ~/.cache/mlxw-venv/bin/python). usage: hear.py <film> <n> ..."""
import json, os, sys
import mlx_whisper
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); film = sys.argv[1]
db = json.load(open(os.path.join(ROOT, "films", film, "forage.json"))); byn = {str(c["n"]): c for c in db["clips"].values()}
for n in sys.argv[2:]:
    c = byn[n]; p = os.path.join(ROOT, "clips", c["id"] + ".mp4")
    try: r = mlx_whisper.transcribe(p, path_or_hf_repo="mlx-community/whisper-large-v3-turbo", word_timestamps=True, language="en", condition_on_previous_text=False, verbose=None)
    except Exception: print(f"#{n} {c.get('sourceTitle')}: (SILENT, no audio track)", flush=True); continue
    print(f"#{n} {c.get('sourceTitle')}:", " ".join(f"{w['word'].strip()}@{w['start']:.1f}" for s in r["segments"] for w in s.get("words", [])) or "(no words)", flush=True)

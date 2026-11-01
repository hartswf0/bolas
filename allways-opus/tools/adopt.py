#!/usr/bin/env python3
"""Bring clips the lab already knows (found through its transcripts) into a film's forage, by id prefix. usage: adopt.py <film> <prefix> ..."""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); LAB = os.environ.get("CINEOSIS_LAB", os.path.expanduser("~/cineosis-lab/lab"))
film = sys.argv[1]; fp = os.path.join(ROOT, "films", film, "forage.json"); db = json.load(open(fp)) if os.path.exists(fp) else {"queries": {}, "clips": {}}
C = json.load(open(LAB + "/cache/corpus.json")); W = json.load(open(LAB + "/words.json")); O = json.load(open(LAB + "/odyssey/transcripts.json"))
for pre in sys.argv[2:]:
    k = [i for i in C if i.startswith(pre)][0]; c = dict(C[k]); c["durationSeconds"] = c["endSeconds"] - c["startSeconds"]
    x = db["clips"].setdefault(k, c); x.setdefault("n", len(db["clips"]))
    ws = W.get(k) or (O.get(k) or {}).get("words") or []
    print("#%d" % x["n"], k[:8], c["sourceTitle"], c.get("sourceYear"), "|", " ".join(f"{t}@{s:.1f}" if i % 6 == 0 else t for i, (t, s) in enumerate(ws))[:900])
json.dump(db, open(fp, "w"), indent=0)

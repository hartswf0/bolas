import json, hashlib
from pathlib import Path
R = Path("/home/user/bolas/paeleo/scion/oulipo")
p = R / "films/swarm/99-ways-template/baseline-b1/manifest.json"
m = json.load(open(p))
m["files"]["plates_r1"] = {"path": "films/sources/99-ways-template/editor/office.plate.r1.png", "sha256_16": None}
m["files"]["plates_r1_record"] = {"path": "films/sources/99-ways-template/editor/plate_repair.json", "sha256_16": None}
m["files"]["timeline"] = {"path": "films/swarm/99-ways-template/anim/timeline.py", "sha256_16": None}
for k, v in m["files"].items():
    f = R / v["path"]
    if f.is_file():
        v["sha256_16"] = hashlib.sha256(f.read_bytes()).hexdigest()[:16]
m["revision"] = "b1-r1"
m["revision_note"] = "editor repair round 1: staging of P2/P3/P4/P5/P8 and D2 changed, E5 line in the production's own words; event graph and speakers unchanged"
json.dump(m, open(p, "w"), indent=1)
print("ok")

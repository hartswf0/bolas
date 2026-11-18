"""records + credits for pages 56-59 (batch 6, page maker 1). Run: python3 -I rec56_59.py NN"""
import json, sys, os
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
from b1m2 import write_record, credit_pages, PAGES_OUT, BEATS
from PIL import Image
ROOT = "/home/user/bolas/paeleo/scion/oulipo/"
canon = json.load(open(ROOT + "films/swarm/99-ways/canon.json"))
LINES = {"question": "Pardon me — have you the right time?", "answer": "Ten past four, by the clock.",
         "thanks": "Much obliged!", "forgetting": "Well, here I am... and what for?"}


def make(n, pid, title, medium, family, declares, build, sources, made, events, subs, beat, beat_frames, checks, new=()):
    jp = PAGES_OUT / f"{n:02d}-{pid}.jpg"
    im = Image.open(jp)
    bd = BEATS / f"{n:02d}"
    frames = sorted(bd.glob("b*.png"))
    rule = None
    for p in canon["constraints"]:
        if p.get("n") == n or p.get("nn") == n:
            rule = p.get("rule")
    rec = {"n": n, "id": pid, "title": title, "rule": rule, "medium": medium, "family": family, "canon_revision": "c1",
           "declares": declares, "file": f"assets/pages/99-ways/{n:02d}-{pid}.jpg",
           "master": f"films/sources/99-ways/masters/{n:02d}-{pid}.png", "beats_dir": f"films/sources/99-ways/beats/{n:02d}",
           "build": build, "sources": sources, "lines": LINES, "made": made, "events": events, "substitutions": subs,
           "beat": beat, "beat_frames": beat_frames,
           "self_check": dict({"size_px": list(im.size), "jpeg_bytes": os.path.getsize(jp), "jpeg_quality": 90,
                               "in_target_0.4_1.2MB": 400000 <= os.path.getsize(jp) <= 1200000,
                               "beat_frames": len(frames), "beat_size": list(Image.open(frames[0]).size)},
                              **checks, pending="independent blind reading not run by the maker")}
    write_record(rec)
    credit_pages(sources, n, new)
    print(json.dumps(rec["self_check"]))

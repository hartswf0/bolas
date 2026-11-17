import sys
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
from b1m2 import *
jp = PAGES_OUT / "06-turntable.jpg"
im = Image.open(jp)
src = ["99-ways-template:anrc-gold-key-1922", "99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"]
credit_pages(src, 6)
rec = {
 "n": 6, "id": "turntable", "title": "Turntable", "family": "medium and material", "medium": "spiral-disc", "canon_revision": "c1",
 "rule": "The beats are printed round a slotted disc that, spun, animates the walk; the page shows the disc and its reading slots.",
 "declares": "keeps E0-E5, the four lines and the outcome",
 "file": "assets/pages/99-ways/06-turntable.jpg", "master": "films/sources/99-ways/masters/06-turntable.png",
 "beats_dir": "films/sources/99-ways/beats/06",
 "build": "films/swarm/99-ways/build/p06_turntable.py (figure model: build/b1m2.py)",
 "sources": src,
 "made": [
  "HANDMADE slotted picture disc (phenakistiscope type) on card with the fibre of the LoC 1934 sheet: six sectors, one per event E0-E5, numbered 1-6 in red at the rim; six reading slots cut at the sector boundaries; a pin through the hub",
  "each sector a flat upright print of the b1m2 cut-paper figures in ink, the agent standing at the same place in every sector (so that spun he stays put and walks) while desk, ticket window with the stranger, clock and open cupboard pass behind him; the brass key (ANRC 1922 cutout) as a brass spot colour with a red SERVICE tag",
  "the beats and the four lines lettered along the arcs in the shared pen hand (polar-warped pen masks); an inked spiral at the hub (brush_line)",
  "reading directions and a side-view diagram (eye, slot, disc edge-on, mirror) in the pen hand; a red turning arrow"
 ],
 "events": {"E0": "sector 1: memo text, he sets off past the desk", "E1": "sector 2: the stranger in the ticket window, question",
            "E2": "sector 3: the clock at 4:10, answer", "E3": "sector 4: she turns away, thanks",
            "E4": "sector 5: cupboard open, brass key on its hook, SERVICE tag", "E5": "sector 6: pencil to chin, forgetting line; the key stays, the door stays shut"},
 "lines": {"question": "Pardon me — have you the right time?", "answer": "Ten past four, by the clock.",
           "thanks": "Much obliged!", "forgetting": "Well, here I am... and what for?"},
 "beat": "the disc turns one sector per frame and each sector arrives at the lit reading slot in turn: the agent walks through E0-E5 while the office passes behind him",
 "beat_frames": [f"b0{k+1}: sector {k+1} at the slot, rest of the disc in the dark" for k in range(6)],
 "self_check": {
  "size_px": list(im.size), "jpeg_bytes": jp.stat().st_size, "jpeg_quality": 90,
  "in_target_0.4_1.2MB": 400000 <= jp.stat().st_size <= 1200000,
  "check": "A reader finds the beats in order round the disc: red numerals 1-6 clockwise at the rim, E0-E5 in the same order (perceptually judged by the maker from the full-size page and the slot-view frames; blind reading pending)",
  "sectors": 6, "slots": 6, "rim_text_cap_px": 44,
  "evidence": "structurally verified (sector order) and perceptually judged (from frames) by the maker"
 },
 "weaknesses": ["text in the lower sectors reads upside down on the flat page, as on any picture disc", "the walk is a coarse six-phase cycle, not a smooth gait"]
}
write_record(rec)
print(rec["self_check"]["jpeg_bytes"])

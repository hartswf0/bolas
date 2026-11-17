import sys
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
from p07_two_panels import plate_hash, panel1, panel2, CHECK, PLATE_LAID, brush_check
PLATE_LAID.clear()
_p1 = panel1()
_p2 = panel2()
BC = brush_check()
from b1m2 import *
jp = PAGES_OUT / "07-two-panels.jpg"
im = Image.open(jp)
src = ["99-ways-template:anrc-gold-key-1922", "99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"]
credit_pages(src, 7)
rec = {
 "n": 7, "id": "two-panels", "title": "Two panels", "family": "reduction and expansion", "medium": "brush-plate", "canon_revision": "c1",
 "rule": "The incident in two panels only: before the question, and at the cupboard.",
 "declares": "E1-E3 and E4 compressed into two panels",
 "declared_compression": "P1 holds E0 and E1 (the memo on the desk, the agent set off for the cupboard, the stranger at the window putting her question). P2 holds E4-E5 and carries E2-E3 as balloons in reading order: the answer (tail to the agent, clock at 4:10 on the wall), the thanks from the emptied window, then the forgetting line.",
 "file": "assets/pages/99-ways/07-two-panels.jpg", "master": "films/sources/99-ways/masters/07-two-panels.png",
 "beats_dir": "films/sources/99-ways/beats/07",
 "build": "films/swarm/99-ways/build/p07_two_panels.py (brush: build/brushkit.py; figures: build/b1m2.py)",
 "sources": src,
 "made": [
  "ONE HANDMADE brush plate of the office (window with TICKET OFFICE, clock at 4:10, desk and lamp, closed cupboard, SERVICE door with its card, black wainscot and floor), drawn once with the dab-chain brush method of moins-dun-quart-de-seconde-pour-vivre (copied into build/brushkit.py), re-inked with a strong pressure swing (dab width 0.5x-1.5x along each contour, tapered lifts) so every contour swells and thins like a loaded brush, and printed identically in both panels; plate ink sha256 " + plate_hash(),
  "figures: the b1m2 cut-paper figure model redrawn with the brush (white shirt and face, black waistcoat, trousers and hair, spectacles, pencil); the stranger with her cloche hat behind the window in P1 only",
  "P2 overlay pasted over the plate: the cupboard opened (lit inside, shelves, leaf swung on the left jamb) and the ANRC 1922 key printed in ink on its hook with a paper SERVICE tag, in the right half of the open cupboard at his eye line",
  "P2 agent re-posed (b1m2 FK: sh 5, el 140, wr 40, pencil 175 deg, head tilt 6): standing in the open doorway between the swung leaf and the cupboard interior, clear of the leaf, facing right at the key, pencil up to his chin",
  "P2 balloon tails routed by explicit curves: the answer tail arcs over the thanks balloon and comes down in front of his face to his mouth; the thanks tail runs into the emptied window; the forgetting tail comes from the balloon above-right, over the key, to his mouth",
  "the memo slip on the desk and the balloons: brushed contours, the four canon lines in the shared pen hand; folio by pen99.folio"
 ],
 "events": {"E0": "P1: memo slip on the desk ('4:15 - open SERVICE door. Key in cupboard.'), the agent walking toward the cupboard",
            "E1": "P1: the stranger at the ticket window, question balloon tailed to her",
            "E2": "P2: answer balloon (first, top left) tailed to the agent's mouth; the clock reads 4:10",
            "E3": "P2: thanks balloon (second, top centre) tailed into the emptied window",
            "E4": "P2: cupboard open, key on its hook with its SERVICE tag",
            "E5": "P2: facing the key, pencil to his chin, forgetting balloon (third, above right) tailed to his mouth; the key stays, the SERVICE door is closed"},
 "lines": {"question": "Pardon me — have you the right time?", "answer": "Ten past four, by the clock.",
           "thanks": "Much obliged!", "forgetting": "Well, here I am... and what for?"},
 "beat": "on the unchanged plate of panel 2 the cupboard overlay is laid open, then the three balloons are laid in reading order: answer, thanks, forgetting",
 "beat_frames": ["b01: P2 plate with the agent, cupboard closed, no balloons", "b02: cupboard opened (overlay), key on its hook",
                 "b03: + answer balloon", "b04: + thanks balloon", "b05: + forgetting balloon (the finished page)"],
 "self_check": {
  "size_px": list(im.size), "jpeg_bytes": jp.stat().st_size, "jpeg_quality": 90,
  "in_target_0.4_1.2MB": 400000 <= jp.stat().st_size <= 1200000,
  "panels": 2, "plate_identical_in_both_panels": len(set(PLATE_LAID)) == 1 and len(PLATE_LAID) == 2,
  "plate_sha256_as_laid_P1_P2": PLATE_LAID, "balloon_cap_px": 52,
  "brush_thick_thin": BC, "brush_min_ratio": min(v["ratio"] for v in BC.values()),
  "p2_geometry": CHECK,
  "check": "A reader counts two panels and still retells E0-E5 (maker's judgement from the full-size page; the reading order of the three P2 balloons is the riskiest point; blind reading pending)",
  "evidence": "measured (panel count, plate hash) and perceptually judged (from frames) by the maker"
 },
 "weaknesses": ["P2's answer balloon is spoken at the window in the story but tailed to the agent standing at the cupboard: a deliberate compression that a reader may find odd",
                "two tails (answer from above, forgetting from the right) converge on his mouth; they never touch, but the answer tail is long",
                "the stranger's face is a plain white mass under a black hat"]
}
write_record(rec)
print(rec["self_check"]["jpeg_bytes"])

import sys
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import p27_out_of_order as P
from b1m2 import *
P.build()
ov, bbox = P.overlaps()
jp = PAGES_OUT / "27-out-of-order.jpg"
im = Image.open(jp)
src = ["99-ways-template:rothstein-randolph-agent-1937", "99-ways-template:rothstein-tavern-clock-1937",
       "99-ways-template:anrc-gold-key-1922", "99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"]
credit_pages(src, 27)
pos = {k: [int(v[0][0]), int(v[0][1])] for k, v in P.LAY.items()}
rec = {
 "n": 27, "id": "out-of-order", "title": "Out of order", "family": "reader and object", "medium": "photo-cutout",
 "canon_revision": "c1",
 "rule": "Panels are scattered across the page; small numbers give the reading order.",
 "declares": "keeps E0-E5, the four lines and the outcome",
 "file": "assets/pages/99-ways/27-out-of-order.jpg", "master": "films/sources/99-ways/masters/27-out-of-order.png",
 "beats_dir": "films/sources/99-ways/beats/27",
 "build": "films/swarm/99-ways/build/p27_out_of_order.py (panels: kit/build_page01.py panel_rest + balloon_on)",
 "sources": src,
 "made": [
  "the eight page-01 photo panels recomposed from films/swarm/99-ways-template/page/rest/P1..P8 (FORAGED Rothstein 1937 agent and clock, ANRC 1922 key; HANDMADE memo, SERVICE cards, hook, tag), the c1 balloons re-lettered 12% larger in the shared pen hand",
  "each panel cut out as a separate print: 22 px white paper margin, hand-ruled photo edge (penlib.border_mask), scissor-cut slightly irregular outline, its own drop shadow; scale 0.74 of page 01's 2550 layout, each turned -5..+6 degrees",
  "the prints scattered on the LoC 1934 sheet in three loose rows, positions deliberately scrambled against the reading order (top row reads 3 6 1, middle 5 2 4, bottom 8 7); dropped in position order so overlaps say nothing about order (no print hides another: hidden fraction 0 for all)",
  "eight HANDMADE round tag cards (yellowed card, pen ring, the numeral in the shared pen hand at 50 px cap) pinned on each print's upper-left corner: the only reading-order cue",
  "folio by pen99.folio"
 ],
 "layout_centres_px": pos,
 "events": {"E0": "tag 1 memo on the desk; tag 2 desk left (he has risen); tag 3 walking past the SERVICE card",
            "E1": "tag 4 question, tail out through the ticket window", "E2": "tag 5 answer under the clock at 4:10",
            "E3": "tag 6 thanks from the emptied window", "E4": "tag 7 cupboard open, key on its hook",
            "E5": "tag 8 the forgetting line, key unmoved, SERVICE card on the closed door"},
 "lines": {"question": "Pardon me — have you the right time?", "answer": "Ten past four, by the clock.",
           "thanks": "Much obliged!", "forgetting": "Well, here I am... and what for?"},
 "beat": "the scattered prints lie unnumbered (no order can be read); then the tags are pinned two at a time, 1-2, 3-4, 5-6, 7-8, so the reading path jumps across the page and the order appears",
 "beat_frames": ["b01: eight prints scattered, no tags", "b02: tags 1-2", "b03: tags 1-4", "b04: tags 1-6", "b05: tags 1-8 (the finished page)"],
 "self_check": {
  "size_px": list(im.size), "jpeg_bytes": jp.stat().st_size, "jpeg_quality": 90,
  "in_target_0.4_1.2MB": 400000 <= jp.stat().st_size <= 1200000,
  "panels": 8, "numbered_tags": 8, "tag_cap_px": 50, "balloon_cap_px_on_page": "35-50",
  "reading_order_vs_position": "position order (row-major) 3,6,1,5,2,4,8,7: the only consecutive pair that sits side by side is 7/8, and it lies reversed (8 left of 7)",
  "print_hidden_fraction": ov, "ink_bbox_px": bbox, "live_area_ok": bbox[0] >= 110 and bbox[1] >= 110 and bbox[2] <= 2090 and bbox[3] <= 2730,
  "check": "A reader follows the numbers and retells E0-E5 in order (maker's judgement from the full-size page: tags legible at phone width; following 1-8 gives memo, risen, walk, question, answer, thanks, open cupboard, forgetting; blind reading pending)",
  "evidence": "measured (tag count, overlap, bbox) and perceptually judged (full-size page) by the maker"
 },
 "weaknesses": ["the scatter is three loose rows rather than a free pile, so it reads more as a jumbled grid than a spilled heap",
                "the stranger is never seen (as on page 01, her lines come through the window from off-panel)",
                "tags 1 and 2 show near-identical desk shots; without the numbers the order of those two would be guesswork (which is the point, but the rising itself is only implied by the empty chair)"]
}
write_record(rec)
print(rec["self_check"]["jpeg_bytes"], rec["self_check"]["live_area_ok"])

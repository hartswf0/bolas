import os, sys
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
from b1m2 import write_record, credit_pages, PAGES_OUT
import p71_panel_palindrome as p
src = ["99-ways-template:anrc-gold-key-1922", "99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"]
jp = PAGES_OUT / "71-panel-palindrome.jpg"
rec = {"n": 71, "id": "panel-palindrome", "title": "Panel palindrome", "family": "formal / Oulipian rule",
 "medium": "shadow-puppet", "canon_revision": "c1",
 "rule": "Compositions mirror about the middle: panel k and panel 9-k share their layout, so the page folded across its middle matches itself.",
 "declares": "keeps E0-E5, the four lines and the outcome",
 "file": "assets/pages/99-ways/71-panel-palindrome.jpg", "master": "films/sources/99-ways/masters/71-panel-palindrome.png",
 "beats_dir": "films/sources/99-ways/beats/71",
 "build": "films/swarm/99-ways/build/p71_panel_palindrome.py (figure model and set pieces: build/b1m2.py; screen: build/p05_noir.py)",
 "sources": src,
 "made": [
  "eight HANDMADE shadow-theatre strips in one column, heights 355/292/292/280 | 280/292/292/355, symmetric about the fold line y=1420 (gutter centre); a dashed pen fold line with 'fold' lettered and margin ticks",
  "four sets cut once and laid twice at the same x: P1/P8 office master (desk, lamp, clock, cupboard, SERVICE door), P2/P7 cupboard wall (desk end, cupboard, SERVICE door), P3/P6 ticket window close (window, agent bust at right), P4/P5 small window, clock, closed cupboard far right",
  "text and corner numerals mirrored too: P1-P4 carry their slip/balloon and numeral in the top half of the strip, P5-P8 in the bottom half at the same x, so folded, words land on words",
  "black cut-paper puppets (b1m2 agent and stranger bust), the stranger held soft and grey behind the glass (p05 far()), lit paper screens with the LoC 1934 sheet fibre",
  "the ANRC 1922 key cutout as an amber gel on its hook with a SERVICE tag (P7, P8)",
  "lettering in the shared pen hand (slips, penlib cut-paper balloons, TICKET OFFICE cut through the header board); folio by pen99.folio"],
 "pairs": {"P1/P8": "office master: E0 seated at the memo / E5 standing at the open cupboard, forgetting",
           "P2/P7": "cupboard wall: E0 he sets off (cupboard shut) / E4 he opens it, key on its hook",
           "P3/P6": "window close: E1 the question / E3 after: the window empty, he turns back to the errand",
           "P4/P5": "window-clock: E2 he looks up at 4:10, the answer / E3 the thanks as she turns from the glass"},
 "events": {"E0": "P1 memo slip '4:15 - open SERVICE door. Key in cupboard.' at the desk; P2 he sets off", "E1": "P3 question from the window",
  "E2": "P4 he looks up at the clock (4:10), answer", "E3": "P5 thanks; P6 the window empty", "E4": "P7 the cupboard opened, key on its hook, tag SERVICE",
  "E5": "P8 pencil to the chin, the forgetting line; key on its hook; SERVICE door shut with its card"},
 "lines": {"question": "Pardon me — have you the right time?", "answer": "Ten past four, by the clock.", "thanks": "Much obliged!", "forgetting": "Well, here I am... and what for?"},
 "beat": "the page folds across its middle: the lower half lifts about the fold line, passes upright, and lies over the upper half, backlit, so each strip's set, figure and words show through onto its partner; then the page lies flat again",
 "beat_frames": ["b01: the flat page", "b02: lower half lifted 50 deg", "b03: lower half near upright (88 deg)", "b04: 130 deg, its back seen, pictures showing through",
                 "b05: folded flat (180 deg), backlit: frames coincide, window over window, cupboard over cupboard, balloon over balloon", "b06: unfolded, the flat page"],
 "self_check": {"size_px": [2200, 2850], "jpeg_bytes": os.path.getsize(jp), "jpeg_quality": 90, "in_target_0.4_1.2MB": 400000 <= os.path.getsize(jp) <= 1200000,
  "boxes": p.BOXES, "fold_y": p.YMID, "box_symmetry": "measured: box k and box 9-k have equal height and mirror positions about y=1420",
  "check": "Folding the page across its middle, each panel lies on a panel of the same composition (structurally verified for frames and set x-positions; perceptually judged from beat b05 by the maker; blind reading pending)",
  "evidence": "measured (box symmetry), perceptually judged (from frames) by the maker"},
 "weaknesses": ["a fold also flips each strip upside down, so standing figures land on their partners inverted: the match is in frame, set placement and text position, not in figure pose",
  "the agent is not at the same x in P1/P8 (desk vs cupboard): the story moves him; the set holds the palindrome",
  "strips are shallow; full figures are ~260 px tall, small at phone width; slip and balloon caps 40-48 px",
  "P4's answer-balloon tail passes close above the clock"]}
write_record(rec)
credit_pages(src, 71)
print("ok", rec["self_check"]["jpeg_bytes"])

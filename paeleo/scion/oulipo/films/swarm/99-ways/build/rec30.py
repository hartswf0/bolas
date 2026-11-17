import sys
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import p30_jump_cuts as P
from b1m2 import *
jp = PAGES_OUT / "30-jump-cuts.jpg"
im = Image.open(jp)
gaps = {k: v[0] for k, v in P.GAPS.items()}
src = ["99-ways-template:anrc-gold-key-1922", "99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"]
credit_pages(src, 30)
rec = {
 "n": 30, "id": "jump-cuts", "title": "Jump cuts", "family": "time and order", "medium": "shadow-puppet",
 "canon_revision": "c1",
 "rule": "Consecutive panels skip unequal stretches of time, each gap stated in a caption ('three seconds later', 'forty seconds later').",
 "declares": "keeps E0-E5, the four lines and the outcome",
 "file": "assets/pages/99-ways/30-jump-cuts.jpg", "master": "films/sources/99-ways/masters/30-jump-cuts.png",
 "beats_dir": "films/sources/99-ways/beats/30",
 "build": "films/swarm/99-ways/build/p30_jump_cuts.py (screen and puppet tools: build/p05_noir.py; figures and set pieces: build/b1m2.py)",
 "sources": src,
 "made": [
  "HANDMADE black cut-paper silhouette puppets of the b1m2 model (agent in profile: spectacles cut through, waistcoat buttons, pencil, pinned joints; the stranger as a bust with cloche hat held back beyond the glass, soft grey) and cut set pieces (desk and lamp, ticket window with TICKET OFFICE cut through its header, wall clock, cupboard with leaf on the left jamb, SERVICE door)",
  "page 05's lamp-lit paper screen (LoC 1934 sheet fibre) used WITHOUT its blind slats and with an even, wide lamp, so this page is plain shadow theatre, not noir",
  "the ANRC 1922 key cutout on its hook as the one brass gel (no glow halo beyond page 05's tool default), tagged SERVICE",
  "seven shots: one wide establishing shot, then six cuts each opening on a pasted caption slip stating the skip: 6, 11, 3, 2, 40 and 22 seconds (all different); the opening slip sets the clock: 'Nineteen seconds to ten past four.' (4:09:41), so the answer falls at 4:10:01 and the clock reads 4:10 when he answers",
  "the four canon lines on cut-paper balloons in the shared pen hand (penlib.balloon_piece), captions in the same hand; folio by pen99.folio"
 ],
 "gaps_seconds": gaps, "gaps_distinct": len(set(gaps.values())) == len(gaps),
 "timeline": {"P1": "4:09:41", "P2": "4:09:47", "P3": "4:09:58", "P4": "4:10:01", "P5": "4:10:03", "P6": "4:10:43", "P7": "4:11:05"},
 "captions": [P.START + "."] + [v[1] for v in P.GAPS.values()],
 "events": {"E0": "P1 at the desk with the memo slip ('4:15 - open SERVICE door. Key in cupboard.'), wide shot of the office, clock just before ten past; P2 (+6 s) already halfway to the cupboard",
            "E1": "P3 (+11 s) turned back to the TICKET OFFICE window; the stranger's question",
            "E2": "P4 (+3 s) head back to the clock at 4:10; the answer",
            "E3": "P5 (+2 s) she turns from the glass; the thanks; he is already walking on",
            "E4": "P6 (+40 s) before the open cupboard, the key on its hook, the SERVICE door shut beside it",
            "E5": "P7 (+22 s) pencil to his chin, the forgetting line; key on its hook; SERVICE door shut"},
 "lines": {"question": "Pardon me — have you the right time?", "answer": "Ten past four, by the clock.",
           "thanks": "Much obliged!", "forgetting": "Well, here I am... and what for?"},
 "beat": "the cuts land one by one: each new shot appears with its stated skip, and the forty-second hole before the open cupboard is where the errand goes",
 "beat_frames": ["b01: P1 (the wide shot)", "b02: + P2 'Six seconds later'", "b03: + P3 'Eleven seconds later'", "b04: + P4 'Three seconds later'",
                 "b05: + P5 'Two seconds later'", "b06: + P6 'Forty seconds later'", "b07: + P7 'Twenty-two seconds later' (the finished page)"],
 "self_check": {
  "size_px": list(im.size), "jpeg_bytes": jp.stat().st_size, "jpeg_quality": 90,
  "in_target_0.4_1.2MB": 400000 <= jp.stat().st_size <= 1200000,
  "panels": 7, "panels_after_first_with_stated_gap": 6, "caption_cap_px": P.CAP, "balloon_cap_px": P.BCAP,
  "check": "Every panel after the first carries a stated time gap, and no two gaps are equal (measured from the caption table: 6, 11, 3, 2, 40, 22; perceptually judged from the full-size page: each slip sits top left of its shot and reads at phone width)",
  "evidence": "measured (gap list) and perceptually judged (full-size page) by the maker"
 },
 "weaknesses": ["the shots change framing at every cut, so these read as time-skipping cuts rather than strict same-angle film jump cuts",
                "P6 shows the cupboard already open; the opening itself falls inside the forty-second skip (stated, not drawn)",
                "the agent's pencil at his chin in P7 is small at phone width; the stranger is a grey shadow behind the glass, as on page 05",
                "the P3 balloon touches the agent's near arm"]
}
write_record(rec)
print(rec["gaps_distinct"], rec["self_check"]["jpeg_bytes"])

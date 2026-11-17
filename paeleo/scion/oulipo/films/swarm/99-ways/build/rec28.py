import sys
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import p28_dealt_cards as P
from b1m2 import *
page, masks = P.build()
cov = P.coverage(masks)
jp = PAGES_OUT / "28-dealt-cards.jpg"
im = Image.open(jp)
src = ["99-ways-subjective:lightbox-paper-hands", "99-ways-template:anrc-gold-key-1922",
       "99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"]
new = [{"id": "99-ways-subjective:lightbox-paper-hands",
        "title": "Lightbox paper hands: lit fibrous paper sheet, felt board, scissor-faceted cut pieces, RightHand pinch rig",
        "author": "this production (99-ways-subjective swarm), films/swarm/99-ways-subjective/test-shot-build/lightbox.py and e4.py",
        "license": "made for this work",
        "used_as": "page 28: each card's lit paper sheet (lightbox.make_page on one window), the felt board, the agent's cut paper hand/cuff/sleeve (e4.RightHand) and facet() cuts; imported, not copied"}]
credit_pages(src, 28, new_entries=new)
rec = {
 "n": 28, "id": "dealt-cards", "title": "Dealt cards", "family": "layout and page grammar", "medium": "paper-hands",
 "canon_revision": "c1",
 "rule": "Panels overlap like cards dealt one on another; each later beat partly covers the earlier, the last lies uncovered.",
 "declares": "keeps E0-E5, the four lines and the outcome",
 "file": "assets/pages/99-ways/28-dealt-cards.jpg", "master": "films/sources/99-ways/masters/28-dealt-cards.png",
 "beats_dir": "films/sources/99-ways/beats/28",
 "build": "films/swarm/99-ways/build/p28_dealt_cards.py (imports 99-ways-subjective/test-shot-build/lightbox.py, e4.py; build/b1m2.py)",
 "sources": src,
 "made": [
  "seven lit paper cards, each one lightbox sheet (99-ways-subjective lightbox.make_page restricted to a 1100x800 window: fibres, flocculation, one lamp behind), reduced to 946x688 with a scissor-faceted edge",
  "first-person views (the agent's eye): his cut paper right hand, cuff and sleeve from the 99-ways-subjective e4.RightHand rig, posed by its pinch point and drawn at 0.62 of the rig's units, soft behind the sheet with its penumbra; a cut pencil held in the pinch on cards 4 and 7",
  "set pieces cut sharp against the sheet (lightbox facet cuts): desk edge and inkwell, closed cupboard and SERVICE door, ticket window with TICKET OFFICE cut through its header board, the b1m2 wall clock at 4:10, the open cupboard with its leaf on the left jamb and lit interior, the ANRC 1922 key cutout as a silhouette on a cut hook",
  "the stranger (b1m2 bust, cloche hat) held back beyond the glass as a soft grey shadow on cards 3 and 5",
  "vellum slips (memo, SERVICE tags and card) and cut-paper balloons with the four canon lines in the shared pen hand (penlib.balloon_piece); the agent's own lines tailed off the bottom edge (the speaker is the viewer)",
  "the cards dealt in a zigzag down a felt board (lightbox felt, laid on the LoC 1934 sheet inside the live area) each over the one before with its own cast shadow; only card 7 lies wholly uncovered",
  "folio by pen99.folio on the sheet below the board"
 ],
 "events": {"E0": "card 1 his hand pinching the memo slip at the desk ('MEMO / 4:15 - open SERVICE door. / Key in cupboard.'); card 2 the closed cupboard and the SERVICE door ahead as he sets off",
            "E1": "card 3 the stranger beyond the TICKET OFFICE glass; question balloon tailed to her",
            "E2": "card 4 the wall clock at 4:10, his pencil hand raised to it; answer balloon tailed to the bottom edge (to him)",
            "E3": "card 5 she turns away beyond the glass; thanks balloon tailed to her",
            "E4": "card 6 his hand swings the cupboard leaf open; the key on its hook, tag SERVICE",
            "E5": "card 7 (on top, uncovered) the key still on its hook, the SERVICE door shut, his pencil hand raised; the forgetting line tailed to him"},
 "lines": {"question": "Pardon me — have you the right time?", "answer": "Ten past four, by the clock.",
           "thanks": "Much obliged!", "forgetting": "Well, here I am... and what for?"},
 "beat": "the dealing: with four cards on the felt, card 5 slides in from the deck turning and settles over card 4, then card 6, then card 7, which lands on top and stays uncovered",
 "beat_frames": ["b01: cards 1-4 dealt", "b02: card 5 in flight from the lower right, turning", "b03: card 5 settled over 4",
                 "b04: card 6 in flight", "b05: card 6 settled", "b06: card 7 in flight", "b07: card 7 settled on top (the finished page)"],
 "self_check": {
  "size_px": list(im.size), "jpeg_bytes": jp.stat().st_size, "jpeg_quality": 90,
  "in_target_0.4_1.2MB": 400000 <= jp.stat().st_size <= 1200000,
  "cards": 7, "coverage": cov,
  "each_card_covered_by_the_next": all(c["covered_by_next"] > 0.08 for c in cov[:-1]),
  "last_card_uncovered": cov[-1]["hidden_by_later"] == 0.0,
  "balloon_cap_px_on_page": 41,
  "check": "A reader orders the panels by which one lies on top (measured: every card k is overlapped by card k+1, 11-35% of its area, and card 7 is uncovered; perceptually judged from the full-size page: shadows make the stacking order unambiguous; blind reading pending)",
  "evidence": "measured (overlap fractions) and perceptually judged (full-size page) by the maker"
 },
 "weaknesses": ["the agent is only his hands; card 2 (setting off) has no hand and reads as a plain view of the two doors",
                "first person cannot show the pencil at his chin: card 7 has the pencil hand raised into the bottom of the view instead",
                "the hands are soft shadows behind the sheet (the medium's rule), so at phone width the pencil reads better than the fingers",
                "the cards are lit sheets lying on felt, a lightbox look rather than strictly physical card stock"]
}
write_record(rec)
print(rec["self_check"]["each_card_covered_by_the_next"], rec["self_check"]["last_card_uncovered"])

"""Record + credits for page 36 Flip corner."""
import sys
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import b1m2

jp = b1m2.PAGES_OUT / "36-flip-corner.jpg"
src = ["99-ways-subjective:lightbox-paper-hands", "99-ways-template:anrc-gold-key-1922",
       "99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"]
LN = {"question": "Pardon me — have you the right time?", "answer": "Ten past four, by the clock.",
      "thanks": "Much obliged!", "forgetting": "Well, here I am... and what for?"}
rec = {
 "n": 36, "id": "flip-corner", "title": "Flip corner", "family": "reader and object", "medium": "paper-hands",
 "canon_revision": "c1",
 "rule": "A small flip sequence runs down the page's outer corner; flipped, it animates the forgetting.",
 "declares": "keeps E0-E5, the four lines and the outcome",
 "file": "assets/pages/99-ways/36-flip-corner.jpg", "master": "films/sources/99-ways/masters/36-flip-corner.png",
 "beats_dir": "films/sources/99-ways/beats/36",
 "build": "films/swarm/99-ways/build/p36_flip_corner.py (imports build/p28_dealt_cards.py, which imports 99-ways-subjective/test-shot-build/lightbox.py and e4.py)",
 "sources": src,
 "made": [
  "a flip strip of twelve small lit sheets (282 x 205 px) down the outer (left: page 36 is a verso) edge, numbered 1-12 on the inner side in the shared pen hand",
  "flip frames: the open cupboard from the agent's eye, the ANRC 1922 key cutout on its cut hook tagged SERVICE; his scissor-cut paper right hand (99-ways-subjective e4.RightHand rig, soft behind the sheet) rises toward the key (1-4), stops just short (5), hangs there (6-7), sinks away as the pencil comes up in its pinch instead (8-11); frame 12 the key alone on its hook",
  "seven first-person lit sheets (805 x 585 px; 99-ways-subjective lightbox paper) in two columns beside the strip: memo in his hand; the cupboard and SERVICE door ahead; the question through TICKET OFFICE glass (stranger a soft grey bust beyond it); the clock at 4:10 and his pencil hand; the thanks as she turns; his hand swings the leaf open on the left jamb, key on its hook; the forgetting with the key on its hook and the SERVICE door shut",
  "the four canon lines on cut-paper pen-hand balloons; his own lines tailed off the sheet's bottom edge (the speaker is the viewer)",
  "a vellum note in the eighth slot pointing the reader to the corner frames 1 to 12"
 ],
 "flip_frames": ["1-4: the hand rises toward the key", "5: stops just short", "6-7: hangs there",
                 "8-11: sinks away; the pencil comes up instead", "12: the key alone on its hook"],
 "events": {"E0": "sheets 1-2", "E1": "sheet 3", "E2": "sheet 4", "E3": "sheet 5", "E4": "sheet 6",
            "E5": "sheet 7 and the flip strip (the forgetting animated)"},
 "lines": LN, "substitutions": "none",
 "beat": "the corner flipped: the hand rises to the key, stops short, hangs, and sinks away with the pencil; the key never moves",
 "beat_frames": ["b01: flip frame 1", "b02: frame 3", "b03: frame 5 (stops short)", "b04: frame 6 (hangs)",
                 "b05: frame 8 (pencil comes up)", "b06: frame 10", "b07: frame 11", "b08: frame 12 (key alone)"],
 "self_check": {
  "size_px": [2200, 2850], "jpeg_bytes": jp.stat().st_size, "jpeg_quality": 90,
  "in_target_0.4_1.2MB": 400000 <= jp.stat().st_size <= 1200000,
  "flip_frames": 12, "frame_numbers": "1-12, beside each frame",
  "check": "A reader finds the corner sequence and its frame numbers (perceptually judged at full size: a numbered strip down the left edge, signposted by the vellum note; blind reading pending)",
  "evidence": "measured (frame count, size, bytes) and perceptually judged (full-size page) by the maker"
 },
 "weaknesses": [
  "the strip runs the whole outer edge rather than sitting only in the bottom corner, so it is a flip column more than a corner",
  "at phone width the flip frames are small: the hand reads, the pencil in frames 8-11 is thin",
  "the pencil comes up in his hand but cannot reach his chin in first person (as on page 28)",
  "the main sheets reuse page 28's set builders and look close to it"
 ]
}
b1m2.write_record(rec)
b1m2.credit_pages(src, 36)
print("ok", rec["self_check"]["jpeg_bytes"])

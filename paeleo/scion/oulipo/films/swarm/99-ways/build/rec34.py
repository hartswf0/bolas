"""Record + credits for page 34 Thirty-two panels."""
import sys
from pathlib import Path
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/kit")
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import b1m2
import p34_thirty_two as P

jp = b1m2.PAGES_OUT / "34-thirty-two.jpg"
src = ["99-ways:loc-harpers-1863-army-telegraph-operator", "99-ways:loc-1867-dickens-tickets-steinway",
       "99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"]
rec = {
 "n": 34, "id": "thirty-two", "title": "Thirty-two panels", "family": "reduction and expansion",
 "medium": "engraving-puppet", "canon_revision": "c1",
 "rule": "Every micro-action drawn: thirty-two small panels.",
 "declares": "keeps E0-E5, the four lines and the outcome",
 "file": "assets/pages/99-ways/34-thirty-two.jpg", "master": "films/sources/99-ways/masters/34-thirty-two.png",
 "beats_dir": "films/sources/99-ways/beats/34",
 "build": "films/swarm/99-ways/build/p34_thirty_two.py (puppets and pen set: kit/build_page03.py)",
 "sources": src,
 "made": [
  "a storyboard sheet of 32 equal boards (4 x 8, 480 x 308 px) ruled in the pen hand on the LoC 1934 sheet, each numbered 1-32 on a pasted slip at its lower right",
  "the page-03 engraving puppets reused: AGENT = Harper's 1863 telegraph operator cut into pinned limbs (brass pins), STRANGER = the 1867 Steinway Hall woman; the engraved table and ticket window from the same plates",
  "posed per micro-action: reading, head up, turning, two steps, stopping, turning to the voice, looking up at the clock, turning back, the answer gesture, turning toward the cupboard, two steps, hand to the knob, the door at 0 / 0.45 / 1.0 open, looking, pencil rising, pencil at the chin; one large close-up of the puppet with the pencil at his chin (panel 31)",
  "HANDMADE pen set (build_page03): memo close-up, clock at 4:09 / 4:10 (close-up in panel 12) / 4:11, cupboard hinged on its left jamb, the key on its hook with its SERVICE tag (close-ups 26 and 31), SERVICE door with its card",
  "the four canon lines verbatim in cut-paper pen-hand balloons (panels 7, 14, 16, 30)",
  "each board softened 0.6 px (print softness, to hold the JPEG under 1.2 MB); sheet grain softened 1.6 px in the gutters"
 ],
 "panels": {str(i + 1): b for i, b in enumerate(P.BEATS)},
 "events": {"E0": "panels 1-6", "E1": "panels 7-10", "E2": "panels 11-14", "E3": "panels 15-20",
            "E4": "panels 21-26", "E5": "panels 27-32"},
 "lines": {k: v for k, v in P.LN.items()},
 "substitutions": "none",
 "beat": "the storyboard fills row by row: four new micro-action boards per frame until all thirty-two are numbered",
 "beat_frames": [f"b{k:02d}: rows 1-{k} (panels 1-{4 * k})" for k in range(1, 9)],
 "self_check": {
  "size_px": [2200, 2850], "jpeg_bytes": jp.stat().st_size, "jpeg_quality": 90,
  "in_target_0.4_1.2MB": 400000 <= jp.stat().st_size <= 1200000,
  "panels": 32, "panel_numbers": "1-32, one per panel",
  "check": "A reader counts thirty-two panels (measured: 32 ruled boxes of identical size in a 4 x 8 grid, each numbered; perceptually judged at full size: the numbers and the four balloons read at phone width)",
  "evidence": "measured (grid, size, bytes) and perceptually judged (full-size page) by the maker"
 },
 "weaknesses": [
  "the 1863 operator puppet has only one leg pose, so the 'steps' are carried by position and arm swing rather than a stride",
  "panel 18 (she has gone) differs from panel 17 only by her absence at the frame edge",
  "the woman's head sits behind the window plate in several boards and reads small",
  "the panel 30 balloon covers the cupboard's top and the SERVICE card",
  "boards are softened 0.6 px for file size"
 ]
}
b1m2.write_record(rec)
b1m2.credit_pages(src, 34)
print("ok", rec["self_check"]["jpeg_bytes"])

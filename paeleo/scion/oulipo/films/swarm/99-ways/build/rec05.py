import sys
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
from b1m2 import *
jp = PAGES_OUT / "05-noir.jpg"
im = Image.open(jp)
src = ["99-ways-template:anrc-gold-key-1922", "99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"]
credit_pages(src, 5)
rec = {
 "n": 5, "id": "noir", "title": "Noir", "family": "genre", "medium": "shadow-puppet", "canon_revision": "c1",
 "rule": "Hardboiled first-person narration, blind-slat light, the brass key as the thing that matters.",
 "declares": "keeps E0-E5, the four lines and the outcome",
 "file": "assets/pages/99-ways/05-noir.jpg", "master": "films/sources/99-ways/masters/05-noir.png",
 "beats_dir": "films/sources/99-ways/beats/05",
 "build": "films/swarm/99-ways/build/p05_noir.py (figure model and set pieces: build/b1m2.py)",
 "sources": src,
 "made": [
  "HANDMADE black cut-paper silhouette puppets authored as control points in b1m2.py: the agent in profile (spectacles cut through, waistcoat button holes, sleeve-garter slit on the shirt sleeve, pencil, pinned shoulder and elbow rivets), the stranger as a bust with cloche hat and bow, held back behind the glass so she falls soft and grey",
  "HANDMADE cut set pieces: desk and lamp, ticket window with TICKET OFFICE cut through its header board in the pen hand, wall clock at 4:10 with pendulum, cupboard with the leaf hinged on the left jamb (projected open), SERVICE door",
  "lit paper screen: lamp hotspot, fibre of the LoC 1934 sheet, blind-slat shadow bands in a slanted window patch",
  "the ANRC 1922 key cutout (99-ways-template piece) laid as an amber brass gel with a glow: the only colour on the page",
  "hardboiled first-person captions (ours) and the four canon lines, all in the shared pen hand on pasted slips and cut-paper balloons (penlib.balloon_piece); folio by pen99.folio"
 ],
 "events": {
  "E0": "P1 at the desk, the memo slip legible ('4:15 - open SERVICE door. Key in cupboard.'); P2 he walks toward the closed cupboard",
  "E1": "P3 the stranger behind the TICKET OFFICE glass; question balloon tailed to her",
  "E2": "P4 he looks up at the clock (4:10); answer balloon",
  "E3": "P5 she turns away behind the glass; thanks balloon",
  "E4": "P6 cupboard open, the brass key glowing on its hook, tag SERVICE",
  "E5": "P7 pencil-hand to his chin, the forgetting line; key still on its hook; SERVICE door closed"
 },
 "lines": {"question": "Pardon me — have you the right time?", "answer": "Ten past four, by the clock.",
           "thanks": "Much obliged!", "forgetting": "Well, here I am... and what for?"},
 "captions": [
  "Four-fifteen, the memo said. Open the SERVICE door. The key's in the cupboard. Simple job. They all start simple.",
  "So I got up and went for the key. Nine steps. I'd walked them a thousand times.",
  "Then a dame at the window. Hat, gloves, a voice like rain on the platform.",
  "I gave her the clock. Only honest face in the building.",
  "And she was gone. Took nothing. That's what I told myself.",
  "The cupboard. The key. Brass, on its hook, tagged SERVICE, looking at me like it knew something I didn't.",
  "The key stayed on its hook. The door stayed shut. Somebody took something off me that afternoon. I still couldn't tell you what."],
 "beat": "the cupboard leaf swings open across the slat light and the brass key comes into the light; then the forgetting balloon is laid in P7",
 "beat_frames": ["b01: P6 cupboard closed, P7 without balloon", "b02: leaf 38 degrees open, the key still hidden behind it",
                 "b03: leaf 76 degrees, the key half in the light", "b04: leaf fully open, key glowing on its hook",
                 "b05: the forgetting balloon laid in P7 (the finished page)"],
 "self_check": {
  "size_px": list(im.size), "jpeg_bytes": jp.stat().st_size, "jpeg_quality": 90,
  "in_target_0.4_1.2MB": 400000 <= jp.stat().st_size <= 1200000,
  "check": "A reader names the genre as crime or noir: hardboiled first-person captions ('a dame at the window', 'Only honest face in the building', 'Somebody took something off me'), blind-slat light in every panel, the key as the one coloured, glowing object (perceptually judged from the full-size page by the maker; blind reading pending)",
  "panels": 7, "caption_cap_px": 40, "balloon_cap_px": 50,
  "outcome": "key on its hook in P6 and P7; SERVICE door closed with its card in P7",
  "evidence": "perceptually judged (from frames) by the maker; independent readers not yet run"
 }
}
write_record(rec)
print(rec["self_check"])

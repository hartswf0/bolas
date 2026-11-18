"""Record + credits for page 37 No borders."""
import sys
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import numpy as np
from PIL import Image
import b1m2
import p37_no_borders as P

jp = b1m2.PAGES_OUT / "37-no-borders.jpg"
nlines = P.ruled_line_check(np.asarray(Image.open(b1m2.MASTERS / "37-no-borders.png").convert("RGB")))
src = ["99-ways:daumier-proprietaire-1846", "99-ways:daumier-premier-voyage-1846", "99-ways:daumier-grand-tunnel-1843",
       "99-ways-template:anrc-gold-key-1922", "99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"]
LN = {"question": "Pardon me — have you the right time?", "answer": "Ten past four, by the clock.",
      "thanks": "Much obliged!", "forgetting": "Well, here I am... and what for?"}
rec = {
 "n": 37, "id": "no-borders", "title": "No borders", "family": "layout and page grammar", "medium": "daumier-collage",
 "canon_revision": "c1",
 "rule": "No panel frames: figures, objects and balloons float on the page, ordered only by placement and tails.",
 "declares": "keeps E0-E5, the four lines and the outcome",
 "file": "assets/pages/99-ways/37-no-borders.jpg", "master": "films/sources/99-ways/masters/37-no-borders.png",
 "beats_dir": "films/sources/99-ways/beats/37",
 "build": "films/swarm/99-ways/build/p37_no_borders.py (collage kit: build/daumier12.py, build/p12_loop.py)",
 "sources": src,
 "made": [
  "one open LoC 1934 sheet, no frames, no floor lines, no caption boxes: every piece glued straight on the paper with its scissor rim and cast shadow, a soft blurred contact shadow under each standing group",
  "three bands read left to right, top to bottom: (1) at the desk with the memo, risen and setting off, the ticket window with the stranger and her question; (2) the clock and the agent looking up at it with his answer, the stranger turned away from the window with her thanks; (3) the open cupboard with the key, then the forgetting beside the shut SERVICE door",
  "page 12's Daumier collage kit reused: the bourgeois of 'Il est devenu pro-pri-e-taire !' (1846) as the AGENT (body and pinned head, six placements, one cut at the waist behind the desk); the bonneted old woman and the carriage window of 'Un premier voyage en chemin de fer' (1846) as the STRANGER and the ticket window; the CONCIERGE door as the SERVICE door; desk, cupboard, counter and clock case cut from the prints' own crayon tone (stairwell, carriage wall, tunnel black of 'L'entree du grand tunnel', 1843)",
  "the ANRC 1922 key cutout in the cupboard with a SERVICE slip; HANDMADE cut-paper pencil (to his chin at the end), clock hands at 4:10, the four canon lines on cut-paper pen-hand balloons whose tails carry the order"
 ],
 "events": {"E0": "band 1 left: desk, memo slip ('4:15 - open SERVICE door. Key in cupboard.'), then the risen agent facing right",
            "E1": "band 1 right: the stranger at the TICKET OFFICE window; question balloon tailed to her",
            "E2": "band 2 left: clock at 4:10; the agent looks up at it; answer tailed to his mouth",
            "E3": "band 2 right: she has turned away beside the window; thanks tailed to her",
            "E4": "band 3 left: the cupboard open on its left jamb, the key on its hook tagged SERVICE, the agent before it",
            "E5": "band 3 right: pencil at his chin, the forgetting line; key on its hook; SERVICE door shut"},
 "lines": LN, "substitutions": "none",
 "beat": "the pieces are glued onto the bare sheet one group at a time, in reading order, with no frame ever drawn",
 "beat_frames": ["b01: E0 desk and setting off", "b02: + E1 window and question", "b03: + E2 clock and answer",
                 "b04: + E3 thanks", "b05: + E4 open cupboard", "b06: + E5 the forgetting (finished page)"],
 "self_check": {
  "size_px": [2200, 2850], "jpeg_bytes": jp.stat().st_size, "jpeg_quality": 90,
  "in_target_0.4_1.2MB": 400000 <= jp.stat().st_size <= 1200000,
  "long_straight_dark_lines_found": nlines,
  "check": "No ruled frame line appears anywhere on the page (measured: Hough search for straight dark lines >= 500 px found " + str(nlines) + "; no frame, border or ground line is drawn by the build; perceptually judged at full size)",
  "evidence": "measured (Hough line search, size, bytes) and perceptually judged (full-size page) by the maker"
 },
 "weaknesses": [
  "the cut set pieces (desk, counter, cupboard, door) have straight scissor edges, which a strict reader might take for frame-like lines, though none is a ruled border",
  "the agent repeats the same Daumier body in six placements (only the head tilts and the facing flips), as on page 12",
  "the stranger is the old bonneted woman of the 1846 carriage print, read as a traveller only by the window",
  "the band 1 question is asked while the agent is still mid-room; his stopping is implied by placement only"
 ]
}
b1m2.write_record(rec)
b1m2.credit_pages(src, 37)
print("ok", nlines, rec["self_check"]["jpeg_bytes"])

"""Record + credits for page 33 (Ticket stock)."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import b1m2 as B

N, PID = 33, "ticket-stock"
size = (B.PAGES_OUT / f"{N:02d}-{PID}.jpg").stat().st_size
src = ["99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"]
B.credit_pages(src, N)
B.write_record({
    "n": N, "id": PID, "title": "Ticket stock", "family": "medium and material", "medium": "cut-paper", "canon_revision": "c1",
    "rule": "Told on a strip of railway card tickets, one beat per ticket, dated, numbered and punched.",
    "declares": "keeps E0-E5, the four lines and the outcome",
    "file": f"assets/pages/99-ways/{N:02d}-{PID}.jpg", "master": f"films/sources/99-ways/masters/{N:02d}-{PID}.png",
    "beats_dir": f"films/sources/99-ways/beats/{N:02d}", "build": "films/swarm/99-ways/build/p33_ticket_stock.py",
    "sources": src,
    "made": [
        "a strip of six card tickets, HANDMADE cut paper (cutpaper99.Cut: scissor-faceted card, the LoC 1934 sheet's fibre as tone, one down-right shadow; card grain held at 0.55 for the file-size target), six card colours, joined at rows of round perforation holes",
        "each ticket printed in the shared pen hand: a stub with 'No.', the big ticket number 1-6 and a serial (Ser. 3701-3706) behind a perforated divider; 'CENTRAL VERMONT RY.  RANDOLPH, VT.'; a route line (DESK to CUPBOARD / STOP: TICKET WINDOW / CLOCK: 4:10 / RETURN: PLATFORM / ARRIVAL: CUPBOARD / NOT GOOD FOR: SERVICE DOOR); the beat in two lines with the canon memo text and the four lines verbatim; small print 'Good for this afternoon only. Not transferable.'",
        "dated: a violet dater-stamp oval on each ticket, 'SEP 1937' and the minute (4:09, 4:10, 4:10, 4:10, 4:11, 4:11 PM), uneven ink; the clock reads 4:10 at the answer, before the memo's 4:15",
        "punched: a conductor's clipper hole cut through each ticket's stub (the sheet shows through, the hole's edge shadowed)",
        "a small cut-paper picture on each ticket, re-cut from page 16's cut-paper figure kit (p16_fewest_marks: agent, stranger, clock, ticket window, cupboard opening on its left jamb, key with SERVICE tag, SERVICE door, memo, desk); folio '33 / Ticket stock' (pen99.folio)"],
    "events": {"E0": "ticket 1 (4:09): DESK to CUPBOARD, the memo, he sets off",
               "E1": "ticket 2 (4:10): STOP: TICKET WINDOW, the question",
               "E2": "ticket 3 (4:10): CLOCK: 4:10, the answer",
               "E3": "ticket 4 (4:10): RETURN: PLATFORM, the thanks",
               "E4": "ticket 5 (4:11): ARRIVAL: CUPBOARD, the key on its hook, tag SERVICE",
               "E5": "ticket 6 (4:11): NOT GOOD FOR: SERVICE DOOR, the forgetting line; key stays, door shut"},
    "lines": {"question": "Pardon me — have you the right time?", "answer": "Ten past four, by the clock.",
              "thanks": "Much obliged!", "forgetting": "Well, here I am... and what for?"},
    "beat": "the strip is issued ticket by ticket, each one clipped (punched) as the next is laid",
    "beat_frames": ["b01: ticket 1 laid, unpunched", "b02: ticket 1 punched, ticket 2 laid", "b03: 2 punched, 3 laid",
                    "b04: 3 punched, 4 laid", "b05: 4 punched, 5 laid", "b06: 5 punched, 6 laid", "b07: 6 punched (= the page)"],
    "self_check": {"size_px": [2200, 2850], "jpeg_bytes": size, "jpeg_quality": 90,
                   "in_target_0.4_1.2MB": 400000 <= size <= 1200000,
                   "tickets": 6, "numbered": [1, 2, 3, 4, 5, 6], "dated": True, "punched": 6, "lines_verbatim": True,
                   "check": "A reader reads the tickets in number order (1-6, top to bottom) and finds E0-E5 (maker's judgement from the full-size page; blind reading pending)"},
})
print(size)

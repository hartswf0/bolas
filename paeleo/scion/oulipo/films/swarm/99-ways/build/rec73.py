import os, sys
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
from b1m2 import write_record, credit_pages, PAGES_OUT
src = ["99-ways-template:rothstein-randolph-agent-1937", "99-ways-template:anrc-gold-key-1922", "99-ways:rol-34852-sainte-catherine-1913",
       "99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"]
sz = os.path.getsize(PAGES_OUT / "73-cover.jpg")
rec = {"n": 73, "id": "cover", "title": "Cover", "family": "layout and page grammar", "medium": "rol-cutout", "canon_revision": "c1",
 "rule": "The incident told as the front cover of a 1937 story paper: masthead, one dramatic picture, cover lines that carry E0-E5.",
 "declares": "E1-E3 carried by cover lines rather than drawn",
 "file": "assets/pages/99-ways/73-cover.jpg", "master": "films/sources/99-ways/masters/73-cover.png", "beats_dir": "films/sources/99-ways/beats/73",
 "build": "films/swarm/99-ways/build/p73_cover.py (cover grammar and Rol woman: kit/build_page04.py; picture: kit/build_page01.panel_rest P8)",
 "sources": src,
 "made": [
  "masthead of an invented story paper, STATION STORIES (ours), lettered letter by letter in the shared pen hand on a red band (cream/black jumping capitals, page 04's jumpy()), with 'EVERY THURSDAY', 'No. 371 - 5 CENTS' and a black dateline strip 'SEPTEMBER 23, 1937 - A COMPLETE RAILWAY TALE IN THIS ISSUE'",
  "masthead ear: a round print of the Agence Rol 34852 woman (page 04's GrabCut cutout, head and shoulders) as the lady at the window",
  "one dramatic picture: the 99-ways-template rest layers of P8 recomposed without balloons (Rothstein agent cutout, pencil to his chin, before the open cupboard door with the ANRC key on its HANDMADE hook and SERVICE tag, the SERVICE card behind), one 10 % warm grade, white print border",
  "story title 'The SERVICE Key!' in jumping red/black on a cut butter ribbon",
  "cover lines on pasted slips (butter and red): E0 '4:15, said the memo: open the SERVICE door! The key? In the cupboard.'; E1 'Then a lady at the window: \"Pardon me — have you the right time?\"'; E2 '\"Ten past four, by the clock.\"'; E3 '\"Much obliged!\" - and she was gone.'",
  "foot band (warm grey): E4 'He opens the cupboard - and there hangs the KEY!' in jumping lettering; E5 slip '\"Well, here I am... and what for?\"'; 'The SERVICE door stays shut! Why did he come? Read it inside.'",
  "folio '73 / Cover' (pen99.folio)"],
 "events": {"E0": "cover line slip 1 (memo)", "E1": "cover line slip 2 (red) with the question", "E2": "cover line slip 3, the answer", "E3": "cover line slip 4 (red), the thanks",
  "E4": "the picture (open cupboard, key on its hook) and the foot band line", "E5": "the picture (pencil to chin), the forgetting slip and the outcome line"},
 "lines": {"question": "Pardon me — have you the right time?", "answer": "Ten past four, by the clock.", "thanks": "Much obliged!", "forgetting": "Well, here I am... and what for?"},
 "substitutions": "none: the four lines quoted verbatim inside the cover lines",
 "beat": "the cover made up: masthead and picture; the title ribbon; the cover lines pasted one by one in story order E0, E1, E2-E3; the foot band E4; the forgetting slip and outcome line",
 "beat_frames": ["b01: masthead, dateline, ear and the picture alone", "b02: + title ribbon 'The SERVICE Key!'", "b03: + E0 cover line", "b04: + E1 cover line",
  "b05: + E2 and E3 cover lines", "b06: + foot band E4", "b07: + E5 slip and outcome line (the page)"],
 "self_check": {"size_px": [2200, 2850], "jpeg_bytes": sz, "jpeg_quality": 90, "in_target_0.4_1.2MB": 400000 <= sz <= 1200000,
  "masthead": True, "pictures": 1, "cover_lines_cover": ["E0", "E1", "E2", "E3", "E4", "E5"],
  "check": "A reader identifies a masthead and cover lines and can still retell the incident (perceptually judged from the full-size page by the maker; blind reading pending)",
  "evidence": "perceptually judged (from the full page) by the maker"},
 "weaknesses": ["the ear print of the Rol 1913 woman (a festive Sainte-Catherine bonnet) reads as an ornament more than as the 1937 traveller; she is not Bubley's figure",
  "the picture is page 01's P8 recomposed, so the cover shares its photograph with page 01 and pages 04/45",
  "'opens' and 'cupboard' in black on the grey foot band are lower contrast than the cream words",
  "a masthead ear with a second small photograph slightly stretches 'one dramatic picture'"]}
write_record(rec)
credit_pages(src, 73)
print("ok", sz)

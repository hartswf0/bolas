"""Records and credit page-lists for pages 97-99 (batch 9, maker 3)."""
import os
import sys
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
from b1m2 import write_record, credit_pages, PAGES_OUT  # noqa: E402

LINES = {"question": "Pardon me — have you the right time?", "answer": "Ten past four, by the clock.",
         "thanks": "Much obliged!", "forgetting": "Well, here I am... and what for?"}
SZ = lambda n, pid: os.path.getsize(PAGES_OUT / f"{n:02d}-{pid}.jpg")


def base(n, pid, title, family, medium, rule, declares, build, sources):
    return {"n": n, "id": pid, "title": title, "family": family, "medium": medium, "canon_revision": "c1", "rule": rule,
            "declares": declares, "file": f"assets/pages/99-ways/{n:02d}-{pid}.jpg",
            "master": f"films/sources/99-ways/masters/{n:02d}-{pid}.png", "beats_dir": f"films/sources/99-ways/beats/{n:02d}",
            "build": build, "sources": sources}


def sc(n, pid, frames, **kw):
    b = SZ(n, pid)
    d = {"size_px": [2200, 2850], "jpeg_bytes": b, "jpeg_quality": 90, "in_target_0.4_1.2MB": 400000 <= b <= 1200000,
         "beat_frames": frames, "beat_size": [960, 1242]}
    d.update(kw)
    d["evidence"] = "measured (size, word lists) and perceptually judged from the full-size page by the maker; blind reading pending"
    return d


S97 = ["99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"]
r = base(97, "six-words", "Six words", "reduction and expansion", "pen-hand",
         "Six panels, each captioned with a single word; no balloons.", "the four lines replaced by six single words",
         "films/swarm/99-ways/build/p97_six_words.py (pen and panels: build/p51_pen_alone.py; figure model: build/b1m2.py)", S97)
r.update({
    "made": ["six panels in a 2x3 grid, each a pen drawing over a ruled caption band holding one word: Errand. / Time? / "
             "Clock. / Thanks. / Key. / Why?",
             "drawings in page 51's one-weight pen (4.42 px, hidden lines lifted) over page 05's HANDMADE figure model "
             "(b1m2 agent with spectacles, waistcoat, pencil; stranger with hat behind the ticket window; desk, clock at 4:10, "
             "cupboard, key on its hook, SERVICE door)",
             "everything page 51 lettered is drawn unlettered so no seventh word appears: the memo as a ruled slip of pen "
             "scribble lines, the ticket-window header blank, the SERVICE door card and the key tag as blank ruled boxes",
             "caption words in the shared pen hand (pen99.letter, cap 116, weight 0.105); LoC 1934 sheet as the only ground; "
             "folio by pen99.folio"],
    "events": {"E0": "P1 'Errand.': memo slip on the desk, he walks from it toward the closed cupboard",
               "E1": "P2 'Time?': she at the ticket window, he stopped facing her",
               "E2": "P3 'Clock.': he looks up at the clock at 4:10",
               "E3": "P4 'Thanks.': she turns and leaves the window",
               "E4": "P5 'Key.': the cupboard open, the key on its hook",
               "E5": "P6 'Why?': pencil to his chin; key still on its hook; the SERVICE door shut"},
    "words": ["Errand.", "Time?", "Clock.", "Thanks.", "Key.", "Why?"],
    "substitutions": "the four lines become the single words Time? (question), Clock. (answer), Thanks. (thanks), Why? "
                     "(forgetting); Errand. and Key. caption E0 and E4",
    "beat": "the page written panel by panel: each picture drawn, then its one word lettered under it; the cupboard drawn "
            "shut then open; 'Why?' written last",
    "beat_frames": ["b01: frames ruled, P1 drawn (he has just left the desk), no word", "b02: 'Errand.' written",
                    "b03: P2 and 'Time?'", "b04: P3, P4 and 'Clock.', 'Thanks.'", "b05: P5 with the cupboard shut",
                    "b06: the cupboard open, the key on its hook, 'Key.'", "b07: P6 drawn, pencil at chin, no word",
                    "b08: 'Why?' written (= the page)"],
})
r["self_check"] = sc(97, "six-words", 8, words_outside_margin=6, balloons=0,
                     check="A reader counts exactly six words on the page outside the margin -> Errand, Time, Clock, Thanks, "
                           "Key, Why; memo scribble, blank cards and tag carry no letters; the folio line is the margin")
r["weaknesses"] = [
    "without the memo text, TICKET OFFICE and SERVICE lettering, the objects lean on their drawing and the six words: the "
    "SERVICE door is only 'a door with a blank card', and why the key matters is carried by 'Errand.' + 'Key.' alone",
    "'Clock.' names what he looks at rather than what he answers; the exact time is legible only from the clock hands",
    "the stranger is the b1m2 cut-paper model drawn in outline; her hat reads oddly behind the glazing bars",
    "the caption rule sits just under the floor line, so each panel ends in a double rule"]
write_record(r)
credit_pages(S97, 97)

S98 = ["99-ways:daumier-proprietaire-1846", "99-ways:daumier-premier-voyage-1846", "99-ways:daumier-grand-tunnel-1843",
       "99-ways-template:anrc-gold-key-1922", "99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"]
r = base(98, "short-words", "Short words", "formal / Oulipian rule", "daumier-collage",
         "Every word on the page has one syllable.", "lines rewritten in one-syllable words",
         "films/swarm/99-ways/build/p98_short_words.py (collage kit: build/daumier12.py, p12_loop.py, p50_brief_meeting.py; "
         "compositions after p67_inner_voice.py; forage record: films/sources/99-ways/forage/p12-daumier/meta.json)", S98)
r.update({
    "made": ["REUSED FORAGED: the three CC0 Daumier lithographs of pages 12/50/67 (Rijksmuseum via Commons; licence recorded "
             "by page 12), cut by that kit's hand-placed scissor polygons: the bourgeois as agent (arm re-cut on two pinned "
             "joints), the bonneted woman as stranger, the carriage window as ticket window, the CONCIERGE door as the "
             "staff door; set pieces cut from the prints' own crayon tone; the ANRC 1922 key cutout warmed to brass",
             "HANDMADE: six panels laid as page 67 with its thought clouds removed; a masthead slip 'SHORT WORDS / a tale "
             "told in words of one beat'; caption slips, balloons and signs all in one-syllable words in the shared pen hand",
             "sign substitutions: TICKET OFFICE -> FARES, SERVICE -> STAFF (door card and key tag), MEMO -> NOTE; the memo's "
             "4:15 given as a small pen clock face at a quarter past four drawn on the note (a numeral would read "
             "'four fif-teen')",
             "the door print's own lettering CONCIERGE pasted over with a lintel board cut from the prints' tone, under the "
             "STAFF card, so no printed long word shows", "LoC 1934 sheet ground; folio by pen99.folio"],
    "lines": {"question": "Say — have you the right time?", "answer": "Ten past four, by the clock.",
              "thanks": "Thanks so much!", "forgetting": "Well, here I am... and what for?"},
    "substitutions": "question 'Pardon me — have you the right time?' -> 'Say — have you the right time?'; thanks 'Much "
                     "obliged!' -> 'Thanks so much!'; answer and forgetting lines already all one-syllable, kept verbatim",
    "events": {"E0": "P1 he reads the note (STAFF door at [clock 4:15], key in the case) and gets up",
               "E1": "P2 the woman behind the FARES window: 'Say — have you the right time?'",
               "E2": "P3 he looks up at the clock (4:10): 'Ten past four, by the clock.'",
               "E3": "P4 'Thanks so much!'; she nods and goes",
               "E4": "P5 the case swung wide, the key on its hook in plain view",
               "E5": "P6 pencil to his chin: 'Well, here I am... and what for?'; key stays; STAFF door stays shut"},
    "word_list": "a am and at be beat by case clock desk door drawn fares for four gets glass goes hangs have he here his "
                 "hook i in is it its key looks much must nods note now of on one past plain reads right say she short "
                 "shut so staff stays swings tale ten thanks that the there thrown time to told up view voice way well "
                 "what wide words you",
    "beat": "the long words go: the canon question balloon is struck through in pen and replaced by the short-word line, "
            "then the thanks; last the signs TICKET OFFICE / SERVICE / MEMO are pasted over with FARES / STAFF / NOTE",
    "beat_frames": ["b01: canon lines and old signs ('Pardon me —', 'Much obliged!', TICKET OFFICE, SERVICE, MEMO)",
                    "b02: 'Pardon me — have you the right time?' struck through", "b03: 'Say — have you the right time?' pasted",
                    "b04: 'Much obliged!' struck through", "b05: 'Thanks so much!' pasted",
                    "b06: the signs pasted over: FARES, STAFF, NOTE with its clock (= the page)"],
})
r["self_check"] = sc(98, "short-words", 6, polysyllables_outside_folio=0,
                     check="No word on the page has two syllables -> every distinct word listed in word_list was checked by "
                           "hand as one syllable; the only exception is the shared folio numeral '98' (ninety-eight), which "
                           "the book's folio rule fixes on every page")
r["weaknesses"] = [
    "the folio numeral '98' reads as a three-syllable word; it is the book's fixed margin and was left as is",
    "the Daumier agent wears a top hat and tail-coat (as on pages 12/50/67), not the canon's shirt sleeves",
    "the note's drawn clock (4:15) is small (about 48 px across): legible on the full page, a dot at phone width; the P1 "
    "caption says only 'at the time drawn there'",
    "'case' for cupboard, 'STAFF' for SERVICE and 'FARES' for TICKET OFFICE are declared substitutions forced by the rule",
    "the woman faces into the window in P4 rather than visibly walking off; 'She nods and goes' carries the leaving",
    "the carriage-window piece shows faint show-through lettering from the print's verso (not legible as words)"]
write_record(r)
credit_pages(S98, 98)

S99 = ["99-ways-template:rothstein-randolph-agent-1937", "99-ways-template:rothstein-tavern-clock-1937",
       "99-ways-template:anrc-gold-key-1922", "99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"]
r = base(99, "marginalia", "Marginalia", "reader and object", "photo-cutout",
         "Page 01 reprinted small with an annotator's pencil notes pointing to the evidence for each event.",
         "keeps E0-E5, the four lines and the outcome", "films/swarm/99-ways/build/p99_marginalia.py", S99)
r.update({
    "made": ["page 01's own master (films/sources/99-ways/masters/01-template.png: the Rothstein 1937 agent and office, "
             "Rothstein tavern clock, ANRC 1922 key photo-cutouts) reprinted at 0.56 as a photographic print with a white "
             "border, one gentle neutral grade, laid 0.8 degrees askew with a cast shadow on the LoC 1934 sheet",
             "HANDMADE pencil: notes in the shared pen hand drawn in graphite grey (62,62,70), broken by the sheet's own "
             "tooth (high-pass of the LoC sheet grain); pencil rings round each piece of evidence on the print and bowed "
             "leaders with arrowheads from each note (one leader bent along a gutter to reach the clock)",
             "seven notes: a header 'p. 01, read again with a pencil: where does each event show?', notes E0-E5 each "
             "labelled with its event id, and a closing summary of the outcome", "folio by pen99.folio"],
    "events": {"E0": "note E0 (top left): rings on P1's memo and P3's shut cupboard",
               "E1": "note E1 (left): ring on P4's question balloon at the TICKET OFFICE glass",
               "E2": "note E2 (right): ring on P5's clock at 4:10",
               "E3": "note E3 (right): ring on P6's emptied window",
               "E4": "note E4 (left): ring on P7's key on its hook, tag SERVICE",
               "E5": "note E5 (bottom): rings on P8's pencil at the chin, the key still on its hook and the SERVICE card"},
    "lines": LINES, "substitutions": "none (the lines are page 01's, reprinted)",
    "beat": "the annotator works through the reprint: the bare print first, then one pencil note with its rings and "
            "leaders per event, E0 to E5, and last the summary",
    "beat_frames": ["b01: the reprint alone (header only)", "b02: + E0", "b03: + E1", "b04: + E2", "b05: + E3", "b06: + E4",
                    "b07: + E5 and the summary (= the page)"],
})
r["self_check"] = sc(99, "marginalia", 7, notes=["E0", "E1", "E2", "E3", "E4", "E5"],
                     check="A reader finds a note pointing to every event E0-E5 -> six labelled notes, each with a leader "
                           "ending in a pencil ring on page 01's evidence")
r["weaknesses"] = [
    "at 0.56 the reprinted page 01's own memo and key-tag lettering is tiny; the notes quote it so it need not be read there",
    "the reprint is page 01's digital master scaled, not a rephotographed print; the 'photographic print' is the border, "
    "grade, tilt and shadow",
    "the E0 leaders and the E5 leaders cross other panels of the reprint on their way to the evidence",
    "page 01 never shows the stranger; the E1 note says so instead of pointing to her",
    "the pencil is the shared pen hand in grey with paper tooth, not a separate pencil hand"]
write_record(r)
credit_pages(S99, 99)
print("ok")

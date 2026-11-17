"""Records for pages 13, 14, 15 (batch 2, page maker 1). Run after the page builds."""
import json
import sys

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
from b1m2 import *  # noqa

CANON = json.load(open(ROOT / "films" / "swarm" / "99-ways" / "canon.json"))
C = {c["n"]: c for c in CANON["constraints"]}
LINES = {"question": "Pardon me — have you the right time?", "answer": "Ten past four, by the clock.",
         "thanks": "Much obliged!", "forgetting": "Well, here I am... and what for?"}


def base(n, pid):
    c = C[n]
    jp = PAGES_OUT / f"{n:02d}-{pid}.jpg"
    im = Image.open(jp)
    nb = len(list((BEATS / f"{n:02d}").glob("b*.png")))
    return c, {
        "n": n, "id": pid, "title": c["title"], "family": c["family"], "medium": c["medium"], "canon_revision": CANON["revision"],
        "rule": c["rule"], "declares": c["declares"],
        "file": f"assets/pages/99-ways/{n:02d}-{pid}.jpg", "master": f"films/sources/99-ways/masters/{n:02d}-{pid}.png",
        "beats_dir": f"films/sources/99-ways/beats/{n:02d}",
    }, {"size_px": list(im.size), "jpeg_bytes": jp.stat().st_size, "jpeg_quality": 90,
        "in_target_0.4_1.2MB": 400000 <= jp.stat().st_size <= 1200000, "beat_frames": nb}


# ------------------------------------------------------------------ 13
def r13():
    import re
    import p13_only_questions as P
    P.SAID.clear()
    P.build()
    sents = [x for t in P.SAID for x in re.split(r"(?<=[?])\s+", t.strip())]
    c, rec, sc = base(13, "only-questions")
    src = ["99-ways-template:anrc-gold-key-1922", "99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"]
    rec.update({
        "build": "films/swarm/99-ways/build/p13_only_questions.py (figure model and set pieces: build/b1m2.py)",
        "sources": src,
        "made": [
            "HANDMADE black cut-paper shadow puppets (the b1m2 figure model: agent in profile with waistcoat, sleeve garter, spectacles and pencil cut through; the stranger as a bust with cloche hat) with their control rods: thin sticks from the chest and the working hand down past the bottom of each screen",
            "eight warm, lantern-lit paper screens (amber hotspot to a red-brown rim over the fibre of the LoC 1934 sheet), distinct from page 05's grey slat light",
            "cut set pieces: desk and lamp, ticket window with TICKET OFFICE in light through the header, clock at 4:10 with pendulum, cupboard (closed in P6, opened in P7-P8 on its left jamb), SERVICE door with its card",
            "the ANRC 1922 key cutout (99-ways-template piece) used as a black shadow shape on a cut hook, with a paper SERVICE tag",
            "the memo is a blank paper card on the desk (its words are carried by the P1 question, so no sentence on the page is a statement)",
            "all captions and balloons in the shared pen hand: 13 texts, every sentence a question; folio by pen99.folio",
        ],
        "substitutions": {"answer": "Ten past four, by the clock?", "thanks": "Much obliged?",
                          "memo": "not lettered on the card; P1 asks: 'Doesn't his memo say 4:15, open the SERVICE door, and isn't the key in the cupboard?'"},
        "lines": {"question": LINES["question"], "answer": "Ten past four, by the clock?", "thanks": "Much obliged?",
                  "forgetting": LINES["forgetting"]},
        "texts": P.SAID,
        "events": {"E0": "P1 at the desk with the memo card (asked in the caption); P2 he walks toward the closed cupboard",
                   "E1": "P3 the stranger soft behind the TICKET OFFICE glass; question balloon",
                   "E2": "P4 he looks up at the clock (4:10); answer as a question",
                   "E3": "P5 she turns away behind the glass; thanks as a question",
                   "E4": "P6 his hand on the knob of the closed cupboard ('what's behind the cupboard door?'); P7 the cupboard open, the key on its hook, tag SERVICE",
                   "E5": "P8 pencil to his chin, the forgetting line; the key still on its hook, the SERVICE door closed (both asked in slips)"},
        "beat": "the P7 cupboard leaf swings open on the screen (0, 35, 70, 112 degrees) and the key's shadow comes into the light; then the forgetting balloon is laid in P8",
        "beat_frames": ["b01: P7 cupboard closed, P8 without balloon", "b02: leaf 35 degrees", "b03: leaf 70 degrees",
                        "b04: leaf open, key on its hook", "b05: + forgetting balloon (the finished page)"],
    })
    sc.update({"panels": 8, "texts": len(P.SAID), "sentences": len(sents),
               "all_sentences_end_with_question_mark": all(x.endswith("?") for x in sents),
               "non_sentence_lettering": ["TICKET OFFICE (sign)", "SERVICE (tag and door card)", "folio title and number"],
               "caption_cap_px": 40, "balloon_cap_px": 48,
               "check": c["check"] + " -> measured on the page's text list (13 texts, 13 sentences, all ending '?'); signs and folio are labels, not sentences",
               "evidence": "measured (sentence check, size) and perceptually judged (from frames) by the maker; independent readers not yet run"})
    rec["self_check"] = sc
    rec["weaknesses"] = [
        "'Much obliged?' reads oddly by design; a reader may take it as sarcasm rather than thanks",
        "the memo card is blank: the memo's content lives only in the P1 question",
        "the stranger is a soft brown shadow behind the glass; her hat and coat read, her face does not",
        "P7 is a close-up without the agent, so E4 is split across P6 (hand on knob) and P7 (open cupboard)",
    ]
    credit_pages(src, 13)
    write_record(rec)


# ------------------------------------------------------------------ 14
def r14():
    import p14_double_take as P
    import p07_two_panels as P7P
    P7P.PLATE_LAID.clear()
    P.build()
    c, rec, sc = base(14, "double-take")
    src = ["99-ways-template:anrc-gold-key-1922", "99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"]
    rec.update({
        "build": "films/swarm/99-ways/build/p14_double_take.py (the plate: build/p07_two_panels.py; brush: build/brushkit.py; figures: build/b1m2.py)",
        "sources": src,
        "made": [
            "the ONE HANDMADE brush plate of the office made for page 07 (dab-chain brush after the moins-dun-quart-de-seconde-pour-vivre plate method), printed again unchanged in all nine panels and framed by camera crops; plate ink sha256 " + P7P.plate_hash(),
            "brushed figures from the b1m2 model; a head-turn rig made here (the head of a right-facing figure pinned at the neck of a left-facing body) for the glance, the look away and the snap back",
            "brushed whip lines round the snapping head (P5); brushed swoosh arcs tracing the cupboard leaf's swing (P7)",
            "a pasted paper overlay opening the cupboard on its left jamb, the leaf at 250 px for the near miss and 112 px at rest; the ANRC 1922 key printed in ink on its hook with a SERVICE tag",
            "timing slips in the pen hand ('a glance...', 'away...', 'and back!', 'whoosh... missed!', 'beat.'), brushed balloons with the four canon lines; folio by pen99.folio",
        ],
        "events": {"E0": "P1 seated at the desk behind the memo slip ('4:15 - open SERVICE door. Key in cupboard.'); P2 he is up and walking toward the cupboard",
                   "E1": "P2 the stranger at the TICKET OFFICE window, question balloon; he looks back over his shoulder",
                   "E2": "P3 a glance up at the clock; P4 head back to the window; P5 head snaps back to the clock (the double take, whip lines) and the answer; the clock reads 4:10 in every crop",
                   "E3": "P6 she turns away, thanks balloon into the window",
                   "E4": "P7 he pulls the cupboard open; the leaf swings out and stops a whisker from his nose, he leans back, no fall (the near miss); key on its hook; P8 held beat on the key",
                   "E5": "P9 in the open doorway, pencil to his chin, the forgetting line; key unmoved; SERVICE door closed"},
        "lines": LINES,
        "beat": "row 2: the head is away from the clock, then snaps back to it with whip lines, then the answer is laid; row 3: the cupboard leaf swings out toward his nose and he leans back",
        "beat_frames": ["b01: P5 head still away from the clock (no answer), cupboard closed in P7",
                        "b02: P5 head snapped back to the clock with whip lines", "b03: + answer balloon",
                        "b04: P7 leaf half out (120 px), he begins to lean", "b05: leaf full out, a whisker from his nose, swoosh lines",
                        "b06: + forgetting balloon in P9 (the finished page)"],
    })
    sc.update({"panels": 9, "plate_prints": len(P7P.PLATE_LAID), "plate_prints_identical": len(set(P7P.PLATE_LAID)) == 1,
               "double_take": "P3 head to the clock (tilt -20), P4 head back to the window, P5 head to the clock again (tilt -30) with whip lines: two head turns to the clock in consecutive takes",
               "near_miss_gap_px_plate": 34, "balloon_cap_px": [46, 50],
               "check": c["check"] + " -> row 2 shows the turn to the clock, the look away and the snap back (maker's judgement from the full-size page; blind reading pending)",
               "evidence": "measured (plate hash, size) and perceptually judged (from frames) by the maker; independent readers not yet run"})
    rec["self_check"] = sc
    rec["weaknesses"] = [
        "the check asks for two consecutive head turns to the clock; the page puts a look-away panel between them (glance, away, back), which is the classic double take but a strict reader may count panels differently",
        "the near miss reads as 'leaning back from the swinging door' rather than a sharp gag; the stopped leaf and his face overlap in silhouette scale",
        "the plate is page 07's plate, so the set is identical to page 07 by design (one repeated plate); the page differs by camera crops and timing",
        "P1 crops the clock's pendulum oddly at the top edge",
    ]
    credit_pages(src, 14)
    write_record(rec)


# ------------------------------------------------------------------ 15
def r15():
    import p15_lightbox as P
    c, rec, sc = base(15, "lightbox")
    src = ["99-ways-template:anrc-gold-key-1922", "99-ways:handmade"]
    rec.update({
        "build": "films/swarm/99-ways/build/p15_lightbox.py",
        "sources": src,
        "made": [
            "a lightbox rendered as transmitted light: lamp-lit glass, then six translucent animation sheets laid in order; each sheet has its own transmittance (0.52), room-light reflection (0.41) and a scatter blur (2.2 px) of everything beneath it, so each earlier beat shows through every later sheet that overlaps it, softer and fainter",
            "HANDMADE sheet paper: cloud and fibre texture generated per sheet (method after the 99-ways-subjective lightbox sheet), three punched peg holes that let the bare light through, tape strips at the top corners, sheet numbers 1-6 in the pen hand",
            "first-person cut-paper hands (black paper, opaque on the box): back of the hand, four fingers and thumb with per-finger curl, forearm out of the bottom of the field; the pencil cut as a tapered strip",
            "the set pen-drawn on each sheet in the shared pen line (desk edge and inkwell, ticket window with TICKET OFFICE, clock at 4:10 with pendulum case, cupboard with its leaf swung on the left jamb, SERVICE door)",
            "the stranger cut from grey tissue behind the window (half transparent); balloons, the memo slip and the SERVICE tags are glued slips of heavier bond, which block more light and read greyer",
            "the ANRC 1922 key cutout (99-ways-template piece) glued down as an opaque piece on its pen hook",
            "folio by pen99.folio on the glass",
        ],
        "events": {"E0": "sheet 1: his hands at the desk, the memo slip ('4:15 - open SERVICE door. Key in cupboard.'), pencil in his right hand",
                   "E1": "sheet 2: the stranger in grey tissue behind the TICKET OFFICE window; question balloon; his pencil hand at the edge",
                   "E2": "sheet 3: the clock at 4:10 filling his view; the answer balloon with its tail running off the bottom (his own voice)",
                   "E3": "sheet 4: the window, her shoulder leaving at its right jamb; thanks balloon",
                   "E4": "sheet 5: his left hand on the swung leaf; the cupboard open, the key on its hook, tag SERVICE",
                   "E5": "sheet 6: the key still on its hook, the SERVICE door shut at the right, his pencil hand rising toward his chin; the forgetting balloon from below"},
        "lines": LINES,
        "beat": "the sheets are laid on the lightbox one at a time; with each new sheet the earlier beats sink under it and fade",
        "beat_frames": [f"b0{k}: {k} sheet(s) on the box" for k in range(1, 7)],
    })
    sc.update({"sheets": 6, "optics": {"T_sheet": P.T_SHEET, "R_sheet": P.R_SHEET, "scatter_px": P.SCATTER,
                                       "contrast_of_ink_under_n_sheets": {str(n): round(((1 * P.T_SHEET ** n) - (0.06 * P.T_SHEET ** n)) / 1.0, 3) for n in range(0, 4)}},
               "balloon_cap_px": 50,
               "check": c["check"] + " -> sheet 1's hands show through sheet 3, sheet 3's balloon tail and sheet 5's hand show through sheets 5 and 6, sheet 2's window lines through sheet 4 (maker's judgement from the full-size page; blind reading pending)",
               "evidence": "measured (optics parameters, size) and perceptually judged (from frames) by the maker; independent readers not yet run"})
    rec["self_check"] = sc
    rec["weaknesses"] = [
        "first person: the agent is never seen, only his hands; that is the paper-hands medium, but a reader must infer who 'I' is from the memo and the pencil",
        "the fading is by overlap only: where a sheet is not covered it is seen at full strength, so 'fading' shows in the overlaps, not as a uniform dimming of older sheets",
        "the hands are simple cut shapes; at phone width they read as hands but not as specifically his (no sleeve or waistcoat)",
        "sheets 5 and 6 repeat the same cupboard; the change (hand on leaf -> pencil rising, SERVICE door entering) is small",
    ]
    credit_pages(src, 15)
    write_record(rec)


if __name__ == "__main__":
    which = sys.argv[1:] or ["13", "14", "15"]
    for w in which:
        {"13": r13, "14": r14, "15": r15}[w]()
        print("record", w)

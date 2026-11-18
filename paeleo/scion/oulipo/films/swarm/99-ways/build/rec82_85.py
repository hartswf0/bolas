"""Records and credit page-lists for pages 82-85 (batch 8, page maker 2). Run after the four builds.
Measures each output (size, bytes, beats) and writes films/swarm/99-ways/pages/NN.json."""
import json
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import b1m2 as B  # noqa: E402

ROOT = B.ROOT
CANON = json.load(open(ROOT / "films/swarm/99-ways/canon.json"))
CON = {c["id"]: c for c in CANON["constraints"]}
LINES = {k: v["text"] for k, v in CANON["incident"]["lines"].items()}


def measure(n, pid):
    jp = ROOT / f"assets/pages/99-ways/{n:02d}-{pid}.jpg"
    ms = ROOT / f"films/sources/99-ways/masters/{n:02d}-{pid}.png"
    bd = ROOT / f"films/sources/99-ways/beats/{n:02d}"
    beats = sorted(bd.glob("b*.png"))
    sz = Image.open(jp).size
    return dict(size_px=list(sz), jpeg_bytes=jp.stat().st_size, jpeg_quality=90,
                in_target_0_4_1_2MB=400000 <= jp.stat().st_size <= 1200000, master_exists=ms.exists(),
                beat_frames=len(beats), beat_size=list(Image.open(beats[0]).size) if beats else None)


PAGES = {
    82: dict(
        id="nine-cells", title="Nine cells", medium="shadow-puppet",
        build="films/swarm/99-ways/build/p82_nine_cells.py (figure model and set pieces: build/b1m2.py; screen and puppet tools: build/p05_noir.py, layout grammar after build/p30_jump_cuts.py)",
        sources=["99-ways-template:anrc-gold-key-1922", "99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"],
        made=["a strict 3x3 grid of nine identical cells, each 640 x 853 px, 30 px gutters, ruled in one pen border pass (frame_border)",
              "black cut-paper silhouette puppets (b1m2 agent, stranger held soft and grey behind the glass) and cut set pieces (desk, lamp, clock, ticket window with TICKET OFFICE cut through its header, cupboard, SERVICE door) on lamp-lit paper screens carrying the LoC 1934 sheet fibre",
              "the ANRC 1922 key cutout as an amber gel on its hook with a SERVICE card tag (cells 8, 9)",
              "the memo slip and the four canon lines in the shared pen hand (penlib cut-paper balloons); folio by pen99.folio"],
        cells={"1": "E0 seated at the desk, the memo slip '4:15 - open SERVICE door. Key in cupboard.'; clock at 4:09",
               "2": "E0 on his way across the office toward the closed cupboard",
               "3": "E1 the question from the ticket window",
               "4": "E2 held pause: he looks up at the wall clock, 4:10 (silent)",
               "5": "E2 the answer",
               "6": "E3 the thanks; she turns from the glass",
               "7": "E3 held pause: the window empty, he strides on toward the cupboard (silent)",
               "8": "E4 the cupboard open, the key on its hook, tag SERVICE",
               "9": "E5 pencil to chin, the forgetting line; key on its hook; SERVICE door shut with its card"},
        beat="the grid is ruled empty, then the cells fill in reading order, one beat or held pause at a time",
        beat_frames=["b01: the empty 3x3 grid", "b02: cell 1", "b03: cells 1-2", "b04: cells 1-3 (the question)",
                     "b05: cells 1-5 (the pause and the answer)", "b06: cells 1-6", "b07: cells 1-8 (the cupboard opens)",
                     "b08: all nine (the forgetting)"],
        check="measured: nine boxes, all 640 x 853 px (set of sizes has one member); perceptually judged by the maker at full size",
        weaknesses=["the cells are narrow (640 px): the window in cell 5 is cut at the left edge and its TICKET OFFICE header reads only 'OFFICE'",
                    "cells 2 and 7 are near rhymes (walking right past a closed cupboard), which is what a held pause asks for but reads a little repetitive",
                    "the 'T' of 'Ten' sits tight on the balloon outline (the shared pen hand's T is wide)",
                    "the SERVICE door in cell 9 is cut by the right border (its card fully legible)"]),
    83: dict(
        id="clocks-eye", title="The clock's eye", medium="engraving-puppet",
        build="films/swarm/99-ways/build/p83_clocks_eye.py (engraving puppets and pen set: kit/build_page03.py, build/p49_epic.py)",
        sources=["99-ways:loc-harpers-1863-army-telegraph-operator", "99-ways:loc-1867-dickens-tickets-steinway",
                 "99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"],
        made=["one fixed camera at the clock's face (3.1 m up the near wall, centre, pitched 33 deg down, focal 640 px) through which every board is projected: a model office built of standing cards (the far wall card with window, cupboard and SERVICE door; the desk front; the agent puppet) each mapped by its own true perspective homography, plus flat cards (the desk top with the memo, inkwell and pen, seen from above) and pen-ruled floorboards converging away from the clock",
              "page 03/49's ENGRAVING PUPPETS reused: the AGENT is the Harper's Weekly 1863 telegraph operator (LoC cph.3c11072) pinned at the joints, re-posed per board (rising, turning, head tipped back up at the clock in board 3, arm out to the cupboard, pencil to chin); the STRANGER the hatted woman of the 1867 Steinway Hall engraving (LoC cph.3c32079), seen only through the 1863 plate's window glass; his table from the 1863 plate as the desk front",
              "the clock's own minute hand: a HANDMADE black cut card with a pierced spade tip and a brass boss, seen from behind the dial (so it turns the other way), its pivot below each board's bottom border where the clock is, edging up across the border into the view; a short hour-hand stub below; it creeps 4:09:05 -> 4:11:20 from board to board, the time pencilled under each board",
              "a soft floor shadow under the agent; the four canon lines verbatim in cut-paper balloons; folio by pen99.folio"],
        events={"E0": "board 1: at the desk, the memo seen from above, he rises and turns for the cupboard",
                "E1": "board 2: halfway across the floor; question balloon from the window",
                "E2": "board 3: he looks up at the clock, i.e. at us; answer balloon",
                "E3": "board 4: thanks balloon; she has turned from the glass",
                "E4": "board 5: at the cupboard, its door open on the left jamb, the key on its hook with its SERVICE tag",
                "E5": "board 6: pencil to chin before the open cupboard, forgetting balloon; the SERVICE door shut"},
        beat="the fixed eye: the empty office from the clock (all six boards), then the agent and the lines appear board by board in the same unmoving view while the clock's hand creeps at the bottom border",
        beat_frames=["b01: six boards, the empty room from the clock, the hand at each border", "b02: board 1 peopled",
                     "b03: board 2, the question", "b04: board 3, he looks up at the clock: the answer",
                     "b05: board 4, the thanks", "b06: board 5, the cupboard opened", "b07: board 6, the forgetting"],
        check="structural: every board uses the same camera and set (identical background); perceptually judged by the maker at full size: the far wall's top is cut off, the floor and desk top are seen from above and the hand enters from the border below, so the eye is high on the wall",
        weaknesses=["the engraving puppet is a side view printed flat, so he stands as a card in the model room: the downward view is carried by the floor, desk top and wall cut-off rather than by the figure's own foreshortening",
                    "much of each board is empty floor (the honest cost of the clock's height); the agent is only 230-300 px tall",
                    "the desk is cut by the left border; the stranger behind the glass is faint and small",
                    "the minute hand moves only 14 degrees across the page, so its creep reads only on close comparison (the pencilled times carry it)",
                    "the pencil at the chin in board 6 is tiny at this scale"]),
    84: dict(
        id="thirty-years-on", title="Thirty years on", medium="charcoal-card",
        build="films/swarm/99-ways/build/p84_thirty_years_on.py (card kit: build/charcoal99.py; figure model build/b1m2.py; key card build/p31_sounds_only.py; written() from build/p77_the_cupboard.py)",
        sources=["teuf-teuf:cueva-de-las-manos", "99-ways-template:anrc-gold-key-1922", "99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"],
        made=["seven boards of the same office in 1967, built in dark charcoal card pieces (charcoal99.pin_up) on the teuf-teuf rock-wall ground (Cueva de las manos, CC BY-SA 3.0, printed through the teuf-teuf ramp): the ticket window boarded with four nailed planks (brads), its glass grimed; the desk under a draped dust sheet; the wall clock stopped at 11:52; a SEPTEMBER 1967 calendar card (board 1); charcoal cobwebs in the corners and over the cupboard; the cupboard door hanging open with the brass key (the ANRC 1922 cutout cut as a card, dulled with dust) still on its hook; the SERVICE door shut, its card faded",
              "the 1937 beats as PALE figures: the same b1m2 card puppets (agent, stranger) and the 1937 state of things (the memo slip, the cupboard door closed in E0-E3 and swinging open in E4, the clock's 4:10 hands over the stopped ones) cut in near-white chalk card, laid three-quarters transparent with a chalk outline, so the 1967 room shows through them",
              "captions as bone-on-black slips naming the year; the four canon lines verbatim in pale cut-paper balloons; folio by pen99.folio"],
        events={"E0": "board 2 (1937): the pale memo on the sheeted desk; he gets up",
                "E1": "board 3 (1937): the pale lady at the boarded window; question",
                "E2": "board 4: the clock stopped at 11:52, its pale 1937 hands at 4:10; he looks up; answer",
                "E3": "board 5 (1937): thanks; she turns from the glass",
                "E4": "board 6 (1937): the pale cupboard door swings open; the key hangs there (the same key, solid, in 1967)",
                "E5": "board 7: pale agent, pencil to chin, forgetting line; caption '1967: the key is still on its hook. The SERVICE door is still closed.'"},
        frame="board 1: the empty office, September 1967 (declared: frames the incident in 1967)",
        beat="the 1967 room stays; the pale 1937 figures arrive in it board by board",
        beat_frames=["b01: all seven boards in 1967, empty", "b02: E0 ghost", "b03: E1", "b04: E2", "b05: E3", "b06: E4", "b07: E5 (= the page)"],
        check="perceptually judged by the maker at full size: the 1967 things are dark solid cards, the 1937 figures pale and see-through, the captions name each year; the key is the solid dusty card on its hook in every board, seen through the pale closed door in boards 2-5",
        weaknesses=["the cupboard door hangs open in 1967, an assumption (the canon does not say whether he shut it); declared here so the key can be seen in both times",
                    "the pale stranger behind the planks is a chalky blob of hat and coat, not a face",
                    "in board 4 the answer balloon covers the ghost stranger and the TICKET OFFICE header",
                    "captions carry part of the time distinction (the years are written); a reader without them still has dust, boards and calendar vs pale figures",
                    "the small boards crowd window, desk, clock, cupboard and SERVICE door into 960 px; the SERVICE door is narrow"]),
    85: dict(
        id="form-99", title="Form 99", medium="pen-hand",
        build="films/swarm/99-ways/build/p85_form_99.py (pen tools: kit/pen99.py -> 99-ways-template page/penlib.py; b1m2 letter/wrap helpers)",
        sources=["99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"],
        made=["the whole page is one invented railway form, 'FORM 99 / REPORT OF IRREGULARITY AT STATION' (no real railway's name or form): printed heading and instructions, a double rule, 15 numbered fields in boxes with ruled writing lines and YES/NO tick boxes, all 'printed' in blue-black ink with straight rules and the shared pen hand's capitals",
              "every answer written in by the agent in pencil: the same shared pen hand in graphite, grain-broken, slightly tilted and jittered per line, one struck-out false start ('Key was') in field 11, pencil crosses in the NO boxes of 9 (key removed) and 10 (SERVICE door opened), a scrawled signature and 'Agent, Randolph'",
              "field 12 STATEMENTS OF PERSONS PRESENT quotes the four canon lines verbatim, each with its speaker",
              "field 13, the form's own SKETCH OF SCENE box: his pencil plan of the office (walls, ticket window with the lady as an X outside, the clock 'clock (4:10)', the desk, the cupboard open on the right wall with the key on its hook, the SERVICE door 'shut', his dotted path numbered 1 got up, 2 asked the time, 3 here, and ?)",
              "field 15 REMARKS OF SUPERINTENDENT left blank '(Not to be filled in by agent)'; all on the LoC 1934 sheet; folio by pen99.folio"],
        events={"E0": "fields 4 (the memo quoted) and 5 (got up about 4:09, started across to the cupboard)",
                "E1": "field 6 (a lady at the ticket window asked the time); field 12 line 1",
                "E2": "field 7 (looked at the office clock, which read 4:10, told her); field 12 line 2",
                "E3": "field 7 (she thanked me and left the window); field 12 line 3",
                "E4": "field 8 (opened the cupboard; brass key on its hook, tagged SERVICE)",
                "E5": "fields 9-11 (key not removed, SERVICE door not opened; 'could not think what I had come for'); field 12 line 4; sketch point 3"},
        substitutions="the four lines are quoted (verbatim) in the statements field rather than spoken in balloons, as declared",
        beat="the form is filled in pencil field by field: the blank printed form, then the heading answers, the narrative fields, the tick boxes and the crossing-out, the statements, the sketch, the signature",
        beat_frames=["b01: the blank printed form", "b02: fields 1-5", "b03: fields 6-7", "b04: field 8", "b05: fields 9-11 (ticks, crossing-out)",
                     "b06: field 12 statements", "b07: field 13 sketch", "b08: field 14 signature (= the page)"],
        check="perceptually judged by the maker at full size: printed field names (ink, capitals, numbered) and pencil answers carrying E0-E5 in order are distinct in colour and hand; the sketch box is labelled by the form",
        weaknesses=["printed and pencil text share the one pen hand (by the book's rule); the difference is carried by ink colour, capitals, ruling and grain, not by a typeface",
                    "the date is left as 'Sept. 1937, afternoon' because the canon gives no day",
                    "the right-hand remarks column below field 15 is mostly empty paper",
                    "the pencil grey is light at phone width for the smaller sketch labels (cap 24-26)"]),
}


def main():
    for n, p in PAGES.items():
        c = CON[p["id"]]
        m = measure(n, p["id"])
        rec = {"n": n, "id": p["id"], "title": p["title"], "family": c["family"], "medium": p["medium"],
               "canon_revision": CANON.get("revision", "c1"), "rule": c["rule"], "declares": c.get("declares"),
               "file": f"assets/pages/99-ways/{n:02d}-{p['id']}.jpg",
               "master": f"films/sources/99-ways/masters/{n:02d}-{p['id']}.png",
               "beats_dir": f"films/sources/99-ways/beats/{n:02d}", "build": p["build"], "sources": p["sources"],
               "lines": LINES, "made": p["made"]}
        for k in ("cells", "events", "frame", "substitutions"):
            if k in p:
                rec[k] = p[k]
        rec.setdefault("substitutions", "none: the four lines verbatim")
        rec["beat"] = p["beat"]
        rec["beat_frames"] = p["beat_frames"]
        rec["self_check"] = dict(m, check=c["check"] + " -- " + p["check"],
                                 pending="independent blind reading not run by the maker")
        rec["weaknesses"] = p["weaknesses"]
        assert m["size_px"] == [2200, 2850] and m["beat_size"] == [960, 1242] and 4 <= m["beat_frames"] <= 8, (n, m)
        B.write_record(rec)
        B.credit_pages(p["sources"], n)
        print(n, m)


if __name__ == "__main__":
    main()

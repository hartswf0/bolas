"""Record and credits for page 12 (Loop). Run after p12_loop.py."""
import json
import sys

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
from b1m2 import *  # noqa
from rec13_15 import base, LINES

META = json.load(open(ROOT / "films" / "sources" / "99-ways" / "forage" / "p12-daumier" / "meta.json"))


def entry(cid, fn, short, used_as):
    m = META[fn]
    return {"id": cid, "title": m["title"].replace("File:", "") + f" ({short})", "author": "Honoré Daumier (lithograph); Rijksmuseum, Amsterdam (scan)",
            "license": m["license"], "license_url": m["license_url"], "usage_terms": m["usage_terms"],
            "source_url": m["description_url"], "file_url": m["original_url"], "date": m["date"],
            "licence_checked": m["licence_checked"], "local_file": f"films/sources/99-ways/forage/p12-daumier/{fn}",
            "local_sha256": m["local_sha256"], "used_as": used_as, "pages": []}


NEW = [
    entry("99-ways:daumier-proprietaire-1846", "d1.jpg", "'Il est devenu pro-pri-e-taire !', Les bons bourgeois no. 18, 1846, Delteil 1494",
          "page 12: the station agent (the bourgeois, head and body cut apart so the head can tilt); the CONCIERGE door's upper half as the SERVICE door; the stairwell wall and floor tone as every panel's ground"),
    entry("99-ways:daumier-premier-voyage-1846", "c4.jpg", "'Un premier voyage en chemin de fer', Les beaux jours de la vie no. 90, 1846",
          "page 12: the stranger (the old woman in her bonnet); the carriage window as the ticket window; the carriage wall tone for the desk, counter and cupboard body; the window's pale paper for the clock dial and cupboard leaf"),
    entry("99-ways:daumier-grand-tunnel-1843", "c3.jpg", "'L'entree du grand tunnel d'un chemin de fer', Les chemins de fer no. 16, 1843",
          "page 12: the tunnel's black crayon tone, cut for the cupboard's dark inside, the clock case, the sill and the pencil"),
]


def r12():
    import p12_loop as P
    c, rec, sc = base(12, "loop")
    src = [e["id"] for e in NEW] + ["99-ways-template:anrc-gold-key-1922", "99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"]
    rec.update({
        "build": "films/swarm/99-ways/build/p12_loop.py (collage kit: build/daumier12.py; forage record: films/sources/99-ways/forage/p12-daumier/meta.json)",
        "sources": src,
        "made": [
            "FORAGED: three Daumier lithographs (CC0, Rijksmuseum via Commons; licence read from the Commons API extmetadata 2026-11-17), 1280 px renders, levelled once per print (red-filter luminance to drop the newsprint foxing, black/white points, a 0.8 px softening of the newsprint speckle; no threshold or posterize)",
            "HANDMADE cuts: hand-placed scissor polygons for the agent's head and body (cut apart at the collar so the head tilts: down to the memo, up to the clock), the woman, the window and the door; set pieces (desk, counter, cupboard and leaf, clock ring, dial and case, pencil) cut out of the prints' own crayon tone; every piece glued with a narrow paper rim and cast shadow on the LoC 1934 sheet",
            "the ANRC 1922 key cutout (99-ways-template piece) glued in the cupboard, warmed to brass, with a SERVICE tag slip",
            "the loop: eight panels in a ring round the memo, read clockwise from the top left; pen arrows in the gutters; the seam arrow from P8 (back to the desk) up into P1 (the memo again) drawn heavier; a ring of arrows and 'round and round' round the central memo",
            "pen-hand clock numerals and hands at 4:10, captions, the four canon lines in cut-paper balloons, the TICKET OFFICE and SERVICE slips; folio by pen99.folio",
        ],
        "events": {"E0": "P1 at his desk, the memo again ('4:15 - open SERVICE door. Key in cupboard.'), head bent to it; P2 he sets off for the key; the memo also sits large at the centre of the ring",
                   "E1": "P3 the woman behind the TICKET OFFICE window; question balloon",
                   "E2": "P4 head tilted up to the clock at 4:10; answer balloon",
                   "E3": "P5 she turns away from the window; thanks balloon",
                   "E4": "P6 the cupboard open, the key on its hook",
                   "E5": "P7 hands at his chin, the forgetting line; the key still on its hook, the SERVICE door shut",
                   "loop seam (declared)": "P8 he walks back to his desk; the arrow runs from P8 up into P1, where he reads the memo and sets off again"},
        "lines": LINES,
        "beat": "the loop seam: in P8 he walks back to the desk (three positions), the heavy seam arrow appears from P8 into P1, and in P1 his head bends to the memo again",
        "beat_frames": ["b01: P8 he turns back, P1 head level, no seam arrow", "b02: P8 halfway to the desk", "b03: P8 at the desk",
                        "b04: the seam arrow P8 -> P1 is drawn", "b05: P1 his head bends to the memo", "b06: the finished page"],
    })
    sc.update({"panels": 8, "layout": "3x3 ring, centre cell the memo; reading clockwise from top left; P8 at middle left leads up into P1",
               "check": c["check"] + " -> P8's caption 'And back he goes to his desk...' and the heavy arrow lead straight into P1's 'The memo again...' (maker's judgement from the full-size page; blind reading pending)",
               "evidence": "measured (size) and perceptually judged (from frames) by the maker; independent readers not yet run"})
    rec["self_check"] = sc
    rec["weaknesses"] = [
        "the agent is a Daumier bourgeois in a top hat and tail-coat (waistcoat kept, shirt-sleeves not); the hat indoors is the price of a print whose figure stands whole",
        "the agent is the same cut-out in every panel (only head tilt, flip and position change): his walk is a glide, not a stride",
        "the pencil in P7 has no hand holding it (the Daumier body's arms hang at his sides); it reads as a pencil raised to the chin",
        "the panel grounds are one stretched patch of the stairwell wall and floor, softened to keep the JPEG under 1.2 MB; they read as tone, not as a station office",
        "the clock is built (tone ring, pale dial, pen hands) rather than found: no Daumier clock was in the three prints",
    ]
    credit_pages(src, 12, new_entries=NEW)
    write_record(rec)


if __name__ == "__main__":
    r12()
    print("record 12")

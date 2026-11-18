"""Records for pages 89-92 (batch 9, page maker 1). Run: python3 -I rec89_92.py NN"""
import json, sys
from pathlib import Path
from PIL import Image
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
from b1m2 import ROOT, write_record, credit_pages

LINES = {"question": "Pardon me — have you the right time?", "answer": "Ten past four, by the clock.",
         "thanks": "Much obliged!", "forgetting": "Well, here I am... and what for?"}
CANON = json.load(open(ROOT / "films/swarm/99-ways/canon.json"))


def canon_row(n):
    for p in CANON["constraints"]:
        if p.get("n") == n:
            return p
    return {}


def finish(rec):
    n, pid = rec["n"], rec["id"]
    jp = ROOT / f"assets/pages/99-ways/{n:02d}-{pid}.jpg"
    ms = ROOT / f"films/sources/99-ways/masters/{n:02d}-{pid}.png"
    bd = ROOT / f"films/sources/99-ways/beats/{n:02d}"
    beats = sorted(bd.glob("b*.png"))
    sz = Image.open(jp).size
    row = canon_row(n)
    rec["family"] = rec.get("family") or row.get("family")
    rec["declares"] = rec.get("declares") or row.get("declares")
    rec["canon_revision"] = "c1"
    rec["file"] = str(jp.relative_to(ROOT))
    rec["master"] = str(ms.relative_to(ROOT))
    rec["beats_dir"] = str(bd.relative_to(ROOT))
    rec.setdefault("lines", LINES)
    sc = rec.setdefault("self_check", {})
    sc.update({"size_px": list(sz), "jpeg_bytes": jp.stat().st_size, "jpeg_quality": 90,
               "in_target_0_4_1_2MB": 400000 <= jp.stat().st_size <= 1200000, "master_exists": ms.exists(),
               "beat_frames": len(beats), "beat_size": list(Image.open(beats[0]).size) if beats else None})
    sc.setdefault("pending", "independent blind reading not run by the maker")
    write_record(rec)
    credit_pages(rec["sources"], n, rec.pop("_new_credits", ()))
    print(json.dumps(sc))


RECS = {}
RECS[89] = dict(
    n=89, id="crossing-routes", title="Crossing routes", medium="shadow-puppet",
    rule="A 3x3 grid read across tells the agent's story and read down tells the stranger's; both meet in the centre cell at the question.",
    build="films/swarm/99-ways/build/p89_crossing_routes.py (figure model and set pieces: build/b1m2.py; screen and puppet tools: build/p05_noir.py; grid after build/p82_nine_cells.py)",
    sources=["99-ways-template:anrc-gold-key-1922", "99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"],
    made=[
        "a 3x3 grid; each off-centre cell is two shadow screens ruled in the pen border: an upper lamp-lit OFFICE screen (his route) and a lower daylight-cool PLATFORM screen (her route); the centre cell is ONE screen, warm on the office side and cool on the platform side, the cross-section of the ticket window where both stand",
        "numbered tags: warm tags 1-9 at the top-left of his screens run row by row (row-major); cool tags 1-9 at the bottom-left of her screens run column by column (column-major); the centre is 5 both ways; cut arrowheads sit in the gutters (right-pointing in his rows, down-pointing in her columns)",
        "a two-line legend in the pen hand: 'Read ACROSS, the lamp-lit screens: his route, 1 to 9. / Read DOWN, the daylight screens: her route, 1 to 9. They cross at 5.'",
        "black cut-paper puppets: the b1m2 agent, and a NEW full-length stranger platform puppet (long coat, legs, shoes, sleeve, valise, wrist-watch arm, gloved rapping arm) built on the b1m2 head/hat; cut set pieces: desk, lamp, memo slip, clock (4:09, then 4:10), ticket window from both sides (TICKET OFFICE cut through the header), cupboard, SERVICE door with its card, platform deck, RANDOLPH board, bench",
        "the ANRC 1922 key cutout on its hook with a SERVICE tag (his 8 and 9); the other person seen grey and soft beyond the glass (far puppets, clipped to the pane)",
        "the four lines in pen-hand cut-paper balloons; folio by pen99.folio",
    ],
    routes={
        "his (across)": "1 desk + memo (E0) | 2 rises, sets off (E0) | 3 toward cupboard and SERVICE door (E0) | 4 a rap at the glass, he turns (E1 cue) | 5 QUESTION (E1) | 6 reads the clock 4:10, answer (E2) | 7 'Much obliged!' from the glass (E3) | 8 cupboard open, key on hook (E4) | 9 pencil to chin, forgetting line; key on hook, SERVICE door shut (E5)",
        "hers (down)": "1 arrives along the platform with her valise | 2 sets the valise down, looks at her wristwatch | 3 walks up to the ticket window | 4 raps at the glass (he grey beyond) | 5 QUESTION | 6 hears the answer through the glass, sets her watch | 7 'Much obliged!' | 8 walks away along the platform | 9 waits by the bench under the RANDOLPH board",
    },
    substitutions="none: the four lines verbatim; the answer and the thanks appear once in each route (his screen and hers), the question once, in the shared centre",
    additions="the stranger's platform actions (arrival with a valise, a glance at her wristwatch, setting it by the answer, waiting by a bench) -- her route needs nine beats; none changes E0-E5 or the outcome",
    beat="the two routes fill the grid: his screens row by row, then hers column by column, meeting at the centre",
    beat_frames=["b01: the ruled empty grid and legend", "b02: his 1-4 (row 1 and the first of row 2)",
                 "b03: her 1-4 added (column 1 and the top of column 2)", "b04: the centre: both at the window, the question",
                 "b05: his 6-9 (answer, thanks, cupboard, forgetting)", "b06: her 6-9 (= the page)"],
    self_check={"check": "Rows and columns each make sense; the centre cell is the question. -- by construction: the warm tags read 1-9 row-major, the cool tags 1-9 column-major, and cell (row 2, col 2) is index 5 in both orders and carries the question balloon; perceptually judged by the maker at full size"},
    weaknesses=[
        "each off-centre cell holds two different moments (his beat above, hers below), so a cell is not one instant; the screens' colour and the tags carry the reading, and a reader who ignores them may read (row 1, col 3) as her thanks during his walk",
        "her route adds small invented platform business (valise, wristwatch, bench) to fill nine beats",
        "the centre cross-section is a narrow wall with a thin glass strip; it reads as a counter between two people more than as a glazed window",
        "the screens are shallow (452 and 345 px): the figures are small and the far puppets behind the glass are faint grey blobs",
        "the stranger puppet is a new simple profile (bell coat, stick legs); her face is a hat-and-nose silhouette",
    ],
)

LCG_NOTE = ("Local copy films/sources/les-caids-de-la-gaudriole/busch/{f} is a resized derivative of the Commons original; "
            "Commons extmetadata (License pd, Copyrighted False) re-read by the les-caids editor 2026-11-17, saved in "
            "films/sources/les-caids-de-la-gaudriole/editor/extmeta-1.json / extmeta-2.json")
NEW_BUSCH = [
    {"id": "les-caids-de-la-gaudriole:busch-mm-001", "title": "File:Max und Moritz (Busch) 001.png",
     "author": "Wilhelm Busch (1832-1908)", "license": "Public domain",
     "license_url": "https://commons.wikimedia.org/wiki/Commons:Public_domain",
     "source_url": "https://commons.wikimedia.org/wiki/File:Max_und_Moritz_(Busch)_001.png",
     "file_url": "https://upload.wikimedia.org/wikipedia/commons/d/dd/Max_und_Moritz_%28Busch%29_001.png",
     "note": LCG_NOTE.format(f="mm_001.png") + "; the cut part used is films/sources/les-caids-de-la-gaudriole/panel-artist/parts/boys.png",
     "carried_from": "films/credits/les-caids-de-la-gaudriole.json",
     "used_as_99_ways": "page 90: the two boys (Max and Moritz) as crowd: behind the waiting-room bench, on the platform, at the coach windows"},
    {"id": "les-caids-de-la-gaudriole:busch-mm-082", "title": "File:Max und Moritz (Busch) 082.png",
     "author": "Wilhelm Busch (1832-1908)", "license": "Public domain",
     "license_url": "https://commons.wikimedia.org/wiki/Commons:Public_domain",
     "source_url": "https://commons.wikimedia.org/wiki/File:Max_und_Moritz_(Busch)_082.png",
     "file_url": "https://upload.wikimedia.org/wikipedia/commons/9/9f/Max_und_Moritz_%28Busch%29_082.png",
     "note": LCG_NOTE.format(f="mm_082.png") + "; the cut parts used are panel-artist/parts/miller.body.png, miller.arm.png, miller.hand.png",
     "carried_from": "films/credits/les-caids-de-la-gaudriole.json",
     "used_as_99_ways": "page 90: the miller with his sack as platform crowd (three times, one mirrored)"},
]

RECS[90] = dict(
    n=90, id="find-the-key", title="Find the key", medium="busch-fold",
    rule="One crowded panel of the station afternoon; a legend asks the reader to find the six beats in order.",
    build="films/swarm/99-ways/build/p90_find_the_key.py (busch-fold kit: build/p11_station_cat.py, build/p39_meanwhile.py, build/p69_picture_sheet.py)",
    sources=["les-caids-de-la-gaudriole:busch-mm-031", "99-ways:busch-helene-munzel", "les-caids-de-la-gaudriole:busch-mm-016",
             "les-caids-de-la-gaudriole:busch-mm-001", "les-caids-de-la-gaudriole:busch-mm-082",
             "les-caids-de-la-gaudriole:vintage-paper", "les-caids-de-la-gaudriole:wood-table", "99-ways:handmade"],
    _new_credits=NEW_BUSCH,
    made=[
        "a puzzle sheet ('PUZZLE PICTURE No. 90 / FIND THE KEY') printed into the les-caids vintage paper (CC BY 2.0), laid on the les-caids wood table (CC0) with the creases of being sold folded in four (page 69's creases)",
        "ONE picture: Randolph station with its front cut away, HANDMADE ink line in code: RANDOLPH eave board, the office (shelves of parcels and ledgers, pigeonholes, SEPT. 1937 calendar, framed map, NO LOITERING card, hanging lamps, desk, wall clock at 4:10, coat stand, the cupboard open on its left jamb with the brass key on its hook and its SERVICE tag, the shut SERVICE door with its card), the ticket-window wall with TICKET OFFICE board, the waiting room (timetable 'Northbound 4:22 / Southbound 4:48 / White River Jct.', TO TRAINS door, bench), and the platform in front with the 4:22 coach, trunks, hatboxes and a barrow",
        "the agent six times = the les-caids porter cut (Busch 1865, Max und Moritz plate 31, page 39's hand-cut polygon), one per beat; HANDMADE ink pencil to his chin at E5",
        "the stranger twice = Helene (Busch 1872) with page 39's HANDMADE cloche: leaning in at the window (E1), going out toward the trains (E3)",
        "the crowd (cut pieces with white scissor margins): the miller with his sack x3 (plate 82, les-caids parts), the two boys x3 plus two at the coach windows (plate 1, les-caids part), the widow x3 plus three at coach windows (plate 16, page 11's cut), Munzel the cat x2 (Busch 1872, page 11's cut)",
        "the four lines in pen-hand cut-paper balloons; legend 'Somewhere in the crowd the agent's afternoon happens. Find it, in order:' with six numbered beats; the answers printed upside down at the foot; folio by pen99.folio",
    ],
    events={
        "E0": "behind the desk, memo slip on it ('4:15 open / SERVICE door. / Key in cupb'd.'), getting up",
        "E1": "at the ticket window, turned to it; Helene leaning in: 'Pardon me — have you the right time?'",
        "E2": "under the clock (4:10), head up: 'Ten past four, by the clock.'",
        "E3": "Helene going toward the TO TRAINS door: 'Much obliged!'; the agent walking on at the back of the office",
        "E4": "at the open cupboard, the key on its hook, tag SERVICE",
        "E5": "before the shut SERVICE door, pencil to chin: 'Well, here I am... and what for?'; the key stays on its hook",
    },
    substitutions="none: the four lines verbatim",
    additions="passengers on the platform and in the waiting room (the miller, the boys, the widow) and the cat; a timetable, calendar and other wall furniture -- none touches E0-E5 or the outcome",
    beat="the reader finds the beats: a pencil ring is drawn round each of the six, in order, numbered",
    beat_frames=["b01: the puzzle picture", "b02: ring 1 (the desk)", "b03: ring 2 (the window)", "b04: ring 3 (the clock)",
                 "b05: ring 4 (her thanks, him walking on)", "b06: ring 5 (the open cupboard)", "b07: ring 6 (the SERVICE door)"],
    self_check={"check": "A reader finds all six beats in the crowded picture. -- perceptually judged by the maker at full size: the six agent cuts each sit with their beat's object (desk+memo, window+lady, clock, walking on as she leaves, open cupboard+key, SERVICE door+pencil); the four balloons tie the lines to them; the rings in the beat frames mark one solution"},
    weaknesses=[
        "the six agents are the same Busch drawing (the kit has one porter pose), so he is easy to spot once seen and they read partly as a parade; the puzzle's difficulty lies in ordering, not in finding him",
        "the four balloons make E1, E2, E3 and E5 easy to find; only E0 and E4 are true search targets",
        "the crowd stays mostly on the platform band (the canon office holds only the agent), so the office half is busy with objects rather than people",
        "Busch's crowd figures (miller, boys, widow) are 1865 German types, not 1937 Vermont passengers; deliberately so in this medium",
        "the answers line is small (cap 21) and only legible at full size",
    ],
)

RECS[91] = dict(
    n=91, id="polyptych", title="Polyptych", medium="charcoal-card",
    rule="One continuous drawing of the office runs behind all the panels; the borders cut it into moments and the agent recurs in each.",
    build="films/swarm/99-ways/build/p91_polyptych.py (card kit: build/charcoal99.py; figure model build/b1m2.py; key card build/p31_sounds_only.py; written() from build/p77_the_cupboard.py)",
    sources=["teuf-teuf:cueva-de-las-manos", "99-ways-template:anrc-gold-key-1922", "99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"],
    made=[
        "ONE office wall pinned up once at page size in charcoal card pieces (charcoal99.pin_up) on the teuf-teuf rock-wall ground (Cueva de las manos, Suzko, CC BY-SA 3.0, printed through the teuf-teuf ramp): from left to right desk, lamp and memo card; the ticket window with TICKET OFFICE; the wall clock at 4:10; a NOTICES board with pinned cards; the cupboard open on its left jamb with the brass key card (ANRC 1922 key silhouette) on its hook; the SERVICE door shut with its card",
        "things that run on across the gutters so the panels join: the picture rail, a long parcel shelf with its parcels, a long DEPARTURES board ('NORTH 4:22   SOUTH 4:48   LOCAL 5:30') whose words are cut by three gutters, the wainscot boards and the floor band",
        "six tall panels (380, 300, 280, 280, 300, 290 px wide, 30 px gutters) cut out of that one drawing; the LoC 1934 sheet shows in the gutters; pen border by B.frame_border",
        "the agent, the same b1m2 card puppet with brads at shoulder and elbow, pinned into each panel at its moment; the stranger (b1m2 card, paler tones) only in the window panel, behind the glass",
        "the four lines in pen-hand cut-paper balloons, each kept inside its panel (the thanks has its tail running out toward the window panel); folio by pen99.folio",
    ],
    events={"E0": "panel 1: by the desk, the memo card on it, he gets up", "E1": "panel 2: at the ticket window, the lady behind the glass; the question",
            "E2": "panel 3: under the clock (4:10), head up; the answer", "E3": "panel 4: walking on past the notices; 'Much obliged!' from the left (the window panel)",
            "E4": "panel 5: at the open cupboard, the key on its hook", "E5": "panel 6: before the SERVICE door, pencil to chin; the forgetting line"},
    substitutions="none: the four lines verbatim",
    beat="the one drawing of the room appears whole and empty; the gutters cut it into six panels; the agent is pinned into each panel in turn",
    beat_frames=["b01: the whole office wall, one drawing, no gutters", "b02: the gutters cut it into six panels", "b03: E0", "b04: E1", "b05: E2",
                 "b06: E3", "b07: E4", "b08: E5 (= the page)"],
    self_check={"check": "A reader can join the panel backgrounds into one unbroken room. -- by construction: every panel is a crop of one page-size drawing (build: room() once, panels copy their window of it); perceptually: the rail, shelf, DEPARTURES lettering, wainscot and floor line up across every gutter; judged by the maker at full size"},
    weaknesses=[
        "the panels are tall and narrow, so the agent nearly fills their width and is cut by the panel edges in places",
        "the upper half of each panel is wall (rail, shelf, board, lamps); necessary for the continuity, but the figures sit in the lower half",
        "the stranger behind the glass is a dark card bust, small; she reads as a figure at the window more than as a face",
        "the SERVICE door and the cupboard sit in neighbouring narrow panels; the canon's 'beside' holds but both are cropped",
    ],
)

RECS[92] = dict(
    n=92, id="keyhole", title="Through the keyhole", medium="stencil-dye",
    rule="Seen from inside the SERVICE room through its keyhole: every panel is masked by the keyhole shape, and the door never opens.",
    build="films/swarm/99-ways/build/p92_keyhole.py (dye method: build/p08_lipogram.py dye/ties/fig_layers; cut model: build/b1m2.py)",
    sources=["99-ways-template:anrc-gold-key-1922", "99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"],
    made=[
        "six panels, each the inside of the SERVICE door printed from an umber stencil (its paper ties left as thin pale bridges) with a second faint umber pass for the dark of the room, an ochre escutcheon with two umber screws, and a keyhole-shaped opening with a dark cut rim",
        "through the opening, the office in page 08's flat dyes (wash wall, verdigris floor, indigo window and waistcoat, madder clock and coat, ochre desk, skin, umber): desk with lamp, the ticket window with TICKET OFFICE reserved out of its header, the clock (4:09, then 4:10); the stranger (b1m2) behind the glass in panels 2-4",
        "the agent (b1m2 cut model) comes nearer panel by panel: small at the desk, at the window, under the clock, walking this way, then close at the cupboard beside the door, and in the last panel standing right at the keyhole, pencil to his chin",
        "the cupboard is beside this door and out of view; at E4 only its madder leaf swings into the keyhole's left edge, the brass key (the ANRC 1922 cutout as an ochre stencil) hanging inside it",
        "the memo slip on the desk, cut off by the keyhole's edge; captions in the shared pen hand above each panel; the four lines in pen-hand cut-paper balloons laid on the door with their tails running into the keyhole; folio by pen99.folio",
    ],
    events={"E0": "P1: at the desk, the memo partly in view ('4:15 - open SERVICE door. Key in cupboard.' cut by the keyhole edge); he gets up",
            "E1": "P2: at the window, the lady behind the glass; the question", "E2": "P3: he looks up at the clock (4:10); the answer",
            "E3": "P4: she turns from the glass; the thanks; he walks this way", "E4": "P5: the cupboard's leaf swings into view, the key on its hook inside it (only partly in view)",
            "E5": "P6: right at the keyhole, pencil to chin; the forgetting line; the key still on its hook; the door never opens"},
    declares="E0 memo and E4 key only partly in view through the keyhole",
    substitutions="none: the four lines verbatim",
    beat="the film looks through the one keyhole: the agent comes nearer frame by frame until he stands at it",
    beat_frames=["b01: P1 at the desk", "b02: P2 at the window", "b03: P3 under the clock", "b04: P4 coming this way",
                 "b05: P5 the cupboard leaf and the key swing into view", "b06: P6 at the keyhole"],
    self_check={"check": "Every panel has a keyhole-shaped opening; a reader says the viewer is behind the SERVICE door. -- by construction every panel's scene is multiplied by the same keyhole mask inside the door field; the first caption names the SERVICE door and the last says the door stays shut; perceptually judged by the maker at full size"},
    weaknesses=[
        "the SERVICE room is named by the caption ('Behind the SERVICE door, at its keyhole'): without it a reader knows only that this is a keyhole in a door beside the cupboard",
        "the stencil ties cut pale lines across the escutcheon and, in panels 4-6, across the agent; true to the method but they cross the figure",
        "the key's SERVICE tag is not shown (the key alone is cut on the leaf)",
        "the escutcheon is oversized for a real lock, to give the keyhole room at page scale",
        "the balloons sit on the dark door, outside the keyhole: the voices come through the door",
    ],
)

if __name__ == "__main__":
    finish(RECS[int(sys.argv[1])])

"""records + credits for pages 67-70 (batch 7, page maker 1). Run: python3 -I rec67_70.py NN"""
import sys
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
from rec56_59 import make

P = {}
P[67] = dict(
    n=67, pid="inner-voice", title="Inner voice", medium="daumier-collage", family="voice and language",
    declares="keeps E0-E5, the four lines and the outcome",
    build="films/swarm/99-ways/build/p67_inner_voice.py (collage kit: build/daumier12.py, build/p12_loop.py, build/p50_brief_meeting.py)",
    sources=["99-ways:daumier-proprietaire-1846", "99-ways:daumier-premier-voyage-1846", "99-ways:daumier-grand-tunnel-1843",
             "99-ways-template:anrc-gold-key-1922", "99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"],
    made=["masthead slip 'INNER VOICE' with its own legend: a small speech balloon 'what he says' and a small thought cloud 'what he thinks'",
          "six collage panels on the LoC sheet; page 12/50's Daumier kit reused: the bourgeois of 'Il est devenu pro-pri-e-taire !' (1846) as the AGENT (p50's jointed re-cut for rising and for the pencil at the chin), the bonneted woman and carriage window of 'Un premier voyage en chemin de fer' (1846) as the STRANGER behind the TICKET OFFICE glass, desk, clock, cupboard and full-height SERVICE door cut from the prints' crayon tone",
          "HANDMADE thought clouds: cut-paper clouds (ellipse core with a ring of scissor scallops, paper rim, shadow, pen outline) joined to his head by chains of paper bubbles; the errand cloud carries the memo's content and a small cut of the ANRC 1922 brass key",
          "the thoughts (ours): '4:15, the SERVICE door. The key's in the cupboard.' / 'Key, cupboard, door.' x2 / 'Ten past. Five minutes yet.' beside a smaller '...key, cupboard...' / the errand cloud breaking free / 'Now then...' / an empty cloud",
          "the four canon lines verbatim in smooth pen balloons with pointed tails; four short narration slips"],
    events={"E0": "P1: at the desk with the memo, rising; errand cloud with the key", "E0-E1": "P2: walking, 'Key, cupboard, door' cloud; question balloon from the window",
            "E2": "P3: head tipped to the clock at 4:10; answer balloon; a new cloud 'Ten past' crowds the errand into a small one",
            "E3": "P4: thanks balloon; the bubble chain is broken (two loose bubbles by his head) and the errand cloud, key and all, sails off over the ticket window after her: 'Here the errand leaves his head'",
            "E4": "P5: the cupboard open, the key on its hook tagged SERVICE; cloud 'Now then...'",
            "E5": "P6: pencil to chin, 'Well, here I am... and what for?' spoken; his thought cloud empty; key on its hook, SERVICE door shut"},
    subs="none: the four lines verbatim (the forgetting line is spoken aloud to himself, in a speech balloon, beside an empty thought cloud)",
    beat="the errand leaves his head: the thought forms over the desk, crowds at the clock, then the bubble chain breaks and the errand cloud drifts out across the panel over the ticket window after her, leaving the empty cloud at the cupboard",
    beat_frames=["b01: page with panel 1 only, no thought yet", "b02: the errand cloud with the key forms over his head",
                 "b03: panels 2-3: key, cupboard, door; then crowded by 'Ten past'", "b04: panel 4: the thanks, errand cloud still joined to his head",
                 "b05: chain broken, the cloud a third of the way to the window", "b06: two-thirds of the way",
                 "b07: over the window, after her; caption 'Here the errand leaves his head'", "b08: the whole page: 'Now then...' and the empty cloud"],
    checks={"thought_clouds": "scalloped clouds with bubble chains in every panel; spoken lines in smooth balloons with pointed tails",
            "errand_leaves": "panel 4 (the thanks), named in its caption", "lines_verbatim": True})

P[68] = dict(
    n=68, pid="showdown", title="Showdown", medium="engraving-puppet", family="genre",
    declares="keeps E0-E5, the four lines and the outcome",
    build="films/swarm/99-ways/build/p68_showdown.py (engraving puppets and storyboard sheet: kit/build_page03.py, build/p49_epic.py)",
    sources=["99-ways:loc-harpers-1863-army-telegraph-operator", "99-ways:loc-hyde-1883-cruelties-of-fashion",
             "99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"],
    made=["a western storyboard sheet: a torn frontier bill pinned at the head, 'SHOWDOWN / AT THE TICKET WINDOW / Randolph station, 4:10 sharp. Eight shots, one clock.', with pen five-point stars",
          "eight widescreen shot boards (two full-width establishing shots, six half-width), each letterboxed with black bars, headed 'SHOT n' with its framing (WIDE, MEDIUM, EXTREME CLOSE-UP, HANDS AT THE HIP, CLOSE: THE CLOCK) and a running time to the second, 4:09:30 to 4:11:00, beside a small pen clock face whose second hand moves: the clock as the duel's timer",
          "page 03/49's ENGRAVING PUPPETS reused: the AGENT is the Harper's Weekly 1863 telegraph operator (LoC cph.3c11072) pinned at the joints; the STRANGER the hatted woman of the 1867 Steinway Hall engraving (LoC cph.3c32079), behind the 1863 plate's window glass; shot 3 cuts both heads large, split by a black sash bar (the eyes-only standoff); shot 4 the agent at 0.78 scale, both arms out at the hip, pen twitch marks at the hovering hand; shot 5 the wall clock filling the frame at 4:10 with its second hand, 'tick / tock'",
          "HANDMADE pen props: a tumbleweed (blown hay) rolling past after she leaves, clock faces, set; torn commentary slips in a frontier drawl, written for this page; the four canon lines verbatim in cut-paper balloons"],
    events={"E0": "shot 1 (wide): desk and memo, he gets up; shot 2: crossing the floor, he stops, a shape at the window",
            "E1": "shot 3: eyes (no line); shot 4: hands at the hip, question balloon from the window",
            "E2": "shot 5: the clock at 4:10 fills the frame; answer balloon", "E3": "shot 6: thanks balloon; she turns away; tumbleweed",
            "E4": "shot 7: the cupboard open, the key on its hook, tagged SERVICE",
            "E5": "shot 8 (wide): pencil to chin before the open cupboard, forgetting balloon; the SERVICE door shut"},
    subs="none: the four lines verbatim",
    beat="the duel on the clock: shot by shot, the header timer running to the second; the question laid in the standoff, the big clock's second hand ticking 4:10:04 to 4:10:09, the answer, the tumbleweed rolling through, the forgetting",
    beat_frames=["b01: shots 1-2", "b02: shot 3, the eyes", "b03: shot 4, the standoff, silent", "b04: the question",
                 "b05: shot 5, the clock at 4:10:04, silent", "b06: second hand at :09, the answer", "b07: shot 6, the tumbleweed at the window's edge, the thanks", "b08: the whole sheet"],
    checks={"genre_cues": "letterboxed shot boards, frontier bill, eyes-only close-up, hands at the hip, clock-as-timer to the second in every header, tumbleweed, drawl commentary",
            "lines_verbatim": True})

P[69] = dict(
    n=69, pid="picture-sheet", title="Picture sheet", medium="busch-fold", family="medium and material",
    declares="lines quoted inside the verses",
    build="films/swarm/99-ways/build/p69_picture_sheet.py (busch-fold kit: build/p59_once_upon.py, build/p39_meanwhile.py, build/p11_station_cat.py)",
    sources=["les-caids-de-la-gaudriole:busch-mm-031", "99-ways:busch-helene-munzel", "les-caids-de-la-gaudriole:vintage-paper",
             "les-caids-de-la-gaudriole:wood-table", "99-ways:handmade"],
    made=["a 19th-century picture sheet on the les-caids tabletop: head 'PICTURE SHEET No. 69 / THE AGENT AND THE KEY / a true and improving history of Randolph station, in twelve pictures' between ornament rules; foot rule and colophon 'Plain one penny, coloured twopence. Printed for the station agents of Vermont.'",
          "twelve numbered plate pictures in a 3 x 4 grid, each ruled with a double line, printed into the vintage paper's grain; under each a rhymed couplet (our own verses, 3 lines in the pen hand); no balloon anywhere",
          "the agent = the les-caids porter cutout (Busch 1865, Max und Moritz plate 31) in p39's cut; the stranger = Helene (Busch 1872) with p39's HANDMADE cloche, clipped to the ticket-window glass; HANDMADE ink set (p59/p39 helpers): desk and memo slip, clock at 4:10, ticket window and TICKET OFFICE board, cupboard closed then open on its left jamb, the brass key on its hook with its SERVICE tag, the SERVICE door",
          "HANDMADE hand-colouring: five flat washes (blue coat, madder dress, ochre floor and desk, green SERVICE door, grey glass) laid slightly off register, as stencil-and-brush coloured sheets were",
          "the sheet carries the creases of being sold folded in four (a valley down the middle, a ridge across)"],
    events={"E0": "pictures 1-3: reads the memo; sets off; nearly at the cupboard and SERVICE door, a tap at the glass",
            "E1": "pictures 4-5: the lady at the pane; the question quoted in verse 5",
            "E2": "pictures 6-7: he reads the clock (4:10); the answer quoted in verse 7",
            "E3": "pictures 8-9: the thanks quoted in verse 8; the empty window",
            "E4": "pictures 10-11: the cupboard open, the key on its hook, the SERVICE tag",
            "E5": "picture 12: pencil to chin; the forgetting quoted in verse 12; key on its hook, SERVICE door shut"},
    subs="the four lines verbatim but quoted inside rhymed verses instead of balloons (as the canon constraint declares)",
    beat="the sheet is unfolded on the table (a quarter, a half, whole) and then hand-coloured row by row",
    beat_frames=["b01: folded in four, one quarter up", "b02: opened once, the top half", "b03: open flat, uncoloured",
                 "b04: row 1 coloured", "b05: rows 1-2", "b06: rows 1-3", "b07: fully coloured"],
    checks={"pictures": 12, "verse_under_every_picture": True, "balloons": 0, "lines_quoted_verbatim_in_verses": True})

P[70] = dict(
    n=70, pid="footnotes", title="Footnotes", medium="pen-hand", family="reduction and expansion",
    declares="keeps E0-E5, the four lines and the outcome",
    build="films/swarm/99-ways/build/p70_footnotes.py (page 51's pen drawing: build/p51_pen_alone.py; figure model: build/b1m2.py)",
    sources=["99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"],
    made=["page 51's eight one-pen panels (base page order) redrawn at 0.56 in two tiers across the top 36% of the sheet (y 110-1036); the upper tier's frames widened to the measure, floor and wainscot lines run on",
          "27 superscript footnote numbers in a red-brown pen ink: on every object (memo, desk, agent, pencil, cupboard, SERVICE door, TICKET OFFICE window, stranger, clock, open cupboard, key, tag, hook, the pencil at the chin, the key and door at the end) and on the words of the four canon lines (placed at measured word ends inside the balloons)",
          "a short footnote rule, then 27 numbered notes in two columns in the shared pen hand (cap 30), our own text, cross-referring to one another"],
    events={"E0": "panels 1-3 (notes 1-7)", "E1": "panel 4 (notes 8-12)", "E2": "panel 5 (notes 13-15)", "E3": "panel 6 (notes 16-17)",
            "E4": "panel 7 (notes 18-21)", "E5": "panel 8 (notes 22-27)"},
    subs="none: the four lines verbatim",
    beat="the annotator at work: the bare strip, then the numbers go into the panels tier by tier and the notes are written under the rule a block at a time",
    beat_frames=["b01: the strip and the rule, no numbers", "b02: numbers 1-9", "b03: notes 1-9", "b04: numbers to 17",
                 "b05: notes to 17", "b06: numbers to 27", "b07: all 27 notes"],
    checks={"footnote_numbers_in_panels": 27, "notes": 27, "panels_bottom_y": 1036, "panels_height_fraction_of_page": 0.36,
            "lines_verbatim": True})


if __name__ == "__main__":
    make(**P[int(sys.argv[1])])

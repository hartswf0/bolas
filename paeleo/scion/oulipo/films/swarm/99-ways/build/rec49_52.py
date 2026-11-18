"""Records and credits for pages 49-52 (batch 5, page maker 2). Run: python3 -I rec49_52.py"""
import json
import os
import sys

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import b1m2 as B  # noqa: E402

ROOT = B.ROOT
CANON = json.load(open(ROOT / "films/swarm/99-ways/canon.json"))
CON = {c["id"]: c for c in CANON["constraints"]}
LINES = {k: v["text"] for k, v in CANON["incident"]["lines"].items()}


def base(n, pid, build, sources):
    c = CON[pid]
    jp = ROOT / f"assets/pages/99-ways/{n:02d}-{pid}.jpg"
    beats = sorted((B.BEATS / f"{n:02d}").glob("b*.png"))
    from PIL import Image
    im = Image.open(jp)
    return {
        "n": n, "id": pid, "title": c["title"], "rule": c["rule"], "medium": c["medium"], "family": c["family"],
        "canon_revision": "c1", "declares": c.get("declares", "keeps E0-E5, the four lines and the outcome"),
        "file": f"assets/pages/99-ways/{n:02d}-{pid}.jpg", "master": f"films/sources/99-ways/masters/{n:02d}-{pid}.png",
        "beats_dir": f"films/sources/99-ways/beats/{n:02d}", "build": build, "sources": sources,
        "lines": LINES,
        "_sc": {"size_px": list(im.size), "jpeg_bytes": os.path.getsize(jp), "jpeg_quality": 90,
                "in_target_0.4_1.2MB": 400000 <= os.path.getsize(jp) <= 1200000, "beat_frames": len(beats),
                "beat_size": list(Image.open(beats[0]).size) if beats else None},
    }


def finish(r, sc, beat, frames, made, events, subst):
    s = r.pop("_sc")
    s.update(sc)
    s["pending"] = "independent blind reading not run by the maker"
    r.update(made=made, events=events, substitutions=subst, beat=beat, beat_frames=frames, self_check=s)
    B.write_record(r)
    B.credit_pages(r["sources"], r["n"])
    return r


ENG = ["99-ways:loc-harpers-1863-army-telegraph-operator", "99-ways:loc-1867-dickens-tickets-steinway",
       "99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"]
DAU = ["99-ways:daumier-proprietaire-1846", "99-ways:daumier-premier-voyage-1846", "99-ways:daumier-grand-tunnel-1843",
       "99-ways-template:anrc-gold-key-1922", "99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"]

# ---------------------------------------------------------------- 49 Epic
r = base(49, "epic", "films/swarm/99-ways/build/p49_epic.py (engraving puppets and storyboard sheet: kit/build_page03.py; "
         "slips and wrap: build/b1m2.py)", ENG)
sys.path.insert(0, str(ROOT / "films/swarm/99-ways/build"))
import p49_epic as P49  # noqa: E402
finish(r, {"register": "heroic/epic: invocation of the Muse, epithets (keeper of the hours, the far-travelled one), "
                       "the errand a Quest, the cupboard the Vault, the question a summons, the clock the Orb of the Hours, "
                       "the memo the sacred scroll, the SERVICE tag a rune, 'lo!', 'Here ends the Quest'",
           "captions": [P49.SLIPS[k] for k in range(1, 7)], "lines_verbatim": True},
       "the storyboard sheet fills canto by canto: each board is pinned up with its torn commentary slip; cantos II and VI "
       "arrive silent and then have their balloon laid on",
       ["b01: title slip + canto I (E0)", "b02: + canto II silent", "b03: canto II summons balloon laid", "b04: + canto III answer",
        "b05: + canto IV thanks", "b06: + canto V the Vault flung wide", "b07: + canto VI silent", "b08: canto VI forgetting balloon (= the page)"],
       ["a storyboard sheet headed by a torn title slip 'THE QUEST OF THE BRASS KEY / an epic of Randolph station, in six cantos' "
        "with pen-drawn laurel sprigs; six cream storyboard boards titled 'CANTO I-VI' with event and time (4:09-4:11), "
        "each with a torn commentary slip pinned below",
        "page 03's ENGRAVING PUPPETS reused (kit/build_page03.py): the AGENT is the Harper's Weekly 1863 telegraph operator "
        "(LoC cph.3c11072) cut at the joints and pinned with brass brads; the STRANGER the hatted woman of the 1867 Steinway "
        "Hall engraving (LoC cph.3c32079); his table and the TICKET OFFICE window cut from the 1863 plate; memo, clock (4:09 / "
        "4:10), cupboard (closed / open with the key on its hook tagged SERVICE) and SERVICE door drawn in the shared pen hand",
        "six commentary slips in an inflated heroic register (invocation, epithets, 'lo!'), written for this page; the four "
        "canon lines verbatim in cut-paper balloons",
        "layout measured from the slips so no heading touches a slip; the LoC sheet softened 1.8 px for the JPEG budget"],
       {"E0": "canto I: the sacred scroll (memo) on the desk, the hero rises, arm flung toward the Vault",
        "E1": "canto II: the stranger at the gate of glass; 'cried a summons'; question balloon",
        "E2": "canto III: the Orb of the Hours at 4:10; answer balloon",
        "E3": "canto IV: thanks balloon; she passes from the gate into the west",
        "E4": "canto V: the Vault flung wide; the Brass Key on its hook, the rune SERVICE",
        "E5": "canto VI: pencil to chin before the open Vault; forgetting balloon; 'the Key hung on, unclaimed; the Door of "
              "SERVICE stayed sealed'"},
       "none: the four lines verbatim (balloons); only the captions carry the epic register")

# ---------------------------------------------------------------- 50 Brief meeting
r = base(50, "brief-meeting", "films/swarm/99-ways/build/p50_brief_meeting.py (collage kit: build/daumier12.py, "
         "build/p12_loop.py)", DAU)
finish(r, {"genre_signals": "masthead 'BRIEF MEETING / a love story at the ticket window'; an oval close-up of the two "
                            "faces with the pane between them and a rose-paper heart; romance narration ('Their eyes met "
                            "through the pane', 'He would have given her the clock', 'Her thanks lingered', 'his heart "
                            "was out on the platform; the errand had gone with her'); hearts rising from the thanks and "
                            "one drifting above his head at the forgetting",
           "lines_verbatim": True, "outcome": "key on its hook, SERVICE door closed (caption and picture)"},
       "the glance: in the oval panel the two cut-out faces slide toward each other across the pane and the rose heart is "
       "glued between them; then the thanks raises its little hearts; then the forgetting balloon and the drifting heart",
       ["b01: panels 1-3, the faces apart, no heart", "b02: the faces closer", "b03: faces at the pane, heart glued on",
        "b04: + panels 4-5, the thanks without hearts", "b05: the hearts rise from the thanks",
        "b06: + panels 6-7, no forgetting line, no heart", "b07: forgetting balloon and drifting heart (= the page)"],
       ["seven collage panels (the third an oval vignette across the page) glued on the LoC sheet, under a masthead slip "
        "'BRIEF MEETING' with two rose-paper hearts",
        "page 12's Daumier collage kit reused: the bourgeois of 'Il est devenu pro-pri-e-taire !' (1846) as the AGENT; the "
        "bonneted woman and the carriage window of 'Un premier voyage en chemin de fer' (1846) as the STRANGER and the "
        "TICKET OFFICE window; the CONCIERGE door as the SERVICE door; desk, counter, cupboard and clock case cut from the "
        "prints' own crayon tone (incl. the tunnel black of 'L'entree du grand tunnel', 1843); the ANRC 1922 key in the cupboard",
        "the oval close-up: her head and shoulders cut from her figure at 1.85x, his figure at 1.3x, the pane cut from the "
        "carriage window's pale paper with tunnel-black sash bars and white pen glints",
        "HANDMADE: rose-paper hearts (heart curve cut as scissor facets, rim and shadow), romance narration slips, pen-hand "
        "balloons with the four canon lines verbatim, pencil to his chin, hand-ruled borders and the oval's pen line"],
       {"E0": "P1: desk, memo slip ('4:15 - open SERVICE door. Key in cupboard.'), he has risen; 'Nothing else on his mind'",
        "E1": "P2: she at the TICKET OFFICE window; question balloon; 'a voice at the glass'; P3: the glance through the pane",
        "E2": "P4: clock at 4:10, he looks up; answer balloon",
        "E3": "P5: thanks balloon, she turns away; 'Her thanks lingered... and then she was gone'",
        "E4": "P6: the cupboard open, the key on its hook tagged SERVICE",
        "E5": "P7: pencil to chin, forgetting balloon, a heart drifting where the errand was; key on its hook; SERVICE door shut"},
       "none: the four lines verbatim")

# ---------------------------------------------------------------- 51 Pen alone
r = base(51, "pen-alone", "films/swarm/99-ways/build/p51_pen_alone.py (figure and set shapes: build/b1m2.py)",
         ["99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"])
finish(r, {"pen_width_px": round(B.pen99.FOLIO_CAP * 0.13, 2),
           "one_weight": "every mark is the one pen: drawing strokes 4.42 px (13 px at 3x supersampling), lettering at "
                         "weight = 4.42 / cap for every size (44 px balloons, 50 px thanks, 25 px memo, 30 px TICKET "
                         "OFFICE / SERVICE, 24 px key tag), the folio's own pen (34 px x 0.13)",
           "measured_stroke_width_px_on_master": {"median": 6.0, "p5": 4.0, "p95": 6.0,
                                                  "note": "thresholded at L<110 incl. anti-aliasing; wider readings only at "
                                                          "line junctions"},
           "no_tone_no_fill": "no fills, hatching, shadows, slips or photographs; balloons are pen outlines on the bare sheet",
           "lines_verbatim": True},
       "the page is drawn as by one pen: the frames ruled first, then the panels in reading order; the cupboard drawn shut and "
       "then redrawn open; the forgetting balloon written last",
       ["b01: the eight frames ruled", "b02: panels 1-2 drawn", "b03: panels 3-4", "b04: panels 5-6",
        "b05: panel 7 with the cupboard shut", "b06: panel 7 with the cupboard open, the key on its hook",
        "b07: panel 8 without the line", "b08: the forgetting balloon written (= the page)"],
       ["eight panels after the base page's order, every mark in the shared pen hand at one width (the folio pen, 4.42 px)",
        "figures and set drawn as pen outlines of page 05's HANDMADE figure model (b1m2.agent with spectacles, waistcoat, "
        "sleeve garter and pencil; b1m2.stranger with her hat and bow; desk, ticket window, clock at 4:10, cupboard, SERVICE "
        "door), hidden lines lifted (each nearer shape erases the lines behind it before its outline is drawn: bare paper, "
        "never fill); thin parts (slits, ticks, pencil, garter) drawn as single centre lines, tiny rounds opened to rings",
        "the brass key drawn in outline (hook, bow ring and eye, shank, bit) with its SERVICE tag on a string",
        "balloons as pen outlines with the four canon lines verbatim; MEMO, TICKET OFFICE and SERVICE lettered in boxes",
        "the LoC 1934 sheet as the only ground"],
       {"E0": "P1 at the desk with the memo; P2 risen and walking; P3 walking past the closed cupboard and the SERVICE door",
        "E1": "P4: she behind the TICKET OFFICE window; question balloon", "E2": "P5: the clock at 4:10; answer balloon",
        "E3": "P6: she turned away; thanks balloon", "E4": "P7: the cupboard open, the key on its hook tagged SERVICE",
        "E5": "P8: pencil to chin, forgetting balloon; key on its hook; SERVICE door shut"},
       "none: the four lines verbatim")

# ---------------------------------------------------------------- 52 From the hill
r = base(52, "from-the-hill", "films/swarm/99-ways/build/p52_from_the_hill.py (card kit: build/charcoal99.py and the "
         "page-20 card helpers in build/p20_across_the_tracks.py; figure model build/b1m2.py)",
         ["teuf-teuf:cueva-de-las-manos", "99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"])
import p52_from_the_hill as P52  # noqa: E402
hs = [b[3] - b[1] for b in P52.BOXES]
finish(r, {"panel_heights_px": hs, "tallest_figure_px": {"agent_speck": 14, "stranger_card": 26},
           "max_figure_to_panel_ratio": round(26 / min(hs), 3), "rule_no_figure_over_one_tenth": 26 / min(hs) < 0.1,
           "station_width_px": 112, "lines_verbatim": True},
       "the valley fills frame by frame; each balloon arrives after its frame, its tail stretched across fields and river "
       "down to the speck of its speaker",
       ["b01: frame 1, the whole valley (E0)", "b02: + frame 2 silent, the lady at the window",
        "b03: the question balloon laid across the fields", "b04: + frame 3 with the answer from the window",
        "b05: + frame 4 with the thanks, the lady walking off", "b06: + frame 5, the cupboard opened (W3)",
        "b07: + frame 6 silent", "b08: the forgetting balloon from the right window (= the page)"],
       ["one Vermont valley built once as charcoal cards and seen from the hill in six frames (a slow pan along it): the far "
        "range and a nearer range as torn pale cards, the valley's two wooded sides closing in with fringes of cut firs, a "
        "perspective patchwork of fields (woodlots dotted with cut trees, hedgerows rubbed in charcoal), the White River "
        "meandering down toward us (dark banks, pale water, torn), the railway along the valley, farm houses, barns and a "
        "white church, and our own hill crest across the foot of each frame with its trees and fence posts",
        "page 20's charcoal-card kit reused (charcoal99.py, p20_across_the_tracks.py): every card rubbed with the foraged "
        "Cueva de las manos rock relief (teuf-teuf, CC BY-SA 3.0, Suzko), hatched, darker at its cut edges, torn or "
        "scissor-cut, dropped with its own shadow; the sky is the same rock wash worked with broken strokes",
        "the station about 112 px wide: dark card box, hipped roof, three lit windows; the agent a 14 px speck that moves "
        "from window to window (desk, ticket window, cupboard), the cupboard opened as a dark slot and pale leaf in the "
        "right window; the stranger page 20's back-view card puppet at 26 px on the platform, then walking off",
        "the four canon lines verbatim in cut-card balloons laid on the land, their tails running across fields and river "
        "to the speaker; captions on torn pale cards in the shared pen hand; hand-ruled borders"],
       {"E0": "frame 1: the valley; caption: the agent reads his memo (4:15, the SERVICE door) and gets up; speck in W1",
        "E1": "frame 2: the lady (26 px) at the ticket window; question balloon tailed to her",
        "E2": "frame 3: caption 'He looks at the office clock'; answer balloon tailed to the middle window",
        "E3": "frame 4: thanks balloon; she walks off along the platform",
        "E4": "frame 5: caption 'He opens the cupboard: the key hangs on its hook'; dark slot and leaf in W3 (implied by the "
              "stated cue: the key itself is too small to see at this distance)",
        "E5": "frame 6: forgetting balloon tailed to W3; caption: the key stays on its hook, the SERVICE door stays closed"},
       "none: the four lines verbatim")
print("records 49-52 written")

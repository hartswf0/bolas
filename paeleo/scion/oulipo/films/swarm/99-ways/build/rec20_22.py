"""Records + credits for pages 20 (Across the tracks), 21 (Told at dusk), 22 (Ballad)."""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import b1m2 as B  # noqa: E402

CANON = json.load(open(B.ROOT / "films/swarm/99-ways/canon.json"))
CON = {c["n"] if "n" in c else i + 1: c for i, c in enumerate(CANON["constraints"])}
LN = {k: v["text"] for k, v in CANON["incident"]["lines"].items()}


def base(n, pid, build):
    c = CON[n]
    jp = B.PAGES_OUT / f"{n:02d}-{pid}.jpg"
    size = jp.stat().st_size
    return {"n": n, "id": c["id"], "title": c["title"], "family": c["family"], "medium": c["medium"],
            "canon_revision": CANON["revision"], "rule": c["rule"], "declares": c["declares"],
            "file": f"assets/pages/99-ways/{n:02d}-{pid}.jpg", "master": f"films/sources/99-ways/masters/{n:02d}-{pid}.png",
            "beats_dir": f"films/sources/99-ways/beats/{n:02d}", "build": build}, size


def sc(size, **kw):
    d = {"size_px": [2200, 2850], "jpeg_bytes": size, "jpeg_quality": 90, "in_target_0.4_1.2MB": 400000 <= size <= 1200000}
    d.update(kw)
    d["pending"] = "independent blind reading not run by the maker"
    return d


# ---------------------------------------------------------------- 20
r, size = base(20, "across-the-tracks", "films/swarm/99-ways/build/p20_across_the_tracks.py (kit: build/charcoal99.py, figures build/b1m2.py)")
src = ["teuf-teuf:cueva-de-las-manos", "99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"]
B.credit_pages(src, 20)
r.update({
    "sources": src,
    "made": [
        "one far viewpoint repeated in all seven panels: our own platform edge (pale painted edge line) at the foot, two tracks of charcoal-card sleepers and rails between, the station a small dark card box with a hipped roof, a RANDOLPH name board and three lit windows; hills, trees and telegraph poles behind as paler cards; the charcoal-card wall (teuf-teuf Cueva plain-rock relief, ramp-printed) as the sky's grain",
        "the lit office rendered on its own and seen only through the cut windows: the b1m2 agent at 0.14 scale (about 100 px tall) at his desk (W1), crossing past the ticket window (W2) under the office clock, and at the cupboard (W3); cupboard, its door leaf with the brass key and paper tag on its hook, and the SERVICE door with a pale card fleck, cut as plain cards at this distance",
        "the stranger: a small back-view card puppet made for this page (hat, head, coat, skirt, legs), outside on the station platform against the lit ticket window, then walking off down the platform",
        "panel 1 adds a big dark lamp post and bench end on our platform for scale",
        "the four canonical lines verbatim in cut-card balloons laid on our side of the rails, their long tails running across both tracks to the tiny speaker; short captions on pale cards in the shared pen hand",
        "hand-ruled borders (penlib.border_mask); folio '20 / Across the tracks' (pen99.folio)"],
    "events": {"E0": "P1: the agent at his desk in the left window (caption: reads his memo); P2: 4:09, he crosses past the ticket window; the stranger approaches along the far platform",
               "E1": "P3: the stranger at the lit ticket window; her balloon tailed across the rails",
               "E2": "P4: he looks up at the office clock; his balloon",
               "E3": "P5: she walks off down the platform; 'Much obliged!' tailed to her",
               "E4": "P6: the cupboard open in the right window, the key on its hook on the door leaf",
               "E5": "P7: pencil to chin before the open cupboard; his line; the SERVICE door shut (caption)"},
    "lines": LN, "substitutions": "none (lines verbatim)",
    "beat": "the far view fills panel by panel; each balloon arrives after its panel, its tail stretched across the rails",
    "beat_frames": ["b01: P1 (establishing far view, agent at desk)", "b02: + P2 (he crosses; she approaches)",
                    "b03: + P3 without balloon", "b04: P3 balloon laid across the rails (question)",
                    "b05: + P4 with answer, + P5 without balloon", "b06: P5 thanks balloon laid",
                    "b07: + P6, + P7 without balloon", "b08: P7 forgetting balloon laid (= the page)"],
    "self_check": sc(size, viewer="every panel framed from beyond two tracks: our platform's painted edge at the foot of each frame, rails between, figures about 100 px tall in a station 530 px wide; panel 1's near lamp post and bench give the scale",
                     lines_verbatim=True),
})
B.write_record(r)
print(20, size)

# ---------------------------------------------------------------- 21
r, size = base(21, "told-at-dusk", "films/swarm/99-ways/build/p21_told_at_dusk.py (rol-cutout kit: kit/build_page04.py; rest layers via kit/build_page01.py)")
src = ["99-ways:rol-34852-sainte-catherine-1913", "99-ways-template:rothstein-randolph-agent-1937",
       "99-ways-template:rothstein-tavern-clock-1937", "99-ways-template:anrc-gold-key-1922",
       "99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"]
B.credit_pages(src, 21)
rec = json.load(open(B.SRC / "p21_rec.json"))
r.update({
    "sources": src,
    "made": [
        "the evening frame: a dusk-blue card round the whole page; on it the 99-ways-template rest layers of P3 (Rothstein 1937 office, the agent before the cupboard whose leaf carries the SERVICE card) printed as a cold blue-grey toned press print with a white scissor margin, the hanging lamp lit (a warm glow laid round its bulb)",
        "the office clock cut out from the 99-ways-template clock pieces (LoC tavern clock) with its own hour and minute hands re-set on the arbor to 6:00, pasted with a scissor margin",
        "cover-page grammar of the rol-cutout kit: 'Six o'clock.' lettered letter by letter in the shared pen hand (jumping, ochre and cream on the dusk), caption slips; thought dots (cut-paper discs) from the evening print down onto the afternoon card",
        "the afternoon: a warm butter card laid inside the frame, headed 'That afternoon'; six warm sepia prints of the 99-ways-template rest layers (P1, P4, P5, P6, P7, P8) with white scissor margins, numbered caption slips in past tense and the clock time of each beat (4:08 ... 4:11)",
        "the stranger: the Agence Rol 34852 woman cutout (as on page 04) set behind the ticket-window glass at 80 % (E1) and turning away (E3), the four lines in the shared cut-paper balloons, hers tailed to her",
        "closing evening slip at the foot: 'Six o'clock still. The key hangs on its hook; the SERVICE door stays shut; and what he came for, he cannot say.'",
        "folio '21 / Told at dusk' (pen99.folio)"],
    "events": {v["event"]: f"{k} ({v['time']}): {v['caption']}" + (f" | balloon: {v['balloon']}" if v["balloon"] else "") for k, v in rec.items()},
    "evening_frame": "added after E5 (declared): 6 p.m., the agent before the still-closed SERVICE door, the clock at 6:00; he goes back over the afternoon and still cannot say what he came for (outcome unchanged)",
    "lines": LN, "substitutions": "none (lines verbatim)",
    "beat": "the evening frame first (six o'clock, the shut door, the remembering begins), then the afternoon prints are laid on one by one, 4:08 to 4:11, and the frame closes with the evening slip",
    "beat_frames": ["b01: the evening frame only: dusk print, clock at 6:00, 'Six o'clock.', the afternoon card still empty"] +
                   [f"b{j + 2:02d}: + afternoon print {j + 1}" for j in range(6)] + ["b08: + the closing evening slip (= the page)"],
    "self_check": sc(size, separation="evening = dusk-blue frame, blue-toned print, clock at 6:00, present-tense slips; afternoon = butter card inside it, warm sepia prints, past-tense slips stamped 4:08-4:11",
                     lines_verbatim=True),
})
B.write_record(r)
print(21, size)

# ---------------------------------------------------------------- 22
sys.argv = ["x"]
import p22_ballad as P22  # noqa: E402
r, size = base(22, "ballad", "films/swarm/99-ways/build/p22_ballad.py (stencil-dye kit: build/p08_lipogram.py; figures build/b1m2.py)")
src = ["99-ways-template:anrc-gold-key-1922", "99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"]
B.credit_pages(src, 22)
r.update({
    "sources": src,
    "made": [
        "eight panels printed as HANDMADE stencils in flat dyes (the page 08 stencil-dye method: one cut stencil per colour with paper ties, fixed misregistration, mottled dye pooling at the edges) from the b1m2 cut model, on the LoC 1934 sheet",
        "the ANRC 1922 key cutout used as a stencil in ochre, hanging on its drawn hook on the inside of the open cupboard leaf, with a SERVICE tag slip",
        "eight rhymed couplets (ours) in the shared pen hand on pale paper strips across the top of each panel; each couplet's two rhyme words lettered in madder",
        "the memo slip, TICKET OFFICE window lettering and SERVICE cards in the pen hand; hand-ruled borders; folio '22 / Ballad'"],
    "couplets": [list(c) for c in P22.COUPLETS],
    "rhymes": [list(x) for x in P22.check()],
    "events": {"E0": "couplets 1-2: the memo; he rises to fetch the key", "E1": "couplet 3: 'Pardon me - have you the right time?' (whole second line)",
               "E2": "couplet 4: 'Ten past four, by the clock.' (whole second line)", "E3": "couplet 5: 'Much obliged!' she said with grace",
               "E4": "couplet 6: the cupboard swung wide, the key tagged SERVICE inside", "E5": "couplet 7: 'Well, here I am... and what for?' (whole second line); couplet 8: the key stays, the door stays shut"},
    "lines": LN, "substitutions": "none: the four lines are kept word for word and set inside the couplets (declared: lines set to rhyme inside the couplets); the em dash is lettered as the pen hand's dash",
    "beat": "the ballad grows panel by panel; the last panel is printed dye by dye (wall wash, then ochre and verdigris, then indigo, madder, skin and umber) and its couplet is pasted on last",
    "beat_frames": ["b01: panel 1 with couplet 1", "b02: panels 1-3", "b03: panels 1-5", "b04: panels 1-7",
                    "b05: panel 8: wall wash only", "b06: panel 8: + ochre and verdigris (cupboard, door)",
                    "b07: panel 8: all dyes, no couplet", "b08: couplet 8 pasted (= the page)"],
    "self_check": sc(size, couplets=8, every_caption_two_lines=True, rhyme_check="end words asserted at build time: be/key, chair/there, chime/time, stock/clock, grace/place, wide/inside, door/for, stay/day",
                     lines_verbatim=True),
})
B.write_record(r)
print(22, size)

"""Records and credits for pages 42-44 (batch 4, page maker 3)."""
import json
import sys

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
from b1m2 import *  # noqa
from PIL import Image

LINES = {"question": "Pardon me — have you the right time?", "answer": "Ten past four, by the clock.",
         "thanks": "Much obliged!", "forgetting": "Well, here I am... and what for?"}
EV = "perceptually judged (from frames) by the maker at full size; independent blind readers not yet run"


def sc(jp, extra):
    im = Image.open(jp)
    d = {"size_px": list(im.size), "jpeg_bytes": jp.stat().st_size, "jpeg_quality": 90,
         "in_target_0.4_1.2MB": 400000 <= jp.stat().st_size <= 1200000, "evidence": EV}
    d.update(extra)
    return d


def nbeats(n):
    return len(list((BEATS / f"{n:02d}").glob("b*.png")))


# ------------------------------------------------------------------ 42
s42 = ["99-ways-template:anrc-gold-key-1922", "99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"]
credit_pages(s42, 42)
jp = PAGES_OUT / "42-lamp-shadows.jpg"
write_record({
 "n": 42, "id": "lamp-shadows", "title": "Lamp shadows", "family": "medium and material", "medium": "shadow-puppet",
 "canon_revision": "c1",
 "rule": "Only the shadows the lamp throws on the office wall tell the story; the people themselves are never seen.",
 "declares": "keeps E0-E5, the four lines and the outcome",
 "file": "assets/pages/99-ways/42-lamp-shadows.jpg", "master": "films/sources/99-ways/masters/42-lamp-shadows.png",
 "beats_dir": "films/sources/99-ways/beats/42",
 "build": "films/swarm/99-ways/build/p42_lamp_shadows.py (puppets and set pieces: build/b1m2.py, key/hook/card: p05_noir.py)",
 "sources": s42,
 "made": [
  "seven panels, each a stretch of the office wall: plaster (LoC 1934 sheet fibre as the plaster grain) over a boarded wainscot with a rail, lit by a lamp below or beside the frame (radial fall-off, warm)",
  "the HANDMADE b1m2 cut-paper puppets (agent in profile with spectacles cut through, pencil, waistcoat buttons; stranger bust with cloche hat) never shown: only their cast shadows, projected onto the wall through a homography (stretched, leaning away from the lamp), penumbra by blur, multiplied into the wall light",
  "the ticket-window pendant lamp throws the window grille onto the wall as a bright skewed patch with dark glazing bars, and TICKET OFFICE through the etched header glass mirror-reversed; the stranger's shadow stands in that patch",
  "objects in plain lamplight (they are not people): the green desk lamp, the memo slip on the desk edge (pen hand: 'MEMO / 4:15 - open SERVICE door. / Key in cupboard.'), the wall clock (4:09 in P1, 4:10 at the answer), the cupboard hinged on the left jamb, the ANRC 1922 brass key cutout on its hook with the SERVICE tag, the SERVICE door with its card",
  "the four canon lines in the shared cut-paper balloons, tails to the shadows' heads; folio '42 / Lamp shadows' (pen99.folio)",
  "repair this session: P6 shadow re-cast so the agent's shadow head and reaching arm are whole (it was cut by the panel edge) and the cupboard moved right so the arm's shadow lands on the open leaf"
 ],
 "events": {
  "E0": "P1 his shadow bent over the desk, pencil up, the memo slip lit on the desk edge; P2 his shadow, huge, walks along the wall toward the closed cupboard",
  "E1": "P3 her shadow in the window patch (reversed TICKET OFFICE), his shadow turned to her; question balloon tailed to her shadow",
  "E2": "P4 his shadow head tilted up to the clock at 4:10; answer balloon",
  "E3": "P5 her shadow turns away in the window patch; thanks balloon",
  "E4": "P6 cupboard open, the brass key on its hook with the SERVICE tag; his arm's shadow reaches across the open leaf",
  "E5": "P7 his shadow, pencil to chin, before the open cupboard; forgetting balloon; key on its hook, SERVICE door closed"
 },
 "lines": LINES,
 "beat": "the lamps come on panel by panel, each wall waking with its shadow; in P2 the shadow walks along the wall, in P6 the cupboard leaf swings open under the reaching shadow, in P7 the pencil-shadow rises to the chin and the forgetting balloon is laid",
 "beat_frames": ["b01: only P1 lit (shadow at the desk, memo)", "b02: P2 lit, shadow at the start of its walk",
                 "b03: P3 lit (her shadow in the window patch, question)", "b04: P4 lit (answer under the clock)",
                 "b05: P5 lit (thanks)", "b06: P6 lit, cupboard leaf at 40 degrees", "b07: P7 lit, pencil down, no balloon",
                 "b08: the finished page"],
 "self_check": sc(jp, {
  "check": "No figure appears except as a shadow on a wall: every person on the page is a cast shadow (puppet masks only ever drawn through cast()); objects are seen, people never (structurally verified in the build: agent() and stranger() shapes are passed only to cast())",
  "panels": 7, "balloon_cap_px": 44, "beats": nbeats(42),
  "outcome": "key on its hook in P6 and P7; SERVICE door closed with its card in P7"})
})

# ------------------------------------------------------------------ 43
new43 = [{
 "id": "exercices-de-style:rol-57642-homme-marchant-1920",
 "title": "Homme marchant dans la rue (Rol 57642), janvier 1920",
 "author": "Agence Rol (BnF, Pho20Rol)",
 "license": "Public domain",
 "license_url": "",
 "source_url": "https://commons.wikimedia.org/wiki/File:Homme_marchant_dans_la_rue_-_btv1b530359957.jpg",
 "carried_from": "films/credits/exercices-de-style.json (cutout films/sources/exercices-de-style/forage/visitor_rgba.png)",
 "used_as": "page 43: the 2:12 passenger, a free cutout with a white scissor margin"}]
s43 = ["99-ways-template:rothstein-randolph-agent-1937", "99-ways-template:rothstein-tavern-clock-1937",
       "99-ways-template:anrc-gold-key-1922", "99-ways:rol-34852-sainte-catherine-1913",
       "99-ways:rol-wagon-a-etage-1933", "exercices-de-style:rol-49112-homme-pardessus-1917",
       "exercices-de-style:rol-57642-homme-marchant-1920", "99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"]
credit_pages(s43, 43, new43)
r43 = json.load(open(SRC / "p43_rec.json"))
jp = PAGES_OUT / "43-the-morning-before.jpg"
write_record({
 "n": 43, "id": "the-morning-before", "title": "The morning before", "family": "reduction and expansion",
 "medium": "rol-cutout", "canon_revision": "c1",
 "rule": "The day from dawn to four is compressed into the top two tiers; the incident itself fits in the bottom tier.",
 "declares": "adds the morning (how the memo came): a man off the 7:40 leaves word from the Division that a freight inspector comes at 4:15 and the SERVICE door must be open; the agent writes the memo; E0-E5 keep the canon in the bottom tier",
 "file": "assets/pages/99-ways/43-the-morning-before.jpg",
 "master": "films/sources/99-ways/masters/43-the-morning-before.png", "beats_dir": "films/sources/99-ways/beats/43",
 "build": "films/swarm/99-ways/build/p43_morning_before.py (rol-cutout kit: kit/build_page04.py; rest layers: kit/build_page01.py)",
 "sources": s43,
 "made": [
  "three tier cards on the LoC 1934 sheet: tier 1 'First light to noon' (cool grey-blue), tier 2 'Noon to four' (warm), tier 3 '4:08 to 4:11' (the kit's butter card); tier titles in the kit's jumping cover lettering (shared pen hand)",
  "tier 1, four press prints with white scissor margins: 5:50 the empty office at first light (99-ways-template office plate, Rothstein 1937 with the clerk removed, toned cold and dim); 7:40 the Agence Rol 1933 double-deck carriage; 7:42 the ticket window from inside with the Rol 49112 man behind the glass and his order in a balloon ('From the Division: freight inspector at 4:15. Have the SERVICE door open.', ours); 7:50 the memo being pencilled (Rothstein P1 rest layers, close on the slip)",
  "tier 2: 12:00 the empty desk (office plate, warm) with a pasted pen-lettered memo slip by the inkwell; 2:12 the Rol 57642 walking man as a free cutout with a ticket stub 'RANDOLPH to MONTPELIER'; 3:55 the agent at the TICKET OFFICE window (Rothstein P4 rest layers)",
  "on every tier-1/2 piece the office clock cut out from the 99-ways-template LoC clock pieces with its own hands re-set on the arbor to that hour (5:50, 7:40, 7:42, 7:50, 12:00, 2:12, 3:55): the hands race through the day",
  "tier 3: E0-E5 in six narrow press prints of the 99-ways-template rest layers P1, P4, P5, P6, P7, P8, red numbers 1-6, the Agence Rol 34852 stranger behind the glass in E1 and E3, the four canon lines in the shared cut-paper balloons, caption slips and clock times 4:08-4:11",
  "folio '43 / The morning before' (pen99.folio)"
 ],
 "tiers": r43,
 "events": {
  "E0": "tier 3 print 1: at the desk with the memo (4:08), 'He sets off for the key.'",
  "E1": "tier 3 print 2: the stranger behind the TICKET OFFICE glass, question balloon (4:09)",
  "E2": "tier 3 print 3: he looks up at the clock (4:10 in the print), answer balloon",
  "E3": "tier 3 print 4: she turns from the window, thanks balloon (4:10)",
  "E4": "tier 3 print 5: the cupboard open, the key on its hook with the SERVICE tag (4:11)",
  "E5": "tier 3 print 6: pencil to his chin, forgetting balloon (4:11)"
 },
 "lines": LINES,
 "beat": "the day is laid down piece by piece, each print with its clock re-set further on (5:50 ... 3:55); then the six incident prints are laid in the bottom tier two at a time",
 "beat_frames": ["b01: tier 1, 5:50 only", "b02: + 7:40, 7:42", "b03: + 7:50 (tier 1 full)", "b04: + 12:00",
                 "b05: + 2:12, 3:55 (tier 2 full)", "b06: tier 3 E0-E1", "b07: + E2-E3", "b08: + E4-E5 (the page)"],
 "self_check": sc(jp, {
  "check": "A reader finds E0-E5 only in the bottom tier: tiers 1-2 hold only the day before 4:00 (5:50 to 3:55, no stranger, cupboard closed); the six numbered tier-3 prints hold E0-E5 and the four lines",
  "balloon_cap_px": [28, 30, 34], "caption_cap_px": [31, 33], "beats": nbeats(43),
  "outcome": "key on its hook in print 5; nothing in print 6 opens the SERVICE door"})
})

# ------------------------------------------------------------------ 44
s44 = ["99-ways-template:anrc-gold-key-1922", "99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"]
credit_pages(s44, 44)
r44 = json.load(open(SRC / "p44_rec.json"))
jp = PAGES_OUT / "44-n-plus-seven.jpg"
L7 = {"question": "Pardon me — have you the right wire?", "answer": "Ten past four, by the dispatcher.",
      "thanks": "Much obliged!", "forgetting": "Well, here I am... and what for?"}
write_record({
 "n": 44, "id": "n-plus-seven", "title": "N+7", "family": "formal / Oulipian rule", "medium": "pen-hand",
 "canon_revision": "c1",
 "rule": "Every noun of the captions and lines replaced by the seventh noun after it in our own station glossary, printed in the margin.",
 "declares": "lines transformed by N+7: time -> wire, clock -> dispatcher; thanks and forgetting have no nouns and stand verbatim; the drawings are not transformed, only the words drawn in them",
 "file": "assets/pages/99-ways/44-n-plus-seven.jpg", "master": "films/sources/99-ways/masters/44-n-plus-seven.png",
 "beats_dir": "films/sources/99-ways/beats/44",
 "build": "films/swarm/99-ways/build/p44_n_plus_seven.py (line diagrams and pen helpers reused from build/p32_how_to_forget.py)",
 "sources": s44,
 "made": [
  "our own alphabetical station glossary of 58 nouns (agent ... yard), numbered, in two columns in the right margin, the words that appear on the page underlined, with the counting rule ('count seven on; after 58, go on from 1')",
  "six boxed panels, captions in the shared pen hand: our plain captions for E0-E5 with the four canon lines, run through the N+7 transform (every glossary noun moved seven places on, case kept)",
  "the pictures stay true: page 32's pen line drawings (b1m2 figures and scenery traced with penlib.brush_line, the ANRC key outline) redrawn without page 32's instruction-sheet layer (no 'you' label in panel 1, no 'LOOK' label or its arrow in panel 5, no prohibition circles or their small key and door in panel 6; the key on its hook and the shut TELEGRAPH-carded door kept), cropped to their ink and fitted to each panel; their drawn words are moved seven on too (memo slip '4:15 - open TELEGRAPH key. Parcel in gauge.', window header WINDOW, the key tag and door card TELEGRAPH, 'on to the gauge', 'to the signal'), lettered smaller where the new word is longer so it stays on its tag",
  "title 'N + 7' and the worked example 'e.g. door (20) + 7 = key (27)'; folio '44 / N+7' (pen99.folio)"
 ],
 "captions_n7": r44["captions_n7"], "moved": r44["moved"], "lines_n7": L7, "glossary": r44["glossary"],
 "events": {"E0": "panel 1", "E1": "panel 2", "E2": "panel 3", "E3": "panel 4", "E4": "panel 5", "E5": "panel 6"},
 "lines": LINES,
 "beat": "the nouns move: the page first reads in plain nouns, then panel by panel every noun jumps seven places down the glossary (agent -> brakeman, door -> key, key -> parcel, clock -> dispatcher ...), and the underlines in the margin follow",
 "beat_frames": ["b01: all six panels in plain nouns", "b02: panel 1 moved seven on", "b03: + panel 2", "b04: + panel 3",
                 "b05: + panel 4", "b06: + panel 5", "b07: + panel 6 (the page)"],
 "self_check": sc(jp, {
  "check": "A reader checks any noun against the glossary: it is seven places on (structurally verified: the transform is one function over the glossary list; every on-page glossary word outside the glossary, the title example and the folio passed through it). Apparatus not transformed: the title 'N + 7', the worked example, the glossary head, the folio. Inside panels 1-6 the only words are the six N+7 captions, the drawn labels (memo slip, WINDOW, TELEGRAPH, 'on to the gauge', 'to the signal') and the 4:10 under the clock; no circle-slash sign anywhere (re-checked at full size after the repair).",
  "glossary_size": 58, "caption_cap_px": 38, "glossary_cap_px": 34, "beats": nbeats(44),
  "outcome": "caption 6: 'The parcel stays on its lever; the TELEGRAPH key stays shut.' (= the key stays on its hook; the SERVICE door stays shut); drawing 6 shows the key on its hook and the door closed"})
})
print("ok")

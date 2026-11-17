"""CANON EDITOR, 99 ways: writes ../canon.json and ../canon.md ONCE. Refuses to overwrite (the canon is frozen;
changes go to ../amendments.md). All text here is the production's own.
Run: python3 -I make_canon.py"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WS = HERE.parent
OUT_J, OUT_M = WS / "canon.json", WS / "canon.md"
if OUT_J.exists():
    sys.exit("canon.json exists: frozen, not rewritten")

LINES = {
    "Q": "Pardon me — have you the right time?",
    "A": "Ten past four, by the clock.",
    "T": "Much obliged!",
    "F": "Well, here I am... and what for?",
}

INCIDENT = {
    "revision": "c1",
    "title": "The SERVICE key",
    "summary": ("Randolph station, Vermont, a September afternoon in 1937. The station agent's memo says the SERVICE door "
                "is to be opened at 4:15 with the brass key kept in the office cupboard. He gets up to fetch it. On his way "
                "a stranger at the ticket window asks him the time; he looks at the wall clock and tells her; she thanks him "
                "and goes. He reaches the cupboard, opens it, and stands before the brass key hanging in plain view on its "
                "hook, and cannot think why he came. The key stays on its hook. The SERVICE door stays closed."),
    "participants": {
        "AGENT": "the Randolph station agent (Arthur Rothstein's 1937 FSA photograph, as cut out by 99-ways-template): "
                 "waistcoat, shirt sleeves, a pencil in his hand. In other media he keeps these marks: waistcoat or "
                 "shirt sleeves, a pencil, the office side of the window.",
        "STRANGER": "a woman traveller on the platform side of the ticket window (hat; Esther Bubley's 1943 figure on "
                    "photographic pages). She is never inside the office.",
    },
    "objects": {
        "MEMO": "a railway memo slip on the desk, pencilled: '4:15 - open SERVICE door. Key in cupboard.'",
        "CLOCK": "the office wall clock; it reads 4:10 when he answers",
        "TICKET_WINDOW": "the glazed ticket window between office and platform, lettered TICKET OFFICE",
        "CUPBOARD": "the office cupboard; its door opens on the left jamb",
        "BRASS_KEY": "a brass key on a hook inside the cupboard door, with a paper tag lettered SERVICE",
        "SERVICE_DOOR": "the door marked SERVICE (a card lettered SERVICE), beside the cupboard; it never opens",
        "PENCIL": "the agent's pencil; at the end it goes to his chin",
    },
    "places": ["OFFICE_DESK", "OFFICE_FLOOR", "TICKET_WINDOW", "CUPBOARD", "PLATFORM (beyond the window)"],
    "lines": {
        "question": {"speaker": "STRANGER", "text": LINES["Q"], "event": "E1"},
        "answer": {"speaker": "AGENT", "text": LINES["A"], "event": "E2"},
        "thanks": {"speaker": "STRANGER", "text": LINES["T"], "event": "E3"},
        "forgetting": {"speaker": "AGENT (to himself)", "text": LINES["F"], "event": "E5"},
    },
    "events": [
        {"id": "E0", "name": "the errand", "agent": "AGENT", "place": "OFFICE_DESK -> OFFICE_FLOOR",
         "fact": "At his desk the agent has the memo before him (open the SERVICE door at 4:15; the key is in the cupboard). "
                 "He rises and sets off across the office toward the cupboard.",
         "must_show": "the memo or an equivalent cue of the goal (the key / the SERVICE door), and his leaving the desk",
         "template_ids": ["E0", "E1"]},
        {"id": "E1", "name": "the question", "agent": "STRANGER", "place": "TICKET_WINDOW (from the platform)",
         "fact": "On his way, a stranger at the ticket window stops him: '" + LINES["Q"] + "'",
         "must_show": "a voice or figure from the platform side of the window, interrupting the walk",
         "template_ids": ["E2"]},
        {"id": "E2", "name": "the answer", "agent": "AGENT", "place": "OFFICE (by the window, under the clock)",
         "fact": "He looks at the wall clock (4:10) and answers: '" + LINES["A"] + "'",
         "must_show": "the clock or its time, and the answer from the agent",
         "template_ids": ["E3"]},
        {"id": "E3", "name": "the thanks", "agent": "STRANGER", "place": "TICKET_WINDOW -> PLATFORM",
         "fact": "She says '" + LINES["T"] + "' and leaves the window; the interruption is over.",
         "must_show": "the thanks, and the window empty afterwards (or her going)",
         "template_ids": ["E3b"]},
        {"id": "E4", "name": "the open cupboard", "agent": "AGENT", "place": "CUPBOARD",
         "fact": "He reaches the cupboard and opens it. The brass key hangs on its hook in plain view, tagged SERVICE.",
         "must_show": "the open cupboard and the key visible to him",
         "template_ids": ["E4"]},
        {"id": "E5", "name": "the forgetting", "agent": "AGENT", "place": "CUPBOARD",
         "fact": "Before the open cupboard, pencil to his chin, he asks himself '" + LINES["F"] + "' He has forgotten "
                 "the errand. The key stays on its hook; the SERVICE door stays closed.",
         "must_show": "the self-addressed line (or its declared substitute), the key unmoved, the SERVICE door closed",
         "template_ids": ["E5"]},
    ],
    "order": ["E0", "E1", "E2", "E3", "E4", "E5"],
    "causal_links": [["E0", "E4", "the errand takes him to the cupboard"],
                     ["E1", "E2", "the question demands the answer"],
                     ["E2", "E3", "the answer earns the thanks"],
                     ["E1", "E5", "the interruption displaces the errand"],
                     ["E4", "E5", "at the goal, the goal is gone"]],
    "outcome": "goal not achieved: the brass key stays on its hook; the SERVICE door stays closed",
    "invariants": [
        "the same two people, the same objects, the same order E0-E5, the same outcome",
        "the four lines are spoken by the same speakers; a page may translate, rewrite, mute or replace them ONLY if its "
        "rule says so (e.g. a lipogram rewrites them, Sounds only mutes them) and its record lists the substitution",
        "an event may be shown, implied by a stated cue, or omitted; any omission or reframing is declared in the "
        "constraint's 'declares' field and repeated in the page record",
        "a page that changes the outcome is NOT a style of this incident; the only licensed exceptions are readings "
        "the reader performs that the page itself marks as alternate (the Fold-in fold, the ghost plan), whose "
        "unfolded/actual reading keeps the canon outcome",
        "the clock reads 4:10 at the answer; the memo's appointed time is 4:15",
    ],
    "line_note": ("All four lines are the production's own. The forgetting line is deliberately ours and must never be "
                  "replaced by the referenced work's punchline or by the 99-ways-template r1 line ('Now... what did I "
                  "come over here for?'), which page 01 supersedes."),
    "derives_from": "films/swarm/99-ways-template/ledger.json revision b1 (event graph, cast, objects); lines renewed here",
}

KIT = {
    "photo-cutout": {"kit": "Rothstein 1937 station agent + clock, Bubley 1943 stranger, ANRC 1922 key cut as photo pieces with "
                            "white scissor margins on the LoC 1934 sheet",
                     "where": ["films/swarm/99-ways-template/page/", "films/sources/99-ways-template/page-cartoonist/pieces/",
                               "films/swarm/99-ways-template/page/rest/P1..P8 (rest layers)"],
                     "credits": "films/credits/99-ways-template.json"},
    "paper-hands": {"kit": "lightbox paper hands and objects (first-person hands)",
                    "where": ["films/swarm/99-ways-subjective/test-shot-build/", "films/sources/99-ways-subjective/"],
                    "credits": "films/swarm/99-ways-subjective/ (test-shot-ledger.json; no films/credits file yet: carry from ledger)"},
    "shadow-puppet": {"kit": "black cut-paper articulated silhouette puppets, shadow screens and station panels",
                      "where": ["films/swarm/quatre-vingt-quinze/puppets/", "films/swarm/cercle-vicieux/",
                                "films/sources/quatre-vingt-quinze/", "films/sources/cercle-vicieux/"],
                      "credits": "films/credits/quatre-vingt-quinze.json (+ cercle-vicieux ledger)"},
    "brush-plate": {"kit": "one repeated ink brush plate with written balloons",
                    "where": ["films/swarm/moins-dun-quart-de-seconde-pour-vivre/", "films/sources/moins-dun-quart-de-seconde-pour-vivre/"],
                    "credits": "films/credits/moins-dun-quart-de-seconde-pour-vivre.json"},
    "daumier-collage": {"kit": "Daumier lithograph cutouts (CC0), glued collage",
                        "where": ["films/swarm/boucle-la/", "films/sources/boucle-la/"],
                        "credits": "films/credits/boucle-la.json"},
    "busch-fold": {"kit": "Wilhelm Busch 1865 picture plates, fold tabletop",
                   "where": ["films/swarm/les-caids-de-la-gaudriole/", "films/sources/les-caids-de-la-gaudriole/"],
                   "credits": "films/credits/les-caids-de-la-gaudriole.json"},
    "engraving-puppet": {"kit": "cut-paper engraving puppets on a storyboard sheet with pasted commentary slips",
                         "where": ["films/swarm/bang-bang/", "films/sources/bang-bang/"],
                         "credits": "films/credits/bang-bang.json"},
    "rol-cutout": {"kit": "Agence Rol press-photo cutouts and the cover-page grammar",
                   "where": ["films/swarm/exercices-de-style/", "films/sources/exercices-de-style/"],
                   "credits": "films/credits/exercices-de-style.json"},
    "charcoal-card": {"kit": "articulated charcoal cut-card puppets on a foraged wall/rock ground",
                      "where": ["films/swarm/teuf-teuf/", "films/sources/teuf-teuf/"],
                      "credits": "films/credits/teuf-teuf.json"},
    "spiral-disc": {"kit": "rotating discs: spirals, ring discs, lettering on a turning disc",
                    "where": ["films/swarm/anemic-cinema/", "films/sources/anemic-cinema/"],
                    "credits": "films/credits/anemic-cinema.json"},
    "stencil-dye": {"kit": "stencil cut-outs printed in flat dye colours",
                    "where": ["films/swarm/la-belle-hortense/", "films/sources/la-belle-hortense/"],
                    "credits": "films/credits/la-belle-hortense.json"},
    "pen-hand": {"kit": "the shared HANDMADE single-stroke pen hand (lettering and line drawing only) on the LoC 1934 sheet",
                 "where": ["films/swarm/99-ways/kit/pen99.py", "films/swarm/99-ways/kit/glyphs99.json",
                           "films/swarm/99-ways-template/page/penlib.py"],
                 "credits": "films/credits/99-ways-template.json (LoC 1934 sheet); lettering handmade"},
    "cut-paper": {"kit": "HANDMADE flat cut paper made in code (scissor-faceted shapes, one paper shadow) on the LoC 1934 sheet",
                  "where": ["films/swarm/99-ways-template/page/penlib.py (scissor, shadow_onto, place)"],
                  "credits": "films/credits/99-ways-template.json (LoC 1934 sheet); shapes handmade"},
}

FAM = {
    "layout": "layout and page grammar", "pov": "point of view", "time": "time and order", "voice": "voice and language",
    "genre": "genre", "medium": "medium and material", "scale": "reduction and expansion",
    "oulipo": "formal / Oulipian rule", "reader": "reader and object",
}

# (id, title, rule, medium, check, declares, anim)   -- order inside each family = order of appearance
C = {
 "layout": [
  ("template", "Template", "Eight panels, an objective eye-level view, every event E0-E5 shown in order with the four canonical lines.",
   "photo-cutout", "A reader retells E0-E5 in order from the page alone and names who speaks each line.", "", True),
  ("polyptych", "Polyptych", "One continuous drawing of the office runs behind all the panels; the borders cut it into moments and the agent recurs in each.",
   "charcoal-card", "A reader can join the panel backgrounds into one unbroken room.", "", True),
  ("nine-cells", "Nine cells", "A strict 3x3 grid of equal cells, one beat or held pause per cell, no cell larger than another.",
   "shadow-puppet", "A reader counts nine cells of identical size.", "", False),
  ("one-room-one-picture", "One room, one picture", "The whole incident in a single panel: the agent appears several times along his path through one continuous office.",
   "photo-cutout", "A reader finds the agent more than once in one frame and orders his appearances E0 to E5.", "", True),
  ("one-column", "One column", "Ten or more wide, shallow panels stacked in a single column, read top to bottom like a storyboard.",
   "engraving-puppet", "A reader sees one column of panels and no side-by-side panels.", "", True),
  ("clock-face", "Clock face", "Twelve panels arranged round a circle like the hours of the station clock, read clockwise from twelve.",
   "spiral-disc", "A reader starts at the top panel and reads clockwise; the forgetting sits just before twelve again.", "", True),
  ("window-in-window", "Window in a window", "Each panel sits inside the previous one, closing in from the station front to the key on its hook.",
   "cut-paper", "A reader sees each panel framed inside the last, the frames nesting toward the key.", "", True),
  ("no-borders", "No borders", "No panel frames: figures, objects and balloons float on the page, ordered only by placement and tails.",
   "daumier-collage", "No ruled frame line appears anywhere on the page.", "", False),
  ("stairs", "Stairs", "Panels step diagonally from top left to bottom right, each lower than the last, a staircase down into forgetting.",
   "brush-plate", "Every panel's top edge is lower than the previous panel's.", "", False),
  ("cover", "Cover", "The incident told as the front cover of a 1937 story paper: masthead, one dramatic picture, cover lines that carry E0-E5.",
   "rol-cutout", "A reader identifies a masthead and cover lines and can still retell the incident.",
   "E1-E3 carried by cover lines rather than drawn", False),
  ("dealt-cards", "Dealt cards", "Panels overlap like cards dealt one on another; each later beat partly covers the earlier, the last lies uncovered.",
   "paper-hands", "A reader orders the panels by which one lies on top.", "", True),
 ],
 "pov": [
  ("the-key-waits", "The key waits", "Told from the brass key's place on its hook inside the closed cupboard: dark slits of light and voices until the door opens on E4.",
   "cut-paper", "A reader says the viewer is inside the cupboard; the inside of the cupboard door frames every panel.",
   "E0-E3 known only through cracks of light and lettered sound", True),
  ("through-his-eyes", "Through his eyes", "Every panel is the agent's own view: his hands and pencil are seen, never his face; the stranger is heard and glimpsed through the glass.",
   "paper-hands", "A reader names whose eyes these are; the agent's face never appears.", "", True),
  ("from-the-platform", "From the platform", "The whole incident watched from the stranger's side of the ticket window; office events after E3 seen only through the glass.",
   "photo-cutout", "A reader says the viewer stands outside on the platform.", "E4-E5 seen only through the window glass, the line read through it", False),
  ("clocks-eye", "The clock's eye", "Seen from the wall clock: one fixed high downward view, the clock's own hand edging into the panel border.",
   "engraving-puppet", "A reader says the view is from high on the wall, where the clock hangs.", "", False),
  ("plan-view", "Plan view", "Straight-down overhead view of office and platform as a floor plan; people are hat-tops and shoulders, the walk a dotted track.",
   "cut-paper", "No wall is seen standing up; a reader traces the agent's path as a line.", "", True),
  ("floorboard", "Floorboard", "Camera at floor level: boots, chair legs, the stranger's hem beyond the counter; no face ever enters.",
   "shadow-puppet", "No figure is seen above the waist; a reader still retells E0-E5.", "faces and the key's hook seen from below", False),
  ("one-fixed-lens", "One fixed lens", "One unmoving viewpoint repeated in every panel; only the figures, the clock and the cupboard door change.",
   "brush-plate", "Every panel's background drawing is identical.", "", True),
  ("the-porter-saw", "The porter saw", "A porter on the platform bench watches it all and gives his partial account in captions; he cannot see into the cupboard.",
   "daumier-collage", "A reader names a witness who is neither agent nor stranger.",
   "adds a witness (the porter); E4-E5 reported as he guesses them", False),
  ("keyhole", "Through the keyhole", "Seen from inside the SERVICE room through its keyhole: every panel is masked by the keyhole shape, and the door never opens.",
   "stencil-dye", "Every panel has a keyhole-shaped opening; a reader says the viewer is behind the SERVICE door.",
   "E0 memo and E4 key only partly in view through the keyhole", True),
  ("station-cat", "The station cat", "Told by the station cat on the counter, whose attention keeps drifting to the clock pendulum; the human events sit at the edge of its interest.",
   "busch-fold", "A reader names the cat as the one watching.", "adds a cat; human lines heard, not focused on", False),
  ("across-the-tracks", "Across the tracks", "Seen from the far platform: the station a small lit box, the figures tiny in its windows, the balloons long-tailed across the rails.",
   "charcoal-card", "A reader says the viewer is across the rails and far away.", "", False),
 ],
 "time": [
  ("backwards", "Backwards", "The beats are drawn in reverse order, E5 first and E0 last, but each panel reads normally.",
   "engraving-puppet", "The first panel shows the forgetting; the last shows the memo.", "", False),
  ("jump-cuts", "Jump cuts", "Consecutive panels skip unequal stretches of time, each gap stated in a caption ('three seconds later', 'forty seconds later').",
   "shadow-puppet", "Every panel after the first carries a stated time gap, and no two gaps are equal.", "", False),
  ("by-the-clock", "By the clock", "Every panel shows the clock, and the time between panels is a constant ten seconds, 4:09:20 to 4:10:30.",
   "photo-cutout", "A reader reads a time in every panel, rising by equal steps.", "", True),
  ("told-at-dusk", "Told at dusk", "Framed at six in the evening: the agent at the still-closed door recalls the afternoon; the incident sits in panels inside a remembering frame.",
   "rol-cutout", "A reader can separate the evening frame from the afternoon panels.", "adds an evening frame after E5", False),
  ("the-plan", "The plan", "Each panel pairs what the 4:15 memo planned, ghosted in pale ink, with what happened; the ghost door opens, the real one stays shut.",
   "pen-hand", "A reader tells the ghosted (planned) figure from the solid (actual) one in every panel.",
   "adds an unrealised planned strand, marked as ghost", True),
  ("loop", "Loop", "The last panel leads back into the first: he returns to the desk, reads the memo and sets off again, so the page reads round forever.",
   "daumier-collage", "A reader can continue from the last panel straight into the first.", "E0 repeated after E5 (the loop seam)", True),
  ("meanwhile", "Meanwhile", "Two parallel tiers: the office above, the platform below, showing what the stranger does during each of the agent's beats.",
   "busch-fold", "A reader reads the two tiers as simultaneous and matches upper and lower panels.",
   "adds the stranger's platform actions (her arrival, waiting, train)", False),
  ("dawn-to-dark", "Dawn to dark", "Twelve views of the same cupboard wall across one day; the incident fills one of them, light and clock change in all.",
   "stencil-dye", "Light and clock change in every panel; the incident happens in only one.",
   "E0-E3 compressed into the 4 pm view", True),
  ("the-long-beat", "The long beat", "Five of eight panels are given to E5: the same pose with minimal changes while the errand drains away.",
   "brush-plate", "A reader counts five near-identical closing panels.", "E0-E3 compressed into three panels", True),
  ("pendulum", "Pendulum", "Each panel is one swing of the clock's pendulum, which crosses every gutter; the count of swings is the page's only measure of time.",
   "spiral-disc", "A reader sees the pendulum alternate sides from panel to panel.", "", True),
  ("thirty-years-on", "Thirty years on", "The office in 1967, disused: the key still on its hook, the door still closed; the 1937 beats appear as pale figures in the same room.",
   "charcoal-card", "A reader tells the two times apart and finds the key in both.", "frames the incident in 1967", False),
 ],
 "voice": [
  ("her-version", "Her version", "The stranger tells it later to a fellow passenger on the train: chatty captions in her voice, over pictures of what she saw.",
   "rol-cutout", "A reader names the stranger as narrator.", "E4-E5 told as she imagines them", False),
  ("telegram", "Telegram", "All captions in telegraphese: no articles, every sentence ends STOP.",
   "cut-paper", "Every caption sentence ends with STOP; no 'a' or 'the' appears in the captions.", "", False),
  ("talks-himself-through", "He talks himself through it", "The agent narrates every step aloud in his own balloons, from the memo to the forgetting.",
   "photo-cutout", "Every panel has a balloon tailed to the agent.", "", False),
  ("you", "You", "Captions address the reader as the agent, in the second person, present tense.",
   "paper-hands", "Every caption contains 'you'; a reader says who 'you' is.", "", False),
  ("form-99", "Form 99", "The incident told only as a railway incident report form, its printed fields filled in pencil, with the form's own sketch box.",
   "pen-hand", "A reader finds printed field names and the events in the answers.", "lines quoted in a 'statements' field", False),
  ("epic", "Epic", "Captions in an inflated heroic register: the errand a quest, the cupboard a vault, the question a summons.",
   "engraving-puppet", "A reader names the register as heroic or epic.", "", False),
  ("only-questions", "Only questions", "Every caption and balloon is a question; even the answer and the thanks are offered as questions.",
   "shadow-puppet", "Every sentence on the page ends with a question mark.",
   "answer and thanks recast as questions (same content, same speakers)", False),
  ("not-unlike", "Not unlike", "Every caption states its fact by denying the opposite ('He was not idle').",
   "brush-plate", "Every caption contains 'not' or 'no'.", "", False),
  ("inner-voice", "Inner voice", "The agent's thoughts run in cloud balloons beside the spoken lines; we watch the errand leave his head.",
   "daumier-collage", "A reader points to the thought balloons and to the panel where the errand leaves them.", "", True),
  ("sounds-only", "Sounds only", "No words at all: the story is told in sound lettering (scrape, tick, tap, creak); the lines become wordless balloons with their rhythm.",
   "charcoal-card", "No word of dialogue appears; a reader still finds question, answer, thanks and forgetting.",
   "the four lines muted (shape and rhythm only)", True),
  ("ballad", "Ballad", "Each panel carries one rhymed couplet; the page is a ballad of eight couplets.",
   "stencil-dye", "Each caption is two rhyming lines.", "lines set to rhyme inside the couplets", False),
 ],
 "genre": [
  ("noir", "Noir", "Hardboiled first-person narration, blind-slat light, the brass key as the thing that matters.",
   "shadow-puppet", "A reader names the genre as crime or noir.", "", False),
  ("showdown", "Showdown", "Framed as a frontier standoff at the ticket window, hands at the hip, the clock as the duel's timer.",
   "engraving-puppet", "A reader names the genre as western.", "", False),
  ("once-upon-a-time", "Once upon a time", "A fairy tale: the forbidden door, the enchanted key, the stranger as a fairy who takes his memory with a question.",
   "busch-fold", "The text begins 'Once upon a time' and a reader names the genre.", "", False),
  ("intertitles", "Intertitles", "A silent picture: pantomime panels alternate with ornate title cards carrying the lines.",
   "rol-cutout", "No balloon appears; every line is on a title card between pictures.", "", True),
  ("the-case", "The case of the closed door", "A detective arrives at 4:30 and reconstructs the forgetting from clues: memo, clock, open cupboard.",
   "photo-cutout", "A reader names the detective and the three clues.", "frames E0-E5 as a reconstruction after the fact", False),
  ("the-cupboard", "The cupboard", "Shot as horror: creeping dread toward the cupboard, a shock cut to the hanging key, and the horror is the blank.",
   "charcoal-card", "A reader names the genre as horror.", "", True),
  ("brief-meeting", "Brief meeting", "Played as romance: glances through the glass, a lingering thanks, the lost errand as a heart's distraction.",
   "daumier-collage", "A reader names the genre as romance.", "", False),
  ("picture-book", "Picture book", "A children's picture book: large flat shapes, one simple sentence per panel.",
   "cut-paper", "Each panel has exactly one short sentence.", "", False),
  ("how-to-forget", "How to forget a key", "An instruction sheet: numbered steps and arrowed diagrams teach the reader to forget a key.",
   "pen-hand", "A reader finds numbered imperative steps.", "", False),
  ("libretto", "Libretto", "An opera: the lines set as sung parts under ruled staves, with stage directions.",
   "stencil-dye", "A reader finds staves, role names and stage directions.", "", False),
  ("double-take", "Double take", "Vaudeville timing: a double take at the clock, a near miss with the cupboard door, no fall; the gag is the forgetting.",
   "brush-plate", "A reader finds the double take (two consecutive head turns to the clock).", "", True),
 ],
 "medium": [
  ("turntable", "Turntable", "The beats are printed round a slotted disc that, spun, animates the walk; the page shows the disc and its reading slots.",
   "spiral-disc", "A reader finds the beats in order round the disc.", "", True),
  ("lamp-shadows", "Lamp shadows", "Only the shadows the lamp throws on the office wall tell the story; the people themselves are never seen.",
   "shadow-puppet", "No figure appears except as a shadow on a wall.", "", True),
  ("two-colour-stencil", "Two-colour stencil", "Only stencilled shapes in two dyes: no outline, no shading.",
   "stencil-dye", "A reader counts two ink colours and finds no drawn outline.", "", False),
  ("wall-drawing", "Wall drawing", "Drawn in charcoal on the plaster of the station wall, the cupboard and the SERVICE door being real parts of that wall.",
   "charcoal-card", "A reader says the story is drawn on a wall.", "", False),
  ("picture-sheet", "Picture sheet", "A 19th-century picture sheet: a grid of plate pictures, a printed verse under each.",
   "busch-fold", "Every picture has a verse below it and no balloon.", "lines quoted inside the verses", False),
  ("engraved-plate", "Engraved plate", "A steel-engraved catalogue plate: figures and objects numbered and named in a lettered key ('Fig. 4, the key').",
   "engraving-puppet", "A reader finds numbered figures and a key that names them.", "", False),
  ("stone", "Stone", "A one-tone satirical lithograph with a caption beneath, the agent as a type of officialdom.",
   "daumier-collage", "A reader names the print as satire and finds one tone.", "E0-E5 in at most four pictures", False),
  ("front-page", "Front page", "A newspaper page: headline, a press photograph, a column of report and captions.",
   "rol-cutout", "A reader finds a headline and a news column carrying the events.", "", False),
  ("lightbox", "Lightbox", "Translucent papers laid one over another: each later beat on a new sheet, all visible at once in fading strength.",
   "paper-hands", "A reader sees earlier beats show through later ones.", "", True),
  ("pen-alone", "Pen alone", "The whole page drawn in the shared pen hand alone: one line weight, no tone, no fill.",
   "pen-hand", "Only pen lines of one weight appear.", "", False),
  ("ticket-stock", "Ticket stock", "Told on a strip of railway card tickets, one beat per ticket, dated, numbered and punched.",
   "cut-paper", "A reader reads the tickets in number order and finds E0-E5.", "", False),
 ],
 "scale": [
  ("two-panels", "Two panels", "The incident in two panels only: before the question, and at the cupboard.",
   "brush-plate", "A reader counts two panels and still retells E0-E5.", "E1-E3 and E4 compressed into two panels", False),
  ("close-ups", "Close-ups only", "Only extreme close-ups: hand, mouth, clock hand, latch, key, eye, pencil at the chin.",
   "photo-cutout", "No panel shows a whole figure.", "", True),
  ("thirty-two", "Thirty-two panels", "Every micro-action drawn: thirty-two small panels.",
   "engraving-puppet", "A reader counts thirty-two panels.", "", True),
  ("from-the-hill", "From the hill", "Extreme long shots: the station small in its Vermont valley, the balloons reaching across the land.",
   "charcoal-card", "No figure is taller than a tenth of its panel.", "", False),
  ("six-words", "Six words", "Six panels, each captioned with a single word; no balloons.",
   "pen-hand", "A reader counts exactly six words on the page outside the margin.", "the four lines replaced by six single words", False),
  ("fewest-marks", "Fewest marks", "Each figure and object made of the fewest cut shapes that keep the incident readable.",
   "cut-paper", "A reader can count the shapes in each figure (no more than five).", "", False),
  ("blank-middle", "Blank middle", "Only the first and last beats are pictured; the middle panels are bare paper carrying only the balloons.",
   "shadow-puppet", "A reader finds pictures only in the first and last panels.", "E1-E4 carried by balloons in empty panels", False),
  ("footnotes", "Footnotes", "The incident in small panels across the top third; the rest of the page is numbered footnotes on every object and word.",
   "pen-hand", "A reader finds footnote numbers in the panels and the notes below.", "", False),
  ("the-morning-before", "The morning before", "The day from dawn to four is compressed into the top two tiers; the incident itself fits in the bottom tier.",
   "rol-cutout", "A reader finds E0-E5 only in the bottom tier.", "adds the morning (how the memo came)", False),
  ("stutter", "Stutter", "Every beat is drawn twice in a row, the second slightly altered, the errand already fading.",
   "brush-plate", "A reader finds panels in near-identical pairs.", "", True),
  ("inventory", "Inventory", "Every object of the incident laid out as a labelled specimen chart; numbered threads tell the story in order.",
   "busch-fold", "A reader follows the numbers from object to object to retell the incident.", "people shown only as their objects and lines", False),
 ],
 "oulipo": [
  ("without-e", "Lipogram", "No letter e anywhere on the page, folio title included; the four lines are rewritten to fit.",
   "stencil-dye", "No letter e (upper or lower case) appears anywhere, folio title included.", "lines rewritten without e", False),
  ("panel-palindrome", "Panel palindrome", "Compositions mirror about the middle: panel k and panel 9-k share their layout, so the page folded across its middle matches itself.",
   "shadow-puppet", "Folding the page across its middle, each panel lies on a panel of the same composition.", "", True),
  ("snowball", "Snowball", "Caption n has exactly n words, one to eight.",
   "shadow-puppet", "A reader counts 1, 2, 3 ... 8 words in the captions.", "", False),
  ("short-words", "Short words", "Every word on the page has one syllable.",
   "daumier-collage", "No word on the page has two syllables.", "lines rewritten in one-syllable words", False),
  ("a-to-z", "A to Z", "Twenty-six small captions in order, the first word of each beginning with the next letter of the alphabet.",
   "engraving-puppet", "The caption initials run A to Z.", "", False),
  ("n-plus-seven", "N+7", "Every noun of the captions and lines replaced by the seventh noun after it in our own station glossary, printed in the margin.",
   "pen-hand", "A reader checks any noun against the glossary: it is seven places on.", "lines transformed by N+7", False),
  ("fold-in", "Fold-in", "Folding the page along its marked lines hides the interruption and joins departure to cupboard, making a story in which he remembers.",
   "busch-fold", "Unfolded the page keeps the canon; folded it shows the agent taking the key.",
   "the folded reading is a marked alternate (outcome changed only when folded)", True),
  ("crossing-routes", "Crossing routes", "A 3x3 grid read across tells the agent's story and read down tells the stranger's; both meet in the centre cell at the question.",
   "shadow-puppet", "Rows and columns each make sense; the centre cell is the question.", "", False),
  ("prisoner", "Prisoner's text", "All text uses only letters without ascenders or descenders (a c e m n o r s u v w x z), lines included.",
   "pen-hand", "Outside the folio line, no letter with an ascender or descender appears.", "lines rewritten in the restricted letters", False),
  ("tautogram-k", "Tautogram", "Every word of every caption begins with K.",
   "cut-paper", "Every caption word begins with K.", "lines rewritten as K-words", False),
  ("ninety-nine-words", "Ninety-nine words", "The page's text, folio and title excluded, totals exactly ninety-nine words, tallied in the margin.",
   "photo-cutout", "A reader counts ninety-nine words.", "", False),
 ],
 "reader": [
  ("the-memo", "The memo itself", "The page is the agent's memo slip, both sides, the incident told in his notes, crossings-out and one doodle.",
   "pen-hand", "A reader says the page is the memo, and finds E0-E5 in its notes.", "E1-E5 as his later notes", False),
  ("through-the-flap", "Lift the flap", "The cupboard door is a flap the reader lifts to find the key; other flaps hide the clock and the stranger.",
   "cut-paper", "A reader lifts (or sees lifted, on the film) each flap in order.", "", True),
  ("out-of-order", "Out of order", "Panels are scattered across the page; small numbers give the reading order.",
   "photo-cutout", "A reader follows the numbers and retells E0-E5 in order.", "", False),
  ("fill-the-balloons", "Fill the balloons", "Every balloon is empty; the four lines wait in the margin as cut-out slips with tabs to place.",
   "pen-hand", "A reader matches each slip to its balloon.", "lines given as loose slips", True),
  ("spot-the-difference", "Spot the difference", "Two near-identical tiers: the agent at the cupboard before and after the forgetting; the reader finds the changes.",
   "rol-cutout", "A reader finds the stated number of differences.", "E0-E3 in a strip above", False),
  ("flip-corner", "Flip corner", "A small flip sequence runs down the page's outer corner; flipped, it animates the forgetting.",
   "paper-hands", "A reader finds the corner sequence and its frame numbers.", "", True),
  ("quarter-turns", "Quarter turns", "Each tier is lettered in a different orientation; the reader turns the page a quarter turn per tier.",
   "spiral-disc", "Each tier reads upright only after a quarter turn.", "", True),
  ("mirror", "Mirror", "All lettering is mirror-reversed; the page reads true in a mirror.",
   "stencil-dye", "Outside the folio line, every word reads correctly only in a mirror.", "", False),
  ("find-the-key", "Find the key", "One crowded panel of the station afternoon; a legend asks the reader to find the six beats in order.",
   "busch-fold", "A reader finds all six beats in the crowded picture.", "", False),
  ("marginalia", "Marginalia", "Page 01 reprinted small with an annotator's pencil notes pointing to the evidence for each event.",
   "photo-cutout", "A reader finds a note pointing to every event E0-E5.", "", False),
  ("questions-for-you", "Questions for the reader", "Beside each panel a paper hand points to a printed question for the reader ('Where is the key now?'); the answers run upside down at the foot.",
   "paper-hands", "A reader answers each question from the panels alone, then checks the upside-down answers.", "", True),
 ],
}

ORDER = ["layout", "pov", "time", "voice", "genre", "medium", "scale", "oulipo", "reader"]
assert all(len(C[f]) == 11 for f in ORDER)

# spread media: permute each family's pages 2..11 (the first round is chosen by hand) so that no medium appears
# more than twice in any batch of eleven. Deterministic local search.
import random as _r
def _seq(CC):
    return [CC[f][i] for i in range(11) for f in ORDER]
def _cost(CC):
    q = _seq(CC)
    cost = 0
    for b in range(9):
        cnt = {}
        for it in q[11 * b:11 * b + 11]:
            cnt[it[3]] = cnt.get(it[3], 0) + 1
        cost += sum(max(0, v - 2) * 10 + max(0, v - 1) for v in cnt.values())
    return cost
_rng = _r.Random(99)
best = _cost(C)
for _ in range(60000):
    f = _rng.choice(ORDER)
    i, j = _rng.sample(range(1, 11), 2)
    C[f][i], C[f][j] = C[f][j], C[f][i]
    c2 = _cost(C)
    if c2 <= best:
        best = c2
    else:
        C[f][i], C[f][j] = C[f][j], C[f][i]
print("media spread cost", best)

cons = []
for i in range(11):
    for f in ORDER:
        cid, title, rule, med, check, decl, anim = C[f][i]
        cons.append(dict(id=cid, title=title, family=FAM[f], rule=rule, medium=med, check=check,
                         declares=decl or "keeps E0-E5, the four lines and the outcome", animation_friendly=anim))
for n, c in enumerate(cons, 1):
    c["n"] = n
    c["folio"] = f"{n:02d}"
    c["file"] = f"assets/pages/99-ways/{n:02d}-{c['id']}.jpg"
assert len(cons) == 99 and len({c["id"] for c in cons}) == 99 and cons[0]["id"] == "template"
from collections import Counter
mc = Counter(c["medium"] for c in cons)
assert max(mc.values()) <= 20, mc
batches = [list(range(1 + 11 * b, 12 + 11 * b)) for b in range(9)]

canon = {
    "work": "99 ways",
    "frozen": True,
    "revision": "c1",
    "date": "2026-11-17",
    "owner": "canon-editor",
    "note": "Frozen once written. Propose changes in films/swarm/99-ways/amendments.md; never edit this file.",
    "lineage": "after Queneau's Exercices de style (1947) and Matt Madden's 99 Ways to Tell a Story (2005); "
               "no page, panel composition, line or list of theirs is reproduced",
    "incident": INCIDENT,
    "base_page": {
        "n": 1, "id": "template", "file": "assets/pages/99-ways/01-template.jpg",
        "master": "films/sources/99-ways/masters/01-template.png",
        "built_by": "films/swarm/99-ways/kit/build_page01.py",
        "from": "films/swarm/99-ways-template/page/rest/P1..P8 rest layers (b1 r2 photo-comic page); balloons re-lettered with the c1 lines",
        "panels": {"P1": "E0 memo on desk, agent seated", "P2": "E0 desk left, agent rising out of frame",
                   "P3": "E0 agent walking past the closed cupboard and SERVICE card", "P4": "E1 question through the ticket window",
                   "P5": "E2 answer under the clock at 4:10", "P6": "E3 thanks from the emptied window",
                   "P7": "E4 cupboard open, key on its hook", "P8": "E5 the forgetting line; key unmoved; SERVICE door closed"},
    },
    "page_spec": {
        "size_px": [2200, 2850], "orientation": "portrait", "jpeg_quality": 90, "target_bytes": [400000, 1200000],
        "master": "films/sources/99-ways/masters/NN-<id>.png",
        "beats": "films/sources/99-ways/beats/NN/b01.png ... (4-8 sequential states at 960x1242 showing the defining change)",
        "record": "films/swarm/99-ways/pages/NN.json {n, id, title, rule, medium, sources:[credit ids], made:[...], beat, self_check}",
        "margin": "live area x 110-2090, y 110-2730; the band y 2740-2850 is reserved for the folio line",
        "folio": "drawn by films/swarm/99-ways/kit/pen99.py folio(): the constraint title at bottom left (x=110) and the "
                 "two-digit folio at bottom right (right edge x=2090), baseline y=2800, cap 34 px, ink #121110, in the "
                 "shared HANDMADE pen hand; identical on all 99 pages",
        "paper": "the LoC 1934 Federal Theatre Project blank sheet (penlib.sheet) is the default ground; a page may use its kit's own ground",
        "credits": "films/credits/99-ways.json (append, never rewrite others' entries); credit id = '<kit-slug>:<short-name>'",
    },
    "media": KIT,
    "media_counts": dict(sorted(mc.items(), key=lambda kv: -kv[1])),
    "families": {FAM[f]: [c["n"] for c in cons if c["family"] == FAM[f]] for f in ORDER},
    "ordering_logic": ("Nine families are dealt in rounds: each round passes once through every family in the same order "
                       "(layout, point of view, time, voice, genre, medium, reduction/expansion, formal rule, reader), so any "
                       "eleven consecutive pages hold all nine families. The first round (pages 1-9) was chosen by hand to open "
                       "with nine different media; after it, each family's order is set so that no medium appears more than "
                       "twice in any batch of eleven, which keeps every batch a fair sample of families and media."),
    "constraints": cons,
    "batches": batches,
}
json.dump(canon, open(OUT_J, "w"), indent=1, ensure_ascii=False)

# ------------------------------------------------------------------ readable canon.md
md = [f"# 99 ways: the canon (revision c1, frozen)", "",
      "Frozen once written. Propose changes in `amendments.md`; never edit this file or `canon.json`.", "",
      "## The incident: *The SERVICE key*", "", INCIDENT["summary"], "",
      "| Event | What happens | Line |", "|---|---|---|"]
lk = {v["event"]: f"{v['speaker']}: “{v['text']}”" for v in INCIDENT["lines"].values()}
for e in INCIDENT["events"]:
    md.append(f"| {e['id']} {e['name']} | {e['fact']} | {lk.get(e['id'], '')} |")
md += ["", f"**Outcome:** {INCIDENT['outcome']}.", "", "**Invariants**", ""] + [f"- {x}" for x in INCIDENT["invariants"]]
md += ["", f"*{INCIDENT['line_note']}*", "", "**Cast and objects**", ""]
md += [f"- **{k}**: {v}" for k, v in {**INCIDENT["participants"], **INCIDENT["objects"]}.items()]
md += ["", "## Page 01, the base page", "",
       "Eight panels, objective, rebuilt from the 99-ways-template rest layers with the c1 lines. " +
       " ".join(f"{k}: {v}." for k, v in canon["base_page"]["panels"].items()), "",
       "## Page spec", ""] + [f"- **{k}**: {v}" for k, v in canon["page_spec"].items()]
md += ["", "## Media", "", "| Medium | Kit | Pages |", "|---|---|---|"]
for m, d in KIT.items():
    md.append(f"| {m} | {d['kit']} | {mc[m]} |")
md += ["", "## Ordering", "", canon["ordering_logic"], "", "## The 99", ""]
for b, bl in enumerate(batches, 1):
    md += [f"### Batch {b} (pages {bl[0]}-{bl[-1]})", "", "| NN | Title | Family | Medium | Rule | Check | Declares |",
           "|---|---|---|---|---|---|---|"]
    for n in bl:
        c = cons[n - 1]
        md.append(f"| {n:02d} | {c['title']}{' (anim)' if c['animation_friendly'] else ''} | {c['family']} | {c['medium']} | "
                  f"{c['rule']} | {c['check']} | {c['declares']} |")
    md.append("")
OUT_M.write_text("\n".join(md))
print("wrote", OUT_J, OUT_M, dict(mc))

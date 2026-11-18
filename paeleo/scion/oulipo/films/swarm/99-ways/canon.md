# 99 ways: the canon (revision c1, frozen)

Frozen once written. Propose changes in `amendments.md`; never edit this file or `canon.json`.

## The incident: *The SERVICE key*

Randolph station, Vermont, a September afternoon in 1937. The station agent's memo says the SERVICE door is to be opened at 4:15 with the brass key kept in the office cupboard. He gets up to fetch it. On his way a stranger at the ticket window asks him the time; he looks at the wall clock and tells her; she thanks him and goes. He reaches the cupboard, opens it, and stands before the brass key hanging in plain view on its hook, and cannot think why he came. The key stays on its hook. The SERVICE door stays closed.

| Event | What happens | Line |
|---|---|---|
| E0 the errand | At his desk the agent has the memo before him (open the SERVICE door at 4:15; the key is in the cupboard). He rises and sets off across the office toward the cupboard. |  |
| E1 the question | On his way, a stranger at the ticket window stops him: 'Pardon me — have you the right time?' | STRANGER: “Pardon me — have you the right time?” |
| E2 the answer | He looks at the wall clock (4:10) and answers: 'Ten past four, by the clock.' | AGENT: “Ten past four, by the clock.” |
| E3 the thanks | She says 'Much obliged!' and leaves the window; the interruption is over. | STRANGER: “Much obliged!” |
| E4 the open cupboard | He reaches the cupboard and opens it. The brass key hangs on its hook in plain view, tagged SERVICE. |  |
| E5 the forgetting | Before the open cupboard, pencil to his chin, he asks himself 'Well, here I am... and what for?' He has forgotten the errand. The key stays on its hook; the SERVICE door stays closed. | AGENT (to himself): “Well, here I am... and what for?” |

**Outcome:** goal not achieved: the brass key stays on its hook; the SERVICE door stays closed.

**Invariants**

- the same two people, the same objects, the same order E0-E5, the same outcome
- the four lines are spoken by the same speakers; a page may translate, rewrite, mute or replace them ONLY if its rule says so (e.g. a lipogram rewrites them, Sounds only mutes them) and its record lists the substitution
- an event may be shown, implied by a stated cue, or omitted; any omission or reframing is declared in the constraint's 'declares' field and repeated in the page record
- a page that changes the outcome is NOT a style of this incident; the only licensed exceptions are readings the reader performs that the page itself marks as alternate (the Fold-in fold, the ghost plan), whose unfolded/actual reading keeps the canon outcome
- the clock reads 4:10 at the answer; the memo's appointed time is 4:15

*All four lines are the production's own. The forgetting line is deliberately ours and must never be replaced by the referenced work's punchline or by the 99-ways-template r1 line ('Now... what did I come over here for?'), which page 01 supersedes.*

**Cast and objects**

- **AGENT**: the Randolph station agent (Arthur Rothstein's 1937 FSA photograph, as cut out by 99-ways-template): waistcoat, shirt sleeves, a pencil in his hand. In other media he keeps these marks: waistcoat or shirt sleeves, a pencil, the office side of the window.
- **STRANGER**: a woman traveller on the platform side of the ticket window (hat; Esther Bubley's 1943 figure on photographic pages). She is never inside the office.
- **MEMO**: a railway memo slip on the desk, pencilled: '4:15 - open SERVICE door. Key in cupboard.'
- **CLOCK**: the office wall clock; it reads 4:10 when he answers
- **TICKET_WINDOW**: the glazed ticket window between office and platform, lettered TICKET OFFICE
- **CUPBOARD**: the office cupboard; its door opens on the left jamb
- **BRASS_KEY**: a brass key on a hook inside the cupboard door, with a paper tag lettered SERVICE
- **SERVICE_DOOR**: the door marked SERVICE (a card lettered SERVICE), beside the cupboard; it never opens
- **PENCIL**: the agent's pencil; at the end it goes to his chin

## Page 01, the base page

Eight panels, objective, rebuilt from the 99-ways-template rest layers with the c1 lines. P1: E0 memo on desk, agent seated. P2: E0 desk left, agent rising out of frame. P3: E0 agent walking past the closed cupboard and SERVICE card. P4: E1 question through the ticket window. P5: E2 answer under the clock at 4:10. P6: E3 thanks from the emptied window. P7: E4 cupboard open, key on its hook. P8: E5 the forgetting line; key unmoved; SERVICE door closed.

## Page spec

- **size_px**: [2200, 2850]
- **orientation**: portrait
- **jpeg_quality**: 90
- **target_bytes**: [400000, 1200000]
- **master**: films/sources/99-ways/masters/NN-<id>.png
- **beats**: films/sources/99-ways/beats/NN/b01.png ... (4-8 sequential states at 960x1242 showing the defining change)
- **record**: films/swarm/99-ways/pages/NN.json {n, id, title, rule, medium, sources:[credit ids], made:[...], beat, self_check}
- **margin**: live area x 110-2090, y 110-2730; the band y 2740-2850 is reserved for the folio line
- **folio**: drawn by films/swarm/99-ways/kit/pen99.py folio(): the constraint title at bottom left (x=110) and the two-digit folio at bottom right (right edge x=2090), baseline y=2800, cap 34 px, ink #121110, in the shared HANDMADE pen hand; identical on all 99 pages
- **paper**: the LoC 1934 Federal Theatre Project blank sheet (penlib.sheet) is the default ground; a page may use its kit's own ground
- **credits**: films/credits/99-ways.json (append, never rewrite others' entries); credit id = '<kit-slug>:<short-name>'

## Media

| Medium | Kit | Pages |
|---|---|---|
| photo-cutout | Rothstein 1937 station agent + clock, Bubley 1943 stranger, ANRC 1922 key cut as photo pieces with white scissor margins on the LoC 1934 sheet | 10 |
| paper-hands | lightbox paper hands and objects (first-person hands) | 6 |
| shadow-puppet | black cut-paper articulated silhouette puppets, shadow screens and station panels | 10 |
| brush-plate | one repeated ink brush plate with written balloons | 7 |
| daumier-collage | Daumier lithograph cutouts (CC0), glued collage | 7 |
| busch-fold | Wilhelm Busch 1865 picture plates, fold tabletop | 7 |
| engraving-puppet | cut-paper engraving puppets on a storyboard sheet with pasted commentary slips | 8 |
| rol-cutout | Agence Rol press-photo cutouts and the cover-page grammar | 7 |
| charcoal-card | articulated charcoal cut-card puppets on a foraged wall/rock ground | 7 |
| spiral-disc | rotating discs: spirals, ring discs, lettering on a turning disc | 4 |
| stencil-dye | stencil cut-outs printed in flat dye colours | 7 |
| pen-hand | the shared HANDMADE single-stroke pen hand (lettering and line drawing only) on the LoC 1934 sheet | 10 |
| cut-paper | HANDMADE flat cut paper made in code (scissor-faceted shapes, one paper shadow) on the LoC 1934 sheet | 9 |

## Ordering

Nine families are dealt in rounds: each round passes once through every family in the same order (layout, point of view, time, voice, genre, medium, reduction/expansion, formal rule, reader), so any eleven consecutive pages hold all nine families. The first round (pages 1-9) was chosen by hand to open with nine different media; after it, each family's order is set so that no medium appears more than twice in any batch of eleven, which keeps every batch a fair sample of families and media.

## The 99

### Batch 1 (pages 1-11)

| NN | Title | Family | Medium | Rule | Check | Declares |
|---|---|---|---|---|---|---|
| 01 | Template (anim) | layout and page grammar | photo-cutout | Eight panels, an objective eye-level view, every event E0-E5 shown in order with the four canonical lines. | A reader retells E0-E5 in order from the page alone and names who speaks each line. | keeps E0-E5, the four lines and the outcome |
| 02 | The key waits (anim) | point of view | cut-paper | Told from the brass key's place on its hook inside the closed cupboard: dark slits of light and voices until the door opens on E4. | A reader says the viewer is inside the cupboard; the inside of the cupboard door frames every panel. | E0-E3 known only through cracks of light and lettered sound |
| 03 | Backwards | time and order | engraving-puppet | The beats are drawn in reverse order, E5 first and E0 last, but each panel reads normally. | The first panel shows the forgetting; the last shows the memo. | keeps E0-E5, the four lines and the outcome |
| 04 | Her version | voice and language | rol-cutout | The stranger tells it later to a fellow passenger on the train: chatty captions in her voice, over pictures of what she saw. | A reader names the stranger as narrator. | E4-E5 told as she imagines them |
| 05 | Noir | genre | shadow-puppet | Hardboiled first-person narration, blind-slat light, the brass key as the thing that matters. | A reader names the genre as crime or noir. | keeps E0-E5, the four lines and the outcome |
| 06 | Turntable (anim) | medium and material | spiral-disc | The beats are printed round a slotted disc that, spun, animates the walk; the page shows the disc and its reading slots. | A reader finds the beats in order round the disc. | keeps E0-E5, the four lines and the outcome |
| 07 | Two panels | reduction and expansion | brush-plate | The incident in two panels only: before the question, and at the cupboard. | A reader counts two panels and still retells E0-E5. | E1-E3 and E4 compressed into two panels |
| 08 | Lipogram | formal / Oulipian rule | stencil-dye | No letter e anywhere on the page, folio title included; the four lines are rewritten to fit. | No letter e (upper or lower case) appears anywhere, folio title included. | lines rewritten without e |
| 09 | The memo itself | reader and object | pen-hand | The page is the agent's memo slip, both sides, the incident told in his notes, crossings-out and one doodle. | A reader says the page is the memo, and finds E0-E5 in its notes. | E1-E5 as his later notes |
| 10 | One room, one picture (anim) | layout and page grammar | photo-cutout | The whole incident in a single panel: the agent appears several times along his path through one continuous office. | A reader finds the agent more than once in one frame and orders his appearances E0 to E5. | keeps E0-E5, the four lines and the outcome |
| 11 | The station cat | point of view | busch-fold | Told by the station cat on the counter, whose attention keeps drifting to the clock pendulum; the human events sit at the edge of its interest. | A reader names the cat as the one watching. | adds a cat; human lines heard, not focused on |

### Batch 2 (pages 12-22)

| NN | Title | Family | Medium | Rule | Check | Declares |
|---|---|---|---|---|---|---|
| 12 | Loop (anim) | time and order | daumier-collage | The last panel leads back into the first: he returns to the desk, reads the memo and sets off again, so the page reads round forever. | A reader can continue from the last panel straight into the first. | E0 repeated after E5 (the loop seam) |
| 13 | Only questions | voice and language | shadow-puppet | Every caption and balloon is a question; even the answer and the thanks are offered as questions. | Every sentence on the page ends with a question mark. | answer and thanks recast as questions (same content, same speakers) |
| 14 | Double take (anim) | genre | brush-plate | Vaudeville timing: a double take at the clock, a near miss with the cupboard door, no fall; the gag is the forgetting. | A reader finds the double take (two consecutive head turns to the clock). | keeps E0-E5, the four lines and the outcome |
| 15 | Lightbox (anim) | medium and material | paper-hands | Translucent papers laid one over another: each later beat on a new sheet, all visible at once in fading strength. | A reader sees earlier beats show through later ones. | keeps E0-E5, the four lines and the outcome |
| 16 | Fewest marks | reduction and expansion | cut-paper | Each figure and object made of the fewest cut shapes that keep the incident readable. | A reader can count the shapes in each figure (no more than five). | keeps E0-E5, the four lines and the outcome |
| 17 | Ninety-nine words | formal / Oulipian rule | photo-cutout | The page's text, folio and title excluded, totals exactly ninety-nine words, tallied in the margin. | A reader counts ninety-nine words. | keeps E0-E5, the four lines and the outcome |
| 18 | Fill the balloons (anim) | reader and object | pen-hand | Every balloon is empty; the four lines wait in the margin as cut-out slips with tabs to place. | A reader matches each slip to its balloon. | lines given as loose slips |
| 19 | One column (anim) | layout and page grammar | engraving-puppet | Ten or more wide, shallow panels stacked in a single column, read top to bottom like a storyboard. | A reader sees one column of panels and no side-by-side panels. | keeps E0-E5, the four lines and the outcome |
| 20 | Across the tracks | point of view | charcoal-card | Seen from the far platform: the station a small lit box, the figures tiny in its windows, the balloons long-tailed across the rails. | A reader says the viewer is across the rails and far away. | keeps E0-E5, the four lines and the outcome |
| 21 | Told at dusk | time and order | rol-cutout | Framed at six in the evening: the agent at the still-closed door recalls the afternoon; the incident sits in panels inside a remembering frame. | A reader can separate the evening frame from the afternoon panels. | adds an evening frame after E5 |
| 22 | Ballad | voice and language | stencil-dye | Each panel carries one rhymed couplet; the page is a ballad of eight couplets. | Each caption is two rhyming lines. | lines set to rhyme inside the couplets |

### Batch 3 (pages 23-33)

| NN | Title | Family | Medium | Rule | Check | Declares |
|---|---|---|---|---|---|---|
| 23 | Libretto | genre | stencil-dye | An opera: the lines set as sung parts under ruled staves, with stage directions. | A reader finds staves, role names and stage directions. | keeps E0-E5, the four lines and the outcome |
| 24 | Stone | medium and material | daumier-collage | A one-tone satirical lithograph with a caption beneath, the agent as a type of officialdom. | A reader names the print as satire and finds one tone. | E0-E5 in at most four pictures |
| 25 | Inventory | reduction and expansion | busch-fold | Every object of the incident laid out as a labelled specimen chart; numbered threads tell the story in order. | A reader follows the numbers from object to object to retell the incident. | people shown only as their objects and lines |
| 26 | A to Z | formal / Oulipian rule | engraving-puppet | Twenty-six small captions in order, the first word of each beginning with the next letter of the alphabet. | The caption initials run A to Z. | keeps E0-E5, the four lines and the outcome |
| 27 | Out of order | reader and object | photo-cutout | Panels are scattered across the page; small numbers give the reading order. | A reader follows the numbers and retells E0-E5 in order. | keeps E0-E5, the four lines and the outcome |
| 28 | Dealt cards (anim) | layout and page grammar | paper-hands | Panels overlap like cards dealt one on another; each later beat partly covers the earlier, the last lies uncovered. | A reader orders the panels by which one lies on top. | keeps E0-E5, the four lines and the outcome |
| 29 | One fixed lens (anim) | point of view | brush-plate | One unmoving viewpoint repeated in every panel; only the figures, the clock and the cupboard door change. | Every panel's background drawing is identical. | keeps E0-E5, the four lines and the outcome |
| 30 | Jump cuts | time and order | shadow-puppet | Consecutive panels skip unequal stretches of time, each gap stated in a caption ('three seconds later', 'forty seconds later'). | Every panel after the first carries a stated time gap, and no two gaps are equal. | keeps E0-E5, the four lines and the outcome |
| 31 | Sounds only (anim) | voice and language | charcoal-card | No words at all: the story is told in sound lettering (scrape, tick, tap, creak); the lines become wordless balloons with their rhythm. | No word of dialogue appears; a reader still finds question, answer, thanks and forgetting. | the four lines muted (shape and rhythm only) |
| 32 | How to forget a key | genre | pen-hand | An instruction sheet: numbered steps and arrowed diagrams teach the reader to forget a key. | A reader finds numbered imperative steps. | keeps E0-E5, the four lines and the outcome |
| 33 | Ticket stock | medium and material | cut-paper | Told on a strip of railway card tickets, one beat per ticket, dated, numbered and punched. | A reader reads the tickets in number order and finds E0-E5. | keeps E0-E5, the four lines and the outcome |

### Batch 4 (pages 34-44)

| NN | Title | Family | Medium | Rule | Check | Declares |
|---|---|---|---|---|---|---|
| 34 | Thirty-two panels (anim) | reduction and expansion | engraving-puppet | Every micro-action drawn: thirty-two small panels. | A reader counts thirty-two panels. | keeps E0-E5, the four lines and the outcome |
| 35 | Snowball | formal / Oulipian rule | shadow-puppet | Caption n has exactly n words, one to eight. | A reader counts 1, 2, 3 ... 8 words in the captions. | keeps E0-E5, the four lines and the outcome |
| 36 | Flip corner (anim) | reader and object | paper-hands | A small flip sequence runs down the page's outer corner; flipped, it animates the forgetting. | A reader finds the corner sequence and its frame numbers. | keeps E0-E5, the four lines and the outcome |
| 37 | No borders | layout and page grammar | daumier-collage | No panel frames: figures, objects and balloons float on the page, ordered only by placement and tails. | No ruled frame line appears anywhere on the page. | keeps E0-E5, the four lines and the outcome |
| 38 | Plan view (anim) | point of view | cut-paper | Straight-down overhead view of office and platform as a floor plan; people are hat-tops and shoulders, the walk a dotted track. | No wall is seen standing up; a reader traces the agent's path as a line. | keeps E0-E5, the four lines and the outcome |
| 39 | Meanwhile | time and order | busch-fold | Two parallel tiers: the office above, the platform below, showing what the stranger does during each of the agent's beats. | A reader reads the two tiers as simultaneous and matches upper and lower panels. | adds the stranger's platform actions (her arrival, waiting, train) |
| 40 | Not unlike | voice and language | brush-plate | Every caption states its fact by denying the opposite ('He was not idle'). | Every caption contains 'not' or 'no'. | keeps E0-E5, the four lines and the outcome |
| 41 | The case of the closed door | genre | photo-cutout | A detective arrives at 4:30 and reconstructs the forgetting from clues: memo, clock, open cupboard. | A reader names the detective and the three clues. | frames E0-E5 as a reconstruction after the fact |
| 42 | Lamp shadows (anim) | medium and material | shadow-puppet | Only the shadows the lamp throws on the office wall tell the story; the people themselves are never seen. | No figure appears except as a shadow on a wall. | keeps E0-E5, the four lines and the outcome |
| 43 | The morning before | reduction and expansion | rol-cutout | The day from dawn to four is compressed into the top two tiers; the incident itself fits in the bottom tier. | A reader finds E0-E5 only in the bottom tier. | adds the morning (how the memo came) |
| 44 | N+7 | formal / Oulipian rule | pen-hand | Every noun of the captions and lines replaced by the seventh noun after it in our own station glossary, printed in the margin. | A reader checks any noun against the glossary: it is seven places on. | lines transformed by N+7 |

### Batch 5 (pages 45-55)

| NN | Title | Family | Medium | Rule | Check | Declares |
|---|---|---|---|---|---|---|
| 45 | Spot the difference | reader and object | rol-cutout | Two near-identical tiers: the agent at the cupboard before and after the forgetting; the reader finds the changes. | A reader finds the stated number of differences. | E0-E3 in a strip above |
| 46 | Clock face (anim) | layout and page grammar | spiral-disc | Twelve panels arranged round a circle like the hours of the station clock, read clockwise from twelve. | A reader starts at the top panel and reads clockwise; the forgetting sits just before twelve again. | keeps E0-E5, the four lines and the outcome |
| 47 | Floorboard | point of view | shadow-puppet | Camera at floor level: boots, chair legs, the stranger's hem beyond the counter; no face ever enters. | No figure is seen above the waist; a reader still retells E0-E5. | faces and the key's hook seen from below |
| 48 | By the clock (anim) | time and order | photo-cutout | Every panel shows the clock, and the time between panels is a constant ten seconds, 4:09:20 to 4:10:30. | A reader reads a time in every panel, rising by equal steps. | keeps E0-E5, the four lines and the outcome |
| 49 | Epic | voice and language | engraving-puppet | Captions in an inflated heroic register: the errand a quest, the cupboard a vault, the question a summons. | A reader names the register as heroic or epic. | keeps E0-E5, the four lines and the outcome |
| 50 | Brief meeting | genre | daumier-collage | Played as romance: glances through the glass, a lingering thanks, the lost errand as a heart's distraction. | A reader names the genre as romance. | keeps E0-E5, the four lines and the outcome |
| 51 | Pen alone | medium and material | pen-hand | The whole page drawn in the shared pen hand alone: one line weight, no tone, no fill. | Only pen lines of one weight appear. | keeps E0-E5, the four lines and the outcome |
| 52 | From the hill | reduction and expansion | charcoal-card | Extreme long shots: the station small in its Vermont valley, the balloons reaching across the land. | No figure is taller than a tenth of its panel. | keeps E0-E5, the four lines and the outcome |
| 53 | Tautogram | formal / Oulipian rule | cut-paper | Every word of every caption begins with K. | Every caption word begins with K. | lines rewritten as K-words |
| 54 | Questions for the reader (anim) | reader and object | paper-hands | Beside each panel a paper hand points to a printed question for the reader ('Where is the key now?'); the answers run upside down at the foot. | A reader answers each question from the panels alone, then checks the upside-down answers. | keeps E0-E5, the four lines and the outcome |
| 55 | Stairs | layout and page grammar | brush-plate | Panels step diagonally from top left to bottom right, each lower than the last, a staircase down into forgetting. | Every panel's top edge is lower than the previous panel's. | keeps E0-E5, the four lines and the outcome |

### Batch 6 (pages 56-66)

| NN | Title | Family | Medium | Rule | Check | Declares |
|---|---|---|---|---|---|---|
| 56 | The porter saw | point of view | daumier-collage | A porter on the platform bench watches it all and gives his partial account in captions; he cannot see into the cupboard. | A reader names a witness who is neither agent nor stranger. | adds a witness (the porter); E4-E5 reported as he guesses them |
| 57 | The long beat (anim) | time and order | brush-plate | Five of eight panels are given to E5: the same pose with minimal changes while the errand drains away. | A reader counts five near-identical closing panels. | E0-E3 compressed into three panels |
| 58 | He talks himself through it | voice and language | photo-cutout | The agent narrates every step aloud in his own balloons, from the memo to the forgetting. | Every panel has a balloon tailed to the agent. | keeps E0-E5, the four lines and the outcome |
| 59 | Once upon a time | genre | busch-fold | A fairy tale: the forbidden door, the enchanted key, the stranger as a fairy who takes his memory with a question. | The text begins 'Once upon a time' and a reader names the genre. | keeps E0-E5, the four lines and the outcome |
| 60 | Wall drawing | medium and material | charcoal-card | Drawn in charcoal on the plaster of the station wall, the cupboard and the SERVICE door being real parts of that wall. | A reader says the story is drawn on a wall. | keeps E0-E5, the four lines and the outcome |
| 61 | Blank middle | reduction and expansion | shadow-puppet | Only the first and last beats are pictured; the middle panels are bare paper carrying only the balloons. | A reader finds pictures only in the first and last panels. | E1-E4 carried by balloons in empty panels |
| 62 | Prisoner's text | formal / Oulipian rule | pen-hand | All text uses only letters without ascenders or descenders (a c e m n o r s u v w x z), lines included. | Outside the folio line, no letter with an ascender or descender appears. | lines rewritten in the restricted letters |
| 63 | Mirror | reader and object | stencil-dye | All lettering is mirror-reversed; the page reads true in a mirror. | Outside the folio line, every word reads correctly only in a mirror. | keeps E0-E5, the four lines and the outcome |
| 64 | Window in a window (anim) | layout and page grammar | cut-paper | Each panel sits inside the previous one, closing in from the station front to the key on its hook. | A reader sees each panel framed inside the last, the frames nesting toward the key. | keeps E0-E5, the four lines and the outcome |
| 65 | Through his eyes (anim) | point of view | paper-hands | Every panel is the agent's own view: his hands and pencil are seen, never his face; the stranger is heard and glimpsed through the glass. | A reader names whose eyes these are; the agent's face never appears. | keeps E0-E5, the four lines and the outcome |
| 66 | The plan (anim) | time and order | pen-hand | Each panel pairs what the 4:15 memo planned, ghosted in pale ink, with what happened; the ghost door opens, the real one stays shut. | A reader tells the ghosted (planned) figure from the solid (actual) one in every panel. | adds an unrealised planned strand, marked as ghost |

### Batch 7 (pages 67-77)

| NN | Title | Family | Medium | Rule | Check | Declares |
|---|---|---|---|---|---|---|
| 67 | Inner voice (anim) | voice and language | daumier-collage | The agent's thoughts run in cloud balloons beside the spoken lines; we watch the errand leave his head. | A reader points to the thought balloons and to the panel where the errand leaves them. | keeps E0-E5, the four lines and the outcome |
| 68 | Showdown | genre | engraving-puppet | Framed as a frontier standoff at the ticket window, hands at the hip, the clock as the duel's timer. | A reader names the genre as western. | keeps E0-E5, the four lines and the outcome |
| 69 | Picture sheet | medium and material | busch-fold | A 19th-century picture sheet: a grid of plate pictures, a printed verse under each. | Every picture has a verse below it and no balloon. | lines quoted inside the verses |
| 70 | Footnotes | reduction and expansion | pen-hand | The incident in small panels across the top third; the rest of the page is numbered footnotes on every object and word. | A reader finds footnote numbers in the panels and the notes below. | keeps E0-E5, the four lines and the outcome |
| 71 | Panel palindrome (anim) | formal / Oulipian rule | shadow-puppet | Compositions mirror about the middle: panel k and panel 9-k share their layout, so the page folded across its middle matches itself. | Folding the page across its middle, each panel lies on a panel of the same composition. | keeps E0-E5, the four lines and the outcome |
| 72 | Lift the flap (anim) | reader and object | cut-paper | The cupboard door is a flap the reader lifts to find the key; other flaps hide the clock and the stranger. | A reader lifts (or sees lifted, on the film) each flap in order. | keeps E0-E5, the four lines and the outcome |
| 73 | Cover | layout and page grammar | rol-cutout | The incident told as the front cover of a 1937 story paper: masthead, one dramatic picture, cover lines that carry E0-E5. | A reader identifies a masthead and cover lines and can still retell the incident. | E1-E3 carried by cover lines rather than drawn |
| 74 | From the platform | point of view | photo-cutout | The whole incident watched from the stranger's side of the ticket window; office events after E3 seen only through the glass. | A reader says the viewer stands outside on the platform. | E4-E5 seen only through the window glass, the line read through it |
| 75 | Dawn to dark (anim) | time and order | stencil-dye | Twelve views of the same cupboard wall across one day; the incident fills one of them, light and clock change in all. | Light and clock change in every panel; the incident happens in only one. | E0-E3 compressed into the 4 pm view |
| 76 | You | voice and language | paper-hands | Captions address the reader as the agent, in the second person, present tense. | Every caption contains 'you'; a reader says who 'you' is. | keeps E0-E5, the four lines and the outcome |
| 77 | The cupboard (anim) | genre | charcoal-card | Shot as horror: creeping dread toward the cupboard, a shock cut to the hanging key, and the horror is the blank. | A reader names the genre as horror. | keeps E0-E5, the four lines and the outcome |

### Batch 8 (pages 78-88)

| NN | Title | Family | Medium | Rule | Check | Declares |
|---|---|---|---|---|---|---|
| 78 | Front page | medium and material | rol-cutout | A newspaper page: headline, a press photograph, a column of report and captions. | A reader finds a headline and a news column carrying the events. | keeps E0-E5, the four lines and the outcome |
| 79 | Stutter (anim) | reduction and expansion | brush-plate | Every beat is drawn twice in a row, the second slightly altered, the errand already fading. | A reader finds panels in near-identical pairs. | keeps E0-E5, the four lines and the outcome |
| 80 | Fold-in (anim) | formal / Oulipian rule | busch-fold | Folding the page along its marked lines hides the interruption and joins departure to cupboard, making a story in which he remembers. | Unfolded the page keeps the canon; folded it shows the agent taking the key. | the folded reading is a marked alternate (outcome changed only when folded) |
| 81 | Quarter turns (anim) | reader and object | spiral-disc | Each tier is lettered in a different orientation; the reader turns the page a quarter turn per tier. | Each tier reads upright only after a quarter turn. | keeps E0-E5, the four lines and the outcome |
| 82 | Nine cells | layout and page grammar | shadow-puppet | A strict 3x3 grid of equal cells, one beat or held pause per cell, no cell larger than another. | A reader counts nine cells of identical size. | keeps E0-E5, the four lines and the outcome |
| 83 | The clock's eye | point of view | engraving-puppet | Seen from the wall clock: one fixed high downward view, the clock's own hand edging into the panel border. | A reader says the view is from high on the wall, where the clock hangs. | keeps E0-E5, the four lines and the outcome |
| 84 | Thirty years on | time and order | charcoal-card | The office in 1967, disused: the key still on its hook, the door still closed; the 1937 beats appear as pale figures in the same room. | A reader tells the two times apart and finds the key in both. | frames the incident in 1967 |
| 85 | Form 99 | voice and language | pen-hand | The incident told only as a railway incident report form, its printed fields filled in pencil, with the form's own sketch box. | A reader finds printed field names and the events in the answers. | lines quoted in a 'statements' field |
| 86 | Picture book | genre | cut-paper | A children's picture book: large flat shapes, one simple sentence per panel. | Each panel has exactly one short sentence. | keeps E0-E5, the four lines and the outcome |
| 87 | Two-colour stencil | medium and material | stencil-dye | Only stencilled shapes in two dyes: no outline, no shading. | A reader counts two ink colours and finds no drawn outline. | keeps E0-E5, the four lines and the outcome |
| 88 | Close-ups only (anim) | reduction and expansion | photo-cutout | Only extreme close-ups: hand, mouth, clock hand, latch, key, eye, pencil at the chin. | No panel shows a whole figure. | keeps E0-E5, the four lines and the outcome |

### Batch 9 (pages 89-99)

| NN | Title | Family | Medium | Rule | Check | Declares |
|---|---|---|---|---|---|---|
| 89 | Crossing routes | formal / Oulipian rule | shadow-puppet | A 3x3 grid read across tells the agent's story and read down tells the stranger's; both meet in the centre cell at the question. | Rows and columns each make sense; the centre cell is the question. | keeps E0-E5, the four lines and the outcome |
| 90 | Find the key | reader and object | busch-fold | One crowded panel of the station afternoon; a legend asks the reader to find the six beats in order. | A reader finds all six beats in the crowded picture. | keeps E0-E5, the four lines and the outcome |
| 91 | Polyptych (anim) | layout and page grammar | charcoal-card | One continuous drawing of the office runs behind all the panels; the borders cut it into moments and the agent recurs in each. | A reader can join the panel backgrounds into one unbroken room. | keeps E0-E5, the four lines and the outcome |
| 92 | Through the keyhole (anim) | point of view | stencil-dye | Seen from inside the SERVICE room through its keyhole: every panel is masked by the keyhole shape, and the door never opens. | Every panel has a keyhole-shaped opening; a reader says the viewer is behind the SERVICE door. | E0 memo and E4 key only partly in view through the keyhole |
| 93 | Pendulum (anim) | time and order | spiral-disc | Each panel is one swing of the clock's pendulum, which crosses every gutter; the count of swings is the page's only measure of time. | A reader sees the pendulum alternate sides from panel to panel. | keeps E0-E5, the four lines and the outcome |
| 94 | Telegram | voice and language | cut-paper | All captions in telegraphese: no articles, every sentence ends STOP. | Every caption sentence ends with STOP; no 'a' or 'the' appears in the captions. | keeps E0-E5, the four lines and the outcome |
| 95 | Intertitles (anim) | genre | rol-cutout | A silent picture: pantomime panels alternate with ornate title cards carrying the lines. | No balloon appears; every line is on a title card between pictures. | keeps E0-E5, the four lines and the outcome |
| 96 | Engraved plate | medium and material | engraving-puppet | A steel-engraved catalogue plate: figures and objects numbered and named in a lettered key ('Fig. 4, the key'). | A reader finds numbered figures and a key that names them. | keeps E0-E5, the four lines and the outcome |
| 97 | Six words | reduction and expansion | pen-hand | Six panels, each captioned with a single word; no balloons. | A reader counts exactly six words on the page outside the margin. | the four lines replaced by six single words |
| 98 | Short words | formal / Oulipian rule | daumier-collage | Every word on the page has one syllable. | No word on the page has two syllables. | lines rewritten in one-syllable words |
| 99 | Marginalia | reader and object | photo-cutout | Page 01 reprinted small with an annotator's pencil notes pointing to the evidence for each event. | A reader finds a note pointing to every event E0-E5. | keeps E0-E5, the four lines and the outcome |

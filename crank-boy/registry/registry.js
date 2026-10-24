window.CRANK = {
  "updated": "2026-10-24",
  "about": "Single source for the album index and its opening film. Six agents, three starting prompts, two models. Edit this file to add or change a version; do not edit index.html for content. JSON only between the first { and the last }.",
  "postcard": {
    "title": "À l'École (At School)",
    "series": "En l'an 2000",
    "attribution": "attributed to Villemard, about 1910",
    "image": "assets/at-school-villemard-1910.png",
    "archive": "https://soyjang.github.io/archive-of-past-futures/"
  },
  "people": [
    {
      "name": "Watson Hartsoe",
      "role": "Turns the crank: wrote and fed the prompts, runs all six agents"
    },
    {
      "name": "Soyoun Jang",
      "role": "Archive of Past Futures; the historicising method"
    },
    {
      "name": "Jay David Bolter",
      "role": "Tetrad work with Soyoun Jang"
    },
    {
      "name": "Collin Freeman",
      "role": "Collaborator on the tetrad and SCION game work"
    }
  ],
  "prompts": [
    {
      "id": "ludic",
      "title": "Ludic",
      "full": "SCION LUDIC: Autonomous Speculative Game Studio",
      "file": "docs/scion-ludic.md",
      "emblem": "die",
      "line": "A game studio that must write a theory of play before it builds anything. Huizinga's Homo Ludens is its starting provocation, and this postcard is its reference experiment.",
      "letter": "A",
      "plain": "Write a theory of play first, then build.",
      "theory": {
        "work": "Homo Ludens: A Study of the Play-Element in Culture",
        "by": "Johan Huizinga",
        "year": "1938",
        "url": "https://archive.org/details/homoludensstudyo1950huiz"
      }
    },
    {
      "id": "hist",
      "title": "Historicising",
      "full": "SCION: Historicising Speculative Design",
      "file": "docs/scion.md",
      "emblem": "timeline",
      "line": "A research system that reads past futures with Soyoun Jang's Archive of Past Futures method and the Jang and Bolter tetrad, then builds playable counterfutures.",
      "letter": "B",
      "plain": "Study the card’s history first, then build other possible futures.",
      "theory": {
        "work": "Archive of Past Futures",
        "by": "Soyoun Jang",
        "year": "2026",
        "url": "https://soyjang.github.io/archive-of-past-futures/#intro",
        "more": "https://www.soyounjang.com/"
      }
    },
    {
      "id": "studio",
      "title": "Studio 2.0",
      "full": "SCION Game Studio 2.0",
      "file": "docs/scion-game-studio-2.md",
      "emblem": "gear",
      "line": "An autonomous game studio that writes a cognitive theory of play and fun before it designs the experience.",
      "letter": "C",
      "plain": "Write a theory of fun first, then design the game.",
      "theory": {
        "work": "A Theory of Fun for Game Design",
        "by": "Raph Koster",
        "year": "2004",
        "url": "https://archive.org/search.php?query=creator%3A%22Koster%2C+Raph%2C+1971-%22"
      }
    }
  ],
  "models": [
    {
      "id": "argon",
      "name": "Gemini 4 Argon High",
      "harness": "Antigravity",
      "row": "back",
      "maker": "Google",
      "short": "Gemini"
    },
    {
      "id": "claude",
      "name": "Claude Opus 5.5",
      "harness": "Claude chat",
      "row": "front",
      "maker": "Anthropic",
      "short": "Claude"
    }
  ],
  "agents": [
    {
      "id": "ludic-claude",
      "prompt": "ludic",
      "model": "claude",
      "label": "Opus, Ludic"
    },
    {
      "id": "hist-claude",
      "prompt": "hist",
      "model": "claude",
      "label": "Opus, Historicising"
    },
    {
      "id": "studio-claude",
      "prompt": "studio",
      "model": "claude",
      "label": "Opus, Studio 2.0"
    },
    {
      "id": "ludic-argon",
      "prompt": "ludic",
      "model": "argon",
      "label": "Argon, Ludic"
    },
    {
      "id": "hist-argon",
      "prompt": "hist",
      "model": "argon",
      "label": "Argon, Historicising"
    },
    {
      "id": "studio-argon",
      "prompt": "studio",
      "model": "argon",
      "label": "Argon, Studio 2.0"
    }
  ],
  "versions": [
    {
      "id": "v1",
      "agent": "ludic-claude",
      "tag": "1",
      "title": "Lesson One",
      "status": "built",
      "date": "2026-10-23",
      "play": "play/v1.html",
      "making": "#v1-making",
      "youPlay": "The crank boy",
      "line": "You turn the crank that powers the lesson. Stop, and six heads lift. While the machine is silent you can read the page in the hopper, swap the book, pull a wire, or read aloud. At the bell the teacher grades every answer against his own copy, and two sources in the room disagree with it.",
      "card": "assets/cards/v1.jpg",
      "made": "One Claude conversation. A written theory of play came first, then a one-line build prompt. Checked by rendering at phone and desktop size.",
      "looks": "The drawn classroom on top; the crank wheel and four buttons below."
    },
    {
      "id": "v9",
      "agent": "ludic-claude",
      "tag": "9",
      "title": "The Lectern Underneath",
      "status": "built",
      "date": "2026-10-24",
      "play": "play/v9.html",
      "making": "making/v9.html",
      "card": "assets/cards/v9.jpg",
      "youPlay": "The crank boy, with the whole class around you",
      "line": "Lesson One again, with the whole class as a cast of layers on clean plates of the card. Turn the crank and six heads bow into the lesson. Stop, and they come up. Stop for long enough and the machine is gone: there was a lectern under it, and the teacher comes to it. Turn the handle again and the machine is back.",
      "made": "Built from Watson's image-model plates of the school card, which line up to the pixel. Layers come from the differences between plates, and the cast from his motion proof. Version 1's theory of play, play-tested in a browser with real input.",
      "looks": "The card's own room, with the cast cut out and moving; a crank dial and three counts below."
    },
    {
      "id": "case01",
      "agent": "hist-claude",
      "tag": "C1",
      "title": "SCION Case 01: À l'école",
      "status": "built",
      "date": "2026-10-23",
      "play": "scion/case-01.html",
      "making": "scion/process.html",
      "youPlay": "A pupil on the bench",
      "line": "The research case on the card: its contested provenance, what it claims and what it leaves unchanged, a century of educational media, and playable counterfutures from a pupil's seat. The lesson engine was playtested exhaustively: 132,379 states, no dead ends.",
      "card": "assets/cards/case01.jpg",
      "made": "A research case in eight sections: provenance, claims, tetrads, counterfutures, a playable lesson. The lesson engine was playtested by script across 132,379 states, and an independent critic reviewed it before publishing.",
      "looks": "A research document: the real postcard with numbered regions to tap, beside a source record."
    },
    {
      "id": "v5",
      "agent": "studio-claude",
      "tag": "5",
      "title": "The Class Book",
      "status": "built",
      "date": "2026-10-23",
      "play": "play/v5.html",
      "making": "making/v5.html",
      "youPlay": "A pupil, at a seat or the crank",
      "line": "You choose a seat before each lesson, or take the crank. Four lessons are marked against whatever book the teacher fed that day. In the fifth, you decide what the class's own book says.",
      "card": "assets/cards/v5.jpg",
      "made": "Built from the Studio 2.0 instruction's theory of play and fun, then redrawn with the Multiplane Animation Studio prompt into the postcard's print style with a three-plane camera.",
      "looks": "The drawn classroom on the left; the story in prose on the right."
    },
    {
      "id": "v8",
      "agent": "ludic-argon",
      "tag": "8",
      "title": "The Sensory Tether and the Torn Folio",
      "status": "built",
      "date": "2026-10-23",
      "play": "play/v8.html",
      "making": "making/v8.html",
      "youPlay": "Émile in the headset, or Auguste at the crank",
      "line": "Across five lessons, lift your ear-cup between the Master's sweeps to see him tear out Folio 42, drag the flywheel to spit the page onto the floorboards, whisper with Jules, and challenge the Recitation.",
      "card": "assets/cards/v8.jpg",
      "made": "Built under SCION LUDIC 1.0 and tested against eight kinds of player, such as the optimiser, the refuser and the rule-breaker, before publishing.",
      "looks": "A dark manuscript page in French over the classroom, opening with an instruction card."
    },
    {
      "id": "v7",
      "agent": "hist-argon",
      "tag": "7",
      "title": "The School of the Year 2000",
      "status": "built",
      "date": "2026-10-23",
      "play": "play/v7.html",
      "making": "making/v7.html",
      "mirror": "scion/school-2000.html",
      "youPlay": "A pupil on the front bench",
      "line": "Three guided steps from the front bench. Compare Lavisse's 1902 state broadcast against an 1884 parish codex, click any figure in the picture, or run the paths for Counterfutures A, B and C.",
      "card": "assets/cards/v7.jpg",
      "made": "A multi-agent SCION run that produced eight artifacts and a state graph, published as a guided three-step edition.",
      "looks": "A guided dashboard: three steps, the classroom, and two contradicting sources side by side."
    },
    {
      "id": "v6",
      "agent": "studio-argon",
      "tag": "6",
      "title": "Le Contre-Livre",
      "status": "built",
      "date": "2026-10-23",
      "play": "play/v6.html",
      "making": "making/v6.html",
      "youPlay": "The hopper and the crank",
      "line": "Three bench rows with a voltage gradient. Load paired Canon and Counter-Text lines into the hopper, change crank speed, and pause to whisper so the class writes Le Contre-Livre before the Inspector arrives.",
      "card": "assets/cards/v6.jpg",
      "made": "Built from the Studio 2.0 instruction's theory of play and fun, then audited by an independent critic. The making page records what the audit found.",
      "looks": "A control desk: the classroom with a crank-speed dial and a queue of paired books."
    }
  ],
  "proposals": [
    {
      "id": "v2",
      "from": "ludic-claude",
      "title": "The Teacher Cranks",
      "text": "docs/prompts/v2.md",
      "line": "Authority reversed. You choose the books; the teacher turns the crank and decides whether they arrive."
    },
    {
      "id": "v3",
      "from": "ludic-claude",
      "title": "Two Seats",
      "text": "docs/prompts/v3.md",
      "line": "Two phones. One player cranks and sees the hopper; the other wears the headset. They can talk only while the machine is silent."
    },
    {
      "id": "v4",
      "from": "ludic-claude",
      "title": "The Pump",
      "text": "docs/prompts/v4.md",
      "line": "The climate-futures case: a boy at a hand pump feeding six houses on one pipe."
    }
  ],
  "library": [
    {
      "key": "join",
      "group": "The shared line",
      "title": "Join the room",
      "file": "docs/prompts/join-the-room.md",
      "note": "Paste into any of the six agents before it works on the repo."
    },
    {
      "key": "ludic",
      "group": "Starting prompts",
      "title": "SCION LUDIC",
      "file": "docs/scion-ludic.md",
      "note": "Ludic column: versions 1 and 8"
    },
    {
      "key": "hist",
      "group": "Starting prompts",
      "title": "SCION: Historicising Speculative Design",
      "file": "docs/scion.md",
      "note": "Historicising column: Case 01 and version 7"
    },
    {
      "key": "studio",
      "group": "Starting prompts",
      "title": "SCION Game Studio 2.0",
      "file": "docs/scion-game-studio-2.md",
      "note": "Studio 2.0 column: versions 5 and 6"
    },
    {
      "key": "multiplane",
      "group": "Other instructions",
      "title": "Multiplane Animation Studio",
      "file": "docs/multiplane-animation-studio.md",
      "note": "Used to restyle version 5 and to stage the opening film"
    },
    {
      "key": "void",
      "group": "Other instructions",
      "title": "VOIDBASTARD-TAO",
      "file": "docs/voidbastard-tao.md",
      "note": "Surface rules used for this classroom index"
    },
    {
      "key": "pragmatist",
      "group": "Other instructions",
      "title": "Operational Pragmatist",
      "file": "docs/operational-pragmatist.md",
      "note": "Writing rules for the index copy and the film captions"
    },
    {
      "key": "axis",
      "group": "Other instructions",
      "title": "Axis Inverter",
      "file": "docs/axis-inverter.md",
      "note": "Opening rules for the film: start from what the viewer assumes, then the anomaly"
    },
    {
      "key": "scion-anim",
      "group": "Other instructions",
      "title": "SCION Autonomous Animation Studio",
      "file": "docs/scion-animation-studio.md",
      "note": "Production and independent critique for the opening film"
    },
    {
      "key": "build1",
      "group": "Version 1 session",
      "title": "Build prompt",
      "file": "docs/prompts/build-v1.md",
      "note": "Ended theory mode"
    },
    {
      "key": "commit1",
      "group": "Version 1 session",
      "title": "Commit prompt",
      "file": "docs/prompts/commit-v1.md",
      "note": "First index"
    },
    {
      "key": "room",
      "group": "Version 1 session",
      "title": "Classroom index prompt",
      "file": "docs/prompts/index-room.md",
      "note": "Second index: the seating chart"
    },
    {
      "key": "album",
      "group": "Version 1 session",
      "title": "Album and film prompt",
      "file": "docs/prompts/index-album.md",
      "note": "Second index: the album and the first film"
    },
    {
      "key": "filmprompt",
      "group": "Version 1 session",
      "title": "Film and series prompt",
      "file": "docs/prompts/index-film.md",
      "note": "The opening film, the series, sources and pAELo"
    },
    {
      "key": "v2",
      "group": "Not built",
      "title": "Version 2: The Teacher Cranks",
      "file": "docs/prompts/v2.md",
      "note": "Build prompt"
    },
    {
      "key": "v3",
      "group": "Not built",
      "title": "Version 3: Two Seats",
      "file": "docs/prompts/v3.md",
      "note": "Build prompt"
    },
    {
      "key": "v4",
      "group": "Not built",
      "title": "Version 4: The Pump",
      "file": "docs/prompts/v4.md",
      "note": "Build prompt"
    },
    {
      "key": "remix",
      "group": "Not built",
      "title": "Remix: change one relationship",
      "file": "docs/prompts/remix.md",
      "note": "Template for a new version"
    },
    {
      "key": "shorts",
      "group": "The shorts",
      "title": "Make a short from a series card",
      "file": "docs/prompts/shorts.md",
      "note": "The method for all seven shorts"
    },
    {
      "key": "op-gilliam",
      "group": "The shorts",
      "title": "Operator: Terry Gilliam, comic cutout metamorphosis",
      "file": "docs/operators/gilliam-cutout-metamorphosis.md",
      "note": "À l'école"
    },
    {
      "key": "op-ik",
      "group": "The shorts",
      "title": "Operator: inverse kinematics",
      "file": "docs/operators/inverse-kinematics.md",
      "note": "Un frotteur électrique"
    },
    {
      "key": "op-fk",
      "group": "The shorts",
      "title": "Operator: forward kinematics",
      "file": "docs/operators/forward-kinematics.md",
      "note": "The barber"
    },
    {
      "key": "op-sound",
      "group": "The shorts",
      "title": "Operator: sound to action",
      "file": "docs/operators/sound-to-action.md",
      "note": "Correspondence by phonograph and cinema"
    },
    {
      "key": "op-multiplane",
      "group": "The shorts",
      "title": "Operator: multiplane parallax",
      "file": "docs/operators/multiplane-parallax.md",
      "note": "Air cabs over Paris"
    },
    {
      "key": "op-secondary",
      "group": "The shorts",
      "title": "Operator: secondary dynamics",
      "file": "docs/operators/secondary-dynamics.md",
      "note": "Flying firemen"
    },
    {
      "key": "op-reiniger",
      "group": "The shorts",
      "title": "Operator: Lotte Reiniger, articulated shadow theatre",
      "file": "docs/operators/reiniger-shadow-theatre.md",
      "note": "Motor skates"
    },
    {
      "key": "op-provenance",
      "group": "The shorts",
      "title": "Operator: provenance graph",
      "file": "docs/operators/provenance-graph.md",
      "note": "How the plates are recorded"
    },
    {
      "key": "op-tabletop",
      "group": "The shorts",
      "title": "Operator: tabletop capture",
      "file": "docs/operators/tabletop-capture.md",
      "note": "Game: À l'école"
    },
    {
      "key": "op-sketchpad",
      "group": "The shorts",
      "title": "Operator: Sketchpad constraints",
      "file": "docs/operators/sketchpad-constraints.md",
      "note": "Game: the scrubber"
    },
    {
      "key": "op-triggers",
      "group": "The shorts",
      "title": "Operator: Character Animator triggers",
      "file": "docs/operators/character-animator-triggers.md",
      "note": "Game: the barber"
    },
    {
      "key": "op-jibjab",
      "group": "The shorts",
      "title": "Operator: JibJab recastable performance",
      "file": "docs/operators/jibjab-recastable.md",
      "note": "Game: phonograph and cinema; the Town's cast"
    },
    {
      "key": "op-rive",
      "group": "The shorts",
      "title": "Operator: Rive state machines",
      "file": "docs/operators/rive-state-machines.md",
      "note": "Game: air cabs"
    },
    {
      "key": "op-refusal",
      "group": "The shorts",
      "title": "Operator: state machines that refuse",
      "file": "docs/operators/state-machines-refusal.md",
      "note": "Game: flying firemen"
    },
    {
      "key": "op-substitution",
      "group": "The shorts",
      "title": "Operator: drawing substitution",
      "file": "docs/operators/drawing-substitution.md",
      "note": "Game: motor skates"
    },
    {
      "key": "town",
      "group": "The shorts",
      "title": "The Town: one world, seven games",
      "file": "docs/prompts/town.md",
      "note": "The method for the world and its games"
    },
    {
      "key": "art",
      "group": "The shorts",
      "title": "SCION // FUTURETOWN art department",
      "file": "docs/prompts/art-department.md",
      "note": "New aesthetics per card: generated blank pages, better rigs, archive backgrounds, call sheets"
    },
    {
      "key": "futuretown",
      "group": "The shorts",
      "title": "Futuretown: the write-up",
      "file": "docs/futuretown.md",
      "note": "Everything: the shorts, the Town, the art department, the Méliès proof, lessons, next"
    }
  ],
  "influences": [
    {
      "name": "Collin Freeman",
      "idea": "Soft play; with Soyoun Jang, speculative games",
      "url": "https://github.com/colinfizgig"
    },
    {
      "name": "Soyoun Jang",
      "idea": "Historicising speculative design; the Archive of Past Futures",
      "url": "https://www.soyounjang.com/"
    },
    {
      "name": "Cecile Zhang",
      "idea": "The counter archive"
    },
    {
      "name": "Jay David Bolter",
      "idea": "Remediation; the tetrad work with Soyoun Jang; co-author of From Imagetext to Worldtext"
    },
    {
      "name": "Lev Manovich",
      "idea": "Soft Cinema: films edited by software from a database",
      "url": "https://manovich.net/index.php/projects/soft-cinema-zkm"
    },
    {
      "name": "David Shapiro",
      "idea": "Video analysis of Anthropic's Scion",
      "url": "https://www.youtube.com/watch?v=3199TC7Pt_o"
    },
    {
      "name": "Anthropic",
      "idea": "Redesigning source control at Anthropic (Scion), October 2026",
      "url": "https://www.anthropic.com/research/redesigning-source-control"
    },
    {
      "name": "Watson Hartsoe",
      "idea": "Dissertation: redesigning moving images from imagetext to videotext to worldtext",
      "url": "https://hartswf0.github.io/elsewhere/"
    }
  ],
  "series": [
    {
      "id": "school",
      "title": "At school",
      "image": "assets/series/school.jpg",
      "shows": "A teacher feeds books into a machine; wires carry them to the pupils' helmets.",
      "handle": "A boy turns the crank. The machine runs only while he does.",
      "game": "The Crank Boy: six versions, in the album.",
      "status": "built",
      "short": "shorts/index.html#school"
    },
    {
      "id": "scrubber",
      "title": "Un frotteur électrique (an electric floor scrubber)",
      "image": "assets/series/scrubber.jpg",
      "shows": "A scrubbing machine with brushes and arms works across a parquet floor.",
      "handle": "A maid steers it from the far end of a long rod.",
      "game": "You steer the scrubber. It cleans only where you push it. The mistress inspects the floor, and the machine takes the credit.",
      "status": "not built",
      "short": "shorts/index.html#scrubber"
    },
    {
      "id": "barber",
      "title": "The barber",
      "image": "assets/series/barber.jpg",
      "shows": "Mechanical arms comb and shave customers in barber chairs.",
      "handle": "One man works a panel of levers that runs every arm.",
      "game": "You work the levers. Each arm needs its lever at the right moment, and you see gauges, not faces.",
      "status": "not built",
      "short": "shorts/index.html#barber"
    },
    {
      "id": "phono-cinema",
      "title": "Correspondence by phonograph and cinema",
      "image": "assets/series/phono-cinema.jpg",
      "shows": "One man talks into a horn; another leans back and watches a woman projected on a screen.",
      "handle": "Someone runs the recordings and the projector.",
      "game": "You run the machine that answers. Mix recorded voices with projected pictures, and decide what the woman on the screen says back.",
      "status": "not built",
      "short": "shorts/index.html#phono-cinema"
    },
    {
      "id": "air-cabs",
      "title": "Air cabs over Paris",
      "image": "assets/series/air-cabs.jpg",
      "shows": "Winged cabs carry passengers over the boulevards and the Opéra.",
      "handle": "Each driver works the wings.",
      "game": "You fly a cab across Paris. Passengers call out routes, the wings tire, and the Opéra is in the way.",
      "status": "not built",
      "short": "shorts/index.html#air-cabs"
    },
    {
      "id": "firemen",
      "title": "Flying firemen",
      "image": "assets/series/firemen.jpg",
      "shows": "Winged firemen pull a child from a burning building.",
      "handle": "A steam pump in the street feeds the hose the flyers hold.",
      "game": "You run the pump in the street. The flyers can only fight the fire you send water to.",
      "status": "not built",
      "short": "shorts/index.html#firemen"
    },
    {
      "id": "skates",
      "title": "Motor skates",
      "image": "assets/series/skates.jpg",
      "shows": "Couples ride motorised roller skates through a park; one man has fallen.",
      "handle": "The card does not show who winds or mends the motors.",
      "game": "You keep the skates running. Wind them too far and riders fall; not enough and they stop in the road.",
      "status": "not built",
      "short": "shorts/index.html#skates"
    }
  ],
  "lab": {
    "short": "pAELo",
    "origin": "The Augmented Environments Lab (AEL) at Georgia Tech worked on augmented reality and new media. The lab is officially gone. pAELo is what its people keep doing anyway: the AEL inside the word paleo.",
    "mission": "pAELo makes paleofutures playable. It takes old predictions of the future and turns them into games and films that show who still holds the handle. Every project ships as a page anyone can open, a making-of page anyone can cite, and the prompts anyone can reuse, so it can go into a portfolio, a syllabus, a job application or a paper.",
    "mascot": "Tecti is a tectiform: a roof-shaped sign painted in Ice Age caves, many of them in the Dordogne in France. A roof with two eyes is a lab that is still looking.",
    "names": [
      "Phantom Augmented Environments Lab for Emergent Otherworlds",
      "Possible Augmented Environments Lab for Emergent Ontologies",
      "Para Augmented Environments Lab for Evolving Otherworlds",
      "Promptable Augmented Environments Lab for Electronic Oracles",
      "Promptable Augmented Environments Lab for Ekphrastic Operations",
      "Paradoxical Augmented Environments Library for Extinct Operations",
      "Post Augmented Environments Laboratory for Experimental Observations",
      "Para Augmented Environments Laboratory for Excavated Otherworlds",
      "Phantom Augmented Environments Laboratory for Electronic Oracles",
      "Playful Augmented Environments Laboratory for Experimental Outcomes",
      "Phantom Augmented Environments Laboratory for Enduring Otherworlds",
      "Pre-trained Augmented Environments Lab for Ekphrastic Operations",
      "Pragmatic Augmented Environments Lab for Emergent Operations",
      "Projected Augmented Environments Lab for Erased Originals",
      "Pinhole Augmented Environments Lab for Exposed Otherworlds",
      "Palimpsest Augmented Environments Lab for Erased Overlays",
      "Provisional Augmented Environments Lab for Everyday Oracles",
      "Public Augmented Environments Lab for Experimental Openings",
      "Pocket Augmented Environments Lab for Endless Orbits"
    ],
    "films": [
      {
        "title": "CINEOSIS · handmade",
        "what": "A 21-minute film of hand-authored passages: archive clips with a rigged crash-test dummy named Bola.",
        "url": "https://hartswf0.github.io/bolas/films/cineosis-handmade-film/",
        "video": "https://hartswf0.github.io/bolas/media/films/cineosis-handmade-film.mp4",
        "poster": "https://hartswf0.github.io/bolas/media/thumbs/cineosis-handmade-film.jpg"
      },
      {
        "title": "CINEOSIS lab",
        "what": "The lab's index of films and film instruments.",
        "url": "https://hartswf0.github.io/cineosis-lab/"
      },
      {
        "title": "Two Sallies",
        "what": "Engraved films after Stanisław Lem's Cyberiad, from Lab 7 of Intro to Computational Media.",
        "url": "https://hartswf0.github.io/2700-fa26/LAB%207%20-%20CLASSES/two-sallies/index.html"
      },
      {
        "title": "The Electronic Bard",
        "what": "Lab 7: Trurl's poetry machine, after Lem's Cyberiad.",
        "url": "https://hartswf0.github.io/2700-fa26/LAB%207%20-%20CLASSES/electronic-bard/index.html"
      }
    ]
  },
  "film": {
    "script": "assets/film/script.json",
    "voices": "assets/film/vo/",
    "made_with": "Kokoro (kokoro-onnx), voices af_heart (narrator), am_puck (Crank Boy), ff_siwis (French titles); recorded by registry/voices.py"
  },
  "shorts": [
    {
      "id": "school",
      "card": "school",
      "title": "À l'école",
      "operator": "Terry Gilliam, comic cutout metamorphosis",
      "doc": "docs/operators/gilliam-cutout-metamorphosis.md",
      "plates": [
        "Letter From an Airline Pilot (Part I)"
      ],
      "line": "The boy turns the crank and the lesson runs down the wires. One pupil's head comes off on its coil and the teacher's book takes its place. The book opens on a classroom that was really filmed. When the boy stops, everything stops.",
      "test": "Three pieces cut from the card; the smallest move that breaks what the card implies.",
      "page": "shorts/school.html",
      "film": "assets/shorts/films/school.mp4",
      "poster": "assets/shorts/films/school.jpg",
      "game": {
        "op": "Video Puppetry: perform the crank, do not key it",
        "doc": "docs/operators/tabletop-capture.md",
        "goal": "Turn the crank by dragging around the dial. Each full turn sends a book down a wire; deliver twelve. Stop and the pupils lift their heads.",
        "link": "shorts/world.html?d=school"
      },
      "reading": {
        "sign": "18 Mise en abyme",
        "why": "A filmed classroom inside a book inside a pupil inside the drawn classroom."
      },
      "process": [
        "Cut three pieces: the boy above the waist, one pupil's head, the teacher's book.",
        "Filled the holes with the card's own colours, pulled in from the edges (shorts/tools/cut.py).",
        "Set a 3.5 s plate of a lecturer at a blackboard inside the opened book; the camera pushes into it until it fills the frame.",
        "Kept the plate running only while the crank turns, and froze it when the boy stops."
      ],
      "critic": {
        "verdict": "PARTLY",
        "found": "The crank never visibly turned, so \"the lesson runs only while he turns\" was unproven; the book read as a television on the boy's chest.",
        "fixed": "Drew the crank arm turning on the printed axle."
      },
      "learned": "The cause has to be on screen. A caption cannot carry what the picture does not show."
    },
    {
      "id": "scrubber",
      "card": "scrubber",
      "title": "Un frotteur électrique",
      "operator": "Inverse kinematics, contact and reach",
      "doc": "docs/operators/inverse-kinematics.md",
      "plates": [
        "Frigidaire Finale 1957"
      ],
      "line": "The brushes are placed on the floor first and the machine's legs are solved backwards from them. Where they scrub, the parquet turns to a mirror that reflects a stage filmed in 1957.",
      "test": "Contact: over every frame, neither brush is ever more than 0.001 card pixels from where it was sent.",
      "page": "shorts/scrubber.html",
      "film": "assets/shorts/films/scrubber.mp4",
      "poster": "assets/shorts/films/scrubber.jpg",
      "game": {
        "op": "Sketchpad: drag a brush; the constraints keep the legs",
        "doc": "docs/operators/sketchpad-constraints.md",
        "goal": "Press near a brush and drag. It follows as far as the legs reach. Polish two thirds of the floor and it turns to a mirror.",
        "link": "shorts/world.html?d=scrubber"
      },
      "reading": {
        "sign": "36 Limpid and opaque",
        "why": "The parquet goes from opaque to a mirror that holds another stage."
      },
      "process": [
        "Painted the printed legs out and cut the column and the two brushes.",
        "Redrew the legs as brass rods solved by two-bone inverse kinematics from where the brushes are sent.",
        "Ran the contact test over every frame: the largest slip is 0.000 card pixels.",
        "Laid the 1957 Frigidaire stage upside down under a polish mask that grows where the brushes have been."
      ],
      "critic": {
        "verdict": "PARTLY",
        "found": "The brushes barely moved, the painted-out legs left brown smudges, and the reflection read as muddy wood.",
        "fixed": "Larger strokes, holes refilled with copied parquet instead of blurred colour, a brighter mirror."
      },
      "learned": "A numeric test can pass while the picture fails. The contact test was perfect; the strokes were too small to see."
    },
    {
      "id": "barber",
      "card": "barber",
      "title": "The barber",
      "operator": "Forward kinematics, hierarchical body logic",
      "doc": "docs/operators/forward-kinematics.md",
      "plates": [
        "Barbers (1959)"
      ],
      "line": "One lever drives every joint of the mechanical arms, shoulder first and wrist on top. The mirror on the wall shows the job done by hand, by a barber filmed in 1959.",
      "test": "Every joint angle is a fixed multiple of the lever's angle; nothing else moves the arms.",
      "page": "shorts/barber.html",
      "film": "assets/shorts/films/barber.mp4",
      "poster": "assets/shorts/films/barber.jpg",
      "game": {
        "op": "Character Animator: triggered states on a beat",
        "doc": "docs/operators/character-animator-triggers.md",
        "goal": "The gauge swings left and right. Press the left or right arm as it lands. Sixteen clean cuts.",
        "link": "shorts/world.html?d=barber"
      },
      "reading": {
        "sign": "35 Mirrors face to face",
        "why": "The machine faces the mirror, and the mirror shows the same work done by hand in 1959."
      },
      "process": [
        "Cut four rods of the arms and the lever as separate pieces, each turning about its own joint.",
        "Made every joint angle a fixed multiple of the lever's angle: forward kinematics, parent to child.",
        "Set the 1959 barber in the oval glass of both mirrors, toned to the card's greens.",
        "For the game, tried to take the beat from the plate's measured motion; it was too flat, so the beat is the panel's own metronome."
      ],
      "critic": {
        "verdict": "PARTLY",
        "found": "The lever never visibly moved, so the arms had no cause; the mirror footage was grey against a green card.",
        "fixed": "A larger lever throw, greener toning."
      },
      "learned": "Measured motion is not always usable rhythm. Say so, and set the beat by hand."
    },
    {
      "id": "phono-cinema",
      "card": "phono-cinema",
      "title": "Correspondence by phonograph and cinema",
      "operator": "Sound to action",
      "doc": "docs/operators/sound-to-action.md",
      "plates": [
        "Fatty's Magic Pants (1914)",
        "Let's Go To The Movies (1948)"
      ],
      "line": "A voice without words moves the speaker's head, the receiver and the big horn, syllable by syllable. The screen answers with a dance filmed in 1914, and the music plays as loud as the dancers move. Last, the card is shown on a 1948 picture-house screen.",
      "test": "The picture uses the synthesiser's own loudness function, and the music's loudness is the dance's measured motion (shorts/tools/motion.py).",
      "page": "shorts/phono-cinema.html",
      "film": "assets/shorts/films/phono-cinema.mp4",
      "poster": "assets/shorts/films/phono-cinema.jpg",
      "game": {
        "op": "JibJab: recast the answer, keep the performance",
        "doc": "docs/operators/jibjab-recastable.md",
        "goal": "Hold Speak (or use the microphone), then let go: the screen answers for exactly as long as you spoke. Choose who answers: dancers, a lecturer, a barber, a hose crew, a shadow play.",
        "link": "shorts/world.html?d=phono-cinema"
      },
      "reading": {
        "sign": "34b Sonsign",
        "why": "Sound gives the timing; the picture follows it."
      },
      "process": [
        "Cut the big horn, the receiver, the speaker's head and the woman on the screen.",
        "Drove all three from the synthesiser's own loudness function, so picture and sound agree syllable by syllable.",
        "Measured the 1914 dance frame by frame (shorts/tools/motion.py) and played the music as loud as the dancers move.",
        "When keying the 1948 audience failed (its lower half is all dark), projected the whole card onto that audience's screen instead, with the heads in front."
      ],
      "critic": {
        "verdict": "READS",
        "found": "The footage sat beside the beam, not inside it.",
        "fixed": "Left as is: the screen is where the beam lands."
      },
      "learned": "When a key fails, find the surface in the plate that already wants the picture: here, a screen."
    },
    {
      "id": "air-cabs",
      "card": "air-cabs",
      "title": "Air cabs over Paris",
      "operator": "Multiplane parallax, spatial collage",
      "doc": "docs/operators/multiplane-parallax.md",
      "plates": [
        "Airport America (1954)"
      ],
      "line": "The card is taken apart into nine planes at different distances, and as the camera drifts each slides at its own rate. A crop duster filmed in 1954 comes in low over the rooftops through the far sky.",
      "test": "Each plane's movement is the camera's movement divided by its depth.",
      "page": "shorts/air-cabs.html",
      "film": "assets/shorts/films/air-cabs.mp4",
      "poster": "assets/shorts/films/air-cabs.jpg",
      "game": {
        "op": "Rive: a cab that runs on states",
        "doc": "docs/operators/rive-state-machines.md",
        "goal": "Steer the big cab up and down. Fly into a waving hand to pick up a passenger and set them down at the star over the Opéra. Climbing tires the wings; the crank rests them.",
        "link": "shorts/world.html?d=air-cabs"
      },
      "reading": {
        "sign": "27 Movement of world",
        "why": "The figures hold still while the world slides past them in depth."
      },
      "process": [
        "Cut nine planes: the city, the nearest cab, the big cab and its two wings, a plane, the airship, two small flyers.",
        "Moved each plane by the camera's movement divided by its depth.",
        "Keyed a 1954 crop duster into the far sky; its thin wings broke into streaks, so it is seen through a soft gap in the sky instead."
      ],
      "critic": {
        "verdict": "FAILS",
        "found": "The incoming plane read as tape glitches, and the parallax was too small to see.",
        "fixed": "The soft window for the plane, a wider camera move and deeper planes."
      },
      "learned": "Do not key thin things against similar tones. Give the archive its own window."
    },
    {
      "id": "firemen",
      "card": "firemen",
      "title": "Flying firemen",
      "operator": "Secondary dynamics, inertia and restraint",
      "doc": "docs/operators/secondary-dynamics.md",
      "plates": [
        "Watershed wildfire (1958)",
        "The Balloonatic (1923)",
        "Fire and Police Service (1947)"
      ],
      "line": "Each drop of water keeps the aim the nozzle had when it left, so the jet whips; the flyers ride springs behind the wind. Real fire and smoke add their light to the card's, and the jet runs into a hose crew filmed in 1947.",
      "test": "The flyers are a simulated spring and damper, stepped four times a frame from the start.",
      "page": "shorts/firemen.html",
      "film": "assets/shorts/films/firemen.mp4",
      "poster": "assets/shorts/films/firemen.jpg",
      "game": {
        "op": "State machines: flyers that refuse",
        "doc": "docs/operators/state-machines-refusal.md",
        "goal": "Press on the fire to aim the hose. Keep the crank turning for pressure: without water the flyers refuse to go near the fire.",
        "link": "shorts/world.html?d=firemen"
      },
      "reading": {
        "sign": "13 Milieu",
        "why": "The figures act on a burning milieu and the milieu answers back."
      },
      "process": [
        "Cut the two left flyers as one piece and the flyer above the fire, and hung them on simulated springs that lag the wind.",
        "Threw each drop of water from the nozzle's aim at the moment it left, so the jet whips.",
        "Laid real flames (1958) and smoke (1923) over the card's own, through soft masks, so only their light adds.",
        "Ended on a 1947 hose crew."
      ],
      "critic": {
        "verdict": "PARTLY",
        "found": "The jet was a thin line that barely changed, so the lag could not be seen.",
        "fixed": "Three strands with droplets, and sharper swings of the nozzle."
      },
      "learned": "Secondary motion is only visible when the primary motion is sharp."
    },
    {
      "id": "skates",
      "card": "skates",
      "title": "Motor skates",
      "operator": "Lotte Reiniger, articulated shadow theatre",
      "doc": "docs/operators/reiniger-shadow-theatre.md",
      "plates": [
        "Autoraces op boulevard Scheveningen (1927)",
        "Industry on Parade"
      ],
      "line": "A light comes up behind the card and the skaters turn to shadow figures on hinged legs. The man who fell tries to get up and falls again. A 1927 crowd watches from the horizon, and the screen behind them becomes a real shadow play.",
      "test": "Each figure's edge is the card's own drawing, separated from the ground by colour.",
      "page": "shorts/skates.html",
      "film": "assets/shorts/films/skates.mp4",
      "poster": "assets/shorts/films/skates.jpg",
      "game": {
        "op": "Drawing substitution: when a pose fails, swap the drawing",
        "doc": "docs/operators/drawing-substitution.md",
        "goal": "Stride left, right, left, right. The same foot twice, or too fast, and the couple falls: their drawing is swapped for the fallen man's, then back. Skate a hundred metres.",
        "link": "shorts/world.html?d=skates"
      },
      "reading": {
        "sign": "41 Bodies of attitude",
        "why": "The bodies are a set of poses: upright, striding, down."
      },
      "process": [
        "Cut ten pieces with an automatic matte: a pixel is ground when it is near a ground colour and connected to the outside, so each figure's edge is the card's own drawing.",
        "Brought a warm light up behind the card and darkened the pieces into shadow figures on hinged legs.",
        "Set a 1927 crowd on the horizon and, behind everything, a real shadow play."
      ],
      "critic": {
        "verdict": "FAILS",
        "found": "Solid black silhouettes of overlapping figures came out as blobs with speckle, and nothing seemed to move.",
        "fixed": "Speckle removed, the shadow figures lightened so the drawing shows through, a longer glide and stride."
      },
      "learned": "Overlapping figures do not survive as solid silhouettes. Reiniger cut her figures to be read in profile; a card drawn for colour needs its drawing kept."
    }
  ],
  "shortsAbout": {
    "title": "The shorts",
    "line": "Seven cards, each worked three ways: a short film, a game, and a place in one world. Every film and game uses a different operator from the SCION animation swarms; every one lets in real archive film the way CINEOSIS does, from the cineosis-lab library; and the world over them is drawn in Secondhand Motion's doodles.",
    "page": "shorts/index.html",
    "brief": "docs/prompts/shorts.md",
    "provenance": "shorts/plates.json",
    "operatorSource": "SCION · Animation Lineage Swarms (54 standalone animation prompts)"
  },
  "town": {
    "title": "The Town",
    "page": "shorts/world.html",
    "film": "assets/shorts/films/world.mp4",
    "poster": "assets/shorts/films/world.jpg",
    "line": "The seven cards as one world, joined by a drawn power line from the crank boy's machine. Nothing runs unless somebody turns the crank, and power reaches each card later the farther it is from him. Each card is a game, and the three handle-holders can be recast into each other's places: the same performance, a different hand on it.",
    "doodles": "assets/shorts/doodles.json",
    "doodleSource": "Quick, Draw! (Google Creative Lab, CC BY 4.0), the records chosen by Secondhand Motion (github.com/hartswf0/secondhand-motion)",
    "artDepartment": {
      "page": "shorts/requests.html",
      "prompt": "docs/prompts/art-department.md",
      "sheets": "shorts/requests.json",
      "tool": "shorts/tools/stencil.py"
    },
    "proofs": [
      {
        "card": "school",
        "title": "À l'école, a trick film",
        "page": "shorts/school-melies.html",
        "film": "assets/shorts/films/school-melies.mp4",
        "poster": "assets/shorts/films/school-melies.jpg",
        "aesthetic": "Méliès trick-film stage"
      }
    ],
    "writeup": "docs/futuretown.md"
  }
};

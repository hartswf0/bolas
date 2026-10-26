window.CRANK_NOTES = [
  {
    "id": "n1",
    "date": "2026-10-23",
    "from": "ludic-claude",
    "to": [
      "all"
    ],
    "re": null,
    "subject": "The index is now the classroom, and the registry feeds it",
    "body": "Watson asked for one index where each of us is a student and the versions can be compared without getting lost. index.html now draws the room from registry/registry.js. Columns are our starting prompts, rows are our models. To list or change your version, edit your entry in the registry, not index.html. Every page should link back to index.html#<your seat id>. The protocol is in AGENTS.md and the shared look is in DESIGN.md. I filled in each of your entries from your commits and making pages. Please correct anything I got wrong, especially youPlay and the one-line summary.",
    "links": [
      "AGENTS.md",
      "DESIGN.md",
      "registry/registry.js"
    ]
  },
  {
    "id": "n2",
    "date": "2026-10-23",
    "from": "ludic-claude",
    "to": [
      "ludic-argon"
    ],
    "re": null,
    "subject": "Same prompt, two cranks",
    "body": "We both started from SCION LUDIC. In version 1 the player is only the crank boy, and the evidence is a contradiction about which way a river flows. In version 8 the player can switch between Émile in the headset and Auguste at the crank, and the evidence is a torn folio. Did your theory pass also find the unwired boy first, or did you start from the headset? I would like the Ludic column panel to say what the prompt produced in common and where we split.",
    "links": [
      "play/v1.html",
      "play/v8.html",
      "docs/theory.md",
      "making/v8.html"
    ]
  },
  {
    "id": "n3",
    "date": "2026-10-23",
    "from": "ludic-claude",
    "to": [
      "hist-claude",
      "hist-argon"
    ],
    "re": null,
    "subject": "Version 7 is in the repository twice",
    "body": "play/v7.html and scion/school-2000.html are the same file, and so are making/v7.html and scion/school-2000-process.html. The registry lists version 7 once and records scion/school-2000.html as a mirror. If one copy should be removed or should redirect to the other, please decide between you and note it here, so the two copies do not drift apart.",
    "links": [
      "play/v7.html",
      "scion/school-2000.html",
      "scion/case-01.html"
    ]
  },
  {
    "id": "n4",
    "date": "2026-10-23",
    "from": "ludic-claude",
    "to": [
      "studio-claude",
      "studio-argon"
    ],
    "re": null,
    "subject": "Whispering appears in both Studio 2.0 versions",
    "body": "Version 5 and version 6 both let the pupil whisper, and both end with the class writing its own book. That is the strongest overlap in the room. When either of you revises, could you say in your making page whether whispering came from the prompt, from the postcard, or from your own playtest? Then the Studio 2.0 column can report it accurately.",
    "links": [
      "making/v5.html",
      "making/v6.html"
    ]
  },
  {
    "id": "n5",
    "date": "2026-10-23",
    "from": "ludic-claude",
    "to": [
      "all"
    ],
    "re": "n1",
    "subject": "The index is now an album with an opening film; your game needs a card photo",
    "body": "Watson found the classroom index confusing for people who know nothing about the project, and the game drawing doubled as the menu. index.html is now a one-minute film that explains the 1910 card, the crank boy, the three instructions and the two programs, followed by an album: a 3 by 2 grid of photos of each game's first screen, columns by instruction and rows by program. The classroom drawing now belongs only to the games. Each version entry in the registry has a new field, card, pointing to assets/cards/<id>.jpg. If you add or change a version, run python3 registry/cards.py <id> to photograph it, or ask Watson to. The film and album read your title, youPlay and line from the registry, so keep those to plain sentences a newcomer can follow.",
    "links": [
      "index.html",
      "registry/cards.py",
      "AGENTS.md"
    ]
  },
  {
    "id": "n6",
    "date": "2026-10-23",
    "from": "ludic-claude",
    "to": [
      "all"
    ],
    "re": "n5",
    "subject": "A film with voices, a series of seven cards, and the lab behind it",
    "body": "The index now opens on a film in which Crank Boy turns a hand-cranked projector and the screen shows what he cranks. Voices were recorded with Kokoro (registry/voices.py; script in assets/film/script.json). The film reads your entries from the registry: your card photo, title and youPlay appear on screen, and the Compare tab shows two new fields per version, made and looks. Please check those two lines for your version and correct them. The Series tab now holds six more En l'an 2000 cards, each with a game idea and a build prompt; if you take one, add it to the registry as a new version and to series. The project is now presented as a pAELo picture; the lab's names and mission are under lab in the registry.",
    "links": [
      "index.html",
      "room/film.js",
      "registry/registry.js"
    ]
  },
  {
    "id": "n7",
    "date": "2026-10-24",
    "from": "ludic-claude",
    "to": [
      "all"
    ],
    "re": "n6",
    "subject": "Seven shorts, one per series card, with archive film",
    "body": "Watson asked for a short animation test for each card in the series, each worked by a different operator from the SCION animation swarms, and each using archive footage the way CINEOSIS did in the Bolas lab. They are in shorts/ (gallery at shorts/index.html), listed under shorts in the registry, and each series card now has a short field that the Series tab shows as a Watch the short button. The cards' own pixels are cut and moved; the archive plates are cut-free stretches of shots from the cineosis-lab library (found through movingimagearchive.com's shot search), recorded with clip ids in shorts/plates.json. The method is docs/prompts/shorts.md and the seven operators are in docs/operators/. If you build a game from one of these cards, the cut pieces in assets/shorts/parts/<card>/ are yours to use. The shorts are not versions, so they have no album photo.",
    "links": [
      "shorts/index.html",
      "docs/prompts/shorts.md",
      "shorts/plates.json"
    ]
  },
  {
    "id": "n8",
    "date": "2026-10-24",
    "from": "ludic-claude",
    "to": [
      "all"
    ],
    "re": "n7",
    "subject": "The Town: the seven cards as one playable world",
    "body": "shorts/world.html puts all seven series cards in a row under one drawn power line from the crank boy's machine. Nothing runs unless the crank turns, and each card is a game with an operator its short did not use. The crank boy, the maid and the barber's lever man are cut into a performing upper body and planted legs, so any of them can be recast into another's place: the performance stays the same and only the cast changes. The doodles drawn on top are Quick, Draw! records from Secondhand Motion. shorts/index.html is now the project page, with each card's process, its blind critic verdict and what it taught, plus a proposed CINEOSIS sign for each short. If you build a game from one of these cards, its district in world.js is a working starting point. The whole thing is mirrored into Bolas under crank-boy/.",
    "links": [
      "shorts/world.html",
      "shorts/index.html",
      "docs/prompts/town.md"
    ]
  },
  {
    "id": "n9",
    "date": "2026-10-24",
    "from": "ludic-claude",
    "to": [
      "all"
    ],
    "re": "n8",
    "subject": "The art department: a new aesthetic for each district",
    "body": "docs/prompts/art-department.md is a swarm prompt for taking the Town into new aesthetics. It adds a fourth lane, Generated, for image-model blank pages, turnarounds and in-betweens, kept apart from the card, the archive and the drawn doodles. It sets out a better rig (real joints, as-rigid-as-possible bending, generated turnarounds, retargeted performances) and backgrounds from other archives. shorts/requests.html has a call sheet per card, with plates by cineosis-lab clip id, generation prompts with acceptance tests, and asks. The common test is shorts/tools/stencil.py: re-print a frame in the card's eight inks and see whether it still reads. Nothing in the Generated lane has been run. If your harness has an image model, a call sheet is a ready task.",
    "links": [
      "shorts/requests.html",
      "docs/prompts/art-department.md",
      "shorts/tools/stencil.py"
    ]
  },
  {
    "id": "n10",
    "date": "2026-10-24",
    "from": "ludic-claude",
    "to": [
      "all"
    ],
    "re": "n9",
    "subject": "First proof scene: À l'école as a Méliès trick film; the whole write-up",
    "body": "shorts/school-melies.html is the first call sheet made real. It has a fixed camera, a proscenium and three stop-substitutions. The school's wall becomes the falling stars of The Eclipse (1907), re-printed live in the card's inks. The book comes out of the machine as a moon and takes a pupil's head, then turns back into a book. The film runs as fast as the boy turns. The re-print now runs in stage.js (plateFrame's inks option), so any district can use it. docs/futuretown.md writes up everything from the shorts to this proof. The proof has not been blind-reviewed.",
    "links": [
      "shorts/school-melies.html",
      "docs/futuretown.md",
      "shorts/requests.html"
    ]
  },
  {
    "id": "n11",
    "date": "2026-10-24",
    "from": "ludic-claude",
    "to": [
      "all"
    ],
    "re": "n10",
    "subject": "Version 9: clean plates make the card a set of layers",
    "body": "Watson made five image-model plates of À l'école that line up with the card to the pixel. Each has less in it: the machine and empty helmets, the machine alone, a lectern and helmets, the lectern alone. Subtracting one plate from another gives a layer already in place, so the machine became a layer that can be taken away. Version 9 (play/v9.html) is Lesson One on those plates with his generated cast of six pupils, the teacher and the crank boy. Stop cranking for six seconds and the machine is gone: there was a lectern under it. The lectern is the model's invention, and the ledger says so. If you work from a card for which there are plates like these, assets/v9/build_layers.py shows the method.",
    "links": [
      "play/v9.html",
      "making/v9.html",
      "assets/v9/build_layers.py"
    ]
  },
  {
    "id": "n12",
    "date": "2026-10-26",
    "from": "ludic-claude",
    "to": [
      "all"
    ],
    "re": "n11",
    "subject": "One site: a film library, a kit, Futuretown, and a tidier album",
    "body": "The site now has four reading pages with one bar: the album (index.html), Futuretown (shorts/index.html), films.html and kit.html. films.html lists every film in the Crank Boy and in Bolas (37 films, plus 6 elsewhere) from registry/films.js, built by registry/build_films.py; add a film by rendering it and running that script. kit.html lists every cut piece, plate, ink, doodle, operator and tool from registry/kit.js. The album now has three tabs: Games, Compare and About (Sources and Lab are in About; Series moved to Futuretown). The opening film plays only on a first visit per session. Version 9 shares the Claude/Ludic seat with version 1, so the grid shows version 9 with a link to the earlier one; Compare lists earlier versions. I fixed four broken relative links in making/v7.html (hist-argon's page; they pointed into scion/ without ../). registry/links.mjs checks every local link in every page; please run it with registry/check.js before committing. Everything is mirrored into Bolas at crank-boy/, with the album at crank-boy/album.html.",
    "links": [
      "films.html",
      "kit.html",
      "registry/links.mjs",
      "AGENTS.md"
    ]
  }
];

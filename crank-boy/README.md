# The Crank Boy

![At School, Villemard, about 1910](assets/at-school-villemard-1910.png)

One postcard, *À l'École* (At School, from *En l'an 2000*, attributed to Villemard, about 1910), and what grew from it: seven versions of a game built by AI programs, an opening film, and Futuretown, where the series' seven cards become short films, games and one playable town. Plain HTML with no build step: open `index.html`.

## Where to look

| | |
|---|---|
| [`index.html`](index.html) | **The album.** The versions as a grid (columns are the starting prompts, rows the AI programs), Compare, and About. Plays the opening film on a first visit. |
| [`shorts/index.html`](shorts/index.html) | **Futuretown.** The seven cards as films, games and one town, each with its process, its blind critic and what it taught. |
| [`shorts/world.html`](shorts/world.html) | **The Town.** Seven cards under one drawn power line, run by one boy's crank. `?d=<card id>` plays one district. |
| [`watch.html`](watch.html) | **Watch.** One theatre for every film in watching order (works numbered), with the process under each film. |
| [`films.html`](films.html) | **Films.** Every film here and in Bolas: 37 films and 6 more elsewhere, with search, filters and a player. Films that belong together are grouped in order (`registry/works.json`): the school card has three, and the Bolas families run in chains. |
| [`kit.html`](kit.html) | **The kit.** Every cut piece, plate, ink, doodle, operator and tool. |
| [`shorts/requests.html`](shorts/requests.html) | **The art department.** Call sheets for a new aesthetic for each card. |
| [`docs/futuretown.md`](docs/futuretown.md) | **The write-up** of everything above. |

Published copy: everything here is mirrored into [Bolas](https://github.com/hartswf0/bolas) at `crank-boy/` by `shorts/tools/to_bolas.py`.

## The versions

| | Ludic | Historicising | Studio 2.0 |
|---|---|---|---|
| **Gemini 4 Argon High, Antigravity** | v8 The Sensory Tether and the Torn Folio | v7 The School of the Year 2000 | v6 Le Contre-Livre |
| **Claude Opus 5.5, Claude chat** | v1 Lesson One, **v9 The Lectern Underneath** | Case 01: À l'école | v5 The Class Book |

Columns are the starting prompts: `docs/scion-ludic.md`, `docs/scion.md`, `docs/scion-game-studio-2.md`.

| Version | What you do |
|---|---|
| 1 Lesson One | Turn the crank that powers the lesson; while it is silent, read the page in the hopper, swap the book, pull a wire |
| 5 The Class Book | Choose a seat or the crank, and decide what the class's own book says |
| 6 Le Contre-Livre | Load paired books into the hopper and whisper so the class writes its own |
| 7 The School of the Year 2000 | Three guided steps comparing Lavisse's 1902 broadcast with an 1884 parish codex |
| 8 The Sensory Tether and the Torn Folio | Lift your ear-cup between the Master's sweeps to see him tear out Folio 42 |
| 9 The Lectern Underneath | The whole class as a cast of layers on clean plates; stop long enough and the machine is gone, with a lectern under it |
| Case 01: À l'école | A research case on the card, with a playable lesson from the pupil's seat |

## Futuretown in one paragraph

Each of the seven cards is worked three ways: a short film, a game, and a place in the Town. Every film and game uses a different operator from the SCION animation swarms (`docs/operators/`). Each lets in real archive film from the [cineosis-lab](https://github.com/hartswf0/cineosis-lab) shot library, the way CINEOSIS does in Bolas, but into a surface the card already has. The doodles over the Town are Quick, Draw! records (CC BY 4.0) chosen by [Secondhand Motion](https://github.com/hartswf0/secondhand-motion). Pictures come from four lanes, kept apart: the card (cut and moved, never repainted), the archive (trimmed, toned, re-printed), drawn marks, and generated images (labelled). The art department tests every new picture by re-printing it in its card's eight inks.

## Make and publish

```sh
node shorts/tools/render.mjs <id>                    # a short, or play/v9, or world: frames from time, synthesised sound
python3 shorts/tools/cut.py <card>                   # cut pieces from a card (outlines in shorts/parts/<card>.json)
python3 shorts/tools/plates.py <cineosis-lab>        # trim the archive plates
python3 registry/build_films.py <bolas>              # registry/films.js and the Bolas thumbnails
python3 registry/build_kit.py                        # registry/kit.js
python3 registry/build_library.py                    # registry/library.js (prompt text for the copy buttons)
node registry/check.js && node registry/links.mjs    # the registry, then every link in every page
python3 shorts/tools/to_bolas.py <bolas>             # mirror into Bolas
```

Methods: [`docs/prompts/shorts.md`](docs/prompts/shorts.md) (a short from a card), [`docs/prompts/town.md`](docs/prompts/town.md) (the Town), [`docs/prompts/art-department.md`](docs/prompts/art-department.md) (new aesthetics). Agents follow [`AGENTS.md`](AGENTS.md) and [`DESIGN.md`](DESIGN.md) and pass notes in [`registry/notes.js`](registry/notes.js).

## Layout

| Path | What it is |
|---|---|
| `index.html`, `films.html`, `kit.html` | The album, the film library, the kit |
| `play/`, `making/`, `scion/` | The versions and how each was made |
| `shorts/` | Futuretown: one page per film, the Town, the art department, `stage.js`, `tools/` |
| `assets/` | The postcard, album photos (`cards/`), the series cards (`series/`), the opening film (`film/`), Futuretown (`shorts/`: parts, plates, films, doodles), version 9 (`v9/`), film thumbnails (`films/`) |
| `registry/` | The shared registry, notes, generated libraries, and the checks |
| `docs/` | The starting prompts, operators, methods, theory and the write-up |
| `room/` | Shared tokens, the site bar, the opening film |

## Ledger

Documented: the postcard and its layout. Interpretation: that the machine turns books into a signal. Invented: the river Verse, Brécourt, Port-Ancel, every book and page, the wall map, the question, the students' names and answers, *Le Contre-Livre*, the torn *Folio 42*, and the lectern under the machine. Generated: the plates and cast of version 9 (made with an image model, supplied by Watson Hartsoe).

Research context: Soyoun Jang, [Archive of Past Futures](https://soyjang.github.io/archive-of-past-futures/). Made by Watson Hartsoe, in collaboration with Soyoun Jang, Jay David Bolter and Collin Freeman, with six AI programs, October 2026.

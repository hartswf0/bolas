# The Crank Boy: protocol for the six agents

Six agents build versions of one game from Villemard's postcard *At School* (about 1910). Each started from a different place:

| | Ludic | Historicising | Studio 2.0 |
|---|---|---|---|
| **Back row: Gemini 4 Argon High, Antigravity** | `ludic-argon` (v8) | `hist-argon` (v7) | `studio-argon` (v6) |
| **Front row: Claude Opus 5.5, Claude chat** | `ludic-claude` (v1) | `hist-claude` (Case 01) | `studio-claude` (v5) |

Starting prompts: Ludic is `docs/scion-ludic.md`, Historicising is `docs/scion.md`, Studio 2.0 is `docs/scion-game-studio-2.md`.

`index.html` opens with a one-minute film for newcomers, then shows this table as an album: one photo per game, columns by instruction, rows by program. Both read everything from `registry/`. Nobody edits `index.html` to add content.

## Shared files

| File | What it holds | Who edits it |
|---|---|---|
| `registry/registry.js` | Prompts, models, seats, versions, proposals, prompt library | Each agent edits its own entries |
| `registry/notes.js` | Notes between agents | Append only |
| `registry/library.js` | Prompt text for the copy buttons, generated | `python3 registry/build_library.py` |
| `registry/films.js` | Every film in the Crank Boy and Bolas, for `films.html`, generated | `python3 registry/build_films.py <bolas checkout>` |
| `registry/kit.js` | Every piece, plate, ink, doodle, operator and tool, for `kit.html`, generated | `python3 registry/build_kit.py` |
| `registry/check.js` | Validates the registry, notes, films and kit | Run before every commit |
| `registry/links.mjs` | Checks every local link and asset in every page | `node registry/links.mjs` before every commit |
| `registry/cards.py` | Photographs each game for the album | Run after adding or changing a game |
| `DESIGN.md`, `room/room.css` | Shared palette, type and the return link | Change by note first |

## Before you work

1. `git pull --rebase`
2. Read this file, `DESIGN.md`, `registry/registry.js`.
3. Read every note in `registry/notes.js` addressed to your seat or to `"all"`. Answer questions asked of you with a note whose `re` is the question's id.

## Adding or changing a version

1. Game at `play/vN.html`, process page at `making/vN.html`. Take the next unused number.
2. Add or update your entry in `versions` in `registry/registry.js`. Fields: `id`, `agent`, `tag`, `title`, `status`, `date`, `play`, `making`, `card`, `youPlay`, `line` (one paragraph, plain sentences a newcomer can follow), optional `mirror`.
3. Photograph the game's first screen for the album: `python3 registry/cards.py <id>` writes `assets/cards/<id>.jpg` (needs Playwright and Pillow). If you cannot run it, leave a note asking for it.
4. Each page links back to `../index.html#<version id>` with the text "The classroom". See `DESIGN.md`.
5. New prompt documents go in `docs/`, get an entry in `library`, then run `python3 registry/build_library.py`.

## Passing a note

Append an object to `registry/notes.js`:

```json
{ "id": "n5", "date": "2026-10-24", "from": "studio-argon", "to": ["studio-claude"], "re": "n4",
  "subject": "Where whispering came from",
  "body": "Plain sentences: what you changed, what another seat could use, what you want to know.",
  "links": ["making/v6.html"] }
```

Use the next free id. `to` is a list of seat ids or `["all"]`. Do not edit or delete other agents' notes.

## Finishing

1. `node registry/check.js` must print `OK`.
2. Commit message starts with your seat id: `hist-argon: remove v7 mirror (n3)`.
3. `git pull --rebase`, then `git push`. If the rebase conflicts in `notes.js`, keep both sides' notes.

The prompt that puts an agent on this protocol is `docs/prompts/join-the-room.md`. It is also on the shelf in the classroom with a copy button.

## Pages

| Page | What it is |
|---|---|
| `index.html` | The album: the versions as a grid, Compare, About. Plays the opening film on a first visit |
| `shorts/index.html` | Futuretown: the seven cards as films, games and one town; the project page |
| `shorts/world.html` | The Town, playable. `?d=<card id>` opens one district. `play/v9.html` is version 9 |
| `shorts/requests.html` | The art department: call sheets for new aesthetics |
| `films.html` | Every film, from `registry/films.js`. `#<film id>` opens one; `#g:<group>` filters |
| `kit.html` | Every element, from `registry/kit.js` |

Reading pages carry the site bar: `<script src="../room/site.js" data-root="../" data-here="films"></script>` just after `<body>`.

## Adding a film

Render it (`node shorts/tools/render.mjs <id>`), then run `python3 registry/build_films.py <bolas checkout>` and `node registry/check.js`. A version with a `film` field in the registry appears in the library as "played". A Futuretown short appears from `shorts` in the registry. Bolas films come from Bolas's `catalog.json`; do not copy them here.

**Films that go together.** If the new film is a second film for a card, program or idea, add it to `registry/works.json` as a member of a work (or start one), with a `role` and one sentence `note` on how it follows the film before. `build_films.py` refuses an unknown film or a film in two works, and `check.js` checks every work. `films.html`, the Futuretown page, the kit and the Bolas film pages all read it (`to_bolas.py` copies it to `bolas/tools/site/works.json`).

## Publishing into Bolas

`python3 shorts/tools/to_bolas.py <bolas checkout>` mirrors this repository into `bolas/crank-boy/`. The Bolas landing page is `crank-boy/index.html`; the album is `crank-boy/album.html`. Run it after any change, then commit in Bolas.

## Opening film and series

- `room/film.js` plays the opening film. It reads the registry (versions, prompts, series, lab) and `assets/film/lines.js`.
- Voices: edit `assets/film/script.json`, then run `python3 registry/voices.py <folder with kokoro-v1.0.onnx and voices-v1.0.bin>`. It writes `assets/film/vo/*.mp3` and `assets/film/lines.js`.
- Each version entry also has `made` (how it was made, one or two sentences) and `looks` (what its first screen looks like). The Compare tab shows both.
- `series` lists the En l'an 2000 cards. Each has a short film and a district in the Town (`short`, `district`). To build a full game from one, add it as a new version and set that card's `status` to `built`.

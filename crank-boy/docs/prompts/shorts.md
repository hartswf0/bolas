# Make a short from a series card

Use this with any card in the series (`registry/registry.js`, `series`) and one operator from the SCION animation swarms (the seven used so far are in `docs/operators/`). The result is a 20 to 25 second film that brings the card to life and lets a real piece of archive film into it.

## What you start with

- The card, as printed. Its pixels are the cast: cut pieces out of it, do not redraw or regenerate it.
- One operator. Read it whole. It names the creative theorem, the formal primitives and a numeric test. Follow its theorem, not its proof scene: the card supplies the scene.
- The archive, reached the way CINEOSIS reached it. The cineosis-lab library (github.com/hartswf0/cineosis-lab) holds shots found through movingimagearchive.com's shot search, one natural-language query per shot. Its read shots ship as local clips in `lab/clips/<id>.mp4` with their source film, year and timecode in the lab's JSON. Search those first. If you can reach movingimagearchive.com, query it the way `search.py` in the lab does and record the clip id and source.

## Steps

1. **Read the card.** Say in one sentence what it already implies: who holds the handle, what moves, what is about to happen.
2. **Pick the plate.** One or two archive shots that answer the card: the thing it predicted as it was later filmed, or the room it would really be shown in. Add each to `shorts/plates.json` with its clip id, in and out times inside the lab clip, title, year and what it shows. Run `python3 shorts/tools/plates.py <cineosis-lab checkout>`. Plates are trimmed and toned, never painted.
3. **Cut the pieces.** Outline each moving piece in `shorts/parts/<card>.json` and run `python3 shorts/tools/cut.py <card> --check`. The holes are filled with the card's own colours. Use `"matte": "auto"` with `"ground"` sample boxes when the piece's own drawing must be its edge (silhouettes).
4. **Compose.** Copy a page in `shorts/` (each is one composition for `shorts/stage.js`). Everything is a function of time: the camera, each piece's motion, the plate's clock and the sound cues. Keep the operator's numeric test in the page and print its result (see the scrubber's contact test).
5. **Render.** `node shorts/tools/render.mjs <id> --stills 3,8,13` for stills; `node shorts/tools/render.mjs <id>` for the film. Sound is synthesised from the page's cues (`shorts/tools/sound.py`); nothing is sampled.
6. **Blind critique.** Give contact sheets to a reviewer who has not seen the intent. Fix what does not read. Record what was reviewed and what was not.
7. **Register.** Add an entry to `shorts` in `registry/registry.js` and a `short` field to the card's `series` entry. Run `node registry/check.js`.

## House rules

- Every page has a ledger: Observed (the card and the plates, with titles and years), Cut and moved, Drawn and synthesised.
- The film says on screen where each plate comes from.
- Plain captions, one idea each. The end card names the operator, the card and the plates.

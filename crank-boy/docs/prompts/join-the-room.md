You are one of six agents building versions of The Crank Boy, a set of games after Villemard's postcard "At School" (En l'an 2000, about 1910). The repository is https://github.com/hartswf0/crank-boy. Its index page opens with a one-minute film, then shows an album with one photo per game: columns by starting instruction, rows by AI program.

The six seats:
- Columns are starting prompts: Ludic (docs/scion-ludic.md), Historicising (docs/scion.md), Studio 2.0 (docs/scion-game-studio-2.md).
- Rows are models: back row Gemini 4 Argon High in Antigravity; front row Claude Opus 5.5 in Claude chat.
- Seat ids: ludic-claude, hist-claude, studio-claude, ludic-argon, hist-argon, studio-argon.

My seat is: [SEAT ID]

Before you change anything:
1. git pull --rebase.
2. Read AGENTS.md (the protocol) and DESIGN.md (the shared look and the return link).
3. Read registry/registry.js. It is the single source the index draws from.
4. Read registry/notes.js, at least every note addressed to your seat or to "all". Answer any question asked of you.

When you add or change a version:
5. Put the game at play/vN.html and its process page at making/vN.html. Do not edit index.html to list it.
6. Add or update your entry in "versions" in registry/registry.js: id, agent (your seat id), tag, title, status, date, play, making, card, youPlay, line. Write title, youPlay and line for someone who has never heard of the project. Keep the file valid JSON between the first { and the last }. Then run python3 registry/cards.py <id> to photograph the game for the album.
7. Give every page you make a link back to the classroom at index.html#<your version id>, labelled "The classroom".
8. If you add a prompt document, put it in docs/, add it to "library" in the registry, then run python3 registry/build_library.py.

To talk to the other agents:
9. Append a note to registry/notes.js: id, date, from (your seat id), to (a list of seat ids, or ["all"]), re (the id of the note you answer, or null), subject, body, links. Say what you changed, what you learned that another seat could use, and any question you have. Plain sentences.

Finish:
10. Run node registry/check.js. It must print OK.
11. Commit with your seat id at the start of the message, for example "studio-argon: add version 9", then git pull --rebase and git push.

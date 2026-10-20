# CRASH LAB

Bolas · department of dramaturgical crash testing. Experiments in authored motion. Figures keyed by hand in a rig, measured like crash-test dummies, and set into archive film.

Live: https://hartswf0.github.io/bolas/

| Program | |
|---|---|
| [The Crash-Test Family](family/) | Three test dummies in a measured bay. Every touch, step and fall is scored for where the weight is, whether the feet hold and whether a hand lands where it was sent. |
| [CINEOSIS](cineosis/) | The crash-test family performs the 45 signs of Deleuze's cinema books, after David Deamer's taxonomy: first in the measured bay, then inside real archive film, then by hand, and finally as a making-of with a blindfolded Critic. |
| [The Found Odyssey](found-odyssey/) | Homer's lines are asked by the CALL track and answered by archive speech; a drawn cast acts in graded archive plates. Each episode runs one formal experiment. |
| [WYGWYL](wygwyl/) | The poet as a jointed paper cut-out made from his own photographs, set over the cineosis-lab cel cuts with the reading on the soundtrack. Every patch is built from the lab's cel database. |

- [Characters](characters/) · [Films](films/) (26) · [Process](process/) · [Docs and prompts](docs/)
- Lab pages: [Bolas Pencil Test](lab/pencil-test/) · [Bolas Range Test](lab/range-test/) · [The Physical](lab/the-physical/) · [Dramaturgy Crash Lab](lab/crash-lab/)

## How the site is built

The site is generated from one catalog. `catalog.json` is its published form: programs, characters, films (with loglines,
running times, thumbnails) and process stages. Pages, thumbnails and the sitemap are generated from it; adding a film is one
catalog entry plus its file under `media/films/`.

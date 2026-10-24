# CRASH LAB

Bolas · department of dramaturgical crash testing. Experiments in authored motion. Figures keyed by hand in a rig, measured like crash-test dummies, and set into archive film.

Live: https://hartswf0.github.io/bolas/

| Program | |
|---|---|
| [The Crash-Test Family](family/) | Three test dummies in a measured bay. Every touch, step and fall is scored for where the weight is, whether the feet hold and whether a hand lands where it was sent. |
| [CINEOSIS](cineosis/) | The crash-test family performs the 45 signs of Deleuze's cinema books, after David Deamer's taxonomy: first in the measured bay, then inside real archive film, then by hand, and finally as a making-of with a blindfolded Critic. |
| [The Found Odyssey](found-odyssey/) | Homer's lines are asked by the CALL track and answered by archive speech; a drawn cast acts in graded archive plates. Each episode runs one formal experiment. |
| [WYGWYL](wygwyl/) | The poet as a jointed paper cut-out made from his own photographs, set over the cineosis-lab cel cuts with the reading on the soundtrack. Every patch is built from the lab's cel database. |

- [This Side Up](this-side-up/): case studies of the cardboard cut-out films, each with a full case page of versions, prompts, critic rounds and sheets
- [PAELEO](paeleo/): Promptable Augmented Environments Lab · Ekphrastic Operations. One research program at three scales (AEL, PEO, PAELEO); its films are made with the SCION swarms
- [Characters](characters/) · [Films](films/) (26) · [Process](process/) · [Docs and prompts](docs/)
- Lab pages: [Bolas Pencil Test](lab/pencil-test/) · [Bolas Range Test](lab/range-test/) · [The Physical](lab/the-physical/) · [Dramaturgy Crash Lab](lab/crash-lab/)

## How the site is built

The site is generated from one catalog. `catalog.json` is its published form: programs, characters, films (with loglines,
running times, thumbnails) and process stages. Pages, thumbnails and the sitemap are generated from it; adding a film is one
catalog entry plus its file under `media/films/`. Every film gets a test number (FAM-03, CIN-05, ODY-E7, WYG-01) from its
program and its order in the catalog.

## The cast around the films

The characters that sit on cards, peek over players and talk to the viewer are sprite strips in `media/cameo/`, rendered
from the rig at one shared scale (`cameos.json` records each strip's frame size and its anchor: soles, seat or hands).
`site/cameo.py` says who appears around which program's films and what they say; `assets/cameo.js` places them, animates
them and has them react to the player (they sit down and turn to watch on play, turn back on pause, cheer at the end).
A new character is a set of sprites plus one entry for its size and lines. The poet is a real person: he appears but never speaks.

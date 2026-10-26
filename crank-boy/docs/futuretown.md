# Futuretown: the write-up

Seven *En l'an 2000* postcards (attributed to Villemard, about 1910), each brought to life three ways, then joined into one town, then given an art department to take the town into new aesthetics. This is the record of what was made, how, what a blind critic found, and what is next. Pages: `shorts/index.html` (the project page), `shorts/world.html` (the Town), `shorts/requests.html` (the art department), `shorts/school-melies.html` (the first proof scene), `play/v9.html` (a better Crank Boy on clean plates). The same pages are mirrored into Bolas at `bolas/crank-boy/`.

## 1. Seven shorts

One short per card, each worked by one operator from the SCION animation swarms (54 standalone animation prompts). The rule throughout: **the card is the cast**. Pieces are cut out of the printed card and moved; the holes they leave are filled with the card's own colours (`shorts/tools/cut.py`). Nothing in a card is redrawn or generated.

| Card | Operator | Archive plate |
|---|---|---|
| À l'école | Gilliam, cutout metamorphosis | *Letter From an Airline Pilot* |
| Un frotteur électrique | Inverse kinematics | *Frigidaire Finale* (1957) |
| The barber | Forward kinematics | *Barbers* (1959) |
| Phonograph and cinema | Sound to action | *Fatty's Magic Pants* (1914), *Let's Go To The Movies* (1948) |
| Air cabs over Paris | Multiplane parallax | *Airport America* (1954) |
| Flying firemen | Secondary dynamics | *Watershed wildfire* (1958), *The Balloonatic* (1923), *Fire and Police Service* (1947) |
| Motor skates | Lotte Reiniger, shadow theatre | *Autoraces op boulevard Scheveningen* (1927), *Industry on Parade* |

**Archive film, the CINEOSIS way.** CINEOSIS, in the Bolas lab, set its figures into unaltered archive shots from the cineosis-lab library. That library found its shots through movingimagearchive.com's shot search, one plain-language query per shot. The shorts use the same library the other way round: the archive comes into the card through a surface the card already has, such as a mirror, a screen, a polished floor, a sky or a fire. Each plate is a cut-free stretch of one shot, trimmed, toned and masked, never painted, and recorded by clip id in `shorts/plates.json`.

**How they are made.** Each short is one page (`shorts/stage.js`) that draws any frame from the time alone. `node shorts/tools/render.mjs <id>` photographs every frame and adds a soundtrack synthesised from the page's cues (`shorts/tools/sound.py`). Nothing in the sound is sampled.

**The blind critic.** A fresh reviewer, told nothing of the intent, described contact sheets of all seven. One short read, four partly read and two failed. Air cabs failed because its keyed biplane broke into streaks; the skates failed because solid silhouettes of overlapping figures became blobs. Each short was fixed once and has not been reviewed again.

## 2. The Town

`shorts/world.html` puts the seven cards in a row under one power line drawn in Secondhand Motion's way. Nothing runs unless somebody turns the crank in the school, and power reaches each card later the farther it is from the boy. The doodles drawn over the cards are real Quick, Draw! records (CC BY 4.0) chosen by Secondhand Motion for its own cartoons.

- **Seven games.** Each card is a district with its own goal and an operator its short did not use: tabletop capture (the crank), Sketchpad constraints (drag a brush), Character Animator triggers (cut on the beat), JibJab recasting (choose who answers on the screen), Rive state machines (the cab tires), state machines that refuse (the flyers will not go near the fire without water), and drawing substitution (a bad stride swaps in the fallen drawing). All seven passed a headless play test with real inputs.
- **The recastable cast.** After JibJab: a film whose cast can be replaced without remaking it. The crank boy, the maid and the barber's lever man are each cut into a performing upper body and planted legs, so any of them can stand in another's place. The performance is a function of the actor's height only, so it does not change. The project page runs this test live; the largest difference between actors over a crank turn is 1.3e-15 px. Front-to-profile turns and grasp, collide and recover are not built.
- **The cartoon.** The same engine, stepped from a fixed script, renders a 96-second film of the Town (`assets/shorts/films/world.mp4`).

## 3. The art department

`docs/prompts/art-department.md` is a swarm prompt, *SCION // FUTURETOWN*, for giving each district its own aesthetic while it stays one town.

- **The test that holds the town together.** A paleofuture card is a print: about eight inks and a key plate slightly off register. `shorts/tools/stencil.py` takes a card's eight inks by k-means and re-prints any frame through the print's dot screen. A 1906 San Francisco ruin, a 1915 exposition colonnade and a 1966 cleaning cart all read as part of their cards (`assets/shorts/art/`). Anything new on screen must survive this re-print.
- **A fourth lane, Generated.** Image-model output is allowed for three jobs only, each labelled with model, prompt, seed and test: blank pages (inpainting the holes and extending a card past its frame), rig coverage (views the card never drew) and in-betweens. A generated image never replaces a figure the card already draws and never stands in for archive. None has been run: this container has no image model.
- **Better rigs**, in order: split at real joints; bend long pieces as-rigid-as-possible (Igarashi et al. 2005); generate turnarounds and choose between views by dynamic programming (after Pose2Pose, Willett et al. 2020); retarget real performances such as Chaplin in *The Rink* (1916); test like a crash lab.
- **Backgrounds from other archives**: the 408 cineosis-lab shots from 1897 to 1916, the cards' own years; the British Library's Mechanical Curator; Smithsonian Open Access; the Library of Congress; Rijksmuseum and the Art Institute of Chicago through IIIF; Gallica.
- **Call sheets** (`shorts/requests.json`): for each card, a new aesthetic, the swarm that leads it, what other swarms would do, plates by clip id, generation prompts with acceptance tests, and asks. The aesthetics: a Méliès trick-film stage (the school), an Ernst engraving collage (the scrubber), turnaround portraits (the barber), a Mouris image torrent (phonograph), Norstein mist (air cabs), the 1906 fire as a Foldès metamorphosis (firemen), and Chaplin's rink retargeted (skates).

## 4. The first proof: À l'école as a trick film

`shorts/school-melies.html`, rendered as `assets/shorts/films/school-melies.mp4` (21 s).

- **Méliès's grammar, kept strictly.** The camera never moves. The card stands on a stage behind a proscenium, with curtains and footlights. Every change is a stop-substitution on an exact frame, with two white frames as a splice and a puff of smoke where a cut is hidden. Titles are black cards with stars.
- **Three substitutions.** First, the wall and window become the falling stars of *The Eclipse* (Méliès, 1907, cineosis-lab clip ed87f1da), re-printed live in the card's four darkest inks and its white. The surface is keyed out by the card's own wall and glass colours (`assets/shorts/parts/school/wall.png`), not painted, so the pictures on the wall and the pupils stay. Second, the teacher's book comes out of the machine as a moon, drawn from two Quick, Draw! records (a moon and a face), and settles where a pupil's head was. Third, it turns back into a book on his desk.
- **The film is cranked.** The story's clock runs as fast as the boy turns: it slows when he slows, as a hand-cranked projector did, and it is shown at 16 frames a second with gate weave, flicker, scratches and dust.
- **What it shows.** An archive frame from the card's own decade, re-printed in the card's inks, can replace a surface of the card on one frame without reading as a seam. The proof has not been blind-reviewed. The re-print now runs live in `stage.js` (the `inks` option of `plateFrame`), so any district can use it.

## 5. A better Crank Boy: version 9, The Lectern Underneath

Watson made five image-model plates of *À l'école* that line up with the card and with each other to the pixel. Each has less in it: the machine with empty helmets, the machine alone (twice, identical), a lectern with helmets, and the lectern alone. He also made a cast: six pupils with rough head and body layers, the teacher reading and pointing, and the crank boy. This was his motion proof (`crankboy_motion_proof`), extracted from generated sprite sheets by connected alpha components.

- **Layers by difference.** Because the plates line up, subtracting one from another gives a layer already in place. The machine is where the machine plate differs from the lectern plate. The tables and the lectern's front are cut by hand-placed outlines, so the pupils can sit between the rows and the teacher can stand behind the lectern (`assets/v9/build_layers.py`).
- **The game** (`play/v9.html`) is Lesson One with the whole class. Turn the crank and six heads bow into the lesson while the wires pulse. Stop, and they come up. Stop for six seconds and, in one stop-substitution, the machine is gone: there was a lectern under it, and the teacher comes to it. Turn the handle for three seconds and the machine is back. The bell rings after ninety seconds. Play-tested in a browser with real key and dial input, at desktop and phone size.
- **Why the lectern.** The card never shows what is under the machine. A clean plate has to invent something there, and the model chose the older future: a man at a desk, talking. The game is built on that invention, and its ledger says it is the model's.
- **The film** (`assets/shorts/films/v9.mp4`, 52 s) is the game stepped from a fixed script.
- **Limits.** The head and body split is a horizontal cut. Nobody walks or turns. The crank boy's arms do not follow the crank. There is one view of everyone. The plates' and cast's model and prompts are not recorded in this repository.

## Films per card, and films that go together

Most cards have one film. The school card has three, asked three different questions of the same room: the Gilliam-cutout short, the trick-film proof scene, and version 9 played on clean plates. Bolas has the same shape at larger scale: the crash-test family in three films, CINEOSIS in five passes (three reels are cuts of the handmade film), the Found Odyssey as a search for its look followed by seven episodes, and WYGWYL from one ink cel to a poem.

`registry/works.json` records this: each work lists its films in order, each with a role and one sentence on how it follows the one before. `films.html` shows each work as a numbered block (`films.html#w:school-card`), the Futuretown page and the kit list every film for a card, and every Bolas film page carries a "Part of" row with before and next links.

## 6. Lessons

1. The card's own drawing is the best cast.
2. The archive belongs on a surface the card already has.
3. Do not key thin things against similar tones; give the archive its own window.
4. Numbers and eyes measure different things; every short needs both a numeric test and a blind critic.
5. Keep the performance apart from the performer; that is what made the Town possible without remaking the shorts.
6. Re-printing in the card's inks is a stronger join than toning: the archive stops looking pasted and starts looking printed.
7. Low resolution limits the camera; three cards are under 600 px wide.
8. Aligned clean plates turn a card into layers by subtraction. One plate per thing taken away is worth more than any amount of inpainting a hole at a time.

## 7. Next

- Blind-review the Town, the fixed shorts, the Méliès proof and version 9.
- Ask for aligned plates of the other six cards, and a cast for each, in the same form as the school's.
- Run the Generated lane on one call sheet: the school's blank pages and the teacher's turnaround.
- Fetch the call sheets' plates that are only on the lab's CDN: *The Rink*, *A Trip Down Market Street* and the 1906 fire.
- Get better scans of the four smallest cards.
- Decide how the firemen district should treat the 1906 fire, in which people died.
- Take the three handle-holders and the seven plates into the CINEOSIS rig as candidate passages, one per proposed sign, under the same blind review CINEOSIS uses.

## Credits

Cards: *En l'an 2000*, attributed to Villemard, about 1910. Archive: the cineosis-lab shot library (github.com/hartswf0/cineosis-lab). Doodles: Quick, Draw! by Google Creative Lab and its contributors, CC BY 4.0, as chosen by Secondhand Motion (github.com/hartswf0/secondhand-motion). Operators: SCION · Animation Lineage Swarms. Fonts: IM Fell, by Igino Marini. Made by Watson Hartsoe, with Claude.

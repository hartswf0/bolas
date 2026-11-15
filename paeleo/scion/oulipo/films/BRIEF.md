# Brief for film agents

Goal: each SCION swarm prompt in `prompts/<slug>.md` gets one original, handmade short film that carries out that prompt's **Hard proof** (section 6), honours its invariants (section 4), and passes its verification fixture (section 7) as far as a solo coded film can. Use the station seed (section 10) whenever the proof leaves the story open — the brass key, bench, bell, sealed envelope and closed service door tie the 25 films together.

"Handmade, from scratch" means: every frame is drawn in code with `films/kit.py` (PIL), every sound is synthesized with `Mix` in the kit. No downloaded images, no stock audio, no generated imagery, no reference images copied from `assets/references/` (look at them for ideas only). Text, jokes, verse and dialogue are original.

## How to work
- Working dir: `/home/user/bolas/paeleo/scion/oulipo`. Read `films/kit.py` fully first, then `films/anemic-cinema.py` (a finished example) and its note `films/notes/anemic-cinema.txt`.
- One script per work: `films/<slug>.py`. Run `python3 films/<slug>.py --stills 2 7 13 ...` to write PNG stills to `films/stills/<slug>/`, LOOK at them with the Read tool (make a contact sheet to save context), fix what is ugly or illegible, then `python3 films/<slug>.py` for the real render → `assets/films/<slug>.mp4` + poster `.webp`.
- **Do not edit `films/kit.py`** (other agents depend on it). If you need more helpers, put them in your own script or in `films/kit_<yourname>.py`.
- Durations: follow the proof (most say 20–60 s). Where a proof asks for two cuts / versions / soundtracks, put them in one film in sequence with a clear title card between ("CUT 1 · ordinary handoff", "CUT 2 · illicit"). Keep each film ≤ 75 s and ≤ ~5 MB.
- Comics and page works: make the film a reading of the page — panels appear/are read in order, the camera moves panel to panel, then show the whole page/grid at the end long enough to read. Palindromes must repeat art exactly (render the panel once, reuse the image). Folds should animate.
- There is no text-to-speech. Voices are captions (`ink.caption`) and, if wanted, `mix.murmur` under them (non-verbal voice-like sound). Say so in the note. A declared silence is allowed where the prompt asks for one.
- Make it look good: compose with intent, use the palette in kit.py (paper, ink, accent red, brass), keep text legible at 960×540, vary the drawing style per work where the prompt calls for distinct visual systems (e.g. A Morning Stroll's three eras). Use `boil`/`wobble` for a hand-drawn line; set boil=0 for exact geometry.
- Write `films/notes/<slug>.txt`: one paragraph (60–110 words) in plain language describing what the film does, how it carries out the proof, and what is declared (captions instead of voices, synthesized sound, any part of the proof it could not do). No marketing tone.
- Do NOT git commit or push. Do not touch build.py, operator.js, index.html or catalogue/. Don't delete other agents' files.
- At the end, report per slug: duration, size, one line on what it shows, and any shortcoming.

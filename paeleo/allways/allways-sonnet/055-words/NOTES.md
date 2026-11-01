# 055-words — Words: Polysemic Relay ("draw")

Files: `edl.json` → `055-words.mp4` (49.1 s, 4.2 MB) + `055-words.ledger.json`;
alternate pivot cut `edl-alt.json` → `055-words-alt.mp4` (53.8 s, 4.5 MB) + ledger; `contact.jpg` (one frame every 2 s).
Revision: first assembly, 2026-10-31. Builder: words-moments (scratch agent). **Independent critic review: PENDING.**

How I checked: I looked at contact sheets (6 frames for each of the 405 archive clips, then 8–10 frame sheets of ~40 candidates at chosen in/out ranges), audio RMS envelopes and spectrogram images. I did **not** watch the clips or the finished film at normal speed, and I could not listen. Every claim about what a shot shows comes from still frames. Claims about sound come from level and spectrogram readings, not from hearing it.

## 1 · Theorem as adapted to archive footage

Over about 45 s, a run of hands-and-bodies actions taken from unrelated public-domain films should let a viewer infer one English verb, *draw*, without the word ever appearing. The sense moves from **draw = inscribe** to **pull out**, **take (a card)**, **inhale**, **attract**, **draw a crowd / haul up**, and back to **inscribe**. The emotional direction is meant to turn halfway. Before the turn, small private hand skills are under a person's control (pencil, reel, cards, cigarette). After it come forces that pull things and people: a magnet, a crowd pulled toward a monument, a statue hanging on a cable, and an emergency flight path. The return to the opening map should make its pencil line read as a planned route and not just a doodle.

## 2 · Forage log

**Method.** I built my own contact sheets of all 405 sound clips (`scratchpad/words-moments/sheets/clip_*.jpg`, sorted by title) and all 474 loops (`loop_*.jpg`). Then I ran regex searches through `forage.py` on queries, titles and subjects: `draw|drawing|curtain|drawer|chalk|pencil|sketch|blackboard`, `run|race`, `turn|spin|wheel|carousel`, `spring|jump|leap`, `press|iron|printing`, `pitch|throw|baseball`, `break|crack|smash`, `light|lamp|match|candle`. The query text often misleads. For example, `9188fbc4` is tagged "floor plan drawn in white chalk" but shows a bank office. Every choice below was made from the frames.

**Candidate words, with what the archive can actually show:**

| word | visible senses found (clip ids) | verdict |
|---|---|---|
| **draw** | pencil line on a map `c3c494ef`; pencil house plan `3a48bbc4`; chalk weather map `dbb38088`; marker loop path `6022db06`; film pulled off a reel `8266284b`; cards drawn at a table `28329221`; drawing on a cigarette `cde56cc9`; magnet attraction `287f3379`; crowd gathered under a hoisted statue `5524afe5`; figure moving a curtain `491529e4` | **chosen**: 6–7 clearly different senses, each readable from frames |
| turn | knob `7102b861`, pages `f9cc73a7`/`d2d995e6`, potter's wheel `163bcd54`, reel rewinding `77a0080e`, dial `18c68920` | almost all are the same physical sense (rotation). Weak polysemy |
| light | match/cigarette `cde56cc9`, flashbulb `cc0ea66a`, lamps, sun | the senses (illuminate / ignite / weight) are not visibly separable |
| break | bread `0e86363a`, smashed windows `6697b1ff` | only two senses |
| spring / pitch / press | diver `652e9a2d`, `f24053fe`; pitcher (one frame in `64a0a6c1`); record press `b3ef2f32`, type `aaf17c56` | 1–2 senses each |
| run | runner on beach `b8637147` | one sense |

**Surprises.** *Facts About Film* (1948) has a boy pulling a film strip off a reel. That makes "draw" refer to the medium itself. *De Joodsche invalide* (1939) has a close, high-contrast card game seen only as hands and cups. *Surviving Forced Landings* (2008) has an instructor closing a looping path with arrows on a whiteboard, which is nearly the "line resembles the path taken" image the prompt asks for.

**What the archive does not have.** No curtain clearly drawn open or shut by a hand. `491529e4` shows a figure moving through and behind a curtain, and the stage curtains in the 1939 Medicus reels are already shut. No drawer being pulled open: the only "man opening drawers" tag is a 3 s loop of the 1963–64 Dallas reconstruction (`f2249e2f`), which I excluded because of its context. No tied game. No pistol draw: `a1ae303e` *Fire and Police Service* shows a line already firing. No group visibly *moving closer* to inspect something; the crowd in `5524afe5` is already gathered. **Almost no non-verbal sync sound**: nearly every clip with sound carries narration, which I cannot transcribe (no speech-recognition tool was available).

## 3 · The cut (main, `edl.json`)

| t (film) | source (year) · clip id · clip in–out | sense / edge | why |
|---|---|---|---|
| 0.00–1.05 | *Caught Mapping* (1940) · c3c494ef · 0.55–1.60 | **inscribe** | Opens on a pencil already moving along a road map. The source's held non-verbal tone (0.5–1.6 s, steady band in the spectrogram) is kept at −6 dB. |
| 1.05–3.55 | same · 1.60–4.10 | inscribe, continued | Narration muted. Cut on the moving hand. |
| 3.55–6.75 | *Facts About Film* (1948) · 8266284b · 9.40–12.60 | **pull out** | A hand draws film strip off a reel. Edge: the hand pulling a line continues the pencil's line. In-point set after the last narration syllable, so the source track is near-silent (−56 dB). |
| 6.75–12.95 | *De Joodsche invalide* (1939) · 28329221 · 0.30–6.50 | **take a card** | Hands lay down and pick up cards among coffee cups. Edge: pulling a flat strip becomes pulling a flat card. The source has no audio track. |
| 12.95–22.15 | *Ask Me, Don't Tell Me* (1961) · cde56cc9 · 0.30–9.50 | **inhale** | A young man strikes a match, lights a cigarette, draws on it and lets out the smoke. The source track, which reads as music in the spectrogram (not verified by ear), is kept at −9 dB. This is the last private, hand-controlled action. |
| 22.15–25.55 | *Principles of Electricity* (1945) · 287f3379 · 0.0–3.4 | **attract** (pivot) | **Deliberately unbridged, silent cut.** A small particle drifts between N and S blocks. Animation, so the analogy is plainly an analogy. The audio track is muted because I could not confirm it has no speech. |
| 25.55–31.55 | *Wording standbeeld van stadhouder Willem III* (1921) · 5524afe5 · 0.5–6.5 | **draw a crowd** | A crowd with bicycles stands looking up. Silent source. |
| 31.55–39.05 | same · 9.5–17.0 | **haul / draw up** | An equestrian statue hangs on a crane cable over its plinth while men guide it. I could not tell from the frames whether it is going up or coming down. |
| 39.05–43.45 | *Surviving Forced Landings* (2008) · 6022db06 · 0.0–4.4 | **inscribe** again | A hand closes a looping path with arrows, then withdraws, and the loop stays. Instructor speech muted. |
| 43.45–46.15 | *Caught Mapping* (1940) · c3c494ef · 3.4–6.1 | **return** | The opening map. The hand lifts away and the drawn route stays. Repeats 0.7 s (3.4–4.1) of the opening, on purpose. Fades out. |
| 46.15–49.15 | card | — | "Sources: movingimagearchive.com · see ledger" |

**Sense graph (directed edges, each with an explicit reason):**
inscribe → pull-out (a moving hand drawing a line becomes a hand drawing a strip; both draw a line outward) → take-a-card (pulling a flat strip becomes pulling a flat card off a table) → inhale (from a table of men to one person's private act; the shared action is drawing *something toward oneself*) → attract (unbridged: the viewer has to supply "toward oneself", now with no hand) → draw-a-crowd (attraction between bodies) → haul (what the crowd looks at is being drawn on a cable) → inscribe-as-route (a drawn path where something has to come down safely) → return to inscribe (the first line now reads as a route).
The ledger records every cut against a source time range.

**Alternate pivot (`edl-alt.json`):** the magnet shot is replaced by *The Door to Heaven* (1941) · 491529e4 · 7.5–15.5, where a figure moves behind and through a curtain beside a lamp (dialogue muted). This tests whether a *literal* curtain pivot is legible where the magnet *analogy* is not. Everything else is identical.

## 4 · Departures from the prompt's hard proof

- **No newly filmed drawing-to-curtain-to-drawer chain.** The archive has no clean hand-drawn curtain and no drawer, so the bridge goes from pencil to film strip (pull) to card. The curtain appears only in the alt cut, as a figure moving the cloth, which is weaker than "drawing a curtain".
- **No tied game.** "Draw a card" stands in, because the visible situation establishes it without commentary.
- **The group does not draw closer.** It is already assembled. "Draw a crowd" depends on the crowd *looking up* and on the next shot showing what they look at. Adjacent shots here come from the same 1921 newsreel, so presenting them together does not invent an encounter.
- **Source sound across the first two handoffs: not achieved.** The relevant sources carry narration I can neither transcribe nor caption, so I muted it. The film is mostly silent, with one non-verbal tone at the start, the reel shot's own near-silence, and source music under the cigarette shot. No newly composed sound. The prompt's "captions for speech" is moot because no speech is audible.
- The ending repeats the opening source and does not use a newly drawn line. The whiteboard loop does the "path taken" work, and the return re-reads the first line.
- *De Joodsche invalide* (1939) records residents of the Jewish home for invalids in Amsterdam, most of whom were deported in 1943. The film does not state or exploit this. The shot is used only for its visible action (hands, cards, cups) and is not framed for pathos.
- *Ask Me, Don't Tell Me* (1961) is a San Francisco youth-program film. The smoker is shown performing an ordinary act, not as a diagnosis or a lesson.

## 5 · Self-review against §5 (builder's own view, not acceptance)

- *Organizing relation identifiable, with ≥2 senses:* probably yes for inscribe / pull / card / inhale, since all four are hand actions held long enough to read. The magnet and statue are the weakest links (perceptual guess, unverified).
- *Transitions do more than repeat a shape:* the reel-to-card and card-to-cigarette edges change the sense while keeping a pulling motion. The pencil-to-reel edge is the most shape-dependent.
- *Return changes the first shot:* intended, via the whiteboard loop just before it. Not tested on a viewer.
- *Sound supports inference without explaining:* only partly. The film is mostly silent because of the narration problem, and the sound design is the largest gap.
- *No invented encounters:* adjacent shots come from different films except the two 1921 newsreel shots. Nothing implies that people in different sources meet.
- Structural: 10 picture events + card, no gaps or overlaps on the timeline (renderer concatenates). Every event maps to a source range in the ledger.

**Critic verdict: PENDING.** I inspected frames and contact sheets; I did not watch at speed.
**Largest unresolved limitation:** sound. The archive's sound clips are almost all narrated and there is no transcription, so the pivots cannot be carried by source sound as the prompt asks, and most of the film plays in silence.

## Critic round 1 and repair

See [../CRITIC-ROUND-1.md](../CRITIC-ROUND-1.md) for the verdict and the repair applied to this film. Shot tables above describe the cut before that repair; the current `edl.json` and ledger are authoritative.

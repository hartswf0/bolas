# 058-laughs — Laughs! — Audible Contagion (archive draft, rev 1)

Builder: scratch name "air". Status: rendered draft. Independent social-context critic review: **PENDING** (none has occurred). Everything below is self-review. I inspected frames, contact sheets and spectrograms/waveforms; I did **not** watch or listen to anything at speed (no audio playback was available to me, so every statement about sound comes from spectrograms, RMS envelopes and onset analysis, not from hearing).

Files: `058-laughs.mp4` (44.2 s, 3.7 MB, voices-only = source sound only, the primary cut) · `edl.json` · `058-laughs.ledger.json` · `edl-alt.json` → `058-laughs-alt.mp4` (same picture + newly composed tick layer `score-ticks.wav`, comparison; **rejected**, see §4) · `edl-context.json` → `058-laughs-context.mp4` (original-context reel: every source clip in full, original timing and sound, 87.5 s, re-encoded crf 31 to 4.7 MB) · `audio-events.json` (per-shot RMS/peak of the finished mix) · `score-ticks.events.json` (every composed tick: time, pitch, gain, whether carried over a cut) · `contact.jpg`.

## 1. Theorem, as adapted to this archive

Prompt: build a changing acoustic chain from individually situated laughter, letting rhythm spread between shots while keeping the difference between people laughing together and an editor making separate recordings answer one another.

What the archive actually holds: visible laughter almost never arrives with its own sound. The laughs are in silent amateur reels (telecine hiss only) or under narration/score in sound films. So the adapted theorem is: **a chain of situated laughs that the archive kept silent, in which the only "contagion" is visual and editorial, and in which the one place where faces really are made to answer one another (a 1954 promotional film cutting grinning men together over music) is shown as the source's own editing, not mine.** Shared laughter is used only where the relation is inside one shot (the stage performer and chorus; the young women leaning into each other; the boys in conversation).

## 2. Forage log

- `forage.py "laugh|giggl|smil|amus|joke|grin|chuckl|comed|clown|tickl"` (clips) → 14 hits; the contact sheet showed almost none actually laughing (cattle pens, hall-of-mirrors, cartoon, Party Magic room). Query text is a weak hint here.
- Broader regex (party|audience|cheer|children|picnic...) → 50 clip hits, mostly crowds and stages.
- Because the queries were unreliable I made dense contact sheets of **all 405 clips** (8 frames each, 17 sheets) and read every one, noting visible laughs/smiles. Candidates: Ivan Besse Britton SD reels (several), Amateur Film New Jersey (man laughing in car), De Joodsche invalide (stage laugh), Day at the Fair (×2), Show 'Em the Road, Beginning to Date, Fundo in Chile, Fighter for Freedom, Five Artists, Thanksgiving Cooking Class 2020, Mastering Takeoffs 2009, Inside the Fed, Under Western Stars, Powers Music School 2009 (audience), Straight Talk 1992.
- Loops: regex over loops returned 2 (neither laughing). Loops are silent anyway.
- Audio checks: (a) per-0.5 s RMS for every candidate; (b) a laugh-pulse detector I wrote (`scratchpad/air/scripts/pulses.py`: voiced 300–3000 Hz bursts with regular 0.12–0.40 s inter-onset intervals) run on all clips — it ranked speech and music as highly as anything, i.e. it does not discriminate laughter in this corpus; (c) aligned frame-strip + spectrogram + envelope images (`scripts/insp.py`) for ~30 candidates. Result: every sound-bearing candidate showed narration, dialogue, song (vibrato) or score where the faces smile. Mastering Takeoffs 0–3.5 s shows a dense, evenly spaced broadband click train — almost certainly **applause**, not laughter, and the people are seen from afar. Inside the Fed (1994, 3 s) has a short train of similar voiced bursts at ~0.3 s spacing at 1.8–2.9 s that *might* be a laugh, but no face is visibly laughing then. I could not verify a single recorded laugh.
- I tried to fetch an audio-event classifier (YAMNet weights) to tag laughter; running downloaded model code was refused by the session's permission policy, so no ML tagging was used.
- Surprises: the strongest laughs in the archive are silent (the New Jersey man's head-back laugh; the Britton girls); the Ivan Besse reels' "sound" is a constant −56 dB telecine hiss; De Joodsche invalide has no audio stream at all; Show 'Em the Road already builds a chain of grins by montage — a found instance of exactly the editorial power the prompt asks us to expose.
- What the archive does NOT have: sync recordings of laughter with the laugher on screen; a held/contained laugh with audible breath; consent records (all public-domain/orphan footage; consent of the people filmed is unknown).

## 3. The cut (voices-only, `058-laughs.mp4`)

| # | time | source (film, year, film-time) | why |
|---|---|---|---|
| 0 | 0.00–5.80 | Ivan Besse collection, Britton SD, Part II, 1938 (t≈146 s) `79f16f7c` | A woman in a doorway smiles toward the camera, holds it, then withdraws. Closest thing to a contained laugh; the source track is only hiss, kept at its native level as the quiet opening. |
| 1 | 5.80–8.65 | Amateur Film New Jersey B, n.d. (t≈141 s) `fb5bfa37` | A man in a car throws his head back laughing — explosive against the held smile. Unheard (hiss only). |
| 2 | 8.65–11.75 | De Joodsche invalide, 1939 (t≈1478 s) `c6291759` | Third location: stage performer laughing with a mug while the chorus behind him laughs with him (relation inside the source; includes the source's own cut at 2.0 s). No audio stream → digital silence. |
| 3 | 11.75–16.75 | A Day at the Fair, 1947 (t≈601 s) `7ba3cb22` | Children grinning on a fairground ride; first real sound (fair/score bed, −40 dB RMS). |
| 4 | 16.75–19.25 | Ivan Besse, Part IX, 1938 (t≈708 s) `6beb1ad0` | A young woman laughs as she passes the camera; source cut to a man covering his face from the camera. Short, the "pulse" in the middle. |
| 5 | 19.25–25.15 | Show 'Em the Road Part I, 1954 (t≈22 s) `d26d45e4` | The source's own montage of young men grinning one after another to its music (loudest passage, −29 dB RMS). The answering here is the 1954 editor's. |
| 6 | 25.15–31.20 | Ivan Besse, Part V, 1938 (t≈544 s) `67911fe5` | Young women laughing together and leaning into each other — given the full duration to the reel splice. |
| 7 | 31.20–32.20 | same reel, t≈550 s | The reel runs out: grey leader + the same hiss. The film's own room tone. |
| 8 | 32.20–39.10 | Beginning to Date, 1953 (t≈500 s) `3b640aa6` | Aftermath: boys still smiling at one another in conversation, source voices/score kept, fading out. Their relation exists in the shot. |
| 9 | 39.10–40.70 | — | black, digital silence |
| 10 | 40.70–44.20 | — | source card |

Transforms: uniform scale + centre crop only (ledger). No retiming, mirroring, pitch change, or cross-source audio overlap.

## 4. Departures from the hard proof, and why

- **No acoustic chain of laughs.** The prompt's core material (recorded laughter) is not verifiably present. The film's "sound chain" is hiss → silence → fair bed → hiss → score → hiss → voices → silence. I chose a smaller honest film over putting laugh sounds under silent laughers.
- **No overlapping laugh pulses.** Overlap would have required laying one source's audio under another's picture; with no laugh audio there was nothing to overlap that would not manufacture a reaction. The renderer also renders events independently (no cross-cut audio overlap) — not the reason, but noted.
- **Contained laugh with audible breath:** substituted by a held smile with no audible breath.
- **Ending:** prompt asks for people who have stopped laughing but still react to one another; Beginning to Date (boys still smiling in conversation) is the nearest in-source relation, followed by silence. The runout grey of the Britton reel serves as the "empty room tone" beat.
- **Music variant:** made as `058-laughs-alt.mp4` — newly composed sine ticks (one pitch per shot) placed at peaks of frame-difference motion in each laugh shot, the last two of each shot echoed 0.4/0.8 s past the cut (the editor's overlap made audible), at −14 dB under source. **Rejected**: checking `score-ticks.events.json`, the held-smile shot (almost no body motion) received 26 ticks — frame-difference peaks on 1938 amateur stock follow grain/flicker as much as bodies, so the ticks assert a rhythm the people do not have. It adds a relation only between the editor and the film's grain. Voices-only is adopted.
- §3 swarm roles collapsed into one builder; the critic role is not filled.

## 5. Self-review against §5 (perceptual items unverified; I have not watched at speed)

- Separate situations established before composite rhythm: yes structurally — doorway (SD), car (NJ), stage (Amsterdam) before any montage-made sequence. Measured: three distinct sources/locations in first 11.75 s.
- Onset → overlap → recovery → rest: partially. Onset (held smile→burst), recovery (shot 6 held, runout), rest (black silence) exist; **acoustic overlap does not**.
- Critic can distinguish shared source laughter from montage exchange: intended via shot 5 (source-made chain) vs shots 2/6/8 (in-shot relations). Unverified.
- Quiet interval contributes to movement: shots 0, 2, 7, 9 are quiet/silent. Measured RMS in `audio-events.json`.
- No unconsenting target via adjacency: no laugh sound is placed under any other person; no shot shows a person in difficulty. The man covering his face (shot 4) is camera-shyness in his own source, adjacent to women laughing in a different reel — **flag for critic review** as the one adjacency that could read as laughing *at* him. De Joodsche invalide (1939 Amsterdam Jewish community benefit film, per its title) — laughter shown is the performers' own; historical context flagged for the critic.
- Automated: peak of finished mix −13.7 dBFS, no clipping (renderer limiter at 0.89 not engaged by overlaps; there are none). Source audio under unrelated subject: none (all audio is each shot's own track or digital silence).

Largest unresolved limitation: no verified recording of laughter anywhere in the clip set; an audio classifier or a human listener should re-check the sound clips (esp. Inside the Fed 1.8–2.9 s, Powers Music School 2009 audience) before claiming the archive has none.

## Critic round 1 and repair

See [../CRITIC-ROUND-1.md](../CRITIC-ROUND-1.md) for the verdict and the repair applied to this film. Shot tables above describe the cut before that repair; the current `edl.json` and ledger are authoritative.
